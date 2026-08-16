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

