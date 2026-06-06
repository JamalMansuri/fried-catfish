"""The cognitive architecture, as plain markdown.

HDE's idea — lock each agent to an immutable identity so it doesn't drift over a long chain —
done the simple way: each loop stage has an identity in `cognition/<stage>.md`, re-read and
re-injected verbatim every round (a markdown identity anchor, not a vector ID-RAG store).
`catfish architecture` distills the whole structure into its own MoC (`cognition/index.md`).

Edit the .md files to change the architecture — they are the source of truth, not these defaults.
"""
from __future__ import annotations

from pathlib import Path

# ordered loop stages + the canonical flow edges (used for the MoC graph)
STAGES = ["generation", "reflection", "ranking", "evolution", "meta-review", "supervisor"]

DEFAULT_IDENTITY = {
    "generation": "You are the Generation agent. Mandate: produce diverse candidate plans that "
                  "differ on first-principle trade-offs, grounded only in the provided context. "
                  "Invariant: never optimize for length; never restate an existing candidate.",
    "reflection": "You are the Reflection panel. Mandate: adversarially critique each candidate in "
                  "parallel isolation; name the single most likely-wrong load-bearing assumption. "
                  "Invariant: critique substance not style; no cross-talk before writing.",
    "ranking":    "You are the Ranking judge. Mandate: in a pairwise comparison, pick the plan that "
                  "better satisfies the first principles. Invariant: ignore length and position; "
                  "answer only A, B, or TIE.",
    "evolution":  "You are the Evolution agent. Mandate: synthesize genuinely NEW candidates from "
                  "the survivors. Invariant: never mutate a top-ranked candidate in place.",
    "meta-review": "You are the Meta-review agent. Mandate: distill recurring concerns and structural "
                   "gaps into a one-line focus for the next round. Invariant: prompt-only signal; "
                   "never invent consensus.",
    "supervisor": "You are the Supervisor. Mandate: run the loop, prune the weakest, decide "
                  "terminate-or-continue. Invariant: never prune below finalist_count; preserve "
                  "dead-ends in memory.",
}


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:].lstrip("\n")
    return text


def load_cognition(stage: str, cog_dir: Path | str = "cognition") -> str:
    """Return the immutable identity anchor for a stage — file body if present, else default."""
    f = Path(cog_dir) / f"{stage}.md"
    if f.is_file():
        body = _strip_frontmatter(f.read_text()).strip()
        if body:
            return body
    return DEFAULT_IDENTITY.get(stage, "")


def _one_line(text: str) -> str:
    # first sentence after the "Mandate:" marker, for the MoC summary
    seg = text.split("Mandate:", 1)[-1]
    return seg.split(".")[0].strip().capitalize()


def render_moc(cog_dir: Path | str = "cognition") -> Path:
    """Distill the cognitive architecture into its own MoC with a flow graph + identity links."""
    cog_dir = Path(cog_dir)
    cog_dir.mkdir(parents=True, exist_ok=True)
    mermaid = [
        "```mermaid", "graph TD",
        "  MoC([Map of Content]) --> G[Generation]",
        "  Personas([Persona panel · moods]) --> R",
        "  G --> R[Reflection]",
        "  R --> K[Ranking · Bradley-Terry]",
        "  K --> E[Evolution]",
        "  E --> M[Meta-review]",
        "  M -->|next-round focus| G",
        "  M --> S[Supervisor]",
        "  S --> C[Decision Card]",
        "  C --> H{Human Gate}",
        "  H -->|approved| L[Linear tree]",
        "```",
    ]
    out = ["---", "id: cognition", "title: Catfish — Cognitive Architecture", "type: moc", "---", "",
           "# Catfish — Cognitive Architecture", "",
           "The generate→debate→evolve decision loop, distilled. Each stage has an **immutable "
           "identity** (its own `.md`, re-injected every round so it cannot drift). Edit the files "
           "to change the architecture.", "",
           "## Loop", "", "\n".join(mermaid), "", "## Stage identities"]
    for stage in STAGES:
        out.append(f"- [[{stage}]] — {_one_line(load_cognition(stage, cog_dir))}")
    out += ["", "_Anti-drift is markdown, not magic: the same identity file is re-read each round._", ""]
    path = cog_dir / "index.md"
    path.write_text("\n".join(out))
    return path
