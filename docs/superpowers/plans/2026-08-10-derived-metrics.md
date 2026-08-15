# Derived Metrics and Dispersion (S4a) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A template can derive a metric from the unit table, and core resamples it for a percentile interval.

**Architecture:** One per-value coercion rule — NumPy coerced, structural refused — implemented for the first time and applied at all three surfaces. `BaseTemplate.aggregate(units, cfg)` receives a four-operation table over the collapsed per-unit rows and returns a flat mapping of scalars; core reports each derived metric as `basis: units` with a percentile `ci95` bootstrapped from the design digest. `repeat_spread` reports one dispersion entry per repeat level. Five declared-but-ignored blocks are refused by name.

**Tech Stack:** Python 3.11+, `uv`, pytest, ruff, mypy, numpy.

## Global Constraints

- Python >= 3.11.
- Runtime dependencies are exactly `pyyaml`, `numpy`, `scipy`, `pyarrow`. Adding one is out of scope.
- ruff: line-length 100, select `["E","F","I","UP","B"]`. mypy: strict over `src/`.
- Commands: `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`, `uv run mypy`.
- `×`, not `x`, for multiplication — including inside fenced blocks and commit messages.
- `stats.py` and `sweep.py` are **pure**: no filesystem, and no runtime import of `config`, `artifacts`, `runner`, or `cli`.
- `artifacts.py` is the only module that writes inside a run directory.
- `validate.py` **collects** findings and never raises to report one.
- Every `E-`/`W-` identifier must have a test that produces it; for a validate-time code that means through `validate_config`.
- The four documents in `docs/` are normative and lead. Where code cannot follow them, the document changes first and the gap is recorded in `docs/superpowers/spec-defects.md`.
- Unimplemented must mean **refused**, never silently ignored.
- **A run with no `aggregate` declared must be byte-for-byte unchanged.** Adding a metric origin risks it appearing where nothing asked for one.

---

## File Structure

| File | Responsibility in this slice |
|---|---|
| `src/publishable/coercion.py` *(new)* | The one per-value scalar rule: NumPy coerced, structural refused |
| `src/publishable/artifacts.py` | `io.record` coerces its values through it |
| `src/publishable/runner.py` | A step's return coerced through it |
| `src/publishable/templates/base.py` | `aggregate(units, cfg)` on `BaseTemplate`, defaulting to `{}` |
| `src/publishable/stats.py` | `UnitTable`; the bootstrap; `percentile_over_units`; `repeat_spread` |
| `src/publishable/cli.py` | Calling `aggregate` once per recording step; derived metrics and `repeat_spread` into the record |
| `src/publishable/validate.py` | The five refusals |

---

### Task 1: The coercion rule

**Files:**
- Create: `src/publishable/coercion.py`
- Test: `tests/test_coercion.py`

**Interfaces:**
- Consumes: `ContractError` from `publishable.errors`.
- Produces: `coerce_scalars(values: dict[str, Any], where: str) -> dict[str, Any]`

`where` names the surface for the message — `"io.record"`, a step name, or a template's `aggregate`.

**This rule does not exist today.** `docs/reference.md` § Steps and artifacts states it — "`io.record`'s `values`, a step's return, and a template's `aggregate` take the same scalars under the same coercion" — and nothing implements it. Both halves are live defects, reproduced: a `numpy.float64` reaches `yaml.safe_dump` and raises `RepresenterError` while writing `run.yaml`, and a nested mapping serializes silently into the record.

**Do not absorb the two existing checks.** `artifacts.py` verifies a *column* holds one type across rows; `runner.py` verifies a step's return is a *mapping*. Both happen to raise `E-STEP-RETURN-TYPE`, but they are different questions from per-value coercion, and merging them would consolidate three rules rather than unify one.

- [ ] **Step 1: Write the failing tests**

