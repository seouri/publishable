## Task 9: `t_over_units_clustered` — CR1

**Files:** Modify `src/publishable/stats.py`; Test `tests/test_stats.py`

§ Statistical reporting: *"Cluster-robust (CR1: the sandwich estimator with the standard finite-sample scaling), **df = clusters − 1**. The df is the part that bites — 10 animals give 9, not 299."*

**Assert the number.** H3a's task 9 asserted a weighted interval was "wider than unweighted" and passed against an implementation using the row count for df, because it is still wider. The same trap is here in sharper form: a clustered interval over correlated data is wider than the unclustered one *whatever* df it uses.

- [ ] **Step 1: Write the failing tests, the df one first**

```python
def test_the_clustered_interval_takes_its_df_from_the_cluster_count():
    """10 clusters of 3 units. df must be 9, not 29 — the document's own example
    is '10 animals give 9, not 299'. Asserting only that the interval is wider
    would pass against an implementation using the unit count, because a
    cluster-robust interval over correlated data is wider either way."""
    ...
    # Compare against `t_over_units` on a three-point fixture whose df is 9 by
    # construction, so the expectation does not come from the code under test.
```

Reuse `_t_critical(df, confidence)` — H3a extracted it precisely so two critical-value expressions cannot drift, and its `df` is already a `float`.

- [ ] **Step 2–4:** Fail, implement the CR1 sandwich with its finite-sample scaling, pass.
- [ ] **Step 5: Two mutations, separately** — df from the unit count; and the finite-sample scaling dropped. **If no existing test fails for the second, write one**: it is the "CR1" half of the name, and an interval that omits it is a different construction wearing the same `method`.
- [ ] **Step 6:** Registry/§ Statistical reporting consistency, and commit.

---

