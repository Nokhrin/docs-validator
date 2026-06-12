"""Markdown report generator."""
from pathlib import Path
from validator.core.models import DocumentationFile, ValidationIssue, LinkStatistics
from validator.reporters.base import BaseReporter

class MarkdownReporter(BaseReporter):
    """Returns a report in markdown format."""
    def __init__(self, include_files: bool = False):
        self.include_files = include_files

    def report(
        self,
        files: dict[Path, DocumentationFile],
        issues: list[ValidationIssue],
        link_stat: LinkStatistics,
    ) -> str:
        report_lines = [
            '# Documentation Validator Report',
            '',
        ]
        if issues:
            report_lines.extend(['## Issues', ''])
            for issue in issues:
                report_lines.append(f'- {issue.severity_level.value}: {issue.message}')
                if issue.link:
                    report_lines.append(f'  - File: `{issue.src_file.path}`:line {issue.link.line_number}')
            report_lines.append('')

        if self.include_files:
            report_lines.extend(['## Files', ''])
            path_width = max((len(str(f.path)) for f in files.values()), default=40)
            title_width = max((len(f.title) for f in files.values()), default=20)
            report_lines.append(f'{"File":<{path_width}}  {"Title":<{title_width}}  Links')
            report_lines.append('-' * (path_width + title_width + 10))
            for file in sorted(files.values(), key=lambda f: f.path):
                report_lines.append(f'{str(file.path):<{path_width}}  {file.title:<{title_width}}  {len(file.links_out)}')
            report_lines.append('')

        report_lines.extend([
            '',
            '## Summary',
            '',
            f'**Total files:** {len(files)}',
            f'**Total issues:** {len(issues)}',
            f'**Internal links:** {link_stat.internal_total} (broken: {link_stat.internal_broken})',
            f'**External links:** {link_stat.external_total} (broken: {link_stat.external_broken})',
            '',
        ])
        return '\n'.join(report_lines)