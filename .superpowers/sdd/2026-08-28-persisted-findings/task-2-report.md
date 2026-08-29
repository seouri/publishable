# Task 2 report

Status: complete. Commit: `b9938c7`.

## Gate

- `uv run pytest -q`: 3560 passed, 1 skipped, 2 xfailed (baseline 3556 + 4 new tests; one
  pre-existing test's `== 37` field-count assertion updated to `== 38` for the new `findings`
  field, and its docstring/`Prepared` docstring updated to say thirty-eight).
- `uv run ruff check .`: All checks passed!
- `uv run ruff format --check .`: 101 files already formatted.
- `uv run mypy`: Success: no issues found in 56 source files.

## Source-pin mutation, both arms

Reverted `src/publishable/cli.py` line 3142 (inside `_prepare_run`, the `W-ENV-UNLOCKED` site) from
`_disclose(warn_c, findings)` back to `print(warn_c.render())`, keeping a `cp` backup first.

- Failing arm: `uv run pytest -q tests/test_cli.py::test_every_run_path_finding_is_disclosed_not_just_printed`
  → `FAILED ... AssertionError: _prepare_run prints a collector directly instead of calling _disclose`
- Restored from the `cp` backup (not `git checkout --`), re-ran the same command:
  `1 passed in 0.53s` — confirmed by behaviour, not `git status`.

## What was built

- `Collector.disclosed()` in `src/publishable/diagnostics.py`, beside `render`: returns
  `[{level, code, path, message}]` with `message` passed through the same `redact(f.message,
  self.credentials)` call `render` makes.
- `Prepared.findings: list[dict[str, str]]` in `cli.py` (plain, unquoted annotation — `list`/`dict`
  are builtins, valid at runtime with no `from __future__ import annotations`); comment beside it
  explains why, mirroring the existing `conditions` comment.
- `_disclose(c, into, *, file=None)` module-level helper in `cli.py`: `print(c.render(), file=file)`
  then `into.extend(c.disclosed())` — one call, preserving each site's stdout/stderr stream.
- Replaced all 12 `print(<collector>.render())` sites (5 in `_prepare_run`, 7 in
  `_execute_prepared`) with `_disclose(...)`. `_prepare_run` builds a local `findings` list from its
  first line and passes it into `Prepared(...)`; `_execute_prepared` unpacks `prepared.findings` and
  extends the same list object (never reassigned — the dataclass is frozen).
- Rewrote the two comments that claimed `run.yaml` has no diagnostics channel for these findings
  (the aggregate-findings comment and the `W-APPARATUS-UNANSWERED` comment), since that becomes
  false as of this task.
- Tests added: `tests/test_diagnostics.py` (`disclosed()` has the four keys; redacts the same way
  `render()` does, and the two surfaces agree; leaves an unset-credential message unchanged) and
  `tests/test_cli.py::test_every_run_path_finding_is_disclosed_not_just_printed` (the source pin).

## Disagreement with the brief

None. One incidental fixup required: an existing test asserted `Prepared` has exactly 37 dataclass
fields; adding `findings` makes 38, so that assertion and the `Prepared`/H9b-era docstrings were
updated to match (expected, since the brief's own docstring convention measures and states the
count).
