# Task 16 report

Status: COMPLETE.

Commit: (recorded below after `git commit`).

Tests: `uv run pytest` — 1795 passed + 2 xfailed (baseline 1792 + 2, three new tests added). `uv run
mypy` and `uv run ruff check .` clean. All three new tests were confirmed FAIL before implementation,
and both named mutations (Step 5) were applied, confirmed FAIL, `__pycache__` cleared, reverted in
place, confirmed PASS.

## What changed

- `cli.py`: `_comparison_step_blocks` gained a `resample_columns: bool` keyword, threaded through
  `_compute_vs_baseline` and `_compute_declared_contrasts` (both gained the same parameter) from
  `command_run`'s `resample_spec["declared"]`. The column branch now takes
  `paired_percentile_of_derived` over `col_keys` (not `base_keys`) and a `_column_mean` closure when
  `resample_columns and n_paired >= 2`, else the existing `paired_t_over_units`. `cohens_dz` still
  computes from the local `diffs` list unconditionally. The `Member` construction now sets
  `corrected_from_pool = is_derived or resample_columns`, gating both `pool=` and `diffs=None`
  together so a column contrast under a declared `resample` carries the pool and *not* diffs.
- `correction.py`: three docstring edits, all from the brief — `_corrected_bounds`'s opening paragraph
  now states the construction is decided by which field the member carries, not by metric kind, and
  names the declared-`resample` case as what puts a column there; `Member`'s docstring states plainly
  that a column carries `pool` under a declared `resample`.
- `tests/test_cli.py`: three new tests, plus `resample_columns=False` added to the one existing direct
  call to `_comparison_step_blocks` in `test_a_comparison_reads_its_own_condition_not_condition_zero`
  (unrelated to this task's behaviour; needed only because the function's signature changed).

## Performance measurement (Step 4)

`paired_percentile_of_derived` at n=240, 2000 draws, one column-comparison: **0.18s**. Well under the
~2s/column-comparison threshold the brief set for switching to a direct index-vector construction, so
the existing `UnitTable`-rebuilding implementation was kept as-is. A run with many recorded columns ×
many comparisons pays this per (column, comparison) pair — e.g. 10 columns × 5 comparisons ≈ 9s of
pure resampling at this n and draw count — worth revisiting if a future project's config makes that
product large, but not a blocker here.

## A real brief/code disagreement found (as flagged: eleven of fifteen implementers hit one)

The brief's Step 1 test code and its own explanatory prose disagree about `_CONDITION_SCALED_STEP`'s
scale factors. The fixture that actually exists in the repo (introduced in Task 1, reused verbatim
here) is:

```python
scale_by_method = {"pearson": 1.0, "spearman": 3.0, "kendall": 5.0}
```

But the brief's prose justifying the "not the t-interval" assertion in
`test_a_column_contrast_corrects_off_its_own_pool_not_a_t_interval` says: *"`pred` is `float(i)` at
pearson and `2 * float(i)` at spearman, so the difference for unit `i` is exactly `float(i)`"* — i.e.
it assumes scale factors 1.0/2.0/3.0 (the progression `_RAGGED_COLUMN_STEP`'s *inline* scale dict uses,
not `_CONDITION_SCALED_STEP`'s). Under the real 1.0/3.0/5.0 fixture the per-unit difference (spearman
− pearson) is `2 * float(i)`, not `float(i)`.

Copying the brief's line verbatim (`diffs = [float(i) for i in range(40)]`) makes the recomputed
`t_bound` come out at half the correct magnitude — `[15.19, 23.81]` instead of the true
`[30.38, 47.62]` — and I confirmed by running the Step-5 mutation *before* fixing this that the
"not-equal-to-t_bound" assertion passed under **both** the correct implementation and the mutated one
(`corrected_from_pool = is_derived`, dropping the `or resample_columns`): the wrong `t_bound` simply
never matches either construction's actual output, so the assertion was vacuously true regardless of
the bug. I changed the test to `diffs = [2.0 * float(i) for i in range(40)]` and updated the
surrounding comment to name the actual scale factors and warn against the 1.0/2.0/3.0 assumption; with
that fix, the mutation now fails on this exact assertion (confirmed: `corr_low`/`corr_high` matched the
correctly-computed `t_bound` under the mutation, and did not match it after reverting).

## Concerns

- None outstanding. The mechanical pass on `reference.md` found nothing to change — § Statistical
  reporting's construction table already states "Every derived metric, and a column metric under
  `resample`" for `paired_percentile_over_units`, which this task's code now actually produces; no
  spec-defect to record.
