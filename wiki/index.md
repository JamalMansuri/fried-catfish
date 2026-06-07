---
id: index
title: Catfish — Codebase Map of Content
type: moc
---

# Catfish — Codebase Map of Content

A **logic map** of the repo, organized by capability (what the code does), not file tree. Each node is a module-level capability; edges are `depends-on`. Open this folder in VS Code with the **Foam** extension for the interactive graph (the static graph below renders anywhere).

**Two layers:** this is the *engineer* dependency view. The *PM* business-capability view is in [[business]].

## Dependency graph

```mermaid
%%{init: {"theme": "base", "themeVariables": {"fontFamily": "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace", "fontSize": "14px", "primaryColor": "#1e293b", "primaryTextColor": "#e2e8f0", "primaryBorderColor": "#475569", "lineColor": "#64748b", "secondaryColor": "#334155", "tertiaryColor": "#0f172a", "edgeLabelBackground": "#0f172a"}, "flowchart": {"curve": "basis", "nodeSpacing": 45, "rankSpacing": 60, "padding": 8}}}%%
graph LR
  catfish([catfish])
  catfish-__main__([__main__])
  catfish-card([card])
  catfish-codemap([codemap])
  catfish-cognition([cognition])
  catfish-fixtures([fixtures])
  catfish-gate([gate])
  catfish-knowledge([knowledge])
  catfish-linear([linear])
  catfish-llm([llm])
  catfish-mcp_server([mcp_server])
  catfish-mcp_tools([mcp_tools])
  catfish-memory([memory])
  catfish-mermaid_theme([mermaid_theme])
  catfish-models([models])
  catfish-personas([personas])
  catfish-retro([retro])
  catfish-server([server])
  catfish-tournament([tournament])
  catfish-tournament_view([tournament_view])
  catfish-__main__ --> catfish-server
  catfish-card --> catfish-models
  catfish-codemap --> catfish-mermaid_theme
  catfish-cognition --> catfish-mermaid_theme
  catfish-knowledge --> catfish-models
  catfish-linear --> catfish-card
  catfish-linear --> catfish-models
  catfish-llm --> catfish-fixtures
  catfish-mcp_server --> catfish-mcp_tools
  catfish-mcp_tools --> catfish-card
  catfish-mcp_tools --> catfish-knowledge
  catfish-mcp_tools --> catfish-linear
  catfish-mcp_tools --> catfish-llm
  catfish-mcp_tools --> catfish-personas
  catfish-mcp_tools --> catfish-retro
  catfish-mcp_tools --> catfish-tournament
  catfish-personas --> catfish-models
  catfish-retro --> catfish-card
  catfish-retro --> catfish-knowledge
  catfish-retro --> catfish-models
  catfish-server --> catfish-card
  catfish-server --> catfish-codemap
  catfish-server --> catfish-cognition
  catfish-server --> catfish-knowledge
  catfish-server --> catfish-linear
  catfish-server --> catfish-llm
  catfish-server --> catfish-mcp_server
  catfish-server --> catfish-memory
  catfish-server --> catfish-personas
  catfish-server --> catfish-retro
  catfish-server --> catfish-tournament
  catfish-server --> catfish-tournament_view
  catfish-tournament --> catfish-cognition
  catfish-tournament --> catfish-llm
  catfish-tournament --> catfish-models
  catfish-tournament --> catfish-personas
classDef engine fill:#155e75,stroke:#22d3ee,stroke-width:1.5px,color:#ecfeff;
classDef io fill:#334155,stroke:#64748b,stroke-width:1px,color:#e2e8f0;
classDef accent fill:#b45309,stroke:#fbbf24,stroke-width:1.5px,color:#fffbeb;
classDef gate fill:#7f1d1d,stroke:#fbbf24,stroke-width:2px,color:#fff7ed;
classDef good fill:#166534,stroke:#4ade80,stroke-width:1.5px,color:#f0fdf4;
  class catfish-gate accent
  class catfish,catfish-__main__,catfish-card,catfish-codemap,catfish-cognition,catfish-fixtures,catfish-knowledge,catfish-linear,catfish-llm,catfish-mcp_server,catfish-mcp_tools,catfish-memory,catfish-mermaid_theme,catfish-models,catfish-personas,catfish-retro,catfish-server,catfish-tournament,catfish-tournament_view io
```

## Capabilities (by load-bearing rank)

- [[catfish-models]] — Shared data models for Catfish. _(used by 6)_
- [[catfish-card]] — Decision cards: build from a tournament result, enforce terseness, render, gate. _(used by 4)_
- [[catfish-knowledge]] — Ingest -> normalized markdown -> Map of Content -> JSONL spine. _(used by 3)_
- [[catfish-llm]] — Inference layer. _(used by 3)_
- [[catfish-personas]] — Personas = reusable lenses. Each stamps a perspective-map: a filtered, typed view over the _(used by 3)_
- [[catfish-cognition]] — The cognitive architecture, as plain markdown. _(used by 2)_
- [[catfish-linear]] — Gated Linear write-back: parent issue -> story children -> sub-issues, by recursive parentId. _(used by 2)_
- [[catfish-mermaid_theme]] — Shared mermaid theming for the generated diagrams (codemap wiki + cognition MoC). _(used by 2)_
- [[catfish-retro]] — Decision ledger + retrospective capture. _(used by 2)_
- [[catfish-tournament]] — The tournament engine: generate -> reflect -> rank -> evolve -> meta-review. _(used by 2)_
- [[catfish-codemap]] — Logic-based Map of Content for a codebase, emitted as a Foam-compatible wiki. _(used by 1)_
- [[catfish-fixtures]] — Recorded demo fixtures — "Where should we grab lunch today?" _(used by 1)_
- [[catfish-mcp_server]] — MCP stdio server (the [mcp] extra). Exposes the catfish tools to Claude Code / Codex. _(used by 1)_
- [[catfish-mcp_tools]] — Tool implementations behind the MCP server. _(used by 1)_
- [[catfish-memory]] — Markdown session memory + handoff notes. _(used by 1)_
- [[catfish-server]] — CLI dispatcher + MCP server entry point. _(used by 1)_
- [[catfish-tournament_view]] — Render the tournament itself — the generate → critique → battle → score story the engine _(used by 1)_
- [[catfish]] — Catfish — stress-test plans in a tournament, decide in one card. _(used by 0)_
- [[catfish-__main__]] — catfish.__main__ _(used by 0)_
- [[catfish-gate]] — PreToolUse gate hook (Claude Code). _(used by 0) ⚙️ entry_

---
_Structure is extracted deterministically (stdlib `ast`). Business-value lines are **proposals**, not facts — confirm them. Catfish mapped itself with `catfish map src`._
