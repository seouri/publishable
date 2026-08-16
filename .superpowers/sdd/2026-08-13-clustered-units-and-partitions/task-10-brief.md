## Task 10: The clustered percentile draw

**Files:** Modify `src/publishable/stats.py`; Test `tests/test_stats.py`

§ Statistical reporting: the percentile forms *"resample whole clusters"*. Note `percentile_over_units` **sorts its pool**, with a comment saying the resample must depend on the multiset rather than row order — H3a's weighted version had to keep each value with its own weight through that sort, and the clustered one must keep each value with its **cluster**.

- [ ] **Step 1: Write the failing test** — a fixture where drawing clusters and drawing units give **different, asserted** numbers. With singleton clusters they coincide, which is the trap.
- [ ] **Step 2–4:** Fail, implement, pass.
- [ ] **Step 5: Mutation** — draw units rather than clusters; the test must fail.
- [ ] **Step 6: Commit.**

---

