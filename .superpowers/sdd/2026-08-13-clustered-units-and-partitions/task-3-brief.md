## Task 3: A cluster must not vary within a unit's measurement rows

**Files:** Modify `src/publishable/units.py`; Test `tests/test_units.py`, `tests/test_validate.py`

**This closes H3a's open weight gap with the same machinery — wire both callers.** § Weighted samples already states the weight rule with the check owed; building the mechanism and wiring only the cluster caller would ship a capability and an identical known bug side by side.

Reproduced before this plan was written:

```
p1's replicate rows declare site S1 and S2
collapse -> 'S1', chosen by the `first` fallback
```

**`validate` cannot host this check.** `resolve_units` collapses internally, so a validate-time check sees the post-collapse roster and the varying values are already gone — which is exactly why H3a could only state the weight rule. `collapse_measurements` groups rows by key and holds the pre-collapse values, so the check belongs there, told which columns must not vary.

- [ ] **Step 1: Write the failing tests** — one per column kind, each asserting the code:

```python
def test_a_cluster_varying_within_a_unit_is_refused():
    """A mis-collapsed cluster decides which side of a split a unit lands on."""
    units = [Unit(key="p1", paths=(), attributes={"read": "r1", "site": "S1"}),
             Unit(key="p1", paths=(), attributes={"read": "r2", "site": "S2"})]
    with pytest.raises(ContractError) as e:
        collapse_measurements(units, by="read", collapse="first", constant=("site",))
    assert e.value.code == "E-DATA-CLUSTER-VARIES"

def test_a_cluster_constant_within_a_unit_is_accepted():
    """The control: same shape, agreeing rows, must NOT raise."""
    units = [Unit(key="p1", paths=(), attributes={"read": "r1", "site": "S1"}),
             Unit(key="p1", paths=(), attributes={"read": "r2", "site": "S1"})]
    collapsed, _ = collapse_measurements(units, by="read", collapse="first", constant=("site",))
    assert collapsed[0].site == "S1"
```

- [ ] **Step 2: Run, confirm both fail** — the first on the missing parameter, not on a passing assertion.
- [ ] **Step 3: Implement.** `collapse_measurements` gains `constant: tuple[str, ...] = ()` and refuses a named column that varies within a group. `resolve_units` passes the names it already knows from `units_decl` — `cluster_by`'s, and `weight_by`'s. **Two codes, not one**: the cluster case and the weight case say different things about what breaks, so `E-DATA-WEIGHT-VARIES` is the weight half and closes H3a's gap.
- [ ] **Step 4: Run, confirm pass**, including the weight half end to end through `validate` (a `ContractError` from `units.py` reaches `validate` through `_check_units`'s `except ContractError` — the route `E-UNITS-COLLAPSE-RULE` already takes).
- [ ] **Step 5: Mutation-test each half separately.** One mutation killing both is not two tests.
- [ ] **Step 6: Both registry rows, both dual-listed** as `E-DATA-MEASUREMENTS-COLLAPSE-TYPE` is — they are raised from `units.py` and surface at both `validate` and run time. Commit.

---

