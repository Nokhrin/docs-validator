"""Execution orchestrator."""
import logging
from argparse import Namespace
from dataclasses import replace, fields
from pathlib import Path

from validator.config import ValidatorConfig, load_config_from_toml, merge_config
from validator.core.explorer import FilesExplorer
from validator.core.extractor import LinkExtractor
from validator.core.models import DocumentationFile, ValidationIssue, LinkStatistics, LinkType, Link
from validator.rules import BrokenLinkValidator, OrphanFileValidator, AnchorLinkValidator, \
    CircularDependencyValidator, ExternalLinkValidator, BaseValidator

log = logging.getLogger(__name__)


def load_configuration(args: Namespace) -> ValidatorConfig:
    """Loads configuration parameter values.
    Priority: cli > toml > default
    """
    config = ValidatorConfig(args.path_to_explore)

    config_file = Path(args.config) if args.config else Path.cwd() / '.docs-validator.toml'
    if config_file.exists():
        config = merge_config(config, load_config_from_toml(config_file))

    valid_fields = {f.name for f in fields(ValidatorConfig)}
    cli_updates = {
        k: v for k, v in vars(args).items()
        if k in valid_fields and v is not None
    }
    return replace(config, **cli_updates)


def explore_files(path_to_explore: Path, config: ValidatorConfig) -> dict[Path, DocumentationFile]:
    """Extracts metadata from files in the directory.
    Recursively from root.
    """
    if not path_to_explore.exists():
        log.error('Requested path not found: %s', path_to_explore)
        return {}
    if not path_to_explore.is_dir():
        log.error('Requested path is not a directory: %s', path_to_explore)
        return {}

    explorer = FilesExplorer(
        root_path=path_to_explore,
        patterns_exclude=set(config.exclude_patterns)
    )

    return {f.path: f for f in explorer.find_files()}


def collect_links(files: dict[Path, DocumentationFile], root_path: Path) -> dict[Path, DocumentationFile]:
    """Appends link information for the file.
    Args:
        files: Dictionary of files (keys are relative paths).
        root_path: Absolute or relative path to the scan root for path resolution.
    Returns:
        Updated dictionary of files.
    """
    for file_path, file_obj in files.items():
        try:
            full_path = root_path / file_path
            file_content = full_path.read_text(encoding='utf-8')
            file_obj.links_out = set(LinkExtractor(file_obj.path).get_links_from_file(file_content))
        except IOError as err:
            log.error('Failed to read %s: %s', file_obj.path, err)
            file_obj.links_out = set()
    return files


def collect_issues(files: dict[Path, DocumentationFile], config: ValidatorConfig) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if config.is_validate:
        if config.path_to_explore is None:
            raise ValueError('path_to_explore is not set. Validation aborted.')

        validators: list[BaseValidator] = [
            BrokenLinkValidator(), OrphanFileValidator(), AnchorLinkValidator(), CircularDependencyValidator()
        ]
        if not config.is_skip_external:
            validators.append(ExternalLinkValidator(
                external_timeout_sec=config.external_timeout_sec,
                max_threads_number=config.max_threads_number,
                hosts_to_ignore=config.hosts_to_ignore,
            ))

        for validator in validators:
            new_issues = validator.validate(files, config.path_to_explore)
            issues.extend(new_issues)
    return issues


def aggregate_issue_statistics(
        files: dict[Path, DocumentationFile],
        issues: list[ValidationIssue],
) -> LinkStatistics:
    broken_links: set[Link] = {i.link for i in issues if i.link is not None}
    internal_total = 0
    internal_broken = 0
    external_total = 0
    external_broken = 0

    for file in files.values():
        for link in file.links_out:
            if link.link_type is LinkType.INTERNAL:
                internal_total += 1
                if link in broken_links:
                    internal_broken += 1
            elif link.link_type is LinkType.EXTERNAL:
                external_total += 1
                if link in broken_links:
                    external_broken += 1

    return LinkStatistics(
        internal_total=internal_total,
        internal_broken=internal_broken,
        external_total=external_total,
        external_broken=external_broken,
    )


def get_exit_code(
        issues: list[ValidationIssue],
        config: ValidatorConfig,
) -> int:
    if config.is_fail_on_error and any(i.severity_level.value == 'error' for i in issues):
        return 1
    return 0


def run_validation(
        config: ValidatorConfig
) -> tuple[dict[Path, DocumentationFile], list[ValidationIssue], LinkStatistics, int]:
    if config.path_to_explore is None:
        log.error('No directory specified for scanning')
        return {}, [], LinkStatistics(), 1
    path_to_explore = Path(config.path_to_explore)
    if not path_to_explore.exists():
        log.error('Directory not found: %s', path_to_explore)
        return {}, [], LinkStatistics(), 1

    files: dict[Path, DocumentationFile] = explore_files(path_to_explore, config)
    if not files:
        return {}, [], LinkStatistics(), 0

    collect_links(files, path_to_explore)
    issues: list[ValidationIssue] = collect_issues(files, config) if config.is_validate else []
    stats: LinkStatistics = aggregate_issue_statistics(files, issues)
    exit_code: int = get_exit_code(issues, config)

    return files, issues, stats, exit_code
