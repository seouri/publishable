# Task 10 report: `assign.<axis>.from` resolves, and defaults to the axis name

**Status:** DONE
**Commit:** `bb978ab` — feat(validate): resolve assign.<axis>.from against the axis-name default

## Test summary

`uv run pytest`: 1434 passed, 2 xfailed (pre-existing). `uv run ruff check .`: clean.
`uv run mypy`: clean, 40 source files. Mutation testing done by hand (apply → run the
named test(s) → confirm FAIL → revert → confirm PASS, `__pycache__` cleared between
steps) for:

- dropping the `from` default (`resolved_from = declared_from` with no axis
  fallback) — kills `test_assign_from_defaults_to_the_axis_name` and
  `test_assign_from_default_is_reported_when_it_misses` (message assertion);
- disabling the `E-DATA-ASSIGN-UNKNOWN` branch — kills exactly the from/default
  tests plus the one write-config test that incidentally carries it, and none of
  the `E-DATA-ASSIGN-LEVELS` tests;
- disabling the `arms_of` call site (`try: pass` instead of calling it) — kills
  exactly the three `E-DATA-ASSIGN-LEVELS` tests and nothing else;
- disabling each of `arms_of`'s two raise branches independently — the "value
  names no declared level" branch kills its two tests (bad value, missing
  attribute) and not the "empty level" test; the "empty level" branch kills only
  its own test.

All reverts confirmed by re-running the affected tests, not by `git status`.

## What was built

- `src/publishable/units.py`: `arms_of(roster, column, levels) -> dict[str, list[Unit]]`,
  beside `clusters_of`. Partitions the roster by `column`'s (stringified) value
  against the declared `levels`, raising `E-DATA-ASSIGN-LEVELS` for either
  direction of a set-equality violation — a value naming no declared level
  (including a unit carrying no value for the attribute at all, folded into this
  case the same way `clusters_of` folds its own missing-value case) or a declared
  level no unit's value names.
- `src/publishable/validate.py`: `_check_assign` now takes `roster: UnitList | None`
  (call site updated beside `_check_weight_by`/`_check_cluster_by`). A new `else`
  branch on the method `elif` chain, reached only for `method == "by_attribute"`,
  resolves `from` (declared, or defaulted to the axis name when absent), checks it
  against `data.units.attributes` (`E-DATA-ASSIGN-UNKNOWN`), then — when a roster
  resolved and the axis's `sweep.groups` entry carries a well-formed `levels` list —
  calls `arms_of` and reports its `ContractError` under its own code.
- `tests/test_validate.py`: 7 new tests (default-exercised pair, declared-`from`
  pair, and three `E-DATA-ASSIGN-LEVELS` direction/missing-value tests using a
  hand-built `UnitList`/`Unit` roster of 3 units — deliberately not 2, so an
  arm-aware partition, which groups two units under one level, is distinguishable
  from a cluster-aware one). Updated the pre-existing `_check_assign` call sites
  (7 of them) for the new `roster` parameter, and fixed two `write_config`-based
  tests whose fixture declares no `data.units.attributes` at all: one now asserts
  the newly-live `E-DATA-ASSIGN-UNKNOWN` alongside the pre-existing refusals, and
  `test_by_attribute_assignment_is_accepted` now writes its own `arm`-column CSV
  and declares `attributes: [arm]` so it is a genuine accept-path control for the
  two new checks rather than one that happens to dodge them.
- `docs/reference.md`: amended § Validation's *Attribute assignment resolves* row
  to state set equality in both directions, added a new *Assignment attribute
  exists* row (phrased on *Weight attribute exists*), and added
  `E-DATA-ASSIGN-LEVELS`/`E-DATA-ASSIGN-UNKNOWN` to § Errors `validate` reports in
  the required sorted position (`DRAWN` < `LEVELS` < `METHOD` < `MISSING` <
  `UNKNOWN`).
