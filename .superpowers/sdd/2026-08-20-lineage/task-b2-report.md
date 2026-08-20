# Batch B2 report — task 2 (`resolve_run`) then task 4 (`resolve_step`)

Branch `h8a-lineage`, on top of batch 1 (`9e9ae6f`) at baseline `2470 passed, 1 skipped, 2
xfailed`; mypy 47 source files, formatter 84 files.

## Commits

- `3002508` — H8a task 2: `resolve_run` — the two locator forms, and the property that
  dies silently
- `f33e0b8` — H8a task 4: `resolve_step` — locating the upstream step from the record's
  execution block

## Test summary

Task 2 alone: `2478 passed, 1 skipped, 2 xfailed` (+8 in `tests/test_lineage.py`: Fixture
L's five arms, Fixture C's refused arm and its control, plus the `-LOCATOR` arm). Task 4
added: `2482 passed, 1 skipped, 2 xfailed` (+4: the scoped/unknown/incomplete refusals and
one positive shared/summary resolution). Final gates on the combined state: `ruff check`
clean, `ruff format --check` → 84 files (unchanged — no new file), `mypy` → 47 source
files (unchanged — no new module). Both `uv run pytest -q` full runs (once per task's
final state) landed exactly on the counts above, with no flake. `tests/test_cli.py -k
h8a` (task 11's four guard-pin arms) still passes 3/3 after both commits — **arm C stayed
green throughout**, and this batch never edited task 11's assertions.

No task in this batch touches `validate`, `io`, or any call site — both functions are
direct-call surface only, exactly as scoped ("NOT ONE CALL SITE").

## Task 2 — `resolve_run(locator, *, output_dir, repo_root)`

Implemented in `src/publishable/lineage.py`. The two forms are told apart by
`Path(locator).is_absolute()` alone. In the relative branch, a locator with more than one
`Path.parts` component is `E-UPSTREAM-LOCATOR` before any filesystem lookup; otherwise the
locator is compared **as given** — never a resolved basename — against
`read_run_record(output_dir / locator)["run_id"]`, raising `E-UPSTREAM-RUNID-MISMATCH` on
disagreement. In the absolute branch, `path.resolve()` runs first (so `<output_dir>/latest`
lands on the real directory), then `provenance.resolves_inside_repo(resolved, repo_root)`
is checked against the caller-supplied `repo_root` — never re-derived from the upstream
path — raising `E-UPSTREAM-REPO-CONTAINED` before any read.

**The `latest` asymmetry's mutation, and why it doesn't die silently.** Mutation: change
the relative-form comparison from `record.get("run_id") != locator` to
`record.get("run_id") != resolved.resolve().name` (comparing a resolved basename instead
of the locator as given). Against the full suite this produced exactly **one** failure —
`test_output_dir_latest_via_relative_form_is_runid_mismatch`, `Failed: DID NOT RAISE
ContractError` — because `point_latest` symlinks `<output_dir>/latest` to the real run
directory's *name*, which **is** its `run_id`; resolving before comparing makes the two
agree and the relative form silently starts accepting `latest`. Reverted; diffed
byte-identical against the pre-mutation copy; re-ran `tests/test_lineage.py` (22 passed)
and the full suite (2482 passed) to confirm the revert.

**Fixture L and Fixture C, and the other four mutations — all run against the full suite,
each isolated to exactly the predicted test(s), each reverted and reconfirmed
byte-identical + green:**

| # | Mutation | Full-suite result | Matches brief? |
|---|---|---|---|
| 2 | Parse `run_id` from the resolved directory's basename in the absolute form | 2 failed: the moved-directory test (`record["run_id"]` now `'outside_run'`/`'moved_run'`... ) and the containment control | Yes — brief predicted both |
| 3 | Drop the containment check entirely | 1 failed: the refused-arm test; the control still passed | Yes |
| 4 | Tell the forms apart by a separator test (`"/" in locator`) instead of `is_absolute()` | 1 failed: the `-LOCATOR` test, with the wrong code (`E-UPSTREAM-RECORD-MISSING`, not merely "raised") | Yes, including the "assert the code, not merely that it raises" detail |
| 5 | Re-derive `repo_root` via `find_repo_root(resolved)` instead of using the caller's | 3 failed (see below) | Partially — see finding |

**Finding on mutation 5.** The brief's mutation table says this is caught by "Fixture C's
control" and that "the mutant refuses the arm that must read." Running it: the *refused*
arm (upstream genuinely inside the repo) still passes unchanged, because walking up from
a path already inside `root` finds `root`'s own `.git` and agrees with the correct answer
by construction. What actually failed were the **three tests whose upstream directory
sits under `tmp_path` with no `.git` anywhere above it** — the containment control, the
moved-directory absolute-form test, and the `latest`-via-absolute test — each raising
`ContractError(code="E-GIT-NO-REPO")` from `find_repo_root`, a **crash**, not a silent
`E-UPSTREAM-REPO-CONTAINED` refusal. The mutation is caught (3 failures against the full
suite, each an assertion that expected a successful read), but the mechanism is "no git
repo found upward from an isolated temp directory," not "the mutant refuses the arm that
must read." Recorded here because the brief's exact phrasing doesn't hold for this
environment's directory layout, and a reviewer should not expect to reproduce that
specific wording.

## Task 4 — `resolve_step(record, run_dir, step)`

Implemented in `src/publishable/lineage.py`, named by this batch (neither the brief nor
the design mandates a specific function name; "resolver-internal step-directory
resolution" is the interface description, so `resolve_step` is this batch's choice).
Resolves against the measured `_execution_block` shape — `shared`/`summary` dicts keyed by
step name, `conditions` a list of `{index, label, steps}` — never against the reference
document's example. A step in `shared` or `summary` resolves to `<run_dir>/shared/<step>/`
or `<run_dir>/summary/<step>/`. A step found inside any condition's `steps` (condition- or
repeat-scoped, membership alone, no distinction needed) is always `E-UPSTREAM-STEP-SCOPED`
— including the unswept case where an unambiguous location exists, deliberately, per
Decision 4. Absent everywhere: `E-UPSTREAM-STEP-UNKNOWN`. Present but `status != "completed"`:
`E-UPSTREAM-STEP-INCOMPLETE`.

Fixture S built so a wrong resolution succeeds rather than merely raising a different
error: the condition-scoped step's artifact and the failed step's artifact both exist on
disk, and a `shared/<absent-step>/x.json` bait file exists for the fallback mutation.

**The three prescribed mutations, each run against the full suite, each isolated to
exactly the predicted test, each reverted and reconfirmed byte-identical + green:**

| Mutation | Full-suite result |
|---|---|
| Resolve a `conditions`-listed step into its condition directory instead of refusing | 1 failed: `-STEP-SCOPED` test, `DID NOT RAISE` — the mutant succeeds because the bait artifact exists |
| Skip the `status == "completed"` check (`if False:`) | 1 failed: `-STEP-INCOMPLETE` test, `DID NOT RAISE` |
| Fall back to `shared/<step>/` for a step absent from every block | 1 failed: `-STEP-UNKNOWN` test, `DID NOT RAISE` — the bait file at `shared/step_absent/x.json` is what the fallback would have read |

Task 11's arm C (`tests/test_cli.py::test_h8a_arm_c_the_execution_blocks_scope_routing_run_and_summary`)
was re-run after every mutation-revert cycle and after both commits; it never failed and
this batch never edited it.

## Disagreements between a brief, the design, or the plan, and the code

Grepped both briefs (`task-2-brief.md`, `task-4-brief.md`), the design's Decision 1 and
Decision 4 sections, and the plan's tasks 2 and 4 plus § Corrections against the code
(items 2, 4, 8, 9) before writing any fixture, and again before writing this report.

- **No disagreement found in the normative claims.** `resolves_inside_repo`'s signature
  (`resolved, repo_root`), `read_run_record`'s three-refusal shape, and `_execution_block`'s
  measured `{shared, conditions: [{index, label, steps}], summary}` shape all matched what
  `src/publishable/provenance.py` and `src/publishable/run_record.py` actually export at
  this commit — checked by reading the source, not by trusting the brief's paraphrase.
- **Correction 4 (a test pre-placing an upstream under the downstream's `output_dir` must
  not use `run_a_project`'s returned `run_dir`)** does not apply to any fixture in this
  batch: task 2's relative-form test writes its own synthesized upstream under a fresh
  `output_dir` and never calls `run_a_project` for it; Fixture C uses `run_a_project` only
  for its git-repo shape (`project["root"]`) and passes an unrelated, unused `output_dir`
  to `resolve_run`. Recorded here because the correction is easy to over-apply once
  memorized.
- **Correction 5's exception-class assignment** (`E-UPSTREAM-NAME`/`E-UPSTREAM-ARTIFACT-MISSING`
  are `ArtifactError`; every other `E-UPSTREAM-*` is `ContractError`) — none of the six
  codes this batch mints (`-LOCATOR`, `-RUNID-MISMATCH`, `-REPO-CONTAINED`, `-STEP-SCOPED`,
  `-STEP-UNKNOWN`, `-STEP-INCOMPLETE`) is in the `ArtifactError` set, so all six are raised
  as `ContractError` — matches, and this batch adds no test pinning `type(exc).__name__`
  since none of these codes reaches `executions.jsonl` yet (no call site exists until task
  3/5 wire the resolver in). Noting this as a gap for whichever task first wires
  `reuse_from` into a real execution: that is where the class becomes observable in the
  ledger, not here.
- **The one mismatch worth flagging is mutation 5's outcome**, reported in full above —
  the brief's own mutation table describes an outcome ("the mutant refuses the arm that
  must read") that this environment's directory layout does not reproduce literally
  (a crash, `E-GIT-NO-REPO`, rather than a silent wrong refusal). The underlying property
  the mutation is meant to prove — re-deriving `repo_root` from the upstream path is wrong
  and observably so — holds; the specific mechanism differs from the brief's prose.

## Concerns

None blocking. One item for the next batch to know: `resolve_step`'s name is this batch's
choice (not specified upstream), so whichever task wires it into `io.reuse_from` (task 5)
should import it by that name or say why it's renaming it.

## Fix round 1

Review at `.superpowers/sdd/2026-08-20-lineage/task-b2-review.md`, reviewed at `559167e`.
Both verdicts PASS; one Major, eight Minors, none blocking. Fix commit: `a58a5fc`.

**Major 1 — fixed.** The review reproduced this batch's own finding (mutation 5's brief
prose doesn't hold in this environment — the existing fixtures crash with
`E-GIT-NO-REPO` rather than misclassifying) and went one step further: it built the
fixture the property actually needs and confirmed it discriminates. Added
`test_containment_guard_uses_the_callers_repo_root_not_a_walk_up_from_the_upstream`
(`tests/test_lineage.py`): an upstream inside its own `git init`'d sibling repo, distinct
from the downstream's `repo_root`. **Verified by running**: unmutated code reads it
(`resolved, record = resolve_run(...)` returns normally); re-applying the exact
mutation (`resolves_inside_repo(resolved, find_repo_root(resolved))`) makes this test
**and** the three the review already found fail — 4 failed against the full,
unfiltered suite (`2480 passed, 1 skipped, 2 xfailed`), the new test failing with an
actual `ContractError(code="E-UPSTREAM-REPO-CONTAINED")` propagating out (an assertion
failure, not a crash), because walking up from the upstream now finds the sibling
repo's own `.git`. Reverted by editing the two lines back; diffed byte-identical
against the pre-mutation copy; re-ran `tests/test_lineage.py` (24 passed) and the full
suite (2484 passed after both fixture additions in this round) to confirm the revert.

