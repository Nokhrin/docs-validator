"""Модели данных для статического анализа документации.

Ключевые сущности:
    Link: Атомарная ссылка с метаданными (неизменяемая).
    FileToValidate: Файл с входящими/исходящими ссылками (изменяемый).
    ValidationIssue: Описание проблемы (битая ссылка, сирота и т.д.).
    ValidationResult: Агрегированный отчет проверки.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Optional


class LinkType(Enum):
    """Тип ссылки.

    INTERNAL: [text](./file.md)
    EXTERNAL: [text](https://...)
    ANCHOR: [text](#section)
    IMAGE: ![alt](image.png)
    """
    INTERNAL = auto()
    EXTERNAL = auto()
    ANCHOR = auto()
    IMAGE = auto()

class SeverityLevel(Enum):
    """Уровень критичности."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class IssueType(Enum):
    """Тип проблемы валидации."""
    BROKEN_LINK = "broken_link"
    MISSING_ANCHOR = "missing_anchor"
    ORPHAN_FILE = "orphan_file"
    CIRCULAR_DEPENDENCY = "circular"
    EXTERNAL_UNREACHABLE = "external_404"

@dataclass(frozen=True)
class Link:
    """Ссылка, извлеченная из документации.
    Args:
        line_number: номер строки в source_file, в которой найдена ссылка
    """
    uri: str
    link_type: LinkType
    source_file: Path
    line_number: int
    anchor: str | None = None

    @property
    def is_internal(self) -> bool:
        """Внутренняя ссылка.
        Является относительным путем к файлу
        """
        return self.link_type is LinkType.INTERNAL

    @property
    def is_external(self) -> bool:
        """Внешняя ссылка.
        Является адресом веб, почты
        """
        return self.link_type is LinkType.EXTERNAL

    @property
    def target_file(self) -> Path | None:
        """Относительный путь к целевому файлу."""
        if self.is_internal:
            if self.uri:
                return Path(self.uri.split('#')[0])
        return None

@dataclass
class FileToValidate:
    """Файл, в котором проверяются ссылки."""
    path: Path
    title: str
    links_out: set[Link] = field(default_factory=set)
    links_in: set[Link] = field(default_factory=set)
    word_count: int = 0
    last_modified: Optional[datetime] = None

    @property
    def is_orphan(self) -> bool:
        """Не содержит входящих ссылок."""
        return len(self.links_in) == 0

@dataclass
class ValidationIssue:
    """Проблема, обнаруженная при проверке."""
    issue_type: IssueType
    severity_level: SeverityLevel
    src_file: FileToValidate
    link: Optional[Link] = None
    message: str = ''
    suggestion: str | None = None

@dataclass
class ValidationResult:
    """Результат проверки."""
    files_processed: dict[Path, FileToValidate]
    issues: list[ValidationIssue]

    @property
    def has_errors(self) -> bool:
        """Наличие ERROR в результатах проверки."""
        return any(issue.severity_level == SeverityLevel.ERROR for issue in self.issues)

    @property
    def is_valid(self) -> bool:
        """Не проходит проверку, если результат содержит ERROR."""
        return not self.has_errors

    @property
    def total_links(self) -> int:
        """Общее количество найденных ссылок."""
        return sum(len(f.links_out) for f in self.files.values())