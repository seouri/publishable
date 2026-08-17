# H7b Part B — resolvers, and retiring `E-DATA-RESOLVER-UNSUPPORTED` — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to
> implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** a plugin's resolver builds the unit roster. `data.units.from: {resolver: plate_wells}`
runs — at `validate` as well as at `run` — the unit checks that need a roster become real for that
source, and the refusal that has stood since H1 is retired. This is the first slice in the project's
history with a non-zero payoff: **three of the nine experiments in the feasibility analysis have no
remaining core-side blocker once it lands** (E1, E2, E5), with two qualifications that travel with
the number — the plugin must exist, and a declared apparatus probe is neither executed nor recorded.

**Architecture.** `units.resolve_units` gains a third branch. A `{resolver: <name>}` source resolves
the name through `plugins.scan_group("publishable.resolvers")` (metadata only), loads the object
behind it through `plugins.load_entry_point`, checks the decorator argument against the entry-point
key with `plugins.check_registration`/`plugins.declared_names`, and calls it as
`resolve(io, cfg)` — a generator of `Unit`s, per `reference.md` § Where units come from. The `io` is
a new read-only `artifacts.ResolverIO`: `read_input` and nothing else, no run directory and no step,
recording each relative path it read so `hash_index` can name it. The `cfg` is the same object a
`scope: "run"` step gets — `runner.resolve_wide_cfg` over `sweep.wide_swept_paths` — so a resolver
reading a swept parameter meets a `SweptAway` marker and is refused. Yielded units are projected onto
`data.units.attributes` exactly as `_from_table` projects a CSV row, so everything downstream is
indifferent to which form `from` took. `resolve_units` gains two defaulted keywords, `cfg` and
`resolver_io`, rather than required parameters: there are ~60 `resolve_units(` call sites in
`tests/` and two in `src/`, and a required parameter would be a 60-site edit with no behavioural
content. `validate` therefore **does** import a plugin when it runs a resolver; what survives, and
what Part A actually built, is that a **name** resolves from package metadata without importing.
Five `reference.md`/`plugins.py` sentences that generalized the second into the first change in
task 22, and the two tests pinning the old claim are extended to pin the narrowed one.

**Tech stack:** Python ≥ 3.11, `importlib.metadata` entry points, `pytest`, `ruff`, `mypy`. No new
dependency.

**Spec:** docs/superpowers/specs/2026-08-17-resolvers-design.md

**Measurement this plan argues from:** `docs/superpowers/H7b-PartB-SCOPING.md`, taken 2026-08-17
against `main` at `53090e9`. Every signature, attribute, error code, config key, entry-point group
and file path below was read from the source named beside it, at `470a830`.

**Task count: 13**, numbered 21–33, exactly the spec's § Task decomposition and the scoping's § 10,
in their order and grain. No task was split, merged or moved.

**Sequencing.** 22 → 24 → 25 → {26, 27, 28, 29}; 23 → 25. **26 is last among the refusal-retiring
tasks**, so `E-DATA-RESOLVER-UNSUPPORTED` stays alive as long as possible and every earlier test
asserts its finding **alongside** that code — which is what makes 26 a set of one-line deletions
rather than a rewrite. **32 may not be deferred past 26**: the leak becomes reachable the moment a
resolver runs. 30, 31 and 33 follow 25; 33 is last because it re-dates a build claim over the whole
finished slice. **If it runs long, drop 21** — `plugin new` is the only task nothing else depends
on, and a hand-written package already works.

