# Task 11 report: refuse a weighted contrast, retire `E-DATA-WEIGHT-UNSUPPORTED`

**Status: complete.** Commits `b36b1b6` ("feat: data.units.weight_by is a declaration core honors,
except beside a contrast") and a follow-up carrying the § Validation checks-table row and a tighter
message assertion. Final state, re-run after every mutation had been reverted: `uv run pytest`
1226 passed, 2 xfailed; `uv run ruff check .` clean; `uv run mypy` clean. `ruff format` not run.

## Part 1 — the refusal, and the blast radius that shaped it

New code: **`E-DATA-WEIGHT-CONTRAST`**, on `data.units.weight_by`. The identifier is the one the
spine already promises H4 will retire (`docs/superpowers/specs/2026-08-08-implementation-spine-design.md`,
H4 Statistics row), so the two now agree by name.

**Measured before writing the guard.** I expanded each candidate shape and counted what
`contrasts.resolve_contrasts` actually builds:

| Config | conditions | comparisons |
|---|---|---|
| `baseline` alone (no axis) | 1 (the baseline row) | **0** |
| `baseline: {}` | 0 | 0 (already `E-SWEEP-EXPANDS-EMPTY`) |
| `baseline` + `grid` (2 levels) | 3 | 2 |
| `baseline` + `ablate` | 2 | 1 |
| `grid` alone | 2 | 0 |
| `grid` + declared `statistics.contrasts` | 2 | 1 |
| `statistics.contrasts` with no sweep | 1 (label `None`) | `KeyError` — already refused by `E-STATS-CONTRAST-UNKNOWN` |
| `statistics.report_by` | — | 0 |

So **`sweep.baseline` does not always produce a contrast**: a baseline with no axis beside it
expands to a single `is_baseline` row, which `resolve_contrasts` skips as an `of`, and the run
publishes no delta at all. A declaration-shaped guard (`weight_by` + truthy `baseline`) would
have refused a design core computes correctly — the wider-than-the-harm failure H2 checked for.
It would also have *missed* the other direction: a declared `statistics.contrasts` entry over a
sweep with no baseline is a real unweighted delta.

**The guard therefore reads the resolved family, not the declaration.** It sits in
`_check_sweep`, immediately after the existing `comparisons = len(resolve_contrasts(doc, conditions))`
(the same count `W-STATS-FAMILY` reports, inside the same `try/except` that already tolerates a
malformed contrasts block), and fires when `comparisons > 0` and `weight_by` is a non-empty
string. `report_by` is outside it by construction — a stratum publishes no delta and joins no
family. Message follows `E-SWEEP-SAMPLE-BASELINE`'s shape: what is wrong (each condition's value
and interval are weighted, the delta between them is not), what to do instead (drop `weight_by`,
or express the difference as a `summary`-step `Estimate`), and that the combination will be
honored once the paired estimators take weights.

Resulting behaviour, against the brief's target table: `weight_by` alone works; `weight_by` +
`statistics.contrasts` refused; `weight_by` + `sweep.baseline` refused **whenever that baseline
generates a comparison**, which is every baseline design except the degenerate axis-free one.
That last row is the one deviation from the brief's table, and it is the deviation the brief's own
"measure the blast radius" instruction asks for; it is pinned by a test with a control.

## Registry placement — confirmed against the documents, not the brief

`reference.md` § The one config file states the `NOT BUILT` family "is deliberately absent from
the validate-time registry", and that this list "and not that table, is where a refused block is
named". § Validation's `### Errors validate reports` carries `E-SWEEP-SAMPLE-BASELINE` and
`E-SWEEP-ABLATE-CROSSED` — both temporary refusals of a *combination*. So the new code takes a
registry row and does **not** join the `NOT BUILT` list, and it carries no `-UNSUPPORTED` suffix
(a suffixed code in the registry would contradict that sentence in the same edit).

**A correction to my own first reading**, caught before commit: the § Validation *checks* table
above the registry does carry a row for `E-SWEEP-SAMPLE-BASELINE` — "Sample draws aren't compared
to a baseline … specified, not built in this build" — and one for `E-SWEEP-ABLATE-CROSSED`. Those
rows are codeless prose, so grepping the identifier had said nothing about them; only reading the
table region does. So the new refusal takes a sibling row there too, "Weighted deltas aren't
computed", in the same "specified, not built in this build" phrasing and beside the other three
weight rows.

## Part 2 — the retirement

- `("weight_by", "E-DATA-WEIGHT-UNSUPPORTED")` removed from the five-field loop, replaced by a
  comment saying what now reads the declaration and where the combination refusal lives.
- `reference.md` § The one config file: `NOT BUILT` marker dropped from `weight_by:`, prose count
  **ten → nine**, `.weight_by` removed from the enumerated list.
