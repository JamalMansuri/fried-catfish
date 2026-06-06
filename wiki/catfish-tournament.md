---
id: catfish-tournament
title: catfish.tournament
type: code-capability
tags: [tournament]
summary: "The tournament engine: generate -> reflect -> rank -> evolve -> meta-review."
ref_count: 1
source: src/catfish/tournament.py
status: proposed
---

# catfish.tournament

> The tournament engine: generate -> reflect -> rank -> evolve -> meta-review.

**Capability** · used by 1 module(s) · 1 class(es) · 12 function(s)

## Business value (proposed — confirm me)
- (proposed) The tournament engine: generate -> reflect -> rank -> evolve -> meta-review.  _(type: enablement · status: proposed)_

## Classes
`TournamentResult`

## Functions
`bradley_terry`, `softmax_scores`, `_persona_context`, `_gen_prompt`, `_reflect_user_prompt`, `_rank_prompt`, `_meta_prompt`, `_evolve_prompt`, `_card_prompt`, `_judge_pair`, `_run_round_robin`, `run_tournament`

## Entry points
`run_tournament`

## Depends on
[[catfish-cognition]] [[catfish-llm]] [[catfish-models]] [[catfish-personas]]

## Used by
[[catfish-server]]
