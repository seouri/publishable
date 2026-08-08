# publishable

**Every parameter in one file. Every run reproducible from one command.**

You have an experiment to run. Here's the whole arc with `publishable`:

1. **Design the run.** One config file holds every parameter, the conditions you're comparing, and the repeats you'll average over. `publishable` generates it fully populated — you edit rather than author.
2. **Run it.** `publishable run config.yaml`. No flags. Conditions and repeats expand on their own, and each one gets its own place in the output tree.
3. **Read the results.** Estimates, confidence intervals over your units, and effect sizes against your baseline, already computed and sitting next to the run that produced them.
4. **Publish it.** Hand a collaborator, a reviewer, or your future self one file. `publishable reproduce` re-runs it exactly — same commit, same locked environment, same input data, each verified by hash.

Nothing about what ran ends up in a shell history, so nothing has to be reconstructed later.

## Try it

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/). Nothing else to configure:

```bash
uv tool install publishable        # or: pipx install publishable, brew install publishable
publishable demo
```

`demo` builds a complete worked example — synthetic data, a three-step pipeline, a parameter sweep — and runs it:

```
Created ./publishable-demo/
  240 synthetic units      ~/publishable-demo-data/input/
  experiment               src/correlation_pilot/
  config                   configs/correlation-pilot/config.yaml

Running 3 conditions × 5 repeats = 15 executions
  00_baseline           method=pearson     ████████████ 5/5
  01_method=spearman                       ████████████ 5/5
  02_method=kendall                        ████████████ 5/5

  condition             r       95% CI            vs baseline (paired, 95% CI)
  00_baseline           0.581   [0.488, 0.661]    —
  01_method=spearman    0.607   [0.517, 0.683]    +0.026  [ 0.017,  0.035]
  02_method=kendall     0.412   [0.298, 0.514]    −0.169  [−0.181, −0.157]

  intervals over 228 of 240 units (12 failed) · seed spread ±0.014

run.yaml → ~/publishable-demo-data/results/run_2026-08-07T09-14-03Z_8e21ab3/run.yaml
```

That `run.yaml` is the point. It carries the results *and* everything needed to regenerate them — so on any other machine:

```bash
publishable reproduce <path-to-run.yaml>
```

clones the exact commit, restores the locked environment, verifies the input data hasn't changed, and runs it again.

> **v0.x — the design is settled, interfaces may still shift before 1.0.** Issues and design feedback are very welcome.

---

## Is this for you?

**A good fit if** you run experiments with parameters you sweep, repeats you average over, and results that end up in a paper — especially with data that can't live in your git repo. What a run executes is your pipeline over that data; measurements taken outside the pipeline arrive as input and are [pinned by hash, not produced](docs/design-principles.md#what-core-does-not-promise).

