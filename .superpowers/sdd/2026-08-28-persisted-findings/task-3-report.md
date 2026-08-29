# Task 3 report — `run_record` assembles the block

## Status
Complete. Commit: (see below, filled after commit)

## What was built
- `run_record.assemble_run_yaml` gains `findings: list[dict[str, str]] | None = None`. Emits
  `findings:` as the LAST top-level key, only when non-empty (`if findings: out["findings"] = findings`).
  No sorting, filtering, or re-derivation — the list is used exactly as handed in.
- `cli.py`'s one production call site (phase 9, ~line 5330) now passes `findings=findings`, the same
  accumulator `_prepare_run`/`_execute_prepared` fill via `_disclose` at all 12 render sites (task 2).
  A disclosure added to that list AFTER this call (`W-APPARATUS-UNANSWERED`, which fires once
  `run.yaml` already exists) is, by construction, never in the record — verified against
  `test_g1_ordering_chain_appends_before_the_gate_fires_end_to_end`, which pins exactly two disclosed
  findings (`W-ENV-UNLOCKED`, `E-APPARATUS-CHANGED`) on a STOP path with `status: failed`, confirming a
  record CAN be written beside an error (Decision 2).

## Tests added (tests/test_run_record.py)
- `test_findings_are_recorded_in_order_with_all_four_fields` — two entries, one warning one error,
  order preserved, all four `Diagnostic` fields present.
- `test_a_clean_run_has_no_findings_key_at_all` — absent, not `[]`, for both the omitted argument and
  an explicit `[]`. Mutation: `run_record.py`'s final block changed to
  `out["findings"] = findings if findings is not None else []` (unconditional emission). Backed up
  with `cp` first. `uv run pytest -q tests/test_run_record.py::test_a_clean_run_has_no_findings_key_at_all`
  went from PASS to `AssertionError: assert 'findings' not in {...}` (1 failed). Restored via `cp` from
  the backup; re-ran green (1 passed), confirming revert by behaviour.
- `test_findings_survive_a_yaml_round_trip` — `yaml.safe_dump` → `yaml.safe_load` reproduces the same
  list of plain dicts.

## The oracle (absorbed task 5)
`test_task1_bit_stability_oracle_over_the_correction_machinery`'s fixture (no `uv.lock`, `units=40`
clears `min_reported_n`) discloses exactly one finding — `W-ENV-UNLOCKED` — before phase 9. The literal
MOVED: four new leaves (`findings.0.code`, `findings.0.level`, `findings.0.message`,
`findings.0.path`), inserted in sorted position between the last `execution.*` leaf and
`layout.conditions`. Nothing above `execution.*` or at/after `layout.conditions` moved; no numeric
value changed. Read the diff (not regenerated blindly) — confirmed via `-v` diff output before editing.

## Other tests updated (grep swept `tests/` for run-record key-list/shape pins, per the ledger note)
Several OTHER pre-existing tests pin `run.yaml`'s whole top-level key list or a full leaf-by-leaf
literal, and each fixture that lacks a `uv.lock` (every test project) now legitimately grows a
`findings` entry once `W-ENV-UNLOCKED` (or, for `units < 10`, `W-STATS-COLUMN-THIN` too) is disclosed.
Updated, each with a comment explaining the new entries and why (all findings verified by inspection
of actual run output before editing the literal, never guessed):
- `test_a_clean_run_completes_with_the_full_run_yaml_shape` — `findings` (2 entries: `W-ENV-UNLOCKED`,
  `W-STATS-COLUMN-THIN`, units=8).
- `test_h8a_arm_a_a_clean_run_top_level_shape_status_and_exit` — same 2 entries (units=8).
- `test_h8b_arm_c_the_records_key_lists_status_and_exit` — 3 entries (`W-ENV-UNLOCKED` + one
  `W-STATS-COLUMN-THIN` per of 2 conditions). This arm's docstring said "sole authorized editor NONE"
  for its own slice (H8b); edited here as a different, later slice legitimately adding a new optional
  block (Decision 2), documented as such rather than silently overwritten.
- `test_g1_ordering_chain_appends_before_the_gate_fires_end_to_end` — 2 entries
  (`W-ENV-UNLOCKED` warning, `E-APPARATUS-CHANGED` error) on the STOP/failed path.
- `test_h9a_arm_a_a_completed_runs_whole_run_yaml_leaf_by_leaf` — 1 entry (`W-ENV-UNLOCKED`,
  `units=20` clears the column-thin threshold).
