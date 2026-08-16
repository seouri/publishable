## Task 1: Documents, part A — the ten refusal surfaces

**Files:** Modify `docs/reference.md`, `docs/experimental-designs.md`

Nothing below may land a check describing a rule no document states, and **the retirement in task 14 removes a code named at ten independent prose sites**. Find them now, while they are still true, so task 14 is a deletion rather than an archaeology exercise.

- [ ] **Step 1: Enumerate, then verify the enumeration can fail.** `grep -n 'E-DATA-ASSIGN-DRAWN' docs/*.md` — the scoping measured 9 in `reference.md` and 1 in `experimental-designs.md`. Run the same grep against a code you know is present and absent (`E-DATA-ASSIGN-LEVELS`, `E-DATA-NOTHING`) and show both outputs. Record the site list in your report; task 14 works from it.
- [ ] **Step 2: § Validation's *Assignment method isn't drawn* row.** It says `random`/`blocked` are "specified, not built in this build; only `by_attribute` executes". Leave it — task 14 removes it — but check its wording still matches `DRAWN_ASSIGN_METHODS` exactly.
- [ ] **Step 3: The four rows this slice implements.** *Ratio names levels*, *Block size fills the arms*, *Stratification is forward-only*, *Allocation strata exist*. Read each and write down, in your report, the exact fault each describes. Tasks 5, 10, 12 and 13 implement them and must not drift from these words.
- [ ] **Step 4: Commit.**

```bash
git commit -am "docs: name the drawing surfaces the code is about to implement"
```

---

