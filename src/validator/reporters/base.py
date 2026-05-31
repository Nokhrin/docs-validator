"""
Расчет метрик
    Errors
    Count(issues where severity == ERROR AND src_file == current_file)

    Warnings
    Count(issues where severity == WARNING AND src_file == current_file)

    Coverage
    (total_links - broken_links) / total_links * 100 для файла

    TOTAL
    Агрегация по всем файлам
"""
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
