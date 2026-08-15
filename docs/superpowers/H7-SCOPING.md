# H7 Plugins and the apparatus — scoping the remainder after H7a

Read-only measurement against `main` at `cb96c7d` (Merge H3b Clustered units and partitions).
No tracked file was edited; this document is the whole deliverable.

Charter, from `docs/superpowers/specs/2026-08-08-implementation-spine-design.md` § The hardening
slices: *"The four registries, entry-point resolution, probes and the change gate, `secrets` /
`requires_env`"*, ordered *"after H1"*. H1 landed long ago, so this slice has been unblocked
throughout and deferred at every reorder. The same file's amendment of 2026-08-14 carved **H7a**
out of it — `register_template` exported, `templates/**` discovered by path, `generate template` —
because `reference.md` § Templates gives a template a third home that needs no entry point.

**This document scopes what is left after H7a.**

## Method

Every claim below is one of two kinds and is labelled as such, because this repo has just been
through a fix for conflating them (`docs/superpowers/spec-defects.md` § `register_template` appears
outside § The importable surface, and the same-day CORRECTION in the spine design):

- **Spec claim** — what one of the four documents says. Cited by section.
- **Build fact** — what `grep` over `src/`, `tests/` and `pyproject.toml` returns today.

Every identifier named here was verified by grep. Nothing is cited by line number.

---

## 1. What exists

### Build facts

| Thing | State in `src/` |
|---|---|
| `templates/registry.py` | 15 lines. `_BUILTIN = {"generic": GenericTemplate}`, `get_template(name)` returning an instance or `None`, `template_names()`. No decorator, no discovery, no plugin path |
| `BaseTemplate` | `templates/base.py`, 38 lines. Class attributes `naming_pattern`, `field_convention`, `default_repeats`, `required_env`, `apparatus_probe`, `apparatus_facts`, `parameter_spec`; methods `validate(config)` and `aggregate(units, cfg)` |
| `apparatus_probe`, `apparatus_facts` | **Confirmed inert.** Declared in `templates/base.py`, re-declared in `templates/builtin/generic.py`, asserted once in `tests/test_templates.py`. Grep for `apparatus` over `src/` and `tests/` returns exactly those, plus two prose comments (`stats.py`, `validate.py`) and one hardcoded `"apparatus": None` in `cli.py`'s run-record assembly. **Nothing reads either attribute** |
| `Apparatus` | Does not exist. No class, no import, no module `apparatus.py` |
| `register_template` · `register_resolver` · `register_probe` · `register_writer` | None exist. `grep -rn "def register_" src/publishable/` returns nothing |
| `secrets` | `src/publishable/secrets.py` does not exist. `python-dotenv` is **not** a dependency — `pyproject.toml` declares `pyyaml`, `numpy`, `scipy`, `pyarrow`. Grep for `dotenv` over `src/` returns nothing |
| `required_env` | Exists as a `BaseTemplate` attribute, default `[]`. Read by nothing but one test assertion |
| `requires_env` | **Does not exist as a `Param` argument.** `param.py`'s `__init__` takes `type_`, `default`, `choices`, `ge`/`gt`/`le`/`lt`, `pattern`, `item_type`, `min_items`/`max_items`, `nullable`, `help` — and nothing else |
| `Param` | Built and exported. Type/constraint checking, `required`, `check`, `comment` all live |
| Entry-point machinery | **None.** `importlib.metadata` is imported in `cli.py` and used at exactly one site, `importlib.metadata.version("publishable")`, for the `publishable_version` field of the run record. `importlib.import_module` appears once more, in `base_experiment.py`, to import the user's own `entrypoint` package from the repo. Grep for `entry_points` over `src/publishable/` returns one unrelated prose use of the words "entry point" in `correction.py` |
| Resolver execution | `units.py` contains no resolver dispatch at all. The word `resolver` appears twice, both inside message strings |
| Longest-suffix writer dispatch | **Built**, and this is the one invariant of the four already honoured: `artifacts.py`'s `_suffix_for` lower-cases the name's last component and takes the longest key of `WRITERS` that it ends with. `WRITERS` and `READERS` are two module-level dicts over the same five suffixes (`.json`, `.yaml`, `.jsonl`, `.csv`, `.parquet`) |
| CLI surface | `validate`, `run`, `new`, `generate`/`g`/`init`. `dry-run`, `draft`, `resume`, `demo`, `docs`, `freeze`, `diff`, `report`, `study`, `plugin new` are unbuilt |

