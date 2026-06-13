import logging
from functools import cached_property
from pathlib import Path
from typing import Iterator, cast

import networkx as nx

from validator.core.models import DocumentationFile, Link

log = logging.getLogger(__name__)
DEFAULT_ROOT_FILES = {
    'README.md', 'README.rst', 'README.txt',
    'index.md', 'index.html', 'index.rst',
}


class ConnectivityGraph:
    """Directed graph representing document connectivity: file -> link -> file."""

    def __init__(self):
        """Initialize the graph structure and file mapping."""
        self._graph = nx.DiGraph()
        self._files: dict[Path, DocumentationFile] = {}

    def add_file(self, file_to_validate: DocumentationFile) -> None:
        """Add a documentation file as a node in the graph.

        The node is represented by the physical file path.
        The document's title is stored as a node attribute.
        Example: G.add_node(Path('/tmp/filename'), title='header')
        """
        self._files[file_to_validate.path] = file_to_validate
        self._graph.add_node(file_to_validate.path, title=file_to_validate.title)

    def add_link(self, link: Link) -> None:
        """Add a link as a directed edge in the graph.

        Args:
            link: Link object containing metadata.

        Note:
            External links (http://, https://, mailto:) are ignored and not added to the graph.

        Example of resulting AdjacencyView:
        AdjacencyView({
            PosixPath('/tmp/file_home'): {PosixPath('/tmp/file_target'): {}},
            PosixPath('/tmp/file_target'): {PosixPath('/tmp/file_home'): {}}
        })
        """
        if link.is_internal:
            self._graph.add_edge(
                link.parent_file,
                link.target_file,
                link_type=link.link_type.name,
                line_number=link.line_number,
                anchor=link.anchor,
            )

    def get_orphans(self, exclude_filenames: set[str] | None = None) -> Iterator[Path]:
        """Yield files that have no incoming links (orphan files).

        Yields:
            Path objects representing orphan files.
        """
        excludes = exclude_filenames if exclude_filenames else DEFAULT_ROOT_FILES
        for node in self._graph.nodes():
            node_path: Path = cast(Path, node)
            if self._graph.in_degree(node) == 0:
                if node_path.name not in excludes:
                    yield node_path

    def get_unreachable(self, start: Path) -> Iterator[Path]:
        """Yield existing files that are unreachable when traversing from the start node.

        The start node itself is considered reachable.

        Yields:
            Path objects representing unreachable files.

        Example:
            nx.descendants(G, Path('/tmp/file_home'))
            {PosixPath('/tmp/file_target')}

            nx.descendants(G, Path('/tmp/file_target'))
            {PosixPath('/tmp/file_home')}
        """
        reachable = {start}
        reachable.update(nx.descendants(self._graph, start))
        for node in self._graph.nodes():
            if node not in reachable:
                yield cast(Path, node)

    def get_simple_cycles(self) -> list[list[Path]]:
        cycles = []
        try:
            cycles = list(nx.simple_cycles(self._graph))
        except ValueError as err:
            log.warning('Ошибка при поиске циклов в графе: %s', err)
        return cycles

    @property
    def node_count(self) -> int:
        """Return the total number of files (nodes) in the graph."""
        return self._graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        """Return the total number of links (edges) in the graph."""
        return self._graph.number_of_edges()

    @cached_property
    def orphan_files(self) -> set[Path]:
        """Return a cached set of files that have no incoming links."""
        return set(self.get_orphans())
