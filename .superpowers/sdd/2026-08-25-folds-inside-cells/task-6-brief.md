## Task 6

> **AMENDED 2026-08-25 by the controller, from batch A's concern 2.** **C25 is undischargeable at tasks 2
> and 3 — measured**: adding the imports with no caller fails `ruff` (F401 + I001). **The imports land with
> their callers, here and at task 8.** Neither brief said so, and both experiments were edited back and
> diffed identical, so nothing is owed but the landing.

**Corrections that bind this task: C4, C5, C25.** **Ruling LL binds this task and is the reason it
exists.**

**Thread the cell-aware basis into the two callers that ask the fold's question, and leave the third
alone.** In `validate_config`, after `_resolved_cells`, the `basis` local becomes
`cell_fold_basis(roster, usable_cluster, cells)` when `cells` is not `None` and non-trivial, and
`fold_basis(roster, usable_cluster)` otherwise — inside the **same** `try`/`except ContractError`
that already guards it. That one local feeds `_check_replication` **and** `_check_sweep` (C5); it is
one local and stays one local. In `_prepare_run` the same substitution, on `cells`.

**`_check_resample`'s `limits.min_clusters` call site keeps `fold_basis` unchanged.** **Delete** the
sentence *"Not threaded through `basis` in this slice; doing so is a cheap follow-up, not a
correctness gap today."* — after this slice threading it would be a defect, not a follow-up. Add one
clause to the paragraph above it naming cells as the third reason the two derivations are not the
same. **Delete rather than rewrite** wherever the choice exists.

**Mutation:** replace the `min_clusters` site's `fold_basis` with `cell_fold_basis` — a test must
fail, namely a `between` design with a thin cell and a `resample` whose `min_clusters` is satisfied
by the whole roster. Write that test in this task; without it the mutation is silent and the silence
would be evidence about the tests, not the code.

**Must not touch:** `fold_basis`, `_check_resample`'s holdout narrowing, `_fold_k`.

