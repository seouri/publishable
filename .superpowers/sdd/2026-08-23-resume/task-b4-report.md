# H9b batch 4 — tasks 14–18 — report

Branch `h9b-resume`. Five commits, in brief order:

| Task | Commit | What |
|---|---|---|
| 14 | `04cad73` | the lock takeover, `lock`'s third key, the wiring, twelve new tests |
| 15 | `8963071` | `resume` dispatched, arm E edited, arms A and G converted, five new tests |
| 16 | `d9b82c6` | the fourteen refusals reported not raised; **the apparatus-stop record loss closed**; `freeze`'s `parameters_hash`; seventeen § Errors rows |
| 17 | `160887d` | the documents, `spec-defects.md`, `CLAUDE.md`, § Executability |
| 18 | this commit | both consistency passes, the disclosure checked item by item |

**Suite: 3098 passed / 1 skipped / 4 xfailed at dispatch → 3132 passed / 1 skipped / 2 xfailed now.**
Twenty-three new tests; the two missing xfails are guard-pin arms A and G, converted to live tests.
Gates clean at every commit: `ruff check`, `ruff format --check`, `mypy`, `pytest`.

**The session crossed midnight.** Every dated record this batch wrote is dated **2026-08-23**, the
slice's own date and the date the dispatch names; the commit timestamps carry the real wall clock.

---

## Task 14 — the takeover, and the race against the SHIPPED code

`run_identity.take_over_dead_lock` is Ruling W's steps 1-3 — the `O_CREAT|O_EXCL` token, the
`_holder_is_dead` verdict, the unlink — released in a `finally` that covers `BaseException`. **Step 4
is `_execute_prepared`'s own `with RunLock(run_dir)`**, whose shipped comment already said so.
`RunLock.__enter__` writes `started_at`, and `_holder_is_dead` deliberately does not read it.

### The race: trials, processes, violations — and the criterion is the finding

Run against the **shipped functions in the shipped order** (`take_over_dead_lock` then `RunLock`),
five processes per trial, each contending on one run directory whose `lock` names a **real reaped
pid** on this host, started from a common wall-clock deadline. Harness in the scratchpad
(`race/contend.py`, `race/race.py`), run with the repo's interpreter from outside the repository.

| Mode | Trials × processes | Violations |
|---|---|---|
| **shipped** | 60 × 5 | **0** |
| **shipped**, with a per-process stagger between the takeover and the claim | 60 × 5 | **0** |
| **shipped**, same stagger | **120 × 5** | **0** |
| **negative control** — step 1 (the exclusive token) deleted, same stagger | 60 × 5 | **36 of 60**, up to four concurrent holders |
| **detector self-test** — no exclusion at all (no takeover, no `RunLock`) | 60 × 5 | **60 of 60** |

**The criterion had to be corrected first, and this is the entry worth carrying.** My first harness
counted *winners per trial* — the criterion the design's own probe reports ("two winners by trial
22") — and it reported violations for the **shipped** protocol, 3 of 3 trials, up to three winners.
That is not a violation: a winner releases the lock when its run ends, so a second `resume` acquiring
it afterwards is exactly what the command is for. **The violation is two holders at one time**, so
every contender now logs the interval it holds the lock for and a trial fails when two intervals
overlap. Under that criterion the shipped protocol is clean and, at first, **so was the token-less
control** — 0 of 60 — because the stale-verdict window (verdict → unlink) is nanoseconds and all five
processes read the lock at once, so all five unlink before any creates and `RunLock`'s own exclusive
create still admits exactly one. *A control that cannot fail is not a control*: the violation needs
one process to unlink a lock another **already created**, so the control got a per-process stagger
between its verdict and its unlink — and the same stagger was placed in the shipped mode between the
takeover and the claim, which is the residual window this task's siting decision is about. 36 of 60
against 0 of 60 is the measured difference the token buys.

**Two claims of the design's own probe therefore do not survive**: the winner-count criterion (it
flags the shipped protocol), and *"deleting the token produced two winners by trial 22"* as evidence
about mutual exclusion — with no stagger, deleting the token produces no overlap at all.

