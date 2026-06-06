---
name: retro
description: Review and close a past Catfish decision — list the decision ledger, surface what the panel warned about, and record what actually happened. Trigger when the user wants to revisit an old decision, run a retrospective, "close the loop", check which decisions are owed a review, or asks "how did decision X turn out?".
---

# Catfish retro

A decision is done when it's reviewed, not when it ships. This closes the loop.

## Steps
1. List the ledger: `catfish retro` — shows every accepted decision and whether each is still owed a retrospective (⏳ retro due / ✓ reviewed).
2. To review one, open its retro surface: `catfish retro .catfish/cards/<id>.json` — this shows the decision, what the panel kept worrying about (`concerns`), what critics warned about the chosen option (`risks`), and the roads not taken.
3. Ask the human the question that matters: we were warned about X — did X actually happen? Pull the chosen option's recorded `risks` into the prompt; checking the warnings against reality is the whole point of a retro.
4. Record the outcome:
   `catfish retro .catfish/cards/<id>.json --outcome "..." --went-well "..." --went-wrong "..." --repeat yes|no --lessons "..." --by <name>`
   This writes the review onto the card and flips the ledger row to reviewed.

## Guardrails
- Record what the human reports; don't editorialize the outcome.
- Read-only until the human gives the outcome — recording the review is the only write.
- A retro never re-opens the Linear tree; it captures what was learned.
