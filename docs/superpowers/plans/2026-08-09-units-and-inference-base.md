# Units and the Inference Base (S2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `n` mean something — a metric recorded per unit carries an interval computed from the units themselves, and the four attrition counts reconcile exactly.

**Architecture:** Two new modules on top of merged S1. `units.py` resolves a roster and owns the frozen `Unit` and the four-operation `UnitList`. `stats.py` is pure: a collapsed table in, values and intervals out. `artifacts.py` gains recording and writes the per-execution tables; `runner.py` gains attrition tracking and one named early stop.

**Tech Stack:** Python 3.11+, PyYAML, **numpy, scipy, pyarrow** (new), pytest, ruff, mypy, uv.

## Global Constraints

- Python `requires-python = ">=3.11"`.
- Runtime dependencies after this slice: `pyyaml`, `numpy`, `scipy`, `pyarrow`. Add nothing else.
- `src/` layout; import root is `publishable`; only `src/publishable/__init__.py` is public API.
- Every error identifier starts `E-`, every warning `W-`. **Every identifier must have a test that produces it.**
- `ruff` line-length 100, select `["E","F","I","UP","B"]`; `mypy` strict over `src/`.
- `×` not `x` for multiplication in prose and comments.
- The four documents in `docs/` are NORMATIVE. Where code cannot follow them, stop and record it in `docs/superpowers/spec-defects.md` rather than diverging silently.
- **Unimplemented must mean refused, never silently ignored.** This is S1's hardest-won lesson: a declared `sweep` was being dropped while the run reported success.

## Existing interfaces this slice builds on

Read these before starting; do not reimplement them.

| Symbol | Signature |
|---|---|
| `errors` | `PublishableError(msg, *, code)`, `ContractError`, `ArtifactError`, `ArtifactExistsError` |
| `diagnostics` | `Collector.error(code, path, msg)` / `.warn(...)` / `.findings` / `.has_errors` / `.exit_code()` / `.render()`; `EXIT_OK/WRONG/INVOCATION/PARTIAL/FAILED/EXTERNAL` |
| `artifacts.StepIO` | `__init__(*, step_dir, input_dir, run_dir)`; `.path(name)`, `.exists(name)`, `.write(name, obj)`, `.append(name, record)`, `.read_input(relpath)`, `.read_upstream(step, name)`; module tables `WRITERS` / `READERS` keyed by suffix, resolved via `_suffix_for` |
| `runner` | `ExecutionResult(execution, status, started_at, wall_seconds, returned, error)`; `execute_plan(*, plan, run_dir, input_dir, cfg, repeats, digest) -> list[ExecutionResult]`; `step_dir_for(run_dir, execution, collapse_repeats)` |
| `run_record` | `assemble_run_yaml(*, run_id, status, config, code_hash, parameters_hash, provenance, results, repeats, draft=False)`; `run_status(results)` |
| `validate` | `validate_config(config_path, c) -> dict \| None`; internals `_check_metadata`, `_check_entrypoint`, `_check_parameters`, `_check_versions`, `_check_data`, `_check_replication`, `_check_unimplemented` |
| `scope` | `Execution(step_cls, step_name, scope, condition_index, condition_label, repeat_label)`; `build_plan(experiment, conditions, repeat_labels)` |
| `replication` | `Repeat(kind, label, seed)`; `resolve_repeats(config, digest)` |
| `hashes` | `code_hash(root)`, `parameters_hash(cfg)`, `design_digest(cfg)`, `short(h)` — all pure, returning `"sha256:<hex>"` |

## File Structure

| File | Responsibility |
|---|---|
| `src/publishable/units.py` *(new)* | `Unit`, `UnitList`, `resolve_units`, `units_hash` |
| `src/publishable/stats.py` *(new)* | **Pure.** `t_over_units`, `summarize_step` — no filesystem, no config parsing |
| `src/publishable/artifacts.py` | `io.units`, `io.record`, `io.skip`, `io.finalize()` writing the per-execution tables |
| `src/publishable/runner.py` | Attrition recomputation; the one named early stop |
| `src/publishable/validate.py` | Retire one refusal, add seven; resolve the roster for real unit checks |
| `src/publishable/materialize.py` | Restore the `data.units` block |
| `src/publishable/cli.py` · `run_record.py` | Resolve and hash the roster; carry `n`, `basis`, `ci95`, `method` into the record |

---

### Task 1: Dependencies and `stats.py`

**Files:**
- Modify: `pyproject.toml`
- Create: `src/publishable/stats.py`
- Test: `tests/test_stats.py`

**Interfaces:**
- Consumes: nothing. This module is pure and can be tested with no repository, run directory, or config.
- Produces: `Interval(low: float, high: float, method: str)` frozen dataclass; `t_over_units(values: Sequence[float], confidence: float = 0.95) -> Interval | None`; `mean_of(values) -> float | None`.

- [ ] **Step 1: Add the three dependencies**

In `pyproject.toml`, `[project].dependencies` becomes:

```toml
dependencies = ["pyyaml>=6.0", "numpy>=1.26", "scipy>=1.11", "pyarrow>=15.0"]
```

Run `uv sync`, then `uv run python -c "import numpy, scipy.stats, pyarrow; print('ok')"`.

- [ ] **Step 2: Write the failing tests**

```python
# tests/test_stats.py
import math

import pytest
from publishable.stats import Interval, mean_of, t_over_units


def test_interval_matches_a_published_critical_value():
    """t(0.975, df=9) = 2.262. Ten values, mean 10, sample sd exactly 1."""
    values = [10 + d for d in (-1.5, -1.5, -0.5, -0.5, 0.0, 0.0, 0.5, 0.5, 1.5, 1.5)]
    n = len(values)
    sd = math.sqrt(sum((v - 10) ** 2 for v in values) / (n - 1))
    expected_half = 2.262 * sd / math.sqrt(n)
    iv = t_over_units(values)
    assert iv is not None
    assert iv.method == "t_over_units"
    assert abs((iv.high - iv.low) / 2 - expected_half) < 1e-3
    assert abs((iv.low + iv.high) / 2 - 10) < 1e-12


def test_interval_is_hand_checkable_on_a_tiny_dataset():
    """values [1, 2, 3, 4]: mean 2.5, sample sd sqrt(5/3)=1.29099,
    sem 0.645497, t(0.975, df=3)=3.182, half-width 2.0540."""
    iv = t_over_units([1.0, 2.0, 3.0, 4.0])
    assert iv is not None
    assert abs(iv.low - (2.5 - 2.0540)) < 1e-3
    assert abs(iv.high - (2.5 + 2.0540)) < 1e-3


def test_the_t_interval_is_wider_than_normal_and_converges():
    """The check that would catch shipping z by mistake."""
    from statistics import NormalDist

    def normal_half(vals):
        n = len(vals)
        m = sum(vals) / n
        sd = math.sqrt(sum((v - m) ** 2 for v in vals) / (n - 1))
        return NormalDist().inv_cdf(0.975) * sd / math.sqrt(n)

    small = [float(i % 7) for i in range(8)]
    large = [float(i % 7) for i in range(4000)]
    small_iv, large_iv = t_over_units(small), t_over_units(large)
    assert small_iv is not None and large_iv is not None
    small_ratio = ((small_iv.high - small_iv.low) / 2) / normal_half(small)
    large_ratio = ((large_iv.high - large_iv.low) / 2) / normal_half(large)
    assert small_ratio > 1.15, "t must be materially wider than z at n=8"
    assert 1.0 < large_ratio < 1.002, "t must converge to z as n grows"


@pytest.mark.parametrize("values", [[], [3.0]])
def test_fewer_than_two_values_has_no_interval(values):
    """df = n - 1, so one value has no dispersion to describe."""
    assert t_over_units(values) is None


def test_zero_variance_yields_a_degenerate_but_real_interval():
    iv = t_over_units([5.0, 5.0, 5.0])
    assert iv is not None and iv.low == iv.high == 5.0


def test_mean_of_is_none_for_an_empty_sequence():
    assert mean_of([]) is None
    assert mean_of([1.0, 2.0]) == 1.5


def test_confidence_widens_the_interval():
    narrow = t_over_units([1.0, 2.0, 3.0, 4.0], confidence=0.80)
    wide = t_over_units([1.0, 2.0, 3.0, 4.0], confidence=0.99)
    assert narrow is not None and wide is not None
    assert (wide.high - wide.low) > (narrow.high - narrow.low)
```

