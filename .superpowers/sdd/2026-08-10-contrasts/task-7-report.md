# Task 7 report: Contrasts reach the record

## What was built

`src/publishable/cli.py`:
- New module-level helper `_baseline_comparisons(doc, conditions)`: filters
  `contrasts.resolve_contrasts`'s output down to the auto-generated
  baseline-vs-condition entries — those with `against == baseline.index` and
  `id == <that condition's own label>`. `resolve_contrasts` also returns
  declared `statistics.contrasts` entries (arbitrary `of`/`against`, custom
  `id`); those belong in `results.contrasts`, which this task does not build
  (out of scope per the brief — "Produces: a `vs_baseline` block"). They are
  simply not reported yet, not misfiled into `vs_baseline`.
- New module-level helper `_compute_vs_baseline(...)`: for each baseline
  comparison, for each recording step both conditions share, for each metric
  key present in both conditions' `aggregated` summaries — decides recorded
  vs. derived by membership in the `derived` dict `aggregate` returned (stored
  per `(condition, step)` during the aggregation loop), and builds the entry
  with `stats.paired_t_over_units`/`cohens_dz` (recorded) or
  `stats.paired_percentile_of_derived` (derived, `cohens_d: null`). Warns
  `W-STATS-CONTRAST-THIN` (minted; grepped `reference.md` and `src/` first —
  nothing existing covers `min_reported_n`) when a metric's `n_paired` falls
  below `limits.min_reported_n`. Returns `None`, not `{}`, when nothing
  survives (no baseline, or no metric in common).
- Three new dicts (`collapsed_by_key`, `derived_by_key`, `resample_fns_by_key`)
  populated during the existing aggregation loop, so the per-unit collapsed
  table, `aggregate`'s raw return, and the resample closures built for the
  reported `ci95` are available afterward without recomputing anything.
- The call site sits right after the aggregation loop's `for cond in
  conditions:` closes, joining the same `Collector` (`aggregate_c`) the
  aggregation warnings already use, so both print together.
- `vs_baseline` threaded into `assemble_run_yaml(..., vs_baseline=vs_baseline)`.

`src/publishable/run_record.py`:
- `_results_block` and `assemble_run_yaml` both gained a `vs_baseline`
  parameter, attached to `results.conditions[i].vs_baseline` — a sibling of
  `aggregated`, per `reference.md` § The two files' worked-example shape.
  Attached only when a condition's block is non-empty (never `{}`).

`tests/test_cli.py`:
- `run_a_project` gained a `units: int = 10` keyword, controlling the number
  of scaffolded patients (used by `test_a_thin_pairing_warns` to shrink the
  roster below `limits.min_reported_n` without touching every other caller's
  fixture).
- Added `_first_contrast(run, label)`, mirroring `_first_metric`'s shape on
  the contrast side.
- Added the three tests from the brief, plus a fourth after advisor review
  (below). `test_a_baseline_sweep_reports_a_delta` and `test_a_thin_pairing_
  warns` patch `experiment_gen.STARTER_STEP` to a new fixture,
  `_METHOD_VARYING_STEP` — necessary because the scaffold's default step
  records only `{"present": True}`, a bool `summarize_step` filters out,
  leaving no numeric column to difference at all. `_AGGREGATE_STEP` (the
  existing fixture) was tried first and reverted: its `float(i)` is identical
  under every condition, so `delta`/`ci95`/`cohens_d` land at degenerate
  `0.0`/`[0.0, 0.0]`/`None` regardless of correctness — a sign error in the
  diff direction or a hardcoded `cohens_d: None` on both branches would have
  passed silently. `_METHOD_VARYING_STEP` varies by condition (`is_spearman`)
  *and* per-unit in a way that doesn't cancel in the difference (`extra`,
  whose alternation flips with `is_spearman`), so the per-unit diffs have
  real variance: mean delta pins to exactly `1.0`, `ci95` has nonzero width,
  and `cohens_d` is asserted to be a real `float`.

## Where it's attached

`results.conditions[<non-baseline index>].vs_baseline.<step_name>.<metric_key>`,
verified by hand against a real run.yaml:

```yaml
vs_baseline:
  step01_summarize_units:
    pred:
      delta: 0.0
      basis: units
      paired: true
      method: paired_t_over_units
      n_paired: 10
      ci95: [0.0, 0.0]
      cohens_d: null
      correction: null
