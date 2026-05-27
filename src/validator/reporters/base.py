from abc import abstractmethod, ABC
from pathlib import Path

from validator.core.models import DocumentationFile, ValidationIssue, LinkStatistics


class BaseReporter(ABC):
    """Интерфейс."""

    @abstractmethod
    def report(
            self,
            files: dict[Path, DocumentationFile],
            issues: list[ValidationIssue],
            link_stat: LinkStatistics,
    ) -> str:
        """Возвращает отчет по результатам валидации."""
        pass
