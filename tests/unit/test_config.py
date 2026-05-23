from pathlib import Path

from validator.config import ValidatorConfig, load_config_from_toml


class TestConfig:

    def test_default_values(self):
        """Конфигурация корректна, все параметры по умолчанию."""
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

    def test_load_config_from_toml(self, config_toml, temp_docs_dir):
        """Конфигурация корректна, все параметры указаны в файле."""
        config = load_config_from_toml(config_toml)

        assert config.exclude_patterns == ['.git', 'node_modules']
        assert config.log_level == 'debug'
        assert config.report_format == 'json'
        assert config.output_file == Path('./report.json')
        assert config.is_validate is True
        assert config.is_fail_on_error is True
        assert config.external_timeout_sec == 5
        assert config.max_threads_number == 1
        assert config.hosts_to_ignore == ["localhost", "127.0.0.1"]
        assert config.is_skip_external == False
