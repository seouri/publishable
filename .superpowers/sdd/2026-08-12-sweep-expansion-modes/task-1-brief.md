## Task 1: `expand()` as a product over axes

**Files:**
- Modify: `src/publishable/sweep.py`
- Test: `tests/test_sweep.py`

**Interfaces:**
- Consumes: nothing
- Produces: `_axes(sweep: dict) -> list[list[dict[str, Any]]]` returning one entry per axis-shaped mode, each a list of `{path: value}` cells. `expand()` keeps its signature `(config: dict) -> list[Condition]`. Later tasks add axes to `_axes`, not to `expand`.

**This is a pure refactor. No new mode, no behaviour change.** The existing `tests/test_sweep.py` is the oracle: it must pass **untouched**. If you find yourself editing an existing test to make it pass, stop — that is the signal you changed behaviour you were meant to preserve, and it belongs in your report instead.

- [ ] **Step 1: Read the current `expand()` and write down what it does**

```bash
sed -n '137,168p' src/publishable/sweep.py
```

It prepends a baseline row when `sweep.baseline` is truthy, then runs `itertools.product` over `grid`'s values, then builds `Condition`s with `enumerate`. Note the comment on `itertools.product`: it varies the **last** argument fastest, which is the declared-order nesting the specification asks for. That property must survive.

- [ ] **Step 2: Write the characterisation test**

Add to `tests/test_sweep.py` — this pins the property the refactor must not break, and it should pass before and after:

```python
def test_grid_axes_vary_the_last_declared_axis_fastest() -> None:
    """`itertools.product` varies its last argument fastest, which is the
    declared-order nesting § Expansion modes asks for. The refactor moves this
    loop, so pin the order it produces before moving it."""
    conditions = expand(
        {"sweep": {"grid": {"a.x": [1, 2], "b.y": ["p", "q"]}}}
    )

    assert [dict(c.values) for c in conditions] == [
        {"a.x": 1, "b.y": "p"},
        {"a.x": 1, "b.y": "q"},
        {"a.x": 2, "b.y": "p"},
        {"a.x": 2, "b.y": "q"},
    ]
```

- [ ] **Step 3: Run it and the whole sweep suite**

Run: `uv run pytest tests/test_sweep.py -v`
Expected: **PASS**, including the new test. This is the baseline you must not move.

- [ ] **Step 4: Restructure**

Replace `expand`'s body with two phases. `_axes` builds the axis list; `expand` takes the product and applies the baseline:

```python
def _axes(sweep: dict[str, Any]) -> list[list[dict[str, Any]]]:
    """One entry per axis-shaped mode present, each a list of `{path: value}` cells.

    The product of these is the condition set. `grid` contributes one axis per
    key; later modes contribute one axis each, whose cells may set several paths
    at once. Keeping every mode in this one list is what makes the composition
    rule — "the product of every axis-shaped mode present" — a property of the
    structure rather than a sentence someone has to remember.
    """
    axes: list[list[dict[str, Any]]] = []
    for path, values in (sweep.get("grid") or {}).items():
        axes.append([{path: value} for value in values])
    return axes


def expand(config: dict[str, Any]) -> list[Condition]:
    """Ordered conditions: a declared baseline as 00, then the product of every axis.

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

    axes = _axes(sweep)
    if axes:
        # `itertools.product` varies its LAST argument fastest, which is the
        # declared-order nesting the specification asks for. Preserved from the
        # grid-only implementation this replaces.
        for combo in itertools.product(*axes):
            values: dict[str, Any] = {}
            for cell in combo:
                values.update(cell)
            rows.append((values, False))

    swept = _swept_paths(sweep)
    return [
        Condition(index=i, label=label_for(values, swept, is_baseline),
                  values=values, is_baseline=is_baseline)
        for i, (values, is_baseline) in enumerate(rows)
    ]
```

- [ ] **Step 5: Change `label_for` and add `_swept_paths`**

`label_for` has exactly one caller — `expand` itself — so this signature change is contained. Verify that before editing:

```bash
grep -rn "label_for(" src/ tests/ | grep -v "def label_for" | grep -v __pycache__
```

```python
def _swept_paths(sweep: dict[str, Any]) -> list[str]:
    """Every path any axis-shaped mode sweeps, in declared order.

    `label_for` shortens these to unique suffixes, so it needs the whole set:
    a key is only unambiguous against every other swept path, not against one
    mode's. Later modes extend this and nothing else about labelling changes.
    """
    return list((sweep.get("grid") or {}))


def label_for(values: dict[str, Any], swept: list[str], is_baseline: bool) -> str:
    if is_baseline:
        return "baseline"
    keys = _keys_for(swept)
    return AXIS_SEPARATOR.join(
        f"{keys.get(path, path.rsplit('.', 1)[-1])}={render_value(value)}"
        for path, value in values.items()
    )
```

- [ ] **Step 6: Run the whole suite**

Run: `uv run pytest && uv run ruff check . && uv run mypy`
Expected: all green, **955 + 1** passing, and **no existing test edited**.

```bash
git diff --stat tests/
```
Expected: only additions to `tests/test_sweep.py`.

- [ ] **Step 7: Mutation-test**

Apply each, run the named test, confirm it FAILS, revert, confirm `git status --porcelain` is empty. **Run them; do not reason about them.**

| Mutation | Test that must fail |
|---|---|
| `for combo in itertools.product(*reversed(axes))` | `test_grid_axes_vary_the_last_declared_axis_fastest` |
| `_axes` returns one axis of all values flattened, rather than one per key | the same test, plus existing grid tests |
| `_swept_paths` returns `[]` | an existing label test — name it in your report |

- [ ] **Step 8: Commit**

```bash
git add src/publishable/sweep.py tests/test_sweep.py
git commit -m "refactor: expand conditions as a product over axes"
```

---

