# Task 18 report: Retire `E-DATA-HOLDOUT-UNSUPPORTED`, and the five end-to-end pins

**Status:** done. **Commit:** `30376a1cc9bf4931b8845f169d99bd47b786d90f`.

**Test summary:** `uv run pytest` — 1953 passed, 2 xfailed (was 1950 passed, 2 xfailed
before this task). `uv run ruff check .` clean. `uv run mypy` clean (42 source files).
`uv run ruff format --check .` reports the same kind of pre-existing repo-wide
reformat backlog it reported before this task (71 files on `HEAD`, 63 after —
fewer, not more; no file I touched was bare-reformatted, per instruction).

## What changed

- `src/publishable/validate.py`: `_check_unimplemented`'s `for field, code in (...)`
  loop is gone (it held exactly one entry, `("holdout", "E-DATA-HOLDOUT-UNSUPPORTED")`),
  and the surrounding commentary is rewritten to state what is true now — no
  `data.units` sub-field is refused wholesale any more, only a `resolver` source
  remains in that state, and `holdout` is checked for real by `_check_holdout`.
- `src/publishable/envelope.py`: one stale comment fixed (claimed `E-DATA-HOLDOUT-UNSUPPORTED`
  "still refuses the block at this commit").
- `docs/reference.md`: § The one config file now says "two declarations ... not yet
  built" (was three), lists only `{resolver: <name>}` and `statistics.null_test`,
  and states `data.units.holdout` left the list this slice. The `holdout: null`
  line's `NOT BUILT` marker and comment are replaced with a shape comment matching
  `measurements`'s sibling line. The stale "`.holdout` inherits the same treatment
  when its slice lands" sentence is replaced with a statement that it has landed,
  closed one level in at its own five keys. § Errors already had full rows for every
  `E-DATA-HOLDOUT-*` code and correctly no row for `-UNSUPPORTED` (that table never
  carried one) — nothing to change there. § Validation and § A fixed holdout split
  were already fully present-tense/built from tasks 1–17; no stale markers found.
- `tests/test_validate.py`: 28 total mentions of `E-DATA-HOLDOUT-UNSUPPORTED` found
  by `grep -n` (23 `assert` lines, 5 comment/docstring mentions); all removed except
  one new `assert "E-DATA-HOLDOUT-UNSUPPORTED" not in by_code` in the rewritten
  `E-REPL-KIND` test (a deliberate confirming assertion, not a leftover). Every test
  that lost its companion assertion was re-read for vacuity (see below). Added one
  new test, `test_a_holdout_repeat_kind_still_routes_to_the_built_field`.
- `tests/test_cli.py`: appended `test_a_declared_holdout_now_validates_and_runs` and
  `test_max_failed_fraction_is_measured_against_the_test_partition`, plus the helpers
  `run_roster_keys`, `_planned_execution_count`, `_HOLDOUT_SEEING_STEP`, and
  `_ALWAYS_FAILING_STEP`. Added `import hashlib`.

## The 28→vacuity check

23 assert-line companions removed, plus one whole test
(`test_holdout_is_refused_on_its_own`, whose *entire* assertion was the companion)
rewritten rather than deleted, since the property it should now prove — a
plain, well-formed `holdout` block validates clean — is real and worth keeping.
The 5 non-assert mentions were comments/docstrings; each rewritten to stop
describing the retired code as live.

I re-read every test that lost a companion line and classified each:

- **Still asserts something real on its own** (no fix needed): the parametrized
  malformed/well-formed holdout tests, the two-undeclared-name test, the
  by-attribute-column tests, the stratify-varies test, the empty-test-partition
  tests, the frac-already-refused test, the cells tests with a positive code,
  and the two resample/cluster tests with message assertions. None of these
  needed a change beyond deleting the one line.
