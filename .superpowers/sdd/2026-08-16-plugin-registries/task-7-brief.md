## Task 7: The entry-point metadata scan, five groups, no `.load()`

**Files:** Create `src/publishable/plugins.py`, `tests/test_plugins.py`. Modify `tests/conftest.py`,
`docs/reference.md` (§ Package layout's marker, deferred from task 4).

**Interfaces:**
- Consumes: `importlib.metadata.entry_points(group: str) -> EntryPoints` — the 3.10+ selection API,
  read from the stdlib; `EntryPoint` carries `.name`, `.value`, `.group` and `.dist`, where `.dist`
  is a `Distribution | None` carrying `.name` and `.version`. **`EntryPoint.load()` exists and is
  never called by this module.**
- Produces, consumed by tasks 8, 9, 11, 13, 14, 15, 16, 17 and 20:
  - `GROUPS: tuple[str, ...]` — every entry-point group core reads.
  - `scan_group(group: str) -> dict[str, list[EntryPoint]]` — keys sorted by name, providers within
    a key sorted by provider string. **Metadata only.**
  - `provider_of(ep: EntryPoint) -> str` — `"<distribution> <version>"`, the string every collision
    message names a claimant by.
  - `names(group: str) -> list[str]` — sorted keys of `scan_group(group)`.

**The guarantee this module exists to keep, stated once.** § Creating a plugin justifies the entry
point mechanism by "core resolves it from installed package metadata — so `validate` can answer 'no
installed package registers `plate_wells`' without importing a line of that package". Decision 3
states that invariant of **resolution**, not merely of the negative answer. So no function in this
module calls `.load()`, and no caller added in Part A does either. A check that reaches for the
object behind a name has changed the guarantee whatever it returns.

**The fixture, and what it costs.** See Global Constraints for the full argument and the four
mechanical rules. In short: a directory holding a hand-written `<name>-<version>.dist-info/` with
`METADATA` and `entry_points.txt`, prepended to `sys.path` with `monkeypatch.syspath_prepend`, **is**
an installed distribution to every API this module calls — that is the layout `uv` and `pip` write
and the layout `importlib.metadata` scans for. It costs no build step, no network, no `slow` marker,
no mutation of the project venv, and no new dependency in `pyproject.toml`. It does not exercise
`hatchling` turning a `pyproject.toml` entry-points table into `entry_points.txt`; core reads no
`pyproject.toml`, so that is outside anything a test here could pin, and it is named as a residual
rather than left implicit.

**The fixture goes in `tests/conftest.py`, not in `tests/test_plugins.py`.** Tasks 8, 13, 14, 15, 16
and 17 all need it and three of them write in `tests/test_templates.py` and `tests/test_validate.py`;
a fixture defined in one test module is not visible from another. **Names already at module level in
`tests/conftest.py`:** `_restore_environ`, `git`, `EXPERIMENT_MODULE`, `write_experiment_module`,
`git_repo`. `installed` and `_DIST_METADATA` are free. It is a **plain fixture requested by name**,
never autouse — the suite already has the only autouse fixture it is allowed, and adding a second is
forbidden by Global Constraints. `tests/test_conftest_helpers.py` imports `git` from this module and
asserts on `git_repo`; it must stay green untouched.

- [ ] **Step 1a: Add the fixture to `tests/conftest.py`.** Append:

```python
_DIST_METADATA = """\
Metadata-Version: 2.1
Name: {name}
Version: {version}
"""


@pytest.fixture
def installed(tmp_path: Path, monkeypatch):
    """Write a real installed distribution and put it where `importlib.metadata` looks.

    A `<name>-<version>.dist-info/` holding `METADATA` and `entry_points.txt` is
    exactly what `uv` and `pip` write, and `importlib.metadata` finds a
    distribution by scanning each `sys.path` entry for one — so this exercises
    the real discovery path rather than a patch of `entry_points`. What it does
    not exercise is a build backend turning a `pyproject.toml` entry-points table
    into `entry_points.txt`; core reads no `pyproject.toml`, so that translation
    is outside anything a test here could pin.

    Each call gets its own directory. `importlib.metadata`'s path cache is keyed
    on a directory and its mtime, so adding a second `.dist-info` to a directory
    already scanned in the same test can be served from cache; two distributions
    therefore means two calls and two directories.

    A plain fixture rather than an autouse one, and requested by name:
    `monkeypatch.syspath_prepend` already restores `sys.path` per test, and the
    environ fixture above is the only autouse fixture this suite has.
    """
    made = 0

    def _install(dist_name: str, version: str, groups: dict[str, dict[str, str]]) -> Path:
        nonlocal made
        made += 1
        site = tmp_path / f"site{made}"
        info = site / f"{dist_name.replace('-', '_')}-{version}.dist-info"
        info.mkdir(parents=True)
        (info / "METADATA").write_text(_DIST_METADATA.format(name=dist_name, version=version))
        (info / "entry_points.txt").write_text(
            "".join(
                f"[{group}]\n" + "".join(f"{k} = {v}\n" for k, v in entries.items()) + "\n"
                for group, entries in groups.items()
            )
        )
        monkeypatch.syspath_prepend(str(site))
        importlib.invalidate_caches()
        return site

    return _install
```

      and add `import importlib` to the file's existing import block (`os`, `subprocess`,
      `pathlib.Path`, `pytest` today), keeping `ruff`'s `I` rule happy.

