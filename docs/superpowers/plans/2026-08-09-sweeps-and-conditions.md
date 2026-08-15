# Sweeps and Conditions (S3a) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a run compare things — a declared sweep expands into N conditions, each measured over the same roster, each carrying its own attrition and its own interval.

**Architecture:** One new pure module, `sweep.py`, turns a config into an ordered condition list with labels. The runner gains a per-condition `Config` so a step reads its own condition's values, and refuses a swept parameter at scopes where it has none. Everything else — `attrition`, `collapse_repeats`, `aggregated` — already takes a `condition_index`; S3a is the first slice that passes it a value other than `0`.

**Tech Stack:** Python 3.11+, PyYAML, numpy, scipy, pyarrow, pytest, ruff, mypy, uv.

## Global Constraints

- Python `requires-python = ">=3.11"`. Runtime dependencies stay exactly `pyyaml`, `numpy`, `scipy`, `pyarrow`.
- `src/` layout; import root `publishable`; only `src/publishable/__init__.py` is public API.
- Every error identifier starts `E-`, every warning `W-`. **Every identifier must have a test that produces it.**
- `ruff` line-length 100, select `["E","F","I","UP","B"]`; `mypy` strict over `src/`.
- `×` not `x` for multiplication in prose and comments.
- The four documents in `docs/` are NORMATIVE. Where code cannot follow them, stop and record it in `docs/superpowers/spec-defects.md`.
- **Unimplemented must mean refused, never silently ignored.** S1 shipped a silently-ignored `sweep`; S2 shipped a silently-ignored eligibility rule. This slice retires the refusal that fixed the first one.

## Existing interfaces (verified against the codebase — do not reimplement)

| Symbol | Signature |
|---|---|
| `scope.build_plan` | `(experiment, conditions: list[tuple[int, str \| None]], repeat_labels: list[str]) -> list[Execution]` |
| `scope.Execution` | fields `step_cls`, `step_name`, `scope`, `condition_index`, `condition_label`, `repeat_label` |
| `runner.step_dir_for` | `(run_dir, execution, collapse_repeats) -> Path` — already nests under `conditions/<nn>_<label>/` when `condition_label is not None` |
| `runner.execute_plan` | `(*, plan, run_dir, input_dir, cfg, repeats, digest, units=None, max_failed_fraction=None)` |
| `runner.attrition` | `(results, roster, step_name: str, condition_index: int) -> dict[str, int]` |
| `stats.collapse_repeats` | `(results, step_name: str, condition_index: int) -> dict[str, dict[str, float]]` |
| `stats.summarize_step` | `(collapsed, counts) -> dict[str, dict]` |
| `run_record.assemble_run_yaml` | `(*, run_id, status, config, code_hash, parameters_hash, provenance, results, repeats, draft=False, aggregated: dict[int, dict[str, dict]] \| None = None)` |
| `artifacts.StepIO` | `(*, step_dir, input_dir, run_dir, units=None)` |
| `config.Config` | `Config(data: dict)`; dot-access only; `.raw` returns the underlying mapping |
| `validate` | `validate_config(path, c) -> dict \| None`; internals `_check_shape`, `_check_metadata`, `_check_entrypoint`, `_check_parameters`, `_check_versions`, `_check_data`, `_check_units`, `_check_replication`, `_check_unimplemented` |

**The `conditions/` level falls out of labels.** `step_dir_for` nests only when `condition_label is not None`. No sweep declared → `build_plan(..., conditions=[(0, None)])` → no level, exactly as S2 behaves. A sweep declared → labelled conditions → the level appears even if there is only one. That is the spec's "declared, not count" rule, and it needs no new branch.

## File Structure

| File | Responsibility |
|---|---|
| `src/publishable/sweep.py` *(new)* | **Pure.** Config dict in, ordered `Condition` list out; the label grammar; the `sweep.yaml` payload |
| `src/publishable/validate.py` | Retire one refusal, add four; swept paths and values; real `max_executions`; `W-STATS-FAMILY` |
| `src/publishable/runner.py` | Per-condition `Config`; `E-STEP-SWEPT-PARAM` |
| `src/publishable/artifacts.py` | `io.conditions`, `io.read_condition`; `read_upstream` direction check |
| `src/publishable/cli.py` | Expand, write `sweep.yaml`, aggregate per condition |

---

### Task 1: `sweep.py` — expansion

**Files:**
- Create: `src/publishable/sweep.py`
- Test: `tests/test_sweep.py`

**Interfaces:**
- Consumes: nothing. Pure — a plain dict in, values out. Must not import `config`, `artifacts`, `runner`, `cli`, or read the filesystem.
- Produces: `Condition` frozen dataclass with `index: int`, `label: str | None`, `values: dict[str, Any]`, `is_baseline: bool`; `expand(config: dict) -> list[Condition]`.

**Semantics.** `sweep.baseline` is prepended as condition `00`. `sweep.grid` is a cartesian product over its axes. **The last declared axis varies fastest**, so numbering reads like nested loops in declaration order. With no `sweep` block at all, `expand` returns a single `Condition(index=0, label=None, values={}, is_baseline=False)` — the label being `None` is what keeps the artifact tree flat.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_sweep.py
from publishable.sweep import Condition, expand


def test_no_sweep_block_is_one_unlabelled_condition():
    """label None is what keeps the `conditions/` level out of the tree."""
    conds = expand({})
    assert conds == [Condition(index=0, label=None, values={}, is_baseline=False)]


def test_a_bare_baseline_is_one_condition_but_labelled():
    """Declared, not count: a sweep with one condition still gets the tree level."""
    conds = expand({"sweep": {"baseline": {"analysis.method": "pearson"}}})
    assert len(conds) == 1
    assert conds[0].label == "baseline"
    assert conds[0].is_baseline is True
    assert conds[0].values == {"analysis.method": "pearson"}


def test_baseline_plus_grid_prepends_the_baseline():
    conds = expand({
        "sweep": {
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman", "kendall"]},
        }
    })
    assert [c.index for c in conds] == [0, 1, 2]
    assert [c.label for c in conds] == ["baseline", "method=spearman", "method=kendall"]
    assert [c.is_baseline for c in conds] == [True, False, False]
    assert conds[1].values == {"analysis.method": "spearman"}


def test_grid_without_a_baseline_starts_at_zero():
    conds = expand({"sweep": {"grid": {"analysis.method": ["pearson", "spearman"]}}})
    assert [c.index for c in conds] == [0, 1]
    assert not any(c.is_baseline for c in conds)