### The takeover window — closed rather than argued

The two residuals batch 3–4 handed me were real. `_execute_prepared`'s `with RunLock` and Ruling W's
step 4 **are** the same acquisition (the shipped comment says so), and the brief's ordering — the
takeover first, then everything else — would put the whole of `_prepare_run`, **user code included**,
between the unlink and that claim. **So the takeover is sited last**, after every comparison, after
`_prepare_run`, and after `Resumed(...)` is built (which is the last file `command_resume` reads):
between `take_over_dead_lock(run_dir)` and `with RunLock(run_dir)` there is one function call and
phase 6's `run_dir = resumed.run_dir`. Nothing reads a file, runs user code, or can block. The
measured evidence is the third row of the table above: a stagger *inside that window*, 120 trials × 5
processes, zero overlaps. The cost is stated in the code — a directory whose holder is **alive** is
refused after phases 1-5 rather than before them, which spends validation on a refusal and touches no
artifact.

### Disagreement with the brief: task 14 had to touch `cli.py`

The brief says **"Must not touch: … `cli.py`"** and also **"You unblock guard-pin arm G"** — an arm
driven through `main(["resume", …])`, which cannot reach a takeover that has no caller. The takeover
has exactly one possible caller. I made the one-line wiring in `command_resume` (plus its docstring),
and it moved no shipped behaviour at that commit: `resume` was still in `NOT_BUILT_COMMANDS`, so
`main` could not reach `command_resume` at all until task 15.

**Arm G's marker was NOT removed in task 14's commit, and that is a deferral rather than compliance.**
The arm drives `main`, so at `04cad73` it would have failed: a commit must pass its own gates.
Removed in task 15's commit, where it passes. Nothing else about the arm moved.

### Mutations — every count off a FULL unfiltered run, labelled with the commit

Read at `04cad73` (the tree that includes the rewritten two-thread test).

| # | Mutation | Result |
|---|---|---|
| M1 | the token's exclusive create → `O_CREAT` without `O_EXCL` | **2 failed**, 3117 passed, 1 skipped, 4 xfailed — `…an_existing_token_refuses_and_leaves_both_files_alone`, `…two_threads_racing_one_dead_holder_reach_one_holder` |
| M2 | unparseable JSON treated as **dead** | **1 failed**, 3118 passed — `test_every_undecidable_lock_is_held[unparseable]` |
| M3 | the liveness test **consults `started_at`** (requires it present) | **3 failed**, 3116 passed — `…a_lock_with_no_started_at_and_a_dead_pid_is_taken_over` (the owed structural replacement), `…the_token_is_released_when_the_liveness_test_raises`, `…two_threads_racing…` |
| M4 | the `finally`'s `token.unlink` deleted | **18 failed**, 3101 passed |

**M1's first form was BLIND, and that is the second finding of this task.** The two-thread test as
first written released both threads together inside the liveness syscall; with the token deleted the
full suite stayed at **1 failed** (only the token-existence test), because two threads that unlink
before either creates still meet `RunLock`'s exclusive create and one wins. *A mutation's silence is
evidence about the test.* The barrier is asymmetric now — the first arrival is held between its
verdict and the lock's replacement until the other thread **holds** the lock, which is the
stale-verdict interleaving — and the same mutation then fails it. Both counts above are post-rewrite.

**M3 is the mutation named blind in advance, made runnable.** No fixture can force a recycled pid, so
the owed replacement is structural: a lock with **no** `started_at` and a dead pid is taken over, which
a `started_at`-consulting test would have to refuse. That test exists and M3 fails it.

**Every assertion this task added has a mutation that fails IT**, not the nearest one to hand:

| Assertion | The mutation that fails it |
|---|---|
| the token is the mutex (mutual exclusion) | M1, via the two-thread test |
| the token refuses a second concurrent takeover | M1, via the token-existence test |
| an undecidable lock is held (11 arms) | M2 for the unparseable arm; each other arm is a `parametrize` case over the same guard, and M4 fails all eleven |
| `started_at` is not consulted | M3 |
| the token is released on every path, `BaseException` included | M4 |
| `lock` records three keys | not a mutation — a new assertion over a new key; a build that wrote two keys fails it by construction, and M3 is the mutation that shows the third is not *read* |

