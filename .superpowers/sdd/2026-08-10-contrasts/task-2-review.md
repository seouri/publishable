# Task 2 review: `units_matching`

## Verdicts

- **Spec compliance:** ✅
- **Task quality:** approved

## What was checked

**`None` vs `set()`.** `units_matching` returns `None` only when `within is None`; any dict input,
including one with no matching units, falls through to the set comprehension and can legitimately
be `set()`. `test_an_empty_stratum_is_an_empty_set_not_none` pins exactly this case with
`assert units_matching(r, {"sex": "m"}) == set()`, which would fail against an implementation that
collapsed "no match" into `None`. Correct, and tested.

**String coercion of values.** Comparison is `str(unit.attributes.get(k)) == str(v)`, coercing
*both* sides rather than only the config-supplied value or only the roster-supplied one.
`test_values_compare_as_strings` exercises the case named in the brief (int `1` from YAML against
string `"1"` from a table) and passes. Since both sides go through `str()`, the reverse direction
(string config value against a numeric-typed attribute, unlikely in practice since `Unit.attributes`
values generally come from CSV/JSON already as str/int/float) is covered by the same code path —
there's no asymmetry to exploit.

**Conjunctive, not disjunctive.** `all(... for k, v in within.items())` is conjunctive by
construction. `test_multiple_levels_are_conjunctive` discriminates: u1 has `{sex: f, site: a}`, u2
has `{sex: f, site: b}`; `within={sex: f, site: a}` expects `{u1}` only. A disjunctive (any-level)
implementation would also match u2 (its `sex` matches), returning `{u1, u2}`, so this test fails
against a disjunctive reading. Good — the test set as a whole is not vacuous on this axis.

**Unknown attribute named in `within`.** Not distinguished from a genuinely empty stratum.
`unit.attributes.get(k)` returns `None` for a typo'd or nonexistent attribute name, `str(None)`
almost never equals `str(v)`, so the result is silently `set()` — identical to what a correctly
spelled attribute with zero matching units produces. This is not a bug in this task: the brief
scopes `units_matching` as a pure set-membership function with no roster-schema knowledge, and
`reference.md` § Contrasts / § Reporting strata assigns this exact class of check ("stratum names
an attribute not in `data.units.attributes`") to `validate`, not to this helper — see reference.md
line ~2124 for the `report_by` analogue, which is the same shape of check. No test in this diff
covers the "typo vs. real empty stratum" ambiguity, but that ambiguity is expected to be resolved
by a `validate`-time check elsewhere (out of scope for Task 2), not by `units_matching` itself.
Worth flagging for whoever owns the `within`-side `validate` rule, so it isn't dropped between
tasks — but it is not a defect in this task's diff.

**Purity.** Only new import is `from publishable.units import UnitList` under `TYPE_CHECKING`
(contrasts.py line 12), used solely as a string-quoted type annotation. No runtime import of
`config`, `artifacts`, `runner`, `cli`, or even `units` was added. Confirmed via
`grep -n "^import\|^from" src/publishable/contrasts.py` — only stdlib `dataclasses` and `typing`.

**Roster contract.** The implementation does `for unit in roster` (contrasts.py line ~63) — plain
iteration, within `UnitList`'s four supported operations (iterate, `len`, integer index, `.train`).
No membership test, slicing, or `.keys()` call. `Unit.attributes` is a `Mapping`, and `.get(k)` is a
method on that mapping, not on `Unit` or `UnitList`, so it doesn't reach past either contract.

## Test-by-test read

| Test | Catches |
|---|---|
| `test_no_within_means_no_restriction` | `within=None` returning anything but `None` (e.g. `set()`, or a full-roster set) |
| `test_a_single_level_selects_matching_units` | Wrong filter predicate, wrong key used for `unit.key`, off-by-one in which units match |
| `test_multiple_levels_are_conjunctive` | A disjunctive (any-match) implementation — see above, this is the one that discriminates |
| `test_an_empty_stratum_is_an_empty_set_not_none` | Collapsing "no match" into `None` |
| `test_values_compare_as_strings` | Comparing attribute/level raw without coercion (would return `set()` for a config that should match) |

No test independently exercises "level value is int, attribute is int" or "level is str, attribute
is str" as separate baseline cases, but `test_a_single_level_selects_matching_units` and
`test_multiple_levels_are_conjunctive` already cover same-type string comparisons, so the coercion
path isn't the only path being tested — the five tests together are non-redundant.

## Minor

- Doc comment on `units_matching` restates the brief's rationale near-verbatim; acceptable since the
  brief's own docstring was designed to be used as-is, and the report says so explicitly.
- No dedicated test for a `within` value that itself needs `str()` coercion on the *attribute* side
  (i.e., an int-typed attribute compared to a string-typed config level) — the brief's own example
  only exercises int-config/string-attribute, not the reverse. Not required by the brief; noted for
  completeness only.
