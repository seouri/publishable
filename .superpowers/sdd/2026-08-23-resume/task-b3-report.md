# H9b batch 3 — tasks 10, 11, 12, 13 — report

**Written 2026-08-23.** Four commits, one per task, plus one comment-only follow-up:

| Task | Commit | What landed |
|---|---|---|
| 10 | `1253a3b` | `sweep.yaml`'s recorded plan: `lineage.read_sweep_plan`, `lineage.check_recorded_conditions`, and the order a resume executes in |
| 11 | `b867663` | `allocation.json` read rather than re-drawn: `lineage.read_allocation`, `cli._resumed_allocation` |
| 12 | `bb522fa` | the input manifest compared not rebuilt: the refusal's three arms and one discriminating pin |
| 13 | `7c3eda4` | the apparatus baseline replayed under `resume`'s own code, and a `cannot happen` comment made to happen |
| 13 follow-up | `5fef506` | the containment filter's union named load-bearing, after the mutation that shows it is |

**Suite: 3079 passed, 1 skipped, 4 xfailed before this batch → 3098 passed, 1 skipped, 4 xfailed
after, at `5fef506`.** +19 tests (7 for task 10, 6 for task 11, 2 for task 12, 4 for task 13). No
existing test's expectation moved. One existing test gained an argument: `test_h9b_resumed_is_frozen_
and_replace_works`'s `Resumed(...)` constructor now passes `execution_order=None`, because task 10's
field is **deliberately not defaulted** — a default would let a caller that forgot to read `sweep.yaml`
re-realize the order silently. That is an addition to a constructor call, not a weakened assertion:
every assertion in that test is unchanged.

**No guard-pin arm was opened.** The two strict `xfail`s are untouched; arm A's remover is task 15.

---

## Task 10 — `sweep.yaml` is read, not re-derived

`lineage.RecordedPlan` (frozen, tuples) plus `read_sweep_plan` and `check_recorded_conditions`.
`command_resume` reads the plan and cross-checks it **after** the hash and manifest comparisons and
**before** the lock, so a refusal has taken no lock and touched no artifact. `Resumed` gains
`execution_order`, applied in `_execute_prepared` instead of re-realizing the shuffle.

**The grep the brief asked for, and what it found.** `grep -rn 'sweep.yaml' src/publishable/*.py` — 30
lines, every one attributed: `freeze.py` at `:111` (a docstring row), `:272`, `:278`, `:289`, `:297`
(the reader), `:322`, `:353` (the cross-check); `cli.py` at `:257` (`_apply_execution_order`'s
docstring), `:2152`, `:2373`, `:3234`, `:4747`, `:4789`, `:4880` (this batch's own comments and
docstrings), `:4901`, `:4911` (`_DRY_RUN_FIXED_FILES` and its comment); `sweep.py` at `:74`, `:295`,
`:342`, `:358`, `:802` (`sweep_document` and prose); `run_record.py` at `:229`, `:275` (comments);
`lineage.py`'s own new lines. **`freeze`'s reader was measured and does not fit**, and I did not reuse
it: it is inline in `command_freeze`, reports through `_refuse`/`Collector` and **returns an exit code
rather than raising**, its codes are `E-FREEZE-PLAN-MISSING`/`-MISMATCH`, and it reads `conditions`
**only** — never `order` or `execution_order`, the two fields `resume` needs most. What I copied is the
*shape*: the four-tuple, in recorded order, named as copied at the cross-check.

**One decision the brief left open, taken and stated.** `_apply_execution_order` regroups repeat
executions **pair-major** where `build_plan` lays them out step-major, and the shipped call site applies
it only under `order: randomized`. So "order the rebuilt plan by `execution_order`" cannot mean
*unconditionally*: applying it to a resumed `as_declared` run would execute in an order the first
attempt did not, with `sweep.yaml` still recording the declared sequence. `resume` therefore takes the
**mode** from the record too — `Resumed.execution_order` is the recorded pairs when the recorded `order`
is `randomized` and `None` when it is `as_declared`. **No order-mismatch refusal was minted**: the
record is the authority, and a fifteenth code would be charter growth.

**Measured, not assumed:** `_apply_execution_order` already raises `E-RUN-ORDER-MISMATCH` when the
recorded pairs do not cover the plan's repeat executions, so a hand-edited `execution_order` that
**drops** a pair raises rather than silently executing a shorter plan against `planned=len(full_plan)`.
No new guard was needed, and the reader adds none.

## Task 11 — `allocation.json` read rather than re-drawn

`lineage.read_allocation` (absent → `None`, unparseable → `E-RESUME-ALLOCATION-STALE`) and
`cli._resumed_allocation`, which replaces four `Prepared` fields through `dataclasses.replace`.

**Ruling S, pre-empted because a reviewer will read one line as a violation.** `_resolved_group_axes`,
`units.arm_members` and `_resolved_holdout` stay exactly where they are, in their current order, inside
`_prepare_run`. `_resumed_allocation` calls `arm_members` **again**, on the overridden axes — that is
overriding a *result*, one step past the seam, not moving a call. It is the alternative that would break
the rule this project already paid for: re-deriving the per-condition mapping by hand here would make
this function a second producer of arm membership. `eval_roster` is likewise re-derived through
`_evaluation_roster` from the overridden holdout, with `_prepare_run`'s own
`assert (eval_roster is None) == (roster is None)` restated on this path, which had no counterpart of it.

**Checked and found not downstream of the override:** `beside_n`, `weights`, `weighted_beside`,
`clusters`, `partitions`, `fold_members`, `plan` and `cfgs` are all computed *above*
`_resolved_group_axes`/`_resolved_holdout` in `_prepare_run`, so `group_axes`, `holdout_plan`,
`eval_roster` and `arm_members_map` are the whole downstream set. `holdout_train` is built inside
`_execute_prepared` from `holdout_plan.train`, so it picks the override up.

**Seed and strata come from the record, not from the recomputed plans**, which is what makes
`provenance.allocation_hash` cover the file on disk: `_execute_prepared` hashes
`build_allocation_document(group_axes, holdout_plan)` and a resume never rewrites `allocation.json`, so
anything taken from the recomputed plans would publish a hash of a document no file holds. Pinned as a
round trip (`build_allocation_document(...) == the recorded document`), and the fixture's edited
document carries a `seed` the config does **not** resolve to — without that line the round-trip arm was
blind, since the declared seed and the recomputed one agree.

**The fold sentence, resolved narrowly and stated as resolved.** The brief's "Fold partitions come from
`sweep.yaml`'s own `partitions` block" is read as *where fold partitions live* — i.e. why this task does
not read them — rather than as an instruction to override them. Grounds: the task's refusal, both
mutations and the fixture are all about `allocation.json`; `partition_units` is a pure function of the
roster and the design digest, so correct and buggy readings coincide for every fixture available here
and a fold override would be an untested derivation with an invented refusal. Named in
`_resumed_allocation`'s docstring rather than left silent. **If the controller reads that sentence as an
instruction, it is unbuilt and this is the disagreement.**

**One design/code disagreement found while building the fixtures.** The two halves of `allocation.json`
**cannot be exercised by one config on this build**: `data.units.holdout` beside a cell structure is
refused by name (`E-DATA-HOLDOUT-CELLS`, H3d's, owned by H3c-3's remaining 14). Measured — the combined
fixture was written first and refused at `validate`, exit 1. So the arms fixture declares a drawn axis
and no holdout, and the holdout fixture a drawn holdout and no axis. Recorded in
`_h9b_holdout_project`'s docstring.

## Task 12 — the manifest compared, not rebuilt

The comparison and the threading landed with task 9's entry point; **this task is pins, and I say so
plainly rather than manufacturing implementation.** Two tests:

1. the refusal, with three arms — a file **added** under `input_dir` (the arm
   `verify_manifest`'s `present - manifest` branch answers, and the one that cannot perturb the roster),
   a file whose **content** moved, and a `manifest/input.json` that cannot be read — each
   `E-RESUME-INPUT-MOVED`, each with the ledger unchanged and no `run.yaml`, each with a control
   between arms;
2. **the discriminating pin on which manifest travels.**

**Why the second exists, and a claim about another test, grepped.** `manifest_hash` covers each file's
`st_mtime_ns`, and the pre-lock check is an equality between the fresh manifest and the recorded one —
so on every directory a resume accepts the two hashes are equal, and an assertion comparing `run.yaml`'s
figure against `manifest/input.json`'s digest passes under both readings. `input_manifest_hash` in this
file's H9b region: `22597` (a docstring), `22735` (arm A's golden, normalized), `23118`/`23120`
(`identity.json`'s deliberate absence), `23981`/`23998` (task 9's assertion), and `24673`+ (this task's).
**The task-9 assertion at `23998` is exactly the blind shape**, and the mutation proves it: with the
fresh manifest travelling, that test **passed** and only the new one failed. It is left in place — it
asserts a claim a reader wants to see — and the new test hand-assembles a `Resumed` whose
`recorded_manifest` differs from the fresh one in one file's `mtime` and nothing else, which
`manifest_hash` covers and `verify_manifest` does not read under `hash_all`.

One fixture correction worth carrying: the content arm first renamed a roster column, which fails **unit
resolution** instead (`E-UNITS-ATTR-MISSING` inside `_prepare_run`, which **returns** an exit code rather
than raising) — so that edit tested the wrong refusal. It appends a row now, and the reason is in the
test.

## Task 13 — the apparatus baseline replayed

`apparatus.replay_ledger` gains `code` defaulting to `"E-FREEZE-LEDGER-UNREADABLE"`, so `freeze` is
byte-identical; `command_resume` passes `"E-RESUME-PROBES-UNREADABLE"`. The replayed `Observations` is
threaded into the `Observer` through the `observations=` keyword H8b already built for `freeze`, so the
change at that call site is one line. The shipped code is **not** renamed.

**`resumed.baseline` is wired and read** (the brief's item 1): it is the third argument of the
`Observer` construction, and it is pinned by the differing-probe fixture below, not by a grep. It is
**EMPTY, not `None`, for a run that never probed** — `replay_ledger` returns an empty `Observations`
for an absent ledger, which is exactly what an `Observer` builds for itself — so **`freeze`'s
`E-FREEZE-LEDGER-MISSING` is not inherited** and this path needs no branch for the absent case. The
field's docstring says so.

**The fixture makes the two readings differ**, which is what H9a's Fixture Y did not: an installed probe
reads its answer from a JSON **file** the fixture rewrites between the crash and the resume, the crash
is `os._exit` in a subprocess carrying the distribution on `PYTHONPATH` (measured: without it the child
reports `E-PROBE-UNKNOWN` instead of crashing where the fixture aims), and both directions are pinned —
the moved apparatus does not complete, the unmoved one completes and publishes
`provenance.apparatus.facts` carrying the **first** attempt's answer.

A second fixture correction worth carrying: two tests sharing one probe **module name** fail the second
time with `E-PLUGIN-DECORATOR`, because a module already in `sys.modules` is not re-imported and its
decorator never re-runs while the `registries` fixture has cleared `PROBES`. Each test now has its own
module name, which is why every shipped probe fixture in that file has one too.

### The record loss this task makes real — ROUTED HERE AND UNFILED

**Yes: my work makes it real, and it is measured.** Before this task a resume of a run whose apparatus
had moved set its own baseline and completed at exit 0. Now:

- a resume of a crashed run whose apparatus moved while it was down raises `E-APPARATUS-CHANGED` at the
  **run-start** round, prints it redacted, and returns **`EXIT_WRONG` (1)** — measured, and pinned as
  that literal;
- **no `run.yaml` is written, at this or any later resume**: the second resume returns the same code, so
  every completed execution stays on disk, paid for, and unpublishable. The test asserts both the
  identity of the surviving artifacts and the repeat refusal.

**Task 16 owns the justification** (whether that state deserves `EXIT_EXTERNAL`, and whether an
un-completable resume deserves a refusal of its own that says so). I did **not** change the exit code:
deciding it in the task that made the state reachable would be deciding a question by side effect.

**It is NOT filed in `spec-defects.md` and NOT appended to the plan**, because all four task briefs say
*"Must not touch: … any `*.md`"* and both routes are `*.md`. Stating the discrepancy rather than
self-authorizing, on batch 1's own precedent: **the controller must route this**, since a report's own
escalation is not a filing. The in-code route exists — two corrected comments at the containment site
name it and point here.

### A comment that said `this cannot happen`, made to happen

`_execute_prepared`'s probe containment carried two claims that were true when written and false after
this task: that **no** path reaches that `try` carrying a `STOP_CODES` member, and that *"narrowing this
filter to `APPARATUS_CODES` leaves the full suite unchanged"*. A resume's run-start round **has** a prior
observation to disagree with, so `E-APPARATUS-CHANGED` reaches it. Both comments are corrected in place
(`7c3eda4`, `5fef506`), and the new claim was **measured, not argued**: narrowing the filter to
`APPARATUS_CODES` fails the new test, full suite, one failure.

---

## Mutations — every count off a FULL unfiltered run, labelled with the commit it was read at

| # | Mutation | Read at | Result |
|---|---|---|---|
| M1 | `check_recorded_conditions` compares `index`/`label` only (the `values`/`is_baseline` branches deleted) | `1253a3b` | **2 failed**, 3084 passed, 1 skipped, 4 xfailed — `test_h9b_the_cross_check_is_over_the_full_four_tuple` and `test_h9b_a_resume_refuses_a_moved_condition_before_it_executes` |
| M2 | a resume re-realizes the order (`_apply_execution_order(plan, execution_order)` in the `resumed` branch) | `1253a3b` | **1 failed**, 3085 passed — `test_h9b_a_resume_executes_the_recorded_order_not_a_re_realization` |
| M3 | the recorded order applied unconditionally (`execution_order=recorded_plan.execution_order`, no mode branch) | `1253a3b` | **1 failed**, 3085 passed — `test_h9b_an_as_declared_resume_keeps_the_step_major_layout` |
| M4 | the allocation override skipped | `b867663` | **1 failed**, 3091 passed — `test_h9b_a_resume_executes_the_recorded_arms_not_a_second_draw` |
| M5 | a membership naming an absent unit accepted (`if False`) | `b867663` | **1 failed**, 3091 passed — `test_h9b_an_allocation_that_cannot_be_applied_is_refused` |
| M6 | `seed` taken from the recomputed plan instead of the record | `b867663` | **1 failed**, 3091 passed — `test_h9b_the_allocation_override_replaces_four_fields_and_round_trips_the_rest` |
| M7 | the fresh manifest compared against itself | `bb522fa` | **1 failed**, 3093 passed — `test_h9b_inputs_that_moved_between_the_crash_and_the_resume_are_refused` |
| M8 | the fresh manifest used in phases 6–10 | `bb522fa` | **1 failed**, 3093 passed — `test_h9b_the_recorded_manifest_is_what_travels_into_phases_6_to_10` (and task 9's `…keeps_every_units_result_and_the_recorded_manifest` **passed**, which is the blindness claim above, measured) |
| M9 | `baseline=None` — the replay dropped | `7c3eda4` | **2 failed**, 3096 passed — `…gates_against_the_original_runs_first_answered_fact` and `…reports_a_mangled_probe_ledger_as_its_own_code` |
| M10 | `replay_ledger`'s two-phase filter widened (`if False: continue`) | `7c3eda4` | **4 failed**, 3094 passed — all four are **shipped H8b tests** (`test_replay_ledger_excludes_freeze_and_dry_run_lines…`, `…an_unrecognized_phase_is_skipped…`, `test_m8_fixture_a_second_freezes_own_answer…`, `test_freeze.py::test_m8_two_exit_codes_through_main…`). The brief's prescribed fixture **already exists**, so no duplicate was written; this is reported rather than claimed as new coverage |
| M11 | the containment filter narrowed to `APPARATUS_CODES` | `7c3eda4` | **1 failed**, 3097 passed — `…gates_against_the_original_runs_first_answered_fact`. This is what makes the corrected comment's new claim measured |
| M12 | `resume` passes `replay_ledger`'s default (`freeze`) code | `7c3eda4` | **1 failed**, 3097 passed — `…reports_a_mangled_probe_ledger_as_its_own_code` |

**Every assertion this batch added or moved has a mutation that fails it**, and the mapping is the table
above read the other way:

| Assertion | The mutation that fails IT |
|---|---|
| the four-tuple cross-check (`values` arm) | M1 |
| the resumed order follows the record | M2 |
| the `as_declared` layout is unchanged by a resume | M3 |
| the resumed arms are the record's | M4 |
| a stale membership refuses | M5 |
| the rebuilt allocation document equals the file | M6 |
| moved inputs refuse | M7 |
| `run.yaml`'s `input_manifest_hash` is the recorded figure | M8 |
| the resume is gated against the original baseline | M9 (and M11 independently) |
| `resume` prints its own probe-ledger code | M12 |
| the two-phase filter | M10 (shipped H8b tests) |
| `Resumed(execution_order=None)` in the frozen-class test | not an assertion — an added constructor argument; the test's assertions are unchanged |

## Disagreements with the brief, the plan and the code — five, not zero

1. **Task 10's "order the rebuilt plan by `execution_order`" cannot be unconditional.** The mode comes
   from the record; grounds above.
2. **Task 11's fold sentence is ambiguous** and is resolved narrowly (no fold override), with grounds
   in the code and above.
3. **Task 11's two halves cannot share one config** — `E-DATA-HOLDOUT-CELLS` refuses a holdout beside a
   group axis. Measured at `validate`.
4. **Task 12 needed no implementation** — task 9 shipped both halves — and the existing assertion for
   the half it shipped is **blind**, measured by M8.
5. **Task 13 falsified two shipped comments** at the probe containment site, one of which asserted a
   suite-wide mutation result that is no longer true. Corrected in place; the replacement claim was
   measured by M11.

## Two things the earlier batches left, answered

- **`resumed.baseline`**: wired into the `Observer` and pinned by the differing-probe fixture. Not
  deleted.
- **The apparatus-stop record loss**: made real by this task, measured (exit 1, no `run.yaml`, repeat
  resume identical), and routed to task 16 in this report and in two code comments. **Unfiled in
  `spec-defects.md` because the briefs forbid touching `*.md` — the controller must route it.**
- **The falsified design fixtures (C and D)**: checked before building. Nothing in this batch rests on
  `attempts: 2` for a crashed triple or on reconstituting a non-`completed` record. The one fixture
  that could have — task 12's ledger-length control — asserts the ledger is **unchanged** by a refusal,
  which is independent of when a line is written.

---

## Appended 2026-08-23, after review — four corrections and one disclosure

A dated record is appended to, never retro-edited. Everything above stands as written; these are the
corrections.

**A. One real defect in this batch's own code, found and closed at `a62084b`.** `read_sweep_plan`
checked the shape of `order` and of each `execution_order` entry and **not** of the `conditions`
entries: a non-mapping entry was silently coerced to `{}` — which the docstring's "each entry exactly
as the file holds it" denied — and a non-mapping `values` reached `dict(...)` in
`check_recorded_conditions`. **Measured before it was fixed**, by driving the two functions over
hand-written files: a bare-string entry reported an `index` disagreement (a field-level message for a
file holding no fields), `values: [1, 2]` raised a bare `TypeError`, and `values: "abc"` a bare
`ValueError` — both un-coded, both out of `main`. This is the **identical** *presence checked, shape
not* Major this slice's batch 4 review found one function over, in `apparatus.replay_ledger`. Both are
now `E-RESUME-PLAN-MISMATCH`, which is `freeze`'s own code for a non-mapping condition entry, and the
reader coerces nothing. Three arms added to `test_h9b_the_cross_check_is_over_the_full_four_tuple`.

| # | Mutation | Read at | Result |
|---|---|---|---|
| M13 | the shape faults answered with `E-RESUME-PLAN-MISSING` instead | `a62084b` | **1 failed**, 3097 passed, 1 skipped, 4 xfailed — `test_h9b_the_cross_check_is_over_the_full_four_tuple` |

**B. The record-loss claim above is broader than what was measured, and is corrected here.** The
sentence "no `run.yaml` is written, at this or any later resume" is true **while the apparatus remains
moved**. `test_h9b_a_resume_through_an_unmoved_apparatus_completes`, three functions below, shows the
same crashed directory completing at exit 0 once the apparatus is back — so the accurate claim is: *a
resume cannot complete for as long as the fact stays moved, and restoring the apparatus lets it
complete.* The finding task 16 inherits survives that narrowing intact: the run cannot be published
while the world is in the state it is in, and nothing in the record or the exit code says the executions
are still there.

**C. One code a user can reach that this report did not name.** A recorded `execution_order` that
**drops** a pair (or is empty under a recorded `randomized`) is refused by `_apply_execution_order`'s
`E-RUN-ORDER-MISMATCH` — a code whose own docstring says *core bugs, not user mistakes* — raised from
inside `_execute_prepared` and therefore **after the lock is taken**, unlike every other resume refusal,
which is pre-lock and named for `resume`. No artifact is written and the lock unwinds, so the failure is
legible; the code and the placement are still wrong for a hand-edited file. **Deliberately not fixed
here**: the coverage check would belong in `check_recorded_conditions` under the existing
`E-RESUME-PLAN-MISMATCH` and mints nothing, but it is a refusal's diagnostic, which is task 16's
surface. Named so task 16 sees it rather than discovers it.

**D. Disclosure: `_resumed_allocation` refuses more than the brief names.** The brief names two faults
(a membership naming an absent unit, a file that will not parse); the code refuses five states — the
axis set disagreeing, an axis's level set disagreeing, the holdout's presence disagreeing in either
direction, and the roster having **gained** a unit as well as having lost one. All are *the record
cannot be applied to this roster*, all are under the one code the brief names, and **no code was minted
that the briefs do not name** — the codes this batch emits are exactly `E-RESUME-PLAN-MISSING`,
`E-RESUME-PLAN-MISMATCH`, `E-RESUME-ALLOCATION-STALE`, `E-RESUME-INPUT-MOVED` and
`E-RESUME-PROBES-UNREADABLE`. The both-directions guard is now bounded in the docstring: union-equals-
roster holds for the two realized methods (`by_attribute` per `arms_of`'s set-equality rule, `random`
per the shipped draw), and a future partial-partition method would make it refuse a legitimate resume.

**E. One more stale claim of the class this batch already corrected twice.** `Observer.__init__`'s
comment said *"every shipped caller … **omits** this and gets a fresh `Observations`"*; after task 13
`cli.py`'s one call site passes the keyword explicitly (`None` for `run`/`draft`, the replay for a
resume). Behaviour unchanged, sentence narrowed in place at `a62084b`. `Observations.record` and
`PHASES` — the two things the brief forbids touching — were not touched.

**Suite unchanged by this round: 3098 passed, 1 skipped, 4 xfailed at `a62084b`.**

**F. Two mechanical notes on this batch's own commits.** `.superpowers/sdd/.gitignore` was found
clobbered to a bare `*` and was **committed in that state inside task 10's commit** (`1253a3b`) — so
this report file was untracked and the first attempt to commit it (`afc6a05`) committed a stray
`tests/test_cli.py` docstring correction under the report's message and nothing else. The gitignore's
content is restored from `78bb794` and the report is committed with `git add -f` at `1305557`, per
CLAUDE.md § The development record. No record was lost: the only file created after the clobber is this
one.
