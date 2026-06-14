import logging
import re
from pathlib import Path

from validator.core.models import DocumentationFile, ValidationIssue, IssueType, SeverityLevel, LinkType
from validator.rules.base_validator import BaseValidator

log = logging.getLogger(__name__)


class AnchorLinkValidator(BaseValidator):
    MARKDOWN_HEADER_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

    def validate(self, files_to_validate: dict[Path, DocumentationFile], root_dir: Path) -> list[ValidationIssue]:
        log.debug('Starting anchor check, total files: %d', len(files_to_validate))
        issues: list[ValidationIssue] = []

        for file_path, doc_file in files_to_validate.items():
            for link in doc_file.links_out:
                if link.link_type != LinkType.INTERNAL or not link.anchor:
                    log.debug('Link is not internal or does not has an anchor')
                    continue

                target_uri_without_anchor = link.uri.split('#')[0]

                if str(link.target_file).startswith('/'):
                    log.debug('Path to target %s is absolute', str(link.target_file))
                    target_path = (root_dir / str(link.target_file)[1:]).resolve()
                else:
                    target_path = (root_dir.parent / link.target_file).resolve()

                if not target_path.exists():
                    log.debug('File does not exist => issue of BrokenLinkValidator')
                    continue

                if not self._has_anchor(target_path, link.anchor):
                    issues.append(
                        ValidationIssue(
                            issue_type=IssueType.MISSING_ANCHOR,
                            severity_level=SeverityLevel.ERROR,
                            src_file=doc_file,
                            link=link,
                            message=f'Anchor "{link.anchor}" not found in file {target_file_path.relative_to(root_dir)}',
                            suggestion='Check the anchor name or add the anchor to the target file',
                        )
                    )

        return issues

    @staticmethod
    def _has_anchor(file_path:Path, anchor:str) -> bool:
        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError as err:
            log.warning('Could not read file %s as UTF-8 for anchor check\n%s', file_path, err)
            log.debug('Unreadable file %s is treated as having not anchor', file_path)
            return False

        anchor_norm = AnchorLinkValidator.get_normalized_anchor(anchor)
        header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        matches = header_pattern.findall(content)

        for _, header_text in matches:
            header_norm = AnchorLinkValidator.get_normalized_anchor(header_text)
            if header_norm == anchor_norm:
                log.debug('Anchor target %s found', header_norm)
                return True

        return False

    def _get_anchors_from_file(self, file_path: Path) -> set[str]:
        anchors: set[str] = set()

        try:
            content = file_path.read_text(encoding='utf-8')
        except IOError as err:
            log.error('Failed to read file %s: %s', file_path, err)
            return anchors

        for header_match in self.MARKDOWN_HEADER_PATTERN.finditer(content):
            header_text = header_match.group(2).strip()
            header_anchor = self.get_normalized_anchor(header_text)
            anchors.add(header_anchor)

        return anchors

    @staticmethod
    def get_normalized_anchor(content: str) -> str:
        """Returns the heading in anchor link format.
        Reproduces the result of a markdown processor.
        """
        anchor = content.lower()
        anchor = re.sub(r'[\s\t]+', '-', anchor)  # spaces, tabs -> hyphens
        anchor = re.sub(r'-+', '-', anchor)  # remove duplicate hyphens
        anchor = re.sub(r'[^a-z0-9-_]', '', anchor)  # keep 'a-z0-9-_'
        anchor = anchor.strip('-')
        return anchor
