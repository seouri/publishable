## Task 6: the hash and the gate agree, and the duplicated `__pycache__` pin is replaced

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is how the previous
> slice shipped a Critical, and this pointer is the fix. **Ruling F (the exclude chain) changes the
> command every hashing task runs.**

**Surface: direct calls to `hashes.hashed_files` and `provenance.git_provenance` over a real repository.**

**Files:** `tests/test_hashes.py`.

**Decision 13, and the false sentence it exists to stop.** The scoping says the hash and the dirty gate
*"would share one file list."* **They do not, and writing that into a docstring would be a false claim.**
They share `HASHED_TREES` — one constant, one pathspec — and ask git **two different questions**:
`git status --porcelain -- src templates` (has anything moved?) and `git check-ignore` (is this path
excluded?). `status` never lists a clean tracked file, so it cannot produce the hash's file list. **What
this task pins is behavioural agreement, not a shared list.**

- [ ] **Step 1: Fixture J — one test, two assertions, on one tree.** Fixture B's tree: assert
      `git_provenance(...).code_dirty is False` **and** that `src/pkg/.env` is absent from
      `hashed_files`' output. Both halves in one place so neither can move alone. The docstring states
      the four states and that they agree — untracked-not-excluded is dirty and hashed, tracked-modified
      is dirty and hashed, tracked-clean is not dirty and hashed, **excluded-but-present is neither** —
      and states that **today** the last one is *not dirty and hashed*, which is the disagreement this
      slice closed.
- [ ] **Step 2: replace the duplicated pin.** `test_code_hash_ignores_pycache` and
      `test_code_hash_still_skips_a_genuine_pycache_dir_inside_the_tree` are **byte-identical in body** —
      both write `src/pkg/step.py`, take a digest, write
      `src/pkg/__pycache__/step.cpython-311.pyc` = `"junk"`, and assert the digest is unchanged. Remove
      **one** and give the survivor Fixture E's tracked arm: a **tracked** `src/pkg/__pycache__/keep.py`
      = `k = 1\n`, `git add -f`-ed, which **git reports as not excluded** (measured, rc 1) and which the
      fixed skip set must keep out anyway. The digest stays `eec1541e…` — measured on Fixture D's tree.
      **This is the positive control for § Templates' *"unconditionally"*.**
- [ ] **Step 3: demonstrate the survivor can fail, by mutation, not by assertion.** Remove `__pycache__`
      from `_SKIP_DIRS` and confirm the test fails. **A mutation that changes nothing is evidence about
      the tests, not about the code** — and the removed twin proves the point: deleting either one alone
      left the suite green, which is why one of them was doing no work.
- [ ] **Step 4: state the delta as added minus removed**, and name the removed test by its full name in
      the report. This is the one task in the slice with a negative component.

**Delta:** +2 tests, −1 test (net +1). The 13 `code_hash(` call sites become 12; **that is expected and
is not a guard-pin arm E violation**, because arm E's claim is about the two negative controls' return
value, neither of which is the removed test.

**What this task must NOT touch.** `src/` — this task is tests only. The two negative controls. Arm D,
whose literal this task's fixture shares and **does not edit**.

**Guard-pin arms this task may edit: NONE.**

---

