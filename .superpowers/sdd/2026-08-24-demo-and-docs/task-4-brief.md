## Task 4

**Binding corrections: 17, 21, 22.**

**The `credentials` region body, and `generate experiment`'s `required_env` merge** — the § Generators
half filed `NOT BUILT`. The body is the two-column `Variable | Needed by` table, one row per variable
any experiment's resolved template declares in `required_env`, sorted by variable name, with the
experiments needing it in the second cell. The empty state is the documented
`_(none yet — added as experiments declare them)_` row.

**Correction 21 binds this:** an **installed** template's class is `None`, so its `required_env` is
unreadable. A row is emitted only for a template whose class this build holds; an experiment whose
template is installed contributes a row saying so, **not silence**.

**Fixture:** two experiments, one declaring two variables and one declaring one of the same two, so the
merge has something to merge — a single experiment tests the write and not the merge.

**Must not touch:** `demo`, `list-templates`, `docs`' dispatch.

---

