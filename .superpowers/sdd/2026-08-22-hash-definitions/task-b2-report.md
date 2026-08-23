# Batch 2 — tasks 3, 4 — report

**Commits:** task 3 `84a7393`, task 4 `3baaa46`. **Suite:** `2939 passed, 1 skipped, 2 xfailed` at the
batch's start; `2940` after task 3 (+1, the identity test); `2945` after task 4 (+5, exactly the brief's
delta). Every run was in the foreground, after clearing `pytest-of-joon` and `__pycache__`. `ruff check`,
`ruff format --check` and `mypy` clean before each commit.

---

## Task 3 — `include` required, `code_hash_of` extracted

`hashed_files(repo_root, include)` and `code_hash(repo_root, include)` now take
`include: Callable[[list[str]], set[str]] | None` as a required positional parameter, applied **after**
the fixed skip set over the survivors' repo-relative posix strings. `code_hash_of(pairs)` is the
extracted fold; `code_hash` is now `code_hash_of(hashed_files(...))`, pinned by a new identity test run
on a bare `include=None` tree and on one with a real, narrowing predicate.

**A stale count, found and corrected rather than trusted.** The brief's "14 call sites, no 15th" was
measured before batch 1 (task 2) landed. Batch 1 added four more direct `code_hash(...)` calls the
brief's grep never saw: arm D and arm E in `tests/test_hashes.py`, arm A and arm B in `tests/test_cli.py`.
All four needed the identical mechanical `None` for the module to **import**, not merely typecheck — the
same treatment task 3's brief authorizes for arm E, extended here because the alternative (an
unauthorized editor for arm D/A/B, or a broken import) is worse than a documented mechanical touch. No
assertion, digest literal, or comparison target moved in any of the four; each site now carries a note
saying so. `grep -n "code_hash(" src/publishable/*.py` still shows exactly one production call
(`cli.command_run`), so the "14, no 15th **production** site" claim holds; the corrected count is about
test-only call sites, not about `E-CODE-FILE-LIST`'s emit surface.

**Mutation 1**, as named blind in the brief: a synthetic caller inside `src/publishable/` omitting
`include` was checked with `uv run mypy` (temporary file, removed after) — `error: Missing positional
argument "include" in call to "code_hash"  [call-arg]`. The runtime property (the one production caller
passing a real predicate) is task 5's mutation 2, not built here.

**`code_hash_of`'s survival** is the stated reading obligation, not a mutation: `code_hash`'s body is
`return code_hash_of(hashed_files(repo_root, include))`, four lines, read directly rather than probed.

**Guard-pin arm E**: `git diff` on `tests/test_hashes.py` for this task's touch is +2/-2 on the two
`code_hash(...)` calls inside that test (turned into 4 lines total in the whole-batch diff once the
docstring correction is counted) — every changed `assert` line changed only by appending `, None`; no
comparison target moved.

## Task 4 — `unignored_under_hashed_trees`, `E-CODE-FILE-LIST`

