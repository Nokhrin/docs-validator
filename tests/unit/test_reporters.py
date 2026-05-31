"""Тесты генераторов отчетов."""
import json
from pathlib import Path

from validator.core.models import DocumentationFile, ValidationIssue, IssueType, SeverityLevel, LinkStatistics, \
    LinkType, Link
from validator.reporters import HTMLReporter
from validator.reporters.json import file_to_dict, files_to_json, link_to_dict
from validator.reporters.markdown import MarkdownReporter


class TestMarkdownReporter:
    def test_report_header(self):
        """Отчет содержит заголовок."""
        stats = LinkStatistics()
        reporter = MarkdownReporter()
        report = reporter.report({}, [], stats)
        assert '# Отчет валидатора документации' in report

    def test_report_summary(self):
        """Отчет содержит сводку."""
        stats = LinkStatistics()
        reporter = MarkdownReporter()
        files = {Path('README.md'): DocumentationFile(path=Path('README.md'), title='Readme')}
        report = reporter.report(files, [], stats)
        assert '**Всего файлов:** 1' in report
        assert '**Всего проблем:** 0' in report

    def test_report_with_issues(self):
        """Отчет содержит секцию проблем."""
        stats = LinkStatistics()
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
        report = reporter.report({Path('README.md'): file}, issues, stats)
        assert '## Проблемы' in report
        assert 'Target not found' in report


class TestHTMLReporter:
    def test_report_title(self):
        """Отчет содержит заголовок страницы."""
        stats = LinkStatistics()
        reporter = HTMLReporter()
        report = reporter.report({}, [], stats)
        assert '<title>Отчет валидатора документации</title>' in report

    def test_report_summary_section(self):
        """Отчет содержит секцию сводки."""
        stats = LinkStatistics()
        reporter = HTMLReporter()
        files = {Path('README.md'): DocumentationFile(path=Path('README.md'), title='Readme')}
        report = reporter.report(files, [], stats)
        assert '<section id="summary">' in report
        assert '<h2>📊 Сводка</h2>' in report
        assert '<div class="stat-value">1</div>' in report
        assert '<div>Файлов</div>' in report

    def test_report_issues_section(self):
        """Отчет содержит секцию проблем."""
        stats = LinkStatistics()
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
        report = reporter.report({Path('README.md'): file}, issues, stats)
        assert '<section id="issues">' in report
        assert '<h2>⚠️ Проблемы (1)</h2>' in report
        assert '<div class="issue error">' in report
        assert 'Target not found' in report

    def test_report_files_section(self):
        """Отчет содержит секцию файлов."""
        stats = LinkStatistics()
        reporter = HTMLReporter(include_files=True)
        files = {
            Path('README.md'): DocumentationFile(path=Path('README.md'), title='Readme'),
            Path('guide.md'): DocumentationFile(path=Path('guide.md'), title='Guide'),
        }
        report = reporter.report(files, [], stats)
        assert '<section id="files">' in report
        assert '<h2>📁 Файлы (2)</h2>' in report
        assert 'README.md' in report
        assert 'guide.md' in report

    def test_report_no_issues_message(self):
        """Отчет содержит сообщение при отсутствии проблем."""
        stats = LinkStatistics()
        reporter = HTMLReporter()
        files = {Path('README.md'): DocumentationFile(path=Path('README.md'), title='Readme')}
        report = reporter.report(files, [], stats)
        assert '✅ Проблем не обнаружено' in report


class TestSerializers:
    def test_file_with_links_to_dict_success(self):
        ftv = DocumentationFile(
            path=Path('TEST-README.md'),
            title='TEST-README-TITLE',
            links_out={
                Link('./guide.md', LinkType.INTERNAL, Path('TEST-README.md'), 1, 'section1')
            }
        )
        ftv_serialized = file_to_dict(ftv)

        assert len(ftv_serialized['links_out']) == 1
        assert ftv_serialized['links_out'][0]['uri'] == './guide.md'

    def test_link_to_dict_success(self):
        link = Link('./guide.md', LinkType.INTERNAL, Path('TEST-README.md'), 1, 'section1')
        expected = {
            'uri': './guide.md',
            'link_type': 'INTERNAL',
            'source_file': 'TEST-README.md',
            'line_number': 1,
            'anchor': 'section1',
        }
        actual = link_to_dict(link)

        assert actual == expected

    def test_files_to_json_success(self):
        ftv_list = [
            DocumentationFile(path=Path('TEST-README.md'), title='readme'),
            DocumentationFile(path=Path('TEST-LICENSE.md'), title='license'),
        ]
        ftv_list_serialized = files_to_json(ftv_list)

        ftv_list_json = json.loads(ftv_list_serialized)
        assert len(ftv_list_json) == 2
        assert ftv_list_json[0]['title'] == 'readme'
        assert ftv_list_json[1]['path'] == 'TEST-LICENSE.md'
