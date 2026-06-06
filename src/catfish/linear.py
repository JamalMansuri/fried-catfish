"""Gated Linear write-back: parent issue -> story children -> sub-issues, by recursive parentId.

The in-code `assert_approved()` is the guaranteed gate on every host. `parentId` is the issue
UUID, not the human key (Linear silently orphans issues if you pass "ENG-42"). Default is
dry-run: it returns the tree it WOULD create and writes nothing. Live writes need the [linear]
extra (httpx, lazy-imported) and CATFISH_LINEAR_TOKEN.
"""
from __future__ import annotations

import os

from .card import assert_approved, GateBlockedError
from .models import DecisionCard


def build_tree(card: DecisionCard) -> dict:
    """Decompose the chosen option into a parent -> stories -> sub-issues tree."""
    chosen = next((o for o in card.options if o.id == card.human_decision.choice), None)
    title = card.problem_statement
    parent = {"title": f"Decision: {title}", "body": _body(card)}
    stories = [{
        "title": f"Implement: {chosen.name}" if chosen else "Implement decision",
        "sub_issues": [{"title": f"Constraint: {p}"} for p in card.first_principles],
    }]
    return {"parent": parent, "stories": stories}


def _body(card: DecisionCard) -> str:
    from .card import render
    return "```\n" + render(card) + "\n```"


def write_tree(card: DecisionCard, *, dry_run: bool = True, team_id: str | None = None) -> dict:
    assert_approved(card)  # guaranteed gate — raises before any network call
    # evidence gate (rjmurillo/ai-agents): no write without an actual deliberation behind it
    if len(card.options) < 2:
        raise GateBlockedError(
            f"Card {card.id} has no deliberation evidence (<2 options compared). Run a tournament first."
        )
    tree = build_tree(card)
    if dry_run:
        return {"dry_run": True, "would_create": tree}

    team_id = team_id or os.environ.get("CATFISH_LINEAR_TEAM")
    if not team_id:
        raise RuntimeError(
            "live Linear write needs a team id: pass team_id (CLI --team) or set CATFISH_LINEAR_TEAM. "
            "Linear's issueCreate silently orphans issues created with no teamId."
        )
    token = os.environ.get("CATFISH_LINEAR_TOKEN")
    if not token:
        raise RuntimeError("live Linear write needs CATFISH_LINEAR_TOKEN (and catfish[linear]).")
    try:
        import httpx  # optional [linear] extra
    except ImportError as e:
        raise RuntimeError("live Linear write needs `pip install catfish[linear]`.") from e

    client = _LinearClient(httpx, token)
    parent_id = client.create_issue(tree["parent"]["title"], tree["parent"]["body"], team_id=team_id)
    card.linear.parent_issue_id = parent_id
    for story in tree["stories"]:
        story_id = client.create_issue(story["title"], "", team_id=team_id, parent_id=parent_id)
        card.linear.story_ids.append(story_id)
        for sub in story["sub_issues"]:
            sub_id = client.create_issue(sub["title"], "", team_id=team_id, parent_id=story_id)
            card.linear.sub_issue_ids.append(sub_id)
    return {"dry_run": False, "parent_issue_id": parent_id,
            "story_ids": card.linear.story_ids, "sub_issue_ids": card.linear.sub_issue_ids}


class _LinearClient:
    URL = "https://api.linear.app/graphql"
    MUT = ("mutation($input: IssueCreateInput!){ issueCreate(input:$input){ issue{ id } } }")

    def __init__(self, httpx, token):
        self._httpx = httpx
        self._headers = {"Authorization": token, "Content-Type": "application/json"}

    def create_issue(self, title, description, *, team_id=None, parent_id=None) -> str:
        inp = {"title": title, "description": description}
        if team_id:
            inp["teamId"] = team_id
        if parent_id:
            inp["parentId"] = parent_id  # UUID, not the ENG-42 key
        r = self._httpx.post(self.URL, headers=self._headers,
                             json={"query": self.MUT, "variables": {"input": inp}}, timeout=30)
        r.raise_for_status()
        return r.json()["data"]["issueCreate"]["issue"]["id"]
