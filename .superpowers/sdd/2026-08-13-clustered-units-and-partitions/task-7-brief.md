## Task 7: The stratified partition

**Files:** Modify `src/publishable/units.py`; Test `tests/test_units.py`

**Why this task exists.** Task 6 made `fold.stratify_by` *validated* — both its checks land — but `partition_units` takes no stratum, so **a declared stratification has no effect on the split.** § Repeat kinds calls folds "stratified" when it is declared, so this is a declaration accepted whose effect is not delivered: the risk this project names first, and the one task 12 would make live by retiring `E-REPL-FOLD-STRATIFY-UNSUPPORTED`.

**This was a gap in the plan, not in task 4 or 6.** Task 4's heading said "and honouring a stratification" and no step owned it; task 6's implementer found it and said so. It is the second gap of that exact shape in this slice, the first being `cli` calling `partition_units` without the clusters.

**Interfaces, read from the code:**
- `units.partition_units(roster, k, digest, clusters: dict[str, str] | None = None)` — task 4's rewrite: group in roster order, shuffle cluster names with the digest-seeded RNG, stable-sort by descending size, assign each whole cluster to the currently-smallest fold by unit count.
- `units.stratum_varies_within_cluster(roster, cluster_by, stratify_by)` — task 6's check, which guarantees that **when clustering is declared, every cluster carries exactly one stratum value.** That is what makes a cluster assignable to a stratum at all, and it is why this task can treat cluster and stratum as compatible rather than competing.
- `units.clusters_of` — the single authority. Do not group a second way.

**The two objectives, and how they compose.** Task 4 balances **unit count** across folds. Stratification balances **stratum proportions**. Because task 6 guarantees a cluster carries one stratum value, a cluster belongs to exactly one stratum — so the composition is: **partition within each stratum, using task 4's rule, then merge the per-stratum folds index-wise.** That keeps clusters whole, keeps each fold's stratum mix close to the roster's, and reuses the existing rule rather than inventing a second balancer.

**Unclustered is the degenerate case, not a separate path.** With no `clusters`, treat each unit as its own cluster of one — the same code, and task 4's `clusters=None` behaviour must stay **byte-identical** because every existing fold test is its oracle.

- [ ] **Step 1: Write the failing test — asymmetric strata, and say why they discriminate**

```python
def test_each_fold_gets_a_proportional_share_of_each_stratum():
    """12 units, 8 label=0 and 4 label=1, at k=2. Deliberately asymmetric: with
    a 6/6 split an unstratified partition often lands 3/3 by luck, so a balanced
    fixture cannot see this rule at all. Here each fold must get 4 and 2."""
    ...
    for fold in folds:
        counts = Counter(u.label for u in fold)
        assert counts["0"] == 4 and counts["1"] == 2
```

- [ ] **Step 2: Run it, confirm it fails.**
- [ ] **Step 3: Implement.** `partition_units(..., strata: dict[str, str] | None = None)`.
- [ ] **Step 4: Run, and run the whole existing fold suite untouched** — it is the oracle for `strata=None`.
- [ ] **Step 5: Four mutations, separately.**
  - drop the stratification (partition the whole roster at once) → the proportion test fails;
  - merge the per-stratum folds by **sorting on size** instead of index-wise → find a fixture where that unbalances the strata and pin it, **or say the mutation cannot fail and why**;
  - **split a cluster** while stratifying → task 4's no-split test must still fail, proving stratification did not reintroduce the leak;
  - stratify but ignore `clusters` → the no-split test fails.
  Each with `__pycache__` cleared, reverts verified by behaviour.
- [ ] **Step 6: State the interaction in the docstring** — that a cluster carries one stratum value *because task 6 refuses otherwise*, so this composition is sound only while that check exists. A later slice removing it would silently break this.
- [ ] **Step 7: Commit.**

---

