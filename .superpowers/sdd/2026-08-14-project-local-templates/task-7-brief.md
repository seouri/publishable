## Task 7: Collision and shadow are refused, naming both providers

**Files:** Modify `src/publishable/templates/discovery.py`, `docs/reference.md`; Test `tests/test_templates.py`

**Mint `E-TEMPLATE-COLLISION`.** § Creating a plugin: two local files claiming one name, and a local claiming `generic`, "fail at load, naming both providers". **Both providers must appear in the message** — that is what the rule promises and what makes it actionable.

**Scope, per the spec's decision 5:** local × local and local-shadows-`generic` only. Local shadowing an *installed plugin* is H7b's — no plugin can exist until entry points do.

- [ ] **Step 1: Write the failing tests** — two files claiming one name; a file claiming `generic`; **and the control**, two files claiming *different* names, which must resolve cleanly. Assert both provider paths appear in the message.
- [ ] **Step 2–4:** Fail, implement, pass.
- [ ] **Step 5: Mutate** — report only the first provider (the naming assertions fail); allow the shadow (its test fails). Neither may kill the control.
- [ ] **Step 6: Registry row** in § Errors `validate` reports, in sort order, checking every row it moves. Commit.

---