- [ ] **Step 3: Run and watch them fail**

Run: `uv run pytest tests/test_stats.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'publishable.stats'`

- [ ] **Step 4: Implement `stats.py`**

```python
# src/publishable/stats.py
"""Statistics over the per-unit table.

Pure by design: a collapsed table in, values and intervals out. No filesystem,
no config parsing, no git — a statistical claim is the last thing that should be
entangled with I/O, and purity is what lets this be tested exhaustively.

See docs/reference.md § Statistical reporting.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass

from scipy import stats as _scipy_stats


@dataclass(frozen=True)
class Interval:
    low: float
    high: float
    method: str


def mean_of(values: Sequence[float]) -> float | None:
    return sum(values) / len(values) if values else None


def t_over_units(values: Sequence[float], confidence: float = 0.95) -> Interval | None:
    """Student's t on the per-unit values, df = completed units − 1.

    Returns None below two values: df would be zero and there is no dispersion
    to describe. Reporting a point with no interval is honest; inventing one is not.
    """
    n = len(values)
    if n < 2:
        return None
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / (n - 1)
    sem = math.sqrt(variance) / math.sqrt(n)
    critical = float(_scipy_stats.t.ppf(1 - (1 - confidence) / 2, df=n - 1))
    half = critical * sem
    return Interval(low=mean - half, high=mean + half, method="t_over_units")
```

- [ ] **Step 5: Run and verify green**

Run: `uv run pytest tests/test_stats.py -v && uv run ruff check . && uv run mypy`
Expected: 8 passed, no lint findings, no type errors. If mypy objects to the scipy import, add `scipy` to a `[[tool.mypy.overrides]]` block with `ignore_missing_imports = true` rather than loosening strictness globally, and say so in your report.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock src/publishable/stats.py tests/test_stats.py
git commit -m "Compute an interval over units, not over executions"
```

---

### Task 2: `units.py` — resolution, the frozen `Unit`, the four-operation list

**Files:**
- Create: `src/publishable/units.py`
- Test: `tests/test_units.py`

**Interfaces:**
- Consumes: `ContractError`; `StepIO.read_input` is NOT used here — this module reads the input directory directly, because resolution runs at `validate` where no run directory or step exists.
- Produces: `Unit` frozen dataclass with `key: str`, `paths: tuple[str, ...]`, `attributes: dict[str, Any]`, attribute passthrough via `__getattr__`, hashable by `key`; `UnitList` supporting iterate / `len` / integer index / `.train`; `resolve_units(units_decl: dict, input_dir: Path) -> UnitList`; `units_hash(units: UnitList) -> str`; `RESERVED_FIELDS = ("key", "paths", "attributes")`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_units.py
from pathlib import Path

import pytest
from publishable import ContractError
from publishable.units import Unit, UnitList, resolve_units, units_hash


@pytest.fixture
def input_dir(tmp_path: Path) -> Path:
    d = tmp_path / "in"
    (d / "scans").mkdir(parents=True)
    (d / "index.csv").write_text("patient_id,label,site\np3,1,a\np1,0,b\np2,1,a\n")
    for name in ("b.dcm", "a.dcm"):
        (d / "scans" / name).write_bytes(b"\x00")
    (d / "top.dcm").write_bytes(b"\x00")
    return d


def test_a_table_resolves_in_row_order_not_sorted(input_dir: Path):
    units = resolve_units(
        {"from": "index.csv", "key": "patient_id", "attributes": ["label", "site"]}, input_dir
    )
    assert [u.key for u in units] == ["p3", "p1", "p2"], "row order is data, not cosmetic"
    assert len(units) == 3
    assert units[0].key == "p3"


def test_declared_attributes_are_readable_directly(input_dir: Path):
    units = resolve_units(
        {"from": "index.csv", "key": "patient_id", "attributes": ["label", "site"]}, input_dir
    )
    assert units[0].site == "a"
    assert units[0].attributes["label"] == "1"


def test_an_undeclared_column_is_not_an_attribute(input_dir: Path):
    units = resolve_units({"from": "index.csv", "key": "patient_id", "attributes": ["label"]},
                          input_dir)
    assert "site" not in units[0].attributes
    with pytest.raises(AttributeError):
        _ = units[0].site


def test_a_glob_resolves_lexicographically_with_the_path_as_key(input_dir: Path):
    units = resolve_units({"from": {"glob": "**/*.dcm"}, "key": "path"}, input_dir)
    assert [u.key for u in units] == ["scans/a.dcm", "scans/b.dcm", "top.dcm"]
    assert units[0].paths == ("scans/a.dcm",)


def test_a_non_recursive_glob_does_not_descend(input_dir: Path):
    units = resolve_units({"from": {"glob": "*.dcm"}, "key": "path"}, input_dir)
    assert [u.key for u in units] == ["top.dcm"]


def test_a_missing_key_column_is_refused(input_dir: Path):
    with pytest.raises(ContractError) as e:
        resolve_units({"from": "index.csv", "key": "subject_id"}, input_dir)
    assert e.value.code == "E-UNITS-KEY-MISSING"
    assert "subject_id" in str(e.value)


def test_a_missing_attribute_column_is_refused(input_dir: Path):
    with pytest.raises(ContractError) as e:
        resolve_units({"from": "index.csv", "key": "patient_id", "attributes": ["age"]}, input_dir)
    assert e.value.code == "E-UNITS-ATTR-MISSING"


def test_a_missing_table_is_refused(input_dir: Path):
    with pytest.raises(ContractError) as e:
        resolve_units({"from": "absent.csv", "key": "patient_id"}, input_dir)
    assert e.value.code == "E-UNITS-SOURCE-MISSING"


def test_duplicate_keys_are_refused_naming_the_offender(input_dir: Path):
    (input_dir / "dup.csv").write_text("patient_id\np1\np2\np1\n")
    with pytest.raises(ContractError) as e:
        resolve_units({"from": "dup.csv", "key": "patient_id"}, input_dir)
    assert e.value.code == "E-UNITS-KEY-DUPLICATE"
    assert "p1" in str(e.value)


@pytest.mark.parametrize("reserved", ["key", "paths", "attributes"])
def test_reserved_attribute_names_are_refused(input_dir: Path, reserved: str):
    (input_dir / "r.csv").write_text(f"patient_id,{reserved}\np1,x\n")
    with pytest.raises(ContractError) as e:
        resolve_units({"from": "r.csv", "key": "patient_id", "attributes": [reserved]}, input_dir)
    assert e.value.code == "E-UNITS-ATTR-RESERVED"


def test_a_unit_is_frozen_and_hashable_by_key():
    u = Unit(key="p1", paths=(), attributes={"label": "1"})
    with pytest.raises(Exception):
        u.key = "p2"  # type: ignore[misc]
    assert hash(u) == hash(Unit(key="p1", paths=(), attributes={"label": "0"}))


def test_the_unit_list_is_exactly_four_operations(input_dir: Path):
    units = resolve_units({"from": "index.csv", "key": "patient_id"}, input_dir)
    assert len(list(units)) == 3          # iterate, repeatably
    assert len(list(units)) == 3
    assert len(units) == 3                # len
    assert units[1].key == "p1"           # index
    for absent in ("append", "index", "count", "sort"):
        assert not hasattr(units, absent), f"{absent} would make this a list"
    # Exercise the operators, not just hasattr: protocol fallbacks make a
    # hasattr-only check pass green while slicing still returns a plain list.
    with pytest.raises(ContractError) as e:
        _ = units[0:2]
    assert e.value.code == "E-STEP-UNITS-CONTRACT"
    # `in` and `reversed` derive from the promised operations, so they are
    # deliberately permitted — see the ledger entry.
    assert units[0] in units
    assert len(list(reversed(units))) == 3


def test_train_raises_when_no_partition_is_declared(input_dir: Path):
    units = resolve_units({"from": "index.csv", "key": "patient_id"}, input_dir)
    with pytest.raises(ContractError) as e:
        _ = units.train
    assert e.value.code == "E-STEP-UNITS-UNAVAILABLE"


def test_units_hash_follows_order_and_content(input_dir: Path):
    a = resolve_units({"from": "index.csv", "key": "patient_id"}, input_dir)
    b = resolve_units({"from": "index.csv", "key": "patient_id"}, input_dir)
    assert units_hash(a) == units_hash(b)
    assert units_hash(a).startswith("sha256:")
    (input_dir / "index.csv").write_text("patient_id,label,site\np1,0,b\np3,1,a\np2,1,a\n")
    reordered = resolve_units({"from": "index.csv", "key": "patient_id"}, input_dir)
    assert units_hash(reordered) != units_hash(a), "order is part of the identity"
```

