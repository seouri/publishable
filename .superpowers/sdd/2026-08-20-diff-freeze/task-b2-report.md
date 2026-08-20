# H8b batch B2 (tasks 1, 2) — report

**Status: complete.** Both tasks done, in order 1 → 2, each committed separately. Nothing in this
batch dispatches — no command reads `probes.jsonl` and no command calls `PHASES`/`replay_ledger` yet.

**Commits:**
- `1fc05dc` — H8b task 1: `replay_ledger` — the baseline, replayed through the shipped `Observations`
- `911fb0c` — H8b task 2: `PHASES`, the four constants, the assert, and every core call site

**Test summary:** baseline `2522 passed, 1 skipped, 2 xfailed` (confirmed by a from-scratch run before
touching anything). After task 1: `2535 passed, 1 skipped, 2 xfailed` (+13 new tests in
`tests/test_apparatus.py`). After task 2: `2539 passed, 1 skipped, 2 xfailed` (+4 more). `mypy` → 47
source files throughout (no new module). `ruff format --check .` → 84 files throughout. `ruff check .`
clean throughout.

## Task 1 — `replay_ledger`

**How the "no reader exists" claim was checked, not carried.** Before writing anything:
`grep -rn "probes.jsonl" src/publishable/` — two hits, `append_observation`'s writer and the literal
string `"apparatus/probes.jsonl"` inside `Observer.block()`. No third hit, no read site. This matches
both `task-1-brief.md`'s and `H8-SCOPING.md`'s stated measurement, re-run at this branch's own HEAD
rather than trusted from `0a636af`.

`replay_ledger(run_dir) -> Observations` lives in `apparatus.py`, beside `append_observation`. It reads
`apparatus/probes.jsonl` line by line, calls the shipped `Observations.record` for each line whose
`phase` is `"run_start"`/`"pre_execution"` (literal strings in task 1; task 2 later points this filter
at the two constants), and returns the accumulated `Observations`. No part of `Observations` was
reimplemented and no keyword was added to `record`. The one refusal is `E-FREEZE-LEDGER-UNREADABLE`
(not valid JSON, not a JSON object, or missing `phase`/`condition`/`facts`); an absent or empty file
returns an empty `Observations` rather than refusing, per the brief's split (that is task 6's
`E-FREEZE-LEDGER-MISSING` to report later, and it needs to cover both "no file" and "a file with no
qualifying line" with the one remedy).

**Tests (13 new, all in `tests/test_apparatus.py`):**
- A real Fixture-P-shaped run (a synthetic installed distribution registering a probe, a
  project-local template declaring `apparatus_probe`/`apparatus_facts`, two swept conditions, driven
  through `run_a_project`/`main(["run", ...])`), asserting `replay_ledger(run_dir).facts_document()`
  equals `run.yaml`'s own `provenance.apparatus.facts`, both read back from the artifacts the real run
  wrote — never asserted as a literal.
- Two conditions scoped independently; `null → value` keeps the value; `value → null` keeps the value;
  a well-formed `freeze` line and a well-formed `dry_run` line both invisible to `facts_document()`; an
  unrecognized future phase skipped rather than refused; each of the three malformed-line shapes
  (not JSON, not a mapping, missing a required key) raising `E-FREEZE-LEDGER-UNREADABLE`; an absent
  file and an empty file both returning `facts_document() == {}`.

**Mutations, both applied by hand against the real code, confirmed, and reverted (verified by
re-running, not by `git status`):**
- **M8** (admit `phase == "freeze"` to the filter): edited the `not in (...)` tuple to include
  `"freeze"`. Result: `test_replay_ledger_excludes_freeze_and_dry_run_lines_from_the_baseline` and
  `test_m8_fixture_a_second_freezes_own_answer_agrees_because_freeze_lines_are_excluded` both **FAILED**
  — the second with `AssertionError: assert ('pinned', 'a', 'b') is None`, i.e. `changed()` now reports
  a contradiction between the freeze-supplied `"a"` and the simulated second freeze's `"b"`, exactly
  the false stop Decision 9 exists to prevent. Reverted; diff against the pre-mutation copy empty;
  full `test_apparatus.py` re-run green (59 passed) immediately after.
