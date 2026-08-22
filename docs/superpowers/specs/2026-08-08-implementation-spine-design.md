# The implementation spine (S1)

**Status:** approved.
**Deliverable:** code. This is the first slice that puts an implementation in a repository
that has until now been specification only — `src/publishable/`, `tests/`, and
`pyproject.toml` land here, and `CLAUDE.md`'s "specification only, no implementation"
premise is rewritten to match.

The four documents remain normative and lead. Code follows them; where code cannot follow
them, the document changes first.

## Why this is a slice and not the whole thing

The four documents specify, at minimum: a config materializer and an ~85-check validation
engine, sweep expansion across six modes, unit resolution with collapse, holdout,
allocation, clustering and weights, a four-scope execution planner with resume and
locking, an append-only artifact layer with a writer registry, a statistics engine with
eight named interval constructions plus corrections and permutation tests, three hashes
with git, uv, manifest and apparatus provenance, hypothesis evaluation, studies,
reporting, four plugin registries, and sixteen CLI commands.

That is a dozen-plus subsystems. A single implementation spec over it would be too vague
to build from, so the work is decomposed and each slice gets its own spec, plan, and
implementation cycle.

### Purpose and acceptance bar

The implementation is built **as a reference implementation first, then hardened into
v0.1.0**. The reference implementation's job is to find where the specification is wrong,
underspecified, or unimplementable — the way `feasibility-llm-growth-studies.md` did from
outside, but from inside.

It is done when **the worked example runs end to end**: `cohort-pilot`, 3 conditions ×
5 seed repeats, 240 units resolving to 228 completed and 12 failed, with the reported
intervals falling out of the code rather than being asserted into it.

**The acceptance test is structural and bounded, not exact.** The pinned intervals in
`CLAUDE.md` were checked against a synthetic 228-unit table that is not in this
repository, so exact reproduction would mean reverse-engineering a dataset to hit three
interval targets — a test that re-breaks whenever the bootstrap draw order changes. The
test instead asserts what is actually specified:

- the four attrition counts: `resolved: 240`, `completed: 228`, `failed: 12`;
- `basis` per metric, and the `method` name recorded beside each interval
  (`percentile_over_units`, `paired_percentile_over_units`);
- `paired: true` and a recorded `n_paired`;
- Holm rank order — kendall rank 1, spearman rank 2 — and `family_size: 2`;
- `cohens_d: null` for the derived `r`;
- `repeat_spread` present, labelled `kind: seed`, and outside the interval;

together with the bounds `CLAUDE.md` states as constraints: kendall's half-width above
0.087, the delta's half-width at or above ≈0.033, and each condition's own interval
markedly wider than the delta's. Point estimates are not asserted, and the documents'
numbers stay as they are — illustrative and vetted. No worked-example churn.

### The slices

| Slice | Adds | Done when |
|---|---|---|
| **S1 Spine** | This document | Scaffold-then-run works; `run.yaml` carries three real hashes |
| **S2 Units** | Resolution from `index.csv`, frozen `Unit`, the `io.units` contract, `io.record`, `units.parquet`, `io.skip`, the four attrition counts, `max_failed_fraction`, **per-unit repeat collapse**, the `basis` split, `t_over_units` | 240 resolve, 12 fail, `n` reports 228, a column metric carries an interval |
| **S3 Sweeps** | `baseline` + `grid`, condition labels and the artifact tree, `sweep.yaml`, `batch` and `fold` kinds, nesting, `order: randomized`, `read_upstream`/`read_condition` and the direction checks | 3 × 5 = 15 executions in the right tree |
| **S4 Statistics** | Template `aggregate`, derived metrics, `percentile_over_units`, `paired_percentile_over_units` and `n_paired`, `vs_baseline`, Holm and family sizing, the `cohens_d` rule, `repeat_spread`, `Estimate` | **The acceptance test passes** |
| **S5 Pre-registration** | Hypothesis evaluation, `verdict_evaluated_on`, `verdict_rests_on`, exploratory marking | The worked example's `h1` renders its verdict |

S5 ends the reference implementation and is followed by a **checkpoint**: every entry in
the spec-defect ledger is resolved into the four documents, and both consistency passes
from `CLAUDE.md` run once over the result. Hardening slices follow, named below.

### The hardening slices

**Amendment, 2026-08-11 (S5 checkpoint, task 16).** Until now the hardening work was one
prose sentence — "the full validation engine, the remaining sweep modes, allocation,
holdout, folds, clusters and weights, contrasts, `resample`, `null_test` and `report_by`,
plugins and the apparatus, studies, `report`, `diff`, `freeze`, `reproduce`, `draft`,
`resume`, `demo`, and `docs`". That sentence named no slice, so no ledger entry could
route to one, and the ledger's deferrals fell back on *descriptions* of a slice — "the
slice that next touches `correction.py`", "whichever slice next touches `validate`'s
import path". Each of those descriptions was satisfied several times over and none was
honoured; that is the failure this amendment exists to close.

