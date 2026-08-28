# Task 9 report — `compare: {to: constant, value: <number>}`

**Status:** done.

**Refusal code chosen:** minted a sibling, `E-HYPOTHESIS-COMPARE-VALUE`, rather than widening
`E-HYPOTHESIS-FORM`. Reason: `E-HYPOTHESIS-FORM`'s row is about scope-vs-`compare`-presence
(summary metric declaring `compare` at all, or a non-summary metric declaring none); "declares
`to: constant` without a numeric `value`" is an unrelated fault about the same field family, and
folding it in would make one row do two jobs the way the other `E-HYPOTHESIS-*` siblings
(`-COMPARE-TO`, `-CONDITION`, `-CONTRAST`) already avoid for their own sub-faults.

**Grammar implemented (confirmed against Decision 2 + advisor):** `compare: {to: constant, value: N}`,
with `condition` optionally still nameable to pick which condition's own value is meant (resolved by
`label_to_index`, same as the baseline form). Omitted `condition` resolves against the sole condition
when the run has exactly one; with more than one and none named, resolves to no observation
(`supported: null`) rather than guessing index 0 — same reasoning `E-HYPOTHESIS-BASELINE` already
rests on. `resolve`/`evaluate` now take a required `aggregated` kwarg (per-condition metric table,
`results.conditions[i].aggregated`) as the fourth resolution source; `where` is prefixed `const:`,
distinct from `cond:`/`contrast:`, so a condition carrying both a `vs_baseline` Member and a
constant-referenced hypothesis can't collide in `evaluate`'s `by_key`. `verdict_for` subtracts
`compare.value` from the tested number once, after `_tested_number`, before the `threshold`
comparison — `threshold` stays the boundary, `value` the reference, both independently writable.
No `Member` is built for this form (nothing to bootstrap-correct beyond the block's own `ci95`), so
it's counted into `family_size` but decided on the raw bound, same as any hypothesis with no matching
`by_key` entry today.

**Mutations run (all: cp backup → mutate → red → restore from backup → green, confirmed by re-running
the suite, never by `git status`):**
- Removed the `value`-subtraction shift in `verdict_for` → `test_auroc_below_chance_is_supported_false_same_constant` failed (39/40 passed, 1 red) → restored → 40/40 green.
- Changed `where` prefix from `const:` to `cond:` → 3 tests failed (with-condition resolve, sole-condition resolve, and the explicit collision test) → restored → 40/40 green.
- Relaxed the ambiguous-no-condition guard to default to the first `aggregated` index → `test_a_constant_hypothesis_with_several_conditions_and_no_condition_named_has_no_block` failed → restored → 40/40 green.
- validate.py: dropped `"constant"` from the accepted `to` values → `test_a_compare_to_constant_with_a_numeric_value_is_not_flagged` failed (COMPARE-TO fired) → restored → 11/11 green.
- validate.py: neutered the `E-HYPOTHESIS-COMPARE-VALUE` condition to `if False` → both missing-value and non-numeric-value tests failed → restored → 11/11 green.

**Tests added:** `tests/test_hypotheses.py` (10 new: sole-condition resolve, ambiguous-no-condition
resolve, named-condition resolve, `where`-collision pin, exceeds/below-chance discriminating pair on
`observed`, `ci95_lower` superiority, `ci95_upper` non-inferiority, family-size-grows-by-one +
`verdict_rests_on: computed`), plus updated all existing `resolve`/`evaluate` call sites for the new
required `aggregated` kwarg. `tests/test_validate.py` (5 new: accepted form, missing value, non-numeric
value, summary-metric-still-form-refused with no double-report).

**Docs:** `docs/reference.md` — § Errors table (`E-HYPOTHESIS-COMPARE-TO` row widened,
`E-HYPOTHESIS-COMPARE-VALUE` row added, alphabetically placed), § Pre-registration's `compare`
"names both sides" paragraph (now three forms), config-schema inline comment, § What a hypothesis
is tested against (new `above_chance` example, "all four forms" phrasing, new paragraph on the
constant form's resolution/family-membership/`value`-vs-`threshold` split).

**Verification:** `uv run pytest tests/test_hypotheses.py tests/test_validate.py tests/test_correction.py`
(912 passed) and `tests/test_cli.py -k hypothes` (7 passed, confirms the `cli.py` call-site change);
`uv run ruff check .` (all checks passed); `uv run ruff format --check .` (101 files already
formatted); `uv run mypy` (no issues, 56 files).

**Concerns for review:**
1. `_is_counted` doesn't check for a matching `Member`, so a constant hypothesis always joins
   `family_size` even though no bootstrap correction is ever built for it (no Member exists for this
   form) — it's always decided on the raw bound. This mirrors existing behavior for any hypothesis
   whose `(where, step, metric)` key isn't in `by_key`, but it means `correction: holm` etc. never
   actually tightens a constant-referenced hypothesis's own bound, only the family size others are
   corrected against. Flagging per the brief's request to record any such tension rather than resolve
   it silently.
2. Did not add a design-time guard forbidding `compare.condition` + `compare.contrast` together for
   the constant form — same permissive precedent as the existing baseline/contrast forms.
