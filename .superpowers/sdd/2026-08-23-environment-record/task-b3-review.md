# Batch 3 review — task 4 (Ruling Q) and task 5 (Ruling N)

Commits reviewed: `b5a3da0` (task 4), `9e292ea` (task 5), `991c849` (report). Baseline 2969 passed,
1 skipped, 2 xfailed; claimed 2971. **Both commits are pure additions** (`git show --stat`: task 4
`docs/reference.md +2 / tests/test_study.py +34`; task 5 `docs/reference.md +2 /
tests/test_provenance.py +51` — no deletions in either), so no shipped test body, guard-pin arm, or
`src/` line could have moved in this batch.

## Task 4 — Ruling Q: PASS

- **Reason paragraph, read directly** (`docs/reference.md` § What `study add` redacts): states
  redaction exists "for identity and credentials," that a platform string/core count "name neither,"
  and draws the explicit parallel to `input_manifest_hash` surviving without its path. States the
  *why*, not merely the *what*, as required. The table stays four rows (verified by reading the
  section).
- **Fixture E, built independently.** Reproduced the end-to-end bundle myself outside the test suite
  (`run_a_project` + `study_new`/`study_add` through a standalone script, real project, real `run`,
  real bundle): source env `{'manager': 'uv', 'python_version': '3.13.7', 'os':
  'Darwin-25.5.0-arm64', 'hostname': 'macbookair.lan', 'hardware': {'cpu_count': 8}, ...}`, bundled
  env identical except `'hostname': '<redacted by study add>'`. Matches the report and the test
  verbatim — verified by **behaviour**, not by reading the test alone.
- **Mutation 7** (`_redact` also redacts `os`): edited `src/publishable/study.py` to add an `os`
  branch, ran `uv run pytest tests/test_study.py -q` → `1 failed, 42 passed` — only Fixture E fails
  (`os` equality assertion). Reverted by editing back; `diff` against a pre-mutation copy confirmed
  byte-identical; re-ran, `43 passed`.
- **Mutation 8** (stop redacting `hostname`): removed the `hostname` branch, ran the same file →
  `2 failed, 41 passed` — Fixture E and arm S's synthesized-record test
  (`test_study_add_redacts_hostname_when_present_on_a_synthesized_record`) both fail, exactly as
  predicted. Reverted and reconfirmed (`43 passed`).
- **Arm S** (`test_study_add_redacts_hostname_when_present_on_a_synthesized_record`,
  `test_study_add_leaves_hostname_untouched_when_absent_from_the_source`): both present, unedited by
  this batch's diff, pass unedited.
