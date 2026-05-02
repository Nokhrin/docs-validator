import logging
from pathlib import Path

from validator.core.models import DocumentationFile, ValidationIssue
from validator.validators.base_validator import BaseValidator

log = logging.getLogger(__name__)


class AnchorLinkValidator(BaseValidator):
    """Проверяет существование якоря."""

    def validate(self, files_to_validate: dict[Path, DocumentationFile], root_dir: Path) -> list[ValidationIssue]:
        log.debug('проверка якоря - заглушка')
        # TODO - спринт 3
        pass
