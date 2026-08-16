# H7b re-scoping — registries, entry points, resolvers

Read-only measurement against `main` at `d86290c`, on 2026-08-16. This **replaces**
`H7-SCOPING.md` § 8's H7b list and `H7a-SCOPING.md`, both pinned to `cb96c7d`; **five
slices have landed since** (H3c-1, H3c-2, H7a, H4a, H3d). Every identifier below was
grepped or probed against that tree, never remembered. Spec claims and build facts are
labelled separately throughout.

**Verdict: 27 tasks**, against the charter's 17 — and **the recommendation is to split
the slice in two**, at the seam § 9 names. The growth is the usual direction: the old
count had no task for the `publishable.readers` gap it itself named, none for
`data.units.from`'s envelope closure, none for the owned prose sweep, and it treated
`register_template`'s two meanings as one retrofit where H7a's shipped predicate makes it
a three-valued question. It also named one code that does not exist.

**Baseline at `d86290c`:** `uv run pytest -q` → **1957 passed, 2 xfailed**, 109 s. Every
probe below ran against that tree with nothing modified, most of them inside a real
scaffolded project (`publishable new my-study`, `generate experiment --template generic`,
an outside `input_dir` holding a four-row `index.csv`) rather than by reading source.

**The charter's 17 is not an independent estimate.** It is `H7-SCOPING.md` § 8's own
enumeration, carried verbatim into the spine design's second amendment. So this document
verifies those seventeen item by item; roughly two thirds re-verify and are marked
**verified** rather than re-argued. What follows concentrates on what moved.

---

## 0. Executive summary — the five things that change how H7b is built

1. **Retiring `E-DATA-RESOLVER-UNSUPPORTED` turns on a roster-check family, but a
   narrower one than the old scoping claims.** `H7-SCOPING` § 5 says "under
   `from: {resolver: ...}` the **entire** unit-checking family is silently inert." Probed:
   the *declaration*-level checks fire today (`E-DATA-CLUSTER-UNKNOWN`,
   `E-DATA-WEIGHT-UNKNOWN`, `E-DATA-HOLDOUT-STRATIFY-UNKNOWN`); what is inert is exactly
   what needs a **resolved roster**. § 4 has the measured list. The correction matters
   because it sizes the test surface the charter does not own.
2. **After H7b, still zero of nine execute — and now for four independent reasons, not
   one.** `Param` has no `requires_env` argument, so the feasibility analysis's own
   `llm_screen` template **cannot be written**, let alone installed; `io.reuse_from` does
   not exist; the probe is H7d's; and executing a resolver at all requires an installed
   distribution, which is `plugin new`. § 8.
3. **`register_template`'s retrofit is a three-valued question, not a two-valued one.**
   H7a shipped `is_local_template`, a **boolean** with two callers. H7b adds a third
   provenance (installed), and both callers are wrong for it: `materialize` writes core's
   `TEMPLATE_VERSION` and `_check_versions` compares against it while its message says
   *"the installed template reports"*. `CLAUDE.md` § Answering a question with a proxy is
   about this exact predicate. § 3.
4. **Three build claims in `src/` about resolvers are already false at `d86290c`, and one
   is falsified by a one-line probe.** `envelope.py`'s *"a misspelled `resolverr` … is
   reported by no check in this build"* — it is, as `E-UNITS-SOURCE-MISSING`. § 7.
5. **A `Status` row overclaims today.** § Creation commands marks `generate` **built** and
   says *"`experiment` accepts `--plugin`"*; § Plugins says `--plugin` runs `uv add`.
   `--plugin` is parsed into `opts` and dropped: exit 0, `plugin: null` written, no
   install. § 6.

---

## 1. Verifying the charter's seventeen, item by item

