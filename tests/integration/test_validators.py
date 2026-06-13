from pathlib import Path

from validator.core.models import IssueType, SeverityLevel, DocumentationFile, Link, LinkType
from validator.rules import CircularDependencyValidator
from validator.rules.broken_link import BrokenLinkValidator
from validator.rules.orphan_file import OrphanFileValidator


class TestBrokenLinkValidator:

    def test_broken_link_validator_validate_valid_link_returns_zero_issues(self, tmp_path: Path):
        (tmp_path / 'README.md').write_text('[VALID-LINK-NO-ANCHOR](./guide.md)')
        (tmp_path / 'guide.md').write_text('# Guide')
        two_files_valid_link_no_anchor = {
            Path('README.md'): DocumentationFile(
                path=Path('README.md'),
                title='README',
                links_out={Link(
                    uri='./guide.md',
                    link_type=LinkType.INTERNAL,
                    parent_file=Path('README.md'),
                    line_number=1,
                )}
            ),
            Path('guide.md'): DocumentationFile(path=Path('guide.md'), title='Guide'),
        }

        validator = BrokenLinkValidator()
        issues = validator.validate(two_files_valid_link_no_anchor, tmp_path)

        assert len(issues) == 0


class TestOrphanFileValidator:

    def test_orphan_validator_validate_single_orphan_returns_one_issue(self, tmp_path: Path):
        (tmp_path / 'README.md').write_text('# Root')
        (tmp_path / 'orphan.md').write_text('# Orphan')

        files = {
            Path('README.md'): DocumentationFile(path=Path('README.md'), title='Root'),
            Path('orphan.md'): DocumentationFile(path=Path('orphan.md'), title='Orphan'),
        }

        validator = OrphanFileValidator()
        issues = validator.validate(files, tmp_path)

        orphan_issues = [i for i in issues if i.issue_type == IssueType.ORPHAN_FILE]
        assert len(orphan_issues) == 1
        assert orphan_issues[0].src_file.path == Path('orphan.md')

    def test_orphan_validator_validate_root_file_returns_zero_issues(self, tmp_path: Path):
        (tmp_path / 'README.md').write_text('# Root')

        files = {
            Path('README.md'): DocumentationFile(path=Path('README.md'), title='Root'),
        }

        validator = OrphanFileValidator()
        issues = validator.validate(files, tmp_path)

        orphan_issues = [i for i in issues if i.issue_type == IssueType.ORPHAN_FILE]
        assert len(orphan_issues) == 0

    def test_orphan_validator_validate_linked_file_returns_zero_issues(self, tmp_path: Path):
        (tmp_path / 'README.md').write_text('[Link](./target.md)')
        (tmp_path / 'target.md').write_text('# Target')

        link = Link(
            uri='./target.md',
            link_type=LinkType.INTERNAL,
            parent_file=Path('README.md'),
            line_number=1
        )

        files = {
            Path('README.md'): DocumentationFile(
                path=Path('README.md'), title='Root', links_out={link}
            ),
            Path('target.md'): DocumentationFile(path=Path('target.md'), title='Target'),
        }

        validator = OrphanFileValidator()
        issues = validator.validate(files, tmp_path)

        orphan_issues = [i for i in issues if i.issue_type == IssueType.ORPHAN_FILE]
        assert len(orphan_issues) == 0

    def test_orphan_validator_validate_multiple_orphans_returns_two_issues(self, tmp_path: Path):
        (tmp_path / 'README.md').write_text('# Root')
        (tmp_path / 'orphan1.md').write_text('# Orphan 1')
        (tmp_path / 'orphan2.md').write_text('# Orphan 2')

        files = {
            Path('README.md'): DocumentationFile(path=Path('README.md'), title='Root'),
            Path('orphan1.md'): DocumentationFile(path=Path('orphan1.md'), title='Orphan 1'),
            Path('orphan2.md'): DocumentationFile(path=Path('orphan2.md'), title='Orphan 2'),
        }

        validator = OrphanFileValidator()
        issues = validator.validate(files, tmp_path)

        orphan_issues = [i for i in issues if i.issue_type == IssueType.ORPHAN_FILE]
        assert len(orphan_issues) == 2