The set below is **closed and derived from that sentence**, plus two buckets the sentence
omitted and residuals need — hashes, and recorded-column integrity. It is deliberately
coarse: a slice minted to hold exactly one ledger entry is a description wearing a name,
and would re-create the same failure. A residual that fits none of these is an argument
for amending this table, not for inventing a tenth name in the ledger.

| Slice | Owns | Order |
|---|---|---|
| **H1 Validation** | The full ~85-check engine; `validate`'s type envelope over scalar leaves; the validate-time `E-` registry; the import-path envelope | first — everything below is easier to test behind a complete `validate` |
| **H2 Sweeps** | `ablate`, `groups`, `paired`, `sample`; per-cell baseline expansion, and the six § Validation checks blocked behind those modes | after H1 |
| **H3 Units** — **four slices, see below** | `allocation`, `assign`, `groups`, `holdout`, `folds`, `cluster_by`, `weight_by`, `measurements`; eight of the nine refusals; the `allocation.json` artifact and `provenance.allocation_hash` | after H1 and H2 |
| **H4 Statistics** | `statistics.resample` and `null_test`; contrast, correction and `report_by` hardening; every `repeat_spread` and per-slice `aggregate` recompute debt; **the weighted contrast family** — `paired_t_over_units`, `paired_delta_of_derived`, `paired_percentile_of_derived` — retiring H3a's `E-DATA-WEIGHT-CONTRAST` | after **H3b + H3c** — not after all of H3; it blocks on `cluster_by`, `allocation` and `groups` only |
| **H5 Artifacts** | `units.parquet` integrity: non-numeric recorded columns, cross-row type unification, and the reserved-column namespace `finalize` merges into | independent; may land any time after the checkpoint |
| **H6 Hashes and provenance** | `code_hash`'s `.gitignore` awareness and its zero-file case, `parameters_hash` normalization against `parameter_spec`, and the purity rule that forced both | independent |
| **H7 Plugins and the apparatus** | The four registries, entry-point resolution, probes and the change gate, `secrets` / `requires_env` | after H1 |
| **H8 Studies and reporting** | `study new`/`add`, `report`, `diff`, `freeze`, lineage and upstream chains | after H4 |
| **H9 Reproduction and the other modes** | `reproduce`, `dry-run`, `draft`, `resume`, `demo`, `docs` — every command that is a second entry into `run`'s own sequence | last — `reproduce` is what reads the environment back, so it decides the unresolved lockfile questions |

**AMENDMENT, 2026-08-22, recording two splits this table never received.** Neither the **H8** row nor the
**H5** row above was amended when its slice split, and both splits are load-bearing enough that a reader
of this table alone would mis-scope the work.

| Row | Split into | Where the split was measured |
|---|---|---|
| **H8 Studies and reporting** | **H8a** lineage and `io.reuse_from` (10) · **H8b** `diff` and `freeze` (8) · **H8c** `report` and `study`, including `BaseReport` (12) — all three merged | [`H8-SCOPING.md`](../H8-SCOPING.md) — 30 tasks against this one-row charter |
| **H5 Artifacts** | **H5a** write-side integrity and the reserved-column namespace (9) — merged 2026-08-22 · **H5b** non-numeric columns downstream to `aggregate` (10) | [`H5-SCOPING.md`](../H5-SCOPING.md) — 19 tasks, split on the write/downstream seam |

H5's seam is worth stating here rather than only in its scoping, because it decides the order: **H5a is
`artifacts.py`, `units.py`, `coercion.py`, `validate.py`, and adds refusals for configs that are corrupt
today; H5b is `stats.py` and `cli.py`, and changes what an existing key — `aggregated` — may contain.**
This project has ruled twice that an additive change to a shipped surface is fine and changing what an
existing key reports is not (H7d Part B, H8b Decision 7), so the behaviour-change exposure is **H5b's
alone**, and H5a went first.

**The general point, which is why this amendment exists at all.** Both splits were recorded in `CLAUDE.md`
and in the slice's own dated scoping, and **neither reached this table** — so the table read as a nine-row
charter while the work had become fourteen slices. A scoping expires and a spec does not, but a spec whose
table is never amended stops describing the plan it exists to hold.

### Order, amended against outside evidence

**AMENDMENT, 2026-08-14, from an executability measurement of
[`docs/feasibility-llm-growth-studies.md`](../../feasibility-llm-growth-studies.md).** All nine of that
analysis's experiments (E1–E6, C1–C3) were run through `validate` on the build at the H3c-2 merge, three
passes each. **Zero execute today.** The measurement changes the remaining order, because the slices
scheduled next unblock none of them.

**What blocks the nine**, by frequency, with the plugin assumed to exist and only *core* declarations judged:

| Blocker | Hits | Owner |
|---|---|---|
| `E-TEMPLATE-UNKNOWN` — no template resolves | **9/9** | **H7** |
| `E-STATS-RESAMPLE-UNSUPPORTED` | 8/9 | H4 |
| `E-DATA-HOLDOUT-UNSUPPORTED` | 6/9 | H3d |
| `E-DATA-WEIGHT-CONTRAST` — `weight_by` × a comparison | 3/9 | H4 |
| `E-STATS-NULLTEST-UNSUPPORTED`, `E-DATA-ALLOCATION-CONTRAST`, `E-DATA-CLUSTER-CONTRAST` | 0/9 | — |

