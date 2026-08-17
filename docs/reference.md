# Reference

Complete reference for `publishable`. For the rationale behind these choices, see [design-principles.md](design-principles.md); for how to express a particular experimental design, see [experimental-designs.md](experimental-designs.md). For a short introduction, see the [README](../README.md).

## Contents

**Setting up a project**
- [Scaffolding: `publishable new`](#scaffolding-publishable-new) — what a new repo contains
- [Generators](#generators) — adding experiments, steps, templates
- [The one config file](#the-one-config-file) — the file you edit

**Writing an experiment**
- [The importable surface](#the-importable-surface) — every name you import, and the errors this document specifies
- [Steps and artifacts](#steps-and-artifacts) — the `io` API
- [Step scope](#step-scope) — how often each step runs
- [Units: the thing being measured](#units-the-thing-being-measured) — patients, samples, trials
- [Templates: where parameters are defined](#templates-where-parameters-are-defined) — `parameter_spec`, `Param`

**Designing a run**
- [Sweeps and repeats](#sweeps-and-repeats) — conditions, repeat kinds, statistics
- [Validation](#validation) — what's checked before you spend a run, and what core warns about before and during one

**What a run produces**
- [Run identity](#run-identity) — the output tree
- [The two files](#the-two-files) — `config.yaml` and `run.yaml`
- [The other files a run writes](#the-other-files-a-run-writes) — `sweep.yaml`, `allocation.json`, manifests, unit tables
- [Three hashes](#three-hashes) — code, parameters, data, and what `auto` derives from
- [Lineage between runs](#lineage-between-runs)

**Reporting and sharing**
- [Pre-registration](#pre-registration) — declaring hypotheses up front
- [Studies: what a paper reports](#studies-what-a-paper-reports)
- [Reproducing on another device](#reproducing-on-another-device)

**Extending and operating**
- [Plugins: where domain knowledge lives](#plugins-where-domain-knowledge-lives)
- [Secrets & credentials](#secrets--credentials)
- [Naming conventions & repeat defaults](#naming-conventions--repeat-defaults)
- [CLI reference](#cli-reference)
- [Package layout](#package-layout)

---

## The one config file

You never write a config from scratch, and you never go looking for what options exist. `init` reads the template's parameter specification and materializes **every** parameter into one fully-populated, commented file:

```bash
uv run publishable init --template generic \
  --input-dir /secure/data/cohort-2026 \
  --output-dir /secure/results/cohort-pilot \
  --name cohort-pilot
```

```yaml
# configs/cohort-pilot/config.yaml
# The config schema for template `generic` v1.0.0, at full expansion: every
# parameter `publishable init` materializes, plus the optional blocks it leaves
# empty or undeclared. Edit it, validate it, run it.

schema_version: "1.0"
experiment_type: generic
template_version: "1.0.0"
plugin: null                       # e.g. "someuser/publishable-llm@v1.2.0"

metadata:
  name: cohort-pilot               # must match the template's naming_pattern
  description: ""                  # REQUIRED — one line, what this run is for
  authors: []                      # REQUIRED
  institution: ""

entrypoint: "cohort_pilot.experiment:CohortPilotExperiment"   # see "Generators"

data:
  input_dir: /secure/data/cohort-2026      # must be OUTSIDE the repo — enforced
  output_dir: /secure/results/cohort-pilot
  input_manifest_policy: hash_all          # hash_all | hash_index | none
  units:                                   # optional; required by fold, resample, null_test
    from: index.csv                        # index.csv | {glob: "*.dcm"} | {resolver: <name>} (NOT BUILT)
    key: patient_id                        # stable, unique identity
    attributes: [label, age, sex]          # available for stratification and reporting
    allocation: within                     # within | between — feeds paired vs unpaired,
                                           #   per contrast
    cluster_by: null                       # e.g. site, when units aren't independent —
                                           #   see "Clustered units"
    weight_by: null                        # e.g. sampling_weight, when the sample is enriched or
                                           #   stratified — see "Weighted samples"
    measurements: null                     # {by: read_id, collapse: mean} for technical
                                           #   replicates; collapse is mean | median | sum | first |
                                           #   mode, or a per-column map — see "What isn't a repeat"
    holdout: null                          # optional single fixed train/test split — see "A fixed
                                           #   holdout split"; at full expansion:
                                           #   method: random     # random | by_attribute
                                           #   frac: 0.2          # test fraction, for random
                                           #   from: null         # the attribute naming the partition, for by_attribute
                                           #   stratify_by: []    # unit attributes to balance the split on
                                           #   seed: auto         # design digest + "holdout"
    assign: {}                             # REQUIRED when allocation is `between` — one
                                           # block per sweep.groups axis, keyed by the axis name:
                                           #   arm:
                                           #     method: random     # random | by_attribute | blocked
                                           #     from: arm          # by_attribute; defaults to the axis name
                                           #     stratify_by: []    # unit attributes, or an earlier axis
                                           #     ratio: {}          # one entry per level of THIS axis
                                           #     block_size: auto   # blocked only; twice the ratio's sum (rounded), or twice the level count when ratio is {}; checked like any block_size
                                           #     seed: auto         # design digest + axis name

parameters:
  # ---- Base values. Everything below is defined by the template, not by core. ----
  analysis:
    method: pearson                # choices: pearson | spearman | kendall
    min_samples: 30                # integer >= 2
    confidence: 0.95               # float in (0, 1)
    drop_missing: true

sweep:
  # ---- What varies. Omit entirely for a single-condition experiment. ----
  # Keys are dotted paths into `parameters`; modes compose. See "Sweeps and repeats".
  baseline: {analysis.method: pearson}   # optional reference condition; enables deltas.
                                         #   Parameter paths only — a `groups` level is not
                                         #   one, the arms being peers
  groups: []                             # optional list of unit-group axes,
                                         #   e.g. [{by: arm, levels: [...]}]
  paired: []                             # optional coupled settings,
                                         #   e.g. [{analysis.min_samples: 30,
                                         #   analysis.confidence: 0.95}] — one axis, not a product
  ablate: null                           # optional; 1 + n one-change conditions, e.g.
                                         #   {from: baseline, remove: [...]} or {override: [...]}
                                         #   — requires baseline
  sample: null                           # optional; continuous ranges instead of
                                         #   enumeration, e.g. {n: 40, method: sobol, seed: auto,
                                         #   ranges: {...}} — one axis of n drawn conditions
  grid:
    analysis.method: [spearman, kendall]
  # 1 baseline + 2 grid = 3 conditions

replication:
  # ---- How each condition repeats. Kind determines the statistics core applies. ----
  repeats:
    - {kind: seed, n: 5}                 # seed | batch | fold
  order: as_declared                     # as_declared | randomized
  rationale: ""

statistics:
  # ---- Computed over the per-unit table after the run. Not execution axes. ----
  correction: holm                       # none | bonferroni | holm | fdr_bh
  contrasts: []                          # optional named pairwise comparisons, for claims that
                                         #   aren't condition-vs-baseline, e.g. [{id: sens,
                                         #   of: "shift=abnormal", against: "shift=normal",
                                         #   within: {sex: f}}] — `within` is optional and
                                         #   restricts to a stratum. See "Contrasts"
  resample: null                         # bootstrap
                                         #   {method: bootstrap, n: 2000, stratify_by: []}
                                         #   → percentile CIs for column metrics too; derived
                                         #   metrics resample either way
  null_test: null                        # NOT BUILT; e.g. {method: permutation, n: 5000,
                                         #   shuffle: label}
  report_by: []                          # optional unit attributes to repeat every aggregated
                                         #   metric over — marginally, never crossed,
                                         #   e.g. [sex, site]. Strata, not design axes — they add
                                         #   no executions. See "Reporting strata"

limits:
  # ---- Thresholds core checks against. All warn except max_failed_fraction, which fails the
  #      run, and min_reported_n, which also prompts at `study add`. ----
  max_executions: 500              # `validate` warns above this many conditions × repeats
  max_failed_fraction: 0.2         # `run` fails the run when units failing anywhere, over the
                                   #   resolved roster, exceed it.
                                   #   Failures only — units a step declared ineligible are not
                                   #   attrition; see `io.skip`
  max_ineligible_fraction: 0.5     # `run` warns when a condition can be built for fewer units
  min_units_per_cell: 20           # a smaller design cell under allocation: between should warn — declared
                                   #   and typed, read by nothing in this build; see "Allocation:
                                   #   within-subjects or between-subjects"
  min_clusters: 10                 # `validate` warns when `resample` would draw fewer than this
  min_reported_n: 10               # `validate` warns for a stratum or `within` contrast this small;
                                   #   `study add` prompts on any metric reported over fewer

hypotheses:
  # ---- Optional, but written BEFORE the run — which is what makes it meaningful. ----
  # A `summary` metric takes no `compare`; see "A hypothesis may name a summary metric".
  # `compare` also accepts {contrast: <id>}; `evaluate_on` picks observed vs. an interval bound.
  - id: h1
    kind: confirmatory                   # confirmatory | exploratory
    statement: "Spearman correlation exceeds Pearson on this cohort."
    metric: step03_analyze.r
    compare: {condition: "method=spearman", to: baseline}
    direction: greater
    threshold: 0.02
    evaluate_on: observed                # observed | ci95_lower | ci95_upper
```

`init` materializes **every parameter the template declares**, each with its default and its inline comment. The four optional `statistics` sub-blocks are shown above at their full expansion because this section is the complete config *schema*, which is a wider thing than the literal output of `init`; a materialized file that does not carry them is not an incomplete config. For `contrasts` and `report_by`, declaring one by hand is how a run asks for it, and `validate` accepts the key whether or not `init` wrote it. **Two declarations above are not yet built, and each is marked `NOT BUILT` where it appears**: the `{resolver: <name>}` form of `data.units.from`, and `statistics.null_test`. A config declaring either is refused today, naming the `-UNSUPPORTED` code its slice will retire — the same treatment [an unbuilt module](#package-layout) and [an unbuilt import](#the-importable-surface) get, because a contract that appears only once its implementation lands is a contract nobody could have designed to. That whole family is [deliberately absent from the validate-time registry](#errors-validate-reports) for the same reason, which is why this list, and not that table, is where a refused block is named. A third refusal in the same family is not a declaration at all and so is marked nowhere above: an `experiment_type` naming a template an installed distribution registers is refused, because core resolves such a name from package metadata and this build does not load what the name points at. It carries `E-TEMPLATE-INSTALLED-UNSUPPORTED` and, like every `-UNSUPPORTED` code, [no row in the registry below](#errors-validate-reports). `statistics.resample` left this list with H4a: `_check_resample` now checks its declaration for real instead of refusing the block wholesale, and its `NOT BUILT` marker is gone from the line above. `data.units.holdout` left it with H3d: `_check_holdout` now checks its declaration for real, `_resolved_holdout` realizes the split once per run, `io.units`/`io.units.train` see the two halves, and `cli.py` narrows every denominator to the test partition and writes `allocation.json`'s fourth key — so its `NOT BUILT` marker is gone from the line above too. `sweep.groups`, `data.units.assign`, and any `data.units.allocation` other than `within` left this list once their own slice landed: `expand` crosses a group axis into the condition product, `_check_assign` checks `allocation` and `assign` against each other and against `sweep.groups` for real, and `cli.py` writes `allocation.json` and `provenance.allocation_hash` — each is refused only in the shapes [§ Validation](#validation) and [§ Errors `validate` reports](#errors-validate-reports) name on their own merits now, not wholesale. What `init` writes is complete with respect to [`parameter_spec`](#templates-where-parameters-are-defined), which is the only source of truth there is one of. `data.units.measurements` is the one *built* block `init` **materializes** as a `null` with its shape in a comment rather than expanded — `statistics.resample` is shown that way too since H4a made it built, but `init` writes no `resample` key at all — the difference that keeps the [column-resample asymmetry](#statistical-reporting) legible: a *declared* `resample` is what turns a column's interval from a *t* into a percentile, so materializing the block at its default expansion would make that the silent default for every generated project. A materialized `resample: null` would not — an explicit `null` is undeclared, exactly as an absent key is — but it would put a key in every config for a choice most runs never make, which is the ordinary reason `init` leaves a block out. `measurements` is materialized because a run declares it only when it has technical replicates to collapse — carried in its input, or produced by a step through [`io.record(..., measurement=)`](#steps-and-artifacts), which core refuses without the declaration. Its two sub-fields, `by` and `collapse`, are named in that comment and nowhere else in this section, and both are keys [the closed schema checks](#validation); `.holdout`'s slice has landed with the same treatment, closed one level in at its own five fixed keys (`method`, `frac`, `from`, `stratify_by`, `seed`), so a misspelled child inside a non-empty `holdout` block is reported the same way. `.assign`'s slice has landed with this closed one level in: `envelope.py` still types the block itself a bare `dict` — the axis name beneath it (`arm` in the expansion above) is user-chosen and no fixed dotted path can name it — but each axis block's own keys are checked against the closed set `{method, from, ratio, block_size, stratify_by, seed}`, so a misspelled field inside an axis block (`stratifyy_by` for `stratify_by`) is reported as `E-CONFIG-KEY-UNKNOWN` rather than silently ignored. `.weight_by` and `.cluster_by`, whose slices have both landed, needed none of it: each is a string naming an attribute rather than a block, so neither has sub-keys for a schema to close, and each is shown as a `null` above for the ordinary reason that most runs declare neither a weight nor a cluster. A `fold` repeat level's `stratify_by` left this list alongside `.cluster_by`, and the `replication` block above names it nowhere — not because anything is unbuilt, but because that block shows what `init` writes, a single `{kind: seed, n: 5}`, and the fields of a level are the *kind's* rather than this block's: a `fold`'s `k` isn't shown there either. [Repeat kinds](#repeat-kinds) is where each kind's own fields are enumerated.

**The four identifying fields above `metadata` say what this config is written against, and `validate` checks each — three for a config generated against a [project-local template](#templates-where-parameters-are-defined), which `init` writes with no `template_version` at all.** `experiment_type` names the template and must resolve to one core, an installed plugin, or this project's own `templates/` registers — an installed one is answered from package metadata, so a name no distribution declares is refused without importing anything, and a name one *does* declare is [not yet loadable in this build](#the-one-config-file); `template_version` records the spec this file was materialized from, and a mismatch with the installed template gets a [warning](#warnings-core-reports) — `W-TEMPLATE-VERSION` — not an error, because upgrading a plugin is ordinary and [nothing ever writes back into your config](#the-one-config-file). What makes an incompatibility *fail* is already covered without a version check: a retired parameter is an unknown key, and a new required one is a missing key. So the version tells you where to look and the existing checks decide whether it matters; `plugin` names where the template came from, and is a readable note beside the authoritative pin in `uv.lock` rather than a second one — core never installs from it. `schema_version` is the config format's own version: core reads any minor at or below its own and refuses a higher one, or a major it doesn't implement, rather than guessing at a field it doesn't recognize. Through v0.x a change that would break an existing config bumps the major, and there is no migration command — a config is small, `init` writes a fresh one, and the [defaults-file argument](#there-is-no-separate-defaults-file) applies to a migration file too. What protects an old *result* is that `run.yaml` embeds its config verbatim alongside the `schema_version` it was written under, so a record stays readable whether or not the format moved. All four are inside [`parameters_hash`](#three-hashes), because a config read against a different spec is a different declaration.

This file is three things at once: the scaffold (you didn't type it), the documentation (every available parameter is present, with its constraints in a comment), and the config (it's what `run` consumes). Keeping them as one artifact is what prevents the usual drift where documentation lists options the code no longer accepts.

**The file is freely editable, and nothing `publishable` does ever writes back into it.** Edit it as much as you like; each run embeds the config it used verbatim into its own `run.yaml`, which is where parameter provenance actually lives.

**Whether you commit it is your call, and core takes no position.** Reproducibility doesn't depend on it either way: `run.yaml` embeds the config verbatim and fingerprints it with `parameters_hash`, so a run is fully reportable whether or not its config was ever tracked. Because of that, the scaffold's `.gitignore` says nothing about `configs/` — imposing a policy there would be the tool overriding a judgment that belongs to you.

Two things worth weighing when you decide:

- **For committing:** parameter changes get review and history like anything else in the repo, and collaborators can start from a known config rather than re-deriving one. Since `code_hash` covers only `src/**` and `templates/**`, committing configs doesn't disturb [same code, different parameters](design-principles.md#same-code-different-parameters) comparisons.
- **Against:** `data.input_dir` is an absolute path that can encode a cohort name or institutional structure, which you may not want in a public repo. And a tracked `configs/` can accumulate stale files that look authoritative but were never run — the only authoritative record of a parameter set is the `run.yaml` of a run that used it.

### There is no separate defaults file

The authoritative catalog of parameters is the template's `parameter_spec` — in code, versioned with the template, in the plugin that owns it. A committed `defaults.yml` would be a second copy of that, free to drift out of sync, and would raise a question with no good answer ("which defaults file is canonical?"). So there is exactly one parameter file per experiment: the config `init` produced. If you want a second parameter set, copy the file — see [Same code, different parameters](design-principles.md#same-code-different-parameters).

---

## Validation

`validate` is the only thing between "I edited YAML" and "I spent four hours of compute," so it checks values, not just presence:

```bash
uv run publishable validate configs/cohort-pilot/config.yaml
```

The table below states each check by the mistake it catches. What `validate` *prints* for one is a [diagnostic](#exit-codes-and-diagnostics) carrying a stable identifier, and the two registries of those are [§ Errors `validate` reports](#errors-validate-reports) and [§ Warnings core reports](#warnings-core-reports) — a row here and a code there are the same check seen from the two ends, so a reader who has an identifier in hand should start there rather than matching prose against this table.

| Check | Example failure |
|---|---|
| Required fields present | `metadata.description` is empty |
| Types | `analysis.min_samples` is `"30"`, expected integer |
| Ranges | `analysis.confidence` is `1.4`, expected float in (0, 1) |
| Choices | `analysis.method` is `pearsonn`, expected one of pearson, spearman, kendall |
| **Unknown keys** | `analysis.min_sample` is not a parameter of template `generic` — did you mean `min_samples`? |
| Naming convention | `metadata.name` doesn't match the template's `naming_pattern` |
| Name matches its directory | `metadata.name` is `cohort-pilot-v2` under `configs/cohort-pilot/`; the two name one experiment |
| Template resolves | `experiment_type` names `llm_diagnostic`, which no installed plugin registers — `plugin` says it should come from `someuser/publishable-llm` |
| Template name is claimed once | `templates/one.py::Assay` and `templates/two.py::Assay2` both register `my_assay`, or a local file registers `generic`; import order is the only tie-break, so core refuses rather than picking |
| Template version moved | `template_version` is `1.0.0` but installed `generic` reports `1.2.0`; `request.timeout` is new and unset (warning) |
| Replication floor | `repeats` total of 1 is below this convention class's default of 5 (warning) |
| Sweep paths resolve | `sweep.grid` key `analysis.methd` is not a parameter of template `generic` |
| Swept values legal | `sweep.grid.analysis.method[1]` is `spearmann`, expected one of pearson, spearman, kendall |
| Ablation targets | `sweep.ablate.remove[0]` is `analysis.min_samples` (int); `remove` needs a boolean or nullable parameter — use `override` |
| Ablation needs a baseline | `sweep.ablate` is declared but `sweep.baseline` is not — there is nothing to ablate from |
| Ablation doesn't compose with a parameter axis | `sweep.ablate` cannot be combined with `grid`, `paired`, or `sample`; one change at a time and a second parameter axis are contradictory. `groups` is permitted — it varies no parameter |
| Ablation baseline isn't a group level | `sweep.baseline` fixes `cohort: derivation` while `ablate` is declared; each cell gets its own baseline condition, so the arms can't have one designated between them |
| Baseline isn't a group level | `sweep.baseline` fixes `arm: control`, a level of a [`sweep.groups`](#expansion-modes) axis; the arms are peers, and the level would be rendered twice — as the baseline row and as its own axis's product row — giving two conditions the same units and the same parameters |
| Sample ranges | `sweep.sample.ranges.analysis.confidence` upper bound 1.4 violates the parameter's `lt=1`; and `{uniform: [10, 200]}` over an integer parameter draws `118.385…`, which no bound of it is |
| Sample draws aren't compared to a baseline | `sweep.baseline` is declared beside a `sweep.sample` axis; each draw would be a comparison against it, and the correction family skips drawn conditions — specified, not built in this build |
| Sample is drawable | `sweep.sample.method` is `gaussian` — the methods are sobol, latin_hypercube, random; and `{uniform: [0.99, 0.80]}` has its bounds the wrong way round |
| Baseline is a valid condition | `sweep.baseline` sets `analysis.method: pearsonn` |
| Swept values are nameable | `sweep.grid.prompt.text[1]` renders as `a long sentence`, which can't be a [condition label](#how-artifacts-are-organized) — a swept value must render as `[A-Za-z0-9._+-]+` |
| Repeat kind coherence | `{kind: bootstrap}` is not a repeat kind — declare `statistics.resample` instead |
| Batch has something to measure | `{kind: batch, n: 5}` is declared but no step sets `nondeterministic = True`, so five batches recompute one answer (warning) |
| Batch takes no fields | `{kind: batch, k: 3}` — a batch varies nothing, so `n` is the only field it accepts |
| Each kind takes its own count | `{kind: fold, k: 2, n: 5}` — `n` is a `seed`/`batch` field and a fold's count is `k`, so this executes two folds while the [execution count](#repeat-kinds) reads five. A count one reader believes and the other ignores is refused, not resolved by precedence |
| Null test coherence | `statistics.null_test` requires `shuffle` to name a unit attribute |
| Shuffle level is unambiguous | `null_test.shuffle: status` varies within `match_set` `M07` but is constant within `M12`, so neither a within-cluster nor a whole-cluster null applies |
| Resample has a roster | `statistics.resample` is declared with no `data.units` — nothing to resample, and the declaration would run nothing |
| Clusters enough to resample | `statistics.resample` with `cluster_by: animal_id` over 4 animals bootstraps 4 draws; below `limits.min_clusters` (warning) |
| Resample draws are honest | `statistics.resample: {n: 50}` — below 80 draws a percentile interval's lower endpoint is the sample minimum, so core reports none and every metric in the run loses its `ci95` |
| Resample draws fit the family | `statistics.resample: {n: 200}` over 3 comparisons under `holm` — the tightest corrected level is 0.01667 and needs 240 draws, so `ci95_corrected` would be null (warning) |
| Technical replicates | `{kind: technical}` is not a repeat kind — declare `data.units.measurements` instead |
| Collapse rule fits the column | `measurements.collapse: mean` over `site`, which is a string — use `first` or `mode`, or a per-column map |
| Measurement axis exists | `measurements: {by: read_id}` over a `reads.csv` with no `read_id` column, where rows sharing a `key` were collapsed anyway — checked only where the input carried the replicates, since a `by` naming a measurement a step supplies through `io.record(..., measurement=)` names no input column |
| Grid size sane | 20 conditions × 10 folds × 3 seeds = 600 executions exceeds `limits.max_executions` — conditions counted over every axis the sweep expands, a [group axis](#expansion-modes) included, since a group level is a condition that executes like any other |
| Leave-one-out is affordable | `{kind: fold, k: all}` over 240 units × 3 conditions = 720 executions exceeds `limits.max_executions` — counted over the cluster count rather than the unit count when `cluster_by` is declared, `k: all` being leave-one-*cluster*-out |
| Credentials present | `INSTRUMENT_API_TOKEN` is not set in `.env` |
| Credentials a swept value needs | `AZURE_OPENAI_API_KEY` is [required by](#a-credential-can-belong-to-a-parameter-value) `llm.provider: azure_openai`, selected in condition `01_model=azure.gpt-4.1`, and is not set in `.env` |
| `requires_env` covers its choices | `llm.provider` declares `requires_env` for `azure_openai`, `openai`; `choices` also lists `ollama` — a value that needs no credential declares `[]` |
| Probe is installed | template `my_assay` declares `apparatus_probe: assay_instrument`, which no installed plugin registers |
| Data outside repo | `output_dir` resolves inside the git repository |
| Manifest readable | `input_dir` is unreadable or empty |
| Unit keys unique | `data.units.key` `patient_id` has 3 duplicate values |
| Attribute names aren't reserved | `data.units.attributes` names `paths`, which is a field of [`Unit`](#where-units-come-from) itself — `key`, `paths`, and `attributes` can't also be attributes |
| Resolver is installed | `data.units.from.resolver` names `plate_wells`, which no installed plugin registers |
| Resolver supplies the attributes | resolver `plate_wells` yields units with no `operator`, declared in `data.units.attributes` |
| Attributes have a source | `data.units.attributes` names `label` under `from: {glob: "*.dcm"}`, which yields a key and a path and nothing else — declare a table or a resolver, or drop the attribute |
| Resolver supplies the measurement field | `measurements: {by: read_id}` is declared but resolver `plate_wells` yields no `read_id` attribute to collapse on |
| Resolver is condition-independent | resolver `plate_wells` reads `instrument.model`, which `sweep` varies — the unit table is one table for the whole run. (An apparatus [probe](#the-apparatus-core-can-only-observe) carries no such restriction, and usually does read a swept parameter) |
| Stratification attribute exists | A `fold` level's or `holdout`'s `stratify_by: label` is not in `data.units.attributes`, or is the column `data.units.measurements.by` names — consumed when a unit's rows collapse, so no resolved unit carries it. Neither reads a group axis, so *Allocation strata exist* is `assign.<axis>.stratify_by`'s row instead, a target an axis name is also legal against |
| Repeat kind needs units | `{kind: fold}` requires `data.units` to be declared |
| Holdout isn't a repeat kind | `{kind: holdout}` is not a repeat kind — declare `data.units.holdout` instead |
| One evaluation split, not two | `data.units.holdout` and `{kind: fold}` are both declared; each divides the units for evaluation, so together they leave no single answer to what a metric is over |
| Holdout is resolvable | `holdout.method: random` needs `frac` in (0, 1); `by_attribute` needs `from`, and column `split` has values `{train, test, dev}`, expected exactly two |
| Holdout strata survive clustering | `holdout.stratify_by: label` with `cluster_by: animal_id`, but `label` varies within animal `A3` |
| One split, not one cell each | `data.units.holdout` or a `{kind: fold}` level is declared beside `allocation: between` or a non-empty `sweep.groups` — one roster-wide evaluation split would give the cells unequal test sizes, and a cell none at all once the split is fine enough |
| Holdout leaves a test partition | `holdout.method: random` with `frac: 0.01` over 40 units apportions the test side zero units, so every metric would be over nothing. Reported for the unstratified, unclustered draw only — a clustered draw and either kind of stratified draw are checked where the run performs them |
| Biological replicates are units | `{kind: biological}` is not a repeat kind — independent samples are rows in the unit table |
| Allocation is a known value | `allocation: sideways` — not `within` or `between` |
| Allocation needs arms | `allocation: between` but `sweep.groups` declares no axis to say what the arms are |
| Every axis is assigned | `sweep.groups` declares `sex` but `data.units.assign` has no `sex` block |
| Every assignment names an axis | `assign.cohort` names no axis in `sweep.groups` |
| Axis names are distinct | `sweep.groups` declares `arm` twice — a condition can't hold two values of one axis |
| Levels are distinct | `sweep.groups` declares `levels: [control, treatment, control]` — a level names a set of units, so the repeat expands into a second condition holding the same units under the same label |
| Stratification is forward-only | `assign.sex.stratify_by: [arm]`, but `arm` is declared after `sex`; an axis may only stratify on one already resolved |
| Cells are populated | `sex × arm` over 40 units gives cells of 10; below `limits.min_units_per_cell` — specified, not built in this build (warning) |
| Arms need allocation | `sweep.groups` declares arms but `allocation` is `within`, which says every unit appears in every condition — a unit can't be in one arm and in all of them |
| Assignment names a method | `assign.arm` declares `stratify_by` and no `method`, or a `method` of `by_column` — the methods are random, by_attribute, blocked, and which of the block's other fields are read follows from which one it is. That a block must exist at all under `allocation: between` is the "Allocation needs arms" and "Every axis is assigned" rows above, between them, so it earns no row of its own |
| Ratio names levels | `assign.arm.ratio` has key `f`; expected one entry per level of axis `arm` (`control`, `treatment`) |
| Every arm draws units | `assign.arm.ratio: {control: 1, treatment: 1000}` over 10 units draws `control` nobody — a ratio every declaration-only rule accepts, refused against the roster it would be apportioned over. Reported for the unstratified, unclustered draw only — a clustered draw and either kind of stratified draw are checked where the run performs them, for the two different reasons the code's own row gives |
| Ratio and strata need a draw | `assign.arm.method: by_attribute` with `ratio: {control: 1, treatment: 1}` — a `ratio` describes a draw that didn't happen; `assign.arm.stratify_by: [site]` is the same fault |
| Block size fills the arms | `assign.arm.block_size: 3` with `ratio: {control: 1, treatment: 1}` — each level's own per-block share must be a whole number, or a block can't hold that arm's share exactly. (`assign.arm.block_size: 1` with `ratio: {a: 0.5, b: 0.5}` is the case a check of the sum alone would miss: 1 divides the sum, 1, evenly, but each level's own share of it is 0.5) |
| Blocked draw excludes clustering | `assign.arm.method: blocked` beside `data.units.cluster_by: site` — a block counts units and fills to an exact size, a cluster is indivisible, and no block size honours both; `random` has no such conflict, since drawing a whole cluster fills no size at all. Use `random` for a cluster-randomized draw, or `by_attribute` for a read one |
| Assignment seed is auto or pinned | `assign.arm.seed: "1234"` under `method: random` — a seed is `auto` or a pinned integer, and a quoted, fractional, or boolean one is discarded for the derivation, which `allocation.json` then records as though it were the pin |
| Assignment attribute exists | `assign.arm.from` — defaulted from the axis name — names `arm`, which is not a unit attribute |
| Attribute assignment resolves | `assign.arm.method: by_attribute` reads column `arm` — defaulted from the axis name — whose values must equal the declared levels exactly, in either direction: `{a, b}` is refused against levels `{control, treatment}` for naming neither, and so is a column whose values name only one of the two levels, leaving the other arm with no units |
| Arm is constant within a unit | Under `method: by_attribute`, `assign.arm.from: arm`, and `p1`'s [measurement rows](#what-isnt-a-repeat) declare `control` and `treatment` — the collapse would file `p1` under whichever the file lists first, so the order the file happens to be in would decide which condition `p1` is measured in |
| Allocation is coherent | `allocation: between` over 2 arms and 12 units gives cells of 6; below `limits.min_units_per_cell` — specified, not built in this build (warning) |
| Allocation strata exist | Under `method: random` or `blocked`, `assign.arm.stratify_by: [site]` but `site` is neither a unit attribute nor a group axis. Owns `assign.<axis>.stratify_by` under those two methods, including a target naming a group axis — unlike *Stratification attribute exists*, whose `fold`/`holdout` stratify targets admit only a unit attribute. `stratify_by` means nothing under `by_attribute`, so this row does not reach it |
| Allocation strata survive clustering | Under `method: random`, `assign.arm.stratify_by: [label]` with `cluster_by: animal_id`, but `label` varies within animal `A3` — a cluster is drawn whole, so an arm can't be balanced on a stratum that cluster carries two of. A stratum naming an earlier **group axis** is read the same way, through the column that axis reads: `stratify_by: [sex]` where `sex` is `by_attribute` on a `patient_sex` that varies within `A3` splits `A3` between `sex`'s own arms before `arm` is drawn at all. An earlier axis that *draws* needs no check — it allocated whole clusters. The same rule and the same reason as *Fold strata survive clustering* below; `blocked` beside any `cluster_by` is refused outright by *Blocked draw excludes clustering* above, so this row reaches `random` alone |
| Allocation deltas aren't computed | A resolved comparison crosses a [group axis](#expansion-modes) — a `statistics.contrasts` entry naming `arm=treatment` against `arm=control`; the two sides hold disjoint units and no contrast construction computes an unpaired delta — specified, not built in this build. A generated `vs_baseline` reaches this only where the baseline fixes a group level, refused outright by `E-SWEEP-BASELINE-GROUP`, so a declared contrast is the shape that carries this alone. Unlike *Clustered deltas aren't computed* and *Weighted deltas aren't computed*, read per comparison rather than for the whole design: `groups × grid`'s within-arm comparisons stay paired and computed |
| Cluster attribute exists | `data.units.cluster_by` names `site`, which is not a unit attribute |
| Cluster is constant within a unit | `cluster_by: site`, and `p1`'s [measurement rows](#what-isnt-a-repeat) declare `S1` and `S2` — the collapse would file `p1` under whichever the file lists first, and its real site would be on both sides of a split |
| Clustering looks undeclared | `site` has 6 distinct values across 240 units but `cluster_by` is unset (warning) |
| Folds fit inside the clusters | `{kind: fold, k: 10}` with `cluster_by: animal_id` over 6 animals — clusters are indivisible, so `k` may not exceed the cluster count |
| Folds fit inside the cells | Superseded by *One split, not one cell each*, the row for the identical combination: a `{kind: fold}` level beside `allocation: between` or a non-empty `sweep.groups` is refused outright (`E-REPL-FOLD-CELLS`) rather than checked against the smallest cell's size, since drawing folds within a cell is not built |
| Fold count is legal | `{kind: fold, k: 1}` — `k` must be an integer ≥ 2, or `all` for leave-one-out |
| Fold strata survive clustering | `{kind: fold, stratify_by: label}` with `cluster_by: animal_id`, but `label` varies within animal `A3` — a stratum can't be balanced across a split that can't divide the cluster |
| Clustered deltas aren't computed | `data.units.cluster_by` is declared and the design resolves to a comparison — a `vs_baseline`, or a `statistics.contrasts` entry; each condition's own interval reads the cluster as the draw and no contrast construction does — specified, not built in this build |
| Baseline leaves contrasts confounded | `sweep.baseline` fixes a value on every `grid` axis (`analysis.method: pearson`, `analysis.min_samples: 30`) over a grid of `method: [spearman, kendall]` × `min_samples: [30, 50]`, so 2 of the 4 contrasts differ on both and are reported `confounded: true`; leaving one axis unfixed gives a baseline per cell instead (warning). This check reads `grid`'s axes alone, and a baseline may not fix a [group axis](#expansion-modes) at all (`E-SWEEP-BASELINE-GROUP`), so a group axis is never one of the axes it counts |
| Contrast names a condition | `statistics.contrasts[0].of` is `occasions=4`, which no condition's label matches |
| Contrast has two distinct sides | `statistics.contrasts[1]` sets `of` and `against` to the same condition |
| Contrast has units in common | `statistics.contrasts[0]` compares two conditions whose completed units don't intersect, so no paired difference exists. Covers the case *Allocation deltas aren't computed* above does not: two same-arm conditions with a `within` stratum, or any pair `resolve_units` happens to leave disjoint, that carry no differing [group axis](#expansion-modes) between them — that row reads `differing_axes ∩ selectors`, this one reads the intersection `stats.paired_keys` actually computes |
| Contrast stratum is an attribute | `statistics.contrasts[1].within` names `site`, which is not in `data.units.attributes` |
| Contrast stratum is populated | `contrasts[1].within: {dx_family: rare}` leaves 6 paired units; below `limits.min_reported_n` (warning) |
| Reporting stratum is an attribute | `statistics.report_by` names `site`, which is not in `data.units.attributes` |
| Reporting stratum is populated | `report_by: [dx_family]` has a level with 4 units; below `limits.min_reported_n` (warning) |
| Weight attribute exists | `data.units.weight_by` names `sampling_weight`, which is not a unit attribute |
| Weights are usable | `sampling_weight` holds a zero or negative value for 3 units; a weight is what a unit stands for |
| Weight is constant within a unit | `weight_by: sampling_weight`, and `p1`'s [measurement rows](#what-isnt-a-repeat) carry 1 and 99 — a weight is what one unit stands for, not what one measurement does |
| Weighted deltas aren't computed | `data.units.weight_by` is declared and the design resolves to a comparison — a `vs_baseline`, or a `statistics.contrasts` entry; each condition's own value and interval are weighted and no contrast construction is — specified, not built in this build |
| Weighting looks undeclared | `sampling_weight` varies across units and looks like an inverse sampling probability, but `weight_by` is unset (warning) |
| Resample strata exist | `statistics.resample.stratify_by` names `count_stratum`, which is not a unit attribute |
| Resample strata survive clustering | **A stratum must be constant within a cluster, and a resample's draw is a cluster drawn within its stratum.** `statistics.resample: {stratify_by: [label]}` with `cluster_by: animal_id`, but `label` varies within animal `A3` — a resample draws whole clusters, so a cluster carrying two stratum values can be drawn within neither |
| Correction declared for a family | 6 enumerated conditions × 3 metrics produce a family of 15 baseline comparisons with `statistics.correction: none` (warning). Not raised for a `sample`-only sweep, whose draws aren't a family |
| Correction can be applied | `statistics.correction: fdr_bh`, but no comparison in the family will carry a p-value — `statistics.null_test` is undeclared, or its `shuffle` reaches none of them; Benjamini-Hochberg has nothing to adjust (warning) |
| Hypothesis needs baseline | `hypotheses[0].compare.to: baseline` but `sweep.baseline` is not declared |
| Hypothesis bound exists | `hypotheses[0].evaluate_on` is `ci95_lower`, but `data.units` is undeclared and template `generic` defines no `aggregate`, so no metric this run computes can carry an interval |
| Hypothesis names a real contrast | `hypotheses[1].compare.contrast` is `invariance`, which `statistics.contrasts` does not declare |
| Hypothesis names a metric | `hypotheses[1]` declares `compare.contrast` and no `metric`; a contrast reports a value per step metric, so the quantity under test is unnamed |
| Hypothesis form matches its metric | `hypotheses[1].metric` names a metric of a `scope: "summary"` step but declares `compare`; a summary metric is one value per run, not a contrast between conditions — and a condition-step metric without `compare` is the same mistake inverted |
| Hypothesis has an inference base | `hypotheses[0]` names a metric under the same declarations, without a bound: every metric will be `basis: repeats`, so it can be reported but not tested (warning) |

The unknown-key check matters more than it looks: a mistyped key in a hand-edited YAML file is otherwise silently ignored, and the run proceeds with a default while you believe you changed something. Since [the schema is closed and `validate` checks every key against it](#the-one-config-file), any key not in the spec is a typo by construction — except inside a block the schema declares as a whole leaf, where the walk stops and the keys within it are not reached: a `hypotheses` or a `statistics.contrasts` entry, a `replication.repeats` entry of kind `seed` or `fold` (a `batch` level is closed), and the mapping form of `data.units.from`. A key not in the spec there is ignored rather than reported — which in the first three means a misspelled `evaluate_on`, `within`, or `n` silently keeps its default — and each is closed by the slice that owns its block.

**Every threshold in that table lives in `limits`**, not in a flag, an environment variable, or a core default nobody can see. A threshold is a parameter of the run like any other: it decides whether the run is allowed to proceed, or whether a reader is warned about the number they're looking at, and a value with that much authority belongs in the file being hashed rather than in the tool's source. `init` writes the defaults; changing one is an ordinary edit, and it moves `parameters_hash` along with everything else — so `diff` prints a raised `max_failed_fraction` as the parameter delta it is, and two runs that disagreed about what counted as too much attrition can be told apart rather than looking identical. This is [Everything is in the file](design-principles.md#everything-is-in-the-file) applied to core's own knobs, which would otherwise be the one set of parameters living outside it.

Six things deliberately absent from that table: the unit failure rate and the ineligible fraction are both enforced by `run` as it goes — `limits.max_failed_fraction` fails the run and `limits.max_ineligible_fraction` warns, as when condition `03_arm=velocity_1.0` turns out to be buildable for 96 of 330 units — a reporting stratum's thinness *among completed units* and a corrected interval's draw floor are both reported once a run has executions to count them from, as [`W-STATS-STRATUM-THIN`](#warnings-core-reports) and [`W-STATS-CORRECTED-THIN`](#warnings-core-reports) — distinct from the "Reporting stratum is populated" row above, whose [`W-STATS-REPORTBY-THIN`](#warnings-core-reports) counts the roster `validate` can already see, and distinct also from *Resample draws fit the family*'s [`W-STATS-RESAMPLE-FAMILY`](#warnings-core-reports), which needs no run at all: comparisons resolve from the declarations alone, so that bound is checked at `validate` time rather than waiting on executions — lockfile drift is checked by `resume` against the run it's resuming, and whether the [apparatus](#the-apparatus-core-can-only-observe) is reachable is checked by `dry-run`. The first five need a run to have happened, and `validate` takes a config path: eligibility in particular is a fact about what a step [declared](#what-isnt-a-repeat) once it ran, which no declaration in the config predicts, and which units survive to be counted for a stratum or a corrected interval is the same kind of fact. The sixth could be checked here and deliberately isn't: `validate` may read your config and your input, and may not reach anything outside the machine, because it's the command you run in a loop while editing YAML and a probe is metered by somebody else.

None of that makes `validate` a read-only pass over YAML. It imports your `entrypoint`, because [it has to](#generators) — the execution plan is a property of the step classes — and that is what lets the batch row above read a step's declared `nondeterministic`, and what makes a package that won't import a `validate` failure rather than a surprise four hours into a `run`. The cost is worth naming beside the promise above: an import executes your package's module scope, so the *reach nothing outside the machine* guarantee is one core makes about its own behavior, not one it can enforce over your code — a module that opens a socket at import time reaches the network on every `validate`. Keep module scope to definitions and the two claims coincide, which is what the generated package does.

**A fifth class is absent for a harder reason: what a step reads, calls, and returns is not a declaration.** Core [never inspects the body of your Python](design-principles.md#greenfield-only), so which parameter a step reads, which step it names in a call, and which keys it returns all exist nowhere until it runs. Those are enforced as it does, by the objects core owns — `cfg`, `io`, and the returned mapping — and each fails that execution the way any other error in it would:

| Checked as a step runs | Example failure |
|---|---|
| Scope read direction | `step02_fit_model` (`scope="condition"`) called `io.read_upstream("step03_analyze", …)`, which is `scope="repeat"` and runs later |
| A swept parameter has no value here | `step01_load_cohort` (`scope="run"`) read `analysis.method`, which `sweep` varies — see [Step scope](#step-scope) |
| The named metric exists | `hypotheses[0].metric` `step03_analyze.r` names a key `step03_analyze` never returned; the hypothesis is recorded unevaluated |
| `Estimate` is summary-only | `step03_analyze` (`scope="repeat"`) returned an `Estimate`; an interval per repeat is not something core will record — see [`Estimate`](#estimate-carries-your-interval-without-core-claiming-it) |
| `Estimate` labels its method | `step04_compare_methods` returned an `Estimate` with `ci95` and no `method`; an interval nobody labelled is unreadable |
| A recorded column doesn't collide | a step recorded a column named `label`, which `null_test.shuffle` also resolves as a unit attribute |
| A derived metric doesn't collide | template `generic`'s `aggregate` returned `r`, which `step03_analyze` also recorded as a per-unit column; one key in `aggregated` cannot hold both a column mean and a derived value — see [`aggregate`](#templates-where-parameters-are-defined) |
| A returned value is recordable | `step03_analyze` returned `{"scores": [0.4, 0.7, …]}`; a returned value is a scalar, and a list of them is an artifact or a unit column — see [Steps and artifacts](#steps-and-artifacts) |

Each of those raises a [`ContractError`](#errors-core-raises) carrying its own identifier, except the hypothesis row.

The cost is real and worth naming: a hypothesis that names a metric no step returns is not caught until that step has run. What `validate` catches instead is everything about the hypothesis that *is* declared — its form, its contrast, its baseline, and whether any metric in this run could carry the interval it asks for. The alternative would be a step declaring its return keys up front, which is a second source of truth for something the `return` statement already states, and the [defaults-file argument](#there-is-no-separate-defaults-file) applies to it unchanged.

`publishable dry-run` goes further: it validates, builds the input manifest, probes the apparatus, resolves the run directory, and prints every artifact path that *would* be written — without executing a step or creating anything. It's the command that pays for the expensive pre-flight, which is why the two are separate names rather than one command and a flag.

### Warnings core reports

A warning is a [diagnostic](#exit-codes-and-diagnostics), not an exception: nothing raises one and nothing catches one. It carries a stable `W-` identifier for the same reason an error carries an `E-` one — a message gets clearer over time, and something pinned to the wording breaks when it does. A warning never changes an exit code; it changes what the record says core was unsure of. Some fire at `validate` time, from the declaration alone; others fire at `run` time, from what the declaration met once units and executions were real — the table names which, in each row's condition.

Each row states the condition, not the wording.

| Reported when | Code |
|---|---|
| A unit attribute looks like a cluster identifier while [`data.units.cluster_by`](#clustered-units) is unset, checked at `validate` against the resolved roster: every unit carries a value for it, its values are not all numeric — `units.is_measurement_numeric` reads at least one as neither a number nor a string that parses as one — it takes more than two distinct values, and at least one of those values is held by more than one unit. **The trigger is structural, and deliberately carries no name test**: few distinct values with many units each is what a cluster *is*, so unlike `W-DATA-WEIGHT-UNDECLARED` this needs no guess about what a column is called. Each clause earns its place — the type clause keeps it off `age`, `dose` and `latency`, whose distinct values are also each held by several units; the third keeps it off a level set like `label` or `sex`, two clusters being no inference base at all when a cluster-robust *t* has df = clusters − 1; the fourth keeps it off a column that is effectively a second key. An attribute another declaration already accounts for is excluded: one a [`sweep.groups`](#expansion-modes) axis names or an `assign.from` reads, since every `between` design would otherwise report one; any `stratify_by`, which must be constant within a cluster and so is coarser than one; and [`statistics.null_test`](#what-isnt-a-repeat)'s `shuffle`, which names the label a cluster is what shuffling *respects*. The cost is a missed integer-coded identifier, which is the right way to be wrong here — a numeric column with repeated values is a measurement far more often than an identifier. Reported for the first such attribute in sorted order, `cluster_by` naming one attribute and the remedy being the same for each | `W-DATA-CLUSTER-UNDECLARED` |
| A completed condition's `ineligible` fraction of its `resolved` units exceeds `limits.max_ineligible_fraction`, checked per step as `run` goes | `W-DATA-INELIGIBLE` |
| A unit attribute looks like a sampling weight while [`data.units.weight_by`](#weighted-samples) is unset, checked at `validate` against the resolved roster: its name contains `weight`, `_prob` or `probability` case-insensitively, every unit's value for it is a positive finite number, and those values are not all equal. All four conditions are the trigger — the name test is what keeps this off `age`, `dose` and `latency`, and the varying test is what keeps it off a constant column that weights nothing. Reported for the first such attribute in sorted order, `weight_by` naming one attribute and the remedy being the same for each | `W-DATA-WEIGHT-UNDECLARED` |
| No `uv.lock` is found at the repository root when a run starts — the environment is unpinned, and `reproduce` will not be able to restore it. This fires on every scaffolded run today: bootstrapping, not a defect, until `publishable` itself is published to an index a lockfile can resolve | `W-ENV-UNLOCKED` |
| `conditions × repeat total` exceeds `limits.max_executions`, checked wherever the total is resolvable outright — not under an unresolved `{kind: fold, k: all}`, where an unknown total must not be reported as though it were a small one | `W-EXEC-BUDGET` |
| A [hypothesis](#pre-registration) names a metric under a run where `data.units` is undeclared and the template defines no `aggregate` — every metric will be `basis: repeats`, reportable but not testable against an interval | `W-HYPOTHESIS-INFERENCE-BASE` |
| [`replication.repeats`](#a-batch-says-when-not-what) declares a `batch` level but no step in the pipeline sets `nondeterministic = True` | `W-REPL-DETERMINISTIC` |
| `replication.repeats`'s total across every declared level is below the template's `default_repeats`, checked only once every level's count is resolvable — a floor warning derived from an already-invalid design would be noise | `W-REPL-FLOOR` |
| A template's `aggregate` produced no usable value for a completed condition and step — it raised, a returned key collided with one a step already recorded, or every resample draw of it was degenerate. Reported at `run` time; the recorded columns' own summaries are unaffected, and only the derived metric is lost | `W-STATS-AGGREGATE-FAILED` |
| A [comparison](#contrasts-claims-that-arent-condition-vs-baseline) declaring `within` is thinner than `limits.min_reported_n`, at either of two points: at `validate`, when fewer units of the roster it can already see match the stratum — skipped for a `within` naming an attribute `E-STATS-CONTRAST-WITHIN` just refused — and at `run`, when the comparison's realized `n_paired` is below it | `W-STATS-CONTRAST-THIN` |
| A family's size implies a corrected level (`correction_level`) smaller than the resample's surviving draws can support — the *corrected*, smaller level is the one that can't be met, so `ci95_corrected` is left `null` rather than reported too narrow | `W-STATS-CORRECTED-THIN` |
| `statistics.correction: fdr_bh` is declared over a family with at least one comparison, but nothing in it will carry a p-value — `statistics.null_test` is undeclared, or a parameter-axis contrast, which can never supply one, accounts for every member — so every `ci95_corrected` will be `null` | `W-STATS-CORRECTION-INAPPLICABLE` |
| A family of more than zero comparisons per metric exists and `statistics.correction` is `none` — every interval is reported uncorrected, and each records `correction: null` to say so | `W-STATS-FAMILY` |
| A level of a [`statistics.report_by`](#reporting-strata) attribute would hold fewer units than `limits.min_reported_n`, checked at `validate` against the roster it can already see — the WHOLE roster, not a group axis's own arm, a gap [§ What isn't a repeat](#what-isnt-a-repeat) records and, with a declared group axis no longer refused at `validate`, a live one rather than a latent one | `W-STATS-REPORTBY-THIN` |
| `statistics.resample` is declared beside `data.units.cluster_by` and falls in fewer clusters than `limits.min_clusters` — counted over `data.units.holdout`'s realized **test** partition when one is declared and its draw succeeds, the roster otherwise (including when a declared holdout's draw could not be performed, which carries its own finding), because a resample draws from the per-unit table and that is what the table holds; a resample draws whole clusters, so the interval rests on that many independent draws however many units they hold | `W-STATS-RESAMPLE-CLUSTERS` |
| `statistics.resample.n` is below the draw count the resolved comparison family's tightest corrected level needs, under `holm` or `bonferroni` — a **lower** bound, since the family is comparisons × metrics and the metric count is not knowable before the run | `W-STATS-RESAMPLE-FAMILY` |
| A derived metric's resample produced fewer surviving draws than were requested, though not zero — the interval is still reported, but rests on less than it claims | `W-STATS-RESAMPLE-THIN` |
| A step records a metric named `by` — the reserved key the reporting strata are attached under — so that column keeps its recorded value but is reported with no contrast delta, and no strata are reported for the step at all | `W-STATS-STRATUM-SHADOWED` |
| A `statistics.report_by` level *completed* fewer units than `limits.min_reported_n`, checked at `run` time against what actually finished — the attrition between the roster `validate` saw and what a run completes is exactly what this catches beyond `W-STATS-REPORTBY-THIN` | `W-STATS-STRATUM-THIN` |
| A `summary`-step [`Estimate`](#estimate-carries-your-interval-without-core-claiming-it) carries a `ci95` but no `n` — an interval with no stated denominator is the disclosure risk `limits.min_reported_n` exists to catch, and `study add` cannot check what it cannot see | `W-STEP-ESTIMATE-N` |
| A [`sweep.baseline`](#expansion-modes) fixing a value on every `sweep.grid` axis leaves at least one condition differing from it on more than one of them, so that comparison is reported `confounded: true` and its delta mixes two effects. Checked at `validate` over `sweep.grid`'s axes alone — no other mode's — and only for a baseline that fixes every one of them. A baseline leaving a *`grid`* axis free is a different shape rather than this fault, expanding to [one baseline per cell](#expansion-modes) of the free axes instead of one reference for the whole run, so the row's condition does not hold and nothing is reported. **That mechanism is the `grid` case only, and every other mode is silence for a narrower reason.** A baseline fixing *some* of the paths a multi-path [`sweep.paired`](#expansion-modes) axis varies counts that axis **fixed**, so nothing expands per cell: there is one baseline, and every comparison against it still differs on the paths the baseline left alone — and is reported `confounded: true` at run time for each level that *also* differs on a fixed path, since `confounded` is more than one differing path rather than any. A level whose value on the fixed path happens to equal the baseline's differs on one path only and is reported clean, so the same half-fixed axis can yield both verdicts at once. And a `sweep.paired` axis is outside the check whether the baseline touches it or not, so the remedy in the message — leave the axis you are stratifying over free — names an outcome a free `grid` axis delivers and a free `paired` one does not. A free [`sweep.groups`](#expansion-modes) axis does deliver it, [expanding per cell](#expansion-modes) exactly as a `grid` axis does, and is silent here for its own reason: this check reads neither a group axis nor a baseline fixing one, so a design confounded across an arm and a parameter is marked at run time and warned about by nothing — deliberately, the marking being the disclosure and this warning a `grid`-only convenience over it, so nothing is owed here. Silence under any of them is not a verdict that the design confounds nothing: what each comparison is taken against is [`vs_baseline`](#expansion-modes)'s question, not this row's | `W-SWEEP-BASELINE-CONFOUNDED` |
| A config's declared `template_version` differs from the installed template's reported version — in this build, compared against the one version core itself writes, since `generic` is the only installed template and a template class reports no version of its own; a plugin's own version is read once the [registry](#creating-a-plugin-publishable-plugin-new) resolves it. Never checked for a [project-local template](#templates-where-parameters-are-defined): `init` writes no `template_version` line against one, and a declared value is not compared against core's constant whatever it says — the reason is [§ Three hashes](#three-hashes)'s. The message also names every `parameter_spec` parameter carrying a default that this config does not set — computed only under that mismatch, and stated as unset-and-defaulted rather than as new, since the declaration does not say which | `W-TEMPLATE-VERSION` |

`W-ENV-UNLOCKED` is the one row above whose *firing condition* is a gap in this project rather than in yours: it fires on every scaffolded run right now, because `publishable` cannot yet be resolved from an index a lockfile pins against. That is bootstrapping, not a defect — a reader hitting it on their first run is seeing an accurate, expected state, not a misconfigured one. (`W-STATS-REPORTBY-THIN` above still fires on your thin stratum, not on this project's state — only its *precision*, counting the whole roster instead of a group axis's own arm, is a gap in this build.)

### Errors `validate` reports

A validate-time error is a [diagnostic](#exit-codes-and-diagnostics), not an exception —
`validate` collects every fault it can find in one pass, and modelling each as a raise would
force it to stop at the first. [§ Errors core raises](#errors-core-raises) covers the surfaces
that raise instead — the run-time one, where there is a step to raise into, and the load-time
refusals a command meets before any step exists; these are the codes a *command* reports, and a
code raised at load can be in both, reported here and raised there. Each
carries a stable `E-` identifier for the same reason a raise-time code does: a message gets
clearer over time, and something pinned to the wording breaks when it does.

Some of these are raised where the roster and the repeat levels are resolved, rather than in
`validate` itself — `validate` resolves both while checking a declaration and reports whatever
it catches under the same code. That reuse is not a guarantee that one problem always gets one
identifier regardless of surface: `{kind: fold, k: 0}` reports `E-REPL-N` at `validate` (its
budget loop returns before the roster-partitioning code runs) and `E-REPL-FOLD-K` at `run`
(where that code is what runs) — the same declaration, two codes, split exactly by which surface
caught it first.

A code ending `-UNSUPPORTED` is deliberately absent from this table: it refuses a block this
build reads but does not yet execute, and it retires with the slice that implements the feature
it names — [§ The one config file](#the-one-config-file) is where that family's rule lives, and
where each currently-refused block is named and marked `NOT BUILT` in the config it shows.
Documenting one here would pin a row this project
already commits to deleting on a schedule neither this table nor its author controls.

Each row states the condition, not the wording.

Five codes return `validate_config` early, in this order: a config that does not parse
(`E-CONFIG-PARSE`), a container-shaped `E-CONFIG-SHAPE` fault, a `templates/*.py` that fails
to load (`E-TEMPLATE-LOAD`), a `templates/` core cannot merge (`E-TEMPLATE-COLLISION`), and an
unresolvable `experiment_type` (`E-TEMPLATE-UNKNOWN`). That is five *codes*. A plugin-side collision adds no sixth: an installed distribution's template claim is decided in the same merge a local one is, so it arrives here as `E-TEMPLATE-COLLISION` — a code already counted. The identifiers a plugin registry mints for its other groups reach this list not at all, for two different reasons: [`E-PLUGIN-COLLISION`](#errors-core-raises) is reported by a check that does not return early, the way `E-TEMPLATE-COLLISION`'s is; `E-PLUGIN-DECORATOR` and `E-PLUGIN-LOAD` are not reported by `validate` at all, early-return or not — `validate` never imports a plugin, so neither check runs there. `E-TEMPLATE-LOAD`
covers three shapes — a file that raises while importing, one that imports cleanly and registers
nothing, one that registers a non-`BaseTemplate` — and a `Param` whose construction raises is the
first of them, so a bad `default=None` or a
[`requires_env`](#a-credential-can-belong-to-a-parameter-value) mapping that is not total over
`choices` adds a shape to `E-TEMPLATE-LOAD` without adding a row to [the table this section carries](#errors-validate-reports) or a sixth
code to this count. Each returns because every check after it reads what it just found wrong, and each is
what triggers its own return rather than sitting behind it. Every other row in this table fires only once all five have passed — except
`E-CONFIG-TYPE` and `E-CONFIG-KEY-UNKNOWN`, which `check_envelope` finds as the document
loads, before any of the later four returns is possible, and except the one non-container
`E-CONFIG-SHAPE` fault — a `sweep.groups` axis name that renders blank — which `_check_shape`
reports on its way past without giving up: nothing later indexes into it, so there is nothing
to cascade.

So a parse fault reports `E-CONFIG-PARSE` and nothing else at all. A container-shape fault
reports every `E-CONFIG-SHAPE` finding `_check_shape` turns up — it loops over every block
rather than stopping at the first — plus whichever of those two envelope rows the document
also earned, and none of this table's other rows — including `E-TEMPLATE-LOAD`,
`E-TEMPLATE-COLLISION` and `E-TEMPLATE-UNKNOWN`, whose checks the shape return comes before, so
those never appear together however wrong all of them are. A load failure reports
`E-TEMPLATE-LOAD` exactly once and, apart from those same two envelope rows, none of the
others — the merge that would compute a collision, or resolve the name at all, never ran, since
`discover_local` raises before either question is reached. A collision reports
`E-TEMPLATE-COLLISION` exactly once and, apart from those same two envelope rows, none of the
others — `E-TEMPLATE-UNKNOWN` included, since the call that would have resolved the name raised
instead of answering it, and a name whose meaning a collision leaves unanswered is not also
unknown. `E-TEMPLATE-LOAD` can never appear beside it: a collision is computed only once
`discover_local` has walked the whole directory without a load fault, so reaching the collision
check at all already rules one out. An unresolvable `experiment_type` reports
`E-TEMPLATE-UNKNOWN` exactly once, since that check returns immediately after, and,
likewise apart from those same two envelope rows, none of the others.

| Reported when | Code |
|---|---|
| A key under a container `check_envelope`'s `LEAF_TYPES` table declares, or a top-level key, that the table does not name — checked with a `difflib` hint, skipping the `parameters` and `sweep` subtrees entirely since each has its own closure (`E-PARAM-UNKNOWN`, `E-SWEEP-KEY-UNKNOWN`), and never descending into a known leaf's own value (a typo inside a `from` mapping is reached by no check at all — not by `_check_shape` either, which checks a container's shape and never the names inside one; [§ Validation](#validation) names the whole-leaf blocks that costs and the slice that closes each. `data.units.holdout` is **not** one of them: the table declares each of its leaves, so a misspelled child inside a non-empty `holdout` block is reported here); a non-string YAML mapping key is coerced with `str()` first so it is still reported. The same code also covers one dynamic block this way: each axis block under `data.units.assign`'s own keys, checked against the closed set `{method, from, ratio, block_size, stratify_by, seed}` — the axis name itself (`arm` in [§ The one config file](#the-one-config-file)'s expansion) stays open, since it is user-chosen and no fixed dotted path can name it, but the fields inside it are not, so a misspelled `stratifyy_by` is reported the same way a misspelled top-level key is | `E-CONFIG-KEY-UNKNOWN` |
| The config file does not parse as YAML, or parses to something other than a mapping | `E-CONFIG-PARSE` |
| A top-level block, or a nested container `_check_shape` walks before its items — `data.units` and its `attributes`, `sweep.baseline`, `sweep.grid` and each axis's values, `sweep.groups` and each entry's `by`/`levels`, `replication.repeats` and each level, `statistics.contrasts`, `statistics.report_by` — is present and not the mapping, list, or string its position requires; unset (`null`) is treated as absent, matching `E-CONFIG-TYPE`. One value fails this row while being of the right type: a `sweep.groups` entry whose `by` renders to a blank axis name. Checked as [`label_for`](#expansion-modes) renders it — the segment after the last `.` — because that is what a reader sees and what a condition directory carries, so `arm.` fails it as surely as `""` or `" "` does. Such a name is still an axis to `expand`, which renders conditions and names their directories from it, while nothing can resolve an `assign` block or an arm under it. That one is not a container fault and so does not trigger the early return this section's intro describes: it is reported alongside every other row the config earns | `E-CONFIG-SHAPE` |
| A leaf `check_envelope`'s `LEAF_TYPES` table declares is present and not its declared type — a `bool` never satisfies any leaf's type, since the table declares none as `bool`, and an `int` satisfies a `float` one; unset (`null`) is treated as absent | `E-CONFIG-TYPE` |
| The resolved template declares a [`required_env`](#secrets--credentials) variable that has no value in the environment or in `.env`. A template-level list says what an experiment *type* always needs, so this is checked from the class alone, before any condition is expanded, and reported at `experiment_type` — the field that decided which template's list applies. One finding per unset variable, in the order the list declares them, so a template needing three keys names all three rather than one at a time. Core loads `.env` from the repository root before this check runs and never overrides a variable already exported, so a value set in the shell satisfies it. The **value** is never printed: the message names the variable and says where to put a value, which is the whole of what a reader needs and the whole of what is safe to say. Distinct from `E-CRED-PARAM-MISSING` in what it can name: that one reports under a parameter's own path and names the value and the condition that selected it, and this one has only the template | `E-CRED-MISSING` |
| A parameter *value* the sweep actually resolves declares a credential through [`requires_env`](#a-credential-can-belong-to-a-parameter-value) that has no value in the environment or in `.env`. Checked as the **union over the conditions [`expand`](#expansion-modes) resolves**, which is the entire reason a value-level requirement exists rather than a template-level list: a config that selects Azure and OpenAI is silent about Ollama's key, and one that selects none of them is silent about all three. Reported at the parameter's own dotted path, so the finding carries the parameter, and the message names the value and the condition that selected it — together the three facts a reader needs to decide whether to supply the key or drop the condition, and the reason this is a second code rather than a second emit site of `E-CRED-MISSING`, whose message can name none of them. A variable required by two conditions is reported once, attributed to the first that selected it, since one missing value is one thing to fix. A value with no key in the mapping requires nothing: `requires_env` is total over `choices`, and [`sweep.ablate.remove`](#expansion-modes) resolves a nullable parameter to `null`, which is not a choice | `E-CRED-PARAM-MISSING` |
| A resolved comparison — a generated `vs_baseline` or a declared [`statistics.contrasts`](#contrasts-claims-that-arent-condition-vs-baseline) entry — whose two conditions differ on a declared [`sweep.groups`](#expansion-modes) axis. A declared contrast is the route that reaches this on its own: a `vs_baseline` comparison takes each condition against its own cell's baseline, so it crosses a group axis only where the baseline fixes a group level, which `E-SWEEP-BASELINE-GROUP` and `E-SWEEP-ABLATE-BASELINE-GROUP` refuse outright — that route still reports here, always beside one of them. Read **per comparison**, not for the whole resolved family the way `E-DATA-WEIGHT-CONTRAST` and `E-DATA-CLUSTER-CONTRAST` below are: [§ Allocation](#allocation-within-subjects-or-between-subjects)'s pairing table says two conditions differing only on parameter axes under `between` share that arm's units and are paired within it, but two conditions differing on *any* group axis hold disjoint sets of units by construction — unpaired — so a `groups × grid` design's within-arm comparisons stay legal while its cross-arm ones are refused. No construction in this build computes an unpaired interval: `paired_t_over_units` takes a list of per-unit differences and nothing else, and there is no `welch_t_over_units` or unpaired percentile form to call. Reached, the delta would be computed over an empty pairing — `stats.paired_keys` over two disjoint arms — and published as `null` beside a `paired: true` that is false. Temporary: the refusal lifts with the slice that builds the unpaired estimator family | `E-DATA-ALLOCATION-CONTRAST` |
| `data.units.allocation` is present and is not `within` or `between`. Checked before `E-DATA-ALLOCATION-NO-ARMS` and `E-DATA-ALLOCATION-WITHIN-ARMS` run, so each can assume `allocation` is already one of the two — matching `ASSIGN_METHODS`'s own enum-check pattern for `assign.<axis>.method` in the same function. An absent or `null` value is `within`, the default, and is not this row's concern | `E-DATA-ALLOCATION-METHOD` |
| [`data.units.allocation`](#allocation-within-subjects-or-between-subjects) is `between` and `sweep.groups` declares no axis to say what the arms are — no axis at all, or none whose `by` this build can read, which is what a malformed `groups` entry leaves it with. The pair is the check rather than either half: `between` says how a unit reaches an arm, not what the arms are, so a design declaring it alone has one cohort and nothing to divide it into. Read from the declarations, so it reports whether or not a roster resolved | `E-DATA-ALLOCATION-NO-ARMS` |
| The mirror of `E-DATA-ALLOCATION-NO-ARMS`: [`sweep.groups`](#expansion-modes) declares an axis, but [`data.units.allocation`](#allocation-within-subjects-or-between-subjects) is `within`, or absent (which defaults to it). `within` says every unit appears in every condition, so a unit can't be in one arm and in all of them — the fault [§ Validation](#validation)'s *Arms need allocation* names, and the pair this row and its mirror form is what makes handing every condition on a group axis the same, whole roster structurally impossible rather than merely avoided. Read from the declarations, so it reports whether or not a roster resolved. Gated on `allocation` being exactly `null`/absent/`within`, not on a bare declared axis, so an out-of-enum `allocation` value is left to `E-DATA-ALLOCATION-METHOD` to catch rather than being misreported here as `within` | `E-DATA-ALLOCATION-WITHIN-ARMS` |
| A `data.units.assign` block's `method` is `blocked` and its `block_size` — declared or, for `"auto"`, resolved (twice `ratio`'s sum, rounded to a whole number of units) — cannot fill each arm's share exactly — **one code over the whole malformed-value family, in two parts**. First, a *declared*, non-`"auto"` `block_size` that is not a positive `int` at all — `0`, a negative number, `2.5`, `"four"`, `null` (a bare `range(0, len(keys), block_size)` in `units.assignment_for` either raises a bare `ValueError` or silently produces no blocks, and neither is a diagnostic). This half never applies to `"auto"` itself, which resolves to a positive `int` by construction. Second, for a resolved `block_size` — declared or `auto` alike — **each declared level's own per-block share** — `block_size` × that level's share of `ratio` — is not a whole number: [§ Allocation](#allocation-within-subjects-or-between-subjects) states the rule as "every block fills each arm exactly," and that is a **different** test from whether the sum of `ratio` divides `block_size` evenly — neither implies the other. `ratio: {a: 0.5, b: 0.5}` sums to 1 and `block_size: 1` divides it, yet the per-block share is `0.5` for both levels; `ratio: {a: 2, b: 2}` sums to 4 and `block_size: 2` does *not* divide it, yet each level's own share, `2 × 2 / 4 = 1`, is whole. `"auto"` is checked by this second half rather than exempted from it: for `ratio: {a: 0.33, b: 0.33, c: 0.34}`, resolved `auto` is 2 and no level's share of it is whole, refused here rather than left to starve a level in every block and fail at `units.assignment_for`'s `E-DATA-ASSIGN-LEVELS` instead — the validate-clean-then-fail gap this whole row exists to close, reached through the derived value exactly as it can be through a declared one. `ratio`'s shares are read the same way `E-DATA-ASSIGN-RATIO`'s own accept path establishes them usable — an absent, empty, or malformed `ratio` (already `E-DATA-ASSIGN-RATIO`'s own fault to report) falls back to an equal share per level. The second half alone is **skipped when the axis's declared `levels` do not resolve to a non-empty list of strings**, `sweep.groups`'s own shape fault — it needs `levels` to have a per-level share to check at all. The first half is not: a malformed declared value is reported regardless of whether `levels` resolve. Not reported under `random`, where `block_size` means nothing — `from`'s own reason, the discriminator deciding which of a block's other fields are read | `E-DATA-ASSIGN-BLOCK-SIZE` |
| A `data.units.assign` block's `method` is `blocked` and [`data.units.cluster_by`](#clustered-units) is a non-empty string — a block fills to an exact unit count and a cluster is indivisible, so no `block_size`, declared or `auto`, honours both at once, and `units.assignment_for`'s own `blocked` branch raises `NotImplementedError` for the identical combination rather than realizing one rule over the other. Checked ahead of *Block size fills the arms* — [§ Validation](#validation)'s row for the same `blocked` branch — so once this fires, that row's own check on the same block never runs: a `block_size` this build refuses to honour beside a cluster is not a value worth validating on its own terms too. Read from the declarations alone, so it reports whether or not a roster resolved. Not reported under `random`, which draws whole clusters instead of filling to an exact size and so has no such conflict with `cluster_by` — [§ Clustered units](#clustered-units) states the asymmetry. The message names both honest routes: `random` for a clustered draw, `by_attribute` for a read one | `E-DATA-ASSIGN-BLOCKED-CLUSTER` |
| An arm that resolves no units, under either of the two ways an arm is decided — **one code, because it is one fault: an arm's condition would measure nobody**. Under `method: by_attribute`, the resolved attribute's values, over the resolved roster, are not exactly the declared [`sweep.groups`](#expansion-modes) levels for that axis — **set equality, in either direction**: a unit's value (including a unit carrying no value for the attribute at all) names none of the declared levels, so that unit would belong to no arm and there is no fourth part of `n` for it; or a declared level no unit's value names. `units.arms_of` is the single authority, the construction `units.clusters_of` is for `cluster_by`, and its raise is caught and reported here under its own code, the same reuse `E-DATA-CLUSTER-UNKNOWN` illustrates for its sibling. Skipped when the roster does not resolve, when the axis's `levels` do not resolve to a non-empty list of strings, or when `from` does not resolve to a unit attribute at all — `E-DATA-ASSIGN-UNKNOWN`'s own fault to report — there being nothing to partition against in any of those cases. Under `method: random` or `blocked` it is the *drawn* arm that resolves nobody: [§ Validation](#validation)'s *Every arm draws units*, where a `ratio` no declaration-only rule can fault — `{control: 1, treatment: 1000}` names every level and every share is positive — apportions a level zero units over **this** roster, and `units.assignment_for` would raise at the draw on a config that had validated clean. The draw itself is the check, run over a block every other row accepted and its plan discarded: an emptiness rule reimplemented in `validate` would be a second answer to "which units are in this arm", which is the disagreement `units.assignment_for` exists as the single producer to prevent. **Restricted to the unstratified, unclustered draw**, and the residue — three draws, excluded for two different reasons — is stated rather than left to be discovered. The first reason is the digest: `validate` has none, so it can only draw where the realized sizes do not depend on the seed, which is where `_apportion` decides them from the roster size and the ratio alone. A **clustered** draw shuffles the cluster order before dealing, so which arm is left empty genuinely varies by seed, and a validate-time draw could be wrong in either direction. The second reason is the strata, and it is not about the digest at all. A stratum naming an **earlier group axis** needs that axis's realized membership, which only the run's own ordered draw produces. A stratum naming a **declared attribute** would answer the same at every seed — `units._stratum_groups` groups by the column's values in roster order and `_apportion` runs inside each group — so that exclusion buys nothing about determinism: it is that `_stratum_groups` raises for an attribute `data.units.attributes` declares and no resolved unit carries (a broken roster, which *Allocation strata exist* passes because it reads the declaration), and `validate` collects findings rather than raising. Drawing there would turn a broken roster into a traceback, and avoiding that means either swallowing that raise or repeating `_stratum_groups`' own precedence rule here — a second rule either way, and one this build does not take. All three therefore still reach this code at the draw rather than at `validate` | `E-DATA-ASSIGN-LEVELS` |
| A `data.units.assign` block's `method` is absent or `null`, or is a value other than `random`, `by_attribute`, or `blocked`. **A block that is not a mapping at all is reported here too**, as the block naming no method that it is: `envelope.py` types `data.units.assign` itself and none of its children, whose keys are axis names no fixed dotted path could ever name, so nothing else speaks for one. Which of a block's other fields are read follows from the discriminator — `from` is `by_attribute`'s, `block_size` is `blocked`'s — so a block without one describes no assignment. Deliberately not gated on `allocation`, unlike `E-DATA-ALLOCATION-NO-ARMS` and `E-DATA-ASSIGN-MISSING`, each of which reports a pair of declarations that disagree: this is a check on the block rather than on a pair of declarations, and a block naming no method describes no assignment wherever it was declared | `E-DATA-ASSIGN-METHOD` |
| `data.units.allocation` is `between` and a [`sweep.groups`](#expansion-modes) axis has no block under [`data.units.assign`](#allocation-within-subjects-or-between-subjects) — an absent or `null` `assign`, the empty `assign: {}` `init` writes, or the axis's own key left `null`. One finding per unassigned axis, in declaration order, since the remedy is one block each. This and `E-DATA-ALLOCATION-NO-ARMS` are between them the whole of [§ The one config file](#the-one-config-file)'s "REQUIRED when `allocation` is `between`", which is why that rule has no third code of its own. Not reported under `allocation: within`, where a declared group axis is [§ Validation](#validation)'s *Arms need allocation* — a different fault, reported under its own code, `E-DATA-ALLOCATION-WITHIN-ARMS`. Skipped when `assign` is present and is not a mapping, which `E-CONFIG-TYPE` already reports | `E-DATA-ASSIGN-MISSING` |
| Under `method: by_attribute`, a non-empty `assign.<axis>.ratio` or `assign.<axis>.stratify_by` — [§ Allocation](#allocation-within-subjects-or-between-subjects) calls the two "the same fault": `by_attribute` reads an arm already assigned rather than drawing one, so a `ratio` would record a proportion, and a `stratify_by` a balance, that no draw produced. One finding per offending field, so a block declaring both earns two findings under this one code rather than one that names only the first. An empty `ratio: {}` or `stratify_by: []` — what `init` writes and what most designs carry — changes no behavior and is not refused. **A wrong-typed value is absorbed here too** — a bare `ratio: 3` or `stratify_by: site` — rather than left silent: neither field is an `envelope.py` `LEAF_TYPES` leaf, so there is no `E-CONFIG-TYPE` backstop, and the closed axis-block key set checks names, not the types of their values, so nothing else in this build reads either field at all; "present and non-empty" is read structurally, so a bare string is as non-empty as a populated mapping, the same absorption `E-DATA-ASSIGN-METHOD` performs for a non-mapping block and `E-DATA-ASSIGN-UNKNOWN` for a non-`str` `from`. Not reported under `random`/`blocked`, where a `ratio` means something instead — `E-DATA-ASSIGN-RATIO`'s row below — and a `stratify_by` is [§ Validation](#validation)'s *Allocation strata exist*, `E-DATA-ASSIGN-STRATIFY-UNKNOWN` | `E-DATA-ASSIGN-NO-DRAW` |
| A `data.units.assign` block's `method` is `random` or `blocked`, and a declared, non-empty `ratio` cannot be apportioned — **one code over the whole malformed-value family**: `ratio` is not a mapping at all (`ratio: 3`); its keys are not exactly the axis's declared [`sweep.groups`](#expansion-modes) levels — a partial mapping (one entry short) or a key naming no declared level, the same set-equality construction [§ Errors `validate` reports](#errors-validate-reports)'s `E-DATA-ASSIGN-LEVELS` row uses for the resolved-attribute case; or its keys are right but a value is not a finite positive number (`{a: -1, b: 2}`, `{a: .nan, b: 2}`) — a share of zero or less draws no units for that level, and a share that is not finite is one no apportionment can divide a roster by. An empty `ratio` is equal allocation and earns nothing, matching every other row here. The not-a-mapping case is checked regardless; the other two are skipped when the axis's declared `levels` do not resolve to a non-empty list of strings, `sweep.groups`'s own shape fault. Not reported under `by_attribute`, where a non-empty `ratio` is refused outright regardless of its shape, as `E-DATA-ASSIGN-NO-DRAW` above | `E-DATA-ASSIGN-RATIO` |
| Under `method: random` or `blocked`, `assign.<axis>.seed` is present and is neither the string `auto` nor a pinned integer — `"1234"`, `1.5`, `true`, a mapping. An explicit `null` is absent, and absent is `auto`, the convention every other leaf here follows. A pinned integer is returned literally by `units.assign_seed_for` and everything else falls through to the derivation, so a wrongly-typed pin is not a fault that surfaces later: the draw succeeds, and [`allocation.json`](#allocationjson--who-went-where) records a *derived* seed under the axis whose seed the config meant to fix. [§ What `auto` derives from](#what-auto-derives-from) calls pinning "the deliberate act, and the one to take for anything you intend to cite," and the sibling field earns `E-SWEEP-SAMPLE-INVALID` for exactly this shape. A code of its own rather than a broadening of a neighbour, because each code in this family owns one field's value space — `ratio`'s, `block_size`'s, `stratify_by`'s — and `E-DATA-ASSIGN-NO-DRAW` is about a field meaning nothing under `by_attribute` rather than about a value's type. A `bool` is not an integer here, matching the exclusion `assign_seed_for` itself makes: `seed: true` would otherwise pin the draw to `1` without ever saying so. Not checked under `by_attribute`, which consults no seed at all | `E-DATA-ASSIGN-SEED` |
| Under `method: random` or `blocked`, `assign.<axis>.stratify_by` names a [`sweep.groups`](#expansion-modes) axis that is not declared *before* this one — the axis declared after it, or this axis itself. [§ Validation](#validation)'s *Stratification is forward-only*: "an axis may only stratify on one already resolved". **A sequencing requirement rather than a check on one**: axes are drawn in declaration order, and a drawn axis leaves no column, so a stratum naming one is balanced on that axis's *realized* membership — which the earlier draw has produced and a later one has not. That is also why a cycle is unrepresentable rather than something `validate` detects: the order is a total one the config already states. The declaration order is `sweep.groups`' own, the same order the run's draws are realized in, so the position this row compares is the position the draw happens at. One finding per offending name, and reported from the declarations alone, so it reports whether or not a roster resolved. **A name `data.units.attributes` declares is not this row's**, even when a group axis shares it: a stratum resolving to an attribute is balanced on the column, by the draw as well as here, so no order question arises — `E-DATA-ASSIGN-STRATIFY-UNKNOWN` covers the name that resolves to neither. Not reported for a block whose axis `sweep.groups` does not declare at all: nothing draws that axis, so it has no position to be forward of | `E-DATA-ASSIGN-STRATIFY-FORWARD` |
| Under `method: random` or `blocked`, `assign.<axis>.stratify_by` names a value that is neither a unit attribute `data.units.attributes` declares nor a [`sweep.groups`](#expansion-modes) axis at all — the one target [§ Validation](#validation)'s *Allocation strata exist* admits that a `fold`'s or `holdout`'s `stratify_by` does not. Existence only: a target naming an axis declared *after* this one is a different fault instead, [§ Validation](#validation)'s *Stratification is forward-only*, whose code is `E-DATA-ASSIGN-STRATIFY-FORWARD` — order is not this row's question, and a name resolving to a declared attribute is exempt here before either question is asked. `data.units.attributes` and `sweep.groups`, not the roster's realized columns, for the same reason `E-DATA-CLUSTER-UNKNOWN` reads that set: a stratum is read per unit when the assignment is drawn, so it has to survive resolution as an attribute or resolve as an axis. **A wrong-typed entry is absorbed here too** — a `stratify_by: [3]`, or an empty `[""]` — rather than left silent, the same absorption `E-DATA-ASSIGN-NO-DRAW` performs for the same two fields under `by_attribute`, and for its reason: `stratify_by` is no `envelope.py` `LEAF_TYPES` leaf, so there is no `E-CONFIG-TYPE` backstop, and a value of the wrong type names neither an attribute nor an axis either. Read through `units.stratum_names`, the same normalization the draw balances on, so a bare `stratify_by: site` is one name to both. One finding per offending name, so a declaration naming two earns two rather than one that names only the first. Checked from the declaration alone, so it reports whether or not a roster resolved | `E-DATA-ASSIGN-STRATIFY-UNKNOWN` |
| Under `method: random`, `assign.<axis>.stratify_by` names a stratum whose value is not the same across every unit of one cluster, under a declared [`data.units.cluster_by`](#clustered-units) — reported for the first such cluster in roster order, naming the values it carries. **A declared attribute, or an earlier group axis read through the column that axis reads**: an axis assigned `by_attribute` has membership that *is* a column's value, so a `from` varying within a cluster splits that cluster between that axis's own arms, and the halves land in different strata here, where the clustered draw allocates each independently and the cluster straddles both of *this* axis's arms — the indivisibility [§ Clustered units](#clustered-units) promises, broken one axis upstream. It needs a `from` differing from the axis name to arise at all: with the default, the stratum resolves as a declared attribute and the first half of this row covers it. An earlier axis that **draws** is exempt rather than unchecked — it allocated whole clusters, so its membership is constant within every one. A cluster is drawn whole, so an arm cannot be balanced on a stratum the cluster carries two of, and core refuses the pair rather than silently prioritizing one of the two constraints — the same rule and the same reason `E-REPL-FOLD-STRATIFY-VARIES` carries for a `fold` level's own `stratify_by`. `units.stratum_varies_within_cluster` is the constancy test, reading membership from `units.clusters_of`, the [single authority](#clustered-units), so a unit carrying no cluster value raises `E-DATA-CLUSTER-UNKNOWN` there rather than being grouped alone and made trivially constant. Checked against the resolved roster, and skipped when it did not resolve, when no `cluster_by` is declared (nothing is then indivisible), or when the name check above already reported. **Not reached under `blocked`**, whose combination with any `cluster_by` is refused outright as `E-DATA-ASSIGN-BLOCKED-CLUSTER` before a stratum's constancy is a question worth asking | `E-DATA-ASSIGN-STRATIFY-VARIES` |
| Under `method: by_attribute`, `assign.<axis>.from` — declared, or **defaulted to the axis name** when absent (§ The one config file: "`from` is `by_attribute` only, and defaults to the axis name") — is present and is an empty string (present, so the default does not apply — an empty declaration changes no behavior), or names a value `data.units.attributes` does not declare. `data.units.attributes`, not the roster's realized names, for the same reason `E-DATA-WEIGHT-UNKNOWN`'s name half reads that set: an arm is read per unit, so it has to survive resolution as an attribute. Read from the declaration, so it reports whether or not a roster resolved. **A non-`str`, non-absent `from` is reported here too**, naming its type rather than a resolved attribute: unlike `weight_by`/`cluster_by`, `assign`'s children are axis names no fixed dotted path can type, so there is no `E-CONFIG-TYPE` backstop to defer to — the same reason `E-DATA-ASSIGN-METHOD`'s own row absorbs a non-mapping block as the block naming no method that it is | `E-DATA-ASSIGN-UNKNOWN` |
| Under `method: by_attribute`, `assign.<axis>.from` — declared, or defaulted to the axis name the same way its own name check resolves it (see `E-DATA-ASSIGN-UNKNOWN`) — names a column whose value is not the same across one unit's [measurement rows](#what-isnt-a-repeat), the same shape `E-DATA-CLUSTER-VARIES`, `E-DATA-WEIGHT-VARIES` and `E-DATA-HOLDOUT-VARIES` refuse and reported the same way, through the same collapse. **The worst of the family**: a mis-collapsed cluster or holdout decides which side of a split a unit lands on and a mis-collapsed weight mis-sizes what one unit stands for, but a mis-collapsed arm decides which *condition* the unit is measured in — so the order the file happens to be in would be silently deciding it. One entry per declared axis feeds the same collapse, and each declaration is checked on its own and still raises its own code when it is the only one declared; a single unit violating more than one gets exactly one code, from whichever declaration's entry is checked first — `assign`, ahead of `holdout`, ahead of `cluster_by`/`weight_by`, matching the severity this row states. `holdout` ahead of `cluster_by` is not a further severity claim — the two say the same thing about the damage — but a fixed, deterministic order rather than an accident of dict-building | `E-DATA-ASSIGN-VARIES` |
| `data.units.holdout.method` is absent, is not a string, or is not one of `random`, `by_attribute`. An allowlist, not a denylist: a method named here and realized nowhere would validate clean and then partition on something core never drew | `E-DATA-HOLDOUT-METHOD` |
| Under `method: random`, `data.units.holdout.frac` is absent or is outside the open interval (0, 1). Both endpoints are excluded: `0` holds nothing out and `1` holds everything out, and each leaves one side of the split empty. A wrong-typed `frac` — a string, a list — is a leaf `envelope.py`'s `LEAF_TYPES` table declares, so it earns `E-CONFIG-TYPE` and never reaches this check | `E-DATA-HOLDOUT-FRAC` |
| Under `method: by_attribute`, `data.units.holdout.from` is absent or is empty — there is no column to read the partition out of, and unlike [`assign.<axis>.from`](#allocation-within-subjects-or-between-subjects) a holdout has no axis name to default to. A wrong-typed `from` is a `LEAF_TYPES` leaf too, so it earns `E-CONFIG-TYPE` instead, the same division `E-DATA-HOLDOUT-FRAC` makes | `E-DATA-HOLDOUT-FROM` |
| A `data.units.holdout` field that means nothing under the declared method: `frac` under `by_attribute`, which reads a partition rather than drawing one; `from` under `random`, which draws one rather than reading one; or a non-empty `stratify_by` under `by_attribute`, which names how a draw is balanced when no draw happened. One finding per offending field, so a block declaring more than one earns more than one. The same fault [`E-DATA-ASSIGN-NO-DRAW`](#errors-validate-reports) names one declaration over, including its `!= []` exemption — this row does not refuse an empty `stratify_by: []` itself. Unlike the `assign` sibling, `init` never materializes a `holdout` block at all, let alone `stratify_by: []`, and `[]` is not silently accepted: it is refused two checks later, as `E-DATA-HOLDOUT-STRATIFY-UNKNOWN`'s own row states | `E-DATA-HOLDOUT-NO-DRAW` |
| `data.units.holdout.seed` is present and is neither `auto` nor a plain integer — a quoted `"1234"`, a `1.5`, or a `true` is a pin nothing can honour, and honouring it as far as the derivation would record a derived seed under a key the config wrote deliberately | `E-DATA-HOLDOUT-SEED` |
| `data.units.holdout.stratify_by` names a value `data.units.attributes` does not declare, names the column `data.units.measurements.by` names — consumed when a unit's rows collapse, so no resolved unit carries it — or is not the name of an attribute at all: a non-string, an empty string, or an empty list. Checked from the declaration alone, so it reports whether or not a roster resolved | `E-DATA-HOLDOUT-STRATIFY-UNKNOWN` |
| `data.units.holdout` and a `{kind: fold}` repeat level are both declared. Two answers to one question — how the data is divided for evaluation — leaving "which units is this metric over?" with none | `E-DATA-HOLDOUT-FOLD` |
| Under `method: by_attribute`, `data.units.holdout.from` names a column whose value is not the same across one unit's [measurement rows](#what-isnt-a-repeat), the fourth member of the family [`E-DATA-ASSIGN-VARIES`](#errors-validate-reports) names above, refused and reported the same way, through the same collapse: a mis-collapsed holdout decides which side of a split a unit lands on, the same severity a mis-collapsed cluster carries. Not a check `validate` can make for itself — `resolve_units` collapses the rows internally, so by the time there is a roster to read the disagreement is gone — and reached the same way `E-DATA-CLUSTER-VARIES` and `E-DATA-WEIGHT-VARIES` are: at run time, by `resolve_units`, and reported by `validate` under the same code through the resolution it already performs | `E-DATA-HOLDOUT-VARIES` |
| Under `method: by_attribute`, the column `data.units.holdout.from` names does not resolve to exactly `train` and `test`: a unit carries some other value, carries none, or one of the two literals names no unit at all. Read through `units.arms_of`, the single authority for a column-read partition, so the same set equality an arm assignment requires is the one a holdout requires | `E-DATA-HOLDOUT-VALUES` |
| `data.units.holdout.stratify_by` names an attribute that varies within a `data.units.cluster_by` cluster, checked through `units.stratum_varies_within_cluster` — the single authority *Fold strata survive clustering* and *Resample strata survive clustering* also read. Whole clusters go to one side of a holdout, so a cluster carrying two stratum values can be dealt to neither | `E-DATA-HOLDOUT-STRATIFY-VARIES` |
| Under `method: random`, unstratified and unclustered, `frac` apportions the test side zero units over the resolved roster — every metric would be over nothing. Reported for the unstratified, unclustered draw only, mirroring *Every arm draws units*: a stratified or clustered split is checked where the run performs it, because a cluster is the smallest thing that can move and only the draw knows what it moved | `E-DATA-HOLDOUT-EMPTY` |
| `data.units.holdout` is declared beside `data.units.allocation: between` or a non-empty `sweep.groups`. One roster-wide split across a cell structure gives the cells unequal test sizes and, at worst, a cell with no test units — refused rather than recorded, because the imbalance is only visible to a reader who crosses `allocation.json`'s membership against the arms list by hand | `E-DATA-HOLDOUT-CELLS` |
| A `{kind: fold}` repeat level is declared beside `data.units.allocation: between` or a non-empty `sweep.groups`, refused for the identical reason and at the identical check site as `E-DATA-HOLDOUT-CELLS`. `k` is bounded by the whole roster's [fold basis](#validation), so a roster-wide partition can leave a small arm with folds holding none of its units | `E-REPL-FOLD-CELLS` |
| [`data.units.cluster_by`](#clustered-units) is a non-empty string and the design resolves to at least one comparison — a generated `vs_baseline` for every non-baseline condition, plus every declared [`statistics.contrasts`](#contrasts-claims-that-arent-condition-vs-baseline) entry, the same family `W-STATS-FAMILY` counts and the same test `E-DATA-WEIGHT-CONTRAST` below applies. [§ Statistical reporting](#statistical-reporting) gives each contrast construction a `_clustered` suffix under a declared cluster — the *t* forms cluster-robust over the differenced values when paired and the arm-level ones when not, the percentile forms resampling whole clusters, jointly across both sides when paired — and **none of those five exists in this build**: `paired_t_over_units` takes a list of per-unit differences and nothing else, the derived forms take rows and a seed and know nothing about membership, and there is no unpaired form at all. So the delta and its interval would be computed as though the units were independent, which is the one thing the declaration says they are not, beside per-condition values that *are* cluster-robust and with nothing in the record saying which is which — the interval [§ Clustered units](#clustered-units) calls too narrow, on the number a reader acts on. The *resolved* family is the test rather than the declaration, exactly as below: a `sweep.baseline` with no axis beside it expands to a single baseline row, never a comparison's subject, so a clustered run of it publishes no delta and is accepted, and a declared contrast over a sweep with no baseline is refused though it declares no baseline at all. [`statistics.report_by`](#reporting-strata) is outside it, a stratum repeating the per-condition aggregation — whose interval is clustered — and publishing no delta. Temporary: the refusal lifts with the slice that builds the `_clustered` contrast family | `E-DATA-CLUSTER-CONTRAST` |
| [`data.units.cluster_by`](#clustered-units) is present and is an empty string — an empty declaration changes no behavior — or names a value `data.units.attributes` does not declare, which includes every name under a `{glob: ...}` source, that source declaring none. `data.units.attributes`, not the source's columns, and for the same reason `E-DATA-WEIGHT-UNKNOWN` below reads that set: a cluster is read per unit when the partition is drawn and again when an interval is computed, so it has to survive resolution as an attribute, where a `measurements.by` is consumed at collapse time and dropped from the merged unit. Checked from the declaration alone, so it reports whether or not a roster resolved; a non-string is left to `E-CONFIG-TYPE`. Raised at run time too, under the same code, wherever cluster membership is resolved for a unit that carries no value for it — `units.clusters_of` is the single authority both surfaces read, so a roster core cannot group raises here rather than inventing a cluster for it | `E-DATA-CLUSTER-UNKNOWN` |
| [`data.units.cluster_by`](#clustered-units) names a column whose value is not the same across one unit's [measurement rows](#what-isnt-a-repeat) — the rows `data.units.measurements` collapses into that unit. Reported for the first such unit, naming the values it declares. Not a check `validate` can make for itself: `resolve_units` collapses the rows internally, so by the time there is a roster to read the disagreement is gone and the cluster is whichever value `first` or `mode` returned. So it is raised where the rows collapse — at run time under the same code, this being one fault with one identifier on both surfaces — and reaches `validate` through the resolution it already performs, the same route `E-UNITS-COLLAPSE-RULE` below takes. A column only some of a unit's rows carry is not a disagreement: the rows that carry it agree, and whether every unit has a value at all is `E-DATA-CLUSTER-UNKNOWN` above | `E-DATA-CLUSTER-VARIES` |
| `data.input_dir` or `data.output_dir` resolves inside the git repository, checked once a repo root is found | `E-DATA-IN-REPO` |
| A `data.units.measurements.collapse` rule of `mean`, `median`, or `sum` — the top-level string, or a per-column map's own entry, or its `first` fallback over a column the map does not name — is checked against the resolved roster's own attribute values for that column, and `units.is_measurement_numeric` — the single authority this check and the run-time coercion both read — says at least one is neither numeric nor a string that parses as one (a `bool` counts as neither); skipped, along with the rest of this row's checks, when the roster does not resolve, since there is then no column to check a rule against. Raised at run time too, under the same code, wherever that coercion runs: over an input table's rows as the roster resolves, and over the rows a step [measured](#what-isnt-a-repeat) as its execution finalizes — the same reuse `E-UNITS-COLLAPSE-RULE` below illustrates. The step-path half is not a fault `validate` can predict: the value is one the *step* recorded, not one any declaration named | `E-DATA-MEASUREMENTS-COLLAPSE-TYPE` |
| `data.units.measurements` is declared (non-null) and is not a mapping, or is an empty mapping — reported alone, since there is then no `by` or `collapse` to check either; or the mapping is neither of those and its `by` is missing or is not a non-empty string, or its `collapse` is missing — an omitted `collapse` names no rule, so it is this row rather than `E-UNITS-COLLAPSE-RULE` below. Also raised where the roster resolves, under the same code, since resolution reads `by` before this check runs and a malformed block reaches it first | `E-DATA-MEASUREMENTS-INVALID` |
| `data.input_dir` or `data.output_dir`, after `expanduser()`, is not an absolute path | `E-DATA-NOT-ABSOLUTE` |
| `data.input_manifest_policy` is empty, or is a value outside the declared policies | `E-DATA-POLICY` |
| `data.input_dir` or `data.output_dir` is empty | `E-DATA-REQUIRED` |
| `data.input_dir` is not a directory, or is a directory with nothing in it | `E-DATA-UNREADABLE` |
| [`data.units.weight_by`](#weighted-samples) is a non-empty string and the design resolves to at least one comparison — a generated `vs_baseline` for every non-baseline condition, plus every declared [`statistics.contrasts`](#contrasts-claims-that-arent-condition-vs-baseline) entry, the same family `W-STATS-FAMILY` counts. Core weights each condition's own value and interval, and no contrast construction in this build weights at all, so the delta would answer a different question than the two values beside it. The *resolved* family is the test rather than the declaration: a `sweep.baseline` with no axis beside it expands to a single baseline row, which is never a comparison's subject, so a weighted run of it publishes no delta and is accepted, and a declared contrast over a sweep with no baseline is refused though it declares no baseline at all. [`statistics.report_by`](#reporting-strata) is outside it, a stratum publishing no delta and joining no family. Temporary: the refusal lifts with the slice that makes the three paired estimators — `paired_t_over_units`, `paired_delta_of_derived` and `paired_percentile_of_derived` — take weights | `E-DATA-WEIGHT-CONTRAST` |
| `data.units.weight_by` names a declared attribute, the roster resolves, and at least one unit's value for it is not a positive finite number — zero, negative, non-numeric, or a NaN. "Numeric" is `units.is_measurement_numeric`, the same single authority the collapse-type check reads, so a table-sourced `"2.0"` counts as the number it holds; finiteness is checked on top of positivity because `float("nan")` parses and compares `False` against every bound. Skipped when the roster does not resolve, there being no values to check, and reported for the whole roster at once naming the first offending unit. Raised at run time too, under the same code, wherever a weight is actually used — the same reuse `E-DATA-MEASUREMENTS-COLLAPSE-TYPE` above illustrates, and for the same single-authority reason | `E-DATA-WEIGHT-INVALID` |
| `data.units.weight_by` is present and is an empty string — an empty declaration changes no behavior — or names a value `data.units.attributes` does not declare, which includes every name under a `{glob: ...}` source, that source declaring none. `data.units.attributes`, not the source's columns, and deliberately unlike the `measurements.by` half of `E-UNITS-ATTR-MISSING` below: a weight is read per unit at analysis time, so it has to survive resolution as an attribute, where a `by` is consumed at collapse time and dropped from the merged unit. Checked from the declaration alone, so it reports whether or not a roster resolved; a non-string is left to `E-CONFIG-TYPE` | `E-DATA-WEIGHT-UNKNOWN` |
| [`data.units.weight_by`](#weighted-samples) names a column whose value is not the same across one unit's [measurement rows](#what-isnt-a-repeat), the same shape `E-DATA-CLUSTER-VARIES` above refuses and reported the same way, through the same collapse. A separate code because the two say different things about what breaks: a mis-collapsed weight mis-sizes what one unit stands for, where a mis-collapsed cluster decides which side of a split it lands on. Whether the surviving value is usable as a weight at all is `E-DATA-WEIGHT-INVALID` above, which reads the collapsed roster and so cannot see this | `E-DATA-WEIGHT-VARIES` |
| Once no experiment was preloaded, `entrypoint` is a non-empty string, and a repository root was found for it, importing it raises anything — a `SystemExit` at module scope, `entrypoint` not shaped `<module>:<attribute>`, or any other exception; skipped without a report when no repository root exists at all, since there is then no `src/` to import from | `E-ENTRYPOINT-IMPORT` |
| `entrypoint` is empty, or is not a string | `E-ENTRYPOINT-REQUIRED` |
| A hypothesis's `compare.to` is `baseline` — explicit, or implicit when `compare.condition` is present and neither `to` nor `compare.contrast` is — and `sweep.baseline` is not declared. Presence is the test, so `condition: null` counts and is *not* treated as absent the way an unset `E-CONFIG-TYPE` or `E-CONFIG-SHAPE` leaf is: `hypotheses` is a whole-leaf block whose entries `hypotheses.resolve` reads by key, stringifying whatever `condition` holds into a label lookup, so a present-but-`null` `condition` names a label that resolves to nothing rather than leaving a field unset. With a baseline declared it draws `E-HYPOTHESIS-CONDITION` instead, for that same reason | `E-HYPOTHESIS-BASELINE` |
| Once the entrypoint has imported and the metric's step is one it declares, a hypothesis names a metric whose scope is not `summary`, sets `evaluate_on` to `ci95_lower` or `ci95_upper`, and no metric this run computes could ever carry an interval — `data.units` is undeclared and the template defines no `aggregate` | `E-HYPOTHESIS-BOUND` |
| A hypothesis's `compare` declares `to`, and its value is not `baseline` | `E-HYPOTHESIS-COMPARE-TO` |
| A hypothesis's `compare.condition` names a label the run's `sweep` does not declare, or names the baseline's own label — checked only once a baseline is declared, since `E-HYPOTHESIS-BASELINE` already covers the case where none is, and only once `sweep` expands cleanly enough to resolve condition labels at all | `E-HYPOTHESIS-CONDITION` |
| A hypothesis's `compare.contrast` names an `id` `statistics.contrasts` does not declare | `E-HYPOTHESIS-CONTRAST` |
| A hypothesis's `direction` is missing or is a value other than `greater` or `less` | `E-HYPOTHESIS-DIRECTION` |
| A hypothesis's `evaluate_on` is set and is a value other than `observed`, `ci95_lower`, or `ci95_upper` — unset (`null`) is accepted, since `observed` is the documented default | `E-HYPOTHESIS-EVALUATE-ON` |
| Once the entrypoint has imported, a hypothesis names a `scope: summary` metric and declares `compare`, or names a `condition`- or `repeat`-scoped metric without declaring `compare` | `E-HYPOTHESIS-FORM` |
| A hypothesis's `kind` is missing or is a value other than `confirmatory` or `exploratory` | `E-HYPOTHESIS-KIND` |
| A hypothesis entry is not a mapping, or its `metric` is missing or not a `step.metric` string, or — once the entrypoint has imported — names a step the entrypoint's `steps` list does not declare | `E-HYPOTHESIS-METRIC` |
| A hypothesis's `threshold` is missing or is not a number — a `bool` does not count as one | `E-HYPOTHESIS-THRESHOLD` |
| `metadata.description` or `metadata.authors` — the two fields this check covers — is empty; one finding per field, and `metadata.name` is not among them | `E-META-REQUIRED` |
| `metadata.name` is truthy and differs from the name of the directory its config file sits in — checked regardless of `name`'s type, so a wrongly-typed truthy `name` reports this alongside `E-CONFIG-TYPE` rather than being skipped, unlike `E-NAME-PATTERN`; and checked only once the config path names a directory at all — a bare filename with no parent segment (`validate config.yaml`, run from inside that config's own directory) resolves to an empty directory name and skips the check | `E-NAME-DIR` |
| `metadata.name` is a non-empty string that does not match the template's `naming_pattern` | `E-NAME-PATTERN` |
| A `parameter_spec` parameter with no `default` is not declared under `parameters` | `E-PARAM-MISSING` |
| A key under `parameters`, flattened to its dotted path, is not one `parameter_spec` declares — checked with a `difflib` hint | `E-PARAM-UNKNOWN` |
| A value declared under `parameters`, or a value fixed by `sweep.grid`/`sweep.baseline`, fails its `Param`'s own check | `E-PARAM-VALUE` |
| One entry-point key claimed by two installed distributions in [`publishable.resolvers`, `publishable.probes`, `publishable.writers` or `publishable.readers`](#creating-a-plugin-publishable-plugin-new). Answered from package **metadata** over the **complete** claim set for the group and reported in **name order**, naming every distribution that claimed the key as `<distribution> <version>` — the same decision [§ Errors core raises](#errors-core-raises)' row describes, reported here as a finding rather than raised. A writer or reader claiming a suffix core itself writes or reads is not this row's case: that is decided at registration, before `validate` ever sees the plugin, and is the other arm of the same code | `E-PLUGIN-COLLISION` |
| The resolved template declares an [`apparatus_probe`](#the-apparatus-core-can-only-observe) that no installed distribution registers under the `publishable.probes` entry-point group. Answered from metadata, the same way and for the same reason a resolver name is. Reported at `experiment_type` — the field that decided which template's declaration applies — since the probe name is the template's rather than the config's, and a reader who cannot install the plugin fixes this by choosing a different template. A template declaring no probe is the ordinary case and draws nothing here | `E-PROBE-UNKNOWN` |
| A `fold` level's `k` is `all` with nothing resolved to size it against (no roster, or no readable cluster count under a declared `cluster_by`), or is not a whole number ≥ 2 — including exactly 1, which `E-REPL-N`'s floor of 1 does not catch and which is what `k: all` over a single cluster resolves to | `E-REPL-FOLD-K` |
| A `fold` level's `k` exceeds the number of things a fold cannot divide — the resolved unit count, or the cluster count when `data.units.cluster_by` is declared — which would leave a fold with nothing to test | `E-REPL-FOLD-K-TOO-LARGE` |
| `replication.repeats` declares a `fold` level and `data.units` is not declared, so there is no roster to partition | `E-REPL-FOLD-NO-UNITS` |
| A `fold` level's `stratify_by` names a value `data.units.attributes` does not declare, or is not the name of an attribute at all — a non-string, an empty string, or an empty list. `data.units.attributes`, not the source's columns, for the reason `E-DATA-CLUSTER-UNKNOWN` above reads that set: a stratum is read per unit when the partition is drawn, so it has to survive resolution as an attribute. **A name `data.units.measurements.by` also holds fails that same test and is reported here too**: the measurement axis is consumed where a unit's rows collapse — it distinguished them and has no value once they are one unit — so a stratum naming it is declared as an attribute and carried by no resolved unit, leaving the partition nothing to balance on. Deliberately unlike `data.units.cluster_by` under the same declaration, which reaches `E-DATA-CLUSTER-VARIES` at run time instead: a cluster naming the measurement axis varies within every unit by construction, and the collapse is the one place holding the rows that prove it, where a stratum's fault needs no rows at all and the two declarations settle it between them. Checked from the declaration alone, so it reports whether or not a roster resolved. A non-string is reported *here* rather than left to `E-CONFIG-TYPE`, deliberately unlike `data.units.cluster_by`: `check_envelope` types `replication.repeats` a `list` and nothing inside a level, so a `stratify_by: [label]` — the list form [`holdout`](#a-fixed-holdout-split), [`assign`](#allocation-within-subjects-or-between-subjects) and [`resample`](#weighted-samples) each take — would otherwise be reported by no check at all. **A `fold` level's only**; [§ Validation](#validation)'s *Stratification attribute exists* also covers `holdout.stratify_by`, reported by its own code, `E-DATA-HOLDOUT-STRATIFY-UNKNOWN`. `assign.<axis>.stratify_by` is a different row, *Allocation strata exist*, and its own code, `E-DATA-ASSIGN-STRATIFY-UNKNOWN`, since an axis name is also a legal target there and neither `fold`'s nor `holdout`'s admits one | `E-REPL-FOLD-STRATIFY-UNKNOWN` |
| A `fold` level's `stratify_by` names a declared attribute whose value is not the same across every unit of one cluster, under a declared [`data.units.cluster_by`](#clustered-units) — reported for the first such cluster in roster order, naming the values it carries. A cluster is indivisible, so a stratum it carries two of cannot be balanced across the split, and core refuses the pair rather than silently prioritizing one of the two constraints. Checked against the resolved roster, and skipped when it did not resolve, when no `cluster_by` is declared (nothing is then indivisible), or when the name check above already reported — a unit carrying no value for the stratum counts as a variation from siblings that carry one, having nothing to be balanced on. `units.stratum_varies_within_cluster` reads membership from `units.clusters_of`, the [single authority](#clustered-units), so a unit carrying no cluster value raises `E-DATA-CLUSTER-UNKNOWN` there rather than being grouped alone and made trivially constant | `E-REPL-FOLD-STRATIFY-VARIES` |
| A repeat level's `kind` is one of the rejected legacy names (`bootstrap`, `permutation`, `technical`, `biological`, `holdout`), or is not one of the supported kinds (`seed`, `batch`, `fold`) | `E-REPL-KIND` |
| A `batch` level is declared anywhere but the outermost position in `replication.repeats` | `E-REPL-LEVEL-BATCH-INNER` |
| `replication.repeats` declares more than two levels | `E-REPL-LEVEL-DEPTH` |
| Two levels of `replication.repeats` declare the same `kind` | `E-REPL-LEVEL-DUPLICATE` |
| A level declares the count field belonging to the other kind — `n` on a `fold` level, or `k` on a `seed`/`batch` level — or a `batch` level declares any key besides `kind` and `n`, checked after the count-field clause so `{kind: batch, k: 3}` still reports its count rather than an unrecognized key. Applied to `batch` alone; no other kind's keys are closed | `E-REPL-LEVEL-FIELD` |
| A `seed` or `batch` level's `n`, or a `fold` level's `k`, resolves to an integer less than 1 | `E-REPL-N` |
| `replication.order` is set and is a value other than `as_declared` or `randomized` — unset (`null`) is accepted | `E-REPL-ORDER` |
| Two members of one repeat level derive the same seed, or resolve to the same label, from the digest the check ran against | `E-REPL-SEED-COLLISION` |
| [`data.units.from.resolver`](#where-units-come-from) names a resolver that no installed distribution registers under the `publishable.resolvers` entry-point group. Answered from package **metadata**, so a name that is absent costs no import at all — [§ Creating a plugin](#creating-a-plugin-publishable-plugin-new) makes that the whole argument for entry points, and a check that reached for the object behind the name would have changed the guarantee whatever it returned. The message names every group member it did find, the way an unresolved template names the templates it knows, because the ordinary cause is a spelling and the ordinary remedy is reading the list. **Not yet emitted:** the resolver source is refused wholesale in this build, and this code replaces that refusal when the dispatch lands | `E-RESOLVER-UNKNOWN` |
| [`data.units.measurements.by`](#what-isnt-a-repeat) names a field, and the resolver the roster came from yields no attribute of that name to collapse on. A table source reports the same fault against its columns; a resolver has no columns beyond the attributes it declares, so the field a CSV would simply have carried has to be yielded, and this is where that obligation is checked. Separate from [`E-UNITS-ATTR-MISSING`](#errors-validate-reports), which reports the same field missing from a **table** source's columns: the two name different declarations, and a reader fixing one is not fixing the other. **Not yet emitted:** a resolver-produced roster does not exist in this build | `E-RESOLVER-MEASUREMENT-FIELD` |
| A resolver reads a parameter the [sweep](#expansion-modes) varies. The unit table is one table for the whole run, so conditions that resolved different units could not be paired and `n` would mean something different in each — [§ Where units come from](#where-units-come-from) states the rule. Its own code rather than the [`E-STEP-SWEPT-PARAM`](#errors-core-raises) the read itself raises: that identifier is a step's, reached at run time from `"run"` or `"summary"` scope, and a reader holding it is sent to a section describing a different fault at a different time. Sharing the mechanism — a sentinel substituted for a swept path, raising on the read — is not sharing the fault, the same way a coded `ContractError` from a local template's top level is reported as `E-TEMPLATE-LOAD` rather than under the code it carried. An [apparatus probe](#the-apparatus-core-can-only-observe) carries no such restriction and usually does read a swept parameter. **Not yet emitted:** no resolver is executed in this build | `E-RESOLVER-SWEPT-PARAM` |
| A `statistics.contrasts` entry's `of` or `against` names another entry's `id` rather than a condition's label — contrasts compare conditions and do not nest | `E-STATS-CONTRAST-NESTED` |
| A `statistics.contrasts` entry sets `of` and `against` to the same condition | `E-STATS-CONTRAST-SAME-SIDES` |
| `statistics.contrasts` is not a list, an entry in it is not a mapping, or an entry's `id` is missing, is not a string, or repeats an earlier entry's | `E-STATS-CONTRAST-SHAPE` |
| A `statistics.contrasts` entry's `of` or `against` names a value that matches no declared condition's label and no other entry's `id` | `E-STATS-CONTRAST-UNKNOWN` |
| A `statistics.contrasts` entry's `within` names an attribute `data.units.attributes` does not declare | `E-STATS-CONTRAST-WITHIN` |
| `statistics.correction` is set and is a value other than `none`, `bonferroni`, `holm`, or `fdr_bh` — unset (`null`) is accepted | `E-STATS-CORRECTION-UNKNOWN` |
| A `statistics.report_by` entry is not a string, or names an attribute `data.units.attributes` does not declare | `E-STATS-REPORTBY-UNKNOWN` |
| `statistics.resample.method` names a value other than `bootstrap` — the whole enum, [§ Statistical reporting](#statistical-reporting)'s *Resample methods*. Unset (`null`) is accepted and takes the documented default | `E-STATS-RESAMPLE-METHOD` |
| `statistics.resample.n` is below 80, the fewest draws both percentile ranks are interior at. Refused rather than warned because under it core reports no interval at all, so a declared `n: 50` would null `ci95` on every metric in the run rather than narrowing one | `E-STATS-RESAMPLE-N` |
| `statistics.resample.stratify_by` names a value `data.units.attributes` does not declare, or an entry that is not a name at all (`stratify_by: [3]`). `data.units.attributes`, not the source's columns, for the same reason `E-DATA-CLUSTER-UNKNOWN` reads that set: a stratum is read per unit when the draw is taken, so it has to survive resolution as an attribute. Read through the same normalization the draw balances on, so a bare `stratify_by: site` is one name to both. One finding per offending name. Unlike `assign.<axis>.stratify_by`, a [`sweep.groups`](#expansion-modes) axis name is **not** a legal target here — a resample draws from the roster, not from an allocation. Unlike that field, `stratify_by` here **is** an `envelope.py` `LEAF_TYPES` leaf (`(str, list)`), so a wrong-typed *declaration* (`stratify_by: 5`) is `E-CONFIG-TYPE` and stays silent under this code rather than being reported twice — only a wrong-typed *entry* inside an otherwise-list declaration reaches this row. A bare `stratify_by: ""` is accepted rather than refused, unlike a `fold` level's own `stratify_by` above: `units.stratum_names` treats an empty string the same as an absent one (both falsy), naming no stratum at all rather than one empty name, so there is nothing here to refuse | `E-STATS-RESAMPLE-STRATIFY-UNKNOWN` |
| **A stratum must be constant within a cluster, and a resample's draw is a cluster drawn within its stratum** — the same composition [§ Clustered units](#clustered-units) already requires for `fold`, `holdout` and `assign`. `statistics.resample.stratify_by` names a value that varies within a cluster under a declared `data.units.cluster_by`, checked here through `units.stratum_varies_within_cluster`, the single authority *Fold strata survive clustering* and *Holdout strata survive clustering* also read; a resample draws whole clusters, so a cluster carrying two stratum values can be dealt to neither. **Dual-listed, unlike `E-DATA-WEIGHT-INVALID`'s single shared `usable_weight` authority**: `stats.percentile_over_units_clustered` re-implements this same equality at run time over the stratum vector and membership map it is handed directly, `stats.py` having no way to import `units.py` and call this row's own function over a roster — normalized the identical way that function is (`"no value"` for `None`, `str()` otherwise) so the two independent checks agree on a stratum read back as `1` in one place and `"1"` in the other, rather than answering differently for one declaration — **for a single, uncomposed `stratify_by` name read straight off the roster**, which is what both checks were built against. A `stratify_by` naming more than one attribute is composed into one cross-label by `cli.py` (`resample_strata`, H4a task 15) before it ever reaches `percentile_over_units_clustered`, with a missing name rendered `<absent>` rather than passed through as `None` — so the run-time check's own `None` branch is not what actually distinguishes a missing unit there, and neither implementation is checked against a real attribute value that happens to equal a sentinel string, or two attribute combinations that happen to compose to the identical label | `E-STATS-RESAMPLE-STRATIFY-VARIES` |
| `statistics.resample` is declared and `data.units` is not — there is no unit table to draw from, so the declaration would change no behavior. Read from the declaration, not from whether a roster resolved: a declared-but-unresolvable `data.units` already has its own finding | `E-STATS-RESAMPLE-UNITS` |
| `sweep.ablate` is declared (truthy) and `sweep.baseline` fixes a level of a [`sweep.groups`](#expansion-modes) axis, which § Expansion modes refuses because "an ablation is one change from *its own cell's* full model, and there is no single reference condition when the reference cohort differs". The consequence is stronger than a mis-numbering, which is why this is an error: in the composition § Expansion modes permits — `ablate` over group axes and nothing else — a baseline fixing an axis expands over nothing, so the crossed ablation has one cell and **every other level of that axis is executed by no condition at all** while the run reports success. `ablate` beside a *parameter* axis duplicates the fixed level instead, the way `E-SWEEP-BASELINE-GROUP` describes, and is refused for its own reason by `E-SWEEP-ABLATE-CROSSED` beside this code. The two group-level refusals are exclusive: a config carries this one or that one, never both | `E-SWEEP-ABLATE-BASELINE-GROUP` |
| `sweep.ablate` is declared and `sweep.baseline` is not, so no condition is one change away from anything and the ablated conditions carry only their own change. Both sides are read for a *truthy* value, so `ablate: null` is not a declaration and an empty `baseline: {}` is not one either | `E-SWEEP-ABLATE-BASELINE-MISSING` |
| `sweep.ablate` is declared (truthy) alongside a non-empty `sweep.grid`, `sweep.paired` or `sweep.sample` — the axis-shaped modes, read as one set rather than named here, so a later axis mode joins this refusal by being classified as one (the mode vocabulary is a closed partition of axis and non-axis modes, and a mode outside it is refused by `E-SWEEP-KEY-UNKNOWN` before it can be used at all). `sweep.groups` is a non-axis mode and composes freely, varying units rather than parameters | `E-SWEEP-ABLATE-CROSSED` |
| A `sweep.ablate.remove` entry names a path `remove` cannot act on, in either of two ways: the parameter is neither a boolean nor `nullable`, so neither `false` nor `null` is a value it may hold (reported whatever the baseline says); or — for a boolean, and only when a `sweep.baseline` is declared at all — the baseline fixes no *boolean* value for that path, so `remove` finds nothing to turn off and sets `null` rather than `false`, planting it at a parameter that is not nullable. Reported only for a path the template declares, since an unknown one is `E-SWEEP-PATH-UNKNOWN`; the baseline reading is `remove`'s alone, an `override` stating its own value | `E-SWEEP-ABLATE-TARGET` |
| A `sweep.grid` axis declares an empty (falsy) list of values, so the sweep would expand to zero conditions | `E-SWEEP-AXIS-EMPTY` |
| `sweep.baseline` fixes a level of a [`sweep.groups`](#expansion-modes) axis and `sweep.ablate` is not declared — § Expansion modes' *the arms of a group axis are peers*. `_baseline_cells` reads a fixed axis as fixed, so it expands over nothing while `_axes` still emits that level as a product row: the level is rendered **twice**, once as the baseline row and once as its own axis's, and the two conditions hold the same units and the same parameters, with directories identical at every artifact — [*two identical measurements reported as two arms*](experimental-designs.md#mistakes-core-prevents). Where the axis declares two or more levels, the other levels' rows cross the single baseline and `E-DATA-ALLOCATION-CONTRAST` reports beside this code — but that refusal is temporary, and at one level there is no cross-arm comparison for it to read at all. The route a control arm actually wants, once there are two of them, is a [`statistics.contrasts`](#contrasts-claims-that-arent-condition-vs-baseline) entry naming both arms — whose delta this build refuses for the same disjoint-units reason, leaving a `summary`-step `Estimate` or two runs joined in a `study`. Where `ablate` is declared the sibling code `E-SWEEP-ABLATE-BASELINE-GROUP` reports instead, never both | `E-SWEEP-BASELINE-GROUP` |
| `sweep` is declared and resolves to zero conditions, whatever shape produced that — a backstop beneath the per-axis checks above | `E-SWEEP-EXPANDS-EMPTY` |
| `sweep` declares a key that is not one of the six recognized sweep modes (`baseline`, `grid`, `paired`, `ablate`, `sample`, `groups`) | `E-SWEEP-KEY-UNKNOWN` |
| A [`sweep.groups`](#expansion-modes) axis declares the same level twice (`levels: [control, treatment, control]`). The route § Mistakes core prevents' *two identical measurements reported as two arms* is not otherwise closed by: `E-DATA-ALLOCATION-NO-ARMS` and `E-DATA-ALLOCATION-WITHIN-ARMS` both read the `within`-versus-arms question and are satisfied here, `E-SWEEP-PATH-DUPLICATE` compares axis *names* across entries rather than values within one entry's `levels`, and `arms_of`'s set equality has nothing to disagree with because `{control} == {control}`. Unrefused, `expand` renders two conditions carrying the same label and the same `values`, each handed the same units, and the two condition directories are identical at every artifact on a green run. A **parameter** axis repeating a value (`grid: {analysis.method: [pearson, pearson]}`) has the same shape and is deliberately not refused — but **not because its consequence is milder**: crossed with a group axis it reproduces this outcome exactly. `groups: [{by: arm, levels: [control, treatment]}] × grid: {analysis.method: [pearson, pearson]}` runs to exit 0 with `00_arm=control__method=pearson` and `01_arm=control__method=pearson` identical at every artifact, and the duplicated label bodies carry the *arm* — so they are [selectors](#contrasts-claims-that-arent-condition-vs-baseline), and a contrast naming one resolves silently to the later of the pair with no ambiguity reported. Only the group axis is checked because a group level is a claim about *which units* and a parameter value is not; the parameter-axis duplicate is a known gap, recorded here rather than closed. The axis's *other* route to two identical arms — a `sweep.baseline` fixing one of its levels, which renders that level as the baseline row and as its own product row — is `E-SWEEP-BASELINE-GROUP`; neither code reaches the other's shape | `E-SWEEP-LEVEL-DUPLICATE` |
| Two axis-shaped modes — any two of `sweep.grid`, `sweep.paired` and `sweep.sample` — write the same dotted path, so `expand`'s product would let whichever mode is later silently overwrite the other's value on every combination; or a [`sweep.groups`](#expansion-modes) axis's `by` names a path one of those three writes, which is the worse version of the same collision — a group cell is a *set of units*, so every condition marks that path a selector and no scope plants the parameter, leaving the parameter axis claiming to sweep a value every condition ran at its base. The same refusal fires when `by` names a path this template declares as a parameter at all, swept or not — an unswept collision has no other axis losing its value, but the condition's own label and directory still claim a value `resolve_condition_cfg` never plants, indistinguishable from a real swept parameter to a reader who has not opened `sweep.yaml`. A group axis's name is a label key rather than a parameter path, so renaming either side resolves it. **Also read one level shallower, entry by entry rather than through the deduping `selector_paths`**: two `sweep.groups` entries naming the same `by` — [§ Validation](#validation)'s *Axis names are distinct* — cross two same-named axes into the product, rendering two conditions under the identical label | `E-SWEEP-PATH-DUPLICATE` |
| A `sweep.grid`, `sweep.paired`, `sweep.baseline`, `sweep.sample.ranges`, `sweep.ablate.override` or `sweep.ablate.remove` key names a dotted path the template's `parameter_spec` does not declare — every mode that names a dotted path at all, whether it fixes a value there, declares bounds to draw one from, or plants a removal, since every one of them reaches a condition's config through a `setdefault` walk that *creates* a misspelled path rather than failing on it | `E-SWEEP-PATH-UNKNOWN` |
| `sweep.baseline` is declared alongside a `sweep.sample` axis, so every non-baseline cell — every combination of a draw with the other axes' levels, not every draw — becomes a `vs_baseline` comparison, while a `sample` draw is [not a comparison](#sweeps-and-repeats) and the correction family skips it, which is specified but not implemented in this build. Both sides are read for a *truthy* value, so an empty `baseline: {}` is not a declaration: it fixes nothing, produces no baseline row, and generates no comparison to correct against. A `sample` sweep with no baseline is unaffected for the same reason, a comparison being generated only against a declared one, and so is a declared [`statistics.contrasts`](#contrasts-claims-that-arent-condition-vs-baseline) entry, whose members are named rather than generated | `E-SWEEP-SAMPLE-BASELINE` |
| `sweep.sample` cannot be drawn from: no `n` or an `n` below 1, no `ranges` or an empty one, a `method` outside `sobol` \| `latin_hypercube` \| `random`, a `seed` that is neither `auto` nor a pinned integer, a range that is not exactly one of `uniform` \| `int_uniform` \| `log_uniform`, or a range whose bounds are not two ordered numbers (positive ones, under `log_uniform`; integral ones, under `int_uniform`). A bound — or a drawn value — that is legal here but violates its own parameter's constraints is `E-PARAM-VALUE` | `E-SWEEP-SAMPLE-INVALID` |
| A `sweep.grid`, `sweep.paired` or `sweep.ablate.override` value, or a [`sweep.groups`](#expansion-modes) axis's level, cannot be rendered into a condition label — every value a config *writes* that `label_for` renders, and a label is also a directory segment, so a value carrying `/` would resolve outside the condition directory. A group level joins them because a group cell renders like any other axis's (`00_arm=control`); it takes this check alone and no `Param` check, naming a set of units rather than a parameter value. A `sweep.baseline` value is exempt, since it is never rendered into one. A `sweep.sample.ranges` bound is exempt for the other reason: a label carries the *drawn* value rather than the bound, and a drawn number always renders within `[A-Za-z0-9._+-]+`, so there is nothing a bound could carry that the label could not | `E-SWEEP-VALUE-UNNAMEABLE` |
| A template name is claimed twice across core's own registry, the [installed distributions'](#creating-a-plugin-publishable-plugin-new) `publishable.templates` entry points, and this project's own [`templates/`](#templates-where-parameters-are-defined): two local registrations of one name — in two files, or twice in one file — a local registration of a name core registers, two installed distributions registering one name, an installed distribution registering a name core registers, or a local registration of a name an installed distribution registers. [§ Creating a plugin](#creating-a-plugin-publishable-plugin-new) states the rule and the reason: install order and import order are the only tie-breaks available, and both are properties of a machine rather than of a design — [§ Errors core raises](#errors-core-raises)' row states the full three-source merge this check reads. **Read from the whole of `templates/`, not from the name the config asks for**, discovery being eager for exactly this reason — so a config naming a third template is refused just as a config naming a colliding one is, the repo having no unambiguous set of templates to resolve anything against. A file in the same directory that fails to load **preempts** this code — `E-TEMPLATE-LOAD` in this table is checked first, and says why — so a repo with both faults sees this one only once the directory loads clean. The message names **every** provider that claimed the name, each as `<path>::<ClassName>` for a local one, `<distribution> <version>` for an installed one, and core's own claimant as its dotted class path, there being no file in your repo to rename. Two decorators stacked on **one** class are the case that pair cannot tell apart, and the message says so rather than printing it twice: the name is still claimed twice and still refused, and the remedy is to delete a line rather than to rename anything. Not a finding `validate` computes but a [`ContractError` the merge raises](#errors-core-raises), reported here under the code the raise carries, since every other command that resolves a template meets the same refusal at load and prints the same identifier — an ambiguity that resolved differently per command would be worse than either answer | `E-TEMPLATE-COLLISION` |
| A project-local `templates/*.py` fails to load — it raises while importing, imports cleanly but never calls `@register_template`, or registers a class that is not a `BaseTemplate` subclass — reported for the first such file in [`discover_local`](#templates-where-parameters-are-defined)'s sorted walk of the directory. **Every file is still imported before this is raised**, the same eagerness `E-TEMPLATE-COLLISION` reads from: a well-formed template elsewhere in `templates/` still resolves into this fault rather than being silently skipped. It **preempts** a collision rather than accompanying it: the claims are collected and then not used, so a directory holding both faults reports this code and no `E-TEMPLATE-COLLISION` at all. That is the same eagerness argued the other way — a collision verdict computed while a file failed to load would be computed over a partial set of claims, since the file that didn't load might have been a third claimant, so the collision is not reported until the directory loads clean. A file that registers a name and then raises has that registration drained and discarded rather than left for the next file to inherit and misattribute. Not a finding `validate` computes but a [`ContractError` the merge raises](#errors-core-raises), reported here under the code the raise carries, for the same reason `E-TEMPLATE-COLLISION` is: every other command that resolves a template meets the same refusal at load. **Every non-dunder-stemmed file under `templates/` is read as a template**; a helper a template means to import as a sibling, rather than have discovered on its own, must be named with the same `__`-prefix `__init__.py` already uses to be skipped | `E-TEMPLATE-LOAD` |
| `template.validate(doc)` yields a message — run last, after every other check in this table, and ungated by their findings, so a cross-block rule can report on `parameters` another row already refused | `E-TEMPLATE-RULE` |
| `experiment_type` is missing, empty, or names a template that neither core, nor any installed distribution's `publishable.templates` entry points, nor this project's own [`templates/`](#templates-where-parameters-are-defined) registers — the installed set read from package metadata, so a name no distribution declares is refused without importing one. When the config declares a [`plugin`](#the-one-config-file), the message names it: that field is a readable note about where the template was expected to come from, so a reader who has not installed it learns that from the diagnostic rather than from a missing-name list. Two surfaces meet this condition — `validate` reports it as a finding, never raising it, and [`generate experiment`](#creation-commands) raises it as a `ContractError` — and this row governs both, the two built from one shared message; the hint appears only at the first, `generate` being the command that writes the file the field would live in | `E-TEMPLATE-UNKNOWN` |
| `data.units.attributes` names a value the source table has no column for, or names any value at all under a `{glob: ...}` source, which yields a key and a path and nothing else — reported for the first such name, and after `E-UNITS-ATTR-RESERVED` under either source; or — for a table source only — names a non-string item. Reported for `data.units.measurements.by` too, when it names no column of the source *and* rows sharing a key were collapsed anyway: the collapse groups on the key alone, so such a `by` averages rows nothing distinguished as measurements of one unit. The source's columns, not `data.units.attributes` — `design-principles.md` § Core vs. plugin lists `measurements.by` beside `attributes` as a parallel namer of an input field, and the fence in [§ What isn't a repeat](#what-isnt-a-repeat) declares no attributes at all. Only when rows were collapsed — the same `by` over an input holding one row per unit names a measurement a [step](#what-isnt-a-repeat) supplies, which no input column carries | `E-UNITS-ATTR-MISSING` |
| `data.units.attributes` names a field of `Unit` itself (`key`, `paths`, or `attributes`), which cannot also be a declared attribute | `E-UNITS-ATTR-RESERVED` |
| `data.units.measurements.collapse` names a rule that is none of `mean`, `median`, `sum`, `first`, or `mode` — raised where [technical replicates](#what-isnt-a-repeat) are collapsed, which `validate` also resolves and reports under the same code, the same reuse `E-REPL-SEED-COLLISION` above illustrates | `E-UNITS-COLLAPSE-RULE` |
| The table `data.units.from` names has no data rows, or the `glob` it names matches no files under `input_dir` | `E-UNITS-EMPTY` |
| Two resolved units share the same `data.units.key` value | `E-UNITS-KEY-DUPLICATE` |
| `data.units.key` names a column the source table does not have | `E-UNITS-KEY-MISSING` |
| `data.units.from` names a table that is not a file under `input_dir`, or is neither a table name nor a `{glob: ...}` mapping | `E-UNITS-SOURCE-MISSING` |

---

## The two files

**`configs/<name>/config.yaml`** — what you edit. Everything needed to *run*. Freely mutable; [committing it is optional](#the-one-config-file) and doesn't affect reproducibility.

**`<output_dir>/run_<id>/run.yaml`** — written once at the end of a run, never modified. Everything needed to *report*: the config embedded verbatim, the three hashes, full provenance, execution record, and results. This is what you attach to a paper or hand a reviewer.

`reproduce` accepts either — a config to run fresh, or a `run.yaml` to re-run exactly what that run did.

```yaml
# <output_dir>/run_2026-08-06T14-02-11Z_8e21ab3/run.yaml
schema_version: "1.0"
run_id: run_2026-08-06T14-02-11Z_8e21ab3      # <timestamp>_<short code_hash>
status: completed                              # completed | partial | failed — see below
draft: false                                   # true when written by `publishable draft`

config: {...}                                  # the config.yaml, embedded verbatim
parameters_hash: sha256:1a2b...
code_hash: sha256:8e21...

provenance:
  git:
    repo_root: /home/jlee/my-study
    commit: 4f9a2c1e...                        # YOUR code, never publishable's
    branch: main
    remote: git@github.com:your-org/my-study.git
    code_dirty: false                          # `src/**` or `templates/**` uncommitted;
                                               #   `run` refuses if true, `draft` permits it
    config_committed: false                    # recorded, not required
  environment:
    manager: uv
    python_version: "3.11.9"
    os: "Linux-6.8.0-x86_64"
    hostname: "hms-gpu-node-04"
    uv_lock: "environment/uv.lock"             # byte-for-byte copy, in this run directory
    uv_lock_hash: sha256:6b1f...
    hardware: {gpu: "1x A100 80GB", cpu_count: 32}
  apparatus: null                              # no probe declared; see "The apparatus core
                                               # can only observe"
  input_manifest: "manifest/input.json"
  input_manifest_hash: sha256:3d8a...
  input_manifest_changed: []                   # paths that drifted between the manifest's build and
                                               #   its re-verification at run end; empty means none did.
                                               #   Non-empty fails the run — see "What status means and
                                               #   when a run keeps going"
  units: {n: 240, key: patient_id}
  units_hash: sha256:c40e...                   # of the resolved unit list
  allocation: null                             # "allocation.json" and its hash, when an arm
  allocation_hash: null                        #   assignment or a holdout is declared
  upstream:                                    # runs whose artifacts this run consumed
    - run_id: run_2026-08-01T10-02-44Z_71c9de2
      code_hash: sha256:71c9...
      parameters_hash: sha256:aa03...
      used: ["step01_load_cohort/cohort.parquet"]
  publishable_version: "0.1.0"
  plugin_versions: {}

layout:                                        # which artifact-tree levels this run's directories
                                               #   actually have — degenerate levels collapse, so a
                                               #   missing `conditions/` could otherwise mean either
                                               #   an unswept run or a failure; see "How artifacts
                                               #   are organized"
  conditions: true                             # more than the one unlabeled condition `run` builds
  repeats: true                                # more than one repeat was resolved

execution:                                     # mechanical; nested by the scope of each step
  shared:
    step01_load_cohort: {status: completed, started_at: "2026-08-06T14:02:13Z",
                        wall_seconds: 12.4, attempts: 1}
  conditions:
    - index: 1
      label: method=spearman
      steps:
        step02_fit_model: {status: completed, started_at: "2026-08-06T14:02:26Z",
                          wall_seconds: 61.0, attempts: 1}
        step03_analyze:
          seed17: {status: completed, started_at: "2026-08-06T14:03:27Z",
                   wall_seconds: 903.1, attempts: 1,      # >1 only after `resume`
                   nondeterministic: false,
                   n: {resolved: 240, completed: 231, failed: 9}}    # this execution's
          seed42: {status: completed, started_at: "2026-08-06T14:18:30Z",
                   wall_seconds: 897.4, attempts: 1,
                   nondeterministic: false,
                   n: {resolved: 240, completed: 233, failed: 7}}
  summary:
    step04_compare_methods: {status: completed, wall_seconds: 4.2, attempts: 1}

results:                                       # scientific; see "Statistical reporting"
  conditions:
    - index: 1
      label: method=spearman
      values: {analysis.method: spearman}
      per_repeat:                              # exactly what the step returned, per repeat
        step03_analyze:
          seed17: {r: 0.62, p: 0.001}
          seed42: {r: 0.59, p: 0.002}
      aggregated:
        step03_analyze:
          r: {value: 0.607, basis: units, method: percentile_over_units,
              n: {resolved: 240, completed: 228, failed: 12},
              ci95: [0.517, 0.683],
              repeat_spread: {std: 0.014, n: 5, kind: seed}}
      vs_baseline:
        step03_analyze:
          r: {delta: 0.026, basis: units, paired: true,
              method: paired_percentile_over_units,
              ci95: [-0.007, 0.059],
              ci95_corrected: [-0.007, 0.059],      # rank 2 of 2 under holm: α/(m−i+1) = α
              correction: holm, correction_level: 0.05,
              family_size: 2, family: {comparisons: 2, metrics: 1},
              cohens_d: null}                       # r is derived, not a per-unit mean
  summary:
    step04_compare_methods: {best_method: spearman}
  hypotheses:                                  # see "Pre-registration"
    - {id: h1, kind: confirmatory, supported: true}
```

A run with no repeat level still writes `per_repeat`, keyed by the empty string — the one repeat
has no label because there is no repeat axis to render one from — as soon as some repeat-scoped step
recorded a return; the key is `''` there rather than absent. The block is present rather than omitted
so that a reader parsing `per_repeat` does not need two code paths, and the empty key is what says
"this run had one execution per condition" rather than "this run recorded nothing".

`repeat_spread` beside a metric is omitted, not zeroed, when the run declared no repeat axis at all —
the single unlabeled repeat core resolves when no `replication` block is declared carries no dispersion
figure, because a standard deviation over an execution that was never repeated would read as agreement
between repeats that don't exist, the same mistake a zero-width `ci95` over one unit would make. A
*declared* repeat that happens to resolve one contributing member is a different fact and is written
as `{std: 0.0, n: 1, kind: <the level's kind>}` — a declared `{kind: seed, n: 1}` writes
`{std: 0.0, n: 1, kind: seed}`: `n` is what tells the two apart, since it counts members that
actually contributed a mean rather than the level's declared count. That `0.0` is definitional
rather than measured. The figure is a *population* standard deviation — divided by the number of
contributing members, not by one less — so a single member falls out as exactly `0.0` with no
special case, and the field states what was computed rather than an estimate of anything wider.
**Whether a record should carry that figure at all is open.** The argument above for omitting an
unrepeated execution's dispersion applies to a declared level that resolved one member just as
well: nothing was repeated in either case, and the only difference is that one config mentioned a
repeat axis. Omitting the entry and writing `std: null` are both defensible successors, and
choosing between them is a decision about what a record should carry rather than a reconciliation
between two rules that disagree — so the asymmetry is named here rather than defended, and this
paragraph changes with it.

### What `status` means, and when a run keeps going

An execution that raises is recorded `failed` and the run **continues to the next one.** Stopping at the first failure would throw away every execution the plan had left — on a 720-execution leave-one-out sweep, a single bad fold would cost the run — and there is nothing to salvage it with, since [`resume`](#resuming) skips completed triples but cannot un-abort a plan that was never attempted. So the plan is executed to the end, and the run's own status says what came of it:

| `status` | Means | Exit |
|---|---|---|
| `completed` | Every execution in the plan completed | `0` |
| `partial` | The plan reached its end with some executions failed, or it stopped early with executions already recorded — either way, a record worth reading | `3` |
| `failed` | There is nothing to report | `4` |

**`failed` means there is nothing to report**, which is why it isn't simply "the plan didn't finish." Three things produce it. A `scope: "run"` step that raises takes every condition with it — there is no shared cohort for them to condition on, so continuing would mean executing a plan whose first premise is missing. `limits.max_failed_fraction` being exceeded stops the run where it stands: unit failures only accumulate, so once the fraction is past the threshold no later execution can bring it back, and spending the remaining compute to confirm that is waste. And the [input manifest failing its re-verification](#steps-and-artifacts) after the last execution fails a run that otherwise reached the end of its plan — the inputs moved underneath it, so every number in it is over a dataset that no longer exists, and there is no honest way to report that as `partial`.

**A run that stops early can still be `partial`**, and one thing produces that: core losing the ability to certify the [apparatus](#the-apparatus-core-can-only-observe). A probe that stops responding altogether — the service down, a credential expired mid-run, which is a different thing from [a fact it returns unanswered](#the-apparatus-core-can-only-observe) — leaves the gate with nothing to compare before the next execution, so the run stops there rather than executing uncertified. Everything up to that point ran under recorded facts, so there is a record worth reading and `failed`'s "nothing to report" doesn't fit it. The exit code is nevertheless [`5`](#exit-codes-and-diagnostics) rather than `3`, per the precedence stated there.

A `scope: "summary"` step that raises is *not* one of these — every condition ran, and its own execution is one failure among the others, so the run is `partial` and the conditions are readable without it.

**`partial` is a reportable status, and that's the point of separating it from `failed`.** A run whose executions all ran and three of which failed has results worth reading, with the attrition recorded per execution and per condition; `report` renders it with the failures shown rather than refusing. What it is not is `completed`, so a `study add` of one is visible as what it is.

**All three are terminal, which is what [`resume`](#resuming) distinguishes itself against.** `run.yaml` is written when the plan ends, once, and never modified — so a run directory holding one is a run that finished, and `resume` refuses it rather than re-executing the triples it recorded as failed. What `resume` is for is the case with *no* terminal status at all: a scheduler, a node eviction, a `^C`. That's also why it takes a run directory rather than a `run.yaml` — at the moment it's needed, there isn't one. To retry failed executions after a `partial`, run again: a fresh `run_<id>/` is the mechanism, and patching a record a collaborator may already hold is not.

Results go here rather than back into the config for four compounding reasons: writing into a git-tracked file dirties the tree; writing into a file whose hash was taken at run start makes that hash unanswerable; overwriting previous results contradicts append-only; and one `results` block can't hold many runs. Immutable-after-write `run.yaml` fixes all four, and embedding the config keeps "one self-sufficient file to report" intact.

---

## Run identity

```
/secure/results/cohort-pilot/
├── run_2026-08-06T14-02-11Z_8e21ab3/     # <timestamp>_<short code_hash>
│   ├── run.yaml
│   ├── manifest/input.json
│   ├── environment/{uv.lock,pyproject.toml}
│   ├── sweep.yaml
│   ├── executions.jsonl
│   ├── conditions/01_method=spearman/seed17/step03_analyze/...
│   └── summary/step04_compare_methods/...
├── run_2026-08-07T09-14-03Z_8e21ab3/     # a second run — collides with nothing
└── latest -> run_2026-08-07T09-14-03Z_8e21ab3
```

Everything beside `run.yaml` there has a shape something reads back; see [The other files a run writes](#the-other-files-a-run-writes).

This is what makes append-only livable. Without a run layer, a second run against the same config would target paths the first already filled, and append-only would turn every rerun into a hard failure — so "rerun with different parameters" would require hand-editing `output_dir`, defeating the purpose. With it, reruns are the normal case and nothing is ever at risk.

Including the short `code_hash` in the run ID means a directory listing already tells you which runs shared code — shared the hashed *trees*, precisely, so two prefixes can differ over a neighbouring experiment's package. See [How the three are computed](#how-the-three-are-computed).

**A collision is resolved by suffix, not by precision.** Two runs of one config started in the same second — a shell loop, a scheduler firing twice, a test suite — would otherwise derive the same ID, and append-only would turn the second into a hard failure at the moment it least deserved one. So core takes the first free name, appending `_b`, `_c`, … when the derived one is taken, and records the ID it actually used. Timestamps to the millisecond would look like a fix and wouldn't be one: the guarantee has to hold against a filesystem, not against a clock.

`latest` is a **pointer, not an artifact**, which is why repointing it on every run doesn't contradict [append-only](design-principles.md#design-goals): nothing a run produced is touched, and the runs it has pointed at are all still there under their own names. Commands always resolve it and record the real ID, so it never reaches a record — a `run.yaml` that said `latest` would mean something different tomorrow. Where a platform doesn't give symlinks cheaply, it's a `latest.txt` holding the run ID, and every command reads either.

### One execution at a time, and what holds the run directory

**Core runs one execution at a time, in the order [`sweep.yaml`](#the-other-files-a-run-writes) records.** That isn't a limitation waiting to be lifted; it's what the rest of the design already assumes. [`order: randomized`](#sweeps-and-repeats) exists to decorrelate execution position from condition, and position means nothing without a sequence. A [`batch`](#a-batch-says-when-not-what) level *is* a position in time. The [apparatus gate](#the-apparatus-core-can-only-observe) probes before every execution and fails the run on a change, which needs a defined "before." And [`max_failed_fraction`](#what-isnt-a-repeat) stops the run the moment it's exceeded, which is only meaningful if there's a moment. Interleaving executions would cost all four to buy a speedup on the axis where it helps least.

**The parallelism worth having is inside a step, and it's yours.** A repeat-scoped step making 440 metered requests is where the wall-clock actually goes, and core neither helps nor hinders: issue them concurrently, and [`io.record`](#units-the-thing-being-measured) and [`io.append`](#steps-and-artifacts) are append-only and safe to call as each returns. What core declines to do is run *your pipeline* twice at once, which is the thing that would make the provenance ambiguous. Scheduling a fleet of runs is a scheduler's job, and [this isn't one](../README.md#is-this-for-you).

**A run holds its directory while it executes.** `run_<id>/lock` records the host, pid, and start time, and is removed when [`run.yaml` is written](#what-status-means-and-when-a-run-keeps-going). `run`, `draft`, and `resume` each take it and each release it — a resumed attempt holds the directory exactly as the first one did, which is what "the invocation that takes it releases it" means when two invocations share a run. `dry-run` takes none: it resolves the run directory to print paths and creates nothing, so running one against a live run is as ordinary as reading the ledger. The lock is what makes `resume` safe: resuming a directory another process is executing would put two writers on one append-only tree, so `resume` refuses a directory whose lock is held. A lock left behind by a killed process is reported rather than assumed dead — core can't tell a crashed run from a live one on another node, and guessing wrong is the one guess that corrupts a run instead of merely delaying it.

Like `latest`, the lock is bookkeeping rather than an artifact, so creating and removing it within one invocation isn't the deletion append-only forbids. A finished run directory holds no trace of it, which is right: what's worth keeping about when a run held its directory is each execution's `started_at`, and that's in the record.

[`freeze`](#cli-reference) is the deliberate exception, and the only one. It executes nothing and writes nothing but one line to the append-only [probe ledger](#the-other-files-a-run-writes), so it is safe against a live lock — which is the entire point of having it, since "between blocks of a multi-day run" is exactly when a run is holding its own directory. Concurrent runs of one config need no rule at all: each gets its own `run_<id>/` — [by suffix if their timestamps collide](#run-identity) — and its own lock, and they share only the `latest` pointer, which the later terminal write wins.

---

## The other files a run writes

`run.yaml` is the deliverable, and the rest of the run directory is read back by something — by `resume`, by `reproduce`, by a statistic, or by you. Each file below is therefore a contract rather than a log. All of them are append-only, which is not the same as written-once: `sweep.yaml` and `allocation.json` are settled before the first execution and never touched again, while the ledger and the per-unit tables grow as the run goes. Neither kind is ever rewritten.

### `sweep.yaml` — the resolved plan

Written before the first execution, from the config and the [design digest](#what-auto-derives-from). It is the answer to "what was this run going to do," and [`resume` reads it back rather than re-deriving it](#resuming):

```yaml
design_digest: sha256:9c04...            # a derivation input, not an identity claim
conditions:
  - {index: 0, label: baseline, is_baseline: true, values: {analysis.method: pearson}}
  - {index: 1, label: method=spearman,  values: {analysis.method: spearman}}
  - {index: 2, label: method=kendall,   values: {analysis.method: kendall}}
repeats:
  - kind: seed
    seeds: [17, 42, 137, 1009, 2027]     # resolved, whether `auto` or listed
labels: [seed17, seed42, seed137, seed1009, seed2027]   # composed, outer to inner —
                                                        #   fold03_seed42 under fold × seed
order: as_declared                       # as_declared | randomized
execution_order:                         # realized, always recorded — the fact, not the rule
  - {condition: 0, repeat: seed17}
  - {condition: 0, repeat: seed42}
  # …
```

**`repeats` is one entry per declared level, outer to inner** — the same list `replication.repeats` declares, resolved. Each entry carries its `kind` plus exactly the fields [that kind takes](#repeat-kinds): a `seed` level its resolved `seeds`, a `batch` level its `n` and nothing else, because a batch has no parameter of its own and that is the point. Nesting is therefore read off the list's order rather than recovered by splitting `labels` apart, which would put the run's design at the mercy of a label format:

This is the [`batch` × `seed` design](#a-batch-says-when-not-what) — five separated blocks, three seeds within each — as `sweep.yaml` records it:

```yaml
repeats:                                 # outer to inner, one entry per level
  - {kind: batch, n: 5}                  # `n` alone — a batch varies nothing else
  - kind: seed
    seeds: [17, 42, 137]
labels: [batch01_seed17, batch01_seed42, batch01_seed137,
         batch02_seed17, …]              # 5 × 3 = 15 composed
```

The `seeds` a level records are its own three, not one per execution: fifteen leaves over three resolved seeds is the [documented consequence](#a-batch-says-when-not-what) of `batch01_seed42` and `batch02_seed42` drawing alike, and a flattened list of fifteen would assert fifteen streams that don't exist.

A `fold` level adds `partitions` — the unit keys in each fold's train and test side, and the realized fold sizes when [`cluster_by`](#clustered-units) makes them uneven. A `sample` sweep adds the drawn `values` per condition — they are the conditions' own values, not a second copy — and `sample_seed`, the seed they came from. `order: randomized` adds the `order_seed` its shuffle used, beside the `execution_order` that shuffle produced — the seed so the plan is derivable, the order because [what happened is not a thing to re-derive](#resuming):

```yaml
order: randomized
order_seed: 4417029                      # absent under `as_declared`, which shuffles nothing
```

All of it is there so a reader never re-derives a design, and so `reproduce` regenerates the same one.

### `executions.jsonl` — what has happened so far

One record appended as each execution finishes, and the file [`resume`](#resuming) reads to know what not to redo. It exists because `run.yaml` is written when the plan ends: an interrupted run has no `run.yaml` at all, so the record of what completed has to be durable before there is one.

```json
{"condition": 1, "repeat": "seed17", "step": "step03_analyze", "status": "completed",
 "started_at": "2026-08-06T14:03:27Z", "wall_seconds": 903.1, "attempt": 1,
 "n": {"resolved": 240, "completed": 231, "failed": 9}}
```

`run.yaml`'s `execution` block is this file folded into the scope nesting, which is why the two never disagree: one is the log, the other is the same facts arranged for a reader. A resumed attempt appends its own record for the triple it re-executes rather than amending the earlier one — that's where the `attempts` count in `run.yaml` comes from, and why an execution that ran three times leaves three records and one summary.

### `allocation.json` — who went where

Present only when an [arm assignment](#allocation-within-subjects-or-between-subjects) or a [holdout](#a-fixed-holdout-split) is declared, and covered by `provenance.allocation_hash`. Both are partitions of one roster drawn once, so they share a file. The worked example has neither; this is the enrollment design from § Allocation:

```json
{
  "seed": {"arm": 774512301},
  "arms": {"arm": {"control": ["P0007", "P0011"], "treatment": ["P0002", "P0019"]}},
  "holdout": {"train": ["P0002", "P0007"], "test": ["P0011", "P0019"],
              "seed": 3310985422, "strata": ["label"]},
  "strata": {"arm": ["site", "severity"]}
}
```

Unit keys, never row numbers — a roster that gains a unit renumbers rows and would silently repoint every membership claim. This is the file that answers "which patients were in the treatment arm" from the record alone, which is why it is [read rather than re-drawn](#resuming) on resume and why a copy edited afterwards no longer matches its hash.

**`seed` and `strata` are keyed by axis, and only a drawn axis appears in them.** An axis assigned under [`method: random` or `blocked`](#allocation-within-subjects-or-between-subjects) records the seed its draw was realized with, and — when it declared a non-empty `stratify_by` — the strata it balanced each arm within, in declared order. An axis assigned under `by_attribute` is left out of both rather than recording a value for either: `by_attribute` reads an arm a trial system or the data already assigned, so a `seed` would record a draw that never happened and a `stratify_by` would describe how a draw was balanced when none was — the same fault § Allocation names when it says a `ratio` under `by_attribute` "describes a draw that didn't happen." A drawn axis that declared no `stratify_by` is left out of `strata` for the same reason and not a different one: an unstratified draw balanced on nothing but its ratio, and an empty record is the true one. So a run whose every axis reads a column writes `"seed": {}, "strata": {}` — the keys stay, because the shape is "keyed by axis" whether or not any axis qualifies, and an omitted key would read as "this file has no such block" rather than "no axis drew."

**A holdout carries its own `seed` and `strata`, inside its own block.** The top-level `seed` and `strata` are keyed by *axis name*, and a holdout is not an axis — hanging it off a fabricated key would invite a reader to index it as one. So the `holdout` block is self-contained: `train` and `test` always, `seed` only when the split was **drawn** (`method: random`), and `strata` only when it declared a non-empty `stratify_by`. A `by_attribute` holdout carries neither, for the reason a `by_attribute` axis is left out of both above: it reads a partition the data already holds, so a seed would record a draw that never happened and a `stratify_by` would describe how a draw was balanced when none was. There is no `holdout_hash`; `provenance.allocation_hash` covers this file whole, both partitions being of one roster drawn once.

### `manifest/input.json` — what was read

Written at run start, re-verified after the run, and carried into a [reproduction](#reproducing-on-another-device) as the manifest its own `run` is checked against. [`dry-run`](#before-you-spend-it) *builds* the same manifest without writing it, which is how it can tell you the input is unreadable while still creating nothing. Its shape follows [`input_manifest_policy`](#three-hashes), and it records which policy produced it so a reader isn't left inferring the strength of the claim:

```json
{
  "policy": "hash_all",
  "files": [
    {"path": "index.csv",         "size": 20481, "mtime": "2026-08-01T09:12:44Z",
     "sha256": "b1c2..."},
    {"path": "scans/P0002.nii.gz", "size": 8402113, "mtime": "2026-07-30T22:04:01Z",
     "sha256": "77aa..."}
  ]
}
```

Under `hash_index` the `sha256` key is present for the files `data.units.from` resolves and absent for the rest; under `none` it is absent throughout. Absent rather than null, so "not hashed" can't be misread as "hashed to nothing."

### The per-unit tables

Each recording step's directory holds the table its [`io.record`](#units-the-thing-being-measured) calls built, and one file per thing that can happen to a unit:

| File | Holds | One row per |
|---|---|---|
| `units.parquet` | The collapsed inference base — [`aggregate`](#templates-where-parameters-are-defined) receives this, and `resample`/`null_test` rebuild it | unit that completed |
| `measurements.parquet` | The uncollapsed rows, present only when a step passed `measurement=` | (unit, measurement) |
| `ineligible.jsonl` | `{"unit": "P0044", "reason": "observed span too short to define a velocity"}` | unit [`io.skip`](#what-isnt-a-repeat) declared |

`units.parquet`'s columns are the unit key under the name [`data.units.key`](#units-the-thing-being-measured) gives it, then every declared attribute, then every key any row recorded — the union, with a column absent from a row reading as null. A failed unit has no row anywhere, which is [how core counts one](#what-isnt-a-repeat): `failed` is what's left after `completed` and `ineligible` are subtracted from `resolved`.

### The apparatus files

`apparatus/probes.jsonl` is the append-only ledger every probe writes to — at `dry-run`, at run start, before each execution, and at [`freeze`](#cli-reference):

```json
{"at": "2026-08-06T14:02:11Z", "phase": "run_start", "condition": "00_baseline",
 "probe": "llm_deployment", "facts": {"model_revision": "gpt-5.5-2026-06-11"}}
```

`provenance.apparatus.facts` in `run.yaml` is the first *answered* observation of each fact — what the [gate](#the-apparatus-core-can-only-observe) compares against, per fact rather than per probe, since a probe that answered three of four facts pinned three of them. A fact still unanswered when the run ends stays `null` there, and `provenance.apparatus.unobserved` counts how many probes left it so. The ledger is every observation, nulls included, so a run that failed on a moved apparatus still shows the evaluable earlier period, and a fact that only started answering halfway through is visible as exactly that. [`apparatus.expected.json`](#reproducing-on-another-device), written by `reproduce` into the checkout rather than into a run directory, is that same per-condition mapping with nothing else in it: `{"probe": …, "facts": {"00_baseline": {…}}}`. It is the one file here you are expected to edit.

---

## The importable surface

Everything you write against — a step, a template, a resolver, a probe, a report override — is imported from `publishable` itself. The submodules in [§ Package layout](#package-layout) are where core's code lives, not how you reach it: which file a name sits in is core's business and may move, and the import line at the top of your step should not move with it.

```python
from publishable import BaseStep, Estimate, Unit, register_resolver
```

| Name | Kind | Status | Is |
|---|---|---|---|
| `BaseExperiment` | subclass | built | The ordered `steps` list, and nothing else — see [Generators](#generators) |
| `BaseStep` | subclass | built | One stage: `scope`, `run(cfg, io)`, `nondeterministic`, `derive_seed` — see [Steps and artifacts](#steps-and-artifacts) |
| `BaseTemplate` | subclass | built | An experiment type's `parameter_spec`, `validate`, `aggregate` — see [Templates](#templates-where-parameters-are-defined) |
| `BaseReport` | subclass | not yet built | A renderer override for one experiment — see [A report override](#a-report-override-renders-one-experiments-own-figures) |
| `Param` | construct | built | One parameter's type, default, constraints, and help text — see [Templates](#templates-where-parameters-are-defined) |
| `Unit` | construct | built | What a resolver yields: `key`, `paths`, `attributes` — see [Where units come from](#where-units-come-from) |
| `Apparatus` | construct | not yet built | What a probe returns: `facts` — see [The apparatus core can only observe](#the-apparatus-core-can-only-observe) |
| `Estimate` | construct | built | An interval a `summary` step computed itself — see [`Estimate`](#estimate-carries-your-interval-without-core-claiming-it) |
| `register_template` | decorator | built | One of the five plugin registries — see [Creating a plugin](#creating-a-plugin-publishable-plugin-new) |
| `register_resolver` | decorator | built | The registry a [`data.units.from.resolver`](#where-units-come-from) name resolves through — see [Creating a plugin](#creating-a-plugin-publishable-plugin-new) |
| `register_probe` | decorator | built | The registry an [`apparatus_probe`](#the-apparatus-core-can-only-observe) name resolves through — see [Creating a plugin](#creating-a-plugin-publishable-plugin-new) |
| `register_writer` | decorator | built | The registry an artifact suffix's writer is claimed through — see [Steps and artifacts](#steps-and-artifacts) |
| `register_reader` | decorator | built | Its inverse, which `io.read_upstream` dispatches through — see [Steps and artifacts](#steps-and-artifacts) |
| `PublishableError` · `ContractError` · `ArtifactError` · `ArtifactExistsError` | exception | built | Everything core raises — see below |

**One root, and no second path to any name.** `from publishable.templates import BaseTemplate` is not a supported spelling even where it happens to work, because two import paths for one class is the [defaults-file problem](#there-is-no-separate-defaults-file) in Python: a plugin written against the deeper one breaks when core reorganizes a module it never promised to hold still. `publishable/__init__.py` is the promise; everything under it is an implementation detail, and [§ Package layout](#package-layout) is a map of core's own source rather than a second index of this table.

**A row marked `not yet built` is a promise, not an export.** Importing one raises `ImportError`
today. The rows stay because this table is the enumerated surface every plugin is written against,
and a contract that appears only once its implementation lands is a contract nobody could have
designed to.

**Not everything core adds is a name on this table, and the credential mechanism is the example.** `required_env` is an attribute of a class you already subclass and [`requires_env`](#a-credential-can-belong-to-a-parameter-value) is a keyword of a construct you already import, so declaring either adds no import line to your template. A mechanism reaching you through a class you subclass and a keyword you pass is the shape to expect: this table enumerates what you *import*, and it moves only when there is a new name to import.

**The five plugin registries move this table; the machinery behind them does not.** `@register_resolver` and its siblings are names you import and decorate with, so each has a row. What resolves those names — a scan of installed package metadata, run by core before your code exists — reaches you through no import at all, and the module holding it is [core's own source](#package-layout) rather than a name on this list. `cfg` and `io` are also constructed by core rather than imported, but they are handed to your `run`; the scan is handed to no step at all, since it is core's own internal machinery rather than an argument any step receives.

**`cfg` and `io` are not on it, and that's the shape of the API rather than an omission.** Both are constructed by core and handed to your `run`, already scoped — there is nothing to import and nothing to construct, which is what lets core decide what backs them. Every other name above is one you subclass, instantiate, decorate with, or catch.

**The root config node carries exactly one accessor, `raw`; every nested node carries none.** That
is a real exception to "no methods at all" and it costs one name: a top-level key named `raw` is
unreachable through dot-access. It is at the root only, because the root is the one node core hands
to something other than a step — `validate` and a template's `validate(config)` both need the
underlying mapping — and a nested node has no such caller. A parameter named `raw` inside a block
is reachable exactly as any other is.

### What you define, and what is core's

Core imports your classes before any instance exists — the [execution plan is derived at `validate`](#generators) from the declared scopes — and then constructs a fresh step per execution. Both halves of that constrain what a subclass may do:

| | Must define | Defaulted | Core's |
|---|---|---|---|
| `BaseStep` | `run(self, cfg, io)` | `scope = "repeat"`, `nondeterministic = False` | `__init__`, `self.condition` / `self.repeat` / `self.rng`, `derive_seed` |
| `BaseTemplate` | `parameter_spec` | `validate(self, config)` returns `[]`, `version` is `None` | The registry, materialization, and every check `parameter_spec` drives |
| `BaseExperiment` | `steps` | — | Everything the plan is derived from |
| `BaseReport` | `sections(self, run, io)`, a generator | — | The standard sections `super().sections` yields |

`BaseReport.format` is deliberately absent from the middle column: [`generate report` always writes the line](#a-report-override-renders-one-experiments-own-figures), so a base default would be a value no generated class could ever be observed to take. `BaseTemplate.aggregate` is on neither list: it has no base implementation, and a template either defines it or doesn't. That absence is readable — it's what [`validate`'s "template `generic` defines no `aggregate`"](#validation) is testing — and a base returning `{}` would make the two cases indistinguishable.

**`scope` is read from the class, not from an instance.** `dry-run` prints how many times each step will execute and where its artifacts will land, and it does that without constructing a step at all — so a `scope` assigned in `__init__` or computed per execution would be invisible to the plan that decides how often `run` is even called. It's a class attribute, and a step wanting two scopes is [two steps](#using-them-in-step-code).

**`__init__` is core's, so don't define one.** Core constructs the instance, sets the execution context on it, and calls `run` — passing nothing you could accept, and discarding the instance when the execution ends. There is nothing an `__init__` could receive and nothing it could carry forward, which is why setup belongs at the top of `run` and shared machinery belongs in a base class you import from a [plugin](#plugins-where-domain-knowledge-lives). Keeping module top level free of work matters for the same reason and is a [separate rule](#generators): `validate` imports your package.

A [resolver](#where-units-come-from) and a [probe](#the-apparatus-core-can-only-observe) are plain functions rather than classes — `resolve(io, cfg)` yielding `Unit`s, and `probe(cfg)` returning an `Apparatus` — because neither has state to carry or a lifecycle to hook, and a class would only be a namespace with one method in it.

### Errors core raises

```
PublishableError                   # catch this to catch everything core raises
├── ContractError                  # your code asked for, or handed back, something its declarations don't allow
└── ArtifactError                  # core will not write this
    └── ArtifactExistsError        # …because the target is already there
```

Two levels, and only one leaf, because only one of these is ever a *state* rather than a mistake: after a crash, the target of a write existing is an ordinary fact about a run being resumed, while every other error in the table means the code is wrong and no `except` improves it. Even there, [`io.exists` is the way through](#resuming) rather than a `try` — the type exists so a failure is greppable and testable, not to make catching it the pattern. **Each carries `.code`**, the same stable `E-` identifier a command [prints beside a diagnostic](#exit-codes-and-diagnostics) — for the same reason it exists there, that a message gets clearer over time and something pinned to the wording breaks when it does.

| Raised by | Type · code |
|---|---|
| [`io.write`](#steps-and-artifacts) or `io.path` onto a target that exists | `ArtifactExistsError` · `E-ARTIFACT-EXISTS` |
| A `name` that escapes the step's directory, an `io.append` onto anything but `.jsonl`, or an extension [no writer claims](#steps-and-artifacts) handed an object that isn't `bytes` or `str` | `ArtifactError` · `E-ARTIFACT-NAME`, `E-ARTIFACT-APPEND`, `E-ARTIFACT-UNWRITABLE` |
| [Reading](#steps-and-artifacts) a name whose suffix has a registered writer and no reader. A writer and its reader are [registered as a pair](#creating-a-plugin-publishable-plugin-new), through two entry-point groups, because `io.write` dispatches on the writer table and `io.read_upstream` looks up the reader table — an inversion only while the two hold the same keys. That inversion is checked in one direction only: dispatch is decided from the writer table alone, so a suffix the reader table holds and the writer table does not is invisible to it and reads back as bytes, the same as a suffix neither table knows. A suffix *neither* table knows is not this fault either: that is the raw-bytes case `io.write` already accepts, and it reads back as bytes | `ArtifactError` · `E-ARTIFACT-UNREADABLE` |
| [Reading a step narrower than the caller](#step-scope) | `ContractError` · `E-STEP-READ-DIRECTION` |
| [`io.read_upstream` from `summary` scope naming a condition- or repeat-scoped step, once the sweep labels its conditions, or naming a repeat-scoped step once the run resolves more than one repeat](#step-scope) | `ContractError` · `E-STEP-READ-AMBIGUOUS` |
| [Reading a swept parameter](#step-scope) at `"run"` or `"summary"` scope | `ContractError` · `E-STEP-SWEPT-PARAM` |
| [`io.units` or `io.units.train`](#a-fold-repeat-puts-the-units-out-of-reach-of-the-wider-scopes) where the declarations put no such list | `ContractError` · `E-STEP-UNITS-UNAVAILABLE` |
| `self.condition` or `self.repeat` at a [scope that has none](#using-them-in-step-code) | `ContractError` · `E-STEP-CONTEXT-ABSENT` |
| An [`Estimate`](#estimate-carries-your-interval-without-core-claiming-it) outside `"summary"` scope, or one carrying `ci95` with no `method` | `ContractError` · `E-STEP-ESTIMATE-SCOPE`, `E-STEP-ESTIMATE-METHOD` |
| An [`Estimate`](#estimate-carries-your-interval-without-core-claiming-it) whose `ci95` is not two numbers in ascending order, or whose `value` is not a number | `ContractError` · `E-STEP-ESTIMATE-CI95`, `E-STEP-ESTIMATE-VALUE` |
| A [returned value core can't record](#steps-and-artifacts), or any [name collision the record can't hold](#validation) — a derived key against a recorded column, a recorded column against a unit attribute | `ContractError` · `E-STEP-RETURN-TYPE`, `E-STEP-KEY-COLLISION` |
| A [`cfg` path](#steps-and-artifacts) the config doesn't hold, or a write through a frozen [`Unit`](#the-unit-list-is-three-operations-and-the-units-in-it-are-frozen) | `ContractError` · `E-STEP-PARAM-UNKNOWN`, `E-UNIT-IMMUTABLE` |
| Collapsing [technical replicates](#what-isnt-a-repeat) under a `collapse` rule name that is none of `mean`, `median`, `sum`, `first`, or `mode` | `ContractError` · `E-UNITS-COLLAPSE-RULE` |
| Collapsing [technical replicates](#what-isnt-a-repeat) whose `data.units.measurements` block is not a mapping or names no `by`, or under a numeric `collapse` rule over a value that is neither numeric nor a string that parses as one — the second raised as an input table's rows collapse and as a step's `measurement=` rows collapse at the end of its execution, which is the surface `validate` cannot reach, the value being one the step recorded rather than one a declaration named; both are also [reported by `validate`](#errors-validate-reports) under the same codes | `ContractError` · `E-DATA-MEASUREMENTS-INVALID`, `E-DATA-MEASUREMENTS-COLLAPSE-TYPE` |
| Collapsing [technical replicates](#what-isnt-a-repeat) of a unit whose rows disagree about the column [`data.units.cluster_by`](#clustered-units), [`data.units.weight_by`](#weighted-samples), or an axis's [`assign.<axis>.from`](#allocation-within-subjects-or-between-subjects) names — the one place the pre-collapse values are in hand, which is why none of the three is a check `validate` makes for itself; all three are also [reported by `validate`](#errors-validate-reports) under the same codes, reaching it through the resolution it performs | `ContractError` · `E-DATA-CLUSTER-VARIES`, `E-DATA-WEIGHT-VARIES`, `E-DATA-ASSIGN-VARIES` |
| Under [`data.units.measurements`](#what-isnt-a-repeat), the column `data.units.holdout.from` names is not constant across the rows collapsing into one unit — the unit would be filed on whichever side the row the collapse happened to keep says, making a train/test membership an accident of row order. The fourth member of the family `E-DATA-CLUSTER-VARIES`, `E-DATA-WEIGHT-VARIES` and `E-DATA-ASSIGN-VARIES` already form, and raised where they are raised: at run time, by `resolve_units`, which is the one place holding the pre-collapse rows that prove it; also [reported by `validate`](#errors-validate-reports) under the same code, reaching it through the resolution it performs, same as the other three | `ContractError` · `E-DATA-HOLDOUT-VARIES` |
| Resolving [cluster membership](#clustered-units) for a unit that carries no value for the column `data.units.cluster_by` names — when the partition is drawn, when an interval is computed, and wherever `units.clusters_of` is read, that being the single authority both surfaces share, so a roster core cannot group raises rather than inventing a cluster for it; also [reported by `validate`](#errors-validate-reports) under the same code, which is where a run that validates first meets it | `ContractError` · `E-DATA-CLUSTER-UNKNOWN` |
| A [drawn arm assignment](#allocation-within-subjects-or-between-subjects) whose realized partition leaves a declared level with no units at all — the same fault, and the same code, [`validate` reports](#errors-validate-reports) for a `ratio` that starves an arm over the resolved roster, raised here for the three draws that pass validate-time: a clustered one, whose empty arm depends on the seed, and a stratified one of either kind — on a declared attribute or on an earlier group axis — which `validate` declines to draw for a reason of its own rather than because the answer would differ. `units.assignment_for` is the single authority, so the run meets it where it draws | `ContractError` · `E-DATA-ASSIGN-LEVELS` |
| Under `method: by_attribute`, the column `data.units.holdout.from` names does not resolve to exactly `train` and `test` over the resolved roster — the same set equality [`validate` reports](#errors-validate-reports) for the identical fault, raised here because `units.arms_of` is the single authority for a column-read partition, so a caller reaching `units.holdout_for` without validating first is refused at the draw rather than partitioning on a column that does not hold the split | `ContractError` · `E-DATA-HOLDOUT-VALUES` |
| Under `method: random`, a realized holdout draw leaves the train or the test side empty — the same fault [`validate` reports](#errors-validate-reports) for the unstratified, unclustered case, raised here for what `validate` does not check: a stratified draw, whose per-stratum sizes only the run's own draw produces; a clustered draw, whose empty side depends on the seed the same way a clustered arm assignment's does; and the **train** side of any draw, since `validate` tests the test side alone. `units.holdout_for` is the single authority, so the run meets it where it draws | `ContractError` · `E-DATA-HOLDOUT-EMPTY` |
| Resampling a metric a template's [`aggregate`](#templates-where-parameters-are-defined) derived, under a declared [`data.units.cluster_by`](#clustered-units). `percentile_of_derived` draws units; the clustered draw for a *recomputed* metric is a different construction — each replicate drawing whole clusters and rebuilding a unit table from their pooled units, so its row count varies per draw — and it does not exist, so the interval would be narrower than the design supports beside recorded columns that are cluster-robust. **Not a fault `validate` can report**, and the one row here whose absence from that table is the point: `aggregate` is user code core never inspects, and a template overriding it may still return `{}` for a given config, so "derives a metric" has no validate-time meaning and this is the first place core holds the answer as a fact. Contained the way a derived key collision is — the whole `derived` mapping is dropped, the code disclosed through [`W-STATS-AGGREGATE-FAILED`](#warnings-core-reports), and the run keeps its record and its recorded columns — and dropped rather than published with `ci95: null`, that state already meaning "no resample callable, or no seed". Temporary, alongside `E-DATA-CLUSTER-CONTRAST`, which is the same missing construction one level over | `ContractError` · `E-DATA-CLUSTER-DERIVED` |
| Computing a [weighted](#weighted-samples) figure — Kish's effective size, or a weighted interval — over a `data.units.weight_by` value that is not a positive finite number, the same `units.usable_weight` predicate `validate` approves the column against, so a weight it cannot use raises here rather than answering a plausible-looking number; also [reported by `validate`](#errors-validate-reports) under the same code, which is where a run that validates first meets it | `ContractError` · `E-DATA-WEIGHT-INVALID` |
| **A stratum must be constant within a cluster, and a resample's draw is a cluster drawn within its stratum** — [§ Clustered units](#clustered-units)'s composition, taken again for `resample` rather than invented a second time. `stats.percentile_over_units_clustered` given both `strata` and `membership`, where a cluster's units disagree about the stratum they carry, raised because a public function handed both vectors directly cannot silently pick one. **Dual-listed, but not by one shared authority the way `E-DATA-WEIGHT-INVALID` above is**: `validate` reports the declaration form of this from the roster, through `units.stratum_varies_within_cluster`; `stats.py` cannot import `units.py` to call that same function, so this is a second, independent implementation of its equality over plain sequences — normalized the identical way (`"no value"` for `None`, `str()` otherwise) so the two cannot disagree over a stratum read back as `1` in one place and `"1"` in the other — **again, for a single uncomposed name read straight off the roster**; a composed, multi-name `stratify_by`'s cross-label and `<absent>` sentinel (`cli.py`'s `resample_strata`, H4a task 15) are outside what this equality was built to compare, and a real value colliding with either sentinel string is an acknowledged, unaddressed gap rather than a case this dual listing rules out | `ContractError` · `E-STATS-RESAMPLE-STRATIFY-VARIES` |
| A [column](#templates-where-parameters-are-defined) no row of the unit table holds, read off `units` in a template's `aggregate` — reported as [`W-STATS-AGGREGATE-FAILED`](#warnings-core-reports), since `aggregate` runs after every execution has completed and a metric core can't compute never costs a run its record | `ContractError` · `E-STEP-COLUMN-UNKNOWN` |
| A [repeat level](#repeat-kinds) whose derived seeds or whose rendered labels are not distinct across its repeats | `ContractError` · `E-REPL-SEED-COLLISION` |
| Two [steps](#steps-and-artifacts) in one experiment deriving the same name — including the same step listed twice — or one whose `scope` is not one of the four | `ContractError` · `E-STEP-NAME-COLLISION`, `E-STEP-SCOPE-UNKNOWN` |
| A template name claimed twice as core's own registry, an [installed distribution's](#creating-a-plugin-publishable-plugin-new) `publishable.templates` entry points, and a repo's [`templates/`](#templates-where-parameters-are-defined) are merged — two local registrations of one name, a local registration of a name core itself registers, two installed distributions registering one name, an installed distribution registering a name core itself registers, or a local registration of a name an installed distribution registers. Decided over the complete claim set from all three sources and reported in name order. An installed claimant is named as `<distribution> <version>`, a local one as `<path>::<ClassName>`, and core's own as its dotted class path — each being what a reader changes to resolve it. **An installed claimant is a name, never a class:** the claim is read from package metadata, so no plugin is imported to decide a collision, which is the guarantee [§ Creating a plugin](#creating-a-plugin-publishable-plugin-new) states and the reason a refused installed claim carries no credential to redact. One of the load-time raises — the refusals a command meets before any step exists — beside `E-STEP-NAME-COLLISION`/`E-STEP-SCOPE-UNKNOWN`, `E-TEMPLATE-LOAD`, `E-PLUGIN-COLLISION`, `E-PLUGIN-DECORATOR` and `E-PLUGIN-LOAD`, and dual-surface: every command that resolves a template meets it at load and prints this code, and `validate` [reports it as a finding](#errors-validate-reports) under the same code rather than raising, that table being where its conditions are stated in full. Never raised inside an execution — which template a name means is settled before the first step runs — so it stops the command rather than failing one step | `ContractError` · `E-TEMPLATE-COLLISION` |
| A project-local `templates/*.py` fails to load, in any of three shapes: it raises while importing, it imports cleanly but registers nothing, or it registers a class that is not a `BaseTemplate` subclass — [reported for the first such file](#errors-validate-reports) in `discover_local`'s sorted walk, once every file in the directory has been imported. One of the load-time raises, beside `E-STEP-NAME-COLLISION`/`E-STEP-SCOPE-UNKNOWN`, `E-TEMPLATE-COLLISION`, `E-PLUGIN-COLLISION`, `E-PLUGIN-DECORATOR` and `E-PLUGIN-LOAD`, and dual-surface for the same reason `E-TEMPLATE-COLLISION` is: every command resolving a template meets `discover_local` at load. Checked *ahead* of a collision — a collision computed while a file failed to load would be computed over a partial set of claims. Never raised inside an execution, for the same reason `E-TEMPLATE-COLLISION` is not | `ContractError` · `E-TEMPLATE-LOAD` |
| Two shapes, both against [`publishable.resolvers`, `publishable.probes`, `publishable.writers` or `publishable.readers`](#creating-a-plugin-publishable-plugin-new). **One entry-point key claimed by two installed distributions**: decided over the **complete** claim set for the group and reported in **name order**, not in the order the metadata scan happened to walk one — install order is a property of a machine rather than of a design, so it may not decide which fault is reported either. The message names every distribution that claimed the key, as `<distribution> <version>`, which is what a reader uninstalls. **A writer or reader claiming a suffix core itself writes or reads**: decided at registration, when the `@register_writer`/`@register_reader` decorator runs, over no claim set at all — the message names the suffix and core rather than a distribution, and the remedy is renaming the plugin's own claim rather than uninstalling anything. The template groups' equivalent is `E-TEMPLATE-COLLISION` rather than this code, since a template name has a second home — [the project's own `templates/`](#templates-where-parameters-are-defined) — and one row cannot state both sets of providers | `ContractError` · `E-PLUGIN-COLLISION` |
| A [`@register_*` argument](#creating-a-plugin-publishable-plugin-new) disagreeing with the entry-point key that named it. The entry point is the registration and the decorator is a declaration checked against it, so two spellings of one name with no rule for which is canonical is refused rather than resolved — the [defaults-file argument](#there-is-no-separate-defaults-file) again. The comparison itself exists as a function; the object behind a key is loaded only at `run` and `dry-run`, so that is where this would be reached once something calls it — `validate` answers a name from metadata and never holds the decorated object, so **`validate` cannot see this disagreement** either way, a property of the guarantee rather than a gap in the check. **No task in this slice gives it a caller**, so it is reached nowhere yet | `ContractError` · `E-PLUGIN-DECORATOR` |
| An entry point whose module raises while importing, or calls `sys.exit()` at module scope. `SystemExit` is a `BaseException` and so needs its own `except` — a plugin building an `argparse` parser at import would otherwise end the command with the plugin's own exit code and no diagnostic at all. The same containment `E-PLUGIN-DECORATOR` describes — reached, once something imports a plugin, at `run` and `dry-run` and never at `validate` — and the same build state: **no task in this slice gives it a caller either.** The fault names the entry point and the distribution rather than the module, since a distribution is what a reader uninstalls or pins | `ContractError` · `E-PLUGIN-LOAD` |
| [`io.record` or `io.skip`](#the-unit-table-is-the-inference-base) naming a unit the roster does not hold, or naming one this execution has already recorded or skipped — a unit measured with `measurement=` counts as settled for both, in either order, since it arrives by one path or the other and never both, while a second measurement of it is what the argument is for | `ContractError` · `E-STEP-UNIT-UNKNOWN`, `E-STEP-UNIT-SETTLED` |
| [`io.record`](#the-importable-surface) given `measurement=` while `data.units.measurements` is undeclared, so there is no rule to collapse the rows under | `ContractError` · `E-STEP-MEASUREMENT-UNDECLARED` |
| An [`io` accessor](#step-scope) reached from a scope that does not have it | `ContractError` · `E-STEP-SCOPE-ONLY` |
| Indexing [`io.units`](#the-unit-list-is-three-operations-and-the-units-in-it-are-frozen) with anything but a plain integer — a slice, a string, a bool | `ContractError` · `E-STEP-UNITS-CONTRACT` |
| [`io.read_condition`](#steps-that-need-every-condition) naming a condition index this run did not resolve, or naming a repeat-scoped step with no `repeat=` to say which copy | `ContractError` · `E-STEP-READ-CONDITION-UNKNOWN`, `E-STEP-READ-REPEAT-REQUIRED` |
| Core's execution plan disagreeing with the state core resolved beside it — a repeat execution whose seed or whose resolved config isn't there, a [realized order](#a-batch-says-when-not-what) naming a pair the plan doesn't hold, a declared fold core can't pair with the units it partitions — a repeat label carrying no fold component, a fold with no resolved roster, drawn partitions with no fold level to label them — or a condition on a [group axis](#expansion-modes) core can't pair with its arm, the same disagreement one level over: a condition index missing from the resolved arms | `ContractError` · `E-RUN-SEED-MISSING`, `E-RUN-CFG-MISSING`, `E-RUN-ORDER-MISMATCH`, `E-REPL-ORDER-UNRESOLVED`, `E-RUN-FOLD-UNRESOLVED`, `E-RUN-ARM-UNRESOLVED` |

**The `E-RUN-`/`E-REPL-ORDER-UNRESOLVED` row — core's plan disagreeing with the state core resolved beside it — is the one you can't cause, and it's in the table anyway.** Every other entry is something your declarations or your step code asked for; those six are core checking its own work, because the plan and the resolved conditions, repeats, seeds, folds, arms, and order are all derived from one config and must agree. If they ever don't, the run would execute something other than what it recorded, and no result from it is worth reading. They carry a type and a code for the same reason everything above does rather than being an `assert`: `assert` disappears under `python -O`, which is precisely the wrong property for the only guard on a condition nothing else detects. One of them reaching you is a bug to report, not a config to fix — and, like the load-time rows (`E-STEP-NAME-COLLISION`/`E-STEP-SCOPE-UNKNOWN`, `E-TEMPLATE-COLLISION`, `E-TEMPLATE-LOAD`, `E-PLUGIN-COLLISION`, `E-PLUGIN-DECORATOR`, `E-PLUGIN-LOAD`) and unlike every other row, none of the six is raised inside an execution, so it stops the run instead of failing one step and continuing. A plan core can't trust is not a plan to keep walking.

**An exception exists where your code could act on the distinction; everything a *command* reports is a [diagnostic](#exit-codes-and-diagnostics), not an exception you catch.** `validate` collecting eleven errors over a config is not eleven raises — it's a report, and modelling it as an exception per finding would force it to stop at the first. So the hierarchy above covers the run-time surface, where there is a step to raise into, plus the load-time refusals a command turns straight into a diagnostic of its own — which is why a code can sit in both registries and why each of those rows says which surface a reader is on.

**A `ContractError` inside an execution fails that execution like any other error**, and the run [continues to the next one](#what-status-means-and-when-a-run-keeps-going). It is not a special stop: core has no way to know whether the mistake is in one step or in all fifteen, and a plan abandoned on the first is the outcome [that section already rejects](#what-status-means-and-when-a-run-keeps-going).

---

## Steps and artifacts

An experiment is a list of ordered steps. Each step is a file under `src/<experiment>/steps/`, and its artifacts land in a directory of the same name — at a depth set by the step's [scope](#step-scope). The code layout *is* the output layout:

```
src/cohort_pilot/steps/            scope         artifacts land in
├── step01_load_cohort.py          run           <run_dir>/shared/step01_load_cohort/
├── step02_fit_model.py            condition     <run_dir>/conditions/<nn>_<label>/step02_fit_model/
├── step03_analyze.py              repeat        <run_dir>/conditions/<nn>_<label>/<repeat>/step03_analyze/
└── step04_compare_methods.py      summary       <run_dir>/summary/step04_compare_methods/
```

```python
# src/cohort_pilot/steps/step03_analyze.py
from publishable import BaseStep

class Step(BaseStep):
    scope = "repeat"                            # the default; stated here for clarity
    nondeterministic = False                    # the default; True when this step depends on
                                                #   something core can't make repeat — a hosted
                                                #   API, an instrument, a human rater

    def run(self, cfg, io):
        cohort = io.read_upstream("step01_load_cohort", "cohort.parquet")
        result = analyze(cohort, method=cfg.parameters.analysis.method,
                         min_samples=cfg.parameters.analysis.min_samples)
        io.write("scores.parquet", result.rows)  # rows: this condition's, this repeat's, this step's
        return {"r": result.r, "p": result.p}  # → results.conditions[i].per_repeat.step03_analyze
```

**`nondeterministic` is a declaration, not a warning.** Core [seeds the process and hands the step its own generator](#randomness-and-which-stream-a-step-should-draw-from), which covers local pseudorandomness and nothing else; a step reaching a hosted service or an instrument cannot be made to repeat, and saying so is what lets core record it per execution in `run.yaml`, note it in `report` rather than implying reproducibility it can't deliver, and check that a [`batch`](#a-batch-says-when-not-what) level has something to measure. It travels with the [apparatus record](#the-apparatus-core-can-only-observe): one says the answer may move, the other says what it moved with.

`cfg` is the object `validate` already checked, so a step can assume every parameter is present, correctly typed, and in range — no defensive `cfg.get(...)`. When a sweep is declared, `cfg.parameters` is already resolved for the current condition (see [Sweeps and repeats](#sweeps-and-repeats)), so step code stays sweep-agnostic — except at `"run"` and `"summary"` scope, where no condition is current and a swept path [raises](#step-scope) instead of resolving.

**It is dot-access and nothing else**: a mapping in the config is a node with the same behavior, a list is a list whose mapping elements are those nodes, and a scalar is the scalar. There is no `.get`, no `.keys()`, and no method of any kind on a node — which is what makes it safe for a parameter to be named `items` or `values`, since there is nothing for it to shadow. The single exception is the root node's `raw` accessor, [described above](#the-importable-surface) and costing only the one top-level name core already owns; every nested node has none. A path the config doesn't hold raises [`ContractError`](#errors-core-raises) naming the full dotted path and the nearest key it could have meant, exactly as [`E-PARAM-UNKNOWN`](#validation) does at validate time, because against a closed schema a path that misses is a typo by construction. Names beginning with an underscore never resolve as config keys and raise `AttributeError` instead, so `hasattr`, `copy`, and every other protocol that probes an object by attribute keeps working rather than meeting an exception it doesn't expect. A template's [`validate(self, config)`](#templates-where-parameters-are-defined) receives this same object, which is how a cross-block rule reads `data.units.holdout` without core handing it a second shape.

`io` is scoped to the step's [declared scope](#step-scope) — for the default `repeat` scope that means this condition, this repeat, this step — so nothing a step writes can collide with another execution:

| Method | Behavior |
|---|---|
| `io.write(name, obj)` | Writes into this step's directory. Raises `ArtifactExistsError` if the target exists — no overwrite, no backup-and-replace, no delete-to-make-room. **Atomic**: temp file plus rename, so a crash leaves nothing rather than a half-file that would permanently block a retry. |
| `io.append(name, record)` | Appends one JSON object per line, so the artifact is `.jsonl` and core rejects any other extension. For incremental work that must survive a crash. Idempotent by the record's own `record_key` field when it carries one: a second record under a key already present is discarded, so **first write wins** — the same rule and the same reason as `io.record`. Without a key, a re-executed range appends a second copy of everything it already wrote. |
| `io.path(name)` | Resolves a *write* location without writing, for libraries that insist on writing themselves. Existence-checked in the same direction as `io.write` — it raises `ArtifactExistsError` when the target is already there — so it is not a way to read something back. See `io.exists` below. |
| `io.exists(name)` | Whether this step's directory already holds that artifact. The question a resumed execution asks before writing — see [Resuming](#resuming). |
| `io.resumed` / `io.recorded_keys` | `True` when this execution is a resumed attempt rather than a first one, and the keys this execution has already settled — recorded *or* [skipped](#what-isnt-a-repeat) — from earlier attempts. A **set**, so `key in io.recorded_keys` is constant-time; it covers skips because its one purpose is telling a resumed step what not to redo. Empty rather than absent on a first execution, so a step needs no second check. Together, what a step needs to skip work it already did — see [Resuming](#resuming). |
| `io.read_upstream(step, name)` | Read-only access to an earlier step's artifact *in this run*. Makes cross-step dependencies visible in code instead of implicit in shared paths. |
| `io.read_input(relpath)` | Read-only access to `input_dir`. |
| `io.units` | The units this execution produces results about — every unit, this arm's, or this fold's or holdout's test partition. A sequence supporting [exactly three operations](#the-unit-list-is-three-operations-and-the-units-in-it-are-frozen) — iterate, `len`, index — plus `.train`. `io.units.train` carries the training partition when a `fold` repeat or a [`holdout`](#a-fixed-holdout-split) is declared, and **raises when neither is** — an empty list would let a fit run on nothing and write a plausible model, which is the failure a partition exists to prevent. Both raise at `"run"` and `"condition"` scope when a `fold` repeat is declared, since no fold exists there — see [Step scope](#a-fold-repeat-puts-the-units-out-of-reach-of-the-wider-scopes). There is no `io.units.train.train`. Neither exists at all when [`data.units`](#units-the-thing-being-measured) is undeclared, so both raise there too — the same raise-rather-than-empty posture, for the same reason. See [Units](#units-the-thing-being-measured). |
| `io.skip(unit_key, reason)` | Declares that this unit admits no result in this execution by design — a transform that can't be built, an assay that doesn't apply. Counted as `ineligible` rather than `failed`, with the reason recorded per unit. |
| `io.record(unit_key, values, measurement=None)` | Appends one row to this step's per-unit result table, keyed by unit — or by `(unit, measurement)` when the step measures one unit more than once, which core then collapses per [`data.units.measurements`](#what-isnt-a-repeat). Append-only and resumable by whichever key applies. `values` is a flat mapping of scalars — `str`, `int`, `float`, `bool`, or `None`, under the same coercion every scalar core takes from you gets (below); the table is a table. Rows need not agree on keys, and a column absent from a row reads as `None`, so `units.columns` is the union across the step's rows plus every declared attribute. |
| `io.conditions` / `io.repeats` / `io.read_condition(condition, step, name, repeat=None)` | **`scope="summary"` only.** Iterate resolved conditions and resolved repeat labels, and read any condition's artifacts. `repeat` names which repeat's copy to read and is required when `step` is repeat-scoped; repeat labels are identical under every condition, which is why `io.repeats` is a run-level list. |
| `io.reuse_from(run_id, step, name)` | Explicitly read an artifact from a *previous* run — the sanctioned way to build on prior work without copying or overwriting. See [Lineage](#lineage-between-runs). |

**What `io.write` does with your object is decided by the extension, from a registry core owns.** Core ships writers for the formats it also has to read — `.json`, `.jsonl`, `.yaml`, `.csv`, `.parquet` — and for anything else the object must be `bytes` or `str`, written verbatim. So `io.write("model.pkl", pickle.dumps(model))` and `io.write("figures/roc.png", fig_bytes)` are how those go out: core never pickles for you and never renders a figure, because guessing a serialization for an arbitrary object is how an artifact ends up in a format nobody can read five years later. A plugin registers a writer for an extension its domain needs, the same way it registers a template. Every reader — `io.read_upstream`, `io.read_condition`, `io.reuse_from`, `io.read_input` — decides the same way `io.write` does, from the suffix, then looks up the reader registered for it: a registered extension comes back as the parsed object, with `.csv` and `.jsonl` yielding rows as mappings, and anything else comes back as `bytes`. The writer table and the reader table are two registrations, not one that inverts — core keeps its own five in step, and a plugin registers each half on its own.

**What a writer takes is what its reader gives back**, so a round trip through an artifact is true by construction rather than by convention:

| Extension | `io.write` takes | Its reader yields |
|---|---|---|
| `.json` · `.yaml` | any nesting of mappings, sequences, and scalars | the parsed value |
| `.jsonl` | a sequence of mappings, one per line | rows, as mappings |
| `.csv` · `.parquet` | a sequence of mappings, one per row, every value a scalar | rows, as mappings |
| anything else | `bytes` or `str`, written verbatim | `bytes` |

Rows as mappings rather than a `DataFrame`, on the same argument [`aggregate`'s table](#templates-where-parameters-are-defined) rests on: accepting a library's table type would make that library part of core's public API, and a step is one `df.to_dict("records")` away from the shape core does take. The column set of a `.csv` or `.parquet` is the union of its rows' keys, a key absent from a row writing empty, exactly as the [per-unit table](#units-the-thing-being-measured) already behaves. Handing a writer anything else — a model, an array, an object whose shape core would have to guess — raises `ArtifactError` · `E-ARTIFACT-UNWRITABLE`, which is the same refusal as never pickling for you, one step earlier.

**The extension is the longest registered suffix of the name's last component, compared in lower case.** A compound extension is the ordinary case in several domains — `.fastq.gz`, `.nii.gz`, `.tar.gz` — so splitting at the final dot is not an option: it would hand `reads.fastq.gz` to whatever claimed `.gz` and lose the format in the name. Longest-suffix is also what keeps a plugin's claim safe from a coarser one, since `.fastq.gz` beats `.gz` whichever was registered first. Only the name's last component is examined, and only against suffixes something actually registered — so `programs/gpt-4.1__seed29.json` is a `.json`, the dot inside its stem matching nothing.

**That is a serialization dependency, not an API one, and the distinction is the same one [`aggregate`](#templates-where-parameters-are-defined) rests on.** Core writing `units.parquet` means core depends on a parquet library; it does not mean the table core hands a template is that library's type, and the four-operation contract holds regardless of what sits underneath. A format is a promise about a file a reader opens in ten years; a type is a promise about an object a plugin is written against. Only the first is worth pinning this hard.

**A `name` is a relative path, not only a filename.** `io.write("figures/roc.png", fig_bytes)` and `io.write("programs/gpt-4.1__seed29.json", program)` both write inside the step's own directory, creating intermediate directories as needed, and every reader — `io.path`, `io.append`, `io.read_upstream`, `io.read_condition`, `io.reuse_from` — addresses them by that same relative path. A step that produces a set rather than a single file is ordinary, and making it flatten a tree into `programs_gpt_4_1_seed29.json` would push structure into filenames where a directory says it better. The path is resolved against the step's directory and normalized first: an absolute path, a `..` segment, or a symlink leading outside are all rejected, so "artifacts land in a directory of the same name" stays a property core enforces rather than one a step could opt out of.

There is no `publishable clean` or `publishable reset`. Nothing in core deletes a file it didn't create in the same call — the [run lock](#one-execution-at-a-time-and-what-holds-the-run-directory) being the whole of the exception, and only in the sense that whichever invocation takes it is the one that releases it.

**On `input_dir` being read-only:** `io.read_input` offers no write path, and core never opens `input_dir` for writing. A step calling `open(path, "w")` on an input file is outside what core can prevent — the same boundary as [Greenfield only](design-principles.md#greenfield-only). What core does instead is verify the manifest after the run and fail if inputs changed.

**What a step returns is the same flat mapping of scalars `io.record` takes.** Keys are strings; values are `str`, `int`, `float`, `bool`, or `None`; nothing nests. `run.yaml` is the file a paper attaches and a reviewer opens in ten years, and [`per_repeat` is *exactly what the step returned*](#the-two-files) — so a returned value that plain YAML can't hold honestly is one the record can't hold either. That is the rule against core guessing a serialization for you, stated above for artifacts and arriving here at the other end of the step: a format nobody can read in five years is as bad in `run.yaml` as in an artifact. Nesting is refused for a second reason: a [hypothesis](#pre-registration) addresses a metric as `step03_analyze.r`, and a nested return leaves that path with more than one reading. The rule is identical for the values a template's [`aggregate`](#templates-where-parameters-are-defined) derives, with one exception at one scope — an [`Estimate`](#estimate-carries-your-interval-without-core-claiming-it), whose whole purpose is to carry a structure core will render as an interval.

**A value that is a scalar in every sense but its type is coerced, and only that.** `pearsonr(...).statistic` is a `numpy.float64`, not a `float`, and a rule that rejected it would reject the return statement in most of this document's own examples. So core coerces anything implementing `__float__`, `__index__`, or `__bool__` to the Python scalar it stands for, keeps that, and raises `ContractError` on everything else — a list, a dict, an array, a `DataFrame`, a fitted model. The line is deliberately at *what the value already is* rather than at what could be talked into serializing: a NumPy scalar is a float that arrived through a library, and an array is a decision about what the metric should have been.

**One rule, all three surfaces.** `io.record`'s `values`, a step's return, and a template's [`aggregate`](#templates-where-parameters-are-defined) take the same scalars under the same coercion — the per-unit value a model hands you is a `numpy.float64` at least as often as a derived metric is, and a table core would reject what a return accepted would be a divergence found on the first line anyone writes. What differs between the three is only where the value lands: a column, `per_repeat`, or `aggregated`.

**One metric name is reserved: `by`.** [`statistics.report_by`](#reporting-strata) spends it — a stratified block keys its rows by `by`, so a name of that kind has two candidate meanings for one column. A template's `aggregate` returning a derived metric called `by` collides outright and raises `ContractError` · [`E-STEP-KEY-COLLISION`](#errors-core-raises); a step *recording* a column called `by` is not refused the same way, since the retry that would raise it re-runs against executions that already completed — the column keeps its recorded value, and is reported instead as [`W-STATS-STRATUM-SHADOWED`](#warnings-core-reports), with no contrast delta and no seat in the correction family. The set is stated here rather than left to be discovered by collision, and it is a set of one today; anything added to it is a breaking change to what a template's `aggregate` may return.

**A `run`- or `condition`-scoped step's return value is not recorded.** Core still requires it to be a flat mapping of scalars — the contract is the same at every scope — but there is nowhere for the values to land: a metric is keyed by unit or reported per repeat, and a wide scope has neither. Use [`io.write`](#steps-and-artifacts) for what a wide step produces, and let a narrower step record what it measures. A number with no denominator in the record is the mistake this refusal exists to prevent, and it is the same one [a usage report makes](#the-unit-table-is-the-inference-base).

### Resuming

Because runs are identified and writes are atomic, resume is well-defined:

```bash
uv run publishable resume /secure/results/cohort-pilot/latest
```

It reopens that run directory and skips every (condition, repeat, step) triple marked `completed`, continuing from the first that isn't. The marks are [`executions.jsonl`](#executionsjsonl--what-has-happened-so-far) in the run directory rather than `run.yaml`, and they have to be: [`run.yaml` is written once, when the plan ends](#what-status-means-and-when-a-run-keeps-going), so a run that was interrupted doesn't have one — core appends each execution's record as it finishes, and assembles `run.yaml` from those at the end. On a 3-condition × 30-repeat sweep that died at condition 3, the first two conditions and all their repeats are simply not re-executed. Partial artifacts can't exist to confuse it; work that used `io.append` resumes from the last complete record.

`resume` refuses if `parameters_hash`, `code_hash`, or `uv.lock` don't match current state. Resuming into a *different* experiment is the failure this guards against; with parameters hashed separately, "I edited the config and then resumed" is caught rather than missed.

**A [`draft`](#draft-runs) is therefore rarely resumable, and that follows rather than being a separate rule.** A draft's `code_hash` is taken from the working tree, so any edit between the crash and the resume moves it and `resume` declines. That is the correct answer — the executions already recorded came from code that no longer exists — and the remedy is the ordinary one: run again, into a fresh `run_<id>/`. Iterating on code and resuming a long run are different activities, and `draft` is named for the first.

**It takes the execution order from `sweep.yaml` rather than re-deriving it.** Under [`order: randomized`](#sweeps-and-repeats) a re-derivation would usually agree, since the shuffle is seeded from the design digest — but "usually" is the problem. The realized order is a fact about what happened, and a fact should not be re-computable to a different answer; that's the same reason [`allocation.json`](#allocation-within-subjects-or-between-subjects) is read rather than re-drawn. Reading it also keeps `run.yaml`'s record of the order true after a resume, which a fresh shuffle would quietly falsify.

Under a [`batch`](#a-batch-says-when-not-what) level reading the execution order rather than re-deriving it is load-bearing rather than tidy. Batches are positions in time, so resume finishes the interrupted batch before opening the next one; a resume free to pick its own order could start batch 4 while batch 3 still had executions outstanding, and the separation the design declared would be gone from the middle of the run.

**`allocation.json`'s "read rather than re-drawn" rule has no reader in this build.** `cli.py`'s `OPERATION_COMMANDS = {"validate", "run"}` contains no `resume` command, so nothing calls `build_allocation_document` a second time against an existing `allocation.json`, and no test exercises the path. "Read rather than re-drawn" is the contract a future `resume` must honour, not behavior this build has or tests — `resume` itself is one of the commands a later slice still owes.

**That gap stopped being harmless once arms are drawn.** While `by_attribute` was the only method core executed, a `resume` that re-derived the allocation would have re-read the same column of the same roster and got the same partition back, so the missing reader cost nothing but tidiness. A [drawn axis](#allocation-within-subjects-or-between-subjects) leaves no column: a second draw is a second allocation. `assign.<axis>.seed` makes it likely to agree — the seed is derived from the design digest, the axis name and the roster, all three unchanged by a resume — but "likely" is the wrong property for the record of which patient was in which arm, and a roster that resolved one unit differently would move it. So the rule is now load-bearing where it used to be housekeeping, and the command that must honour it still does not exist.

#### Skipping work *inside* an execution is the step's job

The triple is the granularity core can be sure of. It knows an execution finished because it recorded that it did, and it [never inspects the body of a step](design-principles.md#greenfield-only), so it cannot know which of 440 patients that step got through. Where re-executing is cheap that's the whole story and there is nothing to arrange. Where each item is metered — a hosted API call, an instrument booking, a queue submission — re-running the first 300 is a real cost, so core hands back the facts a step needs and leaves the decision to the step:

```python
class Step(BaseStep):
    scope = "repeat"
    nondeterministic = True

    def run(self, cfg, io):
        if not io.exists("model.pkl"):                       # a *completed* write survives the
            model = fit(io.units.train)                      # crash, and io.write won't
            io.write("model.pkl", pickle.dumps(model))       # overwrite

        done = io.recorded_keys                         # a set; empty unless this is a resume
        for unit in io.units:                           # every unit, always — see below
            if unit.key in done:
                continue
            resp, status = call(unit)
            io.record(unit.key, {"pred": parse(resp), "status": status})
            io.append("responses.jsonl", {"record_key": unit.key, "raw": resp.text})
        return {}
```

`io.exists` earns its place on the first two lines: atomic writes mean a crash *during* a write leaves nothing, but a write that completed before a later crash leaves a whole artifact, and re-executing into it would raise `ArtifactExistsError` and make the step unresumable. Asking first is the only way through, and it's a question only core can answer.

**`io.units` is never narrowed on resume, and that's deliberate.** `resolved` [is defined as `len(io.units)`](#what-isnt-a-repeat) for the execution, and a resumed execution still produced results about every unit it was handed — the earlier attempt's rows are in the same append-only table. Narrowing the list would drop `resolved` to the remainder and make a correctly resumed run look like one that evaluated 140 patients instead of 440. So the skip is the step's `continue` rather than core's filter, and the three-part `n` comes out identical whether an execution ran once or three times. The execution's `attempts` count in `run.yaml` is where the fact that it ran more than once is recorded.

**`attempts` counts how many times that triple was executed, because core never retries on its own.** It is the number of records the triple has in [`executions.jsonl`](#executionsjsonl--what-has-happened-so-far), so a first run leaves every execution at `attempts: 1`, and the count rises only for a triple a later `resume` actually re-executed — one that completed the first time stays at `1` however many resumes the run goes through. Automatic retry is deliberately absent: it would be a behavior nothing in the config describes, it would double-execute a `nondeterministic = True` step whose first attempt may have half-succeeded, and the resolution of the duplicate rows it produced would be [first-write-wins](#resuming) — a tie-break decided by core over an answer that genuinely differs. Retrying a *unit* is a different question and stays where the domain knowledge is: a step's own loop, under parameters its template declares.

**A duplicate row resolves first-write-wins.** That isn't a new rule, it's [append-only](design-principles.md#design-goals) applied: the first row is already durable and nothing overwrites it. For a deterministic step the resolution is immaterial, which is why it rarely comes up — but under `nondeterministic = True` the two rows genuinely differ, so which answer survives is a question about the experiment rather than about bookkeeping. Check `io.recorded_keys` rather than relying on the tie-break. `io.append` resolves the same way for the same reason, and its idempotency needs a `record_key`: without one there is nothing to deduplicate by, and a re-executed range appends a second copy of every record it already wrote.

---

## Units: the thing being measured

Every experiment measures something repeatedly — patients, samples, trials, items, respondents, cells. Core makes that explicit, because otherwise the concept is present but unnamed, and every plugin reinvents it.

It's load-bearing in more places than it first appears. `fold` partitions units; `statistics.resample` and `statistics.null_test` resample and relabel them. `stratify_by` needs unit attributes. The `n` in a confidence interval is a count of something. Per-item checkpointing needs a stable key. Cohort sizes are unit counts. All of that comes from one declaration:

```yaml
data:
  input_dir: /secure/data/cohort-2026
  units:
    from: index.csv                  # index.csv | {glob: "*.dcm"} | {resolver: <name>} — see below
    key: patient_id                  # stable identity — must be unique and reproducible
    attributes: [label, age, sex, site]   # available for allocation, stratification, reporting
    allocation: within               # within | between — see below
    cluster_by: null                 # e.g. site, when units aren't independent
    holdout: null                    # optional single train/test split — see below
```

### Where units come from

`from` answers a different question from the rest of the block. Everything else — `key`, `attributes`, `allocation`, `cluster_by`, `holdout` — says what the design needs of a unit; `from` says how core finds one. Three forms, in descending order of how much the input already looks like a table:

```yaml
from: index.csv                      # a delimited table in input_dir
from: {glob: "*.dcm"}                # one unit per matching path
from: {resolver: plate_wells}        # a plugin walks the input and yields units
```

A table is the ordinary case, and the one everything else in this document uses: `key` and `attributes` name columns, and core reads them. `glob` covers input whose only structure is the filesystem — core builds the table itself, one row per matching path, with the path relative to `input_dir` as the `key`. The pattern is matched against those relative paths, with `**` recursing, so `{glob: "**/*.dcm"}` walks the tree and `{glob: "*.dcm"}` does not. There are no attributes to declare, so a design that needs them wants one of the other two forms.

**The resolved list keeps the order it was resolved in** — table row order, resolver yield order, or lexicographic path order for a `glob`, which is what makes a glob reproducible across filesystems that walk directories differently. That order is not cosmetic: [`assign.method: blocked`](#allocation-within-subjects-or-between-subjects) balances arms *across the roster's order*, so it's the one declaration that reads the order as data. `provenance.units_hash` covers the list in that same order for the same reason — two runs that resolved the same units in a different sequence did not allocate the same trial, and a hash that called them identical would say they had.

**A resolver is for input that is neither.** A DICOM archive whose units are series rather than files, a plate layout where identity is a barcode and a well position, a benchmark shipped as sharded JSONL: finding the units there is domain work, and it is the *only* domain work in the block. So it's a plugin artifact, registered the way a template is:

```python
# src/publishable_my_assay/resolvers/plate.py
from publishable import Unit, register_resolver

@register_resolver("plate_wells")
def resolve(io, cfg):
    for row in io.read_input("layout.csv"):          # rows are mappings
        yield Unit(
            key=f"{row['barcode']}:{row['well']}",
            paths=[f"reads/{row['barcode']}/{row['well']}.fastq.gz"],
            attributes={"plate": row["barcode"], "operator": row["operator"]},
        )
```

```toml
[project.entry-points."publishable.resolvers"]
plate_wells = "publishable_my_assay.resolvers.plate:resolve"
```

**A resolver is its own registered artifact rather than a method on a template.** A template is [the authoritative definition of an experiment type's *parameters*](#templates-where-parameters-are-defined), and unit resolution isn't parameter-shaped: several experiments over one archive share a resolver while declaring different parameters, and one template can be pointed at inputs laid out two different ways. Coupling them would force a copy of one whenever the other varied.

**What it returns is a unit table with the columns a CSV would have supplied.** `Unit` carries three fields — `key`, the identity `data.units.key` names; `paths`, the input files this unit is made of, relative to `input_dir`, empty when the input is already a table; and `attributes`, the mapping `data.units.attributes` draws from. **A declared attribute is also readable directly** — `unit.label`, `unit.span_days` — because a step reading `unit.attributes["span_days"]` for every attribute would be noise. The three field names are therefore reserved: `validate` rejects an attribute called `key`, `paths`, or `attributes` rather than deciding which one `unit.key` meant. Everything downstream is then indifferent to which form `from` took: `stratify_by`, `assign.from`, `cluster_by`, and `null_test.shuffle` all name attributes, and every check in [Validation](#validation) applies unchanged. [Technical replicates](#what-isnt-a-repeat) work the same way with one extra obligation: yield one `Unit` per measurement, sharing a `key`, and emit `measurements.by` as an *attribute* — a resolver has no columns beyond the ones it declares, so the field a CSV would simply have carried has to be named. That's the division of labour — **the plugin decides how units are found; core decides what is required of them** — and it's why there is no schema block anywhere in `data.units`. What a resolver must produce is a projection of the design declarations already written above it.

**It sees the same `cfg` a `scope: "run"` step does, and the same coherence rule applies:** a resolver that reads a parameter the sweep varies is rejected by `validate`. The unit table is one table for the whole run, so conditions that resolved different units couldn't be paired and `n` would mean something different in each. Parameters the sweep leaves alone are fair game, which is how a resolver is told which assay, panel, or shard to include.

**It runs at `validate` and `dry-run`, not only at `run`.** Every unit check in the validation table — keys unique, strata present, cells populated, `k` within the cluster count — is a question about the resolved table, so the table has to exist before a step does. A resolver that walks a large archive pays for that walk each time you validate. That cost is what makes those checks real rather than deferred to four hours into the run — and it isn't what [`input_manifest_policy`](#three-hashes) controls: that policy bounds what gets *hashed*, not what a resolver reads. For an archive too large to walk cheaply, resolve from an index inside it rather than from the tree, which is the same reason `hash_index` exists.

The `io` a resolver receives is read-only: `io.read_input` and nothing else. There is no run directory yet at validate time and no step yet at run time, so there is nothing for it to write into.

**Provenance is unchanged by the indirection.** The resolved list lands in `provenance.units` and its hash in `provenance.units_hash`, exactly as for a table, the resolver's plugin version in `provenance.plugin_versions`, and its name in the embedded config. A resolver that yields a different roster next month is therefore *detected* when a [reproduction](#reproducing-on-another-device) runs, not prevented — the same promise core makes about the input files themselves. Under [`input_manifest_policy: hash_index`](#three-hashes), "the index and whatever it names" means the paths the resolver read plus the paths its units name, so a unit whose payload the resolver never opened still gets that payload hashed.

### The unit list is three operations, and the units in it are frozen

`io.units` supports iteration, `len`, and integer indexing, and `io.units.train` is the same kind of sequence — there is no `io.units.train.train`, because a partition of a partition is not a thing the declarations describe. That is the whole contract, and it is short for the same reason [`aggregate`'s table](#templates-where-parameters-are-defined) is: a sequence that also promised slicing, membership, and `.index` would just be a `list`, and core could never change what backs it — a lazily materialized roster, a view over a partition — without breaking every step written against it. Iteration is repeatable, so `list(io.units)` and a second `for` both work; filtering is ordinary Python over that iteration, which at cohort scale costs nothing measurable.

**A `Unit` is immutable, and that is a correctness rule rather than a style.** `key` is a string, `paths` a tuple, `attributes` a read-only mapping, and the [declared attributes readable directly](#where-units-come-from) are read-only too. The roster is resolved **once per run** and the same objects are handed to every condition and every execution — which is what [pairing across conditions](#allocation-within-subjects-or-between-subjects) requires — so a step writing `unit.attributes["scored"] = True` would be editing what the next condition sees, and every condition after it would run against a roster silently different from the one `units_hash` covers. Core [cannot inspect a step's body](design-principles.md#greenfield-only) to catch that, so the object refuses instead, raising [`ContractError` · `E-UNIT-IMMUTABLE`](#errors-core-raises) at the write. A unit is also hashable by its `key`, since that is the identity `data.units.key` already declares, which makes a `set` of units the ordinary way to carry a subset through a step.

### Allocation: within-subjects or between-subjects

This is the first question any experimental design answers, so core asks it explicitly rather than assuming.

**`allocation: within`** (default) — every condition sees every unit. The same patients are scored by all three methods; the same simulator inputs run at all parameter settings. Comparisons across conditions are *paired*, and core uses paired statistics automatically.

**`allocation: between`** — each unit belongs to exactly one arm, and `io.units` yields only that arm. This is the parallel-arm trial, the between-subjects psychology study, the A/B test, the case-control comparison. It requires a [group axis](#expansion-modes) to name the arms, because "between" answers *how units reach an arm*, not *what the arms are*:

```yaml
sweep:
  groups:
    - by: arm                      # the axis name — conditions become 00_arm=control, 01_arm=treatment
      levels: [control, treatment]

data:
  units:
    from: index.csv
    key: patient_id
    attributes: [site, sex, severity]
    allocation: between
    assign:
      arm:                         # keyed by axis name — one block per declared axis
        method: random             # random | by_attribute | blocked
        stratify_by: [site, severity]   # balance arms on these
        ratio: {control: 1, treatment: 1}   # keyed by level, one entry per level of THIS axis;
                                            #   `{}` means equal allocation
        block_size: auto           # blocked only; auto = twice the ratio's sum (rounded), or twice the level count when ratio is {}; checked like any block_size
        seed: auto                 # derived from the design digest and the axis name
```

The realized assignment is written to `allocation.json` in the run directory, and its hash lands in `provenance.allocation_hash` beside the path — so "which patients were in the treatment arm" is answerable from the run record alone, and a file edited after the run no longer matches what that run reported. Not from a script someone ran once.

**`limits.min_units_per_cell` is declared, typed, and read by nothing in this build.** An arm no unit resolves to is already refused, as `E-DATA-ASSIGN-LEVELS`; a single-unit arm is not the uncovered case either, since a lone value carries no dispersion to describe and core already declines to interval it. But a two-arm design where one arm resolves to exactly two units passes `validate` clean and reports a real `basis: units` interval [computed](#the-unit-table-is-the-inference-base) from those two observations — small enough that no one should trust it, and nothing warns. § Validation's *Cells are populated* and *Allocation is coherent* name the same gap, and so does this parameter's comment in [§ The one config file](#the-one-config-file).

**All three methods execute.** `random` and `blocked` draw the arm and `by_attribute` reads one a trial system or the data already assigned — which is what a real trial does regardless of which tool is doing the analysis, and the reason it is the method most designs carry. A drawn axis leaves no column, so what it drew is recorded in [`allocation.json`](#allocationjson--who-went-where) instead, under `seed` and, when it balanced on one, `strata`.

`by_attribute` covers the case where nothing was assigned by this tool: the grouping already exists in the data, as it does for a case-control study or an arm randomized by a trial system years ago. It names the column instead of a seed:

```yaml
    assign:
      arm:
        method: by_attribute
        from: arm                  # a unit attribute whose values are exactly the declared levels;
                                   # `from` defaults to the axis name, so this line is optional here
```

**An empty `ratio` is equal allocation**, which is what `init` writes and what most designs want: `{}` allocates each level of the axis the same share, so a two-arm trial needs no entry at all and a three-arm one gets thirds. Spelling it out is for an unequal design — `{control: 1, treatment: 2}` — and a partial mapping is rejected rather than defaulted, since "one entry per level" is checkable and "the levels I left out get the average" is a rule nobody should have to infer, as `E-DATA-ASSIGN-RATIO`. Under `method: by_attribute` a `ratio` describes a draw that didn't happen, so `validate` rejects a non-empty one instead of recording a proportion the data may not honour. The same is true of `assign.<axis>.stratify_by`: under `method: by_attribute` it would describe how a draw was balanced when none was — the same fault — so `validate` rejects a non-empty one there too rather than recording a balance the data may not honour, both under one code, `E-DATA-ASSIGN-NO-DRAW`.

**`stratify_by` balances each arm within every stratum, and the realized totals may not honour the `ratio` exactly.** The roster is split into one group per combination of the named attributes' values, and the ratio is apportioned inside each group — which is what makes an arm carry its share of every site rather than only its share of the roster. The cost is that each group's own rounding is independent and the leftovers add: three strata of five units under `{control: 1, treatment: 1}` give 3/2 in every stratum, so 9/6 overall where an unstratified draw of the same roster gives 8/7, and the surplus goes to the first-declared level each time. So the deviation from the declared ratio is bounded by the number of strata rather than by one unit — the same shape of non-promise [§ Clustered units](#clustered-units) makes for a stratified fold, and for the same reason: balancing the totals across strata is what would unbalance the strata themselves. It also makes an empty arm easier to reach, since a stratum smaller than the level count apportions some level nothing — refused as `E-DATA-ASSIGN-LEVELS` when no stratum covers that level at all, never silently.

`blocked` uses permuted blocks of `assign.block_size` units — `auto` is twice the sum of `ratio`, rounded to a whole number of units, the smallest block that isn't a fixed alternating pattern — and every declared level must get a whole number of units in each block, whether `block_size` is `auto` or explicit, so every block fills each arm exactly. That is a **different** requirement from the sum of `ratio` merely dividing `block_size` evenly — neither implies the other. `{a: 0.5, b: 0.5}` sums to 1, and a `block_size` of 1 divides it, but each level's own per-block share is 0.5, not whole. `{a: 2, b: 2}` sums to 4, and a `block_size` of 2 does *not* divide it, yet each level's own per-block share, `2 × 2 / 4 = 1`, is whole. `auto` is checked the same way an explicit value is, not exempted: for `{a: 0.33, b: 0.33, c: 0.34}` — an ordinary percentage split — `auto` resolves to 2, and none of the three levels' shares of it are whole, refused before it ever reaches a run rather than starving a level in every block and failing there instead. Over an empty `ratio` — equal allocation, one part per level, which is what `init` writes and what most designs carry — the sum is the level count, so `auto` is **twice the number of levels**: a two-arm trial gets 4, a three-arm one gets 6. It balances arms across the roster's order rather than across an enrollment sequence — core assigns a fixed unit list at run start, so there is no accruing cohort for it to balance over time. Use it when the roster order carries meaning (site batches, plate order); otherwise `random` with `stratify_by` is the stronger guarantee. **Beside a declared `cluster_by`, `blocked` is refused outright**, as `E-DATA-ASSIGN-BLOCKED-CLUSTER`: a block counts units and fills to an exact size, a cluster is indivisible, and no block size honours both — `random` has no such conflict, since drawing a whole cluster fills no size at all. Use `random` for a cluster-randomized design.

**Under `method: by_attribute`, `assign.<axis>.from` must not vary within a unit's [measurement rows](#what-isnt-a-repeat)**, and core refuses one that does, as `E-DATA-ASSIGN-VARIES` — the same shape [`cluster_by`](#clustered-units) and [`weight_by`](#weighted-samples) refuse, and reported through the same collapse. **This one is the worst of the three**: a mis-collapsed cluster decides which side of a split a unit lands on and a mis-collapsed weight mis-sizes what one unit stands for, but a mis-collapsed arm decides which *condition* the unit is measured in — so replicate rows declaring `control` and `treatment` would leave that decision to whichever the file lists first. An arm is a fact about the unit, not about the measurement. Not checked under `random`/`blocked`: `from` "means nothing" there either, the same reason `E-DATA-ASSIGN-UNKNOWN`'s name check skips them — a drawn axis reads no column, so there is none whose replicate rows could disagree.

**`assign.<axis>.stratify_by` carries no such refusal, and that gap is recorded rather than closed.** A stratum is read per unit when the draw is balanced, so a stratum column whose replicate rows disagree decides which stratum a unit is balanced within — the same shape the paragraph above calls the worst of three, one field over. It is not among the columns the collapse checks, so replicate rows declaring `site: S1` and `site: S2` collapse to whichever the file lists first and the draw balances on that, silently. Closing it means adding the field to the same constant-column family `from`, `cluster_by` and `weight_by` are already in, under `E-DATA-ASSIGN-VARIES`; until then, the honest statement is that a stratum is trusted where an arm is verified. A stratum varying within a *cluster* is a different question and is refused, as `E-DATA-ASSIGN-STRATIFY-VARIES`.

Getting this wrong is not a subtle error. Analyzing a between-subjects study as if it were paired inflates precision substantially, and the two designs need different comparisons. Because allocation is declared, core derives the comparison type instead of asking you to declare `paired` separately and hoping it matches reality.

**Pairing is derived per comparison, not per config.** `allocation` is one value, but a run can hold contrasts of both kinds at once, so a single boolean over the whole run would be wrong for some of them. What decides a given contrast is whether the two conditions it compares share their units, and that's answerable from which axes they differ on:

| The two conditions differ on | Share units? | Comparison |
|---|---|---|
| Parameter axes only (`grid`, `paired`, `sample`, `ablate`), `allocation: within` | Yes, all of them | Paired, unit by unit |
| Parameter axes only, `allocation: between` | Yes — same arm, so same units | Paired within that arm |
| Any `groups` axis | No, by construction | Unpaired |
| Two `groups` axes, or a `groups` axis *and* a parameter axis | No | Unpaired, and confounded — see below |

So in "each arm analyzed three ways" ([`groups × grid`](#expansion-modes)), control-pearson vs. control-spearman is paired — the same patients scored two ways, and pairing is what cancels the between-patient variance — while control-pearson vs. treatment-pearson is unpaired. Deriving one answer for the whole run would report the first as unpaired and throw that cancellation away, which is the same class of error as the inflation above, just in the conservative direction. Each contrast records its own `paired: true|false` in `vs_baseline`.

The last row is the one to design around rather than rely on. A contrast crossing two axes at once — two group axes, or a group axis and a parameter axis — differs in two places, so its delta mixes the two effects and no amount of correct pairing separates them — that's the [factorial main-effects problem](experimental-designs.md#what-core-will-not-do-for-you), and it's why such a contrast is marked rather than merely reported:

```yaml
vs_baseline:                                   # 03_arm=treatment__method=spearman
  step03_analyze:
    r: {delta: 0.041, basis: units, paired: false, confounded: true,
        method: unpaired_percentile_over_units,
        differs_on: [arm, analysis.method],    # two axes at once — not a main effect
        ci95: [0.012, 0.070]}
```

Leave the nuisance axes out of `sweep.baseline` and the problem doesn't arise: the baseline [expands over every axis it doesn't fix](#expansion-modes), so each cell gets its own reference and every contrast differs in exactly one place. Fixing a value on every axis is the other coherent choice, and it's the one that produces contrasts like the above — interpretable on the single-axis ones, marked on the rest.

### A fixed holdout split

Fitting on most of the data and evaluating on the rest, once, is the most ordinary evaluation there is. It's declared where units are resolved, because that's what it is — a partition of the unit table, decided once and never re-drawn:

```yaml
    holdout:
      method: random                 # random | by_attribute
      frac: 0.2                      # test fraction, for random
      from: null                     # the attribute naming the partition, for by_attribute
      stratify_by: [label]           # balance the split on these
      seed: auto                     # derived from the design digest; recorded explicitly
```

`io.units` then yields the test partition and `io.units.train` the training one — the same two lists a `fold` repeat provides, without the repetition. `by_attribute` covers a split that already exists, which benchmark datasets usually ship: name the column (`from: split`) and core partitions rather than draws. **The column's values must be exactly `train` and `test`** — two fixed literals, not "whichever two values are there". A holdout declares no `levels` for core to read an order out of, and inferring one from the data would make which side is evaluated depend on a lexical accident of the input; a column holding `{A, B}`, or `{train, test, dev}`, is refused as `E-DATA-HOLDOUT-VALUES`. Rename the column's values, or map them in the step that produces the roster.

**A holdout is not a repeat kind, and that's not a technicality.** The repeat axis answers *what varies incidentally* — it exists to express multiplicity, and each level multiplies the executions. A holdout varies nothing and multiplies nothing: it's one split, fixed for the whole run, and `{kind: holdout, n: 1}` would be a repeat that never repeats. Putting it on `data.units` also puts it beside the other two declarations that partition units without re-executing anything, [`assign`](#allocation-within-subjects-or-between-subjects) and [`measurements`](#what-isnt-a-repeat). So [no repeat kind has to cover it](#repeat-kinds).

Four interactions worth knowing, all of them consequences of the rules already stated rather than new ones:

- **`holdout` and `fold` are mutually exclusive**, and `validate` rejects both together. They are two answers to one question — how the data is divided for evaluation — and declaring both leaves "which units is this metric over?" with no single answer. To hold out a final test set *and* cross-validate for model selection, declare the holdout and do the inner search inside the step over `io.units.train`, exactly as [§ Cross-validation](experimental-designs.md#cross-validation) prescribes for nested CV: a setting chosen from results is an output, not a condition.
- **`resolved` is the test partition**, per [§ What isn't a repeat](#what-isnt-a-repeat) — a 20% holdout over 240 units reports `resolved: 48`, and the interval is over those 48. That's the honest denominator: the training units produced no result to generalize from.
- **Whole clusters go to one side**, when [`cluster_by`](#clustered-units) is declared, and `stratify_by` must be constant within a cluster. Same rule and same reason as folds — a holdout that trains on one cell of an animal and tests on another leaks just as thoroughly for happening only once.
- **A roster-wide split beside a cell structure is refused, not drawn.** Under `allocation: between`, or under a non-empty `sweep.groups`, a single split of the whole roster would leave cells with unequal test sizes and, at worst, a cell with no test units at all — so core refuses the combination outright (`E-DATA-HOLDOUT-CELLS`), rather than recording a partition whose imbalance a reader would have to cross against the arms list by hand to see. A `fold` repeat beside the same cell structure is refused for the identical reason and under its own code, `E-REPL-FOLD-CELLS`. Drawing *within* each cell is the design that lifts both refusals, and it is not built.

**A holdout narrows a denominator and adds nothing to the correction family.** `statistics.resample` draws over the per-unit table, which under a holdout holds only the units that recorded — the test partition — so a percentile interval rests on that many units, and on that many [clusters](#clustered-units) when `cluster_by` is declared. `limits.min_clusters` is checked against the **test** partition's cluster count for that reason: a roster of 50 clusters under a `frac: 0.2` holdout resamples roughly 10, and warning against the wider number would be warning against a denominator no interval used. The units held back for training produced no result, so they are counted nowhere: not `completed`, not `ineligible`, not `failed`. `provenance.units.n` and `units_hash` stay whole-roster regardless — they are the roster's identity, not a metric's denominator, which is why `240` there and `48` in a metric's `n` are two true numbers rather than a contradiction.

The realized membership is written to `allocation.json` beside any arm assignment, under the same `provenance.allocation_hash`, so which units were evaluated is answerable from the run record rather than from whoever drew the split. One file and one hash cover both, since both are partitions of the same roster drawn once for the run.

### Weighted samples

A benchmark is often not a simple random sample of the population a claim is about. Cases are enriched, strata are oversampled, a registry draws by site. When the sampling probabilities are known, they are what turns a sample estimate back into a population one, and they're declared where the units are:

```yaml
    weight_by: sampling_weight        # a unit attribute holding the inverse sampling probability
```

Core then computes weighted means for [`basis: units`](#the-unit-table-is-the-inference-base) column metrics, hands the column to [`aggregate`](#templates-where-parameters-are-defined) like any other attribute so a derived metric can weight itself, and records `weighted_by` beside every affected value:

```yaml
r: {value: 0.607, basis: units, weighted_by: sampling_weight,
    n: {resolved: 240, completed: 228, failed: 12, effective: 191.4},
    ci95: [0.517, 0.683]}
```

When this same run also declares `resample.stratify_by` — the pairing the next paragraph makes, since a stratified sample usually needs both — the block carries both siblings at once, `weighted_by` and `resample`, one for each declaration:

```yaml
r: {value: 0.607, basis: units, weighted_by: sampling_weight,
    resample: {method: bootstrap, n: 2000, stratify_by: [dx_status, count_stratum]},
    n: {resolved: 240, completed: 228, failed: 12, effective: 191.4},
    ci95: [0.517, 0.683], resample_draws: 2000}
```

**That field is the point of the feature as much as the arithmetic is.** An unweighted mean over an enriched sample is not a noisier version of the population answer, it is an answer to a different question — and without a marker it arrives in exactly the same shape as the right one, with a `basis: units` and an interval, and nothing for a reader to notice. So `validate` also warns when an attribute *looks* like a weight — numeric, positive, varying across units in a way a measurement wouldn't, and named like one, its name containing `weight`, `_prob` or `probability` — and nothing declares it. The name is part of the test rather than a nicety: the other three hold of `age`, `dose` and `latency` too, and a warning that fires on nearly every numeric attribute is one a reader learns to skip. It is the trigger's weakest part for exactly the reason it is necessary — `weight` is body mass in an assay and a sampling weight in a survey — so the message says what to do about either in one step: declare it, or rename it. That's the same warning, for the same reason, as the one an [undeclared cluster](#clustered-units) draws — though not by the same means, and the difference is why the name is here at all: a cluster is *structurally* distinctive, a column of repeated non-numeric labels too few to be a key and too many to be a level set, so that warning needs no guess about what a column is called — see [`W-DATA-CLUSTER-UNDECLARED`](#warnings-core-reports) for the clauses. A weight has no such shape. `age`, `dose` and `latency` are positive, numeric and varying exactly as a sampling weight is, so the name is the only discriminator left.

**Weighting the estimator and stratifying the draw are two decisions, and a stratified sample usually needs both:**

```yaml
statistics:
  resample: {method: bootstrap, n: 2000, stratify_by: [dx_status, count_stratum]}
```

`weight_by` says how much each unit stands for; `resample.stratify_by` says what an independent draw is, resampling within each stratum so a bootstrap can't return a replicate whose stratum composition the design ruled out. `fold`, `holdout`, and `assign` all take a `stratify_by` already; `resample` taking one closes an asymmetry rather than adding a concept. A `holdout` also decides what a draw is *over*: `resample` draws from the per-unit table, which under a holdout holds the test partition alone — see [A fixed holdout split](#a-fixed-holdout-split).

A weighted `t_over_units` interval uses the weighted mean and the weighted variance, with the degrees of freedom taken from Kish's effective sample size rather than the row count — weighting concentrates the estimate on fewer units, and an interval that ignored that would be narrower than the sample supports. **That size joins the three-part `n` as `effective`**, on exactly the argument [`clusters`](#clustered-units) joins it on: an interval whose df came from 191 is a different construction than one whose df came from 228, and which one a reader is holding shouldn't have to be inferred from `weight_by` being set elsewhere in the config. A percentile interval draws units as usual and recomputes the weighted statistic on each draw, so the weights are in the estimate rather than in the drawing.

Four interactions worth knowing. `n` still counts units — `effective` sits beside `completed` rather than replacing it, because weights change what each unit contributes and not how many there were, so a weighted interval over 228 units is still an interval over 228 units. `cluster_by` still decides the draw when both are declared, since a cluster is what's independent and a weight is what it represents. And a [contrast](#contrasts-claims-that-arent-condition-vs-baseline) between two weighted conditions uses the same weights on both sides, which is automatic under `allocation: within` and worth checking when it isn't. Last, **a weight must not vary within a unit's [measurement rows](#what-isnt-a-repeat)**, and core refuses one that does, as `E-DATA-WEIGHT-VARIES`. `measurements` would otherwise collapse the weight column like any other attribute, so replicate rows carrying 1 and 99 would become a single weight of 100 under `sum` — a number no row declared — or of whichever arrived first under the default rule, which would make the answer depend on the order the file happens to be in. The refusal is raised where the rows collapse, which is inside resolution, so `validate` reports it too: the disagreeing values exist only before the collapse, and by the time there is a roster to check they are already gone. A weight is what one unit stands for, so it is a fact about the unit and not about the measurement.

### Clustered units

When units aren't independent — patients within sites, cells within animals, measurements within subjects — declare it:

```yaml
    cluster_by: site
```

Core then computes cluster-robust intervals — over the same per-unit table every other interval comes from — and reports the number of clusters as the effective sample size alongside the unit count. Ignoring clustering is the standard route to intervals that are too narrow; declaring it costs one line, and `validate` warns when an attribute looks like a cluster identifier but hasn't been declared as one — repeated non-numeric labels, more than two of them, which is few distinct values with many units each without also being a level set like `sex` or a second key. [`W-DATA-CLUSTER-UNDECLARED`](#warnings-core-reports) states the trigger in full, and is the one place it is stated.

**`cluster_by` also constrains how `fold` partitions.** Whole clusters go to one side of a split; a cluster is never divided between train and test. This is not a refinement of the interval, it's the difference between a valid evaluation and a leaky one: with 300 cells from 10 animals split without regard to `animal_id`, every fold trains on other cells of the animal it tests on, and the metric is inflated before any interval is computed — so cluster-robust standard errors don't repair it. Core computes the partitions, so this has to be core's rule rather than something each experiment remembers.

Two consequences of clustering the split:

- **`k` is bounded by the cluster count, not the unit count.** Ten animals admit at most 10 folds, and `validate` rejects a larger `k` rather than emitting empty partitions. Fold sizes also stop being equal — clusters differ in size, so core balances units-per-fold as evenly as whole clusters allow and records the realized sizes in `sweep.yaml`. **The order it assigns in is part of the contract, not an implementation detail**: core shuffles the clusters using the [design digest](#what-auto-derives-from), then walks them largest-first, sending each whole cluster to the fold holding the fewest units so far. Both halves earn their place — without the shuffle, equally sized clusters would be partitioned in whatever order the input file listed them, and without the largest-first pass a big cluster arriving last has no balanced fold left to go to. What is *not* promised is a bound on how uneven the result may be: one cluster larger than the units a fold would otherwise hold makes an uneven split unavoidable, and core reports the realized sizes rather than pretending otherwise.
- **`stratify_by` must be constant within a cluster.** Stratifying folds on an attribute that varies inside a cluster is unsatisfiable once the cluster is indivisible, so `validate` rejects it instead of silently prioritizing one constraint. Stratifying on `animal_strain` works; stratifying on a per-cell `label` that differs within an animal does not. That constancy is also what makes the stratified split well-defined rather than a second balancing problem: a cluster carrying one stratum value belongs to exactly one stratum, so core runs the rule above inside each stratum separately and then merges the per-stratum partitions **index-wise** — fold *i* of every stratum's partition becomes fold *i* of the result, which is what makes each fold carry its share of each stratum. Reordering that merge is invisible to any assertion about fold *sizes*, since permuting a stratum's pieces leaves their sizes alone, which is why the order is stated rather than left to be re-derived. All of it rests on the rejection above: without it a cluster could belong to two strata and there would be nothing to merge.

**A cluster must not vary within a unit's [measurement rows](#what-isnt-a-repeat)**, and core refuses one that does, as `E-DATA-CLUSTER-VARIES`. `measurements` would otherwise collapse the cluster column like any other attribute, under `first` or `mode` — the only rules a string column admits, `mean` over one being [rejected](#validation) rather than coerced — so a unit whose replicate rows declare `S1` and `S2` would collapse to `S1`, chosen by the `first` fallback, which would make the answer depend on the order the file happens to be in. The refusal is raised where the rows collapse, which is inside resolution, so `validate` reports it too: a check reading the roster would see the collapsed value and never the disagreement that produced it. **The consequence is worse than the same mistake in a [weight](#weighted-samples)**: a mis-collapsed weight mis-sizes what one unit stands for, while a mis-collapsed cluster decides which side of a train/test split that unit lands on — and a unit filed under the wrong site is a unit whose real site is on both sides, which is the leak this section calls the difference between a valid evaluation and a leaky one, arriving through the input file rather than through the partition. A cluster is a fact about the unit, not about the measurement.

The same logic governs `assign.stratify_by` under `allocation: between` — **when core is the one assigning.** With `method: random`, a cluster is drawn as a whole, so arms are balanced over clusters and no cluster straddles two arms. A cluster-randomized trial is exactly that design, and the rule is the same one that keeps a cluster out of two folds: core computed the partition, so core keeps it indivisible. **`method: blocked` beside a declared `cluster_by` is refused instead**, as `E-DATA-ASSIGN-BLOCKED-CLUSTER`: a block fills to an exact unit count and a cluster is indivisible, so no block size honours both at once — where `random` draws whole clusters with no size to fill exactly, `blocked`'s whole premise is a block that fills. Use `random` for a cluster-randomized design.

**With `method: by_attribute` the arm is read rather than drawn, and a cluster may span both arms — in a [matched case-control](experimental-designs.md#matched-case-control) design it always does.** A matched set holding one case and one control is what matching *is*, and core neither prevents it nor treats it as an error: nothing was assigned, so there is no draw to keep whole. What `cluster_by` does there is set the inferential draw instead. The contrast stays unpaired, since no unit appears in both arms, but its interval is cluster-robust on the matched set — so the effective `n` is the number of sets rather than the number of subjects, which is the accounting a matched design needs. A conditional *estimator* is still yours, in a `scope: "summary"` step.

**And it decides what [`statistics.resample` and `statistics.null_test`](#what-isnt-a-repeat) operate on.** Both work by rebuilding the unit table, so both need to know what an independent draw is. Undeclared, they treat 300 cells as 300 of them; declared, the cluster is the draw:

- **`resample` resamples clusters, not rows.** A bootstrap that draws 300 cells with replacement from 10 animals produces resamples far more alike than a fresh sample of animals would be, so the percentile interval comes out too narrow — the same failure `cluster_by` exists to prevent, arriving by a different route. Core draws whole clusters with replacement, so a resampled table has a varying row count, and the interval's effective `n` is the cluster count. That count joins the [three-part `n`](#what-isnt-a-repeat) rather than replacing it — `n: {resolved: 300, completed: 300, failed: 0, clusters: 10}` — because a percentile interval over 10 draws is a different claim than one over 300, and which one a reader is holding shouldn't have to be inferred from `cluster_by` being set somewhere else in the config.
- **`null_test` shuffles at the level the shuffled attribute lives at.** Core derives which from the data rather than asking: if `shuffle` names an attribute that varies *within* clusters, labels are permuted within each cluster independently — for [matched case-control](experimental-designs.md#matched-case-control) that's a case/control swap inside each matched set, which is the conditional test that design calls for. If the attribute is constant within a cluster, whole clusters are relabelled, which is the null for a cluster-randomized trial. Shuffling rows freely would destroy the structure the null is supposed to hold fixed, and the two designs need opposite treatments, so guessing is not an option.

`validate` rejects the ambiguous middle: an attribute constant within some clusters and varying within others has no correct level, and neither null is defensible over a mixture.

Core resolves this once at run start, records the resolved list in `provenance.units` and its hash in `provenance.units_hash`, and makes it available everywhere:

```python
class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        model = fit(io.units.train, cfg.parameters)  # empty unless a fold or holdout is declared
        for unit in io.units:                        # this fold's test split, or this arm
            pred = predict(model, unit)
            io.record(unit.key, {"pred": pred, "truth": unit.label})
        return {}                                 # metrics can be derived from the unit table
```

`io.units` is already scoped correctly: under a [group axis](#expansion-modes) it yields only that arm's units, and under a `fold` repeat or a [`holdout`](#a-fixed-holdout-split) only the **test** partition — the units this execution produces results about. The training partition is `io.units.train`, which is a different list for a different purpose, and keeping them separate is what stops a step from silently recording a result for a unit it trained on. Core computes the partitions, so no experiment reimplements k-fold, and the exact membership of every split lands in `sweep.yaml` — which is what makes a cross-validation reproducible rather than merely re-runnable.

**Partitions are computed once per run, not once per condition.** Every condition sees the same fold boundaries and the same seed list, derived from the config-level [design digest](#what-auto-derives-from). This is load-bearing rather than incidental: under `allocation: within`, comparisons across conditions are paired unit by unit, and pairing fold 3 of one condition against a *differently drawn* fold 3 of another would not be a paired comparison at all. Shared partitions are also why the layout can name repeat directories `seed17`/`fold03` identically under every condition.

**Under `allocation: between`, a roster-wide fold is refused rather than drawn within each cell** — the same rule as a [holdout](#a-fixed-holdout-split), for the same reason: one roster-wide partition would give the cells unequal test sizes and, once `k` approaches the smallest cell's size, a fold holding none of that cell's units at all, which is a cell-level metric computed from nothing. Drawing within each cell would keep every fold proportional throughout, bounding `k` by the *smallest* cell's unit count — or its cluster count, when `cluster_by` is declared — but that draw is not built, so `validate` refuses the combination outright (`E-REPL-FOLD-CELLS`) rather than bounding `k` against it.

**`io.record(key, values)` is the inference base, not a convenience.** Between artifacts (files) and results (aggregate metrics) sits the per-unit table, and it is what every confidence interval core reports is computed over. It's append-only like everything else, resumable by key, and materialized as `units.parquet` in the step's directory. A step that records nothing still runs and still reports its returned metrics — but if units were declared, core has nothing to generalize from, so those metrics come back as `basis: repeats` with no interval. See [Statistical reporting](#statistical-reporting).

`data.units` is optional — a simulation with no unit table simply omits it, and `fold`, `statistics.resample`, and `statistics.null_test` then aren't available, which is correct, since there'd be nothing to partition or resample. Such an experiment reports over repeats and says so; that's the one case where a repeat count is the honest denominator, because the executions *are* the observations.

---

## Step scope

Not every step should run the same number of times. Loading a cohort doesn't depend on which analysis method is being tested, so re-running it once per condition per repeat is both wasteful and ontologically wrong — it implies a dependency that doesn't exist.

Each step declares its scope:

| `scope` | Executes | Artifacts land in | Typical use |
|---|---|---|---|
| `"run"` | once | `<run_dir>/shared/<step>/` | ingest, validate, normalize the input dataset |
| `"condition"` | once per condition | `conditions/<nn>_<label>/<step>/` | fit a model for this parameter set — when the training set doesn't vary within the condition; see below |
| `"repeat"` | once per repeat (the default) | `conditions/<nn>_<label>/<repeat>/<step>/` | evaluate on this fold or seed |
| `"summary"` | once, after everything | `<run_dir>/summary/<step>/` | compare conditions, produce the headline table |

```python
class CohortPilotExperiment(BaseExperiment):
    steps = [LoadCohort, FitModel, Analyze, CompareMethods]
```

```python
class LoadCohort(BaseStep):
    scope = "run"            # 1 execution, not 15

class FitModel(BaseStep):
    scope = "condition"      # 3 executions

class Analyze(BaseStep):
    scope = "repeat"         # 15 executions

class CompareMethods(BaseStep):
    scope = "summary"        # 1 execution, reads across everything
```

One ordered `steps` list expresses the whole pipeline, and core derives the execution plan from the declared scopes. A cross-condition comparison needs no separate list of its own — it's simply the outermost scope.

Reading across scopes is directional and read-only: a narrower step reads wider ones via `io.read_upstream(step, name)` regardless of scope, and a `summary` step additionally gets `io.conditions` and `io.read_condition(condition, step, name, repeat=None)`, whose `repeat` is required when the step it names is repeat-scoped. A wider step can never read a narrower one, because at the time it runs those executions haven't happened. Which step a call names is an argument rather than a declaration, so this is enforced where the call is made: `io.read_upstream` raises when the step it names is narrower than the caller, naming both scopes. Same effect check as the two below.

A `summary` step sits above every condition, so once a sweep labels its conditions, `io.read_upstream` naming a condition- or repeat-scoped step has no single condition to resolve to — that ambiguity is exactly what `io.read_condition` exists to name explicitly. With no sweep declared there is exactly one, unlabeled condition, and `io.read_upstream` still resolves it directly. The same ambiguity recurs one level down, independently of any sweep: a `summary` step sits above every *repeat* too, so once a run resolves more than one repeat, `io.read_upstream` naming a repeat-scoped step has no single repeat to resolve to either, and raises for the same reason and toward the same `io.read_condition(..., repeat=...)`. With exactly one repeat that level collapses — the same collapse rule `io.read_condition`'s own nesting already applies — and `io.read_upstream` keeps resolving it directly.

**A swept parameter is unreadable from the scopes where it has no value.** A `"run"`-scoped step that read `analysis.method` would produce output silently wrong for every condition but one, and a `"summary"`-scoped step that read it would be picking a value no single condition owns. Neither is something core can catch by reading the config: which parameters a step reads is a fact about its body. So core doesn't ask — it owns `cfg`, and at `"run"` and `"summary"` scope, reading a path that `sweep` varies raises, naming the path and the axis that varies it. Unswept paths read normally at every scope, which is most of what a wider step wants a parameter for.

That's the same effect check as [`io.units` raising under a `fold` repeat](#a-fold-repeat-puts-the-units-out-of-reach-of-the-wider-scopes), applied to the other thing core hands a step: rather than inspecting what the step intended, core declines to hand over a value that could only be the wrong one.

### A `fold` repeat puts the units out of reach of the wider scopes

Fitting a model is the typical `"condition"`-scoped step, and that is the right scope exactly when the training set doesn't vary *within* the condition: under `seed` repeats, or under a fixed [`holdout`](#a-fixed-holdout-split), one fit serves every repeat and repeating it would be waste.

Under a [`fold`](#repeat-kinds) repeat it is the wrong scope, and not subtly. There is no fold at condition scope — folds are repeats, and repeats haven't happened yet — so a step fitting there fits on the units that later folds will test on, and every fold's metric comes back in-sample. That is the same leak [`cluster_by`](#clustered-units) exists to prevent one level down, arriving through the execution plan instead of through the partition.

Core can't read the body of a step to find out whether it fitted on those units. It doesn't have to, because it owns `io`: **when any `fold` repeat is declared, `io.units` and `io.units.train` raise at `"run"` and `"condition"` scope**, naming the fold that doesn't exist yet and pointing at repeat scope. Fitting moves into the `"repeat"`-scoped step, which is where the fold is. Wider steps that never touch units — loading a shared file, resolving paths, writing a manifest — are unaffected, which is most of what they're for.

This is an effect check, not an inspection of your code: core doesn't ask what the step intended, it declines to hand over a list that could only be the wrong one. Same line as [greenfield only](design-principles.md#greenfield-only) draws everywhere else. A `holdout` does not raise, because its split is fixed for the whole run and a condition-scoped fit over `io.units.train` is exactly correct.

---

## Templates: where parameters are defined

A template is the authoritative definition of an experiment type's parameters. Core never inspects `parameters` itself.

```python
from publishable import BaseTemplate, register_template, Param

@register_template("generic")
class GenericTemplate(BaseTemplate):
    naming_pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    field_convention = "generic"
    default_repeats = 1
    version = "1.0.0"
    required_env = []
    apparatus_probe = None            # see "The apparatus core can only observe"
    apparatus_facts = []              # which keys the probe must supply, if one is declared

    # One spec drives all three jobs: what `init` writes, what its comments say,
    # and what `validate` enforces. There is no second source of truth.
    parameter_spec = {
        "analysis.method":      Param(str,   default="pearson",
                                      choices=["pearson", "spearman", "kendall"]),
        "analysis.min_samples": Param(int,   default=30, ge=2),
        "analysis.confidence":  Param(float, default=0.95, gt=0, lt=1),
        "analysis.drop_missing":Param(bool,  default=True,
                                      help="Drop rows with any missing value before analysis"),
    }

    def validate(self, config) -> list[str]: ...     # cross-field rules; [] if OK.
                                                     # Receives the WHOLE config, not just
                                                     # `parameters` — see below

    # Optional; derives metrics FROM the unit table. `cfg` is this condition's
    # resolved parameters — the same object a step receives.
    def aggregate(self, units, cfg) -> dict:
        fn = {"pearson": pearsonr, "spearman": spearmanr, "kendall": kendalltau}
        return {"r": fn[cfg.parameters.analysis.method](units.pred, units.truth).statistic}
```

**A template can live in three places, and where it lives decides how it's pinned.** Core ships `generic`; a plugin ships its own and arrives as a pinned `uv.lock` entry; `generate template` writes one into `templates/` in your own repo, for a template only this project needs. The third is code the run's numbers came out of and has no version anyone resolves, so [`code_hash` covers `templates/**`](#three-hashes) alongside `src/**` — editing a local `aggregate` moves the hash exactly as editing a step does, and `run` refuses a dirty `templates/` for the same reason it refuses a dirty `src/`. Discovery importing every file to find its registration writes `templates/__pycache__/`, same as any import, and two different mechanisms keep it out of the way. `code_hash` skips `__pycache__` directories and compiled `.pyc`/`.pyo` files unconditionally, wherever in the hashed trees they sit — it reads the working tree rather than git, so no ignore file could have done that for it. The **dirty gate** is what the [scaffolded](#scaffolding-publishable-new) `.gitignore` is for: it already excludes both, so `validate` and `run` see a clean tree. A hand-assembled repo whose `.gitignore` omits that line goes dirty at `validate` and fails `run` — while its `code_hash` is unchanged, that being the mechanism an ignore file has no bearing on. Where it lives also decides how it is *found*: the first two are [registered through an entry point](#creating-a-plugin-publishable-plugin-new), and the third — which is installed nowhere and distributed to nobody — is discovered by path from the fixed layout, making its `@register_template` argument the whole of its registration. Every non-dunder-stemmed file the fixed layout finds under `templates/` is read as one of these local templates, and one that fails to load — see [`E-TEMPLATE-LOAD`](#errors-validate-reports) — is a fault rather than a silence; a genuine helper file is named with the `__`-prefix `__init__.py` already uses to be skipped.

**`validate` receives the whole config, not only `parameters`.** The rules a template most needs to enforce are often *cross-block*, because they are properties of what its steps do and core cannot know them. An experiment type that fits a model needs somewhere to fit — so a template whose pipeline compiles a program can reject a config that declares no [`holdout`](#a-fixed-holdout-split) and no `fold` repeat, because otherwise `io.units.train` is empty and the evaluation happens on the units the model was fitted against. Core has no way to tell that config from a legitimate one; the template does.

Reading the envelope is not owning it. A template still declares nothing outside `parameters` — it cannot add a field to `data` or change what `sweep` means — and returning an error from `validate` is the only thing it does with what it reads. That's the same division [`aggregate`](#templates-where-parameters-are-defined) sits on: it sees a resolved condition without getting to decide what the conditions are.

`aggregate` returns condition-level metrics derived from the per-unit table. It's optional, and it's the only way to give a derived statistic a real confidence interval: because core can call it on a resampled table, the metric becomes `basis: units` instead of a scalar core can only watch vary across seeds. See [The unit table is the inference base](#the-unit-table-is-the-inference-base).

**The table it receives supports exactly four operations, and that's the whole contract:**

| Operation | Is |
|---|---|
| `for row in units` | Iterates rows, each a mapping of column name to value |
| `units.<name>` | That column, as a sequence in row order |
| `len(units)` | The row count — one per unit after collapsing |
| `units.columns` | The column names present |

Columns are whatever the step [recorded](#units-the-thing-being-measured) plus every declared unit attribute, so `units.truth` and `units.pred` are the same shape whichever of the two supplied them. A declared attribute is carried through **unchanged** rather than averaged: it comes from the roster rather than from an execution, so unlike a recorded numeric column it has nothing to collapse across a unit's repeats. It is a column here and nothing else — never a metric, and never something `aggregate`'s own return can collide with, which a [recorded column of that name is](#validation). A column has one entry per row, in row order, reading [`None`](#the-per-unit-tables) where that unit recorded nothing — which is what makes `pearsonr(units.pred, units.truth)` above pair each unit's prediction with *its own* truth even when the two columns are ragged in different rows. A name no row holds is `E-STEP-COLUMN-UNKNOWN` rather than an empty column.

**Four operations rather than a rich table type, on purpose.** The temptation is to promise a `DataFrame`, since one would arrive with filtering, grouping, and vectorized arithmetic already written. The cost is that every template would then be written against that library's idioms — boolean-mask indexing, `.isin`, `~` on a column — and core could never change what backs the table without breaking every plugin at once. A four-operation contract means a template does its filtering in ordinary Python and keeps working whether core stores rows, columns, or something it hasn't chosen yet. At unit-table scale that costs nothing measurable: `n` is a cohort, not a billion rows, and a metric that iterates 440 patients is not the slow part of an experiment that made 440 requests.

So a metric filters by iterating, and reads a whole column only when it wants one:

```python
def aggregate(self, units, cfg) -> dict:
    positives = [r for r in units if r["truth"]]                 # filter in Python
    detected = sum(1 for r in positives if r["pred"])
    return {
        "sensitivity": detected / len(positives) if positives else None,
        "r": pearsonr(units.pred, units.truth).statistic,         # or take columns
    }
```

`aggregate` returning `{}` is the right answer for a table it doesn't recognize — core calls it once per recording step, and a pipeline can have several. What it may return otherwise is [what a step may return](#steps-and-artifacts): a flat mapping of scalars, with the same coercion of a NumPy scalar and the same `ContractError` on anything structural. There is no `Estimate` exception here, since a derived metric is one core computes and resamples itself.

**It receives the condition's resolved `cfg`, and it has to.** In the worked example `analysis.method` is swept, so `r` is a different function in each of the three conditions — an `aggregate` that saw only the table could hard-code one coefficient and would then report the same statistic under all three labels. Core passes the same `cfg` when it recomputes the metric on a resampled table, so the value and its interval are always the same statistic. This is the one place a template sees a condition; step code still doesn't, because `cfg` arrives already resolved (see [Using them in step code](#using-them-in-step-code)).

**A key `aggregate` returns that the step also recorded is rejected as it happens**, since `aggregated` has one place for that name and a column mean and a derived value are different numbers. Rename one, or drop the column once the template derives it — the worked example's `r` is safe because the step *returns* it rather than recording it, which lands it in [`per_repeat`](#the-unit-table-is-the-inference-base) where the two are deliberately visible side by side.

**One call per recording step, attributed to that step.** A pipeline can have several steps that call `io.record`, so there is no single unit table to hand over. Core calls `aggregate` once per step that recorded one, over that step's collapsed table, and files the result under that step — which is why the worked example's derived `r` appears at `aggregated.step03_analyze.r` rather than at the top of the condition. A template that only knows how to derive metrics from some tables returns `{}` for the rest.

`Param` carries type, default, constraints, and help text — so `init` renders the file with accurate inline comments, and `validate` enforces exactly what was documented. Adding a parameter in one place makes it appear in newly-initialized configs and become enforceable at once. It carries one thing that is **not** a constraint and so is not in [the constraint table](#templates-where-parameters-are-defined): [the credential a chosen value requires](#a-credential-can-belong-to-a-parameter-value), which constrains the environment a value may be used in rather than the value.

**The constraint vocabulary is closed**, because `parameter_spec` is the schema `validate` enforces and a spec whose vocabulary is open-ended can't be checked or rendered into a comment:

| Constraint | Applies to | Renders as |
|---|---|---|
| `choices=[...]` | any | `# choices: a \| b \| c` |
| `ge` · `gt` · `le` · `lt` | `int`, `float` | `# integer >= 2`, `# float in (0, 1)` |
| `pattern=r"..."` | `str` | `# matches ^[a-z0-9-]+$` |
| `item_type` · `min_items` · `max_items` | `list` | `# list of float, 2 to 5 items` |
| `nullable=True` | any | permits `null` beside the declared type |
| `help="..."` | any | the trailing comment, when no constraint claims it |

There is no `validator=` hook: a rule that needs code is a cross-field rule, and those belong in the template's [`validate`](#templates-where-parameters-are-defined), where the whole config is in scope and the error message can say what the rule was for.

**Types are `str`, `int`, `float`, `bool`, and `list`.** A list takes `item_type` and is checked element by element, because a parameter whose value is genuinely a list is ordinary — base rates to transport a predictive value to, a retry backoff schedule, a set of thresholds — and the alternatives are all worse than supporting it. Numbered scalars (`rate_1`, `rate_2`) hard-code the length into the schema; a comma-separated string defeats the type checking that is `parameter_spec`'s entire purpose. There is no `dict` type: a mapping is what nesting the dotted path already expresses.

```python
"report.prevalences":     Param(list, item_type=float, default=[0.01, 0.03]),
"request.backoff_secs":   Param(list, item_type=int,   default=[30, 120]),
```

**Three states, not two: a value, a default of `null`, and no default at all.**

| Declaration | Means | `init` writes |
|---|---|---|
| `Param(int, default=30)` | Optional, defaulted | `30` |
| `Param(str, default=None, nullable=True)` | Optional, and `null` is a legal value | `null` |
| `Param(str)` — no `default` | **Required.** You must supply a value | `""  # REQUIRED` |

Omitting `default` is what makes a parameter required, which is why `default=None` is not the way to spell it — `null` is a legal value for some parameters and the absence of one is a different claim. A `Param` declaring `default=None` without `nullable=True` is rejected when the template loads, rather than at the first config that leaves it alone. Nullability is load-bearing beyond this: [`sweep.ablate.remove`](#expansion-modes) sets a boolean to `false` or a nullable parameter to `null`, and `validate` needs to know which parameters those are.

Required parameters get the same treatment `metadata.description` does — materialized with an empty value and a `# REQUIRED` marker, so the file `init` produced is complete and fails validation until you fill it in, rather than being silently short a key. **The marker is what fails**: `validate` rejects a required parameter still holding its type's empty value, exactly as it rejects an empty `metadata.description`. The consequence is worth knowing before you declare one — an empty string can never be a legal value for a required `str`, because there is no way to distinguish the value you meant from the placeholder you didn't fill in. If empty is legitimate, the parameter has a default and isn't required.

### A credential can belong to a parameter value

[`required_env`](#secrets--credentials) is a template-level list, so it says what an experiment *type* always needs — and that is the wrong shape whenever the credential follows a choice. A sweep across model deployments, instrument vendors, or scoring services is a sweep across the things being authenticated to, and a static list has to either demand a key for a provider no condition selects or stay silent about one every condition needs. Neither is a check worth running.

**So a value can carry its own credential requirement, declared beside the choices it belongs to:**

```python
"llm.provider": Param(str, default="azure_openai",
                      choices=["azure_openai", "openai", "ollama"],
                      requires_env={"azure_openai": ["AZURE_OPENAI_API_KEY"],
                                    "openai":       ["OPENAI_API_KEY"],
                                    "ollama":       []}),
```

`validate` then checks **the union over the conditions the sweep actually resolves**, so the config above demands `AZURE_OPENAI_API_KEY` when a condition selects Azure and says nothing about it when none does. `[]` is how a value that needs no credential says so, and it is not the same as omitting the key.

**`init` renders the requirement into the `choices` comment, against every value rather than the one it wrote**, because [nothing ever writes back into a config](#the-one-config-file) and a comment describing the *current* value would be wrong the first time you edited it. Attaching each variable to its own choice keeps the comment true whatever the file holds, which is the property every other inline comment already has:

```yaml
  llm:
    provider: azure_openai          # choices: azure_openai (needs AZURE_OPENAI_API_KEY) | openai (needs OPENAI_API_KEY) | ollama
```

**`requires_env` needs `choices`, and the mapping must be total over them.** A credential requirement is only checkable if the set of values is closed, which is exactly what `choices` declares; and a partial mapping would leave "this value needs nothing" and "nobody wrote this value down" spelled identically, which is the [defaults-file problem](#there-is-no-separate-defaults-file) inside one dict. `validate` rejects a mapping with a missing or unknown key when the template loads, naming both sets — as [`E-TEMPLATE-LOAD`](#errors-validate-reports), which is that code's "raises while importing" shape and mints no identifier of its own, exactly as a `Param` declaring `default=None` without `nullable=True` already does. The consequence to plan for is real and is the point: **adding a choice breaks every template that declared `requires_env` until the new value states its requirement.** A new provider whose credentials nobody wrote down is a bug, and finding it at load beats finding it four hours into a sweep.

This is not a constraint, so it isn't in [the constraint table](#templates-where-parameters-are-defined) — it constrains the *environment* a value may be used in, not the value. It's the same boundary [`apparatus_facts`](#the-apparatus-core-can-only-observe) sits on, read from the other side: the provider is something you decide, so it's a `Param`, and what that decision requires travels with it rather than with the template that happens to offer the choice.

---

## Sweeps and repeats

Varying a parameter across a grid, and repeating each condition for statistical reporting, are what experiments *are*. They belong in core, not in a plugin — every field does both, and neither has anything to do with any particular domain.

### Declaring them

`parameters` holds base values. `sweep` says what varies. `replication` says how each condition repeats.

```yaml
parameters:
  analysis:
    method: pearson
    min_samples: 30

sweep:
  grid:                                  # cartesian product over dotted paths
    analysis.method: [pearson, spearman]
    analysis.min_samples: [30, 50]

replication:
  repeats:
    - {kind: seed, n: 5}
```

That's 4 conditions × 5 repeats = 20 executions of the pipeline.

### Expansion modes

Six modes, each covering a distinct experimental pattern. They compose: the final condition set is the product of every axis-shaped mode present — `grid`, `paired`, `sample`, `groups` — with the declared `baseline` prepended as condition `00`.

`ablate` is the one mode that does not multiply, because it isn't an axis. It emits `n` conditions, each one change away from the baseline, and it reads the baseline rather than re-emitting it — so a declared baseline is condition `00` exactly once, never both as `00_baseline` and as an ablate row. It therefore requires `sweep.baseline`, which `validate` checks.

Combining `ablate` with another *parameter* mode is rejected: the product of "vary one thing at a time" with a second parameter axis is no longer one thing at a time, and there is no defensible reading of what it would mean. `groups` is the exception, and the reason is the same reason it's the exception everywhere else — it varies no parameter. Crossing an ablation with a group axis leaves every condition exactly one parameter change from its arm's baseline; all that changes is which units it was measured on. So `ablate × groups` is permitted, and gives `(1 + n)` conditions per level:

```yaml
sweep:
  groups:
    - {by: cohort, levels: [derivation, validation]}
  baseline: {features.labs: true, features.notes: true}
  ablate:
    from: baseline
    remove: [features.labs, features.notes]
  # 2 levels × (1 baseline + 2 ablations) = 6 conditions:
  #   00_cohort=derivation__baseline   01_cohort=derivation__labs=false   …
  #   03_cohort=validation__baseline   …
```

**`expand` numbers this differently today, and the divergence is unresolved.** It emits every
baseline as one leading block and then the ablations — `00_cohort=derivation__baseline`,
`01_cohort=validation__baseline`, `02_cohort=derivation__labs=false`,
`03_cohort=derivation__notes=false`, `04_cohort=validation__labs=false`,
`05_cohort=validation__notes=false` — so a design written against the indices above looks for a
directory `03_cohort=validation__baseline` that is named `01_` instead. The labels, the conditions,
and every unit each one holds are the ones printed; only the indices differ, and nothing about a
result depends on them. The interleaved rule this section and [§ How artifacts are
organized](#how-artifacts-are-organized)' Index row both state is what a reader should design
against and is ill-defined once a *second* axis makes a cell's rows non-contiguous — which is why
the numbering is stated here rather than quietly changed to match the tool, and why picking one is
a design decision nobody has taken. Address a baseline by its label, never by its index.

That's "which features matter, in each of two cohorts" — an ordinary design, and expressing it as two configs would give up the shared allocation, the shared seed list, and the single `run.yaml` that make the arms comparable in the first place. The baseline becomes one condition per level rather than one per run, which is the honest reading: there is no single reference condition when the reference cohort differs. `sweep.baseline` may not fix a level of the group axis, here or anywhere else — the arms are peers — and this composition is the shape where the refusal bites hardest: a fixed group axis expands over nothing, so the crossed ablation has one cell and every other level is executed by no condition at all. `validate` rejects it as `E-SWEEP-ABLATE-BASELINE-GROUP`; the plain product's own refusal is `E-SWEEP-BASELINE-GROUP`, described under `baseline` below.

**`grid` — cartesian product.** The default. Every combination of every listed value.

**`paired` — coupled assignments.** When parameters must move together rather than combinatorially, a list of dicts is treated as a single axis:

```yaml
sweep:
  grid:
    analysis.method: [pearson, spearman]
  paired:                                # 2 settings, NOT 2×2
    - {analysis.min_samples: 30, analysis.confidence: 0.95}
    - {analysis.min_samples: 50, analysis.confidence: 0.99}
  # grid × paired = 2 × 2 = 4 conditions
```

**`ablate` — one change at a time.** "Baseline, then remove each component individually" is `1 + n` conditions, not `2^n`. Writing that as `grid` is exponentially wrong; writing it as `paired` means hand-maintaining every row:

```yaml
sweep:
  ablate:
    from: baseline                       # start from the baseline condition below
    remove:                              # one condition per entry, each with ONE change
      - features.demographics
      - features.labs
      - features.notes
  # 00_baseline (from `baseline`) + 3 ablations = 4 conditions
```

`remove` sets a boolean parameter to `false` or a nullable one to `null`. Use `override` for non-boolean one-at-a-time variation:

```yaml
  ablate:
    override:
      - {analysis.method: spearman}
      - {analysis.min_samples: 10}
```

**`sample` — search instead of enumerate.** For continuous ranges where exhaustive enumeration is meaningless:

```yaml
sweep:
  sample:
    n: 50
    method: sobol                        # sobol | latin_hypercube | random
    seed: auto                           # auto (the design digest) or a pinned integer;
                                         #   recorded in sweep.yaml either way
    ranges:                              # uniform | int_uniform | log_uniform
      analysis.confidence: {uniform: [0.80, 0.99]}
      analysis.min_samples: {int_uniform: [10, 200]}
```

Sampling is deterministic given its seed, so `sweep.yaml` records both the seed and the fully realized condition list — a reader never has to re-derive the design, and `reproduce` regenerates the same conditions.

**`groups` — comparing arms rather than parameters.** Every mode above varies a *parameter*, which covers designs where the difference is something the pipeline does. In a parallel-arm trial the difference is something that happened to the units: the patients in one arm took the drug. There is no parameter to sweep, and forcing one would be a fiction:

```yaml
sweep:
  groups:
    - by: arm                            # names the axis; levels become the condition labels
      levels: [control, treatment]
  # 2 conditions: 00_arm=control, 01_arm=treatment
```

`groups` is a **list**, always — one axis is a list of one. Two spellings for one concept is the drift this project exists to prevent, so there is no mapping shorthand.

A group level is a *set of units*, resolved from [`data.units`](#allocation-within-subjects-or-between-subjects): core assigns them when `allocation: between` with `assign.method: random` or `blocked`, and reads an existing column when `by_attribute`. `io.units` then yields that level's units, and nothing else about the condition changes. (See [§ Allocation](#allocation-within-subjects-or-between-subjects) for what each method does.)

So two conditions on a group axis can share a `parameters_hash` — and that's correct, not a degenerate case. Identical code and identical parameters over two arms of units is exactly the claim a trial makes, and the three hashes say so precisely: same code, same parameters, different units. The design cell is recorded in `results.conditions[i].values` (`{arm: treatment}`) and the realized membership in `allocation.json`.

**The arms of a group axis are peers, and `sweep.baseline` may not fix one of them** — not `{arm: control}`, not on any axis in the list, whatever else the sweep declares. The reason is what the expansion would otherwise do: the baseline row and the axis's own product row are the same cell, so `control` is rendered *twice* — once as `00_baseline` and once as `01_arm=control` — and the two conditions hold the same units and the same parameters, with directories identical at every artifact. That is [*two identical measurements reported as two arms*](experimental-designs.md#mistakes-core-prevents), which is why it is refused (`E-SWEEP-BASELINE-GROUP`, and `E-SWEEP-ABLATE-BASELINE-GROUP` where `ablate` is declared) rather than resolved by suppressing one of the rows. A baseline that fixes only *parameter* paths stays legal beside a group axis and is the shape to write: it expands over the axis, giving every arm its own reference.

What a control arm actually designates is a comparison, and a comparison between two arms is a [`statistics.contrasts`](#contrasts-claims-that-arent-condition-vs-baseline) entry naming both conditions by label — `of: arm=treatment`, `against: arm=control` — which says the same thing without claiming one arm is the reference for the whole run. **This build refuses to compute that delta** (`E-DATA-ALLOCATION-CONTRAST`, temporary — see [§ Allocation](#allocation-within-subjects-or-between-subjects)): the two sides hold disjoint units, and no unpaired construction exists yet. Until it does, the arm-versus-arm difference is an `Estimate` returned by a `summary` step, or two runs joined in a `study`.

Group axes compose with parameter axes like any other mode, which is how "each arm analyzed three ways" is expressed:

```yaml
sweep:
  groups:
    - {by: arm, levels: [control, treatment]}
  grid:
    analysis.method: [pearson, spearman]
  # groups × grid = 2 × 2 = 4 conditions
```

**Group axes also cross each other**, on the same rule and for the same reason parameter axes do. A between-subjects factorial whose factors are both properties of the units — sex × arm, site × cohort, strain × treatment — is two axes in the list, and the conditions are their product:

```yaml
sweep:
  groups:
    - {by: sex, levels: [f, m]}
    - {by: arm, levels: [control, treatment]}
  # 2 × 2 = 4 cells: 00_sex=f__arm=control, 01_sex=f__arm=treatment, …

data:
  units:
    allocation: between
    assign:
      sex: {method: by_attribute}          # `from` defaults to the axis name
      arm:
        method: random
        stratify_by: [site, sex]           # balance arm within sex
        ratio: {control: 1, treatment: 1}
        seed: auto
```

**Axes resolve in declaration order, and `stratify_by` may name a group axis declared before it.** That one rule is what makes every crossed case fall out of machinery core already has, rather than needing a joint-allocation mode of its own:

| The design | How it's written |
|---|---|
| Both factors already in the data | Two `by_attribute` axes; core assigns nothing |
| One randomized, one observed | Declare the observed axis first, and stratify the randomized one on it — which is how the design is actually run |
| Both randomized (a 2×2 factorial randomization) | Two `random` axes, the second stratifying on the first |

`ratio` is always keyed by its own axis's levels, so no cell tuple appears anywhere in the config, and forward-only stratification makes a cycle unrepresentable rather than something `validate` has to detect. What core still won't do is decompose the result: a crossed design reports each cell and its contrasts, and [main effects and interactions](experimental-designs.md#what-core-will-not-do-for-you) remain a `scope: "summary"` step — exactly as they are for a parameter `grid`.

Comparisons *across* a group axis are unpaired, since no unit appears in two levels — unless the levels are matched, in which case `cluster_by` on the matched-set identifier is what carries the dependence. See [experimental-designs.md § Matched case-control](experimental-designs.md#matched-case-control). Comparisons *within* a level, between two parameter settings applied to the same arm, remain paired: composing a group axis with a parameter axis doesn't make every contrast in the run unpaired. See [Allocation](#allocation-within-subjects-or-between-subjects).

**`baseline` — a designated reference.** Without one, every condition is a peer and `report` can only list them. With one, core computes deltas and effect sizes against it automatically. It fixes *parameter* paths and only those — a group axis's levels are peers, and a baseline naming one is refused (`E-SWEEP-BASELINE-GROUP`, above):

```yaml
sweep:
  baseline: {analysis.method: pearson, analysis.min_samples: 30}
  grid:
    analysis.method: [spearman, kendall]
```

The baseline is condition `00`, and `results.conditions[i].vs_baseline` carries the difference in each numeric metric, with a standardized effect size when the metric is a per-unit mean. Declaring one is optional but recommended: "the treated arm scored 0.12 higher (Cohen's d = 0.4)" is the sentence a paper needs, and it can't be produced from an unlabeled set of peers.

**With more than one axis present, how many baseline conditions there are follows from how many of them the baseline fixes.** Two cases, one rule, and neither a default the other overrides:

| `sweep.baseline` | Baseline conditions | Each `vs_baseline` targets |
|---|---|---|
| A value on every axis — `{analysis.method: pearson, analysis.min_samples: 30}`, over a grid sweeping both | One, condition `00` | That single condition. A contrast differing on two axes at once is marked [`confounded: true`](#allocation-within-subjects-or-between-subjects) |
| A value on some axes — `{analysis.method: pearson}`, over a grid sweeping `analysis.method` and `data.sex`, so `data.sex` is left free | One per cell of the unfixed axes — `sex=f__baseline` and `sex=m__baseline` | Its own cell's baseline: `method=spearman__sex=f` compares against `sex=f__baseline`, resolved by matching the free axes' values rather than by position |

**The rule underneath both is that the baseline expands over whichever axes it doesn't fix** — group axes and parameter axes alike. A group axis is always on the unfixed side, since a baseline may not fix one at all, so a design carrying one is always in the second row. That row is the one to design around anyway, because it's the row where nothing is confounded: fix the factor you're measuring, leave the axes you're stratifying over free, and every contrast differs in exactly one place.

**On that unfixed side the expansion doesn't distinguish group axes from parameter axes, because a design that treats an axis as a stratum wants a reference per stratum either way.** Leaving an observed `sex` axis free while the factor under test is fixed gives the per-subgroup contrasts a subgroup report wants. Fixing the prompt under test and leaving `llm.model` free gives the per-deployment contrasts a benchmark across deployments wants — the same shape, and the second axis is a nuisance axis in both, whether its levels are sets of units or parameter values. Expanding over parameter axes alone would give the benchmark one reference deployment and mark every other deployment's contrast confounded, which is the correct verdict on a contrast nobody wanted to form and the wrong answer to the question being asked.

`ablate × groups` always lands in the second row, since `validate` rejects a baseline that fixes a group level (`E-SWEEP-ABLATE-BASELINE-GROUP` where `ablate` is declared): an ablation is one change from *its own cell's* full model, and there is no single reference condition when the reference cohort differs. Plain `ablate` lands in the first, because it isn't an axis and the baseline fixes every parameter it varies from — so there is one baseline, condition `00`, exactly as the mode's own description above says. Prefer the second row whenever the levels are peers: two cohorts, two sites, a derivation and a validation set.

Baseline conditions are references rather than comparisons, so they never count as one: six conditions under two per-arm baselines are four comparisons in the [correction family](#sweeps-and-repeats), not five.

### Repeat kinds

`replication.repeats` is a list, because "repeat" isn't one thing — and the kinds differ in what they vary *and* in how they must be aggregated. Treating them alike is a statistical error, not a stylistic one.

| Kind | Varies | Aggregation core applies |
|---|---|---|
| `seed` | RNG state only | Averaged per unit; dispersion reported as `repeat_spread` |
| `batch` | *when* — nothing the pipeline declares. Re-measures every condition at a separated time, so drift in the [apparatus](#the-apparatus-core-can-only-observe) shows up as dispersion instead of as a condition effect | Averaged per unit, exactly as `seed`; dispersion reported as `repeat_spread` |
| `fold` | data partition — k-fold, stratified, or leave-one-out via `k: all`; cluster-respecting when [`cluster_by`](#clustered-units) is declared; refused rather than drawn beside `allocation: between` or a non-empty `sweep.groups` — see [A fixed holdout split](#a-fixed-holdout-split) | Per-unit values concatenated across folds — each unit is tested once per fold sweep |

Each kind takes its own fields, and only these:

| Kind | Fields |
|---|---|
| `seed` | `n` (how many), or `seeds: [17, 42, …]` for specific values |
| `batch` | `n` (how many). Nothing else — a batch has no parameter of its own, which is the point |
| `fold` | `k` — an integer ≥ 2, or `all` for leave-one-out — plus optional `stratify_by` |

**`k: all` is how leave-one-out is spelled.** Writing `k: 240` would work arithmetically and is still the wrong thing to type: it hard-codes a count the config doesn't own, so the file silently stops meaning leave-one-out the moment the cohort gains a unit. `all` means "as many folds as there are things to leave out," and with [`cluster_by`](#clustered-units) declared that's the cluster count, making it leave-one-*cluster*-out — the only reading consistent with clusters being indivisible.

Two things to expect from it. Each execution's test partition is a single unit, so `n: {resolved: 1, completed: 1}` per execution and a step's returned metrics are near-meaningless individually — the concatenated per-unit table is the whole point, and a metric that only exists as a step-returned scalar gets nothing useful out of leave-one-out. Under [`cluster_by`](#clustered-units) the partition is a whole cluster instead, so `n` is that cluster's size, and everything else in that sentence still holds. And the execution count is the number of things left out times everything else: 240 units × 3 conditions is 720 executions with 720 repeat directories, which is why `validate`'s [execution-count warning](#validation) and [`dry-run`](#before-you-spend-it) matter more here than anywhere else — while the same 240 units clustered into 20 animals is 60.

**Three kinds, because a repeat is an execution.** A repeat re-runs the pipeline, so the only things that can be a repeat are things that change what the pipeline computes. There are three: the RNG state, which units it sees, and the state of the apparatus it measures through. Resampling, permutation, technical replication, and a fixed holdout all *look* like repeats and aren't — see [What isn't a repeat](#what-isnt-a-repeat).

The third arrived late and for a reason. While the only external state core recorded was a lockfile, "the apparatus drifted" wasn't a claim this tool could make, and a level expressing it would have been a count with a story attached. Now that an [apparatus is probed and recorded per condition](#the-apparatus-core-can-only-observe), the axis along which its drift is measured is nameable, so it gets a name.

**No repeat kind sets `n`.** `n` counts units, always — see [The unit table is the inference base](#the-unit-table-is-the-inference-base). Repeats say how many times the pipeline ran; they never say how many things the claim generalizes over, and conflating the two is how a five-seed run comes to report an interval that looks like evidence about a cohort.

#### A `batch` says *when*, not *what*

Every other repeat kind varies something core hands the pipeline — a seed, a partition. A `batch` varies nothing at all. It re-executes every condition later, and what changes is whatever changed outside: a service under different load, an instrument that warmed up, a model deployment quietly re-tuned. Three properties follow from that, and none of them is optional:

**`batch` and the apparatus gate answer different halves of one question.** The [gate](#the-apparatus-core-can-only-observe) catches a *declared* change of identity — a new revision, a new calibration — and fails the run, because two identities are not one dataset. A `batch` level measures the variation that remains when the identity held still, which is the part no gate can catch and the only part an interval can describe. Running blocks without recording the apparatus leaves drift unattributable; recording the apparatus without blocks leaves it unmeasured.

**Batches execute in order, and `order: randomized` shuffles *within* one.** A batch is a position in time, so shuffling batches against each other would destroy the thing being declared. Core therefore fixes the outer batch order and randomizes the (condition, inner-repeat) pairs inside each — which is also the design an operator wants: every condition met once per batch, in an order that doesn't confound it with position. The realized order and each execution's `started_at` land in `run.yaml`, so "were the batches actually separated?" is answerable from the record rather than from someone's memory. Core does not schedule the separation — it has no wall clock to enforce and inserting one would be a tool deciding when your instrument is free.

**A deterministic pipeline makes a `batch` level pointless, and [`W-REPL-DETERMINISTIC`](#warnings-core-reports) says so.** Under a fully deterministic pipeline a `batch` level re-computes the same answer *n* times, and its `repeat_spread` is a row of zeros that cost you *n* times the compute. That's a declaration-level check, so core can make it before anything runs: it compares the declared kind against the declared attribute, read off the step classes it has [already imported to derive the plan](#generators). Reading a class attribute is not reading a step's body, which core [still never does](design-principles.md#greenfield-only) — so a step that is nondeterministic in fact and silent about it draws the warning anyway, and the fix is the declaration.

```yaml
replication:
  repeats:
    - {kind: batch, n: 5}                # outer: five separated blocks
    - {kind: seed, n: 3}                 # inner: three seeds within each
  order: randomized                      # shuffles condition × seed inside each batch
  rationale: "Five blocks at least a day apart; the deployment is probed before each."
```

Repeat directories read `batch03_seed42`, and `repeat_spread` reports one entry per level, outer to inner — so how much the *world* moved and how much the *RNG* moved are two numbers rather than one average of both:

```yaml
repeat_spread:
  - {std: 0.019, n: 5, kind: batch}
  - {std: 0.004, n: 3, kind: seed}
```

That contrast is the whole reason the kind exists. Reported as a single `kind: seed` figure, those two would have been indistinguishable, and the larger of them mislabelled as randomness the tool controls.

#### What isn't a repeat

Four things that a naive model puts on the repeat axis belong elsewhere, and putting them there is what makes them affordable and correct.

**Resampling and permutation are statistics over the unit table.** `{kind: bootstrap, n: 2000}` would mean two thousand full executions of the pipeline, each with its own condition directory and artifact set — for the documented 15-execution example, roughly 8,500 artifacts to compute an interval conventionally obtained by resampling a table that already exists. So they're declared under `statistics` and computed after the run:

```yaml
statistics:
  resample: {method: bootstrap, n: 2000}          # percentile CIs over units
  null_test: {method: permutation, n: 5000, shuffle: label}
```

Both operate on `units.parquet`, resampling or relabelling it and recomputing the metric — which core can do only for a metric it knows how to compute, so this needs a per-unit column or a template [`aggregate(units, cfg)`](#templates-where-parameters-are-defined). Every declared `attributes` value is carried onto that table beside whatever the step recorded, which is what lets `shuffle` name an attribute — `label`, `arm`, `status` — and have it be a column the metric is actually computed from. A step is free to record a column of the same name, and core rejects that collision [as the step records it](#validation) rather than deciding which one the shuffle meant. The permutation test compares the null it builds against the value the actual run produced; a design in which every execution is permuted has no unpermuted value to test, which is one more way the repeat axis was the wrong home for it.

**What `null_test` tests depends on whether `shuffle` names a design axis.** It relabels units and recomputes the metric, so the question it answers is set by what that label does in the design:

| `shuffle` names | The null it builds | Where the p-value lands |
|---|---|---|
| An ordinary unit attribute | This condition's metric, against a world where the label carries no information | One per condition, beside that condition's estimate |
| A [`groups`](#expansion-modes) axis attribute | That axis's contrast, against a world where its membership carries no information — permuted within cells of every *other* group axis, so a cross isn't destroyed | On the contrast, in `vs_baseline` |

```yaml
aggregated:                                    # shuffle names an ordinary attribute
  step03_screen:
    prob: {value: 0.71, basis: units, method: t_over_units, ci95: [0.66, 0.76],
           p_value: 0.0004, p_value_corrected: 0.0028,
           null_test: {method: permutation, n: 5000, shuffle: label}}
```

The second row isn't an exception to the first so much as its consequence. Permuting an attribute that *defines* the conditions moves units between them, so the quantity that changes under the null is the between-arm difference rather than any one arm's estimate — there is no within-condition permutation available, because the attribute is constant inside each condition by construction. That is also the test a parallel-arm trial and a [matched case-control](experimental-designs.md#matched-case-control) study are actually asking for, and it inherits the level rule below: within clusters when the attribute varies inside one, whole clusters when it doesn't.

**A *parameter*-axis contrast stays out of reach.** Two conditions differing only on `analysis.method` were computed from the same units, so the null for their paired difference is a per-unit sign flip rather than a relabelling, and `shuffle` names an attribute, which can't express that. That contrast's evidence is its [interval and corrected interval](#sweeps-and-repeats), which is the form it's reported in anyway.

What counts as one draw is *rows* by default and *clusters* when [`cluster_by`](#clustered-units) is declared — a bootstrap over rows of clustered data reports an interval too narrow to believe, and a permutation over rows destroys the matching a matched design rests on. See [Clustered units](#clustered-units) for both rules.

**Technical replication is a property of the input, not of execution.** Re-running an identical step on identical inputs under the same seed produces an identical answer, so averaging three such executions is a no-op. The three reads of a sample are not three runs of anything — they're three measurement rows sharing a sample identity, and that's declared where units are resolved:

```yaml
data:
  units:
    from: reads.csv
    key: sample_id
    measurements: {by: read_id, collapse: mean}   # rows sharing a key are technical replicates
```

`collapse` is `mean`, `median`, or `sum` for numeric columns and `first` or `mode` for the rest — `first` meaning the earliest row in [resolution order](#where-units-come-from), and `mode` breaking a tie the same way, by whichever tied value appeared first. `collapse` may be a per-column map — `collapse: {intensity: mean, batch: first}` — when one rule doesn't fit every column. A single rule applies to every collapsed column, so `validate` rejects `mean` over a `site` string rather than coercing it: the alternative is a silently dropped column or a meaningless number, and neither is something to discover after the run. Attributes constant within a key collapse to that value with no rule needed.

Rows sharing a `key` are collapsed to one unit at resolution, before any step sees them, and `technical_n` is reported for transparency — as `{min, max, median}` rather than a single number, because real files are uneven and a bare `technical_n: 3` would be a claim of balance nobody checked. It sits beside each metric's `n`, and appears only where the input actually carried replicates: a run whose *step* does the measuring has one input row per unit, and reporting `{min: 1, max: 1, median: 1}` there would be a claim of no replication beside a `measurements.parquet` full of it. The counts of a step-measured collapse are in that file rather than in `technical_n`. It is withheld a second way, independent of whether the input carried replicates: under a [group axis](#expansion-modes) or a `statistics.report_by` level, `technical_n` is a whole-roster figure — `{min, max, median}` over every unit's collapse, not this arm's or this stratum's own — so it does not appear beside either one's `n` even when the whole roster did carry replicates. Copying it down would state a spread nobody computed over that subset, the same reason a `report_by` level carries no `repeat_spread` either. A unit measured once and a unit measured five times contribute equally to `n` after collapsing, which is worth being able to see. When the pipeline does the measuring rather than the input carrying it, a step names the measurement — `io.record(unit.key, values, measurement=read_id)` — and core collapses the same way, under the same `collapse` rule. That argument is what keeps the two cases apart, and it isn't optional politeness: without it, a second row for the same unit is a resumed retry to be deduplicated — [first write wins](#resuming) — and with it a second measurement to be averaged, and nothing in the row itself distinguishes them. Core raises if a step passes `measurement=` while `data.units.measurements` is undeclared, since there would be no rule to collapse under. It raises too if one unit arrives by both paths within one execution — measured and also recorded plainly, in either order — because the collapsed row and the plain one are the same row, so whichever call came first would decide whether the declared `collapse` rule applied at all; a *second measurement* of that unit is the one thing `measurement=` exists to allow. Either path, technical replicates cannot reach `n`, because they were gone before `n` was counted.

**A recorded gap, not yet closed:** [`W-STATS-REPORTBY-THIN`](#warnings-core-reports) counts a `statistics.report_by` level against the roster `validate` can already see — the whole roster, not a group axis's own arm. A design declaring both would have every arm's predicted stratum size overstated by the same whole-roster figure, the validate-time twin of the run-time gap `technical_n` just closed above. **Reachable now**: a declared group axis is no longer refused wholesale at `validate`, so a config combining `sweep.groups` with `statistics.report_by` constructs this case for real rather than merely being imagined — recorded in `docs/superpowers/spec-defects.md` as a live gap rather than a latent one.

A **technical replicate** is the same sample measured three times; a **biological replicate** is three independent samples. Only the second is evidence about the population, and counting technical replicates as `n` is one of the most common ways a result is overstated.

**Biological replicates aren't a repeat kind either** — they're units, which is exactly what the model already says: independent samples are independent rows in your unit table.

**A train/test holdout is a partition, not a repetition.** It looks like `fold` with `k` of one, and the resemblance is why it gets misfiled: both hand a step a training list and a test list. But a repeat level multiplies executions, and a holdout is drawn once and fixed for the run — `{kind: holdout, n: 1}` would be a repeat that never repeats, and a second one would be incoherent rather than merely wasteful. It belongs with the other declarations that divide units without re-running anything, so it's [`data.units.holdout`](#a-fixed-holdout-split).

`validate` rejects `{kind: biological}`, `{kind: technical}`, `{kind: bootstrap}`, `{kind: permutation}`, and `{kind: holdout}` by name, each pointing at where the thing actually goes. None of them is a [`batch`](#a-batch-says-when-not-what) either: a batch re-executes the pipeline against a world that may have moved, where all five of these re-derive something from data that already exists.

`n` is reported explicitly rather than left to inference, and it never collapses to a single number. (Every metric-block example in this document orders its keys for readability — `value` and `basis` first, an interval last — which is not the literal order `run.yaml` emits them in; key order is not part of the contract, and a reader comparing an example against a real file should match by key name.)

```yaml
r:
  value: 0.607
  basis: units                                 # what the interval is over
  n: {resolved: 240, completed: 228, failed: 12}
  technical_n: {min: 2, max: 3, median: 3}     # collapsed, shown for transparency
  repeat_spread: {std: 0.014, n: 5, kind: seed}   # how much the pipeline moved
  ci95: [0.517, 0.683]
  method: percentile_over_units
  resample_draws: 2000                         # how many draws the interval rests on
```

That block is the worked example's own, whose `statistics` declares no `resample` — which is why it carries no `resample` sibling. A run that *does* declare one carries the same shape with one more key, illustrated here rather than in the worked example itself, so the worked example's config and its numbers stay exactly what they are above. The values below are illustrative — a different, unnamed project, not a variant of `cohort-pilot` and not checked against any synthetic table the way the worked example's own numbers are:

```yaml
mean_pred:                                       # a derived metric; statistics.resample declared
  value: 0.183
  basis: units
  n: {resolved: 40, completed: 40, failed: 0}
  ci95: [0.091, 0.276]
  method: percentile_over_units
  resample: {method: bootstrap, n: 500, stratify_by: [cohort]}  # resolved, not declared verbatim
  resample_draws: 500                            # every draw survived this time
```

`resample.n` is what was *requested*; `resample_draws` beside it is what the interval actually *rests on* — the same figure here because no draw was degenerate, but they answer different questions and a run where one differs from the other is exactly the one [`W-STATS-RESAMPLE-THIN`](#warnings-core-reports) exists to flag. `stratify_by` reads back as a list even where the config wrote a bare string, because the record resolves what the config abbreviates rather than echoing its shorthand.

The three-part `n` closes a reporting gap that otherwise goes unnoticed: when 12 of 240 units error out, a bare `n: 240` is wrong and a bare `n: 228` silently hides attrition. All three numbers are recorded — joined by `clusters` whenever [`cluster_by`](#clustered-units) makes the cluster the inferential draw, by `effective` whenever [`weight_by`](#weighted-samples) makes Kish's size the one the interval was computed at, and by `ineligible` whenever a step [skipped](#what-isnt-a-repeat) a unit, each present only when it applies so a design that never skips reads as it always did — `report` shows the completion rate, and `run` fails the whole run when failures exceed `limits.max_failed_fraction` — because at some level of dropout the complete-case result stops being interpretable, and finding that out after the run is worse than not having spent it.

**How core knows a unit failed** is worth stating, because core never inspects the body of a step. It counts: `resolved` is how many units that execution was *given*, `completed` is how many distinct *unit* keys reached `io.record` in it — measurements of one unit collapse before they are counted — `ineligible` is how many it was told to skip, and `failed` is what's left over. That's an *effect*, which is the only thing core checks — consistent with [greenfield only](design-principles.md#greenfield-only). Two consequences follow. A step that swallows an exception and moves to the next unit is recorded as a failure anyway, because the row is missing; and a step that raises out of its own loop aborts the execution, so the repeat is marked `failed` in `execution` rather than reported as complete with partial units — the run itself [carries on to the next execution](#what-status-means-and-when-a-run-keeps-going). A step that records nothing at all has `completed: 0`, which is a loud failure rather than a silent `n` of zero.

**Not producing a result and failing to produce one are different, so a step can say which.** A counterfactual that can't be constructed for a patient whose observed span is too short, an assay that doesn't apply to a sample type, a metric undefined for a unit with one observation — these are decided by the design in advance, and no amount of retrying changes them. Counting them as failures makes a healthy run look broken and puts [`limits.max_failed_fraction`](#validation) in charge of a number that mixes two unlike things:

```python
for unit in io.units:
    if unit.span_days < cfg.parameters.transform.min_span:
        io.skip(unit.key, "observed span too short to define a velocity")
        continue
    io.record(unit.key, {...})
```

```yaml
n: {resolved: 330, completed: 296, ineligible: 30, failed: 4}   # an arm most of the
                                                                #   cohort admits
```

`io.skip(unit_key, reason)` is a declaration, not an excuse: core takes the step's word for it exactly as it takes `io.record`'s, and both are recorded. The reason is stored per unit in [`ineligible.jsonl`](#the-per-unit-tables) beside the unit table, because *which* patients an arm could not be built for is cohort flow a report has to state, and a bare count doesn't carry it. `report` shows ineligibility per condition, so an arm that quietly lost a third of the roster is visible rather than absorbed.

Three consequences. **`max_failed_fraction` is over failures only** — a run whose arms differ in eligibility no longer trips a threshold meant for attrition. **`limits.max_ineligible_fraction` warns separately**, because an arm evaluable for a fifth of the cohort is a design problem rather than an execution one, and it's the same problem [`n_paired`](#contrasts-claims-that-arent-condition-vs-baseline) exists to keep out of a contrast. And **a skipped unit is decided, so a resumed step doesn't reconsider it**: `io.recorded_keys` holds every key this execution has settled — recorded or skipped — since its one purpose is telling a resumed step what not to redo.

Across repeats, a unit ineligible in **every** repeat it was handed to is ineligible for the condition. A unit ineligible in some and completed in others is counted as **failed**, not ineligible: eligibility is a property of the design, so a step that answered differently for the same unit twice has a bug, and reporting that as a design fact would hide it.

**`resolved` counts what the execution was handed, not the cohort.** This matters the moment a design narrows `io.units`, and getting it wrong would make correct runs look catastrophic. Under `{kind: fold, k: 10}` over 240 units, each execution is handed a 24-unit test partition, so a fold that records all 24 is `{resolved: 24, completed: 24, failed: 0}` — not 216 failures against a cohort it was never given. Under a [group axis](#expansion-modes) it's that arm's roster, ~120 rather than 240. `resolved` always equals `len(io.units)` for that execution, which is the only definition a step could be held to.

So three different `n`s exist, at three levels, and they answer different questions:

| Level | Where | Counts |
|---|---|---|
| Execution | `execution.conditions[i].steps.<step>.<repeat>.n` | The units *this* fold or arm was handed, how many it recorded, and how many it declared ineligible |
| Condition | `results.conditions[i].aggregated.<step>.<metric>.n` | The condition's collapsed table — the inference base for its interval |
| Run | `provenance.units.n` | Every unit the declaration resolved, before any narrowing |

The condition-level `n` is the one that appears beside a `ci95`, and it reconciles with the run level rather than restating it: under `fold`, each unit is tested exactly once per fold sweep, so concatenating ten 24-unit partitions gives one value per unit and the condition's `n` comes back to 240 resolved. Under a group axis it doesn't reconcile, and shouldn't — each arm's interval is over that arm's units, which is what makes it an arm-level estimate.

**A unit counts as completed for the condition only if it completed in every repeat it was handed to**, and ineligible only if it was skipped in all of them. Which repeats those are is decided by the kinds declared, so the rule is one sentence but never one number:

| Repeat structure | A unit is handed to | It counts as completed when |
|---|---|---|
| `seed` or `batch` levels only | Every repeat | It completed in all of them |
| A `fold` level | Exactly one fold per sweep | It completed in that fold |
| `fold` × `seed` | Every seed of its own fold | It completed in all of that fold's seeds |

The qualifier is load-bearing: intersecting over *every* repeat would report `completed: 0` for any design containing a fold, because no unit is ever in more than one of them. Intersecting over the repeats that were actually handed the unit is what makes the condition's `n` return to the full roster under cross-validation, as the three-level table above says it does, while still dropping a unit that failed the one fold it was in.

Failures don't have to line up across repeats — a unit can error under one seed and succeed under another, and in the worked example seed17 loses 9 units and seed42 loses 7, overlapping in 4, so 12 distinct units failed somewhere and the condition reports `completed: 228`. The intersection is the rule rather than the union because [§ Statistical reporting](#statistical-reporting) averages repeats per unit before computing any interval: a unit present in three of five seeds would otherwise enter the average on a different number of observations than its neighbours, which is a ragged table dressed as a rectangular one. Taking the intersection costs a few units and keeps every per-unit value comparable. `report` shows the per-repeat counts alongside, so a repeat that failed unusually many units is visible rather than absorbed into the condition's total.

**The failure fraction `run` enforces is against the run level.** A threshold checked per execution would fire on a small fold long before the cohort was in any trouble, and a threshold checked per condition would let a systematically broken fold hide inside nine healthy ones. Run-level is the number that decides whether the complete-case result is interpretable, so that's the one with a threshold on it. The fraction is **units that failed in at least one execution, over `provenance.units.n`** — distinct units on top, the whole resolved roster underneath. Counting failures instead of units would charge a cohort of 240 with 30 failures when one unit failed in every one of 30 executions, and dividing by the executions' summed `resolved` would move the denominator every time you added a fold. Distinct-over-roster is the only reading that means the same thing under `seed`, under `fold`, and under a group axis, which is what a threshold you set once has to do. It's evaluated as the run goes rather than at the end, because failures only accumulate: once the fraction is past the threshold no later execution can bring it back, so core stops there and the run is [`failed`](#what-status-means-and-when-a-run-keeps-going) — the one failure that ends a run rather than being absorbed into `partial`. Per-execution failures are still recorded and `report` surfaces any execution whose completion rate is an outlier against its condition — an early-stopping signal without a second threshold to tune.

**`repeat_spread` names one level, so nested repeats report a list.** With a single `seed` level it's the mapping shown above. With `fold × seed` there are two questions and they have different answers — how much the RNG moved the answer within a fold, and how much the partition moved it across folds — so core reports one entry per declared level, outer to inner, each recomputing the metric over that level's slice:

```yaml
repeat_spread:
  - {std: 0.019, n: 10, kind: fold}
  - {std: 0.014, n: 3, kind: seed}
```

Collapsing them into one number would average two different sources of variation and label the result with whichever kind was written first.

`repeat_spread` sits beside the interval rather than inside it on purpose. It answers a real question — did this pipeline give the same answer five times? — and it is not a measure of how precisely the cohort was estimated. Keeping both visible, and labelling which is which, is cheaper than expecting a reader to remember the difference.

```yaml
replication:
  repeats:
    - {kind: fold, k: 10, stratify_by: label}   # outer: 10 folds
    - {kind: seed, n: 3}                        # inner: 3 seeds per fold
  order: as_declared                            # as_declared | randomized
  rationale: "10-fold CV, 3 seeds per fold, ML benchmarking convention"

statistics:
  correction: holm                              # none | bonferroni | holm | fdr_bh
```

`order: randomized` shuffles the execution order of (condition, repeat) pairs under a recorded seed. For anything touching an instrument, a plate, or a service whose behaviour drifts over hours, running conditions in index order confounds the comparison with time; randomizing costs nothing and the realized order lands in `sweep.yaml` either way, along with each execution's `started_at` — and [`resume`](#resuming) reads it back rather than re-deriving it. A [`batch`](#a-batch-says-when-not-what) level is the exception that proves the rule: batches are positions in time, so they stay in order and the shuffle happens inside each one.

`statistics.correction` applies across the family of baseline comparisons in a sweep, and reporting that family uncorrected is how a sweep feature turns into a p-hacking feature. Corrected and raw intervals are both reported, so nothing is hidden — shown here for a six-condition sweep reporting three metrics per step, which is a wider family than the worked example's and so corrects further. The contrast shown is the strongest of its family, which is what `rank 1` means and what makes α/15 the level it gets:

```yaml
vs_baseline:
  step03_analyze:
    r: {delta: -0.169, basis: units, method: paired_percentile_over_units,
        ci95: [-0.213, -0.125],
        ci95_corrected: [-0.235, -0.103], correction: holm,
        correction_level: 0.0033,                    # α/15 — rank 1 of this family
        family_size: 15, family: {comparisons: 5, metrics: 3}}
```

**A corrected interval is an interval at a smaller α, and `correction_level` records which one**, because the three methods imply it differently and one of them doesn't imply it at all:

| `correction` | `ci95_corrected` | Also reports |
|---|---|---|
| `none` | absent | — |
| `bonferroni` | The interval at α/m, for a family of size *m* | — |
| `holm` (default) | The interval at α/(m−i+1), where *i* is this comparison's rank in the family — see below | `p_value_corrected` when a [`null_test`](#what-isnt-a-repeat) supplied a p-value |
| `fdr_bh` | **`null`** | `p_value_corrected`, Benjamini-Hochberg adjusted — so it needs p-values; see below |

**Size `resample.n` against the family this table implies, not against the 80-draw floor alone.** A corrected interval at level α/m needs `min_honest_draws(1 − α/m)` ≈ 80·m draws off the same pool a raw interval draws from, so a family of `m = comparisons × metrics` costs roughly that many times the uncorrected floor — 15 members, as the family above, wants on the order of 1200 draws, not 80. A hypothesis family is corrected separately, at its own declared count rather than at the sweep's `comparisons × metrics`, so a config declaring both sizes `resample.n` against whichever family's m is larger.

Holm's rank-implied level is the conventional companion to the procedure rather than a strictly simultaneous band, and calling it that is the honest description: it is what the step-down procedure tests each comparison at, so an interval excluding the threshold agrees with the procedure's verdict. It also means **the weakest comparison in a family is corrected by nothing** — at rank *m* the level is α itself — which the worked example shows: kendall's contrast carries far the stronger evidence, so spearman's is rank 2 of 2 and its corrected interval is its raw one. That is Holm behaving correctly, not a correction that failed to apply, and it is the property that makes Holm uniformly more powerful than Bonferroni. Benjamini-Hochberg has no interval that means anything of the kind — controlling a false discovery *rate* is a statement about a set, not a bound on any one comparison — so core reports the adjusted p-value and leaves `ci95_corrected` null rather than printing a number with no construction behind it. That asymmetry is deliberate and is the same standard the family count is held to below.

**Which rank, though, has to be decided by something every member has.** Holm is a p-value procedure, and this family often carries no p-values at all: a [`null_test` supplies one only where `shuffle` names an attribute](#what-isnt-a-repeat), which [a parameter-axis contrast can never be](#what-isnt-a-repeat) — the worked example's family is two of exactly that kind. So the ranking statistic is the one quantity every member is guaranteed to have, since [only metrics carrying an interval are counted](#sweeps-and-repeats): **the point estimate over half the raw `ci95` width, largest first.** It is monotone in the evidence each construction encodes and is defined whether the interval was t-based or percentile, which is what the p-value isn't. In the worked example that is 0.169 over 0.044 for kendall against 0.026 over 0.033 for spearman — 3.84 against 0.79 — giving the ranks above. Ties break by declaration order — the position the comparison and metric occupy in the config, an index assigned once as the family is built — so a rank is a function of the record rather than of an iteration order: a rank decides which α a member's corrected interval is built at, and an ordering that moved with a metric's name would change which interval got the tightest level the moment someone renamed a column. Ranking on a p-value where one exists and on this ratio elsewhere would leave the family ordered by two statistics, which is not an ordering.

**`fdr_bh` therefore needs a p-value it can't always get.** Declared over a family whose metrics carry none, it leaves every member with a `null` `ci95_corrected` and no `p_value_corrected` either — a correction declared and not applied, which is the state this section exists to prevent. So `validate` warns on the condition that decides it: **no comparison in the family will carry a p-value**, either because `statistics.null_test` is undeclared or because its `shuffle` reaches none of them. Use `holm` or `bonferroni`, whose corrections are interval-shaped, or declare the `null_test` that supplies the p-value.

Only metrics core corrects are counted — that is, [`basis: units`](#the-unit-table-is-the-inference-base) metrics, since a metric reported without an interval isn't a comparison anyone can read as significant. The family is the same set under every method, including `fdr_bh`, where what each member receives is an adjusted p-value rather than an interval. A [reported `Estimate`](#estimate-carries-your-interval-without-core-claiming-it) is excluded for a different reason: core never computed it, so it has nothing to correct and no standing to say the correction was applied. In the worked example that's 2 comparisons × 1 metric, so `family_size: 2`.

**A "comparison" is a baseline contrast or a [declared one](#contrasts-claims-that-arent-condition-vs-baseline)** — both put an interval in front of a reader, so both count. Reporting strata do not: a stratum describes rather than compares, and a subgroup claim you intend to test is a [hypothesis](#pre-registration), corrected in that family.

**The family is comparisons × metrics, not comparisons.** A six-condition sweep is five comparisons, but if each step reports three numeric metrics, a reader is being shown fifteen intervals and any of them can carry the paper. Counting only conditions would under-correct by the factor that actually varies between projects — and a tool that advertises corrected intervals while counting the family too small is worse than one that reports raw intervals honestly, because the number looks handled.

Two consequences worth knowing before you write the config. Every numeric metric a step reports is in the family whether you look at it or not, so a step that returns twelve diagnostics widens the correction on the one you care about; return diagnostics as per-unit columns, which are inputs rather than reported comparisons, or move them to a separate step. And `family` is reported broken out rather than as a single integer, so the count is auditable instead of asserted — `report` prints it, and a reviewer can check it against the table.

`hypotheses` are counted as their own family, separately from the exploratory sweep. A pre-registered confirmatory comparison shouldn't be penalized for the exploration that surrounded it, which is most of the point of declaring it in advance.

**Counted-iff-corrected applies to that family too, which decides what happens to a [summary-metric hypothesis](#a-hypothesis-may-name-a-summary-metric).** Its observation is a [reported `Estimate`](#estimate-carries-your-interval-without-core-claiming-it), so core has nothing to correct — and therefore does not count it. Core's hypothesis family is the confirmatory hypotheses whose observations it computed, which keeps `family_size` predictable from the config: you can see which metrics are per-condition and which are summary without running anything.

A design whose pre-registered family mixes the two therefore has *two* families, and only one of them is core's. Declare your own adjustment inside the `Estimate`'s `method`, where the number it applies to lives: `method: "one-sided BCa, 10000 draws, Bonferroni across 3 gates"`. Core then records three uncorrected `reported` verdicts and a `family_size` that doesn't pretend to cover them. Correcting them itself would mean adjusting an interval it has [already said](#estimate-carries-your-interval-without-core-claiming-it) it has no standing over, and silently absorbing them into the count would misstate the correction it *did* apply.

**`sample` conditions are not a comparison family, and are excluded.** The reasoning above holds wherever each condition is a comparison a reader might act on, which is what an enumerated sweep produces. A `sample` sweep isn't that: forty sobol draws over `drug.dose_mg` are forty points feeding one downstream curve, and nobody claims a finding about draw 17 against draw 1. Holm-adjusting thirty-nine such contrasts corrects a multiplicity no one is exposed to, and it would shrink every interval the curve is fitted through. So `family` counts conditions from `grid`, `paired`, `ablate`, and `groups`, and skips `sample`; `report` says so beside the table rather than leaving a reader to wonder why the count is smaller than the condition list.

That is also why `validate` doesn't warn about `correction: none` for a `sample`-only sweep — under the old counting rule, the config that was statistically right got warned at. `replication.rationale` is the place to say what you're doing with the draws, and for a design whose conclusion comes from a `scope: "summary"` fit, saying so is worth more than any correction core could apply to the conditions feeding it.

Two things this buys:

- **Correct statistics by construction.** Averaging across folds and averaging across seeds are different collapses, because a unit appears once per fold sweep and every time under a seed. Because the kind is declared, core picks the right one instead of flattening both.
- **Nesting.** A list expresses layered repeats — seeds within folds — which a single repeat count could not. Repeats compose outer-to-inner, so the example above is 30 executions per condition. This is repeated cross-validation, not nested: an inner loop that *selects* a setting for the outer one to evaluate is [adaptive](design-principles.md#what-core-does-not-promise) and belongs inside a step.

Comparison type is derived from [`data.units.allocation`](#units-the-thing-being-measured) and from which axes a contrast crosses, rather than declared here: two conditions differing only on parameter axes were evaluated on the same units, so that contrast is paired *unit by unit*; two conditions differing on any `groups` axis are independent samples, so it's unpaired. Deriving it removes the possibility of a config that declares `paired` over a design that isn't, and deriving it per contrast rather than per run is what keeps a composed `groups × grid` design from reporting its paired contrasts as unpaired — see [Allocation](#allocation-within-subjects-or-between-subjects) for the full table. Pairing is over units, never over repeats — matching seed17 against seed17 would cancel RNG variation, which is not the variation a comparison needs to account for.

`{kind: seed, n: 5}` with no explicit list derives seeds deterministically from the [design digest](#what-auto-derives-from); pass `seeds: [17, 42, ...]` for specific values. Either way the resolved list lands in `sweep.yaml`.

### Using them in step code

The elegant part is that **step code has no idea a sweep exists.** Core resolves each condition before the step runs, so `cfg.parameters` is already the fully-substituted parameter set for that condition:

```python
class Step(BaseStep):
    def run(self, cfg, io):
        # For condition 3, this is "spearman" — no sweep-awareness, no lookup, no indexing.
        result = analyze(cohort,
                         method=cfg.parameters.analysis.method,
                         min_samples=cfg.parameters.analysis.min_samples)
        io.write("scores.parquet", result.rows)
        return {"r": result.r}
```

A step written for a single-condition experiment works unchanged when someone later adds a sweep — sweeping is a config concern, not a code concern.

When a step genuinely needs its context — seeding a library, labeling a plot — it's available on the instance, since core constructs a fresh step per execution:

```python
class Step(BaseStep):
    def run(self, cfg, io):
        self.condition.index          # 2
        self.condition.values         # {"analysis.method": "spearman", "analysis.min_samples": 30}
        self.condition.label          # "method=spearman__min_samples=30"
        self.condition.is_baseline    # False

        self.rng                  # this execution's numpy.random.Generator — see "Randomness"
        self.repeat.label         # "fold03_seed42"
        self.repeat.seed          # 42  — the integer self.rng and the global streams came from
        self.repeat.index         # flat index of this execution within the condition
        self.repeat.levels        # [{kind: batch, i: 2, n: 5},
                                  #  {kind: fold, i: 2, k: 10, train: [...], test: [...]},
                                  #  {kind: seed, i: 1, seed: 42}]
```

`repeat.levels` is how a step gets what a repeat kind actually implies — `fold` supplies the train and test index split, `seed` the applied seed. Core computes them so every experiment doesn't reimplement k-fold, and so `run.yaml` can record exactly which units were in which partition.

**Which of those exist follows from the step's [scope](#step-scope), and the ones that don't raise rather than being `None`:**

| `scope` | `self.condition` | `self.repeat` |
|---|---|---|
| `"run"` | raises — executes once, before any condition | raises |
| `"condition"` | present | raises — repeats haven't happened yet |
| `"repeat"` | present | present |
| `"summary"` | raises — it runs across all of them, so no one condition is *its* condition | raises |

Raising rather than returning `None` is the same choice `cfg` makes: a step can assume what it's given is real, so there is no `if self.repeat is not None` to write. A step that wants to behave differently at different scopes is two steps. What it raises is a [`ContractError`](#errors-core-raises), like every other request core declines on a declaration.

**`self.rng` is not in that table, because it's present at every scope.** Core derives a seed for *every* execution, whether or not a repeat named one — see below.

### Randomness, and which stream a step should draw from

**Core derives one seed per execution and does two separate things with it**, and only one of them reaches your code reliably. The seed is the repeat's resolved seed where there is a repeat, and a [`derive_seed`](#a-step-that-partitions-needs-a-seed-and-derive_seed-is-where-it-comes-from) of the step's own name where there isn't — so a `"condition"`-scoped fit is as seeded as a `"repeat"`-scoped one, and none of the four scopes has a hole in it.

| | Is | Reaches |
|---|---|---|
| `self.rng` | A `numpy.random.Generator` built from that seed, at every scope | Whatever you draw from it |
| The global streams | `random.seed(...)` and `numpy.random.seed(...)`, applied from the same seed before `run` is called | Any code that draws from `random.*` or the legacy `numpy.random.*` functions — yours, or a library's |

**Draw from `self.rng`; the globals are there for libraries you don't control.** Seeding a process-global stream is the pattern [the next section argues against](#a-step-that-partitions-needs-a-seed-and-derive_seed-is-where-it-comes-from) — two draws sharing a stream correlate for no reason anyone chose — and that argument holds against core's own seeding as much as against yours. Core does it anyway because a third-party library that draws from the global stream is otherwise unseeded and there is no other way to reach it, which is the whole of the justification: it is a compatibility measure, not the stream your analysis should be built on.

**`numpy.random.seed` reaches the legacy global `RandomState` and nothing else.** A step that calls `numpy.random.default_rng()` gets a generator seeded from OS entropy, so a pipeline written the modern way is *unseeded* by a core that seeds the legacy global — which is exactly the failure `self.rng` exists to close. Take the generator core hands you rather than constructing one.

**A stream drawn from concurrently is order-dependent whatever kind it is.** [The parallelism worth having is inside a step](#one-execution-at-a-time-and-what-holds-the-run-directory), and a step issuing 440 requests at once cannot share one generator across them and stay repeatable — the interleaving decides who gets which draw. Give each worker its own: `self.rng.spawn(n)` where the NumPy version supports it, or a `derive_seed` named per worker where it doesn't. Core doesn't do this for you because it doesn't know how you divided the work, and a step that draws nothing concurrently shouldn't pay for the ceremony.

**`self.rng` is the execution's default stream; [`derive_seed`](#a-step-that-partitions-needs-a-seed-and-derive_seed-is-where-it-comes-from) is how you get a second one** — draw from the first until you need to name the second. Where there is no repeat that means `self.rng` is exactly `default_rng(self.derive_seed("<this step>"))`, so any purpose but that one lands on a stream of its own. It sits beside `self.condition` and `self.repeat` rather than in `io` because it is a fact about this execution rather than about where its artifacts go — but unlike them it never raises, since every execution has a seed and there is no scope at which it would have nothing to hand over.

### A step that partitions needs a seed, and `derive_seed` is where it comes from

Core's own randomness derives from a [design digest](#what-auto-derives-from) rather than from `parameters_hash`, so a fold boundary moves when the roster does and holds still when you edit an analysis parameter. A step doing its own partitioning wants exactly that, and [§ Cross-validation](experimental-designs.md#cross-validation) routes real work here — an inner hyperparameter search, an optimizer's train/dev division. So the same derivation is available:

```python
class FitStep(BaseStep):
    scope = "condition"

    def run(self, cfg, io):
        rng = random.Random(self.derive_seed("optimizer-dev-split"))
        ...
```

`derive_seed(purpose)` mixes the design digest, the resolved roster, and the string you pass, and returns an integer — one you hand to `random.Random`, to `numpy.random.default_rng`, or to any library that takes a seed. The `purpose` argument is not decoration: two partitions drawn in one step would otherwise share a stream and correlate for no reason anyone chose, and naming them keeps each independent — the same reason [`assign.seed`](#what-auto-derives-from) mixes in the axis name.

**It moves when the roster moves, and that is the point.** A seed declared as a template parameter is the other honest option, and it is the right one when you want a division frozen against a growing cohort — but it does *not* redraw when ten patients are added, while every partition core computes does. Pick deliberately: `derive_seed` to track the data, a pinned parameter to track the file. Whichever you use, write the realized division to an artifact — it was chosen inside the step, so the record is the only place it exists.

Available at every scope, because the digest is a property of the run rather than of an execution.

### Steps that need every condition

Comparing across a sweep is a step with a different *scope*, not a different kind of object — declare `scope = "summary"` and it runs once, after every condition and repeat, with read access across all of them. See [Step scope](#step-scope).

```python
class CompareMethods(BaseStep):
    scope = "summary"

    def run(self, cfg, io):
        for condition in io.conditions:                   # every resolved condition
            scores = io.read_condition(condition, "step03_analyze", "scores.parquet")
            ...
        io.write("comparison.csv", table)                 # lands in <run_dir>/summary/
        return {"best_method": "spearman"}
```

`io.conditions` yields `(index, label)` pairs, not bare labels — `read_condition` addresses a
condition by its index, and the label is what you put in a figure. An unswept run yields one pair
whose label is `None`, because there is no `key=value` body to render.

`cfg.parameters` in a summary step holds the *base* values, and reading a path the sweep varies [raises](#step-scope) rather than returning one — there's no condition whose value it would be, so there's no misleading pretense that one applies.

**What a summary step returns is recorded, not interpreted.** It lands in `results.summary`, with no `basis`, no place in the [correction family](#sweeps-and-repeats), and no recomputation on a resampled table — core didn't compute it and can't, which is the same reason a step-returned scalar is [`basis: repeats`](#the-unit-table-is-the-inference-base). Since factorial main effects, curve fits, conditional estimators, and mixed models are all routed here, that's worth being plain about: this scope is where core stops doing statistics and starts storing yours.

#### `Estimate` carries your interval without core claiming it

Storing a number is enough for a `best_method`; it isn't enough for a mixed model's effect and its confidence interval, which is the usual reason a summary step exists. (The step below is a mixed-model example rather than this document's worked pipeline, whose summary step returns a bare `best_method`.) Returned as a bare dict, that interval is a key core can't tell from any other — `report` won't render it as an interval, `study add` can't see the denominator it's over, and nothing in the record distinguishes it from one core computed from the unit table. So there is a shape for it:

```python
from publishable import BaseStep, Estimate

class Step(BaseStep):
    scope = "summary"

    def run(self, cfg, io):
        fit = mixed_model(io.read_condition(c, "step02_score", "units.parquet")
                          for c in io.conditions)
        return {
            "site_adjusted_delta": Estimate(
                value=0.031,
                ci95=[0.008, 0.055],
                n=612,                                    # what the interval is over
                method="mixed model, site random intercept, REML",
            ),
            "converged": True,                            # a bare value still works
        }
```

```yaml
results:
  summary:
    step03_site_model:
      site_adjusted_delta:
        value: 0.031
        reported: true                    # THE STEP computed this; core did not
        ci95: [0.008, 0.055]
        n: 612
        method: "mixed model, site random intercept, REML"
      converged: true
```

**`reported: true` is the whole mechanism, and it is an attribution rather than an endorsement.** Core stores the fields, `report` renders them as an interval, and [`study add`](#what-study-add-redacts) can check `n` against `limits.min_reported_n` — but core never recomputes the value, never resamples it, never corrects it, and never counts it in the family. Nothing about the refusal above changes; what changes is that a reader of `run.yaml` can now tell which intervals core derived from the per-unit table and which an author's own model asserted. Before this, both looked identical to every tool and to every reader, which was the worse of the two situations: the interval was already returnable, just unmarked.

Five rules, each a declaration check rather than a judgement about your statistics:

- **`method` is required whenever `ci95` is present.** An interval nobody labelled is unreadable, and core can enforce that a label exists without having any opinion on whether it's the right method. This is the same standard the [correction family](#sweeps-and-repeats) is held to — a number that looks handled and isn't is worse than an honest one.
- **`n` is optional but its absence is surfaced**, because an interval with no stated denominator is exactly the disclosure risk `min_reported_n` exists to catch.
- **`Estimate` is accepted at `scope: "summary"` only.** Elsewhere it would be a way to attach an interval to a per-execution return value, and `per_repeat` is *"exactly what the step returned"* — an interval per repeat is either a claim about that one execution or an accident, and neither belongs on the record. Intervals at every other scope come from the [unit table](#the-unit-table-is-the-inference-base), which is the refusal that makes the rest of this section work.
- `ci95` is exactly two numbers, in ascending order — refused as
  [`E-STEP-ESTIMATE-CI95`](#errors-core-raises). A bound read off a one-element or reversed pair
  would be the wrong bound, silently, and `evaluate_on: ci95_lower` indexes it.
- `value` is a number — refused as [`E-STEP-ESTIMATE-VALUE`](#errors-core-raises). An `Estimate` is
  the one interval core stores without computing, so the only thing it can check is the shape.

### How artifacts are organized

The output tree mirrors the experiment's structure: what varied, then which repeat, then which step.

```
<run_dir>/
├── run.yaml
├── sweep.yaml                                  # resolved conditions, repeat plan, seeds, fold membership,
│                                               #   realized execution order, design digest
├── allocation.json                             # realized arm assignment and holdout split; present when either is declared
├── executions.jsonl                            # one record per finished execution — what `resume` reads
├── manifest/input.json
├── environment/{uv.lock,pyproject.toml}
├── shared/
│   └── step01_load_cohort/cohort.parquet       # scope="run" — executed once
├── conditions/
│   ├── 00_baseline/                            # present only when `sweep.baseline` is declared
│   │   ├── step02_fit_model/model.pkl          # scope="condition" — once per condition
│   │   ├── seed17/
│   │   │   └── step03_analyze/units.parquet    # scope="repeat" — the per-unit table
│   │   ├── seed42/
│   │   └── ...
│   ├── 01_method=spearman/
│   └── 02_method=kendall/
└── summary/
    └── step04_compare_methods/comparison.csv   # scope="summary"
```

Five properties of this layout:

- **Depth follows scope.** A step's artifacts sit exactly as deep as the thing it varies with, so the path is a readable statement of what its output depends on. `shared/` output depends on nothing but the input; `conditions/01_.../` output depends on the condition; anything under a repeat directory depends on the repeat.

- **Condition directories are self-describing.** `01_method=spearman` tells you what it is without opening `sweep.yaml`. The numeric prefix gives stable ordering; the `key=value` body gives meaning. Labels derive from swept values only, so they stay stable across machines and reruns. A declared baseline is `00_baseline` — or one per cell, `00_cohort=derivation__baseline` and so on, when [another axis is present and the baseline leaves it free](#expansion-modes) — and a group level otherwise reads the same way as any other: `01_arm=treatment`.

  **The grammar is exact, because a label is also a selector.** A [hypothesis](#pre-registration) `compare.condition`, a [contrast](#contrasts-claims-that-arent-condition-vs-baseline)'s `of` and `against`, and a `report` filter all name conditions by the label's body — everything after the numeric prefix — so it has to be something you can write down without seeing the directory:

  | Rule | Is |
  |---|---|
  | Separator | `__` between axes, `=` between key and value, `_` after the numeric prefix. `00_sex=f__arm=control`, and a per-cell baseline is `00_cohort=derivation__baseline` |
  | Axis order | `groups` axes in declaration order, then parameter axes in declaration order. Never sorted — the config's order is the one you already read |
  | Key | The shortest suffix of the dotted path that is unique among the swept paths. `analysis.method` alone becomes `method`; swept beside `scoring.method` both keep a segment, as `analysis.method` and `scoring.method` |
  | Value | Rendered as written in the config — `true`/`false` for booleans, shortest round-trip form for floats. `validate` rejects a swept value whose rendering isn't `[A-Za-z0-9._+-]+`, since a label that needs escaping isn't a name anyone can type |
  | Index | Assigned over the expansion in order, each cell's baseline first *within its cell*. The **last** declared axis varies fastest, so the numbering reads like nested loops written in declaration order. With one baseline it is condition `00`; with [one per cell](#expansion-modes) they land at the head of each cell, which is why `ablate × groups` numbers `00_cohort=derivation__baseline` and `03_cohort=validation__baseline` rather than putting both baselines first. **`expand` does not do this today** — see the note under [§ Expansion modes](#expansion-modes)' `ablate × groups` example, which prints the same numbering this row states and which the tool also does not produce |

  A swept value renders as `[A-Za-z0-9._+-]+` and additionally may not contain `__`, which is the
  separator between one `key=value` component and the next. A value carrying it would produce a
  directory name that parses back into a different set of components than the one it was built from,
  and a label that cannot be read back is not a label.

  The index is the part to be careful with, because it's the part that moves: adding a level to any axis renumbers everything after it. That is why [`reuse_from`](#reuse_from-addresses-an-artifact-not-the-design-that-produced-it) addresses artifacts by name rather than by condition, and why a selector names the label's body rather than its prefix.

  `sample` conditions are the exception, and deliberately: a sobol draw of `dose_mg` has no short exact spelling, and rounding one into a directory name makes two distinct conditions collide at some precision. Sampled conditions are labelled `01_sample`, `02_sample`, with the drawn values in `sweep.yaml` and in `results.conditions[i].values`. Anything that selects a condition by name — a [hypothesis](#pre-registration) `compare.condition`, a `report` filter — is therefore selecting a discrete label, never a float you have to spell identically twice.
- **Repeat directories name their nesting.** A single repeat level is just `seed42`; nested repeats compose into `fold03_seed42`, which reads as the repeat it is rather than as an opaque index.
- **Repeat sits above step, not below.** A repeat is a full re-execution, so `seed17/step03_analyze/` reads correctly as "this repeat's version of this step." The inverse nesting would imply a step owns its repeats.
- **Degenerate levels collapse.** No sweep means no `conditions/` level; a single repeat means no repeat level. Browsing a simple experiment isn't cluttered by structure it doesn't have. Step code never notices, because it never constructs paths — `io` does. The active layout is recorded in `run.yaml` so tooling can rely on it.

  **A collapsed level drops out of the path and nothing takes its place**, so a condition-scoped step under no sweep writes to `<run_dir>/<step>/`, and a repeat-scoped step under no sweep and a single repeat writes there too. `shared/` and `summary/` are unaffected, because they name a *scope* rather than a level — a `"run"`-scoped step's artifacts are in `shared/` whether or not anything varied, which is what keeps "depth follows scope" readable in both layouts. Collapse isn't only cosmetic for the condition level: an unswept run varies nothing, so the [label grammar](#how-artifacts-are-organized) has no `key=value` body to render and there is no directory name for it to produce.

### Statistical reporting

Core aggregates *within* each condition and never pools across conditions, which would be meaningless. Two things decide what it computes, and they're independent: the **basis** of the metric — what the interval is an interval over — and the **kind** of each repeat.

#### The unit table is the inference base

The `n` in a confidence interval is a count of the things the claim generalizes over, and that's units, not executions. So core's intervals come from the per-unit table [`io.record`](#units-the-thing-being-measured) builds, and a metric gets a population interval only when core can compute it *from that table*:

| How the metric exists | `basis` | What core reports |
|---|---|---|
| A column in `units.parquet` | `units` | Mean over units, `n` = completed units, t-based `ci95` — cluster-robust when [`cluster_by`](#clustered-units) is declared |
| Derived from the table by the template's [`aggregate(units, cfg)`](#templates-where-parameters-are-defined) | `units` | The derived value, with a percentile `ci95` from resampling units — or clusters, when [`cluster_by`](#clustered-units) is declared |
| A unit table exists, but the metric isn't derivable from it | `repeats` | Point estimate and across-repeat spread — **no `ci95`** |
| No `data.units` at all | `repeats` | Mean, std, sem and a t-based `ci95` over repeats, labelled as such |

**An interval needs two units, and enough draws to place its bounds.** A metric whose completed
units number fewer than two reports `ci95: null` — there is no dispersion to estimate from one
observation, and a zero-width interval around it would read as certainty. A percentile construction
additionally reports `ci95: null` when the recorded `resample_draws` is below the floor its
confidence level needs, because a bound read off too few draws is a bound placed by the draw count
rather than by the data. `n` still reports the units, and `value` still reports the point estimate:
what is missing is the interval, not the metric.

Those last two rows differ, and `data.units` is the whole discriminator. With no unit table, the executions *are* the observations — a simulation's ten seeds are ten draws from the thing being studied — so an interval over repeats is the honest one, and core computes it. With a unit table present, an interval over repeats would be a claim about seeds standing in for a claim about units, so core refuses it rather than substituting the wrong denominator.

**Each of those constructions is a specific one, named here so two readers of one `run.yaml` agree on what they're holding.** `method` records it beside every value, so nothing below has to be inferred from the config:

| The interval | Is |
|---|---|
| `t_over_units` | Student's *t* on the per-unit values, df = completed units − 1 |
| `t_over_units_clustered` | Cluster-robust (CR1: the sandwich estimator with the standard finite-sample scaling), df = clusters − 1. The df is the part that bites — 10 animals give 9, not 299 |
| `percentile_over_units` | The 2.5th and 97.5th percentiles of the resampled distribution, over `statistics.resample.n` draws, defaulting to `bootstrap` at 2000 |
| `percentile_over_units_clustered` | The same percentiles, drawing whole clusters with replacement and pooling their units, so a replicate's row count varies; the number drawn per replicate is the cluster count |
| `weighted_t_over_units` | The [weighted](#weighted-samples) mean with the weighted variance, df from Kish's effective sample size rather than the row count |
| `weighted_t_over_units_clustered` | The weighted mean with a cluster-robust variance whose scores carry the weights; df = clusters − 1, **not** Kish's effective size, since `cluster_by` is what decides the draw |
| `t_over_repeats` | Student's *t* over the per-repeat values, df = repeats − 1. Only when [no `data.units` is declared](#the-unit-table-is-the-inference-base) |

**A contrast's interval is its own construction, never a difference of the two sides' intervals.** Differencing those would discard the covariance that [pairing exists to exploit](#allocation-within-subjects-or-between-subjects) — in the worked example it would report an interval several times wider than the delta itself — so the delta is computed from the per-unit differences, or from a resample that draws for both sides at once. Which of the four below applies follows from two facts: whether the contrast is [`paired`](#allocation-within-subjects-or-between-subjects), and whether the metric is a column or a derived one:

| The interval | Is |
|---|---|
| `paired_t_over_units` | Student's *t* on the per-unit differences over the [`n_paired`](#contrasts-claims-that-arent-condition-vs-baseline) intersection, df = `n_paired` − 1. A column metric, when no `resample` is declared |
| `paired_percentile_over_units` | The percentiles of the resampled difference, with **one draw over the [`n_paired`](#contrasts-claims-that-arent-condition-vs-baseline) intersection applied to both sides** — the same units are drawn for each, so what's resampled is the difference rather than two independent estimates. Drawing from each side's own completed set instead would leave a unit present on one side and absent from the other with no defined contribution, which is the case `n_paired` exists because it happens. Every derived metric, and a column metric under `resample` |
| `welch_t_over_units` | Welch's *t* on two independent condition means, df from Welch-Satterthwaite. The unpaired counterpart of the first: unequal variances are assumed rather than pooled, because two arms need be neither the same size nor the same spread |
| `unpaired_percentile_over_units` | The percentiles of the difference, resampling within each side independently. The unpaired counterpart of the second |

When [`cluster_by`](#clustered-units) is declared each takes a `_clustered` suffix and reads the cluster as the draw: the *t* forms are cluster-robust (CR1) with df = clusters − 1, over the differenced values when paired and over the arm-level ones when not, and the percentile forms resample whole clusters — jointly across both sides when paired. Same rule and same reason as `t_over_units_clustered` above. Every delta in `vs_baseline` and in [`results.contrasts`](#contrasts-claims-that-arent-condition-vs-baseline) records its `method`, exactly as every value in `aggregated` does — a [hypothesis](#pre-registration) quoting one under `observed` is quoting that record rather than restating it.

And `cohens_d`, when the metric is a per-unit mean: **paired contrasts report *d*z** — the mean of the per-unit differences over their standard deviation — and **unpaired ones report *d*s**, over the pooled within-condition standard deviation. They are different quantities from the same data and the one that applies follows from `paired`, which is [derived rather than declared](#allocation-within-subjects-or-between-subjects). A weighted condition standardizes by the weighted standard deviation, on the same weights the mean used. *d*s pools where `welch_t_over_units` deliberately doesn't, and that isn't an inconsistency: an interval is an inference and gets the assumption-light construction, while *d* is a descriptive standardization whose conventional denominator *is* the pooled one — reporting a *d* against a Welch-style denominator would be a number no reader could compare to another paper's.

A [`null_test`](#what-isnt-a-repeat) p-value is corrected alongside the intervals when the method supplies one, at the same level the interval was computed at. **It does not add a place in the family**: the family counts comparisons × metrics, and a metric reported with both an interval and a p-value is one metric described two ways, not two findings. Counting it twice would correct a design for declaring `null_test` rather than for the comparisons it actually put in front of a reader.

**A derived metric is resampled whether or not you declare `statistics.resample`.** The two `basis: units` rows of the first table above — the column metric and the derived one — are not symmetric, and this is the asymmetry: a column metric has a t-interval available, so resampling it is a choice, and `resample` is what makes it. A derived metric has no such fallback — there is no closed form for the sampling distribution of whatever `aggregate` computed — so the alternatives are a percentile interval from resampling or no interval at all, and core resamples. With `resample: null` it uses the default it documents here, `bootstrap` at `n: 2000`, which is why the worked example reports `method: percentile_over_units` under a config that declares nothing. Declaring `resample` then changes the method or the count rather than switching the behaviour on, and the resolved values are recorded in `run.yaml` beside the interval so the number is never the result of an undocumented default: a `resample: {method, n, stratify_by}` sibling of `n`, present in every metric block of a run that declared one and **absent — not `null`** — from every metric block of a run that didn't, the same absent-not-null shape the recorded-column paragraph below states for its own `resample_draws` (`null` there already means an interval was attempted and came back empty, which is a different fact from nothing having been asked for — the derived metric's own `resample_draws` is a further, three-valued scheme and that rule does not extend to it). `resample.n` is what was *requested*; `resample_draws` beside it is what the interval actually *rests on* — equal for a column by construction, and equal for a derived metric unless a draw was degenerate, which is what [`W-STATS-RESAMPLE-THIN`](#warnings-core-reports) reports. `stratify_by` is always a list in the record, even where the config wrote a bare string — the record resolves what the config abbreviates, the same rule [`of`/`against`](#contrasts-claims-that-arent-condition-vs-baseline) follow. See the `mean_pred` example in [§ What isn't a repeat](#what-isnt-a-repeat) for the shape. **In this build a declared [`cluster_by`](#clustered-units) is the one case where core resamples nothing**: the clustered draw for a *recomputed* metric is a construction that doesn't exist yet, and reporting a unit-level percentile beside recorded columns that are cluster-robust would be the narrower interval this section exists to refuse — so core drops that step's derived metrics and says so. The refusal is [`E-DATA-CLUSTER-DERIVED`](#errors-core-raises) and the record is [`W-STATS-AGGREGATE-FAILED`](#warnings-core-reports) carrying that code in its message — the same containment every other `aggregate` fault gets, so the recorded columns keep their clustered intervals and the run keeps its `run.yaml`. It is a run-time refusal rather than a `validate` one for the reason that row gives: whether a template derives anything is not knowable before `aggregate` runs.

**Resample methods.** `statistics.resample.method` names how the draws are taken, and the vocabulary is closed:

| `method` | What one draw is |
|---|---|
| `bootstrap` | Units drawn with replacement to the original count, or whole [clusters](#clustered-units) when `cluster_by` is declared, or within each [stratum](#weighted-samples) when `stratify_by` is — the statistic recomputed on each draw |

One value is the whole enum. It is stated as an enum rather than left implicit so that adding a second is a documented change rather than a silent one, and so a misspelled `method` is a refusal the schema can name — [`E-STATS-RESAMPLE-METHOD`](#errors-validate-reports) — rather than a value silently ignored. The method strings in the two construction tables above — `percentile_over_units`, `paired_percentile_over_units` and their `_clustered` forms — are what core **emits** into `run.yaml`, not values a config may name here.

**`resample_draws` says how many draws the interval actually rests on**, recorded beside every derived metric in `aggregated`. Resampling a derived metric means [recomputing it](#templates-where-parameters-are-defined), and a draw can legitimately have no answer: a resampled table with no variance makes a correlation `nan`, makes a hand-rolled ratio raise, and makes a careful `aggregate` return `None`. Which library the template happened to call is not a fact about whether the draw was degenerate, so all three are dropped alike and the percentiles are read off what survived. The field is `null` when resampling was never attempted, `0` when it was attempted and every draw was degenerate, and otherwise the surviving count — three different facts that `ci95: null` alone cannot tell apart.

**A recorded column carries `resample_draws` too, once `statistics.resample` is declared, but with different provenance and only two of the three values a derived metric's own `null`/`0`/*n* scheme uses.** A column has the `t_over_units` fallback the derived-metric asymmetry paragraph contrasts it with, so `resample_draws` is **absent** entirely — not `null` — when no `resample` is declared: nothing was attempted, and the key says so by not appearing, the same way the field is absent from a run predating H4a. Once declared, the value is **`null`** whenever `ci95` is (fewer than two units, or too few draws for the confidence level), and otherwise the **requested** `n` — never a lesser count, **given finite recorded values and finite weights**: a column's draw statistic is a mean, or a weighted mean, over a non-empty sample, and under that condition it is always defined once an interval exists at all, with no per-draw failure to survive-count the way a derived metric's recompute can fail draw by draw — so the derived metric's `0` bucket ("attempted, every draw individually degenerate") is unreachable for a column given finite inputs. **Nothing on this path checks that condition today**: a `nan` among the recorded values, or a weight vector whose sum overflows, reaches `ci95` and `resample_draws: n` exactly as a clean sample would, rather than the refusal a non-finite input should get — a known, unfixed gap `docs/superpowers/spec-defects.md` records rather than this build closing. The field is genuinely two-valued for a column (`null` or the requested `n`) against the derived metric's three-valued scheme given that same finiteness condition, and that asymmetry is real rather than smoothed over — it is a fact about what a mean can fail at, not an inconsistency in how core reports it.

**Below 80 surviving draws core reports no interval.** That is the fewest at which both percentile ranks are interior: under it the 2.5th percentile *is* the smallest draw, so the interval contains the sample minimum by construction while its upper end keeps shrinking — low-biased and too narrow — and at two survivors the two ranks coincide and the "interval" has zero width. Reporting a point with no interval is honest; a zero-width 95 % interval is not. `run` warns [`W-STATS-AGGREGATE-FAILED`](#warnings-core-reports) for a degenerate-on-every-draw metric (`resample_draws: 0`) among the other ways `aggregate` can produce nothing usable, and [`W-STATS-RESAMPLE-THIN`](#warnings-core-reports) when fewer draws survived than were requested but not zero — see the table for the rest of each condition. Neither costs the run its record: every execution had already completed, so the run is `completed`, `run.yaml` is written, the recorded columns keep their own summaries, and what is lost is the derived metric.

That first table's third row — a unit table exists and the metric isn't derivable from it — is the important refusal. A step that computes a cohort-level statistic internally and returns it as a number gives core nothing to resample: core never inspects the body of your Python, so it cannot recompute your statistic on a different set of units. What it will not do is fall back to an interval across the five seeds and present that as a confidence interval — **an interval over seeds measures how much the RNG moved the answer, and it narrows as you add seeds.** It says `basis: repeats`, reports the spread, and omits `ci95`. To get an interval, make the quantity a per-unit column, or teach the template to derive it (below).

Repeats are a variance component, not the inference base: for a `basis: units` metric, repeats are averaged per unit *before* any interval is computed — the same collapse technical replicates get at unit resolution — and their dispersion is reported alongside as `repeat_spread`, which answers "is this pipeline stable?" rather than "how precise is this estimate?"

In the worked example, `generic`'s `aggregate` derives `r` from the recorded `pred` and `truth` columns — selecting the coefficient from `cfg.parameters.analysis.method`, since that's what the sweep varies — so `r` is unit-based even though the step also returns it.

**`per_repeat` and `aggregated` come from different places, and neither is derived from the other.** `per_repeat` is verbatim what each step returned on that execution — nothing more, and no derived metric ever appears there, because deriving one per repeat would mean running `aggregate` on a table that hasn't been collapsed yet. `aggregated` is computed once, from the collapsed table. Recording both side by side is deliberate: if the step's own `r` and the derived `r` disagree, that's visible in `run.yaml` rather than reconciled behind your back. Core doesn't adjudicate which is right — one of them is measuring something else, and that's a bug in the experiment, not a number for core to pick.

```yaml
results:
  conditions:
    - index: 0
      label: baseline
      is_baseline: true
      aggregated:
        step03_analyze:
          r: {value: 0.581, basis: units, method: percentile_over_units,
              n: {resolved: 240, completed: 228, failed: 12},
              ci95: [0.488, 0.661],
              repeat_spread: {std: 0.021, n: 5, kind: seed}}
    - index: 1
      label: method=spearman
      per_repeat:                                   # exactly what the step returned
        step03_analyze:
          seed17: {r: 0.62}
          seed42: {r: 0.59}
      aggregated:
        step03_analyze:
          r: {value: 0.607, basis: units, method: percentile_over_units,
              n: {resolved: 240, completed: 228, failed: 12},
              ci95: [0.517, 0.683],
              repeat_spread: {std: 0.014, n: 5, kind: seed}}
      vs_baseline:                                  # only when a baseline is declared
        step03_analyze:
          r: {delta: 0.026, basis: units, paired: true,
              method: paired_percentile_over_units,
              ci95: [-0.007, 0.059],
              ci95_corrected: [-0.007, 0.059],      # rank 2 of 2 under holm: α/(m−i+1) = α
              correction: holm, correction_level: 0.05,
              family_size: 2, family: {comparisons: 2, metrics: 1},
              cohens_d: null}                       # r is derived, not a per-unit mean
  summary:
    step04_compare_methods: {best_method: spearman}
```

**`cohens_d` is reported only for a per-unit mean.** Cohen's *d* standardizes a difference by the dispersion of the values being differenced, which needs a value per unit: with `abs_error` recorded per patient, the paired per-unit differences have a standard deviation and *d* is exactly the right summary. A derived statistic has no such thing — there is no per-patient `r` to difference — so `cohens_d` comes back `null` and the delta's interval carries the magnitude instead. Reporting a *d* there would mean inventing a denominator, which is the same error as reporting a confidence interval over seeds.

The per-condition intervals are wide and the delta's is narrow, and that isn't an inconsistency — it's what `allocation: within` buys. Both conditions were evaluated on the same 228 units, so the paired difference cancels the between-patient variability that dominates each condition's own interval. Reporting the delta from unpaired intervals would throw that away; reporting it from seed dispersion would invent precision that isn't there.

#### Repeat kind still decides how repeats collapse

Within a condition, the two repeat kinds mean something different, so the collapse differs:

| Repeat kind | How its repeats enter |
|---|---|
| `seed` | Averaged per unit; dispersion reported as `repeat_spread` |
| `batch` | Averaged per unit, exactly as `seed` — the difference is what the dispersion *means*, not how it is computed |
| `fold` | Each unit appears in exactly one test partition per fold, so the per-unit values concatenate rather than average |

And two `statistics` declarations change how the interval itself is computed, without adding executions:

| Declaration | What it replaces |
|---|---|
| `resample: {method: bootstrap, n: 2000}` | The t-interval, with a percentile interval over resampled units — or over resampled clusters when [`cluster_by`](#clustered-units) is declared. The right choice for a derived statistic whose sampling distribution isn't t-shaped |
| `null_test: {method: permutation, n: 5000, shuffle: label}` | Nothing; it *adds* a `p_value` against a null built by relabelling units — within clusters, or whole clusters at a time, per [`cluster_by`](#clustered-units) — tested against the value the run actually produced |

With nested repeats, core collapses inner-to-outer, so 10 folds × 3 seeds averages seeds within each fold before combining folds — rather than flattening 30 numbers that aren't exchangeable. Whether the comparison across conditions is paired follows from `data.units.allocation`.

`publishable report` renders a sweep as a comparison table across conditions, with dispersion, and a delta column when a baseline exists.

#### Contrasts: claims that aren't condition-vs-baseline

`vs_baseline` covers the common case — every condition against one designated reference — and it needs no declaration. Some designs' claims aren't that shape. A matched physiology experiment compares an *abnormalizing* arm against its matched *normalizing* arm, neither of which is the reference; an invariance check compares two counterfactual arms directly; a crossover compares two treated periods. No choice of baseline makes those contrasts appear, because the comparison a design cares about is between two conditions it declared for that purpose.

So a contrast can be named:

```yaml
statistics:
  contrasts:
    - id: sensitivity
      of: "shift=abnormal__magnitude=1.0"
      against: "shift=normal__magnitude=1.0"
    - id: invariance
      of: "occasions=3"
      against: "occasions=12"
```

`of` and `against` name conditions by label — the same discrete labels a [hypothesis](#pre-registration) `compare.condition` selects, stable across machines and reruns because they derive from swept values only.

**`within` restricts a contrast to a stratum**, which is how a subgroup claim becomes testable:

```yaml
statistics:
  contrasts:
    - {id: sensitivity,   of: "shift=abnormal", against: "shift=normal"}
    - {id: sensitivity_f, of: "shift=abnormal", against: "shift=normal", within: {sex: f}}
```

It names unit attributes and their levels — the same attributes [`report_by`](#reporting-strata) resolves — and the contrast is computed over units matching all of them. A hypothesis reaches a stratum through the contrast rather than through a selector of its own, which is why `metric` stays `step.metric` and nothing else has to learn about strata.

**A `within` contrast joins the correction family, and a `report_by` stratum does not.** That is the whole difference between the two, and it is the honest one: describing a subgroup costs nothing, *testing* one is a comparison a reader can act on, and six declared subgroup contrasts widen the correction by six. Subgroup multiplicity is the best-known way to turn a null result into a finding, so it is priced rather than free — which is also why a subgroup claim has to be declared before the run to be confirmatory at all.

`limits.min_reported_n` applies to a `within` contrast's `n_paired`, since a stratified paired comparison is where a small denominator is easiest to miss and most disclosive.

**Everything about how a contrast is computed is a rule that already exists.** Pairing is derived from which axes the two conditions differ on, by [the same table](#allocation-within-subjects-or-between-subjects) `vs_baseline` uses — so two arms of one parameter axis under `allocation: within` are paired unit by unit, and two levels of a group axis are not. A contrast crossing two axes is marked `confounded: true` for the same reason. Declared contrasts join the [correction family](#sweeps-and-repeats) alongside baseline comparisons, because a reader shown both is exposed to both.

Results land beside the conditions rather than inside one, since a contrast belongs to neither of its sides:

```yaml
results:
  contrasts:
    - id: invariance
      of: 04_occasions=3                        # recorded with its index; declared without one
      against: 06_occasions=12
      step03_screen:
        prob: {delta: 0.012, basis: units, paired: true,
               method: paired_t_over_units, n_paired: 412,
               ci95: [0.004, 0.021], ci95_corrected: [0.001, 0.024],
               correction: holm, correction_level: 0.0071,
               family_size: 7, family: {comparisons: 7, metrics: 1}}
```

**`n_paired` is the intersection, and it has to be recorded.** Two conditions can complete on different units — a transform that isn't constructible for every patient, an assay that failed on a subset, an arm whose eligibility differs — and a paired comparison exists only for units that completed in *both*. Differencing the two condition means instead would not be a paired comparison at all, however carefully `paired: true` was derived. The condition-level `n` can't carry this, because it belongs to one condition and the contrast spans two, so the contrast records its own. A contrast whose intersection is empty is reported as such rather than as a delta of zero.

**Contrasts don't nest, and the reason is one you already have.** A contrast is between two *conditions*. A comparison between two *contrasts* — is the effect at dose 1.0 larger than at dose 0.5, did the difference between arms differ between sites, is the mean of the native cells above the mean of the foreign ones — is an interaction term, and [core doesn't compute those](experimental-designs.md#what-core-will-not-do-for-you) whether they arrive through a factorial `grid` or through here. Three shapes people reach for, and all of them are the same thing wearing different clothes:

| You want | It is | Where it goes |
|---|---|---|
| A monotonic dose response across three arms | An ordering of contrasts | `scope: "summary"` step, returned as an [`Estimate`](#estimate-carries-your-interval-without-core-claiming-it) |
| A difference-in-differences | An interaction | Same |
| A nested or weighted mean *over* many contrasts | An estimator over contrasts | Same |

Declaring thirty contrasts to build one number is the failure mode worth naming, because `contrasts` makes it look available: it widens the correction family by thirty comparisons nobody reads individually, and the number you actually wanted still isn't computed. Declare the contrasts you will *report*, and build the combination in a summary step where it can carry its own interval and its own method.

#### Reporting strata

Pre-specified subgroup reporting — by sex, by site, by severity band, by record source — is a requirement of most reporting checklists and is *not* a design axis. Making it one would be actively wrong: five reporting attributes as `groups` axes multiply into a cartesian product of cells, each an execution of a pipeline that should run once, most of them below `limits.min_units_per_cell`.

`report_by` names unit attributes instead. Core repeats the aggregation it already performs, over the subsets of the per-unit table each level picks out:

```yaml
statistics:
  report_by: [sex]
```

```yaml
aggregated:
  step03_analyze:
    r: {value: 0.607, basis: units, n: {resolved: 240, completed: 228, failed: 12}, ci95: [...]}
    by:
      sex:
        f:
          r: {value: 0.591, basis: units, n: {resolved: 120, completed: 114, failed: 6}, ci95: [...]}
        m:
          r: {value: 0.622, basis: units, n: {resolved: 120, completed: 114, failed: 6}, ci95: [...]}
```

**Two attributes are two marginal splits, not their cross.** `report_by: [sex, site]` adds a `by.sex` block and a `by.site` block, each over the whole table; it does not produce a `f × site_03` cell. A cross *is* a set of design cells, which is what a [`groups` axis](#expansion-modes) expresses when you want to execute over it and what a [`within` contrast](#contrasts-claims-that-arent-condition-vs-baseline) expresses when you want to test one — and the cells of five reporting attributes are exactly the cartesian product this section exists to avoid. Strata also repeat `aggregated` metrics only, never `vs_baseline` or a contrast's delta — a per-stratum delta would have to join the correction family, which is what a `within` contrast is for.

Three properties, each a consequence of strata not being conditions. **No executions are added** — the run is unchanged and the split happens over a table that already exists. **Strata don't join the correction family**, because a stratum is a description rather than a comparison a reader acts on. A subgroup claim you intend to *test* is a [`within` contrast](#contrasts-claims-that-arent-condition-vs-baseline) — declared before the run, named by a hypothesis, and corrected in that family. The split is deliberate: `report_by` gives you every subgroup for free because it claims nothing, and a subgroup you want to claim something about costs a place in the family. And **`limits.min_reported_n` applies per stratum**, which is where it matters most: a per-subgroup result over a handful of units is exactly what [`study add`](#what-study-add-redacts) says no automatic rule can judge safe.

`validate` rejects a `report_by` attribute that isn't declared in `data.units.attributes`, and warns when a level would hold fewer units than `limits.min_reported_n` — before the run rather than at disclosure.

### Before you spend it

```bash
uv run publishable dry-run configs/cohort-pilot/config.yaml
```

```
sweep: 3 conditions (baseline + grid) × 5 repeats = 15 executions
  00_baseline            analysis.method=pearson
  01_method=spearman
  02_method=kendall
repeats: seed(n=5)
  seeds: [17, 42, 137, 1009, 2027]  (auto, from design digest)
  comparisons: paired (allocation: within)
steps: step01_load_cohort (run) -> step02_fit_model (condition)
       -> step03_analyze (repeat) -> step04_compare_methods (summary)
statistics: basis units (n=240 resolved); r derived by template aggregate()
            percentile CI per condition; paired delta vs 00_baseline
scale:  3,600 unit-executions (15 executions × 240 units handed to each)
would write 64 artifacts under /secure/results/cohort-pilot/run_.../
```

Grid sizes multiply quietly, and nested repeats multiply on top of them. `validate` warns past `limits.max_executions`, and `dry-run` prints the full expansion, because "6 conditions × 10 folds × 3 seeds" is easy to write and slow to discover.

**`unit-executions` is the line to read before a metered run, and it is not the execution count.** It's the sum of `len(io.units)` over every planned execution — one count per unit per (condition, repeat), which core can state exactly because it computed the partitions. The two numbers come apart in both directions: under `{kind: fold, k: 10} × {kind: seed, n: 3}` each execution gets a tenth of the roster, so a condition's 30 executions are 720 unit-executions rather than 7,200, and a 20-execution sweep over a 100,000-unit corpus is cheap by `max_executions` and ruinous in practice. Where a step makes one request, one assay, or one simulation per unit, this is the count the bill is proportional to.

**There is deliberately no token or currency limit, and `limits` gains no field here.** Core has no price list and no way to count tokens, so a threshold in either would be a number it cannot measure — the same standard the [correction family](#sweeps-and-repeats) is held to, where a count that looks handled and isn't is worse than an honest one, and the same reason [`default_repeats` is a plain integer](#naming-conventions--repeat-defaults) rather than a derived one. What core owns is the multiplier; the per-unit cost is yours, and multiplying two numbers is not a feature worth a config field. Where a budget must be part of the pre-registered record, declare it as a template parameter — `pricing.prompt_per_mtok`, `budget.max_usd` — so it is hashed with everything else, and check it in the template's [`validate`](#templates-where-parameters-are-defined) or report it from a [`summary` step](#steps-that-need-every-condition).

**`dry-run` is the command that reaches outward, so it needs what a run needs minus the compute.** It builds the input manifest and [probes the apparatus](#the-apparatus-core-can-only-observe), which means real credentials and a reachable apparatus — for a sweep over six model deployments, all six, including any local one actually running. That is the point of the split rather than a cost of it: [`validate`](#cli-reference) stays free to run in a loop while you edit YAML, and everything expensive happens once, in a command you invoke when you think you're ready. Develop a wide sweep against one level of the axis and widen it last; `dry-run` is where a config you can't afford to run announces itself.

---

## Three hashes

A single git commit hash was doing two incompatible jobs: identifying the code and, implicitly, the parameters. Splitting them is what makes single-variable comparison possible.

| Hash | Covers | Answers |
|---|---|---|
| `code_hash` | Content hash of `src/**` and `templates/**` | Was the code identical? |
| `parameters_hash` | The whole config except `metadata` and the two path fields — see below | Were the parameters identical? |
| `input_manifest_hash` | Relative paths + content hashes of `input_dir`, at the depth `data.input_manifest_policy` asks for | Was the data identical? |

**`code_hash` covers `templates/**` as well as `src/**`, because a [project-local template](#templates-where-parameters-are-defined) is code the reported numbers came out of.** Its `aggregate` derives a condition's metric and its interval, and its `validate` decides which configs are legal — so a run whose `templates/` moved computed something else, and a `code_hash` over `src/**` alone would call the two runs identical. Core's own templates and a plugin's are outside both trees and pinned differently, by `uv.lock`: a dependency has a version you can resolve, while a file in your repo has only the history your repo keeps. That's also why `template_version` isn't the answer for a local template — it's a string its author remembers to bump, which is the class of claim [`publishable_version`](design-principles.md#whose-git-hash-is-this) is deliberately kept to. `init` reflects that by writing no `template_version` line at all for a local template — the generated header comment drops its version clause the same way — and `validate`'s [`W-TEMPLATE-VERSION`](#warnings-core-reports) check is skipped for one regardless of what a config declares: comparing a hand-written string against core's own constant would answer a question that string was never asked. `plugin` stays `null` for a local template too, unchanged from every other template, because it names a distributable source and a local template has none.

### How the three are computed

A hash that two machines compute differently is not an identity claim, so the constructions are fixed rather than left to an implementation.

**`code_hash` is `sha256` over the sorted list of `(repo-relative path, sha256 of file contents)` pairs** across `src/**` and `templates/**`, taken from the **working tree** and skipping whatever `.gitignore` skips. Which repo those paths are relative to is decided by [the walk-up rule](design-principles.md#whose-git-hash-is-this): it starts at the path the command was given, so a hash never depends on the directory you invoked it from. Not a git tree hash, and the reason is [`draft`](#draft-runs): a git tree hash needs the content staged, so a dirty tree has none, and `run` and `draft` would then be computing two incomparable things. Reading the working tree means both compute the same function, and a draft's hash is a real fingerprint of the code that ran — just one no commit reaches, which is exactly what `draft: true` records. File modes, timestamps, and paths outside the two trees are all excluded, so a `chmod` or a touched file changes nothing.

**The boundary is the tree, not the experiment, and what that costs is worth stating.** `src/**` covers every experiment package in the repo, so adding or editing `src/other_pilot/` moves the `code_hash` of a run that never imported it — which shortens "same code, weeks apart at different commits" to "same code, and nobody touched the two trees." The alternative is hashing only the package [`entrypoint`](#generators) names plus whatever it imports, and core cannot compute that without reading your Python, which is [the line it doesn't cross](design-principles.md#greenfield-only). A rule that hashed one package while a shared `src/common/` module produced half the numbers would be a hash claiming more than it covers, and that is the worse failure of the two. So the tree is the honest unit, and the remedy is the one [§ Whose git hash is this?](design-principles.md#whose-git-hash-is-this) already names for the same reason: an experiment whose `code_hash` has to hold still against unrelated work belongs in its own repository.

**`parameters_hash` and the [design digest](#what-auto-derives-from) are `sha256` over a canonical JSON rendering** of what each covers: UTF-8, object keys sorted, no insignificant whitespace, floats in shortest round-trip form. **Values are normalized to what `init` would have materialized before hashing** — an omitted `cluster_by` and an explicit `cluster_by: null` are the same declaration, and a config that omits a defaulted key hashes identically to one that spells it out. Without that rule, a hand-trimmed config and the file `init` wrote would disagree about parameters that are equal, and `diff` would report a difference with nothing to print.

`input_manifest_policy` decides how much of `input_dir` gets hashed, because "hash everything" stops being affordable somewhere between a spreadsheet and a 4 TB imaging archive:

| Policy | Manifest holds | Use when |
|---|---|---|
| `hash_all` | Every file's relative path, size, mtime, and content hash | The default. Anything you can read through once at run start |
| `hash_index` | Content hashes for the files `data.units.from` resolves — the index and whatever it names — plus path, size, and mtime for the rest | The archive is too large to read whole, but the table driving the run isn't |
| `none` | Paths, sizes, and mtimes only | Input lives on storage whose contents you can't read exhaustively, and you accept a weaker claim |

The three make different promises, and `run.yaml` records which one was in force so a reader isn't left inferring it. Only `hash_all` supports "the data was identical" without qualification; under `hash_index` the claim is "the units were identical and nothing else moved size or timestamp"; under `none` it's a change *detector*, not a verification. Verification after the run, and the comparison a [reproduction](#reproducing-on-another-device) makes against the recorded manifest when it runs, both operate at whatever depth the policy captured.

**What `parameters_hash` covers is stated once, here, because four guarantees read it.** The rule is subtractive: **everything in the config except `metadata` and `data.input_dir`/`data.output_dir`.**

| Block | In | Because |
|---|---|---|
| `schema_version`, `experiment_type`, `template_version`, `plugin`, `entrypoint` | ✓ | They decide which code and which spec the values are interpreted against. A config repointed at a different experiment class is not the same run |
| `data`, minus the two path fields | ✓ | `units`, `assign`, `holdout`, `measurements`, and `input_manifest_policy` all decide what is measured and how strong the data claim is |
| `parameters` | ✓ | The obvious case |
| `sweep`, `replication` | ✓ | What varies and how often — the declaration, never the conditions it expands into |
| `statistics`, `limits` | ✓ | They decide which number a reader is shown and whether the run was allowed to proceed. See [Validation](#validation) on why thresholds are parameters |
| `hypotheses` | ✓ | The [pre-registration](#pre-registration) check is exactly this: a hypothesis added after the fact doesn't match the hash of the config that predicted it |
| `metadata` | ✗ | A title, a description, an author list. Editing one changes nothing about what ran, and a re-titled config that no longer matched its own runs would be a false alarm |
| `data.input_dir`, `data.output_dir` | ✗ | Host paths. This is what lets [`study add`](#what-study-add-redacts) redact them without disturbing verification, and what lets two machines with the data mounted differently produce the same hash |

Two consequences worth knowing before they surprise you. **A `metadata`-only edit is invisible to `diff`**, which is the intent — but it means `diff` reporting `parameters_hash identical` is not a claim that the two files are byte-identical. And **adding a hypothesis makes an interrupted run unresumable**, because [`resume` refuses when `parameters_hash` moved](#resuming). That is the same rule catching the same thing it always catches — the config changed under a run in flight — and it applies to an exploratory hypothesis you added mid-run for reasons that felt harmless. Finish the run, then declare it in the config for the next one; a hypothesis declared after a run started is exactly what the mechanism exists to distinguish.

**It is one hash per run, not one per condition.** It covers the declaration, not the per-condition values it expands into. Two properties depend on that, and neither would survive a per-condition hash: `diff` compares two runs by a single hash, and a hypothesis carries the hash of the config that predicted it. A condition's own resolved values live in `results.conditions[i].values` and in `sweep.yaml`, where they belong: they're derived, so they aren't a separate identity claim.

**Covering `data.units` here doesn't make the [design digest](#what-auto-derives-from) redundant**, because the two are read in opposite directions. The hash is an identity claim a reader checks after the fact — *were these the same declarations?* The digest is a derivation input consumed before the run, and it deliberately covers *less*: `data.units` and `sweep.groups` only, so that editing `min_samples` moves `parameters_hash` and leaves every fold boundary and arm assignment exactly where they were. One answers whether two runs declared the same thing; the other decides what gets randomized. Nothing compares two digests.

### The apparatus core can only observe

Code, environment, and input data are all pinned by something core controls: [a hash over the code trees](#how-the-three-are-computed), a lockfile, a content manifest. An experiment that measures through an **external apparatus** — a hosted model deployment, an instrument, a sequencer, a scoring service — depends on a fourth thing that core can neither install nor hash from disk. `uv.lock` pins the client; nothing so far pinned the server.

That gap is not a small one. For an LLM benchmark the deployment revision *is* the intervention; for a wet-lab assay the calibration run is what the numbers are traceable to. Leaving it out means a run record that pins everything except the part that moved.

**So the apparatus is probed, recorded, and gated — and the division of labour is the one [unit resolvers](#where-units-come-from) already use.** A template declares what must be known about the apparatus; a plugin knows how to ask:

```python
# src/publishable_my_assay/probes/instrument.py
from publishable import Apparatus, register_probe

@register_probe("assay_instrument")
def probe(cfg) -> Apparatus:
    client = connect(cfg.parameters.instrument.model)
    return Apparatus(facts={
        "model":          client.model_id,
        "firmware":       client.firmware_version,
        "calibration_id": client.active_calibration,      # read, not declared
        "reagent_lot":    client.loaded_lot,
        "endpoint_host":  sha256(client.host)[:16],        # hashed, not disclosed
    })
```

```toml
[project.entry-points."publishable.probes"]
assay_instrument = "publishable_my_assay.probes.instrument:probe"
```

```python
@register_template("my_assay")
class MyAssayTemplate(BaseTemplate):
    required_env = ["INSTRUMENT_API_TOKEN"]
    apparatus_probe = "assay_instrument"                   # which plugin asks
    apparatus_facts = ["model", "firmware", "calibration_id", "reagent_lot"]
```

`apparatus_facts` is the same projection rule as `data.units.attributes`: core enforces that the probe yields every declared *key* and rejects one that doesn't, without knowing what any of them mean. **The plugin decides how the apparatus is interrogated; core decides what is required of it, records the answer, and refuses to continue when it changes.**

**A probe emits non-secret, non-identifying facts, and that's a rule rather than a convention.** A revision string, a firmware version, and a calibration ID are safe to publish; an endpoint URL or an instrument serial can identify an institution on its own, so a probe emits a *hash* of one instead of the value — which is what makes `provenance.apparatus` publishable as-is and is why [`study add`](#what-study-add-redacts) has nothing to redact from it. Credentials never appear, for the same reason [they never appear anywhere else](#secrets--credentials).

**It runs at `dry-run`, at run start, and before every execution — never at `validate`.** An unreachable apparatus, a fact the probe doesn't supply, or one it supplies unanswered is worth learning before you spend the run, which is why it isn't deferred to `run`; and before every execution is the only placement that catches a revision changing *during* a long run, which is when it actually happens. But `validate` is the cheap command you invoke in a loop while editing YAML, and a probe is an authenticated request to something metered by somebody else.

So the split follows what is answerable without a call. **`validate` checks that the named probe is registered by an installed plugin — the only apparatus question that needs no request.** Everything about what a probe *yields* takes calling it, so `dry-run` is where it runs, where core checks that every key in `apparatus_facts` came back and that no returned value matches a credential, and where it warns for a declared fact that came back `null`.

That line is worth stating in general, because unit resolution sits on the other side of it: **`validate` may read your config and your input, and may not reach anything outside the machine.** A resolver walking a local archive costs you time on your own disk; a probe costs you quota, money, and possibly a rate limit on a service someone else operates. Both are "pre-flight," and only one of them is free to repeat.

```yaml
provenance:
  apparatus:
    probe: assay_instrument
    ledger: "apparatus/probes.jsonl"           # every probe, append-only, with UTC and condition
    hash: sha256:5d7c...                       # over the resolved condition → facts mapping
    facts:                                     # one entry per condition, since the apparatus may
      00_baseline:                             #   legitimately differ across a sweep
        model: "seq-4000"
        firmware: "3.11.2"
        calibration_id: "CAL-2026-07-19"
        reagent_lot: null                      # declared, unanswered — no lot was loaded
    unobserved:                                # per fact, over the run's probes
      reagent_lot: {null_probes: 3, total_probes: 15}
```

**A changed fact fails the run, with no policy knob.** Same line as a dirty code tree, a lockfile mismatch, or an input file that moved: data gathered under two different apparatus states is not one dataset, and a flag to permit it would only ever be used to paper over the moment a result stopped being interpretable. Restarting under a changed apparatus is a new run — [`resume`](#resuming) refuses it too, and the ledger keeps both observations so the evaluable earlier period is still reportable.

**A key is not a value, though, and the change that fails is a change between two *observations*.** An apparatus answers unevenly: a hosted deployment returns a revision fingerprint on most calls and omits it on some, and an instrument reports a reagent lot only when one is loaded. So `null` is a legal fact value meaning *the apparatus did not answer*, and the three states are the three [`Param`](#templates-where-parameters-are-defined) already has — a value, a declared absence, and a key that isn't there at all. Only the third is an error, because only the third is the plugin and the template disagreeing about what this probe supplies.

`null → "LOT-88231"` and `"LOT-88231" → null` are that fact becoming available and becoming unavailable. Neither is evidence the apparatus moved, and failing on them would make an unevenly-reported field more dangerous than no field at all — the one honest thing to do with a flaky pin would be to stop declaring it, which is the opposite of what this section is for. `"LOT-88231" → "LOT-90114"` is two states and fails, exactly as before. Read the other way, the same rule is why the gate is worth having at all: an apparatus that never answers can never contradict itself, so an unobserved fact is a pin you don't have rather than a pin that held.

**That is also the whole of what declaring a fact buys, which is worth being plain about.** Every fact a probe returns is recorded and gated on these terms, named in `apparatus_facts` or not — a probe wouldn't return it if it didn't describe the apparatus. What the declaration adds is a **warning at `dry-run` when the fact comes back `null`**, and an `unobserved` count in the record so a reader can see how often it did. So declaring a fact you may not be able to observe is the right move rather than a mistake: the warning is the point, and leaving it undeclared to avoid one would trade a gap you can see for a gap you can't.

**Unlike a resolver, a probe *may* read parameters the sweep varies**, and usually must: a sweep over `llm.model` or `instrument.model` is a sweep across apparatus. The unit table has to be one table for the whole run, which is why a resolver is [condition-independent](#where-units-come-from); the apparatus has no such obligation. So facts are recorded per condition and the gate is per condition — a deployment is compared against its own first observation, never against another condition's.

**This is not a fourth hash** in the sense [§ Three hashes](#three-hashes) means. It sits beside `uv_lock_hash` as an environment fingerprint: something `diff` compares and a reader checks, rather than one of the three identity claims that make "same code, different parameters" provable. `diff` prints it on the same footing:

```
code_hash          identical    sha256:8e21...
input_manifest     identical    sha256:3d8a...
uv.lock            identical    sha256:6b1f...
apparatus          DIFFERS
  calibration_id   CAL-2026-07-19 → CAL-2026-08-02
parameters_hash    identical    sha256:1a2b...
```

That output is the point of the whole mechanism: two runs with identical code, parameters, and data that disagree, and a record that says why.

`apparatus_probe` is optional and `null` by default. An experiment whose measurements never leave the machine declares nothing and records `apparatus: null` — the worked example throughout this document is one.

### What `auto` derives from

`seed: auto` — for [repeat seeds](#repeat-kinds), [`sample`](#expansion-modes) draws, and [arm allocation](#allocation-within-subjects-or-between-subjects) — derives from a **design digest** over `data.units` (every field except a drawn partition's own seed — `assign.<axis>.seed` and `holdout.seed`) and `sweep.groups`. Those are the declarations describing *what is being randomized over*. It covers nothing about the parameter values being swept.

That separation is load-bearing, not tidiness. If randomization derived from `parameters_hash`, editing any parameter would redraw every fold boundary, reseed every repeat, and reassign every patient — so the comparison [`diff` advertises](design-principles.md#same-code-different-parameters) as "one named parameter changed" would actually be that parameter *plus* a fresh partition of the data under a fresh RNG, confounded and presented as clean. Two runs would differ in one visible place and two invisible ones. And a trial's arm membership would move because someone tuned `min_samples`, which is not a property any trial can have.

| `auto` value | Mixes | So it moves when |
|---|---|---|
| A `seed` level's seeds | digest, as a stream truncated to `n` | the unit declaration or group axis changes — *not* when you raise `n`, which extends the list rather than redrawing it |
| A `fold` level's boundaries | digest + that level's `k` and `stratify_by` | `k` or `stratify_by` changes, or the roster does |
| `sweep.sample` draws | digest + `n`, `method`, `ranges` | the sample declaration changes |
| An axis's `assign.seed` | digest + the axis name + the resolved roster | the roster changes, or any axis is added or edited — see below |
| `data.units.holdout.seed` | digest + the resolved roster | the roster changes, or the unit declaration does — see below |

**Two derivations use the digest without being `auto` values**, and belong on the same page as the four above: [`derive_seed(purpose)`](#a-step-that-partitions-needs-a-seed-and-derive_seed-is-where-it-comes-from), which mixes the digest, the roster, and the string you pass; and the [per-execution seed](#randomness-and-which-stream-a-step-should-draw-from) behind `self.rng`, which is the repeat's own where there is one and a `derive_seed` of the step's name where there isn't. Neither is a config field, so neither has a row — but both move when the digest does, which is the property this section is about.

**An omitted `seed` is `auto`, not an error.** `sweep.sample.seed`, `assign.seed`, and `holdout.seed` each default to the derivation above — which is what `init` writes anyway, so trimming the line changes nothing and a config that never mentions a seed is fully determined. Pinning an integer is the deliberate act, and the one to take for anything you intend to cite. **A seed that is *present* must be one or the other, though** — a quoted `"1234"`, a `1.5`, or a `true` is a pin nothing can honour, and honouring it as far as the derivation would record a derived seed under a key the config wrote deliberately. `sweep.sample.seed` is refused as `E-SWEEP-SAMPLE-INVALID`, `assign.<axis>.seed` as `E-DATA-ASSIGN-SEED`, and `holdout.seed` as `E-DATA-HOLDOUT-SEED`. A pinned `holdout.seed` is excluded from the design digest the same way a pinned `assign.<axis>.seed` is, and for the same reason: a seed that is itself inside the digest it is mixed with would make the derivation self-referential, and would move every *other* derived draw in the run.

The digest is deliberately **not a fourth hash.** The [three](#three-hashes) answer "was this identical?" and are identity claims a reader checks. The digest claims nothing: it's a derivation input, recorded in `sweep.yaml` beside the values it produced so `reproduce` regenerates the same partitions. Nothing compares two digests, and `diff` doesn't print it.

**Adding a group axis moves the draws of the axes already there.** The digest covers `sweep.groups` wholesale, so declaring `sex` alongside an existing `arm` re-randomizes `arm`. That's honest — the design changed, and the new allocation is balanced over a cross the old one knew nothing about — but it has a consequence to plan around: a reporting axis can't be added to a study already allocated without a fresh draw. Deriving each axis from its own sub-digest would keep the earlier one still, at the price of a derivation rule no longer summarizable in a sentence. Pin `seed` to an integer for anything you intend to cite, which is the same advice as below and for the same reason.

**Allocation also depends on the roster, so a changed roster re-randomizes.** Core assigns over the unit list resolved at run start; add ten enrollees to `enrollment.csv` and the draw is over 250 units rather than the previous 240 with ten appended. Nothing carries an earlier assignment forward, so **no `assign.method` supports prospective enrollment** — the general form of the limitation [§ Allocation](#allocation-within-subjects-or-between-subjects) notes for `blocked` specifically. Two honest ways to live with it: freeze the roster before the run and treat allocation as the one-time event it is, or let a trial system randomize and read its result with `assign.method: by_attribute`, which is what a real trial does regardless. For anything you intend to cite, pin `assign.seed` to an integer and keep `allocation.json` — a recorded assignment is a fact about what happened, and it should not be re-derivable to a different answer.

The full `git.commit` is still recorded, because `reproduce` needs something to check out — but it's the *transport* mechanism, not the identity claim. `code_hash` is the identity claim, and it's narrower: it ignores everything outside `src/**` and `templates/**` — the config, the README, `docs/`, `tests/`, and every other tree in the repo. It does *not* ignore another experiment, which lives in `src/`; see [How the three are computed](#how-the-three-are-computed).

`run` refuses to execute when `src/**` or `templates/**` has uncommitted changes, since a `code_hash` that isn't reachable from any commit can't be reproduced. Use [`publishable draft`](#draft-runs) for iteration: it permits a dirty tree and records the run as provisional rather than pretending otherwise.

---

## Lineage between runs

`io.reuse_from(run_id, step, name)` lets a run consume an earlier run's artifacts — expensive preprocessing, a fitted model, a scored cohort. Whenever it's used, core records that dependency in `provenance.upstream`: the upstream run's ID, its `code_hash`, and its `parameters_hash`, plus exactly which artifacts were read.

Without this, the provenance chain silently breaks at the one place work is shared. A run would claim a `code_hash` describing only its own code while depending on outputs produced by code it never names. Recording the upstream closes that: `reproduce` walks the chain and reports if any ancestor is unreachable, and `diff` can tell you two runs differ only because their upstreams did.

**A `run_id` is a label, so `reuse_from` needs a rule for turning one into a path**, and the rule is the narrow one: core looks for `<output_dir>/<run_id>/`, under *this* config's `output_dir`, where this experiment's own runs already live. That covers the ordinary case — a second run consuming a first — without any new declaration. An upstream living somewhere else is named by an absolute path to its run directory in the same argument, and its `run_id` is read back from the `run.yaml` there rather than parsed out of the path you passed. The example above shows where such a path belongs: a *parameter* (`cfg.parameters.program.upstream_run`), so the locator sits inside [`parameters_hash`](#three-hashes) and in the embedded config rather than in a step's source. Either way `provenance.upstream` records the resolved `run_id` and never the path, since a path is a fact about one machine.

Lineage is recorded, not resolved: core won't re-execute an upstream run for you. If an ancestor's artifacts are gone, it says so rather than silently recomputing something that might not match.

### `reuse_from` addresses an artifact, not the design that produced it

There is no condition or repeat selector, and that's deliberate. A selector would couple a downstream config to an upstream run's *layout* — its condition numbering and its repeat labels — and those are derived from a sweep the downstream run doesn't declare. Adding a level to the upstream design renumbers its conditions, so a downstream read pinned to `03_` would silently repoint at a different cell while every hash still matched. What a run publishes for others to consume has to be something it named on purpose.

The upstream run's `scope: "summary"` step is where that naming happens, and it's the only scope that can see every condition at once:

```python
# upstream run, scope="summary" — collect what downstream runs will consume
class Step(BaseStep):
    scope = "summary"

    def run(self, cfg, io):
        for condition in io.conditions:
            for repeat in io.repeats:
                io.write(f"programs/{condition.values['llm.model']}__{repeat}.json",
                         io.read_condition(condition, "step02_optimize",
                                           "compiled.json", repeat=repeat))
        return {}
```

```python
# downstream run, any scope — address it by name
blob = io.reuse_from(cfg.parameters.program.upstream_run,
                     "step03_collect_programs",
                     f"programs/{cfg.parameters.program.origin}__seed{seed}.json")
```

This is the shape any produce-then-consume design takes: one run varies what produces the artifacts, a second varies what consumes them, and the artifact set is the interface between them. Conditions differ in parameters or in which units they see, [never in which steps run](design-principles.md#what-core-does-not-promise), so a single run cannot both produce an artifact per condition and cross those artifacts against each other — the second run is what the crossing needs, and the collected names are what its sweep selects from. `provenance.upstream` then records exactly which of them were read, which is what makes "two runs differ only because their upstreams did" checkable at the level of named artifacts rather than paths.

---

## Pre-registration

The config is written before the run and hashed at run start. That's the mechanical property pre-registration asks for, so core lets you use it: declare what you *expect*, not only what you'll compute.

```yaml
hypotheses:
  - id: h1
    kind: confirmatory
    statement: "Spearman correlation exceeds Pearson on this cohort."
    metric: step03_analyze.r
    compare: {condition: "method=spearman", to: baseline}
    direction: greater
    threshold: 0.02
    evaluate_on: observed
```

Not every key above is required, and `validate` enforces the set below rather than leaving it to prose:

| Field | Required | Because |
|---|---|---|
| `id` | optional | `validate` never checks it; it exists to label an entry in `results.hypotheses`, not to resolve one |
| `kind` | required | `confirmatory` or `exploratory` with no default — an omission would silently drop a pre-registered claim out of its correction family (`E-HYPOTHESIS-KIND`) |
| `statement` | optional | `validate` never checks it; it is the claim in prose, for a reader, and plays no part in resolving or evaluating the hypothesis |
| `metric` | required | `compare` says *where*, never *what*, in every form — `metric` is the one field naming the quantity under test (`E-HYPOTHESIS-METRIC`) |
| `step` | not a key | there is no separate `step` field; it is the part of `metric` before the dot in `step.metric` |
| `direction` | required | `greater` or `less` with no default — a missing or mistyped value gets no default guess, only `supported: null` (`E-HYPOTHESIS-DIRECTION`) |
| `threshold` | required | a number with no default — the same absent-rather-than-guessed rule as `direction` (`E-HYPOTHESIS-THRESHOLD`) |
| `evaluate_on` | optional | `observed` when absent; `ci95_lower` or `ci95_upper` otherwise (`E-HYPOTHESIS-EVALUATE-ON` when present and none of the three) |
| `compare` | conditional | absent exactly when `metric` names a `scope: "summary"` step — a summary metric is one value per run, not a contrast between conditions — and required for every other scope; both directions are `E-HYPOTHESIS-FORM` |

**`compare` names both sides of the comparison, not one.** A condition alone says *what's being measured*; a comparison also needs *what it's measured against*. `to: baseline` is the ordinary spelling of the second side — the named condition against the declared baseline — and a declared contrast, named through `compare.contrast`, is the other. `compare: {condition: X}` with neither `to: baseline` nor a declared `sweep.baseline` names a condition and nothing to compare it against, and `validate` refuses it (`E-HYPOTHESIS-BASELINE`) rather than defaulting the missing side to baseline: a hypothesis whose comparison cannot be resolved has no quantity under test, the same reason `metric` is required, and a silent default would decide what a pre-registered hypothesis tested rather than what the config declared.

Core evaluates each hypothesis against the results and writes the verdict into `run.yaml`:

```yaml
results:
  hypotheses:
    - id: h1
      kind: confirmatory
      declared_in: parameters_hash sha256:1a2b...      # the config that predicted it
      observed: {delta: 0.026, ci95: [-0.007, 0.059],
                 method: paired_percentile_over_units,
                 ci95_corrected: [-0.007, 0.059]}       # corrected in the hypothesis family
      verdict_evaluated_on: observed                   # 0.026 against threshold 0.02
      family_size: 1                                   # this family, not the sweep's 2
      family: {hypotheses: 1}                          # confirmatory and core-computed
      supported: true
      verdict_rests_on: computed                       # core derived the number it compared
```

**The verdict records which number it compared, because the [hypothesis family](#sweeps-and-repeats) is corrected separately from the sweep's.** `family_size` and `family` carry it in the same idiom every other family uses, with a single breakout key because a hypothesis family multiplies nothing: it counts the confirmatory hypotheses whose observations core computed, where a sweep's family counts comparisons × metrics. A reader can check the level without re-deriving it, exactly as `family` beside a `vs_baseline` delta is auditable rather than asserted. Correction reaches a verdict only through a bound: a hypothesis evaluating on `observed` compares a point estimate, which has no α to adjust, while one evaluating on `ci95_lower` or `ci95_upper` reads the corrected bound at the level *this* family implies. `verdict_evaluated_on` names which of the three the comparison actually used — spelled out rather than echoing the config's `evaluate_on`, since a record field one letter from a config field is a typo waiting to be read as agreement. So a verdict is never a number a reader has to reconstruct from `evaluate_on` plus a correction rule.

**In the worked example the two available answers differ, and the field is what makes that legible.** The observed delta of 0.026 clears the declared threshold of 0.02, so `h1` is supported on `observed` — while the same delta's interval over 228 units, [−0.007, 0.059], does not exclude zero, so the same hypothesis written `evaluate_on: ci95_lower` would come back `supported: false`. Neither verdict is wrong; they answer different questions, and a reader who can see which one was asked can decide what the run showed. A record that reported only `supported: true` would be the version worth distrusting. See [What a hypothesis is tested against](#what-a-hypothesis-is-tested-against) for when to declare which.

**`supported` has three states, and the third is not a failure.** `true` and `false` mean the
comparison was made and came out one way or the other. `null` means core could not make it, and it
appears by exactly two routes: the observation does not resolve — the step that would have produced
the metric failed, or every unit on one side of a comparison was ineligible — or the verdict asks
for a bound (`evaluate_on: ci95_lower` or `ci95_upper`) against a bound that isn't there: the raw
`ci95`, or — for a hypothesis whose family is corrected — the corrected bound at the level this
family implies, which can be `null` for two unrelated reasons: a family too large for the resample's
draws to support ([`W-STATS-CORRECTED-THIN`](#warnings-core-reports)) leaves it unmet beside a raw
interval that is perfectly fine, and `correction: fdr_bh` leaves it unmet by construction — Benjamini-
Hochberg implies no per-comparison level at all, so there is no bound to build regardless of sample
size. The shape of `observed` is how a reader tells the two routes apart: the first writes `observed:
null` — there
is no block, because nothing was found to report — and the second writes a real `observed` block
whose `ci95` (or `ci95_corrected`) is the `null` field.

A `false` in either of those places would be indistinguishable from a claim that was tested and did
not hold, which is the confusion [`verdict_evaluated_on`](#what-a-hypothesis-is-tested-against)
exists to prevent one level up. A hypothesis core could not evaluate is not a hypothesis core
refuted.

The second route needs a comparison too thin to carry an interval, which this document's worked
pipeline — 228 units completing on both sides of each of its two comparisons — never produces, so it is shown
against a config of its own. A subgroup claim is the ordinary way to get there: a
[`within` contrast](#contrasts-claims-that-arent-condition-vs-baseline) narrows the paired
intersection to the units matching *every* level it names, and two levels together can leave one.

```yaml
statistics:
  contrasts:
    - id: sensitivity_thin
      of: "shift=abnormal"
      against: "shift=normal"
      within: {site: r07, sex: f}          # both levels, ANDed — one unit completes on both sides

hypotheses:
  - id: h3
    kind: exploratory
    statement: "The abnormalizing shift raises the score for women at site r07."
    metric: step03_screen.prob
    compare: {contrast: sensitivity_thin}
    direction: greater
    threshold: 0.0
    evaluate_on: ci95_lower
```

```yaml
results:
  hypotheses:
    - id: h3
      kind: exploratory
      declared_in: parameters_hash sha256:c7e2...
      observed: {delta: 0.041, ci95: null, method: null}  # one paired unit: a delta,
      supported: null                                     #   but too few draws for a ci95
      verdict_evaluated_on: ci95_lower
      verdict_rests_on: computed
```

`h3`'s one paired unit gives it a `delta` but too few draws for a `ci95`, and its bound test asks
for `ci95_lower` against an interval that isn't there, so `supported` comes back `null` rather than
a guess at which side of zero was meant. The same run reports
[`W-STATS-CONTRAST-THIN`](#warnings-core-reports) for the contrast underneath it, since an
`n_paired` of 1 is below any usable `limits.min_reported_n`. The two are different thresholds and
worth reading as such: the warning is about disclosure risk and fires well above one unit, while the
missing interval is the [fewer-than-two-units floor](#the-unit-table-is-the-inference-base) — a
five-unit stratum trips the first and still carries a `ci95`. And the entry carries no `family_size`,
because `kind: exploratory` keeps it out of the hypothesis family: that family counts the
confirmatory hypotheses core computed, so an exploratory declaration widens no correction and earns
no confirmation.

### What a hypothesis is tested against

`direction` and `threshold` are compared to the observed value by default. Some claims are about the *interval* instead, and the difference is not a refinement:

```yaml
hypotheses:
  - id: superiority
    kind: confirmatory
    statement: "Paired AUROC improvement over the utilization-only baseline exceeds zero."
    metric: step03_screen.auroc                # always required — see below
    compare: {contrast: sensitivity}          # a declared contrast, or condition/to as before
    direction: greater
    threshold: 0.0
    evaluate_on: ci95_lower                   # observed | ci95_lower | ci95_upper

  - id: invariance
    kind: confirmatory
    statement: "Predictions are invariant to visit count between 3 and 12 occasions."
    metric: step03_screen.prob
    compare: {contrast: invariance}
    direction: less
    threshold: 0.05
    evaluate_on: ci95_upper                   # an equivalence claim
```

**`evaluate_on: ci95_upper` is what an equivalence or non-inferiority gate is**, and there is no way to spell one against a point estimate. A mean absolute difference of 0.01 with an interval of [0.001, 0.30] passes `direction: less, threshold: 0.05` on the observed value and fails on the upper bound — and the second verdict is the correct one, because the study claimed invariance and the data are consistent with a large effect. Reporting "supported" there would be the tool asserting the opposite of what the evidence says.

`evaluate_on: ci95_lower` with `direction: greater` is the superiority form, and it is also how "the interval excludes zero in the expected direction" is written — those are the same statement.

Two rules core enforces. A hypothesis evaluating on a bound needs a metric that *has* one, so a [`basis: repeats`](#the-unit-table-is-the-inference-base) metric is rejected rather than warned about — the existing warning is for a metric that can be reported but not tested, and asking for a bound it doesn't have is a stronger error. `validate` catches the config-level form of that, where nothing in the run could carry an interval; the per-metric form is settled [when the step returns](#validation), like everything else about a returned key. And when the metric is a [reported `Estimate`](#estimate-carries-your-interval-without-core-claiming-it), the bound tested is the one the step supplied, so `verdict_rests_on: reported` carries its usual meaning: core compared the numbers and did not derive them.

**`metric` is required in every form, because `compare` says *where* and never *what*.** A [contrast](#contrasts-claims-that-arent-condition-vs-baseline) reports one value per step metric exactly as a condition does, so `compare: {contrast: invariance}` on its own names a comparison and leaves the quantity under test unstated — and a contrast declared over a step that reports three metrics would leave three candidates. `metric` is `step.metric` in all three forms: a baseline comparison, a declared contrast, and a [summary `Estimate`](#a-hypothesis-may-name-a-summary-metric), which is the one form that takes no `compare` at all.

**A hypothesis is one quantity against one threshold**, which is what makes it evaluable at all. A claim about the *shape* of a series — monotonic across doses, trending across ordered strata, flattening over a curve — has no single quantity to threshold, so it is a summary-step estimator returning an `Estimate` rather than a hypothesis. Declaring the shape claim as several adjacent hypotheses is available and rarely what you want: it tests each step of the series separately and corrects for all of them, which is a different claim from the one about the series.

Which corrected interval a bound test uses follows the family rules unchanged — `report` shows both, and a confirmatory gate reads the corrected one when a correction is declared.

### A hypothesis may name a summary metric

The quantity a protocol actually pre-registers is often the model-based one: a mixed model's adjusted effect, an agreement bound, a contrast no single axis expresses. Those are [`Estimate`s returned by a `summary` step](#estimate-carries-your-interval-without-core-claiming-it), and a hypothesis can name one. It takes no `compare`, because a summary metric is one value per run rather than a contrast between conditions. (The example below is a repeatability study rather than this document's worked pipeline, whose one hypothesis is the condition contrast above.)

```yaml
hypotheses:
  - id: h2
    kind: confirmatory
    statement: "Within-block safe agreement exceeds 0.99."
    metric: step04_agreement.s_within_lower_bound      # a summary Estimate
    direction: greater
    threshold: 0.99
    # no `compare`: there are no conditions to contrast
```

```yaml
results:
  hypotheses:
    - id: h2
      kind: confirmatory
      declared_in: parameters_hash sha256:1a2b...
      observed: {value: 0.9931, ci95: [0.9931, 1.0],
                 method: "one-sided BCa, 10000 patient-cluster draws, seed 20260722"}
      verdict_evaluated_on: observed                   # 0.9931 against threshold 0.99
      supported: true                                  # no `family`: core corrects nothing here
      verdict_rests_on: reported                       # THE STEP derived the number
```

**`verdict_rests_on` is the whole of what changes, and it keeps the [refusal](#estimate-carries-your-interval-without-core-claiming-it) intact.** Comparing 0.9931 against 0.99 is arithmetic, and core is willing to do arithmetic on any number in front of it. What it will not do is imply that it derived the number, so the verdict records which of the two it was. A `supported: true` resting on `reported` is a claim about your statistic; the same field resting on `computed` is a claim about core's.

That distinction is why extending pre-registration here costs nothing. Both of the things pre-registration actually buys — the confirmatory/exploratory split, and a `parameters_hash` that catches a hypothesis added after the fact — are properties of *when the declaration was written*, not of who computed the observation. Withholding them from summary metrics would have meant the quantities most worth registering being the only ones that couldn't be.

`validate` checks the two forms don't cross: a hypothesis naming a condition metric needs `compare`, one naming a summary metric may not have it.

Both of these are cheap, because the machinery already exists:

- **A confirmatory/exploratory split that holds up.** `report` renders confirmatory results as findings and exploratory ones as labelled exploration. Anything not declared before the run is exploratory by construction, rather than by anyone's recollection.
- **Detection of after-the-fact editing.** A hypothesis carries the `parameters_hash` of the config that declared it. Add a hypothesis after seeing results and rerun, and the hash won't match the earlier run — so "we predicted this all along" is checkable rather than assertable.

This is optional and empty by default. It matters most for clinical and behavioral work, where the confirmatory/exploratory distinction is the difference between a reportable study and an unpublishable one.

---

## Studies: what a paper reports

A paper reports several runs — a main result, sensitivity analyses, an ablation — and no single `run.yaml` names that set. A **study** is that entity. The important question is where it lives, and the answer is: **not in the code repository.**

### Why not in the repo

A study is one author's claim, assembled from runs that happened on one machine. The repo is shared machinery that many people clone, run, and contribute to. Putting a study inside it re-couples the two things the rest of this design keeps apart:

- **A cloner gains almost nothing from it.** They can already reproduce a result from a `run.yaml` handed to them directly, and the paper already carries the numbers. What they'd get is someone else's results sitting in their working tree.
- **It doesn't survive collaboration.** If two authors each run the experiment, whose study is in `study.yaml`? Results are not mergeable, and a shared file that accumulates one author's runs is a conflict waiting to happen.
- **Dependencies must point one way.** A `run.yaml` names the repo commit; the repo never names its runs. A study names runs; runs never name their studies. Committing a study inverts that — the shared, long-lived thing would reference the personal, point-in-time thing.

So a study is a **publication artifact, sibling to the paper**, not part of the machinery. It belongs wherever you keep the manuscript, or in a data repository as supplementary material.

### Building one

```bash
publishable study new ~/papers/rank-correlation/study --title "Rank correlation methods for cohort triage"
publishable study add ~/papers/rank-correlation/study /secure/results/cohort-pilot/latest/run.yaml --as main
```

```
~/papers/rank-correlation/study/          # outside every experiment repo
├── study.yaml
├── main.run.yaml                         # copied, host paths redacted
├── sensitivity.run.yaml
└── ablation.run.yaml
```

```yaml
# study.yaml
title: "Rank correlation methods for cohort triage"
authors: ["Kyungjoon Lee"]
code:
  remote: git@github.com:your-org/my-study.git
  commit: 4f9a2c1e...                     # the run added as `main`; what to cite
runs:
  main:        {file: main.run.yaml,        run_id: run_2026-08-06T14-02-11Z_8e21ab3}
  sensitivity: {file: sensitivity.run.yaml, run_id: run_2026-08-07T09-14-03Z_8e21ab3}
  ablation:    {file: ablation.run.yaml,    run_id: run_2026-08-07T16-40-12Z_8e21ab3}
```

**`code.commit` is one commit and a study's runs need not share one**, so it names a specific run's: the one added `--as main`, or the first one added if none is. Each bundled `run.yaml` still carries its own `provenance.git.commit` and `code_hash`, which is where a per-run answer lives — `code` is the citable pointer a reader follows from the paper, not a claim that every run came from it. A sensitivity analysis rerun a month later at a later commit is ordinary, so `study add` prints a notice when a run's commit differs from `code.commit` rather than refusing; what it refuses is a **name already in the bundle**, since `main.run.yaml` silently becoming a different run is exactly the overwrite [append-only](design-principles.md#design-goals) forbids, and a bundle beside a manuscript is the last place to allow it. Re-add under a new name, or start a new bundle.

The bundle is self-contained and device-independent: every reference is relative, `run_id` is a label rather than a locator, and nothing resolves through the original output storage. Zip it, attach it as supplementary material, or deposit it and cite the DOI. `publishable report study.yaml` renders it offline, cross-checking that runs claiming the same code really share a `code_hash` — and the same for [`provenance.apparatus.hash`](#the-apparatus-core-can-only-observe), since "these runs used one deployment" is a claim a paper makes and a bundle can check — flagging any [draft](#draft-runs) runs, and collecting every declared [hypothesis](#pre-registration) into one table.

Because the bundle carries `code.commit`, a reader goes from paper → study → the exact repo state, and from any included run record straight to [`publishable reproduce`](#reproducing-on-another-device). The chain is complete without the repo knowing any of it happened.

### What `study add` redacts

Everything host-identifying, not just the obvious paths:

| Field | Why |
|---|---|
| `data.input_dir`, `data.output_dir` | Absolute paths that can encode a cohort name or storage layout |
| `provenance.git.repo_root` | A path that usually contains a username |
| `provenance.environment.hostname` | A node name often identifies an institution on its own |
| `provenance.input_manifest` (path) | Points into governed storage |

Each is replaced with a marker recording that a value existed and was removed, so a reader can distinguish "redacted" from "never captured." The corresponding *hashes* stay — `input_manifest_hash` survives even though the path doesn't, so data is still verifiable by anyone holding it without the record disclosing where it lives.

None of this disturbs verification: `parameters_hash` [never covered the path fields](#three-hashes), and `code_hash` covers `src/**` and `templates/**` only.

**This table redacts host identity, and says nothing about participant identity — `allocation.json` is where that gap shows.** It is the one run-directory artifact that is a list of unit identities — "which patients were in the treatment arm" — and this section, and the table above, have never named it. `study add` is [not yet built](#package-layout), so what follows is a reading of the shape [§ Building one](#building-one) already commits to, not a checked fact: its command block adds a run by a `run.yaml` *path* rather than a run directory, and its file tree shows the bundle holding that file and `study.yaml` — run records, never a copy of a run directory. On that shape, `allocation.json` never travels and there is nothing of it in the bundle for this table to scrub; `provenance.allocation` and `provenance.allocation_hash`, the two fields of it that do reach `run.yaml`, are a bare filename and a hash, neither disclosing membership. Whether a bundle should ever be allowed to carry `allocation.json` itself — for a reader who wants to verify the split, not just trust the hash — is a question this slice leaves open for whichever slice builds `study.py`.

**One thing redaction can't do is judge your metrics.** Aggregates are usually safe, but a per-subgroup result over a handful of units can be disclosive in ways no automatic rule catches. `study add` prints any reported metric whose `n.completed` falls below `limits.min_reported_n` — or, for a [`basis: repeats`](#the-unit-table-is-the-inference-base) metric, its repeat count, and for a [reported `Estimate`](#estimate-carries-your-interval-without-core-claiming-it) the `n` it declared — and asks you to confirm — a prompt for your judgment, not a guarantee. An `Estimate` that declared no `n` is listed too: core has nothing to compare, and an interval without a denominator is the case the prompt exists for.

---

## CLI reference

### Creation commands

These take a name plus what's needed to bring something into existence.

**The `Status` column — carried by this table, by [Operation commands](#operation-commands), and by [Generators](#generators) — says what this build executes, and nothing else.** A row marked `NOT BUILT` is specified here and not yet implemented; invoking it prints that it is specified but not built and cites the section that specifies it, rather than `unknown command`, which is reserved for a name this document never specified — the two are different news, and telling them apart is what the column is for. Both exit `2` — see [Exit codes and diagnostics](#exit-codes-and-diagnostics). The rows stay in present tense because this document leads the code, the same reason [an unbuilt declaration](#the-one-config-file) keeps its expansion and [an unbuilt import](#the-importable-surface) keeps its row; the marker is what stops a reader taking the tense for a build fact. `tests/test_cli.py` reads these three tables and checks both directions against the CLI, so a marker that outlives its slice fails a test rather than misleading a reader.

| Command | Status | Arguments | Does |
|---|---|---|---|
| `publishable demo` | NOT BUILT | *(none)*, `[--into DIR]` | Builds a complete worked example — synthetic units, a three-step pipeline, a sweep with a baseline — then walks you through validating and running it one command at a time. Data goes outside the created repo, as it would for real work. See [What `demo` walks you through](#what-demo-walks-you-through) |
| `publishable new` | built | project name, `[--license]` | Scaffolds an experiment repo with README/LICENSE/CITATION.cff, `git init` + first commit |
| `publishable plugin new` | NOT BUILT | plugin name | Scaffolds an installable template/resolver/step package |
| `publishable generate` (`g`) | built | generator, name, generator args | `experiment` \| `step` \| `template` \| `report` (NOT BUILT); `experiment` recognizes no `--plugin` flag yet: `_dispatch_generate` parses any `--key value` pair and silently drops every one it doesn't read, `--plugin` included, the same as `--nonsense-flag` (NOT BUILT) |
| `publishable init` | built | `--template`, `--name`, `--input-dir`, `--output-dir`, `[--plugin]` | Alias for `generate experiment` |
| `publishable study new` | NOT BUILT | bundle path, `--title` | Creates an empty study bundle, outside any experiment repo |
| `publishable study add` | NOT BUILT | bundle path, run.yaml path, `--as <name>` | Copies a run record into the bundle under that name, with host paths redacted |

### Operation commands

These take paths and nothing else.

| Command | Status | Argument | Does |
|---|---|---|---|
| `publishable validate` | built | config path | Every check in [Validation](#validation). Reads your config and your input; creates nothing and reaches nothing off the machine |
| `publishable dry-run` | NOT BUILT | config path | Validates, expands the sweep and repeat plan, builds the input manifest, [probes the apparatus](#the-apparatus-core-can-only-observe), prints every artifact path that *would* be written. Creates nothing |
| `publishable run` | built | config path | The real thing: requires a clean `src/**` and `templates/**`, creates `run_<id>/`, captures provenance, executes conditions × repeats × steps, writes `run.yaml` |
| `publishable draft` | NOT BUILT | config path | Same as `run`, but permits a dirty code tree. Recorded as `draft: true` — see [Draft runs](#draft-runs) |
| `publishable resume` | NOT BUILT | run directory | Continues an interrupted run in place, skipping completed (condition, repeat, step) triples. Refuses a run that already holds a `run.yaml` — that run [ended](#what-status-means-and-when-a-run-keeps-going) — and one whose [lock is held](#one-execution-at-a-time-and-what-holds-the-run-directory) |
| `publishable report` | NOT BUILT | run.yaml or study.yaml path | Renders Markdown/HTML from one run, or from a whole [study](#studies-what-a-paper-reports) |
| `publishable freeze` | NOT BUILT | run directory | Re-reads the environment and re-probes the [apparatus](#the-apparatus-core-can-only-observe) mid-run, without executing anything. Reports a moved apparatus as a failure; the [gate](#the-apparatus-core-can-only-observe) is what stops the run — see below |
| `publishable reproduce` | NOT BUILT | run.yaml or config path | Clones the recorded commit into a new checkout and prepares it to run — see [Reproducing on another device](#reproducing-on-another-device) |
| `publishable diff` | NOT BUILT | two config or run paths | Reports each hash as identical or differing, then the specific parameter deltas |
| `publishable docs` | NOT BUILT | *(none)* | Regenerates every `publishable:begin/end` managed region |
| `publishable list-templates` | NOT BUILT | *(none)* | Registered templates, including plugin-provided, with their full parameter specs |

`resume` takes a run *directory* rather than a config path: resuming operates on a run that already exists, and that run directory already contains the config it used. A config plus a run identifier would be two arguments describing one thing, with the standing possibility of disagreeing. It is the one command that can't take a `run.yaml`, and for the same reason — the runs it exists for don't have one yet.

**`freeze` reports a moved apparatus; it doesn't decide.** It executes nothing, so it has no execution to fail and no business changing a run's status — it appends the probe to the ledger and reports the difference as a failure rather than a note. Appending that one line is the only thing it writes: `environment/` was captured at run start and is [never rewritten](#one-execution-at-a-time-and-what-holds-the-run-directory), so a moved lockfile is reported too and changes nothing on disk. That's also what makes it the one command safe to point at a run [holding its own lock](#one-execution-at-a-time-and-what-holds-the-run-directory), which is the only situation it's for. The next execution's [gate](#the-apparatus-core-can-only-observe) is what stops the run, and it will. What `freeze` buys is *when* you find out: on a run scheduled over days, between blocks is the natural moment to look, and learning that a revision moved an hour before the next batch is worth more than learning it as that batch dies. A read command that warned quietly would waste the only thing it's good for.

### Exit codes and diagnostics

Every command is scriptable, so what it returns is part of the interface:

| Code | Means |
|---|---|
| `0` | Succeeded. Warnings may have been printed; a warning never changes the code |
| `1` | The thing you asked about is wrong — a config that fails [validation](#validation), a `diff` of runs that don't share a hash, a `resume` whose hashes moved |
| `2` | The invocation is wrong — unknown command, a [specified-but-unbuilt](#creation-commands) command or generator, missing argument, unreadable path |
| `3` | **`run`, `draft`, `resume` only** — the run reached the end of its plan with failures: [`status: partial`](#what-status-means-and-when-a-run-keeps-going). There is a record, and it is worth reading |
| `4` | **`run`, `draft`, `resume` only** — the run stopped: `status: failed`. There is a record of what happened and no result to report |
| `5` | Something outside the machine refused — an unreachable [apparatus](#the-apparatus-core-can-only-observe), a missing credential, a clone or `uv sync` that failed |

**`partial` and `failed` get different codes because the whole point of separating them is that one is reportable.** Collapsing both into "didn't complete" would hand a script the same number for a run whose results belong in a paper and one that has none, which is exactly the judgement the two statuses exist to record. A pipeline that archives on `3` and pages on `4` is the shape this is for.

Both belong to the commands that execute. **`report` of a `partial` run exits `0`** — it was asked to render a record and it rendered one, with the failures shown. A reader learns the run was partial from the report, which is where that belongs, not from the exit code of the command that printed it. `5` is separate from all of them because it is the class you retry, and the others are not — **so when both apply, `5` wins.** A run stopped by an [unreachable probe](#what-status-means-and-when-a-run-keeps-going) writes `status: partial` and exits `5`: the status says what the record contains, the code says what to do about it, and those are different questions. A script keying on `3` archives a finished-with-failures run; the same script shouldn't archive one whose apparatus was merely offline for an hour.

**`dry-run` runs its phases in cost order and stops at the first that fails**, which is what decides its code: validation, then the input manifest, then the [apparatus probe](#the-apparatus-core-can-only-observe). So a config with an error exits `1` without ever reaching the probe, and only a config that validates gets as far as a `5`. That ordering is the point of the command — the cheap objection should never be reported second, behind a metered request that was going to fail anyway.

**`validate` collects rather than stops.** It reports every error and warning it can find in one pass, because the alternative is a fix-one-rerun loop over a file with four typos in it. Findings are grouped by the check that produced them, not by where in the config the offending value sits. A config with three mistakes in one block reports them together, which is the grouping a reader fixing that block wants; a strict document order would interleave unrelated checks. Only a failure that makes later checks meaningless is fatal on its own — a config that won't parse, a template that isn't installed, an experiment package that won't import — and those say so instead of reporting a hundred downstream consequences.

**Each diagnostic carries a stable identifier**, printed beside it and usable to grep, suppress in a reviewer's checklist, or cite in an issue:

```
configs/cohort-pilot/config.yaml
  error   E-PARAM-UNKNOWN     parameters.analysis.min_sample
          not a parameter of template `generic` — did you mean `min_samples`?
  warning W-STATS-FAMILY      statistics.correction
          6 conditions × 3 metrics is a family of 15 with `correction: none`
2 problems (1 error, 1 warning)
```

The identifier is part of the contract and outlives the wording: a message gets clearer over time, and something that pinned the wording would break when it did. It's one namespace rather than two — the `E-` codes the [errors core raises](#errors-core-raises) carry and the ones [`validate` reports](#errors-validate-reports) are drawn from the same vocabulary, since a run-time failure and a pre-flight one are equally worth grepping and there is no reader for whom they are different languages. They are written as two tables because a raise and a printed finding are documented by different things — what raises it, versus what reports it — and not because a code belongs to one or the other; nothing keys on which table a code is listed in. There is no `--json`, because [an operation command takes paths and nothing else](design-principles.md#everything-is-in-the-file) and a flag that switches the output format is still a flag. The identifier is what a tool should key on, and it is equally stable in the output there is.

A local filesystem failure — an unwritable `output_dir`, a full disk — is reported as `E-IO-FAILED` and exits `1`. It is not a `ContractError`: nothing in your declarations asked for it, and no `except` in a step improves it. **A creation command refusing to overwrite an existing file exits `1` for a related reason** — [creation commands take arguments](#creation-commands), and refusing is how one stays safe to re-run. It's one rule shared by every generator with something to protect, not a rule per file it writes: `publishable new` reports `E-PROJECT-EXISTS`, `generate experiment` reports `E-EXPERIMENT-EXISTS`, `generate step` reports `E-STEP-EXISTS`, and `generate template` reports `E-TEMPLATE-EXISTS`. `E-ARTIFACT-EXISTS` is a different thing wearing a similar name — [`io.write`/`io.path` onto a target `run` is already writing to](#errors-core-raises), not a creation command refusing to start, and it carries `ArtifactExistsError` rather than joining this family.

### Draft runs

Iterating on code means running before committing, and that needs a name rather than a flag. An `--allow-dirty`-style flag would read as "suppress a warning," which invites reflexive use; `publishable draft` reads as what it is — a provisional run whose code state isn't reachable from any commit.

Draft runs are recorded with `draft: true` and `git.code_dirty: true`, `report` refuses to render one as a final result, and `diff` labels it. Everything else behaves normally, so iteration stays fast — you just can't accidentally cite one.

### What `demo` walks you through

The one thing `demo` can give a newcomer that they can't easily get themselves is **data in the right format**. Everything after that is the CLI they have to learn anyway, so `demo` hands over the data and then walks them through the real commands rather than running them out of sight.

Six stops. Stops 3 through 5 each have the same beat: print the next command exactly as you would type it, wait, run it on `Enter`, then say in two or three lines what its output meant.

| Stop | Runs | The point of the stop |
|---|---|---|
| 1 | *(`demo` itself)* | Writes 240 synthetic units to `~/publishable-demo-data/input/`, scaffolds `src/correlation_pilot/` and `configs/correlation-pilot/config.yaml`, then `git init` and a first commit. Explains why the data is [outside the repo](#why-not-in-the-repo) |
| 2 | *(`demo` prints a file)* | Shows this config's `sweep` and `replication` blocks verbatim — the whole description of what is about to run |
| 3 | `validate` | Reads the config and the input, creates nothing, reaches nothing off the machine |
| 4 | `dry-run` | 3 conditions × 5 repeats = 15 executions, and every artifact path that *would* be written. Still creates nothing |
| 5 | `run` | The results table: estimates, [intervals over units](#the-unit-table-is-the-inference-base), paired deltas against the baseline |
| 6 | *(nothing — `demo` prints a command)* | Opens the `run.yaml` this all produced and shows the `reproduce` invocation a collaborator would run against it. Hands off to [`publishable new`](#scaffolding-publishable-new) |

Stop 2 invites you to read the config, not to edit a step. That asymmetry is deliberate: `code_hash` covers [`src/**` and `templates/**`](#three-hashes), so a step edited at stop 2 would dirty the tree and make stop 5 refuse — the first `run` a user ever issues would be an error. A config edit costs nothing but a different `parameters_hash`.

**Stop 6 is the one stop that doesn't execute what it prints.** [`reproduce`](#reproducing-on-another-device) reads `provenance.git.remote` and clones it, and the demo repo has one local commit and no remote — so running it here would fail on the first step, in the last thing a new user sees. Printing it is also the truer lesson: `reproduce` is what someone *else* runs, on a machine that has neither your data nor your credentials.

**No pause may alter the config.** Every prompt is proceed-or-quit; nothing asks which method to sweep or how many repeats to use, and the config written at stop 1 is the config executed at stop 5. The reasoning is [Everything is in the file](design-principles.md#everything-is-in-the-file) — a prompt that reached the run without passing through the file would be a parameter flag in disguise.

**Unattended, it doesn't pause.** With no terminal attached — piped, redirected, or in CI — `demo` runs the identical sequence straight through. That is not a mode and takes no flag, because the pause changes presentation only; there is nothing for a second command name to distinguish.

**Quitting is expected.** `q` at any stop prints the remaining commands in order, so you leave holding the whole path, and running `publishable demo` again from the demo directory resumes at the stop you left.

**What tracks the position is `.demo-progress`**, in the demo repo root, listed in the generated `.gitignore`. A file is needed because `validate` and `dry-run` create nothing, so the filesystem alone can't tell stop 3 from stop 4. It sits outside `src/**` and `templates/**`, so it can never move `code_hash`, and being ignored it can never dirty the tree and push you onto [`draft`](#draft-runs). `--into DIR` chooses which directory all of this applies to: given one that already holds a `.demo-progress`, it resumes there rather than starting over — resuming is a property of the directory, not of how you named it.

---

## Scaffolding: `publishable new`

```bash
publishable new my-study
```

```
my-study/
├── README.md                # generated, ready to ship — see below
├── CITATION.cff             # generated; how to cite this work
├── LICENSE                  # MIT by default; --license to change
├── pyproject.toml           # uv project, publishable pinned, src layout
├── uv.lock
├── .git/                    # git init + first commit
├── .env.example             # credential variable NAMES only
├── .gitignore               # .env, __pycache__ — nothing data-related
├── src/                     # one package per experiment            → code_hash
├── templates/               # this project's own template classes   → code_hash
├── configs/                 # one config.yaml per experiment — freely editable; commit or not, your call
├── tests/
└── docs/
```

There's no `data/` or `results/` directory; input and output live outside the repo. Because the layout is fixed, core doesn't need `--repo` or `--templates-dir` flags.

### The generated README

The scaffold writes a real README, not a placeholder. This one matters more than most, because **the repo is the reproducibility artifact** — it's what a reviewer clones. It arrives already correct for this project and stays correct as experiments are added:

````markdown
# my-study

<!-- publishable:begin overview -->
A `publishable` experiment repository. Code, parameters, and provenance are
separated by construction: this repo holds code and configs; input and output
data live outside it, under paths each config names.
<!-- publishable:end overview -->

## Setup

```bash
uv sync
cp .env.example .env    # then fill in the values below
```

<!-- publishable:begin credentials -->
### Required credentials

| Variable | Needed by |
|---|---|
| _(none yet — added as experiments declare them)_ | |
<!-- publishable:end credentials -->

<!-- publishable:begin experiments -->
## Experiments

| Name | Template | Run |
|---|---|---|
| _(none yet — add one with `publishable generate experiment`)_ | | |
<!-- publishable:end experiments -->

## Reproducing a published result

Every result from this repo is reported as a `run.yaml`. Given one:

```bash
uv run --with publishable publishable reproduce run.yaml
```

That clones this repo at the exact recorded commit, restores the locked
environment, and writes out the config that produced the result. It then tells
you the two things you must supply yourself — your own `.env` and your own copy
of the data — before you run it. Core transmits neither.
````

The `<!-- publishable:begin ... -->` regions are **managed**: a generator that populates one leaves everything outside it untouched. `generate experiment` adding a row to the experiments table, and merging any new `required_env` into the credentials table, are both [NOT BUILT](#generators) — the same half `generate template`'s parameter table shares. `required_env` no longer compounds that gap the way it once did: `BaseTemplate.required_env` is read at `validate` (see [Secrets & credentials](#secrets--credentials)), so the reader half of this is built. The merge still has nothing to read from, though — the credentials region itself is specified but its emission into a generated README is [NOT BUILT](#generators), so `generate experiment` has nothing to merge into yet, which is filed separately in the development record. A parameter table's gap is different in kind — the scaffolded README shown above declares no managed region for one at all, so there is nowhere for `generate template` to write it even once it touches the README. Most scaffolding tools write a README once and leave it; here the README is meant to be part of what a reviewer reads to reproduce the work, which is why closing these is worth doing rather than working around.

`publishable docs` regenerates every managed region on demand — useful after editing a template's `parameter_spec` or `required_env`.

`CITATION.cff` is scaffolded because the eventual output of this repo is usually a paper, and the moment to record authorship is when the project starts, not when a reviewer asks.

---

## Generators

| Generator | Status | Example | Creates |
|---|---|---|---|
| `experiment` | built | `publishable g experiment cohort-pilot --template generic --input-dir ~/data --output-dir ~/results` | A fully-populated `configs/cohort-pilot/config.yaml`, `src/cohort_pilot/` (thin `experiment.py` declaring step order, plus `steps/` with one **working** starter step). Refuses if either path resolves inside the repo. Adding a row to the README's managed experiments table is NOT BUILT — the same half `generate template` does not write either. `--plugin` is accepted and dropped: the flag parses, nothing is installed, and `plugin:` is written `null` — NOT BUILT, and the [`plugin` field](#the-one-config-file) is a readable note rather than an install instruction in either case |
| `step` | built | `publishable g step cohort-pilot analyze` | Next-numbered `src/cohort_pilot/steps/step03_analyze.py` with a `BaseStep` stub, registered in order |
| `template` | built | `publishable g template my_assay` | `templates/my_assay.py` with a `BaseTemplate` + `parameter_spec` stub, for a template only this project needs. Refuses if that file already exists, and takes a name `templates/<name>.py` can be imported under and not one prefixed with `__`, which [discovery skips](#templates-where-parameters-are-defined). Adding its parameter table to the README is NOT BUILT: the scaffolded README carries no managed region for one |
| `report` | NOT BUILT | `publishable g report cohort-pilot --format html` | `src/cohort_pilot/report.py` — a renderer override for one experiment; see below |

```python
# src/cohort_pilot/experiment.py — order, nothing else
from publishable import BaseExperiment
from .steps.step01_load_cohort import Step as LoadCohort
from .steps.step02_fit_model import Step as FitModel
from .steps.step03_analyze import Step as Analyze
from .steps.step04_compare_methods import Step as CompareMethods

class CohortPilotExperiment(BaseExperiment):
    # Order, nothing else. Each step declares its own scope; core derives
    # the execution plan from that. Reordering here IS reordering the pipeline.
    steps = [LoadCohort, FitModel, Analyze, CompareMethods]
```

**`entrypoint` names that class, and it is an ordinary Python import path** — `<module>:<attribute>`, resolved with the project's own environment on `sys.path`. Because [`new` scaffolds a src layout](#scaffolding-publishable-new), `src/` is not a package and does not appear in it: the experiment generated into `src/cohort_pilot/` is `cohort_pilot.experiment:CohortPilotExperiment`. `generate experiment` writes the line, and nothing but a hand-edit changes it.

It resolves at `validate`, not at `run`, because the execution plan is a property of classes core has to have imported to see: how many executions each step gets, which artifact paths [`dry-run`](#before-you-spend-it) prints, and which scope each `io` will be built for. So an experiment package that fails to import fails `validate`, with the import error as the message. That is also the one thing `validate` executes: importing a module runs its top level, so a step module that opens a connection or reads a file at import time does so during a command documented as creating nothing. Keep step modules import-clean and put the work in `run`.

### A report override renders one experiment's own figures

`publishable report` renders any run without configuration — the condition table, the deltas, the hypothesis verdicts, the attrition. What it can't produce is the figure your paper actually needs, because that is domain work. `generate report` writes a subclass into your repo for it:

```python
# src/cohort_pilot/report.py — generated
from publishable import BaseReport

class Report(BaseReport):
    format = "html"                             # html | markdown — `--format` seeds this line

    def sections(self, run, io):
        yield from super().sections(run, io)    # the standard blocks, in order
        yield self.section("Method agreement",
                           body=render_scatter(io.read_condition(...)))
```

`run` is the parsed `run.yaml` and `io` is the same read-only accessor a [`summary` step](#steps-that-need-every-condition) gets, so an override can reach any condition's artifacts. `generate report`'s `--format` writes that attribute and does nothing else — the class is the source of truth from then on, exactly as `--input-dir` seeds a config field it doesn't afterwards own. It **adds and reorders sections; it cannot change a number** — the values it renders come from `results`, which core computed and [attributed](#estimate-carries-your-interval-without-core-claiming-it) before the renderer existed. That's the same line [`aggregate`](#templates-where-parameters-are-defined) sits on, one stage later: a renderer decides what a reader sees, never what the record says.

It lives in `src/**` rather than in a plugin because it is one experiment's presentation, so [`code_hash` covers it](#three-hashes) — a figure is a claim, and the code that drew it belongs under the same commit as the analysis. A renderer several experiments share is an ordinary import from a plugin, called by each one's override.

### The starter step runs

`generate experiment` writes a first step that works rather than one that raises `NotImplementedError`. It counts the units it was given, writes them out, and returns that count as a metric:

```python
# src/cohort_pilot/steps/step01_summarize_units.py — generated, and runnable as-is
from publishable import BaseStep

class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        units = list(io.units)
        for unit in units:
            io.record(unit.key, {"present": True})
        return {"n_units": len(units)}          # TODO: replace with your analysis
```

Trivial, but it means `publishable run` succeeds immediately after scaffolding. You get a real `run.yaml`, a real artifact tree, and a real set of provenance hashes before writing a line of your own code — so the shape of the whole loop is visible while you're still deciding whether to adopt it. Replace the body when you're ready: the `TODO` marks the only line that *must* change, and a real pipeline usually renames the file and picks its own [scope](#step-scope) besides — the worked example's first step is `step01_load_cohort` at `scope = "run"`, which is what loading a cohort once should be.

**What "immediately" presumes is the `data.units` block `init` wrote** — a table at `input_dir/index.csv` whose key column is the one the config names — since [`io.units` raises when no units are declared](#steps-and-artifacts) and `validate` fails when they don't resolve. Input shaped some other way means editing that one declaration first, which is [one line and one `validate` away](#where-units-come-from); a pipeline with no unit table at all edits the step too, which is the `TODO` it already carries.

**It's generated rather than imported from core, and that's the point.** Core could export this step and let a config name it, which would spare the generating entirely — but [`code_hash` covers your repo's `src/**` and `templates/**`](#three-hashes), so an imported pipeline is a pipeline outside the hash that claims to cover it. Writing the file into your repo is what keeps the analysis under your commit. See [Core vs. plugin](design-principles.md#core-vs-plugin) for where that line falls and what may still be added on core's side of it.

---

## Plugins: where domain knowledge lives

```bash
uv run publishable generate experiment triage-pilot \
  --plugin someuser/publishable-llm \
  --template llm_diagnostic \
  --input-dir /secure/phi-data/xray-2026 --output-dir /secure/results/triage-pilot
```

`--plugin <github-username>/<repo>` runs `uv add git+https://github.com/<user>/<repo>` and nothing more — **NOT BUILT** in this build, where the flag parses and is dropped. No registry, no bespoke installer, no new trust boundary beyond "this is a git dependency," because it is one. Pin however `uv` supports: `--plugin someuser/publishable-llm@v1.2.0`.

A flag here rather than a field in the file is not the exception it looks like: [operation commands](#operation-commands) take paths and nothing else, and `generate` is a **creation** command — the file it would read does not exist yet, which is the whole distinction that rule draws.

This pays off twice. The plugin becomes a normal `pyproject.toml` line and a pinned `uv.lock` entry — the same lockfile captured as provenance — so `reproduce` gets the exact plugin version free, without core inventing its own pinning story. And plugins ship reusable `BaseStep` subclasses, [unit resolvers](#where-units-come-from), and [apparatus probes](#the-apparatus-core-can-only-observe), not just templates, so shared machinery is importable rather than copy-pasted.

### Creating a plugin: `publishable plugin new`

This scaffolds a standalone installable package rather than an experiment repo, and like `publishable new`, it ships a README you could publish as-is:

```
publishable-my-assay/
├── README.md                 # generated, with a parameter table derived from the spec
├── LICENSE
├── CITATION.cff
├── pyproject.toml            # declares the publishable.templates entry point
├── uv.lock
├── .git/
├── src/publishable_my_assay/
│   ├── templates/my_assay.py     # BaseTemplate + parameter_spec, @register_template applied
│   ├── resolvers/                # optional unit resolvers, @register_resolver applied
│   ├── probes/                   # optional apparatus probes, @register_probe applied
│   ├── writers/                  # optional artifact writers, @register_writer applied
│   └── steps/                    # optional reusable BaseStep subclasses
├── tests/
│   └── test_my_assay.py          # asserts the template materializes and validates
└── examples/
    └── my_assay/config.yaml      # a filled-in config, generated from the spec
```

```toml
[project.entry-points."publishable.templates"]
my_assay = "publishable_my_assay.templates.my_assay:MyAssayTemplate"

[project.entry-points."publishable.resolvers"]
plate_wells = "publishable_my_assay.resolvers.plate:resolve"

[project.entry-points."publishable.probes"]
assay_instrument = "publishable_my_assay.probes.instrument:probe"

[project.entry-points."publishable.writers"]
".fastq.gz" = "publishable_my_assay.writers.fastq:write"

[project.entry-points."publishable.readers"]
".fastq.gz" = "publishable_my_assay.writers.fastq:read"
```

**Five registries, one mechanism.** Templates, [resolvers](#where-units-come-from), [probes](#the-apparatus-core-can-only-observe), [writers and readers](#steps-and-artifacts) are each an entry-point group and a `@register_*` decorator, and `validate` reports a config naming one that no installed package registers — templates are the one registry where that's not the whole check, since a name can also resolve against [the project's own `templates/`](#templates-where-parameters-are-defined); [§ Errors `validate` reports](#errors-validate-reports) states the row in full. A writer is keyed by the extension it claims rather than by a name, since that is what [`io.write` dispatches on](#steps-and-artifacts) — it takes the object and returns `bytes`, and its reader inverts it — which is a fifth group rather than a convention, because [`io.write` dispatches on the writer table and `io.read_upstream` indexes the reader table](#steps-and-artifacts), so a suffix present in one and absent from the other is a promise core cannot keep. That asymmetry is not refused at registration — a check there would have to know whether the reader is merely registered later in the same module, which it cannot — but at the read, and only in the direction dispatch can see: `io.write` decides the suffix from the writer table alone, so `io.read_upstream` and its siblings meet a suffix `WRITERS` holds and `READERS` does not as an [`ArtifactError` under `E-ARTIFACT-UNREADABLE`](#errors-core-raises), a different mechanism, a different time, and a different code from the registration-time `ContractError` a writer claiming a suffix core itself writes raises under [`E-PLUGIN-COLLISION`](#errors-core-raises). The reverse — a suffix `READERS` holds and `WRITERS` does not — is invisible to that same dispatch and reads back as raw bytes rather than through the registered reader, deliberately: nothing in this process ever wrote that suffix, so there is no broken pair to refuse.

**The entry point is the registration; the decorator is a declaration checked against it.** The name a config writes is the entry-point key, and core resolves it from installed package metadata — so `validate` can answer "no installed package registers `plate_wells`" without importing a line of that package, which matters because [importing a module runs its top level](#generators) and `validate` is documented as creating nothing and reaching nothing. The `@register_*` argument is what makes the artifact findable in its own test suite and readable in its own source; when the two disagree, loading the plugin fails naming both, rather than one of them silently winning. That's the [defaults-file argument](#there-is-no-separate-defaults-file) again: two spellings of one name, and no rule for which is canonical, is a drift nobody detects until a config names the loser.

**Two things register without an entry point, and neither is a plugin.** Core's own `generic` is core's to register. A [local `templates/*.py`](#templates-where-parameters-are-defined) is found by path, from the [fixed layout](#scaffolding-publishable-new) that already lets core find things without being told — it isn't installed, isn't distributed, and is pinned by [`code_hash`](#three-hashes) rather than by `uv.lock`, so there is no package metadata for it to declare itself in. Its `@register_template` argument is therefore the whole of its registration, which is the one case where the decorator is authoritative rather than checked.

That authority costs the guarantee two paragraphs up: an entry-point name is resolved from package metadata without importing a line of the package, but a local file's name lives only in the decorator argument, so `validate` can learn it only by importing the file — and because a collision between two local templates is only detectable between files a config never mentions, discovery is eager, importing **every** non-`__`-prefixed file under `templates/`, not only the one a config names. So `validate` does import user files no config references. This is not a greenfield breach — importing is not inspecting, core still never reads the body of that Python, and it is the same line `validate` already crosses to resolve [`entrypoint`](#generators) — but it widens that exception from one named module to a whole directory.

**A name is claimed once, and a collision is refused rather than resolved.** Two installed plugins registering `plate_wells`, a plugin registering `generic`, a plugin claiming an extension core already writes, two [local `templates/*.py`](#templates-where-parameters-are-defined) files registering one name — or one such file registering it twice — and a local file taking the name of an installed one or of core's own `generic` all fail at load, naming both providers — **the installed cases arrive with entry-point resolution; today only the two local cases and the local-core shadow are checked.** Install order and import order are the only tie-breaks available, and both are properties of a machine rather than of a design — a run whose template depended on which package resolved first would be reproducible everywhere except where it mattered. Shadowing is refused in the same breath and for a sharper reason: a plugin that could redefine `generic` could change what a config means without changing the config, which is the one thing [`parameters_hash`](#three-hashes) is supposed to make impossible. Rename yours. A local provider is named as `<path>::<ClassName>`, since the file is what you rename and one file can hold two classes; core's own is named as its class, and two decorators on one class — the pair that cannot distinguish — are named once and said to be one class claiming twice. [`E-TEMPLATE-COLLISION`](#errors-validate-reports) is the code every **template** case carries and [`E-PLUGIN-COLLISION`](#errors-core-raises) is the code the other four groups carry, including a writer claiming a suffix core already writes: a template name has a second home in a project's own `templates/`, and one row cannot state both sets of providers.

**Every non-dunder-stemmed file under `templates/` is a template, and one that fails to load is a fault rather than a silence.** Discovery imports every such file to find its registration, so a file that raises while importing, imports cleanly but never calls `@register_template`, or registers something that is not a `BaseTemplate` subclass leaves `validate` with nothing it can resolve a name against — reported as [`E-TEMPLATE-LOAD`](#errors-validate-reports), naming the file, ahead of a collision for the same partial-information reason a collision is checked ahead of an unresolved `experiment_type`. A helper a template means to import as a sibling, rather than have discovered as a template in its own right, is exempt the same way `__init__.py` already is: name it with the same `__`-prefix.

The generated README documents the plugin the way a user needs it — install line, template list, and **a parameter table generated from `parameter_spec` itself**:

````markdown
# publishable-my-assay

A [`publishable`](https://github.com/your-org/publishable) plugin providing
the `my_assay` experiment template.

## Install

```bash
uv run publishable generate experiment my-pilot \
  --plugin someuser/publishable-my-assay \
  --template my_assay \
  --input-dir /path/to/data --output-dir /path/to/results
```

<!-- publishable:begin templates -->
## Templates

### `my_assay`

Convention class `wet_lab` · default repeats 3 · naming `kebab-case`

| Parameter | Type | Default | Constraints | Description |
|---|---|---|---|---|
| `instrument.model` | str | — | required | Instrument model identifier |
| `instrument.gain` | float | 1.0 | > 0 | Detector gain multiplier |
| `instrument.vendor` | str | `vendor_a` | choices: vendor_a \| vendor_b | Which vendor's API the readings come through |

**Required credentials:** `INSTRUMENT_API_TOKEN`; `VENDOR_B_TOKEN` when `instrument.vendor: vendor_b`

**Apparatus probe:** `assay_instrument` — records `model`, `firmware`, `calibration_id`, `reagent_lot`
<!-- publishable:end templates -->
````

Note what is *not* in that parameter table: the **calibration run this assay is traceable to.** It's a fact about the instrument at the moment of the run, so it's [apparatus provenance](#the-apparatus-core-can-only-observe) rather than a parameter — read from the instrument instead of typed into a config, and outside `parameters_hash`, so recalibrating doesn't read as redesigning the experiment. The rule for the boundary is short: if you decide it, it's a `Param`; if you can only observe it, it's an apparatus fact.

This is the same principle as `init` materializing a config: `parameter_spec` is the single source of truth, so the documentation is *derived* from it rather than maintained alongside it. Add a parameter and run `publishable docs` — the table, the example config, and newly-initialized configs all update together. Documentation that can't drift is the only kind worth generating.

Publishing is "push to GitHub" — that's all `--plugin owner/repo` expects.

---

## Secrets & credentials

Credentials are the one thing that doesn't belong in the config. A config is meant to be shared and archived, so a key in it becomes a leaked key the moment someone uses the config as intended.

**The config stores the environment variable's *name*; the value lives in `.env`.** **Core loads `.env` via `python-dotenv` at two moments**, never reads it into provenance, and gitignores it in every scaffold. [`validate`](#validation) loads it because some of its checks ask whether a variable is *set*, and every command that executes loads it again before any step runs, because a step is about to read one — loading is a precondition of executing rather than a side effect of checking. The load never overrides a variable already exported, so a machine supplying its credentials through a secret manager needs no file at all, and a stale `.env` cannot silently redirect a run. **This is not an exception to [`validate`'s promise](#operation-commands)**, which is that it creates nothing and reaches nothing *off the machine*: a file in the repository root is on-machine. In this build the executing site is `run`; [`draft`, `resume` and `dry-run`](#cli-reference) inherit it when each is built.

```bash
# .env — never committed
INSTRUMENT_API_TOKEN=...
```

```yaml
parameters:
  instrument:
    credential_env_var: "INSTRUMENT_API_TOKEN"   # the NAME, never the value
```

A template lists what it always needs in `required_env`, and a parameter value lists what *it* needs in [`requires_env`](#a-credential-can-belong-to-a-parameter-value); `validate` confirms each is set — the second only for the conditions a sweep actually resolves — without printing or logging it. Steps read `os.environ[cfg.parameters.instrument.credential_env_var]` normally. This is why `report` and `diff` output is ordinarily safe to send as-is: core never writes a **declared** credential's value into a record of its own. That is narrower than "nothing secret is in it" — see "The limit of that, stated rather than discovered" below for what it does not cover.

**An exception's text can carry a value by accident, and it is refused rather than tolerated.** A client library that interpolates a key into a URL in its error message is ordinary, and core turns an exception into text a reader sees in two places: a failed execution's `error`, written into both `run.yaml` and `executions.jsonl`, and a [diagnostic](#exit-codes-and-diagnostics) printed to stdout or stderr — which is how a template's `aggregate` failure, a template's `validate` raising, and an entrypoint that raises at import all reach you. Core replaces each occurrence of a credential value it read with `<redacted:VARIABLE_NAME>` at both, because the record exists to be debugged from — and it says a redaction happened rather than scrubbing silently, so a reader knows both what was removed and which variable to look at. A short or ordinary-looking value is replaced everywhere it occurs in the text, not only where it happens to name a credential — the match fails toward removing too much rather than too little. The match is by **exact value, never by pattern**: core knows what it read out of the environment, so it answers the direct question instead of guessing from a name ending `_KEY` or from how random a string looks.

**The limit of that, stated rather than discovered.** Core redacts only values it read for a **declared** variable — one named in a template's `required_env`, or in the `requires_env` of a value a condition resolves. `io` hands a step no credential, so a step that reaches `os.environ` for a name no declaration mentions holds a value core never saw and cannot match. And redaction runs only at the two constructions above — an exception's text becoming an execution's `error` or a diagnostic's message. A step that itself chooses to write a declared credential's value through `io.record` gets no help from this: core does not scrub what a step deliberately records, so that value reaches the unit table as written. Declare it, and it is covered *in an exception's text and in a diagnostic*; don't, and the redaction is not a guarantee the code can provide either way.

A template's own file failing to load or colliding with another is covered too, even though no template has resolved yet at that point: a class body finishes running before its own `@register_template` call, so a file that raises *after* that call — or a sibling file that already registered cleanly before a later one failed — still leaves a class core can read `required_env`/`requires_env` off, and that declared set is redacted into the `E-TEMPLATE-LOAD`/`E-TEMPLATE-COLLISION` finding itself. The one case that isn't: a raise from *inside* a class body, before its own `@register_template` line is ever reached, leaves no class behind to ask, and a value that reaches only that text is not matched.

---

## Naming conventions & repeat defaults

Templates encode what a field's reviewers expect. Core enforces whatever the template declares and warns rather than silently passing when a config falls below `default_repeats`.

`default_repeats` is a plain integer in every class, because core [does not compute power](experimental-designs.md#what-core-will-not-do-for-you) and a default it cannot derive would be a number pretending to be a calculation. Where a field expects an a-priori sample size, the template asks for it as a parameter — declared by you, recorded in the config, and checkable against the units actually resolved.

| Convention class | Naming | Repeat floor |
|---|---|---|
| `clinical` | `kebab-case`, includes cohort or method identifier | 3 |
| `ml_benchmark` | `snake_case`, includes dataset + method tag | 5 |
| `behavioral` | `snake_case`, includes study phase (`pilot`/`main`/`replication`) | 1; the template instead requires a target-N parameter and warns when resolved units fall below it |
| `simulation` | `dot.case`, includes the swept axis | 10 per condition |
| `generic` | `kebab-case` | 1 |

This is a floor, not a value `init` writes. A template declaring a repeat floor above what a
config asks for makes `validate` warn ([`W-REPL-FLOOR`](#warnings-core-reports)); it never edits
the config. What executes is what the config says, and what the floor buys is that a design running
below it says so in its record.

---

## Reproducing on another device

`reproduce` takes one path and no flags. It **prepares** a runnable checkout rather than running it:

```bash
uv run --with publishable publishable reproduce run.yaml
```

In order, it:

1. Reads `provenance.git.remote` and `.commit` from the file — no existing checkout needed.
2. Clones into a directory derived from the repository name and run ID (`my-study_run_2026-08-06T14-02-11Z_8e21ab3/`), and checks out that exact commit as a detached HEAD. *The only git operation, and you didn't type it.* No `--into`: the destination is derived, so it can't collide with an existing checkout and doesn't need naming.
3. Verifies the checked-out tree's `code_hash` matches the recorded one — catching a rewritten or force-pushed history.
4. Runs `uv sync --locked`, failing loudly on lockfile mismatch. Plugin versions come along automatically.
5. Writes the embedded config to `configs/<name>/config.yaml`, with `data.input_dir` and `data.output_dir` blanked and marked `# REQUIRED: set to your local copy`. When the run had an [apparatus](#the-apparatus-core-can-only-observe), it also writes `configs/<name>/apparatus.expected.json` — the recorded facts, which the first probe is checked against. `reproduce` writes that file once and never rewrites it; you may edit it, and that asymmetry is the whole design — see below.
6. Copies `.env.example` and lists the `required_env` variables that need values.
7. Prints exactly what's left to do, then stops.

```
Prepared my-study_run_2026-08-06T14-02-11Z_8e21ab3/

Before running, edit:
  configs/cohort-pilot/config.yaml   data.input_dir, data.output_dir

Then:
  cd my-study_run_2026-08-06T14-02-11Z_8e21ab3
  uv run publishable validate configs/cohort-pilot/config.yaml
  uv run publishable dry-run  configs/cohort-pilot/config.yaml
  uv run publishable run      configs/cohort-pilot/config.yaml
```

`reproduce` stops rather than running because both remaining inputs need a person — the transcript above lists only the paths because `generic` declares no `required_env`, and an experiment whose template does gets a `.env` line beside them. Core has no mechanism to transmit a secret, and it won't fetch your data — moving governed data goes through whatever protocol governs it. Given that, `--input-dir` and `--output-dir` would only duplicate what the config already expresses, so the config stays the single description of the run.

**Given a config rather than a `run.yaml`, there is nothing to clone and nothing to check against.** A config names no commit, no remote, and no recorded hash, so the first three steps have no input at all: what `reproduce` does with one is prepare the checkout it is already standing in, from step 4 onward — `uv sync --locked`, the `.env.example` copy, the list of what needs values, and the same closing instructions, with step 5 moot because the config is already where it would have been written. It cannot verify a `code_hash` and says so, rather than reporting a match it never made. That form is for the case where someone handed you a config and a repo instead of a record; the `run.yaml` form is the one that reproduces a *result*, and it is the one to prefer whenever both exist.

Verification of the input data still happens: `run` builds the manifest from whatever `input_dir` you set and compares it to the recorded one, reporting a data mismatch as loudly as a lockfile mismatch. Pointing at the wrong data is caught, just at run time rather than at clone time.

**The apparatus is verified the same way, and it has to be.** A reproduction that ran the recorded code, in the recorded environment, over the recorded data, through a *different* model revision or a recalibrated instrument is not a reproduction — and it is the one substitution that leaves every hash matching. So the first probe compares against the facts `reproduce` wrote out and fails on any difference, at the same volume as a lockfile mismatch — on the same terms the [gate](#the-apparatus-core-can-only-observe) uses everywhere else, so a fact the original run never got an answer for doesn't fail a reproduction that does get one. That asymmetry is worth reading as what it is: the reproduction pinned something the original didn't, which is more evidence rather than less.

The worked example above has no apparatus, because template `generic` declares no probe. A run that does gets a third thing to arrange, listed alongside the other two:

```
This run measured through an apparatus. Reproducing it needs:
  llm_deployment   model_revision  gpt-5.5-2026-06-11
                   api_version     2026-05-01
```

It's named in the output rather than only recorded because, unlike a path or a credential, this may take a person days to arrange — or be impossible once a provider has retired a revision. When it *is* impossible, the honest move is a new run whose record says so, not a matching one with a footnote.

**`apparatus.expected.json` is editable, and editing it is the point of naming it.** Core cannot tell a legitimately equivalent deployment from a substituted one — an institution's own endpoint serving the same revision is a different `endpoint_host` and the same apparatus in every sense that matters. So the file is a plain, readable expectation you may change, and changing it is *visible*: it sits beside the config as an untracked file the reproducing checkout didn't have before, and the run you produce records the facts you actually observed rather than the ones you claimed. That's the same posture as [`draft`](#draft-runs) taking a name rather than a flag — bypassing is available and conspicuous, instead of forbidden and therefore worked around.

---

## Package layout

`publishable`'s own source — not a generated project.

```
publishable/
├── src/publishable/
│   ├── __init__.py            # the one public import root — see "The importable surface"
│   ├── errors.py              # PublishableError and the three below it, each carrying its code
│   ├── cli.py                 # dispatch
│   ├── scaffold.py            # `new`
│   ├── plugin_scaffold.py     # `plugin new` — not yet built
│   ├── generators/            # experiment | step | template | report, incl. --plugin
│   ├── materialize.py         # renders a fully-populated, commented config from parameter_spec
│   ├── docs.py                # `docs`: regenerates managed README regions from live specs — not yet built
│   ├── readme_templates/      # the shipped README/CITATION.cff/LICENSE scaffolds
│   ├── param.py               # Param: type, default, constraints, help
│   ├── envelope.py            # the config envelope's leaf types and the closed-schema walk
│   ├── validate.py            # the value-level validation engine
│   ├── base_experiment.py     # BaseExperiment: one ordered steps list, scopes resolved from it
│   ├── base_step.py           # BaseStep: scope, run(cfg, io), self.condition/self.repeat,
│   │                          #     derive_seed, nondeterministic
│   ├── runner.py              # one execution: constructs the step, runs it, records what came back
│   ├── coercion.py            # a step's return to a flat mapping of scalars; the Estimate exemption
│   ├── artifacts.py           # io: scope-aware paths, atomic writes, append, record,
│   │                          #     read_condition, exists/resumed/recorded_keys
│   ├── sweep.py               # grid/paired/ablate/sample/groups/baseline expansion, labels, sweep.yaml
│   ├── units.py               # unit resolution (table/glob/resolver registry), keys, attributes, partitioning
│   ├── scope.py               # step scope resolution, execution plan, read-direction checks
│   ├── lineage.py             # upstream run recording and chain verification — not yet built
│   ├── hypotheses.py          # pre-registered hypothesis evaluation, confirmatory/exploratory,
│   │                          #     computed vs. reported verdict provenance
│   ├── study.py               # study new/add: bundle assembly, redaction, cross-run report — not yet built
│   ├── replication.py         # repeat kinds (seed/batch/fold), nesting, seed derivation
│   ├── stats.py               # unit-table inference, resample/null_test, deltas, effect sizes —
│   │                          #     the computation contrasts.py and strata.py resolve names into
│   ├── contrasts.py           # vs_baseline and declared statistics.contrasts, resolved to comparisons
│   ├── correction.py          # correction families: ranking, holm/bonferroni levels, corrected bounds
│   ├── estimate.py            # Estimate: an interval a summary step computed itself
│   ├── strata.py              # statistics.report_by: stratum levels off the roster
│   ├── run_identity.py        # run_<id> allocation, latest symlink, resume resolution
│   ├── hashes.py              # code_hash (src/** + templates/**), parameters_hash, digest
│   ├── config.py              # load + dot-access Config
│   ├── run_record.py          # run.yaml assembly; Estimate storage and attribution
│   ├── provenance.py          # git discovery (user repo), uv env capture
│   ├── manifest.py            # input_dir manifest build/verify, policies
│   ├── plugins.py             # entry-point metadata scan; the resolver/probe/writer/reader registries
│   ├── apparatus.py           # probe registry, per-condition facts, change gate — not yet built
│   ├── uv_support.py          # uv.lock copy/hash, --locked drift checks
│   ├── secrets.py             # dotenv loading, required_env checks (never touches provenance)
│   ├── reproduce.py           # clone/checkout/sync, then report what's left to supply — not yet built
│   ├── report.py              # BaseReport: standard sections, html/markdown, override discovery — not yet built
│   ├── diagnostics.py         # stable E-/W- identifiers, collected reporting, exit codes
│   └── templates/{base.py,registry.py,discovery.py,builtin/generic.py}
├── tests/
├── examples/generic/
└── pyproject.toml
```

**Modules marked `— not yet built` are specified and unbuilt.** The tree is a map of what core's
source will hold, and a module removed from it because today's `src/` lacks it would have to be
re-argued when its slice lands. What is built is what `src/publishable/` contains.

---
