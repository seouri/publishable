# Batch 4 review — tasks 5 and 6 (`StopSignal`/the `break`, and `run_status`'s contract)

**Reviewed at `8aa2cfd` on branch `h7d-apparatus-part-b`. Measured on 2026-08-20.**

Gates, run directly in the foreground: `uv run ruff check .` **All checks passed**;
`uv run ruff format --check .` **82 files already formatted**; `uv run mypy` **Success, 46 source
files**; `uv run pytest` **2450 passed, 1 skipped, 2 xfailed** (156 s). The arithmetic checks out and
is itself evidence no pin was deleted: 2442 (batch 3) + 3 (task 5) + 5 (task 6) = **2450**, so three
tests were *updated* and none removed.

## Two verdicts

**Spec compliance: PASS, with one deviation from Decision 4 that this batch created and does not
own the fix for.** The mechanism is Decision 3's (`break`, one seam, `apparatus.STOP_CODES` only,
every other code re-raised); the status contract is Decision 5 as the controller narrowed it
(`max_failed_fraction` keeps `completed`, its reason threaded and **genuinely read**); Decision 10
holds (no retry, verified by counting the probe's own calls); Decision 12 holds (`planned` is a
keyword, nothing writes it — confirmed against a real `run.yaml`'s key list); Decision 13 holds
(`StopSignal` is absent from `src/publishable/__init__.py` and reaches no artifact). The deviation:
a **zero-results** apparatus stop now writes `run.yaml` and repoints `latest`, which Decision 4's
own table refuses. Reachable today, unpinned, and unmentioned in the report. Task 7 owns the branch
that closes it.

**Task quality: PASS, and the honesty is the strong part.** Both prescribed negative results are
real and are reported as findings rather than dressed up; the three shipped end-to-end tests were
updated for a mechanically forced reason with each docstring recording the disagreement; the
protected pin and arm A were not touched at all. What the batch did not do is re-read the comments
and the filing that its own wiring falsified — three of them, in the same direction, which is the
`CLAUDE.md` habit *a fix that carries its own justification is not thereby verified*.

**Nothing here blocks the batch.** The one Major with a live consequence has an owner (task 7) and
lands in the next batch; the rest is prose and a dead branch.

---

## Item 1 (the top item): can a credential reach a stream on the stop path? **No.**

**Verified by running, on my own fixtures** (`tests/test_zz_b4_review.py`, written for this review
and deleted before it was filed), at `run`, with the stop firing, for both codes and both credential
shapes:

| Fixture | Shape | Result |
|---|---|---|
| `E-APPARATUS-CHANGED`, mid-plan | declared credential `13579` returned as an **`int`** fact that then moves | exit 4, `status: failed`, **`13579` absent from stdout and stderr** |
| `E-APPARATUS-RAISED`, mid-plan | probe raises `RuntimeError("auth failed for token sekret-42-live …")` — the credential a **substring of a longer string** | exit 3, `status: partial`, **`sekret-42` absent from stdout, stderr, and every file in the run directory** |
| `E-APPARATUS-RAISED`, run-start (**positive control**) | same message, raised on the first call | `<redacted:PUBLISHABLE_TEST_TOKEN>-live` printed — proves my fixture *can* see a leak |
| `E-APPARATUS-FACT-CREDENTIAL` | a **`str`** fact containing the credential | refused by `check_facts` before anything is recorded, redacted diagnostic, exit 1 |

Nothing prints on the stop path at this commit, so there is no stream for a credential to reach.
The residual is the one already filed and unassigned: `apparatus/probes.jsonl` still holds
`"serial": 13579` on disk (`check_facts`'s non-`str` carve-out), which I re-confirmed by reading the
ledger back — pre-existing, not created here.

**Was updating batch 3's credential regression test honest and necessary? Yes to both, and it did
not weaken the pin.** Necessary: task 6 step 3 *is* the wiring, and once `stop` reaches
`execute_plan` the raise cannot reach `command_run`'s containment, so the old assertion (a rendered
redaction) has nothing to assert on. Not weakened — **verified by running**: with
`E-APPARATUS-CHANGED` dropped from `apparatus.STOP_CODES` (task 5's mutation (b)), the raise escapes
to `main`'s bare printer, `E-APPARATUS-CHANGED … changed: 13579 → 999` reaches stderr, and
`test_a_moved_int_valued_credential_is_redacted_through_the_widened_wrapper` **fails**. Its
assertion moved from "a redacted render is present" to "the credential is absent", which is the
stronger property, and it is not absence-only: it is paired with `status: failed` and `EXIT_FAILED`,
which must report.

**What the edits did drop, accounted for:** G1 lost `"pinned" in stderr` / `"r1 → r2" in stderr` /
`not run.yaml.exists()`, and the int-cred test lost `_assert_went_through_the_containment_wrapper`.
Decision 2's message shape is **still pinned by direct call** — `tests/test_apparatus.py:715`
asserts `"r1 → r2" in message` — so no pin was lost, only the end-to-end witness that a stop is
*reported to the operator at all*, which task 7 step 3 restores and which G1's updated test guards
as negative space in the meantime.

---

## Findings

### Major 1 — a zero-results apparatus stop writes `run.yaml` and repoints `latest`, which Decision 4 refuses

**`src/publishable/cli.py:2513`** (the `run_status(results, planned=len(plan), stop=stop.reason)`
call, reached with `results == []`).

**Verified by running.** A probe that raises on its second call — the first `pre_execution` round —
breaks the loop with an empty `results`. Measured: exit **3**, `run.yaml` **written**
(`status: partial`, `execution: {shared: {}, conditions: [], summary: {}}`), `latest` **repointed at
it**, no `executions.jsonl`, and **no diagnostic printed at all**. Decision 4's table and task 7's
own restatement say: *"With **no** results, nothing was paid for … a redacted diagnostic, no
`run.yaml`, `latest` untouched."* Before this batch that corner was accidentally compliant (the
raise escaped to containment: exit 1, no `run.yaml`); task 6's wiring moved it to non-compliant,
with no fixture covering it and no mention in the report.

**The useful half, recorded for task 7:** it does **not** crash. That settles the plan's
§ What could not be measured item 1 — *"whether a `run.yaml` can be assembled over an empty results
list"* — empirically, in the safe direction.

**Route, made actionable:** task 7 step 1's `if not results: return EXIT_WRONG` closes this only if
it is sited before **`assemble_run_yaml`** *and* before the **`latest` repoint** — I measured both
happen today. "Immediately after `execute_plan` returns and before the aggregate phase" is not by
itself sufficient guidance, because `latest` is repointed on that same path.

### Major 2 — the `STOP_CODES` docstring asserts a state the code contradicts

**`src/publishable/apparatus.py:521-523`**: *"Fixture U (task 5's own truncation pin,
`status: partial`, exit 5) remains owed by task 5, since `execute_plan`'s `break` does not exist
yet."* At HEAD the `break` exists (the `break` at `runner.py:644`) and Fixture U exists
(`test_g_fixture_u_unreachable_mid_plan_at_this_commit`), which asserts `EXIT_PARTIAL`, not exit 5.
The neighbouring clause at **`apparatus.py:517-520`** — both members *"going through
`_assert_went_through_the_containment_wrapper`, the same discriminator"* — is false in the same
direction: the int-cred test no longer calls that helper, by this batch's own edit.

