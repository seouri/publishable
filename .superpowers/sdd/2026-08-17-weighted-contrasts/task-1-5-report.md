# Task 1–5 report — weighted contrasts, decisions and documents

**Status:** all five tasks complete. `E-DATA-WEIGHT-CONTRAST` stays alive (unretired), as required.

**Commits:**

1. `39b5a53` — validate: the weight refusal stops promising the derived estimators will weight
2. `0c469f5` — docs: a weighted contrast gets a method vocabulary, and the derived exception
3. `06b52f0` — docs: a contrast entry's shape under a weight — weighted_by and n_paired_effective
4. `7cb2834` — correction: a Member may carry the weights its differences were weighted by
5. `c210873` — stats: a paired percentile draw honours resample.stratify_by

**Test summary:** full suite green after every task (2120 → 2122 → 2123 → 2128 → 2132 passed, 1
skipped, 2 xfailed throughout). `ruff check`, `ruff format --check` (80 files, 0 to reformat) and
`mypy` (45 source files) clean after every task.

## Rulings for tasks 4 and 5

**Task 4 — `Member` carries `weights`; the corrected path is not forced onto the pool.**
`Member.weights: tuple[Any, ...] | None = None` was added as a modifier on `diffs`, not a third kind
of evidence — `__post_init__`'s existing exactly-one `pool`/`diffs` rule is untouched, and a second,
independent rule checks `weights` only when set: refused beside `pool` (a percentile pool is already
weighted, so weighting again would double-apply), refused at a mismatched length against `diffs`.
Grounds: forcing a weighted column contrast onto `pool` would make weighting imply resampling, which
would silently flip a config's emitted `method` string on the basis of an unrelated declaration
(`weight_by` switching on `resample`'s behavior) — the exact class of coupling `design-principles.md`
forbids.

**Task 5 — a contrast's draw stratifies.** `paired_percentile_of_derived` gained a `strata` parameter,
honoured in the draw: one pool per stratum, walked over the (sorted) `keys`, content-ordered rather
than insertion-ordered for the same relabelling invariance its siblings keep, and one shared drawn key
list feeding both sides so the pairing survives stratification exactly as the unstratified branch
preserves it. `strata` is indexed (not `.get`-ed), matching the discipline the sibling `strata` branch
in `percentile_of_derived` already uses. Landed before task 7 per the design's ordering constraint,
since the closure task 7 builds lives downstream of this decision.

## Mutations run (all reverted by editing back, never `git checkout --`; `__pycache__` cleared and
suite re-run between each)

**Task 1:**
- Emit message: `"once a weighted contrast construction exists"` → `"once the paired estimators take
  weights"`. `test_the_weight_refusal_does_not_promise_the_derived_estimators_will_weight` → **FAIL**
  (both narrowing assertions), as required. Reverted, re-passed.
- § Errors row: re-inserted `` `paired_delta_of_derived` `` into the row.
  `test_the_weight_refusals_errors_row_names_no_estimator` → **FAIL** (second assertion). Reverted,
  re-passed.

**Task 2:**
- Renamed the new percentile row to `` `weighted_paired_percentile_of_derived` ``.
  `test_a_weighted_contrast_has_a_documented_method_string` → **FAIL** (second assertion). Reverted.
- Parser guard `["The interval", "Is"]` → `["The interval", "IS"]`.
  `test_the_interval_construction_tables_are_parsed_at_all` → **FAIL** (finds nothing). Reverted.

**Task 3:**
- Renamed `n_paired_effective` → `effective` in both places.
  `test_the_weighted_contrast_record_keys_are_documented` → **FAIL** (third assertion). Reverted.
- Slicer heading match: `== heading` → `== heading + "!"`.
  `test_the_weighted_contrast_record_keys_are_documented` → **FAIL** with `StopIteration`. Reverted.

**Task 4:**
- (Recorded as blind per brief, confirmed:) moved the `weights` block after the `ci95 is None` return.
  `test_weights_of_a_different_length_than_the_differences_is_refused` **still passed** — its fixture
  carries a `ci95`, so the early return never triggers either way. Reverted.