def test_the_last_declared_axis_varies_fastest():
    """Numbering reads like nested loops written in declaration order."""
    conds = expand({
        "sweep": {"grid": {"a.x": [1, 2], "b.y": ["p", "q"]}}
    })
    assert [c.values for c in conds] == [
        {"a.x": 1, "b.y": "p"},
        {"a.x": 1, "b.y": "q"},
        {"a.x": 2, "b.y": "p"},
        {"a.x": 2, "b.y": "q"},
    ]


def test_an_empty_grid_axis_still_expands_to_nothing_here():
    """`expand` is pure and reports what the declaration says; `validate` is what
    refuses it (E-SWEEP-AXIS-EMPTY, Task 4). Pinned so the refusal has something
    to refuse and so nobody later reads the empty list as acceptable output."""
    assert expand({"sweep": {"grid": {"a.x": []}}}) == []


def test_conditions_are_frozen():
    import pytest
    c = expand({"sweep": {"grid": {"a.x": [1]}}})[0]
    with pytest.raises(Exception):
        c.index = 5  # type: ignore[misc]
```

- [ ] **Step 2: Run and watch it fail**

Run: `uv run pytest tests/test_sweep.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'publishable.sweep'`

- [ ] **Step 3: Implement expansion**

```python
# src/publishable/sweep.py
"""Sweep expansion. See docs/reference.md § Expansion modes.

Pure: a config dict in, an ordered condition list out. No filesystem, no
`Config` object, no git — expansion is a function of the declaration alone,
so it can be tested exhaustively without a repository.
"""

import itertools
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Condition:
    index: int
    label: str | None
    values: dict[str, Any] = field(default_factory=dict)
    is_baseline: bool = False


def expand(config: dict[str, Any]) -> list[Condition]:
    """Ordered conditions: a declared baseline as 00, then the grid product.

    With no `sweep` block, one condition whose label is None — which is what
    keeps the `conditions/` level out of the artifact tree.
    """
    sweep = config.get("sweep") or {}
    if not sweep:
        return [Condition(index=0, label=None, values={}, is_baseline=False)]

    rows: list[tuple[dict[str, Any], bool]] = []
    baseline = sweep.get("baseline")
    if baseline:
        rows.append((dict(baseline), True))

    grid = sweep.get("grid") or {}
    if grid:
        axes = list(grid.items())
        # itertools.product varies the LAST argument fastest, which is exactly
        # the declared-order nesting the specification asks for.
        for combo in itertools.product(*(values for _, values in axes)):
            rows.append(({path: value for (path, _), value in zip(axes, combo)}, False))

    return [
        Condition(index=i, label=label_for(values, grid, is_baseline),
                  values=values, is_baseline=is_baseline)
        for i, (values, is_baseline) in enumerate(rows)
    ]
```

`label_for` is written in Task 2. For this task, add a temporary definition immediately above `expand` so the module imports:

```python
def label_for(values: dict[str, Any], grid: dict[str, Any], is_baseline: bool) -> str:
    if is_baseline:
        return "baseline"
    return "__".join(f"{path.rsplit('.', 1)[-1]}={value}" for path, value in values.items())
```

Task 2 replaces its body with the real grammar; the signature does not change.

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest tests/test_sweep.py -v && uv run ruff check . && uv run mypy`
Expected: 7 passed, clean.

- [ ] **Step 5: Commit**

```bash
git add src/publishable/sweep.py tests/test_sweep.py
git commit -m "Expand a declared sweep into ordered conditions"
```

---

### Task 2: The label grammar

**Files:**
- Modify: `src/publishable/sweep.py`
- Test: `tests/test_sweep.py`

**Interfaces:**
- Consumes: `Condition`, `expand` from Task 1.
- Produces: `label_for(values: dict[str, Any], grid: dict[str, Any], is_baseline: bool) -> str` with the real grammar; `render_value(value: Any) -> str`; `SWEPT_VALUE_PATTERN = r"^[A-Za-z0-9._+-]+$"`.

**The grammar, from `docs/reference.md` § How artifacts are organized.** A label is also a *selector* — a hypothesis's `compare.condition` and a contrast's `of`/`against` name conditions by the label's body — so it must be something a person can write down without seeing the directory.

| Rule | Is |
|---|---|
| Separator | `__` between axes, `=` between key and value |
| Key | **The shortest suffix of the dotted path that is unique among the swept paths.** `analysis.method` alone becomes `method`; swept beside `scoring.method`, both keep a segment |
| Value | Rendered as written — `true`/`false` for booleans, shortest round-trip form for floats |
| Baseline | `baseline` |

- [ ] **Step 1: Write the failing test**

```python
def test_a_single_axis_uses_the_shortest_suffix():
    conds = expand({"sweep": {"grid": {"analysis.method": ["spearman"]}}})
    assert conds[0].label == "method=spearman"


def test_a_shared_leaf_forces_both_keys_to_keep_a_segment():
    """The rule is shortest UNIQUE suffix, not shortest suffix."""
    conds = expand({
        "sweep": {"grid": {"analysis.method": ["pearson"], "scoring.method": ["auc"]}}
    })
    assert conds[0].label == "analysis.method=pearson__scoring.method=auc"


def test_a_three_segment_path_disambiguates_only_as_far_as_needed():
    conds = expand({
        "sweep": {"grid": {"a.b.method": ["x"], "c.d.method": ["y"]}}
    })
    assert conds[0].label == "b.method=x__d.method=y"


def test_axes_appear_in_declaration_order_never_sorted():
    conds = expand({"sweep": {"grid": {"z.one": ["a"], "a.two": ["b"]}}})
    assert conds[0].label == "one=a__two=b"


def test_booleans_and_floats_render_readably():
    conds = expand({"sweep": {"grid": {"f.flag": [True, False], "g.rate": [0.5]}}})
    assert [c.label for c in conds] == ["flag=true__rate=0.5", "flag=false__rate=0.5"]


def test_every_generated_label_body_matches_the_selector_pattern():
    import re
    from publishable.sweep import SWEPT_VALUE_PATTERN
    conds = expand({
        "sweep": {"baseline": {"analysis.method": "pearson"},
                  "grid": {"analysis.method": ["spearman", "kendall"]}}
    })
    for c in conds:
        for part in c.label.split("__"):
            value = part.split("=")[-1]
            assert re.match(SWEPT_VALUE_PATTERN, value), part
```

- [ ] **Step 2: Run and watch them fail**

