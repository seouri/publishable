# Task 7 — close the branch

Status: PASS. No disagreements found.

## Full gate (measured 2026-08-28/29, commit 7617c14 base)

- `uv run pytest -q`: 3567 passed, 1 skipped, 2 xfailed (baseline was 3554 passed, 1 skipped, 2 xfailed — the slice added 13 tests, all green)
- `uv run ruff check .`: All checks passed!
- `uv run ruff format --check .`: 101 files already formatted
- `uv run mypy`: Success: no issues found in 56 source files

## The two pins

- `tests/test_cli.py::test_task1_bit_stability_oracle_over_the_correction_machinery` — PASSED (1 passed)
- `tests/test_cli.py::test_every_run_path_finding_is_disclosed_not_just_printed` — the source-level pin asserting no `print(<collector>.render())` remains in `_prepare_run`/`_execute_prepared` — PASSED (1 passed)

## Both consistency passes (README.md, docs/design-principles.md, docs/experimental-designs.md, docs/reference.md)

- **Mechanical**: links/anchors — built a GitHub-accurate slugger (strip backticks only, drop non-word/non-space/non-hyphen chars including `&`, `/`, `.`, `—` without collapsing repeated separators, replace each whitespace char with its own hyphen) and checked every `[text](file#anchor)` link across the four docs. 0 broken anchors, 0 duplicate anchors. (A naive slugger that collapses whitespace falsely flags ~39 double-hyphen anchors like `#secrets--credentials`, `#within-subjects--repeated-measures` — all of those resolve correctly under GitHub's real rule.) Trailing whitespace/tabs: none. Invisible unicode: none. Table column-count check flagged 4 rows, all false positives from escaped `\|` inside cell prose (not real column mismatches, verified by inspection).
- **Cross-document**: `findings:` block, `W-ENV-UNLOCKED`'s no-path message, and the `run`/`draft`/`resume`-persist vs. other-commands-print distinction are stated consistently across `reference.md` §§ "The two files", "Warnings core reports", "CLI reference", and `design-principles.md`. No stale repository-path wording found anywhere in the four documents.

## Sibling repo end-to-end proof (`2026-08-28-gcl-measurement`, editable path dependency on this working tree)

- `uv run pytest -q`: 212 passed.
- E01 (`configs/e01-reference-gate/config.yaml`): printed no warnings; `run.yaml` has no `findings:` key. Agree (both empty).
- E02 (`configs/e02-utilization-baseline/config.yaml`): printed no warnings; `run.yaml` has no `findings:` key. Agree (both empty).
- E06 (`configs/e06-comparator/config.yaml`): printed no warnings; `run.yaml` has no `findings:` key. Agree (both empty).

| config | printed codes | recorded codes |
|---|---|---|
| e01-reference-gate | (none) | (none — no `findings:` key) |
| e02-utilization-baseline | (none) | (none — no `findings:` key) |
| e06-comparator | (none) | (none — no `findings:` key) |

All three configs run clean in this sibling repo: it carries its own `uv.lock` (no `W-ENV-UNLOCKED`) and none of the three trips `W-APPARATUS-UNANSWERED` or any other warning. The printed/recorded agreement holds trivially (empty = empty) for all three; the slice's claim — that whatever a run prints, the record now carries in the same order — was not exercised against a *non-empty* case here, because none of E01/E02/E06 produces any finding. `uv run publishable report` on the E06 run.yaml renders cleanly with no `finding` rows, consistent with the empty `findings` block; `src/publishable/report.py::_finding_rows` (confirmed present, lines 498-519) is the renderer that would emit `kind: finding` rows if any existed.

## Disagreements

None. All three example runs are in perfect agreement on the empty case; the finding-rendering code path exists and is wired in but was not exercised live since none of the three designated configs currently emits a warning.
