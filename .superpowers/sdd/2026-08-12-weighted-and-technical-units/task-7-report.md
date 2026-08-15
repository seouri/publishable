# Task 7 report: `weight_by`'s three checks

**Status:** complete. One commit, `f510ff9` — *feat: check that a weight exists, is usable, and is not silently absent*.

`uv run pytest` 1176 passed / 2 xfailed post-change; `uv run ruff check .` clean;
`uv run mypy` clean on 40 files. `ruff format` was not run. The pre-change
baseline count was not separately measured — the first full-suite run of this
task already carried the new tests.

## What was built

`_check_weight_by(units, roster, c)` and its helpers `_usable_weight` /
`_warn_undeclared_weight` in `src/publishable/validate.py`, called from
`validate_config` immediately after `_check_measurements`. The two share one
`_units_declaration(...)` call now hoisted into a local, so the call count is
unchanged.

Three identifiers, matching the three `reference.md` § Validation rows:

| Emit site condition | Code |
|---|---|
| `weight_by` is a present empty string, or names a value `data.units.attributes` does not declare | `E-DATA-WEIGHT-UNKNOWN` |
| `weight_by` names a declared attribute and some unit's value for it is not a positive finite number | `E-DATA-WEIGHT-INVALID` |
| An attribute is numeric, all-positive-finite, not all-equal, and named `*weight*`/`*_prob*`/`*probability*`, while `weight_by` is unset | `W-DATA-WEIGHT-UNDECLARED` |

Registry rows added in `docs/reference.md`: two in § Errors `validate` reports
(after `E-DATA-UNREADABLE`, the table being alphabetical by code) and one in
§ Warnings core reports (after `W-DATA-INELIGIBLE`). Each row's condition was
written from the emit site, not from the brief.

## The asymmetry with `measurements.by` — verified, not assumed

`attributes` is the correct reference set for `weight_by`, and the check uses the
*declared* list from the config rather than the roster's realized names. What I
checked:

- `units._from_table` builds `Unit(attributes={a: row[a] for a in attrs})` where
  `attrs = decl.get("attributes")`. **`Unit.attributes` holds the declared
  attributes and nothing else** — a column present in the CSV but absent from
  `data.units.attributes` does not survive resolution at all. So an attribute is
  the only thing readable per unit at analysis time, which is what § Weighted
  samples requires when it says core "hands the column to `aggregate` like any
  other attribute".
- `units.collapse_measurements` drops `by` from the merged unit, so a `by` need
  not survive — the reason task 6's fix pointed it at the source's columns.
- The two § Validation rows word this difference themselves: `weight_by` names
  something "which is not a **unit attribute**"; `measurements.by` names a column
  of "a `reads.csv` with no `read_id` column".
- Reading the *declared* list rather than the roster's names follows
  `_check_report_by`, which does exactly this against
  `data.units.attributes`; it is also what lets the name check run with no roster.
  The two are equivalent when a roster does resolve, since `_from_table` refuses
  an attribute its table has no column for.

Consequence worth stating: under a `{glob: ...}` source no attribute can be
declared at all (`_from_glob` refuses any name), so a `weight_by` there always
draws `E-DATA-WEIGHT-UNKNOWN`. That is truthful — a glob yields a key and a path
and nothing else — and it is written into the registry row.

## Two defects in the brief

**1. The brief's numeric test refuses every real weighted config, and makes the
warning unreachable.** The brief's implementation tests
`isinstance(u.attributes.get(declared), (int, float))`. Every table-sourced
attribute value arrives through `csv.DictReader` and is therefore a `str`, so
that test is `False` for every unit of every CSV-sourced roster: the value check
would report `E-DATA-WEIGHT-INVALID` against the exact YAML § Weighted samples
prints, and the identical test inside the warning loop would `continue` on every
column, making `W-DATA-WEIGHT-UNDECLARED` a check that can never fire — which its
negative test (`... not in codes(path)`) would have passed silently.