### The one live wire between `batch` and the apparatus

`validate.py`'s `W-REPL-DETERMINISTIC` check reads `nondeterministic` off the step classes and warns
when a `batch` level is declared with no step setting it. Its own comment names *apparatus drift* as
what a `batch` exists to capture. That comment is the entire link between the `batch` repeat kind and
the apparatus mechanism in the build. See § 4.

---

## 2. The four registries: spec versus build

### What `reference.md` specifies

§ The importable surface lists all four as one row, `decorator`, **`not yet built`** — the table is
already honest, and a row marked so is documented as raising `ImportError` today.

§ Creating a plugin is where the mechanism lives, and it specifies four things:

1. **Four entry-point groups** — `publishable.templates`, `publishable.resolvers`,
   `publishable.probes`, `publishable.writers` — each paired with a `@register_*` decorator.
2. **A writer is keyed by the extension it claims**, not by a name, "since that is what `io.write`
   dispatches on — it takes the object and returns `bytes`, and its reader inverts it."
3. **The entry point is the registration; the decorator is a declaration checked against it**, so
   `validate` can answer "no installed package registers `plate_wells`" *without importing a line of
   that package*.
4. **A name is claimed once**; a collision or a shadow of a core name fails at load, naming both
   providers.

§ Where units come from specifies the resolver's own contract: a plain function `resolve(io, cfg)`
yielding `Unit`s, read-only `io` exposing `io.read_input` and nothing else, resolution order
preserved into `provenance.units_hash`, condition-independence enforced by `validate`, one `Unit`
per measurement under `data.units.measurements`, and the plugin's version recorded in
`provenance.plugin_versions`.

§ The apparatus core can only observe specifies the probe: `probe(cfg)` returning an `Apparatus`,
permitted — unlike a resolver — to read a swept parameter.

### What is built, per registry

| Registry | Spec claim | Build fact |
|---|---|---|
| `register_template` | Decorator; authoritative for a path-discovered local template, checked against the entry-point key otherwise (§ Creating a plugin, § Templates) | Absent. `get_template` reads a one-entry builtin dict (`generic`). **H7a covers the path-discovered half only** |
| `register_resolver` | Decorator; resolver runs at `validate` *and* `dry-run`, not only at `run` (§ Where units come from) | Absent, and so is any resolver execution path. `validate` refuses the declaration outright — see § 5 |
| `register_probe` | Decorator; `validate` checks only that the named probe *is registered*, never calls it (§ The apparatus core can only observe) | Absent, and so is everything downstream of it |
| `register_writer` | Decorator; keyed by extension; longest-suffix dispatch; "what a writer takes is what its reader gives back" (§ Steps and artifacts) | Absent. The *dispatch* it plugs into is built and correct; the plug is not. No plugin can add a suffix |

**The reverse direction is clean**: nothing in `src/publishable/__init__.py`'s `__all__` is a registry
name, so there is no half-built export claiming more than it does.

---

## 3. The invariants this slice must honour, made concrete

`CLAUDE.md` § Invariants states three that are H7's to keep. Each has a concrete mechanical
consequence, and one of them decides the shape of the whole slice.

### (a) The entry-point key *is* the registered name, so `validate` resolves without importing

