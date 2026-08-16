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

## Review fix round (this commit)

Closed the review's Important findings, and investigated the Critical one far enough to change its
disposition rather than paper over it. No `src/` change survives this round — every mutation below
was applied, run, and reverted in place; `git diff src/publishable/cli.py` is empty and byte-identical
to a pre-round backup after every cycle.

**Important — `n` pinned on one of its four keys, and the site it executes (`units=roster` →
`execute_plan`) unasserted.** Fixed together: the pin now asserts the full `n` dict
(`resolved`/`completed`/`ineligible`/`failed`) and `value`/`ci95` on both `pred` and `mean_pred`, not
`resolved` alone. Verified discriminating: mutating `execute_plan`'s `units=roster` argument to
`UnitList(list(roster)[:3])` now **fails** the pin on exactly the numbers the review named —
`completed`: 10→3, `failed`: 0→7 — reverted in place, re-passes. (`pred` and `mean_pred` are the same
number by construction here, both being a mean over the same recorded column — one mutation-detector,
not two independent checks, worth naming plainly rather than double-counting.)

**Important — `units_hash` pinned as a shape, not a value.** Fixed: the pin now recomputes the hash
over the same input directory via `publishable.units.resolve_units` + `units_hash` and asserts
equality, not `.startswith("sha256:")`. Verified: mutating the `units_hash(roster)` call to
`units_hash(UnitList(list(roster)[:3]))` now **fails** on the digest mismatch; reverted, re-passes.

**Minor — the ledger-has-no-`n` consequence.** Stated positively in this test's own docstring already
(committed at `889de01`): task 15's denominators are all `run.yaml`-side, never the ledger.

**Critical — re-investigated rather than "closed with a fixture," and the review's own remedy does
not exist as a reachable config for two of the three sites.**

Traced each of the three named sites to ground truth (direct function calls, a dataclass field
default, and CLI-level mutation-plus-whole-suite runs — the same method the review itself used),
rather than accepting "cheap fixture addition" at face value:

- **`_condition_beside_n`'s `roster` argument (the call at `cli.py`'s `command_run`,
  `_condition_beside_n(beside_n, roster, cond.index, arm_members_map)`) is provably invariant to
  narrowing, in both branches, not merely untested.** `_cond_beside_n`'s only decision is
  `cond_roster is roster` (identity). `_cond_roster` returns `roster` unchanged when
  `arm_members_map is None` — so a mutated (narrowed) `roster` is still identical to itself, and the
  check trivially holds regardless of size. When `arm_members_map` is not `None`, `_cond_roster`
  always constructs a **new** `UnitList` — so the check is always `False`, again regardless of size.
  Confirmed directly:
  ```
  _condition_beside_n(beside_n, roster, 0, None)          == _condition_beside_n(beside_n, UnitList(list(roster)[:3]), 0, None)
  _condition_beside_n(beside_n, roster, 0, arm_members_map) == _condition_beside_n(beside_n, UnitList(list(roster)[:3]), 0, arm_members_map)
  ```
  both hold, byte for byte, for a synthetic 10-unit roster. Confirmed again at the CLI call site: the
  literal source mutation `_condition_beside_n(beside_n, UnitList(list(roster)[:3]), cond.index,
  arm_members_map)` leaves the **whole suite** at `1803 passed, 2 xfailed` — not because no fixture
  reaches it, but because no fixture *can*: the parameter has no effect on any code path this build
  has. Reverted; whole suite re-passes; `git diff` empty.

- **`_compute_vs_baseline`'s `roster=` argument reaches exactly one expression,
  `units_matching(roster, comp.within)`, and `comp.within` is `None` for every comparison that can
  ever reach this function.** `_baseline_comparisons` filters `resolve_contrasts`'s output to
  `not comp.declared`; every `declared=False` `Comparison` is built by `resolve_contrasts`'s own
  baseline loop, which never passes a `within=` kwarg, so it takes the dataclass default —
  confirmed `None` via `dataclasses.fields(Comparison)`. So `units_matching(roster, None)` returns
  `None` unconditionally, `roster`'s content is never read again, and the review's own remedy —
  "needs a `vs_baseline` comparison with `within`" — describes a config this code cannot produce: a
  `within` only ever arrives through a **declared** `statistics.contrasts` entry, and a declared entry
  always routes to `_compute_declared_contrasts`, not here. Confirmed at the CLI call site the same
  way: mutating `roster=UnitList(list(roster)[:3])` at the `_compute_vs_baseline` call leaves the
  whole suite at `1803 passed, 2 xfailed`. Reverted; re-passes; `git diff` empty.

  Both are genuinely dead parameters in the current build — not a coverage gap this task can close,
  because no fixture can make a dead parameter's value observable. That is a different fact from "the
  fixture is expensive," and the distinction matters for what happens next: task 14 is what makes
  `_condition_beside_n`'s `roster` argument live (by giving `arm_members_map`/roster narrowing new
  content to disagree over), and task 15 is what makes `_compute_vs_baseline`'s `roster` argument
  live (by being the point a holdout's test partition could reach it). **The obligation to pin each
  one moves to the task that makes it live, not to a general "file it" note** — recorded here so
  neither reads as closed and neither reads as unowned:
  - **Task 14 must add a pin for `_condition_beside_n`'s `roster` argument once holdout narrowing
    exists**, at the point a holdout's test partition first reaches this call.
  - **Task 15 must add a pin for `_compute_vs_baseline`'s `roster` argument once holdout narrowing
    reaches it**, at the point `_compute_vs_baseline` first receives a narrowed roster.

**Verification that the review's other two "caught (whole suite)" claims still hold, re-checked
rather than taken on trust** (the one part of the review this round had not independently run):

- `_condition_report_by_levels(roster, cond.index, arm_members_map, attribute)`: mutated to
  `UnitList(list(roster)[:3])` → **11 named tests fail**, including
  `test_a_reporting_stratum_repeats_the_metric_over_its_own_units` and
  `test_a_derived_metric_is_stratified_with_its_own_resample`. Reverted; whole suite re-passes.
- `_compute_declared_contrasts(roster=...)`: mutated the same way → **3 named tests fail**, including
  `test_a_stratified_derived_delta_is_computed_over_its_own_intersection` (`n_paired`: 20→1).
  Reverted; whole suite re-passes.

**Skipped, and why:** the three non-narrowing sites (`weights`, `unit_attributes`, `resample_strata`)
were conditioned in the review on "if reaching them is cheap once you have the `measurements`
fixture" — a fixture whose only justification in this task was `_condition_beside_n`, now shown
inert. Building a `measurements` fixture to pin these three would be defensive work the surviving
premise doesn't call for; `test_n_gains_effective_under_a_weighted_design` and
`test_a_declared_stratify_by_reaches_the_column_interval` already exercise those paths elsewhere in
the suite.

**Final verification:** `uv run pytest -q` → 1803 passed, 2 xfailed (test count unchanged — this
round strengthened assertions, added none). `uv run ruff check .` → all checks passed. `uv run mypy`
→ success, 42 source files. `git diff --stat src/` empty throughout.
