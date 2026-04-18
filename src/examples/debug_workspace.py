#!/usr/bin/env python3
"""Примеры использования валидатора для отладки.

Запуск:
    python examples/debug_workspace.py
    python examples/debug_workspace.py /path/to/docs
"""
import logging
from pathlib import Path
from tempfile import TemporaryDirectory

from validator.cli import create_parser
from validator.core.files_explorer import FilesExplorer
from validator.core.link_extractor import LinkExtractor
from validator.core.models import FileToValidate, Link
from validator.logging_config import setup_logging
from validator.serializers import files_to_json


log = logging.getLogger(__name__)

def create_debug_workspace():
    """Создает временную структуру для ручной отладки.

    python -c "from validator.debug import create_debug_workspace; create_debug_workspace()"
    """
    tmp = TemporaryDirectory(delete=False, prefix='debug_validator_')
    root = Path(tmp.name)

    (root / 'README.md').write_text('# Root\n[Link](./docs/guide.md)')
    (root / 'docs').mkdir()
    (root / 'docs' / 'guide.md').write_text('# Guide\n[Back](../README.md#root)')

    log.info(f'Debug workspace: {root}')
    return root

def main():
    setup_logging('DEBUG')

    parser = create_parser()
    # Симуляция cli - чтение docs данного проекта
    # docs-validator scan [RELATIVE_PATH] --report json --log-level debug
    cmd_args = parser.parse_args(['scan', '../../', '--report', 'json'])
    # cmd_args = parser.parse_args()
    log.debug(f'Переданы аргументы: {cmd_args}')

    # создание тестовой директории документов
    # workspace = create_debug_workspace()
    workspace = cmd_args.path

    # проводник
    files_to_validate = FilesExplorer(workspace)
    log.debug(f'Обнаружены файлы:\n{list(files_to_validate.explore())}')

    for file in files_to_validate.explore():
        content = (workspace / file.path).read_text(encoding='utf-8')

        log.debug(f'Файл {file.path.resolve()}\nсодержит:\n{content}')

        link_extractor = LinkExtractor(file.path)
        links = link_extractor.get_links_from_file(content)
        log.debug(f'Найдено всего ссылок:\n{file.links_out} ссылки:\n{links}')
        for link in file.links_out:
            log.debug(f'{link.link_type.name} - {link.uri} - {link.line_number}')
    return 0


if __name__ == '__main__':
    main()