# Batch 5 review — task 11 (`W-PARAM-UNSET` at `validate`, and the shared helper)

**Verdict: PASS.**

Commit reviewed: `c4dea36`. Baseline 2953/1/2 → full suite re-run **2955 passed, 1 skipped, 2
xfailed** (behaviour: `uv run pytest -q`), matching the report and the claimed +2.

## Findings

**Minor — the report overclaims exclusivity for mutation 12.** The report says mutation 12
("delete `W-TEMPLATE-VERSION`'s unset clause after extraction") is "caught by arm F alone,
exactly as specified." Re-run (behaviour): with `detail = ""` hardcoded, **two** tests fail, not
one — `test_h6a_arm_f_the_template_version_warning_message_is_pinned_whole` **and** the
pre-existing `test_a_moved_template_version_names_a_parameter_the_config_leaves_unset` (its
`assert "analysis.confidence" in warnings[0].message` also depends on the clause). The brief
itself only said "caught by arm F," never "alone" — the word was the report's own addition and
is the kind of specific-but-unchecked claim this repo's own ledger flags repeatedly. Harmless to
the pin (arm F still does the job; the report's overclaim doesn't affect what shipped), so Minor
rather than Major.

No other finding. Everything else checked below is CONFIRMED by behaviour.

## What was verified by behaviour (re-run, not read)

- **Blast radius, remeasured myself.** `grep -rn '✓' tests/*.py` → **0** hits (design's "5" is
  wrong). `grep -rn "problems (" tests/*.py` → **4** hits, **3** of them assertions (all in
  `tests/test_diagnostics.py`) — matches § Corrections 7's "zero, three not four," not the
  design's "5+4." The report's own numbers agree with what I measured independently.
- **Instrumented pre-existing firing count.** Patched `Collector.warn` and ran
  `tests/test_validate.py`, `tests/test_templates.py`, `tests/test_materialize.py`,
  `tests/test_diagnostics.py`: **9** tests fire `W-PARAM-UNSET`, one of which is this task's own
  new Fixture K positive test → **8 pre-existing**, not the design's "7." Matches the report
  exactly. This confirms the report's disagreement with the design is real, not carried.
- **Both call sites call the one shared helper.** `grep -n "_unset_defaulted_paths(" validate.py`
  → definition at 1067, calls at 1105 (`_check_parameters`) and 1147 (`_check_versions`). Mutated
  the helper's body to `return []`: **both** readers' tests failed —
  `test_h6a_fixture_k_an_unset_defaulted_parameter_draws_w_param_unset` (the `_check_parameters`
  reader) and `test_a_moved_template_version_names_a_parameter_the_config_leaves_unset` /
  `test_h6a_arm_f_...` (the `_check_versions` reader). Reverted; diff against backup
  byte-identical; targeted tests re-pass.
- **No monkeypatch aimed at what moved.** `grep -rn "monkeypatch.*_check_versions\|_check_parameters\|_unset_defaulted"
  tests/*.py` → no hits.
- **Both directions of the warning, different tests failing.** Mutation 10 (delete the call
  site): Fixture K's positive test fails (`0 == 1`), control arm untouched. Mutation 11 (invert
  the condition to fire when set): **4** failures — both Fixture K arms, arm F, and
  `test_a_moved_template_version_names_a_parameter_the_config_leaves_unset` — matching the
  report's own count exactly. Reverted; diff byte-identical.
- **Mutation 13** (an inlined copy at one call site instead of the shared helper) is, as the
  brief itself states, undetectable by any fixture and is explicitly framed as a reading
  obligation rather than a mutation to run. The grep above discharges it: reading confirms both
  call sites reach the one definition. Judged: reading does discharge this one, because the brief
  pre-declared it blind and named the reading as the intended replacement — this is not the
  "reading obligation" shortcut the repo's ledger warns about elsewhere (that pattern is about
  skipping a mutation that *could* discriminate; here none can).
- **`W-TEMPLATE-VERSION`'s clause survives, unedited.** `git show c4dea36` diff shows the
  `c.warn(...)` call for `W-TEMPLATE-VERSION` unchanged; only the docstring above it and the
  `unset` computation (now via the shared helper) changed. Guard-pin arm F
  (`test_h6a_arm_f_the_template_version_warning_message_is_pinned_whole`) passes unedited before
  and after, and mutation 12 (above) proves it can still fail.
