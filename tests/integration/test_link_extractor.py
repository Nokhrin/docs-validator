from pathlib import Path

import pytest

from validator.core.markdown_extractor import LinkExtractor
from validator.core.models import LinkType


@pytest.mark.parametrize(
    'markdown_text, expected_uri, expected_is_image, expected_link_type, expected_count',
    [
        ('[text](url)', 'url', False, LinkType.INTERNAL, 1),
        ('![alt](image.png)', 'image.png', True, LinkType.IMAGE, 1),
        ('[text](https://example.com)', 'https://example.com', False, LinkType.EXTERNAL, 1),
        ('[text](#section)', '#section', False, LinkType.ANCHOR, 1),
        ('[text](./file.md)', './file.md', False, LinkType.INTERNAL, 1),
        (r'\[not a link\](url)', None, False, None, 0),
    ]
)
def test_link_extractor_extracts_inline_links(
        markdown_text,
        expected_uri,
        expected_is_image,
        expected_link_type,
        expected_count,
):
    extractor = LinkExtractor(Path('test.md'))
    links = list(extractor.get_links_from_file(markdown_text))

    assert len(links) == 1
    if expected_count > 0:
        link = links[0]
        assert link.uri == expected_uri
        assert link.link_type == expected_link_type
