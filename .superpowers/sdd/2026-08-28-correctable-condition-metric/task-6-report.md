# Task 6 report

**Status:** complete.

**What changed.** `src/publishable/hypotheses.py`'s `corrected_unavailable` `elif` branch (line
414) needed no logic change: Task 5's `cli.py` member-building already made `key not in by_key`
true only for the two genuinely-nothing-to-correct cases, since the branch is reached only when the
`if corrected is not None` arm above it did not fire. Rewrote the branch's comment, which still
described the pre-Task-5 world ("core builds one for every `vs_baseline`/contrast comparison but
none for a constant reference"), to name the two residual cases: a metric with no raw interval at
all, and a recorded column carried under both `weight_by` and `cluster_by` (no paired construction
of that shape, no `Member` field for both modifiers, `Member.__post_init__` refuses one that
carries both).

**Documents corrected.**
- `docs/superpowers/spec-defects.md`: amended (not removed) the `{to: constant}` entry — title and
  body narrowed to the weighted+clustered residual, with an "AMENDED" section explaining the three
  closed rows and why the fourth stays open. The brief's "stays open for the `t` case" was stale per
  the controller's ruling; corrected as instructed.
- `docs/superpowers/specs/2026-08-28-correctable-condition-metric-design.md`: appended an
  amendment to Decision 5 naming the Holm-rank-shift exception ("nothing else may move" now has one
  named exception) and why it's kept — the family already counted the constant hypothesis, Task 5
  only gave it a rank to sort into.
- `docs/reference.md` § Pre-registration / § What a hypothesis is tested against: fixed four stale
  passages (and one example comment) claiming core builds no `Member` for a constant-referenced
  hypothesis at all; each now names the weighted+clustered combination as the sole exception.
- `docs/feasibility-growth-chart-literacy.md`: corrected finding #2 (E2 declares neither `weight_by`
  nor `cluster_by`, so its `{to: constant}` claim on `auroc` is no longer limited) and finding #7
  for internal consistency, both without touching § Executability.

**Mutation evidence** (both run against production code, reverted, diffed clean after):
1. Forced the `elif` to never fire (`... and False`) → `test_a_condition_metric_with_no_raw_interval_still_gets_no_member` and `test_a_weighted_clustered_condition_metric_gets_no_member` FAILED (2 failed, 3 passed); the three "now correctable" tests stayed green.
2. Disabled `cli.py`'s `condition_members.append(...)` (`if False:` guard, simulating pre-Task-5) → `test_an_unresampled_condition_metric_corrects_off_its_own_per_unit_values`, `test_a_resampled_condition_metric_corrects_off_its_own_draw_pool`, `test_a_derived_condition_metric_corrects_off_its_own_draw_pool` FAILED (3 failed, 2 passed); the two residual tests stayed green.

Both reverts verified byte-identical via `diff` against a pre-mutation backup, then full 5/5 green.

**Verification:** the 5 relevant end-to-end tests pass; `test_task1_bit_stability_oracle_over_the_correction_machinery` passes with its golden literal untouched; `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy` all clean.

**Concerns:** none — no behavior changed beyond the comment; no run declaring no constant hypothesis is affected.
