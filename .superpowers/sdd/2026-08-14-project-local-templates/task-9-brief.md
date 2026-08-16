## Task 9: `generate template`

**Files:** Modify `src/publishable/cli.py`, `src/publishable/generators/` (a new module beside `experiment.py`); Test `tests/test_cli.py`

Writes `templates/<name>.py` holding a `BaseTemplate` subclass with `parameter_spec` and `@register_template`.

**The stub emits only the five live members** — `parameter_spec`, `validate`, `aggregate`, `naming_pattern`, `default_repeats`. **Not** `field_convention`, `required_env`, `apparatus_probe` or `apparatus_facts`: nothing reads them, and a stub that emits them teaches a user to set fields with no effect.

**Greenfield refusal:** an existing `templates/<name>.py` is refused, never overwritten.

**The README half is deferred** — spec decision 4. § Generators promises the parameter table "is added to the README", but the scaffolded README has no region for one and `generate_experiment` never touches the README at all. Task 15 records the gap; do not invent a region.

- [ ] **Step 1: Write the failing tests** — the file is written and its name resolves through `get_template(name, repo_root)` (**round-trip, not just file existence**); an existing file is refused with the file unchanged; the stub contains none of the four dead members.
- [ ] **Step 2–4:** Fail, implement, pass, and route it in `_dispatch_generate`.
- [ ] **Step 5: Mutate** — overwrite instead of refusing (the refusal test fails); emit `apparatus_probe` in the stub (the dead-members test fails).
- [ ] **Step 6: Commit.**

---

