# Batch 3 review — tasks 10–13, clusters threaded into contrasts

Reviewed at `442fc2d` (the four task commits `c51e049`, `6b9d8a7`, `61d95bd`, `84db48f`, the report
`7cd0891`, and the ledger `442fc2d`). Gates re-run here: `ruff check` clean, `ruff format --check`
80 files, `mypy` clean over 45 source files, `pytest` **2196 passed, 1 skipped, 2 xfailed**.

## Verdicts

**Spec compliance: PASS.** The six-cell `method` table, `Member.clusters` as a modifier on `diffs`,
the `clusters` → `weights` → plain preference in `_corrected_bounds`, and `n_paired_clusters` as an
absent-not-null scalar sibling of `n_paired` all match `docs/reference.md` § Contrasts and
§ Statistical reporting and the design's § Corrections against the code (items 1 and 2 in
particular — the third `method` string rather than a fourth function, and the two-site rather than
one-branch selection). `E-DATA-CLUSTER-CONTRAST` is alive and pinned; every new test routes by
direct call to `_comparison_step_blocks`; no sentence in the commits, the report or the ledger
claims a config is unblocked.

**Task quality: PASS with one Major.** The corrected bound genuinely moves and its α is pinned —
verified by two mutations, not by reading — and the *t*-arm selection, which no mutation in this
batch's own report had exercised beyond the implementer's word, was re-run here and does fail two
tests in opposite directions. The batch's own blind-mutation claims held under
re-running, including one I actively tried to overturn. The Major is a false guarantee in prose: the
df-provenance clause batch 1 deleted from the normative document has come back in three places.

---

## Findings

### Major 1 — the df-provenance clause batch 1 deleted is reintroduced at three sites, and is false for half the reachable cells

- `src/publishable/cli.py:1152-1153` — "…or with no count for a reader to check `clusters − 1`
  against, is a declaration accepted whose effect is half delivered."
- `src/publishable/cli.py:1158-1162` — "`cluster_count_of` is the SINGLE counting expression … so
  the count printed beside an interval **cannot disagree with the df inside it**."
- `tests/test_cli.py:3373-3375` — "§ Contrasts: the cluster count is a scalar sibling of `n_paired`,
  and **it is the count the interval's df was taken from, so a reader can check `clusters − 1`
  against the interval rather than take it on trust**."

