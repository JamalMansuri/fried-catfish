"""Shared mermaid theming for the generated diagrams (codemap wiki + cognition MoC).

GitHub renders mermaid from `init` directives + `classDef` only — no external CSS/JS — so the
palette lives here as a reusable init block + node-role classes, and the generators stay the
single place that styles every diagram. Dark, modern, and cohesive with the demo's terminal
colors (cyan + amber on slate); the fills are mid-tone with light text so they stay legible on
both GitHub light and dark backgrounds.

The init directive is built from a dict via `json.dumps` so the JSON is always valid (no
hand-counting the `%%{init: {...}}%%` braces).
"""
from __future__ import annotations

import json

_CONFIG = {
    "theme": "base",
    "themeVariables": {
        "fontFamily": "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
        "fontSize": "14px",
        "primaryColor": "#1e293b",        # default node fill (slate)
        "primaryTextColor": "#e2e8f0",    # default node text (light)
        "primaryBorderColor": "#475569",
        "lineColor": "#64748b",           # edges — slate-500, visible on light + dark
        "secondaryColor": "#334155",
        "tertiaryColor": "#0f172a",
        "edgeLabelBackground": "#0f172a", # edge labels sit on dark so they read either way
    },
    "flowchart": {"curve": "basis", "nodeSpacing": 45, "rankSpacing": 60, "padding": 8},
}

# First line inside every ```mermaid block.
INIT = "%%{init: " + json.dumps(_CONFIG) + "}%%"

# Reusable node-role classes. Assign with `class id1,id2 <role>`.
CLASSDEFS = [
    "classDef engine fill:#155e75,stroke:#22d3ee,stroke-width:1.5px,color:#ecfeff;",  # cyan — the loop / value buckets
    "classDef io fill:#334155,stroke:#64748b,stroke-width:1px,color:#e2e8f0;",        # slate — inputs / outputs / modules
    "classDef accent fill:#b45309,stroke:#fbbf24,stroke-width:1.5px,color:#fffbeb;",  # amber — load-bearing / actor / entrypoint
    "classDef gate fill:#7f1d1d,stroke:#fbbf24,stroke-width:2px,color:#fff7ed;",      # the human gate (the product's spine)
    "classDef good fill:#166534,stroke:#4ade80,stroke-width:1.5px,color:#f0fdf4;",    # green — the gated write
]


def block(body: list[str], classes: list[str] | None = None) -> str:
    """Wrap graph lines into a themed ```mermaid fenced block.

    `body` is the graph header + nodes + edges (e.g. `["graph TD", "  A --> B"]`), no fences.
    `classes` is a list of `class <ids> <role>` assignment lines (empty ones are dropped).
    """
    lines = ["```mermaid", INIT, *body, *CLASSDEFS]
    lines += [c for c in (classes or []) if c and c.strip()]
    lines.append("```")
    return "\n".join(lines)
