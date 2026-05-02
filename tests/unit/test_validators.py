"""Тесты для валидаторов."""
from pathlib import Path
from wsgiref.validate import validator

import pytest

from validator.core.models import IssueType, SeverityLevel, DocumentationFile, Link, LinkType
from validator.validators import AnchorLinkValidator, CircularDependencyValidator
from validator.validators.broken_link import BrokenLinkValidator
from validator.validators.orphan_file import OrphanFileValidator


class TestBrokenLinkValidator:

    def test_broken_link_detected(self, one_file_one_broken_link, temp_docs_dir):
        validator = BrokenLinkValidator()
        issues = validator.validate(one_file_one_broken_link, temp_docs_dir)

        assert len(issues) == 1
        assert issues[0].issue_type == IssueType.BROKEN_LINK
        assert issues[0].severity_level == SeverityLevel.ERROR

    def test_valid_link_no_issues(self, two_files_valid_link_no_anchor, temp_docs_dir):
        validator = BrokenLinkValidator()
        issues = validator.validate(two_files_valid_link_no_anchor, temp_docs_dir)

        assert len(issues) == 0

    def test_multiple_broken_links(self, one_file_multiple_broken_links, temp_docs_dir):
        """Несколько битых ссылок в одном файле."""
        validator = BrokenLinkValidator()
        issues = validator.validate(one_file_multiple_broken_links, temp_docs_dir)

        assert len(issues) == 2
        assert all(i.issue_type == IssueType.BROKEN_LINK for i in issues)


class TestOrphanFileValidator:

    def test_orphan_file_detected(self, one_root_one_orphan, temp_docs_dir):
        ofv = OrphanFileValidator()
        issues = ofv.validate(one_root_one_orphan, temp_docs_dir)
        orphan_issues = [i for i in issues if i.issue_type == IssueType.ORPHAN_FILE]
        assert len(orphan_issues) == 1

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

    def test_multiple_orphans(self, one_root_two_orphans, temp_docs_dir):
        """Несколько файлов-сирот."""
        validator = OrphanFileValidator()
        issues = validator.validate(one_root_two_orphans, temp_docs_dir)
        orphan_issues = [i for i in issues if i.issue_type == IssueType.ORPHAN_FILE]

        assert len(orphan_issues) == 2


class TestAnchorLinkValidator:

    def test_anchor_exists_no_issues(self, two_files_valid_link_with_anchor, temp_docs_dir):
        alv = AnchorLinkValidator()
        issues = alv.validate(two_files_valid_link_with_anchor, temp_docs_dir)

        assert len(issues) == 0

    def test_anchor_missing_one_issue(self, one_file_broken_anchor, temp_docs_dir):
        alv = AnchorLinkValidator()
        issues = alv.validate(one_file_broken_anchor, temp_docs_dir)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.issue_type == IssueType.MISSING_ANCHOR
        assert issue.severity_level == SeverityLevel.ERROR


class TestCircularDependencyValidator:
    def test_no_cycle_no_issues(self, three_files_no_cycles, temp_docs_dir):
        """Линейная цепочка без циклов не генерирует issues."""
        cdv = CircularDependencyValidator()
        issues = cdv.validate(three_files_no_cycles, temp_docs_dir)

        assert len(issues) == 0

    def test_simple_cycle_detected(self, two_files_circular_dep, temp_docs_dir):
        """Простой цикл A->B->A обнаруживается."""
        cdv= CircularDependencyValidator()
        issues = cdv.validate(two_files_circular_dep, temp_docs_dir)

        assert len(issues) == 2
        assert all(i.issue_type == IssueType.CIRCULAR_DEPENDENCY for i in issues)
        assert all(i.severity_level == SeverityLevel.WARNING for i in issues)

