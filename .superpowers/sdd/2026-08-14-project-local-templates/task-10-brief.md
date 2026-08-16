## Task 10: `template_version` and `plugin` under a local template

**Files:** Modify `src/publishable/materialize.py`, `src/publishable/validate.py`, `docs/reference.md`; Test `tests/test_materialize.py`, `tests/test_validate.py`

**Trap (c), and the single best reason this slice is not three lines.** Today `materialize_config` writes `template_version` from **core's own module constant** and `_check_versions` compares a config against it. For a local template that string certifies nothing — § Three hashes says so: *"`template_version` isn't the answer for a local template — it's a string its author remembers to bump."*

**Spec decisions 2 and 3:** `plugin` stays **`null`** — it names a *distributable source* and a local template has none, so **no code change**, only the test that pins it. `template_version` is **not written and not warned on** for a local template.

- [ ] **Step 1: Write the failing tests** — a config generated against a local template carries no core `template_version`, and `_check_versions` emits no `W-TEMPLATE-VERSION` for it; **the control**, a `generic` config, still gets both, so a change that suppressed the warning globally fails.
- [ ] **Step 2–4:** Fail, implement, pass.
- [ ] **Step 5: Mutate** — suppress the warning for every template (the `generic` control fails); write core's constant for locals (the first test fails).
- [ ] **Step 6:** Amend § Three hashes / § Errors' `W-TEMPLATE-VERSION` row so the document says what the code does. Commit.

---