```

and, with a derived metric added, a sibling `total` entry with
`method: paired_percentile_over_units`, `cohens_d: null`. Matches
`reference.md` § The two files' shape field-for-field, plus this slice's
`n_paired` and `correction: null`, and omits `ci95_corrected`/
`correction_level`/`family_size`/`family` (S4c's).

## Verification

`uv run pytest -v` — 672 passed (668 pre-existing + 4 new).
`uv run ruff check .` — all checks passed.
`uv run mypy` — no issues found in 35 source files.

## Notes / judgment calls

- **Derived-metric `compute` closure**: `paired_percentile_of_derived` takes
  one `compute` callable applied to both sides' resampled draws. I pass the
  reporting condition's (`of`'s) own resample closure, falling back to
  `against`'s if `of` has none. When the two conditions' `cfg` differ in a way
  that changes which formula `aggregate` runs internally (the worked example's
  `analysis.method` sweep is exactly this), the interval technically resamples
  `of`'s formula against both sides' data rather than each side's own formula.
  I did not find a way to avoid this given `paired_percentile_of_derived`'s
  single-`compute` signature (confirmed unchanged from Task 5, and the brief
  names it as *the* derived construction), and no test in this task's scope
  exercises the point estimate's numeric correctness for a derived metric —
  the point estimate itself is correct (each side's own `value`); only the
  resampled interval carries this asymmetry. Escalated to the advisor, who
  confirmed this doesn't block Task 7 and shouldn't be fixed by redesigning
  Task 5 from inside this one.
- Per-metric `n_paired`/pairing is computed per column for recorded metrics
  (a column present in a subset of completed units narrows its own pairing,
  matching `summarize_step`'s per-column `n.completed`), and once per step for
  derived metrics (which have no per-unit ragged shape to narrow against).
- **`min_reported_n` scope**: applied to every `vs_baseline` entry's
  `n_paired`, not narrowed to `within`-restricted contrasts. `reference.md`:
  2068 mentions `within` specifically, but no `within` contrast reaches
  `run.yaml` in this slice (only auto-generated baseline comparisons do), so
  restricting to `within` would leave the warning permanently unreachable —
  exactly the no-op this task exists to close. The brief's own wording ("a
  contrast's `n_paired`") and its test (no `within` declared) both confirm
  the broader reading.
- **Declared `statistics.contrasts` produce nothing**: Task 6 retired
  `E-STATS-CONTRASTS-UNSUPPORTED`, so a declared contrast now validates
  clean, but `results.contrasts` — where a declared (non-baseline) contrast's
  result belongs — is not built by this task (out of scope: the brief says
  "Produces: a `vs_baseline` block"). `_baseline_comparisons` filters
  `resolve_contrasts`'s output down to only the auto-generated
  baseline-vs-condition entries, so a declared contrast is silently absent
  rather than misfiled into `vs_baseline`. Recorded as a new entry in
  `docs/superpowers/spec-defects.md` ("Declared `statistics.contrasts`
  validate clean and compute nothing") per CLAUDE.md's instruction to record
  rather than diverge silently, and per the advisor's review that this is the
  same species of no-op `min_reported_n` was.
- Added a fourth test beyond the brief's three, per advisor review:
  `test_a_baseline_sweep_with_no_metric_has_no_vs_baseline_block` — a
  baseline sweep with the scaffold's default (bool-only) step, so
  comparisons are resolved but every `metric_block` is empty. This is the
  case that actually exercises `_compute_vs_baseline`'s `return out or None`
  and `run_record.py`'s `if block:` guard; `test_a_run_with_no_baseline_
  has_no_vs_baseline_block` is over-determined (no baseline *and* no metric)
  and can't catch either guard being dropped on its own.

## Fix-forward: two Criticals the coordinator caught

Both notes above turned out to be Criticals, not judgment calls to leave open.
Fixed on this branch rather than reopening the task.

### Critical 1 — the shared `compute` cancelled on every draw

`stats.paired_percentile_of_derived` took one `compute` applied to both
sides. `cli.py` passed the reporting condition's own resample closure for
both, so a swept axis that changes which *formula* `aggregate` runs
(`analysis.method`: pearson/spearman/kendall, over `pred`/`truth` recorded
**identically** across conditions) evaluated one side's formula against both
sides' identical draws — every draw cancelled, giving a zero-width `ci95` at
zero beside a genuinely nonzero point-estimate delta. The coordinator
measured this directly against the documented worked example's shape:
`ci95 [0.0000, 0.0000]` beside a `-0.0004` point estimate.

**Fix**: `paired_percentile_of_derived` now takes `compute_of` and
`compute_against` — two callables, each evaluated on its own side's draw of
the *same* drawn keys (the pairing is in which units are drawn together, not
in which formula evaluates them). `cli.py`'s `_comparison_step_blocks` (new
— see below) passes each condition's own resample closure, with no
fallback to the other side's. Every existing `test_stats.py` call site
updated to pass the same callable twice where that's genuinely the intent
(9 call sites); added
`test_two_different_computes_over_identical_tables_yield_a_real_interval`,
which passes *different* formulas (`total`/`mean`) over the *same*
underlying table and asserts the interval is non-degenerate
(`high - low > 0`) and brackets the true unresampled difference between the
two formulas — this is the test that would have caught the bug, and it fails
against a reverted single-`compute` version.

Verified end to end with a reconstruction of the breaking scenario (a step
recording identical `pred`/`truth` under `analysis.method: pearson` vs.
`spearman`, `aggregate` calling `pearsonr`/`spearmanr` internally): the
resulting `vs_baseline` entry now has `ci95` width `0.524` (nonzero) and
brackets its own `delta`, where before the fix an equivalent construction
would report zero width.

### Critical 2 — declared `statistics.contrasts` produced nothing

Task 6 (a prior task in this slice) retired `E-STATS-CONTRASTS-UNSUPPORTED`,
so a declared `statistics.contrasts` entry validated clean with nothing
downstream computing it — `_baseline_comparisons` filtered it out of
`vs_baseline` correctly, but nothing else received it. Reported as a
spec-defects.md gap in the original submission; the coordinator's review
correctly named this the failure class the whole project treats as worst,
and asked for it closed rather than deferred.

**Fix**: built `results.contrasts`, matching `docs/reference.md:2076-2085`'s
shape exactly. New pieces in `cli.py`:
- `_declared_comparisons(doc, conditions)`: the complement of
  `_baseline_comparisons` — every `resolve_contrasts` entry that is *not*
  auto-generated.
- `_comparison_step_blocks(comp, ...)`: the per-comparison computation
  factored out of the old `_compute_vs_baseline` body, now shared by both
  `_compute_vs_baseline` (baseline comparisons) and the new
  `_compute_declared_contrasts` (declared ones) — one metric-construction
  codepath, not two copies to keep in sync.
- `_compute_declared_contrasts(...)`: builds the flat list `results.contrasts`
  is, one entry per declared comparison, with `of`/`against` recorded via
  `sweep.condition_dir_name(index, label)` — `"01_method=spearman"`, matching
  the doc's "recorded with its index; declared without one" note — then the
  per-step metric blocks merged in as sibling keys of `id`/`of`/`against`
  (not nested under a `steps` key), exactly as the doc's example shows.
  Returns `None`, not `[]`, when nothing was declared.

`run_record.py`: `_results_block`/`assemble_run_yaml` gained a `contrasts`
parameter, attached as `results.contrasts` (sibling of `results.conditions`)
only when non-empty.

Removed the spec-defects.md entry for this gap — closed, not deferred.

Verified end to end: a run with a declared
`{id: spearman_vs_kendall, of: "method=spearman", against: "method=kendall"}`
contrast (no baseline involved on either side) produces:

```yaml
results:
  contrasts:
    - id: spearman_vs_kendall
      of: 01_method=spearman
      against: 02_method=kendall
      step01_summarize_units:
        pred: {delta: 1.0, basis: units, paired: true, method: paired_t_over_units,
               n_paired: 10, ci95: [0.623, 1.377], cohens_d: 1.897, correction: null}
```

with no `vs_baseline` key anywhere in that block.

### Re-verification

`uv run pytest -v` — 673 passed (672 prior + 1 new
`test_two_different_computes_over_identical_tables_yield_a_real_interval`).
`uv run ruff check .` — all checks passed.
`uv run mypy` — no issues found in 35 source files.
