# H7d Part A batch 3 — tasks 9, 10, 15

**Status:** complete. All three tasks implemented, tested, mutation-pinned, and committed
separately, in order.

**Commit SHAs:**
- `d645b0d` — task 9: the run-start round, and a probe failure as a redacted diagnostic
- `64f343f` — task 10: a probe before every execution, condition-less ones included
- `6d828e7` — task 15: the call-count contract, pinned against every candidate reading

**Test summary:** `uv run pytest` → **2402 passed, 1 skipped, 2 xfailed** (baseline 2395 + 7:
4 from task 9, 2 from task 10, 1 from task 15). `uv run ruff check .`, `uv run ruff format
--check .`, and `uv run mypy` (46 source files) all clean.

## What was built

- `apparatus.py`: `APPARATUS_CODES` (the five `E-APPARATUS-*` codes, nothing else) and
  `Observer` — the phase-independent object holding the probe callable, declared facts, the
  resolved conditions, per-condition `cfgs` (never the wide one), `run_dir`, `credentials`, and
  an `Observations`. Its `observe_round(*, phase, condition_index)` makes one call per resolved
  condition when `condition_index=None`, one call otherwise; `warn_unanswered(c)` delegates to
  `Observations`. `block()` (task 11) is not implemented — out of scope for this batch.
- `cli.py`: resolves `run_template.apparatus_probe`/`apparatus_facts` and constructs `Observer`
  (or leaves it `None`) inside the run-directory lock, after `sweep.yaml`/`allocation.json` are
  written and before `execute_plan`. The run-start round and `execute_plan` call are wrapped in
  one `try/except ContractError`, filtered to `apparatus.APPARATUS_CODES`; a hit builds a
  **fresh** `Collector` carrying the already-bound `credentials` and returns `EXIT_WRONG`. Every
  other `ContractError` (dispatch codes, `E-RUN-CFG-MISSING`, etc.) keeps escaping to `main`
  exactly as before.
- `runner.py`: `execute_plan` gained `observer: Observer | None = None`. Before each execution
  (before the step is constructed, before anything runs) it calls
  `observer.observe_round(phase="pre_execution", condition_index=execution.condition_index)`
  when `observer is not None`. The condition list for a condition-less round comes from
  `Observer`, never derived from the plan.
- `spec-defects.md`: closed the OPEN filing on `append_observation`/`check_facts` ordering.

## The append_observation / check_facts ordering ruling

`Observer._observe_one` (the first and only caller of both, in this batch) calls `check_facts`
**before** `append_observation`, every time. Grounds: the reverse order would let a probe's
returned credential value reach the ledger file before the credential check ever runs, which is
exactly the leak Decision 6 exists to prevent — satisfying every ordering rule the design states
while still leaking. Pinned by Fixture K's raw-text-over-the-run-directory assertion
(`test_a_probe_returning_a_declared_credential_fails_the_command_and_writes_no_run_yaml`): the
credential never reaches any file, which is only true because the refusal fires before the
append. The `spec-defects.md` entry is struck (renamed to `CLOSED by H7d Part A batch 3`) with
this ruling recorded in it.

## Mutations run, against the full suite, each reverted and reverified

**Task 9** (three, all pinned):
1. Hand every probe call `cfgs[0]` instead of the condition's cfg → Fixture S's test FAILED
   (`00_model=m1` recorded `m1` correctly but `01_model=m2` recorded `m1` instead of `m2`).
2. Delete `probe_c.credentials = credentials` → the K2 test FAILED on `lab7`'s presence in
   stdout/stderr (the un-redacted escape route, `main`'s bare `PublishableError` handler).
3. Probe once for the run instead of once per condition (`self.conditions[:1]`) →
   the run-start test FAILED, `['00_model=m1']` against the expected two-key list.

**Task 10** (two, both pinned; see note below on the fixture change):
1. Guard the call with `execution.condition_index is not None` → the condition-less test FAILED,
   `pre_execution_conditions == set()` against the expected two keys.
2. Move `observe_round` to after `results.append(result)` → the ordering test FAILED, `2`
   against the expected `4`.

**Task 15** (one, pinned): probe only on the first execution
(`if observer is not None and not results:`) → FAILED, `4` lines against the expected `6`, with
a different (shorter) pair list.

## Where the brief and the actual code disagreed

1. **Task 10's second test cannot read `provenance.apparatus.facts`.** The brief's docstring
   asks the test to assert "both keys are present in `provenance.apparatus.facts`" — but that
   assembly is task 11's (`Observer.block()` plus its `cli.py` wiring), which is out of scope
   for this batch; `command_run` still writes `"apparatus": None` unconditionally (confirmed:
   `cli.py` line ~3455, untouched). Asserting against `run.yaml` there would fail on task 11's
   absence, not on task 10's own property. I substituted a reconstruction of the same
   (condition → fact) view directly from the ledger — the first non-null observation per
   (condition, fact), which is `Observations.record`'s own documented rule — so the property
   task 10 actually owns is pinned without depending on unbuilt wiring. Documented inline in the
   test's docstring as a deviation, not silently changed.

2. **The design's Fixture F (8 lines, two condition-scope steps) was not used verbatim for
   task 10's tests; a reduced fixture was, to avoid a real confound.** The ledger carries no
   step identity — only `phase`/`condition`/`probe`/`facts` — so a design with *both* a
   condition-bearing step and a condition-less step produces `pre_execution` lines for the same
   condition keys from two different sources, and a test filtering only by
   `phase == "pre_execution"` cannot tell which source contributed which line. I used
   `_starter_step` to make the run-scoped counting step the **only** execution in the plan for
   both of task 10's tests, removing the confound entirely, and noted this in each test's
   docstring. Task 15's test does use the mixed design (a repeat-scoped step plus a run-scoped
   one), because there the *ordered pair list* — not a per-phase filter — is what's asserted,
   and the pair list is unambiguous regardless of how many sources contribute to it.

