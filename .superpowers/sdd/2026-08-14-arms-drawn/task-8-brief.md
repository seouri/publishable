## Task 8: `random` honouring `ratio`, unclustered

**Files:** Modify `src/publishable/units.py`; Test `tests/test_units.py`

**Interfaces — Consumes:** `assign_seed_for` (task 6), `ArmPlan`/`assignment_for` (task 7).

- [ ] **Step 1: Write the failing tests**

```python
def test_a_random_draw_honours_an_unequal_ratio():
    """12 units, ratio {control: 1, treatment: 2} -> 4 and 8. Deliberately
    unequal AND not a half: 4/8 cannot be confused with 6/6, with 12, or with
    each other. Assert the exact sizes and the exact membership under a pinned
    seed."""

def test_a_random_draw_is_a_partition():
    """Every unit in exactly one arm, every declared level non-empty — the
    property `arms_of` guarantees for a read assignment and a draw must too."""

def test_the_same_seed_draws_the_same_arms():
    """And THE CONTROL: a different pinned seed draws different arms. Without
    it, a draw that ignored the seed entirely would pass the first half."""

def test_a_ratio_that_does_not_divide_the_roster_is_reported_not_rounded_away():
    """13 units at {1: 2} — assert the realized sizes exactly, and state in the
    docstring which unit the remainder went to and why."""
```

- [ ] **Step 2–4:** Fail, implement, pass.
- [ ] **Step 5: Mutations** — ignore the ratio (equal split); ignore the seed; drop the remainder unit. Each fails its own test.
- [ ] **Step 6: Commit.**

---

