# Tasks 1–2 report — the guard pin, and Ruling O in § The two files

**Status: both tasks complete, both committed.**

**Commit SHAs:**
- Task 1 (guard pin, arm T built): `8019578`
- Task 2 (Ruling O, § The two files): `2ed64da`

**Test summary:** baseline reconfirmed at 2963 passed, 1 skipped, 2 xfailed (foreground
`uv run pytest -q`, matches the brief exactly). After task 1: 2964 passed, 1 skipped, 2 xfailed
(delta +1, arm T). After task 2: 2964 passed, 1 skipped, 2 xfailed (delta 0, as required). All
four gates (`ruff check`, `ruff format --check` at 93 files, `mypy` at 52 source files, `pytest`)
clean at both commits.

**Concerns:** none outstanding.

## Task 1 — every pinned literal and how it was computed

- **Arm identification (by test name, `grep -n`):** P = `tests/test_cli.py::test_h8b_arm_d_the_five_figures_diff_reads`
  (line 16438 pre-edit); Q = `test_h8b_arm_c_the_records_key_lists_status_and_exit` (16388); R =
  `test_h5a_arm_d_the_worked_examples_own_numbers_as_raw_text` (17246, parametrized ×3); S =
  `test_study_add_redacts_hostname_when_present_on_a_synthesized_record` and
  `test_study_add_leaves_hostname_untouched_when_absent_from_the_source` in `tests/test_study.py`
  (270, 279); U = `test_h6a_arm_b_an_excluded_env_file_moves_the_hash_today` and
  `test_h6a_arm_c_the_seven_other_present_figures_are_unmoved` (19020, 19069) — H6a's own arms B
  and C of `_h6a_pin_project`, per the brief's naming.
- **Docstring-only edit per arm, `git diff` line counts** (from `git diff` hunk headers on the
  task-1 commit): import `shutil` +1; arm Q +2; arm P +2; arm R +2; arm U's first test (`arm_b`)
  +4; arm U's second test (`arm_c`) +5; arm S's two tests +4 each in `tests/test_study.py` (net
  diff there: 12 insertions, 2 deletions — each docstring's closing `.` moved onto the new
  sentence, which is why it shows as a deletion+insertion of the same line rather than a pure
  addition). No assertion, literal or name changed in any of P/Q/R/S/U — verified by reading each
  diff hunk before committing.
- **Arm R proven unaffected by Ruling O's coming edit (before task 2 touched anything):**
  extracted `_H5A_ARM_D_LITERALS` from `tests/test_cli.py` (26 members: the interval/hash literals
  `0.581` … `2f5c8d0`) and tested each against the literal line
  `    hardware: {gpu: "1x A100 80GB", cpu_count: 32}` read from `docs/reference.md:690`. Result:
  **no member matches** — confirmed by running the tuple through a Python substring check, not by
  reading it. Matches the plan's own measurement (§ Corrections 16).
- **Arm T's grep, re-run and reported:** newline-insensitive (flattened-whitespace) count of
  `E-GIT-NO-REPO` + `E-GIT-NO-COMMIT` per file in `tests/`: `test_lineage.py` 1, `test_provenance.py`
  2, `test_study.py` 1, `test_validate.py` 5 — **nine hits total**, none through `main([...])`
  (confirmed by reading each site: two direct `pytest.raises` calls in `test_provenance.py`, five
  in `test_validate.py` — four monkeypatched raise sites plus one comment — and one docstring
  mention each in `test_lineage.py` and `test_study.py`). Matches the plan's "nine hits" exactly.
- **Arm T's three invocations, built from scratch** (not from `run_a_project`, which always drives
  its own `main(["run", ...])` before a caller could intervene): scaffold via `main(["new", ...])`
  + `generate_experiment` + hand-written `metadata.description`/`authors` (required by
  `E-META-REQUIRED`, discovered empirically — the first draft omitted it and failed on that code
  instead), then (1) commit and `shutil.rmtree(".git")` before `run`; (2) `monkeypatch.chdir` to a
  tmp-path directory with no `.git` before `generate experiment`; (3) `git init` with no commit
  before `run`. All three assert on `capsys.readouterr().err` (the stream `main`'s
  `except PublishableError` prints to), exit code `EXIT_WRONG`, and invocation 3 additionally
  asserts `"E-CODE-DIRTY"` is absent.
- **Arm T proven able to fail (mutation 11):** copied `src/publishable/provenance.py`, inserted a
  `raise ContractError(..., code="E-CODE-DIRTY")` immediately after the `dirty` computation in
  `git_provenance` (before the `HEAD`/commit check) — this is the concrete form of "reorder the
  dirty gate ahead of the HEAD check," since the shipped code never raises on `dirty` inside
  `git_provenance` at all; the mutation makes it do so. Re-ran arm T: **failed**, with
  `err3 == "  error   E-CODE-DIRTY         src/** or templates/**: uncommitted changes; commit them first\n"`
  — `E-GIT-NO-COMMIT` did not appear and `E-CODE-DIRTY` did. Restored `provenance.py` from the
  copy, diffed byte-identical, cleared `__pycache__`, and **re-ran arm T to confirm it passes
  again** (it does) — the revert was verified by behaviour, not by `git status`.

