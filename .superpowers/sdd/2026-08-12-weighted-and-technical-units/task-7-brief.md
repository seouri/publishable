## Task 7: `weight_by`'s three checks

**Files:**
- Modify: `src/publishable/validate.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Produces: `E-DATA-WEIGHT-UNKNOWN` (row 291), `E-DATA-WEIGHT-INVALID` (row 292), `W-DATA-WEIGHT-UNDECLARED` (row 293)

The three rows, verbatim: *"Weight attribute exists — `data.units.weight_by` names `sampling_weight`, which is not a unit attribute."* *"Weights are usable — `sampling_weight` holds a zero or negative value for 3 units; a weight is what a unit stands for."* *"Weighting looks undeclared — `sampling_weight` varies across units and looks like an inverse sampling probability, but `weight_by` is unset (warning)."*

The third fires when `weight_by` is **unset**, so it must not depend on the declaration it is about. Choose its heuristic and **state it in the row you write** — a warning whose trigger is unstated is one a user cannot act on. Recommended: a numeric attribute named `*weight*` or `*_prob*`, all values positive, and more than one distinct value.

- [ ] **Step 1: Write the failing tests** — one per identifier, plus:

```python
def test_an_empty_weight_by_is_a_finding_not_a_default(write_config):
    """Decision 3, the second truthiness hole."""
    path = write_config({"data": {"units": {
        "from": "index.csv", "key": "patient_id", "weight_by": "",
    }}})
    assert "E-DATA-WEIGHT-UNKNOWN" in codes(path)


def test_no_weight_warning_for_a_constant_column(write_config):
    """A column that does not vary is not a sampling weight, and warning about it
    would train a reader to ignore the warning."""
    ...
    assert "W-DATA-WEIGHT-UNDECLARED" not in codes(path)
```

- [ ] **Step 2: Run and confirm each fails.**

- [ ] **Step 3: Implement `_check_weight_by`**

```python
_WEIGHT_HINTS = ("weight", "_prob", "probability")


def _check_weight_by(units: dict[str, Any], roster: UnitList | None, c: Collector) -> None:
    """`data.units.weight_by` — the attribute exists, its values are usable, and
    a column that looks like a weight is not silently going unused.

    The name check runs without a roster; the value checks need one. Skipping the
    value half when the roster does not resolve is not the silent skip H1 removed:
    the name half still reports, and a test pins that.
    """
    declared = units.get("weight_by")
    if declared is not None and not declared:
        c.error(
            "E-DATA-WEIGHT-UNKNOWN",
            "data.units.weight_by",
            "is empty; it names the unit attribute holding the weight, and an empty "
            "declaration changes no behavior",
        )
        return
    names = sorted({n for u in roster for n in u.attributes}) if roster is not None else []
    if declared:
        if roster is not None and declared not in names:
            c.error(
                "E-DATA-WEIGHT-UNKNOWN",
                "data.units.weight_by",
                f"names {declared!r}, which is not a unit attribute. Declared "
                f"attributes are {', '.join(names) or 'none'}",
            )
            return
        if roster is None:
            return
        bad = [u.key for u in roster
               if not isinstance(u.attributes.get(declared), (int, float))
               or u.attributes[declared] <= 0]
        if bad:
            c.error(
                "E-DATA-WEIGHT-INVALID",
                "data.units.weight_by",
                f"holds a zero, negative or non-numeric value for {len(bad)} unit(s) "
                f"(first: {bad[0]!r}); a weight is what a unit stands for, so it has "
                "to be a positive number",
            )
        return
    if roster is None:
        return
    for name in names:
        if not any(hint in name.lower() for hint in _WEIGHT_HINTS):
            continue
        values = [u.attributes.get(name) for u in roster]
        if not all(isinstance(v, (int, float)) and v > 0 for v in values):
            continue
        if len({float(v) for v in values}) < 2:
            continue  # a column that does not vary is not a sampling weight
        c.warn(
            "W-DATA-WEIGHT-UNDECLARED",
            f"data.units.attributes.{name}",
            f"{name!r} is numeric, positive and varies across units, so it looks like "
            "an inverse sampling probability — but `data.units.weight_by` is unset, so "
            "it is reported and never weighted with. Set `weight_by` if it is one, or "
            "rename it if it is not",
        )
        return
```

**Write the heuristic into the `W-` row you add in step 6**, in these terms: a numeric attribute whose name contains `weight`, `_prob` or `probability`, all of whose values are positive and not all equal. A warning whose trigger is unstated is one a user cannot act on.

- [ ] **Step 4: Run and confirm they pass.**

- [ ] **Step 5: Mutation-test each of the three separately.** A single mutation that kills all three is not three tests.

- [ ] **Step 6: Registry rows and commit.** Two `E-` rows (67 → 69) and one `W-` row (18 → 19).

```bash
git commit -am "feat: check that a weight exists, is usable, and is not silently absent"
```

---

