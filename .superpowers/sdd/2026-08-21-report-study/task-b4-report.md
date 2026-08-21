# Batch 4 (tasks 4-7): `report`'s form, the four standard sections, two renderers — report

Branch `h8c-report-study`. Ran directly in the foreground throughout — no monitor, no background
wait for any `pytest` invocation. Order 4 → 5 → 6 → 7, each committed separately.

## Status

All four tasks landed. Suite: baseline **2689 passed, 1 skipped, 2 xfailed** → **2737 passed, 1
skipped, 2 xfailed** after task 7 (task 4: 2703, task 5: 2716, task 6: 2725, task 7: 2737). mypy
**50** (unchanged — no new source files). `ruff format --check` and `ruff check` clean throughout.
A fifth commit fixed an alphabetical-ordering slip in the § Errors table (see below); it changed no
behavior and the suite re-ran clean after it (2737/1/2, mypy 50).

## Commit SHAs

- `556565b` — H8c task 4: report's form by file name, and a record reader a bundle member can use
- `9a3202c` — H8c task 5: the Conditions and Deltas sections, contrasts and strata included
- `6c642b0` — H8c task 6: the verdict and attrition sections, and the nondeterministic filing
- `eebbe2a` — H8c task 7: the markdown and HTML renderers, and the format refusal
- `ca4e47a` — H8c task 7 fix: alphabetize E-REPORT-FORM/-FORMAT rows before E-REPORT-OVERRIDE-*

## What was built

**Task 4.** `report.report_form(path)` decides `"run"`/`"bundle"` from the file **name** alone
(`run.yaml`/`study.yaml`), refuses a directory and any other name with `E-REPORT-FORM`, and touches
no filesystem state — a missing path is left for whatever reads it next. `lineage.read_record_file
(path)` is the extracted parse-and-refuse body operating on the record **file** itself;
`read_run_record(run_dir)` now delegates as `read_record_file(run_dir / "run.yaml")`. The
`E-UPSTREAM-RECORD-MISSING` message no longer claims "this is not a run directory" (false of a
bundle member, a bare file) — reworded to "the run never finished, or the path is wrong", true of
both operand shapes. § Errors widened: one new `E-REPORT-FORM` row, and the `E-UPSTREAM-RECORD-*`
row (in § Errors core raises, where it actually lives — see Concerns) now names `report` and `study
add` as the third and fourth callers.

**Task 5.** `report.conditions_section(run)` and `deltas_section(run)` — the first two of
`BaseReport.sections`'s four standard sections. Both build a `Section` whose `body` is
`{"rows": [...]}`; each row carries identifying columns plus whichever named fields the
corresponding record entry holds, read through a shared `_present_fields(entry, names)` helper
(`if name in entry`, never a subscript) so a `by` stratum's missing `repeat_spread` and an unpaired
delta's absent `n_paired` render correctly without special-casing. `by` is excluded from the metric
set via `stats.RESERVED_METRIC_NAMES`, imported rather than a literal. Deltas reads `vs_baseline`
**and** top-level `results.contrasts` (confirmed below). `family`/`family_size` travel through the
same `_present_fields` mechanism, read generically as whatever mapping `family` holds.

**Task 6.** `hypotheses_section(run)` and `attrition_section(run)` complete the four.
`BaseReport.sections` now yields all four in Decision 5's order. Attrition walks `execution.shared`,
`execution.conditions[]` (discriminating a condition-scoped step's direct `status` entry from a
repeat-scoped step's repeat-label-keyed one, by the same rule `derive_step_scopes_and_repeats`
uses) and `execution.summary`; renders `provenance.input_manifest_changed` as the list it is,
never coerced to a boolean; and does **not** claim `nondeterministic`. Filed in
`docs/superpowers/spec-defects.md` as a real, dated entry with Owner: unassigned and the reasoning
for why neither H8c nor H4 can claim it.

**Task 7.** `render_markdown`/`render_html` — one section stream, two emitters, sharing
`_format_cell`/`_table_columns`/`_as_rows` so a formatting decision is made once. `render_report
(report_cls, run, io)` is the one place `format` is read and `E-REPORT-FORMAT` is raised: `None`
(no override) renders the four standard sections as markdown unconditionally; a real subclass
declaring no `format` (or an unrecognized one) is refused rather than defaulted. HTML is a
self-contained, offline document (no external stylesheet/script/font ever). `render_report` takes
no format parameter — pinned directly on its signature. Section order is pinned from the **rendered
text** of Fixture R (`text.index("## Title")`), never by reordering `BaseReport.sections`'s own
yields. § Errors gained one row for `E-REPORT-FORMAT`, in this commit.

