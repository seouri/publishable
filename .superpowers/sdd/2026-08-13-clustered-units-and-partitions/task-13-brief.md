## Task 13: The consistency passes and the exit criterion

**Files:** whichever of the four documents the passes find defects in.

- [ ] **Step 1: Both retirements, both directions** — absent from `src/**/*.py` **and** every tracked `*.md`. Use `--include='*.py'`; stale bytecode has produced a false positive on this exact check. State each command and prove it can fail.
- [ ] **Step 2: The `NOT BUILT` count reads seven**, and exactly `cluster_by` and the fold `stratify_by` left. A number in prose that no mechanical check catches.
- [ ] **Step 3: Registry integrity, both directions** — and remember the codeless § Validation **checks** table carries rows no identifier grep sees.
- [ ] **Step 4: H3b's rows by title**, never by number: *Clustering looks undeclared*, *Folds fit inside the clusters*, *Fold strata survive clustering*, the `fold.` half of *Stratification attribute exists*, the new *Cluster attribute exists*, and the corrected *Leave-one-out is affordable*.
- [ ] **Step 5: `partition_units`' new contract is stated where H3c and H3d will read it** — they both build on it, and H3c rewrites it next.
- [ ] **Step 6: The worked example did not move.** Verify with a **real temporary commit** — a working-tree edit is invisible to a two-dot diff, which is how this check silently passes.
- [ ] **Step 7: The four prevented mistakes, one at a time.** `experimental-designs.md` § Mistakes core prevents carries **four** cluster rows, and `CLAUDE.md` requires each to be **structurally impossible, not merely discouraged**. Check each against what this slice actually built, and say which task provides it:

| Row | Must be impossible via | Owner |
|---|---|---|
| **Ignored clustering** | the cluster-robust intervals **and** the undeclared warning | tasks 9, 9, 2 |
| **A cluster split across train and test** | the partition rewrite **and** the constancy check — the partition closes the fold route, the check closes the *input-file* route, and **both are needed**: a cluster mis-collapsed at resolution is already in the wrong place before any partition runs | tasks 4, 3 |
| **Resampling clustered rows as if independent** | **Corrected after task 11.** Task 10's `percentile_over_units_clustered` closes the `statistics.resample` path, which H4 still refuses and which has **no caller at all** today. The **live** path is `percentile_of_derived`, still unit-level — so this row closes only by **task 12's refusal** of `cluster_by` beside a derived metric, not by task 10's construction. Check the refusal, not the function | task 12 (task 10 for the gated path) |
| **A permutation that shuffles away the matching** | `null_test`, refused by `E-STATS-NULLTEST-UNSUPPORTED` — **out of scope, and still refused**. Confirm the refusal is live rather than assuming it | H4 |

The second row is the one to check hardest: it is the only one where two different tasks each close half of it, and closing one half looks complete from inside that task.

- [ ] **Step 8: The mechanical pass, then the cross-document pass** over `CLAUDE.md`'s remaining drift classes — **declared vs. derived** (`clusters` is derived; no passage may show it as a settable input), **config completeness**, and **enum comments**.
- [ ] **Step 9: Fix what the passes find; commit only if something changed.** A clean result is a real result — do not create an empty commit.

---

## Sequencing

1 → 13 in order. Task 1 states the rules everything below implements. Tasks 2–3 build the authority and the constancy check the partitioner depends on. Task 4 is the load-bearing rewrite; 5 and 6 depend on it. Tasks 7–10 are the reporting and statistics, which need cluster membership resolved. Task 11 retires only after everything it was masking is handled — the ordering H3a proved, where a retirement ahead of its preconditions ships a wrong number. Task 12 runs last, over a settled tree.
