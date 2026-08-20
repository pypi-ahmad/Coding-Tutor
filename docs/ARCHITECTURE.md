# Architecture

## Runtime system architecture

```mermaid
flowchart LR
    User["Learner in a browser"]

    subgraph App["Local Streamlit process"]
        Router["app.py<br/>navigation and catalog routing"]
        Coding["Coding"]
        Quiz["Quiz"]
        AIQ["AI Questions"]
        Interview["Interview"]
        Progress["Progress"]
        Documents["PDF / DOCX / TXT parser"]
        Workflows["Domain workflows<br/>generation, evaluation, quiz, interview"]
        Prompts["Version-controlled<br/>Markdown prompts"]
        Providers["Provider registry<br/>and adapters"]
        Validation["Strict response<br/>parsing and validation"]
        DBAccess["DuckDB connections<br/>and migrations"]
        Boundary["Learner code remains text<br/>and is never executed"]
    end

    subgraph Storage["Local persistent storage"]
        Catalogs[("algorithm.duckdb<br/>data_analysis.duckdb<br/>interview.duckdb")]
    end

    subgraph External["External services used only by explicit actions"]
        AIAPIs["Selected provider API<br/>OpenAI · Agnes AI · Google Gemini"]
        Firecrawl["Firecrawl MCP"]
    end

    User <--> Router
    Router --> Coding
    Router --> Quiz
    Router --> AIQ
    Router --> Interview
    Router --> Progress

    Coding --> Workflows
    Quiz --> Workflows
    AIQ --> Workflows
    Interview --> Documents --> Workflows
    Progress --> DBAccess
    Prompts --> Workflows
    Workflows --> Providers
    Workflows <--> DBAccess
    Workflows -. "optional generation research" .-> Firecrawl
    Firecrawl -. "bounded untrusted context" .-> Workflows
    Workflows -.-> Boundary

    Providers --> AIAPIs --> Validation --> Workflows
    DBAccess <--> Catalogs
```

The UI, domain logic, provider adapters, and database connections run in one local Python process. There is no separate API server, worker, message queue, authentication service, or learner-code execution service.

## Explicit AI action lifecycle

```mermaid
sequenceDiagram
    actor User
    participant UI as Streamlit mode
    participant Flow as Domain workflow
    participant DB as Active DuckDB catalog
    participant Web as Firecrawl MCP
    participant Prompt as Markdown prompt loader
    participant Provider as Selected AI provider

    User->>UI: Browse locally or request an AI action
    UI->>Flow: Validated settings and user input
    Flow->>DB: Load question, references, or session state
    DB-->>Flow: Local records

    alt Local-only browsing
        Flow-->>UI: Local question or progress
    else Explicit generation, review, planning, or assessment
        opt Question generation, web enabled, and local context insufficient
            Flow->>Web: Bounded topic query
            Web-->>Flow: Source URLs and clipped excerpts
        end
        Flow->>Prompt: Load and render registered template
        Prompt-->>Flow: Bounded prompt content
        Flow->>Provider: Chat request
        Provider-->>Flow: Response text
        Flow->>Flow: Parse and validate response
        alt Valid response
            Flow->>DB: Persist generated item, attempt, session, or report
            Flow-->>UI: Structured result
        else Provider or validation failure
            Flow-->>UI: Sanitized failure, preserving durable state where possible
        end
    end

    UI-->>User: Render local data or AI-estimated feedback
    Note over User,Provider: Learner code is transmitted as text when required and is never executed by Coding Tutor
```

Typing and local catalog browsing do not contact an external service. Firecrawl is generation context only and never participates in scoring.

## Dataset and catalog data flow