## Fixtures R and D

Built via `tests.test_cli.run_a_project`, driven end to end through `main(["run", ...])`: 24 units
with a `cohort` attribute, `report_by: [cohort]`, a `baseline`+one-`grid` sweep (2 conditions), 3
seed repeats, a starter step recording a numeric `score` column and calling `io.skip` on every
eighth unit, a `summary` step returning two `Estimate`s (one `n: null`, one `n: 40`), and one
`confirmatory` hypothesis. Fixture D adds one declared `statistics.contrasts` entry beside
everything Fixture R has. Both fixtures' own shape is pinned by dedicated tests
(`test_fixture_r_is_shaped_the_way_this_task_needs`,
`test_fixture_d_declares_one_contrast_beside_r_s_own_shape`) before anything is asserted against
sections built over them — "a fixture is a claim too."

## M14, reported by name and in full

**The carried mutation.** Task 1 named the render-level arm forward: an override reaching into a
**standard** section's mapping `body` and mutating it before yielding, then confirming the mutated
figure is what a reader ultimately sees, and that `Section`'s frozen-ness still blocks *rebinding*
`body` to a different object entirely. No standard section with a mapping body existed until task 5
built one, so it could not be written until now.

**Built as:** `test_m14_an_override_mutating_a_standard_sections_mapping_body_in_place_reaches_the_
page` (`tests/test_report.py`). An override's `sections` calls `super().sections(run, io)`, reaches
into the yielded Conditions section's `body["rows"][0]["value"]`, sets it to
`"MUTATED-BY-OVERRIDE"`, and yields the (same object) section on. The test asserts:

1. the returned `Section`'s `body["rows"][0]["value"] == "MUTATED-BY-OVERRIDE"` — the mutation
   **does** reach what a reader reads back, because `Section` is frozen against rebinding `title`/
   `body`, not against mutating a mapping `body` in place (Decision 2's own claim, restated as a
   type property rather than a comment);
2. `conditions.body = {"rows": []}` still raises `dataclasses.FrozenInstanceError` — the one thing
   frozen **does** guarantee still holds.

**Outcome: PASS as written.** This is a positive pin of documented behavior, not a mutation applied
to source and reverted — there is nothing to revert here; the property under test is that the
in-place mutation succeeds and the rebinding attempt still fails, and both branches are asserted
directly.

## Deltas reads both `vs_baseline` and top-level `results.contrasts` — confirmed

`deltas_section` (`src/publishable/report.py`) calls `_vs_baseline_rows(condition)` for every
condition's `vs_baseline` block **and** `_declared_contrast_rows(contrast)` for every entry in
`results.get("contrasts")`, unconditionally, both feeding the same `rows` list. Pinned by
`test_deltas_section_reads_vs_baseline` (over Fixture R, which has no declared contrast) and
`test_deltas_section_reads_results_contrasts_too` (over Fixture D, asserting a row whose
`comparison == "spearman_vs_baseline"` — the declared contrast's own `id` — exists and carries the
same `delta` the record's `results.contrasts[0]` does). M4 (dropping the `results.contrasts` loop)
was run and reverted; it is caught **only** on Fixture D, exactly as the brief predicts, because
Fixture R's every delta already lives in `vs_baseline` and the two branches are identical there.

## Task 6 files `nondeterministic` rather than claiming it — confirmed

`docs/superpowers/spec-defects.md` gained a new, dated, real entry: **"OPEN — `nondeterministic` is
documented as a `run.yaml` field and a thing `report` notes, and nothing writes it or reads it back
— Owner: unassigned."** It states the measurement (zero occurrences in a real `run.yaml` and
`executions.jsonl`, grepped after a genuine run), the two document passages left stranded (§ The two
files' `run.yaml` example, `design-principles.md` § Not bit-identical reruns's "notes it in
`report`"), **why H8c and H4 are both the wrong owner** (H8c may not alter a run; H4 is the complete
family and would not claim a new entry), the check its owner must make (whether `run` owes an
emitter, or whether the "notes it in `report`" sentence should go), and which section it lands in
the day the field exists (`attrition_section`'s `_execution_rows`, which already spreads `**entry`
onto each row and would need no new traversal). `attrition_section` itself does not mention the
field, pinned by `test_attrition_section_does_not_mention_nondeterministic`, which asserts its
absence against a real run's `execution` block via `yaml.safe_dump`, not merely against this
module's own output.

