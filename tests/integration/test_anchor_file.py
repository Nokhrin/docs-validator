from pathlib import Path

from validator.core.models import DocumentationFile, Link, LinkType
from validator.rules.anchor_link import AnchorLinkValidator


def test_anchor_exists_in_target_file_not_source_generates_no_issue(tmp_path):
    target_file_path = tmp_path / 'target.md'
    target_file_path.write_text('# Header\n## performance-review\nContent.\n')

    source_file_path = tmp_path / 'source.md'
    source_content = '[Link](./target.md#performance-review)\n'
    source_file_path.write_text(source_content)

    target_doc_file = DocumentationFile(path=Path('target.md'), title='Target')
    source_doc_file = DocumentationFile(path=Path('source.md'), title='Source')

    link = Link(
        uri='./target.md#performance-review',
        link_type=LinkType.INTERNAL,
        parent_file=Path('source.md'),
        line_number=1,
        anchor='performance-review'
    )

    source_doc_file.links_out.add(link)

    files_to_validate = {
        Path('target.md'): target_doc_file,
        Path('source.md'): source_doc_file,
    }

    validator = AnchorLinkValidator()
    issues = validator.validate(files_to_validate, tmp_path)

    assert len(issues) == 0
