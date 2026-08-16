## Task 3: The registry takes an optional repo root and merges per call

**Files:** Modify `src/publishable/templates/registry.py`; Test `tests/test_templates.py`, `tests/test_materialize.py`, `tests/test_validate.py`

**Consumes:** `discover_local` (task 2).
**Produces:** `get_template(name: str, repo_root: Path | None = None) -> BaseTemplate | None` and `template_names(repo_root: Path | None = None) -> list[str]`.

**Three test bindings break, and a partial change fails collection rather than a test** — which reads as a broken suite rather than a failing assertion. Update all of them in this task: `tests/test_templates.py` ×3, `tests/test_materialize.py` ×2, and `tests/test_validate.py`'s `lambda name: RuleBreaker()`, which takes **one** argument.

**`tests/test_templates.py`'s `get_template("llm_diagnostic") is None` asserts the closed set by name.** Decide whether it still means anything and say so — with a repo root it is no longer a statement about the world.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_local_template_resolves_by_name(tmp_path):
    """The headline. THE CONTROL: `generic` still resolves from the same call,
    so a change that replaced builtins with locals fails here."""
    # tmp_path/templates/my_assay.py registers "my_assay"
    assert get_template("my_assay", tmp_path) is not None
    assert get_template("generic", tmp_path) is not None

def test_without_a_repo_root_only_builtins_resolve(tmp_path):
    """No root → local discovery is skipped, `generic` still resolves. This is
    the behaviour task 4's hoist depends on."""
    assert get_template("my_assay") is None
    assert get_template("generic") is not None

def test_template_names_includes_locals_and_stays_sorted(tmp_path):
    assert template_names(tmp_path) == ["generic", "my_assay"]
    assert template_names() == ["generic"]
```

- [ ] **Step 2–4:** Fail, implement, pass. Merge builtins with locals **per call** — build no persistent dict.
- [ ] **Step 5: Mutate** — return locals only (the `generic` control fails); cache the merged mapping module-globally (task 6's test will catch it, but note it here).
- [ ] **Step 6: Commit.**

---

