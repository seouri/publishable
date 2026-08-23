# Batch 1 review — H6b tasks 1–2

**Verdicts: Task 1 PASS. Task 2 PASS.**

## What was verified by behaviour (re-run/re-derived independently, not taken from the report)

- Full suite, foreground, `uv run pytest`: **2964 passed, 1 skipped, 2 xfailed** — reconciles
  exactly with baseline 2963 + 1 (arm T) and matches the report's claimed count at both commits.
- `ruff check .` — all checks passed. `ruff format --check .` — 93 files already formatted.
  `mypy` — success, 52 source files. All match the report's gate numbers exactly.
- Re-ran `git show 8019578` and `git show 2ed64da` in full and read every hunk: task 1 touches only
  `tests/test_cli.py` (+97/−0) and `tests/test_study.py` (+10/−2); task 2 touches only
  `docs/reference.md` (+9/−1). No file outside each brief's stated scope was touched; nothing in
  `src/`. Arms P, Q, R, S, U got exactly one docstring sentence each (or two, for arm U's pair) —
  no assertion, literal, or name in any of their bodies moved.
- Arm P's shipped assertion, read directly: `assert environment == {"manager": "uv", "uv_lock":
  None, "uv_lock_hash": None}` after popping `python_version` — confirms today's shape has no
  `os`/`hostname`/`hardware` keys, so task 3 (the arm's sole authorized editor) will need to pop
  three more keys and assert three more values, exactly as the brief's advance spec requires. The
  advance spec itself (`set(hardware) == {"cpu_count"}`) matches Decision 5 / Ruling O and Decision
  8 in the design (`hardware: {cpu_count: <int|None>}`, one key) — the pin is captured against the
  **post-task-3** shape, which is exactly what avoids H6a's batch-2 Major (a pin captured against a
  signature the design was about to supersede).
- Arm R's unaffectedness, recomputed from scratch: extracted the 25-member `_H5A_ARM_D_LITERALS`
  tuple from `tests/test_cli.py` (lines 17114–17139) and tested each member against both the
  pre-edit line `hardware: {gpu: "1x A100 80GB", cpu_count: 32}` and the post-edit line
  `hardware: {cpu_count: 32}` — **zero matches against either.** Ran the actual test
  `test_h5a_arm_d_the_worked_examples_own_numbers_as_raw_text` after the real edit landed: passes,
  unedited. Confirms arm R is the only pin task 2's edit can reach and it needed no edit.
- Arm T proven able to fail, reproduced independently: copied `provenance.py`, inserted
  `raise ContractError(..., code="E-CODE-DIRTY")` immediately after the `dirty` computation in
  `git_provenance` (before the `HEAD`/commit check). Re-ran
  `test_h6b_arm_t_the_git_layers_two_codes_at_the_cli`: **failed** —
  `AssertionError: assert 'E-GIT-NO-COMMIT' in '  error   E-CODE-DIRTY         mutation test\n'` —
  exactly the failure mode the report describes. Restored from the copy (`diff` byte-identical),
  cleared `__pycache__`, re-ran: **passed**. Revert verified by behaviour, not `git status`.
- Arm T's "nine hits, none through `main`" grep, reproduced at the pre-task commit `2b18435`:
  `test_provenance.py` 2, `test_study.py` 1, `test_validate.py` 5, `test_lineage.py` 1 = 9; and 0 in
  `test_cli.py` at that commit (the new arm itself is what later adds hits there). Matches exactly.
- The six pre-existing arms this batch names but does not build (Q, R, S×2, U×2) were run directly
  and individually: all 9 pass. Arm-by-arm mutation proof for these six was **not required by
  either brief** — only arm R (unaffectedness) and arm T (new coverage) carry a proof obligation in
  task 1's brief; Q/S/U are pre-existing pins whose own failure modes were established by the
  slices that built them (H8a/H8b/H6a) and are unedited here (docstring-only). They are real,
  executing tests, not named-but-absent arms.
- Task 2's `gpu`/`A100` sweep, reproduced independently over the file list (never the grep output):
  `README.md` 0, `design-principles.md` 0, `experimental-designs.md` 0, `reference.md` 2 (the
  pre-existing `hostname: "hms-gpu-node-04"` plus this task's own new "GPU" prose), `CLAUDE.md` 0.
  Also swept `docs/feasibility-llm-growth-studies.md` (named in the reviewer brief but not in task
  2's own brief): 0 hits. Control string `"publishable"` registers nonzero hits in every one of the
  six files (39/15/1/165/16/34), proving the sweep can fail. `test_report.py`'s five
  `{"gpu": "A100"}` apparatus-fixture sites are untouched (no diff there) — confirmed via
  `git diff e2f38cc..110350c -- tests/test_report.py`, empty.
- Mechanical pass on `docs/reference.md`, redone independently: `grep -n " $"` and `grep -nP "\t"`
  both zero hits; the new link `#the-apparatus-core-can-only-observe` resolves against the existing
  `### The apparatus core can only observe` heading (line 3190); no new heading added; no table
  touched.
