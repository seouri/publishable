# Contrasts (S4b)

**Status:** approved.
**Deliverable:** code, on top of S4a. S4a is merged at `0fc2a6f` — 25 modules, 632 tests, a
template able to derive a metric from the unit table with a resampled interval.

S4b makes a run *compare*. Until now every number in `aggregated` describes one condition; after
S4b a run also reports the difference between two of them, with an interval built from the
pairing rather than from the two sides' intervals.

The four documents in `docs/` remain normative and lead. Where code cannot follow them, the
document changes first and the gap goes in `docs/superpowers/spec-defects.md`.

## Why contrasts and correction are two slices

S4 was scoped as one statistics slice and became three. S4a took derived metrics; what remained
— contrasts and multiplicity correction — still splits cleanly.

| Slice | Contents | Retires |
|---|---|---|
| **S4b** | `vs_baseline` deltas, declared `contrasts` with `within`, `n_paired`, `cohens_d`, the two reachable interval constructions, `min_reported_n` | `E-STATS-CONTRASTS-UNSUPPORTED` |
| **S4c** | The correction family — `none`/`bonferroni`/`holm`/`fdr_bh`, `ci95_corrected`, `family_size` | `W-STATS-FAMILY` |

A reviewer could reject correction while approving contrasts: one computes numbers, the other
transforms a family of already-computed ones. And the intermediate state is honest rather than
awkward — it is the state the documents already describe, where deltas are reported, every
metric records `correction: null`, and `W-STATS-FAMILY` says plainly that correction is not
implemented in this build.

## Two constructions, not four

`docs/reference.md` § How a metric becomes a number lists four contrast intervals. **Only two
are reachable in this build**, and saying so explicitly is the point of this section — an
implementer reading that table alone would build twice what is needed.

Line 81 of the config schema is the reason: `allocation: within | between — feeds paired vs
unpaired, per contrast`. `allocation: between` is still refused from S2
(`E-DATA-ALLOCATION-UNSUPPORTED`), so every contrast in this build is paired.

| Construction | Reachable? | Why |
|---|---|---|
| `paired_t_over_units` | **yes** | A column metric: Student's *t* on the per-unit differences, df = `n_paired` − 1 |
| `paired_percentile_over_units` | **yes** | A derived metric: percentiles of the resampled difference |
| `welch_t_over_units` | no | The unpaired counterpart; needs `allocation: between` |
| `unpaired_percentile_over_units` | no | The unpaired counterpart; needs `allocation: between` |

The `_clustered` suffixes are likewise unreachable, since `cluster_by` is refused. This is the
same scope reduction `cluster_by` gave S3c, and it should be stated in the code's docstrings so
the next reader does not go looking for the missing halves.

## The interval is its own construction

`reference.md`: **"A contrast's interval is its own construction, never a difference of the two
sides' intervals."** Differencing them discards the covariance that pairing exists to exploit.

This is not a refinement — it is why the worked example's per-condition intervals are wide
(r = 0.607, [0.517, 0.683]) while the delta's is narrow (0.026, [−0.007, 0.059]). `CLAUDE.md`
calls that contrast "what `allocation: within` buys, and flattening it would reintroduce the
defect this scheme fixed."

**`paired_percentile_over_units` draws once and applies the draw to both sides.** Two
independent draws would resample the two conditions apart and destroy the pairing in exactly
the way differencing intervals does. This is the single most likely thing to get subtly wrong,
because both spellings produce a plausible interval and only the paired one is narrower.

## `n_paired`, and what it counts

A contrast is computed over the **intersection of both sides' completed units** — not the union,
and not either side alone. That count is recorded as `n_paired`, and it is the denominator the
interval rests on.

**`limits.min_reported_n` becomes real here**, closing a live silent no-op. `materialize.py`
writes `min_reported_n: 10` into every generated config and **nothing in `src/` reads it** —
the same class of defect S4a closed for five statistics blocks. `reference.md` § Contrasts says
it "applies to a `within` contrast's `n_paired`, since a stratified paired comparison is where a
small denominator is easiest to miss and most disclosive." So: warn when a contrast's `n_paired`
falls below it.

## `cohens_d` is `d`z, and only for a per-unit mean

