"""Recorded demo fixtures — incident case 01, "checkout p99 is 5× and the database is pegged."

These make `CATFISH_DEMO=1 catfish tournament examples/incidents/cases/01-checkout-latency/inbox
"..."` produce a real, stable decision card with no API key. The tournament control flow runs for
real — generation, reflection, pairwise ranking, Bradley-Terry — only the model *outputs* are
canned. The card you see is traceable to examples/incidents/cases/01-checkout-latency/inbox/.

The point of the scenario: every metric on the dashboard screams "the database is too small," but
the timeline says the p99 spike began twelve minutes after deploy 4821 shipped an N+1 query. The
cold tournament ranks the rollback highest — the one option that undoes the change the timeline
actually implicates — over the louder "scale the box" reflex. An on-call call you can trace end to
end; the human gate is still where you sign off.

This is the single canned scenario (case 01). The full six-case backtest needs a live judge —
see examples/incidents/backtest.py — because a backtest is only honest if the panel never sees the
answer key, and the offline replay only knows this one case.

Deliberately NOT a tidy total order. The rollback beats all three reflex fixes, and those three
form a genuine non-transitive cycle among themselves (Scale ▸ Index ▸ Cache ▸ Scale): win-counting
calls them a three-way tie, which is exactly why scoring is Bradley-Terry, not Elo. The BT numbers
are computed by the engine from these battles — not hand-set here.
"""

# Plan names — also the card option names. First word doubles as the battle-view handle.
ROLLBACK  = "Roll back deploy 4821"
SCALE_DB  = "Scale up the database"
ADD_INDEX = "Add a composite index"
CACHE     = "Cache the order-summary response"

# Four plans the table "generates". Asymmetric by design.
DEMO_CANDIDATES = [
    {"name": ROLLBACK,
     "text": "Revert deploy 4821 and redeploy the previous build — undo the change that landed twelve minutes before the spike. Fast and fully reversible."},
    {"name": SCALE_DB,
     "text": "Fail over to a larger primary and add read replicas so the pegged database has CPU headroom to absorb the load."},
    {"name": ADD_INDEX,
     "text": "Add a composite index on the order-summary query so each call is cheaper and pressure comes off the database CPU."},
    {"name": CACHE,
     "text": "Put a short-TTL cache in front of the order-summary endpoint so repeated reads skip the database entirely."},
]

# Pairwise winner per unordered pair. ROLLBACK beats all three; the other three form a perfect
# non-transitive cycle:  SCALE_DB ▸ ADD_INDEX,  ADD_INDEX ▸ CACHE,  CACHE ▸ SCALE_DB.
# Raw win counts: ROLLBACK=3, others=1 each — a three-way tie win-counting and Elo can't order.
# Bradley-Terry weighs *who* you beat, ranks ROLLBACK clearly on top, the rest equally weak.
PAIRWISE = {
    frozenset({ROLLBACK, SCALE_DB}):  ROLLBACK,
    frozenset({ROLLBACK, ADD_INDEX}): ROLLBACK,
    frozenset({ROLLBACK, CACHE}):     ROLLBACK,
    frozenset({SCALE_DB, ADD_INDEX}): SCALE_DB,
    frozenset({ADD_INDEX, CACHE}):    ADD_INDEX,
    frozenset({CACHE, SCALE_DB}):     CACHE,
}

DEMO_META = {
    "recurring_concerns": ["the loudest metric (CPU) is downstream of the query count, not the root cause",
                           "scaling buys time but leaves the N+1 to peg the bigger box within the hour"],
    "pattern_gaps": ["only the rollback undoes the change the timeline actually implicates"],
    "bias_flags": [],
    "next_round_focus": "Weigh a four-minute reversible rollback against an hour of scaling that never touches the N+1.",
}

