"""Тесты для валидаторов."""
from pathlib import Path

import pytest

from validator.core.models import IssueType, SeverityLevel
from validator.validators import AnchorLinkValidator
from validator.validators.broken_link import BrokenLinkValidator
from validator.validators.orphan_file import OrphanFileValidator


class TestBrokenLinkValidator:

    def test_broken_link_detected(self, one_file_broken_link, temp_docs_dir):
        validator = BrokenLinkValidator()
        issues = validator.validate(one_file_broken_link, temp_docs_dir)

        assert len(issues) == 1
        assert issues[0].issue_type == IssueType.BROKEN_LINK
        assert issues[0].severity_level == SeverityLevel.ERROR

    def test_valid_link_no_issues(self, two_files_valid_link_no_anchor, temp_docs_dir):
        validator = BrokenLinkValidator()
        issues = validator.validate(two_files_valid_link_no_anchor, temp_docs_dir)

        assert len(issues) == 0


class TestOrphanFileValidator:

    def test_orphan_file_detected(self, two_files_one_orphan, temp_docs_dir):
        ofv = OrphanFileValidator()
        issues = ofv.validate(two_files_one_orphan, temp_docs_dir)
        orphan_issues = [i for i in issues if i.issue_type == IssueType.ORPHAN_FILE]
        assert len(orphan_issues) == 1
        assert orphan_issues[0].src_file.path == Path("orphan.md")

    def test_one_root_file_no_orphans(self, root_md_file, temp_docs_dir):
        validator = OrphanFileValidator()
        issues = validator.validate(root_md_file, temp_docs_dir)

        orphan_issues = [i for i in issues if i.issue_type == IssueType.ORPHAN_FILE]
        assert len(orphan_issues) == 0

    def test_linked_file_not_orphan(self, two_files_valid_link_no_anchor, temp_docs_dir):
        validator = OrphanFileValidator()
        issues = validator.validate(two_files_valid_link_no_anchor, temp_docs_dir)

        orphan_issues = [i for i in issues if i.issue_type == IssueType.ORPHAN_FILE]
        assert len(orphan_issues) == 0


class TestAnchorLinkValidator:

    @pytest.mark.skip(reason='заглушка (Спринт 3)')
    def test_anchor_validator_stub(self, two_files_valid_link_with_anchor, temp_docs_dir):
        # TODO
        validator = AnchorLinkValidator()
        issues = validator.validate(two_files_valid_link_with_anchor, temp_docs_dir)

        assert issues == []
