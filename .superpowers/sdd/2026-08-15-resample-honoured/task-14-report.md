## Task 14 report

**Status:** COMPLETE, including the task-14 review round. Commits `b156b1b` (implementation),
`556d13d` (report), `d61c640` (review fixes) on `h4a-resample-honoured` (base `ce2f2db`).

**Tests:** `uv run pytest` — 1781 passed + 2 xfailed (baseline 1770 + 11 new across both rounds:
4+3 in `test_stats.py`, 2+4 in `test_cli.py`). `uv run mypy` clean (42 files). `uv run ruff check .`
clean. Every required mutation (dropped `weights=` in the unclustered and clustered percentile
calls; `resample_draws` emitted unconditionally; `resample_columns` gated on `n != 2000` and on
`True` unconditionally; the new stratify-warning condition forced off and forced on) applied,
confirmed FAIL against the named test, `__pycache__` cleared, reverted in place, confirmed PASS.
Task 1's acceptance pin (`test_the_undeclared_resample_shape_is_pinned_*`) caught the unconditional-
gate mutation directly; a dedicated test now also catches the narrower `n != 2000` mutation the
review found the pin could not distinguish from `declared`.

**Review round (4 Important, 4 Minor, no Critical) — all closed, see
`task-14-review.md` and `progress.md` for the full account:**
1. The `declared` gate was undiscriminated from `resample_spec["n"] != 2000` — no test declared
   `resample` with exactly the undeclared default `n: 2000`. Closed with
   `test_declaring_n_2000_still_gates_a_column_on_declared_not_on_n`.
2. Clustered *and* weighted (the fourth required combination) was unpinned — dropping `weights=`
   from the clustered percentile call left the suite green. Closed with an exact-`ci95`-match test,
   `test_a_clustered_and_weighted_column_pins_both_together_under_resample`.
3. The finiteness claim in `reference.md`/`stats.py` was unhedged ("finite throughout ... always
   defined") against a ruling that is explicit "conditional on finite inputs" — and this task's own
   wiring makes the counterexample (`nan` reaching `ci95`/`resample_draws` through a real run)
   reachable for the first time. Both hedged to state the condition and disclose the unchecked gap.
4. (Merge gate) The stratify_by option set omitted a run-time warning — the cheap, disclosed-gap
   route this project uses everywhere else. Added `W-STATS-RESAMPLE-STRATIFY-UNHONOURED`, fired once
   per run, registered in `reference.md` § Warnings core reports, with positive and negative tests.
5. Minors: a retry-call comment overclaimed a live behavior change it doesn't have (that call passes
   no `seed` either, so `resample_columns` there is inert today); three positional locators renamed
   to what they name; one of the two untested null-interval reasons (too-few-draws-for-confidence)
   given a test, the third (per-stratum constant-pair) noted as unreachable for a column today.

**Brief/code disagreement found (as flagged):** the brief's own Step 1 test asserted
`resample_draws == 2000` for a one-unit column under a declared resample — an interval that is
`None` (`ci95: null`). `docs/superpowers/spec-defects.md`'s own cited ruling (the entry the brief
quotes as "task 11's ruling") says `resample_draws` must be `null` whenever `ci95` is, for exactly
this reason: recording the requested `n` beside a refused interval asserts survivor evidence for a
draw that never produced one. Implemented per the ruling, not the brief's literal snippet. The test
was rewritten and renamed to `test_a_column_below_two_units_reports_a_null_draw_count_under_resample`,
asserting the key is present (declared, attempted) and `None` (nothing to describe), and a new
spec-defects.md entry records which test was wrong and why. Caught via `advisor()` before writing
any test code, by cross-checking the brief's fourth test against spec-defects.md's own text.

**Strata decision (deliberate, disclosed, not silent):** shipped without threading `stratify_by`
into either the column or the derived resample path. `percentile_of_derived` has no `strata`
parameter; wiring only the column path (the cheaper of the two, since `percentile_over_units`/
`_clustered` already accept `strata`) would put two intervals in one `aggregated` block computed
under different designs, with `method` reading identically either way and nothing else in the
record to disclose which is which — worse than today, where both paths agree by both ignoring the
declaration. A new spec-defects.md entry names the gap and what closing it needs: `strata` in
`percentile_of_derived` first (a real construction, not wiring — the derived draw has no per-unit
value to stratify directly), with column wiring landing alongside it rather than ahead of it.
`cli.py`'s stale forward-promise comments from tasks 12–13 ("task 14 wires stratified column
resampling", "declared is unread until task 14") were rewritten to state what this commit actually
does.

**Documentation landed:** `reference.md` § Statistical reporting gained the column-provenance
paragraph task 11 named as owed — absent when undeclared, `null` when declared but `ci95` is,
otherwise the requested `n` — two-valued against the derived metric's `null`/`0`/*n* three-valued
scheme, stated as a real asymmetry rather than smoothed over. Two `spec-defects.md` entries added
(the `stratify_by`-honoured-nowhere gap; the corrected `resample_draws`-under-a-refused-interval
ruling).

**Concerns / things a reviewer should check:**
- The retry `summarize_step` call (post derived-key-collision) deliberately does not receive
  `resample_columns` — commented at the call site, matching the brief.
- The `cli.py` warning loop (`used == 0` / `used < derived_metric_draws`) now reads a column's
  `resample_draws` too. No production `assert` was added (per review guidance against asserts that
  vanish under `-O`); instead the loop carries a comment explaining why neither branch can fire for
  a column, and `test_a_declared_resample_gives_every_column_a_percentile_interval` pins the absence
  of both warning strings positively (both warning strings are independently proven falsifiable
  elsewhere in the existing suite).
- The "summary-step `Estimate` is unreachable through `summarize_step`" claim (brief line 15, task
  18's job) was **not** independently re-verified with a new fixture in this task — building one
  costs a custom `extra_step_source` and the brief explicitly assigns the assertion to task 18.
  Flagging this rather than silently skipping it, since the dispatch instructions I received also
  raised it as something "this task owes."
- `mypy` needed one added `assert column_weights is not None` in the final `else` branch of the
  interval-selection block — narrowing it can't infer across the two separate `if` statements. This
  is a type-narrowing assert (always true by construction), not a behavior-deciding one.
- `uv run ruff format --check .` reports 62 files (including `stats.py`/`cli.py`) as unformatted;
  confirmed via `git stash` that this predates this task's changes (repo-wide drift, not introduced
  here) and is not part of the required gate table.

**Files touched:** `src/publishable/stats.py`, `src/publishable/cli.py`, `tests/test_stats.py`,
`tests/test_cli.py`, `docs/reference.md`, `docs/superpowers/spec-defects.md`,
`.superpowers/sdd/2026-08-15-resample-honoured/progress.md`,
`.superpowers/sdd/2026-08-15-resample-honoured/task-14-review.md`.