---

## Task 15 — dispatch, and all four shapes measured

`resume` leaves `NOT_BUILT_COMMANDS` and joins `OPERATION_COMMANDS`'s existing one-path arity arm; the
branch order is untouched. § Operation commands' `Status` reads `built`.

**Guard-pin arm E, edited by its sole authorized editor to the state written in advance**:
`("resume", "NOT BUILT")` → `("resume", "built")`, plus `assert ("reproduce", "NOT BUILT") in
tables["Command"]`. The `set(NOT_BUILT_COMMANDS)` equalities were not touched.

### The four shapes, through the real console script, outside the repository

Measured **before** the change (all four printed the unbuilt diagnostic at exit 2 — the disclosure's
HEAD column, confirmed) and after:

| Invocation | After | Matches the disclosure? |
|---|---|---|
| `resume` | exit 2, `` `resume` takes exactly one path and no flags`` | yes |
| `resume a b` | exit 2, the same line | yes |
| `resume --json` | exit 2, the same line | yes |
| `resume new` | exit **1**, `  error   E-RESUME-NO-IDENTITY new/identity.json is absent or unreadable, …` | yes — exit 2 → 1 with `resume`'s own refusal for a path that is not a run directory, derived by reading and confirmed by running |

**Task 16 then moved that identifier to `E-IO-FAILED`**, deliberately and in the same batch (Decision
17's third not-minted code: a path that is not a directory is `diff`'s question and `diff`'s answer).
Re-measured through the console script afterwards; exit code and substance unchanged. The design's
disclosure is corrected by appending, and the test asserts the code the build prints.

### Arm A's post-conversion assertion set

The strict `xfail` asserted only *this body fails somehow* — and it was passing because `main` printed
the unbuilt diagnostic and exited 2, which says nothing about `resume`. Live, the same body asserts,
in order:

1. `main(["resume", str(crashed)]) == EXIT_OK` — the resume completes;
2. `crashed/run.yaml` exists and parses;
3. `_h9b_run_yaml_leaves(run_doc, tmp_path) == _H9B_ARM_A_GOLDEN` — **all 94 normalized leaves, in
   order, against the golden committed in batch 1 before any comparison ran**.

Strictly more than the xfail on every count. Arm G's live assertions are likewise now enforced: two
threads, `sorted(codes) == [EXIT_OK, EXIT_WRONG]`, exactly one `E-RUN-LOCKED` in the combined output,
a `run.yaml` written, and no `lock`/`lock.takeover` left behind.

### Mutations, full suite, read at `8963071`

| # | Mutation | Result |
|---|---|---|
| M5 | `resume` dropped from `OPERATION_COMMANDS`, handler kept | **8 failed**, 3118 passed — `test_reference_cli_tables_match_what_the_cli_does[Command]`, arms A and G, and all five new dispatch tests. **Predicted in advance and confirmed: the arity tests fail on their MESSAGE half, not their exit code** (`unknown command` also returns exit 2) |
| M6 | the two-token/`NOT_BUILT_COMMANDS` block hoisted above the built branches | **0 failed**, 3126 passed — **BLIND, and the brief's own prediction is what went stale** |
| M7 | M6 plus `"resume"` re-added to `NOT_BUILT_COMMANDS` | **9 failed**, 3117 passed — the same eight as M5 plus `test_reference_cli_tables_are_parsed_at_all` |

**M6's blindness is derived, not guessed.** The brief expects a `resume <path>` fixture to catch the
hoist. That was true only while `"resume"` was a `NOT_BUILT_COMMANDS` key. After this task the mapping
holds exactly `demo`, `docs`, `list-templates`, `reproduce` — **none** of which has a built branch or a
two-token form — so hoisting the lookups cannot change any answer. What binds the invariant is the
self-maintaining document-versus-CLI pair, and M7 is the measurement: put `resume` in both places and
nine tests fail. Reported rather than left as a mutation that "passed".

*Whether any shipped test already covers a `resume <path>` dispatch*: **no** — grepped
`main(\["resume"` over `tests/` before writing; the only pre-existing callers were arm A and arm G,
both `xfail` at that point. The five tests this task adds are the first.

---

## Task 16 — the refusals, and the record loss CLOSED

### The apparatus stop now writes a record — what, and which exit code, with grounds

**Before** (pinned by task 13): a resume whose apparatus moved while the run was down raised
`E-APPARATUS-CHANGED` at the run-start round, printed it, and returned an exit code with **no
`run.yaml`** — at this and every later resume, for as long as the fact stayed moved. Every completed
execution on disk, paid for, unpublishable.

**Now**: the run-start containment records the stop on the **shared `StopSignal`** — the same three
fields `execute_plan`'s own apparatus gate sets for a mid-plan move — and falls through with no new
results into the one path that prints the stop, folds the reconstituted results back in, aggregates
them and writes `run.yaml`. Two code changes, both gated on `resumed`:

1. the containment branch sets `stop.reason/code/message` and `results = []` instead of returning,
   **for `E-APPARATUS-CHANGED` with a non-empty `resumed.prior_results` only**;
2. the *"with NO results, nothing was paid for"* early return now reads
   `if not results and (resumed is None or not resumed.prior_results)` — the sentence's own ground is
   false on a resume that has prior results. For `run` and `draft` the condition is unchanged.

`stop = StopSignal()` and `full_plan = plan` moved above the `try` (two assignments, neither of which
can fail) because the fall-through reads both.

**The exit code is `4`, and neither of the two the brief named fits.** The brief asked me to decide
`EXIT_EXTERNAL` versus `EXIT_WRONG` on H7d Part B's grounds; the answer those grounds give is a third
one, and § Exit codes' own words are the argument rather than a preference:

- `1`'s row: *"a changed apparatus fact caught before the first execution ran, **which leaves nothing
  to mark `failed` at all**"* — a qualifying clause that is exactly false here.
- `5`: *"the class you retry"*, and an apparatus that **moved** is not retryable.
- `4`: *"the run stopped: `status: failed`. There is a record of what happened"*, and its row already
  reads **`run`, `draft`, `resume` only**.

And the code is not chosen at the stop site at all: `run_status` maps `apparatus_changed` → `failed`
and the shipped final mapping maps `failed` → `EXIT_FAILED`. That is the same answer H7d Part B gives
a **mid-plan** move that completed at least one execution, which is what "on its own grounds" means
here. Task 17's brief corroborates independently: *"§ Exit codes — `3`, `4` and `5` gain their first
`resume` reader; no code is minted."*

**"The record says what it did" is asserted on `run.yaml`, not on `probes.jsonl`.** The test asserts:
`status == "failed"`; every entry in `execution.conditions[*].steps` is `completed` and there are
exactly as many as the crash's ledger recorded; `results.conditions` is non-empty;
`provenance.apparatus.ledger == "apparatus/probes.jsonl"`; `provenance.apparatus.facts` carries the
**first** attempt's `r1` for every condition (the values the results were measured *through*, never
the `r2` that stopped the run); and the ledger's last line carries `r2` — the moving observation,
appended before the gate, which is H7d Part B's own guarantee. Plus **one** diagnostic, not two
(`count(...) == 1`), and the ledger and step artifacts unchanged.

