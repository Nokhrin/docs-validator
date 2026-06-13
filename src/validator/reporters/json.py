import json
from datetime import datetime
from pathlib import Path
from typing import Any

from validator.core.models import DocumentationFile, ValidationIssue, LinkStatistics
from validator.core.models import Link, LinkType
from validator.reporters import BaseReporter


class JSONReporter(BaseReporter):
    def report(
            self,
            files: dict[Path, DocumentationFile],
            issues: list[ValidationIssue],
            link_stat: LinkStatistics,
    ) -> str:
        """Return report as JSON string."""
        files_list: list[DocumentationFile] = list(files.values())
        return files_to_json(files_list, include_content=False)


class DataclassEncoder(json.JSONEncoder):
    """Custom JSON encoder for validator objects."""

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


def file_to_dict(file: DocumentationFile, include_content: bool = False) -> dict[str, Any]:
    """Converts DocumentationFile to dict for JSON serialization.

    Returns:
        Dict ready for json.dumps().
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


def link_to_dict(link: Link) -> dict[str, Any]:
    """Converts Link to dict for JSON serialization.

    Returns:
        Dict ready for json.dumps().
    """
    return {
        'uri': link.uri,
        'link_type': link.link_type.name,
        'source_file': str(link.parent_file),
        'line_number': link.line_number,
        'anchor': link.anchor,
    }


def files_to_json(
        files: list[DocumentationFile],
        include_content: bool = False,
        indent: int = 2,
) -> str:
    """Return Files list as JSON string."""
    data = [file_to_dict(f, include_content) for f in files]
    return json.dumps(data, indent=indent, ensure_ascii=False, cls=DataclassEncoder)
