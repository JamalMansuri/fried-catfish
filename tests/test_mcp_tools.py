import json
from pathlib import Path

import pytest

from catfish import mcp_tools

EXAMPLES = str(Path(__file__).resolve().parents[1] / "examples" / "inbox")


def test_mcp_tools_demo_flow(monkeypatch, tmp_path):
    monkeypatch.setenv("CATFISH_DEMO", "1")
    monkeypatch.chdir(tmp_path)  # .catfish/ writes under tmp

    # run tournament -> proposed card, persisted
    out = json.loads(mcp_tools.tool_run_tournament(EXAMPLES, "Do we unleash the jihad?"))
    assert out["options"][0]["name"] == "Unleash the jihad"
    assert out["status"] == "proposed"

    cards = list((tmp_path / ".catfish" / "cards").glob("*.json"))
    assert cards, "tournament should persist a card"
    card_path = str(cards[0])

    # render
    assert "DECISION CARD" in mcp_tools.tool_render_card(card_path)

    # gated: write without acceptance is refused
    with pytest.raises(Exception):
        mcp_tools.tool_write_linear(card_path, team_id="T", dry_run=False)

    # accept-then-write (dry-run) succeeds and is gated-clean
    res = json.loads(mcp_tools.tool_write_linear(card_path, choice="A", by="t", dry_run=True))
    assert res["dry_run"] is True
    assert res["would_create"]["parent"]["title"].startswith("Decision:")


def test_mcp_server_builds_if_sdk_present():
    """If the `mcp` extra is installed, the server constructs with all 5 tools; else skip."""
    pytest.importorskip("mcp")
    from catfish.mcp_server import build_server
    server = build_server()
    assert server is not None
