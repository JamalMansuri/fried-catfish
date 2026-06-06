from pathlib import Path

from catfish.knowledge import ingest
from catfish.personas import load_personas, stamp_all
from catfish.llm import FakeLLM
from catfish.tournament import run_tournament
from catfish.card import build_card, render

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "inbox"
Q = "Do we unleash the Fremen jihad across the Imperium?"


def _run():
    notes = ingest(EXAMPLES)
    perspectives = stamp_all(load_personas(None), notes)
    result = run_tournament(Q, perspectives, FakeLLM(), max_rounds=2, finalist_count=3)
    return result, build_card(Q, result)


def test_demo_is_deterministic_and_well_formed():
    result, card = _run()
    assert len(card.options) == 3
    # deterministic fixture ranking -> Unleash the jihad wins (beats all three; they cycle)
    assert card.options[0].name == "Unleash the jihad"
    assert card.recommendation.option == card.options[0].id
    assert card.status == "proposed"
    # scores are a normalized distribution over finalists
    total = sum(o.bt_score for o in card.options)
    assert 0.98 <= total <= 1.02
    assert card.options[0].bt_score >= card.options[-1].bt_score


def test_personas_surface_context():
    notes = ingest(EXAMPLES)
    persp = stamp_all(load_personas(None), notes)
    by_id = {p.persona_id: p for p in persp}
    assert by_id["security"].note_ids       # security lens finds the external-powers threat note
    assert by_id["pm"].note_ids             # pm lens finds the dependency / timeline notes


def test_render_contains_gate_and_options():
    _, card = _run()
    text = render(card)
    assert "DECISION CARD" in text
    assert "HUMAN GATE" in text
    assert "Unleash the jihad" in text
