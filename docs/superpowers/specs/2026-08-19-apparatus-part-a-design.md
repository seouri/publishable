# H7d Part A — the apparatus: observe and record — design

**Goal:** a run whose template declares an `apparatus_probe` stops writing a false
`apparatus: null`. Core resolves the declared probe through the same three-step dispatch a
resolver already uses, calls it, projects its facts onto the declared key set, refuses a fact
value that is a credential core read, records every observation in an append-only ledger, and
assembles `provenance.apparatus`'s five sub-keys from what it observed. Nothing here compares
two observations, and nothing here can stop a run that is already executing.

**What it delivers, stated honestly. Part A unblocks ZERO configs.** All nine configs in
[the feasibility analysis](../../feasibility-llm-growth-studies.md) earn exactly
`W-DATA-CLUSTER-UNDECLARED` and no error, measured through `validate_config` at `0faa2e3` in
[`H7d-SCOPING.md`](../H7d-SCOPING.md) § 7. **Six with no remaining core-side blocker and three
executable both stay exactly where H4b-1 left them.** This slice retires **no** refusal at all —
it does not narrow one that goes unhit, it mints refusals rather than retiring them — so the only
honest direction it can move a config-level count is *down*: once the projection exists, a probe
that fails to yield a declared key is a **new** error a run can hit.

**The distinction the old charter collapsed, and both halves are true.** *As measured*, the nine
configs need nothing from Part A: an apparatus probe is declared by a **template**, and the
template those measurements substitute is `generic`, which declares none. *As designed*, the
analysis's `publishable-llm` plugin ships `llm_screen` with `apparatus_probe = "llm_deployment"`
and five `apparatus_facts` — and the scoping reproduced end to end what such a run does today: it
validates clean, runs to `status: completed`, exits 0, writes `provenance.apparatus: null`,
creates no `apparatus/` directory, and **never calls the probe**, which would have raised. So the
sentence this slice is worth is *"Part A moves no count and is what makes a run of these designs
honest,"* never *"Part A unblocks configs."*

**What it is not.** Not the change gate — Part B. Not `EXIT_EXTERNAL`'s reader, `status: partial`
for an unreachable apparatus, or the `run_status` contract — Part B. Not `dry-run`, `freeze`,
`diff`, `reproduce`, `resume` — H8/H9. Not `io.reuse_from`, unbuilt and unowned. Not
`BaseTemplate.field_convention`, whose owner is explicitly unassigned and which this slice
deliberately does not adopt. Every one of those is named with its route in
§ Out of scope, with the route.

---

## The measurement this rests on