| # | Charter item | Status at `d86290c` |
|---|---|---|
| 1 | Entry-point metadata scan for four groups, no `.load()` | **Verified absent.** `importlib.metadata` appears at one site in `src/` — `cli.py:2602`, `version("publishable")` — and `entry_points` at none. Probe: `importlib.metadata.entry_points()` filtered to the four documented groups returns `[]`; can-fail control, the same call filtered for `console_scripts`, returns a hit |
| 2 | Load-time collision/shadow over metadata only, all four § Creating a plugin cases | **Half exists, and the half that exists is the merge point.** `registry._merged` refuses a local name core registers (`E-TEMPLATE-COLLISION`); `discovery.discover_local` refuses two local claims of one name. The other three cases are absent. See § 3 — this is a parameter addition, not a rewrite |
| 3 | `register_template`'s two meanings reconciled — the H7a retrofit | **Stale as framed.** It is three meanings now. § 3 |
| 4 | `register_resolver` + export | **Verified absent.** Probe: `hasattr(publishable, "register_resolver")` → `False`; control, `register_template` → `True` |
| 5 | `register_probe` + export, registration only | **Verified absent** — same probe. But shipping it registration-only is a defect shape, not a neutral scoping choice. § 5 |
| 6 | `register_writer` + export; third-party suffixes; core-suffix refusal; `WRITERS`/`READERS` symmetry with a test | **Verified absent**, and the symmetry claim needs its own task. § 5 |
| 7 | `get_template` reads the union of three sources; `E-TEMPLATE-UNKNOWN` gains the `plugin` hint | **Partly done by H7a.** `resolve_template(name, repo_root)` already merges two sources and returns the known-name list from one merge; the hint is still absent (`spec-defects.md` Row 211, open) |
| 8 | `BaseTemplate.version`; `W-TEMPLATE-VERSION` against the installed template | **Verified open.** `spec-defects.md` Row 212, amended 2026-08-15, owner **H7b**. `BaseTemplate` declares nine members and no `version` |
| 9 | A read-only resolver `io`, no run directory, no step | **Verified needed.** `StepIO.__init__` takes `step_dir` and `run_dir` as required keyword `Path`s; `read_input` is one method on it. A resolver `io` is a new object, not a `StepIO` with placeholder paths |
| 10 | Resolver dispatch in `units.py` | **Verified absent.** `resolve_units` branches on `str` → `_from_table`, `{glob:}` → `_from_glob`, `else` → raise `E-UNITS-SOURCE-MISSING`. § Package layout already gives `units.py` the "table/glob/resolver registry", so the home is settled |
| 11 | Retire `E-DATA-RESOLVER-UNSUPPORTED` **and** the `_check_units` skip in one change | **Verified, and it is the right coupling.** `validate.py:943–945`'s skip cites the refusal as its justification, in a docstring at `:897–900`. Both emit/read sites confirmed by grep |
| 12 | Resolver attribute projection; "`E-UNITS-ATTR-UNKNOWN` generalized off the table's columns" | **The code named does not exist.** `grep -rn "E-UNITS-ATTR-UNKNOWN" src/ docs/reference.md` → exit 1; control, `E-UNITS-ATTR-MISSING` → three files. The task is real, the identifier is `E-UNITS-ATTR-MISSING`, and its message interpolates `{source}` (`units.py:216–219`) |
| 13 | Resolver condition-independence check | **Verified absent — and it is wiring, not construction.** § 5 |
| 14 | `provenance.plugin_versions`; `hash_index` over resolver-read paths | **Verified.** `cli.py:2603` writes the literal `"plugin_versions": {}`; `manifest.POLICIES` holds `hash_index` and keys it on `index_names` |
| 15 | Import-failure containment at load | **Verified absent for plugins**, and H7a shipped the pattern to copy: `discover_local`'s `except SystemExit` / `except Exception` pair, each draining the pending buffer |
| 16 | The § Errors rows for everything above | **Verified, and it is the largest single debt.** § 6 |
| 17 | `plugin new` / `plugin_scaffold.py` | **Verified unowned and absent.** `NOT_BUILT_COMMANDS` holds `"plugin new"`; § Package layout carries `plugin_scaffold.py  # 'plugin new' — not yet built`. **No `spec-defects.md` entry exists for it** — `grep -n "plugin new\|plugin_scaffold" docs/superpowers/spec-defects.md` returns nothing, control being the same grep for `register_resolver`, which returns a hit at `:2627` |

---

## 2. `E-DATA-RESOLVER-UNSUPPORTED` — what it actually gates

**Two sites read `data.units.from.resolver`, and only one of them reports.**

| Site | What it does |
|---|---|
| `validate.py:3542–3549`, inside `_check_unimplemented` | The one emit. Message names the **plugin registry** as the reason |
| `validate.py:943–945`, inside `_check_units` | **Returns early, resolving nothing.** Not an emit site, but it is where the refusal's blast radius lives |

`_check_unimplemented` now holds exactly two entries — the resolver source and
`statistics.null_test`. `data.units.holdout` left it with H3d, and the function's own
comment (`validate.py:3597–3600`) says so: *"One `data.units` sub-field remains read by
nothing: a `resolver` source."*

**It is a `-UNSUPPORTED` refusal, so it is the undocumented build family, retired
wholesale** — `CLAUDE.md` § Misreadings. It carries no § Errors row and must not gain one;
`reference.md:193` is where it is named, under *"Two declarations above are not yet
built"*, and that sentence's count drops to one when H7b lands.

**The complete set of things that must exist for it to retire**, read off the emit site
and the skip rather than off the charter:

1. An entry-point name scan of `publishable.resolvers` (metadata only).
2. `register_resolver`, exported, checked against the key at load.
3. A load-time collision refusal across the group.
4. A read-only resolver `io` constructible with no run directory and no step.
5. Dispatch in `resolve_units`, preserving yield order.
6. The four § Validation rows that only exist under a resolver (§ 6), each with a minted
   code.
7. Deletion of the `_check_units` skip **in the same change**, because the skip's stated
   justification is the refusal.
8. `provenance.plugin_versions`, and `hash_index` over resolver-read plus unit-named paths.

Items 1–3 are shared with the other three registries, which is why the slice is
registries-first and resolvers-second rather than the reverse.

---

## 3. The four registries, and what H7a actually left

### Build state, per registry

| Registry | Built | Absent |
|---|---|---|
| `register_template` | The decorator, the pending buffer, eager path discovery, per-call merge, two local collision cases, `E-TEMPLATE-LOAD`, `E-TEMPLATE-COLLISION`, `is_local_template`, `resolve_template`, `unknown_template_message` | Entry-point half: the metadata scan, the decorator-vs-key check, the three plugin collision cases, the `plugin` hint, `BaseTemplate.version` |
| `register_resolver` | — | All of it |
| `register_probe` | — | All of it |
| `register_writer` | The **dispatch** it plugs into: `artifacts._suffix_for`, longest-match over `WRITERS` | The plug. No third-party suffix is reachable |

Probe, with its control:

```
register_template True      Unit True
register_resolver False     Apparatus False
register_probe    False     BaseReport False
register_writer   False
```

### The collision seam is a parameter, not a rewrite — measured

