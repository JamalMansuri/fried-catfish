---
id: catfish-card
title: catfish.card
type: code-capability
tags: [card]
summary: "Decision cards: build from a tournament result, enforce terseness, render, gate."
ref_count: 2
source: src/catfish/card.py
status: proposed
---

# catfish.card

> Decision cards: build from a tournament result, enforce terseness, render, gate.

**Capability** · used by 2 module(s) · 1 class(es) · 11 function(s)

## Business value (proposed — confirm me)
- (proposed) Decision cards: build from a tournament result, enforce terseness, render, gate.  _(type: enablement · status: proposed)_

## Classes
`GateBlockedError`

## Functions
`_cap`, `build_card`, `_row`, `_border`, `_section`, `_table`, `render`, `assert_approved`, `accept`, `save_card`, `load_card`

## Depends on
[[catfish-models]]

## Used by
[[catfish-linear]] [[catfish-server]]
