## Task 22: does `validate` import a plugin — the decision, and the five sentences it moves

**Files:** Modify `docs/reference.md`, `src/publishable/plugins.py`, `tests/test_plugins.py`,
`tests/test_templates.py`, `tests/test_validate.py`.

**Interfaces:**
- Consumes: § Errors `validate` reports' early-return prose; § Errors core raises' `E-PLUGIN-LOAD`
  and `E-PLUGIN-DECORATOR` rows; `plugins.py`'s module docstring and `check_registration`'s
  docstring; § Where units come from's paragraph beginning *"It runs at `validate` and `dry-run`"*;
  § Creating a plugin's sentence *"`validate` can answer 'no installed package registers
  `plate_wells`' without importing a line of that package"*.
- Produces: no `src/` behaviour change. Five prose sites carrying the **narrowed** claim; two
  existing tests extended to pin it; one new `validate`-level test pinning the negative half.

**The decision, settled by the spec's decision 1 and restated here so no implementer re-opens it.**
`validate` **does** import a plugin when it runs a resolver. § Where units come from is explicit and
argued: a resolver *"runs at `validate` and `dry-run`, not only at `run`"*, because every unit check
is a question about the resolved table, and deferring them costs four hours into a run; § The
apparatus core can only observe states the general line the same way — *"`validate` may read your
config and your input, and may not reach anything outside the machine."* Executing a resolver
imports it. **What survives, and it is the sentence that matters**, is § Creating a plugin's own,
narrower guarantee: a **name** is answered from package metadata, so `validate` can say "no
installed package registers `plate_wells`" without importing a line of that package. `CLAUDE.md`'s
invariant is worded the same narrow way and survives untouched. It is the five *generalizations* of
it, written while nothing loaded anything, that break.

**Three sites are false unconditionally; two turn on decision 4, which the spec settles as
`check_registration` at `validate`** — so all five move here. Separated anyway, because rewriting a
sentence that did not need rewriting is a habit this repo has paid for:

| Site | Why it moves |
|---|---|
| § Errors `validate` reports' early-return prose, *"`validate` never imports a plugin, so neither check runs there"* | Unconditional. Executing a resolver imports it |
| § Errors core raises, `E-PLUGIN-LOAD`'s *"never at `validate`"* | Unconditional. `load_entry_point` **is** the import, it raises that code, and task 24 makes `validate` call it |
| `plugins.py` module docstring's *"`validate` is not such a caller"* | Unconditional, same reason |
| § Errors core raises, `E-PLUGIN-DECORATOR`'s *"`validate` cannot see this disagreement"* | Contingent on decision 4, which says `validate` calls `check_registration`; its *"never holds the decorated object"* clause is false either way |
| `plugins.py` `check_registration`'s *"not `validate`"* | Contingent on the same decision |

**Re-argue, do not append an exception clause.** `plugins.py`'s module docstring is the paragraph
that *justifies* the entry-point mechanism; Part A's own review finding C1 was made to take the
re-argument fix rather than the exception-clause fix. The replacement argument is: resolving a name
imports nothing, and that is what makes a *negative* answer free; loading is a separate, named
operation a caller reaches for **only once a name has resolved and the object is actually needed**,
which `validate` does for a resolver source and for nothing else.

**The trap this task exists for.** The no-import invariant is pinned by two tests —
`tests/test_plugins.py::test_the_scan_imports_nothing` and
`tests/test_templates.py::test_get_template_imports_nothing_for_an_installed_claim` — **and Part B
touches neither.** A resolver that imports at the wrong moment leaves both green, so the guarantee
would survive only as prose. Extending the two tests is necessary and **not sufficient**: both sit
below `validate_config`, and the failure mode is a load at the *wrong moment inside* `validate`. So
this task adds a third test at the `validate_config` level.

- [ ] **Step 1: Write the failing test.** Extend `tests/test_plugins.py::test_the_scan_imports_nothing`
      — replace its trailing bare `.load()` positive control with the production import path, and
      state which claim survives:

