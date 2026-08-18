# H4c batch 2 report — tasks 4–8

**Status: complete.** All five tasks implemented, tested, mutated, and committed in order.

**Commits:**

- `900e22b` — task 4: `welch_t_over_units`, and `_sample_variance` extracted from `t_over_units`
- `1bb70b7` — task 5: `cohens_ds`
- `620f698` — task 6: `unpaired_percentile_of_sides`, and `_draw_pools` extracted from `paired_percentile_of_derived`
- `ecd535a` — task 7: `welch_t_over_units_clustered`, and `_cr1_variance` extracted from `t_over_units_clustered`
- `14587e0` — task 8: the `_clustered` percentile spelling tests (test-only, no `src/` change)

**Test summary:** started at 2208 passed / 1 skipped / 2 xfailed. Ended at 2227 passed / 1 skipped / 2 xfailed (task 4: +4, task 5: +3, task 6: +5, task 7: +4, task 8: +3 — matches each brief's stated delta). `ruff check .`, `ruff format --check .` (80 files), and `mypy` (45 source files) all clean after every task. Every mutation was run against the full, unfiltered suite in the foreground and reverted by editing the file back (never `git checkout --`), then re-verified green before moving on.

## Mutation outcomes

**Task 4** (4 mutations, 1 named blind and not run): pooled variance → FAIL 4.722138614325821; df `min(n)−1` → FAIL 3.9264863229551143 (≈ obtained 3.926486322955114); df `n_of+n_against−2` → FAIL 2.8968851611887434; `_sample_variance` extraction dropping `(n−1)` → FAIL on both its own oracle and `test_every_paired_contrast_cell_is_unmoved_across_this_branch[plain_t]`'s `ci95`.

**Task 5** (3 mutations): Welch-style denominator → FAIL 7.071067811865475; unweighted mean of the two variances → FAIL 2.581988897471611; `sd >= 0` floor → FAIL with `ZeroDivisionError` (an attributable failure, not the bare `None` the brief predicted, but the same corner).

**Task 6** (4 mutations, 1 not prescribed): one draw for both sides → FAIL via `KeyError` inside the `try` (attributable, as the brief anticipated as the alternative to the size assertion); pooled draw split at `len(of_keys)` → **PASSED, contrary to the brief.** Verified by direct call: with no `strata`/`clusters`, `_draw_pools` returns exactly one group per side whose size equals that side's key count, so concatenating `of_pools + against_pools` and splitting the drawn sequence at `len(of_keys)` reconstructs the unmutated per-side draws bit-for-bit — RNG consumption order and count are identical either way. This is the "mutation whose two branches cannot differ" trap the spec names, just not previously identified for this specific mutation; `and`→`or` on the degenerate-refusal connective → FAIL on the one-constant-side case as predicted; reversing `_draw_pools`' unclustered `items` order → FAIL on the extraction oracle's endpoints and on `test_cli.py::test_every_paired_contrast_cell_is_unmoved_across_this_branch[plain_t]`/`[weighted_percentile]` (paired form moved too, confirming the shared extraction is watched from both ends — brief named `plain_percentile`/`clustered_percentile`, `weighted_percentile` moved instead, same property).

**Task 7** (5 mutations, 1 measured-not-prescribed): df→`groups_of−1` → FAIL 35.653950021811816; df→`groups_against−1` → FAIL 26.371354753115764; df→`groups_of+groups_against−2` → FAIL 21.301137240534675; IID variance for both `_cr1_variance` calls → required setting `groups_of=n_of, groups_against=n_against` (not just swapping the variance expression) to reproduce the brief's exact target 9.647234756296374 — the brief's literal instruction ("replace both `_cr1_variance` calls with `_sample_variance/n`") under-specified what happens to the cluster counts; done correctly it reproduces the plain Welch form exactly, confirmed FAIL on both target tests; dropping `G/(G−1)` in `_cr1_variance` → FAIL on 17 tests including its own oracle and `[clustered_t]`'s `ci95`/`ci95_corrected`. Reversing-one-side's-labels was measured rather than prescribed, per the brief's own instruction: both reversals actually change the answer on fixture B (of-reversal: 46.98→42.73 high; against-reversal: 46.98→47.08 high, a smaller but real difference) — the brief's suspicion of possible blindness for the against-side did not hold exactly, so neither was used as a scored mutation.

**Task 8** (3 mutations, test-only): units instead of clusters in `_draw_pools`'s clustered branch → FAIL on the target assertion and on `test_cli.py::test_a_clustered_resampled_contrast_really_drew_clusters` and `[clustered_percentile]`, exactly as predicted; one side's cluster mapping for the other → FAIL via `KeyError`, exactly as predicted; ordering clusters by label instead of by sorted contents → FAIL on the relabelling-invariance test, exactly as predicted.

## Disagreements between the briefs and the code

1. **Task 6, `pytest.raises(ContractError, match="E-STATS-RESAMPLE-STRATIFY-VARIES")`** — as given verbatim in the brief, this cannot pass: `ContractError`/`PublishableError.__str__` is the bare message, which never contains the code string, only `exc.code` does. Every other test in the file asserting this code catches the exception and checks `exc.value.code == "..."`. Fixed to that idiom (`with pytest.raises(ContractError) as exc: ...; assert exc.value.code == "..."`).
2. **Task 6, `column = getattr(table, "m")`** in `_row_count_recorder`, given verbatim in the brief — `ruff check` flags this (`SIM105`-style "replace getattr with attribute access"), which would have failed the gate. Changed to `table.m`, no behavior change.
3. **Task 6, mutation 2 ("a pooled draw")** — see mutation outcomes above: literally blind on fixture A, contrary to the brief's claim that "this is the mutant an interval assertion alone cannot see." Verified by direct call rather than accepted on the brief's say-so, per `CLAUDE.md`'s "a mutation is a claim too."
4. **Task 7, mutation 4 ("the IID variance")** — the brief's instruction ("replace both `_cr1_variance` calls with `_sample_variance(...)/n` per side") is ambiguous about what happens to `groups_of`/`groups_against`. Read literally (variance swapped, cluster counts kept as real cluster counts), it produces neither of the two numbers the brief names (9.647234756296374) nor the fixture-B mutant table's numbers — I got 17.346768653175... To hit the brief's own target exactly, the cluster counts also had to become the unit counts (i.e., simulate no clustering at all), which is what actually reproduces "the IID Welch form on the identical data." Implemented that reading; confirmed exact match.
5. **Task 8's CAPTURE-AND-PASTE literals** were genuinely captured from this branch's first green run (`[-4.7272727272727275, 23.242424242424242]` for the clustered draw, `[4.0, 19.833333333333332]` for the unclustered control), not invented — matches the brief's own discipline for constructions that don't exist yet.

## Notes

- `E-DATA-ALLOCATION-CONTRAST` was not touched; all five tasks tested by direct call as instructed, and no `validate`/`run` path was exercised for the new constructions.
- `PairedResample`'s docstring had "paired" deleted per spec correction 7, in task 6's commit.
- `_draw_pools`'s `ValueError` message had `paired_percentile_of_derived`'s name deleted (not enumerated to two callers), per the brief.
- No config-count or executable-count claims are made anywhere in this report or its commits.

## Fix round 1

Review at `task-b2-review.md`, reviewed commit `72e3e67`. The two verdicts above (spec compliance
PASS; no behavioural defect anywhere) stand; every finding below is prose or a mutation-record error,
none a wrong number. **Nothing above this section is edited** — each original claim stays as the
record of what was found at the time, and this section says what replaces it, per the house
convention for the development record.

### Major 1 — `_sample_variance`'s two false docstring claims

**Repaired by deletion**, not qualification, per the reviewer's ruling and house convention.
`src/publishable/stats.py`: "— the one copy in this module" deleted from the opening line (false:
`cohens_dz` computes the identical expression over the difference vector); the claim that
`weighted_t_over_units` and `cohens_dz` have denominators that "are different quantities" narrowed to
name only `weighted_t_over_units`, whose `Σw − Σw²/Σw` genuinely is different, with `cohens_dz`'s own
sentence rewritten to say its non-use is a scope choice rather than a difference in the expression.
**Verified by running:** `cohens_dz([1.0,2.0,3.0,4.0,5.0])` and
`mean/sqrt(_sample_variance([1.0,2.0,3.0,4.0,5.0], mean))` are bit-identical, matching the reviewer's
own check; full suite still 2227/1/2 after the edit.

### Major 2 — task 6 mutation 2: blindness claim withdrawn, not edited away

**The original report's line 21 sentence — "PASSED, contrary to the brief … the mutation whose two
branches cannot differ trap" — is WITHDRAWN.** It was true only for fixture A (unclustered, no
strata), before task 8's clustered tests existed, and is stated in the present tense as a property of
the mutation rather than of the moment it was measured.

