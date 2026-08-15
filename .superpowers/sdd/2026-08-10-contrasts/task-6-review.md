# Task 6 review

## Verdicts

- **Spec compliance:** ✅
- **Task quality:** approved

## Checks performed

1. **Nesting before unknown.** `_check_contrasts` (`src/publishable/validate.py:996-1009`) checks
   `value in ids and value not in labels` before falling to the `elif value not in labels` branch,
   so an `id` that also fails to resolve as a label is reported `E-STATS-CONTRAST-NESTED`, not
   `-UNKNOWN`. Pinned by `test_a_contrast_naming_another_contrast_is_refused`
   (`tests/test_validate.py:938-970`), whose second entry's `of: "a"` both fails as a label and
   matches entry `a`'s `id` — the ordering is exercised, not just assumed.

2. **Label-wins shadowing ruling.** `value in ids and value not in labels`
   (`validate.py:996`) means a name that is simultaneously a real label and another entry's `id`
   resolves as the label. Judgment: label-wins is the more defensible default over "refuse as
   ambiguous" — `of`/`against` is documented to name a condition by label first
   (`reference.md` § Contrasts), so a legal, resolvable contrast is accepted rather than punished
   for an unrelated entry's naming choice, and nothing about the collision is actually unsafe to
   resolve (the label lookup is unambiguous; only the *diagnostic* would have been ambiguous under
   `-NESTED`). A `W-` advisory noting the collision would have been a nice-to-have but its absence
   is not a correctness gap — no test pins this exact collision case, which is the one minor gap
   worth a follow-up test, not a blocker.

3. **`E-STATS-CONTRAST-WITHIN` grep and spec-defects entry.** Confirmed `reference.md:272`
   ("Contrast stratum is an attribute") states the rule and names no identifier, and its
   `report_by` analogue (`reference.md:2124` per the report; table row at `reference.md:274`) is
   itself unimplemented (refused wholesale until S4c). No prior `E-STATS-CONTRAST-WITHIN` existed
   anywhere in `src/`, `tests/`, `docs/`. `docs/superpowers/spec-defects.md:1526-1543` records the
   new identifier, its rationale, and its two pinning tests, in the same shape as the S4a section
   above it.

4. **Nested-contrast message routes to the fix.** The `E-STATS-CONTRAST-NESTED` message
   (`validate.py:997-1004`) names the interaction route explicitly: "a dose-response ordering, a
   difference-in-differences, a nested mean over cells) is an interaction, and stays a
   `summary`-step `Estimate`." Matches the brief's ask.

5. **Empty-list case.** `test_no_declared_contrasts_still_validates_clean` pins `contrasts: []`
   validating clean of all `E-STATS-CONTRAST-*` codes. `_check_contrasts` early-returns on empty
   `entries` (`validate.py:990-991`). The other four S4a refusals (`resample`, `null_test`,
   `report_by`, `hypotheses`) are untouched in the diff — only the `contrasts` tuple entry was
   removed from `_check_unimplemented`'s loop.

6. **`validate.py` refuses before `resolve_contrasts` can raise.** `contrasts.py:40-44` documents
   the dependency explicitly: `by_label[...]` raises `KeyError` on an unresolvable label, and the
   comment states this is acceptable only because Task 6's validate check runs first and `cli`
   always validates before running. `validate_config` calls `_check_contrasts` before returning
   (`validate.py:227`), so an unresolvable label is always caught at validate.

## Coverage bar

- `E-STATS-CONTRASTS-UNSUPPORTED` is gone from `src/`, `tests/`, and the four documents (README,
  design-principles, experimental-designs, reference) — remaining hits are only in
  `docs/superpowers/plans/` and `docs/superpowers/specs/2026-08-10-*` (planning artifacts, exempt)
  and one historical mention in `spec-defects.md`.
- All three new codes (`-UNKNOWN`, `-NESTED`, `-WITHIN`) are exercised only through
  `write_config`/`codes`, which calls `validate_config` — no internal `_check_contrasts` call in
  tests.
- Both "validates clean" tests assert absence of *all three* `E-STATS-CONTRAST-*` codes
  (`-UNKNOWN`, `-NESTED` explicitly; `-WITHIN` via the `startswith`/full-set checks), closing the
  advisor-flagged gap where only negative assertions existed pre-review.

## Test-as-evidence read

- `test_a_declared_contrast_is_no_longer_refused`: catches a regression to wholesale refusal, and
  (post-review) catches a resolver regression that would make a real label look unknown/nested.
- `test_an_unresolvable_side_is_refused`: catches a missing or broken unknown-label check.
- `test_a_contrast_naming_another_contrast_is_refused`: catches a missing nesting check *and* (via
  its `of: "a"` construction, which also fails as a label) pins the nesting-before-unknown
  ordering — not by accident, since a wrong ordering there would flip the asserted code.
- `test_no_declared_contrasts_still_validates_clean`: catches a check firing on presence rather
  than on a real declared entry — the exact regression that would break every scaffolded project.
- `test_a_contrast_naming_an_unknown_within_attribute_is_refused` /
  `..._with_a_declared_within_attribute_validates_clean`: catch a missing or inverted
  attribute-membership check for `within`.

No test exercises the label/id collision case itself (a name that is both a real label and some
other entry's `id`) — the fix for that is described only in the report and the docstring, not
pinned by an assertion. Minor; not a blocker given the logic is simple and one-line.

## Minor findings (non-blocking)

- No dedicated test for the label-wins collision case described in the report and docstring
  (`validate.py:965-966`). A one-line test (`{"id": "a", ...}` plus a second entry whose
  `of`/`against` equals label `"a"` where `"a"` is also a real condition label) would pin the
  ruling rather than leaving it to the docstring.
- `docs/superpowers/plans/2026-08-10-derived-metrics.md:690,702` and
  `docs/superpowers/specs/2026-08-10-derived-metrics-design.md:54` still reference
  `E-STATS-CONTRASTS-UNSUPPORTED` — expected, since these are historical planning docs for an
  earlier slice (S4a), not one of the four documents, and are exempt from the retirement grep.
