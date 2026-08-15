# H7a Project-local templates — scoping measurement

Read-only measurement, 2026-08-14, against `docs/reference.md`, `CLAUDE.md` and
`src/publishable/` at `cb96c7d` (branch `main`, clean; H1, H2, H3a, H3b landed). No tracked
file was changed. Every claim below states the command that produced it, and every absence
claim is paired with a **can-fail control** — a perturbation of the same command that fires.

Probes ran against a **real scaffolded project** at
`scratchpad/probe/my-study`, built by `publishable new`, carrying a hand-written
`templates/my_assay.py`. Nothing was probed by reading source alone where running it was
possible.

**Headline.** The charter's three absences are all confirmed, and the slice is **bigger than
those three lines** for a reason none of them names: two of § Templates' four claims about a
project-local template are **already build-true and currently vacuous**, and the two that are
missing drag an ordering change in `validate_config`, a registry whose staticness is encoded in
three signatures, two error codes that do not exist, and a `template_version` warning that has
no meaning for a local template but will be written into every config that uses one.
Recommended count: **15 tasks** — 10 code, 5 documentation. Not splittable: the doc rows and
the code are bound in both directions by `tests/test_cli.py`.

## Method

| Probe | What it ran | Where |
|---|---|---|
| Scaffold probe | `publishable new`, then `generate experiment --template my_assay` and `--template generic` as its control | `scratchpad/probe/my-study`, outer repo's `.venv/bin/python`, cwd inside the project |
| Validate probe | `main(["validate", config])` with `experiment_type` flipped between `generic` (control) and `my_assay` | same project |
| Hash probe | `hashes.hashed_files` and `hashes.code_hash` before and after editing `templates/my_assay.py` | same project |
| Import probe | `importlib.util.spec_from_file_location` on `templates/my_assay.py`, then `git status --porcelain -- src templates` and `hashed_files` again | same project |
| Absence greps | `grep -rn` over `src/`, `tests/`, `docs/*.md`, each paired with a control grep of the same shape that returns hits | outer repo |

The scaffolded project cannot `uv sync` (its `pyproject.toml` pins `publishable` from a registry
that does not carry it), so every probe ran the **outer repo's** interpreter with the project as
cwd. That is exactly what the CLI does — `find_repo_root(Path.cwd())` for generators,
`find_repo_root(config_path)` for operations — so the walk-up under test is the real one.

## 1. What exists: the contract a template must satisfy

Read from the code, not from § Templates. `BaseTemplate` (`templates/base.py`, 38 lines)
declares **nine** members. `GenericTemplate` overrides six of them with the same values and
supplies a four-entry `parameter_spec`; it defines **no `aggregate`**, inheriting the
`{}`-returning default. The registry between them is `_BUILTIN = {"generic": GenericTemplate}`,
`get_template(name)` returning a fresh instance, `template_names()` returning `sorted(_BUILTIN)`.

`grep -rn "apparatus_probe\|apparatus_facts\|naming_pattern\|field_convention\|default_repeats\|required_env\|\.parameter_spec\|template\.validate\|\.aggregate(" src/publishable/` over the
whole package, and each member's real consumers:

| Member | Read by | Effect |
|---|---|---|
| `parameter_spec` | `materialize` (what `init` writes and its inline comments), `validate._check_parameters`, `_check_versions`, and two more `validate` sites resolving swept paths | `E-PARAM-UNKNOWN` / `E-PARAM-VALUE` / `E-PARAM-MISSING`; the single source of truth |
| `validate(config)` | `validate_config`, **one** call site, run **last** and ungated by every other finding | each returned message becomes `E-TEMPLATE-RULE` on field `parameters` |
| `aggregate(units, cfg)` | `cli.command_run`, **two** call sites: the single unresampled point estimate (contained by `try` → `W-STATS-AGGREGATE-FAILED`) and a per-key closure re-run on every bootstrap draw | derived metrics with `basis: units`; four-operation table in, flat mapping of scalars out, no `Estimate` exception |
| `naming_pattern` | `validate._check_metadata` | `E-NAME-PATTERN` against `metadata.name` |
| `default_repeats` | `validate` (the repeat-count check) | the warning floor for total repeats |
| `field_convention` | **nothing** | — |
| `required_env` | **nothing** | — |
| `apparatus_probe` | **nothing** | — |
| `apparatus_facts` | **nothing** | — |

