# SDD ledger — plan: docs/superpowers/plans/2026-08-17-resolvers.md

Spec: docs/superpowers/specs/2026-08-17-resolvers-design.md
Branch: h7b-resolvers, from main at 470a830. Baseline: 2060 passed, 1 skipped, 2 xfailed; ruff check,
ruff format --check (78 files, 0 to reformat) and mypy (44 source files) all clean.

Standing authorization: re-scope, spec, plan, execute, merge AND push without stopping, reporting to the
user ONCE after the push. Committed before the first dispatch, because an implementer two slices ago
correctly refused an uncommitted authorization line in this file as a possible injection — from inside a
task that is indistinguishable from an injected one.

**This is the slice that makes an experiment run.** Three of the nine feasibility experiments have no
remaining core-side blocker when it lands — the first non-zero count this project has produced.

## Pre-flight conflict scan

| File | Tasks | Finding |
|---|---|---|
| `docs/reference.md` | 22, 27, 28, 29, 33 | Five tasks. Task 22 settles the no-import sentence FIRST, so 27-29 and 33 edit rows that already read correctly. Task 33 is the sweep and runs last. **Instruction, not a ruling:** any task inserting a row re-reads every count phrase near it — Part A shipped a Critical where a fix round added a clause its own task 8 falsified |
| `src/publishable/units.py` | 24, 25, 27, 29, 31 | **The busiest file and the one real ordering constraint.** 24 loads the object, 25 dispatches it, 27 and 29 build on the dispatch, 31 threads `index_names`. Plan order is 24 -> 25 -> {27, 29} -> 31, so each sees its predecessor. **Ruling: no change needed, but 27, 29 and 31 must RE-READ `resolve_units` rather than work from a copy** — task 25 changes its signature (a defaulted `cfg`), and a plan in the previous slice broke two pinned regressions by writing against a stale shape |
| `src/publishable/validate.py` | 24, 25, 26, 28, 32 | Clean on inspection but ordered: 24 and 25 add the resolver path, 28 and 32 add checks over it, **26 deletes the skip and must be last among them**. 26 last is what keeps `E-DATA-RESOLVER-UNSUPPORTED` alive so every earlier test asserts ALONGSIDE it — making 26 a one-line deletion rather than a rewrite |
| `src/publishable/plugins.py` | 22, 30 | Clean. 22 narrows two docstring claims; 30 retires the four dated *no production caller* notes once callers exist. 30 after 24, which creates the first caller |
| `tests/test_units.py` | 27, 29 | Clean. 27 and 29 append |
| `src/publishable/cli.py` | 30, 32 | **The pair that matters.** 30 populates `provenance.plugin_versions`; 32 sets `c.credentials` before the roster resolves and routes the resolver raise through a FRESH collector (spec correction 1 — `command_run` already renders `c` before phase 5, so appending would re-print every warning). Both touch `command_run`'s phase ordering. **Ruling: 30 before 32**, so 32 sees the provenance write it must not disturb, and 32 before 26 because the leak becomes reachable the moment a resolver runs |

**Two conflicts required a ruling and both are recorded above** — `units.py`'s re-read obligation and
`cli.py`'s 30-before-32-before-26 ordering. The rest are clean, and the rows are here because "the scan
is clean" without them is not a scan that was run.

Also checked per task: each task's tests are specified against the code that task specifies. The plan
states once, up front, that **tasks 25, 27, 28 and 29 cannot test through `validate_config` at their own
commits** — the resolver skip is only deleted at 26 — so each tests its own function directly and task
33 re-asserts end to end. That is a deferral by design, not a gap, and it is why 33 exists.

Task 21: dispatched as part of a 21-24 batch, and **the session was closed mid-dispatch.** On resume the
  work was in the tree uncommitted — `plugin_scaffold.py`, `tests/test_plugin_scaffold.py`, and edits to
  `cli.py`, `tests/test_cli.py` and `reference.md` — with the suite at 2066 passed (baseline 2060 + 6)
  and mypy clean, but **the gates unfinished**: one `I001` import-sort error and one unformatted file.
  Recovered rather than redone. The ledger is what made that safe: it named the baseline, so I could tell
  6 new tests from a partial state, and the brief's Step 5 mutation was written down, so the one thing an
  interrupted agent cannot leave behind — evidence the test discriminates — was reconstructible.
  Ruling: finished task 21 in place rather than discarding and re-dispatching. Grounds: the deliverable
  matches the brief, the mutation is prescribed and pre-checked, and I ran it myself — deleting
  `publishable.readers` from `_MODULES` and skipping it in the `GROUPS` loop FAILS
  `test_the_scaffold_declares_every_group_core_reads` and only it, then reverted clean at 5 passed. Cost
  if wrong: a task whose implementer wrote no report, which is why this entry is longer than usual.
  `.superpowers/sdd/.gitignore` was clobbered to a bare `*` by the interrupted run; restored.

