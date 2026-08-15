# Task 10 report — the stratified × clustered composition rule

Status: COMPLETE
Commits: 97c911c (implementation), 3af1e5a (initial report), 2348477 (review fixes)

## Test summary

`uv run pytest` 1752 passed + 2 xfailed; `uv run ruff check .` and `uv run mypy` both clean. (Baseline
1742 + 10 net new across both rounds — see the review section below for the round-2 accounting.)

## What was built

`percentile_over_units_clustered` in `src/publishable/stats.py` gained `strata: Sequence[Any] | None =
None`, implemented per the brief's given code almost verbatim (fixed one typo in my own added docstring
prose — "a public function hand" → "handed"). `validate._check_resample` gained the roster-side check,
reusing `units.stratum_varies_within_cluster` exactly as *Fold strata survive clustering* does.
`docs/reference.md` gained one § Validation row and one row each in § Errors `validate` reports and §
Errors core raises, all citing `#clustered-units` (verified as an existing anchor) and dual-listing
`E-STATS-RESAMPLE-STRATIFY-VARIES` the way `E-DATA-WEIGHT-INVALID` is dual-listed.

## One brief/code disagreement (as flagged — this was one of the seven)

The brief's `test_validate.py` fixtures used `"limits.min_clusters": 2` as a *dotted* override key.
`write_config`'s override mechanism (`tests/test_validate.py:53-63`) walks dotted keys through existing
dict nodes (`node = node[h]`), and `base_config` has no top-level `"limits"` key at all — so the dotted
form raised `KeyError: 'limits'` before validation ever ran. Every existing test that sets
`limits.min_clusters` in this file (e.g. `test_a_clustered_resample_below_min_clusters_warns`) uses the
nested form, `"limits": {"min_clusters": N}`, instead. Fixed both new tests to match that existing
convention; the rule under test (the composition check) is unaffected — this is pure test-scaffolding
syntax.

## A gap the brief's own reasoning didn't survive contact with: the width-ratio mutation test

Step 5 of the brief expects `test_a_clustered_stratified_draw_takes_clusters_within_strata` to FAIL
under the mutation `for _ in range(len(group))` → `for _ in range(1)`, reasoning that "one cluster per
stratum makes every replicate three clusters instead of six." I ran this exact mutation and the test
PASSED. Traced why: the fixture's interval **extremes** are reached whenever a stratum's draw happens to
repeat its own single most-extreme cluster — and pooling several copies of the *same* cluster's units
gives that cluster's own mean regardless of how many copies are pooled. So the endpoint values are
identical whether a stratum draws 1 cluster or its own count of 2; only interior draws differ, and the
"plain" (unstratified) comparator used by the ratio assertion is built from the *same* mutated loop
(`strata=None` also goes through `stratum_pools = [ordered]`), so it degrades in the same direction and
the `< half` inequality survives. I verified this by hand (`plain` width goes from ~100 to unaffected-ish
while `stratified` also changes, but the ratio still holds) rather than trusting the brief's prose.

To actually catch this mutation I added
`test_a_clustered_stratified_draw_spends_one_pick_per_cluster_the_stratum_holds`, which monkeypatches
`random.Random` with a `_CountingRandom` spy and asserts the total `randrange` call count over 2000
draws equals `2000 * 6` (the true total cluster count across all three strata). This is a structural
pin immune to the value-coincidence that defeats the width comparison. I kept the brief's original test
too (it is still a legitimate demonstration of the intended behavior, just not a sufficient mutation
guard on its own).

## The degenerate case — decided and tested (not handed over as literal test code)

The brief's prose said "the clustered-and-stratified path needs its own answer to the degenerate case,
and it should be the same answer" as `percentile_over_units`'s all-identical-strata refusal, but did not
supply test code for it — only the implementation snippet, which I extended with:
`if all(len(group) < 2 for group in stratum_pools): return None` (added inside the `strata is not None`
branch, right after building `stratum_pools`). The reasoning: if every stratum holds fewer than two
clusters, each stratum always redraws its lone cluster on every replicate, so the resampled mean is
identical on every draw — the same "zero-width 95% interval is not honest" shape `groups < 2` already
refuses one level up, and the same answer `percentile_over_units`'s all-strata-constant check gives.
I added `test_a_clustered_stratified_draw_refuses_a_zero_width_interval_too` (positive: all-strata
singleton → `None`; negative: one stratum given 2 clusters → an interval), and mutated the guard to a
no-op to confirm the positive case FAILED with a real zero-width `Interval(10.5, 10.5)` before reverting.

## Mutation testing

