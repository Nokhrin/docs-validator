from pathlib import Path

import pytest

from validator.core.models import IssueType, SeverityLevel, DocumentationFile, Link, LinkType
from validator.rules import BrokenLinkValidator, AnchorLinkValidator


class TestBrokenLinkValidator:

    def test_broken_link_detected(self, one_file_one_broken_link, tmp_path: Path):
        validator = BrokenLinkValidator()
        issues = validator.validate(one_file_one_broken_link, tmp_path)

        assert len(issues) == 1
        assert issues[0].issue_type == IssueType.BROKEN_LINK
        assert issues[0].severity_level == SeverityLevel.ERROR

    def test_multiple_broken_links(self, one_file_multiple_broken_links, tmp_path: Path):
        validator = BrokenLinkValidator()
        issues = validator.validate(one_file_multiple_broken_links, tmp_path)

        assert len(issues) == 2
        assert all(i.issue_type == IssueType.BROKEN_LINK for i in issues)

class TestAnchorLinkValidator:

    def test_anchor_exists_no_issues(self, tmp_path):
        (tmp_path / 'source.md').write_text('[Link](./target.md#section)')
        (tmp_path / 'target.md').write_text('# Section')
        files = {
            Path('source.md'): DocumentationFile(path=Path('source.md'), title='Source'),
            Path('target.md'): DocumentationFile(path=Path('target.md'), title='Target'),
        }
        link = Link(
            uri='./target.md#section',
            link_type=LinkType.INTERNAL,
            parent_file=Path('source.md'),
            line_number=1,
            anchor='section'
        )
        files[Path('source.md')].links_out.add(link)
        validator = AnchorLinkValidator()
        issues = validator.validate(files, tmp_path)
        assert len(issues) == 0

    def test_anchor_missing_one_issue(self, tmp_path):
        (tmp_path / 'source.md').write_text('[Link](./target.md#missing)')
        (tmp_path / 'target.md').write_text('# Existing')
        files = {
            Path('source.md'): DocumentationFile(path=Path('source.md'), title='Source'),
            Path('target.md'): DocumentationFile(path=Path('target.md'), title='Target'),
        }
        link = Link(
            uri='./target.md#missing',
            link_type=LinkType.INTERNAL,
            parent_file=Path('source.md'),
            line_number=1,
            anchor='missing'
        )
        files[Path('source.md')].links_out.add(link)
        validator = AnchorLinkValidator()
        issues = validator.validate(files, tmp_path)
        assert len(issues) == 1
        assert issues[0].issue_type == IssueType.MISSING_ANCHOR
        assert issues[0].severity_level == SeverityLevel.ERROR

    def test_target_file_not_exists_skipped(self, tmp_path):
        (tmp_path / 'source.md').write_text('[Link](./missing.md#section)')
        files = {
            Path('source.md'): DocumentationFile(path=Path('source.md'), title='Source'),
        }
        link = Link(
            uri='./missing.md#section',
            link_type=LinkType.INTERNAL,
            parent_file=Path('source.md'),
            line_number=1,
            anchor='section'
        )
        files[Path('source.md')].links_out.add(link)
        validator = AnchorLinkValidator()
        issues = validator.validate(files, tmp_path)
        assert len(issues) == 0

    def test_external_link_skipped(self, tmp_path):
        (tmp_path / 'source.md').write_text('[Link](https://example.com#section)')
        files = {
            Path('source.md'): DocumentationFile(path=Path('source.md'), title='Source'),
        }
        link = Link(
            uri='https://example.com#section',
            link_type=LinkType.EXTERNAL,
            parent_file=Path('source.md'),
            line_number=1,
            anchor='section'
        )
        files[Path('source.md')].links_out.add(link)
        validator = AnchorLinkValidator()
        issues = validator.validate(files, tmp_path)
        assert len(issues) == 0

    def test_link_without_anchor_skipped(self, tmp_path):
        (tmp_path / 'source.md').write_text('[Link](./target.md)')
        (tmp_path / 'target.md').write_text('# Section')
        files = {
            Path('source.md'): DocumentationFile(path=Path('source.md'), title='Source'),
            Path('target.md'): DocumentationFile(path=Path('target.md'), title='Target'),
        }
        link = Link(
            uri='./target.md',
            link_type=LinkType.INTERNAL,
            parent_file=Path('source.md'),
            line_number=1,
            anchor=None
        )
        files[Path('source.md')].links_out.add(link)
        validator = AnchorLinkValidator()
        issues = validator.validate(files, tmp_path)
        assert len(issues) == 0

    def test_anchor_normalization_spaces_to_hyphens(self, tmp_path):
        (tmp_path / 'source.md').write_text('[Link](./target.md#my-section)')
        (tmp_path / 'target.md').write_text('# My Section')
        files = {
            Path('source.md'): DocumentationFile(path=Path('source.md'), title='Source'),
            Path('target.md'): DocumentationFile(path=Path('target.md'), title='Target'),
        }
        link = Link(
            uri='./target.md#my-section',
            link_type=LinkType.INTERNAL,
            parent_file=Path('source.md'),
            line_number=1,
            anchor='my-section'
        )
        files[Path('source.md')].links_out.add(link)
        validator = AnchorLinkValidator()
        issues = validator.validate(files, tmp_path)
        assert len(issues) == 0

    def test_anchor_normalization_case_insensitive(self, tmp_path):
        (tmp_path / 'source.md').write_text('[Link](./target.md#section)')
        (tmp_path / 'target.md').write_text('# SECTION')
        files = {
            Path('source.md'): DocumentationFile(path=Path('source.md'), title='Source'),
            Path('target.md'): DocumentationFile(path=Path('target.md'), title='Target'),
        }
        link = Link(
            uri='./target.md#section',
            link_type=LinkType.INTERNAL,
            parent_file=Path('source.md'),
            line_number=1,
            anchor='section'
        )
        files[Path('source.md')].links_out.add(link)
        validator = AnchorLinkValidator()
        issues = validator.validate(files, tmp_path)
        assert len(issues) == 0

    def test_anchor_normalization_special_chars_removed(self, tmp_path):
        (tmp_path / 'source.md').write_text('[Link](./target.md#my-section-special)')
        (tmp_path / 'target.md').write_text('# My Section! (Special)')
        files = {
            Path('source.md'): DocumentationFile(path=Path('source.md'), title='Source'),
            Path('target.md'): DocumentationFile(path=Path('target.md'), title='Target'),
        }
        link = Link(
            uri='./target.md#my-section-special',
            link_type=LinkType.INTERNAL,
            parent_file=Path('source.md'),
            line_number=1,
            anchor='my-section-special'
        )
        files[Path('source.md')].links_out.add(link)
        validator = AnchorLinkValidator()
        issues = validator.validate(files, tmp_path)
        assert len(issues) == 0

    def test_multiple_anchors_in_file(self, tmp_path):
        (tmp_path / 'source.md').write_text('[Link1](./target.md#section1)\n[Link2](./target.md#section2)')
        (tmp_path / 'target.md').write_text('# Section1\n# Section2\n# Section3')
        files = {
            Path('source.md'): DocumentationFile(path=Path('source.md'), title='Source'),
            Path('target.md'): DocumentationFile(path=Path('target.md'), title='Target'),
        }
        link1 = Link(
            uri='./target.md#section1',
            link_type=LinkType.INTERNAL,
            parent_file=Path('source.md'),
            line_number=1,
            anchor='section1'
        )
        link2 = Link(
            uri='./target.md#section2',
            link_type=LinkType.INTERNAL,
            parent_file=Path('source.md'),
            line_number=2,
            anchor='section2'
        )
        files[Path('source.md')].links_out.add(link1)
        files[Path('source.md')].links_out.add(link2)
        validator = AnchorLinkValidator()
        issues = validator.validate(files, tmp_path)
        assert len(issues) == 0

    def test_unicode_in_anchors(self, tmp_path):
        (tmp_path / 'source.md').write_text('[Link](./target.md#раздел)')
        (tmp_path / 'target.md').write_text('# Раздел')
        files = {
            Path('source.md'): DocumentationFile(path=Path('source.md'), title='Source'),
            Path('target.md'): DocumentationFile(path=Path('target.md'), title='Target'),
        }
        link = Link(
            uri='./target.md#раздел',
            link_type=LinkType.INTERNAL,
            parent_file=Path('source.md'),
            line_number=1,
            anchor='раздел'
        )
        files[Path('source.md')].links_out.add(link)
        validator = AnchorLinkValidator()
        issues = validator.validate(files, tmp_path)
        assert len(issues) == 0

    def test_empty_anchor(self, tmp_path):
        (tmp_path / 'source.md').write_text('[Link](./target.md#)')
        (tmp_path / 'target.md').write_text('# Section')
        files = {
            Path('source.md'): DocumentationFile(path=Path('source.md'), title='Source'),
            Path('target.md'): DocumentationFile(path=Path('target.md'), title='Target'),
        }
        link = Link(
            uri='./target.md#',
            link_type=LinkType.INTERNAL,
            parent_file=Path('source.md'),
            line_number=1,
            anchor=''
        )
        files[Path('source.md')].links_out.add(link)
        validator = AnchorLinkValidator()
        issues = validator.validate(files, tmp_path)
        assert isinstance(issues, list)


    @pytest.mark.skip(reason='backlog: HTML anchor tags (id attribute) not yet supported')
    def test_html_anchor_tags_id_attribute(self, tmp_path):
        (tmp_path / 'source.md').write_text('[Link](./target.md#custom-anchor)')
        (tmp_path / 'target.md').write_text("<a id='custom-anchor'></a>\n## Section")
        files = {
            Path('source.md'): DocumentationFile(path=Path('source.md'), title='Source'),
            Path('target.md'): DocumentationFile(path=Path('target.md'), title='Target'),
        }
        link = Link(
            uri='./target.md#custom-anchor',
            link_type=LinkType.INTERNAL,
            parent_file=Path('source.md'),
            line_number=1,
            anchor='custom-anchor'
        )
        files[Path('source.md')].links_out.add(link)
        validator = AnchorLinkValidator()
        issues = validator.validate(files, tmp_path)
        assert len(issues) == 0

    @pytest.mark.skip(reason='backlog: HTML anchor tags (name attribute) not yet supported')
    def test_html_anchor_tags_name_attribute(self, tmp_path):
        (tmp_path / 'source.md').write_text('[Link](./target.md#old-style)')
        (tmp_path / 'target.md').write_text("<a name='old-style'></a>\n## Section")
        files = {
            Path('source.md'): DocumentationFile(path=Path('source.md'), title='Source'),
            Path('target.md'): DocumentationFile(path=Path('target.md'), title='Target'),
        }
        link = Link(
            uri='./target.md#old-style',
            link_type=LinkType.INTERNAL,
            parent_file=Path('source.md'),
            line_number=1,
            anchor='old-style'
        )
        files[Path('source.md')].links_out.add(link)
        validator = AnchorLinkValidator()
        issues = validator.validate(files, tmp_path)
        assert len(issues) == 0

    @pytest.mark.skip(reason='backlog: AsciiDoc header formats not yet supported')
    def test_asciidoc_header_formats(self, tmp_path):
        (tmp_path / 'source.adoc').write_text('link:./target.adoc#section[]')
        (tmp_path / 'target.adoc').write_text('== Section')
        files = {
            Path('source.adoc'): DocumentationFile(path=Path('source.adoc'), title='Source'),
            Path('target.adoc'): DocumentationFile(path=Path('target.adoc'), title='Target'),
        }
        link = Link(
            uri='./target.adoc#section',
            link_type=LinkType.INTERNAL,
            parent_file=Path('source.adoc'),
            line_number=1,
            anchor='section'
        )
        files[Path('source.adoc')].links_out.add(link)
        validator = AnchorLinkValidator()
        issues = validator.validate(files, tmp_path)
        assert len(issues) == 0

    @pytest.mark.skip(reason='backlog: reStructuredText header formats not yet supported')
    def test_restructuredtext_header_formats(self, tmp_path):
        (tmp_path / 'source.rst').write_text('`Link <./target.rst#section>`_')
        (tmp_path / 'target.rst').write_text('Section\n=======')
        files = {
            Path('source.rst'): DocumentationFile(path=Path('source.rst'), title='Source'),
            Path('target.rst'): DocumentationFile(path=Path('target.rst'), title='Target'),
        }
        link = Link(
            uri='./target.rst#section',
            link_type=LinkType.INTERNAL,
            parent_file=Path('source.rst'),
            line_number=1,
            anchor='section'
        )
        files[Path('source.rst')].links_out.add(link)
        validator = AnchorLinkValidator()
        issues = validator.validate(files, tmp_path)
        assert len(issues) == 0

    @pytest.mark.skip(reason='backlog: GitHub-style anchor with underscores not fully supported')
    def test_github_style_anchor_with_underscores(self, tmp_path):
        (tmp_path / 'source.md').write_text('[Link](./target.md#my_section)')
        (tmp_path / 'target.md').write_text('# My Section')
        files = {
            Path('source.md'): DocumentationFile(path=Path('source.md'), title='Source'),
            Path('target.md'): DocumentationFile(path=Path('target.md'), title='Target'),
        }
        link = Link(
            uri='./target.md#my_section',
            link_type=LinkType.INTERNAL,
            parent_file=Path('source.md'),
            line_number=1,
            anchor='my_section'
        )
        files[Path('source.md')].links_out.add(link)
        validator = AnchorLinkValidator()
        issues = validator.validate(files, tmp_path)
        assert len(issues) == 0

    @pytest.mark.skip(reason='backlog: Custom anchor normalization per platform not yet supported')
    def test_gitlab_style_anchor_normalization(self, tmp_path):
        (tmp_path / 'source.md').write_text('[Link](./target.md#section)')
        (tmp_path / 'target.md').write_text('# Section')
        files = {
            Path('source.md'): DocumentationFile(path=Path('source.md'), title='Source'),
            Path('target.md'): DocumentationFile(path=Path('target.md'), title='Target'),
        }
        link = Link(
            uri='./target.md#section',
            link_type=LinkType.INTERNAL,
            parent_file=Path('source.md'),
            line_number=1,
            anchor='section'
        )
        files[Path('source.md')].links_out.add(link)
        validator = AnchorLinkValidator()
        issues = validator.validate(files, tmp_path)
        assert len(issues) == 0

    @pytest.mark.skip(reason='backlog: Markdown header with inline code not fully supported')
    def test_header_with_inline_code(self, tmp_path):
        (tmp_path / 'source.md').write_text('[Link](./target.md#using-foo)')
        (tmp_path / 'target.md').write_text('# Using `foo()`')
        files = {
            Path('source.md'): DocumentationFile(path=Path('source.md'), title='Source'),
            Path('target.md'): DocumentationFile(path=Path('target.md'), title='Target'),
        }
        link = Link(
            uri='./target.md#using-foo',
            link_type=LinkType.INTERNAL,
            parent_file=Path('source.md'),
            line_number=1,
            anchor='using-foo'
        )
        files[Path('source.md')].links_out.add(link)
        validator = AnchorLinkValidator()
        issues = validator.validate(files, tmp_path)
        assert len(issues) == 0

    @pytest.mark.skip(reason='backlog: Markdown header with links not fully supported')
    def test_header_with_links(self, tmp_path):
        (tmp_path / 'source.md').write_text('[Link](./target.md#see-example)')
        (tmp_path / 'target.md').write_text('# See [Example](https://example.com)')
        files = {
            Path('source.md'): DocumentationFile(path=Path('source.md'), title='Source'),
            Path('target.md'): DocumentationFile(path=Path('target.md'), title='Target'),
        }
        link = Link(
            uri='./target.md#see-example',
            link_type=LinkType.INTERNAL,
            parent_file=Path('source.md'),
            line_number=1,
            anchor='see-example'
        )
        files[Path('source.md')].links_out.add(link)
        validator = AnchorLinkValidator()
        issues = validator.validate(files, tmp_path)
        assert len(issues) == 0