## Task 5: The step path collapses, and `measurements.parquet`

**Files:**
- Modify: `src/publishable/artifacts.py`
- Test: `tests/test_artifacts.py`

### The central obligation: a measured unit must count as *completed*

Measured with a control, at task 4's HEAD:

```
io.record("p1", {"score": 10}, measurement="r1")   # measured only
io.record("p2", {"score": 20})                     # plain, the control
io.recorded_keys  ->  ['p2']        # p1 is absent
```

`recorded_keys` is populated only by the plain branch, and `finalize` writes `units.parquet` only `if self._rows:` — while measurement rows live in a separate store. So today a unit that is **only** measured is counted neither `completed` nor `ineligible`, which by `runner`'s subtraction makes it **`failed`**. `reference.md` § The unit table is the inference base states the accounting directly: *"`completed` is how many distinct unit keys reached `io.record` in it — measurements of one unit collapse before they are counted"*.

So the collapse is not merely about producing a nice table: **it is what makes a measured unit exist at all** to the rest of core. Collapse `_measurement_rows` into `_rows` (and `_recorded_keys`) *before* `finalize`'s existing `units.parquet` block, so collapsed units flow through the path that already works rather than a parallel one.

**Pin it with the reconciliation, not just the file**: a run whose step only measures must report `completed` equal to the number of distinct units measured, `failed` zero, and `resolved == completed + ineligible + failed`.

### Also settle: a unit with both a plain row and measurement rows

Task 4 left this reachable in either order, and it is out of that task's scope but squarely in yours:

```
io.record("p1", {"score": 1})
io.record("p1", {"score": 2}, measurement="r1")   # no raise; unit now in both stores
```

Task 4's implementer was asked to argue which is right — refuse the mixture, or define which store wins — citing a document sentence if one settles it. **Read its report before deciding**, then implement your decision and pin it. Silently letting both stores contribute to one unit row is the one outcome to avoid: it is the retry-versus-measurement ambiguity the `measurement=` argument exists to remove, reappearing one layer down.

### First: thread `measurements` from the config into `StepIO`, or none of this is reachable

Task 4 added `StepIO(measurements=...)` and scoped itself to `artifacts.py`, so **`runner.py` never passes it**. Verified: `runner.py`'s single `StepIO(...)` construction has no `measurements` argument, so in a real run `io.record(..., measurement="r1")` raises `E-STEP-MEASUREMENT-UNDECLARED` **even when the config declares `measurements`** — the declaration is honoured at the input path and refused at the step path.

Thread `data.units.measurements` through to that constructor, and pin it with a test that runs a **real step** calling `io.record(..., measurement=)` under a declaring config and gets rows rather than a raise. A `StepIO` built directly in a test cannot catch this — that is exactly how it got missed.

**Interfaces:**
- Consumes: task 1's **`rule_for`, `_apply` and `coerce_for_rule`** — not `collapse_measurements` itself.

**Coercion applies here too.** Task 3 established that a numeric rule must never reach `_apply` with unconverted values. `io.record` coerces through `coerce_scalars`, so recorded values are already `int`/`float`/`str`/`bool`/`None` rather than CSV strings — **check whether that fully settles it rather than assuming either way**, and say which in your report. A recorded `str` column under `collapse: mean` is still reachable if a step records `"10"`.

**A correction to decision 4, found by this plan's type-consistency pass.** The spec says both paths call "one collapse function". They cannot call the *same* one as task 1 writes it: `collapse_measurements` takes `list[Unit]` and returns `Unit`s, while this path holds recorded rows keyed by `(unit_key, measurement)` and must produce rows. **What is genuinely shared is the rule application** — `rule_for` (per-column rule, falling back to `first`) and `_apply` (the rule itself). Both live in `units.py`; `rule_for` is already public because task 2's check calls it too, so you are its **third** caller. `_apply` is still private with one caller outside its module — make it public if you need it, in the same commit, and update every reference.

**Also expect `is_measurement_numeric` (or whatever task 3 names it) to be there by the time you arrive** — task 2 wrote a numeric predicate, and it is being moved beside `_apply` so that the validate-time "this column is numeric" and the runtime's cannot disagree. Use it; do not write a second one.

Decision 4's *reason* is untouched and is what matters: one place decides what `mean` means, so the retry path and the measurement path cannot come to disagree about identical-looking rows. Making `collapse_measurements` generic over mappings to satisfy the letter of "one function" would be worse — a signature shaped by a slogan rather than by either caller. Record this correction in your report; it amends the spec, and the spec is what a later reader will check the code against.

At finalize, measurement rows collapse into unit rows under the declared rule, then flow into `units.parquet` exactly as recorded rows do. The uncollapsed rows are written to `measurements.parquet` at `(unit, measurement)` — **present only when a step passed `measurement=`**, per decision 5: the artifact holds what the *run* measured, and input rows are the input's.

- [ ] **Step 1: Write the failing tests**

```python
def test_measurement_rows_collapse_into_one_unit_row(step_io):
    step_io.record("p1", {"score": 10}, measurement="r1")
    step_io.record("p1", {"score": 20}, measurement="r2")
    step_io.finalize()
    assert read_parquet(step_io.dir / "units.parquet") == [{"unit": "p1", "score": 15.0}]


def test_measurements_parquet_holds_the_uncollapsed_rows(step_io):
    step_io.record("p1", {"score": 10}, measurement="r1")
    step_io.record("p1", {"score": 20}, measurement="r2")
    step_io.finalize()
    rows = read_parquet(step_io.dir / "measurements.parquet")
    assert rows == [
        {"unit": "p1", "measurement": "r1", "score": 10},
        {"unit": "p1", "measurement": "r2", "score": 20},
    ]


def test_no_measurements_parquet_when_no_step_measured(step_io):
    """Decision 5: the file holds what the run measured, not what the input carried."""
    step_io.record("p1", {"score": 10})
    step_io.finalize()
    assert not (step_io.dir / "measurements.parquet").exists()
```

- [ ] **Step 2: Run and confirm each fails**

- [ ] **Step 3: Implement**, calling `rule_for` and `_apply` rather than re-deriving what a rule means.

- [ ] **Step 4: Run and confirm they pass**

- [ ] **Step 5: Mutation-test — the one that matters most in this slice**

Change the *step path* to average with a hand-written `sum(...)/len(...)` instead of calling `_apply`. Confirm the tests still pass (they will — the rule agrees today), then change task 1's `_apply` `mean` branch to a median and confirm **only the input path's test fails** while the step path's passes. That divergence is the defect decision 4 exists to prevent; having seen it, revert both, delete `__pycache__`, verify by behaviour, and record in your report that the shared call is what keeps them from drifting.

- [ ] **Step 6: Commit**

```bash
git commit -am "feat: collapse a step's measurements under the same rule the input takes"
```

---

