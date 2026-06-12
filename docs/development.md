
## Development - Environment
### Editable Installation
For debugging and making changes to the validator code:
```shell
cd ~/projects/project_to_validate/
source .venv/bin/activate
pip install -e ../docs-validator[dev]
```

> The `-e` flag creates symbolic links to `src/validator`. Code changes apply instantly without reinstallation.

### Running Docs Validation
```shell
docs-validator scan . --validate --log-level debug
```


Check without creating a commit:
```shell
bash .githooks/pre-commit
```

Skip check: `git commit --no-verify`

## Development Iteration
1. Make changes in `../docs-validator/src/validator/`.
2. Re-run the validation command. Recompilation or `pip install` is not required.

### Running Tests
```shell
# With coverage
pytest --cov=src/validator --cov-report=term
# Verbose output
pytest tests/unit/ -vv --tb=short
```

### Local Code Validation (pre-commit hook)
The repository uses a native hook to check before committing.
The hook blocks the commit if tests fail or coverage is <70%.
```shell
chmod +x .githooks/pre-commit
git config core.hooksPath .githooks
```

### Updating Dependencies
#### In the `docs-validator` root:
```shell
source .venv/bin/activate
pip install -e ".[dev]"
```

#### In the tested project:
```shell
cd ../project_to_validate/ && source .venv/bin/activate
pip install -e ../docs-validator --upgrade
```

---

### PyCharm Pytest Configuration
To configure pytest templates in PyCharm:
- **Additional arguments**: `-vv --tb=short --color=yes --cov=src/validator --cov-report=term -p no:warnings`
- **Working directory**: `$ProjectFileDir$`
- **Environment variables**: `PYTEST_ADDOPTS="-vv --tb=short --color=yes"`

### Integration Testing Procedure (Example)
To verify the validator's functionality on a real documentation project (e.g., `notes_and_thoughts`):

1. **Setup**: Ensure `docs-validator` is installed in editable mode with `[dev]` dependencies in an adjacent directory.
2. **Clone Test Repository**: `git clone https://gitlab.com/Nokhrin/notes_and_thoughts.git` (or any target project).
3. **Run Full Validation**: 
   ```shell
   docs-validator scan ../notes_and_thoughts --validate --report html --output /tmp/report.html --log-level info
   ```
4. **Analyze Results**: Open `/tmp/report.html` in a browser. Verify sections: *Issues Summary*, *Broken Links*, *Orphan Files*, and *Missing Anchors*.
5. **Strict Mode (CI Simulation)**: 
   ```shell
   docs-validator scan ../notes_and_thoughts --validate --fail-on-error
   echo "Exit code: $?" # Should be 1 if ERRORs exist, 0 otherwise.
   ```
6. **Test Configuration Auto-loading**: Create a `.docs-validator.toml` in the root of `notes_and_thoughts` and run `docs-validator scan` without flags to verify settings are applied.

---

## Debugging in PyCharm
### Prerequisites
- The `docs-validator` project and the tested project (e.g., `project_to_validate`) are cloned into adjacent directories.
- The tested project has a virtual environment with `docs-validator` installed in editable mode.

### Run Configuration for Debugging
1. Create a new configuration: `Run` -> `Edit Configurations...` -> `+` -> `Python`
2. Fill in the parameters:

   | Parameter             | Value                                                      |
   |-----------------------|------------------------------------------------------------|
   | Script path           | `path/to/docs-validator/src/validator/cli.py`              |
   | Module name           | *(leave empty)*                                            |
   | Parameters            | `scan ../project_to_validate --validate --log-level debug` |
   | Python interpreter    | Interpreter from the tested project's `.venv`              |
   | Working directory     | `path/to/project_to_validate`                              |
   | Environment variables | `PYTHONDONTWRITEBYTECODE=1;PYTHONUNBUFFERED=1`             |

3. Set breakpoints.
4. Run `Debug`.

### Test Run Configuration
1. Create a configuration: `Run` -> `Edit Configurations...` -> `+` -> `pytest`
2. Parameters:

   | Parameter             | Value                                                 |
   |-----------------------|-------------------------------------------------------|
   | Name                  | `pytest unit tests`                                   |
   | Target                | `path/to/docs-validator/tests/unit/`                  |
   | Additional arguments  | `-vv --tb=short --color=yes -s --log-cli-level=DEBUG` |
   | Working directory     | `$ProjectFileDir$`                                    |
   | Environment variables | *(leave empty)*                                       |

---

### Technical Nuances and Potential Errors
| Scenario                                                                 | Cause                                                                        | Solution                                                                                                              |
|--------------------------------------------------------------------------|------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| `docs-validator: command not found`                                      | venv is not activated or `PATH` is not updated                               | Run `source .venv/bin/activate` or use `python -m validator.cli scan .`                                               |
| Settings are read from `docs-validator` instead of `project_to_validate` | In `cli.py`, the config is searched in `Path.cwd() / ".docs-validator.toml"` | Run the command from `project_to_validate` or explicitly specify `--config ./docs-validator.toml`                     |
| Absolute paths are displayed in reports                                  | `FilesExplorer` builds paths relative to `root_path`                         | Pass a relative path (`.` or `./docs`) to `scan`, not an absolute one                                                 |
| Dependencies are not resolved                                            | `pyproject.toml` in `docs-validator` requires `networkx`                     | The `[dev]` flag in `pip install` automatically installs dependencies from `dependencies` and `optional-dependencies` |

---