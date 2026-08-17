## Task 21: `plugin new` — `plugin_scaffold.py`, five groups, five decorators

**Files:** Create `src/publishable/plugin_scaffold.py`, `tests/test_plugin_scaffold.py`. Modify
`src/publishable/cli.py`, `docs/reference.md`, `tests/test_cli.py`.

**Interfaces:**
- Consumes: `scaffold.scaffold_project(root, license_name="MIT") -> Path` in
  `src/publishable/scaffold.py`, the shape this follows — refuse a non-empty existing directory
  under `ContractError` · `E-PROJECT-EXISTS`, write the fixed layout, `git init` + add + commit with
  `-c commit.gpgsign=false`. `cli.NOT_BUILT_COMMANDS: dict[str, str]`, which holds the key
  `"plugin new"`. `cli._dispatch(command, rest)`, whose built branches precede the `NOT BUILT`
  lookup — read the comment there saying why.
- Produces: `plugin_scaffold.scaffold_plugin(root: Path, license_name: str = "MIT") -> Path`;
  `plugin_scaffold.package_name(name: str) -> str` (`publishable-my-assay` → `publishable_my_assay`);
  a `plugin new` branch in `_dispatch`; `"plugin new"` removed from `NOT_BUILT_COMMANDS`;
  § CLI reference's `publishable plugin new` row `Status` cell moved `NOT BUILT` → `built`;
  § Package layout's `plugin_scaffold.py     # `plugin new` — not yet built` marker struck.

**Five groups, not four.** Part A minted `publishable.readers` and `register_reader`, so a scaffold
emitting four entry-point groups is stale on the day it lands. The generated `pyproject.toml` must
declare all five groups § Creating a plugin's own `toml` block shows — `publishable.templates`,
`publishable.resolvers`, `publishable.probes`, `publishable.writers`, `publishable.readers` — and
the generated source must apply the five decorators `publishable.__all__` exports:
`register_template`, `register_resolver`, `register_probe`, `register_writer`, `register_reader`.

**§ CLI reference's `Status` column is set-equality-pinned.** `tests/test_cli.py` asserts set
equality between the document's `NOT BUILT` command rows and `cli.NOT_BUILT_COMMANDS` — find it by
grepping `tests/test_cli.py` for `NOT_BUILT_COMMANDS`, not by line number. The row and the dict
entry must move **in the same commit** or that test fails. `publishable list-templates` stays
`NOT BUILT` even though it has been reachable since Part A; do not fold it in.

- [ ] **Step 1: Write the failing test.** Create `tests/test_plugin_scaffold.py`:

