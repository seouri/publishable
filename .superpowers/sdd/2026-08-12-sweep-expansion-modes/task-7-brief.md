## Task 7: Retire `E-SWEEP-BASELINE-PARTIAL` and re-read the warning it stranded

**Files:**
- Modify: `src/publishable/validate.py`, `docs/reference.md`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: task 6's per-cell expansion
- Produces: the refusal gone; `W-SWEEP-BASELINE-CONFOUNDED`'s row true again

`E-SWEEP-BASELINE-PARTIAL`'s own message says the design is *"specified but not implemented in this build"* and *"Per-cell baselines will be honored in a later slice"*. This is that slice.

- [ ] **Step 1: Remove the refusal and its message.** Read `_check_unimplemented` first — the surrounding comment explains the `unfixed` computation, and a stale comment left behind is the defect this project keeps paying for.
- [ ] **Step 2: Test that the previously-refused config now validates and expands.** Use the exact shape the old message described: a baseline leaving a grid axis free.
- [ ] **Step 3: Re-read `W-SWEEP-BASELINE-CONFOUNDED`'s row.** H1's review ruled *"do not touch row 271"* explicitly because H2 would make its remedy expressible. Its remedy — leave one axis unfixed — was a config `E-SWEEP-BASELINE-PARTIAL` refused; now it is not. Read the row and the warning's emit site, confirm the remedy is now reachable, and remove whatever clause said it was not. **Do not weaken the warning itself** — it still fires when a fully-fixed baseline confounds contrasts.
- [ ] **Step 4: Remove `E-SWEEP-BASELINE-PARTIAL`'s registry row** from § Validation's error table, taking it from 60 rows to 59, and confirm no other document text references it:

```bash
grep -rn "E-SWEEP-BASELINE-PARTIAL" src/ tests/ docs/ README.md
```

- [ ] **Step 5: Commit.**

---

