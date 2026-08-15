# H3a Weighted and technical units design

**Goal:** `data.units.weight_by` and `data.units.measurements` execute — a weight changes the
interval it is declared for, and a technical replicate is collapsed before any step sees it —
retiring `E-DATA-WEIGHT-UNSUPPORTED` and `E-DATA-MEASUREMENTS-UNSUPPORTED`.

**Why first among H3's four:** these are the only two pieces of H3 that touch **no partition**.
`weight_by` depends on nothing; `measurements` collapses inside `resolve_units` before uniqueness
is checked. H3b and H3c each rewrite `partition_units` — for clusters, then for cells — and H3a
cannot conflict with either, so it is the one slice that can be built while the shape of the
partitioner is still unsettled.

## A charter this slice starts from correcting

`docs/superpowers/H3-SCOPING.md` measured H3 against the spine's charter line and found four
errors, all now amended into `2026-08-08-implementation-spine-design.md` § H3 decomposes into
four slices. The two that bear on H3a:

- **H3 is not one slice.** Nine refusals, **26** blocked § Validation rows, ≈385 lines of
  `reference.md` across 8 sections, a new run artifact, 4 `W-` identifiers, ≥5 core signature
  changes. H1 was 12 tasks; H2 was 9.
- **The blocked-row count was 25 and its membership was off by three each way.** H3a's share is
  **4** — rows 243, 291, 292, 293 — with row 257 belonging jointly to the resolver, which the
  scoping moved out of H3 and into H7 Plugins on the grounds that `validate`'s own message names
  the missing plugin registry as the reason it cannot execute.

## What the measurement found

**`io.record` has no `measurement=` parameter.** Its signature is
`record(self, unit_key: str, values: dict[str, Any]) -> None` in `artifacts.py`, while
`reference.md` § The importable surface documents `io.record(unit_key, values, measurement=None)`
and § What isn't a repeat describes the collapse it feeds. The document leads and the code lags,
so this is a gap to close rather than a design to choose.

**Nothing in `src/` reads either declaration.** `validate._check_unimplemented` refuses both;
`materialize` writes their `NOT BUILT` comments; `replication` names `measurements` as the route
a `technical` repeat kind is refused toward. `envelope.py` types `data.units.weight_by` as `str`
and `data.units.measurements` as a bare `dict`.

**`stats.t_over_units(values, confidence)` takes a bare sequence** and computes df as
`len(values) − 1`. There is no weighted construction and no `effective` anywhere in `src/`.

**`n` is built in `runner.py` as a four-key dict** — `resolved`, `completed`, `ineligible`,
`failed` — in three places.

**A side finding the scoping recorded, which H3a inherits:** the five-field refusal loop in
`validate.py` is truthiness-gated, so `measurements: {}` and `weight_by: ""` validate clean today
and are read by nothing. Two of the three genuine holes there are H3a's to close, and closing
them is not the same work as un-refusing the declaration — an empty declaration must become a
finding, not silently become a working default.

## Scope

| In | Deliberately not here |
|---|---|
| `data.units.measurements`: both collapse paths, `technical_n`, `measurements.parquet` | `cluster_by` and `fold.stratify_by` (H3b) |
| `data.units.weight_by`: the three checks **and** the weighted interval | `allocation`, `groups`, `assign`, `allocation.json` (H3c) |
| `io.record`'s `measurement=` parameter and the raise when it is undeclared | `holdout` (H3d) |
| `n` gaining `effective`; `weighted_by` in the record | `data.units.from: {resolver:}` — H7, and row 257 with it |
| Closing `measurements`' whole-leaf `envelope.py` block | `statistics.resample.stratify_by` — H4 |
| The two truthiness holes above | Splitting `sweep.AXIS_MODES` — H3c |

**The weighted interval is in scope, and that is the slice's most consequential decision.**
See decision 1.

## Architecture

**One collapse rule, two arrival points, one implementation.** A technical replicate reaches core
either because the input carried several rows sharing a `key`, or because a step called
`io.record(unit.key, values, measurement=read_id)`. `reference.md` § What isn't a repeat is
explicit that keeping the two apart is load-bearing — *without* the `measurement=` argument a
second row for one unit is a resumed retry to be deduplicated under first-write-wins, *with* it a
second measurement to be averaged, and **nothing in the row itself distinguishes them**. The two
paths must therefore call one collapse function, in `units.py`, or "the same rule" becomes two
implementations free to disagree.

**Collapse happens before `n` is counted.** § The unit table is the inference base: technical
replicates cannot reach `n`, because they were gone before `n` was counted. For the input path
that means inside `resolve_units`, before the uniqueness check. For the step path it means at
finalize, before `completed` counts distinct keys.

**`technical_n` is `{min, max, median}`, never a scalar.** The document gives the reason and it is
not stylistic: real files are uneven, and a bare `technical_n: 3` is a claim of balance nobody
checked.

**`measurements.parquet` holds the uncollapsed rows** at `(unit, measurement)` and is present only
when a step passed `measurement=`. The input path does not produce it — those rows are the input's,
not the run's.

**The weighted interval is a construction, not a post-hoc adjustment.** Weighted mean and weighted
variance, with degrees of freedom from Kish's effective sample size rather than the row count.
`reference.md` § Weighted samples states the consequence to preserve: weighting concentrates the
estimate on fewer units, and an interval that ignored that would be narrower than the sample
supports. A percentile interval draws units as usual and recomputes the weighted statistic on each
draw — weights in the estimate, not in the drawing.

