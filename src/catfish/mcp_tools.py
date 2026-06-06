"""Tool implementations behind the MCP server.

Pure functions, NO `mcp` dependency, so they stay unit-testable in CATFISH_DEMO mode without the
[mcp] extra installed. `mcp_server.py` is the thin FastMCP glue that registers these.
"""
from __future__ import annotations

import json
from pathlib import Path

from .card import accept as accept_card
from .card import build_card, load_capability_index, load_card, save_card
from .card import render as render_card
from .knowledge import build_spine, load_tag_vocab
from .knowledge import ingest as _ingest
from .linear import write_tree
from .llm import resolve_llm
from .personas import default_critics, load_personas, parse_critics, stamp_all
from .tournament import run_tournament

CATFISH_DIR = Path(".catfish")


def _personas_dir(config_dir: str = ""):
    # --config-dir retargets a run to a domain (ADAPTING.md): personas come from
    # <config_dir>/personas; else the top-level personas/.
    p = Path(config_dir) / "personas" if config_dir else Path("personas")
    return p if p.is_dir() else None


def tool_ingest(source: str, config_dir: str = "") -> str:
    notes = _ingest(Path(source), vocab=load_tag_vocab(config_dir or "config"))
    spine = build_spine(notes, CATFISH_DIR)
    return json.dumps({"ingested": len(notes), "spine": str(spine),
                       "notes": [{"id": n.id, "title": n.title, "tags": n.tags} for n in notes]})


def tool_build_index(source: str, config_dir: str = "") -> str:
    notes = _ingest(Path(source), vocab=load_tag_vocab(config_dir or "config"))
    spine = build_spine(notes, CATFISH_DIR)
    return json.dumps({"spine": str(spine), "notes": len(notes)})


def tool_run_tournament(source: str, question: str, max_rounds: int = 2,
                        finalists: int = 3, critics: str = "", config_dir: str = "") -> str:
    llm = resolve_llm()
    notes = _ingest(Path(source), vocab=load_tag_vocab(config_dir or "config"))
    if not notes:
        return json.dumps({"error": f"no ingestible files under {source}"})
    build_spine(notes, CATFISH_DIR)
    personas = load_personas(_personas_dir(config_dir))
    perspectives = stamp_all(personas, notes)
    panel = parse_critics(critics, personas) if critics else default_critics(personas)
    result = run_tournament(question, perspectives, llm, critics=panel,
                            max_rounds=max_rounds, finalist_count=finalists)
    card = build_card(question, result, capability_index=load_capability_index(CATFISH_DIR))
    save_card(card, CATFISH_DIR / "cards")
    return json.dumps(card.to_dict())


def tool_render_card(card_path: str) -> str:
    return render_card(load_card(Path(card_path)))


def tool_write_linear(card_path: str, team_id: str = "", dry_run: bool = True,
                      choice: str = "", by: str = "") -> str:
    """Gated Linear write. Pass `choice` to accept-then-write in one human-approved call.

    Without `choice`, the card must already be accepted or `assert_approved()` raises.
    """
    card = load_card(Path(card_path))
    if choice:
        accept_card(card, decided_by=by or "mcp", choice=choice.upper())
        save_card(card, Path(card_path).parent)
        from .retro import append_decision
        append_decision(card, CATFISH_DIR)
    res = write_tree(card, dry_run=dry_run, team_id=team_id or None)
    return json.dumps(res)
