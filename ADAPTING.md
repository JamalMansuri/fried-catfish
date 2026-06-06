# Adapting Catfish to your domain

Catfish ships pointed at software / product / engineering decisions, but the engine is
domain-agnostic. **All domain coupling lives in config files, never in `src/`.** Retargeting it to
your sources — finance, legal, ops, hiring, anything — means editing two files and pointing the
CLI at them. If you find yourself editing Python to change the domain, stop: you've missed a seam.

There is a complete worked example in [`examples/lunch/`](examples/lunch/) — read it alongside
this guide; every step below has a concrete counterpart there.

---

## The seams, in the order you should touch them

### 1. `config/tags.yaml` — the domain vocabulary  *(edit first)*
A flat `keyword: tag` map. At ingest time, any note whose text contains a (lowercased) keyword gets
the corresponding tag. Tags are how persona lenses find the notes that concern them.

```yaml
# default (software/eng)            # retargeted (lunch)
auth: auth                          fresh: health
billing: billing            ──►     cheap: cost
migrat: migration                   twice: variety
launch: launch                      walk: convenience
```

Keep the keys as substrings (`migrat` catches *migrate/migration/migrating*; `cheap` catches
*cheap/cheaper/cheapest*). Keep the tag set small — a dozen tags is plenty.

> **Load-bearing coupling:** the tags you produce here MUST match the `filter.tags_any` lists in
> `personas/*.yaml` (step 2). They are a matched pair. New tags with no matching persona filter are
> invisible; persona filters referencing tags you never produce match nothing.

### 2. `personas/*.yaml` — the critic panel  *(edit second, to match step 1)*
One YAML file per critic. Rewrite `role`, `goal`, `utility_fn`, and especially `filter.tags_any`
so the panel reflects who would actually argue about *your* decisions.

```yaml
id: skeptic
role: First-principles contrarian
goal: Question the whole frame — why a chain at all — and whether we're just repeating last week.
utility_fn: unexamined defaults and autopilot choices surfaced
mood: contrarian          # optional — a tone/severity dial, not an accuracy boost
filter:
  tags_any: [variety, value, health, convenience]   # <- must come from config/tags.yaml
```

Optional: a persona can `knowledge:` a glob of your own docs (e.g. `knowledge: [docs/sop.md]`), read
in as bounded reference — that's how you give a critic your playbook. See `personas/qa.yaml`.

### 3. `cognition/*.md` — usually leave alone
These markdown files are the *stage identities* of the loop (generation, reflection, ranking,
evolution, meta-review, supervisor), re-injected each round so the agents don't drift. The loop is
domain-agnostic — **you almost never edit these to change domain.** Only touch them if your domain
needs a fundamentally different generation mandate (rare). Skip this step by default.

### 4. `examples/<your-domain>/` — your sources
Drop your real notes / emails / transcripts / exported docs into a folder and point the CLI at it.
You don't have to put them under `examples/` — any folder works. Use
[`examples/lunch/`](examples/lunch/) as the template for a self-contained, shippable example.

### 5. Environment — runtime wiring (no domain coupling)
`CATFISH_LLM_API_KEY` (+ optional `CATFISH_MODEL`) for live runs; `CATFISH_LINEAR_TOKEN` /
`CATFISH_LINEAR_TEAM` if you want the gated Linear write. `CATFISH_DEMO=1` runs offline from canned
fixtures (note: the fixtures replay the lunch scenario, so the offline *card content* is always the
lunch card regardless of `--config-dir` — the retarget proves out in ingestion, tagging, and the
persona panel; a real card on your data needs a live key).

---

## Minimum viable retarget

Two files and one flag:

1. Write `your-domain/tags.yaml` (your vocabulary).
2. Write `your-domain/personas/*.yaml` (critics whose `tags_any` use those tags).
3. Run it:
   ```bash
   catfish ingest your-domain/inbox --config-dir your-domain          # check the tags landed
   catfish tournament your-domain/inbox "<your question>" --config-dir your-domain
   ```

`--config-dir` tells Catfish to read `tags.yaml` and `personas/` from that folder instead of the
repo defaults. **Verify it worked:** the `ingest` output should show your domain tags on the notes,
and the tournament run header should print your critic panel and a non-zero persona-lens count. If a
lens is empty, a tag in `tags.yaml` and a `filter.tags_any` in your personas don't agree — fix the
pair.

That's the whole contract. No `src/` edits.