**Minor 1 — fixed.** Deleted the docstring clause in
`test_absolute_form_on_a_moved_directory_reads_the_records_own_id` claiming an
assertion on "the RAW rendered text," and deleted the `yaml.safe_dump(record)`
assertion it justified — `yaml.safe_dump` re-renders the already-parsed dict, which is
exactly the normalisation the rule warns about, and the assertion was redundant with
`record["run_id"] == run_id` on the preceding line (no mutation inside `resolve_run` can
fail one without failing the other, since the function renders nothing). Preferred
deleting the claim to rewriting it, per `CLAUDE.md`.

**Minor 2 — fixed.** `resolve_run`'s `E-UPSTREAM-RUNID-MISMATCH` message now branches on
`locator == "latest"`: the `latest`-specific clause appears only there, and the
renamed-directory fault gets its own clause ("the relative form addresses a run by its
own run_id, never by another name it happens to sit under"). Both existing tests now
assert message text, not only `.code` — batch 1's lesson, one level down. **Verified by
running**: reverting the split back to the single always-`latest` message made
`test_a_renamed_run_directory_disagrees_with_its_own_record` fail on the new
`assert "`latest`" not in str(e.value)` line (`AssertionError`, the substring found).
Reverted; `tests/test_lineage.py` back to 24 passed.

**Minor 3 — fixed.** `resolve_step`'s docstring no longer states
`` `<run_dir>/<repeat>/<step>/` `` unconditionally; it now says the location sits
directly under the run directory, never under `conditions/`, with a `<repeat>/`
segment "only when the run resolved more than one repeat — a single repeat collapses
it," matching what `runner.step_dir_for` actually does and what plan correction 9 itself
qualifies.

**Minor 4 — fixed.** `resolve_run`'s docstring now attributes the "two readings" to
§ Lineage between runs and the `is_absolute()`-and-nothing-else predicate to Decision 1
by name, rather than crediting both to the reference document.

**Minor 5 — fixed.** Added
`test_a_repeat_scoped_step_nested_under_its_repeat_label_is_also_refused`
(`tests/test_lineage.py`): a `conditions[0].steps["step_repeat"]` value shaped as
`{"seed47": {"status": "completed"}}` — the real nested shape
`run_record._execution_block` writes for a repeat-scoped step — routes to the same
`E-UPSTREAM-STEP-SCOPED` refusal as the flat condition-scoped shape, confirming
membership in `conditions` really is the whole test regardless of what sits inside
`steps[step]`. No code change; the review found the routing already correct and only
the seam untested.

**Minor 6 — closed by documenting, not by adding new behaviour.** Added a comment above
`entry.get("status")` in `resolve_step` naming the `AttributeError` a non-mapping
execution entry would raise, that this is a read with no call site yet, and that
whether it earns a coded refusal is task 5's decision — not silenced, not given a new
`E-` code (§ Errors rows and new call-site behaviour are outside this batch's and task
9's remit respectively).

**Minor 7 — not retro-edited; recorded here instead.** The original report's Test
summary line ("`tests/test_cli.py -k h8a` (task 11's four guard-pin arms) still passes
3/3") mislabels the selector: that command reaches three tests because arm D lives in
`tests/test_artifacts.py`, not `tests/test_cli.py`. The 3/3 result itself was correct
and arm D is covered by every full-suite run regardless; only the parenthetical was
wrong. Left the original text as-is (a development-record report is not retro-edited)
and correcting it here instead.

**Minor 8 — filed, not fixed.** `docs/superpowers/spec-defects.md` §
"`resolve_run`'s relative form skips the repo-containment check..." — owner named as
whoever wires `io.reuse_from` (tasks 3/5), with the two checks its owner must make
(resolve the relative path and check both branches, or record why the exemption is
safe against a symlink specifically) spelled out in the filing. Not widened here: the
code matches Decision 1 exactly, and changing the guard's behaviour is outside this
batch's charter and would be a decision reversal made without the argument
`design-principles.md` requires.

**Verification after all fixes.** `uv run ruff check .` clean. `uv run ruff format
--check .` → 84 files (unchanged — no new file). `uv run mypy` → 47 source files
(unchanged). `uv run pytest -q` → **2484 passed, 1 skipped, 2 xfailed** (+2 from this
round's two new fixtures: Major 1's sibling-repo test and Minor 5's repeat-nested-shape
test). `tests/test_cli.py -k h8a` still 3/3 — arm C unedited and green throughout. No
sentence in this section or the diff claims a config count moved.
