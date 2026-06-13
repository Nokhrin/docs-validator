"""Validator configuration management."""
import logging
from dataclasses import dataclass, field, fields, replace
from pathlib import Path
from tomllib import load, TOMLDecodeError
from typing import Optional

log = logging.getLogger(__name__)


@dataclass
class ValidatorConfig:
    path_to_explore: Optional[Path] = None
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
    report_include_files: bool = False
    validate_external_anchors: bool = False
    external_anchor_timeout_sec: int = 10
    external_anchor_user_agent: str = "'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'"


def load_config_from_toml(config_file: Path) -> ValidatorConfig:
    if not config_file.exists():
        log.warning('Specified config file not found: %s. Using default configuration.', config_file)
        return ValidatorConfig()

    try:
        log.debug('Loading configuration from %s', config_file)
        with open(config_file, 'rb') as f:
            config_content: dict[str, Any] = load(f)
    except TOMLDecodeError as err:
        log.error('TOML syntax error in file %s: %s', config_file, err)
        return ValidatorConfig()
    except IOError as err:
        log.error('Failed to read config file %s: %s', config_file, err)
        return ValidatorConfig()

    validator_parameters: dict[str, Any] = config_content.get('validator', {})

    arguments_valid: set[str] = {arg.name for arg in fields(ValidatorConfig)}
    arguments_invalid: set[str] = set(validator_parameters.keys()) - arguments_valid
    if arguments_invalid:
        raise ValueError(f'Unknown configuration fields in {config_file}: {arguments_invalid}')

    config = ValidatorConfig(
        path_to_explore=Path(validator_parameters['path_to_explore']) if 'path_to_explore' in validator_parameters else None,
        exclude_patterns=validator_parameters.get('exclude_patterns', []),
        log_level=validator_parameters.get('log_level', 'warning'),
        report_format=validator_parameters.get('report_format', 'markdown'),
        output_file=Path(validator_parameters['output_file']) if 'output_file' in validator_parameters else None,
        is_validate=validator_parameters.get('is_validate', False),
        is_fail_on_error=validator_parameters.get('is_fail_on_error', False),
        external_timeout_sec=validator_parameters.get('external_timeout_sec', 10),
        max_threads_number=validator_parameters.get('max_threads_number', 5),
        hosts_to_ignore=validator_parameters.get('hosts_to_ignore', []),
        is_skip_external=validator_parameters.get('is_skip_external', False),
        report_include_files=validator_parameters.get('report_include_files', False),
        validate_external_anchors=validator_parameters.get('validate_external_anchors', False),
        external_anchor_timeout_sec=validator_parameters.get('external_anchor_timeout_sec', 10),
        external_anchor_user_agent=validator_parameters.get('external_anchor_user_agent', 'docs-validator/0.0.1'),
    )

    log.debug('Configuration loaded: %s', config)
    return config


def merge_config(config_init: ValidatorConfig, config_to_merge: ValidatorConfig) -> ValidatorConfig:
    updates = {
        f.name: getattr(config_to_merge, f.name)
        for f in fields(config_to_merge)
        if getattr(config_to_merge, f.name) is not None
    }
    return replace(config_init, **updates)
