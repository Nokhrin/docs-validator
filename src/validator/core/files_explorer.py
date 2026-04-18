"""Поиск файлов документации."""
from datetime import datetime
from pathlib import Path
from typing import Iterator
import logging
from validator.core.models import FileToValidate

log = logging.getLogger(__name__)
DEFAULT_EXTENSIONS = {'.md', '.markdown'}
DEFAULT_EXCLUDES = {
    '.git', '.svn', '.hg',
    '__pycache__', '.pytest_cache', '.mypy_cache',
    'node_modules', 'vendor', 'venv', '.venv',
    'target', 'build', 'dist', '*.egg-info',
}


class FilesExplorer:
    """Рекурсивный поиск по имени файла с учетом исключений."""

    def __init__(
            self,
            root_path: Path,
            extensions_include: set[str] | None = None,
            patterns_exclude: set[str] | None = None,
    ):
        self.root_path = root_path
        self.extensions_include = DEFAULT_EXTENSIONS if extensions_include is None else extensions_include
        self.patterns_exclude = DEFAULT_EXCLUDES if patterns_exclude is None else patterns_exclude

    def _get_title(self, file_path: Path):
        """Возвращает заголовок документа.
        Условия "заголовка":
            - расположение в строке с индексом 0
            - первый символ '# '
        """
        try:
            content: str = file_path.read_text(encoding='utf-8')
            first_line: str = content.split('\n')[0].strip()
            if first_line.startswith('# '):
                return first_line[2:].strip()
        except OSError as err:
            log.debug("Не удалось извлечь заголовок из %s: %s", file_path, err)
        return None

    def _create_file_to_validate(self, file_path: Path) -> FileToValidate:
        """Создает проверяемый файл."""
        relative_path: Path = file_path.relative_to(self.root_path)
        title = self._get_title(file_path) or str(relative_path)

        return FileToValidate(
            path=relative_path,
            title=title,
            last_modified=datetime.fromtimestamp(file_path.stat().st_mtime)
        )

    def _is_excluded(self, file_name: str) -> bool:
        """Признак исключения из проверки."""
        if file_name in self.patterns_exclude:
            return True
        for pattern in self.patterns_exclude:
            if pattern.endswith('*') and file_name.startswith(pattern[:-1]):
                return True
        return False

    def _walk_skip_ignored(self) -> Iterator[Path]:
        """Возвращает генератор обхода дерева каталогов с учетом исключений."""
        for root, dirs, files in self.root_path.walk():
            dirs[:] = [d for d in dirs if not self._is_excluded(d)]

            for file_name in files:
                if not self._is_excluded(file_name):
                    yield root / file_name

    def explore(self) -> Iterator[FileToValidate]:
        """Возвращает генератор файлов требующих проверки."""
        for file_path in self._walk_skip_ignored():
            if file_path.suffix.lower() in self.extensions_include:
                yield self._create_file_to_validate(file_path=file_path)