**The cost is asserted too, and it is what scopes the fix.** `run.yaml` **ends** the run, so the
second resume now refuses `E-RESUME-RUN-ENDED`. Correct for a moved fact — it cannot move back, so no
later resume could pass the gate, and the choice is a published partial record or none. An
**unreachable** apparatus is the opposite case (bring it back, resume again), so it keeps today's
behaviour and is **filed** in `spec-defects.md` with that terminality as the stated reason and an
owner that is a fact: no remaining slice has `resume`'s stop paths as its surface.

### Decision 13's containment — built, not assumed

`command_resume` is now the containment and `_resume_prepared` the decision. `except BaseException`,
`KeyboardInterrupt` re-raised **fresh and argument-less**, a non-`PublishableError` re-raised
unchanged (a core defect deserves its traceback), and a fresh `Collector` whose `credentials` is the
set `_prepare_run` resolved — handed back through a sink, because it is resolved *inside* the body
being contained. Every one of the fourteen codes now prints redacted at exit 1 instead of raising into
`main`'s un-redacted printer. A `resume` path that is not a directory reports the shipped
`E-IO-FAILED` (exit 1) through a `Collector`, because § Exit codes says of that code *"it is not a
`ContractError`"*.

Ten shipped assertions changed from `pytest.raises(ContractError)` to *exit code plus identifier on
stderr* — strictly more than the raise asserted, since a raise says nothing about what a user is
shown. M8 below is the mutation that fails all of them.

