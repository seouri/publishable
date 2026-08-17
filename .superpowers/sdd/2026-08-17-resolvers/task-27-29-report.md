# Tasks 27–29 report

**Status:** all three implemented, tested, mutated, and committed on `h7b-resolvers`.

**Commits:**
- `4e47f50` — `units: project a resolver roster onto the declared attributes` (task 27)
- `5b14a61` — `validate: a resolver must yield the measurement field it declares` (task 28)
- `86d87f9` — `units: a resolver reading a swept parameter is refused under its own code` (task 29)

**Test summary:** `uv run pytest` → 2089 passed, 1 skipped, 2 xfailed (baseline 2079 + 4 + 3 + 3 new
tests across the three tasks). `ruff check`, `ruff format --check`, and `mypy` clean throughout.

## Inherited obligations

**Task 28's check now exists and fires ungated.** `validate._check_measurements` gained a
resolver-aware arm, checked immediately after `valid_by` is computed, that reports
`E-RESOLVER-MEASUREMENT-FIELD` whenever `valid_by not in columns` — with no `technical_n` gate.
`test_a_resolver_yielding_no_measurement_field_is_refused_under_its_own_code` passes `technical_n=None`
specifically to prove the ungated reading, and mutating the resolver arm's condition to add the
table arm's `technical_n["max"] > 1` gate made that test FAIL (confirmed). The table arm was narrowed
to `resolver is None` so the two arms cannot both fire for one declaration. The stale docstring claim
this obligation named (`_from_resolver`'s "checked against what actually arrived") was already
removed before this session; it survives only inside the tracked development record
(`docs/superpowers/plans/2026-08-17-resolvers.md`), which is not retro-edited per `CLAUDE.md`.

**A fixture now reads `cfg`, and substituting `Config({})` at the `resolve_units` call site would be
caught.** Task 29 added `_READS_A_PARAM`, a resolver that reads `cfg.parameters.analysis.method`, used
by three tests in `tests/test_units.py`. Two of them (`test_a_resolver_reading_a_swept_parameter_...`
and its control) call `resolve_units` directly with a `cfg` built from `resolve_wide_cfg` — replacing
either with `Config({})` there would either remove the `SweptAway` marker (silently losing the refusal)
or crash on the missing `parameters` tree, and both are exercised.

**Scoped exactly as the brief predicted, not wider:** the *second* mutation the brief names — changing
`_check_units`'s own `resolve_wide_cfg(doc, wide_swept_paths(...))` call to
`resolve_wide_cfg(doc, set())` — was run and left `uv run pytest tests/test_units.py tests/test_validate.py`
fully green (936 passed, no failures). This confirms the brief's own claim: no test added in tasks
25–29 exercises `_check_units`'s threading through `validate_config`, because (per the spec's
corrections) tasks 25/27/28/29 all call their functions directly rather than through `validate_config`
— task 33 owns that end-to-end assertion. Recorded here, not silently left as a gap I introduced.

## Mutations run (all reverted by editing the file back, `__pycache__` cleared each time)

| Task | Mutation | Expected | Outcome |
|---|---|---|---|
| 27 | `attributes={a: unit.attributes[a] for a in attrs if a in unit.attributes}` → `attributes=unit.attributes` (drop projection) | FAIL | FAIL — `test_a_resolver_roster_is_projected_onto_the_declared_attributes` failed, first unit carried `plate`/`scratch` |
| 27 | `if attribute not in yielded:` → `if any(attribute not in u.attributes for u in units):` (union → per-unit) | FAIL | FAIL — `test_a_name_only_some_units_yield_is_not_missing` raised `E-UNITS-ATTR-MISSING` for `scratch` |
| 28 | resolver arm's `if valid_by not in columns:` → add `and technical_n is not None and technical_n["max"] > 1` (inherit table gate) | FAIL | FAIL — `test_a_resolver_yielding_no_measurement_field_is_refused_under_its_own_code`'s `technical_n=None` call reported nothing |
| 28 | resolver arm's code `"E-RESOLVER-MEASUREMENT-FIELD"` → `"E-UNITS-ATTR-MISSING"` | FAIL | FAIL — same test's positive assertion on the resolver code failed |
| 29 | `if exc.code != "E-STEP-SWEPT-PARAM": raise` → `if False: raise` (re-code every raise) | FAIL | FAIL — `test_a_resolvers_own_coded_refusal_keeps_its_own_identifier` got `E-RESOLVER-SWEPT-PARAM` instead of `E-UNITS-EMPTY` |
| 29 | `_check_units`'s `resolve_wide_cfg(doc, wide_swept_paths(...))` → `resolve_wide_cfg(doc, set())` | PASS (by design, task 33's catch) | PASS — 936 passed, confirmed blind at this task's level as the brief states |

## Where a brief or the spec disagreed with the code

**Task 28's two control-test fixtures, as literally given in the brief, do not pass against the actual
code — for a reason unrelated to the resolver check being built.** Both
`test_a_resolver_that_does_yield_the_measurement_field_reports_nothing` and
`test_a_table_source_keeps_its_collapse_gated_reading_of_the_same_field` use
`{"by": "read_id", "collapse": "mean"}` with a roster carrying `attributes={"operator": "kj"}`, and
assert `[f.code for f in c.findings] == []`. `"mean"` is a `NUMERIC_COLLAPSE_RULES` member, and the
unconditional per-column type loop later in `_check_measurements` reports
`E-DATA-MEASUREMENTS-COLLAPSE-TYPE` for `operator="kj"` regardless of my change — verified against
`main`/pre-task-27 code with the identical fixture (same finding, same code, before any of these three
tasks existed). I changed `"collapse": "mean"` to `"collapse": "first"` in both control tests only
(not in the first, non-empty-asserting test, which the brief left as `"mean"` and which still passes
since it only checks membership, not exhaustiveness) to isolate the property each test is meant to
prove. No other fixture or assertion was altered.

## Files touched

- `src/publishable/units.py` — `_from_resolver`'s attribute projection (27) and `E-STEP-SWEPT-PARAM`
  → `E-RESOLVER-SWEPT-PARAM` translation (29)
- `src/publishable/validate.py` — `_check_measurements`'s resolver arm (28)
- `docs/reference.md` — `E-UNITS-ATTR-MISSING` row widened (27); `E-RESOLVER-MEASUREMENT-FIELD` and
  `E-RESOLVER-SWEPT-PARAM` rows' `Not yet emitted:` clauses struck (28, 29)
- `tests/test_units.py` — 7 new tests (4 for task 27, 3 for task 29)
- `tests/test_validate.py` — 3 new tests (task 28), with the two collapse-rule fixes above

## Concerns

None outstanding. `.superpowers/sdd/.gitignore` was clobbered to a bare `*` by tooling mid-session
(the documented `scripts/sdd-workspace` side effect) and was restored via `git checkout --` before any
commit, so no already-tracked record was lost.
