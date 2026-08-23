# H9b batch 2 — tasks 5, 6, 7, 8, 9 — report

**Written 2026-08-23.** Five commits, one per task, in order:

| Task | Commit | What it built |
|---|---|---|
| 5 | `d4e0afd` | `executions.jsonl` gains `recorded_columns` and `returned`; guard-pin arm C edited |
| 6 | `ab2ed50` | `attempts` from the ledger; `lineage`'s ledger reader — the first in `src/` |
| 7 | `2294a22` | `cli.Resumed`; one optional parameter on `_execute_prepared` |
| 8 | `665f68e` | `cli._reconstitute` |
| 9 | `d8b8a35` | `resumed` wired into phases 6-10; `cli.command_resume` |

**Gates, at `d8b8a35`:** `ruff check` clean, `ruff format --check` clean, `mypy` clean over 52 source
files, `uv run pytest` **3078 passed, 1 skipped, 4 xfailed** — 3053 + **25** new tests, the same 1
skipped and the same 4 xfailed the branch started with. Every pytest run below was run **directly, in
the foreground**, and every count is **full-suite** unless the line says otherwise.

---

## The dispatch's Ruling W section is misaimed at this batch, and I did not run the race

**The lock is plan task 14 (batch 6) and `resume`'s dispatch is task 15 (batch 7). Neither is in
5-9.** Task 9's own brief says *"take the lock (task 14)"*, and guard-pin arm G's `xfail` marker names
task 14 as its remover. So the five-process race, its negative control, the two liveness directions
and the undecidable (foreign-host) case are **task 14's deliverable**.

I did not run them, deliberately. A harness racing a protocol I wrote in a scratchpad would measure a
**reimplementation** — code that will not ship — which is the *answering a question with a proxy* fault
this repository has a section about. What I did instead is leave task 14 the two findings below (§ The
lock residual task 14 inherits), so it starts from a measured position rather than rediscovering it.

---

## What each task did, and what it found

### Task 5 — the ledger's two new keys

`execute_plan`'s single ledger write gains `recorded_columns` (the sorted union of the keys the rows
`io` holds carry, `"unit"` excluded) and `returned` (through `run_record.summary_values`).

`summary_values` is imported **function-locally**, and that is not style: `run_record` imports `runner`
for `ExecutionResult`, so a module-level import would close the cycle `runner → run_record → runner`.
Stated in the code at the import.

**`json.dumps`' shipped `allow_nan=True` is kept** (design appendix A1). A fixture whose repeat step
returns `float("nan")` asserts the ledger's raw text holds `NaN` **and** that the value reads back as
`nan` rather than `None` — the raw-text half because the defect could live in the serialization and a
normalising reader would hide it.

**Guard-pin arm C** (`test_h9a_arm_d_the_executions_jsonl_line_key_set`) edited to exactly its advance
post-edit set: `{step, scope, condition, repeat, status, started_at, wall_seconds, error, returned,
recorded_columns}` — **two keys added, none removed, nothing reordered**, and no assertion beside it
touched. The diff is eight literal lines plus two.

