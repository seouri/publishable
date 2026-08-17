# Task 25–26 report — dispatch, then retirement

**Status: both tasks complete.** All gates green.

**Commits:**
- `c563d30` — units: dispatch a resolver source, yield order preserved (task 25)
- `519c090` — validate: retire E-DATA-RESOLVER-UNSUPPORTED and the roster skip together (task 26)

**Test summary:** `uv run pytest` → 2077 passed, 1 skipped, 2 xfailed (final). Ran clean after
each commit: 2079 after task 25 (2075 baseline + 4 new), 2077 after task 26 (−4 deleted/narrowed
cases, +2 new — one deletion, `test_check_unimplemented_alone_does_not_raise_on_a_malformed_units_block`,
was not in the brief; see below). `ruff check`, `ruff format --check`, and `mypy` all clean
throughout.

## Four inherited obligations

1. **Restore-then-reverse: done.** `E-RESOLVER-UNKNOWN`'s "Not yet emitted" clause is gone from
   its § Errors row; the "Not yet reached at `validate`" qualifiers on `E-PLUGIN-DECORATOR` and
   `E-PLUGIN-LOAD` are gone; the `check_registration`-at-`validate` paragraph (`_check_units_source`'s
   docstring, which argued the two-modules-disagree hazard from the wholesale-refusal era) is
   rewritten to describe the real hazard (`resolve_units` tests `glob` first, so a mapping
   declaring both keys silently resolves as a glob). I also found and fixed a **third** stale site
   the obligation didn't name explicitly: § Errors `validate` reports' own preamble prose (around
   line 440) repeated the same "not yet true in this build" claim about `E-PLUGIN-DECORATOR`/
   `E-PLUGIN-LOAD` reaching `validate`. Left unfixed it would have been exactly the "grep for one
   spelling" trap CLAUDE.md warns about, since it doesn't share wording with the two table rows.