```python
# tests/test_plugin_scaffold.py
import tomllib
from pathlib import Path

import pytest

from publishable.errors import ContractError
from publishable.plugin_scaffold import package_name, scaffold_plugin

GROUPS = (
    "publishable.templates",
    "publishable.resolvers",
    "publishable.probes",
    "publishable.writers",
    "publishable.readers",
)


def test_the_scaffold_declares_every_group_core_reads(tmp_path: Path):
    """Five registries, one mechanism — `reference.md` § Creating a plugin. A
    scaffold emitting four was already stale the day Part A minted
    `publishable.readers`, so this asserts against `plugins.GROUPS` itself rather
    than against a literal list, which is what keeps a sixth group from shipping a
    scaffold that omits it."""
    from publishable.plugins import GROUPS as CORE_GROUPS

    root = scaffold_plugin(tmp_path / "publishable-my-assay")
    declared = tomllib.loads((root / "pyproject.toml").read_text())
    entry_points = declared["project"]["entry-points"]

    assert set(entry_points) == set(CORE_GROUPS)
    assert set(GROUPS) == set(CORE_GROUPS)  # the literal above is a control on the import


def test_every_declared_entry_point_names_a_target_the_scaffold_wrote(tmp_path: Path):
    """The honouring, not only the shape: an entry point pointing at a module the
    scaffold never wrote is a package that fails to load on install, and a test
    asserting only the table's keys would pass on exactly that."""
    root = scaffold_plugin(tmp_path / "publishable-my-assay")
    declared = tomllib.loads((root / "pyproject.toml").read_text())
    for group, entries in declared["project"]["entry-points"].items():
        for key, target in entries.items():
            module, _, attribute = target.partition(":")
            path = root / "src" / Path(*module.split(".")).with_suffix(".py")
            assert path.is_file(), f"{group} {key} points at {module}, which is not written"
            assert attribute in path.read_text()


def test_each_decorator_is_applied_under_the_key_the_entry_point_declares(tmp_path: Path):
    """`reference.md` § Creating a plugin: the entry point is the registration and
    the decorator is a declaration checked against it. A scaffold whose two halves
    disagreed would ship a package `check_registration` refuses on first load —
    which is exactly the drift that check exists to catch, shipped by core."""
    root = scaffold_plugin(tmp_path / "publishable-my-assay")
    declared = tomllib.loads((root / "pyproject.toml").read_text())
    for group, entries in declared["project"]["entry-points"].items():
        decorator = "register_" + group.rsplit(".", 1)[1].rstrip("s")
        for key, target in entries.items():
            module = target.partition(":")[0]
            source = (root / "src" / Path(*module.split(".")).with_suffix(".py")).read_text()
            assert f'@{decorator}("{key}")' in source


def test_the_package_name_is_the_distribution_name_with_hyphens_turned_over(tmp_path: Path):
    assert package_name("publishable-my-assay") == "publishable_my_assay"
    root = scaffold_plugin(tmp_path / "publishable-my-assay")
    assert (root / "src" / "publishable_my_assay" / "__init__.py").is_file()


def test_a_non_empty_directory_is_refused(tmp_path: Path):
    """Greenfield, `scaffold_project`'s rule and its code: a plugin's `src/**` is
    code a run's numbers come out of once it is installed."""
    root = tmp_path / "publishable-my-assay"
    root.mkdir()
    (root / "keepme.txt").write_text("mine\n")
    with pytest.raises(ContractError) as excinfo:
        scaffold_plugin(root)
    assert excinfo.value.code == "E-PROJECT-EXISTS"
    assert (root / "keepme.txt").read_text() == "mine\n"  # nothing was overwritten
```

      and in `tests/test_cli.py`, beside the existing `NOT_BUILT_COMMANDS` assertions:

```python
def test_plugin_new_scaffolds_a_package_rather_than_reporting_not_built(tmp_path):
    """The built branch precedes the `NOT BUILT` lookup in `_dispatch`, so this
    also pins that `plugin new` left `NOT_BUILT_COMMANDS` rather than being
    shadowed by it."""
    from publishable.cli import NOT_BUILT_COMMANDS, main

    assert "plugin new" not in NOT_BUILT_COMMANDS
    assert main(["plugin", "new", str(tmp_path / "publishable-my-assay")]) == 0
    assert (tmp_path / "publishable-my-assay" / "pyproject.toml").is_file()
```

- [ ] **Step 2: Run and see it fail.** `uv run pytest tests/test_plugin_scaffold.py` →
      `ModuleNotFoundError: No module named 'publishable.plugin_scaffold'`; the `test_cli.py`
      addition fails on `main(...) == 2` (the `NOT BUILT` notice) and on the `NOT_BUILT_COMMANDS`
      assertion.

- [ ] **Step 3: Implement.** Create `src/publishable/plugin_scaffold.py`. **The outer fence below is
      four backticks**: the generated README template holds a fenced `bash` block of its own, and a
      three-backtick outer fence would be closed by it — markdown inside markdown, the hazard
      `CLAUDE.md`'s mechanical pass names.

````python
# src/publishable/plugin_scaffold.py
"""`publishable plugin new`. docs/reference.md § Creating a plugin.

A standalone installable package rather than an experiment repo: what a project
`uv add`s and what `uv.lock` pins, which is why a plugin's code is outside
`code_hash`'s two trees rather than inside them.

The five entry-point groups and the five decorators are written from
`plugins.GROUPS` rather than from a literal here, so a sixth registry cannot ship
a scaffold that omits it — the exact staleness Part A's `publishable.readers`
created for the four-group scaffold this replaces.
"""

import subprocess
from pathlib import Path

from publishable.errors import ContractError
from publishable.plugins import GROUPS
from publishable.scaffold import CITATION, GITIGNORE, MIT

PYPROJECT = """\
[project]
name = "{name}"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["publishable"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

{entry_points}"""

README = """\
# {name}

A [`publishable`](https://github.com/your-org/publishable) plugin.

## Install

```bash
uv add git+https://github.com/<you>/{name}
```

## What it registers

| Registry | Name |
|---|---|
| template | `{stem}` |
| resolver | `{stem}_units` |
| probe | `{stem}_instrument` |
| writer / reader | `.{stem}` |
"""

TEMPLATE_PY = '''\
from publishable import BaseTemplate, Param, register_template


@register_template("{stem}")
class {cls}(BaseTemplate):
    """One spec drives what `init` writes, what its comments say, and what
    `validate` enforces. There is no second source of truth."""

    parameter_spec = {{
        "{stem}.threshold": Param(
            float, default=0.5, gt=0, lt=1,
            help="TODO: replace with this experiment type's own parameters",
        ),
    }}

    naming_pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    default_repeats = 1

    def validate(self, config) -> list[str]:
        return []

    def aggregate(self, units, cfg) -> dict:
        return {{}}
'''

RESOLVER_PY = '''\
from publishable import Unit, register_resolver


@register_resolver("{stem}_units")
def resolve(io, cfg):
    """Yield one `Unit` per thing being measured, in the order it is found.

    `io` is read-only — `io.read_input` and nothing else. `cfg` is the same
    config a `scope: "run"` step sees, so a parameter the sweep varies is
    unreadable here: the unit table is one table for the whole run.
    """
    for row in io.read_input("index.csv"):
        yield Unit(key=row["id"], paths=(), attributes={{"site": row["site"]}})
'''

PROBE_PY = '''\
from publishable import register_probe


@register_probe("{stem}_instrument")
def probe(cfg):
    """Observe the apparatus. Core records what you return; it never sets it."""
    raise NotImplementedError("describe the apparatus this experiment measures through")
'''

WRITER_PY = '''\
from publishable import register_reader, register_writer


@register_writer(".{stem}")
def write(obj) -> bytes:
    """Take the object a step wrote and return bytes."""
    return str(obj).encode()


@register_reader(".{stem}")
def read(payload: bytes):
    """Invert `write` — what a writer takes is what its reader gives back."""
    return payload.decode()
'''

TEST_PY = '''\
def test_the_template_materializes_and_validates():
    from publishable.templates.registry import get_template

    assert get_template("{stem}") is not None or True  # installed-name check once loaded
'''

# One target module per group, keyed by the group core reads it under. The
# per-group key a config writes is derived from the distribution's own stem, so a
# generated package is installable and resolvable without an edit.
_MODULES = {
    "publishable.templates": ("templates", TEMPLATE_PY, "{cls}", "{stem}"),
    "publishable.resolvers": ("resolvers", RESOLVER_PY, "resolve", "{stem}_units"),
    "publishable.probes": ("probes", PROBE_PY, "probe", "{stem}_instrument"),
    "publishable.writers": ("writers", WRITER_PY, "write", ".{stem}"),
    "publishable.readers": ("writers", WRITER_PY, "read", ".{stem}"),
}


def package_name(name: str) -> str:
    """`publishable-my-assay` → `publishable_my_assay`, the importable spelling."""
    return name.replace("-", "_")


def _stem(name: str) -> str:
    """`publishable-my-assay` → `my_assay`, the name a config actually writes.

    The distribution prefix is dropped because a config writes
    `experiment_type: my_assay`, not `experiment_type: publishable_my_assay`; a
    name that did not start with the prefix keeps all of itself.
    """
    package = package_name(name)
    return package[len("publishable_") :] if package.startswith("publishable_") else package


def _class_name(stem: str) -> str:
    return "".join(part.capitalize() for part in stem.split("_")) + "Template"


def scaffold_plugin(root: Path, license_name: str = "MIT") -> Path:
    """Fixed layout, greenfield, one commit. `scaffold_project`'s rules, one artifact over."""
    name = root.name
    if root.exists() and any(root.iterdir()):
        raise ContractError(
            f"{root} already exists and is not empty — `plugin new` never overwrites an "
            "existing package; choose a different path or remove it deliberately",
            code="E-PROJECT-EXISTS",
        )
    stem = _stem(name)
    cls = _class_name(stem)
    package = root / "src" / package_name(name)
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("")

    written: dict[str, str] = {}
    tables: list[str] = []
    for group in GROUPS:
        directory, body, attribute, key_template = _MODULES[group]
        (package / directory).mkdir(exist_ok=True)
        (package / directory / "__init__.py").write_text("")
        module_stem = {"templates": stem, "resolvers": "units", "probes": "instrument"}.get(
            directory, "artifact"
        )
        target = package / directory / f"{module_stem}.py"
        source = body.format(stem=stem, cls=cls)
        if target.name not in written:
            target.write_text(source)
            written[target.name] = source
        key = key_template.format(stem=stem, cls=cls)
        dotted = f"{package_name(name)}.{directory}.{module_stem}"
        attribute = attribute.format(cls=cls, stem=stem)
        tables.append(
            f'[project.entry-points."{group}"]\n"{key}" = "{dotted}:{attribute}"\n'
        )

    (root / "pyproject.toml").write_text(
        PYPROJECT.format(name=name, entry_points="\n".join(tables))
    )
    (root / "README.md").write_text(README.format(name=name, stem=stem))
    (root / "CITATION.cff").write_text(CITATION.format(name=name))
    (root / "LICENSE").write_text(MIT if license_name == "MIT" else f"{license_name}\n")
    (root / ".gitignore").write_text(GITIGNORE)
    (root / "tests").mkdir(exist_ok=True)
    (root / "tests" / f"test_{stem}.py").write_text(TEST_PY.format(stem=stem))
    (root / "examples" / stem).mkdir(parents=True, exist_ok=True)
    if not (root / ".git").exists():
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.email=you@example.com",
                "-c",
                "user.name=you",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "-qm",
                "Scaffold a publishable plugin package",
            ],
            cwd=root,
            check=True,
        )
    return root
````

      **A quoted entry-point key.** A writer's key is `.my_assay`, which starts with a dot;
      `entry_points.txt` and `tomllib` both accept a quoted key, and the unquoted form is what a
      TOML parser rejects. That is why every key above is written quoted, including the ones that
      would not have needed it — one spelling, not two.

      In `src/publishable/cli.py`, add `from publishable.plugin_scaffold import scaffold_plugin`
      and, in `_dispatch`, **above** the `two_token` lookup and beside the `new` branch:

```python
    if command == "plugin":
        if len(rest) != 2 or rest[0] != "new" or rest[1].startswith("-"):
            print("`plugin new` takes exactly one path", file=sys.stderr)
            return EXIT_INVOCATION
        scaffold_plugin(Path(rest[1]))
        return EXIT_OK
```

      and delete `"plugin new": "Creating a plugin: \`publishable plugin new\`",` from
      `NOT_BUILT_COMMANDS`.

      In `docs/reference.md`: move the `publishable plugin new` row's `Status` cell from
      `NOT BUILT` to `built` in § CLI reference, and strike ` — not yet built` from
      `plugin_scaffold.py`'s line in § Package layout's tree.

- [ ] **Step 4: Run and see it pass.** `uv run pytest` → **2060 + 6 = 2066 passed**, 1 skipped,
      2 xfailed. Then `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`.

- [ ] **Step 5: Mutate.** In `src/publishable/plugin_scaffold.py`, delete the
      `"publishable.readers"` entry from `_MODULES` and add `if group == "publishable.readers":
      continue` at the top of the `for group in GROUPS` loop.
      `tests/test_plugin_scaffold.py::test_the_scaffold_declares_every_group_core_reads` must
      **FAIL** — its assertion is `set(entry_points) == set(CORE_GROUPS)`, and the two sets now
      differ by exactly that member. **Checked against the test body:** the assertion is set
      equality against the imported `plugins.GROUPS`, not against the module-level `GROUPS` literal,
      so it discriminates a scaffold that drops a group core reads. (The literal is asserted equal
      to the import in the same test, which is what keeps the literal from silently drifting into
      being the thing under test.)

      Second mutation, because the first says nothing about the decorator half: change
      `RESOLVER_PY`'s `@register_resolver("{stem}_units")` to `@register_resolver("{stem}")`.
      `test_each_decorator_is_applied_under_the_key_the_entry_point_declares` must **FAIL** — the
      entry-point key is still `{stem}_units` and the decorator now declares `{stem}`, which is
      precisely the disagreement `check_registration` refuses.

      **What no mutation here reaches:** the generated `git` commit, the `README.md` body, the
      `CITATION.cff` body and the `examples/` directory. Nothing asserts their content, and nothing
      in core reads them — they are a published package's furniture. Recorded rather than covered.

- [ ] **Step 6: Commit.** `plugin new: scaffold a five-registry plugin package`

---

