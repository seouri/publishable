## Task 8: The comparison count under multiple baselines

**Files:**
- Modify: `src/publishable/cli.py` or `src/publishable/contrasts.py` — whichever resolves comparisons
- Test: `tests/test_contrasts.py`, `tests/test_cli.py`

**Interfaces:**
- Consumes: task 6's per-cell baselines
- Produces: `vs_baseline` targeting each condition's **own cell's** baseline, and a correction family that counts comparisons rather than conditions

§ Expansion modes: *"Baseline conditions are references rather than comparisons, so they never count as one: six conditions under two per-arm baselines are **four** comparisons in the correction family, not five."*

**This is the rule with reach outside the slice.** It changes `family_size`, which changes every corrected interval in a multi-baseline run. H4 owns the correction family, but H2 makes multi-baseline runs possible, so H2 must not leave this for H4 to discover.

- [ ] **Step 1: Read how comparisons are resolved today.** `resolve_contrasts` builds the family; `_differing_axes` decides `confounded`. Read both, and § Expansion modes' second row: *"Each `vs_baseline` targets its own cell's baseline: `sex=f__arm=treatment` compares against `sex=f__arm=control`."*
- [ ] **Step 2: Write the failing test with the document's own arithmetic** — six conditions under two per-cell baselines, asserting **four** comparisons and a `family_size` of four, not five or six.
- [ ] **Step 3: Implement, run.**
- [ ] **Step 4: Mutation-test.** Count baselines as comparisons (the test must fail); target every condition at the first baseline (a per-cell targeting test must fail).
- [ ] **Step 5: Commit.**

---

