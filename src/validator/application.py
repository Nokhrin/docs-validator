import logging
import sys
from argparse import Namespace
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator, TextIO

from validator.config import ValidatorConfig, load_config_from_toml
from validator.core.files_explorer import FilesExplorer
from validator.core.link_extractor import LinkExtractor
from validator.core.models import DocumentationFile, ValidationIssue, LinkStatistics, LinkType, SeverityLevel, \
    IssueType, Link
from validator.reporters import JSONReporter, MarkdownReporter, HTMLReporter
from validator.validators import BrokenLinkValidator, OrphanFileValidator, AnchorLinkValidator, \
    CircularDependencyValidator, ExternalLinkValidator

log = logging.getLogger(__name__)


def load_configuration(args: Namespace) -> ValidatorConfig:
    """Загружает значения параметров конфигурации.

    Источники конфигурации: cli, *.toml
    """
    DEFAULT_CONFIG_FILENAME = '.docs-validator.toml'
    config_file = Path.cwd() / DEFAULT_CONFIG_FILENAME
    if args.config:
        config_file = Path(args.config)

    default_config = ValidatorConfig(
            exclude_patterns=args.exclude_patterns,
            log_level=args.log_level,
            report_format=args.report_format,
            output_file=args.output_file,
            is_validate=args.is_validate,
            is_fail_on_error=args.is_fail_on_error,
            external_timeout_sec=args.external_timeout_sec,
            max_threads_number=args.max_threads_number,
            hosts_to_ignore=args.hosts_to_ignore,
            is_skip_external=args.is_skip_external,
        )

    if not config_file.exists():
        log.debug('Запрошенный файл конфигурации не найден: %s', config_file)
        log.debug('Используется конфигурация по умолчанию: %s', default_config)
        return default_config
    try:
        log.debug('Используется файл конфигурации: %s', config_file)
        return load_config_from_toml(config_file)
    except IOError as err:
        log.error('Ошибка при чтении конфигурации %s: %s', config_file, err)
        log.debug('Используется конфигурация по умолчанию: %s', default_config)
        return default_config


def explore_files(path_to_explore: Path, config: ValidatorConfig) -> list[DocumentationFile]:
    """Извлекает метаданные из файлов в директории.

    Рекурсивно от root
    """

    if not path_to_explore.exists():
        log.error('Не удалось найти запрошенный путь: %s', path_to_explore)

    if not path_to_explore.is_dir():
        log.error('Запрошенный путь не является каталогом: %s', path_to_explore)

    log.debug('Выполняется обход каталога %s', path_to_explore)

    explorer = FilesExplorer(
        root_path=path_to_explore,
        patterns_exclude=set(config.exclude_patterns)
    )

    return list(explorer.explore())


def collect_links(files: list[DocumentationFile]) -> list[DocumentationFile]:
    """Записывает информацию о ссылках файла.

    Результат в поле DocumentationFile.out_links
    Возвращает новый экземпляр списка
    """
    for file in files:
        try:
            content = file.path.read_text(encoding='utf-8')
            extractor = LinkExtractor(file.path)
            file.links_out = set(extractor.get_links_from_file(content))
        except IOError as err:
            log.error('При чтении файла %s произошла ошибка: %s', file.path, err)
            file.links_out = set()
    return files


def collect_issues(files: list[DocumentationFile], config: ValidatorConfig) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if config.is_validate:
        files_to_validate = {file.path: file for file in files}
        validators = [BrokenLinkValidator(), OrphanFileValidator(), AnchorLinkValidator(), CircularDependencyValidator()]
        if not config.is_skip_external:
            validators.append(ExternalLinkValidator(
                external_timeout_sec=config.external_timeout_sec,
                max_threads_number=config.max_threads_number,
                hosts_to_ignore=config.hosts_to_ignore,
            ))
        for validator in validators:
            new_issues = validator.validate(files_to_validate, config.path_to_explore)
            issues.extend(new_issues)
    return issues


def aggregate_issue_statistics(
        files: list[DocumentationFile],
        issues: list[ValidationIssue],
) -> LinkStatistics:
    """Возвращает статистику валидации ссылок."""
    broken_links: set[Link] = {i.link for i in issues if i.link}
    internal_total = 0
    internal_broken = 0
    external_total = 0
    external_broken = 0

    for file in files:
        for link in file.links_out:
            if link.link_type is LinkType.INTERNAL:
                internal_total += 1
                if link in broken_links:
                    internal_broken += 1
            elif link.link_type is LinkType.EXTERNAL:
                external_total += 1
                if link in broken_links:
                    external_broken += 1

    return LinkStatistics(
        internal_total=internal_total,
        internal_broken=internal_broken,
        external_total=external_total,
        external_broken=external_broken,
    )


def generate_report(files: dict[Path, DocumentationFile], issues: list[ValidationIssue], stats: LinkStatistics, config: ValidatorConfig) -> str:
    reporters: dict[str, Callable[[dict, list, LinkStatistics], str]] = {
        'json': lambda f, i, s: JSONReporter().report(f, i, s),
        'markdown': lambda f, i, s: MarkdownReporter().report(f, i, s),
        'html': lambda f, i, s: HTMLReporter().report(f, i, s),
    }
    make_report = reporters.get(config.report_format, reporters['markdown'])

    try:
        report = make_report(files, issues, stats)
    except Exception as err:
        log.error('Ошибка при генерации отчета: %s', err)
        raise RuntimeError(err) from err

    if config.output_file:
        Path(config.output_file).write_text(report, encoding='utf-8')

    files_total = len(files)
    links_total = sum(len(f.links_out) for f in files)
    summary_lines = [
        "=" * 40, "СТАТИСТИКА ВЫПОЛНЕНИЯ", "=" * 40,
        f"Обработано файлов: {files_total}",
        f"Обнаружено ссылок: {links_total}",
        f"Внутренних ссылок: {stats.internal_total}",
        f"Внешних ссылок: {stats.external_total} (недоступно: {stats.external_broken})",
    ]
    if issues:
        error_count = sum(1 for i in issues if i.severity_level.value == 'error')
        summary_lines.append(f"Найдено проблем: {len(issues)} (из них ошибок: {error_count})")
    else:
        summary_lines.append("Проблем не обнаружено.")
    summary_lines.append("=" * 40)

    return f"{report}\n\n{'\n'.join(summary_lines)}"

def write_report(report_content: str, output_path: Path | None) -> None:
    with open_output(output_path) as out_stream:
        out_stream.write(report_content)
        if output_path is None:
            out_stream.write('\n')


@contextmanager
def open_output(path: Path | None) -> Iterator[TextIO]:
    if path is None:
        yield sys.stdout
    else:
        with open(path, 'w', encoding='utf-8') as file:
            yield file


def get_exit_code(
        issues: list[ValidationIssue],
        config: ValidatorConfig,
) -> int:
    if config.is_fail_on_error and any(i.severity_level.value == 'error' for i in issues):
        return 1
    return 0
