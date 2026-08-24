## Task 5

**Pointer: Decision 5 binds this task. Ruling V's artifact is task 3's; this is the second half of
what a run must make durable.**

`executions.jsonl`'s line gains **two** keys, in `runner.execute_plan`'s single ledger write:

- `"recorded_columns"` — the sorted union of recorded column names for this execution, derived from the
  rows the `io` object already holds, `"unit"` excluded. **An empty list is meaningful**: it says the
  step recorded nothing, which is a different state from a missing `units.parquet`, and it is what
  makes the attribute subtraction in task 8 structural rather than name-based.
- `"returned"` — the step's return, written through `run_record.summary_values`. **Use that function,
  do not write a second expansion**: it is the same one `run.yaml`'s summary block uses, so the two
  cannot disagree, and it is idempotent on an already-expanded mapping, which is what makes reading it
  back safe. A `summary`-scope step can return an `Estimate`, which is not JSON-serializable — that is
  the whole reason this goes through `summary_values`.

**Do not add `attempt` and do not add `n`.** § Resuming already defines `attempts` as the count of a
triple's records, so writing it per line would store a derived figure in an append-only log;
`runner.attrition`'s own docstring already says no per-execution `n` is written. Both are **deleted
from the document** by task 17, not built here.

**Appended 2026-08-23, before dispatch — binding on this task, and it replaces a ground rather than a
decision.** The design's A1: `returned` is **not** serializable "by invariant". Measured —
`json.dumps({'r': float('nan')})` emits `{"r": NaN}`, and `coerce_scalars` passes a non-finite float
through unchanged, so a step returning one is reachable and legal. **Keep `json.dumps`' shipped
default (`allow_nan=True`)**: the same module reads the line back and `json.loads('{"r": NaN}')`
returns `nan`, so the round trip is exact, which is what arm A's leaf equality needs. Do **not** pass
`allow_nan=False` — that would fail a completed execution over a value `run.yaml` accepts — and do
**not** encode non-finite as `null`, which would make a resumed `per_repeat` differ from a
straight-through one. **Add a fixture whose repeat step returns `float('nan')`** and assert the
reconstituted value is `nan` rather than `None`; task 17 records the non-promise in the document.

**You are the SOLE AUTHORIZED EDITOR of guard-pin arm C**, which task 1 re-aimed at you from **NONE**.
Its post-edit key set is in its own docstring. **Two keys added, none removed, nothing reordered**, and
your report must show that diff and state that you edited a formerly-NONE arm by controller ruling.

**Must not touch:** any other arm; `run_record.summary_values` itself; any `*.md`.

**Mutations:** write `returned` without `summary_values` (caught by a new fixture with a `summary` step
returning an `Estimate` — check in advance that no shipped fixture already has one, and report the
grep); emit `recorded_columns` as the parquet's full column list rather than the recorded union (caught
by a fixture carrying a declared attribute, which task 8's fixture also needs — build it here and cite
it there).

---

