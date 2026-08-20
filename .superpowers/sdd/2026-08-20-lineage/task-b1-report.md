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

## Fix round 1

Review at `.superpowers/sdd/2026-08-20-lineage/task-b1-review.md`, reviewed at `3ddf13a`.
Both verdicts PASS; six Minors, no Major. Fix commit: `5d54e94`.

**Corrected upward, per the coordinator's instruction — not filed as a hole:**

- **Drift justification (attack 2).** The `SCHEMA_VERSION` mutation reported in the
  original report was value-preserving (`"1.0"` → `"1.0"`), so by definition it cannot
  be drift and its blindness proves nothing about whether drift is caught. The reviewer
  built the real drift case two ways: writer bumped to `"1.1"` with the import intact —
  `tests/test_lineage.py` alone stays at 10 passed, because the reader tracks the writer;
  writer at `"1.1"` **plus** a stale `"1.0"` literal reintroduced in `lineage.py` — **4
  failed**, including `test_fixture_r_a_real_run_yaml_reads_back_what_the_writer_wrote`
  raising `E-UPSTREAM-RECORD-VERSION`. **Fixture R is the drift pin**, and it holds
  independently of the test file's own import of `SCHEMA_VERSION` (the three synthesized
  fixtures also fail in that second case, but only because the test file imports the
  same name — Fixture R does not need that to fail). Decision 3's reason for importing
  `SCHEMA_VERSION` — "writing it twice is how the two drift" — is therefore pinned, not a
  gap. The original report's claim ("no assertion anywhere hard-codes a version string")
  was true but understated the actual property; this section replaces it as the correct,
  stronger claim.
- **The named-authorized-editor mechanism** was judged sound rather than a loophole, on
  four checkable properties: the post-edit state is specified in advance, the editor is
  one named task, a post-hoc verification obligation is stated, and the clause is scoped
  to arm B alone. Recorded here so this is not read as a residual concern — it isn't one,
  subject to m2 below.

**m1 (most consequential) — fixed.** `tests/test_lineage.py`'s
`test_a_yaml_document_that_is_not_a_mapping_is_record_unreadable` and
`test_a_mapping_with_no_run_id_is_record_unreadable` now assert message text
(`"did not parse to a mapping"` / `` "has no `run_id`" ``) in addition to the shared code
`E-UPSTREAM-RECORD-UNREADABLE`. *Verified by running*: with `if not isinstance(doc,
dict):` neutered (`if False and not isinstance(doc, dict):`), the not-a-mapping fixture
now falls through to the `run_id` branch and raises the *other* message from the *other*
site — the full **unfiltered** suite now reports **1 failed** (exactly
`test_a_yaml_document_that_is_not_a_mapping_is_record_unreadable`), **2469 passed**, 1
skipped, 2 xfailed, rather than the prior 2470-passed blind result. Reverted by editing
the guard back in; diffed byte-identical against a pre-mutation copy; re-ran the full
suite to confirm **2470 passed, 1 skipped, 2 xfailed** again.

**m2 — not fixed here; carried forward, named for task 7's author.** The twelve-key
`provenance` list is pinned in **two** places: task 11's arm B
(`tests/test_cli.py::test_h8a_arm_b_the_provenance_key_list_and_no_upstream_key`, which
carries the authorization clause) and H7d Part A's shipped
`test_a_run_with_no_declared_probe_records_a_null_apparatus_block_and_no_ledger`
(`tests/test_cli.py`, asserting the identical twelve-key list with no such clause). B1
could not add a clause to the second location without editing a shipped H7d assertion,
which this batch was told not to do. **Carry-forward for whichever batch executes task
7:** task 7 must, when it appends `"upstream"` after `"allocation_hash"`, (a) edit arm
B's assertion per its existing clause, AND (b) edit the H7d test's assertion the same
way — same one key appended, nothing reordered — and its report must show **both**
diffs, not one. Until task 7 lands, the H7d test is an unnamed pin that will hard-fail
(loudly, not silently) the moment task 7's edit lands; that is expected and not a defect
to fix now.

**m3 — reported here, not a code change.** Of the four guard-pin arms, **only arm C
carries genuinely new discriminating power**: arm A restates the shipped
`test_a_clean_run_completes_with_the_full_run_yaml_shape`; arm B restates the shipped
H7d provenance test (m2); arm D restates its own immediate shipped neighbour,
`test_a_narrower_step_reads_a_wider_one_normally`, and no mutation isolates it — the
prescribed arm-D mutation (renaming `read_upstream`'s `run`-scope base) failed arm D
together with 11 shipped tests. **Arm C is the one arm B2–B6 should watch**: it is the
only named pin of the `shared`/`summary` routing Decision 4 rests on, and the reviewer
confirmed it breakable (routing `summary` into `shared` fails it). This does not argue
for deleting the other three — the brief prescribed all four, and re-capturing them by
running was the point — but a later batch weighing this pin's marginal value should read
arm C as the load-bearing one.

**m4 — fixed.** Deleted the phrase "anywhere in this slice" from arm A's docstring
(`tests/test_cli.py`), which claimed a guarantee the assertion does not provide — it is
blind to a key written only on a stop path, a boundary the shipped predecessor's own
docstring states and arm A's had dropped. Nothing else in the docstring changed; the
claim now matches what the assertion actually catches.

**m5 — fixed.** Deleted the citation of
`.superpowers/sdd/2026-08-20-lineage/task-11-brief.md` from arm D's docstring
(`tests/test_artifacts.py`) — that file is git-ignored as mechanically regenerable
(`.superpowers/sdd/.gitignore`), so a shipped source file must not point at it. The plan
citation (`docs/superpowers/plans/2026-08-20-lineage.md` task 11) stays.

**m6 — fixed.** Deleted the clause in `lineage.py`'s module docstring that conceded its
own argument ("since a reader living there would need no import of itself") while citing
the cycle as grounds for refusing `run_record.py` as the reader's home. The docstring now
refuses `run_record.py` on its own stated ground alone — "assembles only, computes
nothing" — which stands without the cycle clause.

**m7 — informational, no action.** The cross-test-module import
(`tests/test_lineage.py` importing `run_a_project` from `tests/test_cli.py`) is
sanctioned by the design (Fixture R). Noted for later batches: if more than one further
file needs `run_a_project`, a conftest-level home is worth considering then.

**Carried forward, not this batch's, recorded so B6 does not lose it:**
`docs/reference.md` § Package layout still reads `lineage.py … — not yet built` while the
module now ships; that marker move is task 9's, per the plan.

**Verification after all fixes.** `uv run pytest -q` → **2470 passed, 1 skipped, 2
xfailed** (unchanged from before the fix round — no test was added or removed, only
docstrings and two assertions tightened). `uv run ruff check .` → clean. `uv run ruff
format --check .` → **84 files**. `uv run mypy` → **47 source files**. No sentence in
this section or the diff claims a config count moved.
