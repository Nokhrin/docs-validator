# CI/CD Integration Guide

## GitHub Actions

### Step 1: Create the Workflow File
In your target repository, create the file `.github/workflows/docs-validation.yml`

### Step 2: Add the Configuration
Copy the following template into the file:

```yaml
name: Documentation Validation

on:
  push:
    branches: [ main, master ]
    paths:
      - '/*.md'
      - '/*.markdown'
      - '.github/workflows/docs-validation.yml'
      - '.docs-validator.toml'
  pull_request:
    branches: [ main, master ]
    paths:
      - '/*.md'
      - '/*.markdown'
      - '.github/workflows/docs-validation.yml'
      - '.docs-validator.toml'

jobs:
  validate-docs:
    name: Validate Documentation Links
    runs-on: ubuntu-24.04
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'
          cache: 'pip'

      - name: Install docs-validator
        run: |
          python -m pip install --upgrade pip
          pip install git+https://github.com/Nokhrin/docs-validator.git

      - name: Run documentation validation
        run: |
          docs-validator scan . --validate --fail-on-error --report markdown --output docs-validation-report.md

      - name: Upload validation report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: docs-validation-report
          path: docs-validation-report.md
          retention-days: 7
```


## GitLab Runner

### Step 1: Add Installation and Validation Jobs
Add the following configuration to your `.gitlab-ci.yml`

```yaml
.install_docs_validator:
  before_script:
    - pip install git+https://github.com/Nokhrin/docs-validator.git

validate_docs:
  stage: build
  extends: .install_docs_validator
  script:
    - docs-validator scan . --validate --fail-on-error --report markdown --output docs-validation-report.md
  artifacts:
    paths:
      - docs-validation-report.md
    expire_in: 1 week
    when: on_failure
  rules:
    - changes:
        - "/*.md"
        - "/*.markdown"
        - ".gitlab-ci.yml"
```

### Step 2: Verify Execution
1. Commit and push the changes to your repository
2. Navigate to Build -> Pipelines in GitLab
3. If broken links are found, the `validate_docs` job will fail
4. Download the `docs-validation-report.md` from the job's artifacts to see the detailed breakdown