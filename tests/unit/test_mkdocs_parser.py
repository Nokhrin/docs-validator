from pathlib import Path

from validator.core.mkdocs_parser import get_nav_roots


class TestGetNavRoots:
    def test_mkdocs_file_not_exists(self, tmp_path):
        mkdocs_path = tmp_path / "mkdocs.yml"
        result = get_nav_roots(mkdocs_path)
        assert result == set()

    def test_mkdocs_empty_nav(self, tmp_path):
        mkdocs_path = tmp_path / "mkdocs.yml"
        mkdocs_path.write_text("site_name: Test\nnav: []")
        result = get_nav_roots(mkdocs_path)
        assert result == set()

    def test_mkdocs_simple_list(self, tmp_path):
        mkdocs_path = tmp_path / "mkdocs.yml"
        mkdocs_path.write_text("site_name: Test\nnav:\n  - index.md\n  - about.md")
        result = get_nav_roots(mkdocs_path)
        assert Path("index.md") in result
        assert Path("about.md") in result

    def test_mkdocs_nested_structure(self, tmp_path):
        mkdocs_path = tmp_path / "mkdocs.yml"
        mkdocs_path.write_text(
            "site_name: Test\nnav:\n  - Home: index.md\n  - Guide:\n    - Intro: guide/intro.md\n    - Advanced: guide/advanced.md"
        )
        result = get_nav_roots(mkdocs_path)
        assert Path("index.md") in result
        assert Path("guide/intro.md") in result
        assert Path("guide/advanced.md") in result

    def test_mkdocs_adds_md_suffix(self, tmp_path):
        mkdocs_path = tmp_path / "mkdocs.yml"
        mkdocs_path.write_text("site_name: Test\nnav:\n  - index\n  - about")
        result = get_nav_roots(mkdocs_path)
        assert Path("index.md") in result
        assert Path("about.md") in result

    def test_mkdocs_preserves_existing_suffix(self, tmp_path):
        mkdocs_path = tmp_path / "mkdocs.yml"
        mkdocs_path.write_text("site_name: Test\nnav:\n  - index.md\n  - about.rst")
        result = get_nav_roots(mkdocs_path)
        assert Path("index.md") in result
        assert Path("about.rst") in result

    def test_mkdocs_yaml_error(self, tmp_path):
        mkdocs_path = tmp_path / "mkdocs.yml"
        mkdocs_path.write_text("site_name: Test\nnav:\n  - invalid: yaml: syntax:")
        result = get_nav_roots(mkdocs_path)
        assert result == set()

    def test_mkdocs_io_error(self, tmp_path, mocker):
        mkdocs_path = tmp_path / "mkdocs.yml"
        mocker.patch("builtins.open", side_effect=IOError("Permission denied"))
        result = get_nav_roots(mkdocs_path)
        assert result == set()

    def test_mkdocs_no_nav_section(self, tmp_path):
        mkdocs_path = tmp_path / "mkdocs.yml"
        mkdocs_path.write_text("site_name: Test\ntheme: readthedocs")
        result = get_nav_roots(mkdocs_path)
        assert result == set()

    def test_mkdocs_complex_mixed_structure(self, tmp_path):
        mkdocs_path = tmp_path / "mkdocs.yml"
        mkdocs_path.write_text(
            "site_name: Test\nnav:\n  - Home: index.md\n  - \n    - Guide:\n      - intro.md\n      - advanced.md\n  - API: api.md"
        )
        result = get_nav_roots(mkdocs_path)
        assert Path("index.md") in result
        assert Path("intro.md") in result
        assert Path("api.md") in result