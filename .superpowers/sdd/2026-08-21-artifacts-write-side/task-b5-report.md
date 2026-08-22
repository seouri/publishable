# H5a tasks 5–6 — report

Order: 5 then 6, each committed separately, per dispatch.

Commits:
- Task 5: `828f42b` — "H5a task 5: split the constant, refuse a reserved column name, and pin
  that a recorded by column survives"
- Task 6: `cf3789c` — "H5a task 6: coerce roster attribute values at resolve_units, and pin that
  nothing is paid for before the refusal"

Baseline: **2855 passed, 1 skipped, 2 xfailed**; `ruff check .`, `ruff format --check .`, `mypy`
(52 source files) all clean.

Test summary: full suite green at **2875 passed, 1 skipped, 2 xfailed** — baseline plus 20 new
tests (15 for task 5, 5 for task 6), all passing. All four gates clean after both tasks.

## Task 5 — split the constant, refuse a reserved column name, pin that `by` stays legal

**`src/publishable/units.py`**: `RESERVED_FIELDS` split into `UNIT_FIELDS = ("key", "paths",
"attributes")` and `RESERVED_COLUMNS = ("unit", "measurement", "by")`, each with its membership
rule stated beside it. The three attribute call sites (`_from_table`, `_from_glob`,
`_from_resolver`) now check `UNIT_FIELDS` (→ `E-UNITS-ATTR-RESERVED`), then `RESERVED_COLUMNS`
(→ `E-UNITS-ATTR-COLUMN`, minted by task 4), then the existing unsourced/missing check — the same
order at all three sites. `validate.py`'s one comment and `test_validate.py`'s one docstring
mentioning the old name were updated; no other `src/`/`tests/` site referenced it (swept with
`grep -rn 'RESERVED_FIELDS' src/ tests/ docs/` — only the development record hits, left untouched).

**§ Errors: one emit path, not two surfaces.** Measured by reading (`_check_units` calls
`resolve_units` inside `except ContractError`; `command_run` calls `validate_config` first and
returns `EXIT_WRONG` before its own `resolve_units` call) and confirmed by running both commands:
`tests/test_validate.py::test_a_reserved_column_name_meets_the_same_refusal_at_run` runs
`main(["run", ...])` end to end and asserts `EXIT_WRONG`, `E-UNITS-ATTR-COLUMN` in stdout, and no
run directory.

### `RESERVED_COLUMNS` has exactly ONE reader

