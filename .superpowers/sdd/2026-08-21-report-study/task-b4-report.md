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
