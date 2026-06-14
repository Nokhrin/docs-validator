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
- Link Extraction (`extractor.py`, `asciidoc_extractor.py`): 
  - `LinkExtractor` uses regular expressions to parse Markdown syntax (`[text](url)` and `![alt](url)`), determining the `LinkType` (INTERNAL, EXTERNAL, ANCHOR, IMAGE) and isolating anchor fragments.
  - `AsciiDocLinkExtractor` parses AsciiDoc syntax including link macros (`link:target[text]`), cross-references (`<<anchor>>`), image macros (`image:target[alt]`), and bare URLs.

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

---

## Known Limitations

The following limitations are acknowledged and documented for transparency.  
They are not considered critical issues and will be addressed based on community feedback and resource availability.

### 1. AsciiDoc Support

Impact: Medium  
Current State: Basic support via regex-based extraction  
Limitations:
- Only basic AsciiDoc constructs are supported (link macros, cross-references, image macros, bare URLs)
- Complex AsciiDoc features (conditional includes, attribute substitutions, complex macros) are not parsed
- Anchor validation for AsciiDoc files is not implemented

Rationale: Full AsciiDoc parsing would require integration with `asciidoctor` or similar libraries, 
significantly increasing dependencies and complexity. 
The current regex-based approach covers ~80% of common use cases.

Mitigation: Users can disable AsciiDoc file scanning via `exclude_patterns` if needed.

### 2. External Link Validation Accuracy

Impact: Low  
Current State: Conservative classification with manual verification fallback  
Limitations:
- Some HTTP status codes (403, 503, 5xx) are classified as WARNING instead of ERROR due to potential WAF/bot blocking
- JavaScript-rendered pages may return false positives (content not available in initial HTML response)
- Rate limiting by external services may cause temporary failures

Rationale: Aggressive classification of ambiguous status codes as ERROR would generate excessive false positives, 
reducing trust in validation results. 
The WARNING classification with "manual verification required" message provides actionable feedback without blocking CI/CD pipelines.

Mitigation: Users can add problematic domains to `hosts_to_ignore` configuration.

### 3. Anchor Validation Scope

Impact: Low  
Current State: Markdown headers only  
Limitations:
- HTML anchor tags (`<a id="...">`, `<a name="...">`) in Markdown files are not detected
- AsciiDoc anchor validation is not implemented
- GitHub/GitLab-specific anchor generation rules (underscores, special characters) may not match exactly

Rationale: Full HTML parsing within Markdown files would require additional dependencies (BeautifulSoup) and significantly increase processing time. 
The current implementation covers the most common case (Markdown headers).

Mitigation: Users can disable anchor validation for external links via `validate_external_anchors = false`.

### 4. Performance with Large Repositories

Impact: Low  
Current State: Sequential processing for internal links, concurrent for external  
Limitations:
- Internal link validation is single-threaded
- No caching of external link validation results between runs
- Large repositories (>10,000 files) may experience slow validation times

Rationale: The tool is designed for CI/CD integration where validation runs on changed files only. 
Full repository validation is typically performed during initial setup or periodic audits.

Mitigation: Use `exclude_patterns` to skip non-documentation directories. 
Increase `external_timeout_sec` for slow external resources.

### 5. Report Format Limitations

Impact: Low  
Current State: CLI, Markdown, HTML, JSON formats  
Limitations:
- HTML report does not include interactive filtering or sorting
- JSON report does not include full file content (only metadata)
- No support for custom report templates

Rationale: The current report formats cover the most common use cases. 
Custom templates would require significant architectural changes.

Mitigation: Users can post-process JSON reports for custom analysis.