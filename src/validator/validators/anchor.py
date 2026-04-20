import logging
from pathlib import Path

from validator.core.models import FileToValidate, ValidationIssue
from validator.validators.base import BaseValidator

log = logging.getLogger(__name__)


class AnchorValidator(BaseValidator):
    """Проверяет существование якоря."""

    def validate(self, files_to_validate: dict[Path, FileToValidate], root_file: Path) -> list[ValidationIssue]:
        log.debug('проверка якоря - заглушка')
        # TODO - спринт 3
        pass
