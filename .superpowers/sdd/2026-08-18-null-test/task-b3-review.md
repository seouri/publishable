# Batch 3 review — tasks 11, 12, 13, 14, 15a, 15b

Reviewed at `d97ec9c` on branch `h4d-null-test`, against
`docs/superpowers/specs/2026-08-18-null-test-design.md` including its appended
§ Corrections against the code, the task 11–15 briefs, and `task-b3-report.md`.

**Gates, run at `d97ec9c` before any mutation:** `ruff check` clean, `ruff format --check`
80 files formatted, `mypy` clean (45 files), `uv run pytest` **2321 passed, 1 skipped,
2 xfailed** — the counts the batch claims. `E-STATS-NULLTEST-UNSUPPORTED` is alive
(`validate.py:4033`), and no sentence in the batch's diff claims a config unblocked or moves
the 0/6/3 counts.

## Verdicts

**Spec compliance: FAILS.** The constructions themselves match the spec and its corrections —
`p = 1/5001` is right, the two-argument `compute` is the only shape that can express a derived
permutation, the two cluster levels and the contrast delegation are what § Clustered units and
§ What isn't a repeat describe. What fails is task 15b's central claim and two normative rules:
the collision-under-cluster property is **not** protected by construction in any way a test can
see (Critical 1), the corner it declared closed publishes a **zero-width 95 % interval** and a
zero-width *corrected* interval that `reference.md` § Statistical reporting refuses in those
terms (Major 2), and 15a ships a clustered percentile construction outside the content-based
refusal that document scopes as covering every clustered form (Major 4).

**Task quality: strong on measurement, weakest exactly where it mattered most.** Three fixture
defects found by computing rather than by trusting (all three confirmed here as real, and fixed
by measurement rather than by weakening an assertion), two brief errors adjudicated correctly
(the nonexistent docstring paragraph, the missing method-table row), the `validate.py` sweep done
and clean. But the batch read `ci95: [0.0, 0.0]` as "a real `ci95`" and "a genuine clustered
interval", and its own 15b mutation exercised only a string literal — the report says so in its
own words ("FAILS ... on the `method` assertion") without drawing the conclusion.

## Findings

### Critical 1 — the `_clustered` label and the clustered draw are decoupled, and nothing pins them together (`src/publishable/cli.py:1041-1048`)

**Verified by running.** The derived contrast branch chooses its `method` from one ternary and its
`clusters` argument from a second, independent one. Editing **only** the argument —
`clusters=(None if clusters is None else {...})` → `clusters=None`, label untouched — leaves the
suite green at both levels: `uv run pytest tests/test_cli.py` **308 passed, 1 skipped** — the
branch's own test file — and the full `uv run pytest` **2321 passed, 1 skipped, 2 xfailed**,
unchanged. The record
then reads `method: paired_percentile_over_units_clustered`, `n_paired_clusters: 3`, over a
unit-level draw: **verbatim the shape of the Critical the whole-branch review found**, which
H4b-2's `clusters is None` guard prevented and 15b replaced with an unverified label.

