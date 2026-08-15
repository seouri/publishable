# Derived metrics and dispersion (S4a)

**Status:** approved.
**Deliverable:** code, on top of S3c. S3c is merged at `bcc8e90` — 24 modules, 552 tests, a
`fold` repeat handing each execution its own test partition.

S4a adds the third way a metric can come to exist. Until now a number in `aggregated` is
either a recorded column (`basis: units`) or a step-returned scalar (`basis: repeats`). After
S4a a template can **derive** one from the unit table, and core resamples it for an interval.

The four documents in `docs/` remain normative and lead. Where code cannot follow them, the
document changes first and the gap goes in `docs/superpowers/spec-defects.md`.

## Why S4 is three slices, and why this one is first

S4 was scoped as "the statistics slice": `repeat_spread`, `vs_baseline` deltas, declared
contrasts, multiplicity correction, `cohens_d`, percentile intervals, `Estimate`,
`statistics.resample`, `null_test`, `report_by`, `n_paired`. That is three subsystems.

| Slice | Contents | Retires |
|---|---|---|
| **S4a** | `aggregate(units, cfg)`, the bootstrap that gives a derived metric its interval, `repeat_spread`, one coercion rule across three surfaces, and five refusals | — |
| **S4b** | `vs_baseline` deltas, declared `contrasts` with `within`, `n_paired`, `cohens_d`, the four interval constructions, the correction family | `W-STATS-FAMILY`, and two refusals |
| **S4c** | `statistics.resample` widened to column metrics with `stratify_by`, `null_test`, `report_by` | Three refusals |

**`aggregate` goes first because it decides what a metric *is*.** Contrasts built before it
exists would be built over recorded columns only, then revisited when derived metrics arrive
with different interval semantics and a different `cohens_d` — the build-it-twice failure that
putting sweeps before folds avoided.

**`cohens_d` belongs to S4b, not here.** It is a property of a *difference*, computed from
paired per-unit differences, so it has no meaning without a contrast to attach to. Landing it
in S4a would make it a field that is `null` in every case this slice can produce — untestable
in the direction that matters.

## The live defect this slice closes

A declared `hypotheses` block **validates clean and is ignored**. So do
`statistics.contrasts`, `.resample`, `.null_test`, and `.report_by`. A config declaring a
2000-draw bootstrap and a pre-registered hypothesis runs, reports success, and does neither.

`_check_shape` guards their *shape* — deliberately, so the next reader inherits a guard rather
than the crash a hand-edited config would produce — but nothing refuses them. This is the
silent-no-op class the project treats as worst, and it is shipped in `main` today.

`statistics.correction` is the counter-example and shows what the others should have done:
it is **disclosed**, with `W-STATS-FAMILY` warning that correction is not implemented and every
aggregated metric recording `correction: null` so the record cannot be read as corrected.

So S4a refuses all five by name, and each is retired by the slice that implements it:

| Declaration | Refusal | Retired by |
|---|---|---|
| `statistics.contrasts` | `E-STATS-CONTRASTS-UNSUPPORTED` | S4b |
| `statistics.resample` | `E-STATS-RESAMPLE-UNSUPPORTED` | S4c |
| `statistics.null_test` | `E-STATS-NULLTEST-UNSUPPORTED` | S4c |
| `statistics.report_by` | `E-STATS-REPORTBY-UNSUPPORTED` | S4c |
| `hypotheses` | `E-HYPOTHESIS-UNSUPPORTED` | S5 |

Before minting any of these, grep `docs/reference.md` — several codes this project "added"
already existed in its registry.

## What `aggregate` is

An optional method on a template, deriving metrics **from the unit table** rather than from
anything a step returned:

- **Called once per recording step.** A pipeline can have several, and `reference.md`
  § Templates is explicit that returning `{}` is the right answer for a table `aggregate` does
  not recognize — not an error, and not something core should have to predict.
- **`cfg` is that condition's resolved parameters**, the same object a step receives. Under a
  sweep it therefore differs per condition, which is what lets one `aggregate` compute
  `pearson` here and `kendall` there.
