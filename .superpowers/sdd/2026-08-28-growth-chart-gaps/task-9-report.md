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

---

## Fix round 2 of 5

**Status:** done, all four remaining items addressed.

**Finding 2, still open.** Fixed both residual homes: (a) reference.md ~3628, "two unrelated reasons"
→ "three", adding the constant form as the third alongside thin-resample and `fdr_bh`; (b) ~3742,
"follows the family rules unchanged" now scoped to "a baseline comparison or a declared contrast",
with a new sentence naming the constant form as the standing exception. Swept README,
design-principles.md, experimental-designs.md, both feasibility files and CLAUDE.md for `corrected
one|corrected bound|family rules` myself after editing — no further homes found; the one other hit
(feasibility-llm-growth-studies.md's "a corrected bound built from the same weighted...") is an
unrelated weighted-contrasts passage, not this promise.

**New finding — `_is_counted` conjunct.** Confirmed the surviving mutant (dropping `_is_counted`
from the `elif` guard) and added two tests that pin it from both directions:
`test_an_exploratory_constant_hypothesis_is_unaffected_by_corrected_unavailable` (an exploratory
constant hypothesis, never in the family) and
`test_a_reported_summary_hypothesis_is_unaffected_by_corrected_unavailable` (a `verdict_rests_on:
reported` summary metric, `obs.where is None` so trivially `key not in by_key`). Both assert
`"ci95_corrected" not in observed` and a real (non-null) `supported`.

**Sibling mutant (dropping `key not in by_key`, leaving `_is_counted(hyp, obs) and method != "none"`):
judged not worth a dedicated test, per the reviewer's own finding.** When `key` *is* in `by_key` for a
counted hypothesis, that key is necessarily among `counted_keys` and thus in `family_members_`, so
`corrected_for` builds a real entry for it and `corrected is not None` — the `elif` branch is never
reached for that case under correct behaviour. Constructing an input where `corrected_for` omits an
entry for a member that's genuinely in `family_members_` would mean reaching into `corrected_for`'s
own internal filtering rather than exercising anything specific to this guard, so I left it unpinned
rather than write a test that doesn't actually discriminate the stated mutant from correct code.

**Required filing.** Added `## OPEN` to `docs/superpowers/spec-defects.md`, owner *unassigned*,
matching the shape of the two neighbouring entries read first ("a `sweep.baseline`..." and "a
correction family cannot span runs..."): states in those words that a constant-referenced
hypothesis's bound test is never answerable under a declared correction method and comes back
`supported: null`, notes `evaluate_on: observed` stays usable, states the `correction: none`
qualifier, and cites `_level_for`'s existing `fdr_bh` precedent. Pinned to commit `6e96655` (the fix
round 1 commit, where the behaviour being described currently lives).

**Minor — "THREE DIFFERENT verdicts."** Fixed: the fixture gives `observed: True`, `ci95_lower:
False`, `ci95_upper: True` — two distinct verdicts across three readings, not three. Reworded both
docstrings (`test_a_constant_hypothesis_on_ci95_lower_is_superiority` and
`test_a_constant_hypothesis_on_observed_disagrees_with_its_own_bounds`) to say what is actually true
— `ci95_lower` is the odd one out, `observed` and `ci95_upper` agree.

**Mutation evidence for the `_is_counted` pin (backup → mutate → red → restore → green, confirmed by
re-running, never by `git status`):** dropped `_is_counted(hyp, obs) and ` from the `elif` guard in
`hypotheses.evaluate` → `test_an_exploratory_constant_hypothesis_is_unaffected_by_corrected_unavailable`
and `test_a_reported_summary_hypothesis_is_unaffected_by_corrected_unavailable` both failed (46/48
passed — each caught the injected `ci95_corrected: null` key) → restored → 48/48 green.

**Verification:** `uv run pytest tests/test_hypotheses.py tests/test_validate.py` (859 passed),
`tests/test_cli.py -k hypothes` (8 passed); `uv run ruff check .` (all checks passed);
`uv run ruff format --check .` (101 files formatted); `uv run mypy` (no issues, 56 files).

**Concerns:** none new. The spec-defects entry restates fix round 1's own concern in the file's
permanent-record form, so future readers see it without depending on this SDD report surviving.

---

## Fix round 3 of 5 — whole-branch review finding

**Status:** done.

**Finding:** `compare: {to: constant}` silently discarded a declared `contrast` — `resolve` tested
`to == "constant"` before `"contrast" in compare`, inverting the already-established (if only
partially documented) precedence that a declared `contrast` wins over every other form.

**Shape chosen: legal combination, contrast wins, documented and pinned — not a refusal.** Reused
reasoning already in `validate.py`'s own comment: `{contrast: x, condition: y}` was already legal
and already resolved through the contrast with `condition` silently unread, on the grounds that
`resolve` checks `"contrast" in compare` first. Refusing `{contrast, to: constant}` while leaving the
identical-shaped `{contrast, to: baseline}` and `{contrast, condition}` unrefused would have been a
new, asymmetric special case — the same fault under a different pairing would stay legal. Extending
the one existing precedence rule to cover all three forms uniformly (reorder `resolve` so the
`"contrast" in compare` branch is checked first, ahead of `to: constant` too) fixes the reported case
without inventing an inconsistency. `E-HYPOTHESIS-COMPARE-VALUE` still validates `value` whenever
`to: constant` is present regardless of `contrast`, matching how `compare.condition`'s own label
validity is already checked regardless of `contrast` — one rule, not a per-field carve-out.

**Code:** `src/publishable/hypotheses.py::resolve` — moved the `"contrast" in compare` branch above
the `compare.get("to") == "constant"` branch; docstring updated to state the full precedence.
`src/publishable/validate.py` — updated the `_check_hypotheses` docstring and the inline comment
above `implies_baseline` to state the extended precedence.

**Docs:** `docs/reference.md` § Pre-registration's "compare names both sides" paragraph gained one
sentence stating the precedence explicitly (`compare: {contrast: x, condition: y}` and
`compare: {contrast: x, to: constant, value: 0.5}` both resolve through the contrast). Swept for
`resolve checks|checked first|wins over|precedence` across reference.md — no other home needed a
change; the field never previously documented multi-form combination behaviour at all, so this is
new coverage rather than a correction of an existing false claim.

**Test:** `test_a_contrast_wins_over_a_declared_constant_and_condition` (test_hypotheses.py),
instantiating the reviewer's exact fixture — `{to: constant, value: 0.5, contrast: "sensitivity",
condition: "method=spearman"}` — and asserting `where == "contrast:sensitivity"` with the contrast's
own block, not the named condition's.

**Mutation evidence (backup → mutate → red → restore → re-run to confirm green, never `git status`):**
reverted `hypotheses.py` to the pre-fix ordering (`to: constant` checked before `contrast`) →
`test_a_contrast_wins_over_a_declared_constant_and_condition` failed, reproducing the exact reported
symptom (`AssertionError: assert 'const:1' == 'contrast:sensitivity'`) → restored the reorder →
49/49 green.

**Verification:** `uv run pytest tests/test_hypotheses.py tests/test_validate.py` (860 passed),
`tests/test_cli.py -k hypothes` (8 passed); `uv run ruff check .` (all checks passed);
`uv run ruff format .` (1 file reformatted, then `--check` clean); `uv run mypy` (no issues, 56
files).

**Concerns:** none new.
