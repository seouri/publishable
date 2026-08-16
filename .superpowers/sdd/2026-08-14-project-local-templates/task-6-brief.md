## Task 6: Process hygiene — per-repo registration, non-aliasing module names

**Files:** Modify `src/publishable/templates/discovery.py`; Test `tests/test_templates.py`

**Trap (b), and the reason is written down already.** `load_experiment` purges the root package from `sys.modules` because "two projects in one process can declare the same package name … and a cached module would silently hand back the other project's steps". Two repos can both hold `templates/my_assay.py`.

- [ ] **Step 1: Write the failing test**

```python
def test_two_repos_in_one_process_do_not_cross_contaminate(tmp_path):
    """Both repos hold `templates/my_assay.py`, registering the same name but
    different classes. Resolving from repo A then repo B must give B's class.
    A module-global registry, or a `sys.modules` cache keyed on a name both
    repos share, hands back A's — silently, which is why this is a test and
    not a comment."""
    a = get_template("my_assay", repo_a)
    b = get_template("my_assay", repo_b)
    assert type(a).__doc__ == "A's"
    assert type(b).__doc__ == "B's"      # the assertion that fails on a cache
```

- [ ] **Step 2–4:** Fail, implement, pass. Give each path-imported module a name that cannot alias across repos, and purge it as `load_experiment` does.
- [ ] **Step 5: Mutate** — key the synthetic module name on the file stem alone; the test must fail. **This is the mutation that matters: a naive implementation passes every other test in this plan.**
- [ ] **Step 6: Commit.**

---