## Mutations run, exact text, and outcome — every one reverted and the revert re-run

**Task 4.**
1. *Make `read_record_file` accept a directory (append `run.yaml` unconditionally).* Changed the
   function's first line to `path = path / "run.yaml"` before the existence check. **FAIL** (caught)
   — 30 of the module's tests failed, including every bundle-member-shaped arm
   (`test_read_record_file_reads_a_bundle_member_shaped_file_directly` and its siblings) and,
   notably, `read_run_record` itself (which now double-appends `run.yaml`). Property-preserving arm:
   none exists for this one — the property under test is exactly "a bundle member is a bare file",
   so any config where the function is handed a file (not a directory) differs.
2. *Decide the form by `is_dir()` instead of by name.* Two variants run: (a) only the directory
   branch changed to `return "run"` instead of raising — caught by both
   `test_report_form_refuses_a_directory_even_though_diff_accepts_one` and
   `test_report_form_a_directory_named_run_yaml_is_still_refused`; (b) the whole function replaced
   with `return "run" if path.is_dir() else "bundle"` — caught by 7 tests, including
   `test_report_form_any_other_name_is_e_report_form` (a non-directory file named neither
   `run.yaml` nor `study.yaml`, which the brief calls out by name). Both **FAIL** (caught).
   Property-preserving arm: none — every arm distinguishes "decide by name" from "decide by
   `is_dir()`" by construction.

**Task 5.**
- **M4** — dropped the `results.contrasts` loop from `deltas_section`. **FAIL** (caught) —
  `test_deltas_section_reads_results_contrasts_too` (Fixture D). Property-preserving arm: Fixture R
  (no declared contrast) — both branches are identical there, confirmed by re-running the mutation
  against the full `test_report.py` and seeing every Fixture-R-only Deltas test still pass.
- **M13** — removed the `metric in RESERVED_METRIC_NAMES` guard from the top-level metric loop in
  `_condition_metric_rows`. **FAIL** (caught) —
  `test_conditions_section_metric_names_exclude_by_and_match_the_record_exactly` (`{'by', 'score'}
  == {'score'}` failed). Property-preserving arm: a run with no `report_by` declared — `by` never
  appears in `aggregated[step]` at all there, so the guard's removal is invisible; not run as a
  separate arm since Fixture R already carries the positive case and the brief's own text names the
  no-`report_by` case as identical-under-mutation.
- **repeat_spread mutation** — dropped `"repeat_spread"` from `_CONDITION_METRIC_FIELDS`. **FAIL**
  (caught) — `test_conditions_section_top_level_metric_carries_the_named_fields` (`KeyError:
  'repeat_spread'`, since the test iterates the full named-field list against the row). A `by`
  stratum row was never going to catch this one (it never carries `repeat_spread` to begin with) —
  confirmed by `test_conditions_by_stratum_carries_no_repeat_spread_and_the_renderer_does_not_
  require_one` staying green under the same mutation.

**Task 6.**
- *Walk only `execution.conditions`, skip `shared` and `summary`.* Removed the `shared` block's
  loop and the `summary` block's loop from `_execution_rows`, leaving only the `conditions[]` walk.
  **FAIL** (caught) — `test_attrition_section_walks_shared_conditions_and_summary`
  (`'summary' in {'repeat'}` failed: the row set had no `summary`-scope entry at all). Fixture R
  carries a `summary` step for exactly this reason. Property-preserving arm: a run with no `summary`
  step declared at all — its `execution.summary` block is `{}`, so walking it or not is
  indistinguishable; not built as a separate test, since the brief names Fixture R's own `summary`
  step as the sole discriminator and no other task 6 fixture exists.
