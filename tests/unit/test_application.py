from unittest.mock import patch, MagicMock
from pathlib import Path
from argparse import Namespace
from validator.application import (
    load_configuration, explore_files, collect_links, collect_issues,
    aggregate_issue_statistics, generate_report, write_report, get_exit_code
)
from validator.config import ValidatorConfig
from validator.core.models import LinkStatistics, ValidationIssue, IssueType, SeverityLevel, DocumentationFile, Link, \
    LinkType


class TestLoadConfiguration:
    def test_returns_defaults_when_no_file(self):
        args = Namespace(config=None, exclude_patterns=[], log_level='info',
                         report_format='html', output_file=None, is_validate=False,
                         is_fail_on_error=False, external_timeout_sec=5, max_threads_number=2,
                         hosts_to_ignore=[], is_skip_external=True)
        with patch('validator.application.load_config_from_toml', side_effect=FileNotFoundError):
            cfg = load_configuration(args)
        assert cfg.log_level == 'info'
        assert cfg.report_format == 'html'

    def test_loads_from_toml_when_exists(self, tmp_path):
        config_file = tmp_path / "cfg.toml"
        config_file.write_text("[validator]\nlog_level = 'debug'")

        args = Namespace(
            config=config_file,
            exclude_patterns=[], log_level='info', report_format='html',
            output_file=None, is_validate=False, is_fail_on_error=False,
            external_timeout_sec=5, max_threads_number=2,
            hosts_to_ignore=[], is_skip_external=True
        )

        with patch('validator.application.load_config_from_toml', return_value=MagicMock()) as mock_load:
            result = load_configuration(args)
            mock_load.assert_called_once_with(config_file)
            assert result == mock_load.return_value

class TestExploreFiles:
    @patch('validator.application.FilesExplorer')
    def test_explores_valid_directory(self, mock_explorer):
        mock_explorer.return_value.explore.return_value = [MagicMock()]
        cfg = MagicMock(exclude_patterns=[])
        res = explore_files(Path('.'), cfg)
        assert len(res) == 1
        mock_explorer.assert_called_once()

    @patch('validator.application.FilesExplorer')
    def test_respects_custom_excludes(self, mock_explorer):
        cfg = MagicMock(exclude_patterns=['.git', 'build'])
        explore_files(Path('src'), cfg)
        mock_explorer.assert_called_once_with(root_path=Path('src'), patterns_exclude={'.git', 'build'})


class TestCollectLinks:
    def test_adds_links_to_files(self, tmp_path):
        f1 = tmp_path / 'a.md'
        f1.write_text('[link](b.md)')
        docs = [MagicMock(path=f1, links_out=set())]
        res = collect_links(docs)
        assert len(res[0].links_out) > 0

    def test_handles_io_error_gracefully(self, tmp_path):
        f1 = tmp_path / 'a.md'
        f1.write_text('')
        docs = [MagicMock(path=f1, links_out=set())]
        with patch.object(Path, 'read_text', side_effect=IOError):
            res = collect_links(docs)
        assert res[0].links_out == set()


class TestCollectIssues:
    @patch('validator.application.CircularDependencyValidator')
    @patch('validator.application.AnchorLinkValidator')
    @patch('validator.application.OrphanFileValidator')
    @patch('validator.application.BrokenLinkValidator')
    def test_runs_validators_and_aggregates(self, mock_broken, mock_orphan, mock_anchor, mock_circular):
        mock_broken.return_value.validate.return_value = [MagicMock()]
        mock_orphan.return_value.validate.return_value = []
        mock_anchor.return_value.validate.return_value = []
        mock_circular.return_value.validate.return_value = []

        cfg = MagicMock(is_validate=True, is_skip_external=True, path_to_explore=Path('.'))
        issues = collect_issues([MagicMock()], cfg)

        assert len(issues) == 1
        mock_broken.return_value.validate.assert_called_once()

    def test_skips_external_when_flagged(self):
        cfg = MagicMock(is_validate=True, is_skip_external=True, path_to_explore=Path('.'))
        with patch('validator.application.BrokenLinkValidator') as m1, \
                patch('validator.application.ExternalLinkValidator') as m2:
            m1.return_value.validate.return_value = []
            collect_issues([], cfg)
            m2.assert_not_called()


class TestAggregateIssueStatistics:
    def test_counts_internal_links_correctly(self):
        link = Link(uri="./test.md", link_type=LinkType.INTERNAL, parent_file=Path("a.md"), line_number=1)
        file = DocumentationFile(path=Path("a.md"), title="A", links_out={link})
        stats = aggregate_issue_statistics([file], [])
        assert stats.internal_total == 1

    def test_counts_broken_links_correctly(self):
        link = Link(uri="./missing.md", link_type=LinkType.INTERNAL, parent_file=Path("a.md"), line_number=5)
        file = DocumentationFile(path=Path("a.md"), title="A", links_out={link})
        issue = ValidationIssue(
            issue_type=IssueType.BROKEN_LINK,
            severity_level=SeverityLevel.ERROR,
            src_file=file,
            link=link
        )
        stats = aggregate_issue_statistics([file], [issue])
        assert stats.internal_broken == 1

from pathlib import Path
from validator.application import generate_report
from validator.config import ValidatorConfig
from validator.core.models import LinkStatistics

class TestGenerateReport:
    def test_returns_markdown_string(self):
        cfg = ValidatorConfig(report_format='markdown', output_file=None)
        stats = LinkStatistics(internal_total=5, internal_broken=1, external_total=2, external_broken=0)
        res = generate_report({}, [], stats, cfg)
        assert '# Отчет валидатора документации' in res
        assert 'СТАТИСТИКА ВЫПОЛНЕНИЯ' in res
        assert 'Внутренних ссылок: 5' in res

    def test_returns_html_string(self):
        cfg = ValidatorConfig(report_format='html', output_file=None)
        stats = LinkStatistics(internal_total=0, internal_broken=0, external_total=3, external_broken=1)
        res = generate_report({}, [], stats, cfg)
        assert '<!DOCTYPE html>' in res
        assert 'Внешних ссылок: 3 (недоступно: 1)' in res

class TestWriteReport:
    def test_writes_to_file(self, tmp_path):
        target = tmp_path / 'out.md'
        write_report('content', target)
        assert target.read_text() == 'content'

    def test_writes_to_stdout(self, capsys):
        write_report('console output', None)
        captured = capsys.readouterr()
        assert 'console output' in captured.out


class TestGetExitCode:
    def test_returns_zero_when_no_errors(self):
        cfg = MagicMock(is_fail_on_error=True)
        assert get_exit_code([], cfg) == 0

    def test_returns_one_when_errors_and_flag_enabled(self):
        issue = MagicMock(severity_level=MagicMock(value='error'))
        cfg = MagicMock(is_fail_on_error=True)
        assert get_exit_code([issue], cfg) == 1