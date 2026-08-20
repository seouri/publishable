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
