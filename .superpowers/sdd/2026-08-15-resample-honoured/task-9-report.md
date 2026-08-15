# Task 9 report — the stratified draw

Status: COMPLETE
Commits: f69055a (implementation), 0866fa2 (initial report), 79ae219 (review fixes)

## Test summary

`uv run pytest` 1742 passed + 2 xfailed. `uv run mypy` and `uv run ruff check .` both clean. (Baseline
1732 + 2 xfailed; net +10 tests after the review round: the brief's 6, plus 3 I added for degenerate
shapes, plus 1 net from replacing one weak degenerate test with two — see below.)

## What was built

`percentile_over_units` in `src/publishable/stats.py` gained `strata: Sequence[Any] | None = None`.
When given, values are grouped by stratum before any sort (carrying each value's weight with it via a
single `carried` weight vector shared with the existing weighted path), each stratum's pool is sorted,
the pools are ordered by their own sorted contents (not by label), and each draw pulls exactly as many
indices from each pool as that pool holds. Unstratified callers (`strata=None`, the default) take the
identical code path as before — the existing ~20 `percentile_over_units` tests pass unchanged, and the
task-1 regression pin is untouched.

## Review round — findings and fixes

The coordinator's review confirmed the statistics were correct (checked against an independent
reference implementation, an analytic normal approximation, and 300 randomized cases against the
pre-task-9 commit) but raised three Important findings, all now fixed in commit 79ae219:

1. **Zero-width `ci95` pinned as correct (the spec ❌).** `strata=["a"]*10 + ["b"]*4` over internally
   constant strata returned `Interval(2.142857, 2.142857)` instead of `None`. Fixed by adding a
   structural pre-check: if every stratum's own `(value, weight)` pairs are all identical, no draw can
   ever differ from any other *for whatever constant each stratum holds* — a guarantee independent of
   the specific numbers, not a data coincidence — so the function now returns `None`, mirroring
   `percentile_over_units_clustered`'s refusal at `G < 2` per `reference.md` § Statistical reporting:
   "reporting a point with no interval is honest; a zero-width 95 % interval is not." A single constant
   stratum among others that still vary is unaffected and keeps its interval — that case is data-caused
   and stays settled. `test_more_strata_than_two_units_gives_a_zero_width_interval` (which asserted the
   old, wrong behavior) was replaced by `test_every_unit_its_own_stratum_gives_no_interval_at_all` and a
   new `test_all_strata_internally_constant_gives_no_interval_at_all` using the reviewer's own
   10-and-4 fixture.
2. **Row-order invariance test didn't actually test cross-pool ordering.** The rotate-by-7 fixture left
   first-seen stratum order (low, mid, high) unchanged, so a mutation that pools by insertion order
   instead of by sorted contents survived all ten tests. Changed the rotation to 28 (verified: this
   makes the ordering mutation fail the test — see Mutation testing below).
3. **Two degenerate-shape tests asserted only non-crash.** `test_a_size_one_stratum_...` and
   `test_a_stratum_of_identical_values_...` asserted `low < mean < high`, which holds under a
   pooled-swap mutation too. Both now additionally assert the stratified interval is less than half the
   width of the plain (unstratified) draw at the same seed — the same discriminating margin the base
   `test_a_stratified_draw_preserves_each_stratum_size` uses — which fails under the pooled swap.

Minors also fixed: the weighted-draw test's comment said the weighted centre was "≈ 39.5" when the
correct value is 65.325 (arithmetic: `sum(v·w)/sum(w) = 10452/160 = 65.325`); tightened its loose
`> 20.0` assertion to `> 50.0`. Removed the `float(value)` coercion from the stratified path so it
matches the plain and weighted branches (neither coerces). Renamed the loop variable `pool` to `group`
inside the strata branch so it no longer shares a name with the plain branch's `pool: list[float]`
while holding a different type (`list[tuple[float, float]]`). Deleted the claim (in the now-replaced
test) that a design with degenerate strata would be routed through an `E-STATS-RESAMPLE-*` validation
check — no such check exists or can exist, since stratum sizes are roster-dependent, not
config-dependent.

## Mutation testing (this round)

- Reverted the zero-width guard to a no-op (`if False and all(...)`) — both
  `test_all_strata_internally_constant_gives_no_interval_at_all` and
  `test_every_unit_its_own_stratum_gives_no_interval_at_all` FAILED, reproducing the exact
  `Interval(2.142857142857143, 2.142857142857143)` / `Interval(2.5, 2.5)` the review found. Reverted in
  place, re-ran, PASS.
- Changed `ordered = sorted(sorted(group) for group in pools.values())` to
  `ordered = [sorted(group) for group in pools.values()]` (insertion order) —
  `test_a_stratified_draw_is_invariant_to_row_order` (now rotating by 28) FAILED. Reverted in place,
  re-ran, PASS.
- Forced `strata = None` at function entry (pooled-swap) — both
  `test_a_size_one_stratum_is_drawn_deterministically_every_time` and
  `test_a_stratum_of_identical_values_contributes_no_variance_of_its_own` FAILED on the new width
  assertion. Reverted in place, re-ran, PASS.
`__pycache__` cleared between each mutation and its revert; all reverts were in-place edits, never
`git checkout`.

## Degenerate shapes — decided and tested

- **Misaligned `strata` length**: raises `ValueError` (via `zip(..., strict=True)`). Treated as a
  programming error, not a user error to guard softly — consistent with the existing `weights` contract
  in the same function.
- **Stratum of size 1**: works, contributes its one value deterministically to every draw, and — when
  at least one other stratum still varies — narrows the interval versus the pooled draw.
- **Stratum of all-identical values**: same as above; contributes zero variance of its own, only the
  varying strata widen the interval.
- **Every stratum internally constant (including the all-singleton case)**: returns `None`. This is the
  fix from finding 1, above — no resampling freedom exists anywhere, so there is no honest interval to
  report.

## Concerns / notes for later tasks

- No brief/code disagreement found on the base implementation. The review found real gaps in what my
  tests exercised, not in the arithmetic itself (confirmed independently to ~5e-4 by the reviewer).
- **Slice-level gap, not mine to fix, per the coordinator's routing:** `percentile_of_derived` takes no
  `strata` parameter. Once tasks 13–15 wire `resample.stratify_by` end to end, a declared `stratify_by`
  will stratify column metrics (which go through `percentile_over_units`) but silently NOT derived
  metrics (which go through `percentile_of_derived`) in the same run — two metrics in one table, only
  one of them honoring the declared stratification. This needs a decision at the wiring layer (tasks
  13–15): either give `percentile_of_derived` the same `strata` parameter, or make the wiring refuse/
  warn when a derived metric is asked to stratify.
- Task 14 passes `strata=` through from `summarize_step`/resample resolution, and task 15 builds on top
  of this — both should be able to rely on: unstratified default path is byte-identical to pre-task-9
  behavior; `strata=None` is a true no-op; stratum ordering is by sorted contents, not by first-seen
  order or label; and a stratification that leaves every stratum internally constant returns `None`
  rather than a zero-width interval.
- `docs/superpowers/` progress ledger (`progress.md`) had an uncommitted pre-existing edit (dispatch
  note for task 9) from before this task started; left untouched and uncommitted — not part of this
  task's diff.
