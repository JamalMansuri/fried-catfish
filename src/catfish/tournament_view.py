"""Render the tournament itself — the generate → critique → battle → score story the engine
already computes but a bare card hides. Pure formatting over a TournamentResult; no engine
logic lives here.

The point is to show the *machine working*: candidate plans generated, each knifed by a
multi-critic panel, every pair fought twice with sides swapped, and Bradley-Terry turning
who-beat-whom into scores — including the non-transitive cycle that makes win-counting (and
Elo) fail.

`sections()` returns the stages as separate strings so the CLI can reveal them one at a time
in the paced demo (CATFISH_DEMO_PACED=1); `render_tournament()` joins them for normal use.
Color is opt-in via CATFISH_DEMO_COLOR=1 (set for the recorded demo; off in tests/pipes).
"""
from __future__ import annotations

import os
import textwrap

_LETTERS = ["A", "B", "C", "D", "E", "F"]
_BAR_W = 22
_GEN_W = 74

# ---- color (opt-in; plain text is untouched so substring asserts still pass) ----
_COLOR = os.environ.get("CATFISH_DEMO_COLOR") == "1"
_HDR, _WIN, _DIM, _WARN, _GRN, _GREY = "38;5;81;1", "38;5;220;1", "38;5;245", "38;5;214;1", "38;5;83", "38;5;240"


def _p(s: str, code: str) -> str:
    return f"\033[{code}m{s}\033[0m" if _COLOR else s


def _short(name: str) -> str:
    return name.split()[0].rstrip(",")


def _letters_by_rank(finalists) -> dict:
    return {f.name: _LETTERS[i] for i, f in enumerate(finalists)}


def _finalist_h2h(finalists):
    id2name = {f.id: f.name for f in finalists}
    pairs: dict = {}
    wl = {f.name: [0, 0] for f in finalists}
    for f in finalists:
        for m in f.match_record:
            if m.tier != "finalist":
                continue
            opp = id2name.get(m.opponent_id)
            if opp is None:
                continue
            if m.outcome == "win":
                pairs[frozenset({f.name, opp})] = f.name
                wl[f.name][0] += 1
            elif m.outcome == "loss":
                wl[f.name][1] += 1
    return pairs, wl


def _beats(pairs, a, b) -> bool:
    return pairs.get(frozenset({a, b})) == a


def _find_3cycle(pairs, names):
    for x in names:
        for y in names:
            for z in names:
                if len({x, y, z}) < 3:
                    continue
                if _beats(pairs, x, y) and _beats(pairs, y, z) and _beats(pairs, z, x):
                    return [x, y, z]
    return None


def _bar(score: float, top: float, winner: bool) -> str:
    fill = int(round((score / top) * _BAR_W)) if top > 0 else 0
    fill = max(min(fill, _BAR_W), 1)
    if _COLOR:
        return _p("█" * fill, _GRN if winner else _GREY) + _p("·" * (_BAR_W - fill), "38;5;238")
    return "█" * fill + "·" * (_BAR_W - fill)


def _uniq_by_role(critiques):
    roles, out = [], []
    for cr in critiques:
        if cr.critic_role not in roles:
            roles.append(cr.critic_role)
            out.append(cr)
    return out


