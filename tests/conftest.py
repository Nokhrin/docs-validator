"""Глобальные фикстуры для тестов."""
import re

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from validator.cli import create_parser
from validator.core.connectivity_graph import ConnectivityGraph
from validator.core.models import DocumentationFile, Link, LinkType


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
def root_md_file(temp_docs_dir) -> dict[Path, DocumentationFile]:
    """Создает один тестовый .md-файл с содержимым."""
    file_path = temp_docs_dir / "README.md"
    file_path.write_text(
        "# README Test Document\n\n"
        "[Internal link](./other.md)\n"
        "[External link](https://example.com)\n"
        "[Anchor](#section)\n"
    )
    ftv = DocumentationFile(
        path=file_path,
        title="README",
        links_out={Link(
            uri="./guide.md",
            link_type=LinkType.INTERNAL,
            parent_file=file_path,
            line_number=1,
        )}
    )
    return {file_path: ftv}


@pytest.fixture
def two_files_valid_link_with_anchor(temp_docs_dir) -> dict[Path, DocumentationFile]:
    (temp_docs_dir / "README.md").write_text("[VALID-LINK-WITH-ANCHOR](./guide.md#anchor-link)")
    (temp_docs_dir / "guide.md").write_text("# Guide\nline1\nline2\n### anchor-link\nline3")
    return {
        Path("README.md"): DocumentationFile(
            path=Path("README.md"),
            title="README",
            links_out={Link(
                uri="./guide.md",
                link_type=LinkType.INTERNAL,
                parent_file=Path("README.md"),
                line_number=1,
            )}
        ),
        Path("guide.md"): DocumentationFile(path=Path("guide.md"), title="Guide"),
    }


@pytest.fixture
def two_files_valid_link_no_anchor(temp_docs_dir) -> dict[Path, DocumentationFile]:
    (temp_docs_dir / "README.md").write_text("[VALID-LINK-NO-ANCHOR](./guide.md)")
    (temp_docs_dir / "guide.md").write_text("# Guide")
    return {
        Path("README.md"): DocumentationFile(
            path=Path("README.md"),
            title="README",
            links_out={Link(
                uri="./guide.md",
                link_type=LinkType.INTERNAL,
                parent_file=Path("README.md"),
                line_number=1,
            )}
        ),
        Path("guide.md"): DocumentationFile(path=Path("guide.md"), title="Guide"),
    }


@pytest.fixture
def one_root_one_orphan(temp_docs_dir) -> dict[Path, DocumentationFile]:
    (temp_docs_dir / "README.md").write_text("# Root")
    (temp_docs_dir / "orphan.md").write_text("# Orphan")
    return {
        Path("README.md"): DocumentationFile(path=Path("README.md"), title="Root"),
        Path("orphan.md"): DocumentationFile(path=Path("orphan.md"), title="Orphan"),
    }

@pytest.fixture
def one_root_two_orphans(temp_docs_dir) -> dict[Path, DocumentationFile]:
    (temp_docs_dir / 'README.md').write_text('# Root')
    (temp_docs_dir / 'orphan1.md').write_text('# Orphan 1')
    (temp_docs_dir / 'orphan2.md').write_text('# Orphan 2')
    return {
        Path('README.md'): DocumentationFile(path=Path('README.md'), title='Root'),
        Path('orphan1.md'): DocumentationFile(path=Path('orphan1.md'), title='Orphan 1'),
        Path('orphan2.md'): DocumentationFile(path=Path('orphan2.md'), title='Orphan 2'),
    }


@pytest.fixture
def one_file_one_broken_link(temp_docs_dir) -> dict[Path, DocumentationFile]:
    (temp_docs_dir / "README.md").write_text("[BROKEN-LINK](./missing.md)")
    return {
        Path("README.md"): DocumentationFile(
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

@pytest.fixture
def one_file_multiple_broken_links(temp_docs_dir) -> dict[Path, DocumentationFile]:
    (temp_docs_dir / "README.md").write_text(
        "[Link1](./missing1.md)\n[Link2](./missing2.md)"
    )
    return {
        Path("README.md"): DocumentationFile(
            path=Path("README.md"),
            title="README",
            links_out={
                Link("./missing1.md", LinkType.INTERNAL, Path("README.md"), 1),
                Link("./missing2.md", LinkType.INTERNAL, Path("README.md"), 2),
            }
        )
    }

@pytest.fixture
def one_file_broken_anchor(temp_docs_dir) -> dict[Path, DocumentationFile]:
    (temp_docs_dir / 'README.md').write_text('[BROKEN-LINK](./missing.md)')
    (temp_docs_dir / 'guide.md').write_text('# Guide')
    return {
        Path('README.md'): DocumentationFile(
            path=Path('README.md'),
            title='README',
            links_out={Link(
                uri='./guide.md#missing',
                link_type=LinkType.INTERNAL,
                parent_file=Path('README.md'),
                line_number=1,
                anchor='missing',
            )}
        ),
    }


@pytest.fixture
def three_files_no_cycles(temp_docs_dir) -> dict[Path, DocumentationFile]:
    (temp_docs_dir / 'a.md').write_text('[Link](./b.md)')
    (temp_docs_dir / 'b.md').write_text('[Link](./c.md)')
    (temp_docs_dir / 'c.md').write_text('# End')
    return {
            Path('a.md'): DocumentationFile(
                path=Path('a.md'), title='A', links_out={
                    Link('./b.md', LinkType.INTERNAL, Path('a.md'), 1)
                }
            ),
            Path('b.md'): DocumentationFile(
                path=Path('b.md'), title='B', links_out={
                    Link('./c.md', LinkType.INTERNAL, Path('b.md'), 1)
                }
            ),
            Path('c.md'): DocumentationFile(path=Path('c.md'), title='C'),
        }

@pytest.fixture
def two_files_circular_dep(temp_docs_dir):
    """Создаёт тестовые данные с циклическими зависимостями."""
    (temp_docs_dir / 'a.md').write_text('[Link](./b.md)')
    (temp_docs_dir / 'b.md').write_text('[Link](./a.md)')
    return  {
            Path('a.md'): DocumentationFile(
                path=Path('a.md'), title='A', links_out={
                    Link('./b.md', LinkType.INTERNAL, Path('a.md'), 1)
                }
            ),
            Path('b.md'): DocumentationFile(
                path=Path('b.md'), title='B', links_out={
                    Link('./a.md', LinkType.INTERNAL, Path('b.md'), 1)
                }
            ),
        }