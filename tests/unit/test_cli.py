"""Тесты отображения аргументов CLI в конфигурацию парсера."""
from argparse import Namespace
from pathlib import Path
from unittest.mock import MagicMock, patch

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
