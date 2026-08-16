## Task 14: `E-TEMPLATE-UNKNOWN` stops being about installation

**Files:** Modify `src/publishable/validate.py`, `docs/reference.md`; Test `tests/test_validate.py`

Today the message reads *"names `my_assay`, which no installed template registers (known: generic)"* and its § Errors row says *"names a template no installed package registers"*. **Both stop being true the moment a template installed nowhere can resolve.** And "(known: …)" is `template_names()`, which must now include local names.

- [ ] **Step 1: Write the failing test** — in a project holding local templates, an unknown name's message lists them among the known, and says nothing about installation. Assert the **exact message**.
- [ ] **Step 2–4:** Fail, implement, pass.
- [ ] **Step 5: Mutate** — call `template_names()` without the root; the known-list assertion fails.
- [ ] **Step 6:** Update the § Errors row to match. Commit.

---

