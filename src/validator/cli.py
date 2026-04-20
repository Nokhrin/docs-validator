"""
CLI валидатора документации.

Examples:
    docs-validator scan ./docs --report markdown
    docs-validator scan ./docs --report json --output report.json
    docs-validator --help
"""
import logging
from argparse import ArgumentParser
from pathlib import Path
from validator import setup_logging
def create_parser() -> ArgumentParser:
    """Возвращает парсер."""
    parser: ArgumentParser = ArgumentParser(
        prog='docs-validator',
        description='Static analyzer for documentation link integrity',
        epilog='Example: docs-validator scan ./docs --report markdown',
    )

    subparsers = parser.add_subparsers(
        dest='command',
        description='Available commands',
        required=True,
        help='',
    )

    scan_parser = subparsers.add_parser(
        name='scan',
        help='Scan documentation for links',
    )
    scan_parser.add_argument(
        'path',
        type=Path,
        help='Path to documentation directory',
    )
    scan_parser.add_argument(
        '--report',
        choices=['markdown', 'json'],
        default='markdown',
        help='Report format (default: markdown)',
    )
    scan_parser.add_argument(
        '--output',
        type=Path,
        help='Output file path (default: stdout)',
    )
    scan_parser.add_argument(
        '--exclude',
        action='append',
        default=[],
        help='Exclude pattern (can be specified multiple times)',
    )
    scan_parser.add_argument(
        '--log-level',
        choices=['debug', 'info', 'warning', 'error'],
        default='warning',
        help='Logging level (default: warning)',
    )
    scan_parser.add_argument(
        '--validate',
        action='store_true',
        help='Run validators after scanning',
    )
    scan_parser.add_argument(
        '--fail-on-error',
        action='store_true',
        help='Exit with code 1 if any ERROR issues found',
    )

    return parser
