"""Сериализация объектов валидатора в JSON-формат."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from validator.core.models import FileToValidate, Link, LinkType


class DataclassEncoder(json.JSONEncoder):
    """Кастомный JSON-encoder для объектов валидатора."""

    def default(self, obj: Any) -> Any:
        match obj:
            case Path():
                return str(obj)
            case datetime():
                return obj.isoformat()
            case set():
                return list(obj)
            case LinkType():
                return obj.name
            case _:
                return super().default(obj)


def file_to_dict(file: FileToValidate, include_content: bool = False) -> dict:
    """Преобразует FileToValidate в dict для JSON-сериализации.

    Args:
        file: Объект FileToValidate.
        include_content: Включить содержимое файла (по умолчанию False).

    Returns:
        Dict, готовый к json.dumps().
    """
    result = {
        'path': str(file.path),
        'title': file.title,
        'links_out': [link_to_dict(link) for link in file.links_out],
        'links_in': [link_to_dict(link) for link in file.links_in],
        'word_count': file.word_count,
        'last_modified': file.last_modified.isoformat() if file.last_modified else None,
        'is_orphan': file.is_orphan,
    }

    if include_content:
        try:
            result['content'] = file.path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError) as err:
            result['content_error'] = str(err)

    return result


def link_to_dict(link: Link) -> dict:
    """Преобразует Link в dict для JSON-сериализации."""
    return {
        'uri': link.uri,
        'link_type': link.link_type.name,
        'source_file': str(link.source_file),
        'line_number': link.line_number,
        'anchor': link.anchor,
    }


def files_to_json(
    files: list[FileToValidate],
    include_content: bool = False,
    indent: int = 2,
) -> str:
    """Сериализует список файлов в JSON-строку.

    Args:
        files: Список FileToValidate.
        include_content: Включить содержимое файлов.
        indent: Отступ для форматирования JSON.

    Returns:
        JSON-строка.
    """
    data = [file_to_dict(f, include_content) for f in files]
    return json.dumps(data, indent=indent, ensure_ascii=False, cls=DataclassEncoder)