`E-STATS-RESAMPLE-UNSUPPORTED` is 8/9 rather than 9/9 because E5 declares `statistics.resample: null` and
the guard is truthy. `E-DATA-RESOLVER-UNSUPPORTED`'s own message names the **plugin registry** as why it
cannot execute, so it is cleared by full H7 or by rewriting the roster to a table source — not by H7a.

**CORRECTION, same day.** An earlier version of this amendment said H7 gates all nine, because
`get_template` reads a builtin dict and `entry_points` is read nowhere. The first half is true; the
conclusion was wrong. `reference.md` § Templates gives a template **three** homes, and the third does not
go through the plugin system: *"the first two are registered through an entry point, and the third — which
is installed nowhere and distributed to nobody — is **discovered by path from the fixed layout**, making
its `@register_template` argument the whole of its registration."*

**So the gate is the template registry, not the plugin system**, and the template registry has a smaller
solution than H7 as chartered. What a project-local template needs, none of it built:

| Missing | Evidence |
|---|---|
| `register_template` exported from `publishable` | absent from `src/publishable/__init__.py` |
| path discovery of `templates/**` | `get_template` reads `_BUILTIN` only; source mentions `templates/` just in the dirty-tree check and `code_hash` |
| `generate template` | `generate` accepts `experiment` and `step` only |

Call that **H7a**. It is a subset of H7's "four registries" and needs none of entry-point resolution,
probes, or the change gate. With it, an experiment carries its own template in `templates/`, its steps in
`src/` (`generate step` already exists), and a table roster — and runs without the plugin system.

**What the analysis loses without full H7**, and it is not nothing: its `patient_trajectory` **resolver**
and `llm_deployment` **probe** are genuinely plugin artifacts and are not path-discoverable. The resolver
is replaceable by a table source — the measurement proved a config validates that way — but that is a
change to the design, not a free substitution, since the roster genuinely comes from a trajectory store.
The probe is effectively unbuilt in core: `apparatus_probe` and `apparatus_facts` exist as declarable
`BaseTemplate` attributes and **nothing reads them**, and there is no `Apparatus` type and no
`register_probe` — so no scheduling recovers it.

**H3c-3 and H3d were next and unblock nothing between them.** No config in the analysis declares
`sweep.groups`, `allocation: between`, `assign`, `cluster_by`, `measurements` or a `fold` repeat — so
H3a, H3b, H3c-1 and H3c-2 together unblock **none** of the nine. The one recently built thing any of them
touches is `weight_by`, and that now *fails*, because the slice that made it real also refused it beside
a contrast.

**SECOND AMENDMENT, 2026-08-14, from five scoping measurements** — one per remaining slice, each run
against the code rather than against its charter. Every charter was stale, all in the same direction:
**H4 is ~54 tasks not one slice, H7's remainder is 38, H3d is 16 against a charter that said "3 rows",
and H3c-3 is 17 against a charter that said 6.** Three of the five change the order.

**The three findings that move it:**

1. **H4 splits four ways, and only the first two touch the evidence.** H4a `resample` honoured (15
   tasks, unblocks 8 of the nine) · H4b weights and clusters through contrasts (14, unblocks 3) · H4c the
   unpaired family (12, unblocks **0**) · H4d `null_test` (13, unblocks **0**). `statistics.resample` for
   the unclustered column case is **wiring, not construction** — `percentile_over_units` and
   `percentile_over_units_clustered` are built, tested, and have **zero production callers**. Meanwhile
   `p_value` appears nowhere in `src/`, so `null_test`, `p_value_corrected` and `fdr_bh` are unbuilt end
   to end. **C1–C3 declare `weight_by`, a `baseline` and `resample` in one config, so H4a and H4b's
   weighted half must ship together or H4 delivers zero of nine.**

2. **H3d before H3c-3 is survivable, and the reason is a refusal rather than an argument.** A
   cells-unaware holdout is *silently* wrong — a roster-wide `frac` gives arms unequal test shares, and at
   worst a cell with zero test units. But `holdout` × `sweep.groups` is knowable **from declarations
   alone**, so it is refusable under this repo's own siting rule, exactly as `E-DATA-WEIGHT-CONTRAST` and
   `E-DATA-ALLOCATION-CONTRAST` are. Cost against the evidence driving the reorder: **zero** — all nine
   feasibility configs declare `groups: []`, `allocation: within`, `assign: {}`.

3. **H3c-3 contains a 3-task refusal that closes a live defect, and 14 tasks that can wait.** Reproduced
   at HEAD: 15 units in clusters 7/3/3/1/1 split into arms 8/7 with `k: 5` validates clean, because
   `fold_basis` answers 5 over the **whole roster** — while the realized per-arm folds are `[7,1,1,0,0]`
   and `[3,2,1,0,0]`, **two empty folds in each arm**. `groups` + `between` + `fold` has run roster-wide
   folds since H3c-1, and nothing pairs allocation with a repeat kind. Two normative documents state the
   unbuilt per-cell behaviour in the **present tense, unmarked** — the same conflation class as `162e180`.
   **Refusing `fold` beside `allocation: between` closes the claim and the leak in 3 tasks**; the
   remaining 14 build real per-cell folds and unblock nothing until a design asks for both.

