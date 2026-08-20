# Batch B1 report — tasks 12, 1

**Commits:** `2a10c3a` (task 12), `a59ef6f` (task 1).

## Status

Both tasks done, in order 12 → 1, each its own commit. All four gates clean after each commit.
Baseline at `814eadd`: 2423 passed, 1 skipped, 2 xfailed. After task 12: **2426 passed** (+3), 1
skipped, 2 xfailed. After task 1 (docs only, no test-count change): still 2426/1/2.

## Task 12 — the guard pin

Added to `tests/test_cli.py`: `test_a_clean_run_completes_with_the_full_run_yaml_shape` (arm A),
`test_an_all_completed_truncation_stays_completed_at_exit_0` (arm B), `test_a_mixed_truncation_is_partial_at_exit_3`
(arm C), plus the `_RECORDS_ONCE_THEN_RAISES_STEP` fixture the brief specifies for arm C.

**The three arms' captured literals, and how each was captured** — by running, at this branch's
point (code identical to `814eadd`, only docs commits sit on top), not transcribed from
`run_record.py`:

- **Arm A, a clean run.** `run_a_project(tmp_path, capsys=capsys, units=8, replication={"repeats":
  [{"kind": "seed", "n": 4}]})`. Ran it, read `run.yaml` and `sweep.yaml` back:
  `len(executions.jsonl) == len(sweep.yaml["execution_order"]) == 4`, `run.yaml status ==
  "completed"`, exit `0` (asserted implicitly — `run_a_project`'s own `expect_exit=EXIT_OK` default
  asserts it), the full top-level key list in order matches the brief's list exactly, and
  `results_dir` holds exactly `{"latest", "run_<id>"}`. Default replication is `seed n=5` (read
  from a generated `config.yaml` directly); overridden to `n=4` so the count is unambiguous against
  arms B/C.
- **Arm B, the all-completed truncation.** Re-ran the shipped
  `test_max_failed_fraction_is_measured_against_the_test_partition` fixture's own shape (its own
  `_ALWAYS_FAILING_STEP`, `units=20`, holdout `frac=0.2` giving 4 test units,
  `max_failed_fraction=0.5`) rather than building a second copy, per the brief's instruction. Ran
  it: `len(executions.jsonl) == 2`, `len(execution_order) == 5`, all `completed`, `run.yaml status
  == "completed"`, exit `0`.
- **Arm C, the mixed truncation.** Built `_RECORDS_ONCE_THEN_RAISES_STEP` verbatim from the brief,
  ran with `units=20`, `max_failed_fraction=0.5`, no holdout. Ran it: `len(executions.jsonl) == 2`,
  `len(execution_order) == 5`, statuses `["completed", "failed"]`, `run.yaml status == "partial"`,
  exit `3` (`EXIT_PARTIAL`).

All three passed on the first run with no adjustment needed — the brief's captured literals held
exactly, confirming no code moved between `814eadd` and this branch's point.

**The mutation.** Added `"stopped_at": None,` to the dict `assemble_run_yaml` returns in
`src/publishable/run_record.py` (between `"provenance"` and `"layout"`) — the shape Decision 3
refuses. Ran arm A alone: **FAILS**, at the full-key-list assertion (`'stopped_at' != 'layout'` at
index 8, one extra key on the left). Ran the **full, unfiltered** suite: **exactly one failure** —
`test_a_clean_run_completes_with_the_full_run_yaml_shape` — 2425 passed, 1 failed, 1 skipped, 2
xfailed. Confirms the mutation's blast radius is precisely the pin and nothing else. Reverted by
editing the added line back out (not `git checkout --`); diffed the file against a pre-mutation
copy saved before mutating — byte-identical. Re-ran the three arm tests: all green.

## Task 1 — the document

Edited `docs/reference.md` only (5 sentences touched, in the sections named by the brief):

1. **§ What `status` means** — `failed` paragraph: "Three things" → "Four things produce it," and
   a new closing sentence names the apparatus itself moving (a changed fact, contrasted explicitly
   with "one that stopped answering") as the fourth, on the same "not one dataset, record kept
   anyway" reasoning already used for the input-manifest case. The `max_failed_fraction` clause is
   untouched, per the controller's ruling.
2. **§ What `status` means** — `partial` paragraph: "one thing produces that" now names the
   apparatus **becoming unreachable** explicitly, with an explicit contrast against "the apparatus
   generally" and against "a fact it observed changing" (which is now `failed`'s fourth cause) — a
   pointer rather than a restatement.
