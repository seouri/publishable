# H5a tasks 1–2 — report

Commits: `3230ce1` (task 1), `4dc9a50` (task 2).

Test summary: full suite green at both commits — task 1: **2844 passed, 1 skipped, 2 xfailed**
(unchanged from batch 1's baseline); task 2: **2845 passed, 1 skipped, 2 xfailed** (+1, the new
fixture). All four gates (`ruff check`, `ruff format --check`, `mypy`, `pytest`) clean at both
commits.

## Task 1 — the cross-row unification rule (`docs/reference.md` § The per-unit tables)

Documents only, no code moves. Added, after the existing `units.parquet` column-set sentence:
the five-clause rule (one type round-trips; `int`/`float` promotes; `None` skipped; empty writes
empty; everything else refuses with `E-STEP-RETURN-TYPE`), the "why documented rather than
revised" ground, the "where the code's answer is arguably wrong" paragraph routing the mixed-type
case to H5b's Decision 10, and a sentence scoping the whole rule to `.parquet` (both per-unit
tables), explicitly not generalizing to `.csv`.

**Traced, not asserted:**
- The five clauses trace to `_check_column_types` in `src/publishable/artifacts.py` (lines
  88–120): the `normalized = float if actual in (int, float) else actual` line is the promotion;
  `if value is None: continue` is the skip; `if len(groups) > 1: raise ...` with `code=
  "E-STEP-RETURN-TYPE"` is the refusal, naming the column, both types (`type_a.__name__`/
  `type_b.__name__`) and one unit for each (`unit_a`/`unit_b`); an empty `rows` list makes the
  `for` loops execute zero times, raising nothing.
- **The two shipped tests, grepped by name and confirmed to predate this slice**:
  `test_a_mixed_int_and_float_column_promotes_to_float_deliberately` and
  `test_a_bool_and_int_column_clash_raises_rather_than_coercing`, both in
  `tests/test_artifacts.py`. `git log -S` on the first name's introduction resolves to commit
  `cca47ce` ("Pin the int/float promotion and the loud type clashes"), which predates every H5a
  commit (`badec28` onward).
- **Correction 8 / the `.csv` scoping**: confirmed by reading `_encode_csv` (no
  `_check_column_types` call) versus `_encode_parquet` (calls it) — the check has one call site,
  so the rule is stated for the format it is true of, per the design's task 1 step 3 and the
  plan's correction 8.

No test added (documents-only task); the mechanical pass (anchors, no trailing whitespace/tabs,
no duplicate headings, table column counts) was run over the diff and is clean.

## Task 2 — `measurements.parquet`'s column set, pinned from a real run

**Documents:** the same section gains two paragraphs: the column set (`unit`, `measurement`, then
every recorded key, no declared attribute) with Decision 2's ground (an attribute is constant
across a unit's measurements, so it has nothing to collapse into in the *uncollapsed* table — the
same argument § Templates makes in the other direction for `aggregate`'s table, cited by anchor),
and the disjointness paragraph (the three column groups never collide, because `io.record`'s
`measurement=` branch refuses `unit`, `measurement`, and any name shadowing a declared attribute
— all `E-STEP-KEY-COLLISION`, read from `src/publishable/artifacts.py`'s `record` method before
writing the sentence).

**The fixture — confirmed to come from a real run, not a probe.** `run_a_project` (a project
scaffolded, committed, and run through `main(["run", ...])`) with `unit_attributes=["cohort"]`, a
roster carrying a real `reading` column (the measurement-axis column the table genuinely has), and
`data.units.measurements: {by: reading, collapse: {score: mean}}`; a generated starter step
records two independent measurements per unit via `io.record(unit.key, {"score": ...},
measurement="m1"/"m2")`. Added as
`test_h5a_task2_measurements_parquet_carries_no_declared_attribute` in `tests/test_cli.py`, right
after the H5a arm-A fixture it mirrors.