**Re-verified by running the exact mutation** (`drawn_of`/`drawn_against` replaced by one draw over
`of_pools + against_pools` split at `len(of_keys)`) against the full unfiltered suite at HEAD:
**2 failed, 2225 passed, 1 skipped, 2 xfailed** —
`test_the_unpaired_clustered_percentile_draws_whole_clusters_per_side` and
`test_the_unpaired_clustered_percentile_is_invariant_to_relabelling`, both via an uncaught
`KeyError: 'ag00'` at the `unit_table_from_rows` line, matching the reviewer's finding exactly. Reverted
by editing the file back; re-ran to confirm 2227/1/2 clean.

The corrected answer, carried forward: **a clustered fixture discriminates this mutation** (each
side's drawn key list has variable length under whole-cluster draws, so a fixed split at `len(of_keys)`
cross-contaminates the two key spaces and raises); **a stratified-only fixture does not** (per-side
totals stay fixed at 5 and 25 regardless of stratification, so the split reconstructs both draws
bit-for-bit — blind for the identical reason fixture A is). This mutation is not the
branches-cannot-differ trap; it was mis-fixtured in the original report, which measured it before the
clustered tests existed and did not re-check it after.

**The `unit_table_from_rows`-outside-`try` placement is deliberate, not a finding to file.** It
mirrors `paired_percentile_of_derived`'s own placement exactly, and the review's own conclusion is what
it buys: because the two sides hold disjoint key spaces (unlike the paired form's single shared key
list), a caller-space bug — a key drawn for one side that doesn't index that side's mapping — is
reachable here in a way it structurally cannot be in the paired form. Keeping table construction
outside the `try` means that class of bug raises hard rather than being silently absorbed into
"degenerate draw, continue," which would hide a real defect as a merely-thinned pool. Documented in
place with a comment at the call site (`src/publishable/stats.py`, in `unpaired_percentile_of_sides`)
rather than left implicit.