3. **§ The apparatus core can only observe**: extended "A changed fact fails the run, with no
   policy knob" to state the outcome — `status: failed`, record kept — immediately before the
   existing `resume`/ledger sentence, which is untouched.
4. **§ Exit codes and diagnostics**: added one sentence after the existing unreachable-probe/exit-5
   sentence, stating the code holds whether or not a record was written, contrasting the mid-run
   case (writes `partial`) against the run-start case (leaves a run directory with no `run.yaml` at
   all — per the plan's correction 3, measured against `run_a_project`'s actual behaviour at
   `814eadd`).
5. **§ The apparatus core can only observe** (correction 6): tightened "compared against its own
   first observation" to "compared against its own first *answered* observation," matching § The
   apparatus files' existing wording for the same rule.

**Checked, not changed** (step 6): read `experimental-designs.md` § Mistakes core prevents'
apparatus row (already says "differ from its own first observation... fails the run"),
`design-principles.md`'s design-goal sentence and § Not bit-identical reruns (both already say a
changed fact fails the run), and `README.md` (declares no probe anywhere). None needed editing —
task 1 makes those existing sentences true rather than requiring changes to them.

**Mechanical pass**: verified no trailing whitespace/tabs/invisible unicode in the touched lines;
verified every anchor my new text links to (`#the-apparatus-core-can-only-observe`,
`#what-status-means-and-when-a-run-keeps-going`, `#resuming`, `#steps-and-artifacts`) resolves
against `reference.md`'s actual headings; no `×`/en-dash issues introduced. A crude anchor-slug
script flagged four pre-existing "missing anchors" elsewhere in the file (headings with `&`/`.`
punctuation my slugger mishandles) and two in `experimental-designs.md` — confirmed by diff against
the pre-edit backup that none of these are touched by or related to this task's edits; they predate
this branch.

**Cross-document sweep**, filtering the file list rather than the sweep's output, four documents
named individually plus `CLAUDE.md` and the feasibility analysis: grepped `README.md`,
`docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md`, `CLAUDE.md`,
`docs/feasibility-llm-growth-studies.md` for `"Three things produce it"` (0 hits — confirms the
stale count phrase is gone) and `"core losing the ability to certify"` (0 hits — confirms the old
imprecise `partial` wording is gone). Proved the sweep can fail against a string known to be
present: the same grep for `"its own first observation"` (without "answered") correctly found the
two exempt/checked-not-changed instances — `experimental-designs.md`'s Mistakes-core-prevents row
and the feasibility analysis's own prose — neither of which task 1 owns.

## What this task does NOT close (task 1 step 8, and the report requirement)

**§ What `status` means cannot be made fully self-consistent without a further code change.** Two
things remain, deliberately unrepaired here, per the controller's ruling that a document may not be
made self-consistent by widening a behaviour change:

- **The all-completed truncation is still a state no row in the `status` table describes.**
  `completed` says "every execution in the plan completed" (false for arm B — the plan did not
  reach its declared length); `partial`'s row says "reached its end... or stopped early with
  executions already recorded," which arm B also doesn't cleanly fit, since it stopped early yet
  reports `completed`. The code (arm B, re-confirmed this batch) answers `completed`/exit `0` for
  this case, and no table row names it.
- **The `failed` paragraph's `max_failed_fraction` clause is a clause the code still
  contradicts** — it's listed among what produces `failed`, but the guard shape re-pinned in task 12
  (arm B) reports `completed`, not `failed`. Left untouched deliberately, per the ruling and per
  `test_max_failed_fraction_is_measured_against_the_test_partition`'s docstring, which this batch
  did not touch, edit, or weaken in any way.

Both are task 11's filing, not this task's to repair.

## Disagreements found between a brief/design/plan and the code

None. Every literal in task 12's brief was re-confirmed by running rather than assumed, and all
matched on the first try. Task 1's edits followed the plan's § Corrections against the code exactly
(correction 6 in particular), and no further disagreement surfaced while reading the four passages
this task touches.

## Concerns

None outstanding for this batch. Both tasks change no runtime behaviour — confirmed by the full
suite's count staying at baseline+3 through task 12 and unchanged through task 1 — which is the
property this batch exists to establish before any later batch can move behaviour against it.
