# Implementation Spine (S1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Put the first code in a specification-only repository, so that `publishable new` → `generate experiment` → `validate` → `run` produces a real `run.yaml` carrying three real hashes.

**Architecture:** A CLI dispatches to a ten-phase `run` pipeline. Phases 1–6 (locate, validate, gate, plan, pin, allocate) create nothing; phase 7 executes a plan of (condition, repeat, step) triples; phases 8–10 verify, assemble and write. Two error channels stay structurally separate: collected diagnostics before execution, raised `PublishableError`s during it.

**Tech Stack:** Python 3.11+, PyYAML (the only third-party runtime dependency), pytest, ruff, mypy, uv.

## Global Constraints

- Python `requires-python = ">=3.11"`.
- **PyYAML is the only third-party runtime dependency.** `pyarrow` arrives in S2, `numpy` in S4. Do not add either.
- Package version is `0.1.0`, matching `CITATION.cff`.
- `src/` layout. The import root is `publishable`; nothing outside `src/publishable/__init__.py` is public API.
- Every error and warning carries a stable identifier: `E-` for errors, `W-` for warnings.
- `ruff` for lint and format; `mypy` over `src/` only.
- **Coverage bar:** every `E-`/`W-` identifier defined must have a test that produces it.
- Multiplication in prose and comments uses `×`, never `x`.
- The four documents in `docs/` are normative. If code cannot follow them, stop and record it in `docs/superpowers/spec-defects.md` rather than diverging silently.

## File Structure

| File | Responsibility |
|---|---|
| `pyproject.toml` | Package metadata, entry point, ruff and mypy config |
| `src/publishable/__init__.py` | The one public import root |
| `src/publishable/errors.py` | `PublishableError` → `ContractError` / `ArtifactError` → `ArtifactExistsError` |
| `src/publishable/diagnostics.py` | `Diagnostic`, `Collector`, exit-code mapping |
| `src/publishable/param.py` | `Param`: type, default, closed constraint vocabulary, comment rendering |
| `src/publishable/config.py` | YAML load and the dot-access `Config` node |
| `src/publishable/templates/base.py` | `BaseTemplate` |
| `src/publishable/templates/builtin/generic.py` | `generic`'s four parameters |
| `src/publishable/templates/registry.py` | Name → template class lookup |
| `src/publishable/materialize.py` | `parameter_spec` → a commented `config.yaml` |
| `src/publishable/hashes.py` | `code_hash`, `parameters_hash`, `design_digest` |
| `src/publishable/provenance.py` | Git walk-up: repo root, commit, branch, remote, dirty state |
| `src/publishable/uv_support.py` | Locate and hash `uv.lock` |
| `src/publishable/manifest.py` | Input manifest build and verify |
| `src/publishable/base_step.py` | `BaseStep` |
| `src/publishable/base_experiment.py` | `BaseExperiment` |
| `src/publishable/scope.py` | `Execution`, `build_plan` |
| `src/publishable/replication.py` | `Repeat`, `resolve_repeats` — the `seed` kind |
| `src/publishable/artifacts.py` | `StepIO`: scope-aware paths, atomic write, writers |
| `src/publishable/run_identity.py` | Run ID allocation, `latest` pointer, the lock |
| `src/publishable/runner.py` | The execution loop |
| `src/publishable/run_record.py` | `run.yaml` assembly |
| `src/publishable/validate.py` | The S1 check subset |
| `src/publishable/scaffold.py` | `new` |
| `src/publishable/generators/experiment.py` · `step.py` | `generate experiment` · `generate step` |
| `src/publishable/readme_templates/` | Scaffolded README, CITATION.cff, LICENSE, .gitignore |
| `src/publishable/cli.py` | Argument dispatch and exit codes |

**Interface conventions every task relies on.** Hashes are returned as `"sha256:<hex>"` strings. Paths are always `pathlib.Path`. Anything user-facing that can fail before execution reports into a `Collector`; anything that can fail during execution raises from the `PublishableError` tree.

---

### Task 1: Project foundation and the error tree

**Files:**
- Create: `pyproject.toml`, `src/publishable/__init__.py`, `src/publishable/errors.py`, `tests/conftest.py`
- Test: `tests/test_errors.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `PublishableError(message, code)` with `.code: str`; subclasses `ContractError`, `ArtifactError`, `ArtifactExistsError` (subclass of `ArtifactError`).

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "publishable"
version = "0.1.0"
description = "Run experiments so the record is publishable by default"
requires-python = ">=3.11"
dependencies = ["pyyaml>=6.0"]

[project.scripts]
publishable = "publishable.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/publishable"]

[dependency-groups]
dev = ["pytest>=8.0", "ruff>=0.6", "mypy>=1.11"]

[tool.ruff]
line-length = 100
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.mypy]
files = ["src"]
python_version = "3.11"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = ["slow: exercises real uv or network"]
```

- [ ] **Step 2: Write the failing test**

```python
# tests/test_errors.py
import pytest
from publishable import ArtifactError, ArtifactExistsError, ContractError, PublishableError


def test_hierarchy_is_two_levels_with_one_leaf():
    assert issubclass(ContractError, PublishableError)
    assert issubclass(ArtifactError, PublishableError)
    assert issubclass(ArtifactExistsError, ArtifactError)
    assert not issubclass(ContractError, ArtifactError)


def test_every_error_carries_its_code():
    err = ContractError("bad path", code="E-STEP-PARAM-UNKNOWN")
    assert err.code == "E-STEP-PARAM-UNKNOWN"
    assert "bad path" in str(err)


def test_catching_the_base_catches_everything():
    with pytest.raises(PublishableError):
        raise ArtifactExistsError("already there", code="E-ARTIFACT-EXISTS")
```

- [ ] **Step 3: Run it and watch it fail**

Run: `uv run pytest tests/test_errors.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'publishable'`

- [ ] **Step 4: Implement `errors.py`**

```python
# src/publishable/errors.py
"""The exception tree core raises. See docs/reference.md § Errors core raises."""


class PublishableError(Exception):
    """Catch this to catch everything core raises."""

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


class ContractError(PublishableError):
    """Your code asked for, or handed back, something its declarations don't allow."""


class ArtifactError(PublishableError):
    """Core will not write this."""


class ArtifactExistsError(ArtifactError):
    """...because the target is already there."""
```

- [ ] **Step 5: Implement the import root**

```python
# src/publishable/__init__.py
"""The one public import root. Submodules are implementation detail."""

from publishable.errors import (
    ArtifactError,
    ArtifactExistsError,
    ContractError,
    PublishableError,
)

__all__ = [
    "ArtifactError",
    "ArtifactExistsError",
    "ContractError",
    "PublishableError",
]
__version__ = "0.1.0"
```

- [ ] **Step 6: Add the shared test fixture**

```python
# tests/conftest.py
import subprocess
from pathlib import Path

import pytest


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """A real git repo with one commit. Provenance is never mocked."""
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "placeholder.py").write_text("# placeholder\n")
    git("init", "-q", cwd=repo)
    git("config", "user.email", "test@example.com", cwd=repo)
    git("config", "user.name", "Test", cwd=repo)
    git("add", ".", cwd=repo)
    git("commit", "-qm", "initial", cwd=repo)
    return repo
```

- [ ] **Step 7: Run and verify green**

Run: `uv run pytest tests/test_errors.py -v && uv run ruff check . && uv run mypy`
Expected: 3 passed, no lint findings, no type errors.

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml src/ tests/
git commit -m "Give the specification a package to live in"
```

---

### Task 2: Diagnostics — collected findings and exit codes

**Files:**
- Create: `src/publishable/diagnostics.py`
- Test: `tests/test_diagnostics.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `Diagnostic(level, code, path, message)` frozen dataclass; `Collector` with `.error(code, path, message)`, `.warn(code, path, message)`, `.findings: list[Diagnostic]`, `.has_errors: bool`, `.render() -> str`; `EXIT_OK=0`, `EXIT_WRONG=1`, `EXIT_INVOCATION=2`, `EXIT_PARTIAL=3`, `EXIT_FAILED=4`, `EXIT_EXTERNAL=5`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_diagnostics.py
from publishable.diagnostics import EXIT_OK, EXIT_WRONG, Collector


def test_collector_accumulates_rather_than_stopping():
    c = Collector()
    c.error("E-PARAM-UNKNOWN", "parameters.analysis.min_sample", "did you mean min_samples?")
    c.error("E-META-REQUIRED", "metadata.description", "is empty")
    c.warn("W-STATS-FAMILY", "statistics.correction", "family of 15 with correction: none")
    assert len(c.findings) == 3
    assert c.has_errors


def test_a_warning_alone_is_not_an_error():
    c = Collector()
    c.warn("W-REPL-FLOOR", "replication.repeats", "below the class default")
    assert not c.has_errors
    assert c.exit_code() == EXIT_OK


def test_errors_set_exit_one():
    c = Collector()
    c.error("E-DATA-IN-REPO", "data.output_dir", "resolves inside the git repository")
    assert c.exit_code() == EXIT_WRONG


def test_render_puts_the_identifier_beside_the_finding():
    c = Collector()
    c.error("E-PARAM-UNKNOWN", "parameters.analysis.min_sample", "did you mean `min_samples`?")
    out = c.render()
    assert "E-PARAM-UNKNOWN" in out
    assert "parameters.analysis.min_sample" in out
    assert "1 problem (1 error, 0 warnings)" in out


def test_the_summary_line_matches_the_specs_own_example():
    """docs/reference.md § Exit codes and diagnostics ends with this exact line."""
    c = Collector()
    c.error("E-PARAM-UNKNOWN", "parameters.analysis.min_sample", "did you mean `min_samples`?")
    c.warn("W-STATS-FAMILY", "statistics.correction", "a family of 15 with `correction: none`")
    assert c.render().endswith("2 problems (1 error, 1 warning)")


def test_each_noun_pluralizes_on_its_own_count():
    c = Collector()
    c.error("E-A", "a", "one")
    c.error("E-B", "b", "two")
    assert c.render().endswith("2 problems (2 errors, 0 warnings)")
    assert Collector().render() == "0 problems (0 errors, 0 warnings)"
```

- [ ] **Step 2: Run it and watch it fail**

Run: `uv run pytest tests/test_diagnostics.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'publishable.diagnostics'`

- [ ] **Step 3: Implement `diagnostics.py`**

```python
# src/publishable/diagnostics.py
"""Collected findings. See docs/reference.md § Exit codes and diagnostics."""

from dataclasses import dataclass, field

EXIT_OK = 0
EXIT_WRONG = 1
EXIT_INVOCATION = 2
EXIT_PARTIAL = 3
EXIT_FAILED = 4
EXIT_EXTERNAL = 5


def _plural(count: int, noun: str) -> str:
    """`reference.md` § Exit codes and diagnostics renders `1 error, 1 warning`."""
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


@dataclass(frozen=True)
class Diagnostic:
    level: str  # "error" | "warning"
    code: str
    path: str
    message: str


@dataclass
class Collector:
    """`validate` collects rather than stops, so findings are appended, never raised."""

    findings: list[Diagnostic] = field(default_factory=list)

    def error(self, code: str, path: str, message: str) -> None:
        self.findings.append(Diagnostic("error", code, path, message))

    def warn(self, code: str, path: str, message: str) -> None:
        self.findings.append(Diagnostic("warning", code, path, message))

    @property
    def has_errors(self) -> bool:
        return any(f.level == "error" for f in self.findings)

    def exit_code(self) -> int:
        return EXIT_WRONG if self.has_errors else EXIT_OK

    def render(self) -> str:
        lines = []
        for f in self.findings:
            lines.append(f"  {f.level:<7} {f.code:<20} {f.path}")
            lines.append(f"          {f.message}")
        n_err = sum(1 for f in self.findings if f.level == "error")
        n_warn = len(self.findings) - n_err
        total = len(self.findings)
        lines.append(
            f"{_plural(total, 'problem')} "
            f"({_plural(n_err, 'error')}, {_plural(n_warn, 'warning')})"
        )
        return "\n".join(lines)
```

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest tests/test_diagnostics.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/publishable/diagnostics.py tests/test_diagnostics.py
git commit -m "Collect findings instead of stopping at the first"
```

---

### Task 3: `Param` and the closed constraint vocabulary

**Files:**
- Create: `src/publishable/param.py`
- Test: `tests/test_param.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `Param(type_, *, default=MISSING, choices=None, ge=None, gt=None, le=None, lt=None, pattern=None, item_type=None, min_items=None, max_items=None, nullable=False, help=None)`; `.required: bool`; `.check(value) -> str | None` returning an error message or `None`; `.comment() -> str` returning the inline comment text (possibly `""`); sentinel `MISSING`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_param.py
import pytest
from publishable.param import Param


def test_omitting_default_is_what_makes_a_parameter_required():
    assert Param(str).required
    assert not Param(str, default="pearson").required


def test_default_none_requires_nullable():
    with pytest.raises(ValueError, match="nullable"):
        Param(str, default=None)
    assert Param(str, default=None, nullable=True).default is None


def test_check_enforces_type_choices_and_ranges():
    assert Param(int, default=30, ge=2).check("30") is not None
    assert Param(int, default=30, ge=2).check(1) is not None
    assert Param(int, default=30, ge=2).check(30) is None
    method = Param(str, default="pearson", choices=["pearson", "spearman", "kendall"])
    assert method.check("pearsonn") is not None
    assert method.check("kendall") is None
    assert Param(float, default=0.95, gt=0, lt=1).check(1.4) is not None


def test_bool_is_not_an_int():
    assert Param(int, default=1).check(True) is not None


def test_list_is_checked_element_by_element():
    p = Param(list, item_type=float, default=[0.01, 0.03])
    assert p.check([0.1, 0.2]) is None
    assert p.check([0.1, "x"]) is not None


def test_comments_render_the_constraint_that_claims_them():
    assert Param(str, default="a", choices=["a", "b"]).comment() == "choices: a | b"
    assert Param(int, default=30, ge=2).comment() == "integer >= 2"
    assert Param(float, default=0.95, gt=0, lt=1).comment() == "float in (0, 1)"
    assert Param(bool, default=True, help="Drop missing rows").comment() == "Drop missing rows"
```

- [ ] **Step 2: Run it and watch it fail**

Run: `uv run pytest tests/test_param.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'publishable.param'`

- [ ] **Step 3: Implement `param.py`**