Run: `uv run pytest tests/test_sweep.py -k label -v`
Expected: FAIL — the temporary `label_for` uses the last segment unconditionally, so the shared-leaf cases collide.

- [ ] **Step 3: Implement the grammar**

```python
SWEPT_VALUE_PATTERN = r"^[A-Za-z0-9._+-]+$"


def render_value(value: Any) -> str:
    """As written in the config: `true`/`false` for booleans, shortest round-trip float."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return repr(value)
    return str(value)


def _keys_for(paths: list[str]) -> dict[str, str]:
    """The shortest suffix of each dotted path that is unique among them all.

    A label is also a selector, so the key has to be something a reader can
    type without opening the directory — but it must still identify one axis.
    """
    keys: dict[str, str] = {}
    for path in paths:
        segments = path.split(".")
        for depth in range(1, len(segments) + 1):
            candidate = ".".join(segments[-depth:])
            others = [p for p in paths if p != path]
            if not any(p == candidate or p.endswith("." + candidate) for p in others):
                keys[path] = candidate
                break
        else:
            keys[path] = path
    return keys


def label_for(values: dict[str, Any], grid: dict[str, Any], is_baseline: bool) -> str:
    if is_baseline:
        return "baseline"
    keys = _keys_for(list(grid))
    return "__".join(
        f"{keys.get(path, path.rsplit('.', 1)[-1])}={render_value(value)}"
        for path, value in values.items()
    )
```

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest tests/test_sweep.py -v && uv run ruff check . && uv run mypy`
Expected: 13 passed, clean.

- [ ] **Step 5: Commit**

```bash
git add src/publishable/sweep.py tests/test_sweep.py
git commit -m "Label a condition so a reader can type its name"
```

---

### Task 3: Retire one refusal, add four

**Files:**
- Modify: `src/publishable/validate.py` — the `E-SWEEP-UNSUPPORTED` block in `_check_unimplemented`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: `Collector`.
- Produces: `E-SWEEP-PAIRED-UNSUPPORTED`, `E-SWEEP-ABLATE-UNSUPPORTED`, `E-SWEEP-SAMPLE-UNSUPPORTED`, `E-SWEEP-GROUPS-UNSUPPORTED`. `E-SWEEP-UNSUPPORTED` exists nowhere afterwards.

**This task gets its own reviewer gate** because retiring a blanket refusal is exactly where the door reopens one level down. It happened in S1 with `sweep` and was prevented in S2 by splitting `data.units` into seven refusals.

- [ ] **Step 1: Write the failing tests**

`tests/test_validate.py` already has a `write_config` fixture and a `codes(path)` helper — reuse them.

```python
def test_baseline_and_grid_are_now_accepted():
    found = codes(write_config({"sweep": {"baseline": {"analysis.method": "pearson"},
                                          "grid": {"analysis.method": ["spearman"]}}}))
    assert not [c for c in found if c.startswith("E-SWEEP")]


@pytest.mark.parametrize(
    "mode,value,code",
    [
        ("paired", [{"analysis.method": "pearson"}], "E-SWEEP-PAIRED-UNSUPPORTED"),
        ("ablate", {"from": "baseline", "remove": ["a.b"]}, "E-SWEEP-ABLATE-UNSUPPORTED"),
        ("sample", {"n": 40, "ranges": {}}, "E-SWEEP-SAMPLE-UNSUPPORTED"),
        ("groups", [{"by": "arm", "levels": ["a", "b"]}], "E-SWEEP-GROUPS-UNSUPPORTED"),
    ],
)
def test_each_unimplemented_mode_is_refused_on_its_own(write_config, mode, value, code):
    assert code in codes(write_config({"sweep": {mode: value}}))


def test_an_empty_or_null_mode_is_not_a_declaration(write_config):
    """`init` may write these absent or null; only a truthy value is refused."""
    found = codes(write_config({"sweep": {"grid": {"analysis.method": ["spearman"]},
                                          "paired": [], "ablate": None,
                                          "sample": None, "groups": []}}))
    assert not [c for c in found if c.endswith("-UNSUPPORTED")]


def test_every_sweep_refusal_message_defers_rather_than_scolds(write_config):
    for mode, value, code in [
        ("paired", [{"a.b": 1}], "E-SWEEP-PAIRED-UNSUPPORTED"),
        ("ablate", {"from": "baseline"}, "E-SWEEP-ABLATE-UNSUPPORTED"),
        ("sample", {"n": 1}, "E-SWEEP-SAMPLE-UNSUPPORTED"),
        ("groups", [{"by": "arm"}], "E-SWEEP-GROUPS-UNSUPPORTED"),
    ]:
        c = Collector()
        validate_config(write_config({"sweep": {mode: value}}), c)
        message = next(f.message for f in c.findings if f.code == code)
        assert "later slice" in message, f"{code} must defer, not scold"
```

- [ ] **Step 2: Run and watch them fail**

Run: `uv run pytest tests/test_validate.py -k sweep -v`
Expected: FAIL — the blanket `E-SWEEP-UNSUPPORTED` still fires and none of the four exist.

- [ ] **Step 3: Replace the blanket block**

In `_check_unimplemented`, delete the `E-SWEEP-UNSUPPORTED` block entirely and put this in its place:

```python
    sweep = doc.get("sweep") or {}
    for mode, code, why in (
        ("paired", "E-SWEEP-PAIRED-UNSUPPORTED",
         "couples parameters into one axis"),
        ("ablate", "E-SWEEP-ABLATE-UNSUPPORTED",
         "emits 1 + n one-change conditions and reads the baseline rather than re-emitting it"),
        ("sample", "E-SWEEP-SAMPLE-UNSUPPORTED",
         "draws continuous ranges and labels its conditions `NN_sample`"),
        ("groups", "E-SWEEP-GROUPS-UNSUPPORTED",
         "is an axis over units rather than parameters, so it needs `data.units.allocation` "
         "and `data.units.assign`"),
    ):
        if sweep.get(mode):
            c.error(
                code,
                f"sweep.{mode}",
                f"{why}, and is specified but not implemented in this build — this build "
                "expands `baseline` and `grid` only; the other modes will be honored in a "
                "later slice",
            )
```

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest tests/test_validate.py -v && uv run ruff check . && uv run mypy`
Then confirm the retired identifier is gone: `grep -rn "E-SWEEP-UNSUPPORTED" src/ tests/` — expected: no matches.

- [ ] **Step 5: Record the identifiers**

