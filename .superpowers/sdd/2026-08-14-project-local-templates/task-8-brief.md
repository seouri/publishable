## Task 8: A template that fails to load is a finding, not a traceback

**Files:** Modify `src/publishable/templates/discovery.py`, `docs/reference.md`; Test `tests/test_templates.py`

**Mint `E-TEMPLATE-LOAD`.** Three shapes: a file that **raises on import**, one that **registers nothing**, one that **registers a non-`BaseTemplate`**. `validate` collects and never raises, so each must surface as a finding naming the file.

- [ ] **Step 1: Write the failing tests** — one per shape, **plus the control**: a well-formed template beside a broken one must still resolve, so a discovery that abandoned the directory on the first failure fails here.
- [ ] **Step 2–4:** Fail, implement, pass.
- [ ] **Step 5: Mutate** — let the `ImportError` propagate (the raise test fails with a traceback rather than a finding); accept a non-`BaseTemplate` (its test fails).
- [ ] **Step 6: Registry row**, sorted, rows-moved checked. Commit.

---

