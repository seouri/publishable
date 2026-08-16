## Task 5: Wire the other two call sites

**Files:** Modify `src/publishable/cli.py`, `src/publishable/generators/experiment.py`; Test `tests/test_cli.py`

Both already have a repo root in scope — `cli.command_run` binds `repo_root = find_repo_root(config_path)` in the same function, and `generate_experiment` takes it as a parameter.

**`generate experiment --template my_assay` failing with `E-TEMPLATE-UNKNOWN` is the first probe in the scoping.** It must stop failing.

- [ ] **Step 1: Write the failing tests** — `generate experiment --template my_assay` succeeds in a project holding that local template, with the control that `--template nope` still fails; and `command_run`'s `aggregate` block resolves a local template's `aggregate`.
- [ ] **Step 2–4:** Fail, implement, pass.
- [ ] **Step 5: Mutate** — pass `None` as the root at each site in turn; each must fail its own test.
- [ ] **Step 6: Commit.**

---

