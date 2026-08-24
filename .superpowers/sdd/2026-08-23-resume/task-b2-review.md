# H9b batches 3-4 — tasks 5, 6, 7, 8, 9 — review

**Reviewed 2026-08-23** at `b465a3a`, branch `h9b-resume`, in a worktree of my own.

## 0. The normalization list, committed BEFORE the comparison is run

This section is committed on its own, before any two-sided run, so that its content cannot
be shaped by what the comparison found. Batch 1 established the method and this repeats it.

**The batch changes a shipped artifact for the second time in one slice** (`executions.jsonl`
gains `recorded_columns` and `returned`), so the evidence is a real `run` on a `main` worktree
against a real `run` on this branch, not a green suite.

**Two sides.** A `git worktree` at `main` with its own `uv sync` venv, and this branch's
worktree. A positive control first: each side's `publishable.__file__` must resolve inside
its own worktree, or it is one build run twice.

**One project per side**, scaffolded and executed only through the console script
(`publishable new`, `generate experiment`, `run`, `dry-run`), **outside this repository**.
`index.csv` is copied with `cp -p` **before** both runs, so `st_mtime_ns` cannot move the
input manifest — batch 1 measured that as the one path-independent input that can.

**Normalizing exactly these, and nothing else:**

- any key or line component named `at`, `started_at`, `wall_seconds`;
- `run_id` and everything derived from it (the run directory's own name);
- absolute paths, on either side, including each side's own project directory and worktree;
- `hostname`;
- `code_hash`, `parameters_hash`, `uv_lock_hash` and `input_manifest_hash`, and the run
  directory name's 7-hex `code_hash` prefix — two worktrees are two `src/` trees;
- `attempts`.

**What is compared, and the bar for each.**

| Comparison | The bar |
|---|---|
| Run-directory tree, path by path | Differences must be **added paths only**, each attributed to a named task |
| `run.yaml`, leaf by leaf in order, after normalization | **Zero differing leaves**, and identical leaf order |
| Every shared path's size and sha256 | Every difference on the list above |
| `executions.jsonl`, **key by key, line by line** | Differences must be **added keys only**: `recorded_columns` and `returned`, in that position, on every line. Any removed key, reordered key, or changed value outside the list is a finding |
| `sweep.yaml`, `manifest/input.json` | Byte-identical |
| `run` stdout / stderr / exit | Identical after path normalization |

**`main` vs HEAD conflates batch 2's `identity.json`**, which is already reviewed and PASSed;
that one added path is attributed to batch 2 rather than counted against this one. The
isolation of batches 3-4's own artifact change is `git diff 635b3a9..b465a3a -- src/`, read
for every write site.

---

## 1. Verdicts

| Task | Verdict |
|---|---|
| 5 — the ledger's two new keys | **PASS**, with Major 1 |
| 6 — `attempts` from the ledger, the first ledger reader | **PASS** |
| 7 — `Resumed` | **PASS** |
| 8 — `_reconstitute` | **PASS**, with Major 2 |
| 9 — the wiring and `command_resume` | **PASS**, with Major 3 |

**Gates, at `b465a3a`, run by me:** `ruff check` clean · `ruff format --check` 93 files already
formatted · `mypy` clean over 52 source files · `uv run pytest` **3079 passed, 1 skipped, 4 xfailed**
in 233s, run directly in the foreground. **+26 reconciles**: `git diff 635b3a9..b465a3a -- tests/`
adds exactly 26 `def test_` lines and deletes none (3053 + 26 = 3079).

**Both strict xfails report `XFAIL`, not `XPASS`** (`-rxX`, quoted from my own run): arm A names
tasks 14 and 15, arm G names task 14. No xfail was converted in this batch, which matches the report.

---

## 2. The two-sided real-command comparison — the ledger change IS fully attributed

Two worktrees, two `uv sync` venvs. **Positive control:** the `main` side's
`publishable.__file__` resolves at `…/scratchpad/wt-main/src/publishable/__init__.py` and the branch
side's at `/Users/joon/src/tries/publishable/src/publishable/__init__.py` — two builds, not one build
run twice. One project per side, scaffolded and executed only through the console script
(`publishable new`, `generate experiment`, `validate`, `run`), outside this repository, identical
apart from each side's own absolute paths (verified: `diff` of the two configs modulo the side name is
empty, and `git ls-tree -r HEAD` gives the identical file list). `index.csv` `cp -p`'d before both
runs (both `st_mtime_ns` = 1787527474). 2 conditions × 2 seed repeats over 6 units, one attribute
(`site`), and a step recording `zeta` then `alpha` so that **sorted order is the reverse of insertion
order**. Exit `0` both sides.

