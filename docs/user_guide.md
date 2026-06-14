# Usage

# Installation

## Requirements
- Python 3.13 or higher.
- Install `docs_validator` directly into the target project that requires documentation link validation. This ensures seamless integration with the project's CI/CD pipeline and local development environment.

## Local installation

Install for the docs-validator itself
```shell
pip install -e .
docs_validator --help
```

Install for the system located in a sibling directory
```shell
cd ~/projects/project_to_validate/
python3 -m venv .venv
source .venv/bin/activate
pip install -e ../docs_validator[dev]
docs_validator --help
```

> The `-e` flag creates symbolic links to `src/docs_validator`. Code changes apply instantly without reinstallation.


## GitHub installation

```shell
cd ~/projects/playbook_markdown_validation/
python3 -m venv .venv
source .venv/bin/activate
pip install git+https://github.com/Nokhrin/docs-validator.git
docs_validator --help
```

# Validating docs

### Setup project under test
Example: https://github.com/avito-tech/playbook
Fork
Clone
```shell
mkdir -p "$HOME/projects/"
git clone git@github.com:Nokhrin/playbook.git playbook_markdown_validation
DOCS_DIR="."
```

### Validation Without Reporting
```shell
docs_validator scan $DOCS_DIR
```

### Generate Markdown Report
```shell
docs_validator scan $DOCS_DIR --report markdown --output /tmp/playbook_markdown_validation.md
```

### Generate Interactive HTML Report
```shell
docs_validator scan $DOCS_DIR --report html --output /tmp/playbook_markdown_validation.html
```

### Skip External Link Verification
```shell
docs_validator scan $DOCS_DIR --skip-external
```

### Local Validation via pre-commit Hook

Note: The hook requires dependencies from `[dev]` extras. Install them with:
```shell
pip install -e ".[dev]"
```

Create the hook file `.githooks/pre-commit`
- [pre-commit](../templates/.githooks.pre-commit.docs_validator)

```shell
# setup
chmod +x .githooks/pre-commit
git config core.hooksPath .githooks
# verify
./.githooks/pre-commit
```


### CI/CD Integration
GitHub/GitLab actions examples:
- [github workflow](../templates/.github_workflows.docs_validation.yml)
- [.gitlab-ci](../templates/.gitlab-ci.yml)

Local verification:
```shell
docs_validator scan $DOCS_DIR --validate --fail-on-error
```

### Using a Configuration File
By default, the tool looks for the `.docs_validator.toml` file in the root directory of the project being scanned. Alternatively, you can specify a custom path using the `--config` flag.

Example `infrastructure/.docs_validator.toml`:
```shell
cat > infrastructure/.docs_validator.toml << EOF
[docs_validator]
path_to_explore = '$DOCS_DIR'
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

Run with a custom configuration path:
```shell
docs_validator scan --config infrastructure/.docs_validator.toml
```

---