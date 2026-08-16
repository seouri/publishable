## Task 5: `k` and `k: all` are bounded by clusters

**Files:** Modify `src/publishable/replication.py`, `src/publishable/validate.py`, `src/publishable/cli.py`; Test `tests/test_replication.py`, `tests/test_validate.py`

§ Validation, *"Folds fit inside the clusters"*: `{kind: fold, k: 10}` with `cluster_by: animal_id` over 6 animals — **clusters are indivisible, so `k` may not exceed the cluster count**. And *"Leave-one-out is affordable"* is **already implemented and this task makes it wrong**: `k: all` stops meaning one unit per fold and starts meaning leave-one-*cluster*-out.

**`unit_count` reaches `_fold_k` by two arrival paths and both must change** — `validate`'s call and `cli`'s. H3a's task 9 shipped a bug by changing two of three sites; the regression test for the *unclustered* path is what catches changing only one here.

- [ ] **Step 1: Write the failing tests** — `k` above the cluster count refused; `k: all` yielding the cluster count; and **the control**, an unclustered run whose `k: all` still yields the unit count.
- [ ] **Step 2–4:** Fail, implement, pass. Pass a cluster count where the unit count goes today; do not add a second parameter that can disagree with the first.
- [ ] **Step 5: Mutation** — leave one arrival path unchanged; a named test must fail.
- [ ] **Step 6:** Update the *Leave-one-out is affordable* row for what `k: all` now means under clustering, and commit.

---

