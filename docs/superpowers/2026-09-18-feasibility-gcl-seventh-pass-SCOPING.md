# Scoping: seventh pass of `feasibility-growth-chart-literacy.md`

**Measured 2026-09-18 against `publishable@d9b3b60`, the study at
`gcl-measurements@e94a5cf` (fixed at `60b14b4`), the plugin at
`publishable-growth-chart@368e520` and the plan at `growth-chart-literacy@15a7f7a`.** Every
number below is one a command printed; where a claim is someone else's it says whose.

This pass was asked a different question from the six before it. Not *what does the schema
express* but **what stands between this study and execution, and is E1 the only thing left**. The
answer is no, and the largest finding is one no reading of the four documents could have produced:
at the commit the sixth pass was written against plus two, **thirteen of fifteen configs did not
validate at all.**

## The headline, and why six passes of reading missed it

    $ for c in configs/*/config.yaml; do uv run publishable validate "$c"; done
    error E-PARAM-UNKNOWN parameters.stimulus.availability_mode
      is not a parameter of this template — did you mean `stimulus.height_availability`?

Thirteen times, once per screening arm. `stimulus.availability_mode` was added at
`gcl-measurements@e94a5cf` to `construct.py`, to `step02_construct`, and to all thirteen configs
that declare a deployment — and to `growth_screen.parameter_spec` in none of them. Only `e02` and
`e06`, the two arms on the `growth_label` template, still validated.

**275 tests passed over it**, and that is the more useful half of the finding. The study's suite
exercises the constructor through its own Python signature; **nothing in it had ever run `validate`
over a config**, so the declaration side and the reading side were never held together by a test.
This is `design-principles.md` § Every declarable field has a reader read from the other end: the
reader existed and the declaration did not. `tests/test_configs.py` now closes it, and the mutation
was run rather than assumed — removing the `Param` again turns 13 of its cases red, and restoring it
returns 292 passed.

**The sixth pass could not have caught this and the seventh could not have missed it**, which is the
transferable part. The sixth pass re-quoted fourteen config blocks against the live files — a text
diff, the right instrument for the question it asked. A block can be byte-identical to a document
and still be refused by the tool the document describes. *Quoting a config is not validating one.*

## What was measured

| | measured | previous claim | |
|---|---|---|---|
| configs | **15** | 14 (cost table), 15 (sixth-pass block) | the doc contradicts itself; `e05e` is real |
| `validate`, before the fix | **2 of 15** clean | "validate accepts 14 of 14" | false at this commit |
| `validate`, after | **15 of 15**, 0 errors | — | 6 × `W-STATS-FAMILY`, 3 × `W-DATA-CLUSTER-UNDECLARED` |
| conditions | **64** | 62 | +2, all `e05e` |
| executions | **479** | 462 (§Executability), 450 (cost table) | +17, all `e05e`; the cost table never took the canary |
| unit-executions | **113,100** | 109,700 | +3,400, all `e05e` |
| study suite | **292 passed** | 275 | +17 from the new file |

**The other fourteen reproduce the sixth pass exactly** — 62 / 462 / 109,700 — so the whole delta is
one arm's row. That is the check that the re-measurement is of the same thing.

## Six findings, in the order they matter

### 1. E5e was declared, coded, tested, and had no roster

`configs/e05e-missingness-swap/` exists, `construct.py` implements `availability_mode: fixed_count`
for it, `tests/test_construct.py` pins both of the wrong implementations that preceded it — and
`tools/example_inputs.py` knew fourteen arms, so `data/e05e-missingness-swap/` did not exist and the
config earned `E-DATA-UNREADABLE` on top of the parameter error. Fixed: the generator knows fifteen.
The arm prints **SHORT by 38** — 200 planned against 238 needed — and clears the *uncorrected*
margin at 197, so the shortfall is the Holm family of 2 and nothing else. The plan puts E5e in the
{E5a–e} family of five and [a family cannot span runs](spec-defects.md), so neither number is the
plan's own.

### 2. E3's completed run is of a design its own subject abandoned

`run_2026-09-12T23-51-56Z_d50131d` says `completed`. Its embedded `config.yaml` carries

    source: synthetic_physiology / physiology: concerning / schedule: typical

and the live config reads `observed / as_recorded / as_recorded`. Different `parameters_hash`.
**E3 has not executed as currently specified**, and the 27,000 metered requests are unpaid rather
than paid. The reason the design changed is in the config's own comment and is worth carrying: a
single-valued physiology leaves truth with no variation *in the only place a metric is computed*,
so the first run returned nine flag rates wearing the name `accuracy`.

### 3. E1 gates E3, or it does not, and three passages disagree

This is the finding the whole pass was commissioned to produce, and it cannot be closed here.

| says | where |
|---|---|
| "**Depends on:** Nothing — it is the root of the core" | plan §E3 header |
| "600 constructed trajectories … **validated by the E1 panel** under that section's decision rule" | plan §E3 Sample |
| "E3 and E8 draw from them and **inherit**"; "the panel sits on the critical path to *every* Layer A arm" | plan § Dependency Structure |
| "the generator is corrected **before any arm using synthetic stimuli is run**" | plan §E1 realism failure |
| "**Blocks:** The *interpretation* of E4b, E5b and E9. Nothing else." | plan §E1 header |

The feasibility analysis inherits the split rather than resolving it: § E3 says "E3 inherits that
validation and **waits on it**", and § What remains says "E3 … **depends on nothing** … and can be
run."

**Which reading is right is the study author's call, and it decides the schedule of everything.**
Under the Sample/Dependency reading the panel is upstream of E3 and therefore of all of Layer A, and
the only arms that can run before clinicians read anything are E2, E4a and E6 — Layer C, real
patients, no constructed stimulus. Under the header reading E3 runs now and E4a/E5c/E5d follow it.
A feasibility analysis states the contradiction; it does not pick the tidier side.

### 4. Every downstream arm pins a format E3 is supposed to select

`e04a`, `e05c`, `e05d` — and eight more — carry `serialize: {features: derived, format:
markdown_table}` as literals. The plan's §E3 decision rule says the winner **on the selection half**
becomes the standard serialization for E4–E10. So `markdown_table` in those files today is a
placeholder wearing the shape of a result, and any arm run before E3 reports is run at a format that
E3 may not choose. `features: derived` is different and correctly so — fixed a priori, registered
2026-09-12, and not a selection axis.

### 5. The generator ships with two unmet criteria, not one

Checked because the authorization to run E3 was conditioned on the generator being final. The
companion manuscript states it plainly — "**Two criteria fail, and the second was added the same day
the count rose**" — and they are not of one kind:

| criterion | reads | registered? | disposition |
|---|---|---|---|
| share of recorded falls > 3 cm | −19.02% (se 0.89%) | **yes**, item 8 | reported as a limitation with a mechanism |
| share of curves with per-curve gap CV < 0.02 | **+52.18%** (se 0.29%) | no — added 2026-09-17 | **none recorded** |

The second is a **schedule** row, and §Cross-Cutting has E3's items drawing their visit ages from the
generator's schedule model — only E4b and E7 use real scaffolds. So it reaches E3's own stimuli, it
sits on E5c's H1 by name ("spacing regularity"), and it is the artifact class **E1's realism check is
powered to detect**: the generator makes 2.2× as many effectively-perfect metronomes as the cohort
(0.175 against 0.080 at CV < 0.01). A panel that separates synthetic from real on spacing alone
fails the realism check, and the check's pass condition is failure to reject.

**Two sentences still say "the single miss"** and both are now false: the plan's `CLAUDE.md` row for
`growth-measurement-model.md`, and that manuscript's **own abstract** ("35 criteria … of which 34
fall within 10% … The single miss"), three paragraphs from the block that says two fail.

### 6. The first test to call core's loader broke a sibling, and core is right

`tests/test_configs.py` made `test_the_plausible_range_fallback_barely_moves_the_gross_error_rate`
fail with `('height', 0)`. Diagnosed rather than patched: `load_experiment` purges the entrypoint's
root package from `sys.modules` and re-imports it fresh — deliberate, documented in
`base_experiment.py`, and correct, since two projects in one process can declare the same package
name. The cost lands on a test process, which imported `growth_chart` first: afterwards the name
resolves to a **second module object**. The sibling test tags a channel by `table is
module._stature()`, reading `module` out of `sys.modules` inside the test body while the function
under test came from the top-level import — an identity proxy for a structural question, and the
fragility predates this pass. What this pass added was the first test in that suite that ever calls
core's loader. Containment sits at the site that provokes it.

**This is not a core defect and the entry is here so that the next reader does not file one.**

## What executed

**E2 and E6**, at `publishable@d9b3b60` / `gcl-measurements@60b14b4`, both `status: completed`, both
on rosters extracted from the real cohort on 2026-09-12:

| | verdict | quantity |
|---|---|---|
| `e02` | `supported: true`, `verdict_rests_on: reported` | AUROC **0.5786**, ci95 [0.5436, 0.6153], n = 1000 units, 0 failed |
| `e06` | `supported: true`, `verdict_rests_on: computed` | count contribution to AUROC **+0.0636**, ci95 [0.0251, 0.1018], `paired_percentile_over_units_clustered`, n_paired 562 over 286 clusters |

Both carry a populated `findings:` block holding the `W-STATS-FAMILY` the run raised. `e06` reports
38 of 600 units `ineligible` and 0 `failed`.

**Nothing metered ran.** The four candidates — E3 27,000, E4a 3,000, E5c 1,500, E5d 3,000 — are held
behind findings 3, 4 and 5, and the author's ruling on finding 5 is **fix the CV row first**.

## What the deployment probe answered

`dry-run` on every screening arm reports `W-APPARATUS-UNANSWERED` for `system_fingerprint` and for
**nothing else**, once per condition. The plugin's probe leaves a fact unanswered rather than raising
when a metadata read fails, so `model_version` answering is core's own report that the Azure
deployment resolved and the credentials are live. `system_fingerprint` is returned only on a
completion and is `None` by design.

## What was not measured, and is therefore not claimed

- **The fifteen config blocks were not re-quoted against the live files.** The sixth pass did that at
  `2ff922a`; two commits have landed since and one of them edited thirteen configs.
- **No arm's roster was regenerated except `e05e`.** The other fourteen are inputs to runs already on
  the record and `input_manifest_hash` covers them.
- **`e05e` has never executed**, in this tree or anywhere. It validates and dry-runs.
- **The plan repository was read, not run.** Every figure attributed to it above is quoted from its
  own text at `15a7f7a`, including the two verification numbers in finding 5.

---

## Appended 2026-09-18: finding 5 was acted on, and the criterion is closed

The author's ruling on finding 5 was **fix the CV row first**, so this pass did, in the plan
repository. Recorded here because the finding is above and a filing that says "carried" is not a
filing.

**`cv_under_02` +52.18% → −2.44%; the generator goes 34/36 → 35/36**, at n = 20,000 over all 36
seeds, where the control reproduces the manuscript's published figures to the digit. `over3` is
unmoved at −19.30% against −19.02% and remains the single miss.
`growth-chart-literacy@d4f2e5c`, with `decisions/2026-09-18-late-visit.md` carrying the derivation.

**The preceding refit's conclusion was right and its scope line is what made the fix findable.** It
measured 48 cells and concluded the row could not be closed — *a frontier in `SCHED_SLIP_MU` ×
`SCHED_SLIP_SD`*, explicitly not a claim that the criteria are irreconcilable. `cv_under_02` and
`near` are both consequences of one per-child slip, so their gradients sit 3.8° apart and no setting
of that mechanism separates them. **A second mechanism does.** The model had one interval-level
irregularity — `SCHED_SKIP`, which doubles an interval — and a missed visit is not the only way a
schedule goes irregular. A visit attended *late*, at 1.26× the period (15.7 months), leaves `near`'s
0.8–1.2y denominator instead of degrading its numerator, and sits under `over18`'s 18-month
threshold, which a doubled interval does not. Measured rate **0.047** against the ≤0.097 needed.

**The check that is not a fit.** The peripubertal band is unfitted, unscored by `verify`, and its
targets entered no objective here — and it improves anyway, 17 rows outside to 14, its own
`cv_under_02` going +111% to +34%. A parameter set tuned to one band's row has no reason to move
another band's version of it by 77 points.

### Three things this half of the pass is worth reading for

**1. A branch written the obvious way destroyed its own control, and only looking at it caught that.**
The first implementation read `elif rng.random() < SCHED_LATE`, which costs a second draw whenever
the skip does not fire and re-randomises every later interval of that child. At `SCHED_LATE = 0` the
control then differed from shipped by a whole fresh sample: `over3` moved **5.8pp** and two rows
crossed the band, on a change that does nothing. Rewritten as one uniform against two thresholds it
reproduces the stream bit for bit and the control comes back at 34/36 with `over3` −21.55% exactly.
This is *a control asserting only absences* from `CLAUDE.md` § Writing checks that can fail, in its
other form: **a control that cannot reproduce is not a control**, and nothing would have failed —
the scan would simply have compared every candidate against a baseline that was already a different
sample.

**2. The acceptance rule's condition 5 is unsatisfiable by the status quo.** Conditions 1–4 are to
hold on both held-out pools, and their `DRIFT` baselines and `over3` floor are **fit-pool** figures.
Measured: the shipped parameters fail there — `over3` −22.85% on held-out A against a −22.44% floor,
and on held-out B `f_long` reads 13.89% against the fit pool's 8.75%, past the 9.5% cap.
`slip_scan.check_rule_satisfiable` asserts the rule against the status quo **on the fit pool only**,
which is the same fault that assertion exists to catch, one instrument along. Nothing here rests on
condition 5; the decision rests on Phase 3, where control and candidate share 36 seeds. Recorded and
not repaired — the rule belongs to the refit that wrote it.

**3. The fix does not reach an E3 run out of the measurement tree.** Those rosters take their visit
ages from `tools/example_inputs.py`, which draws its own gaps; the plan's whole `SCHED_` family is
`NOT_PORTED` there for the stated reason that the tree draws no schedule. So the corrected generator
reaches the *manuscript's* E3 stimuli and not that tree's, and an E3 run there would exercise the
pipeline rather than the fix. **This is the fact that should decide whether 27,000 requests are worth
issuing**, and it is not one the earlier authorization could have accounted for.

### What this does not settle

- **`over3` stands**, on its existing disposition as a registered, reported limitation.
- **Two parameters are new and one moved**, so preregistration item 8 makes this a registration
  event. That is the study's to record and is named in the decision record rather than done here.
- **Findings 3 and 4 above are untouched.** The E1-gates-E3 disagreement and the placeholder
  serialization are decisions, not defects, and neither is this pass' to make.
