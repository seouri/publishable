# Task 6 report: the refusals and `min_reported_n`

## What was done

`src/publishable/validate.py`:

- Removed `contrasts` from `_check_unimplemented`'s statistics loop, retiring
  `E-STATS-CONTRASTS-UNSUPPORTED` (no active `c.error` call remains anywhere; the
  code survives only as a historical mention in `_check_contrasts`'s docstring and
  in the negative-assertion test that pins its retirement).
- Added `_check_contrasts(doc, c)`, called from `validate_config` right after
  `_check_sweep`. For each declared `statistics.contrasts[i]` entry:
  - `of`/`against` naming another entry's `id` (and not also a real condition
    label) → `E-STATS-CONTRAST-NESTED`, pointing at the interaction/`summary`-step
    `Estimate` route rather than merely refusing.
  - `of`/`against` resolving to no condition's label → `E-STATS-CONTRAST-UNKNOWN`.
    Nesting is checked first, so an `id` that also fails to resolve as a label is
    still diagnosed as nesting (the more specific fault).
  - A name that is simultaneously a real label and another entry's `id` resolves
    as the label — it is not wrongly refused as nesting just because some other
    entry reused its label as an `id`.
  - `within` naming an attribute not in the declared `data.units.attributes` list
    → `E-STATS-CONTRAST-WITHIN` (new — see below). An empty `contrasts: []` is a
    no-op (early return), matching what `materialize` ships.

`min_reported_n` is explicitly out of scope here per the brief — Task 7's, once
`n_paired` exists.

## The unknown-attribute check (Task 2's carried finding)

Grepped `docs/reference.md` before minting: `report_by`'s unknown-attribute rule
(§ Reporting strata, `reference.md`:2124) and the contrast-stratum row
(`reference.md`:272, "Contrast stratum is an attribute") both **state the rule in
prose but name no identifier** — neither `report_by`'s check nor this one existed
in code before this task, so there was no existing code to reuse. **Minted**
`E-STATS-CONTRAST-WITHIN`, following the `E-STATS-CONTRAST-*` family the brief
already established for `-UNKNOWN`/`-NESTED`. Confirmed no collision anywhere in
`src/`, `tests/`, or `docs/` first.

Recorded the gap in `docs/superpowers/spec-defects.md` under a new section, "New
error identifier: `E-STATS-CONTRAST-WITHIN`", in the same shape as the S4a batch's
section immediately above it (`E-STATS-CONTRASTS-UNSUPPORTED` et al.), since that
section is the precedent for "reference.md states a rule, names no code."

## Tests

`tests/test_validate.py`: replaced `test_declared_contrasts_are_refused` with the
four tests specified verbatim in the brief, plus two for the `within`-attribute
check (one refusing, one validating clean), plus positive assertions added after
an advisor review (see below). All ten `E-STATS-CONTRAST-*` codes and the retired
one are exercised through `validate_config`, not an internal check directly.

## Review round

Called `advisor` before declaring done; it found three real gaps, all fixed:

1. **No test asserted the positive claim.** Every original test asserted either
   "the retired code is absent" or "a *different* code is present" — none proved
   `of`/`against` actually resolved against real labels. Added
   `assert "E-STATS-CONTRAST-UNKNOWN" not in found` (and `-NESTED`) to the two
   "validates clean" tests.
2. **Label-shadowing false positive.** `if value in ids` fired even when `value`
   was also a legal condition label, which would wrongly refuse a legal contrast
   whose target happened to be reused as some other entry's `id`. Changed to
   `if value in ids and value not in labels`, with the docstring updated to say so.
3. **`spec-defects.md` gap**, described above.

## Verification

- `uv run pytest -v` → 663 passed (658 baseline − 1 retired test + 6 new).
- `uv run ruff check .` → all checks passed.
- `uv run mypy` → no issues found in 35 source files.

## Commits

- `454aa4f` — Accept declared contrasts, and refuse the ones that nest.
- `70c6f5c` — Tighten contrast checks per review: positive assertions,
  label-shadowing, spec-defects entry.

## Files touched

- `/Users/joon/src/tries/publishable/src/publishable/validate.py`
- `/Users/joon/src/tries/publishable/tests/test_validate.py`
- `/Users/joon/src/tries/publishable/docs/superpowers/spec-defects.md`
