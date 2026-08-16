# Design principles

Why `publishable` works the way it does. This is the argument behind the [reference](reference.md); read it when a rule seems arbitrary, or before proposing a change to one. For how these rules cash out across experimental designs, see [experimental-designs.md](experimental-designs.md).

## Contents

- [Design goals](#design-goals) — the whole argument in twenty lines
- [Ontology](#ontology) — the ten nouns, and the two easiest to confuse

**The rules, and why**
- [Everything is in the file](#everything-is-in-the-file) — why no command takes a parameter flag
- [Same code, different parameters](#same-code-different-parameters) — why hashes are split
- [Code and data never share a repo](#code-and-data-never-share-a-repo)
- [Whose git hash is this?](#whose-git-hash-is-this)
- [Greenfield only](#greenfield-only) — why there's no `adopt` command

**Boundaries**
- [Core vs. plugin](#core-vs-plugin) — where a feature belongs
- [What core does not promise](#what-core-does-not-promise)

---

## Design goals

Reproducibility usually fails for a boring reason: the true record of what ran is scattered across a shell history, a Slack message, a half-remembered `--temperature 0.7`, and a branch that got deleted. `publishable` forces that record into one file you write *before* the run, and one file captured *during* it.

- **Every parameter is in the config. No exceptions.** No *operation* command takes any argument other than a path — creation commands take what is needed to bring something into existence, and they are the only exception. There are no parameter flags, no selectors, no overrides that live only in a shell history. See [Everything is in the file](#everything-is-in-the-file).
- **`init` writes the whole file for you.** You don't author YAML from scratch or hunt for available options: `init` materializes every parameter the template offers, with sensible defaults and inline documentation. Editing that file *is* designing the run. See [The one config file](reference.md#the-one-config-file).
- **Code and parameters are hashed separately.** `code_hash` covers `src/**` and `templates/**`; `parameters_hash` covers everything the config declares about the run except its `metadata` and its two host paths, one hash per run. This is what makes "same code, different parameters" a provable claim rather than a hopeful one. See [Three hashes](reference.md#three-hashes).
- **Changing parameters costs nothing.** Edit, validate, run. Repeat. No commit required, because code provenance doesn't depend on the config being committed. See [Same code, different parameters](#same-code-different-parameters).
- **`validate` checks values, not just presence.** Types, ranges, choices, unknown keys — before you spend the run. See [Validation](reference.md#validation).
- **Every run gets its own identity.** Artifacts live under `run_<id>/`, so a rerun never collides with a previous one. See [Run identity](reference.md#run-identity).
- **Artifacts are append-only and atomic.** Nothing is ever overwritten or deleted; a crash mid-write leaves nothing behind rather than a half-file that blocks the retry. See [Steps and artifacts](reference.md#steps-and-artifacts).
- **Code, environment, data, and apparatus are all pinned.** Commit and a content hash of the code trees, `uv.lock` for environment, and a content manifest for input data — the third is what most tools leave open. Where measurement goes through something core can't install — a hosted deployment, an instrument — a plugin probe records its state per condition and a change fails the run. `uv.lock` pins the client; the apparatus record pins the server. See [The apparatus core can only observe](reference.md#the-apparatus-core-can-only-observe).
- **Code and data never share a repo.** `input_dir`/`output_dir` are structurally forbidden inside the git repo: code is shareable, governed data isn't, and they need different protocols. See [Code and data never share a repo](#code-and-data-never-share-a-repo).
- **Git isn't optional for code.** `new` initializes a repo, and `run` refuses when `src/**` or `templates/**` has uncommitted changes — a code hash that doesn't match what ran isn't provenance, it's a guess. Config edits don't trip this.
- **It's *your* commit, not ours.** Captured git identity always belongs to your experiment repo. See [Whose git hash is this?](#whose-git-hash-is-this)
- **`uv` is not optional.** Environments are captured and rebuilt through `uv`, so "reproduce this" means `uv sync --locked`.
- **Reproducing elsewhere shouldn't mean typing git commands.** One command clones, checks out the recorded commit, syncs, writes the config back out, and names what only a person can supply — your data and your credentials, neither of which core transmits. It stops there rather than running. See [Reproducing on another device](reference.md#reproducing-on-another-device).
- **Secrets are the one thing never captured.** Credentials live in `.env`; the config stores only variable *names*. This held by absence alone until core started reading the environment at all — now that it does, an exception's text is where a value could otherwise slip into a record, and core redacts it there by exact value rather than relying on nothing ever reading `os.environ` in the first place. See [Secrets & credentials](reference.md#secrets--credentials).
- **The unit of measurement is first-class.** Patients, samples, trials, items — declared once, and everything from fold partitioning to per-unit result tables follows from it. See [Units](reference.md#units-the-thing-being-measured).
- **The sample's own shape is declared, not assumed.** An enriched or stratified benchmark carries sampling weights, and core weights the estimate and says so in the record rather than returning an unweighted number in the same shape as a weighted one. See [Weighted samples](reference.md#weighted-samples).
- **Intervals are over units, never over executions.** `n` counts the things a claim generalizes over, so every interval core reports is computed from the per-unit table. Repeats are a variance component reported separately, because an interval across five seeds narrows as you add seeds. Where core can't compute an interval honestly, it omits it — and where your own model computed one, a `summary` step returns it as an `Estimate` and the record says you computed it rather than core. See [The unit table is the inference base](reference.md#the-unit-table-is-the-inference-base).
- **Steps declare how often they run.** Loading a cohort shouldn't re-execute once per condition per repeat. See [Step scope](reference.md#step-scope).
- **Shared work is traceable.** Consuming an earlier run's artifacts records that dependency. See [Lineage](reference.md#lineage-between-runs).
- **What you expected is recordable, not just what you computed.** The config is written and hashed before the run, which is what pre-registration means. See [Pre-registration](reference.md#pre-registration).
- **Determinism is scoped.** Core doesn't claim bit-identical reruns when a step depends on something external. See [What core does not promise](#what-core-does-not-promise).
- **The layout is fixed, so commands don't need flags.** `new` and `generate` decide where code, configs, and steps live. Because every project has the same shape, `publishable` can find things without being told — there is no `--repo`, no `--templates-dir`, no path configuration to get wrong.
- **Greenfield only.** `publishable` starts new experiments; it doesn't retrofit existing scripts. See [Greenfield only](#greenfield-only).
- **Domain knowledge is a plugin, not a patch.** See [Plugins](reference.md#plugins-where-domain-knowledge-lives).

---

## Ontology

Ten nouns, defined once. Everything else in this document is built from them, and they're chosen to mean the same thing whether you're running a solver, an assay, or a clinical comparison.

| Term | Is | Lives |
|---|---|---|
| **Study** | A set of runs reported together — what a paper reports | A bundle beside the manuscript, never in the repo |
| **Experiment** | A pipeline: code plus the parameters it accepts | `src/<name>/` + a template |
| **Config** | One parameter set instantiating an experiment | `configs/<name>/config.yaml` |
| **Run** | One execution of a config, start to finish | `<output_dir>/run_<id>/` |
| **Condition** | One cell of the design within a run — a parameter combination, a group of units, or both | `conditions/<nn>_<label>/` |
| **Repeat** | One re-execution of a condition — a seed, a timed batch, or a cross-validation fold | `<repeat-label>/` |
| **Step** | One stage of the pipeline, scoped to run, condition, repeat, or summary | `src/<name>/steps/stepNN_*.py` |
| **Unit** | The thing being measured — patient, sample, trial, item, respondent | Resolved from `input_dir` |
| **Artifact** | A file a step produced | Inside its step's directory |
| **Result** | A value a run reports — returned by a step, or derived from the unit table by a template's `aggregate` | Per unit in that step's `units.parquet`; per repeat and per condition in `run.yaml` |

Three distinctions that are easy to conflate:

- **Experiment vs. study.** An experiment is machinery; a study is a claim. One experiment usually produces many runs, and a paper reports a subset of them. Keeping these separate is what lets you rerun freely without every run pretending to be a finding.
- **Condition vs. repeat.** A condition is a difference you're measuring the effect of. A repeat is a difference you're averaging over. Statistics aggregate within a condition and compare across conditions — never the reverse. Getting this backwards is the most common way a reproducible pipeline still produces a wrong number.
- **Repeat vs. unit.** A repeat is how many times the pipeline ran; a unit is how many things were measured. Only the second can be the `n` of an inference, and a tool that blurs them will report a confidence interval that gets narrower the longer you leave it running. See [The unit table is the inference base](reference.md#the-unit-table-is-the-inference-base).

*Condition* is the term experimental fields already use, chosen over alternatives like "point," which carries HPC and optimization connotations.

## Everything is in the file

This is the constraint the rest of the design serves. Commands fall into two classes:

**Creation commands** — `new`, `plugin new`, `generate` (and its `init` alias), `study new`, `study add`, and `demo` — take a name and whatever is needed to bring something into existence. They have arguments because the thing they're creating doesn't exist yet to hold them. `demo` is the degenerate case: what it creates is fixed, so it takes nothing but an optional destination.

**Operation commands** — everything else — take **paths and nothing else.** No `--model`, no `--arm`, no `--set`, no selectors, no behavior flags, and no environment variables that change what happens.

There is no `--dry-run`, no `--resume`, and no `--allow-dirty`, because a flag that changes what a command does is a parameter wearing a disguise: it lives in a shell history nobody archives, and it makes the invocation, not the file, the description of what ran. Where those modes are genuinely useful they're separate commands with their own names — `dry-run`, `resume`, `draft` — each still taking exactly one path.

The test for any future addition: could a reader holding only the config and the run record be misled about what happened? If yes, it doesn't belong on the command line.

The same test governs anything interactive. [`demo`](reference.md#what-demo-walks-you-through) stops between commands and waits, and every one of those prompts is proceed-or-quit: **a pause may never alter the config.** A prompt that asked which method to sweep would be a parameter flag with a friendlier face — it would reach the run without passing through the file, and in the first thing a new user ever touches. Pausing changes what a person sees, never what executes, which is why it needs no mode name and why the same sequence runs unattended when nothing is watching.

Variation that needs expressing — a sweep across models, an ablation, a set of conditions — is [structure inside the config](reference.md#sweeps-and-repeats), expanded by core over the parameters the template defined. Never an invocation.

---

## Same code, different parameters

This needs no feature. It falls out of the design:

```bash
git commit -m "Implement cohort analysis"      # once, when the code is ready

# Edit configs/cohort-pilot/config.yaml — say, method: spearman
uv run publishable validate configs/cohort-pilot/config.yaml
uv run publishable run      configs/cohort-pilot/config.yaml

# Edit again — min_samples: 50. No commit needed.
uv run publishable run      configs/cohort-pilot/config.yaml
```

Each run writes a distinct `run_<id>/` with its own `run.yaml`. To compare:

```bash
uv run publishable diff <run_a>/run.yaml <run_b>/run.yaml
```

```
code_hash          identical    sha256:8e21...
input_manifest     identical    sha256:3d8a...
uv.lock            identical    sha256:6b1f...
parameters_hash    DIFFERS
  parameters.analysis.method       pearson → spearman
  parameters.analysis.min_samples  30 → 50
```

No apparatus row, because template `generic` declares no [probe](reference.md#the-apparatus-core-can-only-observe); a run that measures through one gets one here too, compared on the same footing.

That's the comparison to aim for: code, environment, and data provably identical, with parameters differing in two named places. Note this holds **even if the two runs happened weeks apart at different commits** — `code_hash` covers `src/**` and `templates/**` only, so unrelated commits — a README fix, a new config, a change under `docs/` or `tests/` — don't muddy the claim the way a bare commit hash would. What *does* move it is any change under those two trees, a second experiment's package included: the boundary is the tree rather than the experiment, because core would have to read your Python to know which files an experiment uses. See [reference.md § How the three are computed](reference.md#how-the-three-are-computed), and [Whose git hash is this?](#whose-git-hash-is-this) for the remedy when a package needs a hash that holds still on its own.

**The randomization has to hold still for this to mean anything.** Two named parameters is the whole claim, so anything else that moves silently between the runs breaks it. Seeds, fold boundaries, and arm assignment therefore derive from a design digest over `data.units` and `sweep.groups` — never from `parameters_hash` — so editing `min_samples` changes `min_samples` and nothing else. Deriving them from the parameter hash would mean every parameter edit also redrew the folds and reseeded the run, and `diff` would print one difference where there were three. See [What `auto` derives from](reference.md#what-auto-derives-from).

For several parameter sets side by side, copy the file:

```
configs/
├── cohort-pilot/config.yaml
├── cohort-pearson/config.yaml
└── cohort-spearman/config.yaml
```

Each is complete and self-describing, and still takes exactly one path to run. If the variation is grid-shaped and planned, don't copy files at all — declare it as a sweep in the one config. See the next section.

---

## Core vs. plugin

| Core owns | Plugins own |
|---|---|
| The config envelope — every top-level key except `parameters`: the four identifying fields (`schema_version`, `experiment_type`, `template_version`, `plugin`), then `metadata`, `entrypoint`, `data`, `sweep`, `replication`, `statistics`, `limits`, `hypotheses` | The entire `parameters` block, via `parameter_spec`. A template *reads* the envelope in `validate` — cross-block rules like "this experiment type fits a model, so it needs a partition to fit on" are properties of what its steps do — but declares nothing in it |
| Materializing configs from a spec; value-level validation | The spec: types, defaults, ranges, choices, help text |
| Sweep expansion (`grid`/`paired`/`ablate`/`sample`/`groups`/`baseline`), repeat kinds, seed derivation, kind-aware statistics | Field-appropriate sweep and repeat defaults |
| The three hashes, run identity, step scope, lineage, units, append-only + atomic artifacts | Naming conventions (`naming_pattern`, `field_convention`, `default_repeats`) |
| The [importable surface](reference.md#the-importable-surface): `BaseExperiment` / `BaseStep` / `BaseTemplate` / `BaseReport` / `Param` / `Unit` / `Apparatus` / `Estimate`, the four `register_*` decorators, and the errors core raises | Concrete templates, unit resolvers, apparatus probes, artifact writers for domain formats, reusable `BaseStep` subclasses |
| Lifecycle, all of it: `new`, `plugin new`, `generate` (`init`), `demo`, `validate`, `dry-run`, `run`, `draft`, `resume`, `report`, `diff`, `freeze`, `reproduce`, `study`, `docs`, `list-templates` | Domain dependencies (an API client, an instrument driver, a solver) |
| The secrets mechanism (`required_env` / `requires_env` + dotenv loading) | Which credentials an experiment type needs, and which apparatus facts must be captured |

Core ships one template, `generic`. Anything domain-shaped is a plugin; the reference LLM plugin is documented in `publishable-llm`.

A good test of whether something belongs in core: would it be identical for a wet-lab assay, a simulation sweep, and an LLM benchmark?

**The shape your input must have is derived, not declared.** Every experiment needs its data in a particular shape, and that shape is written down nowhere. It doesn't have to be: `key`, `attributes`, `cluster_by`, `measurements.by`, `holdout.from`, `assign.from`, `stratify_by`, and `null_test.shuffle` each name a field, so what the input must supply is a projection of the design declarations you already wrote. A `data.units.schema` block would be a second copy of that, free to drift, and would raise the same unanswerable question as a defaults file — which one is canonical when they disagree? So core enforces the projection at `validate`, down to values rather than headers: duplicate keys, arm levels that don't match the axis, a split column with three values, a stratum that varies inside a cluster.

That's also where the core/plugin line falls. *What* is required of a unit is identical for an assay, a sweep, and a benchmark, so core owns it. *How* units are found is not — a CSV index is the same everywhere, but a DICOM archive, a plate layout, and a sharded benchmark each need domain code to walk them, so that's a plugin's [unit resolver](reference.md#where-units-come-from). Core never prescribes an input layout, because there is no layout the three fields share.

**Core generates the standard pipeline rather than shipping one to import.** `generate experiment` writes a first step that already runs — it resolves the units, records them, and returns a count — so `publishable run` succeeds before you have written a line (see [The starter step runs](reference.md#the-starter-step-runs)). The obvious economy would be to skip the generating: have core export that step, let a config name it, and an experiment whose analysis is entirely tabular would need no `src/` at all. That's refused for the reason the hashes are split. [`code_hash` covers your repo's `src/**` and `templates/**`](reference.md#three-hashes), so anything core hands you by import sits outside it, and two runs with an identical `code_hash` could then compute different things because core moved underneath them. `provenance.publishable_version` can't repair that — it's a compatibility note, deliberately never conflated with the code that ran your experiment. Generating leaves the analysis in your repo, under your commit, inside the hash it's claimed to be covered by.

The line this draws is narrower than "every line that touches the numbers is hashed," because a template's [`aggregate`](reference.md#templates-where-parameters-are-defined) may be core's or a plugin's, which `uv.lock` pins instead: **what produced the numbers is pinned by something; what your own repo supplies is pinned by the hash.** A template you write yourself lands in `templates/**` and is therefore covered, which is why that tree joined `code_hash`. That's also the test for what may be added — a richer `aggregate` is a legitimate core addition, and a core step that decides what gets measured is not.

---

## Greenfield only

`publishable` creates new experiments; it does not convert existing scripts into its structure. There is no `publishable adopt`, and there won't be:

- `generate experiment` always creates a brand-new `src/<experiment>/`; it never modifies or wraps a file that already exists.
- To bring existing analysis code in, generate a fresh experiment and move logic into `generate step`-scaffolded steps piece by piece.

Inferring an arbitrary script's inputs, outputs, and parameters well enough to synthesize a correct config is a static-analysis problem, and solving it would be a different project than this one.

The same boundary explains what core does and doesn't check elsewhere. Core validates **declarations** — a parameter's type, a step's declared scope, a repeat's kind — and verifies **effects** — that inputs weren't mutated, that no artifact was overwritten. It never inspects the body of your Python to infer intent. Every "core can't verify this" in the rest of this document traces back to that same line.

---

## Code and data never share a repo

Governed data has its own protocol — IRB approval, data use agreements, encrypted transfer, access logs. Code has none of that friction; it's meant to be cloned and attached to a paper. When both live in one repository, someone eventually gets one by asking for the other.

**`input_dir` and `output_dir` may not resolve inside the git repository.** Enforced at three points:

- `generate experiment`/`init` refuse to write such a config (paths resolved symlink-free, so a symlink into the repo doesn't slip through).
- `validate` re-checks every time, catching a data directory that moved into the repo later.
- `run` re-checks immediately before executing — as do `draft` and `resume`, which execute the same plan under different rules about the code tree.

The repo holds code and configs. Everything file-shaped a step produces goes to the run directory under `output_dir`, and `run.yaml` — which does contain aggregate results — is written there too, not into the repo. So the repo is what you'd hand a co-author, and the data is what you'd hand a governance office, with no judgment call in between.

---

## Whose git hash is this?

Always the experiment repo's, never `publishable`'s. **The walk-up starts at the path you gave the command**, not at wherever your shell happens to be: `run configs/cohort-pilot/config.yaml` finds the repo enclosing that config, so the answer doesn't change with your working directory. Commands that take no path — `docs`, `list-templates` — start at the working directory, and so does [`resume`](reference.md#resuming), whose argument is a run directory living [outside the repo by construction](#code-and-data-never-share-a-repo). Those three are the ones you invoke from inside the repo, which for `resume` is what its `code_hash` and `uv.lock` checks against "current state" already assumed. Finding no `.git` from either starting point is an error naming where it looked, never a silent fallback. Whichever repo the walk finds, its commit, branch, and dirty state over the hashed trees go into `provenance.git`. Core's own version is recorded separately as `provenance.publishable_version`, plugin versions as `provenance.plugin_versions` — compatibility notes, never conflated with the code that ran your experiment. In a monorepo the nearest enclosing `.git` wins, so a subpackage that needs its own `code_hash` needs its own repository — there is no flag to override the walk-up.

---

## What core does not promise

- **Not bit-identical reruns.** Core derives a seed for every execution — the repeat's own where there is one — hands it over as a generator, and seeds the Python and NumPy globals from it besides, so a library you don't control is covered too; see [Randomness](reference.md#randomness-and-which-stream-a-step-should-draw-from). That covers local pseudorandomness. It can't make an external dependency deterministic — a hosted API, an instrument, a human rater. A step sets `nondeterministic = True`; core records that in `run.yaml` and notes it in `report` rather than implying reproducibility it can't deliver. What it *can* do is pin the apparatus that dependency runs on and refuse to continue when it moves — see [The apparatus core can only observe](reference.md#the-apparatus-core-can-only-observe). Recording the revision is not determinism; it's the difference between a result whose disagreement is explainable and one whose isn't. Domain mitigations beyond that belong in plugins.
- **Not verification of your step code.** Core can't confirm a step wrote only through `io`, or avoided writing to `input_dir`. It verifies effects instead: manifest checks catch input mutation, existence checks catch overwrites.
- **Not the measurement itself.** A run executes your pipeline — including whatever a step can drive, a hosted API or an instrument with a driver. Measurement a step can't invoke has already happened by the time `run` starts: a bench assay, a chart review, a rater's judgments arrive as files under `input_dir`, and core pins them by [input manifest](reference.md#three-hashes) rather than producing them. Pinning what you read is a claim core can check; producing it isn't — which is also why `generate experiment` requires an `--input-dir`, [outside the repo](#code-and-data-never-share-a-repo), before there is anything to run.
- **Not data transfer.** `reproduce` never fetches your data. Moving governed data to a new device goes through whatever protocol governs it.
- **Not credential transfer.** `reproduce` stops and names missing variables. Core has no mechanism to fetch or transmit a secret and won't grow one.
- **Not adaptive or sequential designs.** Bayesian optimization, active learning, dose escalation, and interim-analysis stopping rules all decide condition *N+1* from the results of condition *N*, so the condition set can't be enumerated before the run. That contradicts "the config fully determines the run," which every other guarantee here leans on. Supporting it means the config declaring a *policy* and the realized conditions becoming an output — coherent, but a real change to the invariant rather than another expansion mode, so it isn't in core today.
- **Not prospective enrollment.** Core assigns arms over the unit list resolved at run start, and carries no assignment forward from a previous run — so adding enrollees means a fresh draw over the whole roster, not an incremental allocation of the new ones. Freeze the roster and treat allocation as the one-time event it is, or let a trial system randomize and read its result with `assign.method: by_attribute`. See [What `auto` derives from](reference.md#what-auto-derives-from).
- **Not a scheduler.** Core executes one execution at a time, in the recorded order, and offers no parallelism, no queue, and no distribution. Three of its guarantees are statements about *when* — a `batch` is a position in time, `order: randomized` decorrelates position from condition, and the apparatus gate fires before each execution — and none of them survives interleaving. The parallelism that pays is inside a step, where a plugin can issue 440 requests at once, and that is untouched. Running many *runs* at once is a scheduler's job, and composing with one is easy precisely because a run takes one path and needs no coordination. See [One execution at a time](reference.md#one-execution-at-a-time-and-what-holds-the-run-directory).
- **Not per-condition pipeline variation.** Conditions differ in parameters, or in which units they see, never in which steps run. Allowing different steps per condition would make `code_hash` comparisons across conditions meaningless, which is the property the whole comparison story rests on.
- **Not scientific validity.** A config that validates is well-formed and well-recorded. Whether the design answers the question is yours — core will run a five-seed design without judging whether five seeds was enough.

Those are the refusals about *mechanism*. The statistical half is a list of its own — modelling beyond summary statistics, factorial main effects and interactions, crossover order and counterbalancing, leakage arriving through your inputs, power analysis — and it lives with the designs it constrains, in [experimental-designs.md § What core will not do for you](experimental-designs.md#what-core-will-not-do-for-you). A reader arriving here from the README's stated limits should read both.

---
