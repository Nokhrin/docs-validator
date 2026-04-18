"""Глобальные фикстуры для тестов."""
import re

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from validator.cli import create_parser


@pytest.fixture
def temp_docs_dir():
    """Создает временную директорию с тестовыми .md-файлами."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        yield root


@pytest.fixture
def sample_markdown_file(temp_docs_dir):
    """Создает один тестовый .md-файл с содержимым."""
    file_path = temp_docs_dir / "test.md"
    file_path.write_text(
        "# Test Document\n\n"
        "[Internal link](./other.md)\n"
        "[External link](https://example.com)\n"
        "[Anchor](#section)\n"
    )
    return file_path


@pytest.fixture
def parser():
    """Фикстура: парсер аргументов."""
    return create_parser()

@pytest.fixture
def markdown_link_pattern():
    """Скомпилированный паттерн Markdown ссылок."""
    return re.compile(r'(!?)\[(.*?)\]\(([^)]+)\)')