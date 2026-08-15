# Task 11 report — the wiring

**Status: complete, with one deliverable found to be a no-op and reported rather than worked
around.** Two commits on `h3b-clustered-units-and-partitions`: `c43e02b` (`feat: a declared cluster
decides the fold's membership and the column's interval`) and `42df52d` (`test: name which task pins
the fold count and which pins its membership` — a stale docstring in task 5's test, which said a
later slice would wire the mapping). `.superpowers/sdd/` and `docs/superpowers/` are gitignored, so
neither this report nor the spec-defects entry is in either commit.

`uv run pytest` **1377 passed + 2 xfailed** (was 1354 + 2; +23 tests). `uv run ruff check .` and
`uv run mypy` green. `ruff format .` **not** run.

No `*.md` among the four documents was edited — see § What was deliberately not done.

## 1. The partition: both arguments, at one call

`cli.py`'s fold step now reads

```python
        partitions = partition_units(
            roster, fold_level.n, digest, clusters=clusters, strata=strata
        )
```

- **`clusters`** is the `clusters_of` mapping `cli` already built for `n.clusters` and `attrition`,
  passed whole. Task 4's rewrite is now reached by a run.
- **`strata`** is built at the call site, `{u.key: str(u.attributes[stratify_by]) for u in roster}`.

**The strata mapping does not reuse `clusters_of`**, per task 7's concern 1: that function raises
`E-DATA-CLUSTER-UNKNOWN`, which would name the wrong declaration for a reader whose config declares
`fold.stratify_by`, and which code a missing value belongs under is a property of the declaration
being served (`holdout` and `assign` will each read the same attribute under their own).