```python
import numpy as np
import pytest
from publishable.coercion import coerce_scalars
from publishable.errors import ContractError


def test_a_numpy_float_becomes_a_python_float():
    out = coerce_scalars({"r": np.float64(0.581)}, "io.record")
    assert out == {"r": 0.581}
    assert type(out["r"]) is float


def test_a_numpy_int_becomes_a_python_int():
    out = coerce_scalars({"n": np.int64(240)}, "io.record")
    assert out == {"n": 240}
    assert type(out["n"]) is int


def test_a_numpy_bool_becomes_a_python_bool():
    out = coerce_scalars({"ok": np.bool_(True)}, "io.record")
    assert type(out["ok"]) is bool


def test_plain_scalars_pass_through_unchanged():
    values = {"a": 1, "b": 2.5, "c": "x", "d": True, "e": None}
    assert coerce_scalars(values, "io.record") == values


def test_a_mapping_is_refused():
    with pytest.raises(ContractError) as exc:
        coerce_scalars({"r": {"nested": 1}}, "step03_analyze")
    assert exc.value.code == "E-STEP-RETURN-TYPE"
    assert "step03_analyze" in str(exc.value)


def test_a_list_is_refused():
    with pytest.raises(ContractError) as exc:
        coerce_scalars({"r": [1, 2]}, "io.record")
    assert exc.value.code == "E-STEP-RETURN-TYPE"


def test_a_numpy_array_is_refused_not_coerced():
    """An array is structural even though its dtype is numeric — coercing it to a
    list would put a sequence in a cell that must hold one value."""
    with pytest.raises(ContractError) as exc:
        coerce_scalars({"r": np.array([1.0, 2.0])}, "io.record")
    assert exc.value.code == "E-STEP-RETURN-TYPE"


def test_the_message_names_the_key_and_the_type():
    with pytest.raises(ContractError) as exc:
        coerce_scalars({"weird": {"a": 1}}, "io.record")
    assert "weird" in str(exc.value) and "dict" in str(exc.value)
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_coercion.py -v`
Expected: FAIL — the module does not exist.

- [ ] **Step 3: Implement**

```python
"""The one scalar rule, shared by every surface that accepts values.

`docs/reference.md` § Steps and artifacts: `io.record`'s `values`, a step's
return, and a template's `aggregate` take the same scalars under the same
coercion — "a table core would reject what a return accepted would be a
divergence found on the first line anyone writes." What differs between the
three is only where the value lands.
"""

from typing import Any

from publishable.errors import ContractError

_SCALARS = (bool, int, float, str)


def coerce_scalars(values: dict[str, Any], where: str) -> dict[str, Any]:
    """Return `values` with NumPy scalars coerced; raise on anything structural.

    A per-unit value a model hands back is a `numpy.float64` at least as often
    as a derived metric is, and uncoerced it reaches `yaml.safe_dump` and raises
    `RepresenterError` while writing `run.yaml` — a traceback rather than a
    diagnostic. Anything structural is refused instead of coerced: a list or a
    mapping in a cell that must hold one value is a mistake no reshaping fixes.
    """
    out: dict[str, Any] = {}
    for key, value in values.items():
        out[key] = _coerce_one(key, value, where)
    return out


def _coerce_one(key: str, value: Any, where: str) -> Any:
    if value is None or isinstance(value, _SCALARS):
        return value
    item = getattr(value, "item", None)
    # `.item()` is NumPy's own scalar unwrap, and `ndim == 0` is what separates a
    # scalar from an array — an array also has `.item()` and would otherwise
    # silently collapse to its first element.
    if item is not None and getattr(value, "ndim", None) == 0:
        unwrapped = item()
        if isinstance(unwrapped, _SCALARS):
            return unwrapped
    raise ContractError(
        f"{where} gave {key!r} a {type(value).__name__}; values must be a scalar — "
        "a bool, int, float, str, or None, or a NumPy scalar core coerces to one",
        code="E-STEP-RETURN-TYPE",
    )
```

- [ ] **Step 4: Run to verify they pass, then commit**

```bash
uv run pytest tests/test_coercion.py -v && uv run ruff check . && uv run mypy
git add src/publishable/coercion.py tests/test_coercion.py
git commit -m "Add the one scalar rule every value surface shares"
```

---

### Task 2: Apply the rule at both existing surfaces

