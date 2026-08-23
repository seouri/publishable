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