```bash
cat >> docs/superpowers/spec-defects.md <<'EOF'

## New error identifiers: the four sweep modes

`E-SWEEP-PAIRED-UNSUPPORTED`, `E-SWEEP-ABLATE-UNSUPPORTED`, `E-SWEEP-SAMPLE-UNSUPPORTED`,
`E-SWEEP-GROUPS-UNSUPPORTED`. None is in § Errors core raises, which enumerates raise-time
codes. They replace the blanket `E-SWEEP-UNSUPPORTED` S1 introduced, following the pattern S2
used when it split `data.units`: retiring a blanket refusal must not leave the modes it covered
silently accepted. Retire these entries as each mode lands.
EOF
git add src/publishable/validate.py tests/test_validate.py docs/superpowers/
git commit -m "Refuse each unimplemented sweep mode on its own"
```

---

### Task 4: Real `max_executions`, swept-path checks, and the family warning

**Files:**
- Modify: `src/publishable/validate.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: `sweep.expand`, `sweep.render_value`, `sweep.SWEPT_VALUE_PATTERN`; `Collector`.
- Produces: `E-SWEEP-KEY-UNKNOWN`, `E-SWEEP-AXIS-EMPTY`, `E-SWEEP-PATH-UNKNOWN`, `E-SWEEP-VALUE-UNNAMEABLE`, `W-EXEC-BUDGET`, `W-STATS-FAMILY`.

**Four checks that only become reachable once sweeps expand.**

`W-STATS-FAMILY` warns on any multi-condition enumerated sweep, naming the family size and saying correction is not implemented in this build. `docs/reference.md` § Sweeps and repeats: reporting a family uncorrected "is how a sweep feature turns into a p-hacking feature."

- [ ] **Step 1: Write the failing tests**

```python
def test_an_unrecognised_sweep_key_is_refused(write_config):
    """A typo'd mode expands to zero conditions and would otherwise run nothing.
    Same argument as the unknown-parameter check: `init` writes every valid key,
    so an unrecognised one is a typo by construction."""
    found = codes(write_config({"sweep": {"gird": {"analysis.method": ["spearman"]}}}))
    assert "E-SWEEP-KEY-UNKNOWN" in found


def test_an_axis_declaring_no_values_is_refused(write_config):
    """Zero conditions is a run that executes nothing while reporting success —
    the same reasoning as E-UNITS-EMPTY: zero is not a small study."""
    assert "E-SWEEP-AXIS-EMPTY" in codes(
        write_config({"sweep": {"grid": {"analysis.method": []}}})
    )


def test_a_swept_path_must_be_a_real_parameter(write_config):
    assert "E-SWEEP-PATH-UNKNOWN" in codes(
        write_config({"sweep": {"grid": {"analysis.methd": ["spearman"]}}})
    )


def test_a_swept_value_must_be_checkable_against_the_spec(write_config):
    assert "E-PARAM-VALUE" in codes(
        write_config({"sweep": {"grid": {"analysis.method": ["spearmann"]}}})
    )


def test_a_swept_value_must_render_as_a_nameable_label(write_config):
    """A label is a selector; a value needing escaping is not a name anyone can type."""
    assert "E-SWEEP-VALUE-UNNAMEABLE" in codes(
        write_config({"sweep": {"grid": {"analysis.method": ["a long sentence"]}}})
    )


def test_the_execution_budget_is_checked_against_the_real_expansion(write_config):
    found = codes(write_config({
        "sweep": {"grid": {"analysis.method": ["pearson", "spearman", "kendall"]}},
        "replication": {"repeats": [{"kind": "seed", "n": 5}]},
        "limits": {"max_executions": 10},          # 3 × 5 = 15 > 10
    }))
    assert "W-EXEC-BUDGET" in found


def test_the_budget_does_not_warn_when_the_expansion_fits(write_config):
    found = codes(write_config({
        "sweep": {"grid": {"analysis.method": ["pearson", "spearman"]}},
        "replication": {"repeats": [{"kind": "seed", "n": 2}]},
        "limits": {"max_executions": 500},
    }))
    assert "W-EXEC-BUDGET" not in found


def test_a_multi_condition_sweep_warns_about_the_uncorrected_family(write_config):
    c = Collector()
    validate_config(write_config({
        "sweep": {"grid": {"analysis.method": ["pearson", "spearman", "kendall"]}}
    }), c)
    warning = next(f for f in c.findings if f.code == "W-STATS-FAMILY")
    assert "3" in warning.message
    assert "not implemented" in warning.message


def test_a_single_condition_run_has_no_family(write_config):
    assert "W-STATS-FAMILY" not in codes(write_config())


def test_warnings_alone_leave_the_exit_code_at_zero(write_config):
    c = Collector()
    validate_config(write_config({
        "sweep": {"grid": {"analysis.method": ["pearson", "spearman"]}}
    }), c)
    assert not c.has_errors
    assert c.exit_code() == 0