**Amended order:**

| # | Slice | Tasks | After it, of the nine |
|---|---|---:|---|
| 1 | **H7a** project-local templates | 15 | 0 — but every config resolves a template for the first time |
| 2 | **H4a** `resample` honoured | 15 | 0 |
| 3 | **H3d** fixed holdout, **plus H3c-3's 3-task cell refusal** | 16 + 3 | **6** (E1–E6) |
| 4 | **H4b** weights and clusters through contrasts | 14 | **9**, with a table roster |
| 5 | **H7b** registries, entry points, resolvers | 17 | **9 as written** |
| — | then, in any order: H7c secrets (7, depends on nothing) · H4c unpaired (12) · H4d `null_test` (13) · H7d apparatus (14, after H7b) · H3c-3's remaining 14 | | |

**Why H3c-3's refusal rides with H3d rather than waiting.** H3d otherwise adds a *second* false cell
claim to the documents — a holdout that ignores cells alongside folds that ignore cells — and the two are
one sentence and one check apart. H3c-3's own measurement recommends it.

**What H3d must be chartered to do up front**, or H3c-3's retrofit stops being small: perform the
**phase hoist** (arm plans are currently resolved *after* `resolve_repeats` and `partition_units`), and
express its split as *"partition within each cell to declared target proportions"* rather than as a
roster-wide fraction. Both are cheap now and expensive later.

**Two things the scopings found that no charter owned.** `plugin new` and `plugin_scaffold.py` belong to
no slice — chartered into H7b. And a plugin **writer's reader is unregistered**: there is no
`publishable.readers` entry-point group, so a plugin can write an artifact core cannot read back.

**A correction to the first amendment.** It said H7a needs *"export `register_template`, discover
`templates/**` by path, add `generate template`"* and implied that was small. It is **15 tasks**, because
discovery inverts the spec's own argument for entry points — § Creating a plugin justifies them by
`validate` resolving a name *"without importing a line"*, while a local template's decorator **is** its
registration, so `validate` must import every file in `templates/`. That is not a greenfield breach, but
it widens a documented promise and H7a owes the sentence.

**Amended order for what remains: H7a → H4a → H3d (+3) → H4b → H7b → the rest.**

**Two columns, because the nine declare a resolver.** *As written* means the configs exactly as the
analysis prints them, `from: {resolver: patient_trajectory}` included — which draws
`E-DATA-RESOLVER-UNSUPPORTED` until **full H7**. *With a table roster* means the one design substitution
the measurement proved validates. Stating a single count would repeat the spec-claim/build-fact
conflation this amendment exists to correct.

| After | As written | With a table roster | Why |
|---|---|---|---|
| H7a | 0 of 9 | 0 of 9 | a project-local template resolves; the statistics blockers remain |
| H7a + H4 | 0 of 9 | **3 of 9** (C1–C3) | `resample` lands and the weighted estimators lift `E-DATA-WEIGHT-CONTRAST` |
| H7a + H4 + H3d | 0 of 9 | **9 of 9** | `holdout` lands; E5 also needs its own YAML corrected, which is not a core change |
| + H3c-3 | 0 of 9 | 9 of 9 | unblocks none of the nine; completes the cell machinery |
| + H7 (the rest) | **9 of 9** | 9 of 9 | entry points and resolvers — this is the column that clears `E-DATA-RESOLVER-UNSUPPORTED` |

**So the order is unchanged by the re-assessment, but the claim is.** Nothing runs the nine *as the
analysis wrote them* until full H7. H7a → H4 → H3d is still right, because it delivers a usable tool to
anyone willing to source a roster from a table — which is most projects — and because each of those three
is small next to H7. But "9 of 9" was never true without a caveat, and the caveat belongs in the table
rather than in a paragraph someone reads later.

**The cost of this reorder, stated rather than buried.** H3d was placed last among the H3 slices because
it *"consumes both prior rules"* — whole clusters **and** cells — and H3c-3 is what makes cells real. Moving
H3d ahead of H3c-3 means it ships a holdout that respects clusters but **not** cells, and H3c-3 must then
retrofit it. That is acceptable only because no experiment in the analysis declares a group axis, so the
combination is unreachable in the evidence driving the reorder. **H3c-3 inherits the retrofit as a named
deliverable**, not as a discovery.

**What this does not change.** The dependency that put H3a before H3b before H3c is untouched, and all four
have landed. The reorder applies only to what remains.

### H3 decomposes into four slices

**AMENDMENT, 2026-08-12, from `docs/superpowers/H3-SCOPING.md`.** The row above originally
chartered H3 as one slice owning "registered resolvers — the whole `E-DATA-*-UNSUPPORTED`
family", after H1, against 25 blocked § Validation rows. Four parts of that were wrong, and
the scoping proved each by measurement rather than estimate:

