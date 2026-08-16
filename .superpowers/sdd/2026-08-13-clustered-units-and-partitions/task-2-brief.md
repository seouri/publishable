## Task 2: Cluster resolution, one authority

**Files:** Modify `src/publishable/units.py`; Test `tests/test_units.py`

**Interfaces:**
- Produces: `clusters_of(roster: UnitList, cluster_by: str) -> dict[str, str]` — unit key to cluster id, and `cluster_count(...)`. Everything below reads these; **nothing re-derives cluster membership**.

H3a proved this pattern twice (`units.usable_weight`, `units.is_measurement_numeric`): one function answers the question, read by `validate` and by `stats`, so a config that validates cannot crash on a value `validate` approved. Three near-misses on a fourth notion were caught in H3a — do not create one here.

**`cluster_by` names a declared attribute**, exactly as `weight_by` does and unlike `measurements.by`, which names a source column. H3a's task 6 shipped a Critical by getting that backwards; § Clustered units' own YAML and the *Cluster attribute exists* row you wrote in task 1 settle it.

- [ ] **Step 1: Write the failing test**

```python
def test_clusters_group_units_by_their_declared_attribute():
    units = [Unit(key=f"u{i}", paths=(), attributes={"site": s})
             for i, s in enumerate(["S1", "S1", "S1", "S2", "S3"])]
    roster = UnitList(units)
    assert clusters_of(roster, "site") == {
        "u0": "S1", "u1": "S1", "u2": "S1", "u3": "S2", "u4": "S3"}
    assert cluster_count(roster, "site") == 3   # 3 clusters over 5 units, deliberately uneven
```

- [ ] **Step 2: Run it, confirm it fails** on the missing name.
- [ ] **Step 3: Implement**, raising `ContractError` for a unit missing the attribute — the code the *Cluster attribute exists* row implies, taken from your task 1 row rather than invented.
- [ ] **Step 4: Run, confirm pass.**
- [ ] **Step 5: Mutation-test** — return the unit key as its own cluster; the count assertion must fail.

- [ ] **Step 6: Emit `W-DATA-CLUSTER-UNDECLARED`.** Task 1 minted the identifier and wrote its row; **no other task owns the emit site**, so without this step the slice ships a documented warning nothing raises. Task 1's implementer found this and it is a real plan gap, not a scope creep.

Implement the trigger **exactly as task 1's row states it** — read that row, do not re-derive from this sentence. It is deliberately predicate-only with no numeric threshold, because `CLAUDE.md` puts every threshold in `limits` and adding a `limits` key is code task 1 could not write. If a predicate proves unimplementable, **change the row and say so** rather than implementing something the document does not describe.

Two tests, and the second is the one that matters:

```python
def test_a_column_that_looks_like_a_cluster_warns_when_undeclared():
    ...
    assert "W-DATA-CLUSTER-UNDECLARED" in codes(path)

def test_the_worked_examples_own_attributes_do_not_warn():
    """cohort-pilot declares `[label, age, sex]` and no cluster_by. `sex` has two
    values over many units, which "few distinct values, many units each" reads as
    a cluster — so this is the control that decides whether the trigger is usable
    at all, not a nicety. Task 1 verified the row's predicates are silent here."""
    assert "W-DATA-CLUSTER-UNDECLARED" not in codes(path)
```

Mutation-test the trigger, and confirm the negative control fails under a deliberately loosened predicate.

- [ ] **Step 7: Commit.**

---

