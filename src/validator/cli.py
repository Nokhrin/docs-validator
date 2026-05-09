"""
CLI валидатора документации.

Usage:
    docs-validator scan <path> [OPTIONS]
    docs-validator --help

Examples:
    docs-validator scan ./docs
    docs-validator scan ./docs --report json --output report.json
    docs-validator scan ./docs --is_validate --fail-on-error
    docs-validator scan ./docs --exclude_patterns .git --exclude_patterns node_modules
    docs-validator --help

Commands:
    scan        Scan documentation directory for broken links

Options:
    --report FORMAT     Report format: markdown, json (default: markdown)
    --output PATH       Output file path (default: stdout)
    --exclude_patterns PATTERN   exclude_patterns pattern (can be specified multiple times)
    --log-level LEVEL   Logging level: debug, info, warning, error (default: warning)
    --is_validate          Run validators after scanning
    --fail-on-error     Exit with code 1 if any ERROR issues found
    --help              Show this help message and exit
"""
import argparse
import logging
from argparse import ArgumentParser
from pathlib import Path

from validator import setup_logging
from validator.config import load_config_from_toml, ValidatorConfig
from validator.core.files_explorer import FilesExplorer
from validator.core.link_extractor import LinkExtractor
from validator.core.models import DocumentationFile, ValidationIssue, SeverityLevel
from validator.serializers import files_to_json
from validator.validators import BrokenLinkValidator, OrphanFileValidator, AnchorLinkValidator, \
    CircularDependencyValidator

log = logging.getLogger(__name__)


