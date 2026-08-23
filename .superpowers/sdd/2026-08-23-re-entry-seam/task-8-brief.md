## Task 8

**Design Decision 11 binds this task: reuse `runner._arm_keys` and `runner._handed_keys`; do NOT
extract the narrowing out of `execute_plan`.** That would be a second behaviour-preserving extraction
on a shipped path, in **phase 7**, outside the phases this slice is chartered to move, and it would
need its own pin arm and its own disclosure line. What prevents drift here is an **agreement pin**, not
a shared function.

**Before you write the narrowing, read `execute_plan`'s own** — the four-way `execution.scope` dispatch
around lines 685–735 — and restate it. *Before writing a walk, a guard or a containment, grep for one
that already exists*: `_arm_keys` and `_handed_keys` are already extracted, single-call-site functions,
and they are what you call.

**The narrowing, as measured at `af78816`**, in order:

1. `_arm_keys(condition_index, keys, arm_members)` narrows when a group axis is declared **and** the
   execution has a condition index.
2. Then: under a declared **fold** — `run` and `condition` scope receive **`None`**, `repeat` scope
   receives `_handed_keys(repeat_label, keys, fold_members)`, `summary` receives the whole
   (arm-narrowed) roster. Under a declared **holdout** — every scope receives the test partition.
   Otherwise — every scope receives the arm-narrowed roster.
3. **An execution handed `None` contributes zero**, and the printed line says so, because a fold's
   `run`- and condition-scoped steps see no units at all and a reader computing by hand would be
   short.

**Fixtures S and T — the agreement pin.** One **fold** config and one **group-axis** config in which
`dry-run`'s printed `unit-executions` must **equal the summed `len(io.units)` a real `run` of the same
config actually hands out**. The expected value is **summed from the real run** — a step records
`len(io.units)` per execution — never computed as `roster / k × executions`, which is arithmetic the
code could be wrong about in the same way. **S and T must give different answers**; if they coincide,
resize them, because two elements only ever distinguish two readings.

**Mutations.** (a) Drop `_arm_keys` → T must fail (its arms are proper subsets). (b) Drop the
`None`-contributes-zero branch and count the whole roster at `run`/`condition` scope under a fold → S
must fail (its fold has k > 1 and a `run`-scoped step). **Check both branches can differ before you
believe either mutation** — a mutation is a claim too.

**Must not touch:** `runner.py` at all. If `execute_plan`'s narrowing is wrong, that is a finding.

---

