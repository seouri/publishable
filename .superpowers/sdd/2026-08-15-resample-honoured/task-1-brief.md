## Task 1: The regression pin — the undeclared-`resample` shape, `null` and absent separately

**Files:** Modify (append) `tests/test_cli.py`. No `src/` change.

**Interfaces:**
- Consumes: `run_a_project(tmp_path, *, capsys=None, aggregate_returns=None, units=10, sweep=..., statistics=..., **overrides)` from `tests/test_cli.py`; `_named_contrast(run, label, metric)` at `tests/test_cli.py:3122`; `_first_metric(run, name)` at `tests/test_cli.py:2218`.
- Produces: `test_the_undeclared_resample_shape_is_pinned_absent_key` and `test_the_undeclared_resample_shape_is_pinned_explicit_null` — the only baseline any later task can be compared against.

**Why first.** Once `percentile_over_units` is wired into `summarize_step` there is nothing left to compare against. The live hazard is Task 13, where the literal `derived_metric_draws = 2000` becomes a resolved value: that is where an undeclared config silently acquires a different draw count. `materialize.py` writes **neither** `resample` key, so the absent-key case and the explicit-`null` case must be pinned separately — `_check_unimplemented`'s `if statistics.get(field)` is false for both, but they are different documents.

**Trap this task must avoid.** `run_a_project` merges overrides with `doc.update(overrides)` — a **top-level replace**. Passing `statistics={"resample": None}` would delete the `correction: holm` `materialize.py` writes, moving `correction_level` and `family_size` and pinning a baseline the test itself changed. The explicit-`null` test therefore passes `statistics={"correction": "holm", "resample": None}`, and **both** tests assert `correction_level` and `family_size` so a future accidental replacement is caught.

**The second trap, and it is the one that would have made this pin worthless.** `tests/test_cli.py`'s existing `_AGGREGATE_STEP` records `pred = float(i)` with **no reference to `cfg`**, so the column is byte-identical under every condition — the derived-contrast test at `tests/test_cli.py:3138` says so in its own docstring, and works only because `aggregate` is monkeypatched to vary by `cfg`. A recorded column has no such patch. So under a baseline sweep the per-unit differences are **all zero**, and verified against the build: `paired_t_over_units([0.0] * 40)` returns `Interval(0.0, 0.0)` and **`cohens_dz([0.0] * 40)` returns `None`**. A pin asserting `cohens_d is not None` would fail, and every later width comparison would be `0 > 0`. This task therefore introduces `_CONDITION_SCALED_STEP`, a step whose recorded column varies with the swept axis, and Task 16 reuses it.

- [ ] **Step 1: Write the failing test** — append to `tests/test_cli.py`:

