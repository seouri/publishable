# Summary `Estimate` (S5a) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A `summary` step can return an interval it computed itself, and the record says who computed it.

**Architecture:** A new frozen `Estimate` dataclass, exported from `publishable`. `coerce_scalars` — the one place that decides what a step's return may contain — gains a scope-aware exemption that admits an `Estimate` at `summary` scope, coerces its own fields, and refuses it anywhere else. `run_record` expands it into the record with `reported: true`, which is the whole feature: without that field an author's interval is indistinguishable from one core derived from the unit table.

**Tech Stack:** Python 3.11+, `uv`, pytest, ruff, mypy, numpy, scipy.

## Global Constraints

- Python >= 3.11.
- Runtime dependencies are exactly `pyyaml`, `numpy`, `scipy`, `pyarrow`. Adding one is out of scope.
- ruff: line-length 100, select `["E","F","I","UP","B"]`. mypy: strict over `src/`.
- Commands: `uv run pytest`, `uv run ruff check .`, `uv run mypy`. (`ruff format` reformats ~33 pre-existing files — do not run it; `ruff check` is the gate.)
- `×`, not `x`, for multiplication — including inside fenced blocks and commit messages.
- `coercion.py`, `estimate.py`, `stats.py`, `strata.py`, `contrasts.py`, `correction.py`, `sweep.py` are **pure**: no filesystem, and no runtime import of `config`, `artifacts`, `runner`, or `cli`.
- `artifacts.py` is the only module that writes inside a run directory.
- Everything a user writes against is imported from `publishable` itself; `reference.md` § The importable surface is the enumerated list, and it already names `Estimate`.
- Core raises `PublishableError` → `ContractError` / `ArtifactError` → `ArtifactExistsError`, each carrying the same stable `E-` identifier a diagnostic prints.
- Every `E-`/`W-` identifier must have a test that produces it — through `main(["run", ...])` for a run-time code.
- An identifier the four documents do not name needs a `docs/superpowers/spec-defects.md` entry (that file is gitignored; write it anyway).
- **Do not amend a reviewed commit.** New commits only.
- **No document changes in this slice.** `Estimate` is already specified in `reference.md` § `Estimate` and already enumerated in § The importable surface. If you believe a document is wrong, report it rather than editing it.

---

## File Structure

| File | Responsibility in this slice |
|---|---|
| `src/publishable/estimate.py` *(new)* | **Pure.** The frozen `Estimate` dataclass and nothing else |
| `src/publishable/__init__.py` | Export `Estimate` |
| `src/publishable/coercion.py` | The `summary`-scope exemption, field coercion, `E-STEP-ESTIMATE-SCOPE`, `E-STEP-ESTIMATE-METHOD` |
| `src/publishable/runner.py` | Pass the execution's scope to `coerce_scalars` |
| `src/publishable/run_record.py` | Expand an `Estimate` into the summary record with `reported: true` |
| `src/publishable/cli.py` | `W-STEP-ESTIMATE-N` |

**Read before starting:** `docs/superpowers/specs/2026-08-10-summary-estimate-design.md`, and `reference.md` § `Estimate` carries your interval without core claiming it.

**Facts established while writing this plan, so you need not re-derive them:**

- `coerce_scalars` currently **already refuses** a dataclass instance: `Estimate` has no `__len__`, `__float__`, `__index__` or `__bool__`, so it falls through to `_refuse`. Verified by probe. That is the behaviour you are carving an exception into, and it is the behaviour that must survive at every non-summary scope.
- `runner.py`'s only coercion call is `returned = coerce_scalars(returned, execution.step_name)`, and `execution.scope` is in scope at that line.
- `executions.jsonl` writes only `step`, `scope`, `condition`, `repeat`, `status`, `started_at`, `wall_seconds`, `error` — never `returned`. So an `Estimate` cannot reach the JSON ledger, and no JSON-serialization work is needed.
- `run_record.py` assigns `summary[e.step_name] = r.returned` verbatim for a `summary`-scoped execution. That verbatim assignment is what Task 3 replaces.

---

### Task 1: The `Estimate` type

