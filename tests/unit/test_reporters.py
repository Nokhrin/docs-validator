"""Тесты генераторов отчетов."""

from pathlib import Path

from validator.core.models import DocumentationFile, ValidationIssue, IssueType, SeverityLevel
from validator.reporters import HTMLReporter
from validator.reporters.markdown_reporter import MarkdownReporter


class TestMarkdownReporter:

    def test_report_header(self):
        """Отчет содержит заголовок."""
        reporter = MarkdownReporter()
        report = reporter.report({}, [])
        assert '# Отчет валидатора документации' in report

    def test_report_summary(self):
        """Отчет содержит сводку."""
        reporter = MarkdownReporter()
        files = {Path('README.md'): DocumentationFile(path=Path('README.md'), title='Readme')}
        report = reporter.report(files, [])
        assert '**Всего файлов:** 1' in report
        assert '**Всего проблем:** 0' in report

    def test_report_with_issues(self):
        """Отчет содержит секцию проблем."""
        reporter = MarkdownReporter()
        file = DocumentationFile(path=Path('README.md'), title='Readme')
        issues = [
            ValidationIssue(
                issue_type=IssueType.BROKEN_LINK,
                severity_level=SeverityLevel.ERROR,
                src_file=file,
                message='Target not found',
            )
        ]
        report = reporter.report({Path('README.md'): file}, issues)
        assert '## Проблемы' in report
        assert 'Target not found' in report


class TestHTMLReporter:

    def test_report_title(self):
        """Отчет содержит заголовок страницы."""
        reporter = HTMLReporter()
        report = reporter.report({}, [])
        assert '<title>Отчет валидатора документации</title>' in report

    def test_report_summary_section(self):
        """Отчет содержит секцию сводки."""
        reporter = HTMLReporter()
        files = {Path('README.md'): DocumentationFile(path=Path('README.md'), title='Readme')}
        report = reporter.report(files, [])
        assert '<section id="summary">' in report
        assert '<h2>📊 Сводка</h2>' in report
        assert '<div class="stat-value">1</div>' in report
        assert '<div>Файлов</div>' in report

    def test_report_issues_section(self):
        """Отчет содержит секцию проблем."""
        reporter = HTMLReporter()
        file = DocumentationFile(path=Path('README.md'), title='Readme')
        issues = [
            ValidationIssue(
                issue_type=IssueType.BROKEN_LINK,
                severity_level=SeverityLevel.ERROR,
                src_file=file,
                message='Target not found',
            )
        ]
        report = reporter.report({Path('README.md'): file}, issues)
        assert '<section id="issues">' in report
        assert '<h2>⚠️ Проблемы (1)</h2>' in report
        assert '<div class="issue error">' in report
        assert 'Target not found' in report

    def test_report_files_section(self):
        """Отчет содержит секцию файлов."""
        reporter = HTMLReporter()
        files = {
            Path('README.md'): DocumentationFile(path=Path('README.md'), title='Readme'),
            Path('guide.md'): DocumentationFile(path=Path('guide.md'), title='Guide'),
        }
        report = reporter.report(files, [])
        assert '<section id="files">' in report
        assert '<h2>📁 Файлы (2)</h2>' in report
        assert 'README.md' in report
        assert 'guide.md' in report

    def test_report_no_issues_message(self):
        """Отчет содержит сообщение при отсутствии проблем."""
        reporter = HTMLReporter()
        files = {Path('README.md'): DocumentationFile(path=Path('README.md'), title='Readme')}
        report = reporter.report(files, [])
        assert '✅ Проблем не обнаружено' in report