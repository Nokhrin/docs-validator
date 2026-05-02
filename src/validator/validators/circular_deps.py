"""
Валидатор циклических зависимостей.

Цикл возникает, когда файл A ссылается на B, B на C, а C снова на A.
Такие зависимости могут указывать на логические ошибки в структуре документации.

"""
import logging
from pathlib import Path

from validator.core.connectivity_graph import ConnectivityGraph
from validator.core.models import DocumentationFile, ValidationIssue, IssueType, SeverityLevel
from validator.validators import BaseValidator

log = logging.getLogger(__name__)


class CircularDependencyValidator(BaseValidator):
    def validate(
            self,
            files_to_validate: dict[Path, DocumentationFile],
            root_dir: Path,
    ) -> list[ValidationIssue]:
        """Возвращает список issues типа CIRCULAR_DEPENDENCY."""
        log.debug('Начало проверки циклических зависимостей, файлов: %d', len(files_to_validate))
        issues: list[ValidationIssue] = []

        dependencies_graph = ConnectivityGraph()
        for file in files_to_validate.values():
            dependencies_graph.add_file(file)
            for link in file.links_out:
                if link.is_internal and link.target_file:
                    target = root_dir / link.target_file
                    if target.exists():
                        dependencies_graph.add_link(link)

        simple_cycles: list[list[Path]] = dependencies_graph.get_simple_cycles()

        # issues
        cycles_processed: set[tuple[Path]] = set()
        for cycle in simple_cycles:
            log.debug('Удаление дубликатов из цикла')
            cycle_key = tuple(sorted(cycle))
            if cycle_key in cycles_processed:
                continue
            cycles_processed.add(cycle_key)
            cycle_repr = ' -> '.join(str(node) for node in cycle) + f' -> {cycle[0]}'

            for file_path in cycle:
                if file_path in files_to_validate:
                    file = files_to_validate[file_path]
                    issues.append(ValidationIssue(
                        issue_type=IssueType.CIRCULAR_DEPENDENCY,
                        severity_level=SeverityLevel.WARNING,
                        src_file=file,
                        message=f'Файл участвует в циклической зависимости: {cycle_repr}',
                        suggestion='Разорвите цикл, удалив или перенаправив одну из ссылок',
                    ))

        log.debug('Найдено циклов: %d, проблем: %d', len(cycles_processed), len(issues))
        return issues
