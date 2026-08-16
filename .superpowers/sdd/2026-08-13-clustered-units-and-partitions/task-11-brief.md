## Task 11: Wire the partition and both constructions, including the draw that already runs

### First, and it is the slice's whole point: `cli` calls `partition_units` without the clusters

**A gap this plan did not contain, found by tasks 4 and 5 independently.** `cli.py`'s fold step is:

```python
        partitions = partition_units(roster, fold_level.n, digest)
```

No `clusters` argument. So today a clustered run gets the right fold **count** — task 5 wired that — and the **wrong membership**: task 4's rewrite is never reached, and every fold still trains on other units of the cluster it tests on. That is precisely the leak § Clustered units calls *"the difference between a valid evaluation and a leaky one"*, and `experimental-designs.md` § Mistakes core prevents requires it to be **structurally impossible**.

Task 3 closed the input-file route and task 4 built the partitioner, but **until this line passes `clusters`, the fold route is open**. Pass it, using `units.clusters_of` — task 2's single authority — and **also the strata task 7 added**, since a declared `fold.stratify_by` is equally unwired at that call site. Both arguments or neither: wiring one and not the other ships half a guarantee that looks whole.

**Pin it end to end, not at the function.** `partition_units`' own tests already prove the partitioner; what is unproven is that a *run* reaches it. Assert over a real run that no cluster appears in two folds, with an unclustered control that must report. And beware the coincidence that caught the controller's own probe: on some fixtures the clustered and unclustered partitioners give the **same fold sizes** while differing in membership — assert membership, never sizes.

### Then: the constructions

**Files:** Modify `src/publishable/cli.py`, `src/publishable/stats.py`; Test `tests/test_cli.py`, `tests/test_stats.py`

**`derived_metric_draws = 2000` is a hard constant, so the derived-metric percentile interval draws unconditionally, ungated by `statistics.resample`.** Un-refusing `cluster_by` therefore makes an **already-running** interval wrong. That is why this slice owns the draw at all, and it is the one wiring that cannot be deferred.

H3a's task 11 is the precedent for what "wired" means: **both the value and the interval**, and the weight vector filtered and ordered exactly as the values are. The same applies to cluster membership — a misalignment weights the wrong unit's cluster and produces a plausible number, not an error.

- [ ] **Step 1–6:** Failing end-to-end tests asserting exact numbers; implement at every `summarize_step` call site (H3a found **three** in `cli.py`, all needing the same argument); mutate by dropping the argument at each site separately; commit.

---

