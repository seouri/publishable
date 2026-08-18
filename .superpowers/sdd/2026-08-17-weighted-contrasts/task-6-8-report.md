# Tasks 6-8 report

**Status:** all three implemented, tested, mutated, and committed.

**Commits:**
- `359d641` — cli: weights and resample strata reach the three comparison functions (task 6)
- `7099c91` — cli: a weighted column contrast weights its delta and every draw (task 7)
- `12ce355` — cli: a weighted contrast entry records weighted_by, its effective size and a weighted dz (task 8)

**Tests:** 2133 baseline → 2135 (task 6) → 2139 (task 7) → 2145 (task 8) passed, 1 skipped, 2 xfailed
throughout. `uv run ruff check .`, `uv run ruff format --check .` (80 files), and `uv run mypy` (45
source files) clean after each task.

**Mutations run (all reverted by editing back, verified by re-run):**

- Task 6: `_column_mean` branch's `strata=strata` → `strata=None` — FAILED
  `test_a_contrasts_column_draw_honours_resample_stratify_by` on the forced 5.0 floor, exactly as
  predicted.
- Task 6: `command_run`'s two `strata=resample_strata` → `strata=None` — confirmed silent: no test in
  this task's scope failed (29 `-k "weighted or strata or resample"` tests all green), matching the
  brief's own claim that this is task 13's mutation to catch, through `run`.
- Task 7: uniform `drawn = [1 for _ in column]` in place of the weight lookup — FAILED
  `test_a_weighted_column_contrast_weights_its_delta_and_its_draws` on `weighted["ci95"][0] >
  plain["ci95"][0]` (both 3.0), exactly as predicted; `delta` stayed 8.0 as the brief said it would.
- Task 7: `delta` back to bare `mean_of(diffs)` — FAILED the same test on `weighted["delta"] ==
  pytest.approx(8.0)` (got 6.0).
- Task 7: derived-branch call given `method="weighted_paired_percentile_over_units"` — FAILED
  `test_a_weighted_derived_contrast_keeps_the_unweighted_method_string` on the `method` string.
- Task 8: Kish argument changed to `list(weights.values())` (whole mapping) — FAILED
  `test_kish_is_taken_over_the_paired_intersection_not_the_weight_mapping` (6.0 vs. expected 3.0), and
  confirmed `test_a_weighted_contrast_entry_carries_the_three_documented_keys` stayed green, exactly as
  the brief predicted (its mapping and intersection coincide at six units).
- Task 8: `cohens_d` back to bare `cohens_dz(diffs)` — FAILED
  `test_a_weighted_contrast_entry_carries_the_three_documented_keys` on `cohens_d == 2.0` (got
  1.3416...).
- Task 8: `weighted_cohens_dz`'s denominator changed to bare `total` — FAILED both
  `test_a_weighted_dz_standardizes_by_the_weighted_standard_deviation` and
  `test_a_weighted_dz_at_equal_weights_is_the_unweighted_one`, matching the brief.
- Confirmed structurally unreachable, not tested: `weighted_cohens_dz`'s `denominator <= 0` branch —
  `weighted_cohens_dz([1.0, 2.0], [1, 0])` raises `ContractError`/`E-DATA-WEIGHT-INVALID` inside
  `checked_weights` before the denominator is ever computed, so no fixture can reach that line.

**Disagreements between the briefs and the code, found and resolved:**

