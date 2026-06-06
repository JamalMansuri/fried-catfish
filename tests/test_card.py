import pytest

from catfish.card import _cap, build_card, assert_approved, accept, GateBlockedError
from catfish.models import Candidate


class _Result:
    def __init__(self, finalists, card_inputs):
        self.finalists = finalists
        self.card_inputs = card_inputs


def _finalists():
    a = Candidate(id="c1", name="Alpha", text="Do the bold thing right now without delay at all costs", bt_score=0.6)
    b = Candidate(id="c2", name="Beta", text="Wait", bt_score=0.4)
    return [a, b]


def _inputs():
    return {
        "problem_statement": "ship or wait",
        "first_principles": ["deadline is fixed", "team is small"],
        "trade_offs": {
            "Alpha": {"good": "fast", "neutral": "needs care", "bad": "risky"},
            "Beta": {"good": "safe", "neutral": "slower", "bad": "misses window"},
        },
        "recommendation": {"option_name": "Beta", "rationale": "the window can move; the risk cannot"},
    }


def test_cap_trims_to_word_limit():
    out = _cap("one two three four five", 3)
    assert out.startswith("one two three") and out.endswith("…")


def test_build_card_maps_options_and_recommendation():
    card = build_card("ship or wait", _Result(_finalists(), _inputs()))
    assert [o.id for o in card.options] == ["A", "B"]
    assert card.options[0].name == "Alpha"
    # recommendation references Beta -> option id B
    assert card.recommendation.option == "B"
    # solution is capped at 25 words (Alpha solution is 11 words -> unchanged here)
    assert card.options[0].solution


def test_gate_blocks_until_accepted():
    card = build_card("ship or wait", _Result(_finalists(), _inputs()))
    with pytest.raises(GateBlockedError):
        assert_approved(card)
    accept(card, decided_by="jamal", choice="A")
    assert card.status == "accepted"
    assert_approved(card)  # no raise


def test_accept_rejects_unknown_choice():
    card = build_card("ship or wait", _Result(_finalists(), _inputs()))
    with pytest.raises(ValueError):
        accept(card, decided_by="x", choice="Z")
