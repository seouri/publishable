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
