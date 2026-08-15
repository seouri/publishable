# H3b Clustered units and partitions design

**Goal:** `data.units.cluster_by` and a `fold` level's `stratify_by` execute — whole clusters go to
one side of a split, `n` reports how many clusters there were, and the intervals become
cluster-robust — retiring `E-DATA-CLUSTER-UNSUPPORTED` and `E-REPL-FOLD-STRATIFY-UNSUPPORTED`.

**Why second among H3's four:** H3a never touched `partition_units`. H3b rewrites it once, for
clusters; H3c rewrites it once more, for cells, on top of that; H3d consumes both rules. Any other
order rewrites an earlier slice's rule. That ordering *is* why H3 is four slices rather than one.

## The sentence that forces the slice's shape

`reference.md` § Clustered units, on the partition rule:

> **`cluster_by` also constrains how `fold` partitions.** Whole clusters go to one side of a split;
> a cluster is never divided between train and test. **This is not a refinement of the interval,
> it's the difference between a valid evaluation and a leaky one**: with 300 cells from 10 animals
> split without regard to `animal_id`, every fold trains on other cells of the animal it tests on,
> and the metric is inflated before any interval is computed — so cluster-robust standard errors
> don't repair it. Core computes the partitions, so this has to be core's rule rather than something
> each experiment remembers.

Two consequences the design takes from it. The partition rewrite is **correctness, not refinement**,
so it cannot be deferred behind the interval work. And the leak happens **before** any interval is
computed, so a slice that shipped cluster-robust intervals over an unclustered partition would have
delivered the cosmetic half and left the load-bearing half undone.

## What the scoping measured, against the charter

`docs/superpowers/H3b-SCOPING.md`. The charter in `docs/superpowers/H3-SCOPING.md` was wrong on four
counts and silent on a fifth.

| Charter | Measurement |
|---|---|
| 4 blocked § Validation rows | **3 owned** — *Clustering looks undeclared*, *Folds fit inside the clusters*, *Fold strata survive clustering*. *Stratification attribute exists* is shared three ways: it names no `stratify_by`, so `fold.` is H3b's, `assign.*.` H3c's, `holdout.` H3d's |
| (silent) | ***Leave-one-out is affordable* is already implemented and H3b makes it wrong.** `k: all` stops meaning one unit per fold and starts meaning leave-one-*cluster*-out. A regression to fix, not a row to write |
| (silent) | **No *Cluster attribute exists* row exists**, though H3a wrote the parallel *Weight attribute exists*. The document owes it |
| "Immediately unblocks two of H4's dependencies" | Both rows are **double-blocked** by `E-STATS-RESAMPLE-UNSUPPORTED` and `E-STATS-NULLTEST-UNSUPPORTED`, which are H4's own. Neither becomes writable. "H4 after H3b + H3c" survives; "immediately unblocks" does not |
| (assigns the draw to H4) | **`derived_metric_draws = 2000` is a hard constant in `cli`** — the derived-metric percentile interval draws *unconditionally*, ungated by `statistics.resample`. Un-refusing `cluster_by` makes an **already-running** interval wrong |

Row titles are cited above and throughout because H3-SCOPING's row *numbers* are already stale — the
§ Validation table grew during H3a. This is `CLAUDE.md`'s own "cite by section, never by line number"
rule arriving as a concrete failure for the second time in H3.

## Scope

| In | Deliberately not here |
|---|---|
| Cluster resolution as one authority | `allocation`, `groups`, `assign` (H3c) |
| `partition_units` drawing **whole clusters**, and honouring `stratify_by` | `holdout` (H3d), which inherits both this rule and H3c's |
| `k: all` as leave-one-**cluster**-out, and the affordability row it breaks | `statistics.resample`'s and `null_test`'s own cluster rules — both still refused by H4's codes |
| `n` gaining `clusters` | The clustered **contrast** family — see decision 2 |
| `t_over_units_clustered` (CR1, df = clusters − 1) and the clustered percentile draw | `limits.min_clusters`'s warning, which § Validation ties to `resample` |
| `W-DATA-CLUSTER-UNDECLARED`, and the *Cluster attribute exists* row the document owes | |
| The `cluster_by` × `measurements` check — see decision 3 | |
| Both retirements | |

## Architecture

