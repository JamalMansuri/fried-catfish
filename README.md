# 🐟 Fried Catfish

**Stress-test plans in a tournament, decide in one card — and let each decision teach the next.**  ·  the `catfish` CLI

![Catfish: a messy folder → a tournament (generate · critique · battle · Bradley-Terry) → one human-gated decision card](demo/catfish.gif)

Catfish runs your project decisions through an AI Co-Scientist-style tournament — generate candidate plans, critique them adversarially, battle them pairwise, evolve the survivors — and hands you one terse decision card. You approve the call. Only then does it write the Linear ticket tree. And once you do, that decision is folded back into the corpus as compressed wisdom the next tournament can draw on.

A **compound AI system** — multi-agent tournament, deterministic Bradley-Terry scorer, human-gated writes — portable across **Claude Code** and **Codex** from a single MCP core.

---

> **Catfish does not tell you the right answer.** It stress-tests your options against adversarial critique and gives you a terse comparison to decide. You are the judge of record. (See [Honest limits](#honest-limits) — this is load-bearing, not boilerplate.)

---

## Sow → reap → gated feedback

Catfish is one loop. You **sow** a corpus, the tournament **reaps** it into a decision, and your gated approval **feeds the decision back** into the corpus as compressed wisdom — so the next reap is informed by the last one.

```
        ┌──────────────────────────────────────────────────────────┐
        │                                                          │
        ▼                                                          │
   ┌─────────┐      ┌──────────────┐      ┌──────────────┐         │
   │  SOW    │      │    REAP      │      │  HUMAN GATE  │         │
   │ folder  │ ───▶ │  tournament  │ ───▶ │  you decide  │ ──┐     │
   │ + tags  │      │  over the    │      │  (approve /  │   │     │
   │ + panel │      │  MoC spine   │      │   reject)    │   │     │
   └─────────┘      └──────────────┘      └──────────────┘   │     │
        ▲                                                    │     │
        │                                          writes Linear   │
        │                                          (gated)         │
        │                                                    ▼     │
        │           the accepted + reviewed decision  ┌──────────┐ │
        └──────────────  re-ingested as a  ◀──────────│ FEEDBACK │─┘
              compressed type="decision" Note         └──────────┘
                  (gated on your review)
```

**The loop:** you sow a corpus, the tournament reaps it into one gated card, and the decision you approve and later review is sown back as a compressed `decision` Note that the next tournament's personas can reap.

## Nothing else does the whole thing

| | Ingests your files | Full tournament loop | Terse card output | Gates writes on human | Decisions feed back | Portable plugin |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Catfish** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| LangSmith | ❌ | ❌ (pairwise judge primitive only) | ❌ | ➖ (annotation queue) | ❌ | ❌ |
| LangGraph | ❌ | ➖ (you build it) | ❌ | ❌ | ❌ | ❌ |
| CrewAI / AutoGen | ❌ | ➖ (you build it) | ❌ | ❌ | ❌ | ❌ |
| AI Co-Scientist | ➖ (biomed only) | ✅ | ❌ | ❌ | ➖ (meta-review, same run) | ❌ (no CLI) |

LangSmith is an LLM-evaluation bench. LangGraph and CrewAI are multi-agent orchestration substrates you'd build Catfish *on top of*, not instead of. AI Co-Scientist is the method, not a product. Catfish is the only row with every box checked.

## The elemental path: one decision, end to end

The shortest way to understand Catfish is to walk one decision through it. `examples/lunch/` is a complete, self-contained sow — an ordinary call anyone has made: **"Where should we grab lunch today?"** across Chipotle, McDonald's, Taco Bell, and the local taquería.

**1. Look at what was sown.** The folder *is* the corpus:

- **5 inbox memos** (`examples/lunch/inbox/`) — one per option (`chipotle.md`, `mcdonalds.md`, `taco_bell.md`, `taqueria.md`) plus `last_week.md`, a meal-history note: chain food four of the last five days, Chipotle twice.
- **`tags.yaml`** — the domain vocabulary (`health / cost / value / variety / speed / convenience`) that replaces the default software vocab.
- **3 personas** (`examples/lunch/personas/`) — `nutritionist` (weighs how processed and how nourishing it is), `budget` (food and time back per dollar, not just the sticker price), and `skeptic` (first principles: *why a chain at all — and are we just repeating last week?*).

The tags and each persona's `tags_any` filter are a **matched pair** — that pairing is the whole adaptation, no source code change. See [`examples/lunch/README.md`](examples/lunch/README.md) and [`ADAPTING.md`](ADAPTING.md).

**2. Reap it.**

```bash
# Offline, no API key — replays this exact scenario, deterministic:
CATFISH_DEMO=1 PYTHONPATH=src python3 -m catfish tournament examples/lunch/inbox \
  "Where should we grab lunch today?" --config-dir examples/lunch --finalists 4
```

The offline run replays a canned recording of this scenario, so the card content lines up with the folder above. For a live run on your own notes, drop `CATFISH_DEMO=1` and set `CATFISH_LLM_API_KEY` — the tournament then reaps your real files through the panel and writes a fresh card.

**3. Read the card.** One terse comparison of the options, side by side, with a recommendation and a `HUMAN GATE` line. ([What it prints](#what-it-prints), below, shows the fully rendered card.)

**4. Decide.** You type the choice. The gate flips the card to `accepted`, and only then does Catfish write the Linear tree. Once you later **review** that decision, it is folded back into the corpus as a compressed `decision` Note — so the next tournament's personas reap your own past calls. (`last_week.md` is exactly that history, stood up by hand so you can see the loop in a single run.)

## What it prints

```
(GENERATION + REFLECTION print first and scroll by in the GIF; here is the tail)

③  RANKING — every pair fought twice, sides swapped
     Taquería  beat Chipotle, McDonald's, Taco 3–0
     Chipotle  beat McDonald's                 1–2
     McDonald's beat Taco                       1–2
     Taco      beat Chipotle                   1–2

   ⚠  non-transitive cycle:  Chipotle ▸ McDonald's ▸ Taco ▸ Chipotle
        each beats the next — win-counting ties them, Elo breaks.

④  BRADLEY-TERRY — strength from who-beat-whom, not raw wins
     [A] Taquería down the block 0.61  ██████████████████████  3–0  ★
     [B] Chipotle               0.13  █████·················  1–2
     [C] McDonald's             0.13  █████·················  1–2
     [D] Taco Bell              0.13  █████·················  1–2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DECISION CARD  card-2026-06-06-001            status: PROPOSED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PROBLEM
  Four lunch spots within reach and forty minutes to eat.
  Where do we go — and does it matter that we keep repeating
  ourselves?

FIRST PRINCIPLES
  1. Most of this week was chain food; another repeat spends
     novelty we won't get back.
  2. Fast food's real cost is processing and sameness, not
     the dollar on the receipt.
  3. A short walk to fresh, made-to-order food beats a drive-
     thru when the time is close.

┌────────────────────────┬────────────────────────┬────────────────────────┬────────────────────────┐
│ [A] Taquería down the  │ [B] Chipotle           │ [C] McDonald's         │ [D] Taco Bell          │
│ block                  │ score 0.13             │ score 0.13             │ score 0.13             │
│ score 0.61  ★REC       │                        │                        │                        │
├────────────────────────┼────────────────────────┼────────────────────────┼────────────────────────┤
│ GOOD                   │ GOOD                   │ GOOD                   │ GOOD                   │
│ Fresh, unprocessed,    │ Fresh-ish,             │ Cheapest and fastest;  │ Most food per dollar;  │
│ biggest portion per    │ customizable, filling  │ back at the desk       │ the value box          │
│ dollar — and a real    │ — a safe known         │ quickest.              │ overdelivers.          │
│ break from the chains. │ quantity.              │                        │                        │
├────────────────────────┼────────────────────────┼────────────────────────┼────────────────────────┤
│ NEUTRAL                │ NEUTRAL                │ NEUTRAL                │ NEUTRAL                │
│ Cash is easier than    │ Mid-price; the line    │ Familiar, and the app  │ Drive-thru speed;      │
│ card; a five-minute    │ gets long right at     │ deals soften the       │ quality varies by      │
│ walk each way.         │ noon.                  │ price.                 │ location.              │
├────────────────────────┼────────────────────────┼────────────────────────┼────────────────────────┤
│ BAD                    │ BAD                    │ BAD                    │ BAD                    │
│ A couple dollars more, │ Third time this week — │ Most processed; hungry │ Processed, and we      │
│ and no app points.     │ palate fatigue is      │ again within the hour. │ already had it         │
│                        │ real.                  │                        │ Thursday.              │
└────────────────────────┴────────────────────────┴────────────────────────┴────────────────────────┘

RECOMMENDATION  →  A  Taquería down the block
  Same money and time as a chain, but fresh, bigger, and the
  one thing we haven't eaten this week.

──────────────────────────────────────────────────────────────
HUMAN GATE  [ thumbs-up required before any Linear write ]
  decided_by: ____    choice: ____ (A/B/C/D)    notes: ____
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

This is the offline card — the same scenario as the files in `examples/lunch/inbox` (a memo per option, plus `last_week.md`: chain food four of the last five days, Chipotle twice). Trace the input to the output yourself. Note what the demo is really showing: the tournament ranks the taquería highest on the merits — fresher, better value, and the one thing not already on this week's rotation — and the `HUMAN GATE` is exactly where you sign off. The machine scores; you are the judge of record.

Type your choice and the gate flips the card to `accepted`. Catfish then writes the Linear tree: parent issue → story children → sub-issues, by `parentId` (the UUID, not the `ENG-42` key). No Linear write happens with the choice still null — the gate is enforced in code via `assert_approved()`, not only by host config.

## Honest limits

Read these before you trust a ranking. This is the trust surface; it leads, it doesn't trail.

- **No ground truth in PM.** Catfish produces stress-tested *options*, not verified *answers*. A Bradley-Terry score is relative persuasiveness among LLM judges — not a measure of correctness. A confident, internally consistent, *wrong* consensus is a real failure mode, and it's worse here than in science because there's no wet-lab to falsify it. **You are the validator.**
- **The offline demo replays one fixed scenario.** `CATFISH_DEMO=1` always emits the canned lunch fixtures (`src/catfish/fixtures.py`). It **ignores `--config-dir` and your input folder** — pointed at `examples/lunch` it lines up exactly; pointed at your own folder, you still get the lunch card. Offline proves the deterministic seams (ingestion, tagging, lenses); a real card on your data needs a live key.
- **Reap-ask is host-orchestrated, not an engine.** The `scout` skill researches an open question by fanning out host sub-agents over your corpus. There is no `query_spine()` in the codebase — retrieval is the host's job, not an engine query.
- **Persona lenses are ephemeral.** They're computed live each run and not persisted to disk. (Persisting them — and a step-0 `catfish review` preview — is on the roadmap.)
- **The spine is flat JSONL.** It's a flat `_graph_index.jsonl` of `{id, title, type, status, summary, tags, source_hash}` rows, not a hierarchical PageIndex tree. The MoC is flat-summary + constrained tags, not a knowledge graph.
- **Tracker write-back is Linear-only.** Jira and other trackers are roadmap adapters, not shipped.
- **5 of 6 Co-Scientist agents.** Catfish implements Generation, Reflection, Ranking, Evolution, and Meta-review; the Proximity agent is absent. Scoring is **Bradley-Terry MLE, not Elo**.
- **LLM-as-judge bias is mitigated, not eliminated.** Position-swap and length-blind judging reduce it. Self-preference bias can only be removed with a different-family judge; on a single model family it can be logged, not fixed. No bias-free LLM judge exists.
- **Personas don't make answers smarter.** Coarse roles in parallel isolation are a diversity and stress-testing lever, not an accuracy guarantee. Named-expertise personas ("senior architect, 20 years") are [explicitly falsified](https://arxiv.org/abs/2311.10054) as a reliability mechanism.
- **Self-improvement is bounded.** Meta-review sharpens later rounds but can't escape the base model's blind spots (the Self-Refine ceiling).
- **Quality scales with ingestion quality.** Clean digital docs work well. Scanned PDFs, audio, and JS-heavy pages need heavier optional extractors and may lose fidelity.
- **Codex gate is not yet verified.** The Claude Code gate runs via a `PreToolUse` hook. On Codex, `approval_mode=prompt` on MCP tool calls is unverified as of Codex v0.3 — until confirmed, the in-code `assert_approved()` is the only guaranteed gate on the Codex path.
- **Markdown memory is small-scale only.** It's the right substrate under ~100 sessions. Beyond that you'd want a vector-DB backend Catfish deliberately doesn't ship.

---

The rest of this README is feature depth — the full loop, the codebase map, the persona system, the skills, and the schema rules. The elemental story above is the whole product; the below is how each part works.

## How the reap works: the tournament loop

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
   → accepted + reviewed decision  →  compressed Note  →  back into the spine
```

The scorer is **Bradley-Terry, not Elo**. Pairwise LLM judgments are non-transitive — A beats B beats C beats A, [documented at ICML 2025](https://arxiv.org/abs/2502.14074) — which breaks Elo's core assumption. LMSYS migrated Chatbot Arena from Elo to Bradley-Terry for stable confidence intervals; that's the same scorer that handles non-transitive cycles. We implement the MLE fit in ~50 lines of pure Python.

## What's shipped in this release: the loop closes

Two changes turn the one-shot tournament into the sow → reap → feedback loop above.

- **Closed loop — decisions become wisdom.** An accepted decision that you've *reviewed* is re-ingested as a `type="decision"` Note into the MoC spine, carrying the **domain tags** of the card it came from (e.g. `variety`, `value`, `health`). Personas reap it through their normal `tags_any` filter — so last week's lunch calls surface to the skeptic's first-principles lens on the next run. Each decision surfaces as a **compressed summary** (problem + choice + rationale + outcome), not raw re-citable evidence — it returns as wisdom, not noise. The feedback is **gated on your review**: a decision you haven't reviewed doesn't re-enter the corpus.
- **Incremental sow — the corpus grows in place.** `build_spine` now **upserts by `source_hash`** instead of rebuilding from scratch. Add a memo, re-run, and the spine grows and updates the changed notes without a full rebuild — the corpus accumulates across runs.

## Also: map a codebase by what it does

Point Catfish at a repo and it builds a **logic map** — organized by capability and flow, not file tree — where each capability carries a one-line **business-value** translation (`auth → account security → churn prevention`). Structure is extracted deterministically (stdlib `ast` / ripgrep in core; tree-sitter in the optional `[code]` extra); the business-value lines are *proposals you confirm*, never asserted as fact. It makes a codebase legible to a PM and lets a decision card weigh a technical call by what it actually protects.

Catfish maps **itself**: `catfish map src` writes a [Foam](https://foambubble.github.io/foam/)-compatible wiki to [wiki/](wiki/) in **two layers** — an engineer dependency graph ([wiki/index.md](wiki/index.md)) and a PM business-capability graph ([wiki/business.md](wiki/business.md)) — both as Mermaid that renders on GitHub, no extension needed.

The decision loop itself is also markdown: `catfish architecture` distills the **cognitive architecture** into [cognition/index.md](cognition/index.md). Each stage's identity lives in an editable `.md` anchor (`cognition/*.md`) that's re-injected every round so the agents can't drift — **context engineering as plain files**, not a vector store.

## Choose your panel (personas have moods)

`catfish roster` shows a character-select of personas × moods. Assemble the critic panel for a run:

```bash
catfish tournament examples/lunch/inbox "<question>" --config-dir examples/lunch --critics nutritionist:concerned,budget:frugal,skeptic:grumpy
```

A skeptic in a grumpy mood nitpicks harder and surfaces more edge cases — a *severity/diversity dial*, not an accuracy boost. Personas can also carry documentation they "know" (a persona that has read your style guide or test playbook), injected as bounded reference. Any emotional state works; unknown moods are used literally.

Ships with the **Project Riley** ([arXiv:2505.20521](https://arxiv.org/abs/2505.20521)) Inside-Out emotion characters as a starter panel — `--critics riley` runs Joy, Sadness, Fear, Anger, Disgust. (`anger` carries the Devil's-Advocate role, because the [research](https://openreview.net/forum?id=mxBmj5LYU2) says an explicit dissent *role*, not emotion, is what actually breaks consensus — mood rides on top.)

## Skills (Claude Code / Codex)

Installed as a plugin, Catfish ships four skills your host invokes by intent — nothing to memorize:

- **tournament** — turn a folder of context + a hard question into one decision card. *("decide X vs Y", "make the call on …")*
- **scout** — research an open question with parallel sub-agents over your corpus, then optionally hand the framing to a tournament. *("scout this", "dig into X before we decide")*
- **retro** — review a past decision: what the panel warned about vs. what actually happened. *("run a retro", "how did decision X turn out?")*
- **map** — map a codebase by capability and business value, not file tree. *("what does this repo do?")*

Each is plain markdown under [skills/](skills/) — edit a `SKILL.md` to change how it behaves. The Linear write stays gated no matter which skill drives it.

## Terseness is a schema rule, not a style

Every card field has a hard word cap, validated as **structured output** before the card is written. A card that runs long is rejected and regenerated shorter. Verbosity creep is a known failure mode of recursive LLM loops, so the cap is structural.

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

One run is roughly **40–60 LLM calls, under $0.50, under a minute.**

**Install from source** (PyPI publish is on the roadmap):
```bash
git clone <your-fork> catfish && cd catfish
pip install -e .          # puts `catfish` on your PATH
```
For Claude Code / Codex, point the host at the bundled `.mcp.json` (MCP wiring); the human-approval gate ships as a `PreToolUse` hook in `hooks/hooks.json`.

## Roadmap

The loop is closed; these sharpen it.

- **Persist persona lenses + a step-0 `catfish review` preview.** Lenses are computed live and thrown away each run. Persisting them lets you preview, before a tournament, exactly what each persona will reap from the current corpus — and keeps sow-time and review-time from drifting apart.
- **A real reap-ask `query_spine()` engine (optional).** Today reap-ask is the host-orchestrated `scout` skill. If host orchestration proves insufficient at scale, a flat-first `query_spine(question, spine_path, llm) -> list[{id, score}]` makes one ranking call over the flat spine — no hierarchy required.
- **Hierarchical PageIndex spine + optional TOON encoding.** The flat JSONL spine is right under a few hundred notes. Past that, a hierarchical PageIndex tree (and a TOON projection of the spine for ~40–60% token savings) lets a tournament traverse the corpus tree-first instead of loading every summary. ROI-positive only above ~500 notes — deliberately deferred.

## License

MIT. AGPL/GPL extractors (Firecrawl, Slackdump) are optional, self-hosted, and never imported by core, so the core stays clean-license.

---

*Catfish is applied AI engineering: it abstracts the methodology of Google's AI Co-Scientist ([arXiv:2502.18864](https://arxiv.org/abs/2502.18864)) into a tool you can install. It is grounded in the research, honest about its limits, and built to stay out of your way.*
