## Task 4: `partition_units` draws whole clusters

**Files:** Modify `src/publishable/units.py`; Test `tests/test_units.py`

**The slice's load-bearing task.** § Clustered units: *"Whole clusters go to one side of a split; a cluster is never divided between train and test … the metric is inflated before any interval is computed — so cluster-robust standard errors don't repair it."*

**What balances is unit count, not cluster count**, and the existing docstring's promise weakens. It currently claims "sizes differ by at most one". Under indivisible clusters that cannot hold, so it becomes *as even as indivisible clusters allow*. **Say the weaker thing in the docstring rather than keep claiming the stronger one.**

**The assignment order is part of the contract, not an implementation detail.** Measured over the fixture below (sizes 7/3/3/1/1 at `k = 2`):

| Order clusters are assigned in | Resulting folds |
|---|---|
| largest first | **8, 7** |
| smallest first | 11, 4 |

So the rule is: **shuffle the clusters with the digest-seeded RNG, then assign largest first, each to the currently-smallest fold.** The shuffle is what keeps the draw a function of the design digest — and what breaks ties among equal-sized clusters, which is the only place it can still matter once the sort is stable. Sorting without shuffling would make the partition deterministic given the sizes alone, which contradicts § What auto-derives from; shuffling without sorting gives the 11/4 split above. **Both halves are load-bearing and each needs its own mutation.**

- [ ] **Step 1: Write the failing test — uneven clusters, and say why they discriminate**

```python
def test_no_cluster_is_split_across_folds():
    """Cluster sizes 7/3/3/1/1 over k=2. Deliberately uneven: with equal-sized or
    singleton clusters the clustered and unclustered partitioners agree, so a test
    over those could not see this rewrite at all."""
    sizes = {"S1": 7, "S2": 3, "S3": 3, "S4": 1, "S5": 1}
    units, clusters = [], {}
    for site, n in sizes.items():
        for i in range(n):
            key = f"{site}_{i}"
            units.append(Unit(key=key, paths=(), attributes={"site": site}))
            clusters[key] = site
    folds = partition_units(UnitList(units), k=2, digest="sha256:abc", clusters=clusters)
    seen = {}
    for f, fold in enumerate(folds):
        for u in fold:
            assert seen.setdefault(clusters[u.key], f) == f, "a cluster spans two folds"
    assert sum(len(f) for f in folds) == 15          # every unit lands exactly once
    assert {len(f) for f in folds} == {8, 7}          # balanced by UNIT count
```

- [ ] **Step 2: Run, confirm it fails.**
- [ ] **Step 3: Implement.** `clusters: dict[str, str] | None = None`; when `None`, behaviour is **byte-identical to today** — pin that separately, because every existing fold test depends on it.
- [ ] **Step 4: Run the whole existing fold suite untouched.** It is the oracle for the unclustered path.
- [ ] **Step 5: Four mutations, separately.**
  - assign units rather than clusters → the split test fails;
  - balance *cluster* count instead of unit count → the `{8, 7}` assertion fails;
  - **drop the largest-first sort**, keeping the shuffle → the `{8, 7}` assertion fails for at least one seed. **Find a seed where it does and pin that seed**, because for some shuffles the greedy result coincides with the sorted one — this mutation is otherwise a check that could not fail, which is the trap this slice has met eight times;
  - **drop the shuffle**, keeping the sort → a test asserting two different digests give different assignments must fail. Write that test; without it the digest-seeding rule is claimed and not provided.
  Each with `__pycache__` cleared, reverts verified by behaviour.
- [ ] **Step 6: Commit.**

---

