# Task 8 report: the acceptance test

## What was done

Added two acceptance tests to `tests/test_cli.py`, right after `test_a_thin_pairing_warns`:

- `test_a_paired_delta_is_narrower_than_the_conditions_it_compares`
- `test_the_delta_half_width_is_not_implausibly_narrow`

Both drive `main(["run", ...])` end to end via `run_a_project`, reusing the existing
`_METHOD_VARYING_STEP` fixture (monkeypatched onto `STARTER_STEP`, matching
`test_a_baseline_sweep_reports_a_delta`'s existing pattern) so the per-unit values
genuinely differ by condition rather than passing degenerately.

Also added one small helper, `_first_metric_width(run, condition_index)`, mirroring
`_first_contrast`'s shape: it walks `results.conditions[condition_index].aggregated`
and returns the `ci95` width of the first numeric metric found. Needed because no
existing helper exposed a *width* rather than a whole metric block.

## src/ changes

None. Every interface needed by these tests — `vs_baseline`, `results.contrasts`,
`_first_contrast`, `_METHOD_VARYING_STEP`, `run_a_project`'s `sweep`/`units` kwargs —
was already wired and reachable from `main(["run", ...])`. This is the good outcome
the task brief asked to check for; unlike two earlier slices, nothing here was built
and left unreachable.

## Verification

`uv run pytest -q` → 675 passed (673 pre-existing + 2 new).
`uv run ruff check .` → All checks passed.
`uv run mypy` → Success: no issues found in 35 source files.

## Hand run (outside the repo)

Scaffolded a project via `generate_experiment` + `main(["new", ...])` +
`main(["run", ...])` directly (no `--help`/flags, per the paths-only invariant),
with a baseline (`pearson`) and one grid condition (`spearman`), 120 units, using the
same per-unit-varying step as the acceptance tests. `run.yaml`:

```yaml
# baseline condition, aggregated.step01_summarize_units.pred
value: 59.75
ci95: [53.461519708686794, 66.0384802913132]   # width ≈ 12.577

# method=spearman condition, aggregated.step01_summarize_units.pred
value: 60.75
ci95: [54.46282969504761, 67.0371703049524]    # width ≈ 12.574

# method=spearman condition, vs_baseline.step01_summarize_units.pred
delta: 1.0
paired: true
method: paired_t_over_units
n_paired: 120
ci95: [0.9092422709643089, 1.0907577290356911]  # width ≈ 0.181
cohens_d: 1.9916492328386208
correction: null
```

The paired delta's interval (width ≈0.181) is about 70× narrower than either
condition's own interval (width ≈12.57–12.58) over the same 120 units — the
`allocation: within` narrowing `CLAUDE.md` calls out, reproduced by hand rather
than only asserted by a test.

`git status` in the scratch directory's parent repo (`/Users/joon/src/tries/publishable`)
was confirmed clean of stray scaffold directories before committing — the scaffold
lived entirely under the session scratchpad, outside the repository.
