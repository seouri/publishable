## Task 17: Import-failure containment, `SystemExit` included

**Files:** Modify `src/publishable/plugins.py`, `docs/reference.md`, `tests/test_plugins.py`.

**Interfaces:**
- Consumes: `discovery.drain_pending() -> list[tuple[str, type[BaseTemplate]]]`, which hands over
  the accumulated registrations and empties the buffer; `discovery.PartialLoadError(message, *,
  code, partial_templates)`; `EntryPoint.load()`.
- Produces: `plugins.load_entry_point(ep: EntryPoint) -> Any`, raising `PartialLoadError` ·
  `E-PLUGIN-LOAD` and carrying whatever the failed import left in the pending buffer.

**The pattern to copy is the widened one, and copying the old one drops the payload.** H7c changed
`discover_local`'s two `except` arms from *discarding* the pending buffer to
`partial.extend(cls for _, cls in drain_pending())`, so a file that raised **after** its
`@register_template` still hands back the class whose declarations a credential redaction reads. A
plugin module raises at the same point in its own life, so it needs the same drain — and copying the
pre-H7c shape would silently drop it. That is the whole of what "WIDENED" means in the re-scoping's
task 17 row.

**`SystemExit` needs its own `except`.** It is a `BaseException`, so a broad `except Exception` does
not see it. A plugin calling `sys.exit()` at module scope, or building an `argparse` parser at
import, would otherwise end the command with the plugin's own exit code and no diagnostic — the one
outcome core is contracted never to produce. `discover_local` and `validate_config`'s entrypoint
import both already carry the pair; this is the third.

**This is the module's only function that imports anything**, and its docstring says so, because the
rest of `plugins.py` exists to answer without importing.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_plugins.py`:

```python
def test_a_plugin_module_that_raises_is_a_coded_refusal_naming_the_distribution(installed):
    """A traceback out of a command is the outcome core is contracted never to
    produce. The distribution is named rather than the module, because a
    distribution is what a reader uninstalls or pins."""
    from publishable.errors import ContractError
    from publishable.plugins import load_entry_point, scan_group

    site = installed(
        "dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "boom_module:resolve"}}
    )
    (site / "boom_module.py").write_text("raise RuntimeError('kaboom')\n")

    ep = scan_group("publishable.resolvers")["plate_wells"][0]
    with pytest.raises(ContractError) as excinfo:
        load_entry_point(ep)

    assert excinfo.value.code == "E-PLUGIN-LOAD"
    message = str(excinfo.value)
    assert "plate_wells" in message
    assert "dist-one 1.0" in message
    assert "RuntimeError" in message


def test_a_plugin_module_calling_sys_exit_is_contained_too(installed):
    """`SystemExit` is a `BaseException`, so the broad arm does not see it — the
    mutation for this is deleting the `except SystemExit` and watching pytest
    exit rather than report."""
    from publishable.errors import ContractError
    from publishable.plugins import load_entry_point, scan_group

    site = installed(
        "dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "exiting_module:resolve"}}
    )
    (site / "exiting_module.py").write_text("import sys\nsys.exit(3)\n")

    ep = scan_group("publishable.resolvers")["plate_wells"][0]
    with pytest.raises(ContractError) as excinfo:
        load_entry_point(ep)

    assert excinfo.value.code == "E-PLUGIN-LOAD"
    assert "SystemExit: 3" in str(excinfo.value)


def test_a_class_a_failing_plugin_declared_before_raising_is_carried(installed):
    """The widened pattern. A class body finishes running before its own
    decorator is reached, so a module that raises AFTER registering still leaves
    a fully formed class — carried on the refusal so a caller that never gets a
    usable object can still read what it declared.
    """
    from publishable.plugins import load_entry_point, scan_group

    site = installed(
        "dist-one", "1.0", {"publishable.templates": {"my_assay": "half_module:T"}}
    )
    (site / "half_module.py").write_text(
        "from publishable import BaseTemplate, register_template\n"
        "\n"
        "\n"
        "@register_template('my_assay')\n"
        "class T(BaseTemplate):\n"
        "    required_env = ['SOME_KEY']\n"
        "\n"
        "\n"
        "raise RuntimeError('after registering')\n"
    )

    ep = scan_group("publishable.templates")["my_assay"][0]
    with pytest.raises(Exception) as excinfo:
        load_entry_point(ep)

    carried = getattr(excinfo.value, "partial_templates", None)
    assert carried is not None
    assert [cls.required_env for cls in carried] == [["SOME_KEY"]]


def test_a_plugin_module_that_imports_cleanly_hands_back_its_object(installed):
    """THE HONOURING. Every test above asserts a refusal; without this one a
    `load_entry_point` that raised unconditionally would pass all three."""
    from publishable.plugins import load_entry_point, scan_group

    site = installed(
        "dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "good_module:resolve"}}
    )
    (site / "good_module.py").write_text("def resolve(io, cfg):\n    return ['a unit']\n")

    ep = scan_group("publishable.resolvers")["plate_wells"][0]
    assert load_entry_point(ep)(None, None) == ["a unit"]