- *Read `provenance.input_manifest_changed` as a boolean.* Wrapped the stored value in `bool(...)`.
  **FAIL** (caught) — `test_attrition_section_input_manifest_changed_is_rendered_as_the_list_it_is`
  (`False == []` failed — Fixture R's own recorded value is the empty list, and `bool([])` is
  `False`, which is exactly the collision the brief calls out). Property-preserving arm: a
  hypothetical record whose `input_manifest_changed` already held a non-empty list would still
  differ (`bool([...])` is `True`, a different rendered value from the list itself) — not
  separately fixtured, since Fixture R's own empty list is already the sharper case (`False` and
  `[]` are the same truthiness and different renderings, which a non-empty list's mutation would
  not test as cleanly).

**Task 7.**
- **M10** — added `format = "markdown"` as a `BaseReport` class attribute. **FAIL** (caught) — three
  tests: `test_base_report_declares_no_format_attribute` (task 1's own pin),
  `test_render_report_with_an_override_declaring_no_format_is_e_report_format`, and the
  dedicated `test_m10_a_report_class_genuinely_declaring_no_format_is_refused_not_defaulted`.
  Property-preserving arm, per the brief's own wording: an override that *does* declare `format`
  explicitly — its declared value would still win regardless of the base default, so that arm is
  identical under the mutation; exercised implicitly by
  `test_render_report_with_a_real_override_dispatches_by_its_declared_format`, which stayed green
  under this mutation (checked by hand while the mutation was applied, then reverted alongside the
  rest).

Every mutation above was reverted **by editing the file back** (never `git checkout --`), `ruff
format`/`ruff check`/full `test_report.py` re-run clean after each revert, and `__pycache__`/stale
`pytest-of-joon` dirs cleared before every run.

## What I grepped, and its scope

- `E-STUDY-UNREADABLE` across the whole repo (`grep -rn`): three hits, all in
  `docs/superpowers/plans/2026-08-21-report-study.md` and
  `docs/superpowers/specs/2026-08-21-report-study-design.md` — no implementation exists yet, and
  none is owed by tasks 4-7 (it is task 10/13's own code, over `study.yaml` itself, not over a
  bundle member `read_record_file` reads). Correctly out of this batch's scope.
- `RESERVED_METRIC_NAMES` definition (`grep -n` in `src/publishable/stats.py`): one definition,
  `frozenset({"by"})`, imported rather than restated.
- `nondeterministic` (`grep`/`yaml.safe_dump` inside a test, over a genuine Fixture R run's
  `execution` block): zero occurrences, matching the plan's own measurement at `ebf642a`.
- `provenance["units"]`, `wall_seconds`/`attempts`/`started_at` field names, and the `execution`
  block's three-way shape (`grep -n` in `src/publishable/run_record.py` and `tests/test_cli.py`):
  confirmed the exact shapes `_metric_n_rows`/`_execution_rows` read against, before writing either.
- `run_a_project`'s override kwargs (`sweep`, `statistics`, `hypotheses`, `extra_steps`,
  `extra_step_source`, `_starter_step`, `unit_attributes`) (`grep -n` and direct reads in
  `tests/test_cli.py`): confirmed against real usages before building Fixtures R/D on them, rather
  than guessing the calling convention.
