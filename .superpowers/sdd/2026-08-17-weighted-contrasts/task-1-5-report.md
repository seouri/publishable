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

## Fix round 1

Review at `.superpowers/sdd/2026-08-17-weighted-contrasts/task-1-5-review.md`, read in full. All three
Majors closed; all six named Minors closed (4, 6, 7, 8, 9) or superseded by the reviewer's own ruling
(Minor 5, folded into Major 3's fix; Minor 4 dismissed by the coordinator's ruling — see below).

**Major 1 — `docs/reference.md`'s contrast construction table, stale prose around six rows.**
- `reference.md:2424`: "Which of the four below applies follows from two facts" → "Which row below
  applies follows from whether the contrast is `paired`, whether the metric is a column or a derived
  one, and whether `weight_by` is declared" — no count, a third fact named, self-maintaining against
  future rows.
- `reference.md:2445` (the `_clustered` rule): narrowed "each takes a `_clustered` suffix" → "each of
  the **unweighted** forms above takes a `_clustered` suffix", resolving the direct contradiction with
  the paragraph ten lines above it that says the suffix does not compose with either weighted form.
- Moved task 2's new paragraph ("A weighted contrast weights a recorded column...") to *after* the
  `_clustered` rule paragraph, as task 2's brief originally specified — the exception now reads after
  the rule it excepts.
- `reference.md:514`, the `E-DATA-CLUSTER-CONTRAST` § Errors row: same narrowing, "gives each
  **unweighted** contrast construction a `_clustered` suffix ... none of those exists in this build" —
  dropped the stale "five" count rather than updating it to a new number, per the coordinator's
  instruction to prefer a self-maintaining sentence.
- Verified by: re-reading the full section after the edit (not the diff), confirming the `_clustered`
  paragraph and the weighted-exception paragraph no longer both make a claim about "each"/"either" that
  contradicts the other; anchor resolution and table-cell-count checks re-run over the touched region;
  full suite green.

**Major 2 — `tests/test_validate.py:7277`, the stale "until the paired estimators weight" comment.**
Swept `README.md`, `docs/*.md`, `src/`, `tests/` for `"paired estimators"` (the reviewer's exact grep).
Closed the one instance in scope (the section comment above the weighted-contrast tests, now reading
"...refused under its own code until a weighted contrast construction exists"). Left untouched, on
purpose: `docs/feasibility-llm-growth-studies.md:515,963`, which also carry the phrase — this is a
feasibility analysis, not one of the four documents, and it is a dated claim about what the refusal
said of itself at the time it was measured; retro-editing a feasibility analysis's dated claims is the
practice `CLAUDE.md` reserves for the four documents' cross-document pass, and applying it here would
destroy the evidence of what was true when the analysis was written. Flagged rather than fixed. The two
other `src/publishable/validate.py` hits (`validate.py:4705,5087,5154`, "unpaired estimators" /
"paired and unpaired estimators take clusters") are unrelated refusals (`E-DATA-ALLOCATION-CONTRAST`,
the cluster-contrast family) and were not touched.

**Major 3 — `test_a_relabelled_stratum_draws_the_identical_sequence` pinned nothing; rebuilt on the
reviewer's discriminating fixture.**
- Replaced `_PAIRED_STRATA` (equal-sized, constant-offset) with a new fixture, `_UNEQUAL_OF` /
  `_UNEQUAL_STRATA` — strata of size 2 and 4, values 1,2 against 3,4,100,200 — matching the reviewer's
  construction exactly.
- Re-verified both outcomes myself before writing the new test: applied the reviewer's label-order
  mutation (`pools = [sorted(group) for _lab, group in sorted(grouped.items())]`) against the new
  fixture via a standalone script — pools differed (`False` on equality) — then against the shipped
  `sorted(sorted(group) for group in grouped.values())` — pools agreed (`True`). Then applied the same
  mutation to `src/publishable/stats.py` directly and ran the rewritten test: **FAILED** (index-1
  values 2.667 vs 2.833). Reverted by editing the file back, `__pycache__` cleared, re-ran: **PASSED**.
- Rewrote the test's docstring to state the actual property (label order alone, not "insertion order
  and label order — two orderings") and to record why the old fixture couldn't see it (constant offset
  between strata makes every drawn difference shift by the same amount regardless of pool order).
- Did **not** keep or re-test the content-order-vs-insertion-order mutation against this or any fixture
  — see Minor 4/5 below for why, and Minor 5 for what was built instead.