**Cluster membership is resolved once, beside the roster.** H3a established the shape: `resolve_units`
returns `(UnitList, technical_n | None, columns)` and `technical_n` travels **beside** the roster
rather than on it, because `io.units` is documented as exactly three operations plus `.train`. Cluster
membership takes the same route — a mapping resolved once and passed to the partitioner and the
statistics, never an attribute of `UnitList`.

**`partition_units` is rewritten once, and parameterised for its two later callers.** Today it is a
shuffle plus a stride-slice. It becomes: group units into clusters, shuffle *clusters*, then assign
whole clusters to folds. H3c will need the same function to draw within cells and H3d to make an
uneven two-way split, so the rewrite is shaped for those rather than against them — but H3b builds
only what it can test.

**What balances is unit count, not cluster count.** The existing docstring's promise is that "sizes
differ by at most one, so no fold is systematically smaller than its neighbours". Under clustering
that promise cannot be kept exactly — clusters are indivisible — so it becomes *as even as
indivisible clusters allow*, by greedy assignment to the currently-smallest fold. The docstring must
say the weaker thing rather than keep claiming the stronger one.

**The constructions take a `_clustered` suffix and read the cluster as the draw.** § Statistical
reporting: `t_over_units_clustered` is CR1 — the sandwich estimator with the standard finite-sample
scaling — with **df = clusters − 1**, and the percentile forms **resample whole clusters**. The
document is emphatic about which part matters: *"The df is the part that bites — 10 animals give 9,
not 299."*

**The single authority pattern H3a proved carries forward.** `units.usable_weight` and
`units.is_measurement_numeric` are each read by `validate` and by `stats`, so a config that validates
cannot crash on a value `validate` approved. Cluster resolution gets the same treatment: one function
answers "which cluster is this unit in", read by the partitioner, the statistics and the checks.

## Decisions

| # | Decision | Ruling | Grounds |
|---|---|---|---|
| 1 | Does H3b own the clustered intervals, or defer them? | **Owns the single-condition pair** — `t_over_units_clustered` and the clustered percentile draw | *Settled by the user.* The derived-metric percentile draw runs unconditionally today, so un-refusing `cluster_by` makes a live interval wrong. And § Clustered units opens by promising cluster-robust intervals; shipping the declaration without them accepts a declaration whose principal effect is undelivered — this project's recurring first risk |
| 2 | The clustered **contrast** family | **Refused by name, deferred to H4** | § Statistical reporting extends the `_clustered` suffix to `paired_*` and the unpaired forms, "jointly across both sides when paired" — a second estimator family. Exactly H3a's shape: it shipped the single-condition weighted case and minted `E-DATA-WEIGHT-CONTRAST` for the combination. H4 owns the contrast family and already owes the weighted one |
| 3 | `cluster_by` × `measurements` | **A check, not only a documented rule** — and it closes H3a's open weight gap with the same machinery | H3a met this for weights and closed it with a document sentence, because it surfaced at whole-branch review. Here the consequence is different in kind: a mis-collapsed weight mis-sizes a contribution, a mis-collapsed cluster **decides which side of a split a unit lands on**, which is the leak § Clustered units calls "the difference between a valid evaluation and a leaky one". Reproduced: replicate rows declaring `S1` and `S2` collapse to `S1` by the `first` fallback. See § Where the constancy check lives |
| 4 | Where the `k: all` fix lands | **With the partition rewrite, not with the affordability row** | `k: all` resolving to a cluster count is a property of the partitioner. The § Validation row is a consequence, and a row edited without the behaviour would describe code that does not exist |
| 5 | `limits.min_clusters` | **Out of scope** | Its § Validation row ties the warning to `statistics.resample`, which stays refused by H4's own code. Building it here would be a check no config can reach |

## Where the constancy check lives

Decision 3 asks for a check, and the obvious place cannot host it. **`validate` reads the
post-collapse roster** — `resolve_units` collapses internally — so by the time any validate-time
check sees a unit, the varying values are already gone. That is precisely why H3a could only state
the weight rule rather than enforce it.

`collapse_measurements` is the one place that holds the pre-collapse values: it groups rows by key
and already has each group in hand. So the check belongs there, told which columns must not vary —
`cluster_by`'s, and `weight_by`'s.

Two consequences worth stating so a task does not rediscover them:

- **`resolve_units` must pass the names down.** It has the whole `units_decl`, so it already knows
  both. No new plumbing, one argument.
