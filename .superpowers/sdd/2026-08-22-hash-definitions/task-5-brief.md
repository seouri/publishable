## Task 5: wire it at `command_run`'s single call site — THE VALUE CHANGE

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is how the previous
> slice shipped a Critical, and this pointer is the fix. **Ruling F (the exclude chain) changes the
> command every hashing task runs.**

**Surface: a real `run` through the installed console script. Not `validate`, not a direct call.**

**Files:** `src/publishable/cli.py`, `tests/test_cli.py`, `tests/test_hashes.py`.

**BINDING, and it reaches this brief because a ruling that overrules a brief has to reach the brief:**

- **You are guard-pin arm B's SOLE AUTHORIZED EDITOR, and exactly two literals move:**
  `ebc5ee53…` → `71bf339c…` and `_ebc5ee5` → `_71bf339`. **Every other literal in that arm stays put.**
  **An edit to arm A, C, D, E or F is a finding**, and arms A, C and D have **no authorized editor at
  all** — a passing arm after this task is the proof.
- **The predicate is built HERE and bound at the moment of hashing — phase 5, not phase 3.** Between the
  dirty gate and the hash, `command_run` resolves units, which runs a **plugin resolver — user code that
  can create or remove files under `src/`**. An ignore answer captured at phase 3 and used at phase 5
  answers *what did git see before user code ran*, which is not the question the hash asks. **State read
  at the wrong moment is a proxy**, and it is the H7a corollary that cost its own round.
- **`git check-ignore` must run exactly ONCE per `run`** (§ Corrections 2). Take the file list once at the
  existing `ch = code_hash(repo_root)` site and fold it with `code_hash_of`.

**The edit.** At `command_run`'s existing hashing site, replace `ch = code_hash(repo_root)` with:

```python
def _include(candidates: list[str]) -> set[str]:
    return unignored_under_hashed_trees(repo_root, candidates)

hashed = hashed_files(repo_root, _include)
# task 8 inserts the E-CODE-EMPTY guard here, over `hashed`
ch = code_hash_of(hashed)
```

- [ ] **Step 0: name the import edits, because the plan this one copies its form from had exactly this
      correction.** H5b's § Corrections held *"`cli.py` does not import `_is_numeric`."* Here, `cli.py`
      imports `code_hash, design_digest, parameters_hash` from `publishable.hashes` and
      `find_repo_root, git_provenance` from `publishable.provenance`. **This task adds `hashed_files` and
      `code_hash_of` to the first and `unignored_under_hashed_trees` to the second.** Neither name is in
      scope before this edit.
- [ ] **Step 1: wire it, and change nothing about where the site sits.** The existing site already runs
      after unit resolution and before `allocate_run_dir`, which is what Decision 5 and Decision 7 both
      require. Do not move it.
- [ ] **Step 2: Fixtures A and B, end to end through `main(["run", …])`.** Assert the recorded
      `code_hash` and the run directory's name for both. Arm B's two literals move here and nowhere else.
- [ ] **Step 3: mutation 2 — compute the filter and ignore it** (drop the `include` application from
      `hashed_files`' loop). Caught by Fixtures B and C: `ebc5ee53…` versus `71bf339c…`, measured.
- [ ] **Step 4: Fixture C, the other two unhonoured patterns.** Untracked `src/.venv/lib/site.py` and
      `src/pkg/loose.pyd` beside B's `.env`. Assert the today digest `1947d2a2…` is **not** what the run
      records and that the recorded digest is `71bf339c…`. Assert the helper's own answer names exactly
      those three paths.
- [ ] **Step 5: Fixtures D and D′, and mutation 4.** A **tracked** `src/pkg/loose.pyd` = `X` (one byte,
      no newline, `git add -f`-ed) is still hashed: `eec1541e…`. **§ Corrections 5 binds this step:** the
      design's literal `6ddb8634…` is not reproducible from its own stated tree because the `.pyd`'s
      bytes were never stated, and `X` gives `eec1541e…`. **Fix the bytes in the fixture and assert the
      recomputed value.** The untracked twin's *today* value is also `eec1541e…`, so **assert the after
      value**; the today value would pass under a mutation that drops tracked files too. Mutation 4
      (`--no-index`) turns `eec1541e…` into `71bf339c…` — measured.
- [ ] **Step 6: mutation 5 — ask git before applying the fixed skip set** and drop the skip for a path
      git calls unexcluded. Caught by Fixture E (task 6 owns Fixture E's own test; **this mutation's
      catch lives there and this report says so**).
- [ ] **Step 7: mutation 7 — build the predicate at phase 3 and reuse it at phase 5. IT IS NOT BLIND, and
      § Corrections 10 gives the construction.** A project-local resolver whose module text embeds an
      **absolute path** into the project's own `src/` and writes `src/pkg/generated.py` during
      `resolve_units` — `tests/test_cli.py`'s `_install_plate_wells_resolver` and `run_a_project` are the
      two helpers that already do everything else this needs. The dirty gate ran at phase 3 and passed
      before the file existed, so the run proceeds. **The assertion:** after the run, recompute
      `code_hash_of(hashed_files(repo_root, live_predicate))` over the same tree and assert it **equals**
      the record's `code_hash`. Under the mutant the phase-3 answer predates the write, `generated.py`
      drops out of `include`, and the two differ by one file. Two branches that differ, and the
      discriminator is a digest rather than a file's presence.
- [ ] **Step 8: mutation P2 — pin the subprocess count.** Patch `subprocess.run` (or the helper) with a
      counter and assert `git check-ignore` is invoked **exactly once** for one `run`. **The mutant:** call
      `hashed_files(repo_root, _include)` and `code_hash(repo_root, _include)` separately — the naive
      shape — and watch the count go to 2. This is the pin § Corrections 2 exists for, and without it the
      correction is prose.
- [ ] **Step 9: Fixture M — one record carrying two hash definitions, and mutation 14.**
      **The sibling that already got it right is the first place to look:** `tests/test_cli.py`'s
      `_build_fixture_f_upstream` builds a **genuinely produced** upstream run with a `run`-scoped step
      publishing `out.json` and reads the shared step's name back out of its own `run.yaml` rather than
      assuming it. **Use it, then rewrite that record's `code_hash` to `ebc5ee53…` in place** — a real
      record with one field edited is a better pre-change artefact than a hand-written mapping, because
      it satisfies `lineage.read_record_file` by construction rather than by luck. Then run a post-change
      run over the base tree that consumes it through `io.reuse_from`. Assert the new record's own `code_hash` is `71bf339c…`, that
      `provenance.upstream[0].code_hash` is `ebc5ee53…` **copied verbatim** (`lineage.py` copies it;
      grepped), and — this is the part that must not be written as an absence —
      **assert the record's top-level key set as a literal**, so a future slice that adds a marker fails
      this fixture and has to come back and read Ruling C. Mutation 14 (recompute the upstream's hash at
      ledger time) makes both digests `71bf339c…`.
- [ ] **Step 10: run the whole suite and report the moved-test list**, named rather than counted.

**Delta:** +6 tests, plus arm B's two edited literals.

**What this task must NOT touch.** Arms A, C, D, E, F. `hashes.py`'s fold. `provenance.py`'s helper.
`diff.py`. The dirty gate at phase 3 — **the predicate is not bound there**, and a task that finds itself
editing phase 3 has misread Decision 5.

**Guard-pin arms this task may edit: B, and only its two enumerated literals.**

---

