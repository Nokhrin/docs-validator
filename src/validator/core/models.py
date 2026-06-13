"""Data models."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Optional


class LinkType(Enum):
    """Link type.
    Values:
        INTERNAL: Relative path to a file
        EXTERNAL: Web address or email
        ANCHOR: Section anchor
        IMAGE: Image link
    """
    INTERNAL = auto()
    EXTERNAL = auto()
    ANCHOR = auto()
    IMAGE = auto()


class SeverityLevel(Enum):
    ERROR = 'error'
    WARNING = 'warning'
    INFO = 'info'


class IssueType(Enum):
    """Validation issue type.
    Values:
        BROKEN_LINK: Link to a non-existent file
        MISSING_ANCHOR: Anchor not found
        ORPHAN_FILE: File with no incoming links
        CIRCULAR_DEPENDENCY: Circular dependency between files
        EXTERNAL_UNREACHABLE: External resource is unreachable
    """
    BROKEN_LINK = 'broken_link'
    MISSING_ANCHOR = 'missing_anchor'
    ORPHAN_FILE = 'orphan_file'
    CIRCULAR_DEPENDENCY = 'circular'
    EXTERNAL_UNREACHABLE = 'external_404'


@dataclass(frozen=True)
class Link:
    """An atomic link with metadata (immutable).
    Args:
        uri: URI string of the link
        link_type: Link type (INTERNAL/EXTERNAL/ANCHOR/IMAGE)
        parent_file: Source file containing the link
        line_number: Line number in the file
        anchor: Section anchor (optional)
    """
    uri: str
    link_type: LinkType
    parent_file: Path
    line_number: int
    anchor: str | None = None

    @property
    def is_internal(self) -> bool:
        return self.link_type is LinkType.INTERNAL

    @property
    def is_external(self) -> bool:
        return self.link_type is LinkType.EXTERNAL

    @property
    def target_file(self) -> Path | None:
        if self.is_internal:
            if self.uri:
                return Path(self.uri.split('#')[0])
        return None


@dataclass
class DocumentationFile:
    """A file with incoming/outgoing links (mutable).
    Args:
        path: Relative path to the file
        title: Document title
        links_out: Outgoing links from the file
        links_in: Incoming links to the file
        word_count: Number of words in the file
        last_modified: Date of last modification
    """
    path: Path
    title: str
    links_out: set[Link] = field(default_factory=set)
    links_in: set[Link] = field(default_factory=set)
    word_count: int = 0
    last_modified: Optional[datetime] = None

    @property
    def is_orphan(self) -> bool:
        return len(self.links_in) == 0


@dataclass
class ValidationIssue:
    """A description of a problem (broken link, orphan file, etc.).
    Args:
        issue_type: Validation issue type
        severity_level: Severity level (ERROR/WARNING/INFO)
        src_file: Source file where the issue was found
        link: Associated link (optional)
        message: Error message text
        suggestion: Recommendation for fixing the issue
    """
    issue_type: IssueType
    severity_level: SeverityLevel
    src_file: DocumentationFile
    link: Optional[Link] = None
    message: str = ''
    suggestion: str | None = None


@dataclass
class ValidationResult:
    """An aggregated validation report.
    Args:
        files_processed: Dictionary of processed files
        issues: List of detected issues
    """
    files_processed: dict[Path, DocumentationFile]
    issues: list[ValidationIssue]

    @property
    def has_errors(self) -> bool:
        return any(issue.severity_level == SeverityLevel.ERROR for issue in self.issues)

    @property
    def is_valid(self) -> bool:
        return not self.has_errors


@dataclass(frozen=True)
class LinkStatistics:
    internal_total: int = 0
    internal_broken: int = 0
    external_total: int = 0
    external_broken: int = 0
