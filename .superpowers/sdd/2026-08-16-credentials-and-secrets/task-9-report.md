# Task 9 report: `required_env` checked at `validate`

**Status:** complete.

**Commit:** (created below) — `feat: required_env gets its first reader at validate, and CLAUDE.md's example moves to field_convention`

**Test summary:** `uv run pytest` — 1977 passed, 2 xfailed (baseline 1973 + 2 xfailed, plus the 4 new
tests in this task). `uv run ruff check .`, `uv run ruff format --check .` (76 files, 0 to reformat
after running `ruff format` on the appended block once), and `uv run mypy` (43 source files) all
clean.

## What was built

- `src/publishable/validate.py`: imported `missing_env` alongside `load_env` from
  `publishable.secrets`; added `_check_required_env(doc, template, c)`, called from
  `validate_config` immediately before `_check_parameters`, exactly as the brief specified. Body
  matches the brief verbatim: reads `template.required_env`, guards with
  `isinstance(names, list)`, reports one `E-CRED-MISSING` per name `missing_env` returns, at
  `experiment_type`, naming the template and the variable and never the value.
- `tests/test_validate.py`: appended the four tests from the brief verbatim (the fixture template,
  the unset/reported test, the satisfied/clean test, the `.env`-supplied test, the
  empty-`required_env`/`generic` test).
- `CLAUDE.md` § Misreadings → *Reading the documents*: replaced the `required_env` example with
  `field_convention`, plus the parenthetical noting `required_env`'s retirement and
  `apparatus_probe`/`apparatus_facts`'s ownership, per the brief's exact replacement text.

## The survivor grep, re-run rather than trusted

`grep -rn "field_convention" src/publishable/` returns exactly three hits: the two declarations
(`templates/base.py:13`, `templates/builtin/generic.py:7`) and the `generators/template.py:9`
comment listing it among the stub's omissions. No reader. Confirmed both before writing the
`CLAUDE.md` row and again after implementation (the new `_check_required_env` reads
`required_env`, not `field_convention`, so the second grep still shows zero readers).

## The position claim — pinned, not disclaimed

Task 8's review left the `validate`-site `load_env` comment claiming "before any check that asks
whether a variable is set" with nothing pinning that position. I reworded it to state precisely
what is now pinned and what is not:

> `.env`, once, before the first check that reads the environment — `_check_required_env` below,
> today, which is what `test_a_required_env_variable_may_be_supplied_by_dot_env` pins. That is
> weaker than "before `resolve_template`": nothing here depends on the stronger position, since
> `resolve_template` reads no environment variable, and no test distinguishes the two placements.

I verified both boundaries by hand (not part of the brief's Step 6 mutation set, but worth
recording): moving `load_env(repo_root)` to just after `resolve_template` (still before
`_check_required_env`) leaves all five `required_env`/`.env` tests green — confirming the weaker
position is genuinely all that's pinned. Moving it to just after the `_check_required_env` call
turns `test_a_required_env_variable_may_be_supplied_by_dot_env` red
(`{'E-CRED-MISSING'} == set()` fails). Both mutations were reverted by editing back (not
`git checkout --`), `__pycache__` cleared, and the revert verified by re-running the targeted
tests, then the full suite and `git diff` (clean).

## Mutations run (brief's Step 6)

- **(a) Delete the `c.error` call** (replaced the call with `pass`, keeping the `for` loop so the
  generator is still consumed). `test_an_unset_required_env_variable_is_reported_with_its_name`
  went red on `assert len(found) == 2` (`AssertionError: [] / assert 0 == 2`), checked against the
  test body's `found = [f for f in c.findings if f.code == "E-CRED-MISSING"]` filter — an absent
  finding is exactly what that assertion is built to see. Reverted; re-ran; green.
- **(b) Report the whole list rather than the missing ones** (`for variable in
  (str(n) for n in names):` instead of `missing_env(...)`).
  `test_a_satisfied_required_env_validates_clean` went red
  (`{'E-CRED-MISSING'} == set()`), because both env vars were set in that test — this is the
  mutation that proves the check actually reads `os.environ` rather than reporting
  unconditionally, and it is only observable because that test's `monkeypatch.setenv` control
  exists. Reverted; re-ran; green.

Both reverts were done by editing the file back to the original text (not `git checkout --`), with
`__pycache__` deleted before each re-run, and each revert verified by re-running the targeted test
(not by `git status`). `git diff src/publishable/validate.py` after all mutations shows a clean,
purely-additive diff against the pre-task file with no mutation residue.

## What no mutation reaches (brief's Step 7, unchanged)

- The `isinstance(names, list)` guard: no fixture declares a non-list `required_env`; a template
  that did would be a plugin-authoring fault outside this task's scope.
- `E-CRED-MISSING`'s position in `validate_config`'s call order relative to the *other* checks
  (`_check_metadata`, `_check_entrypoint`, `_check_parameters`, etc.) — only the five early-return
  refusals have a documented order in § Errors. What I *did* newly pin, beyond the brief's scope,
  is the position of `load_env` relative to `_check_required_env` specifically (see above) — that
  was task 8's leftover gap, not part of task 9's own deliverable, and I closed it because leaving
  the comment's stronger-sounding wording in place would have re-filed the same gap task 8's
  reviewer flagged.

## An accident caught and fixed before it shipped

My first `Edit` call appended the four new tests using an `old_string` that matched up through
`assert codes(write_config()) == set()` — the second-to-last line of
`test_validate_loads_dot_env_from_the_repository_root` — without including that test's true final
line, `assert os.environ.get("PUBLISHABLE_TEST_TOKEN") is None` (the control assertion that `.env`
removal leaves the variable unset). Because `old_string` didn't include it, that assertion ended up
displaced to the end of my new `test_a_template_declaring_no_required_env_reports_nothing`, where
it referenced an undefined `os` and would have broken that test while silently deleting a real
assertion from the pre-existing test. Caught by running the new tests immediately and seeing a
`NameError: name 'os' is not defined` where the brief's Step 2 expected only the one designed
failure. Fixed by restoring the displaced line to its original test and re-verifying
`git diff tests/test_validate.py` was purely additive (`git diff | grep '^-'` empty except the file
header) before proceeding. No other pre-existing test content was touched.

## Where the brief/spec disagreed with the code

- `_check_required_env`'s docstring (brief text, kept verbatim) forward-references
  `_check_requires_env`, which does not exist yet in this branch — it is task 10's function. This
  is not a defect; the design's task decomposition (`docs/superpowers/specs/2026-08-16-credentials-
  and-secrets-design.md` § Task decomposition, item 10) confirms `_check_requires_env` lands next,
  so the forward reference is accurate housekeeping rather than a broken citation. Flagging it only
  because CLAUDE.md's own guidance is to report every place a brief cites something not yet
  present.
- The `.superpowers/sdd/.gitignore` file was clobbered to a bare `*` before I started work (a
  side effect of `scripts/task-brief`, per CLAUDE.md § The development record). Restored its
  original content via `git checkout -- .superpowers/sdd/.gitignore` before committing this report
  (this is restoring already-tracked content to its committed state, not discarding uncommitted
  work — the working tree had no other pending changes to that file).

## Concerns

None outstanding. All four gate commands are clean; the new tests exercise both the failure and
honouring paths, the `.env`-wiring path, the empty-list path, and (beyond the brief) the exact
position boundary of `load_env` relative to the new check.