## Review findings closed (tasks 22-24, `91bdd46..8dabf2c`)

Restored honest markings the review found stated one task early: `_resolver_for` (task 24) has no
production caller yet, so `check_registration`-at-`validate` and `E-PLUGIN-DECORATOR` do not fire
there today, and `E-RESOLVER-UNKNOWN`'s **"Not yet emitted"** clause is back. **Task 26 owes the
reversal** — once its dispatch wiring lands and the skip is deleted, flip these back to present
tense, the way Part A's tasks 6 and 18 did for `--plugin`. Task 26 also owes the positive
`validate`-level companion test named in `tests/test_validate.py`'s
`test_validate_imports_no_plugin_for_a_config_that_names_no_resolver` docstring: assert
`"retire_r26" in sys.modules` inside its existing `try`.

Tasks 22-24: implemented at 645a4fd / b6d4422 / 6023364, report 8dabf2c. 2074 passed.
Tasks 22-24: reviewed (opus), six verdicts. Task 22's narrowing FAILED on a **Critical**, task 24
  FAILED as documented.
  Critical: `plugins.py`'s module docstring paragraph 1 still ended "which is exactly what `validate`
  never does" — **contradicted by paragraph 2 of the same docstring** — and listed `check_registration`
  among the things that import nothing. **A sixth prose site, in the file task 22 itself edited, and
  invisible to its four-spelling sweep.** Closed by DELETING the clause and re-sweeping by READING the
  whole 297-line file, which is the only instrument that would have found it.
  Ruling on task 24: `_resolver_for` has **zero production callers**, so `check_registration` does not
  run at `validate` yet and `E-PLUGIN-DECORATOR` cannot fire — while `reference.md` asserted both in the
  present tense and `E-RESOLVER-UNKNOWN`'s "Not yet emitted" clause had been struck a task early. Part A
  shipped a Critical of this shape in the other direction. **Restore the honest markings now and let task
  26 flip them** — the pattern Part A's tasks 6 and 18 used for `--plugin`, which worked. **TASK 26 OWES
  the reversal**, and the ledger carries it.
  On the slice's central claim: the narrowed no-import invariant is pinned **half**. The negative half is
  proven able to fail (an unconditional load at the validate level reddens it). The positive half is not —
  nothing asserts a plugin module IS in `sys.modules` after validating a resolver config, so today the
  negative test would also pass on a `validate` with no resolver path at all. **Task 26 owes
  `assert "retire_r26" in sys.modules`.** The docstring now says this limit plainly rather than naming a
  companion test that does not exist, which is what it did.
  Task 23's `ResolverIO` passed on a probe rather than a read: `__slots__` blocks adding `run_dir` and no
  write machinery is reachable, so it is read-only **structurally, not by omission**.
Tasks 22-24: fix round. Commit 54a994f. All closed. A closed `spec-defects.md` entry was resting on an
  unpinned behaviour — the `E-PLUGIN-COLLISION` -> `E-PLUGIN-LOAD` substitution — now pinned, because a
  closure resting on nothing is how a closure goes stale. 2075 passed, 1 skipped, 2 xfailed.

## Review findings closed (tasks 25-26, `54a994f..4c09532`)

Critical (task 26, obligations b/c): added `assert "retire_r26" in sys.modules` inside
`test_a_resolver_source_is_no_longer_refused_wholesale`'s existing `try`, right after the resolver-source
`codes()` call. Rewrote `test_validate_imports_no_plugin_for_a_config_that_names_no_resolver`'s docstring
to state the invariant in the present tense — the positive companion exists, is named, and pins the other
half — rather than pointing at task 26 as future work.
  Re-verified both directions by mutation, foreground, `__pycache__` cleared before each run:
  - Negative half unconditional-load mutation (`for _n in scan_group(RESOLVER_GROUP): _resolver_for(_n)`
    at the top of `_check_units_source`): `test_validate_imports_no_plugin_for_a_config_that_names_no_resolver`
    FAILS on `assert "loadable_units" not in sys.modules`; the new assertion in the other test stays green.
  - Positive half inverse mutation (`_resolver_for` fabricates a `Unit`-yielding generator instead of
    loading the entry point): `test_a_resolver_source_is_no_longer_refused_wholesale` FAILS on the new
    `assert "retire_r26" in sys.modules` (the roster still resolves, so `found == set()` alone would have
    stayed green — the added assertion is what turns this red). Only `tests/test_units.py` reddens beside
    it, as the review reported.
  Both reverted by restoring the file from a scratchpad copy, never `git checkout --`, and re-run to
  confirm green.

