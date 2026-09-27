# Documentation Link Validator Architecture

## Context (C4 Level 1)

```mermaid
flowchart TD
    subgraph external["External Actors"]
        User["Developer / Maintainer"]
        CI["CI/CD Pipeline"]
    end

    subgraph validator_system["Documentation Link Validator"]
        Validator["Documentation Link Validator"]
    end

    subgraph input_data["Input Data"]
        MarkdownRepo["Markdown Documentation Repository"]
    end

    subgraph output_data["Output Data"]
        CLIReport["CLI Report"]
        FileReports["File Reports:<br/>Markdown, HTML, JSON"]
        CIStatus["CI Exit Status"]
    end

    User -->|Maintains| MarkdownRepo
    User -->|Executes locally| Validator
    CI -->|Automated execution| Validator
    MarkdownRepo -->|Source files| Validator
    Validator -->|Console output| CLIReport
    Validator -->|Generated artifacts| FileReports
    Validator -->|Pass/Fail signal| CIStatus

    classDef actor fill:#E3F2FD,stroke:#2E86AB,stroke-width:2px,color:#333
    classDef system fill:#FFF3E0,stroke:#FF9800,stroke-width:2px,color:#333
    classDef data fill:#F3E5F5,stroke:#9C27B0,stroke-width:2px,color:#333
    classDef output fill:#E8F5E9,stroke:#4CAF50,stroke-width:2px,color:#333

    class User,CI actor
    class Validator system
    class MarkdownRepo data
    class CLIReport,FileReports,CIStatus output
```

## Components (C4 Level 3)

```mermaid
flowchart LR
    subgraph core["Core Engine"]
        direction TB

        Explorer["FilesExplorer<br/>File discovery & filtering"]
        Extractor["LinkExtractor<br/>Regex-based link parsing"]
        Graph["ConnectivityGraph<br/>NetworkX dependency graph"]
        MkDocs["MkDocsParser<br/>Navigation root extraction"]

        Explorer --> Extractor --> Graph
        MkDocs -.-> Graph
    end

    subgraph validators["Validation Rules"]
        direction LR

        V1["BrokenLinkValidator"]
        V2["OrphanFileValidator"]
        V3["AnchorLinkValidator"]
        V4["CircularDependencyValidator"]
        V5["ExternalLinkValidator"]
    end

    subgraph reporters["Reporting Layer"]
        direction TB

        R1["CLIReporter"]
        R2["MarkdownReporter"]
        R3["HTMLReporter"]
        R4["JSONReporter"]
    end

    subgraph orchestration["Orchestration & Config"]
        Pipeline["Validation Pipeline"]
        Config["ValidatorConfig"]
    end

    Graph --> V1 & V2 & V3 & V4 & V5
    V1 & V2 & V3 & V4 & V5 --> Pipeline
    Pipeline --> R1 & R2 & R3 & R4

    Config --> Pipeline
    Config -.-> Explorer
    Config -.-> V5

    classDef core fill:#E3F2FD,stroke:#2E86AB,stroke-width:2px,color:#333
    classDef validators fill:#FFF3E0,stroke:#FF9800,stroke-width:2px,color:#333
    classDef reporters fill:#E8F5E9,stroke:#4CAF50,stroke-width:2px,color:#333
    classDef orchestration fill:#F3E5F5,stroke:#9C27B0,stroke-width:2px,color:#333

    class Explorer,Extractor,Graph,MkDocs core
    class V1,V2,V3,V4,V5 validators
    class R1,R2,R3,R4 reporters
    class Pipeline,Config orchestration
```
