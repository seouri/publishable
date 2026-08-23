## Task 8: `E-CODE-EMPTY` — the guard, its § Errors row, and its two reachable situations

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is how the previous
> slice shipped a Critical, and this pointer is the fix. **Ruling F (the exclude chain) changes the
> command every hashing task runs.**

**Surface: `src/publishable/cli.py`, and a real `run` through the installed console script.**

**Files:** `src/publishable/cli.py`, `docs/reference.md`, `tests/test_cli.py`.

**The guard is at the CALLER, and the reason is measurable.** Two tests in `tests/test_hashes.py` use
`code_hash(tmp_path / "nonexistent_empty_repo", None)` as a **negative control** —
`test_code_hash_skip_list_matches_relative_path_not_absolute` and
`test_code_hash_handles_a_dot_git_intermediate_path_component`, both of which compare a real digest
against the empty one to prove the skip list is matched against **relative** parts. **A refusal inside
`hashes.py` would break both.** So `hashes.code_hash` still returns `sha256:e3b0c442…` for an empty tree,
and `command_run` refuses.

**The guard is written as `if not hashed:`, NOT as a comparison against the empty digest.** `ch ==
"sha256:e3b0c442…"` is behaviourally exact and it answers *were there zero files?* with a digest
comparison — **a proxy**, and a mutation swapping one for the other passes every fixture in this slice.
It is rejected by name here so it is not discovered in review.

**One emit site, and the cost of that choice is stated rather than hidden.** The site is at the hashing
site established by task 5, before `allocate_run_dir` and before any execution is paid for — **and after
unit resolution, so a resolver's quota may already be spent when it fires.** A second, earlier gate at
phase 3 would save that quota, but a mutation deleting the phase-5 site would then be **blind** unless a
fixture empties the trees *between* the two phases. **Two sites where one has a blind mutation and no
replacement** is the shape the § Errors work exists to catch, so H6a ships **one**.

- [ ] **Step 1: insert the guard** immediately after `hashed = hashed_files(repo_root, _include)` and
      before `ch = code_hash_of(hashed)`. Refuse through a `Collector` the way `E-CODE-DIRTY` does in the
      same function, print, and return `EXIT_WRONG`. The message **names both hashed trees** and says the
      run would otherwise publish the digest of nothing.
- [ ] **Step 2: Fixture G, end to end. Two construction facts, both measured, so the fixture is not
      discovered to be unbuildable mid-task.** **Git does not track an empty directory**, so `src/` must
      exist on disk while git holds nothing under it — which is also why the dirty gate is clean here,
      the same property measured for Fixture H. And the entrypoint must resolve from **outside** both
      trees: `load_experiment` inserts `<repo>/src` at the front of `sys.path`, but
      `importlib.import_module` still resolves anything else already importable, which is exactly how
      the scoping reached this case. A committed repo with an **empty** `src/`, no `templates/`, and
      an entrypoint importable from a `PYTHONPATH` directory outside both trees — the shape the scoping
      measured producing a **completed run at exit 0** with `code_hash: sha256:e3b0c442…` in its
      `run_id`. Assert exit 1, `E-CODE-EMPTY` in the output, **and that no run directory exists** — by
      listing `output_dir`, not by the exit code alone. *A refusal that leaves an empty run directory
      behind is a different behaviour from one that does not.*
- [ ] **Step 3: Fixture H — the situation task 5 CREATED.** A committed repo whose `.gitignore` is
      `src/`, whose `src/pkg/step.py` is untracked, **and which holds no file under `templates/**`**.
      **§ Corrections 6 binds this step:** measured, `git status --porcelain -- src templates` prints
      **nothing** (the dirty gate passes), today's digest is `f6a935cf…` — a real one — and after task 5
      there are **zero** hashed files. **With a `templates/t.py` present the after digest is `ef36e0c9…`
      and the refusal never fires**, so the fixture as the design states it would not reach the code it
      exists to test.
- [ ] **Step 4: mutation 8 — delete the guard.** Caught by Fixtures G and H: exit 0 and a completed run
      with the empty digest, measured as today's behaviour.
- [ ] **Step 5: mutation 9 — move the guard after `allocate_run_dir`.** Caught by Fixture G's *no run
      directory* assertion: the mutant leaves a directory behind.
- [ ] **Step 6: mutation P1 — replace `not hashed` with a comparison against the empty digest.**
      **Named blind in advance**: the two branches cannot differ, because the digest of an
      empty list *is* the empty digest. **The replacement is a reading obligation, stated as one**: the
      batch review reads the guard and confirms it tests the list, not the digest. That is why the
      one-liner is forbidden in this brief rather than left to a test.
- [ ] **Step 7: the § Errors row — ONE row covering EVERY emit site.** Add `E-CODE-EMPTY` to § Errors core
      raises. The row names **both reachable situations in one row**: no file under the two trees at all,
      and every file under them excluded by git. It says the guard is at the caller and that
      `hashes.code_hash` still returns the empty digest, **so a reader does not go looking for it in
      `hashes.py`**. It links the four-case table and restates none of it.
- [ ] **Step 8: the § Errors row for `E-CODE-FILE-LIST`**, whose code landed in task 4 and whose row lands
      here so both new rows are written by one task with one shape. **One row, one emit site** — the
      helper in `provenance.py`, reached from `command_run`'s single hashing site. It names the submodule
      case as the reachable instance, says the message carries git's own stderr, and says **explicitly
      that an empty answer is not read as "nothing excluded"**.
- [ ] **Step 9: mechanical pass** on both `reference.md` rows, as task 1's step 6 specifies.

**Delta:** +2 tests.

**What this task must NOT touch.** `hashes.py` — the empty digest stays. `E-CODE-DIRTY`'s absent row
(H6b task 17). `validate` (Decision 15). The nine undocumented codes.

**Guard-pin arms this task may edit: NONE.**

---

