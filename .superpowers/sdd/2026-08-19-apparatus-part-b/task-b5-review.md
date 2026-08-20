# H7d Part B batch 5 review — tasks 7 and 8, the record on a stop and `EXIT_EXTERNAL`'s first reader

Reviewed at `2b88cd4` on branch `h7d-apparatus-part-b`, 2026-08-20. Gates re-run here, not carried:
`uv run ruff check .` clean, `uv run ruff format --check .` (82 files), `uv run mypy` (46 source
files), `uv run pytest` **2452 passed, 1 skipped, 2 xfailed** — the count the report predicts.
Tree left clean; `src/publishable/cli.py` restored byte-identical (`shasum`
`4cf8b022608ca75c9095f07d97b0d27324a2c4f4`) after every mutation, verified by re-running, never by
`git checkout --`.

## The two verdicts

**Spec compliance: FAIL.** One row of Decision 4 is not built. An unreachable apparatus with **zero
results** exits **1**, where Decision 4's table, task 7's own brief, the marker comment on the line
itself, **and `reference.md` § Exit codes and diagnostics in the normative present tense** all say
**5**. Verified by running (Major 1). Everything else this batch was scoped to do is compliant:
Decision 4's other three rows, Decision 14's fresh redacting `Collector`, and Decision 6's two
branches with the status byte and the exit code pinned as separate statements.

**Task quality: PASS, with one overclaim to close.** Every claim in the report that I could re-derive held. Six prescribed
mutations reproduced (plus three of my own), the blind fixture was genuinely blind and its
replacement genuinely discriminates, the credential pin was **strengthened** rather than weakened,
the arithmetic reconciles with nothing deleted, and the one disagreement the batch found against its
own brief (the diagnostic printing unconditionally once reached) was reported honestly and is the
reason two shipped tests had to move. The failure above is a **missing** branch, not a wrong one — but the report
does claim *"no disagreement found in Decision 6's or Decision 4's own text"* and *"both tasks are
scoped exactly as ruled (Decision 4/14 for task 7, Decision 6 for task 8)"*, and both sentences are
false against Major 1 (Minor 7). PASS survives because the report's honest reconciliations — the
+3→+2 delta, the two docstrings its own change falsified, the blind fixture it found and replaced —
outweigh one dropped table row that its own marker comment shows was known to be pending.

**Major 1 blocks this batch.** A fix round must precede B6: task 11 writes rows against emitted
behaviour, so with Major 1 open it would either write a `1`-row corner the document contradicts or
restate a `5` claim the code does not honour (see Minor 5).

---

## Findings

### Major 1 — an unreachable apparatus with zero results exits `1`, not `5`

`src/publishable/cli.py:2556`, with `cli.py:2522`, `cli.py:3676` and
`src/publishable/runner.py:638-644` as the sites that decide it.

Five sources, and they cannot all be right:

| Source | Says |
|---|---|
| Decision 4's table, row 2 | `Unreachable \| 0 \| none \| — \| **5**` |
| Task 7's brief (same table) | `**5** (task 8)` |
| The comment on the line itself | `# task 8 turns the unreachable arm into EXIT_EXTERNAL` |
| `reference.md` § Exit codes and diagnostics | *"That exit code holds **whether or not a record was written** — a probe unreachable before the first execution leaves a run directory with no `run.yaml` to hold a status at all, and still exits `5`"* |
| The code | `if not results: return EXIT_WRONG` — **1**, for both stop reasons |

Task 8 added `EXIT_EXTERNAL` in exactly two places (`cli.py:2522`, the run-start containment for
`E-APPARATUS-RAISED`; `cli.py:3676`, the final mapping), and **neither is on this path**: a probe
raising on the first `pre_execution` round breaks inside `execute_plan`
(`src/publishable/runner.py:638-644`) with `results == []`, so the early return at 2556 fires before
the final mapping is ever reached.

**Decision 4's table has four rows; this batch fixtured three.** Fixture U is *unreachable, ≥ 1*, G1
is *moved, ≥ 1*, Z arm 2 is *moved, 0* — and the fourth row, **unreachable, 0 results, mid-plan**, has
no fixture at all. It is the row that is wrong, and the absence of a fixture for it is why two
batches of review did not see it. The remedy is a fixture as well as a branch.

**Verified by running.** I built the Z-arm-2 schedule with a raise instead of a move (call 1 =
run-start answers `r1`, call 2 raises), and measured: **exit 1**, no `run.yaml`, no `executions.jsonl`,
`latest` absent, `E-APPARATUS-RAISED` rendered to stderr through the collector. The run-start arm
(call 1 raising, Fixture Z arm 1) correctly returns 5, so it is specifically the
zero-results-mid-plan arm that is missing. Note the document sentence quoted above covers **both** —
"before the first execution" is exactly this fixture.

