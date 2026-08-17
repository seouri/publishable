## Task 24: resolver name resolution and load

**Files:** Modify `src/publishable/units.py`, `src/publishable/validate.py`,
`docs/reference.md`, `docs/superpowers/spec-defects.md`, `tests/test_units.py`,
`tests/test_validate.py`.

**Interfaces:**
- Consumes: `plugins.scan_group(group) -> dict[str, list[EntryPoint]]` (keys in name order,
  claimants in provider order, metadata only); `plugins.names(group) -> list[str]`;
  `plugins.load_entry_point(ep) -> Any`, which drains the pending template buffer before and after,
  calls `ep.load()`, and wraps `SystemExit` and `Exception` into
  `PartialLoadError(code="E-PLUGIN-LOAD")` — a `ContractError` subclass;
  `plugins.declared_names(group, obj) -> list[str]`, which reverse-looks-up `plugins.RESOLVERS`;
  `plugins.check_registration(ep, declared) -> None`, raising `ContractError` ·
  `E-PLUGIN-DECORATOR`. All read from `src/publishable/plugins.py`.
- Produces: `units._resolver_for(name: str) -> Callable[..., Any]`, raising `ContractError` ·
  `E-RESOLVER-UNKNOWN` / `E-PLUGIN-LOAD` / `E-PLUGIN-DECORATOR`. Nothing calls it yet — task 25's
  dispatch is its caller. § Errors' `E-RESOLVER-UNKNOWN` `Not yet emitted:` marker struck.

**This closes four of the six shipped-but-unread surfaces Part A filed**, by name:
`plugins.RESOLVERS`, `load_entry_point`, `check_registration` and `declared_names` all get their
first production caller here. `spec-defects.md`'s `## OPEN — PROBES and RESOLVERS are written by
their decorators and read by nothing` is amended in task 30, once the whole chain is wired, not
here — its list also names `provenance.plugin_versions`, which is task 30's.

**Decision 4: `check_registration` runs at `validate`.** Decision 1 settles it — `validate` already
loads the resolver in order to run it, so the object is in hand and the decorator-vs-key
disagreement is knowable there. Deferring it to `run` would report at `run` a fault `validate` had
the evidence for, which is the shape `CLAUDE.md` calls a check `validate` cannot see.

**The `E-PLUGIN-COLLISION` → `E-PLUGIN-LOAD` re-code, decided here.** `spec-defects.md`'s
`## OPEN — a core-suffix claim's E-PLUGIN-COLLISION becomes E-PLUGIN-LOAD once loading is wired —
Owner: H7b Part B` names two acceptable resolutions. **Take the first: let the re-code stand, and
add one sentence to `E-PLUGIN-COLLISION`'s row recording the precedent.** The argument against the
second: catching `ContractError` ahead of `load_entry_point`'s broad arm would let *any* coded
`ContractError` a plugin's top level raises escape the containment under whatever code it happened
to carry — a fail-open of exactly the shape `CLAUDE.md` § Answering a question with a proxy names,
and one that would defeat the reason `load_entry_point` is broad. Narrowing the catch to the single
code `E-PLUGIN-COLLISION` would instead make `load_entry_point` — a group-generic function — know
about a code only two of the five groups can raise. The precedent already exists and is documented:
§ Errors accepts `E-TEMPLATE-LOAD` swallowing a coded error from a local template's top level, for
the same reason. Strike the `spec-defects.md` entry as CLOSED with this argument.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_units.py`:

