## Task 1: `register_template`, and the decorator that is the whole registration

**Files:** Create `src/publishable/templates/discovery.py`; Modify `src/publishable/__init__.py`; Test `tests/test_templates.py`

**Produces:** `register_template(name: str)` — a decorator returning the class unchanged, recording `(name, cls)` into a module-level *pending* list that discovery drains. Exported from `publishable` and in `__all__`.

- [ ] **Step 1: Write the failing test**

```python
def test_register_template_returns_the_class_and_records_the_name():
    """§ Creating a plugin: a local template's `@register_template` argument
    "is therefore the whole of its registration". The decorator must return the
    class unchanged — a decorator that returned the registration record would
    break `class X(BaseTemplate)` for every later reference to X."""
    from publishable import register_template
    from publishable.templates.discovery import drain_pending

    @register_template("my_assay")
    class MyAssay(BaseTemplate):
        pass

    assert MyAssay.__name__ == "MyAssay"          # returned unchanged
    assert issubclass(MyAssay, BaseTemplate)
    assert drain_pending() == [("my_assay", MyAssay)]
    assert drain_pending() == []                  # draining empties it
```

- [ ] **Step 2: Run it and confirm it fails** on the import, not on an assertion.
- [ ] **Step 3: Implement** the decorator and `drain_pending()`. The pending list is module-level; **the registry mapping is not** — that is task 6's property and this task must not pre-empt it by keeping a persistent name→class dict.
- [ ] **Step 4: Export** from `publishable/__init__.py` and add to `__all__`.
- [ ] **Step 5: Mutate** — make the decorator return the record rather than the class; the first assertion must fail. Then make `drain_pending` not clear; the last assertion must fail.
- [ ] **Step 6: Commit.**

---