### `E-RUN-ORDER-MISMATCH` post-lock — closed, not documented around

Reachable from a hand-edited `sweep.yaml`: the recorded `execution_order` is an **input** on a resume,
and `_apply_execution_order` raises that code from *inside the lock*, under a § Errors row that
describes core's resolved state disagreeing with **itself**. `lineage.check_recorded_order` now
refuses the same disagreement **pre-lock** under `E-RESUME-PLAN-MISMATCH` — no code minted, set
equality over the planned `(condition, repeat)` pairs plus a duplicate check, and the § Errors row
covers both sites. The § Errors core raises row for `E-RUN-ORDER-MISMATCH` needed no widening, and that
is checked rather than assumed: the reader is called exactly when `recorded_plan.order ==
"randomized"`, which is exactly when `resumed.execution_order` is not `None`, which is the only
condition under which a resume applies a recorded order at all.

### § Errors — each table's lead sentence quoted, and why each row is where it is

**§ Errors `validate` reports** — its lead: *"A validate-time error is a diagnostic, not an exception
… `§ Errors core raises` covers the surfaces that raise instead … **these are the codes a command
reports**, and a code raised at load can be in both, reported here and raised there."* The thirteen
`E-RESUME-*` codes and `E-FREEZE-CONFIG-EDITED` are raises that a **command** reports through a
`Collector` — which is now literally true of all fourteen — so they go where the `E-FREEZE-*` rows
already sit, immediately after `E-FREEZE-PROBE-MISMATCH` (anchored by content, not by position).
Fifteen rows written, one per code, each covering **every** fault its code is raised for: the ledger
row names all **three** (not JSON, not an object, missing one of five keys — the amendment's item (a),
closed), `E-RESUME-NO-CONFIG` names both readers' six faults, `E-RESUME-INPUT-MOVED` both,
`E-RESUME-PLAN-MISSING` all five, `E-RESUME-PLAN-MISMATCH` both sites, `E-RESUME-ALLOCATION-STALE`
every arm. `E-FREEZE-CONFIG-EDITED`'s row states that **an absent `identity.json` is not this fault**.

**§ Errors core raises** — its lead: *"**Each carries `.code`** … Two rows in this table are not
raises, and the `Type` cell says so."* `E-RUN-LOCKED` and `E-RUN-ID-EXHAUSTED` are genuine
`ContractError` raises, so neither needs that qualification. `E-RUN-LOCKED`'s row enumerates all four
sites (the lock's own claim, the takeover's token, the takeover's liveness verdict, and the report),
says it is **reachable from `resume` and nowhere else** with the structural reason, states the liveness
rule and the `started_at` non-use, and names `lock.takeover` with its remedy. `E-RUN-ID-EXHAUSTED`'s
row names `run` and `draft` only.

### Mutations, full suite, read at `d9b82c6`

| # | Mutation | Result |
|---|---|---|
| M8 | a refusal raised into `main` instead of reported through the `Collector` | **7 failed**, 3125 passed — including `…a_resume_refusal_is_redacted_through_its_own_collector`, the credential positive control |
| M9 | the record-writing branch disabled (`if False`) | **1 failed**, 3131 passed — `…gates_against_the_original_runs_first_answered_fact` |
| M10 | the zero-results early return restored to `if not results:` | **1 failed**, 3131 passed — same test |
| M11 | `freeze`'s `parameters_hash` gate disabled | **1 failed**, 3131 passed — `…freeze_refuses_a_config_copy_edited_since_the_run_started` |
| M12 | `check_recorded_order` call removed | **1 failed**, 3131 passed — `…an_edited_execution_order_is_refused_before_the_lock` |
| M13 | the not-a-directory gate disabled | **2 failed**, 3130 passed — the `E-IO-FAILED` test and the `resume new` test |

**The fixtures' own perturbations, each made a no-op in turn** (mutations in the *fixture*, so these
counts are **selection-scoped** and labelled as such — each was run with `-k` over the matching test):

