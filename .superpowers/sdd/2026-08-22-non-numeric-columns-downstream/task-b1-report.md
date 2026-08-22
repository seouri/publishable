# Batch 1 report — H5b tasks 1, 2, 3

**Status: complete.** All three tasks done, in order, each committed separately. All gates clean
after each task: `uv run ruff check .` (clean), `uv run ruff format --check .` (93 files, unchanged),
`uv run mypy` (52 source files, unchanged), `uv run pytest` (task 1: 2895 passed / 1 skipped / 2
xfailed — 2891 + 4 new; tasks 2 and 3: same, no delta, as their briefs state).

**Commits:**
- `23b79a9` — H5b task 1 (the guard pin)
- `bc4e56e` — H5b task 2 (§ Templates)
- `2e9f5e4` — H5b task 3 (§ The per-unit tables, § Statistical reporting, `W-STATS-REPEATS-DISAGREE`,
  spec-defects filing)

**HEAD relative to `ee8085e`** (every task-1 literal is dated to this commit): confirmed
`ee8085e` is an ancestor of the branch point, and `git diff ee8085e HEAD -- src/ tests/` was empty
before task 1 started — no `src/`/`tests/` code moved between the measurement commit and this work,
so every literal below was expected to reproduce exactly, and did.

## Task 1 — the guard pin

Six arms, not five (arm F was added by plan correction 16 after the "five arms" heading was
written; the heading is stale, the arm list is not — I kept all six). Arms A, C and D have **no
authorized editor**; arms B, E and F name task 4 as sole editor. Grepped before writing anything,
per the brief's own instruction:

- **Arm C** (`test_a_recorded_column_named_by_keeps_its_metric_and_warns`,
  `test_a_recorded_by_column_warns_even_with_no_report_by_declared` in `tests/test_cli.py`) —
  **already exist, byte-for-byte matching the brief's description**, both asserting
  `step_block["by"]["value"] == pytest.approx(39.0)`. No new code needed; this batch adds nothing
  to arm C, and the diff to both bodies is 0 lines, confirmed by not touching them.
- **Arm D** — also already exists: `test_an_unknown_column_raises` (`UnitTable({"u1": {"pred": 1.0}})`,
  a table holding another column, `t.nope` raises `E-STEP-COLUMN-UNKNOWN`) and
  `test_a_derived_key_colliding_with_a_recorded_column_is_refused` (`collapsed = {f"u{i}": {"r":
  float(i)} ...}`, a **numeric** column, raises `E-STEP-KEY-COLLISION`). Both grepped and read; both
  already satisfy arm D's two sub-claims exactly. No new code added for arm D either.

New tests written for arms A, B, E, F (`tests/test_stats.py` for B and F; `tests/test_cli.py` for A
and E).

