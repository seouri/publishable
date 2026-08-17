# H7b Part B re-scoping — the resolver, and retiring `E-DATA-RESOLVER-UNSUPPORTED`

Read-only measurement against `main` at `53090e9`, on 2026-08-17. This re-measures tasks 21–29 of
`H7b-SCOPING-2.md` § 9 Part B, which was taken 2026-08-16 against `ff51864` — **before H7b Part A
merged**. Part A touched every file Part B acts on except `units.py`. Every identifier below was
grepped, probed or executed against `53090e9`; nothing is carried. Where this document contradicts
`H7b-SCOPING-2.md` it says so and shows the command; where it confirms it, it says that too.

**Verdict: 13 tasks**, against the prior document's 9. Two prior tasks shrank to residuals because
Part A wrote their documentation debt in advance; five items are new, and one of them is a
**normative contradiction between two sentences of `reference.md`** that Part B cannot ship without
settling.

**Baseline at `53090e9`:** `uv run pytest -q` → **2060 passed, 1 skipped, 2 xfailed**, 114 s. (The
Part A ledger records the same triple at its merge commit; re-run here rather than carried, per
this repo's rule.)

**The headline the charter asks for, measured rather than asserted: three of the nine feasibility
experiments have no remaining core-side blocker once this slice lands** — E1, E2 and E5 — against
the prior document's *zero of nine*. § 8 itemizes it, including which of the prior document's three
named blockers survives (one and a half of three).

---

## 0. Executive summary — the six things that change what Part B is

1. **`reference.md` now says two things that cannot both hold, and Part B is the slice that makes
   them collide.** § Errors' early-return prose states flatly *"`validate` never imports a
   plugin"*, and `E-PLUGIN-DECORATOR`/`E-PLUGIN-LOAD`'s rows say the object behind a key is reached
   *"at `run` and `dry-run` and **never** at `validate`."* § Where units come from says of a
   resolver: *"**It runs at `validate` and `dry-run`, not only at `run`.**"* Executing a resolver
   requires importing it. Part A shipped both halves and pinned the no-import half in two tests and
   a module docstring. **This is a decision task with a three-to-five-site edit** — three sentences
   are false unconditionally, two more turn on a choice task 24 has not made — **and it is the
   finding most likely to be missed.** § 2.
2. **The prior document's remedy for the credential leak is insufficient, and I can show it.** All
   three of its probes reproduce at `53090e9` — plus a fourth it did not run. But `redact()` has
   **exactly two call sites**, `Collector.render` and `runner.execute_plan`, and **`main`'s handler
   is neither**: it prints `f"  error   {exc.code:<20} {exc}"` raw. So *"compute the credential set
   before phase 5, do **not** wrap the call"* fixes nothing on its own — moving the computation
   gives you the values with no site that applies them. The raise must **also** be routed through
   `command_run`'s existing collector. § 5.
3. **Part A wrote Part B's documentation debt in advance, and it is smaller and sharper than the
   prior document's eleven sites.** `E-RESOLVER-UNKNOWN`, `E-RESOLVER-MEASUREMENT-FIELD` and
   `E-RESOLVER-SWEPT-PARAM` all exist as § Errors rows carrying an explicit **`Not yet emitted:`**
   marker — `grep -c "Not yet emitted" docs/reference.md` → **3**, all three resolver codes. Six of
   the prior § 6's eleven `NOT BUILT` sites were consumed by Part A. Part B's document work is now
   *strike three markers and five sites*, not *write eight rows*. § 6.
4. **Four of the six shipped-but-unread surfaces Part A filed are Part B's, by name.**
   `spec-defects.md` says so: `RESOLVERS`, `load_entry_point`, `check_registration` and
   `declared_names` all get their **first production caller** in this slice. So does a filed hazard
   — `## OPEN — a core-suffix claim's E-PLUGIN-COLLISION becomes E-PLUGIN-LOAD once loading is
   wired — **Owner: H7b Part B**`. None of this existed when the prior document was written. § 3.
5. **`hash_index` is a documented rule with no code, and it is broken for the *table* case too, not
   only the resolver's.** `build_manifest(input_dir, policy, index_names=None)` — `cli.py` calls it
   with **two** arguments, and `grep -rn "index_names" tests/` returns nothing. Probed: under
   `hash_index` **every** `sha256` comes back `None`. Three `reference.md` passages promise the
   index is hashed. Task 27's half of this is real work; the other half is a pre-existing defect
   nobody has filed. § 7.
6. **The prior document's *"H7d (the probe) blocks all nine"* does not survive.** `apparatus_probe`
   has exactly **one** reader in `src/` — `validate._check_probe`, a *name* check against the
   metadata scan — and nothing at run time reads it. A template declaring a probe whose entry point
   is installed validates clean and runs; it records `apparatus: null`, which is a false record
   under § The apparatus core can only observe's own definition, but it is not an execution
   blocker. § 8.

---

## 1. What Part A changed, and what it therefore could have invalidated

`git diff --numstat ff51864..53090e9 -- src docs tests CLAUDE.md README.md pyproject.toml` names the
complete set (added / removed):

```
 14    2   CLAUDE.md                                 158   37   src/publishable/validate.py
 23    0   docs/feasibility-llm-growth-studies.md    140   36   src/publishable/templates/registry.py
 56   23   docs/reference.md                         300    0   src/publishable/plugins.py   (new)
172    0   docs/superpowers/spec-defects.md           67    4   src/publishable/generators/experiment.py
  5    0   src/publishable/__init__.py                44    4   src/publishable/artifacts.py
 15    9   src/publishable/envelope.py                13   10   src/publishable/generators/template.py
 10    0   src/publishable/cli.py                      7    4   src/publishable/materialize.py
  6    0   src/publishable/templates/base.py           2    0   src/publishable/templates/builtin/generic.py
```

Plus eight test files, `tests/test_plugins.py` (534 lines) new.

**Byte-identical across the merge**, and therefore the files whose claims below are *re-run* rather
than *re-derived* — checked one at a time with `git diff --quiet ff51864..53090e9 -- <path>`:

```
IDENTICAL units.py manifest.py hashes.py provenance.py scaffold.py
IDENTICAL runner.py config.py secrets.py diagnostics.py errors.py base_step.py
```

Control on the same command shape: `git log --oneline ff51864..53090e9 -- src/publishable/validate.py`
returns eight commits, `--  src/publishable/units.py` returns none.

**Note which files that puts on each side.** `units.py` — the file task 25's dispatch lives in — is
untouched, so every claim about `resolve_units` is re-run. `envelope.py`, `materialize.py` and
`templates/base.py` **were** touched, contradicting the prior document's list of seven files it
called byte-identical: three of those seven moved in one slice. Claims about them below are
re-derived from the merged tree.

### The prior document's Part B verification, re-checked item by item

| Prior claim | At `ff51864` | At `53090e9` |
|---|---|---|
| `E-UNITS-ATTR-UNKNOWN` does not exist | absent | **CONFIRMED absent.** `grep -rn "E-UNITS-ATTR-UNKNOWN" src/ docs/reference.md` → exit 1; control, `grep -rln "E-UNITS-ATTR-MISSING" src/ docs/reference.md tests/` → six files |
| `resolve_units` branches `str` → `_from_table`, `{glob:}` → `_from_glob`, else raise | so | **CONFIRMED**, and `units.py` is byte-identical, so this is re-run trivially |
| `StepIO.__init__` takes `step_dir`, `input_dir`, `run_dir` as required keyword `Path`s | so | **CONFIRMED**, read at `artifacts.py`'s `class StepIO`. `artifacts.py` *was* touched (task 14/15) but not in `__init__` |
| `config.SweptAway` exists; `runner.py` plants it | so | **CONFIRMED.** `grep -rn "SweptAway" src/` → `config.py:20,54`, `runner.py:13,436,457`, `cli.py:289`. Both files byte-identical |
| `cli.py` writes the literal `"plugin_versions": {}` | `:2683` | **CONFIRMED**, still `cli.py:2683`, still a literal |
| `manifest.POLICIES` is `("hash_all", "hash_index", "none")` | so | **CONFIRMED** — and § 7 shows the policy is a no-op, which neither prior document measured |
| `io.reuse_from` unbuilt | absent | **CONFIRMED absent.** `grep -rn "reuse_from" src/` → exit 1; control, `grep -rln "read_upstream" src/` → `plugins.py`, `artifacts.py`. Still filed **owner unassigned** |
| `plugin new` / `plugin_scaffold.py` absent and unowned | so | **CONFIRMED.** `ls src/publishable/generators/` → `__init__.py experiment.py step.py template.py`, no `plugin_scaffold.py`; `cli.NOT_BUILT_COMMANDS` still holds `"plugin new"`. **Still unfiled in `spec-defects.md`** |
| The `_check_units` skip and its docstring both unchanged | so | **CONFIRMED unchanged in wording**, moved to `validate.py`'s `_check_units` at `:1303–1304` (skip) and `:1257–1260` (docstring) |
| `--plugin` silently dropped; § Creation commands overclaims | so | **DEAD.** Part A commit `3fbaf13` built it — `grep -rn "uv add" src/` → `generators/experiment.py:55,67,73`. The prior document's tasks 6 and 18 are both spent |
| `envelope.py:51` and `:208`'s two false comments | both false | **DEAD.** Part A task 19 closed the envelope: `LEAF_TYPES` now types `data.units.from.glob` and `.resolver`. Neither sentence survives |
| `artifacts.py`'s `_read` *"Inverts the same table"* true only by coincidence | so | **DEAD.** Part A task 15 rewrote the docstring to *"Two tables and one dispatch"* and added the `E-ARTIFACT-UNREADABLE` raise |
| A `from` declaring both `glob` and `resolver` has two answers | live | **DEAD.** Part A minted `E-UNITS-SOURCE-AMBIGUOUS`; `validate._check_from_source_exclusivity` refuses it |
| `BaseTemplate.version` absent (Row 212) | absent | **DEAD.** `grep -n "version" src/publishable/templates/base.py` → `version: str \| None = None` at `:24` |

**Ten of the fourteen re-confirm; four are dead, all four because Part A did the work.** That is the
opposite direction from every prior re-scoping in this repo, and it is worth naming: a Part A/Part B
seam is the one case where a scoping goes stale by getting *smaller*.

---

## 2. The contradiction Part B must settle before it writes a line

**Two normative sentences, both shipped by Part A, cannot both hold after task 25.**

Located by name, not by line — but quoted so the sweep is reproducible
(`grep -n "never imports a plugin" docs/reference.md`, `grep -n "runs at \`validate\` and" docs/reference.md`):

| Site | What it says |
|---|---|
| § Errors `validate` reports, the early-return prose | *"`E-PLUGIN-DECORATOR` and `E-PLUGIN-LOAD` are not reported by `validate` at all, early-return or not — **`validate` never imports a plugin**, so neither check runs there."* |
| § Errors core raises, `E-PLUGIN-DECORATOR`'s row | *"the object behind a key is loaded only at `run` and `dry-run` … **`validate` cannot see this disagreement** either way, a property of the guarantee rather than a gap in the check"* |
| § Errors core raises, `E-PLUGIN-LOAD`'s row | *"reached, once something imports a plugin, at `run` and `dry-run` and **never at `validate`**"* |
| `plugins.py`'s module docstring | *"`validate` is not such a caller"* — of `load_entry_point` |
| `plugins.py`'s `check_registration` docstring | *"Meant to run only once an object behind a key has actually been loaded — **not `validate`**"* |
| § Where units come from | *"**It runs at `validate` and `dry-run`, not only at `run`.** Every unit check in the validation table … is a question about the resolved table, so the table has to exist before a step does. A resolver that walks a large archive pays for that walk each time you validate."* |

The last one is the design. It is argued for at length, it is why `_check_units` resolves the roster
at all, and it is the reason the kept/lost matrix exists. **So `validate` must import the plugin a
`data.units.from.resolver` names.**

**What survives, and it is the sentence that matters.** § Creating a plugin's actual guarantee is
narrower than the five sentences above: *"`validate` can answer 'no installed package registers
`plate_wells`' **without importing a line of that package**."* That is a claim about the **negative**
answer, and it survives intact — `E-RESOLVER-UNKNOWN` is answered from `plugins.names()`, metadata
only. `CLAUDE.md`'s own invariant is worded the same narrow way (*"so `validate` resolves a name
without importing the package"*) and also survives. It is the five *generalizations* of it, written
while nothing loaded anything, that break.

**What does not survive, checked rather than assumed.** Part A's whole-branch review answered
*"no path reachable from `validate` imports a plugin"* by probe and recorded it as the slice's
central finding. Two tests pin it: `tests/test_plugins.py::test_the_scan_imports_nothing` and
`tests/test_templates.py::test_get_template_imports_nothing_for_an_installed_claim`. **Neither
breaks under Part B** — both are pinned at `scan_group` and `get_template`, and Part B touches
neither — which is exactly the hazard: the invariant Part B retires is pinned nowhere that Part B
will trip over. It dies silently in the documents while the tests stay green.

**Three of the five sites are false unconditionally; two are false only under a choice task 24 has
not made.** Separated here rather than swept together, because rewriting a sentence that did not need
rewriting is a habit this repo has paid for:

| Site | Why |
|---|---|
| § Errors' *"`validate` never imports a plugin"* | **Unconditional.** Executing a resolver imports it, whatever else Part B does |
| `E-PLUGIN-LOAD`'s *"never at `validate`"* | **Unconditional.** `load_entry_point` is the import, and it raises that code; `validate` calls it |
| `plugins.py` module docstring's *"`validate` is not such a caller"* | **Unconditional.** Same reason |
| `E-PLUGIN-DECORATOR`'s *"`validate` cannot see this disagreement"* | **Contingent.** Its `"validate … never holds the decorated object"` clause is false either way, but the *conclusion* survives if Part B calls `check_registration` at `run` only |
| `check_registration`'s docstring *"not `validate`"* | **Contingent**, on the same choice |

**So the discriminating question the design owes is: does Part B call `check_registration` at
`validate` time, or only at `run`?** Answering *run only* keeps two of the five sites intact and
costs a config a diagnostic `validate` could have given. Answering *both* rewrites all five. The
measurement does not decide it; it names the price of each.

**This is a task, and it must precede the dispatch.** The decision to make: does `validate` load a
resolver (the design as written, three document sentences to rewrite plus two docstrings), or does
the resolver run only at `run`/`dry-run` (one document sentence to rewrite, and every unit check
under a resolver becomes deferred — which is the thing § Where units come from's paragraph exists to
refuse)? **The measurement says the first, and says the cost is five sites.** But it is a decision
with an argument on both ends and it belongs in the design, not in a task brief.

---

## 3. What Part A left for Part B by name — the filings

`spec-defects.md` names Part B as owner in two entries. Read at `53090e9`, quoted rather than
summarized because both carry conditions:

**`## OPEN — PROBES and RESOLVERS are written by their decorators and read by nothing`**, amended
2026-08-17 by the whole-branch review's finding I4:

> `load_entry_point`, `check_registration` and `declared_names` are group-generic … so their first
> production caller is whichever slice first dispatches *any* group, which by construction is
> **H7b Part B** … **Owner:** … `RESOLVERS`, `load_entry_point`, `check_registration`,
> `declared_names` → **H7b Part B**, the resolver-dispatch task.

Verified against the code: `grep -rn "load_entry_point\|check_registration\|declared_names" src/`
returns only `plugins.py`'s own definitions and its own docstrings. Control on the same file list:
`grep -rn "scan_group" src/` returns `plugins.py` **and** `templates/registry.py` — a caller.

**Four of the six shipped-but-unread surfaces close in this slice.** `PROBES` stays (H7d);
`registry.template_provenance` stays (unassigned). **If a Part B task ships without wiring one, the
filing count goes up rather than down**, because the entry names Part B as the owner and a closed
slice that did not close it re-owners to nobody — the exact shape `CLAUDE.md` § Habits names.

**`## OPEN — a core-suffix claim's `E-PLUGIN-COLLISION` becomes `E-PLUGIN-LOAD` once loading is
wired — Owner: H7b Part B`.** This one is a live hazard, not bookkeeping. `register_writer` and
`register_reader` raise `ContractError(code="E-PLUGIN-COLLISION")` at decoration time. The moment
`load_entry_point` has a caller, that raise happens **inside** `ep.load()`, where
`load_entry_point`'s broad `except Exception` re-reports it as `E-PLUGIN-LOAD`. The entry states the
two acceptable resolutions (let it stand and document the precedent, or catch `ContractError` ahead
of the broad arm). **Neither prior document has this.**

### `load_entry_point` is a ready-made path, and it is the second place user code can raise

Read in full rather than grepped. `load_entry_point(ep)`:

- drains the pending template buffer **before** the import (not this call's registrations to
  inherit),
- calls `ep.load()` — the sole `.load()` in the package,
- wraps `SystemExit` and `Exception` into `PartialLoadError(code="E-PLUGIN-LOAD")`,
- drains **again** on the success return, and returns `ep.load()`'s object.

So task 24's shape is already built: `scan_group("publishable.resolvers")` → `load_entry_point(ep)`
→ `check_registration(ep, declared_names("publishable.resolvers", fn))` → call `fn`. **Three of the
four Part-B-owned surfaces get their caller in one function.**

**And it is a second arbitrary-raise site the prior document could not have scoped.** A plugin's
module-level `import httpx` failing is an `ImportError` inside `ep.load()` — caught, re-raised as
`PartialLoadError`, which *is* a `ContractError`, so `_check_units`'s narrow guard sees it. Good. But
a plugin's top level calling `os._exit()`, or the resolver body itself raising `KeyError`, is
neither. § 5's probe B covers the resolver body; the import path is covered by construction. Say so
in the design rather than discovering it.

---

## 4. `E-DATA-RESOLVER-UNSUPPORTED` — every site, and what retiring it needs

Enumerated by **reading** `_check_unimplemented`, `_check_units` and
`_check_from_source_exclusivity` in full, then confirmed by `grep -rn "RESOLVER" src/`, which
returns nothing outside these files plus `plugins.py`'s `RESOLVERS` registry.

| Site | What it does |
|---|---|
| `validate._check_unimplemented` | **The one emit.** Message rewritten by Part A: *"names `X`, but a **resolver cannot be dispatched in this build**; resolvers will be honored in a later slice"* |
| `validate._check_units` | **Returns early, resolving nothing.** Not an emit site. The blast radius |
| `validate._check_units`'s docstring | Justifies the skip *by* the refusal — so both die together, unchanged from the prior document's finding |
| `_check_unimplemented`'s two closing comments | *"One `data.units` sub-field remains read by nothing: a `resolver` source"* — Part A rewrote the parenthetical to say the registry **is** built and only the loading is not |

**The prior document's headline about the message is confirmed and is a Part B input.** The old
wording (*"the plugin registry is not implemented in this build"*) was falsified by Part A and
rewritten under the whole-branch review's finding I3. The current wording is true today and false
the moment task 26 lands, so **task 26 deletes it rather than editing it** — which is what the
Part A design's decision 7 bought by requiring every Part A test to assert the refusal *alongside*
its own finding.

**The complete set of things that must exist for it to retire, re-derived at `53090e9`:**

1. ~~An entry-point name scan of `publishable.resolvers`~~ — **built** (`plugins.scan_group`, five
   groups including this one).
2. ~~`register_resolver`, exported~~ — **built** (`publishable/__init__.py`, `RESOLVERS`).
3. ~~A load-time collision refusal across the group~~ — **built** (`validate._check_plugin_collisions`
   → `E-PLUGIN-COLLISION`, over the complete claim set in name order).
4. A read-only resolver `io` — **absent**. `StepIO.__init__` still requires `step_dir` and `run_dir`.
5. Dispatch in `resolve_units`, yield order preserved — **absent**.
6. ~~The § Validation rows and their codes~~ — **written**, all four, three carrying `Not yet
   emitted:` and one (`One source per roster` / `E-UNITS-SOURCE-AMBIGUOUS`) already emitting.
7. Deletion of the `_check_units` skip in the same change — **owed**.
8. `provenance.plugin_versions` and `hash_index` — **both absent**, and `hash_index` is worse than
   absent (§ 7).
9. A redaction path for the resolver's own raise — **owed, and the prior document's remedy is
   wrong** (§ 5).
10. **NEW: name resolution must be decided against § 2's contradiction** before anything loads.
11. **NEW: the `E-PLUGIN-COLLISION` → `E-PLUGIN-LOAD` re-code decision** (§ 3).

**Four of eleven were done by Part A; two are new.**

### The kept/lost matrix is unchanged in structure, re-run rather than re-read

Re-run at `53090e9` on the analysis's own E1 block against a 240-row synthetic table, with the
resolver form and the table form side by side, and with a discriminating control:

```
E1 as written  {resolver: patient_trajectory} → E-DATA-RESOLVER-UNSUPPORTED  (+ 2 fixture-owned errors)
E1 table       index.csv                      → 0 additional errors, 1 warning (W-DATA-CLUSTER-UNDECLARED on age_band)
E1 table, holdout.frac: 0  (control)          → + E-DATA-HOLDOUT-FRAC
```

The control is the one the feasibility analysis itself prescribes, and it fires. **So the resolver
form adds exactly one code to E1 and loses every roster-reading check**, which is the partition the
prior document established and which re-confirms here without re-deriving it.

`validate` collects, confirmed on this build rather than assumed: every run above reports its
fixture-owned `E-NAME-DIR` and `E-CRED-MISSING` **beside** the resolver refusal, never instead of it.

---

## 5. The credential leak — all four paths probed, and the prior remedy falsified

### The two call sites, measured

`command_run` begins at `cli.py:1321`, calls `resolve_units` at `:1365`, and computes
`credential_values(...)` at `:1547`. **182 lines, identical to the prior document's number** — Part
A's ten added `cli.py` lines are all elsewhere. Read `1321`–`1372` in full: **no enclosing `try`**,
and the only `.credentials =` assignments in the file are at `:1770` and `:2653`, both after.

`validate_config`'s ordering **did** move, and in the direction that matters:
`c.credentials = credential_values(declared_credential_names_for(doc, template))` sits at `:646`
and `_check_units` at `:651` — **five lines**, with Part A's new `_check_plugin_collisions` (`:636`)
and `_check_probe` (`:639`) *above* the credentials line.

### The four probes

Run inside a real scaffolded project (`publishable new`, `generate experiment`, a local template
declaring `required_env = ["MY_KEY"]`, `MY_KEY=SENTINEL-sk-abc123`, config validating clean at exit
0), by monkeypatching the `resolve_units` binding in each module and driving `cli.main` — the actual
command, not a helper.

| Probe | Result at `53090e9` |
|---|---|
| **A — `validate`, `ContractError`** | **REDACTED.** `error E-UNITS-SOURCE-MISSING data.units / resolver failed: key=<redacted:MY_KEY>` |
| **B — `validate`, `ValueError`** | **ESCAPES `validate_config`.** `ValueError: resolver failed: key=SENTINEL-sk-abc123` propagates. `_check_units`'s only guard is `except ContractError` |
| **C — `run`, `ContractError`** | **LEAKED.** stderr prints `error E-UNITS-SOURCE-MISSING resolver failed: key=SENTINEL-sk-abc123`, verbatim, in `main`'s bare-handler format |
| **D — `run`, `ValueError`** *(new — the prior document ran three)* | **ESCAPES `main` entirely.** Neither `except PublishableError` nor `except OSError` sees it; a real invocation ends in a traceback with the sentinel in it |

A is the control that makes B, C and D readable: the identical exception, from the identical
function, is redacted at one site and printed whole at another. **All three of the prior document's
probes reproduce.** D is new and is the worse half of C — a plugin resolver raising `KeyError` at
`run` gets no diagnostic at all, and the traceback carries the message.

### Why the prior remedy is insufficient — and this is the conclusion that does not survive

`H7b-SCOPING-2.md` § 5e: *"The remedy is therefore **not** 'wrap the call': it is to compute the
credential set before phase 5, and a plan that reaches for a `try` will have fixed the wrong thing."*
The Part A design repeats it verbatim: *"The remedy is to move the credential computation, **not** to
wrap the call."*

**Measured:** `grep -rn "redact(" src/publishable/ | grep -v "def redact"` returns **exactly two**
sites — `diagnostics.py:69` (`Collector.render`) and `runner.py:710` (`execute_plan`'s step-error
path). `main`'s handler is neither; it prints `f"  error   {exc.code:<20} {exc}"` with no collector
in scope. **So moving `credential_values` above phase 5 produces a set of values that nothing
applies.** The leak persists byte-for-byte.

The working remedy is **both**, and `command_run` already has half of it: `c = Collector()` exists at
`:1322`. Set `c.credentials` before phase 5, **and** catch the resolver's raise into `c.error(...)` /
`print(c.render())` at or above `:1365`. That *is* wrapping the call — with the credential move as
the precondition that makes the wrap do anything.

**The prior document was right about the diagnosis and wrong about the fix**, and a plan written from
it would have shipped a probe C that still leaks with a green suite, because a test asserting "the
sentinel is absent" passes identically when the resolver never raised.

### Two things the prior document said about the `validate` side that also do not survive

- *"The validate-time site is covered only by an ordering nothing pins … a slice that moves the
  resolver call earlier silently inverts it. It needs a test that goes red when the two lines swap."*
  **Read the code Part A shipped:** `c.credentials`'s own comment states *"Redaction happens at
  render, not at construction … so setting this after the fact still covers every finding already
  appended."* Probe A redacts because `c.render()` runs after `:646`, **not** because `:646` precedes
  `:651`. Swapping those two lines does not invert anything. The ordering that is load-bearing is
  `c.credentials` before `c.render()` — and the only way to break *that* is to resolve the roster
  before the **template**, since `declared_credential_names_for` needs the template. **The mutation
  the prior document prescribes cannot fail.** § 10 records it as such.
- The prior document names `generators/experiment.py`'s `E-TEMPLATE-UNKNOWN` raise as "the third
  path" into `main`'s handler. At `53090e9` that site raises `E-TEMPLATE-INSTALLED-UNSUPPORTED` as
  well (`generators/experiment.py:110`), added by Part A's task 8-11 review C1. Still outside any
  collector; still not Part B's to close; **its shape changed and the prior sentence's file/line
  citation is stale.**

---

## 6. The documentation debt, re-measured — smaller and sharper than the prior eleven

### The three `Not yet emitted:` markers are the whole of the new-code debt

`grep -n "Not yet emitted" docs/reference.md` → **three hits, all resolver codes**, each an
`E-` row already written in full with its wording, its argument and its cross-references:

| Code | Its marker | Part B task |
|---|---|---|
| `E-RESOLVER-UNKNOWN` | *"the resolver source is refused wholesale in this build, and this code **replaces that refusal** when the dispatch lands"* | 24 / 26 |
| `E-RESOLVER-MEASUREMENT-FIELD` | *"a resolver-produced roster does not exist in this build"* | 28 |
| `E-RESOLVER-SWEPT-PARAM` | *"no resolver is executed in this build"* | 29 |

Can-fail control on the same file: `grep -oE "E-RESOLVER[A-Z-]*" docs/reference.md | sort -u` → three
distinct codes. **The prior document's *"No `E-RESOLVER-*`, `E-PROBE-*`, `E-PLUGIN-*`, `E-WRITER-*`,
`E-READER-*` or `E-APPARATUS-*` identifier exists anywhere"* is dead** — Part A minted six
(`E-RESOLVER-` ×3, `E-PROBE-UNKNOWN`, `E-PLUGIN-COLLISION`, `E-PLUGIN-DECORATOR`, `E-PLUGIN-LOAD`).

**`E-RESOLVER-SWEPT-PARAM` settles the prior document's open reuse-or-mint question.** Its row argues
the mint explicitly (*"that identifier is a step's, reached at run time … a reader holding it is sent
to a section describing a different fault at a different time"*). Part B honours the decision; it does
not re-make it.

### The eleven `NOT BUILT` sites, classified across the seam

Swept by naming the four documents plus `CLAUDE.md`, never by filtering output.

| Prior § 6 site | State at `53090e9` |
|---|---|
| § The one config file, the `from:` line `{resolver: <name>} (NOT BUILT)` | **LIVE — Part B's** |
| § The one config file, *"**Two** declarations above are not yet built"* | **LIVE — Part B's**, drops to one (`statistics.null_test`, H4d) |
| § The one config file, *"the plugin case is not yet checked"* | **CONSUMED by Part A** — the paragraph now describes `E-TEMPLATE-INSTALLED-UNSUPPORTED` instead |
| § Errors, `E-TEMPLATE-COLLISION`'s *"an installed plugin … is not yet checked"* | **CONSUMED by Part A** |
| § Errors, `E-TEMPLATE-UNKNOWN`'s *"An installed plugin's is not yet checked either"* | **CONSUMED by Part A** |
| § Where units come from, second `from` enum comment | **CONSUMED by Part A** (`materialize.py` now writes all three values) — but see below |
| § Creating a plugin, *"the plugin cases arrive with entry-point resolution"* | **CONSUMED by Part A** |
| § The importable surface, the three-name `not yet built` row | **CONSUMED by Part A** — split into five `built` decorator rows |
| § CLI reference, `plugin new` and `list-templates` | **`plugin new` LIVE — Part B's** (task 21). `list-templates` stays `NOT BUILT` |
| § Generators / § Creation commands, `generate` with `--plugin` | **CONSUMED by Part A** (built at `3fbaf13`) |
| § Package layout, `plugin_scaffold.py — not yet built` | **LIVE — Part B's** (task 21) |

**Six consumed, five live.** Re-probed rather than remembered for the enum comment: a freshly
generated config's `data.units.from` line now reads
`# index.csv | {glob: "*.dcm"} | {resolver: <name>} (NOT BUILT)` — three values, matching
`reference.md`. `materialize.py`'s source is a single literal `"| {resolver: <name>} (NOT BUILT)"`,
and **task 26 must strike the marker there and in `reference.md` in one change**, or the generated
config and the document disagree about build state again.

### Four dated build claims Part B retires

New since the prior document, and easy to miss because they read as prose rather than as markers.
`grep -rn "As measured on 2026-08-17 against commit .deaed2b." docs/reference.md src/` → four hits:

| Site | The claim |
|---|---|
| `reference.md`, `E-PLUGIN-DECORATOR`'s row | *"no task has yet given it a production caller — perishable, since the next slice to import a plugin closes that gap"* |
| `reference.md`, `E-PLUGIN-LOAD`'s row | *"no task has yet given it a production caller either"* |
| `plugins.py` module docstring | *"no command has yet been wired to call it"* |
| `plugins.py` `check_registration` docstring | *"no command yet loads a plugin, so this function has no production caller either"* |

`deaed2b` is a real commit reachable from `main` (`git cat-file -t deaed2b` → `commit`). **Part B is
the slice these four name.** Each is dated exactly the way the repo prescribes, and each expires when
task 24 lands — so retiring them is not optional tidying, it is the mechanism working.

---

## 7. `hash_index` — a documented rule with no code, and it is bigger than task 27

`reference.md` promises the same thing at three sites:

- § Three hashes' table: *"`hash_index` — Content hashes for the files `data.units.from` resolves —
  the index and whatever it names"*
- § What `run.yaml` records: *"Under `hash_index` the `sha256` key is present for the files
  `data.units.from` resolves and absent for the rest"*
- § Where units come from: *"'the index and whatever it names' means the paths the resolver read plus
  the paths its units name"*

**Measured.** `build_manifest(input_dir, policy, index_names=None)` — `grep -rn "build_manifest\|index_names=" src/publishable/cli.py`
returns exactly one call, `cli.py:1613`, passing **two** arguments. `grep -rn "index_names" tests/`
→ **exit 1**; control, `grep -rn "index_names" src/publishable/*.py` → two hits in `manifest.py`.
Probed by behaviour, with its control:

```
build_manifest(d, 'hash_index') → {'index.csv': {'size': 51, 'mtime': …, 'sha256': None}}
build_manifest(d, 'hash_all')   → sha256 = 9c26988de7119d33…      (control)
```

**Under `hash_index` nothing is hashed at all**, for a table source as much as for a resolver, and
`hash_index` appears in **no test file**. `manifest.py` is byte-identical across Part A, so this
predates both prior documents and neither found it — `grep -n "hash_index" docs/superpowers/spec-defects.md`
→ exit 1.

The prior document's task 27 owns *"`hash_index` over resolver-read plus unit-named paths"*. **It
cannot be built without also closing the table case**, because the parameter it must pass is the same
parameter, and half-passing it would make `hash_index` correct for resolvers and silently empty for
every table run that already exists. This is a `CLAUDE.md` § *Assuming a documented rule has code
behind it* instance — five of those shipped in one slice before — and it is the one item here that
Part B will inevitably touch and does not own.

---

## 8. The nine feasibility experiments — how many actually execute

**Three of nine**, against the prior document's zero. Itemized rather than asserted, and the honest
qualifications are stated with it.

### Blocker by blocker, re-verified

| Blocker | Command | Result | Blocks |
|---|---|---|---|
| The resolver dispatch | § 4 | **Part B retires it** | — |
| `io.reuse_from` | `grep -rn "reuse_from" src/` → exit 1; control `read_upstream` → 2 files | **unbuilt, owner unassigned** | E3, E4, E6 |
| `E-DATA-WEIGHT-CONTRAST` | `grep -rn '"E-DATA-WEIGHT-CONTRAST"' src/` → one emit, `validate.py:4966`; the other four hits are prose | **H4b** | C1, C2, C3 |
| The apparatus probe | `grep -rn "apparatus_probe" src/` → **one reader**, `validate._check_probe` | **does not block execution** | none |
| `plugin new` | `cli.NOT_BUILT_COMMANDS` holds `"plugin new"` | **blocks the workflow, not the run** | none |

**The probe claim is the one that changed, and it is the prior document's to lose.**
`H7b-SCOPING-2.md` § 8's table names *"H7d (the probe)"* as a blocker on all nine rows. Measured:
`apparatus_probe` is read at exactly one site, `validate._check_probe`, which compares the declared
*name* against `plugins.names("publishable.probes")` — metadata only — and reports
`E-PROBE-UNKNOWN` if absent. **Nothing at run time reads it.** So a template declaring
`apparatus_probe: llm_deployment`, with the plugin's `publishable.probes` entry point installed,
validates clean and runs to completion.

**With one consequence worth carrying rather than tidying away.** `cli.py:2678` writes
`"apparatus": None` as a hardcoded literal, and § The apparatus core can only observe defines
`apparatus: null` as meaning *"no probe declared"*. After Part B, a run whose template **does**
declare a probe records `apparatus: null` — a record that is false under the document's own
definition. That is H7d's to close, it is not an execution blocker, and it is **newly reachable
because of this slice**. It should be filed by Part B, not discovered by H7d.

`plugin new` is the same shape from the other side: it is a scaffolding convenience. A hand-written
`publishable-llm` package with the five entry-point groups in its `pyproject.toml` installs and
resolves today. **Counting it as an execution blocker conflates the workflow with the run**, and the
prior document's table does exactly that.

### The nine, after Part B

**The cell wording is deliberate.** What was measured is *"this config's `data`/`statistics` blocks
validate with zero errors and every field they declare is honoured"*, which the analysis's own
§ Executability is careful to distinguish from *executes*: **"a block validating clean is not a
config that can execute when the method its steps call does not exist."** So the cells say **no
remaining core-side blocker**, and "executes" is reserved for the prose below, which carries the
three conditions. The distinction is the whole reason that section exists.

| Config | State once this slice lands |
|---|---|
| **E1** screen-calibration | **No remaining core-side blocker.** Resolver dispatched; `holdout` built (H3d); `weight_by: null`; `resample` built (H4a). Measured: its `data`/`statistics` blocks validate with **zero** errors under the table substitution at `53090e9`, with `holdout.frac: 0` as the can-fail control |
| **E2** screen-primary | **No remaining core-side blocker.** Same shape |
| **E5** screen-repeatability | **No remaining core-side blocker.** `resample: null`, `correction: none`. The analysis's § Executability says E5 needs *"one correction of its own, described in § E5"*; read there, that section's own correction is a config-authoring one — a single-condition run **omits** `sweep` rather than writing it empty, which would earn `E-SWEEP-EXPANDS-EMPTY` |
| **E3** screen-cohort-sensitivity | **Blocked** — reads its frozen program through `io.reuse_from`. Unbuilt, **unowned** |
| **E4** screen-reasoning-effort | **Blocked** — same |
| **E6** screen-transfer | **Blocked** — same, plus a swept `program_id` resolved through it |
| **C1/C2/C3** shortcut | **Blocked** — `weight_by` beside a baseline or contrast, `E-DATA-WEIGHT-CONTRAST`, **H4b**. Whether they also carry `io.reuse_from` is unsettled and the analysis says so |

**The honest form, in the shape the feasibility analysis's own § Executability uses:**

> H7b Part B retires **one refusal that 9 of 9 configs hit** (`E-DATA-RESOLVER-UNSUPPORTED`), and
> **three experiments — E1, E2, E5 — have no remaining core-side blocker.** That is the first
> non-zero executable count this project has produced. It is conditional on the plugin being
> written and installed (`plugin new` scaffolds it; a hand-written package works today), and on
> accepting that a declared apparatus probe is neither executed nor recorded. Six stay blocked, on
> two causes neither of which is H7b's: `io.reuse_from` (unbuilt, **unowned**) and
> `E-DATA-WEIGHT-CONTRAST` (H4b).

Task 33 must **re-date** the analysis's § Executability section with this, not restate it — and must
state the three qualifications, because *"three of nine execute"* without them is the same
retired-refusal-count-as-executable-count conflation that section was written to prevent.

---

## 9. § CLI reference's `Status` column — which rows move

`tests/test_cli.py:6765` asserts **set equality** between the document's `NOT BUILT` command rows and
`cli.NOT_BUILT_COMMANDS`, so any row that moves must move in both places in one commit. Confirmed by
reading the assertion, not by the prior document's line number, which moved.

| Row | Moves? |
|---|---|
| `publishable plugin new` | **Yes — `NOT BUILT` → built**, task 21. Removes `"plugin new"` from `NOT_BUILT_COMMANDS` |
| `publishable generate` | **No.** Its arguments cell already says *"`experiment` accepts `--plugin`"* and Part A made that true |
| `publishable list-templates` | **No**, and it is now *overclaiming in the other direction*: it has been reachable since Part A's task 9 made `template_names` list installed claims. Recorded so nobody folds it in unbriefed — it stays `NOT BUILT` |
| `publishable dry-run` | **No** — but § Where units come from says a resolver *"runs at `validate` and `dry-run`"*, and `dry-run` does not exist. The sentence is a spec claim about an unbuilt command, which is correct present tense; **do not "fix" it** |
| § Generators, `report` | **No** |
| § Package layout, `plugin_scaffold.py` | **Yes**, task 21, atomically with the CLI row |

**Nothing else in the three `Status`-carrying tables moves.** The rows were enumerated by reading
each table, not by counting: `grep -c "NOT BUILT" docs/reference.md` → **23**, which is more than the
row count because the marker also appears in prose (§ Generators' *"is NOT BUILT"* sentences, the
`Status`-column paragraph, the config-file cross-reference). **That is exactly why the count is not
the measurement** — a sweep that answers "where does this spelling appear" is not a sweep that
answers "which rows move".

---

## 10. Decomposition — 13 tasks, against the prior document's 9

Grain matches `H7c-SCOPING.md`, `H3d-SCOPING-2.md` and the Part A design: each new code emitted and
each document-table edit is its own task. Prior numbering given where it maps.

| # | Task | Against the prior document |
|---|---|---|
| 21 | **`plugin new` / `plugin_scaffold.py`** — scaffolds a package declaring **five** entry-point groups and using the five decorators, atomically with § CLI reference's row, § Package layout's marker, and `cli.NOT_BUILT_COMMANDS` | **WIDENED** (was 21). Part A minted `publishable.readers` and `register_reader`, so a scaffold that emits four groups is already stale |
| 22 | **Settle *does `validate` import a plugin*** — the decision, plus the three `reference.md` sentences and two `plugins.py` docstrings it falsifies | **NEW.** § 2. Neither prior document could have had it; it must precede 24 |
| 23 | **The read-only resolver `io`** — `read_input` and nothing else, no run directory, no step | unchanged (was 22) |
| 24 | **Resolver name resolution and load** — `scan_group` → `load_entry_point` → `check_registration`/`declared_names`; `E-RESOLVER-UNKNOWN` emitted, its `Not yet emitted:` marker struck; **the `E-PLUGIN-COLLISION` → `E-PLUGIN-LOAD` re-code decision** (§ 3) | **NEW as a separate task.** The prior document folded name resolution into the dispatch; Part A built the pieces, so it is now its own step with its own filed hazard |
| 25 | **Dispatch in `resolve_units`** — `cfg` threaded (it receives none today), yield order preserved into `provenance.units`/`units_hash` | unchanged in intent (was 23); see the ripple note below |
| 26 | **Retire `E-DATA-RESOLVER-UNSUPPORTED` and the `_check_units` skip in one change** — plus § The one config file's `NOT BUILT` marker, its *"Two declarations"* count, and `materialize.py`'s literal, in the same commit | unchanged (was 24), now with an exact document site list |
| 27 | **Attribute projection** — `E-UNITS-ATTR-MISSING`'s `{source}`-worded message generalized past *"which index.csv does not have"* | unchanged (was 25) |
| 28 | **`E-RESOLVER-MEASUREMENT-FIELD` emitted**, marker struck — the yield-one-`Unit`-per-measurement obligation | **SPLIT OUT** of prior 25. It is a distinct code with its own row |
| 29 | **Condition-independence** — `SweptAway`-substituted `cfg` handed to the resolver; `E-RESOLVER-SWEPT-PARAM` emitted, marker struck | **SHRUNK** (was 26). The reuse-or-mint decision is settled by Part A's row |
| 30 | **`provenance.plugin_versions` populated**; the four dated *no production caller* notes retired; `spec-defects.md`'s shipped-but-unread filing amended for the four surfaces this slice reads | **WIDENED** (was half of 27). § 3, § 6 |
| 31 | **`hash_index`** — `index_names` threaded at `cli.py`'s `build_manifest` call for the **table** case and the resolver case together | **WIDENED** (was half of 27). § 7. A documented rule with no code and no test |
| 32 | **The credential leak** — `c.credentials` set before phase 5 **and** the resolver's raise routed through `command_run`'s collector; `_check_units`'s `except ContractError` widened; probe D (a non-`PublishableError` at `run`) covered | **REMEDY CHANGED** (was 28). § 5. A plan written from the prior document fixes nothing |
| 33 | **The owned prose sweep and the reader-facing half** — the newly-live roster-check family tested against a resolver-produced roster, `_check_unimplemented`'s closing comments, and a **re-dated** § Executability entry carrying § 8's three-of-nine with its three qualifications | unchanged (was 29) |

**Sequencing.** 22 before 24 — the decision decides whether 24 exists in the form written. 23 before
25. 24 before 25 (dispatch needs the object). 25 before 26, 27, 28, 29. **26 last among the
refusal-adjacent set**: nothing may retire the wholesale refusal before 23, 25, 27, 28, 29 and 32
land, which is the discipline Part A's decision 7 bought.

**No seam.** 13 is inside this repo's band (H3c-1 20, H3d 19, H7c 14, H7b Part A 20), and there is no
cut that keeps the wholesale refusal alive across it without shipping an executing resolver with no
condition-independence check — which would let a swept-parameter resolver run, the exact fault
`E-RESOLVER-SWEPT-PARAM` exists to refuse. **If it runs long, drop task 21.** `plugin new` is the
only task with no dependency on the rest and no bearing on the refusal, and § 8 shows it blocks the
workflow rather than any run.

### The ripple task 25 carries, measured

Counted by the **call** spelling, not by the name — `grep -rn "resolve_units" src/ tests/` returns
docstring mentions too, and the number carries an argument:

```
grep -c 'resolve_units(' tests/test_units.py  → 56
grep -c 'resolve_units(' tests/test_cli.py    →  4
```

Plus **2 production call sites** (`validate.py:1350`, `cli.py:1365`). A resolver needs the `cfg` that
`resolve_units(units_decl, input_dir)` does not receive. **Adding `cfg` as a keyword with a default
keeps all 60 test call sites compiling** — at the price that a resolver source reached with
`cfg=None` must refuse rather than crash, which is a guard the design must name. A required third
parameter is a 60-site edit. Neither prior document measured this.

---

## 11. What the charter does not own but this slice will inevitably touch

- **`manifest.py` and every existing `hash_index` run** (§ 7). Task 31 cannot close the resolver half
  without closing the table half, and the table half has no test today.
- **`cli.py`'s phase ordering** (§ 5), which no task in either prior document touches.
- **`"apparatus": None` at `cli.py:2678`** (§ 8). Part B makes a false `apparatus: null` record
  reachable for the first time. **File it; do not fix it** — a reader for it is `Apparatus`, facts,
  the ledger and the change gate, all H7d.
- **`spec-defects.md`'s `## OPEN — an installed template's name resolves but its class is never
  loaded`**, owner **unassigned**. Its "what retiring it needs" list names `provenance.plugin_versions`
  — which task 30 builds. The entry needs an amendment, not a closure, and the amendment is Part B's
  because Part B moves one of its three preconditions.
- **`tests/test_units.py`'s ≈ 70 `resolve_units` call sites** (§ 10).
- **The installed-distribution fixture `tests/conftest.py` gained in Part A task 7.** Part B's
  resolver tests need one that is **genuinely importable** — Part A's no-import tests deliberately
  target unimportable modules, and the task 8-11 review already caught the inverse hazard (*"tasks 13
  or 15 making one importable would have silently retired the guarantee"*). Reusing that fixture
  without reading its intent is how the no-import assertions get defused.
- **`CLAUDE.md` § Misreadings**, whose *unbuilt reader of a shipped surface* example is currently
  `field_convention`; four of the six shipped-but-unread surfaces close here.

---

## 12. Documented with no code, and code with no row — in this area

| Item | State |
|---|---|
| `hash_index` hashing the index | **Documented at three sites, implemented nowhere, tested nowhere.** § 7. **Unfiled — task 31 should file it**, since task 31 is the only work that cannot proceed without closing it |
| `apparatus: null` meaning *no probe declared* | **Documented; the code writes the literal unconditionally.** § 8. Becomes false-in-practice with Part B |
| `E-RESOLVER-UNKNOWN` · `E-RESOLVER-MEASUREMENT-FIELD` · `E-RESOLVER-SWEPT-PARAM` | **Rows with no emit site**, each honestly marked `Not yet emitted:`. This is the mechanism working, not a defect |
| `E-PLUGIN-DECORATOR` · `E-PLUGIN-LOAD` | **Rows whose emit sites exist and have no caller**, each honestly dated. Same |
| *"`validate` never imports a plugin"* | **Prose with code behind it today and a design against it.** § 2 |
| § Validation *One source per roster* | **Row and code, both built** by Part A. Recorded so it is not re-scoped as owed |

---

## 13. False guarantees in the files Part B must edit

Swept by claim, filtered by file list. Five Criticals of this shape shipped in Part A alone, so this
table is re-derived rather than carried; the prior document's eight sites are re-checked and four are
gone.

| Site | Claim | Status at `53090e9` |
|---|---|---|
| `plugins.py` module docstring | *"`validate` is not such a caller"* — of `load_entry_point` | **True today, false after task 24.** § 2. Part B's, and it is the paragraph that justifies the mechanism, so it must be **re-argued** rather than given an exception clause — the fix Part A's own C1 was made to take |
| `plugins.py` `check_registration` docstring | *"Meant to run only once an object behind a key has actually been loaded — not `validate`"* | **Contingent** on whether task 24 calls it at `validate`. Part B's to decide, then edit or keep |
| `reference.md` § Errors early-return prose | *"`validate` never imports a plugin, so neither check runs there"* | **False unconditionally, and normative.** Part B's |
| `reference.md` `E-PLUGIN-LOAD`'s row | *"never at `validate`"* | **False unconditionally** — `load_entry_point` raises it and `validate` calls it. Part B's |
| `reference.md` `E-PLUGIN-DECORATOR`'s row | *"`validate` cannot see this disagreement … a property of the guarantee rather than a gap"* | **Contingent**, same choice; but its *"`validate` … never holds the decorated object"* clause is false either way |
| `validate._check_units` docstring | *"resolvers … already refused as `E-DATA-RESOLVER-UNSUPPORTED`; `resolve_units` cannot execute a resolver either"* | **True today**, and dies with task 26. Part B's |
| `validate._check_unimplemented` closing comment | *"One `data.units` sub-field remains read by nothing: a `resolver` source"* | **True today.** Part B's to retire |
| `manifest.build_manifest` docstring | *"Relative paths plus size, mtime, and — **at the policy's depth** — content hash"* | **False for `hash_index`**, which has no depth because nothing supplies `index_names`. § 7 |
| `envelope.py:51`, `envelope.py:208`, `artifacts.py`'s `_read` | the prior document's three | **All three repaired by Part A.** Recorded so they are not re-filed |

---

## 14. Traps specific to this slice

**A guarantee that dies in the documents while every test stays green.** § 2. The no-import invariant
is pinned at `scan_group` and `get_template`, and Part B touches neither. Retiring it is a document
edit with no failing test to prompt it — the single most likely thing to be shipped wrong. **The
discriminating question is not "does a test break" but "which sentence is now false".**

**The mutation the prior document prescribes cannot fail.** § 5: *"a test that goes red when the two
lines swap"* — `c.credentials` at `:646` and `_check_units` at `:651`. Redaction happens at
**render**, and `c.credentials`'s own comment says so, so swapping them changes nothing. **A mutation
is a claim too**; this one has two branches that cannot differ, and it is the eleventh such shape
this repo has caught. The mutation that *can* fail is resolving the roster before the template
resolves, because `declared_credential_names_for` needs the template.

**A leak test asserting only an absence.** § 5's probes C and D. Sweeping stderr for a sentinel and
finding nothing passes identically when the resolver never raised. Pair it with probe A as the
control that proves the sentinel is reachable, exactly as this document did.

**Answering "did `hash_index` work" with the manifest's shape rather than its content.** § 7: the
`sha256` **key is present** and its value is `None`. An assertion on `"sha256" in entry` passes on a
completely broken policy. The document's own wording anticipates this — *"Absent rather than null, so
'not hashed' can't be misread as 'hashed to nothing'"* — and the code does the thing the document
says it must not.

**A check written where the roster is not.** § 4's matrix: the checks that *survive* under a resolver
today are the declaration-against-declaration ones. A test mutating `cluster_by` to prove the
resolver path works proves nothing — that check fires today, with the refusal in place. The
discriminating fixtures are the **lost** ones: a bad `key`, a bad attribute, `fold k=99`.

**A resolver fixture whose config shape varies while its roster does not.** `CLAUDE.md` § Writing
checks that can fail names this directly. Nineteen adversary configs over one roster made every
refusal roster-incidental once. Task 27 and 28 are *about* what the roster contains; vary the
resolver's **yield**, not the config.

**`validate` collects rather than aborting.** Three readers got this wrong across two slices, and it
matters twice here: a resolver that raises does **not** make later checks unreachable, and every
Part A test on a resolver-adjacent config pins a finding list containing the wholesale refusal, so
task 26 is a deletion in those lists rather than a rewrite. Verified live in § 4.

**A grep for one spelling.** `E-DATA-RESOLVER-UNSUPPORTED` appears at four sites in `validate.py` and
**only one of them emits**. `apparatus_probe` appears at six sites in `src/` and **only one of them
reads it**. Both counts above were reached by reading the functions and then confirming by grep, in
that order — the substitution that shipped a credential leak two slices ago.

**A carried line number.** The prior document proved ≈ +242 drift in one slice and then wrote its own
findings with fresh line numbers anyway. Of its Part B citations, `cli.py:1321/:1365/:1547` and the
182-line gap survive exactly; `validate.py:1233`'s guard is now at `_check_units`'s own `except`
around `resolve_units`; `tests/test_cli.py:6692`'s set-equality assertion is at `:6765`;
`registry.py:44`, `envelope.py:51/:208` and `artifacts.py:855` all point at rewritten code. **Cite by
name.**

---

## 15. What is NOT in H7b Part B

| Out | Owner |
|---|---|
| `Apparatus`, probe execution, the ledger, per-condition facts, the change gate, and `cli.py`'s hardcoded `"apparatus": None` | **H7d.** Part B files the false-record consequence and stops |
| `io.reuse_from` and `lineage.py` | **Unowned**, filed. Blocks E3/E4/E6 independently (§ 8) |
| `E-DATA-WEIGHT-CONTRAST` | **H4b.** Blocks C1/C2/C3 (§ 8) |
| `statistics.null_test` | **H4d.** The **other** `_check_unimplemented` entry — retiring one must not retire the loop, and § The one config file's count goes to one rather than to zero |
| Loading an installed **template**'s class; `E-TEMPLATE-INSTALLED-UNSUPPORTED`; `template_provenance` | **Unassigned**, filed. Part B amends the entry (§ 11) rather than closing it |
| `PROBES`'s reader | **H7d** |
| Closing `main`'s un-redacted stderr handler in general | **Unowned**, filed OPEN by H7c. Part B owes only that it does not *widen* the exposure — task 32, a different thing from closing it |
| `publishable list-templates` | Stays `NOT BUILT`, though reachable since Part A (§ 9) |
| `BaseReport` / `generate report` | H8 |
| `hash_index`'s **table** half | Nominally nobody's; **task 31 takes it**, because the resolver half cannot be built without it (§ 7) |
| Anything extending `HASHED_TREES` | Never. A plugin is pinned by `uv.lock`, not by `code_hash` |
