# Task 11 review — Fixture W, Fixture E, Fixture B's cross-spelling arm, and the whole-branch mutation re-run

## Verdict: PASS, one Major

## What was verified by behaviour, not by reading

- **Full suite, twice.** `uv run pytest` (foreground, clean `pytest-of-joon`/`__pycache__` first):
  **2891 passed, 1 skipped, 2 xfailed** both times, matching the report's claimed delta of +7 over the
  stated baseline (2884 passed, 1 skipped, 2 xfailed). Re-confirmed a third time after reverting the
  last mutation, same result.
- **All four gates, rerun directly**: `uv run ruff check .` → all checks passed; `uv run ruff format
  --check .` → 93 files already formatted; `uv run mypy` → success, 52 source files. All match the
  report.
- **Correction 2 and correction 8, measured independently** with a real `StepIO` (not the report's own
  code, built from scratch against `_encode_csv`/`_decode_csv`/`_encode_parquet`/`_decode_parquet`):
  - `.csv` `1.0` → `{'v': '1.0'}`; `np.float64(1.5)` beside `2.5` → `.parquet` gives `1.5`/`2.5` (both
    `float`), `.csv` gives `'1.5'`/`'2.5'` (both `str`).
  - `int` beside `float`: `.parquet` promotes both to `1.0`/`2.5`; `.csv` does **not** promote —
    `'1'`/`'2.5'`. Confirms the report's claim that the two formats disagree on this arm for two
    independent reasons (the `str()` rule and the absent cross-row unification).
  - All-`None` column: `.parquet` → `None`/`None`; `.csv` → `''`/`''` (never `None`, never the string
    `"None"`). Confirms the report's Fixture E finding, which is genuinely false of the design's own
    wording (*"round-trips as `None` in every row. Both formats"*) — grepped the design doc directly at
    `docs/superpowers/specs/2026-08-21-artifacts-write-side-design.md:619` and it says exactly that,
    with no `.csv` carve-out.
  - Empty row list: both formats → `[]`, raises nothing. Confirmed.
- **Mutation 9(v)** (widen `io.write`'s `except ContractError` to the whole body below `path()`, on
  `PublishableError`): applied at the call site in `src/publishable/artifacts.py` (kept a saved copy at
  `/tmp/artifacts_orig.py`), ran the full suite. Result: **exactly 4 failed** —
  `test_an_unregistered_extension_takes_bytes_or_str_verbatim`,
  `test_h5a_step2_control_the_unregistered_suffix_message_is_not_prefixed`,
  `test_write_of_an_unwritable_object_leaves_nothing_behind`,
  `test_h5a_fixture_n_a_non_mapping_row_refuses_with_the_documented_code` — the identical set the report
  names, matching task 9 review `8bc0413`'s corrected count of 4 (not the design's originally
  mis-reported 1). Reverted by restoring the saved copy; `diff` confirmed byte-identical; re-ran and
  confirmed back to 2891/1/2.
- **Mutation 13(ii)** (wrap every value in `float()` before `pa.table(...)` in `_encode_parquet`):
  applied, ran the full suite **twice** for stability. Both runs: **376 failed, 2467 passed, 1 skipped,
  2 xfailed, 48 errors** — see Finding 1 below. Reverted by restoring the saved copy; `diff` confirmed
  byte-identical; re-ran the full suite a third time and confirmed back to 2891 passed / 1 skipped / 2
  xfailed, and `git diff --stat` showed nothing outstanding.
- **Arm D and arm E's `.parquet` half have no editor in this task's commits.** `git log -S
  "test_h5a_arm_d_the_worked_examples_own_numbers_as_raw_text"` → only `badec28` (task 13). `git log -S
  "test_h5a_arm_e1_parquet_keeps_a_structural_or_bytes_cell_intact"` → only `6c3e6c3` (task 13's fix
  round). Neither name appears in `16ba11a`'s diff (confirmed by `git show 16ba11a --stat`, which touches
  only `tests/test_artifacts.py` and `.superpowers/sdd/.gitignore`).
