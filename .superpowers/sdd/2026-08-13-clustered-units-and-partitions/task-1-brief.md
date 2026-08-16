## Task 1: The documents first

**Files:** Modify `docs/reference.md`

Nothing in this slice may land a check describing a rule no document states. Three document changes come first, and each is a rule the code below implements rather than a description of code that exists.

- [ ] **Step 1: The owed *Cluster attribute exists* row.** § Validation has *"Weight attribute exists"* — `data.units.weight_by` names something that is not a unit attribute — and **no cluster equivalent**, though `cluster_by` names an attribute the same way. Add the row, phrased as its weight sibling is. Read that sibling first; do not invent a phrasing.

- [ ] **Step 2: `W-DATA-CLUSTER-UNDECLARED`.** § Clustered units already promises it — *"`validate` warns when an attribute looks like a cluster identifier (few distinct values, many units each) but hasn't been declared as one"* — and § Validation carries the row *"Clustering looks undeclared"*. **The identifier does not exist in any file.** Add its row to § Warnings core reports, stating the trigger the way `W-DATA-WEIGHT-UNDECLARED`'s row does.

**The trigger is structural here, and that is worth stating.** H3a's weight warning needed a *name* test (`weight`/`_prob`/`probability`) because `age`, `dose` and `latency` are shape-identical to a sampling weight. A cluster is not: "few distinct values, many units each" is a genuine structural discriminator, which is why § Weighted samples says the weight case is *"not by the same means"*. **Do not add a name test here** — say in the row what the structural trigger is.

- [ ] **Step 3: The `× measurements` rule.** § Clustered units gains the sentence that a cluster must not vary within a unit's measurement rows, mirroring the one § Weighted samples carries for weights. State the consequence, because it is worse than the weight case: a mis-collapsed cluster decides **which side of a train/test split** a unit lands on, which is the leak the section calls "the difference between a valid evaluation and a leaky one".

- [ ] **Step 4: Mechanical pass over the edited rows, then commit.**

```bash
git commit -am "docs: name the cluster checks the code is about to implement"
```

---

