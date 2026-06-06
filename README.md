# 🐟 Fried Catfish

**Stress-test plans in a tournament, decide in one card.**  ·  the `catfish` CLI

![Catfish: a messy folder → a tournament (generate · critique · battle · Bradley-Terry) → one human-gated decision card](demo/catfish.gif)

Catfish runs your project decisions through an AI Co-Scientist-style tournament — generate candidate plans, critique them adversarially, battle them pairwise, evolve the survivors — and hands you one terse decision card. You approve the call. Only then does it write the Linear ticket tree.

Portable across **Claude Code** and **Codex** from a single MCP core.

---

> **Catfish does not tell you the right answer.** It stress-tests your options against adversarial critique and gives you a terse comparison to decide. You are the judge of record. (See [Honest limits](#honest-limits) — this is load-bearing, not boilerplate.)

---

## Why this exists

AI assistants give you one confident plan, or five plans buried in a wall of text. You can't see the trade-offs side by side, and you can't tell which option survived a real challenge and which just sounded sure of itself.

Google already published the method that fixes this. AI Co-Scientist ([Nature 2026](https://www.nature.com/articles/s41586-026-10644-y), [arXiv:2502.18864](https://arxiv.org/abs/2502.18864)) runs a generate→debate→evolve tournament: candidates fight pairwise, weak ones die, survivors recombine, and a meta-review sharpens the next round. It works — but it's a biomedical science system, not a tool you can install.

Catfish is the assembly nobody had shipped: the full Co-Scientist loop, pointed at project-management and technical decisions, output as a terse card, gated on human approval before any ticket is written. One command after install.

## Nothing else does the whole thing

| | Ingests your files | Full tournament loop | Terse card output | Gates writes on human | Portable plugin |
|---|:---:|:---:|:---:|:---:|:---:|
| **Catfish** | ✅ | ✅ | ✅ | ✅ | ✅ |
| LangSmith | ❌ | ❌ (pairwise judge primitive only) | ❌ | ➖ (annotation queue) | ❌ |
| LangGraph | ❌ | ➖ (you build it) | ❌ | ❌ | ❌ |
| CrewAI / AutoGen | ❌ | ➖ (you build it) | ❌ | ❌ | ❌ |
| AI Co-Scientist | ➖ (biomed only) | ✅ | ❌ | ❌ | ❌ (no CLI) |

LangSmith is an eval bench. LangGraph and CrewAI are substrates you'd build Catfish *on top of*, not instead of. AI Co-Scientist is the method, not a product. Catfish is the only row with every box checked.

## The tournament loop

```
your files (.md .txt .docx .pdf .eml)
   → ingest (MarkItDown) → Map of Content (frontmatter + spine)
   → persona lenses (skeptic / pm / security) run in parallel isolation
   → Generation:  4+ candidate plans
   → Reflection:  adversarial critique per candidate
   → Ranking:     pairwise debate, Bradley-Terry scoring
   → Evolution:   synthesize new candidates; top-ranked never mutated
   → Meta-review: patterns fed into the next round
   → Decision card (terse by schema)  →  human gate  →  Linear (gated)
```

The scorer is **Bradley-Terry, not Elo**. Pairwise LLM judgments are non-transitive — A beats B beats C beats A, [documented at ICML 2025](https://arxiv.org/abs/2502.14074) — which breaks Elo's core assumption. LMSYS migrated Chatbot Arena from Elo to Bradley-Terry for stable confidence intervals; that's the same scorer that handles non-transitive cycles. We implement the MLE fit in ~50 lines of pure Python.

## Also: map a codebase by what it does

Point Catfish at a repo and it builds a **logic map** — organized by capability and flow, not file tree — where each capability carries a one-line **business-value** translation (`auth → account security → churn prevention`). Structure is extracted deterministically (stdlib `ast` / ripgrep in core; tree-sitter in the optional `[code]` extra); the business-value lines are *proposals you confirm*, never asserted as fact. It makes a codebase legible to a PM and lets a decision card weigh a technical call by what it actually protects.

Catfish maps **itself**: `catfish map src` writes a [Foam](https://foambubble.github.io/foam/)-compatible wiki to [wiki/](wiki/) in **two layers** — an engineer dependency graph ([wiki/index.md](wiki/index.md)) and a PM business-capability graph ([wiki/business.md](wiki/business.md)) — both as Mermaid that renders on GitHub, no extension needed.

The decision loop itself is also markdown: `catfish architecture` distills the **cognitive architecture** into [cognition/index.md](cognition/index.md). Each stage's identity lives in an editable `.md` anchor (`cognition/*.md`) that's re-injected every round so the agents can't drift — anti-drift as plain files, not a vector store.

## Choose your panel (personas have moods)

`catfish roster` shows a character-select of personas × moods. Assemble the critic panel for a run:

```bash
catfish tournament ./examples/inbox "<question>" --critics skeptic:grumpy,security:paranoid,qa:bad_mood
```

A "QA in a bad mood" nitpicks harder and surfaces more edge cases — a *severity/diversity dial*, not an accuracy boost. Personas can also carry documentation they "know" (a QA persona that has read your test playbook), injected as bounded reference. Any emotional state works; unknown moods are used literally.

Ships with the **Project Riley** ([arXiv:2505.20521](https://arxiv.org/abs/2505.20521)) Inside-Out emotion characters as a starter panel — `--critics riley` runs Joy, Sadness, Fear, Anger, Disgust. (`anger` carries the Devil's-Advocate role, because the [research](https://openreview.net/forum?id=mxBmj5LYU2) says an explicit dissent *role*, not emotion, is what actually breaks consensus — mood rides on top.)

## Skills (Claude Code / Codex)

Installed as a plugin, Catfish ships four skills your host invokes by intent — nothing to memorize:

- **tournament** — turn a folder of context + a hard question into one decision card. *("decide X vs Y", "make the call on …")*
- **scout** — research an open question with parallel sub-agents over your corpus, then optionally hand the framing to a tournament. *("scout this", "dig into X before we decide")*
- **retro** — review a past decision: what the panel warned about vs. what actually happened. *("run a retro", "how did decision X turn out?")*
- **map** — map a codebase by capability and business value, not file tree. *("what does this repo do?")*

Each is plain markdown under [skills/](skills/) — edit a `SKILL.md` to change how it behaves. The Linear write stays gated no matter which skill drives it.

## Quickstart

One run is roughly **40–60 LLM calls, under $0.50, under a minute.**

**Install from source** (PyPI publish is on the roadmap):
```bash
git clone <your-fork> catfish && cd catfish
pip install -e .          # puts `catfish` on your PATH
```
For Claude Code / Codex, point the host at the bundled `.mcp.json` (MCP wiring); the human-approval gate ships as a `PreToolUse` hook in `hooks/hooks.json`.

Then point it at a folder and ask a question — the first run is **free and offline**, no API key:
```bash
CATFISH_DEMO=1 catfish tournament ./examples/inbox "Do we unleash the Fremen jihad across the Imperium?" --finalists 4
```

It ingests the folder, builds the spine, generates four candidate plans, sends each through a five-critic panel, battles them pairwise, scores the survivors with Bradley-Terry, and prints the tournament and the card below. The first run works on a cold install with no API key — `examples/` ships canned model outputs so you see real output instantly. Wire your host (or set `CATFISH_LLM_API_KEY`) for live runs.

## What it prints

```
(GENERATION + REFLECTION print first and scroll by in the GIF; here is the tail)

③  RANKING — every pair fought twice, sides swapped
     Unleash   beat Restrain, Abdicate, Channel 3–0
     Restrain  beat Abdicate                   1–2
     Abdicate  beat Channel                    1–2
     Channel   beat Restrain                   1–2

   ⚠  non-transitive cycle:  Restrain ▸ Abdicate ▸ Channel ▸ Restrain
        each beats the next — win-counting ties them, Elo breaks.

④  BRADLEY-TERRY — strength from who-beat-whom, not raw wins
     [A] Unleash the jihad      0.61  ██████████████████████  3–0  ★
     [B] Restrain the legions   0.13  █████·················  1–2
     [C] Abdicate the throne    0.13  █████·················  1–2
     [D] Channel the fervor     0.13  █████·················  1–2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DECISION CARD  card-2026-06-06-001            status: PROPOSED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROBLEM
  The Fremen await one word to loose a holy war across the
  Imperium in your name. Prescience shows it kills billions.
  Do you unleash it?

FIRST PRINCIPLES
  1. The Fremen already believe you are the Mahdi; the fervor
     exists whether you lead it or not.
  2. Prescience shows the jihad spreading from Arrakis on
     every path — the question is whether you steer it.
  3. Total power and its cost arrive together; one cannot be
     taken without the other.

┌────────────────────────┬────────────────────────┬────────────────────────┬────────────────────────┐
│ [A] Unleash the jihad  │ [B] Restrain the       │ [C] Abdicate the       │ [D] Channel the fervor │
│ score 0.61  ★REC       │ legions                │ throne                 │ score 0.13             │
│                        │ score 0.13             │ score 0.13             │                        │
├────────────────────────┼────────────────────────┼────────────────────────┼────────────────────────┤
│ GOOD                   │ GOOD                   │ GOOD                   │ GOOD                   │
│ Total power — the      │ Keeps your hands clean │ Refuses to be the      │ Spends the faith on a  │
│ legions sweep every    │ of the jihad's blood.  │ banner a holy war      │ green Arrakis, not a   │
│ Great House before     │                        │ marches under.         │ burning Imperium.      │
│ them.                  │                        │                        │                        │
├────────────────────────┼────────────────────────┼────────────────────────┼────────────────────────┤
│ NEUTRAL                │ NEUTRAL                │ NEUTRAL                │ NEUTRAL                │
│ You become the messiah │ Rules by the spice and │ Hands Arrakis and the  │ Slow — terraforming is │
│ they already believe   │ the threat, not the    │ spice to whoever takes │ a multi-generation     │
│ you are.               │ sword.                 │ them.                  │ dream.                 │
├────────────────────────┼────────────────────────┼────────────────────────┼────────────────────────┤
│ BAD                    │ BAD                    │ BAD                    │ BAD                    │
│ Sixty-one billion dead │ Prescience says the    │ The legend outlives    │ A faith built for      │
│ across the Imperium,   │ fervor breaks the      │ you; they crown a      │ conquest may not       │
│ and it can't be        │ leash and burns        │ martyr and march       │ settle for gardening.  │
│ recalled.              │ anyway.                │ regardless.            │                        │
└────────────────────────┴────────────────────────┴────────────────────────┴────────────────────────┘

RECOMMENDATION  →  A  Unleash the jihad
  Every other path still ends in the jihad — only this one
  puts you at its head.

──────────────────────────────────────────────────────────────
HUMAN GATE  [ thumbs-up required before any Linear write ]
  decided_by: ____    choice: ____ (A/B/C/D)    notes: ____
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

The card is the same scenario as the files in `examples/inbox` — Stilgar's report that the legions are ready, a mentat's tally of who turns hostile, the prescient vision of sixty-one billion dead, the Bene Gesserit's warning, and the war council where it comes to a head. Trace the input to the output yourself. Note what the demo is really showing: the tournament ranks *Unleash* highest on cold strategy, and the gate is exactly where a human has to refuse it. The machine scores; you are the judge of record.

Type your choice and the gate flips the card to `accepted`. Catfish then writes the Linear tree: parent issue → story children → sub-issues, by `parentId` (the UUID, not the `ENG-42` key). No Linear write happens with the choice still null — the gate is enforced in code via `assert_approved()`, not only by host config.

## Terseness is a schema rule, not a style

Every card field has a hard word cap enforced before the card is written. A card that runs long is rejected and regenerated shorter. Verbosity creep is a known failure mode of recursive LLM loops, so the cap is structural.

| Field | Cap |
|---|---|
| problem statement | 30 words |
| each first principle | 20 words |
| each option solution | 25 words |
| each trade-off | 15 words |
| recommendation | 20 words |

## Lightweight by design

Core install is three things: the MCP SDK, `pyyaml`, and MarkItDown for ingestion. The Bradley-Terry fit is pure Python (numpy is an optional `[fast]` extra you'll never need at 3–4 finalists). Linear write-back is an optional `[linear]` extra — the core produces cards as files and runs with zero network dependencies.

No LangGraph, no CrewAI, no AutoGen, no vector DB, no embedding model, no GPU. We borrow the patterns, not the dependency graphs. (MarkItDown is the heaviest part of the tree — it bundles handlers for ~29 formats. That's the one honest weight in an otherwise tiny core.)

Heavier ingestion is opt-in and never imported by core: audio (WhisperX + speaker diarization, free HF token), web crawl (Trafilatura), chat exports (Slack/Discord).

## Honest limits

Read these before you trust a ranking.

- **No ground truth in PM.** Catfish produces stress-tested *options*, not verified *answers*. A Bradley-Terry score is relative persuasiveness among LLM judges — not a measure of correctness. A confident, internally consistent, *wrong* consensus is a real failure mode, and it's worse here than in science because there's no wet-lab to falsify it. You are the validator.
- **Judge bias is mitigated, not eliminated.** Position-swap and length-blind judging reduce it. Self-preference bias can only be removed with a different-family judge; on a single model family it can be logged, not fixed. No bias-free LLM judge exists.
- **Personas don't make answers smarter.** Coarse roles in parallel isolation are a diversity and stress-testing lever, not an accuracy guarantee. Named-expertise personas ("senior architect, 20 years") are [explicitly falsified](https://arxiv.org/abs/2311.10054) as a reliability mechanism.
- **Self-improvement is bounded.** Meta-review sharpens later rounds but can't escape the base model's blind spots (the Self-Refine ceiling).
- **Quality scales with ingestion quality.** Clean digital docs work well. Scanned PDFs, audio, and JS-heavy pages need heavier optional extractors and may lose fidelity.
- **Codex gate is not yet verified.** The Claude Code gate runs via a `PreToolUse` hook. On Codex, `approval_mode=prompt` on MCP tool calls is unverified as of Codex v0.3 — until confirmed, the in-code `assert_approved()` is the only guaranteed gate on the Codex path.
- **Markdown memory is small-scale only.** It's the right substrate under ~100 sessions. Beyond that you'd want a vector-DB backend Catfish deliberately doesn't ship.

## Roadmap

- **v1** — Live Linear write-back (parent→story→sub-issue tree); Claude Code `PreToolUse` gate end-to-end; Codex gate confirmed; codebase logic-map with human-gated business-value translation.
- **v2** — Optional extractor plugins (audio, web crawl, chat exports); tree-sitter `[code]` extra for precise code symbols; persona auto-seeding from your corpus; tiered cost control tuned against real usage.

## License

MIT. AGPL/GPL extractors (Firecrawl, Slackdump) are optional, self-hosted, and never imported by core, so the core stays clean-license.

---

*Catfish abstracts the methodology of Google's AI Co-Scientist ([arXiv:2502.18864](https://arxiv.org/abs/2502.18864)). It is grounded in the research, honest about its limits, and built to stay out of your way.*