- **The `.superpowers/sdd/.gitignore` restore.** `git show 81dabdf --stat` touches exactly
  `.superpowers/sdd/.gitignore` and the new `task-11-report.md` — nothing else was swept in. `git ls-files
  .superpowers/sdd/2026-08-21-artifacts-write-side/` shows every prior batch's `task-*-report.md` /
  `task-*-review.md` and `progress.md` still tracked; `git status --porcelain .superpowers/sdd/` is
  empty. No record went untracked.
- **The "filed for task 12" claim.** Confirmed no `H5a task 12` commit exists yet on this branch (`git
  log --oneline --all | grep -i "task 12"` shows only unrelated slices' task 12s), so the report's
  "task 12, which has not yet landed on this branch" is accurate — this is a flag left in a test
  docstring and the report's own Concerns section, not a false claim of an existing `spec-defects.md`
  entry. No entry for this gap exists yet in `spec-defects.md` (grepped `DictWriter`/`empty string`/
  `round-trips as` — none), which is consistent with the report never claiming one does.

## What was verified by reading only

- The design's Fixture W/E/B wording (`docs/superpowers/specs/2026-08-21-artifacts-write-side-design.md`
  § The discriminating fixtures), the plan's task 11 brief and corrections 2/7/8, and the second
  controller ruling's `.csv`/`.parquet` split — all consistent with what the diff builds and what the
  report claims about them.
- The remaining 22 of 25 mutation rows in the report's table: read against the source they claim to
  mutate (`RESERVED_COLUMNS` call sites in `src/publishable/units.py`, `_coerce_one`'s branches, the
  `_encode_csv`/`_encode_parquet` call sites, `_check_column_types`, `_finalize_columns`) and against the
  test names they claim catch each — every named test exists at the location claimed
  (`test_h5a_arm_a_...`/`test_h5a_arm_b2_...` in `tests/test_cli.py`/`tests/test_artifacts.py`,
  `test_h5a_arm_c_...` and the two pre-existing clash tests in `tests/test_artifacts.py`,
  `test_fixture_d_finalize_columns_is_deduped_by_name` — no `h5a_` prefix, matching the report exactly).
  Not independently re-run given the time cost of a ~3-minute suite per mutation; the two spot-checks run
  (9(v) and 13(ii)) are the ones the dispatch named explicitly.
- The reference.md § Steps and artifacts split row (`docs/reference.md` around line 1215–1245) exists and
  states the `.csv`/`.parquet` asymmetry Fixture W's `.csv` test cites — read, not re-derived.

## Findings

**Major — the report's mutation 13(ii) failure count is wrong by one, in the exact recurring shape this
slice has already caught once (task 9 mutation (v), corrected 1 → 4 in review `8bc0395`).** The report's
table says *"**375 failed, 48 errors**"* for wrapping every value in `float()` before `_encode_parquet`'s
`pa.table(...)` call. Measured twice, independently, foreground, after clearing stale pytest/`__pycache__`
directories: **376 failed, 2467 passed, 1 skipped, 2 xfailed, 48 errors**, both times. The report's own
header for this table states each count was *"read, not estimated"* — this one wasn't read correctly. It
does not change the report's substantive point (the blast radius is far larger than the two arms the
design names, and every one of those failures is a real run correctly refusing rather than corrupting a
`str`/`bool` cell into a crash), and it does not touch any pin's correctness — the mutation itself isn't a
new pin, it's a blast-radius characterization already covered by arm A/B2, per correction 4/8. But an
off-by-one in a number the report explicitly frames as machine-read, in a slice whose whole product is
"pins that pin," is worth naming rather than silently correcting, on the same rule the report itself
invokes for task 9's mutation (v).

No other discrepancy was found. Correction 2, correction 8, and the Fixture E `.csv`-empty-string finding
all reproduced exactly as claimed; mutation 9(v)'s failure list reproduced exactly (4, matching names);
the suite delta, all four gates, the `.gitignore` restore's scope, and arm D/E's absent editorship all
confirmed by behaviour rather than by reading the report's account of them.

## Suite result

`uv run pytest`: **2891 passed, 1 skipped, 2 xfailed** (baseline 2884/1/2, delta +7 — matches the 7 new
tests, no test edited in place). `uv run ruff check .`: all checks passed. `uv run ruff format --check
.`: 93 files already formatted. `uv run mypy`: success, 52 source files.
