# examples/biotech — Catfish retargeted to a different domain

This folder is the proof that Catfish is domain-agnostic. The default examples (`examples/inbox`,
a Dune scenario) run on the built-in software/eng vocabulary. This one runs the **same engine** on
a biotech / lab-R&D decision — *"Do we proceed to the GxP run?"* — using **only two retargeted
files** and no source change:

| File | What it is | Diff from default |
|---|---|---|
| `tags.yaml` | the domain vocabulary | software vocab → `assay / contamination / regulatory / cell-line / validation / timeline` |
| `personas/*.yaml` | the critic panel | `skeptic / pm / security` → `Regulatory Reviewer / QA-Validation Lead / Bench Scientist` |
| `inbox/*.md` | the source docs | Dune memos → 4 synthetic lab memos (assay readiness, a contamination incident, a GxP memo, the campaign schedule) |

The tags in `tags.yaml` and the `filter.tags_any` lists in `personas/*.yaml` are a **matched pair**
— that pairing is the whole adaptation. See [`../../ADAPTING.md`](../../ADAPTING.md) for the
step-by-step.

## Run it

```bash
# See the retarget seam directly — notes tagged with the biotech vocabulary:
catfish ingest examples/biotech/inbox --config-dir examples/biotech

# Run the tournament with the biotech vocab + panel (offline, no key):
CATFISH_DEMO=1 catfish tournament examples/biotech/inbox "Do we proceed to the GxP run?" --config-dir examples/biotech
```

The run header will show the biotech panel (`regulatory, qa_validation, bench, neutral`) and three
persona lenses — that's the retarget working.

> **Honest note on offline mode.** `CATFISH_DEMO=1` uses canned model outputs recorded for the Dune
> scenario (`src/catfish/fixtures.py`), so **offline the decision card content stays Dune-flavored**
> even here. What the biotech example proves offline is the deterministic, no-LLM part — ingestion,
> the domain tagging, and the persona lenses (run `catfish ingest … --config-dir examples/biotech`
> to see it). For a real biotech card, run it live with `CATFISH_LLM_API_KEY` set (drop the
> `CATFISH_DEMO=1`). The data is synthetic — no real lab or patient data.
