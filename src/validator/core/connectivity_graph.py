"""Граф связности документов."""
from functools import cached_property
from pathlib import Path
from typing import Iterator, cast

import networkx as nx

from validator.core.models import FileToValidate, Link

DEFAULT_ROOT_FILES = {
    'README.md', 'README.rst', 'README.txt',
    'index.md', 'index.html', 'index.rst',
}

class ConnectivityGraph:
    """Направленный граф: файл -> ссылка -> файл"""
    def __init__(self):
        """
        Файл: физический файл -> экземпляр файла для валидации
        """
        self._graph = nx.DiGraph()
        self._files: dict[Path, FileToValidate] = {}

    def add_file(self, file_to_validate: FileToValidate) -> None:
        """Добавляет файл как узел графа.
        Узел - физический файл, атрибут узла title: заголовок в файле
        G.add_node(Path('/tmp/filename'), title='header')
        """
        self._files[file_to_validate.path] = file_to_validate
        self._graph.add_node(file_to_validate.path, title=file_to_validate.title)

    def add_link(self, link: Link) -> None:
        """Добавляет ссылку как направленное ребро графа.

        Args:
            link: Объект Link с метаданными.

        Note:
            Внешние ссылки (http://, https://, mailto:) не добавляются в граф

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
        """Возвращает файлы без входящих ссылок.
        Генератор.
        """
        excludes = exclude_filenames if exclude_filenames else DEFAULT_ROOT_FILES
        for node in self._graph.nodes():
            node_path: Path = cast(Path, node)
            if self._graph.in_degree(node) == 0:
                if node_path.name not in excludes:
                    yield node_path

    def get_unreachable(self, start: Path) -> Iterator[Path]:
        """Возвращает файлы существующие, но недоступные при обходе от start.
        Генератор.
        Включает стартовый узел как достижимый

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

    @property
    def node_count(self) -> int:
        """Количество файлов."""
        return self._graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        """Количество ссылок."""
        return self._graph.number_of_edges()

    @cached_property
    def orphan_files(self) -> set[Path]:
        """Файлы, не содержащие входящих ссылок."""
        return set(self.get_orphans())