**What the real run showed that reading could not:** every existing test touching
`measurements.parquet` (`test_measurements_parquet_holds_the_uncollapsed_rows` and its neighbors
in `tests/test_artifacts.py`) builds a `StepIO` directly via `_measuring_io`, which never passes
`units=` — so `self._units` is `None` and `attribute_names` is always empty in those tests. None
of them can show the asymmetry Decision 2 is about, because none of them has a declared attribute
to omit. The new fixture does: it asserts `"cohort" in units_rows[0]` and `"cohort" not in
measurements_rows[0]` from the same run's two sibling files, which is the asymmetry as a fact
about a real run rather than as a property read off `finalize`'s source. It also locates both
files by `rglob` (never a hardcoded step name or repeat label, since `run_a_project` derives both)
and asserts identical bytes across all five seed-repeat directories before reading one.

**The mutation (brief step 4), run and reverted:** changed `finalize`'s `measurements.parquet`
write (`src/publishable/artifacts.py`, the `if self._measurement_rows:` branch) to merge in the
roster's attributes the same way the `units.parquet` write does. Ran
`pytest tests/test_cli.py -k test_h5a_task2` against the mutant:

```
FAILED ... AssertionError: assert ['unit', 'mea...re', 'cohort'] == ['unit', 'mea...ent', 'score']
  Left contains one more item: 'cohort'
```

— the column-list assertion (`list(measurements_rows[0].keys()) == ["unit", "measurement",
"score"]`) is what catches it, exactly as intended: the mutant's `measurements.parquet` gains a
`cohort` column the fixture's absence assertion is written to reject. Reverted by editing the
`if self._measurement_rows:` block back to the single `self.write(...)` line; `diff` against a
pre-mutation copy of `artifacts.py` showed no difference, and the test was re-run and confirmed
PASS.

## What was grepped, and its scope

- `grep -rn "E-STEP-RETURN-TYPE" src/` (task 1, confirming the code paths documented) and
  `grep -n "def test_a_mixed_int_and_float\|def test_a_bool_and_int" tests/test_artifacts.py` plus
  `git log -S` on the first name (confirming both pins predate H5a).
- `grep -rn "measurements.parquet" tests/test_cli.py tests/test_artifacts.py` and
  `grep -n "\.keys()) ==" tests/test_cli.py tests/test_artifacts.py` (task 2, confirming no
  existing test in either file asserts `measurements.parquet`'s column list from a real run, and
  that the only prior fixtures are the direct-`StepIO` ones in `test_artifacts.py` using
  `_measuring_io`, which never declares a unit attribute).
- Both greps are scoped to `tests/test_cli.py` and `tests/test_artifacts.py` — the two files that
  exercise `StepIO`/`finalize` — not to `tests/` as a whole; no claim above is broader than that.

## Concerns

*(Corrected in Fix round 1 below — the original "None found" here was itself wrong: it sat above two Majors in the prose it was describing.)* What I checked, and its scope: `git diff --stat` confirmed both tasks stayed inside `docs/reference.md` plus one new test for task 2; a grep of `docs/reference.md`'s diff for `E-` identifiers confirmed no `§ Errors` row was touched (task 4's); a diff against a pre-mutation copy of `src/publishable/artifacts.py` confirmed no code outside the reverted mutation changed; and `git diff --stat` against `RESERVED_COLUMNS`/`E-UNITS-ATTR-COLUMN`-bearing files (`units.py`, `validate.py`) showed no touch. I did **not** independently re-trace every clause of the two new paragraphs against the code before writing "Concerns: None found" — which is exactly how the two Majors below survived into that sentence.

---

## Fix round 1

Review at `.superpowers/sdd/2026-08-21-artifacts-write-side/task-b2-review.md`, reviewed at `7686556`.
Both verdicts PASS, two Majors and five Minors, none blocking. Credited: the `measurements.parquet`
fixture is a real run, the only test in the suite that catches its own mutation, and it cannot pass
vacuously — the reviewer reproduced the mutation independently (full suite: 1 failed, 2844 passed,
this fixture the sole catcher).

