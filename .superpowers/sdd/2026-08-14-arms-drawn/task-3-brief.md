## Task 3: Documents, part C — which row owns the stratum fault

**Files:** Modify `docs/reference.md`

**Two § Validation rows overlap on `assign.stratify_by`** and the overlap is a real ambiguity, not a wording nit. *Stratification attribute exists* contemplates only a unit attribute. *Allocation strata exist* admits a name that is "neither a unit attribute **nor a group axis**" — and **an axis name is exactly what forward-only stratification requires**.

- [ ] **Step 1: Write the ruling into the rows.** *Allocation strata exist* owns `assign.<axis>.stratify_by`, including the axis-name case; *Stratification attribute exists* keeps `fold` and `holdout`. Say so in both rows, naming what the other one covers rather than where it sits.
- [ ] **Step 2: Register the new code.** `E-REPL-FOLD-STRATIFY-UNKNOWN`'s registry row already promises the shared row covers `holdout.stratify_by` and `assign.<axis>.stratify_by`, "each reported by its own code once its block is built". Mint `E-DATA-ASSIGN-STRATIFY-UNKNOWN` and give it a registry row in sort order. **Check every row your insertion moves.**
- [ ] **Step 3: Commit.**

```bash
git commit -am "docs: allocation strata exist owns the assign stratum, and its code is registered"
```

---