**Files:**
- Create: `src/publishable/estimate.py`
- Modify: `src/publishable/__init__.py`
- Test: `tests/test_estimate.py` *(new)*

**Interfaces:**
- Consumes: nothing.
- Produces: `Estimate(value: float, ci95: list[float] | None = None, n: int | None = None, method: str | None = None)`, frozen, importable as `from publishable import Estimate`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_estimate.py`:

```python
import dataclasses

import pytest

from publishable import Estimate


def test_an_estimate_is_importable_from_the_package_root():
    """`reference.md` § The importable surface: everything a user writes against
    is imported from `publishable` itself, and that section's table already
    enumerates `Estimate`. A user reaching into `publishable.estimate` would be
    depending on where core happens to keep the file."""
    assert Estimate(value=0.031).value == 0.031


def test_only_value_is_required():
    """A summary step may report a number with no interval — `converged: True`
    beside it in the documented example is a bare value, and a bare `Estimate`
    is the same claim with the marking."""
    est = Estimate(value=0.031)
    assert est.ci95 is None
    assert est.n is None
    assert est.method is None


def test_it_is_frozen():
    """Core stores what the step returned. A mutable Estimate would let a later
    step or a template edit a number the record attributes to the step that
    computed it."""
    est = Estimate(value=0.031)
    with pytest.raises(dataclasses.FrozenInstanceError):
        est.value = 0.999