All findings closed by editing `docs/reference.md` inside § The per-unit tables. `src/` and
`tests/` are untouched in this round — `git diff --stat` shows one file, `docs/reference.md`,
`6 insertions(+), 6 deletions(-)` after `ruff format`. No new mutation was applied to code, so no
new revert is owed; the two mutations from the original batch (the `.csv`/`.parquet` promote check
and `finalize`'s measurements-write merge) were already reverted and reconfirmed in the base report
above.

### Major 2 (closed first, because Major 1 depends on it) — the key-column clause was false

**Finding:** `docs/reference.md:985` said `units.parquet`'s unit-key column sits "under the name
`data.units.key` gives it" — false; the column is literally `unit` regardless of what
`data.units.key` names in the source config.

**Changed:** deleted the four-word clause rather than rewriting it (house rule: prefer deleting a
claim to rewriting it). The sentence now reads: *"`units.parquet`'s columns are the unit key, then
every declared attribute, then every key any row recorded — the union, with a column absent from a
row reading as null."*

**Verified by, independently, the same three ways the review named:**
1. **A real run** through `run_a_project` with `unit_attributes=["cohort"]` and the default roster
   (`data.units.key: patient_id` is what `generate_experiment` materializes) — `units.parquet`'s
   first column is `unit`, holding values `p1`, `p2`, …, never a column named `patient_id`. This is
   the same run this batch's own task 2 fixture already produces; re-read rather than re-run.
2. **A direct `StepIO`/`finalize` probe**, run now: a `Unit(key="p1", ...)` recorded and finalized
   writes `{"unit": "p1", ...}` — confirmed with a fresh interpreter call against
   `src/publishable/artifacts.py`'s `_decode_parquet`.
3. **`finalize`'s own source**, read at `src/publishable/artifacts.py`'s `if self._rows:` branch:
   `columns = ["unit", *attribute_names, *recorded]` and `merged: dict[str, Any] = {"unit": key}` —
   `"unit"` is a hardcoded literal, not `units_decl.get("key")` or anything derived from it. There is
   no code path from `data.units.key`'s value to a column name.

**The lesson, carried as asked:** Major 1's claim ("that is the *one* way the two files' column
sets differ") presupposes that the two files agree on how the unit-key column is named, so it can
speak of a single remaining difference. That presupposition is exactly Major 2's clause — and it was
false. Had the key column genuinely been named by `data.units.key` per the original sentence, the
premise Major 1 needed (*"the two files share their key-column naming, so whatever they share and
whatever they don't is now down to one axis"*) would still not make "one way" true, because
`measurement` is a second, independent difference the same paragraph names one clause earlier
regardless of what the key column is called. So the two Majors are not a simple chain where fixing
one fixes the other — each is false on its own terms — but Major 2's falsehood is what let Major 1's
overclaim go unnoticed on a first read: a reader (and the implementer) checking "is this the *one*
difference?" against a mental model where the key-naming clause is also true finds fewer live
differences to count than a reader working from the code. **Two false claims sitting next to each
other are harder to catch than either alone, and the fix is to trace each clause to the code
directly — `finalize`'s literal `"unit"`, the fixture's own two column lists — rather than to let
one clause vouch for its neighbour.**

### Major 1 — "that is the one way the two files' column sets differ" undercounted

**Finding:** the same real run's own two files are `["unit", "measurement", "score"]` and
`["unit", "cohort", "score"]` — two differences (the declared attribute, and the `measurement`
column itself, which the same sentence names one clause earlier as `measurements.parquet`'s own
second column), not one.

**Changed:** deleted *"That is the one way the two files' column sets differ, and"*, keeping the
ground (which the review confirmed sound): *"`measurements.parquet`'s columns are `unit`,
`measurement`, then every key any measurement row recorded — the union, exactly as `units.parquet`'s
recorded columns are, but with **no declared attribute** among them. It is deliberate rather than an
omission: …"*

**Verified by:** re-reading the task 2 fixture's own two asserted column lists
(`tests/test_cli.py`, `test_h5a_task2_measurements_parquet_carries_no_declared_attribute`) —
`["unit", "cohort", "score"]` and `["unit", "measurement", "score"]` — which is the same real run
the review re-ran. No new run was needed; the fixture already carries the two-difference fact, and
the deleted sentence had simply not been checked against it before this round.

### Minor 1 — the disjointness paragraph's count, and its guard's scope

**Finding:** *"the three groups of columns any per-unit table can hold — the unit key, a declared
attribute, and a recorded key"* undercounts `measurements.parquet`, whose three groups are `unit`,
`measurement`, and a recorded key (no attribute group at all) — a fourth name, `measurement`, is
what the guard actually protects there. The sentence's scope ("any per-unit table") was also wider
than the guard it names ("`io.record`'s `measurement=` branch" only refuses column names for the
call that goes through it).

**Changed:** rescoped the sentence to `measurements.parquet` specifically: *"`measurements.parquet`'s
three column groups — `unit`, `measurement`, and a recorded key — never collide: `io.record`'s
`measurement=` branch refuses a recorded key named `unit`, one named `measurement`, and one shadowing
a declared attribute, each `E-STEP-KEY-COLLISION`, so its column set above is always a plain
concatenation rather than a union that has to resolve a clash."* Did not touch the plain branch's
still-live asymmetry (a plain `io.record` column named `measurement` writes unrefused today) — that
is Decision 9 / task 7's, as the review itself says, and no sentence here now claims otherwise.

**Verified by:** re-reading `src/publishable/artifacts.py`'s `record` method — the `measurement=`
branch's three `E-STEP-KEY-COLLISION` raises (`unit`, `measurement`, and the declared-attribute
collision check) are the only guards the sentence now cites, and the plain branch (below it in the
same file) has no `measurement`-name guard, confirmed by reading rather than assumed.

### Minor 2 — the promote clause's unstated exception

**Finding:** an `int` above `2**53` beside a `float` does not promote cleanly; `pyarrow` raises its
own uncoded `ArrowInvalid` rather than `E-STEP-RETURN-TYPE`.

**Changed:** added to the promote bullet: *"**Not stated as absolute:** an `int` above `2**53` (a
nanosecond timestamp is the realistic case) beside a `float` in the same column does not promote
cleanly — `pyarrow` raises its own `ArrowInvalid`, uncoded, rather than `E-STEP-RETURN-TYPE`, and the
one execution that reached it fails rather than the run stopping;"* — qualifying the clause in place
rather than filing it, since the containment (one execution fails, not the run) is itself part of
what a reader needs to know and belongs beside the rule it qualifies.

