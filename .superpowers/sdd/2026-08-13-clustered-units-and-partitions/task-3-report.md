# Task 3 report: A cluster — and a weight — must not vary within a unit's measurement rows

**Status:** complete. Two commits on `h3b-clustered-units-and-partitions`, atop `46c994f`:

- `e63dc01` — `collapse_measurements`' `constant` check, `CONSTANT_COLUMN_RULES`, the
  `resolve_units` wiring for both declarations, five `reference.md` edits, 18 tests.
- `7f0ba8f` — review follow-ups: the absent-from-every-row totality test, and the two-sided wiring
  test made to fire the weight raise through `resolve_units` as well as the cluster one.

`uv run pytest` → **1267 passed, 2 xfailed** (was 1248/2; 19 new). `ruff check` and `mypy` green.
`ruff format` was not run.

## The brief defect, and what I did about it

**Step 3's signature contradicts step 3's own "two codes, not one."** `constant: tuple[str, ...]`
carries column names and nothing else, so `collapse_measurements` receiving `("site",)` cannot know
whether `site` is the cluster or the weight, and therefore cannot choose between
`E-DATA-CLUSTER-VARIES` and `E-DATA-WEIGHT-VARIES`. The step-1 test snippet asserts the cluster code
from exactly that call, so the two halves of the brief cannot both be satisfied.

I made `constant` a **`Mapping[str, str]` keyed by declaration** — `{"cluster_by": "site",
"weight_by": "sampling_weight"}` — and the tests call it that way. Keyed by declaration rather than
by column for two reasons: it needs no precedence rule for a config naming one column in both places
(the column-keyed direction has to pick a winner, and no document says which), and the mapping is a
direct echo of `units_decl`, which is what makes the `resolve_units` wiring obviously correct. Note
what it does *not* buy, so a reviewer does not trace a claim that fails: for a shared column both
directions report `E-DATA-CLUSTER-VARIES` and neither reports the weight half, the first raise ending
resolution either way.

Everything else in the brief held: `resolve_units` needed one argument and no new plumbing, and the
`except ContractError` in `_check_units` carried both codes to `validate` untouched.

## What landed

### The check (`units.collapse_measurements`)

`constant: Mapping[str, str] | None = None`, defaulting to no check at all — the worked example and
every one-row-per-unit roster must collapse exactly as before.

Three placement decisions, each stated at the site and each pinned by a test:

- **Inside the group loop, before the merge loop, and over the members directly** rather than over
  the merge loop's column list. That list excludes `by`, so a `cluster_by` naming the measurement
  axis itself — which varies within every unit by construction — would otherwise be reached by no
  check at all (`test_a_cluster_naming_the_measurement_axis_is_refused`).
- **Ahead of `coerce_for_rule`**, so a varying string cluster column under a blanket `mean` reports
  the leak rather than `E-DATA-MEASUREMENTS-COLLAPSE-TYPE`. Both faults are real; fixing the rule
  name would leave the unit filed under two sites. Ordering pinned by
  `test_the_leakage_code_wins_over_the_collapse_type_code`, so a later reorder cannot flip it
  silently.
- **A column only some members carry is not a disagreement.** The rows that carry it agree, so
  nothing about the collapsed value depends on row order; whether every unit has a value at all is
  the presence question `clusters_of` already raises `E-DATA-CLUSTER-UNKNOWN` for. Present-but-`None`
  beside a real value *is* a disagreement, and is tested separately.

`CONSTANT_COLUMN_RULES` holds each declaration's code and its own explanation, so the two messages
say what actually breaks — leakage versus a mis-sized contribution — rather than sharing wording that
would send the reader to the section that does not describe the damage.

### The wiring (`units.resolve_units`)

Built from `units_decl` at the one call site, filtered by `isinstance(name, str) and name`. That
filter is load-bearing rather than defensive and says so in a comment: a list-valued `cluster_by` is
`E-CONFIG-TYPE`'s finding, and using one as a mapping key is a `TypeError` escaping `validate`, which
never raises — the same class `_check_units`' own `key` guard exists for.
`test_a_non_string_declaration_is_left_to_the_envelope` pins it.

### The document edits (`docs/reference.md`, five)

