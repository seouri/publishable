## Task 15

**Corrections that bind this task: C27.** **RULING II BINDS THIS TASK, and it is the single most
important task in the slice.**

**Narrow `holdout_train` per arm in `runner.execute_plan`, and delete
`assert holdout_train is None or arm_members is None`, IN ONE COMMIT.**

Today: `scoped_units = UnitList([u for u in units if u.key in arm_keys])` then
`step_units = UnitList(list(scoped_units), train=holdout_train)` — and `holdout_train` is built in
`cli` from `roster`, never from the arm. **The sibling that already got it right is fifty lines below
in the same function:** the fold branch composes
`train=UnitList([u for u in scoped_units if u.key not in handed])`. Copy its narrowing — and copy
**where it sits**, not only what it calls.

The composition becomes, for a condition-scoped execution with an arm:

```python
train_units = holdout_train
if arm_members is not None and execution.condition_index is not None:
    train_units = UnitList([u for u in holdout_train if u.key in arm_keys])
step_units = UnitList(list(scoped_units), train=train_units)
```

with `arm_keys` the **execution's own** arm, not any other.

**The first assert stays.** `assert holdout_train is None or fold_members is None` guards
`E-DATA-HOLDOUT-FOLD`, which this slice does not touch (C27).

**Update `cli._resolved_holdout`'s and `execute_plan`'s docstrings** where they cite
`E-DATA-HOLDOUT-CELLS` as the reason a branch is unreachable — three sites, and a grep for the code
across `src/` is how you find them all, not a memory of which files the scoping listed.

**Fixture F4, and it lands IN THIS COMMIT because it cannot exist before or after.** With
`E-DATA-HOLDOUT-CELLS` still live no end-to-end `run` can reach the composition, so the fixture is a
**direct `execute_plan` call** — and that call trips the very assert being deleted. Two arms of 4
units, `holdout_train` over the whole roster. Assertions: `set(io.units.train) ⊆ arm A's keys`
**and** `set(io.units.train)` is **non-empty** — a subset assertion alone passes on an empty train
side.

**Mutation MU-8:** narrow to the wrong arm (`arm_members[0]` rather than the execution's) — F4's two
arms with asymmetric membership catch it.

**Cost if this is got wrong:** a model trained on units it is then evaluated against, across arms,
with no diagnostic. **There is no later slice to catch it.**

**Must not touch:** the fold branch, the first assert, `attrition`'s narrowing rule.