### Major 3 — task 6 mutation 4: corrected to what actually fails

**The original report's line 21 attribution — "FAIL on the extraction oracle's endpoints and on
`[plain_t]`/`[weighted_percentile]`" — is WRONG about the first two names and is corrected here.**
Re-run of the brief's exact mutation (`items = [[key] for key in reversed(keys)]` in `_draw_pools`'s
unclustered branch) against the full unfiltered suite gives **7 failed**, matching the reviewer's list
exactly:
`test_cli.py::test_every_paired_contrast_cell_is_unmoved_across_this_branch[weighted_percentile]`,
`test_cli.py::test_the_undeclared_resample_shape_is_pinned_absent_key`,
`test_cli.py::test_the_undeclared_resample_shape_is_pinned_explicit_null`,
`test_cli.py::test_an_unclustered_resampled_contrast_draws_what_it_always_drew`,
`test_stats.py::test_the_unclustered_paired_draw_is_the_same_sequence_it_always_was`,
`test_stats.py::test_the_unpaired_percentile_draws_each_side_independently`, and
`test_stats.py::test_the_unpaired_clustered_percentile_is_not_the_unclustered_one`. Neither
`test_the_extracted_draw_pools_leaves_the_paired_draw_where_it_was` (the "oracle") nor `[plain_t]` is
among them, and neither can be: the oracle's only draw-reading assertion passes `clusters=`, so it
never exercises the unclustered branch this mutation touches, and `[plain_t]` is a `paired_t_over_units`
cell (`clusters=None`, no `resample_columns`) that never reaches `_draw_pools` at all — it belongs to
task 4's mutation 4, not this one, and is presumably where the line in the original report came from.

**Fixed by narrowing the oracle's docstring** (`tests/test_stats.py`,
`test_the_extracted_draw_pools_leaves_the_paired_draw_where_it_was`) to state plainly that it covers
only the clustered branch, name the two tests that actually cover the unclustered branch
(`test_the_unclustered_paired_draw_is_the_same_sequence_it_always_was`,
`test_the_unpaired_percentile_draws_each_side_independently`), and record that this test's own fixture's
endpoints happen to survive the reversal — a coincidence of the fixture, not a property of the
extraction, and the reviewer's own "a fixture whose numbers agree with the bug" shape. I did not add an
unclustered assertion to make the original "this is the oracle" claim true instead: I checked, and this
specific fixture's unclustered endpoints (`[4.666666666666667, 8.0]`, confirmed by direct call) also
survive the reversal, so adding it would not have closed the coverage gap — narrowing the claim is the
sound fix here, not padding it with an assertion that cannot fail either.

