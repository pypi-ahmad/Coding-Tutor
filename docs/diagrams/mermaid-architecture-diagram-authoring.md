# Mermaid Architecture Diagram Authoring Map

This diagram summarizes the verified concepts in Mermaid's `architecture-beta` syntax: groups, nested services, port-qualified edges, junctions, alignment constraints, layout configuration, and icon sources.

```mermaid
---
title: Mermaid Architecture Diagram Authoring Map
---
architecture-beta
    group authoring(cloud)[Architecture Model]
    group placement(server)[Layout Controls] in authoring
    group resources(disk)[Icon Resources]

    service groups(cloud)[Groups] in authoring
    service services(server)[Services] in authoring
    junction route_hub in authoring
    service edges(internet)[Edges] in authoring

    service aligner(server)[Alignment] in placement
    service fcose(server)[fCoSE Tuning] in placement

    service builtins(database)[Built-in Icons] in resources
    service custom(disk)[Custom Packs] in resources

    groups:R --> L:services
    services:R --> L:route_hub
    route_hub:R --> L:edges
    aligner:B --> T:fcose
    builtins{group}:T --> B:services{group}
    custom{group}:T --> B:services{group}

    align row groups services route_hub edges
    align column aligner fcose
    align row builtins custom
```

## Syntax map

| Element | Form | Purpose |
|---|---|---|
| Diagram | `architecture-beta` | Starts an architecture diagram. |
| Group | `group id(icon)[Label]` | Creates a visual boundary. Add `in parent` for nesting. |
| Service | `service id(icon)[Label]` | Declares a resource. Add `in group` for membership. |
| Junction | `junction id` | Creates an unlabeled four-way routing point. It may also use `in group`. |
| Edge | `source:R --> L:target` | Connects declared nodes through selected `T`, `B`, `L`, or `R` ports. |
| Cross-group edge | `source{group}:R --> L:target{group}` | Routes an edge through group boundaries adjacent to its services. |
| Alignment | `align row a b` / `align column a b` | Pins services or junctions to a shared axis. |

Identifiers must be declared before another component references them. Group identifiers are not direct edge endpoints; the `{group}` modifier applies only to a service that belongs to a group.

## Edge and alignment rules

- The port letter controls which side an edge leaves or enters.
- Add `>` on the target side, `<` on the source side, or both to express direction.
- Use a junction where multiple routes need a shared split or merge point.
- Use `align row` when peers connect through the same vertical port pair, and `align column` when they connect through the same horizontal port pair.
- Combine row and column constraints for grid layouts. The declared order must not contradict directional edges between aligned members.

## Versioned capabilities

| Mermaid version | Capability |
|---|---|
| 11.1.0+ | `architecture-beta`, groups, services, edges, and junctions. |
| 11.14.0+ | `randomize` configuration. It defaults to `false`. |
| 11.15.0+ | fCoSE tuning through `nodeSeparation`, `idealEdgeLengthMultiplier`, `edgeElasticity`, `numIter`, and deterministic `seed`. |
| 11.16.0+ | `align row` and `align column`, including combined grid constraints. |

Use a nonzero `seed` for reproducible placement. A value of `0` opts out of deterministic seeding. Layout tuning changes spacing and force behavior, but does not resolve every logical-position overlap; alignment constraints are the intended control for repeated peer topology.

## Icons

The built-in icon names are `cloud`, `database`, `disk`, `internet`, and `server`. Custom Iconify or project-specific packs must be registered by the host before using namespaced forms such as `logos:aws-ec2`.

Keep labels concise. If a long single-word label does not fit at a small icon size, shorten the title or increase `iconSize`.
