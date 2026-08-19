# Batch 3 report — tasks 12, 13, 14, 15a, 15b

**Note on this file's own premise:** the brief said "your predecessor's task 11 record is already
there," but no `task-b3-report.md` existed on disk before this run — task 11's record lives in
`progress.md` (the ledger), not here. Reporting the disagreement rather than assuming; this file is
created fresh and covers tasks 12–15b only.

## Status

All five tasks complete, each committed separately, all four gates clean after every commit
(`ruff check`, `ruff format --check`, `mypy`, `pytest`).

## Commits

- `691773a` — H4d task 12: `permutation_of_derived`
- `de0dcd7` — H4d task 13: `permutation_over_units_clustered` (both draw levels)
- `3b5230e` — H4d task 14: `permutation_over_contrast`, delegating to `permutation_over_units`
- `5c1a297` — H4d task 15a: `percentile_of_derived_clustered`
- `4ea6f97` — H4d task 15b: `E-DATA-CLUSTER-DERIVED` retired, and every claim describing it

## Test summary

Starting point: 2306 passed, 1 skipped, 2 xfailed (task 11, `0a69c8b`).

| After | Passed | Delta | Brief said |
|---|---|---|---|
| Task 12 | 2311 | +5 | +4 (a fixture defect added a 5th test — see below) |
| Task 13 | 2315 | +4 | +4 |
| Task 14 | 2318 | +3 | +3 |
| Task 15a | 2321 | +3 | +3 |
| Task 15b | 2321 | +0 (conversions, not additions) | matches brief's own framing |

Final: **2321 passed, 1 skipped, 2 xfailed.**

## Ruling for task 12: `compute(table, labels)`

Built exactly as the spec's § Corrections against the code, correction 1, and the batch brief
specify. Verified independently rather than trusted: ran the demonstration script from the brief
(a closure reading the label off the row rather than the `labels` argument) and got `(None, 200)`
— confirming a one-argument `compute` built on `percentile_of_derived`'s shape would report no
p-value ever, because `cli._attributed` erases a relabelling written into the table before
`aggregate` sees it. The two-argument signature is the only construction that lets a permutation of
a derived metric mean anything. Ground: the probe result, not the spec's say-so — I re-ran it myself
before writing `permutation_of_derived`.

## Ruling for task 15b: what protects the collision-under-cluster property now

**Before:** `cli._comparison_step_blocks`'s derived-paired branch was gated on `clusters is None`,
so a derived key colliding with a recorded column — whose closures survive the collision retry
uncleared — could never reach an UNCLUSTERED interval under a declared cluster, because the whole
branch was closed to any clustered run.

**After:** the guard is gone, but the collision-under-cluster property (published values must not
read as though independent when the design is clustered) is now protected by construction rather
than by a suppression: `paired_percentile_of_derived` is handed the same `clusters` mapping the
recorded-column arm already draws through, and the `method` string is chosen from the same
`clusters is not None` test used to build the call. There is no path left where `clusters` is
declared and the derived branch's interval comes back unclustered — the branch either takes the
`_clustered` construction or (when `compute_of`/`compute_against` are `None`, or the comparison is
unpaired) publishes nothing at all. Verified end to end: `test_a_derived_key_collision_under_a_cluster_end_to_end`
now asserts `method: paired_percentile_over_units_clustered` and a real `ci95`, reached through a
genuine `run` with the colliding closures surviving into the contrast exactly as they did when the
bug was found — the difference is what construction they now feed.

## Every disagreement found between a brief/spec and the code

1. **Task 12 fixture, `test_a_derived_permutation_drops_a_degenerate_draw_and_still_reports_its_count`.**
   The brief's fixture raised on "any draw whose `of` arm holds fewer than two units," but a
   permutation null holds the label *multiset* fixed — `rng.shuffle(pool)` only reorders it — so
   the `of` arm's count never varies across draws and the raise could never fire (measured:
   `survivors == 200` for the count-based guard). Replaced with a sum-based condition
   (`sum(of) < 8.0` over six units valued 0–5) that does vary per draw; measured `112/200`
   survivors at the fixture's seed before trusting it.

