# Task 16 review — a column contrast's paired percentile, and the correction pool

Reviewed at `b06079c` (base `c1286bb`). Tree verified identical to the commit after every mutation.

**Spec compliance: ✅**
**Task quality: approved with findings** (1 Important, 6 Minor)

---

## Verified by mutation, not by reading

| Mutation | Where | Result |
|---|---|---|
| `resample_columns=resample_spec["declared"]` → `True`, both `command_run` call sites | `cli.py:2274`, `:2287` | **FAILS** — task 1's `_assert_undeclared_resample_shape` breaks on `col_contrast["method"] == "paired_t_over_units"` (got `paired_percentile_over_units`), on both the absent-key and explicit-`null` pins |
| `corrected_from_pool = is_derived or resample_columns` → `is_derived` | `cli.py` `Member` construction | **FAILS** on exactly the not-equal-to-`t_bound` assertion. The two containment assertions still *pass* under the mutation, so that third assertion is the only load-bearing one |
| `col_keys` → `base_keys` in the `paired_percentile_of_derived` call | column branch | **FAILS** on `ragged["method"]`; probed both entries under the mutation — `sometimes` → `method: None, ci95: None, n_paired: 30`, `always` → `paired_percentile_over_units [16.025, 23.025], n_paired: 40`. Attributed to the ragged units, not incidental |

`__pycache__` cleared between every run; reverts by in-place edit, then byte-compared against a pre-mutation copy (`BOTH-IDENTICAL`). Final state: `1795 passed, 2 xfailed`; `ruff check` and `mypy` clean.

### The `declared` seam is tested — not a third instance
The slice's recurring defect (task 14's gate, task 15's clustered wiring: a seam named in a brief and
instantiated by no fixture) does **not** recur here. Task 1's undeclared-shape pin asserts the column
contrast's `method` *and* its exact `ci95`, so it both reaches the changed code and discriminates.

### The vacuous-test fix is genuine
The implementer's report is accurate. With the brief's `diffs = [float(i) for i in range(40)]` the
assertion passes under both correct and mutated code; with the corrected `[2.0 * float(i) ...]` the
mutation produces `corr = (30.3817, 47.6183)` matching `t_bound` exactly and the assertion fires.
`_CONDITION_SCALED_STEP`'s real scales are 1.0/3.0/5.0 (task 1's review changed them to break a
19.5-vs-19.5 coincidence), so the per-unit difference is `2i`, and the fix is correct.

### Not findings, checked and cleared
- `paired: True` still hard-coded at both sites; derived `cohens_d` still `None`. Unchanged in the diff.
- No new `members.append` — the correction family's shape is unchanged, and Holm still ranks on
  `delta / (raw half-width)`.
- Clustered paired forms: **unreachable**. `validate` refuses `cluster_by` beside a comparison family
  with `E-DATA-CLUSTER-CONTRAST` (confirmed by running such a config), so the missing `_clustered`
  suffix on the contrast path is not a live divergence from § Statistical reporting.
- The `_column_mean`-passed-twice justification is sound: `paired_percentile_of_derived`'s
  shared-closure warning is about one formula evaluated against two *identical* tables; here the two
  tables are the two conditions' own collapsed data, so nothing cancels.
- `resample_draws` is absent from the column contrast entry — symmetric with the derived contrast,
  and task 1's pin only asserts its absence under an *undeclared* resample. Shape unchanged.

---

## Findings

### Important

**I1. `_comparison_step_blocks`'s own docstring still states the guarantee this task falsifies.**
`src/publishable/cli.py:704–707`:

> the second return value is the correction family's raw material: one `Member` per metric entry,
> carrying the evidence its interval was read from — the draw pool for a derived metric, **the
> per-unit differences for a recorded column**.

That is the identical sentence the brief's Step 3(b)/(c) rewrote in `correction.py`, left standing in
the very function that changed it. This is the repo's most-repeated defect (CLAUDE.md § Two habits
that cost real work — "a comment or docstring claiming a guarantee the code does not provide, at
least eight instances"), and the sweep that fixed it two files over stopped one file short. Fix by
naming what now decides — the pool when the column resamples, the differences when it doesn't.

