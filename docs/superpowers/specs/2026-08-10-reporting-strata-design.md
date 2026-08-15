# Reporting strata (S4d) design

**Goal:** a run reports each metric over the subgroups a config names, without adding an
execution, a condition, or a place in the correction family.

**Why it is small:** `report_by` is `stats.summarize_step` applied to a subset of a table that
already exists. No new interval construction, no new statistics, and nothing a plugin sees.

## Scope

| In | Out (S4e) |
|---|---|
| `statistics.report_by`, retiring `E-STATS-REPORTBY-UNSUPPORTED` | The `aggregate` table carrying declared unit attributes |
| Per-stratum `value`, `basis`, `n` and `ci95` under `aggregated.<step>.by` | Non-numeric recorded columns |
| `limits.min_reported_n` per stratum, at validate **and** at run | A repeat-collapse rule for string columns |
| A `report_by` shape guard in `_check_shape`'s nested pass | |

The cut matters and is not the one the S4c design assumed. **`report_by` does not depend on the
table-contents work.** Stratifying is core splitting the per-unit table by an attribute value it
reads from the roster; it does not require `aggregate` to *see* attributes. The two were listed
together in S4c's Out column because both were blocked, not because either needs the other.
Keeping them apart keeps a published-interface change — what every plugin's `aggregate` receives —
out of a slice that is otherwise core-only.

## Architecture

**One new pure module, `src/publishable/strata.py`** — no filesystem, no runtime import of
`config`, `artifacts`, `runner` or `cli`, matching `contrasts.py`, `correction.py` and `stats.py`.

```
levels_for(roster: UnitList, attribute: str) -> dict[str, set[str]]
```

Level value (as a string) to the set of unit keys holding it. Values compare as strings for the
reason `contrasts.units_matching` already does: a config's YAML gives `1` as an int while the same
attribute read from a table is `"1"`, and comparing them raw matches nothing.

`cli.py` then does, per condition, per recording step, per declared attribute, per level: filter
`collapsed` to that level's keys, take `runner.attrition` over that level's units, and call the
**same** `stats.summarize_step` the parent block already uses — same `t` and percentile
constructions, same derived-metric resample, same seed. A stratum is not a new kind of number; it
is the existing number over fewer rows.

Three consequences, each a property of strata not being conditions:

- **No executions are added.** `dry-run`'s count is unchanged, which is the documented promise.
- **Strata never join the correction family.** `correction.Member`s are built only from
  comparisons, so the exclusion is structural — a stratum cannot enter the family by being
  forgotten about, only by someone writing new code to put it there.
- **`repeat_spread` is omitted** from a stratum block. The documented example carries `value`,
  `basis`, `n` and `ci95` and nothing else.

## The record shape, and the document defect it exposes

`reference.md` § Reporting strata shows:

```yaml
aggregated:
  step03_analyze:
    r: {value: 0.607, basis: units, n: {...}, ci95: [...]}
    by:
      sex:
        f: {value: 0.591, basis: units, n: {...}, ci95: [...]}
```

`by` is a sibling of `r`, and `by.sex.f` is a **metric entry**. That is self-consistent only when
the step reports exactly one metric: with two, the second has nowhere to go, because the metric
name appears nowhere under `by`. The only shape that generalizes is one level deeper —

```yaml
    by:
      sex:
        f:
          r: {value: 0.591, basis: units, n: {...}, ci95: [...]}
```

— mirroring `aggregated.<step>`, which is itself a metric block. **`reference.md`'s example gains
the metric level before any code is written**, per CLAUDE.md's rule that the document leads. The
edit is inside a fenced block, so the mechanical pass will not see it; the cross-document pass
applies, and this example belongs to the shared worked example (`step03_analyze`, metric `r`,
n = 240/228/12), so its numbers must not move — only the nesting.

### Three things the example does not settle

**Where the block lives.** `results.conditions[i].aggregated.<step>.by.<attribute>.<level>.<metric>`
— strata are per condition, because `aggregated` is, and core never pools across conditions.

**An empty or thin level still gets a block.** A level whose units all failed reports its `n` with
`completed: 0` and a `null` `ci95`, rather than being dropped. That the subgroup produced nothing
is the finding, and it is the same rule `reference.md` states for a contrast whose paired
intersection is empty: "reported as such rather than as a delta of zero." What is absent, not
empty, is the `by` key itself when `report_by` is undeclared — the house rule the `vs_baseline`
and `contrasts` blocks already follow.

**A stratum resamples on the run's own seed**, the one `stats.resample_seed(digest)` derives, with
no per-level derivation. Conditions already share that seed and differ only by their tables; a
level differs the same way, since it draws from its own key set. A per-level seed would be a new
derived quantity to document and reproduce for no gain.

**Two attributes are two marginal splits, not their cross.** `report_by: [sex, site]` adds a
`by.sex` block and a `by.site` block, each over the whole table. It does not produce an
`f × site_03` cell. `reference.md` is explicit that the cartesian product is the thing this
section exists to avoid, and that a cross you want to *execute* is a `groups` axis while a cross
you want to *test* is a `within` contrast.