**Arm A** (`test_a_numeric_only_run_is_untouched_by_h5b_no_editor`): a real `run_a_project` call,
`aggregate_returns="total"` (so `_AGGREGATE_STEP`'s numeric-only `pred` column is used, not the
default `STARTER_STEP`'s bool `present`), 40 units, two seeds, `pearson`/`spearman` sweep, default
Holm correction. The whole `run["results"]` mapping is asserted against a literal, reproduced twice
via two independent `run_a_project` invocations and diffed byte-identical (both dumped to JSON files
and `diff`'d) before being written into the test.

**Arm B** (`test_a_bool_only_column_widens_exactly_seven_moving_keys`): Fixture A exactly as
specified — `u0`-`u3` recording `{"score": float(i), "valid": True}`, `u4`-`u5` recording
`{"valid": True}` only, `seed=7`, `draws=2000`. The narrow (TODAY) `collapsed` comes from a live
`collapse_repeats([...], "analyze", 0)` call on `_result`-built executions (asserted equal to
`{u0..u3: {"score": i}}`, 4 units — confirming Corrections 10's "carriage vs admission" claim
directly); the wide (AFTER) table is hand-written. `derived`/`resample` were **computed**, not
invented: a helper reads the collapsed dict via `row.get("valid")`/`"score" in row` rather than
`UnitTable.valid`/`UnitTable.score` attribute access, because the narrow table carries no `valid`
column at all (not merely a non-numeric one — the column is absent from every row), and a real
attribute read would raise `E-STEP-COLUMN-UNKNOWN`. Measured (not reasoned) via a scratch probe
against `src/publishable/stats.py` directly; all seven literals in the brief's table reproduced
exactly, including `mean_score.resample_draws` 2000 → **1998** (this fixture's own number at
`seed=7`), and all five "must not move" literals (`mean_score.value`, `score.value`,
`score.n.completed`, `score.ci95`, `score.method`) reproduced identically on both drives.

**Arm E** (`test_the_correction_family_measurement_arm_e_no_editor_except_task_4`): a real
`run_a_project` run, six units, `_ARM_E_STEP` recording `{"score": i+thr, "valid": True}` for `i<4`
and `{"valid": True}` otherwise (`thr` 0.5 pearson / 0.4 spearman), `GenericTemplate.aggregate`
monkeypatched to return `n_rows`/`mean_score` via row-dict access (same reason as arm B). **The
committed test asserts only the TODAY (unpatched) column.** The AFTER column was measured — not
committed — by additionally monkeypatching `publishable.cli.collapse_repeats` with a widened
implementation modelled on the shipped design (admit every unit, carry every non-numeric value when
constant, `None` when a column disagrees) and re-running the identical fixture. That re-measurement:
- **Reproduced all three of the scoping's cited literals**: `n_paired` 4 → 6; the `correction_level`
  swap (`mean_score` 0.025 → 0.05, `score` 0.05 → 0.025); `score.ci95_corrected` moving in its last
  digits (`[-0.10000000000000014, -0.09999999999999998]` → `[-0.10000000000000017,
  -0.09999999999999995]`).
- **Reproduced both literals the scoping's own paragraph does not name** (Corrections 9): the derived
  contrast's own `ci95`/`ci95_corrected` moving (`[-0.10000000000000009, -0.09999999999999998]` →
  `[-0.10000000000000053, -0.09999999999999964]`), and both conditions' `aggregated…mean_score.ci95`
  widening (`[1.0, 3.0]` → `[0.8333333333333334, 3.1666666666666665]`; `[0.8999999999999999, 2.9]` →
  `[0.7333333333333334, 3.0666666666666664]`).
- **Reproduced every "must not move" literal**: `vs_baseline…score.n_paired` (4, both), `score.ci95`
  identical, `n_rows.correction_level` identical (0.016666666666666666, both).
- **A gap between plan correction 7 and arm E's own brief, named as found**: correction 7 says "arm
  E captures 1999 from its own run" but arm E's key table carries no `resample_draws` row at all. I
  did not invent one; `mean_score.resample_draws` was not asserted in the committed test at all
  (only its `ci95` and `n.completed`). The 1999 figure appeared as a `W-STATS-RESAMPLE-THIN` warning
  in the AFTER run's stdout during the re-measurement, confirming the run-derived-seed shape
  correction 7 describes, but it is not a pinned literal in this arm — the brief names no key for it
  to pin.
- The monkeypatch does not ship; it lived only in the scratch probe used to produce the numbers
  above, never in the committed test file.

**Arm F** (`test_a_derived_metrics_permutation_p_value_widens_but_a_recorded_columns_never_gets_one`):
Fixture A's two tables again, `null_test={"method": "permutation", "n": 500, "shuffle": "grp",
"level": "rows"}`, `labels` mapping unit → `"a"`/`"b"` by parity, `seed=7`, and a `null_fn` that
reads the **relabelled mapping** it is handed (`compute(table, labels)`, per
`permutation_of_derived`'s own signature) to compute mean-of-group-a minus mean-of-group-b. Measured:
`mean_score.p_value` `0.846307385229541` (TODAY, 4 units) → `0.812375249500998` (AFTER, 6 units),
`null_draws` `500` both — matching the brief's literals exactly. `score` (the recorded column) has
neither key present at all, in either table, confirmed by `"p_value" not in ...`/`"null_draws" not
in ...` assertions (absence, not `None`) — matching the brief's "score has no p_value at all" claim,
which I also confirmed by reading `stats.py`'s recorded-column loop (no `p_value`/`null_draws` write
anywhere in it; both only appear in the derived branch below).

**The five mutations (step 7)**, each applied by editing the source, keeping a byte-copy first,
running the affected test, then restoring by copying the backup back and re-running to confirm
byte-identical restoration (verified with `diff` against the backup after every restore, not by
`git status`):

1. `collapse_repeats`: deleted `or not _is_numeric(value)` from the inner skip. Arm B's TODAY side
   **failed** (asserted `narrow == {...}` no longer held — the bool-only units now enter the table).
   Arm A **passed** unaffected (its fixture is genuinely numeric-only, confirmed).
2. `summarize_step`: deleted `all(_is_numeric(v) for v in raw)` from the column-loop gate (kept `if
   not raw:`). Arm B's original assertions still passed, so I added two more assertions
   (`"valid" not in today`/`after`) specifically to catch this mutation — under the mutation, a
   `valid` metric block appeared in `after` and the new assertion **failed**, confirming
   discrimination; restored, and the assertion still passes clean.
3. `cli.py`: changed `if "by" in step_summary:` to `if False:`. Both arm C tests **failed**
   (`W-STATS-STRATUM-SHADOWED` no longer printed).
4. `correction.py`: reversed the Holm rank ordering (tried both a sign-flip on `_evidence_ratio` in
   the sort key and a full `list(reversed(sorted(...)))` — same measured result either way). **Arm
   E's `score.correction_level` assertion failed** (0.05 expected, got 0.016666666666666666), and my
   `n_rows.correction_level` "must not move" assertion also failed (0.016666666666666666 expected,
   got 0.05). **`mean_score.correction_level`'s assertion did NOT fail** (stayed 0.025) — measured,
   not assumed, and it is a real finding rather than a fixture defect: this fixture's correction
   family has exactly 3 members (`n_rows`, `mean_score`, `score`), `n_rows`'s zero-width contrast
   gives it an infinite evidence ratio, and Holm's `α/(family_size−rank+1)` map is an involution that
   is its own fixed point at the median rank for any odd-size family — reversing rank order by
   construction cannot move the middle-ranked member's level, whichever of the two ways "reverse the
   ordering" is implemented. The brief's plain reading ("must FAIL for both metrics") does not
   survive this measurement for a 3-member family; 2 of the 3 correction-level assertions in the
   committed test do fail under the mutation, which is sufficient to catch it, but `mean_score`'s
   alone would not be.
5. `UnitTable.__getattr__`: returned an all-`None` column instead of raising. Arm D(i)
   (`test_an_unknown_column_raises`) **failed** (`DID NOT RAISE ContractError`).

All five source files (`stats.py`, `cli.py`, `correction.py`) were restored and verified
byte-identical to their `ee8085e`-derived starting copies via `diff` before the full suite was
re-run and before committing.

## Task 2 — § Templates

Located the target paragraph by `grep -n 'Columns are whatever the step' docs/reference.md` (one
hit, line 1706 pre-edit), under the **first** "§ Templates" heading (`## Templates: where parameters
are defined`, anchor `#templates-where-parameters-are-defined`) — not the later `## Templates`
`my_assay` table, per Corrections 8. Added the recorded-column half beside the existing
declared-attribute sentence, in the same shape: a non-numeric recorded column is carried; it
collapses across a unit's repeats to its value when every repeat agreed and to `None` when they
disagreed (extending [§ What isn't a repeat](#what-isnt-a-repeat)'s "Attributes constant within a
key collapse to that value with no rule needed"); it is disclosed as a warning when repeats
disagree; and it is a column and never a metric, citing § Statistical reporting. Did not touch the
four-operation contract table.

Linked to `#what-isnt-a-repeat` and `#warnings-core-reports`. Both anchors verified by grepping the
actual heading text (`#### What isn't a repeat` at line 2054, `### Warnings core reports` at line
369) rather than by grepping for the link syntax — the check the brief specifically asks for, since
the two headings answering to "§ Templates" is exactly the kind of position-based mistake this
slice's own corrections warn about.

Mechanical pass on the edited line: no trailing whitespace, no tabs (checked with
`grep -nP ' $|\t'`), no table touched, no new `x` for `×` introduced.

Cross-document pass: grepped my diff for backticked `data.`/`statistics.` paths — the only one
introduced is `` `data.units.measurements.collapse` ``, already present and documented elsewhere in
`reference.md` (§ The one config file's row and two § Errors rows), so nothing new is owed to § The
one config file. Grepped the four documents for a repeat-level collapse rule shown as a settable
input: none found — the new sentence states a derived rule (what core computes), matching every
other passage's treatment.

No mutation (a document has no behaviour) — named blind in the task, discharged by task 1's arm B
(and by task 3's read-side decision below, both of which pin the behaviour this sentence describes).

## Task 3 — § The per-unit tables, § Statistical reporting, `W-STATS-REPEATS-DISAGREE`, spec-defects

**Step 1.** Replaced the "not decided here" clause in § The per-unit tables (found by grepping
`more forgiving reading`) with Decision 11's ruling: read side publishes a metric only when every
carried value is a real number (one string costs the column its own block, nothing else, the column
still reaches `aggregate`); write side (`E-STEP-RETURN-TYPE`) stays strict, stated with the config-
vs-data reason given in the design.

**Step 2.** Added one sentence to § Statistical reporting, right before "An interval needs two
units...": "A metric block's `value` is a number" — tied explicitly to the `units`-basis row and
explicitly scoped away from the `repeats`-basis rows and the `summary`-step `Estimate`/`reported:
true` case, which I read first (both the `basis: repeats` table row and the `Estimate`/`reported:
true` worked example around line 2475) to confirm neither is contradicted: `reported: true` lives
under `results.summary`, a different top-level key from `aggregated`, and a `repeats`-basis point
estimate is whatever the step itself returned, which is a different rule entirely.

**Step 3.** Minted `W-STATS-REPEATS-DISAGREE` in § Warnings core reports' single big table, placed
alphabetically between `W-STATS-NULLTEST-FAMILY` and `W-STATS-REPORTBY-THIN` (located by grepping
both codes, not by position). One row, "Reported at `run` time, once per (condition, step)" — Ruling
2's `aggregate_where` locator, restated in prose rather than naming `data.units.measurements` as the
*location* of the fault (the row's condition text does name `data.units.measurements` as the
declared **remedy**, which Ruling 2 explicitly permits — "name the remedy in the message if it
helps; the `where` locates the fault"). Confirmed the single-call-site claim: `grep -n
'collapse_repeats(' src/publishable/*.py` → one production call site (`cli.py:2874`) plus the
definition in `stats.py` — run myself, matching the brief's own instruction not to trust a
helper-scoped claim.

**Step 4.** Read each of the three named § Errors rows, then grepped, in that order:
- `E-STEP-KEY-COLLISION` (line 1117): the row already reads "a derived key against a recorded
  column" and already states the recorded-column half is re-reported at `run` as
  `W-STATS-AGGREGATE-FAILED` rather than raised. No emit site added by this slice's tasks 1-3; the
  row does not move.
- `E-STEP-COLUMN-UNKNOWN` (line 1136): the row reads "a column no row of the unit table holds" —
  stays exactly true as the held set widens. No change.
- `E-STEP-RETURN-TYPE`: covered by step 1's decision — the write stays strict, no change to any row
  naming it (lines 992, 995, 1117, 1228).

No row narrower than its code was found; nothing filed as a finding here.

**Step 5.** Filed the write-side residual in `spec-defects.md` as a new `## OPEN` entry, owner
unassigned with the stated reason (no remaining slice — H6, H9, H3c-3's remaining 14 — has the write
side as its surface, and H5a is merged). Named that H5a's design claimed "Filed, not built, owner
H5b" for this exact question and that no such filing existed:
`grep -n 'more forgiving\|mixed column' docs/superpowers/spec-defects.md` → **0 lines** at `ee8085e`
(re-run before my edit); control `grep -c 'E-STEP-RETURN-TYPE' docs/superpowers/spec-defects.md` →
**4** at the same point, confirming the sweep can hit when the phrase is actually present. Both
greps re-run after my edit: the phrase now appears (my own entry), and the `E-STEP-RETURN-TYPE` count
moved to 7.

**Step 6.** Consistency passes: mechanical (no trailing whitespace/tabs in either edited file,
checked directly) and the enum-comment check — grepped the four documents plus `CLAUDE.md`/`README.md`
for an inline `# a | b | c`-style comment enumerating `W-STATS-*` codes; none found, so nothing needed
widening.

**Step 7.** No mutation (named blind, per the brief) — its replacement is task 1's arms B/F (which
pin the read-side behaviour this task documents) and the later tasks' fixtures C/D, not built in
this batch.

## Concerns / findings to carry forward

1. **Arm E's mutation-4 finding** (above): "reverse the Holm rank ordering must fail both metrics'
   `correction_level`" does not hold for a 3-member family where one member sits at the median Holm
   rank — this is a mathematical property of the correction, not an implementation gap, and the
   committed test still discriminates the mutation (2 of 3 correction-level assertions fail), just
   not via the specific metric the brief's prose names.
2. **Arm E's `resample_draws` gap**: plan correction 7 says arm E should capture `1999` from its own
   run, but arm E's own key table in the brief names no `resample_draws` key to pin it under. I did
   not invent one under a key the brief doesn't ask for; the `1999` figure is visible only as a
   `W-STATS-RESAMPLE-THIN` warning during the (unshipped) AFTER re-measurement.
3. Per CLAUDE.md's rule against reporting zero disagreements: I found real, checkable disagreements
   in (1) and (2) above rather than reporting a clean pass, and both are measured rather than
   reasoned about.

No `.superpowers/sdd/.gitignore` clobber observed; the file still carries its full warning comment
and the `task-*-brief.md`/`*.diff`/`*.txt` ignore rules, unaffected by anything in this batch.
