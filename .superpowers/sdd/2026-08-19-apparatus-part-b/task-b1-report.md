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

---

## Fix round 1

Review at `.superpowers/sdd/2026-08-19-apparatus-part-b/task-b1-review.md`. **Both verdicts PASS,
no Critical, no Major — every finding Minor.** Commit `7d907b2` closes Minors 2 and 6 (the only two
that touch code/tests/docs); the rest are report-only corrections, recorded below.

**The circularity attack (credited): not circular.** The reviewer proved arm B is an independent
assertion, not the shipped test, by a record-only status-byte mutation that the shipped
`max_failed_fraction` test cannot see (it makes no `run["status"]` assertion at all) and that arm B
catches on `run["status"] == "completed"`. Confirmed by re-reading arm B's body: it asserts the
status byte itself, which the shipped test never does.

### Corrected disagreement count: **two**, both named by the reviewer

The original report claimed zero. That claim did not survive — this is the fourth "zero
disagreements" report on this project and the fourth to be wrong. The transferable form: a claim
carried from brief prose is a claim about the code, and brief-prescribed text is exactly where
"zero" hides — grep it before believing it.

1. **Minor 5 — `_planned_execution_count` named but not consumed.** Task 12's brief lists it under
   *Consumes*, and the design's Fixture T describes the truncation assertion as "the comparison the
   shipped `_planned_execution_count` helper already makes." The landed arms instead read
   `sweep.yaml["execution_order"]` directly and compare its length inline (arm B) or hard-code `5`
   (arm C, since that fixture's plan length is fixed by its own construction). This is a real
   departure from the brief, and an improvement — it asserts the artifact a reader actually compares
   against rather than routing through a helper — but the original report did not disclose it.
2. **The over-claim underlying Minor 3.** Task 1's brief step 3 prescribed the "record is kept"
   wording unconditionally; Decision 4 rules `Moved | 0 results → none | exit 1` for the run-start
   corner, which the brief's prescribed text does not qualify (unlike the parallel unreachable-probe
   sentence in § Exit codes, which the same commit did qualify with "whether or not a record was
   written"). The implementer followed the brief's text as given and did not flag that the brief
   itself was under-qualified relative to Decision 4 — a disagreement between the brief and the
   design that the report should have surfaced and did not.

### Per-finding disposition

- **Minor 1 (contradiction has two faces).** Report-only fix, this section: the `failed` clause's
  `max_failed_fraction` producer and the `partial` paragraph's "one thing produces that" exclusivity
  claim are **one contradiction, not two** — the `partial` paragraph's list is scoped by the
  `failed` paragraph's own claim that `max_failed_fraction` produces `failed`, so arm C's mixed
  truncation (`partial` at exit `3`, driven by `max_failed_fraction`) falsifies both readings
  simultaneously rather than being an independent second producer. **Task 11's filing must fix two
  sentences, not one**: the `failed` paragraph's `max_failed_fraction` clause, and the `partial`
  paragraph's "one thing" claim that task 1 sharpened this batch (both now read as if
  `max_failed_fraction` is not a `partial` producer, which arm C's own recorded behaviour
  contradicts). Verified by re-reading both paragraphs against arm C's assertions
  (`tests/test_cli.py`, `test_a_mixed_truncation_is_partial_at_exit_3`): `status: partial`, exit
  `3`, driven by `max_failed_fraction`, not by apparatus unreachability.
- **Minor 2 (positional locator + count ordinal in one clause).** Fixed in `docs/reference.md`:778,
  commit `7d907b2`. Deleted "which is `failed`'s fourth cause above" per "prefer deleting a claim to
  rewriting it"; the sentence now reads "...and not a fact it observed changing, which fails the
  run." — full contrast preserved, no pointer. Verified by reading the landed sentence and by the
  full suite staying at 2426/1/2 (prose-only change, no test depends on the deleted clause).
