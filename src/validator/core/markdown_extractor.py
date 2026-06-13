import logging
import re
from typing import Iterator

from validator.core.base_extractor import BaseLinkExtractor
from validator.core.models import Link, LinkType

log = logging.getLogger(__name__)


class LinkExtractor(BaseLinkExtractor):
    r"""
    Regex pattern for parsing Markdown inline links and images.
    Supports one level nested parentheses in URLs (e.g., Wikipedia links like `.../Page_(disambiguation)`).

    (!?)                          - Group 1: Optional '!' to indicate an image link.
    \[(.*?)\]                     - Group 2: Link text or image alt text inside square brackets (non-greedy).
    \(                            - Literal opening parenthesis for the URL.
    (                             - Group 3: The URL itself.
      [^()]+                      -   One or more characters that are not parentheses.
      (?:                         -   Non-capturing group to handle nested parentheses:
        \([^()]*\)                -     Literal '(', followed by content without parentheses, followed by literal ')'.
        [^()]*                    -     Followed by zero or more non-parenthesis characters.
      )*                          -   The nested group can repeat zero or more times.
    )                             - End of Group 3.
    \)                            - Literal closing parenthesis for the URL.
    """
    MARKDOWN_LINK_PATTERN = re.compile(
        r'(?<!\w)'
        r'(!?)\[(.*?)\]\(([^()]+(?:\([^()]*\)[^()]*)*)\)',
        re.MULTILINE
    )

    def get_links_from_file(self, file_content: str) -> Iterator[Link]:
        for line_number, line_content in enumerate(file_content.split('\n'), start=1):
            yield from self._get_links_from_line(line_number, line_content)

    def _get_links_from_line(self, line_number: int, line_content: str) -> Iterator[Link]:
        for matched_line in self.MARKDOWN_LINK_PATTERN.finditer(line_content):
            uri: str = matched_line.group(3).strip()
            link_type: LinkType | None = self._get_link_type(matched_line)

            if link_type is None:
                continue

            anchor: str | None = self._get_anchor(uri)

            yield Link(
                uri=uri,
                link_type=link_type,
                parent_file=self.source_file,
                line_number=line_number,
                anchor=anchor,
            )

    @staticmethod
    def _get_link_type(matched_line: re.Match[str]) -> LinkType | None:
        is_image = matched_line.group(1) == '!'
        uri = matched_line.group(3).strip()

        if uri.startswith(('?:', '(?:', '[^', '(?!')):
            log.debug('URI "%s" is not a link', uri)
            return None

        if is_image:
            return LinkType.IMAGE
        if uri.startswith(('http://', 'https://', 'mailto:')):
            return LinkType.EXTERNAL
        if uri.startswith('#'):
            return LinkType.ANCHOR
        return LinkType.INTERNAL

    @staticmethod
    def _get_anchor(uri: str) -> str | None:
        char_indices = [pos for pos, char in enumerate(uri) if char == '#']
        if char_indices:
            return uri[char_indices[0] + 1:]
        return None
