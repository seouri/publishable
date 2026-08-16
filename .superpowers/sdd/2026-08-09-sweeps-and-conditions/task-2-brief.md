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

