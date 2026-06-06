from pathlib import Path

from catfish.knowledge import ingest, load_tag_vocab
from catfish.personas import load_personas, stamp_all
from catfish.llm import FakeLLM
from catfish.tournament import run_tournament
from catfish.card import build_card, render

LUNCH = Path(__file__).resolve().parents[1] / "examples" / "lunch"
EXAMPLES = LUNCH / "inbox"
Q = "Where should we grab lunch today?"


def _run():
    notes = ingest(EXAMPLES, vocab=load_tag_vocab(LUNCH))
    perspectives = stamp_all(load_personas(LUNCH / "personas"), notes)
    result = run_tournament(Q, perspectives, FakeLLM(), max_rounds=2, finalist_count=4)
    return result, build_card(Q, result)


def test_demo_is_deterministic_and_well_formed():
    result, card = _run()
    assert len(card.options) == 4
    # deterministic fixture ranking -> the taquería wins (beats all three chains; they cycle)
    assert card.options[0].name == "Taquería down the block"
    assert card.recommendation.option == card.options[0].id
    assert card.status == "proposed"
    # scores are a normalized distribution over finalists
    total = sum(o.bt_score for o in card.options)
    assert 0.98 <= total <= 1.02
    assert card.options[0].bt_score >= card.options[-1].bt_score


def test_personas_surface_context():
    notes = ingest(EXAMPLES, vocab=load_tag_vocab(LUNCH))
    persp = stamp_all(load_personas(LUNCH / "personas"), notes)
    by_id = {p.persona_id: p for p in persp}
    assert by_id["nutritionist"].note_ids   # health lens finds the option memos
    assert by_id["budget"].note_ids         # cost/value lens finds the price notes


def test_render_contains_gate_and_options():
    _, card = _run()
    text = render(card)
    assert "DECISION CARD" in text
    assert "HUMAN GATE" in text
    assert "Taquería down the block" in text
