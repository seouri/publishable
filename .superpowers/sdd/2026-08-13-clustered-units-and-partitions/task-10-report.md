# Task 10 report: the clustered percentile draw

**Status:** complete. `uv run pytest` (1354 passed, 2 xfailed), `uv run ruff check .`,
`uv run mypy` all green. `ruff format .` was not run.

**Commit:** `17ef816` — *feat: a declared cluster makes the cluster the percentile draw*
(`src/publishable/stats.py`, `tests/test_stats.py`). `docs/superpowers/` is gitignored, so
the spec-defects entry below is on disk but not in the commit.

## What was built

`stats.percentile_over_units_clustered(values, keys, membership, seed, draws=2000,
confidence=0.95, weights=None) -> Interval | None`, sitting between
`percentile_over_units` and `percentile_of_derived`.

Each replicate draws **`G` clusters with replacement and pools their units**, where
`G = units.cluster_count_of(membership, keys)` — task 2's and task 8's single authority, so
this cannot disagree with the `n.clusters` printed beside it or with a fold's partition. The
number of pools drawn from agrees with `G` by construction rather than by assertion: both
are the distinct values `membership` takes over the same `keys`, so there is no defensive
check to drift.

Two spellings that respect the groups and are still wrong, both refused by fixture rather
than by comment:

- **Drawing `n` units and repairing the groups afterwards** is a 300-draw interval however
  carefully the groups are respected. The document's own size statement is the test:
  *"300 cells from 10 animals give a 10-draw interval"*.
- **Averaging the drawn clusters' means** gives every cluster equal say. § Clustered units
  says "pools their units" and names the "varying row count" that follows, so a 3-unit
  cluster carries three rows and a 1-unit cluster one. The two coincide exactly on equal
  cluster sizes.

**Pairing.** Grouping happens *before* any sort and carries `(value, weight)` pairs, so a
value cannot part from its cluster or its weight. The pool is then sorted for the row-order
invariance `percentile_over_units` explains, and **clusters are ordered by their own sorted
contents, not by label** — which buys two things: a relabelled roster gives the identical
interval, and the one-unit-per-cluster case reproduces `percentile_over_units` digit for
digit (label-sorting would break that identity).

## The two design points, decided

### 1. The floor is two clusters — a derivation, not task 9's df argument

Task 9's floor rests on df = G − 1 being zero at G = 1. **That argument does not transfer**:
a percentile interval has no df. The floor is instead derived from the draw itself — at
G = 1 every replicate draws the same single cluster, so the resampled distribution is a
point mass, both ranks land on it, and the interval has **zero width**. § Statistical
reporting refuses exactly that: *"a zero-width 95 % interval is not [honest]"*, and *"at two
survivors the two ranks coincide and the 'interval' has zero width"*, with "reporting a
point with no interval is honest" as the alternative it prescribes. So the same number, 2,
for a different and independently sufficient reason.

