## Task 2: Eager path discovery

**Files:** Modify `src/publishable/templates/discovery.py`; Test `tests/test_templates.py`

**Consumes:** `register_template`, `drain_pending` (task 1).
**Produces:** `discover_local(repo_root: Path) -> dict[str, type[BaseTemplate]]` — imports **every** `templates/*.py` under the root and returns what they registered.

**Eager, and the reason is in the documents.** § Creating a plugin: a collision fails "at load, naming both providers", because *"install order and import order are the only tie-breaks available, and both are properties of a machine rather than of a design."* **Lazy discovery makes import order decide which template you get.** So every file is imported, not only the one the config names.

- [ ] **Step 1: Write the failing tests**

```python
def test_discovery_imports_every_file_not_only_the_named_one(tmp_path):
    """Two files, and the config names neither. Both must register, or a
    collision between them could not be detected — which is the whole reason
    discovery is eager rather than lazy."""
    # write templates/alpha.py and templates/beta.py, each registering one name
    found = discover_local(tmp_path)
    assert sorted(found) == ["alpha", "beta"]

def test_discovery_ignores_non_python_and_dunder_files(tmp_path):
    """The scaffold puts `.gitkeep` in `templates/`. THE CONTROL: a real
    template beside it must still be found, so a discovery that returned {}
    for everything fails here rather than passing both assertions."""
    # .gitkeep, __init__.py, notes.md, and one real template
    found = discover_local(tmp_path)
    assert sorted(found) == ["real_one"]

def test_discovery_with_no_templates_directory_is_empty_not_an_error(tmp_path):
    assert discover_local(tmp_path) == {}
```

- [ ] **Step 2–4:** Fail, implement, pass. Import by path, following `load_experiment`'s shape — `try`/`finally`, and drain after each file.
- [ ] **Step 5: Mutate** — import only the file matching a requested name (the eager test fails); include `.gitkeep` (the second fails). **Note the second test's control**: it must find `real_one`, so an implementation returning `{}` fails rather than passing the "ignores junk" half.
- [ ] **Step 6: Commit.**

---

