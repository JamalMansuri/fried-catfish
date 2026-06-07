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


def test_ingest_skips_hidden_dirs(tmp_path):
    # files inside dot-dirs (.memory, .pytest_cache, .git, .catfish) must not be ingested —
    # the walk only skipped .catfish + dotfiles before, so .memory/ leaked in.
    (tmp_path / "real.md").write_text("# Real Note\nbody\n")
    hidden = tmp_path / ".memory" / "sessions"
    hidden.mkdir(parents=True)
    (hidden / "session.md").write_text("# Hidden Session\nshould be skipped\n")
    notes = ingest(tmp_path, vocab={})
    assert [n.title for n in notes] == ["Real Note"]


def test_ingest_reads_title_from_frontmatter(tmp_path):
    # a Foam-style page (YAML frontmatter) must take its title from `title:`, not the `---` fence.
    (tmp_path / "page.md").write_text(
        "---\nid: index\ntitle: Codebase Map\ntype: moc\n---\n\n# Codebase Map\nthe body.\n"
    )
    notes = ingest(tmp_path, vocab={})
    assert len(notes) == 1
    assert notes[0].title == "Codebase Map"
    assert not notes[0].summary.startswith("---")   # summary is taken from the body, past the fence
