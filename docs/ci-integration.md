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
      - '**/*.md'
      - '**/*.markdown'
      - '**/*.asc'
      - '**/*.adoc'
      - '.github/workflows/docs-validation.yml'
      - '.docs-validator.toml'

  pull_request:
    branches: [ main, master ]
    paths:
      - '**/*.md'
      - '**/*.markdown'
      - '**/*.asc'
      - '**/*.adoc'
      - '.github/workflows/docs-validation.yml'
      - '.docs-validator.toml'

  workflow_dispatch:
    inputs:
      target_path:
        description: 'Path to scan'
        required: false
        default: '.'
      fail_on_error:
        description: 'Fail pipeline on errors'
        required: false
        type: boolean
        default: true

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

      - name: Install docs-validator
        run: |
          python -m pip install --upgrade pip
          pip install git+https://github.com/Nokhrin/docs-validator.git

      - name: Run documentation validation
        run: |
          FAIL_FLAG=""
          if [ "${{ github.event.inputs.fail_on_error }}" = "true" ] || [ -z "${{ github.event.inputs.fail_on_error }}" ]; then
            FAIL_FLAG="--fail-on-error"
          fi
          TARGET_PATH="${{ github.event.inputs.target_path || '.' }}"
          docs-validator scan "$TARGET_PATH" --validate $FAIL_FLAG --report markdown --output docs-validation-report.md

      - name: Upload validation report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: docs-validation-report
          path: docs-validation-report.md
          retention-days: 7
```

### Step 3: Manual Execution
1. Navigate to Actions tab in your repository
2. Select Documentation Validation workflow
3. Click Run workflow button
4. Select the branch and configure parameters
5. Click Run workflow

---

## GitLab Runner

### Step 1: Add Installation and Validation Jobs
Add the following configuration to your `.gitlab-ci.yml`:

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
        - "/*.asc"
        - "/*.adoc"
        - ".gitlab-ci.yml"
        - ".docs-validator.toml"

validate_docs_manual:
  stage: build
  extends: .install_docs_validator
  script:
    - |
      FAIL_FLAG=""
      if [ "$FAIL_ON_ERROR" = "true" ]; then
        FAIL_FLAG="--fail-on-error"
      fi
      docs-validator scan "$TARGET_PATH" --validate $FAIL_FLAG --report markdown --output docs-validation-report.md
  artifacts:
    paths:
      - docs-validation-report.md
    expire_in: 1 week
    when: always
  variables:
    TARGET_PATH: "."
    FAIL_ON_ERROR: "true"
  when: manual
  rules:
    - when: always
```

### Step 2: Verify Execution
1. Commit and push the changes to your repository
2. Navigate to CI/CD → Pipelines in GitLab
3. If broken links are found, the `validate_docs` job will fail
4. Download the `docs-validation-report.md` from the job's artifacts to see the detailed breakdown

### Step 3: Manual Execution
1. Navigate to CI/CD → Pipelines
2. Find the pipeline for your branch
3. Click the Play button next to `validate_docs_manual` job
4. Optionally modify variables before starting:
   - `TARGET_PATH` - path to scan (default: `.`)
   - `FAIL_ON_ERROR` - fail pipeline on errors (default: `true`)
5. The report will be available in job artifacts regardless of success/failure