- **It is not one slice.** Nine refusals, **26** blocked rows, ≈385 lines of `reference.md`
  across 8 sections, 5 wholly-blocked designs in `experimental-designs.md`, a new run
  artifact, 4 `W-` identifiers to mint, and ≥5 core signature changes — against H1's 12
  tasks and H2's 9.
- **The count was 25 and the membership was off by three each way.** H1 missed rows 229 and
  269 (both need a group axis) and the `cluster_by` dependency in 240/241; it
  over-attributed 257, which is genuinely shared with the resolver.
- **`E-DATA-RESOLVER-UNSUPPORTED` is H7's, not H3's** — `validate.py`'s own message names
  the missing plugin registry as the reason it cannot execute. Moving it is why the
  headline is 26 rather than 30, and it is why the row above says *eight* of the nine.
- **"after H1" understates the order.** H3 also closes H2's two remaining rows, so it is
  after H1 *and* H2. And the charter named no artifact while H3 owes one.

| Slice | Owns | Rows | `partition_units` |
|---|---|---|---|
| **H3a Weighted and technical units** | `data.units.weight_by`, `data.units.measurements` | 4 | never touches it |
| **H3b Clustered units and partitions** | `data.units.cluster_by`, `fold.stratify_by`; retires `E-REPL-FOLD-STRATIFY-UNSUPPORTED` | 4 | rewrites it for clusters |
| **H3c Allocation, arms, assignment** — **three sub-slices, see below** | `allocation`, `sweep.groups`, `assign`; owns `allocation.json` and `provenance.allocation_hash`; retires `E-SWEEP-GROUPS-UNSUPPORTED`, `E-DATA-ALLOCATION-UNSUPPORTED`, `E-DATA-ASSIGN-UNSUPPORTED` | 15 owned, 1 shared, **2 already implemented that it breaks**, 2 to write from nothing | **does not rewrite it.** Cells attach at `fold_basis` and the caller's loop |
| **H3d Fixed holdout** | `data.units.holdout` | 3 | consumes both prior rules |

**Order a → b → c → d, and the reason is `partition_units`:** each slice touches it exactly
once, in the order that never rewrites an earlier slice's rule. H3c before H3b would
partition for cells first and for clusters second, rewriting the same function twice.

**Two items nobody had counted, both owned by H3c:**

- **`sweep.AXIS_MODES` must be split.** One tuple serves three roles today.
  `reference.md` § Expansion modes puts `groups` in the condition product while `sweep.py`
  keeps it out of `_axes` so `ablate × groups` stays legal — both correct today, and
  incompatible the moment `groups` expands.
- **Three whole-leaf `envelope.py` blocks go live one per un-refusal.** `measurements`,
  `holdout` and `assign` are typed as a bare `dict`; `reference.md` calls that gap "latent
  rather than live" *because* they are refused, so each un-refusal makes its own gap live
  and edits that passage.


### H3c decomposes into three sub-slices

**AMENDMENT, 2026-08-13, from `docs/superpowers/H3c-SCOPING.md`.** Measured at **36 tasks**, against
H3a's 12 and H3b's 13. The charter was wrong on three counts and silent on four more.

| Sub-slice | Owns | Tasks |
|---|---|---|
| **H3c-1 Arms read** | `sweep.groups` expanding; `assign.method: by_attribute`; `allocation.json` and `provenance.allocation_hash`; the `AXIS_MODES` split H2 deferred; the two rows H3c breaks. `random`/`blocked` refused **as a method value** | 20 |
| **H3c-2 Arms drawn** | `assign.method: random` and `blocked`, and the seeding rule | 10 |
| **H3c-3 Folds within cells** | `k` bounded per cell; the empty-fold-per-arm case | 6 |

**The discriminator:** `by_attribute` reads an arm from a column and is runnable and recordable on its
own; `random`/`blocked` must *draw* one, which is a second mechanism with its own seeding and its own
artifact semantics. Refusing a **method value** while honouring the block is the precedent H3a set
with `E-DATA-WEIGHT-CONTRAST` and H3b with `E-DATA-CLUSTER-DERIVED`.

**Four things the charter never named, each measured:**

- **A cell's values become parameters.** `runner.resolve_condition_cfg` writes every `Condition.values`
  key into `parameters`, so a `{arm: control}` cell yields `parameters.arm = 'control'` — a parameter
  no template declares, flowing into `parameters_hash`. Verified against a control. **Nine sites read
  `Condition.values`.** This is the largest item in H3c.
- **`assign.<axis>.from` is unreachable by `CONSTANT_COLUMN_RULES`**, whose comment names H3c by name.
  A `measurements` collapse would **invent an arm membership** — H3a's shipped defect a third time, and
  worse, because it changes the design rather than a weight.
- **`design_digest` covers `data.units` wholesale, including `assign.seed`**, which § What `auto`
  derives from explicitly excludes.
- **There is no `resume` command** (`OPERATION_COMMANDS = {"validate", "run"}`), so `allocation.json`'s
  "read rather than re-drawn on resume" has no reader; and § What `study add` redacts never names it,
  though it is the one artifact that is a list of **unit identities**.