- `stats.py`: `range(len(group))` → `range(1)` in the drawn-cluster loop. The brief's own width-ratio
  test PASSED (see gap above — an empirical finding, not carelessness); my new call-count test FAILED
  (6000 vs expected 12000 `randrange` calls). Reverted in place, `__pycache__` cleared, both PASS.
- `stats.py`: the degenerate-case guard forced to `if False`. My new degenerate test FAILED, producing
  the exact zero-width `Interval(10.5, 10.5)` the guard exists to prevent. Reverted in place, PASS.
- `validate.py`: `stratum_varies_within_cluster(roster, cluster_by, name)` → `None`. The brief's negative
  test (`test_a_resample_stratum_varying_within_a_cluster_is_refused`) FAILED as required; the positive
  companion continued to pass (it asserts absence, so a broken check reporting nothing is
  indistinguishable from a correct one on that test alone — which is exactly why the negative test is
  the one that must fail here, and did). Reverted in place, PASS.

All three reverts were in-place edits, never `git checkout`; `__pycache__` cleared between mutation and
revert each time; full suite (`uv run pytest`, `ruff`, `mypy`) reconfirmed clean after every revert.

## Context carried forward (not this task's to fix)

`percentile_of_derived` still takes no `strata` (task 9's routed gap, unaffected by this task — I did
not touch it and have nothing to add or subtract from that routing). `E-STATS-RESAMPLE-UNSUPPORTED`
still refuses every declared `resample` end to end; nothing in this task's validate.py change or
message wording implies otherwise — the new `E-STATS-RESAMPLE-STRATIFY-VARIES` check runs *inside*
`_check_resample`, which fires alongside `E-STATS-RESAMPLE-UNSUPPORTED` on any config that reaches it,
exactly like the five checks tasks 4-8 already added there.

## Concerns for the reviewer

