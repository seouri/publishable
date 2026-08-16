## Task 3: A group cell is a selector, not a parameter

**Files:** Modify `src/publishable/sweep.py`; Test `tests/test_sweep.py`

**The largest item in the slice, and no charter named it.** Measured against a control:

```
cell {arm: control}          -> parameters gains  arm: 'control'
CONTROL {analysis.method: …} -> correctly overrides an existing parameter
```

`resolve_condition_cfg`'s docstring says *"Each dotted path in `values` names a leaf under `parameters`"*. A group cell breaks that: `{arm: control}` names a **set of units**.

**Carry the distinction on the condition**, set by `expand` — the only place that knows which mode produced a cell. Re-deriving "is this a group path?" at seven readers is how six agree and one does not.

- [ ] **Step 1: Write the failing test**

```python
def test_a_group_cell_is_marked_as_selecting_units_not_setting_a_parameter():
    conditions = expand({"sweep": {"groups": {"arm": ["control", "treatment"]},
                                   "grid": {"analysis.method": ["pearson", "spearman"]}}})
    # 2 × 2 = 4 conditions; each carries one selector path and one parameter path
    for c in conditions:
        assert c.selects == {"arm"}                      # the group axis
        assert set(c.values) - c.selects == {"analysis.method"}
```

**`selects` is a name this plan invented, not one it read** — pick whatever fits and rename the test. What is *not* negotiable is that the answer lives on the condition rather than being re-derived by each reader.

- [ ] **Step 2–4:** Fail, implement, pass. `Condition` is a frozen dataclass with `index`, `label`, `values`, `is_baseline`; **follow how `is_baseline` is carried**, and note `__post_init__` wraps `values` in a `MappingProxyType` for the reason its comment gives — whatever you add gets the same treatment if it is mutable.
- [ ] **Step 5: Mutation** — mark nothing as a selector; the test fails.
- [ ] **Step 6: Commit.**

---

