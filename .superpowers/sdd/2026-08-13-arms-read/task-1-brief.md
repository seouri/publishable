## Task 1: The documents first

**Files:** Modify `docs/reference.md`

Nothing below may land a check describing a rule no document states.

- [ ] **Step 1: The two rows to write from nothing.** § Validation has *Cluster is constant within a unit* and *Weight is constant within a unit* (H3b and H3a). It has **no `assign.<axis>.from` equivalent**, and **nothing checks that `assign.<axis>.method` is present or in-enum**. Add both rows, phrased as their siblings are. Read the siblings first.

- [ ] **Step 2: The two rows this slice breaks.** *Grid size sane* computes the budget as `len(expand(doc)) × repeat_total` and `expand` ignores `groups`, so the count will be wrong the moment `groups` expands. *Baseline leaves contrasts confounded* uses `arm: control` as **its own example**, which is a group axis. State what each means once a group axis is real.

- [ ] **Step 3: The `assign.seed` digest inconsistency.** § What `auto` derives from **excludes** `assign.seed`; `design_digest` canonicalises `data.units` wholesale and therefore includes it. **Decide which is right and say so** — if the document is right the code changes in task 16, and if the code is right this row does. Do not fix the code here.

- [ ] **Step 4: Mechanical pass over the edited rows, then commit.**

```bash
git commit -am "docs: name the arm checks the code is about to implement"
```

---

