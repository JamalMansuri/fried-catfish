from catfish.tournament import bradley_terry


def test_transitive_ordering():
    items = ["A", "B", "C"]
    # A beats B, B beats C, A beats C  ("a" = first item wins) -> expect A > B > C
    matches = [("A", "B", "a"), ("B", "C", "a"), ("A", "C", "a")] * 3
    p = bradley_terry(items, matches)
    assert p["A"] > p["B"] > p["C"]


def test_undefeated_does_not_diverge():
    items = ["A", "B", "C", "D"]
    matches = [("A", x, "a") for x in ["B", "C", "D"]] * 5
    p = bradley_terry(items, matches)
    assert all(v == v and v != float("inf") for v in p.values())  # finite, no NaN/inf
    assert p["A"] > p["B"]


def test_cycle_stays_balanced():
    items = ["A", "B", "C"]
    matches = [("A", "B", "a"), ("B", "C", "a"), ("C", "A", "a")] * 4
    p = bradley_terry(items, matches)
    spread = max(p.values()) / min(p.values())
    assert spread < 1.5  # a 3-cycle should not produce a confident winner


def test_empty():
    assert bradley_terry([], []) == {}
