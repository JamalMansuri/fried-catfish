"""Shared data models for Catfish.

Plain dataclasses + dict (de)serialization. No third-party deps so the demo path
imports on a bare Python 3.11.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Optional


# --- hard terseness caps (words) enforced before a card reaches the human ---
CARD_WORD_CAPS = {
    "problem_statement": 30,
    "first_principle": 20,
    "solution": 25,
    "trade_off": 15,
    "recommendation": 20,
}

VALUE_TYPES = ("revenue", "cost", "risk", "compliance", "retention", "enablement")


def _ulid(prefix: str, n: int) -> str:
    """Monotonic, dependency-free id. Deterministic per (prefix, n) for reproducible runs."""
    return f"{prefix}-{n:04d}"


# ---------------------------------------------------------------- knowledge

@dataclass
class Note:
    id: str
    title: str
    type: str = "source"           # note|moc|source|concept|persona|code-capability|code-entrypoint
    tags: list[str] = field(default_factory=list)
    summary: str = ""
    status: str = "seedling"
    source_hash: str = ""
    source_type: str = "md"
    path: str = ""
    body: str = ""

    def spine_row(self) -> dict:
        return {
            "id": self.id, "title": self.title, "type": self.type,
            "status": self.status, "summary": self.summary, "tags": self.tags,
        }


# ---------------------------------------------------------------- personas

@dataclass
class Persona:
    id: str
    role: str
    goal: str
    backstory: str = ""
    utility_fn: str = ""
    filter: dict = field(default_factory=dict)
    mood: str = ""                                   # emotional-state dial (tone/severity)
    knowledge: list[str] = field(default_factory=list)  # glob(s) of docs this persona "knows"

    def system_prompt(self, token_cap_words: int = 120, mood_modifier: str = "",
                      knowledge: str = "") -> str:
        # role + goal + mood + utility_fn; backstory dropped under cap (PRISM: length scales damage)
        parts = [f"You are a {self.role}.", self.goal]
        if mood_modifier:
            parts.append(mood_modifier)
        parts.append(f"You judge by: {self.utility_fn}.")
        text = " ".join(p for p in parts if p)
        words = text.split()
        if len(words) > token_cap_words:
            text = " ".join(words[:token_cap_words])
        if knowledge:
            # knowledge is appended AFTER the cap — it is reference data, not persona inflation
            text += "\n\nReference (documentation you know):\n" + knowledge
        return text


@dataclass
class PerspectiveArtifact:
    """What a persona surfaces over the MoC — a filtered, typed view, never a copy."""
    persona_id: str
    role: str
    note_ids: list[str] = field(default_factory=list)
    highlights: list[str] = field(default_factory=list)   # summaries of matched notes

    def as_context(self) -> str:
        if not self.highlights:
            return f"[{self.role}] (no directly relevant context found)"
        body = "\n".join(f"  - {h}" for h in self.highlights)
        return f"[{self.role}] relevant context:\n{body}"


# ---------------------------------------------------------------- tournament

@dataclass
class Critique:
    critic_role: str
    text: str
    round: int = 0


@dataclass
class MatchRecord:
    opponent_id: str
    outcome: str          # win|loss|tie
    judge_model: str
    round: int
    tier: str             # early|finalist


@dataclass
class Candidate:
    id: str
    name: str
    text: str
    round_created: int = 0
    source: str = "generation"      # generation|evolution
    persona_tags: list[str] = field(default_factory=list)
    # Grounding set: notes available when this candidate was generated (for evolution, inherited
    # from its survivor parents). NOT a verified per-claim derivation — the engine never checks a
    # plan's text actually depends on a note. It is "what was in the room", not "what it cites".
    note_ids: list[str] = field(default_factory=list)
    critiques: list[Critique] = field(default_factory=list)
    bt_score: Optional[float] = None
    match_record: list[MatchRecord] = field(default_factory=list)
    status: str = "active"          # active|pruned|finalist

    def wins(self) -> float:
        s = 0.0
        for m in self.match_record:
            s += 1.0 if m.outcome == "win" else (0.5 if m.outcome == "tie" else 0.0)
        return s


@dataclass
class MetaReview:
    round: int
    recurring_concerns: list[str] = field(default_factory=list)
    pattern_gaps: list[str] = field(default_factory=list)
    bias_flags: list[str] = field(default_factory=list)
    next_round_focus: str = ""


# ---------------------------------------------------------------- decision card

@dataclass
class TradeOffs:
    good: str = ""
    neutral: str = ""
    bad: str = ""


@dataclass
class Option:
    id: str               # "A", "B", "C"
    name: str
    solution: str
    trade_offs: TradeOffs = field(default_factory=TradeOffs)
    bt_score: float = 0.0
    risks: list[str] = field(default_factory=list)   # critic-surfaced load-bearing risks (for retros)


@dataclass
class Recommendation:
    option: str = ""      # references Option.id
    rationale: str = ""


@dataclass
class HumanDecision:
    decided_by: Optional[str] = None
    choice: Optional[str] = None      # references Option.id; null blocks Linear writes
    notes: Optional[str] = None


@dataclass
class LinearRefs:
    parent_issue_id: Optional[str] = None
    story_ids: list[str] = field(default_factory=list)
    sub_issue_ids: list[str] = field(default_factory=list)


@dataclass
class Review:
    """Retrospective on a shipped decision. A decision is not 'done' when shipped — only when reviewed."""
    status: str = "pending"            # pending|done
    outcome: str = ""                  # what actually happened after the decision shipped
    went_well: str = ""
    went_wrong: str = ""
    would_repeat: Optional[bool] = None
    lessons: str = ""
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None


@dataclass
class DecisionCard:
    id: str
    problem_statement: str
    status: str = "proposed"          # proposed|accepted|rejected|superseded
    first_principles: list[str] = field(default_factory=list)
    options: list[Option] = field(default_factory=list)
    recommendation: Recommendation = field(default_factory=Recommendation)
    human_decision: HumanDecision = field(default_factory=HumanDecision)
    linear: LinearRefs = field(default_factory=LinearRefs)
    affected_capabilities: list[str] = field(default_factory=list)
    business_impact: Optional[str] = None
    # Card-level provenance: the source notes the whole tournament reasoned over (union over
    # finalists). Card-level on purpose — the engine grounds all options in the same combined
    # context, so this is NOT per-option/per-claim attribution (that needs span pointers, later).
    grounding_refs: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)    # meta-review: what the panel kept worrying about
    review: Review = field(default_factory=Review)        # retrospective, filled later via `catfish retro`
    created_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "DecisionCard":
        d = dict(d)
        d["options"] = [
            Option(
                id=o["id"], name=o["name"], solution=o["solution"],
                trade_offs=TradeOffs(**o.get("trade_offs", {})),
                bt_score=o.get("bt_score", 0.0),
                risks=o.get("risks", []),
            )
            for o in d.get("options", [])
        ]
        d["recommendation"] = Recommendation(**d.get("recommendation", {}))
        d["human_decision"] = HumanDecision(**d.get("human_decision", {}))
        d["linear"] = LinearRefs(**d.get("linear", {}))
        d["review"] = Review(**d.get("review", {}))
        return cls(**d)