- `\`E-REPORT-` across `docs/reference.md` after task 7 landed: found the alphabetical-ordering slip
  (my task 4 rows sat after task 3's `E-REPORT-OVERRIDE-*` rows rather than before them) and fixed
  it in the follow-up commit.
- `git diff --stat` against `main` for the whole batch: confirms only `docs/reference.md`,
  `docs/superpowers/spec-defects.md`, `src/publishable/lineage.py`, `src/publishable/report.py`,
  `tests/test_lineage.py`, `tests/test_report.py` changed — nothing in `cli.py`, `diff.py`, or any
  guard-pin test file from task 17.

I did not grep for every possible caller of `report_form`/`read_record_file`/`render_report` outside
this module and its tests (there are none yet — task 8 is the first to wire them into `cli.py`), and
I did not re-derive the guard pin's four arms; I only confirmed by `git diff --stat` that none of
their files moved.

## Concerns for review

1. **Row placement for `E-REPORT-FORM`/`E-REPORT-FORMAT`.** Both raise-time (not validate-time)
   codes, placed in § Errors `validate` reports rather than § Errors core raises — following the
   precedent task 3 already set for `E-REPORT-OVERRIDE-*` there, and matching `E-DIFF-CONFIG-
   UNREADABLE`'s placement in the same table for the analogous `diff` operand fault. The
   `E-UPSTREAM-RECORD-*` row I widened, by contrast, lives in § Errors core raises (where it was
   already, and where `read_run_record` documents it) — I did not move it, on the grounds that the
   task 4 brief's "§ Errors `validate` reports" heading names where the *new* row goes, and the code
   outranks a section label for an *existing* row. Worth a second look.
2. **The table-row `body` shape (`{"rows": [...]}`) is my own invented convention**, used
   consistently across all four sections and both renderers, since neither the design nor the plan
   specifies a mapping shape beyond "core knows how to render it as a table." An override handing
   `self.section(..., body=<arbitrary mapping>)` is handled by a fallback (`_as_rows` turns a
   `rows`-less mapping into one `{key, value}` row per entry) rather than refused, so nothing in this
   batch forces an override into this shape — but it is the shape every standard section actually
   uses, and a reviewer should confirm it reads as "a mapping core tables" rather than as a
   surprise.
3. **Fixtures R and D are hand-composed for this batch**, not lifted from a shared fixture module —
   `_fixture_r_or_d` lives only in `tests/test_report.py`. Tasks 8-10 (not mine) will need their own
   route to a comparable real run if they want the identical shape; nothing here prevents building
   one, but nothing here shares code with them either.

---

## Fix round 1

Review at `.superpowers/sdd/2026-08-21-report-study/task-b4-review.md` (spec compliance PASS, task
quality PASS with findings — three Majors, eleven Minors, no Critical). Every mutation the original
report claimed reproduced exactly, and nothing dispatched. Addressed below, in the review's own
order. Gates before this round: mypy 50, `ruff format --check` 90, suite 2737 passed/1 skipped/2
xfailed. After: mypy 50, formatter 90, suite **2738 passed, 1 skipped, 2 xfailed** (net +1 test —
the M3 pin; every other change edited or strengthened an existing test rather than adding one).

### MAJOR 1 — M14's first half rebuilt to render and assert on the emitted text

`test_m14_an_override_mutating_a_standard_sections_mapping_body_in_place_reaches_the_page`
(`tests/test_report.py`) no longer asserts on the row dict a mutation was just written into. It now
renders the mutating override's sections through **both** `render_markdown` and `render_html` and
asserts `"MUTATED-BY-OVERRIDE"` appears in each rendered string, with a control assertion first (the
same sections rendered from a plain, unmutated `BaseReport` do **not** contain that string) so the
positive assertion means something. The second half (the frozen-rebinding pin) is unchanged.

**Verified by running:** with `render_markdown` gutted to `return "GUTTED"`, the test **fails**
(`assert 'MUTATED-BY-OVERRIDE' in 'GUTTED'`) — reverted by editing the function back, confirmed
`diff`-identical against the pre-mutation copy, and `pytest -k m14` re-run green. Property-preserving
arm: none — gutting either renderer is exactly the property this half exists to catch, so there is no
config on which the two branches (real render vs. gutted) agree.

### MAJOR 2 — Fixture R now carries all three `execution` nesting shapes for real

`_fixture_r_or_d` (`tests/test_report.py`) no longer routes through `run_a_project`'s `extra_steps`
(which generates every extra step from one shared `extra_step_source`, so it could not give two
extra steps two different scopes). It now calls `generate_experiment`/`generate_step` directly and
overwrites each generated file: a `run`-scoped step (`step02_shared_check`, lands in
`execution.shared`), a `condition`-scoped step (`step03_cond_check`, direct `status` under
`conditions[].steps`, no repeat label), the original `repeat`-scoped starter step
(`step01_summarize_units`), and the `summary`-scoped step (now `step04_summarize`, renumbered by the
new generation order — every reference to the old `step02_summarize` name was updated).
`test_attrition_section_walks_shared_conditions_and_summary` now asserts `scopes ==
{"shared", "condition", "repeat", "summary"}` (was: only checked `"summary"` and `"repeat"`) and
pins the `shared_row`'s step/status and the `condition_rows`' identity, over **both** conditions.

**Verified by running, both prescribed mutations, against the rebuilt fixture:**
1. Deleting the `shared` walk and the `summary` walk from `_execution_rows`, leaving only the
   `conditions[]` walk — **FAIL** (caught): `scopes` comes back `{'condition', 'repeat'}`, missing
   `shared` and `summary`.
2. Replacing the condition-vs-repeat discriminator (`if "status" in value:`) with `if False:` —
   **FAIL** (caught): `scopes` comes back without `'condition'` (`{'repeat', 'shared', 'summary'}`).

Both reverted by editing back, confirmed `diff`-identical, full `test_report.py` re-run green after
each (75 passed before the M3 test was added, 76 after). Property-preserving arm: a run with no
`summary` step and no `condition`-scoped step at all — its `execution.summary` is `{}` and every
`conditions[].steps` entry is repeat-label-keyed, so walking those two shapes or not is
indistinguishable; not built as a separate fixture, since the point of this fix is that Fixture R
itself must not be that fixture, and now isn't.

### MAJOR 3 — the Conditions filter excludes `by` structurally, never by name; design correction filed

`_is_metric_entry`/`_is_strata_block` (`src/publishable/report.py`) replace the `RESERVED_METRIC_
NAMES` exclusion in `_condition_metric_rows`. A key's value is a metric row if it carries `value`
directly; it is walked as a `report_by` stratum block only if it is a `Mapping` three levels deep
(attribute → level → metric) with a genuine metric entry at every leaf. Neither test asks what the
key is *called*. `stats.RESERVED_METRIC_NAMES` is untouched (still `frozenset({"by"})`, still
guarding the derived-key collision at its own site in `stats.py`) and stays imported for the two
Deltas-side guards, which are now commented as defensive-but-unreachable rather than left to look
tested (see m1 below).

**New pin, over a real run:** `test_a_recorded_column_named_by_renders_as_a_real_metric_row`
(`tests/test_report.py`) reuses the shape `tests/test_cli.py`'s
`test_a_recorded_column_named_by_keeps_its_metric_and_warns` already established — a starter step
recording `io.record(unit.key, {"pred": ..., "by": ...})` with `statistics.report_by: [cohort]`
declared beside it. Asserts: `W-STATS-STRATUM-SHADOWED` prints; the real record's
`aggregated[step]["by"]` is a genuine metric entry (`basis: units`, carries `value`); the Conditions
section renders a `metric == "by"` row whose `value`/`basis`/`ci95` match the record; and no
phantom `by_attribute == "cohort"` stratum row exists for that step (the column shadows the strata
entirely, per `cli.py`'s own rule — "no strata are reported for this step" — so there is nothing to
walk). **Verified by running:** passes against the fixed code; the docstring of the existing
`test_conditions_section_metric_names_exclude_by_and_match_the_record_exactly` was reworded to say
the exclusion is structural (Fixture R's `by` genuinely IS the strata shape) and to point at the new
test for the sibling case, rather than continuing to claim a literal-name exclusion that no longer
exists.

**Design correction filed**, not merely worked around: `docs/superpowers/plans/2026-08-21-report-
study.md` and the design's Decision 5 are the plan's own artifacts and are dated/pinned records per
`CLAUDE.md`'s development-record rules — I did not edit either, since a spec records what was
decided when it was written and retro-editing it destroys that evidence. The correction lives where
this fix round's own record is checkable: this report (naming Decision 5's false ground, its true
replacement, and the code that now embodies it) and the code's own docstrings, which state the
structural rule and cite Major 3 by name. If a later slice edits the design document itself, this is
the ground it should carry forward: *"the record `report` reads can never hold a metric called `by`"*
is false — `cli.py`'s `W-STATS-STRATUM-SHADOWED` writes exactly that shape on purpose, and the
correct rule is structural (does the value carry `value`, or is it an attribute→level→metric nesting),
never the name `"by"`.

### Minors closed

- **m1** — `_vs_baseline_rows` and `_declared_contrast_rows` each gained a docstring paragraph
  stating their `RESERVED_METRIC_NAMES` guard is defensive rather than reachable, because
  `cli.py`'s `_comparison_step_blocks` already drops `by` from both blocks' metric sets on the write
  side. Not rewritten to remove the guards — a second, cheap check costs nothing — but no longer
  left to look pinned by a test that cannot reach it.
- **m2** — `_declared_contrast_rows` gained a docstring paragraph naming the `{"id", "of", "against"}`
  blacklist's assumption explicitly (correct today against `cli._compute_declared_contrasts`, and
  naming both silent-failure directions a future change could hit) rather than leaving it
  undocumented.