- **The table supports exactly four operations** — row iteration, column access, `len`, and
  `columns`. Deliberately not a `DataFrame`: a table that also promised indexing, filtering and
  `.loc` would be one, and core could never change what backs it without breaking every plugin.
- **The return is a flat mapping of scalars** — what a step may return, with the same NumPy
  coercion and the same `ContractError` on anything structural. **There is no `Estimate`
  exception here**, unlike a `summary` step's return, because a derived metric is one core
  computes and resamples itself rather than one the user asserts.

## A derived metric's interval is a bootstrap

`reference.md` § How a metric becomes a number: a derived metric is `basis: units` with
`method: percentile_over_units`, and its `ci95` is a **percentile interval from resampling
units**. That is not optional — the config's own note says derived metrics "resample either
way", meaning the machinery runs whether or not `statistics.resample` is declared. S4c's block
*widens* resampling to column metrics and adds `stratify_by`; it does not switch it on.

So S4a builds the bootstrap. Its seed derives from the **design digest**, never
`parameters_hash` — the same rule fold partitions and `order_seed` already follow, and for the
same reason: editing an unrelated parameter must not redraw a resample.

Two consequences worth stating rather than discovering:

- **A derived metric cannot collide with a recorded column.** `reference.md` § Validation names
  this: one key in `aggregated` cannot hold both a column mean and a derived value. The code
  already exists and already covers this exact shape — § Errors core raises lists
  `E-STEP-KEY-COLLISION` for "a derived key against a recorded column, a recorded column
  against a unit attribute", and `artifacts.py` raises it today for the second case. **Reuse
  it; do not mint a second code for one fault.**
- **`cohens_d` is `null` for a derived metric**, and the worked example depends on it: `r` is
  derived by `aggregate(units)`, and Cohen's *d* needs a per-unit value to difference. S4a does
  not compute `cohens_d` at all, so it records `null` — which S4b must not "fix" for `r`.

## One coercion, three surfaces

`reference.md` § Steps and artifacts states the rule and the reason together: `io.record`'s
`values`, a step's return, and a template's `aggregate` take the same scalars under the same
coercion, because "a table core would reject what a return accepted would be a divergence found
on the first line anyone writes."

**It is not implemented twice. It is not implemented at all**, and both halves are live defects
in `main`. This spec originally said "twice"; checking the code before writing the plan proved
otherwise, and the correction is what makes this task worth its size.

What exists today are two *different* checks that happen to share the `E-STEP-RETURN-TYPE`
code: `artifacts.py` verifies a **column** holds one type across rows, and `runner.py` verifies
a step's return is a **mapping**. Neither looks at an individual value. `io.record` performs no
value check whatsoever, and nothing in the codebase mentions NumPy.

The two consequences, both reproduced:

| Documented rule | What happens today |
|---|---|
| A NumPy scalar is coerced | `numpy.float64` reaches `yaml.safe_dump` and raises `RepresenterError` — an uncaught traceback while writing `run.yaml`, not a diagnostic |
| Anything structural is a `ContractError` | A nested mapping serializes **silently** into `run.yaml` |

The first is the sharper one: `reference.md` § Steps and artifacts says a per-unit value "is a
`numpy.float64` at least as often as a derived metric is", so the ordinary case of a step
returning a value from a fitted model crashes the run at record-writing time.

So S4a **implements the rule once, for the first time**, and applies it at all three surfaces.
S2's deferral — *"Unifying all three is worth doing once `aggregate` exists"* — comes due here,
but as construction rather than consolidation.

The two existing checks stay as they are: a column-consistency check and a return-shape check
are genuinely different questions from per-value coercion, and folding them together would
merge three rules rather than unify one. Every existing test of those two must pass unchanged.

## `repeat_spread`, a passenger

`reference.md` § A `batch` says *when*, not *what* specifies dispersion as **one entry per
level, outer to inner**:

```yaml
repeat_spread:
  - {std: 0.019, n: 5, kind: batch}
  - {std: 0.004, n: 3, kind: seed}
```

