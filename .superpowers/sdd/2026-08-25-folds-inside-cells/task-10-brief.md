## Task 10

**Corrections that bind this task: C2, C18.**

**Retire `E-REPL-FOLD-CELLS`.** Remove the `fold` arm of `validate._check_evaluation_split_cells`.
The function keeps its `holdout` arm until task 16; when both arms are gone the function and its
call site go with them, and **`tests/test_validate.py::test_a_group_axis_alone_triggers_the_refusal_without_between`
is DELETED, not adapted** (C18).

**And pin the property the refusal was standing in for**, by mutation rather than by assertion:
`runner.attrition`'s per-arm denominator (`handed = union(fold_members) & keys` against the **arm's**
roster) and `runner._handed_keys`' per-`(arm, fold)` answer are **non-empty**, *because* of task 3's
bound. The mutation: remove the cell clause from the bound and watch a real `run` produce an arm
whose denominator for some fold label is **zero**.

**Must not touch:** `E-DATA-HOLDOUT-CELLS`, either assert in `runner.execute_plan`, `attrition`'s
narrowing rule.

**This task declines nothing, but note for the record:** the per-**stratum** fold bound stays a check
that does not exist, in this build and every build — **there is no later slice.** Task 19 owns
saying so.

