# Mermaid Mindmap Authoring Map

This Mermaid `mindmap` organizes the syntax and integration concerns around one central concept.

```mermaid
---
title: Mermaid Mindmap Authoring Map
---
mindmap
  root((Mermaid Mindmap))
    Hierarchy
      Indentation defines levels
        Root
        Parent
        Child
        Sibling
      Ambiguous indentation
        Nearest known parent is selected
    Node shapes
      square[Square]
      rounded(Rounded square)
      circle((Circle))
      bang))Bang((
      cloud)Cloud(
      hexagon{{Hexagon}}
      Default shape
    Content
      Unicode ❤
      markdown["`**Markdown** strings
wrap and support *emphasis*`"]
      Multiline labels
    Styling
      Icons
        Experimental integration
        Host registers icon fonts
      Classes
        Triple-colon attachment
        Host supplies CSS classes
    Runtime integration
      Lazy asynchronous rendering
      Bundled from Mermaid 9.4
      Older versions register an external diagram
    Layout
      Default layout
      Tidy tree
        Requires layout registration
```

## Authoring rules

- Indentation is relative: children are indented further than their parent, while siblings align.
- Use a consistent indentation width even though Mermaid can recover some ambiguous outlines.
- Markdown strings support bold, italics, wrapping, multiline text, and Unicode.
- Icon packs and custom CSS classes are host-level integrations, not self-contained diagram features.
- Mindmaps remain experimental; icon integration is specifically identified as unstable.
