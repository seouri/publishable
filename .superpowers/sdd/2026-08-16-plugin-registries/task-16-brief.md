## Task 16: The decorator-vs-key check at load

**Files:** Modify `src/publishable/plugins.py`, `docs/reference.md`, `tests/test_plugins.py`.

**Interfaces:**
- Consumes: `importlib.metadata.EntryPoint`, whose `.name` and `.group` this reads and whose
  `.load()` it does not call; `plugins.RESOLVERS`, `plugins.PROBES`, `artifacts.WRITERS`,
  `artifacts.READERS`.
- Produces: `plugins.check_registration(ep: EntryPoint, declared: Sequence[str]) -> None`, raising
  `ContractError` · `E-PLUGIN-DECORATOR`; `plugins.declared_names(group: str, obj: object) ->
  list[str]`, the names a loaded object is registered under in that group's mapping.

**Why the caller supplies `declared` rather than this function computing it.** The four function
registries map name → object, so "what did this object declare" is a reverse lookup over a mapping
`plugins.py` holds. Templates do not: `register_template` records into `discovery._pending`, which a
discovery pass drains, and reaching into that buffer from here would make one function depend on
whether anything had drained it yet. So the *comparison* lives here, in one place, and each caller
computes the declared names the way its own group records them. `declared_names` is provided for the
four that share a shape.

**`validate` cannot see this disagreement, and that is a property rather than a gap.** The check
compares a decorator argument against an entry-point key, and a decorator argument exists only once
the module has been imported. `validate` answers a name from metadata and never holds the decorated
object. So this is reached at `run` and `dry-run` — **and in Part A it is reached nowhere**, because
nothing here imports a plugin. The task ships the comparison and its unit tests; the call site
arrives with plugin loading, which no task in this slice owns. Stated in the § Errors row task 2
wrote and stated again here.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_plugins.py`:

```python
def test_a_decorator_argument_matching_its_key_is_accepted(registries):
    """The honouring. Without it, a check that raised unconditionally passes
    every refusal below."""
    from importlib.metadata import EntryPoint

    from publishable.plugins import check_registration, declared_names, register_resolver

    @register_resolver("plate_wells")
    def resolve(io, cfg):
        return []

    ep = EntryPoint(name="plate_wells", value="pkg.r:resolve", group="publishable.resolvers")
    assert declared_names("publishable.resolvers", resolve) == ["plate_wells"]
    check_registration(ep, declared_names("publishable.resolvers", resolve))


def test_a_decorator_argument_disagreeing_with_its_key_is_refused(registries):
    """Two spellings of one name with no rule for which is canonical is a drift
    nobody detects until a config names the loser — the defaults-file argument."""
    from importlib.metadata import EntryPoint

    from publishable.errors import ContractError
    from publishable.plugins import check_registration, declared_names, register_resolver

    @register_resolver("plate_positions")
    def resolve(io, cfg):
        return []

    ep = EntryPoint(name="plate_wells", value="pkg.r:resolve", group="publishable.resolvers")
    with pytest.raises(ContractError) as excinfo:
        check_registration(ep, declared_names("publishable.resolvers", resolve))

    assert excinfo.value.code == "E-PLUGIN-DECORATOR"
    message = str(excinfo.value)
    assert "plate_wells" in message      # the key
    assert "plate_positions" in message  # the decorator argument
    assert "pkg.r:resolve" in message    # where to look


def test_an_object_registered_under_several_names_satisfies_any_of_them(registries):
    """One function may serve two keys — a plugin registering the same resolver
    under an old name and a new one is not a disagreement. The check is
    membership, not equality, and a fixture with one name could not tell the two
    readings apart."""
    from importlib.metadata import EntryPoint

    from publishable.plugins import check_registration, declared_names, register_resolver

    def resolve(io, cfg):
        return []

    register_resolver("plate_wells")(resolve)
    register_resolver("plate_positions")(resolve)

    for key in ("plate_wells", "plate_positions"):
        ep = EntryPoint(name=key, value="pkg.r:resolve", group="publishable.resolvers")
        check_registration(ep, declared_names("publishable.resolvers", resolve))


def test_an_object_that_registered_nothing_is_refused_and_says_so(registries):
    """The distinguishable branch: "declared a different name" and "declared no
    name at all" are different mistakes with different remedies, so their
    messages must differ. Pinned separately, because both carry one code."""
    from importlib.metadata import EntryPoint

    from publishable.errors import ContractError
    from publishable.plugins import check_registration

    ep = EntryPoint(name="plate_wells", value="pkg.r:resolve", group="publishable.resolvers")
    with pytest.raises(ContractError) as excinfo:
        check_registration(ep, [])

    message = str(excinfo.value)
    assert "calls no `@register_" in message   # only this branch says this
    assert "declares `" not in message         # and only the other branch says that