def test_it_constructs_without_validating():
    """Every rule about an Estimate is a diagnostic core emits, not an exception
    user code trips over: a `ValueError` from a constructor inside a plugin
    surfaces as a bare traceback with no identifier, and this repo's contract is
    that a failure prints a stable `E-` code. `ci95` without `method` is
    `E-STEP-ESTIMATE-METHOD` at coercion time (Task 2), not a raise here."""
    est = Estimate(value=0.031, ci95=[0.008, 0.055])
    assert est.method is None
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_estimate.py -v`
Expected: FAIL with `ImportError: cannot import name 'Estimate' from 'publishable'`.

- [ ] **Step 3: Implement**

Create `src/publishable/estimate.py`:

```python
"""An interval a `summary` step computed itself.

`docs/reference.md` § `Estimate`: returned as a bare dict, an interval "is a key
core can't tell from any other — `report` won't render it as an interval,
`study add` can't see the denominator it's over, and nothing in the record
distinguishes it from one core computed from the unit table." This type is that
distinction, and `reported: true` in the record is what it buys.

Deliberately no validation here. The three rules `reference.md` states —
`method` required whenever `ci95` is present, a surfaced missing `n`, and
`summary` scope only — are all diagnostics core emits when the return is
recorded, each carrying an `E-`/`W-` identifier a reader can grep. A raise from
this constructor would land inside a plugin's `run` as a bare traceback with no
identifier, which is the shape every diagnostic in this codebase exists to
replace.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Estimate:
    """`value` plus the optional interval a step computed for it.

    `ci95` is a `list` rather than a tuple, matching how `reference.md`'s example
    constructs one and how the record dumps it; that makes this frozen dataclass
    unhashable, and nothing keys on it.
    """

    value: float
    ci95: list[float] | None = None
    n: int | None = None
    method: str | None = None
```

In `src/publishable/__init__.py`, add the import and the `__all__` entry alongside the existing exports — read how `Unit` and `Param` are exported there and follow it exactly, keeping any alphabetical ordering the file already has (ruff `I` will fail otherwise).

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_estimate.py -v && uv run ruff check . && uv run mypy`
Expected: PASS.

- [ ] **Step 5: Check whether a test enumerates the importable surface**

Run: `grep -rn "importable\|__all__" tests/ | head`

`reference.md` § The importable surface is an enumerated list, and a test may pin it. If one exists, add `Estimate` to it. If none exists, say so in your report — do not create one; that is a larger decision than this task.

- [ ] **Step 6: Commit**

```bash
git add src/publishable/estimate.py src/publishable/__init__.py tests/test_estimate.py
git commit -m "Add the Estimate a summary step returns"
```

---

### Task 2: The `summary`-scope exemption in coercion

**Files:**
- Modify: `src/publishable/coercion.py`, `src/publishable/runner.py`
- Test: `tests/test_coercion.py`

**Interfaces:**
- Consumes: `Estimate` from Task 1.
- Produces: `coerce_scalars(values: dict[str, Any], where: str, *, scope: str | None = None) -> dict[str, Any]`. The keyword defaults to `None`, so the two existing call sites (`artifacts.py`'s `io.record`, `cli.py`'s `aggregate`) keep refusing an `Estimate` without being touched.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_coercion.py` (read its existing imports and helpers first):

```python
import numpy as np

from publishable import Estimate
from publishable.errors import ContractError


def test_an_estimate_passes_through_at_summary_scope():
    est = Estimate(value=0.031, ci95=[0.008, 0.055], n=612, method="mixed model, REML")
    got = coerce_scalars({"delta": est}, "step03_site_model", scope="summary")
    assert got["delta"] == est


def test_an_estimate_is_refused_at_every_other_scope():
    """`reference.md` § `Estimate`: elsewhere it "would be a way to attach an
    interval to a per-execution return value, and `per_repeat` is *exactly what
    the step returned*" — an interval per repeat is either a claim about one
    execution or an accident."""
    est = Estimate(value=0.031)
    for scope in ("repeat", "condition", "run", None):
        with pytest.raises(ContractError) as excinfo:
            coerce_scalars({"delta": est}, "step03_analyze", scope=scope)
        assert excinfo.value.code == "E-STEP-ESTIMATE-SCOPE"


def test_ci95_without_method_is_refused():
    """`reference.md`: "`method` is required whenever `ci95` is present. An
    interval nobody labelled is unreadable." The check is a declaration check,
    not a judgement about the statistics."""
    est = Estimate(value=0.031, ci95=[0.008, 0.055])
    with pytest.raises(ContractError) as excinfo:
        coerce_scalars({"delta": est}, "step03_site_model", scope="summary")
    assert excinfo.value.code == "E-STEP-ESTIMATE-METHOD"


def test_a_bare_estimate_without_ci95_needs_no_method():
    got = coerce_scalars({"delta": Estimate(value=0.031)}, "s", scope="summary")
    assert got["delta"].method is None


def test_an_estimates_own_fields_are_coerced():
    """The half a narrower exemption would miss. `coerce_scalars` exists because
    an uncoerced NumPy scalar "reaches `yaml.safe_dump` and raises
    `RepresenterError` while writing `run.yaml` — a traceback rather than a
    diagnostic", and a mixed model hands back NumPy scalars more often than a
    derived metric does, not less. Passing the Estimate through untouched would
    reintroduce that defect one level of nesting down."""
    est = Estimate(
        value=np.float64(0.031),
        ci95=[np.float64(0.008), np.float64(0.055)],
        n=np.int64(612),
        method="mixed model, REML",
    )
    got = coerce_scalars({"delta": est}, "step03_site_model", scope="summary")["delta"]
    assert type(got.value) is float
    assert [type(v) for v in got.ci95] == [float, float]
    assert type(got.n) is int
    assert got.value == 0.031


def test_something_structural_inside_an_estimate_is_still_refused():
    """The exemption admits an `Estimate`, not everything inside one."""
    est = Estimate(value=[0.031], method="m")  # type: ignore[arg-type]
    with pytest.raises(ContractError):
        coerce_scalars({"delta": est}, "step03_site_model", scope="summary")


def test_a_bare_value_beside_an_estimate_is_untouched():
    """The documented example returns `converged: True` alongside. A bare value
    stays bare — it is not wrapped into the Estimate shape."""
    got = coerce_scalars(
        {"delta": Estimate(value=0.031), "converged": True}, "s", scope="summary"
    )
    assert got["converged"] is True
```

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_coercion.py -k estimate -v`
Expected: FAIL — `coerce_scalars` takes no `scope` keyword.

- [ ] **Step 3: Implement**

In `coercion.py`, import `Estimate` (`from publishable.estimate import Estimate` — `estimate.py` imports nothing from the package, so there is no cycle), and change the entry point:

```python
def coerce_scalars(
    values: dict[str, Any], where: str, *, scope: str | None = None
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in values.items():
        if isinstance(value, Estimate):
            out[key] = _coerce_estimate(key, value, where, scope)
        else:
            out[key] = _coerce_one(key, value, where)
    return out
```

Extend the module docstring to name the exception, since that docstring currently states the rule without it. Then add:

```python
def _coerce_estimate(key: str, value: "Estimate", where: str, scope: str | None) -> "Estimate":
    """The one exception to "anything structural is a `ContractError`".

    `CLAUDE.md`'s invariant: a step's `run` and a template's `aggregate` return a
    flat mapping of scalars, "with a NumPy scalar coerced, anything structural a
    `ContractError`, and an `Estimate` at `summary` scope the one exception".
    That sentence is this function's whole justification, which is why the
    exception lives here rather than being special-cased in `runner.py`: one
    place decides what a step's return may contain.

    The fields are coerced, not merely passed through. A mixed model hands back
    `numpy.float64` at least as often as a derived metric does, and an uncoerced
    one reaches `yaml.safe_dump` and raises `RepresenterError` while writing
    `run.yaml` — the traceback-instead-of-diagnostic this module exists to
    prevent, one level of nesting down.
    """
    if scope != "summary":
        raise ContractError(
            f"{where} gave {key!r} an Estimate at scope {scope!r}; an Estimate is accepted "
            "at scope `summary` only, because elsewhere it would attach an interval to one "
            "execution's return value — `per_repeat` is exactly what the step returned, and "
            "an interval per repeat is either a claim about that one execution or an accident",
            code="E-STEP-ESTIMATE-SCOPE",
        )
    if value.ci95 is not None and not value.method:
        raise ContractError(
            f"{where} gave {key!r} a ci95 with no `method`; an interval nobody labelled is "
            "unreadable, and core can enforce that a label exists without having any opinion "
            "on whether it is the right method",
            code="E-STEP-ESTIMATE-METHOD",
        )
    return Estimate(
        value=_coerce_one(f"{key}.value", value.value, where),
        ci95=(
            None
            if value.ci95 is None
            else [_coerce_one(f"{key}.ci95", v, where) for v in value.ci95]
        ),
        n=None if value.n is None else _coerce_one(f"{key}.n", value.n, where),
        method=value.method,
    )
```

Then in `runner.py`, pass the scope at the one call site:

```python
            returned = coerce_scalars(returned, execution.step_name, scope=execution.scope)
```

- [ ] **Step 4: Run the full suite**

Run: `uv run pytest -q && uv run ruff check . && uv run mypy`

Expected: all pass. The two untouched call sites (`artifacts.py:263`, `cli.py`'s two `aggregate` calls) keep the default `scope=None` and therefore keep refusing an `Estimate` — which is correct: a template's `aggregate` returns metrics core computes over the unit table, and an interval it asserted itself is exactly what `Estimate` is *not* for there.

- [ ] **Step 5: Prove the tests discriminate**

| Mutation in `coercion.py` | Must fail |
|---|---|
| Drop the `scope != "summary"` guard | `test_an_estimate_is_refused_at_every_other_scope` |
| Return `value` unchanged instead of rebuilding it | `test_an_estimates_own_fields_are_coerced` |
| Drop the `ci95 is not None and not method` check | `test_ci95_without_method_is_refused` |
| Coerce only `value`, leaving `ci95` and `n` | `test_an_estimates_own_fields_are_coerced` |

Apply each, run the named test, confirm it fails, revert with `git checkout -- src/publishable/coercion.py`, and confirm `git status --porcelain` is empty before the next.

- [ ] **Step 6: Commit**

```bash
git add src/publishable/coercion.py src/publishable/runner.py tests/test_coercion.py
git commit -m "Admit an Estimate at summary scope, and coerce what it holds"
```

---

### Task 3: The record shape

**Files:**
- Modify: `src/publishable/run_record.py`
- Test: `tests/test_run_record.py`

**Interfaces:**
- Consumes: `Estimate` from Task 1; coercion from Task 2 guarantees every `Estimate` reaching here has already had its fields coerced and its `method` checked.
- Produces: `results.summary.<step>.<key>` as `{"value", "reported": True, "ci95", "n", "method"}` for an `Estimate`, and the bare value unchanged for anything else.

- [ ] **Step 1: Write the failing tests**

Read `tests/test_run_record.py` for how it builds an `ExecutionResult` — you need a `summary`-scoped one whose `returned` holds an `Estimate` — then append:

```python
def test_a_summary_estimate_is_recorded_as_reported():
    """`reference.md` § `Estimate`: "`reported: true` is the whole mechanism, and
    it is an attribution rather than an endorsement." Without it, an author's
    interval and one core derived from the unit table are indistinguishable in
    the record, which the document calls the worse of the two situations."""
    est = Estimate(value=0.031, ci95=[0.008, 0.055], n=612, method="mixed model, REML")
    doc = assemble_run_yaml(**_minimal_kwargs(summary_returned={"site_adjusted_delta": est}))
    entry = doc["results"]["summary"]["step03_site_model"]["site_adjusted_delta"]
    assert entry == {
        "value": 0.031,
        "reported": True,
        "ci95": [0.008, 0.055],
        "n": 612,
        "method": "mixed model, REML",
    }


def test_a_bare_value_beside_an_estimate_stays_bare():
    """The documented example returns `converged: True` alongside, and it is not
    wrapped: a value with no interval makes no attribution claim, so there is
    nothing for `reported` to attribute."""
    doc = assemble_run_yaml(
        **_minimal_kwargs(
            summary_returned={"delta": Estimate(value=0.031), "converged": True}
        )
    )
    summary = doc["results"]["summary"]["step03_site_model"]
    assert summary["converged"] is True


def test_absent_estimate_fields_are_written_as_null():
    """Unlike the comparison blocks, whose absent keys mean no comparison was
    made, a summary entry always exists and its fields are simply unset. A
    reader comparing two summary blocks should not have to tell "no interval"
    from "a key I forgot to look for"."""
    doc = assemble_run_yaml(**_minimal_kwargs(summary_returned={"d": Estimate(value=0.031)}))
    entry = doc["results"]["summary"]["step03_site_model"]["d"]
    assert entry == {"value": 0.031, "reported": True, "ci95": None, "n": None, "method": None}
```

`_minimal_kwargs(summary_returned=...)` is a helper you write, built from whatever `assemble_run_yaml` already requires in that file's existing tests — do not invent parameters it does not take.

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_run_record.py -k estimate -v`
Expected: FAIL — the `Estimate` object lands in the record verbatim rather than as a mapping.

- [ ] **Step 3: Implement**

In `run_record.py`, replace the verbatim assignment for a `summary`-scoped execution:

```python
        if e.scope == "summary":
            summary[e.step_name] = _summary_values(r.returned)
            continue
```

and add:

```python
def _summary_values(returned: dict[str, Any]) -> dict[str, Any]:
    """A summary step's return, with each `Estimate` expanded and every other
    value left exactly as it came back.

    `reference.md` § `Estimate` shows both in one block: the expanded
    `site_adjusted_delta` beside a bare `converged: true`. Only a value carrying
    an interval makes an attribution claim, so only that one gets `reported`.
    """
    out: dict[str, Any] = {}
    for key, value in returned.items():
        if isinstance(value, Estimate):
            out[key] = {
                "value": value.value,
                "reported": True,
                "ci95": value.ci95,
                "n": value.n,
                "method": value.method,
            }
        else:
            out[key] = value
    return out
```

Key order matters for the record's readability: `value` then `reported` then the interval fields, matching the documented example.

- [ ] **Step 4: Run the full suite**

Run: `uv run pytest -q && uv run ruff check . && uv run mypy`

- [ ] **Step 5: Prove the tests discriminate**

| Mutation | Must fail |
|---|---|
| Omit `"reported": True` | `test_a_summary_estimate_is_recorded_as_reported` |
| Wrap every value, not only an `Estimate` | `test_a_bare_value_beside_an_estimate_stays_bare` |
| Omit `ci95`/`n`/`method` when they are `None` | `test_absent_estimate_fields_are_written_as_null` |

- [ ] **Step 6: Commit**

```bash
git add src/publishable/run_record.py tests/test_run_record.py
git commit -m "Record who computed a summary interval"
```

---

### Task 4: `W-STEP-ESTIMATE-N`, and the spec-defects entries

**Files:**
- Modify: `src/publishable/cli.py`
- Test: `tests/test_cli.py`
- Modify: `docs/superpowers/spec-defects.md` *(gitignored; write it anyway)*

**Interfaces:**
- Consumes: `Estimate`; the `results` list `command_run` already holds after `execute_plan`.
- Produces: `W-STEP-ESTIMATE-N`.

**Determine before writing:** which `Collector` this warning belongs in. `run_record.assemble_run_yaml` takes no `Collector`, so the warning cannot live there. `command_run` has the validate-time collector (`c`) and a second one the aggregate phase warns into. Read both and pick the one whose findings are printed with the run's other run-time warnings — `W-STATS-AGGREGATE-FAILED` is the sibling to follow. Say which you chose and why in your report.

- [ ] **Step 1: Write the failing test**

```python
_ESTIMATE_SUMMARY_STEP = '''\
# src/{pkg}/steps/step02_summarize.py — generated, and runnable as-is
from publishable import BaseStep, Estimate


class Step(BaseStep):
    scope = "summary"

    def run(self, cfg, io):
        # An interval with no stated denominator, which is exactly the
        # disclosure risk `limits.min_reported_n` exists to catch.
        return {{"adjusted": Estimate(value=0.031, ci95=[0.008, 0.055],
                                      method="mixed model, REML")}}
'''


def test_an_estimate_with_an_interval_and_no_n_warns(tmp_path, capsys, monkeypatch):
    """`reference.md` § `Estimate`: "`n` is optional but its absence is
    surfaced, because an interval with no stated denominator is exactly the
    disclosure risk `min_reported_n` exists to catch." Optional means the run
    completes; surfaced means it does not pass in silence."""
    doc = run_a_project(tmp_path, capsys=capsys, units=10, extra_steps=["step02_summarize"])
    assert "W-STEP-ESTIMATE-N" in doc["stdout"]
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entry = run["results"]["summary"]["step02_summarize"]["adjusted"]
    assert entry["reported"] is True
    assert entry["n"] is None


_ESTIMATE_WITH_N_SUMMARY_STEP = '''\
# src/{pkg}/steps/step02_summarize.py — generated, and runnable as-is
from publishable import BaseStep, Estimate


class Step(BaseStep):
    scope = "summary"

    def run(self, cfg, io):
        return {{"adjusted": Estimate(value=0.031, ci95=[0.008, 0.055], n=612,
                                      method="mixed model, REML")}}
'''


def test_an_estimate_with_an_n_does_not_warn(tmp_path, capsys, monkeypatch):
    """The other half: a stated denominator is the whole point, so supplying one
    must be silent. A warning that fires either way teaches a reader to ignore
    it."""
    doc = run_a_project(
        tmp_path, capsys=capsys, units=10, extra_steps=["step02_summarize"]
    )
    assert "W-STEP-ESTIMATE-N" not in doc["stdout"]
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    assert run["results"]["summary"]["step02_summarize"]["adjusted"]["n"] == 612


_BARE_ESTIMATE_SUMMARY_STEP = '''\
# src/{pkg}/steps/step02_summarize.py — generated, and runnable as-is
from publishable import BaseStep, Estimate


class Step(BaseStep):
    scope = "summary"

    def run(self, cfg, io):
        return {{"adjusted": Estimate(value=0.031)}}
'''


def test_an_estimate_with_no_interval_does_not_warn(tmp_path, capsys, monkeypatch):
    """`n` is surfaced because an *interval* needs a denominator. A value with no
    interval makes no such claim, so warning about its missing `n` would fire on
    a shape that is entirely correct."""
    doc = run_a_project(
        tmp_path, capsys=capsys, units=10, extra_steps=["step02_summarize"]
    )
    assert "W-STEP-ESTIMATE-N" not in doc["stdout"]
```

One thing to work out rather than guess, and report what you found: **how to make a generated project run a `summary`-scoped step**. `run_a_project`'s `extra_steps` calls `generate_step`, which produces a `repeat`-scoped step; the fixtures in this file override `STARTER_STEP` by monkeypatching `experiment_gen`. Find how an existing test gets a non-`repeat` scope into a generated project — `grep -rn 'scope = "summary"' tests/` — and follow it. If no test does, monkeypatch the generated step's source the way `_METHOD_VARYING_STEP` does, with `scope = "summary"` in the template, and say so. The three fixtures above assume that route; adapt them to whatever the file's actual mechanism turns out to be, keeping the assertions identical.

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_cli.py -k estimate -v`
Expected: the first FAILs because no such identifier is emitted.

- [ ] **Step 3: Implement**

In `command_run`, after `execute_plan` returns and beside where the other run-time warnings are collected:

```python
        for r in results:
            if r.execution.scope != "summary":
                continue
            for key, value in (r.returned or {}).items():
                if isinstance(value, Estimate) and value.ci95 is not None and value.n is None:
                    aggregate_c.warn(
                        "W-STEP-ESTIMATE-N",
                        f"{r.execution.step_name}.{key}",
                        "reports a ci95 with no `n`; an interval with no stated denominator "
                        "is the disclosure risk `limits.min_reported_n` exists to catch, and "
                        "`study add` cannot check what it cannot see",
                    )
```

Use whichever collector name you determined above rather than `aggregate_c` if it differs. This is a two-line condition at the record site rather than a flag threaded out of `coerce_scalars`: the pure function has no `Collector`, and S4c had to accept a `thin` flag for exactly that reason once — there is no need to repeat it where the caller can simply look.

- [ ] **Step 4: Run the full suite**

Run: `uv run pytest -q && uv run ruff check . && uv run mypy`

- [ ] **Step 5: Prove the test discriminates**

| Mutation | Must fail |
|---|---|
| Warn whenever `n is None`, even with no `ci95` | add a third test returning `Estimate(value=0.031)` alone and asserting no warning — write it, then run this mutation |
| Warn whenever `ci95` is present, regardless of `n` | `test_an_estimate_with_an_n_does_not_warn` |

- [ ] **Step 6: Record the three identifiers**

Append one `docs/superpowers/spec-defects.md` entry covering `E-STEP-ESTIMATE-SCOPE`, `E-STEP-ESTIMATE-METHOD` and `W-STEP-ESTIMATE-N`, in the shape the `E-STATS-CONTRAST-WITHIN` entry uses: quote the `reference.md` sentence each implements, and say why the document states the rule but names no identifier for it.

- [ ] **Step 7: Commit**

```bash
git add src/publishable/cli.py tests/test_cli.py
git commit -m "Surface an interval with no denominator"
```

---

### Task 5: The acceptance test

**Files:**
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: everything above.
- Produces: nothing importable. This task should need **zero** `src/` changes; if a test cannot pass without one, an earlier task left a gap and that is the finding, not a step.

- [ ] **Step 1: Write the end-to-end tests**

```python
_NUMPY_ESTIMATE_SUMMARY_STEP = '''\
# src/{pkg}/steps/step02_summarize.py — generated, and runnable as-is
import numpy as np

from publishable import BaseStep, Estimate


class Step(BaseStep):
    scope = "summary"

    def run(self, cfg, io):
        # What a real model hands back. Uncoerced, every one of these reaches
        # `yaml.safe_dump` and raises `RepresenterError` while writing run.yaml.
        return {{"adjusted": Estimate(value=np.float64(0.031),
                                      ci95=[np.float64(0.008), np.float64(0.055)],
                                      n=np.int64(612),
                                      method="mixed model, REML"),
                 "converged": True}}
'''


def test_a_summary_estimate_reaches_run_yaml_marked_as_reported(tmp_path, capsys, monkeypatch):
    """The slice end to end: a summary step returns an interval it computed, and
    the record says so. Every field survives the round trip through coercion and
    the record assembly, and the bare value beside it stays bare."""
    doc = run_a_project(
        tmp_path, capsys=capsys, units=10, extra_steps=["step02_summarize"]
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    summary = run["results"]["summary"]["step02_summarize"]
    assert summary["adjusted"] == {
        "value": 0.031,
        "reported": True,
        "ci95": [0.008, 0.055],
        "n": 612,
        "method": "mixed model, REML",
    }
    assert summary["converged"] is True


def test_a_numpy_estimate_reaches_the_record_without_a_traceback(
    tmp_path, capsys, monkeypatch
):
    """The failure mode `coerce_scalars` exists for, one level of nesting down.
    The run completing at all is half the assertion; the types are the other
    half, since `yaml.safe_dump` would have raised on a `numpy.float64`."""
    doc = run_a_project(
        tmp_path, capsys=capsys, units=10, extra_steps=["step02_summarize"]
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entry = run["results"]["summary"]["step02_summarize"]["adjusted"]
    assert type(entry["value"]) is float
    assert [type(v) for v in entry["ci95"]] == [float, float]
    assert type(entry["n"]) is int
    assert entry["value"] == 0.031


def test_a_summary_estimate_does_not_join_the_correction_family(tmp_path, capsys, monkeypatch):
    """`reference.md` § `Estimate`: core "never recomputes the value, never
    resamples it, never corrects it, and never counts it in the family."

    This holds structurally today — `correction.Member`s are built only from
    comparisons, and a summary step produces none — so the test pins a property
    that currently holds by accident. S5b's `verdict_rests_on: reported` will
    depend on it, and a property that holds by accident and one that holds by
    test are the same until someone edits.
    """
    sweep = {
        "baseline": {"analysis.method": "pearson"},
        "grid": {"analysis.method": ["spearman"]},
    }
    sizes = []
    for extra in ([], ["step02_summarize"]):
        doc = run_a_project(
            tmp_path / f"run{len(extra)}",
            capsys=capsys,
            units=40,
            sweep=sweep,
            extra_steps=extra,
        )
        run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
        entry = _first_contrast(run, "method=spearman")
        sizes.append((entry["family_size"], entry["family"]))
    assert sizes[0] == sizes[1]
```

Two things this task must get right, and both are places an earlier slice went wrong:

- The **family test's two runs must differ only in the summary step.** S4d's equivalent test had to declare the same unit attribute on both sides, because `data.units` is hashed wholly into `design_digest` and a one-sided declaration redrew every seed. Check that adding `extra_steps` does not itself move the digest — if it does, the comparison is measuring the wrong thing, and you must find a fixture where the only difference is the `Estimate`. Report what you found.
- The **`_METHOD_VARYING_STEP` fixture** is what gives the sweep a real numeric column to contrast; without it the scaffold's step records only a bool and there is no family to compare. Read how the existing contrast tests set it up and follow them.

- [ ] **Step 2: Run them**

Run: `uv run pytest tests/test_cli.py -k "summary_estimate or numpy_estimate" -v`
Expected: PASS with no `src/` change. If one fails, fix the **source** gap it found and say which earlier task should have covered it.

- [ ] **Step 3: Run the whole gate**

Run: `uv run pytest -q && uv run ruff check . && uv run mypy`

- [ ] **Step 4: Commit**

```bash
git add tests/test_cli.py
git commit -m "Report an author's own interval end to end"
```

---

## After the last task

- [ ] Re-read the design's § Scope and confirm every In row landed and no Out row (hypothesis evaluation, `evaluate_on`, the verdict fields, `declared_in`, retiring `E-HYPOTHESIS-UNSUPPORTED`) was touched.
- [ ] Confirm `docs/superpowers/spec-defects.md` carries the entry for the three new identifiers, and that the S5 line in the S4a carry table — "A `summary` step returning an `Estimate` will need an exemption at `runner.py`'s coercion call" — is marked resolved, noting that the exemption landed in `coercion.py` rather than at the call site and why.
- [ ] Run the **whole-branch review** over `merge-base(main, HEAD)..HEAD` on the most capable model available. It has found a Critical on every slice but the last two. Do not merge without it.
