# H8a — lineage and `io.reuse_from` — design

**Goal:** a run can consume an earlier run's artifacts, and the record says which run and which
artifacts. `io.reuse_from(run_id, step, name)` resolves a `run_id` to a run directory by the two
rules § Lineage between runs states, reads the named artifact through the reader dispatch `io.write`
already inverts, and every read accumulates into `provenance.upstream` — the upstream's `run_id`,
its `code_hash`, its `parameters_hash`, and exactly which names were read. It mints the first
`E-UPSTREAM-*` refusals and it builds the `run.yaml` **reader** that nothing in `src/` has.

**What it delivers, stated so it cannot be rounded.** `io.reuse_from` is the sole named remaining
core-side dependency of **six** of the nine configs in
[the feasibility analysis](../../feasibility-llm-growth-studies.md) — E3, E4, E6, C1, C2, C3 — and
`grep -rn "reuse_from" src/publishable/` returns **zero lines** at this commit. H8a retires that
dependency for all six. It **adds no `validate`-time check at all**, so the validate-clean figure
(8 of 8 transplantable configs) is unchanged by construction, and the figure that moves is the one
`validate` cannot see. § The payoff states what the § Executability entry may claim and what it may
not, and it declines to reuse the phrase the 2026-08-20 correction retired.

---

## The measurement this rests on

[`H8-SCOPING.md`](../H8-SCOPING.md) was measured on 2026-08-20 against `a346151` and it is this
design's input; it supersedes the spine design's one-row charter. `CLAUDE.md`'s rule is that a
scoping expires and a spec does not, so **every build claim below was re-measured against `main` at
`1540b6f` on 2026-08-20**, by running rather than by reading, and § What did not survive records
four scoping claims that did not.

### Measured on 2026-08-20 against commit `1540b6f`

| What was measured | How | Result |
|---|---|---|
| `reuse_from` anywhere in core | `grep -rn "reuse_from" src/publishable/` | **0 lines**. Control on the same tree: `read_upstream` finds `artifacts.py` and `cli.py` |
| The class that would host it | reading `artifacts.py` | **`StepIO`**, not `ArtifactIO`. Its `__init__` is keyword-only and takes `step_dir`, `input_dir`, `run_dir`, `units`, `scope`, `conditions`, `repeats`, `step_scopes`, `condition_index`, `condition_label`, `repeat_label`, `measurements` — and **no `output_dir`** |
| Whether `read_upstream` enforces the relative-path rule § Steps and artifacts states | **a live probe**: a `StepIO` over a throwaway tree, `read_upstream("step01", "../../secret/x.json")` and then the same call with an absolute path | **Both read the file and returned its parsed contents.** Neither is refused. `read_condition` resolves the same way, by reading: both end in a bare `self._read(base / step / name)`, and only `io.write`/`path`/`exists`/`append` go through `_resolve` |
| Whether any module reads a `run.yaml` | `grep -rn run_record src/publishable/` | one hit, `cli.py`'s import of the **assembler**. `run_record.py`'s own first line is *"Assemble run.yaml. Assembles only — computes nothing."* No reader exists |
| Whether `lineage.py` may import `run_record` | the import graph, read | **Yes, and `artifacts.py` may not.** `run_record` imports `runner`, which imports `artifacts`; nothing outside `cli.py` imports `run_record`. So `lineage → run_record → runner → artifacts` is acyclic and `artifacts → lineage` would not be. This is the literal Decision 2 rests on |
| Where `provenance` is assembled | reading `cli.py`'s phase 9 | a plain `dict` built in `command_run` and handed to `assemble_run_yaml(provenance=…)`, dumped with `sort_keys=False`. So a new key is an insertion in `command_run`, and the assembler stays *assembles only* |
| The `report_by`-under-`resample` gap, and what it actually costs | **direct call**, one table, two argument sets | `summarize_step` over the same 12-row table returns `method: t_over_units` with `ci95 [0.3209, 0.7791]` when `resample_columns` is not passed, and `percentile_over_units` with `[0.3583, 0.7500]` when it is. **Per recorded column, not per headline metric** — both `prob` and `latency_ms` moved. The `report_by` level call site passes `derived`, `seed`, `resample`, `draws`, `beside_n`, `weights`, `clusters`, `strata` and **no `resample_columns`** |
| E6's sweep, whose comment claims 3 baseline + 3 compiled conditions | `expand()` on E6's `sweep` block | **6 conditions**, labelled exactly as the comment describes: three `model=…__baseline`, three `program_id=…__model=…` |
| E4's and E3's condition counts | same | **5** and **5**, E3's being `baseline` plus four one-change conditions |
| Whether anything reads through a `..` segment today | `grep` over `tests/`, the four documents and `src/publishable/templates/` for `read_upstream(`/`read_condition(` with a `../` argument | **nothing**, over 18 `read_upstream` call sites in `tests/`. This is what makes Decision 8 safe to enforce rather than only to file |

Gates at this commit are the scoping's: `uv run pytest` → 2456 passed, 1 skipped, 2 xfailed.

---

## Decisions

### 1. What `reuse_from` reads, and from where — two forms, one predicate, and the repo guard applies to both

`io.reuse_from(run_id, step, name)` takes **one locator argument** in the `run_id` position, and
§ Lineage between runs gives it two readings:

- **A bare `run_id`** resolves to `<output_dir>/<run_id>/`, under *this* config's `data.output_dir`.
- **An absolute path** names a run directory anywhere, and its `run_id` is **read back from the
  `run.yaml` there** rather than parsed out of the path.

The two are told apart by `Path(locator).is_absolute()` and by nothing else — not by a separator
test, not by whether the directory happens to exist. A relative path with a separator in it is
neither form and is refused (`E-UPSTREAM-LOCATOR`): it would otherwise resolve under `output_dir` as
if it were a `run_id`, and `provenance.upstream` would record a value that is not an id.

**The repo-containment invariant applies to the absolute form, checked with the predicate that
already enforces it.** `CLAUDE.md` § Invariants: `input_dir`/`output_dir` may never resolve inside
the git repo, and **which repo is decided by a walk-up from the path the command was given**. The
relative form inherits the guarantee for free — `output_dir` was checked at `validate` and again by
`run` before any step existed. The absolute form is a *parameter value* and has been checked by
nothing, so `reuse_from` checks it with `provenance.resolves_inside_repo(resolved, repo_root)`,
against the `repo_root` `command_run` already computed by walking up from **the config path it was
given**. Re-deriving `repo_root` from the upstream path is refused as a design: it answers a
different question (does the upstream sit in *its own* repo) and a walk-up from an arbitrary
absolute path finds whatever repo happens to be above it — § Answering a question with a proxy is
the section about exactly that substitution.

