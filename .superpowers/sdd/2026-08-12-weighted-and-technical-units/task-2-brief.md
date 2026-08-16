## Task 2: Row 243 — the collapse rule fits the column

**Files:**
- Modify: `src/publishable/validate.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: task 1's `COLLAPSE_RULES`; `validate`'s existing roster resolution, which returns `None` when `input_dir` is unreadable or the roster cannot resolve
- Produces: `E-DATA-MEASUREMENTS-INVALID` (shape) and `E-DATA-MEASUREMENTS-COLLAPSE-TYPE` (row 243)

**Do not remove `E-DATA-MEASUREMENTS-UNSUPPORTED` in this task** — task 6 retires it, after both paths execute. A check that fires only behind a refusal is dead code, so write the tests to call the check directly as well as through `validate_config`.

`reference.md` § Validation row 243 is: *"Collapse rule fits the column — `measurements.collapse: mean` over `site`, which is a string — use `first` or `mode`, or a per-column map."* The type comes from the **resolved roster's actual attribute values**, which `validate` already resolves against a real table. When the roster does not resolve, the check is skipped — and that skip must be *reachable in a test with the roster resolvable*, so it does not become the silent-skip class.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_mean_collapse_over_a_string_column_is_refused(write_config):
    """Row 243. `mean` over `site` has no meaning; the row names the remedies."""
    path = write_config({"data": {"units": {
        "from": "index.csv", "key": "patient_id",
        "attributes": ["site", "read_id"],
        "measurements": {"by": "read_id", "collapse": "mean"},
    }}})
    assert "E-DATA-MEASUREMENTS-COLLAPSE-TYPE" in codes(path)


def test_a_per_column_map_sparing_the_string_column_is_accepted(write_config):
    """The remedy the row names must actually work, or the check is a trap."""
    path = write_config({"data": {"units": {
        "from": "index.csv", "key": "patient_id",
        "attributes": ["site", "depth", "read_id"],
        "measurements": {"by": "read_id", "collapse": {"depth": "mean", "site": "first"}},
    }}})
    assert "E-DATA-MEASUREMENTS-COLLAPSE-TYPE" not in codes(path)


def test_measurements_missing_by_is_refused(write_config):
    path = write_config({"data": {"units": {
        "from": "index.csv", "key": "patient_id",
        "measurements": {"collapse": "mean"},
    }}})
    assert "E-DATA-MEASUREMENTS-INVALID" in codes(path)


def test_an_empty_measurements_block_is_a_finding_not_a_default(write_config):
    """Decision 3. The truthiness gate that lets `{}` through today is a hole:
    un-refusing a declaration must not turn its empty form into a working default."""
    path = write_config({"data": {"units": {
        "from": "index.csv", "key": "patient_id", "measurements": {},
    }}})
    assert "E-DATA-MEASUREMENTS-INVALID" in codes(path)
```

- [ ] **Step 2: Run them and confirm each fails**

Run: `uv run pytest tests/test_validate.py -k measurements -v`
Expected: all four FAIL. **Read the failure text** — a test failing because `E-DATA-MEASUREMENTS-UNSUPPORTED` fired instead is failing for the wrong reason and tells you nothing yet.

- [ ] **Step 3: Implement `_check_measurements`**

**Import `COLLAPSE_RULES` and `NUMERIC_COLLAPSE_RULES` from `units.py`** — task 1 exports both. Do not restate either set here; two lists of what `mean` may be applied to is how the check and the collapse come to disagree.

```python
def _check_measurements(units: dict[str, Any], roster: UnitList | None, c: Collector) -> None:
    """`data.units.measurements` — shape, then the collapse rule against the column.

    The type comes from the resolved roster's own attribute values rather than
    from a declaration, because `attributes` declares names and not types.
    When the roster does not resolve, the type half is skipped and the shape
    half still runs: a config can be wrong about its shape without a directory.
    """
    decl = units.get("measurements")
    if decl is None:
        return
    if not isinstance(decl, dict) or not decl:
        c.error(
            "E-DATA-MEASUREMENTS-INVALID",
            "data.units.measurements",
            "is empty or is not a mapping; it needs `by` (the attribute distinguishing "
            "one measurement of a unit from another) and `collapse` (how rows sharing a "
            "key become one). An empty declaration changes no behavior, which is the "
            "failure the refusal it replaces existed to prevent",
        )
        return
    by = decl.get("by")
    if not isinstance(by, str) or not by:
        c.error(
            "E-DATA-MEASUREMENTS-INVALID",
            "data.units.measurements.by",
            "is missing or is not an attribute name; without it nothing distinguishes "
            "a second measurement of one unit from a resumed retry of the same one, "
            "and the two collapse in opposite directions",
        )
    collapse = decl.get("collapse")
    rules = collapse.values() if isinstance(collapse, dict) else [collapse]
    for rule in rules:
        if rule not in COLLAPSE_RULES:
            c.error(
                "E-DATA-MEASUREMENTS-INVALID",
                "data.units.measurements.collapse",
                f"names {rule!r}; expected one of {', '.join(COLLAPSE_RULES)}, or a "
                "mapping of column name to one of them",
            )
            return
    if roster is None:
        return
    for name in sorted({n for u in roster for n in u.attributes} - {by}):
        rule = collapse.get(name, "first") if isinstance(collapse, dict) else collapse
        if rule not in NUMERIC_COLLAPSE_RULES:
            continue
        offenders = [
            u.attributes[name]
            for u in roster
            if name in u.attributes and not isinstance(u.attributes[name], (int, float))
        ]
        if offenders:
            c.error(
                "E-DATA-MEASUREMENTS-COLLAPSE-TYPE",
                f"data.units.measurements.collapse.{name}",
                f"is {rule!r} over {name!r}, which holds {offenders[0]!r} — a "
                f"{type(offenders[0]).__name__}. Use `first` or `mode` for it, or a "
                "per-column map giving each column the rule that fits it",
            )
```

Call it from `_check_data`'s existing roster-resolving path, where the roster is already in hand.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `uv run pytest tests/test_validate.py -k measurements -v`

- [ ] **Step 5: Mutation-test**

Change `if rule not in NUMERIC_COLLAPSE_RULES: continue` to `if rule in NUMERIC_COLLAPSE_RULES: continue`. `test_a_mean_collapse_over_a_string_column_is_refused` must FAIL. Revert, delete `__pycache__`, verify by behaviour.

Then check the skip is not silent: temporarily make the roster unresolvable in the first test and confirm the *shape* findings still fire. Revert.

- [ ] **Step 6: Add the two registry rows and commit**

Both go in `reference.md` § Validation's `### Errors validate reports` table, in alphabetical position. Row count 65 → 67. Write each row's condition from the emit site, not from this plan.

```bash
git add src/publishable/validate.py tests/test_validate.py docs/reference.md
git commit -m "feat: check the collapse rule against the column it collapses"
```

---

