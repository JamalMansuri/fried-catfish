---
name: map
description: Map a codebase by what it does — a capability/business-value logic map, not a file tree. Trigger when the user wants to understand a repo at a glance, explain a codebase to a PM, see which modules are load-bearing, or asks "map this codebase", "what does this repo do", or "show me the architecture by capability".
---

# Catfish map

Turn a codebase into a logic Map of Content — organized by capability and flow, with a one-line business-value translation per capability.

## Steps
1. Run: `catfish map <src-dir>` (default output: `wiki/`).
2. Report the most load-bearing capabilities — the command prints the top few by reference count — and where to view the graph: `wiki/index.md` (Mermaid renders on GitHub) or the folder in VS Code with the Foam extension for the live graph.
3. If the user wants the PM view, point them at `wiki/business.md` (the capability → business-value graph).

## Guardrails
- Structure is extracted deterministically (`ast` / ripgrep in core; tree-sitter in the optional `[code]` extra). The business-value lines are **proposals the human confirms** — never assert them as fact.
- This maps structure, not correctness.