**Minor 4 — ruled by the coordinator: the report's remediation claim was wrong, and the proposed fix
(an interleaved fixture) is impossible, not merely unbuilt.** Not rebuilt, per the ruling. The report's
"Disagreements" section above (task 5 entry) is superseded by this fix-round section rather than
rewritten in place, per `CLAUDE.md`'s "prefer deleting a claim to rewriting it" — the original entry is
left as a record of what was believed at the time and corrected here, the way the repo corrects a
published claim by appending rather than editing.

**Minor 5 — the sorted-`keys` contract is now enforced at the function, not left an unstated
divergence from `percentile_of_derived`.** Added a guard in `paired_percentile_of_derived`: when
`strata` is given and `keys != sorted(keys)`, raises `ValueError` naming the precondition, rather than
silently sorting (which would mask a caller bug) or leaving the divergence undocumented. Extended the
docstring and the inline comment to state the contract and why the relabelling invariance depends on
it. Added `test_an_unsorted_key_list_with_strata_is_a_core_defect`, which passes an out-of-order `keys`
list with `strata` and asserts `ValueError` is raised, matching "sorted" in the message. Verified: ran
with the guard in place (passes), and confirmed by reading that every current production call site
(`paired_keys` returns `sorted(...)`; the column path's `col_keys` is an order-preserving filter of it)
already satisfies the new precondition, so nothing downstream needed to change.

**Minor 6 — `Member`'s class docstring extended.** Added a paragraph after the `pool`/`diffs` paragraph
naming `weights` as a modifier on `diffs`, travelling alongside it and never alongside `pool`, `None`
by default. Left the field's type (`tuple[Any, ...]`) as briefed — the reviewer's own note says this is
"a note for task 9," not a defect in tasks 1–5.

**Minor 7 — `_section_text`'s control in `test_the_weighted_contrast_record_keys_are_documented` made
discriminating.** Replaced `assert "n_paired" in section` (implied by the very next assertion, since
`n_paired` is a substring of `n_paired_effective`) with two independent checks: `section.startswith(...)`
against the exact heading text, and `"Reporting strata" not in section` — the next `####`-level sibling
heading, ruling out "the slicer ran to end of file." Verified the new control is genuinely
discriminating by mutating `_section_text`'s depth comparison (`<=` → `<`, which makes it skip past the
Contrasts section's own closing boundary and run into `#### Reporting strata`): the test **FAILED** on
the new `"Reporting strata" not in section` assertion. Reverted, re-ran: passed. The `StopIteration`
mutation from the original submission (`heading` → `heading + "!"`) was re-run and still **FAILS** as
before.

**Minor 8 — the reused `id: sensitivity` in `reference.md`'s new YAML block renamed.** `id:
arm_sensitivity`, distinguishing it from the pre-existing `sensitivity`/`sensitivity_f` examples keyed
on `shift=abnormal`/`shift=normal`. Grepped `tests/` and `docs/*.md` for `id: sensitivity` and
`02_arm=abnormal` first to confirm nothing depended on the old string; nothing did.

**Minor 9 — the stale `H4b` owner in `spec-defects.md`'s pre-existing "contrast path discloses
nothing..." entry (line ~5544) re-owned.** Findings 1 and 3 (general contrast-disclosure gaps) and
Finding 2 (the zero-width sweep `paired_percentile_of_derived` still lacks) now name **H4b-2** as
owner, with Finding 2's paragraph cross-referencing the new `OPEN` entry task 5 added just below it in
the same file, which names H4b-2 for the identical reason. Did not split the three findings across
H4b-1/H4b-2 — none of the three is a weights-specific gap, so H4b-2 (the nearer of the two contrast-
family slices) takes all three rather than inventing a third owner.

**Verification for the whole round:** full suite run in the foreground after all fixes — **2133
passed, 1 skipped, 2 xfailed** (2132 + the one new `test_an_unsorted_key_list_with_strata_is_a_core_defect`).
`ruff check .`, `ruff format --check .` (80 files, 0 to reformat), and `mypy` (45 source files) all
clean. `E-DATA-WEIGHT-CONTRAST` still alive — untouched by this round, confirmed by re-running
`tests/test_validate.py::test_a_weighted_declared_contrast_is_refused` and the two task-1 tests.

**Findings not closed, with reason:** none. All nine (three Major, six Minor) were addressed as
described above; Minor 4 was closed by accepting the coordinator's ruling rather than by building
anything.
