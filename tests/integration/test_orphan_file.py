from pathlib import Path

from validator.core.models import DocumentationFile, IssueType
from validator.rules import OrphanFileValidator


class TestOrphanFileValidator:

    def test_orphan_excludes_mkdocs_nav(self, tmp_path: Path):
        (tmp_path / 'mkdocs.yml').write_text("""
    nav:
      - Home: index.md
      - Guide:
        - Intro: guide/intro.md
        - Advanced: guide/advanced.md
    """)

        (tmp_path / 'index.md').write_text('# Home')
        (tmp_path / 'orphan.md').write_text('# Orphan')

        guide_dir = tmp_path / 'guide'
        guide_dir.mkdir(exist_ok=True)
        (guide_dir / 'intro.md').write_text('# Intro')
        (guide_dir / 'advanced.md').write_text('# Advanced')

        files = {
            Path('index.md'): DocumentationFile(path=Path('index.md'), title='Home'),
            Path('guide/intro.md'): DocumentationFile(path=Path('guide/intro.md'), title='Intro'),
            Path('guide/advanced.md'): DocumentationFile(path=Path('guide/advanced.md'), title='Advanced'),
            Path('orphan.md'): DocumentationFile(path=Path('orphan.md'), title='Orphan'),
        }

        validator = OrphanFileValidator()
        issues = validator.validate(files, tmp_path)

        orphan_issues = [i for i in issues if i.issue_type == IssueType.ORPHAN_FILE]
        assert len(orphan_issues) == 1
        assert orphan_issues[0].src_file.path == Path('orphan.md')

    def test_orphan_excludes_mkdocs_paths_without_suffix(self, tmp_path: Path):
        """
        Сценарий:
        - В mkdocs.yml навигация содержит пути без .md: guide/intro, guide/advanced
        - Файлы guide/intro.md и guide/advanced.md существуют
        - Файл orphan.md не указан в навигации и не имеет входящих ссылок
        - Ожидается: только orphan.md помечен как сирота
        """
        (tmp_path / 'mkdocs.yml').write_text("""
    site_name: Test
    nav:
      - Home: index
      - Guide:
        - Intro: guide/intro
        - Advanced: guide/advanced
    """, encoding='utf-8')

        (tmp_path / 'index.md').write_text('# Home')
        guide_dir = tmp_path / 'guide'
        guide_dir.mkdir()
        (guide_dir / 'intro.md').write_text('# Intro')
        (guide_dir / 'advanced.md').write_text('# Advanced')
        (tmp_path / 'orphan.md').write_text('# Orphan')

        files = {
            Path('index.md'): DocumentationFile(path=Path('index.md'), title='Home'),
            Path('guide/intro.md'): DocumentationFile(path=Path('guide/intro.md'), title='Intro'),
            Path('guide/advanced.md'): DocumentationFile(path=Path('guide/advanced.md'), title='Advanced'),
            Path('orphan.md'): DocumentationFile(path=Path('orphan.md'), title='Orphan'),
        }

        validator = OrphanFileValidator()
        issues = validator.validate(files, tmp_path)

        orphan_issues = [i for i in issues if i.issue_type == IssueType.ORPHAN_FILE]

        assert len(orphan_issues) == 1
        assert orphan_issues[0].src_file.path == Path('orphan.md')

        orphan_paths = {i.src_file.path for i in orphan_issues}
        assert Path('guide/intro.md') not in orphan_paths
        assert Path('guide/advanced.md') not in orphan_paths
        assert Path('index.md') not in orphan_paths