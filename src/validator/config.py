"""Управление конфигурацией валидатора."""
import logging
from dataclasses import dataclass, field
from pathlib import Path
from tomllib import load, TOMLDecodeError
from typing import Optional

log = logging.getLogger(__name__)

DEFAULT_CONFIG_FILENAME = '.docs-validator.toml'


@dataclass
class ValidatorConfig:
    exclude_patterns: list[str] = field(default_factory=list)
    log_level: str = 'warning'
    report_format: str = 'markdown'
    output_file: Optional[Path] = None
    is_validate: bool = False
    is_fail_on_error: bool = False
    external_timeout_sec: int = 10
    max_threads_number: int = 5
    hosts_to_ignore: list[str] = field(default_factory=list)
    is_skip_external: bool = False

def load_config_from_toml(config_file: Path) -> ValidatorConfig:
    if not config_file.exists():
        log.warning('Указанный файл конфигурации не найден: %s\n'
                    'Создана конфигурация по умолчанию', config_file)
        return ValidatorConfig()

    try:
        log.debug('Загрузка конфигурации из %s', config_file)
        with open(config_file, 'rb') as f:
            config_content= load(f)
    except TOMLDecodeError as err:
        log.error('Ошибка синтаксиса TOML в файле %s: %s', config_file, err)
        raise
    except IOError as err:
        log.error('Не удалось прочитать файл конфигурации %s: %s', config_file, err)
        raise

    validator_parameters = config_content.get('validator', {})

    config =ValidatorConfig(
        output_file=Path(validator_parameters['output_file']) if 'output_file' in validator_parameters else None,
        exclude_patterns=validator_parameters.get('exclude_patterns', []),
        log_level=validator_parameters.get('log_level', 'warning'),
        report_format=validator_parameters.get('report_format', 'markdown'),
        is_validate=validator_parameters.get('is_validate', False),
        is_fail_on_error=validator_parameters.get('is_fail_on_error', False),
        external_timeout_sec=validator_parameters.get('external_timeout_sec', 10),
        max_threads_number=validator_parameters.get('max_threads_number', 5),
        hosts_to_ignore=validator_parameters.get('hosts_to_ignore', []),
        is_skip_external=validator_parameters.get('is_skip_external', False),
    )

    log.debug('Конфигурация загружена: %s', config)
    return config