The `reference.md` sentence quoted above is **this branch's own**: `git log -S` places it at
`a59ef6f`, *"H7d Part B task 1: reference.md made consistent about the apparatus"*. The branch's
document task wrote the claim two batches before the code task that owns the reader contradicted it.

The consequence is Decision 6's own stated cost-if-wrong, one code over: `1` is *"the thing you asked
about is wrong — a config that fails validation"*, so a retryable external fault reports as a user
error. No record and no execution is lost (Decision 4 wants none here), which is why this is Major
rather than Critical.

### Major 2 — the same line carries a comment claiming work that has already landed and did not happen

`src/publishable/cli.py:2556`. `# task 8 turns the unreachable arm into EXIT_EXTERNAL` was correct as
a *brief snippet* at task 7's commit and is false at HEAD: task 8 is committed (`11ab231`) and this
arm is unchanged. This is `CLAUDE.md`'s named habit — *a comment claiming a guarantee the code does
not provide* — and the **fifth consecutive batch** to ship one. It is filed separately from Major 1
because the fixes differ: Major 1 needs a branch, and this comment must be **deleted** either way
(prefer deleting a claim to rewriting it). Verified by reading the diff of `11ab231` and by the
measurement above.

### Minor 1 — the new `EXIT_EXTERNAL` containment comment names the wrong code set, and contradicts its neighbour

`src/publishable/cli.py:2515-2521`: *"everything else this `try` contains (a dispatch-time
`E-PLUGIN-LOAD`/`E-PLUGIN-DECORATOR` … never reaches here, so in practice this is `STOP_CODES`' own
members) keeps `EXIT_WRONG`."*

Both halves are wrong, and the comment 30 lines above it in the same function says so: `STOP_CODES`'
members are precisely the ones that **cannot** reach this branch (a mid-plan stop breaks; a run-start
`E-APPARATUS-CHANGED` is what Decision 11 rules out). What actually reaches it and keeps `EXIT_WRONG`
is the four Decision 9 contract refusals from `APPARATUS_CODES`. **Verified by running**: a fixture
whose fact value embeds a declared credential as a substring raised
`E-APPARATUS-FACT-CREDENTIAL`, rendered through this very branch, exit **1**. Fix by naming the four
contract refusals, or by deleting the parenthetical.

### Minor 2 — a `spec-defects.md` paragraph this batch falsified was not re-read

`docs/superpowers/spec-defects.md:7116-7124` (written in batch 4) states that
`test_a_moved_int_valued_credential_is_redacted_through_the_widened_wrapper` *"no longer asserts a
redacted render; it now asserts the credential is absent from stdout and stderr entirely"*, and that
*"the `<redacted:PUBLISHABLE_TEST_TOKEN>` claim above is stale and should not be re-cited as current
behaviour."* Task 7 restored exactly that behaviour and the test asserts
`<redacted:PUBLISHABLE_TEST_TOKEN>` again — verified by running. `CLAUDE.md`: *when you change code a
`spec-defects.md` entry describes, re-read the entry*; a filing whose evidence has gone stale is
worse than one that never had any, which this branch's own ledger already recorded once.

### Minor 3 — the non-`str` carve-out filing under-names its surface: `run.yaml`, not only the ledger

`docs/superpowers/spec-defects.md:7124` scopes the open carve-out to *"reaches
`apparatus/probes.jsonl` unredacted."* **Verified by running**: an `int`-valued declared credential
also lands in **`run.yaml`** under `provenance.apparatus.facts`, because the record holds the
first-answered value and that value *is* the credential. **Pre-existing and not this batch's route** —
attributed by running a clean, non-stopping run with the same shape, which writes both files with the
plaintext and prints nothing. Worth one sentence on the existing entry, not a new filing.

### Minor 7 — the report's "scoped exactly as ruled" and "no disagreement in Decision 4's text" are overclaims

`.superpowers/sdd/2026-08-19-apparatus-part-b/task-b5-report.md`, § Disagreements item 5 and
§ Concerns. Both sentences are falsified by Major 1, and the marker comment the implementer left on
`cli.py:2556` is evidence the arm was known to be pending rather than overlooked — which makes the
claim of exact scoping the weaker of the two. Named so the fix round closes the sentence as well as
the branch.

### Minor 4 — a docstring citation points at the wrong section

