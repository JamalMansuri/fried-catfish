"""Decision ledger + retrospective capture.

Every accepted decision is recorded in `.catfish/decisions/_ledger.jsonl` (latest row per id wins)
so you can scan what was decided over time and see which decisions are still owed a retrospective.
`catfish retro` lists them; `catfish retro <card.json> --outcome ...` writes the result back onto the
card's `review` block and closes the ledger row.

The point: a decision is not "done" when it ships — it is done when it has been reviewed. The card
already carries the deliberation we would otherwise forget (the panel's `concerns` and each option's
critic-surfaced `risks`), so a retro can ask the only question that matters — *we were warned about X;
did X actually happen?*
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from . import knowledge
from .card import load_card, save_card
from .models import DecisionCard, Note


def _dir(catfish_dir) -> Path:
    d = Path(catfish_dir) / "decisions"
    d.mkdir(parents=True, exist_ok=True)
    return d


def ledger_path(catfish_dir) -> Path:
    return _dir(catfish_dir) / "_ledger.jsonl"


def _chosen(card: DecisionCard):
    cid = card.human_decision.choice
    return next((o for o in card.options if o.id == cid), None)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def load_rows(catfish_dir) -> list[dict]:
    """All ledger rows, deduped to the latest entry per decision id."""
    p = ledger_path(catfish_dir)
    if not p.exists():
        return []
    out: dict[str, dict] = {}
    for line in p.read_text().splitlines():
        line = line.strip()
        if line:
            r = json.loads(line)
            out[r["id"]] = r          # latest wins
    return list(out.values())


def append_decision(card: DecisionCard, catfish_dir) -> Path:
    """Upsert a one-row summary of an accepted decision into the ledger."""
    chosen = _chosen(card)
    row = {
        "id": card.id,
        "decided_at": _now(),
        "question": card.problem_statement,
        "choice": card.human_decision.choice,
        "chosen_name": chosen.name if chosen else "",
        "chosen_score": chosen.bt_score if chosen else None,
        "decided_by": card.human_decision.decided_by,
        "status": card.status,
        "review_status": card.review.status,
        "linear_parent": card.linear.parent_issue_id,
    }
    rows = {r["id"]: r for r in load_rows(catfish_dir)}
    rows[card.id] = row
    ledger_path(catfish_dir).write_text("".join(json.dumps(r) + "\n" for r in rows.values()))
    return ledger_path(catfish_dir)


def decision_to_note(card: DecisionCard, vocab=None) -> Note:
    """Convert a human-reviewed decision card into a spine Note(type="decision").

    The loop-closure: a decided card becomes durable, reapable wisdom. The body is the full
    deliberation (problem, chosen option, what the panel/critics warned, outcome+lessons) and is
    inspectable on disk — but personas read only ``summary`` (stamp() never sees body), so past
    decisions surface as a COMPRESSED one-liner, never as raw re-citable evidence. That summary-only
    exposure is the tiered-storage drift guard.
    """
    vocab = vocab or knowledge.load_tag_vocab()
    chosen = _chosen(card)
    rev = card.review

    lines = [f"Problem: {card.problem_statement}", ""]
    if chosen:
        lines += [
            "Chosen option:",
            f"  - id: {chosen.id}",
            f"  - name: {chosen.name}",
            f"  - solution: {chosen.solution}",
            f"  - recommendation rationale: {card.recommendation.rationale}",
        ]
    if card.concerns:
        lines += ["", "What the panel worried about:"] + [f"  - {c}" for c in card.concerns]
    if chosen and chosen.risks:
        lines += ["", f"What critics warned about {chosen.name}:"] + [f"  - {r}" for r in chosen.risks]
    if rev.status == "done":
        lines += ["", "Outcome + lessons:",
                  f"  - outcome: {rev.outcome or '—'}",
                  f"  - lessons: {rev.lessons or '—'}"]
    body = "\n".join(lines)

    chosen_name = chosen.name if chosen else "?"
    state = rev.outcome if rev.status == "done" and rev.outcome else "pending review"
    summary = " ".join(f"{card.problem_statement} -> chose {chosen_name}; {state}".split()[:24])

    tags = list(knowledge._tag(body, vocab))
    if "decision" not in tags:
        tags.append("decision")

    return Note(
        id=f"dec-{card.id}",
        title="Decision: " + card.problem_statement,
        type="decision",
        tags=tags,
        summary=summary,
        status="decided",
        source_hash=f"decision:{card.id}",
        source_type="decision",
        path="",
        body=body,
    )


def ingest_decision(card: DecisionCard, catfish_dir, vocab=None) -> Path:
    """Merge an accepted/reviewed decision into the spine as a reapable Note (upsert by source_hash)."""
    note = decision_to_note(card, vocab)
    return knowledge.build_spine([note], Path(catfish_dir))


def record_review(card_path, *, outcome="", went_well="", went_wrong="", would_repeat=None,
                  lessons="", by="", catfish_dir=Path(".catfish")) -> DecisionCard:
    """Write a retrospective onto a card's review block and refresh its ledger row."""
    card = load_card(Path(card_path))
    r = card.review
    if outcome:
        r.outcome = outcome
    if went_well:
        r.went_well = went_well
    if went_wrong:
        r.went_wrong = went_wrong
    if would_repeat is not None:
        r.would_repeat = would_repeat
    if lessons:
        r.lessons = lessons
    r.reviewed_by = by or r.reviewed_by or "cli"
    r.reviewed_at = _now()
    r.status = "done"
    save_card(card, Path(card_path).parent)
    append_decision(card, catfish_dir)
    ingest_decision(card, catfish_dir)  # close the loop: the reviewed decision joins the spine as reapable wisdom
    return card


