# Review — tasks 18 and 19 (H4a, `h4a-resample-honoured`, `c4b82e1..b1b588b`)

**Spec compliance: ✅**
**Task quality: findings** (2 Important + 3 Important on the ruling side, 1 Minor; nothing Critical)

Tree verified at `b1b588b`: `uv run pytest` **1800 passed + 2 xfailed**, `ruff check .` clean, `mypy`
clean, `git status --short` shows only the reviewer's own `progress.md`. All mutations below were
applied where the behaviour lives, `__pycache__` cleared between runs, reverted **by editing in
place**, and each revert verified by re-running the test rather than by `git status` alone.

## What was verified true

- **Both brief mutations reproduce.** Removing `- {"by"}` from `_comparison_step_blocks`' metric loop
  (`src/publishable/cli.py:772`) fails `test_a_report_by_level_resamples_without_joining_the_correction_family`;
  adding `"basis": "units"` to the `Estimate` dict in `run_record.summary_values` fails
  `test_a_summary_estimate_is_not_recomputed_by_the_resample_pass` on its exact-equality assertion.
  Neither pin is decoration.
- **The reported brief defect is real, on all three counts.** `cli.command_run`'s level call
  (`src/publishable/cli.py:2243`) passes `strata` and *not* `resample_columns` — confirmed live: under
  `resample: {method: bootstrap, n: 500}` a level's `pred` comes back `method: t_over_units`,
  `resample_draws: null`, while the parent's `pred` is `percentile_over_units`. It **is** filed:
  `docs/superpowers/spec-defects.md` § "`percentile_of_derived` reported a zero-width interval…",
  **Finding 2**, dated 2026-08-15, owner H4 Statistics, describing exactly this call site. The brief's
  expectation was wrong and the implementer was right to route around it.
- **Task 19 ground 2's quotation is verbatim** (`docs/reference.md`, § The one config file), and the
  fenced schema really does carry `resample: null  # bootstrap` with its full shape in the comment.
- **Only one of task 1's two pins fails under the `materialize.py` mutation — and that is not a
  weakness.** Reproduced: `test_the_undeclared_resample_shape_is_pinned_absent_key` fails,
  `..._explicit_null` passes. The explicit-null pin's subject is the *hand-written* document; its own
  docstring states that `run_a_project` merges by top-level `doc.update`, so its insensitivity to
  `materialize.py` is by design, not by accident. The brief's Step 5 was overstated; **no task-1 pin is
  weaker than the slice assumed.** (Detail the report got right in mechanism: the absent-key pin dies
  at its `"resample" not in run["config"]["statistics"]` line, before `_assert_undeclared_resample_shape`
  is reached — the shape assertions are not the detector.)
- **No parser-normalisation exposure.** Task 17's raw-text `&id`/`*id` pins already cover the
  `report_by` level path (`tests/test_cli.py`, `test_the_resolved_resample_survives_report_by_without_aliasing`),
  so the new tests owe none.
- **`ruff format --check` 62 files is pre-existing** — `tests/test_cli.py` is already unformatted at
  `c4b82e1`. (The review request's "~39" is the stale number; the report's 62 is correct.)

## Findings

### Important 1 — three of task 18's absence assertions have no failing mutation, and the docstring names a detector that does not detect
`test_a_report_by_level_resamples_without_joining_the_correction_family` asserts `family`,
`family_size` and `correction` are absent from each level block. The only mutation applied kills a
*different* line. Under `- {"by"}` removed, the family assertion **still passed**: the entry came back
`{"comparisons": 1, "metrics": 2}` and the test failed three lines later on `"by" not in step_block`.
So the docstring's "`family` is asserted to the exact shape a strata-free run would have, so a level
joining the family shows up as an inflated metric count rather than as a silence" is not true of any
mutation demonstrated here — a `by` block enters the contrast without changing the family count at
all. The implementer observed this in the report (§ Mutations, item 1) and did not propagate it into
the docstring it falsifies. Standing class: a comment claiming a guarantee the code does not provide.

