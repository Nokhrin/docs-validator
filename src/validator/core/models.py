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
    Values:
        INTERNAL: Относительный путь к файлу
        EXTERNAL: Веб-адрес или почта
        ANCHOR: Якорь раздела
        IMAGE: Ссылка на изображение
    """
    INTERNAL = auto()
    EXTERNAL = auto()
    ANCHOR = auto()
    IMAGE = auto()

class SeverityLevel(Enum):
    """Уровень критичности.
    Values:
        ERROR: Критическая ошибка валидации
        WARNING: Предупреждение, не блокирующее
        INFO: Информационное сообщение
    """
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class IssueType(Enum):
    """Тип проблемы валидации.
    Values:
        BROKEN_LINK: Ссылка на несуществующий файл
        MISSING_ANCHOR: Якорь не найден
        ORPHAN_FILE: Файл без входящих ссылок
        CIRCULAR_DEPENDENCY: Циклическая зависимость файлов
        EXTERNAL_UNREACHABLE: Внешний ресурс недоступен
    """
    BROKEN_LINK = "broken_link"
    MISSING_ANCHOR = "missing_anchor"
    ORPHAN_FILE = "orphan_file"
    CIRCULAR_DEPENDENCY = "circular"
    EXTERNAL_UNREACHABLE = "external_404"

@dataclass(frozen=True)
class Link:
    """Ссылка, извлеченная из документации.
    Args:
        uri: URI строка ссылки
        link_type: Тип ссылки (INTERNAL/EXTERNAL/ANCHOR/IMAGE)
        parent_file: Файл-источник ссылки
        line_number: Номер строки в файле
        anchor: Якорь раздела (опционально)
    """
    uri: str
    link_type: LinkType
    parent_file: Path
    line_number: int
    anchor: str | None = None

    @property
    def is_internal(self) -> bool:
        """Внутренняя ссылка.
        Returns:
            True если относительный путь к файлу
        """
        return self.link_type is LinkType.INTERNAL

    @property
    def is_external(self) -> bool:
        """Внешняя ссылка.
        Returns:
            True если веб-адрес или почта
        """
        return self.link_type is LinkType.EXTERNAL

    @property
    def target_file(self) -> Path | None:
        """Относительный путь к целевому файлу.
        Returns:
            Path к файлу или None
        """
        if self.is_internal:
            if self.uri:
                return Path(self.uri.split('#')[0])
        return None

@dataclass
class FileToValidate:
    """Файл, в котором проверяются ссылки.
    Args:
        path: Относительный путь к файлу
        title: Заголовок документа
        links_out: Исходящие ссылки из файла
        links_in: Входящие ссылки в файл
        word_count: Количество слов в файле
        last_modified: Дата последнего изменения
    """
    path: Path
    title: str
    links_out: set[Link] = field(default_factory=set)
    links_in: set[Link] = field(default_factory=set)
    word_count: int = 0
    last_modified: Optional[datetime] = None

    @property
    def is_orphan(self) -> bool:
        """Не содержит входящих ссылок.
        Returns:
            True если links_in пуст
        """
        return len(self.links_in) == 0

@dataclass
class ValidationIssue:
    """Проблема, обнаруженная при проверке.
    Args:
        issue_type: Тип проблемы валидации
        severity_level: Уровень критичности (ERROR/WARNING/INFO)
        src_file: Файл-источник проблемы
        link: Связанная ссылка (опционально)
        message: Текст сообщения об ошибке
        suggestion: Рекомендация по исправлению
    """
    issue_type: IssueType
    severity_level: SeverityLevel
    src_file: FileToValidate
    link: Optional[Link] = None
    message: str = ''
    suggestion: str | None = None

@dataclass
class ValidationResult:
    """Результат проверки.
    Args:
        files_processed: Словарь обработанных файлов
        issues: Список найденных проблем
    """
    files_processed: dict[Path, FileToValidate]
    issues: list[ValidationIssue]

    @property
    def has_errors(self) -> bool:
        """Наличие ERROR в результатах проверки.
        Returns:
            True если есть ERROR issues
        """
        return any(issue.severity_level == SeverityLevel.ERROR for issue in self.issues)

    @property
    def is_valid(self) -> bool:
        """Не проходит проверку, если результат содержит ERROR.
        Returns:
            True если нет ERROR issues
        """
        return not self.has_errors
