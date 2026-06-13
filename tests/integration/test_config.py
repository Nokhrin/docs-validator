from pathlib import Path

import pytest

from validator.config import ValidatorConfig, load_config_from_toml


class TestConfig:

    def test_default_valid_arguments(self):
        config = ValidatorConfig()
        assert config.exclude_patterns == []
        assert config.log_level == 'warning'
        assert config.report_format == 'markdown'
        assert config.output_file is None
        assert config.is_validate is False
        assert config.is_fail_on_error is False
        assert config.external_timeout_sec == 10
        assert config.max_threads_number == 5
        assert config.hosts_to_ignore == []
        assert config.is_skip_external == False

    def test_load_config_from_toml_arguments_valid(self, tmp_path: Path):
        config_file = tmp_path / '.docs-validator.toml'
        config_file.write_text(f"""
        [validator]
        path_to_explore = "{tmp_path.resolve()}/docs"
        exclude_patterns = [".git", "node_modules"]
        log_level = "debug"
        report_format = "json"
        output_file = "./report.json"
        is_validate = true
        is_fail_on_error = true
        external_timeout_sec = 5
        max_threads_number = 1
        hosts_to_ignore = ["localhost", "127.0.0.1"]
        """)
        config = load_config_from_toml(config_file)

        assert config.exclude_patterns == ['.git', 'node_modules']
        assert config.log_level == 'debug'
        assert config.report_format == 'json'
        assert config.output_file == Path('./report.json')
        assert config.is_validate is True
        assert config.is_fail_on_error is True
        assert config.external_timeout_sec == 5
        assert config.max_threads_number == 1
        assert config.hosts_to_ignore == ['localhost', '127.0.0.1']
        assert config.is_skip_external == False

    def test_load_config_from_toml_with_unknown_fields_raises_error(self, tmp_path):
        config_file = tmp_path / '.docs-validator.toml'
        config_file.write_text("""
[validator]
log_level = "debug"
external_parsing_timeout_sec = 10
""")
        with pytest.raises(ValueError, match='Unknown configuration fields'):
            load_config_from_toml(config_file)

    def test_load_config_from_toml_with_typo_in_field_name_raises_error(self, tmp_path):
        config_file = tmp_path / '.docs-validator.toml'
        config_file.write_text("""
[validator]
validate_external_anchors = true
external_anchor_parsing_timeout_sec = 10
""")
        with pytest.raises(ValueError, match='Unknown configuration fields'):
            load_config_from_toml(config_file)

    def test_load_config_from_toml_valid_fields_no_error(self, tmp_path):
        config_file = tmp_path / '.docs-validator.toml'
        config_file.write_text("""
[validator]
validate_external_anchors = true
external_anchor_timeout_sec = 10
""")
        config = load_config_from_toml(config_file)
        assert config.validate_external_anchors is True
        assert config.external_anchor_timeout_sec == 10