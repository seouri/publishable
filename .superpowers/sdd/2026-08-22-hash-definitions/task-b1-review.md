# Batch 1 review — tasks 1, 2, 7, 10

**Verdicts: task 1 PASS · task 2 PASS · task 7 PASS · task 10 PASS.**

All four commits reviewed against their briefs, the twelve plan corrections, the four appended
controller rulings (F–I), and `design-principles.md`/`reference.md`. Full suite (`uv run pytest`, run
directly in the foreground twice, `pytest-of-joon` and `__pycache__` cleared first): **2939 passed, 1
skipped, 2 xfailed** — exactly the claimed `+8` over the `main` baseline of 2931. `ruff check .`, `ruff
format --check .` and `mypy` all clean.

## What was verified by behaviour (not by reading)

- **Every guard-pin literal was independently recomputed**, not merely compared to the commit's own
  claim. Built the base tree (`src/pkg/step.py` = `a = 1\n`, `templates/t.py` = `b = 2\n`, committed) in
  a throwaway repo and called the shipped `code_hash` directly: got `sha256:71bf339c…` (arm A) and, after
  adding an untracked `src/pkg/.env`, `sha256:ebc5ee53…` (arm B) — both match the pinned literals exactly.
  Built Fixture D's tree (tracked `.pyd` = `X`) and got `sha256:eec1541e…`, matching arm D and confirming
  the plan's `6ddb8634…` is correctly abandoned. Confirmed `sha256:e3b0c442…` is `sha256("")`.
- **Every no-editor arm (A, C, D) was proven to fail on a real production mutation and restored by
  editing back, then re-run green.** Doubled the trailing separator in `hashes.code_hash`'s fold
  (`outer.update(b"\n")` → `b"\n\n"`): arms A, B, C and D all failed with the expected digest mismatch;
  arm E (empty-tree case) was correctly unaffected. Restored `hashes.py` from a saved copy, confirmed
  `git diff` empty, and re-ran the five `h6a_arm` tests in `test_hashes.py`/`test_cli.py` green.
- **Arm N and its control were independently mutated against `diff.py`'s `_render_row`.** Inverting
  `figure_a == figure_b` → `!=` failed **both** arm N tests, as claimed. Forcing the branch to `if True:`
  failed the `DIFFERS` test and **passed** the control — the exact asymmetry the fix-round commit
  (`419ca29`) states. Restored `diff.py` from a saved copy; both tests green again.
- **The deleted-sentence sweep was reproduced independently**, newline-insensitive, over the named files
  (four documents, `CLAUDE.md`, the feasibility analysis, `spec-defects.md`, `src/**`, `tests/**`).
  Confirmed the only remaining verbatim hits for `"normalized to what"` / `"would have materialized"` /
  `"an omitted \`cluster_by\`"` are inside `docs/superpowers/spec-defects.md`'s existing (task‑12‑owned)
  entry — none in `reference.md`, `hashes.py`, or anywhere else. Proved the sweep itself can fail by
  running it against a string known present (`"Does not normalize"` in `hashes.py`, found).
- **Anchors task 7 added were resolved against the real heading slugs** (`reuse_from-addresses-…`,
  `the-two-files`, `building-one`, `` manifest/input.json ``'s slug, `the-apparatus-core-can-only-observe`,
  `what-auto-derives-from`, `operation-commands`, `scaffolding-publishable-new`, etc.) — all resolve.
- **`W-STUDY-CODE-HASH-MISMATCH` and `W-TEMPLATE-VERSION` emit sites re-grepped**: one site each
  (`report.py`, `validate.py`), matching the report's claim. `W-TEMPLATE-VERSION`'s message in
  `validate.py` (line 1126–1130) matches arm F's pinned literal character for character.
- **`run.yaml` key-list "not duplicated" claim re-grepped**: `test_h8a_arm_a_…` and
  `test_h8a_arm_b_…` exist in `tests/test_cli.py` exactly as cited.

## Ruling F — correctly implemented despite the stale brief

Task 1's own extracted brief carries a table row and a step-3 paragraph written **before** Ruling F was
appended, and that table (listing `core.excludesFile` as a fourth "no, excluded" case) directly
contradicts Ruling F's mandate to neutralize global/system config and disclose only `.git/info/exclude`
as the residue. **The shipped commit (`c863e3e`) correctly followed the ruling, not the stale brief
table** — its own commit message says so explicitly, and the merged table and prose in `reference.md`
(§ How the three are computed) match Ruling F's neutralized-command framing exactly: the fourth table row
reads "excluded by one of the repo's own committed rules … or by `.git/info/exclude`" — `core.excludesFile`
is gone from the "no" case and is instead the disclosed one residue. This is exactly the failure mode
CLAUDE.md's "a ruling that overrules a brief has to reach the brief" flags, and here it *did* reach the
implementer despite the brief's staleness — worth recording as the good case, not a defect.