**`partition_units` is not rewritten again.** H3b's rewrite stands; cells attach at `units.fold_basis`
as a per-cell minimum and at the caller's loop. Measured: the uneven fixture at `k = 5` gives folds
`[7,3,3,1,1]` over the whole roster and `[7,1,0,0,0]` for one arm — three empty folds, `validate`
silent because the basis is over the roster. That is H3c-3's, and it is the same shape as H3b's
stratified empty-fold finding.

**H4 unblocking, verified rather than repeated:** H3c discharges **one** dependency outright — the
`welch_*`/`unpaired_*` family, whose only blockers are the two refusals H3c retires. The other two stay
double-blocked by H4's own codes, unchanged from H3b's correction.

**Every open ledger entry names one of these nine, or an S-slice above, or closes.** No
entry may defer to a description of a slice.

**Amendment, 2026-08-11 (H2 scoping): H2 no longer owns "wiring `check_swept_value` into
`validate`'s call path".** That work was already done before the charter was written —
`validate.py` imports it and calls it inside `_check_sweep`, and H1's scoping confirmed the
check fires as `E-SWEEP-VALUE-UNNAMEABLE`. The row gains **the six § Validation checks blocked
behind the four refused modes** in its place, which H1 measured and could not write: ablation
targets, ablation needs a baseline, ablation doesn't compose with a parameter axis, the ablation
baseline isn't a group level, sample ranges, and axis names are distinct. They are not extra
scope — they are the checks that become writable the moment the modes exist, and leaving them
unnamed is how a slice ships a feature with no validation.

**Amendment, 2026-08-11 (decided by the user): H1 no longer owns "the diagnostic
ordering".** That charter line was written before the checkpoint's decision 9 settled the
question the other way. `reference.md` § Exit codes and diagnostics now *argues for* the
current behaviour — findings "are grouped by the check that produced them, not by where in
the config the offending value sits", because "a strict document order would interleave
unrelated checks" — and the ledger entry at § `validate` findings are not ordered by config
position is closed on that basis. Implementing config-position ordering in H1 would require
reversing an argument the document makes, which is the defect shape this project has
shipped before: a slice blessing or breaking a rule a document states elsewhere. The
question is settled, not deferred. The row gains **the validate-time `E-` registry** in its
place, which is where the 61 unseated identifiers land.

## What S1 delivers

The promise `reference.md` already makes in § The starter step runs: `publishable run`
succeeds before the user has written a line of their own code, and what it writes is a
real record.

```bash
publishable new my-study
publishable generate experiment cohort-pilot --template generic \
  --input-dir ~/data/cohort-2026 --output-dir ~/results/cohort-pilot
git add src/ && git commit -m "Scaffold"
publishable validate configs/cohort-pilot/config.yaml
publishable run      configs/cohort-pilot/config.yaml     # → run.yaml, exit 0
```

**In scope.** The config spine (`Param` → `parameter_spec` → materialize → dot-access
`Config`); the error and diagnostic registry; `BaseStep`, `BaseExperiment` and
`BaseTemplate` with `generic`'s four parameters; the four-scope execution planner running
one condition × five seed repeats; atomic append-only `io.write`; all three hashes with
git, uv and input-manifest provenance; `run.yaml` assembly; and the CLI commands `new`,
`generate experiment`, `generate step`, `init`, `validate`, and `run`.

**Out of scope, by slice.** Units and `io.record` (S2), sweeps (S3), statistics (S4),
hypothesis evaluation (S5).

**Out of scope, to hardening.** Plugins and the four registries, the apparatus and its
gate, `draft`, `resume`, `diff`, `freeze`, `reproduce`, studies, `report`, `demo`,
`docs`, `list-templates`, the `template` and `report` generators, and secrets
(`required_env` / `requires_env`).

### Repeats are in S1, sweeps are not

S1 runs **one condition × five seed repeats**. Executing repeats is cheap — derive the
seed, run *n* times, write per-repeat directories, and record `per_repeat`, which
`reference.md` defines as *exactly what the step returned*. Collapsing repeats into a
per-unit value needs the unit table, so it waits for S2; reporting their dispersion as
`repeat_spread` needs the statistics engine, so it waits for S4. Neither is needed to
execute a repeat and record what it returned.

The alternative — deferring repeats to S3 — would force S1 to materialize
`repeats: [{kind: seed, n: 1}]`, diverging from the config `reference.md` documents and
tripping the replication-floor warning on every scaffolded project. Pulling seed
derivation and the design digest into S1 is justified on the same grounds as the hashes:
both are provenance, and provenance retrofitted is provenance nobody should believe.

### The artifact tree S1 produces

§ How artifacts are organized specifies that **degenerate levels collapse**: no sweep
means no `conditions/` level, because an unswept run has no `key=value` body to render
and therefore no directory name to produce. Five repeats means the repeat level is
present. So S1's tree is:

```
run_2026-08-08T14-02-11Z_<hash7>/
├── run.yaml
├── executions.jsonl
├── manifest/input.json
├── environment/{uv.lock,pyproject.toml}
├── shared/step01_.../          ← scope="run"
├── seed17/step03_.../          ← scope="repeat", no conditions/ level
├── seed42/…
└── summary/step04_.../         ← scope="summary"
```