- **Also fixed, and not in the brief:** the same paragraph's trailing clause said "`.cluster_by`,
  `.weight_by` and `.holdout` inherit the same treatment when their slices land" — a future tense
  that goes false for `weight_by` the moment its slice lands. It now names the two that are still
  future and says why `weight_by` needed none of it (a string leaf has no sub-keys to close).
- **Verified, not assumed:** `envelope.py` types `data.units.weight_by` as `str`, so there is no
  whole-leaf block to close.
- Test bookkeeping: `weight_by` rows removed from the two `-UNSUPPORTED` parametrizations in
  `tests/test_validate.py`, and the section comment that said the refusal was "still live" rewritten.

## The forcing function

`tests/test_cli.py::test_n_gains_effective_under_a_weighted_design`: `xfail(strict=True)` marker
removed, and it **passes for real** — `weighted_by`, `n.effective == 3.0`, `n.completed == 4`, and
the arithmetic assertion `aggregated["pred"]["value"] == 2.0` (weighted; the unweighted mean of the
same fixture is 1.5). No expectation adjusted.

## The two previously untestable call sites

Both now have an end-to-end test asserting an exact number that differs between weighted and
unweighted, each with a control that must report:

- `test_the_collision_retry_keeps_the_weights_it_was_given` — a derived key colliding with the
  recorded `pred` column, so `cli` retries `summarize_step` without `derived`. Asserts the retry's
  `pred` is 2.0 (weighted), `n.effective` 3.0, `weighted_by` present; control asserts
  `W-STATS-AGGREGATE-FAILED` and `E-STEP-KEY-COLLISION` reached stdout, so the retry really ran.
- `test_a_reporting_stratum_is_weighted_by_its_own_units` — `weight_by` + `report_by: [cohort]`.
  Cohort `a` is `pred` 0/1 under weights 1/3: weighted mean 0.75 against an unweighted 0.5,
  effective size 1.6 against `completed` 2. Cohort `b` (equal weights) is 2.5 either way, and the
  parent block is 8/6 — neither stratum's answer, so the levels are their own tables.

## Mutation testing (each behaviour separately, `__pycache__` deleted between, reverts verified by behaviour)

| Mutation | Result |
|---|---|
| `comparisons > 0` → `comparisons >= 0` (widen the refusal) | 3 fail, incl. the baseline-alone edge and the `report_by` edge |
| `and` → `or` between the two conjuncts | 4 fail, incl. the unweighted-contrast control |
| drop `weights=` from `cli`'s collision-retry `summarize_step` | exactly `test_the_collision_retry_keeps_the_weights_it_was_given` |
| drop `weights=` from `cli`'s `report_by` `summarize_step` | exactly `test_a_reporting_stratum_is_weighted_by_its_own_units` |

Each revert re-ran the same selection green.

## Greps

`git ls-files '*.md' | grep -v '^docs/superpowers/' | xargs grep -n E-DATA-WEIGHT-UNSUPPORTED` →
no hits (exit 1). The same command with `E-DATA-WEIGHT-INVALID` → 2 hits in `docs/reference.md`,
proving it can fail. `docs/superpowers/*` keeps its planning history, as scoped.

Mechanical pass over every tracked `*.md`: links and `#anchor`s resolve (the three anchors in the
new row included), no duplicate heading anchors, no trailing whitespace, tabs or invisible unicode,
table rows match their headers (the only column-count reports are pre-existing lines using escaped
`\|` inside cells, which my checker miscounts and which I did not touch).

## Concerns and notes

1. **A brief item was already done.** The brief said `materialize.py`'s comment "loses `NOT BUILT`" —
   it never carried one: the generated config's line is
   `weight_by: null  # e.g. sampling_weight, when the sample is enriched`. Nothing to change; no
   other `NOT BUILT` string exists anywhere in `src/`.
2. **The brief's target table is coarser than the shipped guard**, deliberately — see the blast
   radius section. If a later reviewer wants `sweep.baseline` refused unconditionally under
   `weight_by`, that is a widening, and the axis-free baseline test is where the decision lands.
3. **§ Weighted samples' prose is unchanged**, and still describes the target behaviour ("a contrast
   between two weighted conditions uses the same weights on both sides"). The build-state fact lives
   only in the registry row, which is exactly how `E-SWEEP-SAMPLE-BASELINE` is documented. No
   `spec-defects.md` entry was added: nothing in the documents is wrong, only unimplemented, and the
   spine already assigns the lift to H4.
4. **Reach and remedy both checked.** This build has exactly two operation commands (`cli.OPERATION_COMMANDS`
   is `{"validate", "run"}`); `command_run` calls `validate_config` and returns `EXIT_WRONG` before
   creating a run directory, so no executing path reaches `resolve_contrasts` past the refusal. The
   remedy the message names is reachable today: a `summary` step returning an `Estimate` lands in
   `run.yaml` with `reported: true`, pinned by `tests/test_cli.py::test_an_estimate_with_an_interval_and_no_n_warns`.
5. **`cohort-pilot` is untouched** — the worked example declares no `weight_by`, and no example
   number moved.
