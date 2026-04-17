"""Тесты для модуля поиска файлов."""
from pathlib import Path
from validator.core.files_explorer import FilesExplorer


class TestFilesExplorer:
    """Тестирование рекурсивного поиска файлов."""

    def test_explore_finds_markdown_files(self, temp_docs_dir):
        """Сканер находит файлы с расширениями .md и .markdown."""
        (temp_docs_dir / "README.md").write_text("# Root")
        (temp_docs_dir / "guide.markdown").write_text("# Guide")
        (temp_docs_dir / "notes.txt").write_text("Should be ignored")

        explorer = FilesExplorer(temp_docs_dir)

        files = list(explorer.explore())

        assert len(files) == 2
        paths = {f.path for f in files}
        assert Path("README.md") in paths
        assert Path("guide.markdown") in paths
