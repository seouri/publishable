## Task 7: `resample` declared with no `data.units`

**Files:** Modify `src/publishable/validate.py`, `docs/reference.md`. Test `tests/test_validate.py`.

**Interfaces:**
- Consumes: `validate._check_resample(doc, roster, c)` (Tasks 4–6).
- Produces: `E-STATS-RESAMPLE-UNITS`.

**Why this is a task and not a footnote.** Today `E-STATS-RESAMPLE-UNSUPPORTED` covers this shape wholesale. Retire it (Task 12) and a bare `resample: {method: bootstrap, n: 2000}` with **no roster** validates clean and does nothing — literally the failure `_check_unimplemented`'s own comment records for `E-SWEEP-SAMPLE-BASELINE`: *"Retiring it made the shape reachable without implementing them."* Tasks 4, 5 and 6 all presuppose a roster and none covers its absence.

`reference.md` marks the `units:` block "required by fold, resample, null_test" and says of a unit-less design that `fold`, `statistics.resample` and `statistics.null_test` "then aren't available, which is correct, since there'd be nothing to partition or resample". The precedent shape is `_check_replication`'s fold-without-basis check, which reports `E-REPL-FOLD-K` when `fold_basis` is `None` for the same reason.

**Gate on the declaration, not on `roster is None`.** `roster` is also `None` when `data.units` *is* declared but failed to resolve — a table that does not exist, a `key` column absent — and that fault already has its own finding from `_check_units`. Reporting a second, derived fault on top of the one the reader has to fix anyway is what the `usable_cluster` guard in `validate_config` avoids by the same reasoning.

- [ ] **Step 1: Write the failing test** — append to `tests/test_validate.py`:

```python
def test_a_resample_with_no_unit_roster_is_refused(write_config):
    """`reference.md` marks `data.units` "required by fold, resample,
    null_test". Once `E-STATS-RESAMPLE-UNSUPPORTED` retires, this shape would
    otherwise validate clean and do nothing — the exact failure
    `_check_unimplemented`'s own `E-SWEEP-SAMPLE-BASELINE` comment records."""
    found = codes(
        write_config({"statistics": {"resample": {"method": "bootstrap", "n": 2000}}})
    )
    assert "E-STATS-RESAMPLE-UNITS" in found
    # Positive companion in the same test: the identical declaration WITH a
    # roster is not refused, so this cannot pass by refusing every resample.
    assert "E-STATS-RESAMPLE-UNITS" not in codes(
        write_config(
            {
                "data.units": {"from": "index.csv", "key": "patient_id"},
                "statistics": {"resample": {"method": "bootstrap", "n": 2000}},
            }
        )
    )


def test_an_unresolvable_roster_does_not_earn_a_second_resample_finding(write_config):
    """`roster` is `None` for a declared-but-unresolvable `data.units` too, and
    that fault already has `_check_units`' own finding. Gating on the DECLARATION
    rather than on `roster is None` is what keeps this from reporting a derived
    fault on top of the one the reader has to fix anyway."""
    c = Collector()
    validate_config(
        write_config(
            {
                "data.units": {"from": "nope.csv", "key": "patient_id"},
                "statistics": {"resample": {"method": "bootstrap", "n": 2000}},
            }
        ),
        c,
    )
    found = {f.code for f in c.findings}
    assert "E-STATS-RESAMPLE-UNITS" not in found
    # The positive half: the real fault IS reported, so the test cannot pass by
    # the config being clean.
    assert any(code.startswith("E-UNITS-") or code.startswith("E-DATA-") for code in found)
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_validate.py -k no_unit_roster or unresolvable_roster -x`. The first fails on the missing code; the second passes vacuously and is the control for the gating decision.

- [ ] **Step 3: Implement** — in `src/publishable/validate.py`, at the **top** of `_check_resample`, immediately after the `if not isinstance(resample, dict) or not resample: return` guard:

```python
    # No roster at all, which is a different fault from every check below and
    # the one they all presuppose away. `reference.md` § The one config file
    # marks `units:` "required by fold, resample, null_test", and § Where units
    # come from says resample "isn't available" without one. The precedent is
    # `_check_replication`'s fold-without-basis check (`E-REPL-FOLD-K`), for the
    # same reason: a declaration that cannot operate on anything is refused
    # rather than accepted and silently skipped.
    #
    # Read from the DECLARATION, not from `roster is None`: the roster is also
    # `None` when `data.units` is declared and failed to resolve, and that fault
    # already has `_check_units`' own finding. A second, derived fault on top of
    # the one the reader has to fix anyway is what `validate_config`'s
    # `usable_cluster` guard avoids by the same argument. Every later check in
    # this function returns after this one, since each of them presupposes a
    # roster it would have nothing to read.
    units_declared = ((doc.get("data") or {}).get("units")) or {}
    if not units_declared:
        c.error(
            "E-STATS-RESAMPLE-UNITS",
            "statistics.resample",
            "is declared and `data.units` is not, so there is no unit table to draw "
            "from and no metric core could recompute on a draw — a declaration that "
            "changes no behavior. Declare `data.units`, or drop `resample` and report "
            "over repeats, which is honest for a design whose executions are the "
            "observations",
        )
        return
```

  (b) `docs/reference.md` § Errors `validate` reports:

```markdown
| `statistics.resample` is declared and `data.units` is not — there is no unit table to draw from, so the declaration would change no behavior. Read from the declaration, not from whether a roster resolved: a declared-but-unresolvable `data.units` already has its own finding | `E-STATS-RESAMPLE-UNITS` |
```

  And a § Validation row:

```markdown
| Resample has a roster | `statistics.resample` is declared with no `data.units` — nothing to resample, and the declaration would run nothing |
```

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_validate.py -k resample`, then `uv run pytest`, `uv run mypy`, `uv run ruff check .`, then the doc mechanical pass.

- [ ] **Step 5: Mutate** — in `validate.py`, change the gate to `if roster is None:`. Run `uv run pytest tests/test_validate.py -k unresolvable_roster`. `test_an_unresolvable_roster_does_not_earn_a_second_resample_finding` must FAIL (the derived finding now appears) while `test_a_resample_with_no_unit_roster_is_refused` still passes — which is the whole point of writing both. Delete `__pycache__`, edit the gate back to `if not units_declared:` in place, re-run.

- [ ] **Step 6: Commit** — `feat: E-STATS-RESAMPLE-UNITS, so retiring the refusal cannot open a silent no-op`.

---

