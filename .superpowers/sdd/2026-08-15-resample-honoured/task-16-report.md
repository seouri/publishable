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

`paired_percentile_of_derived` at n=240, 2000 draws: **0.19s per column-comparison with a single
recorded column**, matching the brief's probe. Re-measured with ten columns sharing the same run,
because the probe's one-column shape understates what a real project pays (`UnitTable` construction
cost is not purely linear in column count): **0.32s per column-comparison at ten columns**. So a
10-column × 5-comparison family costs ≈16s of pure resampling at this n and draw count, not the ≈9s a
naive `1 × 0.18s × 50` multiplication would suggest. Still well under the ~2s/column-comparison
threshold the brief set for switching to a direct index-vector construction, so the existing
`UnitTable`-rebuilding implementation was kept as-is — but the 16s figure, not 9s, is the one a later
reader should inherit.

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

## Review round 1 — addressed

**Finding 1 (Important) — `_comparison_step_blocks`'s own docstring still said a `Member` carries "the
per-unit differences for a recorded column."** That is the exact sentence this task falsifies, left
unfixed in the one function the task changed (the coordinator's brief swept `correction.py` for it and
stopped one file short — the second time this slice's sweep scope missed a file). Fixed: the sentence
now reads "...the per-unit differences for a recorded column **unless a `resample` is declared, when a
column carries the draw pool too**." Swept the rest of the tracked tree for the same class of claim
(`grep` over `src/`, `tests/`, `docs/reference.md`, `docs/design-principles.md`,
`docs/experimental-designs.md`, `CLAUDE.md`): no other instance found. `correction.py`'s own two
docstrings (fixed in the original round) already state the rule correctly; the two hits in
`docs/superpowers/plans/*.md` are dated planning snapshots predating this task's implementation and
were left as historical record rather than rewritten.

**M2 — the new `_comparison_step_blocks` docstring omitted the `n_paired >= 2` condition.** Fixed:
"unless `resample_columns` is set **and the pairing has at least two units**".

**M3 — the flagship test recomputed `level = 0.05 / entry["family_size"]` instead of reading
`entry["correction_level"]`, and assumed this comparison ranks first.** It does today, but only by a
tie-break: kendall's draw pool is element-wise 2× this comparison's own (same seed, same draw indices,
and kendall's scale is 2× spearman's relative to the shared pearson baseline), so the two members'
evidence ratios are exactly equal and `rank_family`'s declaration-order tie-break — not a strength
difference — decides which one is rank 1. Fixed by reading `entry["correction_level"]` directly and
added a comment naming the tie so a future reader doesn't reintroduce the assumption. Re-verified both
mutations from Step 5 still fail correctly against the updated test (see below).

**M5 — the comment above the `Member` construction ("An entry with no `ci95` carries neither") is now
false.** A column contrast whose resample ran but produced too few surviving draws for the confidence
level still carries its (too-short, non-`None`) `pool` alongside a `None` `ci95` —
`Member.__post_init__` exempts a `ci95=None` member from the "exactly one" rule rather than requiring
`pool`/`diffs` to be `None` too. Fixed the comment to say so.

**M6/M7 — not reopened.** Filed with an owner already (H4's contrast-side hardening): a declared
`resample` can silently null a column contrast's interval because `W-STATS-RESAMPLE-THIN` is emitted
only from the per-condition path, and `paired_percentile_of_derived` never got the zero-width sweep its
three siblings have.

Re-ran the full mutation set after these fixes: both Step-5 mutations
(`corrected_from_pool = is_derived`, and `col_keys` → `base_keys`) still fail their respective tests,
confirmed, `__pycache__` cleared, reverted in place, confirmed PASS. Full suite:
`uv run pytest` — 1795 passed + 2 xfailed; `uv run mypy` and `uv run ruff check .` clean.

## Concerns

- None outstanding.
