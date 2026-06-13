from pathlib import Path

from validator.core.models import IssueType, SeverityLevel
from validator.rules import CircularDependencyValidator
from validator.rules.broken_link import BrokenLinkValidator
from validator.rules.orphan_file import OrphanFileValidator


class TestAnchorLinkValidator:

    def test_valid_link_no_issues(self, two_files_valid_link_no_anchor, tmp_path: Path):
        validator = BrokenLinkValidator()
        issues = validator.validate(two_files_valid_link_no_anchor, tmp_path)

        assert len(issues) == 0


class TestOrphanFileValidator:

    def test_orphan_file_detected(self, one_root_one_orphan, tmp_path: Path):
        ofv = OrphanFileValidator()
        issues = ofv.validate(one_root_one_orphan, tmp_path)
        orphan_issues = [i for i in issues if i.issue_type == IssueType.ORPHAN_FILE]
        assert len(orphan_issues) == 1

    def test_one_root_file_no_orphans(self, one_md_file_in_root, tmp_path: Path):
        validator = OrphanFileValidator()
        issues = validator.validate(one_md_file_in_root, tmp_path)

        orphan_issues = [i for i in issues if i.issue_type == IssueType.ORPHAN_FILE]
        assert len(orphan_issues) == 0

    def test_linked_file_not_orphan(self, two_files_valid_link_no_anchor, tmp_path: Path):
        validator = OrphanFileValidator()
        issues = validator.validate(two_files_valid_link_no_anchor, tmp_path)

        orphan_issues = [i for i in issues if i.issue_type == IssueType.ORPHAN_FILE]
        assert len(orphan_issues) == 0

    def test_multiple_orphans(self, one_root_two_orphans, tmp_path: Path):
        validator = OrphanFileValidator()
        issues = validator.validate(one_root_two_orphans, tmp_path)
        orphan_issues = [i for i in issues if i.issue_type == IssueType.ORPHAN_FILE]

        assert len(orphan_issues) == 2



class TestCircularDependencyValidator:
    def test_no_cycle_no_issues(self, three_files_no_cycles, tmp_path: Path):
        cdv = CircularDependencyValidator()
        issues = cdv.validate(three_files_no_cycles, tmp_path)

        assert len(issues) == 0

    def test_simple_cycle_detected(self, two_files_circular_dep, tmp_path: Path):
        cdv= CircularDependencyValidator()
        issues = cdv.validate(two_files_circular_dep, tmp_path)

        assert len(issues) == 2
        assert all(i.issue_type == IssueType.CIRCULAR_DEPENDENCY for i in issues)
        assert all(i.severity_level == SeverityLevel.WARNING for i in issues)

