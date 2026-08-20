# Contributor Diagram Catalog

This reference catalogs the diagram-authoring and code-analysis artifacts used by contributors. For diagrams of the Coding Tutor product itself, see [Architecture](../ARCHITECTURE.md).

> [!NOTE]
> The Markdown (`.md`) and Mermaid (`.mmd`) files are the human-readable canonical documentation. The JSON files are companion specifications for Archify. Interactive HTML files are generated artifacts: do not edit them by hand. GitHub may download or display their source instead of running them, so download and open them locally when needed.

| Diagram | Purpose | Source | Interactive HTML | Archify JSON |
| --- | --- | --- | --- | --- |
| Mermaid flowchart authoring | Nodes, edges, subgraphs, direction, and styling. | [Source](mermaid-flowchart-authoring.md) | [HTML](mermaid-flowchart-authoring.html) | [JSON](mermaid-flowchart-authoring.workflow.json) |
| Mermaid class diagram authoring | Classes, members, relationships, namespaces, and cardinality. | [Source](mermaid-class-diagram-authoring.md) | [HTML](mermaid-class-diagram-authoring.html) | [JSON](mermaid-class-diagram-authoring.workflow.json) |
| Mermaid ER diagram authoring | Entities, attributes, keys, relationships, and cardinality. | [Source](mermaid-er-diagram-authoring.md) | [HTML](mermaid-er-diagram-authoring.html) | [JSON](mermaid-er-diagram-authoring.workflow.json) |
| Mermaid state diagram authoring | States, transitions, composite states, choices, and concurrency. | [Source](mermaid-state-diagram-authoring.md) | [HTML](mermaid-state-diagram-authoring.html) | [JSON](mermaid-state-diagram-authoring.lifecycle.json) |
| Mermaid mindmap authoring | Hierarchies, shapes, icons, classes, and layout. | [Source](mermaid-mindmap-authoring.md) | [HTML](mermaid-mindmap-authoring.html) | [JSON](mermaid-mindmap-authoring.architecture.json) |
| Mermaid block diagram authoring | Fixed-layout blocks, composite blocks, connectors, and styling. | [Source](mermaid-block-diagram-authoring.md) | [HTML](mermaid-block-diagram-authoring.html) | [JSON](mermaid-block-diagram-authoring.architecture.json) |
| Mermaid architecture diagram authoring | Groups, services, ports, junctions, and alignment. | [Source](mermaid-architecture-diagram-authoring.md) | [HTML](mermaid-architecture-diagram-authoring.html) | [JSON](mermaid-architecture-diagram-authoring.architecture.json) |
| Mermaid ZenUML authoring | Participants, messages, nesting, and control fragments. | [Source](mermaid-zenuml-authoring.md) | [HTML](mermaid-zenuml-authoring.html) | [JSON](mermaid-zenuml-authoring.sequence.json) |
| Code walkthrough workflow | Evidence-based tracing from an entry point through the execution path. | [Source](code-walkthrough-skill.mmd) | [HTML](code-walkthrough-skill.html) | [JSON](code-walkthrough-skill.workflow.json) |
| Mermaid diagram production playbook | Diagram creation, validation, correction, and artifact handling. | [Source](mermaid-diagram-production-playbook.mmd) | [HTML](mermaid-diagram-production-playbook.html) | [JSON](mermaid-diagram-production-playbook.workflow.json) |
| Architecture diagram generator | Evidence-driven selection and generation of codebase architecture diagrams. | [Source](architecture-diagram-generator.mmd) | [HTML](architecture-diagram-generator.html) | [JSON](architecture-diagram-generator.workflow.json) |

Earlier variants remain available in the [archive](archive/README.md) for provenance.

## Maintenance

When updating a diagram:

1. Edit the canonical Markdown or Mermaid source.
2. Update its Archify JSON companion when the modeled structure changes.
3. Regenerate the HTML artifact instead of editing generated HTML.
4. Validate both the Mermaid source and Archify specification before committing.

This catalog is contributor-facing reference documentation; it is not part of the application runtime.
