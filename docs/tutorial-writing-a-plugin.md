# Tutorial: writing a plugin

**Non-normative.** The four documents — [`README.md`](../README.md),
[`design-principles.md`](design-principles.md), [`experimental-designs.md`](experimental-designs.md),
[`reference.md`](reference.md) — are the specification. This file teaches the path through them and is
authoritative over nothing. Where it disagrees with `reference.md`, `reference.md` wins and the
disagreement is a defect; every one this tutorial found is [filed](#the-gaps-this-tutorial-found), named
by code, and linked from the step it bites on.

It answers three questions in order: **why** a plugin exists, **when** you actually need one, and **how**
to build one. The short version of the second answer surprises most readers, so it is here rather than
buried: most projects need a **project-local template**, not a plugin. The section that decides between
them is [Do you need a plugin at all?](#do-you-need-a-plugin-at-all)

---

## Measured on 2026-08-27 against commit `e61dcb4`

Every command below was run, and every transcript is copied from what it printed. Build facts expire —
a claim about what the tool does *today* is perishable in a way a specification claim is not — so they
are confined to this notice and to the tables that carry an error code.

**Three behaviours were re-measured**, because writing this tutorial found them and the commits up to
`e61dcb4` — the one this heading names — closed them: `scaffold_project` now writes `[tool.uv] package =
false`, `plugin new` ships a test that can fail plus a `pytest` dev group, and a plugin's writer now
dispatches from its claim with nothing importing the module. Everything else was captured at `937591f`
and still holds here: `hashes.HASHED_TREES` is `("src", "templates")`,
so the edited `pyproject.toml` is outside [`code_hash`](reference.md#three-hashes), and every hash and
`run_id` quoted below is the one `937591f` produced. The one output any of the three could have moved
was re-run at `e61dcb4` — `dry-run`'s fixed-file list, which names `environment/pyproject.toml` — and it
prints the same nine files in the same order. W1 moves no number at all: it decides which writer encodes
an artifact, and touches no hash, no statistic and no count.

What that measurement established, before any prose:

| Route | State at `e61dcb4` |
|---|---|
| A project-local `templates/*.py` template | Works end to end: `validate`, `dry-run`, `run`, `docs`, `list-templates` |
| A plugin's **resolver** | Dispatches at `validate` and at `run` |
| A plugin's **apparatus probe** | Dispatches, and its facts land in `provenance.apparatus` |
| A plugin's **writer / reader** | Dispatches: the suffix is resolved from the claim, and the winning distribution is the only one loaded |
| A plugin's **template** | Refused: `E-TEMPLATE-INSTALLED-UNSUPPORTED`. Core resolves the name from package metadata and this build does not load what it points at |

So a plugin is worth building today for its **machinery** — resolvers, probes, writers — while the
template that names your parameters stays in your own repo. That is not the arrangement
[§ Plugins](reference.md#plugins-where-domain-knowledge-lives) describes, and the difference is a build
state rather than a design change: `reference.md` [names the refusal](reference.md#errors-validate-reports)
in three places.

---

## Contents

- [Why plugins exist](#why-plugins-exist)
- [Do you need a plugin at all?](#do-you-need-a-plugin-at-all)
- [The five registries](#the-five-registries)
- [Route A: a project-local template, end to end](#route-a-a-project-local-template-end-to-end)
- [Route B: packaging the machinery as a plugin](#route-b-packaging-the-machinery-as-a-plugin)
- [Testing a plugin](#testing-a-plugin)
- [What this build refuses, by code](#what-this-build-refuses-by-code)
- [The gaps this tutorial found](#the-gaps-this-tutorial-found)

---

## Why plugins exist

Core knows nothing about assays, cohorts, instruments, solvers, or models. It owns the config envelope,
the three hashes, sweep expansion, unit resolution, the statistics over the unit table, and the whole
command lifecycle. Everything domain-shaped is a plugin, and the test is one sentence from
[`design-principles.md` § Core vs. plugin](design-principles.md#core-vs-plugin):

> would it be identical for a wet-lab assay, a simulation sweep, and an LLM benchmark?

If yes, it is core's and you should not be writing it. If no, it is yours. The split is not a courtesy to
extension authors — it is what keeps `parameters_hash` meaningful. Core materializes and enforces
`parameters` from a **spec** it did not write, so *what* a parameter is stays under your control while
*whether a config honours it* stays under core's.

Two boundaries inside "yours" decide the shape of what you write:

| If the fact is | It is | Because |
|---|---|---|
| Something you **decide** | a `Param` in `parameter_spec` | it is part of the design, so it belongs inside `parameters_hash` |
| Something you can only **observe** | an [apparatus fact](reference.md#the-apparatus-core-can-only-observe) | recalibrating an instrument is not redesigning an experiment, so it must stay outside that hash |

An instrument's gain is the first. Its firmware revision and calibration ID are the second. Getting this
wrong in either direction is the mistake plugin authors make most: a probed fact declared as a parameter
makes every recalibration read as a new design, and a decided value read off the apparatus makes two
different designs share one identity.

---

## Do you need a plugin at all?

A template can live in three places, and [where it lives decides how it is
pinned](reference.md#templates-where-parameters-are-defined):

| Where | Registered by | Pinned by | Use it when |
|---|---|---|---|
| Core | core itself | `publishable`'s own version | `generic` is enough |
| Your repo's `templates/*.py` | its `@register_template` argument, discovered by path | [`code_hash`](reference.md#three-hashes), which covers `templates/**` | the experiment type is **this project's** |
| An installed distribution | a `publishable.templates` entry point | `uv.lock` | two or more projects share the experiment type |

**Start local.** `publishable generate template <name>` writes a file into `templates/`, and it is a real
template in every way that matters — `init` materializes from it, `validate` enforces it, `aggregate`
derives from it, `list-templates` prints its spec, `docs` renders its parameter table. Its cost and its
benefit are the same fact: it is inside `code_hash`, so editing it moves the run identity, exactly as
editing a step does.

**Package it when a second project needs it**, or when the domain work is machinery rather than
parameters — walking a DICOM archive, probing an instrument, encoding a domain file format. That
machinery is what a plugin ships best today, and it is also the part core genuinely cannot supply: what
is required *of* a unit is identical across every field, and *how* units are found is not.

---

## The five registries

One mechanism, five groups. Each is an entry-point group in a plugin's `pyproject.toml` and a
`@register_*` decorator in its source, and [the entry point is the
registration](reference.md#creating-a-plugin-publishable-plugin-new) while the decorator argument is a
declaration checked against it.

| Registry | Provides | A config names it as | Resolved at |
|---|---|---|---|
| `publishable.templates` | an experiment type's `parameter_spec`, `validate`, `aggregate` | `experiment_type` | `validate`, and `init` before it |
| `publishable.resolvers` | how units are found in domain input | `data.units.from: {resolver: <name>}` | `validate` and `run` |
| `publishable.probes` | what the apparatus reports about itself | a template's `apparatus_probe` | run start, and before every execution |
| `publishable.writers` | bytes for a domain artifact suffix | nothing — `io.write` dispatches on the suffix | the `io.write` call |
| `publishable.readers` | the inverse of a writer | nothing — `io.read_upstream` indexes it | the read |

A name is claimed **once**: two installed plugins claiming one name, a plugin shadowing `generic`, a
writer claiming a suffix core already writes, or a local file taking an installed name all fail at load
rather than being resolved by install order. Install order is a property of a machine, and a run whose
template depended on it would be reproducible everywhere except where it mattered.

---

## Route A: a project-local template, end to end

This route runs to completion at `e61dcb4`. Every block is real output.

### 1. Scaffold the project

```bash
publishable new lab-study
```

```
project → lab-study
next: cd lab-study && uv run publishable generate experiment <name> --template generic --input-dir <dir> --output-dir <dir>
```

That next line runs as printed, and one line in the scaffolded `pyproject.toml` is why:

```toml
[tool.uv]
package = false
```

An experiment repository is code under a commit, not a distribution anybody installs — so `uv` is told
not to build it. Without that declaration hatchling looks for a package matching the project's own name,
finds none (`src/` holds a `.gitkeep`, and `generate experiment` writes `src/<experiment>/`), and every
`uv run publishable …` in a fresh project fails on a build traceback. That was true until 2026-08-27;
if you are reading a project scaffolded before then, add those two lines by hand.

### 2. Write the template

```bash
uv run publishable generate template my_assay
```

It prints nothing and exits `0`. The file it wrote is a working skeleton; fill in the spec:

```python
# templates/my_assay.py — a template only this project needs, discovered by path
from publishable import BaseTemplate, Param, register_template


@register_template("my_assay")
class MyAssayTemplate(BaseTemplate):
    version = "1.0.0"
    default_repeats = 3

    parameter_spec = {
        "instrument.model": Param(str, help="Instrument model identifier"),
        "instrument.gain": Param(float, default=1.0, gt=0, help="Detector gain multiplier"),
        "analysis.threshold": Param(
            float, default=0.5, gt=0, lt=1,
            help="Reading above which a well counts as a hit",
        ),
    }
```

Three things about that spec, each a rule rather than a style:

- **`instrument.model` has no `default`, which is what makes it required.** `init` materializes it as
  `""  # REQUIRED` and `validate` rejects the file until it is filled in. `default=None` is a different
  claim — it needs `nullable=True` and means *`null` is a legal value*.
- **The constraint vocabulary is closed** — `choices`, `ge`/`gt`/`le`/`lt`, `pattern`, `item_type`,
  `min_items`/`max_items`, `nullable`, `help`. There is no `validator=` hook, because a rule that needs
  code is a cross-field rule and belongs in `validate`.
- **The dotted path is the config's nesting.** `instrument.gain` becomes `parameters.instrument.gain`,
  which is what a step reads as `cfg.parameters.instrument.gain`.

`list-templates` reads the spec back, with the provenance of every template it can see:

```
### `my_assay`

local · provider /…/lab-study/templates/my_assay.py::MyAssayTemplate

Convention class `generic` · default repeats 3 · naming `^[a-z0-9]+(-[a-z0-9]+)*$`

| Parameter | Type | Default | Constraints | Description |
|---|---|---|---|---|
| `instrument.model` | string | — | required | Instrument model identifier |
| `instrument.gain` | float | `1.0` | > 0 | Detector gain multiplier |
| `analysis.threshold` | float | `0.5` | > 0; < 1 | Reading above which a well counts as a hit |
```

### 3. Generate the experiment from it

```bash
uv run publishable generate experiment my-pilot --template my_assay \
  --input-dir /…/data --output-dir /…/results
```

```
config → /…/lab-study/configs/my-pilot/config.yaml
step   → /…/lab-study/src/my_pilot/steps/step01_summarize_units.py
next: uv run publishable validate /…/lab-study/configs/my-pilot/config.yaml
```

The `parameters` block of that config is your spec, materialized with its comments derived from the same
declarations:

```yaml
parameters:
  # ---- Base values. Everything below is defined by the template, not by core. ----
  instrument:
    model: ""                       # REQUIRED — Instrument model identifier
    gain: 1.0                       # float > 0
  analysis:
    threshold: 0.5                  # float in (0, 1)
```

**Changing `parameter_spec` later does not rewrite a config that already exists.** `init` refuses an
experiment that exists (`E-EXPERIMENT-EXISTS`), by design — it never modifies a package it did not just
create. What tells you exactly what to change is `validate`:

```
  error   E-PARAM-UNKNOWN      parameters.my_assay.threshold
          is not a parameter of this template — did you mean `analysis.threshold`?
  error   E-PARAM-MISSING      parameters.instrument.model
          is required and absent
  warning W-PARAM-UNSET        parameters
          holds paths that carry a default and are left unset here; a step reading one as cfg.parameters.<path> raises E-STEP-PARAM-UNKNOWN: instrument.gain, analysis.threshold
```

### 4. Add the cross-block rule only a template can know

`validate` receives the **whole** config, not just `parameters`, because the rules a template most needs
are cross-block: an experiment type that fits a model can reject a config declaring no `holdout` and no
`fold`, since otherwise it evaluates on the units it was fitted against. Core cannot tell that config
from a legitimate one; the template can.

```python
    def validate(self, config) -> list[str]:
        swept = set()
        for mode in ("grid", "paired", "ablate", "sample"):
            swept |= set((config.get("sweep") or {}).get(mode) or {})
        if "instrument.gain" in swept:
            return ["instrument.gain is a calibration, not a variable: sweeping it "
                    "makes two conditions two instruments"]
        return []
```

**Note the `.get` calls.** [§ The importable surface](reference.md#the-importable-surface) says this
method receives the dot-access config node; at `e61dcb4` it receives a **plain `dict`**, so the
documented idiom `config.data.units.holdout` fails:

```
  error   E-TEMPLATE-RULE      parameters
          raised while validating: AttributeError: 'dict' object has no attribute 'data'
```

Write plain mapping access until that is closed, and expect to revisit it —
filed: [`template.validate` receives a dict](#templatevalidate-receives-a-plain-dict-not-the-dot-access-config-node).
The refusal is contained rather than a traceback, which is why the mistake is cheap to make and easy to
miss: it costs one error line at `validate`, not a crash.

A declared value is refused with the template's own message:

```
  error   E-TEMPLATE-RULE      parameters
          instrument.gain is a calibration, not a variable: sweeping it makes two conditions two instruments
```

Reading the envelope is not owning it. Returning an error is the **only** thing a template does with what
it reads; it cannot add a field to `data` or change what `sweep` means.

### 5. Derive a metric in `aggregate`

`aggregate` is optional and it is the only way to give a derived statistic a real interval — core can
call it on a **resampled** table, which is what makes the metric `basis: units` rather than a scalar core
can only watch vary across seeds.

```python
    def aggregate(self, units, cfg) -> dict:
        if "reading" not in units.columns:
            return {}
        readings = [r for r in units.reading if r is not None]
        if not readings:
            return {}
        threshold = cfg.parameters.analysis.threshold
        return {"hit_rate": sum(1 for r in readings if r > threshold) / len(readings)}
```

The table supports exactly four operations — iterate, `units.<column>`, `len`, `units.columns` — and
nothing else, so filtering is ordinary Python. Returning `{}` for a table this template does not
recognize is the right answer, not an error: core calls `aggregate` once per **recording step**, and a
pipeline can have several. Reading `cfg` is what lets one `aggregate` compute a different statistic per
condition, and core passes the same `cfg` when it recomputes on a resampled table, so a value and its
interval are always the same statistic.

### 6. Record a number in the step

The generated step records a placeholder. Replace the draw and rename the column:

```python
class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        units = list(io.units)
        gain = cfg.parameters.instrument.gain
        for unit in units:
            io.record(unit.key, {"reading": self.rng.random() * gain})
        return {"n_units": len(units)}
```

A **numeric** column is what earns a metric block. A bool or a string column reaches `aggregate`'s table
and earns no interval, so a step recording only those publishes nothing.

### 7. Validate, commit, cost, run

```
  ✓ config valid · configs/my-pilot/config.yaml
```

Commit before running: `code_hash` covers `src/**` and `templates/**`, and `run` refuses a dirty tree
(`E-CODE-DIRTY`) because a hash claiming to cover your code must actually cover what ran.

`dry-run` is what to read before spending anything:

```
steps: step01_summarize_units (repeat)
statistics: basis units (n=6 resolved); correction holm; derived metric names come from the template's aggregate() and are not knowable before the run
scale:  60 unit-executions (10 executions × 6 units handed to each)
would create 10 step directories under /…/results/run_.../
  conditions/00_threshold=0.4/seed72/step01_summarize_units
  …
and 9 fixed files in that directory:
  config.yaml
  environment/pyproject.toml
  environment/repo_root.txt
  environment/uv.lock
  executions.jsonl
  identity.json
  manifest/input.json
  run.yaml
  sweep.yaml
artifact files inside a step directory are NOT listed: their names are `io.write`
  arguments in step code, which core never inspects, so they are declared nowhere
  in the config and cannot be known before the run
creates nothing
```

Then `run`:

```
  warning W-STATS-COLUMN-THIN  limits.min_reported_n
          condition 0, step 'step01_summarize_units': recorded column 'reading' carries a number for 6 unit(s), below limits.min_reported_n (10)
2 problems (0 errors, 2 warnings)
run.yaml → /…/results/run_2026-08-27T13-57-45Z_c075829/run.yaml
```

And the template's derived metric is in the record with an interval of its own, beside the recorded
column's:

```yaml
    aggregated:
      step01_summarize_units:
        reading:
          value: 0.4156447059308137
          basis: units
          n: {resolved: 6, completed: 6, ineligible: 0, failed: 0}
          ci95: [0.3010889920239793, 0.5302004198376481]
          method: t_over_units
        hit_rate:
          value: 0.6666666666666666
          basis: units
          n: {resolved: 6, completed: 6, ineligible: 0, failed: 0}
          ci95: [0.3333333333333333, 1.0]
          method: percentile_over_units
          cohens_d: null
          resample_draws: 2000
```

`reading` is a *t* interval over units; `hit_rate` is a **percentile** interval over 2000 resampled
tables, because it is derived and core recomputed `aggregate` on each draw. That difference is the whole
payoff of writing `aggregate` rather than returning a number from a step.

### 8. Let the documentation derive itself

```bash
uv run publishable docs
```

```
README.md: rewrote `overview`, `credentials`, `experiments`, `templates`
```

The `templates` region now holds the same parameter table `list-templates` printed, generated from
`parameter_spec`. Add a parameter, run `docs`, and the table and newly-initialized configs move together.
Documentation that cannot drift is the only kind worth generating.

---

## Route B: packaging the machinery as a plugin

### 1. Scaffold

```bash
publishable plugin new publishable-plate-assay
```

**It prints nothing and exits `0`.** What it wrote:

```
publishable-plate-assay/
├── README.md
├── LICENSE
├── CITATION.cff
├── pyproject.toml
├── .gitignore
├── .git/
├── src/publishable_plate_assay/
│   ├── templates/plate_assay.py
│   ├── resolvers/units.py
│   ├── probes/instrument.py
│   └── writers/artifact.py
├── tests/test_plate_assay.py
└── examples/plate_assay/
```

Five differences from the tree in
[§ Creating a plugin](reference.md#creating-a-plugin-publishable-plugin-new): there is no `uv.lock`;
`examples/plate_assay/` is created **empty** rather than holding a generated `config.yaml`; the README
carries a static table rather than one derived from the spec; `steps/` is shown there and is not written;
and `.gitignore` is written and is not shown. The README one has a visible consequence —
`publishable docs` inside a plugin refuses:

```
  error   E-DOCS-NO-REGIONS    /…/publishable-plate-assay/README.md
          this README declares none of the managed regions (overview, credentials, experiments, templates), so there is nothing `docs` may rewrite — a README is not regenerated from a template, because everything outside a region is hand-written
```

Filed: [the plugin scaffold's tree and its output disagree five ways](#the-plugin-scaffold-writes-neither-uvlock-an-example-config-nor-a-docs-region).
The names are derived from the distribution's own stem, which is why nothing needs editing to be
resolvable: `publishable-plate-assay` → template `plate_assay`, resolver `plate_assay_units`, probe
`plate_assay_instrument`, suffix `.plate_assay`.

### 2. The entry points are the registration

```toml
[project.entry-points."publishable.templates"]
"plate_assay" = "publishable_plate_assay.templates.plate_assay:PlateAssayTemplate"

[project.entry-points."publishable.resolvers"]
"plate_assay_units" = "publishable_plate_assay.resolvers.units:resolve"

[project.entry-points."publishable.probes"]
"plate_assay_instrument" = "publishable_plate_assay.probes.instrument:probe"

[project.entry-points."publishable.writers"]
".plate_assay" = "publishable_plate_assay.writers.artifact:write"

[project.entry-points."publishable.readers"]
".plate_assay" = "publishable_plate_assay.writers.artifact:read"
```

The key is what a config writes, and core resolves it **from installed metadata without importing the
package** — which is how `validate` answers "no installed package registers `plate_wells`" while
creating nothing and reaching nothing. The `@register_*` argument must agree with the key; when the two
disagree, loading fails naming both rather than one silently winning.

### 3. Install it

The documented flow is one flag on a creation command, and it is `uv add` and nothing more:

```bash
publishable generate experiment my-pilot \
  --plugin someuser/publishable-plate-assay \
  --template plate_assay \
  --input-dir /…/data --output-dir /…/results
```

`--plugin <user>/<repo>` expands to `uv add git+https://github.com/<user>/<repo>`, so publishing is
"push to GitHub" and pinning is whatever `uv` supports (`…@v1.2.0`). While developing locally there is no
remote yet, so add it by path instead — this is a local stand-in for the flag, not a second supported
form:

```bash
uv add --editable ../publishable-plate-assay
```

`uv run` re-syncs when the plugin's `pyproject.toml` changes, so a **new** entry point is picked up
without a manual reinstall — it reinstalls the package and resolves the name. Invoking the console script
directly does not, and the diagnostic enumerates the stale set rather than guessing:

```
$ ./.venv/bin/publishable validate configs/my-pilot/config.yaml
  error   E-RESOLVER-UNKNOWN   data.units
          `data.units.from.resolver` names `plate_assay_probe3`, which no installed distribution registers in the `publishable.resolvers` entry-point group (registered: plate_assay_units, plate_assay_wells)
```

The same config through `uv run publishable validate` prints `Installed 1 package` and then
`✓ config valid`. Stay inside `uv run` while developing a plugin, or `uv sync` after every entry-point
change.

### 4. The template half does not load at this build

```
  error   E-TEMPLATE-INSTALLED-UNSUPPORTED names `plate_assay`, which publishable-plate-assay 0.1.0 registers as a `publishable.templates` entry point — but core resolves an installed template's name without importing its package, and loading one is not implemented in this build; installed templates will be honored in a later slice. Use a project-local `templates/` file or a core template for now
```

`list-templates` says the same thing where it would otherwise print a spec:

```
### `plate_assay`

Installed, provided by `publishable-plate-assay 0.1.0` — its parameter spec is **not readable in this
build** (`E-TEMPLATE-INSTALLED-UNSUPPORTED`) — core resolves an installed template's name from package
metadata without importing the package, so there is no class here to read a `parameter_spec` off.
```

So keep the template project-local for now and let the plugin carry the machinery. Keep the class in the
plugin anyway — it is the artifact that becomes usable the day loading lands, and it is testable today
without core loading it at all, which is what [Testing a plugin](#testing-a-plugin) does.

**A name is claimed once**, so promoting a local template to a plugin means deleting the local file.
Installing a plugin beside a local template of the same name is refused, with both providers named:

```
E-TEMPLATE-COLLISION: the template name `my_assay` is claimed more than once:
/…/lab-study/templates/my_assay.py::MyAssayTemplate and publishable-my-assay 0.1.0 — a template that
could redefine another's name could change what a config means without changing the config, which is
what `parameters_hash` exists to make impossible. Install order and import order are the only
tie-breaks available, and both are properties of a machine rather than of a design. Rename yours.
```

### 5. A resolver — the reason most plugins exist

A CSV index is the same everywhere and core reads it. A DICOM archive whose units are series rather than
files, a plate layout keyed by barcode and well, a benchmark shipped as sharded JSONL: finding units
there is domain work, and it is the **only** domain work in `data.units`.

```python
from publishable import Unit, register_resolver


@register_resolver("plate_assay_units")
def resolve(io, cfg):
    for row in io.read_input("index.csv"):
        yield Unit(key=row["id"], paths=(), attributes={"site": row["site"]})
```

`io` is read-only. `cfg` is what a `scope: "run"` step sees, so a swept parameter is unreadable here by
construction: the unit table is **one** table for the whole run, and a roster that varied by condition
would make the conditions incomparable. Yield order is kept, and it is data —
`assign.method: blocked` balances arms across it and `units_hash` covers the list in it.

```yaml
    from: {resolver: plate_assay_units}
```

```
  ✓ config valid · configs/my-pilot/config.yaml
```

The run record then carries what produced the roster, which is the concrete payoff of packaging rather
than pasting:

```yaml
  plugin_versions:
    publishable-plate-assay: 0.1.0
```

### 6. A probe — for the facts you can only observe

A probe is `probe(cfg) -> Apparatus`, and `Apparatus` carries `facts` and nothing else:

```python
from publishable import Apparatus, register_probe


@register_probe("plate_assay_instrument")
def probe(cfg):
    return Apparatus(facts={"firmware": "4.2.1", "calibration_id": "cal-2026-08-01"})
```

The template declares which probe and which facts it requires — a declared fact the probe does not
supply is a diagnostic, not a silence:

```python
    apparatus_probe = "plate_assay_instrument"
    apparatus_facts = ["firmware", "calibration_id"]
```

Core calls it at run start and before every execution, and assembles the record itself:

```yaml
  apparatus:
    probe: plate_assay_instrument
    ledger: apparatus/probes.jsonl
    hash: sha256:484899159bfcb33ba6b2eb23841c87f27ce76e3ab3e59bfa55f9aa4ea6b98a58
    facts:
      00_threshold=0.4:
        firmware: 4.2.1
        calibration_id: cal-2026-08-01
    unobserved:
      firmware:
        null_probes: 0
        total_probes: 12
```

Twelve probes for ten executions: `apparatus/probes.jsonl` holds twelve lines, the first two carrying `"phase": "run_start"` — one per condition — and one per execution after them. A fact that
**moves** from its first answered observation fails the run — that gate is the reason a probe is worth
declaring, and it is why a probe must never return something it computed rather than observed.

### 7. A writer and its reader, resolved from the claim

```python
from publishable import register_reader, register_writer


@register_writer(".plate_assay")
def write(obj) -> bytes:
    return str(obj).encode()


@register_reader(".plate_assay")
def read(payload: bytes):
    return payload.decode()
```

A step calling `io.write("readings.plate_assay", {"n": 6})` with the plugin installed and **nothing
importing it** writes the artifact beside `units.parquet` in each step directory. `io.write` decides the
suffix over what a writer has registered *plus every suffix an installed distribution claims* — the claim
read from package metadata, and only the winning one loaded — so a plugin's pair works the way its
resolver and its probe do, without a step importing anything for a side effect.

Three rules to know, each of which the dispatch enforces rather than documents:

- **A claim wins only by being strictly longer than what is registered.** `.fastq.gz` beats `.gz`; a
  claim on `.csv` never takes `.csv` from core. That is what keeps core's five unshadowable, and
  `E-PLUGIN-COLLISION` is what refuses such a claim outright at decoration.
- **Each writer takes exactly what its reader gives back.** A pair is registered through two entry-point
  groups, and dispatch is decided from the writer side alone — so a reader for a suffix no writer answers
  for is never consulted, and the file reads back as bytes.
- **A plugin's top level runs at the first write of its suffix**, inside a step and therefore inside an
  execution. A module that raises there is `E-PLUGIN-LOAD` failing that execution, with the run record
  still written; a `KeyboardInterrupt` still stops the command. A plugin doing slow work at import pays
  for it inside a measured execution, so do the work in the writer rather than at module scope.

Until 2026-08-27 none of this was true: the suffix was decided over registered writers alone, so a step
writing a mapping to a plugin's own suffix lost **every** execution —

```
run failed: 10 of 10 executions failed; first error at step01_summarize_units · condition 0 · seed96: E-ARTIFACT-UNWRITABLE ArtifactError: readings.plate_assay has no registered writer, so the object must be bytes or str, not dict
```

— and the remedy was an `import publishable_plate_assay.writers.artifact` in step code, which appeared
in no document. If you are reading a plugin written against an older build, that import is now
unnecessary and harmless.

---

## Testing a plugin

The scaffolded `tests/test_<stem>.py` asks one question, and which question it asks is the interesting
part:

```python
from importlib.metadata import entry_points

from publishable import Param

GROUP = "publishable.templates"
NAME = "plate_assay"


def _registered():
    found = [entry for entry in entry_points(group=GROUP) if entry.name == NAME]
    assert found, (
        f"no installed distribution registers `{NAME}` in `{GROUP}` — run these "
        "tests through `uv run pytest`, which installs this package first"
    )
    assert len(found) == 1, f"`{NAME}` is registered {len(found)} times: {found}"
    return found[0].load()


def test_the_entry_point_resolves_to_the_registered_template():
    assert _registered().__name__ == "PlateAssayTemplate"


def test_the_spec_declares_parameters_and_every_value_is_a_param():
    spec = _registered().parameter_spec
    assert spec, "a `parameter_spec` that is empty declares no parameters at all"
    assert all(isinstance(param, Param) for param in spec.values())
```

It asserts nothing about *which* parameters the spec declares, deliberately. The spec it ships with is a
placeholder whose own help text says to replace it, so a test enumerating those keys would go red on your
first real edit — and a test that fails on arrival gets deleted rather than fixed. What it asserts instead
survives every domain edit and still fails when the package is genuinely broken. Measured:

| Mutation | Result |
|---|---|
| Typo the class name in the entry point | `2 failed` |
| Delete `parameter_spec` | `1 failed, 1 passed` |
| Remove `@register_template` | `2 passed` — **not covered here**; that agreement is `check_registration`'s (`E-PLUGIN-DECORATOR`), which runs wherever core loads the object behind a key |

The second row is what proves the two tests are not measuring one thing. The third is the omission, stated
rather than left for you to discover.

**Your own tests go past that, and they are plain Python** — import the class, call the method, assert the
claim. No run, no config on disk, no installed-template loading:

```python
from publishable_plate_assay.templates.plate_assay import PlateAssayTemplate


def test_the_spec_declares_exactly_the_parameters_a_config_must_carry():
    assert set(PlateAssayTemplate.parameter_spec) == {
        "instrument.model",
        "instrument.gain",
        "analysis.threshold",
    }


def test_a_swept_calibration_is_refused_and_the_message_names_it():
    messages = PlateAssayTemplate().validate(
        {"sweep": {"grid": {"instrument.gain": [1.0, 2.0]}}}
    )
    assert len(messages) == 1
    assert "instrument.gain" in messages[0]


def test_a_swept_analysis_parameter_is_not_refused():
    assert PlateAssayTemplate().validate(
        {"sweep": {"grid": {"analysis.threshold": [0.4, 0.6]}}}
    ) == []
```

**Then prove they can fail.** Deleting the two-line rule from `validate` gives:

```
tests/test_plate_assay.py:16: AssertionError
FAILED tests/test_plate_assay.py::test_a_swept_calibration_is_refused_and_the_message_names_it
1 failed, 2 passed
```

Restored, `3 passed`. The third test is what makes the second one mean something: a refusal test alone
passes just as well against a template that refuses **everything**. Enumerate the spec's keys rather
than counting them, for the same reason — a count passes against the wrong three parameters. And note
what these three do *not* need: none of them enumerates the spec of the **shipped** template, which is
exactly the coupling the scaffolded pair avoids.

`pytest` is declared as a dev group by the scaffold, so `uv run pytest` inside the plugin works with
no setup — it installs the package first, which is what makes the entry point resolvable.

---

## What this build refuses, by code

Measured on 2026-08-27 at `e61dcb4`. Every code below was produced by running the thing that produces it.

| Code | When | What to do |
|---|---|---|
| `E-TEMPLATE-INSTALLED-UNSUPPORTED` | a config's `experiment_type` names an installed plugin's template | keep the template project-local in `templates/`; ship machinery in the plugin |
| `E-TEMPLATE-COLLISION` | one template name claimed twice — two installs, or a local file beside an install | rename yours; when promoting a local template, delete the local file |
| `E-PLUGIN-COLLISION` | two installs claim one resolver/probe/writer/reader name, or a writer claims a core suffix | claim a suffix or a name of your own |
| `E-TEMPLATE-RULE` | a template's `validate` returned a message, or raised | your message, or your bug — a raise is reported here rather than crashing |
| `E-PARAM-UNKNOWN` · `E-PARAM-MISSING` · `W-PARAM-UNSET` | a config disagrees with `parameter_spec` | edit the config; `init` will not rewrite one that exists |
| `E-ARTIFACT-UNWRITABLE` | `io.write` found no writer and no claim for the suffix, and the object is not `bytes` or `str` | register or claim a writer for it, or hand `io.write` bytes |
| `E-DOCS-NO-REGIONS` | `publishable docs` in a README with no managed regions | add the regions, or do not run `docs` in a plugin |
| `E-EXPERIMENT-EXISTS` | `init`/`generate experiment` on an experiment that exists | edit the config by hand; generators never modify what they did not create |
| `E-CODE-DIRTY` | `run` with uncommitted changes under `src/**` or `templates/**` | commit first; a local template is inside `code_hash` |

---

## The gaps this tutorial found

Five, all measured on 2026-08-27 against `937591f` and filed in
[`spec-defects.md`](superpowers/spec-defects.md) with their reasoning and their severity. They are listed
here so a reader of this tutorial knows which of its instructions exist to route around a defect rather
than to teach a rule.

**Three are closed.** *A scaffolded project cannot be built by `uv`* and *the scaffolded test cannot
fail* were closed in the same change that added this file — `scaffold.PYPROJECT` gained `[tool.uv]
package = false`, and `plugin_scaffold.TEST_PY` was replaced by the entry-point pair in
[§ Testing a plugin](#testing-a-plugin). *A plugin's writer never dispatches unless something imports its
module* was closed next, by the slice [`W1-SCOPING.md`](superpowers/W1-SCOPING.md) chartered — the suffix
is now resolved over installed claims as well as registrations, which is what
[§ 7](#7-a-writer-and-its-reader-resolved-from-the-claim) describes. All three are struck in
`spec-defects.md`, and this section lists the two that remain. They are named rather than dropped because
a reader who heard there were five should be able to see which three went and how.

### `template.validate` receives a plain dict, not the dot-access config node

[§ The importable surface](reference.md#the-importable-surface) states that a template's
`validate(self, config)` receives the same node core's own config access uses, "which is how a cross-block
rule reads `data.units.holdout` without core handing it a second shape". It receives
`yaml.safe_load`'s dict, so that exact idiom raises `AttributeError` and lands as `E-TEMPLATE-RULE`.

### The plugin scaffold writes neither `uv.lock`, an example config, nor a `docs` region

[§ Creating a plugin](reference.md#creating-a-plugin-publishable-plugin-new) shows a tree containing
`uv.lock` and `examples/<stem>/config.yaml`, and a README with "a parameter table generated from
`parameter_spec` itself" whose payoff sentence is "Add a parameter and run `publishable docs`". The
scaffold writes no lockfile, creates `examples/<stem>/` empty, and writes a README with no managed
regions — so `docs` refuses there with `E-DOCS-NO-REGIONS` at exit `1`.
