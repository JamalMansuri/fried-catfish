"""Markdown session memory + handoff notes.

SESSION_INDEX.md is a pointer table (the only file a cold start reads). Each session file is
cold-start-parseable and preserves dead-ends. Human directions live in their own override section.
"""
from __future__ import annotations

import time
from pathlib import Path


def _index_row(session_id, status, importance, objective) -> str:
    return f"| {session_id} | {status} | {importance} | {objective} |"


def write_session(memory_dir: Path, *, objective: str, attempted: list[str],
                  failed: list[str], human_directions: list[str], open_threads: list[str],
                  next_step: str, status: str = "open", importance: str = "normal") -> Path:
    memory_dir = Path(memory_dir)
    sessions = memory_dir / "sessions"
    sessions.mkdir(parents=True, exist_ok=True)
    sid = time.strftime("%Y%m%d-%H%M%S")

    def _bullets(items, prefix="- ", empty="- (none)"):
        return [f"{prefix}{a}" for a in items] or [empty]

    body = [
        f"# Session {sid}", "",
        f"- status: {status}",
        f"- importance: {importance}",
        f"- created: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}", "",
        "## Objective", objective or "(none)", "",
        "## What Was Attempted", *_bullets(attempted), "",
        "## What Failed / Dead Ends", *_bullets(failed), "",
        "## Human Directions / Decisions", *_bullets(human_directions, empty="- (none yet)"), "",
        "## Open Threads", *_bullets(open_threads, prefix="- [ ] "), "",
        "## Next Step", next_step or "(none)", "",
    ]
    path = sessions / f"{sid}.md"
    path.write_text("\n".join(body))

    index = memory_dir / "SESSION_INDEX.md"
    header = ("# Session Memory Index\n\n"
              "| id | status | importance | objective |\n"
              "|----|--------|------------|-----------|\n")
    row = _index_row(sid, status, importance, (objective or "")[:60])
    if index.exists():
        index.write_text(index.read_text().rstrip() + "\n" + row + "\n")
    else:
        index.write_text(header + row + "\n")
    return path