3. **Task 15's own fixture is the reduced one already flagged in § Corrections against the
   code, correction 7.** The plan's correction 7 already states this fixture (unlike the
   design's original 8-line Fixture F) has two candidate readings colliding at 5 lines rather
   than a unique count — confirmed by construction here: "once per run at run start" and "one
   wide-cfg call for the condition-less execution" both yield 5 for this `C=2, E_c=2, E_none=1`
   shape. The test's docstring states this rather than claiming the fixture separates every
   reading by count.

No other disagreement between a brief, the design, or the plan and the actual code was found;
`apparatus.py`'s `check_facts`/`observe_once`/`Observations`/`condition_key`/`append_observation`
(batches 1–2) matched their briefs' descriptions exactly, and `execute_plan`'s existing
`credentials` threading, `conditions_list` derivation, and per-execution `try/except` shape were
as measured in § Corrections against the code.

## Concerns for review

- `apparatus._probe_for` (dispatch) is called outside the `try/except` wrapper in `command_run`,
  per Decision/correction 10 — a dispatch failure (`E-PROBE-UNKNOWN`, `E-PLUGIN-LOAD`,
  `E-PLUGIN-DECORATOR`) escapes to `main` unredacted, matching every other pre-existing
  core-inconsistency path. No fixture in this batch reaches it (as the plan states none can).
- `Observer.block()` does not exist yet; `provenance.apparatus` stays `None` for every run in
  this build, including one with a declared, working probe. This is deliberately deferred to
  task 11, not a regression — the guard pin (task 18, already merged) still holds for the
  no-probe case.
- The credential value used in the new tests, `lab7`, is short and ordinary-looking by design
  (Fixture K's requirement) so the exact-value credential check is what's actually exercised,
  not a coincidental pattern match.

---

## Fix round 1

Review at `.superpowers/sdd/2026-08-19-apparatus-part-a/task-b3-review.md`, both verdicts FAIL
on a Critical. Fix commit: `f98ff7f`.

**Test summary:** `uv run pytest` → **2409 passed, 1 skipped, 2 xfailed** (2402 + 7 new tests).
`ruff check`, `ruff format --check`, `mypy` (46 source files) all clean.

### Critical 1 — a probe's dispatch failure leaked a declared credential to stderr

**Changed:** `src/publishable/cli.py` — `apparatus._probe_for(declared_probe)` is now called
inside its own `try/except BaseException`, sited before the run-start/`execute_plan` `try`,
mirroring the roster wrapper's exact shape: `KeyboardInterrupt` re-raised fresh and
argument-less, everything else redacted through a fresh `Collector` carrying `credentials`,
`EXIT_WRONG` returned. Deleted the two comments that claimed this was safe (`cli.py`'s "no
fixture in this plan reaches it" and `apparatus.py`'s matching `APPARATUS_CODES` docstring
paragraph), rather than rewording them — replaced with the actual mechanism.

**Verified by:**
- `test_a_probe_that_fails_to_load_is_a_redacted_diagnostic_at_run` (new, `tests/test_cli.py`):
  a probe module that raises `RuntimeError` at import, carrying the declared credential
  `PUBLISHABLE_TEST_TOKEN=lab7`. **Confirmed this test fails on the pre-fix code**: reverted
  `cli.py` to the committed-batch-3 version, re-ran, got
  `AssertionError: '<redacted:PUBLISHABLE_TEST_TOKEN>' in "...RuntimeError('plugin import
  failed near token lab7')..."` — i.e. the raw credential in stderr, exactly the review's
  reproduction. Restored the fix, re-ran, passes.
- `test_a_probe_s_entry_point_decorator_mismatch_is_a_diagnostic_not_a_traceback` (new): the
  sibling dispatch fault, `E-PLUGIN-DECORATOR`, reaches the same wrapper rather than escaping
  as an unfiltered `ContractError`.
- `spec-defects.md`'s `## OPEN — main's last-resort stderr handler...` entry corrected: the
  "demonstrated path into it is closed" claim is now dated and attributed — a second path was
  found by this batch's review and closed in this fix round; the handler itself still has no
  fix and is still reachable by any other `PublishableError` raised outside a collector.

### Major 2 — three of five `APPARATUS_CODES` were unpinned

**Changed:** nothing in behavior; added three end-to-end tests in `tests/test_cli.py` —
`test_E_APPARATUS_RETURN_is_individually_pinned_through_the_wrapper`,
`test_E_APPARATUS_FACT_TYPE_is_individually_pinned_through_the_wrapper`,
`test_E_APPARATUS_FACT_MISSING_is_individually_pinned_through_the_wrapper` — each driving a
real `run` whose probe returns the bad shape, and asserting the diagnostic carries the
`Collector`'s own rendered shape (`"experiment_type"` path field, `"1 problem (1 error, 0
warnings)"` summary line) rather than `main`'s one-line bare-handler format.

