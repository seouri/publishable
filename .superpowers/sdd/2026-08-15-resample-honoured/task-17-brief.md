## Task 17: Echo the resolved `method`/`n`/`stratify_by` into `run.yaml`

**Files:** Modify `src/publishable/cli.py`, `docs/reference.md`. Test `tests/test_cli.py`.

**Interfaces:**
- Consumes: `cli.command_run`'s `resample_spec` (Task 13); the `beside_n` parameter of `stats.summarize_step`, documented at `src/publishable/stats.py:1220` as "core-supplied context copied verbatim into every metric block"; the locals `cond_beside_n` and `weighted_beside` in `command_run`.
- Produces: a `resample: {method, n, stratify_by}` sibling of `n` in every metric block of a run that declared one.

**Why `beside_n` is the right carrier and not a new one.** `summarize_step`'s docstring states the rule: a key that **joins** `n` travels in `counts` (`clusters`, `effective`, `ineligible`); a key that **sits beside** `n` travels in `beside_n`, and § Weighted samples' `weighted_by` is the precedent — a key that names a declaration rather than reporting a figure. `reference.md` § Statistical reporting requires "the resolved values are recorded in `run.yaml` beside the interval so the number is never the result of an undocumented default", which is the same position. Adding a second mechanism for the same sentence is how two spellings of one construction drift apart.

**`resample.n` is what was requested; `resample_draws` is what the interval rests on.** For a column they are equal by Task 11's invariant. For a derived metric they differ whenever a draw was degenerate, and that difference is exactly what `W-STATS-RESAMPLE-THIN` reports. Both keys are therefore meaningful and neither replaces the other.

**Absent, not null, when nothing was declared.** Task 1's pin asserts the undeclared shape, and an explicit `resample: null` in a metric block would claim a resolution was performed.

- [ ] **Step 1: Write the failing test** — append to `tests/test_cli.py`:

```python
def test_the_resolved_resample_is_recorded_beside_every_interval(tmp_path, capsys):
    """§ Statistical reporting: "the resolved values are recorded in `run.yaml`
    beside the interval so the number is never the result of an undocumented
    default". Carried on `beside_n`, the documented route for a key that sits
    beside `n` rather than joining it — the same position `weighted_by` takes."""
    doc = run_a_project(
        tmp_path, capsys=capsys, aggregate_returns="mean_pred", units=40,
        unit_attributes=["cohort"],
        statistics={"correction": "holm",
                    "resample": {"method": "bootstrap", "n": 500,
                                 "stratify_by": ["cohort"]}},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    aggregated = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]
    for name in ("pred", "mean_pred"):
        assert aggregated[name]["resample"] == {
            "method": "bootstrap", "n": 500, "stratify_by": ["cohort"]
        }
    # `n` is what was REQUESTED; `resample_draws` is what the interval rests on.
    # Equal for a column by construction, and equal here for the derived metric
    # because no draw was degenerate — but they are different facts and both are
    # recorded.
    assert aggregated["pred"]["resample_draws"] == 500
    assert aggregated["mean_pred"]["resample_draws"] == 500


def test_no_resample_block_is_recorded_when_none_was_declared(tmp_path, capsys):
    """Absent, not null: an explicit null would claim a resolution was performed.
    Paired with a positive assertion in the same test so it cannot pass by
    nothing having run."""
    doc = run_a_project(
        tmp_path, capsys=capsys, aggregate_returns="mean_pred", units=40
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    aggregated = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]
    assert "resample" not in aggregated["pred"]
    assert "resample" not in aggregated["mean_pred"]
    # The positive companion: the derived metric IS still resampled at the
    # documented default, so the block really did run.
    assert aggregated["mean_pred"]["resample_draws"] == 2000
    assert aggregated["mean_pred"]["method"] == "percentile_over_units"
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_cli.py -k resolved_resample_is_recorded -x`. Fails on the missing `resample` key; the second test passes and is the control.

- [ ] **Step 3: Implement** — in `src/publishable/cli.py`, where `cond_beside_n` and `weighted_beside` are built, merge in:

```python
            # The resolved block, beside the interval rather than joining `n` —
            # `summarize_step`'s own rule for which carrier a fact takes, and
            # `weighted_by` is the precedent: a key that names a declaration
            # rather than reporting a figure. § Statistical reporting requires
            # it be recorded "so the number is never the result of an
            # undocumented default".
            #
            # ABSENT when nothing was declared, not null: a null would claim a
            # resolution was performed. `stratify_by` is materialized as a list
            # even where the config wrote a bare string, because the record
            # resolves what the config abbreviates — the same rule `of`/`against`
            # follow in `results.contrasts`.
            #
            # `n` here is what was REQUESTED; `resample_draws` beside it is what
            # the interval rests on. Equal for a column by construction and
            # different for a derived metric whenever a draw was degenerate,
            # which is what `W-STATS-RESAMPLE-THIN` reports.
            resample_beside = (
                {
                    "resample": {
                        "method": resample_spec["method"],
                        "n": resample_spec["n"],
                        "stratify_by": list(resample_spec["stratify_by"]),
                    }
                }
                if resample_spec["declared"]
                else {}
            )
```

  and add `**resample_beside` to both `cond_beside_n` and `weighted_beside`. `weighted_beside` is what the `report_by` level call uses, so a level block carries the declaration too — correct, because the declaration is true of the run either way, the same argument the code already makes for `weighted_by` there.

  (b) `docs/reference.md`: extend the `run.yaml` metric-block example in § What isn't a repeat (the one carrying `resample_draws: 2000`) with the sibling, and say in § Statistical reporting which key is which:

```yaml
r:
  value: 0.607
  basis: units                                 # what the interval is over
  n: {resolved: 240, completed: 228, failed: 12}
  technical_n: {min: 2, max: 3, median: 3}     # collapsed, shown for transparency
  repeat_spread: {std: 0.014, n: 5, kind: seed}   # how much the pipeline moved
  ci95: [0.517, 0.683]
  method: percentile_over_units
  resample_draws: 2000                         # how many draws the interval rests on
```

  **Do not change any number in that block** — it is the shared worked example, and `CLAUDE.md` § The worked example says those intervals were checked numerically against a synthetic 228-unit table and must not be narrowed. Add the `resample:` sibling only in a **second**, clearly-labelled example showing a declared resample, so the worked example's config (which declares none) stays consistent with it.

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_cli.py -k resample`, then `uv run pytest`, `uv run mypy`, `uv run ruff check .`. Then the cross-document pass: § Config completeness (no new config field was added, so nothing moves), § Schema fields in prose (the new `resample` record key must appear in a `run.yaml` example and in prose), and the worked example's numbers unchanged — `grep -n '0.517, 0.683\|−0.007, 0.059\|0.014' docs/reference.md README.md docs/design-principles.md` must return what it returned before.

- [ ] **Step 5: Mutate** — in `cli.py`, drop the `if resample_spec["declared"]` guard so the block is emitted unconditionally. Run `uv run pytest tests/test_cli.py -k no_resample_block_is_recorded`. It must FAIL. Delete `__pycache__`, restore the guard in place, re-run. Second mutation: change `"stratify_by": list(resample_spec["stratify_by"])` to `"stratify_by": []`; `test_the_resolved_resample_is_recorded_beside_every_interval` must FAIL. Revert in place.

- [ ] **Step 6: Commit** — `feat: record the resolved resample beside every interval`.

---

