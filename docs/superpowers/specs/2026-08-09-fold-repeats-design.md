# Fold repeats (S3c)

**Status:** approved.
**Deliverable:** code, on top of S3b. S3b is merged at `442810a` — 490 tests, a design that
can declare a `batch` level, nest a second level inside it, and shuffle executions within
each batch.

S3c makes a repeat change *which units a step sees*. Until now every execution is handed the
whole roster; after S3c a `fold` repeat hands each execution one test partition, and the
inference base is rebuilt from the concatenation of those partitions rather than from an
average over them.

The four documents in `docs/` remain normative and lead. Where code cannot follow them, the
document changes first and the gap goes in `docs/superpowers/spec-defects.md`.

## Why this is one slice

S3a split sweeps from repeats, and S3b split `batch` from `fold`, both because each half had
an independently demonstrable acceptance criterion. `fold` does not decompose that way.

Partitioning with the old averaging collapse produces wrong numbers; the new collapse with no
partitions has nothing to concatenate; the counting rule cannot be tested without partitions
to count over. Every piece below is the same rule — **a unit appears in exactly one fold** —
propagating through four places. A boundary you cannot test across is not a boundary.

## The four rules this changes

Three were named when S3b was split out. The fourth was found while writing this spec, and it
is the most severe.

| Rule as S2/S3b built it | What `fold` requires |
|---|---|
| `io.units` is the whole roster; `.train` always raises | Returns one fold's **test partition**; `.train` returns the complement; **both raise at `run` and `condition` scope** |
| `stats.collapse_repeats` averages across all repeats | **Concatenates** across folds, while still averaging seeds *within* a fold — two operations in one function, selected by level kind |
| `runner.attrition` intersects `completed`/`ineligible` across **every** repeat-scoped execution | Intersects over **the repeats a unit was handed** |
| `runner._units_failed_anywhere` measures against the whole roster | Measures against the **partition** |

**The fourth is a hard abort, not a subtle wrong number.** `_units_failed_anywhere` computes
`failed |= keys - (r.recorded | r.skipped)` where `keys` is the entire resolved roster. Under
`{kind: fold, k: 10}` over 240 units, each execution is handed 24, so the other 216 are
neither recorded nor skipped and are counted failed — on the *first* execution. The generated
config ships `max_failed_fraction: 0.2`, so the run crosses the threshold immediately and
stops, reporting `failed`. Every fold run would abort before its second execution.

That guard is right for what it was written for: `reference.md` § The per-unit tables says the
run-level fraction is a union across every recording execution, deliberately unlike
`attrition`'s intersection. What changes is not the union but the **membership set** it
subtracts from — the units an execution was handed, rather than every unit in the run.

## What three still-refused fields buy us

`cluster_by`, `holdout`, and `allocation: between` all remain refused from S2. Stating this
explicitly matters, because `reference.md` § Repeat kinds describes `fold` as
"cluster-respecting when `cluster_by` is declared, and drawn within each arm under
`allocation: between`" — an implementer reading only that sentence would build partitioning
this build cannot reach.

| Still refused | What it removes from this slice |
|---|---|
| `cluster_by` | Cluster-respecting partitioning, and leave-one-*cluster*-out — so `k: all` means exactly one unit per fold |
| `allocation: between` | Drawing partitions within each arm |
| `holdout` | `.train` sourced from anything but a fold, so `E-STEP-UNITS-UNAVAILABLE` keeps its existing message for the holdout half and gains only the fold half |

## Where the partition comes from

**From the design digest, never `parameters_hash`.** `reference.md` § What auto-derives from is
explicit: if randomization derived from the parameters, editing any parameter would redraw
every fold boundary, reseed every repeat, and reassign every unit — a run that varied one
number would share no partition with the run before it. This is the same rule `order_seed`
already follows.

**Drawn once per run and shared across every condition.** `reference.md` § A `fold` repeat puts
the units out of reach already states this and gives the argument: under `allocation: within`,
comparisons across conditions are paired unit by unit, and pairing fold 3 of one condition
against a *differently drawn* fold 3 of another would not be a paired comparison at all.
Shared partitions are also what let the layout name repeat directories `fold03` identically
under every condition.

A consequence worth stating rather than discovering: because the partition is drawn once, a
`seed` level outside a `fold` level does **not** redraw folds per seed. Repeated
cross-validation with re-randomized partitions is therefore not expressible in this build.
That is a non-promise, not a gap to fill later without an argument.

## The collapse is two operations in one function

`reference.md` § How a metric becomes a number: core collapses **inner-to-outer**, so
`10 folds × 3 seeds` averages the seeds within each fold *before* combining folds, rather than
flattening thirty numbers that are not exchangeable.

So `collapse_repeats` selects its operation by level kind:

- `seed` and `batch` levels — **average** a unit's values across that level's members.
- `fold` levels — **concatenate**, because each unit appears in exactly one member.

This is the hardest code in the slice and gets its own task and its own acceptance test.
Averaging across folds would divide each unit's single observation by one and look correct;
concatenating across seeds would enter a unit into the table three times and inflate `n`
without any error surfacing. Both failures produce plausible numbers, which is why the tests
must assert the *shape* of the collapsed table and not only its values.

