# Mermaid Class Diagram Authoring Map

This meta-model uses a Mermaid `classDiagram` to show the main elements available when authoring Mermaid class diagrams.

```mermaid
---
title: Mermaid Class Diagram Authoring Meta-model
---
classDiagram
    direction LR

    class ClassDiagramSource {
        +String direction
        +bool hideEmptyMembersBox
        +render() SVG
    }

    class ClassDefinition {
        +String id
        +String label
        +List~Member~ members
    }

    class Member {
        +Visibility visibility
        +String name
        +String type
        +MemberKind kind
        +Classifier classifier
    }

    class Visibility {
        <<enumeration>>
        PUBLIC
        PRIVATE
        PROTECTED
        PACKAGE_INTERNAL
    }

    class MemberKind {
        <<enumeration>>
        ATTRIBUTE
        METHOD
    }

    class Classifier {
        <<enumeration>>
        INSTANCE
        STATIC
        ABSTRACT
    }

    class Annotation {
        <<enumeration>>
        INTERFACE
        ABSTRACT
        SERVICE
        ENUMERATION
    }

    class Relationship {
        +RelationType type
        +String label
        +String sourceMultiplicity
        +String targetMultiplicity
    }

    class RelationType {
        <<enumeration>>
        INHERITANCE
        COMPOSITION
        AGGREGATION
        ASSOCIATION
        DEPENDENCY
        REALIZATION
        SOLID_LINK
        DASHED_LINK
    }

    class Namespace {
        +String name
        +String displayLabel
        +List~Namespace~ children
    }

    class Note {
        +String text
    }

    class StyleDefinition {
        +String className
        +String declarations
    }

    class Interaction {
        +String action
        +String reference
        +String tooltip
    }

    ClassDiagramSource "1" *-- "*" ClassDefinition : declares
    ClassDefinition "1" *-- "*" Member : owns
    Member --> Visibility : uses
    Member --> MemberKind : distinguishes
    Member --> Classifier : qualifies
    ClassDefinition "1" o-- "*" Annotation : describes

    ClassDiagramSource "1" *-- "*" Relationship : connects
    Relationship "*" --> "2" ClassDefinition : endpoints
    Relationship --> RelationType : selects

    ClassDiagramSource "1" o-- "*" Namespace : groups
    Namespace "1" o-- "*" ClassDefinition : contains
    Namespace "1" o-- "*" Namespace : nests

    ClassDiagramSource o-- Note : documents
    Note ..> ClassDefinition : may target
    ClassDiagramSource o-- StyleDefinition : presents
    StyleDefinition ..> ClassDefinition : applies to
    ClassDiagramSource o-- Interaction : enables
    Interaction ..> ClassDefinition : binds to

    note for Namespace "Display labels and nested namespaces are supported in Mermaid 11.15+"
    note for Interaction "Links and callbacks require a compatible security level"

    classDef root fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e
    classDef model fill:#ede9fe,stroke:#7c3aed,color:#4c1d95
    classDef relation fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef support fill:#fff7ed,stroke:#ea580c,color:#7c2d12

    cssClass "ClassDiagramSource" root
    cssClass "ClassDefinition,Member,Visibility,MemberKind,Classifier,Annotation" model
    cssClass "Relationship,RelationType,Namespace" relation
    cssClass "Note,StyleDefinition,Interaction" support
```

## Relationship notation

| Meaning | Mermaid notation |
|---|---|
| Inheritance | `<\|--` |
| Composition | `*--` |
| Aggregation | `o--` |
| Association | `-->` |
| Dependency | `..>` |
| Realization | `..\|>` |
| Solid link | `--` |
| Dashed link | `..` |

Visibility prefixes are `+` public, `-` private, `#` protected, and `~` package/internal. Methods contain parentheses; attributes do not. Static members end with `$`, while abstract methods end with `*`.
