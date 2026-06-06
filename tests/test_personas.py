from pathlib import Path

from catfish.personas import (
    DEFAULT_PERSONAS, MOODS, mood_modifier, parse_critics, roster, load_knowledge, load_personas,
)
from catfish.models import Persona

ROOT = Path(__file__).resolve().parents[1]


def test_mood_modifier_known_and_literal():
    assert "bad mood" in mood_modifier("bad_mood")
    assert mood_modifier("seething with rage") == "seething with rage"  # unknown -> literal
    assert mood_modifier("") == ""


def test_parse_critics_applies_mood_and_adhoc():
    critics = parse_critics("skeptic:grumpy,qa:bad_mood", list(DEFAULT_PERSONAS))
    by = {c.id: c for c in critics}
    assert by["skeptic"].mood == "grumpy"          # known persona, mood overridden
    assert by["qa"].mood == "bad_mood"             # ad-hoc persona summoned by name
    assert by["qa"].role                            # ad-hoc gets a sensible role


def test_system_prompt_includes_mood_and_respects_cap():
    p = Persona(id="qa", role="QA Engineer", goal="Break it.", utility_fn="defects caught")
    sp = p.system_prompt(mood_modifier=mood_modifier("bad_mood"))
    assert "bad mood" in sp
    # cap holds (first line, before any appended knowledge)
    assert len(sp.split("\n")[0].split()) <= 120


def test_system_prompt_appends_knowledge_after_cap():
    p = Persona(id="qa", role="QA", goal="g", utility_fn="u")
    sp = p.system_prompt(knowledge="# doc\nrollback first")
    assert "Reference (documentation you know)" in sp
    assert "rollback first" in sp


def test_qa_persona_knows_its_docs():
    personas = load_personas(ROOT / "personas")
    qa = next(p for p in personas if p.id == "qa")
    assert qa.mood == "bad_mood"
    kn = load_knowledge(qa, ROOT)
    assert "rollback" in kn.lower()


def test_roster_renders_personas_and_moods():
    text = roster(list(DEFAULT_PERSONAS))
    assert "CHOOSE YOUR PANEL" in text
    assert "bad_mood" in text
    assert "skeptic" in text


def test_riley_preset_expands_to_emotions():
    crits = parse_critics("riley", list(DEFAULT_PERSONAS))
    ids = {c.id for c in crits}
    assert {"joy", "sadness", "fear", "anger", "disgust"} <= ids
    anger = next(c for c in crits if c.id == "anger")
    assert "Devil" in anger.role          # anger carries the dissent role
    assert anger.mood == "anger"
    assert "joy" in MOODS and "anger" in MOODS


def test_mix_emotions_and_moody_roles():
    crits = parse_critics("anger,pm:burned_out", list(DEFAULT_PERSONAS))
    by = {c.id: c for c in crits}
    assert by["anger"].mood == "anger"
    assert by["pm"].mood == "burned_out"
