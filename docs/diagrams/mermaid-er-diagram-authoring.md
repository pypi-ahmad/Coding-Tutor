# Mermaid Entity-Relationship Diagram Authoring Map

This Mermaid `erDiagram` models the pieces used to define another ER diagram: entities, attributes, relationships, endpoints, subgraphs, and reusable styles.

```mermaid
---
title: Mermaid ER Diagram Authoring Meta-model
---
erDiagram
    direction LR

    ER_DIAGRAM ||--o{ ENTITY : declares
    ENTITY ||--o{ ATTRIBUTE : contains

    ER_DIAGRAM ||--o{ RELATIONSHIP : defines
    RELATIONSHIP ||--|{ RELATIONSHIP_ENDPOINT : has
    RELATIONSHIP_ENDPOINT }o--|| ENTITY : references

    ER_DIAGRAM ||--o{ SUBGRAPH_DEF : groups
    SUBGRAPH_DEF o|--o{ SUBGRAPH_DEF : nests
    SUBGRAPH_DEF o|--o{ ENTITY : contains

    ER_DIAGRAM ||--o{ STYLE_CLASS : defines
    STYLE_CLASS }o..o{ ENTITY : applies-to

    ER_DIAGRAM {
        string direction
        string layout
    }

    ENTITY {
        string id PK
        string alias
    }

    ATTRIBUTE {
        string type
        string name
        string key "PK, FK, UK, or combinations"
        string? comment "Optional type syntax requires Mermaid 11.16+"
    }

    RELATIONSHIP {
        string label
        boolean identifying "Solid when true, dashed when false"
        int endpointCount "Must equal two"
    }

    RELATIONSHIP_ENDPOINT {
        string minimum "zero or one"
        string maximum "one or many"
    }

    SUBGRAPH_DEF {
        string id PK
        string title
        string direction
    }

    STYLE_CLASS {
        string name PK
        string declarations
    }

    classDef root fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e
    classDef domain fill:#ede9fe,stroke:#7c3aed,color:#4c1d95
    classDef relation fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef support fill:#fff7ed,stroke:#ea580c,color:#7c2d12

    class ER_DIAGRAM root
    class ENTITY,ATTRIBUTE domain
    class RELATIONSHIP,RELATIONSHIP_ENDPOINT relation
    class SUBGRAPH_DEF,STYLE_CLASS support
```

## Crow’s-foot endpoint markers

| Cardinality | Left marker | Right marker |
|---|---:|---:|
| Zero or one | `\|o` | `o\|` |
| Exactly one | `\|\|` | `\|\|` |
| Zero or more | `}o` | `o{` |
| One or more | `}\|` | `\|{` |

Use `--` for an identifying relationship and `..` for a non-identifying relationship. Relationship labels describe the association from the first entity’s perspective.

For logical models, foreign-key attributes can be omitted when relationships already communicate the association. Include them when the diagram intentionally represents physical relational tables.