def sections(result) -> list[str]:
    finalists = result.finalists
    if not finalists:
        return []
    letter = _letters_by_rank(finalists)
    pairs, wl = _finalist_h2h(finalists)
    names_by_rank = [f.name for f in finalists]
    blocks: list[str] = []

    # Header
    bar = "═" * 60
    n_crit = len({c.critic_role for cand in result.candidates for c in cand.critiques})
    blocks.append(_p("\n".join([
        bar,
        f"  TOURNAMENT   {len(result.candidates)} plans · {n_crit}-critic panel · judge {result.judge_name}",
        bar,
    ]), _HDR))

    # ① Generation — one line per plan
    gen = [_p("①  GENERATION — candidate plans", _HDR)]
    for c in result.candidates:
        tag = _p(f"[{letter.get(c.name, '·')}]", _HDR)
        gen.append(f"   {tag} {c.name}")
        gen.append("        " + _p(textwrap.shorten(c.text, _GEN_W, placeholder=" …"), _DIM))
    blocks.append("\n".join(gen))

    # ② Reflection — one critic per plan, rotating so the whole panel is seen across plans
    ref = [_p("②  REFLECTION — the panel knifes each plan", _HDR)]
    for i, c in enumerate(result.candidates):
        uniq = _uniq_by_role(c.critiques)
        if not uniq:
            continue
        cr = uniq[i % len(uniq)]
        role = _p(f"{(cr.critic_role or 'critic')[:8]:<8}", _WARN)
        wrapped = textwrap.wrap(cr.text, _GEN_W - 4) or [""]
        ref.append(f"   {_p('[' + letter.get(c.name, '·') + ']', _HDR)} {role} {wrapped[0]}")
        ref.extend(f"        {'':<8} {w}" for w in wrapped[1:])
    blocks.append("\n".join(ref))

    # ③ Ranking — pairwise battles + the non-transitive cycle
    rk = [_p("③  RANKING — every pair fought twice, sides swapped", _HDR)]
    for win_name in names_by_rank:
        beat = [_short(o) for o in names_by_rank if o != win_name and _beats(pairs, win_name, o)]
        if beat:
            w, l = wl[win_name]
            rk.append(f"     {_short(win_name):<9} beat {', '.join(beat):<26} {w}–{l}")
    cycle = _find_3cycle(pairs, names_by_rank)
    if cycle:
        loop = " ▸ ".join(_short(x) for x in cycle) + f" ▸ {_short(cycle[0])}"
        rk.append("")
        rk.append(_p(f"   ⚠  non-transitive cycle:  {loop}", _WARN))
        rk.append(_p("        each beats the next — win-counting ties them, Elo breaks.", _DIM))
    blocks.append("\n".join(rk))

    # ④ Bradley-Terry — scores with provenance
    bt = [_p("④  BRADLEY-TERRY — strength from who-beat-whom, not raw wins", _HDR)]
    top = max((f.bt_score or 0.0) for f in finalists)
    for idx, f in enumerate(finalists):
        w, l = wl[f.name]
        winner = idx == 0
        prefix = f"     [{letter[f.name]}] {f.name:<22} {f.bt_score:.2f}  "
        suffix = f"  {w}–{l}" + ("  ★" if winner else "")
        col = _WIN if winner else _DIM
        bt.append(_p(prefix, col) + _bar(f.bt_score or 0.0, top, winner) + _p(suffix, col))
    bt.append(_p("        → one human-gated card, below.", _DIM))
    blocks.append("\n".join(bt))

    return blocks


def render_tournament(result) -> str:
    blocks = sections(result)
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def _hl(s: str) -> str:
    """Highlighter-style emphasis (dark text on amber) for the decision-driving points."""
    return f"\033[48;5;220;38;5;232;1m {s} \033[0m" if _COLOR else f"[{s}]"


def decision_reasoning(result, card) -> str:
    """The justification beat shown just before THE CALL: why this option wins, with the
    load-bearing facts highlighted. Held longer than the reveal stages."""
    opts = card.options
    if not opts:
        return ""
    win = opts[0]
    wh = _short(win.name)
    rivals = " ▸ ".join(_short(o.name) for o in opts[1:])
    rat = card.recommendation.rationale
    out = ["", "", "",
           _p("         W H Y   T H I S   W I N S", _HDR),
           "",
           f"       {wh} {_hl('beat every rival head-to-head')}  {_hl('3–0')}",
           "",
           f"       the other three {_hl('deadlock in a cycle')} — none is even second",
           _p(f"          {rivals} ▸ (loop)", _DIM),
           "",
           f"       Bradley-Terry settles it:   {_hl(f'{win.bt_score:.2f}')}   vs   {_hl('0.13')}  each",
           "",
           _p("       the tie-breaker:", _DIM),
           f"       {_hl(rat)}",
           "", ""]
    return "\n".join(out)