1. The width-ratio-vs-call-count gap above is worth double-checking independently — I traced it by hand
   and with direct interpreter runs, but a reviewer building their own reference implementation (as
   task 9's review did) would be the strongest confirmation that the fix (the spy test) is both
   necessary and sufficient, and that no other mutation escapes both tests at once.
2. I did not attempt an exhaustive-enumeration ("achievable set") style test like the existing
   `_pooled`/`_achievable` pattern for the unstratified clustered percentile, because I found by
   computation that the achievable set's *extremes* coincide across correct and mutated (1-per-stratum)
   draws on this exact fixture — so that style of test would have looked rigorous while still missing
   the bug the call-count test catches. Left as a note in case a future reviewer reaches for that
   pattern here and is surprised it doesn't discriminate.

## Review round — findings and fixes (commit 2348477)

Spec ✅, quality findings 3 Important + 3 Minor. Both concerns I flagged above were addressed by the
review directly: the reviewer built an independent reference implementation from the spec sentence
(own ordering, own seed, 200k draws) and reproduced the interval to the digit, and confirmed my
width-ratio/call-count diagnosis was correct in both halves — the width test does pass under `range(1)`
and the two are non-vacuous jointly.

**Important 1 — weights untested on the stratified-clustered path.** `weight_by` + `cluster_by` +
`stratify_by` are three independently declarable fields, so an ordinary config can reach this
combination, and nothing exercised it. Added
`test_a_clustered_stratified_draw_weights_the_pooled_units_not_the_pick`: a pinned, digit-exact weighted
interval (`c5`, the lone `high` cluster, carries weight 9) compared against the unweighted stratified
interval at the same seed. Verified by mutation: stripping the weight in the `by_stratum` build (forcing
weight 1.0 on every pair) makes the weighted call reproduce the unweighted numbers exactly
(`[16.81, 30.27]` instead of the pinned `[26.54, 64.24]`) — reverted in place, confirmed PASS.

**Important 2 — cross-stratum allocation invisible to a total.** The original spy
(`_CountingRandom`) counted total `randrange` calls per replicate and asserted `2000 * 6`. On
`_clustered_banded` (2/2/2 clusters per stratum), a mutation that makes every stratum draw the FIRST
stratum's own count still totals 6, so it passed all 1748 tests undetected. Fixed by building a second
fixture, `_clustered_uneven_stratum_counts` (1/2/3 clusters across `low`/`mid`/`high`), and replacing the
counting spy with `_RecordingRandom`, which records the `n` argument of every `randrange` call in order.
`test_a_clustered_stratified_draw_gives_each_stratum_exactly_its_own_count` asserts one replicate's calls
read exactly `[1, 2, 2, 3, 3, 3]` — the per-stratum composition, not a total a reordering or a
first-stratum substitution could coincidentally match. Verified against two mutations: `range(1)` (old
bug) now reads `[1, 2, 3, 1, 2, 3]` and fails; forcing every group to use `stratum_pools[0]`'s count now
reads `[1, 1, 1, 1, 1, 1]` and fails. Both reverted in place, confirmed PASS. The old total-only test was
removed rather than kept alongside, since the sequence assertion subsumes it (a correct sequence implies
a correct total, but not the reverse).

**Important 3 — a zero-width interval reachable, in two places.** Content-identical clusters within
every stratum (2 clusters per stratum, but each pair holding identical values) passed the count-only
guard (`len(group) < 2`) and produced a real, non-`None` zero-width interval. Per the review's ruling, I
checked whether the pre-existing *unstratified* sibling (`percentile_over_units_clustered` with no
`strata`, built in task 8) had the same hole — it does: two content-identical clusters at `G == 2` also
produce a zero-width interval today, since `groups < 2` is a count floor and answers a different
question from "can the draw ever vary". I searched `tests/test_stats.py` for any test pinning that
exact shape as correct and found none — `test_two_clusters_still_report_a_percentile` (the nearby
control) uses two clusters with *different* content, so it is unaffected — so per the ruling ("if fixing
it would change a pinned behaviour, stop and report; otherwise fix it too") I fixed both paths with one
change: the count check `if all(len(group) < 2 for group in stratum_pools)` became a content check
`if all(len({tuple(cluster) for cluster in group}) <= 1 for group in stratum_pools)`, applied
unconditionally (not just inside `strata is not None`) so it covers the unstratified case too, since
`stratum_pools = [ordered]` there is one group holding every cluster. Added
`test_two_content_identical_clusters_refuse_a_zero_width_interval` (unstratified) and
`test_a_clustered_stratified_draw_refuses_content_identical_strata_too` (stratified, with a positive
companion proving it isn't a blanket refusal of every two-cluster-per-stratum shape). Both
mutation-verified: reverting to the count-only check reproduces `Interval(3.0, 3.0)` for the stratified
case and fails as required; reverted in place, confirmed PASS.

**Minor 1 — docstring overclaimed equivalence to `E-DATA-WEIGHT-INVALID`.** That code's dual listing
shares ONE authority (`usable_weight`/`checked_weights`) between `validate` and `stats` — literally the
same function, called from two places, so the two surfaces cannot disagree by construction. This
construction cannot do that: `stats.py` is deliberately import-free of `units.py`, so it re-implements
`units.stratum_varies_within_cluster`'s equality independently rather than calling it. Reworded the
docstring and all three `reference.md` rows to say this precisely — two independent checks that must
agree, not one shared predicate — rather than claiming the stronger guarantee the peer code actually has.

**Minor 2 — the positive rule lived only in the docstring.** All three `reference.md` rows (the
validation row, and both error-registry rows) stated only the refusal trigger. Added the positive rule
verbatim — "a stratum must be constant within a cluster, and a resample's draw is a cluster drawn within
its stratum" — to the front of each of the three rows.

**Minor 3 — `validate` and `stats` disagreed on `1` vs `"1"`.** `units.stratum_varies_within_cluster`
renders each stratum value as `"no value"` for `None` and `str(value)` otherwise before comparing;
`stats.py`'s check compared raw values with `!=`, so a cluster carrying stratum `1` (int) on one unit and
`"1"` (str) on another would raise here while validate's roster-side check would call it constant. Fixed
by normalizing `stats.py`'s comparison the identical way — `rendered = "no value" if stratum is None
else str(stratum)` — going with `validate`'s convention since `units.stratum_varies_within_cluster` is
already the shared authority for this exact constancy rule everywhere else it's checked
(`fold`/`holdout`/`assign`). Added
`test_a_clustered_stratified_draws_constancy_check_agrees_with_validates` (a cluster with units `1` and
`"1"` no longer raises) and verified by mutation: reverting to raw comparison reproduces the disagreement
exactly (`ContractError: cluster 'c0' carries stratum values 1 and '1'`) and fails as required; reverted
in place, confirmed PASS.

Net test change this round: +5 (`weights_the_pooled_units_not_the_pick`,
`gives_each_stratum_exactly_its_own_count`, `two_content_identical_clusters_refuse...`,
`refuses_content_identical_strata_too`, `constancy_check_agrees_with_validates`) − 1
(`spends_one_pick_per_cluster_the_stratum_holds`, replaced) = +4, taking 1748 → 1752.

## Nothing carried over unaddressed

All 3 Important and all 3 Minor findings from the review are closed in commit 2348477. The
`percentile_of_derived`-takes-no-`strata` gap remains routed to tasks 13-15 as before; this round did not
touch that function.
