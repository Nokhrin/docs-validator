import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from validator.core.models import DocumentationFile, ValidationIssue, IssueType, SeverityLevel
from validator.rules.anchor_link import AnchorLinkValidator
from validator.rules.base_validator import BaseValidator

log = logging.getLogger(__name__)


class ExternalAnchorValidator(BaseValidator):
    def __init__(
        self,
        timeout_sec: int = 10,
        user_agent: str = 'docs-validator/0.0.1',
    ) -> None:
        self.timeout_sec = timeout_sec
        self.user_agent = user_agent

    def validate(
        self,
        files_to_validate: dict[Path, DocumentationFile],
        root_dir: Path,
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []

        for doc_file in files_to_validate.values():
            for link in doc_file.links_out:
                if not link.is_external or not link.anchor:
                    continue

                uri_parsed = urlparse(link.uri)
                if uri_parsed.scheme not in ('http', 'https'):
                    continue

                page_uri = f'{uri_parsed.scheme}://{uri_parsed.netloc}{uri_parsed.path}'
                found, error = self._find_anchor_in_page(page_uri, link.anchor)

                if not found:
                    severity = SeverityLevel.WARNING
                    message = (
                        f'Anchor "#{link.anchor}" not found on external page {link.uri}'
                        if not error
                        else f'Anchor check failed for {link.uri}: {error}'
                    )

                    issues.append(
                        ValidationIssue(
                            issue_type=IssueType.MISSING_ANCHOR,
                            severity_level=severity,
                            src_file=doc_file,
                            link=link,
                            message=message,
                            suggestion='Verify the anchor manually or disable external anchor validation',
                        )
                    )

        return issues

    def _find_anchor_in_page(self, page_uri: str, anchor_text: str) -> tuple[bool, Optional[str]]:
        """
        Returns:
            (found: bool, error: Optional[str])
        """
        try:
            headers = {'User-Agent': self.user_agent}
            response = requests.get(page_uri, timeout=self.timeout_sec, headers=headers, allow_redirects=True)
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' not in content_type:
                log.debug('Non-HTML content for %s, skipping anchor check', page_uri)
                return True, None

            return self._find_anchor_in_html(response.text, anchor_text), None

        except requests.RequestException as err:
            return False, f'Failed to fetch page: {err}'
        except Exception as err:
            return False, f'Anchor check error: {err}'

    @staticmethod
    def _find_anchor_in_html(html_content: str, anchor: str) -> bool:
        anchor_decoded = anchor
        soup = BeautifulSoup(html_content, 'html.parser')

        for candidate in [anchor_decoded]:
            if soup.find(id=candidate):
                return True
            if soup.find('a', attrs={'name': candidate}):
                return True

        normalized = AnchorLinkValidator.get_normalized_anchor(anchor_decoded)
        if soup.find(id=normalized):
            return True

        for header in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            header_text = header.get_text(strip=True)
            if AnchorLinkValidator.get_normalized_anchor(header_text) == normalized:
                return True

        return False
