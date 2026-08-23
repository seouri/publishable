# H9a — the re-entry seam, `draft`, and `dry-run` — the plan

**Written 2026-08-23 against `main` at `af78816`.** The design is
[`2026-08-23-re-entry-seam-design.md`](../specs/2026-08-23-re-entry-seam-design.md); its Decisions 1–17
bind, and the four controller rulings are Decisions 1–4 (R, S, T, U). **This plan argues from the code
and corrects the design where they disagree — § Corrections against the code is that list, and it is
not empty.**

**Fourteen tasks in seven batches, every batch reviewed.** `scripts/task-brief` extracts **one `## Task
N` section and nothing else**, which is why every binding ruling is restated **inside** each section it
binds rather than cited. A slice shipped a Critical because a ruling lived only in the plan's preamble.

**Standing constraints, restated in every task section that can violate one:**

- **Never `git checkout -- <file>`.** Copy before mutating; verify a revert by behaviour.
- **A probe that runs a creation command belongs outside this repository** — H6a made the dirty gate
  load-bearing and a reviewer has already dirtied this tree that way.
- **Run `uv run pytest` directly, in the foreground.** No monitor, no poll, no background job you
  then wait on. An agent stalled that way and shipped no report.
- **Before writing "no existing test asserts X", grep for it and report what you grepped**, newline-
  insensitively, and **attribute every hit individually** — two sweeps in this family missed a clause
  eight lines from one they found because hits were reconciled against a table of known homes.

---

## § Corrections against the code

Nineteen, each measured at `af78816`. The design carries thirteen of them in its own § Where this
design disagrees with the scoping; the six marked **new here** were found while writing task code.

1. **`command_run` spans 2009–3924 — 1916 lines**, not the scoping's 2009–3926/1918. `ast`,
   `fn.end_lineno`.
2. **The run-start probe is at 2565, after `allocate_run_dir` (2430) and inside `with RunLock`.** So
   the scoping's *"phases 1–5, and the probe"* is not a contiguous prefix, and `dry-run` cannot obtain
   the probe by running phases 1–5. Design Decision 6.
3. **`Observer` cannot be reused for `dry-run`**: `__init__` requires `run_dir: Path` and
   `_observe_one` calls `append_observation` unconditionally, before `record` and before the gate.
4. **`check_changed`'s omission has a stronger ground than "no baseline"**: `Observations.record`
   fills `_first_answered` from the facts it is handed, and `changed` compares the *next* facts against
   that — so for one round per condition it can only return `None`. Read, not inferred.