- [ ] **Step 1b: Write the failing tests.** Create `tests/test_plugins.py`:

```python
# tests/test_plugins.py
import pytest

from publishable.plugins import GROUPS, names, provider_of, scan_group


def test_the_groups_core_reads_are_the_five_the_document_declares():
    """Named rather than counted: `reference.md` § Creating a plugin shows one
    `[project.entry-points."publishable.*"]` block per registry."""
    assert set(GROUPS) == {
        "publishable.templates",
        "publishable.resolvers",
        "publishable.probes",
        "publishable.writers",
        "publishable.readers",
    }


def test_an_absent_group_is_empty_and_a_present_one_is_not(installed):
    """The control and its positive companion in one test: an empty answer proves
    nothing on a machine where no plugin is installed, so the same call must
    return something once a distribution declares it."""
    assert scan_group("publishable.resolvers") == {}
    installed("dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "pkg_one.r:resolve"}})
    found = scan_group("publishable.resolvers")
    assert list(found) == ["plate_wells"]
    assert found["plate_wells"][0].value == "pkg_one.r:resolve"


def test_a_scan_selects_its_own_group_only(installed):
    installed(
        "dist-one",
        "1.0",
        {
            "publishable.resolvers": {"plate_wells": "pkg_one.r:resolve"},
            "publishable.probes": {"assay_instrument": "pkg_one.p:probe"},
            "console_scripts": {"whatever": "pkg_one.cli:main"},
        },
    )
    assert list(scan_group("publishable.resolvers")) == ["plate_wells"]
    assert list(scan_group("publishable.probes")) == ["assay_instrument"]
    assert scan_group("publishable.writers") == {}


def test_two_distributions_claiming_one_name_both_arrive(installed):
    """The metadata scan reports every claimant; deciding between them is the
    collision check's job and not this function's. Two distributions, because one
    cannot produce this arrangement at all."""
    installed("dist-two", "2.0", {"publishable.resolvers": {"plate_wells": "pkg_two.r:resolve"}})
    installed("dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "pkg_one.r:resolve"}})
    providers = [provider_of(ep) for ep in scan_group("publishable.resolvers")["plate_wells"]]
    assert providers == ["dist-one 1.0", "dist-two 2.0"]


def test_names_are_sorted_and_the_sort_is_not_the_install_order(installed):
    """`zz_first` is installed first and sorts last; `aa_second` is installed
    second and sorts first. Two names in one arrangement cannot tell sorted order
    from insertion order — with two, the reverse of insertion IS sorted for one
    arrangement — so three names are declared and their install order is neither
    sorted nor reverse-sorted.
    """
    installed(
        "dist-order",
        "1.0",
        {
            "publishable.resolvers": {
                "zz_first": "pkg.r:a",
                "aa_second": "pkg.r:b",
                "mm_third": "pkg.r:c",
            }
        },
    )
    assert names("publishable.resolvers") == ["aa_second", "mm_third", "zz_first"]


def test_the_scan_imports_nothing(installed, monkeypatch):
    """The whole argument for entry points, asserted rather than described.

    The entry point points at a module that does not exist, so any `.load()` —
    core's or a caller's — raises `ModuleNotFoundError`. The scan returning
    normally is the proof, and the second half proves the fixture could have
    caught one: calling `.load()` on the very object the scan returned raises.
    """
    installed(
        "dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "no_such_module:resolve"}}
    )
    found = scan_group("publishable.resolvers")
    assert provider_of(found["plate_wells"][0]) == "dist-one 1.0"

    with pytest.raises(ModuleNotFoundError):
        found["plate_wells"][0].load()
```

