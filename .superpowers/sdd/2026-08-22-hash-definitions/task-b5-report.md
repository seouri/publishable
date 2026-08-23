# Task 11 report — `W-PARAM-UNSET` at `validate`, and the shared helper

**Status: PASS.**

## What was built

`src/publishable/validate.py`: extracted `_unset_defaulted_paths(doc, template)` out of
`_check_versions`' existing comprehension. Both `_check_versions` (named only inside
`W-TEMPLATE-VERSION`'s message, gated on a version mismatch) and the new
`_check_parameters` call (named unconditionally) now call the one helper. `_check_parameters`
reports `W-PARAM-UNSET` — a warning, path `parameters`, one diagnostic enumerating every
`parameter_spec` path this config leaves to the template's default, stating the consequence
(`cfg.parameters.<path>` raises `E-STEP-PARAM-UNKNOWN`). Covers the `parameters` block only;
the core-schema half stays filed (task 12's, not touched here).

`_check_versions`' docstring was corrected in the same edit: its old claim that the unset list
is "named only inside this warning" became false the moment `_check_parameters` started naming
it unconditionally too, so the docstring now says the duplication with `W-PARAM-UNSET` on a
version-mismatched config is deliberate.

`docs/reference.md`: one § Validation row ("Defaulted parameter left unset") and one §
Warnings row (`W-PARAM-UNSET`, alphabetically between `W-HYPOTHESIS-INFERENCE-BASE` and
`W-REPL-DETERMINISTIC`), the latter stating the condition, the one emit site, the
unconditional-not-version-gated firing, and the core-schema boundary with its filed-not-built
reason. `W-TEMPLATE-VERSION`'s row is untouched (Decision 11).

`tests/test_validate.py`: Fixture K, two tests, added immediately after
`test_an_unset_parameter_is_named_only_when_the_version_moved` — a positive arm (omit
`analysis.confidence` and `analysis.drop_missing`, assert exactly one `W-PARAM-UNSET` at path
`parameters` naming both, `exit_code() == 0`, `has_errors is False`) and a control arm (every
default set — `write_config()`'s own base shape — draws none). Also deleted the now-false
clause from `test_an_unset_parameter_is_named_only_when_the_version_moved`'s docstring ("so a
defaulted parameter it omits is not reported"), keeping the test's name and its
`W-TEMPLATE-VERSION`-only assertion untouched. This edit is outside guard-pin arm F, whose
claim is about the *message*, not this docstring.

## Blast radius — measured, not carried

Full suite: **2955 passed, 1 skipped, 2 xfailed**, up from the stated baseline of 2953/1/2 —
exactly the delta of my two new tests, zero failures, zero tests needed updating or loosening.

Re-ran § Corrections 7's own two greps rather than carrying its numbers: `grep -rn '✓'
tests/*.py` → **0 hits**, confirming no test asserts the `✓ config valid` string. `grep -rn
"problems (" tests/*.py` → 4 hits, 3 of them assertions (all in `tests/test_diagnostics.py`,
over configs that never reach `_check_parameters`) — matching Correction 7's own re-measurement,
not the design's original "5 + 4."

Re-ran the instrumented-subset measurement myself rather than carrying either the design's "7"
or the plan's stated shape. Patching `Collector.warn` to record the firing test's nodeid and
running `tests/test_validate.py`, `tests/test_templates.py`, `tests/test_materialize.py`,
`tests/test_diagnostics.py`: **9 tests fire `W-PARAM-UNSET`**, all passing. One of the 9 is this
task's own new Fixture K positive test. Re-running the identical instrumentation with
`tests/test_validate.py` reverted to its pre-task-11 state (validate.py changed, test file
stashed) isolates the **pre-existing** count: **8**, not the design's claimed 7 — a genuine,
measured disagreement with the design's number, distinct from Correction 7's own already-caught
disagreement with the plan's original "5+4." All 8 pass unmodified; none needed a loosened or
updated assertion, since the warning is additive to `c.findings` and none of the 8 asserts an
exhaustive finding set that the new warning would break.

## Mutations

Working copy backed up (`/tmp/validate.py.bak`) before each; each reverted by editing back,
`__pycache__` cleared, revert verified by re-running the targeted tests plus a `diff` against
the backup showing byte-identical.

- **Mutation 10 — delete the `W-PARAM-UNSET` call site.** Checked first: `analysis.drop_missing`
  appears in many unrelated sweep/ablation tests in this file, but Fixture K's assertions filter
  `c.findings` to `code == "W-PARAM-UNSET"` before checking the message, so no other diagnostic's
  text could satisfy them. Caught: Fixture K's positive arm fails (`0 == 1`).
- **Mutation 11 — invert the condition (fire for parameters that ARE set).** Caught: 4 failures —
  both Fixture K arms, arm F, and the pre-existing
  `test_a_moved_template_version_names_a_parameter_the_config_leaves_unset` (message now lists
  the three *other* parameters instead of the one omitted one).
- **Mutation 12 — delete `W-TEMPLATE-VERSION`'s unset clause after extraction (`detail = ""`
  unconditionally).** Caught by arm F alone, exactly as specified: the full-message assertion
  fails because the clause (a substring of the pinned message) is gone.
- **Mutation 13 — named blind in advance, no test asserts against it.** Inlining the helper's
  body at one of its two call sites is undetectable by any fixture, since two identical
  comprehensions produce identical results. Discharged as the stated reading obligation: `grep
  -n "_unset_defaulted_paths(" src/publishable/validate.py` shows exactly three lines — the
  definition (1067) and one call site inside each of `_check_parameters` (1105) and
  `_check_versions` (1147). Both call sites call the shared helper; neither carries an inlined
  copy.

## End-to-end, through the installed console script

Built a real git repo outside the publishable repo (input/output dirs outside it too, to avoid
tripping the unrelated `E-DATA-IN-REPO` invariant) with a `cohort-pilot` config against
`generic`, and ran `uv run --project /Users/joon/src/tries/publishable publishable validate
<path>` — the real entry point, not `main()` called in-process.

- Config omitting `analysis.min_samples`, `analysis.confidence`, `analysis.drop_missing`:
  printed `warning W-PARAM-UNSET parameters` naming all three, `1 problem (0 errors, 1
  warning)`, **exit 0**.
- Same config with all four parameters set: `✓ config valid`, exit 0, no warning.

Both directions confirmed live, not just through direct `_check_parameters` calls.

## § Warnings row and § Validation row

New `W-PARAM-UNSET` row states the condition (unconditional, validate-time, one diagnostic per
config naming every unset-and-defaulted path), names its one emit site
(`_check_parameters`, confirmed by `grep -rn "W-PARAM-UNSET" src/publishable/*.py` → the
docstring mentions plus the one `c.warn(` call), and states the core-schema boundary with its
filed-not-built reason so the row does not overclaim. Checked the table's own scope sentence
("Some fire at `validate` time... others at `run` time — the table names which") before writing
the row and stated `validate` explicitly, matching sibling rows' style — this is the check
batch 4's finding turned on a row that had skipped it. `W-TEMPLATE-VERSION`'s row: unchanged
(confirmed by diff — zero characters touched). `E-STEP-PARAM-UNKNOWN`'s row: unchanged, still
true (a `cfg` path the config doesn't hold).

## Grepped, not carried

- `grep -rn "W-PARAM-UNSET" src/ tests/ docs/*.md README.md` → **4 hits in `src/publishable/validate.py`
  (1 definition comment reference, 1 emit site, 2 docstring mentions), 5 hits in
  `tests/test_validate.py`, 1 hit in `docs/reference.md`** (all listed above under "What was
  built" and "§ Warnings row"). Zero before this task, per the plan's own grep.
- Control `grep -rn "E-CODE-DIRTY" src/ tests/ docs/*.md README.md` → **3** (`src/publishable/cli.py`,
  `tests/test_acceptance.py`, `docs/reference.md`), matching the plan's stated control.
- `grep -rn "_unset_defaulted_paths(" src/publishable/validate.py` → 1 definition, 2 call sites —
  the mutation-13 reading obligation.

## Guard pin

Arm F (`test_h6a_arm_f_the_template_version_warning_message_is_pinned_whole`) passes unedited —
confirmed by running it standalone before and after the real change, and it is what caught
mutation 12. No other guard-pin arm touched. No arm needed to move.

## Gates

`uv run ruff check .` — all checks passed. `uv run ruff format --check .` — 93 files already
formatted. `uv run mypy` — no issues, 52 source files. `uv run pytest -q` — **2955 passed, 1
skipped, 2 xfailed** (baseline 2953/1/2 plus this task's +2 tests).

Restored `.superpowers/sdd/.gitignore` before committing — `task-brief` had clobbered it to a
bare `*` prior to this session starting (confirmed via `git diff` showing the full documented
content replaced), unrelated to this task's own edits.

## Concerns for the controller

- The pre-existing instrumented-firing count is **8**, not the design's stated **7** — worth
  carrying forward accurately rather than repeating either number, on this slice's own stated
  discipline about not carrying a summary phrase forward unmeasured.
- Everything else matches the brief and Decisions 10/11 as read.