**Which arm has no authorized editor:** five of six — Q, R, S (test bodies), T, and U. Only P has
an authorized editor, and it is task 3 exclusively (not this task).

## Task 1 — the shape captured against, and why

Arm P's advance spec was written against the **post-task-3 shape**, per design Decision 16 and
Ruling O: `hardware` is a **mapping** with exactly one key, `set(hardware) == {"cpu_count"}` — never
`isinstance(hardware, int)` or any scalar reading. This is the shape Decisions 5–9 already settled
(Ruling O: `hardware` carries `cpu_count`, not `gpu`; Decision 8: it is `{"cpu_count": os.cpu_count()}`,
`None` included). Capturing against this shape now — rather than against today's three-key literal
dict `{"manager": "uv", "uv_lock": None, "uv_lock_hash": None}` with no `hardware` key at all — is
exactly what avoids H6a's batch-2 Major: a pin captured against a signature the design was about to
supersede, which forced the next task into an unauthorized edit. Arm P's actual assertion (today's
shipped literal) is untouched by this task; only its **docstring** and the **advance spec table**
in the plan/design carry the post-task-3 shape, so task 3 has a written target rather than having to
re-derive one.

## Task 2 — the worked-example sweep, files covered and can-fail proof

**Files swept for `gpu` and `A100`, individually named, newline-insensitive (flattened whitespace)
and case-insensitive**, filtering the file list rather than the grep output:

| File | Line-based hits | Flattened hits |
|---|---|---|
| `README.md` | 0 | 0 |
| `docs/design-principles.md` | 0 | 0 |
| `docs/experimental-designs.md` | 0 | 0 |
| `docs/reference.md` | 2 (the pre-existing `hostname: "hms-gpu-node-04"` and this task's own new prose, "A GPU, an instrument revision") | 2 (same) |
| `CLAUDE.md` | 0 | 0 |

**Can-fail proof:** ran the identical sweep with the control string `"publishable"` (chosen because
`experimental-designs.md` does not carry `cohort-pilot`, the worked example's own package name — it
deliberately uses varied domain examples per `CLAUDE.md` § The worked example — so `cohort-pilot`
is not a control that works on all five files). Every file registered a nonzero count
(35/12/1/142/11 respectively), proving the sweep can register a hit and that the all-zero-except-
`reference.md` result above is a real finding, not a broken grep.

**`tests/test_report.py`'s apparatus fixtures** (`{"gpu": "A100"}` at five sites) were located and
left untouched, as the task requires — they are apparatus facts in a template fixture, unrelated to
`provenance.environment.hardware`.

**Correction 19 verified:** `grep -c "uv_lock_hash" tests/test_cli.py` → 4, matching the plan's own
measurement. Swept `tests/test_cli.py`, `tests/test_diff.py` and `tests/test_report.py` for every
literal of the environment block (`hardware`, `A100`, `hms-gpu-node`, `Linux-6.8.0`, `manager: uv`,
`python_version:`, `uv_lock:`, `environment:`, `The two files`): the only hits are `uv_lock_hash`'s
four occurrences (unrelated to `hardware`), `A100` in `test_report.py`'s apparatus fixtures
(unaffected), a `test_report.py` docstring citing "§ The two files" by name (about `vs_baseline`,
unrelated to `hardware`), and this task's own new docstring sentence in arm U's `test_h6a_arm_c`
mentioning `hardware` as one of H6b's three insertions (not a literal-value assertion). No other
test reads or asserts the edited line — **arm R is confirmed as the only pin task 2's edit can
reach**, and it was run (not edited) and passes.

**Mechanical pass on `docs/reference.md`:** the new link `[the apparatus core can only
observe](#the-apparatus-core-can-only-observe)` resolves against the existing heading
`### The apparatus core can only observe` (line 3190). No new heading was added, so no anchor
collision is possible. No table was touched. `grep -n " $"` and a tab/invisible-unicode check
(`grep -nP "\t"`) over the whole file returned no hits, before and after the edit.

## Files touched

- `tests/test_cli.py` — arm docstring authorizations (P, Q, R, U×2) plus new test
  `test_h6b_arm_t_the_git_layers_two_codes_at_the_cli`; `import shutil` added.
- `tests/test_study.py` — arm S docstring authorizations (two tests).
- `docs/reference.md` — § The two files' `hardware:` line and one new paragraph naming the
  apparatus as a GPU's route.
