# Task 6 report — Carry `technical_n`, and retire `E-DATA-MEASUREMENTS-UNSUPPORTED`

**Status:** DONE (all four parts; part 2 wired for the input path, step path deferred and recorded).
**Commits:** `ed48f75` *feat: data.units.measurements is a declaration core honors*; `7cbc161`
*docs: state where measurements' sub-fields live, and pin the stratum omission*; `3978870`
*fix: measurements.by is checked against the source's columns, not attributes* (fix round 1).
**Tests:** `uv run pytest` **1160 passed, 2 xfailed**, with `ruff check` and `mypy` clean, all three
run on the tree at `3978870`. `ruff format` not run.

## 1. The precondition (closed before the retirement)

`validate._check_measurements` reports **`E-UNITS-ATTR-MISSING`** at
`data.units.measurements.by` when `by` names **no column of the source table** **and** the input
path actually merged rows. The signal is `technical_n["max"] > 1`, threaded out of
`_check_units` (which now returns `(roster, technical_n)`); the comment that said it was discarded
is gone.

**Why gated rather than unconditional.** `units.collapse_measurements` groups on the unit **key**
alone — `by` is read only to drop that column from the merged attributes — so a typo'd `by` never
misgroups; the fault is that the licence to collapse rests on a name nothing declared. And
`StepIO._collapse_measurements` never reads `by` at all: on the step path the measurement identity
is one the *step* invents (`io.record(..., measurement=read_id)`) and no input column carries it, so
an unconditional check would refuse a design `reference.md` § What isn't a repeat documents. Filed
as a document gap in `spec-defects.md` ("`by` means two different things on the two collapse
paths"), so the gate is not read as timidity later.

**Fix round 1 — the reference set was wrong and is now the source's columns.** The first cut
checked `by` against `data.units.attributes`, which refused the exact YAML `reference.md` § What
isn't a repeat and `experimental-designs.md` § Technical and biological replication both print
(their fence declares no `attributes` at all); `design-principles.md` § Core vs. plugin — the
tiebreaker — lists `measurements.by` beside `attributes` as a *parallel* namer of an input field;
and `E-UNITS-ATTR-MISSING`'s own registry row already stated the doc-faithful predicate ("names a
value the source table has no column for"). The columns are threaded out of the single read
`units._from_table` already does — `_from_table`/`_from_glob` now return `(units, columns)` and
`resolve_units` returns `(roster, technical_n, columns)` — so nothing re-reads the header and the
two cannot disagree. **The gate is unchanged**; only the reference set moved. A typo'd `by` still
names no column and is still refused.

Code reuse rather than a new identifier: the user-facing question is the one `E-UNITS-ATTR-MISSING`
already answers. Its § Errors `validate` reports row now names the new surface and its predicate,
and § Validation gains a "Measurement axis exists" checks-table row beside its neighbours.

New tests from this round: `test_the_documents_own_fence_shape_is_accepted` (a `by` naming a real
column with **no** `attributes` declared — the case whose absence let the wrong predicate through)
and its control `test_a_by_no_column_carries_is_refused_even_with_no_attributes_declared`. Mutation:
swap `columns` back to the declared attributes → the fence test FAILs → revert → PASSes.

## 2. `technical_n` — the route decision task 9 should follow

**Decision: two routes, and which one a fact takes is decided by where `reference.md` shows it.**
Stated in `stats.summarize_step`'s docstring so it is findable from the code:

- **A key that JOINS `n` travels in `counts`.** § What isn't a repeat: the three-part `n` is "joined
  by `clusters` … by `effective` … by `ineligible`". So **`effective` is task 9's `counts` work**, not
  a new carrier. Note for task 9: `counts` is annotated `dict[str, int]` and `n` is built as
  `{**counts, "completed": …}`; Kish's `effective` is not an integer, so that annotation widens.
- **A key that sits BESIDE `n` travels in `summarize_step`'s new `beside_n` parameter** — a mapping
  copied verbatim into every metric block, computed keys merged last so it can never shadow `n`.
  § What isn't a repeat shows `technical_n` there; § Weighted samples shows **`weighted_by`** in the
  same position (`r: {value: 0.607, basis: units, weighted_by: sampling_weight, …}`), so task 9's
  `weighted_by` is this parameter, not `counts`. I checked the document rather than assuming.

Copied into **both** of `summarize_step`'s loops — recorded columns and derived metrics — because the
document's own example of a metric carrying `technical_n` is `r`, which `aggregate` derives.

**Not passed to `report_by` level blocks**, for the reason a level block already carries no
`repeat_spread`: `technical_n` is over the whole roster, and copying it onto a stratum would state a
spread nobody computed over that subset. Pinned, not merely commented, by
`test_a_report_by_level_block_carries_no_technical_n` (mutation: pass `beside_n` to the level call →
FAIL → revert → PASS).

**Input path only; step path deferred.** A step-measured run has one input row per unit, so an
ungated `technical_n` would report `{min: 1, max: 1, median: 1}` beside a `measurements.parquet`
holding three rows per unit — a *false* claim of no replication, the same class of wrong number part
1 closes. `command_run` therefore carries it only when `max > 1`. Carrying the step path's own counts
needs a per-execution measurement count on `ExecutionResult`, reconciled across a condition's repeats
(a unit measured three times in every repeat is one count, not three) — deferred and recorded in
`spec-defects.md`. `reference.md` § What isn't a repeat now states the reporting condition, so the
absence is documented rather than silent.

Pinned by reading `run.yaml` from a real `main(["run", …])`, not a return value:
`test_technical_n_reaches_run_yaml_beside_every_metrics_n` (asserts on both `pred`, a recorded
column, and `total`, a derived metric), plus two controls — undeclared `measurements`, and a
declaration over an input that merged nothing.

## 3. The `envelope.py` outcome: the FIRST one — no whole-leaf block

`data.units.measurements` stays in `LEAF_TYPES` as `dict` **and** gains typed children
`.by` (`str`) and `.collapse` (`str | dict`); `_check_unknown_keys` now checks containers **before**
leaves so a path that is both is typed *and* descended into. No existing path is both, so the
reorder is a no-op for everything else.

So `measurements` never becomes a fifth whole-leaf block, and **neither the closed-schema paragraph
nor the "latent rather than live" passage was edited.** Evidence: `{by: read_id, colapse: mean}` now
reports `E-CONFIG-KEY-UNKNOWN` at `data.units.measurements.colapse`
(`test_a_typo_inside_the_measurements_block_is_now_reported`); `collapse: {depth: mean}` stays a leaf
and reports nothing (`test_a_per_column_collapse_map_is_a_leaf_not_a_container` — descending there
would report every column name as unknown); `measurements: "yes"` still draws a type finding.

## 4. Documents

- § Errors `validate` reports: `E-DATA-MEASUREMENTS-INVALID` and `-COLLAPSE-TYPE` rows now carry the
  dual-listing clause, and the `-COLLAPSE-TYPE` row names **both** run-time surfaces (roster
  resolution *and* step finalize) and no longer calls the coercion "future".
- § Errors core raises: **one** new row for the pair — a reader meeting either code at run time is
  meeting the same block from the same two surfaces, and two rows would repeat the whole premise.
- § Errors `validate` reports: `E-UNITS-ATTR-MISSING` row extended with the `measurements.by` surface
  and its gate.
- § The one config file: `NOT BUILT` marker dropped from `measurements:`, prose count **eleven → ten**
  (re-counted: `sweep.groups`, `assign`, `cluster_by`, `weight_by`, `holdout`, the resolver form,
  non-`within` allocation, `fold.stratify_by`, `resample`, `null_test`).
- § What isn't a repeat: states that `technical_n` sits beside each metric's `n` and appears only
  where the input carried replicates.
- § The one config file also states, in prose, that `measurements` is the one *built* block shown as
  a commented `null` rather than expanded, because `init` materializes it as `null` and a run
  declares it only when its input carries replicates. (The first cut of that sentence justified it
  with "this fence is what `init` writes", which is **false** — the same paragraph says the fence is
  "a wider thing than the literal output of `init`", and `materialize.py` writes different text and
  no `NOT BUILT` markers. Replaced with the true reason.) It also states that `by` and `collapse` are named there and nowhere else in the section, and that
  `cluster_by`/`weight_by`/`holdout` inherit that treatment when their slices land. This is the
  `CLAUDE.md` "Config completeness"/"Schema fields in prose" question the newly-typed sub-fields
  raise; the alternative (expanding the block in the fence) would have shown a config `init` does not
  write. The `collapse` comment now carries its full enum, per the "Enum comments" rule.
- `spec-defects.md`: two entries closed (marked RESOLVED with what was done), two new ones filed.

Grep scope narrowed deliberately: `E-DATA-MEASUREMENTS-UNSUPPORTED` appears nowhere in the four
documents, `CLAUDE.md`, or `docs/feasibility-*.md` (control: `E-DATA-HOLDOUT-UNSUPPORTED` still hits
`reference.md` once). It **does** remain in `docs/superpowers/H3-SCOPING.md` and the plan file, which
are planning history — `CLAUDE.md`'s mechanical pass scopes the grep to the four documents, this
file, and feasibility analyses, and deleting the string from a scoping record would falsify it.

Mechanical pass over every section touched: links/anchors resolve, no duplicate anchors, table rows
are 2 columns (3 pipes) each, no trailing whitespace, tabs, or invisible unicode.

## Mutation testing (apply → named test FAILs → revert → PASSes, `__pycache__` deleted between)

| Mutation | Test that failed |
|---|---|
| `by` check body → `if False` | `test_a_measurements_by_declaring_nothing_is_refused_when_rows_were_collapsed` |
| drop the `technical_n["max"] > 1` gate in `validate` | `test_a_by_no_input_column_carries_is_accepted_when_nothing_was_collapsed` |
| drop `beside_n` from `summarize_step`'s derived loop | `test_technical_n_reaches_run_yaml_beside_every_metrics_n` |
| drop `beside_n` from `summarize_step`'s column loop | same test |
| drop the `max > 1` gate in `cli` | `test_no_all_ones_technical_n_when_the_input_merged_nothing` |
| leaves-before-containers in `_check_unknown_keys` | `test_a_typo_inside_the_measurements_block_is_now_reported` |

Reverts verified by re-running the test, never by `git status`.

## A correction the next task needs

**The brief's premise that both `measurements` codes are raised from both surfaces is false**, and
task 9's author should not inherit it. What actually raises what:

| Surface | Codes it raises |
|---|---|
| `units.resolve_units` (input path) | `E-DATA-MEASUREMENTS-INVALID` (from `_measurement_axis`), `E-UNITS-COLLAPSE-RULE`, `E-DATA-MEASUREMENTS-COLLAPSE-TYPE` |
| `StepIO.finalize` (step path) | `E-UNITS-COLLAPSE-RULE`, `E-DATA-MEASUREMENTS-COLLAPSE-TYPE` — **never** `-INVALID`, since `_collapse_measurements` reads only `collapse` |

The registry rows I wrote say exactly this rather than what the brief ordered.

## Concerns / brief defects found

1. **The brief prescribed the wrong reference set for the `by` check** (`attributes` rather than the
   source's columns), which would have refused two normative documents' own fence. Fixed in round 1;
   the missing test for the fence shape is what let it through, and that test now exists.
2. **The brief's step-1 test was inert.** `write_config`'s `index.csv` holds only `patient_id`, so
   the prescribed config fails at `E-UNITS-ATTR-MISSING` during roster resolution and the assertion
   passes without ever reaching the honoured path. Rewritten over a real two-rows-per-patient table
   with asymmetric values (10/20/60 → mean 30, median 20, first 10, sum 90).
3. **`materialize.py` had no `NOT BUILT` to remove.** That comment never carried the marker for
   `measurements` (nor for `cluster_by`, `weight_by`, `holdout`) — confirmed against the commit that
   introduced the line. Step 3's `materialize.py` clause was a no-op; the file is untouched.
4. **Two stale pins removed** from `tests/test_validate.py` parametrizations
   (`test_each_unimplemented_units_subfield_is_refused_on_its_own`,
   `test_every_unsupported_message_defers_rather_than_scolds`).
5. **`run_a_project` gained two optional parameters** (`roster_csv`, `units_overrides`) so an
   end-to-end test can declare a measured roster; existing callers are unaffected.
6. **Typing the children makes some faults report twice.** `measurements: {by: 5, …}` now draws
   `E-CONFIG-TYPE` at `data.units.measurements.by` *plus* two `E-DATA-MEASUREMENTS-INVALID` — one
   raised by `resolve_units` inside `_check_units` (path `data.units`) and one from
   `_check_measurements` (path `…measurements.by`). The doubled `-INVALID` pre-dates this task
   (task 3's raise surface); the `E-CONFIG-TYPE` is new and matches the `from: 5` precedent
   (`E-CONFIG-TYPE` + `E-UNITS-SOURCE-MISSING`). No document sentence is falsified — the `-INVALID`
   row says "reported alone" only for the empty-mapping case — but a dedupe of the same code at two
   paths, like `_units_declaration`'s `already_reported` guard, would read better and is left alone
   here as out of scope.
7. **Downstream consumers checked**: `run_record.assemble_run_yaml` copies `aggregated` blocks
   verbatim and whitelists no metric-block keys, and `RESERVED_METRIC_NAMES` guards the *step*
   level, one level above `technical_n`. Nothing drops it.
8. **Open, deferred with reasons in `spec-defects.md`:** `by`'s two meanings across the two collapse
   paths (a typo'd `by` in a step-measured config is still reported by nothing — it costs nothing
   today because nothing reads it), and the step path's measurement counts reaching `run.yaml`
   through no field at all.