- The added paragraph is correctly placed immediately after § The two files' explanatory prose
  (right after the `plugin_versions`/`cohort-pilot` paragraph, before the `per_repeat` paragraph),
  names the apparatus as the GPU's route with a link rather than a restatement, and states the cost
  in the document rather than only in the design doc, per Ruling O and the reviewer brief's item 5.
  `apparatus: null` in the same fenced block is untouched — `cohort-pilot` was not given a probe.
- Correction 16, read directly: `_H5A_ARM_D_LITERALS` (see above) contains no substring of the
  `hardware` line under either spelling — confirmed by me, not just cited.
- Correction 19, re-derived: `REFERENCE_MD.read_text()` call sites in `tests/test_cli.py` are 7
  (lines 9406, 9426, 9440, 9482, 9596, 12958, 12975), each reading a table, heading set, or a
  specific `E-` row by its own final cell — none extracts § The two files' `run.yaml` block. Same
  check on `tests/test_diff.py` and `tests/test_report.py`: every site parses `diff`-block rows or
  header shapes from a *different* named worked example (the apparatus `DIFFERS` block, the
  design-principles `parameters_hash DIFFERS` block), never § The two files. Conclusion holds: arm R
  is the only reachable pin.

## Findings

**Minor — `_H5A_ARM_D_LITERALS` miscounted as 26 members in the task-1 report; actual count is 25.**
File: `.superpowers/sdd/2026-08-23-environment-record/task-b1-report.md`. The report's Task 1
section states "(26 members: the interval/hash literals `0.581` … `2f5c8d0`)". Counting the tuple
directly at `tests/test_cli.py:17114–17139` gives 25 elements. Does not change the substantive
result (no member matches either `hardware` line), but it is exactly the kind of uncomputed literal
the batch's own brief asks to have "recomputed by you."

**Minor — `tests/test_study.py`'s diff stat miscounted in the task-1 report.** The report states
"net diff there: 12 insertions, 2 deletions" for `tests/test_study.py`. `git show 8019578 --stat --
tests/test_study.py` reads `10 insertions(+), 2 deletions(-)`. The overall two-file total the report
gives (107 insertions, 2 deletions) is correct — only the per-file breakdown for this one file is
off by two.

No Major or Critical findings. Every mutation claimed in the report was reproduced and matched; the
sweep claims, grep claims, and gate numbers were all independently recomputed rather than read from
the report, and all matched exactly except the two Minor miscounts above (which are about the
report's own arithmetic, not about the code or tests it describes).

## Undisclosed drops

Diffed both task briefs against what shipped, step by step (see checklists in
`task-1-brief.md`/`task-2-brief.md`). No step was dropped in either task; the "must NOT touch" lists
for both were respected (checked via full `--stat` on both commits).

## Suite result

2964 passed, 1 skipped, 2 xfailed (foreground `uv run pytest`, run to completion). `ruff check`,
`ruff format --check` (93 files), `mypy` (52 source files) all clean.
