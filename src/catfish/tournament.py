"""The tournament engine: generate -> reflect -> rank -> evolve -> meta-review.

Scoring is Bradley-Terry MLE (pure Python), NOT raw Elo: pairwise LLM judgments are
non-transitive (arXiv:2502.14074), which breaks Elo's transitivity assumption. Position bias
is handled by judging every pair twice with sides swapped and averaging.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from . import cognition as _cognition
from . import llm as _llm
from . import personas as _personas
from .models import Candidate, Critique, MatchRecord, MetaReview, Persona, PerspectiveArtifact

CRITIC_ROLES = ["skeptic", "pm", "security", "neutral"]


# --------------------------------------------------------------- Bradley-Terry

def bradley_terry(items, matches, iters: int = 500, tol: float = 1e-10) -> dict:
    """MM (minorization-maximization) fit with a symmetric prior.

    matches: iterable of (a_id, b_id, outcome) with outcome in {"a","b","tie"}.
    Regularization: each item gets +1 virtual win and +1 virtual loss vs a fixed anchor of
    strength 1.0, so an undefeated/winless candidate does not diverge. Returns strengths p_i;
    normalized to geometric mean 1 for identifiability.
    """
    items = list(items)
    if not items:
        return {}
    wins = {i: 0.0 for i in items}
    games = {}  # frozenset({i,j}) -> count
    for a, b, o in matches:
        if a not in wins or b not in wins:
            continue
        key = frozenset((a, b))
        games[key] = games.get(key, 0.0) + 1.0
        if o == "a":
            wins[a] += 1.0
        elif o == "b":
            wins[b] += 1.0
        else:
            wins[a] += 0.5
            wins[b] += 0.5

    p = {i: 1.0 for i in items}
    for _ in range(iters):
        new = {}
        for i in items:
            denom = 2.0 / (p[i] + 1.0)  # virtual: 2 games vs anchor strength 1.0
            for j in items:
                if j == i:
                    continue
                n = games.get(frozenset((i, j)), 0.0)
                if n > 0:
                    denom += n / (p[i] + p[j])
            num = wins[i] + 1.0          # +1 virtual win
            new[i] = num / denom if denom > 0 else p[i]
        gm = math.exp(sum(math.log(v) for v in new.values()) / len(new))
        new = {i: v / gm for i, v in new.items()}
        diff = max(abs(new[i] - p[i]) for i in items)
        p = new
        if diff < tol:
            break
    return p


def softmax_scores(finalists) -> dict:
    """Map BT strengths to [0,1] via softmax over finalists (= p_i / sum p over the set)."""
    strengths = {f.id: (f.bt_score if f.bt_score and f.bt_score > 0 else 1.0) for f in finalists}
    total = sum(strengths.values()) or 1.0
    return {fid: s / total for fid, s in strengths.items()}


# --------------------------------------------------------------- prompt builders
# (Used by the live backend; FakeLLM ignores prompt text and routes on `task`.)

def _persona_context(perspectives) -> str:
    if not perspectives:
        return "(no project context ingested)"
    return "\n".join(p.as_context() for p in perspectives)


def _gen_prompt(question, perspectives, meta) -> str:
    focus = f"\nFocus from prior round: {meta.next_round_focus}" if meta else ""
    return (
        f"Decision to make:\n{question}\n\nProject context:\n{_persona_context(perspectives)}{focus}\n\n"
        "Generate 4 candidate plans that differ on first-principle trade-offs, not phrasing. "
        'Return JSON: [{"name": "<=4 words", "text": "<=60 words"}].'
    )


def _reflect_user_prompt(question, c, grounding: str = "") -> str:
    g = f"\n\n{grounding}" if grounding else ""
    return (
        f"Critique this plan for the decision: {question}\n\n"
        f"Plan '{c.name}': {c.text}{g}\n\n"
        "Name the single most likely-wrong load-bearing assumption or omission, <=25 words. "
        "Ground it in the evidence above where one applies; do not invent facts beyond it."
    )


def _rank_prompt(question, a, b) -> str:
    return (
        f"Decision: {question}\n\nPlan A '{a.name}': {a.text}\nPlan B '{b.name}': {b.text}\n\n"
        "Which better satisfies the decision's first principles? Ignore length. Answer only: A, B, or TIE."
    )


def _meta_prompt(question, active) -> str:
    listing = "\n".join(f"- {c.name}: {c.text}" for c in active)
    return (
        f"Decision: {question}\nCandidates:\n{listing}\n\n"
        'Return JSON: {"recurring_concerns":[...],"pattern_gaps":[...],"next_round_focus":"<=25 words"}.'
    )


def _evolve_prompt(question, survivors, meta) -> str:
    listing = "\n".join(f"- {c.name}: {c.text}" for c in survivors)
    return (
        f"Decision: {question}\nTop survivors:\n{listing}\nFocus: {meta.next_round_focus}\n\n"
        'Synthesize 0-1 genuinely new plan combining their strengths. Return JSON: '
        '[{"name":"...","text":"..."}] or [].'
    )


def _card_prompt(question, finalists) -> str:
    listing = "\n".join(f"- {c.name}: {c.text}" for c in finalists)
    return (
        f"Decision: {question}\nFinalist plans:\n{listing}\n\n"
        "Return JSON with: problem_statement (<=30 words), first_principles (1-3, each <=20 words), "
        'trade_offs (object keyed by plan name -> {good,neutral,bad}, each <=15 words), '
        'recommendation {option_name, rationale (<=20 words)}.'
    )


# --------------------------------------------------------------- match running

def _judge_pair(question, a, b, llm, rnd, tier, judge_system=None) -> tuple[str, str, str]:
    """Judge a,b twice with sides swapped; average. Returns (a_id, b_id, outcome a|b|tie)."""
    r1 = llm.complete(_llm.RANK, _rank_prompt(question, a, b), system=judge_system,
                      meta={"a_name": a.name, "b_name": b.name})
    r2 = llm.complete(_llm.RANK, _rank_prompt(question, b, a), system=judge_system,
                      meta={"a_name": b.name, "b_name": a.name})
    # r2 is from b's perspective as "A"; translate back to a/b on the (a,b) frame
    score = 0  # >0 => a, <0 => b
    score += {"A": 1, "B": -1, "TIE": 0}.get(str(r1).strip().upper(), 0)
    score += {"A": -1, "B": 1, "TIE": 0}.get(str(r2).strip().upper(), 0)
    outcome = "a" if score > 0 else ("b" if score < 0 else "tie")
    judge = getattr(llm, "name", "llm")
    om = {"a": ("win", "loss"), "b": ("loss", "win"), "tie": ("tie", "tie")}[outcome]
    a.match_record.append(MatchRecord(b.id, om[0], judge, rnd, tier))
    b.match_record.append(MatchRecord(a.id, om[1], judge, rnd, tier))
    return (a.id, b.id, outcome)


def _run_round_robin(question, group, llm, rnd, tier, judge_system=None):
    matches = []
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            matches.append(_judge_pair(question, group[i], group[j], llm, rnd, tier, judge_system))
    return matches


# --------------------------------------------------------------- orchestration

@dataclass
class TournamentResult:
    card_inputs: dict
    candidates: list
    finalists: list
    metas: list
    judge_name: str


def run_tournament(question, perspectives, llm, *, critics=None, knowledge_base=".",
                   cognition_dir="cognition", max_rounds: int = 2, finalist_count: int = 3,
                   gen_count: int = 4) -> TournamentResult:
    if critics is None:
        critics = [Persona(id=r, role=f"{r.capitalize()} reviewer",
                           goal=f"Critique strictly from a {r} angle.", utility_fn=f"{r} concerns")
                   for r in CRITIC_ROLES]
    knowledge_map = {c.id: _personas.load_knowledge(c, knowledge_base) for c in critics}
    # Ground each critic in the MoC view its own persona stamped (parallel-isolation evidence).
    persp_by_id = {p.persona_id: p for p in (perspectives or [])}

    # immutable stage identities (HDE anti-drift, the simple way): re-injected every round
    def _anchor(stage):
        return _cognition.load_cognition(stage, cognition_dir)
    gen_anchor, evo_anchor, meta_anchor, rank_anchor = (
        _anchor("generation"), _anchor("evolution"), _anchor("meta-review"), _anchor("ranking"))

    # Grounding set: the union of source notes every persona lens surfaced. Generation reasons over
    # the combined persona context, so this is the honest grounding set for generated plans. It is
    # "what was in the room", not a verified per-claim derivation.
    provenance = sorted({nid for p in (perspectives or []) for nid in p.note_ids})

    candidates: list[Candidate] = []
    n = [0]

    def _new(name, text, rnd, source, note_ids):
        n[0] += 1
        return Candidate(id=f"cand-{n[0]:04d}", name=name, text=text, round_created=rnd,
                         source=source, note_ids=sorted(set(note_ids)))

    raw = llm.complete(_llm.GENERATE, _gen_prompt(question, perspectives, None),
                       system=gen_anchor, json=True)
    for c in raw[:gen_count]:
        candidates.append(_new(c["name"], c["text"], 0, "generation", provenance))

    metas: list[MetaReview] = []
    last_meta = None
    for rnd in range(max_rounds):
        active = [c for c in candidates if c.status == "active"]
        # Reflection — each critic (role + mood + known docs + the MoC view it stamped) in parallel isolation
        for c in active:
            for critic in critics:
                pa = persp_by_id.get(critic.id)
                grounding = ""
                if pa and pa.highlights:
                    ev = "\n".join(f"- {h}" for h in pa.highlights)
                    grounding = f"Evidence you surfaced from the project:\n{ev}"
                sysp = critic.system_prompt(mood_modifier=_personas.mood_modifier(critic.mood),
                                            knowledge=knowledge_map.get(critic.id, ""))
                txt = llm.complete(_llm.REFLECT, _reflect_user_prompt(question, c, grounding),
                                   system=sysp, meta={"name": c.name, "role": critic.id})
                c.critiques.append(Critique(critic.id, str(txt), rnd))
        # Ranking — early tier, all pairs, position-swapped
        _run_round_robin(question, active, llm, rnd, "early", rank_anchor)
        # Meta-review
        m = llm.complete(_llm.META, _meta_prompt(question, active), system=meta_anchor, json=True)
        last_meta = MetaReview(rnd, m.get("recurring_concerns", []), m.get("pattern_gaps", []),
                               m.get("bias_flags", []), m.get("next_round_focus", ""))
        metas.append(last_meta)
        # Supervisor — prune bottom, never below finalist_count
        active.sort(key=lambda c: c.wins(), reverse=True)
        for c in active[finalist_count:]:
            if len([x for x in candidates if x.status != "pruned"]) > finalist_count:
                c.status = "pruned"
        # Evolution (not on the last round). An evolved plan is synthesized from its survivor
        # parents and never sees the notes directly, so its grounding is the union of the survivors
        # it was built from — inherited lineage, not the global set.
        if rnd < max_rounds - 1:
            survivors = [c for c in candidates if c.status == "active"]
            evo_prov = sorted({nid for s in survivors for nid in s.note_ids})
            newc = llm.complete(_llm.EVOLVE, _evolve_prompt(question, survivors, last_meta),
                                system=evo_anchor, json=True)
            for c in (newc or []):
                candidates.append(_new(c["name"], c["text"], rnd + 1, "evolution", evo_prov))

    # Finalists — full round-robin + Bradley-Terry
    pool = [c for c in candidates if c.status != "pruned"]
    pool.sort(key=lambda c: c.wins(), reverse=True)
    finalists = pool[:finalist_count]
    for f in finalists:
        f.status = "finalist"
    fmatches = _run_round_robin(question, finalists, llm, max_rounds, "finalist", rank_anchor)
    strengths = bradley_terry([f.id for f in finalists], fmatches)
    for f in finalists:
        f.bt_score = strengths.get(f.id, 1.0)
    scores = softmax_scores(finalists)
    for f in finalists:
        f.bt_score = scores[f.id]
    finalists.sort(key=lambda c: c.bt_score, reverse=True)

    card_inputs = llm.complete(_llm.CARD, _card_prompt(question, finalists), json=True)
    return TournamentResult(card_inputs, candidates, finalists, metas, getattr(llm, "name", "llm"))
