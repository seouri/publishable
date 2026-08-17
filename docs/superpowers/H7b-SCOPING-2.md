# H7b re-scoping (2) — registries, entry points, resolvers

Read-only measurement against `main` at `ff51864`, on 2026-08-16. This **replaces**
`H7b-SCOPING.md`, taken the same day against `d86290c`; **H7c has merged since**, and it
touched eight files under `src/` including four this slice acts on. Every identifier below
was grepped or probed against `ff51864`, never carried. Where this document contradicts
`H7b-SCOPING.md` it says so and shows the command; where it confirms it, it says that too.

**Verdict: 29 tasks**, against the charter's 17 and the prior scoping's 27. The seam moves
by one, to **20/21**. Net +2, but that understates the churn: one task shrank to a residual,
two gained requirements no earlier probe had found, and two are new surfaces H7c created
that neither the charter nor the prior scoping could have had.

**Baseline at `ff51864`:** `uv run pytest -q` → **1999 passed, 2 xfailed**, 107 s. (Prior
scoping recorded 1957/2 at `d86290c`; H7c added 42 tests.) Probes below ran against that
tree with nothing modified, most inside a real scaffolded project (`publishable new proj`,
`generate experiment --template generic pilot`, an outside `input_dir` holding a four-row
`index.csv`) rather than by reading source.

**Why a carried line number is worse than an omitted one — demonstrated, not asserted.**
`H7b-SCOPING.md` cites the resolver emit at `validate.py:3542–3549`, the `_check_units` skip
at `:943–945`, and the skip's docstring at `:897–900`. At `ff51864` they are at `:3785`,
`:1185` and `:1139` — every one displaced by ≈ +242, because H7c's insertions sit *above*
line 897, in the template-load path. Nothing about those three sites changed; only their
addresses did. This document locates code by name.

---

## 0. Executive summary — the five things that change how H7b is built

1. **`H7b-SCOPING.md` § 8 finding 1 is dead, and with it the recommended order change.**
   Its claim was that the feasibility analysis's own `llm_screen` template *cannot be
   written*, because `Param.__init__` rejects `requires_env`. Probed at `ff51864` with the
   analysis's actual three-provider declaration: it constructs, and renders the exact
   comment `reference.md` § A credential can belong to a parameter value shows. **"H7c must
   precede H7b" is satisfied history, not a live constraint.** The other three blockers it
   named — `io.reuse_from`, the probe, `plugin new` — are each re-verified **unchanged**,
   so the payoff is still *zero of nine execute*, now for three reasons rather than four.
   § 8.
2. **H7b now creates a credential-leak surface that did not exist when H7b-SCOPING was
   written.** `cli.py`'s `resolve_units` call sits **182 lines above** the line that
   computes the run's credential set, and its raise is caught by nothing before `main`'s
   bare `except PublishableError`, which prints un-redacted **by construction** (filed
   OPEN by H7c). Today that is harmless — `resolve_units` reads a CSV. **After task 23 it
   executes a plugin resolver**, whose exception text is exactly the "client library
   interpolates the key into a URL" case H7c built redaction for. Probed end to end: the
   same exception is **redacted** at `validate` and **printed whole** at `run`, and a
   *non*-`ContractError` from that call **escapes `validate_config` entirely**, breaking
   the "`validate` never raises" contract as well. This is a whole new task and it is the
   finding most likely to be missed. § 5(e).
3. **Every load-time refusal H7b mints must decide what it carries in `partial_templates`,
   and the entry-point half structurally cannot carry anything.** H7c gave
   `discovery`/`registry` a `PartialLoadError(ContractError)` whose payload is the classes
   a discovery pass constructed, so a credential a refused file declared can still be
   redacted out of the refusal's own message. `_merged` builds that payload from
   `local.values()` — the very function H7b adds a third source to. But the entry-point
   scan is **metadata only, no `.load()`**, so a plugin-side collision has no class to ask.
   That is a documented residual H7b owes, not a bug to fix. § 3.
4. **One charter task shrank, and it shrank because H7c did the edit.** § Errors'
   early-return prose and `validate.py`'s *"two today"* comment — flagged by the prior
   scoping as H7b's to fix — were both rewritten by H7c to distinguish **codes** from
   **shapes**. The residual is real but narrow: H7b must decide whether a plugin-side load
   fault is a new *code*, and only a new code moves that count. § 6.
5. **Everything the prior scoping measured about resolvers themselves re-confirms.** The
   kept/lost matrix, `envelope.py`'s two false comments, `E-UNITS-ATTR-UNKNOWN`'s
   non-existence, `--plugin`'s silent drop, `WRITERS`/`READERS`'s bare `KeyError`, the
   `publishable.readers` gap still unfiled, Rows 211 and 212 still open — all re-run, all
   confirmed. § 1 marks each. One genuinely new fault was found in the same area: a `from`
   mapping declaring **both** `glob` and `resolver` validates as a resolver and would
   resolve as a glob. § 4.

---

## 1. What H7c changed, and what it therefore could have invalidated

`git diff --numstat d86290c..ff51864 -- src` names the complete set of files that can have
moved an H7b claim (added / removed):

```
 80    0   src/publishable/cli.py
 26    1   src/publishable/diagnostics.py
 10    8   src/publishable/generators/template.py
 46    2   src/publishable/param.py
 23    1   src/publishable/runner.py
131    0   src/publishable/secrets.py          (new)
 37    4   src/publishable/templates/discovery.py
  3    3   src/publishable/templates/registry.py
249    8   src/publishable/validate.py
```

Everything else H7b touches — `envelope.py`, `units.py`, `artifacts.py`, `materialize.py`,
`templates/base.py`, `manifest.py`, `hashes.py` — is byte-identical. Control:
`git log --oneline d86290c..ff51864 --` over all seven of those paths returns nothing, while
the same command for `src/publishable/validate.py` returns commits.

**So claims about those seven files are re-run rather than re-derived, and every one below is
labelled with which it was.**

### The prior scoping's seventeen-item verification, re-checked