- **Left absence-only, paired with an existing can-fail control already in the
  file** (comment added, no new assertion needed): `test_a_well_formed_holdout_
  declaration_earns_none_of_the_five` (control is the malformed-declaration
  parametrize directly above), `test_a_declared_holdout_stratum_is_accepted`
  (control is the undeclared-name test above), `test_a_holdout_beside_a_seed_
  repeat_is_not_refused` (control is the fold-exclusion test above),
  `test_an_empty_group_axis_alone_does_not_trigger_the_refusal` and
  `test_an_evaluation_split_without_a_cell_structure_is_not_refused` (both
  already explicitly self-documented as controls whose evidence is a sibling
  trigger test — I updated the docstrings to drop the now-false "the
  `-UNSUPPORTED` companion below" framing but kept the pairing argument, since
  it was already correct).
- **Genuinely vacuous, rewritten with a new finding**: `test_holdout_is_refused_
  on_its_own` → `test_a_plain_holdout_declaration_is_now_accepted`, asserting
  the config earns no `-UNSUPPORTED` and no `E-DATA-HOLDOUT-*` finding at all
  (needed a 20-unit roster override — `write_config`'s default 1-unit roster
  makes any `frac` apportion the test side to zero, tripping `E-DATA-HOLDOUT-
  EMPTY`, an unrelated real finding this test must not hit).
  `test_an_unrelated_unsupported_field_does_not_suppress_a_real_roster_defect`
  used `holdout` as its "unrelated unsupported field" example — no longer
  unsupported, so it now uses `statistics.null_test` instead, the field that
  remains in the family.
  `test_every_unsupported_message_defers_rather_than_scolds`'s second
  parametrize case declared `holdout` to get an `-UNSUPPORTED` message — also
  switched to `statistics.null_test`.
  `test_a_misspelled_holdout_child_is_reported_alongside_the_wholesale_refusal`
  → renamed and simplified to just check `E-CONFIG-KEY-UNKNOWN`, since the
  "alongside the wholesale refusal" half of its point no longer exists.

Nothing was found asserting only absences with **no** control anywhere in the
file — every one either had a real assertion left, or a genuine can-fail
sibling already present.

## `E-REPL-KIND` re-check

`{kind: holdout, n: 1}` still reports `E-REPL-KIND` with the message naming
`data.units.holdout` — confirmed via `replication.REJECTED_KINDS["holdout"]`,
unchanged by this task (task 5 sited the `fold` exclusion in `validate`, not
`resolve_repeats`, so `REPL_DECLARATION_CODES` needed no change either, matching
the brief). New test asserts both that the route fires and that
`E-DATA-HOLDOUT-UNSUPPORTED` no longer accompanies it — moved to
`test_validate.py`, not `test_cli.py` (see disagreements below).

## `findings[0]` sweep

`grep -rn 'findings\[0\]' tests/` found 27 sites, all in unrelated `assign`
tests whose configs never declare `holdout`. Full suite passes, confirming no
order flip — nothing to pin.

## The five end-to-end pins

All landed in the two new `test_cli.py` tests, verified against three
mutations, each reverted by editing the file back (never `git checkout --`)
and re-verified by re-running the targeted tests:

- (a) `execute_plan(units=eval_roster)` → `units=roster`: both new tests FAIL
  (first on the task-14 `split.json` check since `io.units` stops narrowing;
  second on `len(ledger) < planned` since the denominator no longer discriminates).
- (b) `holdout_train=` → `None`: both FAIL (on `expect_exit`, since `io.units.train`
  now raises `E-STEP-UNITS-UNAVAILABLE` inside both starter steps).
- (c) `build_allocation_document(group_axes, holdout_plan)` → drop the second
  arg: first test FAILS on `alloc_path.exists()`.

**Task 13's siting has no mutation among the three**, as the brief states, and
I did not add one: the property (`_resolved_holdout` called once, outside every
per-condition loop) is behaviourally invisible to any test — a call inside a
loop draws the same partition every time given the same seed and roster, so no
assertion distinguishes it. Reading the call site (`cli.py`, called once before
`build_plan`, its result threaded into three later reads) remains the only
instrument, exactly as task 13's own reviewer concluded.

## Disagreements with the brief

