# Mermaid State Diagram Authoring Map

This Mermaid `stateDiagram-v2` demonstrates a finite-state authoring lifecycle and the principal behavior constructs available to state diagrams.

```mermaid
---
title: Mermaid State Diagram Authoring Lifecycle
---
stateDiagram-v2
    direction LR

    accTitle: Mermaid state diagram authoring lifecycle
    accDescr: A state model progresses from draft through state and transition definition, then chooses a flat or advanced composite model before presentation and completion.

    [*] --> Draft
    Draft --> StatesDefined : declare states
    StatesDefined --> TransitionsDefined : connect transitions

    state ModelChoice <<choice>>
    TransitionsDefined --> ModelChoice : choose structure
    ModelChoice --> FlatModel : simple
    ModelChoice --> AdvancedModel : nested or parallel

    FlatModel --> Presentation : ready
    AdvancedModel --> Presentation : ready
    Presentation --> Complete : review
    Complete --> [*]

    state AdvancedModel {
        direction TB

        [*] --> BehaviorChoice
        state BehaviorChoice <<choice>>
        BehaviorChoice --> SerialPath : sequential
        BehaviorChoice --> ParallelFork : parallel
        SerialPath --> [*]

        state ParallelFork <<fork>>
        ParallelFork --> WorkerA
        ParallelFork --> WorkerB

        state ParallelJoin <<join>>
        WorkerA --> ParallelJoin
        WorkerB --> ParallelJoin
        ParallelJoin --> [*]

        --

        [*] --> ObserverIdle
        ObserverIdle --> ObserverActive : event
        ObserverActive --> ObserverIdle : reset
    }

    note right of Presentation
        Add direction, notes, comments,
        accessibility text, and classDef styles.
    end note

    note left of AdvancedModel : Internal states remain inside their composite boundary.

    classDef draft fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e
    classDef active fill:#ede9fe,stroke:#7c3aed,color:#4c1d95
    classDef polished fill:#dcfce7,stroke:#16a34a,color:#14532d

    class Draft draft
    class StatesDefined,TransitionsDefined,FlatModel active
    class Presentation,Complete polished
```

## Construct guide

| Construct | Mermaid syntax | Purpose |
|---|---|---|
| Initial or terminal state | `[*]` | Marks entry or completion according to arrow direction |
| Transition | `A --> B : event` | Connects states with an optional event or guard |
| Composite state | `state Name { ... }` | Encapsulates nested states |
| Choice | `state Name <<choice>>` | Selects among guarded paths |
| Fork and join | `<<fork>>`, `<<join>>` | Splits and reunites parallel paths |
| Concurrent regions | `--` | Separates independent regions inside a composite state |

Internal states belonging to different composite states cannot transition directly. Current `classDef` limitations also prevent styling initial/terminal markers and states inside composite states.
