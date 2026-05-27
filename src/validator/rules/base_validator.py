"""Интерфейс валидатора."""
from abc import ABC, abstractmethod
from pathlib import Path

from validator.core.models import DocumentationFile, ValidationIssue


class BaseValidator(ABC):
    @abstractmethod
    def validate(
            self,
            files_to_validate: dict[Path, DocumentationFile],
            root_dir: Path,
    ) -> list[ValidationIssue]:
        """Возвращает список ошибок валидации."""
        pass
