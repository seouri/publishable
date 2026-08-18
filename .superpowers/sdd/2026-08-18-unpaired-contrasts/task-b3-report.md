# Batch 3 report: tasks 10, 11, 12, 13 (+17a)

**Status: all four tasks complete, committed separately, full suite green after each.**

## Commits

| Task | SHA | Subject |
|---|---|---|
| 10 | `730551c` | feat: the unpaired key path, n_of/n_against and the per-side cluster counts |
| 11 | `3900661` | feat: Member's third evidence kind, and the exactly-one rule counted over pool/diffs/sides |
| 12 | `f39b40b` | feat: _corrected_bounds' two unpaired arms — the Welch forms rebuilt at a smaller alpha |
| 13 (+17a) | `4c91108` | feat: paired derived at every contrast branch, and the source-text pin replaced by a behavioural one |

## Test summary

Final full suite (after task 13): **2252 passed, 1 skipped, 2 xfailed.** Deltas matched each brief's
stated arithmetic: task 10 +7 (2235→2242), task 11 +4 (2242→2246), task 12 +4 (2246→2250), task 13 +2
net (2250→2252, one test renamed/replaced, two added). All four gates (`pytest`, `ruff check`,
`ruff format --check`, `mypy`) clean at every commit.

## Task 9's mutation (re-applied and verified before any new work)

`contrasts.crossed_group_axes` mutated to bare `return differing_axes(of, against)` (dropping the
`& (of.selectors | against.selectors)` intersection). Ran the full, unfiltered suite: **90 failed**,
2145 passed, 1 skipped, 2 xfailed. It discriminates strongly — task 9's pin is not a no-op. Reverted by
editing the file back (never `git checkout --`), cleared `__pycache__`, re-ran: 2235 passed, 1 skipped,
2 xfailed, matching the stated baseline exactly.

## Task 11 ruling

`UnpairedEvidence` was implemented as a **new evidence kind**, not a fourth modifier: `Member.sides:
UnpairedEvidence | None = None`, and the exactly-one rule was recast as a count over
`pool`/`diffs`/`sides` rather than a second equality. Grounds: a Welch interval's evidence is two
independent per-side value vectors — neither a pool nor a difference vector — so it cannot be
expressed as a modifier on `diffs` the way `weights`/`clusters` are. Both existing modifiers gained a
"never beside `sides`" check in `Member.__post_init__`, checked before the exactly-one rule's early
return. `UnpairedEvidence` owns its own per-side cluster-label alignment invariant in its own
`__post_init__`, because a modifier's length invariant belongs to the object that defines the vectors
it aligns against — a flat cluster pair on `Member` beside `sides` would be one field with two
admissible shapes.

## Brief/code disagreements found and how they were resolved

1. **Task 10's `min_reported_n` placeholder expression was wrong as written.** The brief's literal —
   `len(col_keys) if is_paired else min(len(of_col), len(against_col))` — references `col_keys`, which
   is only ever bound in the recorded-column (non-derived) branch. A derived, paired, `within`-scoped
   metric (exercised by the pre-existing `test_a_thin_within_contrast_warns`, whose contrast metric `r`
   is computed by `aggregate`) hits `is_paired=True` with `is_derived=True`, and `col_keys` is unbound
   there — confirmed by running the suite, which raised `UnboundLocalError`. Deviated to
   `(len(base_keys) if is_derived else len(col_keys)) if is_paired else min(len(of_col),
   len(against_col))`, matching the same expression the record literal itself uses for `n_paired`.
   Documented the deviation inline.

2. **Task 10's record-literal ternary for the derived branch tripped `ruff`'s F821.** The brief's
   snippet — `{"n_paired": len(base_keys) if is_derived else len(col_keys)}` — written inside the
   `if is_derived:` branch (where `is_derived` is always `True` there) makes `col_keys` reachable-in-
   text but never-executed; pyflakes still flags it as an undefined name on that control-flow path
   (confirmed with a minimal repro). Simplified to `{"n_paired": len(base_keys)}` in that branch only,
   since `is_derived` is trivially `True` there; the recorded-column branch keeps `len(col_keys)`
   unconditionally for the same reason.

3. **Task 10 required updating a pre-existing count-based test.**
   `test_a_contrast_entrys_paired_flag_is_written_unconditionally_at_every_branch` hardcoded
   `source.count('"paired": True') == 2`; task 10 legitimately adds two more literal sites (the two new
   unpaired arms), so the count became 4. Updated the assertion and docstring rather than leaving it
   red. Task 13 later replaced this whole test with the behavioural pin, as its own brief specified.

4. **Task 12 mutation 1's predicted magnitude did not match the measured one.** The brief predicted the
   clustered-arm-dropped mutation would land the half-width "near 41.9" (implying a ratio of 1.2276 at
   df 8.399); the actual measured value on that fixture was 11.485 (`1.348 mean... ` — see the raw
   Welch interval computed directly). The mutation still correctly **FAILED** the discriminating test on
   the expected assertion; only the specific predicted number was off. Recorded rather than silently
   corrected.

5. **Task 12 mutation 4's predicted discriminating test was not the one that actually failed.** The
   brief named `test_the_five_t_arms_are_each_reached_by_one_member_shape` as the test that would fail
   on the distinctness assertion. Measured: that test stayed **green** (the centre-flip changes the
   `sides_clustered` arm's bounds tuple, but it still lands distinct from the other five, so the `== 6`
   count holds). The mutation was still caught by the full, unfiltered suite —
   `test_an_unpaired_clustered_members_corrected_bound_reads_its_own_two_cluster_counts` failed instead,
   via a `zip()` length-mismatch `ValueError` (its fixture's `of`/`against` differ in length, 9 vs 12,
   so swapping them without swapping the label vectors crashes before reaching any centre-flip
   arithmetic). The qualitative claim ("this mutation is caught") held; the specific attribution in the
   brief did not. Followed the brief's own instruction to record this rather than force the named test
   to be the one that fails.

No other brief/code disagreements were found. All prescribed mutations were run against the full,
unfiltered suite in the foreground and reverted by editing the file back; none were left applied.
