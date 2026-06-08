"""Provenance backbone: note_ids thread through Candidate to a card-level grounding set, and the
two code-aware card fields (affected_capabilities / business_impact) get a real, gated writer.

Provenance here is an honest GROUNDING set ("what the tournament reasoned over"), not per-claim
attribution — every option shares it, so it lives card-level, not per-option.
"""
from pathlib import Path

from catfish.knowledge import ingest, load_tag_vocab
from catfish.personas import load_personas, stamp_all
from catfish.llm import FakeLLM
from catfish.tournament import run_tournament
from catfish.card import build_card, derive_impact, load_capability_index
from catfish.models import DecisionCard

INCIDENTS = Path(__file__).resolve().parents[1] / "examples" / "incidents"
CASE = INCIDENTS / "cases" / "01-checkout-latency"
EXAMPLES = CASE / "inbox"
Q = (CASE / "question.txt").read_text().strip()


def _demo():
    notes = ingest(EXAMPLES, vocab=load_tag_vocab(INCIDENTS))
    perspectives = stamp_all(load_personas(INCIDENTS / "personas"), notes)
    result = run_tournament(Q, perspectives, FakeLLM(), max_rounds=2, finalist_count=4)
    expected = sorted({nid for p in perspectives for nid in p.note_ids})
    return perspectives, result, expected


# --- grounding set threaded through the engine ---

def test_generation_candidates_carry_the_grounding_set():
    _, result, expected = _demo()
    assert expected, "demo perspectives should surface at least one note"
    gen = [c for c in result.candidates if c.source == "generation"]
    assert gen and all(c.note_ids == expected for c in gen)


def test_evolution_candidates_inherit_survivor_lineage_subset():
    _, result, expected = _demo()
    evo = [c for c in result.candidates if c.source == "evolution"]
    # an evolved plan never sees the notes — its grounding is the union of its survivor parents,
    # which is a subset of the global grounding set (we do not overclaim direct grounding).
    assert all(set(c.note_ids) <= set(expected) for c in evo)


def test_card_grounding_refs_is_card_level_union_not_per_option():
    _, result, expected = _demo()
    card = build_card(Q, result)
    assert card.grounding_refs == expected                 # union the tournament reasoned over
    assert not hasattr(card.options[0], "evidence_refs")   # no fake per-option provenance


def test_grounding_refs_survive_roundtrip():
    _, result, _ = _demo()
    card = build_card(Q, result)
    restored = DecisionCard.from_dict(card.to_dict())
    assert restored.grounding_refs == card.grounding_refs


# --- the two code-aware fields (derive_impact takes the card-level refs list) ---

def test_derive_impact_knowledge_only_is_empty():
    assert derive_impact(["nt-0001", "nt-0002"], None) == ([], None)
    assert derive_impact(["nt-0001"], {}) == ([], None)


def test_derive_impact_ignores_non_code_refs():
    idx = {"nt-0001": {"type": "source", "value": {}}}
    assert derive_impact(["nt-0001"], idx) == ([], None)


def test_derive_impact_lists_code_nodes_but_gates_business_impact():
    # a code node is listed in affected_capabilities, but a PROPOSED value never auto-asserts impact
    idx = {"cap.auth": {"type": "code-capability",
                        "value": {"status": "proposed", "value_type": "risk",
                                  "value_statement": "auth surface"}}}
    affected, impact = derive_impact(["cap.auth", "nt-0001"], idx)
    assert affected == ["cap.auth"]
    assert impact is None


def test_derive_impact_business_impact_only_from_confirmed():
    idx = {
        "cap.auth": {"type": "code-capability",
                     "value": {"status": "confirmed", "value_type": "risk",
                               "value_statement": "closes AUTH-07 exposure"}},
        "cap.bill": {"type": "code-capability",
                     "value": {"status": "proposed", "value_type": "revenue",
                               "value_statement": "billing throughput"}},
    }
    affected, impact = derive_impact(["cap.auth", "cap.bill"], idx)
    assert affected == ["cap.auth", "cap.bill"]                  # both are code nodes
    assert impact and "risk" in impact and "AUTH-07" in impact   # only the confirmed value composed
    assert "billing throughput" not in impact                   # proposed value excluded from impact


def test_derive_impact_count_matches_body_with_overflow():
    # 5 confirmed -> 'Affects 5' header must not silently list only 3 with no signal
    idx = {f"cap.{i}": {"type": "code-capability",
                        "value": {"status": "confirmed", "value_type": "cost",
                                  "value_statement": f"statement {i}"}} for i in range(5)}
    affected, impact = derive_impact(list(idx), idx)
    assert len(affected) == 5
    assert "Affects 5 mapped capabilities" in impact
    assert "+2 more" in impact


def test_load_capability_index_tolerates_corruption(tmp_path):
    (tmp_path / "_code_index.jsonl").write_text("\n".join([
        '{"id": "cap.ok", "type": "code-capability", "value": {"status": "confirmed"}}',
        "",                                # blank line
        "not json at all",                 # bad json
        "42",                              # bare scalar — must skip, not TypeError
        "null",                            # bare scalar
        '"a string with id in it"',        # JSON string containing 'id' — must not AttributeError
        "[1, 2, 3]",                       # JSON array
        '{"type": "code-capability"}',     # no id
        '{"id": 7, "type": "x"}',          # non-string id
        '{"id": "cap.badval", "type": "code-capability", "value": "oops"}',  # non-dict value
    ]))
    idx = load_capability_index(tmp_path)
    assert set(idx) == {"cap.ok", "cap.badval"}
    assert idx["cap.badval"]["value"] == {}    # non-dict value coerced to {}


def test_build_card_demo_stays_knowledge_only():
    # the incident demo has no code-capability ids in its grounding set -> both fields empty/None
    _, result, _ = _demo()
    card = build_card(Q, result, capability_index={"cap.x": {"type": "code-capability", "value": {}}})
    assert card.affected_capabilities == []
    assert card.business_impact is None
