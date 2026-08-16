# SDD ledger — plan: docs/superpowers/plans/2026-08-15-fixed-holdout.md

Slice H3d — a fixed holdout split. Branch `h3d-fixed-holdout`, forked from `78bb794` (main, post
H7a + H4a + the spec-defects audit). Baseline at fork: 1801 passed + 2 xfailed; ruff and mypy clean.
Spec: docs/superpowers/specs/2026-08-15-fixed-holdout-design.md (6 decisions + 6 appended corrections)
Measurement: docs/superpowers/H3d-SCOPING-2.md (2026-08-15, pinned to 78bb794) — REPLACES
  H3d-SCOPING.md, which was pinned to cb96c7d, FOUR SLICES BACK.
Execution: subagent-driven, WITHOUT standing merge authorization — STOP AND ASK before merge/push.

## Pre-flight scan

| Tasks | Shared | Finding |
|---|---|---|
| 2 -> 5,6,7,8,9 | the thirteen new `E-DATA-HOLDOUT-*` codes | Task 2 mints, 5-9 emit. Sequential. Task 2 also mints E-DATA-HOLDOUT-VARIES, which the scoping prescribed an entry for WITHOUT NAMING — controller-verified absent from src/ and reference.md |
| 5 -> 6,7 | `validate._check_holdout` | Task 5 CREATES it; 6 and 7 extend the same function. Same shape as H4a's _check_resample, which five tasks extended and whose COMMENTS carried five false claims read as instructions. Every dispatch must say the function already exists |
| 8, 16 | `validate.py`, separate check sites | Independent of _check_holdout. No conflict |
| 10,11,12 | `units.holdout_for` / seed | 10 builds unclustered, 11 clustered+strata, 12 the seed — and PER THE PLANNING CORRECTION `seed` is a REQUIRED KWARG holdout_for never derives, so 10/11 carry no forward reference to 12 |
| 13,15,17 | `cli.command_run` | 13 realizes once; 15 narrows six denominators; 17 writes allocation.json. Sequential |
| 1 -> 13,15,17,18 | `tests/test_cli.py` | Task 1's pin is the acceptance criterion for the wiring tasks, exactly as H4a's was |
| 2,4,8 | `spec-defects.md` | Three independent appends |
| 2 x 19 | `reference.md` NOT BUILT marker | CHECKED AND CLEAN: task 19 owns the marker and the count sentence; task 2's section contains ZERO "NOT BUILT" references. This is the H4a task-2/task-12 conflict I had to rule on there, and the plan avoided it unprompted |

Self-consistency per task: checked each task's tests against the code it specifies and the files it
creates against the files later tasks touch. **No conflict found requiring a ruling** — unusual, and
attributable to the plan author having been given H4a's fourteen brief defects as explicit rules.

Two plan properties worth recording because they are H4a lessons applied without being asked:
  - the "alongside, not instead of" rule appears FOUR times — every Part A test asserts its new
    finding beside E-DATA-HOLDOUT-UNSUPPORTED, so task 18's retirement is a one-line deletion
    rather than a rewrite of eight tasks' tests;
  - task 19's prose sweep carries a MUTATION PROVING THE SWEEP CAN FAIL (reintroduce a known
    sentence, confirm the grep returns it). Three H4a sweeps stopped one file short and none was
    mutation-tested.

## Task log

Task 1: implemented, commit 889de01 (tests only). 1803 passed + 2 xfailed (baseline 1801 + 2); ruff and
  mypy clean. Both required mutations (runner.execute_plan's no-fold branch, attrition's no-fold branch)
  confirmed FAIL then reverted in place with git diff empty afterward.
  THREE BRIEF DEFECTS, AND ONE WOULD HAVE MADE THE PIN VACUOUS:
  (1) executions.jsonl records carry NO `n` field at all — the brief's "n.resolved in executions.jsonl"
  corresponds to nothing this build writes; the real denominator lives only in run.yaml's aggregated
  block via _condition_counts.
  (2) THE VACUITY: the default one-step scaffold's aggregated block is EMPTY —
  {"step01_summarize_units": {}} — because it records a bool column stats.summarize_step drops outright.
  The brief's `assert aggregated` guard WOULD HAVE PASSED WHILE THE PIN'S INNER LOOP NEVER RAN. Fixed
  with aggregate_returns="mean_pred". This is the "control asserting only an absence" class wearing a
  new coat: the guard was truthy, the iteration was empty.
  (3) a single always-failing step yields run status "failed", not "partial", since run_status requires
  at least one completed execution; fixed by adding an always-completing second step.
  BASE for task 2 is 889de01.
Task 1 review: spec ✅, quality 1 CRITICAL + 2 Important + 1 Minor. All three brief defects verified
  independently, including the vacuity — the reviewer dumped the fixture and confirmed
  aggregated == {"step01_summarize_units": {}}, so `assert aggregated` passes while the loop iterates
  ZERO times.
  CRITICAL — THREE OF THE SIX NARROWING SITES MOVE WITH THE WHOLE SUITE GREEN. Mutating
  _condition_beside_n, _compute_vs_baseline(roster=) and the units_hash call each to
  UnitList(list(roster)[:3]) leaves 1803 passed / 2 xfailed. NO TEST IN THIS REPO CAN SEE THEM CHANGE.
  Two are exactly what the spec singles out (units_hash "must stay whole-roster"; _condition_beside_n is
  the filed technical_n gap). Unreachable for a FIXTURE reason, not a code reason — no measurements, no
  vs_baseline with `within`. Ruled: CLOSE THEM IN TASK 1. The plan routes end-to-end coverage to task 18,
  which lands AFTER the narrowing and therefore cannot be a baseline for it.
  IMPORTANT — THE PIN COVERS 1 OF 6. The units=roster -> execute_plan site is EXECUTED by the fixture and
  still missed: under mutation `value` 4.5 -> 1.0, `completed` 10 -> 3, `failed` 0 -> 7, BOTH ci95s move,
  and the run still exits EXIT_OK because _units_failed_anywhere is scoped to the same narrowed list so
  max_failed_fraction: 0.2 never fires on 7/10 — AND BOTH TESTS PASS, because the pin asserts
  n["resolved"] alone. Same shape as the previous slice's pin, which is why this one was promoted to
  first.
  IMPORTANT: units_hash pinned as a SHAPE (startswith("sha256:")) on one of the two values task 15 must
  not touch. A shape assertion survives any change to the thing it names. Ruled: recompute and compare,
  not a literal digest.
CARRY FORWARD (task 1 Minor, shapes tasks 14-17): executions.jsonl carries NO `n` field, so ALL OF TASK
  15'S DENOMINATORS ARE run.yaml-SIDE. Any test of a narrowing that looks for it in the ledger is
  looking in the wrong artifact.