**Five of the nine are live; four are declarable and dead** — the grep finds
`field_convention`, `required_env`, `apparatus_probe` and `apparatus_facts` only in `base.py`
and `generic.py` themselves. `required_env` is `secrets.py`'s (`— not yet built`); the two
apparatus members are H7's. This is not a footnote: it decides what task 9's `generate template`
stub may emit, since a stub that writes four attributes nothing reads teaches the wrong contract
on day one.

So the whole contract a template must satisfy today is: subclass `BaseTemplate`; supply a
`parameter_spec` of `Param`s; optionally override `validate` (whole config in, list of message
strings out) and `aggregate` (four-operation table + resolved `cfg` in, flat mapping of scalars
out, `{}` for a table it does not recognize); optionally set `naming_pattern` and
`default_repeats`. Nothing else is read.

## 2. The three absences, confirmed

```
ImportError: cannot import name 'register_template' from 'publishable'
template_names() -> ['generic']
get_template('my_assay') -> None          # with templates/my_assay.py present on disk
get_template('generic')  -> <GenericTemplate object>      # can-fail control
```

| Charter claim | Verdict | Evidence |
|---|---|---|
| `register_template` not exported | **confirmed** | `ImportError` above; `grep -rn "def register_" src/publishable/` run this session returns nothing (exit 1) — zero of the four registries exist, which `spec-defects.md` § The importable surface names five things independently records |
| Nothing discovers `templates/**` by path | **confirmed** | `templates/registry.py` is 15 lines: a module-level `_BUILTIN = {"generic": GenericTemplate}`, `get_template(name)`, `template_names()`. `grep -n "templates" src/publishable/validate.py` returns only the two import lines. `importlib` appears in exactly two modules, `base_experiment.py` (the entrypoint) and `cli.py` (`importlib.metadata.version`) — no `spec_from_file_location` anywhere |
| `generate template` not implemented | **confirmed** | `cli.NOT_BUILT_GENERATORS = {"report": …, "template": "Generators"}`; `_dispatch_generate` routes `experiment` and `step` only |

**End to end, with its control.** In a project that *has* `templates/my_assay.py`:

```
generate experiment --template my_assay  -> E-TEMPLATE-UNKNOWN  no installed template
                                            registers `my_assay`            exit 1
generate experiment --template generic   -> exit 0                        # CONTROL

validate (experiment_type: my_assay)     -> E-TEMPLATE-UNKNOWN  experiment_type
                                            names `my_assay`, which no installed template
                                            registers (known: generic)    1 problem
validate (experiment_type: generic)      -> E-META-REQUIRED ×2,
                                            E-DATA-UNREADABLE             3 problems  # CONTROL
```

The control is load-bearing twice: it shows the same file validating past the template check,
and it shows the three findings the `my_assay` run **suppressed** — confirming § Errors'
documented early return (`E-TEMPLATE-UNKNOWN` fires exactly once and nothing else fires with
it).

## 3. Spec claims vs. build facts, separated

`reference.md` § Templates makes four claims about the third home. **Two are already
implemented.** Stating this is the point of the section — the repo has just been through a fix
for reading one paragraph as one undifferentiated promise.

| § Templates claim | Status | Evidence |
|---|---|---|
| "`code_hash` covers `templates/**` alongside `src/**` — editing a local `aggregate` moves the hash exactly as editing a step does" | **BUILT** | `hashes.HASHED_TREES = ("src", "templates")`. Probe: `hashed_files` over the project returns `templates/.gitkeep` and `templates/my_assay.py`; editing one character of `my_assay.py` moved `code_hash` from `sha256:f4ab556…` to `sha256:35d86c4…` |
| "`run` refuses a dirty `templates/` for the same reason it refuses a dirty `src/`" | **BUILT** | `provenance.git_provenance` computes `dirty` from `git status --porcelain -- src templates` (the same `HASHED_TREES` tuple); `cli.command_run` raises `E-CODE-DIRTY` on `src/** or templates/**` before any execution. Probe: `git status --porcelain -- src templates` reports `?? templates/my_assay.py` |
| "discovered by path from the fixed layout" | **NOT BUILT** | § 2 |
| "its `@register_template` argument [is] the whole of its registration" | **NOT BUILT** | § 2 |

