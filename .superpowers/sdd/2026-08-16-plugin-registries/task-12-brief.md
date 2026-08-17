## Task 12: `register_resolver`, exported

**Files:** Modify `src/publishable/plugins.py`, `src/publishable/__init__.py`,
`docs/reference.md`, `tests/test_plugins.py`.

**Interfaces:**
- Consumes: `publishable/__init__.py`'s import block and its `__all__`, which today lists
  `ArtifactError`, `ArtifactExistsError`, `BaseExperiment`, `BaseStep`, `BaseTemplate`,
  `ContractError`, `Estimate`, `Param`, `PublishableError`, `Unit`, `register_template`;
  `discovery.register_template(name) -> Callable[[type[BaseTemplate]], type[BaseTemplate]]`, the
  shape every registry decorator follows — record and return unchanged.
- Produces: `plugins.RESOLVERS: dict[str, Callable[..., Any]]`;
  `plugins.register_resolver(name: str) -> Callable[[F], F]`, exported from `publishable`; the
  § The importable surface `Status` cell for `register_resolver` moved to `built`.

**What this task deliberately does not build, and where it says so.** `register_resolver` fills a
mapping when a plugin module is imported, and **nothing in Part A imports a plugin module.** So the
decorator has no production caller in this slice and `RESOLVERS` is populated only by a test. That
is not the shipped-but-unread shape the traps name — `register_probe` is, and task 13 ships its
reader for exactly that reason. A resolver's reader is `resolve_units`' dispatch, which is Part B
task 23, and this task's own text names it. **The export is what a plugin author needs to be able to
write the plugin at all**, which is the whole of what Part A promises.

**Return the object unchanged.** `register_template`'s decorator returns `cls` so
`class X(BaseTemplate)` still resolves for every later reference to `X`; a resolver is a plain
function and the same rule applies for the same reason — `@register_resolver("plate_wells")` above
`def resolve(io, cfg)` must leave `resolve` callable from the module that defined it.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_plugins.py`:

```python
def test_register_resolver_records_the_name_and_returns_the_function(registries):
    """The decorator's two obligations. Returning the object unchanged is the
    half a decorator gets wrong silently: a `None` return leaves the plugin's own
    module holding `None` under the name it just defined, and its own test suite
    is where that surfaces."""
    from publishable.plugins import RESOLVERS, register_resolver

    @register_resolver("plate_wells")
    def resolve(io, cfg):
        return ["a unit"]

    assert RESOLVERS["plate_wells"] is resolve
    assert resolve(None, None) == ["a unit"]  # still callable under its own name


def test_a_resolver_is_importable_from_the_one_root():
    """`reference.md` § The importable surface: everything you write against is
    imported from `publishable` itself. A plugin importing
    `publishable.plugins.register_resolver` is not a supported spelling even
    where it works."""
    import publishable

    assert "register_resolver" in publishable.__all__
    assert publishable.register_resolver is not None
```

      and add the registry-restoring fixture to `tests/conftest.py`, beside `installed`. It goes
      there rather than in `tests/test_plugins.py` because `tests/test_artifacts.py` needs it in
      task 15 and a fixture defined in one test module is invisible from another — putting it in
      one file now and moving it in three tasks' time is churn with a chance to forget:

```python
@pytest.fixture
def registries():
    """Restore the process-level plugin registries around a test that fills them.

    These mappings are module-global by design — a decorator runs at import and
    has nowhere else to put what it recorded — so a test that registers a name
    leaks it into every test after it. Restored by snapshot rather than by
    unsetting what was seen, which covers a test that replaces an entry as well
    as one that adds it. A plain fixture requested by name: the suite's one
    autouse fixture is `conftest`'s environ restore and there may not be a
    second.
    """
    from publishable import artifacts, plugins

    saved = (
        dict(plugins.RESOLVERS),
        dict(plugins.PROBES),
        dict(artifacts.WRITERS),
        dict(artifacts.READERS),
    )
    yield
    for live, was in zip(
        (plugins.RESOLVERS, plugins.PROBES, artifacts.WRITERS, artifacts.READERS),
        saved,
        strict=True,
    ):
        live.clear()
        live.update(was)
```

      **`PROBES`, `WRITERS` and `READERS` are named here although tasks 13, 14 and 15 create them**
      — write the fixture whole in this task and let those tasks use it, rather than growing it
      three times and leaving three chances to forget one. That means this task defines `PROBES` in
      `plugins.py` too, as an empty mapping with no decorator; task 13 adds the decorator. Say so in
      the commit message.

- [ ] **Step 2: Run and see it fail.** `ImportError: cannot import name 'register_resolver'`.

- [ ] **Step 3: Implement.** In `src/publishable/plugins.py`, add to the imports
      `from collections.abc import Callable` and `from typing import Any, TypeVar`, then:

```python
F = TypeVar("F", bound=Callable[..., Any])

