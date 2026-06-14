import logging
from collections import defaultdict
from concurrent.futures import as_completed
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse, ParseResult

import requests
from requests import RequestException

from validator.core.models import DocumentationFile, Link, ValidationIssue, IssueType, SeverityLevel
from validator.rules import BaseValidator

log = logging.getLogger(__name__)

GUARANTEED_ERROR_CODES = {404, 410}

BROWSER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
}


class ExternalLinkValidator(BaseValidator):
    def __init__(
            self,
            external_timeout_sec: int = 10,
            max_threads_number: int = 5,
            hosts_to_ignore: list[str] | None = None,
    ) -> None:
        self.external_timeout_sec = external_timeout_sec
        self.max_threads_number = max_threads_number
        if hosts_to_ignore is not None:
            hosts_normalized: set[str] = set()
            for host in hosts_to_ignore:
                hosts_normalized.add(host.lower().lstrip('.'))
            self.hosts_to_ignore = sorted(hosts_normalized)
        else:
            self.hosts_to_ignore = []

    def _is_host_ignored(self, hostname_to_verify: str) -> bool:
        for hostname_to_ignore in self.hosts_to_ignore:
            if hostname_to_verify == hostname_to_ignore or hostname_to_verify.endswith(f'.{hostname_to_ignore}'):
                return True
        return False

    def _check_single_link(
            self,
            link: Link,
            src_file: DocumentationFile,
            session: requests.Session
    ) -> ValidationIssue | None:
        log.debug('Processing link: %s', link.uri)
        try:
            log.debug('Stage 1: HEAD request (fast, checks headers only)')
            resp = session.head(
                link.uri,
                timeout=self.external_timeout_sec,
                allow_redirects=True,
            )

            if resp.status_code >= 400 and resp.status_code:
                log.debug('Stage 2: Retry with GET (HEAD returned %s)', resp.status_code)
                resp = session.get(
                    link.uri,
                    timeout=self.external_timeout_sec,
                    allow_redirects=True,
                    stream=True,
                )
                resp.close()

            if resp.status_code < 400:
                log.debug('Success')
                return None

            if resp.status_code in GUARANTEED_ERROR_CODES:
                log.debug('Guaranteed error (resource definitely missing)')
                return ValidationIssue(
                    issue_type=IssueType.EXTERNAL_UNREACHABLE,
                    severity_level=SeverityLevel.ERROR,
                    src_file=src_file,
                    link=link,
                    message=f'External resource not found ({resp.status_code}): {link.uri}',
                    suggestion='Check URL availability or update the link',
                )

            else:
                log.debug('Ambiguous error (WAF, timeout, server error) -> Manual verification')
                return ValidationIssue(
                    issue_type=IssueType.EXTERNAL_UNREACHABLE,
                    severity_level=SeverityLevel.WARNING,
                    src_file=src_file,
                    link=link,
                    message=f'Manual verification required ({resp.status_code}): {link.uri}',
                    suggestion='Verify manually or add to hosts_to_ignore',
                )

        except RequestException as err:
            log.debug('Network error -> Manual verification')
            return ValidationIssue(
                issue_type=IssueType.EXTERNAL_UNREACHABLE,
                severity_level=SeverityLevel.WARNING,
                src_file=src_file,
                link=link,
                message=f'Connection error, manual verification required: {link.uri}\n{err}',
                suggestion='Check the URL and network connection',
            )

        return None

    def validate(self, files_to_validate: dict[Path, DocumentationFile], root_dir: Path) -> list[ValidationIssue]:
        targets_by_file: dict[Path, list[Link]] = defaultdict(list)
        ignored_count = 0

        for doc_file in files_to_validate.values():
            for link in doc_file.links_out:
                if not link.is_external:
                    continue

                uri_parsed: ParseResult = urlparse(link.uri)
                if uri_parsed.scheme not in ('http', 'https'):
                    continue

                if self._is_host_ignored(uri_parsed.hostname):
                    ignored_count += 1
                    continue
                targets_by_file[doc_file.path].append(link)

        if ignored_count:
            log.debug('Links excluded by hosts_to_ignore: %d', ignored_count)
        if not targets_by_file:
            log.debug('No external links found')
            return []

        total_links = sum(len(links) for links in targets_by_file.values())
        log.debug('Starting external link check: %d links in %d files', total_links, len(targets_by_file))

        issues: list[ValidationIssue] = []

        with requests.Session() as session, ThreadPoolExecutor(max_workers=self.max_threads_number) as executor:
            session.headers.update(BROWSER_HEADERS)

            for file_path, links in targets_by_file.items():
                log.debug('Checking file: %s (%d external links)', file_path, len(links))
                doc_file = files_to_validate[file_path]

                file_futures = [
                    executor.submit(self._check_single_link, link, doc_file, session)
                    for link in links
                ]

                for future in as_completed(file_futures):
                    issue = future.result()
                    if issue:
                        issues.append(issue)

                log.debug('Check completed: %s', file_path)

        log.debug('External link check completed. Issues found: %d', len(issues))
        return issues