```python
def test_an_unregistered_resolver_name_is_refused_from_metadata_alone(installed, registries):
    """`E-RESOLVER-UNKNOWN`, and the message names what it did find — the ordinary
    cause is a spelling and the ordinary remedy is reading the list."""
    from publishable.errors import ContractError
    from publishable.units import _resolver_for

    installed("dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "no_one:resolve"}})
    with pytest.raises(ContractError) as excinfo:
        _resolver_for("plate_welz")
    assert excinfo.value.code == "E-RESOLVER-UNKNOWN"
    assert "plate_welz" in str(excinfo.value)
    assert "plate_wells" in str(excinfo.value)  # the list it names


def test_a_registered_resolver_name_loads_the_object_behind_it(installed, registries, tmp_path):
    """THE HONOURING. Without this, a `_resolver_for` returning `None` for every
    name would pass every refusal test above and below it."""
    from publishable.units import _resolver_for

    site = installed(
        "dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "loadable_r24:resolve"}}
    )
    (site / "loadable_r24.py").write_text(
        "from publishable import register_resolver\n\n\n"
        '@register_resolver("plate_wells")\n'
        "def resolve(io, cfg):\n    return ['loaded']\n"
    )
    importlib.invalidate_caches()
    try:
        assert _resolver_for("plate_wells")(None, None) == ["loaded"]
    finally:
        sys.modules.pop("loadable_r24", None)


def test_a_resolver_whose_module_raises_is_contained_as_a_plugin_load(
    installed, registries
):
    """`E-PLUGIN-LOAD`'s first production caller. The distribution is named rather
    than the module, since a distribution is what a reader uninstalls or pins."""
    from publishable.errors import ContractError
    from publishable.units import _resolver_for

    site = installed(
        "dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "broken_r24:resolve"}}
    )
    (site / "broken_r24.py").write_text("raise RuntimeError('module scope blew up')\n")
    importlib.invalidate_caches()
    try:
        with pytest.raises(ContractError) as excinfo:
            _resolver_for("plate_wells")
    finally:
        sys.modules.pop("broken_r24", None)
    assert excinfo.value.code == "E-PLUGIN-LOAD"
    assert "dist-one 1.0" in str(excinfo.value)


def test_a_decorator_argument_disagreeing_with_the_entry_point_key_is_refused(
    installed, registries
):
    """`E-PLUGIN-DECORATOR`'s first production caller, and decision 4's siting:
    the object is in hand at `validate`, so the disagreement is knowable there."""
    from publishable.errors import ContractError
    from publishable.units import _resolver_for

    site = installed(
        "dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "misnamed_r24:resolve"}}
    )
    (site / "misnamed_r24.py").write_text(
        "from publishable import register_resolver\n\n\n"
        '@register_resolver("plate_positions")\n'
        "def resolve(io, cfg):\n    return []\n"
    )
    importlib.invalidate_caches()
    try:
        with pytest.raises(ContractError) as excinfo:
            _resolver_for("plate_wells")
    finally:
        sys.modules.pop("misnamed_r24", None)
    assert excinfo.value.code == "E-PLUGIN-DECORATOR"
    assert "plate_wells" in str(excinfo.value)
    assert "plate_positions" in str(excinfo.value)
```

      (`tests/test_units.py` needs `import importlib`, `import sys` and `import pytest` — check
      which are already present before adding, and read its existing module-level names before
      choosing any helper name.)

- [ ] **Step 2: Run and see it fail.** `ImportError: cannot import name '_resolver_for'`.

- [ ] **Step 3: Implement.** In `src/publishable/units.py`, add to the imports
      `from collections.abc import Callable` (extend the existing `collections.abc` import) and

```python
from publishable.plugins import check_registration, declared_names, load_entry_point, scan_group
```

      then, above `resolve_units`:

