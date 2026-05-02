import logging
from pathlib import Path

from validator.core.models import DocumentationFile, ValidationIssue, IssueType, SeverityLevel
from validator.validators.base_validator import BaseValidator
log = logging.getLogger(__name__)

class BrokenLinkValidator(BaseValidator):
    """Проверяет существование файлов, на которые указывают internal ссылки."""

    def validate(self, files_to_validate: dict[Path, DocumentationFile], root_dir: Path) -> list[ValidationIssue]:
        log.debug(f'Начало проверки существования файлов, количество файлов: {len(files_to_validate)}')
        issues = []
        for file in files_to_validate.values():
            for link in file.links_out:
                target_path = root_dir / link.target_file
                if target_path is not None and not target_path.exists():
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
