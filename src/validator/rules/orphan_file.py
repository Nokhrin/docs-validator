import logging
from pathlib import Path
from typing import Optional

from validator.core.mkdocs_parser import get_nav_roots
from validator.core.models import DocumentationFile, ValidationIssue, IssueType, SeverityLevel
from validator.rules.base_validator import BaseValidator

log = logging.getLogger(__name__)

def _find_mkdocs_config(start_dir: Path) -> Path | None:
    """Searches for mkdocs.yml, moving up from start_dir to the FS root."""
    current = start_dir.resolve()
    while True:
        candidate = current / 'mkdocs.yml'
        if candidate.exists():
            return candidate
        parent = current.parent
        if parent == current:
            return None
        current = parent


class OrphanFileValidator(BaseValidator):
    """Finds files without incoming links.
       Orphans DO NOT include:
       - Files from DEFAULT_ROOT_FILES (README.md, index.md, etc.)
       - Files listed in mkdocs.yml navigation (if found)
    """

    DEFAULT_ROOT_FILES: set[str] = {
        'README.md', 'README.rst', 'README.txt',
        'index.md', 'index.html', 'index.rst', 'CONTRIBUTING.md',
    }


    def validate(self, files_to_validate: dict[Path, DocumentationFile], root_dir: Path) -> list[ValidationIssue]:
        log.debug(f'Starting orphan check, total files: {len(files_to_validate)}')
        target_files: set[Path] = set()
        for file in files_to_validate.values():
            for link in file.links_out:
                if link.is_internal:
                    target = link.target_file
                    if target is not None:
                        target_files.add(target)

        mkdocs_file: Optional[Path] = _find_mkdocs_config(root_dir)

        if mkdocs_file is not None:
            nav_roots: set[Path] = get_nav_roots(mkdocs_file)
            log.debug('mkdocs.yml found: %s', mkdocs_file)
        else:
            nav_roots = set()
            log.debug('mkdocs.yml not found in directory tree from %s', root_dir)

        log.debug('Root files - cannot be orphans: %s', nav_roots)

        excluded_paths_posix: set[str] = set()
        for p in nav_roots:
            normalized = p.with_suffix('.md').as_posix() if not p.suffix else p.as_posix()
            excluded_paths_posix.add(normalized)

        log.debug('excluded_paths from mkdocs: %s', excluded_paths_posix)

        issues = []
        for file in files_to_validate.values():
            file_path_str = file.path.as_posix()

            is_in_excluded = (
                file_path_str in excluded_paths_posix or
                any(file_path_str.endswith(f'/{ex}') for ex in excluded_paths_posix)
            )

            is_excluded = file.path.name in self.DEFAULT_ROOT_FILES or is_in_excluded

            log.debug('Checking file: %s (in excluded: %s)', file_path_str, is_in_excluded)

            if not is_excluded and file.path not in target_files:
                log.debug(f'Orphan found: {file.path}')
                issues.append(ValidationIssue(
                    issue_type=IssueType.ORPHAN_FILE,
                    severity_level=SeverityLevel.WARNING,
                    src_file=file,
                    message=f'File {file.path} has no incoming links',
                    suggestion='Add a link to the file or include it in the mkdocs navigation',
                ))
        return issues