### Important 2 — task 18's second test swapped its companion to a weaker one, undisclosed, and mislabelled it
The brief's `test_a_summary_estimate_is_not_recomputed_by_the_resample_pass` companion asserted on the
recorded column `pred`. Shipped, it asserts on `mean_pred` (with `aggregate_returns="mean_pred"` added,
which the brief did not have) under the comment *"Positive companion: a column in the same run IS
resampled."* `mean_pred` is a **derived metric**, not a column. Verified in that exact fixture: with the
`resample` block removed, `pred` is `t_over_units` and `mean_pred` is still `percentile_over_units`
with `resample_draws: 2000`. So `assert aggregated["mean_pred"]["method"] == "percentile_over_units"`
is declaration-insensitive decoration; only `["resample"]["n"] == 2000` saves the companion from
vacuity. The correct, declaration-sensitive companion (`pred`) was available and working in the same
run. The report discloses the *property-1* companion rewrite and is silent on this one.

### Important 3 — a level's recorded column now records a resample block beside an interval that resample did not build, and that increment is not on record
Verified live under `report_by: [cohort]` + `resample: {n: 500}`: a level's `pred` carries
`resample: {method: bootstrap, n: 500, stratify_by: []}` and `resample_draws: null` beside
`method: t_over_units`. Finding 2's deferral rests in part on "`run.yaml` already discloses the
difference, it just doesn't explain it" — written at task 15, **before task 17 landed the
beside-recording**. The record now states resolved resample parameters next to an interval built
without them, which is more than an unexplained asymmetry. Task 18 confirmed this code path live and
filed nothing; Finding 2 should be amended with the task-17 increment.

### Important 4 — task 19's ground 2 claims an inheritance the cited sentence does not extend
`reference.md` § The one config file reads: "For `contrasts` and `report_by`, declaring one by hand is
how a run asks for it, and `validate` accepts the key whether or not `init` wrote it" — enumerated for
two named blocks. `resample` is now a **built** feature whose key `init` does not write, which is
precisely the condition the same spec-defects entry's 2026-08-11 amendment calls "a real gap, not a
slice boundary", and which task 16 fixed by editing `reference.md`. The ruling's "`resample` and
`null_test` inherit that sentence rather than needing their own" is asserted, not argued, and the "no
`reference.md` change" half of the conclusion is under-argued as a result. The decision itself — don't
materialize — is unaffected and stands on grounds 1 and 3.

### Important 5 — the entry task 19 closed still contradicts itself two paragraphs above the ruling
`docs/superpowers/spec-defects.md` still reads: "`resample` and `null_test` are still refused outright
(`E-STATS-RESAMPLE-UNSUPPORTED`, `E-STATS-NULLTEST-UNSUPPORTED`) and remain a boundary."
`E-STATS-RESAMPLE-UNSUPPORTED` was retired by this slice's task 12 — `grep -rn` finds it nowhere in
`src/` or `docs/reference.md`, only in `tests/test_validate.py`'s absence pin. A reader arriving after
the merge reads a live refusal claim, then a ruling premised on that refusal being gone. Task 19 edited
this entry and swept only the paragraph it was pointed at.

### Minor 6 — ground 1 proves too much
"`parameter_spec` is the single source of truth for what `init` writes, and none of these is a
parameter" would equally forbid `statistics.correction`, which `init` does write and which is not a
`parameter` either — as the ground's own next sentence states. The conclusion survives on grounds 2
and 3; ground 1 as written does not carry weight.

## Verdicts

- **Spec compliance: ✅** — no invariant broken. Task 18 adds tests only; task 19 changes one
  gitignored-tree document and leaves `materialize.py` and the four documents untouched, consistent
  with `parameter_spec` as the single source of truth for `init`'s output and with the schema-wider-
  than-`init` sentence in `reference.md`.
- **Task quality: findings** — five Important, one Minor. The two pins are real and both mutate to
  failure; the ruling is argued rather than asserted (ground 3 is the empirical one, and it
  reproduces) and a reader six months out can act on it. What is owed: a docstring that names the
  detector the mutation actually hit (1), the companion put back on `pred` (2), Finding 2 amended for
  the task-17 increment (3), an argued or executed answer for `resample` in `reference.md`'s
  enumeration (4), and the stale `-UNSUPPORTED` sentence in the entry just closed (5).
