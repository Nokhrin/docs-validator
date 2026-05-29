from pathlib import Path

from validator.core.models import IssueType, SeverityLevel
from validator.rules import BrokenLinkValidator, AnchorLinkValidator


class TestBrokenLinkValidator:

    def test_broken_link_detected(self, one_file_one_broken_link, tmp_path: Path):
        validator = BrokenLinkValidator()
        issues = validator.validate(one_file_one_broken_link, tmp_path)

        assert len(issues) == 1
        assert issues[0].issue_type == IssueType.BROKEN_LINK
        assert issues[0].severity_level == SeverityLevel.ERROR

    def test_multiple_broken_links(self, one_file_multiple_broken_links, tmp_path: Path):
        """Несколько битых ссылок в одном файле."""
        validator = BrokenLinkValidator()
        issues = validator.validate(one_file_multiple_broken_links, tmp_path)

        assert len(issues) == 2
        assert all(i.issue_type == IssueType.BROKEN_LINK for i in issues)

class TestAnchorLinkValidator:

    def test_anchor_exists_no_issues(self, two_files_valid_link_with_anchor, tmp_path: Path):
        alv = AnchorLinkValidator()
        issues = alv.validate(two_files_valid_link_with_anchor, tmp_path)

        assert len(issues) == 0

    def test_anchor_missing_one_issue(self, one_file_broken_anchor, tmp_path: Path):
        alv = AnchorLinkValidator()
        issues = alv.validate(one_file_broken_anchor, tmp_path)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.issue_type == IssueType.MISSING_ANCHOR
        assert issue.severity_level == SeverityLevel.ERROR