```

- [ ] **Step 2: Run and see them fail.** `ImportError: cannot import name 'check_registration'`.

- [ ] **Step 3: Implement.** In `src/publishable/plugins.py`, add
      `from collections.abc import Sequence` to the imports, then:

```python
def _registry_for(group: str) -> dict[str, Callable[..., Any]] | None:
    """The mapping a group's decorator fills, or `None` for a group whose
    registration is not a name-to-object mapping.

    Templates are the `None` case: `register_template` records into a pending
    buffer a discovery pass drains, so what a template class declared is known to
    whoever drained it and not to this module.
    """
    return {
        "publishable.resolvers": RESOLVERS,
        "publishable.probes": PROBES,
        "publishable.writers": WRITERS,
        "publishable.readers": READERS,
    }.get(group)


def declared_names(group: str, obj: object) -> list[str]:
    """Every name `obj` is registered under in `group`'s mapping, in name order.

    A list rather than one name because one function may serve two keys — a
    plugin keeping an old resolver name alongside a new one registers twice — and
    that is not a disagreement.
    """
    registry = _registry_for(group)
    if registry is None:
        return []
    return sorted(name for name, registered in registry.items() if registered is obj)


def check_registration(ep: EntryPoint, declared: Sequence[str]) -> None:
    """The `@register_*` argument against the entry-point key that named it.

    `reference.md` § Creating a plugin: the entry point is the registration and
    the decorator is a declaration checked against it. Two spellings of one name
    with no rule for which is canonical is a drift nobody detects until a config
    names the loser, so loading fails naming both rather than letting one
    silently win.

    Takes the declared names rather than computing them, so one comparison serves
    every group: a template's registration lands in a pending buffer its
    discovery pass drains, and a reverse lookup here would depend on whether
    anything had drained it yet.

    Reached only where an object behind a key has actually been loaded, which is
    not `validate` — `validate` answers a name from package metadata and never
    holds the object. That is the guarantee working rather than a check missing.
    """
    if ep.name in declared:
        return
    if declared:
        detail = f"declares `{'`, `'.join(declared)}` instead"
    else:
        detail = "calls no `@register_*` naming it"
    raise ContractError(
        f"the entry point `{ep.name}` in `{ep.group}` points at `{ep.value}`, which "
        f"{detail} — the entry point is the registration and the decorator is a "
        "declaration checked against it, so two spellings of one name are refused "
        "rather than resolved. Make them agree",
        code="E-PLUGIN-DECORATOR",
    )
```

      **The two branches' messages are distinguishable and each is pinned separately**, per Global
      Constraints: only the disagreement branch contains "declares `", and only the
      registered-nothing branch contains "calls no `@register_". Check that neither fragment appears
      in the other's rendered message before believing the tests — the invariant tail is shared, so
      a fragment chosen from it would be vacuous.

- [ ] **Step 4: Document the consequence.** § Errors core raises' `E-PLUGIN-DECORATOR` row, written
      by task 2, already states that `validate` cannot see the disagreement. Read it and confirm; if
      it does not, fix the row here rather than adding a second statement elsewhere.

- [ ] **Step 5: Run and see them pass**, then the whole suite. Expected: predecessor's count **+ 4**.
      `uv run mypy` must be clean — `EntryPoint(name=…, value=…, group=…)` is its documented
      constructor and is typed.

- [ ] **Step 6: Mutate — three.**

  **(a) Compare against the first declared name.** Change `if ep.name in declared:` to
  `if declared and ep.name == declared[0]:`.
  `test_an_object_registered_under_several_names_satisfies_any_of_them` must FAIL on its
  `plate_positions` iteration — `declared` sorts to `["plate_positions", "plate_wells"]`, so
  `plate_wells` fails. **Checked against the body:** it loops over both keys, which is what makes
  membership distinguishable from equality; a single-key fixture would pass under both.

  **(b) Collapse the two message branches.** Change the `else` to produce the same string as the
  `if`. `test_an_object_that_registered_nothing_is_refused_and_says_so` must FAIL on
  `assert "calls no \`@register_" in message`. **Checked against the body:** the empty-`declared`
  call renders `declares `` instead` under the mutant, which contains neither asserted fragment in
  the right direction — and the test's second assertion, `"declares \`" not in message`, catches it
  from the other side.

  **(c) Refuse nothing.** Delete the raise. Both refusal tests FAIL with `DID NOT RAISE`, and
  `test_a_decorator_argument_matching_its_key_is_accepted` still passes — which is the point of
  having it: it is what proves the refusal tests are about a disagreement rather than about the
  function raising.

  After each: `find . -name __pycache__ -type d -exec rm -rf {} +`, edit the file back by hand,
  re-run, confirm green.

- [ ] **Step 7: Which deliverable no mutation reaches, stated plainly.** **`check_registration` has
      no production caller in this slice and no task in Part A or Part B gives it one.** It is
      reached when a plugin's entry point is loaded, which is the same unowned work
      `spec-defects.md`'s `## OPEN — an installed template's name resolves but its class is never
      loaded` describes for templates and which the apparatus slice will need for probes. The tests
      here exercise the comparison directly and prove nothing about where it is called from.
      **`_registry_for`'s `None` branch for templates** is pinned only by `declared_names` returning
      `[]`, which no test asserts — add nothing; a test that pinned it would pin the absence of a
      template registry mapping, which is a design choice stated in the docstring.

- [ ] **Step 8: Verify and commit.** All four commands.
      `feat: the decorator-vs-key comparison, and the consequence that validate cannot see it`

---

