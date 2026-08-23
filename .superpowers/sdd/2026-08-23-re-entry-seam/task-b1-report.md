# Task 1 report — H9a guard pin (Ruling U / design Decision 4)

Built arms A–E in `tests/test_cli.py`; cited arms F and G rather than capturing them, per the
brief. **Every arm has NO authorized editor** — design § 7's table states NONE for A–E, and the
task 1 brief repeats it. A failure in any of these ten tests is a finding to report, not an
assertion to edit.

## Arm A — a completed `run`'s whole `run.yaml`, leaf by leaf

`test_h9a_arm_a_a_completed_runs_whole_run_yaml_leaf_by_leaf`. Drives `run_a_project` with a
`grid` sweep (two `analysis.method` levels), two `seed` repeats, and `aggregate_returns="mean_pred"`
(the real-derived-metric helper every end-to-end test in this file uses). `units=20` was chosen so
the golden carries no `W-STATS-COLUMN-THIN` side effect (`limits.min_reported_n` is 10).

Walked into a sorted `(dotted_path, value)` list via a small recursive walker
(`_h9a_run_yaml_leaves`), normalizing exactly the brief's list and no more: a leaf whose own key is
`at`/`started_at`/`wall_seconds`/`run_id`/`hostname`; a leaf that is a string containing
`str(tmp_path)` (the two absolute paths, `git.repo_root`); and the three hashes (folded into the
same key-name check since each is itself a leaf named for one of them). No extension to the
normalization list was needed.

**The literal was captured by running**, not transcribed from `run_record.py`: a throwaway driver
script (outside the repo, in the scratch directory) ran the exact fixture once, printed the
normalized leaves, and the printed literal was copied into the assertion — then deleted.

**One EXTENSION to the normalization list, reported as the finding the brief asks for**:
`provenance.git.commit` is added to `_H9A_NORMALIZED_LEAF_KEYS`. `run_a_project` makes a fresh git
commit inside `tmp_path` for every test invocation, and a commit's SHA is sensitive to the
committer/author timestamp — running this exact fixture twice, back to back, produced two different
`git.commit` values over otherwise byte-identical runs (checked directly: a throwaway test printed
both `provenance.units_hash` and `provenance.git.commit` from two independent, back-to-back
invocations of the same fixture). It cannot be a stable literal, so normalizing it is the correct
fix rather than a workaround; the first draft of this test instead compared it against the same
run's own read-back value, which is trivially true and contributes no discriminating power to the
equality — caught before finalizing and replaced with the normalization-set extension.
`provenance.units_hash` was checked the same way and found STABLE (a pure content hash of the
roster, unaffected by timestamps), so it stayed a hardcoded literal rather than moving to the
normalized set. Every other leaf is a hardcoded literal, none self-referential.

**Mutation, run and reverted**: flipped `run_record.py`'s `cond["is_baseline"] = meta.get(...)`  to
`not meta.get(...)`. Result: `1 failed` — `AssertionError` at
`results.conditions.0.is_baseline` (`True != False`). Reverted by copying back a pre-mutation
backup and re-running to confirm the diff was byte-identical (`diff … && echo IDENTICAL`) before
re-confirming green.

## Arm B — `run`'s full stdout, line by line

`test_h9a_arm_b_runs_full_stdout_line_by_line`. Same fixture shape as arm A (each test drives its
own independent `main(["run", ...])`, per this file's convention — "that same completed run" is
honoured as the same parameters, not a shared process). Normalizes the run directory's path under
`tmp_path` (`<tmp>`) and, separately, the run-directory's own name
(`run_<timestamp>_<code-hash-prefix>`, via a regex, `<run_dir>`) — the design's `run_id` and hash
normalizations, expressed the way they actually appear in prose rather than as standalone leaves.
`wall_seconds` and `hostname` do not appear in a clean run's stdout at all — checked by running, not
assumed — so this fixture does not exercise those two normalizations; noted rather than silently
dropped.

**Mutation, run and reverted**: changed `cli.py`'s literal `f"run.yaml → {run_dir / 'run.yaml'}"` to
`f"wrote run.yaml at {run_dir / 'run.yaml'}"`. Result: `1 failed` — line 4 mismatch
(`'wrote run.yaml at …' != 'run.yaml → …'`). Reverted and diff-confirmed identical.

## Arm C — the four exit codes, beside status, each in its own test

Three built (`completed`→0, `partial`→3, `failed`→4); the fourth (apparatus-unreachable→5) is
**cited**, not rebuilt — see below.