- [ ] **Step 2: Run and see it fail.** `uv run pytest tests/test_plugins.py -q` →
      `ModuleNotFoundError: No module named 'publishable.plugins'`.

- [ ] **Step 3: Implement.** Create `src/publishable/plugins.py`:

```python
"""Entry-point discovery for the registries a plugin declares.

docs/reference.md § Creating a plugin. Every name a config can write for a
plugin artifact resolves through this module, and it resolves from **package
metadata**: nothing here calls `EntryPoint.load()`, and nothing that calls this
module may either. That is not a performance choice. § Creating a plugin
justifies the whole entry-point mechanism by `validate` being able to answer
"no installed package registers `plate_wells`" without importing a line of that
package, and `validate` is documented as creating nothing and reaching nothing
off the machine. A check that reaches for the object behind a name has changed
the guarantee whatever it returns.

The cost of that, stated rather than discovered: a claim read from metadata is a
name and a provider and nothing else. A refusal computed from it therefore has
no class to interrogate — no `parameter_spec`, no `required_env` — which is why
a plugin-side collision cannot redact a credential the way a project-local one
can. See `templates/registry.py` and § Creating a plugin for that residual.

Templates are scanned through here like everything else, but they are *merged*
in `templates/registry.py`, because a template name has a second home — a
project's own `templates/` — and the merge is the one place holding all three
sources at once.
"""

from importlib.metadata import EntryPoint, entry_points

GROUPS = (
    "publishable.templates",
    "publishable.resolvers",
    "publishable.probes",
    "publishable.writers",
    "publishable.readers",
)
"""Every entry-point group core reads, one per registry § Creating a plugin declares."""


def provider_of(ep: EntryPoint) -> str:
    """What a reader uninstalls or pins, which is a distribution rather than a module.

    Falls back to the entry point's own target only when `entry_points()` handed
    back an unattached object, which its own construction does not produce — kept
    so a message can never interpolate `None`.
    """
    dist = ep.dist
    if dist is None:  # pragma: no cover - entry_points() always attaches one
        return ep.value
    return f"{dist.name} {dist.version}"


def scan_group(group: str) -> dict[str, list[EntryPoint]]:
    """Every claim on every key in `group`, keyed by the key a config writes.

    A list per key rather than a single entry point, because two installed
    distributions claiming one key is a fault to *report* — naming both — rather
    than one to resolve by whichever the scan walked first. Keys come back in
    name order and claimants in provider order for the same reason: install order
    is a property of a machine, so it may not decide what a message says either.
    """
    found: dict[str, list[EntryPoint]] = {}
    for ep in entry_points(group=group):
        found.setdefault(ep.name, []).append(ep)
    return {name: sorted(found[name], key=provider_of) for name in sorted(found)}


def names(group: str) -> list[str]:
    """The keys `group` registers, in name order."""
    return list(scan_group(group))
```

