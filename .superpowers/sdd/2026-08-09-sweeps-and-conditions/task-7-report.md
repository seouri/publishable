# Task 7 report: Summary-scope reads and the direction check

## What was implemented

`StepIO` (`src/publishable/artifacts.py`) gains four constructor arguments —
`scope: str = "repeat"`, `conditions: list[tuple[int, str]] | None = None`,
`repeats: list[str] | None = None`, `step_scopes: dict[str, str] | None = None` — and:

- `io.conditions` / `io.repeats` (properties) and `io.read_condition(condition, step, name,
  repeat=None)`, all refusing with `E-STEP-SCOPE-ONLY` outside `summary` scope.
- `read_condition` raises `E-STEP-READ-REPEAT-REQUIRED` when the named step is repeat-scoped
  and no `repeat=` is given, and `E-STEP-READ-CONDITION-UNKNOWN` when `condition` isn't one of
  the resolved indices (new — see below).
- `read_upstream` gains the direction check: `E-STEP-READ-DIRECTION` when the named step's
  scope is narrower than the caller's, naming both scopes. Own-scope and any wider read still
  succeed.

`read_condition`'s path (`run_dir/conditions/<nn>_<label>[/repeat]/step/name`) reuses
`runner.step_dir_for`'s layout rather than re-deriving it: extracted the `<nn>_<label>`
formatting into `sweep.condition_dir_name(index, label)`, used by both `step_dir_for` and
`read_condition`. The repeat subdirectory is included only when the run's repeat count is > 1
(mirrors `step_dir_for`'s `collapse_repeats`), derived from `len(self._repeats or []) <= 1`.

12 new tests in `tests/test_artifacts.py`, including one per new `E-` code and the boundary
cases (own-scope read succeeds, one-level-narrower fails, repeat=None vs named repeat, single-
vs multi-repeat path collapse). 398 tests total (was 386), all pass; `ruff check .` and `mypy`
clean.

## Wired by Task 8 (landed at `104b018` while this was in review)

`runner.execute_plan` now builds `conditions_list`/`repeats_list`/`step_scopes` from the plan
and passes them into every `StepIO`, so `io.conditions`/`io.read_condition`/`read_upstream`'s
direction check are live in a real run — confirmed by
`test_a_summary_step_reads_every_condition_in_a_real_run` in `tests/test_acceptance.py`.

## Review round 2 — two Important findings, both fixed

**Finding 1 (real defect):** `read_condition`'s membership check was `dict(...).get(index) is
None`, which conflates "index absent" with "index present, label `None`." The no-`sweep` case
(`sweep.expand` resolves one `Condition(index=0, label=None, ...)`) is exactly the latter, so
`read_condition(0, ...)` in a no-sweep run's summary step raised `E-STEP-READ-CONDITION-UNKNOWN`
on a perfectly valid index. Fixed in two places:
- `runner.execute_plan`'s `conditions_list` now includes every resolved `condition_index` even
  when its label is `None` (previously filtered out on `and e.condition_label is not None`,
  which is what made the no-sweep condition invisible to `read_condition` in the first place).
- `StepIO.read_condition` now checks `index not in by_index` (membership over the mapping's
  keys) before reading `by_index[index]`, so a `None` label passes through as "no `conditions/`
  level to nest under" rather than "unresolved." `condition`'s type and `StepIO.conditions`'
  return type widened to `... str | None`.

Added `test_read_condition_succeeds_for_a_resolved_condition_with_a_null_label` (no-sweep case,
asserts the read succeeds and no `conditions/` directory is expected) alongside the existing
`test_read_condition_rejects_an_unresolved_condition_index` (genuinely absent index still
raises), pinning the two cases apart.

**Finding 2 (real gap, no bug found):** no test called `read_upstream` from a `scope="summary"`
caller. Added
`test_a_summary_step_reads_upstream_from_every_narrower_scope`, parametrized over
`run`/`condition`/`repeat` targets — all three pass. `SCOPE_ORDER["summary"] == 3` is already
the maximum, so every other scope ranks lower and none trips `E-STEP-READ-DIRECTION`; no ranking
bug was hiding here, but the hole in coverage was real and is now closed.

## Fixed per coordinator ruling: `read_condition` now accepts what `io.conditions` yields

Originally flagged as a spec disagreement; ruling was that this was a code defect, not an
ambiguity — the documented `for condition in io.conditions: io.read_condition(condition, ...)`
(reference.md:1784, :1806, :2318) works for any element type as long as `read_condition`
accepts it, and mine didn't. Fixed: `condition` parameter widened to `int | tuple[int, str]`,
normalized to the index before the lookup. Added
`test_read_condition_accepts_the_element_io_conditions_yields`, which iterates `io.conditions`
and passes the element straight through (the documented pattern verbatim), alongside the
existing literal-index tests. `spec-defects.md` entry rewritten as RESOLVED, with only a
one-line residual: the doc never states `io.conditions`'s element type in prose, only through
the three examples' use.

## New error identifiers minted

`E-STEP-SCOPE-ONLY`, `E-STEP-READ-REPEAT-REQUIRED` (both from the brief), and
`E-STEP-READ-CONDITION-UNKNOWN` (not in the brief — added because the brief's own
`read_condition` pseudocode left an unresolved condition index to fail opaquely inside
`_read`'s `FileNotFoundError`, formatting `None` into the path; `E-STEP-UNIT-UNKNOWN` already
names the equivalent mistake for a unit key). None of the three is in `reference.md` § Errors
core raises — same pre-existing gap as `E-STEP-UNIT-UNKNOWN`/`E-STEP-UNIT-SETTLED`/etc. Grepped
first for collisions with existing identifiers; none found. Logged in spec-defects.md.

## Commits

- `7374581` — extract `sweep.condition_dir_name`, used by `runner.step_dir_for`
- `09882a7` — `StepIO` scope/conditions/repeats/step_scopes, the four behaviors above, tests
- `82f16c0` — widen `read_condition`'s `condition` param to `int | tuple[int, str]`
- `104b018` — (Task 8, not mine) wires the CLI/runner end to end
- (this round) — fix the null-label conflation in `read_condition` and its `conditions_list`
  source in `runner.execute_plan`; add the `read_upstream`-from-`summary` coverage

## Verification

`uv run pytest -v` → 409 passed. `uv run ruff check .` → all checks passed.
`uv run mypy` → no issues found in 33 source files.
