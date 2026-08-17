## Task 28: `E-RESOLVER-MEASUREMENT-FIELD` emitted, marker struck

**Files:** Modify `src/publishable/validate.py`, `docs/reference.md`, `tests/test_validate.py`.

**Interfaces:**
- Consumes: `validate._check_measurements(units: dict, roster: UnitList | None, technical_n: dict[str, float] | None, columns: frozenset[str], c: Collector) -> None`
  — read its signature and body in `src/publishable/validate.py`; it is already imported by name in
  `tests/test_validate.py` for direct calls. Its existing `by`-against-`columns` check reports
  `E-UNITS-ATTR-MISSING` and is gated on `technical_n["max"] > 1`.
- Produces: a source-aware branch reporting `E-RESOLVER-MEASUREMENT-FIELD` when the source is a
  resolver; § Errors' `Not yet emitted:` clause for that code struck.

**Ungated for a resolver, and gated for a table — a decision, not an inheritance.** The table
path's `max > 1` gate exists because `measurements.by` means two different things on the two paths:
against a table with real columns, a `by` may name a measurement identity the **step** invents
through `io.record(..., measurement=)`, and refusing it would refuse a design § What isn't a repeat
documents. A resolver has no columns at all, and § Where units come from turns that into an explicit
obligation — *"yield one `Unit` per measurement, sharing a `key`, and emit `measurements.by` as an
attribute — a resolver has no columns beyond the ones it declares, so the field a CSV would simply
have carried has to be named."* `E-RESOLVER-MEASUREMENT-FIELD`'s own row is worded unconditionally
to match: *"names a field, and the resolver the roster came from yields no attribute of that name to
collapse on."* So emit ungated. **The consequence, stated rather than discovered:** a resolver-based
roster whose measurement identity is invented by a step must still yield the `by` attribute. That is
the row's own rule, not a narrowing this task invents; no document changes.

**The columns it checks against are the pre-projection ones** task 25 returns — the union of
attribute names the resolver actually yielded — not the projected roster, which by construction
carries only declared attributes and would make this check fire for every correct config.

- [ ] **Step 1: Write the failing test.** In `tests/test_validate.py`, calling `_check_measurements`
      directly (the module already imports it):

```python
def test_a_resolver_yielding_no_measurement_field_is_refused_under_its_own_code():
    """`E-RESOLVER-MEASUREMENT-FIELD`, ungated: § Where units come from makes
    yielding `measurements.by` an obligation for a resolver, where a table's `by`
    may name an identity the step invents. Its own code rather than
    `E-UNITS-ATTR-MISSING`: the two name different declarations, and a reader
    fixing one is not fixing the other."""
    c = Collector()
    _check_measurements(
        {"from": {"resolver": "plate_wells"}, "measurements": {"by": "read_id", "collapse": "mean"}},
        UnitList([Unit(key="a1", attributes={"operator": "kj"})]),
        None,
        frozenset({"operator"}),
        c,
    )
    found = {f.code: f.message for f in c.findings}
    assert "E-RESOLVER-MEASUREMENT-FIELD" in found
    assert "E-UNITS-ATTR-MISSING" not in found
    assert "read_id" in found["E-RESOLVER-MEASUREMENT-FIELD"]
    assert "plate_wells" in found["E-RESOLVER-MEASUREMENT-FIELD"]


def test_a_resolver_that_does_yield_the_measurement_field_reports_nothing():
    """THE CONTROL. Without it, a branch that reported unconditionally would pass
    the test above."""
    c = Collector()
    _check_measurements(
        {"from": {"resolver": "plate_wells"}, "measurements": {"by": "read_id", "collapse": "mean"}},
        UnitList([Unit(key="a1", attributes={"operator": "kj"})]),
        None,
        frozenset({"operator", "read_id"}),
        c,
    )
    assert [f.code for f in c.findings] == []


def test_a_table_source_keeps_its_collapse_gated_reading_of_the_same_field():
    """The two paths stay different, deliberately. A table's `by` naming no column
    is only a fault once rows were actually collapsed, because the same
    declaration serves the step path. Asserting this here is what stops a future
    tidy-up from unifying the two branches on the resolver's stricter rule."""
    c = Collector()
    _check_measurements(
        {"from": "index.csv", "measurements": {"by": "read_id", "collapse": "mean"}},
        UnitList([Unit(key="a1", attributes={"operator": "kj"})]),
        {"min": 1, "max": 1, "median": 1},
        frozenset({"operator"}),
        c,
    )
    assert [f.code for f in c.findings] == []
```

