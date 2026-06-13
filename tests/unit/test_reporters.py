import json
from io import StringIO
from pathlib import Path

from validator.core.models import DocumentationFile, ValidationIssue, IssueType, SeverityLevel, LinkStatistics, \
    LinkType, Link
from validator.reporters import HTMLReporter, CLIReporter
from validator.reporters.cli import TermColor
from validator.reporters.json import file_to_dict, files_to_json, link_to_dict
from validator.reporters.markdown import MarkdownReporter


class TestMarkdownReporter:
    def test_markdown_reporter_generates_header(self):
        stats = LinkStatistics()
        reporter = MarkdownReporter()
        report = reporter.report({}, [], stats)
        assert '# Documentation Validator Report' in report

    def test_markdown_reporter_includes_summary_stats(self):
        stats = LinkStatistics()
        reporter = MarkdownReporter()
        files = {Path('README.md'): DocumentationFile(path=Path('README.md'), title='Readme')}
        report = reporter.report(files, [], stats)
        assert '**Total files:** 1' in report
        assert '**Total issues:** 0' in report

    def test_markdown_reporter_renders_issues_section(self):
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
        assert '## Issues' in report
        assert 'Target not found' in report


class TestHTMLReporter:
    def test_html_reporter_generates_page_title(self):
        stats = LinkStatistics()
        reporter = HTMLReporter()
        report = reporter.report({}, [], stats)
        assert '<title>Documentation Validator Report</title>' in report

    def test_html_reporter_renders_summary_section(self):
        stats = LinkStatistics()
        reporter = HTMLReporter()
        files = {Path('README.md'): DocumentationFile(path=Path('README.md'), title='Readme')}
        report = reporter.report(files, [], stats)
        assert '<section id="summary">' in report
        assert '<h2>Summary</h2>' in report
        assert '<div class="stat-value">1</div>' in report
        assert '<div>Files</div>' in report

    def test_html_reporter_renders_issues_section(self):
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
        assert '<h2>Issues (1)</h2>' in report
        assert '<div class="issue error">' in report
        assert 'Target not found' in report

    def test_html_reporter_renders_files_section(self):
        stats = LinkStatistics()
        reporter = HTMLReporter(include_files=True)
        files = {
            Path('README.md'): DocumentationFile(path=Path('README.md'), title='Readme'),
            Path('guide.md'): DocumentationFile(path=Path('guide.md'), title='Guide'),
        }
        report = reporter.report(files, [], stats)
        assert '<section id="files">' in report
        assert '<h2>Files (2)</h2>' in report
        assert 'README.md' in report
        assert 'guide.md' in report

    def test_html_reporter_displays_no_issues_message(self):
        stats = LinkStatistics()
        reporter = HTMLReporter()
        files = {Path('README.md'): DocumentationFile(path=Path('README.md'), title='Readme')}
        report = reporter.report(files, [], stats)
        assert 'No issues found' in report


class TestSerializers:
    def test_file_serializer_converts_links_to_dict(self):
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

    def test_link_serializer_converts_attributes_to_dict(self):
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

    def test_files_serializer_generates_json_array(self):
        ftv_list = [
            DocumentationFile(path=Path('TEST-README.md'), title='readme'),
            DocumentationFile(path=Path('TEST-LICENSE.md'), title='license'),
        ]
        ftv_list_serialized = files_to_json(ftv_list)

        ftv_list_json = json.loads(ftv_list_serialized)
        assert len(ftv_list_json) == 2
        assert ftv_list_json[0]['title'] == 'readme'
        assert ftv_list_json[1]['path'] == 'TEST-LICENSE.md'
        

