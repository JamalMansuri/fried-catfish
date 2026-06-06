---
name: scout
description: Research an open question against a folder of notes/emails/docs using parallel sub-agents, then optionally hand the framing into a Catfish decision tournament. Trigger when the user has a messy pile of context and a hard open question, wants a researched briefing before deciding, or says "scout this", "research this before we decide", "dig into X", or "fan out and investigate".
---

# Catfish scout

Decompose an open question, research it in parallel against an ingested corpus, synthesize a terse briefing, and optionally feed the framing into a decision tournament. Scouting *frames* a decision; the tournament *makes* one.

## Steps
1. Identify the source folder and the open question.
2. Build the spine: `catfish ingest <folder>` (prefix `CATFISH_DEMO=1` for the free offline path). This normalizes the corpus into `.catfish/` and prints each note's id, title, and tags.
3. Decompose the question into 3–6 crisp, non-overlapping sub-questions. State them to the user before fanning out.
4. **Fan out — one sub-agent per sub-question, in parallel** (use the host's Task/Agent tool, all in a single batch). Each sub-agent's brief: answer exactly one sub-question using only the ingested notes (read `.catfish/` and the source folder); cite the note ids it relied on; explicitly flag any sub-question the corpus cannot answer. Allow web research per sub-agent **only if the user asks** — the default is corpus-grounded.
5. Synthesize a short briefing from the findings: what we know (with note ids), what's contested, what's missing. Keep it terse — no walls of text.
6. Handoff (optional, ask first): if the briefing surfaces a real decision, sharpen the question and run `catfish tournament <folder> "<sharpened question>"` to turn it into a decision card, then follow the `tournament` skill's gate flow.

## Guardrails
- Sub-agents research; they do not decide. The decision is the tournament's job and the human's call.
- Ground every claim in note ids from the ingested corpus. If the corpus can't answer a sub-question, say so — do not invent.
- A briefing is stress-tested *context*, not a verified answer.
- Never write to Linear from this skill. Only the gated tournament-accept flow writes.
