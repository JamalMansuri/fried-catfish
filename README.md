# 🐟 Fried Catfish

**Stress-test plans in a tournament, decide in one card.**  ·  the `catfish` CLI

Ask an AI assistant for a plan and you get one confident answer, or five of them buried in a wall of text. Either way, you can't tell which one holds up under pressure. Catfish settles that with a tournament: it runs your decision through an [AI Co-Scientist](https://www.nature.com/articles/s41586-026-10644-y)-style loop that generates candidate plans, critiques them adversarially, battles them pairwise, and breeds new ones from the survivors. You get back one terse card with the options side by side, a recommendation, and a gate you have to sign off on. It won't hand you the answer; it pressure-tests your options and leaves you as the judge of record. It's a compound AI system, and it runs the same in Claude Code and Codex from a single MCP core.

**Why I built this**
- I read the AI Co-Scientist paper and it put names to things I was already doing: personas arguing it out, multiple rounds, Maps of Content built through different lenses. But the paper shipped no tool (it's a biomedical system, no repo), so I built one for the everyday product and engineering calls the rest of us make.
- I also think the harness, how you actually wire the model up, is starting to matter as much as the frontier model. This is me betting on that.

<img src="demo/catfish.gif" width="640" alt="An on-call incident — checkout p99 spiking, the database pegged — runs through the tournament (generate, critique, battle, Bradley-Terry) and lands on one human-gated call: roll back the deploy, not scale the database">

<sub>Checkout latency is 5× and every metric blames the database. The tournament reads the timeline instead, and lands on rolling back the deploy — gated on your sign-off. Offline, no key; the quickstart below replays it, and the six-case [backtest](examples/incidents/) is where it's scored.</sub>

## How it works

```
folder → persona lenses → generate → critique → rank (Bradley-Terry) → evolve
       → terse card → human gate → Linear (gated) → decision sown back ↺
```

The ranker is Bradley-Terry, not Elo. Pairwise LLM judgments go non-transitive (A beats B beats C beats A), which breaks Elo's main assumption; Bradley-Terry handles the cycles fine. Architecture lives in [SPEC.md](SPEC.md).

## What you get

- A tournament instead of one model's first guess: generate, critique, battle, evolve, meta-review, all scored by Bradley-Terry.
- A critic panel you pick yourself with `catfish roster`. Persona moods are a severity dial, not an accuracy boost.
- Short decision cards behind a hard gate. Nothing reaches Linear until you approve it, and that gate lives in code, so host config can't route around it.
- A loop that closes: once you review a decision it folds back into the corpus, so the next run starts from what the last one learned.
- Point it at a repo and it maps the code by capability and business value (`catfish map src`).
- Skills your host already speaks: `tournament`, `scout`, `retro`, `map`.

## Quickstart

```bash
git clone https://github.com/JamalMansuri/fried-catfish && cd fried-catfish
pip install -e .

# Offline, no API key. Replays a sample on-call incident tournament:
CATFISH_DEMO=1 catfish tournament examples/incidents/cases/01-checkout-latency/inbox \
  "$(cat examples/incidents/cases/01-checkout-latency/question.txt)" \
  --config-dir examples/incidents --finalists 4
```

For a live run on your own folder, drop `CATFISH_DEMO=1` and set `CATFISH_LLM_API_KEY`.

## Does it actually work?

Most decisions Catfish is built for have no ground truth — but production incidents do: the
postmortem eventually settles the real fix. So [`examples/incidents/`](examples/incidents/) is a
**backtest** over six past on-call incidents, each built so the loud, obvious read is a trap
(loudest-metric, recency bias, blame-the-vendor, correlation≠causation…). It runs the tournament
**blind** — the answer key never enters the corpus — then scores the pick against the held-out
outcome and a deterministic "loudest-signal" baseline:

```bash
CATFISH_LLM_API_KEY=... python examples/incidents/backtest.py
```

That's the one thing a toy demo can't show: on decisions where truth is knowable, does
stress-testing beat the confident first answer? The baseline scores **0/6 by construction** —
every case's obvious answer is wrong — so the gap to Catfish's column is the whole point. Recorded
scoreboard: [RESULTS.md](examples/incidents/RESULTS.md).

## Learn more

- [SPEC.md](SPEC.md) covers the architecture, the tournament engine, and how it's built.
- [ADAPTING.md](ADAPTING.md) shows how to point it at your own sources (one tags file, one persona set).
- [examples/incidents/](examples/incidents/) is the worked example + the backtest, start to finish.
- [AGENTS.md](AGENTS.md) is for driving or developing it from an agent.

## Honest limits

- There's no ground truth in most of this work. You get stress-tested options, not verified answers. A Bradley-Terry score measures persuasiveness among LLM judges, which isn't the same as being right, so you stay the validator. (The backtest above is the one place truth is knowable — and it's honest about misses.)
- The offline demo always replays the same canned incident (case 01). A real card on your own data — and the full six-case backtest — needs a live key.
- Judge bias gets reduced, not solved. Position-swapping and length-blind judging help, but no bias-free LLM judge exists.

The rest of the caveats are in [SPEC.md](SPEC.md), under "Honest limits."

## License

MIT. See [LICENSE](LICENSE).
