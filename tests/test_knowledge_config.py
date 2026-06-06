"""The tag vocabulary is a config seam, not source. These tests pin the contract:
no-config falls back to the in-code default, the shipped default config is byte-identical,
a custom config overrides it, and the biotech retarget actually changes the tags produced.
"""
from pathlib import Path

from catfish.knowledge import DEFAULT_TAG_VOCAB, ingest, load_tag_vocab

REPO = Path(__file__).resolve().parents[1]


def test_missing_config_falls_back_to_default():
    assert load_tag_vocab("does-not-exist-anywhere") == DEFAULT_TAG_VOCAB


def test_shipped_default_config_is_identical():
    # config/tags.yaml must load to exactly the in-code default, so behavior is
    # unchanged out of the box once the file exists.
    assert load_tag_vocab(REPO / "config") == DEFAULT_TAG_VOCAB


def test_custom_config_overrides(tmp_path):
    (tmp_path / "tags.yaml").write_text("assay: assay\nmycoplasma: contamination\n")
    assert load_tag_vocab(tmp_path) == {"assay": "assay", "mycoplasma": "contamination"}


def test_ingest_uses_supplied_vocab(tmp_path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "note.md").write_text("# Run\nThe assay shows mycoplasma in the bank.\n")
    notes = ingest(inbox, vocab={"assay": "assay", "mycoplasma": "contamination"})
    assert len(notes) == 1
    assert set(notes[0].tags) == {"assay", "contamination"}


def test_ingest_default_vocab_unchanged():
    # no vocab arg => the in-code default, so existing callers/tests are unaffected.
    inbox = REPO / "examples" / "inbox"
    notes = ingest(inbox)
    vision = next(n for n in notes if "prescience" in n.body.lower())
    assert "risk" in vision.tags and "dependency" in vision.tags


def test_biotech_example_retargets_tags():
    # the shipped biotech retarget tags notes with its OWN vocabulary, never the default's.
    base = REPO / "examples" / "biotech"
    notes = ingest(base / "inbox", vocab=load_tag_vocab(base))
    all_tags = {t for n in notes for t in n.tags}
    assert {"assay", "contamination", "regulatory", "validation"} <= all_tags
    assert "billing" not in all_tags  # a default-only tag that must not leak in
