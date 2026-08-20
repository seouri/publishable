# Tasks 6, 7 (batch 5) — accumulation, and `provenance.upstream`

Dated 2026-08-20, against branch `h8a-lineage` at `68a1726` (batch 4 closed, task-b4 report
committed) before this batch's own two commits.

## What changed

**Task 6** (`src/publishable/lineage.py`, `src/publishable/artifacts.py`,
`tests/test_lineage.py`). `UpstreamLedger` gained `record(*, step, name, record)` and `entries()`.
`record` is called from `artifacts.StepIO.reuse_from` exactly once, immediately after `self._read`
returns — never before, and never from an `except` path — so a call that raises leaves the ledger
untouched (Decision 6, step 1). The ledger itself is unchanged in this respect: it was already a
run-level object built once in `command_run` and handed to every execution's `StepIO`, so an entry
made before an execution later fails is never removed (Decision 6, step 2) — nothing new needed
building for that half; it falls out of the object's existing lifetime. Keyed by the *resolved*
`run_id` (from the record `resolve_run`/`UpstreamResolver.resolve` already produced), never by the
locator string a step passed, so a read of one upstream once by `run_id` and once by an absolute
path is one entry with both artifact names in `used`. `used` is stored as a **list**, deduplicated
on append, not a set — see the mutation-quality note below. `entries()` returns entries sorted by
`run_id`, each `used` sorted lexicographically.

**Task 7** (`src/publishable/cli.py`, `tests/test_cli.py`,
`docs/superpowers/spec-defects.md`). `command_run`'s `provenance` dict gains
`"upstream": upstream_ledger.entries()`, inserted immediately after `allocation_hash` and nothing
else reordered. Always a list, `[]` when nothing was read — Decision 7, on
`input_manifest_changed`'s precedent rather than `apparatus: null`'s. `run_record.py` is untouched.
Closes and strikes the `provenance.upstream` row in `spec-defects.md`'s "no code writes" table
(§ Six `provenance` and `results` keys), with a dated amendment paragraph rather than a silent
deletion.

## The two guard-pin diffs, both by task 7

**Arm B** (`tests/test_cli.py`, `test_h8a_arm_b_the_provenance_key_list_and_upstream_empty`,
renamed from `..._and_no_upstream_key`):

```diff
     assert list(provenance.keys()) == [
         "git", "environment", "apparatus", "input_manifest", "input_manifest_hash",
         "input_manifest_changed", "publishable_version", "plugin_versions", "units",
         "units_hash", "allocation",
         "allocation_hash",
+        "upstream",
     ]
-    assert "upstream" not in provenance
+    assert provenance["upstream"] == []
```

**The shipped H7d test**
(`test_a_run_with_no_declared_probe_records_a_null_apparatus_block_and_no_ledger`):

```diff
     assert list(run["provenance"]) == [
         "git", "environment", "apparatus", "input_manifest", "input_manifest_hash",
         "input_manifest_changed", "publishable_version", "plugin_versions", "units",
         "units_hash", "allocation",
         "allocation_hash",
+        "upstream",
     ]
```

Both are exactly the one-key append the brief prescribes, nothing reordered. **Arm A and arm C are
untouched** — confirmed by `git diff` scoped to this batch's commits touching only the two hunks
above inside `tests/test_cli.py`'s guard-pin section — and arm C stayed green throughout every run
in this batch (`test_h8a_arm_c_the_execution_blocks_scope_routing_run_and_summary`, part of every
full-suite run below).

## Why Fixture F sits in task 7's commit, not task 6's

Task 6's own interface is `UpstreamLedger.entries()` — it does not touch `cli.py`. Fixture F
("a read from an execution that later fails") is task 6's fixture in the design and the plan, but
it asserts on `run.yaml`'s `provenance.upstream` through a real end-to-end `run` — the surface the
brief's own "test at `run` level" rule requires, since an upstream read is a step-level call and
H7d Part A's only Critical was invisible to every direct-call probe. That key does not exist in
`provenance` until task 7's `cli.py` edit lands. Committing task 6 alone with Fixture F included
would either leave a real run's assertion on a `KeyError` (before task 7) or require reaching into
`StepIO._upstream.ledger` internals to observe the same fact, which the brief forbids. So: task 6's
commit carries Fixture O only (direct-call, `tests/test_lineage.py`, needs no wiring beyond the
ledger itself); task 7's commit carries Fixture E, Fixture R, and Fixture F together, all in
`tests/test_cli.py`. **Verified, not assumed**: the full suite was run at the task-6-only commit
(stashing task 7's `cli.py`/`test_cli.py`/`spec-defects.md` changes with
`git stash push --keep-index`) and is green there — see the suite line below — before task 7's
changes were restored and committed.

