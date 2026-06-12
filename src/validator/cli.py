"""
Documentation validator CLI.
Responsibilities:
- Parsing sys.argv and type casting
- Basic validation of required parameters
- Invoking the single application entry point
- Converting the result to an exit code (sys.exit())
"""
import argparse
import logging
import sys
from argparse import ArgumentParser
from pathlib import Path

from validator.pipeline import load_configuration, run_validation
from validator.reporters import CLIReporter, JSONReporter, MarkdownReporter, HTMLReporter

log = logging.getLogger(__name__)


def create_parser() -> ArgumentParser:
    """Returns the argument parser."""
    parser: ArgumentParser = ArgumentParser(
        prog='docs-validator',
        description='Static analyzer for documentation link integrity',
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
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s scan ./docs
  %(prog)s scan ./docs --validate --report html --output report.html
  %(prog)s scan ./docs --validate --fail-on-error --log-level debug
  %(prog)s scan ./docs --skip-external --exclude node_modules --exclude .git
  %(prog)s scan ./docs --config ./.my-config.toml
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
        help='Pattern to exclude (can be specified multiple times)',
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
        help='Run rules after scanning',
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

    log_level = getattr(logging, validation_config.log_level.upper(), logging.WARNING)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S',
        stream=sys.stdout,
        force=True
    )

    files, issues, stats, exit_code = run_validation(validation_config)

    # Console output
    CLIReporter(stream=sys.stdout).report(files, issues, stats)

    # File output
    if validation_config.output_file:
        reporters = {
            'json': JSONReporter(),
            'markdown': MarkdownReporter(include_files=validation_config.report_include_files),
            'html': HTMLReporter(include_files=validation_config.report_include_files),
        }
        reporter = reporters.get(validation_config.report_format, reporters['markdown'])
        content = reporter.report(files, issues, stats)
        Path(validation_config.output_file).write_text(content, encoding='utf-8')

    return exit_code


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()

    match args.command:
        case 'scan':
            return execute_scan(args)
        case _:
            log.error('Unknown command: %s', args.command)
            return 2


if __name__ == '__main__':
    sys.exit(main())