| # | Charter item | At `d86290c` | At `ff51864` |
|---|---|---|---|
| 1 | Entry-point metadata scan, four groups, no `.load()` | absent | **CONFIRMED absent.** `grep -rn "entry_points" src/` → exit 1; control, `grep -rn "importlib" src/` → five hits. Probe: `entry_points().select(group=g)` for all four documented groups plus `publishable.readers` → `[]` each; control, `console_scripts` → non-empty |
| 2 | Load-time collision/shadow over metadata, four cases | half exists | **CONFIRMED, and the half that exists gained a payload.** `_merged` still refuses a local name core registers and `discover_local` still refuses two local claims — but both now raise `PartialLoadError` carrying `partial_templates`. § 3 |
| 3 | `register_template`'s meanings reconciled | three meanings | **CONFIRMED unchanged.** `grep -rn "is_local_template" src/` → the same two callers, `validate.py:997` and `materialize.py:103` (both moved; neither changed) |
| 4 | `register_resolver` + export | absent | **CONFIRMED absent.** `hasattr(publishable, "register_resolver")` → `False`; control, `register_template` → `True` |
| 5 | `register_probe` + export | absent | **CONFIRMED absent**, same probe. And its sibling-defect framing narrowed — see below |
| 6 | `register_writer` + export; symmetry | absent | **CONFIRMED absent**, same probe. `artifacts.py` untouched, and the symmetry fault re-probed live (§ 5a) |
| 7 | `get_template` union of three; `plugin` hint | partly done | **CONFIRMED.** `spec-defects.md` Row 211 read at `ff51864`: still OPEN, owner *"H7 — specifically H7b"*, amended 2026-08-15 and **not** re-amended by H7c |
| 8 | `BaseTemplate.version`; `W-TEMPLATE-VERSION` | open | **CONFIRMED.** `grep -rn "version" src/publishable/templates/base.py` → exit 1. Row 212 still OPEN, owner H7b. `_check_versions`'s message still reads `f"is {declared} but the installed template reports {TEMPLATE_VERSION}"` |
| 9 | A read-only resolver `io` | needed | **CONFIRMED.** `StepIO.__init__` still takes `step_dir`, `input_dir` and `run_dir` as required keyword `Path`s |
| 10 | Resolver dispatch in `units.py` | absent | **CONFIRMED.** `resolve_units` still branches `str` → `_from_table`, `{glob:}` → `_from_glob`, `else` → raise `E-UNITS-SOURCE-MISSING` |
| 11 | Retire the refusal **and** the `_check_units` skip together | verified | **CONFIRMED, and still the right coupling.** The skip and its justifying docstring both moved (+242) and neither changed a word |
| 12 | *"`E-UNITS-ATTR-UNKNOWN` generalized"* | the code does not exist | **CONFIRMED.** `grep -rn "E-UNITS-ATTR-UNKNOWN" src/ docs/reference.md` → exit 1; control, `E-UNITS-ATTR-MISSING` → `validate.py`, `units.py`, `reference.md`, three test files |
| 13 | Resolver condition-independence | wiring, not construction | **CONFIRMED.** `config.SweptAway` still exists with `Node.__getattr__` raising on read; `runner.py:457` still plants it |
| 14 | `provenance.plugin_versions`; `hash_index` | verified | **CONFIRMED.** `cli.py` still writes the literal `"plugin_versions": {}` (moved to `:2683`); `manifest.POLICIES` still `("hash_all", "hash_index", "none")` |
| 15 | Import-failure containment at load | absent for plugins | **CONFIRMED, and the pattern to copy grew.** `discover_local`'s `except SystemExit` / `except Exception` pair now *drains pending into `partial`* rather than discarding. Copying the old shape would drop the payload |
| 16 | The § Errors rows for everything above | largest debt | **CONFIRMED, minus one line.** § 6 |
| 17 | `plugin new` / `plugin_scaffold.py` | unowned, absent, unfiled | **CONFIRMED on all three.** `publishable plugin new foo` → *"specified but not built"*, exit 2. `grep -n "plugin new\|plugin_scaffold" docs/superpowers/spec-defects.md` → **exit 1**, control being the same grep for `register_resolver`, which returns six hits. H7c's task 14 filed four entries and **none of them is this one** |

**The one item whose framing narrowed.** `H7b-SCOPING.md` § 5c called `register_probe`
without a consumer *"a fifth member"* of a four-member family of shipped-unread
`BaseTemplate` attributes. Re-measured: **the family is three, not four.** H7c built the
reader for `required_env`.

```
$ grep -rn "field_convention\|required_env\|apparatus_probe\|apparatus_facts" src/
templates/base.py:13,15,16,17          declarations
templates/builtin/generic.py:7,9,10,11 re-declarations
generators/template.py:9,12            "`required_env` now has a reader … `field_convention`,
                                        `apparatus_probe` and `apparatus_facts` are [not]"
validate.py:783,796,908 · cli.py:344   readers of `required_env` — NEW
```

So `register_probe` shipped bare would be a **fourth** member, not a fifth. The argument is
unchanged and slightly weaker in magnitude; the conclusion — ship it only with the *Probe is
installed* check that consumes it — stands. `spec-defects.md` now carries
`## OPEN — BaseTemplate.field_convention is declarable and read by nothing`, which is
`CLAUDE.md`'s worked example's new home.

---

## 2. `E-DATA-RESOLVER-UNSUPPORTED` — re-read end to end