`importlib.metadata.entry_points(group="publishable.resolvers")` returns `EntryPoint` objects whose
`.name` and `.value` are read from installed *distribution metadata*. Reading them imports nothing;
`.load()` is the import. That single distinction carries the whole invariant:

- **`validate` reads `.name` only.** It can answer "no installed package registers `plate_wells`"
  from metadata, which is what keeps the promise in § Creating a plugin and what keeps `validate`
  inside § The apparatus core can only observe's rule that it "may read your config and your input,
  and may not reach anything outside the machine" — and inside `reference.md` § Generators' rule
  that importing a module runs its top level.
- **The `@register_*` check is therefore a *load-time* check, not a validate-time one.** The
  decorator argument cannot be compared against the key until the object is loaded, which happens at
  `run` and `dry-run`. Stating this plainly is load-bearing: the two halves of "the entry point is
  the registration; the decorator is a declaration checked against it" execute on two different
  commands, and a slice that puts both at `validate` breaks the no-import promise.

### (b) A collision fails at load, never resolved by install order

The refusal set must be computed **over metadata only**, before any `.load()`, over the union of:

- entry-point names within one group, across every installed distribution;
- core's own registrations — `generic` for templates, and the five suffixes in `artifacts.WRITERS`
  for writers;
- the path-discovered local `templates/**` names H7a introduces.

Four distinct collisions are named in § Creating a plugin and all four must fail: two plugins on one
name, a plugin claiming `generic`, a plugin claiming an extension core already writes, and a local
template taking an installed one's name. The last is the seam with H7a — see § 9.

### (c) `io.write` dispatches on the longest registered suffix

Already built and already correct; `_suffix_for` is a longest-match over `WRITERS`, and § Steps and
artifacts argues it from `.fastq.gz` versus `.gz`. What H7 adds is third-party keys into that dict —
plus a constraint the build already satisfies implicitly and would newly need to enforce: `WRITERS`
and `READERS` must stay key-symmetric, because `io.read_upstream` inverts through `READERS`. **The
spec does not say how a plugin registers the reader** — see § 7, gap 4.

---

## 4. The apparatus: how much is specification with nothing underneath

Plainly: **all of it except two inert class attributes.**

