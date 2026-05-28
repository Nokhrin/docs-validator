import logging
import sys
from argparse import Namespace
from contextlib import contextmanager
from dataclasses import replace, fields
from pathlib import Path
from typing import Callable, Iterator, TextIO

from validator.config import ValidatorConfig, load_config_from_toml, merge_config
from validator.core.explorer import FilesExplorer
from validator.core.extractor import LinkExtractor
from validator.core.models import DocumentationFile, ValidationIssue, LinkStatistics, LinkType, Link, SeverityLevel
from validator.reporters import JSONReporter, MarkdownReporter, HTMLReporter
from validator.rules import BrokenLinkValidator, OrphanFileValidator, AnchorLinkValidator, \
    CircularDependencyValidator, ExternalLinkValidator, BaseValidator

log = logging.getLogger(__name__)


def load_configuration(args: Namespace) -> ValidatorConfig:
    """Загружает значения параметров конфигурации.

    Приоритет конфигурации: cli, toml, default
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
    """Извлекает метаданные из файлов в директории.

    Рекурсивно от root
    """
    if not path_to_explore.exists():
        log.error('Не удалось найти запрошенный путь: %s', path_to_explore)
        return {}
    if not path_to_explore.is_dir():
        log.error('Запрошенный путь не является каталогом: %s', path_to_explore)
        return {}

    explorer = FilesExplorer(
        root_path=path_to_explore,
        patterns_exclude=set(config.exclude_patterns)
    )

    return {f.path: f for f in explorer.find_files()}


def collect_links(files: dict[Path, DocumentationFile], root_path: Path) -> dict[Path, DocumentationFile]:
    """Записывает информацию о ссылках файла.

    Args:
        files: Словарь файлов (ключи - относительные пути).
        root_path: Абсолютный или относительный путь к корню сканирования для резолва путей.

    Результат в поле DocumentationFile.out_links
    Возвращает новый экземпляр списка
    """
    for file_path, file_obj in files.items():
        try:
            full_path = root_path / file_path
            file_content = full_path.read_text(encoding='utf-8')
            file_obj.links_out=set(LinkExtractor(file_obj.path).get_links_from_file(file_content))
        except IOError as err:
            log.error('Не удалось прочитать %s: %s', file_obj.path, err)
            file_obj.links_out = set()
    return files


def collect_issues(files: dict[Path, DocumentationFile], config: ValidatorConfig) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if config.is_validate:
        if config.path_to_explore is None:
            raise ValueError("Не задан path_to_explore. Валидация отменена.")

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
    """Возвращает статистику валидации ссылок."""
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


def generate_summary(
        files: dict[Path, DocumentationFile],
        issues: list[ValidationIssue],
        stats: LinkStatistics,
) -> str:
    files_total = len(files)
    links_total = sum(len(f.links_out) for f in files.values())

    error_count = sum(1 for i in issues if i.severity_level == SeverityLevel.ERROR)
    warning_count = sum(1 for i in issues if i.severity_level == SeverityLevel.WARNING)

    lines = [
        '=' * 40,
        'СТАТИСТИКА ВЫПОЛНЕНИЯ',
        '=' * 40,
        f'Обработано файлов: {files_total}',
        f'Обнаружено ссылок: {links_total}',
        f'Внутренних ссылок: {stats.internal_total}',
        f'Внешних ссылок: {stats.external_total} (недоступно: {stats.external_broken})',
    ]

    if issues:
        parts = []
        if error_count:
            parts.append(f'ошибок: {error_count}')
        if warning_count:
            parts.append(f'предупреждений: {warning_count}')
        detail = f' ({', '.join(parts)})' if parts else ''
        lines.append(f'Найдено проблем: {len(issues)}{detail}')
    else:
        lines.append('Проблем не обнаружено.')

    lines.append('=' * 40)
    return '\n'.join(lines)

def generate_report(
        files: dict[Path, DocumentationFile],
        issues: list[ValidationIssue],
        stats: LinkStatistics,
        config: ValidatorConfig,
) -> str:
    reporters: dict[str, Callable[[dict[Path, DocumentationFile], list[ValidationIssue], LinkStatistics], str]] = {
        'json': lambda f, i, s: JSONReporter().report(f, i, s),
        'markdown': lambda f, i, s: MarkdownReporter().report(f, i, s),
        'html': lambda f, i, s: HTMLReporter().report(f, i, s),
    }
    make_report = reporters.get(config.report_format, reporters['markdown'])

    return make_report(files, issues, stats)

def write_report(report_content: str, output_path: Path | None) -> None:
    with open_output(output_path) as out_stream:
        out_stream.write(report_content)
        if output_path is None:
            out_stream.write('\n')


@contextmanager
def open_output(path: Path | None) -> Iterator[TextIO]:
    if path is None:
        yield sys.stdout
    else:
        with open(path, 'w', encoding='utf-8') as file:
            yield file


def get_exit_code(
        issues: list[ValidationIssue],
        config: ValidatorConfig,
) -> int:
    if config.is_fail_on_error and any(i.severity_level.value == 'error' for i in issues):
        return 1
    return 0

def run_validation(config: ValidatorConfig) -> tuple[int,str]:
    if config.path_to_explore is None:
        log.error('Не указана директория для сканирования')
        return 1, ''
    path_to_explore = Path(config.path_to_explore)
    if not path_to_explore.exists():
        log.error('Директория не найдена: %s', path_to_explore)
        return 1, ''

    files = explore_files(path_to_explore, config)
    if not files:
        return 0, ''

    collect_links(files, path_to_explore)
    issues=collect_issues(files,config) if config.is_validate else []
    stats=aggregate_issue_statistics(files,issues)
    report_content = generate_report(files, issues, stats, config)

    return get_exit_code(issues, config), report_content