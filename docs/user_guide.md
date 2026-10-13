# Usage

# Installation

## Requirements

- Python 3.13 or higher.
- Install `docs_validator` directly into the target project that requires documentation link validation.

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
python3 -m venv .venv
source .venv/bin/activate
pip install git+https://github.com/Nokhrin/docs-validator.git
docs_validator --help
```



---

# Validating docs

### Setup system to test

Example
Source: https://github.com/avito-tech/playbook
Fork: https://github.com/Nokhrin/playbook
Clone

```shell
mkdir -p "$HOME/projects/"
cd "$HOME/projects/"
git clone git@github.com:Nokhrin/playbook.git playbook_markdown_validation
cd playbook_markdown_validation
python3 -m venv .venv
source .venv/bin/activate
pip install git+https://github.com/Nokhrin/docs-validator.git
docs_validator --help
```

### Validation: result in stdout

```shell
docs_validator scan
```

### Validation: result in md

```shell
TS=$(date +%Y%m%d_%H%M%S)
docs_validator scan --report markdown --output /tmp/playbook_markdown_validation_$TS.md
less /tmp/playbook_markdown_validation_$TS.md
```

### Validation: result in html

```shell
TS=$(date +%Y%m%d_%H%M%S)
docs_validator scan --report html --output /tmp/playbook_markdown_validation_$TS.html
less /tmp/playbook_markdown_validation_$TS.html
```

### Validation: Skip External Link Verification

```shell
docs_validator scan --skip-external
```

### Validation: run via pre-commit Hook

Note: The hook requires

- python environment
- dependencies from `[dev]` extras. Install them with:

```shell
pip install -e ".[dev]"
```

### Git hook
Create pre-commit script
```shell
docs-validator install --pre-commit 
```

### CI/CD Integration

Create workflow scripts:
```shell
docs-validator install --github 
```

```shell
docs-validator install --gitlab 
```


### Using a Configuration File

By default, the tool looks for the `.docs_validator.toml` file in the root directory of the project being scanned.
Alternatively, you can specify a custom path using the `--config` flag.

Run with a custom configuration path:

```shell
docs_validator scan --config infrastructure/.docs_validator.toml
```

---