2. **Task 14 fixture, `test_a_contrast_permutation_is_confined_to_the_cells_of_every_other_group_axis`.**
   The brief's two-cell, four-unit fixture asserted `confined == 1/1000`, but with two 2-unit
   cells there are only `2 × 2 = 4` within-cell relabellings — the observed is the unique max, but
   over a space of 4, not thousands (measured `confined ≈ 0.252`, not `0.001`). The total roster is
   also only 4 units, so even the *free* permutation has only `C(4,2) = 6` arrangements, nowhere
   near the "three orders of magnitude apart" the brief's own docstring predicted (measured
   `free ≈ 0.344`, not the ≈0.5 expected). Replaced by reusing fixture C (task 11/13's own 50-unit,
   10-cluster roster) with its clusters passed as `strata` instead — the identical within-group
   shuffle mechanism — which reproduces the brief's original literal exactly (`confined == 1/1000`
   at `seed=2, n=999`) once the fixture actually has the arrangement space to earn it.

3. **§ Corrections against the code's own claim about task 14's `strata` docstring paragraph.**
   The brief's step 3 said to "extend the docstring by adding a paragraph rather than rewriting
   one," giving a code block that mixed a Python comment with the `groups`-building logic. No such
   paragraph asserting the in-place shuffle is deliberate exists anywhere in `permutation_over_units`
   as shipped by task 11 (`0a69c8b`) — checked by reading the function and by `git show` on the
   commit that introduced it. There was nothing to delete. I added a real docstring paragraph (prose,
   inside the triple-quote) and, separately, the code comment the brief's block actually contained,
   in the function body above the `groups` construction — treating the brief's block as describing
   two different edits rather than one.

4. **`validate.py`'s two stale comments** (flagged by the predecessor's ledger entry as outside
   task 15b's stated file list, and confirmed still live): one at `_check_units`'s cluster-by
   documentation claiming a derived metric under `cluster_by` "may not yet" resample, one at the
   weight+cluster contrast guard citing `E-DATA-CLUSTER-DERIVED` as precedent for "a construction
   that does not exist." Both edited to state the current fact (derived-under-cluster now resamples
   through `percentile_of_derived_clustered`; the weight+cluster refusal stands on its own reasoning
   rather than on a retired precedent).

