# Task 7 report — close the branch

Status: complete.

**Whole-branch re-run** (uv run pytest -q): 3544 passed, 1 skipped, 2 xfailed (437.98s). Baseline
before this slice was 3531 passed / 1 skipped / 2 xfailed; the 13 additional passes are this slice's
new tests (Tasks 1-6).
- `uv run ruff check .`: All checks passed!
- `uv run ruff format --check .`: 101 files already formatted.
- `uv run mypy`: Success: no issues found in 56 source files.

**Oracle**, re-checked explicitly:
`tests/test_cli.py::test_task1_bit_stability_oracle_over_the_correction_machinery` — 1 passed.

**Consistency passes**, over README.md, docs/design-principles.md, docs/experimental-designs.md,
docs/reference.md:
- Mechanical (script-driven, GitHub slugger semantics, fences skipped): no broken relative links,
  no broken `#anchor`s (self or cross-file), no duplicate heading anchors, no table row/header
  column mismatches (unescaped-pipe count), no trailing whitespace/tabs/invisible unicode. Clean.
- Cross-document: read § Pre-registration, § What a hypothesis is tested against, § Statistical
  reporting, and the inline `compare` enum comment in § The one config file. All state the same two
  standing exceptions ("a metric with no raw interval at all" and "a recorded column carried under
  both `weight_by` and `cluster_by`") identically everywhere they appear; no stale "sole exception"
  language remains (Task 6 already swept that). design-principles.md, experimental-designs.md, and
  README.md carry no `to: constant`/`Member`/correctable-condition-metric claims, so nothing there
  needed reconciling. Clean.

**Fifteen configs** in `2026-08-28-gcl-measurement/` (`uv sync`, `tools/make_fixtures.py
../2026-08-28-gcl-measurement-data`, then `publishable validate` on each):
13 clean, `e05c-fixed-n` and `e08-ordering` each carrying exactly one `W-DATA-CLUSTER-UNDECLARED` —
matches the expected retracted-gap shape.

**E2 conclusion**: `configs/e02-utilization-baseline/config.yaml`'s `h1` is **unchanged and
unaffected** by this slice as literally written. It has no `compare` block at all — `metric:
step03_compare.auroc_count_only` names a `summary`-scope `Estimate` (`step03_compare.py`), so
`verdict_rests_on: reported`, always outside the correction family, both before and after this
slice. `step03_compare.py`'s own docstring still narrates the *pre-slice* reason for that routing
("core builds no correctable member for a condition's own value"), which this slice fixed — but the
config was not rewritten to exploit it. What **did** become true: if E2 declared
`compare: {to: constant, value: 0.5}` directly on the condition-scoped `auroc` the template's
`aggregate` already derives (derived, under E2's declared `statistics.resample` — Decision 1's third
row), that hypothesis would now get a real corrected bound instead of `supported: null`. This matches
what Task 6 already recorded in `feasibility-growth-chart-literacy.md` finding 2 (verified against
`docs/superpowers/specs/2026-08-28-correctable-condition-metric-design.md` Decision 1 table) — not a
new finding, and not a regression: E2's answerability is unchanged; its *rewritability* improved.

Appended a dated entry ("Re-checked on 2026-08-28 against commit `ae9677e`") to
`docs/feasibility-growth-chart-literacy.md` § Executability on this build, stating the above and that
the fixture re-validation reproduced the prior measurement's 13-clean/2-warning shape.

**Concerns**: none. No code changed in this task; only the report and the feasibility-doc append.
