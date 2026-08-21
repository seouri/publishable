# Batch 4 (tasks 4-7) review — `report`'s form, the four standard sections, two renderers

Reviewed at `2092594` on `h8c-report-study`. Gates re-run in the foreground: `ruff check` clean,
`ruff format --check` **90 files**, `mypy` **50 source files**, `uv run pytest` **2737 passed, 1
skipped, 2 xfailed** — every one matching the report's own numbers. Stale `pytest-of-*` and
`__pycache__` cleared before runs. Every mutation below was applied by editing the file, reverted by
restoring a scratchpad copy, and the revert verified `diff`-identical (never `git checkout --`).

## Verdicts

- **Spec compliance: PASS.** Decisions 1, 5, 16 and 19 are implemented as written, and corrections
  1, 8 and 9 are honoured. Verified by running: Deltas reads `vs_baseline` **and** top-level
  `results.contrasts` (a record with a declared contrast and no `vs_baseline` anywhere still renders
  its delta; a record with both renders both, one row per source); Conditions carries `basis`,
  `correction` **and** `repeat_spread`, with a `by` stratum row rendering `repeat_spread` as `null`
  rather than raising; `family`/`family_size` are read generically (an invented `{alpha, beta,
  gamma}` comparison family and a `{zeta, eta}` hypothesis family both render); the four standard
  sections are pure functions of the record (every probe ran over a hand-built mapping with `io =
  object()` and no directory in existence); section order is pinned from rendered text and a swap of
  two yields fails it; the HTML page is self-contained and the assertion fails when a `<link
  rel="stylesheet">` is inserted; `render_report` has no `format` parameter. **Nothing dispatches**:
  `report` is still in `NOT_BUILT_COMMANDS` (`cli.py:152`), `cli.py`/`diff.py` are absent from the
  batch diffstat, and the only import of this module outside its own tests is task 1's
  `from publishable.report import BaseReport` in `__init__.py`. Arm D did not fire —
  `tests/test_diff.py` is untouched by the batch and the suite is green.
- **Task quality: PASS with findings — three Majors, eleven Minors.** No Critical. The four tasks'
  reported mutations all reproduce exactly, naming the same tests; the findings are about seams the
  fixtures cannot see and about one carried mutation whose named property is asserted by nothing.
  **Which verdict each Major bears on:** M1 and M2 are task quality (unpinned properties). **M3 is a
  spec-side finding** — task 5 implemented Decision 5's instruction in Decision 5's own words, and
  the false claim is the design's — so it does not dock task quality, and the spec-compliance PASS is
  a PASS on *this batch's compliance with the design as written*, with M3 the one place the design
  itself needs the change.

## Findings

### Major

**M1 — M14's first half is vacuous: the property in its own name is asserted by nothing.**
`tests/test_report.py:1126-1155`. The test is named `..._reaches_the_page` and its docstring says
"confirm what a reader ultimately sees" — but it renders nothing. It sets
`section.body["rows"][0]["value"] = "MUTATED-BY-OVERRIDE"` and then asserts that the same dict holds
that value, which is a property of Python dicts, not of this module. **Verified by running:** with
`render_markdown`'s body replaced by `return "GUTTED"`, `pytest -k m14` **passes**. The real property
does hold — a probe confirms `"MUTATED"` appears in both `render_markdown` and `render_html` output
of the mutating override — so this is an unpinned true claim, not a defect in the code. The report
compounds it by calling the row dict "what a reader reads back", which is the proxy substitution
`CLAUDE.md` § Answering a question with a proxy is about. The fix is one line: assert on
`render_markdown(MutatingReport().sections(...))`. M14's **second** half is a genuine pin —
dropping `frozen=True` fails `test_m14_...` and `test_section_is_frozen_and_carries_title_and_body`
(verified) — though it duplicates task 1's coverage.

**M2 — two of the three nesting shapes `_execution_rows` exists to walk are exercised by nothing.**
`src/publishable/report.py:307-372` — `_execution_rows`' `shared` block (`:323`) and its
condition-scoped branch (`:339`, `if "status" in value`). **Verified by running:** deleting the `shared` walk entirely leaves
`tests/test_report.py` at **75 passed**; replacing the condition-vs-repeat discriminator with `if
False:` also leaves **75 passed**. **Verified by dumping the record:** Fixture R's
`execution.shared` is `{}` and its only `conditions[].steps` entry is repeat-label-keyed — it has no
run-scoped and no condition-scoped step. So the brief's prescribed mutation ("walk only
`execution.conditions`, skip `shared` and `summary`") is caught by its `summary` half alone, and
`test_attrition_section_walks_shared_conditions_and_summary` claims `shared` in its name while
asserting nothing about it (`CLAUDE.md`: *a test whose name claims the guarantee*). The discriminator
is the most delicate line in the function — correction 2's own measured rule, deliberately restated
rather than imported from `artifacts.derive_step_scopes_and_repeats` — and a restated rule with no
fixture is exactly the *seam named in the brief and instantiated by no fixture* row. Route:
`run_a_project`'s `extra_steps` can add a `run`-scoped and a `condition`-scoped step; the report's
disclosure ("Property-preserving arm: a run with no `summary` step") does not mention either gap.