`H7-SCOPING` § 9 called the local-shadows-installed case "the H7a retrofit" without
knowing what shape H7a would leave. It left a good one. `registry._merged(repo_root)`
builds the mapping fresh on every call, from two sources, and its module docstring already
argues the merge point: *"This is the merge, so it is the first place that holds both
sides."* Adding a third source is an addition to that function.

**What is genuinely new work there is the collision *matrix*, not the merge.** Four cases
arrive at once — entry-point × entry-point within a group, entry-point × core's `generic`,
entry-point × local, and a writer claiming a core suffix — and § Creating a plugin requires
all four to fail at load naming both providers, computed **over metadata only, before any
`.load()`**. `discover_local`'s own precedent applies verbatim: collect every claim, then
verdict, in name order rather than in discovery order.

### `is_local_template` is a boolean where H7b needs three values

**This is the trap `CLAUDE.md` § Answering a question with a proxy was written about**, and
H7b supplies its third caller.

```
$ grep -rn "is_local_template" src/
src/publishable/materialize.py:103    local = is_local_template(type(template))
src/publishable/validate.py:756       if is_local_template(type(template)):
```

Today `False` means "core's `generic`". After H7b it means "core's **or** an installed
plugin's", and the two want opposite treatment:

- `materialize.py:103` writes `template_version` for a non-local template from core's own
  module constant `TEMPLATE_VERSION`. For an installed plugin's template that string
  certifies nothing.
- `validate._check_versions` warns `W-TEMPLATE-VERSION` with the message
  `f"is {declared} but the installed template reports {TEMPLATE_VERSION}"` — **a message
  claiming a guarantee the code does not provide** the moment a second installed template
  can exist. § Errors' row currently discloses the gap honestly; the message does not.

`spec-defects.md` Row 212 is exactly this and is **open**, owner H7b. Closing it means
`BaseTemplate.version` — a four-document change, since § Templates' class-attribute example
does not list it.

**The predicate must become a provenance, not a second boolean.** A `local` /
`core` / `installed` answer read at the point of merge, where all three sources are in
hand — the same argument `_merged`'s docstring already makes for the shadow refusal, and
the same argument `LocalTemplate.provider` makes for building the provider string at
discovery time rather than recovering it later. A second boolean (`is_plugin_template`)
would be two predicates that can disagree, which is what `is_local_template`'s own
docstring spent thirty lines avoiding.

### `E-TEMPLATE-UNKNOWN` has two emit sites, and H7a already gave them one wording

`CLAUDE.md` warns that a diagnostic's unit of work is every site that raises *or* reports
it. Measured:

| Site | Surface |
|---|---|
| `validate.py:529` | reports as a finding |
| `generators/experiment.py:58` | raises `ContractError` |

Both build their message from `registry.unknown_template_message(name, known)`, whose
docstring gives the reason. **So H7b changes one wording, not two** — a reduction against
the charter, and the one place where H7a's shipped shape makes this slice smaller. The
message already reads *"which no template — core's, an installed plugin's, or this
project's own `templates/` — registers"*, which becomes true rather than aspirational; the
`known` list is what must grow.

---

## 4. Resolvers — what is closed, what is open, what the retirement turns on

### The schema is open one level too far

`envelope.LEAF_TYPES` types `"data.units.from": (str, dict)` and stops. `_check_unknown_keys`
never descends into a known leaf, so **nothing checks the key inside a `from` mapping**.
The precedent for closing it is already in the file, twice: `measurements` closed at
`{by, collapse}`, `resample` closed at `{method, n, stratify_by}` *before* its wholesale
refusal retired, and `holdout` closed at its five keys the same way with H3d. The module
comment states the rule — **validate the shape before honouring the values** — and names
`from` as the leaf left whole.

So H7b owes `data.units.from.glob` / `.resolver` in `LEAF_TYPES`, and it belongs in the
half that ships *before* the refusal retires, exactly as `holdout`'s did.

### What the refusal actually suppresses — measured, not asserted

`H7-SCOPING` § 5 says the entire unit-checking family goes silent. **That is too broad.**
Probe: one config, mutated one field at a time, run through `validate_config` twice — once
with `from: index.csv` (control) and once with `from: {resolver: patient_trajectory}`.

```
TABLE clean (control)   []
RESOLVER clean          ['E-DATA-RESOLVER-UNSUPPORTED']
  TAB bad key           ['E-UNITS-KEY-MISSING']
  RES bad key           ['E-DATA-RESOLVER-UNSUPPORTED']                              ← lost
  TAB bad attribute     ['E-UNITS-ATTR-MISSING']
  RES bad attribute     ['E-DATA-RESOLVER-UNSUPPORTED']                              ← lost
  TAB reserved attr     ['E-UNITS-ATTR-RESERVED']
  RES reserved attr     ['E-DATA-RESOLVER-UNSUPPORTED']                              ← lost
  TAB fold k=99         ['E-REPL-FOLD-K-TOO-LARGE']
  RES fold k=99         ['E-DATA-RESOLVER-UNSUPPORTED']                              ← lost
  TAB measurements      ['E-DATA-MEASUREMENTS-COLLAPSE-TYPE']
  RES measurements      ['E-DATA-RESOLVER-UNSUPPORTED']                              ← lost
  TAB cluster_by unk    ['E-DATA-CLUSTER-UNKNOWN']
  RES cluster_by unk    ['E-DATA-CLUSTER-UNKNOWN', 'E-DATA-RESOLVER-UNSUPPORTED']    ← kept
  TAB weight_by unk     ['E-DATA-WEIGHT-UNKNOWN']
  RES weight_by unk     ['E-DATA-WEIGHT-UNKNOWN', 'E-DATA-RESOLVER-UNSUPPORTED']     ← kept
  TAB holdout strat     ['E-DATA-HOLDOUT-STRATIFY-UNKNOWN']
  RES holdout strat     ['E-DATA-HOLDOUT-STRATIFY-UNKNOWN', ...UNSUPPORTED]          ← kept
```

