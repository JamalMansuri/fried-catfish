from pathlib import Path

from catfish.cognition import load_cognition, render_moc, STAGES, DEFAULT_IDENTITY

ROOT = Path(__file__).resolve().parents[1]


def test_load_identity_from_file_then_default(tmp_path):
    body = load_cognition("generation", ROOT / "cognition")   # real shipped identity file
    assert "Generation agent" in body
    fallback = load_cognition("ranking", tmp_path / "missing")  # no dir -> default anchor
    assert fallback == DEFAULT_IDENTITY["ranking"]


def test_render_moc_distills_architecture(tmp_path):
    path = render_moc(tmp_path / "cog")
    text = path.read_text()
    assert "```mermaid" in text
    assert "Cognitive Architecture" in text
    assert all(f"[[{s}]]" in text for s in STAGES)   # every stage linked in the MoC
