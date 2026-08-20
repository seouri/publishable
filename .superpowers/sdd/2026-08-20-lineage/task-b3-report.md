# H8a batch 3 (tasks 3, 5) — report

Commits: `569113f` (task 3 — `UpstreamResolver`/`UpstreamLedger`, injected), `e21d795`
(task 5 — `io.reuse_from` completed: `_contained`, `E-UPSTREAM-NAME`,
`E-UPSTREAM-ARTIFACT-MISSING`).

## Status

Both tasks done, in order (3 → 5), each committed separately. All four gates clean after
each commit: `uv run ruff check .`, `uv run ruff format --check .` (84 files, unchanged),
`uv run mypy` (47 source files, unchanged), `uv run pytest` full suite.

Test count: **2484 → 2487** (task 3, +3) **→ 2494** (task 5, +7), 1 skipped, 2 xfailed
throughout — no regressions, no skip/xfail count change.

## What was built

**Task 3.** `lineage.py` gains `UpstreamLedger` (a bare container at this point — task 6
owns the accumulation rule) and `UpstreamResolver`, holding `output_dir`, `repo_root`, the
ledger, and a cache of `(run_dir, record)` keyed by `run_id`. `command_run` builds one of
each *before* `allocate_run_dir` creates `output_dir` (this placement is load-bearing, not
cosmetic — see Concerns) and threads the resolver through `execute_plan` into every
execution's `StepIO` as a private `upstream=` keyword. `artifacts.py` still imports nothing
from `lineage.py` outside `TYPE_CHECKING`; `runner.py` gained the same guard. `StepIO`
gained a first cut of `reuse_from` that resolves the locator and the step directory through
the resolver and reads the name directly, with a bare `assert` for a missing resolver.

**Task 5.** Completed `reuse_from`: `StepIO._contained(base, name, *, code)` refuses `..`
traversal, an absolute name, and an escaping symlink, and is otherwise silent on the shape
of the path (a forward separator is legal, per `reference.md`'s own
`programs/gpt-4.1__seed29.json` example). `reuse_from` calls it with `code="E-UPSTREAM-NAME"`;
a missing step directory or missing name is one code, `E-UPSTREAM-ARTIFACT-MISSING`; a
writer-without-reader suffix still raises the inherited `E-ARTIFACT-UNREADABLE` — no second
code minted. `_contained` is built but **not** wired into `read_upstream`/`read_condition`
(that is task 12's, not this batch's).

## The open containment filing — ruling

**Closed, not re-filed.** `resolve_run`'s relative form now resolves its path (following
symlinks) and runs `resolves_inside_repo` on it before reading the record — exactly the
check the absolute form already ran, same predicate, so the two branches share one rule
instead of two that could drift. This also closes the filing's "second half": the relative
form now returns a resolved path, matching the absolute form's return kind. `spec-defects.md`
is struck (not left open, not re-filed) with the fix's grounds and its pinning tests named.

Positive control confirmed: `test_relative_form_containment_control_reads_an_ordinary_subdirectory`
passes — an ordinary, non-symlinked run directory under `output_dir` still reads through the
relative form. The widening fix does not overshoot: it only rejects paths that resolve
outside `repo_root`, not ordinary subdirectories of `output_dir`.

Grounds for closing now rather than deferring: the fix is mechanical (reuse the existing
`resolves_inside_repo` predicate, same call shape as the absolute branch already has), it
does not change any already-shipped test's outcome (confirmed by the full-suite run), and
`CLAUDE.md`'s instruction was explicit that "do not widen containment silently — if you
change it, say so and pin it," which is what the two new tests plus this doc edit do.

## Mutations run (all reverted, all confirmed to discriminate)

