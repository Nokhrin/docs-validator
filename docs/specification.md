# Documentation Connectivity Static Analyzer Specification

## Problem Statement
Documentation repositories frequently suffer from structural degradation over time:
- Links point to deleted files, renamed directories, or non-existent anchors.
- Files become "orphans" (isolated pages with no incoming links), making them undiscoverable.
- Cross-references become outdated after section refactoring.
- Circular dependencies create confusing navigation loops.
This fragmentation degrades the user experience and increases maintenance overhead.

## Solution
`docs-validator` is a Python-based CLI tool that performs static analysis of documentation repositories. It:
- Recursively scans `.md` and `.markdown` files for internal and external links.
- Builds a directed connectivity graph of the documentation structure.
- Applies a set of validation rules to detect broken links, orphaned files, missing anchors, and circular dependencies.
- Generates structured reports (CLI, Markdown, HTML, JSON) suitable for CI/CD integration.

## System Architecture

The system is organized into distinct logical layers, corresponding to the `src/validator/` directory structure.

### 1. Core Engine (`src/validator/core/`)
Responsible for data representation, file discovery, and structural analysis.
- Data Models (`models.py`): Defines immutable and mutable data structures: `Link`, `DocumentationFile`, `ValidationIssue`, `ValidationResult`, `LinkStatistics`, and enumerations (`LinkType`, `SeverityLevel`, `IssueType`).
- File Discovery (`explorer.py`): `FilesExplorer` class performs recursive directory traversal, filtering by allowed extensions (`.md`, `.markdown`) and applying exclusion patterns (e.g., `.git`, `node_modules`, `.venv`).
- Link Extraction (`extractor.py`): `LinkExtractor` uses regular expressions to parse Markdown syntax (`[text](url)` and `![alt](url)`), determining the `LinkType` (INTERNAL, EXTERNAL, ANCHOR, IMAGE) and isolating anchor fragments.
- Graph Analysis (`connectivity_graph.py`): `ConnectivityGraph` utilizes `networkx.DiGraph` to model file dependencies. It provides methods to identify orphaned nodes (`get_orphans`), unreachable subgraphs (`get_unreachable`), and cyclic dependencies (`get_simple_cycles`).
- MkDocs Integration (`mkdocs_parser.py`): Parses `mkdocs.yml` to extract navigation roots, ensuring that files listed in the site navigation are not falsely flagged as orphans.

### 2. Validation Rules (`src/validator/rules/`)
Implements the `BaseValidator` interface. Each validator operates on the populated `DocumentationFile` dictionary and the root directory path.
- `BrokenLinkValidator`: Resolves relative paths and verifies `Path.exists()` for all `INTERNAL` links.
- `OrphanFileValidator`: Identifies files with zero incoming links (`in_degree == 0`), explicitly excluding standard root files (`README.md`, `index.md`) and paths defined in `mkdocs.yml`.
- `AnchorLinkValidator`: Extracts Markdown headers (`^(#{1,6})\s+(.+)$`), normalizes them to standard anchor formats (lowercase, spaces to hyphens, stripping special characters), and verifies their existence against `ANCHOR` link targets.
- `CircularDependencyValidator`: Leverages `ConnectivityGraph.get_simple_cycles()` to detect and report files participating in reference loops.
- `ExternalLinkValidator`: Validates `EXTERNAL` links using `requests.Session` with configurable timeouts. It employs `ThreadPoolExecutor` for concurrent checking and supports a `hosts_to_ignore` allowlist to bypass local or known-unreliable domains.

ls### 3. Reporting Layer (`src/validator/reporters/`)
Implements the `BaseReporter` interface to format `ValidationResult` data.
- `CLIReporter`: Outputs a colorized, tabular summary to `stdout`/`stderr` for immediate developer feedback.
- `MarkdownReporter`: Generates a structured Markdown document suitable for committing to the repository or posting as a PR comment.
- `HTMLReporter`: Produces a standalone, styled HTML file with navigation, summary statistics, detailed issue breakdowns, and optional full file-link mapping.
- `JSONReporter`: Serializes the validation state using a custom `DataclassEncoder` for programmatic consumption by external tools or dashboards.

### 4. Orchestration & Configuration (`src/validator/`)
- Configuration Management (`config.py`): Defines the `ValidatorConfig` dataclass. Handles loading defaults, parsing `.docs-validator.toml` files, and merging CLI arguments with file-based settings.
- Execution Pipeline (`pipeline.py`): The central orchestrator (`run_validation`). It sequences the operations: configuration loading -> file exploration -> link collection -> rule validation -> statistics aggregation -> exit code determination.
- CLI Entry Point (`cli.py`): Parses `sys.argv` using `argparse`, initializes logging, invokes the pipeline, and triggers the appropriate reporter based on the `--report` flag.

## Key Technical Constraints & Behaviors
1. Path Resolution: All internal link targets are resolved relative to the directory of the source file containing the link, not the execution root.
2. Concurrency: External link validation is the only operation that utilizes multithreading (`ThreadPoolExecutor`), bounded by `max_threads_number` to prevent resource exhaustion.
3. Graceful Degradation: I/O errors (e.g., unreadable files) are logged as warnings/errors but do not crash the entire validation pipeline.
4. Extensibility: New validation rules can be added by subclassing `BaseValidator` and registering the class in the `pipeline.py` validator list.