# Code Walkthrough Workflow

This workflow describes how a code walkthrough moves from a requested feature, behavior, symbol, or file to an evidence-backed execution narrative.

```mermaid
flowchart LR
    request["Walkthrough request<br/>Feature, behavior, symbol, or file"]
    target["Resolve target<br/>Interpret intent and scope"]
    entry["Verify entry point<br/>Trigger, symbol, input, and line"]
    chain["Read call chain<br/>Inspect each relevant implementation"]
    trace["Trace behavior<br/>Data, branches, side effects, and errors"]
    check{"Evidence complete?"}
    inspect["Inspect more source<br/>Configuration, callers, tests, or adapters"]
    output["Verified walkthrough<br/>Ordered flow with source references"]

    request --> target --> entry --> chain --> trace --> check
    check -- "Yes" --> output
    check -- "No" --> inspect --> chain

    classDef requestNode fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e
    classDef analysisNode fill:#ede9fe,stroke:#7c3aed,color:#4c1d95
    classDef decisionNode fill:#fff7ed,stroke:#ea580c,color:#7c2d12
    classDef outputNode fill:#dcfce7,stroke:#16a34a,color:#14532d

    class request requestNode
    class target,entry,chain,trace,inspect analysisNode
    class check decisionNode
    class output outputNode
```

The trace records, where applicable:

- who calls each stage and what it calls next;
- inputs, outputs, and data transformations;
- validation, branching, and early returns;
- external calls, state changes, side effects, and exceptions.

Missing links return to source inspection. They are never filled with assumptions.
