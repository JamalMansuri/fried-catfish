# Research Dossier — Tournament Abstraction Plugin

> Abstracting Google's **AI Co-Scientist** (Nature 2026, `s41586-026-10644-y`; arXiv:2502.18864)
> into a domain-general **idea/plan tournament** engine for project-management & technical decisions,
> packaged as a portable **Claude Code + Codex plugin**.
>
> Core loop: ingest anything → Map of Content → personas stamp perspective-maps →
> generate candidate plans → adversarial critique → pairwise tournament → evolve/recombine →
> meta-review → terse **decision cards** → human gate → Linear issue/story/sub-ticket tree.
>
> Compiled 2026-06-05 from 7 parallel research streams. Each item: what it is · URL · load-bearing insight.

---

## 0. Does this already exist? (LangSmith / LangChain question)

**No off-the-shelf product is this.** The *assembly* is the gap.

- **LangSmith** = eval/observability infra, NOT an app. Ships two primitives that map onto Co-Scientist:
  - Pairwise LLM-as-judge → = the **Ranking agent's pairwise debate**. https://www.langchain.com/blog/pairwise-evaluations-with-langsmith
  - Annotation queues (side-by-side human A/B, multi-reviewer) → = the **human thumbs-up gate**. https://www.langchain.com/langsmith/evaluation
  - It's the *scoring bench*, not the engine. Won't ingest→md, build MoC, run personas, or open tickets.
- **LangGraph** = build substrate (graph nodes=agents, HITL breakpoints, memory checkpoints). Closest framework to build ON. https://www.langchain.com/langgraph
- **Denario** = closest OSS analog to a co-scientist (deep-knowledge agents for scientific discovery) — but science, not PM, not a plugin. arXiv:2510.26887

| Layer | Off-the-shelf? | Where |
|---|---|---|
| Pairwise tournament scoring | ✅ primitive | LangSmith pairwise eval |
| Human approval gate | ✅ primitive | LangSmith annotation queues |
| Multi-agent orchestration | ✅ substrate | LangGraph / CrewAI |
| Ingest anything → md | ✅ tools | MarkItDown, Docling, WhisperX |
| MoC / navigable spine | ✅ tools | PageIndex, GraphRAG, TOON |
| Co-Scientist *loop* | ❌ | build it |
| Persona perspective-map stamping | ❌ | build it |
| Decision-cards → Linear tree | ❌ | build it |
| One portable Claude Code + Codex plugin | ❌ | build it |

---

## 1. Methodology & academic grounding

### Core architecture
**AI Co-Scientist** (Gottweis et al., Google DeepMind) — arXiv:2502.18864 · HTML: https://ar5iv.labs.arxiv.org/html/2502.18864
Multi-agent Gemini system; generate-debate-evolve via Elo tournament + persistent context memory. **Six agents + Supervisor (verbatim):**
- **Generation** — produces initial candidates, extends focus areas
- **Reflection** — simulates peer review; critiques correctness/quality/novelty
- **Ranking** — Elo tournament via pairwise simulated debate; new entries start Elo 1200; top-ranked get multi-turn debates, lower get single-turn
- **Proximity** — similarity graph; clusters; dedup; focuses comparisons on similar-tier candidates
- **Evolution** — generates *new* hypotheses (synthesis/analogy/simplification); **never mutates existing ones** (protects top-ranked)
- **Meta-review** — synthesizes patterns across reviews/debates; appends as context next round ("learning without backprop")
- **Supervisor** — orchestrates task queue, weights/samples agents, writes stats to context memory

Reuse: separate generation from evaluation; protect top-ranked from in-place mutation; proximity graph makes comparisons non-random/cheap; meta-review = prompt-only improvement signal between rounds.

### Multi-agent debate
- **Du et al., Multiagent Debate** (ICML 2024) — arXiv:2305.14325 · https://composable-models.github.io/llm_debate/ — multi-round debate cuts hallucination, improves reasoning, black-box. **Caveat: needs diversity or it's an echo chamber.**
- **ChatEval** — arXiv:2308.07201 — referee team w/ distinct personas/focuses; +10–16% human correlation. **Role diversity is load-bearing; don't give every critic the same generic prompt.**
- **Society of Mind** (Minsky 1986) — theoretical grounding for specialized competing agents. Cite as theory, not evidence.

