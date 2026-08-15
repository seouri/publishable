# Task 11 — controller additions

**Task 11 owes TWO rows, not one** — a registry row in § Errors `validate` reports **and** a § Validation
row. Tasks 2–3 wrote `E-DATA-ASSIGN-BLOCKED-CLUSTER` into prose at two sites (§ Clustered units and
§ Allocation's `blocked` paragraph) as a **forward reference**, deliberately unmarked, on the
understanding that this task lands before any mechanical pass. Without both rows the next pass finds a
code named in prose and registered nowhere.

**The ruling this implements, and its grounds** (settled by the user before execution): the documents
were contradictory. § Where units come from makes `blocked` the one declaration reading roster order as
data; § Clustered units said a cluster is drawn whole under `random` **or** `blocked`. **Block size
counts units and a cluster is indivisible, so no block size honours both** — and the existing
whole-cluster primitive *shuffles* cluster order, destroying exactly the property `blocked` exists for.

**Two controls that must report**, and they are the point of the task:
- `random` beside a declared `cluster_by` is **legal** — task 9 built it, and it draws whole clusters.
- `blocked` with **no** `cluster_by` is **legal** — task 10 built it.

Assert exact finding sets on all three configs, and mutate each control separately: neither may die to
the other's branch.

**The message** follows the sibling refusals' shape: what is wrong (block size counts units, a cluster
is indivisible, no block size honours both), and the two honest routes — `random` for a clustered draw,
`by_attribute` for a read one.

`assignment_for` already raises when `clusters is not None` for a method it has not implemented; this
task's refusal is at **`validate`**, so a config never reaches the draw. Check both layers agree.