**The line is exactly "does this check need the resolved roster".** Declaration-against-
declaration checks (a `cluster_by` / `weight_by` / `holdout.stratify_by` naming something
outside `data.units.attributes`) survive; everything reading the table does not. That is
a smaller inert family than the old scoping claims and a sharper one to test.

**The consequence the charter does not own:** every one of the lost checks becomes
reachable for the first time against a *resolver-produced* roster, whose columns are
whatever the plugin yielded rather than whatever a CSV header holds. `_from_table`'s
messages interpolate `{source}` — *"which index.csv does not have"* — and there is no
source file to name. Generalizing that wording is charter task 12 and it is one task; the
**test** pass over the newly-live family is not in the charter at all.

One more, from the same probe: a misspelled `{resolverr: x}` reports
`E-UNITS-SOURCE-MISSING` today. That falsifies `envelope.py:51` (§ 7).

---

## 5. Four things the charter treats as one line each and are not

### (a) `WRITERS`/`READERS` symmetry is load-bearing today and unenforced

`H7-SCOPING` § 3(c) says the constraint is "already satisfied implicitly". Measured, it is
worse than that:

```python
def _suffix_for(name: str) -> str | None:      # iterates WRITERS
    ...
@staticmethod
def _read(path: Path) -> Any:
    suffix = _suffix_for(path.name)             # WRITERS
    if suffix is not None:
        return READERS[suffix](path.read_bytes())   # indexed on READERS
```

`_read`'s docstring says *"Inverts the same table `write` dispatches through"*. It does
not — it dispatches on one dict and indexes another. Both hold the same five keys today,
so nothing can fail. **A third-party writer key with no reader makes `io.read_upstream`
raise a bare `KeyError`, not a coded `ArtifactError`** — and § Steps and artifacts's "what
a writer takes is what its reader gives back" is the promise that breaks. This is its own
task, and its can-fail control is trivial: add a key to `WRITERS` only, and read the
artifact back.

### (b) `publishable.readers` — a **spec** gap, still unfiled

§ Creating a plugin declares four entry-point groups and no fifth:

```
$ grep -n "entry-points" docs/reference.md
1214, 2679, 3391, 3394, 3397, 3400     # templates, resolvers, probes, writers — four names
$ grep -rn "publishable.readers" docs/ src/ README.md
(no output)
```

