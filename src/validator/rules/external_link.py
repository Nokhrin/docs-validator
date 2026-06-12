import logging
from collections import defaultdict
from concurrent.futures import as_completed
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

import requests
from requests import RequestException

from validator.core.models import DocumentationFile, Link, ValidationIssue, IssueType, SeverityLevel
from validator.rules import BaseValidator

log = logging.getLogger(__name__)


class ExternalLinkValidator(BaseValidator):
    """Checks the availability of resources via external links."""

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

    def _is_host_ignored(self, uri: str) -> bool:
        hostname_to_verify = urlparse(uri).hostname.lower()
        if not hostname_to_verify:
            return False
        return any(hostname_to_verify == hostname_to_ignore or hostname_to_verify.endswith(f'.{hostname_to_ignore}')
                   for hostname_to_ignore in self.hosts_to_ignore)

    def _check_single_link(
            self,
            link: Link,
            src_file: DocumentationFile,
            session: requests.Session
    ) -> ValidationIssue | None:
        try:
            resp = session.head(
                link.uri,
                timeout=self.external_timeout_sec,
                allow_redirects=True,
            )
            if resp.status_code == 405:
                resp = session.get(
                    link.uri,
                    timeout=self.external_timeout_sec,
                    allow_redirects=True,
                )
                resp.close()

            if resp.status_code >= 400:
                return ValidationIssue(
                    issue_type=IssueType.EXTERNAL_UNREACHABLE,
                    severity_level=SeverityLevel.ERROR,
                    src_file=src_file,
                    link=link,
                    message=f'External resource unavailable ({resp.status_code}): {link.uri}',
                    suggestion='Check URL availability or update the link',
                )

        except RequestException as err:
            return ValidationIssue(
                issue_type=IssueType.EXTERNAL_UNREACHABLE,
                severity_level=SeverityLevel.ERROR,
                src_file=src_file,
                link=link,
                message=f'Connection error: {link.uri}\n{err}',
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
                if self._is_host_ignored(link.uri):
                    ignored_count += 1
                    continue
                targets_by_file[doc_file.path].append(link)

        if ignored_count:
            log.info('Links excluded by hosts_to_ignore: %d', ignored_count)
        if not targets_by_file:
            log.info('No external links found')
            return []

        total_links = sum(len(links) for links in targets_by_file.values())
        log.info('Starting external link check: %d links in %d files', total_links, len(targets_by_file))

        issues: list[ValidationIssue] = []

        with requests.Session() as session, ThreadPoolExecutor(max_workers=self.max_threads_number) as executor:
            for file_path, links in targets_by_file.items():
                log.info('Checking file: %s (%d external links)', file_path, len(links))
                doc_file = files_to_validate[file_path]

                file_futures = [
                    executor.submit(self._check_single_link, link, doc_file, session)
                    for link in links
                ]

                for future in as_completed(file_futures):
                    issue = future.result()
                    if issue:
                        issues.append(issue)

                log.info('Check completed: %s', file_path)

        log.info('External link check completed. Issues found: %d', len(issues))
        return issues