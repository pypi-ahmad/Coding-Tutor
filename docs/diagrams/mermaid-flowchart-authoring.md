# Mermaid Flowchart Authoring Map

This diagram condenses Mermaid flowchart syntax into an authoring path and a small set of reference groups.

```mermaid
---
title: Mermaid Flowchart Authoring Map
---
flowchart TD
    Start(["Declare flowchart or graph"])
    Direction["Choose direction<br/>TB · TD · BT · RL · LR"]
    Nodes["Define nodes<br/>Stable IDs · quoted labels · semantic shapes"]
    Edges["Connect nodes<br/>Arrow · open · dotted · thick · circle · cross"]
    Groups["Compose subgraphs<br/>Group related topology"]
    Style["Apply presentation<br/>classDef · linkStyle · curve configuration"]
    Interaction["Add optional interaction<br/>Links · callbacks · tooltips"]
    Render((("Render")))

    Start --> Direction --> Nodes --> Edges --> Groups --> Style --> Interaction --> Render

    subgraph ShapeReference["Semantic shape vocabulary"]
        direction LR
        Process["Process"]
        Decision{"Decision"}
        Database[("Database")]
        Event(["Event"])
        Document["Document / storage"]
        Modern["Expanded metadata shapes<br/>Mermaid v11.3+"]
    end

    subgraph EdgeReference["Relationship controls"]
        direction LR
        Labels["Edge labels"]
        Length["Extra dashes<br/>minimum rank"]
        EdgeIDs["Edge IDs<br/>animation and curves<br/>v11.10+"]
    end

    subgraph Guardrails["Parser guardrails"]
        direction LR
        EndRule["Capitalize an End node label"]
        OXRule["Space or capitalize o/x after a link"]
        QuoteRule["Quote syntax-sensitive labels"]
        CommentRule["Place %% comments on their own lines"]
    end

    Nodes -.-> ShapeReference
    Edges -.-> EdgeReference
    Render -.-> Guardrails

    classDef foundation fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e
    classDef topology fill:#ede9fe,stroke:#7c3aed,color:#4c1d95
    classDef composition fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef warning fill:#fff7ed,stroke:#ea580c,color:#7c2d12
    classDef reference fill:#f8fafc,stroke:#64748b,color:#0f172a

    class Start,Direction foundation
    class Nodes,Edges topology
    class Groups,Style,Interaction,Render composition
    class EndRule,OXRule,QuoteRule,CommentRule warning
    class Process,Decision,Database,Event,Document,Modern,Labels,Length,EdgeIDs reference
```

## Selection guide

- Use node shapes to communicate meaning, not decoration.
- Use labeled edges only when the relationship is not already obvious.
- Use subgraphs for real boundaries or conceptual groupings.
- Prefer `classDef` for reusable styling.
- Use ELK for larger diagrams when the hosting Mermaid version supports it.
