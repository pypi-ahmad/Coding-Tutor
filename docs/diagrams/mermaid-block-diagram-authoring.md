# Mermaid Block Diagram Authoring Map

This Mermaid `block` diagram demonstrates explicit columns, spans, reserved space, semantic shapes, block arrows, nested composition, edges, and reusable styles.

```mermaid
---
title: Mermaid Block Diagram Authoring Map
---
block
  columns 4

  declaration["block"]
  grid["columns N"]
  span["id:N span"]
  composite["block:ID ... end"]

  space:4

  shape(("Shapes"))
  connector<["Edges"]>(right)
  spacer["space / space:N"]
  styleNode{{"style / classDef"}}

  space:4

  block:System:4
    columns 4
    Frontend["Frontend"]
    request<["request"]>(right)
    Backend["Backend"]
    persist<["persist"]>(down)

    space:2
    Cache[("Cache")]
    Database[("Database")]
  end

  declaration --> grid
  grid --> span
  span --> composite
  Backend --> Cache
  Backend --> Database

  classDef syntax fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e
  classDef feature fill:#ede9fe,stroke:#7c3aed,color:#4c1d95
  classDef service fill:#dcfce7,stroke:#16a34a,color:#14532d
  classDef storage fill:#fff7ed,stroke:#ea580c,color:#7c2d12

  class declaration,grid,span,composite syntax
  class shape,connector,spacer,styleNode feature
  class Frontend,Backend service
  class Cache,Database storage
```

## Authoring guide

- `columns N` establishes the placement grid; declarations fill cells in order.
- `id:N` makes a block occupy `N` columns.
- `block:ID:N ... end` creates a named composite spanning `N` columns.
- `space` reserves one cell; `space:N` reserves several cells.
- Composite blocks can define their own column count independently.
- Block arrows occupy layout cells and communicate direction visually.
- Use normal edges for relationships that should remain explicit beyond placement.
- Prefer classes for repeated styling and `style` for isolated emphasis.

Block diagrams prioritize author-controlled placement. That makes them useful when automatic flowchart layout moves components away from their intended positions.