5. **Several `tests/test_cli.py` docstrings and one `tests/test_validate.py` docstring** described
   `E-DATA-CLUSTER-DERIVED` as live, temporary-but-current build state. All updated per task 15b's
   step 2 discipline (convert, don't just delete the pin) — see the commit for the full list:
   `test_a_clustered_derived_metric_is_refused_rather_than_drawn` →
   `test_a_clustered_derived_metric_is_now_resampled_by_the_clustered_construction`;
   `test_a_derived_key_collision_under_a_cluster_end_to_end` converted to assert the computed
   clustered interval rather than the suppressed nulls; `test_a_contained_aggregate_fault_does_not_downgrade_a_declared_column_resample`
   re-triggered through `E-STEP-KEY-COLLISION` (via `aggregate_returns="pred"`, a genuine name
   collision) since its original cluster-refusal trigger no longer fires;
   `test_the_shipped_template_derives_nothing_so_no_generated_project_is_reached` renamed and
   reworded to state what remains true (no generated project's `aggregate` returns anything, clustered
   or not) rather than describe a retired refusal's blast radius.

6. **`docs/reference.md`'s first method table had no row for `percentile_of_derived_clustered`
   at all**, unlike the brief's step 4, which named only a sentence to delete and two citations to
   re-point. This is a genuinely new `method` string this slice mints (distinct from the recorded
   column's `_clustered`-suffix pattern), so I added a row for it — the same obligation H4b-1's
   entry in `CLAUDE.md` names ("the vocabulary was minted in `reference.md` before any code emitted
   it"). Checked the second (contrast) method table separately: `paired_percentile_over_units_clustered`
   needs no new row there, because its general suffix-rule paragraph ("each of the unweighted forms
   above takes a `_clustered` suffix... the percentile forms resample whole clusters") already
   covers it, and the `paired_percentile_over_units` row already says "every derived metric" — so
   that table was already consistent once the construction became reachable.

## Mutations run (all reverted by editing back, all re-verified after revert)

- **Task 12:** (a) `drawn_labels = dict(zip(keys, pool, strict=True))` → `dict(labels)` — FAILS
  `test_a_derived_permutation_relabels_and_recomputes_through_the_labels_argument` (`None` where a
  p-value in (0.3, 0.7) was asserted). (b) `survivors += 1` → `survivors += 0` — FAILS both the
  degenerate-draw test (`0 < survivors` becomes `0 < 0`) and the invariance test's `survivors == 100`.
- **Task 13:** (a) within-cluster branch replaced with `rng.shuffle(drawn_labels)` (free
  relabelling) — FAILS the `1/5001` test (`0.4845` obtained). (b) `if level == "whole_cluster":` →
  `if False:` — FAILS the whole-cluster test on `assert p is not None` (within-cluster permutation
  of that fixture is a no-op, returns `None`). (c) the `±1` mutation is blind here by design (not
  factored into a shared helper — confirmed by grep, three separate spellings of
  `(1 + reached) / (n + 1)` across the file) and named as such per the brief, not applied.
- **Task 14:** (a) `permutation_over_contrast`'s clustered-branch guard → `if False:` — FAILS the
  contrast test (`≈0.49` where `1/5001` was asserted). (b) `permutation_over_units`'s
  `groups = list(by_stratum.values())` → `groups = [list(range(len(values)))]` — FAILS the
  confinement test (stratified answer becomes the free one).
- **Task 15a:** the draw changed to sample `G` units instead of `G` clusters — FAILS the
  width-comparison test (`(clustered.high - clustered.low) > (unit_level.high - unit_level.low)`,
  collapsed to an equality: `34.5 - 25.0 > 34.5 - 25.0`).
- **Task 15b:** the clustered routing reverted to call `percentile_of_derived` unconditionally —
  FAILS both the direct-call test (`test_a_clustered_derived_metric_is_resampled_by_the_clustered_construction`,
  on the `method` assertion) and the end-to-end one
  (`test_a_clustered_derived_metric_is_now_resampled_by_the_clustered_construction`), confirming the
  width/method assertions I added are not blind.

## Concerns

- **Host disk is critically low** (1.2 GiB free at the end of this batch, down from 3.7 GiB at the
  start — measured before/after every full-suite run). This is host-wide pressure, not artifacts
  from this session (`.git` is 176M, the scratchpad is 23M) — worth flagging to whoever runs the
  next batch, since the same ENOSPC risk that interrupted the predecessor is live again.
- **Two test conversions in `test_cli.py`** (`test_a_derived_key_collision_under_a_cluster_end_to_end`
  and its direct-call sibling) reactivate the exact corner the whole-branch review found a Critical
  in. Read both fully before touching either again — the direct-call test's null output is correct
  only on its own narrower premise (no resample closures at all), not because the collision is still
  suppressed.

## Fix round 1 (review at `task-b3-review.md`, commit `33f5753`)

**Own the reasoning error, as asked.** I read `ci95: [0.0, 0.0]` as "a genuine clustered
interval" while writing task 15b's own end-to-end verification. A zero-width interval is the one
value identical under every construction — it verifies nothing about which construction produced
it, the same class as a Welch interval that happens to coincide with a pooled one. My own 15b
mutation exercised a string literal (`method`) rather than the arithmetic, which is exactly why it
could not have caught this. That is the transferable lesson and I take it as such.

### Critical 1 — the `_clustered` label and the clustered draw were decoupled

**Changed:** `cli._comparison_step_blocks`'s derived-paired branch now computes ONE variable,
`base_col_clusters`, and both the `method` ternary and the `clusters=` argument read from it —
previously two independently-written ternaries, each keyed off `clusters is not None` separately,
which is exactly how a one-line edit to either could drift from the other. Same fix applied to the
unpaired recorded-column branch (`unpaired_percentile_of_sides`'s call site), which had the
identical shape (`method` keyed off `clusters`, the two `*_clusters` arguments keyed off it too —
three independent reads of one fact).

**Verified by:** a new end-to-end fixture,
`test_a_derived_key_collision_under_a_cluster_computes_the_clustered_width` (`tests/test_cli.py`),
built from the reviewer's own numbers — `_CLUSTER_CONTRAST_STEP` (non-degenerate `pred`, varying by
site) combined with `aggregate_returns="pred"` so the derived recompute collides with the recorded
column AND varies with which clusters a draw pools. Measured directly before trusting it: clustered
`ci95 == [1.0, 9.0]`, unit-level (clusters argument alone nulled) `ci95 == [4.666…, 8.0]` —
categorically different, unlike the batch's own degenerate `[0.0, 0.0]` fixture. **The
argument-only mutation** — `clusters=base_col_clusters` → `clusters=None`, every `method` ternary
left untouched — now FAILS this test on the `ci95` assertion (`[4.666666666666667, 8.0]` where
`[1.0, 9.0]` was asserted). Reverted by editing the line back; re-ran to confirm PASS. This is the
pin the review asked for, not the string-literal one 15b shipped.

### Major 2 — the zero-width interval and corrected interval, filed

**Changed:** nothing in code (the reviewer confirmed it is not introduced by this batch — the
identical shape reproduces unclustered at `d97ec9c`). Filed a new `spec-defects.md` entry:
*"`paired_percentile_of_derived`'s degenerate-draw refusal is row-content-based, and a
compute-cancellation still publishes a zero-width interval and a zero-width corrected interval"*.
Named the gap precisely (`_drawable_content` checks ROW identity, not the identity of the
COMPUTED VALUES two colliding formulas produce), named why it survived 15b's own citation of it as
verification, and named the owner: unassigned, the next slice touching this function's
degenerate-draw refusal, with the exact check that owner must make (a value-level content check
over the resample pool, run after the draw loop, alongside the existing row-level one).

### Major 3 — `n.clusters` disagreeing with the draw it rests on

**Changed:** `stats.summarize_step`'s derived branch now recomputes `n.clusters` from
`collapsed`'s own keys (`cluster_count_of(clusters, collapsed)`, computed once per step rather than
passed through from `counts` unmodified) — mirroring the recorded-column branch's own discipline,
and making `percentile_of_derived_clustered`'s docstring guarantee ("cannot disagree with the
`n.clusters` a caller prints") true rather than aspirational.

**Verified by:** a new direct-call test,
`test_a_clustered_derived_metrics_n_clusters_matches_the_draw_it_actually_rests_on`
(`tests/test_stats.py`), handing `counts["clusters"] = 4` beside a `collapsed` table spanning only
2 of those 4 clusters — the exact mismatch shape the reviewer probed. **Mutation:** reverted the
fix (dropped the `derived_n["clusters"] = derived_clusters_n` line) — FAILS on `4 == 2`. Reverted
by editing back; re-ran to confirm PASS. As the review noted, I did not construct reachability
through a real `run` (would need a step recording for a proper subset of completed units) — the
direct-call claim is the one verified, and I say so rather than implying the stronger one.

### Major 4 — no zero-width refusal on `percentile_of_derived_clustered`

**Changed:** added the content-based degenerate-draw refusal `percentile_over_units_clustered`
already makes "whether or not `strata` is declared" to `percentile_of_derived_clustered` — checked
unconditionally (not gated on `strata`, matching the clustered family rule rather than
`percentile_of_derived`'s own narrower, strata-only version of the same check). Updated
`reference.md`'s scoping paragraph to name both derived forms alongside the column forms it already
named, rather than leaving `percentile_of_derived`/`percentile_of_derived_clustered` as an
undocumented member of the family the paragraph describes.

**Verified by:** a new test, `test_a_clustered_derived_draw_over_constant_content_reports_no_interval`
(`tests/test_stats.py`) — 20 units of identical content in 4 clusters, `interval is None`.
**Mutation:** the new `if all(...)` block replaced with `if False:` — FAILS
(`Interval(low=5.0, high=5.0, ...)` returned where `None` was asserted). Reverted by editing back;
re-ran to confirm PASS.

### Minor 5 — stale "two callers" count

**Changed:** deleted the count rather than updating it to three, per `CLAUDE.md`'s own rule
against call-site enumerations. `_draw_pools`' docstring now says "a percentile construction's
callers" and states the shared contract without naming how many there are.

### Minor 6 — "an identity" claim on the moved RNG stream

**Changed:** the docstring paragraph (kept; the duplicate inline comment deleted — see Minor 7) now
distinguishes the STRUCTURAL sameness (one group covering every position, same domain as before)
from the RNG-IDENTICAL claim it was wrongly implying, and states the measured before/after values
(`0.48050` → `0.47351` at `seed=7, n=5000`) plainly rather than asserting an identity that isn't
one. Added `test_the_unstratified_permutation_walk_is_pinned_at_a_literal_seed`
(`tests/test_stats.py`) pinning `0.473505298940212` at that seed — the pin the review said was
missing, so the next such refactor is no longer invisible.

### Minor 7 — one claim at two sites

**Changed:** deleted the inline comment duplicate of the docstring paragraph above (`strata`
confinement rationale), rather than maintaining both. One statement of the claim, in the docstring.

### Minor 8 — rewritten rather than deleted, and the two rewrites' own invented claims

The two comments the review names (`stats.summarize_step`'s derived-cluster paragraph,
`cli._comparison_step_blocks`'s suppression comment) were rewritten in the original 15b commit
where the brief said delete, and two of the invented sentences became Findings 1 and 3. Both
paragraphs needed further correction this round regardless, because the CODE they describe changed
today (Critical 1's shared-variable fix, Major 3's `n.clusters` recompute) — so I re-read each in
full rather than patching around the flagged sentence, and found a THIRD stale claim my own
original rewrite had left behind: `stats.summarize_step`'s docstring said "this loop's own
`clusters` only ever reaches the RECORDED-column branches" — false as of today's Major 3 fix, which
makes the derived branch read `clusters` too. Deleted that clause rather than rewriting it again,
and rewrote the surrounding paragraph's factual claim (effective vs. clusters no longer take
identical treatment for a derived metric) to state what is now true, since the underlying code
itself changed and the paragraph must track it. `cli._comparison_step_blocks`'s comment was
re-read in full and found still accurate against today's changes — no edit needed there.

## Fix round 1 — test summary

2321 → **2325 passed, 1 skipped, 2 xfailed.** Four new tests: the Critical 1 end-to-end pin, the
Major 3 direct-call pin, the Major 4 content-refusal pin, and the Minor 6 RNG-stream pin. All four
gates clean (`ruff check`, `ruff format --check`, `mypy`, `pytest`) after the commit.

## Findings not closed

None. All four Majors/Critical and all four Minors from the review are addressed above, each with
a mutation confirming the fix is not blind (except Minor 5/6/7, which are documentation/duplication
fixes with no code behavior to mutate — Minor 6's claim is instead pinned by a literal seed value).