[`docs/superpowers/H7d-SCOPING.md`](../H7d-SCOPING.md), taken 2026-08-19 against `main` at
`0faa2e31456d052ec63d3f58c0d6d872213371dd`, **which supersedes
[`H7-SCOPING.md`](../H7-SCOPING.md)** — measured against `cb96c7d`, before H7a, H7b Parts A and B,
H7c and the whole H4 family, and whose headline claim (*"the apparatus is all of it except two
inert class attributes"*) that scoping falsified against five surfaces that now exist. Verdict
there: **22 tasks against the charter's 14, split 13 / 9** on the observe-and-record /
gate-and-stop seam. Baseline recorded there: `uv run pytest -q` → **2363 passed, 1 skipped, 2
xfailed**, 138 s.

**Two commit pins, deliberately not blurred into one.** Everything inherited from the scoping —
the end-to-end false-`apparatus: null` reproduction, the `_check_probe` probe-raises mutation, the
`batch` two-arm re-measurement, the nine-config re-run with its can-fail control — is pinned to
**`0faa2e3`**. Everything measured while writing this document is pinned to **`27e397e`**, the
commit that merged the scoping, and it is this:

- `EXIT_EXTERNAL = 5` **is defined** in `diagnostics.py`, at `0faa2e3` and at `27e397e` alike, and
  is a free identifier everywhere else across `src/`, `tests/` and the four documents. This
  **contradicts the scoping's executive summary** and is corrected in
  § Corrections against the scoping.
- `E-APPARATUS`, `E-PROBE-FACT` and `W-APPARATUS` are free identifiers across `src/`, `tests/`,
  `reference.md`, `design-principles.md` and `experimental-designs.md`. Can-fail control on the
  same file list: `E-PROBE-UNKNOWN` → `validate.py`, `test_validate.py`, `reference.md`;
  `register_probe` → five files. **The file list was filtered; no sweep's output was.**
- `Apparatus` appears in `docs/` only — not in `src/`, not in `tests/`.
- `coercion._SCALARS` is `(bool, int, float, str)` and `_coerce_one` passes `None` through
  untouched, refusing anything with `__len__` under `E-STEP-RETURN-TYPE`.
- `runner.execute_plan` already takes `credentials: dict[str, str] | None`, and
  `cli.command_run` binds it from `credential_values(declared_credential_names(...))` **before**
  the roster call, deliberately, so a raise carrying a credential meets a redacting collector.

**No production code ships from this document.** Every build claim above is perishable in the way
`CLAUDE.md` says a build fact is.

---

## The decision that comes first, because it changes the document before the code

`reference.md` § The apparatus core can only observe sites three checks — *every key in
`apparatus_facts` came back*, *no returned value matches a credential*, and *a declared fact came
back `null`* — at **`dry-run`**, in one sentence, and `dry-run` **does not exist in this build**
(measured: `uv run publishable dry-run` prints *"specified but not built in this version"*). The
same section runs the probe **at run start and before every execution**, which are Part A's.

Taken literally, Part A ships a slice that calls user code once per execution with **nothing
checking that a declared key came back**, the enforcing check parked behind a command nobody has
built. That is not a defensible slice, and `CLAUDE.md` is unambiguous about the remedy: **the
document changes first**, and the gap is recorded rather than diverged from silently. So:

**Ruling (Decision 1).** The projection, the credential check and the null accounting are
**phase-independent functions in `apparatus.py`, invoked by every caller that runs a probe** —
`dry-run`, run start, before each execution, `freeze` — and `reference.md` says so before any code
emits against it. **No new command is invented**, and no check moves *off* `dry-run`: `dry-run`
keeps all three, because it also runs a probe. What changes is that `dry-run` stops being *where
they live* and becomes *one of the places they run*.

**Two sentences in `reference.md` carry the wrong siting and both must move**, because a sweep
that stops at the first is this repo's own named habit:

1. § The apparatus core can only observe: *"…so `dry-run` is where it runs, where core checks that
   every key in `apparatus_facts` came back and that no returned value matches a credential, and
   where it warns for a declared fact that came back `null`."* The split it is drawing —
   `validate` answers what needs no call, everything about what a probe *yields* takes calling it
   — is correct and survives; what must change is the second clause, which reads as *the only*
   place a yield is checked. It becomes: everything about what a probe yields takes calling it, so
   those checks run **wherever a probe runs**, `dry-run` being the first and cheapest of them.
2. § The apparatus core can only observe, the paragraph beginning *"That is also the whole of what
   declaring a fact buys"*: *"What the declaration adds is a **warning at `dry-run`** when the fact
   comes back `null`."* Same widening — the warning is a function of the observations, and a run
   makes observations `dry-run` never saw.

`experimental-designs.md` § Mistakes core prevents carries the same `dry-run` siting in its
apparatus row (*"`dry-run` warns instead of the run failing"*) and moves with them; that is the
third file the sweep must reach, and § The consistency sweep below names all of them.

**What it costs if this ruling is wrong.** If the checks genuinely belonged at `dry-run` alone,
this design makes core do work twice — once at `dry-run`, once per probe thereafter — for a probe
whose answer is already in hand. That cost is a function call over a mapping core just built, and
it buys the property that no reachable path calls user code unchecked. The reverse error is a run
recording facts nobody projected.

---

## Decisions

Every decision below states its grounds and what it costs if wrong. Where a decision contradicts
the scoping, it says so and shows the measurement.

### 1. Where the three checks live — ruled above

**Phase-independent functions in `apparatus.py`, invoked wherever a probe runs; `reference.md`
changes first, in the two sentences named, plus `experimental-designs.md`'s row.** Grounds and
cost are in the section above. It is task 1 and it precedes every code task, so no code emits
against a sentence the repo has not yet corrected.

### 2. Which `cfg` a probe receives, and how many probes run at run start

**Ruling: a probe receives `runner.resolve_condition_cfg(doc, condition)` — this condition's
config, the same object a `condition`-scoped step receives — and never
`runner.resolve_wide_cfg`. Consequently, "the probe at run start" is one call per resolved
condition, not one call per run.**

**Grounds, three, none of which is the charter.** § The apparatus core can only observe states
that unlike a resolver a probe *may* read parameters the sweep varies **and usually must**, since
a sweep over `llm.model` or `instrument.model` is a sweep across apparatus. `resolve_wide_cfg`
plants a `SweptAway` marker on every swept leaf that raises `E-STEP-SWEPT-PARAM` on read, so
handing a probe the wide cfg would refuse precisely the read the document says is the normal case.
Second, that same section makes facts **recorded per condition** and the gate **per condition** —
*"a deployment is compared against its own first observation, never against another condition's"*
— and a mapping keyed by condition cannot be filled by a call that belonged to no condition.
Third, the record shape agrees from two independent sites: § The apparatus files' ledger line
carries `"condition": "00_baseline"` on a `"phase": "run_start"` record, and § The apparatus core
can only observe's `provenance.apparatus.facts` is keyed by condition label. Two sites rather than
one is what makes this a reading of the specification rather than of an example.

**What is handed over, exactly.** The signature is `probe(cfg) -> Apparatus`, which
§ The importable surface already fixes — **no `io`**. A resolver takes `resolve(io, cfg)` and gets
a `ResolverIO` over `input_dir`; a probe takes neither. So a probe cannot read the input directory,
cannot see the run directory, cannot see the unit roster, and cannot write an artifact. What it
*can* reach is one `Config` root: dot-access with no methods, `E-STEP-PARAM-UNKNOWN` on a path the
config does not hold, `AttributeError` on an underscore-prefixed name, and the root node's single
`raw` accessor — reachable because it is the root node and core neither adds nor removes an
accessor for this caller. **State it rather than leave it**: a probe reading `cfg.raw` sees the
whole config document including `data.input_dir`, exactly as a template's `validate(config)` does,
and that is the existing cost of the one exception rather than a new one this slice creates.

**The vacuity the scoping named, and the pin that replaces it.** Under this ruling the test
"a probe may read a swept parameter" is **vacuous as a raise test** — there is no `SweptAway`
marker present to fail to raise. The non-vacuous pin is a **two-condition** fixture whose probe
returns the swept leaf it read: the assertion is that the two conditions' recorded facts **differ
and equal the two swept values**. Its mutation is in § The mutations.

**Cost if wrong.** If a probe were meant to see the wide cfg, this design pays N_conditions probe
calls at run start where one would do — real money on somebody else's quota — and records a
per-condition mapping whose entries are identical. That is the recoverable direction. The
unrecoverable one is the reverse: a single wide-cfg probe cannot answer for a sweep across
apparatus at all, and the facts it recorded would be attributed to conditions it never saw.

### 3. Which executions are probed — every one of them, and under which cfg

**Ruling: a probe runs before **every** execution, with no narrowing. An execution that belongs to
a condition is probed once, under that condition's cfg. An execution that belongs to **no**
condition — `run` or `summary` scope — is probed **once per resolved condition**, under each
condition's own cfg. `reference.md`'s "before every execution" stands unamended.**

**Grounds, and this reverses an earlier draft of this decision.** *"Before every execution"* is
stated at **two** sites, and the second is argument-bearing rather than illustrative: § One
execution at a time gives it as one of the four guarantees that make serial execution non-optional
— *"The apparatus gate probes before every execution and fails the run on a change, which needs a
defined 'before'"* — alongside `batch` being a position in time and `order: randomized`
decorrelating position from condition. A design asking that sentence to become *less* true is
trading an invariant for a call count, which is the wrong direction. And the window matters most
exactly where a narrowing would open it: a `summary`-scoped execution runs **after** every
condition-bearing execution, so under any narrowing the most recent observation preceding it can be
hours old on the long run that *"before every execution is the only placement that catches a
revision changing during a long run"* was written for.

**Two rejected readings, with their reasons, since both are more economical and both are wrong.**

- **Hand a condition-less execution the wide cfg** (`resolve_wide_cfg`), one call, ledger
  `"condition": null`. This is the cheapest reading and it **breaks the documented normal case**:
  § The apparatus core can only observe says a probe *may* read a swept parameter *and usually
  must*, and a probe that does would meet `E-STEP-SWEPT-PARAM` at every `run`- and `summary`-scoped
  execution. Nearly every design has a `summary` step, so this reading fails almost every real run
  at the last execution in its plan, for a fact core asked it to read.
- **Skip the condition-less execution.** Narrows the normative sentence at both sites above, and
  leaves the `summary` execution — the one furthest in time from any observation — as the single
  uncertified one.

**What it costs, stated rather than discovered.** The call count is
`C + E_c + C × E_none` — the run-start round, one call per condition-bearing execution, and `C`
calls before each condition-less one. For the ordinary shape (one `run` step, one `summary` step)
that is `3C + E_c`, which `dry-run` states before the run is scheduled. Every one of those calls
lands in `facts` under a condition and is comparable by Part B's gate, which is what distinguishes
it from a paid call nothing may read.

**Cost if wrong.** If `C` calls before a condition-less execution proves too expensive for a wide
sweep, the narrowing is available to Part B *with the document change it requires* — the route is
named in § Out of scope. Taking the narrowing here, silently, would be the cheaper mistake made
first.

### 4. `apparatus_facts` projection — three states, and only one of them is an error

**Ruling.** § The apparatus core can only observe already answers this and the code follows it
rather than re-deciding it:

| What happened | The record | Is it an error? |
|---|---|---|
| Declared key, probe returned a value | the value, in `facts[<condition>]` and in the ledger line | no |
| Declared key, probe returned `null` | `null` in both, and the fact's `unobserved` counter advances | no — a warning at run end, Decision 8 |
| Declared key, **absent** from what the probe returned | nothing; the command refuses | **yes** — `E-APPARATUS-FACT-MISSING` |
| **Undeclared** key the probe returned | the value, in `facts[<condition>]` and in the ledger line; **no `unobserved` entry** | no |

The first three are the section's own three states — *"a value, a declared absence, and a key that
isn't there at all… Only the third is an error, because only the third is the plugin and the
template disagreeing about what this probe supplies"* — and they are the same three `Param`
already has, which is why this is a projection rule rather than a new vocabulary. The fourth row
is the section's *"Every fact a probe returns is recorded and gated on these terms, named in
`apparatus_facts` or not"*, and its `unobserved` exclusion is the very next sentence: *"What the
declaration adds is a warning… and an `unobserved` count in the record."* **So `unobserved` is
keyed by declared facts only**, and a run whose template declares no `apparatus_facts` records
`unobserved: {}` while still recording every fact the probe returned.

This is the same projection rule as `data.units.attributes` with one deliberate difference, stated
so nobody "fixes" it: a resolver's undeclared attribute is **dropped**, a probe's undeclared fact
is **kept**. The reason is in the section — a probe would not return a fact if it did not describe
the apparatus — and the reason a roster drops one is that a unit table's columns are the config's
declared shape. Two projections, two directions, both documented.

**This closes `apparatus_facts`'s filing.** `spec-defects.md`'s *`BaseTemplate.field_convention`
is declarable and read by nothing* entry names `apparatus_facts` as the second member of that
family; this task gives it its first reader. **`field_convention` stays open and unassigned** and
this slice does not adopt it — see § Out of scope.

**Cost if wrong.** Refusing an undeclared key instead of recording it would make a plugin that
returns one more fact than the template names fail every run, which turns a richer record into a
breakage; recording a missing declared key as `null` would erase the one disagreement the
declaration exists to catch, and Part B's gate would then pin a fact that never existed.

### 5. `Apparatus`'s value contract

**Ruling: `Apparatus` is a frozen construct carrying exactly one field, `facts: Mapping[str, …]`.
Keys must be `str`. Values are the closed scalar set `coercion` already enforces — `bool`, `int`,
`float`, `str`, `None`, plus what core coerces to one — refused under its own code,
`E-APPARATUS-FACT-TYPE`.**

**Grounds.** The ledger is JSON and `provenance.apparatus.hash` is canonical JSON over the facts
mapping, so a value neither can encode is not recordable at all; discovering that at
`json.dumps` is a traceback rather than a diagnostic, which is the exact failure
`coerce_scalars`'s own docstring says it exists to prevent for `yaml.safe_dump`. `None` is already
a pass-through in `_coerce_one`, which is the null semantics of Decision 4 for free rather than by
coincidence. **Its own code rather than `E-STEP-RETURN-TYPE`**: that identifier is a step's,
reached from a step's return, and a reader holding it is sent to § Steps and artifacts, which
describes a different fault at a different time — the identical substitution `E-RESOLVER-SWEPT-PARAM`
already makes for `E-STEP-SWEPT-PARAM`, and the precedent is cited rather than re-argued. Sharing
the *mechanism* — one scalar walk — is not sharing the *fault*.

**Ordering, and it is a leak if reversed: the credential check of Decision 6 runs *before* this
scalar walk, and this walk's refusal message names the value's **type** and never the value.**
A probe returning a credential as a plain `str` passes the scalar walk and must reach the
credential check; a probe returning an object whose `__str__` or `__repr__` carries a credential
must not have that text interpolated into a refusal. `coercion._refuse` already interpolates
`type(value).__name__` rather than the value, which is the shape to copy rather than re-derive —
and copying it is the difference between two instances of this leak class and three.

`facts` is the only field. § The importable surface's row says *"What a probe returns: `facts`"*,
and a second field would be a surface no document describes.

**Cost if wrong.** A permissive contract puts a `dict` or a NumPy array into a fact value, and the
first thing it breaks is the hash — silently, if the encoder happens to accept it, which is worse
than a refusal because two runs would then disagree on a digest for reasons no reader can see.

### 6. The credential check on returned facts — a refusal, not a redaction

**Ruling: a fact value equal to a credential value core read for a *declared* variable **fails the
command** under `E-APPARATUS-FACT-CREDENTIAL`. It is not redacted, not warned about, and not
recorded.**

**Grounds.** § The apparatus core can only observe makes non-secret, non-identifying facts *"a rule
rather than a convention"*, and the property it buys is that `provenance.apparatus` is
**publishable as-is** and [`study add`](../../reference.md) *"has nothing to redact from it."* A
redaction would leave `<redacted:INSTRUMENT_API_TOKEN>` sitting in a block whose whole contract is
that it needs no redaction — and it would be *recorded*, i.e. the block would carry evidence of a
credential having been there. Refusing is the only outcome consistent with the sentence. The match
is by **exact value, never by pattern**, on H7c's decision 4: core knows what it read out of the
environment, and a pattern check fails open on a credential named `instrument_pw` and fails closed
on a config value that happens to look random.

**Two mechanisms, not one, and the second is the leak.** The check above protects the **record**.
The **ledger and the terminal** are protected by a different thing: a probe is user code that runs
at least once per condition-bearing execution, so a probe that *raises* can carry a credential in
its message. **This exact class of leak has now been found twice** — H7c sited its redaction by
grepping for one spelling of an exception interpolation and missed a site formatting a bare
`{exc}`, through which a declared credential reached stderr; H7b Part A left `command_run`'s
credential set computed *after* `resolve_units`, so a resolver's raise reached `main`'s
un-redacted printer, and Part B closed it. **Part A must not make it three.** So: a probe's raise
is caught and turned into a redacted diagnostic through a fresh `Collector` whose `credentials` is
the mapping `command_run` **already binds before the roster call** — reused, never recomputed, on
the grounds that a second derivation is a second answer. `except BaseException`, so a probe calling
`sys.exit()` is covered; `KeyboardInterrupt` re-raised **fresh and argument-less, `from None`**, so
Ctrl-C still stops the command and a `KeyboardInterrupt("…secret…")` a probe body constructed never
reaches Python's own printer. Every clause of that is H7b Part B's shipped resolver path, cited
rather than re-derived, and the code is `E-APPARATUS-RAISED`, the sibling of `E-RESOLVER-RAISED`.

**Which values are checked.** Exactly `credential_values(declared_credential_names(doc, template,
conditions))` — the same set `redact` answers from and the same set `validate` checks for presence.
Deliberately the same set: that is what makes this a fact rather than a guess, and a value a probe
read from `os.environ` for a name nothing declared is outside what core saw and is not matched,
identically to § Secrets & credentials' existing statement of that limit.

**Cost if wrong.** Redacting instead of refusing publishes a block whose contract says it needs no
redaction. Checking by pattern instead of by value fails open on the credential that matters.

### 7. Null semantics, and what `provenance.apparatus` holds in each state

**Ruling, applying `reference.md`'s existing absent-versus-`null` convention rather than minting
one.** The convention — absent means *nothing was asked for*, `null` means *attempted and came
back empty* — is § Statistical reporting's for `resample` and § Contrasts' for `n_paired`, and it
transfers without amendment:

| State | `provenance.apparatus` |
|---|---|
| Template declares no `apparatus_probe` | **`null`** — the whole block. § The apparatus core can only observe defines exactly this: *"An experiment whose measurements never leave the machine declares nothing and records `apparatus: null`"* |
| A probe is declared and every call answered | the five sub-keys, `facts` per condition, `unobserved` per declared fact |
| A probe is declared and returned `Apparatus(facts={})` with no `apparatus_facts` declared | the five sub-keys, with `facts: {<condition>: {}}` per condition and `unobserved: {}` — **attempted and empty**, which is the `null` half of the convention expressed at the level the record has |
| A probe is declared and omitted a declared key | no `run.yaml` at all: the command refuses under `E-APPARATUS-FACT-MISSING` |
| A probe raised | no `run.yaml` at all in Part A: a redacted diagnostic and a non-zero exit, Decision 6. **Part B replaces this with `status: partial` and exit `5`** |

**`probe: null` is never written, and the scoping's task 10 phrasing is wrong.** It says *"`probe:
null` staying the honest record for a template declaring none."* The document's own words make the
**whole block** `null` in that case, and a block present with `probe: null` beside four other
`null`s would be a *different* record — one that says "a probe was asked for and did not name
itself." Reproducing the false-record defect in a new spelling is exactly the failure this slice
exists to close. Corrected in § Corrections against the scoping.

**Cost if wrong.** Writing the block for a run with no probe makes `apparatus: null` mean two
things at once, and every downstream reader — `diff`'s apparatus row, `report study.yaml`'s
cross-check, `reproduce`'s `apparatus.expected.json` — has to distinguish them without a rule.

### 8. The null warning: one channel, and it fires from the counts

**Ruling: a declared fact that came back `null` produces `W-APPARATUS-UNANSWERED`, one finding per
(condition, fact), emitted **once at run end** from `provenance.apparatus.unobserved`, printed to
stdout through a `Collector`. Never one per probe call.**

**Grounds, and this is the sub-decision the scoping does not name.** `run.yaml` has no diagnostics
channel — `cli.command_run`'s own comment says so where it prints `aggregate_c.render()` to
stdout for exactly that reason — so the warning has to be terminal output, and the shipped
precedent for a run-time finding that is disclosed rather than corrective is that print. Per call
is wrong for a measured reason: under Decision 3 an N-execution run makes one call per
execution plus one per condition at run start, so a single flaky fact would emit
the same line many times over, which trains a reader to ignore it. The counts are the durable
record and the warning is a **function of them**, which also makes it the one function `dry-run`
(H9) calls unchanged — there it fires once because there is one round of probes, with no special
case anywhere.

**A warning never changes an exit code**, on `W-ENV-UNLOCKED`'s existing precedent.

**Cost if wrong.** Per-call emission floods the terminal on exactly the design the null rule exists
for — a hosted deployment that omits a fingerprint on some calls. Suppressing it entirely loses
the thing § The apparatus core can only observe says declaring a fact *buys*.

### 9. The ledger — `apparatus/probes.jsonl`

**Ruling: one line appended per probe call, at the call, **before** the execution it precedes runs.
The line's keys are exactly § The apparatus files' five: `at`, `phase`, `condition`, `probe`,
`facts` — nulls included, undeclared facts included. `phase` is a closed vocabulary of four —
`run_start`, `pre_execution`, `dry_run`, `freeze` — of which Part A emits the first two.
`condition` is the condition **label**. `at` is UTC, in the same `%Y-%m-%dT%H:%M:%SZ` spelling
`executions.jsonl` already writes.**

**Grounds.** The shape is the document's, taken from the example **and** confirmed against a
second site — `provenance.apparatus.facts` is keyed by condition label in § The apparatus core can
only observe — so this is not a row's example being read as its definition. The four phases are
the four places § The apparatus files says a probe writes (*"at `dry-run`, at run start, before
each execution, and at `freeze`"*); naming all four here and emitting two keeps H8's and H9's
callers from minting a fifth spelling of a phase Part A already has a name for. Appending
**before** the execution rather than after is what makes *"the ledger keeps both observations so
the evaluable earlier period is still reportable"* true of a run that dies inside an execution:
the observation the run executed *under* is on disk regardless of how the execution ended.

**One inconsistency, named rather than smoothed.** `executions.jsonl` writes `condition` as an
**index**; this ledger writes it as a **label**. Both are the record their own document specifies,
and the label is what `facts` is keyed by, so a reader joining the two files joins on
`sweep.yaml`'s index↔label mapping. Recorded here so nobody "harmonizes" one to the other and
breaks the join with `facts`.

**What "the ledger keeps both observations" means under Part A**, since a probe runs at run start
*and* before every execution: the file simply holds every call in order, so one condition
contributes one `run_start` line, one `pre_execution` line per condition-bearing execution, and
one more per condition-less execution.
Part A never removes or rewrites a line — it is append-only in the same sense `executions.jsonl`
is. Part B is what makes that property *load-bearing*, because it is the slice that can stop a run
between two lines.

**Where the run-start round sits in `command_run`'s phases, and why it is not earlier.** After the
run directory is allocated and inside its lock, after `sweep.yaml` and `allocation.json` are
written, before the first execution. The ledger is a **run artifact**, so it has nowhere to go
before the directory exists — and the ordering is the same cost ordering § Exit codes and
diagnostics states for `dry-run`, where *"the cheap objection should never be reported second,
behind a metered request that was going to fail anyway."* Everything before this point is free:
validation, the manifest, the roster, the plan, the two partition files. Stated explicitly because
a plan author reading "fail fast" will otherwise move the probe ahead of the run directory and
leave the ledger with no home.

**Cost if wrong.** Appending after the execution loses the observation for exactly the run that
died, which is the run the ledger exists for.

### 10. `provenance.apparatus.hash` — what it covers, and where it lives

**Ruling: sha256 over canonical JSON (`sort_keys=True`, `separators=(",", ":")`,
`ensure_ascii=False`) of the resolved **condition → facts** mapping — that is, of
`provenance.apparatus.facts` exactly — `sha256:`-prefixed, computed by a function in
`apparatus.py` beside the builder of that mapping.**

**Grounds, and the invariant it must not break.** `CLAUDE.md` § Invariants: **three hashes, split
on purpose**, and `H7-SCOPING.md` records that the apparatus is explicitly *not a fourth hash*.
§ The apparatus core can only observe says the same in its own words: it *"sits beside
`uv_lock_hash` as an environment fingerprint: something `diff` compares and a reader checks,
rather than one of the three identity claims."* Two mechanical consequences follow and both are
part of the ruling: **`HASHED_TREES` is not touched**, and the function does **not** go in
`hashes.py`. It goes in `apparatus.py`, on `manifest_hash`'s and `allocation_hash`'s shipped
placement — `allocation_hash`'s own docstring argues that `hashes.py` holds hashes over things the
caller already had lying around, while a hash over a document *this module just built* belongs
beside the construction, *"so the construction and the hash of what it constructs stay one property
of one artifact rather than two modules that have to agree on a shape from a distance."* **That
placement is itself the argument that this is not a fourth hash**, which is why it is a decision
rather than a filing detail.

**Carry `allocation_hash`'s document-versus-file-bytes warning verbatim in kind:** the hash is over
the *mapping*, not over any file's bytes. `run.yaml` renders the same mapping through
`yaml.safe_dump` and the ledger renders individual observations through `json.dumps`; neither
encoding hashes to this digest, and a reader reproducing it by hand must re-canonicalize the
parsed `facts` mapping.

**What it does not cover:** the ledger, the probe name, the phase, the timestamps, and
`unobserved`. It covers the facts and only the facts, because the question it answers is *"did two
runs measure through the same apparatus"* — a run that probed more times is not a different
apparatus.

**Cost if wrong.** Folding it into `hashes.py` or into `HASHED_TREES` converts an environment
fingerprint into an identity claim, and "same code, different parameters" stops being provable the
moment a deployment answers a fact unevenly.

### 11. Probe dispatch reuses `E-PROBE-UNKNOWN` rather than minting a sibling

**Ruling: `apparatus._probe_for(name)` is `units._resolver_for`'s sibling — `scan_group` →
`load_entry_point` → `check_registration` over `declared_names` — and the three codes it can raise
are `E-PROBE-UNKNOWN`, `E-PLUGIN-LOAD` and `E-PLUGIN-DECORATOR`. `E-PROBE-UNKNOWN` becomes
**dual-surface**, reported by `validate` and raised at dispatch, and its § Errors row says so.**

**Grounds.** The scoping measured **two sources of truth for "is this probe registered"** and
required them reconciled: a probe registered in-process by `@register_probe` with no entry point is
in `PROBES` and invisible to `_check_probe`; one with an entry point and no decorator resolves at
`validate` and is absent from `PROBES` until loaded. H7b Part B settled that exact shape for
resolvers with those three functions, all built and all with production callers, so this is a
sibling rather than a new mechanism. Reusing the code follows the house rule that **§ Errors
carries one row per code, not per emit site** — the same dual-listing `E-RESOLVER-SWEPT-PARAM`,
`E-DATA-CLUSTER-UNKNOWN` and `E-TEMPLATE-COLLISION` already carry, each with the two surfaces
stated in the row.

**This gives `PROBES` its first reader and closes that filing's H7d half.** The filing's stated
reason for being a filing rather than a fix — *"a reader for `PROBES` means executing a probe"* —
is satisfied here, and its `RESOLVERS` half is already closed.

**Cost if wrong.** A second code for one fault splits the § Errors row and sends a reader looking
for the wrong section; a dispatch that reads `PROBES` alone would resolve a decorator-only
registration `validate` refused.

### 12. Part A refuses; it does not truncate

**Ruling: nothing in Part A stops a run that is executing. A probe that raises, omits a declared
key, returns a credential, or returns an unencodable value ends the **command** before or between
executions, through a redacted diagnostic and a non-zero exit — never by truncating a plan and
never by writing a `status`.**

**Grounds, and the sentence must exist because a Part B author will read Part A as having settled
it.** The scoping promises Part A "stops no run"; `reference.md` says an unreachable apparatus
produces `status: partial` plus exit `5`. Both are true of different slices, and the seam is
this: **Part A has no gate, so it has no truncation**, and its failures are command-level refusals
that leave the run directory with its ledger and no `run.yaml` — the same shape a crash before
`run.yaml` already produces today. **Part B replaces that outcome** for the unreachable case with
`status: partial`, exit `5`, and the `run_status` contract change the scoping measured is missing.
Part A must therefore not assert anywhere — comment, docstring or test name — that an unreachable
probe *cannot* stop a run mid-plan; it asserts only that Part A does not make it do so.

**Cost if wrong.** A Part A that quietly truncates on a probe failure ships Part B's hardest
decision unreviewed, in the slice whose review was scoped for a different risk.

### 13. `validate` calls no probe, and the pin moves into Part A

**Ruling: the test asserting that no `validate` path calls a probe — the old charter's task 3,
still owed — ships in **Part A**, not Part B.**

**Grounds.** Before Part A there is no call site, so the guard is a claim about code that does not
exist; after Part A there are call sites in `command_run`, and the guard is exactly what keeps
`validate` inside *"may read your config and your input, and may not reach anything outside the
machine."* Leaving it in Part B means the first slice that can violate the rule ships without the
pin. The scoping's own measurement makes the shape available: a probe that **writes a flag file and
then raises**, so a call cannot be silent, with the assertion on the flag's absence *and* on the
findings list being the expected set — a control asserting only an absence passes identically if
nothing ran.

**Cost if wrong.** `validate` is the command you run in a loop while editing YAML; an accidental
probe call there is metered money per keystroke.

### 14. Decline the old charter's tasks 12 and 13

**Ruling: Part A ships **no** `resume`/`dry-run`/`freeze` hooks "as callables with tests." The
calling slice builds its own call site against `apparatus.py`'s public functions.**

**Grounds, strengthened by a measurement this document made.** The scoping recommends declining
because this repo has filed the shipped-but-unread family three times in four commits — `PROBES`,
`load_entry_point`, `declared_names`, `template_provenance` — and manufacturing three more
callables with no production caller is that filing again by choice. **The family is larger than
the scoping knew:** `EXIT_EXTERNAL = 5` ships in `diagnostics.py` and is read by nothing, at
`0faa2e3` and at `27e397e` alike (§ Corrections against the scoping), and `field_convention` is a
fifth member with no owner. Adding three more deliberately is not a defensible slice.

**What Part A gives those slices instead**: `apparatus.py`'s functions are public, phase-independent
and take a `phase` argument whose vocabulary already names all four (Decision 9). H9's `dry-run`
calls them with `phase="dry_run"`; H8's `freeze` with `phase="freeze"`. Nothing is stubbed, and
nothing ships unread.

**Cost if wrong.** If those slices need a shape Part A did not anticipate, they change
`apparatus.py` — which is cheaper than three unread callables aging against a design that moved.

---

## Out of scope, with the route

Named the way the H4 designs name theirs: every exclusion carries where it goes.

| Excluded | Route |
|---|---|
| The per-condition, per-fact change gate against the first *answered* observation; `value → value` fails, `null → value` and `value → null` do not | **Part B**, tasks 14–15. Its fixture must separate all three transitions; a two-observation fixture cannot |
| Run-stops-here placement, on `max_failed_fraction`'s existing `break` | **Part B**, task 16 |
| `run_status`'s contract — nothing downstream of `execute_plan` compares `len(results)` against the plan, so a truncated all-completed plan records `completed` | **Part B**, task 17. Measured in the scoping § 0.4; Part A creates no truncation, so it neither fixes nor worsens it |
| `EXIT_EXTERNAL`'s **reader** and the documented precedence (5 wins over 3 and 4) | **Part B**, task 18 — **narrower than the scoping states**: the constant already ships. See § Corrections against the scoping |
| The unreachable-probe path distinguished from the moved-fact path (`partial` + 5 versus a failed run) | **Part B**, task 19 |
| The ledger keeping both observations *across a gate failure*, asserted on the file | **Part B**, task 20. Part A ships the append-only file; Part B ships the property that survives a stop |
| The test asserting `batch` and the apparatus stay independent | **Part B**, task 21. The scoping re-measured the `batch` wire by running both arms: it reads **step declarations**, discriminates, and H7d owes it no change |
| `dry-run`'s probe phase and its cost-ordered exit codes; `resume`'s refusal of a changed apparatus; `reproduce`'s `apparatus.expected.json`; `demo`, `docs` | **H9**, per the spine design § The hardening slices. All unbuilt — every claim this document makes about them is a **spec claim**, read, never a build fact |
| `freeze`'s re-probe; `diff`'s `apparatus DIFFERS` row; `report study.yaml` cross-checking `provenance.apparatus.hash` | **H8**, same section, same unbuilt status |
| **Narrowing** the per-execution probe — skipping a `run`- or `summary`-scoped execution, or giving it one wide-cfg call | **Part B**, if `C` calls before a condition-less execution proves too expensive, **and only with the `reference.md` change it requires** — "before every execution" is stated at two sites, one of them argument-bearing. Decision 3 states both rejected readings and their costs |
| `BaseTemplate.field_convention`, declarable on a shipped class and read by nothing | **Unassigned** in `spec-defects.md`, and deliberately not adopted here. Folding it in would make this slice the owner of a gap it did not find, and the entry says the family is both members |
| `io.reuse_from`, which is what keeps six configs non-executable | **Unassigned**, not apparatus |
| Holdouts and folds inside cells | **H3c-3** |
| An interaction, a dose-response ordering, a difference-in-differences | **Permanent refusal.** Contrasts do not nest; the route is a `summary`-step `Estimate` |
| Core inspecting a probe's body to decide whether it reaches the network | **Permanent refusal.** Core validates declarations and verifies effects; it never inspects the body of user Python |
| A policy knob permitting a changed fact | **Permanent refusal**, stated in § The apparatus core can only observe. Part B task 15 is the test that nothing under `limits` can permit one |

---

## Cost and risk — what a metered probe does and does not constrain

**A probe is user code; core only ever needs a fake.** Quota constrains **placement, not
testability**, and every check in this design is pinnable with a fixture that never leaves the
machine: the projection, the credential refusal, the null accounting, the ledger, the hash, the
publishable-as-is property, and the `validate`-calls-no-probe guard. The scoping's harness already
registers a real installed distribution whose probe writes a flag and raises, which is the
strongest fixture shape the slice needs.

What quota *does* constrain, as three rules rather than a caveat:

1. **`validate` must never call one** — Decision 13 is the pin, and it ships here rather than in
   Part B.
2. **The call count is a number `dry-run` must be able to state before the run is scheduled.**
   Under Decisions 2 and 3 it is `C + E_c + C × E_none`, where `C` is the resolved condition
   count, `E_c` the number of condition-bearing executions and `E_none` the number of `run`- and
   `summary`-scoped ones. That formula is part of Part A's contract because
   H9 prints it, and § The discriminating fixtures pins it with a fixture that separates all four
   candidate readings.
3. **A failed observation must not retry** — a retry is another paid call against an apparatus
   already known to be in trouble. Part A retries nothing; Part B inherits the rule for the gate.

The one thing a fixture cannot stand in for is the behaviour the null rule exists for — a hosted
deployment that returns a fingerprint on most calls and omits it on some. That is why `null` is a
legal value, and it is also why an integration test against a real deployment would be a **worse**
pin than the fixture: it would pass or fail for reasons the code does not control.

---

## The discriminating fixtures, stated here so no later task can weaken them

**The constraints first**, because a later task may only substitute fixtures meeting all of them:

- **Every literal is computed, not guessed.** Six fixtures on the immediately preceding slice
  failed their own constraints — one asserting `b = 0` where 66 hits were expected, one asserting
  the very value it existed to reject. So every count below is derived here in writing from the
  design it is testing, and every *derived* value (a hash, a per-condition fact mapping, an
  `unobserved` count) is **recomputed by the test from the ledger it just read**, never
  hard-coded. The only hard-coded numbers are the ledger line counts, derived immediately below.
- **A fixture must separate every candidate reading**, not two of them. Two elements only ever
  distinguish two answers.
- **A control asserting only absences passes identically if nothing ran.** Every control here is
  paired with something that must report.

### Fixture P — the plugin, inherited

The scoping's `h7d_probe.py` shape: a scaffolded project, a **project-local** template declaring
`apparatus_probe` and `apparatus_facts`, and a synthetic **installed** distribution whose
`publishable.probes` entry point names a module whose probe is instrumented. Both halves are load
bearing — a project-local template is what makes the declaration reachable without publishing a
plugin, and an installed distribution is what `_check_probe` and `_probe_for` both answer from.

### Fixture F — the call count, which must separate five readings

**Design:** two conditions (a one-axis `grid` with two levels), one `condition`-scoped step, one
`repeat`-scoped step at one repeat, and one `run`-scoped step. So `C` = 2, `E_c` = 2 + 2 = **4**,
`E_none` = **1**, and **5 executions** in the plan.

| Candidate reading | Ledger lines |
|---|---|
| Once per run | 1 |
| Once per condition, at run start only | 2 |
| Run start per condition, then before every **condition-bearing** execution — the narrowing Decision 3 rejects | 6 |
| Run start per condition, then one **wide-cfg** call before the condition-less execution — the other rejected reading | 7 |
| **This design** — `C + E_c + C × E_none` = 2 + 4 + 2 | **8** |

Five readings, five different answers, from one fixture. A design with no `run`-scoped step
collapses the last three into one number and can distinguish none of them.

### Fixture S — which `cfg`, and why the raise test is not the pin

**Design:** Fixture F's two conditions differ in one swept parameter the probe reads and returns
as a fact. **Assertion:** the two conditions' `provenance.apparatus.facts` entries differ, and each
equals its own condition's swept value — read back from `sweep.yaml` rather than written twice.
**Not** an assertion that no `E-STEP-SWEPT-PARAM` was raised: under Decision 2 no marker is present,
so that assertion is true of a build that hands the probe nothing at all.

### Fixture N — the null accounting, computed from the call log

**Design:** the template declares two facts; the probe answers both for condition `01_…` and
answers only the first for condition `00_…`. Over Fixture F's 8 calls, 4 belong to each condition
— one `run_start`, two `pre_execution` for its own executions, and one before the condition-less
execution. **Assertions, every number recomputed by the test from
the ledger it reads:** `facts["00_…"]` holds the first fact's value and `null` for the second;
`unobserved` carries one entry per **declared** fact, with `total_probes` equal to the ledger's own
line count and `null_probes` equal to the count of lines where that fact was `null`;
`W-APPARATUS-UNANSWERED` appears exactly once for the (condition, fact) pair that went unanswered
and **not** for the answered one — a control that must report, paired with the absence.

**And the condition-less execution's own round**, whose two calls each carry a condition label
like any other and therefore land in `facts` exactly as the rest do — the ledger and `facts`
disagree about nothing under Decision 3, which is one of the things that decision buys.

**And one fact the probe returns that the template does not declare**, asserted present in `facts`
and in every ledger line, and **absent from `unobserved`** — Decision 4's fourth row, which no
other fixture reaches.

### Fixture K — the credential refusal, whose mutation can actually differ

**Design:** a declared credential whose value is **short and ordinary-looking** — the kind a name
heuristic and an entropy heuristic both miss — and a probe that returns it as a fact value.
**Assertion:** the command exits non-zero with `E-APPARATUS-FACT-CREDENTIAL`, no `run.yaml` is
written, and the credential's value appears in **no** byte of the run directory. That last clause
is asserted on the **raw text** of every file written, not on parsed content: a defect that lives
in how a value is written is one a parsing reader undoes before the assertion.

**Why the value must be ordinary-looking:** a random-looking value makes an exact-value check and
a pattern check agree, so the mutation in § The mutations would have two branches that cannot
differ — which this repo has already shipped once as a proposed proof.

### Fixture H — the hash, as a construction

**Never a digest literal.** The test recomputes
`sha256(json.dumps(facts, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())`
from the `facts` mapping it read back out of `run.yaml`, and compares. A second assertion pins the
property the literal would have hidden: two runs of Fixture F whose probe returns identical facts
produce **identical** `hash` values while their `run_id`s, timestamps and ledgers differ; changing
one fact value changes it.

---

## The mutations, each with the assertion that catches it

**A mutation caught by a crash or by a string literal is not a pin.** Each row below names the
assertion, and each mutation's two branches can produce different results.

| Mutation | Caught by |
|---|---|
| Hand every probe call `cfgs[0]` instead of this condition's cfg | Fixture S: the two conditions' facts become equal, failing the differ-and-equal-the-swept-values assertion. (Handing `resolve_wide_cfg` instead would crash, so it is **not** the mutation) |
| Delete the declared-key check from the projection | A Fixture P variant whose probe omits one declared key: the command exits 0 and writes `run.yaml`, failing the assertion that it exits non-zero with `E-APPARATUS-FACT-MISSING` and wrote none |
| Drop an **undeclared** returned fact instead of recording it | Fixture N's undeclared-fact assertion — present in `facts` and in every ledger line |
| Key `unobserved` by every returned fact rather than by declared facts only | Fixture N: the undeclared fact gains an `unobserved` entry, failing the absence assertion paired with its presence assertion |
| Replace exact-value credential matching with any pattern or name heuristic | Fixture K: the ordinary-looking value stops matching, the run completes, and the exit-code/code assertion fails |
| Redact the credential into the record instead of refusing | Fixture K's raw-text assertion over the run directory finds `<redacted:…>` where nothing should exist, and the exit-code assertion fails |
| Skip the condition-less execution | Fixture F: 6 ledger lines against the asserted 8 |
| Hand the condition-less execution one wide-cfg call instead of `C` per-condition ones | Fixture F: 7 lines against 8, and the wide line's `condition` is absent from `facts` |
| Probe once per run instead of once per condition at run start | Fixture F: 6 lines against 8, and Fixture S's per-condition facts collapse |
| Append the ledger line **after** the execution | A Fixture P variant whose step raises: the ledger is short by one line, asserted on the file |
| Emit `W-APPARATUS-UNANSWERED` per call rather than from the counts | Fixture N: the warning appears 3 times for one (condition, fact) pair against the asserted 1 |
| Hash the `run.yaml` bytes, or the whole `apparatus` block, instead of the facts mapping | Fixture H's recomputation, and its two-runs-identical-facts assertion |
| Add a probe call to any `validate` path | Decision 13's flag-file test — the flag exists, and the findings-list control still reports its expected set |
| Write `probe: null` plus four `null`s for a template declaring no probe | The no-probe test's assertion that `provenance["apparatus"] is None` |

---

## Task decomposition — 17

**Documents and constructs — 3**

1. **`reference.md` § The apparatus core can only observe: the check-placement change (Decision 1),
   both sentences, and `experimental-designs.md` § Mistakes core prevents' matching row.**
   **"Before every execution" is not narrowed** — Decision 3 rejects the narrowing an earlier draft
   of this design proposed. First, so no code emits
   against a sentence the repo has not corrected. No new command.
2. **`Apparatus` + export from `publishable`**, its value contract (Decision 5), § The importable
   surface's row `not yet built` → `built`, and § Package layout's `apparatus.py` marker retired.
3. **`apparatus.py`: probe resolution as `_resolver_for`'s sibling** (Decision 11) — `scan_group`
   → `load_entry_point` → `check_registration`/`declared_names`, giving `PROBES` its first reader
   and closing that filing's H7d half.

**Observation — 5**

4. **Probe invocation**: `probe(cfg)` under this condition's cfg (Decision 2), with the raise path
   — `except BaseException`, `KeyboardInterrupt` fresh and `from None`, redacted through the
   collector `command_run` already holds — under `E-APPARATUS-RAISED` (Decision 6, second half).
5. **`apparatus_facts` projection** (Decision 4), phase-independent, giving `apparatus_facts` its
   first reader. `E-APPARATUS-FACT-MISSING`.
6. **The credential check on returned fact values** (Decision 6, first half).
   `E-APPARATUS-FACT-CREDENTIAL`.
7. **Null semantics and the `unobserved` counts** (Decision 7), plus `W-APPARATUS-UNANSWERED`
   emitted from the counts at run end (Decision 8).
8. **`apparatus/probes.jsonl`** (Decision 9), with § Artifact layout's tree row.

**Placement — 2**

9. **The probe at run start**, once per resolved condition, after the run directory is allocated
   and inside its lock so the ledger has somewhere to go.
10. **The probe before every execution** (Decision 3), inside `execute_plan`'s loop, before the
    execution runs — once for a condition-bearing execution, once per condition for a
    condition-less one.

**The record — 3**

11. **`provenance.apparatus`'s five sub-keys** replacing `cli.py`'s unconditional `None`, with the
    whole block staying `null` for a template declaring no probe (Decision 7). **Closes the OPEN
    filing** *a run whose template declares an installed probe records a false `apparatus: null`*.
12. **`provenance.apparatus.hash`** (Decision 10), in `apparatus.py`, not in `hashes.py`, not in
    `HASHED_TREES`.
13. **The publishable-as-is test**: no credential value anywhere in the block, and `study add` has
    nothing to redact from it.

**Guards, rows and filings — 4**

14. **The `validate` calls no probe pin** (Decision 13), by the flag-file-and-raise mutation, with
    a control that must report.
15. **The call-count contract**: Fixture F, pinning `C + E_c + C × E_none` against all five
    readings, because
    H9's `dry-run` must state that number before a run is scheduled.
16. **Every § Errors `validate` reports, § Errors core raises, § Validation and § Artifact layout
    row** for the codes minted here, plus `E-PROBE-UNKNOWN`'s row restated as **dual-surface**. The
    family has **one** code today; that is the documentation debt's whole measured size.
17. **The filings, in `spec-defects.md` itself and not in a ledger line**: strike the false-`apparatus:
    null` entry and the `PROBES` half of its neighbour, **amend** the `field_convention` entry to
    name `field_convention` alone now that `apparatus_facts` has a reader, and **file
    `EXIT_EXTERNAL` as shipped-and-unread with Part B as its owner**. A separate task because *a
    ledger line saying "filed" is not a filing* — a gap recorded as "registered against \<owner\>"
    has already existed only in a ledger here — and because a filing's claims about the code go
    stale, so the two struck entries are re-read against the code this slice changed before they
    are struck.

**Direction against the scoping's 13: +4.** Up: task 1, the check-placement document change split
out and put first, which the scoping identified as owed but folded into its task 4; task 2's value
contract, split from invocation because it is a construct's contract rather than a call site; task
14, **moved in from Part B** (its task 22), because Part A is the slice that creates the call sites
the guard exists for; and task 17, the filings, which the scoping's decomposition names in its
prose and gives no task. Down: nothing. **Part B therefore goes 9 → 8**, and its task 18 is
narrower than stated — see § Corrections against the scoping.

### The ordering constraints, each with its reason

- **1 before everything.** The document changes first; a code task emitting against the un-amended
  sentence would site three checks at a command that does not exist.
- **2 and 3 before 4.** There is nothing to call and no type to return until the construct exists
  and a name resolves.
- **4 before 5, 6, 7.** Each of the three checks takes a returned mapping.
- **5, 6, 7 before 9 and 10.** A call site added before its checks is exactly the slice Decision 1
  refuses to ship, even transiently within the branch.
- **8 before 9 and 10**, since both placements append to it.
- **9 and 10 before 11 and 12**, since the record and the hash are assembled from what was
  observed.
- **14 may land any time after 3** and must not wait for 10 — the guard is about a path that must
  stay callless, not about the paths being built.
- **16 and 17 last**, so every code documented exists and every row is written against emitted
  behaviour rather than against intent, and so the two struck filings are struck against code that
  has landed rather than against an intention to land it.

---

## The traps this slice is most likely to hit

Drawn from `CLAUDE.md` § Misreadings, narrowed to what this design actually touches.

- **Scoping a diagnostic by the helper it calls.** `E-PROBE-UNKNOWN` gains a second emit site in
  task 3. § Errors carries **one row per code, not per emit site**, so its unit of work is every
  site that raises *or* reports it — and a task scoped by `_check_probe`'s single call site will
  miss the dispatch site, which is the exact shape `E-TEMPLATE-UNKNOWN` already failed on.
- **Reading a subprocess probe as a pin.** Five times in three slices a correct fix shipped
  unpinned. Verify each check through the real console script, then pin by a mutation from
  § The mutations, and check the mutation's two branches can differ.
- **Reading a mutation's silence as confirmation.** A mutation that changes nothing is evidence
  about the **tests**. Every mutation in the table names the assertion that catches it; a mutation
  that leaves the suite green means the fixture is missing, not that the code is unreachable.
- **Inferring "this path does not run" from "this config is refused."** `validate` collects rather
  than aborting, so `E-PROBE-UNKNOWN` never makes a later check unreachable. Two independent
  readers already recorded a mutation as blind on that reasoning and a reviewer disproved it.
- **A comment claiming a guarantee the code does not provide.** Decision 12 is the one at risk: no
  comment, docstring or test name in Part A may assert that an unreachable probe *cannot* stop a
  run mid-plan. If a comment says *this cannot happen*, make it happen.
- **Answering a question with a proxy.** "Is this fact value a credential" must be answered by
  equality against the values core read, never by a name pattern or a randomness heuristic —
  Fixture K exists to make the substitution visible.
- **Sweeping for the claim, not the file.** Task 1 touches two documents; task 16 touches four
  document sections. Three sweeps in one recent slice stopped one file short.
- **Locating a table row by position.** § Errors' tables gain rows; name what a sibling row *does*,
  and check every count phrase near an insertion.

---

## The consistency sweep this slice owes

The four documents only; the development record is **exempt** and must not be retro-edited.

- **`reference.md`** — § The apparatus core can only observe (two sentences, Decision 1 —
  and **nothing** in Decision 3, which is the one decision here that leaves the document alone),
  § One execution at a time (**checked, not changed**: its "before every execution" is what
  Decision 3 preserves), § The apparatus files (the phase vocabulary, the ledger's keys), § The importable surface (`Apparatus` → `built`), § Package layout
  (`apparatus.py`'s `— not yet built` marker), § Errors `validate` reports, § Errors core raises,
  § Validation, § Artifact layout (the `apparatus/` directory in the run tree), and § The one
  config file only if a field changes — **it does not**, since every declaration here is a
  template attribute rather than a config field.
- **`experimental-designs.md`** — § Mistakes core prevents' apparatus row.
- **`design-principles.md`** — its `Apparatus` mention in the core-vs-plugin table needs no change;
  checked, not assumed.
- **`README.md`** — no change: the worked example has no apparatus, because `generic` declares no
  probe.
- **Mechanical pass in full** on every file touched: relative links and `#anchor`s resolve, no two
  headings collide, table rows match their header's column count, no trailing whitespace or tabs,
  `×` not `x`, hyphens rather than en dashes in anything becoming an anchor. Fenced blocks skipped.
- **After removing or renaming any string**, grep the four documents, `CLAUDE.md` and the
  feasibility analysis for what should no longer exist — filtering the **file list**, never a
  sweep's output.

`CLAUDE.md` § Misreadings' *unbuilt reader of a shipped surface* row names `apparatus_facts` as
its sole remaining example; task 5 gives it a reader, so that row's example must move to
`field_convention` — which the scoping already showed was true even before this slice, since
`CLAUDE.md`'s "sole" was false at `0faa2e3`.

---

## The filings this slice touches

| Filing | What Part A does |
|---|---|
| *a run whose template declares an installed probe records a false `apparatus: null`* — **Owner H7d** | **Closed** by task 11, and struck in `spec-defects.md`. Its claims about the code were re-verified end to end at `0faa2e3`, so it is closed against a live reproduction rather than against its own text |
| *`PROBES` and `RESOLVERS` are written by their decorators and read by nothing* — `PROBES` half **Owner H7d** | **Closed** by task 3. Its stated reason for being a filing — *"a reader for `PROBES` means executing a probe"* — is exactly what this slice ships |
| *`BaseTemplate.field_convention` is declarable and read by nothing* — **unassigned** | **Untouched and still unassigned.** Its `apparatus_facts` member is closed by task 5, so the entry must be **amended** to name `field_convention` alone — the amendment H7c's entry already models |
| *two specified readers of `required_env` belong to unbuilt commands* | Not H7d's; named so it is not folded in |
| *`io.reuse_from` is unbuilt and unowned* | Not apparatus; named because it is what keeps six configs non-executable, and no sentence here may imply otherwise |

**No apparatus filing points at a closed slice for unbuilt work** — the scoping swept for the
re-ownering problem H4d hit and this family passed. **A new one is owed**, and **task 17 writes it**: `EXIT_EXTERNAL` is shipped and unread, with Part
B as its owner. Part A does not create that gap — it measured it — and a correction in this
document is not a filing.

---

## The payoff, stated so it cannot be rounded

### Measured on 2026-08-19 against commit `0faa2e3`

**Part A unblocks ZERO configs.** All nine configs in
[the feasibility analysis](../../feasibility-llm-growth-studies.md) return exactly
`['W-DATA-CLUSTER-UNDECLARED']` through `validate_config`, with the can-fail control
(`holdout.frac → 0` ⇒ `E-DATA-HOLDOUT-FRAC`) firing. **Six with no remaining core-side blocker;
three executable. Neither moves.** Part A retires no refusal — it mints four codes
(`E-APPARATUS-FACT-MISSING`, `E-APPARATUS-FACT-CREDENTIAL`, `E-APPARATUS-FACT-TYPE`,
`E-APPARATUS-RAISED`) and one warning
— and the only direction it can move a config-level count is down, once a probe that omits a
declared key becomes a reachable error.

**A closed filing is not an executable-run count**, and no sentence this slice writes may put the
two in one breath.

**What Part A is worth instead**, stated so it is not mistaken for nothing:

- **A run's record stops lying.** Today a template declaring an installed, resolvable probe
  validates clean, exits 0, and writes `provenance.apparatus: null` — which
  `reference.md` defines as *"no probe declared"* — with the probe never called. That is a
  publishable-looking record with nothing pinning the server, reproduced end to end rather than
  inferred from an emit site.
- **The `uv.lock`-pins-the-client / nothing-pins-the-server gap closes on the observe half.**
  `design-principles.md`'s first design goal claims code, environment, data **and apparatus** are
  all pinned; the fourth becomes true of what a run records here, and true of what a run *refuses*
  in Part B.
- **Two shipped-but-unread surfaces gain readers** — `PROBES` and `apparatus_facts` — which is two
  of the five members of the family this repo has filed three times.
- **`apparatus/probes.jsonl` and `provenance.apparatus` become producible**, which is what H8's
  `diff` row, H8's `report study.yaml` cross-check and H9's `reproduce` expectation file are all
  written against.

**Nothing in the feasibility analysis gets closer to running because Part A lands.** What changes
is that a run of the designs it describes would, for the first time, record what it measured
through.

**Task count is 17.**

---

## What the scoping left unmeasured, and this design had to assume

Every item here is a **reading of `reference.md`**, not a build fact, and each is where this design
is most likely to be wrong.

1. **That the run-start round is one probe per condition.** § The apparatus files' ledger example
   carries a `condition` on a `run_start` line and § The apparatus core can only observe keys
   `facts` by condition — two sites, but neither states the call count. Decision 2 reads it off
   them.
2. **Which `cfg` a condition-less execution's probe receives.** *"Before every execution"* is
   stated at two sites and neither says what a `run`- or `summary`-scoped execution probes under.
   Decision 3 rules it **toward the document** — one call per condition, under each condition's own
   cfg — rather than narrowing the sentence, and names the two cheaper readings it rejects. This is
   the assumption in this list most worth re-measuring, because it is the one that costs money.
3. **The null warning's channel and frequency at run time.** The document sites the warning at
   `dry-run` and says nothing about a run, because under the un-amended text a run never checks.
   Decision 8 rules it.
4. **Whether `probe: null` or a `null` block is the record for a template declaring none.** The
   scoping says the first; the document says the second. Decision 7 takes the document and corrects
   the scoping.
5. **Whether `Apparatus` accepts a non-scalar fact value.** No document sentence constrains it.
   Decision 5 rules it from what the ledger and the hash can encode.
6. **Whether the ledger's `condition` is a label or an index.** Only the example says, and it says
   label; `facts`'s keying agrees. Decision 9 takes it and records the resulting inconsistency with
   `executions.jsonl`.
7. **Everything about `dry-run`, `freeze`, `diff`, `reproduce`, `resume`.** All five print
   *specified but not built*. Every claim here about where their checks live is a spec claim.
8. **The nine configs' actual plugin.** `publishable-llm`, `llm_screen` and `llm_deployment` are
   designs in the feasibility analysis, not code; Fixture P is a documented substitution for them,
   the same substitution every § Executability entry has used since 2026-08-16.

---

## Corrections against the scoping

**Written 2026-08-19 against `27e397e`**, correcting
[`H7d-SCOPING.md`](../H7d-SCOPING.md) — which is **not** retro-edited, per `CLAUDE.md`: a
correction is appended and says what it replaces.

**1. `EXIT_EXTERNAL = 5` exists.** The scoping's § 0.3 says *"Exit code 5 does not exist in this
build. `diagnostics.py` defines `EXIT_OK`=0, `EXIT_WRONG`=1, `EXIT_INVOCATION`=2, `EXIT_PARTIAL`=3,
`EXIT_FAILED`=4 and nothing else."* Measured: `git show 0faa2e3:src/publishable/diagnostics.py`
and `git show 27e397e:src/publishable/diagnostics.py` both define `EXIT_EXTERNAL = 5` on the line
after `EXIT_FAILED`, and `grep -rn EXIT_EXTERNAL src/ tests/ docs/` finds **one** definition, **no**
reader, and two mentions in the development record — one of them the spine plan that specified it.
Three consequences:

- **Part B's task 18 is narrower than stated.** The constant ships; what is owed is a **reader**
  and the documented precedence (5 wins over 3 and 4), not the constant.
- **`EXIT_EXTERNAL` is a fourth member of the shipped-but-unread family**, beside `PROBES`,
  `field_convention` and `apparatus_facts`, and it is unfiled. **Task 17 files it**, in
  `spec-defects.md` and not in a ledger line, with Part B as its owner. That strengthens Decision 14's
  refusal of the old charter's tasks 12 and 13 rather than merely restating it.
- **It is evidence for the scoping's own § 8 lesson applied to itself**: an enumeration read off a
  file is exactly the kind of claim that goes stale, and this one was stale on the day it was
  written.

**2. Task 10's `probe: null`.** The scoping's Part A task 10 says *"`probe: null` staying the
honest record for a template declaring none."* § The apparatus core can only observe says such a
run records `apparatus: null` — the whole block. Decision 7 takes the document. Replacing the
scoping's phrasing rather than reconciling it, because the two records differ in what they claim.

**3. What survives unchanged, stated so this section is not read as a general doubt.** The
end-to-end false-`apparatus: null` reproduction, the `_check_probe` boundary measurement and its
two-sources-of-truth finding, the `batch` two-arm re-measurement, the nine-config re-run with its
control, the H8/H9 structural routing, the check-placement finding that produced Decision 1, and
the 13/9 seam are all **re-read and unchallenged** — the seam moves only by the three tasks
Decision-level rulings added and the one moved across it.