**`effective` joins `n` only when weighting applies**, on the same argument `clusters` joins it on:
an interval whose df came from 191 is a different construction than one whose df came from 228, and
which one a reader holds should not have to be inferred from `weight_by` being set elsewhere in the
config. A design that never weights must read exactly as it does today.

## Decisions

| # | Decision | Ruling | Grounds |
|---|---|---|---|
| 1 | Does the weighted interval ship here or route to H4? | **Here** | Shipping `weight_by` as an accepted declaration while `t_over_units` still returns an unweighted interval is this project's dominant defect exactly — a declaration validated but its effect not delivered, silently — and it is strictly worse than today's honest refusal. The scoping separately measured H4 as blocking on `cluster_by`, `allocation` and `groups` only, so this pulls none of H4's work forward |
| 2 | `measurements` and `weight_by` in one slice | **One slice, two independent halves** | They share nothing, so neither can break the other; and each alone is smaller than any slice this project has run. If it runs long they split cleanly on that seam — flagged now rather than discovered at task 9 |
| 3 | `measurements: {}` and `weight_by: ""` | **Become findings** | The truthiness gate that lets them through today is a hole, not a feature. Un-refusing a declaration must not turn its empty form into a working default — that is the silent-skip class H1 spent a slice removing |
| 4 | Where the collapse lives | `units.py`, one function, called by both paths | Two implementations of "the same rule" is how the retry path and the measurement path come to disagree about identical-looking rows |
| 5 | Does the input path write `measurements.parquet`? | **No** | The artifact holds what the *run* measured. Input rows are the input's, and `reference.md` scopes the file to "present only when a step passed `measurement=`" |
| 6 | Where a retired `-UNSUPPORTED` code is recorded | **§ The one config file's `NOT BUILT` list — not the validate-time registry** | That family is *deliberately absent* from § Errors `validate` reports, which is why the list and not the table is where a refused block is named. H3a takes **eleven declarations to nine** and removes two `NOT BUILT` inline comments. Missing this is how H2 nearly mis-scoped a code's home, and the count is a number in prose that no mechanical check will catch |

## Risks

- **A declaration accepted whose effect is not delivered.** The `weight_by`-without-weighting
  shape decision 1 refuses, and its twin: `measurements` accepted while `technical_n` is never
  computed. **Every check needs a test producing its identifier, and every declaration needs a
  second test proving its effect.** The identifier test alone is what would let this ship.
- **The retry/measurement ambiguity.** First-write-wins and collapse-and-average are opposite
  behaviours over rows that look identical. The `measurement=` argument is the only discriminator;
  a bug here silently averages retries into an estimate. This wants a test with both shapes in
  one run.
- **The two collapse paths diverging.** Decision 4 is the guard; the test is a mutation that
  changes one path's rule and must break both paths' tests.
- **`n`'s parts changing shape for designs that do not weight.** `effective` is conditional. The
  regression is a run with no `weight_by` whose `n` gains a key.
- **A weighted interval that is not actually wider.** Kish's size is the whole point. A test must
  pin that a weighted interval over a genuinely uneven weight column is wider than the unweighted
  one over the same values — an assertion on the number, not on the presence of a field.
- **The worked example.** `cohort-pilot` declares neither field, so nothing about it may move.
  Verified before designing; re-verified at the end.

## Testing

Every check H3a adds needs a test producing its identifier — the project's standing rule. Four
rows means four, plus the raise-time error and the two truthiness findings.

Three tests carry the slice, each pinning a different failure mode:

| Test | Pins |
|---|---|
| A run whose input carries three rows for one key, and a step that also calls `io.record(..., measurement=)` | Both collapse paths, in one run, against one rule |
| A step calling `io.record(..., measurement=)` with `measurements` undeclared | The raise — there is no rule to collapse under |
| A weighted interval over an uneven weight column, asserted **wider** than the unweighted one | That the weight reached the construction, not just the record |

The third is the one to write first. A test that only asserts `weighted_by` is recorded would pass
against an implementation that stores the declaration and computes the unweighted interval — which
is the bug, not the fix.

**Mutations each must kill:** dropping the weights from the variance but keeping them in the mean;
using the row count for df instead of Kish's size; collapsing at finalize instead of before `n`;
making the input path's collapse rule differ from the step path's; and emitting `effective` on a
run that declares no `weight_by`.

## Task sequence

Two independent halves. Within each, the order is what the next step needs.

**A — `measurements`.** The collapse function and its rule check (row 243); the input path inside
`resolve_units`; `io.record`'s `measurement=` parameter and the undeclared raise; the step path's
collapse at finalize; `technical_n`; `measurements.parquet`; the whole-leaf `envelope.py` closure
and the `reference.md` passage that calls the gap latent.

**B — `weight_by`.** The three checks (attribute exists, weights usable, the undeclared warning);
the weighted mean and variance and Kish's df in `stats.py`; `n` gaining `effective`; `weighted_by`
in the record; the percentile path recomputing the weighted statistic per draw.

**C — the consistency passes and the exit criterion.** The two `E-DATA-*` retirements verified in
both directions — absent from `src/` *and* from the documents, the direction a `comm -23` cannot
see; § The one config file's count taken from eleven to nine with both `NOT BUILT` inline comments
removed; the validate-time registry moved by exactly what this slice minted and by nothing else;
the worked example unmoved; and `partition_units` **untouched**, which is H3a's own claim to being
first and the one H3b and H3c will both rely on.