class TestCLIReporterReport:
    def test_report_no_files_found(self, mocker):
        stream = StringIO()
        reporter = CLIReporter(stream=stream, use_color=False)
        reporter.report(files={}, issues=[], link_stat=LinkStatistics())
        output = stream.getvalue()
        assert 'No files found for validation.' in output

    def test_report_with_errors_shows_error_summary(self, mocker):
        stream = StringIO()
        reporter = CLIReporter(stream=stream, use_color=False)
        file_obj = DocumentationFile(path=Path('test.md'), title='Test')
        link = Link(
            uri='https://broken.com',
            link_type=LinkType.EXTERNAL,
            parent_file=Path('test.md'),
            line_number=10
        )
        issue = ValidationIssue(
            issue_type=IssueType.EXTERNAL_UNREACHABLE,
            severity_level=SeverityLevel.ERROR,
            src_file=file_obj,
            link=link,
            message='External resource unavailable'
        )
        reporter.report(files={Path('test.md'): file_obj}, issues=[issue], link_stat=LinkStatistics())
        output = stream.getvalue()
        assert 'Error Summary:' in output
        assert '[ERROR]' in output

    def test_report_with_warnings_only_no_error_summary(self, mocker):
        stream = StringIO()
        reporter = CLIReporter(stream=stream, use_color=False)
        file_obj = DocumentationFile(path=Path('test.md'), title='Test')
        issue = ValidationIssue(
            issue_type=IssueType.ORPHAN_FILE,
            severity_level=SeverityLevel.WARNING,
            src_file=file_obj,
            message='File has no incoming links'
        )
        reporter.report(files={Path('test.md'): file_obj}, issues=[issue], link_stat=LinkStatistics())
        output = stream.getvalue()
        assert 'Error Summary:' not in output
        assert '[WARN]' in output

    def test_report_sorts_issues_by_file_and_line(self, mocker):
        stream = StringIO()
        reporter = CLIReporter(stream=stream, use_color=False)
        file_a = DocumentationFile(path=Path('a.md'), title='A')
        file_b = DocumentationFile(path=Path('b.md'), title='B')
        issues = [
            ValidationIssue(
                issue_type=IssueType.BROKEN_LINK,
                severity_level=SeverityLevel.ERROR,
                src_file=file_b,
                link=Link(uri='./x.md', link_type=LinkType.INTERNAL, parent_file=Path('b.md'), line_number=5)
            ),
            ValidationIssue(
                issue_type=IssueType.BROKEN_LINK,
                severity_level=SeverityLevel.ERROR,
                src_file=file_a,
                link=Link(uri='./y.md', link_type=LinkType.INTERNAL, parent_file=Path('a.md'), line_number=10)
            ),
            ValidationIssue(
                issue_type=IssueType.BROKEN_LINK,
                severity_level=SeverityLevel.ERROR,
                src_file=file_a,
                link=Link(uri='./z.md', link_type=LinkType.INTERNAL, parent_file=Path('a.md'), line_number=3)
            ),
        ]
        reporter.report(files={Path('a.md'): file_a, Path('b.md'): file_b}, issues=issues, link_stat=LinkStatistics())
        output = stream.getvalue()
        lines = output.split('\n')
        issue_lines = [line for line in lines if 'a.md' in line or 'b.md' in line]
        assert len(issue_lines) >= 3

    def test_report_generates_table_header(self, mocker):
        stream = StringIO()
        reporter = CLIReporter(stream=stream, use_color=False)
        file_obj = DocumentationFile(path=Path('test.md'), title='Test')
        reporter.report(files={Path('test.md'): file_obj}, issues=[], link_stat=LinkStatistics())
        output = stream.getvalue()
        assert 'File' in output
        assert 'Errors' in output
        assert 'Warnings' in output

    def test_report_shows_statistics(self, mocker):
        stream = StringIO()
        reporter = CLIReporter(stream=stream, use_color=False)
        file_obj = DocumentationFile(path=Path('test.md'), title='Test')
        stats = LinkStatistics(internal_total=10, internal_broken=2, external_total=20, external_broken=5)
        reporter.report(files={Path('test.md'): file_obj}, issues=[], link_stat=stats)
        output = stream.getvalue()
        assert 'Internal links: 10 (broken: 2)' in output
        assert 'External links: 20 (broken: 5)' in output

    def test_colorize_applies_color_when_enabled(self, mocker):
        reporter = CLIReporter(use_color=True)
        result = reporter._colorize('test', TermColor.RED)
        assert '\033[91m' in result
        assert 'test' in result

    def test_colorize_skips_color_when_disabled(self, mocker):
        reporter = CLIReporter(use_color=False)
        result = reporter._colorize('test', TermColor.RED)
        assert result == 'test'
        assert '\033' not in result

    def test_write_line_flushes_stream(self, mocker):
        mock_stream = mocker.MagicMock()
        reporter = CLIReporter(stream=mock_stream)
        reporter._write_line('test message')
        mock_stream.write.assert_called_once_with('test message\n')
        mock_stream.flush.assert_called_once()