**Verified by running:** full suite 2227/1/2 after the docstring edit (no assertion changed); the
7-failure mutation outcome re-confirmed and reverted by editing back.

### Minor 4 — `UnpairedEvidence` present-tense claims

Fixed at both sites (`src/publishable/stats.py`, `welch_t_over_units` and
`welch_t_over_units_clustered`): "carries them as" / "carries exactly that pair" → "will carry … (task
11, not yet built)". Verified by re-reading both docstrings whole, not only the edited clause, per
`CLAUDE.md`'s "when you edit a docstring, re-read the whole one."

### Minor 5 — `_cr1_variance`'s uniqueness claim

**Repaired by deletion**, matching Major 1's remedy rather than qualifying the claim with an
exclusion clause (an earlier draft of this fix added a qualifying sentence naming
`weighted_t_over_units_clustered`'s own sandwich; reverted in favour of deleting the false
universal — "One expression for the cluster-robust variance" — and keeping only the accurate "three
callers" enumeration, which was never in dispute).

### Minor 6 — `t_over_units_clustered`'s unfalsifiable guard

**Removed**, since `_cr1_variance`'s own `n < 2` check produces the identical `None` first in every
reachable case — verified by inspection that no path reaches `mean = sum(values)/len(values)` without
having already passed `_cr1_variance`'s internal floor, so `len(values)` is never zero there. Docstring
narrowed to say plainly that this function keeps no guard of its own, matching what it already claimed
about where the floors live. Verified by running: full suite unchanged at 2227/1/2, confirming the
removal is truly behavior-preserving.

### Minor 7 — CAPTURE-AND-PASTE literals given a real constraint

Both task 8 tests' docstrings (`tests/test_stats.py`) gained the reviewer's exact-rational
construction-pinning argument: `-4.7272727272727275` = −52/11 and `23.242424242424242` = 767/33 are
reachable under the whole-cluster draw and unreachable under a unit draw; `4.0` and
`19.833333333333332` = 119/6 are the reverse; both sets share the same range so only the denominators
discriminate. Not re-derived independently — recorded on the reviewer's verified enumeration, credited
as such, since the point was that the record state the reason rather than that I reproduce the
computation a second time.

### Minor 8 — two small misstatements in the original report

- Task 5 mutation 3: the original line said the brief predicted "the bare `None`," which is wrong —
  `task-5-brief.md` Step 5 predicts `ZeroDivisionError` explicitly, and the recorded outcome matched
  it. Left as-is above per the no-retro-edit convention; noted here as WRONG and superseded by this
  line: the outcome agreed with the brief throughout.
- Task 7's literal-reading note (17.346768653175…) is accurate but incomplete: that number sits
  0.017% from the spec's own fixture-B row for `CR1 meat, df = n_of + n_against − 2`
  (`17.343852668925262`), a coincidence no test depends on but worth carrying, per the reviewer.

### The brief-mislabelling correction ("26.371… is `G_against−1`, not `G_total−2`")

**Checked, not found in any artifact of this batch.** `task-7-brief.md`'s own text, this report's task
7 mutation-outcomes line, `tests/test_stats.py`'s `test_the_unpaired_clustered_t_combines_two_per_side_cluster_dfs`
docstring, and `src/publishable/stats.py`'s `welch_t_over_units_clustered` docstring all already label
`26.371354753115764` as `G_against − 1` and `21.301137240534675` as `G_total − 2` (or "the pooled
reading"), matching the correct assignment. The mislabelling the coordinator's note refers to was in a
document given to the reviewer that is not part of this batch's artifacts (the review itself already
carries its own correction at its § "Verified by running" bullet, and `progress.md` carries a ledger
entry). No file in this batch's diff needed a change for this item. `grep -rn '26.371' .` (excluding
`.git/`) confirms every hit outside `.superpowers/sdd/.../progress.md` (the ledger's own correction) and
`task-b2-review.md` (the review's own correction) already reads `G_against − 1`.

### Verification of the whole fix round

Gates at HEAD, foreground: `ruff check .` clean, `ruff format --check .` 80 files, `mypy` 45 source
files, `pytest` **2227 passed, 1 skipped, 2 xfailed** — unchanged from before the fix round, as
expected, since every fix is a docstring/comment correction plus one dead-code deletion verified
behavior-preserving. Tree diff touches only `src/publishable/stats.py` (docstrings, one dead guard
removed, one new comment) and `tests/test_stats.py` (one docstring narrowed, two docstrings given real
constraints). `git status --short` empty after commit.
