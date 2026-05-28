from argparse import Namespace
from pathlib import Path
from unittest.mock import MagicMock

from validator.cli import create_parser, execute_scan, main


class TestCli:
    def test_execute_scan_delegates_and_handles_output(self, mocker):
        mock_load = mocker.patch('validator.cli.load_configuration')
        mock_setup = mocker.patch('validator.cli.setup_logging')
        mock_run = mocker.patch('validator.cli.run_validation')
        mock_write = mocker.patch('validator.cli.Path.write_text')

        mock_config = MagicMock(output_file=MagicMock(), log_level='WARNING')
        mock_load.return_value = mock_config
        mock_run.return_value = (0, 'mock_report')

        ret = execute_scan(Namespace(path_to_explore='/tmp/docs'))

        mock_load.assert_called_once()
        mock_setup.assert_called_once_with('WARNING')
        mock_run.assert_called_once_with(mock_config)
        mock_write.assert_called_once_with('mock_report', encoding='utf-8')
        assert ret == 0

    def test_parser_maps_flags_to_namespace(self):
        parser = create_parser()
        args = parser.parse_args([
            'scan', './docs',
            '--report', 'json',
            '--validate',
            '--config', './custom.toml'
        ])
        assert args.report_format == 'json'
        assert args.is_validate is True
        assert args.config == Path('custom.toml')  # Path нормализует ./custom.toml
        assert args.command == 'scan'

    def test_main_dispatches_scan(self, mocker):
        mock_parser = mocker.patch('validator.cli.create_parser')
        mock_scan = mocker.patch('validator.cli.execute_scan', return_value=1)

        mock_parser.return_value.parse_args.return_value = Namespace(command='scan')
        assert main() == 1
        mock_scan.assert_called_once()