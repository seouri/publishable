### Task 7: Contrasts reach the record

**Files:**
- Modify: `src/publishable/cli.py`, `src/publishable/run_record.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: everything above; `collapse_repeats(results, step_name, condition_index, fold_members)`; `summarize_step`'s output shape; the condition metadata `cli.py` already builds with `label`, `is_baseline`, and `values`.
- Produces: a `vs_baseline` block in the record.

`docs/reference.md` § The two files shows the entry shape:

```yaml
vs_baseline:
  step03_analyze:
    r: {delta: 0.026, basis: units, paired: true,
        method: paired_percentile_over_units,
        ci95: [-0.007, 0.059],
        cohens_d: null}
```

**In this slice each entry also carries `n_paired`, and `correction: null`.** The correction, `ci95_corrected`, `correction_level`, `family_size` and `family` keys belong to S4c — do not add them, and do not remove `W-STATS-FAMILY`.

**Which construction applies is decided by the metric's origin**, not by a flag: a recorded column metric takes `paired_t_over_units` over the per-unit differences; a derived metric takes `paired_percentile_of_derived`. `cohens_d` is `cohens_dz(diffs)` for the first and `None` for the second.

**`min_reported_n` becomes real here.** `materialize.py` writes it into every generated config and nothing reads it — a live silent no-op. `reference.md` § Contrasts: it "applies to a `within` contrast's `n_paired`". Warn when a contrast's `n_paired` falls below `limits.min_reported_n`. Grep for an existing `W-` identifier before minting one.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_baseline_sweep_reports_a_delta(tmp_path, capsys):
    doc = run_a_project(tmp_path, capsys=capsys, sweep={
        "baseline": {"analysis.method": "pearson"},
        "grid": {"analysis.method": ["spearman"]}})
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entry = _first_contrast(run, "method=spearman")
    assert entry["paired"] is True
    assert entry["n_paired"] > 0
    assert entry["method"] in ("paired_t_over_units", "paired_percentile_over_units")
    assert entry["correction"] is None          # S4c's job, disclosed not applied


def test_a_run_with_no_baseline_has_no_vs_baseline_block(tmp_path, capsys):
    """Absent, not empty. An empty block would claim a comparison was made and
    found nothing."""
    doc = run_a_project(tmp_path, capsys=capsys)
    text = (doc["run_dir"] / "run.yaml").read_text()
    assert "vs_baseline" not in text


def test_a_thin_pairing_warns(tmp_path, capsys):
    doc = run_a_project(tmp_path, capsys=capsys, units=3, limits={"min_reported_n": 10},
                        sweep={"baseline": {"analysis.method": "pearson"},
                               "grid": {"analysis.method": ["spearman"]}})
    assert "min_reported_n" in doc["stdout"] or "N_PAIRED" in doc["stdout"]
```

`run_a_project` is the end-to-end driver in `tests/test_cli.py`; **reuse it**, extending it additively with defaulted keywords if it cannot yet vary units or limits, and say what you added. `_first_contrast` is a small local helper — write it if the file has none.

- [ ] **Step 2: Run to verify they fail, then implement**

Read how `aggregated` is assembled in `cli.py` and follow that shape for `vs_baseline`. **Report where you attached it** so the reviewer can check it against `reference.md` § The two files rather than guess.

- [ ] **Step 3: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/cli.py src/publishable/run_record.py tests/test_cli.py
git commit -m "Report a contrast beside the conditions it compares"
```

---

