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
