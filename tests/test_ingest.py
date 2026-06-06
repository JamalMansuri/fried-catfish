from pathlib import Path

from catfish.knowledge import ingest, build_spine, load_tag_vocab

LUNCH = Path(__file__).resolve().parents[1] / "examples" / "lunch"
EXAMPLES = LUNCH / "inbox"


def test_ingest_examples():
    notes = ingest(EXAMPLES, vocab=load_tag_vocab(LUNCH))
    assert len(notes) == 5
    # the taquería note is fresh, made-to-order, and a short walk — health + convenience tags
    taqueria = next(n for n in notes if "carne asada" in n.body.lower())
    assert "health" in taqueria.tags
    assert "convenience" in taqueria.tags
    # every note has an id, summary, source hash
    for n in notes:
        assert n.id and n.source_hash.startswith("sha256:")


def test_spine_written(tmp_path):
    notes = ingest(EXAMPLES, vocab=load_tag_vocab(LUNCH))
    spine = build_spine(notes, tmp_path / ".catfish")
    lines = spine.read_text().strip().splitlines()
    assert len(lines) == len(notes)
    assert (tmp_path / ".catfish" / "notes").is_dir()