class TestCircularDependencyValidator:

    def test_circular_validator_validate_linear_graph_returns_zero_issues(self, tmp_path: Path):
        (tmp_path / 'a.md').write_text('[Link](./b.md)')
        (tmp_path / 'b.md').write_text('[Link](./c.md)')
        (tmp_path / 'c.md').write_text('# End')

        link_a_b = Link(uri='./b.md', link_type=LinkType.INTERNAL, parent_file=Path('a.md'), line_number=1)
        link_b_c = Link(uri='./c.md', link_type=LinkType.INTERNAL, parent_file=Path('b.md'), line_number=1)

        files = {
            Path('a.md'): DocumentationFile(path=Path('a.md'), title='A', links_out={link_a_b}),
            Path('b.md'): DocumentationFile(path=Path('b.md'), title='B', links_out={link_b_c}),
            Path('c.md'): DocumentationFile(path=Path('c.md'), title='C'),
        }

        validator = CircularDependencyValidator()
        issues = validator.validate(files, tmp_path)

        assert len(issues) == 0

    def test_circular_validator_validate_simple_cycle_returns_two_warning_issues(self, tmp_path: Path):
        (tmp_path / 'a.md').write_text('[Link](./b.md)')
        (tmp_path / 'b.md').write_text('[Link](./a.md)')

        link_a_b = Link(uri='./b.md', link_type=LinkType.INTERNAL, parent_file=Path('a.md'), line_number=1)
        link_b_a = Link(uri='./a.md', link_type=LinkType.INTERNAL, parent_file=Path('b.md'), line_number=1)

        files = {
            Path('a.md'): DocumentationFile(path=Path('a.md'), title='A', links_out={link_a_b}),
            Path('b.md'): DocumentationFile(path=Path('b.md'), title='B', links_out={link_b_a}),
        }

        validator = CircularDependencyValidator()
        issues = validator.validate(files, tmp_path)

        assert len(issues) == 2
        assert all(i.issue_type == IssueType.CIRCULAR_DEPENDENCY for i in issues)
        assert all(i.severity_level == SeverityLevel.WARNING for i in issues)

    def test_circular_validator_validate_self_reference_returns_one_warning_issue(self, tmp_path: Path):
        (tmp_path / 'a.md').write_text('[Self](./a.md)')

        link_a_a = Link(uri='./a.md', link_type=LinkType.INTERNAL, parent_file=Path('a.md'), line_number=1)

        files = {
            Path('a.md'): DocumentationFile(path=Path('a.md'), title='A', links_out={link_a_a}),
        }

        validator = CircularDependencyValidator()
        issues = validator.validate(files, tmp_path)

        assert len(issues) == 1
        assert issues[0].issue_type == IssueType.CIRCULAR_DEPENDENCY
        assert issues[0].severity_level == SeverityLevel.WARNING
        assert issues[0].src_file.path == Path('a.md')

    def test_circular_validator_validate_complex_cycle_returns_three_warning_issues(self, tmp_path: Path):
        (tmp_path / 'a.md').write_text('[Link](./b.md)')
        (tmp_path / 'b.md').write_text('[Link](./c.md)')
        (tmp_path / 'c.md').write_text('[Link](./a.md)')

        link_a_b = Link(uri='./b.md', link_type=LinkType.INTERNAL, parent_file=Path('a.md'), line_number=1)
        link_b_c = Link(uri='./c.md', link_type=LinkType.INTERNAL, parent_file=Path('b.md'), line_number=1)
        link_c_a = Link(uri='./a.md', link_type=LinkType.INTERNAL, parent_file=Path('c.md'), line_number=1)

        files = {
            Path('a.md'): DocumentationFile(path=Path('a.md'), title='A', links_out={link_a_b}),
            Path('b.md'): DocumentationFile(path=Path('b.md'), title='B', links_out={link_b_c}),
            Path('c.md'): DocumentationFile(path=Path('c.md'), title='C', links_out={link_c_a}),
        }

        validator = CircularDependencyValidator()
        issues = validator.validate(files, tmp_path)

        assert len(issues) == 3
        assert all(i.issue_type == IssueType.CIRCULAR_DEPENDENCY for i in issues)
        assert all(i.severity_level == SeverityLevel.WARNING for i in issues)
        issue_paths = {i.src_file.path for i in issues}
        assert issue_paths == {Path('a.md'), Path('b.md'), Path('c.md')}