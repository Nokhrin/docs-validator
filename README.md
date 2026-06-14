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

[CI/CD Integration Guide](docs/ci-integration.md)  
[Developer Guide](docs/development.md)  
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
- 
---

## Usage
### Requirements
- Python 3.13 or higher.

### Installation
Install `docs-validator` directly into the target project that requires documentation link validation. This ensures seamless integration with the project's CI/CD pipeline and local development environment.
```shell
cd ~/projects/project_to_validate/
python3 -m venv .venv
source .venv/bin/activate
pip install git+https://github.com/Nokhrin/docs-validator.git
docs-validator --help
```

---

## Use Cases
### 1. Validation Without Reporting
```shell
docs-validator scan ./docs
```

### 2. Generate Markdown Report
```shell
docs-validator scan ./docs --report markdown --output /tmp/report.md
```

### 3. Generate Interactive HTML Report
```shell
docs-validator scan ./docs --report html --output /tmp/report.html
```

### 4. CI/CD Integration (Strict Mode)
```shell
docs-validator scan ./docs --validate --fail-on-error
```

### 5. Using a Configuration File
By default, the tool looks for the `.docs-validator.toml` file in the root directory of the project being scanned. Alternatively, you can specify a custom path using the `--config` flag.

Example `.docs-validator.toml`:
```shell
cat > .docs-validator.toml << 'EOF'
[validator]
path_to_explore = './docs'
exclude_patterns = ['.git', 'node_modules', '*.tmp']
log_level = 'warning'
report_format = 'markdown'
is_validate = true
is_fail_on_error = true
external_timeout_sec = 10
max_threads_number = 5
hosts_to_ignore = ['localhost', '127.0.0.1']
is_skip_external = false
EOF
```

Run (automatically uses `.docs-validator.toml` from the current directory):
```shell
docs-validator scan
```

Run with a custom configuration path:
```shell
docs-validator scan --config /path/to/custom-config.toml
```

### 6. Skip External Link Verification
```shell
docs-validator scan ./docs --skip-external
```

---

### Local Validation via pre-commit Hook

> Note: The hook requires dependencies from `[dev]` extras. Install them with:
> ```shell
> pip install -e ".[dev]"
> ```

Create the hook file `.githooks/pre-commit`
[Example](.githooks/pre-commit)

```shell
# setup
chmod +x .githooks/pre-commit
git config core.hooksPath .githooks
# verify
bash .githooks/pre-commit
```

---

[![Unit Tests](https://github.com/Nokhrin/docs-validator/actions/workflows/test.yml/badge.svg)](https://github.com/Nokhrin/docs-validator/actions/workflows/test.yml)