```

      **`installed` returns the site directory**, which is on `sys.path`, so writing a module beside
      the `.dist-info` makes it importable — that is why the fixture returns a `Path` rather than
      `None`, and why these are the only tests in the slice whose entry points name a module that
      exists. Note that `test_a_class_a_failing_plugin_declared_before_raising_is_carried` leaves an
      entry in `discovery._pending` if the drain is missing; that is the defect it exists to catch
      and it is **also a leak into the next test**, so run this file twice in a row and confirm both
      runs are green before believing either.

- [ ] **Step 2: Run and see them fail.** `ImportError: cannot import name 'load_entry_point'`.

- [ ] **Step 3: Implement.** In `src/publishable/plugins.py`, add
      `from publishable.templates.discovery import PartialLoadError, drain_pending`, then:

```python
def load_entry_point(ep: EntryPoint) -> Any:
    """Import what `ep` points at, containing every way a plugin's top level can fail.

    **The one function in this module that imports anything.** Everything else
    answers from package metadata, which is the guarantee § Creating a plugin
    justifies the whole mechanism by; this is what a command calls once it has
    resolved a name and actually needs the object.

    `SystemExit` gets its own arm because it is a `BaseException` and the broad
    one below does not see it: a plugin calling `sys.exit()` at module scope, or
    building an `argparse` parser at import, would otherwise end the command with
    the plugin's own exit code and no diagnostic at all.

    Whatever the failed import left in the pending registration buffer is drained
    onto the refusal rather than discarded. A class body finishes running before
    its own `@register_*` call is reached, so a module that raises after
    registering still leaves a fully formed class — and a caller that never gets
    a usable object can still ask that class what credentials it declares. It is
    drained rather than kept for the next load either way: a registration this
    import made is not the next one's to inherit.

    The distribution is named rather than the module, because a distribution is
    what a reader uninstalls or pins.
    """
    try:
        return ep.load()
    except SystemExit as exc:
        raise PartialLoadError(
            f"the entry point `{ep.name}` in `{ep.group}`, from {provider_of(ep)}, called "
            f"`sys.exit()` while importing and registers nothing usable: SystemExit: {exc.code}",
            code="E-PLUGIN-LOAD",
            partial_templates=[cls for _, cls in drain_pending()],
        ) from exc
    except Exception as exc:
        raise PartialLoadError(
            f"the entry point `{ep.name}` in `{ep.group}`, from {provider_of(ep)}, raised "
            f"while importing and registers nothing usable: {exc!r}",
            code="E-PLUGIN-LOAD",
            partial_templates=[cls for _, cls in drain_pending()],
        ) from exc
```

      **`{exc!r}` rather than `{exc}`**, matching `discover_local`'s wording, which is why the test
      asserts `"RuntimeError"` rather than `"kaboom"` alone. **`plugins` importing
      `templates.discovery`** introduces no cycle: `discovery` imports `errors` and `templates.base`
      and nothing else of core's. Confirm with `uv run python -c "import publishable"` before
      running the suite.

- [ ] **Step 4: Document it.** § Errors core raises' `E-PLUGIN-LOAD` row, written by task 2, already
      states the `SystemExit` half and the distribution-naming half. Read it and confirm; fix the
      row here if it does not, rather than adding a second statement.

- [ ] **Step 5: Run and see them pass**, then the whole suite **twice in a row in one command**
      (`uv run pytest -q && uv run pytest -q`) — a drain that fails to empty the buffer shows as a
      second-run failure in `tests/test_templates.py`, whose discovery tests assert on exactly what
      the buffer holds. Expected: predecessor's count **+ 4**.

- [ ] **Step 6: Mutate — three.**

  **(a) Discard instead of draining.** Change both `partial_templates=` expressions to `[]`.
  `test_a_class_a_failing_plugin_declared_before_raising_is_carried` must FAIL on
  `assert [cls.required_env for cls in carried] == [["SOME_KEY"]]`. **Checked against the body:**
  the module registers a class and *then* raises, so the buffer is genuinely non-empty at the
  moment of the raise; a module that raised before registering could not tell this mutant from
  correct code, which is why the fixture's `raise` is the last line.

  **(b) Delete the `except SystemExit` arm.** `test_a_plugin_module_calling_sys_exit_is_contained_too`
  must FAIL — and it will fail by **pytest itself exiting**, not by an assertion, since `SystemExit`
  propagates. Run it as `uv run pytest tests/test_plugins.py -q -k sys_exit` on its own and read the
  exit code; that is the observable, and it is the whole reason the arm exists.

  **(c) Never drain on the broad arm only.** Change the `except Exception` arm's
  `partial_templates=` to `[]` while leaving the `SystemExit` arm draining. The same test as (a)
  must FAIL, because its fixture raises a `RuntimeError`. **This is what proves the two arms are
  separately wired**, which mutation (a) does not.

  After each: `find . -name __pycache__ -type d -exec rm -rf {} +`, edit the file back by hand,
  re-run, confirm green.

- [ ] **Step 7: Which deliverable no mutation reaches.** **`load_entry_point` has no production
      caller in this slice**, for the same reason `check_registration` does not: nothing in Part A
      loads a plugin. Named here and filed against the same unowned work. The `from exc` chaining is
      unpinned — no test reads `__cause__` — and deliberately so; adding an assertion would pin a
      traceback detail no document states.

- [ ] **Step 8: Verify and commit.** All four commands.
      `feat: plugin import-failure containment, SystemExit included, draining the pending buffer`

---