```mermaid
flowchart LR
    HF["Public Hugging Face<br/>coding datasets"]
    GitHub["Approved GitHub<br/>interview sources"]

    DownloadCoding["download_datasets.py"]
    DownloadInterview["download_interview_sources.py<br/>authenticated gh api"]

    RawAlgorithm["Dataset/algorithm_problems"]
    RawAnalysis["Dataset/data_analysis_problems"]
    RawInterview["Dataset/interview_sources/raw"]
    Manifest["Interview manifest<br/>revision, hash, license, ingestion decision"]

    ImportCoding["import_datasets.py"]
    ImportInterview["import_interview_sources.py"]
    ImportSelectedAI["import_user_ai_interview_questions.py"]
    NormalizeAlgorithm["Inspect and normalize<br/>algorithm records"]
    NormalizeAnalysis["Inspect and normalize<br/>data-analysis records"]
    NormalizeInterview["Parse allowed sources,<br/>record provenance, deduplicate"]

    Algorithm[("algorithm.duckdb")]
    Analysis[("data_analysis.duckdb")]
    InterviewDB[("interview.duckdb")]

    CodingRuntime["Coding and Quiz runtime"]
    InterviewRuntime["AI Questions and Interview runtime"]
    ProgressRuntime["Progress runtime"]

    HF --> DownloadCoding
    DownloadCoding --> RawAlgorithm
    DownloadCoding --> RawAnalysis
    GitHub --> DownloadInterview
    DownloadInterview --> RawInterview
    DownloadInterview --> Manifest

    RawAlgorithm --> ImportCoding
    RawAnalysis --> ImportCoding
    RawInterview --> ImportInterview
    RawInterview --> ImportSelectedAI
    Manifest --> ImportInterview
    ImportCoding --> NormalizeAlgorithm --> Algorithm
    ImportCoding --> NormalizeAnalysis --> Analysis
    ImportInterview --> NormalizeInterview
    ImportSelectedAI --> NormalizeInterview
    NormalizeInterview --> InterviewDB

    CodingRuntime <--> Algorithm
    CodingRuntime <--> Analysis
    InterviewRuntime <--> InterviewDB
    ProgressRuntime --> Algorithm
    ProgressRuntime --> Analysis
    ProgressRuntime --> InterviewDB
```

Download and import commands are offline preparation steps. Normal application use reads and writes the three consolidated catalogs rather than querying raw dataset directories.

## Local embedded storage

DuckDB keeps questions, provenance, fixture/expected-result assets, attempts, and quiz state in one file without a database server. Transactional migrations and imports suit a single-user local app. DuckDB is storage for data-analysis exercise context, not an engine for learner SQL: the application does not execute submissions. The trade-off is that the user must protect and back up the file; the app is not designed for concurrent multi-user or public deployment.

## Semantic classification

Import catalog metadata—not the folder name—sets `algorithm` or `data_analysis`. This avoids turning directory layout into product semantics and lets validation expose curated algorithms in Python, JavaScript/TypeScript, Java, and C++ while preserving the shared analytical-asset contract.

## One analytical problem, four expressions

A complete data-analysis task has one schema, deterministic fixture, and expected rows. SQL, Pandas, PySpark, and Polars are alternative authoring forms for that same task. The shared contract makes model feedback comparable, but the app does not execute any form or prove equivalence. Imported SQL sources without fixture/expected rows remain incomplete.

## Curated and generated questions

Curated questions are repeatable and preserve source context. Generated questions add topic/difficulty variety and can provide the complete cross-method data contract. Strict validation rejects malformed output; it cannot prove semantic correctness.

## Provenance and licensing

Dataset name, stable identity, file/revision/index, license, attribution, and import time support deduplication and traceability. Metadata is not legal clearance: users must review current upstream terms, especially mixed-origin or unlicensed cards.

## Why code is not executed

Executing arbitrary learner code safely would require a real isolation boundary with no secrets, database, source-tree, network, or unrestricted filesystem access plus resource limits and cleanup. Those guarantees are difficult to provide reliably on local Windows. The current design avoids that boundary entirely and sends text for static AI review. Its trade-off is fundamental: marks are estimates, not test results.

If execution is ever added, it must be isolated outside Streamlit and separately threat-modeled. The current code contains no runner or sandbox.

## Windows and PySpark trade-offs

Windows 11 is the tested launcher platform. JavaScript/TypeScript, Java, C++, and PySpark appear only as editor and AI-review methods. The project does not install language runtimes, compilers, PySpark, or Spark. Polars is likewise not installed. Users may run code externally in an environment they control, but that is outside Coding Tutor's safety model.
