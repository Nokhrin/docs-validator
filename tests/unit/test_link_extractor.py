"""Тесты для LinkExtractor."""
from pathlib import Path

from validator.core.link_extractor import LinkExtractor
from validator.core.models import LinkType


class TestLinkExtractor:
    """Тестирование парсера ссылок."""

    def test_extract_internal_link(self):
        """Извлечение внутренней ссылки."""
        extractor = LinkExtractor(Path('test.md'))
        content = '[Guide](./docs/guide.md)'
        links = list(extractor.get_links_from_file(content))

        assert len(links) == 1
        assert links[0].uri == './docs/guide.md'
        assert links[0].link_type == LinkType.INTERNAL
        assert links[0].line_number == 1

    def test_extract_external_link(self):
        """Извлечение внешней ссылки."""
        extractor = LinkExtractor(Path('test.md'))
        content = '[GitHub](https://github.com)'
        links = list(extractor.get_links_from_file(content))

        assert len(links) == 1
        assert links[0].link_type == LinkType.EXTERNAL

    def test_extract_image_link(self):
        """Извлечение ссылки на изображение."""
        extractor = LinkExtractor(Path('test.md'))
        content = '![Logo](./logo.png)'
        links = list(extractor.get_links_from_file(content))

        assert len(links) == 1
        assert links[0].link_type == LinkType.IMAGE

    def test_extract_anchor_link(self):
        """Извлечение якорной ссылки."""
        extractor = LinkExtractor(Path('test.md'))
        content = '[Section](#installation)'
        links = list(extractor.get_links_from_file(content))

        assert len(links) == 1
        assert links[0].link_type == LinkType.ANCHOR
        assert links[0].anchor == 'installation'

    def test_extract_multiple_links_one_line(self):
        """Несколько ссылок в одной строке."""
        extractor = LinkExtractor(Path('test.md'))
        content = '[Link1](./a.md) and [Link2](./b.md)'
        links = list(extractor.get_links_from_file(content))

        assert len(links) == 2
        assert links[0].uri == './a.md'
        assert links[1].uri == './b.md'

class TestLinkTypeDetection:
    def test_image_link(self, markdown_link_pattern):
        match = markdown_link_pattern.match('![Logo](./img.png)')
        assert LinkExtractor._get_link_type(match) == LinkType.IMAGE

    def test_external_link(self, markdown_link_pattern):
        match = markdown_link_pattern.search('[GitHub](https://github.com)')
        assert LinkExtractor._get_link_type(match) == LinkType.EXTERNAL

    def test_anchor_link(self, markdown_link_pattern):
        match = markdown_link_pattern.search('[Section](#installation)')
        assert LinkExtractor._get_link_type(match) == LinkType.ANCHOR

    def test_internal_link(self, markdown_link_pattern):
        match = markdown_link_pattern.search('[Guide](./docs/guide.md)')
        assert LinkExtractor._get_link_type(match) == LinkType.INTERNAL


class TestAnchorExtraction:
    def test_single_anchor(self):
        assert LinkExtractor._get_anchor("file.md#sec") == "sec"

    def test_no_anchor(self):
        assert LinkExtractor._get_anchor("file.md") is None

    def test_empty_anchor(self):
        assert LinkExtractor._get_anchor("file.md#") == ""

    def test_multiple_hashes(self):
        assert LinkExtractor._get_anchor("a#b#c") == "b#c"

    def test_anchor_with_special_chars(self):
        assert LinkExtractor._get_anchor("file.md#section-1_2") == "section-1_2"