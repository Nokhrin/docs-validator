import logging
from pathlib import Path

from validator.core.models import DocumentationFile, ValidationIssue, IssueType, SeverityLevel
from validator.rules.base_validator import BaseValidator
log = logging.getLogger(__name__)

class BrokenLinkValidator(BaseValidator):
    """Проверяет существование файлов, на которые указывают internal ссылки.

    Работает с локальной файловой системой.
    """

    def validate(self, files_to_validate: dict[Path, DocumentationFile], root_dir: Path) -> list[ValidationIssue]:
        log.debug(f'Начало проверки существования файлов, количество файлов: {len(files_to_validate)}')
        issues = []
        for file in files_to_validate.values():
            for link in file.links_out:

                if not link.is_internal or link.target_file is None:
                    continue

                source_abs = root_dir / link.parent_file
                target_path = (source_abs.parent / link.target_file).resolve()
                if not target_path.exists():
                    log.debug(f'Не найден адресуемый файл: {link.target_file} по ссылке {link}',)
                    issues.append(ValidationIssue(
                        issue_type=IssueType.BROKEN_LINK,
                        severity_level=SeverityLevel.ERROR,
                        src_file=file,
                        link=link,
                        message=f'Не найден адресуемый файл: {link.target_file}',
                        suggestion='Проверьте ссылку и целевой файл',
                    ))
        return issues
