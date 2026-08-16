## Task 2: `AXIS_MODES` splits into three predicates

**Files:** Modify `src/publishable/sweep.py`; Test `tests/test_sweep.py`

**H2 deferred this and named it explicitly.** One tuple answers three different questions today, and `groups` answers them **yes–no–no**:

| Predicate | `grid`/`paired`/`sample` | `groups` |
|---|---|---|
| Contributes to the condition product | yes | **yes** |
| Sweeps a parameter path | yes | **no** |
| `ablate` may not cross it | yes | **no** |

Split into `PRODUCT_MODES` and `PARAMETER_AXIS_MODES`. **`SWEEP_MODES` stays derived** from the partition — that is the property H2 built so `E-SWEEP-KEY-UNKNOWN` is the only way to add a mode, and it is pinned.

**`validate.py` is the second consumer and the plan nearly missed it.** It imports `SWEEP_MODES`, uses it for `E-SWEEP-KEY-UNKNOWN` and its `difflib` hint, and carries **three comments** arguing about which tuple is the pin — including one saying *"`AXIS_MODES` is not the pin: `known` above reads `SWEEP_MODES`, derived from `AXIS_MODES + NON_AXIS_MODES`"*. That sentence names the very tuple you are splitting. **Read all three and update each**, or the module explains the vocabulary in terms that no longer exist. A comment falsified by its own commit is the defect this project has shipped four times.

- [ ] **Step 1: Write the failing test — and note why the obvious one cannot fail**

```python
def test_ablate_may_cross_a_groups_axis_but_not_a_parameter_axis():
    """Both halves in one test, because `ablate × grid` being refused passes
    under either predicate — it is only the `ablate × groups` half that
    distinguishes them. A test asserting the refusal alone could not fail."""
    assert refused({"ablate": {...}, "grid": {...}})      # unchanged
    assert not refused({"ablate": {...}, "groups": {...}})  # THIS is the discriminator
```

- [ ] **Step 2: Run it, confirm the second assertion fails.**
- [ ] **Step 3: Implement the split**, keeping `SWEEP_MODES` derived.
- [ ] **Step 4: Run the whole existing sweep suite untouched** — it is the oracle for every mode but `groups`.
- [ ] **Step 5: Two mutations.** Put `groups` in `PARAMETER_AXIS_MODES` → the `ablate × groups` assertion fails. Hand-write `SWEEP_MODES` rather than deriving it → add a test that a mode absent from both partitions is refused by `E-SWEEP-KEY-UNKNOWN`, or the derivation is claimed and not provided.
- [ ] **Step 6: Commit.**

---

