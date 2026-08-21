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
`grep -rn "probes.jsonl" src/publishable/` — **five hits, not two as originally reported here (see
Fix round 1 below)**: `append_observation`'s writer, the literal string `"apparatus/probes.jsonl"`
inside `Observer.block()`, and three docstring mentions elsewhere in `apparatus.py`. No read site
among the five. The substantive conclusion — one writer, one recorded string, no reader — matches
both `task-1-brief.md`'s and `H8-SCOPING.md`'s stated measurement; only the hit count in this
report's first version was wrong.

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
by `grep -rn "phase=" src/publishable/*.py` afterward: three hits total — the same two literals just
found by reading, plus one more inside `apparatus.py` itself: `Observer._observe_one`'s own call
**to** `append_observation`, passing `phase=phase` through (not, as this report first said,
`append_observation` receiving it — `append_observation` receives the value under its own parameter
name and passes it nowhere; see Fix round 1 below). No third core call site exists. Reading came
first, the grep second, per the brief's own instruction and `CLAUDE.md`'s proxy warning.

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
  writing `replay_ledger`: **five hits within `apparatus.py`** (the writer, the recorded path string,
  and three docstring mentions), not the two this report first stated (Minor 1, closed in Fix round 1
  below) — the brief's own two-hit count is itself under-counting the same way, but the substantive
  claim, no reader existed, held exactly.
- `H8-SCOPING.md` § 113: *"A ledger reader ... absent ... Observations is in-memory, built during a
  run"* — consistent with the above; `Observations` itself is unchanged by this batch (`replay_ledger`
  is a new caller of its existing `record`, not a modification to the class).
- `task-2-brief.md`: *"append_observation(t, phase="BOGUS_FIFTH_SPELLING", …) wrote that string
  verbatim"* — reproduced directly (transcript above) before adding `PHASES`.
- `task-2-brief.md` Step 3: *"Observer._observe_one receives phase from Observer.observe_round, which
  receives it from two callers — cli.command_run's run-start round ... and runner.execute_plan's
  per-execution round"* — confirmed by reading both functions; the grep afterward found those same two
  literal call sites plus one further `phase=` hit that is not a third call site
  (`Observer._observe_one`'s own pass-through call to `append_observation` — Minor 2, closed below),
  so the claim held exactly at the level it was making (two callers of `observe_round`), unlike several
  prior slices' "grep for one spelling" proxy failures this repo has recorded.
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

---

## Fix round 1

Reviewed at `2ccd10b`; review at `.superpowers/sdd/2026-08-20-diff-freeze/task-b2-review.md`.
Spec compliance PASS; task quality PASS with findings — three Majors, four Minors. All three Majors
closed here; Minors 1 and 2 (report corrections) closed; Minors 3 and 4 (optional) also closed, cheaply.

### Major 1 — M7's test iterated the set under test; rebuilt to iterate the four literal spellings

`test_append_observation_accepts_each_of_the_four_named_phases` looped over `sorted(PHASES)` — the
mutated value itself — so a removed name was never passed to `append_observation`, and the follow-up
assertion (`{...} == set(PHASES)`) compared against the mutated set and was vacuous. Rebuilt to loop
over the four literal strings `("run_start", "pre_execution", "dry_run", "freeze")`, independent of
`PHASES`, with the assertion tightened to an ordered list rather than a set (so a duplicate or
reordered write would also show).

**Verified by running all four removals again**, each reverted by editing back and confirmed clean by
`diff` before the next: dropping `PHASE_RUN_START` → `AssertionError: append_observation got phase
'run_start', which is not one of the four named phases: dry_run, freeze, pre_execution`; dropping
`PHASE_PRE_EXECUTION` → same shape at `'pre_execution'`; dropping `PHASE_DRY_RUN` → same shape at
`'dry_run'`; dropping `PHASE_FREEZE` → same shape at `'freeze'`. Every one now fails **inside
`append_observation`**, at **its own removed name**, not through the arithmetic `len(lines) == 4`
check the original version relied on.

### Major 2 — the run-start half of the dated measurement was false; deleted, not rewritten

Re-measured independently (not copied from the review) by patching `apparatus.append_observation` to
raise on the Nth call and driving a real `run` through `main(["run", …])` on a Fixture-P-shaped
project:
- Raised on the **first** call (the run-start round): run-directory root
  `['environment', 'manifest', 'sweep.yaml']` — **`apparatus/` is absent**, `lock` absent (never
  created), `run.yaml`/`executions.jsonl` absent. This confirms the review's finding and falsifies the
  docstring's prior claim that the root "holds `apparatus/`, `environment/`, `manifest/`, `sweep.yaml`"
  at that fire — it cannot, since the assert is `append_observation`'s first statement, above the
  `mkdir` that would create that directory.
- Raised on the **fourth** call (two run-start calls, then the first execution's `pre_execution`
  call): root `['apparatus', 'conditions', 'environment', 'executions.jsonl', 'manifest',
  'sweep.yaml']`, `executions.jsonl` holds **1** line, `run.yaml` absent, `lock` absent (removed). This
  confirms the review's finding that this half was accurate.

**Repair, preferring deletion to rewriting per `CLAUDE.md`:** the run-start sentence's enumerated
survivor list (`apparatus/`, `environment/`, `manifest/`, `sweep.yaml`) was deleted outright rather
than corrected to a shorter list or annotated — the sentence now states only what was measured and
holds for both fires without qualification: uncaught traceback, `lock` removed, `run.yaml`/
`executions.jsonl` absent. No claim about directory contents remains in that sentence.

**The surviving shape is now pinned by two new tests**, not left only in the docstring (the review's
own note that "no test asserts the surviving shape"):
`test_the_run_start_fire_leaves_no_run_yaml_no_executions_and_no_lock` and
`test_a_later_pre_execution_fire_leaves_one_paid_execution_and_no_run_yaml`, both driving a real run
with `append_observation` monkeypatched to raise on the first/fourth call respectively, asserting the
measured survivor shape directly on the run directory.

### Major 3 — carried forward into task 4, not fixed here

`replay_ledger`'s `E-FREEZE-LEDGER-UNREADABLE` guard checks key presence only. Reproduced the review's
three probes directly: `facts: null` and `facts: [1, 2]` both raise a bare `AttributeError` out of
`Observations.record` rather than being refused, and `condition: 42` is accepted silently and yields
an int-keyed baseline (`{42: {...}}`) that reads as "never answered." This is task 4's refusal set to
extend (`isinstance(doc["facts"], Mapping)` and `isinstance(doc["condition"], str)`, under code that
already exists), not this batch's to fix — task 1 is done and dispatches nothing.

**Carried forward, not left as a ledger line calling itself "filed."** `docs/superpowers/plans/2026-08-20-diff-freeze.md`
§ Task 4, Step 9, gained a new sub-bullet directly under the existing `E-FREEZE-LEDGER-MISSING` bullet,
stating the two escaping shapes, why each matters (a fail-open `freeze` could adopt a pin it should
have refused to compute), the § Errors row's stated cause this gate cannot currently honour, and the
concrete repair. Task briefs are extracted from the plan (`CLAUDE.md` § The development record), so
this is where task 4's author will meet it — not a `spec-defects.md` entry naming a slice as owner
before that slice's own plan carries the finding, which is the shape `CLAUDE.md` names as an unfiled
filing.

### Minor 1 — report's `probes.jsonl` grep count corrected

Re-ran `grep -n "probes.jsonl" src/publishable/apparatus.py` at commit `6b4bcd2` (pre-task-1): **five**
hits — the writer, `Observer.block`'s recorded path string, and three docstring mentions (lines 419,
447, 553 at that commit) — not the two originally reported. The substantive conclusion (one writer,
one recorded string, no reader) was and remains correct; only the count was wrong. Both places in the
report that repeated the two-hit figure are corrected, with a note that the brief's own count is the
same under-count and the claim that matters — no reader existed — held regardless.

