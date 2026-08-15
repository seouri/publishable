# Task 5 report — `k` and `k: all` are bounded by clusters

**Status: complete.** Commit `0261be0`, plus the test follow-up committed on top of it (the tip of
`h3b-clustered-units-and-partitions`; it is the commit carrying this report, so it cannot name its
own hash). `uv run pytest` 1290 passed + 2 xfailed (was 1272 + 2);
`ruff check` and `mypy` green. `ruff format` not run.

## What landed

- **`units.fold_basis(roster, cluster_by)`** — the one derivation of "how many indivisible things
  a fold may be drawn from": `cluster_count` when `cluster_by` is declared, `len(roster)` when it
  is not. One number, resolved by the caller that holds the roster; no function anywhere takes a
  unit count beside a cluster count.
- **`replication.resolve_repeats(config, digest, fold_basis=None)`** — the keyword `unit_count`
  is renamed, because the number it carries is no longer always a unit count. `_fold_k` takes the
  same number plus `cluster_by`, read from the `config` it already holds, **only to name the
  things it counted**: the refusal reads "over 5 clusters of `site`" rather than a unit count
  nobody supplied. That noun cannot introduce a second count. `E-REPL-FOLD-K-TOO-LARGE` is reused
  (same fault class, already in `REPL_DECLARATION_CODES`); no new code was minted, so nothing
  could escape `validate`.
- **`validate_config`** resolves the basis once, next to `_check_cluster_by`, inside
  `try/except ContractError` — `fold_basis` raises `E-DATA-CLUSTER-UNKNOWN` for a unit carrying no
  cluster value, and this module collects rather than raises. Both `_check_replication` and
  `_check_sweep` take `fold_basis` from that one local.
- **`cli.command_run`** resolves it the same way from the roster `run` re-resolves fresh.
- **Docs** — `reference.md` § Errors validate reports, both `E-REPL-FOLD-K` rows; and § Repeat
  kinds' "two things to expect" paragraph, which said flatly that each leave-one-out execution
  tests a single unit.

## Brief defects and pre-discharged work

1. **The brief undercounts the arrival paths: three, not two.** `_fold_k` has two (`validate`,
   `cli`), but the brief's own second bullet — the execution count `Leave-one-out is affordable`
   guards — reaches the number through `_level_count` → `_repeat_total` → `W-EXEC-BUDGET`, fed by
   `validate_config`'s **second** `len(roster)` call site (`_check_sweep`), which never touches
   `_fold_k`. That is the H3a "two of three" shape reproduced inside the brief warning about it.
   Three sites changed, three mutations run, one named failing test each.
2. **Brief step 6's document edit was already discharged by task 1** (commit `6a3c3a9`): the
   *Leave-one-out is affordable* row already read "counted over the cluster count rather than the
   unit count when `cluster_by` is declared, `k: all` being leave-one-*cluster*-out". Left alone.
   What actually needed editing was the § Errors table — `E-REPL-FOLD-K-TOO-LARGE` said "exceeds
   the resolved unit count", and `E-REPL-FOLD-K` said `all` fails only with "no resolved roster",
   which went counterfactual: the roster can resolve while its clusters do not.
3. **§ Clustered units needed nothing** — it already states "`k` is bounded by the cluster count,
   not the unit count. Ten animals admit at most 10 folds, and `validate` rejects a larger `k`".
   That sentence was describing code that did not exist; it now describes code that does.

## Tests (18 new)

Fixture is task 4's 7/3/3/1/1 over 15 units — 5 clusters, 15 units, two numbers that cannot be
confused. Every clustered probe has an unclustered control on the **same roster**.

| Where | Probe | Control that must report |
|---|---|---|
| `test_units.py` | `fold_basis(roster, "site") == 5` | `fold_basis(roster, None) == 15`, and `""` → 15 |
| `test_units.py` | a unit with no cluster value → `E-DATA-CLUSTER-UNKNOWN` | — |
| `test_replication.py` | `k: 10`, basis 6 → `E-REPL-FOLD-K-TOO-LARGE`, message names "6 clusters of `animal_id`" | `k: 10`, basis 15, no `cluster_by` → accepted |
| `test_replication.py` | `k: all`, basis 5 → 5 members, `fold01`…`fold05` | `k: all`, basis 15 → 15 |
| `test_replication.py` | `k: all` over a single cluster → `E-REPL-FOLD-K` naming `k: 1`, never a traceback | — |
| `test_replication.py` | an empty `cluster_by` still says "240 resolved units" | — |
| `test_validate.py` | through `validate_config`: `k: 10` clustered → `E-REPL-FOLD-K-TOO-LARGE` **beside** `E-DATA-CLUSTER-UNSUPPORTED` | same roster, `cluster_by` removed → neither code |
| `test_validate.py` | budget: clustered `k: all` vs `max_executions: 8` → no `W-EXEC-BUDGET` (5 ≤ 8) | unclustered → `W-EXEC-BUDGET`, "15 executions exceeds 8" |
| `test_validate.py` | direct `_check_replication(..., fold_basis=5)` — reaches the check where `E-DATA-CLUSTER-UNSUPPORTED` cannot | direct call, `fold_basis=15` → no finding |
| `test_validate.py` | `cluster_by` naming an undeclared attribute + `k: all` → `E-DATA-CLUSTER-UNKNOWN` **and** `E-REPL-FOLD-K`, `validate` never raises | — |
| `test_validate.py` | `W-REPL-FLOOR` — the basis's *other* consumer inside `_check_replication` — over a clustered `k: all` with `fold_basis=2` under a `default_repeats = 3` template | `fold_basis=15` → no floor warning |
| `test_cli.py` | end-to-end `run`: clustered `k: all` → `fold01`…`fold05`, 5 executions | same roster unclustered → `fold01`…`fold15`, 15 executions |