Why no test sees it: the only fixture reaching this branch
(`tests/test_cli.py:4168`, `test_a_derived_key_collision_under_a_cluster_end_to_end`) produces
`ci95: [0.0, 0.0]` under **both** constructions, so its `ci95 is not None` assertion is blind to
the arithmetic and the `method` literal is the entire pin. I confirmed the branch is the one that
writes the record (sentinel: line 1042's literal changed to `SENTINEL_DERIVED` appeared in
`run.yaml`'s contrast entry), so this is the exercised path, not a dead one.

**Where the fix belongs:** a direct-call test in `tests/test_stats.py` beside the existing
`paired_percentile_of_derived` clustered tests pins the *construction* but **not** `cli.py`'s two
ternaries agreeing. Only an **end-to-end** fixture — a non-degenerate derived metric under a
declared `cluster_by`, reached through `run` — makes this mutation fail.  A discriminating fixture is trivially available — direct call to
`paired_percentile_of_derived` over 4 clusters × 5 units, same keys both sides, non-degenerate
computes: clustered width **100.0**, unit-level width **49.95**. The missing pin is an omission,
not an impossibility. Both mutations reverted by editing back; `diff` against a pre-mutation copy
reports identical, `git status` clean.

### Major 2 — the corner declared closed publishes a zero-width interval, and a zero-width corrected interval (`src/publishable/cli.py:1030-1050`, record shape)

**Verified by running** the end-to-end fixture and reading `run.yaml`:

```
delta: 0.0, method: paired_percentile_over_units_clustered, ci95: [0.0, 0.0],
ci95_corrected: [0.0, 0.0], correction_level: 0.025, n_paired_clusters: 3
```

beside per-condition `t_over_units_clustered` intervals of width 19.4, with `validate` reporting
zero errors and only the collision warning. `reference.md` § Statistical reporting is normative
here: *"The contrast then reports its `delta` with `ci95: null` ... a zero-width 95 % interval is
not [honest]"*. The guard that enforces it, `_drawable_content`, compares **row content**;
compute-degeneracy — both sides evaluating the same formula over the same rows — escapes it, which
is the case `paired_percentile_of_derived`'s own docstring names as *"plausible but wrong ... with
nothing to raise"*.

**Not introduced by this batch**: I ran the same project without `cluster_by` at `d97ec9c` and got
the identical shape under `paired_percentile_over_units`, so the unclustered route pre-dates 15b.
What 15b did is extend a documented-refused shape to a second path, cite that output as its
end-to-end verification, and file nothing. It belongs in `spec-defects.md` at minimum.

### Major 3 — a docstring guarantee the code does not provide: `n.clusters` beside a draw of a different G (`src/publishable/stats.py:1738-1741`, caller at `3048-3054`)

`percentile_of_derived_clustered`'s docstring: *"`G` being `units.cluster_count_of`'s answer, so
this cannot disagree with the `n.clusters` a caller prints beside the interval."* **Verified false
by direct call:** `summarize_step` with `counts` carrying `clusters: 4` and a `collapsed` spanning
only 2 clusters records `n: {..., clusters: 4}` beside
`method: percentile_of_derived_clustered`, `ci95: [80.0, 90.0]` — an interval drawn from **2**
clusters. The derived branch passes `attrition`'s condition-wide figure straight through
(`"n": {**counts, "completed": len(collapsed)}`) while the recorded-column branch deliberately
recomputes with `cluster_count_of(clusters, column_keys)` for exactly this reason. The docstring
should be deleted or the figure recomputed. Reachability through a real `run` needs a step that
records for a subset of completed units — plausible, and the shape the recorded-column docstring
already treats as real, but **I did not construct it**: that half is a weaker claim than the
surface fact.

### Major 4 — a clustered percentile construction with no zero-width refusal, where its sibling has one (`src/publishable/stats.py:1724-1789`)

**Verified by direct call** on identical content (20 units of `y = 5.0` in 4 clusters):
`percentile_of_derived_clustered` → `Interval(5.0, 5.0, 'percentile_of_derived_clustered')` with
500 survivors; `percentile_over_units_clustered` → `None`. `reference.md` scopes the open gap
narrowly — *"the plain unweighted, unstratified, unclustered `percentile_over_units` carries no
such check"*, immediately after stating that `percentile_over_units_clustered` **does** make the
refusal *"whether or not `strata` is declared"*. 15a adds a clustered form to the gap and changed
neither the guard nor that paragraph. (`percentile_of_derived` was already an undocumented member
of the gap; the new function makes the family rule read wrong rather than incomplete.)

### Minor 5 — stale call-site count in `_draw_pools`' docstring (`src/publishable/stats.py:1963`, `1978`)

*"One draw shape, for a percentile construction's **two** callers"* and *"**Two callers**:
`paired_percentile_of_derived` ... `unpaired_percentile_of_sides`"*, while there are now three
(`1765`, `2151`, `2291-2292`). Task 15a's brief calls itself *"a third caller"* and the new
function's own docstring says *"other two callers"*, so the count was known and not swept — the
count-phrase-near-an-insertion trap `CLAUDE.md` lists.

### Minor 6 — the strata refactor moved the unstratified RNG stream, and the new prose calls that path "an identity"

**Verified by computation:** fixture C, no strata, seed 7, n = 5000 — the pre-refactor in-place
walk gives `p = 0.48050`, the new per-group walk `p = 0.47351` (also at seeds 2 and 3). The brief
predicted this (*"This changes the unstratified draw's RNG consumption"*), task 11's assertions are
range-based so nothing failed, and nothing user-visible moved because `null_test` is unwired. But
the shipped docstring and comment say *"With no `strata` the whole vector is one stratum, which is
an identity rather than a second path"* — a distributional identity, where `_draw_pools`' analogous
refactor was careful to claim *"it is RNG-IDENTICAL"* and mean it. No test pins the unstratified
stream, so the next such refactor is invisible too.

### Minor 7 — one claim at two sites (`src/publishable/stats.py:929-935` and `945-951`)

The same six lines of prose appear verbatim as both the docstring's `strata` paragraph and an
inline comment above the `groups` construction. The implementer's adjudication of the brief here is
**correct and I verified it**: `git show 0a69c8b:src/publishable/stats.py` shows task 11 shipped no
paragraph asserting the in-place shuffle is deliberate, so there was nothing to delete. The result
is nonetheless one claim maintained twice.

### Minor 8 — rewritten rather than deleted, against the brief's explicit instruction

Task 15b step 3 says *"Delete the raise and its whole justifying comment rather than rewriting
either"*. `stats.summarize_step`'s paragraph (`2828-2835`) and `cli._comparison_step_blocks`'
comment (`995-1015`) were both rewritten. Two of the invented sentences are Findings 1 and 3 above
— which is the argument for the rule.

### Minor 9 — observation, not a defect: the derived `method` vocabulary is asymmetric

Unclustered, a derived metric records `percentile_over_units`, indistinguishable from a column's;
clustered, it records `percentile_of_derived_clustered`. Both are documented (the new
`reference.md` row states exactly this), so the record is self-describing — but a reader cannot
tell derived from column in one case and can in the other.

## Adjudications, each verified rather than accepted

- **Task 12's count-based fixture defect: real, and correctly fixed.** A permutation holds the
  label multiset fixed, so an `of`-arm **count** guard can never fire. The replacement's enumeration
  is exactly right — I reproduced `[3,4,5,5,6,6,6,7,7,7,8,8,8,9,9,9,10,10,11,12]`, ten of twenty
  below 8. The assertion was **strengthened** to two-sided `0 < survivors < 200`, not weakened.
- **Task 14's confinement fixture defect: real, and correctly fixed.** Two 2-unit cells give
  `|Π| = 4` within-cell and `C(4,2) = 6` free — no `1/1000` is earnable there. The replacement
  reuses fixture C, whose `1/1000` is **arithmetic, not fitting**: I independently confirmed
  within-stratum `reached = 0` (the observed labelling is the unique maximum; second-best delta
  `29/12 ≈ 2.41667`) and free `p ≈ 0.4795`, so both separations the test asserts are real.
- **Fixture C's four separations: independently recomputed.** Observed delta exactly 2.5
  (`ΣS_c/12 − 920`), `b = 0` → `p = 1/5001 = 0.0001999600079984003`; `b/n` → 0.0; reused assignment
  → 1.0; wrong stratum → ≈0.4795; wrong level → every cluster's label is `against`, so `of` is
  empty and the answer is `None`. Each is asserted. The report's "±1 mutation is blind here" is the
  brief's own framing; in fact the clustered spelling's `1/5001` literal would catch it, so nothing
  is unpinned by that decision.
- **The two-argument `compute` contract: honoured at every call site, because the only call sites
  are tests.** `grep -rn 'permutation_of_derived\|_make_null_fn' src/` returns the definition and
  nothing else — wiring is task 20 and `E-STATS-NULLTEST-UNSUPPORTED` is alive. Fixture C2
  discriminates without a prescribed mutation, as the correction predicted: a labels-ignoring
  closure returns `None`, not `1.0`, and the invariance test pins that.
- **The `validate.py` sweep: done and clean.** Both comments are corrected in the commit. My own
  read-then-grep sweep for the *claim* (`does not exist`, `doesn't exist`, `may not yet`,
  `not yet`, `Temporary`, `does not have`, `resamples nothing`, `cannot be clustered`, intersected
  with `deriv|recomput`) over `src/`, `tests/` and the four documents found one unrelated
  pre-existing hit (`reference.md:1175`, about an absent `resume` reader). The sweep can fail:
  the control string `percentile_of_derived_clustered` hits 17 lines over the same file set.
- **The missing method-table row: correctly identified and required.** `percentile_of_derived_clustered`
  is a newly minted string and now has a row. `paired_percentile_over_units_clustered` needs none —
  I read both the suffix paragraph (*"each of the unweighted forms above takes a `_clustered`
  suffix ... the percentile forms resample whole clusters — jointly across both sides when
  paired"*) and the `paired_percentile_over_units` row (*"Every derived metric"*), and together
  they cover it. `E-STEP-KEY-COLLISION`, newly cited from § Contrasts, has its row at
  `reference.md:1032`.
- **Mechanical pass on the touched documents:** no trailing whitespace, tabs or invisible unicode;
  the new table row matches its header's column count; no positional locators or count phrases
  near the deleted § Errors row; `×` unaffected. The deleted row's neighbours read correctly.

## What I could not check

- Reachability **through a real `run`** of Major 3's `n.clusters` disagreement (needs a step
  recording for a proper subset of completed units — I verified the surface fact only).
- The task 12 / 13 / 15a mutations the report lists: I re-ran only the ones adjacent to 15b and the
  new decoupling one. Their described branches are plausible from reading; not verified by running.
- Anything about the `null_test` record keys, the echo or `p_value_corrected` — unwired here.

## Tree state

Clean. Two edits to `cli.py` took effect and were reverted **by editing the file back** — the
`clusters=None` decoupling, and line 1042's `SENTINEL_DERIVED` — and two further heredoc attempts
asserted out and wrote nothing. Both applied edits were verified by `diff` against a pre-mutation copy (`REVERTED_IDENTICAL`) plus `git status --short`
reporting nothing. The scratch probe file `tests/test_zz_scratch_review.py` was created and deleted
three times and is not present. `.superpowers/sdd/.gitignore` was not clobbered (no
`sdd-workspace`/`task-brief` run); this review file needs `git add -f`.