| Perturbation neutered | Matching test | Result |
|---|---|---|
| the `identity.json` hash edit (`moved[key] = recorded[key]`) | `…each_recorded_hash_that_moved…` | fails |
| the `execution_order` truncation | `…an_edited_execution_order…` | fails |
| `freeze`'s `parameters` edit (m3 → m1) | `…config_copy_edited…` | fails |
| the credential in the raised message | `…refusal_is_redacted…` | fails |
| the apparatus moving across the crash (`r2` → `r1`) | `…gates_against_the_original…` | fails |
| the non-directory path (a real directory instead) | `…no_directory_is_the_shipped_io_failure` | fails |

For the eight codes whose fixtures were built in batches 2–5, the perturbations were mutation-verified
in those batches' own M-tables; what **this** task changed about them is the assertion *mechanism*
(raise → report), and M8 is the mutation that fails every one of them. Stated as a difference rather
than claimed as new verification.

---

## Task 17 — the documents

`reference.md`: `identity.json` joins the settled-before-the-first-execution list and gains its own
subsection (five keys, and `input_manifest_hash`'s absence stated as a **rule** — the manifest is the
operand); the `config.yaml`/`repo_root.txt` sentence is **extended** to three artifacts naming which
figure each supplies; § Resuming's three comparisons get their operands and codes, plus
`E-RESUME-NO-IDENTITY`, the takeover, the liveness rule, the `started_at` non-use, the residual
`lock.takeover`, and the draft paragraph **kept and made true** rather than rewritten; the two
`allocation.json` paragraphs that said the reader *"has no reader in this build"* are now true;
§ `executions.jsonl`'s example is the **ten** keys with `attempt` and `n` deleted, plus the
Python-`json` non-promise and the *"the two never disagree"* claim now resting on `attempts` being
counted from those lines; § One execution at a time's *"reported rather than assumed dead"* sentence is
**narrowed rather than deleted** (it stays true of `run` and `draft` and of every state the liveness
test cannot answer); § What status means gains a resumed run's status and the publishing stop; § CLI
reference's `Does` cell gains the takeover; § Exit codes gains `3`/`4`/`5`'s first `resume` reader with
**no code minted**; both `<run_dir>/` trees, the `dry-run` transcript and the table of contents move.

**The `dry-run` count: the transcript now reads `and 9 fixed files`, and 9 is derived.**
`_DRY_RUN_FIXED_FILES` is eight with `identity.json`, plus `environment/uv.lock` when a lockfile was
found — which the worked example has. The shipped test asserts **8** because `run_a_project` writes no
`uv.lock`; both numbers are right for their own scenario, which is why the doc's figure is not the
test's. The amendment's *"it reads `and 8 fixed files` and is wrong on the branch today"* is confirmed:
8 was right before `identity.json` and is one short now.

**A guard pin was honoured by not colliding with it.** Arm R (editor NONE) pins every line of the four
documents carrying a worked-example literal. My first `identity.json` example showed `8e21…`/`1a2b…`/
`6b1f…` and my ledger line showed `0.607` — **four extra lines, arm R red**. The arm was not touched:
the digests are elided (`"sha256:..."`) with a sentence saying the run record is the one place a reader
compares them, and `returned` is `{}`, which is what the worked example's repeat-scope step actually
returns — the correlation is derived by the template's `aggregate`, so `{"r": 0.607}` would have
contradicted the worked example as well as the pin. **No arm moved.**

