# H4a `statistics.resample` honoured — design

**Goal:** a config that declares `statistics.resample` gets the method, draw count and strata it
asked for, and a config that declares nothing gets **byte-identical output to today**. This retires
`E-STATS-RESAMPLE-UNSUPPORTED`, the refusal 8 of the 9 feasibility configs hit first.

**What it delivers, stated honestly.** One refusal retired, a regression preserved, and **zero
experiments newly executing**. Three payoff figures are in circulation and they count three different
things — 8/9 is refusal-gated, 0 is cumulative end-to-end, "six" is cumulative-with-a-table-roster
after H4a *and* H3d. E1–E6 still declare `holdout` (H3d), C1–C3 still declare `weight_by` beside a
baseline (H4b), and all nine declare a resolver (H7b). Writing "unblocks 8 of the nine" anywhere
normative would read as the executable count a month later, which is exactly the undated-build-claim
failure `CLAUDE.md`'s feasibility procedure step 10 exists to prevent.

**What it is not.** Not `null_test` and nothing `p_value`-shaped (H4d — `p_value` appears nowhere in
`src/`). Not the weighted or clustered **contrast** families (H4b). Not the unpaired family, and
`cli._entry_for`'s hard-coded `paired: True` **stays hard-coded** — its docstring says it expires with
`E-DATA-ALLOCATION-CONTRAST`, which is H4c. H4a edits the same metric-block builder, so a helpful
"while I'm here" derivation would land H4c's task here with none of H4c's estimators behind it.

---

## The measurement this rests on

`docs/superpowers/H4a-SCOPING.md`, taken 2026-08-15 against `main` at `eaf3605`. It re-measures
`H4-SCOPING.md` (taken at `cb96c7d`, before H3c-1, H3c-2 and H7a) and **the charter's 15 becomes 19**.
Load-bearing findings:

- **`stats.py` and `correction.py` are byte-identical to `cb96c7d`**, which licenses carrying forward
  the old scoping's construction inventory without re-grepping it. All drift lives in `validate.py`
  (+1798), `units.py` (+1207), `cli.py` (+603).
- **`percentile_over_units` and `percentile_over_units_clustered` are fully written, tested, and have
  zero production callers** — verified, no caller appeared. The unclustered column half really is
  wiring. The seed is already computed in `cli.command_run` and already passed to `summarize_step`.
- **But zero callers also means never production-shaped input.** The gap list is short and specific,
  and two of its entries are where this slice can produce a wrong number with a green suite.

---

## Decisions

| # | Decision | Ruling | Grounds |
|---|---|---|---|
| 1 | Is `bootstrap` the whole `resample.method` enum? | **Yes — a closed, one-value enum** | It is the only value the schema shows, the only construction that exists, and § Statistical reporting's method table lists strings core *emits*, not inputs. A one-value enum is a legitimate answer and an unstated one is not: closing it makes adding a second value a documented change rather than a silent one, and makes `method: bootstap` a diagnostic rather than a shrug |
| 2 | `resample_draws` for a column metric | **Record the requested `n`**; do not change `percentile_over_units`'s return type | A column metric's draw statistic is a mean over a non-empty sample, which is always defined — unlike a derived metric, whose `compute` can fail on a degenerate draw, which is why `percentile_of_derived` returns `(Interval, int)`. Changing the signature would touch ~20 existing tests for a value provably constant. **The implementer must verify that invariant before relying on it**; if a degenerate column draw is reachable, take `(Interval, int)` instead and say so |
| 3 | The stratified × clustered composition rule | **A stratum must be constant within a cluster; the draw is a cluster, drawn within its stratum** | `stratify_by` says what an independent draw is; `cluster_by` says the draw is a cluster. § Clustered units already requires exactly this constancy for `fold`, `holdout` and `assign` — resample takes the same rule rather than a second one, and `units.stratum_varies_within_cluster` (H3c-1) is the check that already exists |
| 4 | The validate-time bound on `n` | **Comparisons-only lower bound, plus a filed spec defect for the residue** | The old scoping's `comparisons × metrics` bound **cannot be built**: `correction.family_shape` derives `metrics` from `Member`s built *after* the run, out of `io.record` keys and `aggregate`'s return. Nothing in the config declares the metric set, so the full bound needs core to inspect user Python — which the greenfield invariant forbids. Comparisons *are* resolvable at validate time, so a bound that is always true when it fires and silent when it might not be is what survives |
| 5 | Where `_check_resample` sits in the sequence | **After `_check_sweep`**, before `_check_contrasts` | **Corrected during task 4's review — the original rationale here was false in both halves.** It said the strata check needs the roster that `_check_sweep` makes available and the `n` bound needs the comparison family `_check_sweep` computes. Neither is true: `roster` comes from `_check_units` and is already passed to `_check_fold_stratify_by` three calls earlier, so roster availability does not discriminate this position from any position after `_check_units`; and `_check_sweep` returns `None` and stores nothing on `doc`, so **the comparison family is never handed over and task 6 must recompute it locally**, which is position-independent. What the position actually buys is grouping with the other `statistics.*` checks and a sensible finding order. The placement is right; only its justification was wrong |
| 6 | `W-STATS-REPORTBY-THIN`'s whole-roster-vs-arm gap | **Declined, owner H4c, recorded in `spec-defects.md`** | Measured cost of claiming it: under `random`/`blocked` it requires `validate` to **perform the allocation draw** — apportionment, seeded shuffle, forward-only stratification on realized membership — which is 3–5 tasks and touches `provenance.allocation_hash`'s determinism story. That is 20–25% of H4a for a warning's precision. H4c already must reason about arm membership to derive `paired`. An explicit decline with a named owner satisfies the "silence is how it went stale" concern at a fraction of the cost |
| 7 | Split H4a at 19 tasks? | **No** | H3c-1 shipped 20. The only deferral candidate is the stratified draw, and **six of the seven non-null `resample:` declarations in the feasibility analysis carry a `stratify_by`** — deferring it would honour the declaration two-thirds of the way, the exact failure `_check_unimplemented` exists to prevent |