**Two sites read `data.units.from.resolver`, and only one reports.** Enumerated by reading
`_check_unimplemented` and `_check_units` in full, then confirmed by
`grep -rn "RESOLVER" src` — which returns exactly `validate.py:1139` (the skip's docstring),
`:1185` (the skip) and `:3785` (the emit) and nothing else in `src/`.

| Site | What it does |
|---|---|
| `validate._check_unimplemented`, `:3785` | The one emit. Message names the **plugin registry** as the reason |
| `validate._check_units`, `:1185` | **Returns early, resolving nothing.** Not an emit site; where the refusal's blast radius lives |

`_check_unimplemented` still holds exactly two entries — the resolver source and
`statistics.null_test` — and its own closing comment still says so. It is a
`-UNSUPPORTED` refusal, so it is the undocumented build family: **no § Errors row, and it
must not gain one on the way out.** `reference.md` § The one config file's *"Two declarations
above are not yet built"* is where it is named, and that count drops to one when H7b lands.
H7c did not touch that sentence — re-read at `ff51864`.

**The complete set of things that must exist for it to retire**, read off the emit site and
the skip:

1. An entry-point name scan of `publishable.resolvers` (metadata only).
2. `register_resolver`, exported, checked against the key at load.
3. A load-time collision refusal across the group, **carrying whatever `partial_templates`
   is decided to mean for an entry point** (§ 3).
4. A read-only resolver `io` constructible with no run directory and no step.
5. Dispatch in `resolve_units`, preserving yield order.
6. The four § Validation rows that exist only under a resolver (§ 6), each with a code.
7. Deletion of the `_check_units` skip **in the same change** — its stated justification is
   the refusal.
8. `provenance.plugin_versions`, and `hash_index` over resolver-read plus unit-named paths.
9. **NEW: a redaction path for the resolver's own raise**, at both call sites (§ 5e).

---

## 3. The four registries, and the payload H7c added under them

### Build state, per registry — re-probed

```
register_template True      Unit      True
register_resolver False     Apparatus False
register_probe    False     BaseReport False
register_writer   False     Estimate  True
```

**H7c touched no registry** — the task brief said to verify rather than assume, and this is
the verification: three of four absent, with two live controls on the same call. What H7c
*did* touch is what a registry **raises**.

### `PartialLoadError` — the new constraint on every load-time refusal H7b mints

`git diff d86290c..ff51864 -- src/publishable/templates/discovery.py
src/publishable/templates/registry.py` is 47 lines and it is entirely this:

- `PartialLoadError(ContractError)` carries `partial_templates: list[type[BaseTemplate]]`.
  Its docstring is explicit that it is **not a new public error kind** — `.code` and
  `str(exc)` are unchanged and every existing `except ContractError` still matches.
- `discover_local` accumulates into `partial` at four points: both `except` arms now do
  `partial.extend(cls for _, cls in drain_pending())` where they previously discarded, the
  non-`BaseTemplate` arm appends the bad class, and the success arm appends the good one.
- `registry._merged` raises `PartialLoadError(..., partial_templates=[found.cls for found
  in local.values()])` for the core-shadow case.
- `validate_config`'s `except ContractError` reads `getattr(exc, "partial_templates", None)`
  and sets `c.credentials` from it, so a refused file's declared credential is redacted out
  of the refusal's own message.

**Three consequences H7b inherits, none of which is in the charter or the prior scoping:**

1. **`_merged` is the function H7b adds a third source to, and it is also the function that
   builds the payload.** Its payload expression names `local` explicitly. An installed
   source added without touching that line silently narrows the redaction to local
   templates — a fail-open of exactly the shape `CLAUDE.md` § Answering a question with a
   proxy describes, because `local.values()` is a *proxy* for "every class this pass
   constructed" that is correct only while local is the only non-core source.
2. **The entry-point half structurally has no payload.** § Creating a plugin's whole
   argument for entry points is that a name resolves *"without importing a line of that
   package"*. A plugin-side collision therefore holds no class, so its finding can carry no
   declared credential and cannot be redacted. That is a **documented residual**, not a
   defect — and it must be written down, because the natural repair (call `.load()` to get
   the class) destroys the invariant the whole mechanism exists for.
3. **`H7b-SCOPING.md` § 3's argument about the collision matrix survives and sharpens.**
   It argued the verdict must be computed over the *complete* claim set, on
   `discover_local`'s precedent — collect every claim, then verdict, in name order. An
   exception that *carries partially-loaded classes* does not weaken that: `partial` is a
   credential-reading convenience for a fault already decided, not an input to the verdict.
   Checked by reading, not assumed: `partial` is appended to and never read inside
   `discover_local`, and the verdict loop reads `claims`, never `partial`.

### `is_local_template` is still a boolean where H7b needs three values

```
$ grep -rn "is_local_template" src/
validate.py:39, :997        `_check_versions` early return
materialize.py:7, :103      writes `template_version` from core's own constant
discovery.py:106            the definition
```

Unchanged from `d86290c` in every respect except line number. The prior scoping's argument
stands verbatim and is not restated here: **the predicate must become a provenance
(`local` / `core` / `installed`) read at the merge**, and `validate._check_versions`'s
message *"the installed template reports {TEMPLATE_VERSION}"* is a false guarantee the
moment a second installed template can exist.

### `E-TEMPLATE-UNKNOWN` still has two emit sites and one shared wording

```
$ grep -rn "E-TEMPLATE-UNKNOWN\|unknown_template_message" src/
validate.py:569, :571          reports as a finding
generators/experiment.py:57,58 raises `ContractError`
registry.py:59, :75            the one shared message
```

**Confirmed: H7b changes one wording, not two.** But see § 5e — the *raising* site has no
collector, so it prints through `main`'s un-redacted handler.

---

## 4. Resolvers — the schema, and what the refusal actually suppresses

### The `from` envelope is open one level too far, and now for two reasons

`envelope.py` is byte-identical to `d86290c`. `LEAF_TYPES` types
`"data.units.from": (str, dict)` and stops, while `measurements`, `resample` and `holdout`
are each closed one level in. So the prior scoping's task stands.

**What is new is a second fault at the same seam, found by probe.** A `from` mapping
declaring **both** keys:

```
$ RES from={'glob': '*.csv', 'resolver': 'x'}   → ['E-DATA-RESOLVER-UNSUPPORTED']
```

`_check_unimplemented` branches on `"resolver" in source` and `_check_units` skips on the
same test — so `validate` calls it a resolver. `units.resolve_units` branches on
`"glob" in source` **first** — so a run would call it a glob. Today the refusal makes that
unreachable. **After task 24 it is reachable, and the two halves disagree about what the
config says.** So task 19 owes mutual exclusion, not only a type table entry. Control that
the probe can fail: the same mutation with a misspelled key,
`from={'resolverr': 'x'}`, reports `E-UNITS-SOURCE-MISSING` instead — a different code from
a different site.

That misspelling probe also **re-confirms `envelope.py:51`'s claim false at `ff51864`**:
*"a misspelled `resolverr` … is reported by no check in this build."* It is, as
`E-UNITS-SOURCE-MISSING`.

### The kept/lost matrix — re-run, not re-read

H7c gave `validate_config` new early-return behaviour around template load, which sits
**upstream of every check in this table**. Re-derived from scratch at `ff51864`, with the
project's own fixtures rather than the prior scoping's, one field mutated at a time,
against `from: index.csv` (control) and `from: {resolver: patient_trajectory}`:

```
  TAB clean            []
  RES clean            ['E-DATA-RESOLVER-UNSUPPORTED']
  TAB bad key          ['E-UNITS-KEY-MISSING']
  RES bad key          ['E-DATA-RESOLVER-UNSUPPORTED']                          ← lost
  TAB bad attribute    ['E-UNITS-ATTR-MISSING']
  RES bad attribute    ['E-DATA-RESOLVER-UNSUPPORTED']                          ← lost
  TAB fold k=99        ['E-REPL-FOLD-K-TOO-LARGE']
  RES fold k=99        ['E-DATA-RESOLVER-UNSUPPORTED']                          ← lost
  TAB measurements     ['E-CONFIG-TYPE', 'E-UNITS-COLLAPSE-RULE']
  RES measurements     ['E-CONFIG-TYPE', 'E-DATA-RESOLVER-UNSUPPORTED',
                        'E-UNITS-COLLAPSE-RULE']                                ← mixed
  TAB cluster_by unk   ['E-DATA-CLUSTER-UNKNOWN']
  RES cluster_by unk   ['E-DATA-CLUSTER-UNKNOWN', 'E-DATA-RESOLVER-UNSUPPORTED'] ← kept
  TAB weight_by unk    ['E-DATA-WEIGHT-UNKNOWN']
  RES weight_by unk    ['E-DATA-RESOLVER-UNSUPPORTED', 'E-DATA-WEIGHT-UNKNOWN']  ← kept
  TAB holdout strat    ['E-DATA-HOLDOUT-METHOD', 'E-DATA-HOLDOUT-STRATIFY-UNKNOWN']
  RES holdout strat    [both, + 'E-DATA-RESOLVER-UNSUPPORTED']                   ← kept
```

**The partition is confirmed: the line is exactly "does this check need the resolved
roster".** Declaration-against-declaration checks survive; everything reading the table is
lost. Two rows print different codes from the prior scoping's table — the `measurements`
mutation and the reserved-attribute one — because **my mutation differs, not because
behaviour moved**; the `measurements` row is the more interesting of the two, since it shows
an envelope-level `E-CONFIG-TYPE` and a values-level `E-UNITS-COLLAPSE-RULE` **both**
surviving under a resolver, which sharpens the partition rather than blurring it.

**`validate` collects, confirmed on this build rather than assumed.** Every `RES` row that
earns a second code prints it *alongside* `E-DATA-RESOLVER-UNSUPPORTED`. Nothing about
H7c's early return changes that, because the early return is at template *load* and every
row above resolves `generic` cleanly. So `H7b-SCOPING.md` § 9's mitigation — each Part A
test asserts its new finding appears **beside** the wholesale refusal — is still sound.

**The consequence the charter does not own** is unchanged: every lost check becomes reachable
for the first time against a *resolver-produced* roster, whose columns are whatever the
plugin yielded. `_from_table`'s messages interpolate `{source}` — *"which index.csv does not
have"* — and there is no source file to name.

---

## 5. Five things the charter treats as one line each

### (a) `WRITERS`/`READERS` symmetry — re-probed live, with its control

`artifacts.py` is untouched, so the prior scoping's reading holds; it is re-established here
by **behaviour** rather than by re-reading, because a docstring claim needs a mutation:

```
$ artifacts.WRITERS['.fastq'] = lambda rows: b'x'
$ StepIO._read(Path('a.fastq'))
RAISED KeyError KeyError('.fastq')
$ del artifacts.WRITERS['.fastq']          # control
$ StepIO._read(Path('a.fastq'))
b'x'
```

`_read`'s docstring — *"Inverts the same table `write` dispatches through"* — dispatches on
`WRITERS` and indexes `READERS`. A third-party writer key with no reader gives
`io.read_upstream` a bare `KeyError`, not a coded `ArtifactError`, and § Steps and artifacts's
*"what a writer takes is what its reader gives back"* is the promise that breaks. **The
mutation that can fail is adding a key to one dict only** — swapping a value between them is
a mutation whose two branches cannot differ.

### (b) `publishable.readers` — still a spec gap, and **still unfiled after H7c task 14**

The prior scoping flagged that the spine design calls this *"chartered into H7b"* while
`spec-defects.md` carried no entry. H7c's task 14 filed that family's first four entries.
Re-checked whether one of them is this:

```
$ grep -rn "publishable\.readers" docs src README.md
docs/superpowers/H7-SCOPING.md:291         prior scoping prose
docs/superpowers/H7b-SCOPING.md:11,292,299,509   prior scoping prose
docs/superpowers/specs/2026-08-08-implementation-spine-design.md:210
$ grep -n "publishable.readers" docs/superpowers/spec-defects.md      → exit 1
$ grep -n "register_resolver" docs/superpowers/spec-defects.md        → 6 hits (control)
```

**It is not.** The name appears in no `reference.md`, no `src/`, and no defects entry, while
§ Creating a plugin declares four groups and says of a writer *"its reader inverts it"* with
no mechanism for supplying one. H7b owes the filing and the spec decision — a fifth group,
or a stated convention that a writer's entry point resolves its inverse — before it owes any
code. **`H7b-SCOPING.md`'s conclusion here survives verbatim.**

### (c) `register_probe` without `Apparatus` — the family is three, not four

Re-measured in § 1. `required_env` now has three readers in `validate.py` and one in
`cli.py`; `field_convention`, `apparatus_probe` and `apparatus_facts` remain declarable and
unread, and `generators/template.py`'s comment was updated by H7c to say exactly that.
Exporting `register_probe` with no consumer adds a **fourth**, and an exported one. The
charter's *"registration and the is-it-registered answer only"* is defensible **if** the
§ Validation *Probe is installed* row is what consumes it — which means `validate` reading
`BaseTemplate.apparatus_probe` for the first time. Not defensible as a bare export.

### (d) Condition-independence is wiring, not construction

`config.SweptAway` unchanged: a sentinel substituted for a swept path whose
`Node.__getattr__` raises on the **read**, so the refusal lands under `E-STEP-SWEPT-PARAM`.
A resolver runs at validate time and receives a `cfg`; handing it a `SweptAway`-substituted
config is the whole check. Two consequences the charter does not carry: the identifier is a
**step** code raised for a resolver, so H7b either mints one or documents the reuse; and this
is the *wiring, not construction* shape H4a found for `statistics.resample`.

### (e) **NEW — the resolver's raise reaches stderr un-redacted, at both call sites**

This is the finding that most changes what H7b is, and it did not exist at `d86290c`.

H7c's decision 3 put redaction at exactly two serialization boundaries:
`runner.execute_plan`'s step-error path and `Collector.render()`. It then filed
`## OPEN — main's last-resort stderr handler prints an exception un-redacted, by
construction` (`spec-defects.md`), noting the handler *"remains reachable by any other
`PublishableError` raised outside a collector"* and that the one path H7c built into it was
closed in the same slice.

**H7b builds three new paths into it.** Probed end to end at `ff51864` by patching
`resolve_units` to raise with a sentinel — the pattern § 5a used for `WRITERS` — inside a
real scaffolded project whose config validates clean, and running the *actual* command:

| Probe | Result |
|---|---|
| **A — validate time, `ContractError`.** `validate.resolve_units` raises `ContractError("resolver failed: key=SENTINEL-sk-abc123")`; `credential_values` returns `{"MY_KEY": SENT}` as a real declaration would | **REDACTED.** `c.render()` prints `resolver failed: key=<redacted:MY_KEY>` |
| **B — validate time, any other exception.** The same site raises `ValueError` instead | **ESCAPES `validate_config` entirely** — `ValueError: resolver failed: key=SENTINEL-sk-abc123` propagates out. `_check_units`'s only guard is `except ContractError` (`validate.py:1233`) |
| **C — run time, `ContractError`.** `cli.resolve_units` raises the same fault; `publishable run configs/pilot/config.yaml` through `cli.main()` | **LEAKED.** stderr prints `error   E-UNITS-SOURCE-MISSING resolver failed: key=SENTINEL-sk-abc123`, verbatim, in `main`'s bare-handler format |

A is the control that makes B and C readable: the identical exception, from the identical
function, is redacted at one site and printed whole at another. Each probe can fail — A goes
red if `c.credentials` is not populated, C goes green if anything between `command_run` and
the call catches it.

**Why C leaks, structurally.** `command_run` begins at `cli.py:1321` and calls
`resolve_units` at `:1365`; `grep -n "^def \|try:\|except" ` over that span shows **no
enclosing `try`**. The credential set is computed at `:1547` — 182 lines later — and the
only `.credentials =` assignments in `cli.py` are at `:1770` and `:2653`, both after it. So
`command_run`'s own collectors never hold the values at the moment the roster resolves.
**The remedy is therefore not "wrap the call": it is to compute the credential set before
phase 5**, and a plan that reaches for a `try` will have fixed the wrong thing.

**Why B is the larger half.** *"`validate` is contracted never to raise"* is stated in
`validate_config`'s own guards for `load_experiment` and `template.validate` — both
deliberately broad `except Exception`. `_check_units` is narrow, and today that is correct,
because the only thing inside it that raises is core's own table reader. **After task 23 it
executes arbitrary plugin code**, and a resolver raising `KeyError` or `httpx.HTTPError`
turns a diagnosable config into a traceback. So task 28 owes both a broad guard at
`_check_units` — on the shape those two existing guards already establish — and a decision
about which identifier the resulting finding carries.

**The third path is `generators/experiment.py:57–58`**, which raises `E-TEMPLATE-UNKNOWN`
outside any collector today and is joined by every load-time collision H7b mints (§ 3).

**The validate-time site is covered only by an ordering nothing pins.** `validate_config`
sets `c.credentials` immediately after `_check_requires_env` and **before**
`_check_parameters`, `_check_data` and `_check_units` — which is why probe A redacts. A
slice that moves the resolver call earlier, or resolves the roster before the template
(a natural-looking simplification), silently inverts it. **It needs a test that goes red
when the two lines swap**, not a comment saying it is fine.

This is one whole task (28) plus a trap.

---

## 6. The documentation debt, and the row that still overclaims

### § Validation rows H7b owns — each re-checked for an emit site

Located by name (`grep -n "Resolver is installed\|…" docs/reference.md`), never by line.

| Row | Code at `ff51864` | H7b owes |
|---|---|---|
| *Template resolves* | `E-TEMPLATE-UNKNOWN`, built | The `plugin` hint. Row 211, **OPEN, owner H7b**, re-read |
| *Template name is claimed once* | `E-TEMPLATE-COLLISION`, built for the two local cases | The three plugin cases; the row's own closing clause still says they are not yet checked |
| *Template version moved*, first half | none | `BaseTemplate.version`. Row 212, **OPEN, owner H7b**, re-read |
| *Probe is installed* | **none** | The check and its code |
| *Resolver is installed* | **none** — only the `-UNSUPPORTED` refusal, which retires | The check and its code |
| *Resolver supplies the attributes* | partial — `E-UNITS-ATTR-MISSING`, worded against a table | Generalization |
| *Resolver supplies the measurement field* | **none** | The check and its code |
| *Resolver is condition-independent* | **none** | The check; reuse-or-mint (§ 5d) |

**No `E-RESOLVER-*`, `E-PROBE-*`, `E-PLUGIN-*`, `E-WRITER-*`, `E-READER-*` or
`E-APPARATUS-*` identifier exists anywhere.** Sweep by **file list**, not by filtering
output: `grep -rnE "E-(RESOLVER|PROBE|PLUGIN|WRITER|READER|APPARATUS)[A-Z-]*"` over
`docs/reference.md docs/design-principles.md docs/experimental-designs.md README.md src/`
→ exit 1. Can-fail control on the identical file list:
`grep -oE "E-TEMPLATE[A-Z-]*" docs/reference.md | sort -u` → five distinct codes. Plus the
load-time refusals § Creating a plugin describes in prose with **no identifier at all**: a
cross-group name collision, a shadow of a core name, a writer claiming a core suffix, and a
`@register_*` argument disagreeing with its key.

### The task that shrank, because H7c did the edit

`H7b-SCOPING.md` task 2 bundled *"place every new load fault in § Errors' documented
early-return ordering"* with *"fix `validate.py:519`'s **two today** count"*. Both were
rewritten by H7c, and both now distinguish **codes** from **shapes**:

- `reference.md` § Errors: *"That is five **codes**. `E-TEMPLATE-LOAD` covers three shapes …
  a `Param` whose construction raises is the first of them … adds a shape to
  `E-TEMPLATE-LOAD` without adding a row … or a sixth code to this count."*
- `validate.py`'s guard comment: *"two codes … Two *codes*, not two faults … Adding such a
  fault adds no code and does not move this count."*

So the residual is narrow and precise: **H7b moves that count only if a plugin-side load
fault is a new *code*.** If the three plugin collision cases ride `E-TEMPLATE-COLLISION` —
which the row's own wording anticipates — neither sentence moves. The decision belongs in
the design, and the task stays because the decision is real; it is no longer a rewrite.
This is the one place H7c made H7b smaller.

### `--plugin` still overclaims — re-probed, not remembered

```
$ publishable generate experiment p2 --template generic --plugin someuser/publishable-llm …
exit=0
$ grep -n "^plugin" configs/p2/config.yaml
8:plugin: null
$ publishable generate experiment p3 --template generic --nosuchflag x …
exit=0
$ grep -rn "uv add" src/            → exit 1
$ grep -rln "uv_lock" src/          → cli.py, uv_support.py   (control)
```

`reference.md` § Creation commands still marks `generate` **built** with *"`experiment`
accepts `--plugin`"*; § Plugins still says `--plugin <user>/<repo>` *"runs `uv add` … and
nothing more."* **Neither is true at `ff51864`.** `--plugin` is collected into `opts` and
dropped, as is any unknown flag. The CLI-table tests bind command names and `Status` markers,
not the arguments column — `tests/test_cli.py:6692` asserts **set equality** between the
document's `NOT BUILT` rows and `cli.NOT_BUILT_COMMANDS`, and says nothing about arguments —
which is why this survives a green suite.

### The `NOT BUILT` markers H7b retires, located by string

Sweeping the four documents by file list. Each was re-found by grep at `ff51864`; none is
cited by line number.

| Where | The claim |
|---|---|
| § The one config file, the `from:` line | `{resolver: <name>} (NOT BUILT)` |
| § The one config file, prose | *"**Two** declarations above are not yet built"* → one |
| § The one config file, the identifying-fields paragraph | *"the plugin case is not yet checked, since no entry point is resolved in this build"* |
| § Errors, `E-TEMPLATE-COLLISION` | *"A local name an **installed plugin** registers … is not yet checked"* |
| § Errors, `E-TEMPLATE-UNKNOWN` | *"An installed plugin's is not yet checked either"* |
| § Where units come from, second `from` enum comment | the three-value spelling |
| § Creating a plugin | *"The two local cases are the ones this build checks … the plugin cases arrive with entry-point resolution"* |
| § The importable surface | the three-name `register_resolver · register_probe · register_writer` `not yet built` row |
| § CLI reference | `publishable plugin new` and `list-templates`, both `NOT BUILT` |
| § Generators / § Creation commands | `generate` marked built with `--plugin` |
| § Package layout | `plugin_scaffold.py — not yet built` |

**And the enum comment is still out of sync**, re-probed by generating a real config:
`reference.md` writes `# index.csv | {glob: "*.dcm"} | {resolver: <name>} (NOT BUILT)`;
the generated config's `data.units.from` line carries `# index.csv | {glob: "*.dcm"}` —
**two values where the document defines three**, written by `materialize.py`. Live today,
and H7b edits that line anyway.

---

## 7. Comments in `src/` claiming guarantees the code does not provide

Swept by claim, filtered by file list. Nineteen of H7c's twenty-six review findings were
this shape, so this table is re-derived rather than carried.

| Site | Claim | Status at `ff51864` |
|---|---|---|
| `envelope.py:51` | *"a misspelled `resolverr` in a `data.units.from` mapping is **reported by no check** in this build"* | **Still false, re-probed.** `{resolverr: x}` → `E-UNITS-SOURCE-MISSING`. True only of *key-name* checking, which the sentence does not say |
| `envelope.py:208` | *"a `from` dict's `resolver` is **reached by no check** in this build: not here, and not by `_check_shape`"* | **Still false as written.** `_check_unimplemented` reads `source["resolver"]` and interpolates it; `_check_units` branches on it |
| `artifacts.py:855` | `_read`'s *"Inverts the same table `write` dispatches through"* | **Still true only by coincidence** — proved false by mutation, § 5a |
| `validate.py:1016` | `W-TEMPLATE-VERSION`'s *"the installed template reports {TEMPLATE_VERSION}"* | **Still true only while core is the only installer.** Row 212 |
| `validate.py:534` | *"two codes, `E-TEMPLATE-LOAD` and `E-TEMPLATE-COLLISION` … Adding such a fault adds no code and does not move this count"* | **Repaired by H7c.** Now false only if H7b mints a load *code*. § 6 |
| `validate.py:3838` | *"One `data.units` sub-field remains read by nothing"* | True today; H7b's to retire |
| `registry.py:86` | *"no template — core's, an installed plugin's, or this project's own `templates/` — registers"* | Aspirational; becomes true with H7b. **Not a defect** — recorded so it is not "fixed" |
| `registry.py:44` | `_merged`'s `partial_templates=[found.cls for found in local.values()]` | **No comment claims anything, and that is the finding.** The expression is a proxy for "every class this pass constructed", correct only while local is the only non-core source. § 3 |

Eight sites, five of them H7b's to own. Two were found the way `CLAUDE.md` prescribes — *if
a comment says this cannot happen, make it happen*.

---

## 8. The payoff, re-measured — and the prior scoping's finding 1 is dead

**`H7b-SCOPING.md` § 8 finding 1 said the analysis's own plugin cannot be written**, because
`Param.__init__` rejects `requires_env`, and concluded *"H7c must precede H7b … upgraded from
preference to dependency."* Re-probed at `ff51864` with the analysis's **actual**
declaration — `llm.provider`, three choices, the credential map § Parameters and
§ A credential can belong to a parameter value both show:

```
$ Param(str, default='azure_openai',
        choices=['azure_openai','openai','ollama'],
        requires_env={'azure_openai':['AZURE_OPENAI_API_KEY'],
                      'openai':['OPENAI_API_KEY'], 'ollama':[]})
constructed OK -> choices: azure_openai (needs AZURE_OPENAI_API_KEY) | openai (needs OPENAI_API_KEY) | ollama
```

It constructs, and its rendered comment is byte-identical to the one `reference.md` shows.
The blocker did not merely move to a different exception — controls confirm the totality
check is real and would have caught a partial map (`ValueError: requires_env must be total
over choices: choices are a, b; requires_env names a; no key for b`) and a `requires_env`
with no `choices`. **That conclusion did not survive. It is satisfied history.**

**The other three blockers are each re-verified unchanged:**

| Blocker | Command | Result |
|---|---|---|
| `io.reuse_from` | `grep -rn "reuse_from" src/` | exit 1; control `read_upstream` → `artifacts.py`. Now filed: `spec-defects.md` `## OPEN — io.reuse_from is unbuilt and unowned by any H7 sub-slice`, **owner unassigned** |
| The probe | `grep -rn "Apparatus\|register_probe" src/` | Only `apparatus_probe`/`apparatus_facts` declarations and unrelated prose. No `Apparatus`, no probe call |
| `plugin new` | `publishable plugin new foo` | *"specified but not built"*, exit 2 |

**Measured on 2026-08-16 against `ff51864`:**

> H7b retires **one refusal that 9 of 9 configs hit** (`E-DATA-RESOLVER-UNSUPPORTED`), and
> **zero experiments newly execute.** Three independent blockers remain, all outside H7b.

| Configs | Needs from H7b | Still blocked by |
|---|---|---|
| E1, E2, E5 | The resolver half in full: name resolution, dispatch, the attribute projection their `data.units.attributes` declares | H7d (the probe) and `plugin new`. Nothing else |
| E3, E4, E6 | The same | The same two, **plus `io.reuse_from`**, which no H7 sub-slice owns |
| C1, C2, C3 | The same | The same two, plus H4b's `E-DATA-WEIGHT-CONTRAST`, and `io.reuse_from` **unsettled** — the analysis says so in its own words |

**The honest form: H7b makes the nine configs *validate* against a plugin that can now be
written and that `plugin new` must still be able to produce.** That is worth having — it is
the first time `validate` answers a resolver name at all — but it is not an executable
count. The feasibility analysis's own § Executability entry dated 2026-08-16 already states
the H7c half of this correctly (*"H7c retires no refusal … a fourth, unrecorded blocker
sitting behind the three"*), and task 29 must re-date it rather than restate it.

---

## 9. Decomposition — 29 tasks, against the charter's 17 and the prior scoping's 27

Grain matches `H3d-SCOPING-2.md`, `H7b-SCOPING.md` and `H7c-SCOPING.md`: each document-table
edit and each new code is its own task. Numbering is this document's; the prior scoping's
number is given where it differs.

### Part A — declare and register. `E-DATA-RESOLVER-UNSUPPORTED` stays alive throughout · 20

| # | Task | Change against the prior scoping |
|---|---|---|
| 1 | **§ Validation ↔ § Errors `validate` reports**: mint codes for *Resolver is installed*, *Resolver supplies the measurement field*, *Resolver is condition-independent*, *Probe is installed*; settle reuse-vs-mint for `E-STEP-SWEPT-PARAM` | unchanged (was 1) |
| 2 | **§ Errors core raises + § Creating a plugin**: the four load-time refusals described in prose with no identifier; extend `E-TEMPLATE-COLLISION`'s row to the three plugin cases; **decide whether any of them is a new *code*, because only that moves § Errors' five-code count and `validate.py:534`** | **SHRUNK** (was 2). H7c rewrote both the prose and the comment to distinguish codes from shapes; the ordering edit is no longer owed, only the decision |
| 3 | **Settle and file the `publishable.readers` gap** — a fifth group or a stated convention — plus a `spec-defects.md` entry | unchanged (was 3). **Re-confirmed unfiled after H7c task 14** |
| 4 | **§ Package layout + § The importable surface**: a home for the shared entry-point scan; split the three-name `register_*` row as each lands | unchanged (was 4) |
| 5 | **The `NOT BUILT` markers and the enum comments**, including `materialize.py`'s two-value spelling of a three-value enum | unchanged (was 5). Re-probed live |
| 6 | **§ Creation commands / § Plugins: `--plugin`** — mark it honestly now, whichever way task 18 goes | unchanged (was 6). Re-probed live |
| 7 | **Entry-point metadata scan**, four groups, name → `EntryPoint`, no `.load()`. Fixture: a real installed distribution | unchanged (was 7) |
| 8 | **The collision matrix over metadata only**: entry-point × entry-point, × core, × local; providers named, name order not discovery order | unchanged (was 8), **constrained by task 20** |
| 9 | **Template provenance becomes three-valued**: `is_local_template` → `local`/`core`/`installed`, read at the merge; `_merged` takes a third source | unchanged (was 9) |
| 10 | **`BaseTemplate.version`; `W-TEMPLATE-VERSION` against it** — Row 212, a four-document change | unchanged (was 10). Row re-read, still OPEN |
| 11 | **`E-TEMPLATE-UNKNOWN`'s `plugin` hint** through the one shared `unknown_template_message` | unchanged (was 11). Row 211 re-read, still OPEN |
| 12 | **`register_resolver`** + export | unchanged (was 12) |
| 13 | **`register_probe`** + export, and the *Probe is installed* check that consumes it — `validate` reading `BaseTemplate.apparatus_probe` for the first time | unchanged (was 13); the unread-attribute family it joins is **three, not four** |
| 14 | **`register_writer`** + export; third-party suffixes into `WRITERS`; refusal of a core-suffix claim | unchanged (was 14) |
| 15 | **`WRITERS`/`READERS` symmetry made an enforced invariant**, `_read`'s docstring corrected | unchanged (was 15). Re-proved by mutation |
| 16 | **The decorator-vs-key check at load**, `run`/`dry-run` only — plus the stated consequence that `validate` cannot see a disagreement | unchanged (was 16) |
| 17 | **Import-failure containment for a plugin module**, `SystemExit` included | **WIDENED** (was 17). `discover_local`'s pattern now *drains pending into `partial`*; copying the `d86290c` shape drops the payload |
| 18 | **`--plugin` on `generate experiment` / `init`**: `uv add`, and the `plugin` config field written | unchanged (was 18) |
| 19 | **Envelope closure of `data.units.from`** one level in (`glob`, `resolver`); **plus mutual exclusion — a mapping declaring both validates as one thing and would resolve as another**; retire `envelope.py`'s two false comments | **WIDENED** (was 19). The both-keys fault is new, found by probe |
| 20 | **NEW — `PartialLoadError` semantics for the entry-point half.** Extend `_merged`'s payload past `local.values()`; decide and **document** that a metadata-only collision carries no class and so cannot be redacted; file the residual | **NEW.** H7c's mechanism; neither the charter nor the prior scoping could have had it |

### Part B — resolve, and retire the refusal · 9

| # | Task | Change against the prior scoping |
|---|---|---|
| 21 | **`plugin new` / `plugin_scaffold.py`** — atomically with § Creation commands' `NOT BUILT` marker and `cli.NOT_BUILT_COMMANDS`, since `tests/test_cli.py:6692` asserts set equality | unchanged (was 20) |
| 22 | **The read-only resolver `io`** — `read_input` and nothing else, no run directory, no step | unchanged (was 21) |
| 23 | **Resolver dispatch in `resolve_units`**, yield order preserved into `provenance.units` / `units_hash` | unchanged (was 22) |
| 24 | **Retire `E-DATA-RESOLVER-UNSUPPORTED` and the `_check_units` skip in one change**; add *Resolver is installed* | unchanged (was 23) |
| 25 | **Attribute projection**; `E-UNITS-ATTR-MISSING`'s `{source}`-worded message generalized | unchanged (was 24). `E-UNITS-ATTR-UNKNOWN` re-confirmed non-existent |
| 26 | **Condition-independence through `SweptAway`** | unchanged (was 25) |
| 27 | **`provenance.plugin_versions` populated; `hash_index` over resolver-read plus unit-named paths** | unchanged (was 26) |
| 28 | **NEW — the resolver's raise, at both sites.** Compute the run's credential set **before** phase 5 (`cli.py`'s `resolve_units` sits 182 lines above `credential_values`, uncaught, and leaks a sentinel through `main` verbatim); widen `_check_units`'s `except ContractError` so a plugin resolver raising anything else does not escape `validate_config`; pin the validate-time ordering with a test that goes red when the two lines swap | **NEW.** § 5e. Three probes, one of them its own control |
| 29 | **The owned prose sweep and the reader-facing half**: § 6's eleven document sites, § 7's five owned `src/` claims, the newly-live roster-check family tested against a resolver-produced roster, and a **re-dated** § Executability entry | unchanged (was 27) |

### The seam, at 20/21

**Ship Part A (1–20) and Part B (21–29) as two slices.** This is the seam `H7-SCOPING` § 8
named and the prior scoping adopted; it moves by one only because task 20 is new and belongs
with the collision matrix it constrains.

- **It keeps the wholesale refusal alive across the seam**, which is what H3d's seam bought
  and what `envelope.py`'s own comment argues for: shape checked before values honoured.
- **Part A delivers three registries, the collision matrix and the whole documentation debt
  with no change to `units.py` and no roster.** Part B touches `units.py`, `artifacts.py`,
  `cli.py` and `validate.py`'s skip.
- **Neither half is past twenty**, this repo's own band (H3c-1 20, H3d 19, H7c 14).

**The price, unchanged and re-confirmed on this build.** `validate` collects (§ 4), so every
Part A test on a resolver-adjacent config pins a finding list containing
`E-DATA-RESOLVER-UNSUPPORTED`, and **task 24 retires it**. Mitigate as before: require each
Part A test to assert positively that its new finding appears **alongside** the wholesale
refusal, so the retirement is a deletion rather than a rewrite.

If the slice ships whole, task 24 is the ordering constraint: nothing may retire the refusal
before 22, 23, 25, 26 and 28 land.

---

## 9b. What the charter does not own but this slice will inevitably touch

- **The test environment gains a real installed distribution.** Tasks 7, 8 and 21 all need
  one: an entry-point *metadata* scan cannot be exercised by a fixture that only writes
  files, and the collision matrix needs **two** distributions (§ 10). So `tests/` gains a
  packaging fixture and the suite gains an install step — a build-infrastructure cost in
  neither the charter nor the prior scoping, and the direct analogue of `H7c-SCOPING` § 7's
  `python-dotenv` note. `H7b-SCOPING.md` task 7 said *"test fixture: a real installed
  distribution"* in a cell and drew no consequence from it.
- **`cli.py`'s phase ordering** (§ 5e), which no task in either prior document touches.
- **`spec-defects.md`'s `## OPEN — declared_credential_names reports a template-default
  credential for a parameter value never written`**, filed by H7c against `validate.py` and
  `cli.py`. Both readers take `template.parameter_spec`; after task 9 that spec can come
  from an installed plugin, so the entry widens without anyone editing it. H7b owes an
  amendment, not a closure.
- **`pyproject.toml`**, if the packaging fixture needs a dev dependency or a test extra.
- **`CLAUDE.md` § Misreadings**, whose *unbuilt reader of a shipped surface* example moved
  to `field_convention` with H7c and moves again if task 13 reads `apparatus_probe`.

---

## 10. Traps specific to this slice

**A proxy for "where did this class come from" — now in two predicates, not one.**
`is_local_template` is the known one (§ 3). The new one is `_merged`'s
`partial_templates=[found.cls for found in local.values()]`: it answers "every class this
pass constructed" with "every *local* class", which is right only while local is the only
non-core source — and task 9 is the task that makes it wrong. **The direct question is asked
at the merge**, where all three sources are in hand, which is where the provenance answer
must live too.

**A redaction whose coverage is a line ordering.** § 5e. `validate_config` sets
`c.credentials` before `_check_units`, so a resolver's raise at validate time is redacted;
`cli.py` computes the same set 182 lines *after* `resolve_units`, so the same raise at run
time is not. Neither placement is asserted anywhere. **The mutation that can fail is
swapping the two lines** — not adding a comment, and not a test that merely asserts the
sentinel is absent, which passes identically if the resolver never raised.

**A control asserting only absences, in the shape H7c already paid for.** A leak test for
task 28 that sweeps artifacts for a sentinel and finds nothing proves nothing unless a
mutation — a resolver that raises with the sentinel in its message — makes it go red. Sweep
by **file list**, never by filtering output.

**`.load()` at `validate` time.** `EntryPoint.name` is metadata; `.load()` is an import.
`validate` is documented as creating nothing and reaching nothing *off the machine*, and
§ Creating a plugin justifies the whole entry-point mechanism by that promise. Task 20 adds
a second, sharper reason to keep it: a metadata-only collision has no class, so the
temptation to `.load()` will now arrive dressed as *"we need the class to redact its
credentials."* It is not worth the invariant, and the residual must be documented instead.

**H7a's local discovery still inverts the entry-point argument, and the inversion is still
live.** It is *already documented* — § Creating a plugin's paragraph beginning *"That
authority costs the guarantee two paragraphs up"* states it in full. So the tension
`H7a-SCOPING` § 5(a) flagged is **resolved in the documents and unresolved in the
mechanism**: after H7b one command resolves names by two methods with opposite import costs.
The thing to avoid is "simplifying" them into one.

**A check written where the roster is not.** § 4: the surviving checks under a resolver are
the declaration-against-declaration ones. A test that mutates `cluster_by` to prove the
resolver path works proves nothing — that check fires today, with the refusal in place.

**A mutation aimed at the dict rather than at the dispatch.** § 5a: `WRITERS` and `READERS`
hold the same five keys, so swapping a *value* between them cannot fail. The mutation that
can is adding a key to one dict only — demonstrated above, with its control.

**Two elements cannot distinguish four orderings.** The collision matrix has four cases and
three sources. One local plus one installed template rules out one pairing; the
entry-point × entry-point case needs **two** installed distributions, and the
name-order-not-discovery-order property needs names whose sorted order differs from their
install order. Count the orderings, then size the fixture.

**A `-UNSUPPORTED` retirement is not a § Errors row.** `E-DATA-RESOLVER-UNSUPPORTED` has no
row and must not gain one on its way out; § The one config file's *"Two declarations above
are not yet built"* is where it is named and where the count drops to one.

**A carried line number.** Demonstrated in this document's header: every `validate.py`
address in the prior scoping moved by ≈ +242 in one slice, while the code at each did not
change by a character. Cite by name.

---

## 11. What is NOT in H7b

| Out | Owner |
|---|---|
| `secrets.py`, `.env`, `required_env`, `Param(requires_env=)` | **H7c — merged.** No longer a prerequisite, and no longer a sibling: it is done (§ 8) |
| `Apparatus`, probe execution, the ledger, per-condition facts, the change gate | **H7d.** H7b ships `register_probe` and the *Probe is installed* answer only, and only because that row consumes it |
| `field_convention`, the third still-unread `BaseTemplate` member | **Unowned.** `spec-defects.md` `## OPEN — BaseTemplate.field_convention is declarable and read by nothing`, filed by H7c |
| `io.reuse_from` and `lineage.py` | **Unowned**, and now filed as such by H7c task 14. Blocks E3/E4/E6 independently (§ 8) |
| Closing `main`'s un-redacted stderr handler | **Unowned**, filed OPEN by H7c with its reasoning. H7b owes only that it does not *widen* the exposure — which is task 28, a different thing from closing it |
| `publishable list-templates` | Its `Status` row stays `NOT BUILT`. Reachable after task 9; recorded so nobody folds it in unbriefed |
| `BaseReport` / `generate report` | H8 for behaviour; the export is the § The importable surface residual |
| The README managed regions — `credentials`, a parameter-table region, `generate experiment`'s merge | `docs` for the merge; **`new` for the `credentials` region itself**, per `H7c-SCOPING.md` § 7's correction to `H7b-SCOPING.md` § 11, which is accepted here rather than re-argued |
| The unknown-flag silent acceptance in `_dispatch_generate` (`--nosuchflag x` → exit 0) | Not H7b's; re-probed at `ff51864` and still unfiled. Worth a `spec-defects.md` entry from whoever files task 3's |
| Anything extending `HASHED_TREES` | Never. A plugin is pinned by `uv.lock`, not by `code_hash` |
| `statistics.null_test` | H4d. It is the **other** remaining `_check_unimplemented` entry, and retiring one must not retire the loop |
