import logging
from concurrent.futures import as_completed
from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

import requests
from requests import RequestException

from validator.core.models import DocumentationFile, Link, ValidationIssue, IssueType, SeverityLevel
from validator.validators import BaseValidator

log = logging.getLogger(__name__)


class ExternalLinkValidator(BaseValidator):
    """Проверяет доступность ресурсов по внешним ссылкам."""

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
                    message=f'Внешний ресурс недоступен ({resp.status_code}): {link.uri}',
                    suggestion='Проверьте работоспособность URL или обновите ссылку',
                )
        except RequestException as err:
            return ValidationIssue(
                issue_type=IssueType.EXTERNAL_UNREACHABLE,
                severity_level=SeverityLevel.ERROR,
                src_file=src_file,
                link=link,
                message=f'Ошибка соединения: {link.uri}\n{err}',
                suggestion='Проверьте URL и сетевое подключение',
            )
        return None

    def validate(
            self,
            files_to_validate: dict[Path, DocumentationFile],
            root_dir: Path,
    ) -> list[ValidationIssue]:
        log.debug('Начало проверки внешних ссылок')
        targets: tuple[Link, DocumentationFile] = []
        ignored_count: int = 0

        for doc_file in files_to_validate.values():
            for link_to_validate in doc_file.links_out:
                if not link_to_validate.is_external:
                    continue
                if self._is_host_ignored(link_to_validate.uri):
                    log.debug(f'Ссылка %s исключена из проверки по требованию отбора', link_to_validate.uri)
                    ignored_count += 1
                    continue
                log.debug('В файле %s найдена внешняя ссылка: %s', doc_file.path, link_to_validate.uri)
                targets.append((link_to_validate, doc_file))
                log.debug('В файле %s отсутствуют внешние ссылки', doc_file.path)

        if ignored_count:
            log.debug('По требованию отбора всего непроверенных ссылок: %d', ignored_count)

        if not targets:
            log.debug('Внешние ссылки отсутствуют')
            return []

        issues: list[ValidationIssue] = []
        with requests.Session() as session, ThreadPoolExecutor(max_workers=self.max_threads_number) as executor:
            futures = {}
            for link_to_validate, doc_file in targets:
                futures[
                    executor.submit(
                        self._check_single_link, link_to_validate, doc_file, session
                    )] = (link_to_validate, doc_file)
            for future in as_completed(futures):
                issue = future.result()
                if issue:
                    issues.append(issue)

        log.debug('Проверка внешних ссылок завершена. Найдено проблем: %d', len(issues))
        return issues