def create_parser() -> ArgumentParser:
    """Возвращает парсер."""
    parser: ArgumentParser = ArgumentParser(
        prog='docs-validator',
        description='Static analyzer for documentation link integrity',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
    Examples:
      docs-validator scan ./docs --report markdown
      docs-validator scan ./docs --is_validate --fail-on-error
    """,
    )

    subparsers = parser.add_subparsers(
        dest='command',
        description='Available commands',
        required=True,
        help='subcommands',
    )

    scan_parser = subparsers.add_parser(
        name='scan',
        help='Scan documentation for broken links',
        description='Scans documentation directory for broken links, orphan files, and missing anchors.',
        epilog="""
    Examples:
      %(prog)s scan ./docs
      %(prog)s scan ./docs --report json --output report.json
      %(prog)s scan ./docs --validate --fail-on-error
      %(prog)s scan ./docs --exclude .git --exclude_patterns node_modules
      """,
    )
    scan_parser.add_argument(
        # 'path',
        type=Path,
        dest='path_to_explore',
        help='Path to documentation directory',
    )
    scan_parser.add_argument(
        '--report',
        choices=['markdown', 'json'],
        default='markdown',
        dest='report_format',
        help='Report format: markdown, json (default: markdown)',
    )
    scan_parser.add_argument(
        '--output',
        type=Path,
        dest='output_file',
        help='Output file path (default: stdout)',
    )
    scan_parser.add_argument(
        '--exclude',
        action='append',
        default=[],
        dest='exclude_patterns',
        help='pattern to exlude (can be specified multiple times)',
    )
    scan_parser.add_argument(
        '--log-level',
        choices=['debug', 'info', 'warning', 'error'],
        default='warning',
        help='Logging level: debug, info, warning, error (default: warning)',
    )
    scan_parser.add_argument(
        '--validate',
        action='store_true',
        dest='is_validate',
        help='Run validators after scanning',
    )
    scan_parser.add_argument(
        '--fail-on-error',
        action='store_true',
        dest='is_fail_on_error',
        help='Exit with code 1 if any ERROR issues found',
    )
    scan_parser.add_argument(
        '--config',
        type=Path,
        help='Путь к файлу конфигурации (по умолчанию: ./.docs-validator.toml)',
    )

    return parser


def cmd_scan(args: argparse.Namespace) -> int:
    """Выполняет сканирование."""
    config_file = None

    if hasattr(args, 'config') and args.config:
        config_file = Path(args.config)
        if not config_file.exists():
            log.error('Файл конфигурации не найден: %s', config_file)
            return 1
        log.debug('Используется явный файл конфигурации: %s', config_file)

    else:
        config_file = Path.cwd() / '.docs-validator.toml'
        if config_file.exists():
            log.debug('Найден файл конфигурации по умолчанию: %s', config_file)
        else:
            log.debug('Файл конфигурации не найден, используются значения по умолчанию')

    config_effective = ValidatorConfig()
    if config_file:
        try:
            config_effective = load_config_from_toml(config_file)
        except IOError as err:
            log.error('Ошибка при чтении конфигурации %s: %s', config_file, err)
            return 1

    path_to_explore = args.path_to_explore or config_effective.path_to_explore or Path.cwd()
    output_file = args.output_file or config_effective.output_file
    exclude_patterns = args.exclude_patterns or config_effective.exclude_patterns
    log_level = args.log_level or config_effective.log_level
    report_format = args.report_format or config_effective.report_format
    is_validate = args.is_validate or config_effective.is_validate
    is_fail_on_error = args.is_fail_on_error or config_effective.is_fail_on_error

    setup_logging(log_level.upper())

    if not path_to_explore.exists():
        log.error('Не удалось найти запрошенный путь: %s', args.path)
        return 1

    if not path_to_explore.is_dir():
        log.error('Запрошенный путь не является каталогом: %s', args.path)
        return 1

    log.info('Выполняется обход каталога %s', path_to_explore)

    explorer = FilesExplorer(
        root_path=path_to_explore,
        patterns_exclude=set(exclude_patterns)
    )
    files_explored: list[DocumentationFile] = list(explorer.explore())

    if not files_explored:
        log.warning('Файлы документации не найдены')
        return 0

    for file in files_explored:
        file_path = path_to_explore / file.path
        try:
            content = file_path.read_text(encoding='utf-8')
            extractor = LinkExtractor(file_path)
            file.links_out = set(extractor.get_links_from_file(content))
        except IOError as err:
            log.error('При чтении файла %s произошла ошибка %s', file.path, err)

    issues_explored: list[ValidationIssue] = []
    if is_validate:
        log.info('Выполнение валидации')

        files_to_validate: dict[Path, DocumentationFile] = {file.path: file for file in files_explored}

        validators = [
            BrokenLinkValidator(),
            OrphanFileValidator(),
            AnchorLinkValidator(),
            CircularDependencyValidator(),
        ]

        for validator in validators:
            issues = validator.is_validate(files_to_validate, path_to_explore)
            issues_explored.extend(issues)
            log.info('Валидатор %s обнаружил проблемы в количестве %d',
                     validator.__class__.__name__, len(issues))

        # проблемы
        if issues_explored:
            log.warning('Всего обнаружено проблем: %d', len(issues_explored))
            for issue in issues_explored:
                log.warning(
                    '[%s] %s: %s (строка %d)',
                    issue.severity_level.value,
                    issue.issue_type.value,
                    issue.message,
                    issue.link.line_number if issue.link else 0,
                )
        # exit codes ошибок
        if is_fail_on_error:
            has_errors = any(issue.severity_level == SeverityLevel.ERROR for issue in issues_explored)
            if has_errors:
                log.error('Проверка не пройдена - обнаружены проблемы уровня ERROR')
                return 1

    # генерация отчета
    if report_format == 'json':
        report = files_to_json(files_explored, include_content=False)
    elif report_format == 'markdown':
        report = _generate_markdown_report(files_explored, issues_explored)

    # генерация отчета
    report_file: Path = output_file
    if report_file:
        report_file.write_text(report, encoding='utf-8')
        log.info('Отчет записан в файл: %s', report_file)
    else:
        log.debug('Генерация отчета не была запрошена')

    # собрать статистику
    files_total: int = len(files_explored)
    links_total: int = sum(len(file.links_out) for file in files_explored)
    log.info('Обработано файлов: %d\nОбнаружено ссылок: %d\n', files_total, links_total)

    return 0


def _generate_markdown_report(
        files_explored: list[DocumentationFile],
        issues_found: list[ValidationIssue],
) -> str:
    """Генерирует отчет в markdown."""
    report_lines: list[str] = [
        '# Documentation Validator Report',
        '',
        f'**Total files:** {len(files_explored)}',
        f'**Total links:** {sum(len(f.links_out) for f in files_explored)}',
    ]

    # issues
    if issues_found:
        report_lines.extend([
            f'**Issues found:** {len(issues_found)}',
            '',
            '## Issues',
            '',
        ])

        for issue in issues_found:
            report_lines.append(
                f'- **[{issue.severity_level.value.upper()}]** '
                f'{issue.issue_type.value}: {issue.message}'
            )
            if issue.link:
                report_lines.append(f'  - File: {issue.src_file.path}:{issue.link.line_number}')
        report_lines.append('')

        report_lines.append('## Files')
        report_lines.append('')

    # files
    for file in files_explored:
        report_lines.extend([
            f'### {file.path}',
            f'- Title: {file.title}',
            f'- Links found: {len(file.links_out)}',
        ])

        for link in sorted(file.links_out, key=lambda x: x.line_number):
            report_lines.append(
                f'| {link.link_type.name} | {link.uri} | '
                f'{link.anchor or "-"} | {link.line_number} |'
            )

    report_lines.append('')
    return '\n'.join(report_lines)


def main() -> int:
    """Точка входа cli."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command == 'scan':
        return cmd_scan(args)

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())