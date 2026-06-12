import logging
import re
from pathlib import Path

from validator.core.models import DocumentationFile, ValidationIssue, IssueType, SeverityLevel
from validator.rules.base_validator import BaseValidator

log = logging.getLogger(__name__)


class AnchorLinkValidator(BaseValidator):
    """Checks anchor existence."""

    MARKDOWN_HEADER_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

    def validate(self, files_to_validate: dict[Path, DocumentationFile], root_dir: Path) -> list[ValidationIssue]:
        log.debug('Starting anchor check, total files: %d', len(files_to_validate))
        issues: list[ValidationIssue] = []

        for file in files_to_validate.values():
            log.debug('Checking file: %s', file.path)
            for link in file.links_out:
                log.debug('Checking internal links with anchors')
                if link.anchor and link.is_internal and link.target_file:
                    source_abs = root_dir / link.parent_file
                    target_path = (source_abs.parent / link.target_file).resolve()

                    if not target_path.exists():
                        log.debug('Target file %s not found, different error type: %s', target_path, link)
                        continue

                    file_anchors: set[str] = self._get_anchors_from_file(file.path)
                    log.debug('Anchors found:\n%s', file_anchors)

                    if link.anchor not in file_anchors:
                        log.warning(
                            'Anchor "%s" not found in file %s (link from %s:%d)',
                            link.anchor, target_path, file.path, link.line_number
                        )
                        issues.append(ValidationIssue(
                            issue_type=IssueType.MISSING_ANCHOR,
                            severity_level=SeverityLevel.ERROR,
                            src_file=file,
                            link=link,
                            message=f'Anchor "#{link.anchor}" not found in file {link.target_file}',
                            suggestion='Check the heading name or create the corresponding section',
                        ))

        return issues

    def _get_anchors_from_file(self, file_path: Path) -> set[str]:
        anchors: set[str] = set()

        try:
            content = file_path.read_text(encoding='utf-8')
        except IOError as err:
            log.error('Failed to read file %s: %s', file_path, err)
            return anchors

        for header_match in self.MARKDOWN_HEADER_PATTERN.finditer(content):
            header_text = header_match.group(2).strip()
            header_anchor = self._get_anchor_from_header(header_text)
            anchors.add(header_anchor)

        return anchors

    def _get_anchor_from_header(self, header_text: str) -> str:
        """Returns the heading in anchor link format.
        Reproduces the result of a markdown processor.
        """
        anchor = header_text.lower()
        anchor = re.sub(r'[\s\t]+', '-', anchor)  # spaces, tabs -> hyphens
        anchor = re.sub(r'-+', '-', anchor)  # remove duplicate hyphens
        anchor = re.sub(r'[^a-z0-9-_]', '', anchor)  # keep 'a-z0-9-_'
        anchor = anchor.strip('-')
        return anchor