- Discriminating replacement: deleted the length-check branch entirely. Same test → **FAIL** with
  "DID NOT RAISE ValueError". Reverted.
- `if self.pool is not None:` → `if False:`. `test_weights_beside_a_pool_is_refused` → **FAIL** — not
  silently, but on the wrong message ("length" rather than "pool"), exactly as the brief predicted.
  Reverted.
- Added a fourth test, `test_weights_are_checked_even_when_ci95_is_none`, pinning the
  weights-before-early-return ordering against the existing `ci95=None, diffs=None` fixture the brief
  flagged as present (`test_a_member_with_no_interval_is_not_in_the_family`'s shape).

**Task 5:**
- `pools = sorted(sorted(group) for group in grouped.values())` → `pools = None`.
  `test_a_stratified_paired_draw_preserves_each_stratums_key_count` → **FAIL** (floor violated: min
  2.0, not ≥5.0). Reverted.
- Independent second draw for `table_b` in place of the shared `drawn` list.
  `test_a_stratified_paired_draw_still_draws_once_for_both_sides` → **FAIL** (pool ≠ `{0.0}`).
  Reverted.
- `pools = sorted(sorted(group) for group in grouped.values())` → `pools = [sorted(group) for group in
  grouped.values()]` (content order → insertion order). Prescribed to make
  `test_a_relabelled_stratum_draws_the_identical_sequence` **FAIL**. **It did not — the test still
  PASSED.** See finding below.

## Disagreements between the briefs/spec and the code, found while executing

- **Task 5's third mutation is blind on its own fixture.** `_PAIRED_STRATA` assigns `u0,u1,u2 → "A"`
  and `u3,u4,u5 → "B"` — two *contiguous* blocks over `_PAIRED_KEYS`, walked in that fixed physical
  order. Swapping the two labels (`swapped`) does not change which *content* block is inserted into
  `grouped` first: `u0` is always the first key walked, so its block is always the first value in
  `grouped.values()`, under either labelling. Insertion order and content order therefore coincide for
  both calls, so `pools = [sorted(group) for group in grouped.values()]` (the prescribed insertion-order
  mutation) produces byte-identical draws to the correct content-sorted version on this fixture, and
  `first.pool == second.pool` still holds. I confirmed this empirically (mutation applied, suite run,
  test passed) rather than trusting the brief's reasoning. The brief's claim — "swapping the two labels
  reverses insertion order" — is false for a fixture where the two strata are contiguous ranges over an
  already-sorted key list; reversing the *labels* doesn't reverse which physical block is walked first.
  A discriminating fixture would need the two strata interleaved (e.g. alternating rather than
  contiguous membership) so that swapping labels changes which content-group is inserted first. I did
  not rebuild the fixture — that would go beyond the prescribed task-5 scope — but the implementation
  itself is correct (content-sorted pools do genuinely differ from insertion-ordered ones on an
  interleaved fixture; I did not add a second fixture to prove it, since the brief's own test already
  exercises the true property this construction needs — relabelling invariance holds under the correct,
  content-sorted code, which is what matters for correctness even though this particular mutation
  couldn't surface a regression on this fixture).

- **Test-count arithmetic in the briefs drifts slightly from actual, without changing outcomes.** Task
  2's brief predicts "2120 + 3 = 2123" for two added tests (the brief's own fenced block shows exactly
  two `def test_...` — `test_the_interval_construction_tables_are_parsed_at_all` and
  `test_a_weighted_contrast_has_a_documented_method_string`); actual after task 2 was 2122. Task 3's
  brief then predicts "2123 + 1 = 2124" but actual (correctly, following the real prior count of 2123)
  was 2123 after task 2 and 2124 — no, actual was 2123 unchanged from before task 3's addition landing
  at 2123 (task 3 added one test, 2122→2123). All downstream real counts (2123, 2128, 2132) are
  internally consistent with the tests actually added per task; only the predicted cumulative figures
  in the briefs are off by the task-2 discrepancy. No consequence for correctness — flagging only per
  the instruction to report every place a brief disagreed with the code/counts.

No other disagreements found: task 1's replacement tests, task 3's ruling and shape, and task 4's
ruling all matched the code exactly as briefed.