**So the two hash/provenance claims are true and currently vacuous** — precisely: the only thing
core ever *writes* into `templates/` is the `.gitkeep` the scaffold puts there
(`scaffold.scaffold_project` creates `src`, `templates`, `configs`, `tests`, `docs`, each with a
`.gitkeep`), and that `.gitkeep` *is* hashed. A hand-placed `my_assay.py` is hashed and made
dirty too — the probe above did exactly that — it simply cannot be **resolved** by any supported
path, so no run's numbers can have come out of it. H7a builds neither claim; it makes both
load-bearing. Nothing in the hash or
provenance layer is H7a work.

**What the documents specify beyond § Templates:**

- § Creating a plugin, *Two things register without an entry point*: a local `templates/*.py`
  "is found by path, from the fixed layout … Its `@register_template` argument is therefore the
  whole of its registration, which is the one case where the decorator is authoritative rather
  than checked."
- § Creating a plugin, *A name is claimed once*: "a local `templates/*.py` taking the name of an
  installed one" fails **at load**, "naming both providers." Shadowing `generic` is refused in
  the same breath.
- § Three hashes: "`template_version` isn't the answer for a local template — it's a string its
  author remembers to bump."
- § Generators: the `template` row, `NOT BUILT`, `publishable g template my_assay` →
  "`templates/my_assay.py` with a `BaseTemplate` + `parameter_spec` stub … Its parameter table
  is added to the README."
- § The importable surface: `register_template` sits in a **four-name row** marked `not yet
  built`, under a paragraph stating "Importing one raises `ImportError` today."

**What `E-TEMPLATE-UNKNOWN` says today** — build fact, quoted from `validate.py`:

> `experiment_type` names `my_assay`, which no installed template registers (known: generic)

and its § Errors row: "`experiment_type` names a template no installed package registers." Both
wordings stop being true the moment a template that is *installed nowhere* can resolve. The
"(known: …)" list is `template_names()`, which takes no argument and therefore cannot name a
local one.

## 4. The seams

**How `validate` resolves a template today.** `validate_config` (`validate.py`, after
`_check_shape`):

```
name = doc.get("experiment_type", "")
template = get_template(name)
if template is None: c.error("E-TEMPLATE-UNKNOWN", …); return None
```

Only *then* does the entrypoint branch below it discover the repo root, and it does so
defensively:

```
try:    repo_root = find_repo_root(config_path)
except ContractError:  repo_root = None      # "That is `_check_data`'s finding to make (or not)"
```

**Where path discovery attaches: the `find_repo_root` call must be hoisted above the template
resolution, and must stay silent on failure.** Two constraints pin the shape:

1. § Errors documents the early-return order — parse, container shape, then
   `E-TEMPLATE-UNKNOWN` "exactly once, since that check returns immediately after," with none
   of the other rows. A hoisted `find_repo_root` that *reported* a missing repo would put a new
   finding ahead of a documented one. The existing `repo_root = None` precedent is the pattern
   to reuse, and the behaviour to write down is: **no repo → local discovery is skipped,
   `generic` still resolves.**
2. `get_template(name)` and `template_names()` both take no argument, and `_BUILTIN` is a
   module-level dict. **Staticness is encoded in three signatures, not just in the dict's
   contents.** `template_names()` is called inside the `E-TEMPLATE-UNKNOWN` message, so the
   "known:" list cannot include a local name without a repo root reaching it.

**Every call site of `get_template`, and whether a repo root is at hand:**

