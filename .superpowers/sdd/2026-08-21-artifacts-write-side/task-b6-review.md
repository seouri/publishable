# H5a batch 6 (tasks 7–8) — review

Commits reviewed: `44399fd` (task 7), `3b58442` (task 8), `66d4581` (the report), diffed against
`d147f73`.

Gates re-run here, foreground, caches cleared: `ruff check .` clean, `ruff format --check .` — 93
files already formatted, `mypy` — Success, no issues in 52 source files, `uv run pytest -q`
**2879 passed, 1 skipped, 2 xfailed** (185.5s) — the count the report claims, and the +4 delta
(three Fixture M arms, one Fixture D) reconciles exactly against the two briefs. Tree left clean;
every mutation applied below was reverted by restoring a pre-mutation copy (`cp` back from a saved
`/tmp` copy) and re-running the affected selection, never `git checkout --`.

## Verdicts

- **Task 7: PASS.** No findings.
- **Task 8: PASS.** No findings.

Both tasks are built exactly as their briefs specify, both mutations each report claims are real
and reproduce identically under my own re-run, and the one control this batch exists to police —
that the residual named in plan correction 5 is stated and not overclaimed or overcorrected — holds
under a case I built independently before reading the fixture that already covers it.

## What I verified by behaviour, not by reading

**Task 7, real end-to-end run (item 1 of the dispatch).** Built a scratch generated project with a
starter step calling plain `io.record(unit.key, {"measurement": "HIJACK"})` (no `measurement=`) and
ran it through `main(["run", ...])`. The execution ledger records
`'status': 'failed', 'error': 'E-STEP-KEY-COLLISION ContractError: ... may not be named
`measurement`'`, exit code is `EXIT_FAILED`, and no `units.parquet` is written anywhere under the
run directory — the guard fires through the full pipeline, not only via a direct `StepIO` call. A
second scratch run drove the identical key through the `measurement=` branch (with
`data.units.measurements` declared) and got the same code end to end — the `measurement=` branch is
unchanged. A third scratch run recorded the plural `measurements` column plainly and it landed in
`units.parquet` with value `3`, matching Fixture M's arm 3 in-process assertion. (Test file used for
this, `tests/test_h5a_b6_review.py`, was scratch-only and removed before finishing; not part of the
deliverable.)

**Task 7, the prescribed mutation (item 3).** Replaced the plain branch's guard
(`if "measurement" in values:`) with `if any("measurement" in k for k in values):` in
`src/publishable/artifacts.py`. `uv run pytest tests/test_artifacts.py -k fixture_m`: arms 1 and 2
still PASS, arm 3 (`measurements`, plural) FAILS with the same `E-STEP-KEY-COLLISION`, reproducing
the report's claim exactly. Reverted by restoring the saved copy; re-ran the same selection —
3 passed.

**Task 7, § Errors row (item 6).** `docs/reference.md` line 1116's `E-STEP-KEY-COLLISION` row
already reads "...a recorded column named `unit`, or one named `measurement`" with no branch tied
to either name, and neither commit touches `docs/reference.md` at all (`git show <sha> --stat --
docs/reference.md` is empty for both). The row already covered the new emit site before this batch
added it — confirmed by reading the row's wording and by the diffstat showing no doc edit, matching
the report's claim of "no row required widening."

**Task 8, the residual case (item 2, the sharpest instruction in the dispatch).** Built the case
myself, independently, before reading Fixture D's own assertion: a `UnitList` with one `Unit(key="p0",
attributes={"unit": "HIJACK", "site": "n"})`, a plain `io.record("p0", {"score": 1.0})`, then
`finalize()`. Read back `units.parquet`: `[{'unit': 'HIJACK', 'site': 'n', 'score': 1.0}]`. The unit-
key column carries the attribute's value, not the real key `"p0"` — exactly the hijack correction 5
and the report describe, and exactly what Fixture D's own final assertion
(`rows == [{"unit": "HIJACK", "site": "a", "score": 1}]`) already encodes. The report's account is
neither overclaimed (the dedupe genuinely does not close this) nor understated (it does not silently
also fix something the docstring doesn't say it fixes). Routing: `docs/superpowers/spec-defects.md`
is untouched by either commit (confirmed the same way as above), and plan §Corrections correction 5
and the task 8 brief both name task 12 as the filer — task 12 has not run yet in this branch, so an
unfiled defect at this point is correct, not a gap.

**Task 8, both prescribed mutations (item 3).** (a) Replaced `_finalize_columns`'s body with a bare
`return ["unit", *attribute_names, *recorded]`: `uv run pytest tests/test_artifacts.py -k fixture_d`
FAILS on `columns.count("unit") == 1` (`AssertionError: assert 2 == 1`), reproducing the report. (b)
Reverted the helper's body and instead pointed `finalize`'s call site back at the raw inline
concatenation, bypassing the helper: same selection FAILS on `len(calls) == 1` (`assert 0 == 1`) —
the "mutation applied to a proxy" case the brief names, confirmed distinct from mutation (a). Both
reverted by restoring the saved copy; `diff` against the saved copy is empty after each revert, and
the selection re-passes (1 passed) both times.

**Task 8, "the file cannot distinguish the two" claim (Fixture D's own justification for not
asserting on the parquet).** Built both the deduped and the non-deduped call site by hand and wrote
`units.parquet` for the identical hijack case through each. Both are **951 bytes, byte-identical** —
confirming the report's (and the design's) claim that a file-based assertion would pass before and
after the dedupe either way, which is why Fixture D asserts on the column list via a spy instead.

**`by` column survival (item 7).** Re-ran
`test_a_plain_recorded_by_column_survives_into_units_parquet` and
`test_a_measured_by_column_survives_the_collapse_into_units_parquet` after both commits: both pass.
Neither task's diff touches either test or the `by`-handling code path.

**Arm D / arm E (item 8).** Neither commit's diffstat names `tests/test_cli.py` or any file besides
`src/publishable/artifacts.py` and `tests/test_artifacts.py`. Arm D and arm E's `.parquet` half moved
no byte — consistent with the full-suite count moving by exactly +4 and none of `test_cli.py`'s
existing assertions changing.

**Undisclosed drops (item 9).** Diffed each brief's six numbered steps against the two commits'
actual diffs line by line: task 7's steps 1–6 and task 8's steps 1–6 are all present — the guard, the
unconditional-placement comment, the three-arm Fixture M, the prescribed mutation revert, all four
gates, and the exact prescribed commit message (task 7: `git log -1 --format=%B` matches the brief's
message verbatim; task 8 likewise). No brief clause found dropped.

**Grepped claims about other code (item 5).** `_measuring_io` (used by Fixture M arm 2) is a
pre-existing helper (`git log --oneline -- tests/test_artifacts.py` shows it predates both commits in
this batch, first appearing before task 5), not something task 7 invented and mislabeled as
"already passing" — the report's framing of arm 2 checks out. `RESERVED_COLUMNS` is grepped in
neither commit's diff, matching the report's claim that neither guard is re-pointed at it.

## Concerns

None found beyond what the report already discloses. No comment in either diff makes a "this cannot
happen" claim that turned out false under test — task 8's docstring explicitly says the opposite (a
direct caller *can* reach the hijack), and I reproduced that directly.
