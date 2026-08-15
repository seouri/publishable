# Task 1 report: regression pin for the undeclared-`resample` shape

## Status

Done. Commit `0f62ba0` on branch `h4a-resample-honoured` (parent `eaf3605`).

## What was verified before writing anything

- `paired_t_over_units([0.0] * 40)` → `Interval(low=0.0, high=0.0, method='paired_t_over_units')`
  and `cohens_dz([0.0] * 40)` → `None`, exactly as the brief states — this is why
  `_CONDITION_SCALED_STEP` (not `_AGGREGATE_STEP`) had to be introduced.
- `derived_metric_draws = 2000` at `src/publishable/cli.py:1507`.
- `summarize_step`'s unweighted/unclustered column branch is
  `interval = t_over_units(values)` in `src/publishable/stats.py` (around line 1366).
- `run_a_project`'s override merge is a top-level `doc.update(overrides)`
  (`tests/test_cli.py`), confirming the stated `statistics={"resample": None}` hazard.

No disagreement between the brief and the code was found; both traps described in the
brief were reproduced exactly as predicted.

## What was changed

- `tests/test_cli.py`: added `_CONDITION_SCALED_STEP`, `_assert_undeclared_resample_shape`,
  `_PIN_SWEEP`, `_pinned_run`, and the two tests
  `test_the_undeclared_resample_shape_is_pinned_absent_key` /
  `..._explicit_null`, verbatim from the brief.
- `tests/test_cli.py`: added a `_starter_step` keyword to `run_a_project`, monkeypatching
  `publishable.generators.experiment.STARTER_STEP` inside the existing
  `pytest.MonkeyPatch.context()` block, the same way `aggregate_returns` does — plus a
  docstring paragraph beside `extra_step_source` documenting it. This is the only
  production-adjacent (test-helper) addition; **no file under `src/` was changed** in the
  committed diff.

## Test summary

`uv run pytest -q` → **1691 passed, 2 xfailed** (baseline 1689 passed + 2 xfailed, plus the
2 new tests — no regressions). `uv run ruff check .` → all checks passed. `uv run mypy` →
success, 42 source files (unchanged from baseline; test files are outside its configured
scope). `uv run ruff format --check tests/test_cli.py` reports pre-existing reformat
suggestions unrelated to this change (confirmed present on `eaf3605` before any edit, via
`git stash`/`ruff format --check`/`git stash pop`) — not a regression.

## How each assertion was proven able to fail

Two mutations were applied to `src/`, run against the two new tests, observed to fail on
exactly the assertion the brief predicted, then reverted **by editing the line back in
place** (never `git checkout`), with `__pycache__` cleared and the tests re-run to confirm
they pass again:

1. `src/publishable/cli.py`: `derived_metric_draws = 2000` → `500`. Both tests failed on
   `assert derived["resample_draws"] == 2000` (`500 == 2000`). Reverted; both pass.
2. `src/publishable/stats.py`: the unweighted/unclustered branch's
   `interval = t_over_units(values)` → `interval = percentile_over_units(values, 1, draws=2000)`.
   Both tests failed on `assert column["method"] == "t_over_units"`
   (`'percentile_over_units' == 't_over_units'`). Reverted; both pass.

`git diff --stat` after the final revert showed only `tests/test_cli.py` changed, confirmed
by re-running the full suite (1691 passed / 2 xfailed) before committing.

The remaining assertions in `_assert_undeclared_resample_shape` (family/correction-level
shape, `cohens_d` presence/absence on each of the four metric kinds, `resample_draws`
absence on non-derived metrics) were not separately mutation-tested beyond the two
mutations above, since the brief specifies exactly these two as the load-bearing pins for
this task; the assertions were, however, each checked once by hand to confirm the
unmutated run actually produces the value asserted (i.e., none is a tautology against a
degenerate fixture) — in particular confirming `col_contrast["cohens_d"] is not None` and
`derived_contrast["cohens_d"] is None` both hold only because `_CONDITION_SCALED_STEP`
varies with `analysis.method`, unlike `_AGGREGATE_STEP`.

## Concerns (original, superseded below)

None. Both traps described in the brief (top-level `doc.update` override replacement, and
`_AGGREGATE_STEP`'s condition-invariant column degenerating every contrast to zero-width)
were independently reproduced against the build before being designed around, matching the
brief's own verification. No conflict was found between the brief and the code.

## Addendum: coordinator review, second commit `a80e50d`

The reviewer found the "Concerns: None" line above was wrong, and the underlying pin had
two real gaps. Both are fixed in `a80e50d`.

### Important 1 — the fixture's numbers agreed with the bug

At the original scale map (`pearson: 1.0, spearman: 2.0`), four distinct quantities all
came out to `19.5`: the baseline column's own mean, the derived metric's value, the column
contrast's `delta`, and the derived contrast's `delta`. Verified against the build (a
throwaway probe test, `tests/test_zzz_probe.py`, deleted before committing):

```
column value 19.5      column ci95 [15.761212085024908, 23.23878791497509]
derived value 19.5     derived ci95 [16.025, 23.025]
col_contrast delta 19.5        derived_contrast delta 19.5
```

Two consequences, both reproduced then fixed:

- Dropping the subtraction in `cli.py`'s column-contrast delta (`of - against` → `of`
  alone) still passed both tests, because the fixture's own numbers made the wrong and
  right delta indistinguishable at this scale.
- Shifting `_compute_vs_baseline`'s resample seed by `+1` (`seed=resample_seed_value` →
  `seed=resample_seed_value + 1`) still passed, because no assertion read `ci95`
  numerically.

