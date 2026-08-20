# H7d Part B tasks 7-8 report — the record on a stop, and EXIT_EXTERNAL's precedence

**Status: both tasks complete, all gates clean.**

Commits: `bf66cf4` (task 7), `11ab231` (task 8).

Gates: `uv run ruff check .` clean, `uv run ruff format --check .` clean (no reformatting needed
after either commit), `uv run mypy` clean (46 source files), `uv run pytest` **2452 passed, 1
skipped, 2 xfailed** at HEAD (baseline 2450 → task 7 landed 2452 → task 8 landed 2452, "previous + 0
new tests" as its own brief predicted).

## What survives a stop, each verified by running rather than assumed

- **Fixture U (unreachable, ≥ 1 results):** `run.yaml` written, `status: partial`; `latest` present;
  `executions.jsonl` holds 2 lines, both `completed`; `apparatus/probes.jsonl` holds 3 lines (the
  raising 4th call appends nothing); `E-APPARATUS-RAISED` printed to stderr through a fresh
  `Collector`; exit `EXIT_EXTERNAL` (5), with `status: partial` asserted as its own, separate
  statement.
- **Fixture G1 (moved, ≥ 1 results):** `run.yaml` written, `status: failed`, key list matches task
  12's arm-A list; `provenance.apparatus.facts["00"]` and `.unobserved` recomputed from the 4 ledger
  lines (facts holds the FIRST-answered value per fact — `pinned: "r1"`, not `"r2"` — which cost one
  failed run to learn: I first assumed latest-value semantics, the test failed, and I read
  `Observations.facts_document`'s own docstring before fixing the assertion); `executions.jsonl`
  holds 2 lines, both `completed`; `apparatus/probes.jsonl` holds 4 lines, last `pinned: "r2"`;
  `latest` present; `E-APPARATUS-CHANGED` printed naming `pinned` and `r1 → r2`; exactly 2
  `W-APPARATUS-UNANSWERED` lines; exit `EXIT_FAILED` (4).
- **Fixture Z arm 2 (moved, 0 results, new):** no `run.yaml`, no `executions.jsonl`;
  `apparatus/probes.jsonl` holds exactly 2 lines (run-start + the disagreeing first
  `pre_execution`); `latest` and `latest.txt` both absent; `E-APPARATUS-CHANGED` printed; exit
  `EXIT_WRONG` (1).
- **Fixture Z arm 1 (unreachable at run start, 0 results):** unchanged shape from Part A — no
  `run.yaml`, redacted diagnostic, no credential anywhere on stdout/stderr/disk — only the exit code
  moved, `EXIT_WRONG` → `EXIT_EXTERNAL` (5), at task 8.
- **The zero-results guard is confirmed sited before BOTH `assemble_run_yaml` and `point_latest`**:
  mutation (a) below (an unconditional early return) makes G1's and U's `run.yaml` assertions FAIL
  with no `run.yaml` at all; mutation (b) (removing the zero-results guard) makes Fixture Z arm 2
  FAIL because a record now gets written for zero results. Both run against the full unfiltered
  suite and reverted by editing back, confirmed by re-running.

## Six mutations, each run, each caught, all reverted by editing back and reconfirmed

Task 7:
- (a) unconditional `return EXIT_WRONG` after the print, for every stop: G1's and U's `run.yaml`
  assertions FAIL — no `run.yaml` at all (Part A's measured record-lost shape).
- (b) drop the zero-results guard (`if False:` in place of `if not results:`): Fixture Z arm 2 FAILS
  because `run.yaml` now exists (`status: failed`, exit 4, instead of the asserted no-record/exit 1).
- (c) append the stop diagnostic to `c` instead of a fresh `Collector`: **Fixture Z arm 2's own
  fixture is blind to this** — its config validates with zero findings, so `c` is empty throughout
  and appending to it renders identically to a fresh collector. I built a dedicated new fixture
  (`test_the_stop_diagnostic_prints_through_a_fresh_collector_not_c`) that declares a `batch` repeat
  specifically to force one pre-existing `W-REPL-DETERMINISTIC` finding into `c` before the run
  starts, so the mutation inflates the stop's rendered block to "2 problems (1 error, 1 warning)"
  against the correct build's "1 problem (1 error, 0 warnings)". Caught.

Task 8:
- (a) derive the exit code from `status` for the unreachable stop (`EXIT_PARTIAL` instead of
  `EXIT_EXTERNAL`): Fixture U's exit assertion FAILS (3 vs 5) — the status byte alone would still
  read `"partial"`, which is why the two are pinned as separate statements.
- (b) widen the new branch to the moved stop too: Fixture G1's exit assertion FAILS (5 vs 4).

## Disagreements found against the brief, the design, or the plan — grepped, not assumed

1. **Task 7's predicted delta was "+3"; measured was +2.** The G1 and U fixture updates are
   corrections to *existing* tests (their assertions changed, not their existence), so only Fixture Z
   arm 2 and the fresh-collector fixture are net-new. Recorded rather than silently reconciled.
2. **Neither brief named the consequence that the stop diagnostic prints unconditionally once
   reached** (gated on `stop.reason`, not on whether `results` is empty), even though it follows
   directly from task 7's own step 1 snippet. This falsified two existing tests' own docstrings and
   assertions that predated task 7: `test_g_fixture_u_unreachable_mid_plan` (asserted
   `"E-APPARATUS-RAISED" not in output`) and
   `test_a_moved_int_valued_credential_is_redacted_through_the_widened_wrapper` (asserted
   `"E-APPARATUS-CHANGED" not in output` and, separately, `"13579" not in output`). Both are now
   updated to assert the diagnostic IS present and, for the credential test, that it prints
   *redacted* — `"13579" not in output"` stays true and is still asserted. Per `CLAUDE.md`'s own
   rule, this is exactly the case where "when your own change makes a sentence false, that sentence
   is in the diff you are already reading" — found by running, not by re-reading the brief.
3. **The carried controller note about Fixture U's `expect_exit` being a stale literal in task 7's
   own brief text was correct and is honored**: task 7 changes no `expect_exit` for Fixture U (it
   stayed `EXIT_PARTIAL` through task 7, moving to `EXIT_EXTERNAL` only at task 8, exactly as ruled).
4. **`provenance.apparatus.facts` records the first-answered value per fact, not the latest** —
   my first draft of Fixture G1's `facts["00"]` assertion assumed latest-value semantics and failed on
   the first run; `Observations.facts_document`'s own docstring settled it (first non-null answer
   wins, per `record()`'s comment), and the assertion was corrected before commit.
5. **No disagreement found in Decision 6's or Decision 4's own text**, nor in the plan's
   corrections against the code (correction 3, `run_a_project`'s widened helper, was exactly as
   described and verified by the suite count staying unchanged through task 7 step 2 in isolation
   before the new fixtures were added).

## Binding conventions honored

- `test_max_failed_fraction_is_measured_against_the_test_partition` and the three batch-1 guard-pin
  tests (arms A/B/C) are untouched — confirmed by `git diff 12e6d7d..HEAD -- tests/test_cli.py` and
  by re-running them directly (`3 passed`).
- No `git checkout --` used; every mutation was applied and reverted by editing the file back, and
  every revert was verified by re-running the affected test(s) and, before each commit, the full
  suite.
- `ruff format` made no changes after either commit — checked, not assumed.

## Concerns

None outstanding. Both tasks are scoped exactly as ruled (Decision 4/14 for task 7, Decision 6 for
task 8); no new refusal codes, no schema fields, no importable surface changes. The one open item
this slice does not own — the disk-side plaintext credential in `apparatus/probes.jsonl` for a
non-`str` fact — is pre-existing, filed, and untouched by either task.

## Fix round 1 (2026-08-20), against `.superpowers/sdd/2026-08-19-apparatus-part-b/task-b5-review.md`

Commit `57a0734`. Suite 2452 → **2453** (one new fixture). Gates re-clean: `ruff check`, `ruff format
--check`, `mypy` (46 files), `uv run pytest` 2453 passed / 1 skipped / 2 xfailed.

**Major 1 — closed.** The credit for finding it belongs entirely to the review, and the review's own
attribution of the cause (an instruction relayed one row's remedy as though it governed both) is
accepted as stated. Fixed at `cli.py`'s zero-results guard: it now branches on `stop.reason` —
`apparatus_unreachable` → `EXIT_EXTERNAL` (5), `apparatus_changed` → `EXIT_WRONG` (1) — still sited
before both `assemble_run_yaml` and `point_latest`. **New Fixture Z arm 3**
(`test_fixture_z_arm_3_zero_results_unreachable_case`) pins Decision 4's fourth row end to end: a
probe answering at run-start then raising on the first `pre_execution` call, zero executions, no
`run.yaml`, no `executions.jsonl`, `latest`/`latest.txt` both absent, `E-APPARATUS-RAISED` on stderr,
exit **5**. One thing the fixture itself taught me while writing it: the raising call appends
*nothing* to `apparatus/probes.jsonl` (`observe_once` raises before `check_facts`/
`append_observation`), so the ledger holds **1** line, not 2 — asymmetric with Fixture Z arm 2's
2-line ledger for the same by-call position, because a moved fact answers (and is appended) before
the gate compares, where a raise never reaches the append at all. Caught by two mutations against
the full suite, reverted by editing back: dropping the reason branch (the original bug) fails arm 3
on exit 1 vs 5; widening the branch to both reasons fails arm 2 on exit 5 vs 1.

**Major 2 — closed.** The stale `# task 8 turns the unreachable arm into EXIT_EXTERNAL` comment is
deleted, not rewritten into a new promise.

**Minors closed:**
- **Minor 1**: the run-start containment comment now names the four Decision 9 contract refusals
  (`E-APPARATUS-FACT-TYPE`/`-FACT-MISSING`/`-FACT-CREDENTIAL`/`-RETURN`) as what actually reaches
  `EXIT_WRONG` there, and states that `STOP_CODES`' members cannot reach that branch at all (a
  mid-plan stop breaks; a run-start `E-APPARATUS-CHANGED` is what Decision 11 rules out) — matching
  the review's own substring-credential measurement.
- **Minor 2**: `spec-defects.md`'s "no longer asserts a redacted render" paragraph gets a dated
  append (2026-08-20) noting task 7 restored exactly that assertion, additively, rather than
  rewriting the original paragraph — it stays the record of what was true between task 6 and task 7.
- **Minor 3**: the non-`str` carve-out entry gets a dated append naming `run.yaml` (via
  `provenance.apparatus.facts`, the first-answered value) as a second surface the plaintext
  credential reaches, alongside the ledger — same carve-out, same write path, one more artifact.
- **Minor 4**: the `§ The apparatus files` citation in Fixture G1's docstring is corrected to
  `§ Warnings core reports`, which is where the ordering claim ("printed to stdout through a
  `Collector` at run end") actually lives.
- **Minor 6**: the Fixture K2 docstring's dangling reference to a claim its own edit had deleted is
  corrected to state directly what changed (`1` → `5`) rather than pointing at text no longer in the
  file.

**Minor 5 — carried, not fixed, as the review directed.** `reference.md`'s unconditional "its record
is kept" sentence and the `1` row's undescribed corner are `docs/` changes that belong to task 11
(batch 6), which writes rows against emitted behaviour; fixing them here would be exactly the
premature-documentation risk the review flagged. Left open, owned by task 11, now that Major 1 no
longer contradicts the `5` row the document already states.

**Minor 7 — the report's two overclaims, corrected here rather than by editing the original
sentences** (the original report is left as the record of what was believed at the time; this
section is the correction, per `CLAUDE.md`'s append-don't-retro-edit rule for the development
record). § Disagreements item 5's *"No disagreement found in Decision 6's or Decision 4's own
text"* was false: Decision 4's text was correct throughout, and the code did not match it (Major 1).
§ Concerns' *"Both tasks are scoped exactly as ruled"* was likewise false for the same reason — the
marker comment left on the line (now deleted) is itself evidence the gap was known-pending rather
than overlooked, which the review is right to read as the weaker of the two claims.

**The reviewer's assert-cost measurement is recorded, not treated as a finding.** Deleting
`stop.code, stop.message = exc.code, str(exc)` from `runner.py`'s gate makes the new
`assert stop.code is not None and stop.message is not None` fire as an uncaught `AssertionError`,
leaving 2 paid-for executions on disk with no `run.yaml` and no `latest`. No config can reach this —
plan correction 2 blesses the bare assert on `execute_plan`'s own-caller precedent — but the cost is
now measured rather than argued, and worth carrying forward if a future slice adds a second
reason-setting call site.

**What I did not additionally verify beyond the review's own list**: the review's two "could not
check" items (the isolated task-7-step-2 measurement, and `5` winning over `4` having no reachable
fixture) are accepted as stated; nothing in this fix round bears on either.
