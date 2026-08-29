# Task 1 report — W-ENV-UNLOCKED stops naming the repository path

**Status:** done, committed on `main` at `76aa752` (not pushed).

## Changes

- `src/publishable/cli.py` (~3119): `W-ENV-UNLOCKED`'s message no longer interpolates
  `repo_root`. Old: `f"no uv.lock found at {repo_root}; the environment is not pinned, and "
  "\`reproduce\` will not be able to restore it"`. New: `"no uv.lock found; the environment is
  not pinned, and "` + same tail. Both invariant substrings ("the environment is not pinned",
  "`reproduce` will not be able to restore it") are preserved verbatim.
- `tests/test_acceptance.py`: added `test_w_env_unlocked_names_no_host_path` (asserts the
  diagnostic's own rendered message, located by its header line, contains no host path) and
  `test_no_run_path_warning_or_error_interpolates_a_host_path` (an `ast`-based sweep over
  `_prepare_run`/`_execute_prepared` for any `.warn(`/`.error(` call interpolating `repo_root`,
  `input_dir`, `output_dir`, or `Path(...)`).
- `tests/test_cli.py`: `test_h9a_arm_b_runs_full_stdout_line_by_line` pinned the OLD message
  verbatim, including the tmp-path-derived repo path, in a whole-stdout literal list — exactly
  the leak this task closes. Updated the pinned line to the new message. Not in the brief; found
  by running the full suite before considering the task done.
- `README.md`: the `demo` walkthrough transcript showed the old message with `~/publishable-demo`
  inline; updated to match (cross-document worked-example consistency).

## Gate (all clean)

- `uv run pytest -q`: **3556 passed, 1 skipped, 2 xfailed** in 423.84s (baseline 3554/1/2; +2 new tests).
- `uv run ruff check .`: **All checks passed!**
- `uv run ruff format --check .`: **101 files already formatted**
- `uv run mypy`: **Success: no issues found in 56 source files**

## Mutation 1 — message-content test

Restored `f"no uv.lock found at {repo_root}; ..."` in `cli.py`, ran
`test_w_env_unlocked_names_no_host_path`:
```
E       AssertionError: no uv.lock found at /private/var/.../test_w_env_unlocked_names_no_h0/my-study; the environment is not pinned, and `reproduce` will not be able to restore it
E       assert '/private/va..._h0/my-study' not in 'no uv.lock ...o restore it'
1 failed in 14.47s
```
Reverted via `sed` back to the fixed wording (not `git checkout --`), re-ran: `1 passed in 14.88s`.

## Mutation 2 — source sweep test

Added `f"no uv.lock found; the environment is not pinned ({repo_root}), and "` inline in `cli.py`,
ran `test_no_run_path_warning_or_error_interpolates_a_host_path`:
```
E       AssertionError: ["_prepare_run line 3116: interpolates 'repo_root'"]
E       assert ["_prepare_ru... 'repo_root'"] == []
1 failed in 0.53s
```
Reverted from a `cp` backup taken before mutating, re-ran both new tests: `2 passed in 0.80s`.

## Disagreement with the brief

None on scope. One thing the brief didn't anticipate but the global constraint ("suite ... clean
at every commit") required: an existing guard-pin test in `test_cli.py` pinned the pre-fix message
verbatim (including a real filesystem path) in a whole-stdout literal. Fixing task 1 without
touching that test would have left the suite red, so it was updated in the same commit — a small,
mechanical, in-scope fix, not a design change.
