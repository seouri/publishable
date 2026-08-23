## Task 4: the ignore helper in `provenance.py`, and `E-CODE-FILE-LIST`

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is how the previous
> slice shipped a Critical, and this pointer is the fix. **Ruling F (the exclude chain) changes the
> command every hashing task runs.**

**Surface: `src/publishable/provenance.py`, plus tests through direct calls and real repositories.**

**Files:** `src/publishable/provenance.py`, `tests/test_provenance.py`.

**The helper.**

```python
def unignored_under_hashed_trees(repo_root: Path, candidates: list[str]) -> set[str]:
    """The candidates git does NOT exclude, asked as one question in one call.

    `git check-ignore -z --stdin`, fed the repo-relative posix paths
    `hashes.hashed_files` already found, run with cwd=repo_root. Returncode 0
    means some listed path is excluded, 1 means none is, and anything else is
    a fault this refuses rather than reads: a path inside a submodule exits
    128 with `fatal: Pathspec ... is in submodule ...`, and inferring "nothing
    is excluded" from an empty stdout would hash another repository's files
    under a claim this record cannot support.

    `-z` is passed on BOTH ends and each entry is decoded with `os.fsdecode`:
    without `-z` git returns an excluded non-ASCII path C-quoted
    (`"src/pkg/na\\303\\257ve.env"`), which matches no key `hashed_files`
    produces, and `text=True` would decode with the locale's encoding rather
    than the filesystem's.
    """
```

**Three implementation routes are forbidden by name, because each is the likely error.**

1. **It must NOT call `provenance._git`.** That helper runs `check=False` and returns
   `result.stdout.strip()`, discarding the returncode — precisely the inference this refusal forbids, and
   it would turn rc 128 into an empty string indistinguishable from *nothing is excluded*.
   **`provenance.py` is the right place for the helper to sit; `_git` is the wrong thing for it to
   call.** *A recipe is its calls plus where they sit.* The precedent for refusing at a call site where
   an empty answer has no honest reading is `git_provenance`'s own `E-GIT-NO-COMMIT` block, in this same
   file — copy where it sits, not only what it calls.
2. **It must NOT pass `--no-index`.** Measured: for a committed `src/pkg/loose.pyd` against a
   `*.py[cod]` pattern, plain `check-ignore` reports **no match** (git does not exclude a tracked file)
   while `--no-index` reports `.gitignore:3:*.py[cod]`. **The flag that looks like a purity improvement
   is the one that breaks the rule.**
3. **It must NOT be reached with an empty candidate list and read as an error.** Measured:
   `check-ignore -z --stdin` with empty stdin returns rc **1**, which the tri-state already reads
   correctly as *nothing excluded* — but short-circuit on an empty list anyway and say why, because a
   subprocess for a question with no subject is work with no answer.

- [ ] **Step 1: write the helper**, exactly the signature Decision 4 specifies, so the caller can pass it
      as `include` without an adapter. Subtract git's answer from the candidate set and return the
      remainder.
- [ ] **Step 2: check the returncode, and raise `E-CODE-FILE-LIST` on anything but 0 or 1.** The message
      carries **git's own stderr verbatim** and names the repo root. Use `ContractError` with
      `code="E-CODE-FILE-LIST"`, the same shape `E-GIT-NO-COMMIT` uses.
- [ ] **Step 3: build Fixture I and assert the refusal.** A host repo with `src/pkg/step.py` and
      `src/vendor` added as a git submodule holding `lib/z.py`. **Measured here:** `check-ignore` exits
      **128** with `fatal: Pathspec 'src/vendor/lib/z.py' is in submodule 'src/vendor'`, while
      `hashed_files` finds `src/pkg/step.py`, `src/vendor/lib/z.py` and `templates/t.py`. Assert the
      raised error's `.code` is `E-CODE-FILE-LIST` and its message contains `src/vendor`. **Adding a
      submodule inside a test needs `-c protocol.file.allow=always`** on the `git submodule add`
      invocation; that is measured, not guessed.
- [ ] **Step 4: mutation 6 — route the call through `provenance._git`.** Caught by Fixture I: rc 128
      comes with **empty stdout**, so the mutant reads *nothing excluded*, keeps every candidate and
      raises nothing. Two branches that differ, measured.
- [ ] **Step 5: build Fixture F and assert the `-z` claim on EXCLUDED non-ASCII paths.** **§ Corrections
      4 binds this step and replaces the design's Fixture F.** The base tree with `*.env` appended to
      `.gitignore`, plus untracked `src/pkg/naïve.env` = `K=1\n` and `src/pkg/ünï.pyd` = `x\n`. Assert
      **two things**: the returned set equals `{"src/pkg/step.py", "templates/t.py"}` — set equality on
      the **kept** set, which is what `-z` protects — and `code_hash_of` over the kept pairs is
      `sha256:71bf339c…`, the base tree's digest. The docstring records that this was measured on
      macOS/APFS with `core.precomposeunicode = true`, and that **the paths are untracked**, so no index
      round-trip and therefore **no NFC/NFD normalization question arises** on any platform.
- [ ] **Step 6: mutation 3 — drop `-z` and split on newlines.** Caught by step 5's set equality **and**
      its digest: measured, the mutant's excluded set is
      `{'"src/pkg/na\\303\\257ve.env"', '"src/pkg/\\303\\274n\\303\\257.pyd"'}`, nothing is subtracted,
      the kept set gains both files and the digest becomes `sha256:06604d0c…` instead of `71bf339c…`.
      Two branches that differ, computed.
- [ ] **Step 7: mutation 4 — add `--no-index`.** Caught at task 5 by Fixture D's after value; **name it
      here and say which task's fixture catches it**, because a mutation whose catch lives in another
      task is a mutation whose report must say so.
- [ ] **Step 8: the ASCII control.** A tree with an excluded ASCII path only must return the same
      **shape** of answer, so a reviewer can see the non-ASCII arm is testing the encoding rather than
      the mechanism.
- [ ] **Step 9: the helper's docstring links the four-case table** in § How the three are computed
      (task 1) and **does not restate it**.

**Delta:** +5 tests.

**What this task must NOT touch.** `hashes.py`. `cli.py` — the wiring is **task 5's**. `_git` itself, and
no other `_git` call site. `git_provenance`'s pathspec.

**Guard-pin arms this task may edit: NONE.**

---

