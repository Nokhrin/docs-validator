import logging
import sys
from enum import Enum
from pathlib import Path
from typing import TextIO

from validator.core.models import DocumentationFile, ValidationIssue, LinkStatistics
from validator.reporters import BaseReporter

log = logging.getLogger(__name__)


class TermColor(Enum):
    """Цвета текста консоли."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"  # ERROR
    YELLOW = "\033[93m"  # WARNING
    BLUE = "\033[94m"  # INFO
    GREEN = "\033[92m"  # успех
    GRAY = "\033[90m"  # прочее

    def apply(self, text: str) -> str:
        return f'{self.value}{text}{TermColor.RESET.value}'


class CLIReporter(BaseReporter):
    """Генерирует отчет для печати в консоль."""

    def __init__(
            self,
            stream: TextIO = sys.stderr,
            use_color: bool = True,
    ):
        self.stream = stream
        self.use_color = use_color

    def _colorize(self, text: str, color: TermColor) -> str:
        if self.use_color:
            return color.apply(text)
        return text

    def report(
            self,
            files: dict[Path, DocumentationFile],
            issues: list[ValidationIssue],
            link_stat: LinkStatistics,
    ) -> str:
        """Возвращает строку для вывода в поток."""
        if not issues:
            self._write_line(self._colorize('No issues found', TermColor.BLUE))
            return ''

        result_statistics: dict[str, dict[str, int]] = {}
        for issue in issues:
            issue_type = issue.issue_type.value
            severity = issue.severity_level.value.upper()
            if issue not in result_statistics:
                result_statistics[issue_type] = {
                    'ERROR': 0,
                    'WARNING': 0,
                    'INFO': 0,
                }
            result_statistics[issue_type][severity] += 1

            self._write_line('', 'info')
            self._write_line(self._colorize('=' * 42, TermColor.GRAY), 'info')
            self._write_line(self._colorize('ISSUES SUMMARY', TermColor.BOLD), 'info')
            self._write_line(self._colorize('=' * 42, TermColor.GRAY), 'info')

        total_count = 0
        error_count = 0

        for issue_type in sorted(result_statistics.keys()):
            issue_count = result_statistics[issue_type]
            issue_type_total: int = sum(issue_count.values())
            errors_total: int = issue_count.get('ERROR', 0)

            total_count += issue_type_total
            error_count += errors_total

            parts = []
            if issue_count["ERROR"] > 0:
                parts.append(f"{issue_count['ERROR']} ERR")
            if issue_count["WARNING"] > 0:
                parts.append(f"{issue_count['WARNING']} WARN")
            if issue_count["INFO"] > 0:
                parts.append(f"{issue_count['INFO']} INFO")

            details = ', '.join(parts) if parts else f'{issue_count} items'

            line_type = issue_type
            if errors_total > 0:
                line_type = self._colorize(issue_type, TermColor.RED)

            self._write_line(f'{line_type:<20}: {details}', 'warning')

        self._write_line('-' * 42, 'info')

        if error_count > 0:
            msg = f'TOTAL: {total_count} issues ({error_count} errors)'
            self._write_line(self._colorize(msg, TermColor.RED), 'error')
        else:
            msg = f'TOTAL: {total_count} issues (no critical errors)'
            self._write_line(self._colorize(msg, TermColor.YELLOW), 'warning')

        self._write_line(self._colorize('=' * 42, TermColor.GRAY), 'info')
        self._write_line('', 'info')

        return ''

    @staticmethod
    def _write_line(text: str = '', log_level: str = 'info') -> None:
        if log_level == 'warning':
            log.warning(text)
        elif log_level == 'error':
            log.error(text)
        elif log_level == 'info':
            log.info(text)