**Totality (task 7's concern 2) is guaranteed, not assumed, so the lookup is indexed.**
`units._from_table` builds `Unit.attributes` as `{a: row[a] for a in attrs}` for *every* row, and a
`glob` source refuses an `attributes` declaration outright (`E-UNITS-ATTR-MISSING`), so every unit
carries every declared attribute; `validate` guarantees the name is one of them
(`E-REPL-FOLD-STRATIFY-UNKNOWN`). A blank CSV cell is therefore stratum `''` — a real stratum of its
own, which is what the source says it is. **One exception, found after the fact and named in the
code rather than guarded:** `units.collapse_measurements` rebuilds `attributes` and drops the name
equal to `data.units.measurements.by`, and nothing refuses an `attributes` entry of that name — so a
config stratifying on the measurement axis itself would reach a bare `KeyError` (verified: the
collapse really does drop it). Unreachable today, since `E-REPL-FOLD-STRATIFY-UNSUPPORTED` refuses
every `stratify_by`; **task 12 should decide whether it gets a coded refusal**, because a coded one
is a § Validation row and an § Errors entry, which belong with the retirement rather than here. **No `"no value"` sentinel was introduced**: it would
merge blank-cell units into whatever real stratum happened to be spelled the same way, and it would
be a second notion of what a stratum is. A missing key is a core defect and drops out as `KeyError`,
which is exactly the contract `partition_units`' docstring already states. This is the same stance
`cli` takes for the weights, and the comment cites the same guarantee.

**`stratify_by` now rides `RepeatLevel`** (`replication.py`), set only for a `fold` and only when
truthy. `resolve_repeats` is already the single reader of a level's declaration — it is what turns
`k: all` into a count — and a `cli` walking `replication.repeats` again to find the same level would
be a second answer to which level is the fold and what it stratifies on. The field is defaulted, so
every positional `RepeatLevel(...)` in the tests is unaffected.

## 2. The interval: `t_over_units_clustered` **and** a weighted sandwich that had to be decided

All three `summarize_step` call sites in `cli.py` (the first call, the collision retry, and the
`report_by` level block) **already passed `clusters`** — task 8 wired that for `n.clusters`. So this
half is one change inside `stats.summarize_step` rather than three at the call sites, and the
per-call-site mutation the brief asked for is one mutation with the same reach. The branch is now
four-way, over the column's own keys taken in the same pass as its values:

| declared | value | interval |
|---|---|---|
| neither | `mean_of` | `t_over_units` |
| `cluster_by` | `mean_of` | `t_over_units_clustered` |
| `weight_by` | `weighted_mean_of` | `weighted_t_over_units` |
| both | `weighted_mean_of` | `weighted_t_over_units_clustered` |

`n.effective` survives on the fourth row — Kish's size is a fact about the weighting, not about the
construction, and § Weighted samples has `effective` and `clusters` both join `n`. That line is the
easy casualty of a four-way branch, and it is asserted at both the function and the run.

### The branch point task 9 found: `weight_by` + `cluster_by`. **Built, not refused.**

Task 9 left this open as "underspecified — a weighted CR1 needs either Kish's effective size or
clusters − 1, and the documents name neither". On the evidence it is **determined**, and refusing it
would have been expensive:

1. § Weighted samples names the combination among its *"four interactions worth knowing"* — this is
   a documented pair, not an accident. Refusing it costs **every `basis: units` interval** in such a
   run, which is the whole column-metric surface.
2. § Weighted samples decides the **draw**: *"`cluster_by` still decides the draw when both are
   declared, since a cluster is what's independent and a weight is what it represents."*
3. § Statistical reporting decides the **df**: it gives the clustered form *"df = clusters − 1"*
   unqualified, and a df is a property of the draw. **Kish's size enters nowhere.** That mixing is
   the actual incoherence task 9 smelled, and it is what the construction refuses.
4. The estimate is the weighted mean, by the same sentence's second clause.

`stats.weighted_t_over_units_clustered(values, keys, membership, weights, confidence=0.95)`:
`S_g = Σ_{i∈g} w_i(v_i − v̄_w)`, `V = [G/(G−1)] · Σ_g S_g² / (Σw)²`, `half = t(G−1)·√V`.

**The check that settles it is the reduction:** at `w ≡ 1`, `Σw = n` and each score collapses to the
residual sum, so this is `t_over_units_clustered` **digit for digit** — asserted as exact equality,
not `approx`, so a scaling factor too small for `approx` cannot hide. Nothing had to be corrected
for, unlike `weighted_t_over_units`, whose `Σw − Σw²/Σw` denominator exists to buy the same
property. This is task 10's stance applied to the *t* form: a composition of two documented
sentences, with an exact boundary identity, rather than an invention.

The expectations are independent of the module: computed as **exact rationals** in a scratch script
(`Fraction`), then rendered — `Σw = 12`, `v̄_w = 23/12`, `Σ S_g² = 3607/72`, se = 0.7223891, df 2 —
and the module agreed to the last digit. Rescaling invariance is asserted (weights ×100 give the
identical interval), as is the `checked_weights` gate (`E-DATA-WEIGHT-INVALID` on a zero weight) and
`strict=True` on the three-way zip.

**Method name:** `weighted_t_over_units_clustered` is a string § Statistical reporting's method table
does not define — the same class task 10 recorded for `percentile_over_units_clustered`. **Appended
to the same `docs/superpowers/spec-defects.md` entry** with a proposed row, so task 13 lands one doc
edit covering both.

## 3. The clustered percentile draw: **there is no call site to wire, and I did not build one**

`percentile_over_units_clustered` (task 10) has **no caller in `src/` outside `stats.py`** —
re-verified here, independently of task 10's finding: `percentile_over_units` itself has none
either, because the only route to it is `statistics.resample`, which
`E-STATS-RESAMPLE-UNSUPPORTED` still refuses. The brief's item 3 ("at the `summarize_step` site that
uses it") names a site that does not exist. Nothing was worked around: the derived draw that *does*
run unconditionally is `percentile_of_derived`, whose clustered form is a different construction and
does not exist, and per the user's ruling task 12 refuses that combination by name. **No clustered
derived draw was wired, and none was built.**

What I did add is the note where the next reader will be: `summarize_step`'s docstring now says in
those words that a derived metric's interval is *not* clustered, that this is a gap rather than a
decision, and that the slice retiring `E-DATA-CLUSTER-UNSUPPORTED` owes a refusal of that
combination in its place.

## Tests (22 new)

**`tests/test_cli.py` — end to end, over a real run, which is what was unproven.** Fold membership
is observable: a `repeat`-scope step is handed only its own fold's units, and the generated step
records one row per unit, so each fold's `units.parquet` **is** its membership. `_fold_membership`
reads it through `artifacts._decode_parquet`. `sweep.yaml` carries fold labels only, which is why
task 5 could assert the count and not the membership.

| Test | Asserts |
|---|---|
| `test_a_clustered_folds_units_reconcile_in_the_record` | over the same uneven 7/4/4 partition: `resolved == completed + ineligible + failed`, `completed == 15` (every unit in exactly one fold), and the uneven sizes as the control that must report |
| `test_a_clustered_fold_puts_no_cluster_in_two_folds` | exact membership `{fold01: a's 7 units, fold02: b+d, fold03: c+e}` **and** the property (no cluster in two folds, every unit once) asserted separately, so a redrawn digest still fails for the right reason |
| `test_an_unclustered_fold_of_the_same_roster_splits_a_cluster` | the control that must report: cluster `a` in **all three** folds, folds 5/5/5 |
| `test_a_stratified_fold_balances_the_declared_stratum` | 10+4 labels at `k = 2` → `(5, 2)` and `(5, 2)`, plus totality |
| `test_an_unstratified_fold_of_the_same_roster_is_lopsided` | the control: `(4, 3)` and `(6, 1)` |
| `test_a_clustered_run_reports_the_cluster_robust_interval` | `method` **and** both endpoints `[0.38426, 13.61574]`, `n.clusters: 5`, and the `resolved == completed + ineligible + failed` reconciliation |
| `test_an_unclustered_run_of_the_same_column_keeps_the_plain_interval` | the control: `t_over_units`, `[4.52341, 9.47659]`, no `clusters` key |
| `test_a_weighted_clustered_run_reports_the_weighted_sandwich` | `weighted_t_over_units_clustered`, value 228/29, `[1.74598, 13.97815]`, `n.effective` 11.21333 beside `n.clusters` 5 |
| `test_a_reporting_stratum_inside_one_cluster_reports_no_interval` | a stratum whose units are all one cluster reports its point with `ci95: null`, its sibling (4 clusters) reports `[6.46925, 14.53075]`, the parent keeps its own |

**Membership, never sizes** — the brief's warning is real in both places: the clustered and
unclustered draws of the interval fixture agree on nothing useful, but the *stratified* fixture had
to be chosen against the coincidence. My first stratum fixture (8 zeros + 4 ones at `k = 2`) gave
`(4, 2)`/`(4, 2)` **both stratified and not**, i.e. an unstratifiable test — task 7's lesson landing
again one slice later. Probed six label distributions and took 10+4, whose unstratified draw is
genuinely lopsided; mutation 2 below confirms the fixture discriminates at the digest the stratified
config actually produces.

**`tests/test_stats.py`** — 9 for `weighted_t_over_units_clustered` (the exact reduction at `w ≡ 1`;
the hand-computed unbalanced sandwich with the unweighted one as the control that must differ; df
from the cluster count with Kish's 4.5 named as the rival and the standard error rebuilt from the
scores so neither assertion is vacuous; rescaling invariance; the two-cluster floor with a
*Kish-below-two but three clusters* control that still reports, which is the visible consequence of
the df decision; the two-value floor; the weight gate; the strict zip) and 4 for `summarize_step`
(the column's interval becomes clustered, over its **own** units with the whole-table rival asserted
to differ; the unclustered regression; the weighted-and-clustered branch with both single-declaration
controls; the single-cluster column reporting a point with no interval).

## Mutations (six, each separately, `__pycache__` deleted between every mutation and its revert; reverts verified by `diff` against pre-mutation copies **and** by the full suite, never `git status`)

| Mutation | Result |
|---|---|
| Drop `clusters` from `partition_units` | **FAIL, exactly 1**: `test_a_clustered_fold_puts_no_cluster_in_two_folds`. The unclustered control passed, as it must |
| Drop `strata` from `partition_units` | **FAIL, exactly 1**: `test_a_stratified_fold_balances_the_declared_stratum`, landing `(4, 3)`/`(6, 1)` — the unstratified composition, which is also what the control pins. The fixture is not coincidence-prone at this digest |
| Unweighted branch back to `t_over_units` | **FAIL, 4**: the clustered run, the `report_by` stratum, and both `summarize_step` tests |
| Weighted-and-clustered branch back to `weighted_t_over_units` | **FAIL, 2**: the weighted run and the weighted `summarize_step` test |
| Weights dropped from the cluster scores (mean only) | **FAIL, 4** — the reduction test **passed**, correctly: at `w ≡ 1` the two coincide, which is why it is not the headline |
| Weighted df from Kish's effective size | **FAIL, 4**, including the reduction test (Kish's size is `n` there only when weights are equal — it fails on the fixture with 6 values and df 2 vs 5) and the dedicated df test |