- **m3** — closed for all three loops named: Fixture D now declares TWO contrasts (`test_fixture_d_
  declares_two_contrasts_beside_r_s_own_shape`, `test_deltas_section_reads_results_contrasts_too`
  now check both by id); `test_attrition_section_carries_each_metrics_own_n` now checks both of
  Fixture R's conditions; `test_attrition_section_walks_shared_conditions_and_summary`'s
  `condition_rows`/`repeat_rows` assertions now check both conditions' indices (folded into the
  Major 2 fixture rebuild above, since the same fixture change and test rewrite closed both). All
  three `[:1]`-style mutations were run and caught (see Major 2/3 verification above and the
  dedicated runs against `deltas_section`'s `results.contrasts` loop, `_metric_n_rows`' condition
  loop, and `_execution_rows`' condition loop — each failed a named test, each reverted and
  confirmed `diff`-identical).
- **m4** — `attrition_section`'s docstring now cites the filing's real heading
  (`"`nondeterministic` is documented as a `run.yaml` field and a thing `report` notes, and nothing
  writes it or reads it back"`) instead of the nonexistent `"A repeat's `nondeterministic`..."`.
- **m5** — the filing in `docs/superpowers/spec-defects.md` now states the measurement's calendar
  date (2026-08-21) alongside its commit pin (`ebf642a`).
