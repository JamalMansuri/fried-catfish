"""Personas = reusable lenses. Each stamps a perspective-map: a filtered, typed view over the
MoC, never a copy. Coarse roles only (long/expert personas hurt accuracy — PRISM 2603.18507),
run in parallel isolation before the tournament (debate converges to groupthink — 2511.07784).
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from .models import Note, Persona, PerspectiveArtifact

# Emotional-state dials. A mood is a tone/severity lever, NOT an accuracy booster — it changes
# how hard a critic pushes and what register it uses, not whether it is right (the persona
# double-edged-sword finding, arXiv:2311.10054, applies). Keep them short.
MOODS = {
    "calm":       "You are calm and methodical; weigh things evenly.",
    "bad_mood":   "You are in a bad mood: irritable, terse, and unforgiving. You have seen this "
                  "kind of failure before and you assume the happy path is a lie.",
    "grumpy":     "You are grumpy and short-tempered; you nitpick and trust nothing you cannot verify.",
    "paranoid":   "You are paranoid: assume every input is hostile and every boundary breached "
                  "until proven otherwise.",
    "burned_out": "You are burned out; push back hard on anything that adds scope or risk.",
    "optimistic": "You are optimistic and solution-oriented; look for the fastest path that could work.",
    "pedantic":   "You are pedantic about correctness, naming, and spec compliance; small "
                  "inconsistencies bother you.",
    "exhausted":  "You are exhausted; spend energy only on the one thing that actually matters here.",
    # Project Riley (Inside-Out) named emotions — first-class agents, not adjectives (arXiv:2505.20521)
    "joy":        "You are upbeat and momentum-seeking; you look for the upside and what will delight.",
    "sadness":    "You are melancholic and honest about loss; you name what will be given up.",
    "fear":       "You are anxious and vigilant; you assume the worst case is the likely case.",
    "anger":      "You are angry and confrontational; you attack the weakest assumption without mercy.",
    "disgust":    "You are contemptuous of sloppiness; you reject anything off-standard or over-engineered.",
}


def mood_modifier(mood: str) -> str:
    """Resolve a mood id to its modifier sentence. An unknown id is treated as a literal mood."""
    if not mood:
        return ""
    return MOODS.get(mood, mood)

# Built-in defaults so the demo runs without any persona files on disk.
DEFAULT_PERSONAS = [
    Persona(
        id="skeptic", role="Adversarial Critic",
        goal="Find the load-bearing assumption that, if wrong, collapses the plan.",
        backstory="Assumes every proposal hides a fatal flaw. Reads for what is not said.",
        utility_fn="identified single-points-of-failure and unstated assumptions",
        filter={"tags_any": ["risk", "dependency", "assumption", "constraint"], "tags_exclude": [], "types": []},
    ),
    Persona(
        id="pm", role="Delivery PM",
        goal="Surface timeline, capacity, scope, and dependency risk to delivery.",
        backstory="Owns the schedule and the team's finite capacity.",
        utility_fn="delivery feasibility under real constraints",
        filter={"tags_any": ["timeline", "resource", "scope", "milestone", "dependency", "billing", "launch"],
                "tags_exclude": [], "types": []},
    ),
    Persona(
        id="security", role="Security Reviewer",
        goal="Surface attack surface, auth/permission, and data-exposure risk.",
        backstory="Treats every external boundary as hostile until proven otherwise.",
        utility_fn="reduced attack surface and closed findings",
        filter={"tags_any": ["auth", "permission", "external", "pii", "credential", "network", "security"],
                "tags_exclude": [], "types": []},
    ),
]

# Project Riley (Inside-Out) starter characters — named emotions as first-class critic agents
# (arXiv:2505.20521). Critic-only (no filter) so they don't double as MoC perspective lenses;
# they compose with roles. Note: `anger` carries the Devil's-Advocate dissent role, which the
# research says is what actually breaks consensus — emotion rides on top of that role.
RILEY_CHARACTERS = [
    Persona(id="joy", role="Joy", mood="joy",
            goal="Find why this plan could delight users and build momentum.",
            utility_fn="upside, morale, and shipping momentum"),
    Persona(id="sadness", role="Sadness", mood="sadness",
            goal="Name honestly what will be lost or grieved if this ships.",
            utility_fn="honest losses and second-order costs"),
    Persona(id="fear", role="Fear", mood="fear",
            goal="Name what could go catastrophically wrong.",
            utility_fn="catastrophic and tail risks surfaced"),
    Persona(id="anger", role="Anger (Devil's Advocate)", mood="anger",
            goal="Attack the weakest load-bearing assumption without mercy.",
            utility_fn="broken consensus and fatal flaws"),
    Persona(id="disgust", role="Disgust", mood="disgust",
            goal="Reject what is sloppy, over-engineered, or off-standard.",
            utility_fn="quality, taste, and standard compliance"),
]

PRESETS = {
    "riley": ["joy", "sadness", "fear", "anger", "disgust"],   # Inside-Out emotion panel
    "default": ["skeptic", "pm", "security", "neutral"],       # role-based (best for divergence)
}


def load_personas(personas_dir: Path | None = None) -> list[Persona]:
    if personas_dir is None:
        return list(DEFAULT_PERSONAS)
    d = Path(personas_dir)
    if not d.is_dir():
        return list(DEFAULT_PERSONAS)
    try:
        import yaml  # graceful: fall back to defaults if pyyaml absent
    except ImportError:
        return list(DEFAULT_PERSONAS)
    loaded = []
    for f in sorted(d.glob("*.yaml")):
        data = yaml.safe_load(f.read_text()) or {}
        loaded.append(Persona(
            id=data.get("id", f.stem), role=data.get("role", f.stem),
            goal=data.get("goal", ""), backstory=data.get("backstory", ""),
            utility_fn=data.get("utility_fn", ""), filter=data.get("filter", {}),
            mood=data.get("mood", ""), knowledge=data.get("knowledge", []) or [],
        ))
    return loaded or list(DEFAULT_PERSONAS)


def _matches(note: Note, flt: dict) -> bool:
    tags_any = flt.get("tags_any") or []
    tags_exclude = flt.get("tags_exclude") or []
    types = flt.get("types") or []
    if any(t in note.tags for t in tags_exclude):
        return False
    if types and note.type not in types:
        return False
    if tags_any and not any(t in note.tags for t in tags_any):
        return False
    return True


def stamp(persona: Persona, notes: list[Note]) -> PerspectiveArtifact:
    matched = [n for n in notes if _matches(n, persona.filter)]
    return PerspectiveArtifact(
        persona_id=persona.id, role=persona.role,
        note_ids=[n.id for n in matched],
        highlights=[n.summary for n in matched if n.summary],
    )


def stamp_all(personas: list[Persona], notes: list[Note]) -> list[PerspectiveArtifact]:
    # Parallel isolation: each persona filters independently, no cross-visibility.
    return [stamp(p, notes) for p in personas]


# --------------------------------------------------------------- choose-your-method

def load_knowledge(persona: Persona, base_dir: Path | str = ".") -> str:
    """Read the docs a persona 'knows' into a short reference excerpt (capped)."""
    base = Path(base_dir)
    chunks = []
    for ref in persona.knowledge or []:
        for path in sorted(base.glob(ref)):
            if path.is_file():
                txt = " ".join(path.read_text(errors="replace").split())
                chunks.append(f"# {path.name}\n{txt[:600]}")
    return "\n\n".join(chunks)


def parse_critics(spec: str, personas: list[Persona]) -> list[Persona]:
    """Parse 'skeptic:grumpy,security:paranoid,qa:bad_mood' into mood-flavored critic personas.

    Unknown ids become ad-hoc generic critics so you can summon e.g. 'qa' without a file.
    """
    by_id = {p.id: p for p in list(personas) + RILEY_CHARACTERS}
    tokens: list[str] = []
    for raw in spec.split(","):
        raw = raw.strip()
        if not raw:
            continue
        head = raw.split(":", 1)[0]
        if head in PRESETS:          # a preset expands to its members (no mood suffix)
            tokens.extend(PRESETS[head])
        else:
            tokens.append(raw)
    critics: list[Persona] = []
    for token in tokens:
        pid, _, mood = token.partition(":")
        base = by_id.get(pid) or Persona(
            id=pid, role=pid.replace("_", " ").title(),
            goal=f"Critique strictly as a {pid.replace('_', ' ')}.",
            utility_fn=f"{pid.replace('_', ' ')} quality and risk",
        )
        critics.append(replace(base, mood=mood or base.mood))
    return critics


def default_critics(personas: list[Persona]) -> list[Persona]:
    """The default reflection panel: the loaded personas + a neutral evaluator."""
    crit = list(personas)
    crit.append(Persona(id="neutral", role="Neutral Evaluator",
                        goal="Judge plainly, without a persona.", utility_fn="balanced correctness"))
    return crit


def roster(personas: list[Persona]) -> str:
    """The gamified character-select screen: pick your panel of personas × moods."""
    out = ["", "╔══════════════════════════════════════════════════════════╗",
           "║  CHOOSE YOUR PANEL   —   personas × moods                 ║",
           "╚══════════════════════════════════════════════════════════╝", "", "PERSONAS"]
    for p in personas:
        mood = f"  (default mood: {p.mood})" if p.mood else ""
        out.append(f"  ▸ {p.id:<10} {p.role}{mood}")
        out.append(f"      judges by: {p.utility_fn}")
        if p.knowledge:
            out.append(f"      knows: {', '.join(p.knowledge)}")
    out += ["", "STARTER CHARACTERS  (Project Riley — named emotions)"]
    for c in RILEY_CHARACTERS:
        out.append(f"  ▸ {c.id:<10} {c.role} — {c.goal}")
    out += ["", "PRESETS"]
    for name, members in PRESETS.items():
        out.append(f"  ▸ {name:<10} {', '.join(members)}")
    out += ["", "MOODS"]
    for mid, desc in MOODS.items():
        out.append(f"  ▸ {mid:<11} {desc.split(';')[0]}")
    out += ["", "ASSEMBLE A PANEL",
            "  --critics riley                              # the Inside-Out emotion panel",
            "  --critics skeptic:grumpy,security:paranoid,qa:bad_mood   # mix roles + moods",
            "  --critics anger,fear,pm:burned_out          # emotions + a moody role", ""]
    return "\n".join(out)
