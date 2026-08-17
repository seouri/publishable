# Tasks 9-12 report

**Status:** all four implemented, tested, mutated, and committed.

**Commits:**
- `854f0ef` — correction: a weighted raw interval gets a weighted corrected counterpart (task 9)
- `753fb19` — cli: a weighted column contrast with no resample takes the weighted paired t (task 10)
- `982b9b8` — docs: the sibling refusal rows state their own reading, and weights reach both sides (task 11)
- `95723dc` — cli: the three shortcut shapes publish a weighted, stratified contrast (task 12)

**Tests:** 2147 baseline → 2152 (task 9) → 2154 (task 10) → 2159 (tasks 11+12, 2 + 3 tests) passed,
1 skipped, 2 xfailed throughout. `uv run ruff check .`, `uv run ruff format --check .` (80 files), and
`uv run mypy` (45 source files) clean after each task. `uv run pytest` run in the foreground every
time, including every mutation's full-suite run.

**Mutations run (all reverted by editing back, verified by re-run against the full suite):**

- Task 9: `_corrected_bounds`' weighted/unweighted conditional → bare `paired_t_over_units(...)` —
  **FAIL** on `test_a_corrected_bound_over_weighted_differences_is_weighted_too`'s weighted-centre
  assertion (both members centred on 6.0 instead of 8.0/6.0), full suite 1 failed / 2151 passed.
- Task 9: `weighted_paired_t_over_units`'s delegation → `t_over_units(diffs, confidence)` — **FAIL** on
  `test_a_weighted_paired_t_is_the_weighted_construction_under_a_paired_name`'s weighted-centre
  assertion, plus a bonus catch on `test_a_weighted_paired_t_returns_none_when_kish_falls_below_two`
  (returned an `Interval` instead of `None`).
- Task 9: returned `method` → `"paired_t_over_units"` — **FAIL** on the same test's `method` assertion.
- Task 10: `else:` branch → bare `paired_t_over_units(diffs)` — **FAIL** on
  `test_a_weighted_column_contrast_with_no_resample_takes_the_weighted_t`'s `method` assertion.
- Task 10: `Member(weights=...)` → `weights=None` unconditionally — **FAIL** on the same test's
  `members[0].weights == (1, 1, 1, 3, 3, 3)`.
- Task 10: pool guard removed (`weights=(None if col_weights is None else tuple(col_weights))`) —
  **FAIL**, but as a `ValueError` raised inside `Member.__post_init__` during construction
  (`test_a_resampled_column_contrasts_member_carries_no_weights` errors rather than asserting), exactly
  as the brief said task 4's rule would produce.
- Task 11: re-inserted `` `E-DATA-WEIGHT-CONTRAST` `` into `E-DATA-CLUSTER-CONTRAST`'s row — **FAIL**
  on `test_the_sibling_refusal_rows_state_their_own_reading`'s last assertion, both control assertions
  still green.
- Task 11: deleted "the same weights reach both sides" from § Weighted samples — **FAIL** on
  `test_weighted_samples_says_what_core_does_with_a_contrasts_weights`'s third assertion, control and
  absence assertions both still green.
- Task 12: derived branch's `strata=strata` → `strata=None` — **FAIL** on
  `test_the_c1_shape_publishes_a_weighted_stratified_vs_baseline_delta`'s `derived["ci95"][0] >= 5.0 -
  1e-9` (got 3.0).
- Task 12: `by`-exclusion removed (`sorted(set(of_summary) & set(against_summary))`) — **FAIL** on
  `test_a_weighted_report_by_level_mints_no_member_and_no_delta`'s set-equality assertion (`by` leaked
  in as a third "metric").
- Task 12: `command_run`'s two `weighted_by=weight_by if weights else None` → `weighted_by=None` —
  run against the **full, unfiltered** suite: **2159 passed, 0 failed**, confirming the brief's own
  claim that this path is unreachable by any test in tasks 9-12 and is task 13's mutation to catch,
  through `run`. Reverted; full suite back to 2159.

Every revert was by editing the file back, never `git checkout --`, `__pycache__` cleared between
runs, and every revert verified by re-running (not by `git status`).

**Disagreements between the briefs and the code:** none found this batch. All four tasks' prescribed
diffs applied cleanly against the state tasks 1-8 left, and every prescribed test passed on arrival or
failed exactly as predicted. The one adjustment made was mechanical, not a disagreement: ruff's `B009`
flagged the task-12 brief's own `getattr(table, "prob")` in `_c_shape_common`'s derived closure (the
same shape task 6-8's report already noted for `getattr(table, "m")`); fixed to `table.prob`, no
behavioral change.

**Other notes:**
- `E-DATA-WEIGHT-CONTRAST` is untouched and still fires; every test in this batch that could reach
  `validate` at all (task 11's two doc tests) asserts about the document rather than about `validate`,
  and neither test touches `validate` — task 12's four new tests call `_compute_vs_baseline` /
  `_compute_declared_contrasts` directly, per the plan's correction that `command_run` cannot reach a
  weighted contrast until task 13 retires the refusal.
- Task 9 built `weighted_paired_t_over_units` in `stats.py` and wired it into `correction._corrected_bounds`
  as its first caller, per the plan's correction 2 (inverting the spec's task 9/10 ordering). Task 10
  then wired the same function into `_comparison_step_blocks`' `else:` branch (the raw interval) and
  bound `col_weights = None` once before the derived/column split so the name is never reached unbound
  regardless of how `corrected_from_pool`'s short-circuit is later refactored.
- Task 11 left the § Validation row (*Weighted deltas aren't computed*) untouched, per the plan's
  correction 3 — that row moves to task 13 alongside the emit site it describes.
- Task 12's three C-shape tests all passed on arrival, which the brief states is the correct outcome
  for an integration task; the mutations in step 4 are what establish they can fail.

**Concerns:** none. `E-DATA-WEIGHT-CONTRAST`'s retirement, the § Validation row move, and the
`weighted_by=None` gap through `run` all remain task 13's, untouched here.