Each of the three wirings the brief named therefore fails a **named** test on its own, and the two
constructions' internals fail beyond the wiring.

## Bypasses: **two, and task 12 retires exactly two**

1. **`_without_the_cluster_refusal`** — task 5's, reused unchanged, filtering
   `E-DATA-CLUSTER-UNSUPPORTED` out of `run`'s own `validate` pass. Now called by six tests (was two).
2. **`_without_the_stratify_refusal`** — **new, and necessarily a second one**:
   `E-REPL-FOLD-STRATIFY-UNSUPPORTED` is a `raise` inside `replication._fold_k`, not a `validate`
   finding, so filtering findings cannot reach it. It monkeypatches `_fold_k` to drop the
   `stratify_by` key only; every other refusal that function makes still fires. Called by one test.

Two refusals, two mechanisms, two bypasses — neither is a duplicate of the other, and task 12 should
expect to delete both.

## The unclustered world did not move

`cohort-pilot` declares neither `cluster_by` nor a `fold.stratify_by`, and both wirings are gated on
the declaration: `partition_units` with `clusters=None, strata=None` is the call it was, and
`summarize_step` with `clusters=None` takes the same two branches it took. Pinned by
`test_an_unclustered_run_of_the_same_column_keeps_the_plain_interval`,
`test_an_unclustered_column_keeps_the_interval_it_always_had`, task 4's
`test_the_unclustered_draw_is_unmoved_by_the_clustered_rewrite`, task 8's
`test_an_unclustered_run_grows_no_clusters_key`, and the whole suite green — including
`tests/test_acceptance.py`, which recomputes an interval from `units.parquet` by hand.