## The two thin-stratum warnings

`reference.md` says `validate` "warns when a level would hold fewer units than
`limits.min_reported_n` — before the run rather than at disclosure." That is implementable —
`validate_config` already resolves the roster — but it is not sufficient on its own, and the gap
is worth stating plainly: validate counts **resolved** units, so a level holding 40 resolved units
of which 8 complete is thin in the published record with nothing having warned. Attrition is
exactly what validate cannot see.

So both, under separate identifiers:

| Identifier | When | Counts |
|---|---|---|
| `W-STATS-REPORTBY-THIN` | `validate` | Resolved units per level, from the roster |
| `W-STATS-STRATUM-THIN` | `run` | Completed units per level, per condition per step |

The run-time one is not in any document. It gets a `docs/superpowers/spec-defects.md` entry naming
the sentence it extends and why the validate-time warning alone leaves a disclosure gap — the same
shape `W-STATS-CONTRAST-THIN` already has for a `within` contrast's `n_paired`, which warns at run
time for precisely this reason.

`validate` also refuses an attribute not in `data.units.attributes`. `reference.md` states that
rule and names no identifier, so it needs a `spec-defects.md` entry alongside — the pattern
`E-STATS-CONTRAST-WITHIN` and `E-STATS-CONTRAST-SAME-SIDES` already follow.

**A shape guard is not optional here.** `report_by` is a nested config value that new code will
read, and S4c shipped two separate crashes of exactly that kind — a scalar `statistics.contrasts`
reaching `_check_sweep`, and an unhashable contrast `id` reaching a set. `report_by` goes into
`_check_shape`'s nested pass under `E-CONFIG-SHAPE`, refused once upstream, and every reader still
guards what it reads. `validate.py` collecting findings and never raising is a hard constraint.

## Cost, stated rather than capped

Each level's derived metric gets its own 2000-draw resample, so `report_by: [sex, site]` over
seven levels multiplies derived-metric resampling by seven per condition per recording step. No
executions are added, so `dry-run`'s count and the metered-work estimate are unchanged — but
wall-clock is not. This is stated so nobody is surprised, and deliberately **not** capped: a limit
nobody asked for is a feature, and `limits` gains no field here.

## Testing

`strata.levels_for` is pure and unit-testable. Everything else is end to end through
`main(["run", ...])`, which is where every defect in the last two slices actually hid.

### Mutations each test must kill

Named here rather than discovered in review. Fifteen tests that passed against wrong
implementations were found in S4c; every one was caught by running the mutation, not by reasoning
about it.

| Mutation | Caught by |
|---|---|
| Stratify over all units instead of the level's keys | every level's value equalling the parent's |
| Drop the `str()` coercion on attribute values | a YAML-int attribute matching no unit |
| Compute the cross of two attributes instead of two marginals | `report_by: [sex, site]` producing an `f × site_03` cell |
| Take the parent's `n` instead of the stratum's own attrition | a level's `n` exceeding the level's size |
| Build `Member`s from strata | `family_size` growing when `report_by` is added |
| Nest `by` inside a metric entry | the record-shape assertion |
| Warn `W-STATS-STRATUM-THIN` on resolved rather than completed counts | a level that resolves 40 and completes 8 |

The fourth is the S4b Critical's exact shape — a number reported beside a denominator computed
over a different set. The fifth is the one that would silently over-correct every real comparison
in the run, since a larger family means a smaller α.

## Risks

Each has a precedent in this repository.

- **A number and its denominator from different sets.** The S4b Critical. Here it is a stratum's
  `n` or `ci95` computed over the parent's units. Prevented by taking one filtered key set and
  deriving both the counts and the table from it.
- **`validate` raising instead of collecting.** S4c shipped two of these. Hence the shape guard,
  and hence every new reader guarding what it reads even behind that guard.
- **A silent no-op.** `report_by` must never validate clean and produce no `by` block. The
  end-to-end tests assert the block's contents, not the absence of a crash.
- **Over-correction by accident.** Strata entering the correction family would tighten every
  interval in the run. Structural exclusion plus a test that adds `report_by` and asserts
  `family_size` is unmoved.

## Task sequence

Seven tasks, each landing green.

1. `reference.md`: add the metric level to the § Reporting strata example. Document leads.
2. `strata.py`: `levels_for`, pure, with the string coercion.
3. `validate.py`: retire `E-STATS-REPORTBY-UNSUPPORTED`, refuse an undeclared attribute, add the
   `_check_shape` nested guard.
4. `validate.py`: `W-STATS-REPORTBY-THIN` over resolved counts.
5. `cli.py`: build `aggregated.<step>.by.<attribute>.<level>.<metric>` from `summarize_step`.
6. `run`: `W-STATS-STRATUM-THIN` over completed counts, plus the `spec-defects.md` entries for it
   and for the undeclared-attribute refusal.
7. The end-to-end acceptance test: marginal-not-cross, per-level `n` and `ci95`, `family_size`
   unmoved, both warnings, and a run with no `report_by` unchanged.
