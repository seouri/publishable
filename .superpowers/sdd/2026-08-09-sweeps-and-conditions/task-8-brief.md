### Task 8: Wire the CLI, and the acceptance test

**Files:**
- Modify: `src/publishable/cli.py`
- Test: `tests/test_acceptance.py`

**Interfaces:**
- Consumes: everything above.
- Produces: `command_run` expands the sweep, builds one `cfgs` mapping, writes `sweep.yaml`, and aggregates per condition.

**The wiring, precisely.** `cli.py` currently hardcodes `conditions=[(0, None)]` and `condition_index == 0` in two places. Both become the real expansion.

- [ ] **Step 1: Write the failing acceptance test**

```python
def test_a_sweep_runs_every_condition_over_one_roster(tmp_path: Path):
    """3 conditions × 5 seed repeats = 15 executions, in the right tree."""
    root, cfg, results_dir = build_sweep_project(tmp_path, n_units=240)
    assert main(["run", str(cfg)]) == EXIT_OK

    run_dir = next(results_dir.glob("run_*"))
    doc = yaml.safe_load((run_dir / "run.yaml").read_text())

    conds = doc["results"]["conditions"]
    assert [c["label"] for c in conds] == ["baseline", "method=spearman", "method=kendall"]
    assert conds[0]["is_baseline"] is True

    # the tree: a conditions/ level, five repeat dirs under each
    labels = sorted(p.name for p in (run_dir / "conditions").iterdir())
    assert labels == ["00_baseline", "01_method=spearman", "02_method=kendall"]
    for label in labels:
        seeds = [p for p in (run_dir / "conditions" / label).iterdir() if p.is_dir()]
        assert len(seeds) == 5, label

    lines = (run_dir / "executions.jsonl").read_text().splitlines()
    assert len(lines) == 15


def test_each_condition_reports_its_own_numbers(tmp_path: Path):
    """The headline test: two conditions must not share an aggregated block."""
    root, cfg, results_dir = build_sweep_project(tmp_path, n_units=240)
    assert main(["run", str(cfg)]) == EXIT_OK
    doc = yaml.safe_load((next(results_dir.glob("run_*")) / "run.yaml").read_text())

    blocks = [c["aggregated"]["step01_summarize_units"]["score"]
              for c in doc["results"]["conditions"]]
    values = [b["value"] for b in blocks]
    assert len(set(values)) == 3, f"conditions must differ, got {values}"
    assert blocks[0] is not blocks[1], "aggregated must not be a shared object"
    for b in blocks:
        assert b["basis"] == "units"
        assert b["correction"] is None, "an uncorrected interval must say so"
        assert b["n"]["resolved"] == 240


def test_sweep_yaml_records_the_resolved_plan(tmp_path: Path):
    root, cfg, results_dir = build_sweep_project(tmp_path, n_units=40)
    assert main(["run", str(cfg)]) == EXIT_OK
    sweep_doc = yaml.safe_load((next(results_dir.glob("run_*")) / "sweep.yaml").read_text())
    assert [c["label"] for c in sweep_doc["conditions"]] == [
        "baseline", "method=spearman", "method=kendall"]
    assert len(sweep_doc["repeats"]) == 5
    assert len(sweep_doc["order"]) == 15


def test_a_single_condition_run_is_unchanged(tmp_path: Path):
    """The regression risk of adding a level is that it appears where it should not."""
    root, cfg, results_dir = build_project_without_sweep(tmp_path, n_units=40)
    assert main(["run", str(cfg)]) == EXIT_OK
    run_dir = next(results_dir.glob("run_*"))
    assert not (run_dir / "conditions").exists()
```

Write `build_sweep_project(tmp_path, n_units)` and `build_project_without_sweep(tmp_path, n_units)` as module-level helpers. Both scaffold a project, write an `index.csv` of `n_units` rows, generate the experiment, fill `metadata`, and commit. The sweep variant adds `sweep: {baseline: {analysis.method: pearson}, grid: {analysis.method: [spearman, kendall]}}` and overwrites the starter step with one recording a numeric `score` whose value depends on `cfg.parameters.analysis.method`, so the three conditions genuinely differ.

