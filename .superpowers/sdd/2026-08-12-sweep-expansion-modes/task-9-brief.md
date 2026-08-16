## Task 9: Consistency passes and the slice's exit criterion

**Files:**
- Modify: whichever of the four documents the passes find defects in
- Read: all four documents, `CLAUDE.md`

**Interfaces:**
- Consumes: every task above
- Produces: the slice's exit criterion

- [ ] **Step 1: Confirm `groups` is still refused.** The slice's most consequential constraint. A config declaring `groups` must still report `E-SWEEP-GROUPS-UNSUPPORTED`, and rows 219 and 257 must still be unimplemented. **If any task made a groups axis expand, that is a blocking defect**, not a minor.

- [ ] **Step 2: Confirm the worked example did not move.**

```bash
git diff main..HEAD -- README.md docs/ | grep "^-" | \
  grep -E "0\.581|0\.607|0\.412|0\.026|−0\.007|0\.059|−0\.169|0\.014|228|240|8e21|1a2b|3d8a|6b1f|2f5c8d0"
```
Expected: **no output**. Then confirm `cohort-pilot` still expands to exactly 3 conditions with one baseline, by running its expansion directly.

- [ ] **Step 3: Registry integrity.** Three `-UNSUPPORTED` codes retired and one refusal removed, so counts moved. Verify both directions: every code `src/` emits is documented or is a surviving `-UNSUPPORTED`; every documented code is still emitted.

```bash
comm -23 <(grep -rhoE "\b[EW]-[A-Z][A-Z0-9]*(-[A-Z0-9]+)*\b" src/ | grep -v __pycache__ | sort -u) \
         <(grep -hoE "\b[EW]-[A-Z][A-Z0-9]*(-[A-Z0-9]+)*\b" README.md docs/*.md | sort -u)
```
Expected: only surviving `-UNSUPPORTED` codes and `E-GIT-NO-REPO`. **State the method, not just the conclusion** — this project's absence claims have been wrong six times, always when established by a grep that could not fail. Include a self-test proving each check can fail.

- [ ] **Step 4: The mechanical pass.** Throwaway checks, not committed tooling: anchors and links resolve, no duplicate anchors, table rows match their headers, no trailing whitespace or tabs or invisible unicode, `×` not `x`. Skip fenced code blocks. Three anchors are known false positives of simplified sluggers — `secrets--credentials`, `naming-conventions--repeat-defaults`, the `executions.jsonl` heading — do not "fix" them.

- [ ] **Step 5: The cross-document pass.** `CLAUDE.md`'s seven drift classes. The ones this slice most plausibly disturbed: **prevented mistakes** (`experimental-designs.md` § Mistakes core prevents must stay structurally impossible — three modes just became possible, so confirm none of them re-opened a prevented mistake), **enum comments** (`method: sobol | latin_hypercube | random` must list what the code accepts), and **schema fields in prose**.

- [ ] **Step 6: Fix what the passes find; commit only if something changed.** A clean result is a real result — do not create an empty commit.

---

## Sequencing

1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9, in order. Task 1 restructures what every later task extends; 6 needs 4's `ablate` to test the composition; 7 needs 6; 8 needs 6's per-cell baselines. Task 9 last, over a settled tree.

Tasks 2–5 are each small enough to land in one commit; task 6 is the largest and the only one that moves artifact paths.
