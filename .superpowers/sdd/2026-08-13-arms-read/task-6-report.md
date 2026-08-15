# Task 6 report — The budget counts group conditions

**Status:** complete. **No code change and no document change was owed** — the arithmetic was
already correct after task 5, and task 1 had already rewritten the § Validation row. What landed
is the test that pins it, which nothing else did.

## The finding: the count is already right

`validate._check_sweep` computes `executions = len(conditions) * repeat_total` where
`conditions = expand(doc)`. Task 5 put group axes into `_axes`, so `len(expand(doc))` multiplies
by the group levels *before* the budget reads it — the budget path inherits the fix rather than
needing one. Probed before touching anything, with a 2-level group axis crossed with a 3-level
grid and 5 seed repeats against `max_executions: 20`:

```
6 conditions × 5 repeats = 30 executions exceeds 20
```

6 = 2 arms × 3 methods, and 30 is the real count. The message already names it, because the
message is formatted from the same `len(conditions)`.

**§ Validation's *Grid size sane* row needed no edit either.** Task 1 already rewrote it to
"conditions counted over every axis the sweep expands, a [group axis](#expansion-modes) included,
since a group level is a condition that executes like any other", which is exactly the behaviour.
`W-EXEC-BUDGET`'s own row in § Errors `validate` reports says "conditions × repeat total", which
is true by definition post-`groups` — task 1 deliberately left it, and I concur. Per the brief,
no change was manufactured on either side.

## What landed

**Commit `0a69863`** — `test(validate): the budget's condition count includes a group axis's levels`.
One test, `tests/test_validate.py::test_the_budget_counts_the_conditions_a_group_axis_expands`,
placed with the other `W-EXEC-BUDGET` tests.

Exact numbers, never membership:

| Leg | Assertion |
|---|---|
| Probe: `groups`(2) × `grid`(3) × 5 repeats, budget 20 | message is exactly `6 conditions × 5 repeats = 30 executions exceeds 20` |
| Control A (must be silent): same minus the group axis, budget 20 | no `W-EXEC-BUDGET` — 3 × 5 = 15 ≤ 20, so the two levels are what pushed it over |
| Control B (**must report**): same minus the group axis, budget 10 | message is exactly `3 conditions × 5 repeats = 15 executions exceeds 10` |

Control B exists because a silence-only control cannot distinguish "the group factor is counted"
from "the check is dead".

**How the check was reached without retiring `E-SWEEP-GROUPS-UNSUPPORTED`:** task 5's route —
`validate` collects rather than stops, so the warning is raised beside the refusal. The probe leg
asserts the *exact error set* is `{"E-SWEEP-GROUPS-UNSUPPORTED"}`, which also proves no unrelated
refusal is carrying the config. No refusal was retired and no baseline fixes a group level.

## Mutation — applicable, and it is the brief's own

Counting the product without `groups` (`sweep._axes` reads no `groups` entries, the brief's step 5):
**the new test fails alone** (`1 failed, 438 deselected`, `KeyError` on the absent `W-EXEC-BUDGET`).
Not an invented mutation against unchanged code, so task 4's escape hatch does not apply here —
the behaviour is newly live and this test is the only thing pinning it. `__pycache__` deleted
between mutation and revert; the revert verified by re-running the probes and the full suite, never
by `git status`.

## The `fold` question the brief routed to H3c-3 — measured, not derived

Task 5's expansion **did** change what the budget computes for a `fold` repeat over a group axis.
A 60-unit roster, a 2-level group axis, `{kind: fold, k: all}`, budget 10:

```
2 conditions × 60 repeats = 120 executions exceeds 10      # with the group axis
1 conditions × 60 repeats = 60  executions exceeds 10      # control, no group axis
```

Three parts, and only the third is H3c-3's:

1. `_repeat_total` → `_level_count` resolves `k: all` to `fold_basis`, which is the **roster**
   (or cluster) count that `_check_units` resolved. `fold_basis` did not move; `len(conditions)`
   did, so the product is now levels × roster where it was roster.
2. Under `allocation: within` — the only allocation this build accepts, `between` being refused at
   `_check_units` as `NOT BUILT` — **120 is the correct number**: every unit is in every condition,
   so each of the 2 conditions really does run 60 folds.
3. Under `allocation: between`, once built, folds are drawn within each cell, so the truth is
   2 cells × 30 folds = 60 and the budget would overcount by exactly the level count.
   `_repeat_total` never sees `allocation`, so the overcount is **latent, not reachable today**.
   That is task 1's concern 2 and § Validation's *Leave-one-out is affordable* row — H3c-3's,
   not fixed here, and no `between` test was added.

## Concerns

- **Non-blocking, pre-existing, reported so the next reader does not re-derive it:** § Validation's
  *Grid size sane* example reads `20 conditions × 10 folds × 3 seeds = 600 executions`, while the
  emitted message collapses every repeat level into one factor (`N conditions × M repeats = …`).
  The row is an illustrative failure, not a message template (task 1's reading of § Validation),
  and the arithmetic agrees, so nothing is owed — but the two shapes are not the same shape.
- Task 5's open concern that **`groups` has no shape guard in `_check_shape`** touches this path
  too: a malformed `groups` contributes no axis, so the budget silently computes the
  parameter-only product. Refused wholesale today; task 17 inherits it. Not widened here.
- The worked example is untouched — `cohort-pilot` declares no `groups`, no `src/` or `docs/` file
  was modified, and the only diff is one test function.

**Tests:** `uv run pytest` → **1408 passed, 2 xfailed** (was 1407 + 2 at `379cc18`); `ruff check .`
and `mypy` clean. `ruff format .` not run (`ruff format --diff` consulted for the new lines only;
the file carries pre-existing drift elsewhere that was left alone).