```python
def test_the_scan_imports_nothing(installed, registries):
    """The whole argument for entry points, asserted rather than described, and
    narrowed to the claim that is actually true.

    **A NAME resolves from package metadata without importing** — that is
    § Creating a plugin's guarantee and the whole of it. `validate` does import a
    plugin once it needs the object behind a name: a resolver runs at `validate`,
    which is § Where units come from's design.

    The target is a module that **does** import, and the assertion is that it is
    absent from `sys.modules` after every name-answering call. That is the only
    shape that catches a load: against a target that cannot import, a scan calling
    `.load()` inside a bare `except` returns normally and every assertion still
    holds. `load_entry_point` is the positive control and is the production import
    path rather than a bare `.load()`, so this test states the boundary in the
    terms the code uses: everything that answers a name imports nothing;
    `load_entry_point` imports, by name.
    """
    site = installed(
        "dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "loadable_probe:resolve"}}
    )
    (site / "loadable_probe.py").write_text(
        "from publishable import register_resolver\n\n\n"
        '@register_resolver("plate_wells")\n'
        "def resolve(io, cfg):\n    return []\n"
    )
    importlib.invalidate_caches()
    assert "loadable_probe" not in sys.modules

    found = scan_group("publishable.resolvers")
    assert provider_of(found["plate_wells"][0]) == "dist-one 1.0"
    assert "loadable_probe" not in sys.modules

    assert names("publishable.resolvers") == ["plate_wells"]
    assert "loadable_probe" not in sys.modules

    try:
        loaded = load_entry_point(found["plate_wells"][0])
        assert loaded(None, None) == []
        assert "loadable_probe" in sys.modules
        assert declared_names("publishable.resolvers", loaded) == ["plate_wells"]
    finally:
        sys.modules.pop("loadable_probe", None)
```

      (add `load_entry_point`, `declared_names` and `names` to that file's import from
      `publishable.plugins`, and request `registries` because the target now registers for real).

      Extend `tests/test_templates.py::test_get_template_imports_nothing_for_an_installed_claim`
      with the same-shaped statement of the surviving claim — append, after its existing
      assertions:

```python
    # The claim that survives, said in the terms the documents now carry: a NAME
    # is answered from metadata. Loading is a separate, named operation, and this
    # is the control proving the fixture CAN import — without it every assertion
    # above holds for a target that simply cannot be imported at all.
    from publishable.plugins import load_entry_point, scan_group

    ep = scan_group("publishable.templates")["vendor_assay"][0]
    try:
        assert load_entry_point(ep).__name__ == "T"
        assert "loadable_tpl" in sys.modules
    finally:
        sys.modules.pop("loadable_tpl", None)
```

      And add, in `tests/test_validate.py`, the pair that catches a load at the wrong moment:

```python
def test_validate_imports_no_plugin_for_a_config_that_names_no_resolver(
    installed, registries, write_config
):
    """The narrowed invariant, pinned where it can actually die.

    The two tests that pinned the old, wider claim sit at `scan_group` and
    `get_template`; neither breaks if `validate` loads a resolver at the wrong
    moment. This one does: the distribution is installed and its target genuinely
    imports, and the config's `data.units.from` is a table, so nothing about this
    config needs the object behind `plate_wells`. A `validate` that loaded the
    group unconditionally — or loaded before deciding what shape `from` is —
    turns this red.

    Its positive companion is task 24's
    `test_a_resolver_source_loads_the_object_behind_the_name`, which asserts the
    module IS present for a config that names one. Without that half, this test
    would pass on a `validate` that had no resolver path at all.
    """
    site = installed(
        "dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "loadable_units:resolve"}}
    )
    (site / "loadable_units.py").write_text(
        "from publishable import register_resolver\n\n\n"
        '@register_resolver("plate_wells")\n'
        "def resolve(io, cfg):\n    return []\n"
    )
    importlib.invalidate_caches()
    try:
        assert codes(write_config()) == set()
        assert "loadable_units" not in sys.modules
    finally:
        sys.modules.pop("loadable_units", None)
```

      (`tests/test_validate.py` needs `import importlib` and `import sys` at the top; check whether
      either is already there before adding.)

- [ ] **Step 2: Run and see it fail.** The two extended tests fail on the new
      `load_entry_point`/`declared_names` assertions if the names are not imported; the new
      `test_validate.py` test passes today — **and that is expected and is the point**: it is a
      regression pin written before the behaviour it guards against exists. Record in the commit
      message that it is green on arrival, so nobody later mistakes it for a test that was never
      run. Its can-fail proof is Step 5's mutation.

