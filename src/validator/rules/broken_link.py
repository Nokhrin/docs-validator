import logging
from pathlib import Path

from validator.core.models import DocumentationFile, ValidationIssue, IssueType, SeverityLevel
from validator.rules.base_validator import BaseValidator
log = logging.getLogger(__name__)

class BrokenLinkValidator(BaseValidator):
    """Checks the existence of files pointed to by internal links.
    Works with the local file system.
    """
    def validate(self, files_to_validate: dict[Path, DocumentationFile], root_dir: Path) -> list[ValidationIssue]:
        log.debug(f'Starting file existence check, total files: {len(files_to_validate)}')
        issues = []
        for file in files_to_validate.values():
            for link in file.links_out:

                if not link.is_internal or link.target_file is None:
                    continue

                source_abs = root_dir / link.parent_file
                target_path = (source_abs.parent / link.target_file).resolve()
                if not target_path.exists():
                    log.debug(f'Target file not found: {link.target_file} for link {link}')
                    issues.append(ValidationIssue(
                        issue_type=IssueType.BROKEN_LINK,
                        severity_level=SeverityLevel.ERROR,
                        src_file=file,
                        link=link,
                        message=f'Target file not found: {link.target_file}',
                        suggestion='Check the link and the target file',
                    ))
        return issues