The test docstring is **verbatim** the sentence batch 1's review Major 1 ordered deleted from
`docs/reference.md` § Contrasts (ledger: *"the percentile one is a **resampling draw with no df**.
… Deleted rather than rewritten"*), and it now cites *§ Contrasts* as its source — a section that no
longer contains it. Confirmed by reading `docs/reference.md:2648-2682`, which carries the
`n_paired_clusters` paragraph with no df clause.

**Verified by running**, not by reading: a direct call with `resample_columns=True` and the fixture's
membership returns

```
{'delta': 6.333…, 'basis': 'units', 'paired': True,
 'method': 'paired_percentile_over_units_clustered', 'n_paired': 12,
 'ci95': [1.0, 8.0], 'cohens_d': 2.0338…, 'correction': None, 'n_paired_clusters': 3}
```

— `n_paired_clusters` is written in the percentile cell, where the interval is a percentile of a
resampled pool and there is no df at all. Confirmed by reading `stats.paired_percentile_of_derived`:
no degrees of freedom anywhere in it or its helpers. The clause is true only for the two *t* cells,
false for the two percentile ones, and it is written as general over `n_paired_clusters`.

This is the *"comment or docstring claiming a guarantee the code does not provide"* shape, made
worse by the misattribution — a reader greps § Contrasts for the sentence and does not find it.
`CLAUDE.md` prefers deleting a claim to rewriting it: the surrounding sentences at all three sites
stand without it (the single-counting-expression argument at cli.py:1158 is independently true —
`cluster_count_of` is the only counting expression, verified by grep: `runner.py:104`,
`stats.py:292/374/943/2090`, `cli.py:1175`, and `units.cluster_count` itself — it is only the
*"cannot disagree with the df"* half that overclaims).

**Disposition: a fix round before task 14 starts**, on the precedent batch 1 set for the identical
clause ("Owner: this batch's fix round … before task 6 starts"). All three sites, **deleted rather
than rewritten**. The test docstring is the urgent half: it attributes the sentence to § Contrasts,
so a reader greps the normative document, finds nothing, and cannot tell whether the code or the
document is behind. Behaviour is unaffected — this does not block the branch, but it must not reach
task 14's brief, which reads these comments as its specification.

### Minor 1 — one of task 12's two asserted numbers is arithmetic on the test's own literal

`tests/test_correction.py:663-664`: `raw_half = (member.ci95[1] - member.ci95[0]) / 2` then
`assert raw_half == pytest.approx(8.763214143637903)`. `member.ci95` is constructed two lines above
from that same literal, so the assertion touches no production code. The docstring
(`tests/test_correction.py:646-649`) claims "**both** are asserted so a construction that ignored
the level would fail as loudly as one that ignored the membership" — one of the two cannot fail.

The guarantee itself **does** hold, verified by running two mutations (below), so this is the
docstring overclaiming rather than a coverage hole. Inherited verbatim from the brief.

### Minor 2 — the report inverts the executability counts

`task-10-13-report.md:116-117`: "the no-remaining-core-side-blocker count stays **six** and the
executable count stays **three**". `CLAUDE.md` says the opposite: "**three of nine — E1, E2, E5 —
have no remaining core-side blocker** … **Six** stay blocked on two causes". The report's *claim*
(nothing changed) is correct; the two numbers are swapped against their labels. Development-record
file, not normative, but it is the kind of number a later scoping copies.

### Minor 3 — positional locators in the new prose

`src/publishable/cli.py:1076` and `1095` ("the guard at the **top of this function**", twice),
`cli.py:1171-1172` ("the weighted block **beside it**"), `tests/test_cli.py:3324` ("the
parametrized table **above**"). `CLAUDE.md`'s rule is written about table rows but the failure mode is the same — seven
instances, wrong twice, falsified by insertions that moved them. Naming what the sibling *does*
(e.g. "the weighted-clustered guard") costs nothing here.

### Minor 4 — the derived arm writes `n_paired_clusters` beside a null interval, and nothing records that for task 14

`src/publishable/cli.py:1167-1177` writes the count under `if clusters is not None:` regardless of
`is_derived`. The comment at 1168-1174 claims the derived arm is unreachable under a declared
cluster; **I checked its grounds and they hold** — `resample_fns` is built for *every* derived key
whenever `derived` is truthy (`cli.py:2288-2292`), `resample_seed_value` is always an `int`
(`cli.py:2029`), so `summarize_step`'s `drawable` test (`stats.py:2204-2220`) always fires and the
`except ContractError` retry (`cli.py:2322-2330`) drops the whole derived mapping. Verified by
reading that chain; a direct call bypassing `summarize_step` does reach the arm and writes
`n_paired_clusters: 3` beside `ci95: None, method: None`.

So no live defect. What is worth recording: batch 1 asked **task 14 to re-check the derived corner
when `E-DATA-CLUSTER-CONTRAST` retires** (ledger, Major 2 ruling), and that corner now has one more
consequence — a cluster count written beside a null interval — which is named nowhere. One sentence
in task 14's brief closes it.

### Minor 5 — four threading sites, one mutation

Task 10 mutation 1 covers `_compute_vs_baseline`'s call site only. **Verified by running**: dropping
`clusters=clusters` at *all four* sites simultaneously — `cli.py:1309` (`_compute_vs_baseline`),
`cli.py:1387` (`_compute_declared_contrasts`), `cli.py:2785` and `cli.py:2802` (`command_run`'s two
calls) — **plus** widening the percentile membership, leaves the suite at **2196 passed, 1 skipped,
2 xfailed**. Blindness is expected while the refusal is alive and the batch says so; the scoping
risk is that task 14 is told about one site and inherits four. This is the `E-TEMPLATE-UNKNOWN`
shape (a diagnostic scoped by one call site). Task 14's brief should name all four.

---

## What I verified by running

| Claim | Mutation | Result |
|---|---|---|
| **The *t* arm selects the clustered construction** (task 10 mutation 2, unrun by the batch's own report until here) | `cli.py:1098` `if col_clusters is not None:` → `is None` | **60 failed**, including **both** named tests in opposite directions: `test_a_clustered_column_contrast_takes_the_cluster_robust_t` and `test_an_unclustered_column_contrast_is_untouched`. The *t* site's two branches are provably different — the arm the percentile mutations say nothing about |
| The clustered corrected bound is the clustered construction | `correction.py:250` `member.clusters is not None` → `is None` | **57 failed** including `test_a_clustered_members_corrected_bound_is_the_clustered_construction`; matches the report's "named test + 56 collateral" |
| **The clustered corrected call's α is threaded** (H4b-1's silently-unpinned α, one axis over) | `correction.py:252` `confidence=1.0 - level` → `confidence=0.95` | **1 failed** — exactly that test, `Expected: 20.213931212789273`. **The α is pinned**; H4b-1's failure did not recur |
| The six-cell table catches a fall-through at the cell | task 11 mutation 1, `method=` first arm inverted | **2 failed**: the `(False, True, True)` cell and `test_a_clustered_resampled_contrast_really_drew_clusters`. Other five cells pass — the table discriminates per cell, not globally |
| `n_paired_clusters` counts the column, not the roster | task 13 mutation 1, `cluster_count_of(clusters, clusters.keys())` | **1 failed**: the ragged test, `assert 3 == 2`. The un-ragged test passes — the dimension only the ragged fixture can see |
| Task 11 mutation 3 is genuinely blind (**overturn attempt**) | widened membership + a ragged, resampled direct call to `paired_percentile_of_derived` with `col_keys` = 10 of 12 and cluster `a` absent | Identical `Interval` **and identical pool**. The blindness is structural: `stats.py:1405-1409` builds `by_cluster` by walking `keys`, so a wider mapping contributes no pool. Unlike batch 2's, this claim survives |
| Both weighted-clustered cells are removed by the refusal, not by omission | direct call with `weights` + `clusters` at `resample_columns` both `False` and `True` | Both raise `ValueError`. The guard sits at `cli.py:905`, ahead of every branch, so one site removes both cells |
| `E-DATA-CLUSTER-CONTRAST` alive | `pytest tests/test_validate.py -k cluster` | 67 passed. `test_validate.py:7577` asserts the code for a `vs_baseline`-only design ("publishes 2 comparisons"), `:7618` asserts the weight-cluster code **alongside** it |
| The fixture's five half-widths | independent hand computation of the CR1 sandwich | mean 76/12 = 6.3333; per-cluster residual sums −10.6667 / −5.3333 / 16.0; `se` = √(398.222/144 × 3/2) = 2.036693; × t(.975, 2) = **8.76321**; unclustered **1.97854**; wrong-df 4.4827; IID-variance 3.8680. All five agree with the plan and are mutually distinguishable — this is **not** the "correct and buggy cluster counts are both 3" fixture, because the ragged case separates 3 from 2 |

## The consistency passes

**Not applicable, and verified rather than assumed.** The batch's five commits touch
`src/publishable/cli.py`, `src/publishable/correction.py`, `tests/test_cli.py`,
`tests/test_correction.py`, `task-10-13-report.md` and `progress.md` — **none of the four
documents**, so neither the mechanical nor the cross-document pass is owed. The mechanical checks
that apply to any file were run anyway over all five changed files: no trailing whitespace, no tabs,
no stray `x` for multiplication. `docs/reference.md` § Contrasts was read but not edited, and the
shipped record shape matches it (§ Contrasts' `n_paired_clusters` example, the absent-not-null rule,
and `cohens_d` explicitly outside the move-together set).

## On the report's "no brief/code disagreements" claim

Treated as a hypothesis and checked at the interfaces batch 2 produced. All four match what tasks
10–13 consume, **verified by reading the definitions**: `stats.paired_t_over_units_clustered(diffs,
labels, confidence=0.95)` (`stats.py:435`), `paired_percentile_of_derived(..., method=, clusters=)`
(`stats.py:1295-1307`), `units.cluster_count_of(membership, keys)` (`units.py:2439`),
`units.clusters_of` (`units.py:1140`) and `command_run`'s roster-wide `clusters = clusters_of(roster,
cluster_by)` (`cli.py:1683`). **The claim stands.** The one elaboration the report declares — pasting
the real `[1.0, 8.0]` over the brief's `[0.0, 0.0]` placeholder — is correct and is in the shipped
test.

The `ValueError` guard's own safety argument (`cli.py:900-905`: "validate refuses the combination and
`cli` always validates before running") was checked rather than taken: `resolve_contrasts`
(`contrasts.py:186-207`) returns **vs_baseline comparisons as well as declared ones**, so
the `comparisons > 0` test at `validate.py:5014` (the cluster guard) and at `validate.py:5051-5057`
(the weight-cluster guard) covers both record shapes. The `ValueError` is genuinely
unreachable, not a crash deferred to task 14.

## What I could not check

- **Task 14's half.** Whether the threading actually reaches `run.yaml` cannot be shown from this
  batch — `E-DATA-CLUSTER-CONTRAST` gates every `run`-through fixture, which is the batch's own
  stated convention. Minor 5 is the residue.
- **The derived-arm unreachability** is established by reading a four-hop chain
  (`resample_fns` → `seed` → `drawable` → the retry), not by a `run`-through fixture. A config that
  makes `template.aggregate` return a derived metric under a declared `cluster_by` would settle it
  by execution; task 14 will have one.
- I did not re-verify `_drawable_content`'s degenerate-draw refusal (batch 2's task 9), which the
  `[1.0, 8.0]` endpoints pass through.

## Tree state

**Clean.** Every mutation was reverted by editing the file back — never `git checkout --` —
`__pycache__` cleared between runs, and the revert confirmed **by behaviour**: `git status --short`
empty, four gates green, `2196 passed, 1 skipped, 2 xfailed` on the final full run. No `ENOSPC` was
hit; no `pytest-of-*` directories needed clearing.