| Comparison | Result |
|---|---|
| Run-directory tree, path by path | **`identity.json` on the branch side only.** Nothing else added, removed or moved — attributed to **batch 2**, already reviewed and PASSed |
| `run.yaml`, leaf by leaf | **151 leaves each, key order identical, ONE differing leaf**: `provenance.git.commit`. Attributed below |
| Shared paths' sha256 | 4 differ: `config.yaml` (2868 vs 2872 bytes — the side name inside the embedded paths), `environment/repo_root.txt`, `executions.jsonl`, `run.yaml`. **`manifest/input.json` and `sweep.yaml` byte-identical** |
| `executions.jsonl`, key by key, line by line | 4 lines each. **`added=['recorded_columns','returned']` on every line, `removed=[]`, and the pre-existing eight keys in unchanged order.** No value outside `started_at`/`wall_seconds` differs on any line |
| `run` stdout / stderr / exit | stdout identical after path and run-ID normalization; **stderr empty (0 bytes) on both**; exit `0` both |

**Every difference in the ledger is an added key**, in position, with `recorded_columns` =
`['alpha', 'zeta']` (sorted, the reverse of insertion order, as specified) and `returned` =
`{'n_units': 6}`. **The artifact change is fully attributed.**

**The one `run.yaml` leaf, attributed by measurement rather than by argument.**
`provenance.git.commit` is each side's **own project repo's** HEAD, and the two project trees differ
(`a3639bfe…` vs `52b52b57…`) because `configs/cmp-pilot/config.yaml` embeds each side's own absolute
`input_dir`/`output_dir` — same file list, configs identical modulo the side name. Nothing about the
branch. Not on my pre-committed list, so it is named here rather than waved through; it is the same
class as batch 1's `input_manifest_hash` attribution.

**Isolation of batches 3-4's own artifact change**, since `main` vs HEAD conflates batch 2's file:
`git diff 635b3a9..b465a3a -- src/` has exactly one artifact-**writing** change, `execute_plan`'s
single ledger `json.dumps` gaining two keys. Every other change in the range either gates an existing
write behind `if resumed is None` or adds a reader.

---

## 3. Findings

### Major 1 — arm C's assertion MOVED and no mutation in this batch fails it (task 5)

Design § 7: *"Every arm must be proven able to fail before the batch is reviewed, by a mutation in the
production code — not by reading."* Arm C's post-edit set is the one assertion this batch changed, and
the report's arm section offers **no** failability mutation for it. Measured, not read:

- **Mutation 5.2** (`recorded_columns` unioned with the declared attribute names) —
  `uv run pytest tests/test_cli.py -k "recorded_columns or arm_d_the_executions"` →
  `1 failed, 1 passed`: the named test fails and **arm C passes**.
- **Mutation 5.1** (`"returned": returned`) — full suite `15 failed, 3016 passed, 48 errors`. I listed
  all fifteen: thirteen are shipped `Estimate` fixtures, one is
  `test_h9b_returned_is_written_through_summary_values`, one is `test_study.py`'s.
  **Arm C is not among them.**
- **The honest mutation** — delete the `"recorded_columns"` key from `execute_plan`'s ledger dict —
  fails arm C on its own (`1 failed in 1.05s`) and **15 failed, 3064 passed** full-suite.

