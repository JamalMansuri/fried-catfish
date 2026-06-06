"""Recorded demo fixtures — "Muad'Dib's choice: unleash the jihad?"

These make `CATFISH_DEMO=1 catfish tournament examples/inbox "..."` produce a real, stable
decision card with no API key. The tournament control flow runs for real — generation,
reflection, pairwise ranking, Bradley-Terry — only the model *outputs* are canned. The card
you see is traceable to examples/inbox/.

The point of the scenario: the cold tournament ranks "Unleash the jihad" highest on raw
strategic merit — and the human gate is where you must decide whether to sign off on sixty-one
billion dead. Catfish scores the options; you are the judge of record.

Deliberately NOT a tidy total order. "Unleash" beats all three alternatives, and those three
form a genuine non-transitive cycle among themselves (Restrain ▸ Abdicate ▸ Channel ▸ Restrain):
win-counting calls them a three-way tie, which is exactly why scoring is Bradley-Terry, not Elo.
The BT numbers are computed by the engine from these battles — not hand-set here.
"""

# Plan names — also the card option names. First word doubles as the battle-view handle.
UNLEASH  = "Unleash the jihad"
RESTRAIN = "Restrain the legions"
ABDICATE = "Abdicate the throne"
CHANNEL  = "Channel the fervor"

# Four plans the war council "generates". Asymmetric by design.
DEMO_CANDIDATES = [
    {"name": UNLEASH,
     "text": "Ride the holy war. Loose the Fremen legions in your name, sweep the Great Houses, and take the throne and the whole Imperium."},
    {"name": RESTRAIN,
     "text": "Hold the legions back. Rule Arrakis through the spice monopoly and threat alone, and refuse to let the jihad leave the planet."},
    {"name": ABDICATE,
     "text": "Refuse the mantle. Walk away from the throne and the prophecy, and deny the holy war the messiah it needs."},
    {"name": CHANNEL,
     "text": "Turn the fervor inward — spend the Fremen's faith on Liet-Kynes' dream, greening Arrakis instead of burning the Imperium."},
]

# Pairwise winner per unordered pair. UNLEASH beats all three; the other three form a perfect
# non-transitive cycle:  RESTRAIN ▸ ABDICATE,  ABDICATE ▸ CHANNEL,  CHANNEL ▸ RESTRAIN.
# Raw win counts: UNLEASH=3, others=1 each — a three-way tie win-counting and Elo can't order.
# Bradley-Terry weighs *who* you beat, ranks UNLEASH clearly on top, the rest equally weak.
PAIRWISE = {
    frozenset({UNLEASH, RESTRAIN}): UNLEASH,
    frozenset({UNLEASH, ABDICATE}): UNLEASH,
    frozenset({UNLEASH, CHANNEL}):  UNLEASH,
    frozenset({RESTRAIN, ABDICATE}): RESTRAIN,
    frozenset({ABDICATE, CHANNEL}):  ABDICATE,
    frozenset({CHANNEL, RESTRAIN}):  CHANNEL,
}

DEMO_META = {
    "recurring_concerns": ["the jihad spreads from Arrakis whether or not you lead it",
                           "no plan un-makes the messiah the Fremen already believe in"],
    "pattern_gaps": ["only unleashing it puts you at the head of the war instead of under it"],
    "bias_flags": [],
    "next_round_focus": "Weigh total power against sixty-one billion dead — and whether refusing even stops it.",
}

DEMO_CARD = {
    "problem_statement": "The Fremen await one word to loose a holy war across the Imperium in your name. Prescience shows it kills billions. Do you unleash it?",
    "first_principles": [
        "The Fremen already believe you are the Mahdi; the fervor exists whether you lead it or not.",
        "Prescience shows the jihad spreading from Arrakis on every path — the question is whether you steer it.",
        "Total power and its cost arrive together; one cannot be taken without the other.",
    ],
    "trade_offs": {
        UNLEASH: {
            "good": "Total power — the legions sweep every Great House before them.",
            "neutral": "You become the messiah they already believe you are.",
            "bad": "Sixty-one billion dead across the Imperium, and it can't be recalled.",
        },
        RESTRAIN: {
            "good": "Keeps your hands clean of the jihad's blood.",
            "neutral": "Rules by the spice and the threat, not the sword.",
            "bad": "Prescience says the fervor breaks the leash and burns anyway.",
        },
        ABDICATE: {
            "good": "Refuses to be the banner a holy war marches under.",
            "neutral": "Hands Arrakis and the spice to whoever takes them.",
            "bad": "The legend outlives you; they crown a martyr and march regardless.",
        },
        CHANNEL: {
            "good": "Spends the faith on a green Arrakis, not a burning Imperium.",
            "neutral": "Slow — terraforming is a multi-generation dream.",
            "bad": "A faith built for conquest may not settle for gardening.",
        },
    },
    "recommendation": {
        "option_name": UNLEASH,
        "rationale": "Every other path still ends in the jihad — only this one puts you at its head.",
    },
}


def rank(a_name: str, b_name: str) -> str:
    """Pairwise judgment for the fake judge: 'A' if a_name wins, 'B' if b_name wins."""
    winner = PAIRWISE.get(frozenset({a_name, b_name}))
    if winner is None:
        return "TIE"
    return "A" if winner == a_name else "B"


# Reflection: a DIFFERENT load-bearing flaw per (plan, critic) — five advisors who actually
# weighed the war, not one template rephrased four times.
_PLAN_CRITIQUES = {
    UNLEASH: {
        "skeptic":  "Assumes you can ride a holy war you've already watched consume sixty billion — no one rides the storm.",
        "pm":       "Once loosed, the legions answer to the myth, not to you.",
        "security": "Total exposure: every Great House, the Guild, and the Bene Gesserit unite against the Mahdi.",
        "qa":       "There is no rollback on a jihad — it cannot be stopped once it starts.",
        "neutral":  "Wins the throne and loses the question of whether you should.",
    },
    RESTRAIN: {
        "skeptic":  "Assumes faith obeys a leash; the Fremen's does not.",
        "pm":       "Holding the legions back spends the one force that makes you untouchable.",
        "security": "A throttled jihad leaves every enemy alive to move against you.",
        "qa":       "Untested — no one has ever bottled a messiah's war.",
        "neutral":  "Buys time the prescience says you don't have.",
    },
    ABDICATE: {
        "skeptic":  "Walking away doesn't unmake the legend — they'll march for your ghost.",
        "pm":       "Hands the spice, the throne, and the fervor to someone worse.",
        "security": "Leaves Arrakis to the Harkonnens' return the moment you step aside.",
        "qa":       "No test that the jihad needs you alive — martyrs serve it better.",
        "neutral":  "Clean hands, and the war comes anyway.",
    },
    CHANNEL: {
        "skeptic":  "Assumes a faith forged for conquest will settle for terraforming.",
        "pm":       "Greening Arrakis is generations of work the Imperium won't grant you.",
        "security": "Turns your back on armed enemies to plant grass.",
        "qa":       "Untested whether fervor redirects or just reroutes to the nearest war.",
        "neutral":  "The noblest plan, and the one the desert is least built for.",
    },
}


def critique(name: str, role: str) -> str:
    lenses = _PLAN_CRITIQUES.get(name, {})
    return lenses.get(role) or next(iter(lenses.values()), "No load-bearing flaw surfaced.")