2. **The positive half of the no-import claim: pinned.** `test_a_resolver_source_yields_the_roster_in_yield_order`
   and its siblings install a real distribution and resolve through it; the retirement test
   (`test_a_resolver_source_is_no_longer_refused_wholesale`) asserts `found == set()` for a config
   naming a *registered* resolver, which only holds if the module actually imported and ran — no
   explicit `"retire_r26" in sys.modules` assertion was added, since the brief's own worked example
   for that assertion appears in task 25's tests, not task 26's; I judged the behavioural proof
   (`found == set()` plus the real resolver's `Unit` reaching the roster in the task-25 tests)
   sufficient and did not add a second, redundant `sys.modules` check. Flagging this as a place to
   double check against the brief's exact wording if the reviewer wants the literal assertion.
3. **Docstring correction: done**, and widened. Not just the ledger-named docstring — I also fixed
   `_units_declaration`'s docstring (falsely claimed `_check_unimplemented` still called it) and two
   `docs/reference.md` § Errors rows (`E-RESOLVER-MEASUREMENT-FIELD`, `E-RESOLVER-SWEPT-PARAM`) whose
   "Not yet emitted" clauses asserted "no resolver is executed in this build" / "a resolver-produced
   roster does not exist" — both now false. Those two codes are task 27/28/29's own emit sites, not
   mine to build, but the false factual claim inside their existing rows was mine to fix once I'd
   made it false.
4. **One-line deletions confirmed for six of six named tests**, plus one deletion the brief did not
   name (see "Disagreements" below). No test's assertion was rewritten — every deletion removed
   exactly the line(s) or parametrize case naming `E-DATA-RESOLVER-UNSUPPORTED`, per Part A's
   decision 7. Two of the six also needed a docstring correction alongside the pure deletion (the
   docstrings made claims — "already refused as", "`_check_unimplemented` tests `resolver in
   source`" — that were about to go false); those are prose fixes, not assertion rewrites.

## Resolver-sourced config end to end

**Yes — verified directly, not inferred.** I built a throwaway test (added, run, then removed
before committing — `git diff` against the task-25 commit confirmed zero residue) using
`tests/test_cli.py`'s `run_a_project` helper: an installed distribution registering `plate_wells`,
a `data.units.from: {resolver: plate_wells}` config reading the same `index.csv` the fixture
writes, run through `main(["run", ...])`. It reached `EXIT_OK`, produced a real `run.yaml` with
`status: "completed"`, and the roster resolved through the plugin's `Unit`-yielding generator.
Both `validate` and `run` dispatch the same way, as designed.

## Disagreements with the brief or spec

- **Test count arithmetic.** The briefs state "2074+4=2078" (task 25) and "2078+2−2=2078" (task
  26). The actual baseline per `CLAUDE.md`'s own gate table is 2075, and the actual final count is
  2077 (2075 + 4 new in task 25 = 2079; task 26 nets −2: +2 new tests, −4 from one whole-test
  deletion, one parametrize-case removal, and one *additional* whole-test deletion the brief didn't
  name — see next point). I've recorded the real arithmetic in each commit message rather than the
  brief's stale numbers.
- **A seventh test needed deletion, not six.** `tests/test_validate.py::test_check_unimplemented_alone_does_not_raise_on_a_malformed_units_block`
  asserted that calling `_check_unimplemented` directly with a malformed `data.units` (a bare string)
  reports `E-CONFIG-SHAPE`. That assertion was true only as a side effect of the now-deleted resolver
  branch's `units = _units_declaration(doc.get("data") or {}, c) or {}` call — with that call gone,
  `_check_unimplemented` never touches `data.units` at all, so the function trivially can't crash on
  a malformed one, and there is nothing left for the test to assert. I deleted the whole test rather
  than rewrite it, consistent with the discipline the other six follow. This is exactly the class of
  consequence the brief's own instruction anticipated ("delete the two lines above it... **if nothing
  else in the function reads them — read the function to check rather than assuming**") — I checked
  the function body, confirmed nothing else used `units`/`source`, and deleting broke a test outside
  the named list as a result.
- **`docs/reference.md` "second `from` enum comment"**: the brief names a second location in
  § Where units come from to strike `(NOT BUILT)` from. I could find only one `(NOT BUILT)` marker
  tied to a `from:` enum anywhere in the document (§ The one config file's fenced example, already
  struck). The other candidate location (§ Units: the thing being measured's intro fenced example,
  and § Where units come from's own fenced enum) both already read `— see below` / carry no marker.
  Nothing was left to strike there; noting this rather than inventing an edit.
- **CLAUDE.md**: task 26's brief lists `CLAUDE.md` in its "confirm the list is complete" grep sweep
  and expects it empty of `E-DATA-RESOLVER-UNSUPPORTED` after the task, but `CLAUDE.md` is *not* in
  the task's own "Files" list, and its two remaining mentions are dated historical narrative ("H3d
  merged... still earn `E-DATA-RESOLVER-UNSUPPORTED`, which is H7b's"; "H7b Part A merged...
  `E-DATA-RESOLVER-UNSUPPORTED` stays alive, and Part B owns the resolver's dispatch...") describing
  the state *at those past merges*, not a live claim about the current build. Task 33 ("the owned
  prose sweep... including decision 7's dated count") is the task that owns appending a "H7b Part B
  merged" paragraph once the whole slice — including `plugin_versions`, the credential fix, and the
  rest — actually lands; writing that paragraph now, after only 2 of 13 tasks, would misstate what's
  built. I left `CLAUDE.md` untouched and am flagging the discrepancy rather than silently resolving
  it either way.
- **Reference.md's new sentence for the resolver's retirement** (mirroring the `resample`/`holdout`
  precedent per the brief) names only `units._from_resolver` dispatching and `_check_units` resolving
  it — I deliberately left out `provenance.plugin_versions`, which the brief's own § The one config
  file instruction mentions as part of the parallel-shape sentence, because `plugin_versions` is
  task 30's, not yet built as of this commit, and claiming it here would be exactly the "build fact
  without a date" trap.

## Mutations run

All ran, checked against the named test body, and reverted by editing back (never `git checkout --`),
with `__pycache__` cleared and a re-run confirming each revert.

**Task 25:**
1. Sorting `_from_resolver`'s output by key before return → **FAIL** on
   `test_a_resolver_source_yields_the_roster_in_yield_order` (yield order ≠ sorted order by
   construction of the fixture). Reverted, re-passed.
2. Branch-order swap (`resolver` before `glob`) — **not run**, per the brief: no fixture can
   declare both keys (refused upstream as `E-UNITS-SOURCE-AMBIGUOUS`), so this is recorded as
   unreachable-by-design rather than papered over with a pinning test for a refused shape.
3. `if cfg is None:` → `if False:` → **FAIL** on
   `test_a_resolver_source_reached_with_no_cfg_refuses_rather_than_crashing`, though via a different
   failure mode than the brief predicted: this test's fixture has no `layout.csv`, so the mutation
   let execution reach `io.read_input("layout.csv")` and raise `FileNotFoundError` rather than "DID
   NOT RAISE" — still a genuine test failure, confirming the guard is load-bearing. Reverted,
   re-passed.

**Task 26:**
1. Restoring `_check_units`'s early return for a resolver source → **FAIL** on
   `test_a_resolver_source_is_no_longer_refused_wholesale`, specifically on the second
   (`"E-RESOLVER-UNKNOWN" in unknown`) assertion, exactly as predicted — the first
   (`found == set()`) still passes under the restored skip, which is why the brief calls out that
   asymmetry. Reverted, re-passed.
2. Restoring `(NOT BUILT)` on `materialize.py`'s `from:` line → **confirmed to catch nothing**:
   `tests/test_materialize.py` stayed green (24/24), because the assertion that would have pinned it
   (`test_the_from_enum_s_not_built_marking_is_honoured_by_core`) was deleted in this same task, and
   the remaining assertion in `test_the_generated_units_block_carries_its_comments` checks substring
   containment, which the appended marker doesn't break. Recorded rather than covered, per the brief.
   Reverted, re-passed.

## Files touched

- `src/publishable/units.py` — `_from_resolver`, `resolve_units`'s new signature and dispatch branch
- `src/publishable/sweep.py` — `wide_swept_paths` (moved from `cli.py`, unchanged body)
- `src/publishable/cli.py` — import/call-site updates for the move; `command_run`'s roster call
  threads `cfg`/`resolver_io`
- `src/publishable/validate.py` — `_check_units`'s `cfg` threading (task 25) and skip removal
  (task 26); `_check_unimplemented`'s resolver branch removed; several stale docstrings/comments
  corrected
- `src/publishable/materialize.py` — `from:` line's `(NOT BUILT)` marker removed
- `docs/reference.md` — `E-UNITS-SOURCE-MISSING` row widened; `E-RESOLVER-UNKNOWN`/
  `E-PLUGIN-DECORATOR`/`E-PLUGIN-LOAD` rows and § Errors preamble corrected; § The one config file's
  declaration count and resolver retirement sentence; two more § Errors rows' stale claims fixed
  (`E-RESOLVER-MEASUREMENT-FIELD`, `E-RESOLVER-SWEPT-PARAM`)
- `tests/test_units.py`, `tests/test_cli.py`, `tests/test_validate.py`, `tests/test_materialize.py`