The attribute-name check at the three call sites above, and nothing else. A comment beside the
constant (and beside the projection each call site's own comment already had) states why it must
NOT be pointed at `io.record`'s collision guards, `_collapse_measurements`'s structural-column
exclusion, or `finalize`'s `key != "unit"` filter: all three answer a *different* question — "may
a **recorded** column be named this?" — whose answer for `by` is yes (design Decision 4: the
refusal removes one producer of a `by` column, an attribute declaration, never the possibility of
one, since a step *recording* `by` stays legal). The three literals (`"unit"`/`"measurement"` in
`record`'s guards, `("unit", "measurement")` in `_collapse_measurements`, `"unit"` in `finalize`)
are untouched.

### The pin that a legally recorded `by` column survives both `record` branches

`tests/test_artifacts.py`, two new tests, both reading the parquet back:

- `test_a_plain_recorded_by_column_survives_into_units_parquet` — a **plain** `io.record({"by":
  2.0, "score": 10})` reaches `units.parquet` with `by: 2.0` intact.
- `test_a_measured_by_column_survives_the_collapse_into_units_parquet` — a **`measurement=`**
  -recorded `by: "north"`, declared `collapse: "first"` (not a numeric rule — under a numeric rule
  `coerce_for_rule` would refuse a string `by` value before this arm could observe survival at
  all, which is exactly the "fires for the wrong reason" fixture this repo has shipped before), and
  a string value (not numeric — a numeric value under `first` would pass even if
  `_collapse_measurements`'s exclusion tuple HAD been re-pointed at `RESERVED_COLUMNS`, since
  `coerce_for_rule` produces a number either way; only a non-numeric value under `first`
  distinguishes "excluded" from "collapsed").

Mutation (iv) — pointing `finalize`'s `key != "unit"` at `RESERVED_COLUMNS` — makes **both** arms
fail (not only arm (a)): `finalize`'s filter runs once over every row in `self._rows`, which holds
both plain rows and `_collapse_measurements`'s output, so the same re-pointed filter drops `by`
from `recorded` for either path. Both failures are on the column's absence from the read-back
parquet, exactly the shape the brief names.

### Fixture A — the reserved column name, decoy on each side

Three arms (`unit`, `measurement`, `by`), each declared beside `aaa_site` (sorts before) and
`zzz_site` (sorts after) as real columns, run through both `resolve_units` directly
(`tests/test_units.py`) and `validate_config` (`tests/test_validate.py`). A fourth arm (`paths`)
asserts `E-UNITS-ATTR-RESERVED`, proving the two codes are told apart rather than one swallowing
the other (`test_a_units_field_name_among_decoys_is_still_reported_reserved_not_column` /
`test_units_field_among_decoys_is_reserved_not_column_at_validate`). The resolver arm's decoys are
yielded attributes, not table columns (`_from_resolver` projects onto the union of what was
yielded). The glob arm carries the reserved name alone, with its docstring stating why it can't
carry the decoys its siblings do (`_from_glob` refuses *every* declared attribute as unsourceable,
so a leading decoy would raise `E-UNITS-ATTR-MISSING` first).

### Mutations — four, against the full suite

| # | Mutation | Result | Assertion that failed |
|---|---|---|---|
| (i) | Drop `unit` from `RESERVED_COLUMNS` (then, separately, `measurement`, then `by`) | Exactly the matching Fixture A arm fails each time (`[unit]` alone, then `[measurement]` alone, then `[by]` alone) | `DID NOT RAISE ContractError` on that one parametrized arm; the other two pass |
| (ii) | Point the attribute check at `UNIT_FIELDS` alone | Fixture A's three reserved-column arms all fail; the `paths` control still passes | `DID NOT RAISE ContractError` on `unit`/`measurement`/`by`; `E-UNITS-ATTR-RESERVED` still asserted correctly for `paths` |
| (iii) | Raise `E-UNITS-ATTR-RESERVED` for a reserved column | 11 tests fail across `test_units.py` and `test_validate.py` — every Fixture A code assertion, plus the dual-surface `run` test | `assert 'E-UNITS-ATTR-COLUMN' in found` (or in stdout) — code came back `E-UNITS-ATTR-RESERVED` |
| (iv) | Point `finalize`'s `key != "unit"` at `RESERVED_COLUMNS` | Both step-6 survival arms fail | `by` absent from the read-back `units.parquet` row |

Each reverted by editing back in place (no `git checkout --`), verified by re-running the affected
test(s) green afterward, then confirmed by the full-suite green run reported above.

## Task 6 — coerce roster attribute values at `resolve_units`, pin the ordering

**Step 1 — re-read `cli._attributed`'s docstring, own conclusion:** confirmed at current HEAD:
`_attributed` merges the roster's declared attributes into a unit table's **rows** only, feeding
`tmpl.aggregate(...)`, whose return is then coerced into a **fresh** `derived` mapping — never
merged into `collapsed`, which is what `stats.py`'s `_is_numeric`-gated code (recorded-column
walks, correction family, `report_by`) actually reads. `numpy.int64` is confirmed not an `int`
subclass by grep/read. So coercing `Unit.attributes` values cannot move a published number: a
resolver could already hand `aggregate` a numeric attribute pre-coercion (as `np.float64`), and
this task only normalizes its *type*, never its numeric-ness, for any check that feeds a
publication. The docstring's own hazard sentence is unchanged and still accurate; this task does
not touch it. My own conclusion matches the design's: scope unchanged.

**`src/publishable/units.py`**: at the very end of `resolve_units`, after the source, after
`collapse_measurements`, and after the key-uniqueness loop, every resolved `Unit`'s attribute
mapping is run through `coerce_scalars` and rebuilt **unconditionally** into a fresh `Unit`. A
`ContractError` from the coercion is caught and re-raised under `E-RESOLVER-YIELD` (message
preserved, code only changed — the same catch-and-re-code shape `E-RESOLVER-SWEPT-PARAM` already
uses over `E-STEP-SWEPT-PARAM`). No new identifier minted, per Decision 4's own test: the fault —
"what this resolver yielded is not something core can build a roster row from" — does not differ
between a non-`Unit` yield and a `Unit` carrying an unusable attribute value.