So the pin is real and the evidence for it was owed and absent. This is batch 1's Major 1 recurring on
the one arm whose assertion moved: *an arm whose assertion moved needs the mutation that fails IT.*

### Major 2 — task 8's owed statement is FALSE, and the fail-open it rests on has no owner (task 8)

The controller amendment asked task 8 to *"state, with the config that would separate the readings,
that none exists."* The report answers: `columns − attributes − {"unit"} ≡ recorded_columns`
identically for every config, and the case where the structural rule wins is *"reachable only from
core's own API, never from a config."* **I built the config, and it runs.**

`resolve_units` (units.py) accumulates `yielded.update(item.attributes)` and checks each declared
attribute against that **union**, so a resolver whose FIRST unit lacks an attribute later units carry
passes `validate`. `StepIO._declared_attributes` (artifacts.py:688-691) reads
`self._units[0].attributes` **only**, so `io.record`'s `E-STEP-KEY-COLLISION` never fires. Measured,
through a real run of a real installed resolver distribution:

```
  recorded_columns: [['cohort']]
  file columns: ['unit', 'cohort']
  row p1: {'unit': 'p1', 'cohort': 0.0}
  by-name keeps: []   structural keeps: ['cohort']
```

Three consequences, in order of cost:

1. **`E-STEP-KEY-COLLISION` fails open from a config**, and a recorded value silently occupies a
   declared attribute's column — the *reserved-name-versus-structural-fact* fault, live, in
   `artifacts.py`, **unfiled and unowned**. Batch 1 measured the collision as *"eight failed
   executions"* on a **table** roster; that is the positive control, and it does not hold for the
   resolver source.
2. **The prescribed by-name mutation was therefore NOT blind** for a resolver-sourced roster, so the
   amendment's own premise is wrong too — the fixture the amendment said could not exist is the one
   above.
3. The report's ground — *"attributes are a roster table's columns, so every unit has the same keys"*
   — is true of `_from_table` and false of `resolve_units`. **Sweep for the claim, not for the source
   the claim was first noticed in.**

**Nothing wrong ships from H9b**: `_reconstitute` narrows structurally, which is the reading that
survives this case. What is wrong is the reachability claim, and what is unowned is the fail-open.

### Major 3 — two of the five OWED items live only in `task-b2-report.md` (task 9)

Batch 1's Major 2 was *three escalations that lived only in a report*. Adjudicated against one bar —
does the item exist in a live task section, a dispatched brief, or `spec-defects.md`?

| Owed item | Routed? |
|---|---|
| `E-RESUME-LEDGER-UNREADABLE`'s § Errors row narrower than its code | **NO.** Design Decision 17's row reads *"…is not a JSON object, or lacks `step`/`scope`/`condition`/`repeat`/`status`"* — grepped, one hit, and it does not cover the third fault the code raises. Neither plan task 16 nor task 17 mentions widening it |
| Decision 13's `Collector` containment not built | **YES** — plan task 16's own section already requires building it (*"copy where it sits, not only what it calls"*), and `command_resume`'s docstring now names it by decision number |
| Zero-new-results apparatus stop on a resume | **NO**, and it is owed to *"task 13 … or task 16 …, whichever reaches it first"* — the *"whichever slice does X"* anti-pattern `CLAUDE.md` names |
| Arm A's sorted-leaf normalization blind to mapping key order | **Partly** — stated in the report and in the new test's own docstring, nowhere else. Arm A's editor is NONE, so it cannot be closed by a code task; it needs a filing |
| The ragged rectangular round trip | **Pinned as behaviour**, and **now answered** — see § 4 |

### Minor 1 — the apparatus-stop residual is NOT a record loss, and the report's wording reads as one

The report: *"a resume whose first pre-execution probe stops the run discards the reconstituted prior
results and writes no record — for a run where a great deal was paid for."* Reproduced by injecting
the stop at `execute_plan` (the one function that sets `stop.reason`; the same zero-results/
`apparatus_unreachable` state `test_fixture_z_arm_3_zero_results_unreachable_case` already produces
through a real probe on a plain `run`):

