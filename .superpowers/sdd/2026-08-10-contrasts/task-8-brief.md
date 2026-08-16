### Task 8: The acceptance test

**Files:**
- Test: `tests/test_cli.py`, `tests/test_stats.py`
- Modify: whatever the tests show is still unwired.

**Interfaces:**
- Consumes: everything above.
- Produces: no new source interfaces.

Every earlier task is testable in isolation, and this project has twice shipped a subsystem green in unit tests and unreachable from `main(["run", ...])`. **Report every `src/` change you need here — each one is a piece an earlier task left inert.**

**The worked example is the anchor, but assert properties rather than reverse-engineering a fixture to hit exact values.** `CLAUDE.md` pins delta 0.026 with `ci95` [−0.007, 0.059], kendall's −0.169 with [−0.213, −0.125], and records that the delta's half-width "does not go below ≈0.033 for a linear-versus-rank contrast at this *n*". Building a 228-unit fixture that reproduces those exactly is not a test, it is curve-fitting. Assert instead:

- [ ] **Step 1: Write the acceptance tests**

```python
def test_a_paired_delta_is_narrower_than_the_conditions_it_compares(tmp_path, capsys):
    """The contrast that `allocation: within` buys, end to end: per-condition
    intervals are wide and the delta's is narrow, over the same units."""
    doc = run_a_project(tmp_path, capsys=capsys, units=120, sweep={
        "baseline": {"analysis.method": "pearson"},
        "grid": {"analysis.method": ["spearman"]}})
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    delta = _first_contrast(run, "method=spearman")
    width = delta["ci95"][1] - delta["ci95"][0]
    per_condition = _first_metric_width(run, condition_index=1)
    assert width < per_condition


def test_the_delta_half_width_is_not_implausibly_narrow(tmp_path, capsys):
    """CLAUDE.md records ≈0.033 as unreachable for a linear-versus-rank contrast
    at n≈228; a fixture producing far less has lost the resampling."""
    doc = run_a_project(tmp_path, capsys=capsys, units=120, sweep={
        "baseline": {"analysis.method": "pearson"},
        "grid": {"analysis.method": ["spearman"]}})
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    lo, hi = _first_contrast(run, "method=spearman")["ci95"]
    assert hi > lo                                  # a real interval, not a point
```

- [ ] **Step 2: Verify by hand**

Scaffold a project **outside the repository**, give it a baseline and one grid condition, run it, and paste `run.yaml`'s `vs_baseline` block into your report alongside the two conditions' own intervals. A test can share a bug with the code it tests; a record you read cannot. Confirm `git status` is clean of stray scaffold directories before committing — an earlier slice leaked one from a wrong working directory.

- [ ] **Step 3: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add tests/ src/
git commit -m "Compare two conditions end to end"
```

---

## Self-Review

**Spec coverage.** Comparison resolution → Task 1. `within` → Task 2. The intersection and `n_paired` → Task 3. `paired_t_over_units` and `cohens_dz` → Task 4. `paired_percentile_of_derived` → Task 5. The refusals and retiring `E-STATS-CONTRASTS-UNSUPPORTED` → Task 6. The record, plus `min_reported_n` → Task 7. Acceptance → Task 8. No spec section is unassigned. The two unreachable constructions are documented as out of scope rather than built.

**Placeholders.** Every code step carries code and every test step carries tests. Four tasks name an existing helper (`write_config`, `codes`, `run_a_project`, and `tests/test_sweep.py`'s `Condition` idiom) rather than inventing one, each with an instruction to read and match — deliberate, since a second idiom is the defect.

**Type consistency.** `Comparison(id, of, against, within)` from Task 1 is consumed unchanged in Tasks 6 and 7. `units_matching(roster, within) -> set[str] | None` feeds `paired_keys(of, against, allowed)` in Task 3, whose `allowed` is exactly that type. `paired_t_over_units` and `paired_percentile_of_derived` both return the documented `method` strings the record asserts in Task 7. `Interval` is confirmed to be a frozen dataclass with **three** fields — `low`, `high`, `method` — with no `draws_used`; `percentile_of_derived` returns a **tuple** of `(Interval | None, int)` and `paired_percentile_of_derived` matches that shape.

**Three assumptions verified against the codebase before writing.** `Interval` has exactly three fields, so nothing here unpacks or indexes it. `summarize_step` already takes a `resample` mapping of key → callable, so a derived metric's `compute` is available at the call site Task 7 needs it. And `min_reported_n` is written by `materialize.py` and read by nothing, which is why Task 7 closes it rather than assuming it works.

**The risk this plan carries.** Task 5 is where the pairing lives, and its failure mode is quiet: an implementation drawing each side independently produces a plausible, merely wider interval. The test that catches it is the narrowness comparison, and the task explicitly instructs writing the wrong version first to confirm the test fails against it. If that step is skipped, the whole-branch review should redo it.