- [ ] **Step 3: Implement.** No `src/` behaviour change. Rewrite the five prose sites:

      In `docs/reference.md`, § Errors `validate` reports' early-return prose, replace
      *"`E-PLUGIN-DECORATOR` and `E-PLUGIN-LOAD` are not reported by `validate` at all, early-return
      or not — `validate` never imports a plugin, so neither check runs there."* with:

      > `E-PLUGIN-DECORATOR` and `E-PLUGIN-LOAD` are reported by `validate` only where it actually
      > loads a plugin, which is a [resolver source](#where-units-come-from) and nothing else —
      > resolving a *name* is answered from package metadata and imports nothing, so a config that
      > names no resolver reaches neither check. Both are findings rather than early returns:
      > `_check_units` reports what resolution raised and the pass continues.

      In `E-PLUGIN-LOAD`'s row, replace *"reached, once something imports a plugin, at `run` and
      `dry-run` and never at `validate`"* with *"reached wherever a plugin is imported, which is a
      [resolver source](#where-units-come-from)'s dispatch — at `validate`, `dry-run` and `run`
      alike, since the resolver runs at all three"*, and **delete** the dated *"no task has yet
      given it a production caller either"* sentence rather than rewriting it (task 30 owns the
      other two dated notes; this one dies with its claim).

      In `E-PLUGIN-DECORATOR`'s row, delete the clause *"`validate` answers a name from metadata and
      never holds the decorated object, so **`validate` cannot see this disagreement** either way, a
      property of the guarantee rather than a gap in the check"* and replace it with *"checked
      wherever a plugin is loaded, so a resolver's disagreement is `validate`'s finding as much as
      `run`'s"*. Delete its dated *no production caller* sentence.

      In `src/publishable/plugins.py`'s module docstring, replace the paragraph ending *"`validate`
      is not such a caller"* with a re-argument:

```
Loading the object behind a name is a separate, named operation —
`load_entry_point`, the one function in this module that calls
`EntryPoint.load()` — reached only once a name has resolved and the object is
actually needed. That is what keeps the guarantee above intact where it is
claimed: a *negative* answer costs nothing, because deciding that no installed
package registers `plate_wells` never reaches the package. A caller that does
need the object pays the import, and `validate` is such a caller for exactly one
declaration, `data.units.from.resolver`, whose resolver `reference.md` § Where
units come from puts at `validate` and `dry-run` rather than only at `run`.
```

      In `check_registration`'s docstring, replace *"Meant to run only once an object behind a key
      has actually been loaded — not `validate`, which answers a name from package metadata and
      never holds the object. As measured …"* with *"Meant to run once an object behind a key has
      actually been loaded, wherever that happens — including `validate`, which loads a resolver."*

- [ ] **Step 4: Run and see it pass.** `uv run pytest` → **2066 + 1 = 2067 passed** (the two
      extended tests are edits, not additions), 1 skipped, 2 xfailed. Then the other three commands.

- [ ] **Step 5: Mutate.** Two, because this task's deliverable is half prose.

      **(a) The new validate-level pin can fail.** In `src/publishable/validate.py`, at the top of
      `_check_units`, insert:

```python
        from publishable.plugins import load_entry_point, scan_group

        for eps in scan_group("publishable.resolvers").values():
            load_entry_point(eps[0])
```

      `tests/test_validate.py::test_validate_imports_no_plugin_for_a_config_that_names_no_resolver`
      must **FAIL** on `"loadable_units" not in sys.modules`. **Checked against the test body:** the
      fixture's target is a module that genuinely imports (it registers a resolver and returns a
      list), so the assertion distinguishes "not loaded" from "could not load" — the exact
      distinction Part A's unimportable `no_one:T` fixtures could not make.

      **(b) The extended scan test can fail.** In `src/publishable/plugins.py`, add
      `ep.load()` as the first statement of `scan_group`'s `for ep in entry_points(group=group):`
      loop. `tests/test_plugins.py::test_the_scan_imports_nothing` must **FAIL** on the assertion
      immediately after `scan_group`. **Checked against the test body:** the target now imports
      cleanly, so a `.load()` inside the scan really does put it in `sys.modules`; against the old
      unimportable-target shape this mutation would have been silent, which is why Part A rewrote
      the fixture.

      **What no mutation here reaches:** the five prose sites. No test reads them, and no test
      should — a sentence is not a check. Their verification is the sweep in Step 6.

- [ ] **Step 6: Sweep, then commit.** Prove the rewrite is complete by **naming the file list**,
      never by filtering output:
      `grep -rn "never imports a plugin\|never at \`validate\`\|not such a caller\|cannot see this disagreement" README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md CLAUDE.md src/`
      → must be empty. Can-fail control on the identical file list:
      `grep -rn "without importing a line" README.md docs/reference.md CLAUDE.md src/` → must be
      non-empty, since that is the narrow claim which survives.
      Commit: `docs: validate imports a plugin to run a resolver — narrow the five sentences that said otherwise`

---

