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

## Fix round 1

Review at `.superpowers/sdd/2026-08-17-weighted-contrasts/task-9-12-review.md`. Spec compliance
passed; four Majors and five Minors on quality, none a wrong answer in shipped arithmetic. All four
Majors closed; the Minors that asked for a code or test change are closed, the two that were purely
informational (m4's brief-pointer note, m5's owned-by-task-14 note) required no edit here. Every
mutation reverted by editing the file back (never `git checkout --`), `__pycache__` cleared between
runs, reverts verified by re-running the full, unfiltered suite in the foreground.

**Major 1 — the weighted corrected bound's α was threaded but unpinned.**
`test_a_corrected_bound_over_weighted_differences_is_weighted_too` (`test_correction.py`) ran only at
family size 1, where `1.0 - level` is `0.95` — the same default `weighted_paired_t_over_units` falls
back to even with the keyword dropped, so the test could not tell a threaded α from a silently
defaulted one. Added a second check inside the same test at family size 2 (bonferroni, so
`confidence=0.975`, a value nothing defaults to), asserting the exact bound the reviewer probed:
`[1.4426305905416408, 14.55736940945836]`.
*Mutation:* `correction.py:213`, `weighted_paired_t_over_units(member.diffs, member.weights,
confidence=1.0 - level)` → `weighted_paired_t_over_units(member.diffs, member.weights)` (dropping the
now-pinned keyword, matching the reviewer's own mutation) — **FAIL**, full unfiltered suite: `assert
2.8239563251976074 == 1.4426305905416408 ± 1.4e-06`, 1 failed, 2159 passed. Reverted; full suite back
to 2160 passed, 1 skipped, 2 xfailed.

**Major 2 — `_corrected_bounds`' docstring (`correction.py:186-189`) still said the `diffs` branch
re-runs `paired_t_over_units`, contradicted by the comment four lines below it.** Rewrote the sentence
to name both constructions and the field that decides between them: *"A member carrying per-unit
differences re-runs `paired_t_over_units` over them, or `weighted_paired_t_over_units` when the member
also carries `weights` — exact at any α either way."*

**Major 3 — `_comparison_step_blocks`' docstring (`cli.py:815-818`) described the `else:` branch as it
was before task 10.** Re-read the whole docstring, not just the sentence named. Rewrote: *"A recorded
column takes `paired_t_over_units` over the per-unit differences — `weighted_paired_t_over_units`
instead, under a declared weight — unless `resample_columns` is set **and the pairing has at least two
units**, when it instead takes `paired_percentile_of_derived` over its own column mean (weighted
inside the closure when a weight is declared), the same construction a derived metric uses."*

**Major 4 — task 11 fixed one end of a two-ended check.** `reference.md:309`, § Validation's
*Allocation deltas aren't computed* row, still cited *Weighted deltas aren't computed* by name — the
identical dangling citation task 11 removed from its § Errors twin in the same commit. Removed the
citation, keeping *Clustered deltas aren't computed*'s (that row is not deleted by task 13). Added
`test_the_validation_rows_own_reading_names_no_row_task_13_deletes` (`test_cli.py`), asserting the row
still names *Clustered deltas aren't computed* and "per comparison" (controls) while no longer naming
*Weighted deltas aren't computed*.
*Mutation:* re-inserted `and *Weighted deltas aren't computed*` into the row's citation clause —
**FAIL** on the new test's last assertion, both controls still passing. Reverted.

**Minor m1 — narrowed two docstrings that implied `Member.__post_init__` is pinned by the assertion
next to it, when the real pin is `test_weights_beside_a_pool_is_refused` in `test_correction.py`.**
`test_a_resampled_column_contrasts_member_carries_no_weights` and
`test_the_c1_shape_publishes_a_weighted_stratified_vs_baseline_delta`'s comment above `all(m.pool is
not None and m.weights is None for m in members)`: both now state plainly that `weights is None`
follows from `pool is not None` once construction succeeded, and name what each test actually adds (that
`cli` reaches the shape at all on a real call) rather than implying either assertion is an independent
pin on the guard.

**Minor m2 — a stats-test docstring overclaimed.** `test_a_weighted_paired_t_is_the_weighted_
construction_under_a_paired_name` (`test_stats.py`) said its final assertion was "pinned as the
half-width ratio," but the assertion is `!=`, an inequality that passes under nearly any wrong df.
Corrected the docstring to say so and to name where the df itself is actually pinned:
`test_the_weighted_interval_is_the_t_interval_at_kishs_effective_size` and this file's own
equal-weights oracle.

**Minor m3 — two arithmetic slips in this report, corrected here rather than by editing the original
claims.** The task-12 brief's own docstring says the unstratified derived draw "reaches 4.33 at this
seed and draw count" — measured **3.0** when the mutation was actually run (the mutation is still
sound; the floor it must clear is 5.0 either way, and 3.0 fails it as surely as 4.33 would). Separately,
this report's "Other notes" section says "task 12's four new tests call `_compute_vs_baseline` /
`_compute_declared_contrasts` directly" — there are **three**
(`test_the_c1_shape_publishes_a_weighted_stratified_vs_baseline_delta`,
`test_the_c2_and_c3_shape_publishes_a_weighted_declared_contrast`,
`test_a_weighted_report_by_level_mints_no_member_and_no_delta`), matching the "2 + 3 tests" this same
report states correctly two paragraphs earlier.

**Minor m4 — the `weighted_by=None` deferral is legitimate; this report's pointer was wrong.** The
reviewer independently verified the deferral is structurally sound (checked the emit's gating, the
`weights`-gated expression, and that `command_run` is the only executor). The correction is only to the
citation: task 13's brief prescribes `weights=weights` → `weights=None` at step 5, not
`weighted_by=None`; its test does assert `entry["weighted_by"] == "sampling_weight"`
(`task-13-brief.md:138`), so the mutation is in fact caught, by a route this report's original text did
not name. No code change; recorded so task 13 names it explicitly.

**Minor m5 — recorded, not acted on here.** `reference.md:524` and the `E-DATA-WEIGHT-CONTRAST`
message both still say "no contrast construction in this build weights at all," false as of `753fb19`.
Task 14's sweep claim 1 already names this exact sentence, so it is owned there — no action in this
round.

**Full-suite counts:** 2160 → 2160 passed (1 skipped, 2 xfailed) — one new assertion inside an existing
test (M1) and one new test (M4); every other finding closed by editing an existing docstring or comment.
`uv run ruff check .`, `uv run ruff format --check .` (80 files), and `uv run mypy` (45 source files)
clean; `uv run pytest` run in the foreground throughout, including every mutation's full-suite run.