DEMO_CARD = {
    "problem_statement": "Checkout p99 is 5× normal and the database is pegged. Do we feed the box more resources, or is the spike a deploy we can undo?",
    "first_principles": [
        "Latency was flat until twelve minutes after deploy 4821; the timeline names a suspect the CPU graph hides.",
        "Pegged CPU is downstream of an N+1 query explosion — a symptom of the change, not the cause.",
        "The reversible fix wins under pressure: a rollback costs four minutes; scaling the database costs an hour.",
    ],
    "trade_offs": {
        ROLLBACK: {
            "good": "Undoes the exact change in the window; reversible in one command, p99 recovers in minutes.",
            "neutral": "Reverts everyone's 4821 work until it can reland behind the N+1 fix.",
            "bad": "Wrong if the spike isn't 4821 — but the timeline makes that unlikely.",
        },
        SCALE_DB: {
            "good": "Adds real CPU headroom; the standard play when a database is genuinely saturated.",
            "neutral": "No code change and no revert; buys time while the cause is found.",
            "bad": "Treats a symptom: the N+1 pegs the bigger box too, an hour later.",
        },
        ADD_INDEX: {
            "good": "Cuts per-query cost without reverting the deploy; helps if the query is the floor.",
            "neutral": "Needs the right columns; the index build adds load while it runs.",
            "bad": "An N+1 is many cheap queries, not one slow one — an index barely helps.",
        },
        CACHE: {
            "good": "Skips the database on repeat reads; fewer queries, less CPU, the deploy stays.",
            "neutral": "Adds a cache layer and a TTL to reason about.",
            "bad": "Masks the N+1 and adds staleness; the next uncached path pegs CPU again.",
        },
    },
    "recommendation": {
        "option_name": ROLLBACK,
        "rationale": "Same minutes as any mitigation, but it undoes the actual change and is the only fully reversible move under fire.",
    },
}


def rank(a_name: str, b_name: str) -> str:
    """Pairwise judgment for the fake judge: 'A' if a_name wins, 'B' if b_name wins."""
    winner = PAIRWISE.get(frozenset({a_name, b_name}))
    if winner is None:
        return "TIE"
    return "A" if winner == a_name else "B"


# Reflection: a DIFFERENT load-bearing flaw per (plan, critic) — three on-call engineers who each
# actually weighed the incident, not one template rephrased four times.
_PLAN_CRITIQUES = {
    ROLLBACK: {
        "sre":      "Smallest blast radius and reversible in one command — the safe move while we confirm the N+1.",
        "forensic": "Lines up with the timeline: flat until 14:15, deploy at 14:03, the spike at 4821's N+1.",
        "skeptic":  "The only real risk is that 4821 is innocent — but nothing else changed in the window.",
        "neutral":  "Cheapest reversible test of the most likely cause; little downside if it's wrong.",
    },
    SCALE_DB: {
        "sre":      "Failover and replicas are a big, slow change under fire — high blast radius for a symptom.",
        "forensic": "CPU is pegged because the query count exploded; more CPU doesn't undo the N+1.",
        "skeptic":  "This is the dashboard talking. 'CPU is high' isn't 'the box is too small.'",
        "neutral":  "Standard saturation play, wrong incident — the load is self-inflicted by the deploy.",
    },
    ADD_INDEX: {
        "sre":      "A schema change mid-incident is risky, and the index build itself adds load.",
        "forensic": "An N+1 is many small queries; indexing one of them barely moves p99.",
        "skeptic":  "Plausible-sounding, but it optimizes the wrong shape of the problem.",
        "neutral":  "Might help a little; it doesn't address why the query count jumped.",
    },
    CACHE: {
        "sre":      "A new cache layer under pressure adds a failure mode instead of removing one.",
        "forensic": "Hides the N+1 behind cache hits; the first miss pegs CPU again.",
        "skeptic":  "Caching to avoid fixing the regression is treating the alarm, not the fire.",
        "neutral":  "Cuts load on repeat reads, but adds staleness and doesn't fix the cause.",
    },
}


def critique(name: str, role: str) -> str:
    lenses = _PLAN_CRITIQUES.get(name, {})
    return lenses.get(role) or next(iter(lenses.values()), "No load-bearing flaw surfaced.")