| # | Mutation | File | Assertion that caught it | Confirmed |
|---|---|---|---|---|
| 1 | `UpstreamResolver.__init__` does I/O (`output_dir.iterdir()`) | `lineage.py` | any real `run` (all of `test_lineage.py`'s real-run tests, including the wiring test) | FAIL as required, then reverted, re-confirmed identical to saved copy, suite re-green |
| 2 | Drop `upstream=` at the `StepIO` construction site | `runner.py` | the wiring test's specific `E-UPSTREAM-RECORD-MISSING` assertion | FAIL (an uncoded `AssertionError` from the bare guard, not the specific code — the wildcard-vs-specific distinction the brief named actually matters here), reverted, re-confirmed |
| 3 | Revert the relative-form containment fix | `lineage.py` | the new symlink-into-repo test | FAIL (`DID NOT RAISE ContractError`); its control still passed | reverted, re-confirmed |
| 4 | Drop `_contained` from `reuse_from` | `artifacts.py` | Fixture N's three refusal arms | FAIL (`DID NOT RAISE ArtifactError`) | reverted, re-confirmed |
| 5 | Widen `_contained` to refuse any separator | `artifacts.py` | Fixture N's positive control | FAIL (raised where it must read) | reverted, re-confirmed |
| 6 | Return `None` for a missing artifact | `artifacts.py` | the `-ARTIFACT-MISSING` code assertion | FAIL (`DID NOT RAISE`) | reverted, re-confirmed |
| 7 | Mint a second code for a writer-without-reader suffix | `artifacts.py` | the inherited `E-ARTIFACT-UNREADABLE` arm, and the pre-existing shipped test for the same mechanism | FAIL (both), confirming the mutation also breaks a shipped test | reverted, re-confirmed |

Every mutation's two branches were checked to actually differ before trusting the fixture
(e.g., mutation 3's control test targets an *ordinary* subdirectory specifically so the fix
can't be indistinguishable from a no-op on it; mutation 5's positive control targets
`programs/a.json`, which the un-widened rule reads and the widened one refuses). Each
mutation was reverted by editing the file back in place (never `git checkout --`), verified
by diffing against a saved copy (byte-identical) and by re-running the affected tests.

## Disagreements found, after grepping what each brief/design/plan asserted

- **The dropped mutation's placement mattered and the brief didn't say where.** Task 3
  step 1's mutation ("make the constructor stat or iterdir `output_dir`; a first run with no
  prior runs then dies at start") only discriminates if the resolver is constructed *before*
  `allocate_run_dir` creates `output_dir`. My first placement (just before the
  `execute_plan` call, after `run_dir` was already allocated) let the mutation pass silently
  — `output_dir` already existed and was non-empty by then. Verified by running: the mutant
  test suite stayed green at that placement. Moved the construction to immediately before
  `allocate_run_dir` (`cli.py`, still using `output_dir`/`repo_root` already in hand at that
  point) and re-ran the mutation, which then failed as the brief predicted. Neither the
  design nor the plan states this placement constraint explicitly — Decision 2 says only that
  `__init__` "does no I/O and cannot raise," and the plan's task 3 step 4 says "both are in
  hand" without saying by when construction must happen relative to `allocate_run_dir`. I
  built the placement that makes the prescribed mutation actually discriminate, since a
  mutation whose two branches can't differ under some code arrangement is exactly the
  *mutation is a claim too* failure `CLAUDE.md` warns about.
- **No disagreement found in task 5's brief, design, or plan against the code** — its
  mutation table and fixture descriptions matched the shipped `_resolve`/`_read` shapes
  exactly once traced through.
- I did not find a case where a task brief cited a git-ignored file, and I greped
  `spec-defects.md` for the exact filing title before treating it as still open, per the
  brief's own warning about ledger lines that say "filed" without a real filing existing.

## Ruling: Minor 6 (non-mapping `execution` entry → `AttributeError`)

Deferred to "task 5's decision" by the batch-2 review. Ruled here: **no coded refusal.**
Grounds: this is a hand-edited-`run.yaml` fault, not a config's or a step's, and
`read_run_record` (Decision 3) already draws its validation line at three narrow refusals
rather than the whole document's shape; widening that line with no config-reachable case to
justify it would be scope creep. `execute_plan`'s bare `except Exception` still contains it
— the execution is recorded `failed`, the run continues — so Decision 10 ("nothing in H8a
stops or alters a run") is not at risk merely because the exception carries no code. Recorded
in `lineage.py`'s comment at the site, replacing the deferred pointer with the ruling and its
grounds (not rewritten — the deferred claim was deleted, not amended, since it was pointing
at a decision not yet made).

## Task 12's boundary held

`_contained` exists but is used only by `reuse_from` in this batch; `read_upstream` and
`read_condition` are untouched, confirmed by the full-suite run showing no change to any of
their existing tests (task 12's own "this is the only task that can change a shipped test's
outcome" claim stays true after this batch).

## Concerns for the reviewer

- **The resolver's construction point moved during task 3** (from beside `execute_plan` to
  immediately before `allocate_run_dir`) specifically to make the prescribed
  no-I/O-at-construction mutation discriminate. Worth a second look: is there any reason
  `output_dir`/`repo_root` being captured that much earlier in `command_run` could matter for
  a later task (e.g. task 7's provenance assembly, or a future `resume`/`draft` path this
  function also serves)? I did not find one, but the move was made for a specific,
  narrow reason and is worth confirming against the whole function rather than just the
  diff.
- **`UpstreamResolver.resolve`'s cache is keyed by `run_id`, not by the raw locator.** A
  relative locator is checked against the cache before any read (since a valid relative
  locator's `run_id` equals itself); an absolute locator always triggers a `resolve_run` call
  before it is cached under the `run_id` it turns out to name. This means two *identical*
  absolute-locator calls each cost one record read, while a relative call repeating a
  previously-resolved `run_id` (or an absolute call to an upstream a relative call already
  cached) is free. No fixture in this design's own § The discriminating fixtures tests a
  read count directly, and neither task 3's nor task 5's brief prescribes one, so this was
  built to the letter of "a per-run_id record cache" without a dedicated pinning test. Task
  6 (accumulation) or a later reviewer may want one if this behavior turns out to matter.

## Fix round 1

Review: `.superpowers/sdd/2026-08-20-lineage/task-b3-review.md`, reviewed at `db41b5a`.
Verdicts: spec compliance PASS with one Major that did not block; task quality PASS. Fix
commit: `292c236`.

### Major 1 — cache did not hold "one answer per run" for the absolute form

**Changed:** `UpstreamResolver._records` is now keyed by the **locator exactly as given**,
never by the `run_id` it resolves to. `resolve()` checks this cache for *both* forms before
calling `resolve_run` at all (previously only the relative branch consulted it, and only
after resolution). `lineage.py`'s docstrings for the field and the method were rewritten to
state the actual guarantee and why keying by locator delivers it.

**Verified by:** three new tests in `test_lineage.py`.
`test_resolver_cache_reads_a_repeated_absolute_locator_only_once` monkeypatches
`lineage.read_run_record` with a counting wrapper and asserts three identical absolute
`resolve()` calls produce exactly one real read.
`test_resolver_cache_reads_a_repeated_relative_locator_only_once` is the same check for the
relative form. `test_resolver_cache_a_mid_run_edit_between_two_identical_absolute_calls_cannot_leak_through`
reproduces the review's own `code_hash` `AAAA`→`BBBB` scenario directly and asserts the
second identical absolute call still returns `AAAA`. All three were run against the
pre-fix code (`lineage.py.pre_fixround1`, restored temporarily) and failed exactly as the
review predicted (3 reads, not 1; `BBBB` leaking through); reverted to the fix and
re-confirmed green.

### Minor 3 — warm cache let a relative locator resolve a run outside `output_dir`

Closed by the same change as Major 1, per the review's own suggestion (locator-keyed cache
closes both). **Verified by:** `test_resolver_cache_does_not_let_a_warm_absolute_call_shortcut_a_later_relative_one`
— cold `resolve(run_id)` against an `output_dir` that does not contain that run fails with
`E-UPSTREAM-RECORD-MISSING`; the same run is then resolved via its absolute path (a
*different* locator string, warming the cache under that string, not under `run_id`); the
relative call is repeated and must still fail the same way. Run against the pre-fix code:
the second relative call incorrectly succeeded (`DID NOT RAISE ContractError`); against the
fix, both cold and warm refuse. Reverted/confirmed the same way as Major 1's tests.

### Minor 1 — Fixture N's absolute-`name` arm carried no weight

**Changed:** added a fourth arm to
`test_reuse_from_name_containment_refuses_traversal_absolute_path_and_symlink_escape` in
`test_artifacts.py` — an absolute path pointing to a file that exists *inside* the step
directory (`step_dir / "ok.json"`), refused only by `_contained`'s `Path(name).is_absolute()`
clause, since the `startswith` half would happily accept it.

**Verified by:** applying the review's exact mutation (drop `Path(name).is_absolute() or`
from `_contained`, leave `_resolve` untouched) — the new arm is the *only* one of the seven
`reuse_from` tests that fails (`DID NOT RAISE ArtifactError`); the other six, including the
`..` and symlink arms in the same test function, stay green. Reverted, `diff -q` confirmed
byte-identical, full `test_artifacts.py` + `test_lineage.py` re-run green (147 passed).

### Minor 2 — the closed filing claimed a pin two named tests did not provide

**Changed:** added `test_relative_form_returns_a_resolved_path_not_merely_a_contained_one`
to `test_lineage.py` — `<output_dir>/<run_id>` is itself a symlink to a differently-named
real directory outside `output_dir` (not inside a repo, so containment is not what this
test isolates); asserts `resolve_run`'s returned path equals the real target's own
`.resolve()`, not the unresolved `output_dir / locator`. `spec-defects.md`'s CLOSED entry
was amended (appended, not rewritten) to strike the "also closes the second half" overclaim
and name this test as the actual pin, per the rule that a closed filing's claims are checked
like any other comment.

**Verified by:** the review's exact mutation (keep containment on a resolved `probe`, return
the unresolved `output_dir / locator`) — the two originally-named tests both stay green
(confirmed: only the new test fails, `DID NOT RAISE` becomes a value mismatch — resolved
path expected, unresolved path returned); the other 143 tests in both files stay green,
matching the review's own "142 passed" count structurally (one more test now exists to catch
what those 142 could not). Reverted, re-confirmed identical to the fixed file, full suite
green.

