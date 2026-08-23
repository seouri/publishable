## Task 9: the zero-file blast radius, and the stale owner corrected before it is struck

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is how the previous
> slice shipped a Critical, and this pointer is the fix. **Ruling F (the exclude chain) changes the
> command every hashing task runs.**

**Surface: reading and re-running, plus one `spec-defects.md` correction.**

**Files:** `docs/superpowers/spec-defects.md`.

- [ ] **Step 1: re-run guard-pin arm E and report it.** `code_hash(tmp_path / "nonexistent_empty_repo",
      None)` still returns `sha256:e3b0c442…`; both negative controls still pass. **Report the `git diff`
      line count** across `tests/test_hashes.py` for the whole branch to this point and confirm every
      changed line in those two tests is a call rather than an assert.
- [ ] **Step 2: correct the stale owner line BEFORE the entry is struck, so the correction survives in
      the record.** The `code_hash` over zero files entry routes its diagnostic to *"H1 Validation's
      registry once H6 says what it should say"* — **and H1 has shipped.** That is the closed-slice-owner
      pattern this file rejects by name at its own `RE-OWNED 2026-08-19` entry. Append the correction
      naming what it replaces; **do not retro-edit the original text.** The strike itself is **task
      12's**, and it will read the corrected owner rather than the stale one.
- [ ] **Step 3: report what you grepped, not a count.** Before writing any claim about what other tests
      assert about the empty digest, grep for it across `tests/` by name and report the file list and the
      hits.

**Delta:** 0 tests.

**What this task must NOT touch.** The strike itself. Any other `spec-defects.md` entry. Any code.

**Guard-pin arms this task may edit: NONE** — arm E is re-run, not edited.

---

