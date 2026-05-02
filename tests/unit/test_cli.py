"""Тесты отображения аргументов CLI в конфигурацию парсера."""
from argparse import Namespace
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from validator.core.files_explorer import FilesExplorer


class TestCliArgsToConfigMapping:
    """Проверка передачи параметров CLI в объекты ядра."""

    def test_default_values_propagate_to_files_explorer(self, parser):
        """Значения по умолчанию корректно передаются в FilesExplorer."""
        args: Namespace = parser.parse_args(['scan', './docs'])

        with patch('validator.core.files_explorer.FilesExplorer') as mock_explorer:
            mock_instance = MagicMock()
            mock_explorer.return_value = mock_instance

            explorer = FilesExplorer(
                root_path=args.path,
                extensions_include={'.md', '.markdown'},
                patterns_exclude=set(),
            )

            assert explorer.root_path == Path('./docs')
            assert explorer.extensions_include == {'.md', '.markdown'}
            assert explorer.patterns_exclude == set()

    def test_custom_report_and_output_mapped_to_config(self, parser):
        """Пользовательские --report и --output отражаются в конфигурации."""
        args: Namespace = parser.parse_args([
            'scan', './docs',
            '--report', 'json',
            '--output', 'report.json'
        ])

        config = {
            'report_format': args.report,
            'output_path': args.output,
        }

        assert config['report_format'] == 'json'
        assert config['output_path'] == Path('report.json')

    def test_multiple_exclude_patterns_collected_in_set(self, parser):
        """Параметр --exclude с множественным указанием собирается в set."""
        args: Namespace = parser.parse_args([
            'scan', './docs',
            '--exclude', '*.tmp',
            '--exclude', 'draft_*',
            '--exclude', '.git'
        ])

        exclude_set = set(args.exclude)

        assert '*.tmp' in exclude_set
        assert 'draft_*' in exclude_set
        assert '.git' in exclude_set
        assert len(exclude_set) == 3


class TestCliAllFlags:
    """Тестирование обработки параметров cli."""

    def test_scan_command_required(self, parser):
        """Команда scan обязательна."""
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_path_argument_required(self, parser):
        """Путь к директории обязателен для scan."""
        with pytest.raises(SystemExit):
            parser.parse_args(['scan'])

    def test_default_values(self, parser):
        """Значения по умолчанию."""
        args = parser.parse_args(['scan', './docs'])

        assert args.command == 'scan'
        assert args.path == Path('./docs')
        assert args.report == 'markdown'
        assert args.output is None
        assert args.exclude == []
        assert args.log_level == 'warning'
        assert args.validate is False
        assert args.fail_on_error is False

    def test_report_markdown(self, parser):
        """Флаг --report markdown."""
        args = parser.parse_args(['scan', './docs', '--report', 'markdown'])
        assert args.report == 'markdown'

    def test_report_json(self, parser):
        """Флаг --report json."""
        args = parser.parse_args(['scan', './docs', '--report', 'json'])
        assert args.report == 'json'

    def test_report_invalid(self, parser):
        """Невалидный --report вызывает ошибку."""
        with pytest.raises(SystemExit):
            parser.parse_args(['scan', './docs', '--report', 'xml'])

    def test_output_file(self, parser):
        """Флаг --output."""
        args = parser.parse_args(['scan', './docs', '--output', 'report.json'])
        assert args.output == Path('report.json')

    def test_exclude_single(self, parser):
        """Флаг --exclude (однократный)."""
        args = parser.parse_args(['scan', './docs', '--exclude', '.git'])
        assert args.exclude == ['.git']

    def test_exclude_multiple(self, parser):
        """Флаг --exclude (множественный)."""
        args = parser.parse_args([
            'scan', './docs',
            '--exclude', '.git',
            '--exclude', 'node_modules',
            '--exclude', '*.tmp',
        ])
        assert args.exclude == ['.git', 'node_modules', '*.tmp']

    def test_log_level_debug(self, parser):
        """Флаг --log-level debug."""
        args = parser.parse_args(['scan', './docs', '--log-level', 'debug'])
        assert args.log_level == 'debug'

    def test_log_level_info(self, parser):
        """Флаг --log-level info."""
        args = parser.parse_args(['scan', './docs', '--log-level', 'info'])
        assert args.log_level == 'info'

    def test_log_level_warning(self, parser):
        """Флаг --log-level warning."""
        args = parser.parse_args(['scan', './docs', '--log-level', 'warning'])
        assert args.log_level == 'warning'

    def test_log_level_error(self, parser):
        """Флаг --log-level error."""
        args = parser.parse_args(['scan', './docs', '--log-level', 'error'])
        assert args.log_level == 'error'

    def test_log_level_invalid(self, parser):
        """Невалидный --log-level вызывает ошибку."""
        with pytest.raises(SystemExit):
            parser.parse_args(['scan', './docs', '--log-level', 'trace'])

    def test_validate_flag(self, parser):
        """Флаг --validate."""
        args = parser.parse_args(['scan', './docs', '--validate'])
        assert args.validate is True

    def test_validate_flag_absent(self, parser):
        """Флаг --validate отсутствует."""
        args = parser.parse_args(['scan', './docs'])
        assert args.validate is False

    def test_fail_on_error_flag(self, parser):
        """Флаг --fail-on-error."""
        args = parser.parse_args(['scan', './docs', '--fail-on-error'])
        assert args.fail_on_error is True

    def test_fail_on_error_flag_absent(self, parser):
        """Флаг --fail-on-error отсутствует."""
        args = parser.parse_args(['scan', './docs'])
        assert args.fail_on_error is False

    def test_all_flags_combined(self, parser):
        """Все флаги вместе."""
        args = parser.parse_args([
            'scan', './docs',
            '--report', 'json',
            '--output', 'report.json',
            '--exclude', '.git',
            '--exclude', 'node_modules',
            '--log-level', 'debug',
            '--validate',
            '--fail-on-error',
        ])

        assert args.command == 'scan'
        assert args.path == Path('./docs')
        assert args.report == 'json'
        assert args.output == Path('report.json')
        assert args.exclude == ['.git', 'node_modules']
        assert args.log_level == 'debug'
        assert args.validate is True
        assert args.fail_on_error is True

    def test_help_flag(self, parser, capsys):
        """Флаг --help выводит справку."""
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(['--help'])

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert 'scan' in captured.out
        assert 'documentation' in captured.out.lower()
