"""CLI dispatcher + MCP server entry point.

`catfish` with no subcommand starts the MCP stdio server (Claude Code / Codex). Subcommands
run the same engine from the terminal. `server.py` speaks MCP only and dispatches; it has no
host-specific logic.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import __version__

# MCP tool catalog (gated column is the safety contract).
TOOLS = [
    {"name": "catfish_ingest", "purpose": "files -> normalized .md + spine", "gated": False},
    {"name": "catfish_build_index", "purpose": "rebuild the JSONL spine", "gated": False},
    {"name": "catfish_run_tournament", "purpose": "run the loop, return a card", "gated": False},
    {"name": "catfish_render_card", "purpose": "render a card to text", "gated": False},
    {"name": "catfish_write_linear", "purpose": "write the parentId tree", "gated": True},
]

CATFISH_DIR = Path(".catfish")
MEMORY_DIR = Path(".memory")


def _personas_dir() -> Path | None:
    p = Path("personas")
    return p if p.is_dir() else None


def _friendly_llm():
    from .llm import resolve_llm, LLMError
    try:
        return resolve_llm()
    except LLMError as e:
        print(f"\n✗ {e}\n", file=sys.stderr)
        print("  Quick start (free, offline):  CATFISH_DEMO=1 catfish tournament examples/lunch/inbox \"<question>\" --config-dir examples/lunch\n",
              file=sys.stderr)
        raise SystemExit(2)


def cmd_tournament(args) -> int:
    from .knowledge import ingest, build_spine, load_tag_vocab
    from .personas import load_personas, stamp_all, parse_critics, default_critics
    from .tournament import run_tournament
    from .card import build_card, render, save_card, accept, load_capability_index
    from .tournament_view import render_tournament, sections, report_blocks
    from .memory import write_session
    from .linear import write_tree

    llm = _friendly_llm()
    # --config-dir retargets a run to a domain: tags.yaml + personas/ are read from that folder
    # (see ADAPTING.md). Default = top-level config/ + personas/.
    config_dir = getattr(args, "config_dir", None)
    notes = ingest(Path(args.source), vocab=load_tag_vocab(config_dir or "config"))
    if not notes:
        print(f"✗ no ingestible files under {args.source}", file=sys.stderr)
        return 1
    build_spine(notes, CATFISH_DIR)
    personas_dir = (Path(config_dir) / "personas") if config_dir else _personas_dir()
    personas = load_personas(personas_dir)
    perspectives = stamp_all(personas, notes)
    # Default reflection panel = the loaded persona files (personality + mood + grounding docs) + a
    # neutral evaluator — not thin generic roles. --critics overrides with a custom mood-flavored panel.
    critics = parse_critics(args.critics, personas) if args.critics else default_critics(personas)

    panel = ", ".join(f"{c.id}:{c.mood}" if c.mood else c.id for c in critics) if critics else "default"
    print(f"· ingested {len(notes)} notes · {len(perspectives)} persona lenses · panel=[{panel}] · judge={llm.name}\n")
    result = run_tournament(args.question, perspectives, llm, critics=critics,
                            max_rounds=args.max_rounds, finalist_count=args.finalists)
    card = build_card(args.question, result, capability_index=load_capability_index(CATFISH_DIR))

    if args.decide:
        accept(card, decided_by=args.by or "cli", choice=args.decide.upper())

    # Paced reveal for the recorded demo (CATFISH_DEMO_PACED=1): the engine finishes in ~0.07s,
    # so without pauses the whole tournament scrolls off-screen and only the card is seen.
    paced = os.environ.get("CATFISH_DEMO_PACED") == "1"
    if paced:
        import time
        for blk in sections(result):
            print(blk + "\n", flush=True)
            time.sleep(float(os.environ.get("CATFISH_DEMO_PACE_SEC", "1.3")))
        time.sleep(0.4)
    else:
        print(render_tournament(result))
        print(render(card))   # the paced demo shows a focused panel instead of the wide card
    saved = save_card(card, CATFISH_DIR / "cards")
    write_session(
        MEMORY_DIR, objective=args.question,
        attempted=[f"{f.name} (score {f.bt_score:.2f})" for f in result.finalists],
        failed=[c.name for c in result.candidates if c.status == "pruned"],
        human_directions=[f"decided {args.decide}" ] if args.decide else [],
        open_threads=[] if args.decide else ["awaiting human decision on the card"],
        next_step="write Linear tree" if args.decide else "human reviews card and picks an option",
        status="closed" if args.decide else "open",
    )

    if card.status == "accepted":
        from .retro import append_decision
        append_decision(card, CATFISH_DIR)                          # real: record the call to the ledger
        team = getattr(args, "team", None) or os.environ.get("CATFISH_LINEAR_TEAM")
        res = write_tree(card, dry_run=not args.linear, team_id=team)
        if not paced:
            print()
            if res.get("dry_run"):
                print("LINEAR (dry-run — nothing written):")
                print(json.dumps(res["would_create"], indent=2))
                print("\n  add --linear (+ CATFISH_LINEAR_TOKEN, catfish[linear]) to actually create the tree.")
            else:
                print(f"LINEAR: created parent {res['parent_issue_id']} + {len(res['story_ids'])} stories.")
    elif not paced:
        print(f"\nGate open. To accept and draft the Linear tree (dry-run):")
        print(f"  catfish accept {saved} --choice A --by you")

    # Demo climax: the REAL decision report, typed out block-by-block + colored — the source truths,
    # the grounded reasoning, the machine-proposed-vs-human-decided split, and what got recorded.
    if paced:
        import time
        print("\033[2J\033[3J\033[H", flush=True)
        for blk in report_blocks(notes, card):
            print(blk + "\n", flush=True)
            time.sleep(float(os.environ.get("CATFISH_DEMO_REPORT_PACE", "1.1")))
    return 0


def cmd_ingest(args) -> int:
    from .knowledge import ingest, build_spine, load_tag_vocab
    config_dir = getattr(args, "config_dir", None)
    notes = ingest(Path(args.source), vocab=load_tag_vocab(config_dir or "config"))
    spine = build_spine(notes, CATFISH_DIR)
    print(f"ingested {len(notes)} notes -> {spine}")
    for n in notes:
        print(f"  {n.id}  {n.title[:48]:48}  tags={n.tags}")
    return 0


def cmd_accept(args) -> int:
    from .card import load_card, accept, render, save_card
    from .linear import write_tree
    card = load_card(Path(args.card))
    accept(card, decided_by=args.by or "cli", choice=args.choice.upper(), notes=args.notes)
    save_card(card, Path(args.card).parent)
    from .retro import append_decision
    append_decision(card, CATFISH_DIR)
    print(render(card))
    print()
    team = getattr(args, "team", None) or os.environ.get("CATFISH_LINEAR_TEAM")
    res = write_tree(card, dry_run=not args.linear, team_id=team)
    if res.get("dry_run"):
        print("LINEAR (dry-run — nothing written):")
        print(json.dumps(res["would_create"], indent=2))
    else:
        print(f"LINEAR: created parent {res['parent_issue_id']} + {len(res['story_ids'])} stories.")
    return 0


def cmd_retro(args) -> int:
    from .card import load_card
    from .retro import load_rows, record_review, render_ledger, render_review
    if not args.card:
        print(render_ledger(load_rows(CATFISH_DIR)))
        return 0
    has_update = any([args.outcome, args.went_well, args.went_wrong, args.lessons, args.repeat])
    if has_update:
        repeat = {"yes": True, "y": True, "no": False, "n": False}.get((args.repeat or "").lower()) if args.repeat else None
        card = record_review(args.card, outcome=args.outcome or "", went_well=args.went_well or "",
                             went_wrong=args.went_wrong or "", would_repeat=repeat,
                             lessons=args.lessons or "", by=args.by or "cli", catfish_dir=CATFISH_DIR)
        print(render_review(card))
    else:
        print(render_review(load_card(Path(args.card))))
    return 0


def cmd_map(args) -> int:
    from .codemap import scan_python, render_foam
    modules = scan_python(Path(args.source))
    if not modules:
        print(f"✗ no Python modules found under {args.source}", file=sys.stderr)
        return 1
    n = render_foam(modules, Path(args.out), CATFISH_DIR)
    ranked = sorted(modules.values(), key=lambda m: -m["ref_count"])[:3]
    print(f"mapped {len(modules)} capabilities -> {args.out}/ ({n} notes)")
    print("  most load-bearing: " + ", ".join(f"{m['name']} (used by {m['ref_count']})" for m in ranked))
    print(f"\nOpen the folder in VS Code with the Foam extension for the graph, "
          f"or view {args.out}/index.md (Mermaid graph renders on GitHub).")
    return 0


def cmd_roster(args) -> int:
    from .personas import load_personas, roster
    print(roster(load_personas(_personas_dir())))
    return 0


def cmd_architecture(args) -> int:
    from .cognition import render_moc, STAGES, load_cognition
    path = render_moc(args.dir)
    print(f"distilled the cognitive architecture -> {path}")
    for s in STAGES:
        print(f"  [[{s}]]  {load_cognition(s, args.dir).split('Mandate:')[-1].split('.')[0].strip()[:60]}")
    print(f"\nOpen {args.dir}/ in VS Code with Foam for the loop graph. Edit the .md files to change the architecture.")
    return 0


def cmd_serve(args) -> int:
    try:
        from .mcp_server import run_stdio  # only present/works with the [mcp] extra
    except Exception:  # noqa: BLE001
        print("MCP tool catalog:")
        for t in TOOLS:
            print(f"  {t['name']:24} {'[GATED]' if t['gated'] else '       '}  {t['purpose']}")
        print("\nMCP stdio server needs `pip install catfish[mcp]`. "
              "CLI works now — try: catfish tournament <dir> \"<question>\"")
        return 0
    return run_stdio(TOOLS)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="catfish", description="Tournament of plans -> one decision card.")
    p.add_argument("--version", action="version", version=f"catfish {__version__}")
    sub = p.add_subparsers(dest="cmd")

    t = sub.add_parser("tournament", help="run a decision tournament over a folder")
    t.add_argument("source")
    t.add_argument("question")
    t.add_argument("--max-rounds", type=int, default=2, dest="max_rounds")
    t.add_argument("--finalists", type=int, default=3)
    t.add_argument("--critics", help="custom critic panel, e.g. skeptic:grumpy,security:paranoid,qa:bad_mood")
    t.add_argument("--config-dir", dest="config_dir",
                   help="folder holding tags.yaml + personas/ to retarget the run to a domain "
                        "(default: config/ + personas/). See ADAPTING.md / examples/lunch.")
    t.add_argument("--decide", help="auto-accept option (A/B/C) — skips the manual gate")
    t.add_argument("--by", help="decider name (with --decide)")
    t.add_argument("--linear", action="store_true", help="actually write Linear (default: dry-run)")
    t.add_argument("--team", help="Linear team id (or CATFISH_LINEAR_TEAM env) — required for --linear")
    t.set_defaults(func=cmd_tournament)

    sub.add_parser("roster", help="show the persona × mood roster (choose your panel)").set_defaults(func=cmd_roster)

    mp = sub.add_parser("map", help="build a logic-based Map of Content of a codebase (Foam wiki)")
    mp.add_argument("source", help="source dir to map (e.g. src)")
    mp.add_argument("--out", default="wiki", help="output wiki dir (default: wiki)")
    mp.set_defaults(func=cmd_map)

    ar = sub.add_parser("architecture", help="distill the cognitive architecture into its own MoC")
    ar.add_argument("--dir", default="cognition", help="cognition dir (default: cognition)")
    ar.set_defaults(func=cmd_architecture)

    i = sub.add_parser("ingest", help="ingest a folder into the MoC spine")
    i.add_argument("source")
    i.add_argument("--config-dir", dest="config_dir",
                   help="folder holding tags.yaml to tag with a domain vocabulary (default: config/)")
    i.set_defaults(func=cmd_ingest)

    a = sub.add_parser("accept", help="accept a card and write/preview its Linear tree")
    a.add_argument("card", help="path to .catfish/cards/<id>.json")
    a.add_argument("--choice", required=True, help="option id A/B/C")
    a.add_argument("--by", help="decider name")
    a.add_argument("--notes")
    a.add_argument("--linear", action="store_true")
    a.add_argument("--team", help="Linear team id (or CATFISH_LINEAR_TEAM env) — required for --linear")
    a.set_defaults(func=cmd_accept)

    rt = sub.add_parser("retro", help="list decisions, or record the outcome of one (close the loop for retros)")
    rt.add_argument("card", nargs="?", help="path to .catfish/cards/<id>.json (omit to list all decisions)")
    rt.add_argument("--outcome", help="what actually happened after the decision shipped")
    rt.add_argument("--went-well", dest="went_well")
    rt.add_argument("--went-wrong", dest="went_wrong")
    rt.add_argument("--repeat", help="decide the same again? yes/no")
    rt.add_argument("--lessons")
    rt.add_argument("--by")
    rt.set_defaults(func=cmd_retro)

    sub.add_parser("serve", help="run the MCP stdio server (default if no subcommand)").set_defaults(func=cmd_serve)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if not getattr(args, "cmd", None):
        return cmd_serve(args)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
