from pathlib import Path

from catfish.codemap import scan_python, render_foam

SRC = Path(__file__).resolve().parents[1] / "src"


def test_scan_finds_modules_and_edges():
    mods = scan_python(SRC)
    assert "catfish.tournament" in mods
    t = mods["catfish.tournament"]
    # tournament depends on llm, models, personas (intra-repo edges resolved)
    assert "catfish.llm" in t["depends_on"]
    assert "catfish.models" in t["depends_on"]
    assert "catfish.personas" in t["depends_on"]
    assert "run_tournament" in t["funcs"]


def test_models_is_most_load_bearing():
    mods = scan_python(SRC)
    assert mods["catfish.models"]["ref_count"] >= 3  # everything imports the schemas
    assert mods["catfish.models"]["used_by"]


def test_value_is_a_proposal_not_a_fact():
    mods = scan_python(SRC)
    v = mods["catfish.card"]["value"]
    assert v["status"] == "proposed"
    assert v["value_statement"].startswith("(proposed)")


def test_render_foam_writes_two_layers(tmp_path):
    mods = scan_python(SRC)
    n = render_foam(mods, tmp_path / "wiki", tmp_path / ".catfish")
    assert n == len(mods) + 2                        # per-module notes + index + business
    index = (tmp_path / "wiki" / "index.md").read_text()
    assert "```mermaid" in index
    assert "[[catfish-models]]" in index            # Foam wikilink
    assert "[[business]]" in index                   # links to the PM layer
    # PM business layer exists and groups by value
    business = (tmp_path / "wiki" / "business.md").read_text()
    assert "Business Capability Map" in business
    assert "[[catfish-" in business
    assert (tmp_path / "wiki" / "catfish-tournament.md").exists()
    note = (tmp_path / "wiki" / "catfish-tournament.md").read_text()
    assert "[[catfish-llm]]" in note
