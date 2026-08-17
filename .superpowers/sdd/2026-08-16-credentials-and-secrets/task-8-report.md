# Task 8 report: the two load sites, and the reconciled single-site sentence

**Status:** done. **Commit:** `99a62c3` on branch `h7c-credentials`.

**Tests:** `uv run pytest -q` → **1973 passed, 2 xfailed** (baseline 1971 passed + 2 xfailed, plus the
two tests this task adds). `uv run ruff check .` and `uv run ruff format --check .` clean (76 files
formatted). `uv run mypy` clean (43 source files).

## What was built

- `src/publishable/validate.py`: `from publishable.secrets import load_env` added alphabetically
  between `scope` and `stats`; `load_env(repo_root)` called inside `validate_config`, immediately
  after the `try/except ContractError` that resolves `repo_root` and before `resolve_template` is
  called — exactly the site the brief names, verified by reading the surrounding code first.
- `src/publishable/cli.py`: same import, alphabetically between `scope` and `stats`; `load_env(repo_root)`
  called in `command_run` immediately after `repo_root = find_repo_root(config_path)` and before
  `git_provenance(...)`.
- `docs/reference.md` § Secrets & credentials: the single-site sentence replaced with the
  two-site, `draft`/`resume`-inheriting version from the brief verbatim. Checked `#validation` and
  `#cli-reference` both resolve to real headings (`## Validation` and `## CLI reference`) before
  committing.