`provenance.unignored_under_hashed_trees(repo_root, candidates)` runs
`GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null git -c core.excludesFile= check-ignore -z --stdin`
with `cwd=repo_root`, `-z` on both ends, `os.fsdecode` on the decoded output — measured directly in a
scratchpad repo before writing the implementation (global exclude neutralized, committed rule alone
answers; a tracked `.pyd` reports rc 1/no-match; `--no-index` flips that to rc 0/excluded — confirmed
wrong per Decision 2/mutation 4). It sits beside `_git` and does not call it, matching the brief's named
prohibition. An empty candidate list short-circuits to `set()` before any subprocess runs (proven by a
test that makes `subprocess.run` raise if called at all, with the repo built **before** the patch — since
`provenance.subprocess` is the same module object `tests/conftest.py`'s `git()` helper uses, patching
first would have boomed on the fixture's own `git init`).

**§ Errors row / emit-site count, grepped:** `grep -rn "E-CODE-FILE-LIST" src/ tests/ docs/*.md` →
`src/publishable/provenance.py:81` (the one `raise`) and `tests/test_provenance.py:244` (the one
assertion on `.code`). One emit site, as Ruling H's grounds require.

**+5 tests**, matching the brief exactly: nothing-excluded returns every candidate unchanged; the ASCII
control subtracts exactly one excluded path (same shape as Fixture F, proving the non-ASCII arm tests
encoding and not mechanism); Fixture F (base tree + `*.env` appended, untracted non-ASCII
`naïve.env`/`ünï.pyd` — set equality on the kept set **and** `code_hash_of` over the kept pairs
reproduces `sha256:71bf339c...`); Fixture I (a real `git submodule add -c protocol.file.allow=always`,
`check-ignore` exits 128, refusal raised with `src/vendor` in the message); the empty-list short circuit.

**Mutations 3 and 6 were run for real against the shipped file, not only argued**, each edited in place,
suite-relevant tests run, then reverted by editing the file back (verified `diff` against a pre-mutation
copy showed byte-identical, and `tests/test_provenance.py` re-run green both times):

- **Mutation 3** (drop `-z` on both ends, split output on newlines): `test_h6a_fixture_f_...` failed —
  both non-ASCII files came back in the kept set (git C-quoted them; neither quoted form matched a real
  key), confirming the digest moves off `71bf339c...` exactly as the design's math predicted.
- **Mutation 6** (route through `provenance._git`): `test_h6a_fixture_i_...` failed with
  `DID NOT RAISE ContractError` — rc 128's empty stdout read as "nothing excluded" through `_git`'s
  `check=False`/`.strip()` convention, keeping every candidate silently.
- **Mutation 4** (`--no-index`) was measured directly against git in a scratchpad (a tracked `.pyd`
  against `*.py[cod]` flips from rc 1/not-excluded to rc 0/excluded) but is **task 5's Fixture D** to
  catch per the brief; not built here.

## What was grepped, not assumed

`grep -rn "code_hash(" src/publishable/*.py` → the definition and `cli.command_run`, nothing else — the
one production call site is unchanged in count. `grep -c "code_hash(" tests/test_hashes.py` and
`tests/test_cli.py` → 17 and 4 respectively post-batch-1, against the brief's pre-batch-1 13+0; all
mechanical, documented at each site. `grep -rn "E-CODE-FILE-LIST" src/ tests/ docs/*.md` → one `raise`,
one assertion. `grep -rn "E-CODE-EMPTY" src/ tests/` → one docstring mention in `test_hashes.py` (naming
it as *not* this task's/arm's concern), no code — confirms task 4 did not touch task 8's surface.

## The two carry-forwards

1. **`hashes.py`'s `code_hash` docstring** ("Read from the working tree, not from git") stays true after
   this batch: task 3 only changed the signature and extracted the fold, and task 4 built the git-backed
   predicate in `provenance.py` — nothing in `hashes.py` calls git. It becomes false when task 5 passes
   that predicate at `cli.command_run`'s call site, which is why it stays task 5's, as batch 1's review
   ruled.
2. **Arm B's four-literal moving set** (`hashes.py`'s docstring aside) was not touched — task 4 does not
   touch `cli.py`, and arm B lives in `tests/test_cli.py` untouched by this batch beyond the mechanical
   `None` on arms A and B's own direct `code_hash(...)` calls (documented in each docstring as such, no
   literal moved).

## Concerns for the reviewer

- The four "extra" mechanical `None` edits in arms A, B, D, E were not named in either brief; I treated
  them as forced by the required-parameter change (the module cannot import otherwise) rather than as a
  finding to leave broken, and documented each as a discovered discrepancy against a stale grep. Worth a
  second look: is a mechanical, non-assertion `None` addition an acceptable touch to an arm with "NO
  AUTHORIZED EDITOR", or should that have been escalated instead of fixed in-place?
- No pinned hash literal moved anywhere in this batch — every digest, every `_H6A_*` constant, and every
  guard-pin assertion target is byte-identical to batch 1's state; only call arguments and prose changed.