## What was deliberately not done

- **No edit to the four documents.** Both declarations are still refused
  (`E-DATA-CLUSTER-UNSUPPORTED`, `E-REPL-FOLD-STRATIFY-UNSUPPORTED`), so `reference.md`'s "Nine
  declarations above are not yet built" and its `NOT BUILT` comments are still *true today*. They
  become false with the retirement, which is task 12's, and the count task 13 checks (seven) is the
  post-retirement one. Task 7's concern 3 assigned the § Validation rows and the NOT BUILT comments
  to "task 11"; on the tree as it stands they belong with the retirement, and moving them now would
  make the documents wrong for the length of one commit.
- **No refusal added anywhere.** Task 12 owns both refusals it inherited (the clustered contrast
  family, the clustered derived draw) and both retirements.
- **No clustered derived draw**, per § 3.
- `ruff format .` not run (the repo is not format-clean today, so it is not a gate here).

## Concerns / obligations for later slices

1. **A `report_by` stratum can legitimately lose its interval under clustering**, and it reads as a
   bug. A stratum whose completed units all sit in one cluster has one draw and no df, so `ci95` and
   `method` are `null` while the parent block keeps an interval. Tested and stated in the docstring.
   Whoever owns § Reporting strata may want a sentence there; it is a consequence of two documented
   rules meeting, not a defect.
2. **The derived-metric draw is the live hole — and task 13's step 7 attributes it to the wrong
   task.** That step ticks *Resampling clustered rows as if independent* off against task 10. After
   this slice it is **not** structurally impossible: task 10 built the clustered form of the
   **gated** path (`percentile_over_units`, reachable only through the still-refused
   `statistics.resample`), while the path that runs unconditionally is `percentile_of_derived`,
   which draws units. The row closes only when **task 12's refusal** lands — the same two-task split
   the brief already flags as the one to check hardest, in a second place. Every recorded column's
   interval is now clustered; a derived metric's is still `percentile_of_derived`, drawing units.
   Nothing reaches it today (`E-DATA-CLUSTER-UNSUPPORTED`), and task 12 must refuse it *by name* — a clustered
   run whose template derives a metric would otherwise get a 2000-draw unit-level percentile with
   nothing in the record to say so. Recorded in the docstring and in spec-defects.
3. **The contrast family is still unbuilt** (task 9's concern 2, unchanged): `vs_baseline` and
   `statistics.contrasts` under a declared `cluster_by` reach `paired_t_over_units` /
   `paired_percentile_of_derived`, neither of which knows about clusters. Task 12's second refusal.
4. **`validate` still has no per-stratum `k` bound** (task 7's concern 6), and it is now reachable
   by a run rather than only by a direct call: a `k` inside `fold_basis` but past some stratum's
   cluster count gives a fold holding none of that stratum. The partition stays total and visibly
   short, which is the pinned behaviour; the check does not exist.
5. **`E-DATA-CLUSTER-UNKNOWN` still has no § Errors *at run time* row** (task 2's debt, grown by
   task 8). `cli`'s strata builder adds no new raise site — it is indexed against a guaranteed-total
   attribute set — but `clusters_of` is now on the `run` path for the partition as well as for `n`.
6. **The brief was accurate except for its item 3**, which names a `summarize_step` site that uses
   `percentile_over_units`; there is none, and task 10 had already found the same thing from the
   other side. That is the fifth brief defect of the slice and, like task 10's, it is a conflation of
   two functions — `percentile_over_units` with `percentile_of_derived`. Item 3 is discharged as a
   verified no-op, not as work.