- `tests/test_validate.py`: `test_validate_loads_dot_env_from_the_repository_root`, appended verbatim
  from the brief (one `ruff format` reflow of an inline comment's spacing).
- `tests/test_cli.py`: `run_a_project` gained `_env_file` and `_local_template` keywords (with one
  docstring paragraph each, describing what each does rather than enumerating call sites, per the
  brief's own warning about that going stale twice already), the write logic for both immediately
  after `assert main(["new", str(root)]) == EXIT_OK`, the `_ENV_READING_STEP` fixture (placed after
  `_TRAIN_TOUCHING_STEP`, the free name the brief pointed at), and
  `test_run_loads_dot_env_itself_rather_than_relying_on_validate`.

## The two load sites — patch targets checked against the test bodies, not assumed

- `test_validate_loads_dot_env_from_the_repository_root` exercises `publishable.validate.load_env`
  by calling `validate_config` through `codes()`, with no patch — it's the direct, unpatched
  behaviour of the site under test.
- `test_run_loads_dot_env_itself_rather_than_relying_on_validate` patches
  `publishable.validate.load_env` to `lambda repo_root: False` — a no-op on the *other* module's
  attribute. `cli.py` imports its own `load_env` name into its own module namespace
  (`from publishable.secrets import load_env`), so patching `validate`'s copy leaves `cli.command_run`'s
  call untouched. If `command_run` did not load for itself, `_ENV_READING_STEP`'s
  `os.environ["PUBLISHABLE_TEST_TOKEN"]` would raise `KeyError`, the run would land `partial`
  (`EXIT_PARTIAL` = 4), and `run_a_project`'s `assert main(...) == expect_exit` (default `EXIT_OK` = 0)
  would fail before the `token_len` assertion is ever reached. Confirmed this precisely via mutation
  (a) below, including reading the actual exit code (4) it produced.

## Mutations — two, both reverted by editing the file back and confirmed by re-running the test

`__pycache__` cleared between runs; each revert confirmed by re-running the affected test, never by
`git status`.

**(a) Delete `load_env(repo_root)` in `cli.command_run`.**
Checked against the test body first (see above). Result: **FAIL**,
`test_run_loads_dot_env_itself_rather_than_relying_on_validate` —
`AssertionError: assert 4 == 0` (`main([...])` returned `EXIT_PARTIAL`, not the default `EXIT_OK`).
`test_validate_loads_dot_env_from_the_repository_root` stayed **PASS**, exactly as predicted: it
never touches `cli.py`.

**(b) Delete `load_env(repo_root)` in `validate_config`.**
Result: **FAIL**, `test_validate_loads_dot_env_from_the_repository_root`, on precisely the assertion
named in the brief — `AssertionError: assert None == 'from-the-file'` at
`os.environ.get("PUBLISHABLE_TEST_TOKEN") == "from-the-file"`.
`test_run_loads_dot_env_itself_rather_than_relying_on_validate` stayed **PASS**: it already patches
that call site to a no-op, so deleting the real call changes nothing it observes.

The two mutations discriminate the two sites separately, as the brief predicted a single
end-to-end test could not.

## What no mutation in this task reaches (Step 7)

The "never overrides" clause is pinned in `tests/test_secrets.py` (task 7's mutation (a)), but not
through either wired site here — no test in this task writes a `.env` whose value differs from an
already-exported one and then runs `validate` or `run` through it. Accepted per the brief:
`load_env` is the single implementation both sites call, so duplicating the override test at each
call site would pin the call rather than the behaviour. Named here so it is not rediscovered.

A second gap, specific to this task rather than inherited from task 7: **nothing pins the
`validate`-site call's *position*.** Mutation (b) deletes the call outright; a mutant that instead
*moved* it — past `resolve_template`, or to the end of `validate_config` — would still pass
`test_validate_loads_dot_env_from_the_repository_root`, which only asserts `os.environ` after
`validate_config` has already returned. The comment placed above the call claims the position
matters ("before any check that asks whether a variable is set"), which is a claim about task 9's
`required_env` reader, not yet built — task 9 is the natural owner of pinning it, since it is the
one that adds a check that would go red if the load ran too late. Named here so it is not
rediscovered as a gap belonging to no task.

## Disagreements between the brief/spec and the code

Two, both mechanical rather than a design disagreement — nothing here changed what was built.

- **The brief's literal `run_a_project(...)` call line cannot be committed as written.** The brief's
  Step 1 text puts it on one line —
  `run_a_project(tmp_path, units=4, _starter_step=_ENV_READING_STEP, _env_file="PUBLISHABLE_TEST_TOKEN=abcdefgh\n")` —
  which is 105 characters and fails `ruff check .` (`E501 Line too long (105 > 100)`) against a repo
  that is format-clean at 76 files. Split across four lines (one argument per line); behaviour
  unchanged.
- **The brief's inline-comment spacing in the `validate` test fails `ruff format --check .`.** The
  literal `assert codes(path) == set()                      # the config itself is clean` gets
  reflowed to a single space before the comment. Reformatted; behaviour unchanged.

Everything else measured against the current code matched the brief and the design's corrections
exactly:

- `cli.NOT_BUILT_COMMANDS` does include `draft`, `resume`, `dry-run` — confirmed by grepping
  `src/publishable/cli.py` directly (the dict literal at line 121 and its lookups at line
  2683/2685), not assumed from the brief's own claim. This confirms the design's correction #2, so
  only `command_run` was wired and no `command_draft` stub was added. The reconciled `reference.md`
  sentence states this as "in this build the executing site is `run`; `draft`, `resume` and
  `dry-run` inherit it when each is built," matching the treatment `dry-run` already got elsewhere
  in the document.
- `validate_config`'s `try/except ContractError` resolving `repo_root`, and its position before
  `resolve_template`, matched the brief's description of the interface verbatim — no adjustment
  needed to the insertion point.
- `command_run`'s `repo_root = find_repo_root(config_path)` call and its position before
  `git_provenance(...)` also matched verbatim.
- Import alphabetization: `secrets` sorts between `scope` and `stats` in both files' import blocks,
  which is where it was placed; the brief's own snippet for `validate.py` said "alphabetical among
  the `from publishable.…` imports" without naming the neighbours, and `cli.py`'s wasn't specified
  at all, so this was verified against each file's actual import list rather than assumed.
- `_TRAIN_TOUCHING_STEP` was confirmed to already exist in `tests/test_cli.py` (used as the anchor
  point for the new `_ENV_READING_STEP` fixture, itself confirmed free of collision).
## The `.superpowers/sdd/.gitignore` clobber

Found already modified to a bare `*` when I ran `git status`, before I touched anything in this
task — the residue of an earlier `task-brief`/`sdd-workspace` invocation, not something I caused.
Restored with `git checkout -- .superpowers/sdd/.gitignore` rather than editing it back by hand;
verified the restore rather than trusting the command: `head` on the restored file shows the full
22-line warning-and-rationale block (not `*`), and `git log -1 -- <path>` plus
`git merge-base --is-ancestor` confirm HEAD already carried that correct content from an earlier
commit (`78bb794`, ~100 commits back), so restoring to HEAD lost nothing of mine — I had made no
edit to that file. `task-8-report.md` itself is not matched by any pattern in the restored
`.gitignore` (`task-*-brief.md`, `*.diff`, `*.txt`), so no `-f` was needed to add it; checked this
by running `git status --porcelain` and confirming the report listed as an ordinary untracked file
rather than silently absent.