- [ ] **Step 2: Run and watch them fail**

Run: `uv run pytest tests/test_units.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'publishable.units'`

- [ ] **Step 3: Implement `units.py`**

```python
# src/publishable/units.py
"""The thing being measured. See docs/reference.md § Units.

Resolution runs at `validate` as well as at `run`, so this module reads
`input_dir` directly rather than through `io` — at validate time there is no run
directory and no step for an `io` to belong to.
"""

import csv
import hashlib
import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from publishable.errors import ContractError

RESERVED_FIELDS = ("key", "paths", "attributes")


@dataclass(frozen=True, eq=False)
class Unit:
    """Frozen, and hashable by `key`: one roster is resolved per run and shared."""

    key: str
    paths: tuple[str, ...] = ()
    attributes: dict[str, Any] = field(default_factory=dict)

    def __getattr__(self, name: str) -> Any:
        # Only reached when normal lookup fails, so it never shadows the three fields.
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return object.__getattribute__(self, "attributes")[name]
        except KeyError:
            raise AttributeError(
                f"{name!r} is not a declared attribute of unit {self.key!r}"
            ) from None

    def __hash__(self) -> int:
        return hash(self.key)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Unit) and other.key == self.key


class UnitList:
    """Iterate, len, index — plus `.train`. Deliberately not a list.

    A sequence that also promised slicing, membership and `.index` would just be a
    `list`, and core could never change what backs it without breaking every step.
    """

    def __init__(self, units: list[Unit], train: "UnitList | None" = None) -> None:
        self._units = units
        self._train = train

    def __iter__(self) -> Iterator[Unit]:
        return iter(self._units)

    def __len__(self) -> int:
        return len(self._units)

    def __getitem__(self, index: int) -> Unit:
        return self._units[index]

    @property
    def train(self) -> "UnitList":
        if self._train is None:
            raise ContractError(
                "`io.units.train` needs a `fold` repeat or a `data.units.holdout`; "
                "neither is declared, and an empty list would let a fit run on nothing",
                code="E-STEP-UNITS-UNAVAILABLE",
            )
        return self._train


def _rows_from_table(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _from_table(decl: dict[str, Any], input_dir: Path, source: str) -> list[Unit]:
    path = input_dir / source
    if not path.is_file():
        raise ContractError(
            f"`data.units.from` names {source}, which is not a file under {input_dir}",
            code="E-UNITS-SOURCE-MISSING",
        )
    rows = _rows_from_table(path)
    key_col = decl.get("key")
    attrs = list(decl.get("attributes") or [])
    columns = set(rows[0]) if rows else set()
    if key_col not in columns:
        raise ContractError(
            f"`data.units.key` names {key_col!r}, which {source} does not have "
            f"(columns: {', '.join(sorted(columns))})",
            code="E-UNITS-KEY-MISSING",
        )
    for name in attrs:
        if name in RESERVED_FIELDS:
            raise ContractError(
                f"`data.units.attributes` names {name!r}, which is a field of `Unit` itself; "
                f"{', '.join(RESERVED_FIELDS)} cannot also be attributes",
                code="E-UNITS-ATTR-RESERVED",
            )
        if name not in columns:
            raise ContractError(
                f"`data.units.attributes` names {name!r}, which {source} does not have",
                code="E-UNITS-ATTR-MISSING",
            )
    return [
        Unit(key=row[key_col], paths=(), attributes={a: row[a] for a in attrs})
        for row in rows
    ]


def _from_glob(pattern: str, input_dir: Path) -> list[Unit]:
    # Lexicographic over relative paths: filesystems walk directories differently,
    # and a roster whose order depends on that is not reproducible.
    rels = sorted(
        p.relative_to(input_dir).as_posix()
        for p in input_dir.glob(pattern)
        if p.is_file()
    )
    return [Unit(key=rel, paths=(rel,), attributes={}) for rel in rels]


def resolve_units(units_decl: dict[str, Any], input_dir: Path) -> UnitList:
    """Resolve the roster, preserving the order it was resolved in."""
    source = units_decl.get("from")
    if isinstance(source, str):
        units = _from_table(units_decl, input_dir, source)
    elif isinstance(source, dict) and "glob" in source:
        units = _from_glob(str(source["glob"]), input_dir)
    else:
        raise ContractError(
            f"`data.units.from` is {source!r}; expected a table name or {{glob: ...}}",
            code="E-UNITS-SOURCE-MISSING",
        )
    seen: dict[str, int] = {}
    for u in units:
        if u.key in seen:
            raise ContractError(
                f"`data.units.key` is not unique: {u.key!r} appears more than once",
                code="E-UNITS-KEY-DUPLICATE",
            )
        seen[u.key] = 1
    return UnitList(units)


def units_hash(units: UnitList) -> str:
    """Covers the list in resolved order — two runs that resolved the same units in a
    different sequence did not allocate the same trial."""
    payload = json.dumps(
        [{"key": u.key, "paths": list(u.paths), "attributes": u.attributes} for u in units],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()
```

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest tests/test_units.py -v && uv run ruff check . && uv run mypy`
Expected: 16 passed (the reserved-name test is parametrised three ways), clean lint and types.

- [ ] **Step 5: Commit**

```bash
git add src/publishable/units.py tests/test_units.py
git commit -m "Resolve a roster, and keep the order it was resolved in"
```

---

### Task 3: Retire one refusal, add seven

**Files:**
- Modify: `src/publishable/validate.py` (the `_check_unimplemented` function, and its `E-DATA-UNITS-UNSUPPORTED` block)
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: `Collector`.
- Produces: identifiers `E-DATA-ALLOCATION-UNSUPPORTED`, `E-DATA-ASSIGN-UNSUPPORTED`, `E-DATA-CLUSTER-UNSUPPORTED`, `E-DATA-WEIGHT-UNSUPPORTED`, `E-DATA-MEASUREMENTS-UNSUPPORTED`, `E-DATA-HOLDOUT-UNSUPPORTED`, `E-DATA-RESOLVER-UNSUPPORTED`. `E-DATA-UNITS-UNSUPPORTED` no longer exists anywhere.

**Why this task is separate:** retiring the blanket refusal is the moment the door S1 slammed could swing back open one level down. It gets its own reviewer gate.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_validate.py`. The file already has a `write_config` fixture and a `codes(path)` helper — reuse them.

```python
def test_a_plain_units_block_is_now_accepted(write_config):
    """The blanket refusal is retired: S2 resolves a roster."""
    found = codes(write_config({"data.units": {"from": "index.csv", "key": "patient_id"}}))
    assert "E-DATA-UNITS-UNSUPPORTED" not in found


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("allocation", "between", "E-DATA-ALLOCATION-UNSUPPORTED"),
        ("assign", {"arm": {"method": "random"}}, "E-DATA-ASSIGN-UNSUPPORTED"),
        ("cluster_by", "site", "E-DATA-CLUSTER-UNSUPPORTED"),
        ("weight_by", "sampling_weight", "E-DATA-WEIGHT-UNSUPPORTED"),
        ("measurements", {"by": "read_id"}, "E-DATA-MEASUREMENTS-UNSUPPORTED"),
        ("holdout", {"method": "random", "frac": 0.2}, "E-DATA-HOLDOUT-UNSUPPORTED"),
    ],
)
def test_each_unimplemented_units_subfield_is_refused_on_its_own(write_config, field, value, code):
    units = {"from": "index.csv", "key": "patient_id", field: value}
    assert code in codes(write_config({"data.units": units}))


def test_allocation_within_is_accepted_because_it_is_a_no_op_here(write_config):
    units = {"from": "index.csv", "key": "patient_id", "allocation": "within"}
    assert "E-DATA-ALLOCATION-UNSUPPORTED" not in codes(write_config({"data.units": units}))


def test_a_resolver_source_is_refused_until_plugins_exist(write_config):
    units = {"from": {"resolver": "plate_wells"}, "key": "well"}
    assert "E-DATA-RESOLVER-UNSUPPORTED" in codes(write_config({"data.units": units}))


def test_a_null_subfield_is_not_a_declaration(write_config):
    """`init` writes these as null; null must not trip a refusal."""
    units = {"from": "index.csv", "key": "patient_id",
             "cluster_by": None, "weight_by": None, "measurements": None, "holdout": None}
    found = codes(write_config({"data.units": units}))
    assert not [c for c in found if c.endswith("-UNSUPPORTED")]
```