**M3 — a recorded column named `by` is silently dropped from the report, and the design's grounds for
the guard are false against the code.** `src/publishable/report.py:97` (and, downstream,
`_metric_n_rows`). **Verified by running a real run** whose starter step calls `io.record(unit.key,
{"by": ..., "score": ...})`: `aggregated["step01_summarize_units"]` holds `by` as a **genuine metric
entry** — `{value: 5.5, basis: units, n: {...}, ci95: [3.21, 7.79], method: t_over_units,
repeat_spread: {...}}` — and `conditions_section` renders metrics `["score"]` only. `cli.py:3467-3477`
is explicit that this is intended on the write side: the `W-STATS-STRATUM-SHADOWED` message says the
recorded column of that name **"keeps its value"** and no strata are written. So Decision 5's
sentence *"the record `report` reads can never hold a metric called `by`"* is measurably false, and
the unconditional exclusion turns a warned-about shadowing at run time into an undisclosed omission
in the rendered deliverable — the silent-no-op class Decision 5's own cost paragraph names. No
phantom rows are produced (the `by` metric entry's nested values are not mappings-of-mappings, so the
strata walk yields nothing — checked), so the loss is the only symptom.

**Not a re-filing, and not task 5's fault.** `spec-defects.md` § New reserved metric name: `by`
(S4d task 5) already holds this ground and rules the opposite way for the record: *"The column wins:
it is a real measurement over the units, while the strata re-present numbers already in the
record"*, pinned by `test_a_recorded_column_named_by_keeps_its_metric_and_warns`. What is **new** is
that the column's win is defeated one consumer later — that filing's own opening sentence is *"every
consumer of a step block reads its keys as metric names"*, and `report` is the consumer that inherits
it, exactly as Decision 5 said it would. Task 5 implemented the instruction it was given, in the
words it was given (*"never from a literal"*), so **this Major bears on the design and on the S4d
filing, not on task quality.** Route, in order: correct Decision 5's grounds sentence and extend the
S4d entry (its own stated route — *"a future edit ... should say the name is spent"* — is about
documenting the reservation, not about the render); then either discriminate the two shapes (a strata
block is attribute → level → metric; a metric entry carries `value`/`method`) or render a row
disclosing the shadowed column, so a reader is told rather than shown nothing.

### Minor

