# Task 1 report: the regression pin — a run with no holdout

**Status:** Complete. No `src/` file touched (constraint honoured — `git diff src/publishable/runner.py` is empty after both mutation/revert cycles).

**Files changed:** `tests/test_cli.py` only — appended `_TRAIN_TOUCHING_STEP` and the two tests named in the brief's Interfaces section: `test_a_run_without_a_holdout_pins_its_denominators_and_artifacts` and `test_io_units_train_raises_without_a_fold_or_holdout`.

## What the pin asserts (final form)

- `run.yaml`'s `config.data.units.holdout` is `null` (materialize.py's explicit-null shape).
- Every `executions.jsonl` record has `status: "completed"` (ledger is non-vacuous: `assert ledger`).
- `run.yaml`'s aggregated block reports `n.resolved == 10` for both the recorded column (`pred`) and the template-derived metric (`mean_pred`) — the actual task 15 denominator surface.
- `provenance.units.n == 10`, `provenance.units.key == "patient_id"`, `provenance.units_hash` starts with `sha256:` — the roster identity task 15 must leave whole.
- No `allocation.json`, and `provenance.allocation` / `provenance.allocation_hash` are both `None`.
- A step reaching `io.units.train` with no `fold` and no `holdout` raises `E-STEP-UNITS-UNAVAILABLE`, contained per-execution; paired with a second step (`extra_steps=["control"]`) that always completes, so the run is genuinely `partial` (5 failed + 5 completed), not accidentally all-failed.

## Three real disagreements between the brief and the code (all found by running Step 2 before touching anything, per the brief's own instruction to "fix the assertion to what the run actually produces")

1. **`executions.jsonl` has no `"n"` key at all.** `runner.execute_plan`'s ledger write (`src/publishable/runner.py` around line 655–670) writes exactly `step`/`scope`/`condition`/`repeat`/`status`/`started_at`/`wall_seconds`/`error`. There is no other write site to that file. The brief's line "the four things tasks 14–17 are most likely to move... `n.resolved` in `executions.jsonl`" does not correspond to any field this build ever writes there — the real per-metric denominator (`_condition_counts`'s `n`) lives only in `run.yaml`'s aggregated block. I replaced the ledger `n.resolved` assertion with a plain `status == "completed"` check and moved the denominator pin to where the field genuinely exists.

2. **The default scaffold's one auto-generated step produces an empty `aggregated` block.** `run_a_project(tmp_path, units=10)` with no overrides records `{"present": True}` per unit; `stats.summarize_step` drops any column whose values are bools ("skipped entirely... a string, or a bool") outright. So `run["results"]["conditions"][0]["aggregated"]` is `{"step01_summarize_units": {}}` — truthy at the top level (the brief's `assert aggregated` guard would have passed) but empty exactly where the pin's inner loop needs to iterate, so the whole "aggregated" half of the original test body was vacuous — the loop body never ran, silently. Fixed by passing `aggregate_returns="mean_pred"`, the same helper every other end-to-end test in this file already uses to get a real `basis: units` metric with a real `n`.

3. **A single always-failing step makes the run `"failed"` (`EXIT_FAILED`=4), not `"partial"` (`EXIT_PARTIAL`=3).** `run_record.run_status` returns `"partial"` only when *some* execution completed; with only `_TRAIN_TOUCHING_STEP` in the pipeline and every one of its 5 repeats raising, none complete, so the run is wholly `"failed"`. The brief's docstring ("the plan runs to its end and `run_status` turns it into `partial`") does not hold for the single-step scaffold. Fixed by adding `extra_steps=["control"]` (the generated no-op step, always completes), which makes the run genuinely mixed — the shape `run_status` actually calls `partial`.

All three are documented inline in the tests' docstrings/comments as well, so a reader hits the explanation at the point of the assertion, not only here.

## Verification

- `uv run pytest tests/test_cli.py -k "without_a_holdout or units_train_raises" -q` → 2 passed.
- `uv run pytest -q` → **1803 passed, 2 xfailed** (baseline 1801 + these 2 new tests; nothing else moved).
- `uv run ruff check .` → All checks passed.
- `uv run mypy` → Success: no issues found in 42 source files.
- Mutation (a) — `execute_plan`'s no-fold branch changed to `step_units = UnitList(list(scoped_units or []), train=scoped_units)`: `test_io_units_train_raises_without_a_fold_or_holdout` **FAILED** (`main(...)` returned `EXIT_OK`=0, not `EXIT_PARTIAL`=3, because the train-touching step no longer raises). Reverted by editing in place; re-ran, passes. `git diff src/publishable/runner.py` empty afterward.
- Mutation (b) — `attrition`'s no-fold branch changed to `handed = set(sorted(keys)[:3])`: `test_a_run_without_a_holdout_pins_its_denominators_and_artifacts` **FAILED** on `aggregated[name]["n"]["resolved"] == 10` (got `3`). Reverted by editing in place; re-ran, passes. `git diff src/publishable/runner.py` empty afterward.
- `__pycache__` cleared between each mutation and its revert; every revert verified by re-running the test (behaviour), not by `git status`.

## Concerns / carry-forward for later tasks

- The brief's premise about `executions.jsonl` carrying a per-execution `n.resolved` is not just imprecise but flatly absent from the ledger schema this build writes. If a later task (15, or its own pin at task 18) intends to add such a field to the ledger itself, that would be new ledger schema work, not a narrowing of an existing field — worth flagging explicitly if it comes up, since nothing in this commit's `runner.py` suggests that was ever planned.
- `test_io_units_train_raises_without_a_fold_or_holdout` now depends on `extra_steps=["control"]` producing a step literally named `step02_control` with source `return {{}}` — if a later task changes what "the run is genuinely partial" needs (e.g. changes step ordering or the generated no-op step's shape), this test's `step02_control`/count-of-5 assertions are the ones to revisit.
- No holdout-related code was touched or exercised beyond what already exists (`UnitList.train`, `E-STEP-UNITS-UNAVAILABLE`) — `E-DATA-HOLDOUT-UNSUPPORTED` was never reached because neither fixture declares `data.units.holdout`.