`tests/test_cli.py:14435`: the two `W-APPARATUS-UNANSWERED` lines print *"only after `run.yaml` is
written (§ The apparatus files)"*. The ordering claim is **true** (verified by code placement and by
the run), but § The apparatus files does not state it; § Warnings core reports does (*"printed to
stdout through a `Collector` at run end"*). Re-cite or drop the parenthetical.

### Minor 5 — `reference.md`'s unconditional "its record is kept" is now false, and is still owed

`docs/reference.md:3099`: *"The run is marked `status: failed`, and its record is kept rather than
discarded"* — unconditional, while Decision 4 rules `Moved | 0 results → none | exit 1`, which this
batch built and which I confirmed by running (Fixture Z arm 2's shape: no `run.yaml`, exit 1).
§ Exit codes' `1` row does not name the corner either. **The qualification did not land in this
batch** — the b5 diff touches no `docs/` file, and task 11 (batch 6) owns the rows — so this is
*unlanded and owned*, not a fault of tasks 7/8. Flagged for two reasons: the document is now false
against shipped code, and **task 11 must not write the `1` row's corner while the `5` row's corner
(Major 1) is broken**, or the document will describe behaviour the code does not have. The twin
sentence in § Exit codes (the unreachable/no-record case) is already there and is the one Major 1
contradicts.

### Minor 6 — a rewritten docstring quotes a claim it deleted from itself

`tests/test_cli.py:13210`: *"Its docstring's 'exit non-zero' claim stays true either way"* — the
docstring that made that claim is the one this edit replaced, so the sentence now refers to nothing
in the file. Harmless, but it is the shape of the habit the last four batches were fixing; the honest
form is to state what the test asserts.

---

## What I verified by running, item by item

**1. The credential regression test's update: STRENGTHENED, and strictly so.** The update is
**additive** — `assert "13579" not in output` survives untouched, and `E-APPARATUS-CHANGED in output`
plus `<redacted:PUBLISHABLE_TEST_TOKEN> in output` were added. Sweeping every removed line in
`git diff 12e6d7d..HEAD -- tests/test_cli.py` confirms the only assertions deleted anywhere in the
batch are the three now-false `"… not in output"` negatives; **no credential-absence assertion was
removed.** Unlike the previous batch's update (which traded a redaction check for an absence check),
this one keeps both, so it is a superset of what it replaced.

Beyond the shipped test I built four fixtures of my own and drove them end to end:

| Fixture | Result |
|---|---|
| `int` credential, **moved** stop, ≥ 1 results | streams: `<redacted:…>` present, plaintext **absent**; exit 4 |
| `int` credential, **unreachable** stop, ≥ 1 results, with the credential's digits **inside the raise message** | streams: plaintext **absent**; `status: partial`, exit 5 |
| credential as a **substring** of a longer `str` fact value | refused at `check_facts`; plaintext absent from **streams and every file**; exit 1 |
| clean run, `int` credential fact (attribution control) | plaintext on disk, nothing on streams |

**No credential reaches stdout or stderr on either stop path, in any of the four shapes.**
**Positive control**: unwiring `stop_c.credentials = credentials` made the plaintext `int` credential
appear on stderr and failed **both** my fixture and the shipped regression test — so that assertion
is reachable and does catch a real leak. Disk side: the `int` credential is on disk in
`apparatus/probes.jsonl` **and `run.yaml`**, pre-existing and filed (Minor 3), no new route created
here; the sweep proved it can see a leak by finding those hits.

**2. What survives a stop.** Fixture U (unreachable, ≥ 1 results): `run.yaml` with `status: partial`,
`latest` present, `executions.jsonl` 2 of the 4-line `sweep.yaml` plan both `completed`,
`apparatus/probes.jsonl` 3 lines, diagnostic on stderr, exit 5. Fixture G1 (moved, ≥ 1 results): the
same shape with `status: failed`, 4 probe lines, exit 4. Fixture Z arm 2 (moved, 0 results): no
`run.yaml`, no `executions.jsonl`, 2 probe lines, `latest` and `latest.txt` both absent, exit 1.

**The zero-results guard is sited before BOTH sinks, and each site is pinned by its own assertion.**
I reproduced both prescribed mutations and added a third that the report did not run:

- unconditional early return → G1 and U fail (no record at all);
- guard removed (`if False:`) → Z arm 2 fails, `run.yaml` written **and** `latest` repointed, exit 4;
- **guard moved to sit after the `run.yaml` write and before `point_latest`** → Z arm 2 fails on
  `not (run_dir / "run.yaml").exists()` specifically. This is what separates the two sinks: without
  it, both mutations fail on the exit code and neither shows the `run.yaml` half is independently
  pinned.

One imprecision in the report: under the unconditional-return mutation, G1 and U fail on
`run_a_project`'s **exit-code** assertion before their `run.yaml` assertions are reached. The
mutation is caught; the reported mechanism is one assertion off.

**3. `provenance.apparatus.facts` holds the first-answered value; the ledger holds the mover.**
Verified on my own fixture (facts move `r1 → r2` on call 3): `run.yaml`'s
`provenance.apparatus.facts["00"]["rev"] == "r1"` while `apparatus/probes.jsonl`'s last line carries
`"r2"`. The asymmetry Decision 1's single-authority grounds rest on holds, and G1's shipped
assertions recompute both from the artifacts rather than transcribing them.

**4. The replaced blind fixture discriminates.** Appending the stop diagnostic to `c` instead of a
fresh `Collector` leaves Z arm 2, G1 and U **all green** — the blindness the implementer reported is
real — and fails `test_the_stop_diagnostic_prints_through_a_fresh_collector_not_c` on its rendered
counts line (`2 problems (1 error, 1 warning)` against the asserted `1 problem (1 error, 0
warnings)`). It is not an absence-only control: it also asserts `E-APPARATUS-CHANGED` on stderr and
`W-REPL-DETERMINISTIC` on stdout, both of which must report.

**5. Task 8's codes.** `5` over `3` verified by running: deleting the final `stop.reason` branch makes
Fixture U exit 3 while `status: partial` is unchanged — which is why the two must be separate
statements, and they are. Widening the branch to the moved reason too makes G1 (and the int-cred test)
fail 5 against 4. Plan correction 3's widened `run_a_project` guard is real and needed; the suite
count landing at 2452 with no test deleted is the measurement that stands in for it.

**7. The batch-1 pin and the protected test are untouched.** `git diff 12e6d7d..HEAD` shows no hunk
in either; all four (`test_a_clean_run_completes_with_the_full_run_yaml_shape`, arms B and C, and
`test_max_failed_fraction_is_measured_against_the_test_partition`) re-run green in isolation. On the
sub-question: **this batch adds no `run.yaml` key at all** — the entire `src/` delta is two branches,
one assert and comments, with no write into the record document — so the arm-A boundary (a stop-path
key invisible to all three arms) is not exercised. G1's new whole-key-list assertion on a **stop**
path narrows that boundary in the batch's favour.

**8. The arithmetic.** `git diff 12e6d7d..HEAD -- tests/test_cli.py | grep -E "^[+-]def test_"` gives
exactly two additions and **zero deletions**; 2450 + 2 = 2452, matching my own full run. The report's
"+3 predicted, +2 measured" reconciliation is correct and nothing was silently removed.

**9/10. Prose.** No docstring claims a § Errors row, no invented fixture name, no count phrase, no
positional table locator, no bare `x` for multiplication. Findings Minor 4 and Minor 6 are the two
prose defects. No sentence anywhere in the diff mentions unblocking a config, an executable count,
`six`, or `three` — swept over the whole batch diff.

## The new assert's safety argument, made to fire

`cli.py:2543` is a new bare `assert stop.code is not None and stop.message is not None` **inside** the
stop branch, whose comment argues it cannot fire because reason, code and message are set together at
one call site. `CLAUDE.md` requires that claim to be mutated rather than believed, and the precedent
is exactly this branch's subject. I made it fire — deleting
`stop.code, stop.message = exc.code, str(exc)` from `runner.py`'s gate — and drove Fixture U:

- an **uncaught `AssertionError` traceback**, not a diagnostic;
- the run directory holds `executions.jsonl` with its **2 paid-for executions**, `apparatus/`,
  `environment`, `manifest`, `sweep.yaml`, both step output directories — and **no `run.yaml`, no
  `latest`**.

So the cost of a fire is precisely *every execution paid for, the record lost*. **This is not a
finding**: the invariant holds at the one call site that can set a reason, no config can reach it, and
plan correction 2 explicitly blesses a bare assert about core's own callers on `execute_plan`'s
precedent. It is recorded because the assert sits four lines from the guard whose siting I verified,
its cost was previously unmeasured, and a future slice adding a second reason-setting call site
inherits that cost silently.

## What I could not check

- **The isolated measurement behind task 7 step 2** (that widening `run_a_project`'s guard alone left
  the count at task 12's number). I can only confirm the aggregate: 2452 with two net-new tests and
  no deletions, which is consistent with it.
- **`5` winning over `4`.** No fixture can reach it — `run_status` maps `apparatus_unreachable` to
  `partial` unconditionally — so I verified it **by placement**: the `stop.reason` branch precedes the
  `{...}.get(status, EXIT_FAILED)` return, so any status yields 5. Decision 6 deliberately declines a
  fixture and a filing for that composition, and I am not proposing one.
