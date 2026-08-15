# Task 9 report — the stratified draw

Status: COMPLETE
Commit: f69055a

## Test summary

`uv run pytest` 1741 passed + 2 xfailed (baseline 1732 + 2 xfailed; 9 new tests: the brief's 6 plus
3 I added for degenerate shapes — size-one stratum, all-identical-value stratum, and more strata than
units where every unit is a singleton stratum). `uv run mypy` and `uv run ruff check .` both clean.

## What was built

`percentile_over_units` in `src/publishable/stats.py` gained `strata: Sequence[Any] | None = None`.
When given, values are grouped by stratum before any sort (carrying each value's weight with it via a
single `carried` weight vector shared with the existing weighted path), each stratum's pool is sorted,
the pools are ordered by their own sorted contents (not by label), and each draw pulls exactly as many
indices from each pool as that pool holds. Unstratified callers (`strata=None`, the default) take the
identical code path as before — the existing ~20 `percentile_over_units` tests pass unchanged, and the
task-1 regression pin is untouched.

Mutation-tested per the brief:
- Draw-count mutation (`range(1)` instead of `range(len(pool))`) — `test_a_stratified_draw_preserves_each_stratum_size`
  FAILED (interval moved to ~36.7–37.4, next to the mean-of-stratum-means 37.17 the fixture is sized to
  distinguish). Reverted in place, re-ran, PASS.
- Pool-ordering mutation (`ordered = [sorted(pools[k]) for k in sorted(pools)]`, i.e. order by label
  instead of by sorted contents) — `test_a_stratified_draw_is_invariant_to_stratum_labels` FAILED
  (9.68... vs a different number under relabelling). Reverted in place, re-ran, PASS.
`__pycache__` cleared between mutation and revert both times; reverts were in-place edits, never
`git checkout`.

## Degenerate shapes — decided and tested

- **Misaligned `strata` length**: raises `ValueError` (via `zip(..., strict=True)`), per the brief's
  own test. Treated as a programming error, not a user error to guard softly — consistent with the
  existing `weights` contract in the same function.
- **Stratum of size 1**: works, contributes its one value deterministically to every draw. Tested with
  the "high" band split into two singletons.
- **Stratum of all-identical values**: works, contributes zero variance of its own; only the varying
  strata widen the interval. Tested by replacing the "mid" band with a repeated constant.
- **More strata than... every unit its own stratum**: works, collapses to a zero-width point interval
  at the sample mean (no resampling freedom left). Not an error — noted in the test docstring that a
  design landing here is a `validate`-time concern (`E-STATS-RESAMPLE-*`), not something this
  construction should refuse.

## Concerns / notes for later tasks

- No brief/code disagreement found — the brief's exact implementation matched what I read at
  `stats.py:488` before editing, and the fixture arithmetic (9.83 / 37.17) checks out.
- Task 14 passes `strata=` through from `summarize_step`/resample resolution, and task 15 builds on
  top of this — both should be able to rely on: unstratified default path is byte-identical to
  pre-task-9 behavior; `strata=None` is a true no-op; stratum ordering is by sorted contents, not by
  first-seen order or label, so callers must not assume label order survives.
- `docs/superpowers/` progress ledger (`progress.md`) had an uncommitted pre-existing edit (dispatch
  note for task 9) from before this task started; left untouched and uncommitted — not part of this
  task's diff.
