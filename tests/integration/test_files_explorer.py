from pathlib import Path
from validator.core.explorer import FilesExplorer


class TestFilesExplorer:
    def test_files_explorer_finds_md_and_markdown_extensions_returns_two_files(self, tmp_path: Path):
        (tmp_path / 'README.md').write_text('# Root')
        (tmp_path / 'guide.markdown').write_text('# Guide')
        (tmp_path / 'notes.txt').write_text('Should be ignored')

        explorer = FilesExplorer(tmp_path)
        files = list(explorer.find_files())

        assert len(files) == 2
        paths = {f.path for f in files}
        assert Path('README.md') in paths
        assert Path('guide.markdown') in paths

    def test_files_explorer_custom_directory_exclusion_ignores_target_dir(self, tmp_path: Path):
        (tmp_path / 'doc.md').write_text('# Doc')

        custom_dir = tmp_path / 'custom_ignore'
        custom_dir.mkdir()
        (custom_dir / 'ignored.md').write_text('# Ignored')

        normal_dir = tmp_path / 'normal_dir'
        normal_dir.mkdir()
        (normal_dir / 'found.md').write_text('# Found')

        explorer = FilesExplorer(
            root_path=tmp_path,
            patterns_exclude={'custom_ignore'}
        )

        files = list(explorer.find_files())
        found_paths = {f.path.name for f in files}

        assert len(files) == 2
        assert 'doc.md' in found_paths
        assert 'found.md' in found_paths
        assert 'ignored.md' not in found_paths