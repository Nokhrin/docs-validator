from pathlib import Path

from validator.core.asciidoc_extractor import AsciiDocLinkExtractor
from validator.core.base_extractor import BaseLinkExtractor
from validator.core.markdown_extractor import LinkExtractor

_EXTRACTOR_REGISTRY: dict[str, type[BaseLinkExtractor]] = {
    '.md': LinkExtractor,
    '.markdown': LinkExtractor,
    '.adoc': AsciiDocLinkExtractor,
    '.asc': AsciiDocLinkExtractor,
}

def get_extractor(source_file: Path) -> BaseLinkExtractor:
    """
    Notes:
        Fallback to Markdown.
    """
    suffix = source_file.suffix.lower()
    extractor_class = _EXTRACTOR_REGISTRY.get(suffix, LinkExtractor)
    return extractor_class(source_file)