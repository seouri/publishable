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
from publishable.scaffold import read_scaffold

PYPROJECT = """\
[project]
name = "{name}"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["publishable"]

[dependency-groups]
dev = ["pytest"]

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
        """Cross-field rules over the whole config; `[]` when there is nothing to
        say. `config` is the parsed document, a plain mapping — not the
        dot-access `cfg` a step gets — so read an optional block as
        `(config.get("data") or {{}}).get("units") or {{}}`, which cannot raise
        on an absence."""
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
from importlib.metadata import entry_points

from publishable import Param

GROUP = "publishable.templates"
NAME = "{stem}"


def _registered():
    """The template this distribution registers, loaded through its own entry point.

    Asked through `importlib.metadata` rather than through core, and the reason
    is core's own rule: core resolves an installed name from package metadata
    WITHOUT importing the package, so there is no accessor on the `publishable`
    import root to ask — and reaching into a submodule for one would leave the
    single import root that document enumerates.

    It is also the question worth asking. A mistyped module path or class name in
    `pyproject.toml` breaks nothing until a config names this template, and then
    reads like a config typo rather than a packaging one.
    """
    found = [entry for entry in entry_points(group=GROUP) if entry.name == NAME]
    assert found, (
        f"no installed distribution registers `{{NAME}}` in `{{GROUP}}` — run these "
        "tests through `uv run pytest`, which installs this package first"
    )
    assert len(found) == 1, f"`{{NAME}}` is registered {{len(found)}} times: {{found}}"
    return found[0].load()


def test_the_entry_point_resolves_to_the_registered_template():
    assert _registered().__name__ == "{cls}"


def test_the_spec_declares_parameters_and_every_value_is_a_param():
    spec = _registered().parameter_spec
    assert spec, "a `parameter_spec` that is empty declares no parameters at all"
    assert all(isinstance(param, Param) for param in spec.values())
'''
"""The test `plugin new` ships, and it is written to survive being edited.

It asserts nothing about which parameters the spec declares, because the spec it
ships with is a placeholder whose own help text says to replace it — a test
enumerating those keys would go red on the first real edit, and a test that
fails on arrival gets deleted rather than fixed. What it asserts instead
survives every domain edit and still fails when the package is genuinely
broken: mistype the entry point's class name and both tests fail; delete
`parameter_spec` and the second fails alone.

What it replaces was `assert get_template(...) is not None or True`, which
**cannot fail** — and which reached `publishable.templates.registry` for a
`get_template` the import root does not export. The registry question it was
reaching for (does core resolve this name?) is `E-TEMPLATE-INSTALLED-UNSUPPORTED`
today; when loading an installed template lands, this file gains a case rather
than being replaced.

**What it does not cover, measured rather than assumed:** removing
`@register_template` entirely leaves both tests green, because loading an entry
point yields the class whether or not the decorator ran. That agreement is
`check_registration`'s (`E-PLUGIN-DECORATOR`), which runs wherever core loads the
object behind a key — for a resolver or a probe that is `validate` and `run`, and
for an installed template it is nowhere yet, which is the same refusal again.
"""

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
        tables.append(f'[project.entry-points."{group}"]\n"{key}" = "{dotted}:{attribute}"\n')

    (root / "pyproject.toml").write_text(
        PYPROJECT.format(name=name, entry_points="\n".join(tables))
    )
    (root / "README.md").write_text(README.format(name=name, stem=stem))
    (root / "CITATION.cff").write_text(read_scaffold("CITATION.cff.tmpl").format(name=name))
    (root / "LICENSE").write_text(
        read_scaffold("LICENSE.mit.tmpl") if license_name == "MIT" else f"{license_name}\n"
    )
    (root / ".gitignore").write_text(read_scaffold("gitignore.tmpl"))
    (root / "tests").mkdir(exist_ok=True)
    (root / "tests" / f"test_{stem}.py").write_text(TEST_PY.format(stem=stem, cls=cls))
    # `steps/` has no entry-point group — a reusable `BaseStep` is imported by the
    # consuming project's own code and registered nowhere — so there is nothing to
    # generate into it and the directory is the whole of what § Creating a plugin
    # names. Written beside its four siblings, with their `__init__.py`, because a
    # reader of any plugin relies on that layout being there.
    (package / "steps").mkdir(exist_ok=True)
    (package / "steps" / "__init__.py").write_text("")
    # A `.gitkeep`, because git tracks no empty directory: without it this folder
    # exists on the author's disk, is absent from the scaffold's own commit and
    # from every clone, and `git status` reports nothing in either direction.
    # `scaffold_project` writes one into each of its five directories for exactly
    # this reason.
    (root / "examples" / stem).mkdir(parents=True, exist_ok=True)
    (root / "examples" / stem / ".gitkeep").touch()
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
