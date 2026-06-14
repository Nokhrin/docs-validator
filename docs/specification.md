# Documentation Connectivity Static Analyzer Specification

## Problem Statement & Requirements

### Problem
Documentation repositories accumulate structural issues over time:
- **Broken links**: References to deleted files, renamed directories, or non-existent anchors
- **Orphan files**: Undiscoverable pages with no incoming links
- **Circular dependencies**: Navigation loops that confuse users
- **Missing anchors**: Cross-references to non-existent sections

These issues degrade user experience and increase maintenance overhead.

### Functional Requirements
1. **File Discovery**: Recursive traversal of `.md`, `.markdown`, `.adoc`, `.asc` files with pattern-based exclusions
2. **Link Extraction**: Parse internal links, external URLs, anchors, and images using regex-based extraction
3. **Graph Analysis**: Build directed connectivity graph to detect structural issues
4. **Validation Rules**:
  - Broken link detection (file existence checks)
  - Orphan file identification (zero incoming links)
  - Missing anchor validation (Markdown headers only)
  - Circular dependency detection
  - External link validation (configurable timeout, concurrent checking)
5. **Reporting**: Generate CLI, Markdown, HTML, and JSON reports
6. **CI/CD Integration**: Exit codes for pipeline automation, configuration via TOML

### Constraints
- Python 3.13+
- Support for MkDocs navigation awareness
- Graceful degradation on I/O errors
- Configurable thread pool for external validation

## Solution Overview

### Architecture
The tool implements a four-layer architecture:

1. **Discovery Layer**: Recursively scans documentation directories, filtering by allowed extensions and exclusion patterns (`.git`, `node_modules`, etc.)

2. **Extraction Layer**: Uses regex patterns to parse:
  - Markdown: `\[text\]\(url\)` и `!\[alt\]\(url\)` syntax
  - AsciiDoc: `link:target[text]`, `<<anchor>>`, image macros
  - Classifies links as INTERNAL, EXTERNAL, ANCHOR, or IMAGE

3. **Analysis Layer**:
  - Builds directed graph using NetworkX where nodes represent files and edges represent links
  - Applies validation rules as graph traversals:
    - Orphans: nodes with in-degree = 0 (excluding README.md, index.md, MkDocs nav)
    - Cycles: detects simple cycles via DFS
    - Broken links: resolves relative paths and checks file system existence
  - External validation uses ThreadPoolExecutor with configurable concurrency

4. **Reporting Layer**: Formats validation results as:
  - CLI: Colorized terminal output with summary statistics
  - Markdown/HTML: Structured documents for PR comments or artifacts
  - JSON: Machine-readable format for dashboards

### Workflow
```
Configuration → File Discovery → Link Extraction → Graph Construction →
Rule Validation → Statistics Aggregation → Report Generation → Exit Code
```

### Key Design Decisions
- **Path Resolution**: All internal links resolve relative to source file directory, not execution root
- **Concurrency**: Only external link validation uses multithreading (bounded by `max_threads_number`)
- **Extensibility**: New validators implement `BaseValidator` interface and register in pipeline
- **Graceful Degradation**: I/O errors logged as warnings, don't crash validation

### Known Limitations
- AsciiDoc: Basic regex extraction only (no complex macros or conditional includes)
- Anchors: Markdown headers only (no HTML `<a id>` tags)
- External links: Conservative classification (403/5xx → WARNING, not ERROR) to avoid false positives from WAF/bot blocking
- Performance: Optimized for CI/CD (changed files), not full repository scans (>10k files may be slow)
