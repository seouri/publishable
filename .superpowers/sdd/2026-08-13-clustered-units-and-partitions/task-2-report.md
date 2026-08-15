# Task 2 report: Cluster resolution, one authority

**Status:** complete. Two commits on `h3b-clustered-units-and-partitions`, atop `6a3c3a9`:

- `df3a4f2` — `units.clusters_of`/`cluster_count`, `validate._check_cluster_by` (the *Cluster
  attribute exists* row and the glob cross-check), `W-DATA-CLUSTER-UNDECLARED`'s emit site, one
  new § Errors row, 21 tests.
- `46c994f` — two review findings: the exclusion walk scoped off `parameters`, and the envelope
  deferral pinned by a test that can tell a correct deferral from a dropped finding.

`uv run pytest` → **1248 passed, 2 xfailed** (was 1226/2; 22 new). `ruff check` and `mypy` green.
`ruff format` was not run.

## The brief defect, and what I did about it

**Step 3 says to raise "the code the *Cluster attribute exists* row implies, taken from your task 1
row rather than invented." No such code exists.** § Validation is a two-column table (check name,
example); it carries no codes, and task 1's report states step 1 added the row and nothing else — no
§ Errors entry. So the row implies a code by *shape* (`E-DATA-WEIGHT-UNKNOWN`'s sibling) and names
none. Verified: `grep -rn "E-DATA-CLUSTER" docs/` before this task returned only the row text and
`W-DATA-CLUSTER-UNDECLARED`; the only cluster `E-` in `src/` was `E-DATA-CLUSTER-UNSUPPORTED`.

I minted **`E-DATA-CLUSTER-UNKNOWN`** and added its § Errors validate reports row, in the table's
alphabetical position (immediately before `E-DATA-IN-REPO`; the table is alphabetical by code, and
`-UNSUPPORTED` codes are deliberately absent from it per § Errors' own note). Documents lead code, so
the row landed with the code rather than after it.

Rejected reusing `E-UNITS-ATTR-MISSING`: row 424 frames that as "the `measurements.by` half", i.e.
the *source-column* code, and borrowing it for a declared-attribute namer would re-create the exact
asymmetry the brief warns about.

**One code on both surfaces**, `validate`'s declaration check and `clusters_of`'s raise for a unit
carrying no value — the precedent being `E-DATA-WEIGHT-INVALID`'s own row ("Raised at run time too,
under the same code … the same single-authority reason"). Single authority applied to the identifier,
not only to the function.

**The validate-side check is scope the brief undercounts.** `H3b-SCOPING.md` § Task order line 2
assigns task 2 "the attribute-existence check and the glob cross-check", and task 1's concern 5 says
task 2 "discharges the *Cluster attribute exists* row". The brief's "two deliverables" omits it. It
is one row's worth of code and the row is already published, so I built it rather than leaving a
second documented check with no implementation beside the warning I was sent to fix.

## The declared-attribute question — verified, not assumed

**The reference set is `data.units.attributes`, the `weight_by` side.** Three independent
confirmations:

1. Task 1's row: "`data.units.cluster_by` names `site`, **which is not a unit attribute**" — the
   weight row's phrasing verbatim in shape. The `measurements.by` framing is different in the same
   table ("a `reads.csv` with no `read_id` column").
2. `design-principles.md` § Core vs. plugin lists `cluster_by` among declarations that "all name
   attributes".
3. § Clustered units' own YAML: `attributes: [animal_id], cluster_by: animal_id` — declared **and**
   named, which is only coherent if `attributes` is the set.

That is also what makes `clusters_of` implementable at all: `_from_table` populates
`Unit.attributes` from `data.units.attributes` and nothing else, so a name outside that list has not
survived resolution and there would be nothing per-unit to read. The glob cross-check falls out for
free — `_from_glob` refuses every declared attribute, so a `cluster_by` under a glob always reports.

## What landed

### A — cluster resolution (`src/publishable/units.py`)

`clusters_of(roster, cluster_by) -> dict[str, str]` and `cluster_count(roster, cluster_by) -> int`.

- Insertion order **is** roster order, so task 4 derives its ordered cluster list from this mapping
  instead of walking the roster a second time.
- Values stringified: a table yields `str` for every column, a hand-built roster need not, and a
  cluster id is a label rather than a quantity.
- A unit carrying no value raises `ContractError`/`E-DATA-CLUSTER-UNKNOWN` rather than becoming a
  singleton cluster — an invented singleton makes that unit its own inferential draw.
- `cluster_count` is `len(set(clusters_of(...).values()))`, not a second walk: the count is what
  bounds `k`, and a count disagreeing with the membership is a `k` the partitioner cannot satisfy.

### B — `W-DATA-CLUSTER-UNDECLARED`'s emit site (`validate._warn_undeclared_cluster`)

The row's four predicates verbatim, in order: every unit carries a value; not all values numeric
(through `units.is_measurement_numeric`); more than two distinct; at least one value held by more
than one unit. Plus `_accounted_attribute_names`' exclusions — `sweep.groups[].by`, an `assign` axis
key and its `from`, **any** `stratify_by`, and `statistics.null_test.shuffle`. `report_by` is
deliberately not excluded. First candidate in sorted order, one warning.

Two implementation decisions the row leaves open, both stated in the docstring:

- **An empty cell is "carries no value"**, not "carries the empty label". `is_measurement_numeric("")`
  is `False` and blanks repeat, so a sparse column would otherwise satisfy clauses 2 and 4 on its
  blanks alone. Test: `test_no_cluster_warning_for_a_column_with_a_blank_cell`.
- **`stratify_by` is collected by walking for the key**, not from an enumerated list of the blocks
  that carry one. The row says *any* `stratify_by`, and three of those blocks (`assign`,
  `statistics.resample`, a `fold` level's) are unbuilt or in flux, so an enumeration would quietly
  stop matching the row. The walk covers `data`, `sweep`, `replication` and `statistics` — **not
  `parameters`**, which is the template's namespace: a template may declare a parameter of any name,
  and one called `stratify_by` silencing a real cluster column would be invisible to a reader.
  `test_a_parameter_named_stratify_by_does_not_silence_the_cluster_warning` fails under the
  whole-document walk, verified by mutation.

**No numeric threshold, so no `limits` key** — the row is predicate-only and every clause proved
implementable as written. Nothing in the row needed changing.

**The warning does not call `clusters_of`, deliberately**, and the docstring says so at length. It
asks "does this column look like a cluster", not "which cluster is this unit in" — a candidate scan,
not a membership decision. Reading it as a second notion of membership is the misreading to avoid:
nothing in it decides what any cluster contains, and `clusters_of` raises on precisely the
missing-value case that is clause 1's ordinary skip here.

### The one document edit

`docs/reference.md` § Errors validate reports, one row for `E-DATA-CLUSTER-UNKNOWN`. No other change.

## Verification

**The negative control, which is the test that matters.**
`test_the_worked_examples_own_attributes_do_not_warn` builds cohort-pilot's `[label, age, sex]` over
12 units and asserts silence. Each attribute is silenced by a *different* clause, which is what makes
it a test of the trigger rather than of one clause: `age` by the type clause, `label` and `sex` by
"more than two distinct values". Note `label` is silenced here by the distinct-count clause, **not**
by task 1's `null_test.shuffle` exclusion — the exclusion is unreachable in this build, `null_test`
being refused, so a fixture that relied on it would prove nothing.

**Mutation tests, each deliverable separately**, `__pycache__` deleted between mutation and revert,
every revert verified by re-running the tests rather than by `git status`:

| Mutation | Killed by |
|---|---|
| `clusters_of` returns the unit key as its own cluster | 4 tests in `test_units.py`, including the brief's `cluster_count == 3` |
| Warning's distinct-count clause loosened `<= 2` → `< 2` | `test_the_worked_examples_own_attributes_do_not_warn` — the control fails, so it is the clause doing the work |
| `_check_cluster_by`'s name check made unreachable | 3 tests, including the direct-call one |

The second mutation caught a near-miss of my own: running `pytest -k cluster` reported **16 passed**
because the control's name contains no "cluster". Re-running by its real name showed it failing, as
it must. A `-k` filter that silently excludes the one test that had to fail is exactly the
"probe reports nothing for every input" trap.

**Every check is exercised by a direct call as well as through `validate_config`**, since
`E-DATA-CLUSTER-UNSUPPORTED` is still live and fires beside every `cluster_by` declaration:
`test_the_cluster_name_check_reports_without_a_roster` asserts the finding list is *exactly*
`["E-DATA-CLUSTER-UNKNOWN"]` on a direct call, which no refusal can reach. The warning path cannot be
masked at all — it only runs when `cluster_by` is unset, which is exactly when the refusal is silent.
`test_an_empty_cluster_by_is_reported` additionally asserts `E-DATA-CLUSTER-UNSUPPORTED` is *absent*,
that refusal reading `cluster_by` truthily.

**Totality over the brief's four cases**, all tested: absent (`{}`), null, non-string (returned to
`E-CONFIG-TYPE`, no duplicate finding), and naming an attribute some units lack (the warning skips
the column; `clusters_of` is the surface that raises). `validate` still never raises — no test
produces an escape.

**The `E-CONFIG-TYPE` deferral is verified, not assumed.** `envelope.py`'s `LEAF_TYPES` really does
carry `"data.units.cluster_by": str` (line beside `weight_by`'s), and
`test_a_non_string_cluster_by_is_left_to_the_envelope` now asserts both halves: the check is silent
*and* `E-CONFIG-TYPE` appears in `codes(path)`. The silence-only form of that test could not
distinguish "correctly deferred" from "silently dropped", and the difference goes live the moment
task 11 retires `E-DATA-CLUSTER-UNSUPPORTED`, which fires on a truthy `3` today.

**Nothing core scaffolds can trigger the warning.** `materialize.py`'s `init` block writes
`attributes: []` and `cluster_by: null`, so a generated project has no attribute for the trigger to
read; `demo` is not implemented in this build (`grep -rn "demo" src/publishable/*.py` returns
nothing). The synthetic control above is therefore the whole exposure, not a proxy for a real
artifact that could still fire.

**Mechanical pass.** A throwaway checker over `reference.md`, `design-principles.md`,
`experimental-designs.md`, `feasibility-llm-growth-studies.md`, `README.md`, `CLAUDE.md`: anchors,
duplicate anchors, relative links, table widths, empty rows, trailing whitespace, tabs, invisible
unicode, en dash in headings, fences skipped. It reports 4 findings — **all pre-existing**, proved by
running the same checker over `git show HEAD:docs/reference.md`, which reports the same 3 at the same
lines minus my one-line offset (they are rows containing `|` inside code spans). Every check proved
able to fail *on the new row*: bad anchor → `415: unresolved anchor`, pipe removed →
`415: table row has 1 cells`, trailing space → `415: trailing whitespace`, tab → `415: tab`,
U+200B → `415: invisible unicode U+200B`.

**Cross-document pass.** No config field added, so config completeness is untouched and no `limits`
key was needed. No enum gained a value. Every field the new row names (`data.units.cluster_by`,
`data.units.attributes`, `measurements.by`) exists in § The one config file. `cluster_by` stays a
declaration everywhere. The worked example's values, intervals, counts and hash prefixes are
unchanged — and the new warning is silent on its roster, which is the control above. `NOT BUILT` and
`-UNSUPPORTED` counts unchanged: `E-DATA-CLUSTER-UNSUPPORTED` is untouched, per the brief.
`partition_units` is untouched.

## Concerns

1. **`E-DATA-CLUSTER-UNKNOWN` has no row in § Errors *at run time*, only in § Errors validate
   reports** — where its text does state the run-time raise. That is honest today: nothing in a run
   calls `clusters_of` yet. Once task 4 or task 11 wires it, the run-time table wants the row
   `E-DATA-WEIGHT-INVALID` has at § Errors at run time, and whichever task makes it reachable owes
   it. Flagged rather than pre-written.
2. **The exclusion list is mostly unreachable in this build.** `sweep.groups`, `assign`,
   `statistics.null_test` and `statistics.resample` are all refused, and a `fold` level's
   `stratify_by` is refused by `_fold_k` until task 7. The exclusions are implemented and two are
   tested through `validate_config` (the refusal is a finding *beside* the silence, not a substitute
   for it), but they are silencing columns in configs that cannot run. If a later task changes where
   `stratify_by` may appear, `_accounted_attribute_names`' document walk follows it automatically —
   that is why it is a walk.
3. **Task 1's `> 2 distinct` clause is what keeps the warning off cohort-pilot, not the
   `null_test.shuffle` exclusion**, and the row's own worked reasoning cites both for `label`. If a
   later slice ever loosened the distinct-count clause, the control would start failing and the
   exclusion would not save it while `null_test` stays refused. Recorded so the clause is not read as
   redundant with the exclusion.
4. **The brief's step 3 is defective as written** (no such code existed) — item 1 above. The scoping
   document's task-2 line is the accurate one; the brief's "two deliverables" framing is what dropped
   the attribute-existence check.
5. `docs/superpowers/spec-defects.md` is gitignored, so nothing was recorded there; no spec defect
   was found that the row itself did not already cover.
