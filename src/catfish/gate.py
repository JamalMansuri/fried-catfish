"""PreToolUse gate hook (Claude Code).

Wired in hooks/hooks.json to fire before `catfish_write_linear`. It blocks the write so a
human must confirm the decision card first. This is the transport-layer gate; the guaranteed
gate is `card.assert_approved()` inside `linear.py`, which runs regardless of host config.
"""
from __future__ import annotations

import json
import sys


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        payload = {}
    tool = payload.get("tool_name") or payload.get("tool", "")
    if tool == "catfish_write_linear":
        # Force the host to ASK the human before any Linear write — not hard-deny, which would make the
        # gated write impossible to complete in-host. The in-code assert_approved() in linear.py is the
        # guarantee regardless of whether the host honors this decision.
        decision = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": (
                    "Catfish: writing to Linear requires explicit human approval of the decision card. "
                    "Confirm the chosen option before the ticket tree is created."
                ),
            }
        }
        print(json.dumps(decision))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
