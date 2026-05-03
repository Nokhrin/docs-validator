"""Управление конфигурацией валидатора."""
import logging
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

DEFAULT_CONFIG_FILENAME = '.docs-validator.toml'


@dataclass
class ValidatorConfig:
    path_to_explore: Optional[Path] = None
    exclude_patterns: list[str] = field(default_factory=list)
    log_level: str = 'warning'
    report_format: str = 'markdown'
    output_file: Optional[Path] = None
    validate: bool = False
    fail_on_error: bool = False

def load_config_from_toml(config_file: Path) -> ValidatorConfig:
    if not config_file.exists():
        log.warning('Указанный файл конфигурации не найден: %s\n'
                    'Создана конфигурация по умолчанию', config_file)
        return ValidatorConfig()

    log.debug('Загрузка конфигурации из %s', config_file)
    with open(config_file, 'rb') as f:
        config_content= tomllib.load(f)

    validator_parameters = config_content.get('validator', {})

    config =ValidatorConfig(
        path_to_explore=Path(validator_parameters['path_to_explore']) if 'path_to_explore' in validator_parameters else None,
        output_file=Path(validator_parameters['output_file']) if 'output_file' in validator_parameters else None,
        exclude_patterns=validator_parameters.get('exclude_patterns', []),
        log_level=validator_parameters.get('log_level', 'warning'),
        report_format=validator_parameters.get('report_format', 'markdown'),
        validate=validator_parameters.get('validate', False),
        fail_on_error=validator_parameters.get('fail_on_error', False),
    )

    log.debug('Конфигурация загружена: %s', config)
    return config