`reference.md` § The apparatus core can only observe and § The apparatus files together specify the
`Apparatus` construct, `register_probe`, the `apparatus/probes.jsonl` ledger, the five
`provenance.apparatus` sub-keys (`probe`, `ledger`, `hash`, `facts`, `unobserved`), the per-condition
first-answered-observation gate, the three fact states (a value, a declared absence, a key that
isn't there), the null-transition rule, the credential-leak check on returned values, and
`apparatus.expected.json`.

Against that:

| Specified | Built |
|---|---|
| `Apparatus` construct | nothing |
| `register_probe` | nothing |
| `apparatus.py` (§ Package layout, marked "— not yet built") | nothing |
| `apparatus/probes.jsonl` | nothing |
| `provenance.apparatus.{probe,ledger,hash,facts,unobserved}` | `cli.py` writes the literal `"apparatus": None` |
| the change gate | nothing |
| probe execution at four phases | nothing |

**Four of the six surfaces that consume the apparatus belong to other slices**, and this is the
argument that the apparatus is not as blocked as it looks. § The apparatus files says the ledger is
written "at `dry-run`, at run start, before each execution, and at `freeze`":

| Surface | Owner |
|---|---|
| run start, before each execution | **H7** |
| `dry-run` — where the declared-keys check, the credential check and the null-fact warning live | H9 |
| `freeze` | H8 |
| `diff`'s `apparatus DIFFERS` row | H8 |
| `apparatus.expected.json`, written by `reproduce` | H9 |
| `resume` refusing a changed apparatus | H9 |

So the apparatus sub-slice delivers the registry, the probe call, the ledger, the per-condition
facts, the gate, and the two run-time placements. The other four are hooks later slices call. None
of them blocks it.

### `nondeterministic` and the `batch` repeat kind

`CLAUDE.md` § Invariants defines `batch` as "the state of the apparatus it measures through", and
`W-REPL-DETERMINISTIC` is built and live. **That is a warning about step declarations, not an
apparatus mechanism**, and nothing connects the two in code. A `batch` level today executes repeats
in order with no probe, no ledger and no gate — exactly as it will after H7, since a `batch` says
*when* rather than *what* (§ A `batch` says *when*, not *what*). H7 owes no change to `batch` and
should ship a test asserting the independence, so that nobody later "connects" them.

---

## 5. `E-DATA-RESOLVER-UNSUPPORTED`, and the skip a measurement had to work around

### What the refusal says and where it is raised

`validate.py`'s `_check_unimplemented` reports it against `data.units.from.resolver`, and the
message names the reason: *"resolvers are plugin artifacts and the plugin registry is not
implemented in this build"*. That is why `docs/superpowers/H3-SCOPING.md` moved it out of H3 and
into H7, and why the spine design's H3 row says *eight* of the nine `-UNSUPPORTED` refusals.

### The skip, and why a reader would not expect it

`validate._check_units` — the function whose whole purpose is *"Resolve the roster so unit checks
are real rather than deferred to run time"* — **returns early and resolves nothing** when the source
is a resolver mapping. Its docstring states the reason: `resolve_units` cannot execute a resolver
either, and without the skip it would raise `E-UNITS-SOURCE-MISSING`, "describing a resolver as a
missing file."

The consequence is what a measurement has to work around: **under `from: {resolver: ...}` the entire
unit-checking family is silently inert.** Key uniqueness, attribute presence, stratum population,
`k` against the cluster count, `W-DATA-CLUSTER-UNDECLARED`, `W-DATA-WEIGHT-UNDECLARED`,
`W-STATS-REPORTBY-THIN` — every check that reads a resolved roster reports nothing, and the config
looks cleaner than it is. This is exactly why the spine design's amendment carries two columns
(*as written* / *with a table roster*): substituting a table roster is not a free rewrite, it is
what makes the rest of the diagnostics *reachable for the first time*.

The same shape recurs one level up and is worth flagging for whoever schedules H7a:
`validate_config` **returns immediately** after `E-TEMPLATE-UNKNOWN`, because every later check reads
the template's spec. So a config naming a plugin template gets exactly one diagnostic and nothing
else. That is why the executability measurement ran *three passes each* rather than one — its
per-refusal counts (`E-STATS-RESAMPLE-UNSUPPORTED` 8/9, `E-DATA-HOLDOUT-UNSUPPORTED` 6/9) are
unobservable in a pass that stops at `E-TEMPLATE-UNKNOWN`, so a resolvable template had to be
substituted to see them. The accurate statement of what H7a buys is therefore narrower than "new
findings": those diagnostics are already measured, and H7a makes them reachable **without a
substitution** — reproducible by a user with the config as written rather than only by the
measurement harness. Reading the amended order as "H7a changes nothing observable for the nine" is
still wrong; reading it as "H7a reveals unmeasured diagnostics" would be wrong too.

### What must exist for a resolver to run

1. Entry-point metadata scan of `publishable.resolvers` (name only) — invariant (a).
2. `register_resolver`, exported from `publishable`, checked against the key at load.
3. Load-time collision refusal across the group — invariant (b).
4. A read-only `io` exposing `io.read_input` and nothing else, constructible with **no run directory**
   (validate time) and **no step** (run time), per § Where units come from.
5. Resolver dispatch inside `units.py`'s resolution, preserving yield order into `provenance.units`
   and `units_hash`.
6. The four resolver-specific `validate` checks from § Validation: attributes supplied, measurement
   field supplied, condition-independence, and the reserved `Unit` field names — the last already
   built as `E-UNITS-ATTR-RESERVED`.
7. Deletion of both the refusal in `_check_unimplemented` and the skip in `_check_units`, in the same
   change, since the skip's stated justification is the refusal.
8. `provenance.plugin_versions`, and the `input_manifest_policy: hash_index` rule that "the index and
   whatever it names" covers the paths the resolver read plus the paths its units name.

---

## 6. The second output: identifiers the specification does not have

`reference.md` § Validation's checklist carries **eight rows this slice owns with no identifier at
all**, plus the two template rows `spec-defects.md` already routed here — **ten in total**. § Errors
`validate` reports carries exactly **one** code for the family, `E-TEMPLATE-UNKNOWN`. Grep for
`E-SECRET`, `E-ENV`, `E-RESOLVER`, `E-PROBE`, `E-WRITER`, `E-PLUGIN`, `E-APPARATUS` over every
tracked `*.md` returns nothing.

| § Validation row | Code today |
|---|---|
| Template is installed | `E-TEMPLATE-UNKNOWN` (built; the `plugin`-field hint is not — spec-defects, Row 211) |
| Template version moved, first half | none; needs `BaseTemplate.version` (spec-defects, Row 212) |
| Credentials present | **none** |
| Credentials a swept value needs | **none** |
| `requires_env` covers its choices | **none** |
| Probe is installed | **none** |
| Resolver is installed | **none** (only the `-UNSUPPORTED` refusal, which retires) |
| Resolver supplies the attributes | partial — `E-UNITS-ATTR-UNKNOWN` is written against a *table's* columns |
| Resolver supplies the measurement field | **none** |
| Resolver is condition-independent | **none** |

Plus the load-time refusals § Creating a plugin describes in prose with no identifiers at all: a name
collision, a shadow of a core name, a writer claiming a core extension, and a `@register_*` argument
disagreeing with its entry-point key.

**None of these is `-UNSUPPORTED`**, so none is covered by that family's exemption from § Errors
`validate` reports. Per `CLAUDE.md` § Repository status, the document changes first: H7 owes new rows
in that table (and in § Errors core raises for the load-time raises) before the code lands. That is
this analysis's second output, and it is the largest single documentation debt in the slice.

Two further gaps the measurement turned up:

3. **§ Package layout gives the shared machinery no home.** It names `apparatus.py` and `secrets.py`
   as unbuilt, `templates/{base,registry}.py`, and `units.py` as holding the "table/glob/resolver
   registry" — but nothing holds the *entry-point scan and the collision refusal*, which are shared
   across all four groups. A module has to be added to that tree, or the layout has to say which
   existing one owns it.
4. **A plugin writer's reader is unregistered.** § Creating a plugin shows one entry point,
   `".fastq.gz" = "…writers.fastq:write"`, and § Steps and artifacts requires that "what a writer
   takes is what its reader gives back" — core inverts through a separate `READERS` dict. There is no
   `publishable.readers` group and no stated convention for naming the inverse. A plugin can make an
   artifact core can write and cannot read back through `io.read_upstream`.

---

## 7. Traps

**Loading third-party code at `validate` time versus at `run` time.** The sharpest trap in the slice,
and the easiest to get wrong by writing the obvious code. `EntryPoint.load()` at `validate` would
make `validate` — documented as the cheap command you run in a loop while editing YAML — execute
arbitrary plugin top-level code. The split is: metadata `.name` at `validate`, `.load()` at `run` and
`dry-run`. The corollary is uncomfortable and must be stated in the implementation, not discovered:
**a `@register_*` argument that disagrees with its key is invisible to `validate`**, because catching
it requires the import that `validate` promises not to do.

**Core never inspects the body of user Python.** `design-principles.md` § Greenfield only. Every check
in this slice is a check on a *declaration* or on an *effect*: the entry-point key is metadata, the
decorator argument is a value passed at import, `apparatus_facts` is a declared key set checked
against what the probe *returned*, `required_env` is a list, and the resolver's condition-independence
is checked from what it read through `io`/`cfg` — not by reading its source. A check that would need
to parse a plugin's AST is out of scope by construction, however tempting.

**`code_hash` covers `src/**` and `templates/**`; a plugin is pinned by `uv.lock` instead.** A plugin's
resolver, probe, writer and template are *outside* `code_hash` — deliberately, per `CLAUDE.md` §
Invariants and § Creating a plugin's "the plugin becomes a normal `pyproject.toml` line and a pinned
`uv.lock` entry." So a run whose roster came from a resolver has its code identity claimed by a hash
that does not cover the code that produced the roster, and the pin lives in `uv_lock_hash` plus
`provenance.plugin_versions`. Two consequences: nothing in H7 may extend `HASHED_TREES` (`hashes.py`),
and the apparatus is explicitly "not a fourth hash" — it sits beside `uv_lock_hash` as an environment
fingerprint. The seam with H7a is exactly here: a *local* template is inside `code_hash` and outside
`uv.lock`, which is why it needs no entry point and why `run` refuses a dirty `templates/`.

Three further traps, smaller:

- **Probes cost somebody else's quota.** § The apparatus core can only observe draws the line
  explicitly: a resolver's cost is your own disk, a probe's is money and rate limits. `validate` must
  never call one, and the placement "before every execution" means an N-execution run makes N
  authenticated calls — which `dry-run` must be able to state before the run is scheduled.
- **A gate with no policy knob.** A changed fact fails the run, same line as a dirty tree. Any
  configurable override reintroduces the thing the section exists to refuse; there is no `limits` entry
  for it and there must not be.
- **`requires_env` must stay out of the closed constraint vocabulary.** `CLAUDE.md` § Invariants and §
  A credential can belong to a parameter value both make this a rule with a reason: it constrains the
  environment a value may be used in, not the value. It needs `choices` and must be *total* over them,
  and the totality check fires when the template loads — not when the sweep resolves.

---

## 8. Decomposition, with counts

**Verdict: split into three, and one of the three is not gated on the plugin system at all.**

The seam the task suspected — the apparatus — is real, but it is not the only one, and it is not the
most useful one. The secrets sub-slice is the finding: `required_env` is a `BaseTemplate` attribute
that `generic` could declare today, and `Param(requires_env=)` needs only `parameter_spec` and the
sweep's resolved conditions. **Both are built.** Secrets depends on neither entry points nor probes
and can land first, alone, in an afternoon.

Ordering constraint is exactly one: **H7b → H7d**, because the probe registry is one of the four
registries. H7c is free.

### H7b — Registries, entry-point resolution, resolvers · **17 tasks**

1. Entry-point metadata scan for the four groups: name → `EntryPoint`, no `.load()`. Tests against a
   synthetic installed distribution.
2. Load-time collision and shadow refusal computed over metadata only, across all four cases in §
   Creating a plugin. New identifiers; document first.
3. `register_template`'s two meanings reconciled — authoritative for a path-discovered local template
   (H7a), checked against the key for an entry-point one. **The H7a retrofit**, see § 9.
4. `register_resolver` + export from `publishable`.
5. `register_probe` + export — registration and the validate-time "is it registered" answer only,
   no execution.
6. `register_writer` + export; third-party suffixes into `WRITERS`; refusal of a claim on a core
   suffix; `WRITERS`/`READERS` symmetry made an invariant with a test.
7. `get_template` reads the union of builtin, path-discovered and entry-point names; `E-TEMPLATE-UNKNOWN`
   gains the `plugin`-field hint (spec-defects Row 211).
8. `BaseTemplate.version`; `W-TEMPLATE-VERSION` compares against the installed template's own version
   (spec-defects Row 212, first half) — a four-document change.
9. The read-only resolver `io` (`io.read_input` only), constructible with no run directory and no step.
10. Resolver dispatch in `units.py`; yield order preserved into `provenance.units` and `units_hash`.
11. `validate` "resolver is installed"; retire `E-DATA-RESOLVER-UNSUPPORTED` **and** the
    `_check_units` skip in one change.
12. Resolver attribute projection: attributes supplied, `measurements.by` supplied as an attribute;
    `E-UNITS-ATTR-UNKNOWN` generalized off "the source table's columns".
13. Resolver condition-independence check. New identifier.
14. `provenance.plugin_versions`; `input_manifest_policy: hash_index` over resolver-read paths plus
    unit-named paths.
15. Import-failure containment at load: a plugin whose module raises, calls `sys.exit`, or registers
    nothing — the same shape `E-ENTRYPOINT-IMPORT` already handles for the user's own package.
16. The § Errors `validate` reports and § Errors core raises rows for everything above.
17. `publishable plugin new` / `plugin_scaffold.py` — the command that *writes* the entry points and
    the four artifact directories. Unowned in the charter (§ 10); folded in here because H7b needs a
    real installed distribution to test tasks 1–3 against regardless.

### H7c — Secrets and `requires_env` · **7 tasks** · no dependency on H7b

1. `secrets.py`; `python-dotenv` dependency; `.env` loaded before any step runs; never read into
   provenance.
2. `required_env` checked at `validate`. New identifier.
3. `Param(requires_env=...)`: constructor argument, `choices` requirement, totality-over-choices check
   at template load. New identifier.
4. The union-over-resolved-conditions check, per § A credential can belong to a parameter value.
5. `materialize`/`init` renders the requirement into the `choices` comment, against every value.
6. A test that no command's output, and no provenance field, can carry a secret's *value*.
7. `generate experiment` merges new `required_env` into the README's managed credentials region.

### H7d — The apparatus · **14 tasks** · after H7b

1. `Apparatus` construct + export.
2. `apparatus.py`: probe invocation, per-condition facts.
3. A test that no `validate` path calls a probe.
4. Probe at run start.
5. Probe before every execution.
6. `apparatus/probes.jsonl`, append-only, with UTC, phase, condition, and nulls included.
7. `apparatus_facts` projection: every declared key must come back; a missing key is the one error.
8. The credential-leak check on returned values.
9. Null-fact semantics: the three states, and the `null` ↔ value transitions that do **not** fail.
10. `provenance.apparatus` — five sub-keys, replacing `cli.py`'s hardcoded `None`; per-fact
    `unobserved` counts.
11. The change gate: per condition, per fact, against the first *answered* observation; value → value
    fails the run, with no knob.
12. The hook `resume` will call (H9) to refuse a changed apparatus.
13. The hooks `dry-run` (H9) and `freeze`/`diff` (H8) will call, delivered as callables with tests,
    not as commands.
14. A test asserting `batch` and the apparatus stay independent — see § 4.

**Total after H7a: 38 tasks.** Against this repo's own grain — H3a 12, H3b 13, H3c-1 20, H3c-2 14 —
one slice of 38 is the H3 mistake again. Three slices of 17 / 7 / 14 sit inside the band, with H7b
just under H3c-1's 20, which is this repo's own evidence for where a further split becomes necessary.
If H7b's task 17 grows a scaffold's usual tail, splitting the resolver half (tasks 9–14) back out is
the natural second seam.

**Suggested order: H7c → H7b → H7d.** H7c first because it is free, unblocks the credential half of
the feasibility analysis's template, and is the only part of the charter that cannot be made to
depend on anything. **This orders the three within the charter's last slot only** — the global
sequence `H7a → H4 → H3d → H3c-3 → H7 (the rest)` is unchanged by this scoping, with one caveat: H7c
could be pulled forward anywhere, including before H4, since nothing in it depends on any unbuilt
thing.

---

## 9. The H7a carve-out: agree, with one named retrofit

**Agree.** The argument in the spine design's CORRECTION is sound and I verified both halves of it:
`reference.md` § Templates does give a template a third home discovered by path, and the three things
H7a names are genuinely all that is missing for it (`register_template` absent from `__init__.py`,
`get_template` reading `_BUILTIN` only, `generate` accepting `experiment` and `step` only). The
scaffold already creates `templates/` (`scaffold.py`) and `hashes.py` already covers it
(`HASHED_TREES = ("src", "templates")`), so the pinning story needs no work. Nothing in H7a requires
entry points, probes or the gate.

**Where I disagree — two things, neither a reason to reject the split:**

1. **Collision semantics span the seam, and H7a can only implement half of them.** § Creating a
   plugin refuses "a local `templates/*.py` taking the name of an installed one" in the same breath
   as the other three collisions. H7a can refuse a local template shadowing `generic`; it cannot
   refuse one shadowing an installed plugin's template, because it has no way to enumerate installed
   templates. H7b must retrofit that case.
2. **`register_template`'s contract changes meaning across the seam.** In H7a the decorator argument
   *is* the registration — § Creating a plugin's "the one case where the decorator is authoritative
   rather than checked." After H7b it is authoritative for a local template and *checked against the
   key* for an entry-point one. That is one decorator with two semantics selected by provenance, and
   H7a will ship the simpler one.

Both should be written into H7b as **named deliverables**, using the precedent this repo already set
when it moved H3d ahead of H3c-3: *"H3c-3 inherits the retrofit as a named deliverable, not as a
discovery."*

**One consequence for the amended order table.** The feasibility analysis's proposed `llm_screen`
template declares `apparatus_probe = "llm_deployment"` and five `apparatus_facts`. So the table's
"+ H7 (the rest)" row needs **H7b and H7d**, not H7b alone: H7b makes those nine configs *validate*
(the probe resolves as registered) and H7d is what makes a run of them honest, since a template
declaring a probe that never runs records `apparatus: null` for a design that asked to be gated.
H7c is needed too — every credential those configs use is selected by `llm.provider`'s `requires_env`.

---

## 10. What is NOT in H7

| Not H7 | Owner |
|---|---|
| `register_template`, path discovery of `templates/**`, `generate template` | **H7a** |
| `dry-run` itself — and with it the declared-keys check, the credential-value check and the null-fact warning, all of which § The apparatus core can only observe places there. H7 delivers them as callables; H9 delivers the command | H9 |
| `reproduce`, `apparatus.expected.json`, `resume`'s refusal of a changed apparatus, `draft`, `demo`, `docs` | H9 |
| `freeze`'s probe, `diff`'s apparatus row, `study add`'s redaction (which has nothing to redact from `provenance.apparatus`, by design), `report` | H8 |
| `BaseReport` — shares the "unexported importable-surface names" residual with H7, but the class itself is H8's | H8 (spec-defects § routes the export to H7, the behaviour to H8) |
| `statistics.resample` / `null_test`, the weighted contrast family — the 8-of-9 and 3-of-9 blockers | H4 |
| `data.units.holdout` — the 6-of-9 blocker | H3d |
| Cells, and H3d's cell retrofit | H3c-3 |
| `code_hash` awareness of `.gitignore`, `parameters_hash` normalization | H6 |
| `units.parquet` column integrity | H5 |

**One unowned residual, named rather than absorbed.** `publishable plugin new` and
`plugin_scaffold.py` (§ Package layout, "— not yet built") are what *writes* the entry points and the
four artifact directories. The charter's H7 row says "entry-point **resolution**" and names no
scaffold; no other slice claims it either. It is small — a sibling of `scaffold.py` — but it should be
chartered deliberately rather than discovered by whoever implements H7b and finds no way to produce a
plugin to test against. **This scoping charters it into H7b as task 17**, and the 38-task total in
§ 8 includes it; if a later reader would rather it went elsewhere, H7b drops to 16 and the total to
37.
