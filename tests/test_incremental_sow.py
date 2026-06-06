"""Roadmap #2: incremental sow. build_spine must UPSERT (keyed by source_hash), not overwrite.

Re-ingesting an unchanged corpus is idempotent; new/changed notes are added/updated; a note added
once (e.g. a decision Note from item #1) survives a later ingest of a different note set.
"""
import json

from catfish.knowledge import build_spine
from catfish.models import Note


def _rows(spine):
    return [json.loads(line) for line in spine.read_text().splitlines() if line.strip()]


def test_spine_rows_carry_source_hash(tmp_path):
    note = Note(id="nt-0001", title="A", summary="first", source_hash="sha256:aaa")
    spine = build_spine([note], tmp_path / ".catfish")
    rows = _rows(spine)
    assert len(rows) == 1
    assert rows[0]["source_hash"] == "sha256:aaa"


def test_idempotent_then_union_with_no_duplicate_source_hash(tmp_path):
    catfish_dir = tmp_path / ".catfish"

    # set X
    x = [
        Note(id="nt-0001", title="A", summary="A v1", source_hash="sha256:aaa"),
        Note(id="nt-0002", title="B", summary="B v1", source_hash="sha256:bbb"),
    ]
    spine = build_spine(x, catfish_dir)

    # re-ingesting the SAME corpus is idempotent
    spine = build_spine(x, catfish_dir)
    assert len(_rows(spine)) == 2

    # set Y overlaps X by source_hash (aaa, updated content) and adds a new note (ccc)
    y = [
        Note(id="nt-0001", title="A", summary="A v2 UPDATED", source_hash="sha256:aaa"),
        Note(id="nt-0003", title="C", summary="C v1", source_hash="sha256:ccc"),
    ]
    spine = build_spine(y, catfish_dir)

    rows = _rows(spine)
    by_hash = {r["source_hash"]: r for r in rows}

    # UNION of X and Y with no duplicate source_hash rows
    assert set(by_hash) == {"sha256:aaa", "sha256:bbb", "sha256:ccc"}
    assert len(rows) == 3
    # overlap content was updated
    assert by_hash["sha256:aaa"]["summary"] == "A v2 UPDATED"
    # the non-overlapping earlier note survived the later ingest
    assert by_hash["sha256:bbb"]["summary"] == "B v1"


def test_legacy_row_without_source_hash_keys_on_id(tmp_path):
    catfish_dir = tmp_path / ".catfish"
    catfish_dir.mkdir(parents=True)
    spine = catfish_dir / "_graph_index.jsonl"
    # a legacy row predating source_hash in spine_row
    spine.write_text(json.dumps({"id": "nt-0001", "title": "legacy", "summary": "old"}) + "\n")

    build_spine([Note(id="nt-0002", title="new", source_hash="sha256:zzz")], catfish_dir)
    rows = _rows(spine)
    keys = {r.get("source_hash") or r.get("id") for r in rows}
    assert keys == {"nt-0001", "sha256:zzz"}
    assert len(rows) == 2