```

- [ ] **Step 2: Run and watch them fail**

Run: `uv run pytest tests/test_validate.py -k "swept or budget or family" -v`
Expected: FAIL — none of the four identifiers exists.

- [ ] **Step 3: Implement `_check_sweep`**

```python
def _check_sweep(doc: dict[str, Any], template: Any, c: Collector) -> None:
    """Checks that only become reachable once a sweep actually expands."""
    import re

    from publishable.sweep import SWEPT_VALUE_PATTERN, expand, render_value

    sweep = doc.get("sweep") or {}
    known = {"baseline", "grid", "paired", "ablate", "sample", "groups"}
    for key in sweep:
        if key not in known:
            import difflib

            near = difflib.get_close_matches(key, sorted(known), n=1)
            hint = f" — did you mean `{near[0]}`?" if near else ""
            c.error(
                "E-SWEEP-KEY-UNKNOWN", f"sweep.{key}",
                f"is not a sweep mode{hint}. `expand` understands only `baseline` and `grid` "
                "in this build, so an unrecognised key would expand to zero conditions and "
                "the run would execute nothing while reporting success",
            )

    grid = sweep.get("grid") or {}
    spec = template.parameter_spec
    for path, values in grid.items():
        if not values:
            c.error(
                "E-SWEEP-AXIS-EMPTY", f"sweep.grid.{path}",
                "declares no values, so the sweep expands to zero conditions and the run "
                "would execute nothing while reporting success",
            )
            continue
        if path not in spec:
            import difflib

            near = difflib.get_close_matches(path, list(spec), n=1)
            hint = f" — did you mean `{near[0]}`?" if near else ""
            c.error("E-SWEEP-PATH-UNKNOWN", f"sweep.grid.{path}",
                    f"is not a parameter of this template{hint}")
            continue
        for i, value in enumerate(values or []):
            problem = spec[path].check(value)
            if problem:
                c.error("E-PARAM-VALUE", f"sweep.grid.{path}[{i}]", problem)
            elif not re.match(SWEPT_VALUE_PATTERN, render_value(value)):
                c.error(
                    "E-SWEEP-VALUE-UNNAMEABLE", f"sweep.grid.{path}[{i}]",
                    f"renders as {render_value(value)!r}, which cannot be a condition label — "
                    "a label is also a selector, so a swept value must match "
                    f"{SWEPT_VALUE_PATTERN}",
                )

    conditions = expand(doc)
    levels = ((doc.get("replication") or {}).get("repeats")) or []
    repeats = 1
    for level in levels:
        count = level.get("n")
        if count is None:
            count = level.get("k")
        if isinstance(count, int) and count >= 1:
            repeats *= count
    executions = len(conditions) * repeats
    budget = (doc.get("limits") or {}).get("max_executions")
    if isinstance(budget, int) and executions > budget:
        c.warn("W-EXEC-BUDGET", "limits.max_executions",
               f"{len(conditions)} conditions × {repeats} repeats = {executions} executions "
               f"exceeds {budget}")

    if len(conditions) > 1:
        c.warn(
            "W-STATS-FAMILY", "statistics.correction",
            f"{len(conditions)} conditions form a family of {len(conditions) - 1} baseline "
            "comparisons per metric, and multiplicity correction is not implemented in this "
            "build — every interval reported is uncorrected, and each records "
            "`correction: null` to say so",
        )
```

Call it from `validate_config` after `_check_unimplemented`, guarded so it only runs when the template resolved.

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest tests/test_validate.py -v && uv run ruff check . && uv run mypy`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/publishable/validate.py tests/test_validate.py
git commit -m "Check the expansion, and warn about the family it creates"
```

---

### Task 5: Per-condition `cfg`, and the swept-parameter refusal

**Files:**
- Modify: `src/publishable/runner.py`
- Test: `tests/test_runner.py`

**Interfaces:**
- Consumes: `Condition` from `sweep.py`; `Config`; `ContractError`.
- Produces: `execute_plan` replaces `cfg: Any` with `cfgs: dict[int, Any]` keyed by condition index; `resolve_condition_cfg(base: dict, values: dict[str, Any]) -> Config`; `resolve_wide_cfg(base: dict, swept_paths: set[str]) -> Config`.
- **Also modifies `src/publishable/config.py`**: `SweptAway` is defined THERE, and `Node.__getattr__` raises `E-STEP-SWEPT-PARAM` when it resolves one. `runner.py` imports it — no cycle, since `runner` already imports `config`.

**Why the marker cannot live in `runner.py`.** A sentinel object stored at the leaf does not raise when the leaf is read — `cfg.parameters.analysis.method` simply returns the sentinel, and the raise fires only on a further attribute access. Verified. A step doing `return {"m": cfg.parameters.analysis.method}` would then fail with `E-STEP-RETURN-TYPE` from the S2 shape gate, naming the return shape rather than the sweep, and a step that merely stored the value would get no error at all. The refusal has to fire on the read, so `Node` has to know.

**This is the slice's central mechanic.** A step reads `cfg.parameters.analysis.method` and gets *this* condition's value — which is what makes the specification's promise true that steps never mention sweeps.

**Its mirror image is a refusal.** A swept parameter is unreadable at `"run"` and `"summary"` scope, where it has no single value: a `"run"`-scoped step reading it would produce output silently wrong for every condition but one. `E-STEP-SWEPT-PARAM` is already in the specification's registry.

- [ ] **Step 1: Write the failing test**

```python
def test_each_condition_sees_its_own_parameter_value(tmp_path: Path):
    seen = []

    class Reads(BaseStep):
        def run(self, cfg, io):
            seen.append(cfg.parameters.analysis.method)
            return {}

    run_two_conditions(tmp_path, Reads)
    assert sorted(seen) == ["pearson", "spearman"]


def test_a_run_scoped_step_cannot_read_a_swept_parameter(tmp_path: Path):
    class Wide(BaseStep):
        scope = "run"

        def run(self, cfg, io):
            return {"m": cfg.parameters.analysis.method}

    results = run_two_conditions(tmp_path, Wide)
    failed = [r for r in results if r.status == "failed"]
    assert failed and "E-STEP-SWEPT-PARAM" in (failed[0].error or "")


def test_a_summary_scoped_step_cannot_read_a_swept_parameter(tmp_path: Path):
    class Sum(BaseStep):
        scope = "summary"

        def run(self, cfg, io):
            return {"m": cfg.parameters.analysis.method}

    results = run_two_conditions(tmp_path, Sum)
    failed = [r for r in results if r.status == "failed"]
    assert failed and "E-STEP-SWEPT-PARAM" in (failed[0].error or "")


def test_an_unswept_path_reads_normally_at_every_scope(tmp_path: Path):
    """Only the swept paths are withheld; the rest is ordinary."""
    class Wide(BaseStep):
        scope = "run"

        def run(self, cfg, io):
            return {"n": cfg.parameters.analysis.min_samples}

    results = run_two_conditions(tmp_path, Wide)
    assert all(r.status == "completed" for r in results)
```

Write `run_two_conditions(tmp_path, step_cls)` as a module-level helper: it builds a two-condition plan (`pearson`, `spearman` over `analysis.method`), constructs `cfgs` for both, and calls `execute_plan`. Base parameters are `{"analysis": {"method": "pearson", "min_samples": 30}}`.

- [ ] **Step 2: Run and watch them fail**

Run: `uv run pytest tests/test_runner.py -k "condition_sees or swept" -v`
Expected: FAIL — `execute_plan() got an unexpected keyword argument 'cfgs'`

- [ ] **Step 3: Implement**

```python
In `src/publishable/config.py`, add the marker and make `Node` raise on it:

```python
class SweptAway:
    """Marks a parameter that `sweep` varies, at a scope with no single value for it.

    `Node.__getattr__` raises when it resolves one, so the refusal fires on the read
    itself. A bare sentinel returned to the caller would not — the raise would land
    on some later attribute access, under the wrong identifier.
    """

    __slots__ = ("path",)

    def __init__(self, path: str) -> None:
        self.path = path
```