That contrast is the whole reason the `batch` kind exists: reported as a single figure, how much
the *world* moved and how much the *RNG* moved would be indistinguishable, and the larger of
them mislabelled as randomness the tool controls.

It rides in S4a because it is small and reads directly off the `RepeatLevel` list S3b built —
**not** because it belongs with `aggregate`. A reviewer should not hunt for a conceptual link
that isn't there.

Under a `fold` level there is nothing to average across, so a fold contributes no
`repeat_spread` entry — each unit appears in exactly one fold, which is why S3c made the
collapse concatenate there rather than average.

## Modules

| Module | Responsibility |
|---|---|
| `stats.py` | The bootstrap; `percentile_over_units`; `repeat_spread`; derived metrics entering `summarize_step`'s output |
| `templates/base.py` | `aggregate` on `BaseTemplate`, defaulting to `{}` |
| `coercion` *(new, or an existing home)* | The one scalar rule — NumPy coerced, structural refused — called by `io.record`, a step's return, and the `aggregate` path. It does **not** absorb `artifacts.py`'s column-consistency check or `runner.py`'s return-shape check; those are different questions |
| `validate.py` | The five refusals |
| `runner.py` · `cli.py` | Calling `aggregate` once per recording step; carrying derived metrics and `repeat_spread` into the record |

`stats.py` stays **pure** — no filesystem, no runtime import of `config`, `artifacts`,
`runner`, or `cli`. A bootstrap is a function of a table and a seed, and it can then be tested
exhaustively without a run directory.

## Testing

- **The bootstrap is verified against something other than itself.** Checking a percentile
  interval by re-running the same code proves nothing. Verify instead that it brackets the
  point estimate, that it reproduces exactly from the same digest and differs from another,
  that it converges toward the analytic interval as draws increase for a mean, and that it is
  invariant to row order.
- **`aggregate` is tested for what it must *not* do**: a template without one is unchanged; one
  returning `{}` produces no derived metric rather than an empty one; one returning a
  structural value raises `ContractError`; one colliding with a recorded column is refused.
- **The coercion work edits no existing test.** It adds a rule that did not exist rather than
  changing two that did, so `artifacts.py`'s column-consistency tests and `runner.py`'s
  return-shape tests must pass untouched. If one had to change, something merged that should
  not have, and that is the finding.
- **Both live defects get a test that fails before the fix**: a step returning a NumPy scalar
  reaches `run.yaml` as a plain number rather than raising `RepresenterError`, and a step
  returning a nested mapping raises `ContractError` rather than serializing silently.
- **`repeat_spread` is asserted per level under `batch × seed`**, outer to inner, and absent
  under a bare `fold`.
- **Every new `E-`/`W-` identifier has a test that produces it** — the project's coverage bar,
  which has caught unexercised codes in five consecutive slices. For a validate-time code,
  producing it means through `validate_config`.
- **A run with no `aggregate` and no `repeat_spread` is unchanged.** The regression risk of
  adding a metric origin is that it appears where nothing asked for it.

## Explicitly out of scope

- `vs_baseline`, declared contrasts, `n_paired`, `cohens_d`, and the correction family — S4b.
  `W-STATS-FAMILY` and `correction: null` stay exactly as they are.
- `statistics.resample` as a *declared block*, `stratify_by`, `null_test`, `report_by` — S4c.
  The bootstrap machinery lands here; the block that widens it does not.
- `Estimate`, `hypotheses`, verdicts, `verdict_rests_on` — S5. Refused by name here.
- `weight_by`, `cluster_by`, `measurements`, `holdout` — still refused from S2, unchanged. A
  derived metric's interval is therefore over units, never over clusters, in this build.

## Ledger entries this slice should retire or answer

- *"The full scalar-coercion rule for returned values"* — retired: unified across all three.
- *"The generated config calls itself 'the complete parameter set' before it is one"* — narrow
  it again; after S4a the `statistics` sub-keys exist and are refused rather than absent.
- *"A single repeat has no dispersion, and the documents don't say what is reported"* — answer
  it here, since `repeat_spread` is what reports dispersion.
- *"An empty roster misattributes a fold's `E-REPL-N`"* — untouched, still open from S3c.
