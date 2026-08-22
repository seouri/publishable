# Batch 4 report — H5b tasks 12, 13, 14

**Status: complete.** All three tasks done, in order, each committed separately. Gates clean after
each task: `uv run ruff check .` (clean), `uv run ruff format --check .` (93 files, unchanged),
`uv run mypy` (52 source files, unchanged). Suite: 2926 passed / 1 skipped / 2 xfailed (baseline,
end of batch 3) → task 12: **2928** passed → task 13: **2929** passed → task 14: **2931** passed,
skip/xfail counts unchanged throughout. `.superpowers/sdd/.gitignore` was found already clobbered
to a bare `*` at the start of this session (the tracked-content restoration this file itself warns
about); restored to its documented content before any commit, confirmed byte-identical to the
tracked version by `git diff` before proceeding.

**Commits:**
- `29d0a0d` — H5b task 12 (`E-STEP-COLUMN-UNKNOWN` pinned in both directions)
- `336ed45` — H5b task 13 (the silent case's discriminating test)
- `a855f91` — H5b task 14 (`report`/`study` as readers of `aggregated`, three docstrings re-derived)

## Task 12 — `E-STEP-COLUMN-UNKNOWN` pinned in both directions

Grepped first, per the brief's own instruction: `grep -rn 'E-STEP-COLUMN-UNKNOWN' tests/*.py` found
five hits — `tests/test_stats.py:2316` (`test_an_unknown_column_raises`, pin arm D(i): a table
holding `pred`, `t.nope` raises) and four in `tests/test_cli.py` (a docstring, and
`test_fixture_b_control_...`'s own real-run assertion of the code on stdout). Arm D(i) already
covers the direct-call "still fires, on a table that holds other columns" shape exactly, so no third
copy was added — reported rather than duplicated.

Two new tests in `tests/test_cli.py`:
- `test_task_12_step1_an_attribute_read_of_a_now_carried_column_stops_firing`: six units, `p1`-`p4`
  record only `score` (numeric), `p5`-`p6` record only `valid` (bool, no number at all).
  `AttrReader.aggregate` reads `units.valid` by **attribute** (`UnitTable.__getattr__`), never
  `.get`. `n_valid` is `2.0`, no `W-STATS-AGGREGATE-FAILED`/`E-STEP-COLUMN-UNKNOWN` on stdout.
- `test_task_12_step2_still_fires_for_a_genuinely_absent_column_with_containment`: `AbsentContainment`
  reads `units.nothing_ever_records_this` — still raises, contained, `run.yaml` written, and `score`'s
  own `t_over_units` block (`value: 1.5`) is present and correct despite the derived call failing
  whole — `cli.py` calls `template.aggregate` once inside one `try`, so a raise there loses the WHOLE
  `derived` dict, but the recorded-column loop in `summarize_step` never touches `aggregate` at all.

**The mutation proving each direction**, applied to `_gather_repeats` (restoring the pre-H5b rule:
drop a unit from `gathered` entirely when none of its values, across every column, are numeric —
verified empirically against Corrections 5/10's own pre-H5b numbers before writing the fixture,
since the brief names the concept rather than a literal diff and the exact code shape needed
reconstruction from documented pre-H5b behaviour):
- Mutation (i), `UnitTable.__getattr__` returns an all-`None` column instead of raising: step 2's
  real-run assertion (`W-STATS-AGGREGATE-FAILED`/`E-STEP-COLUMN-UNKNOWN` in stdout) **and** arm D(i)
  (`test_an_unknown_column_raises`) both FAIL — `DID NOT RAISE`/`AssertionError` respectively. Step 1
  unaffected (still passes) — confirms the mutation is arm-specific.
- Mutation (ii), the admission-rule restore in `_gather_repeats`: step 1's `n_valid` assertion FAILS
  (`KeyError: 'n_valid'` — the derived call now raises `E-STEP-COLUMN-UNKNOWN` again since `p5`/`p6`
  are dropped entirely and `valid` never reaches any surviving row). Step 2 unaffected.
Both reverted by editing the file back (not `git checkout`), each revert verified by re-running the
affected tests, then the full suite.

## Task 13 — the silent case's discriminating test

`test_task_13_the_silent_drop_cannot_be_mistaken_for_the_fix` in `tests/test_cli.py`. Eight units:
`p1`-`p3` record ONLY `flag: True` (no numeric column — the pre-H5b admission rule drops these three
entirely); `p4`-`p5` record BOTH `flag: True` and `score` (admitted either way, `flag` intact under
the old rule too since it does not filter individual values, only whole rows); `p6`-`p8` record only
`score`. `FlagCounter.aggregate` counts `flag` via row-dict `.get` over `UnitTable` iteration — never
an attribute read, so the wrong number cannot masquerade as a raised exception.

**The two readings, computed by running, both ways:**
- Correct (current code): `value: 5.0` (`p1`-`p5`), `n.completed: 8` (`len(collapsed)`, the whole
  table), `ci95: [2.0, 8.0]`.
- Buggy (mutation applied — the same admission-rule restore as task 12's mutation (ii)):
  `value: 2.0` (`p4`, `p5` only — `p1`-`p3` dropped since they carry no number anywhere), `n.completed:
  5`, `ci95: [0.0, 4.0]`.

Why the fixture discriminates and Fixture A (task 4/1) does not: the units with NO numeric column
(`p1`-`p3`) are placed to coincide exactly with bool carriers, so the admission rule's row-drop
actually removes `flag` values from the table (rather than merely shrinking `n` while leaving the
count unchanged) — Fixture A's own bool-only units never disagree with its own count assertions on
this axis.

**Deviation from the brief's literal third fact, disclosed rather than silently substituted**: the
brief names `resample_draws` not equalling `draws` as the third discriminating fact. Measured both
ways it is `2000` under both codes — `percentile_of_derived` only drops a draw when `compute` returns
`None`/`nan` or raises, and a plain count over a bootstrap draw that always holds `len(units)` rows can
never do any of the three (unlike Fixture A's `mean_score`, which divides by a possibly-empty numeric
subset). Substituted the interval itself (`[2.0, 8.0]` vs `[0.0, 4.0]`) as the third fact — a stronger
one, since a buggy point estimate of `2.0` would still have to reproduce the correct interval to be
mistaken for it, and does not.

**Mutation**: same admission-rule restore. All three assertions were checked in sequence; `assert
block["value"] == 5.0` is the one that fails first (`2.0 == 5.0`), reported per the brief's
instruction to name which fails first. Reverted by editing back, verified by re-running.

**What this test does not pin**, stated in its own docstring per the brief's step 3: nothing about the
correction family (arm E), nothing about a column disagreeing non-numerically across repeats
(Fixture C/L), nothing about `report`/`study` (task 14's).

## Task 14 — `report`/`study` as readers of `aggregated`, three docstrings re-derived

**Fixture J** (`_fixture_j_run`, `tests/test_report.py`): six units, `p1`-`p4` record `score` and
`valid` together, `p5`-`p6` record only `valid`. `limits.min_reported_n: 1` so `study add`'s thin-
metric prompt never fires on this fixture's own numbers (default floor is 10; `score`'s contributing
count is 4).

- `test_fixture_j_report_renders_the_carried_and_the_dropped_columns_correctly`: renders
  `publishable report` over Fixture J's `run.yaml`. Parses the `## Conditions` markdown table
  **structurally** — extracts the `metric` column's exact cell values via `_table_metric_names`,
  rather than a substring search over the whole page (`assert "valid" not in out` would also pass
  if the word never appeared anywhere else, or if `report` crashed before rendering). Asserts
  `{n_rows, n_valid, mean_score, score} <= names` and `"valid" not in names`.
- `test_fixture_j_the_floor_walk_sees_exactly_four_metric_entries` (`tests/test_study.py`): grepped
  `_floor_metric_entries` first (`grep -n '_floor_metric_entries' src/publishable/study.py` → two
  hits, its definition and its one caller in `study_add`) and read the walk before asserting what it
  sees, per the brief. Builds a real bundle (`study new` + `study add ... --as main` through `main`),
  reads the bundled `main.run.yaml` back, calls `_floor_metric_entries` directly on that real record,
  and asserts the four metric-name suffixes and no fifth.

**Both mutations, run against the real fixtures above:**
- (i) Emptied `summarize_step`'s `carried = [... if _is_numeric(value)]` gate (made it a no-op) —
  step 1's `"valid" not in names` FAILS (`'valid'` present in the parsed column) and step 2's four-
  entry assertion FAILS (`'valid'` is a fifth name in the set). Both confirmed by running.
- (ii) Pointed `study.py`'s floor walk at `condition.get("aggregated")` itself rather than iterating
  its `step → block` nesting (one level short — the shape a prior slice's review found "dead on
  every real record") — step 2 FAILS: `_floor_metric_entries` returns an empty list against the same
  real record that gave four entries before the mutation.
Both reverted by editing back, each revert verified by re-running the affected test.

**The three docstrings, re-derived, each grepped against the code before editing:**
- `test_a_run_without_a_holdout_pins_its_denominators_and_artifacts` (`tests/test_cli.py`) claimed
  *"`stats.summarize_step` drops a bool column outright"* as the reason the scaffold's un-narrowed
  `aggregated[step]` is `{}`. False attribution: `GenericTemplate` inherits `BaseTemplate.aggregate`,
  which returns `{}` unconditionally regardless of what `collapsed` holds (Decision 12) — true
  whether `present` is a bool or a number, and true before and after H5b. `summarize_step`'s own
  per-column gate does separately refuse `present` a metric block of its own (still true, still
  live), but that is not why the derived side is `{}`. Re-derived to name Decision 12 as the actual
  cause and state the column-gate fact as a separate, secondary one — the false clause deleted
  rather than relocated.
- `test_a_baseline_sweep_reports_a_delta` (`tests/test_cli.py`) said the scaffold's step *"records
  only a bool ..., filtered by `_is_numeric`"*, naming the right predicate without saying which
  function runs it — ambiguous after H5b's task 4, since the collapse itself no longer filters
  anything by type (it did, pre-H5b). Re-derived to name `stats.summarize_step`'s own per-column
  `_is_numeric` gate explicitly, and to state that the collapse carries `present` unfiltered since
  task 4.
- `test_an_unclustered_resampled_contrast_draws_what_it_always_drew` (`tests/test_cli.py`) said the
  default step's bool *"grows no `basis: units` column and no `vs_baseline` block at all"* — **true
  and unchanged**, since a non-numeric-for-every-unit column still earns no metric block after H5b
  (Ruling 1's first row), so no contrast can be built over it either. Left untouched, per the brief.

**Grep counts reported, not assumed**: at the commit before this batch's edits (`336ed45`),
`grep -c "drops a bool column outright" tests/test_cli.py` → 1; `grep -c "filtered by
\`_is_numeric\`" tests/test_cli.py` → 1; `grep -n "grows no"` → 1 (the third docstring's claim spans
a line break, so a single-line `-c` search for the full phrase gave 0 — found by the `-n` search
instead, which is why the exact phrase is quoted here rather than assumed present from a `-c` count
alone).

## Concerns

- Task 12's and task 13's mutation is not literally "restore `or not _is_numeric(value)` in
  `_gather_repeats`" as a textual diff — the current `_gather_repeats` (post task-4 refactor) has no
  such clause to "restore" verbatim, and a literal per-value filter alone reproduces task 12's
  outcome but not task 13's (verified by direct experiment before writing either fixture: a pure
  per-value filter drops `flag`/`valid` from every row unconditionally, giving `n_flag: 0` rather
  than task 13's required `2.0`). The mutation actually applied — dropping a unit from `gathered`
  entirely when none of its values are numeric — reproduces both tasks' required outcomes and
  matches Corrections 5/10's documented pre-H5b numbers (`n_rows: 4.0` for Fixture A's six-unit
  case). Flagging this reconstruction for review rather than asserting it is the literal historical
  diff.
- Task 13's third discriminating fact deviates from the brief's literal wording (`resample_draws`)
  for a stated, measured reason (a plain count cannot produce a degenerate draw) and substitutes the
  bootstrap interval itself, which is a strictly stronger discriminator. Disclosed in both the test's
  own docstring and above rather than silently swapped.
