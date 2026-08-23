# Batch 3 report — task 4 (Ruling Q) and task 5 (Ruling N)

## Task 4 — Ruling Q: `os`/`hardware` unredacted, `hostname` redacted

`docs/reference.md` § What `study add` redacts gains one paragraph, no new table rows (the four
rows stay four): `os` and `hardware` travel unredacted because redaction here exists for identity
and credentials, and a platform string / core count names neither — it is provenance a bundle
reader needs, the same distinction the section already draws for `input_manifest_hash` surviving
without its path.

**End-to-end bundle evidence for all three keys** (`tests/test_study.py::
test_study_add_redacts_hostname_but_leaves_os_and_hardware_end_to_end`, Fixture E): built a real
project via `_real_run` (a `git`-committed project run through `run_a_project`, outside any repo —
`tmp_path`), `study new`+`study add`'d it into a bundle also under `tmp_path`, and compared the
bundled `main.run.yaml` against the **source** `run.yaml` the same run wrote:

- `bundled.provenance.environment.hostname == REDACTED`
- `bundled...os == source...os`, and it is a non-empty `str` (`Darwin-25.5.0-arm64` in this run)
- `bundled...hardware == source...hardware`, and it is a `dict` (`{"cpu_count": 8}`)

Added beside the existing hand-built Fixture Y
(`test_study_add_redacts_hostname_when_present_on_a_synthesized_record`), never in place of it.

**Mutations, run and reverted by editing back (`diff` confirmed byte-identical each time):**
- Mutation 7 (`_redact` also redacts `os`): Fixture E fails on the `os` equality assertion; every
  other `test_study.py` test, including both arm-S tests, stays green (43 → 42 passed, 1 failed).
- Mutation 8 (`_redact` stops redacting `hostname`): **two** failures — Fixture E (hostname
  assertion) and arm S's synthesized-record test
  (`test_study_add_redacts_hostname_when_present_on_a_synthesized_record`), exactly as the brief
  predicted (43 → 41 passed, 2 failed).

Arm S's two tests (`test_study_add_redacts_hostname_when_present_on_a_synthesized_record`,
`test_study_add_leaves_hostname_untouched_when_absent_from_the_source`) pass **without any edit** —
its arm was left as the controller's batch-2 ruling (`354bb46`) already set it, which this task did
not touch.

Commit: `b5a3da0`.

## Task 5 — Ruling N: § Errors core raises rows for `E-GIT-NO-REPO`/`E-GIT-NO-COMMIT`

**Scope check, read before writing either row.** § Errors core raises' preamble: *"Two rows in this
table are not raises, and the `Type` cell says so"*, siting `E-CODE-DIRTY`/`E-CODE-EMPTY` there
because *"`validate` does not report them ... a reader who meets one at `run` looks for it here"*.
Header: `| Raised by | Type · code |`. Both `E-GIT-NO-REPO` and `E-GIT-NO-COMMIT` **are** raises,
both carry `ContractError` (confirmed by reading `src/publishable/provenance.py:167,202`), so neither
needed an invented `Type` cell and neither widens or touches the "two rows" count — verified after
insertion by re-grepping the same preamble sentence, still reading "Two rows".

