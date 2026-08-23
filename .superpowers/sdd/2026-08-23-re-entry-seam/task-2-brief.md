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