So a plugin can register a writer for `.fastq.gz` and core has no way to read that
artifact back. The spine design's second amendment says this was *"chartered into H7b"* —
but `CLAUDE.md` § Habits: **a ledger line saying "filed" is not a filing**, and
`spec-defects.md` carries no entry. H7b owes the filing and the spec decision (a fifth
group, or a stated convention that a writer's entry point resolves its inverse), before it
owes any code. `H7-SCOPING` § 6 named the gap and gave it **no task**.

### (c) `register_probe` without `Apparatus` is the `required_env` shape

`CLAUDE.md` § Reading the documents: *"An unbuilt reader of a **shipped** surface is a
defect: `BaseTemplate.required_env` is declarable today on a class that ships, and nothing
reads it."*

Re-measured, that defect is still live and has three siblings:

```
$ grep -rn "field_convention\|required_env\|apparatus_probe\|apparatus_facts" src/
templates/base.py:13,15,16,17           declarations
templates/builtin/generic.py:7,9,10,11  re-declarations
generators/template.py:9,10             a comment saying the stub omits them
```

**Four declarable, shipped, unread attributes** — and re-measured here rather than carried
from `H7a-SCOPING` § 1, which is where the list was first written. H7a's `generate template` stub
deliberately omits them, which is the honest containment — but the class still ships them.
Exporting `register_probe` with no `Apparatus`, no probe call and no gate adds a **fifth**
member of the same family, and this time an exported one. The charter's "registration and
the is-it-registered answer only" is defensible *if* the § Validation *Probe is installed*
row is what consumes it — a config naming an unregistered probe is refused, which is a real
effect. It is **not** defensible as a bare export. H7b must state which, and the § The
importable surface row split is where the answer is written down.

### (d) Condition-independence is wiring, not construction

§ Where units come from: *"a resolver that reads a parameter the sweep varies is rejected
by `validate`."* The mechanism already exists — `config.SweptAway`, a sentinel substituted
for a swept path whose `Node.__getattr__` raises on the **read** rather than returning a
marker, precisely so the refusal lands under the right identifier
(`E-STEP-SWEPT-PARAM`). A resolver runs at validate time and receives a `cfg`; handing it
a `SweptAway`-substituted config is the whole check.

Two consequences the charter does not carry: the identifier is a **step** code being raised
for a resolver, so H7b either mints a resolver code or documents the reuse; and this is
the same *"wiring, not construction"* shape H4a found for `statistics.resample`, which is
worth stating so nobody rebuilds it.

---

## 6. The documentation debt, and one row that overclaims

### § Validation rows H7b owns, each checked for an emit site

| Row | Code today | H7b owes |
|---|---|---|
| *Template resolves* | `E-TEMPLATE-UNKNOWN`, built | The `plugin` field hint (`spec-defects.md` Row 211, open) |
| *Template name is claimed once* | `E-TEMPLATE-COLLISION`, built for the two local cases | The three plugin cases; the row's own closing clause says they are "not yet checked" |
| *Template version moved*, first half | none | `BaseTemplate.version` (Row 212, open) |
| *Probe is installed* | **none** | The check and its code |
| *Resolver is installed* | **none** — only the `-UNSUPPORTED` refusal, which retires | The check and its code |
| *Resolver supplies the attributes* | partial — `E-UNITS-ATTR-MISSING`, worded against a table | Generalization |
| *Resolver supplies the measurement field* | **none** | The check and its code |
| *Resolver is condition-independent* | **none** | The check; reuse-or-mint decision (§ 5d) |

**No `E-RESOLVER-*`, `E-PROBE-*`, `E-PLUGIN-*`, `E-WRITER-*`, `E-READER-*` or
`E-APPARATUS-*` identifier exists anywhere.** Sweep over `docs/reference.md`,
`docs/design-principles.md`, `docs/experimental-designs.md`, `README.md` and `src/` — exit
1; can-fail control, the same regex for `E-TEMPLATE[A-Z-]*` over `reference.md`, returns
five distinct codes. Plus the load-time refusals § Creating a plugin describes in prose
with no identifier at all: a cross-group name collision, a shadow of a core name, a writer
claiming a core suffix, and a `@register_*` argument disagreeing with its key.

**None of these is `-UNSUPPORTED`**, so none is covered by that family's exemption from
§ Errors `validate` reports. The document changes first.

### The disclosures H7a wrote, which H7b retires

H7a was scrupulous about this and left a findable set. Sweeping the four documents by
**file list**, not by filtering output:

| Site | The claim |
|---|---|
| `reference.md:79` | `{resolver: <name>} (NOT BUILT)` in the schema's `from` comment |
| `reference.md:193` | "**Two** declarations above are not yet built" → one |
| `reference.md:195` | "the plugin case is not yet checked, since no entry point is resolved in this build" |
| `reference.md:423` | the currently-refused-block cross-reference |
| `reference.md:567` | `E-TEMPLATE-COLLISION`: "A local name an **installed plugin** registers … is not yet checked" |
| `reference.md:570` | `E-TEMPLATE-UNKNOWN`: "An installed plugin's is not yet checked either" |
| `reference.md:1175` | the second `from` enum comment |
| `reference.md:3412` | "The two local cases are the ones this build checks … the plugin cases arrive with entry-point resolution" |
| `reference.md:930` | § The importable surface's three-name `not yet built` row |
| `reference.md:3097` · `:3119` | `plugin new` and `list-templates`, `NOT BUILT` |
| § Package layout | `plugin_scaffold.py — not yet built`; no home named for the shared entry-point scan |

### One enum comment already out of sync, and one Status row already overclaiming

**Enum comment.** `CLAUDE.md`'s cross-document rule: *an inline `# a | b | c` comment must
list every value its corresponding table or section defines.* `reference.md:79` and `:1175`
both write `# index.csv | {glob: "*.dcm"} | {resolver: <name>}`. `materialize.py:128` writes
`# index.csv | {glob: "*.dcm"}` — probed by generating a real config, whose `from` line
carries two values, not three. Live today, small, and H7b touches that line anyway.

**Status row.** § Creation commands marks `publishable generate` **built** and its *Does*
cell says *"`experiment` accepts `--plugin`"*; § Plugins opens by saying `--plugin
<user>/<repo>` *"runs `uv add git+https://github.com/<user>/<repo>` and nothing more."*

```
$ grep -rn "uv add" src/            → no output   (control: "uv_lock" → hits in uv_support.py, cli.py)
$ publishable generate experiment p2 --template generic --plugin someuser/publishable-llm ...
exit=0
$ grep -n "^plugin" configs/p2/config.yaml
8:plugin: null
```

`_dispatch_generate` collects every `--x y` pair into `opts` and reads only `template`,
`input-dir`, `output-dir`, `name`. **`--plugin` is accepted and silently dropped** — as is
any unknown flag (`--nosuchflag x` also exits 0). The CLI-table tests bind command *names*
and Status markers, not the arguments column, which is why this survived. It is H7b's
because a plugin nobody can install is a registry nobody can test, and because the
`plugin` config field § The one config file documents has no writer.

---

## 7. Comments in `src/` claiming guarantees the code does not provide

Swept by claim across `src/`, filtered by file list.

| Site | Claim | Status |
|---|---|---|
| `envelope.py:51` | "a misspelled `resolverr` in a `data.units.from` mapping is **reported by no check** in this build" | **False, probed.** `{resolverr: x}` reports `E-UNITS-SOURCE-MISSING`, from `resolve_units`'s `else` branch. The claim is true only of *key-name* checking, which the sentence does not say |
| `envelope.py:208` | "a `from` dict's `resolver` is **reached by no check** in this build: not here, and not by `_check_shape`" | **False as written.** `_check_unimplemented` reads `source["resolver"]` and interpolates it into its message; `_check_units` branches on it |
| `artifacts.py:855` | `_read`'s "Inverts the same table `write` dispatches through" | **True by coincidence.** Dispatches on `WRITERS`, indexes `READERS`. § 5a |
| `validate.py:774` | `W-TEMPLATE-VERSION`'s "the installed template reports {TEMPLATE_VERSION}" | **True only while core is the only installer.** § 3 |
| `validate.py:519–531` | "The load-time refusals resolving a template can make — **two today**, `E-TEMPLATE-LOAD` and `E-TEMPLATE-COLLISION`" | True today, **false the moment task 8 lands**. A count phrase beside an insertion point — `CLAUDE.md`'s "check every count phrase near it" |
| `validate.py:3597–3600` | "One `data.units` sub-field remains read by nothing" | True today; H7b's to retire |
| `registry.py:86` | "no template — core's, an installed plugin's, or this project's own `templates/` — registers" | Aspirational today; becomes true with H7b, so it is **not** a defect — recorded so it is not "fixed" |

Six sites, four of them owned. `CLAUDE.md`: *if a comment says this cannot happen, make it
happen* — the first two were found exactly that way.

---

## 8. The payoff, stated honestly

**The spine design's table says "+ H7 (the rest) → 9 of 9 as written."** That row is a
drift of the same kind H3d's "unblocks 6 of 9" was, and it fails for **four independent
reasons**, three of which are outside H7b.

Measured on 2026-08-16 against `d86290c`:

> H7b retires **one refusal that 9 of 9 configs hit** (`E-DATA-RESOLVER-UNSUPPORTED`), and
> **zero experiments newly execute.**
>
> 1. **The analysis's own plugin cannot be written.** `llm_screen`'s `parameter_spec`
>    declares `Param(..., requires_env=...)` on `llm.provider`
>    (`feasibility-llm-growth-studies.md:490`, `:834`, `:941`). `param.Param.__init__`
>    takes `type_` plus twelve keyword-only arguments and `requires_env` is not among
>    them, so that module raises `TypeError` at import — an entry point that cannot load.
>    Probed: `Param(str, default="a", choices=["a"], requires_env={"a": []})` →
>    `TypeError: Param.__init__() got an unexpected keyword argument 'requires_env'`;
>    control, the same call without it, constructs. **H7c is a hard
>    prerequisite for the nine, not an independent slice**, and `H7-SCOPING` § 9 already
>    said H7c "is needed too" without drawing the conclusion that it blocks.
> 2. **`io.reuse_from` does not exist.** `grep -rn "reuse_from" src/` → no output; control,
>    `read_upstream` → `artifacts.py`. E3, E4 and E6 read their frozen compiled program
>    through it, and the analysis records C1–C3's dependence as unsettled.
> 3. **The probe is H7d's.** `llm_screen` declares `apparatus_probe = "llm_deployment"` and
>    five `apparatus_facts`; nothing in `src/` reads either.
> 4. **There is no way to produce an installed plugin.** `plugin new` is `NOT BUILT` and
>    `--plugin` is dropped (§ 6). Executing a resolver requires an installed distribution;
>    testing entry-point resolution requires one too, which is why the charter folded
>    `plugin new` in.

**Per config, against those four:**

| Configs | Needs from H7b | Still blocked by |
|---|---|---|
| E1, E2, E5 | The resolver half in full: name resolution, dispatch, the attribute projection their `data.units.attributes` declares | H7c (1), H7d (3), `plugin new` (4). Nothing else — these are the three H3d-SCOPING § 7 found clean under a table-roster substitution |
| E3, E4, E6 | The same | The same three, **plus `io.reuse_from`** (2), which no H7 sub-slice owns |
| C1, C2, C3 | The same | The same three, plus H4b's `E-DATA-WEIGHT-CONTRAST`, and `io.reuse_from` **unsettled** — the analysis says so in its own words rather than claiming absence |

So H7b moves every one of the nine from "one refusal before any resolver question is
asked" to "blocked on three slices and one unowned method". No row of that table reaches
`run`.

**The honest form: H7b makes the nine configs *validate* against a plugin that H7c must be
able to express and `plugin new` must be able to produce.** That is worth having — it is
the first time `validate` answers a resolver name at all — but it is not an executable
count, and writing it as one would repeat the mistake this repo has now made twice.

**Recommended order change.** `H7-SCOPING` § 8 suggested `H7c → H7b → H7d` and called H7c
"free". Finding 1 upgrades that from preference to dependency: **H7c must precede H7b** if
the deliverable is measured against the feasibility analysis at all, because without
`Param(requires_env=)` there is no plugin to point H7b's registry at.

---

## 9. Decomposition — 27 tasks, and the seam to split them at

Grain matches `H3d-SCOPING-2.md`: each doc-table edit and each new code its own task.

### Part A — declare and register. `E-DATA-RESOLVER-UNSUPPORTED` stays alive throughout · 19

| # | Task | Why separate |
|---|---|---|
| 1 | **§ Validation + § Errors `validate` reports**: mint the codes for *Resolver is installed*, *Resolver supplies the measurement field*, *Resolver is condition-independent*, *Probe is installed*; settle reuse-vs-mint for `E-STEP-SWEPT-PARAM` (§ 5d) | Four rows with no identifier; `CLAUDE.md` requires the document first |
| 2 | **§ Errors core raises + § Creating a plugin**: the four load-time refusals described in prose with no identifiers — cross-group collision, core-name shadow, core-suffix claim, decorator-vs-key disagreement. Extend `E-TEMPLATE-COLLISION`'s row to the three plugin cases, **and place every new load fault in § Errors' documented early-return ordering** (parse → shape → `E-TEMPLATE-LOAD` → `E-TEMPLATE-COLLISION` → `E-TEMPLATE-UNKNOWN`, each "exactly once"); fix `validate.py:519`'s "**two today**" count | Load-time raises, a different table from task 1's — and the ordering prose is normative, so a new refusal on that surface either widens a condition or earns a row |
| 3 | **Settle and file the `publishable.readers` gap** — a fifth group or a stated convention — plus a `spec-defects.md` entry, since none exists | § 5b. **Absent from the charter's seventeen entirely** |
| 4 | **§ Package layout + § The importable surface**: a home for the shared entry-point scan and the collision refusal; split the three-name `register_*` row as each lands | Two normative trees; the second decides whether `register_probe` ships as an export or as a checked declaration (§ 5c) |
| 5 | **The `NOT BUILT` markers and the enum comments**: `reference.md:79`, `:193`'s count, `:1175`, and `materialize.py:128`'s third spelling — already out of sync today | The mechanical enum-comment rule; one line of code inside a documentation task |
| 6 | **§ Creation commands / § Plugins: `--plugin`** — mark it honestly now, whichever way task 18 goes | § 6. A `Status` row that overclaims is the defect the column exists to prevent |
| 7 | **Entry-point metadata scan**, four groups, name → `EntryPoint`, no `.load()`. Test fixture: a real installed distribution | The no-import invariant lives or dies here |
| 8 | **The collision matrix over metadata only**: entry-point × entry-point, × core, × local; providers named, name order not discovery order | `discover_local`'s own precedent; four cases, one verdict site |
| 9 | **Template provenance becomes three-valued**: `is_local_template` → `local`/`core`/`installed`, read at the merge; `_merged` takes a third source | § 3. **This is H7a's inherited retrofit, and it is bigger than the charter's "two meanings reconciled"** |
| 10 | **`BaseTemplate.version`; `W-TEMPLATE-VERSION` against it** — `spec-defects.md` Row 212; a four-document change | Version semantics, not registry semantics; the message at `validate.py:774` is false without it |
| 11 | **`E-TEMPLATE-UNKNOWN`'s `plugin` hint** (Row 211), through the one shared `unknown_template_message` | Both emit sites share one wording — smaller than the charter assumed |
| 12 | **`register_resolver`** + export | |
| 13 | **`register_probe`** + export, and the *Probe is installed* check that consumes it — **which means `validate` reading `BaseTemplate.apparatus_probe` for the first time**, one of § 5c's four dead attributes | § 5c. Ships only with a consumer, or it is a fifth unread surface. The declaration side is not free: nothing reads that attribute today |
| 14 | **`register_writer`** + export; third-party suffixes into `WRITERS`; refusal of a core-suffix claim | |
| 15 | **`WRITERS`/`READERS` symmetry made an enforced invariant**, and `_read`'s docstring corrected | § 5a. Would be missed by any task scoped to "add a writer" |
| 16 | **The decorator-vs-key check at load**, `run`/`dry-run` only — plus the stated consequence that `validate` cannot see a disagreement | The two halves of one sentence execute on two commands; a slice that puts both at `validate` breaks the no-import promise |
| 17 | **Import-failure containment for a plugin module**, `SystemExit` included, on `discover_local`'s pattern | H7a shipped the shape; the fault surface is different |
| 18 | **`--plugin` on `generate experiment` / `init`**: `uv add`, and the `plugin` config field written | § 6. Absent from the charter |
| 19 | **Envelope closure of `data.units.from`** one level in (`glob`, `resolver`); retire `envelope.py`'s two false comments | § 4. The `holdout`/`resample` precedent: shape before values, ahead of the refusal |

### Part B — resolve, and retire the refusal · 8

| # | Task | Why separate |
|---|---|---|
| 20 | **`plugin new` / `plugin_scaffold.py`** — writes the entry points and the four artifact directories; **atomically with** § Creation commands' `NOT BUILT` marker and the `"plugin new"` key in `cli.NOT_BUILT_COMMANDS` | Charter task 17. Placed here because Part A's tests need only a synthetic distribution, while Part B needs a real resolver a user could have written. `tests/test_cli.py:6666` asserts **set equality** between the document's `NOT BUILT` rows and that dict, so a partial change fails collection rather than misleading a reader — H7a task 11's experience |
| 21 | **The read-only resolver `io`** — `read_input` and nothing else, constructible with no run directory and no step | `StepIO` requires both; a placeholder path is a proxy answer |
| 22 | **Resolver dispatch in `resolve_units`**, yield order preserved into `provenance.units` / `units_hash` | The one seam in `units.py` |
| 23 | **Retire `E-DATA-RESOLVER-UNSUPPORTED` and the `_check_units` skip in one change**; add *Resolver is installed* | The skip's justification is the refusal; separating them is how a config silently resolves nothing |
| 24 | **Attribute projection**: attributes supplied, `measurements.by` supplied as an attribute; `E-UNITS-ATTR-MISSING`'s `{source}`-worded message generalized | Charter task 12, with the identifier corrected |
| 25 | **Condition-independence through `SweptAway`** | § 5d. Wiring; the risk is rebuilding it |
| 26 | **`provenance.plugin_versions` populated; `hash_index` over resolver-read plus unit-named paths** | `cli.py:2603` writes `{}` today |
| 27 | **The owned prose sweep and the reader-facing half**: the eleven document sites of § 6, the four `src/` claims of § 7, the newly-live roster-check family (§ 4) tested against a resolver-produced roster, and the honest count of § 8 written into the dated executability section | `CLAUDE.md`: three sweeps in one slice stopped one file short. The count needs re-measuring, not restating |

### The seam, at 19/20

**Recommend shipping Part A (1–19) and Part B (20–27) as two slices**, and this is the seam
`H7-SCOPING` § 8 itself named ("splitting the resolver half back out is the natural second
seam") — adopted rather than invented, with its boundary moved by one: `plugin new` goes
with Part B, not Part A, because Part A's entry-point tests need only a synthetic
distribution while Part B needs a resolver a user could have written.

- **It keeps the wholesale refusal alive across the seam**, which is what H3d's own seam
  bought and what `envelope.py`'s comment argues for: shape checked before values honoured.
- **Part A delivers three registries, the collision matrix and the whole documentation
  debt with no change to `units.py` and no roster.** Part B touches `units.py`,
  `artifacts.py`, `cli.py` and `validate.py`'s skip.
- **Neither half is past twenty**, which is this repo's own band (H3c-1 20, H3d 19).

**The price, named rather than discovered — it is H3d's price verbatim.** `validate`
collects, so every Part A test on a resolver-adjacent config pins a finding list containing
`E-DATA-RESOLVER-UNSUPPORTED`, and **task 23 retires it**, so every one of those tests
changes when Part B lands. Mitigate the same way: require each Part A test to assert
positively that its new finding appears **alongside** the wholesale refusal, so the
retirement is a one-line deletion rather than a rewrite.

If the slice ships whole, task 23 is the ordering constraint: nothing may retire the
refusal before 21, 22, 24, 25 land.

---

## 10. Traps specific to this slice

**A proxy for "where did this template come from".** § 3. H7a closed two fail-opens in
`is_local_template` — a module-name prefix, then a marker on a shared class — and a third
from reading `sys.modules` after the restore. H7b adds the third provenance to the same
predicate. **The direct question is asked at the merge**, where all three sources are in
hand; anything asked later is asking a proxy again.

**`.load()` at `validate` time.** `EntryPoint.name` is metadata; `.load()` is an import.
`validate` is documented as creating nothing and reaching nothing, and § Creating a plugin
justifies the whole entry-point mechanism by that promise. The uncomfortable corollary must
be *written*, not discovered: **a `@register_*` argument that disagrees with its key is
invisible to `validate`.**

**H7a's discovery already inverted that argument, and the inversion is still live.** It is
also *already documented* — § Creating a plugin's paragraph beginning *"That authority
costs the guarantee two paragraphs up"* states it in full, and § Templates carries the
`__pycache__` consequence. So the tension `H7a-SCOPING` § 5(a) flagged is **resolved in the
documents and unresolved in the mechanism**: after H7b one command resolves names by two
methods with opposite import costs. The thing to avoid is "simplifying" them into one.

**A check written where the roster is not.** § 4: the surviving checks under a resolver are
the declaration-against-declaration ones. A test that mutates `cluster_by` to prove the
resolver path works proves nothing — that check fires today, with the refusal in place.
`CLAUDE.md`'s *fixture whose numbers agree with the bug*, one level up.

**A mutation aimed at the dict rather than at the dispatch.** § 5a: `WRITERS` and `READERS`
hold the same five keys, so a mutation that swaps a *value* between them cannot fail. The
mutation that can is adding a key to one dict only.

**Two elements cannot distinguish four orderings.** The collision matrix has four cases and
three sources. A fixture with one local and one installed template rules out one pairing;
the entry-point × entry-point case needs two installed distributions, and the
name-order-not-discovery-order property needs names whose sorted order differs from their
install order. Count the orderings, then size the fixture.

**A `-UNSUPPORTED` retirement is not a § Errors row.** `E-DATA-RESOLVER-UNSUPPORTED` has no
row and must not gain one on its way out; `reference.md:193` is where it is named and where
the count drops from two to one.

---

## 11. What is NOT in H7b

| Out | Owner |
|---|---|
| `secrets.py`, `.env`, `required_env`, `Param(requires_env=)` | **H7c** — and § 8 finding 1 makes it a **prerequisite**, not a sibling |
| `Apparatus`, probe execution, the ledger, per-condition facts, the change gate | **H7d.** H7b ships `register_probe` and the *Probe is installed* answer only, and only because that row consumes it (§ 5c) |
| `io.reuse_from` and `lineage.py` | Unowned by any H7 sub-slice; blocks E3/E4/E6 independently (§ 8) |
| `publishable list-templates` | Its Status row stays `NOT BUILT`. Its job is enumerating the merged set, so it is *reachable* after task 9 — recorded so nobody folds it in unbriefed |
| `BaseReport` / `generate report` | H8 for behaviour; the export is the § The importable surface residual `spec-defects.md` routes to H7 |
| The README managed regions — `credentials`, a parameter-table region, `generate experiment`'s merge | `docs`. `reference.md:3271` and `:3283` already mark both halves `NOT BUILT`, and `required_env` compounds it |
| The unknown-flag silent acceptance in `_dispatch_generate` (`--nosuchflag x` → exit 0) | Not H7b's; found while probing `--plugin` (§ 6) and worth a `spec-defects.md` entry from whoever files task 3's |
| Anything extending `HASHED_TREES` | Never. A plugin is pinned by `uv.lock`, not by `code_hash` — `CLAUDE.md` § Invariants |
| `statistics.null_test` | H4d. It is the **other** remaining `_check_unimplemented` entry, and retiring one must not retire the loop |