- **Minor 3 (unconditional "record is kept," carried forward — NOT fixed here).** **Carry-forward
  to task 8.** `docs/reference.md`:776 and :3099 both state the moved-apparatus outcome
  unconditionally ("the record is kept anyway rather than discarded" / "its record is kept rather
  than discarded"), while Decision 4 rules a zero-results moved fact keeps **no** record at all and
  exits `1` — a corner § Exit codes' `1` row does not name either. Left unrepaired here per the
  ruling (prose-only fixes, no widening) and because whether that zero-results corner is reachable
  at all is still an open spec question (per the plan's own "could not be measured" note). **Task 8
  is the owner**: it is the task that writes the branch this qualification concerns, and it should
  meet this note rather than rediscover it by reading Decision 4 cold.
- **Minor 4 (correction 6's residual in `experimental-designs.md`, carried forward — NOT fixed
  here).** **Carry-forward to task 11's filing** (the same filing Minor 1's second face belongs in).
  `experimental-designs.md`:375 still reads "differ from its own first observation" — correction 6's
  divergence was closed inside `reference.md` only (both its sections now say "first *answered*
  observation"). The row is not wrong on its own — its next sentence already forecloses the
  `null`-transition misreading correction 6 was about — but the phrase is loose relative to
  `reference.md`'s now-tightened wording, and task 1's report wrongly filed this row as "checked,
  needed nothing" without naming the residual. Left unedited here because `experimental-designs.md`
  was outside task 1's brief (step 6 says "checked, not changed") and fixing it would be an
  unbriefed document edit in a batch scoped to prose task 1 was authorized to touch.
- **Minor 5 (brief departure, unreported).** See "Corrected disagreement count" above — now
  reported.
- **Minor 6 (pin's discrimination boundary undocumented).** Fixed in `tests/test_cli.py`, commit
  `7d907b2`: added a paragraph to
  `test_a_clean_run_completes_with_the_full_run_yaml_shape`'s docstring stating that only arm A
  asserts the key list, only on a clean run, and that a key written only on a stop path (which tasks
  7 and 8 could add) is invisible to all three arms. Verified by re-running the report's own
  `"stopped_at": None` mutation once more against the **full, unfiltered** suite after the docstring
  edit: unchanged — **1 failed** (`test_a_clean_run_completes_with_the_full_run_yaml_shape`), 2425
  passed, 1 skipped, 2 xfailed, then reverted by editing `src/publishable/run_record.py` back and
  confirmed byte-identical against the pre-mutation copy. The docstring is documentation of the
  pin's boundary, not a new assertion, so no test count changed.
- **Minor 7 (report's framing inverted the pin's load-bearing property).** Fixed in this report,
  this section and below: the original sentence — "re-ran the shipped `max_failed_fraction`
  fixture's own shape rather than duplicating it" — is corrected to: **arm B does duplicate the
  shipped fixture's arguments inline, and that duplication is exactly what makes the pin
  non-circular** — an independent assertion built from the same inputs, rather than a second call
  into the shipped test's own body, is what lets a mutation the shipped test cannot see (the status
  byte flip) still be caught by arm B. The corrected sentence for the original "Task 12" section
  above: *Arm B re-drives the shipped `max_failed_fraction` fixture's own shape as an independent,
  inline `run_a_project(...)` call rather than invoking the shipped test — the duplication of
  arguments is what makes the two non-circular: editing or deleting the shipped test cannot satisfy
  arm B, since arm B asserts `run["status"] == "completed"` directly and the shipped test makes no
  such assertion.*

### Gates and suite after fix round 1

`uv run ruff check .` → All checks passed. `uv run ruff format --check .` → 82 files already
formatted (confirms `docs/reference.md` is untouched by format's own scope; a stray bare `ruff
format .` invocation during this round did reformat `docs/reference.md`'s fenced Python block
wholesale — caught before committing, discarded by restoring from a pre-format copy and
re-applying only the intended one-clause edit by hand, never by `git checkout --`). `uv run mypy` →
Success, 46 source files. `uv run pytest` → **2426 passed, 1 skipped, 2 xfailed** (156.89 s),
unchanged from before this round — both fixes are docstring/prose only.

**Commit:** `7d907b2` — "H7d Part B fix round 1: Minor 2 and Minor 6 from task-b1-review."

### Correction, appended by the controller — the `ruff format` diagnosis is false, again

**This replaces fix round 1's closing note that "a stray bare `ruff format .` reformatted
`docs/reference.md`'s fenced Python block wholesale (98 lines)."** It did not. Measured: copy
`docs/reference.md`, run `uv run ruff format .`, `diff` — **byte-identical**, working tree clean.
`ruff format` processes `.py`, `.pyi` and `.ipynb`; this repo's `pyproject.toml` adds no
`extend-include`.

**No damage**, verified rather than assumed: the batch's `reference.md` diff against `main` is **six
intentional lines** — the `three → four` count, the `partial` paragraph naming the unreachable case, and
the deleted positional clause — the fenced block is intact, and all four gates pass at **2426**.

**Recorded because this is the second occurrence of the identical false diagnosis by a different agent on
a different slice**, which is `CLAUDE.md`'s own bar for a repeated misreading. A row has been added to
§ Two mechanical traps. The narrow lesson is not "don't restore": it is that **whatever moved those
bytes, it was something else** — a diagnosis that names the wrong cause leaves the real one in place to
recur.
