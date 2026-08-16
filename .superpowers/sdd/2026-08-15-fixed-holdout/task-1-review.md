# Task 1 review — the regression pin, a run with no holdout

Reviewed at `889de01` on branch `h3d-fixed-holdout`. Tree left clean: `1803 passed, 2 xfailed`,
`ruff check` clean, `mypy` clean, `git diff src/` empty after every mutation cycle (all reverts
by in-place edit from a scratchpad copy, `__pycache__` cleared between runs, each revert verified
by re-running the test).

## Verdicts

- **Spec compliance: ✅** — no `src/` change, the two named tests exist, nothing implies a declared
  holdout works, `E-DATA-HOLDOUT-UNSUPPORTED` is untouched and unreached.
- **Task quality: findings** — 1 Critical, 2 Important, 1 Minor. The assertions the pin *does* make
  are sound and non-vacuous; the problem is coverage, and it is only fixable before task 14.

Every mutation below was run **twice**: against the two pin tests (answering "does the pin cover
this site") and against the **whole suite** (answering "can task 14 move this site silently at
all"). The two answers differ, and the severities are graded on the second.

## The three brief defects — all three verified, all three real

**(a) `executions.jsonl` carries no `n` field.** Verified: one write site only
(`src/publishable/runner.py`, the `ledger.open("a")` block in `execute_plan`), writing exactly
`step`/`scope`/`condition`/`repeat`/`status`/`started_at`/`wall_seconds`/`error`. `grep -n
executions.jsonl src/publishable/*.py` finds no second writer. The brief's ledger `n.resolved`
assertion referenced a field this build never writes. Correctly relocated to `run.yaml`.

**(b) the empty `aggregated` block — confirmed, and the fix is load-bearing.** Ran the default
fixture and dumped the block: `run["results"]["conditions"][0]["aggregated"] ==
{"step01_summarize_units": {}}`. The brief's `assert aggregated` guard passes on that, and its
inner `for block in aggregated.values(): for metric in block.values():` iterates zero times —
a textbook vacuous check. With `aggregate_returns="mean_pred"` the block is populated:
`pred` and `mean_pred`, each with `n: {resolved: 10, completed: 10, ineligible: 0, failed: 0}`.
The replacement guard `assert set(aggregated) == {"pred", "mean_pred"}` is strictly stronger than
`assert aggregated` (it pins membership, not truthiness) and both metrics are then asserted on a
value. Fix accepted.

**(c) single failing step yields `failed`, not `partial`.** Verified in
`run_record.run_status`: `partial` requires `any(r.status == "completed")`. With only the
train-touching step, no execution completes. `extra_steps=["control"]` is the right repair, and
the test's `len(failed) == len(completed) == 5` plus the per-step name assertions make the mix
genuine rather than incidental.

## The nine sites — enumerated from `cli.command_run`, then mutated

Six narrowing sites (each mutated to `UnitList(list(roster)[:3])`, run against both pin tests):

| Site | What it decides | vs. the pin | vs. the whole suite |
|---|---|---|---|
| `units=roster` → `execute_plan` | `scoped_units` → `io.units`, `max_failed_fraction` | **survived** | caught (58 tests) |
| `_condition_beside_n(beside_n, roster, ...)` | `technical_n` withholding | **survived** | **SURVIVED — 1803 passed, 2 xfailed** |
| `_condition_counts(results, roster, ...)` | `n.resolved` per metric | caught | caught |
| `_condition_report_by_levels(roster, ...)` | per-stratum table + `attrition` | **survived** | caught |
| `_compute_vs_baseline(roster=)` | `units_matching` for `within` | **survived** | **SURVIVED — 1803 passed, 2 xfailed** |
| `_compute_declared_contrasts(roster=)` | same | **survived** | caught |

Plus, outside the six: narrowing the roster handed to `units_hash` — a site the spec says must
stay whole — **survives the whole suite** as well (see the Important below).

A seventh call site, `attrition(results, level_roster, ...)` inside the `report_by` loop, is
reached only through `_condition_report_by_levels` and is therefore unexecuted for the same
reason; naming it separately does not change the count of *unpinned* surface.

Three non-narrowing sites: `weights`, `unit_attributes`, `resample_strata`. The fixture's resolved
`data.units` is `{allocation: within, attributes: [], cluster_by: null, from: index.csv,
holdout: null, key: patient_id, measurements: null, weight_by: null}` and `statistics` is
`{correction: holm}`. So `weights` is `{}`, `unit_attributes` is `{}`, and no `resample.stratify_by`
exists — **zero of the three "surplus keys are inert" claims have any regression guard.**

## Findings

### Critical — three sites can be moved with the entire suite green

`_condition_beside_n`, `_compute_vs_baseline(roster=)`, and the `units_hash` call each survive an
unconditional 3-unit narrowing with **1803 passed, 2 xfailed**. That is the real silent-movement
surface at task 14/15: no test in this repo, pin or otherwise, can see those three change. Two of
them are exactly what the spec singles out — `units_hash` as one of the pair that "must stay
whole-roster", and `_condition_beside_n` as the `technical_n` guard the spec's own correction #6
already filed a gap against.

They are unreachable for the fixture reason, not the assertion reason: `_condition_beside_n` needs
`data.units.measurements`, `_compute_vs_baseline`'s roster argument feeds `units_matching`, so it
needs a `vs_baseline` comparison with `within`. Close them here (they are cheap fixture additions
to this pin) or file all three with a named owner **before task 14 merges** — after that there is
no un-narrowed build to characterize them against, and the spec's correction #4 routes end-to-end
coverage to task 18's pins, which land *after* the narrowing and so cannot serve as baselines.

### Important — the pin covers 1 of 6 narrowing sites, including one it executes and does not assert

Only `_condition_counts` is defended by the pin itself. The other three that the suite happens to
catch (`units=roster`, `_condition_report_by_levels`, `_compute_declared_contrasts`) are covered
by tests that will still exist at task 14, so this is a weakness in the pin rather than a hole in
the repo — but it matters for `units=roster`, which the fixture *does* execute and the pin still
misses, because it asserts `n["resolved"]` alone. Under that mutation the produced `run.yaml` is:

```
"pred": {"value": 1.0, "n": {"resolved": 10, "completed": 3, "ineligible": 0, "failed": 7},
         "ci95": [-1.484, 3.484], ...}
```

against the true `value: 4.5`, `completed: 10`, `failed: 0`, `ci95: [2.334, 6.666]`. **Four
observable numbers moved, the run still exited `EXIT_OK`** (`_units_failed_anywhere` is scoped to
the same narrowed list, so `max_failed_fraction: 0.2` never fired on 7/10), and both pin tests
passed. Adding `n.completed`, `n.failed` and the metric `value`/`ci95` to the assertions already
present closes it, and is the cheapest change in this review.

### Important — `units_hash` is a shape assertion on a value the spec says must not change

`assert provenance["units_hash"].startswith("sha256:")`. Mutating the call to
`units_hash(UnitList(list(roster)[:3]))` passes the pin **and the whole suite** (counted in the
Critical above). The spec names `provenance.units.n`/`units_hash` as the pair task 15 must leave
whole; the `n` half is a value assertion and correctly caught its mutation, the `units_hash` half
checks only the prefix. Assert equality against `units_hash` recomputed over the full roster rather
than a literal digest — the mutation of concern is at the call site, so a recompute discriminates it
without depending on the generated CSV being byte-stable.

### Important — `n` is pinned on one of its four keys

CLAUDE.md defines `n` as `resolved`/`completed`/`ineligible`/`failed`. Only `resolved` is asserted,
on both metrics. `completed` is the key task 14 moves. Cheapest single fix for the Critical above.

### Minor — the report's carry-forward understates finding (a)'s consequence

The report notes the ledger has no `n` and flags it for later tasks. Worth stating positively in
the slice ledger: the ledger is *not* a denominator surface at all, so task 15's "six denominators"
are all `run.yaml`-side, and any later brief repeating the ledger claim should be corrected at
source rather than re-discovered.

## What is good, explicitly

- Both brief mutations reproduce as reported: `step_units = UnitList(..., train=scoped_units)`
  fails `units_train_raises`; `_condition_counts` narrowing fails the denominator pin.
- `assert failed` / `assert completed` are a proper positive-companion pair — the absence-only trap
  is avoided, and `len(failed) == len(completed) == 5` pins both halves.
- `holdout is None` asserted rather than `not in` — the right call for the explicit-null shape.
- No parsed-structure normalisation hazard: everything asserted is a scalar or a plain mapping key;
  `yaml.safe_load` has nothing to undo here.
- The three brief-vs-code disagreements were found by running before writing, and documented at the
  assertion site as well as in the report.
