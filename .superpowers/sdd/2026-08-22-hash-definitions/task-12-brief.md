## Task 12: the records

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is how the previous
> slice shipped a Critical, and this pointer is the fix. **Ruling F (the exclude chain) changes the
> command every hashing task runs.**

**Surface: tracked records and `CLAUDE.md`. `spec-defects.md` is a live list, so a closed gap is struck;
every other tracked record is appended to, never retro-edited.**

**Files:** `docs/superpowers/spec-defects.md`, `docs/superpowers/specs/2026-08-08-implementation-spine-design.md`, `CLAUDE.md`.

- [ ] **Step 1: strike *"`code_hash` is not `.gitignore`-aware (S1 deviation, not a spec defect)"*.** The
      strike carries the ruling **and quotes and corrects the entry's own false sentence**: *"In practice
      nothing else gitignored appears under `src/**` or `templates/**`, so the two agree today"* was
      falsified by **three of the scaffold's own four patterns** — `.env`, `.venv/` and a `.pyd` all move
      the hash today, while `__pycache__/x.pyc` and a loose `.pyc` do not, and that last pair is a
      coincidence rather than a partial honouring. Note that the resolution the entry itself names —
      *"passing an `is_ignored` predicate in from the caller, which already shells to git"* — is what
      shipped, and that the predicate answers about **git's whole exclude chain**, not `.gitignore`
      alone.
- [ ] **Step 2: strike *"`parameters_hash` does not normalize to what `init` would have materialized"* —
      AS RULED, NOT AS BUILT.** Say which of the entry's own two options it took: the second (*"state in
      § How the three are computed that normalization is the caller's job and name the caller"*) is close
      to what shipped, and what actually shipped is **the sentence deleted rather than relocated**, with
      its false `diff` justification deleted beside it. **Check `hashes.covered_config`'s docstring
      against this strike before committing** — task 10 re-pointed it, and a filing's claims about the
      code go stale like any other comment.
- [ ] **Step 3: strike *"`code_hash` over zero files is indistinguishable from several distinct
      situations"* — after task 9's owner correction, which must already be in the file.** The strike
      names `E-CODE-EMPTY`, its **one** emit site, and the fact that the empty digest is still what
      `hashes.code_hash` returns.
- [ ] **Step 4: append to the nine-undocumented-codes entry.** Record that H6a documented **its own two
      new codes and took none of the nine**, and that `E-CODE-DIRTY` remains **H6b task 17's** gated
      question. Do not resolve the widening question; it is the spine owner's.
- [ ] **Step 5: file the new gap — an omitted CORE-SCHEMA key validates clean and kills a step that reads
      it.** **Owner: unassigned, with the reason** — no remaining slice (H6b, H9, H3c-3's remaining 14)
      has core's schema envelope as its surface, and closing it needs either the forbidden defaults
      structure or reading user Python. **Not *"whichever slice next touches the schema"***, the form
      this file rejects by name. **A ledger line saying "filed" is not a filing**: write the entry.
- [ ] **Step 6: do NOT touch the six-unwritten-`run.yaml`-keys entry.** Its last live row
      (`provenance.environment.os`/`.hostname`/`.hardware`) is **H6b's**; H6a writes no environment key.
      Named here so its survival is not read as an omission.
- [ ] **Step 7: append a correction to the spine design § The hardening slices — APPEND, DO NOT EDIT.**
      Three things: the H6 row's *"`parameters_hash` normalization against `parameter_spec`"* is
      **rejected**, with Decision 9's grounds; its *"the purity rule that forced both"* names a rule that
      is **not in `design-principles.md` at all** and is already broken in its own terms (`hashes.py`
      rglobs, reads bytes and carries `_SKIP_DIRS`, which is filesystem policy); and its *"Independent"*
      verdict is **too strong in one direction — H6 before H9.**
- [ ] **Step 8: the `CLAUDE.md` slice entry.** It states: the **value change** and that `code_hash` is the
      only hash that moves; the two minted errors and one warning; **zero configs unblocked**; that
      `diff` prints `code_hash DIFFERS` for identical code across the boundary and `uv.lock` is the
      carrier; and Ruling C's sharpest cost — **one record can carry two hash definitions**, its own
      under the new rule and a copied upstream's under the old, with nothing marking which is which.
      Update the order line from *"H6 Hashes and provenance, H9, then H3c-3's remaining 14"* to **H6b,
      H9, then H3c-3's remaining 14**.
- [ ] **Step 9: both consistency passes, over NAMED files.** **Mechanical**, in full, over every `.md`
      this branch touched: every relative link and `#anchor` resolves; no two headings in a file produce
      the same anchor; every table's rows match its header's column count and no row is empty; no
      trailing whitespace, tab or invisible unicode; `×` not `x`; hyphens in anchors. **Skip fenced
      blocks.** **Cross-document**, over the four documents only: the shared worked example, config
      completeness, enum comments, schema fields in prose, declared-versus-derived, versions, prevented
      mistakes. **Neither pass governs the development record**, and `spec-defects.md` is the one
      exception where a closed gap is struck rather than left.
- [ ] **Step 10: the sweeps.** After removing or renaming any string, sweep the four documents, `CLAUDE.md`
      and the feasibility analysis for what should no longer exist. **Name the file list. Never filter
      the output of a sweep whose job is to find a string — filter the file list.** **Every sweep must be
      newline-insensitive**: normalize whitespace over the whole file before matching, because a `grep
      -F` cannot match a wrapped phrase, and that is how two of one false sentence's five homes hid.
      **Prove each sweep can fail** by running it against a string known to be present, and **report what
      you swept rather than a count.**

**Delta:** 0 tests.

**What this task must NOT touch.** The § Executability entry — **task 13's**. Any `spec-defects.md` entry
this slice did not close. Any code.

**Guard-pin arms this task may edit: NONE.**

---