Fixed by using `units.is_measurement_numeric`, which the repo already declares the
single authority for that question and which accepts a `str` that parses as
`float` for precisely this reason. Two conditions added on top of it:

- `math.isfinite` — `is_measurement_numeric("nan")` is `True` and `nan <= 0` is
  `False`, so positivity alone admits a value that turns every weighted mean into
  `nan`. Pinned by `test_a_non_finite_weight_is_refused`.
- positivity, kept separate at the emit site so the message can name which
  failed.

**2. The brief routes a wrongly-typed `weight_by` into the "is empty" message.**
`envelope.LEAF_TYPES` types `data.units.weight_by` a `str`, so `weight_by: 3` is
already `E-CONFIG-TYPE`; `if declared is not None and not declared` would add a
second finding calling `3` empty. The check now returns on a non-string, matching
the `input_dir`/`key` guards in `_check_units`. Pinned by
`test_a_non_string_weight_by_is_left_to_the_envelope`.

A third, smaller one found while testing: an absent or `null`
`data.units.attributes` must be read as an empty list, not as a reason to skip —
"nothing is declared, so `weight_by` names none of it" is row 291's own case
(`weight_by: sampling_weight` with no `attributes` block), and skipping it made
the commonest form of the mistake the one form reporting nothing. Only a
*present, wrongly-shaped* `attributes` is skipped, `E-CONFIG-SHAPE` having
reported it.

Also: the brief's registry counts are stale. The `E-` table held **68** rows, not
67 (task 6 added one), so it is now 70; the `W-` table's 18 → 19 was right.

## The warning's heuristic — judged, and the documents made to agree

I kept the name test, and I do not think it is core-clean. § Weighted samples
states the trigger as "numeric, positive, and varying across units in a way a
measurement wouldn't" — **no name component** — and by CLAUDE.md's core-vs-plugin
test a substring match on English words is not identical for a wet-lab assay
(where `weight` is body mass, a measurement) and an LLM benchmark. The reason I
kept it anyway: without it the other three conditions hold of `age`, `dose`,
`latency` and `score`, so the warning fires on nearly every numeric attribute, and
a warning that fires on almost everything is one a reader trains themselves to
skip — a worse outcome than a false positive on `body_weight`. What makes the
false positive payable is that the message states its own remedy in one step:
declare it, or rename it.

Because I shipped the name test, three statements about one trigger would
otherwise have disagreed (the prose, the § Validation row, the new `W-` row).
Per CLAUDE.md the document changes first, so **§ Weighted samples' sentence now
names the name test**, says why it is part of the trigger, and concedes it is the
trigger's weakest part. The § Validation row needed no change; it says
"varies across units and looks like an inverse sampling probability", which the
name test is a reading of. `experimental-designs.md`'s one-line mention was
checked and is still accurate. I added no second discriminator (values near 1,
values summing to `n`) — that would be unstated numerology.

## Tests — 15 (16 cases), all reaching the checks

In `tests/test_validate.py`, with a local `_weighted_table` helper that writes
into the same `input/` directory `write_config` points `data.input_dir` at (the
harness trap named in the task). Every assertion names its own identifier, never
"some finding", so none of them can pass off the live
`E-DATA-WEIGHT-UNSUPPORTED` refusal — which `codes()` does return alongside, and
which task 11 retires.

Both directions are pinned for each check: a declared attribute is *not* reported
unknown; a weight-shaped column warns and a `dose`-shaped one on the identical
fixture does not; declaring `weight_by` silences the warning. The no-roster skip
is reachable in both directions — `test_the_name_check_still_runs_with_no_roster`
(relative `input_dir`, name check still reports) and a direct
`_check_weight_by(..., None, c)` call proving the value half is what is skipped.

The positive warning test is parametrized over **both** forms of "unset" — the
key absent, and `weight_by: null`, which is the form `init` actually materializes
and the one a check keyed on key-absence would miss — and asserts the message
names `sampling_weight`, so it claims "the warning about this column fired"
rather than "a warning fired".

