## Task 12

**Corrections that bind this task: C13.**

**Verify — assert rather than assume — that the flat `fold_members` mapping survives per-cell
partitions, across ALL FOUR `stats.py` readers**, not the one `H3c-3-SCOPING.md` named. The four:
`handed_to`, `_gather_repeats`, `collapse_repeats`, `repeats_disagreeing` (the last two are H5b's
split, which is what killed the "only contact point" claim). Plus `runner.attrition`,
`runner._handed_keys`, `runner._units_failed_anywhere`.

**Expected outcome: no code change, one test per reader.** If a reader turns out to need arm
narrowing it does not have, this task grows and the report says so rather than the reader being
patched quietly.

**The property to assert:** each unit is in exactly one cell and in exactly one partition, so
`fold_members` stays a flat `label → frozenset(keys)` that partitions the roster — the same shape
`fold_members_for` produced before.

**Must not touch:** any of the seven readers, unless the verification fails.

---

# Batch D — the holdout half

**Ruling II governs this batch.** Task 13 lands before task 15; **task 15 narrows `holdout_train`
per arm and deletes `assert holdout_train is None or arm_members is None` in ONE commit**; task 16
retires `E-DATA-HOLDOUT-CELLS` strictly after task 15. **No commit exists in which the assert is gone
and `holdout_train` still comes from `roster`.**