### Self-improvement loops
- **Self-Refine** (NeurIPS 2023) — arXiv:2303.17651 · https://selfrefine.info/ — ~20% over one-shot. **Limit: bounded by model's own blind spots.**
- **Reflexion** (NeurIPS 2023) — arXiv:2303.11366 — verbal self-critique of failures as persistent memory. **Maps to meta-review: store loss rationales, not just W/L. Prune for long runs.**
- **Tree of Thoughts** (NeurIPS 2023) — arXiv:2305.10601 — branch+backtrack; 4%→74% on Game of 24. **Use selectively in Evolution; high cost.**

### LLM-as-judge + tournament scoring
- **MT-Bench / LLM-as-Judge** (Zheng) — arXiv:2306.05685 — 3 biases to design around: **position** (swap+average), **verbosity** (length-normalize), **self-preference** (use different-family judge).
- **Non-Transitivity in LLM-as-Judge** (ICML 2025) — arXiv:2502.14074 — pairwise judgments are non-transitive (A>B>C>A), **which breaks Elo's assumption.** Use **round-robin + Bradley-Terry**, not raw Elo accumulation. (Spearman 95.0→96.4; Kendall 82.1→86.3.) "Swim tournament" = cheaper approximation.
- **Chatbot Arena / LMSYS** — https://www.lmsys.org/blog/2023-05-03-arena/ — migrated Elo→Bradley-Terry MLE for stable CIs. **Adopt Bradley-Terry as default scorer.**
- **Self-Preference Bias** — arXiv:2410.21819 — judges favor low-perplexity (own-style) outputs, not quality. **Ensemble judges across model families.**

### Persona effects — HONEST picture
- **"When 'A Helpful Assistant' Is Not Really Helpful"** (EMNLP Findings 2024) — arXiv:2311.10054 — 162 personas, 4 families: **personas do NOT reliably improve performance** ("no better than random"). → Use distinct **evaluation criteria per agent** (what to measure), NOT character personas (who the agent is), when you want quality gains.

### Honest caveats (where these methods are weakest)
1. **No ground truth in open-ended domains.** Elo rank = relative persuasiveness among LLMs, not truth. PM has no wet-lab; risk of locally-coherent-but-wrong consensus is amplified. Keep a human as validator/selector.
2. **Judge bias compounds under recursion.** Verbosity bias → Evolution drifts toward length over substance across rounds. Round-robin + Bradley-Terry reduces, doesn't eliminate. No bias-free judge exists (2025).
3. **Persona/role assignment overclaims.** Debate gains are often vs weak baselines; named-expertise personas are directly falsified as a reliability lever. Practical ceiling is poorly characterized.

---

## 2. Persona & multi-agent frameworks

**Frameworks** (borrow patterns, not the dependency graphs):
- **AutoGen** — https://microsoft.github.io/autogen/ — conversational topologies. Borrow **nested-chat** (orchestrator spawns sub-convos per persona).
- **CAMEL** — https://www.camel-ai.org/ — role-play primitives. Borrow explicit role+task at convo start.
- **ChatDev** — https://github.com/OpenBMB/ChatDev — Borrow: personas stamp **concrete artifacts**, not opinions.
- **MetaGPT** — https://github.com/geekan/MetaGPT — Borrow **role→typed-output mapping** (risk matrix, plan diff, concern list).
- **CrewAI** — https://www.crewai.com/ — Borrow the **`(role, goal, backstory, tools)` persona schema** (cleanest declarative spec). Add `utility_function`.
- **LangGraph** — https://github.com/langchain-ai/langgraph — Borrow **typed shared-state** (tournament state object read/written by persona nodes, not chat history).
- **OpenAI Swarm → Agents SDK** — https://github.com/openai/openai-agents-python — closest to "plugin not framework". Borrow **handoff primitive** (~30 LOC) for persona routing.
- **Magentic-One** — Borrow **Orchestrator+ledger** pattern = the "tournament director" tracking which lenses fired.

**Generative Agents** (Park et al. 2023) — arXiv:2304.03442 — memory stream scored by **recency × importance × relevance**; reflection trees; persona = 1 paragraph of NL seeded as memories. Borrow importance-weighted retrieval (each persona has a different relevance profile) + a reflection step after stamping a map.

