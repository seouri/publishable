## Task 5: `sweep.groups` expands

**Files:** Modify `src/publishable/sweep.py`; Test `tests/test_sweep.py`

A group axis contributes to the product like any other, per § Expansion modes.

- [ ] **Step 1: Failing tests** — `groups` alone gives one condition per level; `groups × grid` gives the product; a per-cell baseline over a group axis behaves as H2 built it.
- [ ] **Step 2–4:** Fail, implement, pass. Run the whole H2 sweep suite untouched.
- [ ] **Step 5: Mutation** — exclude `groups` from the product; the count assertions fail.
- [ ] **Step 6: Commit.**

---

