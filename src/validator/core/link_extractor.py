"""Парсеры ссылок."""
import re
from pathlib import Path
from typing import Iterator

from validator.core.models import Link, LinkType


class LinkExtractor:
    """Парсер ссылок."""
    # '[text](url)' => [('', 'text', 'url')]
    # '![alt](url)' => [('!', 'alt', 'url')]
    # '[text](https://...)' => [('', 'text', 'https://...')]
    # '[text](#section)' => [('', 'text', '#section')]
    # '[text](./file.md)' => [('', 'text', './file.md')]
    MARKDOWN_LINK_PATTERN = re.compile(r'(!?)\[(.*?)\]\(([^)]+)\)', re.MULTILINE)

    def __init__(self, source_file: Path):
        self.source_file = source_file

    def get_links_from_file(self, file_content: str) -> Iterator[Link]:
        """Извлекает ссылки из Markdown-контента.
        line_number: base 1

        Returns:
            Генератор объектов Link
        """
        for line_number, line_content in enumerate(file_content.split('\n'), start=1):
            yield from self._get_links_from_line(line_number, line_content)

    def _get_links_from_line(self, line_number: int, line_content: str) -> Iterator[Link]:
        """Возвращает ссылки, найденные в строке line_number.
        Генератор.
        line_number: base 1
        """
        for matched_line in self.MARKDOWN_LINK_PATTERN.finditer(line_content):
            uri: str = matched_line.group(3).strip()
            link_type: LinkType = self._get_link_type(matched_line)
            anchor: str | None = self._get_anchor(uri)

            yield Link(
                uri=uri,
                link_type=link_type,
                source_file=self.source_file,
                line_number=line_number,
                anchor=anchor,
            )

    @staticmethod
    def _get_link_type(matched_line: re.Match[str]) -> LinkType:
        """Определяет тип ссылки по объекту совпадения regex.

        Использует группы:
            group(1): '!' для изображений, '' для обычных ссылок
            group(3): URI ссылки
        """
        is_image = matched_line.group(1) == '!'
        uri = matched_line.group(3).strip()

        if is_image:
            return LinkType.IMAGE
        if uri.startswith(('http://', 'https://', 'mailto:')):
            return LinkType.EXTERNAL
        if uri.startswith('#'):
            return LinkType.ANCHOR
        return LinkType.INTERNAL

    @staticmethod
    def _get_anchor(uri: str) -> str | None:
        """Извлекает якорь из URI.
        Первый # - разделитель, остальное (в том числе другие '#') - часть якоря
        Возвращает None, если якоря нет.

        file.md#anchor => 'anchor'
        file.md#anchor#text => 'anchor#text'
        file.md# => None
        file.md => None
        """
        char_indices = [pos for pos, char in enumerate(uri) if char == '#']
        if char_indices:
            return uri[char_indices[0] + 1:]
        return None