- [ ] **Step 2: Run and watch them fail**

Run: `uv run pytest tests/test_validate.py -k units -v`
Expected: FAIL — the blanket `E-DATA-UNITS-UNSUPPORTED` still fires, and none of the seven exist.

- [ ] **Step 3: Replace the blanket block**

In `_check_unimplemented`, delete the `E-DATA-UNITS-UNSUPPORTED` block entirely and put this in its place:

```python
    units = (doc.get("data") or {}).get("units") or {}
    source = units.get("from")
    if isinstance(source, dict) and "resolver" in source:
        c.error(
            "E-DATA-RESOLVER-UNSUPPORTED",
            "data.units.from.resolver",
            f"names `{source['resolver']}`, but resolvers are plugin artifacts and the "
            "plugin registry is not implemented in this build; resolvers will be honored "
            "in a later slice. Use a table or a glob for now",
        )
    if units.get("allocation") not in (None, "within"):
        c.error(
            "E-DATA-ALLOCATION-UNSUPPORTED",
            "data.units.allocation",
            f"is `{units['allocation']}`, which needs a `sweep.groups` axis to say what the "
            "arms are; group axes are not implemented in this build. `within` is the "
            "supported value and is what a single-condition run means anyway",
        )
    for field, code in (
        ("assign", "E-DATA-ASSIGN-UNSUPPORTED"),
        ("cluster_by", "E-DATA-CLUSTER-UNSUPPORTED"),
        ("weight_by", "E-DATA-WEIGHT-UNSUPPORTED"),
        ("measurements", "E-DATA-MEASUREMENTS-UNSUPPORTED"),
        ("holdout", "E-DATA-HOLDOUT-UNSUPPORTED"),
    ):
        # `init` writes these as null; only a real declaration is refused.
        if units.get(field):
            c.error(
                code,
                f"data.units.{field}",
                "is specified but not implemented in this build — it is read by nothing "
                "here, and a declaration that changes no behavior is the failure this "
                "refusal exists to prevent; it will be honored in a later slice",
            )
```

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest tests/test_validate.py -v && uv run ruff check . && uv run mypy`
Expected: all pass. Then confirm the retired identifier is gone everywhere:
`grep -rn "E-DATA-UNITS-UNSUPPORTED" src/ tests/` — expected: no matches.

- [ ] **Step 5: Commit**

```bash
git add src/publishable/validate.py tests/test_validate.py
git commit -m "Refuse each units sub-field on its own, not the block as a whole"
```

---

### Task 4: `validate` resolves the roster

**Files:**
- Modify: `src/publishable/validate.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: `resolve_units`, `RESERVED_FIELDS` from `units.py`; `ContractError`.
- Produces: `_check_units(doc, c) -> None`, called from `validate_config` after `_check_data`. Every `ContractError` `resolve_units` raises becomes a diagnostic with the SAME identifier, so the code a user sees is identical whether resolution failed at validate or at run.

**Why resolution happens here:** § Where units come from is explicit that it runs at `validate` and `dry-run`, not only at `run`, because every unit check is a question about the resolved table. That is what makes key-uniqueness a pre-flight check rather than a four-hours-in surprise.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_resolvable_roster_validates_clean(write_config, tmp_path):
    (tmp_path / "input" / "index.csv").write_text("patient_id,label\np1,0\np2,1\n")
    assert codes(write_config({"data.units": {"from": "index.csv", "key": "patient_id",
                                              "attributes": ["label"]}})) == set()


def test_duplicate_keys_are_reported_as_a_diagnostic_not_an_exception(write_config, tmp_path):
    (tmp_path / "input" / "index.csv").write_text("patient_id\np1\np1\n")
    found = codes(write_config({"data.units": {"from": "index.csv", "key": "patient_id"}}))
    assert "E-UNITS-KEY-DUPLICATE" in found


def test_a_missing_key_column_is_reported_at_validate(write_config, tmp_path):
    (tmp_path / "input" / "index.csv").write_text("subject_id\ns1\n")
    assert "E-UNITS-KEY-MISSING" in codes(
        write_config({"data.units": {"from": "index.csv", "key": "patient_id"}})
    )


def test_a_reserved_attribute_name_is_reported_at_validate(write_config, tmp_path):
    (tmp_path / "input" / "index.csv").write_text("patient_id,paths\np1,x\n")
    assert "E-UNITS-ATTR-RESERVED" in codes(
        write_config({"data.units": {"from": "index.csv", "key": "patient_id",
                                     "attributes": ["paths"]}})
    )


def test_no_units_block_still_validates_clean(write_config):
    """`data.units` is optional; a pipeline with no unit table is legal."""
    assert codes(write_config()) == set()
```

- [ ] **Step 2: Run and watch them fail**

Run: `uv run pytest tests/test_validate.py -k roster -v`
Expected: FAIL — resolution is not wired in, so a duplicate key validates clean.

- [ ] **Step 3: Implement `_check_units` and call it**

```python
def _check_units(doc: dict[str, Any], c: Collector) -> None:
    """Resolve the roster so unit checks are real rather than deferred to run time.

    A `ContractError` from resolution becomes a diagnostic carrying the SAME
    identifier, so a user sees one code for one problem whether it surfaced here
    or during a run.
    """
    data = doc.get("data") or {}
    units_decl = data.get("units")
    if not units_decl:
        return
    input_dir = data.get("input_dir")
    if not input_dir:
        return  # already reported by _check_data
    try:
        resolve_units(units_decl, Path(input_dir).expanduser())
    except ContractError as exc:
        c.error(exc.code, "data.units", str(exc))
```

Call it from `validate_config` immediately after `_check_data(doc, config_path, c)`, and add the imports:

```python
from publishable.errors import ContractError
from publishable.units import resolve_units
```

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest tests/test_validate.py -v && uv run ruff check . && uv run mypy`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/publishable/validate.py tests/test_validate.py
git commit -m "Resolve the roster at validate, so key checks are pre-flight"
```

---

### Task 5: Restore `data.units` to the generated config

**Files:**
- Modify: `src/publishable/materialize.py`
- Test: `tests/test_materialize.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: the emitted `data:` block gains a `units:` sub-block.

- [ ] **Step 1: Write the failing test**

```python
def test_the_generated_config_declares_a_unit_roster():
    doc = yaml.safe_load(rendered())
    units = doc["data"]["units"]
    assert units["from"] == "index.csv"
    assert units["key"] == "patient_id"
    assert units["attributes"] == []
    assert units["allocation"] == "within"
    for optional in ("cluster_by", "weight_by", "measurements", "holdout"):
        assert units[optional] is None, f"{optional} must be null, not absent or declared"


def test_the_generated_units_block_carries_its_comments():
    text = rendered()
    assert "# index.csv | {glob: \"*.dcm\"}" in text
    assert "# within | between" in text
```

- [ ] **Step 2: Run and watch them fail**

Run: `uv run pytest tests/test_materialize.py -k units -v`
Expected: FAIL — `KeyError: 'units'`

- [ ] **Step 3: Emit the block**

In `materialize_config`, replace the `data:` lines with:

```python
        "data:",
        f"  input_dir: {input_dir}          # must be OUTSIDE the repo — enforced",
        f"  output_dir: {output_dir}",
        "  input_manifest_policy: hash_all  # hash_all | hash_index | none",
        "  units:",
        '    from: index.csv                # index.csv | {glob: "*.dcm"}',
        "    key: patient_id                # stable, unique identity",
        "    attributes: []                 # available for stratification and reporting",
        "    allocation: within             # within | between",
        "    cluster_by: null               # e.g. site, when units aren't independent",
        "    weight_by: null                # e.g. sampling_weight, when the sample is enriched",
        "    measurements: null             # e.g. {by: read_id, collapse: mean}",
        "    holdout: null                  # optional single fixed train/test split",
```

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest tests/test_materialize.py -v`
Expected: all pass. Then confirm the generated config still validates against the seven new refusals — a generated config that its own validator rejects would be the embarrassment S1 caught in the generators:

```bash
uv run python -c "
import yaml
from publishable.materialize import materialize_config
from publishable.templates.registry import get_template
d = yaml.safe_load(materialize_config(template=get_template('generic'), template_name='generic',
    name='c', input_dir='/i', output_dir='/o', entrypoint='c:C'))
