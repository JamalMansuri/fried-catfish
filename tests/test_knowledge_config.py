"""The tag vocabulary is a config seam, not source. These tests pin the contract:
no-config falls back to the in-code default, the shipped default config is byte-identical,
a custom config overrides it, and the incidents retarget actually changes the tags produced.
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
    (tmp_path / "tags.yaml").write_text("fresh: health\ncheap: cost\n")
    assert load_tag_vocab(tmp_path) == {"fresh": "health", "cheap": "cost"}


def test_ingest_uses_supplied_vocab(tmp_path):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "note.md").write_text("# Note\nThe rollout is fresh and the fix is cheap.\n")
    notes = ingest(inbox, vocab={"fresh": "health", "cheap": "cost"})
    assert len(notes) == 1
    assert set(notes[0].tags) == {"health", "cost"}


def test_ingest_default_vocab_unchanged(tmp_path):
    # no vocab arg => the in-code default, so existing callers/tests are unaffected.
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (inbox / "note.md").write_text("# Q3\nThe auth migration is a dependency risk for the team.\n")
    notes = ingest(inbox)
    tags = set(notes[0].tags)
    assert {"auth", "migration", "dependency", "risk"} <= tags


def test_incidents_example_retargets_tags():
    # the shipped incidents retarget tags notes with its OWN vocabulary, never the default's.
    base = REPO / "examples" / "incidents"
    notes = ingest(base / "cases" / "01-checkout-latency" / "inbox", vocab=load_tag_vocab(base))
    all_tags = {t for n in notes for t in n.tags}
    assert {"symptom", "change", "timeline", "reversibility"} <= all_tags
    assert "billing" not in all_tags  # a default-only tag that must not leak in
