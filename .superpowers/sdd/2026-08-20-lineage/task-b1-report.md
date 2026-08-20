# Batch B1 report — task 11 (guard pin) then task 1 (`lineage.py` reader)

Branch `h8a-lineage`, off `main` at `28e311d` (this session created the branch).

## Commits

- `1f55711` — H8a task 11: pin the record shape, the scope routing and the shipped read
  before anything moves
- `00bf45f` — H8a task 1: lineage.py and read_run_record — the run.yaml reader nothing in
  src/ has

## Test summary

Baseline `2456 passed, 1 skipped, 2 xfailed`. After task 11: `2460 passed` (+4: arms A, B,
C, D). After task 1: `2470 passed` (+10 in `tests/test_lineage.py`). Final full run:
**2470 passed, 1 skipped, 2 xfailed**, `ruff check` clean, `ruff format --check` → **84
files**, `mypy` → **47 source files** — both gate deltas match the plan's corrections 7
exactly (mypy 46→47, formatter 82→84, moved by `lineage.py`/`tests/test_lineage.py` and
nothing else).

## The four arms, and how each literal was captured

All four were captured by **running** (`uv run python` against a scratch script driving
`tests.test_cli.run_a_project` directly, then reading the produced artifacts back), not
transcribed from `run_record.py`:

- **Arm A** — a clean run (`units=8`, `replication: {repeats: [{kind: seed, n: 2}]}`):
  `run.yaml` top-level keys, in order, `['schema_version', 'run_id', 'status', 'draft',
  'config', 'parameters_hash', 'code_hash', 'provenance', 'layout', 'execution',
  'results']`; `status == "completed"`; `len(executions.jsonl) == len(sweep.yaml
  execution_order)` (both 2). Matches the brief exactly.
- **Arm B** — the same run's `provenance` key list, twelve keys ending in
  `allocation_hash`, with `upstream` absent. Matches the brief exactly. Its test's
  docstring names task 7 as the sole authorized editor, permitted to append
  `"upstream"` after `"allocation_hash"` with nothing reordered, and states that any
  other task finding this arm failing has a finding to report, not an assertion to edit.
- **Arm C** — two real runs (one `run`-scoped generated step, one `summary`-scoped one),
  driven with `extra_steps=["step09_publish"]` and a monkeypatched `extra_step_source`.
  Measured: the generated step's actual name was **not** `step09_publish` (confirms
  plan correction 8 — `run_a_project` prefixes it), read back from the run's own
  `execution` block rather than assumed. The `run`-scoped step's entry landed in
  `execution.shared` with its artifact at `shared/<name>/cohort.json`; the
  `summary`-scoped one's entry landed in `execution.summary` with artifacts at
  `summary/<name>/programs/a.json` and `summary/<name>/programs/gpt-4.1__seed29.json`.
  The test asserts both the routing and the on-disk paths.
- **Arm D** — `read_upstream("step01", "ok.json")`, built with the shipped `make_io`
  helper in `tests/test_artifacts.py` (a `step01` step writing under `shared/`, read
  back through the ordinary `run`-scoped path an existing shipped test already
  exercises), returns `{"ok": True}`. Added beside the shipped `read_upstream` tests as
  the brief specified.

## Task 11 mutation

Added `"stopped_at": None,` to the `provenance` dict literal in `cli.py`
(`command_run`). Full suite: **arm B FAILED** on the key-list assertion (`AssertionError:
... Left contains one more item: 'stopped_at'`), **arm A PASSED**. Reverted by editing
the line back out (diffed byte-identical against a pre-mutation copy); re-ran the full
suite and confirmed **2460 passed** (before task 1 landed).

## Task 1 mutations

1. **Blind, as prescribed.** Replaced the imported `SCHEMA_VERSION` with the literal
   `"1.0"`. Full suite stayed green at 2470 passed — confirmed rather than assumed. Not
   offered as a pin; what pins the import is that no assertion in this slice hard-codes
   a version string, so a future bump moves one line in `lineage.py` alone.
2. **Discriminating.** Made the `run_id`-presence check unreachable (`if False and
   "run_id" not in doc:`). `tests/test_lineage.py::test_a_mapping_with_no_run_id_is_record_unreadable`
   FAILED (`DID NOT RAISE ContractError`) while the other 9 tests in that file still
   passed. Reverted; full suite re-run confirmed 2470 passed again, diff against the
   pre-mutation file byte-identical.

## Disagreements between a brief/design/plan and the code

None found. Every literal named in task 11's and task 1's briefs was re-verified by
running rather than assumed:

- Grepped `docs/superpowers/specs/2026-08-20-lineage-design.md` and
  `docs/superpowers/plans/2026-08-20-lineage.md` for the claims task 1's brief repeats
  (the import-direction argument, the three-refusal table, the "not refused for
  partial/failed" rule) — all consistent with what `grep -rn run_record
  src/publishable/` and the measured `run_record → runner → artifacts` chain show at
  this commit.
- Confirmed `errors.py`'s `ArtifactError` docstring still reads "Core will not write
  this" and § Errors core raises still carries the same gloss — per the brief, this is
  task 9's fix, not touched here, and no false claim was repeated in `lineage.py`
  (`ContractError` is what task 1 raises throughout, not `ArtifactError`, so the false
  gloss is not even adjacent).
- Confirmed via `grep -rn "reuse_from" src/publishable/` that it is still zero — task 1
  builds no part of `io.reuse_from` and nothing here is reachable from a step.

## Concerns

None. Both tasks' gates are clean; task 11's arm B is a bounded, named-editor pin ready
for task 7; task 1's reader imports `SCHEMA_VERSION` rather than restating it, and its
docstring states the import direction and the measured cycle that makes the reverse
direction impossible, with no count or call-site enumeration.
