from pathlib import Path

import requests
import responses

from validator.core.models import DocumentationFile, Link, LinkType, SeverityLevel, IssueType
from validator.rules import ExternalLinkValidator


class TestExternalLinkValidator:
    def test_is_host_ignored_subdomain_and_case(self):
        validator = ExternalLinkValidator(hosts_to_ignore=["Example.COM"])
        assert validator._is_host_ignored("https://SUB.EXAMPLE.COM/docs") is True

    def test_is_host_ignored_strict_match_no_false_positives(self):
        validator = ExternalLinkValidator(hosts_to_ignore=["localhost"])
        assert validator._is_host_ignored("https://localhost-api.com/test") is False
    
    
    @responses.activate
    def test_check_missed_target_issue_created(self):
        url = "https://example.com/missing"
        responses.add(responses.HEAD, url, status=404)
    
        validator = ExternalLinkValidator()
        link = Link(uri=url, link_type=LinkType.EXTERNAL, parent_file=Path("test.md"), line_number=1)
        file = DocumentationFile(path=Path("test.md"), title="Test")
    
        with requests.Session() as session:
            issue = validator._check_single_link(link, file, session)
    
        assert issue.issue_type == IssueType.EXTERNAL_UNREACHABLE
        assert issue.severity_level == SeverityLevel.ERROR

    
    @responses.activate
    def test_check_target_not_available_issue_created(self):
        url = "https://example.com/timeout"
        responses.add(responses.HEAD, url, body=requests.exceptions.ConnectionError("DNS fail"))
    
        validator = ExternalLinkValidator()
        link = Link(uri=url, link_type=LinkType.EXTERNAL, parent_file=Path("test.md"), line_number=1)
        file = DocumentationFile(path=Path("test.md"), title="Test")
    
        with requests.Session() as session:
            issue = validator._check_single_link(link, file, session)

        assert issue.issue_type == IssueType.EXTERNAL_UNREACHABLE
        assert issue.severity_level == SeverityLevel.ERROR

    @responses.activate
    def test_internal_and_external_valid_proccessed_missing_skipped_one_request_no_issue(self):
        responses.add(responses.HEAD, "https://valid.com", status=200)

        validator = ExternalLinkValidator(hosts_to_ignore=["ignored.com"])
        root = Path("/tmp")

        internal_link = Link(uri="./guide.md", link_type=LinkType.INTERNAL, parent_file=Path("a.md"), line_number=1)
        ignored_link = Link(uri="https://ignored.com", link_type=LinkType.EXTERNAL, parent_file=Path("a.md"),
                            line_number=2)
        external_link = Link(uri="https://valid.com", link_type=LinkType.EXTERNAL, parent_file=Path("a.md"),
                             line_number=3)

        files = {
            Path("a.md"): DocumentationFile(
                path=Path("a.md"), title="A",
                links_out={internal_link, ignored_link, external_link}
            )
        }

        issues = validator.validate(files, root)
        assert len(issues) == 0
        assert len(responses.calls) == 1

    def test_validate_empty_no_external_links(self):
        validator = ExternalLinkValidator()
        internal_link = Link(uri="./guide.md", link_type=LinkType.INTERNAL, parent_file=Path("a.md"), line_number=1)
        files = {Path("a.md"): DocumentationFile(path=Path("a.md"), title="A", links_out={internal_link})}

        issues = validator.validate(files, Path("/tmp"))
        assert issues == []