Fix: rescaled `_CONDITION_SCALED_STEP`'s method scale from `{pearson: 1.0, spearman: 2.0,
kendall: 3.0}` to `{pearson: 1.0, spearman: 3.0, kendall: 5.0}`, so the paired delta
(`19.5 * (3.0 - 1.0) = 39.0`) is numerically distinct from the baseline column's own value
(`19.5`). Re-probed at the new scale:

```
column value 19.5       column ci95 [15.761212085024908, 23.23878791497509]
derived value 19.5      derived ci95 [16.025, 23.025]
col_contrast delta 39.0         ci95 [31.522424170049817, 46.47757582995018]
derived_contrast delta 39.0     ci95 [32.050000000000004, 46.050000000000004]
```

`_assert_undeclared_resample_shape` now asserts each of these seven numbers with
`pytest.approx`, not merely `is not None`. Also added a `ValueError` (instead of a bare
`KeyError`) if `_CONDITION_SCALED_STEP` is ever swept over a fourth `analysis.method` value
lacking a scale entry — cheap, and named as a Minor by the reviewer.

### Important 2 — correction levels were order-blind

The original `sorted(...) == [0.025, 0.05]` check passed regardless of which contrast
carried which level. Replaced with per-member assertions:
`col_contrast["correction_level"] == pytest.approx(0.05)` and
`derived_contrast["correction_level"] == pytest.approx(0.025)` (the derived contrast's
2000-draw percentile interval is narrower than the column contrast's t-interval, giving it
the stronger evidence ratio and so Holm's rank-1, tighter level).

### Every new numeric assertion, and the mutation each one catches

All four mutations below were run against `src/`, observed to fail both tests on exactly
the named assertion, then reverted **in place** (edited back, never `git checkout`), with
`__pycache__` cleared before each re-run, and the full suite (`uv run pytest`, 1691 passed
/ 2 xfailed) and `git diff --stat` (clean) confirmed after the last revert:

| Assertion | Mutation that fails it |
|---|---|
| `derived["resample_draws"] == 2000` | `cli.py`: `derived_metric_draws = 2000 → 500` (brief's mutation 1; re-confirmed against the new assertions) |
| `column["method"] == "t_over_units"` | `stats.py`: unclustered branch `t_over_units(values)` → `percentile_over_units(values, 1, draws=2000)` (brief's mutation 2; re-confirmed) |
| `col_contrast["delta"] == pytest.approx(39.0)` | `cli.py`: column-contrast `diffs` computed as `of_collapsed[k][metric_key]` alone, dropping `- against_collapsed[k][metric_key]` — obtained `58.5`, not `39.0`, so still caught even though the fixture's collision made the *originally reported* `19.5` no longer the number produced |
| `derived_contrast["ci95"] == pytest.approx((32.05..., 46.05...))` | `cli.py`: `_compute_vs_baseline`'s `seed=resample_seed_value` → `seed=resample_seed_value + 1`; obtained `[31.65, 45.85]` |
| `col_contrast["correction_level"] == pytest.approx(0.05)` and `derived_contrast["correction_level"] == pytest.approx(0.025)` | `correction.py`: `rank_family`'s sort key `-_evidence_ratio(m)` → `_evidence_ratio(m)` (drop the negation), swapping which member ranks first; obtained `col_contrast["correction_level"] == 0.025` |

`column["value"] == pytest.approx(19.5)`, `derived["value"] == pytest.approx(19.5)`, and
`column["ci95"] == pytest.approx((15.76..., 23.24...))` were not separately mutated beyond
the above — they are read off the same computations the delta/ci95 mutations already
exercise (the column value feeds directly into the delta the drop-subtraction mutation
breaks), and were checked once by hand against the probe's un-mutated output to confirm
they are not tautological.

### Minors: taken or skipped

- **Brace-doubling rule for `_starter_step`, and precedence with `aggregate_returns`** —
  taken. Added to the docstring: `_starter_step` goes through the same
  `STARTER_STEP.format(pkg=pkg)` as its sibling, so a literal `{` must be doubled; and
  because its `mp.setattr` runs after `aggregate_returns`'s in `run_a_project`'s body, it
  wins for `STARTER_STEP` if both are passed, while `aggregate_returns`'s `aggregate` patch
  still applies on top.
- **`_CONDITION_SCALED_STEP` `KeyError` on a fourth swept value** — taken. Now raises
  `ValueError` naming the missing method.
- **`repeat_spread.std == 0.0`** — skipped. `_CONDITION_SCALED_STEP` records a value that is
  a deterministic function of `(unit index, analysis.method)` with no seed dependence, the
  same as `_AGGREGATE_STEP` it's modeled on, so every seed repeat produces an identical
  value and `repeat_spread` is uninformative here by construction. Fixing it would mean
  giving the step actual seed-dependent noise, which is more than "cheap" and isn't needed
  by this task's two pins (neither asserts on `repeat_spread`); noting it here since Tasks
  15/16 inherit this fixture and should know the field carries no signal in it.

### Calibration retraction

The original report's "Concerns: None" and its claim that no assertion was "a tautology
against a degenerate fixture" were wrong — the whole `_CONDITION_SCALED_STEP` fixture was
degenerate in exactly the way that phrase warns against, at the original scale. Running
the brief's two named mutations was necessary but not sufficient; the fix required asking
what else could slip past the pin, which the brief could not enumerate. Retracted.
