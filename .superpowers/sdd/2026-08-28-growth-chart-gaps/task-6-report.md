## Task 6+7 report

Status: complete.

Implemented `W-SWEEP-CONDITION-DUPLICATE` in `src/publishable/validate.py`
(`_warn_duplicate_conditions`, called from `_check_sweep`), over `expand`'s output via
`contrasts.differing_axes`, gated on neither condition carrying a `Condition.selectors`
(group axis) — since equal `values` implies equal units only for a parameter path, not
a `groups` level (assignment-method-dependent). Message reuses the working-spelling
remedy `W-SWEEP-BASELINE-CONFOUNDED` already emits, joined by semicolon (same
containment, not a fresh sentence). Added the row to `docs/reference.md` § Warnings
core reports, alphabetically after `W-SWEEP-BASELINE-CONFOUNDED`.

Mutation evidence (each: backed up file, mutated, ran red, restored from backup,
confirmed byte-identical + green):
- Removed selectors guard → `test_a_group_axis_duplicate_level_is_not_this_warning` and
  `test_a_baseline_fixing_a_group_level_is_not_this_warning_either` both failed (red),
  passed after restore.
- Inverted `differing_axes` polarity → `test_a_baseline_colliding_with_its_own_grid_cell_warns_once`,
  `test_a_normal_baseline_plus_grid_config_has_no_duplicate_condition`,
  `test_a_repeated_grid_value_is_the_soft_case_this_warning_reaches` all failed, passed after restore.
- Removed the early `return` (report-once) → `test_a_baseline_colliding_with_its_own_grid_cell_warns_once`
  failed on the pair-(0,2)-vs-(1,3) assertion (dict overwrite showed the later pair), passed after restore.

`uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy` all pass; full
`tests/test_validate.py` (800 tests) passes.

Concern: the measured example in the brief (baseline+grid, no groups) is the only
shape Decision 3 discusses explicitly; the group-axis exclusion (task 8's own
requirement) was derived from `E-SWEEP-LEVEL-DUPLICATE`'s giant comment about
assignment-method-dependent unit collision, not stated directly in Decision 3 — worth
a second look by task 8's author.