```
  exit: 5      run.yaml written: False
  ledger lines before/after: 2 2      step dirs still present: 2
  second resume exit: 0   run.yaml now: True
```

**Nothing is lost.** The ledger and every step artifact are untouched and the directory is still
resumable — a second `resume` completes at exit `0` and writes `run.yaml`. What is wrong is the
branch's own justification (*"with NO results, nothing was paid for"*), which is false on a resume,
plus one wasted retry. Worth carrying into the filing: for `apparatus_changed` the loss **would** be
real once task 13 replays the baseline, because the run could never complete again — so the filing
should name the two stop reasons separately rather than as one row.

### Minor 2 — mutation 5.1's reported passed-count does not reconcile

Report: *"15 failed, 48 errors, 2994 passed"* — which with 1 skipped and 4 xfailed sums to 3062 items
against a tree of 3083 (3078 + 1 + 4). Mine: **15 failed, 48 errors, 3016 passed**, summing to 3084 =
3079 + 1 + 4, exactly. The `failed` and `errors` figures reproduce; the `passed` figure is understated
by about 21.

### Minor 3 — `command_resume`'s docstring overclaims what a refusal costs

*"everything below happens before `_execute_prepared` is reached, so a refusal costs nothing and
touches no artifact."* The artifact half is true and I verified it by behaviour (below). The
"costs nothing" half is false in the case that matters: `_prepare_run` runs `validate` **and roster
resolution**, i.e. a resolver's user code, which can hit a metered API — the report's own lock
residual 1 says exactly this. The verifiable claim is *no step executes, no lock is taken, no artifact
is written.* Habit: *a comment claiming a guarantee the code does not provide.*

### Minor 4 — arm C's editor: brief and design still disagree, and only the docstring reconciles them

The design's appended § Correction from batch 1 declares arm C's *"(plan task 6)"* parenthetical
**correct** while fixing arms B and D's; the dispatched task 5 brief opens *"You are the SOLE
AUTHORIZED EDITOR of guard-pin arm C"*; task 5 edited it. Tasks 5 and 6 are one batch, the edit is
exactly the two-key addition specified in advance (verified: the diff is `+"returned"`,
`+"recorded_columns"` inside the set literal and twelve docstring lines, nothing removed, nothing
reordered), and the docstring states the discrepancy rather than resolving it — the third option, and
the right one. Recorded so the design and the briefs are reconciled once by the controller rather
than re-litigated by task 15's editor of arm E.

### Minor 5 — the mutation table's counts are per-commit and do not say so

Re-run at HEAD, the same mutations bite harder: **6.1** fails 2 (`test_attempts_is_the_given_count_per_triple`
**and** `test_h9b_a_contained_failure_then_a_resume_records_two_attempts`), not 1; **8.1** fails 7
full-suite (`7 failed, 3072 passed`), not 4; **8.3** fails 2, not 1. Each report figure is right for
the commit it was measured at — task 9's tests did not exist yet — but the table does not say so, and
a later reader re-running a pin will get a different number and not know which is wrong.

### Minor 6 — `resumed.baseline` is written and read nowhere, and the report's site list omits it

`grep -n "\.baseline" src/publishable/cli.py` → **0 hits**. Correctly deferred: plan task 13's own
section owns *"thread the replayed `Observations` into the `Observer` `_execute_prepared` builds"*, so
this is a seam and not a drop. But the task 9 brief lists *"`resumed.baseline` into the `Observer`"*
among its phase-6 sites, and the report's task 9 enumeration omits the field entirely — the only trace
is `command_resume`'s docstring. Named here so task 13 inherits it stated rather than discovered.

---

## 4. What I verified, and by what

### The ragged round trip — the question the report says nobody has answered, answered

Report residual 3: a reconstituted row is rectangular where the original was ragged, and *"whether it
moves a published number is a question only a leaf-by-leaf ragged round trip can answer — the fixtures
here are rectangular, so arm A does not cover it."* Built it: a repeat step recording `{pred, extra}`
on odd units and `{pred}` on even ones, over 20 units × 2 conditions × 4 seeds, run straight through
and then crashed-and-resumed, compared through **the same `_h9b_run_yaml_leaves` helper**.

