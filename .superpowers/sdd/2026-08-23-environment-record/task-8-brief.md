## Task 8: `spec-defects.md` — one entry closed, the rest filed with owners that are facts

> **Bindings that reach this task:** **Ruling N**'s filing half, restated below, and design Decision
> 14. **A ledger line saying "filed" is not a filing** — a gap recorded as *"registered against
> \<owner\>"* once existed only in a ledger while the defects file had no such entry. **An entry naming
> its owner as *"whichever slice does X"* points at a closed slice once X lands.**

**RULING N's filing half, restated:** H6b takes `E-GIT-NO-REPO` and `E-GIT-NO-COMMIT`. **The others
belong to their own surfaces; file each with an owner that is a fact with a reason**, never *"whichever
slice next touches X"*.

**THE COUNT IS FIVE, NOT SIX, AND YOU MUST NOT CARRY EITHER NUMBER WITHOUT RE-DERIVING IT.** The ruling
as it arrived said *"the other six"*. That subtracted `E-CODE-DIRTY` from the nine and **not**
`E-EXPERIMENT-UNKNOWN`, which H8c task 16 documented (`c794029`, recorded in the entry's own appended
note). Derived: the nine are `E-GIT-NO-REPO`, `E-GIT-NO-COMMIT`, `E-CODE-DIRTY`, `E-INPUT-CHANGED`,
`E-RUN-LOCKED`, `E-RUN-ID-EXHAUSTED`, `E-PROJECT-EXISTS`, `E-EXPERIMENT-EXISTS`,
`E-EXPERIMENT-UNKNOWN`; minus the two already documented leaves **seven**; minus H6b's two leaves
**five**. **`E-STEP-EXISTS` is NOT one of the nine** — the entry names it as *"the one sibling that is
documented, and only partially"* — so it is recorded as a separate observation and never counted in.
**Re-derive this yourself from the entry's table before writing the number**, and report the
derivation; a count carried forward without re-deriving what it counted is the failure this repo has
made twice, and this plan's own first draft made it a third time.

**Steps**

- [ ] **Close the six-unwritten-keys entry** — *"Six `provenance` and `results` keys in the `run.yaml`
      example that no code writes"* — **only after checking every row of its own table.** Its
      `provenance.allocation`/`.allocation_hash` row was struck at H3c1 task 14, `provenance.upstream`
      at H8a task 7, and `provenance.environment.os`/`.hostname`/`.hardware` is closed by task 3.
      **Verify each of the two prior strikes against the code at HEAD** rather than trusting the
      amendments; a filing's claims about the code go stale like any other comment. The entry's own
      *"Also recorded, and deliberately not fixed"* key-order note about `provenance`'s construction
      order **stays** — H6b added no top-level key and reordered nothing — and say why it stays, so a
      later reader does not read the closure as covering it. Record that `environment` is now the one
      sub-block whose key order matches the example exactly, and that this was matching a document
      rather than reordering an example.
- [ ] **Append to the nine-undocumented-codes entry**, correcting the count: H6a took one
      (`E-CODE-DIRTY`), H8c had already documented `E-EXPERIMENT-UNKNOWN`, and **H6b takes two**
      (`E-GIT-NO-REPO`, `E-GIT-NO-COMMIT`). **Verify each claim by reading `docs/reference.md`, not by
      reading the entry's own amendments** — H6a's batch 6 found that both its brief and its design
      said H6a *"took none"* when it had taken one, found by `git log -S` rather than by reading. State
      the remaining count and enumerate what remains: `E-INPUT-CHANGED`, `E-RUN-LOCKED`,
      `E-RUN-ID-EXHAUSTED`, `E-PROJECT-EXISTS` and `E-EXPERIMENT-EXISTS` — **five, derived above and
      not carried**, and the heading's count goes from nine to five. **Owner: unassigned, with the
      reason** — no remaining chartered slice has `run_identity.py`, the manifest path or `generators/`
      as its surface: H9 is `reproduce`/`dry-run`/`draft`/`resume`/`demo`/`docs`, H3c-3's remaining 14
      are folds and holdouts inside cells. **And re-verify the entry's own "a mention inside another
      code's row is not documentation of that code" states** for each of the five, by sweeping the four
      documents **named individually** — that distinction is the entry's heading, and it went stale for
      one row before.
- [ ] **File: `validate_config`'s bare `except ContractError` around `find_repo_root` is wider than its
      comment's claim** (*"No repo at all"*). It would swallow any future coded fault from the walk-up.
      Reproduce: read the two catch sites and note that `_check_data`'s neighbour catches **by code**
      while this one does not. Narrowing it is a behaviour change to `validate`, so it is not H6b's.
      **Owner: unassigned, with the reason** — no remaining chartered slice has `validate`'s
      template-discovery path as its surface.
- [ ] **Record `E-STEP-EXISTS` as a separate observation, NOT as one of the nine.** It has a sentence
      in § Exit codes and diagnostics and no § Errors row, and the entry already calls it *"the one
      sibling that is documented, and only partially."* Counting it in is what turned five into six in
      this plan's own first draft; label it as what it is, beside the five.
- [ ] **Record as a stated non-gap, not as a filing:** `diff` gains no row for `os`/`hardware`
      (Decision 14). § What `diff` compares says *five rows* and the five-row shape is documented and
      deliberate, so no owner is invented for it. Say this **once**, in the six-unwritten-keys closure,
      so a later reader does not file it as a gap.
- [ ] **Every sweep names its files, filters the file list rather than the output, is
      newline-insensitive, and is proven able to fail** against a control string known to be present.
      This is a rule about the checker as much as the claim: H6a's batch 6 disclosed that its own
      mechanical checker produced eight false positives on first run.
- [ ] Four gates. **Delta: 0 tests.** Commit.

**What this task must NOT touch.** The two entries task 6 amends — the root-`.gitignore` one and the
`validate`-seat one. Any tracked record other than `spec-defects.md`, which is the one live list; a
spec or a scoping is **appended** to, never retro-edited. § Executability (task 11's). `src/`, `tests/`.

---

