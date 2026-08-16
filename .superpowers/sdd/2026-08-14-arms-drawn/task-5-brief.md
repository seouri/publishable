## Task 5: `ratio` validation, and the live gap under `by_attribute`

**Files:** Modify `src/publishable/validate.py`, `docs/reference.md`; Test `tests/test_validate.py`

**Ships before drawing exists and closes a gap that is live today.** § Allocation says *"Under `method: by_attribute` a `ratio` describes a draw that didn't happen, so `validate` rejects a non-empty one"* — and **nothing reads `ratio` anywhere in `src/`.**

- [ ] **Step 1: Write the failing tests.** Three faults and two controls:

```python
def test_a_partial_ratio_is_refused(write_config):
    """§ Allocation: 'a partial mapping is rejected rather than defaulted, since
    "one entry per level" is checkable and "the levels I left out get the
    average" is a rule nobody should have to infer.' Two levels, one entry."""
    ...  # assert the exact finding set

def test_a_ratio_naming_an_undeclared_level_is_refused(write_config):
    """`ratio: {control: 1, f: 2}` against levels [control, treatment]."""

def test_a_non_empty_ratio_under_by_attribute_is_refused(write_config):
    """The draw didn't happen, so the proportion describes nothing."""

def test_an_empty_ratio_is_equal_allocation_and_is_accepted(write_config):
    """The control, and it must report: `{}` is what `init` writes and what most
    designs carry, so a check that refused it would fire on the common case.
    Assert the exact finding set, not an absence."""

def test_a_full_ratio_under_a_drawn_method_is_accepted(write_config):
    """The second control. Under this build the config still reports
    E-DATA-ASSIGN-DRAWN — assert that exact set, so the test keeps its teeth
    when task 14 retires that code and the set becomes empty."""
```

- [ ] **Step 2: Run them and confirm each fails for its own reason.**
- [ ] **Step 3: Implement** in `_check_assign`, beside the existing method checks. *Ratio names levels* is the row.
- [ ] **Step 4: Mutate each branch separately** — each test must die to its own branch and no other.
- [ ] **Step 5: Commit.**

---