u = d['data']['units']
assert u['allocation'] == 'within' and u['cluster_by'] is None
print('generated units block is refusal-clean')"
```

- [ ] **Step 5: Commit**

```bash
git add src/publishable/materialize.py tests/test_materialize.py
git commit -m "Put the unit roster back in the config init writes"
```

---

### Task 6: `io.units`, `io.record`, `io.skip`

**Files:**
- Modify: `src/publishable/artifacts.py`
- Test: `tests/test_artifacts.py`

**Interfaces:**
- Consumes: `UnitList` from `units.py`; `ContractError`.
- Produces: `StepIO.__init__` gains `units: UnitList | None = None`; properties/methods `io.units -> UnitList` (raises `E-STEP-UNITS-UNAVAILABLE` when the roster is absent), `io.record(unit_key: str, values: dict[str, Any]) -> None`, `io.skip(unit_key: str, reason: str) -> None`; read-only accessors `io.recorded_keys -> set[str]`, `io.skipped -> dict[str, str]`.

**Recording is append-only and first-write-wins**, matching `io.append`'s documented idempotency: a second `io.record` under a key already present is discarded rather than overwriting.

- [ ] **Step 1: Write the failing tests**

```python
def test_units_raises_when_no_roster_was_declared(io: StepIO):
    with pytest.raises(ContractError) as e:
        _ = io.units
    assert e.value.code == "E-STEP-UNITS-UNAVAILABLE"


def test_record_and_skip_accumulate_by_key(tmp_path: Path):
    from publishable.units import Unit, UnitList
    roster = UnitList([Unit(key=f"p{i}") for i in range(3)])
    sd = tmp_path / "run" / "s"; sd.mkdir(parents=True); (tmp_path / "in").mkdir()
    io = StepIO(step_dir=sd, input_dir=tmp_path / "in", run_dir=tmp_path / "run", units=roster)
    assert len(io.units) == 3
    io.record("p0", {"pred": 0.5, "truth": 1})
    io.skip("p1", "no baseline visit")
    assert io.recorded_keys == {"p0"}
    assert io.skipped == {"p1": "no baseline visit"}


def test_a_second_record_under_one_key_is_discarded_first_write_wins(tmp_path: Path):
    from publishable.units import Unit, UnitList
    sd = tmp_path / "run" / "s"; sd.mkdir(parents=True); (tmp_path / "in").mkdir()
    io = StepIO(step_dir=sd, input_dir=tmp_path / "in", run_dir=tmp_path / "run",
                units=UnitList([Unit(key="p0")]))
    io.record("p0", {"v": 1})
    io.record("p0", {"v": 2})
    assert io.rows() == [{"unit": "p0", "v": 1}]


def test_recording_a_key_not_in_the_roster_is_refused(tmp_path: Path):
    from publishable.units import Unit, UnitList
    sd = tmp_path / "run" / "s"; sd.mkdir(parents=True); (tmp_path / "in").mkdir()
    io = StepIO(step_dir=sd, input_dir=tmp_path / "in", run_dir=tmp_path / "run",
                units=UnitList([Unit(key="p0")]))
    with pytest.raises(ContractError) as e:
        io.record("ghost", {"v": 1})
    assert e.value.code == "E-STEP-UNIT-UNKNOWN"


def test_a_unit_cannot_be_both_recorded_and_skipped(tmp_path: Path):
    from publishable.units import Unit, UnitList
    sd = tmp_path / "run" / "s"; sd.mkdir(parents=True); (tmp_path / "in").mkdir()
    io = StepIO(step_dir=sd, input_dir=tmp_path / "in", run_dir=tmp_path / "run",
                units=UnitList([Unit(key="p0")]))
    io.record("p0", {"v": 1})
    with pytest.raises(ContractError) as e:
        io.skip("p0", "changed my mind")
    assert e.value.code == "E-STEP-UNIT-SETTLED"
```

- [ ] **Step 2: Run and watch them fail**

Run: `uv run pytest tests/test_artifacts.py -k "record or skip or units" -v`
Expected: FAIL — `StepIO.__init__() got an unexpected keyword argument 'units'`

- [ ] **Step 3: Implement**

Add to `StepIO.__init__` and the class body:

```python
    def __init__(
        self,
        *,
        step_dir: Path,
        input_dir: Path,
        run_dir: Path,
        units: "UnitList | None" = None,
    ) -> None:
        self.step_dir = step_dir
        self.input_dir = input_dir
        self.run_dir = run_dir
        self.resumed = False
        self.recorded_keys: set[str] = set()
        self._units = units
        self._rows: dict[str, dict[str, Any]] = {}
        self.skipped: dict[str, str] = {}

    @property
    def units(self) -> "UnitList":
        if self._units is None:
            raise ContractError(
                "`io.units` needs a `data.units` declaration; none is present, and an "
                "empty list would let a step report results about nothing",
                code="E-STEP-UNITS-UNAVAILABLE",
            )
        return self._units

    def _settle(self, unit_key: str) -> None:
        if self._units is not None and unit_key not in {u.key for u in self._units}:
            raise ContractError(
                f"{unit_key!r} is not in this execution's roster",
                code="E-STEP-UNIT-UNKNOWN",
            )
        if unit_key in self._rows or unit_key in self.skipped:
            raise ContractError(
                f"{unit_key!r} was already recorded or skipped in this execution",
                code="E-STEP-UNIT-SETTLED",
            )

    def record(self, unit_key: str, values: dict[str, Any]) -> None:
        """Append one row to this step's per-unit table, keyed by unit."""
        if unit_key in self._rows:
            return  # first write wins, matching io.append's idempotency
        self._settle(unit_key)
        self._rows[unit_key] = {"unit": unit_key, **values}
        self.recorded_keys.add(unit_key)

    def skip(self, unit_key: str, reason: str) -> None:
        """Declare that this unit admits no result by design — `ineligible`, not `failed`."""
        self._settle(unit_key)
        self.skipped[unit_key] = reason

    def rows(self) -> list[dict[str, Any]]:
        return list(self._rows.values())
```

Import `UnitList` under `TYPE_CHECKING` to avoid a cycle, and `ContractError` normally.

Note the ordering: `record` returns early on a duplicate BEFORE `_settle` would raise `E-STEP-UNIT-SETTLED`, because first-write-wins and settled-conflict are different rules — a repeated `record` is idempotent, while `skip` after `record` is a contradiction.

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest tests/test_artifacts.py -v && uv run ruff check . && uv run mypy`
Expected: all pass, including every pre-existing artifact test.

- [ ] **Step 5: Commit**

```bash
cat >> docs/superpowers/spec-defects.md <<'EOF'

## New error identifiers: `E-STEP-UNIT-UNKNOWN`, `E-STEP-UNIT-SETTLED`

Raised by `io.record`/`io.skip`. Neither is in § Errors core raises, which enumerates the
raise-time codes. `E-STEP-UNIT-UNKNOWN` fires when a step records a key absent from its
roster; `E-STEP-UNIT-SETTLED` when a unit is both recorded and skipped in one execution —
the two states are mutually exclusive by construction, since `completed` and `ineligible`
partition the roster alongside `failed`. Propose adding both to that section's table.
EOF
git add src/publishable/artifacts.py tests/test_artifacts.py docs/superpowers/
git commit -m "Let a step record and skip units, keyed by unit"
```

---

### Task 7: The per-execution tables

**Files:**
- Modify: `src/publishable/artifacts.py`
- Test: `tests/test_artifacts.py`

**Interfaces:**
- Consumes: `WRITERS`/`READERS` from this module; `pyarrow`.
- Produces: `StepIO.finalize() -> None`, writing `units.parquet` when any row was recorded and `ineligible.jsonl` when anything was skipped; `WRITERS[".parquet"]` and `READERS[".parquet"]` registered so the reader inverts the writer, as `reference.md` § Steps and artifacts requires.

**Column order is specified**: the unit key first, then every declared attribute, then the union of every key any row recorded, a column absent from a row reading as null.

- [ ] **Step 1: Write the failing tests**