This is a useful accident of the slicing: S1 exercises level collapse, one of the subtler
layout rules, from the first run. The active layout is recorded in `run.yaml`, as
§ How artifacts are organized requires.

## Modules and boundaries

| Module | One purpose | Depends on |
|---|---|---|
| `errors.py` | `PublishableError` → `ContractError` / `ArtifactError` → `ArtifactExistsError`, each carrying `.code` | — |
| `diagnostics.py` | The `E-`/`W-` registry, a collector that accumulates findings, exit-code mapping | `errors` |
| `param.py` | `Param`: type, default, constraints, help text. An omitted default is what makes a parameter required | `errors` |
| `config.py` | YAML load and the dot-access node: `ContractError` on a path the config doesn't hold, `AttributeError` on an underscore-prefixed name | `errors` |
| `materialize.py` | `parameter_spec` → a fully-populated, commented `config.yaml` | `param` |
| `templates/base.py` · `templates/builtin/generic.py` | `BaseTemplate`; `generic`'s four parameters | `param` |
| `base_step.py` · `base_experiment.py` | `scope`, `run(cfg, io)`, `nondeterministic`, `derive_seed`; the ordered `steps` list | `errors` |
| `scope.py` | Derive an immutable execution plan — a list of (condition, repeat, step) triples — from declared scopes | `base_*` |
| `replication.py` | The `seed` kind: *n* repeats, resolved seeds, repeat labels | `hashes` |
| `artifacts.py` | `io`: scope-aware paths, atomic write, append-only refusal, `io.path`, `io.exists` | `errors` |
| `hashes.py` | `code_hash`, `parameters_hash`, the design digest | `config` |
| `provenance.py` | Git walk-up from the given path; commit, branch, dirty state over the hashed trees | — |
| `manifest.py` | Input manifest build and verify, all three policies | — |
| `uv_support.py` | Locate and hash `uv.lock` | — |
| `run_identity.py` | `run_<id>` allocation, the `latest` symlink, the directory lock | — |
| `runner.py` | The execution loop: walk the plan, construct a step per execution, catch and record | everything above |
| `run_record.py` | Assemble `run.yaml` | — |
| `validate.py` | The S1 check subset, reporting into a collector | `diagnostics`, `config` |
| `cli.py` · `scaffold.py` · `generators/` · `readme_templates/` | Dispatch; `new`; `generate` `experiment` \| `step` | all |

Four boundary rules, each chosen so a spec property is structural rather than a
convention someone has to remember:

- **`config.py` is the only module that parses YAML.** Everything downstream receives a
  `Config`.
- **`artifacts.py` is the only module that writes inside a run directory.**
  `run_record.py` hands it bytes; it assembles and never computes.
- **`validate.py` never raises for a finding.** It reports into the collector, which is
  what makes "`validate` collects rather than stops" structural.
- **`hashes.py` is pure.** Resolved paths and a `Config` in, hex out. No filesystem
  policy, no git.

**`runner.py` is a divergence from § Package layout,** which has `scope.py` and `cli.py`
but no execution loop. Adding the module is better than hiding a loop inside dispatch.
This and any further divergence are logged in the defect ledger and applied to
`reference.md` § Package layout **at the S5 checkpoint** rather than piecemeal, so the
cross-document consistency passes run once.

**S1's only third-party dependency is PyYAML.** `pyarrow` arrives with S2's
`units.parquet`, `numpy` with S4's statistics. A stdlib-only spine keeps the provenance
code trivially testable.

## The execution path

`publishable run <path>` runs ten phases. Phases 1 through 6 create nothing, which is
what lets `validate` and `dry-run` be honest prefixes of this same sequence later rather
than separate code paths.

| # | Phase | Fails as |
|---|---|---|
| 1 | Resolve the path; walk up for `.git` from **the path given**, not the working directory | exit 1, naming where it looked |
| 2 | Load the config; run the S1 check subset into a collector | exit 1, every finding at once |
| 3 | Gates: `input_dir`/`output_dir` outside the repo, `src/**` and `templates/**` clean, entrypoint imports | exit 1 |
| 4 | Derive the execution plan — scopes × 1 condition × 5 repeats | exit 1 |
| 5 | Pin: `code_hash`, `parameters_hash`, design digest, input manifest, git, uv | exit 1 |
| 6 | Allocate `run_<id>/`, take the lock, decide the collapsed layout | exit 1 if the lock is held |
| 7 | Execute the plan | a failed execution is recorded and **the run continues** |
| 8 | Re-verify the input manifest | `status: failed`, exit 4 |
| 9 | Assemble and atomically write `run.yaml`; release the lock | — |
| 10 | Exit | 0 completed · 3 partial · 4 failed |

`executions.jsonl` is written as the loop goes, one record per finished execution.
Nothing in S1 consumes it, but it is what `resume` reads later, and writing it
retroactively would mean re-deriving state the loop already had.

### Two error channels

