# Task 4 report — `report` renders the findings

## Status
Done. Commit `aa12e21` on `main` (not pushed).

## What was built
`src/publishable/report.py`: a new `_finding_rows(run)` helper reads `run.get("findings")`
(absent/non-list → no rows) and maps each entry verbatim to `{"kind": "finding", "level",
"code", "path", "message"}`, in the record's own order — no sort, no grouping by level, no
re-redaction. `attrition_section` extends its existing `rows` list with `_finding_rows(run)`
after its `_execution_rows` call, following the same `kind`-discriminated idiom as
`metric_n`/`execution`/`provenance_units`/`input_manifest_changed`. Docstring updated to
describe the new row and to state explicitly that a clean run's Attrition table is unchanged.

`tests/test_report.py` gained three tests (in the Attrition block): findings render with
level/code visible; emission order is preserved against a fixture that defeats both a
by-code and a by-level sort; a record with no `findings` key renders identically to one with
`findings: []`, both producing zero `finding` rows.

## Gate (all run in foreground)
- `uv run pytest -q` → **3567 passed, 1 skipped, 2 xfailed in 418.18s** (baseline was 3564
  passed; +3 for the three new tests; skip/xfail counts unchanged).
- `uv run ruff check .` → All checks passed!
- `uv run ruff format --check .` → 101 files already formatted
- `uv run mypy` → Success: no issues found in 56 source files

## Absent-case mutation (real code, `cp` backup, behaviour-verified revert)
Backed up `src/publishable/report.py` to the scratchpad before mutating. Mutation: after
building `_finding_rows`' real rows list, unconditionally appended a phantom row —
`rows.append({"kind": "finding", "level": "warning", "code": "X-PHANTOM", ...})` — regardless
of whether `run` carried a `findings` key.

- Before restoring (mutant in place): `uv run pytest -q tests/test_report.py -k finding` →
  `3 failed, 125 deselected in 14.00s` (all three new tests fail, including the
  no-findings-key test on the phantom row).
- After `cp`-restoring the backup and re-running: `uv run pytest -q tests/test_report.py -k
  finding` → `3 passed, 125 deselected in 1.43s`.
Revert verified by this second run's behaviour, not by `git status`.

## Order fixture sizing
Three entries, not two, because the test must rule out two distinct wrong orderings at once:
emission `[W-ZEBRA(warning), W-ALPHA(error), W-MID(warning)]`. Sorting by `code` ascending
gives `[W-ALPHA, W-MID, W-ZEBRA]` (differs from emission). Sorting by `level` (either
"error" before "warning" alphabetically, or the reverse) moves the middle "error" entry to
an end (differs from emission either direction). A two-element fixture can only ever
distinguish one such alternative; this one distinguishes both at once.

## Swept for pinned output shape
Grepped `tests/test_report.py` for `Attrition`/`five standard sections`/exact title-list
assertions before touching `attrition_section` — found `test_base_report_sections_is_a_
generator_yielding_all_four_standard_sections` and the override-composition test, both
asserting the Attrition section's title and, for the empty-run fixture, its exact `body ==
{"rows": [...]}`. Since `run={}` in those fixtures carries no `findings` key, `_finding_rows`
contributes nothing there, so those pinned assertions were unaffected — verified by the full
suite passing, not by inspection alone. Grepped `README.md` and `docs/*.md` for `findings:`
and for `## Attrition`/`report` output-shape references: no document currently pins the
`findings:` block or its rendering (Task 6 in this slice's plan owns documenting it), so
nothing there needed updating for this task.

## Disagreement with the brief
None. One incidental finding, not a disagreement: `fixture_r`'s own generated project
already emits real warnings (`W-ENV-UNLOCKED`, `W-STATS-STRATUM-THIN`, etc.) that Task 1-3's
wiring now persists into its `run.yaml`, so the "no findings key" test builds its own clean
run by popping the key from a copy of `fixture_r["run"]` rather than assuming the fixture is
clean — noted in that test's docstring.
