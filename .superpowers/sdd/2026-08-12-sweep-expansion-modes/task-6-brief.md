## Task 6: The baseline expands over unfixed axes

**Files:**
- Modify: `src/publishable/sweep.py`
- Test: `tests/test_sweep.py`

**Interfaces:**
- Consumes: tasks 1–4
- Produces: one baseline condition per cell of the unfixed axes

**This is the slice's central change**, and the one this build refuses with `E-SWEEP-BASELINE-PARTIAL`. § Expansion modes' two-row table:

| `sweep.baseline` | Baseline conditions | Each `vs_baseline` targets |
|---|---|---|
| A value on every axis | One, condition `00` | That single condition |
| A value on some axes | **One per cell of the unfixed axes** | Its own cell's baseline |

*"The rule underneath both is that the baseline expands over whichever axes it doesn't fix — group axes and parameter axes alike."*

- [ ] **Step 1: Write the failing test**

```python
def test_a_baseline_fixing_some_axes_expands_over_the_rest() -> None:
    """§ Expansion modes' second row: a baseline that fixes `analysis.method`
    and leaves `sex` free gives one baseline per level of `sex`, and each
    comparison targets its own cell's baseline rather than a single global one."""
    conditions = expand(
        {
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "grid": {
                    "analysis.method": ["pearson", "spearman"],
                    "data.sex": ["f", "m"],
                },
            }
        }
    )

    baselines = [c for c in conditions if c.is_baseline]
    assert len(baselines) == 2
    assert {dict(c.values)["data.sex"] for c in baselines} == {"f", "m"}
    assert all(dict(c.values)["analysis.method"] == "pearson" for c in baselines)
```

- [ ] **Step 2: Run, implement, run.** The baseline's row set becomes the product of its fixed values with the cells of the axes it does not fix.

- [ ] **Step 3: Labels gain their cell.** § Expansion modes shows `00_cohort=derivation__baseline`. One baseline stays `baseline`; per-cell baselines are `<cell>__baseline`. **`condition_dir_name` does not change** — it is the single source of truth `runner.step_dir_for` and `artifacts.StepIO.read_condition` both nest through.

- [ ] **Step 4: Verify the artifact path oracle.** Existing tests over `condition_dir_name` and condition directories must pass **untouched**:

```bash
uv run pytest tests/test_artifacts.py tests/test_runner.py -q
git diff --stat tests/test_artifacts.py tests/test_runner.py
```
Expected: green, and no diff.

- [ ] **Step 5: Mutation-test.** Make the baseline expand over axes it **does** fix (the test must fail); make it never expand (the same); make a per-cell baseline's label omit its cell (a label test must fail — write one if none exists).

- [ ] **Step 6: Commit.**

---

