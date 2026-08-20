# Tasks 5 and 6 report

**Status: both tasks complete, suite green.**

**Commits:**
- `e056ef7` — H7d Part B task 5: StopSignal and the break, on max_failed_fraction's precedent
- `f1b2a7a` — H7d Part B task 6: run_status's contract, widened for the apparatus only

**Test summary:** `uv run pytest -q` → **2450 passed, 1 skipped, 2 xfailed** (baseline 2442 + 3 at
task 5 + 5 at task 6). `ruff check .`, `ruff format --check .`, `uv run mypy` all clean (46 source
files).

## Batch-1 pin and the protected test

The batch-1 guard pin's arms B and C (`test_an_all_completed_truncation_stays_completed_at_exit_0`,
`test_a_mixed_truncation_is_partial_at_exit_3`) received **only appended lines** — confirmed by
`git diff` hunk inspection (`@@ -14283,6 +14290,14 @@ ...` and `@@ -14318,6 +14333,11 @@ ...`, both
pure additions, no `-` lines in either function's original body) and by sha256 over the original
line ranges before editing (arm B `292f1f0e...a5`, arm C `f283c490...71b`), which I re-verified
matched the pre-edit bytes exactly before adding the new assertions. Arm A
(`test_a_clean_run_completes_with_the_full_run_yaml_shape`) was not touched at all.

`test_max_failed_fraction_is_measured_against_the_test_partition` (the protected docstring/pin) was
**not touched** — no edit to its body or its argument.

## Task 5

`StopSignal` (dataclass: `reason`, `code`, `message`, all `| None = None`) added beside
`ExecutionResult` in `runner.py`, not exported, not written into any artifact. `execute_plan` gains
`stop: StopSignal | None = None`. The per-execution probe round is now wrapped:

```python
if observer is not None:
    try:
        observer.observe_round(phase="pre_execution", condition_index=execution.condition_index)
    except ContractError as exc:
        if stop is None or exc.code not in apparatus.STOP_CODES:
            raise
        stop.reason = ("apparatus_unreachable" if exc.code == "E-APPARATUS-RAISED" else "apparatus_changed")
        stop.code, stop.message = exc.code, str(exc)
        break
```

`max_failed_fraction`'s existing `break` now also sets `stop.reason = "max_failed_fraction"` when
`stop is not None`.

Direct-call tests in `test_runner.py`: a fake observer raising on its Nth round breaks the loop and
records the reason without the exception escaping; a Decision-9 contract code (`E-APPARATUS-FACT-MISSING`)
still escapes unconditionally even with a `StopSignal` given. Fixture U (unreachable, mid-plan) added
end to end in `test_cli.py`, using the design's own probe module verbatim.

### Mutations, task 5

- **(a) widen the filter to `apparatus.APPARATUS_CODES`**: the escape test
  (`test_a_stop_signal_re_raises_a_contract_refusal_unchanged`) **FAILED** as prescribed
  (`DID NOT RAISE ContractError`) — reached its named assertion, not a crash. Reverted, re-verified
  identical to backup by diff.
- **(b) drop `E-APPARATUS-CHANGED` from `apparatus.STOP_CODES`**: **the brief's named test
  (`test_g1_ordering_chain_appends_before_the_gate_fires_end_to_end`) did NOT fail** when run alone —
  a real finding, not assumed away. I verified the mutation does change behaviour (a probe-render
  check showed the diagnostic switching from the Collector's two-line-plus-trailer format to `main`'s
  bare one-line format, i.e. the raise genuinely stopped going through `command_run`'s containment),
  but G1's own assertions (`"pinned" in stderr`, `"r1 → r2" in stderr`, `EXIT_WRONG` either way, no
  `run.yaml` either way) cannot see that difference. Run against the **full, unfiltered suite**, the
  mutation **is** caught — by two *other* tests: `test_stop_codes_holds_exactly_the_two_codes_execute_plan_breaks_on`
  (a set-equality pin in `test_apparatus.py`) and
  `test_a_moved_int_valued_credential_is_redacted_through_the_widened_wrapper` (batch 3's own Major-1
  regression test, whose entire point is `E-APPARATUS-CHANGED`'s `STOP_CODES` membership). So: the
  brief named the wrong test as the discriminator; the actual pins are elsewhere and they hold.
  Reverted, re-verified identical to backup by diff.

## Task 6

`run_status(results, *, planned=None, stop=None)` moved to `run_record.py` (per § Corrections,
correction 1 — it already lived there, not in `runner.py`). A module-level
`_STOP_REASON_TO_STATUS = {"apparatus_unreachable": "partial", "apparatus_changed": "failed"}` is
consulted first; `max_failed_fraction` is deliberately absent and falls through unchanged. The
truncation guard is a bare `assert` (§ Corrections, correction 2), not a coded `ContractError`.
`cli.command_run` constructs one `StopSignal`, passes `stop=stop` into `execute_plan`, and calls
`run_status(results, planned=len(plan), stop=stop.reason)`; `planned` is not written into `run.yaml`
(Decision 12).

Direct-call pins added in `test_runner.py`: each of the three reasons, the truncation assert firing
with `stop=None`, and the same truncation folding (not asserting) with `stop="max_failed_fraction"`.
That is 5 new tests, not the brief's stated 4 — a minor reconciliation miss, noted rather than forced
to fit.

### The cliff advisor flagged, confirmed by running it

Task 6 step 3's own wiring — `stop=stop` into `execute_plan` — has a consequence neither brief
mentions: once an apparatus stop no longer raises out of `execute_plan` (task 5's mechanism), it no
longer reaches `command_run`'s own `except ContractError` containment either. `command_run` falls
through to its ordinary completion path, and the pre-existing exit tail
(`{"completed": EXIT_OK, "partial": EXIT_PARTIAL}.get(status, EXIT_FAILED)`) now decides the exit code
— `EXIT_FAILED` for `"failed"`, `EXIT_PARTIAL` for `"partial"` — **before task 7 has added any
diagnostic-printing code and before task 8's `EXIT_EXTERNAL` branch exists.** This broke three shipped
end-to-end tests that asserted the pre-task-6 shape (`EXIT_WRONG`, no `run.yaml`, a printed
diagnostic):

1. `test_g1_ordering_chain_appends_before_the_gate_fires_end_to_end` (task 4's fixture)
2. `test_g_fixture_u_unreachable_mid_plan_at_this_commit` (task 5's own fixture, written this batch)
3. `test_a_moved_int_valued_credential_is_redacted_through_the_widened_wrapper` (batch 3's Major-1
   regression test)

I updated all three to the honest, mechanically-necessary state at task 6's own commit (`run.yaml`
now written with the correctly-mapped status; exit code from the pre-existing tail; **nothing**
printed about the stop, since Decision 14's Collector is task 7's addition — verified for the
credential test that `"13579"` still never appears in output, which is if anything a stronger
safety property than the interim mechanism it replaces). Each docstring states the disagreement
with its own prior text explicitly rather than silently overwriting it, and none of the three
touches anything about the *shape* of `run.yaml`'s record beyond the `status` key — no key-list
assertions, no provenance assertions, no warning-count assertions — leaving that fully to task 7,
per "task 7 owns what `run.yaml` holds on a stop."

**This is a real disagreement with both briefs, not merely with the design's exploratory prose**:
task 6's own brief is silent about this consequence, and it is task 6's step 3 — not task 7's — that
causes it. Task 7's own plan text ("the exit code and the presence of `run.yaml` are task 7's ...
since `break`ing the loop (task 5) does not by itself give the stop a record") is the specific claim
that does not survive contact with the code once task 6's wiring lands; that attribution belongs to
task 6, mechanically, regardless of which task's *brief* mentions it. I did not attempt to resolve
task 7/8's own apparent internal inconsistency (task 7 step 4's text says Fixture U's `expect_exit`
stays `EXIT_WRONG` "at this commit" even with `status: partial` and non-empty results, which the
task 7 code snippet's own `if not results: return EXIT_WRONG` guard does not produce for a non-empty
`results` list) — that is squarely task 7's to reconcile, and I flag it here rather than guessing.

### Mutations, task 6

- **(a) map `max_failed_fraction` → `partial`**: arm B **FAILED** exactly as prescribed
  (`partial`/exit 3 against asserted `completed`/exit 0). Reverted, diff-verified clean.
- **(b) map `max_failed_fraction` → `failed`**: arm C **FAILED** exactly as prescribed
  (`failed`/exit 4 against asserted `partial`/exit 3). Reverted, diff-verified clean.
- **(c) delete the truncation assert**: **blind end to end** (full suite: 1 failed, 2449 passed) —
  only the direct-call pin (`test_run_status_asserts_on_a_silent_truncation_with_no_stop_reason`)
  caught it, exactly as the design says to expect. Reverted, diff-verified clean.
- **(d) suppress the assert for every stop rather than for a recorded reason**: constructed as
  `if planned is not None and False:` — I could not build a mutation textually distinct from (c) that
  still matches the brief's description, because by the time execution reaches the assert's guard,
  `stop` can only be `None` or `"max_failed_fraction"` (the two apparatus reasons already returned
  earlier via `_STOP_REASON_TO_STATUS`), so "suppress for every stop" and "suppress for the one
  recorded reason that can still be here" collapse to the identical observable code path in this
  implementation. Run, it produced the **identical** result to (c): blind end to end, caught only by
  the same direct-call pin. Reported rather than dressed up as a distinct discriminator. Reverted,
  diff-verified clean.

## Disagreements found, and what was and wasn't done about them

1. **Task 5 mutation (b) is caught by different tests than the brief names** — reported above, not
   silently reattributed as a pass on the named test.
2. **Task 6's wiring changes three end-to-end tests the brief does not mention** — G1, Fixture U, and
   the Major-1 credential test. Updated to the honest post-task-6 state, with each docstring recording
   the disagreement rather than erasing the prior claim. This is the only way I found to keep
   "task 5 → task 6, in order, each committed with the suite green" true, given task 6's own step 3 is
   explicit about wiring `stop=stop` into `execute_plan`.
3. **Task 7's own plan text (step 4, Fixture U) appears to contradict its own code snippet** for the
   non-empty-results case. Not resolved here — flagged for whoever picks up task 7.
4. **5 new direct-call tests for `run_status`, not 4** — the brief's count and mine differ; not
   forced to fit.

No changes were made to `run.yaml`'s record shape, to any diagnostic-printing code, or to
`EXIT_EXTERNAL`. Task 7 and task 8's own work is untouched.
