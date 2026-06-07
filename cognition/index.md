---
id: cognition
title: Catfish — Cognitive Architecture
type: moc
---

# Catfish — Cognitive Architecture

The generate→debate→evolve decision loop, distilled. Each stage has an **immutable identity** (its own `.md`, re-injected every round so it cannot drift). Edit the files to change the architecture.

## Loop

```mermaid
%%{init: {"theme": "base", "themeVariables": {"fontFamily": "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace", "fontSize": "14px", "primaryColor": "#1e293b", "primaryTextColor": "#e2e8f0", "primaryBorderColor": "#475569", "lineColor": "#64748b", "secondaryColor": "#334155", "tertiaryColor": "#0f172a", "edgeLabelBackground": "#0f172a"}, "flowchart": {"curve": "basis", "nodeSpacing": 45, "rankSpacing": 60, "padding": 8}}}%%
graph TD
  MoC([Map of Content]) --> G[Generation]
  Personas([Persona panel · moods]) --> R
  G --> R[Reflection]
  R --> K[Ranking · Bradley-Terry]
  K --> E[Evolution]
  E --> M[Meta-review]
  M -->|next-round focus| G
  M --> S[Supervisor]
  S --> C[Decision Card]
  C --> H{Human Gate}
  H -->|approved| L[Linear tree]
classDef engine fill:#155e75,stroke:#22d3ee,stroke-width:1.5px,color:#ecfeff;
classDef io fill:#334155,stroke:#64748b,stroke-width:1px,color:#e2e8f0;
classDef accent fill:#b45309,stroke:#fbbf24,stroke-width:1.5px,color:#fffbeb;
classDef gate fill:#7f1d1d,stroke:#fbbf24,stroke-width:2px,color:#fff7ed;
classDef good fill:#166534,stroke:#4ade80,stroke-width:1.5px,color:#f0fdf4;
  class MoC,Personas io
  class G,R,K,E,M,S engine
  class C accent
  class H gate
  class L good
```

## Stage identities
- [[generation]] — Produce diverse candidate plans that differ on first-principle trade-offs, not phrasing, grounded only in the provided map of content and persona context
- [[reflection]] — Adversarially critique each candidate in parallel isolation; name the single most likely-wrong load-bearing assumption or omission
- [[ranking]] — In a pairwise comparison, pick the plan that better satisfies the decision's first principles
- [[evolution]] — Synthesize genuinely new candidates from the survivors — combine two that solve different concerns, simplify an over-engineered one, or import a pattern the meta-review surfaced
- [[meta-review]] — Distill recurring concerns and structural gaps across the round's critiques and matches into a one-line focus for the next round
- [[supervisor]] — Run the loop — track active candidates, scores, and round; prune the weakest; decide terminate-or-continue; hand finalists to the decision card

_Anti-drift is markdown, not magic: the same identity file is re-read each round._