- **M9** (reimplement first-answered as most-recent): replaced the `Observations.record(...)` call
  inside the replay loop with an unconditional `observations._first_answered[(condition, fact)] = value`
  assignment. Result: 7 of 59 tests in `test_apparatus.py` **FAILED**, including
  `test_m9_fixture_the_baseline_is_first_answered_not_most_recent`
  (`AssertionError: assert ('pinned', 'r2', 'r1') is None` — baseline became `r2`, contradicting the
  incoming `r1`, exactly the drift the scoping named). Reverted; diff empty; full `test_apparatus.py`
  re-run green (59 passed) immediately after.

**What each mutation's assertion pins, and where the other half lives.** Per the brief, M8's fixture is
only half-assertable here: this batch asserts `replay_ledger`'s own `changed()` result (the internal
state), and task 6 (not yet built) is where the same fixture gets re-run as a `freeze` exit-code
assertion (`0` for both freezes under the shipped exclusion, `1`/`E-APPARATUS-CHANGED` for the second
freeze if the mutation shipped). This report states plainly which half is pinned now: the internal
`changed()` result, not an exit code — there is no `freeze` command yet for an exit code to come from.

## Task 2 — `PHASES`, the four constants, the assert, every core call site

**How the "verbatim write" claim was checked, not carried.** Before adding anything:

```
>>> append_observation(tmp_dir, phase="BOGUS_FIFTH_SPELLING", condition="00", probe="p", facts={})
>>> open(tmp_dir/"apparatus"/"probes.jsonl").read()
{"at": "...", "phase": "BOGUS_FIFTH_SPELLING", "condition": "00", "probe": "p", "facts": {}}
```
Confirmed at this branch's own HEAD (post-task-1, pre-task-2 commit) — the docstring's "closed
vocabulary of four" was unenforced, matching the brief exactly.

**How the two core call sites were enumerated.** Read `cli.py` for `command_run`'s run-start round —
found one call, `observer.observe_round(phase="run_start", condition_index=None)`. Read `runner.py`'s
`execute_plan` for its per-execution round — found one call,
`observer.observe_round(phase="pre_execution", condition_index=execution.condition_index)`. Confirmed
by `grep -rn "phase=" src/publishable/*.py` afterward: three hits total —
`apparatus.py`'s own `phase=phase` inside `append_observation` (not a literal call site) plus the same
two literals just found by reading. No third core call site exists. Reading came first, the grep
second, per the brief's own instruction and `CLAUDE.md`'s proxy warning.

Added `PHASE_RUN_START`/`PHASE_PRE_EXECUTION`/`PHASE_DRY_RUN`/`PHASE_FREEZE` and `PHASES` at module
scope in `apparatus.py`, with the docstring stating both the constants-carry-it argument and the
measured `AssertionError` cost (dated 2026-08-20, from the brief's own prescribed measurement — not
independently re-measured against a live `run` in this batch, since the brief supplies the exact
transcript and the point of this task is the enforcement, not re-confirming H7d Part B's own runner
plumbing a fourth time). `append_observation` now opens with `assert phase in PHASES` as its first
statement, above the `mkdir`. Both call sites converted to the constants;
`replay_ledger`'s filter (task 1) now reads the same two constants instead of literal strings.

**Tests (4 new):** `PHASES`' exact membership against both the constant names and the literal strings;
all four phases each landing their own ledger line via `append_observation`; the fifth-spelling refusal
raising `AssertionError` before the `mkdir` runs, naming the offending value and all four legal names,
with no line written to disk; and a source-inspection test (`inspect.getsource` on `command_run` and
`execute_plan`) asserting each contains `phase=apparatus.PHASE_*` and does **not** contain the bare
literal string it replaced — this is what makes a reversion to a literal fail the suite rather than
only failing silently under `python -O`.