| Site | Repo root available? |
|---|---|
| `validate.validate_config` | only below the template check, and only inside a `try` — needs the hoist |
| `cli.command_run` (the `aggregate` block) | yes — `repo_root = find_repo_root(config_path)` is already bound in the same function |
| `generators/experiment.generate_experiment` | yes — it is a parameter |

**Two test bindings a signature change breaks**, both must be updated in the same task:
`tests/test_templates.py` calls `get_template("generic")` / `get_template("llm_diagnostic")`
positionally, and `tests/test_validate.py` monkeypatches
`validate_mod.get_template` with `lambda name: RuleBreaker()` — a one-argument lambda.
`tests/test_materialize.py` calls `get_template("generic")` twice.

**What reads `template_version`** — four places, and none of them reads a template:

| Reader | What it does |
|---|---|
| `materialize.py` | `TEMPLATE_VERSION = "1.0.0"`, a **module constant**, written into every config `init` materializes and into the header comment |
| `validate._check_versions` | compares `doc["template_version"]` against that same constant and warns `W-TEMPLATE-VERSION`, listing every defaulted-and-unset `parameter_spec` path |
| `envelope.py` | declares it a leaf of type `str` |
| `validate._STRING_BLOCKS` | shape check |

`BaseTemplate` declares **no version attribute at all** (`grep` over `templates/base.py`:
`naming_pattern`, `field_convention`, `default_repeats`, `required_env`, `apparatus_probe`,
`apparatus_facts`, `parameter_spec`, `validate`, `aggregate` — that is the whole class). § Errors'
`W-TEMPLATE-VERSION` row already admits this: "in this build, compared against the one version
core itself writes, since `generic` is the only installed template and a template class reports
no version of its own."

**Does anything assume the template set is static?** Yes, in three ways, all of them cheap to
fix and none of them free:

- the two zero-argument signatures above;
- `_BUILTIN` being module-level means a decorator writing into it makes the registry
  **process-global while being repo-dependent** — two projects in one process (this test suite
  today; `study add` later) cross-contaminate. `base_experiment.load_experiment` already carries
  the precedent and the reasoning: it purges the entrypoint's root package from `sys.modules`
  because "two projects in one process can declare the same package name … and a cached module
  would silently hand back the other project's steps";
- `tests/test_templates.py`'s `get_template("llm_diagnostic") is None` asserts the closed set by
  name.

## 5. Traps

**The three sharpest, in order.**

**(a) Discovery inverts the spec's own argument for entry points.** § Creating a plugin
justifies entry-point resolution by saying `validate` can answer "no installed package registers
`plate_wells`" "**without importing a line of that package**, which matters because importing a
module runs its top level and `validate` is documented as creating nothing and reaching
nothing." A local template's decorator argument *is* its registration, so its name **cannot be
learned without importing the file** — and because a collision must "fail at load, naming both
providers," discovery has to scan **every** file in `templates/`, not only the one the config
names. So `validate` will import user files no config references. The spec accepts the premise
and nowhere states the consequence; **H7a owes that sentence.**

This does **not** breach the greenfield invariant — importing is not inspecting, and core still
never reads the body of user Python; the same line `validate` already crosses for `entrypoint`
("that is also the one thing `validate` executes", § Generators). But it **widens** that
exception from one named module to a whole directory, and the widening is a documented promise
changing, not an implementation detail.

**(b) The registry is static by signature, and a decorator makes it globally mutable.** See
§ 4. The shape that survives is a mapping built **per call** from a repo root, with the
decorator draining into a transient collection rather than a persistent module-level dict —
otherwise a second config in the same process resolves the first project's template. Path-imported
modules also need a naming scheme that cannot alias across two repos, which is the exact failure
`load_experiment`'s `sys.modules` purge exists to prevent.

**(c) `W-TEMPLATE-VERSION` has no meaning for a local template, and `materialize_config` will
write one anyway.** `generate template my_assay` then `generate experiment --template my_assay`
runs `materialize_config`, which writes `template_version: "1.0.0"` from core's own module
constant — a string certifying nothing, for a template § Three hashes says explicitly is pinned
by `code_hash` instead. `_check_versions` then compares a *local* template's config against
*core's* constant. The warning either fires spuriously or must be suppressed for locals, and
`plugin:` has no defined value for a template that came from no plugin. **Nobody predicts this
from the charter.** It is the single best reason the slice is bigger than three lines.

