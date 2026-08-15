# Task 8 report: wire the CLI, and the acceptance test

## Status

Done. `uv run pytest` (405 passed), `uv run ruff check .`, and `uv run mypy` are all
clean. Commit: `104b018` on `s3a-sweeps-and-conditions` — "Run every condition a sweep
declares".

## What changed

- **`src/publishable/cli.py`** — `command_run` now calls `sweep.expand(doc)` to get the
  real condition list, builds `plan` from `[(c.index, c.label) for c in conditions]`
  instead of the hardcoded `[(0, None)]`, and builds `cfgs` from
  `resolve_condition_cfg`/`resolve_wide_cfg` instead of `{0: Config(doc), -1: Config(doc)}`.
  Writes `sweep.yaml` inside the run lock, next to `manifest/input.json`. Aggregation
  loops over every condition (not just `0`), each with its own `attrition`/
  `collapse_repeats` call scoped by `cond.index`. Builds `condition_meta` (`label`,
  `is_baseline` per index) and passes it to `assemble_run_yaml`.
- **`src/publishable/runner.py`** — `execute_plan` derives `conditions_list` (unique
  `(index, label)` pairs with a real label — empty when there's no sweep),
  `repeats_list`, and `step_scopes` from the plan and resolved repeats, and threads them
  into `StepIO(scope=execution.scope, conditions=..., repeats=..., step_scopes=...)`.
  This is what makes `io.conditions`/`io.repeats`/`io.read_condition` work in a real run
  — previously `StepIO` was constructed with none of those, so the whole Task 7 read
  surface was unreachable outside its own unit tests.
- **`src/publishable/stats.py`** — `summarize_step` now emits `"correction": None` on
  every metric explicitly, so a record can't be misread as corrected when the config's
  default is `statistics.correction: holm`.
- **`src/publishable/run_record.py`** — `_results_block`/`assemble_run_yaml` gained a
  keyword-only `condition_meta: dict[int, dict[str, Any]] | None`, since `Execution`
  carries `index`/`label` but not `is_baseline`.
- **`src/publishable/materialize.py`** — `init`-generated configs now include a `sweep:
  {}` block (literally empty — zero keys) plus commented `baseline`/`grid` guidance,
  restoring `sweep` to what the "complete parameter set" header claims. Verified this
  doesn't reintroduce the zero-condition risk (see gap below).
- **`tests/test_acceptance.py`** — added `build_sweep_project`/
  `build_project_without_sweep`/`write_sweep_step` helpers and 6 new tests: the four
  from the brief (tree shape, per-condition numbers, `sweep.yaml` contents, unchanged
  single-condition run) plus two I added to satisfy the brief's explicit ask to *prove*
  the two carry-forwards through a real `run`, not only via unit tests:
  `test_a_summary_step_reading_a_swept_parameter_is_refused_in_a_real_run` and
  `test_a_summary_step_reads_every_condition_in_a_real_run`.

## The three carry-forwards

1. **`E-STEP-SWEPT-PARAM`** — proven end-to-end: a generated `step02_check_swept`
   summary step reads `cfg.parameters.analysis.method` (a swept path) in a real
   `main(["run", ...])` call; the run finishes `status: partial`, and
   `run.yaml["execution"]["summary"]["step02_check_swept"]["error"]` contains
   `E-STEP-SWEPT-PARAM`.
2. **The Task 7 read surface** — proven end-to-end: a generated `step02_compare_conditions`
   summary step iterates `io.conditions` and calls `io.read_condition(...)` to read back
   each condition's own `step01_summarize_units` output; the run completes and
   `run.yaml["results"]["summary"]["step02_compare_conditions"]` equals
   `{"baseline": 1.0, "method=spearman": 2.0, "method=kendall": 3.0}`.
3. **The shared `doc` object** — no longer an issue: `cfgs` is now built from
   `resolve_condition_cfg`/`resolve_wide_cfg`, both of which `copy.deepcopy(base)`
   internally, so every condition's `Config` (and the wide one) wraps its own
   independent dict. Confirmed via the acceptance test's
   `assert blocks[0] is not blocks[1]`.

## Manual CLI journey (scaffold → generate → run)

Ran the full journey by hand against a fresh scratch project (40-unit roster,
`sweep: {baseline: {analysis.method: pearson}, grid: {analysis.method: [spearman,
kendall]}}`, a step recording `score` = 1.0/2.0/3.0 by method). `validate` printed
`W-STATS-FAMILY` (3 conditions → family of 2 comparisons); `run` completed with
`status: completed`, produced `conditions/00_baseline/`, `01_method=spearman/`,
`02_method=kendall/`, each with 5 `seed*/` dirs, and `sweep.yaml`/`run.yaml` matching
exactly what the acceptance test checks. Condensed `run.yaml["results"]` and
`sweep.yaml`:

```yaml
# sweep.yaml
design_digest: sha256:05175f50da061b6c5c1c7a321d1fa28bf4d09409816d5cb7461d850c5f52f3f7
conditions:
- {index: 0, label: baseline, values: {analysis.method: pearson}, is_baseline: true}
- {index: 1, label: method=spearman, values: {analysis.method: spearman}, is_baseline: false}
- {index: 2, label: method=kendall, values: {analysis.method: kendall}, is_baseline: false}
repeats:
- {kind: seed, seeds: [1823117535, 2155741529, 3570529064, 2943013590, 135328984]}
labels: [seed35, seed29, seed64, seed90, seed84]
order: as_declared
execution_order:  # 15 entries, 5 per condition
- {condition: 0, repeat: seed35}
# ... (15 total)
```

```yaml
# run.yaml (results block, condensed)
results:
  conditions:
  - index: 0
    label: baseline
    is_baseline: true
    aggregated:
      step01_summarize_units:
        score: {value: 1.0, basis: units, n: {resolved: 40, completed: 40, ineligible: 0, failed: 0},
                ci95: [1.0, 1.0], method: t_over_units, correction: null}
  - index: 1
    label: method=spearman
    is_baseline: false
    aggregated:
      step01_summarize_units:
        score: {value: 2.0, ..., correction: null}
  - index: 2
    label: method=kendall
    is_baseline: false
    aggregated:
      step01_summarize_units:
        score: {value: 3.0, ..., correction: null}
layout: {conditions: true, repeats: true}
status: completed
```

Three conditions, three genuinely different values (1.0 / 2.0 / 3.0), each with its own
attrition (`n.resolved: 40` etc.) and `correction: null`.

## Ledger entries (`docs/superpowers/spec-defects.md`)

Note: `docs/superpowers/` is `.gitignore`d in this repo (never tracked in git history),
so these edits are local documentation only, not part of the commit.

- **Retired `E-SWEEP-UNSUPPORTED`**, per the brief's exact text.
- **Narrowed** "The generated config calls itself 'the complete parameter set' before it
  is one" to say `sweep` is now restored (S3a) and only `statistics.contrasts`/
  `resample`/`null_test`/`report_by` remain (S4).
- **New gap found while doing this task**: `sweep.expand`'s guard
  (`sweep = config.get("sweep") or {}; if not sweep: return [...]`) checks the block's
  *presence*, not whether it declares anything that actually varies. A hand-written
  `sweep: {groups: [], paired: [], ablate: null}` is a non-empty dict (guard doesn't
  fire) but every key is falsy, so `expand` returns `[]` — zero conditions, nothing
  executed, `status: completed`. This is exactly the "declares a sweep, runs nothing,
  reports success" failure `E-SWEEP-AXIS-EMPTY` exists to catch for one empty `grid`
  axis, reachable here without tripping it. `materialize_config`'s new `sweep: {}` is
  written as a *literally* empty dict specifically to stay clear of this, but nothing in
  `validate.py` stops a hand-edited config from reintroducing it. Proposed resolution
  recorded in the ledger: `if sweep and not conditions: c.error(...)` in `_check_sweep`,
  after computing `conditions = expand(doc)`.

## Test results

```
uv run pytest -q          → 405 passed
uv run ruff check .       → All checks passed!
uv run mypy               → Success: no issues found in 33 source files
```

(`uv run ruff format --check .` reports 28 files would be reformatted — pre-existing
across the repo, not introduced by this change, and not part of this task's Definition
of Done, which names `ruff check`/`mypy` only.)