**Verified by:** deleted all three codes from `APPARATUS_CODES` together — all three new tests
FAILED (each on the `"experiment_type"` assertion, since the exception re-raised past the
wrapper to `main`'s bare handler). Restored the three, deleted only `E-APPARATUS-RETURN` alone
— only that one test failed, the other two still passed, confirming each is now individually
discriminated. Reverted by editing back, `uv run pytest tests/test_cli.py -k "..."` re-run
clean at each step.

### Major 3 — `append_observation`'s stale docstring

**Changed:** deleted the paragraph in `apparatus.py`'s `append_observation` instructing
"batch 3... must either call `check_facts` before this function or the gap is
`spec-defects.md`'s to carry" — the ruling now lives in `Observer`'s own docstring and the
filing is already closed. Replaced with one sentence pointing at `Observer._observe_one` as
where the order is fixed, rather than repeating the ruling a second place.

### Major 4 — the substituted assertion in task 10's second test could not fail

**Changed:** `tests/test_cli.py`,
`test_a_condition_less_execution_is_probed_once_per_condition` — the `facts_first_answered`
reconstruction now iterates `counter_lines` (the `pre_execution` round only) instead of the
whole `ledger`, so it no longer trivially passes off the `run_start` round's own facts.
Docstring updated to state the original bug and the fix.

**Verified by:** reproduced the review's exact mutation (restricted the reconstruction to
`phase == "run_start"` only) against the ORIGINAL (whole-ledger) version — confirmed it passed
vacuously, matching the review's finding. Applied the fix (restrict to `counter_lines`) and
re-ran: passes normally, and the earlier task 10 mutation (guarding the call on
`execution.condition_index is not None`) still fails the test as a whole (at the
`pre_execution_conditions` assertion, reached before the facts assertion). Reverted the
reproduction, re-confirmed the fixed version.

### Minor 5 — the batch's own new filing was stale on arrival

**Changed:** `spec-defects.md`'s entry on a fact-key-equal-to-credential shape — corrected the
claim "reaches a diagnostic with that credential in the message" (true of the raw exception,
false of what prints) to state it is redacted at `run` today because `E-APPARATUS-FACT-TYPE`
is inside `APPARATUS_CODES`, and narrowed the still-open question to whether `check_facts`
itself should check keys (not values only), rather than striking the entry outright — the
underlying gap (no key check) is real and worth keeping open.

### Minor 6 — Decision 3's motivating case (a `summary`-scoped execution) had no fixture

**Changed:** added
`test_a_summary_scoped_execution_is_probed_once_per_condition_and_runs_last` (`C=3, E_c=6,
E_none=1` → 12 lines), using a `summary`-scoped extra step. Widened
`_APPARATUS_ASSAY_TEMPLATE`'s `instrument.model` choices from two to three values to support
the three-condition sweep (harmless to every other test using this template — none relies on
the choice set being exactly two).

**Verified by:** confirmed the count (12), that the summary execution's condition is `None`
and runs last in `executions.jsonl`, and that its three `pre_execution` lines (the ledger's
last three) carry each condition's own swept value. Mutated `runner.py` to guard the
per-execution call on `execution.condition_index is not None` — test FAILED, 9 lines against
12. Reverted, re-confirmed 12.

### Minor 7 — `Observer.warn_unanswered` had no caller and no test

**Changed:** added
`test_observer_warn_unanswered_delegates_to_observations_with_declared_facts` in
`tests/test_apparatus.py` — constructs an `Observer` directly, runs one `observe_round`, and
checks `warn_unanswered` fires `W-APPARATUS-UNANSWERED` for a declared null fact and not for an
undeclared one, pinning that `self.declared_facts` (not every observed fact) reaches
`Observations.warn_unanswered`. Did not wire a call site — that is task 11 step 2's, per the
plan, and wiring it here would mean guessing at task 11's own `Collector` plumbing.

**Verified by:** mutated the delegation to pass `[]` instead of `self.declared_facts` — test
FAILED (0 findings instead of 1). Reverted, re-confirmed.

### Minor 8 — positional locators in new prose

**Changed:** `runner.py` ("`conditions_list` below" → names it as this function's own,
built for `io.conditions`), `cli.py` ("the run-start round just below" →
"`Observer.observe_round`'s run-start round"; the flagged "the `try` below" no longer exists,
subsumed by the Critical 1 rewrite), `apparatus.py` ("`_observe_one` below" →
"`Observer._observe_one`, this class's own per-condition probe-and-append step").

### Findings not closed, and why

None. All eight findings (one Critical, three Major, four Minor) were addressed in this round.