```python
# src/publishable/param.py
"""One parameter's type, default, constraints and help text.

The constraint vocabulary is closed on purpose: docs/reference.md § Templates.
"""

from typing import Any

MISSING = object()
_TYPE_NAMES = {str: "string", int: "integer", float: "float", bool: "bool", list: "list"}


class Param:
    def __init__(
        self,
        type_: type,
        *,
        default: Any = MISSING,
        choices: list[Any] | None = None,
        ge: float | None = None,
        gt: float | None = None,
        le: float | None = None,
        lt: float | None = None,
        pattern: str | None = None,
        item_type: type | None = None,
        min_items: int | None = None,
        max_items: int | None = None,
        nullable: bool = False,
        help: str | None = None,
    ) -> None:
        if type_ not in _TYPE_NAMES:
            raise ValueError(f"unsupported Param type {type_!r}")
        if default is None and not nullable:
            raise ValueError("default=None requires nullable=True")
        if pattern is not None and type_ is not str:
            # § Templates types `pattern` to `str`. Refusing the combination at
            # construction is what keeps `check` unable to raise on a mistyped value.
            raise ValueError(f"pattern applies to str, not {_TYPE_NAMES[type_]}")
        self.type_ = type_
        self.default = default
        self.choices = choices
        self.ge, self.gt, self.le, self.lt = ge, gt, le, lt
        self.pattern = pattern
        self.item_type = item_type
        self.min_items, self.max_items = min_items, max_items
        self.nullable = nullable
        self.help = help

    @property
    def required(self) -> bool:
        return self.default is MISSING

    def check(self, value: Any) -> str | None:
        """Return an error message, or None when the value is legal."""
        import re

        if value is None:
            return None if self.nullable else "is null, but the parameter is not nullable"
        if not self._is_type(value, self.type_):
            return f"is {value!r}, expected {_TYPE_NAMES[self.type_]}"
        if self.choices is not None and value not in self.choices:
            joined = ", ".join(str(c) for c in self.choices)
            return f"is {value!r}, expected one of {joined}"
        for bound, op, sym in (
            (self.ge, lambda v, b: v >= b, ">="),
            (self.gt, lambda v, b: v > b, ">"),
            (self.le, lambda v, b: v <= b, "<="),
            (self.lt, lambda v, b: v < b, "<"),
        ):
            if bound is not None and not op(value, bound):
                return f"is {value!r}, expected {sym} {bound}"
        if self.pattern is not None and isinstance(value, str):
            if not re.match(self.pattern, value):
                return f"is {value!r}, expected to match {self.pattern}"
        if self.type_ is list:
            return self._check_list(value)
        return None

    def _check_list(self, value: list[Any]) -> str | None:
        if self.item_type is not None:
            for i, item in enumerate(value):
                if not self._is_type(item, self.item_type):
                    return f"[{i}] is {item!r}, expected {_TYPE_NAMES[self.item_type]}"
        if self.min_items is not None and len(value) < self.min_items:
            return f"has {len(value)} items, expected at least {self.min_items}"
        if self.max_items is not None and len(value) > self.max_items:
            return f"has {len(value)} items, expected at most {self.max_items}"
        return None

    @staticmethod
    def _is_type(value: Any, expected: type) -> bool:
        if expected is bool:
            return isinstance(value, bool)
        if isinstance(value, bool):
            return False  # a bool is not an int here
        if expected is float:
            return isinstance(value, (int, float))
        return isinstance(value, expected)

    def comment(self) -> str:
        """The inline comment `init` renders. One constraint claims it, else `help`."""
        if self.choices is not None:
            return "choices: " + " | ".join(str(c) for c in self.choices)
        if self.gt is not None and self.lt is not None:
            return f"float in ({self.gt}, {self.lt})"
        for bound, sym in ((self.ge, ">="), (self.gt, ">"), (self.le, "<="), (self.lt, "<")):
            if bound is not None:
                return f"{_TYPE_NAMES[self.type_]} {sym} {bound}"
        if self.pattern is not None:
            return f"matches {self.pattern}"
        if self.type_ is list and self.item_type is not None:
            return f"list of {_TYPE_NAMES[self.item_type]}"
        return self.help or ""
```

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest tests/test_param.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add src/publishable/param.py tests/test_param.py
git commit -m "Make parameter_spec the single source of truth it claims to be"
```

---

### Task 4: `Config` — dot-access with nothing to shadow

**Files:**
- Create: `src/publishable/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: `ContractError`.
- Produces: `load_config(path: Path) -> Config`; `Config` with `.raw: dict`, dot access returning `Node`/list/scalar, `Node` with no public methods.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
import pytest
from publishable import ContractError
from publishable.config import Config


def cfg() -> Config:
    return Config({
        "parameters": {"analysis": {"method": "pearson", "min_samples": 30}},
        "metadata": {"name": "cohort-pilot"},
        "sweep": {"grid": {"analysis.method": ["spearman"]}},
    })


def test_dot_access_walks_nested_mappings():
    assert cfg().parameters.analysis.method == "pearson"
    assert cfg().parameters.analysis.min_samples == 30


def test_a_path_the_config_does_not_hold_raises_with_the_nearest_key():
    with pytest.raises(ContractError) as e:
        _ = cfg().parameters.analysis.min_sample
    assert "parameters.analysis.min_sample" in str(e.value)
    assert "min_samples" in str(e.value)
    assert e.value.code == "E-STEP-PARAM-UNKNOWN"


def test_underscore_names_raise_attribute_error_so_protocols_keep_working():
    c = cfg()
    with pytest.raises(AttributeError):
        _ = c.parameters._ipython_canary
    assert not hasattr(c.parameters, "_repr_html_")


def test_a_node_has_no_methods_to_shadow_a_parameter_name():
    node = Config({"parameters": {"items": 3, "values": 4, "keys": 5}}).parameters
    assert node.items == 3
    assert node.values == 4
    assert node.keys == 5
```

- [ ] **Step 2: Run it and watch it fail**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'publishable.config'`

- [ ] **Step 3: Implement `config.py`**

```python
# src/publishable/config.py
"""The only module that parses YAML. See docs/reference.md § The importable surface."""

import difflib
from pathlib import Path
from typing import Any

import yaml

from publishable.errors import ContractError


def _wrap(value: Any, path: str) -> Any:
    if isinstance(value, dict):
        return Node(value, path)
    if isinstance(value, list):
        return [_wrap(v, f"{path}[{i}]") for i, v in enumerate(value)]
    return value


class Node:
    """Dot-access and nothing else, so no parameter name can be shadowed."""

    def __init__(self, data: dict[str, Any], path: str = "") -> None:
        object.__setattr__(self, "_data", data)
        object.__setattr__(self, "_path", path)

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        data: dict[str, Any] = object.__getattribute__(self, "_data")
        base: str = object.__getattribute__(self, "_path")
        full = f"{base}.{name}" if base else name
        if name not in data:
            near = difflib.get_close_matches(name, list(data), n=1)
            hint = f" — did you mean `{near[0]}`?" if near else ""
            raise ContractError(
                f"{full} is not a path this config holds{hint}", code="E-STEP-PARAM-UNKNOWN"
            )
        return _wrap(data[name], full)


class Config(Node):
    def __init__(self, data: dict[str, Any]) -> None:
        super().__init__(data, "")

    @property
    def raw(self) -> dict[str, Any]:
        return dict(object.__getattribute__(self, "_data"))


def load_config(path: Path) -> Config:
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise ContractError(f"{path} does not parse as a mapping", code="E-CONFIG-PARSE")
    return Config(data)
```

Note: `Config.raw` is a property, which `Node.__getattr__` never sees because `__getattr__` runs only when normal lookup fails. A config key literally named `raw` would be shadowed; that is a known limitation to record in the defect ledger, not to fix here.

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest tests/test_config.py -v`
Expected: 4 passed.

- [ ] **Step 5: Record the `raw` shadowing in the ledger**

```bash
mkdir -p docs/superpowers
cat >> docs/superpowers/spec-defects.md <<'EOF'

## `Config.raw` shadows a config key named `raw`

`reference.md` § The importable surface says a `cfg` node has "no method of any kind",
which is what makes a parameter named `items` or `values` safe. The implementation needs
some way to reach the underlying mapping for hashing and embedding. `Config.raw` is a
property on the root only, so `cfg.raw` would shadow a top-level key named `raw` — core
owns the envelope's top level, so no user key can collide today, but the rule as written
admits no exception at all. Proposed resolution: state in § The importable surface that
the root object carries one accessor and nested nodes carry none.
EOF
```

- [ ] **Step 6: Commit**

```bash
git add src/publishable/config.py tests/test_config.py
git commit -m "Give cfg dot-access and nothing a parameter could shadow"
```

---

### Task 5: `BaseTemplate`, `generic`, and the registry

**Files:**
- Create: `src/publishable/templates/__init__.py`, `src/publishable/templates/base.py`, `src/publishable/templates/builtin/__init__.py`, `src/publishable/templates/builtin/generic.py`, `src/publishable/templates/registry.py`
- Modify: `src/publishable/__init__.py`
- Test: `tests/test_templates.py`

**Interfaces:**
- Consumes: `Param`, `Config`.
- Produces: `BaseTemplate` with class attributes `naming_pattern: str`, `field_convention: str`, `default_repeats: int`, `required_env: list[str]`, `apparatus_probe: str | None`, `apparatus_facts: list[str]`, `parameter_spec: dict[str, Param]`, and `validate(self, config) -> list[str]`; `get_template(name: str) -> BaseTemplate`; `KnownTemplateError` is not introduced — an unknown name returns `None`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_templates.py
from publishable import BaseTemplate, Param
from publishable.templates.registry import get_template


def test_generic_is_registered_and_declares_its_conventions():
    t = get_template("generic")
    assert isinstance(t, BaseTemplate)
    assert t.field_convention == "generic"
    assert t.default_repeats == 1
    assert t.required_env == []
    assert t.apparatus_probe is None


def test_generic_declares_exactly_its_four_parameters():
    spec = get_template("generic").parameter_spec
    assert list(spec) == [
        "analysis.method",
        "analysis.min_samples",
        "analysis.confidence",
        "analysis.drop_missing",
    ]
    assert spec["analysis.method"].choices == ["pearson", "spearman", "kendall"]
    assert spec["analysis.min_samples"].ge == 2


def test_an_unknown_template_is_not_resolved():
    assert get_template("llm_diagnostic") is None


def test_validate_defaults_to_no_cross_field_rules():
    class Bare(BaseTemplate):
        parameter_spec: dict[str, Param] = {}

    assert Bare().validate(None) == []
```

- [ ] **Step 2: Run it and watch it fail**

Run: `uv run pytest tests/test_templates.py -v`
Expected: FAIL — `ImportError: cannot import name 'BaseTemplate'`

- [ ] **Step 3: Implement `templates/base.py`**

```python
# src/publishable/templates/base.py
"""An experiment type's parameters. See docs/reference.md § Templates."""

from typing import Any

from publishable.param import Param


class BaseTemplate:
    naming_pattern: str = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    field_convention: str = "generic"
    default_repeats: int = 1
    required_env: list[str] = []
    apparatus_probe: str | None = None
    apparatus_facts: list[str] = []
    parameter_spec: dict[str, Param] = {}

    def validate(self, config: Any) -> list[str]:
        """Cross-field rules. Receives the WHOLE config; [] when OK."""
        return []
```

`aggregate` is deliberately absent — a template either defines it or doesn't, and that absence is readable (S4 relies on it).

- [ ] **Step 4: Implement `generic` and the registry**

```python
# src/publishable/templates/builtin/generic.py
from publishable.param import Param
from publishable.templates.base import BaseTemplate


class GenericTemplate(BaseTemplate):
    naming_pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    field_convention = "generic"
    default_repeats = 1
    required_env: list[str] = []
    apparatus_probe = None
    apparatus_facts: list[str] = []

    parameter_spec = {
        "analysis.method": Param(
            str, default="pearson", choices=["pearson", "spearman", "kendall"]
        ),
        "analysis.min_samples": Param(int, default=30, ge=2),
        "analysis.confidence": Param(float, default=0.95, gt=0, lt=1),
        "analysis.drop_missing": Param(
            bool, default=True, help="Drop rows with any missing value before analysis"
        ),
    }
```

```python
# src/publishable/templates/registry.py
"""Name → template. S1 knows only core's own; plugins arrive in hardening."""

from publishable.templates.base import BaseTemplate
from publishable.templates.builtin.generic import GenericTemplate

_BUILTIN: dict[str, type[BaseTemplate]] = {"generic": GenericTemplate}


def get_template(name: str) -> BaseTemplate | None:
    cls = _BUILTIN.get(name)
    return cls() if cls else None


def template_names() -> list[str]:
    return sorted(_BUILTIN)
```

Both `templates/__init__.py` and `templates/builtin/__init__.py` are empty files.

- [ ] **Step 5: Export from the import root**

Add to `src/publishable/__init__.py`, keeping `__all__` sorted:

```python
from publishable.param import Param
from publishable.templates.base import BaseTemplate
```

with `"BaseTemplate"` and `"Param"` added to `__all__`.

- [ ] **Step 6: Run and verify green**

Run: `uv run pytest tests/test_templates.py -v && uv run mypy`
Expected: 4 passed, no type errors.

- [ ] **Step 7: Commit**

```bash
git add src/publishable/templates src/publishable/__init__.py tests/test_templates.py
git commit -m "Ship the one template core is allowed to ship"
```

---

### Task 6: `materialize` — the fully-populated, commented config

**Files:**
- Create: `src/publishable/materialize.py`
- Test: `tests/test_materialize.py`

**Interfaces:**
- Consumes: `BaseTemplate`, `Param`.
- Produces: `materialize_config(template, template_name, name, input_dir, output_dir, entrypoint) -> str` returning YAML text.

**S1 scoping decision, recorded in the ledger by this task:** the materialized `data` block **omits `data.units`**, because unit resolution is S2. `reference.md` § The one config file shows it populated. S2 restores it.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_materialize.py
import yaml
from publishable.materialize import materialize_config
from publishable.templates.registry import get_template


def rendered() -> str:
    return materialize_config(
        template=get_template("generic"),
        template_name="generic",
        name="cohort-pilot",
        input_dir="/secure/data/cohort-2026",
        output_dir="/secure/results/cohort-pilot",
        entrypoint="cohort_pilot.experiment:CohortPilotExperiment",
    )


def test_every_parameter_is_materialized_with_its_default():
    doc = yaml.safe_load(rendered())
    assert doc["parameters"]["analysis"] == {
        "method": "pearson",
        "min_samples": 30,
        "confidence": 0.95,
        "drop_missing": True,
    }


def test_the_four_identifying_fields_are_present():
    doc = yaml.safe_load(rendered())
    assert doc["schema_version"] == "1.0"
    assert doc["experiment_type"] == "generic"
    assert doc["template_version"] == "1.0.0"
    assert doc["plugin"] is None


def test_constraints_arrive_as_inline_comments():
    text = rendered()
    assert "# choices: pearson | spearman | kendall" in text
    assert "# integer >= 2" in text
    assert "# float in (0, 1)" in text


def test_limits_carry_the_documented_defaults():
    doc = yaml.safe_load(rendered())
    assert doc["limits"] == {
        "max_executions": 500,
        "max_failed_fraction": 0.2,
        "max_ineligible_fraction": 0.5,
        "min_units_per_cell": 20,
        "min_clusters": 10,
        "min_reported_n": 10,
    }


def test_s1_omits_the_units_block_because_resolution_is_s2():
    doc = yaml.safe_load(rendered())
    assert "units" not in doc["data"]
    assert doc["data"]["input_manifest_policy"] == "hash_all"


def test_replication_defaults_to_five_seed_repeats():
    doc = yaml.safe_load(rendered())
    assert doc["replication"]["repeats"] == [{"kind": "seed", "n": 5}]
    assert doc["replication"]["order"] == "as_declared"
```

- [ ] **Step 2: Run it and watch it fail**

Run: `uv run pytest tests/test_materialize.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'publishable.materialize'`

- [ ] **Step 3: Implement `materialize.py`**

```python
# src/publishable/materialize.py
"""parameter_spec → the one config file. docs/reference.md § The one config file."""

from typing import Any

from publishable.param import MISSING, Param
from publishable.templates.base import BaseTemplate

TEMPLATE_VERSION = "1.0.0"
INIT_REPEATS = 5  # what `init` writes; `default_repeats` is the warning floor


def _scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return value
    return repr(value)


def _parameters_block(spec: dict[str, Param]) -> list[str]:
    """Render dotted paths as nested YAML with each Param's comment."""
    tree: dict[str, Any] = {}
    for path, param in spec.items():
        head, _, leaf = path.rpartition(".")
        tree.setdefault(head, {})[leaf] = param
    lines: list[str] = []
    for head, leaves in tree.items():
        lines.append(f"  {head}:")
        for leaf, param in leaves.items():
            value = "" if param.default is MISSING else _scalar(param.default)
            entry = f"    {leaf}: {value}"
            comment = param.comment()
            if comment:
                pad = " " * max(1, 36 - len(entry))
                entry = f"{entry}{pad}# {comment}"
            lines.append(entry)
    return lines


def materialize_config(
    *,
    template: BaseTemplate,
    template_name: str,
    name: str,
    input_dir: str,
    output_dir: str,
    entrypoint: str,
) -> str:
    body = [
        f"# configs/{name}/config.yaml",
        f"# Generated by `publishable init` from template `{template_name}` "
        f"v{TEMPLATE_VERSION}.",
        "# This file is the complete parameter set. Edit it, validate it, run it.",
        "",
        'schema_version: "1.0"',
        f"experiment_type: {template_name}",
        f'template_version: "{TEMPLATE_VERSION}"',
        "plugin: null",
        "",
        "metadata:",
        f"  name: {name}",
        '  description: ""                  # REQUIRED — one line, what this run is for',
        "  authors: []                      # REQUIRED",
        '  institution: ""',
        "",
        f'entrypoint: "{entrypoint}"',
        "",
        "data:",
        f"  input_dir: {input_dir}          # must be OUTSIDE the repo — enforced",
        f"  output_dir: {output_dir}",
        "  input_manifest_policy: hash_all  # hash_all | hash_index | none",
        "",
        "parameters:",
        "  # ---- Base values. Everything below is defined by the template, not by core. ----",
        *_parameters_block(template.parameter_spec),
        "",
        "replication:",
        "  repeats:",
        f"    - {{kind: seed, n: {INIT_REPEATS}}}          # seed | batch | fold",
        "  order: as_declared               # as_declared | randomized",
        '  rationale: ""',
        "",
        "statistics:",
        "  correction: holm                 # none | bonferroni | holm | fdr_bh",
        "",
        "limits:",
        "  max_executions: 500",
        "  max_failed_fraction: 0.2",
        "  max_ineligible_fraction: 0.5",
        "  min_units_per_cell: 20",
        "  min_clusters: 10",
        "  min_reported_n: 10",
        "",
        "hypotheses: []",
        "",
    ]
    return "\n".join(body)
