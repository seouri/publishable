## Task 5: `resample.stratify_by` names declared attributes

**Files:** Modify `src/publishable/validate.py`, `docs/reference.md`. Test `tests/test_validate.py`.

**Interfaces:**
- Consumes: `validate._check_resample(doc, roster, c)` (Task 4); `units.stratum_names(stratify_by) -> tuple[str, ...]` (`src/publishable/units.py:1117`), already imported by `validate._check_assign`.
- Produces: `E-STATS-RESAMPLE-STRATIFY-UNKNOWN`, which mints the identifier § Validation's *Resample strata exist* row has never had.

**Reuse `_check_report_by`'s shape, not `units._stratum_groups`.** The reference set is `data.units.attributes` — the declared set, exactly as `_check_report_by` reads it — because a stratum is read per unit when the draw is taken, so it has to survive resolution as an attribute. `units._stratum_groups` is `assign`-specific: it also admits a `sweep.groups` axis name as a legal target and raises `E-DATA-ASSIGN-STRATIFY-UNKNOWN`, neither of which applies to a resample.

**Read the declaration through `units.stratum_names`.** A bare `stratify_by: site` names one stratum exactly as `[site]` does — the same normalization the draw (Task 9) will balance on. Two independent readings of one declaration is the validate-clean-then-disagree shape `stratum_names`' own docstring exists to prevent. **Resample takes several names**, and the stratum is their cross: `stratify_by: [dx_status, count_stratum]` is `reference.md` § Weighted samples' own example.

**One finding per offending name**, so a declaration naming two undeclared attributes earns two findings rather than one that names only the first — the rule `E-DATA-ASSIGN-STRATIFY-UNKNOWN` already follows.

- [ ] **Step 1: Write the failing test** — append to `tests/test_validate.py`:

```python
def test_a_resample_stratum_must_be_a_declared_attribute(write_config):
    """§ Validation's *Resample strata exist* row has never had an identifier.
    The reference set is `data.units.attributes`, the declared one — the same set
    `_check_report_by` reads, and for its reason: a stratum is read per unit when
    the draw is taken, so it has to survive resolution as an attribute."""
    found = codes(
        write_config(
            {
                "data.units": {
                    "from": "index.csv",
                    "key": "patient_id",
                    "attributes": ["cohort"],
                },
                "statistics": {
                    "resample": {"method": "bootstrap", "n": 2000,
                                 "stratify_by": ["count_stratum"]}
                },
            }
        )
    )
    assert "E-STATS-RESAMPLE-STRATIFY-UNKNOWN" in found
    # Positive companion, same test: a DECLARED name is not refused, so this
    # cannot pass by the check refusing every stratum it is handed.
    assert "E-STATS-RESAMPLE-STRATIFY-UNKNOWN" not in codes(
        write_config(
            {
                "data.units": {
                    "from": "index.csv",
                    "key": "patient_id",
                    "attributes": ["cohort"],
                },
                "statistics": {
                    "resample": {"method": "bootstrap", "n": 2000, "stratify_by": ["cohort"]}
                },
            }
        )
    )


def test_a_resample_declaration_earns_one_finding_per_offending_stratum(write_config):
    """Two undeclared names, two findings — not one naming only the first. The
    count is the assertion: a check that `break`s after the first offender passes
    a membership test and fails this."""
    c = Collector()
    validate_config(
        write_config(
            {
                "data.units": {
                    "from": "index.csv",
                    "key": "patient_id",
                    "attributes": ["cohort"],
                },
                "statistics": {
                    "resample": {
                        "method": "bootstrap",
                        "n": 2000,
                        "stratify_by": ["dx_status", "count_stratum", "cohort"],
                    }
                },
            }
        ),
        c,
    )
    offenders = [f for f in c.findings if f.code == "E-STATS-RESAMPLE-STRATIFY-UNKNOWN"]
    assert len(offenders) == 2
    named = " ".join(f.message for f in offenders)
    assert "dx_status" in named and "count_stratum" in named
    # `cohort` IS declared and must not be among them — three names, two
    # offenders, so a check that reported all three would also fail the count.
    assert "cohort" not in named


def test_a_bare_string_resample_stratum_is_read_as_one_name(write_config):
    """`units.stratum_names` reads `stratify_by: site` as one name exactly as
    `[site]` is — the same normalization the draw balances on. Read as a
    sequence of characters instead, this would report four findings (`s`, `i`,
    `t`, `e`) rather than one, which is what the count catches."""
    c = Collector()
    validate_config(
        write_config(
            {
                "data.units": {"from": "index.csv", "key": "patient_id",
                               "attributes": ["cohort"]},
                "statistics": {"resample": {"method": "bootstrap", "n": 2000,
                                            "stratify_by": "site"}},
            }
        ),
        c,
    )
    offenders = [f for f in c.findings if f.code == "E-STATS-RESAMPLE-STRATIFY-UNKNOWN"]
    assert len(offenders) == 1
    assert "site" in offenders[0].message


def test_an_empty_resample_stratify_by_is_not_refused(write_config):
    """`stratify_by: []` is what a full expansion shows and what most designs
    carry; it names no stratum and sends the draw down its unstratified path.
    `stratum_names` returns `()` for it, so there is nothing to refuse."""
    found = codes(
        write_config(
            {
                "data.units": {"from": "index.csv", "key": "patient_id"},
                "statistics": {"resample": {"method": "bootstrap", "n": 2000,
                                            "stratify_by": []}},
            }
        )
    )
    assert "E-STATS-RESAMPLE-STRATIFY-UNKNOWN" not in found
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_validate.py -k resample_stratum or resample_declaration_earns -x`. Expect all four to fail on the missing code (the first three) and the last to pass vacuously (note it: a test that passes before the feature exists is a control, and its value comes from the three beside it).

