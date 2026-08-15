# Task 2 report: `AXIS_MODES` splits into three predicates

**Status:** complete. Commit `4e19d5c`.

**Tests:** `uv run pytest` 1391 passed, 2 xfailed; `ruff check` and `mypy` clean.
`ruff format` not run.

## What changed

- `src/publishable/sweep.py`: `AXIS_MODES`/`NON_AXIS_MODES` → `PRODUCT_MODES` =
  (`grid`, `paired`, `sample`, `groups`), `NON_PRODUCT_MODES` = (`baseline`,
  `ablate`), `PARAMETER_AXIS_MODES` = (`grid`, `paired`, `sample`).
  `SWEEP_MODES = PRODUCT_MODES + NON_PRODUCT_MODES` — still derived.
  `axis_modes_present` → `parameter_axis_modes_present`.
- `src/publishable/validate.py`: import, one call site, and the three comments —
  **two rewritten, one deliberately left**: the comment inside the
  `E-SWEEP-KEY-UNKNOWN` `c.error` message names only `SWEEP_MODES`, which
  survived the split, so it is still true as written. The gate comment above it
  and the `E-SWEEP-ABLATE-CROSSED` comment both named the deleted tuples and are
  rewritten.
- `tests/test_sweep.py`: the partition test reworked; `tests/test_validate.py`:
  two docstrings.
- No `*.md` changed. `cohort-pilot` untouched (it declares no `groups`).
  Retirement grep run after the change: `git grep -wn` for `AXIS_MODES`,
  `NON_AXIS_MODES` and `axis_modes_present` returns nothing in tracked files.
  The commit is exactly those four files.

**`groups` still expands to no conditions.** Pinned explicitly:
`expand({"sweep": {"groups": [...]}}) == []` and `not _axes({"groups": ...})`,
tagged as the task-5 boundary — the old `for mode in NON_AXIS_MODES` loop used
to cover that, and moving `groups` into `PRODUCT_MODES` would have dropped it
silently. `E-SWEEP-GROUPS-UNSUPPORTED` untouched (task 17).

## Brief defects

1. **Steps 1–2 rest on a false premise.** `groups` was *already* in
   `NON_AXIS_MODES`, so `axis_modes_present` already excluded it and
   `ablate × groups` was already permitted. The discriminating assertion cannot
   fail before the change, and the discriminating test already existed:
   `tests/test_validate.py::test_ablate_composes_with_a_group_axis`. This task
   is behaviour-preserving vocabulary work; no new test could be red first. I
   did not manufacture one, and did not add an eleventh non-discriminating
   check — I sharpened the two existing halves' docstrings instead.
2. **"Split into `PRODUCT_MODES` and `PARAMETER_AXIS_MODES`, `SWEEP_MODES`
   derived from the partition" is not satisfiable as written.**
   `PARAMETER_AXIS_MODES` ⊂ `PRODUCT_MODES`, so those two are not a partition —
   deriving `SWEEP_MODES` from them would double-count three modes. A third name
   is forced: the partition is `PRODUCT_MODES ⊎ NON_PRODUCT_MODES`, and
   `PARAMETER_AXIS_MODES` is a predicate subset of the first half.
3. **Mutation 2 as specified is degenerate.** Hand-writing `SWEEP_MODES` with
   the same six contents changes no value — I ran it: 1391 passed, nothing
   failed. The brief's fallback test (a mode absent from both partitions refused
   by `E-SWEEP-KEY-UNKNOWN`) would also pass under the literal, so it would not
   have discriminated either; I did not add it. The contentful mutation is
   *literal `SWEEP_MODES` plus a seventh mode in `PRODUCT_MODES` only* — run
   below.

## Mutations run (`__pycache__` cleared each time, reverts verified by test run)

| Mutation | Result |
|---|---|
| `groups` into `PARAMETER_AXIS_MODES` | 2 failed, incl. `test_ablate_composes_with_a_group_axis` (the discriminator) |
| `SWEEP_MODES` hand-written, same six | **0 failed — degenerate, see defect 3** |
| `SWEEP_MODES` hand-written + `arms` added to `PRODUCT_MODES` only | 1 failed (the partition assert) |

## Concern

The subset relation is a new hole: a mode added to `PRODUCT_MODES` and forgotten
in `PARAMETER_AXIS_MODES` becomes one `ablate` may cross, and the derivation
cannot catch that. The residual literal `PRODUCT_MODES - PARAMETER_AXIS_MODES ==
{"groups"}` in `tests/test_sweep.py` is the only thing forcing the second
classification; task 5 must update it deliberately if it ever changes.
