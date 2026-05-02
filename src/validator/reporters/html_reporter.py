"""
Отчет в html.
"""
from pathlib import Path
from validator.core.models import DocumentationFile, ValidationIssue
from validator.reporters.base_reporter import BaseReporter


class HTMLReporter(BaseReporter):
    """Генерирует отчет в формате HTML."""

    def report(
        self,
        files: dict[Path, DocumentationFile],
        issues: list[ValidationIssue],
    ) -> str:
        """Возвращает HTML-отчет."""
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="ru">',
            '<head>',
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            '<title>Отчет валидатора документации</title>',
            '<style>',
            self._get_styles(),
            '</style>',
            '</head>',
            '<body>',
            '<header>',
            '<h1>🔍 Отчет валидатора документации</h1>',
            '</header>',
            '<main>',
            self._render_summary(files, issues),
            self._render_issues(issues),
            self._render_files(files),
            '</main>',
            '</body>',
            '</html>',
        ]
        return '\n'.join(html_parts)

    @staticmethod
    def _get_styles() -> str:
        """Возвращает CSS-стили."""
        return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        header {
            background: #2E86AB;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        nav {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        nav a {
            margin-right: 15px;
            color: #2E86AB;
            text-decoration: none;
        }
        nav a:hover {
            text-decoration: underline;
        }
        section {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h2 {
            color: #2E86AB;
            border-bottom: 2px solid #2E86AB;
            padding-bottom: 10px;
        }
        .issue {
            padding: 10px;
            margin: 10px 0;
            border-left: 4px solid;
            border-radius: 4px;
        }
        .issue.error {
            background: #ffebee;
            border-color: #f44336;
        }
        .issue.warning {
            background: #fff3e0;
            border-color: #ff9800;
        }
        .issue.info {
            background: #e3f2fd;
            border-color: #2196f3;
        }
        .file-card {
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            margin: 10px 0;
        }
        .file-card h3 {
            margin-top: 0;
            color: #333;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background: #2E86AB;
            color: white;
        }
        tr:nth-child(even) {
            background: #f9f9f9;
        }
        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }
        .badge-error { background: #f44336; color: white; }
        .badge-warning { background: #ff9800; color: white; }
        .badge-info { background: #2196f3; color: white; }
        .stats {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }
        .stat-card {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 8px;
            min-width: 150px;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #2E86AB;
        }
        """

    def _render_summary(
        self,
        files: dict[Path, DocumentationFile],
        issues: list[ValidationIssue],
    ) -> str:
        """Рендерит сводку."""
        total_files = len(files)
        total_links = sum(len(f.links_out) for f in files.values())
        error_count = sum(1 for i in issues if i.severity_level.value == 'error')
        warning_count = sum(1 for i in issues if i.severity_level.value == 'warning')

        return f"""
        <section id="summary">
            <h2>📊 Сводка</h2>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{total_files}</div>
                    <div>Файлов</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{total_links}</div>
                    <div>Ссылок</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color: #f44336;">{error_count}</div>
                    <div>Ошибок</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color: #ff9800;">{warning_count}</div>
                    <div>Предупреждений</div>
                </div>
            </div>
        </section>
        """

    def _render_issues(self, issues: list[ValidationIssue]) -> str:
        """Рендерит секцию проблем."""
        if not issues:
            return """
            <section id="issues">
                <h2>⚠️ Проблемы</h2>
                <p>✅ Проблем не обнаружено</p>
            </section>
            """

        issues_html = []
        for issue in issues:
            severity = issue.severity_level.value
            issues_html.append(f"""
            <div class="issue {severity}">
                <strong>[{severity.upper()}]</strong> {issue.issue_type.value}: {issue.message}
                {f'<br><small>Файл: {issue.src_file.path}:{issue.link.line_number}</small>' if issue.link else ''}
            </div>
            """)

        return f"""
        <section id="issues">
            <h2>⚠️ Проблемы ({len(issues)})</h2>
            {''.join(issues_html)}
        </section>
        """

    def _render_files(self, files: dict[Path, DocumentationFile]) -> str:
        """Рендерит секцию файлов."""
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
                <h3>📄 {file.path}</h3>
                <p><strong>Заголовок:</strong> {file.title}</p>
                <p><strong>Ссылок:</strong> {len(file.links_out)}</p>
                {f"""
                <table>
                    <thead>
                        <tr>
                            <th>Тип</th>
                            <th>URI</th>
                            <th>Якорь</th>
                            <th>Строка</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(links_rows)}
                    </tbody>
                </table>
                """ if file.links_out else '<p>Нет исходящих ссылок</p>'}
            </div>
            """)

        return f"""
        <section id="files">
            <h2>📁 Файлы ({len(files)})</h2>
            {''.join(files_html)}
        </section>
        """