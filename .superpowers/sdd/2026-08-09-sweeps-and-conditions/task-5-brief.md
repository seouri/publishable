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