**Verified by, independently reproducing the review's own finding:** a fresh interpreter call —
`_encode_parquet([{"v": 2**53 + 1}, {"v": 2.5}])` — raised `pyarrow.lib.ArrowInvalid: Integer value
9007199254740993 is outside of the range exactly representable by a IEEE 754 double precision value`.
Read `runner.py`'s per-execution `except Exception` to confirm the containment claim (one execution
marked failed, not a stopped run) before writing it, rather than repeating the review's characterization.

### Minor 3 — the premise/conclusion scope mismatch

**Finding:** the sentence's premise ("every value a step records") is narrower than its stated
conclusion ("what one row's cell holds is always `bool`/`int`/`float`/`str`/`None`"), since a
declared attribute's value is not (yet) coerced — a resolver-yielded structural attribute publishes a
list cell today. Symmetrically, the clause list's stated scope ("every row that recorded it") is
narrower than what `_check_column_types` actually checks (every column, attributes included).

**Changed:** *"Every value a step **records** already passes through the same scalar coercion
`io.record`'s values take, so a recorded cell always holds `bool`, `int`, `float`, `str`, or `None`
by the time a column is built from it. A declared attribute's value is not run through that coercion
today — a resolver may yield one that is not a scalar at all, and this section does not close that
gap — but the check below runs over every column alike, attributes included, and the rule for what a
*column* may hold, across every row that carries it, is:"*

**Verified by:** a fresh interpreter call building a `UnitList` with `Unit(attributes={"tags": [1,
2]})`, recording a plain numeric column, and finalizing — the written `units.parquet` row was
`{'unit': 'p1', 'tags': [1, 2], 'score': 1.0}`, confirming the list cell publishes uncoerced today.