RESOLVERS: dict[str, Callable[..., Any]] = {}
"""Every resolver a plugin module registered, by the name a config writes.

Module-global because a decorator runs when a plugin is imported and has nowhere
else to put what it recorded. That is the opposite arrangement from
`templates/registry.py`'s per-call merge, and for a reason that does not apply
here: two projects resolved in one process must never see each other's
`templates/`, but an installed distribution is the same distribution for both.
"""

PROBES: dict[str, Callable[..., Any]] = {}
"""Every apparatus probe a plugin module registered. See `RESOLVERS`."""


def register_resolver(name: str) -> Callable[[F], F]:
    """Record `name -> fn` for this process and return `fn` unchanged.

    The entry point is the registration and this argument is a declaration
    checked against it — `reference.md` § Creating a plugin — so this records
    what the source says and `check_registration` is what compares the two.
    Returned unchanged so the plugin's own module keeps a callable under the
    name it just defined, which is what makes the artifact testable in its own
    suite.
    """

    def decorator(fn: F) -> F:
        RESOLVERS[name] = fn
        return fn

    return decorator
```

      In `src/publishable/__init__.py`, add `from publishable.plugins import register_resolver` and
      `"register_resolver"` to `__all__`, keeping both alphabetical — `ruff`'s `I` rule sorts the
      imports and `__all__` is hand-sorted today, so put it after `"register_template"`? **No:
      `"register_resolver"` sorts before `"register_template"`.** Place it there and confirm by
      reading the list rather than by assuming.

- [ ] **Step 4: Move the `Status` cell.** In § The importable surface, task 3 split the `not yet
      built` row in two. The row whose `Name` cell is `` `register_resolver` · `register_probe` ``
      must now be split again so the two names can carry different statuses:

```
| `register_resolver` | decorator | built | The registry a [`data.units.from.resolver`](#where-units-come-from) name resolves through — see [Creating a plugin](#creating-a-plugin-publishable-plugin-new) |
| `register_probe` | decorator | not yet built | The registry an [`apparatus_probe`](#the-apparatus-core-can-only-observe) name resolves through — see [Creating a plugin](#creating-a-plugin-publishable-plugin-new) |
```

      Splitting rather than rewriting the prose beneath: the sentence "Importing one raises
      `ImportError` today" derives its claim from the `Status` column, and it stays true and
      self-maintaining only while each name's status is its own cell. Also update § The importable
      surface's fenced import example, which already reads
      `from publishable import BaseStep, Estimate, Unit, register_resolver` — read it and confirm no
      change is needed.

- [ ] **Step 5: Run and see them pass** — and run **`uv run pytest -q` whole**, not
      `tests/test_plugins.py` alone. The fixture added in step 1 lives in `tests/conftest.py`, and a
      `conftest.py` that raises at collection fails every file in the suite while collecting one
      file says nothing. Expected: predecessor's count **+ 2**.

- [ ] **Step 6: Mutate — two.**

  **(a) Return `None` from the decorator.** Change `return fn` to `return None` (and let `mypy`
  complain — run the test before fixing the type error).
  `test_register_resolver_records_the_name_and_returns_the_function` must FAIL on
  `assert resolve(None, None) == ["a unit"]` with `TypeError: 'NoneType' object is not callable`.
  **Checked against the body:** the test calls the decorated name after decorating it, which is the
  only thing that can tell "returns the function" from "records the name"; the `RESOLVERS` assertion
  alone passes under this mutant.

  **(b) Record under a fixed key.** Change `RESOLVERS[name] = fn` to `RESOLVERS["resolver"] = fn`.
  The same test must FAIL on `RESOLVERS["plate_wells"]` with a `KeyError`. **Checked against the
  body:** the test looks the name up rather than checking `len(RESOLVERS)`, so the two branches
  differ.

  Revert each by editing the file back; delete `__pycache__`; re-run; confirm green.

- [ ] **Step 7: Which deliverable no mutation reaches.** **`RESOLVERS` has no production reader in
      this slice** — nothing in `src/` looks a resolver up, so a decorator that recorded into a
      throwaway dict would pass every test here. **Part B task 23 closes it**, where `resolve_units`
      dispatches through this mapping. Named rather than hidden, and it is the reason this task is
      *not* the shipped-but-unread shape task 13 guards against: a resolver's reader has an owner
      and a task number, and `register_probe`'s did not until task 13 gave it one.

- [ ] **Step 8: Verify and commit.** All four commands.
      `feat: register_resolver, exported — and the registry-restoring fixture the next three tasks use`

---