- **H3a's open gap closes for free.** § Weighted samples already states the weight rule — *"a weight
  must not vary within a unit's measurement rows"* — as a documented rule with the check owed. The
  same one-column-constancy machinery serves both, so H3b should close both rather than build the
  mechanism and leave one caller unwired. Doing otherwise is how a slice ships a capability and an
  identical known bug side by side.

The refusal is a `ContractError` from `units.py`, surfacing at validate time through the
`except ContractError` wrapper `_check_units` already has — the route `E-UNITS-COLLAPSE-RULE` and
`E-DATA-MEASUREMENTS-COLLAPSE-TYPE` both take, both of which are dual-listed for exactly that reason.

## Risks

- **A cluster fixture where the clustered and unclustered draws coincide.** With equal-sized or
  singleton clusters the two partitioners agree, so a test over them cannot see the rewrite. This is
  H3a's "check that could not fail" — eight instances — in its natural habitat. **Every partition
  test uses deliberately uneven clusters, and states why its numbers discriminate.**
- **CR1 asserted by presence rather than by number.** H3a's task 8 asserted an interval was "wider
  than unweighted" and passed against an implementation using the row count for df, because it is
  still wider. CR1's whole point is `df = clusters − 1`. **Assert the number.**
- **The unit-table reconciliation.** `resolved == completed + ineligible + failed`. H3a found three
  ways to break it, none raising an error. Clustering changes what a fold *sees*, so every new path
  is checked against `n`'s parts, not just against its own output.
- **A defect existing only in a combination no task owns.** H3a shipped exactly one, and it was the
  combination of its own two halves. Decision 3 names the one already found; the spec's testing
  section requires the others to be enumerated rather than discovered.
- **Retiring a refusal makes latent defects live.** It happened three times in H3a. The scoping
  enumerates nine things `E-DATA-CLUSTER-UNSUPPORTED` masks and four for the fold code, including a
  **code-ordering flip**: `E-REPL-FOLD-STRATIFY-UNSUPPORTED` is raised before `k` is resolved, so
  retiring it changes what `{k: 1, stratify_by: x}` reports.
- **The worked example.** `cohort-pilot` declares no `cluster_by`, so nothing about it may move.
  Verified before designing; re-verified at the end, with a real temporary commit.

## Testing

Every check needs a test producing its identifier, and every declaration a second test proving its
effect. Three tests carry the slice:

| Test | Pins |
|---|---|
| A roster of deliberately uneven clusters, partitioned at `k` — **no cluster appears in two folds** | The leak the document calls the point of the feature |
| `t_over_units_clustered` over 10 clusters of 30 units — **df is 9, not 299** | That CR1 reached the construction, not merely the record |
| A `fold` whose `stratify_by` varies *within* a cluster | The impossible-request row, which is what makes the two features interact |

The second is the one to write first. A test asserting only that a clustered interval *exists*, or
that it is wider, would pass against an implementation that records the method name and computes the
unclustered interval — which is the bug, not the fix.

**Mutations each must kill:** splitting one cluster across folds; using the unit count for df instead
of the cluster count; resampling units rather than clusters in the percentile draw; balancing cluster
count instead of unit count; and emitting `clusters` in `n` for a run that declares no `cluster_by`.

## Task sequence

Roughly twelve tasks — H3a's size, not a quarter of it. Do not split the slice: the "rewrite
`partition_units` once" argument is what orders H3 at all.

**A — the documents first.** The *Cluster attribute exists* row the document owes, the
`W-DATA-CLUSTER-UNDECLARED` identifier, and the `cluster_by` × `measurements` rule. Written before
the code, per the document-leads rule, so no check lands describing a rule no document states.

**B — cluster resolution.** One authority answering which cluster a unit is in, read by everything
below; the attribute check; the undeclared warning.

**C — the partition rewrite.** Whole clusters to one side; balance by unit count as evenly as
indivisible clusters allow; `k: all` as leave-one-cluster-out; the affordability row it breaks; the
*Folds fit inside the clusters* check.

**D — stratification.** `fold.stratify_by`, the shared *Stratification attribute exists* row in its
`fold.` half, and *Fold strata survive clustering* — with the code-ordering flip the scoping found.

**E — the constructions.** `n` gaining `clusters`; `t_over_units_clustered` with CR1 and
df = clusters − 1; the clustered percentile draw; wiring both, including the derived-metric draw that
runs today.

**F — the refusals and the retirements.** The clustered-contrast refusal, then both retirements, then
the consistency passes and the exit criterion — `partition_units` is the one thing H3c and H3d rely
on, so its new contract is stated where they will read it.
