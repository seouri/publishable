## Task 9: `random` over whole clusters

**Files:** Modify `src/publishable/units.py`; Test `tests/test_units.py`

**A sibling of `_assign_whole_clusters`, not a parameterization of it** — spec decision 6. That function deals whole clusters to the **least-loaded** of `k` *equal* buckets; an unequal `ratio` needs *furthest below its own target share*. Its fold behaviour is pinned by a bit-stability oracle, and **changing it risks a fold regression for an arm feature.**

- [ ] **Step 1: Write the failing tests.** The fixture must not let clusters and arms coincide:

```python
def test_a_clustered_random_draw_keeps_every_cluster_whole():
    """§ Clustered units: 'core computed the partition, so core keeps it
    indivisible.' 12 units in 5 clusters of 4/3/2/2/1 — sizes chosen so no
    subset sums to exactly half, so a draw that split a cluster could not
    reproduce a legal-looking balance by accident."""

def test_a_clustered_draw_approaches_an_unequal_ratio_as_closely_as_clusters_allow():
    """Assert the realized sizes exactly, and state in the docstring why they
    are not the exact ratio: a cluster is the smallest thing that can move, so
    one large cluster sets a floor. `partition_units`' docstring makes the same
    argument for folds — do not claim the stronger thing."""
```

- [ ] **Step 2: Confirm the fold oracle still passes before you touch anything**, and name it in your report.
- [ ] **Step 3–4:** Fail, implement, pass.
- [ ] **Step 5: Mutations** — route the clustered draw through `_assign_whole_clusters` unchanged (the ratio test fails); split a cluster (the whole-cluster test fails). **And re-run the fold oracle**: if it moved, the sibling is not a sibling.
- [ ] **Step 6: Commit.**

---