1. § Weighted samples' rule sentence and 2. § Clustered units' rule sentence. **Both were
counterfactual after this change** — each stated the *outcome* of the unchecked collapse ("become a
single weight of 100 under `sum`", "collapses to `S1`, chosen by the `first` fallback"). Rewritten to
the conditional plus the refusal and its code, per CLAUDE.md's *Prevented mistakes* class: a mistake
now structurally impossible must not be documented as something that happens.
3. and 4. § Errors validate reports, one row each, in the table's alphabetical position
(`-VARIES` after each code's `-UNKNOWN` sibling), each stating the run-time raise — dual-listed as
`E-DATA-MEASUREMENTS-COLLAPSE-TYPE` is.
5. § Errors core raises, one row carrying both codes, adjacent to the two collapse rows; line 892's
precedent is a row carrying two codes for one collapse-time fault.
Plus two § Validation rows, *Cluster is constant within a unit* and *Weight is constant within a
unit*, beside their siblings — the table already carries the idiom in *Shuffle level is unambiguous*
and *Holdout strata survive clustering*.

`experimental-designs.md` § Mistakes core prevents' *A cluster split across train and test* row was
**not** edited: it is still accurate, it describes the partition route, and task 4 rewrites that
route. Editing it now would only create a conflict.

## Verification

**The run-time row is honest, not aspirational.** The `resolve_units` call at `cli.py` line 707 is
inside **`command_run`** (checked by reading the enclosing `def`, not by grepping the line), so both
codes really are raised at run time as well as reported by `validate` — the difference from task 2's
concern 1, where `clusters_of` had no run-time caller yet.

**The cluster half reaches `validate` end to end**, checked before writing the test rather than after:
`_check_unimplemented` is called *after* `_check_units` in `validate_config` and reports without
returning, so `E-DATA-CLUSTER-UNSUPPORTED` fires *beside* the new finding rather than short-circuiting
it. Both halves therefore have `validate_config` tests, not only the weight half the brief named.

**Every check has its own control that must report.** Four positive/negative pairs — cluster and
weight, at the function and through `validate_config` — plus
`test_neither_check_fires_where_measurements_is_undeclared` (the shape the worked example is in) and
`test_no_declaration_leaves_the_collapse_exactly_as_it_was` (the default checks nothing).

**Mutation tests, the two halves separately**, `__pycache__` deleted between each mutation and its
revert, every revert verified by re-running the tests rather than by `git status`:

| Mutation | Killed |
|---|---|
| `resolve_units` builds `constant` from `("weight_by",)` only | the two `validate` cluster tests, plus the two-sided wiring test |
| …from `("cluster_by",)` only | `test_a_weight_varying_within_a_units_rows_is_reported`, plus the two-sided wiring test |
| `CONSTANT_COLUMN_RULES["cluster_by"]` given the weight code | 8 tests, on *code selection* rather than on raising — a different property from the two above |

The first two are the clean pair: apart from the one test that deliberately exercises both
declarations through `resolve_units`, neither killed a test of the other half, which is what makes
them two tests rather than one mutation killing both. Reverts verified by re-running the tests, with
`__pycache__` deleted between each mutation and its revert.

**`validate` still never raises.** `test_validate_reports_rather_than_raising_on_a_varying_cluster`
calls `validate_config` directly and reads the finding off the collector. Totality is tested over the
column being absent from some rows, absent from *every* row (the case that survives only by `any()`'s
laziness over an empty list — rewritten as `len(set(values)) > 1` it would be an `IndexError`, and it
is reachable whenever `cluster_by` names something `attributes` does not declare), present but
`None`, the declaration absent entirely, the declaration non-string, and the declaration naming the
measurement axis.

**Mechanical pass.** A throwaway checker over all six tracked `*.md` — anchors, duplicate anchors,
relative links, table widths, empty rows, trailing whitespace, tabs, invisible unicode, en dash in
headings, fences skipped. It reports only the pre-existing `&`-in-heading class (`#secrets--credentials`
and friends), which is my slugger dropping a character GitHub keeps; nothing on any line I touched.
**Each check was proved able to fail on the new `E-DATA-CLUSTER-VARIES` row itself** — anchor broken →
`418: unresolved anchor`, pipe dropped → `418: table row has 1 cells`, trailing space added →
`418: trailing whitespace` — each reverted and the file re-checked clean, so the silence above is a
result rather than a probe that reports nothing for every input.

**Cross-document pass.** No config field added or renamed, so § The one config file is untouched and
no `run.yaml` example changes. No enum gained a value. Every field the new rows name
(`data.units.cluster_by`, `data.units.weight_by`, `data.units.measurements`) already exists there.
Nothing moved in the worked example: `cohort-pilot` declares neither `measurements` nor `cluster_by`
nor `weight_by`, so no roster it describes can reach either check — pinned by the
undeclared-`measurements` test. Versions untouched. `partition_units` untouched;
`E-DATA-CLUSTER-UNSUPPORTED` untouched.

## Concerns

1. **`artifacts._collapse_measurements` — the step-recorded path — carries no equivalent check, and
   deliberately.** It collapses the rows a step supplied through `io.record(..., measurement=)`, which
   are *recorded columns*, not unit attributes; `cluster_by` and `weight_by` name declared attributes,
   which that path never merges. If a later slice ever lets a step record over a declared attribute,
   the same constancy question arrives there and this check will not be covering it.
2. **The message names one unit, and resolution stops there.** A roster with fifty disagreeing units
   reports the first, because this is a raise inside resolution rather than a `validate` walk that
   could collect them all. That matches `E-UNITS-KEY-DUPLICATE`'s behaviour beside it, but it is a
   worse diagnostic than `E-DATA-WEIGHT-INVALID`'s whole-roster report.
3. **The two `-VARIES` codes fire before `E-DATA-WEIGHT-INVALID` and `E-DATA-CLUSTER-UNKNOWN` can**,
   since a raise inside `resolve_units` returns no roster and the later checks skip. That is the right
   order (the disagreement is the cause) but it means a config with both faults reports one at a time.
4. `docs/superpowers/spec-defects.md` is gitignored, so nothing was recorded there; the only defect
   found was the brief's, recorded above.
