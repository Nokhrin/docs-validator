"""
CLI валидатора документации.
"""
import argparse
import logging
from argparse import ArgumentParser
from pathlib import Path

from validator import setup_logging
from validator.application import load_configuration, explore_files, write_report, get_exit_code, \
    aggregate_issue_statistics, generate_report, collect_issues, collect_links

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
        'path_to_explore',
        type=Path,
        help='Path to documentation directory (positional, required)',
    )

    scan_parser.add_argument(
        '--report',
        choices=['markdown', 'json', 'html'],
        default='markdown',
        dest='report_format',
        help='Report format: markdown, json, html (default: markdown)',
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
        help='pattern to exlcude (can be specified multiple times)',
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
        help='Configuration file path (default: ./.docs-validator.toml)',
    )

    scan_parser.add_argument(
        '--skip-external',
        action='store_true',
        dest='is_skip_external',
        help='Skip external links verification',
    )

    return parser


def execute_scan(args: argparse.Namespace) -> int:
    validation_config = load_configuration(args)
    setup_logging(validation_config.log_level.upper())

    if not Path(args.path_to_explore).exists():
        log.error('Не найдена запрошенная директория: %s', args.path_to_explore)
        return 1

    files_explored = explore_files(args.path_to_explore, validation_config)
    if not files_explored:
        log.debug('Файлы не найдены')
        return 0

    collect_links(files_explored)

    issues = []
    if validation_config.is_validate:
        issues = collect_issues(files_explored, validation_config)

    stats = aggregate_issue_statistics(files_explored, issues)

    report: str = generate_report(
        {f.path: f for f in files_explored},
        issues,
        stats,
        validation_config,
    )

    if validation_config.output_file:
        write_report(report, Path(validation_config.output_file))
    else:
        write_report(report, None)

    return get_exit_code(issues, validation_config)


def main() -> int:
    """Точка входа cli."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command == 'scan':
        return execute_scan(args)

    return 0


if __name__ == '__main__':
    import sys

    sys.exit(main())
