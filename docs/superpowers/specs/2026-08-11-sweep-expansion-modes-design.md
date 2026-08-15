# H2 Sweep expansion modes design

**Goal:** `expand()` becomes a genuine product over axis-shaped modes, `paired`, `sample` and
`ablate` execute, and a baseline expands over the axes it does not fix — which is the design
`reference.md` tells a user to prefer and this build refuses.

**Why now:** H1 closed the identifier gap and the config envelope, so every check H2 adds has a
registry to land in and a type envelope to trust. H2 is ordered ahead of H4 because contrasts and
correction families count comparisons, and per-cell baselines change how many there are.

## A correction this slice starts from

During H1's scoping a subagent reported that `E-SWEEP-BASELINE-PARTIAL` refuses a design
§ Expansion modes recommends, quoting "Prefer the second row whenever the levels are peers". The
controller grepped for that sentence case-sensitively, found nothing, recorded it in H1's spec as
**fabricated**, and told H1's tasks not to carry it forward.

**The sentence is real.** It is at `reference.md` § Expansion modes, sentence-initial and therefore
capitalised, which is why a lowercase grep could not match it. The absence claim was established by
a check that could not succeed — the exact defect H1 spent twelve tasks catching in others. H1's
spec now carries the correction; this slice inherits the finding as its central one.

## What the measurement found

`src/publishable/sweep.py` is 269 lines. `expand()` is **not** a product over axes — it prepends a
baseline row and runs `itertools.product` over `grid` alone. `label_for(values, grid, is_baseline)`
takes `grid` by signature and returns a flat `"baseline"` for the reference condition. Nothing
resolves units per group level.

§ Expansion modes is 161 lines specifying six modes. Four are refused wholesale today:
`E-SWEEP-{ABLATE,PAIRED,SAMPLE,GROUPS}-UNSUPPORTED`. Six § Validation checks are blocked behind
them, measured by H1's scoping.

So this is a restructure of `expand()`, not four additions to it.

## Scope

| In | Deliberately not here |
|---|---|
| `expand()` as a product over axis-shaped modes | **`groups`** — see below |
| `paired`, `sample`, `ablate`, retiring three `-UNSUPPORTED` codes | Anything `allocation`/`assign`/`by_attribute` (H3 Units) |
| Per-cell baseline expansion over unfixed axes; retiring `E-SWEEP-BASELINE-PARTIAL` | The two blocked checks that need a group axis |
| Four of the six blocked § Validation checks | `report`'s rendering of multi-baseline results (H8) |
| Re-reading `W-SWEEP-BASELINE-CONFOUNDED`'s row, whose remedy becomes reachable | |

**`groups` stays refused, and that is the slice's most consequential decision.** § Expansion modes
says a group level *is a set of units*, assigned by `allocation: between` with `assign.method`, or
read from a column by `by_attribute`. All three live behind `E-DATA-*-UNSUPPORTED` and belong to
H3 Units; nothing in `units.py` resolves units per level. A `groups` axis that expanded conditions
while handing each the same roster would run to completion and report two identical measurements as
two arms — precisely what `experimental-designs.md` § Mistakes core prevents exists to make
structurally impossible. **Building half of it would introduce that failure, so H2 builds none of
it.** `E-SWEEP-GROUPS-UNSUPPORTED` retires in H3, beside the assignment that makes a level real.

The cost is that `ablate × groups` — the composition § Expansion modes illustrates most fully, and
where per-cell baselines first appear — cannot be tested end to end in this slice. Per-cell
expansion is specified over "group axes and parameter axes alike", so it is fully testable over
parameter axes alone; only its best-known illustration waits.

## The composition matrix is the specification

The individual modes are small. The rules about how they combine are the slice:

| Rule | Source |
|---|---|
| The condition set is the **product** of every axis-shaped mode present — `grid`, `paired`, `sample`, `groups` | § Expansion modes |
| `ablate` does **not** multiply. It emits `n` conditions, each one change from the baseline, and **reads** the baseline rather than re-emitting it | § Expansion modes |
| `ablate` therefore **requires** `sweep.baseline` | § Expansion modes, checked by `validate` |
| `ablate ×` any **parameter** mode is **rejected** — "vary one thing at a time" crossed with a second parameter axis is no longer one thing at a time | § Expansion modes |
| `ablate × groups` is **permitted**, giving `(1 + n)` per level, because `groups` varies no parameter | § Expansion modes — **untestable here, groups is refused** |
| `sweep.baseline` may not fix a group level while `ablate` is declared | § Expansion modes — **H3** |
| A baseline fixing **every** axis gives one condition `00`; fixing **some** gives **one per cell of the unfixed axes** | § Expansion modes' two-row table |
| Baseline conditions are references, not comparisons — six conditions under two per-arm baselines are **four** comparisons in the correction family, not five | § Expansion modes |

