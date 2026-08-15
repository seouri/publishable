# Task 4 report: `io.record` gains `measurement=`

**Status:** DONE

**Commits:** `ab6fb2e` — "feat: io.record takes a measurement, and refuses one with no rule"; `a3d8aa2` — fix round 1; fix-round-2 commit (below).

**Test summary:** `uv run pytest` — 1133 passed, 2 xfailed; `uv run ruff check .` — all checks passed; `uv run mypy` — no issues (40 source files).

## What was done (original pass)

- `src/publishable/artifacts.py`: `StepIO.__init__` gained keyword-only `measurements: dict[str, Any] | None = None` (the `data.units.measurements` declaration itself, stored as `self._measurements`), plus `self._measurement_rows: dict[tuple[str, str], dict[str, Any]] = {}`. `record` gained `measurement: str | None = None`; it raises `ContractError` · `E-STEP-MEASUREMENT-UNDECLARED` when `measurement=` is given but `self._measurements` is falsy, otherwise stores a row keyed by `(unit_key, measurement)`, first-write-wins, under the same `coerce_scalars` every other recorded value goes through. Added `measurement_rows()`, mirroring `rows()`.
- `docs/reference.md` § Errors core raises: added the row for `E-STEP-MEASUREMENT-UNDECLARED`, confirmed raise-time placement (not the validate-time table).
- Did **not** touch `runner.py`, `partition_units`, or any `-UNSUPPORTED` code, per the brief's scope.

## Fix round 1: coordinator's two Important findings

Both were real gaps in the measurement branch of `record`, reproduced and then fixed.

**IMPORTANT 1 — measurement path bypassed `_settle` entirely.** Decomposed `_settle` into `_check_roster` (the `E-STEP-UNIT-UNKNOWN` roster-membership check) and `_settle` itself (roster check + the `_rows`/`_skipped` settled check, unchanged for the plain path). The measurement branch now calls `_check_roster` unconditionally, then checks only `unit_key in self._skipped` (raising `E-STEP-UNIT-SETTLED`) — never `unit_key in self._rows`, since a second measurement of one unit is the feature's whole point. This gives the measurement path exactly "one and a half" of `_settle`'s checks, composed rather than duplicated.

**IMPORTANT 2 — measurement path never checked declared attributes.** Added the same `self._declared_attributes() & values.keys()` collision check (raising `E-STEP-KEY-COLLISION` naming the shadowed attribute) to the measurement branch, matching the plain path.

Both fixes live in `record`'s `measurement is not None` branch in `src/publishable/artifacts.py`.

New tests in `tests/test_artifacts.py`, each with the control the coordinator asked for:
- `test_measuring_a_key_not_in_the_roster_is_refused` (raises `E-STEP-UNIT-UNKNOWN`) — control is the existing plain-path `test_recording_a_key_not_in_the_roster_is_refused`.
- `test_measuring_a_skipped_unit_is_settled` (raises `E-STEP-UNIT-SETTLED`) paired with `test_a_second_measurement_of_an_unskipped_unit_is_not_settled` (must NOT raise) — each is the other's control, per the coordinator's stated distinction.
- `test_a_measurement_column_matching_a_declared_attribute_is_a_key_collision` (raises `E-STEP-KEY-COLLISION`, then a non-colliding call on the same unit succeeds) — control is the existing plain-path `test_recording_a_column_matching_a_declared_attribute_is_a_key_collision`.

## Mutation tests, round 1 (each fix mutated and reverted separately)

1. **Roster check** — commented out `self._check_roster(unit_key)` in the measurement branch. `test_measuring_a_key_not_in_the_roster_is_refused` FAILED (`DID NOT RAISE`); `test_a_second_measurement_of_an_unskipped_unit_is_not_settled` (control) PASSED. Reverted, deleted every `__pycache__`, reran — both passed.
2. **Skip-settled check** — removed the `if unit_key in self._skipped: raise ...` block from the measurement branch. `test_measuring_a_skipped_unit_is_settled` FAILED (`DID NOT RAISE`); `test_a_second_measurement_of_an_unskipped_unit_is_not_settled` (control) PASSED. Reverted, deleted every `__pycache__`, reran — both passed.
3. **Declared-attribute collision check** — removed the `collision = self._declared_attributes() & values.keys()` block from the measurement branch. `test_a_measurement_column_matching_a_declared_attribute_is_a_key_collision` FAILED (`DID NOT RAISE`); the plain-path control `test_recording_a_column_matching_a_declared_attribute_is_a_key_collision` PASSED. Reverted, deleted every `__pycache__`, reran — both passed.

Every revert was verified by rerunning the test (behaviour), never by `git status`.

## MINOR 3 — restating the `measurement` type claim

