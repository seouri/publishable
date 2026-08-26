## Task 17

**Corrections that bind this task: C10, C11, C20, C23, C27.** **RULING KK BINDS THIS TASK.**

**Make the safety argument fail before you write its replacement.** `_resumed_allocation`'s docstring
rules that fold partitions need no override because *"`partition_units` is a pure function of the
roster and the design digest."* Under cells it is also a function of the **cell decomposition**,
which this same function overrides one call later.

**Step 1, and it is not optional: build the mutation and watch it fail (C11).** A `Prepared` whose
`group_axes` were drawn from a roster in **reverse** resolution order, against an `allocation.json`
recorded from the forward order. Measured literals to check your fixture against: `units_hash`
forward `sha256:f3ba4914…` / reversed `sha256:ee083cab…`; `assign_seed_for({"method": "random"},
"arm", "d", ·)` → `2988051695` / `1647976561`; the realized `c` arm `[u01, u04, u05]` /
`[u02, u04, u05]`. `_resumed_allocation`'s guards compare **sets** of levels and **sets** of keys, in
both directions, and nothing about order — so the stale reading passes every guard.

**Step 2: re-derive.** Call the **same** producer `_prepare_run` calls —
`units.partition_within_cells` — on the **overridden** axes, and replace `Prepared.partitions` and
`Prepared.fold_members`. **Unconditionally**, with no `if group_axes` gate: with no axes the producer
takes the one-cell path and returns the identical partition, and a branch is one more thing to get
wrong than a proof. **Do not re-derive by hand here** — that would make this function a second
producer of fold membership, the fault its own docstring exists to prevent a third instance of.

**Step 3: replace the docstring paragraph by deleting it**, and state what is now true: the partition
is a function of the roster, the digest and the cell decomposition; the decomposition is overridden
here; therefore the partition is re-derived here, through the single producer.

**Guard-pin arm C (C23).** You are its **sole authorized editor**. The design derives that it does
**not move** — `within` is rebuilt from `group_axes`, which this function overrides consistently.
**Measure it.** If it does move, edit arm C **once**, append `holdout.within` to the expected
document, reorder nothing, and report the measurement. If it does not move, say so and leave it.

**Fixture F5, and F5 is `groups × fold`, never `groups × holdout` (C27):** the assertion is on
partition **membership**, not on sizes — both decompositions give the same sizes.

**Mutations:** MU-9 (the pre-slice code: no re-derivation → F5 fails), MU-10 (add a `group_axes`
gate → guard-pin arm D plus a no-axis resume asserting byte-identical partitions fails).

**Must not touch:** `Prepared`'s other fields (C20); `arm_members`' second call; the set-equality
guards.

---

# Batch E — the thin cell, the interactions, the filings