**FINDING (arm C's editor): the design says task 6, my brief says task 5, and I edited it as task 5.**
Design § The guard pin gives arm C the parenthetical *"The ledger task only (plan task 6)"*, and the
appended § Correction from batch 1 declares that parenthetical **correct** while fixing arms B and D's.
But plan task 5 is the task that adds the two keys; task 6 computes `attempts` from the file and adds
no key. My brief opens *"You are the SOLE AUTHORIZED EDITOR of guard-pin arm C"*. Tasks 5 and 6 are one
batch, so no task edited it out of turn either way. I took the third option the design's own correction
names: the edit is the specified one, and the docstring now **states the discrepancy** rather than
resolving it silently or rewriting the clause.

**Greps run, every hit attributed.** `grep -n "Estimate(" tests/test_cli.py` → 10 hits, and the answer
is the opposite of what the brief's *"check in advance that no shipped fixture already has one"*
expects: **shipped fixtures DO put a `summary` step returning an `Estimate` through a real run** (the
`W-STEP-ESTIMATE-N` family at `_ESTIMATE_SUMMARY_STEP` and its neighbours, plus H5a's and H8c's summary
steps). So mutation 5.1 is caught by shipped tests as well as by mine — reported rather than claimed
otherwise. `grep -n "recorded_columns" tests/test_cli.py` before this task → 2 hits: batch 1's arm-A
fixture comment, and `test_a_non_numeric_recorded_by_column_warns_and_suppresses_the_strata`'s
docstring, which uses the phrase for an unrelated concept (a stats-side recorded-column set).

### Task 6 — `attempts`, and the first reader of this ledger

`lineage.read_execution_ledger`, `lineage.ledger_key` and `lineage.attempt_counts`.
`assemble_run_yaml` gains one optional `attempts` mapping, threaded to `_execution_block`, which writes
`1` when it is absent — byte-identical to what it wrote before.

**Where the reader lives, and why:** `lineage.py`, whose own module docstring makes it the home of *the
reader over what an assembler wrote*. `run_record` refuses the job on its own first line (*"Assembles
only — computes nothing"*), and `runner` is imported **by** `run_record`, so a reader placed in `runner`
could not be called from `run_record` at all. One reader, two callers (`attempt_counts` and task 8's
reconstitution).

**Correction 21's grep, re-run before writing the reader:** `grep -rn "executions.jsonl"
src/publishable/*.py` printed **eight** lines and **no reader** — `apparatus.py:483`/`:485` (prose),
`cli.py:2712` (a comment), `cli.py:4257` (`_DRY_RUN_FIXED_FILES`' entry), and four in `runner.py`, of
which one is the writer's path binding, one is task 5's own new comment and two are prose.
`apparatus.replay_ledger` and `freeze._ledger_probe_names` read `apparatus/probes.jsonl`, a different
file. Re-run after the task: 15 lines, the seven new ones all mine.

**`run_status`'s bare assert: NOT changed, and its docstring not edited.** It is satisfied by
construction — task 9 passes `planned=len(full_plan)` and prepends the reconstituted triples, so
`len(results) >= planned` holds. Verified end to end by a wrapper (see task 9). H7d Part B's
`max_failed_fraction` pin is untouched.

A mangled ledger line raises `E-RESUME-LEDGER-UNREADABLE` rather than reading as *this triple never
ran*, which would make `resume` re-execute an already-paid-for execution or publish intervals over the
remainder.

### Task 7 — `Resumed`

Frozen dataclass, five fields, `prior_results` a tuple. `_execute_prepared` gains `resumed: Resumed |
None = None` **at its signature only**; the diff's sole deletion in that function is the old signature
line, so the 36-field unpack block is provably unchanged (correction 19). Nothing read the parameter at
this commit, and the tests assert the **signature and frozenness**, never behaviour — a behavioural
assertion here is one task 9 would have to delete, and deleting an assertion is indistinguishable from
weakening a pin.

### Task 8 — `_reconstitute`

In `cli.py`, ~120 lines with its docstring. **Sited there rather than in a new module**: `reference.md`
§ Package layout has no `resume.py` (its "resume resolution" line names `run_identity.py`, which owns
the run-ID and lock surface and reads no step artifact), and a new module would be a § Package layout
change carried by a code task rather than by the documents task. Its only caller is `command_resume`.

**Greps: the shipped parquet reader exists and the brief's name for it is wrong.** The brief says
*"`artifacts` has a `_READERS` table"*; the shipped name is **`READERS`** (public, no underscore), with
`".parquet": _decode_parquet`. `grep -n "_READERS" src/publishable/*.py` → **0 hits**. I use
`READERS[".parquet"]` and `READERS[".jsonl"]`, so both tables read back what `io.write` wrote.
`runner.step_dir_for` is used for the step directory; no second path construction exists.

Refusals: `E-RESUME-ROWS-MISSING`, `E-RESUME-ROWS-UNREADABLE` (two faults, distinguishable by message:
will-not-decode, and columns not covering the record's `recorded_columns`), and
`E-RESUME-LEDGER-UNREADABLE` for a completed line predating H9b's two keys.

**OWED, for task 16/17: `E-RESUME-LEDGER-UNREADABLE`'s § Errors row will be NARROWER than its code.**
Decision 17's row reads *"a line of `executions.jsonl` is not a JSON object, or lacks
`step`/`scope`/`condition`/`repeat`/`status`"*. I raise it for a **third** fault — a `completed` line
with no `returned` or `recorded_columns` — because the alternative is a `per_repeat` hole and a unit
table narrowed to `unit` alone, which is the silent-wrong-numbers shape Decision 4 exists to prevent.
The row must cover all three, or the code needs splitting. **A row narrower than its code is exactly
what H9a's gate found**, which is why this is filed rather than left to a reviewer.

#### Task 8's owed replacement for the mutation measured unreachable

The prescribed mutation — narrow by subtracting declared attribute NAMES instead of by
`recorded_columns` — rests on a recorded key colliding with an attribute name, which the controller
amendment measured unreachable (`io.record` raises `E-STEP-KEY-COLLISION` first; eight failed
executions on batch 1's capture). **I did not implement it and do not report it as run.** The
replacement is in two parts.

**(a) The statement the amendment asks for: no config separates the two readings, and here is why.**
`units.parquet`'s columns are `unit ⊎ attributes ⊎ recorded`, and the three sets are **disjoint for
every config**: `artifacts.record` refuses `"unit"` and `"measurement"` outright and refuses
`self._declared_attributes() & values.keys()` as `E-STEP-KEY-COLLISION`, on **both** the plain and the
`measurement=` path (read, `artifacts.py`, the two guard blocks). So `columns − attributes − {"unit"} ≡
recorded_columns` **identically**, and the by-name rule and the structural rule return the same rows for
every config that can run. Two sharpenings worth carrying rather than smoothing over:

* `_declared_attributes()` reads **`self._units[0].attributes` only** — the FIRST unit. A roster whose
  first unit lacked an attribute a later unit carried would slip a collision past `record`, because
  `finalize` collects attribute names across **all** units. Not reachable from a config (attributes are
  a roster table's columns, so every unit has the same keys), and reachable from a direct `StepIO`
  construction, which `Unit` being on § The importable surface makes legal.
* So the case where the structural rule wins over the by-name rule **exists** and is reachable only
  from core's own API, never from a config. That is the honest form of "no config separates them".

**(b) A discrimination that IS reachable, built and mutated.** The narrowing has a second reading the
brief did not name: **which key ORDER a reconstituted row carries.** `recorded_columns` is *sorted*;
`io.rows()` and `units.parquet` are *first-seen*. A narrowing that iterated the sorted list would move
`run.yaml`'s column order with every value correct — the exact failure arm A's docstring names, and one
arm A cannot yet see. So the fixture records `zeta` before `alpha` (sorted order is the reverse of
insertion order), and the mutation that iterates `recorded_columns` **fails** it (mutation 8.2 below).

### Task 9 — the wiring, and `command_resume`

Phase-6 sites only: the run directory, the seven run-start artifact writes (gated, `identity.json`
included), the plan filter, `planned=len(full_plan)`, the prepended prior results, the recorded
manifest, and `attempts` into `assemble_run_yaml`. `sweep.yaml`'s and `allocation.json`'s **writes** are
skipped while the order realization and the allocation hash still compute, each with the later task
(10, 11) named at the seam. The 36-field unpack block is untouched.

**`command_resume` deviates from the brief's stated ORDER in one place, deliberately.** The brief lists
the hash comparison *before* `_prepare_run`. Computing the three hashes there would be a **second
derivation** of figures `Prepared` already holds — the *second answer to one question* fault. Design
Decision 7's actual requirement is that the comparison refuse *before the lock is taken and before
anything executes*, and it does: phases 1-5 allocate nothing, take no lock and execute no step. The
visible cost is that a hash mismatch prints `validate`'s findings first, which is the order `run` prints
them in anyway.

**FINDING, and it changed the code: `resumed.attempts` alone is stale by one.** The count read at
re-entry does not include the line **this** attempt writes for a re-executed triple, so a triple whose
ledger held 2 records was recorded as `attempts: 1`. Measured — the fixture failed on exactly that.
`_execute_prepared` now adds one per execution **this** attempt ran, before prepending the prior
results, on the invariant that `execute_plan` appends exactly one line per `ExecutionResult` in the same
loop iteration, unconditionally, including the iteration a `max_failed_fraction` `break` ends (the write
precedes the `break`). The field is read rather than left unread, and no second reader of the ledger
appears.

---

## Both design fixtures whose claims the code falsifies

**Fixture C's `attempts: 2` for "the crashed triple" is FALSE of this build.** `execute_plan` writes the
ledger line **after** the execution returns, so a triple killed mid-execution by `os._exit` leaves **no
record at all** and its resumed attempt is its FIRST. Measured: after a crash-and-resume round trip of
the arm-A fixture, every one of the sixteen triples ends at `attempts: 1`, and the crashed ledger holds
exactly 2 lines before the resume and 16 after. Pinned as
`test_h9b_an_interrupted_triple_gets_one_record_not_two`.

A genuine `2` needs a triple whose earlier attempt **reached the write** — i.e. one that failed and was
contained. `test_h9b_a_contained_failure_then_a_resume_records_two_attempts` builds it (a step that
raises on one attempt and succeeds on the next, plus a later `os._exit`), and one thing was measured on
the way: **the shipped `max_failed_fraction: 0.2` stops such a run**, because a contained failure fails
every unit of that execution — which writes `run.yaml` and makes the directory `E-RESUME-RUN-ENDED`
rather than resumable. The fixture sets `max_failed_fraction: 1.0` and says so at the line.

**Fixture D — "a `resume` whose status is `partial` BECAUSE OF the previous attempt" — is not
buildable as described, for the same reason.** Only a `completed` record is reconstituted (Decision 4's
own table), so a previous attempt's failure is **not** in `results`: its triple is re-executed, and if
the retry succeeds the status is `completed`. Measured on the fixture above. A resumed run is `partial`
because of **this** invocation's failure, never a prior one. Whoever owns fixture D should argue against
this rather than rediscover it.

---

## Two things measured after the five commits, at the reviewer's prompting

**The `order: randomized` arm passes, and the reason matters more than the pass.**
`_h9b_round_trip_project` declares `as_declared`, so arm A cannot see the shape where
`_apply_execution_order` reorders the plan **inside** `_execute_prepared` while `command_resume` calls
`_reconstitute(prepared.plan, …)` **before** that — reconstituted results in declared order, executed
results in shuffled order. Built and run
(`test_h9b_a_randomized_order_round_trip_also_equals_its_straight_through`, resumed versus
straight-through of the same project, same normalization helper): **it passes.**

**But it passes partly for a reason that is itself a finding: `_h9a_run_yaml_leaves` sorts
`(dotted_path, value)` pairs, so MAPPING key order is invisible to it.** List order is visible (indices
are path components); a mapping's is not. So arm A's own docstring hazard — *"a parquet round trip can
move `run.yaml`'s column order with every value correct"* — is **not** detectable by arm A's comparison
wherever that order lives in a mapping. Read, not inferred: the helper's walk emits dotted paths and
its last line is `normalized.sort(key=lambda kv: kv[0])`. **Arm A's editor is NONE and I did not touch
it**; the only assertion in this branch that actually pins row key order is task 8's direct
`list(result.rows[0].keys()) == ["unit", "zeta", "alpha"]`, and mutation 8.2 is what proves it can fail.

**Decision 13 is NOT implemented, and calling it "diagnostics" understated it.** It is a redaction rule:
every refusal `resume` decides must print through one fresh credential-bearing `Collector` and **never
be raised into `main`**, whose `PublishableError` handler prints `{exc}` with no collector in scope.
`command_resume` **raises** `ContractError` for `E-RESUME-RUN-ENDED`, the three hash codes and
`E-RESUME-INPUT-MOVED`, and lets `read_identity`, `config_path_for`, `read_execution_ledger` and
`_reconstitute` raise through it. No live exposure — nothing dispatches `resume` — but **task 16 must
build the containment rather than assume it**, and `command_resume`'s docstring now says so by decision
number.

`latest` is asserted too: a crashed run leaves no pointer (correction 10) and a completed resume writes
one naming the resumed directory.

Final gate after these two additions: **3079 passed, 1 skipped, 4 xfailed.**

---

## Mutations — every count read off a FULL-suite run

| # | Mutation | Full-suite result | Caught by |
|---|---|---|---|
| 5.1 | `"returned": returned` (no `summary_values`) | **15 failed, 48 errors**, 2994 passed | shipped `Estimate` fixtures (the raw object breaks the ledger write, which sits OUTSIDE the per-execution `try`, so the run dies) plus my `returned` equality |
| 5.2 | `recorded_columns` unioned with the declared attribute names (the file's column list) | **1 failed**, 3056 passed | `test_h9b_recorded_columns_is_the_recorded_union_not_the_files_columns` |
| 6.1 | keep `"attempts": 1` when the mapping is given | **1 failed**, 3063 passed | `test_attempts_is_the_given_count_per_triple` |
| 6.2 | `ledger_key` returns `(step, None, None)` — the wrong triple | **1 failed**, 3063 passed | `test_h9b_attempt_counts_counts_records_per_triple` (the neighbour's `1` is what makes it bite) |
| 7.1 | `Resumed` not frozen | **2 failed**, 3064 passed | the frozenness test and the signature test |
| 8.1 | reconstitute without `rows` | **4 failed**, 3067 passed | the reconstitution, scalar-only, refusal and ragged tests |
| 8.2 | narrow by iterating the SORTED `recorded_columns` | **1 failed**, 3070 passed | the row-key-order assertion (§ the owed replacement, part b) |
| 8.3 | a missing `units.parquet` is always fatal | **1 failed**, 3070 passed | `test_h9b_a_scalar_only_triples_missing_table_is_not_a_refusal` |
| 8.4 | return a `list` where a tuple is expected | **1 failed**, 3070 passed — **and `mypy` fails without a `type: ignore`** | `assert isinstance(results, tuple)`; `mypy`: *"Incompatible return value type (got `list[ExecutionResult]`…)"* |
| 9.1 | `planned=len(plan)` — the FILTERED length | **1 failed**, 3077 passed | `test_h9b_run_status_is_handed_the_full_plans_length` |
| 9.2 | drop the prior results | **6 failed**, 3072 passed | the round-trip golden, both `attempts` tests, the units/manifest test, the no-rewrite test, the `planned` test |

Every revert was made by **editing back** (`git checkout --` was never used on a source file), with
`__pycache__` cleared, and verified by **re-running**: the post-revert full suite is `3078 passed, 1
skipped, 4 xfailed` at `d8b8a35`.

**Two mutations are named BLIND, in advance, with what would separate them.**

* **9.1's *status* claim.** The brief says the filtered-length mutation is *"caught by arm A:
  `run_status` returns `completed` for a run that should be `partial`"*. **That is wrong**: `planned`
  feeds **nothing but the bare assert** (read, `run_status`), and on a resume `len(results)` is the full
  plan's length either way, so the mutation changes no status, no record and no exit code anywhere. What
  it costs is the **tripwire**: the assert would stop catching a core defect that truncated a resumed
  plan. So it is caught by a wrapper around `cli.run_status` that records the `planned` it was handed
  (with the wrapper's own call count asserted, since a monkeypatch aimed at a name the code no longer
  calls is silently inert), plus a direct check that the assert still fires on a genuinely short list.
* **9.3, "rebuild the manifest instead of using the recorded one": blind, and structurally so.**
  `command_resume` already refuses `E-RESUME-INPUT-MOVED` when the recorded and recomputed manifests
  disagree, so by the time phase 8 runs the two are equal and no assertion can separate them. The
  config that would separate the readings is one whose **step mutates a file under `input_dir` during
  the run** — then `verify_manifest` against the recorded manifest reports a change and against a fresh
  one reports none. Not built here; **owed to task 12**, which owns the manifest arm.
* 9.4, re-realizing the order, is task 10's fixture (this task changes no ordering code — the
  re-realization is what HEAD already does, now with the write skipped).

---

## Guard-pin arms: what moved, what did not, and one mis-assignment

**Arm C is the only arm edited**, to its advance post-edit key set. Arms A, B, D, E, F, G and H are
untouched.

**FINDING — arm A's `xfail` marker names the wrong task, and I left it in place.** Its reason string
says *"H9b task 9 builds `resume`'s execution"*, and my brief's gate list says a named remover must
convert. **It cannot be converted by task 9**, and the reason is measured rather than argued: the
`xfail` half drives `main(["resume", str(crashed)])`, and `resume` is still in `NOT_BUILT_COMMANDS` —
correction 11 measured all four invocation shapes exiting 2, and **arm E, which flips `("resume", "NOT
BUILT")` to `("resume", "built")`, names plan task 15 as its sole editor**. The arm also needs task 14,
because `_execute_prepared`'s `RunLock` refuses a directory whose crashed holder left a `lock` behind.
Run after task 9 landed: it reports **`XFAIL`, not `XPASS`** (`-rxX`, quoted in the run above). So
**no xfail was converted in this batch, and both remain strict**: arm A's needs tasks 14 **and** 15,
arm G's needs 14. Reported, not edited.

**Because arm A cannot run, this batch's evidence bypasses `main`.** `test_h9b_a_crash_and_resume_
round_trip_equals_the_straight_through_golden` calls `command_resume` directly, against arm A's own
crash fixture, and asserts `_h9b_run_yaml_leaves(...) == _H9B_ARM_A_GOLDEN` — **the same literal arm A
captured in batch 1, before any of this code existed**. It passes. That is the leaf-by-leaf equality
Decision 4 exists for, one route short of arm A's. A green suite with arm A still `xfail`ing is **not**
evidence about this wiring, because `xfail(strict=True)` absorbs every failure reason — which is why
this test exists at all.

---

## The lock residual task 14 inherits

1. **`_execute_prepared`'s `with RunLock(run_dir)` is unchanged and my brief's skip-list does not name
   it, while Ruling W's step 4 also ends by taking `RunLock`.** Both cannot be the claim. I took the
   minimal-diff reading: the acquisition stays where it is, `command_resume` takes no lock, and the code
   says so at the line. **The residual for task 14: the brief's ordering puts all of `_prepare_run`
   between a takeover's `unlink` and that acquisition** — a window holding validate, an import, roster
   resolution and hashing, i.e. user code — where Ruling W's own argument for the token is that *a
   decision taken from the directory's state is stale by the time the claim is made*. Task 14 should
   either hold the token through the acquisition or move the takeover to immediately before it.
2. **A zero-new-results apparatus stop on a resume returns with no `run.yaml`.** The stop path's `if not
   results: return` predates `resumed` and sits **before** the prepend, so a resume whose first
   pre-execution probe stops the run discards the reconstituted prior results and writes no record —
   for a run where a great deal *was* paid for, which is the opposite of that branch's own justification
   (*"with NO results, nothing was paid for"*). Not touched: the stop path is H7d Part B's and outside
   this task's sites. **Owed to task 13** (the baseline) or task 16 (the refusals), whichever reaches it
   first.

## Two more residuals, measured

3. **A reconstituted row is RECTANGULAR where the original was ragged.** `finalize` writes one column
   per recorded key across all rows, filling `None` where a row recorded nothing — so a step whose units
   record different key sets round-trips with `b: None` present where the in-memory row had no `b` at
   all. Not recoverable and not guessable: `io.record(u, {"note": None})` is legal, so dropping
   `None`-valued keys would lose a genuinely recorded value. Pinned as behaviour
   (`test_h9b_a_ragged_recording_step_round_trips_rectangular`) rather than papered over. Whether it
   moves a published number is a question only a leaf-by-leaf ragged round trip can answer — the
   fixtures here are rectangular, so **arm A does not cover it**.
4. **`E-RESUME-LEDGER-UNREADABLE`'s owed row widening** (task 8 above).

## Sweeps and claims about other code

Every claim this report makes about other tests or rows was grepped, and the greps are quoted where
they were run: `Estimate(` in `tests/test_cli.py` (10 hits, attributed), `recorded_columns` in
`tests/` (2 pre-existing hits, both attributed), `executions.jsonl` in `src/publishable/*.py` (8 before,
15 after, every one attributed), `_READERS` in `src/publishable/*.py` (**0 hits** — the brief's name is
wrong and the shipped table is `READERS`), and `run_status(` in `src/publishable/*.py` (one call site,
`_execute_prepared`'s). **This is not a claim of zero disagreements**: this batch found seven — arm C's
editor, arm A's `xfail` task, fixture C's `attempts: 2`, fixture D's unbuildability, mutation 9.1's
stated catcher, the brief's `_READERS`, and arm A's
sorted-leaf normalization being blind to the mapping key order its own docstring names.
