# Task 10 report — the stratified × clustered composition rule

Status: COMPLETE
Commit: 97c911c

## Test summary

`uv run pytest` 1748 passed + 2 xfailed (baseline 1742 + 6 new: the brief's 2 stats tests and 2
validate tests, plus 2 I added — a call-count test and a degenerate-case pair — see below). `uv run
ruff check .` and `uv run mypy` both clean.

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