and in `Node.__getattr__`, immediately before `return _wrap(data[name], full)`:

```python
        value = data[name]
        if isinstance(value, SweptAway):
            raise ContractError(
                f"`{value.path}` is varied by `sweep`, so it has no single value at this "
                "scope; read it from a `condition`- or `repeat`-scoped step",
                code="E-STEP-SWEPT-PARAM",
            )
```


def resolve_condition_cfg(base: dict[str, Any], values: dict[str, Any]) -> Config:
    """Overlay this condition's swept values onto the base config."""
    import copy

    doc = copy.deepcopy(base)
    for path, value in values.items():
        node = doc.setdefault("parameters", {})
        *heads, leaf = path.split(".")
        for head in heads:
            node = node.setdefault(head, {})
        node[leaf] = value
    return Config(doc)
```

For the wide scopes, build a config whose swept leaves are replaced by a sentinel that raises on access:

```python
def resolve_wide_cfg(base: dict[str, Any], swept_paths: set[str]) -> Config:
    """A config for `run`/`summary` scope, with every swept path made unreadable."""
    import copy

    doc = copy.deepcopy(base)
    for path in swept_paths:
        node = doc.get("parameters", {})
        *heads, leaf = path.split(".")
        for head in heads:
            node = node.get(head)
            if node is None:
                break
        else:
            node[leaf] = SweptAway(f"parameters.{path}")
    return Config(doc)
```

In `execute_plan`, replace the `cfg` parameter with `cfgs: dict[int, Any]` and select per execution: the condition's cfg when `execution.condition_index is not None`, otherwise the wide cfg stored under key `-1`.

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest tests/test_runner.py -v && uv run ruff check . && uv run mypy`
Expected: all pass, including every pre-existing runner test (update their `cfg=` call sites to `cfgs={...}`).

- [ ] **Step 5: Commit**

```bash
git add src/publishable/runner.py tests/test_runner.py
git commit -m "Give each condition its own cfg, and withhold what a scope cannot know"
```

---

### Task 6: `sweep.yaml`

**Files:**
- Modify: `src/publishable/sweep.py`
- Test: `tests/test_sweep.py`

**Interfaces:**
- Consumes: `Condition`; `Repeat` from `replication.py` (fields `kind`, `label`, `seed`).
- Produces: `sweep_document(conditions: list[Condition], repeats: list[Repeat], digest: str, order: list[tuple[int, str]]) -> dict[str, Any]`.

`docs/reference.md` § The other files a run writes: `sweep.yaml` holds "resolved conditions, repeat plan, seeds, fold membership, realized execution order, design digest". Fold membership is S3b and is absent here.

- [ ] **Step 1: Write the failing test**

```python
def test_the_sweep_document_records_the_resolved_plan():
    from publishable.replication import Repeat
    from publishable.sweep import expand, sweep_document

    conds = expand({"sweep": {"baseline": {"analysis.method": "pearson"},
                              "grid": {"analysis.method": ["spearman"]}}})
    repeats = [Repeat("seed", "seed17", 17), Repeat("seed", "seed42", 42)]
    order = [(0, "seed17"), (0, "seed42"), (1, "seed17"), (1, "seed42")]
    doc = sweep_document(conds, repeats, "sha256:abc", order)

    assert doc["design_digest"] == "sha256:abc"
    assert doc["conditions"] == [
        {"index": 0, "label": "baseline", "values": {"analysis.method": "pearson"},
         "is_baseline": True},
        {"index": 1, "label": "method=spearman", "values": {"analysis.method": "spearman"},
         "is_baseline": False},
    ]
    assert doc["repeats"] == [{"kind": "seed", "label": "seed17", "seed": 17},
                              {"kind": "seed", "label": "seed42", "seed": 42}]
    assert doc["order"] == [[0, "seed17"], [0, "seed42"], [1, "seed17"], [1, "seed42"]]


def test_the_document_is_plain_yaml_safe_data():
    """It is written with the artifact writer, so it must hold no custom types."""
    import yaml
    from publishable.replication import Repeat
    from publishable.sweep import expand, sweep_document

    doc = sweep_document(expand({"sweep": {"grid": {"a.x": [1]}}}),
                         [Repeat("seed", "seed01", 1)], "sha256:d", [(0, "seed01")])
    assert yaml.safe_load(yaml.safe_dump(doc)) == doc
```

- [ ] **Step 2: Run and watch it fail**

Run: `uv run pytest tests/test_sweep.py -k sweep_document -v`
Expected: FAIL — `ImportError: cannot import name 'sweep_document'`

- [ ] **Step 3: Implement**

```python
def sweep_document(
    conditions: list[Condition],
    repeats: list["Repeat"],
    digest: str,
    order: list[tuple[int, str]],
) -> dict[str, Any]:
    """The `sweep.yaml` payload: the resolved plan, as plain YAML-safe data.

    Fold membership belongs here too per § The other files a run writes; folds
    are a later slice and the key is absent rather than empty, so its absence
    is not read as "no folds were drawn".
    """
    return {
        "design_digest": digest,
        "conditions": [
            {"index": c.index, "label": c.label, "values": dict(c.values),
             "is_baseline": c.is_baseline}
            for c in conditions
        ],
        "repeats": [{"kind": r.kind, "label": r.label, "seed": r.seed} for r in repeats],
        "order": [[index, label] for index, label in order],
    }
```

Import `Repeat` under `TYPE_CHECKING` so `sweep.py` stays free of a runtime dependency on `replication`.

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest tests/test_sweep.py -v && uv run ruff check . && uv run mypy`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/publishable/sweep.py tests/test_sweep.py
git commit -m "Write down the plan a run actually resolved"
```

---

### Task 7: Summary-scope reads and the direction check

**Files:**
- Modify: `src/publishable/artifacts.py`
- Test: `tests/test_artifacts.py`

**Interfaces:**
- Consumes: `Execution`; `ContractError`.
- Produces: `StepIO.__init__` gains `scope: str = "repeat"`, `conditions: list[tuple[int, str]] | None = None`, `repeats: list[str] | None = None`, `step_scopes: dict[str, str] | None = None`; `io.conditions`, `io.repeats`, `io.read_condition(condition, step, name, repeat=None)`; `read_upstream` gains the direction check.

**Two rules from `docs/reference.md` § Step scope:**
- `io.conditions` / `io.read_condition` are **`summary` scope only** — a narrower step has no business reading across conditions.
- **A wider step can never read a narrower one**, because at the time it runs those executions have not happened. `io.read_upstream` raises `E-STEP-READ-DIRECTION` naming both scopes.