**Files:**
- Modify: `src/publishable/artifacts.py` (`io.record`), `src/publishable/runner.py` (a step's return)
- Test: `tests/test_artifacts.py`, `tests/test_runner.py`

**Interfaces:**
- Consumes: `coerce_scalars(values, where)` from Task 1.
- Produces: no new names.

**The acceptance bar: no existing test changes.** This adds a rule that did not exist rather than altering two that did. `artifacts.py`'s column-consistency tests and `runner.py`'s return-shape tests must pass untouched. If one had to change, something merged that should not have — stop and report it.

- [ ] **Step 1: Write the failing tests**

```python
def test_io_record_coerces_a_numpy_value(tmp_path):
    io = make_io(tmp_path, units=UnitList([_u("u1")]))
    io.record("u1", {"score": np.float64(1.5)})
    row = io.rows()[0]
    assert type(row["score"]) is float


def test_io_record_refuses_a_structural_value(tmp_path):
    io = make_io(tmp_path, units=UnitList([_u("u1")]))
    with pytest.raises(ContractError) as exc:
        io.record("u1", {"score": {"nested": 1}})
    assert exc.value.code == "E-STEP-RETURN-TYPE"
```

and for the runner, a step returning a NumPy scalar whose value reaches the record as a plain float. Build it with whatever `tests/test_runner.py` already uses to run a step — **read the file and reuse its idiom**; do not add a second harness.

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_artifacts.py -k coerce -v`
Expected: FAIL — the NumPy value passes through as `numpy.float64` and the structural value is accepted.

- [ ] **Step 3: Wire it in**

In `io.record`, coerce **after** the existing collision checks and before storing the row:

```python
        self._rows[unit_key] = {"unit": unit_key, **coerce_scalars(values, "io.record")}
```

In `runner.py`, coerce the step's return **after** the existing mapping check, so a non-mapping still reports the shape error rather than a per-value one:

```python
            returned = coerce_scalars(returned, execution.step_name)
```

- [ ] **Step 4: Confirm the live defect is closed**

Add a test that a step returning `np.float64` produces a `run.yaml` that serializes — before this task it raised `RepresenterError` from `yaml.safe_dump`. Use the end-to-end driver `run_a_project` in `tests/test_cli.py`; **read it first and reuse it**.

- [ ] **Step 5: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/artifacts.py src/publishable/runner.py tests/
git commit -m "Coerce values at io.record and at a step's return"
```

---

### Task 3: `UnitTable`, the four operations

**Files:**
- Modify: `src/publishable/stats.py`
- Test: `tests/test_stats.py`

**Interfaces:**
- Consumes: the collapsed table `dict[str, dict[str, float]]` that `collapse_repeats` returns.
- Produces: `UnitTable(collapsed: dict[str, dict[str, float]])`, supporting **exactly** row iteration, column access by attribute, `len`, and `.columns`.

**Why exactly four.** `docs/reference.md` § Templates: a table that also promised indexing, filtering, and `.loc` would be a `DataFrame`, and core could never change what backs it without breaking every plugin. The same argument that keeps `io.units` to three operations.

Column access is by attribute, because the worked example reads `units.pred` and `units.truth`.

- [ ] **Step 1: Write the failing tests**

```python
def test_iteration_yields_one_row_per_unit():
    t = UnitTable({"u1": {"pred": 1.0}, "u2": {"pred": 2.0}})
    assert [r["unit"] for r in t] == ["u1", "u2"]
    assert [r["pred"] for r in t] == [1.0, 2.0]


def test_column_access_returns_values_in_iteration_order():
    t = UnitTable({"u1": {"pred": 1.0}, "u2": {"pred": 2.0}})
    assert list(t.pred) == [1.0, 2.0]


def test_len_counts_units():
    assert len(UnitTable({"u1": {"pred": 1.0}, "u2": {"pred": 2.0}})) == 2


def test_columns_lists_the_recorded_columns():
    t = UnitTable({"u1": {"pred": 1.0, "truth": 0.0}})
    assert sorted(t.columns) == ["pred", "truth"]


def test_a_ragged_column_omits_the_missing_unit():
    """A unit with no value for a column is absent from it, not None — a mean over
    a column must not be diluted by units that never recorded it."""
    t = UnitTable({"u1": {"pred": 1.0}, "u2": {}})
    assert list(t.pred) == [1.0]


def test_an_unknown_column_raises():
    t = UnitTable({"u1": {"pred": 1.0}})
    with pytest.raises(ContractError) as exc:
        t.nope
    assert exc.value.code == "E-STEP-COLUMN-UNKNOWN"


def test_iteration_is_repeatable():
    t = UnitTable({"u1": {"pred": 1.0}})
    assert [r["unit"] for r in t] == [r["unit"] for r in t]
```

`E-STEP-COLUMN-UNKNOWN` is a new identifier. **Grep `docs/reference.md` for it first** — several codes this project "added" already existed. If it does not exist, mint it, and record it in `docs/superpowers/spec-defects.md`.

- [ ] **Step 2: Run to verify they fail, then implement**

Run: `uv run pytest tests/test_stats.py -k UnitTable -v`

```python
class UnitTable:
    """Row iteration, column access, `len`, `columns` — and nothing else.

    Deliberately not a `DataFrame`: one that also promised indexing, filtering
    and `.loc` would be one, and core could never change what backs it — a lazily
    materialized table, a view over a partition — without breaking every plugin.
    The same reasoning that keeps `io.units` to three operations.
    """

    def __init__(self, collapsed: dict[str, dict[str, float]]) -> None:
        self._rows = [{"unit": key, **values} for key, values in collapsed.items()]

    def __iter__(self) -> "Iterator[dict[str, Any]]":
        return iter(self._rows)

    def __len__(self) -> int:
        return len(self._rows)

    @property
    def columns(self) -> list[str]:
        seen: dict[str, None] = {}
        for row in self._rows:
            for key in row:
                if key != "unit":
                    seen[key] = None
        return list(seen)

    def __getattr__(self, name: str) -> list[Any]:
        if name.startswith("_"):
            raise AttributeError(name)
        values = [row[name] for row in self._rows if name in row]
        if not values:
            raise ContractError(
                f"{name!r} is not a column this table holds; it has "
                f"{', '.join(self.columns) or 'no columns'}",
                code="E-STEP-COLUMN-UNKNOWN",
            )
        return values
```

**`columns` is a property, so a recorded column named `columns` cannot shadow it** — `__getattr__` runs only when normal lookup fails. Note that in a comment; it is the same shadowing question `cfg`'s no-methods rule answers.

- [ ] **Step 3: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/stats.py tests/test_stats.py
git commit -m "Hand a template four operations over the unit table"
```

---

### Task 4: The bootstrap

**Files:**
- Modify: `src/publishable/stats.py`
- Test: `tests/test_stats.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces:
  - `resample_seed(digest: str) -> int`
  - `percentile_over_units(values: Sequence[float], seed: int, draws: int = 2000, confidence: float = 0.95) -> Interval | None`

`Interval` already exists in `stats.py`. Return `None` below two values, matching `t_over_units` — a single observation has no dispersion to describe and inventing an interval for it would not be honest.

**The seed derives from the design digest, never `parameters_hash`** — the same rule fold partitions and `order_seed` already follow, and for the same reason: editing an unrelated parameter must not redraw a resample. Use an explicit `random.Random`, never the module-level global.

- [ ] **Step 1: Write the failing tests**

**`Interval` is a frozen dataclass with `low`, `high`, and `method` — not a tuple.** It does not unpack and does not index; read its fields by name, and construct it with all three, as `t_over_units` does (`Interval(low=..., high=..., method="t_over_units")`).

```python
def test_the_interval_brackets_the_point_estimate():
    values = [float(i) for i in range(50)]
    got = percentile_over_units(values, seed=7)
    assert got.low < sum(values) / len(values) < got.high


def test_it_names_its_method():
    assert percentile_over_units([float(i) for i in range(50)], seed=7).method == (
        "percentile_over_units"
    )


def test_the_same_seed_reproduces_the_interval():
    values = [float(i) for i in range(50)]
    assert percentile_over_units(values, seed=7) == percentile_over_units(values, seed=7)


def test_a_different_seed_gives_a_different_interval():
    values = [float(i) for i in range(50)]
    assert percentile_over_units(values, seed=7) != percentile_over_units(values, seed=99)


def test_it_is_invariant_to_row_order():
    """A bootstrap resamples with replacement, so the order units arrive in must
    not change the interval — only the multiset of values may."""
    values = [float(i) for i in range(50)]
    assert percentile_over_units(values, seed=7) == percentile_over_units(
        list(reversed(values)), seed=7
    )


def test_it_converges_toward_the_analytic_interval_for_a_mean():
    """Verified against something other than itself: for a mean over many units the
    percentile interval should sit close to Student's t, which is computed by
    entirely different code."""
    values = [float(i % 10) for i in range(400)]
    boot = percentile_over_units(values, seed=7, draws=4000)
    analytic = t_over_units(values)
    assert abs(boot.low - analytic.low) < 0.15
    assert abs(boot.high - analytic.high) < 0.15


def test_one_value_has_no_interval():
    assert percentile_over_units([1.0], seed=7) is None


def test_resample_seed_depends_on_the_digest():
    assert resample_seed("a") != resample_seed("b")
    assert resample_seed("a") == resample_seed("a")
```

The convergence test is the one that verifies the bootstrap against **something other than itself** — checking a percentile interval by re-running the same code proves nothing.

- [ ] **Step 2: Run to verify they fail, then implement**

Run: `uv run pytest tests/test_stats.py -k percentile -v`

```python
def resample_seed(digest: str) -> int:
    """From the design digest, never `parameters_hash`.

    Editing an unrelated parameter must not redraw a resample — the same rule
    fold partitions and `order_seed` follow (reference.md § What auto-derives from).
    """
    return int.from_bytes(hashlib.sha256(f"{digest}|resample".encode()).digest()[:4], "big")


def percentile_over_units(
    values: Sequence[float], seed: int, draws: int = 2000, confidence: float = 0.95
) -> Interval | None:
    """A percentile interval over the units, by resampling with replacement.

    This is what gives a derived metric its `ci95`: a value computed from the
    whole table has no per-unit spread to run a t-interval over, so core
    resamples the units it was computed from (reference.md § How a metric becomes
    a number).
    """
    if len(values) < 2:
        return None
    rng = random.Random(seed)
    pool = list(values)
    n = len(pool)
    means = sorted(
        sum(pool[rng.randrange(n)] for _ in range(n)) / n for _ in range(draws)
    )
    tail = (1.0 - confidence) / 2.0
    lo = means[max(0, int(tail * draws) - 1)]
    hi = means[min(draws - 1, int((1.0 - tail) * draws))]
    return Interval(low=lo, high=hi, method="percentile_over_units")
```

Add `import hashlib` and `import random` if absent. Sorting the values before indexing is what makes row order irrelevant.

- [ ] **Step 3: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/stats.py tests/test_stats.py
git commit -m "Bootstrap a percentile interval over the units"
```

---

### Task 5: `aggregate` on `BaseTemplate`

**Files:**
- Modify: `src/publishable/templates/base.py`
- Test: `tests/test_templates.py` (it exists; read it and match its idiom)

**Interfaces:**
- Consumes: `UnitTable` from Task 3.
- Produces: `BaseTemplate.aggregate(self, units: "UnitTable", cfg: Any) -> dict[str, Any]`, returning `{}`.

`BaseTemplate` currently declares `naming_pattern`, `field_convention`, `default_repeats`, `required_env`, `apparatus_probe`, `apparatus_facts`, `parameter_spec`, and `validate`. `aggregate` joins them as an optional override.

- [ ] **Step 1: Write the failing tests**

```python
def test_the_base_aggregate_returns_nothing():
    """`{}` is the right answer for a table a template doesn't recognize — core
    calls `aggregate` once per recording step, and a pipeline can have several."""
    assert BaseTemplate().aggregate(UnitTable({"u1": {"pred": 1.0}}), None) == {}


def test_a_subclass_can_derive_from_the_table():
    class T(BaseTemplate):
        def aggregate(self, units, cfg):
            return {"total": sum(units.pred)}

    assert T().aggregate(UnitTable({"u1": {"pred": 1.0}, "u2": {"pred": 2.0}}), None) == {
        "total": 3.0
    }
```

- [ ] **Step 2: Run to verify they fail, then implement**

```python
    def aggregate(self, units: "UnitTable", cfg: Any) -> dict[str, Any]:
        """Derive metrics from the unit table; `{}` when there is nothing to derive.

        Core calls this once per recording step, and a pipeline can have several,
        so returning `{}` for a table this template does not recognize is the
        right answer rather than an error. `cfg` is this condition's resolved
        parameters — the same object a step receives — which is what lets one
        `aggregate` compute pearson under one condition and kendall under another.

        The return is what a step may return: a flat mapping of scalars under the
        same coercion. There is no `Estimate` exception here, unlike a `summary`
        step's return, because a derived metric is one core computes and resamples
        itself rather than one the user asserts.
        """
        return {}
```

Import `UnitTable` under `TYPE_CHECKING` to keep the import graph flat; say in your report whether that was necessary.

- [ ] **Step 3: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/templates/base.py tests/
git commit -m "Give a template an aggregate over the unit table"
```

---

### Task 6: Derived metrics reach the record

**Files:**
- Modify: `src/publishable/stats.py`, `src/publishable/cli.py`
- Test: `tests/test_stats.py`, `tests/test_cli.py`

**Interfaces:**
- Consumes: `UnitTable`, `percentile_over_units`, `resample_seed`, `coerce_scalars`, `BaseTemplate.aggregate`.
- Produces: `summarize_step(collapsed, counts, derived=None, seed=None)` — **two new trailing defaulted parameters**, so existing callers are untouched.

A derived metric is reported as `basis: units` with `method: percentile_over_units` and a `ci95` from the bootstrap over the units the metric was computed from. `cohens_d` is **not** computed by this slice; the field records `null`, and S4b must not "fix" that for a derived metric — Cohen's *d* needs a per-unit value to difference, and a derived value has none.

**A derived key may not collide with a recorded column.** `docs/reference.md` § Errors core raises already names this exact case — `E-STEP-KEY-COLLISION` for "a derived key against a recorded column" — and `artifacts.py` already raises it for the sibling case. **Reuse it; do not mint a second code.**

- [ ] **Step 1: Write the failing tests**

```python
def test_a_derived_metric_is_reported_over_units():
    collapsed = {f"u{i}": {"pred": float(i)} for i in range(20)}
    out = summarize_step(collapsed, {"completed": 20}, derived={"total": 190.0}, seed=7)
    assert out["total"]["basis"] == "units"
    assert out["total"]["method"] == "percentile_over_units"
    assert out["total"]["ci95"] is not None
    assert out["total"]["cohens_d"] is None


def test_a_derived_key_colliding_with_a_recorded_column_is_refused():
    collapsed = {f"u{i}": {"r": float(i)} for i in range(5)}
    with pytest.raises(ContractError) as exc:
        summarize_step(collapsed, {"completed": 5}, derived={"r": 1.0}, seed=7)
    assert exc.value.code == "E-STEP-KEY-COLLISION"


def test_no_derived_metrics_leaves_the_output_unchanged():
    collapsed = {f"u{i}": {"pred": float(i)} for i in range(5)}
    assert summarize_step(collapsed, {"completed": 5}) == summarize_step(
        collapsed, {"completed": 5}, derived=None, seed=7
    )
```

The third test is the regression guard: a run with no `aggregate` must be unchanged.

- [ ] **Step 2: Run to verify they fail, then implement**

Read the current `summarize_step` body before editing. Recorded columns keep their existing treatment — `basis: units`, `t_over_units`. Derived metrics are added after, each with the bootstrap interval over **the values the metric was derived from**; where a derived metric has no obvious source column, resample the unit count's worth of the collapsed rows so the interval still reflects unit-level uncertainty, and say in your report which you did.

- [ ] **Step 3: Wire `aggregate` into `cli.py`**

Call it **once per recording step**, passing a `UnitTable` over that step's collapsed rows and the condition's resolved `cfg`, coercing the return through `coerce_scalars` with the template's name as `where`, then handing the result to `summarize_step` as `derived`. The seed is `resample_seed(digest)`.

- [ ] **Step 4: End-to-end test**

Use `run_a_project` from `tests/test_cli.py` — **reuse it, do not add a second driver**. A template whose `aggregate` derives a value from a recorded column should produce that metric in `run.yaml` with `basis: units`, `method: percentile_over_units`, and a `ci95`.

- [ ] **Step 5: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/stats.py src/publishable/cli.py tests/
git commit -m "Report a derived metric with a resampled interval"
```

---

### Task 7: `repeat_spread`

**Files:**
- Modify: `src/publishable/stats.py`, `src/publishable/cli.py`
- Test: `tests/test_stats.py`

**Interfaces:**
- Consumes: `RepeatLevel` from `replication` (`kind`, `members`, `n`); the per-execution results.
- Produces: `repeat_spread(results, step_name, condition_index, levels) -> list[dict[str, Any]]`

`docs/reference.md` § A `batch` says *when*, not *what* fixes the shape as one entry per level, **outer to inner**:

```yaml
repeat_spread:
  - {std: 0.019, n: 5, kind: batch}
  - {std: 0.004, n: 3, kind: seed}
```

That contrast is why the `batch` kind exists: as a single figure, how much the *world* moved and how much the *RNG* moved would be indistinguishable, and the larger mislabelled as randomness the tool controls.

**A `fold` level contributes no entry.** Each unit appears in exactly one fold, so there is nothing to average across — which is why S3c made the collapse concatenate there rather than average.

- [ ] **Step 1: Write the failing tests**

```python
def test_one_entry_per_level_outer_to_inner():
    levels = resolve_repeats(
        cfg([{"kind": "batch", "n": 2}, {"kind": "seed", "n": 2}]), "d"
    )
    spread = repeat_spread(_results_for_batch_seed(), "analyze", 0, levels)
    assert [e["kind"] for e in spread] == ["batch", "seed"]
    assert [e["n"] for e in spread] == [2, 2]
    assert all(e["std"] >= 0 for e in spread)


def test_a_fold_level_contributes_no_entry():
    """Each unit is in exactly one fold, so there is nothing to average across."""
    levels = resolve_repeats(cfg([{"kind": "fold", "k": 2}]), "d", unit_count=4)
    assert repeat_spread(_results_for_folds(), "analyze", 0, levels) == []


def test_a_single_member_level_reports_zero_spread_not_none():
    """One repeat has no dispersion; reporting 0.0 with n: 1 says that plainly,
    where omitting the entry would read as 'this level was not run'."""
    levels = resolve_repeats(cfg([{"kind": "seed", "n": 1}]), "d")
    spread = repeat_spread(_results_for_one_seed(), "analyze", 0, levels)
    assert spread == [{"std": 0.0, "n": 1, "kind": "seed"}]
```

`_results_for_*` stand for fixtures built with `tests/test_stats.py`'s existing `_repeat_result(step, repeat_label, condition_index, rows_by_unit, skipped=...)` helper. **Read it and reuse it.**

- [ ] **Step 2: Run to verify they fail, then implement**

For each non-`fold` level, compute the per-member mean of the step's recorded values across the units that member saw, then the population standard deviation of those member means. Outer to inner, one entry per level.

- [ ] **Step 3: Carry it into the record**

`repeat_spread` belongs beside the metric in `aggregated`. Read how `summarize_step`'s output is placed into the record in `cli.py`/`run_record.py` and follow it; report where you attached it.

- [ ] **Step 4: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/stats.py src/publishable/cli.py tests/
git commit -m "Report dispersion once per repeat level"
```

---

### Task 8: The five refusals

**Files:**
- Modify: `src/publishable/validate.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: the `Collector` convention — `validate.py` **collects** findings and never raises to report one.
- Produces: `E-STATS-CONTRASTS-UNSUPPORTED`, `E-STATS-RESAMPLE-UNSUPPORTED`, `E-STATS-NULLTEST-UNSUPPORTED`, `E-STATS-REPORTBY-UNSUPPORTED`, `E-HYPOTHESIS-UNSUPPORTED`.

**This closes a live defect.** A declared `hypotheses` block validates clean and is ignored today, as do `statistics.contrasts`, `.resample`, `.null_test`, and `.report_by`. A config declaring a 2000-draw bootstrap and a pre-registered hypothesis runs, reports success, and does neither — the silent-no-op class this project treats as worst.

`statistics.correction` is the counter-example and stays exactly as it is: **disclosed**, with `W-STATS-FAMILY` warning and every metric recording `correction: null`. Do not refuse it.

Each message says the block is specified but not implemented in this build and will be honored later, matching the register the other `-UNSUPPORTED` messages use. Read two of them before writing yours.

- [ ] **Step 1: Write the failing tests**

```python
def test_declared_contrasts_are_refused(write_config):
    assert "E-STATS-CONTRASTS-UNSUPPORTED" in codes(write_config(
        {"statistics": {"contrasts": [{"id": "s", "of": "a", "against": "b"}]}}))


def test_a_declared_resample_is_refused(write_config):
    assert "E-STATS-RESAMPLE-UNSUPPORTED" in codes(write_config(
        {"statistics": {"resample": {"method": "bootstrap", "n": 2000}}}))


def test_a_declared_null_test_is_refused(write_config):
    assert "E-STATS-NULLTEST-UNSUPPORTED" in codes(write_config(
        {"statistics": {"null_test": {"method": "permutation", "n": 5000}}}))


def test_declared_report_by_is_refused(write_config):
    assert "E-STATS-REPORTBY-UNSUPPORTED" in codes(write_config(
        {"statistics": {"report_by": ["sex"]}}))


def test_a_declared_hypothesis_is_refused(write_config):
    assert "E-HYPOTHESIS-UNSUPPORTED" in codes(write_config(
        {"hypotheses": [{"id": "h1", "metric": "r", "direction": "greater"}]}))


def test_empty_declarations_are_not_refused(write_config):
    """The generated config ships these keys empty; only a real declaration is
    refused, or every scaffolded project would fail to validate."""
    found = codes(write_config(
        {"statistics": {"contrasts": [], "resample": None, "null_test": None,
                        "report_by": []},
         "hypotheses": []}))
    assert not [c for c in found if "UNSUPPORTED" in c and ("STATS" in c or "HYPOTHESIS" in c)]


def test_correction_is_still_not_refused(write_config):
    found = codes(write_config({"statistics": {"correction": "holm"}}))
    assert not [c for c in found if c.startswith("E-STATS")]
```

The sixth test is the one that matters most: `materialize.py` writes these keys empty into every generated config, so refusing presence rather than a real declaration would break `new` → `validate` for every project.

- [ ] **Step 2: Run to verify they fail, then implement**

Run: `uv run pytest tests/test_validate.py -k unsupported -v`

Add the checks where the other `-UNSUPPORTED` refusals live. Grep `docs/reference.md` for each identifier before minting it, and record the new ones in `docs/superpowers/spec-defects.md`.

- [ ] **Step 3: Run the full suite and commit**

Confirm `uv run publishable new` → `validate` on a fresh scaffold still passes — the empty-declaration test covers it, but a scaffold is the real check.

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/validate.py tests/test_validate.py
git commit -m "Refuse the statistics blocks this build does not honor"
```

---

### Task 9: The acceptance test

**Files:**
- Test: `tests/test_cli.py`
- Modify: whatever the test shows is still unwired.

**Interfaces:**
- Consumes: everything above.
- Produces: no new source interfaces.

Every earlier task is testable in isolation, and this project has twice shipped a subsystem that was green in unit tests and unreachable from `main(["run", ...])`. **Report every `src/` change you need here — each one is a piece an earlier task left inert.**

- [ ] **Step 1: Write the acceptance test**

```python
def test_a_derived_metric_end_to_end(tmp_path, capsys):
    doc = run_a_project(tmp_path, capsys=capsys, aggregate_returns="mean_pred")
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    metric = _first_metric(run, "mean_pred")
    assert metric["basis"] == "units"
    assert metric["method"] == "percentile_over_units"
    assert metric["ci95"] is not None
    assert metric["cohens_d"] is None
    assert metric["correction"] is None      # S4b's job; disclosed, not silently corrected


def test_the_same_digest_reproduces_the_derived_interval(tmp_path, capsys):
    a = run_a_project(tmp_path / "a", capsys=capsys, aggregate_returns="mean_pred")
    b = run_a_project(tmp_path / "b", capsys=capsys, aggregate_returns="mean_pred")
    ra = yaml.safe_load((a["run_dir"] / "run.yaml").read_text())
    rb = yaml.safe_load((b["run_dir"] / "run.yaml").read_text())
    assert _first_metric(ra, "mean_pred")["ci95"] == _first_metric(rb, "mean_pred")["ci95"]


def test_a_project_without_aggregate_reports_no_derived_metric(tmp_path, capsys):
    doc = run_a_project(tmp_path, capsys=capsys)
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    assert _first_metric(run, "mean_pred") is None
```

`run_a_project` will need a way to scaffold a template with an `aggregate`; extend it **additively** with a defaulted keyword so its existing callers are untouched, and say what you added. `_first_metric(run, name)` is a small local helper — write it if the file has none.

- [ ] **Step 2: Verify by hand**

Scaffold a project, give its template an `aggregate` deriving a value from a recorded column, run it, and paste `run.yaml`'s `aggregated` block into your report. A test can share a bug with the code it tests; a record you read cannot.

- [ ] **Step 3: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add tests/ src/
git commit -m "Derive a metric from the unit table end to end"
```

---

## Self-Review

**Spec coverage.** The coercion rule → Tasks 1–2. `UnitTable`'s four operations → Task 3. The bootstrap → Task 4. `aggregate` on `BaseTemplate` → Task 5. Derived metrics reaching the record, plus the `E-STEP-KEY-COLLISION` reuse → Task 6. `repeat_spread` → Task 7. The five refusals → Task 8. Acceptance → Task 9. No spec section is unassigned.

**Placeholders.** Every code step carries code and every test step carries tests. Six tasks name an existing helper (`make_io`, `_u`, `_repeat_result`, `run_a_project`, `cfg`, `codes`) rather than inventing one, and each says to read the file and match its idiom — a deliberate instruction, since a second idiom is the defect.

**Type consistency.** `UnitTable(collapsed: dict[str, dict[str, float]])` is built in Task 3 and consumed identically in Tasks 5 and 6. `percentile_over_units(values, seed, draws, confidence) -> Interval | None` from Task 4 is called in Task 6 with the seed from `resample_seed(digest)`. `coerce_scalars(values, where)` from Task 1 is called at three sites across Tasks 2 and 6. Every new parameter is added **last and defaulted** — `summarize_step` gains `derived` and `seed`; `run_a_project` gains a scaffold keyword — so no existing call site breaks.

**Four assumptions verified against the codebase before writing.** `BaseTemplate` lives in `templates/base.py`, not a `base_template.py`. `E-STEP-KEY-COLLISION` already exists and `reference.md` § Errors core raises already names the derived-vs-recorded case, so Task 6 reuses rather than mints. The per-value coercion rule is implemented **nowhere** — the two checks that share `E-STEP-RETURN-TYPE` are a column-consistency check and a return-shape check, which is why Task 2's bar is that no existing test changes. And both halves of the missing rule are live defects, reproduced: `numpy.float64` raises `RepresenterError` from `yaml.safe_dump`, and a nested mapping serializes silently.

**The risk this plan carries.** Task 6 is where a derived metric's interval is computed, and the spec leaves one thing genuinely open: which values a derived metric resamples when it has no single source column. The task says to decide and report rather than guess silently, and the whole-branch review should check that decision against `reference.md` § How a metric becomes a number rather than accepting it.
