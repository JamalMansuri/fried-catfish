---
id: catfish-linear
title: catfish.linear
type: code-capability
tags: [linear]
summary: "Gated Linear write-back: parent issue -> story children -> sub-issues, by recursive parentId."
ref_count: 2
source: src/catfish/linear.py
status: proposed
---

# catfish.linear

> Gated Linear write-back: parent issue -> story children -> sub-issues, by recursive parentId.

**Capability** · used by 2 module(s) · 1 class(es) · 3 function(s)

## Business value (proposed — confirm me)
- (proposed) Gated Linear write-back: parent issue -> story children -> sub-issues, by recursive parentId.  _(type: enablement · status: proposed)_

## Classes
`_LinearClient`

## Functions
`build_tree`, `_body`, `write_tree`

## Depends on
[[catfish-card]] [[catfish-models]]

## Used by
[[catfish-mcp_tools]] [[catfish-server]]
