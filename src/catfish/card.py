"""Decision cards: build from a tournament result, enforce terseness, render, gate.

A card is a MADR-style artifact with status:proposed and a human gate. Terseness is a hard
schema constraint: any field over its word cap is trimmed before the card reaches the human.
The gate is structural — `assert_approved` refuses any downstream write until a human has
chosen an option and the card is accepted.
"""
from __future__ import annotations

import json
import textwrap
import time
from pathlib import Path

from .models import (
    CARD_WORD_CAPS, DecisionCard, HumanDecision, Option, Recommendation, TradeOffs,
)

_LETTERS = ["A", "B", "C", "D", "E"]


class GateBlockedError(RuntimeError):
    """Raised when a write is attempted before the human gate is satisfied."""


def _cap(text: str, words: int) -> str:
    text = " ".join(str(text).split())
    parts = text.split(" ")
    if len(parts) <= words:
        return text
    return " ".join(parts[:words]).rstrip(".,;:") + " …"


# ------------------------------------------------------------------ build

def _risks(candidate, limit: int = 3) -> list[str]:
    """Distinct critic-surfaced risks for a candidate (dedup'd, capped) — the retro 'what we were warned about'."""
    seen: set[str] = set()
    out: list[str] = []
    for cr in getattr(candidate, "critiques", []):
        t = _cap(cr.text, 18)
        if t and t not in seen:
            seen.add(t)
            out.append(t)
        if len(out) >= limit:
            break
    return out


_CODE_TYPES = ("code-capability", "code-entrypoint")


def load_capability_index(catfish_dir) -> dict:
    """Load the code logic-spine (present only if a codebase was mapped) as id -> {type, value}.

    Tolerant of a hand-edited / partially-corrupt JSONL: blank lines, bad JSON, and any row that is
    not a JSON object with a string id are skipped rather than crashing the card build. Absent file
    -> {} -> the code-aware card fields stay empty/None (correct for a knowledge-only decision).
    """
    f = Path(catfish_dir) / "_code_index.jsonl"
    if not f.is_file():
        return {}
    index: dict = {}
    for line in f.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict) or not isinstance(row.get("id"), str):
            continue
        val = row.get("value")
        index[row["id"]] = {"type": row.get("type", ""), "value": val if isinstance(val, dict) else {}}
    return index


def derive_impact(grounding_refs, capability_index: dict | None) -> tuple[list[str], str | None]:
    """Compose the two code-aware card fields from the card's grounding set (card-level, not per-option).

    `affected_capabilities` = the grounding refs the logic spine confirms are code nodes.
    `business_impact` = a one-line roll-up composed ONLY from value blocks whose status ==
    'confirmed' — never from a 'proposed' value, because business value is a human-gated proposal,
    not something the engine asserts. Both are empty/None for a knowledge-only decision (no code
    nodes in the grounding set), which is the correct, honest result.
    """
    if not capability_index:
        return [], None
    refs = sorted(set(grounding_refs or []))
    affected = [r for r in refs if capability_index.get(r, {}).get("type") in _CODE_TYPES]
    if not affected:
        return [], None
    confirmed = []
    for cid in affected:
        v = capability_index.get(cid, {}).get("value")
        v = v if isinstance(v, dict) else {}
        if v.get("status") == "confirmed" and v.get("value_statement"):
            confirmed.append((v.get("value_type", "impact"), _cap(v["value_statement"], 12)))
    if not confirmed:
        return affected, None
    parts = "; ".join(f"{vt}: {stmt}" for vt, stmt in confirmed[:3])
    if len(confirmed) > 3:
        parts += f"; +{len(confirmed) - 3} more"      # body never silently undercounts the 'Affects N'
    noun = "capability" if len(affected) == 1 else "capabilities"
    return affected, _cap(f"Affects {len(affected)} mapped {noun}; {parts}", 60)


def build_card(question: str, result, card_id: str | None = None,
               capability_index: dict | None = None) -> DecisionCard:
    ci = result.card_inputs or {}
    finalists = result.finalists
    trade_map = ci.get("trade_offs", {})

    options: list[Option] = []
    for i, f in enumerate(finalists):
        t = trade_map.get(f.name, {})
        options.append(Option(
            id=_LETTERS[i],
            name=f.name,
            solution=_cap(f.text, CARD_WORD_CAPS["solution"]),
            trade_offs=TradeOffs(
                good=_cap(t.get("good", ""), CARD_WORD_CAPS["trade_off"]),
                neutral=_cap(t.get("neutral", ""), CARD_WORD_CAPS["trade_off"]),
                bad=_cap(t.get("bad", ""), CARD_WORD_CAPS["trade_off"]),
            ),
            bt_score=round(float(f.bt_score or 0.0), 2),
            risks=_risks(f),
        ))

    # Card-level grounding set: union of the finalists' grounding notes — what the tournament
    # reasoned over. Not per-option; the engine grounds every option in the same combined context.
    grounding_refs = sorted({nid for f in finalists for nid in getattr(f, "note_ids", []) or []})
    affected_capabilities, business_impact = derive_impact(grounding_refs, capability_index)

    rec_in = ci.get("recommendation", {})
    rec_name = rec_in.get("option_name", "")
    rec_id = next((o.id for o in options if o.name == rec_name), options[0].id if options else "")

    # deliberation memory for retrospectives: what the panel kept worrying about (meta-review).
    metas = getattr(result, "metas", None) or []
    concerns: list[str] = []
    if metas:
        last = metas[-1]
        raw = list(getattr(last, "recurring_concerns", []) or []) + list(getattr(last, "pattern_gaps", []) or [])
        seen: set[str] = set()
        for c in raw:
            cc = _cap(c, 14)
            if cc and cc not in seen:
                seen.add(cc)
                concerns.append(cc)
            if len(concerns) >= 4:
                break

    cid = card_id or f"card-{time.strftime('%Y-%m-%d')}-001"
    return DecisionCard(
        id=cid,
        problem_statement=_cap(ci.get("problem_statement", question), CARD_WORD_CAPS["problem_statement"]),
        status="proposed",
        first_principles=[_cap(p, CARD_WORD_CAPS["first_principle"]) for p in ci.get("first_principles", [])[:3]],
        options=options,
        recommendation=Recommendation(option=rec_id, rationale=_cap(rec_in.get("rationale", ""), CARD_WORD_CAPS["recommendation"])),
        human_decision=HumanDecision(),
        affected_capabilities=affected_capabilities,
        business_impact=business_impact,
        grounding_refs=grounding_refs,
        concerns=concerns,
        created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )


# ------------------------------------------------------------------ render

def _row(cells, inner):
    return "│" + "│".join(" " + c.ljust(inner) + " " for c in cells) + "│"


def _border(kind, n, inner):
    left, mid, right = {"top": "┌┬┐", "mid": "├┼┤", "bot": "└┴┘"}[kind]
    seg = "─" * (inner + 2)
    return left + mid.join(seg for _ in range(n)) + right


def _section(per_option_lines, inner):
    height = max((len(lines) for lines in per_option_lines), default=1)
    rows = []
    for k in range(height):
        cells = [(lines[k] if k < len(lines) else "") for lines in per_option_lines]
        rows.append(_row(cells, inner))
    return rows


def _table(options, rec_id, inner=22):
    n = len(options)
    if n == 0:
        return "  (no options survived)"
    header = []
    for o in options:
        name_lines = textwrap.wrap(f"[{o.id}] {o.name}", inner) or [f"[{o.id}]"]
        score_line = f"score {o.bt_score:.2f}" + ("  ★REC" if o.id == rec_id else "")
        header.append(name_lines + [score_line])
    good = [["GOOD"] + (textwrap.wrap(o.trade_offs.good, inner) or [""]) for o in options]
    neutral = [["NEUTRAL"] + (textwrap.wrap(o.trade_offs.neutral, inner) or [""]) for o in options]
    bad = [["BAD"] + (textwrap.wrap(o.trade_offs.bad, inner) or [""]) for o in options]

    lines = [_border("top", n, inner)]
    lines += _section(header, inner)
    lines.append(_border("mid", n, inner))
    lines += _section(good, inner)
    lines.append(_border("mid", n, inner))
    lines += _section(neutral, inner)
    lines.append(_border("mid", n, inner))
    lines += _section(bad, inner)
    lines.append(_border("bot", n, inner))
    return "\n".join(lines)


def render(card: DecisionCard) -> str:
    bar = "━" * 62
    out = [bar, f"DECISION CARD  {card.id}".ljust(46) + f"status: {card.status.upper()}", bar, ""]
    out.append("PROBLEM")
    for line in textwrap.wrap(card.problem_statement, 58) or [""]:
        out.append("  " + line)
    out.append("")
    if card.first_principles:
        out.append("FIRST PRINCIPLES")
        for i, p in enumerate(card.first_principles, 1):
            wrapped = textwrap.wrap(p, 56) or [""]
            out.append(f"  {i}. {wrapped[0]}")
            out.extend("     " + w for w in wrapped[1:])
        out.append("")
    out.append(_table(card.options, card.recommendation.option))
    out.append("")
    rec_name = next((o.name for o in card.options if o.id == card.recommendation.option), "")
    out.append(f"RECOMMENDATION  →  {card.recommendation.option}  {rec_name}")
    for line in textwrap.wrap(card.recommendation.rationale, 58) or [""]:
        out.append("  " + line)
    if card.business_impact:
        out.append("")
        out.append("BUSINESS IMPACT")
        for line in textwrap.wrap(card.business_impact, 58):
            out.append("  " + line)
    out.append("")
    out.append("─" * 62)
    if card.status == "accepted":
        out.append(f"HUMAN GATE  ✓ accepted by {card.human_decision.decided_by} → option {card.human_decision.choice}")
    else:
        out.append("HUMAN GATE  [ thumbs-up required before any Linear write ]")
        out.append("  decided_by: ____    choice: ____ (" + "/".join(o.id for o in card.options) + ")    notes: ____")
    out.append(bar)
    return "\n".join(out)


# ------------------------------------------------------------------ gate + io

def assert_approved(card: DecisionCard) -> None:
    if card.human_decision.choice is None:
        raise GateBlockedError(
            f"Card {card.id} is still proposed. Set human_decision.choice before any Linear write."
        )
    if card.status != "accepted":
        raise GateBlockedError(f"Card {card.id} status is '{card.status}', not 'accepted'.")


def accept(card: DecisionCard, decided_by: str, choice: str, notes: str | None = None) -> DecisionCard:
    valid = {o.id for o in card.options}
    if choice not in valid:
        raise ValueError(f"choice {choice!r} not one of {sorted(valid)}")
    card.human_decision = HumanDecision(decided_by=decided_by, choice=choice, notes=notes)
    card.status = "accepted"
    return card


def save_card(card: DecisionCard, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    j = out_dir / f"{card.id}.json"
    j.write_text(json.dumps(card.to_dict(), indent=2))
    (out_dir / f"{card.id}.md").write_text("```\n" + render(card) + "\n```\n")
    return j


def load_card(path: Path) -> DecisionCard:
    return DecisionCard.from_dict(json.loads(Path(path).read_text()))