### The fail-open filing (not a finding against this batch; filed as instructed)

Added a new `spec-defects.md` entry: `provenance.resolves_inside_repo` compares paths
without resolving `repo_root` itself, so a caller that hands it an unresolved `repo_root`
gets a **false negative** on a genuinely-contained path (reproduced with a `/tmp` vs
`/private/tmp`-style symlink split, matching what the reviewer hit in their own probe).
Every shipped caller resolves via `find_repo_root` first, so nothing in this repo is
affected; filed with the concrete fix its owner should make (resolve `repo_root` inside the
function, cheaper than sweeping every caller for the precondition) rather than left as a
vague note. Owner: unassigned, since no slice currently owns `provenance.py`'s containment
predicate.

### Gates and full suite after the fix round

`uv run ruff check .` — all checks passed. `uv run ruff format --check .` — 84 files
unchanged. `uv run mypy` — 47 source files, no issues. `uv run pytest` (full, unfiltered,
foreground, `__pycache__`/`pytest-of-*` cleared first) — **2494 → 2499 passed**, 1 skipped,
2 xfailed (130.7s). `git diff --stat` against the pre-fix-round tree confirms
`tests/test_cli.py` untouched (arm B stays task 7's) and arm D
(`test_h8a_arm_d_the_shipped_positive_read_upstream_read`) still passes on its own.

### Findings not closed, and why

None. All four findings (Major 1, Minor 1, Minor 2, Minor 3) were fixed and pinned; the
fifth item (the `resolves_inside_repo` fail-open) was explicitly not a finding against this
batch and was filed rather than fixed, per the coordinator's instruction.
