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
