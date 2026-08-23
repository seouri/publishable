## Task 3: `include` becomes a required batch parameter, and the fold is extracted

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is how the previous
> slice shipped a Critical, and this pointer is the fix. **Ruling F (the exclude chain) changes the
> command every hashing task runs.**

**Surface: `src/publishable/hashes.py`, plus 14 call sites.**

**Files:** `src/publishable/hashes.py`, `src/publishable/cli.py`, `tests/test_hashes.py`.

**The signature, and `None` is an explicit claim.**

```python
def hashed_files(
    repo_root: Path, include: Callable[[list[str]], set[str]] | None
) -> list[tuple[str, Path]]:
    """Sorted (repo-relative path, file) pairs across src/** and templates/**.

    `include` is handed EVERY candidate path that survived the fixed skip set,
    as repo-relative posix strings, and returns the subset to keep. It is
    positional and required: `None` is not a default, it is the explicit claim
    `hash every file these trees hold`, which only a caller without a
    repository can honestly make.
    """
```

```python
def code_hash_of(pairs: list[tuple[str, Path]]) -> str:
    """The fold, over a file list the caller already holds."""


def code_hash(repo_root: Path, include: Callable[[list[str]], set[str]] | None) -> str:
    return code_hash_of(hashed_files(repo_root, include))
```

**Why `code_hash_of` exists, and it is § Corrections 2 rather than tidiness.** Task 8's zero-file guard
needs the file list, and `command_run` also needs the digest. Without the extraction the command calls
`hashed_files` **and** `code_hash`, which walks the two trees **twice** and runs `git check-ignore`
**twice** — measured at 233 ms and 875 ms respectively on a 10,002-file tree — and makes
`E-CODE-FILE-LIST`'s **one emit site** false against the code, since the helper would have two reachable
raise paths. The extraction also makes Decision 4's *"the walk happens once, in one place"* literally
true.

**Why the parameter is required rather than defaulted.** `code_hash` has exactly **one** production
caller, so requiring it costs one line there and 13 mechanical edits in the pins, and it converts *a
future caller forgets and silently gets the un-excluded hash* into a `mypy` error. **Both of H7a's
fail-opens were predicates that answered permissively when nobody had told them otherwise.**

**Why a batch filter and not a per-path predicate.** `git check-ignore` costs **12.1 ms for 53 paths in
one call**; asking it per path would be 53 subprocesses. A memoizing per-path closure would have to do
**its own walk** to build its cache, re-introducing the second path spelling Decision 2 exists to
eliminate. Batching also makes Decision 3's *"git is never consulted about a path that is skipped
anyway"* literally true: the filter is called **after** the skip set has run, over exactly the survivors.

- [ ] **Step 1: add the parameter and apply it after the fixed skip set.** Collect the candidates exactly
      as today, then — when `include` is not `None` — call it **once** with the list of repo-relative
      posix strings and keep the pairs whose path is in the returned set. **The fixed skip set runs
      first, unconditionally**, so a tracked file inside `__pycache__` never reaches the filter. Sort as
      today.
- [ ] **Step 2: extract `code_hash_of` and make `code_hash` call it.** The fold is unchanged, byte for
      byte: `sha256(path) \0 sha256(contents) \n` folded over the sorted pairs, `sha256:`-prefixed.
- [ ] **Step 3: pin the identity, with a test rather than a comment.** Assert
      `code_hash(repo, None) == code_hash_of(hashed_files(repo, None))` on a real tree, **and** on a tree
      with a non-trivial `include`. Two implementations of one fold is what `covered_config` was
      extracted to prevent; this assertion is what keeps them one.
- [ ] **Step 4: edit the 14 call sites.** **13 in `tests/test_hashes.py`**, spread over six tests —
      `test_code_hash_covers_src_and_templates_only` (3), `test_code_hash_ignores_pycache` (2),
      `test_code_hash_is_prefixed_and_short_takes_seven` (1),
      `test_code_hash_skip_list_matches_relative_path_not_absolute` (3),
      `test_code_hash_still_skips_a_genuine_pycache_dir_inside_the_tree` (2),
      `test_code_hash_handles_a_dot_git_intermediate_path_component` (2) — **and `cli.command_run`'s
      `ch = code_hash(repo_root)`**, which gains a literal `None` here and is swapped for the real filter
      by task 5. **Without the production site, batch 2 does not typecheck.**
      **A near-miss worth not re-deriving:** `grep -c "code_hash(" tests/test_run_identity.py` returns 1,
      and it is the **name** of `test_the_id_is_timestamp_then_short_code_hash`, not a call site. There is
      no 15th site.
- [ ] **Step 5: guard-pin arm E — you are its SOLE AUTHORIZED EDITOR, and the edit is `None` only.**
      **Change no assertion.** Report the `git diff` line count for `tests/test_hashes.py` and confirm
      every changed line is a call rather than an assert. The two negative controls
      (`test_code_hash_skip_list_matches_relative_path_not_absolute`,
      `test_code_hash_handles_a_dot_git_intermediate_path_component`) must still resolve
      `code_hash(tmp_path / "nonexistent_empty_repo", None)` to `sha256:e3b0c442…`.
- [ ] **Step 6: mutation 1, and it is NAMED PARTLY BLIND IN ADVANCE.** Making `include` default to `None`
      has **no runtime difference** for callers that pass it. The catch is `uv run mypy` against a
      synthetic caller that omits it, and the runtime property that matters — that the one production
      caller passes a real predicate — is **task 5's mutation 2**. Name this in the report; do not claim
      it as a runtime pin.
- [ ] **Step 7: `code_hash_of`'s survival is a READING OBLIGATION, not a mutation, and it is stated as
      one.** Deleting the extraction does not make step 3's test *fail*, it makes it fail to **import** —
      two branches that cannot differ in the way a mutation needs. **A mutation is a claim too**, so this
      is not dressed up as one: the batch review reads `code_hash`'s body and confirms it delegates to
      `code_hash_of`, and task 5's **mutation P2** is what pins the property that actually matters — that
      the production caller takes the file list **once**.

**Delta:** +1 test.

**What this task must NOT touch.** `provenance.py` — the predicate is **task 4's**. Any assertion in
`tests/test_hashes.py`. The two byte-identical `__pycache__` tests, whose replacement is **task 6's**;
this task edits their call sites and nothing else, and **the 13 becomes 12 when task 6 removes one** —
that is expected and is not an arm-E violation.

**Guard-pin arms this task may edit: E, and only by adding `None`.**

---

