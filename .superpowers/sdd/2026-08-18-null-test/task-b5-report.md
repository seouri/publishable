# H4d batch 5 report — tasks 21, 22, 23, 25+26, 28, 29

## Status

All seven tasks complete and committed, in order (21 → 22 → 23 → 25+26 → 28 → 29). Gates clean:
`ruff check .`, `ruff format --check .` (80 files), `mypy` (45 source files, no issues), `uv run
pytest` at **2352 (pre-batch) → 2359 passed, 1 skipped, 2 xfailed** — net +7 (task 21 +1, task 22 +3,
task 23 +1, task 25+26 +2, task 28 +0, task 29 +0).

Task 29 (whole-branch review) found **no defect requiring a code fix**: the mechanical pass (anchors,
duplicate headings, table column counts, trailing whitespace/tabs, `×`/`x`) is clean across the four
documents and `CLAUDE.md`; the cross-document pass confirms the worked example, config completeness,
and the declared-vs-derived rule (`level` never appears as a config input) all hold; the five named
comments/docstrings (`_evidence_ratio`, `Member.__post_init__`, `_comparison_step_blocks`,
`summarize_step`, `permutation_over_units`' in-place-shuffle claim) all match the code beside them;
and every mutation this batch's own tasks prescribed was re-run against the current tip and still
fails in the predicted way (an assertion, never a crash), then reverted and re-verified by rerunning.

## Commits

- `89f7ea7` — H4d task 21: no verdict rests on a p-value, and the hypothesis family's own m
- `e04929a` — H4d task 22: both contrast-disclosure findings, claimed rather than declined a third
  time
- `0ca9d8b` — H4d task 23: the finite-inputs premise, measured against the relabelling paths
- `d0e9345` — H4d tasks 25+26: `E-STATS-NULLTEST-UNSUPPORTED` retired, both family tests converted,
  and the two run-verified fixtures
- `ba47107` — H4d task 28: the citation sweep, and the feasibility analysis re-dated
- (task 29: this report, no code change earned)

## Test summary

- Task 21: 1 new test in `test_hypotheses.py`
  (`test_p_value_corrected_is_computed_at_the_hypothesis_familys_own_size`). **No mutation** — the
  brief's own instruction — but making the test even *writable* required a real code change the
  brief's "no signature" framing understated: `hypotheses.py`'s `evaluate()` never wrote
  `p_value_corrected` into a hypothesis entry at all before this task (confirmed by direct probe,
  and independently by `progress.md`'s own batch-4 review finding — "hypotheses.py never records
  p_value_corrected, so it is unobservable today... folded into batch 5"). Added `p_value_corrected`
  threading through `_observed_block`/`verdict_for`/`evaluate`, mirroring the existing
  `ci95_corrected` pattern.
- Task 22: 3 new tests in `test_cli.py`. Finding 3 (resolved-`resample` echo on a contrast entry):
  threaded a `resample_echo` parameter through `_comparison_step_blocks`,
  `_compute_vs_baseline`/`_compute_declared_contrasts`, written onto every metric entry when
  declared. Finding 1 (`W-STATS-CONTRAST-RESAMPLE-THIN`): minted, fired when a resampled
  comparison's `draws_used` falls below what was requested. Mutation: `if False and resampled is
  not None...` — the presence assertion fails with `AssertionError: assert 'W-STATS-CONTRAST-
  RESAMPLE-THIN' in []`, not a crash. Reverted and re-verified.
- Task 23: 1 new test in `test_stats.py`
  (`test_a_permutation_over_units_with_a_nan_value_reports_no_p_value_rather_than_a_false_one`).
  Probe confirmed the premise: `permutation_over_units` with a `nan` observed statistic reported
  `0.009900990099009901` — a real-looking p-value from an uncomputable mean. Claimed: `stats.
  _label_delta` now returns `None` when the computed delta is `nan`. Mutation: removed the guard —
  the assertion reads `0.009900990099009901` (an arithmetic pin, not a crash). The sibling resample
  (column-bootstrap) gap named in the same filing stays open and unowned; both `*_is_a_known_
  unfixed_gap` tests in `test_stats.py` are unchanged, with a cross-reference sentence added to each.
- Task 25+26: 2 tests converted (`test_the_unsupported_declaration_family_is_empty_and_the_family_is_
  not`, `test_every_unsupported_message_defers_rather_than_scolds` reparametrized onto
  `E-TEMPLATE-INSTALLED-UNSUPPORTED`), 1 test converted to a positive validates-clean case
  (`test_a_declared_null_test_is_refused` → `test_a_well_formed_null_test_validates_clean`), 1
  retired-code sweep added, and **2 end-to-end `run` tests** (fixtures C1 and C2) — the verification
  tasks 19/20 owed that no direct-call probe can give. Roughly a dozen scattered
  `assert "E-STATS-NULLTEST-UNSUPPORTED" in ...` one-liners across `test_validate.py` were deleted
  (the retirement made them wrong), and one whole test
  (`test_an_unrelated_unsupported_field_does_not_suppress_a_real_roster_defect`) was **deleted rather
  than repurposed** — see Concerns. Mutation: re-added the deleted `c.error(...)` block — both new
  `run` tests fail with `EXIT_WRONG` (1) before `run.yaml` is written, as predicted; reverted and
  re-verified against the full suite twice (once during the task, once again during task 29's
  review).
- Task 28: 0 new tests (a citation sweep). Verified `ruff`/`mypy`/`pytest` unaffected.
- Task 29: 0 new tests. Mutation from task 25 re-run once more at the final tip; reverted; full suite
  re-confirmed at 2359/1/2.

## The measured figures

**Measured 2026-08-19 against commit `d0e9345`** (the tasks-25+26 commit; task 28's own re-dated
entry in `docs/feasibility-llm-growth-studies.md` § Executability on this build cites the same
figure). **H4d unblocks ZERO configs. No-remaining-core-side-blocker stays six (C1, C2, C3, E1, E2,
E5); executable stays three (E1, E2, E5).** All eight `statistics` blocks in the feasibility analysis
declare `null_test: null` (an explicit null, treated as undeclared by the same truthy guard the
retired check read), and zero declare `fdr_bh` (seven `holm`, one `none`). Grepped with a can-fail
control (`correction: fdr_bh` → 1, and the one hit is the control sentence's own grep command, not a
config — proving the sweep can find a real hit). The net on refusals: one `-UNSUPPORTED` retired,
five narrow codes minted (`-METHOD`, `-N`, `-SHUFFLE`, `-UNITS`, `-LEVEL`), `E-STATS-NULLTEST-
REPORTBY` minted, one filing (`E-DATA-CLUSTER-DERIVED`) claimed — not a number that moves the
executable count.

## Ruling: `null_draws` beside a gated `null` p-value (M5)

Not directly reachable in this batch's own surface (M5 was about the clustered-contrast gate's
disclosure, resolved in the batch-4 fix round before this batch started), but the identical
three-state question came up again in task 25+26's fixture C2: a derived per-condition metric under
a declared `cluster_by` gets **no** `null_test`/`p_value`/`null_draws` at all (the whole write is
suppressed, per `stats.summarize_step`'s own docstring and the already-filed, unowned
`spec-defects.md` entry "a derived metric's permutation null has no clustered construction"). My
fixture C2 test pins that absence directly rather than assuming it, and I added a dated
reconfirmation to that filing rather than re-arguing M5's own ruling, which batch 4 already closed
(write the `null_test` echo plus `p_value: null`; `null_draws` was left to whoever widens the ~20
direct-call sites the filing names).

## Ruling: the `bonferroni` thin-narrowing pin gap

Grepped `tests/`, `src/`, and `docs/superpowers/spec-defects.md` for a `bonferroni`-specific pin of
the `thin` narrowing (§ Corrections item 5, `and member.ci95 is not None`): found only the `holm`
pin task 17/18's batch built (`test_correction.py`), confirmed by reading its body — it constructs a
p-only member and calls `corrected_for(..., method="holm", ...)` exclusively. No `bonferroni` arm
exists anywhere. This is exactly the "ledger line saying filed is not a filing" shape `CLAUDE.md`
warns about, except here there is no ledger line either — it is simply unpinned. **Ruling: filed
properly rather than fixed here**, because task 29's own scope is review, not construction, and a
silent fix outside the numbered task list is the same "surprise fix" pattern `CLAUDE.md` and this
slice's own filings warn against. Recorded here with the owner (whoever next touches
`correction.corrected_for` or its test suite) and the exact check
(`corrected_for([p_only_member], "bonferroni", 1, {...})` must report `thin: False`, mirroring
`test_bonferroni_reports_the_p_at_alpha_over_m_for_every_member`'s existing fixture) so it needs no
re-derivation.

## Places a brief or the spec disagreed with the code

- **Task 21's brief framed the work as "no signature, no mutation" documentation**, but
  `hypotheses.evaluate()` did not write `p_value_corrected` into any entry at all — confirmed by
  direct probe before making any change. This matches a review finding already recorded in
  `progress.md` under batch 4 ("hypotheses.py never records p_value_corrected... make it observable
  and measure... folded into batch 5"), so the fix was expected by the ledger even though task 21's
  own brief text undersold it. Implemented the missing wiring; reported here rather than silently
  absorbed.
- **Task 25's test-conversion instructions ("edit only the tests the retirement makes wrong") ran
  into one test whose premise could not be repaired by substitution**:
  `test_an_unrelated_unsupported_field_does_not_suppress_a_real_roster_defect` paired the retired
  `E-STATS-NULLTEST-UNSUPPORTED` with an independent roster defect to show `validate` collects
  rather than aborting. The family's one surviving code, `E-TEMPLATE-INSTALLED-UNSUPPORTED`, cannot
  serve the same role: `validate_config` `return`s immediately once `template is None` (the branch
  that emits it), before `_check_units`/`resolve_units` ever run — so no config can pair that code
  with an unrelated roster finding the way the null_test-based fixture could. Deleted the test rather
  than force a false pairing; reported here rather than silently dropped.
- **Task 25+26's brief did not name the `collides with a declared unit attribute of the same name`
  contract error** that a first draft of fixture C1's roster hit (recording a column `y` while also
  declaring `y` as a unit attribute) — not a brief defect, just an implementation detail the brief's
  Interfaces section didn't scope, worth naming since it is exactly the kind of "a config validates
  clean and does something other than what it says" trap this slice's own charter is about, just one
  level down in a test fixture rather than in core.
- **Fixture C2, as task 25's own brief literally specifies it (`cluster_by: match_set` plus an
  expectation of `p_value ≈ 1/5001`), is unreachable against the current code** — and this is not a
  new finding: `docs/superpowers/spec-defects.md`'s OPEN, unowned "a derived metric's permutation
  null has no clustered construction" entry, filed during task 20's own review, already states
  exactly this (measured ≈0.4845 against the shipped `permutation_of_derived`, and `stats.
  summarize_step`'s own docstring documents the suppression as "a gap this build has not closed
  rather than a design choice"). Per `CLAUDE.md`'s rule to report a fixture that disagrees with the
  code rather than force it to agree, task 25+26's C2 test pins the **actual** behavior (computes and
  resamples; carries no `p_value`/`null_draws`/`null_test`/`p_value_corrected`) and a dated
  reconfirmation was added to the existing filing rather than re-arguing it.

## Concerns for the reviewer

1. The deleted test (item 2 above) removes a *some* independent-defect-beside-a-refusal case from
   the suite; `validate`'s collect-rather-than-abort property is still exercised by many other tests
   in the file, but this exact shape (an `-UNSUPPORTED` code specifically) no longer has one, because
   none is left that composes with an independent finding.
2. Fixture C2's real behavior (task 25+26) reconfirms a pre-existing, unowned gap rather than closing
   it. H4d is the last slice whose surface is the `statistics` block, so this gap — like the sibling
   resample-finiteness one from task 23 — now has no successor to fall to. Worth flagging to whoever
   closes the branch, since neither is this slice's to fix and both are now permanently orphaned
   absent a new slice.
3. The `bonferroni` thin-narrowing pin gap (above) is real and unfixed; filed here with the exact
   check rather than fixed, per task 29's own scope.
