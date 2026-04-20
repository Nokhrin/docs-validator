#!/usr/bin/env python3
"""Примеры использования валидатора для отладки.

Запуск:
    python examples/debug_workspace.py
    python examples/debug_workspace.py /path/to/docs
"""
import logging
from validator import setup_logging
from pathlib import Path
from tempfile import TemporaryDirectory

from validator.cli import create_parser
from validator.core.connectivity_graph import ConnectivityGraph
from validator.core.files_explorer import FilesExplorer
from validator.core.link_extractor import LinkExtractor
from validator.validators import OrphanFileValidator

log = logging.getLogger('validator.debug')

def create_debug_workspace():
    """Создает временную структуру для ручной отладки.

    python -c "from validator.debug import create_debug_workspace; create_debug_workspace()"
    """
    tmp = TemporaryDirectory(delete=False, prefix='debug_validator_')
    root = Path(tmp.name)

    (root / 'README.md').write_text('# Root\n[Link](./docs/guide.md)')
    (root / 'docs').mkdir()
    (root / 'docs' / 'guide.md').write_text('# Guide\n[Back](../README.md#root)')

    log.info('Debug workspace: %s', root)
    return root

def parse():
    parser = create_parser()
    # Симуляция cli - чтение docs данного проекта
    # docs-validator scan [RELATIVE_PATH] --report json --log-level debug
    cmd_args = parser.parse_args(['scan', '../../', '--report', 'json'])
    # cmd_args = parser.parse_args()
    log.debug('Переданы аргументы: %s', cmd_args)

    # создание тестовой директории документов
    # workspace = create_debug_workspace()
    workspace = cmd_args.path

    # проводник
    files_to_validate = FilesExplorer(workspace)
    log.debug('Обнаружены файлы: %s', list(files_to_validate.explore()))

    for file in files_to_validate.explore():
        content = (workspace / file.path).read_text(encoding='utf-8')

        log.debug('Файл %s\nсодержит:\n%s', file.path.resolve(), content)

        link_extractor = LinkExtractor(file.path)
        links = list(link_extractor.get_links_from_file(content))
        log.debug('Найдено ссылок: %d', len(links))
        for link in file.links_out:
            log.debug('%s - %s - %d', link.link_type.name, link.uri, link.line_number)
    return 0

def make_graph():
    workspace = create_debug_workspace()
    files_to_validate = list(FilesExplorer(workspace).explore())

    graph = ConnectivityGraph()
    log.debug('Тип графа: %s', type(graph._graph))

    for file in files_to_validate:
        graph.add_file(file_to_validate=file)

        link_extractor = LinkExtractor(file.path)
        content = (workspace / file.path).read_text(encoding='utf-8')
        links = link_extractor.get_links_from_file(content)
        for link in links:
            graph.add_link(link=link)
        log.debug('Узлы: %s', list(graph._graph.nodes))
        log.debug('Ребра: %s', list(graph._graph.edges))

        # 1 - edges
        # [(
        # PosixPath('/home/nohal/projects/docs-validator/src/validator/README.md'),
        # PosixPath('/home/nohal/projects/docs-validator/src/validator/docs/guide.md')
        # )]

        # 2 - edges
        # [
        # (
        # PosixPath('/home/nohal/projects/docs-validator/src/validator/README.md'),
        # PosixPath('/home/nohal/projects/docs-validator/src/validator/docs/guide.md')
        # ),
        # (
        # PosixPath('/home/nohal/projects/docs-validator/src/validator/docs/guide.md'),
        # PosixPath('/home/nohal/projects/docs-validator/src/README.md#root')
        # )
        # ]

    ofv = OrphanFileValidator()

    log.debug('OrphanFileValidator: %s', ofv)
    return 0

if __name__ == '__main__':

    setup_logging()
    # parse()
    make_graph()