Because `E-DATA-CLUSTER-UNSUPPORTED` is still live (task 11 retires it), each `validate_config`
probe **asserts that refusal is reported alongside** the fold finding — that is the proof the check
was reached rather than shadowed — and the same rule is also exercised by a direct call, which the
refusal never reaches.

The `cli` test needs the refusal out of the way to reach `command_run` at all, so it monkeypatches
`cli.validate_config` to drop that one code and nothing else (every other error still refuses the
run). Without it this arrival path would be unpinned until task 11, which is when a mutation to it
would have surfaced.

## Mutations (each reverted; reverts verified by the full suite, not `git status`)

`__pycache__` deleted between each mutation and its revert.

| Mutation | Failing test |
|---|---|
| `_check_replication(fold_basis=len(roster))` | `test_k_above_the_cluster_count_is_refused_through_validate` (and `test_an_unreadable_cluster_leaves_k_all_unresolved_rather_than_raising`) |
| `_check_sweep(fold_basis=len(roster))` | `test_leave_one_cluster_out_is_costed_in_clusters` |
| `cli`'s `fold_basis=len(roster)` | `test_leave_one_out_draws_one_fold_per_cluster` |
| `_level_count`'s `return fold_basis` → `return None` (the shared consumer feeding both `W-REPL-FLOOR` and `W-EXEC-BUDGET`) | `test_leave_one_out_is_costed_in_units_when_nothing_is_clustered`, plus two pre-existing unclustered tests |

## Pinned for task 6

`_fold_k`'s body order is **untouched**: `E-REPL-FOLD-STRATIFY-UNSUPPORTED` still raises before
`k` is read at all. `fold_basis` and `cluster_by` are parameters, so nothing about resolving them
moved ahead of that raise.

## Concerns

1. **The `cli` arrival path is only reachable through the test's own bypass.** `command_run`
   returns `EXIT_WRONG` on `E-DATA-CLUSTER-UNSUPPORTED` before reaching the fold basis, so nothing
   a user can type exercises it yet. Consequently **task 2's owed § Errors AT RUN TIME row for
   `E-DATA-CLUSTER-UNKNOWN` is still not mine**: `units.clusters_of` is now *called* from `cli`,
   but unreachably. Task 11 (or whichever slice retires the refusal) owes it, and should also
   re-check my monkeypatch harness — once the refusal is gone the bypass is dead weight and the
   test should call `run_a_project` plainly.
2. **`partition_units` is still called from `cli` without the cluster mapping** (task 4's recorded
   gap, deliberately not touched). So a clustered run today draws the right *number* of folds and
   the wrong *membership*. The `cli` test asserts fold count only, and says so.
3. **`k: all` over a single cluster** reports `E-REPL-FOLD-K` with a message naming `k: 1` for a
   config that wrote `all`. Pinned by test, and it is the same shape a 1-unit roster already had,
   but a reader may find "`{kind: fold, k: 1}` is not a fold count" confusing when they wrote
   `all`. A dedicated message is a document change, so it is not in this task.
4. **`reference.md` § Repeat kinds' `fold` row says "cluster-respecting when `cluster_by` is
   declared"** — a document-describes-code-that-does-not-exist item, and *not* introduced here:
   `cli` calls `partition_units` without the cluster mapping (concern 2), so a clustered run today
   gets the right fold count and the wrong membership. Task 4's report flagged the wiring gap;
   this names the row that will be false until it lands. § Validation's *Folds fit inside the
   cells* row (`allocation: between`) is the same shape and is owned by a later slice —
   `allocation` other than `within` is still refused outright.
5. **`resolve_repeats`'s keyword rename** (`unit_count` → `fold_basis`) touched ~15 test call
   sites. It is a private-ish surface — nothing in `reference.md` § The importable surface names
   it — but any in-flight branch calling `resolve_repeats(..., unit_count=)` will break loudly
   rather than silently, which is the intended failure mode.