```python
_CONDITION_SCALED_STEP = '''\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        # The recorded column VARIES with the swept axis. `_AGGREGATE_STEP`
        # records `float(i)` regardless of `cfg`, which makes every per-unit
        # difference zero: `paired_t_over_units` then returns a zero-width
        # interval and `cohens_dz` returns `None`, so a contrast pin over it
        # asserts nothing and every width comparison is `0 > 0`. Scaled by
        # `analysis.method` so both the differences and the draw pool have real
        # dispersion under every comparison this file builds.
        scale = {{"pearson": 1.0, "spearman": 2.0, "kendall": 3.0}}[
            cfg.parameters.analysis.method
        ]
        units = list(io.units)
        for i, unit in enumerate(units):
            io.record(unit.key, {{"pred": float(i) * scale}})
        return {{"n_units": len(units)}}
'''


def _assert_undeclared_resample_shape(run: dict[str, Any]) -> None:
    """The full shape an undeclared `statistics.resample` produces, which H4a
    must not move. Shared by the absent-key and the explicit-`null` pins because
    the two configs are different documents that must produce one shape:
    `materialize.py` writes neither key, and `_check_unimplemented`'s
    `if statistics.get(field)` is false for both — so a resolution step that read
    `.get("resample", DEFAULT)` instead of `.get("resample") or DEFAULT` would
    separate them, and nothing else in the suite would notice."""
    assert run["status"] == "completed"
    aggregated = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]
    # A recorded column: the t-interval, and NO `resample_draws` key at all.
    column = aggregated["pred"]
    assert column["basis"] == "units"
    assert column["method"] == "t_over_units"
    assert column["ci95"] is not None
    assert "resample_draws" not in column
    # A derived metric: resampled whether or not `resample` is declared, at the
    # documented default of 2000 draws, and never carrying an effect size.
    derived = aggregated["mean_pred"]
    assert derived["basis"] == "units"
    assert derived["method"] == "percentile_over_units"
    assert derived["resample_draws"] == 2000
    assert derived["cohens_d"] is None
    assert derived["ci95"] is not None
    # A column contrast: Student's t on the per-unit differences, with Cohen's dz.
    col_contrast = _named_contrast(run, "method=spearman", "pred")
    assert col_contrast is not None
    assert col_contrast["method"] == "paired_t_over_units"
    assert col_contrast["cohens_d"] is not None
    assert "resample_draws" not in col_contrast
    # A derived contrast: the joint percentile, and no effect size.
    derived_contrast = _named_contrast(run, "method=spearman", "mean_pred")
    assert derived_contrast is not None
    assert derived_contrast["method"] == "paired_percentile_over_units"
    assert derived_contrast["cohens_d"] is None
    # The correction family, which a replaced `statistics` block would move:
    # two metrics over one comparison is a family of 2, and holm's rank-1 level
    # is ALPHA/2. Asserted on both pins so an override that dropped
    # `correction: holm` cannot pass.
    assert col_contrast["family"] == {"comparisons": 1, "metrics": 2}
    assert col_contrast["family_size"] == 2
    assert col_contrast["correction"] == "holm"
    assert col_contrast["correction_level"] in (
        pytest.approx(0.05 / 2), pytest.approx(0.05 / 1)
    )
    # Holm ranks on the point estimate over HALF THE RAW ci95 WIDTH, never on a
    # p-value — the family often carries none. Both members' levels come from
    # that ranking, so the two distinct levels must both be present exactly once.
    levels = sorted(
        m["correction_level"]
        for m in (col_contrast, derived_contrast)
    )
    assert levels == [pytest.approx(0.025), pytest.approx(0.05)]


_PIN_SWEEP = {
    "baseline": {"analysis.method": "pearson"},
    "grid": {"analysis.method": ["spearman"]},
}


def _pinned_run(tmp_path, capsys, monkeypatch, **overrides):
    """One run carrying both a recorded column and a derived metric under one
    baseline comparison. `_starter_step` rather than `aggregate_returns`,
    because that shorthand's step records `float(i)` regardless of `cfg` and a
    contrast over it is degenerate."""
    from publishable.templates.builtin.generic import GenericTemplate

    monkeypatch.setattr(
        GenericTemplate,
        "aggregate",
        lambda self, units, cfg: {"mean_pred": sum(units.pred) / len(units)},
    )
    return run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        sweep=_PIN_SWEEP,
        _starter_step=_CONDITION_SCALED_STEP,
        **overrides,
    )


def test_the_undeclared_resample_shape_is_pinned_absent_key(tmp_path, capsys, monkeypatch):
    """`materialize.py` writes no `resample` key at all, so this is the shape a
    generated config actually produces. Pinned before H4a wires
    `percentile_over_units` into `summarize_step`, because after that there is
    nothing left to compare against."""
    doc = _pinned_run(tmp_path, capsys, monkeypatch)
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    assert "resample" not in (run["config"].get("statistics") or {})
    _assert_undeclared_resample_shape(run)


def test_the_undeclared_resample_shape_is_pinned_explicit_null(tmp_path, capsys, monkeypatch):
    """`resample: null` is a DIFFERENT document from the absent key and must
    produce the identical shape. `correction: holm` is restated here because
    `run_a_project` merges overrides with `doc.update`, a top-level replace: a
    bare `statistics={"resample": None}` would delete the correction
    `materialize.py` writes and move every `correction_level` below."""
    doc = _pinned_run(
        tmp_path, capsys, monkeypatch,
        statistics={"correction": "holm", "resample": None},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    assert run["config"]["statistics"]["resample"] is None
    _assert_undeclared_resample_shape(run)
```

`run_a_project` has no `_starter_step` parameter today. **Add one in this task**, and Tasks 15 and 16 reuse it: a keyword that `monkeypatch`es `publishable.generators.experiment.STARTER_STEP` inside the existing `pytest.MonkeyPatch.context()` block, exactly the way `aggregate_returns` already does, and document it in `run_a_project`'s docstring beside `extra_step_source`. Duplicating the scaffold-and-commit dance instead is what that helper exists to prevent.

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_cli.py -k undeclared_resample_shape -x`. Both tests fail first on the unknown `_starter_step` keyword; once that parameter is added, **this is a characterization pin, so both must PASS immediately.** If either then fails, the assertion is wrong, not the code — fix the assertion to what the run actually produces and record the difference in the commit message. Two verified facts to check the assertions against before changing anything: `paired_t_over_units([0.0] * 40)` returns `Interval(0.0, 0.0)` and `cohens_dz([0.0] * 40)` returns `None`, which is why `_CONDITION_SCALED_STEP` exists.

- [ ] **Step 3: Implement** — the `_starter_step` parameter on `run_a_project`, and nothing else. The pin itself is the deliverable. `_PIN_SWEEP` gives exactly one baseline comparison, `_CONDITION_SCALED_STEP` gives a column that differs between the two sides, and the monkeypatched `aggregate` gives the derived metric.

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_cli.py -k undeclared_resample_shape`, then the whole suite: `uv run pytest`.

- [ ] **Step 5: Mutate** — in `src/publishable/cli.py`, change `derived_metric_draws = 2000` to `derived_metric_draws = 500`. Run `uv run pytest tests/test_cli.py -k undeclared_resample_shape`. Both tests must FAIL on `derived["resample_draws"] == 2000`. Delete `__pycache__`. Edit the line back to `2000` in place. Re-run; both pass. Then a second mutation, because the first only proves the draw count is pinned: in `src/publishable/stats.py`'s `summarize_step`, change the unweighted unclustered column branch `interval = t_over_units(values)` to `interval = percentile_over_units(values, 1, draws=2000)`. Both tests must FAIL on `column["method"] == "t_over_units"`. Revert in place the same way.

- [ ] **Step 6: Commit** — `test: pin the undeclared-resample shape, absent key and explicit null separately`.

---