No `check-ignore` invocation exists anywhere in `src/`, `tests/`, or `docs/reference.md` yet — correct,
since that wiring is task 3/5's, not this batch's. Checklist item 3 (every `check-ignore` call uses the
neutralized form) is therefore not yet applicable to this batch's diff.

## Findings

**No Critical or Major findings.**

- **Minor.** The report's own "Concerns for the controller" section hands `hashes.py`'s `code_hash`
  docstring ("Read from the working tree, not from git") to **"task 3 or task 5"** — a disjunctive owner,
  which is the exact anti-pattern CLAUDE.md names ("An owner that is a disjunction is not an owner").
  The plan's own task 3 section shows task 3 only changes `code_hash`'s **signature** (adding `include`);
  it is task 5 that wires the real git-exclude predicate, which is what actually falsifies "not from
  git." The single accurate owner is task 5; naming both defers the decision rather than making it.
  Low severity — the docstring is not yet load-bearing and the gap is disclosed, just imprecisely routed.
- **Minor.** Arm C's docstring names "Fixture M" as what will cover the upstream `code_hash`/
  `parameters_hash` pair — consistent with the design's own Fixture M vocabulary (§ design line 745) — but
  two *unrelated* fixtures already named "Fixture M" exist in this same test suite from prior slices
  (H8b's metadata-vs-limits pin in `test_hashes.py`/`test_diff.py`). Not a defect in this batch (task 2
  didn't build anything under that name), but a name collision a later task should not compound.

## Per-task detail

- **Task 1 (`c863e3e`).** Four-case table added once in § How the three are computed; every other site
  (§ Three hashes' `code_hash` row, § Templates, `W-STUDY-CODE-HASH-MISMATCH` row) links rather than
  restates. § Templates' two clauses split correctly: the fixed-skip-set sentence stays true and gains a
  link; the ignore-file sentence narrows to the dirty gate and states the "other three cases" pointer
  precisely. The "goes dirty at `validate`" clause is untouched, correctly deferred to H6b task 18.
  Mechanical pass (anchors, table column counts, no en dash) checked and clean.
- **Task 2 (`ad59bdd`).** Six-arm pin (A–F) captured, all seven literals recomputed independently above
  and matched. The plan's one-tree design for arms A/B is correctly identified as unrunnable
  (`E-TEMPLATE-LOAD`) and reshaped into a two-tree construction per arm, with the extra pair of moving
  literals for arm B's `run_id` half stated in the docstring in advance for task 5. Arm C deliberately
  omits the three figures that would be absences on this project (apparatus, upstream copies, derived
  seeds), stated rather than silently dropped. Grep evidence for "no existing test asserts X" claims is
  concrete (exact grep commands, not counts).
- **Task 7 (`76efc72`).** Ruling C written: the five carrier fields enumerated with locations, the
  consequence stated plainly (`diff` prints `DIFFERS` for identical code across the boundary,
  `W-STUDY-CODE-HASH-MISMATCH` still names three causes), and the sharpest cost (one record, two hash
  definitions, unmarked) stated rather than mitigated. Fixture N built by copying a real run rather than
  hand-writing records, per the brief; the can-fail control was found broken by this batch's own review
  and fixed in `419ca29` (see below) rather than shipped broken.
- **Task 10 (`13ae83c`).** Both the normalization sentence and its false `diff`-justification are
  deleted outright, not softened or rewritten elsewhere. `covered_config`'s docstring stops quoting the
  deleted sentence and no longer points at a filing task 12 will strike; it states the ruling and its
  three grounds instead. `parameters_hash`'s body and `covered_config`'s body are byte-identical to
  before (confirmed by reading the diff — no code line touched beyond the docstring). Sweep reproduced
  independently and found the identical single remaining home (`spec-defects.md`, task 12's).

## The in-batch fix round (`419ca29`)

Both findings this batch's own review raised were closed correctly, not merely papered over:

1. Arm N's control originally named itself `..._print_identical` while its first assertion block
   asserted `DIFFERS` against a genuinely differing pair, plus a construction-satisfied `assert same_a
   == same_b`. The offending block was **deleted**, not patched, and the control now asserts the
   single property its name claims. Independently re-mutated above; behaves as the new docstring states.
2. Arm C's `_H6A_RUN_WITH_ENV_DIGEST` reference to arm B's constant is now stated explicitly, so a
   reviewer sees why a "no-editor" arm's asserted value is allowed to move when task 5 lands.

## Suite and gates

- `uv run pytest`, foreground, twice (once via an auto-backgrounded long-running command whose
  completion was awaited via notification, once via `ruff`/`mypy` runs which stayed under the
  foreground timeout): **2939 passed, 1 skipped, 2 xfailed**, matching the report's claimed progression
  (2931 → 2937 after task 2 → 2939 after task 7, unchanged by tasks 1 and 10).
- `uv run ruff check .` → all checks passed.
- `uv run ruff format --check .` → 93 files already formatted.
- `uv run mypy` → Success: no issues found in 52 source files.

All mutations were reverted by editing the file back from a saved copy (never `git checkout`), and each
revert was verified by re-running the affected tests green, per the repo's own verification rule.