### Minor

**M2. The added docstring paragraph omits the `n_paired >= 2` condition.** It reads "unless
`resample_columns` is set, when it instead takes `paired_percentile_of_derived`". The code also
requires `n_paired >= 2`; below that it still calls `paired_t_over_units`. Harmless in effect
(`paired_t_over_units` returns `None` at n < 2, so no interval is published and `Member.__post_init__`
exempts `ci95=None`), but the sentence overstates.

**M3. The test recomputes Holm's level instead of reading it, and the two family members are exactly
tied.** `level = 0.05 / entry["family_size"]` is holm's *rank-1* level; `run.yaml` exposes
`correction_level` and task 1's pin already asserts on it. Measured on this fixture: spearman
`delta 39.0 / half-width 7.0`, kendall `78.0 / 14.0` — kendall's pool is element-wise exactly 2×
spearman's (same seed → same index draws), so the ranking statistic is *identical* and spearman's
rank-1 position comes from the tie-break, not from evidence. The failure mode is loud rather than
silent (the strict-widening assertion breaks first, since at level 0.05 `interval_at` reads the raw
ranks), so this is fragility, not vacuity — but reading `entry["correction_level"]`, or adding
`assert entry["correction_level"] == 0.025`, removes an expected value derived from an assumption
about the fixture. Same class as the defect just fixed one line above it.

**M4. The performance extrapolation ignores row width.** The conclusion is right; the number isn't.
The brief's probe row carries **one** column, but each draw does `{"unit": k, **of[k]}` over whole
rows, so the per-column-comparison cost itself grows with columns-per-row while the column count is
*also* the outer multiplier. Re-measured at n=240 / 2000 draws: **1 column 0.19 s** (matching the
report's 0.18 s), **10 columns 0.32 s** — 1.7×, not 10×, since the per-draw cost is dominated by the
two dict constructions and `unit_table_from_rows` rather than by row width. So the report's
"10 columns × 5 comparisons ≈ 9 s" is ≈ **16 s**. Still far under the brief's
~2 s/column-comparison threshold, so keeping `paired_percentile_of_derived` rather than writing the
direct construction was correct.

**M5. The comment above the `Member` construction is now false on the new path.** "An entry with no
`ci95` carries neither and is dropped by `family_members`" — when `resampled.interval is None`
(surviving draws below `min_honest_draws`) the member still carries `pool=` with `ci95=None`.
`__post_init__` exempts that case, so nothing breaks; the sentence is simply wrong. Pre-existing shape
on the derived branch, newly reachable for every recorded column.

**M6. A declared `resample` can now silently remove a column contrast's interval, with no warning.**
A ragged column that previously reported `paired_t_over_units` over its own `col_keys` can now come
back below `min_honest_draws` and report `ci95: null`. `W-STATS-RESAMPLE-THIN` is emitted only from
the per-condition path (`cli.py:1974`); `_comparison_step_blocks` emits no resample finding at all.
Pre-existing for derived contrasts, widened here to columns. **Filed** in
`docs/superpowers/spec-defects.md` (§ "The contrast path discloses nothing about its resample…"),
owner **H4's contrast-side hardening**, rather than fixed here.

**M7. The zero-width refusal is not settled on `paired_percentile_of_derived`.** It carries none of
the content-based degenerate refusals `percentile_over_units`, `percentile_over_units_clustered` and
`percentile_of_derived` acquired. Confirmed end to end: a column identical across both conditions
(`_AGGREGATE_STEP`) now publishes `method: paired_percentile_over_units, delta: 0.0,
ci95: [0.0, 0.0], ci95_corrected: [0.0, 0.0]`. **Not a regression** — `paired_t_over_units([0.0] * 40)`
already returned `Interval(0.0, 0.0)`, and the delta is 0.0 beside it, so this is not the
"plausible but wrong" nonzero-delta-beside-zero-width case the construction's own docstring warns of.
But it is now the *fourth* construction reachable from a recorded column, and it is the one that
never got the sweep. **Filed** in the same `spec-defects.md` entry as M6, same owner; not fixed here.
