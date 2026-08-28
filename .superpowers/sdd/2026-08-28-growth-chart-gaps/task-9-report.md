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

---

## Fix round 1 of 5

**Status:** done, all five findings addressed.

**Finding 1 (Critical, counted but never corrected).** Chose the sanctioned fallback: no `Member`
exists for a constant-referenced observation, so `hypotheses.evaluate` now sets
`corrected_unavailable=True` for any counted hypothesis whose `(where, step, metric)` key is absent
from `by_key`, whenever `method != "none"`. Under `correction: none` the entry is unchanged (absent
`ci95_corrected`, matching every other uncorrected member); under a real method a bound test now
reads `supported: null` / `ci95_corrected: null` instead of the raw, uncorrected bound.
Rebuilding a real `Member` from the condition's own resample pool was not attempted: `stats.py`'s
per-condition intervals (`t_over_units`/`percentile_of_derived`) don't retain their draws past
`summarize_step`, so building one would mean plumbing raw per-unit or resample state through to
`hypotheses.evaluate` — out of scope for this fix round. Updated the one existing test that had
pinned the old (now-acknowledged-wrong) behavior
(`test_a_counted_hypothesis_with_no_matching_member_is_corrected_unavailable`, renamed) and added
`test_a_constant_hypothesis_is_corrected_unavailable_on_a_real_correction_method` /
`..._under_no_correction_gets_the_ordinary_absent_field`.

**Finding 2 (Critical, doc over-promise).** Fixed the general sentence at reference.md ~3612 to carve
out the constant form's exception, changed the `above_chance` example's `evaluate_on` to `observed`
(the only evaluate_on that isn't gated by the missing-Member fallback), and added a paragraph after
the worked example spelling out exactly when a constant hypothesis reads `null` under correction.

**Finding 3 (Important, baseline arm unwritable).** `E-HYPOTHESIS-CONDITION`'s "names the baseline
itself" branch now excludes `compare_to == "constant"` — `resolve` never reads `vs_baseline` for that
form, so the baseline's own `aggregated` entry is a real observation. Updated the docstring, the §
Errors row, and added `test_a_hypothesis_naming_the_baseline_itself_under_to_constant_is_not_flagged`
(validate.py) and `test_a_constant_hypothesis_can_name_the_baseline_arm` (hypotheses.py).

**Finding 4 (Important, wrong message).** `E-HYPOTHESIS-COMPARE-VALUE`'s message no longer claims
`supported: null`; it now says what actually happens — `verdict_for` silently treats a bad `value` as
no constant at all and compares the metric's raw value instead. Fixed the matching test docstring too.

**Finding 5 (Important, thin coverage).** Replaced both bound tests with fixtures where `observed`,
`ci95_lower` and `ci95_upper` disagree (added a fourth test, `..._on_observed_disagrees_with_its_own_bounds`,
making the three-way disagreement explicit), and added
`test_the_briefs_own_worked_example_auroc_exceeds_0_5_by_at_least_0_02` instantiating the brief's own
`value: 0.5, threshold: 0.02` example. Added the end-to-end pin
`test_a_constant_hypothesis_resolves_through_a_real_run` (test_cli.py) running a real `run` through
the console script.

**Mutation evidence (all: backup → mutate → red → restore from backup → re-run to confirm green,
never `git status`):**
- Removed the Finding-1 `elif` branch entirely → `test_a_counted_hypothesis_with_no_matching_member_is_corrected_unavailable`, `..._still_reports_observed`, and `test_a_constant_hypothesis_is_corrected_unavailable_on_a_real_correction_method` all failed (40/43 passed) → restored → 43/43 green.
- Reverted Finding 3's `compare_to != "constant"` exclusion → `test_a_hypothesis_naming_the_baseline_itself_under_to_constant_is_not_flagged` failed → restored → green.
- **The exact mutant the reviewer named**: gated the `value`-subtraction in `verdict_for` on `evaluate_on == "observed"` → `test_a_constant_hypothesis_on_ci95_lower_is_superiority` and `..._on_ci95_upper_is_non_inferiority` both failed (43/45 passed) → restored → 45/45 green. (Confirms the earlier fixtures were blind to exactly this bug, as Finding 5 said, and the new ones are not.)
- Mutated `cli.py:4845`'s `aggregated=aggregated` to `aggregated=None` → `test_a_constant_hypothesis_resolves_through_a_real_run` failed (`verdict["observed"]` was `None`) → restored → green.

**Verification:** `uv run pytest tests/test_hypotheses.py tests/test_validate.py` (857 passed),
`tests/test_cli.py -k hypothes` (8 passed); `uv run ruff check .` (all checks passed);
`uv run ruff format --check .` (101 files formatted); `uv run mypy` (no issues, 56 files).

**Concerns:** Finding 1's fallback means a constant-referenced hypothesis's bound is *never*
correctable today (not just occasionally) — every such hypothesis under a real correction method and
a bound `evaluate_on` reads `null`. That is honest but means `evaluate_on: observed` is, in practice,
the only usable form under `correction: holm`/`bonferroni`/`fdr_bh`; a future slice building a real
resample-backed `Member` for the constant form would be the way to lift this.
