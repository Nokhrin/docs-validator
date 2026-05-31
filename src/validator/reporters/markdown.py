"""
Отчет в markdown.
"""
from pathlib import Path

from validator.core.models import DocumentationFile, ValidationIssue, LinkStatistics
from validator.reporters.base import BaseReporter


class MarkdownReporter(BaseReporter):
    """Возвращает отчет в формате markdown."""

    def __init__(self, include_files: bool = False):
        self.include_files = include_files

    def report(
            self,
            files: dict[Path, DocumentationFile],
            issues: list[ValidationIssue],
            link_stat: LinkStatistics,
    ) -> str:
        report_lines = [
            '# Отчет валидатора документации',
            '',
        ]

        # issues
        if issues:
            report_lines.extend([
                '## Проблемы',
                '',
            ])
            for issue in issues:
                report_lines.append(
                    f'- {issue.severity_level.value}: '
                    f'{issue.message}'
                )
                if issue.link:
                    report_lines.append(
                        f'  - Файл: `{issue.src_file.path}`:строка {issue.link.line_number}'
                    )
            report_lines.append('')

        if self.include_files:
            # files
            report_lines.append('## Файлы')
            report_lines.append('')
            path_width = max((len(str(f.path)) for f in files.values()), default=40)
            title_width = max((len(f.title) for f in files.values()), default=20)
            report_lines.append(f'{"Файл":<{path_width}}  {"Заголовок":<{title_width}}  Ссылок')
            report_lines.append('-' * (path_width + title_width + 10))
            for file in sorted(files.values(), key=lambda f: f.path):
                report_lines.append(
                    f'{str(file.path):<{path_width}}  {file.title:<{title_width}}  {len(file.links_out)}'
                )
            report_lines.append('')

        # total
        report_lines.extend([
            '',
            '## Сводка',
            '',
            f'**Всего файлов:** {len(files)}',
            f'**Всего проблем:** {len(issues)}',
            f'**Внутренних ссылок:** {link_stat.internal_total} (битых: {link_stat.internal_broken})',
            f'**Внешних ссылок:** {link_stat.external_total} (битых: {link_stat.external_broken})',
            '',
        ])

        return '\n'.join(report_lines)
