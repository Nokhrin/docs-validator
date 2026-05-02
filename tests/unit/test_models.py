"""Тесты для моделей данных."""
from pathlib import Path
from validator.core.models import (
    DocumentationFile, Link, LinkType,
    IssueType, SeverityLevel, ValidationIssue, ValidationResult
)


class TestLink:
    """Тестирование модели ссылки."""

    def test_link_with_anchor(self):
        """Ссылка с якорем корректно сохраняет значение."""
        link = Link(
            uri="./guide.md#installation",
            link_type=LinkType.INTERNAL,
            parent_file=Path("README.md"),
            line_number=3,
            anchor="installation"
        )
        assert link.anchor == "installation"
        assert link.uri == "./guide.md#installation"


class TestFileToValidate:
    """Тестирование модели файла."""

    def test_file_is_orphan_when_no_incoming(self):
        """Файл без входящих ссылок считается сиротой."""
        file = DocumentationFile(path=Path("orphan.md"), title="Orphan")
        assert file.is_orphan is True


class TestValidationIssue:
    """Тестирование модели проблемы."""

    def test_issue_with_link(self):
        """Проблема может быть связана с конкретной ссылкой."""
        file = DocumentationFile(path=Path("broken.md"), title="Broken")
        link = Link("missing.md", LinkType.INTERNAL, Path("broken.md"), 10)

        issue = ValidationIssue(
            issue_type=IssueType.BROKEN_LINK,
            severity_level=SeverityLevel.ERROR,
            src_file=file,
            link=link,
            message="Target file not found",
            suggestion="Check the path or create the file"
        )

        assert issue.issue_type == IssueType.BROKEN_LINK
        assert issue.severity_level == SeverityLevel.ERROR
        assert issue.link == link
        assert "not found" in issue.message


class TestValidationResult:

    def test_is_valid_when_no_errors(self):
        """is_valid возвращает True, если нет ошибок (только предупреждения)."""
        file = DocumentationFile(path=Path("test.md"), title="Test")

        warning_issue = ValidationIssue(
            issue_type=IssueType.ORPHAN_FILE,
            severity_level=SeverityLevel.WARNING,
            src_file=file,
            message="Orphan"
        )

        result = ValidationResult(
            files_processed={file.path: file},
            issues=[warning_issue]
        )

        assert result.has_errors is False
        assert result.is_valid is True