```
straight leaves: 171   resumed leaves: 171
  DIFF: (none)   only straight: []   only resumed: []
  extra.n.completed = 10 on BOTH sides
  extra.ci95 = [5.668298820663662, 14.331701179336338] on BOTH sides
```

**No published number moves.** A `None`-filled cell is excluded from `n` and from the interval, so the
raggedness residual is cosmetic. The probe is non-vacuous by construction: it asserts an `extra` leaf
exists, and `n.completed` is 10 against 20 resolved units, which is the raggedness itself showing up
in the record. **Residual 3 can be closed with this measurement rather than carried as an open
question.**

### The bypass, and its substitute (check 6)

The bypass is honest: arm A's resume half drives `main(["resume", …])`, `resume` is in
`NOT_BUILT_COMMANDS` (grepped, `cli.py:180`), and arm E — which flips it — names **plan task 15** as
its sole authorized editor (grepped, `tests/test_cli.py:9592`). So no task in this batch could convert
it.

The substitute is equivalent, and I verified the equality myself rather than trusting it:

- `_H9B_ARM_A_GOLDEN` is **byte-identical at `811feee` (batch 1), `635b3a9` and `b465a3a`** —
  sha256 prefix `9702b322e7f0fa1b`, 188 lines, all three. The literal was captured before any of this
  code existed and was not retro-edited.
- **Both normalizers are byte-identical across the same range** — `_h9b_run_yaml_leaves`
  (`0d4538b3dc0f1608`) and the `_h9a_run_yaml_leaves` it delegates to (`dbdf425d462e314a`). The
  comparison was not loosened to make the equality pass.
- The equality is **non-vacuous**: `test_h9b_a_crash_and_resume_round_trip_equals_the_straight_through_golden`
  fails under mutation 9.2 (drop the prior results), under 8.1 (reconstitute without rows) and under
  my arm-C mutation.
- One caveat, which the report itself discloses and I confirmed by reading: `_h9a_run_yaml_leaves`
  ends `normalized.sort(key=lambda kv: kv[0])`, so **mapping key order is invisible to this
  equality** — which is why mutation 8.2 is caught by a direct row-key-order assertion
  (`tests/test_cli.py:23552`, `list(result.rows[0].keys()) == ["unit","zeta","alpha"]`) and by
  nothing else.

### The stale-by-one defect (check 2)

There is **no pre-fix commit** — the fix landed inside `d8b8a35` with the wiring — so I reproduced it
by removing the loop's `+ 1`:

```
tests/test_cli.py:23922: assert recorded[failed_key] == 2
E       assert 1 == 2
```

The ledger holds 2 records for that triple and `run.yaml` recorded `attempts: 1` — exactly the defect
described. **Pinned by two tests, full-suite**: `2 failed, 3077 passed, 1 skipped, 4 xfailed`
(`test_h9b_a_contained_failure_then_a_resume_records_two_attempts` and
`test_h9b_an_interrupted_triple_gets_one_record_not_two`, the latter because a re-executed triple with
no prior record then records `0`).

### Both falsified design fixtures (check 3)

Built both. After a crash of the arm-A fixture the ledger holds **2 lines** and their triples are
`(step01, 0, seed08)` and `(step01, 0, seed76)` — the interrupted triple has **no record at all**,
because `execute_plan` writes the line after the execution returns. After the resume:
`max ledger attempts: 1`, `max recorded attempts: 1`, `triples with 2+: []`. **Fixture C's
`attempts: 2` for a crashed triple is impossible**, and a genuine 2 needs a contained failure —
which is what the replacement fixture builds, with `max_failed_fraction: 1.0` stated at the line
because the shipped `0.2` otherwise ends the run.

