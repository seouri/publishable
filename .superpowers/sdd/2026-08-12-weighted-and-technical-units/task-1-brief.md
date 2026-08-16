## Task 1: The collapse function

**Files:**
- Modify: `src/publishable/units.py`
- Test: `tests/test_units.py`

**Interfaces:**
- Consumes: `Unit` (frozen, hashable by `key`, with `.attributes`), `UnitList`
- Produces: `collapse_measurements(units, by, collapse) -> tuple[list[Unit], list[int]]` — the collapsed units in first-seen order, and the per-unit measurement counts in the same order. Tasks 3 and 5 both call it. `COLLAPSE_RULES = ("mean", "first", "mode")`.

`collapse` is either one rule applied to every column, or a mapping of column name to rule. A column absent from the mapping falls back to `first`, because a column the config did not name is one the design did not ask to average.

- [ ] **Step 1: Write the failing test**

```python
def test_rows_sharing_a_key_collapse_to_one_unit():
    units = [
        Unit(key="p1", paths=(), attributes={"read_id": "r1", "depth": 10, "site": "A"}),
        Unit(key="p1", paths=(), attributes={"read_id": "r2", "depth": 20, "site": "A"}),
        Unit(key="p2", paths=(), attributes={"read_id": "r3", "depth": 30, "site": "B"}),
    ]
    collapsed, counts = collapse_measurements(units, by="read_id", collapse="mean")
    assert [u.key for u in collapsed] == ["p1", "p2"]
    assert counts == [2, 1]
    assert collapsed[0].depth == 15.0        # mean of 10 and 20
    assert collapsed[0].site == "A"          # non-numeric, constant: carried
    assert "read_id" not in collapsed[0].attributes   # the measurement axis is consumed
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `uv run pytest tests/test_units.py::test_rows_sharing_a_key_collapse_to_one_unit -v`
Expected: FAIL, `ImportError` / `NameError` on `collapse_measurements`.

- [ ] **Step 3: Implement**

```python
COLLAPSE_RULES = ("mean", "first", "mode")


def _rule_for(column: str, collapse: Any) -> str:
    """One rule for every column, or a per-column map falling back to `first`.

    A column the config did not name is one the design did not ask to average,
    so the fallback carries the first value rather than guessing at a statistic.
    """
    if isinstance(collapse, Mapping):
        return str(collapse.get(column, "first"))
    return str(collapse)


def _apply(rule: str, values: list[Any]) -> Any:
    if rule == "first":
        return values[0]
    if rule == "mode":
        return Counter(values).most_common(1)[0][0]
    if rule == "mean":
        return sum(values) / len(values)
    raise ContractError(
        f"`data.units.measurements.collapse` names {rule!r}; expected one of "
        f"{', '.join(COLLAPSE_RULES)}",
        code="E-UNITS-COLLAPSE-RULE",
    )


def collapse_measurements(
    units: list[Unit], by: str, collapse: Any
) -> tuple[list[Unit], list[int]]:
    """Collapse rows sharing a `key` into one unit, in first-seen order.

    `reference.md` § What isn't a repeat: rows sharing a key are technical
    replicates, collapsed at resolution, before any step sees them — which is
    what keeps them out of `n`. The measurement axis `by` is consumed: it
    distinguished the rows and has no value once they are one unit.

    Returns the collapsed units and their measurement counts in the same order,
    because `technical_n` is `{min, max, median}` over exactly these counts and
    recomputing them from a second walk is how the two come to disagree.
    """
    groups: dict[str, list[Unit]] = {}
    for unit in units:
        groups.setdefault(unit.key, []).append(unit)
    collapsed: list[Unit] = []
    counts: list[int] = []
    for key, members in groups.items():
        names: list[str] = []
        for member in members:
            for name in member.attributes:
                if name != by and name not in names:
                    names.append(name)
        merged = {
            name: _apply(
                _rule_for(name, collapse),
                [m.attributes[name] for m in members if name in m.attributes],
            )
            for name in names
        }
        paths = tuple(p for m in members for p in m.paths)
        collapsed.append(Unit(key=key, paths=paths, attributes=merged))
        counts.append(len(members))
    return collapsed, counts
```

Add `from collections import Counter` and `from collections.abc import Mapping` to the imports if absent.

- [ ] **Step 4: Run the test and confirm it passes**

Run: `uv run pytest tests/test_units.py -v`

- [ ] **Step 5: Mutation-test**

Change `return values[0]` in the `first` branch to `return values[-1]`. Run the test — it must FAIL on `collapsed[0].site`. Revert, delete `__pycache__`, confirm it passes by behaviour.

Then a second mutation that matters more: make `counts` be recomputed as `[len(groups[u.key]) for u in collapsed]` in a separate walk instead of accumulated in the loop. This must NOT change behaviour today — note in your report that it does not, and that the docstring's reason is about future drift rather than a current bug, so the claim is honest.

- [ ] **Step 6: Commit**

```bash
git add src/publishable/units.py tests/test_units.py
git commit -m "feat: collapse rows sharing a key into one unit"
```

---

