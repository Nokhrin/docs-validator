from pathlib import Path

import pytest

from docs_validator.core.asciidoc_extractor import AsciiDocLinkExtractor
from docs_validator.core.models import LinkType


@pytest.fixture
def extractor():
    return AsciiDocLinkExtractor(Path("test.adoc"))


@pytest.mark.parametrize(
    "content, expected_count, expected_uri, expected_type",
    [
        pytest.param(
            "link:./guide.adoc[Guide]",
            1,
            "./guide.adoc",
            LinkType.INTERNAL,
            id="Link macros",
        ),
        pytest.param(
            "link:https://example.com[External]",
            1,
            "https://example.com",
            LinkType.EXTERNAL,
            id="Link macros",
        ),
        pytest.param("link:target[]", 1, "target", LinkType.INTERNAL, id="Empty text"),
        pytest.param(
            "<<installation>>",
            1,
            "installation",
            LinkType.ANCHOR,
            id="Cross-references",
        ),
        pytest.param(
            "<<installation,Install section>>",
            1,
            "installation",
            LinkType.ANCHOR,
            id="Cross-references",
        ),
        pytest.param(
            "image:./logo.png[Logo]", 1, "./logo.png", LinkType.IMAGE, id="Image macros"
        ),
        pytest.param(
            "image:https://example.com/img.png[Remote]",
            1,
            "https://example.com/img.png",
            LinkType.IMAGE,
            id="Image macros",
        ),
        pytest.param(
            "Visit http://example.com",
            1,
            "http://example.com",
            LinkType.EXTERNAL,
            id="Bare URLs",
        ),
        pytest.param(
            "Email mailto:test@example.com",
            1,
            "mailto:test@example.com",
            LinkType.EXTERNAL,
            id="Bare URLs",
        ),
        pytest.param(
            "link:./a.adoc[A] and link:./b.adoc[B]",
            2,
            "./a.adoc",
            LinkType.INTERNAL,
            id="Boundary: multiple links in one line",
        ),
        pytest.param(
            "Plain text without-links", 0, None, None, id="Boundary: no matches"
        ),
        pytest.param(
            "notalink:target[text]",
            0,
            None,
            None,
            id="Equivalence class: non-matching patterns: notalink",
        ),
        pytest.param(
            "x-link:target[text]",
            0,
            None,
            None,
            id="Equivalence class: non-matching patterns: x-link",
        ),
        pytest.param("<<>", 0, None, None, id="Malformed xref"),
        pytest.param(
            "mylink:target[text]", 0, None, None, id="Invalid: prefix attached to link"
        ),
        pytest.param(
            "x-link:target[text]", 0, None, None, id="Invalid: hyphenated prefix"
        ),
        pytest.param(
            "image-link:target[text]", 0, None, None, id="Invalid: compound prefix"
        ),
        pytest.param(
            "See link:./guide.adoc[Guide]",
            1,
            "./guide.adoc",
            LinkType.INTERNAL,
            id="Valid: macro after word",
        ),
        pytest.param(
            "(link:./guide.adoc[Guide])",
            1,
            "./guide.adoc",
            LinkType.INTERNAL,
            id="Valid: macro in parentheses",
        ),
    ],
)
def test_ascii_doc_link_extractor(
    extractor, content, expected_count, expected_uri, expected_type
):
    links = list(extractor.get_links_from_file(content))
    assert len(links) == expected_count
    if expected_count > 0:
        assert links[0].uri == expected_uri
        assert links[0].link_type == expected_type


def test_handles_multiline_content(extractor):
    content = """= Document Title
    
    link:./guide.adoc[Guide]
    
    <<section-1>>
    
    image:./logo.png[Logo]
    
    
    """
    links = list(extractor.get_links_from_file(content))
    assert len(links) == 3
    assert {link.link_type for link in links} == {
        LinkType.INTERNAL,
        LinkType.ANCHOR,
        LinkType.IMAGE,
    }


def test_skips_escaped_patterns(extractor):
    content = r"""
\link:./guide.adoc[Guide]
\<<section-1>>
\image:./logo.png[Logo]
"""
    links = list(extractor.get_links_from_file(content))
    assert len(links) == 0
