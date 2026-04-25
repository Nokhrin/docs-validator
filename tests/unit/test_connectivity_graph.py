from pathlib import Path

import pytest

from validator.core.models import FileToValidate, Link, LinkType


class TestConnectivityGraph:
    def test_add_file(self, graph):
        """Добавление файла создает узел в графе."""
        file = FileToValidate(path=Path('README.md'), title='Readme')
        graph.add_file(file)
        assert graph.node_count == 1

    def test_add_link(self, graph):
        """Добавление ссылки создает ребро в графе."""
        source_file: Path = Path('README.md')
        target_file: Path = Path('Guide.md')
        file1 = FileToValidate(path=source_file, title='Readme')
        file2 = FileToValidate(path=target_file, title='Guide')
        graph.add_file(file1)
        graph.add_file(file2)
        link = Link(
            uri=f'./{target_file.name}',
            link_type=LinkType.INTERNAL,
            parent_file=source_file,
            line_number=1,
        )
        graph.add_link(link)
        assert graph.edge_count == 1

    def test_get_orphans(self, graph):
        """Корректно определен файл без входящих ссылок."""
        readme_not_orphan = FileToValidate(path=Path('README.md'), title='Readme')
        guide_orphan = FileToValidate(path=Path('guide.md'), title='Guide')
        graph.add_file(readme_not_orphan)
        graph.add_file(guide_orphan)
        orphans: list[Path] = list(graph.get_orphans())
        assert len(orphans) == 1
        assert Path('README.md') not in orphans
        assert Path('guide.md') in orphans

    def test_get_unreachable(self, graph):
        """Корректно определены узлы по признаку связи."""
        readme_file = FileToValidate(path=Path('README.md'), title='Readme')
        reachable_file = FileToValidate(path=Path('reachable.md'), title='reachable Guide')
        unreachable_file = FileToValidate(path=Path('unreachable.md'), title='unreachable Guide')
        graph.add_file(readme_file)
        graph.add_file(reachable_file)
        graph.add_file(unreachable_file)
        link = Link(
            uri=f'./{reachable_file.path.name}',
            link_type=LinkType.INTERNAL,
            parent_file=readme_file.path,
            line_number=10,
        )
        graph.add_link(link)
        unreachable_files: list[Path] = list(graph.get_unreachable(readme_file.path))
        assert len(unreachable_files) == 1
        assert unreachable_file.path in unreachable_files
        assert reachable_file.path not in unreachable_files

    def test_node_count(self, graph):
        """Корректно определено количество узлов."""
        source_file: Path = Path('README.md')
        target_file: Path = Path('Guide.md')
        file1 = FileToValidate(path=source_file, title='Readme')
        file2 = FileToValidate(path=target_file, title='Guide')
        graph.add_file(file1)
        graph.add_file(file2)
        assert graph.node_count == 2

    def test_edge_count(self, graph):
        """Корректно определено количество ребер."""
        source_file: Path = Path('README.md')
        target_file: Path = Path('Guide.md')
        file1 = FileToValidate(path=source_file, title='Readme')
        file2 = FileToValidate(path=target_file, title='Guide')
        graph.add_file(file1)
        graph.add_file(file2)

        assert graph.edge_count == 0
