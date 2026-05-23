"""
Отчет в markdown.
"""
from pathlib import Path

from validator.core.models import DocumentationFile, ValidationIssue, LinkStatistics
from validator.reporters.base_reporter import BaseReporter


class MarkdownReporter(BaseReporter):
    """Возвращает отчет в формате markdown."""

    def report(
            self,
            files: dict[Path, DocumentationFile],
            issues: list[ValidationIssue],
            link_stat: LinkStatistics = None,
    ) -> str:
        report_lines = [
            '# Отчет валидатора документации',
            '',
            '## Сводка',
            '',
            f'**Всего файлов:** {len(files)}',
            f'**Всего проблем:** {len(issues)}',
            '',
        ]

        if link_stat is not None:
            report_lines.extend([
                f'**Внутренних ссылок:** {link_stat.internal_total}',
                f'**Внешних ссылок:** {link_stat.external_total} (доступно: {link_stat.external_valid}, недоступно: {link_stat.external_broken})',
            ])

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

        # files
        report_lines.extend([
            '## Файлы',
            '',
        ])
        for file in sorted(files.values(), key=lambda f: f.path):
            report_lines.append(f'- `{file.path}` — {file.title}')

        return '\n'.join(report_lines)
