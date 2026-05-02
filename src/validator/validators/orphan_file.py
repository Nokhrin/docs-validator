import logging
from pathlib import Path

from validator.core.models import DocumentationFile, ValidationIssue, IssueType, SeverityLevel
from validator.validators.base_validator import BaseValidator

log = logging.getLogger(__name__)


class OrphanFileValidator(BaseValidator):
    """Находит файлы без входящих ссылок.

    Сиротами никогда не считаются entry points

    Entry points (не считаются сиротами по умолчанию):
    - README.md, README.rst, README.txt
    - index.md, index.html, index.rst

    Это соответствует конвенциям документации:
    - MkDocs, Sphinx, Docusaurus используют index.md как entry point раздела
    - GitHub показывает README.md как описание директории

    Ограничения:
    - Файл orphan-section/index.md не будет помечен как сирота
    #TODO - строгая валидация: --strict режим (Спринт 3+)
    """

    DEFAULT_ROOT_FILES = {
        'README.md', 'README.rst', 'README.txt',
        'index.md', 'index.html', 'index.rst',
    }


    def validate(self, files_to_validate: dict[Path, DocumentationFile], root_dir: Path) -> list[ValidationIssue]:
        log.debug(f'Начало проверки на отсутствие входящих ссылок, количество файлов: {len(files_to_validate)}')
        issues = []
        target_files: set[Path] = set()
        for file in files_to_validate.values():
            for link in file.links_out:
                if link.is_internal and link.target_file is not None:
                    target_files.add(link.target_file)

        for file in files_to_validate.values():
            if file.path.name not in self.DEFAULT_ROOT_FILES:
                if file.path not in target_files:
                    log.debug(f'Найден сирота: {file.path}', )
                    issues.append(ValidationIssue(
                        issue_type=IssueType.ORPHAN_FILE,
                        severity_level=SeverityLevel.WARNING,
                        src_file=file,
                        link=None,
                        message=f'Файл {file.path} не содержит входящих ссылок',
                        suggestion='Добавьте ссылку на файл',
                    ))
        return issues