---

## The two places this slice can be wrong with a green suite

These are the reason H4a is not a wiring afternoon, and each gets its own task with its own mutation.

**1. `diffs` wins the tie in the correction pool.** `correction._corrected_bounds` tests
`member.diffs is not None` **first** and only then falls through to `member.pool`.
`cli._comparison_step_blocks` sets `diffs=None if is_derived else tuple(diffs)`, so a column contrast
**always** carries diffs today. The rule: under a declared `resample`, a column contrast's `Member`
carries the **pool** and sets **`diffs=None`**, while `cohens_dz` keeps computing from the local list.
`Member`'s own docstring — "exactly one of `pool`/`diffs`" — is what is being honoured.

> **Corrected during planning, and the correction matters for the mutation.** An earlier draft of this
> section said the failure mode is "add `pool=`, leave `diffs=` alone → a silent mismatch, nothing
> raises." **That is wrong.** `Member.__post_init__` tests `(pool is None) == (diffs is None)` and
> raises `ValueError` when both are set — and it raises *catastrophically*, because
> `_compute_vs_baseline` sits outside the `try/except ContractError`, so the run loses `run.yaml`
> after every execution is already spent. Loud, not silent. **The genuinely silent path is forgetting
> the `Member` entirely**, which drops the row from the correction family with nothing to show for it,
> and that is the mutation this task must fail.

**Naming, corrected during planning:** the spec originally attributed `paired: True`, the `col_keys`
narrowing, the `Member` loop, and `pool=`/`diffs=` to `cli._entry_for`. **All of them live in
`cli._comparison_step_blocks`**; `_entry_for` is a lookup helper that touches none of it. The facts
survive the correction — only the function name was wrong.

**2. `col_keys`, not `base_keys`.** The column branch narrows `base_keys → col_keys` on the metric
being present on both sides; the derived branch does not, because a derived metric has no column to be
ragged about. `paired_percentile_of_derived` builds its `UnitTable`s from whole rows, so handing it
`base_keys` for a column metric feeds `compute` rows missing that column — **loud if the compute
indexes, silent if it `.get`s**. `n_paired` stays `len(col_keys)`. The scoping's own verification probe
used 120 units all carrying the column, so it could not have seen this; the fixture must be ragged.

---

## The regression this slice exists to preserve

Trap 2 of the old scoping, and the reason the pin is **task 1, not a verification at the end**: once
`percentile_over_units` is wired into `summarize_step` there is nothing left to compare against.

**The live hazard is the threading task, not the wiring task.** Replacing the literal
`derived_metric_draws = 2000` with a resolved value is where an undeclared config silently acquires a
different draw count. The pin must cover `resample: null → 2000` **and** the absent-key case
separately, since `materialize.py` writes neither key at all.