**Per-code emit-site check, both ends read independently (Fixture G):**
- `E-GIT-NO-REPO`: one raise, `provenance.find_repo_root:167`. Grepped every reach path
  (`grep -rn "find_repo_root\|git_provenance" src/publishable/*.py`): `cli.command_run` (uncaught,
  `main`'s `except PublishableError` → stderr, exit 1), the `generate`/`init` dispatch via
  `find_repo_root(Path.cwd())` (uncaught, same printer, walk-up from cwd since these commands take
  no path), `validate._check_data` (catches by code, `return`s quietly), `validate.validate_config`
  (bare `except ContractError`, `repo_root = None`), `cli._load_experiment_for` (`except Exception`,
  returns `None`), `study._refuse_if_in_repo` (catches by code, pass branch of `E-STUDY-IN-REPO`).
  Six reach paths, matching correction 12 exactly.
- `E-GIT-NO-COMMIT`: one raise, `provenance.git_provenance:202`, one reach path,
  `cli.command_run` (`git_provenance(config_path, config_path)` at `cli.py:2027`, called
  immediately before the dirty-gate check at `cli.py:2028` — confirmed it precedes `E-CODE-DIRTY`
  by reading the call order directly).

The two rows were written to carry everything Decisions 2 and 3 name (six reach paths and the
cwd-walk-up exception to `CLAUDE.md` § Invariants for the first; the single reach path, the
"precedes `E-CODE-DIRTY`" fact, and the `--verify` rationale for the second) and placed immediately
before the `E-CODE-DIRTY` row per Decision 4.

**Fixture G** (`tests/test_provenance.py::
test_h6b_fixture_g_e_git_no_repo_and_e_git_no_commit_have_one_row_and_one_raise_each`): the table
side comes from `tests.test_cli._section_text("### Errors core raises")`'s own rows (never the
design's instruction, per the "check the table's own scope sentence" trap); the code side comes
from an independent grep of `code="E-GIT-NO-REPO"`/`code="E-GIT-NO-COMMIT"` across
`src/publishable/*.py`. Asserts exactly one table row and exactly one raise site per code — both
ends read, not the table compared with itself.

**Mutations, run and reverted (`diff` confirmed byte-identical each time):**
- Mutation 9 (delete the `E-GIT-NO-REPO` row): Fixture G fails — `AssertionError: ('E-GIT-NO-REPO',
  [])`, `0 == 1` — the table side finds nothing while the `src/` grep is untouched.
- Mutation 10 (append a duplicate `E-GIT-NO-COMMIT` row): Fixture G fails — `2 == 1`, exactly-one
  becomes two.

**Named blind in advance, as the brief requires**: a mutation to either row's own **prose** — a
wrong reach-path count stated in English while the code, count and behaviour stay right — is caught
by nothing; no test reads a row's sentence. Reporting that I left it, not zero. The brief's own
replacement is Fixture G (existence/count) plus arm T (behaviour); both exist and both were run.

**Correction 15 (no existing test asserts either code through `main([...])`) — verified, and the
gap is already closed.** Grepped `tests/` for both codes (newline-flattened): nine hits at
`2b18435`, none through `main`, matching the brief's own count. But H6b **task 1**, in batch 1
(commit `8019578`), already built
`tests/test_cli.py::test_h6b_arm_t_the_git_layers_two_codes_at_the_cli` — three real `main([...])`
invocations (`run` after removing `.git` → `E-GIT-NO-REPO` exit 1; `generate experiment` with cwd
outside any repo → `E-GIT-NO-REPO` exit 1; `run` in a commitless `git init` repo → `E-GIT-NO-COMMIT`
exit 1, explicitly not `E-CODE-DIRTY`). Ran it standalone: **passes, unedited.** So the missing
end-to-end pin correction 15 flagged is not a gap task 5 needed to close — arm T already is that
pin, built one task before this one's brief was written. Task 5 added no new `main([...])` test;
Fixture G plus the pre-existing arm T together satisfy the brief's "replacement" requirement.

Commit: `9e292ea`.

## Gates and suite

Both tasks: `uv run ruff check .` — all checks passed; `uv run ruff format .`/`--check .` — clean
(each task's new test file needed one auto-format pass, applied and reconfirmed clean);
`uv run mypy` — success, 52 source files. Full suite, run in the foreground, caches cleared first:
baseline 2969 passed, 1 skipped, 2 xfailed → after task 4, 2970 passed (+1, Fixture E) → after
task 5, **2971 passed, 1 skipped, 2 xfailed** (+1, Fixture G). Both deltas match each brief's
stated `+1 test`; no reconciliation gap.

## Concerns

None outstanding. Guard-pin arm S was read but not edited (task 4). No guard-pin arm was touched in
task 5 either. `docs/feasibility-llm-growth-studies.md` untouched. `.superpowers/sdd/.gitignore`
was found clobbered to a bare `*` at session start (pre-existing, not caused by this session) and
was restored via `git checkout --` before the first commit, matching its own tracked content
exactly.
