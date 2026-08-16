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

