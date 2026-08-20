# Code Walkthrough Generator

The generator accepts a feature, behavior, symbol, endpoint, command, pipeline, or file and produces a source-backed explanation of its real execution path.

```mermaid
flowchart TD
    invoke["/code-walkthrough &lt;target&gt;"]

    subgraph intake["1. Understand the request"]
        classify["Classify the target"]
        kinds["Feature · workflow · endpoint · CLI · job · event<br/>Function · class · module · file · database operation<br/>Authentication · data pipeline · ML/AI/RAG pipeline"]
        classify -. "may describe behavior" .-> kinds
    end

    subgraph discovery["2. Identify and verify the entry point"]
        locate["Locate source and framework wiring"]
        verify["Verify the actual entry point"]
        entryEvidence["Record file path and line<br/>Function or class<br/>Trigger and initial input"]
        locate --> verify --> entryEvidence
    end

    subgraph tracing["3. Trace the execution path"]
        read["Read every relevant implementation"]
        follow["Follow callers and callees"]
        analyze["Analyze each stage"]
        stageEvidence["Purpose · inputs · outputs · transformations<br/>Validation · branches · early returns<br/>External calls · side effects · exceptions"]
        read --> follow --> analyze --> stageEvidence
    end

    complete{"Every link verified?"}
    inspect["Inspect more source<br/>Configuration · adapters · tests · dispatch"]
    output["Comprehensive walkthrough<br/>Ordered execution flow with source references"]

    invoke --> classify --> locate
    entryEvidence --> read
    stageEvidence --> complete
    complete -- "Yes" --> output
    complete -- "No" --> inspect --> read

    rule["Follow the architecture that exists.<br/>Do not impose conventional layers or infer missing behavior."]
    rule -.-> complete

    classDef requestNode fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e
    classDef discoveryNode fill:#ede9fe,stroke:#7c3aed,color:#4c1d95
    classDef evidenceNode fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef decisionNode fill:#fff7ed,stroke:#ea580c,color:#7c2d12
    classDef outputNode fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef ruleNode fill:#fee2e2,stroke:#dc2626,color:#7f1d1d

    class invoke requestNode
    class classify,kinds,locate,verify,read,follow,analyze,inspect discoveryNode
    class entryEvidence,stageEvidence evidenceNode
    class complete decisionNode
    class output outputNode
    class rule ruleNode
```

## Invocation examples

```text
/code-walkthrough authentication flow
/code-walkthrough src/api/payments.ts
/code-walkthrough "what happens when a user submits an order"
/code-walkthrough POST /api/orders
/code-walkthrough processPayment()
```

The walkthrough must be derived from implementation code and verified configuration. Names, comments, documentation, and conventional architecture patterns are not substitutes for reading the actual execution chain.
