from pathlib import Path
from validator.core.models import (
    DocumentationFile, Link, LinkType,
    IssueType, SeverityLevel, ValidationIssue, ValidationResult
)


class TestLink:
    def test_link_model_with_anchor_stores_anchor_value(self):
        link = Link(
            uri='./guide.md#installation',
            link_type=LinkType.INTERNAL,
            parent_file=Path('README.md'),
            line_number=3,
            anchor='installation'
        )
        assert link.anchor == 'installation'
        assert link.uri == './guide.md#installation'


class TestDocumentationFile:
    def test_documentation_file_is_orphan_returns_true_when_no_incoming_links(self):
        file = DocumentationFile(path=Path('orphan.md'), title='Orphan')
        assert file.is_orphan is True


class TestValidationIssue:
    def test_validation_issue_with_link_stores_link_and_message(self):
        file = DocumentationFile(path=Path('broken.md'), title='Broken')
        link = Link('missing.md', LinkType.INTERNAL, Path('broken.md'), 10)

        issue = ValidationIssue(
            issue_type=IssueType.BROKEN_LINK,
            severity_level=SeverityLevel.ERROR,
            src_file=file,
            link=link,
            message='Target file not found',
            suggestion='Check the path or create the file'
        )

        assert issue.issue_type == IssueType.BROKEN_LINK
        assert issue.severity_level == SeverityLevel.ERROR
        assert issue.link == link
        assert 'not found' in issue.message


class TestValidationResult:
    def test_validation_result_is_valid_returns_true_when_only_warnings(self):
        file = DocumentationFile(path=Path('test.md'), title='Test')

        warning_issue = ValidationIssue(
            issue_type=IssueType.ORPHAN_FILE,
            severity_level=SeverityLevel.WARNING,
            src_file=file,
            message='Orphan'
        )

        result = ValidationResult(
            files_processed={file.path: file},
            issues=[warning_issue]
        )

        assert result.has_errors is False
        assert result.is_valid is True