```python
RESOLVER_GROUP = "publishable.resolvers"


def _resolver_for(name: str) -> Callable[..., Any]:
    """The callable `data.units.from.resolver` names, or the refusal that answers instead.

    Three steps, three codes, in the order the information arrives:

    - **The name**, answered from package metadata alone (`scan_group`), so a name
      no installed distribution registers costs no import at all —
      `reference.md` § Creating a plugin makes that the whole argument for entry
      points. `E-RESOLVER-UNKNOWN`, naming every member of the group it did find,
      because the ordinary cause is a spelling.
    - **The object**, through `load_entry_point`, the one function in core that
      calls `EntryPoint.load()`. Every way a plugin's top level can fail arrives
      as `E-PLUGIN-LOAD`, including `SystemExit`.
    - **The declaration against the key** (`check_registration` over
      `declared_names`), `E-PLUGIN-DECORATOR`. Checked here rather than deferred
      to `run`: the object is already in hand, and reporting at `run` a fault
      `validate` had the evidence for is the shape this repo refuses.

    A collision between two distributions claiming this key is **not** decided
    here. `validate._check_plugin_collisions` reports it as `E-PLUGIN-COLLISION`
    for every config, from metadata, over the complete claim set in name order —
    the first claimant is used here rather than re-deciding the tie, since a
    verdict computed twice is a verdict that can disagree with itself.
    """
    found = scan_group(RESOLVER_GROUP)
    claimants = found.get(name)
    if not claimants:
        listed = ", ".join(found) if found else "none installed"
        raise ContractError(
            f"`data.units.from.resolver` names `{name}`, which no installed distribution "
            f"registers in the `{RESOLVER_GROUP}` entry-point group (registered: {listed})",
            code="E-RESOLVER-UNKNOWN",
        )
    ep = claimants[0]
    fn = load_entry_point(ep)
    check_registration(ep, declared_names(RESOLVER_GROUP, fn))
    return fn
```

      In `docs/reference.md`, strike `E-RESOLVER-UNKNOWN`'s **`Not yet emitted:`** clause — the
      whole clause, not just the marker word, since the sentence that follows it
      (*"the resolver source is refused wholesale in this build, and this code replaces that refusal
      when the dispatch lands"*) is the claim that expires. Prefer deleting to rewriting.

      In `E-PLUGIN-COLLISION`'s row, append: *"A writer or reader claiming a core suffix from inside
      a plugin's top level raises this at decoration time, which is inside the import
      [`E-PLUGIN-LOAD`](#errors-core-raises) contains — so a load reports the containing code, the
      same substitution `E-TEMPLATE-LOAD` already makes for a coded error from a local template's
      top level."*

      In `docs/superpowers/spec-defects.md`, strike `## OPEN — a core-suffix claim's
      `E-PLUGIN-COLLISION` becomes `E-PLUGIN-LOAD` once loading is wired — **Owner: H7b Part B**`
      as CLOSED, appending the argument above rather than editing the entry's body.

- [ ] **Step 4: Run and see it pass.** `uv run pytest` → **2070 + 4 = 2074 passed**, 1 skipped,
      2 xfailed. Then the other three commands.

- [ ] **Step 5: Mutate.** In `src/publishable/units.py`, delete the `check_registration(...)` line
      from `_resolver_for`.
      `tests/test_units.py::test_a_decorator_argument_disagreeing_with_the_entry_point_key_is_refused`
      must **FAIL** with "DID NOT RAISE". **Checked against the test body:** the fixture's module
      registers under `plate_positions` while the entry point declares `plate_wells`, so the two
      spellings genuinely differ and `declared_names` genuinely returns the other one — the
      distinction survives the deletion only if something asserts it, and that test does.

      Second mutation, because the first says nothing about the metadata-only half: replace
      `claimants = found.get(name)` with `claimants = next(iter(found.values()), None)`.
      `test_an_unregistered_resolver_name_is_refused_from_metadata_alone` must **FAIL** — a
      misspelled name would resolve to the one installed claimant instead of raising.

      **Non-discriminating mutation, named so nobody prescribes it:** *"swap `claimants[0]` for
      `claimants[-1]`"* cannot fail. Every fixture here installs one distribution per name, so the
      two indices select the same object. The mutation that could discriminate would need two
      distributions claiming `plate_wells` — which is `E-PLUGIN-COLLISION`'s fixture, and that
      collision is reported by `validate._check_plugin_collisions` rather than decided here, so the
      order this function picks in is deliberately not load-bearing.

- [ ] **Step 6: Commit.** `units: resolve a resolver name from metadata, then load the object behind it`

---

