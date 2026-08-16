## Task 4: The seven readers learn the distinction

**Files:** Modify `src/publishable/runner.py`, `src/publishable/cli.py`, `src/publishable/contrasts.py`, `src/publishable/validate.py`; Test each module's suite

Take them **one at a time**, and for each say in the report whether it must change or is correct as-is. A reader that "obviously doesn't care" is exactly the one that turns out to.

- [ ] **Step 1: The headline test first — the leak**

```python
def test_a_group_cell_adds_no_parameter():
    """`parameters` must gain no `arm` key, and `parameters_hash` must match the
    same design without the group axis. Every other test in this slice passes
    whether or not the phantom parameter appears, which is why this one is first."""
    ...
    assert "arm" not in resolved.raw["parameters"]
```

- [ ] **Step 2: `resolve_condition_cfg`** — skip selector paths, and **rewrite the docstring**, which currently asserts the thing this task falsifies. A docstring left claiming it is the defect class this project has shipped four times.
- [ ] **Step 3: The other six**, each with a test asserting what it does with a group cell:
  - `cli` run.yaml conditions block and `sweep.sweep_document` — a selector path is still recorded; **say whether the record distinguishes them**, since a reader of `run.yaml` cannot otherwise tell an arm from a parameter.
  - `sweep.label_for` — a group cell renders in the label, as § How artifacts are organized shows with `arm=control`.
  - `contrasts` free-axis matching — a group axis **is** an axis for baseline matching.
  - `validate`'s two sites — the swept-value checks and the confounded check.
- [ ] **Step 4: `parameters_hash` is unchanged** by adding a group axis, asserted directly.
- [ ] **Step 5: Mutation per site** — restore the old behaviour at each, one at a time; a *named* test must fail for each. **Six mutations, six tests.**
- [ ] **Step 6: Commit.**

---