**Two traps that probed clean, recorded so they are not re-litigated.** Importing
`templates/my_assay.py` by path creates `templates/__pycache__/`; the probe confirmed
`git status --porcelain -- src templates` still reports only `?? templates/my_assay.py` (the
scaffold's `.gitignore` carries `__pycache__/` and `*.py[cod]`) and `hashed_files` still returns
seven files, none of them a `.pyc` (`hashes._SKIP_DIRS` / `_SKIP_SUFFIXES`). So neither the
dirty gate nor `code_hash` is disturbed by discovery — **in a project the scaffold wrote**. A
hand-made repo whose `.gitignore` lacks `__pycache__` would go dirty on `validate` and fail
`run`, which is worth one sentence somewhere.

**A gap this measurement found that `spec-defects.md` does not carry.** § The generated README
specifies managed regions `overview`, `credentials`, `experiments`, and says "`generate
experiment` adds a row to the experiments table and merges any new `required_env` into the
credentials table." Build fact: `scaffold.README` contains **only** `overview` and `experiments`
(no `credentials`, and neither holds a table), and `generate_experiment` returns after writing
the config **without touching the README** — `grep -n "README" src/publishable/generators/experiment.py`
returns nothing. `publishable docs` is `NOT BUILT`. § Generators makes the same promise for
`generate template` ("Its parameter table is added to the README"), and § The generated README
specifies **no region for a template parameter table at all** — so where it would go is
undetermined. This is a pre-existing `generate experiment` defect plus a genuinely
under-specified spot; recommend recording it in `spec-defects.md` and **deferring the README
half of `generate template`** to whoever owns `docs`, rather than inventing a region here.

**Two things I could not determine from the documents:**

- Whether discovery is **eager** (import every `templates/*.py` at every `validate`) or **lazy**
  (import only until the named one is found). The collision rule pushes toward eager; the
  "`validate` creates nothing and reaches nothing" principle pushes toward lazy. The documents
  do not settle it, and it is a design decision this slice must make explicitly.
- What `plugin:` should hold for a config whose template is local. § The one config file and
  § Validation both describe it as naming where the template came from; neither names the local
  case.

## 6. Task decomposition — 15

Ten code, five documentation. The count is what the enumeration produced, not a target: H3b
reached 13 off three owned rows by counting each doc-table edit and each new code as its own
task, and the same grain is used here.

### Code

| # | Task | Why it is its own task |
|---|---|---|
| 1 | `register_template` decorator: define it, export it from `publishable/__init__.py` and `__all__`, with the "decorator argument is the whole registration" semantics | The one name of the four registries H7a ships |
| 2 | Path discovery: import every `templates/*.py` from a repo root, collect registrations. Decide **eager vs. lazy** and record the decision | § 5's undetermined question; the module's home also touches § Package layout (task 13) |
| 3 | Registry signature: `get_template` / `template_names` take an optional repo root and merge core builtins with local ones per call; update `tests/test_templates.py`, `tests/test_materialize.py`, and the one-argument monkeypatch in `tests/test_validate.py` | Three signature bindings in the suite; a partial change fails collection, not a test |
| 4 | Hoist `find_repo_root` above the template check in `validate_config`, silent on failure, preserving the documented early-return order and `E-TEMPLATE-UNKNOWN`-fires-exactly-once | The ordering constraint § Errors pins; probed and controlled in § 2 |
| 5 | Wire the other two call sites: `cli.command_run`'s `aggregate` block and `generators/experiment.generate_experiment` | `--template my_assay` must stop being `E-TEMPLATE-UNKNOWN` at generate time — the first probe in § 2 |
| 6 | Process hygiene: per-repo (not module-global) registration, and a module-naming scheme for path-imported files that cannot alias across two repos | Trap (b); `load_experiment`'s purge is the precedent to follow |
| 7 | Collision and shadow refusal + its new error code: two local files claiming one name, and a local claiming `generic`, each naming both providers | § Creating a plugin requires it; **no code exists** — `grep` returns only `E-TEMPLATE-UNKNOWN`, `E-TEMPLATE-RULE`, `W-TEMPLATE-VERSION` |
| 8 | Load-failure diagnostic + its new error code: a `templates/*.py` that raises on import, registers nothing, or registers a non-`BaseTemplate` | Same absence; and this is user code failing at `validate`, which must be a finding rather than a traceback |
| 9 | `generate template`: the `templates/<name>.py` stub (`BaseTemplate` + `parameter_spec` + `@register_template`), greenfield refusal on an existing file, and its `_dispatch_generate` route. The stub emits only the **five live** members of § 1's contract table — not `field_convention`, `required_env`, `apparatus_probe` or `apparatus_facts`, which nothing reads. **README half deferred** — see § 5 | The third charter absence |
| 10 | `template_version` / `plugin` under a local template: decide and implement what `materialize_config` writes and whether `_check_versions` warns | Trap (c) |

### Documentation

| # | Task | Why it is its own task |
|---|---|---|
| 11 | § Generators `template` row → `built`, the inline `` `template` (NOT BUILT) `` spelling in the § Operation commands `generate` row, and removal from `cli.NOT_BUILT_GENERATORS` | Bound in **both** directions by `test_reference_cli_tables_are_parsed_at_all` and `test_reference_cli_tables_match_what_the_cli_does`; must land atomically or the suite fails |
| 12 | § The importable surface: split the four-`register_*` row so only `register_template` is `built` | That table's `Status` is its **third** column, so the CLI test does not parse it — an unsplit row would silently claim three unbuilt exports |
| 13 | § Package layout: add the discovery module to the `templates/{base.py,registry.py,builtin/generic.py}` line, if task 2 lands a new file | "Modules marked `— not yet built` are specified and unbuilt"; the tree is normative |
| 14 | `E-TEMPLATE-UNKNOWN`: message wording and its § Errors row — "no installed template registers" / "no installed package registers" both stop being true — plus the "(known: …)" list now including local names | Wording is in two places, code and doc, and the doc row states the condition |
| 15 | § Errors rows for the two new codes (tasks 7, 8), and any § Validation ordering sentence they need | This repo registers every code in the table; a code with no row is the defect the table exists to prevent |

## 7. What is NOT in this slice

Named explicitly, because each is one reach away from a task above.

| Out | Why |
|---|---|
| Entry-point resolution (`importlib.metadata.entry_points`, `publishable.templates` group) | The whole point of the H7a carve-out: a local template is installed nowhere, so there is no package metadata to read. `E-DATA-RESOLVER-UNSUPPORTED` stays until full H7 |
| `register_resolver`, `register_probe`, `register_writer` | The other three registries; the § The importable surface row split (task 12) is what keeps them honestly marked `not yet built` |
| Probes and `Apparatus` | `apparatus_probe` / `apparatus_facts` are declarable `BaseTemplate` attributes that **nothing reads** — `grep` finds them only in `base.py` and `generic.py`. `apparatus.py` does not exist |
| The apparatus change gate | Same module, same slice — H7 |
| `plugin new` and `plugin_scaffold.py` | `NOT_BUILT_COMMANDS`; scaffolds a distributable package, which a local template by definition is not |
| `list-templates` | In `NOT_BUILT_COMMANDS`. Its entire job is enumerating the template set, so it is the first thing reached for after discovery lands — and it is still H7's, not H7a's |
| `publishable docs` and the managed README regions | `NOT_BUILT_COMMANDS`; carries the deferred half of task 9 and the pre-existing `generate experiment` gap in § 5 |
| Anything in `code_hash` or the dirty gate | Already built — § 3 |
| `BaseReport` / `generate report` | Unrelated registry-adjacent name; H7 exports it, H8 makes it do something |

**What H7a unblocks, restated against the spine design's own table:** 0 of the 9 feasibility
experiments, as written *and* with a table roster. It removes the gate that stops all nine at
the first check; H4 and H3d are what make any of them run.
