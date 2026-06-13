from pathlib import Path

import requests
import responses

from validator.core.models import DocumentationFile, Link, LinkType, SeverityLevel, IssueType
from validator.rules import ExternalLinkValidator


class TestExternalLinkValidatorValidate:

    @responses.activate
    def test_validate_skips_non_http_schemes_no_requests_made(self):
        validator = ExternalLinkValidator()
        mailto_link = Link(uri='mailto:test@example.com', link_type=LinkType.EXTERNAL, parent_file=Path('a.md'), line_number=1)
        tel_link = Link(uri='tel:+1234567890', link_type=LinkType.EXTERNAL, parent_file=Path('a.md'), line_number=2)
        ftp_link = Link(uri='ftp://files.example.com/doc', link_type=LinkType.EXTERNAL, parent_file=Path('a.md'), line_number=3)
        files = {Path('a.md'): DocumentationFile(path=Path('a.md'), title='A', links_out={mailto_link, tel_link, ftp_link})}
        issues = validator.validate(files, Path('/tmp'))
        assert len(issues) == 0
        assert len(responses.calls) == 0

    @responses.activate
    def test_validate_processes_only_http_https_schemes(self):
        responses.add(responses.HEAD, 'https://valid.com', status=200)
        responses.add(responses.HEAD, 'http://valid2.com', status=200)
        validator = ExternalLinkValidator()
        http_link = Link(uri='http://valid2.com', link_type=LinkType.EXTERNAL, parent_file=Path('a.md'), line_number=1)
        https_link = Link(uri='https://valid.com', link_type=LinkType.EXTERNAL, parent_file=Path('a.md'), line_number=2)
        mailto_link = Link(uri='mailto:test@example.com', link_type=LinkType.EXTERNAL, parent_file=Path('a.md'), line_number=3)
        files = {Path('a.md'): DocumentationFile(path=Path('a.md'), title='A', links_out={http_link, https_link, mailto_link})}
        issues = validator.validate(files, Path('/tmp'))
        assert len(issues) == 0
        assert len(responses.calls) == 2

    @responses.activate
    def test_validate_hostname_case_normalized_before_check(self):
        responses.add(responses.HEAD, 'https://EXAMPLE.COM/test', status=200)
        validator = ExternalLinkValidator(hosts_to_ignore=['example.com'])
        link = Link(uri='https://EXAMPLE.COM/test', link_type=LinkType.EXTERNAL, parent_file=Path('a.md'), line_number=1)
        files = {Path('a.md'): DocumentationFile(path=Path('a.md'), title='A', links_out={link})}
        issues = validator.validate(files, Path('/tmp'))
        assert len(issues) == 0
        assert len(responses.calls) == 0

    @responses.activate
    def test_validate_subdomain_case_normalized_before_check(self):
        responses.add(responses.HEAD, 'https://SUB.Example.COM/test', status=200)
        validator = ExternalLinkValidator(hosts_to_ignore=['example.com'])
        link = Link(uri='https://SUB.Example.COM/test', link_type=LinkType.EXTERNAL, parent_file=Path('a.md'), line_number=1)
        files = {Path('a.md'): DocumentationFile(path=Path('a.md'), title='A', links_out={link})}
        issues = validator.validate(files, Path('/tmp'))
        assert len(issues) == 0
        assert len(responses.calls) == 0

    @responses.activate
    def test_validate_external_link_unreachable_issue_created(self):
        url = 'https://example.com/missing'
        responses.add(responses.HEAD, url, status=404)
        validator = ExternalLinkValidator()
        link = Link(uri=url, link_type=LinkType.EXTERNAL, parent_file=Path('test.md'), line_number=1)
        file = DocumentationFile(path=Path('test.md'), title='Test', links_out={link})
        files = {Path('test.md'): file}
        issues = validator.validate(files, Path('/tmp'))
        assert len(issues) == 1
        assert issues[0].issue_type == IssueType.EXTERNAL_UNREACHABLE
        assert issues[0].severity_level == SeverityLevel.ERROR

    @responses.activate
    def test_validate_external_link_connection_error_issue_created(self):
        url = 'https://example.com/timeout'
        responses.add(responses.HEAD, url, body=requests.exceptions.ConnectionError('DNS fail'))
        validator = ExternalLinkValidator()
        link = Link(uri=url, link_type=LinkType.EXTERNAL, parent_file=Path('test.md'), line_number=1)
        file = DocumentationFile(path=Path('test.md'), title='Test', links_out={link})
        files = {Path('test.md'): file}
        issues = validator.validate(files, Path('/tmp'))
        assert len(issues) == 1
        assert issues[0].issue_type == IssueType.EXTERNAL_UNREACHABLE
        assert issues[0].severity_level == SeverityLevel.ERROR

    @responses.activate
    def test_validate_internal_links_skipped_no_requests(self):
        responses.add(responses.HEAD, 'https://valid.com', status=200)
        validator = ExternalLinkValidator(hosts_to_ignore=['ignored.com'])
        internal_link = Link(uri='./guide.md', link_type=LinkType.INTERNAL, parent_file=Path('a.md'), line_number=1)
        ignored_link = Link(uri='https://ignored.com', link_type=LinkType.EXTERNAL, parent_file=Path('a.md'), line_number=2)
        external_link = Link(uri='https://valid.com', link_type=LinkType.EXTERNAL, parent_file=Path('a.md'), line_number=3)
        files = {Path('a.md'): DocumentationFile(path=Path('a.md'), title='A', links_out={internal_link, ignored_link, external_link})}
        issues = validator.validate(files, Path('/tmp'))
        assert len(issues) == 0
        assert len(responses.calls) == 1

    def test_validate_no_external_links_empty_result(self):
        validator = ExternalLinkValidator()
        internal_link = Link(uri='./guide.md', link_type=LinkType.INTERNAL, parent_file=Path('a.md'), line_number=1)
        files = {Path('a.md'): DocumentationFile(path=Path('a.md'), title='A', links_out={internal_link})}
        issues = validator.validate(files, Path('/tmp'))
        assert issues == []