- [ ] **Step 1: Write the failing tests**

```python
SCOPE_ORDER = {"run": 0, "condition": 1, "repeat": 2, "summary": 3}


def test_conditions_and_read_condition_are_summary_only(tmp_path: Path):
    io = make_io(tmp_path, scope="repeat", conditions=[(0, "baseline")])
    for call in (lambda: io.conditions, lambda: io.read_condition(0, "s", "a.json")):
        with pytest.raises(ContractError) as e:
            call()
        assert e.value.code == "E-STEP-SCOPE-ONLY"


def test_a_summary_step_can_list_conditions_and_repeats(tmp_path: Path):
    io = make_io(tmp_path, scope="summary", conditions=[(0, "baseline"), (1, "method=spearman")],
                 repeats=["seed17"])
    assert io.conditions == [(0, "baseline"), (1, "method=spearman")]
    assert io.repeats == ["seed17"]


def test_a_wider_step_cannot_read_a_narrower_one(tmp_path: Path):
    io = make_io(tmp_path, scope="condition", step_scopes={"analyze": "repeat"})
    with pytest.raises(ContractError) as e:
        io.read_upstream("analyze", "units.parquet")
    assert e.value.code == "E-STEP-READ-DIRECTION"
    assert "condition" in str(e.value) and "repeat" in str(e.value)


def test_a_narrower_step_reads_a_wider_one_normally(tmp_path: Path):
    io = make_io(tmp_path, scope="repeat", step_scopes={"load": "run"})
    (io.run_dir / "shared" / "load").mkdir(parents=True)
    (io.run_dir / "shared" / "load" / "a.json").write_text('{"x": 1}\n')
    assert io.read_upstream("load", "a.json") == {"x": 1}


def test_read_condition_requires_a_repeat_for_a_repeat_scoped_step(tmp_path: Path):
    io = make_io(tmp_path, scope="summary", conditions=[(0, "baseline")],
                 step_scopes={"analyze": "repeat"})
    with pytest.raises(ContractError) as e:
        io.read_condition(0, "analyze", "units.parquet")
    assert e.value.code == "E-STEP-READ-REPEAT-REQUIRED"
```

Write `make_io(tmp_path, **kwargs)` as a module-level helper constructing a `StepIO` with a created `step_dir`, `input_dir`, and `run_dir`.

- [ ] **Step 2: Run and watch them fail**

Run: `uv run pytest tests/test_artifacts.py -k "summary or direction or read_condition" -v`
Expected: FAIL — `StepIO.__init__() got an unexpected keyword argument 'scope'`

- [ ] **Step 3: Implement**

Add the four constructor arguments, a module-level `SCOPE_ORDER = {"run": 0, "condition": 1, "repeat": 2, "summary": 3}`, and:

```python
    def _summary_only(self, what: str) -> None:
        if self._scope != "summary":
            raise ContractError(
                f"`io.{what}` is available at `summary` scope only; this step is "
                f"`{self._scope}`-scoped, and a narrower step has no business reading "
                "across conditions",
                code="E-STEP-SCOPE-ONLY",
            )

    @property
    def conditions(self) -> list[tuple[int, str]]:
        self._summary_only("conditions")
        return list(self._conditions or [])

    @property
    def repeats(self) -> list[str]:
        self._summary_only("repeats")
        return list(self._repeats or [])

    def read_condition(
        self, condition: int, step: str, name: str, repeat: str | None = None
    ) -> Any:
        self._summary_only("read_condition")
        target = (self._step_scopes or {}).get(step)
        if target == "repeat" and repeat is None:
            raise ContractError(
                f"`{step}` is repeat-scoped, so `read_condition` needs a `repeat=` naming "
                "which repeat's copy to read",
                code="E-STEP-READ-REPEAT-REQUIRED",
            )
        label = dict(self._conditions or {}).get(condition)
        base = self.run_dir / "conditions" / f"{condition:02d}_{label}"
        if repeat is not None:
            base = base / repeat
        return self._read(base / step / name)
```

And in `read_upstream`, before reading:

```python
        target = (self._step_scopes or {}).get(step)
        if target is not None and SCOPE_ORDER[target] > SCOPE_ORDER[self._scope]:
            raise ContractError(
                f"`{step}` is `{target}`-scoped and this step is `{self._scope}`-scoped; "
                "a wider step cannot read a narrower one, because at the time it runs those "
                "executions have not happened",
                code="E-STEP-READ-DIRECTION",
            )
```

- [ ] **Step 4: Run and verify green**

Run: `uv run pytest tests/test_artifacts.py -v && uv run ruff check . && uv run mypy`
Expected: all pass, including every pre-existing artifact test.

- [ ] **Step 5: Commit**

```bash
git add src/publishable/artifacts.py tests/test_artifacts.py
git commit -m "Let a summary step read across conditions, and only a summary step"
```

---

### Task 8: Wire the CLI, and the acceptance test

**Files:**
- Modify: `src/publishable/cli.py`
- Test: `tests/test_acceptance.py`

**Interfaces:**
- Consumes: everything above.
- Produces: `command_run` expands the sweep, builds one `cfgs` mapping, writes `sweep.yaml`, and aggregates per condition.

**The wiring, precisely.** `cli.py` currently hardcodes `conditions=[(0, None)]` and `condition_index == 0` in two places. Both become the real expansion.

- [ ] **Step 1: Write the failing acceptance test**