1. **Executions.jsonl carries no `n` key.** The brief's Step 1 test body
   asserted `record["n"]["resolved"] == 4` directly against ledger records.
   `runner.execute_plan` writes `step`/`scope`/`condition`/`repeat`/`status`/
   `started_at`/`wall_seconds`/`error` only — task 1's own end-to-end test
   found and documented this exact same gap between the plan and the code.
   Both new tests use a plain `status` assertion on the ledger and read the
   real per-metric `n` from `run.yaml`'s `aggregated` block instead (which does
   carry it, as task 15 actually wired it).
2. **`test_max_failed_fraction_is_measured_against_the_test_partition`'s
   `_ALWAYS_FAILING_STEP` needed a real design, not a bare `raise`.**
   `runner._units_failed_anywhere`'s own docstring: a step whose every
   execution crashes before producing a row is never classified as
   "recording" and so can never trip `max_failed_fraction` — a bare
   always-raising step trips nothing under either the narrowed or the
   un-narrowed denominator, so it cannot discriminate mutation (a) at all
   (verified empirically: it passed the guard-fired assertion even with
   `units=roster`, un-narrowed). The step actually appended records the
   training partition (`io.units.train`) every execution — present only when
   un-narrowed — and the test partition exactly once, on the first execution
   only, which is just enough to satisfy the "recording" requirement while
   leaving the test partition permanently in the run-wide failed union. This
   produces 3–4 of 4 failed under the fix (guard fires) and 3–4 of 20 under
   the reverted mutation (guard does not fire) — the same qualitative
   arithmetic the brief states ("4 of 4" vs "4 of 20"), reached by construction
   rather than by a step design that turns out not to exercise the guard at
   all. A consequence: the step never raises, so every execution status is
   `"completed"` and `run_status` returns `"completed"` even though the plan
   stops short (`max_failed_fraction` and the execution-level exit code are
   two independent mechanisms) — `expect_exit=EXIT_OK`, not `EXIT_PARTIAL` as
   the brief assumed.
3. **The third test (`E-REPL-KIND` routing) belongs in `test_validate.py`, not
   `test_cli.py`.** It uses `write_config`, `_holdout`, and `messages_by_code`,
   none of which exist in `test_cli.py` — all three are `test_validate.py`
   fixtures/helpers, and the test needs no run at all (pure validate-time
   check). Added it there, beside `test_an_unknown_repeat_kind_is_refused_
   through_validate`.
4. **Step 3(d)'s grep scope (`src/ tests/ docs/`) versus task boundaries.**
   Literally run, `grep -rn 'E-DATA-HOLDOUT-UNSUPPORTED' src/ tests/ docs/`
   still hits `docs/feasibility-llm-growth-studies.md`, which is not under
   `docs/superpowers/`. But that file's update is explicitly task 20's job
   ("The reader-facing half — the honest count") in the same plan, and the
   feasibility-analysis convention (`CLAUDE.md` § Feasibility analyses) is to
   *append* a new dated measurement rather than edit an old one — doing that
   work here would both preempt and duplicate task 20. I left it untouched and
   record this as the literal grep instruction's scope exceeding task 18's own
   file list (`src/publishable/validate.py`, `docs/reference.md`,
   `tests/test_validate.py`, `tests/test_cli.py`).

## Files touched

- `/Users/joon/src/tries/publishable/src/publishable/validate.py`
- `/Users/joon/src/tries/publishable/src/publishable/envelope.py`
- `/Users/joon/src/tries/publishable/docs/reference.md`
- `/Users/joon/src/tries/publishable/tests/test_validate.py`
- `/Users/joon/src/tries/publishable/tests/test_cli.py`

## Concerns

- None blocking. The `.superpowers/sdd/.gitignore` clobber (from `task-brief`)
  was noticed and restored to its tracked content before committing.
- `docs/feasibility-llm-growth-studies.md` still names `E-DATA-HOLDOUT-
  UNSUPPORTED` in its "Measured on 2026-08-15" section — correct as a dated
  historical claim, and task 20's to update with a new dated measurement.
