# H7d Part B batch 3 report — tasks 4 and 13

Commits: `033c09a` (task 4), `935902f` (task 13).

Suite: 2436 → 2438 (task 4) → 2439 (task 13). `ruff check .`, `ruff format --check .`,
`mypy` (46 source files) all clean at each commit.

## Task 4: the ordering chain

Wired `check_changed(self.observations, key, facts)` as the last statement of
`Observer._observe_one`, after `self.observations.record(key, facts)` — the order is now
`check_facts → append_observation → Observations.record → the gate compares → raise`, exactly
Decision 3. Nothing else in the method moved.

**The two assertions only this task can make, named as the brief asked:**

1. **The direct-call pin for record-before-gate**
   (`test_the_ordering_chain_counts_the_moving_call_before_the_gate_fires`,
   `tests/test_apparatus.py`): drives Fixture G1's schedule through a bare `Observer` across four
   rounds, catches the raise, and asserts `observer.observations.unobserved(["pinned"])["pinned"]
   ["total_probes"] == 4`. This is the **count** discriminator — the only assertion that can see
   record-before-gate, because `_first_answered` never overwrites an answered pair, so every
   *value* assertion is true under either ordering.
2. **The run-level pin for append-before-gate** (`test_g1_ordering_chain_appends_before_the_gate_fires_end_to_end`,
   `tests/test_cli.py`): drives Fixture G1 end to end with `expect_exit=EXIT_WRONG` (the shape at
   this commit — task 5 is what turns this into a stop, and the test's own docstring says so) and
   asserts all 4 ledger lines are on disk, the fourth carrying `pinned: "r2"`, and the diagnostic
   naming `pinned` and `r1 → r2`. This is the **ledger-line-count** discriminator.

## Task 13: the run-start round, and the sentinel

Added `test_g3_run_start_round_never_trips_the_gate_across_conditions`: two conditions sweeping
`instrument.model`, exit 0, `status: completed`, two distinct recorded `model_revision` values, and
`E-APPARATUS-CHANGED` absent from stdout and stderr — the absence paired with the values and status
that must report. Its own distribution and module names (`dist-t13g3`/`t13g3_probe_mod`), per
Fixture P's warning about module-name collisions across a test session.

**The sentinel measurement — run rather than assumed, per the brief's own instruction not to
guess the outcome.** Mutated `Observations.changed` to fail on a `null → value` transition too,
using the null/total counts `record` already keeps (a bare `first != incoming` comparison cannot
see this transition at all, since `first` is reflexively equal to `incoming` the instant it is
first established — that reflexivity is exactly what makes the ordinary code accept the
transition). Ran the **full, unfiltered** suite under the mutation:

```
FAILED tests/test_apparatus.py::test_changed_null_to_value_passes_and_becomes_first_answered
FAILED tests/test_apparatus.py::test_the_ordering_chain_counts_the_moving_call_before_the_gate_fires
FAILED tests/test_cli.py::test_a_declared_probe_records_the_five_sub_keys_per_condition
FAILED tests/test_cli.py::test_the_unanswered_warning_fires_once_per_condition_and_fact_with_a_null
FAILED tests/test_cli.py::test_g1_ordering_chain_appends_before_the_gate_fires_end_to_end
5 failed, 2434 passed, 1 skipped, 2 xfailed
```

**`test_a_declared_probe_records_the_five_sub_keys_per_condition` — Fixture N's own test, named in
the brief — DID fail.** The sentinel is real: Part A's shipped Fixture N test would have caught a
gate that fires spuriously on `null → value`, even though it predates the gate and was never
written as a pin for it. Per the brief, nothing further is owed — no new fixture was built, since
the measurement came back positive rather than imaginary. Reverted by editing the file back to the
saved original; `diff` against the saved copy confirmed byte-identical before re-running the full
suite clean at 2439.

## Disagreements between the brief/plan and the code, found by grepping and running rather than
## by repeating the prose

**Both of task 4's step-5 prescribed mutations are caught by an internal `AssertionError`, not by
the named count assertion, contradicting the brief's "Neither is a crash."** `Observations.changed`
carries a reflexivity-safety `assert` (added in batch 2's fix round, for the `nan` finding) that
requires `record()` to have already run for every non-null incoming value by the time `changed()`
sees it. Both prescribed reorderings place the gate before `record()` has run for at least one
fact on the very first round (`run_start`, where `pinned`, `vanishes`, and the undeclared
`sometimes` all answer non-null for the first time), so both trip that `assert` immediately:

- **Mutation (a) — comparison moved above `append_observation`.** Taken literally this also moves
  the comparison above `record()` (since in the correct order `record()` sits between
  `append_observation` and the gate), so it produces the same `AssertionError` as (b), not the
  predicted "3 ledger lines against 4." Confirmed by running both the direct-call test and the
  end-to-end test against this ordering — both raised `AssertionError` from
  `src/publishable/apparatus.py:303` rather than failing on their named assertion.
- **Mutation (b) — comparison moved above `Observations.record`.** Same `AssertionError`, same
  line, confirmed the same way.

Both mutations still make their named test **FAIL** (pytest reports a failure either way), so the
mutations do catch the reordering — but via an unrelated invariant crash rather than via the
count-based discriminator the plan names, which is precisely the shape `CLAUDE.md` flags ("a
mutation caught by a crash is not a pin"). This is reported rather than silently rewritten: the
tests as shipped are correct pins for the *unmutated* code (confirmed passing at 2438/2439), and
the disagreement is with the plan's prediction of *how* the mutation would be caught, not with
the tests' validity. No code or test change was made in response — the instruction was to run each
mutation, check it against the test's own body, and report the outcome, which is what this section
does.

**`run_a_project`'s `EXIT_WRONG` branch could not be reused for task 4 step 3.** That branch (in
`tests/test_cli.py`) assumes a `validate`-time refusal and returns `run_dir: None` without globbing
`results_dir`. Fixture G1's raise happens mid-plan, well after a run directory and its ledger exist,
so the new end-to-end test globs `results_dir` itself (`next(doc["results_dir"].glob("run_*"))`)
rather than trusting that branch — noted inline in the test's own comment, not filed as a defect,
since `run_a_project` is a test helper rather than a documented contract and this is the shape task
4's brief itself anticipated ("the shape at this commit").

**`run_a_project` requires an explicit `parameters={}` override for a template declaring no
`parameter_spec`.** The scaffold's generated `config.yaml` always materializes `parameters.analysis.*`
for the starter step regardless of `experiment_type`; a custom template with no matching
`parameter_spec` entries fails `E-PARAM-UNKNOWN` at `validate` unless the caller passes
`parameters={}` to wholesale-replace the block via `doc.update(overrides)`. Both of this batch's new
templates (`ApparatusG1Assay`, `ApparatusG3Assay`) needed this; `ApparatusG3Assay` needed
`instrument.model` instead. Noted here since it cost a debugging round; not a code defect, since
every existing apparatus fixture in `test_cli.py` already follows this pattern for the same reason.

## Concerns for review

- The task-4 mutation-crash finding above is worth the reviewer's own look: is an `AssertionError`
  from a shipped internal invariant an acceptable way to "catch" a reordering mutation, or does the
  ordering clause need a discriminator that survives independently of that assert? No code was
  changed here since the brief's instruction was to run and report, not to redesign the pin.
- Task 5 (not in this batch) is what changes task 4 step 3's `EXIT_WRONG` expectation to a stop with
  a record — that test's docstring says so explicitly, and the report above repeats it so a reviewer
  reading only the report knows it is expected to change.

---

## Fix round 1 (review at `task-b3-review.md`)

Both Majors closed, all six Minors addressed. Suite: 2439 → 2442. `ruff check .`, `ruff format
--check .` (`ruff format .` re-run, 82 files unchanged), `mypy` (46 source files) all clean.

### Major 1 — the live credential leak (closed)

**Cause, confirmed by reproducing the reviewer's exact repro.** A declared credential
(`required_env = ["PUBLISHABLE_TEST_TOKEN"]`, `.env` supplying `PUBLISHABLE_TEST_TOKEN=13579`) held
as an **`int`** fact that then moves printed `E-APPARATUS-CHANGED ... changed: 13579 → 999` to
stderr, unredacted, exit 1. Two composing causes, both pre-existing: `check_facts`'s containment
check skips any non-`str` value by its own carve-out, and `E-APPARATUS-CHANGED` sits outside
`APPARATUS_CODES`, so task 4's new call site let the raise reach `command_run`'s containment `try`,
find itself excluded by the `APPARATUS_CODES`-only filter, and re-raise to `main`'s bare
`PublishableError` handler.

**Fix.** `cli.command_run`'s containment filter (the `try` wrapping the run-start round and
`execute_plan`) now admits `apparatus.STOP_CODES` as well as `apparatus.APPARATUS_CODES`
(`src/publishable/cli.py`, one changed condition plus an expanded comment). `E-APPARATUS-CHANGED`
itself still does **not** join `APPARATUS_CODES` — plan correction 4's exclusion is unchanged and
still correct about not adding an unpinned member to `_probe_for`'s dispatch-time filter — this
widens only the local exception filter in `command_run`, reusing the same `Collector` and
`credentials` every `APPARATUS_CODES` member already renders through. This is an interim fix: task
5/7 replaces this branch entirely with Decision 14's own fresh redacting `Collector` on the stop
path.

**Verified by running, end to end.** New test
`test_a_moved_int_valued_credential_is_redacted_through_the_widened_wrapper`
(`tests/test_cli.py`) reproduces the reviewer's exact fixture — `ApparatusIntCredAssay`,
`required_env = ["PUBLISHABLE_TEST_TOKEN"]`, a probe returning `{"serial": 13579}` (an `int`) on its
first two calls and `{"serial": 999}` on the third — and asserts, over combined stdout+stderr:
`<redacted:PUBLISHABLE_TEST_TOKEN>` present, `"13579"` absent, and (via
`_assert_went_through_the_containment_wrapper`) that the diagnostic went through the real `Collector`
path (the code string, `"experiment_type"` as the path, and the `"1 problem (1 error, 0 warnings)"`
summary line) rather than `main`'s bare one-line printer. A manual re-run outside pytest confirmed the
exact terminal text:

```
  error   E-APPARATUS-CHANGED  experiment_type
          condition `00`'s fact `serial` changed: <redacted:PUBLISHABLE_TEST_TOKEN> → 999
1 problem (1 error, 0 warnings)
```

**Both `STOP_CODES` members now individually pinned through this wrapper**, the shape Part A's
whole-branch review demanded of `APPARATUS_CODES`: `E-APPARATUS-RAISED` by Part A's own Fixture K2
(`test_a_probe_that_raises_is_a_redacted_diagnostic_at_run`, unchanged, still green), and
`E-APPARATUS-CHANGED` by the new test above — both going through
`_assert_went_through_the_containment_wrapper`, the same discriminator the `APPARATUS_CODES` members
use.

**The disk half is deliberately not fixed here, per the reviewer's own adjudication.** The same run
still writes `{"serial": 13579}` into `apparatus/probes.jsonl` in plaintext (confirmed by a manual
run reading the ledger file directly) — `check_facts`'s non-`str` carve-out lets it through the
credential check regardless of the gate, and this is pre-existing (not created by task 4's wiring).
Filed as a new open entry in `spec-defects.md` (owner: unassigned), and the existing open entry for
the credential-valued-**key** case is amended with a note that its own prediction — *"a future code
added outside that set … would reopen the leak"* — is exactly what happened, and was closed in this
fix round.

### Major 2 — the overclaiming docstring (closed)

**Confirmed and extended, exactly as the reviewer found.** Re-ran both prescribed orderings
(gate-before-`record`, in either of the two literal forms task 4's own mutations used) against the
direct-call count test and the end-to-end ledger test: both still crash with `AssertionError` from
`apparatus.py`'s reflexivity-safety assert, and the named count assertion
(`unobserved(["pinned"])["pinned"]["total_probes"] == 4`) is never reached. The assert fires on the
**first answering observation of any fact**, so no fixture escapes it under a gate-before-`record`
reordering — the finding stands and is narrower than my original report stated: the append half's
discriminator is real (see below), and only the record half is affected.

**Action 1 (minimum, taken).** Deleted the count test's overclaiming clause. It no longer says this
count "is the only assertion that can see this ordering" or cites "the plan's own correction" (Minor
3: `total_probes` appears in the plan's mutation table and in task 4 step 2, never in § Corrections
against the code — fixed in the same edit). The docstring now states plainly that this is a census
assertion true under the surviving ordering, names the assert as the actual guard, and points at the
two new tests below for what they each do and do not pin.

**Action 2 (taken).** Added `test_changed_asserts_when_called_without_record_first`
(`tests/test_apparatus.py`): a direct call to `changed()` for a pair whose non-`None` value never
went through `record()` first, asserting the `AssertionError`. Its docstring states precisely what
this does and does not witness: that `changed` *requires* record-first (grep-confirmed no prior test
asserted it), not that `_observe_one` *satisfies* that requirement — this test is unaffected by a
reorder of `_observe_one` itself.

**Action 3 (taken).** Added `test_the_ordering_chain_records_before_it_gates`
(`tests/test_apparatus.py`): wraps `Observations.record` and `check_changed` with spies logging call
order, drives one `Observer` round, and asserts `order == ["record", "check_changed"]` — the direct,
legible witness of `_observe_one`'s actual sequence, independent of any downstream count or value.
Verified against the same gate-before-record mutation used above: this test also fails (via the same
`AssertionError`, since that assert is strictly earlier than anything this spy could observe under
that specific reordering) — consistent with the reviewer's finding that the ordering is not
unguarded, only untested at the count level.

**The append discriminator, reconfirmed real.** Re-ran the reviewer's assert-safe form of mutation
(a) — `append_observation` moved below `check_changed`, `record` left in place — against both tests:
`test_g1_ordering_chain_appends_before_the_gate_fires_end_to_end` failed on its own
`assert len(ledger) == 4` (`3 == 4`), and
`test_the_ordering_chain_counts_the_moving_call_before_the_gate_fires` passed. Exactly the brief's
original prediction. No test change was needed for this half; it was already sound.

### Minors

- **Minor 1** (`check_changed`'s "there is no call site yet"): deleted rather than rewritten, and the
  surrounding paragraph updated to state what is now true — task 4 gave it a live call site, the
  residual was real, and it is now mitigated (interim) by the widened containment filter, with
  Decision 14's `Collector` as the permanent fix.
- **Minor 2** (`STOP_CODES`' "Fixture U and Fixture G1 … do not exist here"): corrected. The
  docstring now names Fixture K2 and Fixture G1 as `E-APPARATUS-RAISED`'s and
  `E-APPARATUS-CHANGED`'s individual pins respectively, and states plainly that Fixture U (task 5's
  own truncation pin) remains owed.
- **Minor 3** (mis-citation of "the plan's own correction"): fixed in the same edit as Major 2's
  action 1 — now cites the mutation table and task 4 step 2.
- **Minor 4** (docstring names task 5 where the brief said task 7): kept and clarified rather than
  reverted, per the reviewer's own adjudication ("keep the docstring; record the substitution"). The
  G1 end-to-end test's docstring now separates the two halves explicitly: the redacted-vs-bare
  rendering path is task 5's (Decision 14's `Collector`), while the exit code and `run.yaml`'s
  presence are task 7's (Decision 4's `status: failed`/exit 4/written record) — recorded here as the
  substitution the brief's step 3 anticipated differently.
- **Minor 5** (redundant "above" locator): deleted.
- **Minor 6** (Decision 11's cost-if-wrong sentence names the wrong test): appended a dated
  correction to `docs/superpowers/specs/2026-08-19-apparatus-part-b-design.md` rather than
  retro-editing Decision 11 — the sentence claimed Fixture G3's own test would fail if a future round
  probed one condition twice; it would not, since G3's per-condition value is constant, and the
  design's own mutation table already has the right guard (Part A's call-count contract). Neither
  verdict changes; Fixture G3's actual pin (a true cross-condition comparison) still discriminates.

### What was not touched

The protected `test_max_failed_fraction_is_measured_against_the_test_partition` and the batch-1 guard
pin (arms B and C) are unedited — confirmed by re-hashing the protected test's body
(`sha256: 61e63bc5dc75…`, 2327 bytes, matching the reviewer's recorded value) and by `git diff
c33f061 -- tests/test_cli.py` showing no deleted lines relative to that commit outside pure additions.
§ Errors rows were not touched (none of this fix round's changes claim one). No sentence added in
this fix round says this slice unblocks a config.