`len(values) < 2` is kept in front of it (parity with `percentile_over_units`' own floor),
and `draws < min_honest_draws(confidence)` is orthogonal to both — that one is about how
many *replicates* the ranks are read off, not how many things each replicate draws.

**There is deliberately no higher threshold on `G`.** G = 3 reports. The judgment that a
cluster count is too small for a resample is already assigned elsewhere:
`statistics.min_clusters: 10`, *"`validate` warns when `resample` would draw fewer than
this"*. A second threshold in `stats.py` would be a competing authority for one judgment.
The docstring says so, because a reviewer will otherwise ask.

### 2. `weight_by` + `cluster_by`: implemented, and here is why that is not invention

Task 9 refused the combination for the *t* form because its underspecification is the
**df** — a weighted CR1 needs either Kish's effective size or clusters − 1 and the documents
name neither. A percentile has no df, so the only free choice left is which statistic is
recomputed, and § Weighted samples answers that **unqualified by what the draw is**: a
percentile interval *"recomputes the weighted statistic on each draw, so the weights are in
the estimate rather than in the drawing"*. The cluster sentence — *"`cluster_by` still
decides the draw when both are declared, since a cluster is what's independent and a weight
is what it represents"* — moves only the draw, and its reason clause is itself a statement
that the two live in different places. So: **the draw is by cluster, the statistic is the
weighted mean over the pooled units**, and a cluster drawn twice contributes its units'
weights twice (the only reading of "pools their units"). `checked_weights` gates once before
grouping, for the reason the unclustered weighted branch states.

Answering the brief's question directly: the sentence tells you what the *draw* does; what
tells you what the *statistic* does is the other sentence in the same section, and the
composition is of two documented sentences rather than one invented rule.

**Asymmetry task 11 must reconcile:** under this decision a run declaring both gets a
weighted clustered *percentile* while its column metrics still hit task 9's unbuilt weighted
CR1. Building one and refusing the other in the same `run.yaml` is a choice task 11 has to
make explicitly.

## Fixture design — three coincidences avoided, and the near-miss

The brief names singleton clusters. Two more would have hidden the work, and one of them
bit during construction:

- **Four clusters, not three.** With G clusters a replicate is G draws, so the
  all-one-cluster replicate has probability G⁻ᴳ: 1/27 at G = 3, which is *above* the 2.5 %
  tail. A first fixture at G = 3 therefore pinned both endpoints onto the achievable set's
  **extremes** — and at the extremes "pool the units" and "average the cluster means"
  coincide, so the cluster-mean mutation reproduced the correct endpoints exactly (4.0 /
  15.0 on every seed). This is task 7's lesson in a new place: the coincidence was in the
  *tail probability*, not in the sizes. At G = 4 it is 1/256, both ranks land interior, and
  the two constructions separate (6.0 / 14.0 vs. 7.2 / 157⁄11).
- **Unequal cluster sizes** (1, 2, 3, 2) — equal sizes make pooling units and averaging
  cluster means the same estimator.
- **Interleaved value ranges** — B spans [0, 22], C spans [2, 31], A's single 4.0 sits
  inside both. Clusters whose ranges are disjoint and ascending re-pair to themselves under
  a separate sort, so mutation 2 would be the identity on them.

**The oracle is enumeration, not a captured float.** A 4-cluster replicate is one of the 35
multisets drawn with replacement, each with an exactly computable pooled mean (34 distinct
values). The headline asserts both endpoints **exactly**, as `_pooled(("A","A","A","D"))`
and `_pooled(("B","C","C","C"))` computed in the test from the cluster declaration, **and**
as members of that enumerated set — which is what makes the unit-drawing mutation fail
structurally rather than by two numbers happening to differ. Checked across seeds 7, 1, 42,
99, 2026, 13: the same two endpoints, interior, in-set on every one.

Controls that must report: the unclustered `percentile_over_units` over the same eight
values ([5.25, 19.0], neither endpoint achievable by any whole-cluster replicate); the
G = 2 case (reports, non-zero width); the rival mean-of-means set (non-empty, and the
endpoints are absent from it); the re-paired construction ([2.0, 65⁄3], interval-shaped and
unachievable); and the unweighted clustered interval beside the weighted one.

One honest note recorded rather than tidied: `test_the_same_seed_reproduces_the_clustered_percentile`
carries only the reproducibility half, not the usual "a different seed moves it" — 4
clusters have 35 achievable replicates and this roster's endpoints are the same two on every
seed tried. That discreteness is the clustered draw telling the truth. The
different-seed half is asserted on a separate 25-cluster roster.

## Mutations (run separately, `__pycache__` deleted between each, reverts verified by behaviour)

| Mutation | Result |
|---|---|
| Draw `n` **units** with replacement from the flat pool | 3 tests fail (headline, pooling, weighted) |
| Sort values and cluster labels as **separate sequences**, then group | 5 tests fail (adds the pairing test and the invariance test) |
| Draw `G` clusters but average their **means** | 4 tests fail (adds the equal-weights boundary) |

All three reverted from a pre-mutation copy; the full suite is green afterwards, verified by
running it, not by `git status`.

## Not done here — what task 11 must pass, and where

- **Nothing is wired.** `summarize_step` still calls `t_over_units` /
  `weighted_t_over_units` and `percentile_of_derived`; `clusters` there still only adds
  `n.clusters`. `percentile_over_units` is byte-identical, and its pin
  (`test_an_unweighted_percentile_interval_is_untouched_to_the_last_digit`, low = 20.4 /
  high = 28.54) still holds — `cohort-pilot` declares no `cluster_by` and nothing about it
  moved — verified by the full suite running green, which includes that test.
- **`weights` is built-and-ready, not built-and-wired, and task 11 should not read the next
  bullet as an instruction to pass weights from `summarize_step`.** Under that function's
  current shape there is **no branch that reaches this function with weights at all**: a
  column metric's clustered interval is `t_over_units_clustered` per § Statistical
  reporting's first table, whose weighted form task 9 refused as underspecified; and the
  derived path is unweighted by design, as `summarize_step`'s own docstring states at length
  ("A DERIVED metric is not weighted here… the weight column reaches `aggregate` as a unit
  attribute and the template decides"). The parameter exists because the composition is
  determined by the documents (above) and because whichever slice builds the clustered
  *derived* draw or a weighted contrast will want it — not because a caller can use it
  today. This sharpens concern 1 rather than replacing it: the clustered percentile has no
  reachable caller yet, weighted or not.
- **What a caller must pass:** the column's own `values` **and its own unit keys**, aligned
  in one pass — `summarize_step` already holds both as `carried`'s two elements — plus the
  roster-wide `clusters` mapping it already receives, **passed whole** (no pre-resolved
  label vector, so alignment cannot drift), plus a `seed` (`resample_seed(digest)`, as the
  derived path uses) and `draws`. Weights, when declared, are the same per-column vector
  `weighted_t_over_units` gets.
- `E-DATA-CLUSTER-UNSUPPORTED` in `validate.py` is untouched — task 12's.

## Concerns

1. **The brief's motivation attaches to a different function than its deliverable.** The
   brief argues urgency from `cli`'s hard constant `derived_metric_draws = 2000`, which is
   correct — but that constant drives `percentile_of_derived`, not `percentile_over_units`.
   Verified: `grep -rn "percentile_over_units(" src/` returns **no call site outside
   `stats.py`** (`statistics.resample` is unbuilt, so the column percentile is unreachable
   today). So the interval that will actually be wrong for a clustered design the moment
   task 12 lands is the **derived** one, whose clustered form is a *different construction*
   — each replicate drawing `G` clusters and building a `UnitTable` from their pooled units,
   which `unit_table_from_rows` already supports — and **it does not exist**. Task 10's
   deliverable is right and needed; it is not sufficient for the motivation the brief gives
   it. Task 11 cannot wire what isn't built, so either task 11 grows that construction or
   task 12 must keep refusing `cluster_by` where a derived metric is resampled. The same
   applies to `paired_percentile_of_derived`, which `cli.py` calls directly.
2. **`percentile_over_units_clustered` is a name the documents do not contain.** §
   Statistical reporting's first method table (`t_over_units`, `t_over_units_clustered`,
   `percentile_over_units`, `t_over_repeats`) has no clustered-percentile row; the
   `_clustered` suffix rule is stated only in the paragraph under the *contrast* table,
   whose "Same rule and same reason as `t_over_units_clustered` above" is what makes it
   general. Chosen deliberately rather than silently, and **recorded in
   `docs/superpowers/spec-defects.md`** ("The method table has no row for a clustered
   percentile…") with a proposed fifth row, together with concern 1. Whoever owns the doc
   edit should land it with the wiring — `method` exists so two readers of one `run.yaml`
   agree on what they hold, and it currently names something no table defines.
3. **`_clustered` is still a family, not two functions.** After tasks 9 and 10 the column
   *t* and the column percentile exist. The contrast forms § Statistical reporting names —
   `paired_percentile_over_units_clustered` (jointly across both sides),
   `unpaired_…`, `paired_t_…`, `welch_…` — do not, so contrasts under a declared
   `cluster_by` remain unimplemented.