**`docs/reference.md`**: § Errors validate reports and § Errors core raises' `E-RESOLVER-YIELD`
rows widened to name the second shape and where it's raised. § Where units come from gains a new
paragraph stating the scalar rule, what ran before (a resolver-yielded list wrote a list column
into `units.parquet` unrefused), what happens now, and the identity cost (a resolver's own yielded
`Unit` object is replaced by an equal-but-coerced one; `Unit` promises no object identity, only
equality by `key`).

### Fixture R

`tests/test_units.py`:

- `test_a_resolver_yielding_a_structural_attribute_value_is_refused` — a resolver yielding
  `Unit(attributes={"tags": [1, 2], "site": "north"})`, with `tags` **declared**, asserts
  `E-RESOLVER-YIELD` at `resolve_units` (the surface `validate` reaches). Declaring `tags` matters:
  `_from_resolver` projects onto the declared list, so an undeclared structural attribute is
  silently dropped and never reaches the coercion at all (confirmed against the existing
  `test_a_resolver_roster_is_projected_onto_the_declared_attributes`).
- `test_a_resolver_yielding_a_numpy_scalar_attribute_coerces_to_exact_python_float` — the
  **positive control**: the same shape with `np.float64(1.5)` in place of the structural value.
  Asserts `type(roster[0].attributes["score"]) is float` — exact-type, not `isinstance`, since
  `np.float64` passes `isinstance(v, float)` and an exact-type check is the only thing that proves
  the coercion ran rather than merely that nothing refused.
- `test_the_coercion_runs_after_the_uniqueness_check` — the placement pin: a resolver yielding two
  units sharing a key, one carrying a structural declared attribute, reports
  `E-UNITS-KEY-DUPLICATE`, not `E-RESOLVER-YIELD` — the roster-identity fault, exactly as today.

### THE ORDERING PIN — arms O1 and O2, `tests/test_cli.py`

Two separate test functions (kept apart rather than sharing one, because two `installed(...)`
calls registering the same entry-point name in one test would leave both distributions on
`sys.path` simultaneously and collide as `E-PLUGIN-COLLISION` — an unrelated refusal that would
have made the pin meaningless):

- `test_arm_o1_a_structural_resolved_attribute_pays_for_nothing_before_it_refuses` — a real,
  10-unit `run_a_project` against a resolver yielding a structural declared attribute
  (`unit_attributes=["tags"]`), `expect_exit=EXIT_WRONG`. Asserts `run_dir is None`, **and** — the
  actual ordering pin — `next(results_dir.glob("run_*"), None) is None` and neither `latest` nor
  `latest.txt` exists under `results_dir`. The exit code alone is not the pin: `EXIT_WRONG` is
  identical whether the run never started or started and then failed differently.
- `test_arm_o2_the_positive_control_for_the_ordering_pin_completes_and_coerces` — the same project
  shape with `np.float64(i)` in place of the structural attribute (`unit_attributes=["score"]`).
  The run completes; a `run_*` directory exists; `units.parquet` (found via `rglob`, since the
  step is `repeat`-scoped and nested) holds `score` for every unit, coerced.

**What O1 alone would miss, and what O2 alone would miss.** O1 alone proves only that `run`
returns `EXIT_WRONG` for this project shape — indistinguishable from a run that never started for
an unrelated reason (a missing template, a bad path). O2 alone proves the coercion works but says
nothing about ordering. Together: O1 shows the refusal happens with nothing paid for, O2 shows the
identical project shape, absent the structural value, executes and coerces — so O1's refusal is
attributable to the coercion, not to something else about the fixture.

### Mutations — three, against the full suite

