# Zero-condition sweep expansion — defect closure report

## The defect

`sweep: {grid: {}}` (and any other `sweep` block whose declared modes are all
falsy) validated clean and expanded to zero conditions, so a run executed
nothing while reporting `status: completed`. The per-axis check in
`_check_sweep` (`E-SWEEP-AXIS-EMPTY`) only runs inside `for path, values in
grid.items()`, which never iterates when `grid` is `{}`.

## The fix

In `src/publishable/validate.py::_check_sweep`, immediately after
`conditions = expand(doc)`:

```python
if sweep and not conditions:
    c.error(
        "E-SWEEP-EXPANDS-EMPTY",
        "sweep",
        "expands to zero conditions, so the run would execute nothing while "
        "reporting success — declare `baseline`, a non-empty `grid`, or remove "
        "`sweep` entirely",
    )
```

This is a **backstop beneath** `E-SWEEP-AXIS-EMPTY`, not a replacement: the
per-axis check still runs first (earlier in the function) and still produces
its specific diagnosis for an empty grid axis. The new check refuses on the
*expansion result* — `expand(doc)` returning `[]` — so it catches every
present and future shape that reaches zero conditions, not just the one shape
(`{"path": []}`) the per-axis check enumerates. The `sweep and ...` guard is
what keeps the no-`sweep`-at-all case (`expand({})` → one unlabelled
condition) unflagged, since `sweep = doc.get("sweep") or {}` is falsy there.

Mint check: grepped `docs/reference.md` for `E-SWEEP-EXPANDS-EMPTY`,
`E-SWEEP-EMPTY`, `E-SWEEP-ZERO`, `E-SWEEP-NO-CONDITIONS` — none exist in the
spec, so `E-SWEEP-EXPANDS-EMPTY` is a clean new identifier, following the
existing `E-SWEEP-*` naming in `validate.py`.

Recorded in `docs/superpowers/spec-defects.md` under the existing "A `sweep`
block present but declaring only falsy keys silently expands to zero
conditions" entry, appending a "FIXED" note with the identifier, the
rationale, and the test names (that file is gitignored, per project
convention, so it is not part of the commit).

## Second gap: bare-baseline `conditions/` level

`docs/reference.md` § How artifacts are organized says the `conditions/`
level appears when a sweep is *declared*, not when N > 1: a bare
`sweep.baseline` with no `grid` gives one condition **with** the level
(`conditions/00_baseline/...`), while no `sweep` at all gives one condition
**without** it. Both behaviors already existed in `sweep.expand` (label
`"baseline"` vs. `None`) and `runner.step_dir_for` (nests under
`conditions/<nn>_<label>` only when `condition_label is not None`), but
nothing exercised the bare-baseline case end-to-end.

Added `test_a_bare_baseline_still_gets_the_conditions_level` in
`tests/test_runner.py`, extending the existing `harness()` helper with an
optional `conditions` parameter (default unchanged: `[(0, None)]`). The new
test drives `conditions=[(0, "baseline")]` and asserts the actual directory
layout: `conditions/00_baseline/seed17/analyze` and
`conditions/00_baseline/seed42/analyze` exist, and the bare `seed17`/`seed42`
directories used by the no-sweep case do not — the direct contrast with
`test_no_sweep_means_no_conditions_level` right above it.

## Tests added

- `tests/test_validate.py`:
  - `test_an_empty_grid_block_is_refused_by_the_backstop`
  - `test_an_empty_axis_still_gets_the_specific_diagnosis_not_just_the_backstop`
  - `test_no_sweep_at_all_still_validates_clean`
  - `test_a_normal_baseline_plus_grid_config_still_validates_clean`
- `tests/test_runner.py`:
  - `test_a_bare_baseline_still_gets_the_conditions_level`

`tests/test_sweep.py::test_a_bare_baseline_is_one_condition_but_labelled`
already existed and pins `expand`'s side of the bare-baseline behavior; no
change needed there.

## Verification

- `uv run pytest -v`: 414 passed (409 pre-existing + 5 new), 0 failed.
- `uv run ruff check .`: All checks passed.
- `uv run mypy`: Success, no issues found in 33 source files.

## Files touched

- `src/publishable/validate.py` — the fix and docstring update.
- `tests/test_validate.py` — four new tests.
- `tests/test_runner.py` — `harness()` gains a `conditions` parameter; one new test.
- `docs/superpowers/spec-defects.md` — FIXED note (gitignored, not committed).
