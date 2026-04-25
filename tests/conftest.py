"""Глобальные фикстуры для тестов."""
import re

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from validator.cli import create_parser
from validator.core.connectivity_graph import ConnectivityGraph
from validator.core.models import FileToValidate, Link, LinkType


@pytest.fixture
def temp_docs_dir():
    """Создает временную директорию с тестовыми .md-файлами."""
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        yield root


@pytest.fixture
def parser():
    """Фикстура: парсер аргументов."""
    return create_parser()


@pytest.fixture
def markdown_link_pattern():
    """Скомпилированный паттерн Markdown ссылок."""
    return re.compile(r'(!?)\[(.*?)\]\(([^)]+)\)')


@pytest.fixture
def graph():
    return ConnectivityGraph()


@pytest.fixture
def one_md_file(temp_docs_dir):
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
def two_files_valid_link_with_anchor(temp_docs_dir) -> dict[Path, FileToValidate]:
    (temp_docs_dir / "README.md").write_text("[VALID-LINK-WITH-ANCHOR](./guide.md#anchor-link)")
    (temp_docs_dir / "guide.md").write_text("# Guide\nline1\nline2\n### anchor-link\nline3")
    return {
        Path("README.md"): FileToValidate(
            path=Path("README.md"),
            title="README",
            links_out={Link(
                uri="./guide.md",
                link_type=LinkType.INTERNAL,
                parent_file=Path("README.md"),
                line_number=1,
            )}
        ),
        Path("guide.md"): FileToValidate(path=Path("guide.md"), title="Guide"),
    }


@pytest.fixture
def two_files_valid_link_no_anchor(temp_docs_dir) -> dict[Path, FileToValidate]:
    (temp_docs_dir / "README.md").write_text("[VALID-LINK-NO-ANCHOR](./guide.md)")
    (temp_docs_dir / "guide.md").write_text("# Guide")
    return {
        Path("README.md"): FileToValidate(
            path=Path("README.md"),
            title="README",
            links_out={Link(
                uri="./guide.md",
                link_type=LinkType.INTERNAL,
                parent_file=Path("README.md"),
                line_number=1,
            )}
        ),
        Path("guide.md"): FileToValidate(path=Path("guide.md"), title="Guide"),
    }


@pytest.fixture
def two_files_one_orphan(temp_docs_dir) -> dict[Path, FileToValidate]:
    (temp_docs_dir / "README.md").write_text("# Root")
    (temp_docs_dir / "orphan.md").write_text("# Orphan")
    return {
        Path("README.md"): FileToValidate(path=Path("README.md"), title="Root"),
        Path("orphan.md"): FileToValidate(path=Path("orphan.md"), title="Orphan"),
    }


@pytest.fixture
def one_file_broken_link(temp_docs_dir) -> dict[Path, FileToValidate]:
    (temp_docs_dir / "README.md").write_text("[BROKEN-LINK](./missing.md)")
    return {
        Path("README.md"): FileToValidate(
            path=Path("README.md"),
            title="README",
            links_out={Link(
                uri="./missing.md",
                link_type=LinkType.INTERNAL,
                parent_file=Path("README.md"),
                line_number=1,
            )}
        )
    }