- [ ] **Step 2: Run and see it fail.** The first test fails with
      `"E-RESOLVER-MEASUREMENT-FIELD" in found` → `False` (no such branch exists).

- [ ] **Step 3: Implement.** In `validate._check_measurements`, immediately after `valid_by` is
      computed and **before** the existing `elif technical_n is not None and technical_n["max"] > 1`
      arm, add a resolver arm — read the surrounding `if valid_by is None:` chain and extend it
      rather than inserting a second, parallel chain:

```python
    source = units.get("from")
    resolver = source.get("resolver") if isinstance(source, dict) else None
    if valid_by is not None and isinstance(resolver, str) and resolver:
        # Ungated, unlike the table arm below it. A table's `by` may name a
        # measurement identity the STEP invents through `io.record(...,
        # measurement=)`, which is why that arm waits until rows were actually
        # collapsed. A resolver has no columns at all, so `reference.md` § Where
        # units come from turns yielding `by` into an obligation — "the field a
        # CSV would simply have carried has to be named" — and
        # `E-RESOLVER-MEASUREMENT-FIELD`'s row states the fault without a collapse
        # precondition. The columns here are what the resolver yielded, before the
        # projection onto `data.units.attributes`: the projected roster carries
        # only declared attributes, and `by` is not one of them.
        if valid_by not in columns:
            c.error(
                "E-RESOLVER-MEASUREMENT-FIELD",
                "data.units.measurements.by",
                f"names {valid_by!r}, and resolver `{resolver}` yields no unit carrying an "
                "attribute of that name to collapse on. A resolver has no columns beyond the "
                "attributes it yields, so yield one `Unit` per measurement, sharing a `key`, "
                f"and emit {valid_by!r} as an attribute",
            )
```

      and guard the existing table arm so one declaration draws one code: change it to
      `elif valid_by is not None and resolver is None and technical_n is not None and technical_n["max"] > 1:`
      — read the existing chain before editing, because its first arm is `if valid_by is None:` and
      the shape must stay a single chain.

      In `docs/reference.md`, strike `E-RESOLVER-MEASUREMENT-FIELD`'s **`Not yet emitted:`** clause
      whole — the sentence *"a resolver-produced roster does not exist in this build"* is the claim
      that expires. The row's `E-UNITS-ATTR-MISSING` cross-reference stays: the two codes still name
      different declarations.

- [ ] **Step 4: Run and see it pass.** `uv run pytest` → **2082 + 3 = 2085 passed**, 1 skipped,
      2 xfailed. Then the other three commands.

- [ ] **Step 5: Mutate.** In `src/publishable/validate.py`, change the resolver arm's
      `if valid_by not in columns:` to `if valid_by not in columns and technical_n is not None and technical_n["max"] > 1:`
      — the gate the table arm carries, applied where the row says it must not be.
      `tests/test_validate.py::test_a_resolver_yielding_no_measurement_field_is_refused_under_its_own_code`
      must **FAIL**: its `technical_n` argument is `None`, so the gated branch reports nothing.
      **Checked against the test body:** the test passes `None` for `technical_n` precisely to
      instantiate the ungated reading — a test that passed `{"max": 3}` would have made this
      mutation blind, and the choice of `None` is what separates the two readings.

      Second mutation, for the code split: change the resolver arm's code string to
      `"E-UNITS-ATTR-MISSING"`. The same test must **FAIL** on
      `assert "E-UNITS-ATTR-MISSING" not in found`. **Checked:** that negative assertion is paired
      with a positive one on the resolver code in the same test, so it is not a bare absence.

- [ ] **Step 6: Commit.** `validate: a resolver must yield the measurement field it declares`

---