- [ ] **Step 2: Run and watch them fail**

Run: `uv run pytest tests/test_acceptance.py -k sweep -v`
Expected: FAIL — one condition executes and there is no `conditions/` level.

- [ ] **Step 3: Wire `command_run`**

Replace the hardcoded expansion:

```python
    from publishable.sweep import expand, sweep_document

    conditions = expand(doc)
    swept_paths = set((doc.get("sweep") or {}).get("grid") or {})
    plan = build_plan(
        experiment,
        conditions=[(c.index, c.label) for c in conditions],
        repeat_labels=labels,
    )
    cfgs: dict[int, Config] = {
        c.index: resolve_condition_cfg(doc, c.values) for c in conditions
    }
    cfgs[-1] = resolve_wide_cfg(doc, swept_paths)
```

Write `sweep.yaml` inside the lock, next to `manifest/input.json`:

```python
        order = [(e.condition_index or 0, e.repeat_label or "")
                 for e in plan if e.scope == "repeat"]
        (run_dir / "sweep.yaml").write_text(
            yaml.safe_dump(sweep_document(conditions, repeats, digest, order), sort_keys=False)
        )
```

And aggregate per condition rather than only condition 0:

```python
        # Condition metadata the ExecutionResults cannot carry: `Execution` holds
        # index and label but not `is_baseline`, and the acceptance test asserts it.
        condition_meta = {c.index: {"label": c.label, "is_baseline": c.is_baseline}
                          for c in conditions}
        aggregated = {}
        if roster is not None:
            for cond in conditions:
                recording = {
                    r.execution.step_name for r in results
                    if r.execution.scope == "repeat"
                    and r.execution.condition_index == cond.index and r.rows
                }
                aggregated[cond.index] = {
                    name: summarize_step(
                        collapse_repeats(results, name, cond.index),
                        attrition(results, roster, name, cond.index),
                    )
                    for name in sorted(recording)
                }
```

`summarize_step` gains `"correction": None` on each metric — the config's default is `holm`, so a record that said nothing could be read as corrected.

`assemble_run_yaml` gains keyword-only `condition_meta: dict[int, dict[str, Any]] | None = None`, and `_results_block` writes each condition's `label` and `is_baseline` from it. `ExecutionResult` carries `condition_index` and `condition_label` but has no way to know which condition is the baseline, so the fact has to arrive alongside `aggregated` rather than be inferred. Pass `condition_meta=condition_meta`.

- [ ] **Step 4: Run the whole suite and the real journey**

Run: `uv run pytest -v && uv run ruff check . && uv run mypy`
Then run the CLI by hand: scaffold, generate, write an `index.csv`, add the sweep block, fill metadata, commit, `validate`, `run`. Read the produced `run.yaml` and `sweep.yaml` and paste both into your report. Confirm the three conditions report three different values.

- [ ] **Step 5: Retire and narrow the ledger entries**

```bash
cat >> docs/superpowers/spec-defects.md <<'EOF'

## RETIRED in S3a: `E-SWEEP-UNSUPPORTED`

`baseline` and `grid` now expand and execute. The four modes S3a does not implement are
refused individually, and the `sweep` block is back in the config `init` generates, narrowing
the "complete parameter set" entry to the `statistics` sub-keys alone.
EOF
git add src/publishable/cli.py tests/test_acceptance.py docs/superpowers/
git commit -m "Run every condition a sweep declares"
```

---

## Definition of done for S3a

- [ ] `uv run pytest` green, including all four acceptance tests.
- [ ] `uv run ruff check .` and `uv run mypy` clean.
- [ ] Every `E-`/`W-` identifier defined in `src/` has a test that produces it.
- [ ] `E-SWEEP-UNSUPPORTED` appears nowhere in `src/` or `tests/`.
- [ ] The four mode refusals each fire, and a generated config trips none of them.
- [ ] Three conditions produce three genuinely different values over one shared roster, and their `aggregated` blocks are not the same object.
- [ ] A run with no `sweep` block has no `conditions/` level — unchanged from S2.
- [ ] Each aggregated metric records `correction: null`.
