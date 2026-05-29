import logging
from pathlib import Path

from validator.core.mkdocs_parser import get_nav_roots
from validator.core.models import DocumentationFile, ValidationIssue, IssueType, SeverityLevel
from validator.rules.base_validator import BaseValidator

log = logging.getLogger(__name__)


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
        'index.md', 'index.html', 'index.rst',
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

        mkdocs_file: Path = root_dir / 'mkdocs.yml'
        nav_roots: set[Path] = get_nav_roots(mkdocs_file)

        excluded_paths: set[Path]=set()
        for file in nav_roots:
            if file.suffix:
                excluded_paths.add(file)
            else:
                excluded_paths.add(file.with_suffix('.md'))

        issues = []
        for file in files_to_validate.values():
            is_excluded = (file.path.name in self.DEFAULT_ROOT_FILES) or (file.path in excluded_paths)

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