```

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest tests/test_materialize.py -v`
Expected: 6 passed.

- [ ] **Step 5: Record two ledger entries**

```bash
cat >> docs/superpowers/spec-defects.md <<'EOF'

## What `init` writes into `replication.repeats` is underspecified

§ The one config file shows `init --template generic` producing
`repeats: - {kind: seed, n: 5}`, while § Naming conventions & repeat defaults gives
`generic` a `default_repeats` of 1 and § Templates shows `default_repeats = 1` on
`GenericTemplate`. Both are satisfiable at once only if `default_repeats` is a warning
floor rather than the materialized value — but the table's column header reads "Default
repeats", which invites the other reading. S1 implements the floor reading and writes 5.
Proposed resolution: rename the column to "Repeat floor", or state in § Naming
conventions that `init` writes a starter value independent of the floor.

## S1 omits `data.units` from the materialized config

Unit resolution is S2, so `materialize_config` writes no `data.units` block, which
§ The one config file shows populated and § The starter step runs depends on. Not a spec
defect — a slice boundary. Removed from this ledger when S2 lands.
EOF
```

- [ ] **Step 6: Commit**

```bash
git add src/publishable/materialize.py tests/test_materialize.py docs/superpowers/
git commit -m "Write the config so nobody has to author one"
```

---

### Task 7: The three hashes

**Files:**
- Create: `src/publishable/hashes.py`
- Test: `tests/test_hashes.py`

**Interfaces:**
- Consumes: nothing (pure — resolved paths and plain dicts in, strings out).
- Produces: `code_hash(repo_root: Path) -> str`; `parameters_hash(config: dict) -> str`; `design_digest(config: dict) -> str`; `short(hash_str: str) -> str` returning the first 7 hex characters.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_hashes.py
from pathlib import Path

from publishable.hashes import code_hash, design_digest, parameters_hash, short


def write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def test_code_hash_covers_src_and_templates_only(tmp_path: Path):
    write(tmp_path, "src/pkg/step.py", "a = 1\n")
    write(tmp_path, "templates/mine.py", "b = 2\n")
    before = code_hash(tmp_path)
    write(tmp_path, "docs/notes.md", "unrelated\n")
    write(tmp_path, "configs/c/config.yaml", "x: 1\n")
    assert code_hash(tmp_path) == before, "changes outside the two trees must not move it"
    write(tmp_path, "src/pkg/step.py", "a = 2\n")
    assert code_hash(tmp_path) != before


def test_code_hash_ignores_pycache(tmp_path: Path):
    write(tmp_path, "src/pkg/step.py", "a = 1\n")
    before = code_hash(tmp_path)
    write(tmp_path, "src/pkg/__pycache__/step.cpython-311.pyc", "junk")
    assert code_hash(tmp_path) == before


def test_code_hash_is_prefixed_and_short_takes_seven(tmp_path: Path):
    write(tmp_path, "src/pkg/step.py", "a = 1\n")
    h = code_hash(tmp_path)
    assert h.startswith("sha256:")
    assert len(short(h)) == 7


def test_parameters_hash_excludes_metadata_and_the_two_paths():
    base = {
        "experiment_type": "generic",
        "metadata": {"name": "a", "description": "one"},
        "data": {"input_dir": "/x", "output_dir": "/y", "input_manifest_policy": "hash_all"},
        "parameters": {"analysis": {"method": "pearson"}},
    }
    retitled = {**base, "metadata": {"name": "b", "description": "two"}}
    moved = {**base, "data": {**base["data"], "input_dir": "/elsewhere"}}
    changed = {**base, "parameters": {"analysis": {"method": "spearman"}}}
    assert parameters_hash(base) == parameters_hash(retitled)
    assert parameters_hash(base) == parameters_hash(moved)
    assert parameters_hash(base) != parameters_hash(changed)
    policy = {**base, "data": {**base["data"], "input_manifest_policy": "none"}}
    assert parameters_hash(base) != parameters_hash(policy), "policy is inside the hash"


def test_parameters_hash_is_insensitive_to_key_order():
    a = {"parameters": {"x": 1, "y": 2}, "limits": {"max_executions": 500}}
    b = {"limits": {"max_executions": 500}, "parameters": {"y": 2, "x": 1}}
    assert parameters_hash(a) == parameters_hash(b)


def test_design_digest_covers_units_and_groups_only():
    base = {
        "data": {"units": {"key": "patient_id"}},
        "sweep": {"groups": [], "grid": {"analysis.method": ["spearman"]}},
        "parameters": {"analysis": {"min_samples": 30}},
    }
    edited = {**base, "parameters": {"analysis": {"min_samples": 50}}}
    assert design_digest(base) == design_digest(edited), "editing a parameter must not redraw"
    roster = {**base, "data": {"units": {"key": "sample_id"}}}
    assert design_digest(base) != design_digest(roster)
```

- [ ] **Step 2: Run it and watch it fail**

Run: `uv run pytest tests/test_hashes.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'publishable.hashes'`

- [ ] **Step 3: Implement `hashes.py`**

```python
# src/publishable/hashes.py
"""The three hashes. See docs/reference.md § How the three are computed."""

import hashlib
import json
from pathlib import Path
from typing import Any

HASHED_TREES = ("src", "templates")
_SKIP_DIRS = {"__pycache__", ".git", ".ruff_cache", ".mypy_cache", ".pytest_cache"}
_SKIP_SUFFIXES = {".pyc", ".pyo"}


def _prefixed(digest: str) -> str:
    return f"sha256:{digest}"


def short(hash_str: str) -> str:
    return hash_str.split(":", 1)[-1][:7]


def hashed_files(repo_root: Path) -> list[tuple[str, Path]]:
    """Sorted (repo-relative path, file) pairs across src/** and templates/**."""
    found: list[tuple[str, Path]] = []
    for tree in HASHED_TREES:
        base = repo_root / tree
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(repo_root)
            # Match the skip-list against the path INSIDE the hashed tree. Matching
            # `path.parts` would test every component above repo_root too, so a repo
            # checked out under a directory named `__pycache__` would hash nothing
            # and return the empty-tree digest — a hash that certifies nothing.
            if any(part in _SKIP_DIRS for part in rel.parts):
                continue
            if path.suffix in _SKIP_SUFFIXES:
                continue
            found.append((rel.as_posix(), path))
    return sorted(found)


def code_hash(repo_root: Path) -> str:
    """sha256 over the sorted list of (relative path, sha256 of contents) pairs.

    Read from the working tree, not from git, so `run` and `draft` compute the
    same function over a clean and a dirty tree alike.
    """
    outer = hashlib.sha256()
    for rel, path in hashed_files(repo_root):
        inner = hashlib.sha256(path.read_bytes()).hexdigest()
        outer.update(rel.encode())
        outer.update(b"\0")
        outer.update(inner.encode())
        outer.update(b"\n")
    return _prefixed(outer.hexdigest())