**Fixture D is unbuildable as described**: `_reconstitute` admits only `entry.get("status") ==
"completed"` (read), so a prior attempt's failure is not in `results` — its triple re-executes, and
the resumed run I built reports `status: completed`. A resumed run is `partial` because of **this**
invocation.

### Task 8's declined mutation (check 4)

The report does **not** implement the prescribed by-name mutation and does **not** report it as run —
confirmed against the diff (`_reconstitute` narrows by `keep = {"unit", *columns}`) and against the
mutation table (8.1-8.4, no by-name arm). The replacement discriminates: **mutation 8.2** (iterate the
sorted `recorded_columns` instead of filtering the row's own items) → full suite **1 failed, 3078
passed**, caught by the row-key-order assertion and by nothing else, and its two branches genuinely
differ because the fixture records `zeta` before `alpha`. The *statement* half of the replacement is
where Major 2 lands.

### `run_status`'s bare assert (check 5)

**Designed around, not changed, and the answer is stated rather than accidental.** `run_record.py` is
untouched in `run_status`'s body and docstring (the task 6 diff touches `_execution_block` and
`assemble_run_yaml` only), `planned=len(full_plan)` is bound **before** the filter, and the prior
results are prepended before the call. **Made it fire**, directly:

```
ASSERT FIRES: execute_plan returned 0 results against a plan of 1, with no stop reason recorded — core t…
max_failed_fraction suppresses: failed
```

And the pin is sound rather than nominal: the wrapper test asserts `len(seen) == 1` (so a patch aimed
at a name the code no longer calls cannot pass vacuously), asserts `planned == 16` and
`results_len == 16`, and re-fires the assert on a genuinely short list. Mutation 9.1
(`planned=len(plan)`) → full suite **1 failed, 3078 passed**, and the report's claim that the
mutation is blind to every *status* assertion is right: I read `run_status` and `planned` feeds nothing
but the assert.

### The deliberate deviation (check 8)

Verified **by running**, not by reading the docstring. A crashed directory with `identity.json`'s
`code_hash` rewritten, the counter file armed so any execution would tick it:

```
  code: E-RESUME-CODE-MOVED
  lock present: False          counter after: 0
  ledger unchanged: True       tree unchanged: True      added: []
```

No lock, no execution, no artifact — the comparison sitting after `_prepare_run` costs nothing on
disk. `validate`'s findings do print first, which the docstring discloses. See Minor 3 for the one
half of the docstring's claim that does not hold.

### Guard-pin arms (check 9)

`git diff d4e0afd~1..b465a3a -- tests/` has **928 insertions and zero deletions**, so no assertion
anywhere in the suite was removed or altered except arm C's set literal gaining two members — which
is the authorized edit, matching the advance spec exactly. Arms A, B, D, E, F, G, H untouched. Arm C
provably failable (Major 1 supplies the mutation the batch owed). H7d Part B's `max_failed_fraction`
pin untouched.

### Must-not-touch (check 12)

