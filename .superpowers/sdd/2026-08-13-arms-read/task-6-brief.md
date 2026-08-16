## Task 6: The budget counts group conditions

**Files:** Modify `src/publishable/validate.py`; Test `tests/test_validate.py`

*Grid size sane* computes `len(expand(doc)) × repeat_total`. Once `groups` expands, that number changes — **the row was already implemented and this slice makes it wrong** unless it is updated with the behaviour.

- [ ] **Step 1: Failing test** — a design whose group axis pushes it past `limits.max_executions` is refused, and the message names the real count.
- [ ] **Step 2–4:** Fail, implement, pass.
- [ ] **Step 5: Mutation** — count the product without `groups`; the test fails.
- [ ] **Step 6:** Update the § Validation row per task 1's decision, and commit.

---

