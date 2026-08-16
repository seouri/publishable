## Task 13: Forward-only stratification

**Files:** Modify `src/publishable/units.py`, `src/publishable/validate.py`; Test `tests/test_units.py`, `tests/test_validate.py`

**A sequencing requirement, not a check.** Axis 2's draw consumes axis 1's **realized** membership as its stratum column. Nothing today establishes any per-axis draw order — `_resolved_group_axes` builds a dict in declaration order **by accident of construction, not by contract**.

- [ ] **Step 1: Write the failing tests**

```python
def test_an_axis_may_stratify_on_an_earlier_axis():
    """experimental-designs.md § Between-subjects factorial: 'Axes resolve in
    declaration order and `stratify_by` may name an earlier axis'. `sex` then
    `arm: {stratify_by: [sex]}` — assert arm is balanced WITHIN each sex."""

def test_stratifying_on_a_later_axis_is_refused(write_config):
    """*Stratification is forward-only*: 'an axis may only stratify on one
    already resolved'. The control is the same pair declared the other way
    round, which must be accepted."""

def test_the_draw_order_is_the_declaration_order_by_contract():
    """Pins the sequencing itself, so a later refactor of `_resolved_group_axes`
    into an unordered mapping fails here rather than silently reordering draws."""
```

- [ ] **Step 2–4:** Fail, implement, pass.
- [ ] **Step 5: Mutation** — reverse the draw order; the earlier-axis test must fail. **If it passes, axis 2 is not actually consuming axis 1's membership** and the feature is decorative.
- [ ] **Step 6: Commit.**

---

