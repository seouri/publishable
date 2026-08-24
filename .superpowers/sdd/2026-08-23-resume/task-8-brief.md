## Task 8

> **AMENDED 2026-08-23 by the controller, after batch 1 measured it.** This task's prescribed
> by-name-versus-structural mutation rests on a **recorded key colliding with a declared attribute
> name**, and that state is **unreachable**: `io.record` raises `E-STEP-KEY-COLLISION` first — measured as
> eight failed executions on batch 1's first capture. **So the mutation as written is blind and the task
> owes a replacement.** Build the discriminating case some other way, or state, with the config that would
> separate the readings, that none exists — *reporting a mutation blind is necessary and not sufficient*.
> Do not implement the prescribed mutation and report it as run.

**Pointer: Decision 4 binds this task, and it is the correction that reshaped the slice. Read design
§ Where this design disagrees with the scoping item 1 before writing a line.**

**The claim you are building against:** the aggregate phase reads `ExecutionResult.rows`, `.recorded`,
`.skipped` and `.returned` and **no file at all**. So a `resume` that skipped completed triples without
reconstituting them would publish every interval, every `n`, every delta and every hypothesis verdict
over the re-executed triples only — plausible numbers, no diagnostic, `status: completed`.

Build `cli._reconstitute` (or a new module if it grows past ~120 lines — say which you chose and why),
returning one `ExecutionResult` per triple with a `completed` ledger record:

| Field | Source |
|---|---|
| `execution` | the plan entry, matched on `(step_name, condition_index, repeat_label)` |
| `status`, `started_at`, `wall_seconds`, `error` | the ledger line |
| `returned` | the ledger line's `returned` |
| `rows` | `<step_dir>/units.parquet`, decoded through the **shipped** reader, each row narrowed to `{"unit": …}` plus the columns the line's `recorded_columns` names |
| `recorded` | `frozenset` of those rows' `unit` values |
| `skipped` | `frozenset` of `<step_dir>/ineligible.jsonl`'s `unit` values, `()` when absent |

**The narrowing is by `recorded_columns`, never by subtracting declared attribute names.** Correction 6:
a recorded key colliding with an attribute name lands the *recorded* value under one column, so a
by-name rule drops a real column — the *reserved name standing in for a structural fact* proxy this
repository has already paid for once.

**A missing `units.parquet` is legitimate when `recorded_columns` is empty** and is
`E-RESUME-ROWS-MISSING` when it is not. **Grep for an existing parquet reader before writing one** —
`artifacts` has a `_READERS` table with a `.parquet` entry — and report the grep. *Before writing a
walk, a guard or a containment, grep for one that already exists.*

**Use `runner.step_dir_for` for the step directory.** It already owns the degenerate-level collapse; a
second path construction would be a second answer to which directory a triple wrote into.

**Must not touch:** `stats.py`, `runner.attrition`, `run_record`'s blocks. **Appended 2026-08-23, with
the reason sharpened**: those functions are the **arbiters your reconstitution is measured against**,
so editing one would make guard-pin arm A compare a changed reader against a changed writer and the
equality would prove nothing. Not merely redundant — forbidden. No `*.md`. No arm. **The parquet
reader already exists** (`artifacts`' `_READERS` table, `.parquet` → `_decode_parquet`) and the
`executions.jsonl` reader is task 6's, built there for both of you — correction 21.

**Mutations, each with two branches checked in advance:** reconstitute without `rows` (arm A —
`recording_steps` drops the step, so `aggregated` loses whole conditions); narrow by attribute name
(the colliding-name fixture task 5 built); treat a missing parquet as always-fatal (the scalar-only
step); return a `list` where the caller expects a tuple of results in plan order (report whether any
assertion can see it, and if none can, say so rather than claiming it cannot happen).

---