`spec-defects.md`: the five-codes filing amended to **THREE** (heading count chain updated, the two H9b
documented, the remaining three's *reason* given as surface rather than count, and the four-file sweep
re-run with **every hit attributed** — `E-RUN-LOCKED` is 3 hits, not 1); the run-start
`parameters_hash` entry **STRUCK** with its own open question quoted as what decided it; the
`resolve_contrasts` precondition **amended, not struck** (H9c still bound, `resume` discharged by
construction, the eight-line grep re-read); the `command_run`-prose entry **re-read** — still 195 lines
in 22 files, unmoved — with the one claim this slice made false **deleted** rather than rewritten
(`_execute_prepared`'s twice-stated *"byte-identical to what `command_run` held"*, false since the
`resumed` branches landed and false again since task 16's branch); the bytecode-cache disagreement
recorded as **H9d's** with the substantive reason; and H9-SCOPING § 4.5's falsification filed as its own
entry.

`CLAUDE.md`: one H9b paragraph — zero configs unblocked, the four-row table unmoved, the disclosure's
six items **plus the appended seventh** with item 3 named as the under-read one — and five things worth
carrying (the record loss, the exit-code ground, the race criterion, the blind mutations, the arm-R
collision). The remaining-order sentence now reads H9c, H9d, then H3c-3's 14.

### § Executability — the derivation

One dated entry, `### Measured on 2026-08-23 against commit d9b82c6 — after H9b`. **Zero configs
unblocked**, row by row: row 1 (8 of 8 validating) — `resume` runs at no `validate` and from no step,
so `validate`'s answer is byte-identical; row 2 (`io.reuse_from`, 0) — untouched, `resume` reads no
upstream it does not inherit through the same `_prepare_run` call; row 3 (the `report_by`-under-
`resample` gap, 7) — a construction inside `summarize_step`, phase 8, which a resumed run reaches
through the identical function, and the reconstitution exists precisely so phase 8 sees the same
results either way; row 4 (free of every core-side dependency, 1) — `resume` needs a crashed run
directory, a property of an operator's history and not of a config, and none of the nine declares an
`apparatus_probe`, a `study`, a `fold` or a group axis, so none can reach the baseline replay, the
takeover or the allocation reader. **The four-row block was extracted, not retyped**, by the two
independent methods the H9a entry describes (a walk to the last `| Figure | Count | Visible to` header,
and a fixed six-line slice) — `diff` empty, six lines each — so its cells still name **H8a**. **No
fifth number minted**, and the one behaviour change worth naming (the publishing stop) is stated with
why it moves no row.

---

## Task 18 — both passes

### Mechanical, over `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md`, `docs/feasibility-llm-growth-studies.md`, `CLAUDE.md`

A throwaway script (scratchpad `mech.py`), fenced blocks skipped everywhere. **0 problems.** Checks
and their can-fail probes — each probe appends one line to **every** file in the list, so a check that
cannot fire shows as `0 problem(s)`:

| Check | Probe | Result |
|---|---|---|
| duplicate heading anchors | append `## Run identity` | **1** (only `reference.md` has that heading) |
| trailing whitespace | a line ending in a space | **6** |
| tabs | a tab-indented line | **6** |
| invisible unicode (`Cf`) | — | no probe; 0 hits, and the class is checked per character |
| table row width vs header | a 3-cell row under a 2-cell header | **6** |
| empty table row | `\|  \|  \|` under a header | **6** |
| `×` not `x` | `a 3 x 5 grid` | **6** |
| en dash in a heading | `## An en–dash heading` | **6** |
| relative links resolve | `[nope](docs/no-such-file.md)` | **6** |
| `#anchor`s resolve | `[nope](#no-such-anchor-at-all)` | **6** |

**Two of my own checks were wrong before they were right, and both were found by the probes.** The
slugger collapsed runs of whitespace, so every link to `#secrets--credentials` (from *Secrets &
credentials*) read as dead — GitHub replaces each space with one hyphen and keeps underscores. And the
table-width check counted `|` inside code spans and escaped `\|`, which flagged three legitimate rows.
The empty-row check needed two corrections: it must read the **raw** cells (a row whose cells are all
code spans is not empty) and must not treat `|  |  |` as a separator.

**Mechanical hygiene over the development-record files this slice edited** (`spec-defects.md`, the
design, the plan) — reported, never fixed, since a dated record is appended to: **one finding**, and it
predates this batch — the design's `### Decision 8 — … travels into phases 6–10` heading carries an **en
dash**, which GitHub's slugger strips (`…phases-610`). **Nothing links to that anchor** (grepped
`phases-6` over `docs/`, `.superpowers/`, `CLAUDE.md`: zero hits), so it is a latent hazard rather than
a broken link, and it is recorded here rather than retro-edited.