- `docs/superpowers/spec-defects.md`: recorded the divergence below (gitignored
  path, so not part of the commit — written to disk per the project's convention).

## A brief requirement that does not hold as written

The brief's "Read `_check_weight_by`... before writing either... Every one of those
applies here unchanged" claims the non-`str`-declaration reasoning transfers as-is.
It does not: `weight_by`/`cluster_by` are `envelope.py` `LEAF_TYPES` entries, so a
non-`str` value there really is caught by `E-CONFIG-TYPE` before either check runs,
and returning silently defers to that real backstop. `assign.<axis>.from` is not a
`LEAF_TYPES` entry at all — `envelope.py`'s own comment names `assign`'s children as
one of the dynamic-key families no fixed dotted path can type, the same reason
`method` itself carries no such guard. So `_check_assign` skipping a non-`str`,
non-`None` `from` is *not* deferring to a backstop; it is a latent gap — the fault is
reported by nothing in this build. I kept the skip (matching the two siblings'
control flow) but documented the divergence in `_check_assign`'s docstring, the new
`E-DATA-ASSIGN-UNKNOWN` row, and a `spec-defects.md` entry, rather than letting the
brief's false "unchanged" claim stand silently — which is exactly the defect class
the brief itself warns against (the H3a review's finding, twice).

## Review round 2: fixes

**Status:** DONE
**Commit:** `e455a1e` — fix(validate): close the assign.from non-str gap, and stop citing table position

### Test summary

`uv run pytest`: 1442 passed, 2 xfailed (pre-existing). `uv run ruff check .`: clean.
`uv run mypy`: clean, 40 source files. Additional mutation testing (apply → run →
confirm FAIL → revert → confirm PASS, `__pycache__` cleared between steps):

- disabling the (now-live) non-`str` `from` guard — kills
  `test_assign_from_a_non_string_is_reported_rather_than_skipped` on the message
  assertion (falls through to the generic name-lookup path and reports a different
  message, same code);
- disabling the `from: ""` guard — kills
  `test_assign_from_an_empty_string_matches_weight_bys_own_wording` on the message
  assertion, same reason;
- removing `arms_of`'s `str()` coercion — kills
  `test_arms_stringify_values_before_comparison` in `tests/test_units.py`, and only it.

### What changed, addressing each point

1. **Critical 1 (falsified neighbours).** Reworded every "immediately above/below" /
   "row above" reference in `docs/reference.md`'s `E-DATA-ASSIGN-DRAWN` and
   `E-DATA-ASSIGN-METHOD` rows and in `_check_assign`'s docstring (five spots plus one
   code comment) to name what the sibling row/check *does* rather than where it sits.
   Left the one occurrence outside `_check_assign` (line ~2757, an unrelated function)
   untouched — not part of this diff.
2. **Important 2 (fresh positional phrasing).** Removed both `... below` references I
   had just added (`E-DATA-ASSIGN-LEVELS`'s "see `E-DATA-ASSIGN-UNKNOWN` below" and
   `E-DATA-ASSIGN-UNKNOWN`'s "`E-DATA-WEIGHT-UNKNOWN` below reads that set") — reworded
   to name what the sibling does or, for the `E-DATA-WEIGHT-UNKNOWN` case, to drop
   "below" and keep the true, non-positional "for the same reason ... reads that set".
   Left the pre-existing `E-DATA-CLUSTER-UNKNOWN` row's identical construction alone,
   per the instruction not to fix it elsewhere.
3. **Important 3 (close the gap).** `_check_assign` no longer skips a non-`str`,
   non-`None` `from`: it now reports `E-DATA-ASSIGN-UNKNOWN`, naming the value's type
   (`is a {type} ('{value!r}') rather than a string...`) — folded into the existing
   code per the `E-DATA-ASSIGN-METHOD`/non-mapping-block precedent, not a new one.
   Added a matching test. Rewrote the `spec-defects.md` entry to `RESOLVED`, recording
   what was closed and why the sibling's silent-return reasoning did not transfer
   (no `LEAF_TYPES` backstop exists for a dynamic axis key, so silence there was a real
   gap rather than a deferral).
4. **Important 4 (no end-to-end LEVELS test).** Added
   `test_assign_levels_is_reported_through_a_real_validate_config`: a `write_config`
   test with a real `input/index.csv` (`patient_id,arm` / two `control` rows, no
   `treatment` row), driving `E-DATA-ASSIGN-LEVELS` through `validate_config`'s real
   roster resolution and `sweep.groups` reading, asserted as an exact code set.
5. **Important 5 (`arms_of` untested directly).** Added five direct tests in
   `tests/test_units.py` for `arms_of`'s stated promises: roster order preserved
   within a bucket, value stringification (`{'arm': 1}` against `['1', '2']`), the
   "names no declared level" direction (including the missing-attribute-entirely
   case, folded into the same message), and the "declared level holds no unit"
   direction.
6. **Minor 6.** Fixed the stale "two units" opening clause in
   `test_assign_levels_resolve_when_every_unit_names_a_declared_level`'s docstring —
   the fixture has three, and the rationale now says so.
7. **Minor 7.** `arms_of`'s docstring in `units.py` no longer names "task 12"/"task
   13"; it names what each consumer does instead (the subset view a `between`
   condition's roster is built from, and the per-arm `n` a report counts).
8. **Minor 8.** `from: ""` now gets its own `E-DATA-ASSIGN-UNKNOWN` message, matching
   `_check_weight_by`'s wording for the same shape ("is empty ... changes no
   behavior ... Name the attribute, or remove the key"), with a docstring note
   ("matches the sibling rather than diverging") and a matching § Errors row clause
   and test.
9. **Minor 9.** Reworded § Validation's amended *Attribute assignment resolves* row's
   second clause from "a resolving column with a value only one of the two levels
   holds" to "a column whose values name only one of the two levels, leaving the
   other arm with no units" — units hold values, not levels.

Ran the mechanical pass (trailing whitespace, pipe/column counts, anchor resolution)
over every row touched in `docs/reference.md`; all clean.
