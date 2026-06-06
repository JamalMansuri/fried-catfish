# examples/lunch — the everyday demo

An ordinary decision, run through the full Catfish loop: **"Where should we grab lunch
today?"** across four options — Chipotle, McDonald's, Taco Bell, and the local taquería —
weighed by three relatable lenses.

It's a small, self-contained example you can read end to end in a minute. The same machinery
runs on real project and technical decisions; this one just keeps the stakes legible.

## What's in here

| File | What it is |
|---|---|
| `inbox/*.md` | the corpus — one short memo per option, plus `last_week.md`, a meal-history note |
| `tags.yaml` | the domain vocabulary: `health / cost / value / variety / speed / convenience` |
| `personas/*.yaml` | the panel — **Nutritionist** (health), **Budget** (cost/value), **Skeptic** (first-principles: *why a chain at all?*) |

`tags.yaml` and each persona's `filter.tags_any` are a **matched pair** — that pairing is
the whole adaptation, no source change. See [`../../ADAPTING.md`](../../ADAPTING.md).

The `last_week.md` note is the point: it's the kind of history a past decision leaves behind
in the corpus. The tournament *reaps* it — the panel notices we've had chain Mexican four of
the last five days — which is how the sow → reap → feedback loop shows up in one short run.

## Run it

```bash
# Offline, no API key — prints the full tournament + decision card instantly:
CATFISH_DEMO=1 catfish tournament examples/lunch/inbox \
  "Where should we grab lunch today?" --config-dir examples/lunch --finalists 4

# See the tagging seam directly — notes tagged with the food vocabulary:
catfish ingest examples/lunch/inbox --config-dir examples/lunch
```

The run header shows the panel (`nutritionist, budget, skeptic, neutral`) and the persona
lenses — that's the retarget working.

> **Note on offline mode.** `CATFISH_DEMO=1` replays a canned recording of this exact
> scenario (`src/catfish/fixtures.py`) so the demo runs free and deterministic with no key.
> For a live run on your own folder, drop `CATFISH_DEMO=1` and set `CATFISH_LLM_API_KEY`.
