# Task 5 report: the step path collapses, and `measurements.parquet`

**Status:** DONE

**Commits:**
- `eef7ff7` — "feat: collapse a step's measurements under the same rule the input takes"
- `a76f0e7` — "test: pin mean against median on the input path, so the shared rule is checkable"

**Test summary:** `uv run pytest` — 1148 passed, 2 xfailed; `uv run ruff check .` — all checks passed;
`uv run mypy` — no issues (40 source files). `ruff format` was not run.

## What was done

**`src/publishable/artifacts.py`**

- `StepIO._collapse_measurements()` — new. Groups `_measurement_rows` by unit key (insertion order,
  so `first` means "earliest recorded", mirroring `collapse_measurements`' resolution order), unions
  each group's column names in first-seen order minus the structural `unit`/`measurement`, and for
  each column calls `rule_for` → `coerce_for_rule` → `apply_rule` — the same three calls
  `units.collapse_measurements` makes. Writes the result into **both** `_rows` and `_recorded_keys`.
  A column absent from a member contributes no value rather than a `None`, matching
  `collapse_measurements`' absent-skip; a `None` would be refused outright by a numeric rule.
- `finalize` calls it **before** the existing `if self._rows:` block, so a collapsed unit flows
  through the path a plain recorded one already takes — which is also how it gets the
  declared-attribute merge for free rather than through a second, drift-prone table.
- `measurements.parquet` is written after `units.parquet`, guarded on `if self._measurement_rows:`
  — never on `self._measurements`, since an input-path run carries that declaration in every
  execution. The existing `_encode_parquet` already unions columns across ragged rows and fills
  absent ones with `None`, so no separate normalization was needed; pinned by a test rather than
  assumed.
- The mixture is **refused** in both directions (obligation 3, below).

**`src/publishable/units.py`, `validate.py`, tests, `docs/superpowers/spec-defects.md`** — `_apply`
renamed to `apply_rule` (it now has a caller outside its module), every reference updated including
docstrings and comments. Dated plan files under `docs/superpowers/plans/` were left alone: they are
records of what was planned, not descriptions of current code.

**`src/publishable/runner.py` / `cli.py`** — `execute_plan` gained `measurements: dict | None = None`,
passed into the single `StepIO(...)` construction (`grep` confirms it is the only one in `src/`).
`cli.py` passes `(units_decl or {}).get("measurements")`.

**`docs/reference.md` § What isn't a repeat** — the normative sentence, beside task 4's
"core raises if a step passes `measurement=` while … is undeclared": core raises too if one unit
arrives by both paths in one execution, in either order, because the collapsed row and the plain row
are the same row — while a *second measurement* of that unit is the one thing `measurement=` exists
to allow. Task 4's precedent is that the rule lives here and § Errors core raises is the raise-time
index; this task follows it.

**`docs/reference.md` § Errors core raises** — the `E-STEP-UNIT-SETTLED` row now covers "a unit
measured with `measurement=` counts as settled for both, in either order … while a second
measurement of it is what the argument is for". That one row closes both this task's refusal and
task 4's skip-direction half, which shipped without a doc note. Mechanical pass run over the file:
no trailing whitespace or tabs outside fences, table row column counts unchanged, no new links or
anchors introduced.

## The central obligation: a measured unit counts as `completed`

Confirmed at HEAD before the change, then closed. Pinned at two levels:

- `test_a_measured_only_unit_is_completed_not_failed` (`tests/test_artifacts.py`) — `recorded_keys`
  holds the measured unit and the plain control after `finalize`.
- `test_attrition_reconciles_for_a_step_that_only_measures` (`tests/test_runner.py`) — a **real
  step** through `execute_plan`, 4 units, 3 measured twice each, 1 skipped:
  `{"resolved": 4, "completed": 3, "ineligible": 1, "failed": 0}`, and the four-part identity
  asserted explicitly. `attrition`'s signature was read before calling it, and the harness runs one
  repeat-scoped step so the intersection across repeats does not mask the count.

`finalize()` is called by the runner immediately before it reads `io.recorded_keys`/`io.rows()`, so
collapsing inside `finalize` is genuinely on the accounting path — verified in `runner.py`'s
execution loop, not assumed.

## Obligation 3: I refuse the mixture, and the reason is this task's own code

Task 4's recommendation is **adopted**, with a stronger reason than the symmetry argument it gave:
the collapse writes its result to `self._rows[unit_key]`. Refusing is what makes that assignment
provably collision-free. Defining a winner instead would mean `finalize` deciding whether a
collapsed row overwrites a plain one — and the declared `collapse` rule would then apply or not
depending on which call the step happened to make first, which is the retry-versus-measurement
ambiguity `measurement=` exists to remove, reappearing one layer down. Both directions:

- measure-after-plain: the measurement branch now raises `E-STEP-UNIT-SETTLED` on
  `unit_key in self._rows`.
- plain-after-measure: the plain branch calls the existing `_check_unmeasured` (task 4's helper,
  previously called only by `skip`), placed after `_settle`. The plain branch's
  `if unit_key in self._rows: return` first-write-wins cannot mask it, because a measured-only unit
  is not in `_rows`.

The measurement branch's comment — which said `_settle`'s `_rows` half "must not apply here" — was
**false** once that check landed, and has been rewritten: a second measurement is fine because
measurement rows never reach `_rows`; `_rows` membership means a *plain* row. `_check_unmeasured`'s
docstring, which named only `skip` as its caller, was rewritten too.

## Coercion: `coerce_scalars` does **not** settle it

`coerce_scalars` guarantees a scalar (`str`/`int`/`float`/`bool`/`None`), not a *number*. A step
recording `{"score": "10"}` under `collapse: mean` reaches the collapse as a `str`, where
`apply_rule`'s constant-column shortcut would hand back the string `"10"` for a constant column and
`sum` would raise a bare `TypeError` otherwise — exactly the case `is_measurement_numeric`'s
docstring calls load-bearing. `coerce_for_rule` is therefore called before `apply_rule` on this path
too, and pinned by `test_a_numeric_rule_coerces_a_recorded_string_before_applying` (`"10"`/`"20"` →
`15.0`).

## The decision-4 correction, restated for the spec

Confirmed as the brief states it: the two paths cannot call one collapse *function*, because
`collapse_measurements` takes and returns `Unit`s while this path holds and produces rows. What is
shared is the **rule application** — `rule_for`, `coerce_for_rule`, `apply_rule`, all three, not just
the last. Decision 4's reason is untouched and is what the mutation test below demonstrates
empirically.

## Mutation tests

All six applied, run, confirmed FAIL, reverted, `__pycache__` deleted, and every revert verified by
re-running the tests — never by `git status`. Every probe carries a control that must report.

| # | Mutation | Failed | Control that stayed passing |
|---|---|---|---|
| 1 | Step path averages with hand-written `sum/len` instead of `apply_rule` | *(nothing — expected: the rules agree today)* | — |
| 1b | …then `apply_rule`'s `mean` branch → `median`, both mutations live | input path only (`test_mean_over_three_measurements_is_a_mean_and_not_a_median`) | step path's collapse test **passed** — the divergence |
| 1c | Step path restored to `apply_rule`, `median` mutation still live | **both** paths' tests | — (this is the proof the shared call binds them) |
| 2 | Collapse stops adding to `_recorded_keys` | `test_a_measured_only_unit_is_completed_not_failed`, `test_attrition_reconciles_for_a_step_that_only_measures` | `test_attrition_reconciles_exactly` (plain path) |
| 3 | `measurements.parquet` guarded on `self._measurements` | `test_no_measurements_parquet_when_no_step_measured` | `test_measurements_parquet_holds_the_uncollapsed_rows` |
| 4 | Measurement branch drops the `_rows` refusal | `test_measuring_a_plain_recorded_unit_is_settled` | `test_a_second_measurement_of_an_unskipped_unit_is_not_settled` |
| 5 | Plain branch drops `_check_unmeasured` | `test_plain_recording_a_measured_unit_is_settled` | `test_a_different_unit_may_be_plain_recorded_alongside_a_measured_one` |
| 6 | `runner.py` stops passing `measurements=` | `test_a_real_step_may_measure_when_the_config_declares_measurements` | `test_a_step_that_only_measures_is_refused_without_the_declaration` |

**Row 1 is the one the brief got wrong, and it would have reported a false pass.** The brief's own
step-5 values are 10 and 20, and `statistics.median([10.0, 20.0])` is `15.0` — identical to the
mean — so the prescribed `mean → median` mutation is invisible at those values. Worse, *no*
input-path test distinguished `mean` from `median` either: every existing `mean` case collapses two
symmetric values. So the "only the input path's test fails" half would have reported nothing at all.
Fixed by using three asymmetric values (10/20/60 → mean 30, median 20) on the step path, and by
adding `test_mean_over_three_measurements_is_a_mean_and_not_a_median` on the input path — a genuine
coverage gap, closed in its own commit. With those in place the divergence is visible exactly as
decision 4 predicts, and 1c shows the shared call is what removes it.

## Two things checked because the refusal could have broken them

- **Resume is unaffected.** `grep -rn "resumed\|_rows\[\|_recorded_keys" src/publishable/` outside
  `artifacts.py` returns only prose in comments — nothing anywhere preloads `_rows` or
  `_recorded_keys` from an existing `units.parquet`, and `StepIO.resumed` is set `False` in
  `__init__` and never set again in this build. So the new `unit_key in self._rows` refusal cannot
  turn a resumed measuring step into a raise; resumed-measurement idempotency stays where task 4 put
  it, on `(unit, measurement)` first-write-wins.
- **`execute_plan` has exactly one call site.** `grep -rn "execute_plan(" src/` returns its
  definition in `runner.py` and the single call in `cli.py` — `draft`/`resume` do not call it
  separately in this build, so threading it once is threading it everywhere. Worth re-checking when
  a second executing command lands, since mutation 6 cannot see a call site that does not exist yet.

## Concerns

- **Row order in `units.parquet`.** A collapsed unit lands after every plain-recorded one, whatever
  order the step recorded them in, because the collapse runs at `finalize`. No document pins row
  order and every reader keys by unit, so this is behaviour rather than a defect — it is asserted in
  `test_a_different_unit_may_be_plain_recorded_alongside_a_measured_one` rather than left to be
  discovered. It only arises for a step that both measures some units and plain-records others,
  which the mixture refusal now confines to *different* units.
- **`E-DATA-MEASUREMENTS-UNSUPPORTED` is untouched**, so the step path is reachable only through
  `execute_plan` today, not through `publishable run` on a validating config. That is task 6's
  retirement, and the runner test deliberately goes through `execute_plan` for that reason.
- `data.units.measurements` is threaded as the declaration dict rather than being re-read from the
  config inside `StepIO`, so a future caller of `execute_plan` that forgets the argument reopens
  exactly the gap mutation 6 pins. The gap is now covered by a test; there is no type-level guard.
- The brief's `read_parquet`/`step_io` were shorthand, as warned. Local helpers `_read_parquet`
  (wrapping `artifacts._decode_parquet`) and `_measuring_io` were added to `tests/test_artifacts.py`;
  `tests/test_runner.py`'s existing `harness(...)` gained `measurements=None`, leaving every current
  caller unchanged.
- No document sentence settled the mixture question, consistent with task 4's finding. The refusal is
  a design decision made here and now recorded in `reference.md` § What isn't a repeat (the rule) and
  § Errors core raises (the identifier), so a later reader meets it as a rule rather than as
  unexplained code.
- **Inherited, not introduced: `E-DATA-MEASUREMENTS-COLLAPSE-TYPE` outside `validate`.**
  `reference.md` describes it only in § Validation (row 410), as a check against the resolved
  roster, and there is no § Errors core raises row for it. Task 3 already made it raisable at run
  time by wiring `coerce_for_rule` into `resolve_units`, which `run` calls; this task extends the
  same code to a step-recorded value at `finalize`. Naming it rather than fixing it here — the
  raise-time documentation of that code is one row that belongs to whoever closes it deliberately.
- **Inherited: nothing carries the step path's measurement counts.** The collapse knows how many
  measurements each unit had, and `technical_n` has no route to a metric — the same parked plumbing
  `cli.py`'s phase-5 comment describes for the input path. The step path is not special here.