*Grounds.* An artifact tree core forbids itself to write inside the repo is not one it should read
from either; admitting it would make a run's inputs live in the tree `code_dirty` and `code_hash`
are computed over, and the invariant's whole purpose is that the two trees never touch.
*Cost if wrong.* A legitimate layout is refused — a tutorial or fixture run committed inside a repo
on purpose. The route is stated in the refusal's own message: copy it outside the repo, or address
it by `run_id` under `output_dir`. If a later slice (`demo` is the candidate, and it is H9's) needs
in-repo runs, it changes this rule with an argument rather than discovering the refusal.

**The absolute form resolves symlinks, which makes `<output_dir>/latest` usable and honest.**
`resolve()` runs before the containment check, so a `latest` path lands on the real run directory and
its `run_id` is read from the record — `provenance.upstream` records the resolved id and never
`latest`, which is § Lineage's own rule that a path is a fact about one machine. The **relative**
form cannot accept `latest`, because `latest` is not a `run_id` and the directory it points at holds
a record saying so: that is `E-UPSTREAM-RUNID-MISMATCH` (Decision 4). **This asymmetry is a
property, not a bug**, and it is named here so a reviewer does not close it: the two forms differ in
exactly the way their arguments differ, one being an identity and the other a location.

### 2. `output_dir` never reaches `io` — the resolver is injected, and the step-facing surface gains one method and zero fields

`CLAUDE.md` § Invariants: *"What core hands a step is minimal and immutable on purpose."* The
scoping's task 3 is *"getting `output_dir` onto `io`"*. **H8a does not do that.** `command_run`
constructs one `UpstreamResolver` — in `lineage.py`, holding `output_dir`, `repo_root`, a per-`run_id`
record cache, and the accumulating ledger — and `StepIO.__init__` gains **one private keyword-only
parameter, `upstream=None`**, stored as `self._upstream`. `io.reuse_from` delegates to it. No public
attribute is added; the step-facing surface gains exactly the one method § Steps and artifacts'
`io` table **already documents**, and no new readable field.

*Grounds, three, and the third is mechanical.* (a) The invariant is about what a step can read, and a
step can read nothing new. (b) `output_dir` on `io` would be a second source of truth for a value the
config already holds, and a step that wanted it could compose a path core forbids it to write to.
(c) **`artifacts.py` cannot import `lineage.py`** — measured: `run_record` imports `runner` imports
`artifacts`, so a `lineage` that reads a `run.yaml` (Decision 3) and is imported by `artifacts` closes
a cycle. Injection removes the import edge rather than dodging it with a function-local import.

**And the acyclic claim needs one clause to stay true.** `runner.py` constructs `StepIO` and will now
pass the resolver through it, so a plain `from publishable.lineage import UpstreamResolver` in
`runner.py` reopens the cycle from the other side (`lineage → run_record → runner → lineage`). The
annotation goes under `if TYPE_CHECKING:` in both `runner.py` and `artifacts.py` — the latter already
imports `TYPE_CHECKING` for `UnitList`, so the precedent is in the file being changed. A reader who
later replaces it with a plain import undoes this decision rather than tidying an import.

*And it forecloses the proxy structurally rather than guarding against it.* `run_dir.parent` is the
tempting answer to "where do this experiment's runs live", and it is a proxy: it answers "where does
*this* run sit". With the resolver built in `command_run` from `doc["data"]["output_dir"]`, the
proxy is never in scope inside `StepIO` at all. § The mutations records that this is the one
prescribed mutation that **cannot** discriminate, and why.

*Cost if wrong.* A future surface that genuinely needs `output_dir` inside a step (none is specified)
pays for a second plumbing pass. Cheap, and reversible in the direction that widens rather than
narrows.

### 3. The `run.yaml` reader lives in `lineage.py`, and it is the reader every later sub-slice uses

`read_run_record(path) -> dict` in `lineage.py`: read the file, parse it as YAML, require a mapping,
require a `schema_version` this build can read, require `run_id`. It imports
`run_record.SCHEMA_VERSION` rather than restating it, so the writer and the reader of one file cannot
drift — the argument `artifacts._nest_repeat`'s own docstring already makes about two callers of one
rule (*"Writing it twice is how the two drift — which is exactly what had happened"*).

*Grounds.* § Package layout glosses `lineage.py` as *"upstream run recording and chain
verification"*, and a record reader is what verification reads. `run_record.py` is the other
candidate and is refused on its own docstring — *assembles only, computes nothing* — and on the
cycle above.
*Cost if wrong.* H8b and H8c import a reader from a module named for lineage when they want it for
`diff`, `report` and `study add`. That is a naming cost, not a behaviour one, and moving it later
moves one import line.

**Three refusals, not one.** A whole-record fault is the shape H4d closed by splitting: three
distinguishable faults with three different remedies.

| Fault | Code | Remedy a reader takes |
|---|---|---|
| No `run.yaml` at the resolved run directory | `E-UPSTREAM-RECORD-MISSING` | the run never finished, or the directory is not a run directory |
| Present and unreadable — invalid YAML, not a mapping, no `run_id` | `E-UPSTREAM-RECORD-UNREADABLE` | the file was edited or truncated |
| A `schema_version` this build does not read | `E-UPSTREAM-RECORD-VERSION` | pin the `publishable` version that wrote it |

**A run whose `status` is `partial` or `failed` is *not* refused here.** A partial run's completed
step wrote a real artifact, and refusing the whole record would make the artifact unreadable because
of a sibling condition that failed. The named **step**'s own status is what Decision 5 checks.

### 4. Locating the upstream step with no scope selector — `shared/` and `summary/` only, and the reason is the document's own

§ `reuse_from` addresses an artifact, not the design that produced it argues that there is no
condition or repeat selector *because* one would couple a downstream config to an upstream run's
layout, which a renumbering silently moves. **The same argument decides where a read may land**:
the only two artifact locations that carry no condition and no repeat coordinate are `shared/`
(a `run`-scoped step) and `summary/` (a `summary`-scoped step). So:

- The upstream record's `execution` block is the authority for a step's scope. A step named under
  `execution.shared` reads from `<upstream>/shared/<step>/`; under `execution.summary` from
  `<upstream>/summary/<step>/`. **This was measured against the assembler, not read off § The two
  files' example** — and it is the one place in this design where that distinction matters most,
  because a fixture synthesized against the example would pass against a mechanism that does not
  match what core writes, which is the *fixture whose numbers agree with the bug* shape.
  `run_record._execution_block` returns exactly `{"shared": {step: entry}, "conditions": [{index,
  label, steps}], "summary": {step: entry}}`; a `run`-scoped result goes to `shared` and a `summary`
  one to `summary` **on the step's scope alone**, with no sweep involved, and `conditions` is a list
  keyed by index. A `condition`-scoped step and a `repeat`-scoped one both sit inside one condition's
  `steps`, the latter nested under its repeat label (`""` when unlabeled) — which is why membership
  in `conditions` is the whole test and this design never has to tell those two apart.
- A step appearing under `execution.conditions` is refused: `E-UPSTREAM-STEP-SCOPED`, whose message
  names the step, its scope, and the route — **republish it from a `summary` step in the upstream
  run**, which is the code sample § `reuse_from` addresses an artifact already shows.
- A step appearing nowhere in the block is `E-UPSTREAM-STEP-UNKNOWN`.
- A step present whose recorded `status` is not `completed` is `E-UPSTREAM-STEP-INCOMPLETE` — a
  refusal rather than a read, because an artifact from an execution that did not finish is exactly
  the case *"lineage is recorded, not resolved"* exists to stop being silently consumed.

**The one case where the refusal is broader than the ambiguity, named so it is not read as an
oversight.** In an *unswept* upstream, a `condition`-scoped step writes into the run directory
directly — measured in `read_condition`, where `label is None` gives `base = run_dir` — so there is
an unambiguous location and the blanket refusal declines to use it. That is deliberate: § `reuse_from`
addresses an artifact's argument is about the upstream's design *changing*, and an upstream that is
unswept today and gains one level tomorrow relocates that artifact while every hash still matches.
A downstream read that worked before the level was added and reads a different cell after it is the
precise failure the missing selector exists to prevent.

*Grounds.* The rule is derived from the specification's own justification rather than invented, and
it means H8a resolves a scope without ever parsing a condition directory name.
*Cost if wrong.* A produce-then-consume design pays for one extra upstream `summary` step. That cost
is real and it lands on the feasibility analysis's own plugin — see § The prose read, where it is a
plugin obligation and not a core blocker.

### 5. `reuse_from`'s own contract, and the name rule enforced for all three readers

`reuse_from` resolves the locator (Decision 1), reads and caches the record (Decision 3), resolves
the step directory (Decision 4), normalizes `name` against that directory, and reads through
`StepIO._read` — the same longest-registered-suffix dispatch `io.write` inverts, so an unregistered
suffix comes back as `bytes` and a **writer-without-reader** suffix is the already-shipped
`E-ARTIFACT-UNREADABLE`. H8a mints no second code for that; the scoping is right that it is
inherited.

- The artifact not being there is `E-UPSTREAM-ARTIFACT-MISSING`, one code for a missing step
  directory and a missing file within it: the remedy is identical (the upstream published no such
  name) and § Errors carries one row per code.
**`name` is a containment rule and nothing more, and its scope is bounded on purpose (controller
ruling 1).** What is refused is **`..` traversal, an absolute path, and a symlink leading outside**;
`E-UPSTREAM-NAME` carries it — its own code rather than the shipped `E-ARTIFACT-NAME`, on the
precedent `E-RESOLVER-SWEPT-PARAM` already sets over `E-STEP-SWEPT-PARAM`: one mechanism, two
faults, because a reader holding `E-ARTIFACT-NAME` is sent to a section about *this* step's own
directory and this escape is out of another run's.

**Forward separators stay legal, and that is not a concession — it is the documented design.**
§ Steps and artifacts states *"A `name` is a relative path, not only a filename"*, that *"only the
name's last component is examined"* for the suffix dispatch, and gives
**`programs/gpt-4.1__seed29.json`** as a worked legal name whose interior dot matches nothing. § Lineage's
own downstream example reads `f"programs/{...}__seed{seed}.json"`. A rule refusing separators would
break a documented example — here the example *is* load-bearing, which is the *treating a row's
example as its definition* trap read from the other side. So the helper normalizes and checks
**containment**, and never the shape of the path.

**And it is not a boundary. A step can read any file on the machine regardless, and this must not be
written up as a sandbox escape.** `name` is supplied by the user's own step, which can `open()`
anything it likes; `CLAUDE.md` § Invariants is explicit that **core never inspects the body of user
Python**, and § Greenfield only draws that line in the same place `io.read_input`'s read-only note
does. What the rule buys is that **an artifact read resolves inside the run directory it names**, so
a typo'd `..` fails loudly instead of silently returning something unrelated — a wrong answer that
looked like an artifact is the failure being prevented, not an exfiltration.

**On those merits, the rule is adopted, and it goes onto `read_upstream` and `read_condition` in
this slice.** § Steps and artifacts states it for *every* reader by name — `io.path`, `io.append`,
`io.read_upstream`, `io.read_condition`, `io.reuse_from` — and the live probe above shows the two
that ship enforce **neither** a `..` escape nor an absolute path. A normative sentence asserting a
guarantee two shipped readers do not provide is a defect and not specification, on `CLAUDE.md`'s own
distinction: *an unbuilt reader of a shipped surface is a defect*. The alternative — narrow the
sentence and file the code gap — is charter-defensible and is rejected because the fix is one shared
helper shaped like the `_resolve` that already exists, the probe above is its pin, and **nothing in
`tests/`, the four documents or `src/publishable/templates/` reads through a `..` segment**
(measured, over 18 `read_upstream` call sites), so enforcing it breaks nothing.

*Grounds.* One helper, three callers, one sentence that becomes true — and a loud failure where
there is currently a quiet wrong answer.
*Cost if wrong.* A user's step that reads a sibling step's artifact by `../otherstep/x.json` starts
failing. That path was never sanctioned — `read_upstream(step, name)` takes the step as its own
argument — and the refusal names the supported call. **The cost of declining the rule instead** is
the state measured today: a `..` typo reads an unrelated file and the record calls it an artifact.

**One apparent contradiction with Decision 1, named so it is not closed as an oversight.** An
**absolute *locator*** is legal (Decision 1: it is how an upstream outside `output_dir` is named, and
§ Lineage puts it in a parameter for exactly that). An **absolute *name*** is refused (here). The two
arguments differ and both hold: a locator addresses a run, whose location is a fact about a machine
the config is allowed to state; a name addresses an artifact *within* a run, whose location is
derived from the step it belongs to and is not the caller's to choose.

### 6. Accumulation: what enters `used`, when, and in what order

One `UpstreamLedger`, created in `command_run`, handed to every `StepIO` through Decision 2's
parameter, so it outlives the per-execution `StepIO` objects and survives an execution that fails.

- **An entry is made when a read *returns*.** A `reuse_from` call that raises entered nothing: no
  artifact was read, and a `used` list naming an artifact that is not there would make the chain
  unverifiable in exactly the direction `provenance.upstream` exists to close.
- **A read from an execution that later fails is kept.** The dependency is a fact about what was
  consumed, not about what succeeded, and dropping it would hide the ancestor a failed step rested
  on. These are two rules and they are easy to conflate in one sentence, so they are two bullets.
- `used` entries are `f"{step}/{name}"`, matching § The two files' own `["step01_load_cohort/cohort.parquet"]`.
- **`used` is deduplicated and sorted lexicographically**, and the entry list is **sorted by
  `run_id`**. Not insertion order: insertion order is *execution* order, which `order: randomized`
  moves between two runs of the same design, so a record key that is stable across two identical
  runs cannot be built from it. This is the same reason § Resuming reads the realized order rather
  than re-deriving it — a fact should not be re-computable to a different answer.
- The upstream's `code_hash` and `parameters_hash` are read from its record once per `run_id` and
  cached, so N reads from one upstream do one record read. **One answer per run**, on
  `allocation.json`'s read-rather-than-re-draw precedent; a cache is also why an upstream edited
  mid-run cannot give two answers inside one record.

*Cost if wrong.* Insertion order would make two runs of one design produce records that differ in a
field neither run's design mentions, and a `diff` (H8b) would report a difference that is not one.

### 7. `provenance.upstream` is **always written, and `[]` when there is no upstream**

Measured: `upstream` is absent from a real run's `provenance` today, while `apparatus`, `allocation`
and `allocation_hash` are written `None`. No document says what a no-upstream run writes. **H8a
writes `upstream: []`, unconditionally.**

*Grounds.* The absent-versus-`null` convention (absent = nothing was asked for, `null` = attempted
and came back empty) is a convention for a **scalar-or-object** value, and it is what
`repeat_spread`'s omission and H4c's absent `n_paired` rest on. `upstream` is a **list**, and the
in-block precedent for a list is `input_manifest_changed: []` — always present, empty meaning none
did — which sits in the same `provenance` mapping and answers the same shape of question. A `null`
for a list is also a reader hazard: `for u in provenance["upstream"]` breaks on `None` and not on
`[]`. And the third state the convention would distinguish does not exist here: core cannot know
whether a step *intended* to reuse and found nothing, because it never inspects the body of user
Python.
*Reconciled with the neighbours rather than contradicting them:* `apparatus: null` and
`allocation: null` say *this run's config declared no such feature*, which is a declaration core can
see. `upstream` has no declaration anywhere — it is a consequence of step code — so there is no
"declared and did not apply" state for a `null` to name.
*Cost if wrong.* A reader cannot distinguish a run written by a build predating this key from one
that consumed no upstream. `schema_version` is what carries that, and it is already in the record.

The key is inserted immediately after `allocation_hash`, which is its documented position relative to
a sibling that already ships. Nothing else in the mapping is reordered — the shipped insertion order
already differs from § The two files' example in another place, and reordering it would rewrite every
run.yaml fixture in the suite for a cosmetic reason.

### 8. The three hashes: `provenance.upstream` records **no new hash**, and the chain is verified by re-reading

`CLAUDE.md` § Invariants: three hashes, split on purpose, `code_hash` over `src/**` and
`templates/**`. **H8a hashes nothing.** `provenance.upstream` carries a *copy* of two figures the
upstream computed for itself, plus the resolved `run_id` and the names read — four keys, exactly what
§ Lineage between runs enumerates, and no fifth.

**How a reader verifies the chain.** Resolve the recorded `run_id` by the rule of Decision 1 — the
same rule, which is why the rule and not a stored path is what the record carries — open that run's
`run.yaml`, and compare its own `code_hash` and `parameters_hash` against what the downstream
recorded. Agreement means the ancestor at that location is the ancestor that was read; disagreement
means it is not; absence means unreachable, **reported and never recomputed**, which is § Lineage's
own sentence. Walking the chain is `reproduce`'s (H9's) and reporting a difference is `diff`'s
(H8b's); H8a's obligation is that the four keys are true.

**Refused: a manifest hash over the artifacts read.** It would be a fourth hash, over another run's
tree, computed by a downstream run that produced none of it — and `input_manifest_hash` deliberately
covers `input_dir` only. § `reuse_from` addresses an artifact chooses the level of assurance
explicitly: *"checkable at the level of named artifacts rather than paths."* A reader wanting bytes
has the upstream's own two hashes, which identify the run that produced them.
*Cost if wrong.* An upstream whose artifacts were edited in place after it finished is not detected
by this record. It is not detected by the upstream's own record either, and closing it means hashing
an output tree, which no hash in this project does.

### 9. Read direction and scope: legal at every scope, and no cross-run direction check

`scope.py`'s read-direction rules order steps **within one run** — `read_upstream` reads wider steps
because a narrower one has not executed yet. `reuse_from` reads a run that has already ended, so
there is no such relation to check, and § Lineage's own downstream example is annotated *"downstream
run, any scope"*. So `reuse_from` is available at `run`, `condition`, `repeat` and `summary` scope
with no direction check and no `_summary_only` gate, and `E-STEP-READ-DIRECTION` /
`E-STEP-READ-AMBIGUOUS` are not reachable through it.

**A resolver's `io` does not get it.** `ResolverIO` offers `read_input` and nothing else, and it stays
that way: a roster is one run's own resolution, and a roster that depended on another run's artifact
would put the inference base behind a lineage read `validate` cannot see. Routed, not built — if a
design needs it, it argues for it against § Where units come from.

### 10. Nothing here stops or alters a run, and that follows from a shipped rule rather than a new one

Every `E-UPSTREAM-*` code is a `ContractError` or `ArtifactError` raised **inside an execution**, and
§ Errors core raises already settles what that means: *"A `ContractError` inside an execution fails
that execution like any other error, and the run continues to the next one."* H8a adds no stop, no
new exit code, and no new path on which a paid-for record is lost. The failed execution is recorded
`failed`, the plan continues, `status` follows the existing rule, and `provenance.upstream` records
the reads that did return (Decision 6).

*Why this is stated rather than assumed.* H7d Part B established the boundary carefully and
`CLAUDE.md` names the habit it protects — *every execution paid for, the record lost*. A lineage
read is a natural place to reach for a hard stop ("the ancestor is gone, nothing downstream is
meaningful"), and that reasoning is rejected here: core has no way to know whether the mistake is in
one step or all fifteen, which is the argument § What `status` means already makes.

### 11. `validate` gains nothing, and that is a consequence of two invariants

H8a adds **no** `validate`-time check. The locator is a **parameter** — § Lineage puts it there on
purpose, so it sits inside `parameters_hash` and in the embedded config — and core cannot know which
parameter is a run locator without either a declared lineage block (refused by the same argument
that removed the selector) or reading the body of user Python (refused outright, § Greenfield only).
So `validate` collecting rather than aborting is irrelevant to this slice: there is nothing in the
family for it to collect.

*The cost, named rather than filed.* A config naming an upstream run that does not exist validates
clean and fails at the first execution that reads it — after paying for every execution before it.
For E3, E4 and E6 that is the `run`-scoped `step01_serialize` and a `condition`-scoped compile, so
the cost is real money. The mitigation available today is a `dry-run` (H9's) and the honest statement
is that a step-level dependency is invisible to `validate` **by design**, which is exactly the
distinction that made "six" wrong.

---

## Out of scope, with the route for each

| Refused here | Route |
|---|---|
| `publishable diff` and `publishable freeze`, and the `E-DIFF-*`/`E-FREEZE-*` families | **H8b**, 8 tasks, including the `freeze`-has-no-config hole `H8-SCOPING.md` § 4 measured and `append_observation`'s unenforced phase vocabulary |
| `publishable report`, `BaseReport`, `generate report`, `study new`/`study add` | **H8c**, 12 tasks. `BaseReport` is H8's; the `spec-defects.md` note re-owning it to *unassigned* is contradicted by three measured sites (`H8-SCOPING.md` § 7) |
| Walking a chain deeper than one hop, and reporting an unreachable ancestor | **H9** (`reproduce`, § Reproducing on another device) for the walk, **H8b** (`diff`) for *"two runs differ only because their upstreams did"*. H8a's obligation is that the four recorded keys are true and re-resolvable |
| `apparatus.expected.json` | **H9**, per `H7-SCOPING.md` § 10. Not H8's at all |
| `report_by` under a declared `resample` — a level's recorded-column interval stays `t_over_units` | **H4 Statistics**, filed, and **re-attributed by this design**: it is live on seven of the nine configs, not on C1–C3 (§ The prose read) |
| A hash over the upstream artifacts read | Refused as a fourth hash (Decision 8) |
| `ResolverIO.reuse_from` | Refused (Decision 9); a design needing it argues against § Where units come from |
| A `validate`-time upstream check | Refused (Decision 11) as a consequence of § Greenfield only and of the locator being a parameter |
| Reading a condition- or repeat-scoped upstream step | Refused (Decision 4); the route is an upstream `summary` step that republishes under stable names, which § `reuse_from` addresses an artifact already shows in code |

---

## The prose read H8a's design owes for E3, E4 and E6

`H8-SCOPING.md` § 6.3 projects three → six *"pending the prose read H8a's design owes"*, and § 10
names its limit: a step-level call is invisible to `validate`, so this can only be a **read**. Here
it is, with what was measured beside what was inferred.

**Every core declaration E3, E4 and E6 make is built, and three of the four doubts were measured
away.**

| Dependency the prose or YAML implies | State |
|---|---|
| E3's `sweep.ablate` with `from: baseline` and `override` | **Built**, measured: `expand()` gives 5 conditions — `baseline`, two `censor_buffer_years` arms, two `min_valid_visits` arms — exactly what its comment claims |
| E3's `io.skip` → `ineligible`, and `limits.max_ineligible_fraction` | **Built**: `StepIO.skip` ships and `cli.py` reads the limit |
| E4's `{kind: batch, n: 5}` with `order: randomized` | **Built**: `batch` is in `replication.SUPPORTED_KINDS` with a position rule of its own |
| E6's baseline left free over an unfixed `llm.model` axis | **Built**, measured: 6 conditions, three `model=…__baseline` and three `program_id=…__model=…`, which is the analysis's own arithmetic |
| E6's `sweep.paired` for the provider/model cell, and `Param(requires_env=)` on a swept value | **Built** (`paired` is a product mode; `requires_env` is H7c's) |
| `statistics.resample` with `stratify_by` | **Built** (H4a) |
| `io.reuse_from` | **This slice** |
| A `report_by` level's recorded-column interval under a declared `resample` | **Live gap, H4's** — and this is the finding |

**The finding: the `report_by`-under-`resample` gap is live on seven of the nine configs, not on
three, and the record attributes it to C1–C3 alone.** Measured two ways. First, what the gap costs:
`summarize_step` over one 12-row table returns `t_over_units` and `[0.3209, 0.7791]` without
`resample_columns` and `percentile_over_units` and `[0.3583, 0.7500]` with it — **per recorded
column**, both `prob` and `latency_ms` moving, so it is not a property of a config's headline metric.
Second, what the configs record: all six screening runs and all three shortcut runs draw their
per-unit rows from **one** request step, whose `io.record` payload is `pred`, `prob`, `truth`,
`valid`, `invalid_reason`, `prompt_tokens`, `completion_tokens`, `reasoning_tokens`, `latency_ms`,
`attempts`, `finish_reason` — numeric recorded columns throughout. So every config with a declared
`resample` **and** a non-empty `report_by` publishes level blocks whose recorded-column intervals are
unresampled: **E1, E2, E4, E6, C1, C2, C3**. E5 escapes, and escapes for its own reason — `resample:
null` and `report_by: []`.

**E1 and E2 are inside today's three.** So the record already applies a standard under which this gap
is **not** a core-side blocker; charging C1–C3 with it while not charging E1, E2, E4 and E6 is the
same inconsistency the 2026-08-20 correction documented — *one dependency, two treatments, one
table* — appearing one document later in `H8-SCOPING.md` § 6.3's own "blocked, and on what" row.

**E3 carries one more thing, and it is a plugin obligation rather than a core blocker.** Under
Decision 4, an upstream step must be `run`- or `summary`-scoped to be addressable. `growth_screen`'s
shown pipeline compiles at **`condition`** scope (`step02_compile_program`), and its two summary
steps compare rather than republish — so E2, the run E3/E4/E6 read their frozen program from, needs a
`summary` step that republishes the compiled programs under stable names. That is § `reuse_from`
addresses an artifact's own code sample, it is the plugin's to write, and it changes no core-side
count. It is stated because a reader costing E3 would otherwise discover it at the first read.

**And two limits inherited rather than closed.** E3's `data`/`statistics` blocks were never
transplanted — its section shows only what differs from E1 and carries no such YAML — so *"E3
inherits E1's `statistics` block"* is an **inference** from the analysis's "only the blocks that
differ are shown" convention and not a measurement; I never saw E3's YAML. And no step of
`growth_screen` exists, so no dependency of the *step bodies* can be measured at all, by anyone,
until the plugin is written.

---

## The payoff, stated as separate figures so no single number needs a footnote

The 2026-08-20 correction retired *"six with no remaining core-side blocker"* because it answered no
consistent question. This design does not mint a successor phrase. The § Executability entry H8a
writes reports **four figures, each with the question it answers**, and labels the projection.

| Figure | Before H8a (measured, `8d5c046`/`1540b6f`) | After H8a | Question it answers |
|---|---|---|---|
| Transplantable configs validating clean | **8 of 8** | **8 of 8, unchanged** | what `validate` reports. H8a adds no validate-time check (Decision 11), so this cannot move |
| Configs whose named unbuilt-core dependency `io.reuse_from` is retired | 0 | **6** — E3, E4, E6, C1, C2, C3 | what this slice is for. Measurable by probe: `io.reuse_from` resolving and reading against a real produced upstream run |
| No remaining core-side blocker / **executable**, under the standard the record applies | **3** (E1, E2, E5) | **8 of 8 transplantable, projected, and only with the plugin written and installed** — E3 stated separately as unmeasured | the same standard that puts E1 and E2 inside today's three, applied consistently. **6 is not the answer**: reaching it requires charging C1–C3 with the `report_by` gap while not charging E1, E2, E4 and E6 with it |
| Configs carrying the live `report_by`-under-`resample` gap | **7** (E1, E2, E4, E6, C1, C2, C3) | **7** | filed to H4, not folded in. Named for all seven rather than for three |

**What the entry may claim, and what it may not.** It may claim, by probe, that `io.reuse_from`
resolves both locator forms, reads through the registered reader, and writes `provenance.upstream`
with the upstream's own two hashes — because that is testable end to end. It may **not** claim that
E3, E4 or E6 executes: both standing qualifications survive H8a and neither is H8a's to retire —
**the `growth_screen`/`growth_shortcut` plugin must be written and installed**, and a declared
apparatus probe needs a real plugin behind it. And it may not claim any of this from `validate`: a
config that validates clean is not a config that executes, and **every claim this slice makes about
a config is invisible to `validate`** — the locator is a parameter, the read is a step-level call,
and the record key is written at run end.

**The honest single sentence, if one is needed:** *H8a retires `io.reuse_from` as a named dependency
for six of nine configs and moves no `validate` finding at all.*

---

## What the record still gets wrong

**The `report_by`-under-`resample` gap is live on seven of the nine configs — E1, E2, E4, E6, C1, C2,
C3 — and `CLAUDE.md`, `H8-SCOPING.md` § 6.3 and the § Executability entries charge it to C1–C3
alone.** Measured twice on 2026-08-20 against `1540b6f`, both by computing rather than reading:
`summarize_step` over one 12-row table returns `t_over_units` and `[0.3209, 0.7791]` without
`resample_columns` and `percentile_over_units` and `[0.3583, 0.7500]` with it, moving **both** `prob`
and `latency_ms` — so the gap is per *recorded column*, not per headline metric; and all nine configs
record their rows through **one** request step whose `io.record` payload (`prob`, `prompt_tokens`,
`completion_tokens`, `reasoning_tokens`, `latency_ms`, `attempts`) is numeric throughout. Any config
with a declared `resample` and a non-empty `report_by` is affected; E5 escapes on `resample: null`
and `report_by: []`.

**So the surviving "three" is itself now suspect, for the same reason "six" was.** E1 and E2 sit
inside it while carrying the identical gap E3, E4 and E6 are excluded for — one dependency, two
treatments, one table, which is precisely what the 2026-08-20 correction documented, appearing one
document later and in the opposite direction. **This design does not resolve it by adjusting a
count.** The gap is **H4 Statistics'**, live, and re-attributed here on measurement rather than on
the record's attribution; the honest output is § The payoff's four measured figures plus this named
live gap, and **not a fifth number**.

---

## The discriminating fixtures

**A fixture is a claim too.** Every literal below is computed or read back; where a value cannot be a
literal, the fixture says what it is compared against instead.

### Fixture R — one genuinely produced upstream run

One real end-to-end `run` through `main(["run", …])` over a scaffolded project: a `run`-scoped step
that writes `cohort.json`, a `summary`-scoped step that writes `programs/a.json`, `programs/b.json`
and `programs/c.json`, one condition, one repeat. This is the only fixture that needs a real run, and
it needs one for exactly one reason: **it pins that the reader reads what the writer wrote.** Every
hash it yields is read back from its own `run.yaml` and **never written as a literal** — a literal
would be a hash of this repo's tree at fixture-writing time and would pin the test to a commit.
Every other upstream record below is **synthesized**, on `H8-SCOPING.md` § 5's pattern, and says so.

### Fixture L — the two locator forms, and the mismatch

Three synthesized run directories under one `output_dir`, plus one copied to `elsewhere/moved_run/`
whose record still holds its original `run_id`.

- Relative form: `reuse_from("run_…_aaa", …)` resolves under `output_dir` and reads.
- Absolute form on `elsewhere/moved_run/`: reads, and `provenance.upstream[0]["run_id"]` is the
  **record's** id. A second assertion checks the string `moved_run` appears **nowhere** in the
  rendered record — the pin for *"records the resolved `run_id` and never the path"*.
- `<output_dir>/latest` (a real symlink) via the **absolute** form: reads, and records the resolved
  id. Via the **relative** form: `E-UPSTREAM-RUNID-MISMATCH`, which is Decision 1's named asymmetry.
- A directory under `output_dir` renamed so its basename and its record's `run_id` disagree:
  `E-UPSTREAM-RUNID-MISMATCH`.

### Fixture C — the containment guard

A synthesized upstream run directory inside a throwaway git repo that is also the **downstream's**
repo (a `.git` above it, and the downstream config beneath the same root). The absolute form is
refused with `E-UPSTREAM-REPO-CONTAINED`. The control is the identical directory moved one level
above the repo root: it reads.

### Fixture S — the scope refusal, built so the mutant succeeds

The upstream is synthesized with an `execution` block naming a `run` step under `shared`, a `summary`
step under `summary`, and a **`condition`** step under `conditions[].steps` — **and the
condition-scoped artifact genuinely exists on disk** at `conditions/00_x/step02/out.json`. That last
clause is the whole fixture: without it, a mutant that resolved into the condition directory would
raise `E-UPSTREAM-ARTIFACT-MISSING` and a test asserting only "it raises" would pass. The assertion
is on the **code**, and the mutant reads successfully.

Beside it: a step absent from the block (`E-UPSTREAM-STEP-UNKNOWN`) and a step present with
`status: failed` whose artifact **exists** (`E-UPSTREAM-STEP-INCOMPLETE`) — same construction, same
reason.

### Fixture N — the name rule, across all three readers

Parametrized over `reuse_from`, `read_upstream` and `read_condition`, and over three names:
`../../secret.json`, an absolute path, and a symlink inside the step directory pointing outside.
Each asserts the code (`E-UPSTREAM-NAME` for `reuse_from`, `E-ARTIFACT-NAME` for the two shipped
readers, which is the code `_resolve` already raises). **The file each one targets exists and holds
distinguishable content**, so an unenforced reader returns it rather than failing for an unrelated
reason — which is what the live probe in § The measurement already demonstrated for two of the three.

**The positive control is the half that bounds the rule, and it is not optional.** Two legal names
that must keep reading: `programs/a.json` — a forward separator, § Steps and artifacts' own worked
shape — and `programs/gpt-4.1__seed29.json`, whose interior dot must still dispatch as `.json` and
not as some suffix ending in `.1`. Without it, a helper that refused every separator would pass the
three refusal arms and the fixture would certify the rule the controller's ruling 1 forbids.

### Fixture O — `used` and entry ordering, sized for three candidate orderings

`CLAUDE.md`: *two elements only ever distinguish two answers.* There are **three** orderings to rule
out — sorted, insertion, and reverse-insertion — so the fixture reads **three** artifacts in the
order `c.json`, `a.json`, `b.json`:

| Candidate | Result |
|---|---|
| sorted (the ruling) | `a.json`, `b.json`, `c.json` |
| insertion | `c.json`, `a.json`, `b.json` |
| reverse-insertion | `b.json`, `a.json`, `c.json` |

All three differ, so the single assertion on the exact list discriminates all three. The same shape
for entries: **three** upstream run directories (one real, two synthesized) read in an order that is
neither their sorted `run_id` order nor its reverse.

### Fixture E — the empty case, two assertions because one cannot see it

A real `run` with no `reuse_from` call anywhere. **Two** assertions: `"upstream" in
record["provenance"]` and `record["provenance"]["upstream"] == []`. `[]` and absent are both falsy
and a single truthiness assertion cannot tell them apart — which is the whole content of Decision 7.

### Fixture F — a read from an execution that later fails

A repeat-scoped step that calls `reuse_from` and **then** raises. Assertions: the execution is
recorded `failed`, the run's `status` is not `completed`, `run.yaml` **exists**, and
`provenance.upstream[0]["used"]` contains the name that was read. Beside it, the other half of
Decision 6: a step whose `reuse_from` call **raises** (a missing artifact) contributes **no** entry —
`provenance.upstream == []` — while the execution is still recorded `failed` and the plan still
continues to the next one.

### Fixture P — the scopes

`reuse_from` called from a `run`-, `condition`-, `repeat`- and `summary`-scoped step in one run, all
four succeeding, and `provenance.upstream` carrying one entry with four `used` names. The control
that makes it non-vacuous: the same run's `read_upstream` from a wider scope still raises
`E-STEP-READ-DIRECTION`, so the test proves `reuse_from` is exempt rather than proving the direction
check is gone.

---

## The mutations, each with the assertion that catches it — and the one that cannot

Across the two H7d parts at least seven prescribed mutations could not discriminate. Each row below
names the assertion and states why the two branches differ.

| Mutation | Assertion that catches it | Why the branches differ |
|---|---|---|
| Delete the `sorted()` on `used` | Fixture O's exact-list assertion | insertion order is `c, a, b`; sorted is `a, b, c` |
| Delete the `sorted()` on entries | Fixture O's entry-order assertion | read order is not sorted `run_id` order, by construction |
| Write `upstream` only when non-empty | Fixture E's **membership** assertion | absent vs. `[]`; the equality assertion fails too, but only membership names the fault |
| Resolve a condition-scoped step into `conditions/<nn>_<label>/` instead of refusing | Fixture S's code assertion | the mutant **succeeds**, because that artifact exists on disk |
| Skip the `status == "completed"` check | Fixture S's `E-UPSTREAM-STEP-INCOMPLETE` assertion | the failed step's artifact exists, so the mutant returns it |
| Parse `run_id` from the directory basename in the absolute form | Fixture L's *record's id* assertion, plus *`moved_run` appears nowhere* | the copied directory's basename and its record's id differ by construction |
| Drop the containment check | Fixture C's code assertion, against its own control | the mutant reads the in-repo record successfully |
| Drop the `name` normalization in any of the three readers | Fixture N's refusal arms, parametrized | each target file exists and holds distinguishable content — already demonstrated by live probe for two of the three |
| Widen the rule to refuse **any** separator in `name` | Fixture N's **positive control** | `programs/a.json` reads under the rule as ruled and raises under the widened one — the two branches differ, and this is the mutation that catches a fix that overshoots |
| Record an entry when the read **raised** | Fixture F's second half (`upstream == []`) | one call, one raise, and the ledger is either empty or holds a name for an artifact that is not there |
| Drop the entry when the execution later fails | Fixture F's first half | the same run yields one entry or none |
| Widen a `reuse_from` refusal into a run stop | Fixture F's *`run.yaml` exists* assertion, plus the run reaching its next execution | the mutant leaves no record and an unexecuted second condition |

**One prescribed mutation is dropped, and saying so is the point.** Replacing `output_dir` with
`run_dir.parent` **cannot be caught by any fixture**, because core allocates every run directory
under the config's own `output_dir`, so the two are equal in every reachable state and the two
branches produce identical results. `CLAUDE.md`'s rule is that a mutation is a claim too. The proxy
is therefore prevented **structurally** rather than tested: under Decision 2 the resolver is built in
`command_run` from `doc["data"]["output_dir"]` and `run_dir` is never in its scope, so the wrong
answer is not available to be written. Anyone later tempted to derive it from a `run_dir` — and
`freeze` and `resume` both take a run directory a user typed, possibly through `latest` or a moved
copy — is changing a design decision, not a line.

**And a safety claim to make happen rather than assert.** No comment may say a `reuse_from` refusal
"cannot reach the plan". Fixture F is that claim's mutation: patch `reuse_from` to raise on every
call and check `run.yaml` still exists and the next execution still ran. H7d Part A's only Critical
came from an unreachability claim a three-line fixture falsified.

---

## Task decomposition — 10

Matching `H8-SCOPING.md` § 9's count. Task 5 is wider than the scoping's (it covers the two shipped
readers as well, for the reason Decision 5 gives) and task 3 is narrower (it does **not** put
`output_dir` on `io`).

| # | Task | Testable by |
|---|---|---|
| 1 | `lineage.py`: `read_run_record`, importing `run_record.SCHEMA_VERSION`; the three record refusals | direct call on synthesized records + Fixture R's real one |
| 2 | `resolve_run(locator)`: both forms, the absolute/relative split, `E-UPSTREAM-LOCATOR`, `-RUNID-MISMATCH`, `-REPO-CONTAINED`, `-RECORD-MISSING`, symlink resolution | direct call; Fixtures L and C |
| 3 | `UpstreamResolver` + `UpstreamLedger` in `lineage.py`, built in `command_run` from `data.output_dir` and `repo_root`, injected as `StepIO(upstream=…)`. **No `output_dir` on `io`** | direct call plus one wiring test that a step reached through `main(["run", …])` has a resolver |
| 4 | Step location from the upstream record's `execution` block; `-STEP-UNKNOWN`, `-STEP-SCOPED`, `-STEP-INCOMPLETE` | direct call; Fixture S |
| 5 | `io.reuse_from` itself: `-NAME`, `-ARTIFACT-MISSING`, `_read` dispatch, inherited `E-ARTIFACT-UNREADABLE` — **and the shared containment helper wired into `read_upstream` and `read_condition`. Containment only: `..`, an absolute path and an escaping symlink; forward separators stay legal (ruling 1)** | direct call on `StepIO`; Fixture N **including its positive control**; Fixture R for the real read |
| 6 | Accumulation: entry on return only, kept across a failing execution, `used` and entry ordering | **a real `run`** for the failing-execution arm; Fixtures O and F |
| 7 | `provenance.upstream` assembly and the always-`[]` ruling, inserted after `allocation_hash`; `assemble_run_yaml` unchanged | **two real runs**, one with an upstream and one without; Fixtures E and R |
| 8 | Scope and read direction: all four scopes, no direction check, `ResolverIO` unchanged | Fixture P, with its control |
| 9 | Documents: § Lineage between runs (the two forms' refusals, the scope rule, the no-upstream shape), § The two files (`upstream: []`), § Errors core raises rows — **including `E-ARTIFACT-NAME`'s own row, which today reads as a write-side fault and gains two readers in task 5**; a row narrower than its code is the `E-TEMPLATE-UNKNOWN` two-emit-sites shape — and § Package layout (`lineage.py` marker, `artifacts.py` gloss) | the mechanical + cross-document passes |
| 10 | § Executability re-measurement with § The payoff's four figures; `spec-defects.md` — the `io.reuse_from` entry struck, the `..`/absolute escape entry closed by task 5, the `report_by` re-attribution filed | the sweep below |

**Ordering constraints, each with its reason.** 1 → 2 (a locator is resolved by reading a record).
2 → 4 (a step is located inside a resolved run). 3 before 5 (the method delegates to the injected
resolver). 5 → 6 (nothing accumulates until something reads). 6 → 7 (the key is assembled from the
ledger). 9 after 7, so the documented no-upstream shape is the one that ships. 10 last, because a
re-measurement must run against the finished branch.

---

## The consistency sweep this slice owes

After the document edits, over **the four documents, `CLAUDE.md`, and the feasibility analysis**, by
naming the files — never by filtering a sweep's output, per § Two mechanical traps:

- `reuse_from`, `upstream`, `lineage` — every occurrence re-read against what shipped, including
  § Steps and artifacts' `io` table row, which needs no change and must be confirmed rather than
  assumed.
- `lineage.py` and `not yet built` in § Package layout — the marker moves, and the `artifacts.py`
  gloss gains `reuse_from`.
- The § Steps and artifacts sentence enumerating which readers reject an absolute path, a `..`
  segment or an escaping symlink — **true after task 5, and the sweep is what proves the sentence
  and the code agree in both directions.**
- `E-ARTIFACT-NAME` — every mention, since task 5 gives it two new emit sites and § Errors carries
  one row per code rather than per site.
- `provenance` key lists — § The two files' example, § Reproducing on another device, and any
  `run.yaml` excerpt elsewhere: a new key can invalidate a downstream example that was correct
  without it.
- Each sweep is proved able to fail by running it first against a string known to be present.

---

## The filings this slice touches

| Filing | What H8a does to it |
|---|---|
| *"`io.reuse_from` is unbuilt and unowned"* | **Struck.** Built here; the ownership half was already closed by `H8-SCOPING.md` § 7 |
| *"Six `provenance` and `results` keys in the `run.yaml` example that no code writes"* | Narrowed: `upstream` comes off the list. The rest stay, with their owners |
| The `..`/absolute escape in `read_upstream` and `read_condition` | **Closed by task 5**, not filed — the sentence stating it is normative and names both readers |
| `report_by` under `resample` | Filed to **H4**, and its entry **re-scoped**: live on E1, E2, E4, E6, C1, C2, C3, not on C1–C3 alone. A filing's claims go stale like any other comment |
| `BaseTemplate.field_convention`, `max_failed_fraction`'s truncation status | Untouched, and still unassigned |

---

## What did not survive

| Claim, and where | Verdict |
|---|---|
| *"`ArtifactIO.__init__` takes `step_dir`, `input_dir`, `run_dir`, … and no `output_dir`"* (`H8-SCOPING.md` § 2 and § 9 task 3) | **The substance survives; the name does not.** There is no `ArtifactIO` in `src/`. The class is `StepIO` in `artifacts.py`, and the parameter list is otherwise as measured |
| *"`io.reuse_from` itself: the relative-path rules `io.write`/`read_upstream` already enforce (no absolute, no `..`, no symlink escape)"* (`H8-SCOPING.md` § 9 task 5) | **False for `read_upstream`, and this is the sharpest correction here.** Measured by live probe: `read_upstream` returned the contents of both `../../secret/x.json` and an absolute path. Only `io.write`/`path`/`exists`/`append` go through `_resolve`. There was no rule to inherit — task 5 builds it, for all three readers |
| *"`run_id` in the path form disagreeing with the record"* as a refusal (`H8-SCOPING.md` § 9 task 8) | **Backwards.** In the path form the `run_id` is *read back*, so there is nothing to disagree with. The real fault is in the **relative** form: a directory under `output_dir` whose basename and whose record's `run_id` differ |
| *"After H8a: 6 with no remaining core-side blocker, 6 executable; C1/C2/C3 blocked on `report_by`-under-`resample`"* (`H8-SCOPING.md` § 6.3) | **Does not survive, and it is the third appearance of one inconsistency.** Measured: E1, E2, E4 and E6 declare the identical `resample` + non-empty `report_by` combination, and the gap costs a *recorded column's* interval — so charging C1–C3 with it while leaving E1 and E2 inside the count of three repeats exactly what the 2026-08-20 correction documented. Under the record's own applied standard the projection is **8 of 8 transplantable**, with E3 unmeasured; under the other standard today's figure is **1**, not 3. § The payoff reports four figures instead |
| *"H8 builds nothing that runs at `validate`"* (`H8-SCOPING.md` § 6.1) | **Survives**, and Decision 11 gives it the reason the scoping did not: the locator is a parameter and core never inspects the body of user Python |
| *"`io.read_upstream`'s bare `KeyError` … is CLOSED; H8a inherits a coded refusal for an unregistered suffix and should not mint a second one"* (`H8-SCOPING.md` § 7) | **Survives**, re-read at this commit: `_read` raises `ArtifactError` · `E-ARTIFACT-UNREADABLE` for a writer-without-reader suffix, and a suffix neither table knows reads back as bytes |

---

## What the scoping left unmeasured and this design had to assume

Distinct from § What could not be measured below: these are places where the design **acted** on
something the scoping did not establish.

- **The `execution` block's shape.** The scoping named it (*"the upstream's scopes are in its own
  `run.yaml`'s `execution` block"*) and did not measure it. Decision 4 rests entirely on it, so it
  was measured against `run_record._execution_block` rather than against § The two files' example —
  the residue is nil, and the measurement is recorded in Decision 4 rather than assumed.
- **Task 5 is wider than one tenth of this slice, and the plan author should size batches
  accordingly.** The scoping sized it against *"the relative-path rules `io.write`/`read_upstream`
  already enforce"* — a rule that does not exist. `read_upstream` and `read_condition` enforce none
  of it, so task 5 builds the helper, wires three callers, and repairs one § Errors row on top of
  `reuse_from` itself. The count stays 10 to match the scoping; the **weight** does not.
- **That `demo` does not write runs inside the repo.** Decision 1's containment refusal assumes it,
  and `demo` is unbuilt and H9's, so nothing could be measured. If H9 needs in-repo runs it changes
  Decision 1 with an argument rather than discovering the refusal.
- **That no user step reads an artifact through a `..` segment.** Measured over `tests/`, the four
  documents and `src/publishable/templates/` — which is every reader this repo can see, and not
  every reader that exists.

---

## What could not be measured

- **Whether E3, E4 or E6 has a dependency inside a step *body*.** No step of `growth_screen` exists.
  This is the same limit every § Executability entry names, and § The payoff's projection inherits it
  exactly as the "three executable" figure it corrects does.
- **E3's `data`/`statistics` blocks.** Its section carries none, so "E3 inherits E1's blocks" is an
  inference from the analysis's own convention and is labelled one.
- **Whether an upstream written by a *future* schema version should be readable.** Decision 3 refuses
  anything but the version this build writes, which is the only version that exists; the forward
  question is real and unanswerable today.
- **What `diff` prints for an upstream that differs** — H8b's, and `H8-SCOPING.md` § 10 already
  records that `diff`'s row set under an unchanged apparatus was not derivable either.

---

## Rulings from the controller, recorded so the plan author sees why two decisions are shaped as they are

Both were issued on 2026-08-20, after the first draft of this design and before it went to plan. The
draft is uncommitted and unread downstream, so this is a revision rather than a retro-edit of a
published claim.

### Ruling 1 — Decision 5's name rule is **containment**, and separators stay legal

The draft's phrasing ("a relative path inside the step's directory") permitted separators but did not
**say** so, and a plan author sizing task 5 from it could have built a rule refusing them.

*Grounds, as ruled.* § Steps and artifacts documents separators as legal by design — *"A `name` is a
relative path, not only a filename"*, *"only the name's last component is examined"* — and gives
**`programs/gpt-4.1__seed29.json`** as a worked legal name; § Lineage's own downstream example reads
`f"programs/{...}__seed{seed}.json"`. A rule refusing separators would break a documented example.
And the finding must be classified correctly: `name` comes from the user's own step, which can
`open()` anything, and core **never inspects the body of user Python** — so this is a containment
rule (an artifact read resolves inside the run it names, and a typo'd `..` fails loudly instead of
returning something unrelated), **not** a sandbox boundary, and must not be written up as one.

*What it costs if wrong.* If containment is the wrong rule, a step that deliberately reached a
sibling directory through `../` loses a path that was never sanctioned. If the rule had instead been
declined, the cost is the state measured today: a `..` typo reads an unrelated file and the record
calls it an artifact. The over-refusal failure mode — a helper that refuses every separator — is
caught by Fixture N's **positive control**, which is why that control is not optional.

*Does it force a change to another decision?* **No.** One clarification was owed and is now in
Decision 5: an absolute **locator** stays legal (Decision 1) while an absolute **name** is refused,
because a locator addresses a run — a location the config is allowed to state — and a name addresses
an artifact within a run, whose location is derived from the step it belongs to. Decisions 1, 2, 3,
4, 6, 7, 8, 9, 10 and 11 are unchanged, and the task count stays **10**.

### Ruling 2 — the `report_by` measurement belongs in the record, and no count is to be tidied

*Grounds, as ruled.* The measurement changes a correction published the same day: the gap is live on
seven of nine configs while the record charges it to three, which puts E1 and E2 inside the surviving
"three" carrying the same dependency E3/E4/E6 are excluded for. The measurement lives in this design
(§ What the record still gets wrong, with both measurements and how each was taken) and the
controller carries it into the feasibility analysis and `CLAUDE.md`.

*What it costs if wrong.* If the seven-of-nine reading is wrong — the way it could be wrong is if a
`report_by` level block did not in fact carry recorded-column entries, which the direct
`summarize_step` call rules out — then a live gap is named against four configs that do not have it,
and H4 sizes a slice too large. That is the cheaper direction: the expensive one is a fifth number
minted to make the table look consistent, which is the failure both this ruling and the correction it
follows exist to stop.

*Explicitly not re-opened, per the ruling:* Decision 2's injection and its zero readable fields, and
Decision 7's `upstream: []` on `input_manifest_changed`'s precedent rather than `apparatus: null`'s.
And the dropped mutation stays dropped and stays **stated**: `output_dir → run_dir.parent` cannot
differ in any reachable state, so it is foreclosed structurally instead of tested, and recording a
foreclosed proxy is worth more than a mutation that proves nothing.