- Report's claim that `study.py`'s stale `hostname`-never-written docstring (lines ~128-133) is
  task 7's: confirmed by reading — `git show b5a3da0 -- src/publishable/study.py` and `git show
  9e292ea -- src/publishable/study.py` are both empty; the docstring is untouched and still stale,
  still routed to a later task, consistent with the batch-2 review's ruling.

No findings.

## Task 5 — Ruling N: PASS

- **Scope check, read directly.** § Errors core raises' preamble ("Two rows in this table are not
  raises, and the `Type` cell says so") and header (`| Raised by | Type · code |`) read as claimed.
  Grepped `docs/reference.md` for the preamble sentence post-edit: still reads "Two rows," confirming
  the two new rows (both genuine `ContractError` raises) don't widen that count.
- **Emit-site re-derivation, independent grep** (not trusting the report's grep):
  `grep -n "find_repo_root\|git_provenance" src/publishable/*.py` reproduces all six
  `E-GIT-NO-REPO` reach paths named in Decision 2 (`cli.command_run` uncaught;
  `generate`/`init` dispatch via `Path.cwd()` uncaught; `validate._check_data` catch-by-code-return;
  `validate.validate_config` bare `except ContractError`; `cli._load_experiment_for` `except
  Exception`; `study._refuse_if_in_repo` pass branch) and the single `E-GIT-NO-COMMIT` reach path
  (`cli.command_run:2027`, preceding the dirty gate at `cli.py:2028`, confirmed by reading the call
  order). Matches the shipped row text exactly.
- **Row placement**: immediately before the `E-CODE-DIRTY` row, per Decision 4 — confirmed by
  reading `docs/reference.md` around line 1149-1151.
- **Fixture G**, read and run: extracts codes from `tests.test_cli._section_text("### Errors core
  raises")` on one side and greps `code="E-GIT-NO-REPO"`/`code="E-GIT-NO-COMMIT"` across
  `src/publishable/*.py` independently on the other — genuinely reads both ends, not the table
  against itself.
- **Mutation 9** (delete the `E-GIT-NO-REPO` row): removed the row from `docs/reference.md`, ran
  Fixture G → `AssertionError: ('E-GIT-NO-REPO', []); assert 0 == 1`. Reverted, `diff` confirmed
  byte-identical, re-ran clean.
- **Mutation 10** (duplicate the `E-GIT-NO-COMMIT` row): appended a copy, ran Fixture G →
  `assert 2 == 1`. Reverted, `diff` confirmed byte-identical, re-ran clean.
- **Correction 15 / arm T, checked by mutation, not by assertion.** Ran
  `test_h6b_arm_t_the_git_layers_two_codes_at_the_cli` standalone: **passes, unedited.** Confirmed
  by `git log -S` that it was added in `8019578` (task 1, batch 1) — one task before task 5's brief
  was written — so the report's "already closed by arm T" is not a convenient assertion but a
  checkable fact. Then mutated `provenance.git_provenance`'s `E-GIT-NO-COMMIT` raise into a silent
  fallback (`commit = "0"*40` instead of raising): arm T **fails**
  (`AssertionError: assert 'E-GIT-NO-COMMIT' in ''`), proving the test genuinely exercises the code
  through `main([...])` rather than passing vacuously. Reverted, `diff` byte-identical, re-ran clean.
- **Grep-the-claim check on correction 15's "nine hits... none through main."** Independently
  re-grepped every `tests/*.py` file **at commit `2b18435`** (not HEAD) for both codes,
  newline-flattened: 9 hits total (`test_lineage.py` ×1, `test_provenance.py` ×2, `test_study.py`
  ×1, `test_validate.py` ×5), matching the report's count exactly; read `test_validate.py`'s five
  hits directly — one comment/docstring, four monkeypatched raise sites — none through `main`.
  Report's grep claim holds.

No findings.

## Bug in my own review process, disclosed

While probing task 4's Fixture E manually via the installed CLI (`uv run publishable generate
experiment ...`), a malformed invocation wrote a stray `configs/cohort-pilot/` and
`src/cohort_pilot/` into the **reviewed repo's own working tree** (not into the intended `tmp_path`
scratch target), which then made `ruff format --check .` flag one file. Deleted
(`rm -rf configs src/cohort_pilot`) before any gate was taken as final; `git status` confirmed clean
before recording the gate results below. Not a defect in the batch under review — a mistake in how
I invoked the CLI directly rather than through `run_a_project`.

## Gates (re-run fresh, caches cleared)

- `uv run ruff check .` → all checks passed.
- `uv run ruff format --check .` → 93 files already formatted, clean.
- `uv run mypy` → Success: no issues found in 52 source files.
- Full suite, foreground, `pytest-of-joon` and `__pycache__` cleared first: **2971 passed, 1
  skipped, 2 xfailed** in 207.96s. Reconciles with baseline 2969 + 2 (Fixture E, Fixture G) = 2971,
  matching the report's claimed delta with no gap.

## What was verified by behaviour vs. by reading

By behaviour (ran or mutated): both fixtures re-run clean; mutations 7, 8, 9, 10 all reproduce the
report's stated pass/fail counts; arm T re-run standalone and shown to fail under a direct mutation
of `E-GIT-NO-COMMIT`'s raise site; an independent end-to-end bundle built outside the test suite
reproduced the hostname/os/hardware behaviour; the 2026-08-22 "nine hits" grep was reproduced at
`2b18435` rather than trusted from the report; all four gates re-run.

By reading only: the six/one reach-path enumerations against `src/publishable/*.py` (grep output
read and matched to the shipped prose by eye); the preamble/header text; that arm T's git-blame
predates task 5's brief.

## Verdicts

- Task 4 (Ruling Q): **PASS**
- Task 5 (Ruling N): **PASS**

Suite: **2971 passed, 1 skipped, 2 xfailed** — reconciles with the claimed +2 over baseline.
