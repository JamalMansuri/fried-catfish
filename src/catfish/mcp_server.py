"""MCP stdio server (the [mcp] extra). Exposes the catfish tools to Claude Code / Codex.

Imported lazily by `server.cmd_serve`; if the `mcp` SDK is not installed this module fails to import
and the CLI prints the static tool catalog instead. The tool LOGIC lives in `mcp_tools.py` (no MCP
dependency) so it stays unit-testable without the extra. The single GATED tool, `catfish_write_linear`,
is guarded in code by `assert_approved()` and (on Claude Code) by the PreToolUse hook in hooks/hooks.json.
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP  # the [mcp] extra; ImportError is handled by the caller

from . import mcp_tools


def build_server() -> "FastMCP":
    """Construct the FastMCP server with all catfish tools registered (no transport started)."""
    mcp = FastMCP("catfish")

    @mcp.tool()
    def catfish_ingest(source: str, config_dir: str = "") -> str:
        """Ingest a folder of notes/emails/transcripts into a normalized Map of Content + JSONL spine.

        `config_dir` retargets the domain (a folder with tags.yaml + personas/); default = config/. See ADAPTING.md.
        """
        return mcp_tools.tool_ingest(source, config_dir)

    @mcp.tool()
    def catfish_build_index(source: str, config_dir: str = "") -> str:
        """Rebuild the JSONL Map-of-Content spine from a source folder. `config_dir` retargets the tag vocab (see ADAPTING.md)."""
        return mcp_tools.tool_build_index(source, config_dir)

    @mcp.tool()
    def catfish_run_tournament(source: str, question: str, max_rounds: int = 2,
                               finalists: int = 3, critics: str = "", config_dir: str = "") -> str:
        """Run the generate->debate->evolve tournament over a folder and return a PROPOSED decision card.

        Does NOT write to Linear. `critics` is an optional panel spec like "skeptic:grumpy,security:paranoid".
        `config_dir` retargets the run to a domain (a folder with tags.yaml + personas/); default = config/ + personas/. See ADAPTING.md.
        """
        return mcp_tools.tool_run_tournament(source, question, max_rounds, finalists, critics, config_dir)

    @mcp.tool()
    def catfish_render_card(card_path: str) -> str:
        """Render a saved decision card (.catfish/cards/<id>.json) as a terse text card."""
        return mcp_tools.tool_render_card(card_path)

    @mcp.tool()
    def catfish_write_linear(card_path: str, team_id: str = "", dry_run: bool = True,
                             choice: str = "", by: str = "") -> str:
        """GATED: write the accepted card's parent->story->sub-issue tree to Linear.

        Requires an accepted card (in-code assert_approved). Pass `choice` (A/B/C) to accept-then-write
        in one human-approved call; the host should prompt for approval (see hooks/hooks.json).
        `dry_run=True` returns the tree it WOULD create without writing. Live writes need a `team_id`
        (or CATFISH_LINEAR_TEAM) and CATFISH_LINEAR_TOKEN.
        """
        return mcp_tools.tool_write_linear(card_path, team_id, dry_run, choice, by)

    return mcp


def run_stdio(tools=None) -> int:
    """Start the MCP stdio server (blocks). `tools` (the static catalog) is accepted for the caller's
    contract but ignored — the real tools are registered in build_server()."""
    build_server().run()
    return 0