def _canonical(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def parameters_hash(config: dict[str, Any]) -> str:
    """Everything in the config except `metadata` and the two host paths."""
    covered = {k: v for k, v in config.items() if k != "metadata"}
    data = covered.get("data")
    if isinstance(data, dict):
        covered["data"] = {
            k: v for k, v in data.items() if k not in ("input_dir", "output_dir")
        }
    return _prefixed(hashlib.sha256(_canonical(covered)).hexdigest())


def design_digest(config: dict[str, Any]) -> str:
    """`data.units` and `sweep.groups` only, so a parameter edit redraws nothing."""
    units = (config.get("data") or {}).get("units")
    groups = (config.get("sweep") or {}).get("groups")
    return _prefixed(
        hashlib.sha256(_canonical({"units": units, "groups": groups})).hexdigest()
    )
```

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest tests/test_hashes.py -v`
Expected: 6 passed.

- [ ] **Step 5: Record two deliberate divergences from the specification**

Both are narrow in S1 and both are real. Neither is fixed here — `hashes.py` is pure by
design, and closing either requires reaching outside it.

```bash
cat >> docs/superpowers/spec-defects.md <<'EOF'

## `code_hash` is not `.gitignore`-aware (S1 deviation, not a spec defect)

§ How the three are computed says `code_hash` is taken from the working tree "skipping
whatever `.gitignore` skips". S1 skips a fixed set instead — `__pycache__`, `.pyc`/`.pyo`,
and the tool cache directories — because honouring `.gitignore` means asking git, and this
plan makes `hashes.py` pure so it can be tested without a repository. In practice nothing
else gitignored appears under `src/**` or `templates/**`, so the two agree today. Closing
it properly means passing an `is_ignored` predicate in from the caller, which already
shells to git. Do that in hardening, or relax the purity rule and say so.

## `parameters_hash` does not normalize to what `init` would have materialized

§ How the three are computed says values are "normalized to what `init` would have
materialized before hashing — an omitted `cluster_by` and an explicit `cluster_by: null`
are the same declaration". S1 hashes the config as written, so a hand-trimmed config and
the file `init` wrote hash differently even when they declare the same run. Normalizing
requires the template's `parameter_spec`, which `parameters_hash` deliberately does not
take. Every config in S1 comes straight from `init`, so nothing hits this yet. Resolution:
either give `parameters_hash` the spec, or state in § How the three are computed that
normalization is the caller's job and name the caller.
EOF
```

- [ ] **Step 6: Commit**

```bash
git add src/publishable/hashes.py tests/test_hashes.py docs/superpowers/
git commit -m "Split code from parameters so one variable can be proven"
```

---

### Task 8: Git and uv provenance

**Files:**
- Create: `src/publishable/provenance.py`, `src/publishable/uv_support.py`
- Test: `tests/test_provenance.py`

**Interfaces:**
- Consumes: `hashed_files`.
- Produces: `find_repo_root(start: Path) -> Path` raising `ContractError` code `E-GIT-NO-REPO`; `GitInfo` frozen dataclass with `repo_root: Path`, `commit: str`, `branch: str`, `remote: str | None`, `code_dirty: bool`, `config_committed: bool`; `git_provenance(start: Path, config_path: Path) -> GitInfo`; `uv_lock_info(repo_root: Path) -> tuple[Path | None, str | None]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_provenance.py
from pathlib import Path

import pytest
from publishable import ContractError
from publishable.provenance import find_repo_root, git_provenance
from publishable.uv_support import uv_lock_info
from tests.conftest import git


def test_walk_up_starts_at_the_path_given_not_the_cwd(git_repo: Path):
    nested = git_repo / "configs" / "cohort-pilot"
    nested.mkdir(parents=True)
    (nested / "config.yaml").write_text("x: 1\n")
    assert find_repo_root(nested / "config.yaml") == git_repo


def test_no_repo_is_an_error_naming_where_it_looked(tmp_path: Path):
    with pytest.raises(ContractError) as e:
        find_repo_root(tmp_path / "nowhere.yaml")
    assert e.value.code == "E-GIT-NO-REPO"
    assert str(tmp_path) in str(e.value)


def test_a_clean_tree_is_not_dirty(git_repo: Path):
    info = git_provenance(git_repo, git_repo / "configs" / "c.yaml")
    assert info.code_dirty is False
    assert len(info.commit) == 40
    assert info.branch


def test_only_the_hashed_trees_make_it_dirty(git_repo: Path):
    (git_repo / "docs").mkdir()
    (git_repo / "docs" / "notes.md").write_text("untracked\n")
    assert git_provenance(git_repo, git_repo / "c.yaml").code_dirty is False
    (git_repo / "src" / "placeholder.py").write_text("changed\n")
    assert git_provenance(git_repo, git_repo / "c.yaml").code_dirty is True


def test_config_committed_is_recorded_not_required(git_repo: Path):
    cfg = git_repo / "configs" / "c.yaml"
    cfg.parent.mkdir()
    cfg.write_text("x: 1\n")
    assert git_provenance(git_repo, cfg).config_committed is False
    git("add", "configs", cwd=git_repo)
    git("commit", "-qm", "add config", cwd=git_repo)
    assert git_provenance(git_repo, cfg).config_committed is True


def test_a_missing_lockfile_is_reported_as_absent(git_repo: Path):
    assert uv_lock_info(git_repo) == (None, None)


def test_a_present_lockfile_is_hashed(git_repo: Path):
    (git_repo / "uv.lock").write_text("version = 1\n")
    path, digest = uv_lock_info(git_repo)
    assert path == git_repo / "uv.lock"
    assert digest is not None and digest.startswith("sha256:")
```

- [ ] **Step 2: Run it and watch it fail**

Run: `uv run pytest tests/test_provenance.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'publishable.provenance'`

- [ ] **Step 3: Implement `provenance.py`**

```python
# src/publishable/provenance.py
"""Whose git hash is this? Always the experiment repo's.

See docs/design-principles.md § Whose git hash is this?
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path

from publishable.errors import ContractError
from publishable.hashes import HASHED_TREES


@dataclass(frozen=True)
class GitInfo:
    repo_root: Path
    commit: str
    branch: str
    remote: str | None
    code_dirty: bool
    config_committed: bool


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=False
    )
    return result.stdout.strip()


def find_repo_root(start: Path) -> Path:
    """Walk up from the path the command was given, never from the cwd."""
    current = start.resolve()
    if not current.is_dir():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    raise ContractError(
        f"no git repository found from {current} upwards", code="E-GIT-NO-REPO"
    )


def git_provenance(start: Path, config_path: Path) -> GitInfo:
    repo = find_repo_root(start)
    dirty = bool(_git(repo, "status", "--porcelain", "--", *HASHED_TREES))
    tracked = _git(repo, "ls-files", "--error-unmatch", str(config_path))
    # `_git` swallows failure by design, which is right for `config_committed` —
    # empty means "not tracked", the fact we want. It is wrong here: a repo with no
    # commits would record `commit: ""`, a provenance claim that certifies nothing.
    # `--verify` matters: bare `rev-parse HEAD` on a commit-less repo exits 128 but
    # still prints the literal string "HEAD" to stdout, which is truthy and would
    # sail past this check straight into the record. `--verify` prints nothing.
    commit = _git(repo, "rev-parse", "--verify", "HEAD")
    if not commit:
        raise ContractError(
            f"{repo} has no commits yet, so there is no code state to record",
            code="E-GIT-NO-COMMIT",
        )
    return GitInfo(
        repo_root=repo,
        commit=commit,
        branch=_git(repo, "rev-parse", "--abbrev-ref", "HEAD"),
        remote=_git(repo, "remote", "get-url", "origin") or None,
        code_dirty=dirty,
        config_committed=bool(tracked),
    )
```

- [ ] **Step 4: Implement `uv_support.py`**

```python
# src/publishable/uv_support.py
"""uv is not optional. S1 hashes the lockfile; syncing arrives with `reproduce`."""

import hashlib
from pathlib import Path


def uv_lock_info(repo_root: Path) -> tuple[Path | None, str | None]:
    lock = repo_root / "uv.lock"
    if not lock.is_file():
        return None, None
    return lock, "sha256:" + hashlib.sha256(lock.read_bytes()).hexdigest()
```

- [ ] **Step 5: Run and verify green**

Run: `uv run pytest tests/test_provenance.py -v`
Expected: 7 passed.

- [ ] **Step 6: Commit**

```bash
git add src/publishable/provenance.py src/publishable/uv_support.py tests/test_provenance.py
git commit -m "Record the experiment repo's commit, never publishable's"
```

---

### Task 9: The input manifest

**Files:**
- Create: `src/publishable/manifest.py`
- Test: `tests/test_manifest.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `build_manifest(input_dir: Path, policy: str, index_names: set[str] | None = None) -> dict` — `index_names` is unused until `hash_index` matters in S2, and callers omit it; `manifest_hash(manifest: dict) -> str`; `verify_manifest(input_dir: Path, manifest: dict) -> list[str]` returning relative paths that changed (empty when clean).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_manifest.py
from pathlib import Path

import pytest
from publishable.manifest import build_manifest, manifest_hash, verify_manifest


@pytest.fixture
def input_dir(tmp_path: Path) -> Path:
    d = tmp_path / "input"
    (d / "sub").mkdir(parents=True)
    (d / "index.csv").write_text("patient_id\np1\np2\n")
    (d / "sub" / "scan.bin").write_bytes(b"\x00\x01")
    return d


def test_hash_all_records_a_content_hash_for_every_file(input_dir: Path):
    m = build_manifest(input_dir, "hash_all")
    assert m["policy"] == "hash_all"
    assert set(m["files"]) == {"index.csv", "sub/scan.bin"}
    assert all(e["sha256"] for e in m["files"].values())
    assert all("size" in e and "mtime" in e for e in m["files"].values())


def test_none_records_paths_sizes_and_mtimes_but_no_content_hash(input_dir: Path):
    m = build_manifest(input_dir, "none")
    assert all(e["sha256"] is None for e in m["files"].values())


def test_a_clean_input_verifies(input_dir: Path):
    m = build_manifest(input_dir, "hash_all")
    assert verify_manifest(input_dir, m) == []


def test_changed_content_is_detected_under_hash_all(input_dir: Path):
    m = build_manifest(input_dir, "hash_all")
    (input_dir / "index.csv").write_text("patient_id\np1\np2\np3\n")
    assert verify_manifest(input_dir, m) == ["index.csv"]


def test_a_removed_file_is_detected(input_dir: Path):
    m = build_manifest(input_dir, "hash_all")
    (input_dir / "sub" / "scan.bin").unlink()
    assert verify_manifest(input_dir, m) == ["sub/scan.bin"]


def test_an_added_file_is_detected(input_dir: Path):
    """`hash_all` claims the data was identical; a new file means it was not."""
    m = build_manifest(input_dir, "hash_all")
    (input_dir / "extra.csv").write_text("patient_id\np3\n")
    assert verify_manifest(input_dir, m) == ["extra.csv"]


def test_the_manifest_hash_is_stable_and_prefixed(input_dir: Path):
    m = build_manifest(input_dir, "hash_all")
    assert manifest_hash(m) == manifest_hash(build_manifest(input_dir, "hash_all"))
    assert manifest_hash(m).startswith("sha256:")
```

- [ ] **Step 2: Run it and watch it fail**

Run: `uv run pytest tests/test_manifest.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'publishable.manifest'`

- [ ] **Step 3: Implement `manifest.py`**

```python
# src/publishable/manifest.py
"""What was read. See docs/reference.md § How the three are computed."""

import hashlib
import json
from pathlib import Path
from typing import Any

POLICIES = ("hash_all", "hash_index", "none")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(input_dir: Path, policy: str, index_names: set[str] | None = None) -> dict:
    """Relative paths plus size, mtime, and — at the policy's depth — content hash."""
    if policy not in POLICIES:
        raise ValueError(f"unknown input_manifest_policy {policy!r}")
    files: dict[str, Any] = {}
    for path in sorted(p for p in input_dir.rglob("*") if p.is_file()):
        rel = path.relative_to(input_dir).as_posix()
        stat = path.stat()
        hash_it = policy == "hash_all" or (
            policy == "hash_index" and rel in (index_names or set())
        )
        files[rel] = {
            "size": stat.st_size,
            # Nanoseconds, not seconds: truncating to whole seconds leaves a
            # one-second window in which a same-size in-place edit is invisible
            # to the size+timestamp policies.
            "mtime": stat.st_mtime_ns,
            "sha256": _sha256(path) if hash_it else None,
        }
    return {"policy": policy, "files": files}


def manifest_hash(manifest: dict) -> str:
    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def verify_manifest(input_dir: Path, manifest: dict) -> list[str]:
    """Relative paths that moved since the manifest was built. Empty when clean.

    An added file counts as a change: `hash_all` claims the data was identical,
    and a dataset with a file in it that was not there at run start is not.
    """
    changed: list[str] = []
    present = {p.relative_to(input_dir).as_posix() for p in input_dir.rglob("*") if p.is_file()}
    changed.extend(present - set(manifest["files"]))
    for rel, entry in manifest["files"].items():
        path = input_dir / rel
        if not path.is_file():
            changed.append(rel)
            continue
        stat = path.stat()
        if entry["sha256"] is not None:
            if _sha256(path) != entry["sha256"]:
                changed.append(rel)
        elif stat.st_size != entry["size"] or stat.st_mtime_ns != entry["mtime"]:
            changed.append(rel)
    return sorted(changed)
```

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest tests/test_manifest.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add src/publishable/manifest.py tests/test_manifest.py
git commit -m "Pin the data, which is the one most tools leave open"
```

---

### Task 10: Steps, experiments, and the execution plan

**Files:**
- Create: `src/publishable/base_step.py`, `src/publishable/base_experiment.py`, `src/publishable/scope.py`
- Modify: `src/publishable/__init__.py`
- Test: `tests/test_scope.py`

**Interfaces:**
- Consumes: `ContractError`.
- Produces: `BaseStep` with class attributes `scope: str = "repeat"`, `nondeterministic: bool = False`, instance attributes `condition`, `repeat`, `rng`, method `derive_seed(purpose: str) -> int`, abstract `run(cfg, io)`; `BaseExperiment` with `steps: list[type[BaseStep]]`; `SCOPES = ("run", "condition", "repeat", "summary")`; `Execution` frozen dataclass with `step_cls`, `step_name: str`, `scope: str`, `condition_index: int | None`, `condition_label: str | None`, `repeat_label: str | None`; `build_plan(experiment, conditions, repeat_labels) -> list[Execution]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_scope.py
import pytest
from publishable import BaseExperiment, BaseStep, ContractError
from publishable.scope import build_plan


class Load(BaseStep):
    scope = "run"

    def run(self, cfg, io): ...


class Fit(BaseStep):
    scope = "condition"

    def run(self, cfg, io): ...


class Analyze(BaseStep):
    scope = "repeat"

    def run(self, cfg, io): ...


class Compare(BaseStep):
    scope = "summary"

    def run(self, cfg, io): ...


class Pipeline(BaseExperiment):
    steps = [Load, Fit, Analyze, Compare]


def test_scope_decides_execution_count():
    plan = build_plan(Pipeline(), conditions=[(0, None)], repeat_labels=["seed17", "seed42"])
    counts = {s: sum(1 for e in plan if e.step_name == s) for s in
              ("load", "fit", "analyze", "compare")}
    assert counts == {"load": 1, "fit": 1, "analyze": 2, "compare": 1}


def test_the_plan_is_ordered_run_then_conditions_then_summary():
    plan = build_plan(Pipeline(), conditions=[(0, None)], repeat_labels=["seed17"])
    assert [e.scope for e in plan] == ["run", "condition", "repeat", "summary"]


def test_repeat_executions_carry_their_repeat_label():
    plan = build_plan(Pipeline(), conditions=[(0, None)], repeat_labels=["seed17", "seed42"])
    labels = [e.repeat_label for e in plan if e.scope == "repeat"]
    assert labels == ["seed17", "seed42"]


def test_step_name_is_derived_from_the_module_style_class_name():
    plan = build_plan(Pipeline(), conditions=[(0, None)], repeat_labels=["seed17"])
    assert {e.step_name for e in plan} == {"load", "fit", "analyze", "compare"}


def test_an_unknown_scope_is_refused():
    class Bad(BaseStep):
        scope = "epoch"

        def run(self, cfg, io): ...

    class BadPipeline(BaseExperiment):
        steps = [Bad]

    with pytest.raises(ContractError) as e:
        build_plan(BadPipeline(), conditions=[(0, None)], repeat_labels=["seed17"])
    assert e.value.code == "E-STEP-SCOPE-UNKNOWN"


def test_derive_seed_is_stable_and_varies_with_purpose():
    step = Analyze()
    step._bind(condition=None, repeat="seed17", digest="sha256:abc", seed=17)
    a = step.derive_seed("optimizer-dev-split")
    b = step.derive_seed("optimizer-dev-split")
    c = step.derive_seed("other-split")
    assert a == b and a != c
```

- [ ] **Step 2: Run it and watch it fail**

Run: `uv run pytest tests/test_scope.py -v`
Expected: FAIL — `ImportError: cannot import name 'BaseExperiment'`

- [ ] **Step 3: Implement `base_step.py`**

```python
# src/publishable/base_step.py
"""One stage of the pipeline. `__init__` is core's — don't define one."""

import hashlib
import random
from typing import Any

from publishable.errors import ContractError


class BaseStep:
    scope: str = "repeat"
    nondeterministic: bool = False

    def __init__(self) -> None:
        self._condition: Any = None
        self._repeat: str | None = None
        self._digest: str = ""
        self._seed: int = 0
        self.rng: random.Random = random.Random(0)

    def _bind(self, *, condition: Any, repeat: str | None, digest: str, seed: int) -> None:
        """Core sets the execution context before calling `run`."""
        self._condition = condition
        self._repeat = repeat
        self._digest = digest
        self._seed = seed
        self.rng = random.Random(seed)

    @property
    def condition(self) -> Any:
        if self._condition is None:
            raise ContractError(
                f"`self.condition` has no value at scope {self.scope!r}",
                code="E-STEP-CONTEXT-ABSENT",
            )
        return self._condition

    @property
    def repeat(self) -> str:
        if self._repeat is None:
            raise ContractError(
                f"`self.repeat` has no value at scope {self.scope!r}",
                code="E-STEP-CONTEXT-ABSENT",
            )
        return self._repeat

    def derive_seed(self, purpose: str) -> int:
        """Mix the design digest, the execution seed, and the purpose into an integer."""
        payload = f"{self._digest}|{self._seed}|{purpose}".encode()
        return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")

    def run(self, cfg: Any, io: Any) -> dict[str, Any]:
        raise NotImplementedError
```

- [ ] **Step 4: Implement `base_experiment.py` and `scope.py`**

```python
# src/publishable/base_experiment.py
"""The ordered steps list, and nothing else."""

from publishable.base_step import BaseStep


class BaseExperiment:
    steps: list[type[BaseStep]] = []
```

```python
# src/publishable/scope.py
"""Derive the execution plan from declared scopes. docs/reference.md § Step scope."""

import re
from dataclasses import dataclass

from publishable.base_experiment import BaseExperiment
from publishable.base_step import BaseStep
from publishable.errors import ContractError

SCOPES = ("run", "condition", "repeat", "summary")


def step_name(cls: type[BaseStep]) -> str:
    """`LoadCohort` → `load_cohort`; a generated `Step` uses its module name."""
    if cls.__name__ == "Step":
        return cls.__module__.rsplit(".", 1)[-1]
    return re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()


@dataclass(frozen=True)
class Execution:
    step_cls: type[BaseStep]
    step_name: str
    scope: str
    condition_index: int | None
    condition_label: str | None
    repeat_label: str | None


def build_plan(
    experiment: BaseExperiment,
    conditions: list[tuple[int, str | None]],
    repeat_labels: list[str],
) -> list[Execution]:
    for cls in experiment.steps:
        if cls.scope not in SCOPES:
            raise ContractError(
                f"{cls.__name__} declares scope {cls.scope!r}; expected one of "
                + ", ".join(SCOPES),
                code="E-STEP-SCOPE-UNKNOWN",
            )
    plan: list[Execution] = []
    for cls in (c for c in experiment.steps if c.scope == "run"):
        plan.append(Execution(cls, step_name(cls), "run", None, None, None))
    for index, label in conditions:
        for cls in (c for c in experiment.steps if c.scope == "condition"):
            plan.append(Execution(cls, step_name(cls), "condition", index, label, None))
        for cls in (c for c in experiment.steps if c.scope == "repeat"):
            for repeat in repeat_labels:
                plan.append(Execution(cls, step_name(cls), "repeat", index, label, repeat))
    for cls in (c for c in experiment.steps if c.scope == "summary"):
        plan.append(Execution(cls, step_name(cls), "summary", None, None, None))
    return plan
```

- [ ] **Step 5: Export from the import root**

Add `BaseExperiment` and `BaseStep` imports and `__all__` entries to `src/publishable/__init__.py`.

- [ ] **Step 6: Run and verify green**

Run: `uv run pytest tests/test_scope.py -v && uv run mypy`
Expected: 6 passed, no type errors.

- [ ] **Step 7: Commit**

```bash
git add src/publishable/base_step.py src/publishable/base_experiment.py \
        src/publishable/scope.py src/publishable/__init__.py tests/test_scope.py
git commit -m "Let a step say how often it should run"
```

---

### Task 11: Repeats — the `seed` kind

**Files:**
- Create: `src/publishable/replication.py`
- Test: `tests/test_replication.py`

**Interfaces:**
- Consumes: `design_digest`, `ContractError`.
- Produces: `Repeat` frozen dataclass with `kind: str`, `label: str`, `seed: int`; `resolve_repeats(config: dict, digest: str) -> list[Repeat]`; `REJECTED_KINDS` mapping a rejected name to its pointer.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_replication.py
import pytest
from publishable import ContractError
from publishable.replication import resolve_repeats


def cfg(repeats):
    return {"replication": {"repeats": repeats}}


def test_five_seed_repeats_resolve_to_five_labelled_repeats():
    reps = resolve_repeats(cfg([{"kind": "seed", "n": 5}]), "sha256:abc")
    assert len(reps) == 5
    assert all(r.kind == "seed" for r in reps)
    assert len({r.label for r in reps}) == 5
    assert all(r.label.startswith("seed") for r in reps)


def test_labels_and_seeds_are_stable_for_one_digest():
    a = resolve_repeats(cfg([{"kind": "seed", "n": 3}]), "sha256:abc")
    b = resolve_repeats(cfg([{"kind": "seed", "n": 3}]), "sha256:abc")
    assert [r.label for r in a] == [r.label for r in b]
    assert [r.seed for r in a] == [r.seed for r in b]


def test_seeds_move_with_the_design_digest_not_with_parameters():
    a = resolve_repeats(cfg([{"kind": "seed", "n": 3}]), "sha256:abc")
    b = resolve_repeats(cfg([{"kind": "seed", "n": 3}]), "sha256:def")
    assert [r.seed for r in a] != [r.seed for r in b]


def test_no_replication_block_means_one_unlabelled_repeat():
    reps = resolve_repeats({}, "sha256:abc")
    assert len(reps) == 1
    assert reps[0].label == ""


@pytest.mark.parametrize(
    "kind,pointer",
    [
        ("bootstrap", "statistics.resample"),
        ("permutation", "statistics.null_test"),
        ("technical", "data.units.measurements"),
        ("biological", "unit table"),
        ("holdout", "data.units.holdout"),
    ],
)
def test_rejected_kinds_are_refused_by_name_with_a_pointer(kind, pointer):
    with pytest.raises(ContractError) as e:
        resolve_repeats(cfg([{"kind": kind, "n": 3}]), "sha256:abc")
    assert e.value.code == "E-REPL-KIND"
    assert pointer in str(e.value)


def test_s1_does_not_yet_implement_batch_or_fold():
    with pytest.raises(ContractError) as e:
        resolve_repeats(cfg([{"kind": "fold", "k": 10}]), "sha256:abc")
    assert e.value.code == "E-REPL-KIND-UNSUPPORTED"
```

- [ ] **Step 2: Run it and watch it fail**

Run: `uv run pytest tests/test_replication.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'publishable.replication'`

- [ ] **Step 3: Implement `replication.py`**

```python
# src/publishable/replication.py
"""Repeat kinds. S1 implements `seed`; `batch` and `fold` arrive in S3.

See docs/reference.md § Repeat kinds.
"""

import hashlib
from dataclasses import dataclass
from typing import Any

from publishable.errors import ContractError

SUPPORTED_KINDS = ("seed",)
PLANNED_KINDS = ("batch", "fold")
REJECTED_KINDS = {
    "bootstrap": "declare `statistics.resample` instead",
    "permutation": "declare `statistics.null_test` instead",
    "technical": "declare `data.units.measurements` instead",
    "biological": "independent samples are rows in the unit table",
    "holdout": "declare `data.units.holdout` instead",
}


@dataclass(frozen=True)
class Repeat:
    kind: str
    label: str
    seed: int


def _seed_for(digest: str, index: int) -> int:
    payload = f"{digest}|seed|{index}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "big")


def resolve_repeats(config: dict[str, Any], digest: str) -> list[Repeat]:
    levels = ((config.get("replication") or {}).get("repeats")) or []
    if not levels:
        return [Repeat(kind="seed", label="", seed=_seed_for(digest, 0))]
    if len(levels) > 1:
        raise ContractError(
            "nested repeat levels are not supported yet; S3 adds them",
            code="E-REPL-KIND-UNSUPPORTED",
        )
    level = levels[0]
    kind = level.get("kind")
    if kind in REJECTED_KINDS:
        raise ContractError(
            f"`{kind}` is not a repeat kind — {REJECTED_KINDS[kind]}", code="E-REPL-KIND"
        )
    if kind in PLANNED_KINDS:
        raise ContractError(
            f"repeat kind `{kind}` is specified but not implemented in this build",
            code="E-REPL-KIND-UNSUPPORTED",
        )
    if kind not in SUPPORTED_KINDS:
        raise ContractError(f"`{kind}` is not a repeat kind", code="E-REPL-KIND")
    n = int(level.get("n", 1))
    if n < 1:
        # Returning [] here would produce a run with no repeat executions at all,
        # which reads as success. A design that repeats nothing is a declaration error.
        raise ContractError(
            f"`{{kind: seed, n: {n}}}` executes nothing; n must be at least 1",
            code="E-REPL-N",
        )
    repeats = []
    for index in range(n):
        seed = _seed_for(digest, index)
        repeats.append(Repeat(kind="seed", label=f"seed{seed % 100:02d}", seed=seed))
    if len({r.label for r in repeats}) != n:
        repeats = [
            Repeat(kind="seed", label=f"seed{r.seed}", seed=r.seed) for r in repeats
        ]
    return repeats
```

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest tests/test_replication.py -v`
Expected: 10 passed (the parametrised test counts five).

- [ ] **Step 5: Commit**

```bash
git add src/publishable/replication.py tests/test_replication.py
git commit -m "Refuse the five kinds that are not re-executions"
```

---

### Task 12: `io` — atomic, append-only artifacts

**Files:**
- Create: `src/publishable/artifacts.py`
- Test: `tests/test_artifacts.py`

**Interfaces:**
- Consumes: `ArtifactError`, `ArtifactExistsError`.
- Produces: `StepIO(step_dir: Path, input_dir: Path, run_dir: Path)` with `.write(name, obj)`, `.append(name, record)`, `.path(name)`, `.exists(name)`, `.read_input(relpath)`, `.read_upstream(step, name)`, `.resumed: bool`, `.recorded_keys: set[str]`; `WRITERS: dict[str, Callable]`; `write_atomic(path: Path, data: bytes) -> None`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_artifacts.py
from pathlib import Path

import pytest
from publishable import ArtifactError, ArtifactExistsError
from publishable.artifacts import StepIO, write_atomic


@pytest.fixture
def io(tmp_path: Path) -> StepIO:
    step_dir = tmp_path / "run" / "shared" / "step01"
    step_dir.mkdir(parents=True)
    (tmp_path / "input").mkdir()
    return StepIO(step_dir=step_dir, input_dir=tmp_path / "input", run_dir=tmp_path / "run")


def test_write_dispatches_on_the_longest_registered_suffix(io: StepIO):
    io.write("a.json", {"x": 1})
    io.write("b.yaml", {"y": 2})
    io.write("c.jsonl", [{"i": 1}, {"i": 2}])
    io.write("d.csv", [{"k": "p1", "v": 1}])
    assert (io.step_dir / "a.json").read_text().strip() == '{"x": 1}'
    assert "y: 2" in (io.step_dir / "b.yaml").read_text()
    assert (io.step_dir / "c.jsonl").read_text().count("\n") == 2
    assert "k,v" in (io.step_dir / "d.csv").read_text()


def test_an_unregistered_extension_takes_bytes_or_str_verbatim(io: StepIO):
    io.write("model.pkl", b"\x80\x04")
    assert (io.step_dir / "model.pkl").read_bytes() == b"\x80\x04"
    with pytest.raises(ArtifactError) as e:
        io.write("model2.pkl", {"not": "bytes"})
    assert e.value.code == "E-ARTIFACT-UNWRITABLE"


def test_nothing_is_ever_overwritten(io: StepIO):
    io.write("a.json", {"x": 1})
    with pytest.raises(ArtifactExistsError) as e:
        io.write("a.json", {"x": 2})
    assert e.value.code == "E-ARTIFACT-EXISTS"
    assert io.exists("a.json")


def test_path_is_existence_checked_in_the_write_direction(io: StepIO):
    assert io.path("fig.png").parent.exists()
    io.write("fig.png", b"\x89PNG")
    with pytest.raises(ArtifactExistsError):
        io.path("fig.png")


def test_a_name_is_a_relative_path_and_intermediate_dirs_are_created(io: StepIO):
    io.write("figures/roc.png", b"\x89PNG")
    assert (io.step_dir / "figures" / "roc.png").is_file()


def test_escaping_the_step_directory_is_rejected(io: StepIO):
    for bad in ("/etc/passwd", "../escape.json", "figures/../../escape.json"):
        with pytest.raises(ArtifactError) as e:
            io.write(bad, {"x": 1})
        assert e.value.code == "E-ARTIFACT-NAME"


def test_append_is_jsonl_only(io: StepIO):
    io.append("log.jsonl", {"event": "start"})
    io.append("log.jsonl", {"event": "stop"})
    assert (io.step_dir / "log.jsonl").read_text().count("\n") == 2
    with pytest.raises(ArtifactError) as e:
        io.append("log.txt", {"event": "x"})
    assert e.value.code == "E-ARTIFACT-APPEND"


def test_a_crash_mid_write_leaves_nothing(tmp_path: Path, monkeypatch):
    """The rename is the only moment the target appears. Break it and nothing lands.

    Note the failure is injected INSIDE write_atomic — passing an expression that
    raises would be evaluated before the call and would test nothing.
    """
    target = tmp_path / "out.bin"

    def boom(*args: object, **kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr("publishable.artifacts.os.replace", boom)
    with pytest.raises(OSError):
        write_atomic(target, b"real bytes that never land")
    assert not target.exists()
    assert list(tmp_path.iterdir()) == [], "no .partial- temp file may survive either"


def test_read_input_reaches_the_input_dir_read_only(io: StepIO, tmp_path: Path):
    (tmp_path / "input" / "index.csv").write_text("patient_id\np1\n")
    rows = io.read_input("index.csv")
    assert rows == [{"patient_id": "p1"}]
```

- [ ] **Step 2: Run it and watch it fail**

Run: `uv run pytest tests/test_artifacts.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'publishable.artifacts'`

- [ ] **Step 3: Implement `artifacts.py`**

```python
# src/publishable/artifacts.py
"""Scope-aware, atomic, append-only artifacts. docs/reference.md § Steps and artifacts."""

import csv
import io as _io
import json
import os
import tempfile
from pathlib import Path
from typing import Any

import yaml

from publishable.errors import ArtifactError, ArtifactExistsError


def write_atomic(path: Path, data: bytes) -> None:
    """Temp file plus rename, so a crash leaves nothing rather than a half-file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".partial-")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def _encode_json(obj: Any) -> bytes:
    return (json.dumps(obj, ensure_ascii=False) + "\n").encode()


def _encode_yaml(obj: Any) -> bytes:
    return yaml.safe_dump(obj, sort_keys=False).encode()


def _encode_jsonl(rows: Any) -> bytes:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode()


def _encode_csv(rows: Any) -> bytes:
    rows = list(rows)
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    buf = _io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode()


WRITERS = {
    ".json": _encode_json,
    ".yaml": _encode_yaml,
    ".jsonl": _encode_jsonl,
    ".csv": _encode_csv,
}


def _suffix_for(name: str) -> str | None:
    """The longest registered suffix of the name's last component, lower-cased."""
    last = name.rsplit("/", 1)[-1].lower()
    best: str | None = None
    for suffix in WRITERS:
        if last.endswith(suffix) and (best is None or len(suffix) > len(best)):
            best = suffix
    return best


class StepIO:
    def __init__(self, *, step_dir: Path, input_dir: Path, run_dir: Path) -> None:
        self.step_dir = step_dir
        self.input_dir = input_dir
        self.run_dir = run_dir
        self.resumed = False
        self.recorded_keys: set[str] = set()

    def _resolve(self, name: str) -> Path:
        candidate = (self.step_dir / name).resolve()
        base = self.step_dir.resolve()
        if Path(name).is_absolute() or not str(candidate).startswith(str(base) + os.sep):
            raise ArtifactError(
                f"{name!r} resolves outside the step's directory", code="E-ARTIFACT-NAME"
            )
        return candidate

    def path(self, name: str) -> Path:
        target = self._resolve(name)
        if target.exists():
            raise ArtifactExistsError(f"{name} already exists", code="E-ARTIFACT-EXISTS")
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    def exists(self, name: str) -> bool:
        return self._resolve(name).exists()

    def write(self, name: str, obj: Any) -> Path:
        target = self.path(name)
        suffix = _suffix_for(name)
        if suffix is not None:
            data = WRITERS[suffix](obj)
        elif isinstance(obj, bytes):
            data = obj
        elif isinstance(obj, str):
            data = obj.encode()
        else:
            raise ArtifactError(
                f"{name} has no registered writer, so the object must be bytes or str, "
                f"not {type(obj).__name__}",
                code="E-ARTIFACT-UNWRITABLE",
            )
        write_atomic(target, data)
        return target

    def append(self, name: str, record: dict[str, Any]) -> None:
        if not name.lower().endswith(".jsonl"):
            raise ArtifactError(
                f"`io.append` writes one JSON object per line, so {name} must be .jsonl",
                code="E-ARTIFACT-APPEND",
            )
        target = self._resolve(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    def read_input(self, relpath: str) -> Any:
        return self._read(self.input_dir / relpath)

    def read_upstream(self, step: str, name: str) -> Any:
        return self._read(self.run_dir / "shared" / step / name)

    @staticmethod
    def _read(path: Path) -> Any:
        low = path.name.lower()
        if low.endswith(".json"):
            return json.loads(path.read_text())
        if low.endswith(".yaml"):
            return yaml.safe_load(path.read_text())
        if low.endswith(".jsonl"):
            return [json.loads(line) for line in path.read_text().splitlines() if line]
        if low.endswith(".csv"):
            return list(csv.DictReader(_io.StringIO(path.read_text())))
        return path.read_bytes()
```

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest tests/test_artifacts.py -v`
Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add src/publishable/artifacts.py tests/test_artifacts.py
git commit -m "Never overwrite, and never leave half a file behind"
```

---

### Task 13: Run identity and the directory lock

**Files:**
- Create: `src/publishable/run_identity.py`
- Test: `tests/test_run_identity.py`

**Interfaces:**
- Consumes: `short`, `ContractError`.
- Produces: `allocate_run_dir(output_dir: Path, code_hash: str, when: datetime) -> Path`; `point_latest(output_dir: Path, run_dir: Path) -> None`; `RunLock(run_dir)` as a context manager raising `ContractError` code `E-RUN-LOCKED`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_run_identity.py
from datetime import datetime, timezone
from pathlib import Path

import pytest
from publishable import ContractError
from publishable.run_identity import RunLock, allocate_run_dir, point_latest

WHEN = datetime(2026, 8, 8, 14, 2, 11, tzinfo=timezone.utc)
HASH = "sha256:8e21ab3cafe0000000000000000000000000000000000000000000000000000"


def test_the_id_is_timestamp_then_short_code_hash(tmp_path: Path):
    run_dir = allocate_run_dir(tmp_path, HASH, WHEN)
    assert run_dir.name == "run_2026-08-08T14-02-11Z_8e21ab3"
    assert run_dir.is_dir()


def test_a_collision_is_resolved_by_suffix_not_by_precision(tmp_path: Path):
    first = allocate_run_dir(tmp_path, HASH, WHEN)
    second = allocate_run_dir(tmp_path, HASH, WHEN)
    third = allocate_run_dir(tmp_path, HASH, WHEN)
    assert second.name == first.name + "_b"
    assert third.name == first.name + "_c"


def test_latest_points_at_the_real_id(tmp_path: Path):
    run_dir = allocate_run_dir(tmp_path, HASH, WHEN)
    point_latest(tmp_path, run_dir)
    latest = tmp_path / "latest"
    resolved = latest.resolve() if latest.is_symlink() else tmp_path / (
        tmp_path / "latest.txt"
    ).read_text().strip()
    assert resolved.name == run_dir.name


def test_the_lock_records_who_holds_it_and_is_released(tmp_path: Path):
    run_dir = allocate_run_dir(tmp_path, HASH, WHEN)
    with RunLock(run_dir):
        assert (run_dir / "lock").is_file()
        assert "pid" in (run_dir / "lock").read_text()
    assert not (run_dir / "lock").exists()


def test_a_held_lock_is_reported_rather_than_assumed_dead(tmp_path: Path):
    run_dir = allocate_run_dir(tmp_path, HASH, WHEN)
    with RunLock(run_dir):
        with pytest.raises(ContractError) as e:
            with RunLock(run_dir):
                pass
        assert e.value.code == "E-RUN-LOCKED"
```

- [ ] **Step 2: Run it and watch it fail**

Run: `uv run pytest tests/test_run_identity.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'publishable.run_identity'`

- [ ] **Step 3: Implement `run_identity.py`**

```python
# src/publishable/run_identity.py
"""Run identity and the directory lock. docs/reference.md § Run identity."""

import json
import os
import socket
import string
from datetime import datetime
from pathlib import Path
from types import TracebackType

from publishable.errors import ContractError
from publishable.hashes import short


def allocate_run_dir(output_dir: Path, code_hash: str, when: datetime) -> Path:
    """First free name. A collision takes a suffix, never more clock precision."""
    stamp = when.strftime("%Y-%m-%dT%H-%M-%SZ")
    base = f"run_{stamp}_{short(code_hash)}"
    output_dir.mkdir(parents=True, exist_ok=True)
    for suffix in ("", *(f"_{c}" for c in string.ascii_lowercase[1:])):
        candidate = output_dir / (base + suffix)
        try:
            # mkdir IS the claim. Checking `exists()` first would leave a window
            # in which two runs started in the same second both see it free —
            # exactly the shell-loop and scheduler cases this suffix exists for.
            candidate.mkdir()
        except FileExistsError:
            continue
        return candidate
    raise ContractError(
        f"26 runs already share the id {base}", code="E-RUN-ID-EXHAUSTED"
    )


def point_latest(output_dir: Path, run_dir: Path) -> None:
    """A pointer, not an artifact. Falls back to latest.txt without symlinks."""
    link = output_dir / "latest"
    try:
        if link.is_symlink() or link.exists():
            link.unlink()
        link.symlink_to(run_dir.name)
    except (OSError, NotImplementedError):
        (output_dir / "latest.txt").write_text(run_dir.name + "\n")


class RunLock:
    """A run holds its directory while it executes."""

    def __init__(self, run_dir: Path) -> None:
        self.path = run_dir / "lock"

    def __enter__(self) -> "RunLock":
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise ContractError(
                f"{self.path} is held: {self.path.read_text().strip()}. "
                "A lock left by a killed process is reported, never assumed dead.",
                code="E-RUN-LOCKED",
            ) from None
        with os.fdopen(fd, "w") as fh:
            json.dump(
                {"host": socket.gethostname(), "pid": os.getpid()}, fh
            )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.path.unlink(missing_ok=True)
```

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest tests/test_run_identity.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add src/publishable/run_identity.py tests/test_run_identity.py
git commit -m "Give every run its own name and its own lock"
```

---

### Task 14: The runner and `run.yaml`

**Files:**
- Create: `src/publishable/runner.py`, `src/publishable/run_record.py`
- Test: `tests/test_runner.py`

**Interfaces:**
- Consumes: `Execution`, `build_plan`, `Repeat`, `StepIO`, `Config`, `PublishableError`.
- Produces: `ExecutionResult` frozen dataclass with `execution`, `status: str`, `started_at: str`, `wall_seconds: float`, `returned: dict`, `error: str | None`; `execute_plan(...) -> list[ExecutionResult]`; `assemble_run_yaml(...) -> dict`; `run_status(results) -> str`.

**Layout rule this task implements:** degenerate levels collapse. With no sweep there is no `conditions/` level; with one repeat there is no repeat level. `shared/` and `summary/` name a scope, so they are unaffected.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_runner.py
from pathlib import Path

from publishable import BaseExperiment, BaseStep
from publishable.config import Config
from publishable.replication import Repeat
from publishable.run_record import assemble_run_yaml, run_status
from publishable.runner import execute_plan
from publishable.scope import build_plan


class Load(BaseStep):
    scope = "run"

    def run(self, cfg, io):
        io.write("cohort.json", {"loaded": True})
        return {"n": 2}


class Analyze(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        return {"r": 0.5}


class Boom(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        raise ValueError("this execution is broken")


def harness(tmp_path: Path, steps):
    class P(BaseExperiment):
        pass

    P.steps = steps
    repeats = [Repeat("seed", "seed17", 17), Repeat("seed", "seed42", 42)]
    plan = build_plan(P(), conditions=[(0, None)], repeat_labels=[r.label for r in repeats])
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / "input").mkdir(parents=True, exist_ok=True)
    results = execute_plan(
        plan=plan,
        run_dir=run_dir,
        input_dir=tmp_path / "input",
        cfg=Config({"parameters": {}}),
        repeats=repeats,
        digest="sha256:abc",
    )
    return run_dir, results


def test_no_sweep_means_no_conditions_level(tmp_path: Path):
    run_dir, _ = harness(tmp_path, [Load, Analyze])
    assert (run_dir / "shared" / "load" / "cohort.json").is_file()
    assert not (run_dir / "conditions").exists()
    assert (run_dir / "seed17").is_dir()
    assert (run_dir / "seed42").is_dir()


def test_a_failed_execution_is_recorded_and_the_run_continues(tmp_path: Path):
    _, results = harness(tmp_path, [Boom, Analyze])
    statuses = [r.status for r in results]
    assert statuses.count("failed") == 2
    assert statuses.count("completed") == 2
    assert any("this execution is broken" in (r.error or "") for r in results)


def test_status_is_partial_when_some_failed(tmp_path: Path):
    _, results = harness(tmp_path, [Boom, Analyze])
    assert run_status(results) == "partial"
    _, ok = harness(tmp_path / "b", [Load, Analyze])
    assert run_status(ok) == "completed"


def test_executions_jsonl_gets_one_record_per_finished_execution(tmp_path: Path):
    run_dir, results = harness(tmp_path, [Load, Analyze])
    lines = (run_dir / "executions.jsonl").read_text().splitlines()
    assert len(lines) == len(results)


def test_per_repeat_holds_exactly_what_the_step_returned(tmp_path: Path):
    _, results = harness(tmp_path, [Load, Analyze])
    doc = assemble_run_yaml(
        run_id="run_x", status="completed", config={"a": 1}, code_hash="sha256:c",
        parameters_hash="sha256:p", provenance={}, results=results,
    )
    per_repeat = doc["results"]["conditions"][0]["per_repeat"]["analyze"]
    assert per_repeat == {"seed17": {"r": 0.5}, "seed42": {"r": 0.5}}


def test_run_yaml_carries_the_three_hashes_and_the_config_verbatim(tmp_path: Path):
    _, results = harness(tmp_path, [Load, Analyze])
    doc = assemble_run_yaml(
        run_id="run_x", status="completed", config={"metadata": {"name": "c"}},
        code_hash="sha256:c", parameters_hash="sha256:p",
        provenance={"input_manifest_hash": "sha256:m"}, results=results,
    )
    assert doc["code_hash"] == "sha256:c"
    assert doc["parameters_hash"] == "sha256:p"
    assert doc["provenance"]["input_manifest_hash"] == "sha256:m"
    assert doc["config"] == {"metadata": {"name": "c"}}
    assert doc["draft"] is False
    assert doc["schema_version"] == "1.0"
```

- [ ] **Step 2: Run it and watch it fail**

Run: `uv run pytest tests/test_runner.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'publishable.run_record'`

- [ ] **Step 3: Implement `runner.py`**

```python
# src/publishable/runner.py
"""The execution loop. One execution at a time, in the recorded order."""

import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from publishable.artifacts import StepIO
from publishable.replication import Repeat
from publishable.scope import Execution


@dataclass(frozen=True)
class ExecutionResult:
    execution: Execution
    status: str
    started_at: str
    wall_seconds: float
    returned: dict[str, Any]
    error: str | None


def step_dir_for(run_dir: Path, execution: Execution, collapse_repeats: bool) -> Path:
    """Depth follows scope; degenerate levels collapse."""
    if execution.scope == "run":
        return run_dir / "shared" / execution.step_name
    if execution.scope == "summary":
        return run_dir / "summary" / execution.step_name
    base = run_dir
    if execution.condition_label is not None:
        base = base / "conditions" / (
            f"{execution.condition_index:02d}_{execution.condition_label}"
        )
    if execution.scope == "repeat" and not collapse_repeats and execution.repeat_label:
        base = base / execution.repeat_label
    return base / execution.step_name


def execute_plan(
    *,
    plan: list[Execution],
    run_dir: Path,
    input_dir: Path,
    cfg: Any,
    repeats: list[Repeat],
    digest: str,
) -> list[ExecutionResult]:
    collapse = len(repeats) <= 1
    seeds = {r.label: r.seed for r in repeats}
    ledger = run_dir / "executions.jsonl"
    results: list[ExecutionResult] = []

    for execution in plan:
        started = datetime.now(timezone.utc)
        clock = time.monotonic()
        step = execution.step_cls()
        step._bind(
            condition=execution.condition_index,
            repeat=execution.repeat_label or None,
            digest=digest,
            seed=seeds.get(execution.repeat_label or "", 0),
        )
        io = StepIO(
            step_dir=step_dir_for(run_dir, execution, collapse),
            input_dir=input_dir,
            run_dir=run_dir,
        )
        io.step_dir.mkdir(parents=True, exist_ok=True)
        try:
            returned = step.run(cfg, io) or {}
            status, error = "completed", None
        except Exception as exc:  # a failed execution never stops the run
            returned, status, error = {}, "failed", f"{type(exc).__name__}: {exc}"

        result = ExecutionResult(
            execution=execution,
            status=status,
            started_at=started.strftime("%Y-%m-%dT%H:%M:%SZ"),
            wall_seconds=round(time.monotonic() - clock, 3),
            returned=returned,
            error=error,
        )
        results.append(result)
        with ledger.open("a", encoding="utf-8") as fh:
            fh.write(
                json.dumps(
                    {
                        "step": execution.step_name,
                        "scope": execution.scope,
                        "condition": execution.condition_index,
                        "repeat": execution.repeat_label,
                        "status": status,
                        "started_at": result.started_at,
                        "wall_seconds": result.wall_seconds,
                        "error": error,
                    }
                )
                + "\n"
            )
    return results
```

- [ ] **Step 4: Implement `run_record.py`**

```python
# src/publishable/run_record.py
"""Assemble run.yaml. Assembles only — computes nothing.

See docs/reference.md § The two files.
"""

from typing import Any

from publishable.runner import ExecutionResult

SCHEMA_VERSION = "1.0"


def run_status(results: list[ExecutionResult]) -> str:
    if not results:
        return "failed"
    if all(r.status == "completed" for r in results):
        return "completed"
    if any(r.status == "completed" for r in results):
        return "partial"
    return "failed"


def _execution_block(results: list[ExecutionResult]) -> dict[str, Any]:
    shared: dict[str, Any] = {}
    summary: dict[str, Any] = {}
    conditions: dict[int, dict[str, Any]] = {}
    for r in results:
        entry = {
            "status": r.status,
            "started_at": r.started_at,
            "wall_seconds": r.wall_seconds,
            "attempts": 1,
        }
        if r.error:
            entry["error"] = r.error
        e = r.execution
        if e.scope == "run":
            shared[e.step_name] = entry
        elif e.scope == "summary":
            summary[e.step_name] = entry
        else:
            index = e.condition_index or 0
            cond = conditions.setdefault(index, {"index": index, "label": e.condition_label,
                                                 "steps": {}})
            if e.scope == "condition":
                cond["steps"][e.step_name] = entry
            else:
                cond["steps"].setdefault(e.step_name, {})[e.repeat_label or ""] = entry
    return {
        "shared": shared,
        "conditions": [conditions[k] for k in sorted(conditions)],
        "summary": summary,
    }


def _results_block(results: list[ExecutionResult]) -> dict[str, Any]:
    conditions: dict[int, dict[str, Any]] = {}
    summary: dict[str, Any] = {}
    for r in results:
        e = r.execution
        if e.scope == "summary":
            summary[e.step_name] = r.returned
            continue
        if e.scope == "run":
            continue
        index = e.condition_index or 0
        cond = conditions.setdefault(
            index, {"index": index, "label": e.condition_label, "per_repeat": {}}
        )
        if e.scope == "repeat":
            cond["per_repeat"].setdefault(e.step_name, {})[e.repeat_label or ""] = r.returned
        else:
            cond.setdefault("per_condition", {})[e.step_name] = r.returned
    return {
        "conditions": [conditions[k] for k in sorted(conditions)],
        "summary": summary,
    }


def assemble_run_yaml(
    *,
    run_id: str,
    status: str,
    config: dict[str, Any],
    code_hash: str,
    parameters_hash: str,
    provenance: dict[str, Any],
    results: list[ExecutionResult],
    draft: bool = False,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "status": status,
        "draft": draft,
        "config": config,
        "parameters_hash": parameters_hash,
        "code_hash": code_hash,
        "provenance": provenance,
        "execution": _execution_block(results),
        "results": _results_block(results),
    }
```

- [ ] **Step 5: Run and verify green**

Run: `uv run pytest tests/test_runner.py -v`
Expected: 6 passed.

- [ ] **Step 6: Record the two gaps this task exposes**

`_results_block` writes `per_repeat` and nothing else — no `aggregated` block, because
statistics is S4. Two things the documents leave unstated fall out of that.

```bash
cat >> docs/superpowers/spec-defects.md <<'EOF'

## Where a `"run"`-scoped step's return value goes is unstated

§ The two files gives `results` exactly two children, `conditions` and `summary`, and
`execution` gives `"run"` steps a `shared` block carrying status and timing but no
returned values. So a `"run"`-scoped step's `return {...}` is silently discarded. Every
other scope's return is recorded somewhere. Proposed resolution: either state in
§ Steps and artifacts that a `"run"` step's return is not recorded and should be an
artifact instead, or add a `results.shared` block alongside `results.summary`.

## A single repeat has no dispersion, and the documents don't say what is reported

§ The unit table is the inference base says that with no `data.units` declared, core
reports "mean, std, sem and a t-based `ci95` over repeats". With `n: 1` — legal, and what
`generic`'s `default_repeats` floor of 1 permits — std, sem and a t-interval are all
undefined. The documents state no rule for it. S1 does not hit this, because it emits no
`aggregated` block at all; **S4 does**, and needs an answer before it computes anything.
Proposed resolution: state in § The unit table is the inference base that a single repeat
reports the value with `basis: repeats` and omits `std`, `sem` and `ci95`.
EOF
```

- [ ] **Step 7: Commit**

```bash
git add src/publishable/runner.py src/publishable/run_record.py tests/test_runner.py \
        docs/superpowers/
git commit -m "Execute the plan to its end and write the record once"
```

---

### Task 15: `validate` — the S1 check subset

**Files:**
- Create: `src/publishable/validate.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: `Collector`, `get_template`, `Param`, `find_repo_root`.
- Produces: `validate_config(config_path: Path, collector: Collector) -> dict | None` returning the parsed config dict, or `None` when a fatal finding makes later checks meaningless.

**Identifiers this task defines** — each needs a test: `E-CONFIG-PARSE`, `E-META-REQUIRED`, `E-PARAM-UNKNOWN`, `E-PARAM-VALUE`, `E-PARAM-MISSING`, `E-NAME-PATTERN`, `E-NAME-DIR`, `E-TEMPLATE-UNKNOWN`, `E-TEMPLATE-RULE`, `E-DATA-REQUIRED`, `E-DATA-IN-REPO`, `E-DATA-UNREADABLE`, `E-REPL-N`, `W-TEMPLATE-VERSION`, `W-REPL-FLOOR`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_validate.py
from pathlib import Path

import pytest
import yaml
from publishable.diagnostics import Collector
from publishable.validate import validate_config


def base_config(tmp_path: Path) -> dict:
    return {
        "schema_version": "1.0",
        "experiment_type": "generic",
        "template_version": "1.0.0",
        "plugin": None,
        "metadata": {"name": "cohort-pilot", "description": "a pilot", "authors": ["A"]},
        "entrypoint": "cohort_pilot.experiment:CohortPilotExperiment",
        "data": {
            "input_dir": str(tmp_path / "input"),
            "output_dir": str(tmp_path / "results"),
            "input_manifest_policy": "hash_all",
        },
        "parameters": {
            "analysis": {
                "method": "pearson",
                "min_samples": 30,
                "confidence": 0.95,
                "drop_missing": True,
            }
        },
        "replication": {"repeats": [{"kind": "seed", "n": 5}], "order": "as_declared"},
    }


@pytest.fixture
def write_config(git_repo: Path, tmp_path: Path):
    (tmp_path / "input").mkdir(exist_ok=True)
    (tmp_path / "input" / "index.csv").write_text("patient_id\np1\n")

    def _write(overrides: dict | None = None) -> Path:
        doc = base_config(tmp_path)
        for dotted, value in (overrides or {}).items():
            node = doc
            *heads, leaf = dotted.split(".")
            for h in heads:
                node = node[h]
            if value is _DELETE:
                del node[leaf]
            else:
                node[leaf] = value
        path = git_repo / "configs" / "cohort-pilot" / "config.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(doc))
        return path

    return _write


_DELETE = object()


def codes(path: Path) -> set[str]:
    c = Collector()
    validate_config(path, c)
    return {f.code for f in c.findings}


def test_a_valid_config_reports_nothing(write_config):
    assert codes(write_config()) == set()


def test_an_empty_description_is_required(write_config):
    assert "E-META-REQUIRED" in codes(write_config({"metadata.description": ""}))


def test_an_unknown_key_is_a_typo_by_construction(write_config):
    path = write_config()
    doc = yaml.safe_load(path.read_text())
    doc["parameters"]["analysis"]["min_sample"] = 30
    path.write_text(yaml.safe_dump(doc))
    assert "E-PARAM-UNKNOWN" in codes(path)


def test_values_are_checked_not_just_presence(write_config):
    assert "E-PARAM-VALUE" in codes(write_config({"parameters.analysis.confidence": 1.4}))
    assert "E-PARAM-VALUE" in codes(write_config({"parameters.analysis.method": "pearsonn"}))
    assert "E-PARAM-VALUE" in codes(write_config({"parameters.analysis.min_samples": "30"}))


def test_a_missing_parameter_is_reported():
    """Exercised directly: every `generic` parameter has a default, so deleting one
    yields E-PARAM-UNKNOWN-free silence, never E-PARAM-MISSING. Same reason the floor
    warning below needs a stub template."""
    from publishable.param import Param
    from publishable.templates.base import BaseTemplate
    from publishable.validate import _check_parameters

    class NeedsOne(BaseTemplate):
        parameter_spec = {"analysis.required_one": Param(str)}   # no default => required

    c = Collector()
    _check_parameters({"parameters": {"analysis": {}}}, NeedsOne(), c)
    assert [f.code for f in c.findings] == ["E-PARAM-MISSING"]


def test_the_name_must_match_the_pattern_and_the_directory(write_config):
    assert "E-NAME-PATTERN" in codes(write_config({"metadata.name": "Cohort_Pilot"}))
    assert "E-NAME-DIR" in codes(write_config({"metadata.name": "cohort-pilot-v2"}))


def test_an_uninstalled_template_is_fatal(write_config):
    assert "E-TEMPLATE-UNKNOWN" in codes(write_config({"experiment_type": "llm_diagnostic"}))


def test_data_may_not_resolve_inside_the_repo(write_config, git_repo: Path):
    inside = str(git_repo / "results")
    assert "E-DATA-IN-REPO" in codes(write_config({"data.output_dir": inside}))


def test_an_unreadable_input_dir_is_reported(write_config, tmp_path: Path):
    assert "E-DATA-UNREADABLE" in codes(
        write_config({"data.input_dir": str(tmp_path / "absent")})
    )


def test_a_moved_template_version_warns_rather_than_failing(write_config):
    found = codes(write_config({"template_version": "0.9.0"}))
    assert "W-TEMPLATE-VERSION" in found


def test_a_repeat_count_below_one_executes_nothing_and_is_an_error(write_config):
    assert "E-REPL-N" in codes(write_config({"replication.repeats": [{"kind": "seed", "n": 0}]}))


def test_falling_below_the_repeat_floor_warns():
    """Exercised directly: `generic`'s floor is 1, so no legal count can breach it.

    Routing this through `validate_config` would need a template that does not
    exist yet, and asserting the warning against an illegal `n: 0` would be
    testing the error path while claiming to test the floor.
    """
    from publishable.templates.base import BaseTemplate
    from publishable.validate import _check_replication

    class Benchmark(BaseTemplate):
        default_repeats = 5

    c = Collector()
    _check_replication({"replication": {"repeats": [{"kind": "seed", "n": 3}]}}, Benchmark(), c)
    findings = [f for f in c.findings if f.code == "W-REPL-FLOOR"]
    assert len(findings) == 1
    assert "3" in findings[0].message and "5" in findings[0].message

    clean = Collector()
    _check_replication({"replication": {"repeats": [{"kind": "seed", "n": 5}]}}, Benchmark(), clean)
    assert clean.findings == []
```

- [ ] **Step 2: Run it and watch it fail**

Run: `uv run pytest tests/test_validate.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'publishable.validate'`

- [ ] **Step 3: Implement `validate.py`**

```python
# src/publishable/validate.py
"""The S1 check subset. Collects rather than stops. docs/reference.md § Validation."""

import re
from pathlib import Path
from typing import Any

import yaml

from publishable.diagnostics import Collector
from publishable.materialize import TEMPLATE_VERSION
from publishable.param import MISSING
from publishable.provenance import find_repo_root
from publishable.templates.registry import get_template, template_names

REQUIRED_METADATA = ("description", "authors")


def _flatten(node: Any, prefix: str = "") -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for key, value in (node or {}).items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(_flatten(value, path))
        else:
            flat[path] = value
    return flat


def validate_config(config_path: Path, c: Collector) -> dict[str, Any] | None:
    try:
        doc = yaml.safe_load(config_path.read_text())
    except yaml.YAMLError as exc:
        c.error("E-CONFIG-PARSE", str(config_path), f"does not parse: {exc}")
        return None
    if not isinstance(doc, dict):
        c.error("E-CONFIG-PARSE", str(config_path), "does not parse as a mapping")
        return None

    name = doc.get("experiment_type", "")
    template = get_template(name)
    if template is None:
        c.error(
            "E-TEMPLATE-UNKNOWN",
            "experiment_type",
            f"names `{name}`, which no installed template registers "
            f"(known: {', '.join(template_names())})",
        )
        return None  # every later check reads the spec

    _check_metadata(doc, config_path, template, c)
    _check_parameters(doc, template, c)
    _check_versions(doc, c)
    _check_data(doc, config_path, c)
    _check_replication(doc, template, c)
    for message in template.validate(doc):
        c.error("E-TEMPLATE-RULE", "parameters", message)
    return doc


def _check_metadata(doc: dict, config_path: Path, template: Any, c: Collector) -> None:
    metadata = doc.get("metadata") or {}
    for field in REQUIRED_METADATA:
        if not metadata.get(field):
            c.error("E-META-REQUIRED", f"metadata.{field}", "is empty, and is required")
    name = metadata.get("name", "")
    if name and not re.match(template.naming_pattern, name):
        c.error(
            "E-NAME-PATTERN",
            "metadata.name",
            f"is `{name}`, which does not match the template's naming_pattern "
            f"{template.naming_pattern}",
        )
    directory = config_path.parent.name
    if name and directory and name != directory:
        c.error(
            "E-NAME-DIR",
            "metadata.name",
            f"is `{name}` under `configs/{directory}/`; the two name one experiment",
        )


def _check_parameters(doc: dict, template: Any, c: Collector) -> None:
    declared = _flatten(doc.get("parameters"), "")
    spec = template.parameter_spec
    for path, value in declared.items():
        param = spec.get(path)
        if param is None:
            import difflib

            near = difflib.get_close_matches(path, list(spec), n=1)
            hint = f" — did you mean `{near[0]}`?" if near else ""
            c.error(
                "E-PARAM-UNKNOWN",
                f"parameters.{path}",
                f"is not a parameter of this template{hint}",
            )
            continue
        problem = param.check(value)
        if problem:
            c.error("E-PARAM-VALUE", f"parameters.{path}", problem)
    for path, param in spec.items():
        if path not in declared and param.default is MISSING:
            c.error("E-PARAM-MISSING", f"parameters.{path}", "is required and absent")


def _check_versions(doc: dict, c: Collector) -> None:
    declared = doc.get("template_version")
    if declared and declared != TEMPLATE_VERSION:
        c.warn(
            "W-TEMPLATE-VERSION",
            "template_version",
            f"is {declared} but the installed template reports {TEMPLATE_VERSION}",
        )


def _check_data(doc: dict, config_path: Path, c: Collector) -> None:
    data = doc.get("data") or {}
    try:
        repo_root = find_repo_root(config_path).resolve()
    except Exception:
        return
    for field in ("input_dir", "output_dir"):
        raw = data.get(field)
        if not raw:
            c.error("E-DATA-REQUIRED", f"data.{field}", "is empty, and is required")
            continue
        resolved = Path(raw).expanduser().resolve()
        if resolved == repo_root or repo_root in resolved.parents:
            c.error(
                "E-DATA-IN-REPO",
                f"data.{field}",
                f"resolves inside the git repository at {repo_root}",
            )
    input_dir = data.get("input_dir")
    if input_dir:
        path = Path(input_dir).expanduser()
        if not path.is_dir() or not any(path.iterdir()):
            c.error("E-DATA-UNREADABLE", "data.input_dir", f"{path} is unreadable or empty")


def _check_replication(doc: dict, template: Any, c: Collector) -> None:
    levels = ((doc.get("replication") or {}).get("repeats")) or []
    total = 1
    for level in levels:
        # `or` would read a declared 0 as "absent" and silently substitute 1,
        # which is the difference between warning about an empty design and not.
        count = level.get("n")
        if count is None:
            count = level.get("k")
        if count is not None and int(count) < 1:
            c.error(
                "E-REPL-N",
                "replication.repeats",
                f"declares {count}, which executes nothing; the count must be at least 1",
            )
            return
        total *= 1 if count is None else int(count)
    if total < template.default_repeats:
        c.warn(
            "W-REPL-FLOOR",
            "replication.repeats",
            f"total of {total} is below this convention class's default of "
            f"{template.default_repeats}",
        )
```

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest tests/test_validate.py -v`
Expected: 11 passed.

- [ ] **Step 5: Commit**

```bash
git add src/publishable/validate.py tests/test_validate.py
git commit -m "Check values before anyone spends four hours of compute"
```

---

### Task 16: `new` and the generators

**Files:**
- Create: `src/publishable/scaffold.py`, `src/publishable/generators/__init__.py`, `src/publishable/generators/experiment.py`, `src/publishable/generators/step.py`, `src/publishable/readme_templates/__init__.py`
- Test: `tests/test_scaffold.py`

**Interfaces:**
- Consumes: `materialize_config`, `get_template`.
- Produces: `scaffold_project(root: Path, license_name: str = "MIT") -> Path`; `generate_experiment(repo_root, name, template_name, input_dir, output_dir) -> Path` returning the config path; `generate_step(repo_root, experiment, step_name) -> Path`; `package_name(experiment: str) -> str` mapping `cohort-pilot` → `cohort_pilot`.

**S1 starter step deviation:** `reference.md` § The starter step runs specifies a body that calls `io.units` and `io.record`, which need S2. S1 generates a body that returns a trivial scalar and carries the same `TODO`. S2 replaces the one string in `generators/experiment.py`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_scaffold.py
from pathlib import Path

import yaml
from publishable.generators.experiment import generate_experiment, package_name
from publishable.generators.step import generate_step
from publishable.scaffold import scaffold_project


def test_new_creates_the_fixed_layout_and_a_first_commit(tmp_path: Path):
    root = scaffold_project(tmp_path / "my-study")
    for expected in ("README.md", "CITATION.cff", "LICENSE", "pyproject.toml",
                     ".gitignore", ".env.example"):
        assert (root / expected).is_file(), expected
    for expected in ("src", "templates", "configs", "tests", "docs", ".git"):
        assert (root / expected).exists(), expected
    assert not (root / "data").exists()
    assert not (root / "results").exists()


def test_the_scaffold_gitignores_env_but_says_nothing_about_configs(tmp_path: Path):
    root = scaffold_project(tmp_path / "my-study")
    ignored = (root / ".gitignore").read_text()
    assert ".env" in ignored
    assert "configs/" not in ignored


def test_package_name_converts_the_kebab_config_name(tmp_path: Path):
    assert package_name("cohort-pilot") == "cohort_pilot"


def test_generate_experiment_writes_config_package_and_a_runnable_step(tmp_path: Path):
    root = scaffold_project(tmp_path / "my-study")
    cfg_path = generate_experiment(
        repo_root=root, name="cohort-pilot", template_name="generic",
        input_dir=str(tmp_path / "data"), output_dir=str(tmp_path / "results"),
    )
    assert cfg_path == root / "configs" / "cohort-pilot" / "config.yaml"
    doc = yaml.safe_load(cfg_path.read_text())
    assert doc["metadata"]["name"] == "cohort-pilot"
    assert doc["entrypoint"] == "cohort_pilot.experiment:CohortPilotExperiment"
    pkg = root / "src" / "cohort_pilot"
    assert (pkg / "experiment.py").is_file()
    starter = next((pkg / "steps").glob("step01_*.py"))
    assert "TODO" in starter.read_text()
    assert "BaseStep" in starter.read_text()


def test_generate_step_numbers_the_next_file_and_registers_it(tmp_path: Path):
    root = scaffold_project(tmp_path / "my-study")
    generate_experiment(
        repo_root=root, name="cohort-pilot", template_name="generic",
        input_dir=str(tmp_path / "data"), output_dir=str(tmp_path / "results"),
    )
    path = generate_step(repo_root=root, experiment="cohort-pilot", step_name="analyze")
    assert path.name == "step02_analyze.py"
    experiment_py = (root / "src" / "cohort_pilot" / "experiment.py").read_text()
    assert "step02_analyze" in experiment_py


def test_generate_experiment_refuses_paths_inside_the_repo(tmp_path: Path):
    root = scaffold_project(tmp_path / "my-study")
    import pytest
    from publishable import ContractError

    with pytest.raises(ContractError) as e:
        generate_experiment(
            repo_root=root, name="cohort-pilot", template_name="generic",
            input_dir=str(root / "data"), output_dir=str(tmp_path / "results"),
        )
    assert e.value.code == "E-DATA-IN-REPO"
```

- [ ] **Step 2: Run it and watch it fail**

Run: `uv run pytest tests/test_scaffold.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'publishable.scaffold'`

- [ ] **Step 3: Implement `scaffold.py`**

````python
# src/publishable/scaffold.py
"""`publishable new`. docs/reference.md § Scaffolding."""

import subprocess
from pathlib import Path

GITIGNORE = """\
# Credentials — never committed
.env

# Python
__pycache__/
*.py[cod]
.venv/
"""

README = """\
# {name}

<!-- publishable:begin overview -->
A `publishable` experiment repository. Code, parameters, and provenance are
separated by construction: this repo holds code and configs; input and output
data live outside it, under paths each config names.
<!-- publishable:end overview -->

## Setup

```bash
uv sync
```

## Experiments

<!-- publishable:begin experiments -->
None yet. Create one with `publishable generate experiment <name>`.
<!-- publishable:end experiments -->
"""

CITATION = """\
cff-version: 1.2.0
message: "If you use this software, please cite it as below."
type: software
title: {name}
authors:
  - family-names: ""
    given-names: ""
version: 0.1.0
"""

MIT = """\
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
"""

PYPROJECT = """\
[project]
name = "{name}"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["publishable"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""


def scaffold_project(root: Path, license_name: str = "MIT") -> Path:
    """Fixed layout, so commands never need --repo or --templates-dir."""
    name = root.name
    root.mkdir(parents=True, exist_ok=True)
    for directory in ("src", "templates", "configs", "tests", "docs"):
        (root / directory).mkdir(exist_ok=True)
        (root / directory / ".gitkeep").touch()
    (root / "README.md").write_text(README.format(name=name))
    (root / "CITATION.cff").write_text(CITATION.format(name=name))
    (root / "LICENSE").write_text(MIT if license_name == "MIT" else f"{license_name}\n")
    (root / "pyproject.toml").write_text(PYPROJECT.format(name=name))
    (root / ".gitignore").write_text(GITIGNORE)
    (root / ".env.example").write_text("# Credential variable NAMES only, never values\n")
    if not (root / ".git").exists():
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(
            # gpgsign=false so scaffolding cannot hang or fail on a machine that
            # has commit signing configured globally.
            ["git", "-c", "user.email=you@example.com", "-c", "user.name=you",
             "-c", "commit.gpgsign=false",
             "commit", "-qm", "Scaffold a publishable experiment repository"],
            cwd=root, check=True,
        )
    return root
````

- [ ] **Step 4: Implement the generators**

```python
# src/publishable/generators/experiment.py
"""`generate experiment` — always creates, never wraps. Greenfield only."""

from pathlib import Path

from publishable.errors import ContractError
from publishable.materialize import materialize_config
from publishable.templates.registry import get_template

STARTER_STEP = '''\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        return {{"scaffold_ok": True}}      # TODO: replace with your analysis
'''

EXPERIMENT_PY = '''\
# src/{pkg}/experiment.py — order, nothing else
from publishable import BaseExperiment

from .steps.step01_summarize_units import Step as SummarizeUnits

STEPS = [SummarizeUnits]


class {cls}(BaseExperiment):
    # Order, nothing else. Each step declares its own scope; core derives
    # the execution plan from that. Reordering here IS reordering the pipeline.
    steps = STEPS
'''


def package_name(experiment: str) -> str:
    return experiment.replace("-", "_")


def class_name(experiment: str) -> str:
    return "".join(part.capitalize() for part in experiment.split("-")) + "Experiment"


def generate_experiment(
    *, repo_root: Path, name: str, template_name: str, input_dir: str, output_dir: str
) -> Path:
    template = get_template(template_name)
    if template is None:
        raise ContractError(
            f"no installed template registers `{template_name}`", code="E-TEMPLATE-UNKNOWN"
        )
    root = repo_root.resolve()
    for label, raw in (("input_dir", input_dir), ("output_dir", output_dir)):
        resolved = Path(raw).expanduser().resolve()
        if resolved == root or root in resolved.parents:
            raise ContractError(
                f"{label} {resolved} resolves inside the git repository at {root}",
                code="E-DATA-IN-REPO",
            )

    pkg = package_name(name)
    entrypoint = f"{pkg}.experiment:{class_name(name)}"
    pkg_dir = repo_root / "src" / pkg
    (pkg_dir / "steps").mkdir(parents=True, exist_ok=False)
    (pkg_dir / "__init__.py").touch()
    (pkg_dir / "steps" / "__init__.py").touch()
    (pkg_dir / "steps" / "step01_summarize_units.py").write_text(
        STARTER_STEP.format(pkg=pkg)
    )
    (pkg_dir / "experiment.py").write_text(
        EXPERIMENT_PY.format(pkg=pkg, cls=class_name(name))
    )

    config_path = repo_root / "configs" / name / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        materialize_config(
            template=template, template_name=template_name, name=name,
            input_dir=input_dir, output_dir=output_dir, entrypoint=entrypoint,
        )
    )
    return config_path
```

```python
# src/publishable/generators/step.py
"""`generate step` — the next-numbered file, registered in order."""

from pathlib import Path

from publishable.errors import ContractError
from publishable.generators.experiment import package_name

STEP_PY = '''\
from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        return {{}}      # TODO: implement {step_name}
'''


def generate_step(*, repo_root: Path, experiment: str, step_name: str) -> Path:
    pkg = package_name(experiment)
    steps_dir = repo_root / "src" / pkg / "steps"
    if not steps_dir.is_dir():
        raise ContractError(
            f"no experiment package at src/{pkg}/", code="E-EXPERIMENT-UNKNOWN"
        )
    existing = sorted(steps_dir.glob("step[0-9][0-9]_*.py"))
    number = len(existing) + 1
    path = steps_dir / f"step{number:02d}_{step_name}.py"
    path.write_text(STEP_PY.format(step_name=step_name))

    experiment_py = repo_root / "src" / pkg / "experiment.py"
    text = experiment_py.read_text()
    module = path.stem
    cls = "".join(part.capitalize() for part in step_name.split("_"))
    text = text.replace(
        "\nSTEPS = [",
        f"\nfrom .steps.{module} import Step as {cls}\n\nSTEPS = [",
    ).replace("STEPS = [", f"STEPS = [{cls}, ", 1)
    text = text.replace(f"STEPS = [{cls}, ]", f"STEPS = [{cls}]")
    experiment_py.write_text(_reorder(text, cls))
    return path


def _reorder(text: str, cls: str) -> str:
    """Keep the new step last in the ordered list rather than first."""
    import re

    match = re.search(r"STEPS = \[(.*?)\]", text, re.S)
    if not match:
        return text
    names = [n.strip() for n in match.group(1).split(",") if n.strip()]
    names = [n for n in names if n != cls] + [cls]
    return text[: match.start(1)] + ", ".join(names) + text[match.end(1) :]
```

`src/publishable/generators/__init__.py` is an empty file. `src/publishable/readme_templates/` gets an empty `__init__.py` and nothing else in S1: the scaffolded README, CITATION.cff and LICENSE live as string constants in `scaffold.py` while there are only three of them. They move into `readme_templates/` as files when `publishable docs` needs to rewrite managed regions, which is a hardening slice.

- [ ] **Step 5: Run and verify green**

Run: `uv run pytest tests/test_scaffold.py -v`
Expected: 6 passed.

- [ ] **Step 6: Commit**

```bash
git add src/publishable/scaffold.py src/publishable/generators \
        src/publishable/readme_templates tests/test_scaffold.py
git commit -m "Scaffold a repository whose first run already works"
```

---

### Task 17: The CLI, the acceptance test, and the `CLAUDE.md` rewrite

**Files:**
- Create: `src/publishable/cli.py`, `tests/test_acceptance.py`
- Modify: `CLAUDE.md`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: everything above.
- Produces: `main(argv: list[str] | None = None) -> int`; `command_run(config_path: Path) -> int` implementing the ten phases.

- [ ] **Step 1: Write the failing CLI test**

```python
# tests/test_cli.py
from pathlib import Path

from publishable.cli import main
from publishable.diagnostics import EXIT_INVOCATION, EXIT_WRONG


def test_an_unknown_command_is_an_invocation_error(capsys):
    assert main(["frobnicate", "x"]) == EXIT_INVOCATION


def test_a_missing_argument_is_an_invocation_error():
    assert main(["run"]) == EXIT_INVOCATION


def test_run_on_a_path_with_no_repo_is_wrong_not_invalid(tmp_path: Path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("schema_version: '1.0'\n")
    assert main(["run", str(cfg)]) == EXIT_WRONG


def test_operation_commands_take_no_flags(capsys):
    assert main(["run", "cfg.yaml", "--allow-dirty"]) == EXIT_INVOCATION
```

- [ ] **Step 2: Run it and watch it fail**

Run: `uv run pytest tests/test_cli.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'publishable.cli'`

- [ ] **Step 3: Implement `cli.py`**

```python
# src/publishable/cli.py
"""Dispatch. Operation commands take paths and nothing else."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from publishable.config import Config
from publishable.diagnostics import (
    EXIT_FAILED,
    EXIT_INVOCATION,
    EXIT_OK,
    EXIT_PARTIAL,
    EXIT_WRONG,
    Collector,
)
from publishable.errors import PublishableError
from publishable.generators.experiment import generate_experiment
from publishable.generators.step import generate_step
from publishable.hashes import code_hash, design_digest, parameters_hash
from publishable.manifest import build_manifest, manifest_hash, verify_manifest
from publishable.provenance import find_repo_root, git_provenance
from publishable.replication import resolve_repeats
from publishable.run_identity import RunLock, allocate_run_dir, point_latest
from publishable.run_record import assemble_run_yaml, run_status
from publishable.runner import execute_plan
from publishable.scaffold import scaffold_project
from publishable.scope import build_plan
from publishable.uv_support import uv_lock_info
from publishable.validate import validate_config

OPERATION_COMMANDS = {"validate", "run"}


def _load_experiment(repo_root: Path, entrypoint: str):
    """Import the entrypoint class from the project's own src/ on sys.path.

    The package is purged from sys.modules first: two projects in one process
    can declare the same package name, and a cached module would silently hand
    back the other project's steps.
    """
    import importlib

    module_name, _, attr = entrypoint.partition(":")
    root_pkg = module_name.split(".", 1)[0]
    for cached in [m for m in sys.modules if m == root_pkg or m.startswith(root_pkg + ".")]:
        del sys.modules[cached]
    sys.path.insert(0, str(repo_root / "src"))
    try:
        module = importlib.import_module(module_name)
        return getattr(module, attr)()
    finally:
        sys.path.pop(0)


def command_validate(config_path: Path) -> int:
    c = Collector()
    validate_config(config_path, c)
    if c.findings:
        print(config_path)
        print(c.render())
    else:
        print(f"  ✓ config valid · {config_path}")
    return c.exit_code()


def command_run(config_path: Path) -> int:
    c = Collector()
    doc = validate_config(config_path, c)          # phases 1–2
    if c.findings:
        print(config_path)
        print(c.render())
    if doc is None or c.has_errors:
        return EXIT_WRONG

    repo_root = find_repo_root(config_path)
    git = git_provenance(config_path, config_path)  # phase 3
    if git.code_dirty:
        print(
            "  error   E-CODE-DIRTY        src/** or templates/**\n"
            "          uncommitted changes; commit them first"
        )
        return EXIT_WRONG
    experiment = _load_experiment(repo_root, doc["entrypoint"])

    digest = design_digest(doc)                     # phase 5
    repeats = resolve_repeats(doc, digest)          # phase 4
    plan = build_plan(experiment, conditions=[(0, None)],
                      repeat_labels=[r.label for r in repeats if r.label])
    if not any(r.label for r in repeats):
        plan = build_plan(experiment, conditions=[(0, None)], repeat_labels=[""])

    input_dir = Path(doc["data"]["input_dir"]).expanduser()
    output_dir = Path(doc["data"]["output_dir"]).expanduser()
    ch = code_hash(repo_root)
    ph = parameters_hash(doc)
    manifest = build_manifest(input_dir, doc["data"]["input_manifest_policy"])

    run_dir = allocate_run_dir(output_dir, ch, datetime.now(timezone.utc))  # phase 6
    with RunLock(run_dir):
        (run_dir / "manifest").mkdir()
        (run_dir / "manifest" / "input.json").write_text(json.dumps(manifest, indent=2))
        (run_dir / "environment").mkdir()
        lock_path, lock_hash = uv_lock_info(repo_root)
        if lock_path:
            (run_dir / "environment" / "uv.lock").write_bytes(lock_path.read_bytes())

        results = execute_plan(                      # phase 7
            plan=plan, run_dir=run_dir, input_dir=input_dir,
            cfg=Config(doc), repeats=repeats, digest=digest,
        )

        status = run_status(results)                 # phase 8
        if verify_manifest(input_dir, manifest):
            status = "failed"

        provenance = {
            "git": {
                "repo_root": str(git.repo_root), "commit": git.commit,
                "branch": git.branch, "remote": git.remote,
                "code_dirty": git.code_dirty, "config_committed": git.config_committed,
            },
            "environment": {
                "manager": "uv",
                "python_version": ".".join(str(v) for v in sys.version_info[:3]),
                "uv_lock": "environment/uv.lock" if lock_path else None,
                "uv_lock_hash": lock_hash,
            },
            "apparatus": None,
            "input_manifest": "manifest/input.json",
            "input_manifest_hash": manifest_hash(manifest),
            "publishable_version": "0.1.0",
            "plugin_versions": {},
        }
        doc_out = assemble_run_yaml(                 # phase 9
            run_id=run_dir.name, status=status, config=doc,
            code_hash=ch, parameters_hash=ph, provenance=provenance, results=results,
        )
        (run_dir / "run.yaml").write_text(yaml.safe_dump(doc_out, sort_keys=False))
    point_latest(output_dir, run_dir)

    print(f"run.yaml → {run_dir / 'run.yaml'}")
    return {"completed": EXIT_OK, "partial": EXIT_PARTIAL}.get(status, EXIT_FAILED)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("usage: publishable <command> [args]", file=sys.stderr)
        return EXIT_INVOCATION
    command, rest = args[0], args[1:]
    try:
        if command in OPERATION_COMMANDS:
            if len(rest) != 1 or rest[0].startswith("-"):
                print(
                    f"`{command}` takes exactly one path and no flags", file=sys.stderr
                )
                return EXIT_INVOCATION
            path = Path(rest[0])
            return command_validate(path) if command == "validate" else command_run(path)
        if command == "new":
            if len(rest) != 1:
                return EXIT_INVOCATION
            scaffold_project(Path(rest[0]))
            return EXIT_OK
        if command in ("generate", "g", "init"):
            return _dispatch_generate(command, rest)
        print(f"unknown command `{command}`", file=sys.stderr)
        return EXIT_INVOCATION
    except PublishableError as exc:
        print(f"  error   {exc.code}  {exc}", file=sys.stderr)
        return EXIT_WRONG


def _dispatch_generate(command: str, rest: list[str]) -> int:
    opts: dict[str, str] = {}
    positional: list[str] = []
    i = 0
    while i < len(rest):
        if rest[i].startswith("--"):
            if i + 1 >= len(rest):
                return EXIT_INVOCATION
            opts[rest[i][2:]] = rest[i + 1]
            i += 2
        else:
            positional.append(rest[i])
            i += 1
    kind = "experiment" if command == "init" else (positional.pop(0) if positional else "")
    repo_root = find_repo_root(Path.cwd())
    if kind == "experiment":
        name = opts.get("name") or (positional[0] if positional else "")
        # Every option is checked before use: a missing one is a wrong invocation
        # (exit 2), never a KeyError traceback.
        missing = [f"--{o}" for o in ("template", "input-dir", "output-dir") if o not in opts]
        if not name or missing:
            print(
                "`generate experiment` needs a name plus "
                + ", ".join(missing or ["a name"]),
                file=sys.stderr,
            )
            return EXIT_INVOCATION
        generate_experiment(
            repo_root=repo_root, name=name, template_name=opts["template"],
            input_dir=opts["input-dir"], output_dir=opts["output-dir"],
        )
        return EXIT_OK
    if kind == "step":
        if len(positional) != 2:
            return EXIT_INVOCATION
        generate_step(repo_root=repo_root, experiment=positional[0], step_name=positional[1])
        return EXIT_OK
    return EXIT_INVOCATION
```

- [ ] **Step 4: Write the acceptance test**

```python
# tests/test_acceptance.py
"""S1's whole promise: `reference.md` § The starter step runs."""

import subprocess
from pathlib import Path

import yaml
from publishable.cli import main
from publishable.diagnostics import EXIT_OK, EXIT_WRONG


def build(tmp_path: Path) -> tuple[Path, Path, Path]:
    root = tmp_path / "my-study"
    data = tmp_path / "data"
    results = tmp_path / "results"
    data.mkdir()
    (data / "index.csv").write_text("patient_id\np1\np2\n")
    assert main(["new", str(root)]) == EXIT_OK
    from publishable.generators.experiment import generate_experiment

    cfg = generate_experiment(
        repo_root=root, name="cohort-pilot", template_name="generic",
        input_dir=str(data), output_dir=str(results),
    )
    doc = yaml.safe_load(cfg.read_text())
    doc["metadata"]["description"] = "the spine's acceptance run"
    doc["metadata"]["authors"] = ["Kyungjoon Lee"]
    cfg.write_text(yaml.safe_dump(doc))
    for args in (["add", "."], ["-c", "user.email=t@e.com", "-c", "user.name=t",
                                "commit", "-qm", "experiment"]):
        subprocess.run(["git", *args], cwd=root, check=True)
    return root, cfg, results


def test_scaffold_then_run_produces_a_real_record(tmp_path: Path):
    root, cfg, results = build(tmp_path)
    assert main(["validate", str(cfg)]) == EXIT_OK
    assert main(["run", str(cfg)]) == EXIT_OK

    run_dir = next(results.glob("run_*"))
    doc = yaml.safe_load((run_dir / "run.yaml").read_text())

    assert doc["status"] == "completed"
    assert doc["draft"] is False
    assert doc["code_hash"].startswith("sha256:")
    assert doc["parameters_hash"].startswith("sha256:")
    assert doc["provenance"]["input_manifest_hash"].startswith("sha256:")
    assert doc["config"]["metadata"]["name"] == "cohort-pilot"

    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True
    ).stdout.strip()
    assert doc["provenance"]["git"]["commit"] == commit
    assert doc["provenance"]["git"]["code_dirty"] is False

    assert run_dir.name.startswith("run_")
    assert run_dir.name.endswith(doc["code_hash"].split(":")[1][:7])
    assert (run_dir / "executions.jsonl").is_file()
    assert (run_dir / "manifest" / "input.json").is_file()
    assert not (run_dir / "lock").exists()


def test_five_seed_repeats_land_in_a_collapsed_layout(tmp_path: Path):
    _, cfg, results = build(tmp_path)
    assert main(["run", str(cfg)]) == EXIT_OK
    run_dir = next(results.glob("run_*"))
    assert not (run_dir / "conditions").exists(), "no sweep means no conditions level"
    repeat_dirs = sorted(p.name for p in run_dir.glob("seed*") if p.is_dir())
    assert len(repeat_dirs) == 5
    doc = yaml.safe_load((run_dir / "run.yaml").read_text())
    per_repeat = doc["results"]["conditions"][0]["per_repeat"]["step01_summarize_units"]
    assert len(per_repeat) == 5
    assert all(v == {"scaffold_ok": True} for v in per_repeat.values())


def test_run_refuses_a_dirty_code_tree(tmp_path: Path):
    root, cfg, _ = build(tmp_path)
    (root / "src" / "cohort_pilot" / "experiment.py").write_text("# edited\n")
    assert main(["run", str(cfg)]) == EXIT_WRONG


def test_run_refuses_data_inside_the_repo(tmp_path: Path):
    root, cfg, _ = build(tmp_path)
    doc = yaml.safe_load(cfg.read_text())
    doc["data"]["output_dir"] = str(root / "results")
    cfg.write_text(yaml.safe_dump(doc))
    assert main(["run", str(cfg)]) == EXIT_WRONG
```

- [ ] **Step 5: Run the whole suite**

Run: `uv run pytest -v && uv run ruff check . && uv run mypy`
Expected: every test passes, no lint findings, no type errors.

- [ ] **Step 6: Rewrite `CLAUDE.md`'s status section**

Replace the section headed `## Repository status: specification only, no implementation` — from that heading down to (but not including) `## The documents` — with:

```markdown
## Repository status: specification and implementation

This repository holds both the normative specification and the tool it specifies.

- `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md` and
  `docs/reference.md` are **the four documents**. They are normative and they lead.
- `src/publishable/` is the implementation. It follows the documents. Where it cannot
  follow them, **the document changes first** — record the gap in
  `docs/superpowers/spec-defects.md` rather than diverging silently.

**Commands:**

| Task | Command |
|---|---|
| Tests | `uv run pytest` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |
| Types | `uv run mypy` |

`docs/reference.md` § Package layout describes a tree that now **partially** exists.
Modules not yet built are still planned, and the slices that build them are listed in
`docs/superpowers/specs/2026-08-08-implementation-spine-design.md`.
```

Everything else in `CLAUDE.md` is untouched and still governs: the invariants, both
consistency passes, the worked example, the documentation conventions, and the
feasibility-analysis procedure.

- [ ] **Step 7: Run the repo's own mechanical consistency pass**

Write a throwaway fence-aware script per `CLAUDE.md` § Checking consistency after any `*.md` edit and confirm links, anchors, tables and whitespace are clean across all tracked `*.md`. Then grep every tracked `*.md` for the strings just removed — `specification only, no implementation` and `the binary does not exist here` — and confirm neither survives.

- [ ] **Step 8: Commit**

```bash
git add src/publishable/cli.py tests/test_cli.py tests/test_acceptance.py CLAUDE.md
git commit -m "Make the starter step run, and say so in CLAUDE.md"
```

---

## Definition of done for S1

- [ ] `uv run pytest` green, including `tests/test_acceptance.py`.
- [ ] `uv run ruff check .` and `uv run mypy` clean.
- [ ] Every `E-`/`W-` identifier defined in `src/` has a test that produces it.
- [ ] `CLAUDE.md` no longer claims the repo is specification-only.
- [ ] `docs/superpowers/spec-defects.md` holds every gap found, each naming the document
      and section that governs it.
- [ ] `runner.py`'s absence from `reference.md` § Package layout is recorded in the ledger
      for the S5 checkpoint — **not** applied to `reference.md` yet.