**Persona generation:**
- **PersonaHub** (Tencent) — arXiv:2406.20094 · HF: proj-persona/PersonaHub — Text-to-Persona: auto-generate personas from domain docs (tickets→user-pain persona, CVEs→adversary persona). Need ~10–50 high-coverage lenses, not 1B.
- **Persona is a Double-Edged Sword** — arXiv:2408.08631 — personas help ~15.75% / hurt ~13.78% on AQuA; MMLU drops. **Fix: Jekyll&Hyde ensemble** (run persona + neutral, pick better). +~10% across 12 datasets.
- **PRISM** — arXiv:2603.18507 — expert personas help alignment/tone (+17.7% safety) but damage knowledge accuracy (68.0 vs 71.6). **Persona length scales the damage → keep persona prompts short.**
- **Can LLM Agents Really Debate?** — arXiv:2511.07784 — strong **conformity bias**; role labels give minimal benefit. → enforce diversity **structurally** (run personas in parallel isolation, THEN tournament; don't let them see each other during generation).
- **Debate Only When Necessary (DOWN)** — arXiv:2504.05047 — gate debate on low confidence → 6× efficiency, less error propagation.
- **Lexical diversity of personas** — arXiv:2505.17390 — fine-grained backstories ≈ coarse role names on diversity. **Coarse roles ("skeptic","PM","security") suffice.**

**Plugin takeaways:** persona = `(role, goal, backstory, tools, utility_fn)`; typed artifacts not free text; orchestrator+ledger; importance-weighted retrieval per persona; seed personas from KB; persona+neutral ensemble for factual claims; confidence-gated debate. **Overkill:** full frameworks, reflection trees, 1B personas, mandatory multi-round debate, long persona descriptions.

---

## 3. Token-efficient formats & navigable spines

- **TOON** (Token-Oriented Object Notation) — https://github.com/toon-format/toon — YAML-indent + CSV-rows; lossless JSON round-trip; `[N]` length hint lets LLM verify completeness. **~60% fewer tokens than pretty JSON on uniform arrays** (2,518 vs 6,360 toks/100 records; one real case 62.7% savings); accuracy 76.4 vs 75.0 at -39.9% tokens. Wins on uniform tabular records; loses on deeply-nested irregular objects (compact JSON wins) and pure flat tables (CSV ~5–9% smaller). Include a one-shot example in prompt.
- **PageIndex** (Vectify) — https://github.com/VectifyAI/PageIndex · MCP: https://github.com/VectifyAI/pageindex-mcp · https://yuv.ai/blog/pageindex — vectorless tree-search RAG. Node = `{id,title,start_page,end_page,summary,children[]}`; LLM reasons down the tree (load index→pick branch→load branch). 98.7% on FinanceBench vs ~30–50% vector RAG. Wins single structured docs + traceability; loses on 1,000+ doc corpora. **Its node schema = our spine schema.**
- **GraphRAG** (Microsoft) — https://microsoft.github.io/graphrag/ — entity/relation extraction + Leiden community summaries; Global/Local/DRIFT search. 86% vs 32% baseline on enterprise. Cost cliff: $33k(2024)→$33(2025, LazyGraphRAG). **Overkill for our spine; borrow community-summary concept as tree-node summaries.** Schema: entities/relations/communities/text_units.
- **LLMLingua / LongLLMLingua** (Microsoft) — https://github.com/microsoft/LLMLingua — small-LM perplexity-based prompt compression, 3–20×; LongLLMLingua +21.4% on NQ at 4× fewer tokens. **Run on prose summaries / retrieved passages, NOT on an already-terse TOON spine.** Use question-aware mode.
- **JSONL** — one JSON/line; ~85% of pretty-JSON tokens (keys repeat every line). Fine fallback for **heterogeneous** records / external tooling; TOON beats it 40–60% on uniform schema.

**Format recommendation table:**
| Artifact | Format | Why |
|---|---|---|
| Human MoC | **Markdown** | humans navigate; free hierarchy from headers; not stuffed raw into prompts |
| Machine spine (uniform nodes) | **TOON** | 40–60% savings; LLM-verifiable count via `[N]` |
| Machine spine (heterogeneous) | **JSONL** | safe fallback, tooling compat |
| Per-node summaries (prose) | **MD prose, LLMLingua-compressed** | ≤3 sentences; tighten on retrieval |
| Tournament state (matches/scores) | **TOON** (uniform) / minified JSON (irregular) | tabular = TOON sweet spot |
| LLM structured *output* | **JSON** (constrained decode) | downstream parse reliability |
Rule: never pretty-JSON in a prompt; never YAML over TOON for uniform arrays; never re-encode prose as TOON.

---

## 4. Map of Content / knowledge-graph generation

**Concept:** MoC = living index note linking related notes (Nick Milo / LYT — https://www.linkingyourthinking.com/). vs Folders(=houses, one home) vs Tags(=signs) vs Links(=roads). MoCs become load-bearing >~200 notes. **Multi-homing** (one note in many MoCs) is the key affordance folders can't do. dsebastien guide: https://www.dsebastien.net/2022-05-15-maps-of-content/

**Zettelkasten for machine traversal:** atomicity, stable UIDs, **typed links** (supports/contradicts/elaborates → directed traversal + conflict detection), bidirectional backlinks, per-note summary field.
- **A-MEM** — arXiv:2502.12110 — ingesting a new note should **update existing nodes' metadata**, not append-only. (Strong single-paper claim; provisional.)

**Auto-generation OSS (Obsidian-centric):**
- **Smart Connections** — https://github.com/brianpetro/obsidian-smart-connections — local-first embeddings; surfaces (doesn't write) links → avoids link pollution.
- **Metadata Auto Classifier** — per-field prompts beat one global prompt.
- **LLM Tagger** — constrained tag vocab beats open-ended; hash-cache skips unchanged.
- **Notemd** — auto-injects `[[wikilinks]]` + auto-creates stub notes (bootstraps the graph).
- **Obsidian LLM Wiki** (green-dalii) — 3-layer `sources/`(read-only) → `wiki/`(regenerable) → `schema/`.
- **Note Linker** — proposes links for human confirmation (right default).
- **Khoj** / **Reor** / **Quartz** — second-brain search / local AI notes / publish-to-web.
- **KGGen** — arXiv:2502.09956 — SPO triples = minimal interoperable KG format.

**Perspective = filter predicate, NOT a copy.** InfraNodus / Capacities / Anytype: views-as-queries; Obsidian Canvas references paths not copies.

**Proposed MoC schema (frontmatter, every note):**
```yaml
id, title, aliases[], type(note|moc|source|concept|persona), tags[](constrained),
summary(1-sentence, required), created, modified, status(seedling|budding|evergreen),
links[]{id, rel(elaborates|supports|contradicts|cites|part-of|instance-of)}, sources[]
```
MoC note adds `covers[]` (machine-readable scope so an LLM routes a new note without reading the body). Auto-build `_graph_index.json` {nodes,edges,mocs,communities} = the machine API surface (read this, not 500 md files).

**Persona perspective-map = derived artifact** (`type: persona` note, ~100 lines YAML): `filter{tags_any,tags_exclude,types,status_min}`, `emphasis[]{tag,weight}`, `entry_mocs[]`, `annotations[]{id,note}`. Runtime: load index → apply filter → reweight edges → start at entry_mocs → inject annotations on fetch. Never copies content.

---

## 5. Universal ingestion → markdown

**Documents:**
- **MarkItDown** (MS, MIT) — https://github.com/microsoft/markitdown — 29+ formats, no GPU, ~100× faster than Docling, MCP built-in. 82% F1. **Default for clean digital Office docs.**
- **Docling** (IBM, MIT) — https://github.com/DS4SD/docling — 88% F1, TableFormer for merged/nested tables; **also handles EML/MSG/WAV/MP3/WebVTT**. Heavier/slower. **Best-quality local; single tool for mixed doc+email.**
- **Unstructured** (Apache-2.0) — 64+ types, ETL connectors; needs system deps; advanced chunking is paid. Production ETL mindset.
- **Pandoc** (GPL) — markup↔markup only, **cannot read PDFs**. DOCX/HTML/EPUB→MD.

**Web:** **Trafilatura** (Apache, 87% acc, local, no JS) default for batch; **Jina Reader** (`r.jina.ai`, self-hostable Docker) for JS-heavy single fetches; **Firecrawl** (AGPL, 129k★) only tool that crawls+extracts a whole site — self-host to dodge AGPL/billing.

**Audio/video:** **WhisperX** (BSD) — https://github.com/m-bain/whisperX — **only local tool with word-timestamps + speaker diarization** → meeting-quality; needs free HF token. **whisper.cpp** for Apple Silicon/edge (Metal; 60s audio in ~6s on M2 Pro). **faster-whisper** for Linux/CUDA servers.

**Email:** stdlib `email`+`html2text` (prefer text/plain) → YAML frontmatter; or Docling v2 (native EML/MSG).
**Chat:** Slack → **slackprep** (official exports) or **Slackdump** (non-admin, AGPL, ToS risk); Discord → **DiscordChatExporter** → JSON → MD serializer.
**All-in-one:** LlamaIndex (+LlamaParse for hard PDFs), RAGFlow, Haystack (auditable), txtai (lowest overhead).

**Normalized pipeline:** every output `.md` with frontmatter `{source_type, source_url, source_hash(sha256), date, participants[], title, extractor}`. Single normalization layer between extractors and storage; hash-dedup on `source_hash`. Per-type default: complex-PDF→Docling, simple→MarkItDown, web→Trafilatura, crawl→Firecrawl, meeting→WhisperX, email→stdlib/Docling.

---

## 6. Agent memory & handoff (markdown-based)

**Systems:**
- **MemGPT/Letta** — arXiv:2310.08560 — OS-style paging: core(always-in-context)/recall/archival. → **MEMORY.md = core; topic/session files = archival.**
- **Mem0** — arXiv:2504.19413 — temporal facts supersede w/ timestamps, don't overwrite. → versioned fact blocks w/ `updated:`.
- **Zep** — temporal KG; superseded facts retained w/ timestamps. → **dead-ends are load-bearing; date them, don't delete.**
- **LangMem** — procedural memory (agent rewrites own rules) = powerful+dangerous → human-direction blocks as explicit overrides.
- **Generative Agents** — recency×importance×relevance; importance scored at write-time (1–10) → survives compaction.
- **CoALA** — arXiv:2309.02427 — working/episodic/semantic/procedural. → keep raw logs (episodic) separate from curated handoffs (semantic).

**Compaction/handoff:** ACON (arXiv:2510.00615) — what-to-preserve learned from failure; "what-failed" is the primary compression signal. OpenAI Agents SDK handoffs — **every note must be cold-start parseable** (zero other context). Claude Code CLAUDE.md/MEMORY.md — 200-line/25KB load cap → **index is pointers, not content; load-on-read**. AGENTS.md = Codex equivalent.

**Failure memory:** Reflexion — first-person corrective ("In next trial I will…"), bounded buffer Ω≤3. ExpeL — contrast success vs failure → rules of thumb. MPR (arXiv:2509.03990) — graduate episodic→predicate rules w/ confidence. AgentErrorTaxonomy (arXiv:2509.25370) — log which module failed (memory/reflection/planning/action/system) + the cascade.

**MD-files vs vector DB:** files win on auditability/governance/simplicity/forced-curation for single-agent + ≤~100 sessions; vector DB wins at multi-agent/millions scale.

**Proposed memory layout:**
```
.memory/
  SESSION_INDEX.md   # always loaded, ≤150 lines: Active Threads (links+status), @RULES.md, load convention
  sessions/YYYY-MM-DD_session-NN.md
  RULES.md           # graduated from failures recurring ≥2 sessions; [HIGH|MED|LOW] + source sessions
```
Session handoff frontmatter: `session, status(open|closed|blocked), objective, model, started, last-updated, failure-types[], importance(1-10)`. Body sections: **Objective · What Was Attempted · What Failed/Dead Ends · Human Directions/Decisions · Open Threads · Next Step(first-person, concrete) · Notes.**
Principles: cold-start parseable; preserve dead-ends; human directions = named override section; index=pointers; importance at write-time; promote recurring rules; bounded buffer (≤2–3 session files/context).

---

## 7. Packaging + Linear + decision cards

### Dual Claude Code + Codex packaging
**MCP server is the single portable artifact** (both hosts speak MCP). Thin host layers wire it.
- **Claude Code plugin** — https://code.claude.com/docs/en/plugins-reference — dir w/ `plugin.json`, `skills/*/SKILL.md`, `agents/*.md`, `hooks/hooks.json`, `.mcp.json`. SKILL.md frontmatter: `name, description(the trigger signal — only thing always loaded), disable-model-invocation, allowed-tools`. `` !`cmd` `` inlines shell output. **PreToolUse hook = native approval gate.** Skills follow cross-tool standard https://agentskills.io
- **Codex** — MCP via `~/.codex/config.toml` `[mcp_servers.<id>]`; `approval_mode="prompt"` per server = approval gate; **AGENTS.md** = CLAUDE.md equivalent (3-tier discovery). Codex adopted plugins (MCP transport) by 2026.
- One-step load: `claude plugin install …` / `codex mcp add …`. Same binary both sides.

### Linear / ticketing
- MCP servers: **dvcrn/mcp-server-linear** (multi-workspace, full fields) & **cosmix/linear-mcp**. `create_issue{title,description,teamId,parentId,status,priority,assigneeId,labelIds}`.
- **Hierarchy = recursive `parentId`** (no fixed epic/story/subtask types). 3-level tree: create parent → capture UUID → create children w/ `parentId=<UUID>`. **`parentId` is the UUID, not "ENG-42".** labels+projects = cross-cutting.
- **Approval gate before creation** (issues notify on creation, hard to un-send): Claude Code PreToolUse hook matching `create_issue` / Codex `approval_mode:prompt`. Use **pre-execution pause**, not post-review.
- Jira: no official MCP; REST `POST /rest/api/3/issue` w/ `parent.id`. Linear model is cleaner.

### Decision cards
- **MADR 4.0** (https://adr.github.io/madr/) is the backbone. Use its **"Pros and Cons of the Options"** structure (`Good/Neutral/Bad, because {arg}`) verbatim as the comparison. Y-statement = terse form. A decision card = an ADR with `status: proposed` + a human gate before `accepted`.
- **Weighted decision matrix** (weight×score, 4–6 criteria fits 6 rows, ~10s read). **Elicit weights from human BEFORE scoring** (prevents rationalization). RICE is for single-dimension backlog, not lateral option comparison.
- **HITL UX:** show only what changed the decision, not the reasoning chain; <2s round-trip; thumbs-down → persistent blocklist, thumbs-up → ephemeral approval. AG-UI interrupt/resume protocol; LangGraph human_review node.

**Proposed decision-card schema:**
```yaml
id: dc-<ulid>; status: proposed|accepted|rejected|superseded; created_at; decision_makers[]
problem_statement: |   # what's broken + what forces a choice now
first_principles: |    # 1-3 irreducible constraints the solution must satisfy
options:
  - {id, name, solution, trade_offs:{good[],neutral[],bad[]}, weighted_score}
criteria_weights: {…}  # elicited from human BEFORE scoring
recommendation: {option, rationale(1 sentence: decisive criterion)}
human_decision: {decided_by, decided_at, choice(A|B|defer|reject_all), notes}  # gate; null blocks Linear
linear: {parent_issue_id, story_ids[], sub_issue_ids[]}  # written back after approval
```

---

## Open design tensions to resolve in the spec
1. **Elo vs Bradley-Terry** — non-transitivity says use round-robin+BT; cost says use sparing pairwise. Resolve by tier (BT on finalists, cheap single-vote early).
2. **Personas: diversity vs accuracy damage** — coarse roles + persona/neutral ensemble + parallel isolation before tournament.
3. **No ground truth in PM** — keep human as validator; the engine produces *stress-tested options*, not *verified answers*. State this loudly in the README.
4. **Verbosity bias → length creep** — length-normalize judge; enforce card terseness as a hard schema constraint.
5. **Build-on-LangGraph vs zero-dep plugin** — MCP server core (portable) + thin skills/hooks; borrow patterns from frameworks without their dependency graphs.
6. **Deterministic vs LLM in code MoC** — L0/L1 (ripgrep+stdlib) are ground truth and live in core; L2 behavior summaries + `value{}` are human-gated proposals; tree-sitter/PageRank/Leiden/CPG all behind the opt-in `[code]` extra, never imported by core, to preserve the tiny-core north star.
7. **Consensus: AI-lens agreement vs human-stakeholder agreement** — never one blended number. Resolved in SPEC "Consensus layer": an advisory lens-convergence *chip* (no gate power) + a human stakeholder-agreement *tally* (the only gate), strict-plurality with ties hard-blocking, dissent preserved (Habermas predict-then-confirm + Polis bridging, §9). Open sub-question: default quorum/threshold and whether 1-of-1 is a valid floor.

---

## 8. Codebase logic-MoC + business-value translation (added 2026-06-05, 2nd workflow)

**Prior art — code maps:** aider repo map (tree-sitter + PageRank, Apache-2.0, local — steal the ranking heuristic) https://aider.chat/docs/repomap.html · Codebase-Memory (tree-sitter→SQLite property graph, arXiv:2603.27277 — closest substrate; SQLite not Neo4j; Louvain "communities" ≈ modules; 83% vs 92% file-explore) · DeepWiki (Cognition, cloud-only — proves LLM-over-repo narrative per module) https://deepwiki.com · Sourcegraph/Cody SCIP (precise symbol graph, enterprise) · GitDiagram/Swark (LLM→Mermaid, hallucinates — "first render" only; Swark MIT ~200 LOC pattern) · repomix/gitingest/code2prompt (repo→single-file serializers, MIT — ingest not map) · code2flow (AST call graph, MIT) · Potpie (Neo4j full graph, Apache-2.0 — heavy stack; replicate schema in SQLite) · CodeSee (annotation layer = the human-stamp model) · CodeScene (git-churn "business risk" — indirect proxy).

**Logic extraction:** Joern/CPG (AST+CFG+PDG+call, most complete static layer; marks unresolved as external/empty) https://cpg.joern.io · tree-sitter-graph (66 langs, deterministic, seconds, no LLM/network) · CFG/DFG (function-granularity; cross-module stitching is where accuracy degrades) · Reliable Graph-RAG arXiv:2601.08773 (deterministic AST-KG beats LLM-extracted KG on correctness; vector-only highest hallucination) · C4 model (Context→Container→Component→Code = leveled logical map; L1 Context = business layer; matches MoC spine hierarchy; auto-extraction structurally-right/semantically-wrong without human annotation) https://c4model.com · DDD bounded contexts (boundaries = capability boundaries; reliable only where DDD was applied).

**Business-value translation:** business capability maps / TOGAF capability-based planning / ArchiMate / LeanIX (chain: code→app→capability→objective→revenue/cost/risk; TOGAF stops at app layer — last mile to code needs AST/LLM) · value stream mapping (Jellyfish maps git+Jira→OKRs without story points — closest prior art, but work-items not code structures) · DDD ubiquitous language (code↔business bridge where applied) · tech-debt-in-business-terms (Tracy arXiv:1908.01347, SQALE, CodeScene CodeHealth, velocity-tax framing) · RICE/ICE at node level. **No tool spans code-structure → capability → OKR end-to-end — that's the gap.**

**Chosen hybrid architecture:** deterministic skeleton (ripgrep core / tree-sitter `[code]` extra) → connected-components clustering → bounded per-cluster LLM summarization + value proposal → **human gate** → spine. Deterministic = ground truth; LLM behavior + value = gated proposals.

**Honest limits:** static analysis = structure not intent; LLM summaries pattern-matched not reasoned (same summary for semantically-changed fn ~30-40%; API hallucination 8-40%; severity ±1.8/10 across runs; accuracy degrades sharply with file count — CodeMap >90% ≤44 files, lower at 668+); business value not derivable from source (needs product/cohort data) so human confirmation is load-bearing; naming unreliable in legacy codebases (LLM most confidently wrong there); language coverage uneven (ripgrep coarse/false-positive edges, tree-sitter per-language grammar gaps → graceful downgrade to ripgrep-only).

---

## 9. Group social-dynamics & deliberation frontier (added 2026-06-05, 3rd workflow)

> Answers a standing question: *is there a research frontier on engineering group social dynamics so multi-agent deliberation resembles real human communication?* Yes — and it splits into **three programs.** Catfish lives in a 4th (judge/tournament mechanics); it should borrow from program 2, treat program 3 as its safety spec, and explicitly **refuse** program 1.

### Program 1 — Simulation (make agents resemble real people/societies). *Goal: study/predict humans — NOT our goal; the trap.*
- **Generative Agents / Smallville** — Park 2023, arXiv:2304.03442 (already §2). Memory-stream agents in a sandbox town.
- **Generative Agent Simulations of 1,000 People** — Park, arXiv:2411.10109 — 2-hr interviews → agents reproduce a person's survey answers **85% as well as the person does two weeks later.** That 85% is the honest *ceiling* of "resembling a real person," and it needs real interview data you won't have pre-decision.
- **Concordia** — DeepMind, arXiv:2312.03664 — "Game Master" referees a language-mediated society; cleanest generative agent-based-modeling (GABM) framework.
- **Project Sid** — Altera/FRL, arXiv:2411.00114 — 1000+ Minecraft agents grew an economy, a constitution they voted to amend, and a religion. PIANO architecture.
- **OASIS** (~1M-agent social-media sim) / **SocioVerse** (arXiv:2504.10157, 10M real-user world model) — the scale frontier.
- **Take:** do **not** sell Catfish personas as "simulated stakeholders." Generic role-personas perform ≈ random (§1, §2); even interview-grounded agents cap at 85% and collapse on contested topics. Personas = *diverse evaluation lenses*, not *people*.

### Program 2 — Mediation / collective intelligence (help a *real* group converge). *Closest match to Catfish's consensus layer.*
- **The Habermas Machine** — Tessler et al., **Science 2024**, doi:10.1126/science.adq2852 · code https://github.com/google-deepmind/habermas_machine — LLM "caucus mediator." **Mechanism to steal = predict-then-confirm:** a Personalized Reward Model (Bradley-Terry over each person's pairwise prefs, conditioned on their own opinion/critique) **predicts** every member's ranking of 16 candidate statements; rankings aggregated by the **Schulze method** (clone-independent — near-dup statements don't split the vote) to pick the statement maximizing *broad endorsement*, not majority. 5,734 UK participants; beat human mediators 56–44; group-agreement index **+~8pp.** **The predicted number is a selection signal only — every scientific claim rests on real human ratings afterward.** Caveats: a preference proxy is gamed by length (HM statements ~20% longer); "agreement" can be settled-disagreement, not opinion change; miscalibrates out-of-distribution; aggregation can underweight minorities.
- **Polis + Collective Constitutional AI** — https://compdemocracy.org/group-informed-consensus · Anthropic CCAI (~1000 US adults via Polis). **Bridging math to steal:** consensus = **product of per-cluster agreement** `GIC(c)=∏_g p_g`, with `p_g=(agrees_g+1)/(votes_g+2)`. A product behaves like an AND/min gate — *one* small dissenting cluster multiplicatively tanks the score → built-in **minority veto;** selects ~70–80% across *all* groups over 90% in one. Minority surfacing is a *separate* metric (**Representativeness** = inside/outside agree-ratio). Never one global %: a **per-group grid + each group's distinctive concerns.** Caveats: only ranks statements people wrote (agenda-dependent); **rewards vagueness** (platitudes bridge easier than actionable clauses); bridging content is rare (<10% in Community Notes); the % is conditional on the discovered clusters.
- **Take for Catfish:** *stakeholder agreement* should use a real social-choice rule (Schulze / strict-plurality-with-margin) over **human** votes, preserve `dissent`, and may show an explicitly-fenced *predicted* number as triage only — never as the gate. (Implemented in SPEC "Consensus layer.")

### Program 3 — Social dynamics as failure modes (when groups go wrong). *Goal: characterize/avoid the pathologies — our safety spec.*
- **Group conformity in multi-agent LLMs** — ACL Findings 2025 / arXiv:2506.01332 — neutral agents conform **63%** to a 2:1 majority, **83%** when one side looks smarter; consensus *strengthens each round even when no agent was confident.*
- **Correlated errors** — arXiv:2506.07962 — same-family models agree ~60% even when both wrong → N personas act like **far fewer effective votes** (down-weight same-family; show effective-N).
- **Self-preference / verbosity bias in LLM-as-judge** — arXiv:2410.21819 — judges favor own-style/low-perplexity outputs; anonymization doesn't kill it (it runs on familiarity). **Toxic agreement / group polarization** — arXiv:2512.04691.
- **Melting Pot** — DeepMind — 50+ MARL substrates for cooperation/defection/trust; the game-theory backbone. **Meta CICERO** (Science 2022) — human-level negotiation/alliance-building in Diplomacy.
- **Take:** this is the rigorous version of §2's conformity caveat. It justifies **parallel isolation before the tournament** (already in the loop) and the consensus layer's rule that an AI "agreement" number is an **upper bound capped at the human inter-annotator ceiling**, never P(correct).

### Forecasting human agreement — the honest limit on any "predicted %"
Silicon sampling (Argyle, arXiv:2209.06899) ~57% raw and produces caricatures; interview-grounded tops at ~85% (arXiv:2411.10109) but needs data you lack pre-vote; direct vote-prediction from a partial matrix (Polis, arXiv:2306.11932) is best-calibrated. **Mode collapse on contested topics** (OpinionQA, arXiv:2303.17548) → split issues look like false consensus; minorities predicted worst. Wrap any forecast in prediction-powered inference (arXiv:2502.17773) and **report a band, never a point.**

**Net:** Catfish is a persuasion tournament (program 4). The frontier the operator sensed is consensus *mediation* (program 2). Grafting the Habermas/bridging idea onto the human-vote layer — predict-then-confirm, product-not-mean, dissent preserved — is the highest-value borrow; the "simulate real humans" dream (program 1) is the trap to stay out of.
