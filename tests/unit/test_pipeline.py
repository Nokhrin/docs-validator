from argparse import Namespace
from pathlib import Path

from validator.config import ValidatorConfig
from validator.core.models import (
    ValidationIssue, SeverityLevel, IssueType, DocumentationFile, Link, LinkType
)
from validator.pipeline import (
    load_configuration, run_validation, collect_issues,
    aggregate_issue_statistics
)


class TestPipeline:
    def test_load_configuration_priority(self, mocker):
        mocker.patch('validator.pipeline.Path.exists', return_value=True)
        mocker.patch(
            'validator.pipeline.load_config_from_toml',
            return_value=ValidatorConfig(report_format='json', is_validate=True)
        )

        args = Namespace(
            path_to_explore=Path('./docs'),
            config=Path('./custom.toml'),
            report_format='html',
            is_validate=False
        )
        cfg = load_configuration(args)

        assert cfg.report_format == 'html'
        assert cfg.is_validate is False
        assert cfg.path_to_explore == Path('./docs')

    def test_run_validation_orchestration(self, mocker, tmp_path):
        cfg = ValidatorConfig(path_to_explore=tmp_path, is_validate=True, is_skip_external=True)
        mock_files = {Path('a.md'): mocker.MagicMock()}

        mock_explore = mocker.patch('validator.pipeline.explore_files', return_value=mock_files)
        mock_links = mocker.patch('validator.pipeline.collect_links')

        mock_issues_result = [mocker.MagicMock()]
        mock_issues = mocker.patch('validator.pipeline.collect_issues', return_value=mock_issues_result)

        mock_stats = mocker.MagicMock()
        mock_agg = mocker.patch('validator.pipeline.aggregate_issue_statistics', return_value=mock_stats)
        mocker.patch('validator.pipeline.get_exit_code', return_value=1)

        files, issues, stats, exit_code = run_validation(cfg)

        mock_explore.assert_called_once_with(tmp_path, cfg)
        mock_links.assert_called_once_with(mock_files, tmp_path)
        mock_issues.assert_called_once_with(mock_files, cfg)
        mock_agg.assert_called_once_with(mock_files, mock_issues_result)

        assert files == mock_files
        assert issues == mock_issues_result
        assert stats == mock_stats
        assert exit_code == 1

    def test_collect_issues_respects_skip_external(self, mocker, tmp_path):
        mock_external_cls = mocker.patch('validator.pipeline.ExternalLinkValidator')
        mock_external_instance = mocker.MagicMock()
        mock_external_cls.return_value = mock_external_instance

        mocker.patch('validator.pipeline.CircularDependencyValidator')
        mocker.patch('validator.pipeline.AnchorLinkValidator')
        mocker.patch('validator.pipeline.OrphanFileValidator')
        mocker.patch('validator.pipeline.BrokenLinkValidator')

        files = {Path('a.md'): mocker.MagicMock()}
        cfg_with_skip = ValidatorConfig(is_validate=True, is_skip_external=True, path_to_explore=tmp_path)
        cfg_without_skip = ValidatorConfig(is_validate=True, is_skip_external=False, path_to_explore=tmp_path)

        collect_issues(files, cfg_with_skip)
        collect_issues(files, cfg_without_skip)

        mock_external_instance.validate.assert_called_once_with(files, cfg_without_skip.path_to_explore)

    def test_aggregate_issue_statistics_pure(self):
        broken_link = Link('./missing.md', LinkType.INTERNAL, Path('a.md'), 1)
        valid_link = Link('./other.md', LinkType.INTERNAL, Path('a.md'), 2)
        file_obj = DocumentationFile(path=Path('a.md'), title='A', links_out={broken_link, valid_link})
        issue = ValidationIssue(IssueType.BROKEN_LINK, SeverityLevel.ERROR, file_obj, broken_link)

        stats = aggregate_issue_statistics({Path('a.md'): file_obj}, [issue])

        assert stats.internal_total == 2
        assert stats.internal_broken == 1
        assert stats.external_total == 0
