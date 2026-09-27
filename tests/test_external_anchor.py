from pathlib import Path

import pytest
import requests
import responses

from docs_validator.core.models import (
    DocumentationFile,
    Link,
    LinkType,
    SeverityLevel,
    IssueType,
)
from docs_validator.rules import ExternalAnchorValidator


@pytest.fixture
def validator():
    return ExternalAnchorValidator(user_agent="test-agent")


@pytest.fixture
def doc_file():
    return DocumentationFile(path=Path("test.md"), title="TEST Title")


@pytest.fixture()
def external_link_with_anchor():
    return Link(
        uri="https://example.com/docs#setup",
        link_type=LinkType.EXTERNAL,
        parent_file=Path("test_parent.md"),
        line_number=1,
        anchor="setup",
    )


@pytest.mark.parametrize(
    "scheme, expected",
    [
        pytest.param("http", True, id="valid scheme"),
        pytest.param("https", True, id="valid scheme"),
        pytest.param("ftp", False, id="invalid scheme"),
        pytest.param("mailto", False, id="invalid scheme"),
        pytest.param("file", False, id="invalid scheme"),
    ],
)
def test_skips_non_http(validator, doc_file, scheme, expected):
    link = Link(
        uri=f"{scheme}://example.org/docs#anchor",
        link_type=LinkType.EXTERNAL,
        parent_file=Path("test_parent.md"),
        line_number=1,
        anchor="anchor",
    )
    files = {Path("test_child.md"): doc_file}
    doc_file.links_out.add(link)

    issues = validator.validate(files, Path("/tmp"))
    if expected:
        assert len(issues) == 1
    else:
        assert len(issues) == 0


@responses.activate
@pytest.mark.parametrize(
    "content_type, anchor_in_html, expected_issues_count",
    [
        pytest.param(
            "text/html",
            True,
            0,
            id="HTML + anchor found -> no issue",
        ),
        pytest.param(
            "text/html",
            False,
            1,
            id="HTML + anchor missing -> WARNING",
        ),
        pytest.param(
            "application/json",
            None,
            0,
            id="Non-HTML -> skip (found=True)",
        ),
        pytest.param(
            "application/pdf",
            None,
            0,
            id="Non-HTML -> skip",
        ),
    ],
)
def test_decision_content_type_anchor_presence(
    validator,
    doc_file,
    external_link_with_anchor,
    content_type,
    anchor_in_html,
    expected_issues_count,
):
    url = "https://example.com/docs"

    if anchor_in_html is True:
        html = '<html><body><h1 id="setup">Install</h1></body></html>'
    elif anchor_in_html is False:
        html = '<html><body><h1 id="other">Other</h1></body></html>'
    else:
        html = '{"data": "not html"}'

    responses.add(responses.GET, url, body=html, status=200, content_type=content_type)
    files = {Path("test.md"): doc_file}
    doc_file.links_out.add(external_link_with_anchor)

    issues = validator.validate(files, Path("/tmp"))
    assert len(issues) == expected_issues_count
    if expected_issues_count > 0:
        assert "setup" in issues[0].message


@responses.activate
@pytest.mark.parametrize(
    "status_code, expected_severity",
    [
        pytest.param(200, SeverityLevel.WARNING, id="Success but anchor missing"),
        pytest.param(404, SeverityLevel.WARNING, id="Page not found"),
        pytest.param(500, SeverityLevel.WARNING, id="Server error"),
        pytest.param(403, SeverityLevel.WARNING, id="Forbidden"),
    ],
)
def test_http_errors(
    validator, doc_file, external_link_with_anchor, status_code, expected_severity
):
    url = "https://example.com/docs"
    responses.add(
        responses.GET,
        url,
        body="<html><body>No matching anchor here</body></html>",
        content_type="text/html",
        status=status_code,
    )

    files = {Path("test.md"): doc_file}
    doc_file.links_out.add(external_link_with_anchor)

    issues = validator.validate(files, Path("/tmp"))
    assert len(issues) == 1
    assert issues[0].severity_level == expected_severity
    assert issues[0].issue_type == IssueType.MISSING_ANCHOR


@responses.activate
def test_boundary_network_timeout(validator, doc_file, external_link_with_anchor):
    validator.timeout_sec = 1
    url = "https://example.com/docs"
    responses.add(
        responses.GET, url, requests.exceptions.Timeout("Connection timed out")
    )

    files = {Path("test.md"): doc_file}
    doc_file.links_out.add(external_link_with_anchor)

    issues = validator.validate(files, Path("/tmp"))
    assert len(issues) == 1
    assert issues[0].severity_level == SeverityLevel.WARNING
    assert "Failed to fetch page" in issues[0].message


@responses.activate
@pytest.mark.parametrize(
    "html_content, anchor, expected_found",
    [
        pytest.param(
            '<h1 id="install">Install</h1>', "install", True, id="Case-insensitive"
        ),
        pytest.param(
            '<h2 id="Install">Install</h2>', "install", True, id="Case-insensitive"
        ),  #
        pytest.param(
            '<a name="install">Link</a>', "install", True, id="Legacy <a name>"
        ),
        pytest.param(
            "<h1>Install Section</h1>", "install-section", True, id="Normalized header"
        ),
        pytest.param("<h1>Install</h1>", "missing", False, id="Not in header"),
        pytest.param("<div>No anchor here</div>", "any", False, id="Not in div"),
    ],
)
def test_eq_classes_anchor_detection(
    validator, doc_file, html_content, anchor, expected_found
):
    url = "https://example.com/docs"
    responses.add(
        responses.GET,
        url,
        body=f"<html><body>{html_content}</body></html>",
        status=200,
        content_type="text/html",
    )

    link = Link(f"{url}#{anchor}", LinkType.EXTERNAL, Path("test.md"), 1, anchor)

    files = {Path("test.md"): doc_file}
    doc_file.links_out.add(link)

    issues = validator.validate(files, Path("/tmp"))

    if expected_found:
        assert len(issues) == 0
    else:
        assert len(issues) == 1
        assert issues[0].severity_level == SeverityLevel.WARNING
