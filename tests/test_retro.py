from catfish import retro
from catfish.card import accept, build_card, load_card, save_card
from catfish.models import Candidate, Critique, MetaReview


class _Result:
    def __init__(self, finalists, card_inputs, metas):
        self.finalists = finalists
        self.card_inputs = card_inputs
        self.metas = metas


def _result():
    a = Candidate(id="c1", name="Alpha", text="go now", bt_score=0.7,
                  critiques=[Critique("skeptic", "rollback path is untested", 0),
                             Critique("qa", "rollback path is untested", 0)])  # dup -> deduped
    b = Candidate(id="c2", name="Beta", text="wait", bt_score=0.3)
    ci = {
        "problem_statement": "ship or wait",
        "first_principles": ["fixed deadline"],
        "trade_offs": {"Alpha": {"good": "fast", "neutral": "", "bad": "risky"},
                       "Beta": {"good": "safe", "neutral": "", "bad": "misses window"}},
        "recommendation": {"option_name": "Alpha", "rationale": "do it"},
    }
    metas = [MetaReview(0, ["rollback coverage"], ["none address capacity"], [], "focus rollback")]
    return _Result([a, b], ci, metas)


def test_card_captures_deliberation_for_retro():
    card = build_card("ship or wait", _result())
    assert card.concerns                          # meta-review concerns captured
    assert card.options[0].risks == ["rollback path is untested"]  # deduped critic risks
    assert card.review.status == "pending"


def test_ledger_and_review_roundtrip(tmp_path):
    card = build_card("ship or wait", _result())
    accept(card, decided_by="jamal", choice="A")
    cards_dir = tmp_path / "cards"
    save_card(card, cards_dir)

    retro.append_decision(card, tmp_path)
    rows = retro.load_rows(tmp_path)
    assert len(rows) == 1
    assert rows[0]["review_status"] == "pending"
    assert rows[0]["chosen_name"] == "Alpha"

    updated = retro.record_review(cards_dir / f"{card.id}.json", outcome="shipped clean",
                                  would_repeat=True, lessons="protect the buffer week",
                                  by="jamal", catfish_dir=tmp_path)
    assert updated.review.status == "done"
    assert retro.load_rows(tmp_path)[0]["review_status"] == "done"

    # serialization round-trip preserves the review + per-option risks
    reloaded = load_card(cards_dir / f"{card.id}.json")
    assert reloaded.review.outcome == "shipped clean"
    assert reloaded.review.would_repeat is True
    assert reloaded.options[0].risks == ["rollback path is untested"]


def test_render_ledger_and_review():
    card = build_card("ship or wait", _result())
    accept(card, decided_by="jamal", choice="A")
    text = retro.render_review(card)
    assert "RETROSPECTIVE" in text
    assert "not yet reviewed" in text          # pending state surfaced
    assert "rollback path is untested" in text  # warning carried into the retro
