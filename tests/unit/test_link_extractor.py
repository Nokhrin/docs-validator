from pathlib import Path

import pytest

from validator.core.markdown_extractor import LinkExtractor
from validator.core.models import LinkType


class TestLinkExtractor:
    def test_extract_internal_link(self):
        extractor = LinkExtractor(Path('test.md'))
        content = '[Guide](./docs/guide.md)'
        links = list(extractor.get_links_from_file(content))

        assert len(links) == 1
        assert links[0].uri == './docs/guide.md'
        assert links[0].link_type == LinkType.INTERNAL
        assert links[0].line_number == 1

    def test_extract_external_link(self):
        extractor = LinkExtractor(Path('test.md'))
        content = '[GitHub](https://github.com)'
        links = list(extractor.get_links_from_file(content))

        assert len(links) == 1
        assert links[0].link_type == LinkType.EXTERNAL

    def test_extract_image_link(self):
        extractor = LinkExtractor(Path('test.md'))
        content = '![Logo](./logo.png)'
        links = list(extractor.get_links_from_file(content))

        assert len(links) == 1
        assert links[0].link_type == LinkType.IMAGE

    def test_extract_anchor_link(self):
        extractor = LinkExtractor(Path('test.md'))
        content = '[Section](#installation)'
        links = list(extractor.get_links_from_file(content))

        assert len(links) == 1
        assert links[0].link_type == LinkType.ANCHOR
        assert links[0].anchor == 'installation'

    def test_extract_multiple_links_one_line(self):
        extractor = LinkExtractor(Path('test.md'))
        content = '[Link1](./a.md) and [Link2](./b.md)'
        links = list(extractor.get_links_from_file(content))

        assert len(links) == 2
        assert links[0].uri == './a.md'
        assert links[1].uri == './b.md'


class TestAnchorExtraction:
    def test_single_anchor(self):
        assert LinkExtractor._get_anchor('file.md#sec') == 'sec'

    def test_no_anchor(self):
        assert LinkExtractor._get_anchor('file.md') is None

    def test_empty_anchor(self):
        assert LinkExtractor._get_anchor('file.md#') == ''

    def test_multiple_hashes(self):
        assert LinkExtractor._get_anchor('a#b#c') == 'b#c'

    def test_anchor_with_special_chars(self):
        assert LinkExtractor._get_anchor('file.md#section-1_2') == 'section-1_2'


class TestLinkTypeDetection:
    @pytest.mark.parametrize(
        "markdown_content, expected_link_type",
        [
            ("![Logo](./img.png)", LinkType.IMAGE),
            ("[GitHub](https://github.com)", LinkType.EXTERNAL),
            ("[Section](#installation)", LinkType.ANCHOR),
            ("[Guide](./docs/guide.md)", LinkType.INTERNAL),
        ],
    )
    def test_link_type_detection(self, markdown_content, expected_link_type):
        extractor = LinkExtractor(Path("test.md"))
        links = list(extractor.get_links_from_file(markdown_content))

        assert len(links) == 1
        assert links[0].link_type == expected_link_type