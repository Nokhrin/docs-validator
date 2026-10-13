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

from docs_validator.pipeline import execute_scan
from docs_validator.utils.scaffold import execute_setup, SetupOptions

log = logging.getLogger(__name__)


def create_parser() -> ArgumentParser:
    """Returns the argument parser."""
    parser: ArgumentParser = ArgumentParser(
        prog="docs_validator",
        description="Static analyzer for documentation link integrity",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        description="Available commands",
        required=True,
        help="subcommands",
    )

    scan_parser = subparsers.add_parser(
        name="scan",
        help="Scan documentation for broken links",
        description="Scans documentation directory for broken links, orphan files, and missing anchors.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s scan <docs_dir>
  %(prog)s scan <docs_dir> --validate --report html --output report.html
  %(prog)s scan <docs_dir> --validate --fail-on-error --log-level debug
  %(prog)s scan <docs_dir> --skip-external --exclude node_modules --exclude .git
  %(prog)s scan <docs_dir> --config ./.my-config.toml
""",
    )

    scan_parser.add_argument(
        "path_to_explore",
        type=Path,
        nargs="?",
        default=None,
        help='Path to documentation directory (default: current dir "." or value from config)',
    )

    scan_parser.add_argument(
        "--report",
        choices=["markdown", "json", "html"],
        default="markdown",
        dest="report_format",
        help="Report format: markdown, json, html (default: markdown)",
    )

    scan_parser.add_argument(
        "--output",
        type=Path,
        dest="output_file",
        help="Output file path (default: stdout)",
    )

    scan_parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        dest="exclude_patterns",
        help="Pattern to exclude (can be specified multiple times)",
    )

    scan_parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="warning",
        help="Logging level: debug, info, warning, error (default: warning)",
    )

    scan_parser.add_argument(
        "--validate",
        action="store_true",
        dest="is_validate",
        help="Run rules after scanning",
    )

    scan_parser.add_argument(
        "--fail-on-error",
        action="store_true",
        dest="is_fail_on_error",
        help="Exit with code 1 if any ERROR issues found",
    )

    scan_parser.add_argument(
        "--config",
        type=Path,
        help="Configuration file path (default: ./.docs_validator.toml)",
    )

    scan_parser.add_argument(
        "--skip-external",
        action="store_true",
        dest="is_skip_external",
        help="Skip external links verification",
    )

    setup_parser = subparsers.add_parser(
        name="setup",
        help="Generate CI configuration, pre-commit hook, docs-validator config for the current repository.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s setup --github
  %(prog)s setup --gitlab --force
  %(prog)s setup --config --pre-commit
""",
    )

    setup_parser.add_argument(
        "--force",
        action="store_true",
        dest="is_force",
        help="Overwrite existing files with generated files",
    )

    setup_parser.add_argument(
        "--config",
        required=False,
        action="store_true",
        dest="is_config",
        help="Generates docs-validator config in repository root",
    )

    setup_parser.add_argument(
        "--pre-commit",
        required=False,
        action="store_true",
        dest="is_pre_commit",
        help="Generate .githooks/pre-commit hook",
    )

    ci_group = setup_parser.add_mutually_exclusive_group()

    ci_group.add_argument(
        "--github",
        required=False,
        action="store_true",
        dest="is_github",
        help="Generates GitHub actions workflow script",
    )

    ci_group.add_argument(
        "--gitlab",
        required=False,
        action="store_true",
        dest="is_gitlab",
        help="Generates GitLab CI workflow script",
    )

    return parser


def _setup_options_from_namespace(args: argparse.Namespace) -> SetupOptions:
    force: bool = getattr(args, "is_force", False)
    config: bool = getattr(args, "is_config", False)
    github: bool = getattr(args, "is_github", False)
    gitlab: bool = getattr(args, "is_gitlab", False)
    precommit: bool = getattr(args, "is_pre_commit", False)
    return SetupOptions(
        force=force,
        config=config,
        github=github,
        gitlab=gitlab,
        precommit=precommit,
    )


def main() -> int:
    parser = create_parser()
    args: argparse.Namespace = parser.parse_args()

    match args.command:
        case "scan":
            return execute_scan(args)
        case "setup":
            try:
                options = _setup_options_from_namespace(args)
                return execute_setup(options, stream=sys.stdout)
            except ValueError as e:
                log.error("Setup: %s", e)
                return 1

        case _:
            log.error("Unknown command: %s", args.command)
            return 2


if __name__ == "__main__":
    sys.exit(main())
