#!/usr/bin/env python3
"""Backtest Catfish on six on-call incidents whose real root-cause fix is known.

For each case we run the tournament BLIND — the corpus is only `inbox/`, and the answer key in
`outcome.yaml` never enters it — then score the card's recommendation against the held-out truth,
and against a deterministic "go with the loudest signal" baseline.

    python examples/incidents/backtest.py        # needs CATFISH_LLM_API_KEY (a real judge)

Why a live key: a backtest only means something if the panel never sees the answer, and the
offline replay (CATFISH_DEMO=1) only knows case 01. So the real scoreboard needs a real judge.
The baseline and the truth columns are pure, key-free Python — it's the Catfish column that needs
the live tournament.

Honesty note: the six cases are fixed. We report whatever the run gives; we do not re-tune cases
until Catfish wins. A Bradley-Terry rank is persuasiveness among LLM judges, not truth — this
measures how often that proxy lands on the answer the postmortem later confirmed.
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
CASES = HERE / "cases"
REPO = HERE.parents[1]

# Run from a source checkout without `pip install -e .` by adding ./src to the path.
try:
    from catfish.knowledge import ingest, load_tag_vocab
except ModuleNotFoundError:  # pragma: no cover - convenience for source checkouts
    sys.path.insert(0, str(REPO / "src"))
    from catfish.knowledge import ingest, load_tag_vocab

from catfish.personas import load_personas, stamp_all, default_critics
from catfish.tournament import run_tournament
from catfish.card import build_card
from catfish.llm import resolve_llm

# ----------------------------------------------------------------- deterministic baseline

_STOP = set(
    "the a an and or of to in on at for with is are be it its this that as by from we our you your "
    "they their them not no so if then than into over under out up down off can could should would "
    "will just but about which who what when where why how each one two three more most less few "
    "many much very real only also some any all".split()
)


def _tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in _STOP and len(w) > 2}


def _jaccard(a: str, b: str) -> float:
    A, B = _tokens(a), _tokens(b)
    return len(A & B) / len(A | B) if (A | B) else 0.0


def option_memos(inbox: Path) -> dict[str, str]:
    """key -> memo text, for every `option_<key>.md` in a case inbox."""
    return {f.stem[len("option_"):]: f.read_text() for f in sorted(inbox.glob("option_*.md"))}


def baseline_pick(inbox: Path) -> str:
    """The knee-jerk: the remediation whose memo reads most like the loud alert. Deterministic,
    no LLM — models 'do the thing the alarm points at' rather than reading the timeline."""
    alert = (inbox / "alert.md").read_text()
    memos = option_memos(inbox)
    return max(memos, key=lambda k: _jaccard(alert, memos[k]))


# ----------------------------------------------------------------- scoring a free-form pick

def classify_pick(text: str, options: dict) -> str | None:
    """Map a free-form recommended option (name + solution) onto a canonical option key by
    keyword hits from outcome.yaml. Returns None if nothing matches."""
    low = text.lower()
    best, best_hits = None, 0
    for key, spec in options.items():
        hits = sum(1 for kw in spec.get("keywords", []) if kw.lower() in low)
        if hits > best_hits:
            best, best_hits = key, hits
    return best


def load_outcome(case: Path) -> dict:
    return yaml.safe_load((case / "outcome.yaml").read_text())


# ----------------------------------------------------------------- the run

def catfish_pick(case: Path, llm) -> tuple[str | None, str]:
    """Run the blind tournament on a case and return (canonical_key_or_None, recommended_name)."""
    inbox = case / "inbox"
    question = (case / "question.txt").read_text().strip()
    vocab = load_tag_vocab(HERE)
    notes = ingest(inbox, vocab=vocab)
    personas = load_personas(HERE / "personas")
    perspectives = stamp_all(personas, notes)
    critics = default_critics(personas)
    result = run_tournament(question, perspectives, llm, critics=critics, max_rounds=2, finalist_count=4)
    card = build_card(question, result)
    rec = next((o for o in card.options if o.id == card.recommendation.option), None)
    if rec is None:
        return None, "(no recommendation)"
    outcome = load_outcome(case)
    return classify_pick(f"{rec.name} {rec.solution}", outcome["options"]), rec.name


def run(llm) -> list[dict]:
    rows = []
    for case in sorted(p for p in CASES.iterdir() if p.is_dir()):
        outcome = load_outcome(case)
        correct = outcome["correct_option"]
        base = baseline_pick(case / "inbox")
        cf, cf_name = catfish_pick(case, llm)
        rows.append({
            "case": case.name,
            "correct": correct,
            "baseline": base,
            "catfish": cf or "unmatched",
            "catfish_name": cf_name,
            "catfish_hit": cf == correct,
            "baseline_hit": base == correct,
            "why_baseline_misses": " ".join(str(outcome.get("why_baseline_misses", "")).split()),
        })
    return rows


# ----------------------------------------------------------------- rendering

def scoreboard(rows: list[dict]) -> str:
    cf = sum(r["catfish_hit"] for r in rows)
    bl = sum(r["baseline_hit"] for r in rows)
    n = len(rows)
    out = []
    out.append(f"# Backtest results — Catfish vs. the loudest-signal baseline\n")
    out.append(f"**Catfish {cf}/{n}  ·  loudest-signal baseline {bl}/{n}**  "
               f"(recorded {time.strftime('%Y-%m-%d %H:%M %Z')})\n")
    out.append("| case | known fix | Catfish | ✓ | baseline | ✓ |")
    out.append("|---|---|---|:--:|---|:--:|")
    for r in rows:
        out.append(f"| {r['case']} | {r['correct']} | {r['catfish']} | "
                   f"{'✅' if r['catfish_hit'] else '❌'} | {r['baseline']} | "
                   f"{'✅' if r['baseline_hit'] else '❌'} |")
    out.append("")
    misses = [r for r in rows if not r["catfish_hit"]]
    if misses:
        out.append("## Where Catfish missed\n")
        for r in misses:
            out.append(f"- **{r['case']}** — picked `{r['catfish']}` ({r['catfish_name']}), "
                       f"known fix was `{r['correct']}`.")
        out.append("")
    out.append("## How to read this\n")
    out.append("The baseline is a deterministic foil — the remediation whose memo reads most like "
               "the loud alert (it never reads the timeline), computed with no LLM. It lands on "
               "each case's trap by construction, so it scores near zero. The Catfish column is the "
               "live tournament's recommendation. The gap is what adversarial stress-testing buys "
               "on decisions where the truth is knowable.\n")
    out.append("> A Bradley-Terry rank is persuasiveness among LLM judges, not truth. The cases are "
               "fixed; we report whatever the run gives.")
    return "\n".join(out)


def main() -> int:
    llm = resolve_llm()
    if getattr(llm, "name", "") == "fake-demo":
        print(
            "✗ The backtest needs a live judge (set CATFISH_LLM_API_KEY).\n"
            "  CATFISH_DEMO=1 only replays case 01, and a backtest is only honest if the panel\n"
            "  never sees the answer key. The single-case card demo still works offline:\n"
            "    CATFISH_DEMO=1 catfish tournament examples/incidents/cases/01-checkout-latency/inbox \\\n"
            "      \"$(cat examples/incidents/cases/01-checkout-latency/question.txt)\" \\\n"
            "      --config-dir examples/incidents --finalists 4",
            file=sys.stderr,
        )
        return 1

    print(f"· judge={llm.name} · {sum(1 for _ in CASES.iterdir())} cases · running blind tournaments…\n")
    rows = run(llm)
    md = scoreboard(rows)
    (HERE / "RESULTS.md").write_text(md + "\n")
    print(md)
    print(f"\n· wrote {HERE / 'RESULTS.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
