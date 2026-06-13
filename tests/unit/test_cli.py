from argparse import Namespace
from pathlib import Path

from validator.cli import create_parser, execute_scan, main


class TestCli:
    def test_execute_scan_delegates_and_handles_output(self, mocker):
        mock_load = mocker.patch('validator.cli.load_configuration')
        mock_run = mocker.patch('validator.cli.run_validation')
        mock_cli_reporter = mocker.patch('validator.cli.CLIReporter')
        mock_md_reporter = mocker.patch('validator.cli.MarkdownReporter')
        mock_write = mocker.patch('validator.cli.Path.write_text')

        mock_config = mocker.MagicMock(
            output_file=mocker.MagicMock(),
            log_level='WARNING',
            report_format='markdown',
            report_include_files=False
        )
        mock_load.return_value = mock_config

        mock_files = {}
        mock_issues = []
        mock_stats = mocker.MagicMock()
        mock_run.return_value = (mock_files, mock_issues, mock_stats, 0)

        mock_cli_instance = mocker.MagicMock()
        mock_cli_reporter.return_value = mock_cli_instance

        mock_md_instance = mocker.MagicMock()
        mock_md_reporter.return_value = mock_md_instance
        mock_md_instance.report.return_value = 'mock_file_report'

        ret = execute_scan(Namespace(path_to_explore='/tmp/docs'))

        mock_load.assert_called_once()
        mock_run.assert_called_once_with(mock_config)

        mock_cli_reporter.assert_called_once()
        mock_cli_instance.report.assert_called_once_with(mock_files, mock_issues, mock_stats)

        mock_md_reporter.assert_called_once_with(include_files=False)
        mock_md_instance.report.assert_called_once_with(mock_files, mock_issues, mock_stats)
        mock_write.assert_called_once_with('mock_file_report', encoding='utf-8')

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