"""Generates a report for console output."""
import logging
import sys
from enum import Enum
from pathlib import Path
from typing import TextIO

from validator.core.models import DocumentationFile, ValidationIssue, LinkStatistics, SeverityLevel
from validator.reporters import BaseReporter

log = logging.getLogger(__name__)


class TermColor(Enum):
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"  # ERROR
    YELLOW = "\033[93m"  # WARNING
    BLUE = "\033[94m"  # INFO
    GREEN = "\033[92m"  # success
    GRAY = "\033[90m"  # other

    def apply(self, text: str) -> str:
        return f'{self.value}{text}{TermColor.RESET.value}'


class CLIReporter(BaseReporter):
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

    def _write_line(self, text: str = '') -> None:
        self.stream.write(text + '\n')
        self.stream.flush()


class TermColor(Enum):
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    GRAY = "\033[90m"

    def apply(self, text: str) -> str:
        return f'{self.value}{text}{TermColor.RESET.value}'


class CLIReporter(BaseReporter):
    def __init__(
            self,
            stream: TextIO = sys.stdout,
            use_color: bool = True,
    ):
        self.stream = stream
        self.use_color = use_color

    def _colorize(self, text: str, color: TermColor) -> str:
        return color.apply(text) if self.use_color else text

    def _write_line(self, text: str = '') -> None:
        self.stream.write(text + '\n')
        self.stream.flush()

    def report(
            self,
            files: dict[Path, DocumentationFile],
            issues: list[ValidationIssue],
            link_stat: LinkStatistics,
    ) -> str:
        if not files:
            self._write_line('No files found for validation.')
            return ''

        file_issues: dict[Path, list[ValidationIssue]] = {}
        for issue in issues:
            file_issues.setdefault(issue.src_file.path, []).append(issue)

        rows: list[tuple[str, int, int, int, int]] = []
        for file_path, file_obj in sorted(files.items(), key=lambda x: str(x[0])):
            f_issues = file_issues.get(file_path, [])
            errors = sum(1 for i in f_issues if i.severity_level == SeverityLevel.ERROR)
            warnings = sum(1 for i in f_issues if i.severity_level == SeverityLevel.WARNING)
            total_links = len(file_obj.links_out)
            broken_links = len({i.link for i in f_issues if i.link is not None})
            rows.append((str(file_path), errors, warnings, total_links, broken_links))

        col_file_width = max((len(r[0]) for r in rows), default=10)
        col_file_width = max(col_file_width, len('File'))

        lines: list[str] = ['']
        header = f"{'File':<{col_file_width}} {'Errors':>7} {'Warnings':>9} {'Links':>6} {'Broken':>7}"
        lines.append(self._colorize(header, TermColor.BOLD))
        lines.append('-' * len(header))

        for path, errors, warnings, total, broken in rows:
            line = f"{path:<{col_file_width}} {errors:>7} {warnings:>9} {total:>6} {broken:>7}"
            if errors > 0:
                line = self._colorize(line, TermColor.RED)
            elif warnings > 0:
                line = self._colorize(line, TermColor.YELLOW)
            lines.append(line)

        lines.append('-' * len(header))

        if issues:
            lines.append('')
            lines.append(self._colorize('Error Details:', TermColor.BOLD))
            for issue in issues:
                if issue.severity_level == SeverityLevel.ERROR:
                    location = f'{issue.src_file.path}:{issue.link.line_number}' \
                        if issue.link else str(issue.src_file.path)
                    target = issue.link.uri if issue.link else 'N/A'
                    lines.append(f'  {self._colorize(location, TermColor.YELLOW)} -> {target}')
            lines.append('')

        total_errors = sum(r[1] for r in rows)
        total_warnings = sum(r[2] for r in rows)
        total_links = sum(r[3] for r in rows)
        total_broken = sum(r[4] for r in rows)

        summary_label = f'{len(files)}'
        summary_line = f'{summary_label:<{col_file_width}} {total_errors:>7} {total_warnings:>9} {total_links:>6} {total_broken:>7}'
        footer = f"TOTAL\n{'Files':<{col_file_width}} {'Errors':>7} {'Warnings':>9} {'Links':>6} {'Broken':>7}"
        lines.append(self._colorize(footer, TermColor.BOLD))
        lines.append(summary_line)
        lines.append('-' * len(header))

        lines.append(f'Total issues: {len(issues)}')
        lines.append(f'Internal links: {link_stat.internal_total} (broken: {link_stat.internal_broken})')
        lines.append(f'External links: {link_stat.external_total} (broken: {link_stat.external_broken})')
        lines.append('')

        for line in lines:
            self._write_line(line)
        return ''
