"""Recorded demo fixtures — "Where should we grab lunch today?"

These make `CATFISH_DEMO=1 catfish tournament examples/lunch/inbox "..."` produce a real,
stable decision card with no API key. The tournament control flow runs for real —
generation, reflection, pairwise ranking, Bradley-Terry — only the model *outputs* are
canned. The card you see is traceable to examples/lunch/inbox/.

The point of the scenario: four ordinary lunch options, and the cold tournament ranks the
local taquería highest — fresh, great value, and the one thing not already eaten this week
(the corpus carries a meal-history note the panel reaps). An everyday call you can trace
end to end; the human gate is still where you sign off.

Deliberately NOT a tidy total order. The taquería beats all three chains, and those three
form a genuine non-transitive cycle among themselves (Chipotle ▸ McDonald's ▸ Taco Bell ▸
Chipotle): win-counting calls them a three-way tie, which is exactly why scoring is
Bradley-Terry, not Elo. The BT numbers are computed by the engine from these battles — not
hand-set here.
"""

# Plan names — also the card option names. First word doubles as the battle-view handle.
TAQUERIA  = "Taquería down the block"
CHIPOTLE  = "Chipotle"
MCDONALDS = "McDonald's"
TACO_BELL = "Taco Bell"

# Four plans the table "generates". Asymmetric by design.
DEMO_CANDIDATES = [
    {"name": TAQUERIA,
     "text": "Walk two blocks to the family taquería — a fresh, made-to-order carne asada burrito, a huge portion, and nothing we've eaten all week."},
    {"name": CHIPOTLE,
     "text": "Order the usual chicken bowl — fresh, customizable, filling, and a known quantity if we beat the noon line."},
    {"name": MCDONALDS,
     "text": "Hit the drive-thru for a combo — cheapest, fastest, and back at our desks in fifteen minutes flat."},
    {"name": TACO_BELL,
     "text": "Grab the five-dollar cravings box — cheap, fast, and more filling than it has any right to be."},
]

# Pairwise winner per unordered pair. TAQUERIA beats all three; the other three form a perfect
# non-transitive cycle:  CHIPOTLE ▸ MCDONALDS,  MCDONALDS ▸ TACO_BELL,  TACO_BELL ▸ CHIPOTLE.
# Raw win counts: TAQUERIA=3, others=1 each — a three-way tie win-counting and Elo can't order.
# Bradley-Terry weighs *who* you beat, ranks TAQUERIA clearly on top, the rest equally weak.
PAIRWISE = {
    frozenset({TAQUERIA, CHIPOTLE}):  TAQUERIA,
    frozenset({TAQUERIA, MCDONALDS}): TAQUERIA,
    frozenset({TAQUERIA, TACO_BELL}): TAQUERIA,
    frozenset({CHIPOTLE, MCDONALDS}): CHIPOTLE,
    frozenset({MCDONALDS, TACO_BELL}): MCDONALDS,
    frozenset({TACO_BELL, CHIPOTLE}): TACO_BELL,
}

DEMO_META = {
    "recurring_concerns": ["chain food four of the last five days — variety has real value",
                           "cheap-and-fast optimizes for price and speed, not for how the food holds you"],
    "pattern_gaps": ["only the taquería is both fresh and something we haven't just eaten"],
    "bias_flags": [],
    "next_round_focus": "Weigh a couple of dollars and a short walk against fresh food and a break from the rotation.",
}

DEMO_CARD = {
    "problem_statement": "Four lunch spots within reach and forty minutes to eat. Where do we go — and does it matter that we keep repeating ourselves?",
    "first_principles": [
        "Most of this week was chain food; another repeat spends novelty we won't get back.",
        "Fast food's real cost is processing and sameness, not the dollar on the receipt.",
        "A short walk to fresh, made-to-order food beats a drive-thru when the time is close.",
    ],
    "trade_offs": {
        TAQUERIA: {
            "good": "Fresh, unprocessed, biggest portion per dollar — and a real break from the chains.",
            "neutral": "Cash is easier than card; a five-minute walk each way.",
            "bad": "A couple dollars more, and no app points.",
        },
        CHIPOTLE: {
            "good": "Fresh-ish, customizable, filling — a safe known quantity.",
            "neutral": "Mid-price; the line gets long right at noon.",
            "bad": "Third time this week — palate fatigue is real.",
        },
        MCDONALDS: {
            "good": "Cheapest and fastest; back at the desk quickest.",
            "neutral": "Familiar, and the app deals soften the price.",
            "bad": "Most processed; hungry again within the hour.",
        },
        TACO_BELL: {
            "good": "Most food per dollar; the value box overdelivers.",
            "neutral": "Drive-thru speed; quality varies by location.",
            "bad": "Processed, and we already had it Thursday.",
        },
    },
    "recommendation": {
        "option_name": TAQUERIA,
        "rationale": "Same money and time as a chain, but fresh, bigger, and the one thing we haven't eaten this week.",
    },
}


def rank(a_name: str, b_name: str) -> str:
    """Pairwise judgment for the fake judge: 'A' if a_name wins, 'B' if b_name wins."""
    winner = PAIRWISE.get(frozenset({a_name, b_name}))
    if winner is None:
        return "TIE"
    return "A" if winner == a_name else "B"


# Reflection: a DIFFERENT load-bearing flaw per (plan, critic) — three friends who each
# actually weighed lunch, not one template rephrased four times.
_PLAN_CRITIQUES = {
    TAQUERIA: {
        "nutritionist": "Fresh and unprocessed, but a loaded carne asada burrito is still a big calorie hit — split it or save half.",
        "budget":       "Nine dollars and cash-only; pricier than the dollar menu, and the ATM nibbles the difference.",
        "skeptic":      "The only knock is that it's unfamiliar — which is the whole point; don't talk yourself back into the chain.",
        "neutral":      "Best food, smallest real downside — the case against it is mostly inertia.",
    },
    CHIPOTLE: {
        "nutritionist": "Fresher than the drive-thrus, but the full bowl creeps past a thousand calories fast.",
        "budget":       "Eleven dollars and a fifteen-minute line — you pay in money and minutes both.",
        "skeptic":      "Third time this week. 'The usual' is just last week's decision you never re-made.",
        "neutral":      "Safe and fine, and you'll have forgotten you ate it by tomorrow.",
    },
    MCDONALDS: {
        "nutritionist": "Most processed on the list; hungry again within the hour and reaching for a snack.",
        "budget":       "Cheapest sticker price, worst food-per-dollar once you're hungry again at three.",
        "skeptic":      "Fast and cheap is solving the wrong problem if the food doesn't hold you.",
        "neutral":      "Quickest in and out; that's the entire argument for it.",
    },
    TACO_BELL: {
        "nutritionist": "Surprising value, but it's processed and the sodium does the heavy lifting.",
        "budget":       "Genuinely the most food per dollar — though 'cheap and filling' isn't the same as good.",
        "skeptic":      "You had it Thursday; twice in a week makes it the default, not a choice.",
        "neutral":      "Cheap and filling; quality is a coin-flip by location.",
    },
}


def critique(name: str, role: str) -> str:
    lenses = _PLAN_CRITIQUES.get(name, {})
    return lenses.get(role) or next(iter(lenses.values()), "No load-bearing flaw surfaced.")