### Cross-document, over the four documents only

- **Config completeness — § The one config file does not move, checked and said so.** `identity.json`
  is a run artifact, not a config field: the only `identity` inside that section is
  `key: patient_id  # stable, unique identity`, unrelated prose.
- **Declared versus derived — `attempts` is derived, and no passage shows it as an input.** Every
  occurrence in the four documents is an *output*: `run.yaml`'s five example lines (one carrying
  `# >1 only after resume`) and the § Resuming paragraph that defines it as a count of ledger records.
- **Removed strings, swept over the four documents, `CLAUDE.md` and the feasibility analysis, with the
  file list named and never the output filtered**: `"attempt"` → **0**, `"attempt":` → **0**,
  `"n": {` → **0**. Can-fail control on the same list: `"attempts"` → 1 hit (the feasibility analysis'
  own plugin dict at line 923, unrelated to the ledger) and `attempts:` → 6 hits in `reference.md`,
  every one attributed above.
- **Enum comments**: none added or changed by this slice.
- **Schema fields in prose**: `identity.json`'s five keys appear in prose and in the artifact example,
  in the same order, and nowhere else.
- **Versions**: untouched — `CITATION.cff` 0.1.0, README's v0.x notice unchanged.
- **The shared worked example**: unchanged, and pinned rather than asserted — guard-pin arm R passes
  for all three documents, which is what the collision above is about. `cohort-pilot`'s intervals were
  not narrowed and not touched.

### The disclosure, checked item by item against the code

Corrected by **appending** to the design (§ Correction, 2026-08-23, from batch 4):

| Item | Verdict |
|---|---|
| 1 — `run`, `draft` **and `resume`** write `identity.json` | **WRONG**: the write sits inside `_execute_prepared`'s `if resumed is None:` block. `run` and `draft` write it; a resume reads it and writes nothing. Corrected |
| 2 — the ledger's two new keys | stands |
| 3 — `dry-run` prints 8 where it printed 7 | stands (and the doc's own scenario is 9, with `uv.lock`) |
| 4 — `attempts` becomes a count | stands |
| 5 — the four invocation shapes | exit codes and substance stand; **the identifier for `resume new` moved to `E-IO-FAILED`** in task 16, recorded |
| 6 — `freeze` gains `E-FREEZE-CONFIG-EDITED` | stands |
| A2 — `replay_ledger`'s defaulted code parameter | stands |
| **8 (new)** — a resume stopped by a moved apparatus writes the record, exit `4` | **added**: it is the one place `_execute_prepared`'s own control flow moved |

---

## Concerns for the reviewer

1. **The takeover's siting is a deliberate deviation from the design's literal step order**, argued in
   the code and measured by the race. If the controller wants the refusal to come *before* phases 1-5,
   that is a second liveness read and a different design.
2. **`_h9b_resume` still removes the stale lock by hand**, so twelve tests do not exercise the
   takeover; three of them re-write a `{"host": "h", "pid": 1}` lock between arms, which a takeover
   would (correctly) refuse as *cannot tell*. The end-to-end pin is arm G. Left alone deliberately;
   changing it means editing three shipped tests to mint real dead pids.
3. **`freeze`'s `_assert_refused` helper takes a `code` argument it cannot check** — `_Refused` carries
   only `exit_code`, so ten shipped gate tests assert *that* a refusal happened and not *which*. Not
   touched; my two new arms assert on stderr instead.
4. **The unreachable-apparatus half of the record loss is filed, not closed**, with the terminality of
   `run.yaml` as the reason. A reviewer who disagrees should argue against that paragraph.
