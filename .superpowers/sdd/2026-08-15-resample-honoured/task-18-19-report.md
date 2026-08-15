# Task 18+19 report — the last two tasks of H4a, batched

**Status: both COMPLETE.** Two commits, one per task, on `h4a-resample-honoured`:

- Task 18: `645a009` — `test: pin that strata mint no Members and a summary Estimate is never recomputed`
- Task 19: `aee11b3` — `docs: close the init-materializes-optional-blocks residual — no, and here is the behaviour argument`

**Test summary:** `uv run pytest` — **1800 passed + 2 xfailed** (baseline 1798 + 2 new tests in task
18, task 19 added none). `ruff check .` clean. `mypy` clean. `ruff format --check .` reports 62
pre-existing reformattable files unrelated to either task (confirmed via `git stash` against the
pre-task tree — identical count).

## Task 18

Both properties verified live before writing anything, per the brief's "check what exists before
building."

**Property 1 (`report_by` levels mint no `Member`s): already true, confirmed by reading the code**
(`_comparison_step_blocks`'s per-metric loop at `src/publishable/cli.py:772` excludes `- {"by"}`)
and by task 15's review, which already ran this live with a positive companion. Wrote the pin anyway
per the brief ("this slice touches this code whether or not it claims anything here"), with a fresh
positive companion produced inside the same test.

**Property 2 (a `summary`-step `Estimate` is never recomputed): structural, and owed a test.**
`run_record.summary_values` (the only place an `Estimate` is expanded into `results.summary`) shares
no code with `stats.summarize_step` (the resample pass), so there is nothing for the pass to walk
into. Pinned with an exact-equality assertion plus a positive companion (a real column in the same
run resampled).

### A real disagreement with the brief, found and fixed

The brief's property-1 test asserted that a `report_by` level's **recorded column** (`pred`) would
carry `method: percentile_over_units` under a declared `resample`. Empirically it does not:
`cli.command_run`'s `report_by` level call to `summarize_step` (`src/publishable/cli.py`, around
line 2243) never passes `resample_columns`, so a level's own column interval stays `t_over_units`
regardless of what the run declares — confirmed by running the scenario before writing the test.
This is not a live bug introduced by this slice: it is `docs/superpowers/spec-defects.md`'s
`percentile_of_derived` entry, **Finding 2**, already found by task 15's review and deferred with a
named owner (H4 Statistics) on 2026-08-15. A level's own *derived* metric, by contrast, resamples
unconditionally whenever a seed and callable exist (`resample_columns` or not) — confirmed live and
matching the filed entry's own wording.

Fixed by rewriting the test's positive companion to use the level's derived metric (`mean_pred`,
via `aggregate_returns` composed with `_starter_step=_METHOD_VARYING_STEP`) rather than the
recorded column, and adjusting the family-shape assertion from `{comparisons: 1, metrics: 1}` to
`{comparisons: 1, metrics: 2}` since both a recorded column and a derived metric are present. Also
fixed the brief's `_SUMMARY_ESTIMATE_STEP` fixture, whose header comment referenced an unsupplied
`{pkg}` format key — `generate_step`'s `STEP_PY.format(step_name=step_name)` call only supplies
`step_name`, so the literal raised `KeyError: 'pkg'`; removed the `{pkg}` segment, matching every
other `extra_step_source` fixture in the file. Also corrected `extra_steps=["step02_report"]` to
`extra_steps=["report"]` — `generate_step` numbers and prefixes the file itself
(`step{number:02d}_{step_name}.py`), so the brief's literal would have written
`step02_step02_report.py`.

### Mutations (both applied, confirmed FAIL, reverted in place)

1. Removed `- {"by"}` from `_comparison_step_blocks`'s metric loop
   (`sorted(set(of_summary) & set(against_summary))`). `test_a_report_by_level_resamples_without_
   joining_the_correction_family` failed on the "no `by` entry in `vs_baseline`" assertion — a `by`
   block appeared as an ordinary (nonsensical) metric.
2. Added `"basis": "units"` to the `Estimate` dict `run_record.summary_values` builds.
   `test_a_summary_estimate_is_not_recomputed_by_the_resample_pass` failed on its exact-equality
   assertion.

Both reverted by editing in place (never `git checkout`); `__pycache__` cleared between mutate and
revert each time; confirmed PASS after revert. `git status --short src/publishable/cli.py
src/publishable/run_record.py` shows no diff after task 18.

## Task 19

Read the open entry first, as instructed. `docs/superpowers/spec-defects.md`'s "The generated config
calls itself 'the complete parameter set' before it is one" entry's **Open residual, routed**
paragraph named H4 Statistics as owner and left the materialize-or-not question open. Confirmed the
three grounds against the actual code before writing the ruling:

1. `grep -n 'resample\|null_test' src/publishable/materialize.py` — no hits; the `statistics:` block
   `materialize.py` writes contains only `correction: holm` and, at top level, `hypotheses: []`.
2. `reference.md` § The one config file already carries the "schema is wider than `init`'s literal
   output" sentence for `contrasts`/`report_by` (confirmed by reading it, unchanged by this task).
3. Empirically demonstrated (see Step 5 below) that materializing `resample` would be a **behaviour**
   change, not a text one, now that H4a has wired `resample_columns` into the honoring path.

**Ruling: no.** `init` should not materialize `statistics.resample`/`null_test`/`contrasts`/
`report_by`. Replaced the **Open residual, routed** paragraph with the closing ruling verbatim as
given in the brief (three grounds, in the order they bind). No `materialize.py` change, no
`reference.md` change.

### Step 5 mutation, and where the brief overstated it

Added `"  resample: {method: bootstrap, n: 2000}",` to `materialize.py`'s `statistics:` block and ran
`uv run pytest tests/test_cli.py -k undeclared_resample_shape`. The brief's Step 5 says "**Both** of
Task 1's pins must FAIL." Empirically only one did:

- `test_the_undeclared_resample_shape_is_pinned_absent_key` — **FAILED**, exactly as predicted: a
  generated project's `config.statistics` now carries the declared `resample` key, which the test
  asserts absent.
- `test_the_undeclared_resample_shape_is_pinned_explicit_null` — **still passed.** Its own
  `statistics={"correction": "holm", "resample": None}` override replaces the whole materialized
  `statistics` block via `run_a_project`'s top-level `doc.update(overrides)` (a plain dict replace,
  not a merge), so the mutation to `materialize.py` never reaches this test's config at all.

This is a minor overstatement in the brief, not a defect that changes the ruling: one pin failing is
sufficient to demonstrate ground 3 empirically (a materialized `resample` reaches an ordinary
generated project and changes its `run.yaml`). Reverted in place, `__pycache__` cleared, both pins
confirmed PASS again; `git status --short src/publishable/materialize.py` shows no diff.

## Concerns / carried forward

- Nothing new filed. Task 18's finding (the `report_by` level column asymmetry) was already on
  record as spec-defects.md's Finding 2 before this task started; this task's contribution is
  confirming it live and routing around it correctly in the test rather than asserting the brief's
  mistaken expectation.
- Task 19 leaves `materialize.py` and `reference.md` untouched, per the ruling's own conclusion — no
  follow-up owed.
- The pre-existing `ruff format --check .` non-idempotence (62 files) predates both tasks (verified
  via `git stash`) and is out of scope for this batch.
