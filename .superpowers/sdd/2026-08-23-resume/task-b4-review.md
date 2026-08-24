# H9b — review of tasks 10–18 (batches 5–8)

Reviewer's own run, `h9b-resume` at `6ddd882`, worktree clean at start and at finish.
**Suite at HEAD: 3132 passed, 1 skipped, 2 xfailed** (259s). **`main` at `f2e545d`: 3019 passed,
1 skipped, 2 xfailed.** Gates clean: `ruff check` (All checks passed), `ruff format --check`
(93 files already formatted), `mypy` (52 source files, no issues).

**What follows is labelled by how it was established.** Every mutation was applied by editing,
reverted by editing back, and every revert verified by **re-running** — the closing full suite
returned exactly the baseline triple. Where a mutation count is a **blindness** claim it was read off
a **FULL unfiltered** run; where it is an **attribution** claim it was read off a `-k`-scoped run and
is labelled `(scoped)`.

---

## Verdicts

| Task | Verdict |
|---|---|
| 10 — `sweep.yaml`'s recorded plan | **PASS** |
| 11 — `allocation.json` read rather than re-drawn | **PASS** |
| 12 — the input manifest compared not rebuilt | **PASS** |
| 13 — the apparatus baseline replayed | **PASS** |
| 14 — the lock takeover | **PASS** — with Minor 1 (the `RunLock` message the document narrowed and the code did not) |
| 15 — `resume` dispatched | **PASS** — with Minor 2 (two stale test comments the dispatch falsified) |
| 16 — the fourteen refusals, and the record loss closed | **PASS WITH FINDINGS** — Major 1 (`E-RESUME-LEDGER-UNREADABLE`'s row is narrower than its code, and it is the amendment item this task was told to close) and Major 2 (`command_resume`'s docstring asserts four things this task falsified) |
| 17 — the documents | **PASS WITH FINDINGS** — Major 4 (the code count carried into a dated build claim) |
| 18 — both consistency passes | **PASS WITH FINDINGS** — Major 3 (`freeze._assert_refused`'s fail-open reported in Concerns and filed nowhere) and Major 4's other half |

---

## 1. The race, re-run against the shipped code

Harness in the scratchpad (`race/contend.py`, `race/race.py`), run with the repo's interpreter from
outside the repository, five contending processes per trial released from a common wall-clock deadline,
each trial a fresh temp run directory whose `lock` names a **real reaped pid on this host**. A trial
fails when **two hold-intervals overlap**. In `shipped` mode the stagger is placed exactly where the
siting decision puts the residual window: between `take_over_dead_lock` **returning** and
`RunLock.__enter__`.

| Mode | Trials × procs | Stagger | Violations | Max concurrent holders |
|---|---|---|---|---|
| detector self-test (no exclusion at all) | 60 × 5 | — | **60 of 60** | 5 |
| negative control — step 1 (the token) deleted | 60 × 5 | none | **0 of 60** | 1 |
| negative control — step 1 deleted | 60 × 5 | 20 ms | **60 of 60** | 5 |
| **shipped** | 60 × 5 | none | **0 of 60** | 1 |
| **shipped** | 60 × 5 | 20 ms | **0 of 60** | 1 |
| **shipped** | **120 × 5** | 20 ms | **0 of 60** → **0 of 120** | 1 |

**All three of the report's rows reproduce, and its criterion finding reproduces with it.** The
token-less control at 0/60 **without** a stagger is the finding restated in my own harness: all five
processes read the lock at once, all five unlink before any creates, and `RunLock`'s own exclusive
create still admits one — *a control that cannot fail is not a control*. My control is stronger than
the report's 36/60 because my stagger is longer (20 ms against theirs); the direction and the
conclusion are identical. **The detector fires 60/60 before any zero above is trusted.**

The winner-count criterion argument is verified by construction rather than by rebuilding the
report's first harness: a winner releases the lock in `RunLock.__exit__` when its run ends, so a
second `resume` acquiring afterwards is the command working, and any criterion counting *winners per
trial* over a time-spread arrival pattern flags the correct protocol. My harness measures overlap and
is the criterion the report settled on.

## 2. The takeover window — enumerated, not accepted

**By reading.** Between `take_over_dead_lock(run_dir)` (cli.py:5061) and
`with RunLock(run_dir)` (cli.py:3048) the following executes, and nothing else: the call to
`_execute_prepared`; its 36-field unpack block (cli.py:2997–3030); `run_dir = resumed.run_dir` and
`manifest = resumed.recorded_manifest`. `Prepared` is a plain dataclass with **no properties and no
`__getattr__`** (checked), so all 38 of those are bare attribute reads. **The load-bearing property
holds exactly as the comment states it**: nothing in the span reads a file, runs user code, or can
block.

**By behaviour.** Row 3 of the table above — a 20 ms stagger placed inside that span, 120 trials × 5
processes, zero overlaps.

**Minor 7**: the comment's *enumeration* ("one function call and phase 6's
`run_dir = resumed.run_dir`") omits the unpack block and the `manifest` assignment. The safety
argument is unaffected; the sentence undercounts what it lists.

## 3. The record loss, closed at exit 4

**By reading, and this is stronger than a probe.** The code is not chosen at the stop site:
`run_record._STOP_REASON_TO_STATUS["apparatus_changed"] → "failed"` is unconditional, and phase 10's
`{"completed": EXIT_OK, "partial": EXIT_PARTIAL}.get(status, EXIT_FAILED)` (cli.py:4745) has **no
branch on `resumed`**. So a mid-plan `E-APPARATUS-CHANGED` on an ordinary `run` and a run-start one on
a `resume` are not two paths that happen to agree — they are the **same two lines**. *"The same answer
H7d Part B gives a mid-plan move"* is true by construction, and neither `1` nor `5` is reachable from
that fold.

**By behaviour.** `test_h9b_a_resume_gates_against_the_original_runs_first_answered_fact` runs a real
crash, moves the fact, resumes, and asserts `code == EXIT_FAILED`, `status: failed`, every
reconstituted entry `completed` and as many as the crash's ledger held, non-empty
`results.conditions`, `provenance.apparatus.ledger`, the first attempt's `r1` in
`provenance.apparatus.facts`, `r2` as the ledger's last line, exactly **one** diagnostic, `latest`
naming the resumed directory, the ledger and step artifacts unchanged, and the second resume refusing
`E-RESUME-RUN-ENDED`. It is the single test the closure rests on, and both mutations kill it:

| Mutation | Result |
|---|---|
| M9 — the record-writing branch `if False and …` | **1 failed**, 3131 passed, 1 skipped, 2 xfailed (**FULL**) |
| M10 — the zero-results early return restored to `if not results:` | **1 failed** (scoped, 59 passed) |

**The unreachable half is filed**, `spec-defects.md` § *OPEN — a resume stopped by an UNREACHABLE
apparatus still writes no record…*, owner *unassigned, with the reason*. The reason is the terminality
of `run.yaml` and it is argued rather than asserted; the owner names why no remaining slice holds the
surface. Verified by reading the entry against the code: `E-APPARATUS-RAISED` still returns
`EXIT_EXTERNAL` before `assemble_run_yaml` (cli.py:3421–3427). **I do not disagree with the
paragraph.**

## 4. Arms A and G — the conversions

**By reading `git diff 04cad73 8963071 -- tests/test_cli.py`.** Neither body changed: the only
removals are the two `@pytest.mark.xfail(strict=True)` decorators and the two docstrings' `xfail`
paragraphs. A strict `xfail` asserts only *this body fails somehow* — and both were passing because
`main` printed the unbuilt diagnostic at exit 2, which says nothing about `resume`. Live, arm A
enforces `main(["resume", …]) == EXIT_OK`, a parseable `run.yaml`, and all 94 normalized leaves
against the batch-1 golden; arm G enforces `sorted(codes) == [EXIT_OK, EXIT_WRONG]`, exactly one
`E-RUN-LOCKED`, a `run.yaml`, and no `lock`/`lock.takeover`. **Strictly more on every count.**

**Failability, by behaviour.** Arm A fails under the `take_over_dead_lock` no-op (below) and under
M5; arm G fails under M1 (the token loses `O_EXCL`), M3, M4 and M5.

## 5. `resume` flipped to `built`

**Through the installed console script, from `/tmp/h9bprobe` outside the repository:**

| Invocation | Exit | First line |
|---|---|---|
| `publishable resume` | 2 | `` `resume` takes exactly one path and no flags`` |
| `publishable resume a b` | 2 | the same line |
| `publishable resume --json` | 2 | the same line |
| `publishable resume new` | **1** | `  error   E-IO-FAILED          new` / `is not a directory, so there is no run to continue …` |

All four match the corrected disclosure, including the identifier task 16 moved. **No other `Status`
cell moved**: `git diff main...HEAD -- docs/reference.md` grepped for `NOT BUILT`/`| built` returns
exactly one changed row, `publishable resume`.

M5 (drop `resume` from `OPERATION_COMMANDS`, keep the handler): **8 failed** (scoped) — the same eight
the report names, and the captured stderr confirms the report's prediction that the arity tests fail
on their **message** half (`unknown command \`resume\`` also exits 2).

M6 (the two-token/`NOT_BUILT_COMMANDS` lookups hoisted above the built branches): **FULL unfiltered
run, 3132 passed, 1 skipped, 2 xfailed — 0 failed.** The report's blindness claim reproduces exactly,
and its derivation is correct: `NOT_BUILT_COMMANDS` holds `demo`, `docs`, `list-templates`,
`reproduce`; none has a built branch, and no key contains a space, so the two-token arm can never
match. See **Minor 4**.

## 6. The four concerns — adjudicated

**Concern 1 (the takeover's siting).** Upheld. The design's literal order would put `_prepare_run` —
a plugin import and a resolver, user code — between the unlink and the claim; the shipped siting
leaves 38 attribute reads and two assignments. I do **not** ask for the refusal to move earlier: a
second liveness read is a second answer to one question, and a refusal after phases 1–5 still touches
no artifact.

**Concern 2 (`_h9b_resume` removes the lock by hand).** Accurate about the twelve tests and
**understated about the coverage.** Adjudicated by the mutation the concern invites — a bare `return`
at the top of `take_over_dead_lock`, **FULL run: 21 failed, 3111 passed**:

- 19 in `tests/test_run_identity.py` — the takeover's direct unit coverage;
- `test_h9b_arm_g_the_takeovers_mutual_exclusion`;
- **`test_h9b_arm_a_crash_and_resume_equals_straight_through`** — which the report's *"the end-to-end
  pin is arm G"* omits. Arm A drives `main(["resume", …])` against a directory holding a real stale
  lock, so **arm A is a second end-to-end pin of the takeover.** Not a defect; the report undersells
  itself.

None of the twelve `_h9b_resume` callers appears in that list, so the concern's substance is exactly
right. Left alone is the correct call.

**Concern 3 (`freeze._assert_refused`).** **Reproduced, and it is worse than reported.** See
**Major 3**.

**Concern 4 (the unreachable half filed).** Upheld — see § 3.

## 7. § Errors — one row per code, every emit site

**By reading, code side first.** Discriminating count, `grep -rn 'code="E-RESUME-' src/publishable/`
plus the three `MOVED` codes raised through a loop variable: **fourteen** `E-RESUME-*` codes with real
raise sites, plus `E-FREEZE-CONFIG-EDITED` (1 site) — **fifteen codes, fifteen rows** at
`docs/reference.md` 649–663, one per code, all in § Errors `validate` reports beside the `E-FREEZE-*`
rows. No warning code is minted anywhere in the branch (`git diff main...HEAD -- src/` grepped for
`W-`: zero). Each table's lead sentence admits its rows, and the two § Errors core raises rows
(`E-RUN-LOCKED`, `E-RUN-ID-EXHAUSTED`) are genuine `ContractError` raises needing no `Type`-cell
qualification.

Row-versus-site, read individually:

| Code | Raise sites | Faults the row names | Verdict |
|---|---|---|---|
| `E-RESUME-NO-IDENTITY` | 4 | 4 | covered |
| `E-RESUME-NO-CONFIG` | 6 (3 in `read_repo_root`, 3 in `config_path_for`) | 6 | covered |
| `E-RESUME-RUN-ENDED` | 1 | 1 | covered |
| `E-RESUME-CODE/PARAMS/LOCKFILE-MOVED` | 1 loop, 3 codes | each | covered |
| `E-RESUME-INPUT-MOVED` | 2 | 2 | covered |
| `E-RESUME-PLAN-MISSING` | 5 | 5 | covered |
| `E-RESUME-PLAN-MISMATCH` | 5 across 2 readers | 4 + the order arm, "two sites, one code" | covered |
| **`E-RESUME-LEDGER-UNREADABLE`** | **4** | **3, and the fourth denied by name** | **Major 1** |
| `E-RESUME-ROWS-UNREADABLE` | 2 | 2 | covered |
| `E-RESUME-ROWS-MISSING` | 1 | 1 | covered |
| `E-RESUME-ALLOCATION-STALE` | 9 fault shapes across 2 modules | 6 phrases | **Minor 5** |
| `E-RESUME-PROBES-UNREADABLE` | 1, delegating to `replay_ledger` | delegated to the `E-FREEZE-LEDGER-UNREADABLE` row, which enumerates four | covered |
| `E-FREEZE-CONFIG-EDITED` | 1 | 1, plus the absent-`identity.json` sentence | covered |
| `E-RUN-LOCKED` | 4 (the lock's claim, the token, the liveness verdict, the report) | all four, plus reachability, the liveness rule, the `started_at` non-use, and the `lock.takeover` residual | covered |
| `E-RUN-ID-EXHAUSTED` | 1 | `run` and `draft` only | covered |

The displaced-antecedent repair from the fix round is correct: the two new rows now sit **above** the
paragraph whose antecedent they were displacing, the `E-RUN-` prefix shorthand is replaced by *"the
last row above"*, and the paragraph's own back-reference names both new codes.

## 8. Mutations — re-run

| # | Claim | My result | Scope |
|---|---|---|---|
| M1 | token loses `O_EXCL` | **2 failed**, 3130 passed, 1 skipped, 2 xfailed | **FULL** |
| M2 | unparseable JSON read as dead | 1 failed — `…[unparseable]` | scoped |
| M3 | liveness consults `started_at` | **3 failed**, 3129 passed — `…no_started_at_and_a_dead_pid_is_taken_over`, `…token_is_released_when_the_liveness_test_raises`, `…two_threads_racing…` | **FULL** |
| M4 | the `finally`'s `token.unlink` deleted | 16 failed | scoped |
| M5 | `resume` out of `OPERATION_COMMANDS` | 8 failed | scoped |
| M6 | the lookups hoisted | **0 failed, 3132 passed** — BLIND, as reported | **FULL** |
| M8 | a refusal raised into `main` | 7 failed, incl. the credential positive control | scoped |
| M9 | the record-writing branch disabled | **1 failed**, 3131 passed | **FULL** |
| M10 | the zero-results return restored | 1 failed — same test | scoped |
| M11 | `freeze`'s `parameters_hash` gate disabled | 1 failed | scoped (`test_freeze.py`, 41 passed) |
| M12 | `check_recorded_order` call removed | 1 failed | scoped |
| M13 | the not-a-directory gate disabled | 2 failed | scoped |
| M9 (batch 3) | `baseline=None` | 2 failed, the same two names | scoped |

**Every count and every named test matches the reports.** Each mutation was checked against the body
of the test it names: M3's named test is the structural replacement for the mutation declared blind in
advance (a lock with **no** `started_at` and a dead pid, which a `started_at`-consulting test must
refuse) and it is the one that fails; M9's and M10's shared test asserts the record's existence, not a
proxy for it.

**Arms, failability, each by behaviour:** arm B fails when the `identity.json` write is neutered; arm C
fails when `recorded_columns` is dropped from the ledger line (emptying it is not enough — the
key-set arm survives that, which is why the mutation must remove the key); arm D fails when
`identity.json` leaves `_DRY_RUN_FIXED_FILES`; arm E fails when § Operation commands' `Status` cell is
put back to `NOT BUILT` (2 failed, including `…_are_parsed_at_all`); arms A and G as in § 4.

## 9. Task 18's two passes, re-run

**Mechanical**, my own script over `README.md`, `docs/design-principles.md`,
`docs/experimental-designs.md`, `docs/reference.md`, `docs/feasibility-llm-growth-studies.md`,
`CLAUDE.md`, fenced blocks skipped: **0 problems.** Every check proven able to fail by appending one
line to **every** file in the list:

| Probe | Problems reported |
|---|---|
| `## Resuming` (duplicate anchor) | 2 |
| a line ending in a space | 6 |
| a tab-indented line | 6 |
| `a 3 x 5 grid` | 6 |
| `## An en–dash heading` | 6 |
| `[nope](docs/no-such-file.md)` | 6 |
| `[nope](#no-such-anchor-xyz)` | 6 |
| a 3-cell row under a 2-cell header | 1 |
| `\|  \|  \|` | 1 |

**Cross-document.** `README.md`, `docs/design-principles.md` and `docs/experimental-designs.md` are
**untouched by the branch** (`git diff main...HEAD --stat` empty for all three), and every
`cohort-pilot` literal I checked is present and unchanged — `[0.488, 0.661]`, `[0.517, 0.683]`,
`[0.347, 0.477]`, `[−0.007, 0.059]`, `[−0.213, −0.125]`, `0.014`, `8e21`, `1a2b`, `3d8a`, `6b1f`,
`2f5c8d0`. **Nothing narrowed.** Removed-string sweep over the six files, `grep -RnF`, file list named
and output never filtered: `"attempt"` **0**, `"attempt":` **0**, `"n":` **0**; can-fail control
`"attempts"` → **1 hit**, `docs/feasibility-llm-growth-studies.md:923`, the analysis' own plugin dict,
unrelated to the ledger. `attempts` in the four documents: nine occurrences, every one an output
(`run.yaml`'s five example lines, and prose defining it as a count) — **no passage shows it as an
input.** § The one config file does not move.

---

## Findings

### Major 1 — `E-RESUME-LEDGER-UNREADABLE`'s § Errors row is narrower than its code, and denies the fourth fault by name (task 16)

`docs/reference.md:658` reads *"…it is not valid JSON, it parses to something other than an object, or
it is missing any of `step`, `scope`, `condition`, `repeat`, `status`. **Three faults, one code**, one
remedy — the ledger was truncated or hand-edited. … `returned` and `recorded_columns` are **not** in
the required set: a ledger written by an earlier build reads clean here."*

There is a **fourth** emit site, and it is exactly the case that sentence denies:

```
$ grep -rn 'code="E-RESUME-LEDGER-UNREADABLE"' src/publishable/
src/publishable/lineage.py:478  src/publishable/lineage.py:483  src/publishable/lineage.py:489
src/publishable/cli.py:2262
```

`src/publishable/cli.py:2256–2263`, inside `_reconstitute`:

```python
for name in ("returned", "recorded_columns"):
    if name not in entry:
        raise ContractError(
            f"… the completed record for {execution.step_name!r} … has no {name!r}; "
            "a run recorded by a build older than this one cannot be resumed",
            code="E-RESUME-LEDGER-UNREADABLE",
        )
```

So a ledger written by an earlier build reads clean at `read_execution_ledger` and then earns **this
same code** at `_reconstitute` — the message says so in its own words. The row's *"Three faults"*
count and its *"reads clean here"* clause are both false of the code taken whole, and § Errors carries
**one row per code, not per emit site** (`CLAUDE.md` § Misreadings).

**This is the amendment item this task was told to close.** Task 16's brief: *"(a)
`E-RESUME-LEDGER-UNREADABLE`'s § Errors row is **narrower than its code** — Decision 17's row was
grepped and covers two of its three faults — so widen it to cover **every** fault the code raises it
for."* The report answers: *"the ledger row names all **three** (… the amendment's item (a),
closed)"* — a count carried from the brief rather than derived from the emit sites, and the report's
own § Errors paragraph claims *"Fifteen rows written, one per code, each covering **every** fault its
code is raised for."*

**Route.** Widen the row to name the fourth fault, and delete (do not rewrite) the *"reads clean
here"* clause — or split the row's claim so that *the required set* is scoped to
`read_execution_ledger` and the `_reconstitute` check is named beside it. Then append a correction to
the batch-4 report, since its claim that item (a) is closed is what a later reader would trust.
Established **by reading**, with the grep above.

### Major 2 — `command_resume`'s shipped docstring asserts four things this batch falsified, and its own last sentence contradicts them (task 16)

`src/publishable/cli.py:4880–4890`, inside `command_resume`'s docstring:

> **Decision 13 is NOT implemented here** … Every refusal below RAISES `ContractError` today … **There
> is no live exposure — `resume` is not dispatched, so nothing can reach `main` this way** — but **the
> containment does not exist yet** and must not be assumed by the task that adds the remaining
> refusals. **Task 16 owns building it**, over all fourteen codes at once.

At HEAD all four clauses are false. Decision 13 **is** implemented in this very function — the
`except BaseException` handler with the fresh credential-bearing `Collector` sits eighteen lines
below the paragraph. `resume` **is** dispatched (task 15). The containment **does** exist. Task 16
**built** it. And the same docstring's closing line says the opposite:

> Every step above raises; the containment that turns each raise into a redacted diagnostic is
> `command_resume`, which is the only caller.

*(That closing line was written for `_resume_prepared` and now sits in `command_resume`'s own
docstring saying `command_resume` is the only caller of itself — a second incoherence from the same
split.)*

The append-a-correction rule governs the **development record**, not source docstrings, and this batch
knew the difference: at `tests/test_cli.py:25100` task 16 appended a correction to a stale
measurement in a test comment. It did not sweep its own function.

**Route.** Delete the paragraph (`CLAUDE.md` § Habits — *prefer deleting a claim to rewriting it*),
and reconcile the closing sentence with the split. Established **by reading**, quoted above.

### Major 3 — `freeze._assert_refused` cannot check the `code` it is given: 21 call sites assert *that* a refusal happened, not *which* — and the concern is filed nowhere

```
$ grep -c "_assert_refused(result" tests/test_freeze.py
21
$ sed -n '115,120p' tests/test_freeze.py
def _assert_refused(result, code: str, exit_code: int, ledger_before: list[dict], run_dir: Path):
    assert isinstance(result, _Refused), result
    assert result.exit_code == exit_code
    assert _ledger_lines(run_dir) == ledger_before
```

`code` is never read. Reproduced by behaviour — `E-FREEZE-RUN-ENDED` renamed to
`E-FREEZE-BOGUS-MUTATION` in `src/publishable/freeze.py:139`:

```
$ uv run pytest -q tests/test_freeze.py
42 passed in 24.01s
```

and that code has exactly **one** test reference in the repository, the `_assert_refused` call at
`tests/test_freeze.py:147` — so the fail-open is total for it.

**Whose it is: H8b's**, `git log -S "_assert_refused" -- tests/test_freeze.py` → `60f5d61` *"H8b task
4: freeze.py — the refusal gate, template resolution, credential pre-check"*, a closed slice. This
branch added **zero** uses of the helper (`git diff main...HEAD -- tests/test_freeze.py` grepped: 0)
and its own two new arms assert on stderr, which is right.

**Why it is a finding against this batch.** It lives only in the batch-4 report's *Concerns for the
reviewer*. `docs/superpowers/spec-defects.md` has no entry for it (`grep`: 0 hits). This branch's own
batch 3–4 review already raised *"two escalations still living only in a report"* as a Major, and
`CLAUDE.md` § Habits states the rule: **a ledger line saying "filed" is not a filing** — a Concerns
paragraph is less than that. The report also undercounts it: *"ten shipped gate tests"* is 21 call
sites.

**Route.** File it in `spec-defects.md` as OPEN with an owner that is a fact and a reason (no
remaining slice owns `freeze`'s test surface), the reproduction above as its evidence, and the count
as 21. Established **by behaviour** (the rename) and **by reading** (the helper, the blame, the
absent filing).

### Major 4 — the refusal count is wrong by one, and it was carried into a dated build claim (tasks 16, 17)

`docs/feasibility-llm-growth-studies.md:2154`, inside § Executability's dated entry:

> H9b mints **thirteen** `E-RESUME-*` codes plus `E-FREEZE-CONFIG-EDITED` and retires none, and every
> one of the **fourteen** is reachable only from `resume` or `freeze`

Counted from the emit sites rather than from the phrase:

```
$ grep -rn 'code="E-RESUME-' src/publishable/ | grep -o 'E-RESUME-[A-Z-]*' | sort -u | wc -l
11                       # plus CODE-MOVED, PARAMS-MOVED, LOCKFILE-MOVED, raised through a loop variable
$ grep -c '`E-RESUME-' <the 14 rows at docs/reference.md 649-662>
14
```

**Fourteen `E-RESUME-*` codes, fifteen codes and fifteen rows in total.** The origin is design
Decision 17, whose heading says *"fourteen codes are minted"* and whose prose says *"Thirteen
`E-RESUME-*` codes plus `E-FREEZE-CONFIG-EDITED`"* — **while its own table lists fourteen
`E-RESUME-*` rows plus that one.** The plan's task 16 repeats *"the thirteen `E-RESUME-*` codes"*; the
batch-4 report carries it forward and then says *"Fifteen rows written, one per code"* eleven lines
later, which is the tell.

This is the shape `CLAUDE.md` names twice — *a slice … carries the summary phrase forward without
re-deriving what it counted* — and it landed in the one section the feasibility procedure requires to
be dated and re-derived (§ Feasibility analyses, step 10). `CLAUDE.md:211`'s *"refuses fourteen named
ways"* is the one place the figure is right, for the E-RESUME codes alone.

**Route.** Correct the feasibility sentence to fourteen/fifteen; append a correction to design
Decision 17 naming its own table as the evidence. Established **by reading**, with the greps above.

### Minor 1 — the `RunLock` message the document narrowed and the code did not (task 14/17)

`docs/reference.md:894` was narrowed by task 17 to *"A lock left behind by a killed process is
reported rather than assumed dead — **for `run` and `draft`, and for every case a liveness test cannot
answer.**"* The identical sentence in the code was not:

```
src/publishable/run_identity.py:69:  "A lock left by a killed process is reported, never assumed dead.",
```

`RunLock.__enter__` is **step 4 of the takeover**, so a `resume` that has just proved a holder dead
and unlinked its lock can print the unqualified form when a concurrent `resume` wins the claim — arm
G's own scenario. Route: narrow the message the way the document was narrowed. **By reading.**

### Minor 2 — two stale test comments the dispatch falsified (task 15)

- `tests/test_cli.py:23761` — *"`resume` is not dispatched until plan task 15, so `main(["resume", …])`
  still prints the unbuilt diagnostic and exits 2 … which is why guard-pin arm A's resume half stays
  `xfail`"*. Both clauses false at HEAD.
- `tests/test_cli.py:24677` — *"task 14's takeover does not exist yet."* False at HEAD.

Swept with `grep -rn "not dispatched\|does not exist yet\|owns building it" src/ tests/`; every hit
attributed — the other seven are about surfaces that genuinely do not exist (`units.py:2929`,
`validate.py:2468`, `report.py:1298`, `test_report.py:1988-9`) plus Major 2's three lines. Route:
delete the stale clauses. **By reading.**

### Minor 3 — the guard-pin editor correction repeats its own fault one row over (batch 1, carried)

The appended design correction (`a0f2f64`) fixes arms B and D's parenthetical and asserts *"the two
sibling parentheticals (arm C → task 6, arm E → task 15) are correct"*. Arm C's editor is **task 5**:
the plan's task 5 section reads *"You are the SOLE AUTHORIZED EDITOR of guard-pin arm C"*, and
`git log -S '"recorded_columns",' -- tests/test_cli.py` → `d4e0afd` *"H9b task 5"* is where it was
edited. The edit is properly authorized by the plan; the correction's claim about it is not. Route:
append. **By reading.**

### Minor 4 — `_dispatch`'s "load-bearing" branch order is constrained by nothing (task 15)

M6 is blind on a **full unfiltered run** (3132 passed, 0 failed), so the shipped comment's *"Safe only
because of this function's branch ORDER"* rests on a property no test can detect today. The report
disclosed this honestly and gave M7 as the corroborating measurement of what **is** bound (membership,
via the document-versus-CLI pair). It is not filed. Route: file it, so the next slice that adds a
two-token unbuilt name knows the order is unpinned. **By behaviour.**

### Minor 5 — `E-RESUME-ALLOCATION-STALE`'s row names six fault phrases against nine shapes (task 16)

The code raises it for: will-not-parse; not an allocation document; `arms` not a mapping; the axis
**set** disagreeing; **an individual axis's members not being a mapping**; that axis's level set
disagreeing; a membership that is not the roster in both directions; a holdout existing on one side
only; a holdout that is not a partition of the roster. The row names all but the fifth — *"has an
`arms` block that is not a mapping"* is the outer check, and `cli.py:2404`'s *"records axis {axis!r} as
{type}, not a mapping"* is a sibling. Borderline, and reported rather than argued. **By reading.**

### Minor 6 — two report-accuracy corrections

Concern 2's *"the end-to-end pin is arm G"* omits arm A (§ 6 above), and concern 3's *"ten shipped
gate tests"* is 21 call sites (Major 3). Route: append to the batch-4 report.
