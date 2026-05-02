#!/usr/bin/env python3
"""Примеры использования валидатора для отладки.

Запуск:
    python examples/debug_workspace.py
    python examples/debug_workspace.py /path/to/docs
"""
import logging

from tests.conftest import two_files_valid_link_with_anchor
from validator import setup_logging
from pathlib import Path
from tempfile import TemporaryDirectory

from validator.cli import create_parser
from validator.core.connectivity_graph import ConnectivityGraph
from validator.core.files_explorer import FilesExplorer
from validator.core.link_extractor import LinkExtractor
from validator.core.models import DocumentationFile, Link, LinkType
from validator.validators import OrphanFileValidator, BrokenLinkValidator, AnchorLinkValidator

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

    log.debug('Debug workspace: %s', root)
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
    return 0



def create_test_data_orphan(temp_dir: Path) -> dict[Path, DocumentationFile]:
    """Создаёт тестовые данные для OrphanFileValidator."""
    (temp_dir / "README.md").write_text("# Root")
    (temp_dir / "orphan.md").write_text("# Orphan")
    return {
        Path("README.md"): DocumentationFile(path=Path("README.md"), title="Root"),
        Path("orphan.md"): DocumentationFile(path=Path("orphan.md"), title="Orphan"),
    }


def create_test_data_broken(temp_dir: Path) -> dict[Path, DocumentationFile]:
    """Создаёт тестовые данные для BrokenLinkValidator."""
    (temp_dir / "README.md").write_text("[BROKEN](./missing.md)")
    return {
        Path("README.md"): DocumentationFile(
            path=Path("README.md"),
            title="README",
            links_out={Link(
                uri="./missing.md",
                link_type=LinkType.INTERNAL,
                parent_file=Path("README.md"),
                line_number=1,
            )}
        )
    }


def create_test_data_anchor(temp_dir: Path) -> dict[Path, DocumentationFile]:
    """Создаёт тестовые данные для AnchorLinkValidator."""
    (temp_dir / "README.md").write_text("[Link](./guide.md#anchor)")
    (temp_dir / "guide.md").write_text("# Guide\n### anchor\n")
    return {
        Path("README.md"): DocumentationFile(
            path=Path("README.md"),
            title="README",
            links_out={Link(
                uri="./guide.md#anchor",
                link_type=LinkType.INTERNAL,
                parent_file=Path("README.md"),
                line_number=1,
                anchor="anchor",
            )}
        ),
        Path("guide.md"): DocumentationFile(path=Path("guide.md"), title="Guide"),
    }


def check_validators():
    """Запускает валидаторы на тестовых данных."""
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # OrphanFileValidator
        log.debug('=== OrphanFileValidator ===')
        ofv = OrphanFileValidator()
        orphan_data = create_test_data_orphan(temp_path)
        orphan_issues = ofv.validate(files_to_validate=orphan_data, root_dir=temp_path)
        log.debug('Найдено проблем: %d', len(orphan_issues))
        for issue in orphan_issues:
            log.warning('  - %s: %s', issue.issue_type.name, issue.message)
        # 19:00:15 [DEBUG] validator.validators.orphan_file: Найден сирота: orphan.md

        # BrokenLinkValidator
        log.debug('=== BrokenLinkValidator ===')
        blv = BrokenLinkValidator()
        broken_data = create_test_data_broken(temp_path)
        broken_issues = blv.validate(files_to_validate=broken_data, root_dir=temp_path)
        log.debug('Найдено проблем: %d', len(broken_issues))
        for issue in broken_issues:
            log.warning('  - %s: %s', issue.issue_type.name, issue.message)
        # 19:01:00 [DEBUG] validator.validators.broken_link: Не найден адресуемый файл: missing.md по ссылке Link(uri='./missing.md', link_type=<LinkType.INTERNAL: 1>, parent_file=PosixPath('README.md'), line_number=1, anchor=None)

        # AnchorLinkValidator
        log.debug('=== AnchorLinkValidator ===')
        alv = AnchorLinkValidator()
        anchor_data = create_test_data_anchor(temp_path)
        anchor_issues = alv.validate(files_to_validate=anchor_data, root_dir=temp_path)
        log.debug('Найдено проблем: %d', len(anchor_issues))
        for issue in anchor_issues:
            log.warning('  - %s: %s', issue.issue_type.name, issue.message)
        # TODO
        # 19:02:15 [DEBUG] validator.validators.anchor_link: проверка якоря - заглушка
        
    return 0


if __name__ == '__main__':
    setup_logging()
    # parse()
    # make_graph()
    check_validators()