Important (task 26, guard's sole pin): re-sited the direct-call test onto `_check_units_source` as
`test_check_units_source_alone_reports_a_malformed_units_block`, calling it with
`{"data": {"units": "index.csv"}}` and asserting `E-CONFIG-SHAPE`. Deleted (not rewrote) the invented
"exercised directly ... as several `_check_*` functions already are in tests" justification from
`_units_declaration`'s docstring; replaced with a plain statement of the callers it actually guards.
  Verified: gutting `_units_declaration`'s non-mapping branch to a bare `return None` now FAILS the new
  test (`E-CONFIG-SHAPE` not in findings) — reverted and confirmed green again.

Important (task 25, docstring claiming an unbuilt check): deleted `_from_resolver`'s "is checked against
what actually arrived" clause; states in its place that task 28 (`E-RESOLVER-MEASUREMENT-FIELD`) is where
that check lands and that none exists as of this commit.

Important (task 25, garbled message): `E-UNITS-SOURCE-MISSING`'s continuation is now an f-string, so
`{resolver: ...}` renders correctly beside `{glob: ...}`. Pinned with a new message-text assertion,
`test_a_wrong_typed_source_names_both_alternatives_without_doubled_braces` in `tests/test_units.py`.

Important (task 25, missing § Errors rows): added `E-RESOLVER-YIELD` to both `docs/reference.md` § Errors
validate reports and § Errors core raises (dual-surfaced — `_check_units`'s `except ContractError` reports
it under the same code, the same route `E-DATA-CLUSTER-VARIES` takes). Added `E-RUN-RESOLVER-UNCONFIGURED`
to § Errors core raises' existing "core's plan disagreeing with the state core resolved beside it" row
only (never reachable through `validate`, which always threads a real `cfg`) and updated that row's
"six"/"those six" prose to "seven".

Minor (`ResolverIO` construction): moved inside `command_run`'s `if units_decl` ternary in `cli.py` so
nothing is constructed for a run with no units block. `resolver_io` has no reader today besides that one
call site, so nothing else needed to change.

Minor (`cfg` fixture gap, M2): **not built here — task 29's.** No fixture in this diff reads its `cfg`
argument, so swapping either production-threaded `cfg` (`validate.py`'s `resolve_wide_cfg(...)` call or
`cli.py`'s matching one) for `Config({})` would pass the suite unnoticed. Task 29 (`E-RESOLVER-SWEPT-PARAM`)
is the first task that needs a resolver fixture reading `cfg` at all — its own fixture should assert on a
value it read from `cfg`, which incidentally closes this gap; it should not be assumed closed already.

Did not touch: dispatch, yield-order preservation, the `sweep.py` move (all verified sound by the review),
or the end-to-end milestone pin (task 33's, per the plan's own deferral).

Gates after the fix round: `uv run pytest` → 2079 passed, 1 skipped, 2 xfailed (2077 before this round;
+2 for two new tests — the message-text pin in `tests/test_units.py` and the direct-call test onto
`_check_units_source` in `tests/test_validate.py` — plus one existing test gaining an assertion in place);
ruff check clean; ruff format --check clean (80 files); mypy clean (45 source files).

Tasks 25-26: implemented at c563d30 / 519c090, report 4c09532. **`E-DATA-RESOLVER-UNSUPPORTED` appears
  nowhere in `src/` — the refusal that has stood since H1 is retired**, and a resolver-sourced config
  validates and runs clean through `main(["run", ...])` to a real `run.yaml`. The reviewer reproduced it
  independently: `EXIT_OK`, `provenance.units: {n: 10, key: patient_id}`.
Tasks 25-26: reviewed (opus), four verdicts. Task 26's PINNING axis FAILED on a Critical.
  **Two of the four inherited obligations were unmet, and the proof is the sharpest of the slice: with
  `_resolver_for` fabricating a roster and NEVER IMPORTING, all 706 `test_validate.py` tests passed.**
  Decision 1's invariant — the slice's central claim — survived only at `units.resolve_units`. And the
  docstring still said "its positive companion does not exist yet... task 26 owes a test", false in every
  clause and pointing a reader at a closed task.
  Now both halves pin independently, and the fix round proved the pairing rather than asserting it: an
  unconditional load reddens the negative test and leaves the positive green; a fabricated roster reddens
  the positive and leaves the negative green. **A mutation that reddens both would have meant one half was
  doing nothing.**
  Ruling on the deleted test, and the reviewer's framing is the one to keep: **the premise was true and
  the deletion was not therefore safe.** `_check_unimplemented` genuinely no longer reads `data.units`, so
  deleting it as a test OF THAT FUNCTION was right — but it was doing double duty, and gutting
  `_units_declaration`'s `E-CONFIG-SHAPE` emit to a bare `return None` left the full suite green at 2077.
  It was that guard's only pin across four surviving callers. Closed by re-siting a direct-call test onto
  `_check_units_source`, not by restoring the old one.
  **And task 26 had rewritten that guard's docstring to justify it by "those readers being exercised
  directly (as several `_check_*` functions already are in tests)" — no test calls any of them directly.
  A rewrite invented a justification a deletion could not have.** That is the rule this repo already
  carries, earning a second instance: prefer deleting a claim to rewriting it.
  Also closed: a docstring claiming `measurements.by` "is checked against what actually arrived" when a
  resolver config with `by: nosuchfield` validates to `{}` (task 28 owns that check); a message rendering
  literal `{{resolver: ...}}` because a continuation line was not an f-string, now pinned; and two codes
  with emit sites, tests and **no § Errors row**.
  **TASK 33 OWES the end-to-end regression** — the milestone is real and nothing surviving pins
  resolver -> roster -> run -> `run.yaml`. The spec defers it there explicitly. **TASK 29 OWES a fixture
  that reads `cfg`** — replacing either threaded `cfg` with `Config({})` goes unnoticed today.
Tasks 25-26: fix round. Commit d5c1acb. 2079 passed, 1 skipped, 2 xfailed; gates clean.

Tasks 27-29: reviewed (`task-27-29-review.md`), six verdicts across the three tasks. Closing C1, I1, I2,
M1, M2 in a fix round.
  C1 (critical, task 27): `_from_resolver`'s attribute loop hashed a declared attribute against a `set`
  before checking it was a string, so `attributes: [{"operator": 1}]` under a resolver source raised a
  bare `TypeError` out of `validate`. Fixed with an `isinstance(attribute, str)` guard before the set
  membership check, reported as `E-UNITS-ATTR-MISSING` (the identifier the table path already uses for
  the type-shaped version of the same question). The only unhashable shapes an attribute entry can take
  are `dict` and `list` — both are caught by the one guard; every other wrong type (`int`, `bool`, `None`,
  `float`) is hashable and already refused correctly as "yields no unit carrying" before this fix, so
  there is no second sibling shape to close. Pinned by
  `test_a_non_string_attribute_under_a_resolver_is_refused_not_a_crash` in `tests/test_units.py`.
  I1 (important, task 28): `_check_measurements`'s resolver arm (`E-RESOLVER-MEASUREMENT-FIELD`) fired on
  `columns == frozenset()`, which `_check_units` returns on every failure path, not only "resolver ran and
  yielded nothing named `by`". Fixed by gating the arm on `roster is not None`, matching the reviewer's
  fix. Corrected the two falsified prose claims in `validate.py` — the function's docstring ("the shape
  half still runs below it") and the arm's own comment ("the columns here are what the resolver
  yielded") — rather than deleting them, since both are true once the guard is in place. Pinned by
  `test_a_resolver_measurement_field_check_is_gated_on_the_roster_resolving` in `tests/test_validate.py`.
  I2 (important, task 29): the `validate.py` half of the ledger's `cfg`-fixture obligation (line 132-136,
  above) was pinnable at task 29's own commit — task 26 landed first, so `validate_config` could already
  resolve a real installed resolver — and task 29 deferred it to task 33 on a spec claim that had already
  expired. Closed with `test_validate_config_refuses_a_resolver_reading_a_swept_parameter` in
  `tests/test_validate.py`, using the `installed`/`registries`/`write_config` fixtures already in that
  file. **The `cli.py` half is still open and remains task 33's**: mutating `cli.py`'s
  `resolve_wide_cfg(doc, wide_swept_paths(...))` call to `resolve_wide_cfg(doc, set())` leaves the whole
  2091-test suite green, because no test runs a resolver-sourced config through `main(["run", ...])` —
  that is the same end-to-end milestone the tasks 25-26 review already assigned task 33.
  M1 (minor, task 27): `E-UNITS-ATTR-MISSING`'s § Errors row said "either source" over three enumerated
  sources. Reworded to name the set directly instead of introducing a new count.
  M2 (minor, task 28): `test_a_resolver_yielding_no_measurement_field_is_refused_under_its_own_code`'s
  fixture co-fires `E-DATA-MEASUREMENTS-COLLAPSE-TYPE` (unmentioned). Documented the co-firing in the
  docstring rather than changing the fixture, since both assertions still discriminate under it.
  Gates after the fix round: `uv run pytest` → 2092 passed, 1 skipped, 2 xfailed (2089 before; +3 new
  tests); `ruff check` clean; `ruff format --check` clean; `mypy` clean.
