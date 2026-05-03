from pathlib import Path

from validator.config import ValidatorConfig, load_config_from_toml


class TestConfig:

    def test_default_values(self):
        """Конфигурация корректна, все параметры по умолчанию."""
        config = ValidatorConfig()
        assert config.path_to_explore is None
        assert config.exclude_patterns == []
        assert config.log_level == 'warning'
        assert config.report_format == 'markdown'
        assert config.output_file is None
        assert config.validate is False
        assert config.fail_on_error is False

    def test_load_full_config(self, config_toml, temp_docs_dir):
        """Конфигурация корректна, все параметры указаны в файле."""
        config = load_config_from_toml(config_toml)

        assert config.path_to_explore == Path('./docs')
        assert config.exclude_patterns == ['.git', 'node_modules']
        assert config.log_level == 'debug'
        assert config.report_format == 'json'
        assert config.output_file == Path('./report.json')
        assert config.validate is True
        assert config.fail_on_error is True