- **The false docstring clause was deleted, not merely softened past falseness, and the test's
  name is untouched.** Old: "...so a defaulted parameter it omits is not reported." New: "...
  draws no `W-TEMPLATE-VERSION` warning at all." The rewrite is more than a bare deletion — it
  also names which warning is meant — but this is necessary, not cosmetic: the test's own config
  (`template_version` unchanged, `analysis.confidence` deleted) now *does* draw `W-PARAM-UNSET`
  under this build, so an unqualified "draws no warning at all" would itself have been false.
  Confirmed the test's assertion (`"W-TEMPLATE-VERSION" not in codes(path)`) and name are
  unchanged — `git show c4dea36` diff.
- **Fixture K's control arm is not vacuous.** Mutation 11 (fire unconditionally of what's unset)
  fails the control arm specifically — different assertion, different test, from mutation 10's
  failure. Both arms filter `c.findings` by `code == "W-PARAM-UNSET"` before checking anything
  else, so no neighbouring diagnostic (`analysis.drop_missing` appears in many unrelated
  sweep/ablation fixtures in this file) can satisfy the assertions by accident — confirmed
  directly: mutation 10 makes the filtered list empty rather than non-empty-but-wrong.
- **§ Warnings row respects the table's own scope sentence.** The scope sentence ("Some fire at
  `validate` time... others at `run` time — the table names which") is honoured: the new row
  opens "Checked at `validate`, from the declaration alone" rather than relying on the design's
  instruction alone — this is the exact check batch 4's finding turned on.
- **§ Validation row and § Warnings row anchors resolve.** `#the-importable-surface`,
  `#warnings-core-reports`, `#errors-core-raises`, `#there-is-no-separate-defaults-file`,
  `design-principles.md#greenfield-only` all match real headings. `E-STEP-PARAM-UNKNOWN` is
  listed under "### Errors core raises" (line 1092/1130), which is the section the new row's
  link points to — correct, not the sibling "### Errors `validate` reports" section.
  Two-column table rows match their headers; no trailing whitespace introduced (`git show` diff
  checked with `grep -P ' $'`).
- **Core-schema deferral is disclosed where task 12 will see it.** The report says the filing
  "stays filed (task 12's, not touched here)" rather than claiming a filing that doesn't exist.
  Checked `docs/superpowers/spec-defects.md` — no `W-PARAM-UNSET`/core-schema entry exists yet,
  consistent with the report's own statement that it did not file. Task 12's own brief text (plan
  step 5, "file the new gap... Owner: unassigned, with the reason... A ledger line saying 'filed'
  is not a filing: write the entry") already carries this obligation independent of task 11's
  report — the deferral is not resting on the report alone.
- **Guard-pin arms A, C, D, N — no authorized editor, none moved.** `git show c4dea36 --stat`
  touches only `validate.py`, `docs/reference.md`, `tests/test_validate.py`, and the batch-5
  report — none of `test_cli.py` (arms A, C), `test_hashes.py` (arm D), or `test_diff.py` (arm N).
  Re-ran all five arm tests: pass unedited. Re-ran batch 1's fold-separator mutation to
  `hashes.code_hash_of` (`\0` → `|`): arms A, C, D all fail as expected; reverted (diff
  byte-identical), re-ran, pass.
- **Gates.** `ruff check .` — all checks passed. `ruff format --check .` — 93 files already
  formatted. `mypy` — no issues, 52 source files. `pytest -q` — 2955 passed, 1 skipped, 2
  xfailed.
- **Undisclosed drops.** Brief's file list (`validate.py`, `reference.md`, `test_validate.py`)
  matches exactly what shipped. Nothing outside that scope touched (`hashes.py`,
  `_check_versions`' message, `E-PARAM-MISSING`'s condition, `CLAUDE.md` all untouched — checked
  by diff and by the arm-F/arm-N-etc. re-runs above).

## What was verified by reading only

- The design's and correction's own prior numbers (5+4, "7") — read from the spec/plan text,
  then independently re-measured rather than trusted (see blast-radius bullet above).
- The report's prose claims about which lines it changed — cross-checked against `git show
  c4dea36`'s actual diff rather than accepted as stated.

## Reconciliation

Baseline 2953/1/2 (task 10) + 2 new Fixture K tests = 2955/1/2, exactly what both the commit
message and my own from-scratch full-suite run show. No unexplained delta.
