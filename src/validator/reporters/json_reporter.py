from pathlib import Path

from validator.core.models import DocumentationFile, ValidationIssue
from validator.reporters import BaseReporter
from validator.serializers import files_to_json


class JSONReporter(BaseReporter):
    """Генерирует отчет в формате JSON."""

    def report(self, files: dict[Path, DocumentationFile], issues: list[ValidationIssue]) -> str:
        """Возвращает JSON строку.
        Работает с DocumentationFile
        """
        files_list: list[DocumentationFile] = list(files.values())
        return files_to_json(files_list, include_content=False)
