# Backtest results — Catfish vs. the loudest-signal baseline

> ⚠️ **Not yet run against a live judge.** The Catfish column below is blank because a backtest is
> only honest if a real model reasons over each case blind, and that needs a key. The **baseline**
> and **known fix** columns are deterministic (pure Python, no LLM), so they're filled in already.
>
> Populate the Catfish column with a real run:
> ```bash
> CATFISH_LLM_API_KEY=... python examples/incidents/backtest.py
> ```
> It overwrites this file with the recorded scoreboard.

**Catfish _/6 (not yet run)  ·  loudest-signal baseline 0/6**

| case | known fix | Catfish | ✓ | baseline (loudest signal) | ✓ |
|---|---|---|:--:|---|:--:|
| 01-checkout-latency | rollback | _(run to populate)_ | – | scale_db | ❌ |
| 02-intermittent-500s | revert_config | _(run to populate)_ | – | vendor_ticket | ❌ |
| 03-slow-oom | add_eviction | _(run to populate)_ | – | disable_flag | ❌ |
| 04-webhook-dupes | restore_idempotency | _(run to populate)_ | – | rate_limit_provider | ❌ |
| 05-stale-search | fix_clock | _(run to populate)_ | – | restart_indexer | ❌ |
| 06-mobile-crash | server_default | _(run to populate)_ | – | rollback_backend | ❌ |

## How to read this

The baseline is a deterministic foil — the remediation whose memo reads most like the loud alert
(it never reads the timeline), computed with no LLM. It lands on each case's trap by construction,
so it scores **0/6**: every case is built so the obvious read is wrong. The Catfish column is the
live tournament's recommendation on the same blind corpus. The gap between the two columns is what
adversarial stress-testing buys on decisions where the truth is knowable.

Case 06 is deliberately the most arguable (rollback also stops new crashes), so a Catfish miss
there is honest signal, not a tuning failure. **The six cases are fixed; we report whatever the
run gives.**

> A Bradley-Terry rank is persuasiveness among LLM judges, not truth. This backtest measures how
> often that proxy lands on the answer the postmortem later confirmed — not whether the tool is
> "right" on your own undecided call.
