"""Глобальные фикстуры для тестов."""
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory


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