- [ ] **Step 4: Run and see it pass.** `uv run pytest tests/test_plugins.py -q`, then the whole
      suite: **the count your predecessor left, plus 6.** `uv run mypy` must be clean — probed
      against this exact shape under `strict = true` over `files = ["src"]` and it is; `EntryPoint`
      and `EntryPoints` are typed in the stdlib, so **no `[[tool.mypy.overrides]]` is expected**. If
      one is reported anyway, add `module = "importlib.metadata"` with `ignore_missing_imports = true`
      and **say so in the task report** — the contingency is named here so it is not discovered.

- [ ] **Step 5: Retire task 4's marker, in this commit.** In § Package layout, delete
      `— not yet built` from the `plugins.py` line so it reads:

```
│   ├── plugins.py             # entry-point metadata scan; the resolver/probe/writer/reader registries
```

      Deferred from task 4 for the reason task 4 states: the marker means "specified and unbuilt",
      so retiring it is a build claim and belongs in the commit that makes it true.

- [ ] **Step 6: Mechanical pass** over the § Package layout edit: the tree line's alignment matches
      its neighbours, no trailing whitespace introduced.

- [ ] **Step 7: Mutate — three, each with the test that must go red, each checked against the test
      body.**

  **(a) Return in walk order instead of name order.** In `scan_group`, change the return to
  `{name: found[name] for name in found}`. `test_names_are_sorted_and_the_sort_is_not_the_install_order`
  must FAIL. **Checked against the test body:** its fixture declares three names whose declaration
  order (`zz_first`, `aa_second`, `mm_third`) is neither sorted nor reverse-sorted, so the mutant's
  output differs from the asserted list under either candidate reading. A two-name fixture would
  **not** discriminate — with two names the reverse of insertion order is sorted order for one
  arrangement — which is why the fixture has three.

  **(b) Keep one claimant per name.** Change the accumulation to `found[ep.name] = [ep]`.
  `test_two_distributions_claiming_one_name_both_arrive` must FAIL: it asserts a two-element list of
  providers, and the mutant yields one. **Checked against the test body:** the fixture installs two
  distributions in two directories, so both claims genuinely reach the scan; a one-distribution
  fixture could not tell this mutant from correct code.

  **(c) Sort claimants by something that is not the provider.** Change the inner sort key to
  `lambda ep: ep.value`. `test_two_distributions_claiming_one_name_both_arrive` must FAIL — its
  fixture's values are `pkg_two.r:resolve` and `pkg_one.r:resolve`, whose sort order is the reverse
  of the providers' (`dist-one 1.0` before `dist-two 2.0`). **Checked against the test body:** the
  fixture was written with the value order deliberately opposed to the provider order, which is what
  makes this mutation discriminate; had both agreed it would have been blind.

  After each: `find . -name __pycache__ -type d -exec rm -rf {} +`, edit the file back by hand,
  re-run, confirm green. **Never `git checkout --`.**

- [ ] **Step 8: Which deliverable no mutation reaches.** **`GROUPS`' membership is pinned only by a
      test asserting set equality against a literal**, so a group added to the tuple and to that
      test in one edit would pass — which is unavoidable for a constant and is why the test's
      docstring names § Creating a plugin as the authority rather than counting. **`provider_of`'s
      `dist is None` branch is unreachable** through `entry_points()` and is marked
      `# pragma: no cover`; nothing reaches it and nothing will. **The no-`.load()` guarantee is
      pinned by `test_the_scan_imports_nothing` only for `scan_group`** — a *caller* added later
      that loads is not caught here, and no test in this slice catches one. Tasks 8, 9, 11, 13, 14
      and 20 each restate the prohibition in their own text; that is the whole of the enforcement,
      and it is stated rather than claimed to be more.

- [ ] **Step 9: Verify and commit.** All four commands.
      `feat: the entry-point metadata scan, five groups, and no .load()`

---