Diffed each brief against what shipped. **No undisclosed drop.** Specifically verified:
`git diff d4e0afd~1..b465a3a -- src/publishable/cli.py | grep '= prepared\.'` → **no hits**, so the
36-field unpack block is unchanged (correction 19); `_resolved_group_axes`/`arm_members` appear in no
diff line, so Ruling S holds; `src/publishable/provenance.py` untouched; `run_status`, `stats.py` and
`runner.attrition` untouched; no `*.md` in any of the five task commits. Every deferral (`sweep.yaml`'s
order → task 10, `allocation.json` → 11, the manifest arm → 12, the baseline → 13, the lock → 14, the
dispatch → 15, the refusals' containment → 16) names its task at the seam.

### Claims about other tests, rows and code (check 11)

Grepped every one. All correct: `_READERS` → **0 hits**, the shipped table is `READERS`
(`artifacts.py:217`) — the brief was wrong and the report right; `run_status(` → one call site;
`_declared_attributes` reads `self._units[0].attributes` only; `artifacts.record`'s collision guard
exists on **both** paths (lines 754 and 799); `_finalize_columns` is documented and implemented
first-seen order; § Package layout has no `resume.py` and its `run_identity.py` line does carry
*"resume resolution"*; Decision 17's `E-RESUME-LEDGER-UNREADABLE` row is narrower than the code;
`ineligible.jsonl` lines are `{"unit": …, "reason": …}`, which is what the reader reads. The one claim
that does **not** survive is task 8's reachability statement — Major 2, and it is a claim about
`resolve_units` and `_declared_attributes`, i.e. about other code, which is where this repository's
zero-disagreement failures have always hidden.

### The mutation table, re-run

| # | Full-suite at HEAD | Targeted | Verdict |
|---|---|---|---|
| 5.1 | **15 failed, 3016 passed, 48 errors** | all 15 listed and attributed | reproduces; passed-count differs (Minor 2) |
| 5.2 | — | `1 failed, 1 passed` (arm C green) | reproduces |
| 6.1 | — | 2 failed at HEAD (1 at task 6's commit) | reproduces (Minor 5) |
| 6.2 | — | `1 failed` in lineage/run_record, 12 in `-k h9b` at HEAD | reproduces |
| 7.1 | — | `2 failed` | reproduces exactly |
| 8.1 | **7 failed, 3072 passed** | — | reproduces (Minor 5) |
| 8.2 | **1 failed, 3078 passed** | — | reproduces exactly |
| 8.3 | — | 2 failed at HEAD | reproduces (Minor 5) |
| 8.4 | — | `1 failed` **and** `mypy` errors at `cli.py:2298` | reproduces exactly, both halves |
| 9.1 | **1 failed, 3078 passed** | — | reproduces exactly; blindness claim confirmed by reading `run_status` |
| 9.2 | **7 failed, 3072 passed** | — | reproduces (Minor 5) |
| mine — drop `"recorded_columns"` | **15 failed, 3064 passed** | arm C alone: `1 failed` | **Major 1** |
| mine — drop the `attempts` `+ 1` | **2 failed, 3077 passed** | — | **check 2 reproduced** |

Both mutations the report names blind are blind for the reasons it gives: 9.1's *status* claim (read:
`planned` feeds only the assert), and 9.3's manifest rebuild (`command_resume` refuses
`E-RESUME-INPUT-MOVED` before phase 8, so the two manifests are equal by then — the separating config
is one whose step mutates a file under `input_dir` mid-run, correctly owed to task 12).

**Every mutation was reverted by editing back** — `git checkout --` was used on no source file —
`__pycache__` cleared each time, and the reverts verified by **behaviour**: `git status --short src/`
empty, all four touched modules byte-identical to their pre-mutation copies, and a final full
unfiltered run of **3079 passed, 1 skipped, 4 xfailed** with both H9b xfails reporting `XFAIL`.

---

## 5. What is verified by behaviour versus by reading

**By behaviour** (a command, a run, or a mutation): the two-sided real-command comparison in full
(tree, `run.yaml`'s 151 leaves, every shared hash, the ledger key by key, both streams, both exits);
the ledger change being additive on every line; the stale-by-one defect and its two pins; both
falsified design fixtures; the ragged leaf-by-leaf round trip and its identical `n` and interval; the
zero-new-results apparatus stop and the second resume that completes after it; the hash refusal taking
no lock, executing nothing and writing nothing; the config-reachable by-name/structural discrimination
through a real installed resolver; arm C failing under the honest mutation and passing under 5.2;
`run_status`'s assert firing; all eleven reported mutations; every gate.

**By reading** (stated as such): that `planned` feeds nothing but the assert; that only `completed`
records are reconstituted; that Decision 17's § Errors row is narrower than the code; that plan task
13 owns the `Observer` threading and plan task 16 owns Decision 13's containment; that the 36-field
unpack block and the arm-plan call order are untouched (via the diff); that `_prepare_run` runs a
resolver before the hash comparison.

**Not verified either way, and named:** the lock, the takeover and the five-process race — task 14's,
and the report is right not to have raced a scratchpad reimplementation.