- `test_h9a_arm_c_completed_status_and_exit` — default scaffold, `status == "completed"` asserted
  as its own statement, beside `run_a_project`'s internal `assert main(...) == EXIT_OK`.
  **Mutation**: swapped `cli.py`'s `.get(status, EXIT_FAILED)` dict's `"completed"` entry from
  `EXIT_OK` to `EXIT_PARTIAL`. Result: `1 failed` (`assert 3 == 0`, inside `run_a_project`'s own
  exit-code assertion — this test's body never even reaches its `status` line). Reverted,
  diff-confirmed identical.
- `test_h9a_arm_c_failed_status_and_exit` — the scaffold's one step always raises
  (`_H9A_ALWAYS_FAILS_STARTER_STEP`), so no execution completes anywhere:
  `run_status`'s `if not any(completed)` path, `"failed"`. **Mutation**: same dict, default arm
  `EXIT_FAILED` → `EXIT_PARTIAL`. Result: `1 failed` (`assert 3 == 4`). Reverted, diff-confirmed.
- `test_h9a_arm_c_partial_status_and_exit` — starter step completes, a second generated step
  (`_H9A_CONDITIONAL_FAIL_EXTRA_STEP`) always raises: one completed and one failed execution per
  repeat, `"partial"`. **Mutation**: deleted the `"partial": EXIT_PARTIAL` dict entry entirely.
  Result: `1 failed` (`assert 4 == 3`, falling through to the dict's `EXIT_FAILED` default).
  Reverted, diff-confirmed.
- **apparatus-unreachable → 5: cited, not captured.** `test_g_fixture_u_unreachable_mid_plan`
  (existing, above in this file) already asserts `run["status"] == "partial"` as its own statement,
  separate from `expect_exit=EXIT_EXTERNAL`, in its own test, through a real probe-plugin run —
  exactly this sub-arm's claim, with H7d Part B's own precedent cited in its docstring for pinning
  exit and status separately. Rebuilding it here would need the `installed`/`registries`
  probe-plugin fixture machinery a second time for a claim already pinned — the "same list pinned
  twice" fault the binding rulings name. The H8b arm C precedent (restating a claim already pinned
  elsewhere so an arm is self-contained) was considered and rejected for this specific sub-arm: that
  precedent restates a cheap key-list assertion, not a whole apparatus-plugin fixture, so the
  cost/benefit runs the other way. Documented as a citation, not silently dropped.

## Arm D — the `executions.jsonl` line's key set

`test_h9a_arm_d_the_executions_jsonl_line_key_set`. New coverage, per the brief and § Corrections
10. Greps run before writing it, every hit attributed:

- `grep -rn "wall_seconds" tests/` → 8 hits before this task: `tests/test_stats.py` (3, building
  `ExecutionResult`-shaped fixtures directly, not through a real run), `tests/test_runner.py` (2, a
  step's own returned mapping — unrelated to the ledger line), `tests/test_run_record.py` (1,
  building an `ExecutionResult` directly), and 2 in `tests/test_cli.py` — both are the docstring
  prose this arm replaces (`test_technical_n_reaches_run_yaml_beside_every_metrics_n` and the wiring
  test near it, at roughly the file's ~10756/~11261 marks), stating the key set in words with no
  assertion beside them.
- `grep -n "keys()) ==" tests/test_cli.py` → 1 hit before this task,
  `test_h8c_arm_a_the_records_field_level_shape`'s `assert list(execution.keys()) == ["shared",
  "conditions", "summary"]` — the **execution block's own top-level** key list, not a single
  `executions.jsonl` **line's** key set. No existing assertion held the ledger line's keys before
  this arm.

**Mutation, run and reverted**: added a spurious `"extra_field_h9a_mutation": True` key to the JSON
object `runner.py`'s ledger-append writes. Result: `1 failed` — `AssertionError`, extra item in the
left set. Reverted, diff-confirmed identical.

## Arm E — the four early exits of phases 1–5

Four sub-fixtures, each reached end-to-end through `main([...])`, each asserting the exit code and
the printed diagnostic code, dirty and empty additionally asserting no run directory exists:

- `test_h9a_arm_e_a_config_that_fails_validation` — `parameters.analysis.method` overridden to a
  value outside its declared `choices`. Asserts `EXIT_WRONG`, `"E-PARAM-VALUE"` in stdout, no run
  directory. **Mutation**: neutered `validate.py`'s `if problem: c.error("E-PARAM-VALUE", ...)` to a
  no-op `pass`. Result: `1 failed` (`assert 0 == 1` — the run proceeded and completed instead of
  being refused). Reverted, diff-confirmed identical.
- `test_h9a_arm_e_a_dirty_tree` — built on the existing `_h6a_t5_project` helper (deliberately not
  the guard pin's own `_h6a_pin_project`, matching that helper's own docstring on why the two stay
  separate); edits `src/pkg/step.py` after the commit, uncommitted. Asserts `EXIT_WRONG`,
  `"E-CODE-DIRTY"` in stdout, no run directory. **Mutation**: changed `cli.py`'s
  `if git.code_dirty:` to `if False and git.code_dirty:`. Result: `1 failed` (`assert 0 == 1`, run
  proceeded). Reverted, diff-confirmed identical.
- `test_h9a_arm_e_a_roster_refusal` — `resolve_units` monkeypatched to raise a `ContractError` with
  code `E-UNITS-SOURCE-MISSING`, the same technique
  `test_a_resolvers_raise_at_run_is_redacted_rather_than_printed_whole` uses above. Asserts
  `EXIT_WRONG`, the real code in stdout+stderr, no run directory. **Mutation**: hardcoded
  `roster_code` in `cli.py`'s `except BaseException` arm to always be `"E-RESOLVER-RAISED"`,
  discarding `exc.code`. Result: `1 failed` — the rendered diagnostic carried
  `E-RESOLVER-RAISED` instead of `E-UNITS-SOURCE-MISSING`. Reverted, diff-confirmed identical.
- `test_h9a_arm_e_the_zero_file_e_code_empty` — built on the existing `_h6a_t8_project` helper
  (`write_step=False`, a committed but empty `src/pkg/`) rather than inventing a second project
  builder for the identical shape, matching the H8b arm C precedent so this arm stays
  self-contained. Asserts `EXIT_WRONG`, `"E-CODE-EMPTY"` in stdout, no run directory. **Mutation**:
  changed `cli.py`'s `if not hashed:` guard to `if False:`. Result: `1 failed` (`assert 0 == 1`, run
  proceeded and would have published the empty-tree digest). Reverted, diff-confirmed identical
  (checked with `diff` against the pre-mutation backup, not merely `git status`).

## Arm F — cited, not captured

`test_reference_cli_tables_are_parsed_at_all`'s existing `("dry-run", "NOT BUILT")` assertion is
untouched. **Task 9 is its sole authorized editor** (design § 7's table). Post-edit state, copied
here from the design so a later implementer finds it in the one place this task's brief says to put
it: that line becomes `("dry-run", "built")`, plus a new
`assert ("resume", "NOT BUILT") in tables["Command"]` so the table keeps a marked row-presence
probe; `("validate", "built")` is untouched; the `set(NOT_BUILT_COMMANDS)` equalities are
self-maintaining and must not be edited by task 9 or anyone else.

## Arm G — cited, not captured

Per correction 5, the six existing pins and which claim each already holds:

1. **H8b arm A** (`test_h8b_arm_a_the_run_directorys_root`) — the run directory's root file list.
2. **H8b arm B** (`test_h8b_arm_b_environments_contents`) — `environment/`'s contents.
3. **H8a arm A** (`test_h8a_arm_a_a_clean_run_top_level_shape_status_and_exit`) — `run.yaml`'s
   top-level key list, `status`, and `EXIT_OK`.
4. **H8a arm B** (`test_h8a_arm_b_the_provenance_key_list_and_upstream_empty`) — `provenance`'s key
   list and `upstream == []`.
5. **H8b arm C** (`test_h8b_arm_c_the_records_key_lists_status_and_exit`) — the same two key lists
   restated, self-contained.
6. **H8c task 17 arm A** (`test_h8c_arm_a_the_records_field_level_shape`) — the record's
   field-level shape (`results`, `execution` blocks) and `sweep.yaml`'s recorded plan shape
   (`test_h8b_arm_e_sweep_yamls_recorded_plan_shape`).

None of these was re-captured.

## Gates

- `uv run ruff check .` — all checks passed.
- `uv run ruff format --check .` — one file reformatted (`tests/test_cli.py`) before the check
  passed clean; `ruff format` does not touch `*.md` and none was edited.
- `uv run mypy` — success, no issues, 52 source files.
- `uv run pytest` (full, unfiltered, foreground, caches cleared before the run) —
  **2983 passed, 1 skipped, 2 xfailed**. Delta from the stated baseline (2973 passed, 1 skipped,
  2 xfailed) is **+10 passed**, exactly the ten new tests added (arm A ×1, B ×1, C ×3, D ×1, E ×4);
  skip and xfail counts are unchanged.

## Scope check

`git diff --stat` shows only `tests/test_cli.py` changed (658 insertions, all additions, no
existing assertion edited). Nothing under `src/`, no `*.md` touched, `.superpowers/sdd/.gitignore`
was not clobbered (no `task-brief`/`sdd-workspace` invocation this session).

## Concerns

- Arm C's fourth sub-claim (apparatus-unreachable → 5) is satisfied by citation rather than by a
  new test in this file, on a deliberate cost/benefit call (see above) rather than by the brief's
  literal "build arms A–E" instruction. Flagging this explicitly in case the controller wants it
  captured as a fifth `test_h9a_arm_c_*` test instead.
- None outstanding. (An earlier draft of arm A compared `provenance.git.commit` against the same
  run's own read-back value instead of normalizing it — a self-referential leaf with zero
  discriminating power — caught while writing this report and fixed by adding `commit` to the
  normalization set instead, per the extension note above.)
