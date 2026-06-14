# Documentation Link Validator
A static analyzer for documentation link integrity in Markdown-based repositories. The tool detects broken links, orphan files, missing anchors, and circular dependencies, generating reports in Markdown, HTML, or JSON formats for CI/CD integration.

## Key Features

| Feature          | Description                                                                        |
|------------------|------------------------------------------------------------------------------------|
| File Scanning    | Recursive traversal of `.md` and `.markdown` files with pattern-based exclusions.  |
| Graph Analysis   | Builds a directed connectivity graph to detect structural issues.                  |
| Validation Rules | Checks for broken links, orphan files, missing anchors, and circular dependencies. |
| Reporting        | Generates CLI, Markdown, HTML, and JSON reports for CI/CD integration.             |
| AsciiDoc Support | Basic parsing of `.adoc` and `.asc` files (link macros, cross-references, images). |

---

## Quick Start
1. Install: `pip install git+https://github.com/Nokhrin/docs-validator.git`
2. Run: `docs_validator scan ./docs`
3. Fix issues

---

## Documentation
[User Guide](docs/user_guide.md)
[Developer Guide](docs/developer_guide.md)  
[Specification](docs/specification.md)  
[Architecture Details](docs/architecture.md)

---

## Known Limitations

For detailed information about current limitations and their impact, see [docs/specification.md#known-limitations](docs/specification.md#known-limitations).

**Key points**:
- AsciiDoc support is basic (regex-based, no complex macros)
- External link validation uses conservative classification (WARNING for ambiguous status codes)
- Anchor validation covers Markdown headers only (no HTML anchors in Markdown files)
- Performance is optimized for CI/CD (changed files only), not full repository scans

---

[![Unit Tests](https://github.com/Nokhrin/docs-validator/actions/workflows/test.yml/badge.svg)](https://github.com/Nokhrin/docs-validator/actions/workflows/test.yml)