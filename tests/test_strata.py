from publishable.strata import levels_for
from publishable.units import Unit, UnitList


def _roster(*specs):
    return UnitList([Unit(key=k, paths=(), attributes=a) for k, a in specs])


def test_each_level_holds_the_units_that_carry_it():
    roster = _roster(
        ("u1", {"sex": "f"}), ("u2", {"sex": "m"}), ("u3", {"sex": "f"})
    )
    assert levels_for(roster, "sex") == {"f": {"u1", "u3"}, "m": {"u2"}}


def test_values_compare_as_strings():
    """A config's YAML gives `1` as an int while the same attribute read from a
    CSV is `"1"`. `contrasts.units_matching` coerces for this reason and so does
    this: two units whose attribute differs only in type are one level, not two,
    or a stratum silently splits in half."""
    roster = _roster(("u1", {"site": 1}), ("u2", {"site": "1"}), ("u3", {"site": 2}))
    assert levels_for(roster, "site") == {"1": {"u1", "u2"}, "2": {"u3"}}


def test_a_unit_missing_the_attribute_forms_no_level():
    """`.get` returns `None` for an attribute a unit does not carry. Coercing that
    to the string `"None"` would publish a subgroup named after a bug — the same
    trap `contrasts.resolve_contrasts` hit with a missing `id`. Such a unit is in
    no level, and so is absent from every stratum's `n`."""
    roster = _roster(("u1", {"sex": "f"}), ("u2", {}), ("u3", {"sex": None}))
    assert levels_for(roster, "sex") == {"f": {"u1"}}


def test_an_unknown_attribute_yields_no_levels():
    """Not an exception: `validate` refuses an undeclared attribute (Task 3), so
    this is unreachable from a validated config, and a pure function has no
    diagnostic to raise into."""
    roster = _roster(("u1", {"sex": "f"}))
    assert levels_for(roster, "nosuch") == {}


def test_an_empty_roster_yields_no_levels():
    assert levels_for(UnitList([]), "sex") == {}