| # | Mutation | Result | Assertion that failed |
|---|---|---|---|
| (i) | Remove the coercion from `resolve_units` (drop the whole rebuild block, restore the plain `return UnitList(units), ...`) | Fixture R's refusal arm: structural value survives, no raise. Fixture R's control arm: `type(...) is float` fails (`np.float64` survives uncoerced). Arm O1: fails **one line earlier than my own custom assertion** — inside `run_a_project`'s own `assert main(...) == expect_exit`, because the run now returns `EXIT_OK` (`0`) instead of `EXIT_WRONG`. Captured stdout shows a real `run_2026-...` directory and `run.yaml` written — exactly "the run executed" the brief names as the ordering pin's failure shape. | `Failed: DID NOT RAISE ContractError` (refusal arm); `assert <class 'numpy.float64'> is float` (control arm); `assert 0 == 1` inside `run_a_project`, with a real run directory visible in captured stdout (arm O1) |
| (ii) | Make the coercion refuse a NumPy float instead of coercing it (inline type-name check before the `coerce_scalars` call, raising `ContractError` on any `numpy.float*` value) | Fixture R's refusal arm still passes (refuses, as it did before — for a different reason now, but still refuses). Fixture R's **control** arm fails: the resolved-roster assertion never runs because resolution itself now raises. | `publishable.errors.ContractError: mutated refusal` raised where the control test expected a resolved roster |
| (iii) | Move the coercion above the uniqueness loop | The placement pin fails: reports `E-RESOLVER-YIELD` instead of `E-UNITS-KEY-DUPLICATE` | `assert 'E-RESOLVER-YIELD' == 'E-UNITS-KEY-DUPLICATE'` |

Each reverted by editing back in place, verified green afterward.

**Task 9 has not landed** (per correction 6's ordering, task 9 — the two row-shaped writers'
coercion — is a later task in this same slice, not yet built as of this batch). Mutation (i)'s
run therefore *completes* rather than raising inside `finalize`, exactly as the brief predicts;
the full "every execution paid for, the record lost" shape (a completed run's late `ContractError`
inside `finalize`) is only observable once task 9 lands, and that re-run is task 11's, not this
batch's.

## Confirming Fixture R closes correction 6's enforcement gap

Plan correction 6 ordered task 10 (the shared `str`-by-inheritance branch in `coerce_scalars`)
before tasks 6 and 9, and the ledger for batch 4 recorded that the ordering constraint was
enforced only at the shared function — nothing pinned the **resolver surface** specifically. Task
6's `test_a_resolver_yielding_a_numpy_scalar_attribute_coerces_to_exact_python_float` calls
`resolve_units` on a real installed resolver yielding an attribute value, going through
`units.py`'s own call site (not a direct call to `coercion.coerce_scalars`), and asserts the exact
Python type survives. This is the resolver-surface pin the ledger named as missing: it would fail
if `units.py`'s coercion call site were ever removed or reverted, independent of whether the
shared function's own branch stays intact.

## Zero-disagreements check

Grepped rather than assumed: `grep -rn 'RESERVED_FIELDS' src/ tests/ docs/` confirms the only live
(non-development-record) hits were the one comment in `validate.py` and the one docstring in
`test_validate.py`, both updated; `grep -n 'W-STATS-STRATUM-SHADOWED'` confirmed it is already
shipped before citing it in a docstring; `grep -n '_is_numeric'` confirmed its four call sites are
all over `collapsed`/recorded-column tables, never over `_attributed`'s output, before stating
task 6's step-1 conclusion. No disagreement found between the design/plan and the code for either
task.

## Concerns

- Task 5's mutation (iv) breaks *both* survival arms, not only arm (a) as literally named in the
  brief — because `finalize`'s `key != "unit"` filter runs once over every row regardless of which
  branch produced it. Reported rather than silently narrowed to match the brief's wording; both
  failures are on the correct property (the column's absence from the file).
- Task 6 mutation (i)'s arm-O1 failure surfaces one assertion earlier than the one I wrote
  (`run_a_project`'s own `assert main(...) == expect_exit`, before my `run_*`-glob assertion is
  ever reached) — the shared test helper checks the exit code first. The captured stdout under
  that failure shows the real `run_*` directory and `run.yaml`, which is the same fact the brief's
  named failure shape describes.