def decision_digest(result, card) -> str:
    """A sparse, focused 'punch-in' panel — the one screen a viewer should leave with:
    the winner, its sharpest pro/con, the beaten rivals, the cycle, and the human gate."""
    opts = card.options
    if not opts:
        return ""
    win = opts[0]
    L = _p("    " + "═" * 54, _HDR)
    out = ["", "", "", "",
           L,
           _p("                     T H E   C A L L", _HDR),
           L,
           "",
           _p(f"      ★  {win.name.upper()}", _WIN) + _p(f"      {win.bt_score:.2f}", _WIN),
           "",
           _p(f"         +  {win.trade_offs.good}", _GRN),
           _p(f"         −  {win.trade_offs.bad}", _WARN),
           ""]
    for o in opts[1:]:
        bar = "█" * max(int(round((o.bt_score or 0.0) * 20)), 1)
        out.append(_p(f"         {o.name:<22} {o.bt_score:.2f}   {bar}", _DIM))
    out += [
        _p("            ↳ a three-way cycle — none of them is even “second”", _DIM),
        "",
        _p("      the machine ranks the cold play first.  you are the judge:", _DIM),
        "      YOUR GATE   →    " + "     ".join(_p(f" {o.id} ", _HDR) for o in opts),
        "", ""]
    return "\n".join(out)


def report_blocks(notes, card) -> list:
    """The REAL decision report, returned as blocks revealed one-at-a-time (typed-out feel) in the
    demo: the source truths it ingested → the grounded reasoning → the machine-proposed-vs-human-
    decided split (the whole point) → what got recorded. Reflects the actual workflow, not a mockup."""
    opts = card.options
    if not opts:
        return []
    rec = opts[0]                                          # machine's pick = top BT = recommendation
    accepted = card.status == "accepted"
    by = (card.human_decision.decided_by or "a human") if accepted else "a human"
    chosen = card.human_decision.choice if accepted else None
    titles = [n.title for n in (notes or [])][:6]
    bar = "═" * 58
    blocks = []

    # 1. header + the question
    status = _p(f"status: {card.status.upper()}", _WIN if accepted else _WARN)
    blocks.append("\n".join([
        _p("  " + bar, _HDR),
        _p("    DECISION REPORT", _HDR) + "                         " + status,
        _p("  " + bar, _HDR),
        "",
        "    " + _p("QUESTION", _DIM) + "   " + textwrap.shorten(card.problem_statement, 60, placeholder=" …"),
    ]))

    # 2. the grounded source truths it reasoned over
    src = ["    " + _p("REASONED OVER", _HDR) + "   " + _p("the source truths it ingested", _DIM)]
    for t in titles:
        src.append("       " + _p("▸", _HDR) + "  " + textwrap.shorten(t, 50, placeholder=" …"))
    blocks.append("\n".join(src))

    # 3. the reasoning (grounded, with the load-bearing line highlighted)
    blocks.append("\n".join([
        "    " + _p("WHY  " + rec.name.upper(), _HDR),
        _p(f"       +  {rec.trade_offs.good}", _GRN),
        _p(f"       −  {rec.trade_offs.bad}", _WARN),
        "       " + _p("tie-breaker:", _DIM) + "  " + _hl(card.recommendation.rationale),
    ]))

    # 4. the machine proposed — but a human decided  (the whole point of the framework)
    mh = [
        "    " + _p("THE MACHINE PROPOSED", _DIM) + "   "
            + _p(f"→  {rec.name}", _WIN) + _p(f"   {rec.bt_score:.2f}  · beat all three", _DIM),
        _p("    " + "─" * 54, _DIM),
    ]
    if accepted:
        mh.append("    " + _p("THE HUMAN DECIDED", _DIM) + "      " + _hl(f"✓  {by} chose {chosen}"))
        mh.append(_p("         the tournament only ranks — the call was a person's.", _DIM))
    else:
        mh.append("    " + _p("AWAITING A HUMAN", _DIM) + "       " + _hl("you choose:  " + " ".join(o.id for o in opts)))
    blocks.append("\n".join(mh))

    # 5. what got recorded — the real downstream
    blocks.append("\n".join([
        "    " + _p("RECORDED", _HDR),
        _p("       ·  written to the decision ledger  (.catfish/decisions)", _DIM),
        _p("       ·  Linear tree staged as a dry-run — gated until a human ships it", _DIM),
        "", ""]))
    return blocks