## Attrition keys on the repeats a unit was handed

`reference.md` § The per-unit tables gives the rule as a three-row table, and the qualifier is
load-bearing: intersecting over *every* repeat "would report `completed: 0` for any design
containing a fold, because no unit is ever in more than one of them."

| Repeat structure | A unit is handed to | It counts as completed when |
|---|---|---|
| `seed` or `batch` levels only | Every repeat | It completed in all of them |
| A `fold` level | Exactly one fold per sweep | It completed in that fold |
| `fold` × `seed` | Every seed of its own fold | It completed in all of that fold's seeds |

The named test is the third row: a unit that completes in one seed of its fold and not the
other. A rewrite that grouped by fold but forgot to intersect within the group passes the
`fold`-alone case and fails only here.

**`resolved` counts what the execution was handed, not the cohort.** Under `{k: 10}` over 240
units, a fold that records all 24 of its partition is `{resolved: 24, completed: 24,
failed: 0}` — not 216 failures against a cohort it was never given. The condition-level `n`
then returns to 240 by concatenation, which is the reconciliation to assert.

## What S3c refuses

| Declaration | Refusal | Why not now |
|---|---|---|
| `fold.stratify_by` | `E-REPL-FOLD-STRATIFY-UNSUPPORTED` | A second partitioning algorithm with its own cross-field validation — the attribute must exist, be categorical, and leave enough units per stratum per fold. It proves none of the four contract changes |
| `k` exceeding the resolved unit count | `E-REPL-FOLD-K-TOO-LARGE` | A fold with no units to test is a declaration error, not a small fold — the same reasoning that refuses a sweep expanding to zero conditions |

`k` is an integer ≥ 2 or the literal `all`. `reference.md` § Repeat kinds argues `all` rather
than a hard-coded count: writing `k: 240` works arithmetically and silently stops meaning
leave-one-out the moment the cohort gains a unit.

## Modules

| Module | Responsibility |
|---|---|
| `replication.py` | `fold` accepted; `k`/`all` resolved against the roster; the two new refusals; fold members carry their partition index |
| `units.py` | The partitioning function itself; `io.units` returns the test partition at `repeat` scope; `.train` returns the complement; both raise at `run` and `condition` scope |
| `stats.py` | `collapse_repeats` selects average or concatenate by level kind, inner-to-outer |
| `runner.py` | `attrition` intersects over the repeats a unit was handed; `_units_failed_anywhere` measures against the partition |
| `cli.py` · `sweep.py` | `partitions` into `sweep.yaml` |

**Partitioning lives in `units.py`, not a new module.** `reference.md` § Package layout assigns
it there explicitly — "unit resolution (table/glob/resolver registry), keys, attributes,
partitioning" — and the documents lead. An earlier draft of this spec proposed a separate pure
`folds.py`; that would have been a divergence from the documented layout bought with nothing,
since the partitioning *function* can be pure and exhaustively tested wherever it sits.

`io.units.train` is **the same kind of sequence** as `io.units` — iteration, `len`, integer
indexing, and nothing more. `reference.md` § The unit list is three operations is explicit that
there is no `io.units.train.train`, because a partition of a partition is not something the
declarations describe.

## Testing

- **The partition gets a property suite**, not a fixture comparison: every unit appears in
  exactly one test partition, the partitions cover the roster, sizes differ by at most one,
  `k: all` yields one unit each, and the same digest reproduces the same split while a
  different one does not.
- **The collapse is asserted on shape as well as value.** Averaging across folds and
  concatenating across seeds both produce plausible numbers; only the row count and the
  per-unit observation count distinguish them.
- **`max_failed_fraction` is tested from both sides under a fold**: a healthy fold run does not
  trip it (the regression that would otherwise abort every fold run), and a genuinely failing
  one still does.
- **The scope raise is tested at both `run` and `condition`**, for `io.units` *and*
  `io.units.train`, and confirmed **not** to fire at `repeat` scope.
- **Every new `E-`/`W-` identifier has a test that produces it** — the project's coverage bar,
  which has caught unexercised codes in four consecutive slices.
- **A run with no `fold` level is unchanged.** Every rule above is conditional on a fold being
  declared, and the regression risk is that one of them fires when none is.

## Explicitly out of scope

- `stratify_by`, and `k` beyond the roster — refused by name above.
- `cluster_by`, `holdout`, `allocation: between` — still refused from S2, unchanged.
- Repeated cross-validation with re-randomized partitions — not expressible, by the
  once-per-run rule argued above.
- `repeat_spread` and every other statistic — still S4. This slice changes *how* the unit
  table is built and adds no new reported quantity.
- Three or more repeat levels, and two levels of one kind — still refused from S3b.

## Ledger entries this slice should retire or answer

- *"`E-REPL-FOLD-UNSUPPORTED`"* — retired by this slice.
- *"`io.units.train` always raises"* — answered: it now returns the complement under a fold,
  and keeps its existing message when neither a fold nor a `holdout` is declared.
- *"A single repeat has no dispersion"* — still deferred, still S4's.
- *"The `any_invalid` early return masks later refusals in one pass"* — untouched, still open.
