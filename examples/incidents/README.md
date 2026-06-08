# examples/incidents — the testable backtest

Most decisions Catfish is built for have no ground truth, so "is the stress-test actually worth
it?" is hard to answer. **Production incidents are the exception**: the postmortem eventually
settles what the real fix was. So this example is a *backtest* — six past on-call incidents whose
root-cause fix is now known, each built so the **loud, obvious read is a trap** and the correct
call needs a careful read of the timeline.

We run the tournament **blind** (the answer key never enters the corpus), then score its pick
against the held-out outcome — and against a deterministic "go with the loudest signal" baseline.
That gives a real number for the one thing a legible-but-untestable demo could never show: *does
adversarial stress-testing beat the confident first answer when we can actually check?*

## What's in here

| File | What it is |
|---|---|
| `cases/<id>/inbox/*.md` | the corpus for one incident — `alert.md` (the loud signal), `investigation.md` (the careful read), and `option_*.md`, one memo per candidate remediation |
| `cases/<id>/question.txt` | the decision the on-call faces |
| `cases/<id>/outcome.yaml` | **held-out** — the real root-cause fix + why the loud read misses. Lives *outside* `inbox/`, so the panel never sees it |
| `tags.yaml` | the domain vocabulary: `symptom / change / timeline / external / blast_radius / reversibility / evidence` |
| `personas/*.yaml` | the panel — **SRE** (blast radius, reversibility), **Forensic** (timeline, what changed), **Skeptic** (correlation ≠ causation) |
| `backtest.py` | the scoreboard runner — tournament per case, pick vs. truth vs. baseline |
| `RESULTS.md` | the recorded scoreboard from a real run |

`tags.yaml` and each persona's `filter.tags_any` are a **matched pair** — that pairing is the
whole adaptation, no source change. See [`../../ADAPTING.md`](../../ADAPTING.md).

The six cases bait classic on-call reflexes — scale the loudest metric (01), blame a slow third
party (02, 04), disable the newest change (03), restart a job that logs zero (05), roll back the
deploy that correlates (06) — and each is built so the careful read of the timeline beats the
reflex. Symptom-vs-cause is the shape underneath them all.

## Run one case (offline, no key)

```bash
# Replays the canned recording of case 01 — prints the full tournament + decision card instantly:
CATFISH_DEMO=1 catfish tournament examples/incidents/cases/01-checkout-latency/inbox \
  "$(cat examples/incidents/cases/01-checkout-latency/question.txt)" \
  --config-dir examples/incidents --finalists 4
```

## Run the backtest (live — needs a key)

```bash
# Runs the tournament on all six cases and scores it. A backtest is only honest if the panel
# never sees the answer key, and the offline replay only knows case 01 — so the real scoreboard
# needs a live judge:
CATFISH_LLM_API_KEY=... python examples/incidents/backtest.py
```

It prints a per-case ✓/✗ table — Catfish's pick, the loudest-signal baseline's pick, and the
known truth — plus the headline hit-rate, and writes it to [`RESULTS.md`](RESULTS.md).

> **Honest by construction.** We report whatever the run gives; the cases are not tuned until
> Catfish wins. A Bradley-Terry rank is still *persuasiveness among LLM judges*, not truth — the
> backtest measures how often that proxy lands on the answer the postmortem later confirmed.