**Mutations, both applied by hand, confirmed, and reverted:**
- **M7** (remove one name from `PHASES`): run once per name (all four), each time editing the
  frozenset literal to drop that one name, then running
  `test_append_observation_accepts_each_of_the_four_named_phases`. All four removals **FAILED** the
  same way — `assert len(lines) == 4` became `assert 3 == 4` — because the removed name's own call now
  raises `AssertionError` before writing its line. Reverted after each of the four, diff against the
  pre-mutation copy empty each time, full `test_apparatus.py` re-run green (63 passed) after the last.
- **M6** (move the assert below the file write): edited `append_observation` to write the ledger line
  first and assert afterward. Result:
  `test_append_observation_refuses_a_fifth_spelling_before_writing_anything` **FAILED** on
  `assert not (tmp_path / "apparatus" / "probes.jsonl").exists()` — `AssertionError: assert not True` —
  the raise still happened (the earlier message assertions passed) but the bogus line was on disk by
  the time it fired, exactly the one-line-off shape the plan names. Reverted; diff empty; full
  `test_apparatus.py` re-run green (63 passed) immediately after.

**No shipped test's count or outcome moved.** Full-suite delta from task 1's 2535 to task 2's 2539 is
exactly +4 (this task's own new tests); nothing else shifted, which is the check the brief names for
whether the constants are equal to the literals they replaced.

## Brief/design/plan vs. code — what was grepped, and what it found

Rather than assert a count of disagreements, here is every claim from the briefs, the design, or the
plan that was checked against the code in this batch, and the check's outcome:

- `task-1-brief.md`: *"grep -rn "probes.jsonl" src/publishable/ finds append_observation's writer and
  Observer.block's recorded path string. No reader exists."* — Re-grepped at this branch's HEAD before
  writing `replay_ledger`: two hits, matches exactly, no reader existed.
- `H8-SCOPING.md` § 113: *"A ledger reader ... absent ... Observations is in-memory, built during a
  run"* — consistent with the above; `Observations` itself is unchanged by this batch (`replay_ledger`
  is a new caller of its existing `record`, not a modification to the class).
- `task-2-brief.md`: *"append_observation(t, phase="BOGUS_FIFTH_SPELLING", …) wrote that string
  verbatim"* — reproduced directly (transcript above) before adding `PHASES`.
- `task-2-brief.md` Step 3: *"Observer._observe_one receives phase from Observer.observe_round, which
  receives it from two callers — cli.command_run's run-start round ... and runner.execute_plan's
  per-execution round"* — confirmed by reading both functions; the grep afterward found the same two
  literal call sites and no others, so this claim held exactly, unlike several prior slices' "grep for
  one spelling" proxy failures this repo has recorded. No third call site was found by either method.
- `task-2-brief.md`: *"Observations.changed's own shipped assert about its caller's ordering, and
  execute_plan's asserts about its callers, are the precedent"* — read directly: `Observations.changed`
  carries its own `assert incoming is None, (...)` (apparatus.py), and `runner.py` carries two asserts
  about `execute_plan`'s own callers (`holdout_train is None or fold_members is None` and the sibling
  `arm_members` line) — both exist as described, confirming the precedent claim rather than assuming it.
- Batch 1's own gate figures (2522 tests, 47 mypy files, 84 formatted files) — reproduced by a
  from-scratch `uv run pytest`/`uv run mypy`/`uv run ruff format --check .` run before any edit in this
  batch, matching the brief's stated baseline exactly.

No check in this list turned up a value different from what the source document claimed. That is
reported as the specific list above, not as a summary count, per the ledger's own instruction not to
repeat a bare "zero disagreements" claim.

## Concerns

None outstanding for tasks 1 and 2 specifically. Two things worth flagging forward rather than fixing
here, since fixing either is out of this batch's scope:
- Task 1's M8 fixture is only half-pinned by this batch (`replay_ledger`'s own `changed()` result, not
  an exit code) — task 6 owns re-running it as a `freeze` exit-code assertion once `freeze` exists, and
  this report states that explicitly so the split is legible rather than silently half-covered.
- `PHASE_DRY_RUN` remains named and called by nothing, consistent with the brief's own statement that
  where a `dry_run` line should be appended is filed to H9 — no action taken here, and none was asked
  for.
