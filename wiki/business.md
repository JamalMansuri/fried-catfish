---
id: business
title: Catfish — Business Capability Map
type: moc
---

# Catfish — Business Capability Map

PM-facing view: what each capability is *for*, grouped by the kind of value it protects. Pairs with the engineer view in [[index]]. **Business-value lines are proposals — confirm them.**

## Value flow

```mermaid
graph LR
  user([Stakeholder / PM])
  risk[[Risk]]
  user --> risk
  risk --> catfish-gate(gate)
  enablement[[Enablement]]
  user --> enablement
  enablement --> catfish-models(models)
  enablement --> catfish-card(card)
  enablement --> catfish-knowledge(knowledge)
  enablement --> catfish-llm(llm)
  enablement --> catfish-personas(personas)
  enablement --> catfish-cognition(cognition)
  enablement --> catfish-linear(linear)
  enablement --> catfish-retro(retro)
  enablement --> catfish-tournament(tournament)
  enablement --> catfish-codemap(codemap)
  enablement --> catfish-fixtures(fixtures)
  enablement --> catfish-mcp_server(mcp_server)
  enablement --> catfish-mcp_tools(mcp_tools)
  enablement --> catfish-memory(memory)
  enablement --> catfish-server(server)
  enablement --> catfish-tournament_view(tournament_view)
  enablement --> catfish(catfish)
  enablement --> catfish-__main__(__main__)
```

## Capabilities by value

### Risk
- [[catfish-gate]] — (proposed) PreToolUse gate hook (Claude Code).

### Enablement
- [[catfish-models]] — (proposed) Shared data models for Catfish.
- [[catfish-card]] — (proposed) Decision cards: build from a tournament result, enforce terseness, render, gate.
- [[catfish-knowledge]] — (proposed) Ingest -> normalized markdown -> Map of Content -> JSONL spine.
- [[catfish-llm]] — (proposed) Inference layer.
- [[catfish-personas]] — (proposed) Personas = reusable lenses. Each stamps a perspective-map: a filtered, typed view over the
- [[catfish-cognition]] — (proposed) The cognitive architecture, as plain markdown.
- [[catfish-linear]] — (proposed) Gated Linear write-back: parent issue -> story children -> sub-issues, by recursive parentId.
- [[catfish-retro]] — (proposed) Decision ledger + retrospective capture.
- [[catfish-tournament]] — (proposed) The tournament engine: generate -> reflect -> rank -> evolve -> meta-review.
- [[catfish-codemap]] — (proposed) Logic-based Map of Content for a codebase, emitted as a Foam-compatible wiki.
- [[catfish-fixtures]] — (proposed) Recorded demo fixtures — "Where should we grab lunch today?"
- [[catfish-mcp_server]] — (proposed) MCP stdio server (the [mcp] extra). Exposes the catfish tools to Claude Code / Codex.
- [[catfish-mcp_tools]] — (proposed) Tool implementations behind the MCP server.
- [[catfish-memory]] — (proposed) Markdown session memory + handoff notes.
- [[catfish-server]] — (proposed) CLI dispatcher + MCP server entry point.
- [[catfish-tournament_view]] — (proposed) Render the tournament itself — the generate → critique → battle → score story the engine
- [[catfish]] — (proposed) Catfish — stress-test plans in a tournament, decide in one card.
- [[catfish-__main__]] — (proposed) __main__ capability
