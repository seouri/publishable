# Task 4 review: real `max_executions`, swept-path checks, and the family warning

## Verdicts

- **Spec compliance:** ✅
- **Task quality:** approved

## What was checked

Read brief, report, and diff in order. Re-ran `uv run pytest`, `ruff check .`, and
`mypy` from a clean checkout — 108/108 in `test_validate.py`, full suite green,
ruff clean, mypy clean on 33 source files, matching the report's claims.

## Spec compliance

- `validate.py` only collects (`c.error`/`c.warn`); `_check_sweep` never raises. It
  runs after `_check_unimplemented`, guarded by the existing "template resolved"
  early return in `validate_config` — no second shape guard added.
- `sweep.py` is untouched in this diff (`git diff 2b8d9e6..66cf0da -- src/publishable/sweep.py`
  is empty) — no impurity pushed into it, and `check_swept_value`/`expand` are
  imported, not re-derived. The implementation wires `check_swept_value(value)`
  directly rather than hand-rolling `re.match(SWEPT_VALUE_PATTERN, ...)`, which is
  strictly better than the brief's own illustrative snippet (see below).
- Condition count comes from `sweep.expand(doc)` directly; `_repeat_total` only
  multiplies repeat-level counts, a genuinely separate computation, not a second
  expansion. Confirmed by mutating `>` to `>=` in the budget comparison and `> 1`
  to `>= 1` in the family check — both mutations were caught by
  `test_the_budget_passes_at_exactly_the_limit_and_fails_one_over` and
  `test_a_single_condition_run_has_no_family` respectively, so these boundaries are
  real, not decorative.
- `W-EXEC-BUDGET`/`W-STATS-FAMILY` are warnings (`c.warn`), matching
  `docs/reference.md` lines 147/2118 ("validate warns past `limits.max_executions`").
  `test_warnings_alone_leave_the_exit_code_at_zero` confirms warnings don't flip
  `exit_code()`.
- Interaction checked directly:
  - The four refused-but-known modes (`paired`/`ablate`/`sample`/`groups`) are in
    `_check_sweep`'s `known` set, so they do not also fire `E-SWEEP-KEY-UNKNOWN`
    on top of `_check_unimplemented`'s own `E-SWEEP-*-UNSUPPORTED` codes — verified
    both in the diff and by `test_the_four_refused_modes_are_known_keys_not_unknown_ones`.
  - `expand(doc)` is called unconditionally after the per-value loop, including on
    malformed input (unknown sweep key, empty axis, unknown path, bad/unnameable
    value). Traced `expand`'s body: an empty-key sweep or a typo'd mode leaves
    `grid = {}`, giving `rows = []`, no crash; an empty axis list makes
    `itertools.product` return zero combinations, no crash; an unknown path or an
    invalid/unnameable value is never validated by `expand` itself (it just builds
    `Condition`s from whatever's in `grid`), so nothing there can crash either. The
    check that "crashes on the input it was meant to diagnose" concern does not
    apply here.
  - `E-PARAM-VALUE` and `E-SWEEP-VALUE-UNNAMEABLE` are independent `if`s (not
    `elif`), so both can fire on the same value — this is the documented, approved
    deviation from the brief's buggy illustrative `elif`, and it's implemented
    correctly (calls `check_swept_value` rather than re-deriving the pattern, which
    is a further improvement over the brief's own sample code).
- Style/typing: `×` used correctly in the budget message; ruff (`E,F,I,UP,B`,
  line-length 100) and mypy strict both clean; no new dependencies.

## Task quality

Coverage bar met — every identifier (`E-SWEEP-AXIS-EMPTY`, `E-SWEEP-KEY-UNKNOWN`,
`E-SWEEP-PATH-UNKNOWN`, `E-SWEEP-VALUE-UNNAMEABLE`, `W-EXEC-BUDGET`,
`W-STATS-FAMILY`) has a positive test, and the negatives called out in the task
brief are all present and real:
- a resolving path is not flagged (`test_a_swept_path_that_resolves_is_not_flagged`)
- a single `_` is accepted, only `__` is refused
  (`test_a_value_with_a_single_underscore_is_accepted`)
- the four known-but-unimplemented modes don't double-fire `E-SWEEP-KEY-UNKNOWN`
- a single-condition run has no `W-STATS-FAMILY`
- the budget boundary is exclusive in the right direction, confirmed by mutation
  testing above, not just by reading the assertion

## Findings

None rise to Critical or Important.

Minor (informational only, no action required):
- `_repeat_total`'s "get n, fall back to k, else treat as absent" logic duplicates
  a few lines of `_check_replication`'s loop shape (though not its error-reporting
  or total-accumulation semantics — the report's justification for keeping them
  separate is sound and matches the "don't couple a validity check to a budget
  computation" reasoning given). Not worth extracting for three lines of overlap.
