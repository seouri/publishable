# Task 4 report: real `max_executions`, swept-path checks, and the family warning

## What was implemented

`src/publishable/validate.py`:
- Added `_check_sweep(doc, template, c)`, called from `validate_config` after
  `_check_unimplemented`.
- Added a small `_repeat_total(doc)` helper (product of repeat-level counts,
  permissive about invalid levels since `_check_replication` already reports those
  under `E-REPL-N`).
- New identifiers: `E-SWEEP-KEY-UNKNOWN`, `E-SWEEP-AXIS-EMPTY`,
  `E-SWEEP-PATH-UNKNOWN`, `E-SWEEP-VALUE-UNNAMEABLE`, `W-EXEC-BUDGET`,
  `W-STATS-FAMILY`.

## One deviation from the brief's illustrative code, and why

The brief's Step 3 sample checked swept-value nameability with an inline
`re.match(SWEPT_VALUE_PATTERN, ...)` gated behind `elif` after the spec-value
check. That reimplements `sweep.check_swept_value`'s predicate (which the task
explicitly forbids) and, worse, is unreachable for the brief's own test case:
`"a long sentence"` is not a member of `analysis.method`'s `choices`, so
`spec[path].check(value)` already returns a truthy `problem`, and the `elif`
would skip the nameability check entirely — `E-SWEEP-VALUE-UNNAMEABLE` would
never fire, contradicting `test_a_swept_value_must_render_as_a_nameable_label`.

Fixed by making the two checks independent (both `if`, not `if`/`elif`) and
calling `sweep.check_swept_value(value)` directly rather than re-checking the
pattern by hand. Both `E-PARAM-VALUE` and `E-SWEEP-VALUE-UNNAMEABLE` can now
fire on the same value when it is both an invalid choice and unrenderable —
which is correct, since they are two independent defects, and the brief's own
test only asserts membership (`in codes(...)`), not exclusivity.

## Coverage

Every identifier has a positive test that produces it and a negative test
that doesn't fire on the adjacent-but-fine case:
- `E-SWEEP-KEY-UNKNOWN`: typo'd mode fires it; the four refused-but-known modes
  (`paired`/`ablate`/`sample`/`groups`) do not double-report it.
- `E-SWEEP-AXIS-EMPTY`: empty grid axis fires it.
- `E-SWEEP-PATH-UNKNOWN`: typo'd path fires it; a real path does not.
- `E-SWEEP-VALUE-UNNAMEABLE`: a space-containing value fires it; a single `_`
  does not (only `__`, the axis separator, is refused).
- `W-EXEC-BUDGET`: 3×5=15 over a budget of 10 warns; 2×2=4 under 500 does not;
  exactly-at-budget (2×5=10 vs. limit 10) passes, one-over (3×5=15 vs. limit
  14) fails.
- `W-STATS-FAMILY`: 3-condition grid warns and names "3" and "not implemented";
  a single-condition run (no sweep) does not warn.
- Warnings alone leave `exit_code() == 0` and `has_errors` false.

## Verification

`uv run pytest -v`: 371 passed (357 pre-existing + 14 new).
`uv run ruff check .`: clean.
`uv run mypy`: clean, 33 source files.

## No unresolved duplication

Condition count comes from `sweep.expand(doc)` directly, not re-derived.
`_repeat_total` is a genuinely separate, trivial computation (multiply the
repeat levels' `n`/`k`) — not a second implementation of expansion — and is
the same shape as (but intentionally not shared with) `_check_replication`'s
internal total, which additionally needs to detect and report invalid levels
inline; sharing that code would couple a validity check to a budget
computation for no benefit.