```python
def test_finalize_writes_a_parquet_table_and_an_ineligible_ledger(tmp_path: Path):
    from publishable.units import Unit, UnitList
    roster = UnitList([Unit(key=f"p{i}", attributes={"site": "a"}) for i in range(3)])
    sd = tmp_path / "run" / "s"; sd.mkdir(parents=True); (tmp_path / "in").mkdir()
    io = StepIO(step_dir=sd, input_dir=tmp_path / "in", run_dir=tmp_path / "run", units=roster)
    io.record("p0", {"pred": 0.5})
    io.record("p1", {"pred": 0.7, "extra": 9})
    io.skip("p2", "no baseline visit")
    io.finalize()
    rows = io.read_upstream("s", "units.parquet")
    assert [r["unit"] for r in rows] == ["p0", "p1"]
    assert rows[0]["extra"] is None, "a column absent from a row reads as null"
    lines = (sd / "ineligible.jsonl").read_text().splitlines()
    assert json.loads(lines[0]) == {"unit": "p2", "reason": "no baseline visit"}


def test_no_files_are_written_when_nothing_was_recorded_or_skipped(tmp_path: Path):
    from publishable.units import Unit, UnitList
    sd = tmp_path / "run" / "s"; sd.mkdir(parents=True); (tmp_path / "in").mkdir()
    io = StepIO(step_dir=sd, input_dir=tmp_path / "in", run_dir=tmp_path / "run",
                units=UnitList([Unit(key="p0")]))
    io.finalize()
    assert not (sd / "units.parquet").exists()
    assert not (sd / "ineligible.jsonl").exists()


def test_parquet_round_trips_through_the_registered_reader(tmp_path: Path):
    sd = tmp_path / "run" / "s"; sd.mkdir(parents=True); (tmp_path / "in").mkdir()
    io = StepIO(step_dir=sd, input_dir=tmp_path / "in", run_dir=tmp_path / "run")
    io.write("t.parquet", [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}])
    assert io.read_upstream("s", "t.parquet") == [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]


def test_the_writer_and_reader_tables_stay_in_step():
    from publishable.artifacts import READERS, WRITERS
    assert sorted(WRITERS) == sorted(READERS)
    assert ".parquet" in WRITERS
```

- [ ] **Step 2: Run and watch them fail**

Run: `uv run pytest tests/test_artifacts.py -k "finalize or parquet" -v`
Expected: FAIL — `AttributeError: 'StepIO' object has no attribute 'finalize'`

- [ ] **Step 3: Register the parquet codec and implement `finalize`**

```python
def _encode_parquet(rows: Any) -> bytes:
    import io as _stdio

    import pyarrow as pa
    import pyarrow.parquet as pq

    rows = list(rows)
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    table = pa.table({c: [r.get(c) for r in rows] for c in columns})
    buf = _stdio.BytesIO()
    pq.write_table(table, buf)
    return buf.getvalue()


def _decode_parquet(path: Path) -> Any:
    import pyarrow.parquet as pq

    return pq.read_table(path).to_pylist()
```

Add `".parquet": _encode_parquet` to `WRITERS` and `".parquet": _decode_parquet` to `READERS`.

Then on `StepIO`:

```python
    def finalize(self) -> None:
        """Write this execution's per-unit tables. Called by the runner when a step returns.

        Columns are the unit key, then every declared attribute, then the union of
        every key any row recorded — docs/reference.md § The per-unit tables.
        """
        if self._rows:
            attribute_names: list[str] = []
            if self._units is not None:
                for unit in self._units:
                    for name in unit.attributes:
                        if name not in attribute_names:
                            attribute_names.append(name)
            by_key = {u.key: u for u in self._units} if self._units is not None else {}
            recorded: list[str] = []
            for row in self._rows.values():
                for key in row:
                    if key != "unit" and key not in recorded:
                        recorded.append(key)
            columns = ["unit", *attribute_names, *recorded]
            rows = []
            for key, row in self._rows.items():
                unit = by_key.get(key)
                merged: dict[str, Any] = {"unit": key}
                for name in attribute_names:
                    merged[name] = unit.attributes.get(name) if unit else None
                for name in recorded:
                    merged[name] = row.get(name)
                rows.append({c: merged.get(c) for c in columns})
            self.write("units.parquet", rows)
        for key, reason in self.skipped.items():
            self.append("ineligible.jsonl", {"unit": key, "reason": reason})
```

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest tests/test_artifacts.py -v && uv run ruff check . && uv run mypy`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/publishable/artifacts.py tests/test_artifacts.py
git commit -m "Write the per-unit table and the ineligible ledger"
```

---

### Task 8: Attrition, and the runner's one named early stop

**Files:**
- Modify: `src/publishable/runner.py`
- Test: `tests/test_runner.py`

**Interfaces:**
- Consumes: `UnitList`; `StepIO(..., units=...)` and `io.finalize()`, `io.recorded_keys`, `io.skipped`.
- Produces: `ExecutionResult` gains `recorded: frozenset[str]` and `skipped: frozenset[str]`; `execute_plan` gains keyword-only `units: UnitList | None = None` and `max_failed_fraction: float | None = None`; `attrition(results, roster) -> dict[str, int]` returning `{"resolved", "completed", "ineligible", "failed"}`.

**The counting rule.** A failed unit has no row anywhere: `failed = resolved − completed − ineligible`. Failure is derived, never signalled. Across repeats a unit is `completed` only if it was recorded in EVERY repeat-scoped execution it was handed to — intersection, not union, because the collapse averages per unit and a unit present in three of five seeds would enter that average on a different number of observations than its neighbours.

**The early stop.** S1's guarantee is that a failed execution never stops the run. This adds the one documented exception, and the docstring must state the guarantee in full: *a failed execution never stops the run; only crossing the attrition threshold does.*

- [ ] **Step 1: Write the failing tests**

```python
def test_attrition_reconciles_exactly(tmp_path: Path):
    """resolved == completed + ineligible + failed, in every scenario."""
    roster = UnitList([Unit(key=f"p{i}") for i in range(10)])

    class Partial(BaseStep):
        def run(self, cfg, io):
            for u in list(io.units)[:7]:
                io.record(u.key, {"v": 1.0})
            io.skip("p9", "by design")
            return {}

    _, results = harness(tmp_path, [Partial], units=roster)
    counts = attrition(results, roster)
    assert counts == {"resolved": 10, "completed": 7, "ineligible": 1, "failed": 2}
    assert counts["resolved"] == counts["completed"] + counts["ineligible"] + counts["failed"]


def test_completion_is_the_intersection_across_repeats(tmp_path: Path):
    """A unit recorded in one repeat but not another is NOT completed."""
    roster = UnitList([Unit(key=f"p{i}") for i in range(4)])

    class Flaky(BaseStep):
        def run(self, cfg, io):
            keep = list(io.units) if self.repeat == "seed17" else list(io.units)[:2]
            for u in keep:
                io.record(u.key, {"v": 1.0})
            return {}

    _, results = harness(tmp_path, [Flaky], units=roster,
                         repeats=[Repeat("seed", "seed17", 17), Repeat("seed", "seed42", 42)])
    assert attrition(results, roster)["completed"] == 2


def test_crossing_the_attrition_threshold_stops_the_run(tmp_path: Path):
    roster = UnitList([Unit(key=f"p{i}") for i in range(10)])

    class Bad(BaseStep):
        def run(self, cfg, io):
            io.record("p0", {"v": 1.0})     # 9 of 10 fail
            return {}

    _, results = harness(tmp_path, [Bad, Bad], units=roster, max_failed_fraction=0.2,
                         repeats=[Repeat("seed", "s1", 1), Repeat("seed", "s2", 2)])
    assert len(results) < 4, "the plan must stop rather than run to its end"
    assert results[-1].status in ("completed", "failed")


def test_staying_under_the_threshold_runs_to_the_end(tmp_path: Path):
    roster = UnitList([Unit(key=f"p{i}") for i in range(10)])

    class MostlyGood(BaseStep):
        def run(self, cfg, io):
            for u in list(io.units)[:9]:
                io.record(u.key, {"v": 1.0})
            return {}

    _, results = harness(tmp_path, [MostlyGood, MostlyGood], units=roster,
                         max_failed_fraction=0.2,
                         repeats=[Repeat("seed", "s1", 1), Repeat("seed", "s2", 2)])
    assert len(results) == 4


def test_a_raising_step_still_does_not_stop_the_run(tmp_path: Path):
    """S1's guarantee is intact — only the threshold stops a run."""
    roster = UnitList([Unit(key="p0")])

    class Boom(BaseStep):
        def run(self, cfg, io):
            raise ValueError("broken")

    class Fine(BaseStep):
        def run(self, cfg, io):
            io.record("p0", {"v": 1.0})
            return {}

    _, results = harness(tmp_path, [Boom, Fine], units=roster)
    assert [r.status for r in results] == ["failed", "completed"]
```

