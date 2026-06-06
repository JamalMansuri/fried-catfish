from pathlib import Path

from catfish.knowledge import ingest, build_spine

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "inbox"


def test_ingest_examples():
    notes = ingest(EXAMPLES)
    assert len(notes) == 5
    # the prescient-vision note weighs the jihad's dependency-on-this-choice and total risk
    vision = next(n for n in notes if "prescience" in n.body.lower())
    assert "risk" in vision.tags
    assert "dependency" in vision.tags
    # every note has an id, summary, source hash
    for n in notes:
        assert n.id and n.source_hash.startswith("sha256:")


def test_spine_written(tmp_path):
    notes = ingest(EXAMPLES)
    spine = build_spine(notes, tmp_path / ".catfish")
    lines = spine.read_text().strip().splitlines()
    assert len(lines) == len(notes)
    assert (tmp_path / ".catfish" / "notes").is_dir()
