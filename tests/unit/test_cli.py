"""Тесты отображения аргументов CLI в конфигурацию парсера."""
from pathlib import Path
from unittest.mock import MagicMock, patch

from validator.cli import create_parser, execute_scan


class TestCreateParser:
    def test_returns_parser_with_scan_command(self):
        parser = create_parser()
        assert parser.parse_known_args(['scan', './docs'])[0].command == 'scan'

    def test_maps_report_flag_to_json(self):
        parser = create_parser()
        args = parser.parse_args(['scan', './docs', '--report', 'json'])
        assert args.report_format == 'json'


class TestExecuteScan:
    @patch('validator.cli.load_configuration')
    @patch('validator.cli.setup_logging')
    @patch('validator.cli.explore_files', return_value=[])
    def test_returns_zero_on_empty_dir(self, mock_explore, mock_log, mock_config, parser, tmp_path):
        mock_config.return_value = MagicMock(log_level='warning', is_validate=False, output_file=None)
        args = parser.parse_args(['scan', str(tmp_path)])
        assert execute_scan(args) == 0
        mock_explore.assert_called_once()

    @patch('validator.cli.get_exit_code', return_value=0)
    @patch('validator.cli.write_report')
    @patch('validator.cli.generate_report', return_value='report text')
    @patch('validator.cli.aggregate_issue_statistics', return_value=MagicMock())
    @patch('validator.cli.collect_issues', return_value=[])
    @patch('validator.cli.collect_links')
    @patch('validator.cli.explore_files', return_value=[MagicMock(path=Path('a.md'))])
    @patch('validator.cli.load_configuration')
    @patch('validator.cli.setup_logging')
    def test_executes_full_pipeline_without_output_file(self, mock_log, mock_cfg, mock_exp,
                                                        mock_coll, mock_iss, mock_agg, mock_gen, mock_wr, mock_exit, parser, tmp_path):
        mock_cfg.return_value = MagicMock(log_level='warning', is_validate=False, output_file=None)
        args = parser.parse_args(['scan', str(tmp_path)])
        assert execute_scan(args) == 0
        # Код всегда вызывает write_report: в файл или в stdout (None)
        mock_wr.assert_called_once_with('report text', None)