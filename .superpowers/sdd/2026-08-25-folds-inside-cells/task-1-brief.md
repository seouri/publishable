## Task 1

**Corrections that bind this task: C23.** **This is the last slice; nothing follows it.**

**Capture the guard pin, before anything else in this slice moves.** Five arms, in
`tests/test_units.py`, `tests/test_cli.py` and `tests/test_sweep.py` as each arm's subject dictates.
The sole authorized editor and the post-edit state of each arm are **specified now**, in the test's
own docstring, per H8a's rule.

| Arm | Pins | Authorized editor | Post-edit state |
|---|---|---|---|
| A | `partition_units(_roster(50), 5, "d")` byte-identical (the existing oracle, re-asserted in a new test that names this slice), plus the clustered and stratified draws at their pinned seeds | **NONE — no task in this slice may edit arm A** | unchanged |
| B | A no-group-axis run's `sweep.yaml`: each `partitions` entry's key set is exactly `{fold, test, train}`, and the document has **no** `partitions_within` key | **NONE** | unchanged |
| C | `_resumed_allocation`'s round trip: the rebuilt `allocation.json` equals the recorded one | **task 17, and only task 17** | **unchanged.** If task 17 measures otherwise it edits this arm **once**, appends `holdout.within` to the expected document, reorders nothing, and reports the measurement |
| D | A no-group-axis `_prepare_run` makes **exactly one** `partition_units` call, with the **bare** digest — counted by monkeypatching a counting wrapper at the name `cli` resolves | **NONE** | unchanged |
| E | A 6-unit, no-`sweep.groups` generated config's **exact** `validate` finding set | **NONE** | unchanged — in particular it must never gain `W-DATA-CELL-THIN` |

**Arm D's mechanism, because a monkeypatch aimed at the wrong name is a named trap.** Patch the
symbol `cli` calls, not `units.partition_units`, and assert both the call **count** and the `digest`
argument's value. Task 8 reroutes that call site through `partition_within_cells`; **arm D must
survive that reroute unedited**, so it is written against the name `cli` imports and task 8 is
required to keep calling `partition_units` from inside `partition_within_cells` rather than
inlining it.

**Must not touch:** any `src/` file. This task adds tests only.

**Mutation:** delete the shuffle inside `partition_units` — arm A must fail. Run it, confirm the
failure, restore by **behaviour** (re-run and see green), never by `git checkout -- <file>`.

