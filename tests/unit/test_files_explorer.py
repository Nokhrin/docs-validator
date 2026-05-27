"""Тесты для модуля поиска файлов."""
from pathlib import Path
from validator.core.explorer import FilesExplorer


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


def test_custom_directory_exclusion(temp_docs_dir: Path):
    """Проверка исключения пользовательского каталога через patterns_exclude.
    
    Структура тестового каталога:
    temp_docs_dir/
      ├── doc.md (должен быть найден)
      ├── custom_ignore/
      │   └── ignored.md (должен быть ИСКЛЮЧЕН)
      └── normal_dir/
          └── found.md (должен быть найден)
    """

    (temp_docs_dir / 'doc.md').write_text('# Doc')

    custom_dir = temp_docs_dir / 'custom_ignore'
    custom_dir.mkdir()
    (custom_dir / 'ignored.md').write_text('# Ignored')

    normal_dir = temp_docs_dir / 'normal_dir'
    normal_dir.mkdir()
    (normal_dir / 'found.md').write_text('# Found')

    explorer = FilesExplorer(
        root_path=temp_docs_dir,
        patterns_exclude={'custom_ignore'}
    )

    files = list(explorer.explore())
    found_paths = {f.path.name for f in files}

    assert len(files) == 2
    assert 'doc.md' in found_paths, 'Корневой файл должен быть найден'
    assert 'found.md' in found_paths, 'Файл в обычном каталоге должен быть найден'
    assert 'ignored.md' not in found_paths, 'Файл в исключенном каталоге не должен быть найден'

