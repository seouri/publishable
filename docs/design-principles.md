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

- **Every parameter is in the config. No exceptions.** After `init`, no command takes any argument other than a path. There are no parameter flags, no selectors, no overrides that live only in a shell history. See [Everything is in the file](#everything-is-in-the-file).
- **`init` writes the whole file for you.** You don't author YAML from scratch or hunt for available options: `init` materializes every parameter the template offers, with sensible defaults and inline documentation. Editing that file *is* designing the run. See [The one config file](reference.md#the-one-config-file).
- **Code and parameters are hashed separately.** `code_hash` covers `src/**`; `parameters_hash` covers the resolved parameters. This is what makes "same code, different parameters" a provable claim rather than a hopeful one. See [Three hashes](reference.md#three-hashes).
- **Changing parameters costs nothing.** Edit, validate, run. Repeat. No commit required, because code provenance doesn't depend on the config being committed. See [Same code, different parameters](#same-code-different-parameters).
- **`validate` checks values, not just presence.** Types, ranges, choices, unknown keys — before you spend the run. See [Validation](reference.md#validation).
- **Every run gets its own identity.** Artifacts live under `run_<id>/`, so a rerun never collides with a previous one. See [Run identity](reference.md#run-identity).
- **Artifacts are append-only and atomic.** Nothing is ever overwritten or deleted; a crash mid-write leaves nothing behind rather than a half-file that blocks the retry. See [Steps and artifacts](reference.md#steps-and-artifacts).
- **Code, environment, and data are all pinned.** Commit and tree hash for code, `uv.lock` for environment, and a content manifest for input data — the third is what most tools leave open.
- **Code and data never share a repo.** `input_dir`/`output_dir` are structurally forbidden inside the git repo: code is shareable, governed data isn't, and they need different protocols. See [Code and data never share a repo](#code-and-data-never-share-a-repo).
- **Git isn't optional for code.** `new` initializes a repo, and `run` refuses when `src/**` has uncommitted changes — a code hash that doesn't match what ran isn't provenance, it's a guess. Config edits don't trip this.
- **It's *your* commit, not ours.** Captured git identity always belongs to your experiment repo. See [Whose git hash is this?](#whose-git-hash-is-this)
- **`uv` is not optional.** Environments are captured and rebuilt through `uv`, so "reproduce this" means `uv sync --locked`.
- **Reproducing elsewhere shouldn't mean typing git commands.** One command clones, checks out the recorded commit, syncs, and runs. See [Reproducing on another device](reference.md#reproducing-on-another-device).
- **Secrets are the one thing never captured.** Credentials live in `.env`; the config stores only variable *names*. See [Secrets & credentials](reference.md#secrets--credentials).
- **The unit of measurement is first-class.** Patients, samples, trials, items — declared once, and everything from fold partitioning to per-unit result tables follows from it. See [Units](reference.md#units-the-thing-being-measured).
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
| **Condition** | One parameter combination within a run | `conditions/<nn>_<label>/` |
| **Repeat** | One re-execution of a condition (seed, fold, bootstrap, permutation) | `<repeat-label>/` |
| **Step** | One stage of the pipeline, scoped to run, condition, repeat, or summary | `src/<name>/steps/stepNN_*.py` |
| **Unit** | The thing being measured — patient, sample, trial, item, respondent | Resolved from `input_dir` |
| **Artifact** | A file a step produced | Inside its step's directory |
| **Result** | A value a step returned — per unit, per repeat, per condition | `run.yaml` |

Two distinctions that are easy to conflate:

- **Experiment vs. study.** An experiment is machinery; a study is a claim. One experiment usually produces many runs, and a paper reports a subset of them. Keeping these separate is what lets you rerun freely without every run pretending to be a finding.
- **Condition vs. repeat.** A condition is a difference you're measuring the effect of. A repeat is a difference you're averaging over. Statistics aggregate within a condition and compare across conditions — never the reverse. Getting this backwards is the most common way a reproducible pipeline still produces a wrong number.

*Condition* is the term experimental fields already use, chosen over alternatives like "point," which carries HPC and optimization connotations.

## Everything is in the file

This is the constraint the rest of the design serves. Commands fall into two classes:

**Creation commands** — `new`, `plugin new`, `generate` (and its `init` alias) — take a name and whatever is needed to bring something into existence. They have arguments because the thing they're creating doesn't exist yet to hold them.

**Operation commands** — everything else — take **paths and nothing else.** No `--model`, no `--arm`, no `--set`, no selectors, no behavior flags, and no environment variables that change what happens.

There is no `--dry-run`, no `--resume`, and no `--allow-dirty`, because a flag that changes what a command does is a parameter wearing a disguise: it lives in a shell history nobody archives, and it makes the invocation, not the file, the description of what ran. Where those modes are genuinely useful they're separate commands with their own names — `dry-run`, `resume`, `draft` — each still taking exactly one path.

The test for any future addition: could a reader holding only the config and the run record be misled about what happened? If yes, it doesn't belong on the command line.

Variation that needs expressing — a sweep across models, an ablation, a set of conditions — is [structure inside the config](reference.md#sweeps-and-repeats), interpreted by the template that defined it. Never an invocation.

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

That's the comparison to aim for: code, environment, and data provably identical, with parameters differing in two named places. Note this holds **even if the two runs happened weeks apart at different commits** — `code_hash` covers `src/**` only, so unrelated commits (a README fix, a new experiment added elsewhere) don't muddy the claim the way a bare commit hash would.

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
| The config envelope: `metadata`, `data`, `units`, `replication`, `hypotheses`, `entrypoint` | The entire `parameters` block, via `parameter_spec` |
| Materializing configs from a spec; value-level validation | The spec: types, defaults, ranges, choices, help text |
| Sweep expansion (`grid`/`paired`/`ablate`/`sample`/`baseline`), repeat kinds, seed derivation, kind-aware statistics | Field-appropriate sweep and repeat defaults |
| The three hashes, run identity, step scope, lineage, units, append-only + atomic artifacts | Naming conventions (`naming_pattern`, `field_convention`, `default_repeats`) |
| `BaseExperiment` / `BaseStep` / `BaseTemplate` / `Param` / `Unit` / `io` | Concrete templates, unit resolvers, reusable `BaseStep` subclasses |
| Lifecycle: `new`, `generate`, `validate`, `dry-run`, `run`, `draft`, `resume`, `report`, `diff`, `freeze`, `reproduce`, `study` | Domain dependencies (an API client, an instrument driver, a solver) |
| The secrets mechanism (`credential_env_var` + dotenv loading) | Which credentials an experiment type needs |

Core ships one template, `generic`. Anything domain-shaped is a plugin; the reference LLM plugin is documented in `publishable-llm`.

A good test of whether something belongs in core: would it be identical for a wet-lab assay, a simulation sweep, and an LLM benchmark?

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
- `run` re-checks immediately before executing.

The repo holds code and configs. Everything file-shaped a step produces goes to the run directory under `output_dir`, and `run.yaml` — which does contain aggregate results — is written there too, not into the repo. So the repo is what you'd hand a co-author, and the data is what you'd hand a governance office, with no judgment call in between.

---

## Whose git hash is this?

Always the experiment repo's, never `publishable`'s. Core walks up from the working directory to find `.git`; that repo's commit, branch, and `src/**` dirty state go into `provenance.git`. Core's own version is recorded separately as `provenance.publishable_version`, plugin versions as `provenance.plugin_versions` — compatibility notes, never conflated with the code that ran your experiment. In a monorepo, `--repo path/to/subpackage` pins a specific root.

---

## What core does not promise

- **Not bit-identical reruns.** Core seeds Python and NumPy per repeat from the resolved seed list, covering local pseudorandomness. It can't make an external dependency deterministic — a hosted API, an instrument, a human rater. A step sets `nondeterministic = True`; core records that in `run.yaml` and notes it in `report` rather than implying reproducibility it can't deliver. Domain mitigations belong in plugins.
- **Not verification of your step code.** Core can't confirm a step wrote only through `io`, or avoided writing to `input_dir`. It verifies effects instead: manifest checks catch input mutation, existence checks catch overwrites.
- **Not data transfer.** `reproduce` never fetches your data. Moving governed data to a new device goes through whatever protocol governs it.
- **Not credential transfer.** `reproduce` stops and names missing variables. Core has no mechanism to fetch or transmit a secret and won't grow one.
- **Not adaptive or sequential designs.** Bayesian optimization, active learning, dose escalation, and interim-analysis stopping rules all decide condition *N+1* from the results of condition *N*, so the condition set can't be enumerated before the run. That contradicts "the config fully determines the run," which every other guarantee here leans on. Supporting it means the config declaring a *policy* and the realized conditions becoming an output — coherent, but a real change to the invariant rather than another expansion mode, so it isn't in core today.
- **Not per-condition pipeline variation.** Conditions differ in parameters, never in which steps run. Allowing different steps per condition would make `code_hash` comparisons across conditions meaningless, which is the property the whole comparison story rests on.
- **Not scientific validity.** A config that validates is well-formed and well-recorded. Whether the design answers the question is yours — core will compute a confidence interval over five seeds without judging whether five seeds was enough.

---