## Mutation results — each check killed separately

`__pycache__` deleted between every mutation and revert; the revert was verified
by re-running the tests and `mypy`, never by `git status`.

| Mutation | Killed by |
|---|---|
| `if declared not in names:` → `if False:` | `test_a_weight_by_naming_no_attribute_is_reported` |
| empty-string branch disabled | `test_an_empty_weight_by_is_a_finding_not_a_default` |
| `number <= 0` → `number < 0` | `test_a_zero_weight_is_refused` (+ the zero-column warning test) |
| `math.isfinite` dropped | `test_a_non_finite_weight_is_refused` |
| `is_measurement_numeric` gate dropped | `test_a_non_numeric_weight_is_refused` (raised `ValueError` — the gate is also what keeps the check total) |
| `c.warn(...)` disabled | `test_a_weight_looking_column_warns_when_nothing_declares_it` |
| constancy test dropped | `test_no_weight_warning_for_a_constant_column` |
| name-hint test dropped | `test_no_weight_warning_for_a_column_the_name_test_does_not_match` |

The `<= 0` → `< 0` mutation is the one the task warned about: with only a
negative-weight case it survives. It is killed by the zero case, which is why the
two are separate tests rather than one parametrized "bad weight".

**One mutation initially survived** — disabling the empty-string branch. `''` is
also "not a unit attribute", so the name check reported the same code by a
different route and a code-only assertion could not tell the branches apart. The
test now asserts the message says "is empty", and the mutation dies. Worth
recording as the shape of a passing-but-blind test: two branches, one identifier.

## Concerns

1. **The name test is a genuine core-vs-plugin compromise**, argued above rather
   than hidden. If a reviewer wants it out, the alternative is not "drop the name
   test" but "drop the warning" — without a name component it fires on nearly
   every numeric attribute, and § Weighted samples would need the warning removed
   from it. I did not think that trade was mine to make unilaterally, so I kept
   the warning and changed the prose to state what it actually tests.
2. **The registry rows document checks that are unreachable in isolation until
   task 11**, since `E-DATA-WEIGHT-UNSUPPORTED` accompanies every one of them
   today. `reference.md` § The one config file already explains that the
   `-UNSUPPORTED` family is a deferral rather than a fault, so the rows are not
   contradicted; but a reader hitting `E-DATA-WEIGHT-UNKNOWN` today also gets the
   refusal, and only task 11 makes the pair read as one answer.
3. **Only the first candidate attribute warns**, in sorted order. `weight_by`
   names one attribute and the remedy is the same sentence for each, so a second
   warning adds no decision — but a roster carrying `sampling_weight` and
   `site_prob` reports only one of them, and that is stated in the `W-` row
   rather than left to be discovered.
4. **`E-DATA-WEIGHT-INVALID` reports once for the whole roster**, naming the count
   and the first offending unit. That matches how the collapse-type check reports
   and keeps a 240-unit roster from producing 240 findings, but a user fixing them
   one at a time re-runs `validate` per fix.
5. **A `== set()` test that declares a weight-shaped attribute will now fail.**
   Several existing tests assert exact emptiness; all still pass, because
   `base_config` declares no `data.units` at all and the warning never runs
   against it. A future test declaring `attributes: [sampling_weight]` and
   asserting `== set()` is failing correctly, not regressing.
6. **`_units_declaration` is still called twice with the same `Collector`**, as
   it was before this task — once in `_check_units`, once at the hoisted call
   site. Read rather than assumed: it dedupes, reporting `E-CONFIG-SHAPE` only
   when that exact diagnostic is not already in `c.findings`, so the second call
   cannot double-report. No third call was added.
7. **Task 8 must not re-derive "is this a usable weight"** from a bare isinstance
   test. `_usable_weight` is the predicate `validate` approves a config against;
   a weighted mean built on a different notion of numeric reopens exactly the
   validate-clean-then-crash gap `is_measurement_numeric` exists to close.