5. **Most of scoping task 1's arms already exist.** H8b arm A (the run directory's root list), H8b arm
   B (`environment/`), H8a arms A and B (`run.yaml`'s and `provenance`'s key lists), H8b arm C (the
   same restated), H8c task 17 arm A (the record's field-level shape), and `sweep.yaml`'s key list.
   Re-capturing recreates H8a's *same list pinned twice*.
6. **`("dry-run", "NOT BUILT")` is a shipped assertion, not an arm to capture**, and its sibling
   `{n for n, s in …} == set(NOT_BUILT_COMMANDS)` is self-maintaining and must not be edited.
7. **Eight `spec-defects.md` entries name H9, not six.** The two missed are the S4c-task-9
   `resolve_contrasts` precondition (H9a's) and `UpstreamLedger.record`'s missing-hash entry (H9c's).
8. **`docs/experimental-designs.md` § Mistakes core prevents is a second home of the dry-run-ledger
   claim** — *"recorded per condition at `dry-run`"*. The scoping names only § The apparatus files.
9. **`docs/feasibility-llm-growth-studies.md` carries three claims this slice falsifies**: *"`draft`
   … does not dispatch in this build"*, *"`dry-run` prints specified but not built"*, and *"`dry-run`
   prints … where every artifact will land"*.
10. **The `executions.jsonl` key set is asserted nowhere** — two `tests/test_cli.py` docstrings claim
    it (~10756, ~11261) and no assertion holds it.
11. **The shared `OPERATION_COMMANDS` arity arm is pinned by nothing.** `grep -rn "takes exactly one
    path" tests/` → 0; `grep -rn "no flags" tests/` → 1, and that one is `_DIFF_ARITY_MESSAGE`,
    `diff`'s own.
12. **§ Draft runs' conjunction cannot be honoured** — `code_dirty` is measured, so a clean-tree draft
    records `false`. Design Decision 9.
13. **`warn_c` does not cross the seam** — re-bound at 3906 before its second read. The true crossing
    count is **35**, after removing `warn_c`, `r`, and the comprehension variable `u` from a raw 38.
14. **Phases 1–5 hold four early exits, not five** — the `return` at 2361 is inside the nested
    `_include` def.
15. **Two shipped comments already assert `draft`'s behaviour** and must be re-read when it lands:
    `hashes.py`'s `code_hash` docstring and `runner.py`'s *"`draft` and `resume` when they land
    (H9)"*.
16. **new here — `_dispatch`'s branch order is load-bearing and must not move.** The built branches
    precede the `NOT_BUILT_COMMANDS` lookups deliberately (its own comment says so), and the two-token
    arm `f"{command} {rest[0]}"` is evaluated **before** the single-name lookup. Adding two names to
    `OPERATION_COMMANDS` is safe only because that arm comes first; a task that "tidies" the order
    changes what `publishable draft <path>` prints.
17. **new here — `run` prints `warn_c` twice under one name.** The `W-ENV-UNLOCKED` collector at 2405
    and the `W-APPARATUS-UNANSWERED` collector at 3906 are two bindings of one name. The extraction
    moves the first; the second is a fresh local in phase 9 and must stay one. A brief that treated
    `warn_c` as a single value would have carried a diagnostic across the seam.
18. **new here — `validate_config` does not call `build_manifest`.** Attributed: **one** hit in
    `validate.py`, a comment at its `_check_units` region reading *"a repo-less config still has to be
    one `manifest.build_manifest` can execute"* — a comment, not a call. So `dry-run`'s manifest build
    is genuinely new work, and it is the second of its three cost-ordered phases.
19. **new here — `E-CODE-EMPTY`'s refusal is inside phases 1–5** (the print at 2389, the exit at
    2390), so `dry-run` inherits it. That is correct and worth stating: a config whose hashed trees
    hold no file is refused before any metered call, which is the cost ordering doing its job.

**Appended 2026-08-23, batch 3–5 fix round (Major 4 of
[`task-b4-review.md`](../2026-08-23-re-entry-seam/task-b4-review.md)) — correcting correction 11
above, not replacing it (a dated record is appended to, never retro-edited):**

20. **Correction 11's "the shared arm is pinned by nothing" is false — both greps in it were on
    message text, which answered "where does this spelling appear" rather than "what does this
    guard do."** The full-suite mutation that drops only the **count** half of the shared condition
    (`if len(rest) != 1:`) fails two shipped tests that predate this slice
    (`tests/test_cli.py::test_a_missing_argument_is_an_invocation_error` and
    `::test_operation_commands_take_no_flags`, both `git log -S`-dated to `dc21d55`) — so the count
    half was already pinned before task 4. Only the **flag** half
    (`rest[0].startswith("-")`) was genuinely unpinned, which is what task 4's own mutation (dropping
    only that half) actually shows. The task 4 pin itself stands; the claim about what it was a
    *first* pin of does not. `docs/superpowers/specs/2026-08-23-re-entry-seam-design.md` Decision 13
    carries the matching appended correction.

---

## Task 1

**Ruling U binds this task (design Decision 4): the pin comes first, and every arm is captured in the
shape the design has already decided.** H6a captured arms against a superseded signature and forced a
later task into an unauthorized edit; H6b captured forward and its edit matched byte for byte. **You
are the only task in this slice that may create an arm.** Every arm below gets an authorized editor or
an explicit **NONE**, and the authorized post-edit state is already written in the design — copy it
into the arm's own docstring, because that is the only place a later implementer will read it.

**Also binding: proving an arm cannot move is NOT proof the line is pinned** (H6b whole-branch gate,
Major 2). For each arm, run a mutation in the **production** code and show the arm fails. An arm you
cannot make fail is not an arm.

Build arms **A–E** in `tests/test_cli.py`, and **cite** arms F and G rather than capturing them.

- **Arm A — a completed `run`'s whole `run.yaml`, leaf by leaf.** Drive `run_a_project` with a sweep
  (`grid` over `analysis.method`, two levels), `replication.repeats = [{kind: seed, n: 2}]`, a real
  `aggregate` metric (`aggregate_returns=`, the helper every end-to-end test here uses), and read the
  record back. Walk it into a sorted list of `(dotted_path, value)` leaves, **normalizing**: any key
  named `at`, `started_at`, `wall_seconds`, `run_id`, `hostname`; any value that is an absolute path
  under `tmp_path`; and the three hashes. Assert the normalized list equals a literal captured **by
  running**, not transcribed from `run_record.py`. The normalization list is the one § 5 of the design
  fixes in advance — do not extend it, and if you must, say so in the report as a finding.
- **Arm B — `run`'s full stdout, line by line**, for that same completed run, normalized the same way.
- **Arm C — the four exit codes**, each asserted **beside** the `status` it wrote and each in its own
  test: `completed` → 0, `partial` → 3, `failed` → 4, apparatus-unreachable → 5. H7d Part B pinned
  exit and status separately for a reason its own Fixture U states — a build deriving the code from
  the status cannot tell a truncation `partial` from an unreachable-apparatus `partial`.
- **Arm D — the `executions.jsonl` line's key set**, exactly `{step, scope, condition, repeat, status,
  started_at, wall_seconds, error}`. **This is new coverage**: the claim exists in two docstrings in
  this same file and in no assertion. Grep for `wall_seconds` and for `keys()) ==` over `tests/`
  before you write it, and report both greps with every hit attributed.
- **Arm E — the four early exits of phases 1–5**, each reached end-to-end through `main([...])`: a
  config that fails validation, a dirty `src/**`, a roster refusal, and the zero-file `E-CODE-EMPTY`.
  Assert the exit code **and** the printed code, and for the dirty case assert **no run directory was
  created**.
- **Arm F — cite.** `test_reference_cli_tables_are_parsed_at_all` already asserts
  `("dry-run", "NOT BUILT")`. Add nothing. Record in this task's report that **task 9 is its sole
  authorized editor** and copy the post-edit state from the design.
- **Arm G — cite.** Name the six existing pins listed in correction 5 and say, per arm, which claim it
  already holds. **Do not re-capture any of them.**

**Must not touch:** anything under `src/`. No `*.md`. No existing test's assertions.

**Report:** every arm, its mutation, and the failure it produced. A named arm with no test is not an
arm.

---

## Task 2

**Ruling S binds this task (design Decision 2): the extraction moves phases, and it must NOT move the
arm-plan resolution.** `_resolved_group_axes` (line 2314) and `arm_members` (2331) sit inside the
region you are extracting. They move **as-is, in place, in their current relative order**, and nothing
about *when* they run changes. H3c-3's remaining 14 owns that hoist — its task 2 — because folds and
holdouts inside cells need the axes realized before the cell decomposition. **Same function, different
move.** If you find a reason the hoist would make this extraction cleaner, that is a finding to
report, not a change to make.

**Ruling T also binds (design Decision 3):** you introduce the `allow_dirty` parameter, and **the
pathspec never moves.** `provenance.py` is not in your file list. `git_provenance`'s call, its
`-c` neutralization flags and `HASHED_TREES` are byte-unchanged, and your diff must show it.

**Ruling U binds (design Decision 4):** task 1's arms A–E have **no authorized editor**. If one fails,
you have found a finding to report — **leaving the branch red is correct.** An implementer may not
self-authorize an arm edit, even a mechanical one, even one that turns out clean.

**What to build.** In `cli.py`:

```python
@dataclass(frozen=True)
class Prepared:
    """Everything phases 1-5 of `command_run` produce that phases 6-10 read.

    Thirty-five values, measured rather than chosen: an `ast` walk over
    `command_run` at `af78816` found exactly this set assigned before the
    `allocate_run_dir` call and read after it before being re-assigned there.
    The count is the argument FOR the seam: nothing in phases 6-10 can be
    re-entered without these, so a second entry either receives them or
    recomputes them, and recomputing is what `resume` (H9b) must not do.

    `c` is the run's live `Collector` -- a channel, not a value. It is in here
    because phases 6-10 append to the same collector, and it is named
    separately so a reader does not mistake it for state.

    Frozen on purpose: phases 6-10 must not write back into what phases 1-5
    pinned. That is the property `resume` will rest on.
    """
```

with the 35 fields in their assignment order: `c`, `doc`, `repo_root`, `git`, `digest`, `input_dir`,
`output_dir`, `units_decl`, `conditions`, `run_template`, `credentials`, `roster`, `beside_n`,
`weight_by`, `weights`, `weighted_beside`, `cluster_by`, `clusters`, `levels`, `repeats`, `partitions`,
`fold_members`, `group_axes`, `holdout_plan`, `eval_roster`, `arm_members_map`, `plan`, `cfgs`, `ch`,
`ph`, `manifest`, `lock_path`, `lock_hash`, `upstream_ledger`, `upstream_resolver`. **Verify the list
by re-running the `ast` measurement yourself** — it is cheap, and a field list carried from a plan is
the shape correction 13 is about.

```python
def _prepare_run(config_path: Path, *, allow_dirty: bool) -> "Prepared | int":
    """Phases 1-5 of a run, for every command that is a second entry into them.

    Returns `Prepared` or the exit code the run would have returned. **Every
    caller checks the union with `isinstance`, never truthiness** -- `EXIT_OK`
    is `0` and a truthiness test would mis-handle it. Phases 1-5 never return
    `EXIT_OK` today, which is exactly why that mutation is blind and why the
    rule is stated here rather than pinned: `mypy` is the enforcer, and task
    1's arm E pins the four codes end to end instead.

    `allow_dirty` is the one thing that varies between callers, and it varies
    the GATE, never its PATHSPEC. `run` passes `False`, `draft` and `dry-run`
    pass `True`. Widening what `E-CODE-DIRTY` covers is a separate, DECLINED
    decision (H6b Decision 12) that lives one line from this one.
    """
```

The body is `command_run`'s lines 2010–2426 moved **verbatim**, with the four `return EXIT_WRONG`
statements kept, the six print sites kept on their current streams, and the dirty check wrapped as
`if git.code_dirty and not allow_dirty:`. `command_run` becomes:

```python
def command_run(config_path: Path) -> int:
    prepared = _prepare_run(config_path, allow_dirty=False)
    if not isinstance(prepared, Prepared):
        return prepared
    return _execute_prepared(prepared, draft=False)
```

where `_execute_prepared` is lines 2430–3924 with each of the 35 names read off `prepared` at the top
of the function — one `p = prepared` unpack block, not 35 attribute accesses scattered through 1500
lines, so the diff of the body itself is empty.

**Watch two things the measurement found.** `warn_c` is **two** bindings of one name (correction 17) —
the `W-ENV-UNLOCKED` collector at 2405 moves into `_prepare_run` and the `W-APPARATUS-UNANSWERED`
collector at 3906 stays a fresh local in phase 9. And `credentials` is computed **before** the roster
resolution deliberately (the comment at 2052–2058 says why: a resolver's body is the first thing here
that can raise carrying a credential). **Preserve statement order throughout**; this pair is the one
where reordering is silently wrong rather than loudly wrong.

**Mutations.** (a) Return `Prepared` without the dirty check when `allow_dirty=False` → arm E's
dirty-tree test must fail. (b) Move the `credentials` assignment below the roster resolution → **named
blind in advance**, because no shipped fixture makes the two orders differ. **The replacement is
mandatory and it is not a fork**: build a resolver-raises fixture at `run` — a resolver whose body
raises with a **declared** credential in the message — and assert `<redacted:…>`. It is a variant of
tests that already ship: H7b Part B pins resolver-raise redaction at both `validate` and `run`, and
H6a batch 3 measured that a resolver's body runs at `validate` dispatch, so the shape exists. **Do not
substitute an assertion over `_prepare_run`'s own AST** — statement position answers *where does this
sit*, not *does a credential leak*, and answering with a position is the proxy substitution this repo
has paid for twice. If the fixture genuinely cannot be built, that is a finding to report, not a
second-choice pin.

**Must not touch:** `provenance.py`, `runner.py`, `apparatus.py`, `run_record.py`, any `*.md`, any of
task 1's arms, and the arm-plan resolution's position.

**Report:** the two-worktree comparison. One config, run on a `main` worktree and on this branch;
`run.yaml` compared **leaf by leaf**, the run tree **path by path**, stdout **line by line**, the exit
code. The normalization list is fixed in advance by the design — **every remaining difference must be
attributed individually.** Green tests are not the evidence; H6b's gate is the precedent.

---

## Task 3

**Ruling T binds this task (design Decision 3): `draft` relaxes the gate and must NOT widen what the
gate covers.** The pathspec stays `src/**` and `templates/**`. `provenance.py` is not in your file
list; `git_provenance`, its `-c` flags and `HASHED_TREES` are byte-unchanged and your diff must show
it. H6b Decision 12 **declined** widening `E-CODE-DIRTY`'s pathspec to the repository root, and the
two edits are one line apart — **a draft must not close a declined decision sideways.**

**Ruling S also binds:** you touch `command_run`'s neighbourhood and you may not move the arm-plan
resolution (`_resolved_group_axes`/`arm_members`) — that is H3c-3's task 2.

**What to build.** In `cli.py`:

```python
def command_draft(config_path: Path) -> int:
    """`publishable draft` -- `run` with the dirty-tree gate relaxed.

    `reference.md` § Draft runs: a provisional run whose code state is not
    reachable from any commit. The gate exists to protect a RECORD's identity
    claim; a draft's record says `draft: true` in its own top-level key, which
    is what every reader keys on (`report.py` twice, `diff.py` once -- grepped,
    all three read `record.get("draft")` and none reads `code_dirty`).

    `git.code_dirty` stays a MEASUREMENT: a draft of a clean tree records
    `false`, because `provenance.git_provenance` answers about the tree and
    forcing it would make a provenance figure lie about the one thing
    provenance is for. § Draft runs' conjunction is corrected in task 6.
    """
    prepared = _prepare_run(config_path, allow_dirty=True)
    if not isinstance(prepared, Prepared):
        return prepared
    if prepared.git.code_dirty:
        # A notice, not a warning and not a finding: it changes no exit code
        # and enters no record. stderr, because it is about the invocation
        # rather than part of what the run reports -- and because `run`'s
        # stdout is pinned (task 1, arm B) and this must not enter it.
        print(
            "notice  draft   src/** or templates/** is uncommitted; "
            "recording draft: true and git.code_dirty: true",
            file=sys.stderr,
        )
    return _execute_prepared(prepared, draft=True)
```

`_execute_prepared` passes `draft=draft` to `assemble_run_yaml`, which **already takes it** (`draft:
bool = False`, writing `"draft": draft`) — measured, so no signature changes.

**Fixture Q** — `draft` on a **dirty** tree, outside this repository: scaffold a project, commit, then
write into `src/**`, then `main(["draft", cfg])` via a direct call to `command_draft` (the name is not
dispatched until task 4). Assert exit `0`, `record["draft"] is True`,
`record["provenance"]["git"]["code_dirty"] is True`, and the notice on **stderr**.

**Mutations.** (a) Pass `draft=False` → Q's `draft` assertion fails. (b) Force
`code_dirty=True` under `draft` → task 6's Fixture R fails (declare it here, build it there).
(c) Delete the notice → Q's stderr assertion fails; **assert it on stderr, not on a combined stream**,
because an absence asserted on the wrong stream is this repo's recorded trap.

**Must not touch:** `provenance.py`, `run_record.py`, any `*.md`, task 1's arms, `NOT_BUILT_COMMANDS`
(task 4 owns it), the H7d Part B `max_failed_fraction` pin — `draft` runs the same loop and **must not
weaken that pin** to make a drafted truncation tidier.

---

## Task 4

**Ruling T binds (design Decision 3):** the gate's pathspec does not move. You wire a name; you change
no gate.

**What to build.** Three edits and one new pin.

1. `OPERATION_COMMANDS = {"validate", "run", "draft", "freeze", "report"}` and
   `handlers["draft"] = command_draft`. **Join the existing arm** — do not write a second arity
   enforcer. Its own comment argues against two enforcers of one rule, and `diff`'s separate arm is a
   different *arity*, not a second enforcer of the same one.
2. Remove `"draft"` from `NOT_BUILT_COMMANDS`.
3. `reference.md` § Operation commands: the `publishable draft` row's `Status` becomes `built`. **That
   row only.** The `dry-run` row is task 9's.

**Do not reorder `_dispatch`'s branches** (correction 16). The built branches precede the
`NOT_BUILT_COMMANDS` lookups deliberately, and the two-token arm is evaluated first. **One shipped
answer moves and belongs in your report**: `publishable draft new` reaches `_report_not_built` today
(the two-token key misses, the single-name lookup hits) and after this task reaches the arity arm,
printing `` `draft` takes exactly one path and no flags``. Assert it, so the change is pinned rather
than merely disclosed.

**The new pin, and it is the point of this task.** The shared arity arm is pinned by **nothing**:
`grep -rn "takes exactly one path" tests/` returns 0 and `grep -rn "no flags" tests/` returns 1, which
is `_DIFF_ARITY_MESSAGE`. Report both greps. Add a test asserting, for `draft`:

- `main(["draft"])` → `EXIT_INVOCATION` and the message `` `draft` takes exactly one path and no flags``;
- `main(["draft", "a", "b"])` → the same;
- `main(["draft", "--json"])` → the same. **This is the arm the `len` half cannot cover.**

**Mutation, and it is not blind:** replace the condition with a bare `len(rest) != 1`. The
`--json` case is one argument, so the two branches differ and the test must fail. Run it.

**One shipped test now drives your command and asserts only absences.**
`test_reference_cli_tables_match_what_the_cli_does` will call `main(["draft", "_probe_a", "_probe_b"])`
and assert the output holds neither `unknown command` nor `is specified but not built`, and that
nothing was scaffolded or executed. **That is a constraint, not a pin** (H8b's Minor: a CLI arm
demonstrated by one prose invocation and by nothing else). Confirm it passes and say so; it is not a
substitute for the mutation above.

**Must not touch:** `tests/test_cli.py`'s `("dry-run", "NOT BUILT")` assertion — **task 9 is its sole
authorized editor** — the `set(NOT_BUILT_COMMANDS)` equalities, which are self-maintaining, any other
§ CLI reference row, and `provenance.py`.

**Correction (whole-branch fix round, 2026-08-23), replacing this section's "one shipped answer moves"
sentence above:** measured through the real console script, `publishable draft new` does **not**
"after this task reach the arity arm" and does **not** print the arity message with the same exit
code. `rest == ["new"]` has length 1, so it never trips the arm's `len(rest) != 1` at all — it
dispatches into `command_draft` and fails inside `_prepare_run`, unable to open `new` as a path: exit
**1**, `` error   E-IO-FAILED          No such file or directory``. The built test's own docstring
(`test_h9a_draft_new_now_reaches_the_arity_arm_not_the_not_built_diagnostic`) already asserts this
correctly — `code != EXIT_INVOCATION`, not the arity message — despite what its name and this
paragraph both claimed. This was also wrong in the design's § 5 item 3 and in a dated
§ Executability entry in the feasibility analysis; both are corrected the same way.

---

## Task 5

`draft`'s three readers all ship and all are today testable only against **synthesized** records —
H8c Decision 7 says so in its own docstring. This task gives each a **real** draft.

Build, each through `main([...])` now that `draft` dispatches:

- **`report` refuses a real draft.** `main(["report", str(run_yaml)])` over Fixture Q's record →
  `E-REPORT-DRAFT`, exit `1`. Grep for the existing synthesized-record test first and **name it in
  your report**, so the new coverage is stated as a difference rather than as a count.
- **`study add` flags a real draft.** Bundle outside any repo (`study new`, then `study add`), then
  `report <study.yaml>` → the member's identity line carries the `**draft**` label and the render
  **succeeds**. Decision 7's asymmetry is the claim: a bundle flags, a single run refuses.
- **`diff` labels a real draft.** `main(["diff", draft_run_yaml, clean_run_yaml])` → the per-side
  header carries `draft` on one side and not the other. **Assert per side**, not as a substring of the
  whole output: `assert "draft" in out` has already passed in this repo because a member was named
  `draft_run`, and a `run` tag's pin has already passed on a bundle header's `##`.

**Each reader must be shown able to fail.** Neuter each reader's `record.get("draft") is True` test in
turn and confirm exactly the corresponding test fails.

**Must not touch:** `report.py`, `study.py`, `diff.py` — this task adds fixtures, not behaviour. If a
reader is wrong, that is a finding.

---

## Task 6

**Design Decision 9 binds this task.** § Draft runs reads *"Draft runs are recorded with `draft: true`
and `git.code_dirty: true`"*, and the second half is false of the code: `code_dirty` is computed from
the tree, so a draft of a clean tree records `false`. **Correct the document, not the code.** Forcing
the flag would make a `provenance` figure lie about the tree and would break `diff`'s `git` comparison
between a clean draft and the `run` of the same commit.

**Fixture R** — `draft` on a **clean** tree, outside this repository. The fixture must **verify its own
premise**: run `git status --porcelain -- src templates` inside it and assert it is empty, *then*
`main(["draft", cfg])`. Assert `record["draft"] is True` and
`record["provenance"]["git"]["code_dirty"] is False`, and assert the task-3 notice was **not** printed
— on **stderr**, the stream it writes to.

**Then edit § Draft runs**, minimally: `draft: true` is unconditional and is the flag every reader keys
on; `git.code_dirty` records what the tree was. Say which is which. **Prefer deleting the false half
of the conjunction to rewriting the sentence around it** — a rewrite invents, a deletion cannot.

**Sweep before you edit.** Grep `code_dirty` over `README.md`, `docs/design-principles.md`,
`docs/experimental-designs.md`, `docs/reference.md`, `CLAUDE.md` and
`docs/feasibility-llm-growth-studies.md`, **named individually, never `*.md`**, and attribute every
hit. Two known homes: § Draft runs and § The two files' `run.yaml` example comment. **Sweep for the
claim, not for the file the claim was first noticed in** — three sweeps in one slice stopped one file
short.

**Mutation:** force `code_dirty=True` under `draft` → Fixture R must fail. Its premise is verified
clean, so the two branches differ.

**Must not touch:** `provenance.py`, `cli.py`, § Operation commands' rows.

---

## Task 7

**Ruling R binds this task (design Decision 1): `dry-run` prints step directories and fixed files,
never `io.write` names from step bodies.** § Operation commands promises *"every artifact path that
would be written"*, which needs the calls inside user Python — and `reference.md` itself says core
never inspects the body of user Python. **A promise that requires breaking a stated non-promise is the
document being wrong**, and the document changes first (task 9 edits the row; task 12 edits the
transcript). **The narrowed output must say what it omits and why** — a line that quietly printed less
would reproduce the defect in the direction the reader cannot see.

**Ruling S also binds:** you call `_prepare_run`; you may not move the arm-plan resolution.

**Design Decisions 8 and 16 bind:** `dry-run` passes `allow_dirty=True` (it writes no record, so there
is no identity claim for the gate to protect), and it prints **no comparison list** — nothing here may
reach `contrasts.resolve_contrasts`, which is reached only from phase 8 and whose unguarded
unhashable-side crash is a standing precondition on H9.

**What to build.** `cli.command_dry_run(config_path: Path) -> int`, calling
`_prepare_run(config_path, allow_dirty=True)`, then printing — derived from `Prepared`, nothing
transcribed:

```
sweep: <n> conditions (baseline + grid) × <m> repeats = <e> executions
  <one line per condition: index_label and its values>
repeats: <the repeat plan, from `prepared.repeats`>
  seeds: [...]  (auto, from design digest)
  comparisons: paired (allocation: within)
steps: <step (scope) -> ...> from `prepared.plan`
statistics: basis units (n=<resolved> resolved); <derived-by note>
scale:  <u> unit-executions (<e> executions × <k> units handed to each)
would create <d> step directories under <output_dir>/<experiment>/run_.../
  <the fixed files a run writes, named>
artifact files inside a step directory are named by `io.write` in step code and
  are declared nowhere in the config, so they cannot be listed before the run
```

The step-directory count is **one per planned (step, condition, repeat) triple**, which is exactly
what `runner.step_dir_for` returns — call it, do not re-derive the path scheme. Print the directories
themselves, not only the count. The fixed files are `config.yaml`, `sweep.yaml`, `manifest/input.json`,
`environment/pyproject.toml`, `environment/repo_root.txt`, `executions.jsonl`, `run.yaml`, plus
`environment/uv.lock` when a lockfile resolved, `allocation.json` when a drawn axis is declared, and
`apparatus/probes.jsonl` when a probe is declared. **Derive each condition from `Prepared`, never from
a hard-coded list** — `lock_path is not None` decides the lockfile, and a reserved NAME standing in for
a structural fact is the proxy move this repo keeps paying for.

**`unit-executions` is task 8's.** Print the line, wired to task 8's function, and leave the
narrowing to that task if you are dispatched in parallel; otherwise build both.

**Fixture U** — the step-directory list **and the fixed-file list**, both compared **set to set**
against the tree a real `run` of the same config creates, not against a count and not against a
literal: a count literal that happens to match is the fixture-agrees-with-the-bug shape. **The
fixed-file list has three conditional branches and each needs a config that exercises it** —
`environment/uv.lock` (`lock_path is not None`), `allocation.json` (a drawn axis declared), and
`apparatus/probes.jsonl` (a probe declared). Without them the command's whole output rests on three
untested predicates, which is the *seam named in the brief and instantiated by no fixture* shape:
naming a branch is not testing it.

**Mutation:** drop the degenerate-level collapse by calling `step_dir_for(..., collapse_repeats=True)`
unconditionally → Fixture U must fail. Choose the fixture's repeat count so `True` and `False` give
different trees (n ≥ 2), and **say in the report why n = 1 would have made the mutation blind.**

**Must not touch:** `runner.py`, `apparatus.py` (task 10 owns the probe), `NOT_BUILT_COMMANDS` and
`OPERATION_COMMANDS` (task 9), any `*.md` (tasks 9 and 12).

---

## Task 8

**Design Decision 11 binds this task: reuse `runner._arm_keys` and `runner._handed_keys`; do NOT
extract the narrowing out of `execute_plan`.** That would be a second behaviour-preserving extraction
on a shipped path, in **phase 7**, outside the phases this slice is chartered to move, and it would
need its own pin arm and its own disclosure line. What prevents drift here is an **agreement pin**, not
a shared function.

**Before you write the narrowing, read `execute_plan`'s own** — the four-way `execution.scope` dispatch
around lines 685–735 — and restate it. *Before writing a walk, a guard or a containment, grep for one
that already exists*: `_arm_keys` and `_handed_keys` are already extracted, single-call-site functions,
and they are what you call.

**The narrowing, as measured at `af78816`**, in order:

1. `_arm_keys(condition_index, keys, arm_members)` narrows when a group axis is declared **and** the
   execution has a condition index.
2. Then: under a declared **fold** — `run` and `condition` scope receive **`None`**, `repeat` scope
   receives `_handed_keys(repeat_label, keys, fold_members)`, `summary` receives the whole
   (arm-narrowed) roster. Under a declared **holdout** — every scope receives the test partition.
   Otherwise — every scope receives the arm-narrowed roster.
3. **An execution handed `None` contributes zero**, and the printed line says so, because a fold's
   `run`- and condition-scoped steps see no units at all and a reader computing by hand would be
   short.

**Fixtures S and T — the agreement pin.** One **fold** config and one **group-axis** config in which
`dry-run`'s printed `unit-executions` must **equal the summed `len(io.units)` a real `run` of the same
config actually hands out**. The expected value is **summed from the real run** — a step records
`len(io.units)` per execution — never computed as `roster / k × executions`, which is arithmetic the
code could be wrong about in the same way. **S and T must give different answers**; if they coincide,
resize them, because two elements only ever distinguish two readings.

**Mutations.** (a) Drop `_arm_keys` → T must fail (its arms are proper subsets). (b) Drop the
`None`-contributes-zero branch and count the whole roster at `run`/`condition` scope under a fold → S
must fail (its fold has k > 1 and a `run`-scoped step). **Check both branches can differ before you
believe either mutation** — a mutation is a claim too.

**Must not touch:** `runner.py` at all. If `execute_plan`'s narrowing is wrong, that is a finding.

---

## Task 9

**Ruling R binds this task (design Decision 1).** You edit § Operation commands' `dry-run` row, and its
`Does` cell carries the promise Ruling R narrows. The row's two halves — `Status` and `Does` — are one
fact seen from two ends and are edited in **one commit**.

**Ruling U binds (design Decision 4): you are the sole authorized editor of guard-pin arm F**, and its
post-edit state was written before you existed. `tests/test_cli.py::test_reference_cli_tables_are_parsed_at_all`:
the line `assert ("dry-run", "NOT BUILT") in tables["Command"]` becomes
`assert ("dry-run", "built") in tables["Command"]`, **and** a line
`assert ("resume", "NOT BUILT") in tables["Command"]` is added so that table keeps a marked
row-presence probe — the device that test's own docstring says exists to rule out a parser finding
some rows but not the ones a reader would look for. `("validate", "built")` is untouched. **The
`set(NOT_BUILT_COMMANDS)` equalities are self-maintaining and must not be edited.** Your report must
show the diff is exactly those two lines with nothing reordered.

**What to build.** `OPERATION_COMMANDS` gains `"dry-run"`; `handlers["dry-run"] = command_dry_run`;
`NOT_BUILT_COMMANDS` loses `"dry-run"`. **Do not reorder `_dispatch`'s branches** (correction 16).
§ Operation commands' `dry-run` row: `Status` → `built`, and `Does` → *"Validates, expands the sweep
and repeat plan, builds the input manifest, probes the apparatus, prints the step directories and the
fixed files a run would write, and the unit-execution count. **Does not** list the artifact files
inside those directories: their names are `io.write` arguments in step code, which core never inspects
— see [design-principles.md § Greenfield only]. Creates nothing."* — wording yours, that content
mandatory, the link resolved.

**Add the end-to-end tests this slice's batching order defers to here**: `main(["dry-run", cfg])` over
a real project, exit `0`, the transcript on stdout, and the arity trio (`no argument`, `two
arguments`, `--json`) for `dry-run` as task 4 built it for `draft`.

**Must not touch:** § Before you spend it's transcript (task 12), § The apparatus files (task 13),
§ Draft runs (task 6), any other `Status` cell, `provenance.py`.

---

## Task 10

**Design Decisions 6, 7, 14 and 15 bind this task, and Decision 14 is the one that has already cost
this repo a credential leak.**

**Decision 14 — the recipe is its calls PLUS where they sit.** Copy `cli.py`'s probe-dispatch wrapper
(~2522–2548) **with its `try`**: `except BaseException`, `KeyboardInterrupt` re-raised fresh and
argument-less, a **fresh credential-bearing `Collector`**, rendered to stderr. The same containment
covers `observe_once`, where the probe body actually runs. H8c's `report` lifted `freeze`'s calls and
left the `try` behind, and a declared credential reached stderr in a case § Secrets promises to
redact. **The file you are copying from already has it right.**

**Decision 6 — do not construct an `Observer`.** Measured: `Observer.__init__` requires `run_dir:
Path` and `_observe_one` calls `append_observation` unconditionally. Call the shipped pieces instead —
`apparatus.observe_once` → `apparatus.check_facts` → `Observations.record` →
`Observations.warn_unanswered` — once per resolved condition, under that condition's own cfg from
`prepared.cfgs`, never the wide one. **Defaulting `run_dir=None` on `Observer` is rejected**: it is a
fail-open shape on a class whose whole guarantee is that the append happens first.

**`check_changed` is omitted, and the ground is measured rather than argued.** `Observations.record`
fills `_first_answered` from the facts it is handed; `changed` compares the *next* facts against that
entry. With one round per condition, the value the gate would compare against is the value it was just
given, so it can only return `None`. Do not call it, and put that reason in the code, not "there is no
baseline".

**Decision 7 — append nothing, and `replay_ledger`'s filter does not widen.** `PHASE_DRY_RUN` keeps
its constant and gains no call site; the **document** is what changes (task 13). Do not touch
`apparatus.PHASES`, and do not touch `replay_ledger`: `dry_run` is load-bearing in two shipped
fixtures as the phase the filter must **exclude** (`tests/test_apparatus.py` ~1113,
`tests/test_freeze.py` ~357), and deleting it would collapse two distinct exclusion reasons into one.

**Decision 15 — the cost ordering is the behaviour.** validate → manifest → probe, stopping at the
first failure: a config with an error exits `1` **without the probe being called**, and only a config
that validates reaches `5`. § Exit codes' own paragraph states this and has no reader; you are it.
Mint no code.

**Fixtures.** **V** — a project-local probe, called once per resolved condition (the probe counts its
own calls into a file **outside `output_dir`**, so the count is evidence and task 11's arm stays
true); `W-APPARATUS-UNANSWERED` fires for a declared fact it did not answer; exit `5` when it is
unreachable. **W** — the credential positive control: a probe raising with a **declared** credential
(through `Param(requires_env=)`, with the variable actually set, so the value set is real and the
redaction is not vacuous) in its message → `<redacted:…>` on stderr. **X** — cost ordering: a config
with a validation error exits `1` and **the probe's entry file does not exist**. An exit-code-only
assertion would pass with the ordering reversed.

**Mutations.** Remove the `try` → W must fail. Reorder so the probe precedes validation → X must fail.
Add `append_observation` → task 11's Fixture Y must fail. Each has two branches that differ; check
before believing.

**Must not touch:** `apparatus.py`, `freeze.py`, `runner.py`, any `*.md`.

---

## Task 11

**Design Decision 12 binds this task, and it corrects a premise you would otherwise write.** *Creates
nothing* is scoped to **`output_dir`**, not to the repository. `dry-run` imports the entrypoint and
runs `discover_local`, which writes `src/**/__pycache__/` and `templates/__pycache__/` — measured live
by H6b batch 4 for `validate`, and § Templates' *"goes dirty at `validate`"* is the shipped sentence
about it. **A repo-wide byte-identity assertion fails, and the fix would be to weaken the assertion**,
which is the worst of the three outcomes. Scope the arm, name `__pycache__` as the excluded residue
with that citation, and say in the code why that scoping **is** what the promise means: it is about the
artifacts of a run, and a bytecode cache is not one.

**Fixture Y.** A recursive `(relative_path, size, sha256)` snapshot of `output_dir` before and after
`main(["dry-run", cfg])`, asserted equal, plus the absence of any `run_*` directory. Then the second
arm: a run directory holding a **live `lock`** (write the lock file by hand, as `freeze`'s own tests
do — do not kill a real run), and `dry-run` against the same config completes at its normal exit code
and takes no lock. § One execution at a time says pointing a read command at a live run is *"as
ordinary as reading the ledger"*, and `dry-run` is the stronger case because it takes no lock at all.

**Mutation:** have `command_dry_run` create `output_dir / "scratch"` → Y must fail. And confirm the
snapshot helper can fail at all by running it against a directory you *do* write to — *prove every
sweep can fail* applies to a checker as much as to a claim.

**Must not touch:** anything under `src/` except the notice-free path you are asserting about; no
`*.md`.

---

## Task 12

Three document edits, all in `reference.md`, and one sweep that must be run before any of them.

1. **§ Before you spend it's transcript.** Replace `would write 64 artifacts under
   /secure/results/cohort-pilot/run_.../` with the narrowed lines Ruling R licenses, and **state the
   counting rule beside the number** so the next reader re-derives instead of carrying: one step
   directory per planned (step, condition, repeat) triple, which is what `runner.step_dir_for` returns.
   For the worked example that is **20** — `shared/step01_load_cohort` (1) + `conditions/<c>/step02_fit_model`
   × 3 (3) + `conditions/<c>/<seed>/step03_analyze` × 3 × 5 (15) + `summary/step04_compare_methods`
   (1). **Verify the 20 by running a dry-run of a 4-step, 3-condition, 5-seed project** rather than by
   trusting this arithmetic; if it disagrees, the arithmetic is the thing that is wrong and you report
   which.
2. **The omission sentence.** The transcript and the row must both say what is *not* listed and why,
   citing `design-principles.md` § Greenfield only.
3. **§ Exit codes and diagnostics.** `dry-run`'s cost-ordering paragraph and the `3`/`4` rows now have
   readers. **Change no code and no row's meaning** — if a row needs no edit, edit nothing and say so.
   H6a's batch 6 restraint is the precedent: a Minor named rather than a self-authorized out-of-scope
   edit.

**The sweep, before any edit — AMENDED 2026-08-23, batch 3–5 fix round (Major 2 of
[`task-b4-review.md`](../2026-08-23-re-entry-seam/task-b4-review.md)). This replaces the paragraph
below it, which is left struck rather than deleted so the reason for the replacement stays legible:
task 9's three unowned `reference.md` edits (its own report's Concern 1) already narrowed `:368`,
`:3756` and `:3882` away from `every artifact path` before task 12 was dispatched, so a sweep for that
phrase finds zero homes across all six files and "Measured already" below is stale — not because the
edits were wrong (the review adjudicated their content correct) but because the plan was never
amended to say what replaced what it swept for, which is exactly the omission
`CLAUDE.md` § The development record warns against.**

Sweep for `step directories` and `would write` instead — the phrasing task 9 actually landed — over
the same six files, **named individually, never `*.md`**, and **never filter the output of a sweep
whose job is to find a string; filter the file list.** Re-measured 2026-08-23 against `HEAD` at the
start of this fix round: `step directories` has **four** homes, all in `reference.md`
(`:368`, `:3673`, `:3756`, `:3882` — the last three task 9's, the first also task 9's but outside its
own section, per its Concern 1); `would write` has **three**, all in `reference.md`
(`:3094` — task 12's own, unedited; `:3673`, `:3756` — task 9's). `64 artifacts` keeps its one home,
`:3094`. Zero hits in `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`, and
`CLAUDE.md`. `docs/feasibility-llm-growth-studies.md` carries its own home of the artifact-path
promise (plan correction 9), owned by task 14, not this sweep. **Attribute every hit individually** —
a hit in a file already accounted for reads as noise, and that is how one claim's fifth and sixth
homes were missed in one slice. Editing `:3094`'s `64 artifacts`/`would write` line per item 1 above
will change its own count in a re-sweep; that is expected, not a discrepancy to chase.

~~**The sweep, before any edit.** `64 artifacts`, `would write`, and `every artifact path` over
`README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md`,
`CLAUDE.md` and `docs/feasibility-llm-growth-studies.md` — **named individually, never `*.md`**, and
**never filter the output of a sweep whose job is to find a string; filter the file list.** Measured
already: `64 artifacts` and `would write` have **one home each**, both in `reference.md`; a third home
of the artifact-path promise is in the feasibility analysis (task 14). **Attribute every hit
individually** — a hit in a file already accounted for reads as noise, and that is how one claim's
fifth and sixth homes were missed in one slice.~~

**`×` not `x`, including inside fenced blocks. Hyphens, never en dashes, in anything that becomes an
anchor. No positional row locators** — name what a sibling row *does*.

**Must not touch:** § Operation commands' rows (tasks 4 and 9), § Draft runs (task 6), § The apparatus
files (task 13), and the worked example's statistics — `r = 0.581/0.607/0.412` and every interval
around them **may not move**.

---

## Task 13

The records, and the sweep the scoping got one home short of.

1. **§ The apparatus files.** *"at `dry-run`, at run start, before each execution, and at `freeze`"* →
   delete `at dry-run` and add one sentence: `dry_run` is a **reserved** phase name that no build
   appends, because the ledger lives inside a run directory `dry-run` never creates. Naming it keeps
   the vocabulary total against `apparatus.PHASES`, which still holds four members and must.
2. **`docs/experimental-designs.md` § Mistakes core prevents — the second home the scoping does not
   name.** *"its facts are recorded per condition at `dry-run`, at run start, before every execution,
   and at `freeze`"*. `dry-run` **probes**; it does not **record**. Fix the verb's scope, minimally.
   **Sweep for the claim**, not for the file: grep `dry-run` over the four documents named
   individually (measured: `README.md` 3, `design-principles.md` 2, `experimental-designs.md` 1,
   `reference.md` 20) and attribute every hit. `design-principles.md`'s two are about flags-versus-
   names and are correct; check them rather than assuming.
3. **`apparatus.py`'s `PHASES` docstring** says `PHASE_DRY_RUN` *"is named here and called by NOTHING
   at this commit"* and cites the filing. After task 13 the filing is closed, so that paragraph is a
   **sentence going false under its own slice's change** — the most frequent single defect in this
   family. Rewrite it to say the constant is reserved and why, and **cite the design decision rather
   than the struck filing.**
4. **`spec-defects.md`.** **Strike** the `PHASE_DRY_RUN` entry with its resolution named — a live list
   keeps recruiting readers to a closed gap. **Amend, do not strike**, the S4c-task-9
   `resolve_contrasts` precondition: H9a discharges it for `dry-run` by construction (phase 1 *is*
   `validate_config`, and `resolve_contrasts` is reached only from phase 8), and it still binds
   `resume` (H9b) and `reproduce` (H9c). **Record, without taking**, that this file holds **eight**
   H9-owned entries rather than the six the scoping counted, naming the two extras and their parts.
   A ledger line saying "filed" is not a filing; check each entry you touch still reproduces before
   you write about it.
5. **`CLAUDE.md`.** One paragraph for H9a in the running record, in the established form: what it
   built, **what it retires (nothing) and what it unblocks (zero configs, with the structural
   reason)**, and the three or four things worth carrying. The order line: H9a is done; **H9b, H9c,
   H9d and H3c-3's remaining 14 remain.** Do not restate § Executability's table; point at it.

**Must not touch:** `reference.md` § Before you spend it or § Exit codes (task 12), the worked
example's numbers, any `src/` file other than `apparatus.py`'s docstring, and the H7d Part B
`max_failed_fraction` filing.

---

## Task 14

Both consistency passes, and the dated entry.

1. **Mechanical, over every `*.md` this branch edited**, written as a throwaway script: every relative
   link and `#anchor` resolves, no two headings in a file produce the same anchor, every table's rows
   match its header's column count with no empty row, no trailing whitespace, no tab, no invisible
   unicode. **Skip fenced blocks** — the docs contain markdown inside markdown. **Prove the checker
   can fail** before trusting it: a records task in this family disclosed eight false positives on
   first run.