For a paired contrast, Cohen's *d* is **d*z*** — the mean of the per-unit differences over their
standard deviation. (*d*s is the unpaired form and is unreachable here.)

It is reported **only when the metric is a per-unit mean**, and is `null` otherwise. A derived
metric has no per-unit value to difference, which is why the worked example reports
`cohens_d: null` for `r` — and S4a was told not to compute it precisely so this slice could.
Reintroducing a *d* for `r` would contradict the worked example the three documents share.

## What a contrast may not be

**Contrasts compare conditions and do not nest.** `reference.md` and `design-principles.md` both
say so: anything comparing two contrasts — a dose-response ordering, a difference-in-differences,
a nested mean over cells — is an **interaction**, and stays a `summary`-step `Estimate`.

So a declared contrast whose `of` or `against` names another contrast's `id` rather than a
condition label is refused. `of`/`against` name conditions **by label**, which is the selector
property S3a's label grammar exists to provide: a label has to be something a person can write
down without seeing the directory.

`within` names unit attributes and their levels, and the contrast is computed over units matching
all of them. It is per-contrast and independent of `statistics.report_by`, which remains refused.

## Modules

| Module | Responsibility |
|---|---|
| `stats.py` | The paired difference table; `paired_t_over_units`; `paired_percentile_over_units`; `cohens_d` |
| `contrasts.py` *(new)* | **Pure.** Resolving `vs_baseline` and declared entries into a list of comparisons, with `within` applied |
| `validate.py` | Retire `E-STATS-CONTRASTS-UNSUPPORTED`; refuse a contrast naming a contrast; check `of`/`against` resolve to real condition labels |
| `cli.py` · `run_record.py` | The `vs_baseline` block in the record |

`contrasts.py` is pure for the same reason `sweep.py` is: resolving which comparisons a config
asks for is a function of the config and the resolved conditions alone, and can be tested
exhaustively without a run directory.

## Testing

- **The pairing is verified by the property that makes it worth doing.** A paired interval over
  correlated conditions must be **narrower** than an unpaired difference of the same data — and
  a fixture where the two conditions move together should show it starkly. That is the test a
  two-independent-draws implementation fails.
- **The worked example's own numbers.** delta 0.026 with `ci95` [−0.007, 0.059]; kendall's
  −0.169 with [−0.213, −0.125]. `CLAUDE.md` records that the delta's half-width "does not go
  below ≈0.033 for a linear-versus-rank contrast at this *n*", so an interval narrower than that
  is a defect, not an improvement.
- **`n_paired` is the intersection**, asserted against a fixture where the two sides complete
  different unit sets — the union and either side alone must all give different numbers.
- **`cohens_d` is `null` for a derived metric and a number for a column metric**, both pinned.
- **Every new `E-`/`W-` identifier has a test that produces it**, and for a validate-time code
  that means through `validate_config`.
- **A run with no baseline and no declared contrasts is unchanged** — no `vs_baseline` block at
  all. Adding a comparison origin risks it appearing where nothing asked for one, which is the
  regression that has landed in three consecutive slices.

## Explicitly out of scope

- The correction family, `ci95_corrected`, `family_size`, `correction_level` — S4c.
  `correction: null` and `W-STATS-FAMILY` stay exactly as they are.
- `welch_t_over_units`, `unpaired_percentile_over_units`, and every `_clustered` variant —
  unreachable while `allocation: between` and `cluster_by` are refused.
- `statistics.resample` as a declared block, `null_test`, `report_by` — still refused from S4a.
  A `null_test` p-value corrected alongside the intervals is S4c's concern at the earliest.
- `Estimate`, `hypotheses`, verdicts — S5, still refused.
- Interactions of any kind. They are a `summary`-step `Estimate`, and this slice refuses the
  contrast spelling of them rather than implementing one.

## Ledger entries this slice should retire or answer

- *"`limits.min_reported_n` is written by `materialize` and read by nothing"* — retired here.
- *"`E-STATS-CONTRASTS-UNSUPPORTED`"* — retired here; the other four refusals stay.
- *"`percentile_over_units` is unguarded and currently unreachable"* — still open, and this slice
  must not wire it up as-is; the paired construction needs the same survivor floor.
- *"`limits.max_ineligible_fraction` validates clean and is read by nothing"* — untouched, still
  open, and now the last of its kind.
