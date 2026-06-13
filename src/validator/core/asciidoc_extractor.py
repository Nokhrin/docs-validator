import re
from pathlib import Path
from typing import Iterator

from validator.core.base_extractor import BaseLinkExtractor
from validator.core.models import Link, LinkType


class AsciiDocLinkExtractor(BaseLinkExtractor):
    # link:target[text] или link:target[]
    LINK_MACRO_PATTERN = re.compile(r'link:([^\[\s]+)\[[^]]*]', re.MULTILINE)

    # <<anchor,text>> или <<anchor>> (cross-references)
    XREF_PATTERN = re.compile(r'<<([^,>]+)(?:,[^>]*)?>>', re.MULTILINE)

    # image:target[alt]
    IMAGE_PATTERN = re.compile(r'image:([^\[\s]+)\[[^]]*]', re.MULTILINE)

    # URL without macros (http/https/mailto)
    BARE_URL_PATTERN = re.compile(r'(?<!link:)(?<!["(=])(https?://[^\s\[\]]+|mailto:[^\s\[\]]+)', re.MULTILINE)

    def get_links_from_file(self, file_content: str) -> Iterator[Link]:
        for line_number, line_content in enumerate(file_content.split('\n'), start=1):
            yield from self._get_links_from_line(line_number, line_content)

    def _get_links_from_line(self, line_number: int, line_content: str) -> Iterator[Link]:
        for match in self.LINK_MACRO_PATTERN.finditer(line_content):
            uri = match.group(1).strip()
            yield self._create_link(uri, line_number)

        for match in self.XREF_PATTERN.finditer(line_content):
            anchor = match.group(1).strip()
            yield Link(
                uri=anchor,
                link_type=LinkType.ANCHOR,
                parent_file=self.source_file,
                line_number=line_number,
                anchor=anchor
            )

        for match in self.IMAGE_PATTERN.finditer(line_content):
            uri = match.group(1).strip()
            yield Link(
                uri=uri,
                link_type=LinkType.IMAGE,
                parent_file=self.source_file,
                line_number=line_number
            )

        for match in self.BARE_URL_PATTERN.finditer(line_content):
            uri = match.group(1).strip()
            yield self._create_link(uri, line_number)

    def _create_link(self, uri: str, line_number: int) -> Link:
        if uri.startswith(('http://', 'https://', 'mailto:')):
            link_type = LinkType.EXTERNAL
            anchor = self._get_anchor(uri)
        elif uri.startswith('#'):
            link_type = LinkType.ANCHOR
            anchor = uri[1:]
        else:
            link_type = LinkType.INTERNAL
            anchor = self._get_anchor(uri)

        return Link(
            uri=uri,
            link_type=link_type,
            parent_file=self.source_file,
            line_number=line_number,
            anchor=anchor
        )

    @staticmethod
    def _get_anchor(uri: str) -> str | None:
        if '#' in uri:
            return uri.split('#', 1)[1]
        return None