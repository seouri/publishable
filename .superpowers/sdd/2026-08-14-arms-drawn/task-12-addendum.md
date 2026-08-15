# Task 12 — controller additions

**Carried from task 7's review — read before writing:** `validate._check_assign` still calls
`units.arms_of` **directly** (it reports `E-DATA-ASSIGN-LEVELS` and discards the partition). When this
task makes `validate` resolve stratum membership, it must call **`assignment_for`**, not `arms_of`, or
the second membership producer that seam exists to prevent reappears one level up.

Carry a latent asymmetry with it: `validate._declared_levels` returns the **first** `sweep.groups` entry
matching `by`, while `cli._resolved_group_axes` keeps the **last**. Unreachable today because a duplicate
`by` is `E-SWEEP-PATH-DUPLICATE`, but it is the second place a level list could diverge once both sides
resolve plans.

**Task 8 already refuses a non-empty `stratify_by` under `random`** — a raise inside `assignment_for`,
naming this task. **This task replaces that raise with real stratified drawing.** Find it; do not leave
it beside a working implementation.

**`E-DATA-ASSIGN-STRATIFY-UNKNOWN` was minted by task 3** with a registry row already written, narrowed
to **existence only** — a target naming an axis declared *after* this one is task 13's fault, not this
one's. Do not widen it.

**Reuse `units.stratum_varies_within_cluster`** — it exists, `_check_fold_stratify_by` already uses it,
and `partition_units`' docstring says its per-stratum composition "is sound only while
`stratum_varies_within_cluster` refuses the pair it refuses". Do not reimplement the constancy test.

**Step 5's exclusion check is not optional.** `W-DATA-CLUSTER-UNDECLARED`'s row excludes an attribute
"a `sweep.groups` axis names or an `assign.from` reads… any `stratify_by`". **Under a draw there is no
`assign.from`**, so check the exclusion reaches `assign.<axis>.stratify_by` and add a test either way.

**Step 6 records rather than fixes:** `assign.<axis>.stratify_by` is **not** in
`units.CONSTANT_COLUMN_RULES`, so a stratum column varying across a unit's measurement rows collapses
silently — unlike `assign.<axis>.from`, which the previous slice wired in. Record it in `reference.md`,
**not** in the gitignored `spec-defects.md`.

**The fixture:** three strata of different sizes (A6/B4/C2 over 12 units), so a draw balancing only
overall leaves at least one stratum lopsided. Assert each stratum's per-arm counts exactly. **Five
mutations have survived a full suite across this project's last three slices, every one because a
fixture's numbers agreed with the bug** — say why yours discriminate.