The shape that must not move, for an undeclared-`resample` config with no `cluster_by` and no
`weight_by`:

- `aggregated.<step>.<column>.method` = `t_over_units`; **no `resample_draws` key**.
- `aggregated.<step>.<derived>.method` = `percentile_over_units`, `resample_draws: 2000`,
  `cohens_d: null`.
- `vs_baseline.<cond>.<step>.<column>.method` = `paired_t_over_units`, `cohens_d` = `cohens_dz`.
- `vs_baseline.<cond>.<step>.<derived>.method` = `paired_percentile_over_units`, `cohens_d: null`.
- `correction_level`, `family_size`, `family: {comparisons, metrics}` unchanged; Holm still ranks on
  `abs(delta)` over half the raw interval width.
- `CLAUDE.md` § The worked example's numbers — the r intervals, the delta's `[−0.007, 0.059]`, the
  `repeat_spread` std 0.014 — **must not narrow.** They were checked numerically and the file says so.

The baseline is **already partly pinned** by existing tests in `tests/test_cli.py`, so this is
*extend a pin*, not *write one*.

---

## The traps, and where each lives

| Trap | The rule |
|---|---|
| A declared `n` nulls every interval in the run, silently | `t_over_units` returns `None` below 2 units; `percentile_over_units` returns `None` below 2 units **and** below `min_honest_draws(confidence)` draws. So `resample: {n: 50}` nulls every column. The `n >= 80` floor is mandatory, and it must land **before** the wiring that honours `n` — validate-before-honour, inside the slice |
| Retiring a refusal opens a silent no-op | `resample` with no `data.units` validates clean and does nothing the moment the refusal goes. This is literally the `E-SWEEP-SAMPLE-BASELINE` failure `_check_unimplemented`'s own comment records: *"Retiring it made the shape reachable without implementing them."* **Corrected during task 7's review:** the precedent is `E-REPL-FOLD-NO-UNITS`, a near-exact twin in `_check_replication` — same `not (doc.get("data") or {}).get("units")` expression, likewise silent when the roster is declared but unresolvable. An earlier draft of this row named `E-REPL-FOLD-K` instead, which is the different `k: all`-basis-unknowable fault; that miscitation reached the task brief and then the shipped comment, so it is fixed here as well as there. **The twin does not `return` after reporting**, which settles the question of whether the roster-independent checks below the gate should still run: they should |
| A control that asserts only an absence | "A `report_by` level mints no `Member`s" and "a `summary`-step `Estimate` is never recomputed" both pass identically if nothing ran. Each needs a positive companion **in the same test**: the level *did* produce an interval; the `Estimate` *is* still present and unchanged |
| Holm's ranking quietly changing | The invariant is that Holm ranks on the point estimate over half the raw `ci95` width, **because the family often carries no p-value at all**. A resample pass that walks every metric block must not disturb it, and the test needs a mutation that changes ranking and fails something |
| A fixture whose numbers agree with the bug | Statistical fixtures are the richest habitat for this. Draw counts and stratum levels need enough distinct values that each candidate wrong answer produces a *different* result — the fixture-sizing rule H7a wrote into `CLAUDE.md` applies directly |
| `cohens_d` reintroduced for a derived metric | It stays `null`. `r` is derived by `aggregate`, so there is no per-unit value to difference. A slice touching effect sizes is exactly where someone helpfully adds one back |
| A `summary`-step `Estimate` recomputed | It is `reported: true`, outside the correction family, never recomputed. Task 12's pass walks every metric block, so this is a test H4a **owes**, not a boundary it merely respects |

---

## Task decomposition — 19

From the scoping's own enumeration. Seven schema and validation, three construction, five wiring, four
retirement/regression/residue — **plus the regression pin promoted to first**, because it cannot be
written after the behaviour changes.

1. **The regression pin** — extend the existing `tests/test_cli.py` pins to the full undeclared-shape
   above, including `resample: null` and absent-key as separate cases. Must land before any behaviour
   changes.
2. Mint the `resample.method` table in § Statistical reporting; fix § The one config file's inline
   comment to the `# a | b | c` form. Cross-document pass: § Config completeness and § Enum comments
   both apply.