`reference.md` § Errors core raises already draws this line: *an exception exists where
your code could act on the distinction; everything a command reports is a diagnostic, not
an exception you catch.* S1 keeps the two apart structurally.

- **Diagnostics** — phases 1 through 6. Collected, never raised. Each carries a stable
  `E-`/`W-` identifier, and `validate` reports all of them in config order. A warning
  never changes the exit code.
- **Exceptions** — phase 7. The `PublishableError` tree, each carrying the same `E-`
  identifier in `.code`. A `ContractError` inside an execution fails that execution and
  the loop moves on; it is not a special stop.

S1 emits exit codes 0, 1, 2, 3 and 4. Code 5 requires the apparatus, credentials, or a
clone, none of which exist before hardening.

## Testing

pytest, test-driven. Most of S1 is pure — `param`, `config`, `materialize`, `hashes`,
`replication`'s seed derivation — so those are table-driven tests with no fixtures. Three
areas need a stated decision:

- **Git is real, never mocked.** Provenance honesty is the thing being built, and a
  mocked `git` would test nothing. Tests `git init` into `tmp_path` and make real
  commits.
- **`uv` is not invoked in the normal suite.** S1 only hashes `uv.lock`, so tests use a
  fixture lockfile. One test marked `slow` exercises a real `uv lock`, because `new` does
  have to produce a lockfile and that path should not go unexercised.
- **Atomicity is tested by injection**, not inspection: raise inside the write, then
  assert that no partial file and no leftover temp remain.

**The coverage bar is not a percentage.** It is: *every `E-`/`W-` identifier S1 defines
has a test that produces it.* That bar is spec-derived, cannot be satisfied by testing
accessors, and keeps the diagnostic registry from accumulating codes nothing emits.

**The S1 acceptance test** scaffolds into a temp directory, commits, and runs, then
asserts a `run.yaml` with `status: completed`, three well-formed hashes,
`provenance.git.commit` matching the real commit, the config embedded verbatim, the
collapsed layout recorded, and exit code 0 — plus the dirty-tree refusal and the
`input_dir`-inside-repo refusal both firing.

## Repo changes

| Change | Detail |
|---|---|
| `pyproject.toml` | `publishable` 0.1.0, matching `CITATION.cff`; `requires-python >=3.11`; one dependency, PyYAML; `publishable = "publishable.cli:main"` |
| `src/publishable/` | The modules above |
| `tests/` | Unit tests and the acceptance test |
| Tooling | `ruff` for lint and format; `mypy` over `src/` only |
| `CLAUDE.md` | The "Repository status: specification only, no implementation" section is replaced |

### The `CLAUDE.md` rewrite

Two statements become false the moment S1 lands: *"Repository status: specification only,
no implementation"* and *"There are no build, lint, or test commands. Do not invent them,
and do not run `publishable <anything>`: the binary does not exist here."*

That section is replaced with one describing the repository's dual nature and the rule
that governs it: **the four documents remain normative and lead; code follows them, and
where code cannot follow them, the document changes first.** The replacement also names
the real build, lint, and test commands, and states that `docs/reference.md` § Package
layout now describes a tree that partially exists, with the unbuilt modules still marked
as planned.

Everything else in `CLAUDE.md` is untouched and still governs: the invariants, both
consistency passes, the worked example, the documentation conventions, and the
feasibility-analysis procedure.

## Known deviations, and the defect ledger

Two deviations from the documents are accepted for S1 and resolved later. Both are
recorded rather than quietly absorbed.

1. **The starter step is not yet the specified starter step.** `reference.md` § The
   starter step runs and `design-principles.md` § Core vs. plugin both say it "resolves
   the units, records them, and returns a count", which needs S2. In S1 it returns a
   trivial scalar. The generator is written so S2 changes one file.

2. **A candidate spec gap, found before any code was written.** `data.units` is optional,
   and § The unit table is the inference base says that with no unit table core reports
   "mean, std, sem and a t-based `ci95` over repeats". The general case includes `n: 1` —
   legal, and what `generic`'s `default_repeats` floor of 1 permits — where std, sem and
   a t-interval are all undefined, and the documents state no rule for it. **S1 does not
   hit this**, because it emits `per_repeat` and no `aggregated` block at all; S4 does,
   and needs an answer before it computes anything. Recorded in the ledger by the slice
   that found it, resolved by the slice that needs it.

**The ledger lives at `docs/superpowers/spec-defects.md`**, inside the gitignored working
area. It is scaffolding, not a deliverable: what ships is the fixes landing in the four
documents at the S5 checkpoint. Each entry records what the code could not do, which
document and section governs it, and the proposed resolution.

## Explicitly out of scope

- Any command not listed above. In particular `draft` is deferred, which means a commit
  is required before every `run` during development. That is what the documents specify,
  and living with it is a useful test of whether the rule is tolerable.
- `examples/generic/` from § Package layout. Nothing consumes it until `demo`.
- Any change to the worked example's numbers. The acceptance test is structural and
  bounded precisely so that no implementation detail can force a documentation rewrite.
- Optimizing anything. This is a reference implementation; the hardening pass is where
  performance becomes a question worth asking.
