# Catfish — agent instructions (Codex / Claude Code)

Catfish runs a plan tournament over ingested context and produces one terse decision card.

## Start here (which doc for what)
- `README.md` — what it is, why, quickstart. **Humans start here.**
- `AGENTS.md` (this file) — how to invoke + the adaptation seams. **An AI starts here.**
- `ADAPTING.md` — retarget Catfish to a new domain/sources, step by step.
- `SPEC.md` — full architecture and design decisions.
- `RESEARCH.md` — the academic grounding behind the method.

## How to invoke
- CLI: `catfish tournament <folder> "<question>"` (add `CATFISH_DEMO=1` for a free offline run).
- MCP: tools are listed by `catfish serve`.

## Adapting Catfish to a new domain (read ADAPTING.md for the full walkthrough)
Catfish is domain-agnostic; ALL domain coupling lives in config, never in `src/`:
1. `config/tags.yaml` — keyword→tag vocabulary (default: software/eng). **Edit first.**
2. `personas/*.yaml` — the critic panel; each `filter.tags_any` MUST match tags from `config/tags.yaml`.
3. `examples/<domain>/` — drop in the user's sources; `examples/biotech/` is a complete retarget to copy.
4. `cognition/*.md` — the loop's stage identities; domain-agnostic, rarely edited.

Run a retarget without copying files into the repo: pass `--config-dir <folder>` (a folder holding
`tags.yaml` + `personas/`) to `catfish ingest` / `catfish tournament`. See `examples/biotech/`.

**If you reach for `src/` to change the domain, you've missed a seam — stop and use the config above.**

## Hard constraints (do not violate)
- **Never call `catfish_write_linear` without an `accepted` card.** The write is gated in code by
  `card.assert_approved()`; do not try to bypass it. On Claude Code a `PreToolUse` hook also blocks it.
- **Never mutate a top-ranked candidate in place.** Evolution only creates new candidates.
- **Card terseness is schema-enforced.** Do not pad card fields; over-cap fields are trimmed.
- **Business-value on code nodes is a human-confirmed proposal**, never asserted as fact.

## Honest limit to surface to users
Catfish outputs stress-tested *options*, not verified *answers*. Bradley-Terry rank = relative
persuasiveness among LLM judges, not truth. The human is the validator.
