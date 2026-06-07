# 🐟 Fried Catfish

**Stress-test plans in a tournament, decide in one card.**  ·  the `catfish` CLI

Ask an AI assistant for a plan and you get one confident answer, or five of them buried in a wall of text. Either way, you can't tell which one holds up under pressure. Catfish settles that with a tournament: it runs your decision through an [AI Co-Scientist](https://www.nature.com/articles/s41586-026-10644-y)-style loop that generates candidate plans, critiques them adversarially, battles them pairwise, and breeds new ones from the survivors. You get back one terse card with the options side by side, a recommendation, and a gate you have to sign off on. It won't hand you the answer; it pressure-tests your options and leaves you as the judge of record. It's a compound AI system, and it runs the same in Claude Code and Codex from a single MCP core.

**Why I built this**
- I read the AI Co-Scientist paper and it put names to things I was already doing: personas arguing it out, multiple rounds, Maps of Content built through different lenses. But the paper shipped no tool (it's a biomedical system, no repo), so I built one for the everyday product and engineering calls the rest of us make.
- I also think the harness, how you actually wire the model up, is starting to matter as much as the frontier model. This is me betting on that.

<img src="demo/catfish.gif" width="640" alt="A folder of options runs through a tournament (generate, critique, battle, Bradley-Terry) and lands on one human-gated decision card">

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

# Offline, no API key. Replays a sample "where should we grab lunch?" tournament:
CATFISH_DEMO=1 catfish tournament examples/lunch/inbox \
  "Where should we grab lunch today?" --config-dir examples/lunch --finalists 4
```

For a live run on your own folder, drop `CATFISH_DEMO=1` and set `CATFISH_LLM_API_KEY`.

## Learn more

- [SPEC.md](SPEC.md) covers the architecture, the tournament engine, and how it's built.
- [ADAPTING.md](ADAPTING.md) shows how to point it at your own sources (one tags file, one persona set).
- [examples/lunch/](examples/lunch/) is the worked example, start to finish.
- [AGENTS.md](AGENTS.md) is for driving or developing it from an agent.

## Honest limits

- There's no ground truth in this kind of work. You get stress-tested options, not verified answers. A Bradley-Terry score measures persuasiveness among LLM judges, which isn't the same as being right, so you stay the validator.
- The offline demo always replays the same canned lunch scenario. A real card on your own data needs a live key.
- Judge bias gets reduced, not solved. Position-swapping and length-blind judging help, but no bias-free LLM judge exists.

The rest of the caveats are in [SPEC.md](SPEC.md), under "Honest limits."

## License

MIT. See [LICENSE](LICENSE).