1. **Task 6's own regression pin went stale the moment task 7 landed, and the task 7 brief never says
   so.** `test_the_three_comparison_functions_accept_weights_and_strata` (written in task 6) asserted
   `threaded[1]["s"]["m"]["delta"] == pytest.approx(6.0)` with `resample_columns=False`, i.e. "a weight
   passed today must not move a number, since nothing reads it yet." Task 7's prescribed `delta`
   formula — `mean_of(diffs) if col_weights is None else weighted_mean_of(diffs, col_weights)` — is
   **unconditional on `resample_columns`**, matching the per-condition rule that a weighted column mean
   doesn't wait on a declared `resample`. So after task 7, that same call now legitimately returns 8.0,
   and the task-6 test fails. I updated the test's assertion to `pytest.approx(8.0)` and rewrote its
   docstring to record the amendment explicitly (replacing the stale claim rather than layering a note
   over it, per `CLAUDE.md`'s "prefer deleting a claim to rewriting it"). Neither brief flagged this
   interaction.

2. **Task 8's own prescribed test for the derived-branch record keys omits the keyword its assertion
   needs.** `test_a_weighted_derived_contrast_carries_the_record_keys_without_a_weighted_method`, as
   written in the brief, calls `_comparison_step_blocks` directly with `weights=_W_WEIGHTS` but **no
   `weighted_by=`** — yet asserts `entry["weighted_by"] == "sampling_weight"`. Since `weighted_by` is a
   defaulted, independently-threaded keyword (by design — `_comparison_step_blocks` has no way to
   derive the attribute name from the mapping alone), the call as literally specified returns
   `weighted_by: None` and the assertion fails. Verified empirically: reverting my fix reproduces
   `AssertionError: assert None == 'sampling_weight'`. Fixed by adding `weighted_by="sampling_weight"`
   to the call, matching how every other fixture in this file that declares weights also declares the
   attribute name.

**Other notes:**
- Ruff's `B009` flagged the brief's own `getattr(table, "m")` in the derived-closure test fixture
  (task 7); fixed to `table.m` via `ruff check --fix`, no behavioral change.
- `_weighted_contrast_block`'s two-line `weighted_by` `setdefault` (prescribed in task 8) was inserted
  in task 8's commit, not task 6's, per the brief's explicit "insert ... in this step."
- `E-DATA-WEIGHT-CONTRAST` is untouched and still fires; all new tests call the three comparison
  functions directly, never through `run`, per the brief's own note that task 12 (end-to-end) is
  blocked on task 13 (refusal retirement).

## Fix round 1

Review at `.superpowers/sdd/2026-08-17-weighted-contrasts/task-6-8-review.md` (`dbc0830`). Spec
compliance passed; four Majors and six Minors on quality, none a wrong answer in shipped arithmetic.
All ten closed. Every mutation below reverted by editing the file back (never `git checkout --`),
`__pycache__` cleared between runs, reverts verified by re-running — the full suite, not a `-k`
filter, for every mutation the review itself ran against the full suite.

**Major 1 — `_compute_declared_contrasts`'s `weights` threading was unpinned.** The test whose name
claimed all three signatures (`test_the_three_comparison_functions_accept_weights_and_strata`)
asserted only `n_paired == 6` on that arm, true under any weighting. Added
`assert out[0]["s"]["m"]["delta"] == pytest.approx(8.0)` beside it.
*Mutation:* `weights=weights,` → `weights=None,` at the `_comparison_step_blocks` call inside
`_compute_declared_contrasts` (`cli.py`, then line 1278) — **FAIL**, `AssertionError: 6.0 == 8.0 ±
8.0e-06` on the new assertion, full suite: 1 failed, 2146 passed. Reverted; full suite back to 2147
passed.

**Major 2 — the "silent, task 13 catches it" excuse for `strata=None` at `command_run`'s two call
sites was wrong.** `E-DATA-WEIGHT-CONTRAST`'s emit (`validate.py:5020`) gates on `weight_by`, not on
`stratify_by`, so an unweighted config declaring `statistics.resample.stratify_by` beside a sweep
validates and runs today — I had inferred "this path does not run" from "a *different* config shape
is refused," the exact substitution `CLAUDE.md` names, and had offered a `-k`-filtered 29-test run as
evidence of silence rather than the full suite. Built
`test_a_declared_stratify_by_reaches_a_contrasts_interval_through_run`: an unweighted,
`weight_by`-free config with a baseline sweep *and* a declared `statistics.contrasts` entry, using a
step (`_COHORT_CONTRAST_STEP`) whose per-unit spearman-minus-pearson difference is a deterministic
0.0 for cohort `a` and 5.0 for cohort `b` — so a stratified draw is a fixed 50/50 mix every time and
an unstratified one is not, giving a measurably narrower interval at both call sites in one run.
*Mutations, each against the full, unfiltered suite:*
- `_compute_vs_baseline`'s `strata=resample_strata,` → `strata=None,` — **FAIL**,
  `assert 1.6249999999999998 < 1.6249999999999998` on the `vs_baseline` width assertion; full suite 1
  failed, 2146 passed. Reverted; full suite back to 2147.
- `_compute_declared_contrasts`'s `strata=resample_strata,` → `strata=None,` — **FAIL**, the same
  equal-width assertion on the declared-contrast width; full suite 1 failed, 2146 passed. Reverted;
  full suite back to 2147.

Also corrected here rather than by editing the original entries above (the development record is not
retro-edited): the task 6 mutation-table row for this same `strata=None` mutation gave the right
observed outcome (silent) for the wrong reason (task 13's blocker, which does not gate `stratify_by`)
and cited filtered output as if it were evidence of silence. The observation stands; the reasoning in
that row does not.

**Major 3 — `weighted_cohens_dz`'s zero-denominator branch was reachable, and two docstrings claimed
a refusal no assertion made.** My report's `weighted_cohens_dz([1.0, 2.0], [1, 0])` probed one input
and generalized to "structurally unreachable" — a proxy (one candidate) standing in for the real
question (is the branch reachable at all). It is: `Σw − Σw²/Σw` for `[1e17, 1.0]` computes to exactly
`0.0` in floating point (`1e17 + 1.0` and `1e17 - 1e34/1e17` both round to `1e17`), not by concentrating
all weight on one unit (algebraically impossible for two positive weights — `checked_weights` also
refuses a literal zero weight before the denominator is ever reached). Rewrote both docstrings
(`stats.py`'s `weighted_cohens_dz` and the test's) to name the actually-reachable cause, and added
`assert weighted_cohens_dz([1.0, 2.0], [1e17, 1.0]) is None` to
`test_a_weighted_dz_refuses_the_degenerate_shapes_the_unweighted_one_does`, plus a direct assertion
that the computed denominator is exactly `0.0` for that input.
*Mutation:* `if denominator <= 0:` → `if denominator < 0:` in `weighted_cohens_dz` — **FAIL**,
`ZeroDivisionError: float division by zero` inside the test (still a failure, just raised rather than
asserted). Reverted; test green.

**Major 4 — `_comparison_step_blocks`'s docstring still described the pre-task-7/8 column branch.**
"A recorded column takes `paired_t_over_units`... with `cohens_d = cohens_dz(diffs)`... while
`cohens_d` keeps computing from the local `diffs` list regardless" is false under a weight
(`cohens_d` is `weighted_cohens_dz(diffs, col_weights)` there), and the paragraph task 6 added named
what `weights` *is* without ever saying what it *does* to the block. Re-read the whole docstring (not
just the lines task 6 touched) and rewrote: deleted the false `cohens_d = cohens_dz(diffs)` clause
and the "regardless" claim, and replaced the `weights`-is paragraph's missing half with what the
weighted path actually produces — the weighted `delta`, `cohens_d`, `method` spelling, and the two
additional record keys (`weighted_by`, `n_paired_effective`) and the derived/column split those keys
still travel across.

**Minor 5** — deleted the nonexistent `entry_weights` name and the positional "below" locator from
the Kish comment; the sentence is complete without either. **Minor 6** — "The mean of the per-unit
differences" → "The (weighted, when `col_weights` is not `None`) mean...". **Minor 7** — amended the
task-6 test's docstring again to name what it does *not* yet pin: a weighted `delta`/`cohens_d`
beside an unweighted `paired_t_over_units` interval at `resample_columns=False`, owned by task 10,
unreachable through `run` while the refusal stands. **Minor 8** — added
`test_a_weighted_contrast_records_the_declared_attribute_name_not_a_constant`, passing
`weighted_by="cohort_inverse_probability"` (distinct from every other fixture's
`"sampling_weight"`) and asserting it comes back unchanged.
*Mutation:* `metric_block[metric_key]["weighted_by"] = weighted_by` → `= "sampling_weight"` —
**FAIL**, `AssertionError: 'sampling_weight' == 'cohort_inverse_probability'`. Reverted; test green.
**Minor 9** — narrowed `test_a_weighted_stratified_column_contrast_weights_inside_the_strata`'s
docstring: it does not, by itself, separate a correctly-drawn weight vector from the mispairing
mutation the review found (that mutation passed this test; only the payoff test's `ci95[0] >
plain_ci95[0]` comparison catches it) — the docstring now says which two separations the assertions
actually make and names the sibling test that catches the mispairing. **Minor 10** — the count is a
report fact, not a code fact; recorded here rather than edited into the original line: the correct
figure throughout was 2139 → 2145, not 2143.

**Full-suite counts:** 2145 → 2147 passed (1 skipped, 2 xfailed) — two new tests
(`test_a_declared_stratify_by_reaches_a_contrasts_interval_through_run`,
`test_a_weighted_contrast_records_the_declared_attribute_name_not_a_constant`); every other finding
closed inside an existing test. `uv run ruff check .`, `uv run ruff format --check .` (80 files), and
`uv run mypy` (45 source files) clean; `uv run pytest` run in the foreground throughout, including
every mutation's full-suite run.