**Verified by reading the code the clause describes and by running the tests it names.** This is the
named habit *when you change a guard, re-read its justification*, and per `CLAUDE.md` the fix is to
**delete the two clauses**, not to rewrite them — the constant's set-equality pin and the two named
end-to-end tests are self-maintaining without them.

### Major 3 — the containment filter's `STOP_CODES` arm is now unreachable and unpinned, under a comment that says it is load-bearing

**`src/publishable/cli.py:2500`** (`if exc.code not in apparatus.APPARATUS_CODES and exc.code not in
apparatus.STOP_CODES:`) with the comment at **`cli.py:2496`**: *"until then, this widened filter is
what keeps a live leak from shipping in the meantime."*

**Verified by running the mutation against the full suite**: narrowing the filter back to
`APPARATUS_CODES` alone leaves the suite at **2455 passed, 1 skipped, 2 xfailed** (2450 + my 5
review tests) — **byte-identical outcome, nothing catches it**. It is unreachable, not merely
unpinned: `E-APPARATUS-RAISED` is already an `APPARATUS_CODES` member, a mid-plan stop of either
code now `break`s instead of raising, and the only path left — `E-APPARATUS-CHANGED` from the
run-start round — is the one Decision 11 rules out and task 13 pins. This is plan correction 4's own
warning about unpinned members of that enumeration, arrived at from the other side.

Two prose consequences of the same fact, both stale at HEAD and both better deleted than rewritten:
- **`src/publishable/apparatus.py:390-395`** — `check_changed`'s docstring names the widened filter
  as the interim mitigation for the non-`str` residual. It mitigates nothing at HEAD.