def render_ledger(rows) -> str:
    if not rows:
        return "No decisions recorded yet. Accept a card to start the ledger."
    rows = sorted(rows, key=lambda r: r.get("decided_at", ""), reverse=True)
    out = ["DECISION LEDGER", ""]
    for r in rows:
        flag = "⏳ retro due" if r.get("review_status") != "done" else "✓ reviewed"
        sc = r.get("chosen_score")
        sc = f"{sc:.2f}" if isinstance(sc, (int, float)) else "—"
        out.append(f"  {r['id']}  [{flag}]")
        out.append(f"      Q: {r.get('question', '')}")
        out.append(f"      → {r.get('choice', '?')} {r.get('chosen_name', '')} (score {sc}), by {r.get('decided_by', '?')}")
    pend = sum(1 for r in rows if r.get("review_status") != "done")
    out += ["", f"{len(rows)} decision(s) · {pend} awaiting a retrospective"]
    return "\n".join(out)


def render_review(card: DecisionCard) -> str:
    """The retrospective surface: the decision + what we were warned about + the outcome (if recorded)."""
    chosen = _chosen(card)
    out = [f"RETROSPECTIVE  {card.id}", "", f"Decision: {card.problem_statement}"]
    if chosen:
        out.append(f"Chose: {chosen.id} {chosen.name} (score {chosen.bt_score:.2f}) — by {card.human_decision.decided_by}")
    if card.concerns:
        out += ["", "What the panel kept worrying about:"] + [f"  - {c}" for c in card.concerns]
    if chosen and chosen.risks:
        out += ["", f"What critics warned about the chosen option ({chosen.name}):"] + [f"  - {r}" for r in chosen.risks]
    others = [o for o in card.options if not chosen or o.id != chosen.id]
    if others:
        out += ["", "Roads not taken:"] + [f"  - {o.id} {o.name}: {o.trade_offs.bad}" for o in others]
    r = card.review
    out += ["", "Outcome:"]
    if r.status == "done":
        rep = {True: "yes", False: "no", None: "—"}[r.would_repeat]
        out += [f"  reviewed by {r.reviewed_by} on {r.reviewed_at}",
                f"  what happened : {r.outcome or '—'}",
                f"  went well     : {r.went_well or '—'}",
                f"  went wrong    : {r.went_wrong or '—'}",
                f"  would repeat  : {rep}",
                f"  lessons       : {r.lessons or '—'}"]
    else:
        out += ['  (not yet reviewed — run: catfish retro <card.json> --outcome "..." --lessons "...")']
    return "\n".join(out)
