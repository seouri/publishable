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