- `_H9B_ARM_A_GOLDEN` (shared module constant, consumed by `test_h9b_arm_a_the_straight_through_golden`,
  `test_h9b_arm_a_crash_and_resume_equals_straight_through`,
  `test_h9b_a_crash_and_resume_round_trip_equals_the_straight_through_golden`, and
  `test_h9b_the_run_path_is_untouched_by_the_resumed_parameter`) — 1 entry (`W-ENV-UNLOCKED`). One edit
  fixed all four consuming tests.
- `test_a_condition_scoped_step_returning_a_metric_warns` — its old
  `assert "accuracy" not in run.yaml.read_text()` broke because `W-STEP-RETURN-DISCARDED`'s own message
  legitimately names `accuracy` and now reaches the record. Narrowed to
  `assert "accuracy" not in yaml.safe_dump(run["results"])` (the actual property under test — the
  discarded value never reaches `results`) and added a positive assertion that the finding IS recorded.

Every finding's content was captured by actually running the fixture (throwaway debug scripts, deleted
after use) before writing the literal — never guessed from the message text.

## Gate results
- `uv run pytest -q`: 3563 passed, 1 skipped, 2 xfailed (baseline 3560 passed + 3 new tests; 0
  regressions).
- `uv run ruff check .`: All checks passed!
- `uv run ruff format --check .`: 101 files already formatted
- `uv run mypy`: Success: no issues found in 56 source files

## Disagreement with the brief
None. The brief's oracle section anticipated exactly this ("determine it first... if it does, the
literal gains a findings block"), and the wider set of key-list-pinning tests that also broke is
exactly what the brief's "Ledger note from Task 1" discipline point told me to grep for and fix — not
a disagreement, an expected consequence of the same design decision applied consistently.

## Review fixes (post-PASS, three findings)

1. **MEDIUM — stale comment, second home.** `cli.py` ~5178's "Neither substitutes for the
   other — run-time findings are not written to the record at all" was falsified by this same
   commit (`aggregate_c`'s `W-HYPOTHESIS-UNEVALUABLE` now reaches `run.yaml` via `_disclose`).
   Rewrote to justify the field-plus-warning split on the two readers/two shapes it still is
   (structured, hypothesis-keyed field vs. a human-readable sentence for whoever is watching the
   run), not on findings never reaching the record. Swept the whole tree for the same claim:
   `grep -rn "not written to the record\|never reach(es)? the record\|no diagnostics channel\|
   findings.*never reach\|warnings.*never reach\|not.*written to.*run\.yaml\|screen only"
   --include='*.py' --include='*.md' .` Two more LIVE, non-record homes found and fixed:
   `src/publishable/hypotheses.py` (a pure `evaluate`/`_tested_number` comment — kept the true half,
   "no `Collector` reaches this pure function," dropped the now-false "`run.yaml` has nowhere to
   carry a finding") and a test-fixture template's own comment in `tests/test_cli.py`
   (`_AGGREGATE_LEAKING_TEMPLATE`, describing `W-STATS-AGGREGATE-FAILED`, which is disclosed through
   `aggregate_c` the same way). Remaining hits are in `docs/reference.md` (normative — Task 6 "the
   documents"), `docs/feasibility-growth-chart-literacy.md` and `docs/superpowers/spec-defects.md`
   (dated analysis / live gap list — also Task 6's), and inside `docs/superpowers/plans/*.md` and
   `.superpowers/sdd/*/progress.md`/`task-*-report.md` (development record — never retro-edited per
   `CLAUDE.md`). Left untouched, out of this task's scope.
2. **LOW — no end-to-end absent-when-empty witness.** Added
   `test_persisted_findings_task3_a_real_uv_lock_leaves_no_findings_key` in `tests/test_cli.py`,
   reusing `_h6a_pin_project`'s real hand-written `uv.lock` fixture (the only one in the suite) for a
   genuine `main(["run", ...])` whose `run.yaml` has no `findings` key at all. Mutation (same as
   before, `out["findings"] = findings if findings is not None else []`, `cp` backup first): PASS →
   `AssertionError: assert 'findings' not in {...}` (1 failed); reverted via `cp`, re-ran →
   1 passed.
3. **LOW — over-narrowed scope.** `test_a_condition_scoped_step_returning_a_metric_warns`'s raw-text
   check now excludes only `findings` —
   `yaml.safe_dump({k: v for k, v in run.items() if k != "findings"})` — restoring `execution` and
   `layout` to the scanned text instead of the earlier `results`-only narrowing.

Gate: `uv run pytest -q` → 3564 passed, 1 skipped, 2 xfailed (3563 + 1 new). `ruff check .`: All
checks passed. `ruff format --check .`: 101 files already formatted (one reformat applied to
`tests/test_cli.py` mid-fix, then re-verified). `uv run mypy`: Success, 56 source files.
