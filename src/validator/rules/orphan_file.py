import logging
from pathlib import Path
from typing import Optional

from validator.core.mkdocs_parser import get_nav_roots
from validator.core.models import DocumentationFile, ValidationIssue, IssueType, SeverityLevel
from validator.rules.base_validator import BaseValidator

log = logging.getLogger(__name__)

def _find_mkdocs_config(start_dir: Path) -> Path | None:
    """Ищет mkdocs.yml, поднимаясь от start_dir к корню ФС."""
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
    """Находит файлы без входящих ссылок.

    Сиротами НЕ считаются:
    - Файлы из DEFAULT_ROOT_FILES (README.md, index.md и т.д.)
    - Файлы, указанные в навигации mkdocs.yml (если файл найден)

    Entry points (не считаются сиротами по умолчанию):
    - README.md, README.rst, README.txt
    - index.md, index.html, index.rst

    Это соответствует конвенциям документации:
    - MkDocs, Sphinx, Docusaurus используют index.md как entry point раздела
    - GitHub показывает README.md как описание директории
    """

    DEFAULT_ROOT_FILES: set[str] = {
        'README.md', 'README.rst', 'README.txt',
        'index.md', 'index.html', 'index.rst', 'CONTRIBUTING.md',
    }


    def validate(self, files_to_validate: dict[Path, DocumentationFile], root_dir: Path) -> list[ValidationIssue]:
        log.debug(f'Начало проверки на сирот, файлов: {len(files_to_validate)}')
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
            log.debug('mkdocs.yml найден: %s', mkdocs_file)
        else:
            nav_roots = set()
            log.debug('mkdocs.yml не найден в дереве каталогов от %s', root_dir)

        log.debug('Корневые файлы - не могут быть сиротами: %s', nav_roots)

        excluded_paths_posix: set[str] = set()
        for p in nav_roots:
            normalized = p.with_suffix('.md').as_posix() if not p.suffix else p.as_posix()
            excluded_paths_posix.add(normalized)

        log.debug('excluded_paths из mkdocs: %s', excluded_paths_posix)

        issues = []
        for file in files_to_validate.values():
            file_path_str = file.path.as_posix()

            # Точное совпадение или вхождение как суффикса (учитывает префикс docs/)
            is_in_excluded = (
                file_path_str in excluded_paths_posix or
                any(file_path_str.endswith(f'/{ex}') for ex in excluded_paths_posix)
            )

            is_excluded = file.path.name in self.DEFAULT_ROOT_FILES or is_in_excluded

            log.debug('Проверка файла: %s (в excluded: %s)', file_path_str, is_in_excluded)

            if not is_excluded and file.path not in target_files:
                log.debug(f'Найден сирота: {file.path}', )
                issues.append(ValidationIssue(
                    issue_type=IssueType.ORPHAN_FILE,
                    severity_level=SeverityLevel.WARNING,
                    src_file=file,
                    message=f'Файл {file.path} не содержит входящих ссылок',
                    suggestion='Добавьте ссылку на файл или укажите файл в оглавлении mkdocs',
                ))
        return issues
