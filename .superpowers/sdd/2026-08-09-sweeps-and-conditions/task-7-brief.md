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

