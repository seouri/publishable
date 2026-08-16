### Task 2: `within` matching over the roster

**Files:**
- Modify: `src/publishable/contrasts.py`
- Test: `tests/test_contrasts.py`

**Interfaces:**
- Consumes: `units.Unit` — frozen, with `key`, `paths`, `attributes`. `UnitList` supports iteration, `len`, integer indexing, and `.train`.
- Produces: `units_matching(roster: "UnitList", within: dict[str, str] | None) -> set[str] | None`

`None` in, `None` out — meaning "no restriction", which is different from "no units matched". Downstream code must be able to tell those apart, because an empty stratum is a real condition worth reporting and an unrestricted contrast is not.

**`within` matches unit *attributes*, not recorded columns.** `docs/reference.md` § Contrasts: it "names unit attributes and their levels — the same attributes `report_by` resolves — and the contrast is computed over units matching **all** of them."

- [ ] **Step 1: Write the failing tests**

```python
def _roster(*specs):
    return UnitList([Unit(key=k, paths=(), attributes=a) for k, a in specs])


def test_no_within_means_no_restriction():
    r = _roster(("u1", {"sex": "f"}), ("u2", {"sex": "m"}))
    assert units_matching(r, None) is None


def test_a_single_level_selects_matching_units():
    r = _roster(("u1", {"sex": "f"}), ("u2", {"sex": "m"}), ("u3", {"sex": "f"}))
    assert units_matching(r, {"sex": "f"}) == {"u1", "u3"}


def test_multiple_levels_are_conjunctive():
    r = _roster(("u1", {"sex": "f", "site": "a"}), ("u2", {"sex": "f", "site": "b"}))
    assert units_matching(r, {"sex": "f", "site": "a"}) == {"u1"}


def test_an_empty_stratum_is_an_empty_set_not_none():
    """Empty means nobody matched; None means nobody asked. Downstream reports
    those differently, so they must not collapse."""
    r = _roster(("u1", {"sex": "f"}))
    assert units_matching(r, {"sex": "m"}) == set()


def test_values_compare_as_strings():
    """A config's YAML gives `1` as an int while an attribute read from a CSV is
    `"1"`; comparing them raw would silently match nothing."""
    r = _roster(("u1", {"cohort": "1"}))
    assert units_matching(r, {"cohort": 1}) == {"u1"}
```

- [ ] **Step 2: Run to verify they fail, then implement**

```python
def units_matching(roster: "UnitList", within: dict[str, str] | None) -> set[str] | None:
    """Unit keys matching every level in `within`, or `None` when unrestricted.

    `None` and `set()` are different answers: nobody asked, versus nobody
    matched. An empty stratum is a real finding — `limits.min_reported_n` exists
    to warn about small ones — so collapsing the two would hide it.

    Values compare as strings: a config's YAML gives `1` as an int while the same
    attribute read from a table is `"1"`, and comparing them raw matches nothing.
    """
    if within is None:
        return None
    return {
        unit.key
        for unit in roster
        if all(str(unit.attributes.get(k)) == str(v) for k, v in within.items())
    }
```

- [ ] **Step 3: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/contrasts.py tests/test_contrasts.py
git commit -m "Select the units a within stratum names"
```

---