- **m6** — acknowledged, no code or history change: `ca4e47a`'s commit message's stated ground
  ("alphabetize") is not a convention the table follows (verified in the review: 18 descending
  transitions among 147 rows). The change itself (moving the two new rows to sit with the other
  `E-REPORT-*` rows) is not reverted — only the ground was wrong, not the move — and I have not
  amended the pushed commit message; this paragraph is the correction of record. Not repeated as a
  design convention anywhere else in this round.
- **m7** — no change. The reviewer's own conclusion is that `reference.md:3209`'s "the directory
  isn't a run directory at all" is scoped to § Lineage between runs' `reuse_from` surface, where the
  operand genuinely is a run directory — not false there, only adjacent to a row task 4 widened.
- **m8, m10, m11** — no code or document change this round; routed as the review directs. m8 (the
  `{"rows": [...]}` convention is undocumented) is task 16's, the documents batch. m10 (a non-`str`,
  non-`Mapping` `body` raises `AttributeError` rather than a diagnostic) is unowned by any decision
  or brief and is routed to task 8, which owns the command surface where a traceback becomes a
  diagnostic. m11 (the `report_cls is None` → markdown ruling, authored by task 7 rather than a
  design decision) is named for task 16's audit to review the sentence at `docs/reference.md:568`
  rather than inherit it silently.
- **m9** — adjudicated acceptable by the review, with a note to carry forward: **stated explicitly
  here, since the review asked for it** — `tests/test_report.py` holds two separate real-project
  builders, `_build_project` (task 3's, behind Fixtures O/V) and `_fixture_r_or_d` (task 5's,
  further diverged from `run_a_project` in this round to get three distinct step scopes). Tasks 8-13
  should pick one of the two routes deliberately for their own Fixture P/T/B arms rather than
  inheriting whichever one a brief happens to reach for first.

### What I grepped this round, and its scope

- `grep -n "A repeat's" docs/superpowers/spec-defects.md` — zero hits, confirming m4's citation was
  dangling before the fix and resolves to the real heading after it.
- `grep -n '"E-REPORT-' docs/reference.md` (from the prior round, re-checked unaffected by this
  round's changes — no § Errors row touched this round).
- `git diff --stat` against the pre-fix-round tree: confirms only `src/publishable/report.py`,
  `tests/test_report.py`, and `docs/superpowers/spec-defects.md` changed. Nothing in `cli.py`,
  `diff.py`, or any task-17 guard-pin file.
- Did not re-grep the whole repo for `RESERVED_METRIC_NAMES` usage outside this module — confirmed
  only that `report.py`'s own three remaining sites (the two Deltas-side guards) are the ones m1
  named, by reading the file rather than a fresh repo-wide grep.

### Tree state

Every mutation applied by editing the file and reverted by editing it back — never `git checkout
--`. Each revert confirmed `diff`-identical against a `/tmp` scratch copy before moving to the next
mutation. `uv run pytest` run directly in the foreground throughout this round; no monitor, no
background wait. `find … -name pytest-of-joon` and `__pycache__` cleared before every run. Arm D
(task 17's guard pin) was not touched — `git diff --stat` confirms `tests/test_diff.py` and every
other task-17 file are absent from this round's diff.