**Probably not** if you want a pipeline scheduler, a live dashboard, or something to retrofit onto existing scripts. `publishable` is [greenfield only](docs/design-principles.md#greenfield-only).

**Designs it speaks natively:** within- and between-subjects (with recorded randomization), factorial over parameters or over crossed arms, ablation, dose-response, train-test holdout, repeated cross-validation, bootstrap, permutation, technical-vs-biological replication, clustered units, matched case-control. The statistics follow the design — bootstrap resamples get percentile intervals, technical replicates never enter `n`, and a multi-condition sweep won't report uncorrected comparisons without warning you. Modelling beyond summary statistics is yours: see [Experimental designs](docs/experimental-designs.md) for what's supported, what needs an override, and the [errors core refuses to let you make](docs/experimental-designs.md#mistakes-core-prevents).

| Tool | Optimizes for | `publishable` differs by |
|---|---|---|
| **MLflow / W&B** | Tracking and comparing runs as they happen | Producing a self-contained record built for *publication*, not a server you query |
| **Hydra** | Flexible config composition and CLI overrides | Refusing overrides entirely — the file is the only description of the run |
| **DVC** | Versioning data and pipelines in git | Keeping data structurally *out* of the repo, for governed and clinical work |
| **Snakemake / Nextflow** | Expressing and scheduling complex DAGs | A linear pipeline, with statistics and provenance as first-class concerns |
| **Sacred** | Lightweight run capture | Pinning code, environment, *and* input data, with pre-registration and effect sizes built in |

These overlap, and several compose fine with `publishable`. The distinguishing bet: the deliverable is a **paper**, so the tool should produce something a reviewer can check, not just something you can query.

---

## How it fits together

Five words carry the whole model:

| Word | Means |
|---|---|
| **Unit** | the thing you measure — a patient, sample, trial, respondent |
| **Step** | one stage of your pipeline, one file in `src/` |
| **Condition** | one parameter combination you're *comparing* |
| **Repeat** | one re-execution you're *averaging over* — a seed or a cross-validation fold |
| **Run** | one execution of the whole thing: every step, every condition, every repeat |

Statistics aggregate *within* a condition and compare *across* conditions. Getting that backwards is the most common way a reproducible pipeline still produces a wrong number, which is why the two are named separately rather than both being called "runs."

### Where things live

Your repo holds code and configs — never data:

```
my-study/
├── src/cohort_pilot/          # your pipeline, one file per step   → code_hash
│   ├── experiment.py          #   declares step order
│   └── steps/
│       ├── step01_load_cohort.py
│       ├── step02_fit_model.py
│       ├── step03_analyze.py
│       └── step04_compare_methods.py
├── configs/cohort-pilot/
│   └── config.yaml            # every parameter                    → parameters_hash
├── pyproject.toml + uv.lock   # the environment                    → locked
└── .env                       # credentials, never committed
```

Your data lives outside it, and so does everything a run produces:

```
~/results/cohort-pilot/
└── run_2026-08-07T09-14-03Z_8e21ab3/
    ├── run.yaml                        ← results + all three hashes. This is the deliverable.
    ├── conditions/
    │   ├── 00_baseline/                ← one folder per condition, self-describing
    │   │   ├── seed17/                 ← one folder per repeat
    │   │   │   └── step03_analyze/scores.parquet
    │   │   └── seed42/…
    │   └── 01_method=spearman/…
    └── summary/                        ← steps that compare across conditions
```

The directory structure *is* the experiment structure, so finding an artifact never requires reading code. Nothing here is ever overwritten: a second run creates a new `run_<id>/` beside this one.

### And then

```
run.yaml  ──►  publishable reproduce   ──►  anyone re-runs it exactly
          └─►  publishable study add   ──►  a bundle beside your manuscript
```

Full vocabulary: [Ontology](docs/design-principles.md#ontology).

---

## What you actually write

One config, generated fully populated by `publishable generate experiment` (or its shorter alias `publishable init`), so you edit rather than author from scratch:

```yaml
parameters:
  analysis:
    method: pearson              # choices: pearson | spearman | kendall
    min_samples: 30              # integer >= 2

sweep:
  baseline: {analysis.method: pearson}
  grid:
    analysis.method: [spearman, kendall]

replication:
  repeats:
    - {kind: seed, n: 5}         # seed | batch | fold — what a re-execution varies
```

And steps that never mention sweeps — each condition is resolved before your code runs:

```python
class Step(BaseStep):
    scope = "repeat"                      # run once per repeat, per condition

    def run(self, cfg, io):
        # io.units — your patients, samples, trials: whatever you're measuring
        # cfg.parameters — already resolved to THIS condition's values
        result = analyze(io.units, method=cfg.parameters.analysis.method)

        io.write("scores.parquet", result)   # lands in this condition + repeat's own folder
        return {"r": result.r}               # returned values become the reported metrics
```

Write it once for a single condition; adding a sweep later changes nothing here.

Statistics come back computed, next to the hashes that make them checkable:

```yaml
results:
  conditions:
    - label: method=spearman
      aggregated:
        step03_analyze: {r: {value: 0.607, basis: units, n: {completed: 228},
                             ci95: [0.517, 0.683], repeat_spread: {std: 0.014}}}
      vs_baseline:
        step03_analyze: {r: {delta: 0.026, paired: true, ci95: [0.017, 0.035]}}
provenance:
  code_hash: sha256:8e21…            # your src/** + templates/**, from a clean tree
  parameters_hash: sha256:1a2b…      # this exact parameter set
  input_manifest_hash: sha256:3d8a…  # the data it actually read
```

---

## Start your own

```bash
# 1. Scaffold a repo. Runs `git init`; writes README, LICENSE, CITATION.cff.
publishable new my-study && cd my-study

# 2. Create an experiment. Data paths must live outside the repo.
publishable generate experiment cohort-pilot \
  --template generic \
  --input-dir ~/data/cohort-2026 \
  --output-dir ~/results/cohort-pilot

# 3. Run it right away — the scaffold ships a working starter step.
publishable run configs/cohort-pilot/config.yaml

# 4. Now make it yours: add steps, implement them, commit.
publishable generate step cohort-pilot analyze
git add src/ && git commit -m "Implement cohort analysis"

# 5. Edit configs/cohort-pilot/config.yaml, then check before spending a run.
publishable validate configs/cohort-pilot/config.yaml
publishable dry-run  configs/cohort-pilot/config.yaml
publishable run      configs/cohort-pilot/config.yaml

# 6. When you publish, collect the runs you're reporting.
publishable study new ~/papers/triage/study --title "Cohort triage pilot"
publishable study add ~/papers/triage/study ~/results/cohort-pilot/latest/run.yaml --as main
```

Step 3 works before you've written any code, so you can see the whole loop before committing to it.

### The loop you'll actually live in

Once the code is committed, changing an experiment means editing one file. No commit, no flags, no bookkeeping:

```bash
# edit configs/cohort-pilot/config.yaml — say, min_samples: 30 → 50
publishable run configs/cohort-pilot/config.yaml

publishable diff ~/results/cohort-pilot/run_A/run.yaml \
                 ~/results/cohort-pilot/run_B/run.yaml
```

```
code_hash          identical    sha256:8e21…
input_manifest     identical    sha256:3d8a…
uv.lock            identical    sha256:6b1f…
parameters_hash    DIFFERS
  parameters.analysis.min_samples   30 → 50
```

That's the payoff of hashing code and parameters separately: you get to *prove* only one thing changed, which is the claim a comparison rests on.

---

## What you get

- **One file, no flags.** After `init`, every command takes a path and nothing else. A selector flag would live in a shell history that nobody archives.
- **Code and parameters hashed separately.** `code_hash` covers your code trees only, so "same code, different parameters" is a *provable* claim — even across commits weeks apart.
- **Three things pinned, not two — four when you measure through something.** Git commit for code, `uv.lock` for environment, and a content manifest for input data; the third is what most tools leave open. And when measurement goes through an apparatus core can't install — a hosted model deployment, an instrument — a plugin probe records its revision per condition and a change fails the run. `uv.lock` pins the client; that record pins the server.
- **Artifacts are append-only and atomic.** Nothing is ever overwritten or deleted, and a crash mid-write leaves nothing behind rather than a half-file that blocks the retry.
- **Code and data never share a repo.** Data paths are structurally forbidden inside the git repo — code is shareable, governed data isn't, and they need different protocols.
- **Intervals over units, not over executions.** `n` counts the things your claim generalizes over. Repeats are reported as pipeline stability, separately and labelled, because an interval across five seeds narrows as you add seeds and says nothing about your cohort. Where core can't compute an interval honestly, it reports the estimate and omits the interval.
- **Statistics that match your design.** Declaring how units are allocated and how repeats are structured determines the analysis: paired or unpaired, t-based or percentile, clustered or not. A t-interval over bootstrap resamples is wrong, and core won't compute one — nor will it count technical replicates as `n`.
- **Pre-registration for free.** The config is written and hashed *before* the run, so declared hypotheses can be checked against results — and after-the-fact additions don't match the hash.
- **Stated limits.** Core documents what it [does not promise](docs/design-principles.md#what-core-does-not-promise) — bit-identical reruns against external services, verification of your Python, or scientific validity.

---

## Commands

Creation commands take a name and what's needed to create it. **Everything else takes paths only.**

| Command | Does |
|---|---|
| `demo` | Build and run a complete worked example, no setup required |
| `new` · `plugin new` · `generate` · `init` | Scaffold a project, a plugin, an experiment, a step |
| `validate` · `dry-run` | Check values, ranges, and the full execution plan before spending a run |
| `run` · `draft` · `resume` | Execute; `draft` permits a dirty tree, `resume` continues an interrupted run |
| `report` · `diff` · `freeze` | Render results, compare two runs hash by hash, snapshot the environment |
| `reproduce` | Clone the recorded commit and prepare it to run — no git commands typed |
| `study new` · `study add` | Assemble the runs a paper reports, outside the repo |

Full details: [CLI reference](docs/reference.md#cli-reference).

---

## Extending it

Core knows nothing about LLMs, cohorts, instruments, or solvers. Domain knowledge lives in **plugins**, and a plugin doesn't need a PR here:

```bash
publishable generate experiment triage-pilot \
  --plugin someuser/publishable-llm \
  --template llm_diagnostic \
  --input-dir ~/data/xray-2026 --output-dir ~/results/triage-pilot
```

`--plugin owner/repo` is `uv add git+…` and nothing more — so the plugin lands in your lockfile and gets captured in provenance like any other dependency. Write your own with `publishable plugin new`, which scaffolds an installable package whose docs generate from its parameter spec.

The reference LLM plugin is [`publishable-llm`](https://github.com/someuser/publishable-llm).

---

## Documentation

- **[Experimental designs](docs/experimental-designs.md)** — how to express each design, and the mistakes core prevents
- **[Reference](docs/reference.md)** — config schema, CLI, `io` API, templates, sweeps, artifact layout
- **[Design principles](docs/design-principles.md)** — why the rules are what they are; read before proposing a change
- **[Plugin guide](docs/reference.md#plugins-where-domain-knowledge-lives)** — building and sharing templates

## Contributing

Most new templates should be a [plugin](docs/reference.md#plugins-where-domain-knowledge-lives), not a PR here — that's what `--plugin owner/repo` is for. Upstream contributions are for core mechanisms: the config envelope, provenance capture, the artifact model, the validation engine, the CLI.

A good test of whether something belongs in core: **would it be identical for a wet-lab assay, a simulation sweep, and an LLM benchmark?** If not, it's a plugin.

Design disagreements are welcome as issues. If a rule seems arbitrary, [design-principles.md](docs/design-principles.md) probably explains it — and if it doesn't, that's a documentation bug worth filing.

## License

MIT — see [LICENSE](LICENSE).