**m1 — three of the four `RESERVED_METRIC_NAMES` guards are unpinned.**
`src/publishable/report.py:113, 186, 210` (stratum loop, `_vs_baseline_rows`, `_declared_contrast_rows`). **Verified by running:** removing `metric in
RESERVED_METRIC_NAMES or ` from each in turn leaves `tests/test_report.py` at **75 passed**; only the
top-level site (`:97`, M13's) fails a test. `_comparison_step_blocks` already drops `by`
unconditionally on the write side, so the two delta-side guards are defensive rather than reachable —
which is worth *saying in a comment* rather than leaving four guards of which one is pinned. Accepting
one site's mutation as covering four is a mutation applied to a proxy.

**m2 — `_declared_contrast_rows` separates identity keys from step keys by a literal blacklist.**
`src/publishable/report.py:207` (`if step in ("id", "of", "against")`). Correct today — verified
by reading `cli._compute_declared_contrasts`, whose entry is exactly `{id, of, against}` plus
`_comparison_step_blocks`' step → metric mapping, with corrections merged at metric level — and
`cli._entry_for` reads the same shape the same way. Two silent failure directions all the same, in a
module whose every other key decision is made from a shared constant: a future mapping-valued
non-step key renders as a phantom step whose keys are read as metric names, and a step named `id`,
`of` or `against` loses its rows.

**m3 — positional blindness in three list walks.** **Verified by running:** `[:1]` on the
`results.contrasts` loop (`:236`) leaves 75 passed, because Fixture D declares exactly one contrast —
`CLAUDE.md`'s *two elements only ever distinguish two answers*; `[:1]` on `_metric_n_rows`' condition
loop (`:288`) and on `_execution_rows`' condition loop (`:328`) both leave 75 passed **even though
Fixture R has two conditions**, so nothing asserts either walk covers the second one. The code loops
correctly; the fixtures cannot tell a loop from a first-element read.

**m4 — the docstring cites a filing heading that does not exist.**
`src/publishable/report.py:383` points a reader at `spec-defects.md`, *"A repeat's
`nondeterministic`..."*. **Verified by grep:** no heading or line beginning "A repeat's" exists in
that file; the real heading begins "`nondeterministic` is documented as a `run.yaml` field". A reader
greps for the quoted phrase and finds nothing.

**m5 — the filing is commit-pinned but not dated.** `docs/superpowers/spec-defects.md`, the new
`nondeterministic` entry. Task 6 step 3 asked for *"the measurement and its date and commit"*; the
entry gives `ebf642a` and no calendar date. Everything else the step asked for is there and correct —
owner `unassigned`, both stranded document passages, why H8c and H4 are both wrong owners, the check
the owner must make, and the section it lands in. The claim itself is sound: **verified by grep**
that `nondeterministic` has no writer in `src/` (a `BaseStep` attribute and `W-REPL-DETERMINISTIC`'s
read of the classes, nothing else), and no section claims it.

**m6 — `ca4e47a`'s stated ground is not a convention this table follows.** § Errors `validate`
reports is grouped **thematically, not sorted**; the evidence is a script over its code column, which
finds descending transitions throughout (18 among 147 rows on this revision). The move itself is benign and locally sensible (the two new rows now
sit with the other `E-REPORT-*` rows), but "alphabetize" as the reason is a rule the table does not
keep, and a later task may enforce it against 18 other rows.

**m7 — the reworded claim survives in prose.** `docs/reference.md:3209` still explains
`E-UPSTREAM-RECORD-MISSING` as *"the run never finished, or the directory isn't a run directory at
all"* — the half task 4 deleted from the emitted message as false of a bundle member. It is scoped to
§ Lineage between runs' own `reuse_from` surface, where the operand **is** a run directory, so the
sentence is not false; flagged because the row task 4 widened now points `report`'s bundle-member
reader at the same code, and *sweep for the claim, not for the file* is how this repo lost three
sweeps in one slice.

**m8 — concern (b), adjudicated: the `{"rows": [...]}` convention is documented nowhere.** **Verified
by grep of the four documents:** § A report override shows `body=render_scatter(...)` and says nothing
about `body`'s admissible shapes; § The importable surface's `BaseReport` row names only `sections`,
`self.section` and `__init__`; the phrase "a mapping core knows how to table" exists only in the
design. So an override author handing `self.section(..., body={...})` a mapping has no stated
contract, and `_as_rows`' key/value fallback — which makes any other mapping render rather than
refuse — is undocumented too. Nothing breaks; the four documents owe one sentence, and task 16 is the
documents batch. The convention itself is consistent across all four sections and both renderers, and
reads as "a mapping core tables" rather than as a surprise.

**m9 — concern (c), adjudicated: acceptable, with one note.** Local fixtures are fine — `run_a_project`
is the shared driver and the design describes each fixture per-slice. The note is that
`tests/test_report.py` now holds **two** project builders (`_build_project`, from task 3, behind
Fixtures O/V; `_fixture_r_or_d`, task 5's) while the design calls Fixture O *"a Fixture R project"* —
so tasks 8-13's Fixture P/T/B arms will pick one of two routes to a real run in this same file. Not a
defect; worth a line in the next brief so the choice is made rather than inherited.

**m10 — a non-`str`, non-`Mapping` `body` is an `AttributeError`, not a diagnostic.** **Verified by
running:** `render_markdown(iter([Section(title="t", body=42)]))` raises `AttributeError: 'int' object
has no attribute 'get'` out of `_as_rows`; same for a `list`, for `None`, and for `render_html`.
`body` is the one value an override supplies freely, and this module already refuses a bad `format`
with a coded refusal, so the asymmetry is worth naming. No decision or brief assigns the guard, so
this is **unowned rather than task 7's defect** — route it to task 8, which owns the command and the
surface where a traceback has to become a diagnostic.

**m11 — the `report_cls is None` → markdown ruling was authored by a code task.** `render_report` in
`src/publishable/report.py` and the § Errors row at `docs/reference.md:568`. The design's Fixture O
licenses the *path* — *"a positive control with no `report.py`, asserting the four standard sections
render and no diagnostic prints"* — but no decision rules that the medium there is **markdown**, and
task 7 both chose it and wrote it into a normative § Errors row in the same commit (*"is not refused:
core renders its own four standard sections as markdown"*). The behaviour is almost certainly right
(`generate report` is opt-in, so the no-override path must render something) and the row's reasoning
is sound; graded low because Fixture O anticipates the case. Named so task 16's audit reviews the
sentence rather than inheriting it.

### Concern (a) — adjudicated, no finding

The split is right. § Errors `validate` reports' own intro says it carries *"the codes a **command**
reports, and a code raised at load can be in both, reported here and raised there"* — so raise-time
codes a command prints belong there, which is where `E-DIFF-CONFIG-UNREADABLE` and task 3's
`E-REPORT-OVERRIDE-*` already sit (verified by line number: all inside the 406-1058 table).
`E-UPSTREAM-RECORD-*` correctly stays in § Errors core raises, because `io.reuse_from` raises it into
a step; the row now names all four callers. No row was moved that should not have been.

## Attack items verified by running, with their result

| Item | Result |
|---|---|
| Deltas reads both sources | **PASS.** Declared-contrast-only record renders its delta; both-sources record renders two rows, one per source. `by` excluded via `stats.RESERVED_METRIC_NAMES` (imported, `frozenset({"by"})`). Conditions carries `basis`, `correction`, `repeat_spread` |
| M14, both halves | **Half a pin** — see M1. Rebinding raises `FrozenInstanceError` (pinned); "reaches the page" is asserted by nothing |
| Decision 19, generic family | **PASS.** A `{alpha, beta, gamma}` comparison family and a `{zeta, eta}` hypothesis family both travel and render; nothing keys on `comparisons`/`metrics` |
| Task 6 files rather than claims | **PASS**, with m4 and m5 |
| Correction 1's three parts | **PASS.** `read_record_file` extracted, `read_run_record` delegates. Each of the five guards deleted in turn fails a named test: missing (8 tests across `test_lineage` **and** `test_diff`, i.e. reachable from both entries), invalid YAML, not-a-mapping, no `run_id`, `schema_version`. The **message** separation the brief demanded is pinned too — rewriting the not-a-mapping message to the YAML one fails `test_read_record_file_not_a_mapping_on_a_bare_file_path_is_distinguishable_by_message`. `E-STUDY-UNREADABLE` is correctly absent (task 10 owns it, and the plan carries it at its § Task 10) |
| Three disclosed concerns | (a) no finding; (b) m8; (c) m9 |
| Batch 3's two lessons | Ordering: the section-order pin is read from rendered text and a yield swap fails it (verified). Positional: m3 |
| Prose and pins | Arm D untouched and green; § Errors rows landed in their raising commits (`E-REPORT-FORM` in `556565b`, `E-REPORT-FORMAT` in `eebbe2a`); anchors in both new rows resolve; no trailing whitespace or tabs on any added line; no `x`-for-`×`; no positional locators and no config-count claim in the report. **The moved-row sweep the two insertions and the reorder owed:** the prose bracketing § Errors `validate` reports makes no count claim over its rows — its one enumeration phrase (*"those two envelope rows"*) names `E-CONFIG-PARSE`/`E-CONFIG-SHAPE` by identity earlier in the same paragraph, and its *"none of this table's other rows"* claims stay true with two more rows in it. The one positional locator in that region (`docs/reference.md:297`, *"the rows above, between them"*) sits above the insertion point and did not move. § Errors core raises' widened row moved nothing |
| The report's own mutation table | **Every entry reproduces**, naming the same tests: M4 → `test_deltas_section_reads_results_contrasts_too` only; M13 → `test_conditions_section_metric_names_exclude_by_and_match_the_record_exactly`; `repeat_spread` → `test_conditions_section_top_level_metric_carries_the_named_fields`; skip-shared-and-summary → `test_attrition_section_walks_shared_conditions_and_summary` (see M2); `bool()` → `test_attrition_section_input_manifest_changed_is_rendered_as_the_list_it_is`; M10 → three tests including task 1's own pin. Task 4's directory mutation is caught by `test_report_form_a_directory_named_run_yaml_is_still_refused` **alone** — the sibling arm passes under it, exactly as that test's own docstring predicts, which is the two-arm sizing the brief asked for |

## What I could not check

- The per-task intermediate suite counts (2703 / 2716 / 2725) — not re-run per commit. The final
  **2737 / 1 / 2**, mypy **50** and formatter **90** are verified.
- Fixture R's two `Estimate`s (`n: null` and `n: 40`) — read in the fixture source, not asserted
  against the record by me.
- Whether tasks 8-10 need a shared route to a Fixture-R-shaped run: their briefs are not extracted
  yet, so m9 is a note rather than a ruling.

## Tree state

Clean at `2092594`. Every mutation reverted by editing back and confirmed byte-identical against a
scratchpad copy; two throwaway probe test files were created and deleted; `git status` reports no
changes.
