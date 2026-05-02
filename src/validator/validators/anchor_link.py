"""
Валидатор якорных ссылок.

(* Синтаксис якоря в Markdown-ссылке *)

anchor_reference = "#", anchor_name ;
anchor_name = { anchor_character } ;
anchor_character = letter | digit | special_char ;
letter = "a" | "b" | ... | "z" | "A" | "B" | ... | "Z" ;
digit = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" ;
special_char = "-" | "_" | "#" | "." | ":" | "%" ;

(* Примеры:
   #section
   #anchor-link
   #section_1
   #anchor#text  (несколько #)
   #             (пустой якорь)
*)

(* URI с якорем *)
uri_with_anchor = path, anchor_reference ;
path = { path_character } ;
path_character = letter | digit | "/" | "." | "-" | "_" ;

(* Полная Markdown-ссылка *)
markdown_link = "[", link_text, "]", "(", uri_with_anchor, ")" ;
link_text = { character } ;

---

Если # отсутствует - якоря нет
Первый # - разделитель в 'путь#якорь'
Якорь может быть пустым - file.md#
Символы после первого # - элементы якоря

"""
import logging
import re
from pathlib import Path

from validator.core.models import DocumentationFile, ValidationIssue, IssueType, SeverityLevel
from validator.validators.base_validator import BaseValidator

log = logging.getLogger(__name__)


class AnchorLinkValidator(BaseValidator):
    """Проверяет существование якоря."""

    MARKDOWN_HEADER_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

    def validate(self, files_to_validate: dict[Path, DocumentationFile], root_dir: Path) -> list[ValidationIssue]:
        log.debug('Начало проверки якорей, файлов: %d', len(files_to_validate))
        issues: list[ValidationIssue] = []

        for file in files_to_validate.values():
            log.debug('Проверка файла: %s', file.path)
            for link in file.links_out:
                log.debug('Проверка внутренних ссылок с якорями')
                if link.anchor and link.is_internal and link.target_file:
                    target_path = root_dir / link.target_file

                    if not target_path.exists():
                        log.debug('Целевой файл %s не найден, ошибка другого типа: %s', target_path, link)
                        continue

                    file_anchors: set[str] = self._get_existing_anchors(file.path)
                    log.debug('Обнаружены якоря:\n%s', file_anchors)

                    if link.anchor not in file_anchors:
                        log.warning(
                            'Якорь "%s" не найден в файле %s (ссылка из %s:%d)',
                            link.anchor, target_path, file.path, link.line_number
                        )
                        issues.append(ValidationIssue(
                            issue_type=IssueType.MISSING_ANCHOR,
                            severity_level=SeverityLevel.ERROR,
                            src_file=file,
                            link=link,
                            message=f'Якорь "#{link.anchor}" не найден в файле {link.target_file}',
                            suggestion='Проверьте название заголовка или создайте соответствующий раздел',
                        ))

        return issues

    def _get_existing_anchors(self, file_path: Path) -> set[str]:
        """Возвращает ссылки, найденные в файле."""
        anchors: set[str] = set()

        try:
            content = file_path.read_text(encoding='utf-8')
        except IOError as err:
            log.error('Не удалось прочитать файл %s: %s', file_path, err)
            return anchors

        for header_match in self.MARKDOWN_HEADER_PATTERN.finditer(content):
            header_text = header_match.group(2).strip()
            header_anchor = self._get_anchor_from_header(header_text)
            anchors.add(header_anchor)

        return anchors

    def _get_anchor_from_header(self, header_text: str) -> str:
        """Возвращает заголовок в формате якорной ссылки.
        Воспроизводит результат работы markdown-процессора
        """
        anchor = header_text.lower()
        anchor = re.sub(r'[\s\t]+', '-', anchor)  # пробелы, табы -> дефисы
        anchor = re.sub(r'-+', '-', anchor)  # удалить повторы дефисов
        anchor = re.sub(r'[^a-z0-9-_]', '', anchor)  # оставить 'a-z0-9-_'
        anchor = anchor.strip('-')
        return anchor