The existing `harness` helper in this file must be extended to accept `units`, `repeats` and `max_failed_fraction` keyword arguments and pass them through; keep its existing defaults so pre-existing tests are unchanged.

- [ ] **Step 2: Run and watch them fail**

Run: `uv run pytest tests/test_runner.py -k "attrition or threshold or intersection" -v`
Expected: FAIL — `ImportError: cannot import name 'attrition'`

- [ ] **Step 3: Implement**

Add `recorded: frozenset[str] = frozenset()` and `skipped: frozenset[str] = frozenset()` to `ExecutionResult`. In `execute_plan`, construct `StepIO(..., units=units)`, call `io.finalize()` after a successful `run`, and capture `frozenset(io.recorded_keys)` / `frozenset(io.skipped)` into the result. Then:

```python
def attrition(results: list[ExecutionResult], roster: "UnitList | None") -> dict[str, int]:
    """The four counts. A failed unit has no row anywhere, so failure is derived.

    Completion is the INTERSECTION across the repeat-scoped executions a unit was
    handed to: the collapse averages per unit, and a unit present in three of five
    seeds would otherwise enter that average on a different number of observations
    than its neighbours — a ragged table dressed as a rectangular one.
    """
    if roster is None:
        return {"resolved": 0, "completed": 0, "ineligible": 0, "failed": 0}
    keys = {u.key for u in roster}
    recording = [r for r in results if r.execution.scope == "repeat"]
    if not recording:
        return {"resolved": len(keys), "completed": 0, "ineligible": 0, "failed": len(keys)}
    completed = set(keys)
    for r in recording:
        completed &= r.recorded
    # INTERSECTION, exactly as `completed` is computed. reference.md line 1580:
    # "A unit ineligible in some and completed in others is counted as failed, not
    # ineligible: eligibility is a property of the design." A union here would file an
    # inconsistently-skipped unit as ineligible, hiding it from max_failed_fraction,
    # which guards `failed` and deliberately does not guard `ineligible`.
    ineligible: set[str] = set(keys)
    for r in recording:
        ineligible &= r.skipped
    return {
        "resolved": len(keys),
        "completed": len(completed),
        "ineligible": len(ineligible),
        "failed": len(keys) - len(completed) - len(ineligible),
    }
```

And inside the loop, after appending each result:

```python
        if max_failed_fraction is not None and units is not None:
            counts = attrition(results, units)
            if counts["resolved"] and counts["failed"] / counts["resolved"] > max_failed_fraction:
                break
```

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest tests/test_runner.py -v && uv run ruff check . && uv run mypy`
Expected: all pass, including every pre-existing runner test.

- [ ] **Step 5: Commit**

```bash
git add src/publishable/runner.py tests/test_runner.py
git commit -m "Count attrition four ways, and stop when the cohort is past saving"
```

---

### Task 9: Collapse, the `basis` split, and the record

**Files:**
- Modify: `src/publishable/stats.py`, `src/publishable/run_record.py`
- Test: `tests/test_stats.py`, `tests/test_runner.py`

**Interfaces:**
- Consumes: `Interval`, `t_over_units`, `mean_of`; `ExecutionResult`.
- Produces: `collapse_repeats(results: list[ExecutionResult], step_name: str, condition_index: int) -> dict[str, dict[str, float]]` — `condition_index` is REQUIRED so cross-condition pooling, which § Statistical reporting forbids outright, cannot be written by omission mapping unit key → column → mean across repeats; `summarize_step(collapsed, counts) -> dict[str, dict]` returning per-column `{"value", "basis", "n", "ci95", "method"}`; `assemble_run_yaml` gains keyword-only `aggregated: dict[str, dict] | None = None`. It does NOT gain `counts` — `summarize_step` already embeds the counts as `n` on each metric, and the documented condition-entry shape has no bare `n` sibling.

**The `basis` split.** A recorded column is `basis: units` and carries a `ci95`. A metric that exists only as a step-returned scalar is `basis: repeats` and gets **no** `ci95` — an interval over seeds measures how much the RNG moved the answer and narrows as you add seeds.

- [ ] **Step 1: Write the failing tests**

```python
def _result(repeat_label: str, rows: list[dict]):
    """An ExecutionResult carrying rows, as execute_plan would produce."""
    from publishable.runner import ExecutionResult
    from publishable.scope import Execution

    class _Step:
        scope = "repeat"

    ex = Execution(
        step_cls=_Step, step_name="analyze", scope="repeat",
        condition_index=0, condition_label=None, repeat_label=repeat_label,
    )
    return ExecutionResult(
        execution=ex, status="completed", started_at="2026-08-09T00:00:00Z",
        wall_seconds=0.0, returned={}, error=None,
        recorded=frozenset(r["unit"] for r in rows), skipped=frozenset(),
        rows=tuple(rows),
    )


def test_collapse_averages_a_unit_across_repeats():
    from publishable.stats import collapse_repeats

    results = [
        _result("seed17", [{"unit": "p0", "pred": 0.2}, {"unit": "p1", "pred": 1.0}]),
        _result("seed42", [{"unit": "p0", "pred": 0.4}, {"unit": "p1", "pred": 2.0}]),
    ]
    collapsed = collapse_repeats(results, "analyze")
    assert collapsed["p0"]["pred"] == pytest.approx(0.3)
    assert collapsed["p1"]["pred"] == pytest.approx(1.5)


def test_collapse_ignores_other_steps_and_non_repeat_scopes():
    from publishable.stats import collapse_repeats

    results = [_result("seed17", [{"unit": "p0", "pred": 0.2}])]
    assert collapse_repeats(results, "some_other_step") == {}


def test_a_recorded_column_is_basis_units_and_carries_an_interval():
    from publishable.stats import summarize_step
    collapsed = {f"p{i}": {"pred": float(i)} for i in range(10)}
    out = summarize_step(collapsed, {"resolved": 10, "completed": 10,
                                     "ineligible": 0, "failed": 0})
    assert out["pred"]["basis"] == "units"
    assert out["pred"]["n"] == {"resolved": 10, "completed": 10, "ineligible": 0, "failed": 0}
    assert out["pred"]["method"] == "t_over_units"
    low, high = out["pred"]["ci95"]
    assert low < out["pred"]["value"] < high


def test_a_single_completed_unit_reports_a_value_with_no_interval():
    """Answers the ledger's open question: one observation has no dispersion."""
    from publishable.stats import summarize_step
    out = summarize_step({"p0": {"pred": 1.0}},
                         {"resolved": 1, "completed": 1, "ineligible": 0, "failed": 0})
    assert out["pred"]["value"] == 1.0
    assert out["pred"]["ci95"] is None
    assert out["pred"]["method"] is None


def test_a_non_numeric_column_is_not_summarized():
    from publishable.stats import summarize_step
    out = summarize_step({"p0": {"site": "a"}, "p1": {"site": "b"}},
                         {"resolved": 2, "completed": 2, "ineligible": 0, "failed": 0})
    assert "site" not in out
```

- [ ] **Step 2: Run and watch them fail**

Run: `uv run pytest tests/test_stats.py -k "collapse or basis or single or non_numeric" -v`
Expected: FAIL — `ImportError: cannot import name 'collapse_repeats'`

- [ ] **Step 3: Implement**

```python
def collapse_repeats(
    results: list["ExecutionResult"], step_name: str
) -> dict[str, dict[str, float]]:
    """Average each unit's numeric columns across the repeats that recorded it."""
    gathered: dict[str, dict[str, list[float]]] = {}
    for r in results:
        if r.execution.step_name != step_name or r.execution.scope != "repeat":
            continue
        for row in r.rows:
            key = row["unit"]
            for column, value in row.items():
                if column == "unit" or not isinstance(value, (int, float)):
                    continue
                if isinstance(value, bool):
                    continue
                gathered.setdefault(key, {}).setdefault(column, []).append(float(value))
    return {
        key: {col: sum(vals) / len(vals) for col, vals in cols.items()}
        for key, cols in gathered.items()
    }


