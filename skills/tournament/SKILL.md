---
name: tournament
description: Run a Catfish decision tournament over a folder of notes/emails/transcripts and produce one terse, human-gated decision card with side-by-side options. Trigger when the user wants to compare 2-3 plans, make a hard project/technical call, or turn a pile of context into an approve-ready decision.
---

# Catfish tournament

Turn a folder of context into one decision card.

## Steps
1. Identify the source folder and the decision question.
2. Run: `catfish tournament <folder> "<question>"`
   - Free offline trial: prefix `CATFISH_DEMO=1`.
   - Live: set `CATFISH_LLM_API_KEY` (+ optional `CATFISH_MODEL`).
3. Show the rendered card. Do **not** write anything to Linear yet — the card is `proposed`.
4. When the human picks an option, accept it:
   `catfish accept .catfish/cards/<id>.json --choice <A|B|C> --by <name>`
   This previews the Linear tree (dry-run). Add `--linear` (+ `CATFISH_LINEAR_TOKEN`, `catfish[linear]`) to create it.

## Guardrails
- The Linear write is gated: no write happens until a human has chosen an option.
- Cards are terse by schema; never expand them into walls of text.
- Report the result honestly: a tournament score is relative persuasiveness, not truth.
