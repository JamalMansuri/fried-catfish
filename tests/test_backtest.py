"""Offline coverage for the incident backtest runner (examples/incidents/backtest.py).

The Catfish column of the backtest needs a live judge, but everything else is deterministic and
key-free: the baseline picker, the keyword classifier, the held-out-key invariant, and the
case-fairness checks. Those are what we pin here so `make test` validates the harness with no key.
"""
import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BT_PATH = REPO / "examples" / "incidents" / "backtest.py"
CASES = REPO / "examples" / "incidents" / "cases"


def _load_bt():
    spec = importlib.util.spec_from_file_location("incidents_backtest", BT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bt = _load_bt()


def _case_dirs():
    return sorted(p for p in CASES.iterdir() if p.is_dir())


def test_six_cases_present():
    assert len(_case_dirs()) == 6


def test_each_case_is_fair():
    # The cases must be built so the loud read is a trap: the deterministic baseline lands on the
    # documented trap, and the trap is never the correct fix. Otherwise the backtest is rigged.
    for case in _case_dirs():
        outcome = bt.load_outcome(case)
        base = bt.baseline_pick(case / "inbox")
        assert base == outcome["trap_option"], f"{case.name}: baseline {base} != trap {outcome['trap_option']}"
        assert outcome["trap_option"] != outcome["correct_option"], f"{case.name}: trap == correct"


def test_correct_memo_classifies_to_correct_option():
    # The keyword classifier must recover the right canonical key from a memo's own text, with no
    # cross-contamination between option keyword sets.
    for case in _case_dirs():
        outcome = bt.load_outcome(case)
        memo = (case / "inbox" / f"option_{outcome['correct_option']}.md").read_text()
        assert bt.classify_pick(memo, outcome["options"]) == outcome["correct_option"]


def test_classify_returns_none_on_no_match():
    outcome = bt.load_outcome(_case_dirs()[0])
    assert bt.classify_pick("nothing relevant here at all", outcome["options"]) is None


def test_outcome_key_is_held_out_of_inbox():
    # outcome.yaml must live OUTSIDE inbox/, so the panel never ingests the answer key.
    for case in _case_dirs():
        assert (case / "outcome.yaml").is_file()
        assert not (case / "inbox" / "outcome.yaml").exists()


def test_backtest_refuses_offline(monkeypatch):
    # A backtest under the fake demo judge would be meaningless (it only knows case 01) — refuse.
    monkeypatch.setenv("CATFISH_DEMO", "1")
    from catfish.llm import resolve_llm
    assert resolve_llm().name == "fake-demo"
    assert bt.main() == 1