def summarize_step(
    collapsed: dict[str, dict[str, float]], counts: dict[str, int]
) -> dict[str, dict[str, Any]]:
    """Per-column value, basis, n and interval over the collapsed unit table."""
    columns: list[str] = []
    for cols in collapsed.values():
        for name in cols:
            if name not in columns:
                columns.append(name)
    out: dict[str, dict[str, Any]] = {}
    for column in columns:
        values = [cols[column] for cols in collapsed.values() if column in cols]
        interval = t_over_units(values)
        out[column] = {
            "value": mean_of(values),
            "basis": "units",
            "n": dict(counts),
            "ci95": [interval.low, interval.high] if interval else None,
            "method": interval.method if interval else None,
        }
    return out
```

`ExecutionResult` gains `rows: tuple[dict[str, Any], ...] = ()`, captured from `io.rows()` in `execute_plan`. Import it under `TYPE_CHECKING` in `stats.py` to keep the module free of a runtime dependency on the runner.

In `run_record.assemble_run_yaml`, accept `aggregated` and `counts` and place `aggregated` inside each condition entry beside `per_repeat`; leave `per_repeat` exactly as it is — it is verbatim what the step returned, and no derived value ever appears there.

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest -v && uv run ruff check . && uv run mypy`
Expected: all pass.

- [ ] **Step 5: Answer two ledger entries**

```bash
cat >> docs/superpowers/spec-defects.md <<'EOF'

## ANSWERED in S2: a single completed unit reports no interval

The open question was what a design with no dispersion reports. S2's answer, applied to
`basis: units`: below two completed units, `value` is reported and `ci95` and `method` are
`null`. Reporting a point with no interval is honest; inventing one is not, and this matches
the posture § The unit table is the inference base already takes toward `basis: repeats`.
The `t_over_units` construction returns `None` below n=2 rather than raising, so the caller
renders the absence rather than the failure. Propose stating this in § Statistical reporting.
EOF
```

- [ ] **Step 6: Commit**

```bash
git add src/publishable/stats.py src/publishable/run_record.py tests/ docs/superpowers/
git commit -m "Collapse repeats per unit, and say what basis each metric rests on"
```

---

### Task 10: Wire it through the CLI, and the acceptance test

**Files:**
- Modify: `src/publishable/cli.py`
- Test: `tests/test_acceptance.py`

**Interfaces:**
- Consumes: everything above.
- Produces: `command_run` resolves the roster at phase 5, records `provenance.units` and `provenance.units_hash`, passes `units` and `max_failed_fraction` to `execute_plan`, and carries `aggregated` and the four counts into `run.yaml`.

- [ ] **Step 1: Write the failing acceptance test**

```python
def test_the_inference_base_is_real(tmp_path: Path):
    """240 units resolve, some are skipped, 12 go unrecorded, and n reports what completed."""
    root, cfg, results_dir, data = build_with_units(tmp_path, n_units=240)
    # the generated step records 226, skips 2, and leaves 12 unrecorded
    write_step(root, recorded=226, skipped=2)
    commit(root)
    assert main(["run", str(cfg)]) == EXIT_OK

    doc = yaml.safe_load((next(results_dir.glob("run_*")) / "run.yaml").read_text())
    counts = doc["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]["score"]["n"]
    assert counts["resolved"] == 240
    assert counts["completed"] == 226
    assert counts["ineligible"] == 2
    assert counts["failed"] == 12
    assert counts["resolved"] == counts["completed"] + counts["ineligible"] + counts["failed"]

    metric = doc["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]["score"]
    assert metric["basis"] == "units"
    assert metric["method"] == "t_over_units"
    low, high = metric["ci95"]
    assert low < metric["value"] < high

    assert doc["provenance"]["units"]["n"] == 240
    assert doc["provenance"]["units_hash"].startswith("sha256:")


def test_the_interval_matches_an_independent_computation(tmp_path: Path):
    """Recompute the interval from units.parquet by hand and compare."""
    root, cfg, results_dir, _ = build_with_units(tmp_path, n_units=40)
    write_step(root, recorded=40, skipped=0)
    commit(root)
    assert main(["run", str(cfg)]) == EXIT_OK
    run_dir = next(results_dir.glob("run_*"))
    doc = yaml.safe_load((run_dir / "run.yaml").read_text())
    metric = doc["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]["score"]

    import math
    import pyarrow.parquet as pq
    tables = sorted(run_dir.glob("*/step01_summarize_units/units.parquet"))
    per_unit: dict[str, list[float]] = {}
    for t in tables:
        for row in pq.read_table(t).to_pylist():
            per_unit.setdefault(row["unit"], []).append(row["score"])
    values = [sum(v) / len(v) for v in per_unit.values()]
    n = len(values)
    mean = sum(values) / n
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1))
    from scipy import stats as sp
    half = float(sp.t.ppf(0.975, df=n - 1)) * sd / math.sqrt(n)
    assert metric["value"] == pytest.approx(mean)
    assert metric["ci95"][0] == pytest.approx(mean - half)
    assert metric["ci95"][1] == pytest.approx(mean + half)
```

Write `build_with_units` and `write_step` as module-level helpers in the test file: `build_with_units` scaffolds a project, writes an `index.csv` of `n_units` rows with a `patient_id` column, generates the experiment, fills `metadata`, and returns `(root, cfg_path, results_dir, data_dir)`. `write_step` overwrites the generated starter step with one that records a deterministic `score` for the first `recorded` units, calls `io.skip` on the next `skipped`, and leaves the rest untouched.

- [ ] **Step 2: Run and watch them fail**

Run: `uv run pytest tests/test_acceptance.py -k inference -v`
Expected: FAIL — no `aggregated` key in the record.

- [ ] **Step 3: Wire the CLI**

In `command_run`, after the manifest is built and before the run directory is allocated:

```python
    units_decl = (doc.get("data") or {}).get("units")
    roster = resolve_units(units_decl, input_dir) if units_decl else None
```

Pass `units=roster` and `max_failed_fraction=(doc.get("limits") or {}).get("max_failed_fraction")` into `execute_plan`. After the loop, compute the counts and the aggregate:

```python
        counts = attrition(results, roster)
        aggregated: dict[str, dict[str, Any]] = {}
        if roster is not None:
            recording_steps = {
                r.execution.step_name for r in results
                if r.execution.scope == "repeat" and r.rows
            }
            for step_name in sorted(recording_steps):
                collapsed = collapse_repeats(results, step_name)
                aggregated[step_name] = summarize_step(collapsed, counts)
```

Add to `provenance`:

```python
            "units": {"n": len(roster), "key": units_decl.get("key")} if roster else None,
            "units_hash": units_hash(roster) if roster else None,
```

Pass `aggregated=aggregated` and `counts=counts` to `assemble_run_yaml`.

- [ ] **Step 4: Run the whole suite and the real journey**

Run: `uv run pytest -v && uv run ruff check . && uv run mypy`
Then run the CLI by hand in a temp directory — scaffold, generate, write an `index.csv`, fill metadata, commit, `validate`, `run` — and read the produced `run.yaml`. Confirm `aggregated` carries a real interval and the counts reconcile. Paste the record into your report.

- [ ] **Step 5: Retire the ledger entry S2 closes**

```bash
cat >> docs/superpowers/spec-defects.md <<'EOF'

## RETIRED in S2: "S1 omits `data.units` from the materialized config"

`materialize_config` now emits the block and `validate` resolves it. The seven sub-fields
S2 does not implement are refused individually rather than the block being refused whole.
EOF
```

- [ ] **Step 6: Commit**

```bash
git add src/publishable/cli.py tests/test_acceptance.py docs/superpowers/
git commit -m "Make n mean the thing the claim generalizes over"
```

---

## Definition of done for S2

- [ ] `uv run pytest` green, including both acceptance tests.
- [ ] `uv run ruff check .` and `uv run mypy` clean.
- [ ] Every `E-`/`W-` identifier defined in `src/` has a test that produces it.
- [ ] `E-DATA-UNITS-UNSUPPORTED` appears nowhere in `src/` or `tests/`.
- [ ] The seven sub-field refusals each fire, and a generated config trips none of them.
- [ ] The reconciliation identity `resolved == completed + ineligible + failed` is asserted in every attrition scenario.
- [ ] The interval is verified three non-circular ways: a published critical value, a hand-computed dataset, and the wider-than-normal-and-converging property.
- [ ] `docs/superpowers/spec-defects.md` records what S2 answered and what it retired.