3. Close the block one level in — `statistics.resample.{method,n,stratify_by}` in `envelope.py`'s
   `LEAF_TYPES`, so `stratifyy_by` reports `E-CONFIG-KEY-UNKNOWN` rather than being ignored.
   **Corrected during planning: the precedent is `data.units.measurements`, not `assign.<axis>`, and
   no closed key set is needed.** `_known_containers()` derives containers from `LEAF_TYPES` paths and
   `_check_unknown_keys` checks containers before leaves, so the three leaf entries alone make
   `statistics.resample` both leaf and container and yield the unknown-key finding with a difflib
   hint. `_check_assign_axis_keys` exists only because axis *names* are dynamic, which is not the case
   here.
4. `_check_resample` value checks: `method` against the enum, `n` a positive int, **`n >= 80`**.
5. `resample.stratify_by` names declared attributes; mints the identifier § Validation's *Resample
   strata exist* row has never had. Reuse `_check_report_by`'s declared-set shape, **not**
   `units._stratum_groups`, which is `assign`-specific.
6. The comparisons-only lower-bound warning on `n`, plus the `spec-defects.md` entry for the
   metric-count residue.
7. `resample` declared with no `data.units`.
8. `limits.min_clusters` made real — the § Validation row *Clusters enough to resample*, plus the
   one-line docstring fix miscititing it as `statistics.min_clusters`.
9. The stratified draw — construction, not wiring.
10. The stratified × clustered composition rule, stated then implemented.
11. `resample_draws` for a column metric, per decision 2.
12. Resolve the block once in `cli.command_run` and thread it through all seven read sites.
13. Column-metric percentile in `summarize_step` — unclustered and clustered, weighted and not.
14. Stratum membership from `cli` into `summarize_step`, aligned to the column's own keys.
15. A column contrast's paired percentile — the `diffs=None` and `col_keys` rules above, and a
    measurement of the per-draw `UnitTable` rebuild cost.
16. Echo the resolved `method`/`n`/`stratify_by` into `run.yaml`, including the example in
    `reference.md`.
17. Retire `E-STATS-RESAMPLE-UNSUPPORTED` — the loop entry, the `NOT BUILT` markers, and the
    feasibility doc's § Executability on this build, which is dated and must be **re-dated**, not
    edited in place.
18. `report_by` levels resample without minting `Member`s — one assertion with a positive companion,
    not a build.
19. The `init`-materializes-optional-blocks residual that `spec-defects.md` routes to H4 by name.

**Sequencing.** Task 1 first. Then the `n >= 80` floor and the threading before the column-percentile
wiring, or the first `resample: {n: 50}` gets a run whose every interval is `null` with no diagnostic.

**One constraint neither the spec nor the scoping originally stated, found while planning:
retirement must precede the threading, not follow it.** `cli` validates before it runs, and a
validate error exits before a run directory exists — so while `E-STATS-RESAMPLE-UNSUPPORTED` still
fires, **no end-to-end test of a declared `resample` can exist at all**. The plan therefore lands the
retirement once every validate-time refusal is in place and immediately before the threading, which
makes the window in which a declared `resample` validates clean but is only partly honoured exactly
two tasks wide. Retiring earlier widens that window to five; retiring later makes the wiring tasks
untestable.

**A test-fixture defect found while planning, which no scoping could have seen.** `tests/test_cli.py`'s
`_AGGREGATE_STEP` records `pred = float(i)` with no reference to `cfg`, so a **column** contrast over
it has all-zero per-unit differences — `paired_t_over_units([0.0] * 40)` returns `Interval(0.0, 0.0)`
and `cohens_dz` returns `None`. The column-contrast task's flagship assertions would have compared two
zero-width intervals, making correct and buggy indistinguishable: a fixture whose numbers agree with
the bug, in the exact shape `CLAUDE.md` warns about. The plan introduces a condition-scaled starter
step so the differences are non-zero.

---

## Out of scope, with the route

`null_test` and `p_value` · the weighted and clustered contrast families · the unpaired family and
`paired` becoming derived · `data.units.holdout` · the plugin registry and `{resolver: …}` · folds
within cells · `study`/`report`/`diff`/`freeze` — H4d, H4b, H4c, H3d, H7b, H3c-3, H8 respectively.
`W-STATS-REPORTBY-THIN`'s whole-roster gap is declined here with H4c named. A validate-time
`comparisons × metrics` bound is not deferred but **shown to be unbuildable**, and the residue is
filed rather than left silent.