- **`docs/superpowers/spec-defects.md:7113-7118`** — *"Verified by running:
  `test_a_moved_int_valued_credential_is_redacted_through_the_widened_wrapper` … shows
  `<redacted:PUBLISHABLE_TEST_TOKEN>` in place of `13579` in both stdout and stderr."* That test
  asserts no such thing now. `CLAUDE.md`: *when you change code a `spec-defects.md` entry describes,
  re-read the entry.*

**Route:** the branch itself is task 7's to replace under Decision 14 — I am not recommending its
deletion in this review, only the deletion of the three claims about it.

### Minor 1 — positional locators, two of them across files

**`tests/test_runner.py:2149`** (*"the two-entry mapping above … the truncation assert below"*) and
**`tests/test_runner.py:2170`** (*"the same short list that raises above"*): the mapping and the
assert are in `src/publishable/run_record.py`, not above or below anything in this file, and "raises
above" points at the preceding test function by position. **`tests/test_cli.py:14484`** (*"Fixture
G1's test above"*) is the same shape. `CLAUDE.md`: name what the sibling *does*.

### Minor 2 — a test name that encodes a commit

`test_g_fixture_u_unreachable_mid_plan_at_this_commit` (`tests/test_cli.py`). Its body has already
been rewritten once for a different "this commit" and tasks 7 and 8 will both move it again. Not
introduced by a rule this repo has written down; noted because a reader greps for a name.

---

## The two negative results, adjudicated

**Task 5 mutation (b) — "the brief named the wrong test".** *Correct at task 5's commit, and
superseded at HEAD.* Verified by running: with `E-APPARATUS-CHANGED` removed from `STOP_CODES`,
`test_g1_ordering_chain_appends_before_the_gate_fires_end_to_end` now **does** fail (it asserts
`EXIT_FAILED` and reads `run.yaml`, and the mutation gives exit 1 with no `run.yaml`), as do
`test_stop_codes_holds_exactly_the_two_codes_execute_plan_breaks_on` and the int-cred test. The
implementer measured G1 at task 5, where it still asserted `EXIT_WRONG` and no `run.yaml` — both
true under either branch, hence blind. So: honest finding, correctly reported, and task 6's own
wiring is what turned G1 into the discriminator the brief predicted.

**Task 6 mutation (d) — "could not be built distinct from (c)".** *Confirmed, and it is stronger
than "collapses".* As described — *suppress the assert for every stop rather than for a recorded
reason* — (d) is **exactly what the shipped code already does** (`if planned is not None and stop is
None`), so it is not a mutation at all; the brief asked for a discriminator in a direction where
none exists. **A distinct discriminator does exist, in the inverse direction, and it is not blind**:
dropping `and stop is None` (assert for *every* stop) fails **three** tests — the direct pin
`test_run_status_max_failed_fraction_suppresses_the_truncation_assert` **and both end-to-end
truncation arms**, which crash on `AssertionError: execute_plan returned 1 results against a plan of
8`. **Verified by running.** That is the answer to item 3 as well, below.

---

## The controller's ruling, item by item

- **`max_failed_fraction` keeps `completed`.** Verified by running: arm B still reports
  `completed`/exit 0, arm C `partial`/exit 3, and both still discriminate — mapping the reason to
  `partial` fails arm B; mapping it to `failed` fails **both** arms.
- **The third reason is threaded and genuinely read.** Not a documented no-op that nothing reads:
  deleting the branch that reads it (dropping `and stop is None` at `run_record.py:50`) fails the
  direct pin **and both end-to-end arms**. Verified by running. Worth carrying — the design's claim
  that this guard is *"blind end to end"* is true only of the deletion direction, not of the
  over-broad-suppression direction.
- **A truncation with no reason still raises, as a bare `assert`.** `run_record.py:50-55`, a bare
  `assert` with no code minted and no § Errors row owed (plan correction 2 honoured). Mutation (c),
  run myself: disabling the guard fails only
  `test_run_status_asserts_on_a_silent_truncation_with_no_stop_reason` — the direct-call pin, exactly
  as the design says to expect.

## The batch-1 pin and the protected test

**Verified independently of the report**, by extracting each function body at `0c1d094` (the commit
before task 5) and at HEAD and diffing them:

