## Task 19

**Corrections that bind this task: none directly; read C8 and C9 for context.**

**The empty-cell × empty-fold-per-cell interaction — refused where it can be, RECORDED where it
cannot.**

- A cell too thin for `k` is **refused** at `validate` by task 7's clause, computed from task 3's
  bound. Pin it.
- A cell that is **empty** (a crossed combination no unit carries) makes the bound `0`, so any
  `k ≥ 1` is refused. Pin that too — and pin that an empty cell with **no** evaluation split declared
  is not an error at all, only task 18's warning.
- The per-**stratum** bound is **still a check that does not exist.** Cells add a **third** multiplier
  to `partition_units`' `c × s` independent lists. Update that docstring to say `cells × c × s`, and
  state explicitly that this slice **has not added** the per-stratum bound.

**This slice must not appear to have added a bound it did not add**, and **there is no later slice**
to add it: the filing task 20 writes says so as a fact, not as a deferral.

**Must not touch:** `partition_units`' body.

