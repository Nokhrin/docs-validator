from pathlib import Path

import pytest
import requests
import responses

from validator.core.models import DocumentationFile, Link, LinkType, SeverityLevel, IssueType
from validator.rules.external_link import ExternalLinkValidator


class TestExternalLinkValidator:
    def test_is_host_ignored_exact_match_true(self):
        validator = ExternalLinkValidator(hosts_to_ignore=['example.com'])
        assert validator._is_host_ignored('example.com') is True

    def test_is_host_ignored_subdomain_match_true(self):
        validator = ExternalLinkValidator(hosts_to_ignore=['example.com'])
        assert validator._is_host_ignored('sub.example.com') is True

    def test_is_host_ignored_nested_subdomain_match_true(self):
        validator = ExternalLinkValidator(hosts_to_ignore=['example.com'])
        assert validator._is_host_ignored('a.b.example.com') is True

    def test_is_host_ignored_different_domain_false(self):
        validator = ExternalLinkValidator(hosts_to_ignore=['example.com'])
        assert validator._is_host_ignored('other.com') is False

    def test_is_host_ignored_partial_match_false(self):
        validator = ExternalLinkValidator(hosts_to_ignore=['example.com'])
        assert validator._is_host_ignored('example.com.evil.com') is False

    def test_is_host_ignored_localhost_exact_match_true(self):
        validator = ExternalLinkValidator(hosts_to_ignore=['localhost'])
        assert validator._is_host_ignored('localhost') is True

    def test_is_host_ignored_localhost_subdomain_match_true(self):
        validator = ExternalLinkValidator(hosts_to_ignore=['localhost'])
        assert validator._is_host_ignored('test.localhost') is True

    def test_is_host_ignored_empty_hostname_false(self):
        validator = ExternalLinkValidator(hosts_to_ignore=['example.com'])
        assert validator._is_host_ignored('') is False

    @pytest.fixture
    def validator(self):
        return ExternalLinkValidator()

    @pytest.fixture
    def link(self):
        return Link(
            uri='https://example.com/test',
            link_type=LinkType.EXTERNAL,
            parent_file=Path('test.md'),
            line_number=1
        )

    @pytest.fixture
    def src_file(self):
        return DocumentationFile(path=Path('test.md'), title='Test')

    @pytest.mark.parametrize('status_code,expected_severity', [
        # Success - no issue
        (200, None),
        (204, None),
        (301, None),

        # Guaranteed error - resource definitely missing
        (404, SeverityLevel.ERROR),
        (410, SeverityLevel.ERROR),

        # Ambiguous error - manual verification required
        (400, SeverityLevel.WARNING),
        (401, SeverityLevel.WARNING),
        (403, SeverityLevel.WARNING),
        (406, SeverityLevel.WARNING),
        (429, SeverityLevel.WARNING),
        (500, SeverityLevel.WARNING),
        (503, SeverityLevel.WARNING),
        (520, SeverityLevel.WARNING),
        (521, SeverityLevel.WARNING),
        (522, SeverityLevel.WARNING),
        (523, SeverityLevel.WARNING),
        (524, SeverityLevel.WARNING),
        (525, SeverityLevel.WARNING),
    ])
    def test_check_single_link_http_status_codes_returns_expected_severity(
            self, validator, link, src_file, status_code, expected_severity, mocker
    ):
        mock_session = mocker.MagicMock()
        mock_response = mocker.MagicMock()
        mock_response.status_code = status_code
        mock_session.head.return_value = mock_response
        mock_session.get.return_value = mock_response

        issue = validator._check_single_link(link, src_file, mock_session)

        if expected_severity is None:
            assert issue is None
        else:
            assert issue is not None
            assert issue.severity_level == expected_severity
            assert issue.issue_type == IssueType.EXTERNAL_UNREACHABLE

    def test_check_single_link_network_error_returns_warning(self, validator, link, src_file, mocker):
        mock_session = mocker.MagicMock()
        mock_session.head.side_effect = requests.exceptions.ConnectionError("DNS fail")

        issue = validator._check_single_link(link, src_file, mock_session)

        assert issue is not None
        assert issue.severity_level == SeverityLevel.WARNING
        assert issue.issue_type == IssueType.EXTERNAL_UNREACHABLE
        assert 'manual verification required' in issue.message.lower()

    def test_check_single_link_timeout_returns_warning(self, validator, link, src_file, mocker):
        mock_session = mocker.MagicMock()
        mock_session.head.side_effect = requests.exceptions.Timeout("Connection timed out")

        issue = validator._check_single_link(link, src_file, mock_session)

        assert issue is not None
        assert issue.severity_level == SeverityLevel.WARNING
        assert issue.issue_type == IssueType.EXTERNAL_UNREACHABLE

    @responses.activate
    def test_check_single_link_head_returns_403_get_returns_200_no_issue(self):
        url = 'https://www.rfc-editor.org/rfc/rfc9110.html'
        responses.add(responses.HEAD, url, status=403)
        responses.add(responses.GET, url, status=200)

        validator = ExternalLinkValidator()
        link = Link(uri=url, link_type=LinkType.EXTERNAL, parent_file=Path('test.md'), line_number=1)
        file = DocumentationFile(path=Path('test.md'), title='Test', links_out={link})

        with requests.Session() as session:
            issue = validator._check_single_link(link, file, session)

        assert issue is None

    @responses.activate
    def test_check_single_link_head_returns_404_get_returns_200_no_issue(self):
        url = 'https://example.com/resource'
        responses.add(responses.HEAD, url, status=404)
        responses.add(responses.GET, url, status=200)

        validator = ExternalLinkValidator()
        link = Link(uri=url, link_type=LinkType.EXTERNAL, parent_file=Path('test.md'), line_number=1)
        file = DocumentationFile(path=Path('test.md'), title='Test', links_out={link})

        with requests.Session() as session:
            issue = validator._check_single_link(link, file, session)

        assert issue is None

    @responses.activate
    def test_check_single_link_head_returns_500_get_returns_200_no_issue(self):
        url = 'https://example.com/resource'
        responses.add(responses.HEAD, url, status=500)
        responses.add(responses.GET, url, status=200)

        validator = ExternalLinkValidator()
        link = Link(uri=url, link_type=LinkType.EXTERNAL, parent_file=Path('test.md'), line_number=1)
        file = DocumentationFile(path=Path('test.md'), title='Test', links_out={link})

        with requests.Session() as session:
            issue = validator._check_single_link(link, file, session)

        assert issue is None

    @responses.activate
    def test_check_single_link_head_and_get_both_return_404_error_issue(self):
        url = 'https://example.com/missing'
        responses.add(responses.HEAD, url, status=404)
        responses.add(responses.GET, url, status=404)

        validator = ExternalLinkValidator()
        link = Link(uri=url, link_type=LinkType.EXTERNAL, parent_file=Path('test.md'), line_number=1)
        file = DocumentationFile(path=Path('test.md'), title='Test', links_out={link})

        with requests.Session() as session:
            issue = validator._check_single_link(link, file, session)

        assert issue is not None
        assert issue.issue_type == IssueType.EXTERNAL_UNREACHABLE
        assert issue.severity_level == SeverityLevel.ERROR