## Suite, gates

Baseline (batch 4 closed): **2503 passed, 1 skipped, 2 xfailed**; mypy 47; formatter 84.

After task 6 alone (commit `ea8174e`), full unfiltered `uv run pytest -q`: **2506 passed, 1
skipped, 2 xfailed** (+3: Fixture O's three tests). `ruff check .`, `ruff format --check .`, `mypy`
all clean at 47/84.

After task 7 (commit `d6e65ed`), full unfiltered `uv run pytest -q`: **2510 passed, 1 skipped, 2
xfailed** (+4 more: Fixture E, Fixture R, and Fixture F's two tests — total delta from baseline
+7). Gates clean at 47/84 again.

## The mutations, run against the full unfiltered suite, each reverted and re-verified by re-running

Task 6:

| Mutation | Result |
|---|---|
| Delete `sorted()` on `used` (`"used": list(...)"`) | **FAILED** — Fixture O's exact-list assertion, three times in a row (checked determinism, see below) |
| Delete `sorted()` on entries (`for entry in self._entries.values()`) | **FAILED** — Fixture O's entry-order assertion |
| Record an entry when the read raised (moved `ledger.record(...)` before the `target.exists()` check, so it fires even on the `E-UPSTREAM-ARTIFACT-MISSING` branch) | **FAILED** — Fixture F's raising half (`upstream == []`), only after fixing the fixture itself — see below |
| Drop the entry when the execution later fails (added `upstream.ledger._entries.clear()` in `runner.py`'s per-execution `except`) | **FAILED** — Fixture F's returning-then-failing half (`len(entries) == 1`) |
| Key the ledger by locator (threaded `_key=locator` through `record()`, keyed `setdefault` on it) | **FAILED** — the both-forms arm (`len(entries) == 1` became 2) |
| Widen a `reuse_from` refusal into a run stop (re-raised any `E-UPSTREAM*`-coded exception out of `runner.py`'s per-execution `try`) | **FAILED** — `test_fixture_f_a_read_that_raises_contributes_no_entry` (the run crashed with exit 1, `main()` never returning `expect_exit`, before any `run.yaml`/ledger-line assertion was reached) |

Task 7:

| Mutation | Result |
|---|---|
| Write `upstream` only when non-empty (`if _upstream_entries: provenance["upstream"] = _upstream_entries`) | **FAILED** — three tests at once: Fixture E's membership assertion, arm B, and the shipped H7d test |
| Copy the downstream's hashes into the entry (hardcoded a placeholder string for `code_hash`/`parameters_hash` in `record()`) | **FAILED** — Fixture R's read-back comparison |
| Add a fifth key (`"note": "extra"`) | **FAILED** — Fixture R's exact-key-list assertion |

Every mutation was reverted by editing the file back (never `git checkout --`), `__pycache__`
cleared, and the affected tests re-run green before moving to the next mutation. `git diff --stat`
against each of the two commits was empty immediately before committing.

**One mutation caught nothing on the first attempt, and the fix is worth recording rather than
hiding.** The prescribed "record an entry when the read raised" mutation was first tried against a
Fixture F variant whose raise came from a **step name the upstream never recorded**
(`E-UPSTREAM-STEP-UNKNOWN`), which raises inside `resolve_step`/`locate_step` — upstream of the
line the mutation moves entirely. The mutation passed the full suite unnoticed: a refusal firing
for the wrong reason is not a pin (`CLAUDE.md`). Fixed by changing the fixture to raise from the
exact call site the accumulation edit sits beside — a valid step, a **missing artifact name**
(`E-UPSTREAM-ARTIFACT-MISSING`) — after which the same mutation failed the test as prescribed. Both
attempts are in the git history of this session's work, not just asserted here.

**A second mutation-quality gap, found while checking the sort mutation against three repeated
runs rather than one.** `used`'s original implementation stored artifact names in a `set`;
`entries()`'s `sorted(entry["used"])` still produced a correctly sorted result, but the "delete
`sorted()`" mutation (`"used": list(entry["used"])`) then reads back a `set`'s **iteration order**,
which is Python's randomized hash order for `str` and not insertion order. The mutant could
therefore have matched the expected sorted list by chance on some process invocations, making the
mutation an unreliable pin. Fixed before it shipped: `used` is now a plain list, deduplicated on
append (`if key not in entry["used"]: append`), so insertion order is a genuine, reproducible fact
(`c, a, b` in Fixture O's construction) and the mutation fails deterministically — re-run three
times in a row to confirm, all three failed.

## The two caches, and why the "must not re-introduce a per-`run_id` assumption" check answers
different objects correctly

Two distinct caches exist and must not be conflated. `UpstreamResolver._records` (built in an
earlier batch, unchanged here) is keyed by the **locator string exactly as given**, for a different
reason: Decision 6's "one answer per run" for `resolve()` itself, so a `run.yaml` re-read mid-run
cannot answer two different absolute-locator calls two different ways, and two *different* locator
strings naming the same run are two independent resolver queries. `UpstreamLedger`'s own storage
(this batch) is keyed by the **resolved `run_id`**, deliberately not by locator — the opposite
choice, for the opposite reason: Decision 6's "one answer per run" for *the record*, so the same
underlying run addressed twice under two different locator strings still accumulates into one
`provenance.upstream` entry. The brief's step 4 wording ("the record is read once per `run_id` and
cached") is loose about which object does the caching — it is the resolver, keyed by locator, that
avoids the re-read; the ledger performs no I/O and merely aggregates under the run_id key. No
per-`run_id` assumption was reintroduced into the resolver; the ledger's `run_id` keying is new and
correct for what it does.

## Disagreements checked against the actual text (grepped, not assumed)

- **Task 7 step 1's citation of `spec-defects.md`** ("already records as deliberately not fixed")
  was grepped rather than trusted: `docs/superpowers/spec-defects.md` § "Six `provenance` and
  `results` keys in the `run.yaml` example that no code writes" does carry the sentence *"Also
  recorded, and deliberately not fixed: the example's `provenance` key order differs from
  `cli.py`'s construction order... Recorded so it is not re-found and mistaken for drift."* The
  brief's claim holds; no disagreement.
- **The same section's `provenance.upstream` row** was stale in the other direction: it still read
  "owner: H8 Studies and reporting" with no closure, even though this task now writes the key.
  Not something either brief mentioned, but `CLAUDE.md`'s rule that `spec-defects.md` is a live
  list where a closed gap is struck rather than left to mislead applies regardless — closed with a
  dated amendment and the row struck, following the file's own `~~struck~~` convention and the
  precedent two paragraphs above it (the H3c1 amendment closing `allocation`/`allocation_hash`).
- **No other disagreement found** between the two briefs, the design's Decision 6/7 text, the
  plan's task 6/7 sections, and the code as built — each literal in both briefs (the four-key entry
  shape, the `f"{step}/{name}"` format, the insertion point, the `[]`-not-`None` rule) was checked
  against the actual `record`/`resolve_run` return shape and `cli.py`'s existing `provenance` dict
  before being relied on, not repeated from the brief's prose.

## Concerns

None outstanding. Arm C stayed green throughout (Decision 4's foundation; no finding to report).
`.superpowers/sdd/2026-08-20-lineage/task-b4-review.md` is untracked in the working tree at the
time of this batch — not created or touched by this batch's work, left as found.

## Fix round 1 — the review's three Minors

Reviewed in `task-b5-review.md` (spec compliance PASS, task quality PASS — all nine prescribed
mutations re-run and failed by the reviewer independently, including a scratch-clone re-run of
`ea8174e` reproducing 2506 exactly). Three Minors, all prose/docstring, no behaviour finding.
Closed all three:

- **Minor 1 — `UpstreamLedger.record`'s docstring claimed a guarantee the code does not provide.**
  *"which is what makes N reads from one upstream do one record read"* was false: the reviewer
  instrumented `read_run_record` and measured **2 reads** for two locators naming one run. The
  ledger performs no I/O at all; the object that collapses reads is `UpstreamResolver._records`,
  keyed by locator. Deleted the false half rather than rewriting it (`CLAUDE.md`: *prefer deleting
  a claim to rewriting it*) — the docstring now says only what `record` itself does (the first-
  sight copy, real and unchanged) and attributes the read-collapsing to `UpstreamResolver._records`
  by name, without claiming a count relationship this method cannot see.
- **Minor 2 — `record.get("code_hash")`/`.get("parameters_hash")` fail open for a corrupt-but-
  parseable upstream record. Filed, not fixed** — the reviewer's own disposition, and correct: it
  is a real open question (refuse a hash-less record as `E-UPSTREAM-RECORD-UNREADABLE`, or accept
  `None` as this build's own honest "not carried" reading) that this batch is not positioned to
  settle, since settling it means deciding whether `read_run_record`'s validation should widen.
  Filed in `docs/superpowers/spec-defects.md` as *"`UpstreamLedger.record` copies a missing hash as
  `None` rather than refusing it"*, **owner named: H9** (`reproduce`, which walks a resolved
  `run_id` back through its recorded ancestors — the design's own routing for "walking a chain
  deeper than one hop, and reporting an unreachable ancestor") **and secondarily H8b** (`diff`,
  the other consumer that would read a silently-`None` hash as a false absence of drift), with the
  check to run before dispositioning it stated in the entry (widen `read_run_record`'s existing
  `run_id`/`schema_version` validation to the two hashes, or document the missing-hash case as
  intentional in `reference.md` § Lineage between runs).
- **Minor 3 — two positional locators in the new `spec-defects.md` amendment, one of them
  ambiguous to the point of contradiction.** The struck row's *"see the amendment below"* resolved
  first to the pre-existing 2026-08-13 amendment, whose own last sentence still reads
  `provenance.upstream` as *"unaffected and still unwritten"* — landing a reader on text that
  appears to contradict the strike, rather than on the entry that actually closes it. Fixed by
  naming the target explicitly: *"see the 2026-08-20 amendment below, not the 2026-08-13 one
  directly beneath this table, whose own last sentence still says `upstream` is unwritten (dated;
  superseded in the same file, not contradicted)"*. The second locator, *"the key-order note two
  paragraphs above"*, named what the note does but stayed positional; replaced with *"the 'Also
  recorded, and deliberately not fixed' key-order note (naming the divergence between `cli.py`'s
  construction order and § The two files' example)"* — no position, so a later insertion cannot
  make it stale the way `CLAUDE.md` names (seven prior instances of exactly this).

**Not changed.** The 2026-08-13 amendment's now-stale sentence itself is not edited — the reviewer
is explicit that it is not a finding: it is dated, and the new 2026-08-20 amendment supersedes it
in the same file without needing the older paragraph rewritten. Consistent with `spec-defects.md`'s
own convention of appending a correction and saying what it replaces, rather than editing history.

**Verified.** `src/publishable/lineage.py`'s docstring edit is a comment-only change (no code
line moved) — re-ran `tests/test_lineage.py`, `tests/test_artifacts.py`, `tests/test_cli.py`
(517 passed, 1 skipped) and then the full, unfiltered suite: **2510 passed, 1 skipped, 2 xfailed**,
unchanged from before this fix round, as expected for a prose-only round. `ruff check .`,
`ruff format --check .` (84 files) and `mypy` (47 files) all clean. `git diff --stat` before
committing touches exactly `src/publishable/lineage.py`, `docs/superpowers/spec-defects.md`,
`tests/test_artifacts.py`, and both `task-b4-report.md`/`task-b5-report.md` — no behaviour file
(`cli.py`, `artifacts.py`, `runner.py`) in the diff, matching "all prose and record hygiene, no
behaviour findings."
