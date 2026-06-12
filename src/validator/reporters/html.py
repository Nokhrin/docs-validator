"""HTML report generator."""
from pathlib import Path
from validator.core.models import DocumentationFile, ValidationIssue, LinkStatistics
from validator.reporters.base import BaseReporter

class HTMLReporter(BaseReporter):
    """Generates a report in HTML format."""
    def __init__(self, include_files: bool = False):
        self.include_files = include_files

    def report(
        self,
        files: dict[Path, DocumentationFile],
        issues: list[ValidationIssue],
        link_stat: LinkStatistics,
    ) -> str:
        int_total = link_stat.internal_total if link_stat else 0
        ext_total = link_stat.external_total if link_stat else 0
        ext_valid = link_stat.external_total - link_stat.external_broken if link_stat else 0
        ext_broken = link_stat.external_broken if link_stat else 0

        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="en">',
            '<head>',
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            '<title>Documentation Validator Report</title>',
            '<style>',
            self._get_styles(),
            '</style>',
            '</head>',
            '<body>',
            '<header>',
            '<h1>Documentation Validator Report</h1>',
            '</header>',
            '<main>',
            self._render_summary(files, issues, int_total, ext_total, ext_valid, ext_broken),
            self._render_issues(issues),
        ]
        if self.include_files:
            html_parts.append(self._render_files(files))
        html_parts.extend([
            '</main>',
            '</body>',
            '</html>',
        ])
        return '\n'.join(html_parts)

    @staticmethod
    def _get_styles() -> str:
        """Returns CSS styles."""
        return """
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        header { background: #2E86AB; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        section { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h2 { color: #2E86AB; border-bottom: 2px solid #2E86AB; padding-bottom: 10px; }
        .issue { padding: 10px; margin: 10px 0; border-left: 4px solid; border-radius: 4px; }
        .issue.error { background: #ffebee; border-color: #f44336; }
        .issue.warning { background: #fff3e0; border-color: #ff9800; }
        .issue.info { background: #e3f2fd; border-color: #2196f3; }
        .file-card { border: 1px solid #ddd; border-radius: 4px; padding: 15px; margin: 10px 0; }
        .file-card h3 { margin-top: 0; color: #333; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background: #2E86AB; color: white; }
        tr:nth-child(even) { background: #f9f9f9; }
        .stats { display: flex; gap: 20px; flex-wrap: wrap; }
        .stat-card { background: #f5f5f5; padding: 15px; border-radius: 8px; min-width: 150px; }
        .stat-value { font-size: 24px; font-weight: bold; color: #2E86AB; }
        """

    def _render_summary(self, files: dict[Path, DocumentationFile], issues: list[ValidationIssue], internal_total: int, external_total: int, external_valid: int, external_broken: int) -> str:
        total_files = len(files)
        total_links = sum(len(f.links_out) for f in files.values())
        return f"""
        <section id="summary">
        <h2>Summary</h2>
        <div class="stats">
        <div class="stat-card"><div class="stat-value">{total_files}</div><div>Files</div></div>
        <div class="stat-card"><div class="stat-value">{total_links}</div><div>Links</div></div>
        <div class="stat-card"><div class="stat-value" style="color: #2196f3;">{internal_total}</div><div>Internal</div></div>
        <div class="stat-card"><div class="stat-value" style="color: #2196f3;">{external_total}</div><div>External</div></div>
        <div class="stat-card"><div class="stat-value" style="color: #4caf50;">{external_valid}</div><div>Valid External</div></div>
        <div class="stat-card"><div class="stat-value" style="color: #f44336;">{external_broken}</div><div>Broken External</div></div>
        </div>
        </section>
        """

    def _render_issues(self, issues: list[ValidationIssue]) -> str:
        if not issues:
            return """
            <section id="issues">
            <h2>Issues</h2>
            <p>No issues found</p>
            </section>
            """
        issues_html = []
        for issue in issues:
            severity = issue.severity_level.value
            issues_html.append(f"""
            <div class="issue {severity}">
            <strong>[{severity.upper()}]</strong> {issue.issue_type.value}: {issue.message}
            {f'<br><small>File: {issue.src_file.path}:{issue.link.line_number}</small>' if issue.link else ''}
            </div>
            """)
        return f"""
        <section id="issues">
        <h2>Issues ({len(issues)})</h2>
        {''.join(issues_html)}
        </section>
        """

    def _render_files(self, files: dict[Path, DocumentationFile]) -> str:
        files_html = []
        for file in sorted(files.values(), key=lambda f: f.path):
            links_rows = []
            for link in sorted(file.links_out, key=lambda x: x.line_number):
                links_rows.append(f"""
                <tr>
                <td>{link.link_type.name}</td>
                <td>{link.uri}</td>
                <td>{link.anchor or '-'}</td>
                <td>{link.line_number}</td>
                </tr>
                """)
            files_html.append(f"""
            <div class="file-card" id="file-{file.path}">
            <h3>{file.path}</h3>
            <p><strong>Title:</strong> {file.title}</p>
            <p><strong>Links:</strong> {len(file.links_out)}</p>
            {f"""
            <table>
            <thead>
            <tr>
            <th>Type</th>
            <th>URI</th>
            <th>Anchor</th>
            <th>Line</th>
            </tr>
            </thead>
            <tbody>
            {''.join(links_rows)}
            </tbody>
            </table>
            """ if file.links_out else '<p>No outgoing links</p>'}
            </div>
            """)
        return f"""
        <section id="files">
        <h2>Files ({len(files)})</h2>
        {''.join(files_html)}
            </section>
        """