| Test | Removed lines | Added lines |
|---|---|---|
| `test_an_all_completed_truncation_stays_completed_at_exit_0` (arm B) | **0** | 8 |
| `test_a_mixed_truncation_is_partial_at_exit_3` (arm C) | **0** | 5 |
| `test_a_clean_run_completes_with_the_full_run_yaml_shape` (arm A) | 0 | **0** |
| `test_max_failed_fraction_is_measured_against_the_test_partition` | 0 | **0** |

Append-only for B and C, untouched for A and for the protected pin. The appended lines are what task
6 step 5 asked for (*"each must additionally assert that no apparatus diagnostic was printed"*), and
both arms still discriminate, per the mutations above. The suite arithmetic (2442 + 3 + 5 = 2450)
independently rules out a silent deletion anywhere else.

## Decision 10 — a stop never retries, and the paid-for record survives

**Verified by running**, counting the probe's own module-level call counter after the run: a probe
raising on its third call is called **exactly 3 times**, `executions.jsonl` holds the **1** execution
that was paid for with `status: completed`, its artifact directory (`seed47/`) is on disk,
`apparatus/probes.jsonl` holds the **2** completed calls (nothing appended for the raise), and
`run.yaml` is written with `status: partial` against a 4-execution plan in `sweep.yaml`. This is the
inversion of Part A's *every execution paid for, the record lost* — for the non-empty case. **No
comment in this batch claims a path cannot raise**; the one comment making a reachability claim
(`STOP_CODES`' run-start clause) explicitly declines to, and points at task 13's fixture.

## Item 6 — task 7's plan text versus its own snippet, adjudicated

The flag is real. **Task 7 step 1's snippet governs; step 4's `expect_exit=EXIT_WRONG` is the stale
literal.** Grounds: the snippet returns `EXIT_WRONG` only `if not results:`, and Fixture U's stop
leaves **2** completed executions, so it falls through to the pre-existing exit tail —
`EXIT_PARTIAL`. Decision 4's own table agrees (unreachable, ≥ 1 result → `run.yaml`, `partial`,
exit 5 *at task 8*), and Decision 6 is explicit that 5 arrives with task 8 and not before. Step 4's
`EXIT_WRONG` is inherited from Fixture U's pre-task-6 shape, which task 6 dissolved.

**So task 7 changes no `expect_exit` literal for Fixture U at all** — HEAD already asserts
`EXIT_PARTIAL` — and what it adds there is the diagnostic assertions plus the `latest` check. Task 7
step 5 (Fixture Z arm 2) is where Major 1 above must be closed, and its stated expectations (no
`run.yaml`, `latest` and `latest.txt` both absent) are exactly the assertions HEAD would fail.

## Prose sweep

- **No docstring names a § Errors row.** Two added sentences mention one (`run_record.py:43`,
  `tests/test_runner.py:2161`) and both say a coded error *would owe* a row it does not mint —
  an argument for not minting, not a claim about a document. Task 11's surface untouched.
- **Every backticked `test_*` name in the batch's added lines resolves to a real `def`** — checked
  mechanically over all 580 added lines against `tests/`.
- **No count phrases, no `x` for `×`** in the added lines.
- **No sentence claims this slice unblocks a config.** Zero configs, six with no remaining core-side
  blocker, three executable — all three figures unmoved and unmentioned, which is correct.
- **Build facts are dated where they appear** in the design's appended correction (2026-08-20) and
  are scoped as *"at this commit"* in the three updated docstrings.
- Positional locators are Minor 1 above.

## What I could not check

- **Whether any of this composes with `resume`, `dry-run`, `freeze`, `diff` or `reproduce`.** All
  five print *specified but not built*; every claim about them stays a spec claim.
- **Whether `EXIT_EXTERNAL`'s arrival (task 8) can reach Major 1's corner** — the zero-results
  unreachable row wants exit 5 with no record, and that combination has no code at HEAD to measure.
- **The end-to-end blindness of mutation (c)** — I ran it against the `run_status` and truncation
  subset only, not the full suite; the full-suite measurement (1 failed, 2449 passed) is the
  implementer's, and it is consistent with the structural argument that no reachable `run` truncates
  without a reason.
- **A real metered probe.** Every fixture here is a fake this repo wrote, as the plan requires.

## Tree

`tests/test_zz_b4_review.py` (this review's own fixtures) was deleted after the final measurement.
Every mutation was applied from a `/tmp` backup copy and reverted by copying it back, never with
`git checkout`, and each revert was verified by `diff` against the backup **and** by re-running the
suite. Final state: `uv run pytest` **2450 passed, 1 skipped, 2 xfailed**; `git status --short`
empty apart from this review file. **The tree is clean.**