### Minor 2 — report's third `phase=` hit mislocated

The report said the third `grep -rn "phase=" src/publishable/*.py` hit was "`apparatus.py`'s own
`phase=phase` inside `append_observation`." Re-checked by reading: that hit is at
`Observer._observe_one`'s own call **to** `append_observation` (`apparatus.py:731` at the time of the
original report), passing `phase=phase` through as a keyword argument — `append_observation` itself
receives the value under its own parameter name and passes `phase` nowhere. Both places in the report
that named the wrong function are corrected.

### Minor 3 (optional, closed) — the call-site pin's scope stated honestly

`test_cli_and_runner_call_sites_pass_the_named_constants` inspects exactly `command_run` and
`execute_plan`'s source; a third literal call site added elsewhere in `src/publishable/` would not be
caught by this test alone (confirmed conceptually by the review; not independently re-run here since
the review's own repro — adding an unrelated function with a bare literal call — was accepted at face
value as a straightforward claim about what `inspect.getsource` on two named functions can and cannot
see). Docstring extended to say so explicitly, attributing completeness to the reading-then-grep
enumeration rather than to this assertion.

### Minor 4 (nit, optional, closed) — cross-function locator replaced

The `PHASES` docstring's "the assert below" (pointing at `append_observation`, ~60 lines away) is now
"the assert in `append_observation`" — a self-maintaining reference per `CLAUDE.md` § Habits, not a
positional one that breaks if either function moves.

### Mutations re-verified against the full, unfiltered suite after the fix

All four mutations were re-applied to the post-fix code (not the pre-fix snapshot), run against the
**full suite** (not `test_apparatus.py` alone), reverted by editing back, and the revert confirmed by
`diff` against a pre-mutation copy before the next mutation:

| Mutation | Full-suite result | Matches original report? |
|---|---|---|
| M6 (assert moved below the write) | 1 failed (`test_append_observation_refuses_a_fifth_spelling_before_writing_anything`, on `assert not …exists()`), 2540 passed | Yes |
| M7 (drop `PHASE_FREEZE`, rebuilt test) | 3 failed (`test_phases_is_exactly_the_four_named_constants`, `test_append_observation_accepts_each_of_the_four_named_phases`, `test_append_observation_refuses_a_fifth_spelling_before_writing_anything`), 2538 passed — the second now failing **inside `append_observation` at `'freeze'`**, verified separately by an isolated re-run | Mechanism now correct; count differs from the original (unfixed) report because the rebuilt test also trips `test_phases_is_exactly_the_four_named_constants`, which the loop-over-`PHASES` version did not |
| M8 (admit `PHASE_FREEZE` to `replay_ledger`'s filter) | 2 failed, 2539 passed | Yes |
| M9 (first-answered → unconditional most-recent) | 7 failed, 2534 passed | Yes |

Final state after all four reverts: `diff` against the pre-fix-round snapshot clean; full suite
**2541 passed, 1 skipped, 2 xfailed**; `ruff check .` clean; `ruff format --check .` 84 files;
`mypy` 47 source files.

### What was not independently re-verified

The review's own Minor-3 repro (adding an unrelated function with a bare literal `phase="run_start"`
call and confirming the suite stays green) was not re-run here; the fix accepted the review's claim
about what the source-inspection test can and cannot see, since re-deriving it would only reproduce a
finding already verified by the review's own hand-run.