### Minor 4 — the unreachable empty-row clause, and the unpinned reverse promote order

**Finding (closed):** *"an empty row set writes an empty table and raises nothing"* is true of the
encoder but unreachable for either per-unit table, since `finalize` guards both writes
(`if self._rows:` / `if self._measurement_rows:`) and never calls the encoder on an empty row set for
`units.parquet` or `measurements.parquet`.

**Changed:** *"an empty row set writes an empty table and raises nothing — true of the encoder
itself, and unreachable for either per-unit table: `finalize` writes
`units.parquet`/`measurements.parquet` only when there is at least one row to put in it, so this
clause describes `.parquet`'s general behavior, never something a real run's per-unit table does;"*

**Verified by:** reading `src/publishable/artifacts.py`'s `finalize`, confirming both guards by line
(`if self._rows:` before the `units.parquet` write, `if self._measurement_rows:` before the
`measurements.parquet` write) rather than trusting the review's citation.

**Finding (not closed — reason below):** the *"in either declaration order"* half of the promote
clause is pinned by a shipped test in one direction only
(`test_a_mixed_int_and_float_column_promotes_to_float_deliberately` asserts `[{v:1},{v:1.5}]`); the
reverse order is true (confirmed by running `_encode_parquet([{"v": 1.5}, {"v": 1}])` and decoding
both values as `float`) but has no shipped regression test. **Not closed here**, because this
batch's scope is documents plus the one task 2 fixture — adding a new pin is task 11's fixture-W
territory, not a documents fix, and the doc's own clause is accurate as stated (it does not claim
the reverse order is pinned, only that it round-trips). Left for task 11 to pick up; noted here so
it is not silently dropped.

### Minor 5 — "Concerns: None found"

**Finding:** the base report's closing line was wrong — two Majors lived in exactly the prose it
described clause by clause.

**Changed:** replaced the zero-count sentence with what was actually checked and its scope (see the
edited § Concerns above), and left a note there pointing at this section rather than re-asserting a
count.

### Gates and suite after this round

`ruff format .` (93 files left unchanged after the edit), `ruff check .` (all checks passed),
`ruff format --check .` (93 files already formatted), `mypy` (52 source files, no issues), and
`pytest` run directly in the foreground: **2845 passed, 1 skipped, 2 xfailed** — unchanged from
before this round, since no test or code moved. `git diff --stat` confirms the only file touched is
`docs/reference.md`.

### Consistency passes

**Mechanical**, run fresh over the edited section: no trailing whitespace/tabs (checked over the
whole file), no duplicate anchors (checked over every heading in the file with fenced blocks
skipped), and every link/`#anchor` this section already used still resolves (`#steps-and-artifacts`,
`#templates-where-parameters-are-defined`, `#what-isnt-a-repeat`, `#units-the-thing-being-measured`
all still point at existing headings — no heading text changed). **Proven able to fail**: injected a
trailing space and a duplicate `### The per-unit tables` heading into a scratch copy, confirmed both
were caught, then discarded the scratch copy (the real file was never touched by the probe).

**Cross-document**, swept by name over `README.md`, `docs/design-principles.md`,
`docs/experimental-designs.md`, `docs/reference.md`, `docs/feasibility-llm-growth-studies.md`, and
`CLAUDE.md`, filtering the file list rather than the grep output: `grep -n "the one way the two
files"` and `grep -n "under the name .data.units.key. gives it"` both return zero hits everywhere,
confirming the two deleted claims left no echo. **Sweep proven able to fail**: the same grep command
against a known-present string (`"carried through"`) returns real hits in `docs/reference.md`
(lines 999 and 1696), so an absent string is a true negative rather than a broken grep.

### What I did not close

Only the reverse-order promote pin (Minor 4's second half), for the reason stated there: it is a
test-coverage gap task 11 owns, not a documents defect, and the doc's own text does not overclaim
what is pinned. Everything else in the review — both Majors and the other four Minors — is closed
above.
