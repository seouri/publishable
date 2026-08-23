# H6a batch 4 — tasks 8 and 9 — `E-CODE-EMPTY`, and the stale owner corrected

Commits `758f8a7` (task 8) and (task 9, this file's own commit). Suite **2951 → 2953 passed**, 1
skipped, 2 xfailed — task 8's stated `+2 tests`; task 9's stated `0 tests`, confirmed by the same
count after both. `ruff check .`, `ruff format --check .`, `mypy` all clean throughout.

## Task 8 — the guard, its § Errors row, and `E-CODE-FILE-LIST`'s

**The guard, at the caller.** `command_run` now refuses with `E-CODE-EMPTY` immediately after
`hashed = hashed_files(repo_root, _include)` and before `ch = code_hash_of(hashed)`, written as
`if not hashed:` — testing the file list, never a comparison against the empty digest. Refuses
through a fresh `Collector`, prints, returns `EXIT_WRONG`. `hashes.py` is untouched: `code_hash`
and `code_hash_of` still fold zero files into `sha256:e3b0c442…` exactly as before.

**Mutation proving the "fires when it should" direction.** Deleted the guard entirely (mutation
8). Fixtures G and H both went from `EXIT_WRONG`/`E-CODE-EMPTY` to `EXIT_OK` with a completed run
carrying `…_e3b0c44` in its `run_id` — the exact shape the design's Ruling D and § Corrections 6
measured as today's behaviour. Reverted by editing the guard back in (not `git checkout`), diffed
byte-identical against a pre-mutation copy, re-ran both fixtures: pass.

**Mutation proving the "leaves no run directory" direction.** Moved the guard to immediately
after `allocate_run_dir` (mutation 9). Both fixtures failed on the `not list(results_dir.glob("*"))`
assertion specifically — a run directory existed even though the run still refused. Reverted,
diffed byte-identical, re-ran: pass.

**Mutation P1, confirmed blind as the brief names it in advance.** Replaced `if not hashed:` with
`if code_hash_of(hashed) == "sha256:e3b0c442…":` (the exact literal). Both fixtures still passed
— the two branches cannot differ, since the digest of an empty list *is* the empty digest — which
is why the brief forbids this one-liner by name rather than leaving it to a mutation to catch.
Reverted, diffed byte-identical, re-ran: pass. This is a reading obligation on the batch review,
per the brief: confirm the shipped guard tests `hashed`, not `ch`.

**The two negative controls, named and status.** `test_code_hash_skip_list_matches_relative_path_not_absolute`
and `test_code_hash_handles_a_dot_git_intermediate_path_component` in `tests/test_hashes.py`, both
calling `code_hash(tmp_path / "nonexistent_empty_repo", None)` directly (bypassing `command_run`
entirely) — both still pass, confirming the guard sits at the caller and not inside `hashes.py`.

**End to end, through the installed console script, both directions.** Built a project by hand
(empty `src/`, no `templates/`, entrypoint on `PYTHONPATH` outside both trees) and ran
`PYTHONPATH=<outside> uv run --project . publishable run <config>`: exit 1,
`E-CODE-EMPTY` printed, `results/` never created. Added `src/pkg/step.py`, committed, re-ran the
identical command: exit 0, `run.yaml` written normally, `results/run_<ts>_f6a935c/` and `latest`
both present — the ordinary path is honoured, not merely refused.

**Fixtures G and H, in `tests/test_cli.py`.**
- `test_h6a_fixture_g_a_wholly_empty_src_refuses_e_code_empty` — a committed repo with an empty
  `src/` (directory exists on disk, git holds nothing under it — git does not track empty
  directories), no `templates/`, entrypoint outside both trees. Asserts exit 1, `E-CODE-EMPTY` in
  stdout, and `results/` holds nothing.
- `test_h6a_fixture_h_a_wholly_ignored_src_refuses_e_code_empty` — a committed repo whose
  `.gitignore` is exactly `src/\n`, `src/pkg/step.py` present but untracked (git-excluded), no
  `templates/`. Asserts `git status --porcelain -- src templates` prints nothing first (the dirty
  gate is clean), then exit 1, `E-CODE-EMPTY`, and no run directory.

Both use a new, task-8-only builder, `_h6a_t8_project` — deliberately not task 5's
`_h6a_t5_project`, which always writes `src/pkg/step.py` and so cannot build Fixture G's wholly
empty tree.

**The § Errors row — `E-CODE-EMPTY`, one row, every emit site.** Added to `docs/reference.md`
§ Errors core raises, between the `E-RESOLVER-YIELD` row and the `E-APPARATUS-RAISED` row (the
same chronological slot in `command_run`: after unit resolution, before the apparatus probe).
Grepped for every emit site before writing "one": `grep -n "E-CODE-EMPTY" src/publishable/*.py`
→ one hit, the `error(...)` call in `cli.py`. States plainly that no exception is raised — the
check builds a `Collector` diagnostic directly, the same mechanism `E-CODE-DIRTY` uses (which
still has no row of its own; that gap is H6b task 17's, untouched here) — so a reader who greps
`hashes.py` for the guard is told in the row itself not to look there.

**The § Errors row for `E-CODE-FILE-LIST`.** Its code shipped in task 4 (`provenance.py`) with no
row until now. `grep -n "E-CODE-FILE-LIST" src/publishable/*.py` → one hit, the `raise
ContractError(...)` in `unignored_under_hashed_trees`. The row names the submodule case as the
reachable instance (measured in batch 3's fix round: `check-ignore` exits 128 with
`fatal: Pathspec '<path>' is in submodule '<name>'`), says the message carries git's stderr
verbatim, and states explicitly that an empty `stdout` is never read as "nothing excluded" — only
returncode `0`/`1` licenses that reading.

**Mechanical pass on both rows.** Table column count matches the header (4 pipe-delimited fields
on both new rows, checked with `awk -F'|'`). Both links — `#how-the-three-are-computed`,
`#the-apparatus-core-can-only-observe` — resolve, checked with a throwaway slug script against
every heading in the file. No trailing whitespace or tabs on either line (`grep -nP '[ \t]$'`).
Grepped the four documents, this file, and the feasibility analysis for the two new codes —
`grep -rn "E-CODE-EMPTY\|E-CODE-FILE-LIST" README.md docs/design-principles.md
docs/experimental-designs.md docs/reference.md docs/feasibility-llm-growth-studies.md CLAUDE.md`
— only `docs/reference.md`'s two new rows match; nothing else in the four documents mentions
either code, so no other passage needed touching.

## Task 9 — the zero-file blast radius, and the stale owner corrected

**Guard-pin arm E, re-run.** `test_h6a_arm_e_code_hash_of_a_directory_that_does_not_exist_is_the_empty_digest`
passes, standalone. `code_hash(tmp_path / "nonexistent_empty_repo", None)` still returns
`sha256:e3b0c442…`.

**`git diff` line count for `tests/test_hashes.py`, whole branch to this point.**
`git diff --stat main...HEAD -- tests/test_hashes.py` → **393 insertions(+), 21 deletions(-)**
(414 changed lines), across commits `ad59bdd`, `84a7393`, `9685ae0`, `c98b24e`, `cb5003d` — task 8
touched no line of this file (confirmed: `git show --stat 758f8a7` lists only `src/publishable/cli.py`,
`tests/test_cli.py`, `docs/reference.md`).

**Confirmed the two negative controls' own changed lines are calls, not asserts.** Isolated their
diff hunks: every changed line is `code_hash(...)` gaining a literal `, None` argument —
`empty_digest = code_hash(tmp_path / "nonexistent_empty_repo")` →
`… , None)`, `h = code_hash(repo)` → `…, None)`, `assert code_hash(repo) != h` →
`assert code_hash(repo, None) != h`. The `assert` keyword and every compared value are unchanged
in both tests; only the call signature moved, matching task 3's own report that "no assertion
here changes."

**The stale owner, corrected before the strike.** Appended a `RE-OWNED 2026-08-22 (H6a task 9)`
paragraph to `docs/superpowers/spec-defects.md`'s "`code_hash` over zero files…" entry, below the
existing `AMENDED 2026-08-11` paragraph — neither edited, both left as written, per the rule that
a spec-defects correction is appended rather than retro-edited. The new paragraph: names H1
Validation's routing as stale (H1 shipped 2026-08-11 without touching this); states both halves
Ruling D actually decided (the empty-tree return value unchanged, confirmed against the two
negative controls by name; the diagnostic built directly at `command_run` through a `Collector`,
never through `validate`'s registry); notes `validate` does not check this at all and that
whether it ever will is H6b task 18's open ruling (Decision 15), not decided here; and re-owns to
**H6a task 8**, which built the guard, the row, and the pinning tests. The strike itself is left
to task 12, per this task's own scope — not performed here.

**What was grepped, before any claim about other tests.** `grep -rln "e3b0c442" tests/` →
`tests/test_hashes.py`, `tests/test_cli.py` (2 hits total: the module-level literal
`_H6A_EMPTY_DIGEST` in the former, one docstring mention of the value in the latter — not a call
site). `grep -rln "nonexistent_empty_repo" tests/` → `tests/test_hashes.py` only, 5 hits: the two
negative controls (2 call sites) plus guard-pin arm E's own test and its docstring (3 more).
`grep -rln "empty_digest" tests/` → `tests/test_hashes.py` only, 5 hits, the same set. No other
test file references the empty-tree digest by value or by name.

## Concerns for the reviewer

1. **The § Errors row for `E-CODE-EMPTY` cannot honestly claim a `Type` in the "Raised by |
   Type · code" table's usual sense** — nothing is ever raised as a Python exception; the check
   builds a `Collector` diagnostic directly, the same shape `E-CODE-DIRTY` uses (which has no row
   at all, deferred to H6b task 17 for exactly this reason). Wrote the cell as
   `*(no exception; a `Collector` diagnostic)*` rather than force a false `ContractError`. A
   reviewer who reads this differently should say what `E-CODE-DIRTY`'s eventual row does instead,
   since the two are the same shape.
2. **`_h6a_t8_project` duplicates `_h6a_t5_project`'s shape** (project scaffold, outside-package
   entrypoint, `.gitignore`, `pyproject.toml`, `uv.lock`) with one parameterization difference
   (whether `src/pkg/step.py` is written, and the `.gitignore` text). Deliberate — task 5's helper
   cannot build an empty `src/` — but it is duplication a reviewer should price against a shared
   helper with more parameters.
3. **Fixture G's and Fixture H's config directory is named `configs/t5/`, not `configs/t8/`** —
   `_H6A_T5_CONFIG`'s `metadata.name: t5` is fixed, and `E-NAME-DIR` requires the directory to
   match it. Disclosed in a comment at the call site rather than silently reusing the name.