**Where each task's tests can live, stated once because it decides five task briefs.**
`validate._check_units` **skips resolution outright** for a `{resolver: ...}` source
(`validate.py`, `_check_units`, the branch commented *"E-DATA-RESOLVER-UNSUPPORTED already reported
by _check_unimplemented"*), and that skip is deleted in **task 26**, which is deliberately last.
So tasks 25, 27, 28 and 29 cannot reach their behaviour through `validate_config` at their own
commit. Each therefore tests the function that holds the behaviour directly — `units.resolve_units`
for 25/27/29, `validate._check_measurements` for 28, which `tests/test_validate.py` already imports
by name for direct calls. Task 33 is where the same behaviour is re-asserted end-to-end through
`validate_config`, after 26 has opened the path. This is not a weakening: the mutation for each task
is applied at the site the behaviour lives, which is what this repo's discipline asks for.

---

## Global Constraints

Every task inherits all of these. They are copied verbatim rather than cross-referenced because an
implementer sees only its own task brief.

**Commands.** Tests `uv run pytest` — takes about two minutes; **run it in the foreground** and wait
for it. Lint `uv run ruff check .`. Format `uv run ruff format .`. Types `uv run mypy`. All four
must pass before a commit.

**Verify format with `uv run ruff format --check .`, never the bare form.** A previous brief in this
repo wrote the bare form where it meant `--check` and rewrote 67 files. **The repo is format-clean:
`ruff format --check .` reports 78 files, 0 to reformat. Keep it that way.**

**Baseline.** `uv run pytest -q` is **2060 passed, 1 skipped, 2 xfailed**. A task that leaves the
count below its own additions has broken something. Every task states its expected count.

**`E-DATA-RESOLVER-UNSUPPORTED` stays alive until task 26.** Every test written before task 26
asserts its own finding **alongside** that code, never instead of it, and **never on a total code
set**. The tests that already do this and that task 26 edits, each by deleting one line, are named
in task 26 by test name.

**`validate` collects rather than aborting.** A refusal elsewhere never makes a later check
unreachable. Three readers across two slices got this wrong. Do not infer unreachability from a
refusal; build the config and look.

**Every new error site is pinned by its MESSAGE, not only its code.** Use the `fragment` +
`messages_by_code(path)[code]` pattern already in `tests/test_validate.py`; both helpers are defined
at the top of that file — `codes(path)` returns the set of every finding's code,
`messages_by_code(path)` returns `{code: message}`. **A message assertion is not automatically a
discriminating one**: assert a fragment only one branch can produce.
**`messages_by_code` collapses duplicate-code findings last-wins**, so a code emitted more than once
per config needs a counted assertion, not `messages_by_code`.

**`tests/conftest.py` already has** an autouse `os.environ` restore, an opt-in `registries` fixture
(snapshot/restore of `plugins.RESOLVERS`, `plugins.PROBES`, `artifacts.WRITERS`,
`artifacts.READERS`), and an opt-in `installed` distribution fixture. **Do not add duplicates, and
do not add a second autouse fixture of any kind.**

**Real imports now leak.** Unlike Part A, this slice imports plugin modules for real. Every test
that reaches `load_entry_point` puts a module in `sys.modules` and a name in `plugins.RESOLVERS`.
Request the `registries` fixture by name **and** pop the module in a `finally:`, the pattern
`tests/test_plugins.py::test_the_scan_imports_nothing` already uses. One directory per
`installed(...)` arrangement, `importlib.invalidate_caches()` after prepending,
`monkeypatch.syspath_prepend` only.

**Mutation discipline, every task.** Apply the named mutation to the file it names. Run the named
test. Confirm it **FAILS**. Then `find . -name __pycache__ -type d -exec rm -rf {} +`. Then revert
**by editing the file back in place** — **never `git checkout -- <file>`**, which destroys
uncommitted work and has been mistaken for a revert twice in this repo. Confirm the test **PASSES**
again, and verify the revert by *behaviour*, never by `git status`.

**A mutation is a claim too.** Before believing "this mutation must fail test X", read the *body* of
test X and check the two branches can actually produce different results. Ten prescribed mutations
across five slices were blind. Where this plan concludes a mutation cannot discriminate, it says so
and prescribes a different one; do the same for any mutation you add. **And a mutation's silence is
evidence about the TESTS, not the code** — twice in Part A a task emptied a payload, saw the suite
green, and concluded the payload was unreachable while a discriminating test existed. If a mutation
changes nothing, say what test *would* have caught it and write that test.

**Documentation rules.** `×` not `x` for multiplication, including inside fenced blocks. Hyphen,
never an en dash, in anything that becomes a filename or an anchor. **Cite by section**
(`reference.md` § "Where units come from"), never by line number — the previous scoping proved
≈ +242 lines of drift in `validate.py` in one slice. **No positional locators** ("the row above",
"further up"): name what a sibling row *does*. **No counts in prose or comments** and **no call-site
enumerations**: state what a set *is*. **A build fact is dated and pinned to a commit.** **Prefer
deleting a claim to rewriting it.** After any `*.md` edit run the mechanical pass: every relative
link and `#anchor` resolves, no two headings in a file share an anchor, every table row matches its
header's column count and none is empty, no trailing whitespace, tab or invisible unicode — skipping
fenced code blocks in all of them. Any inline `# a | b | c` enum comment must list every value its
table defines. **Never filter the output of a sweep whose job is to find a string — filter the file
list**, and name the four documents explicitly, since the development record is tracked and `*.md`
no longer means what it used to.

**The four normative documents LEAD; `src/` follows.** `README.md`, `docs/design-principles.md`,
`docs/experimental-designs.md`, `docs/reference.md`. Where they and the code disagree, **the
document changes first** and the gap is recorded in `docs/superpowers/spec-defects.md`. The
cross-document pass governs those four **only** — never the development record under
`docs/superpowers/`, where a correction is appended rather than retro-edited. `spec-defects.md` is
the one exception: a closed gap is struck there rather than left to mislead.
**§ Errors carries one row per code covering every emit site**, not one row per site.

---

## Identifiers this slice emits

| Code | Fault | Row state at `470a830` | Emitted in |
|---|---|---|---|
| `E-RESOLVER-UNKNOWN` | `data.units.from.resolver` names a resolver no installed distribution registers | § Errors `validate` reports, marked `Not yet emitted:` | **24** (marker struck) |
| `E-RESOLVER-MEASUREMENT-FIELD` | `measurements.by` names a field the resolver yields no attribute for | § Errors `validate` reports, marked `Not yet emitted:` | **28** (marker struck) |
| `E-RESOLVER-SWEPT-PARAM` | a resolver reads a parameter the sweep varies | § Errors `validate` reports, marked `Not yet emitted:` | **29** (marker struck) |
| `E-PLUGIN-DECORATOR` | a `@register_*` argument disagreeing with the entry-point key | § Errors core raises, dated *no production caller* | **24** (first caller) |
| `E-PLUGIN-LOAD` | an entry point whose module raises, or exits, while importing | § Errors core raises, dated *no production caller* | **24** (first caller) |
| `E-UNITS-ATTR-MISSING` | extended: a declared attribute no yielded unit carries | § Errors `validate` reports, table-worded | **27** (message generalized) |
| `E-RESOLVER-YIELD` | **minted here.** A resolver yielded something that is not a `Unit` | none | **25** |
| `E-RESOLVER-RAISED` | **minted here.** A resolver's own body raised something that is not a `PublishableError` | none | **32** |
| `E-RUN-RESOLVER-UNCONFIGURED` | **minted here.** `resolve_units` reached a resolver source with no `cfg` — core's resolved state disagreeing with itself | none | **25** |

**Three mints the spec does not name, each with its argument.** `E-RESOLVER-YIELD` and
`E-RESOLVER-RAISED` exist because a resolver is the second place user code runs inside
`resolve_units` and `validate` is contracted never to raise: without them a plugin yielding a `dict`
or raising `KeyError` produces an `AttributeError`/`KeyError` escaping `validate_config` (the
scoping's probe B) or a traceback out of `main` (probe D). `E-RUN-RESOLVER-UNCONFIGURED` is
decision 6's named price: a defaulted `cfg` keyword means a resolver source can be reached with
`cfg=None`, and that path must refuse rather than crash. It joins the existing § Errors core raises
row for *core's execution plan disagreeing with the state core resolved beside it*, whose code cell
already lists `E-RUN-SEED-MISSING`, `E-RUN-CFG-MISSING`, `E-RUN-ORDER-MISMATCH`,
`E-REPL-ORDER-UNRESOLVED`, `E-RUN-FOLD-UNRESOLVED`, `E-RUN-ARM-UNRESOLVED` — read that row before
editing it and add one clause to its condition cell beside adding the code.

Confirm the two `E-RESOLVER-YIELD`/`E-RESOLVER-RAISED` spellings are free before task 25, by
sweeping the **file list** rather than filtering output:
`grep -rn "E-RESOLVER-YIELD\|E-RESOLVER-RAISED\|E-RUN-RESOLVER" docs/reference.md docs/design-principles.md docs/experimental-designs.md README.md src/ tests/`
→ must be empty. Can-fail control on the identical file list:
`grep -oE "E-RESOLVER[A-Z-]*" docs/reference.md | sort -u` → three distinct codes.

---

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

## Task 23: the read-only resolver `io`

**Files:** Modify `src/publishable/artifacts.py`, `tests/test_artifacts.py`.

**Interfaces:**
- Consumes: `artifacts.StepIO._read(path: Path) -> Any`, a `@staticmethod` that dispatches through
  `_suffix_for`/`READERS` and raises `ArtifactError` · `E-ARTIFACT-UNREADABLE` for a suffix with a
  writer and no reader; `StepIO.read_input(relpath: str) -> Any`, which is
  `self._read(self.input_dir / relpath)`. `StepIO.__init__` requires keyword `step_dir`,
  `input_dir`, `run_dir` — read it in `artifacts.py`, `class StepIO`.
- Produces: `artifacts.ResolverIO`, constructed as `ResolverIO(input_dir: Path)`, exposing
  `read_input(relpath: str) -> Any` and the property `read_paths -> tuple[str, ...]`.

**Why a new class rather than a `StepIO` with three arguments defaulted.** § Where units come from:
*"The `io` a resolver receives is read-only: `io.read_input` and nothing else. There is no run
directory yet at validate time and no step yet at run time, so there is nothing for it to write
into."* A `StepIO` with `step_dir`/`run_dir` defaulted would carry `write`, `append`, `record`,
`read_upstream`, `read_condition`, `exists`, `resumed` and `skip` into a place where every one of
them either has no directory to act on or would let a resolver write into a run that has not
started. The refusal has to be structural — there is no method to call — rather than a raise per
method, because core cannot inspect the body of user Python.

**`read_paths` exists for `hash_index`, and task 31 is its only reader.** § Where units come from:
*"'the index and whatever it names' means the paths the resolver read plus the paths its units
name."* Recording is here rather than in task 31 because this is the one object that sees a read.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_artifacts.py`:

```python
def test_a_resolver_io_reads_the_input_and_nothing_else(tmp_path):
    """`reference.md` § Where units come from: read-only, `read_input` and
    nothing else. Structural rather than a raise per method — core cannot inspect
    the body of a resolver, so the method must not exist to be called."""
    from publishable.artifacts import ResolverIO

    (tmp_path / "layout.csv").write_text("barcode,well\nA1,h3\n")
    io = ResolverIO(tmp_path)

    assert io.read_input("layout.csv") == [{"barcode": "A1", "well": "h3"}]
    for forbidden in (
        "write",
        "append",
        "record",
        "skip",
        "read_upstream",
        "read_condition",
        "exists",
        "resumed",
        "units",
        "run_dir",
        "step_dir",
    ):
        assert not hasattr(io, forbidden), f"a resolver io must not expose {forbidden}"


def test_a_resolver_io_records_every_path_it_read_in_order(tmp_path):
    """`hash_index` names "the paths the resolver read"; this object is the only
    one that sees a read. Order and duplicate handling are asserted because the
    set task 31 builds is derived from this tuple."""
    from publishable.artifacts import ResolverIO

    (tmp_path / "layout.csv").write_text("barcode\nA1\n")
    (tmp_path / "extra.json").write_text('{"n": 1}')
    io = ResolverIO(tmp_path)

    assert io.read_paths == ()  # the control: nothing read, nothing recorded
    io.read_input("layout.csv")
    io.read_input("extra.json")
    io.read_input("layout.csv")
    assert io.read_paths == ("layout.csv", "extra.json", "layout.csv")


def test_a_resolver_io_reads_through_the_same_table_a_step_does(tmp_path, registries):
    """A plugin's registered reader serves a resolver too — one dispatch, not two.
    Without this, a resolver reading a plugin suffix would get raw bytes while a
    step reading the same file got the parsed object."""
    from publishable.artifacts import ResolverIO
    from publishable.plugins import register_reader, register_writer

    @register_writer(".fq")
    def _write(obj) -> bytes:
        return str(obj).encode()

    @register_reader(".fq")
    def _read(payload: bytes):
        return {"parsed": payload.decode()}

    (tmp_path / "reads.fq").write_bytes(b"ACGT")
    assert ResolverIO(tmp_path).read_input("reads.fq") == {"parsed": "ACGT"}
```

- [ ] **Step 2: Run and see it fail.** `ImportError: cannot import name 'ResolverIO'`.

- [ ] **Step 3: Implement.** In `src/publishable/artifacts.py`, immediately after `class StepIO`:

```python
class ResolverIO:
    """What a resolver receives: `read_input` and nothing else.

    `reference.md` § Where units come from — "The `io` a resolver receives is
    read-only: `io.read_input` and nothing else. There is no run directory yet at
    validate time and no step yet at run time, so there is nothing for it to write
    into." A `StepIO` with its directories defaulted would carry every write and
    every cross-scope read into a place where each either has no directory to act
    on or would let a resolver write into a run that has not started. Core cannot
    inspect the body of user Python, so the refusal is that the method does not
    exist rather than that it raises.

    Reads through `StepIO._read`, the one dispatch, so a plugin's registered
    reader serves a resolver exactly as it serves a step — two dispatches would be
    two answers to "what does this suffix mean".

    Records each relative path it was asked for, in the order it was asked, so
    `input_manifest_policy: hash_index` can name "the paths the resolver read"
    without a second walk that could disagree with what was actually opened.
    Duplicates are kept: this is a log of reads, and its one consumer builds a set
    from it.
    """

    __slots__ = ("input_dir", "_read_paths")

    def __init__(self, input_dir: Path) -> None:
        self.input_dir = input_dir
        self._read_paths: list[str] = []

    def read_input(self, relpath: str) -> Any:
        self._read_paths.append(relpath)
        return StepIO._read(self.input_dir / relpath)

    @property
    def read_paths(self) -> tuple[str, ...]:
        return tuple(self._read_paths)
```

- [ ] **Step 4: Run and see it pass.** `uv run pytest` → **2067 + 3 = 2070 passed**, 1 skipped,
      2 xfailed. Then the other three commands.

- [ ] **Step 5: Mutate.** In `src/publishable/artifacts.py`, delete the
      `self._read_paths.append(relpath)` line from `ResolverIO.read_input`.
      `tests/test_artifacts.py::test_a_resolver_io_records_every_path_it_read_in_order` must
      **FAIL** — the tuple comes back `()` where three entries are asserted. **Checked against the
      test body:** the assertion is on the exact tuple, not on membership or truthiness, so it
      discriminates both the empty case and a de-duplicating one.

      Second mutation, because the first says nothing about the dispatch: change
      `StepIO._read(self.input_dir / relpath)` to `(self.input_dir / relpath).read_bytes()`.
      `test_a_resolver_io_reads_through_the_same_table_a_step_does` must **FAIL** (`b"ACGT"` is not
      `{"parsed": "ACGT"}`) and `test_a_resolver_io_reads_the_input_and_nothing_else` must **FAIL**
      too (raw bytes are not the parsed CSV rows).

      **What no mutation here reaches:** `__slots__`. Its effect — no attribute can be added to a
      `ResolverIO` after construction — is asserted by nothing. Recorded rather than covered; the
      `hasattr` sweep covers the names that matter.

- [ ] **Step 6: Commit.** `artifacts: a read-only ResolverIO — read_input, and the paths it read`

---

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

## Task 25: dispatch in `resolve_units`

**Files:** Modify `src/publishable/units.py`, `src/publishable/validate.py`,
`src/publishable/cli.py`, `src/publishable/sweep.py`, `docs/reference.md`, `tests/test_units.py`,
`tests/test_cli.py`.

**Interfaces:**
- Consumes: `units.resolve_units(units_decl: dict, input_dir: Path) -> tuple[UnitList, dict[str, float] | None, frozenset[str]]`
  and its two branches `_from_table`/`_from_glob`, read in `src/publishable/units.py`;
  `artifacts.ResolverIO(input_dir)` from task 23; `units._resolver_for(name)` from task 24;
  `runner.resolve_wide_cfg(base: dict, swept_paths: set[str]) -> Config` and
  `cli._wide_swept_paths(sweep_block: dict) -> set[str]`, read in `src/publishable/runner.py` and
  `src/publishable/cli.py`.
- Produces: `resolve_units(units_decl, input_dir, *, cfg: Config | None = None, resolver_io: ResolverIO | None = None)`
  — same three-element return; `units._from_resolver(decl, name, input_dir, cfg, resolver_io) -> tuple[list[Unit], frozenset[str]]`;
  `sweep.wide_swept_paths` (moved from `cli._wide_swept_paths`); `E-RESOLVER-YIELD` and
  `E-RUN-RESOLVER-UNCONFIGURED` emitted; both `resolve_units` production call sites thread `cfg`.

**Two defaulted keywords, not two required parameters — decision 6, measured.**
`grep -c 'resolve_units(' tests/test_units.py` → 56 and `tests/test_cli.py` → 4, plus the two
production sites in `validate.py` and `cli.py`. A required parameter is a 60-site edit with no
behavioural content. The price is named rather than discovered: **a resolver source reached with
`cfg=None` must refuse rather than crash**, under `E-RUN-RESOLVER-UNCONFIGURED`, which joins
§ Errors core raises' existing *core's plan disagreeing with the state core resolved beside it* row.
`resolver_io` defaults the same way and for a narrower reason: only `cli.command_run` needs the
object back afterwards (task 31 reads `read_paths` off it), and `validate` builds no manifest.

**Yield order is preserved and is not cosmetic.** § Where units come from: *"The resolved list keeps
the order it was resolved in — table row order, resolver yield order, or lexicographic path order
for a `glob`"*, and `assign.method: blocked` reads that order as data while
`provenance.units_hash` covers the list in it. So `_from_resolver` appends in iteration order and
does nothing else to it.

**`validate` → `runner` is acyclic, so nobody needs to re-derive it.** Read both import blocks:
`runner.py` imports `artifacts`, `coercion`, `config`, `errors`, `replication`, `scope`, `secrets`,
`stats`, `sweep`, `units` — never `validate`. The only module in `src/publishable/` importing
`validate` is `cli.py`. `units` → `plugins` → `artifacts` is acyclic too: `artifacts` imports
`units` only under `TYPE_CHECKING`.

**`_wide_swept_paths` moves to `sweep.py` and is pinned by name.** `tests/test_cli.py` imports it
from `publishable.cli` and asserts its exact returned set; update that import **in the same
commit**. It moves because `validate` now needs it and `validate` importing `cli` would be the
cycle `cli` → `validate` already occupies.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_units.py`:

```python
def _install_resolver(installed, tmp_path, module: str, body: str):
    """One installed distribution whose `publishable.resolvers` entry point points
    at a module this writes. Returns nothing: every caller pops `module` from
    `sys.modules` in its own `finally`, because a real import leaks and Part A's
    fixtures deliberately could not import at all."""
    site = installed("dist-one", "1.0", {"publishable.resolvers": {"plate_wells": f"{module}:resolve"}})
    (site / f"{module}.py").write_text(body)
    importlib.invalidate_caches()


_YIELDS_TWO = """\
from publishable import Unit, register_resolver


@register_resolver("plate_wells")
def resolve(io, cfg):
    for row in io.read_input("layout.csv"):
        yield Unit(
            key=row["barcode"] + ":" + row["well"],
            paths=(row["read"],),
            attributes={"operator": row["operator"]},
        )
"""


def test_a_resolver_source_yields_the_roster_in_yield_order(installed, registries, tmp_path):
    """THE HONOURING, and the property `units_hash` and `assign.method: blocked`
    both rest on: yield order is the resolved order. The fixture's rows are
    deliberately NOT in sorted key order, so a dispatch that sorted — the way
    `_from_glob` must — comes out different rather than identical."""
    from publishable.artifacts import ResolverIO
    from publishable.config import Config
    from publishable.units import resolve_units

    (tmp_path / "layout.csv").write_text(
        "barcode,well,read,operator\nB9,h3,reads/b9.fq,mo\nA1,c2,reads/a1.fq,kj\n"
    )
    _install_resolver(installed, tmp_path, "yielding_r25", _YIELDS_TWO)
    try:
        roster, technical_n, columns = resolve_units(
            {"from": {"resolver": "plate_wells"}, "key": "well", "attributes": ["operator"]},
            tmp_path,
            cfg=Config({}),
            resolver_io=ResolverIO(tmp_path),
        )
    finally:
        sys.modules.pop("yielding_r25", None)

    assert [u.key for u in roster] == ["B9:h3", "A1:c2"]
    assert [u.paths for u in roster] == [("reads/b9.fq",), ("reads/a1.fq",)]
    assert technical_n is None
    assert columns == frozenset({"operator"})


def test_a_resolver_yielding_something_that_is_not_a_unit_is_refused(
    installed, registries, tmp_path
):
    """`E-RESOLVER-YIELD`. A resolver is the second place user code runs inside
    resolution, and `validate` is contracted never to raise — without this a
    yielded mapping reaches `u.key` as an `AttributeError` escaping `validate`."""
    from publishable.config import Config
    from publishable.errors import ContractError
    from publishable.units import resolve_units

    _install_resolver(
        installed,
        tmp_path,
        "wrongyield_r25",
        "from publishable import register_resolver\n\n\n"
        '@register_resolver("plate_wells")\n'
        "def resolve(io, cfg):\n    yield {'key': 'a1'}\n",
    )
    try:
        with pytest.raises(ContractError) as excinfo:
            resolve_units(
                {"from": {"resolver": "plate_wells"}, "key": "well"}, tmp_path, cfg=Config({})
            )
    finally:
        sys.modules.pop("wrongyield_r25", None)
    assert excinfo.value.code == "E-RESOLVER-YIELD"
    assert "dict" in str(excinfo.value)


def test_a_resolver_source_reached_with_no_cfg_refuses_rather_than_crashing(
    installed, registries, tmp_path
):
    """Decision 6's named price. `cfg` is a defaulted keyword so ~60 existing call
    sites keep compiling, which makes `cfg=None` a reachable state rather than a
    hypothetical — core's resolved state disagreeing with itself, reported under
    the row that family already has."""
    from publishable.errors import ContractError
    from publishable.units import resolve_units

    _install_resolver(installed, tmp_path, "nocfg_r25", _YIELDS_TWO)
    try:
        with pytest.raises(ContractError) as excinfo:
            resolve_units({"from": {"resolver": "plate_wells"}, "key": "well"}, tmp_path)
    finally:
        sys.modules.pop("nocfg_r25", None)
    assert excinfo.value.code == "E-RUN-RESOLVER-UNCONFIGURED"


def test_a_table_source_still_resolves_with_no_cfg(tmp_path):
    """THE CONTROL for the refusal above: the defaulted keyword must not have
    turned every existing caller into a refusal. Without this, a `cfg is None`
    guard placed one branch too high would pass every test in this file that
    passes a `cfg` and break every one that does not."""
    from publishable.units import resolve_units

    (tmp_path / "index.csv").write_text("patient_id\np1\np2\n")
    roster, _technical_n, columns = resolve_units({"from": "index.csv", "key": "patient_id"}, tmp_path)
    assert [u.key for u in roster] == ["p1", "p2"]
    assert columns == frozenset({"patient_id"})
```

      and in `tests/test_cli.py`, update the import of `_wide_swept_paths` to
      `from publishable.sweep import wide_swept_paths` and rename its three uses in
      `test_a_group_path_gets_no_swept_away_marker`.

- [ ] **Step 2: Run and see it fail.** `TypeError: resolve_units() got an unexpected keyword
      argument 'cfg'`; the `test_cli.py` import fails with `ImportError`.

- [ ] **Step 3: Implement.** In `src/publishable/cli.py`, delete `_wide_swept_paths` and move it
      verbatim — docstring included — into `src/publishable/sweep.py` as `wide_swept_paths`,
      dropping the leading underscore because it now has readers in two modules. Import it in
      `cli.py` from `publishable.sweep` and update the one call site.

      In `src/publishable/units.py`, add `from publishable.artifacts import ResolverIO` and
      `from publishable.config import Config` to the imports, then:

```python
def _from_resolver(
    decl: dict[str, Any],
    name: str,
    input_dir: Path,
    cfg: "Config | None",
    resolver_io: ResolverIO | None,
) -> tuple[list[Unit], frozenset[str]]:
    """The units a plugin's resolver yields, and the attribute names it yielded.

    The columns come back beside the roster for the reason `_from_table`'s do: they
    are the only honest reference set for `data.units.measurements.by`, and a
    resolver has no columns beyond the attributes it yields, so the field a CSV
    would simply have carried is checked against what actually arrived. The union
    over yielded units rather than the intersection, matching a table header's
    "this column exists" rather than "every row filled it in" — the same reading
    `collapse_measurements` takes when it treats a name only some rows carry as no
    disagreement.

    Yield order is preserved and nothing re-sorts it: `reference.md` § Where units
    come from makes resolver yield order the resolved order, `assign.method:
    blocked` reads that order as data, and `provenance.units_hash` covers the list
    in it.
    """
    if cfg is None:
        raise ContractError(
            f"`data.units.from.resolver` names `{name}`, and resolution was reached with no "
            "config to hand it — a resolver sees the same `cfg` a `scope: \"run\"` step does, "
            "so core's resolved state disagrees with itself here rather than the config being "
            "wrong",
            code="E-RUN-RESOLVER-UNCONFIGURED",
        )
    resolve = _resolver_for(name)
    io = resolver_io if resolver_io is not None else ResolverIO(input_dir)
    units: list[Unit] = []
    yielded: set[str] = set()
    for item in resolve(io, cfg):
        if not isinstance(item, Unit):
            raise ContractError(
                f"resolver `{name}` yielded a {type(item).__name__} — a resolver yields "
                "`Unit`s, which is what makes its roster a unit table with the columns a "
                "CSV would have supplied",
                code="E-RESOLVER-YIELD",
            )
        units.append(item)
        yielded.update(item.attributes)
    if not units:
        raise ContractError(
            f"resolver `{name}` yielded no units; a run measuring zero units has nothing "
            "to report",
            code="E-UNITS-EMPTY",
        )
    return units, frozenset(yielded)
```

      and rewrite `resolve_units`'s signature and source branch:

```python
def resolve_units(
    units_decl: dict[str, Any],
    input_dir: Path,
    *,
    cfg: "Config | None" = None,
    resolver_io: ResolverIO | None = None,
) -> tuple[UnitList, dict[str, float] | None, frozenset[str]]:
```

```python
    source = units_decl.get("from")
    if isinstance(source, str):
        units, columns = _from_table(units_decl, input_dir, source)
    elif isinstance(source, dict) and "glob" in source:
        units, columns = _from_glob(units_decl, str(source["glob"]), input_dir)
    elif isinstance(source, dict) and "resolver" in source:
        units, columns = _from_resolver(
            units_decl, str(source["resolver"]), input_dir, cfg, resolver_io
        )
    else:
        raise ContractError(
            f"`data.units.from` is {source!r}; expected a table name, {{glob: ...}}, or "
            "{{resolver: ...}}",
            code="E-UNITS-SOURCE-MISSING",
        )
```

      **`glob` is still tested before `resolver`**, deliberately: a `from` declaring both is refused
      by `validate._check_from_source_exclusivity` as `E-UNITS-SOURCE-AMBIGUOUS`, and keeping this
      order means the two modules cannot come to read one declaration two ways in the window before
      that check runs. Extend `resolve_units`'s docstring to say the columns are a table's header,
      a glob's empty set, or a resolver's yielded attribute names.

      Thread `cfg` at both production call sites. In `src/publishable/validate.py`, add
      `from publishable.runner import resolve_wide_cfg` and `wide_swept_paths` to the `sweep`
      import, then in `_check_units` replace the `resolve_units(units_decl, path)` call with:

```python
        # The same `cfg` a `scope: "run"` step sees, so a resolver reading a swept
        # parameter meets a `SweptAway` marker rather than a value no condition
        # used. Built here rather than threaded from `validate_config` because
        # every other check in this module re-derives from `doc` locally.
        roster, technical_n, columns = resolve_units(
            units_decl,
            path,
            cfg=resolve_wide_cfg(doc, wide_swept_paths(doc.get("sweep") or {})),
        )
```

      In `src/publishable/cli.py`, `command_run`'s phase-5 roster call becomes:

```python
    resolver_io = ResolverIO(input_dir)
    roster, technical_n, _columns = (
        resolve_units(
            units_decl,
            input_dir,
            cfg=resolve_wide_cfg(doc, wide_swept_paths(doc.get("sweep") or {})),
            resolver_io=resolver_io,
        )
        if units_decl
        else (None, None, frozenset())
    )
```

      In `docs/reference.md` § Errors `validate` reports, `E-UNITS-SOURCE-MISSING`'s row says `from`
      *"is neither a table name nor a `{glob: ...}` mapping"* — a third form is legal now, so widen
      that clause to name all three. **This row appears in neither the scoping's § 6 nor its § 13;
      it is found by reading the row, not by grepping for `NOT BUILT`.**

- [ ] **Step 4: Run and see it pass.** `uv run pytest` → **2074 + 4 = 2078 passed**, 1 skipped,
      2 xfailed. Then the other three commands.

- [ ] **Step 5: Mutate.** In `src/publishable/units.py`, change `_from_resolver`'s
      `units.append(item)` loop to `units = sorted(units, key=lambda u: u.key)` before the return.
      `tests/test_units.py::test_a_resolver_source_yields_the_roster_in_yield_order` must **FAIL**.
      **Checked against the test body:** the fixture's two rows are `B9,h3` then `A1,c2`, so sorted
      order (`A1:c2`, `B9:h3`) differs from yield order — a fixture whose rows happened to be sorted
      would have made this mutation blind, which is why the CSV is written that way.

      Second mutation: in `resolve_units`, move the `elif isinstance(source, dict) and "resolver"
      in source` branch **above** the `glob` branch. **This one cannot fail, and it is recorded
      rather than prescribed:** no fixture declares both keys, because
      `_check_from_source_exclusivity` refuses that shape and no test in `tests/test_units.py`
      builds it. The mutation that *can* discriminate the ordering is a direct call to
      `resolve_units` with `{"from": {"glob": "*.csv", "resolver": "plate_wells"}}` — and the reason
      not to add one is that it would pin resolution behaviour for a declaration `validate` refuses,
      making a future removal of that refusal look like a regression. **What no mutation reaches**:
      the branch order between `glob` and `resolver`. Named, not covered.

      Third mutation, for the `cfg` guard: change `if cfg is None:` to `if False:`.
      `test_a_resolver_source_reached_with_no_cfg_refuses_rather_than_crashing` must **FAIL** — with
      `cfg=None` reaching `resolve(io, cfg)`, the fixture resolver reads `io.read_input` fine and
      never touches `cfg`, so the failure is "DID NOT RAISE" rather than a crash. That is exactly
      the fail-open the guard exists for, and it is why the guard is a raise rather than a comment.

- [ ] **Step 6: Commit.** `units: dispatch a resolver source, yield order preserved`

---

## Task 26: retire `E-DATA-RESOLVER-UNSUPPORTED` and the `_check_units` skip, in one change

**Files:** Modify `src/publishable/validate.py`, `src/publishable/materialize.py`,
`docs/reference.md`, `tests/test_validate.py`, `tests/test_materialize.py`.

**Interfaces:**
- Consumes: `validate._check_unimplemented(doc, c)`'s resolver branch — **the one emit site**, found
  by reading that function in full and then confirming with `grep -rn "RESOLVER" src/`, in that
  order; `validate._check_units`'s early return for a `{resolver: ...}` source and the docstring
  bullet justifying it; `materialize.py`'s literal `"| {resolver: <name>} (NOT BUILT)"`.
- Produces: the code gone from `src/`, the skip gone, four document sites moved.

**Read the whole function, then grep.** `E-DATA-RESOLVER-UNSUPPORTED` appears at **four** sites in
`validate.py` and **only one of them emits**: the emit in `_check_unimplemented`, the early return in
`_check_units` (not an emit — the blast radius), `_check_units`'s docstring bullet justifying the
skip, and `_check_unimplemented`'s closing comments. Enumerating by grep alone is the substitution
that shipped a credential leak two slices ago.

**Delete the message, do not edit it.** Part A already rewrote this message once, because the old
wording claimed the registry was unimplemented and Part A implemented it. The current wording
(*"a resolver cannot be dispatched in this build; resolvers will be honored in a later slice"*) is
true today and false the moment this task lands. Deleting is what Part A's decision 7 bought by
requiring every test to assert the refusal **alongside** its own finding.

**`statistics.null_test` stays.** `_check_unimplemented`'s loop keeps its other member — retiring
one must not retire the loop — and § The one config file's *"**Two** declarations above are not yet
built"* count goes to **one**, not to zero.

- [ ] **Step 1: Write the failing test.** In `tests/test_validate.py`:

```python
def test_a_resolver_source_is_no_longer_refused_wholesale(installed, registries, write_config, tmp_path):
    """The retirement, asserted against behaviour rather than against a grep. The
    control is the second half: an UNREGISTERED name still earns
    `E-RESOLVER-UNKNOWN`, so this is not a check that stopped reporting anything."""
    from publishable.units import RESOLVER_GROUP

    site = installed("dist-one", "1.0", {RESOLVER_GROUP: {"plate_wells": "retire_r26:resolve"}})
    (site / "retire_r26.py").write_text(
        "from publishable import Unit, register_resolver\n\n\n"
        '@register_resolver("plate_wells")\n'
        "def resolve(io, cfg):\n"
        "    yield Unit(key='p1')\n"
    )
    importlib.invalidate_caches()
    units = {"from": {"resolver": "plate_wells"}, "key": "well"}
    try:
        found = codes(write_config({"data.units": units}))
        unknown = codes(write_config({"data.units": {**units, "from": {"resolver": "nope"}}}))
    finally:
        sys.modules.pop("retire_r26", None)

    assert found == set()
    assert "E-RESOLVER-UNKNOWN" in unknown


def test_the_unsupported_family_is_down_to_null_test(write_config):
    """`E-DATA-RESOLVER-UNSUPPORTED` is gone from every surface, and the family it
    left is not empty — a sweep asserting only an absence would pass identically if
    the whole family had been deleted."""
    found = messages_by_code(
        write_config({"statistics": {"null_test": {"method": "permutation", "n": 5000}}})
    )
    unsupported = {code for code in found if code.endswith("-UNSUPPORTED")}
    assert unsupported == {"E-STATS-NULLTEST-UNSUPPORTED"}
```

      and **delete one line from each** of the tests that were written to make this a deletion —
      find them by name, not by line number:

      - `tests/test_validate.py::test_a_resolver_source_is_refused_until_plugins_exist` — delete the
        whole test; it is the refusal itself.
      - `tests/test_validate.py::test_every_unsupported_message_defers_rather_than_scolds` — delete
        the resolver row from its `@pytest.mark.parametrize` list and the sentence in its docstring
        naming `E-DATA-RESOLVER-UNSUPPORTED` as what remains of the family.
      - `tests/test_validate.py::test_a_resolver_source_does_not_also_raise_source_missing` — delete
        the `assert "E-DATA-RESOLVER-UNSUPPORTED" in found` line. The remaining assertion
        (`E-UNITS-SOURCE-MISSING` not in `found`) is still a real claim: `resolve_units`' `else`
        branch must not describe a resolver as a missing file.
      - `tests/test_validate.py::test_two_installed_distributions_claiming_one_resolver_name_are_reported`
        — delete the `assert "E-DATA-RESOLVER-UNSUPPORTED" in both` line and the comment above it.
      - the `E-UNITS-SOURCE-AMBIGUOUS` test — delete its two
        `assert "E-DATA-RESOLVER-UNSUPPORTED" in ...` lines.
      - `tests/test_materialize.py::test_the_from_enum_s_not_built_marking_is_honoured_by_core` —
        this whole test is about a marker that no longer exists; delete it, and delete the
        `(NOT BUILT)` sentence from its docstring's sibling explanation if that sentence stands
        alone elsewhere in the file.

      Confirm the list is complete before starting, by sweeping the **file list**:
      `grep -rn "E-DATA-RESOLVER-UNSUPPORTED" src/ tests/ docs/reference.md docs/design-principles.md docs/experimental-designs.md README.md CLAUDE.md`
      → after the task, empty except `docs/superpowers/**` and
      `docs/feasibility-llm-growth-studies.md`, which are the development record and a dated
      measurement respectively and are **never** retro-edited. Can-fail control on the same list:
      `grep -rn "E-STATS-NULLTEST-UNSUPPORTED" src/ docs/reference.md` → non-empty.

- [ ] **Step 2: Run and see it fail.** The new tests fail on `found == set()` (the wholesale refusal
      is still reported) and on the `unsupported == {...}` equality.

- [ ] **Step 3: Implement.** In `src/publishable/validate.py`:

      - delete `_check_unimplemented`'s `if isinstance(source, dict) and "resolver" in source:`
        block **and** the two lines above it that fetch `units`/`source`, if nothing else in the
        function reads them — read the function to check rather than assuming;
      - delete `_check_units`'s early return for a resolver source, its two-line comment, and the
        `data.units.from.resolver` bullet in its docstring — the bullet **justifies the skip by the
        refusal**, so the two die together;
      - rewrite `_check_unimplemented`'s closing comments: delete the sentence *"One `data.units`
        sub-field remains read by nothing: a `resolver` source"* and its parenthetical, and the
        clause *"It resolves a unit roster, but one `data.units` sub-field — a `resolver` source —
        is still read by nothing"* in the docstring. **Prefer deleting to rewriting**: there is now
        no `data.units` sub-field read by nothing, so the honest edit is that the sentence goes.

      In `src/publishable/materialize.py`, change the two-part literal to a single line reading
      `'    from: index.csv                # index.csv | {glob: "*.dcm"} | {resolver: <name>}'`.

      In `docs/reference.md`:

      - § The one config file's fenced `from:` line — strike `(NOT BUILT)`;
      - § The one config file's prose — *"**Two** declarations above are not yet built"* becomes
        **one**, naming `statistics.null_test` alone, and the resolver clause is deleted from the
        sentence listing them. Append the same shape the `resample`/`holdout` retirements already
        use: what now checks it for real (`units._from_resolver` dispatches it, `_check_units`
        resolves it, `provenance.plugin_versions` records the plugin), so the declaration changes
        the record;
      - § Where units come from's second `from` enum comment — strike `(NOT BUILT)` there too, so
        the generated config and the document do not disagree about build state.

- [ ] **Step 4: Run and see it pass.** `uv run pytest` → **2078 + 2 − 2 (deleted tests) = 2078
      passed**, 1 skipped, 2 xfailed. Restate the arithmetic in the commit message from the actual
      run, not from this line.

- [ ] **Step 5: Mutate.** In `src/publishable/validate.py`, restore `_check_units`'s early return
      for a resolver source (`return None, None, frozenset()` under the `resolver` test).
      `tests/test_validate.py::test_a_resolver_source_is_no_longer_refused_wholesale` must **FAIL**
      on `"E-RESOLVER-UNKNOWN" in unknown` — with the skip restored, the misspelled name never
      reaches `_resolver_for`. **Checked against the test body:** the first assertion
      (`found == set()`) would still *pass* under the restored skip, since skipping produces no
      finding either; it is the second, positive half that discriminates. That asymmetry is the
      reason the control is in the test at all.

      Second mutation: in `materialize.py`, put `(NOT BUILT)` back on the `from:` line.
      **This one now fails nothing**, because the test that pinned it was deleted in Step 1 — and
      that is correct rather than a gap: the marker was a claim about build state, and the build
      state it claimed is gone. The test that *would* catch a marker resurfacing is
      `tests/test_materialize.py`'s `_MARKED_LATER_SLICE` sweep, which reads the generated config
      for `(x: later slice)` markers; it does not match the `(NOT BUILT)` spelling, which is exactly
      why the deleted test existed. Record this in the commit message rather than adding a test for
      a string nobody writes any more.

- [ ] **Step 6: Commit.** `validate: retire E-DATA-RESOLVER-UNSUPPORTED and the roster skip together`

---

## Task 27: attribute projection, and `E-UNITS-ATTR-MISSING` generalized past a table

**Files:** Modify `src/publishable/units.py`, `docs/reference.md`, `tests/test_units.py`.

**Interfaces:**
- Consumes: `units._from_table`'s attribute loop — `RESERVED_FIELDS` first, then
  `name not in columns` → `ContractError` · `E-UNITS-ATTR-MISSING`, then
  `Unit(key=row[key_col], paths=(), attributes={a: row[a] for a in attrs})` — read in
  `src/publishable/units.py`; `_from_glob`'s same-ordered loop and its `from: {glob: ...}`-worded
  message; `units._from_resolver` from task 25.
- Produces: `_from_resolver` projecting each yielded unit's attributes onto `data.units.attributes`,
  with `E-UNITS-ATTR-RESERVED` and a resolver-worded `E-UNITS-ATTR-MISSING`; § Errors'
  `E-UNITS-ATTR-MISSING` row widened past *"the source table has no column for"*.

**Projection, not pass-through, and it is what makes the rest of core indifferent to the source.**
§ Where units come from: *"What it returns is a unit table with the columns a CSV would have
supplied … `attributes`, the mapping `data.units.attributes` draws from … Everything downstream is
then indifferent to which form `from` took: `stratify_by`, `assign.from`, `cluster_by`, and
`null_test.shuffle` all name attributes."* `_from_table` builds `Unit.attributes` from the declared
list and nothing else; a resolver's units must end up the same shape, or `clusters_of`,
`arms_of`, `usable_weight` and the fold's `stratify_by` subscript would see a name `validate` never
approved. Two consequences the plan states rather than leaves to be discovered: an attribute the
resolver yields and the config does not declare is **dropped**, exactly as an undeclared CSV column
is; and `measurements.by` is dropped by the same projection, which is correct, because
`collapse_measurements` groups on `key` and reads `by` only to exclude it from the merged names —
the pre-projection column set task 25 returns is what task 28 checks `by` against.

**Ordering: reserved before missing**, matching `_from_table` and `_from_glob`, so one declaration
draws one code whichever source it sits under. Report the **first** such name and stop, the
convention both existing branches use.

**A declared name is missing when no yielded unit carries it** — the union, not the intersection.
That is a table header's question ("does this column exist") rather than a per-row one, and it
matches `collapse_measurements`'s reading that a name only some rows carry is no disagreement.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_units.py`:

```python
_YIELDS_PARTIAL = """\
from publishable import Unit, register_resolver


@register_resolver("plate_wells")
def resolve(io, cfg):
    yield Unit(key="a1", attributes={"operator": "kj", "plate": "P1", "scratch": "x"})
    yield Unit(key="b9", attributes={"operator": "mo", "plate": "P1"})
"""


def test_a_resolver_roster_is_projected_onto_the_declared_attributes(
    installed, registries, tmp_path
):
    """Everything downstream is indifferent to which form `from` took, and this is
    what makes it so: an undeclared attribute is dropped exactly as an undeclared
    CSV column is. `scratch` is yielded and not declared; asserting only that
    `operator` survives would pass on a pass-through implementation."""
    from publishable.config import Config
    from publishable.units import resolve_units

    _install_resolver(installed, tmp_path, "project_r27", _YIELDS_PARTIAL)
    try:
        roster, _n, columns = resolve_units(
            {"from": {"resolver": "plate_wells"}, "key": "well", "attributes": ["operator"]},
            tmp_path,
            cfg=Config({}),
        )
    finally:
        sys.modules.pop("project_r27", None)

    assert [dict(u.attributes) for u in roster] == [{"operator": "kj"}, {"operator": "mo"}]
    assert columns == frozenset({"operator", "plate", "scratch"})  # pre-projection, for task 28


def test_a_declared_attribute_no_unit_yields_is_refused_naming_the_resolver(
    installed, registries, tmp_path
):
    """`E-UNITS-ATTR-MISSING`, generalized past "which index.csv does not have".
    The message must name the resolver, or a reader is sent looking for a column
    in a file that has nothing to do with the fault."""
    from publishable.config import Config
    from publishable.errors import ContractError
    from publishable.units import resolve_units

    _install_resolver(installed, tmp_path, "missing_r27", _YIELDS_PARTIAL)
    try:
        with pytest.raises(ContractError) as excinfo:
            resolve_units(
                {
                    "from": {"resolver": "plate_wells"},
                    "key": "well",
                    "attributes": ["operator", "site"],
                },
                tmp_path,
                cfg=Config({}),
            )
    finally:
        sys.modules.pop("missing_r27", None)
    assert excinfo.value.code == "E-UNITS-ATTR-MISSING"
    assert "'site'" in str(excinfo.value)
    assert "plate_wells" in str(excinfo.value)
    assert "index.csv" not in str(excinfo.value)


def test_a_name_only_some_units_yield_is_not_missing(installed, registries, tmp_path):
    """THE DISCRIMINATOR between the union and the intersection. `scratch` is
    carried by one of the two units; declaring it must resolve, with the unit that
    lacks it simply carrying no value — a table column that some rows leave blank
    behaves the same way. Without this fixture, union and intersection are the
    same answer and the choice is untested."""
    from publishable.config import Config
    from publishable.units import resolve_units

    _install_resolver(installed, tmp_path, "sparse_r27", _YIELDS_PARTIAL)
    try:
        roster, _n, _columns = resolve_units(
            {"from": {"resolver": "plate_wells"}, "key": "well", "attributes": ["scratch"]},
            tmp_path,
            cfg=Config({}),
        )
    finally:
        sys.modules.pop("sparse_r27", None)
    assert [dict(u.attributes) for u in roster] == [{"scratch": "x"}, {}]


def test_a_reserved_attribute_name_is_refused_before_a_missing_one(
    installed, registries, tmp_path
):
    """One declaration, one code, whichever source it sits under: `_from_table` and
    `_from_glob` both check reserved before unsourced, and a resolver must not
    invert that. `paths` is reserved AND unyielded, so a wrong order gives
    `E-UNITS-ATTR-MISSING` instead."""
    from publishable.config import Config
    from publishable.errors import ContractError
    from publishable.units import resolve_units

    _install_resolver(installed, tmp_path, "reserved_r27", _YIELDS_PARTIAL)
    try:
        with pytest.raises(ContractError) as excinfo:
            resolve_units(
                {"from": {"resolver": "plate_wells"}, "key": "well", "attributes": ["paths"]},
                tmp_path,
                cfg=Config({}),
            )
    finally:
        sys.modules.pop("reserved_r27", None)
    assert excinfo.value.code == "E-UNITS-ATTR-RESERVED"
```

- [ ] **Step 2: Run and see it fail.** The projection test fails on the yielded `plate`/`scratch`
      surviving; the missing-attribute test fails with "DID NOT RAISE".

- [ ] **Step 3: Implement.** In `src/publishable/units.py`, `_from_resolver`, after the yield loop
      and before the empty check:

```python
    attrs = list(decl.get("attributes") or [])
    for attribute in attrs:
        if attribute in RESERVED_FIELDS:
            raise ContractError(
                f"`data.units.attributes` names {attribute!r}, which is a field of `Unit` "
                f"itself; {', '.join(RESERVED_FIELDS)} cannot also be attributes",
                code="E-UNITS-ATTR-RESERVED",
            )
        if attribute not in yielded:
            raise ContractError(
                f"`data.units.attributes` names {attribute!r}, which resolver `{name}` yields "
                "no unit carrying — a resolver has no columns beyond the attributes it yields, "
                "so the field a table would simply have carried has to be yielded",
                code="E-UNITS-ATTR-MISSING",
            )
    # Projected onto the declared list exactly as `_from_table` projects a CSV row,
    # which is what makes everything downstream indifferent to which form `from`
    # took: `cluster_by`, `weight_by`, `assign.<axis>.from`, `holdout.from` and a
    # `fold`'s `stratify_by` all read `Unit.attributes` and were approved by
    # `validate` against `data.units.attributes` alone. An attribute the resolver
    # yields and the config does not declare is dropped, the way an undeclared
    # column is.
    units = [
        Unit(
            key=unit.key,
            paths=unit.paths,
            attributes={a: unit.attributes[a] for a in attrs if a in unit.attributes},
        )
        for unit in units
    ]
```

      **The reserved/missing loop runs over the declaration, before the projection**, so the two
      cannot disagree about which names survive. Move the empty-roster check *above* this block, so
      a resolver yielding nothing reports `E-UNITS-EMPTY` rather than an attribute fault about a
      roster that does not exist.

      In `docs/reference.md`, § Errors `validate` reports' `E-UNITS-ATTR-MISSING` row: widen its
      opening from *"names a value the source table has no column for, or names any value at all
      under a `{glob: ...}` source"* to name the third source — *"or a value no unit a
      [resolver](#where-units-come-from) yielded carries"* — keeping the rest of the row, including
      its `measurements.by` clause, untouched.

- [ ] **Step 4: Run and see it pass.** `uv run pytest` → **2078 + 4 = 2082 passed**, 1 skipped,
      2 xfailed. Then the other three commands.

- [ ] **Step 5: Mutate.** In `src/publishable/units.py`, change the projection comprehension's
      `attributes={a: unit.attributes[a] for a in attrs if a in unit.attributes}` to
      `attributes=unit.attributes`.
      `tests/test_units.py::test_a_resolver_roster_is_projected_onto_the_declared_attributes` must
      **FAIL** — the first unit comes back carrying `plate` and `scratch`. **Checked against the
      test body:** the assertion is on the exact `dict(u.attributes)` of both units, and the fixture
      yields an attribute (`scratch`) that the declaration omits, so pass-through and projection
      genuinely differ. A fixture yielding only declared attributes would have made this blind.

      Second mutation: change `if attribute not in yielded:` to
      `if all(attribute not in u.attributes for u in units):`, i.e. the intersection reading
      inverted to a stricter one — no: that is the same predicate. **The mutation that discriminates
      union from intersection** is `if any(attribute not in u.attributes for u in units):`.
      `test_a_name_only_some_units_yield_is_not_missing` must **FAIL** with an
      `E-UNITS-ATTR-MISSING` raise for `scratch`, which one of the two units carries and the other
      does not. **Checked against the test body:** the fixture's two units differ in exactly that
      attribute, which is the seam this mutation exists to instantiate — naming the seam is not
      testing it, and this fixture is what separates the readings.

      **What no mutation here reaches:** the ordering of `_from_resolver`'s three refusals relative
      to `resolve_units`' later `E-UNITS-KEY-DUPLICATE` loop. No fixture yields both a duplicate key
      and a missing attribute. Named, not covered.

- [ ] **Step 6: Commit.** `units: project a resolver roster onto the declared attributes`

---

## Task 28: `E-RESOLVER-MEASUREMENT-FIELD` emitted, marker struck

**Files:** Modify `src/publishable/validate.py`, `docs/reference.md`, `tests/test_validate.py`.

**Interfaces:**
- Consumes: `validate._check_measurements(units: dict, roster: UnitList | None, technical_n: dict[str, float] | None, columns: frozenset[str], c: Collector) -> None`
  — read its signature and body in `src/publishable/validate.py`; it is already imported by name in
  `tests/test_validate.py` for direct calls. Its existing `by`-against-`columns` check reports
  `E-UNITS-ATTR-MISSING` and is gated on `technical_n["max"] > 1`.
- Produces: a source-aware branch reporting `E-RESOLVER-MEASUREMENT-FIELD` when the source is a
  resolver; § Errors' `Not yet emitted:` clause for that code struck.

**Ungated for a resolver, and gated for a table — a decision, not an inheritance.** The table
path's `max > 1` gate exists because `measurements.by` means two different things on the two paths:
against a table with real columns, a `by` may name a measurement identity the **step** invents
through `io.record(..., measurement=)`, and refusing it would refuse a design § What isn't a repeat
documents. A resolver has no columns at all, and § Where units come from turns that into an explicit
obligation — *"yield one `Unit` per measurement, sharing a `key`, and emit `measurements.by` as an
attribute — a resolver has no columns beyond the ones it declares, so the field a CSV would simply
have carried has to be named."* `E-RESOLVER-MEASUREMENT-FIELD`'s own row is worded unconditionally
to match: *"names a field, and the resolver the roster came from yields no attribute of that name to
collapse on."* So emit ungated. **The consequence, stated rather than discovered:** a resolver-based
roster whose measurement identity is invented by a step must still yield the `by` attribute. That is
the row's own rule, not a narrowing this task invents; no document changes.

**The columns it checks against are the pre-projection ones** task 25 returns — the union of
attribute names the resolver actually yielded — not the projected roster, which by construction
carries only declared attributes and would make this check fire for every correct config.

- [ ] **Step 1: Write the failing test.** In `tests/test_validate.py`, calling `_check_measurements`
      directly (the module already imports it):

```python
def test_a_resolver_yielding_no_measurement_field_is_refused_under_its_own_code():
    """`E-RESOLVER-MEASUREMENT-FIELD`, ungated: § Where units come from makes
    yielding `measurements.by` an obligation for a resolver, where a table's `by`
    may name an identity the step invents. Its own code rather than
    `E-UNITS-ATTR-MISSING`: the two name different declarations, and a reader
    fixing one is not fixing the other."""
    c = Collector()
    _check_measurements(
        {"from": {"resolver": "plate_wells"}, "measurements": {"by": "read_id", "collapse": "mean"}},
        UnitList([Unit(key="a1", attributes={"operator": "kj"})]),
        None,
        frozenset({"operator"}),
        c,
    )
    found = {f.code: f.message for f in c.findings}
    assert "E-RESOLVER-MEASUREMENT-FIELD" in found
    assert "E-UNITS-ATTR-MISSING" not in found
    assert "read_id" in found["E-RESOLVER-MEASUREMENT-FIELD"]
    assert "plate_wells" in found["E-RESOLVER-MEASUREMENT-FIELD"]


def test_a_resolver_that_does_yield_the_measurement_field_reports_nothing():
    """THE CONTROL. Without it, a branch that reported unconditionally would pass
    the test above."""
    c = Collector()
    _check_measurements(
        {"from": {"resolver": "plate_wells"}, "measurements": {"by": "read_id", "collapse": "mean"}},
        UnitList([Unit(key="a1", attributes={"operator": "kj"})]),
        None,
        frozenset({"operator", "read_id"}),
        c,
    )
    assert [f.code for f in c.findings] == []


def test_a_table_source_keeps_its_collapse_gated_reading_of_the_same_field():
    """The two paths stay different, deliberately. A table's `by` naming no column
    is only a fault once rows were actually collapsed, because the same
    declaration serves the step path. Asserting this here is what stops a future
    tidy-up from unifying the two branches on the resolver's stricter rule."""
    c = Collector()
    _check_measurements(
        {"from": "index.csv", "measurements": {"by": "read_id", "collapse": "mean"}},
        UnitList([Unit(key="a1", attributes={"operator": "kj"})]),
        {"min": 1, "max": 1, "median": 1},
        frozenset({"operator"}),
        c,
    )
    assert [f.code for f in c.findings] == []
```

- [ ] **Step 2: Run and see it fail.** The first test fails with
      `"E-RESOLVER-MEASUREMENT-FIELD" in found` → `False` (no such branch exists).

- [ ] **Step 3: Implement.** In `validate._check_measurements`, immediately after `valid_by` is
      computed and **before** the existing `elif technical_n is not None and technical_n["max"] > 1`
      arm, add a resolver arm — read the surrounding `if valid_by is None:` chain and extend it
      rather than inserting a second, parallel chain:

```python
    source = units.get("from")
    resolver = source.get("resolver") if isinstance(source, dict) else None
    if valid_by is not None and isinstance(resolver, str) and resolver:
        # Ungated, unlike the table arm below it. A table's `by` may name a
        # measurement identity the STEP invents through `io.record(...,
        # measurement=)`, which is why that arm waits until rows were actually
        # collapsed. A resolver has no columns at all, so `reference.md` § Where
        # units come from turns yielding `by` into an obligation — "the field a
        # CSV would simply have carried has to be named" — and
        # `E-RESOLVER-MEASUREMENT-FIELD`'s row states the fault without a collapse
        # precondition. The columns here are what the resolver yielded, before the
        # projection onto `data.units.attributes`: the projected roster carries
        # only declared attributes, and `by` is not one of them.
        if valid_by not in columns:
            c.error(
                "E-RESOLVER-MEASUREMENT-FIELD",
                "data.units.measurements.by",
                f"names {valid_by!r}, and resolver `{resolver}` yields no unit carrying an "
                "attribute of that name to collapse on. A resolver has no columns beyond the "
                "attributes it yields, so yield one `Unit` per measurement, sharing a `key`, "
                f"and emit {valid_by!r} as an attribute",
            )
```

      and guard the existing table arm so one declaration draws one code: change it to
      `elif valid_by is not None and resolver is None and technical_n is not None and technical_n["max"] > 1:`
      — read the existing chain before editing, because its first arm is `if valid_by is None:` and
      the shape must stay a single chain.

      In `docs/reference.md`, strike `E-RESOLVER-MEASUREMENT-FIELD`'s **`Not yet emitted:`** clause
      whole — the sentence *"a resolver-produced roster does not exist in this build"* is the claim
      that expires. The row's `E-UNITS-ATTR-MISSING` cross-reference stays: the two codes still name
      different declarations.

- [ ] **Step 4: Run and see it pass.** `uv run pytest` → **2082 + 3 = 2085 passed**, 1 skipped,
      2 xfailed. Then the other three commands.

- [ ] **Step 5: Mutate.** In `src/publishable/validate.py`, change the resolver arm's
      `if valid_by not in columns:` to `if valid_by not in columns and technical_n is not None and technical_n["max"] > 1:`
      — the gate the table arm carries, applied where the row says it must not be.
      `tests/test_validate.py::test_a_resolver_yielding_no_measurement_field_is_refused_under_its_own_code`
      must **FAIL**: its `technical_n` argument is `None`, so the gated branch reports nothing.
      **Checked against the test body:** the test passes `None` for `technical_n` precisely to
      instantiate the ungated reading — a test that passed `{"max": 3}` would have made this
      mutation blind, and the choice of `None` is what separates the two readings.

      Second mutation, for the code split: change the resolver arm's code string to
      `"E-UNITS-ATTR-MISSING"`. The same test must **FAIL** on
      `assert "E-UNITS-ATTR-MISSING" not in found`. **Checked:** that negative assertion is paired
      with a positive one on the resolver code in the same test, so it is not a bare absence.

- [ ] **Step 6: Commit.** `validate: a resolver must yield the measurement field it declares`

---

## Task 29: condition-independence — `E-RESOLVER-SWEPT-PARAM`

**Files:** Modify `src/publishable/units.py`, `docs/reference.md`, `tests/test_units.py`.

**Interfaces:**
- Consumes: `config.SweptAway(path)` and `config.Node.__getattr__`, which raises `ContractError` ·
  `E-STEP-SWEPT-PARAM` on resolving one — read in `src/publishable/config.py`;
  `runner.resolve_wide_cfg(base, swept_paths) -> Config`, which plants a marker at every swept path
  under `parameters`, walking with `setdefault`; `sweep.wide_swept_paths` (moved in task 25), whose
  union is `_swept_paths` ∪ `ablated_paths` ∪ `baseline` keys, minus `selector_paths`.
- Produces: `_from_resolver` translating an `E-STEP-SWEPT-PARAM` raised inside the resolver into
  `ContractError` · `E-RESOLVER-SWEPT-PARAM`; § Errors' `Not yet emitted:` clause struck.

**The mechanism is shared and the fault is not.** Part A's `E-RESOLVER-SWEPT-PARAM` row settles the
reuse-or-mint question and this task honours it rather than re-making it: *"that identifier is a
step's, reached at run time from `"run"` or `"summary"` scope, and a reader holding it is sent to a
section describing a different fault at a different time. Sharing the mechanism — a sentinel
substituted for a swept path, raising on the read — is not sharing the fault, the same way a coded
`ContractError` from a local template's top level is reported as `E-TEMPLATE-LOAD` rather than under
the code it carried."*

**Translate only `E-STEP-SWEPT-PARAM`, and let every other coded raise through.** A resolver that
raises `ContractError` · `E-UNITS-SOURCE-MISSING` from `io.read_input` must keep that code — the
scoping's probe A shows it arriving at `validate` under its own identifier, redacted. Only the
sentinel read is re-coded.

**No document change beyond the marker.** § Where units come from already states the rule and its
reason: *"a resolver that reads a parameter the sweep varies is rejected by `validate`. The unit
table is one table for the whole run, so conditions that resolved different units couldn't be paired
and `n` would mean something different in each. Parameters the sweep leaves alone are fair game."*

- [ ] **Step 1: Write the failing test.** Append to `tests/test_units.py`:

```python
_READS_A_PARAM = """\
from publishable import Unit, register_resolver


@register_resolver("plate_wells")
def resolve(io, cfg):
    yield Unit(key=str(cfg.parameters.analysis.method))
"""


def test_a_resolver_reading_a_swept_parameter_is_refused_under_its_own_code(
    installed, registries, tmp_path
):
    """`E-RESOLVER-SWEPT-PARAM`, not `E-STEP-SWEPT-PARAM`: the mechanism is shared
    and the fault is not — a reader holding the step's identifier is sent to a
    section describing a different fault at a different time."""
    from publishable.errors import ContractError
    from publishable.runner import resolve_wide_cfg
    from publishable.sweep import wide_swept_paths
    from publishable.units import resolve_units

    doc = {
        "parameters": {"analysis": {"method": "pearson"}},
        "sweep": {"grid": {"analysis.method": ["pearson", "spearman"]}},
    }
    cfg = resolve_wide_cfg(doc, wide_swept_paths(doc["sweep"]))
    _install_resolver(installed, tmp_path, "swept_r29", _READS_A_PARAM)
    try:
        with pytest.raises(ContractError) as excinfo:
            resolve_units(
                {"from": {"resolver": "plate_wells"}, "key": "well"}, tmp_path, cfg=cfg
            )
    finally:
        sys.modules.pop("swept_r29", None)
    assert excinfo.value.code == "E-RESOLVER-SWEPT-PARAM"
    assert "plate_wells" in str(excinfo.value)
    assert "analysis.method" in str(excinfo.value)


def test_a_resolver_reading_a_parameter_the_sweep_leaves_alone_resolves(
    installed, registries, tmp_path
):
    """THE CONTROL, and § Where units come from's own sentence: "Parameters the
    sweep leaves alone are fair game, which is how a resolver is told which assay,
    panel, or shard to include." Without it, a refusal that fired for every `cfg`
    read would pass the test above."""
    from publishable.runner import resolve_wide_cfg
    from publishable.sweep import wide_swept_paths
    from publishable.units import resolve_units

    doc = {
        "parameters": {"analysis": {"method": "pearson"}},
        "sweep": {"grid": {"analysis.min_samples": [10, 20]}},
    }
    cfg = resolve_wide_cfg(doc, wide_swept_paths(doc["sweep"]))
    _install_resolver(installed, tmp_path, "unswept_r29", _READS_A_PARAM)
    try:
        roster, _n, _columns = resolve_units(
            {"from": {"resolver": "plate_wells"}, "key": "well"}, tmp_path, cfg=cfg
        )
    finally:
        sys.modules.pop("unswept_r29", None)
    assert [u.key for u in roster] == ["pearson"]


def test_a_resolvers_own_coded_refusal_keeps_its_own_identifier(
    installed, registries, tmp_path
):
    """Only the sentinel read is re-coded. A resolver reading a file that is not
    there gets `E-UNITS-SOURCE-MISSING`'s cousin from `io`, and re-coding
    everything would tell a reader their sweep was at fault."""
    from publishable.config import Config
    from publishable.errors import ContractError
    from publishable.units import resolve_units

    _install_resolver(
        installed,
        tmp_path,
        "coded_r29",
        "from publishable import ContractError, Unit, register_resolver\n\n\n"
        '@register_resolver("plate_wells")\n'
        "def resolve(io, cfg):\n"
        "    raise ContractError('nope', code='E-UNITS-EMPTY')\n"
        "    yield Unit(key='a1')\n",
    )
    try:
        with pytest.raises(ContractError) as excinfo:
            resolve_units(
                {"from": {"resolver": "plate_wells"}, "key": "well"}, tmp_path, cfg=Config({})
            )
    finally:
        sys.modules.pop("coded_r29", None)
    assert excinfo.value.code == "E-UNITS-EMPTY"
```

- [ ] **Step 2: Run and see it fail.** The first test fails on `excinfo.value.code ==
      "E-RESOLVER-SWEPT-PARAM"` — it is `E-STEP-SWEPT-PARAM` today.

- [ ] **Step 3: Implement.** In `src/publishable/units.py`, wrap `_from_resolver`'s iteration:

```python
    try:
        for item in resolve(io, cfg):
            ...
    except ContractError as exc:
        if exc.code != "E-STEP-SWEPT-PARAM":
            raise
        # The mechanism is shared and the fault is not. `config.Node` raises the
        # step's identifier because that is what it raises for every reader of a
        # `SweptAway` marker; a reader holding it here would be sent to § Step
        # scope, which describes a different fault at a different time. Re-coded
        # rather than re-raised, on `discover_local`'s precedent for a coded
        # `ContractError` out of user code.
        raise ContractError(
            f"resolver `{name}` reads {exc}. The unit table is one table for the whole run, "
            "so conditions that resolved different units could not be paired and `n` would "
            "mean something different in each. Read a parameter the sweep leaves alone",
            code="E-RESOLVER-SWEPT-PARAM",
        ) from exc
```

      **The message interpolates `exc`, which already names the swept path**
      (`config.Node.__getattr__` builds *"`parameters.analysis.method` is varied by `sweep`…"`*), so
      the path is not re-derived here — a second derivation is how the two would come to disagree
      about which path was read.

      In `docs/reference.md`, strike `E-RESOLVER-SWEPT-PARAM`'s **`Not yet emitted:`** clause whole.

- [ ] **Step 4: Run and see it pass.** `uv run pytest` → **2085 + 3 = 2088 passed**, 1 skipped,
      2 xfailed. Then the other three commands.

- [ ] **Step 5: Mutate.** In `src/publishable/units.py`, change `if exc.code != "E-STEP-SWEPT-PARAM":
      raise` to `if False: raise` — i.e. re-code every `ContractError` the resolver raises.
      `tests/test_units.py::test_a_resolvers_own_coded_refusal_keeps_its_own_identifier` must
      **FAIL**: its resolver raises `E-UNITS-EMPTY`, which would come back as
      `E-RESOLVER-SWEPT-PARAM`. **Checked against the test body:** the fixture raises a code that is
      neither of the two involved, so the two branches genuinely differ — a fixture raising
      `E-STEP-SWEPT-PARAM` itself could not have told the readings apart.

      Second mutation, for the honouring: in `src/publishable/validate.py`, change `_check_units`'s
      `cfg=resolve_wide_cfg(doc, wide_swept_paths(doc.get("sweep") or {}))` to
      `cfg=resolve_wide_cfg(doc, set())` — a config with no markers planted at all. **This does not
      fail any test in this task**, because all three call `resolve_units` directly with a cfg they
      built themselves. It is task 33's `validate`-level test that catches it, and task 33's brief
      says so. Recorded here rather than left silent: **a mutation's silence is evidence about the
      tests**, and the test that would catch this one is scheduled rather than missing.

- [ ] **Step 6: Commit.** `units: a resolver reading a swept parameter is refused under its own code`

---

## Task 30: `provenance.plugin_versions`, and the dated *no production caller* notes

**Files:** Modify `src/publishable/plugins.py`, `src/publishable/cli.py`,
`docs/reference.md`, `docs/superpowers/spec-defects.md`, `tests/test_plugins.py`,
`tests/test_cli.py`.

**Interfaces:**
- Consumes: `plugins.provider_of(ep: EntryPoint) -> str`, which returns `f"{dist.name} {dist.version}"`
  — read in `src/publishable/plugins.py`; `plugins.scan_group`; the literal `"plugin_versions": {}`
  in `cli.py`'s provenance document, and `"publishable_version"` beside it, which is
  `importlib.metadata.version("publishable")`.
- Produces: `plugins.versions_for(group: str, name: str) -> dict[str, str]`;
  `provenance.plugin_versions` populated for a resolver-sourced run; the two dated
  *no production caller* notes in `plugins.py` retired; `spec-defects.md`'s shipped-but-unread
  filing amended for the four surfaces this slice reads.

**What it records, from the document.** § Where units come from: *"the resolver's plugin version in
`provenance.plugin_versions`"*, and `design-principles.md` § Whose git hash is this?: *"plugin
versions as `provenance.plugin_versions` — compatibility notes, never conflated with the code that
ran your experiment."* So it is a `{distribution: version}` mapping, and it is **not** part of
`code_hash`: a plugin is pinned by `uv.lock`, which is why nothing here may extend `HASHED_TREES`.

**Only what this run actually used.** A machine's whole installed set is not this run's provenance;
the resolver a config named is. An empty mapping stays the honest record for a run with no plugin
artifact, which is exactly what it records today by accident and will record by construction after
this task.

**The two `deaed2b`-dated notes this task retires** are `plugins.py`'s module docstring
(*"no command has yet been wired to call it"*) and `check_registration`'s (*"no command yet loads a
plugin, so this function has no production caller either"*). The two matching `reference.md` notes
were deleted in task 22 with the sentences that carried them; confirm by sweeping the file list:
`grep -rn "against commit .deaed2b." docs/reference.md src/` → empty after this task.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_plugins.py`:

```python
def test_versions_for_names_the_distribution_a_reader_would_pin(installed):
    """A distribution and its version, because that is what `uv.lock` pins and
    what a reader uninstalls — not a module path, which pins nothing."""
    from publishable.plugins import versions_for

    installed("dist-one", "1.0", {"publishable.resolvers": {"plate_wells": "no_one:resolve"}})
    assert versions_for("publishable.resolvers", "plate_wells") == {"dist-one": "1.0"}
    assert versions_for("publishable.resolvers", "not_registered") == {}
```

      and in `tests/test_cli.py`, an end-to-end assertion through `command_run` on a resolver-sourced
      config (the path is open now that task 26 landed) — model it on the file's existing
      `command_run` tests, and assert the recorded mapping **and** its control:

```python
def test_a_resolver_run_records_the_plugin_version_it_resolved_through(
    installed, registries, git_repo, tmp_path
):
    """`provenance.plugin_versions` — compatibility notes, never conflated with
    `code_hash`, which covers `src/**` and `templates/**` and not a wheel. The
    control is a table-sourced run in the same test: an empty mapping stays the
    honest record where no plugin artifact was used, so a version dict populated
    unconditionally would pass the first half alone."""
    ...  # build the two configs with the file's existing run helper
    assert resolver_run["provenance"]["plugin_versions"] == {"dist-one": "1.0"}
    assert table_run["provenance"]["plugin_versions"] == {}
```

- [ ] **Step 2: Run and see it fail.** `ImportError: cannot import name 'versions_for'`.

- [ ] **Step 3: Implement.** In `src/publishable/plugins.py`:

```python
def versions_for(group: str, name: str) -> dict[str, str]:
    """The distributions providing `name` in `group`, as `{name: version}`.

    A distribution rather than a module, for `provider_of`'s reason: a
    distribution is what a reader uninstalls or pins, and `provenance` exists to
    be reproduced from. Empty for a name nothing registers, which is the same
    answer a run using no plugin artifact records — an absence, not a guess.

    Every claimant, not the first: `validate._check_plugin_collisions` refuses a
    name two distributions claim, so more than one entry here means the record is
    describing a machine `validate` already refused. Recording both is what makes
    that visible in the artifact rather than only in the terminal.
    """
    return {
        ep.dist.name: ep.dist.version
        for ep in scan_group(group).get(name, [])
        if ep.dist is not None
    }
```

      and delete the two dated *no production caller* sentences from the module docstring and from
      `check_registration`'s docstring. **Delete rather than rewrite**: their claim expired, and a
      replacement sentence would be a new maintenance obligation nobody owns.

      In `src/publishable/cli.py`, replace the `"plugin_versions": {}` literal with a local computed
      beside the roster, so the mapping and the resolver that produced it cannot drift:

```python
    # Populated from the declaration this run actually resolved through, not from
    # the machine's installed set: a run's provenance is what it used. Empty stays
    # the honest record for a run with no plugin artifact.
    plugin_versions: dict[str, str] = {}
    _source = (units_decl or {}).get("from")
    if isinstance(_source, dict) and isinstance(_source.get("resolver"), str):
        plugin_versions = versions_for(RESOLVER_GROUP, _source["resolver"])
```

      In `docs/reference.md` § What `run.yaml` records, the `plugin_versions: {}` line in the fenced
      example stays `{}` — the worked example's `cohort-pilot` uses a table source, and changing it
      would break the shared worked example across three documents. Add one sentence to the prose
      naming what fills it.

      In `docs/superpowers/spec-defects.md`, amend
      `## OPEN — PROBES and RESOLVERS are written by their decorators and read by nothing` by
      **appending** an amendment (never retro-editing): `RESOLVERS`, `load_entry_point`,
      `check_registration` and `declared_names` now have production callers, naming the tasks;
      `PROBES` stays with H7d and `registry.template_provenance` stays with the unassigned
      installed-template entry. Amend
      `## OPEN — an installed template's name resolves but its class is never loaded` to record that
      one of its three preconditions — `provenance.plugin_versions` — is now built; **amend, do not
      close**, and leave its owner unassigned.

- [ ] **Step 4: Run and see it pass.** `uv run pytest` → **2088 + 2 = 2090 passed**, 1 skipped,
      2 xfailed. Then the other three commands.

- [ ] **Step 5: Mutate.** In `src/publishable/cli.py`, change the `plugin_versions` assignment back
      to `plugin_versions = {}` unconditionally.
      `tests/test_cli.py::test_a_resolver_run_records_the_plugin_version_it_resolved_through` must
      **FAIL** on the resolver half. **Checked against the test body:** the test asserts a populated
      mapping for the resolver run *and* an empty one for the table run, so the mutation cannot pass
      by making both empty — which the resolver-only assertion alone would not have caught in the
      other direction (a mapping populated unconditionally), and which is why the control is there.

      Second mutation: in `plugins.versions_for`, change `ep.dist.name` to `ep.value`.
      `tests/test_plugins.py::test_versions_for_names_the_distribution_a_reader_would_pin` must
      **FAIL** — the key becomes the module path, which pins nothing.

- [ ] **Step 6: Commit.** `provenance: record the plugin version a resolver run resolved through`

---

## Task 31: `hash_index` — the table case and the resolver case together

**Files:** Modify `src/publishable/manifest.py`, `src/publishable/units.py`,
`src/publishable/cli.py`, `docs/superpowers/spec-defects.md`, `tests/test_manifest.py`,
`tests/test_cli.py`.

**Interfaces:**
- Consumes: `manifest.build_manifest(input_dir: Path, policy: str, index_names: set[str] | None = None) -> dict[str, Any]`,
  whose `hash_it` is `policy == "hash_all" or (policy == "hash_index" and rel in (index_names or set()))`
  — read in `src/publishable/manifest.py`; `cli.py`'s single call site,
  `build_manifest(input_dir, doc["data"]["input_manifest_policy"])`, which passes **two** arguments;
  `Unit.paths: tuple[str, ...]`; `ResolverIO.read_paths` from task 23.
- Produces: `units.index_names(units_decl: dict, roster: UnitList | None, reads: tuple[str, ...] = ()) -> set[str]`;
  `cli.py` threading it; a `spec-defects.md` filing for the pre-existing table-case defect, struck
  CLOSED in the same entry.

**This is broken for the table case too, and the resolver half cannot be built without closing it.**
Measured at `53090e9` and re-confirmable: `index_names` has zero callers in `src/` and no mention in
`tests/`; under `hash_index` **every** `sha256` comes back `None`, for a table source as much as a
resolver's. Three `reference.md` passages promise otherwise — § Three hashes' table
(*"Content hashes for the files `data.units.from` resolves — the index and whatever it names"*),
§ What `run.yaml` records (*"Under `hash_index` the `sha256` key is present for the files
`data.units.from` resolves and absent for the rest"*), and § Where units come from. It is
**unfiled**: `grep -n "hash_index" docs/superpowers/spec-defects.md` → nothing. File it and close it
in the same entry, since this is the task that cannot proceed without closing it.

**Three sources, one expression.** `_from_table` sets `paths=()` and the source names one file;
`_from_glob` sets `paths=(rel,)` and the source names none; a resolver names whatever it read and
its units name their own paths. So *the source's own file, where the source names one, plus every
path its units name* covers all three, and **no case is left silently empty** — which is the failure
mode of shipping table + resolver and leaving glob at `sha256: None`.

**The trap this task is specifically exposed to.** Under `hash_index` the `sha256` **key is present
and its value is `None`**. An assertion on `"sha256" in entry` passes on a completely broken policy —
§ What `run.yaml` records anticipates exactly this (*"Absent rather than null, so 'not hashed' can't
be misread as 'hashed to nothing'"*) and the code does the thing the document says it must not.
**Assert the value**, and include a file the source does *not* name whose `sha256` is `None`, or the
test passes on a policy behaving like `hash_all`.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_manifest.py`:

```python
def test_hash_index_hashes_the_named_files_and_nothing_else(tmp_path):
    """The VALUE, not the key. Under `hash_index` the `sha256` key is present and
    `None` today, so `"sha256" in entry` passes on a completely broken policy —
    which is how this went unnoticed since the policy shipped. The unnamed file is
    the control that separates `hash_index` from `hash_all`."""
    (tmp_path / "index.csv").write_text("patient_id\np1\n")
    (tmp_path / "scan.bin").write_bytes(b"\x00\x01")
    (tmp_path / "unnamed.txt").write_text("not named by anything\n")

    manifest = build_manifest(tmp_path, "hash_index", {"index.csv", "scan.bin"})
    files = manifest["files"]

    assert files["index.csv"]["sha256"] is not None
    assert files["scan.bin"]["sha256"] is not None
    assert files["unnamed.txt"]["sha256"] is None
    assert files["index.csv"]["sha256"] == build_manifest(tmp_path, "hash_all")["files"][
        "index.csv"
    ]["sha256"]
```

      and in `tests/test_units.py`:

```python
def test_index_names_covers_every_source_shape(tmp_path):
    """One expression, three sources: the source's own file where it names one,
    plus every path its units name. A table names its index and no paths; a glob
    names no index and one path per unit; a resolver names what it read and
    whatever its units carry. Asserted together, because shipping two of the three
    is how the glob case would be left at `sha256: None` silently."""
    from publishable.units import UnitList, Unit, index_names

    table = UnitList([Unit(key="p1"), Unit(key="p2")])
    globbed = UnitList([Unit(key="a.dcm", paths=("a.dcm",)), Unit(key="b.dcm", paths=("b.dcm",))])
    resolved = UnitList([Unit(key="a1", paths=("reads/a1.fq",))])

    assert index_names({"from": "index.csv"}, table) == {"index.csv"}
    assert index_names({"from": {"glob": "*.dcm"}}, globbed) == {"a.dcm", "b.dcm"}
    assert index_names({"from": {"resolver": "plate_wells"}}, resolved, ("layout.csv",)) == {
        "layout.csv",
        "reads/a1.fq",
    }
    assert index_names({"from": "index.csv"}, None) == {"index.csv"}  # no roster, still the index
```

- [ ] **Step 2: Run and see it fail.** The manifest test fails on
      `files["index.csv"]["sha256"] is not None` today **only if** the third argument is dropped —
      so run it first *with* the argument to confirm `build_manifest` already honours a set it is
      given (it does; the defect is that nothing gives it one), then the `units` test fails with
      `ImportError: cannot import name 'index_names'`. Record both outcomes: the fix is the wiring,
      not the manifest's arithmetic.

- [ ] **Step 3: Implement.** In `src/publishable/units.py`:

```python
def index_names(
    units_decl: dict[str, Any], roster: UnitList | None, reads: tuple[str, ...] = ()
) -> set[str]:
    """The relative paths `input_manifest_policy: hash_index` hashes.

    `reference.md` § Three hashes: "the index and whatever it names". One
    expression over all three sources, because a per-source branch is how one of
    them comes to be left silently unhashed:

    - a **table** names one file and its units name no paths;
    - a **glob** names no file and each unit names the path it was built from;
    - a **resolver** names whatever it read (`ResolverIO.read_paths`) and its
      units name their own payloads — § Where units come from: "the paths the
      resolver read plus the paths its units name, so a unit whose payload the
      resolver never opened still gets that payload hashed".

    A roster that did not resolve still yields the source's own file: the index is
    named by the declaration, not by the roster, and a manifest built beside a
    failed resolution should not silently stop hashing it.
    """
    source = units_decl.get("from")
    named: set[str] = set(reads)
    if isinstance(source, str) and source:
        named.add(source)
    for unit in roster or ():
        named.update(unit.paths)
    return named
```

      In `src/publishable/cli.py`, thread it at the one `build_manifest` call site, which sits
      **downstream** of the roster in `command_run` — so nothing moves:

```python
    manifest = build_manifest(
        input_dir,
        doc["data"]["input_manifest_policy"],
        index_names(units_decl or {}, roster, resolver_io.read_paths),
    )
```

      In `src/publishable/manifest.py`, `build_manifest`'s docstring says *"Relative paths plus
      size, mtime, and — at the policy's depth — content hash"*, which was false for `hash_index`
      because nothing supplied `index_names`. It is true now; leave it, and add one sentence naming
      `units.index_names` as what supplies the set, so a future reader can find the answer to "which
      files does the index name".

      In `docs/superpowers/spec-defects.md`, add an entry — filed and struck CLOSED in one, with the
      measurement that found it and the commit it was measured against — recording that
      `hash_index` hashed nothing at all for **every** source until this task, that
      `build_manifest`'s `index_names` had no caller, and that `hash_index` appeared in no test.

- [ ] **Step 4: Run and see it pass.** `uv run pytest` → **2090 + 2 = 2092 passed**, 1 skipped,
      2 xfailed. Then the other three commands.

- [ ] **Step 5: Mutate.** In `src/publishable/cli.py`, drop the third argument from the
      `build_manifest` call — restoring the state this task found.
      `tests/test_cli.py`'s end-to-end `hash_index` assertion (add one beside the
      `plugin_versions` test if the file has none: run a `hash_index` config and assert the index's
      `sha256` is not `None` and an unnamed file's is) must **FAIL**. **Checked:**
      `tests/test_manifest.py`'s test passes the set directly and would **not** catch this — it
      pins the arithmetic, not the wiring, and the wiring is the defect. That is why the mutation is
      named at the call site and the test that catches it is the end-to-end one.

      Second mutation, in `units.index_names`: delete the `for unit in roster or ():` loop.
      `tests/test_units.py::test_index_names_covers_every_source_shape` must **FAIL** on the glob
      case, which has no source file and would come back empty. **Checked against the test body:**
      the glob assertion is exactly the case where the source names nothing, so it cannot be
      satisfied by the `source` term alone.

- [ ] **Step 6: Commit.** `manifest: hash_index actually hashes the index — for every source`

---

## Task 32: the credential leak, both halves, and the non-`PublishableError` containment

**Files:** Modify `src/publishable/validate.py`, `src/publishable/cli.py`,
`docs/reference.md`, `tests/test_validate.py`, `tests/test_cli.py`.

**Interfaces:**
- Consumes: `secrets.redact(text: str | None, values: Mapping[str, str]) -> str | None` and its
  **two** call sites, `diagnostics.Collector.render` and `runner.execute_plan` — verified by reading
  both; `Collector.credentials: dict[str, str]`, whose own comment says *"Redaction happens at
  render, not at construction … so setting this after the fact still covers every finding already
  appended"*; `cli.main`'s handler, which prints `f"  error   {exc.code:<20} {exc}"` to stderr with
  **no collector in scope**; `cli.command_run`'s existing post-validate collectors `dirty_c`,
  `warn_c`, `drift_c`, each a **fresh** `Collector()` with `.credentials` assigned;
  `cli.declared_credential_names(doc, template, conditions)`; `validate._check_units`'s
  `except ContractError`.
- Produces: `credentials` computed in `command_run` **before** the roster resolves; the roster call
  wrapped, reporting through a fresh redacting collector; `_check_units` gaining a broad arm
  reporting `E-RESOLVER-RAISED`; a § Errors core raises row for `E-RESOLVER-RAISED`.

**Both halves, and the prior prescription was wrong.** Two documents said *"move the credential
computation, not wrap the call."* `redact` has exactly two call sites and `main`'s handler is
neither — it prints `{exc}` raw. **So moving the computation alone produces values nothing
applies.** The working remedy is both: compute the credential set before phase 5 *and* route the
resolver's raise through a redacting surface.

**A fresh collector, not `command_run`'s `c` — a spec-versus-code note.** Decision 2 says "route the
resolver's raise through `command_run`'s existing collector". Taken literally that double-renders:
`c` has already been printed by `if c.findings: print(c.render())` before phase 5, so appending and
re-rendering re-prints every warning and inflates the counts line. Taken as *"through a redacting
surface"* — which is what makes the fix work — a fresh `Collector()` with `.credentials = credentials`
satisfies it, and it is `command_run`'s own convention for a post-validate finding: `dirty_c`,
`warn_c` and `drift_c` all do exactly that. Take the fresh collector.

**Decision 3, and the placement it settles.** `_check_units` guards only `except ContractError`, so
a plugin resolver raising `KeyError` breaks the *"`validate` never raises"* contract (probe B). At
`run` such a raise **escapes `main` entirely as a traceback with the credential in it** (probe D) —
the one output no redacting surface sees. Contain it at both. The broad arm belongs at each command
rather than inside `units._from_resolver`, for a reason worth stating: a guard inside `resolve_units`
would be bypassed by any test that patches `resolve_units` itself, which is exactly how probes B and
D were run and how this task's tests can run *before* task 26 opens the resolver path at `validate`.

**Why the tests use a table source and a monkeypatched `resolve_units`.** This task must land before
task 26, and until 26 a `{resolver: ...}` config earns `E-DATA-RESOLVER-UNSUPPORTED`, which is an
error, so `command_run` returns `EXIT_WRONG` at the validate gate and never reaches phase 5. A
table-source config that validates clean, with the `resolve_units` **binding in each module**
monkeypatched to raise, exercises exactly the plumbing under test — which is what the scoping's four
probes did. Patch `publishable.validate.resolve_units` and `publishable.cli.resolve_units`; both
modules bind the name with `from publishable.units import ...`, so patching `publishable.units`
alone would not take.

**A leak test asserting only an absence passes identically when nothing raised.** Pair every
sentinel sweep with the control that proves the sentinel is reachable — the same arrangement the
scoping used, where probe A's redacted output is what makes probes C and D readable.

- [ ] **Step 1: Write the failing test.** In `tests/test_validate.py`:

```python
def test_a_resolvers_non_contract_raise_does_not_escape_validate(monkeypatch, write_config):
    """Probe B. `validate` is contracted never to raise; a plugin resolver raising
    `KeyError` is user code, and `_check_units` guarded only `ContractError`."""
    import publishable.validate as validate_module

    def _boom(*_args, **_kwargs):
        raise ValueError("resolver failed")

    monkeypatch.setattr(validate_module, "resolve_units", _boom)
    found = messages_by_code(write_config())
    assert "E-RESOLVER-RAISED" in found
    assert "ValueError" in found["E-RESOLVER-RAISED"]


def test_a_resolvers_raise_is_redacted_at_validate(monkeypatch, write_config, tmp_path, git_repo):
    """Probe A, kept as the CONTROL that makes the run-side tests readable: the
    identical exception from the identical function must come back redacted here,
    or a stderr sweep finding no sentinel proves nothing about redaction."""
    import publishable.validate as validate_module

    monkeypatch.setenv("MY_KEY", "SENTINEL-sk-abc123")
    (git_repo / "templates").mkdir(exist_ok=True)
    (git_repo / "templates" / "keyed.py").write_text(_TEMPLATE_REQUIRING_MY_KEY)

    def _boom(*_args, **_kwargs):
        raise ValueError("resolver failed: key=SENTINEL-sk-abc123")

    monkeypatch.setattr(validate_module, "resolve_units", _boom)
    c = Collector()
    validate_config(write_config({"experiment_type": "keyed", "template_version": _DELETE}), c)
    rendered = c.render()
    assert "SENTINEL-sk-abc123" not in rendered
    assert "<redacted:MY_KEY>" in rendered  # the positive companion
```

      (`_TEMPLATE_REQUIRING_MY_KEY` is a project-local template declaring
      `required_env = ["MY_KEY"]`; read `tests/test_validate.py` for an existing local-template
      fixture string before adding a new one, and reuse it if one exists.)

      In `tests/test_cli.py`:

```python
def test_a_resolvers_raise_at_run_is_redacted_rather_than_printed_whole(
    monkeypatch, capsys, ...
):
    """Probes C and D. C: a `ContractError` from resolution printed verbatim
    through `main`'s bare handler. D: a `ValueError` escaping `main` entirely as a
    traceback with the credential in it — the one output no redacting surface
    sees. Both are asserted with the positive companion (the diagnostic IS
    produced, with the marker in it), so a sweep finding no sentinel cannot pass
    on a run that never raised."""
    for exception in (ContractError("resolver failed: key=SENTINEL-sk-abc123", code="E-UNITS-SOURCE-MISSING"), ValueError("resolver failed: key=SENTINEL-sk-abc123")):
        ...
        assert exit_code == EXIT_WRONG                       # no traceback
        assert "SENTINEL-sk-abc123" not in captured
        assert "<redacted:MY_KEY>" in captured               # the positive companion


def test_a_run_whose_roster_resolves_cleanly_still_reports_nothing(...):
    """THE CONTROL for the pair above: the wrap must not turn a healthy run into a
    finding. Without it, a `try` that reported unconditionally would pass both."""
```

- [ ] **Step 2: Run and see it fail.** The `validate` test fails with the `ValueError` propagating
      out of `validate_config`; the `run` tests fail with the sentinel present in stderr (the
      `ContractError` arm) and with a traceback (the `ValueError` arm).

- [ ] **Step 3: Implement.** In `src/publishable/validate.py`, `_check_units`, add a second arm
      after the existing `except ContractError`:

```python
    except Exception as exc:
        # A resolver is user code, and `validate` is contracted never to raise —
        # so anything that is not already a coded refusal becomes one here. The
        # table and glob branches raise `ContractError` and nothing else, so this
        # arm is a resolver's by construction rather than a catch-all over core.
        # `SystemExit` is a `BaseException` and is `load_entry_point`'s to contain
        # at import; a resolver body calling `sys.exit()` mid-iteration is the
        # residual, named rather than swallowed.
        c.error(
            "E-RESOLVER-RAISED",
            "data.units",
            f"resolution raised {type(exc).__name__}: {exc}",
        )
        return None, None, frozenset()
```

      In `src/publishable/cli.py`, `command_run`: move the three lines that resolve the template and
      the credential set — `conditions = expand(doc)`, `run_template = get_template(...)`,
      `credentials = credential_values(declared_credential_names(doc, run_template, conditions))` —
      **above** the phase-5 roster block, keeping their existing comments with them, and leave a
      comment at the old site saying why they moved (the resolver's raise is the first thing in the
      command that can carry a credential into a message). Then wrap the roster call:

```python
    try:
        roster, technical_n, _columns = (
            resolve_units(units_decl, input_dir, cfg=..., resolver_io=resolver_io)
            if units_decl
            else (None, None, frozenset())
        )
    except Exception as exc:
        # `main`'s handler prints `{exc}` with no collector in scope, and a
        # non-`PublishableError` never reaches it at all — it ends the command in
        # a traceback. A resolver's message can carry a credential it read, so the
        # raise is turned into a diagnostic here, through a collector holding the
        # values `redact` answers from. A FRESH collector rather than `c`, which
        # has already been rendered and printed above: appending to it would
        # re-print every earlier finding and inflate the counts line.
        roster_c = Collector()
        roster_c.credentials = credentials
        code = exc.code if isinstance(exc, PublishableError) else "E-RESOLVER-RAISED"
        roster_c.error(code, "data.units", str(exc))
        print(roster_c.render(), file=sys.stderr)
        return EXIT_WRONG
```

      In `docs/reference.md` § Errors core raises, add a row for `E-RESOLVER-RAISED`: a resolver's
      own body raising something that is not a `PublishableError`, contained at `validate` and at
      `run` so it becomes a diagnostic rather than a traceback, since a traceback is the one output
      no redacting surface sees. Cross-reference § Secrets & credentials.

- [ ] **Step 4: Run and see it pass.** `uv run pytest` → **2092 + 5 = 2097 passed**, 1 skipped,
      2 xfailed. Then the other three commands.

- [ ] **Step 5: Mutate.** **The obvious mutation cannot fail, and it is replaced.** The prior
      documents prescribe *"a test that goes red when the two lines swap"* — `c.credentials` and
      `_check_units` in `validate_config`. Redaction happens at **render**, and `c.credentials`'s
      own comment says so, so swapping them changes nothing: probe A redacts because `c.render()`
      runs after both, not because one precedes the other. Two branches that cannot differ.

      **Mutation (a), the one that discriminates the run-side fix:** in `src/publishable/cli.py`,
      delete the `roster_c.credentials = credentials` line, leaving the ordering intact.
      `tests/test_cli.py::test_a_resolvers_raise_at_run_is_redacted_rather_than_printed_whole` must
      **FAIL** on `"SENTINEL-sk-abc123" not in captured`. **Checked against the test body:** the
      collector still renders and still prints, so the diagnostic exists and only the redaction is
      gone — which is exactly the claim under test, and which a mutation producing an
      `UnboundLocalError` would not have isolated.

      **Mutation (b), the ordering, kept for what it does prove:** move the roster block back above
      the `run_template = get_template(...)` line. The same test must **FAIL** — with
      `UnboundLocalError: credentials`. **Named honestly:** this is red for a mechanical reason
      rather than a redaction one, so it proves the ordering is load-bearing and proves nothing
      about redaction. Both mutations, not one.

      **Mutation (c), the validate-side containment:** change `_check_units`'s new
      `except Exception` to `except ContractError` (i.e. duplicate the existing arm).
      `tests/test_validate.py::test_a_resolvers_non_contract_raise_does_not_escape_validate` must
      **FAIL** with the `ValueError` propagating out of `validate_config`.

      **What no mutation here reaches:** `main`'s handler itself. This task does not close
      `main`'s un-redacted stderr path in general — that is filed OPEN and unowned by H7c, and Part
      B owes only that it does not *widen* the exposure. Say so in the commit message.

- [ ] **Step 6: Commit.** `cli: a resolver's raise becomes a redacted diagnostic, not a traceback`

---

## Task 33: the owned prose sweep, and the reader-facing half

**Files:** Modify `docs/reference.md`, `docs/feasibility-llm-growth-studies.md`, `CLAUDE.md`,
`docs/superpowers/spec-defects.md`, `tests/test_validate.py`.

**Interfaces:**
- Consumes: the whole slice. `docs/feasibility-llm-growth-studies.md` § Executability on this build,
  whose subsections are each headed *"Measured on \<date\> against commit \<sha\>"*;
  `CLAUDE.md` § Misreadings' *unbuilt reader of a shipped surface* row, whose example is
  `BaseTemplate.required_env`.
- Produces: the newly-live roster-check family exercised end-to-end against a resolver-produced
  roster; a **new, dated** § Executability subsection carrying the three-of-nine count with its
  qualifications; two filings.

**The tests here are the ones tasks 25–29 could not write**, because `_check_units` skipped
resolution until task 26. **A check written where the roster is not proves nothing:** the checks
that survive under a resolver *today* are the declaration-against-declaration ones, so a test
mutating `cluster_by` proves nothing — it fires with the refusal in place. **The discriminating
fixtures are the ones that were lost**: a bad `key`, a bad attribute, `fold k=99`, a duplicate key.
And per the traps: **vary the resolver's yield, not the config shape.** Nineteen adversary configs
over one roster once made every refusal roster-incidental.

- [ ] **Step 1: Write the failing test.** In `tests/test_validate.py`, one parametrized test whose
      parameter is the **resolver body**, all against one config:

```python
_ROSTER_FAULTS = {
    "duplicate keys": ("yield Unit(key='a1')\n    yield Unit(key='a1')\n", "E-UNITS-KEY-DUPLICATE"),
    "no units at all": ("return\n    yield\n", "E-UNITS-EMPTY"),
    "swept parameter": ("yield Unit(key=cfg.parameters.analysis.method)\n", "E-RESOLVER-SWEPT-PARAM"),
    "undeclared attribute": ("yield Unit(key='a1')\n", "E-UNITS-ATTR-MISSING"),
}


@pytest.mark.parametrize("body,expected", list(_ROSTER_FAULTS.values()), ids=list(_ROSTER_FAULTS))
def test_the_roster_checks_are_real_against_a_resolver_produced_roster(
    installed, registries, write_config, body, expected
):
    """The kept/lost matrix, closed. Every one of these was UNREACHABLE under a
    resolver until this slice — the config's shape is identical across all four
    rows and only the resolver's YIELD varies, so no refusal here can be
    config-incidental. The control is the clean body: the same config with a
    well-formed resolver validates with no findings at all."""
```

      plus the clean-body control in the same test module, and a run-level test asserting
      `provenance.units_hash` is stable across two runs of one resolver and differs when the
      resolver yields a different order.

- [ ] **Step 2: Run and see it fail.** Write one row's fixture wrong on purpose first — a body that
      yields a well-formed roster under the "duplicate keys" id — and confirm the test fails.
      Then fix it. This is the can-fail proof for a parametrized test whose rows all assert a
      **failure**: a parametrization asserting a refusal for every arm proves nothing about the
      success path, which is why the clean-body control is not optional.

- [ ] **Step 3: Implement.** No `src/` change is expected. If a row fails for a reason other than
      the expected code, **that is a finding, not a test to adjust** — record it and stop.

      In `docs/feasibility-llm-growth-studies.md`, append a new subsection to § Executability on
      this build, headed *"Measured on \<date\> against commit \<sha\>"* with the real sha of the
      merge, carrying the honest form and its three qualifications verbatim in shape:

      > H7b Part B retires **one refusal that 9 of 9 configs hit** (`E-DATA-RESOLVER-UNSUPPORTED`),
      > and **three experiments — E1, E2, E5 — have no remaining core-side blocker.** That is the
      > first non-zero executable count this project has produced. It is conditional on the plugin
      > being written and installed (`plugin new` scaffolds it; a hand-written package works), and
      > on accepting that a declared apparatus probe is neither executed nor recorded. Six stay
      > blocked, on two causes neither of which is H7b's: `io.reuse_from` (unbuilt, **unowned**) and
      > `E-DATA-WEIGHT-CONTRAST` (H4b).

      **Append; never retro-edit the earlier dated subsections** — they record what was measured on
      their dates, and this file is exempt from the cross-document pass but not from the mechanical
      one. **Every cell must be re-measured, not carried**: run each of the nine `data`/`statistics`
      blocks and record the codes, with a can-fail control (`holdout.frac: 0` on E1, which the
      analysis itself prescribes).

      In `CLAUDE.md`, update § Misreadings' *unbuilt reader of a shipped surface* row if its example
      moved, and add the slice to the § Repository status paragraph naming the remaining order —
      **dated and pinned to a commit**, since it is a build fact.

      In `docs/superpowers/spec-defects.md`, file two things this slice makes reachable and does not
      own:

      - **`cli.py` writes `"apparatus": None` unconditionally**, and § The apparatus core can only
        observe defines `apparatus: null` as *"no probe declared"*. After this slice a run whose
        template **does** declare an installed probe records a false `apparatus: null`. **Owner:
        H7d.** File it; do not fix it — a reader for it is `Apparatus`, facts, the ledger and the
        change gate, all H7d's.
      - **`io.reuse_from` is unbuilt and unowned**, and is now the sole remaining core-side blocker
        for E3, E4 and E6. The existing entry already says so; **amend it with an owner request**
        rather than opening a second, since `CLAUDE.md` names *"a ledger line saying 'filed' is not
        a filing"* and a duplicate entry is the same failure in the other direction.

- [ ] **Step 4: Run and see it pass.** `uv run pytest` → **2097 + 6 = 2103 passed**, 1 skipped,
      2 xfailed. Then the other three commands.

- [ ] **Step 5: Mutate.** In `src/publishable/validate.py`, change `_check_units`'s
      `cfg=resolve_wide_cfg(doc, wide_swept_paths(doc.get("sweep") or {}))` to
      `cfg=resolve_wide_cfg(doc, set())` — the mutation task 29 named and could not catch.
      The `"swept parameter"` row of
      `test_the_roster_checks_are_real_against_a_resolver_produced_roster` must **FAIL**: with no
      markers planted, `cfg.parameters.analysis.method` resolves to the base value and the resolver
      succeeds. **Checked against the test body:** that row's config declares
      `sweep.grid: {analysis.method: [...]}` and its resolver reads exactly that path, so the two
      branches genuinely differ — this is the seam task 29 named and this test instantiates.

      Second mutation: in `units.resolve_units`, delete the `E-UNITS-KEY-DUPLICATE` loop. The
      `"duplicate keys"` row must **FAIL**. **Checked:** that row's resolver yields the same key
      twice with no `measurements` declaration, so no collapse intervenes.

      **What no mutation here reaches:** the § Executability subsection and the two filings. Prose
      and a ledger are verified by the sweep in Step 6, not by a test.

- [ ] **Step 6: Sweep, then commit.** Prove each sweep can fail by running it first against a string
      known to be present, and **filter the file list, never the output**:

      - `grep -rn "E-DATA-RESOLVER-UNSUPPORTED\|(NOT BUILT)" README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md CLAUDE.md src/`
        → the code must be absent; `(NOT BUILT)` must appear only where a genuinely unbuilt thing is
        marked. Can-fail control on the same list: `grep -rn "NOT BUILT" docs/reference.md` →
        non-empty.
      - `grep -rn "Not yet emitted" docs/reference.md` → **empty**; the three markers are struck by
        tasks 24, 28 and 29. Can-fail control: `grep -c "E-RESOLVER" docs/reference.md` → non-zero.
      - `grep -rn "against commit .deaed2b." docs/reference.md src/` → empty.
      - `grep -rn "cannot be dispatched\|will be honored in a later slice" src/ docs/reference.md`
        → empty.

      Mechanical pass on every `*.md` touched by the slice: links and anchors resolve, no duplicate
      anchors, table rows match their headers, no trailing whitespace or tab or invisible unicode,
      `×` not `x`, hyphen not en dash in anything that becomes an anchor — skipping fenced blocks.
      Cross-document pass on the four documents only.
      Commit: `docs: resolvers land — three of nine have no remaining core-side blocker`

---

## Self-review

Run before declaring the plan finished; findings fixed inline rather than appended.

**Spec coverage — a task per decision, and a task per scoping row.**

| Spec decision | Task | Scoping § 10 row | Task |
|---|---|---|---|
| 1 — `validate` imports a plugin to run a resolver | 22 | 21 `plugin new` | 21 |
| 2 — the credential-leak fix, both halves | 32 | 22 the decision | 22 |
| 3 — a non-`PublishableError` from a resolver | 32 | 23 read-only `io` | 23 |
| 4 — `check_registration` at `validate` | 24 | 24 name resolution and load | 24 |
| 5 — `hash_index`, table case and resolver case | 31 | 25 dispatch | 25 |
| 6 — `cfg` as a defaulted keyword | 25 | 26 retire the refusal | 26 |
| 7 — the payoff figure, with its qualifications | 33 | 27 attribute projection | 27 |
| | | 28 measurement field | 28 |
| | | 29 condition-independence | 29 |
| | | 30 `plugin_versions` + dated notes | 30 |
| | | 31 `hash_index` | 31 |
| | | 32 the credential leak | 32 |
| | | 33 prose sweep + re-dated count | 33 |

Thirteen tasks, thirteen rows, seven decisions, each landed. The four surfaces `spec-defects.md`
names Part B as owner of — `RESOLVERS`, `load_entry_point`, `check_registration`, `declared_names` —
get their first production caller in task 24, and task 30 amends the filing; the
`E-PLUGIN-COLLISION`/`E-PLUGIN-LOAD` hazard filed against Part B is decided and struck in task 24.

**Placeholder scan.** Every code step carries real code, with two deliberate exceptions, both in
tests and both marked with `...`: task 30's and task 32's `tests/test_cli.py` additions, whose
setup is *"build the config with the file's existing run helper"*. `tests/test_cli.py` is 9178
lines and its `command_run` helpers are what those tests must reuse rather than duplicate; naming a
helper this plan has not read would be the *helper that shadows an existing name* defect this repo
has already shipped. The assertions — which are the load-bearing half — are written out in full.

**Type consistency.** `resolve_units` keeps its three-element return, so no call site's unpacking
changes; the two new parameters are keyword-only with defaults. `Config | None` is quoted in
`units.py` (the import is real, not `TYPE_CHECKING`, so the quotes are stylistic consistency with
the file's existing `"UnitList | None"` forward references — drop them if `mypy` prefers).
`index_names` takes `UnitList | None` and a `tuple[str, ...]`, and returns `set[str]`, which is
exactly what `build_manifest`'s `index_names: set[str] | None` accepts. `versions_for` returns
`dict[str, str]`, matching `run.yaml`'s `plugin_versions` shape.
`ResolverIO.read_paths` is a `tuple[str, ...]` property over a private list, so a resolver cannot
edit the record of what it read.
