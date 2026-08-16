## Task 18: `report_by` levels resample without minting `Member`s, and a `summary` `Estimate` is never recomputed

**Files:** Test only — `tests/test_cli.py`. No `src/` change expected.

**Interfaces:**
- Consumes: `cli.command_run`'s `report_by` block at `src/publishable/cli.py:1832–2000`, whose `summarize_step` call is at `:1984`; `cli._comparison_step_blocks`'s per-metric loop at `:766`, which iterates `sorted((set(of_summary) & set(against_summary)) - {"by"})`; `run_record.summary_values` at `src/publishable/run_record.py:58`.
- Produces: two assertions that keep two properties holding once levels start carrying percentile intervals. **Verify-and-pin, not a build.**

**Property 1, already true.** `Member`s are constructed in exactly one place — `_comparison_step_blocks`' per-metric loop — which explicitly excludes the `by` key, where the whole `report_by` block lives, with a comment saying why. So a `report_by` level never constructs a `Member` and never joins the correction family. Task 15 threads `strata` into that call site and Task 17 threads the declaration, so H4a touches this code whether or not it claims anything here.

**Property 2, a boundary this slice owes rather than merely respects.** A `summary`-step `Estimate` is `reported: true`, sits outside the correction family, and is never recomputed. Task 14's pass walks every metric block, so the test is owed. It is **structural**: an `Estimate` reaches `run.yaml` through `run_record.summary_values` into `results.summary`, never through `summarize_step`.

**Both are absence assertions and both need positive companions in the same test.** "A `report_by` level mints no `Member`s" and "an `Estimate` is never recomputed" pass identically if nothing ran. The companions: the level **did** produce a percentile interval; the `Estimate` **is** still present with its `ci95` and `method` unchanged, beside a column in the same run that **did** take `method: percentile_over_units`.

- [ ] **Step 1: Write the failing test** — append to `tests/test_cli.py`:

```python
def test_a_report_by_level_resamples_without_joining_the_correction_family(
    tmp_path, capsys
):
    """`Member`s are built in one place, `_comparison_step_blocks`' per-metric
    loop, which excludes the `by` key the whole strata block lives under. That
    property already holds; this keeps it holding now that levels carry
    percentile intervals.

    The absence assertion has a positive companion IN THE SAME TEST: the level
    genuinely produced an interval, so the test cannot pass by nothing having
    been stratified. And `family` is asserted to the exact shape a
    strata-free run would have, so a level joining the family shows up as an
    inflated metric count rather than as a silence."""
    doc = run_a_project(
        tmp_path, capsys=capsys, units=40, unit_attributes=["cohort"],
        sweep={"baseline": {"analysis.method": "pearson"},
               "grid": {"analysis.method": ["spearman"]}},
        statistics={"correction": "holm", "report_by": ["cohort"],
                    "resample": {"method": "bootstrap", "n": 2000}},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    aggregated = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]
    # Positive companion: the level exists and carries a real percentile
    # interval, drawn over its own units.
    level = aggregated["by"]["cohort"]["a"]["pred"]
    assert level["method"] == "percentile_over_units"
    assert level["ci95"] is not None
    assert level["n"]["completed"] < aggregated["pred"]["n"]["completed"]
    # The absence: one comparison, one metric — `pred`. The `by` key is not a
    # metric and neither are its levels, so the family stays 1 × 1.
    entry = _named_contrast(run, "method=spearman", "pred")
    assert entry["family"] == {"comparisons": 1, "metrics": 1}
    assert entry["family_size"] == 1
    # And there is no contrast entry for `by` at all.
    for condition in run["results"]["conditions"]:
        for step_block in condition.get("vs_baseline", {}).values():
            assert "by" not in step_block


_SUMMARY_ESTIMATE_STEP = '''\
# src/{pkg}/steps/{step_name}.py — generated, and runnable as-is
from publishable import BaseStep, Estimate


class Step(BaseStep):
    scope = "summary"

    def run(self, cfg, io):
        return {{
            "site_adjusted_delta": Estimate(
                value=0.041, ci95=[0.012, 0.070], n=228, method="mixed_model"
            ),
            "converged": True,
        }}
'''


def test_a_summary_estimate_is_not_recomputed_by_the_resample_pass(tmp_path, capsys):
    """A `summary`-step `Estimate` is `reported: true`, outside the correction
    family, and never recomputed — and H4a's column pass walks every metric
    block, so this is a boundary the slice OWES a test for rather than one it
    merely respects. Structural: an `Estimate` reaches `results.summary` through
    `run_record.summary_values`, never through `summarize_step`.

    The positive companion is in the same test: a recorded column in the same
    run DID take a percentile interval, so this cannot pass by the resample
    having done nothing at all."""
    doc = run_a_project(
        tmp_path, capsys=capsys, units=40,
        extra_steps=["step02_report"],
        extra_step_source=_SUMMARY_ESTIMATE_STEP,
        statistics={"correction": "holm",
                    "resample": {"method": "bootstrap", "n": 2000}},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    estimate = run["results"]["summary"]["step02_report"]["site_adjusted_delta"]
    assert estimate == {
        "value": 0.041,
        "reported": True,
        "ci95": [0.012, 0.070],
        "n": 228,
        "method": "mixed_model",
    }
    # Nothing the resample pass writes has been added to it.
    assert "resample_draws" not in estimate
    assert "resample" not in estimate
    assert "basis" not in estimate
    assert "correction" not in estimate
    # The non-Estimate return is untouched too.
    assert run["results"]["summary"]["step02_report"]["converged"] is True
    # Positive companion: a column in the same run IS resampled.
    aggregated = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]
    assert aggregated["pred"]["method"] == "percentile_over_units"
    assert aggregated["pred"]["resample"]["n"] == 2000
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_cli.py -k report_by_level_resamples or summary_estimate_is_not_recomputed -x`. Both are expected to **pass immediately**: they pin properties that already hold. If either fails, a preceding task broke a boundary — stop and fix the task that did, not the test.

- [ ] **Step 3: Implement** — no `src/` change. If `test_a_report_by_level_resamples_without_joining_the_correction_family` fails on the level's `method`, Task 15 did not thread `resample_columns`/`strata` into the `:1984` call site; fix it there.

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_cli.py -k report_by or summary_estimate`, then `uv run pytest`.

- [ ] **Step 5: Mutate** — in `src/publishable/cli.py`, remove `- {"by"}` from `_comparison_step_blocks`' metric loop, so it reads `sorted(set(of_summary) & set(against_summary))`. Run `uv run pytest tests/test_cli.py -k report_by_level_resamples`. It must FAIL on `entry["family"] == {"comparisons": 1, "metrics": 1}` — the metric count becomes 2 — which is why the family shape is asserted to an exact value rather than merely checked non-empty. Delete `__pycache__`, restore `- {"by"}` in place, re-run. Second mutation: in `src/publishable/run_record.py`, add `"basis": "units"` to the dict `summary_values` builds for an `Estimate`. `test_a_summary_estimate_is_not_recomputed_by_the_resample_pass` must FAIL on the exact-equality assertion. Revert in place.

- [ ] **Step 6: Commit** — `test: pin that strata mint no Members and a summary Estimate is never recomputed`.

---