The original report said `measurement` "must be a plain `str`." That was an unenforced aspiration, not actual behaviour: `measurement=5` is silently accepted and keyed unchanged, exactly as `unit_key` itself is never type-checked. Per the coordinator's instruction, I am **not** inventing a new coercion or type-check for this round — no sentence in `reference.md` requires one, and adding one now would be an invented rule. Restating precisely: **`measurement` is documented and used as a string in every example, but is not enforced to be one — consistent with `unit_key`'s existing laxness, not a gap this task introduces.**

## Upheld findings (no change made)

- Reserving `unit`/`measurement` as structural column names is textually supported: `reference.md` names `measurements.parquet`'s columns as exactly `(unit, measurement)`. Correcting my earlier report, which undersold this as "my inference" — it is a direct reading of that row.
- `E-STEP-MEASUREMENT-UNDECLARED`'s placement in § Errors core raises only (no validate-time dual listing) is correct: `validate` never constructs a `StepIO` or calls `.record`, so there is no validate-time path that can reach this code.

## Fix round 2: the mirror ordering

The coordinator's round-1 instruction named one direction (measuring a skipped unit must raise). The scoped re-review found the other direction was still open: `skip()` called `_settle`, which checks only `self._rows`/`self._skipped`, never `self._measurement_rows` — so a unit could be measured, then skipped, ending up in both `measurement_rows()` and `_skipped`. That is the same accounting failure finding 1 was written to prevent, reachable from the other call order.

**The full rule, stated once, in both places it's enforced:** a unit may be measured many times, but never both measured and skipped, in either order. `record(measurement=...)` enforces the `skip`-then-measure direction (checking `self._skipped`); `skip` now enforces the measure-then-skip direction via a new `_check_unmeasured` helper (checking `self._measurement_rows`), raising `E-STEP-UNIT-SETTLED`. Both docstrings/comments now state the one-sentence rule so a reader doesn't have to derive it from two guards in two methods — see `_check_unmeasured`'s docstring and the updated comment in `record`'s measurement branch, both in `src/publishable/artifacts.py`.

New tests in `tests/test_artifacts.py`:
- `test_skipping_a_measured_unit_is_settled` — `record(..., measurement="r1")` then `skip(...)` raises `E-STEP-UNIT-SETTLED`, and `io.skipped` stays empty.
- `test_skipping_an_unmeasured_unit_still_succeeds` — control: an unmeasured unit is still skippable, proving the new check doesn't block the ordinary case.

**Mutation test, round 2:** commented out the `self._check_unmeasured(unit_key)` call in `skip`. `test_skipping_a_measured_unit_is_settled` FAILED (`DID NOT RAISE`); the control `test_skipping_an_unmeasured_unit_still_succeeds` PASSED. Reverted, deleted every `__pycache__`, reran — both passed, confirming the revert by behaviour.

## Recorded for task 5: mixing plain `record` and `measurement=` on one unit

Not a defect against this fix — the re-review confirmed it's out of scope and explained by the stated rule (`_rows`-membership must not block a measurement, by design). But it is a real ambiguity task 5 will meet: `record("p1", {...})` then `record("p1", {...}, measurement="r1")` (or the reverse order) leaves `p1` in both `self._rows` and `measurement_rows()`, with no raise either way.

**My view: refuse the mixture, symmetric with the measured/skipped rule just added, rather than defining a winner.** Reasoning:
- `reference.md` § What isn't a repeat frames `measurement=` as *how a unit gets measured* when "the pipeline does the measuring rather than the input carrying it" — it describes one arrival path or the other for a given unit's technical replication, not a per-unit choice made twice under two different mechanisms in the same execution.
- Task 5 collapses `measurement_rows()` into a unit row per the declared `collapse` rule (`mean`/`median`/`sum`/`first`/`mode`). A plain `record()` row was never subject to that rule. Defining a "winner" (e.g., plain row wins, or last-write wins) would silently apply — or silently skip — a declared collapse rule depending on which path got there first, which is exactly the kind of silent behavior this slice's hardening work has been closing elsewhere (per `docs/superpowers/spec-defects.md`'s pattern of naming rather than papering over gaps).
- A raise is the same shape as the fix just made for measured+skipped: both are "two structural claims about one unit's origin, in the same execution, that disagree" — refusing is cheap, symmetric, and matches the existing `E-STEP-UNIT-SETTLED` vocabulary (`unit_key` already "settled" once it has a plain row; extending settlement to cover "has any measurement row" for the plain-record side, and vice versa, closes the gap uniformly).
- No document sentence settles this directly — I'm not aware of one — so this is my recommendation, not a claim of authority.

Not implemented here per the coordinator's instruction; routing the reasoning above for task 5.

## Concerns

- `runner.py` still does not pass `measurements` into `StepIO` — confirmed by the coordinator as task 5's obligation ("pin it through a real step rather than a directly-constructed `StepIO`"), not something to fix here.
- The plain-record/measurement mixture above is now a known, recorded gap for task 5, not a concern about this task's own correctness.
- No other open concerns. All originally-named tests, all review-driven additions across both fix rounds, and the full suite pass; ruff and mypy are clean; every behavioural fix across both rounds was independently mutation-tested with its own control.