- [ ] **Step 3: Implement** — in `src/publishable/validate.py`, add `stratum_names` to the existing `from publishable.units import (...)` block, and append inside `_check_resample`, after the `n` check:

```python
    # The declared set, `data.units.attributes` — the same reference
    # `_check_report_by` reads, and for its reason: `strata.levels_for` and the
    # draw both read the attribute per unit, so a typo and an attribute no unit
    # carries are indistinguishable downstream. NOT `units._stratum_groups`,
    # which is `assign`-specific: it admits a `sweep.groups` axis name as a
    # legal target and raises `E-DATA-ASSIGN-STRATIFY-UNKNOWN`, and a resample
    # draws from the roster rather than from an allocation, so neither applies.
    #
    # Read through `units.stratum_names`, the same normalization the draw
    # balances on: a bare `stratify_by: site` is one name to both. Two
    # independent readings of one declaration is the validate-clean-then-
    # disagree shape that function's own docstring exists to prevent.
    #
    # Filtered to strings the same way `_check_report_by` filters `attributes`:
    # a non-string item there is `_check_units`' own finding (`E-UNITS-ATTR-
    # MISSING`), and `set(...)` over the raw list would raise on an unhashable
    # one before that finding is ever reached.
    declared = {
        a
        for a in (((doc.get("data") or {}).get("units") or {}).get("attributes") or [])
        if isinstance(a, str)
    }
    for name in stratum_names(resample.get("stratify_by")):
        # One finding per offending name, not one naming only the first: the
        # declaration is a list and each entry is separately fixable, the same
        # rule `E-DATA-ASSIGN-STRATIFY-UNKNOWN` follows. A non-string entry is
        # absorbed here rather than left silent — it names no attribute either,
        # and `stratify_by`'s LEAF type is the container's, not each item's.
        if not isinstance(name, str) or name not in declared:
            c.error(
                "E-STATS-RESAMPLE-STRATIFY-UNKNOWN",
                "statistics.resample.stratify_by",
                f"names `{name}`, which is not a unit attribute — a stratum is read "
                "per unit when the draw is taken, so it has to be one. "
                f"`data.units.attributes` declares {', '.join(sorted(declared)) or 'none'}",
            )
```

  (b) `docs/reference.md`: give the existing § Validation row *Resample strata exist* its identifier by adding a registry row in § Errors `validate` reports:

```markdown
| `statistics.resample.stratify_by` names a value `data.units.attributes` does not declare, or is not a name at all. `data.units.attributes`, not the source's columns, for the same reason `E-DATA-CLUSTER-UNKNOWN` reads that set: a stratum is read per unit when the draw is taken, so it has to survive resolution as an attribute. Read through the same normalization the draw balances on, so a bare `stratify_by: site` is one name to both. One finding per offending name. Unlike `assign.<axis>.stratify_by`, a [`sweep.groups`](#expansion-modes) axis name is **not** a legal target here — a resample draws from the roster, not from an allocation | `E-STATS-RESAMPLE-STRATIFY-UNKNOWN` |
```

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_validate.py -k resample`, then `uv run pytest`, `uv run mypy`, `uv run ruff check .`, then the doc mechanical pass.

- [ ] **Step 5: Mutate** — in `validate.py`, add `break` as the last statement of the `for name in stratum_names(...)` loop body's `if` branch. Run `uv run pytest tests/test_validate.py -k earns_one_finding_per_offending_stratum`. It must FAIL on `len(offenders) == 2` (getting 1) while `test_a_resample_stratum_must_be_a_declared_attribute` still passes — which is why the count assertion exists and a membership assertion alone would not have caught it. Delete `__pycache__`, remove the `break` in place, re-run. Then a second mutation: replace `stratum_names(resample.get("stratify_by"))` with `resample.get("stratify_by") or []`; `test_a_bare_string_resample_stratum_is_read_as_one_name` must FAIL with 4 offenders. Revert in place.

- [ ] **Step 6: Commit** — `feat: E-STATS-RESAMPLE-STRATIFY-UNKNOWN, the identifier the Resample strata exist row never had`.

---

