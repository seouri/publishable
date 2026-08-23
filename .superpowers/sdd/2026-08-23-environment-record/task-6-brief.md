## Task 6: Ruling P and Decision 12, decided together

> **Bindings that reach this task:** **Ruling P** and design Decision 12, both restated below. The
> `spec-defects.md` entry itself asks for the two to be decided together, which is why they are one
> task.

**RULING P, restated here in full:** **no new `W-` code** for § Templates' *"goes dirty at `validate`"*,
and **the sentence STAYS**. H6a's design appended a correction establishing that the sentence is **true
as written**: discovery imports every file under `templates/` to find its registration, which writes
`templates/__pycache__/`, so a repo whose `.gitignore` omits that line **becomes dirty as a result of
validating**. Grounds for adding nothing: **a `W-` code is a registry seat**, the condition is already
caught at `run` by `E-CODE-DIRTY`, and the scaffold's own `.gitignore` excludes `__pycache__` so only a
hand-assembled repo reaches it. **This task is a confirmation, not a change** — and its job is to check
the sentence against the code **as H6a left it**, since Ruling F changed what the surrounding paragraph
claims.

**What Ruling F changed, and it is the likely finding.** § Templates' neighbouring clause reads
`code_hash` *"skips `__pycache__` directories and compiled `.pyc`/`.pyo` files unconditionally,
wherever in the hashed trees they sit — it reads the working tree rather than git, so no ignore file
could have done that for it."* **The second half is now false: the hash asks git.** The fixed skip set
is still applied unconditionally, which is what keeps the first half true. **So the paragraph the
scoping did not name is where the defect probably is.** **Prefer deleting a false clause to rewriting
it.**

**Decision 12, restated in full:** `spec-defects.md` carries *"OPEN — an uncommitted root `.gitignore`
decides what `code_hash` covers, and the dirty gate cannot see it — **Owner: H6b**"*, filed 2026-08-23
by H6a's whole-branch fix round. **H6b DECLINES it, in writing, and re-owns it unassigned with the
reason.** Grounds: closing it means the dirty gate reading a file **outside** the two hashed trees —
a **behaviour change to a shipped command**, where every uncommitted root file becomes a candidate the
gate must rule on and a repo with an ordinary uncommitted `README.md` would stop running. H6b is
chartered **additive**; this is the one item in its inbox that cannot be done additively. The entry's
own owner paragraph asks a successor to decide it **together with** the `validate` tree-state ruling,
and Ruling P answers that one with *no new seat*; answering this one with *widen the gate* would leave
the two decided in opposite directions in one slice, on no argument. **A decline is recorded as an
amendment, never as a strike** — the gap is real and reproduces, and the entry's own recipe stands.

**Steps**

- [ ] **Measure, do not read.** Build a hand-assembled repo whose `.gitignore` omits `__pycache__`,
      with a `templates/` holding a real registering template. Run `git status --porcelain`, then
      `publishable validate`, then `git status --porcelain` again. **Report all three outputs.** That
      is the measurement Ruling P's confirmation rests on, and it is the difference between an
      assertion and a fact.
- [ ] Re-read **the whole § Templates paragraph** against the code at HEAD, not only the sentence the
      scoping named. Report, clause by clause, which are true and which are false. The
      *"no ignore file could have done that for it"* clause is expected to be **false**; report what
      you find, and if it is false, **delete the false clause** rather than rewriting the sentence
      around it. `grep -rn "excludesFile" src/publishable/hashes.py src/publishable/provenance.py` is
      the check.
- [ ] **Add nothing to any registry.** No `W-` code, no § Warnings row, no § Validation row. If your
      measurement contradicts Ruling P — if `validate` genuinely does not leave the tree dirty — **stop
      and report it**; that is a controller question, not a task's licence to mint a seat.
- [ ] Amend the OPEN root-`.gitignore` entry in `spec-defects.md`: H6b considered it, **declined** it
      on the additive-charter ground above, decided it beside Ruling P as the entry asked, and re-owns
      it **unassigned, with the reason** — no remaining chartered slice has `E-CODE-DIRTY`'s pathspec
      as its surface (H9 is `reproduce`/`dry-run`/`draft`/`resume`/`demo`/`docs`; H3c-3's remaining 14
      are folds and holdouts inside cells) — and name the closer's own cost accounting: what an
      uncommitted root file that is **not** a `.gitignore` should do at the gate. **Amend, never
      strike.** A struck entry reads as closed.
- [ ] Amend the entry that names *"H6b task 18's ruling"* about whether `validate` gains a tree-state
      seat, recording Ruling P's answer: **no seat**, with the three grounds.
- [ ] Mechanical pass on every `*.md` you edited.
- [ ] Four gates. **Delta: 0 tests.** Commit.

**What this task must NOT touch.** `src/`. `tests/`. Any registry — no new code of any kind.
§ How the three are computed, which H6a wrote and which is not this task's to re-litigate. The other
`spec-defects.md` entries (task 8's).

---

