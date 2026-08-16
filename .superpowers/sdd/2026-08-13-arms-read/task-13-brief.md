## Task 13: `n` reconciles per arm

**Files:** Modify `src/publishable/runner.py` if needed; Test `tests/test_runner.py`, `tests/test_cli.py`

Arms partition units **across conditions**, so each condition's `resolved` is a subset. `resolved == completed + ineligible + failed` must hold **per condition**, and the arms' `resolved` must sum to the roster when every unit is assigned.

- [ ] **Step 1: Failing test** asserting both, over the uneven 7/5 fixture.
- [ ] **Step 2–4:** Fail, implement (or confirm no change needed and say so), pass.
- [ ] **Step 5: Mutation** — count the whole roster per condition; both assertions fail.
- [ ] **Step 6: Commit.**

---

