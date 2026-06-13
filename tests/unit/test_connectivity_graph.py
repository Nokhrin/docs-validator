from pathlib import Path

from validator.core.connectivity_graph import ConnectivityGraph
from validator.core.models import DocumentationFile, Link, LinkType


class TestConnectivityGraph:
    def test_connectivity_graph_add_file_increases_node_count_by_one(self):
        graph = ConnectivityGraph()
        file = DocumentationFile(path=Path('README.md'), title='Readme')
        graph.add_file(file)
        assert graph.node_count == 1

    def test_connectivity_graph_add_link_increases_edge_count_by_one(self):
        graph = ConnectivityGraph()
        source_file: Path = Path('README.md')
        target_file: Path = Path('Guide.md')
        file1 = DocumentationFile(path=source_file, title='Readme')
        file2 = DocumentationFile(path=target_file, title='Guide')
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

    def test_connectivity_graph_get_orphans_returns_files_without_incoming_links(self):
        readme_not_orphan = DocumentationFile(path=Path('README.md'), title='Readme')
        guide_orphan = DocumentationFile(path=Path('guide.md'), title='Guide')
        graph = ConnectivityGraph()
        graph.add_file(readme_not_orphan)
        graph.add_file(guide_orphan)
        orphans: list[Path] = list(graph.get_orphans())
        assert len(orphans) == 1
        assert Path('README.md') not in orphans
        assert Path('guide.md') in orphans

    def test_connectivity_graph_get_unreachable_returns_disconnected_nodes(self):
        graph = ConnectivityGraph()
        readme_file = DocumentationFile(path=Path('README.md'), title='Readme')
        reachable_file = DocumentationFile(path=Path('reachable.md'), title='reachable Guide')
        unreachable_file = DocumentationFile(path=Path('unreachable.md'), title='unreachable Guide')
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

    def test_connectivity_graph_node_count_returns_total_files(self):
        graph = ConnectivityGraph()
        source_file: Path = Path('README.md')
        target_file: Path = Path('Guide.md')
        file1 = DocumentationFile(path=source_file, title='Readme')
        file2 = DocumentationFile(path=target_file, title='Guide')
        graph.add_file(file1)
        graph.add_file(file2)
        assert graph.node_count == 2

    def test_connectivity_graph_edge_count_returns_total_links(self):
        graph = ConnectivityGraph()
        source_file: Path = Path('README.md')
        target_file: Path = Path('Guide.md')
        file1 = DocumentationFile(path=source_file, title='Readme')
        file2 = DocumentationFile(path=target_file, title='Guide')
        graph.add_file(file1)
        graph.add_file(file2)
        assert graph.edge_count == 0