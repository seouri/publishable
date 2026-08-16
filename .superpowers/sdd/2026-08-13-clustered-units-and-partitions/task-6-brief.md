## Task 6: `stratify_by`, and strata that survive clustering

**Files:** Modify `src/publishable/replication.py`, `src/publishable/units.py`, `src/publishable/validate.py`; Test `tests/test_units.py`, `tests/test_validate.py`

Two rows. *"Stratification attribute exists"* — shared three ways, and **only its `fold.` half is yours**; `assign.*.` is H3c's and `holdout.` is H3d's, so scope the check to a `fold` level and say so. And *"Fold strata survive clustering"*: `{kind: fold, stratify_by: label}` with `cluster_by: animal_id` where `label` varies within an animal — **a stratum cannot be balanced across a split that cannot divide the cluster carrying both values.**

**The ordering trap the scoping found.** `_fold_k` raises `E-REPL-FOLD-STRATIFY-UNSUPPORTED` **before** `k` is read, so retiring it changes what other configs report: `{k: 1, stratify_by: x}` becomes `E-REPL-FOLD-K` and `{k: 99, …}` becomes `E-REPL-FOLD-K-TOO-LARGE`. **Pin both of those before touching the raise**, so the change in reported code is visible rather than discovered.

**`_fold_k` has no roster**, so the survives-clustering check cannot live there. It needs cluster membership and the stratum attribute together — put it where both are in hand, and say where in the report.

- [ ] **Step 1–6:** Failing tests (each row's identifier, plus the two ordering pins and a control where the stratum *is* constant within every cluster); implement; mutate each check separately; commit.

---