That last row is the one with reach outside this slice: it changes `family_size`, which changes
corrected intervals. H4 owns the correction family, but H2 is what makes multi-baseline runs
possible, so **H2 must not leave the comparison count to H4 to discover.**

## Architecture

**`expand()` becomes two phases.** First build the axis list — one entry per axis-shaped mode
present, each a list of `{path: value}` cells — then take the product. `grid` contributes one axis
per key; `paired` contributes one axis whose cells are whole dicts; `sample` contributes one axis
of realized draws. Second, apply the non-multiplying modes: `ablate` reads the baseline and emits
its rows; the baseline expands over unfixed axes. Today's behaviour is the degenerate case where
the axis list has one member and the baseline fixes it, which is why the existing suite is a valid
oracle for phase one.

**`label_for` loses its `grid` parameter.** A label is built from the condition's own `values`
against the set of swept paths, whichever mode contributed them. `_keys_for` already shortens paths
to their last component and disambiguates collisions; it needs the union of swept paths rather than
`grid`'s keys. `condition_dir_name` does not change — the `<nn>_<label>` format is the single
source of truth `runner` and `artifacts` both nest through, and it stays that way.

**A baseline condition's label gains its cell.** One baseline stays `baseline`; per-cell baselines
are `<cell>__baseline`, as § Expansion modes shows with `00_cohort=derivation__baseline`. This is
the piece with artifact-path blast radius, and it is why per-cell expansion lands last.

**`sample` records what it drew.** § Expansion modes requires `sweep.yaml` to carry both the seed
and the fully realized condition list, so a reader never re-derives the design and `reproduce`
regenerates it. The seed is `auto` — derived from the design digest — so sampling is deterministic
given the config, and `sweep_document` already exists to write the record.

## Decisions

| # | Decision | Ruling | Grounds |
|---|---|---|---|
| 1 | `groups` in H2 | **Refused; retires in H3** | *Settled by the user.* A group level is a set of units, and the assignment that makes it one is H3's. Half of it is worse than none |
| 2 | The stale charter line | **Amended before the slice began** | "Wiring `check_swept_value` into `validate`'s call path" was already done; H1's scoping confirmed it fires as `E-SWEEP-VALUE-UNNAMEABLE`. The row now names the six blocked checks instead |
| 3 | `E-SWEEP-BASELINE-PARTIAL` | **Retires with per-cell expansion** | Its own message concedes the design is "specified but not implemented in this build". It is a placeholder, not a rule |
| 4 | `W-SWEEP-BASELINE-CONFOUNDED`'s remedy | **Re-read in this slice** | H1's review ruled "do not touch row 271" explicitly on the grounds that H2 would make the remedy expressible. H2 is that slice; leaving it would strand the ruling |
| 5 | Where the product lives | `sweep.py`, which stays pure | It already is: no filesystem, no `config`/`artifacts`/`cli` imports. The restructure must not change that |

## Risks

- **A composition rule stated more generally than the code enforces.** H1's dominant defect — nine
  occurrences — was a claim true only under an unstated condition, and every one lived in prose
  summarising rows rather than in the rows. H2's cousin is a docstring or a registry row describing
  how modes compose when the product loop enforces something narrower. **Every sentence about
  composition is checked against the loop, not against the mode being added.**
- **A half-built `groups`.** Decision 1 is the guard; the test is that `E-SWEEP-GROUPS-UNSUPPORTED`
  still fires at the end of the slice.
- **Per-cell labels reaching artifact paths.** Labels are directory names. A per-cell baseline
  changes a label that `runner.step_dir_for` and `artifacts.StepIO.read_condition` both build from.
  The existing tests over `condition_dir_name` are the oracle, and they must not be edited to pass.
- **The comparison count.** Baselines are references, not comparisons. Getting this wrong changes
  `family_size` and every corrected interval in a multi-baseline run.
- **The worked example.** `cohort-pilot`'s baseline fixes `analysis.method`, the only axis it
  sweeps, so it stays in the one-baseline row and its pinned labels do not move. **Verified before
  designing; re-verified at the end.**

## Task sequence

Four groups, ordered by what the next one needs.

**A — the product restructure.** `expand()` in two phases with `grid` as the only axis; `label_for`
loses `grid`. No new modes, no behaviour change, existing suite green untouched.

**B — `paired` and `sample`.** Two parameter axes joining the product. `sample`'s realized draws and
seed recorded in `sweep.yaml`. Retires two `-UNSUPPORTED` codes; lands the "sample ranges" check.

**C — `ablate`.** The non-multiplying mode, plus the three composition checks that are about what it
may combine with: ablation targets, ablation needs a baseline, ablation doesn't compose with a
parameter axis. Retires one `-UNSUPPORTED` code.

**D — per-cell baseline expansion.** The baseline expands over unfixed axes; labels gain their cell;
`E-SWEEP-BASELINE-PARTIAL` retires; `W-SWEEP-BASELINE-CONFOUNDED`'s row is re-read; the comparison
count is pinned. Last, because it is the only piece that moves artifact paths.