2. **Cross-document, over the four documents only.** The classes that actually drift: the shared
   worked example (`cohort-pilot`'s 20 step directories is a **new** figure in it and must appear
   nowhere else in a contradicting form), config completeness (no field added), enum comments
   (`apparatus.PHASES` versus § The apparatus files — see task 13), declared-versus-derived, versions,
   and prevented mistakes. **The development record is exempt from both passes and must not be
   retro-edited.**
3. **§ Executability on this build** — one dated entry, *"Measured on 2026-08-23 against commit
   `<sha>` — after H9a"*, the **four-row table repeated character for character** from the preceding
   entry, and **no fifth number**. Derive each row rather than repeating the derivation: `dry-run` and
   `draft` neither run at `validate` nor are called from a step, the extraction is behaviour-preserving,
   nothing here reads an upstream, nothing here chooses an interval construction, and every one of the
   nine configs validates against `generic`, whose `apparatus_probe` resolves to `None`. **H9a unblocks
   ZERO configs**, and the reason is structural: both commands are second entries into a sequence these
   configs already reach or do not. Extract the preceding table programmatically and **diff it byte for
   byte** rather than retyping it.
4. **Three live claims in that same analysis go false and are corrected by appending, never by
   retro-editing a dated entry**: *"`draft` … does not dispatch in this build"*, *"`dry-run` prints
   specified but not built"*, and *"`dry-run` prints … where every artifact will land"* — the last
   being Ruling R's third home.

**Do not assert an ordinal.** *"the seventh consecutive entry"* is the easiest kind of claim to carry
without checking; derive it from the diff or omit it.

**Must not touch:** any `src/` or `tests/` file. If a pass finds a code defect, that is a finding to
report.