```python
def test_a_sweep_runs_every_condition_over_one_roster(tmp_path: Path):
    """3 conditions × 5 seed repeats = 15 executions, in the right tree."""
    root, cfg, results_dir = build_sweep_project(tmp_path, n_units=240)
    assert main(["run", str(cfg)]) == EXIT_OK

    run_dir = next(results_dir.glob("run_*"))
    doc = yaml.safe_load((run_dir / "run.yaml").read_text())

    conds = doc["results"]["conditions"]
    assert [c["label"] for c in conds] == ["baseline", "method=spearman", "method=kendall"]
    assert conds[0]["is_baseline"] is True

    # the tree: a conditions/ level, five repeat dirs under each
    labels = sorted(p.name for p in (run_dir / "conditions").iterdir())
    assert labels == ["00_baseline", "01_method=spearman", "02_method=kendall"]
    for label in labels:
        seeds = [p for p in (run_dir / "conditions" / label).iterdir() if p.is_dir()]
        assert len(seeds) == 5, label

    lines = (run_dir / "executions.jsonl").read_text().splitlines()
    assert len(lines) == 15


def test_each_condition_reports_its_own_numbers(tmp_path: Path):
    """The headline test: two conditions must not share an aggregated block."""
    root, cfg, results_dir = build_sweep_project(tmp_path, n_units=240)
    assert main(["run", str(cfg)]) == EXIT_OK
    doc = yaml.safe_load((next(results_dir.glob("run_*")) / "run.yaml").read_text())

    blocks = [c["aggregated"]["step01_summarize_units"]["score"]
              for c in doc["results"]["conditions"]]
    values = [b["value"] for b in blocks]
    assert len(set(values)) == 3, f"conditions must differ, got {values}"
    assert blocks[0] is not blocks[1], "aggregated must not be a shared object"
    for b in blocks:
        assert b["basis"] == "units"
        assert b["correction"] is None, "an uncorrected interval must say so"
        assert b["n"]["resolved"] == 240


def test_sweep_yaml_records_the_resolved_plan(tmp_path: Path):
    root, cfg, results_dir = build_sweep_project(tmp_path, n_units=40)
    assert main(["run", str(cfg)]) == EXIT_OK
    sweep_doc = yaml.safe_load((next(results_dir.glob("run_*")) / "sweep.yaml").read_text())
    assert [c["label"] for c in sweep_doc["conditions"]] == [
        "baseline", "method=spearman", "method=kendall"]
    assert len(sweep_doc["repeats"]) == 5
    assert len(sweep_doc["order"]) == 15


def test_a_single_condition_run_is_unchanged(tmp_path: Path):
    """The regression risk of adding a level is that it appears where it should not."""
    root, cfg, results_dir = build_project_without_sweep(tmp_path, n_units=40)
    assert main(["run", str(cfg)]) == EXIT_OK
    run_dir = next(results_dir.glob("run_*"))
    assert not (run_dir / "conditions").exists()
```

Write `build_sweep_project(tmp_path, n_units)` and `build_project_without_sweep(tmp_path, n_units)` as module-level helpers. Both scaffold a project, write an `index.csv` of `n_units` rows, generate the experiment, fill `metadata`, and commit. The sweep variant adds `sweep: {baseline: {analysis.method: pearson}, grid: {analysis.method: [spearman, kendall]}}` and overwrites the starter step with one recording a numeric `score` whose value depends on `cfg.parameters.analysis.method`, so the three conditions genuinely differ.

- [ ] **Step 2: Run and watch them fail**

Run: `uv run pytest tests/test_acceptance.py -k sweep -v`
Expected: FAIL — one condition executes and there is no `conditions/` level.

- [ ] **Step 3: Wire `command_run`**

Replace the hardcoded expansion:

```python
    from publishable.sweep import expand, sweep_document

    conditions = expand(doc)
    swept_paths = set((doc.get("sweep") or {}).get("grid") or {})
    plan = build_plan(
        experiment,
        conditions=[(c.index, c.label) for c in conditions],
        repeat_labels=labels,
    )
    cfgs: dict[int, Config] = {
        c.index: resolve_condition_cfg(doc, c.values) for c in conditions
    }
    cfgs[-1] = resolve_wide_cfg(doc, swept_paths)
```

Write `sweep.yaml` inside the lock, next to `manifest/input.json`:

```python
        order = [(e.condition_index or 0, e.repeat_label or "")
                 for e in plan if e.scope == "repeat"]
        (run_dir / "sweep.yaml").write_text(
            yaml.safe_dump(sweep_document(conditions, repeats, digest, order), sort_keys=False)
        )
```

And aggregate per condition rather than only condition 0:

```python
        # Condition metadata the ExecutionResults cannot carry: `Execution` holds
        # index and label but not `is_baseline`, and the acceptance test asserts it.
        condition_meta = {c.index: {"label": c.label, "is_baseline": c.is_baseline}
                          for c in conditions}
        aggregated = {}
        if roster is not None:
            for cond in conditions:
                recording = {
                    r.execution.step_name for r in results
                    if r.execution.scope == "repeat"
                    and r.execution.condition_index == cond.index and r.rows
                }
                aggregated[cond.index] = {
                    name: summarize_step(
                        collapse_repeats(results, name, cond.index),
                        attrition(results, roster, name, cond.index),
                    )
                    for name in sorted(recording)
                }
```

`summarize_step` gains `"correction": None` on each metric — the config's default is `holm`, so a record that said nothing could be read as corrected.

`assemble_run_yaml` gains keyword-only `condition_meta: dict[int, dict[str, Any]] | None = None`, and `_results_block` writes each condition's `label` and `is_baseline` from it. `ExecutionResult` carries `condition_index` and `condition_label` but has no way to know which condition is the baseline, so the fact has to arrive alongside `aggregated` rather than be inferred. Pass `condition_meta=condition_meta`.

- [ ] **Step 4: Run the whole suite and the real journey**

Run: `uv run pytest -v && uv run ruff check . && uv run mypy`
Then run the CLI by hand: scaffold, generate, write an `index.csv`, add the sweep block, fill metadata, commit, `validate`, `run`. Read the produced `run.yaml` and `sweep.yaml` and paste both into your report. Confirm the three conditions report three different values.

- [ ] **Step 5: Retire and narrow the ledger entries**

```bash
cat >> docs/superpowers/spec-defects.md <<'EOF'

## RETIRED in S3a: `E-SWEEP-UNSUPPORTED`

`baseline` and `grid` now expand and execute. The four modes S3a does not implement are
refused individually, and the `sweep` block is back in the config `init` generates, narrowing
the "complete parameter set" entry to the `statistics` sub-keys alone.
EOF
git add src/publishable/cli.py tests/test_acceptance.py docs/superpowers/
git commit -m "Run every condition a sweep declares"
```

---

## Definition of done for S3a

- [ ] `uv run pytest` green, including all four acceptance tests.
- [ ] `uv run ruff check .` and `uv run mypy` clean.
- [ ] Every `E-`/`W-` identifier defined in `src/` has a test that produces it.
- [ ] `E-SWEEP-UNSUPPORTED` appears nowhere in `src/` or `tests/`.
- [ ] The four mode refusals each fire, and a generated config trips none of them.
- [ ] Three conditions produce three genuinely different values over one shared roster, and their `aggregated` blocks are not the same object.
- [ ] A run with no `sweep` block has no `conditions/` level — unchanged from S2.
- [ ] Each aggregated metric records `correction: null`.
