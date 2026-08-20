# H7d Part B — the apparatus: gate and stop — design

**Goal:** a run whose apparatus moves under it stops, says so, and keeps the record of the period
that was certified. Part A observes and records; Part B is the half that can end a run. It compares
each condition's facts against that condition's own first *answered* observation, stops the plan on
a change, distinguishes an apparatus that **moved** from one that became **unreachable**, gives
`EXIT_EXTERNAL` its first reader, and closes the `run_status` contract that lets a truncated plan
call itself `completed`.

**What it delivers, stated honestly. Part B unblocks ZERO configs, and the only direction it can
move a count is down.** No config in [the feasibility analysis](../../feasibility-llm-growth-studies.md)
declares an `apparatus_probe` a real plugin backs — the declaration is a **template** attribute and
the template those measurements substitute is `generic`, which declares none. **Six with no
remaining core-side blocker and three executable both stay exactly where H4b-1 left them.** Part B
retires no refusal; it mints one (`E-APPARATUS-CHANGED`) and it converts one shipped exit code from
1 to 5. What it is worth instead is at § The payoff, and it is not a count.

---

## The measurement this rests on, and why it was re-taken

[`H7d-SCOPING.md`](../H7d-SCOPING.md) was measured against `0faa2e3` — **before Part A existed** —
and its appended correction already records one claim that did not survive a same-week re-read.
Part A then merged **17 tasks** that Part B builds directly on: `apparatus.py`, `Apparatus`,
`Observations`, `Observer`, the ledger, `provenance.apparatus`, five error codes and one warning.
`CLAUDE.md`'s rule is that a scoping expires and a spec does not, so **every build claim below was
re-measured against `main` at `290634e` on 2026-08-19**, by running rather than by reading, and each
says how. Where the scoping or Part A's routing disagrees with the code, the code wins and
§ What did not survive the re-measurement says so.

### Measured on 2026-08-19 against commit `290634e`

Four end-to-end runs through `main(["run", …])`, each with a project-local template declaring
`apparatus_probe`, a synthetic installed distribution registering it, and a probe counting its own
calls in a file — the scoping's Fixture P shape, inherited from Part A's shipped tests. Two
conditions (`sweep.grid` over `instrument.model`), 5 seed repeats, one repeat-scoped step, so
**10 executions planned** and the run-start round is **2 calls**.

| What was run | What happened |
|---|---|
| A probe returning `model_revision: "r1"` for two calls and **`"r2"` from the third on** | **exit 0**, `status: completed`, `run.yaml` written, `latest` created, `provenance.apparatus.facts` records **`r1` for both conditions** while **all ten `pre_execution` ledger lines say `r2`**, and `hash` is the digest of the `r1` mapping. A publishable-looking record whose own ledger contradicts it |
| A probe **raising** on its fourth call (mid-plan) | **exit 1**, `E-APPARATUS-RAISED` on stderr, **no `run.yaml`**, no `status:` byte, `latest` uncreated, the ledger's 3 lines and the one completed execution's `units.parquet` and `executions.jsonl` line preserved. One execution paid for, the run record lost |
| A probe **omitting a declared key** on its fourth call | Identical shape: exit 1, `E-APPARATUS-FACT-MISSING`, no `run.yaml`, one execution paid for. So all five `APPARATUS_CODES` lose the record mid-plan, not only the raise |
| The shipped `test_max_failed_fraction_is_measured_against_the_test_partition` fixture, re-driven and read back | The plan stopped at **2 of 5** executions, **every execution `completed`**, and `run.yaml` records **`status: completed`** with **exit 0** — a truncated plan calling itself complete, with no apparatus involved at all |

Three further measurements, each with its control:

- **`EXIT_EXTERNAL = 5` is defined in `diagnostics.py` and read by nothing** in `src/` or `tests/`
  — re-confirmed at `290634e`, agreeing with the scoping's appended correction and with Part A's
  filing. Control on the same file list: `EXIT_PARTIAL` finds `cli.py`, `test_cli.py` and
  `test_acceptance.py`.
- **`E-APPARATUS-CHANGED`, `E-APPARATUS-MOVED`, `StopSignal` and `stop_reason` are free
  identifiers** across `src/`, `tests/`, the four documents and `CLAUDE.md`. Control on the same
  list: `E-APPARATUS-RAISED` finds four files. The file list was filtered; no sweep's output was.
- **`limits` is a closed key set.** A config declaring `limits.allow_apparatus_change: true` earns
  `E-CONFIG-KEY-UNKNOWN` through `validate_config`; the control without that key reports nothing.
  This is the shipped half of Decision 7.
- **`len(plan) == len(results)` on a run that is not truncated**, measured by direct call over a
  plan carrying a `run` step, a `condition` step, a fold-repeat step and a `summary` step with a
  mixed status set: 8 and 8. Structurally too — `execute_plan` appends one `ExecutionResult` per
  loop iteration, unconditionally, after its per-execution `try`. This is the literal Decision 5
  rests on and it is the one most dangerous to guess.
- **`max_failed_fraction: 0.2` is materialized into every generated config** (`materialize.py`), so
  the truncation guard is armed in every end-to-end test — and yet the shipped tests asserting
  `EXIT_PARTIAL` are **not** truncations, because a step whose every execution raises is never
  classified as *recording* and so trips nothing. It is what makes Fixture T's two arms the whole of
  that guard's observable surface here, and it is measured rather than assumed.
- **`apparatus.py` reads nothing about `batch`**, and `replication.py` reads nothing about the
  apparatus; the `batch`-versus-`nondeterministic` wire the scoping measured (`W-REPL-DETERMINISTIC`
  reads **step declarations**) is untouched by Part A.
- **Part A shipped the "no `validate` path calls a probe" pin** — verified:
  `test_no_validate_path_calls_a_declared_probe` in `tests/test_validate.py`, whose probe writes a
  flag file **and then raises**, asserting the flag's absence **and** an exact empty findings set as
  the control that must report. It is not Part B's, and Part B adds nothing to it.

No production code ships from this document, and every claim in this section is perishable in the
way `CLAUDE.md` says a build fact is.

---

## Decisions

Fourteen, each with its grounds and what it costs if wrong. Where one contradicts the scoping or
Part A's routing, it says so and shows the measurement.

### 1. What "a fact changed" means — the first *answered* observation, per condition, per fact

**Ruling.** For each `(condition, fact)` pair, an observation is compared against the **first
answered** value for that pair — never against the previous observation, never against another
condition's. The four cases, and only the first fails:

| Transition | Verdict | Why |
|---|---|---|
| `value → different value` | **fails** | § The apparatus core can only observe: *"`"LOT-88231" → "LOT-90114"` is two states and fails"* |
| `null → value` | passes, and the value becomes the pair's first answered | *"that fact becoming available"* — an apparatus that never answered can never contradict itself |
| `value → null` | passes; the first answered value stands | *"becoming unavailable"*. Failing on it would make an unevenly-reported field more dangerous than no field at all |
| the key is **absent** from a later call | passes, and nothing is compared | `reference.md`'s own absent-versus-`null` convention — absent means *nothing was asked for*, `null` means *attempted and came back empty*. A **declared** key's absence is already `E-APPARATUS-FACT-MISSING`, Part A's, so the only absence reaching the gate is an undeclared fact's |
| `value → null → different value` | **fails** | This is what makes *first answered* a different rule from *most recent*, and it is the reason the rule is stated that way in the document rather than as "the previous observation" |

**Grounds, and it needs no new mechanism.** `Observations._first_answered` — shipped in Part A — is
already keyed by `(condition_key, fact)` and already updates **only** when the pair has no answered
value and the incoming value is not `None`. That is the rule above, already built for the record's
sake; the gate reads the same mapping rather than keeping a second one, so `provenance.apparatus.facts`
and the gate can never disagree about what a fact was pinned to. § The apparatus files says `facts`
is *"the first answered observation of each fact — what the gate compares against"*, from which the
single-authority reading follows.

**Per condition, never across.** § The apparatus core can only observe: *"facts are recorded per
condition and the gate is per condition — a deployment is compared against its own first
observation, never against another condition's"*, because a probe **may** read a swept parameter and
usually must. Fixture G3 is the pin, and it is not a hypothetical: Part A's shipped swept-fact test
already runs two conditions whose `model_revision` differs *by design*.

**Cost if wrong.** Comparing against the most recent observation would let an apparatus that
answered `A`, went quiet, and came back as `B` pass — the exact drift the gate exists to catch, and
the one a long run is most likely to see. Comparing across conditions would fail every sweep across
apparatus, which is the normal case § The apparatus core can only observe describes.

### 2. `E-APPARATUS-CHANGED`, and what its message may name

**Ruling: one new code, `E-APPARATUS-CHANGED`, raised where the comparison happens. Its message
names the condition key, the fact name, and **both values** — `calibration_id: CAL-2026-07-19 →
CAL-2026-08-02` — in the shape `diff`'s own apparatus row prints.**

**Grounds.** A fact value is contracted non-secret and non-identifying (*"a rule rather than a
convention"*), and Part A's `check_facts` **refuses** a fact value that equals or contains a
declared credential before any value is recorded — so by the time the gate sees a pair of values,
core has already established that neither is a credential it read. The diagnostic still renders
through a credential-bearing `Collector`, so a value core did not read but a plugin embedded is
redacted on the way out; the two mechanisms are Part A's and are reused, not re-derived. A message
naming neither value would send a reader to the ledger to answer *what moved*, which is the one
question a stop must answer on its own.

**Cost if wrong.** A message naming only the fact makes the operator diff two JSONL lines by hand at
the moment they are least inclined to. Naming a value that *is* a credential is the failure class
this repo has hit four times — which is why this decision rests on Part A's refusal rather than on
a fresh judgement about what a fact value can hold.

### 3. Where the stop happens, and the order the observation is written in

**Ruling: the stop is a `break` in `execute_plan`'s loop, on `max_failed_fraction`'s existing
precedent — the one shipped mechanism for "the run stops where it stands."**

**One seam, not two.** `Observer.observe_round` **raises** a `ContractError` for both faults — which
is what the shipped `observe_once` already does for an unreachable probe, and what the gate does for
a moved one — and `execute_plan`'s loop catches `ContractError`, and for **exactly**
`{E-APPARATUS-RAISED, E-APPARATUS-CHANGED}` records the reason on `StopSignal` and breaks. Every
other code, the four of Decision 9 included, is **re-raised** and keeps Part A's containment path
byte for byte. Stating it this way matters because the alternative — a gate that returns a verdict
while the unreachable path raises — is two mechanisms over one decision, neither one's mutation
visible from the other's site, and it is how Decision 9 would drift into being a separate assertion
about the code rather than a consequence of one line of it. So "stops rather than raising" means
**does not escape to `command_run`'s containment**, which is what the mutation *raise instead of
stopping* actually tests.

**Inside one probe round, the order is fixed and every step of it is load-bearing:**

```
check_facts  →  append_observation  →  Observations.record  →  the gate compares  →  stop
```

**Grounds, clause by clause.**

- `check_facts` **first**, unchanged from Part A's ruling: a credential-carrying fact is refused
  before a byte reaches the ledger.
- `append_observation` **before** the comparison, because § The apparatus files requires that
  *"a run that failed on a moved apparatus still shows the evaluable earlier period"* and § The
  apparatus core can only observe that *"the ledger keeps both observations"* — **both**, which
  means the moving observation is on disk. A gate that stopped before appending would record the
  earlier period and lose the evidence of what ended it.
- `record` **before** the comparison, so the moving call is counted in `unobserved.total_probes` like
  any other probe. It was a probe; the counts are a census of calls, not of agreements. Because
  `_first_answered` never overwrites an answered pair, this ordering cannot change the value the
  gate compares against — which is why the discriminator for this clause is a **count**, not a
  value.
- The gate **last**, and it stops rather than raising. A raise reaches `command_run`'s Part A
  containment and ends the command with no `run.yaml` — measured above, one execution paid for and
  the record lost, which is `CLAUDE.md`'s named habit and the thing this slice exists to stop doing.

**What survives a stop, stated so a reader knows what to look for.** `run.yaml` with a `status`
byte, `latest` repointed, `apparatus/probes.jsonl` holding every observation **including the moving
one**, `executions.jsonl` holding one line per execution that ran, each execution's own artifacts,
`sweep.yaml`, `allocation.json` and the input manifest. What a reader can tell about *where* the run
stopped: `executions.jsonl` is short of `sweep.yaml`'s plan, the ledger's last line carries the
observation that ended it, and the diagnostic names the fact and both values. **What is deliberately
not there is a `stopped_at` key in `run.yaml`** — the two files already say it, and a third statement
of the same fact is a third thing that can disagree.

**Cost if wrong.** Appending after the comparison loses the moving observation for exactly the run
that needed it. Stopping by raising keeps Part A's record loss in the slice whose job was to end it.

### 4. Which stops write a record — the code and the record move together

**Ruling: an apparatus stop continues into `command_run`'s record phase — the same path
`max_failed_fraction`'s `break` already takes — whenever at least one `ExecutionResult` exists. With
**no** results, nothing was paid for, and the command keeps Part A's shape: a redacted diagnostic,
no `run.yaml`, `latest` untouched.**

| Fault | Results | Record | `status` | Exit |
|---|---|---|---|---|
| Unreachable (a probe raised) | ≥ 1 | `run.yaml` | `partial` | **5** |
| Unreachable | 0 | none | — | **5** |
| Moved (a fact changed) | ≥ 1 | `run.yaml` | `failed` | **4** |
| Moved | 0 | none | — | **1** |

**Grounds for the unreachable case.** § What status means and § Exit codes and diagnostics state it
verbatim: *"A run that stops early can still be `partial`, and one thing produces that: core losing
the ability to certify the apparatus"*, with *"the exit code is nevertheless `5` rather than `3`"*.
Nothing here is inferred.

**Grounds for the moved case, and the tension is named rather than hidden.** § The apparatus core can
only observe is the only passage that states this case's outcome at all — *"A changed fact **fails
the run**"* — and it puts it on the *"same line as … an input file that moved"*, whose shipped
implementation, `E-INPUT-CHANGED`, sets `status = "failed"`, writes the record and exits 4. That is
the analogue to copy; the dirty code tree named in the same sentence is refused before a run
directory exists and has no shape to copy at all. **The tension, named rather than hidden.** § What status means'
`partial` table row admits *"stopped early with executions already recorded"*, which a
moved-apparatus stop literally is. **The principle this decision and Decision 5 share is the same
one — the passage that names the fault governs**, and where nothing names it, Part B rules nothing:
the apparatus section names a changed fact and states its outcome outright, so it governs here,
while nothing names truncation by the failure fraction as more than a member of a list, which is
why Decision 5 **declines to re-decide that case at all** and files it instead. The specific
statement wins over the general one: that row speaks about early stopping in general, while the
apparatus section speaks about **this** fault and says it fails the run. The substantive difference
is that an unreachable apparatus leaves core unable to certify anything further, while a moved one is
core having certified that the thing being measured through is no longer the thing the earlier
executions measured through — which is `E-INPUT-CHANGED`'s situation exactly, one dependency along.

**Cost if wrong.** If `partial` is the better reading for a moved fact, the loss is that a
reportable-in-part run is labelled `failed` and exits 4 rather than 3 — a label a reader can correct
from the ledger, which holds both observations. The reverse error labels a run `partial` while its
own record says its apparatus moved, which is the record § The apparatus core can only observe exists
to prevent.

**The zero-results corner, and why the code follows the record.** Exit 4's own row promises *"There
is a record of what happened"* and exit 3's promises one *"worth reading"*; with no `run.yaml` there
is no `status` byte anywhere, so a script keying on 4 would go looking for a record and find a
ledger it has no documented reason to read. So a moved fact that stops before anything executed
exits **1** — whose row already covers *"a `resume` whose hashes moved"*, the same fault at the same
emptiness. Exit **5** is not conditioned that way, because its row describes the *fault* — *"Something
outside the machine refused"* — rather than a record, and unlike 3 and 4 it is not marked
*"`run`, `draft`, `resume` only"*.

**This changes one shipped literal.** `test_a_probe_that_raises_is_a_redacted_diagnostic_at_run`
asserts `expect_exit=EXIT_WRONG` for a probe raising in the run-start round; under this ruling it
becomes `EXIT_EXTERNAL`. Its docstring says *"exit non-zero"* and stays true, and its no-`run.yaml`
and no-credential-anywhere assertions are untouched.

**Cost if wrong.** Writing a record over zero results would exercise the aggregate and statistics
phases over an empty results list — a path no fixture at `290634e` can reach and therefore one this
design will not put on the failure route. If it turns out to be safe, the cost of this ruling is a
missing `run.yaml` for a run that produced nothing, which loses no execution's worth of work. The
reverse error is a crash on the failure path, which loses the run.

### 5. `run_status`'s contract — widened for the apparatus, and **not** re-decided for the neighbour

**Ruling: `run_status(results, *, planned=None, stop=None)`. `stop` is a closed vocabulary of three
reasons. Two of them decide the status outright — `apparatus_unreachable` → `partial`,
`apparatus_changed` → `failed`. The third, `max_failed_fraction`, is **threaded and deliberately
mapped to today's fold over the results**, so that guard's observable behaviour is **unchanged by
this slice**, including the all-completed truncation that reports `completed` at exit 0. When
`planned` is given, `len(results) < planned` with `stop is None` is a **core defect** and raises
rather than folding, on `E-RUN-CFG-MISSING`'s precedent for asserting about core's own callers.
`execute_plan` reports the reason through a small mutable `StopSignal` the caller constructs and
passes — a defaulted keyword, exactly as `credentials` and `observer` already are, so no existing
call site changes and no test line is deleted.**

**Why the third reason is threaded at all, since it changes nothing.** It is what makes the
truncation assert sound: without a reason on that path, every `max_failed_fraction` stop would trip
a guard meant to catch core truncating a plan for no recorded reason. So the enum member **is** read
— by the branch that suppresses the assert and falls through to the fold — and the fall-through is a
documented no-op rather than an omission. It also leaves the change its owner may want as **one
mapping entry**, with the plumbing already measured.

**Grounds for not re-deciding it, and the first is the one that settles it.** The current behaviour
is **pinned with its reason written down**: `test_max_failed_fraction_is_measured_against_the_test_partition`'s
docstring argues it — *"`max_failed_fraction` is a fraction of UNRESOLVED units, not of raised
executions, and `run_status` reports `completed` even though the plan stops short — the guard and
the execution-level exit code are two different mechanisms."* That is deliberately pinned behaviour
with an argument attached, not an unnoticed defect, and **a slice about something else editing both
a shipped assertion and the argument justifying it is indistinguishable in the record from weakening
a pin to pass** — the move this project has been burned by. Second, **`max_failed_fraction` is not
this slice's guard**: widening `run_status` to carry *apparatus* stop reasons is squarely H7d's,
while re-deciding what the failure fraction reports changes **every run that declares it**, apparatus
or not, and belongs to whichever slice owns that guard. Inheriting a neighbouring mechanism's status
semantics is scope creep even when the new answer is better.

**What the measurement therefore buys, and it is not a code change.** The finding stands in full — a
truncated plan reporting `completed` at exit 0 is reachable, reached and pinned, and § What status
means describes it in none of its rows (Decision 5's table below) — and Part B's contribution is that
the question is **filed with the check its owner must make**, rather than either fixed by a slice that
does not own it or left in a scoping's prose.

**The document contradiction, which stays partly open, stated so nobody reads task 1 as closing it.**
Measured by reading the section in full:

| Passage | What it says a truncated run is |
|---|---|
| The `status` table's `partial` row | *"…or it **stopped early with executions already recorded** — either way, a record worth reading"*, at exit `3` |
| The `failed` paragraph | *"Three things produce it … `limits.max_failed_fraction` being exceeded stops the run where it stands"* |
| The paragraph after it | *"A run that stops early can still be `partial`, and **one thing** produces that"* — the apparatus, exclusively |
| The `completed` row | *"Every execution in the plan completed"* |
| The code at `290634e`, and after Part B | `completed` at exit **0** for an all-completed truncation — which **no row above describes**: `completed`'s row is false of a plan two of whose five executions ran, and `partial`'s row carries exit 3 |

Task 1 makes the section consistent **about the apparatus** and touches the `max_failed_fraction`
clause not at all. The remainder — a state no row describes, under a clause the code contradicts — is
**filed**, and the filing says what its owner must reconcile.

**Cost if wrong.** If `len(plan)` were not the count a clean run's `results` reaches, the assert
would fire on healthy runs — the worst failure a status guard can have. That is why it was measured
by direct call over a fold-plus-summary plan with a mixed status set (8 and 8) **and** argued
structurally from `execute_plan`'s unconditional append, rather than inferred from a test helper that
derives its number from the config. And if the narrow ruling is wrong — if `max_failed_fraction`
genuinely belonged here — the cost is that a documented contradiction outlives this slice by one
more, visible in a filing, which is the recoverable direction. The unrecoverable one is a slice about
the apparatus having quietly changed what every run declaring a failure fraction reports.

### 6. `EXIT_EXTERNAL`'s reader, and the precedence

**Ruling: `cli.command_run`'s final mapping gains one branch — an `apparatus_unreachable` stop
returns `EXIT_EXTERNAL` regardless of the status it wrote. Nothing else in this slice reads the
constant, and nothing else in the exit-5 family is built here.**

**Grounds.** § Exit codes and diagnostics states the precedence outright: *"`5` is separate from all
of them because it is the class you retry, and the others are not — so when both apply, `5` wins"*,
with the worked case *"writes `status: partial` and exits `5`"*. The constant ships and is read by
nothing (measured, at three commits now), so what is owed is a reader and a pin — **narrower than
the scoping states, and Part A's correction already said so.** The pin must assert the status byte
and the exit code **separately**: a build that derived the code from the status alone would return 3,
and an assertion on either one alone cannot see it.

**Not built here, and named so they are not folded in:** exit 5 for *"a missing credential"* and for
*"a clone or `uv sync` that failed"*. Measured: a missing declared credential is `E-CRED-MISSING` /
`E-CRED-PARAM-MISSING` at `validate`, exiting **1** today, and the clone case belongs to `reproduce`,
which prints *specified but not built*. Both are § Exit codes' own words about commands this slice
does not touch, routed to H9 rather than fixed here.

**Cost if wrong.** Returning 3 for an unreachable apparatus tells a script to archive a run whose
apparatus was offline for an hour — the exact confusion the two codes exist to prevent.

### 7. No policy knob, and what the pin can and cannot prove

**Ruling: nothing configurable can permit a changed fact. Part B adds no field, and the pin is two
arms: (a) an invented knob under `limits` is refused by the shipped closed-key check —
`E-CONFIG-KEY-UNKNOWN`, measured, with a clean control — so a config cannot even *express* one; and
(b) the gate stops a run whose `limits` block is at its most permissive on every key that exists
(`max_failed_fraction: 1.0`, a huge `max_executions`, the floor at its lowest).**

**Grounds.** § The apparatus core can only observe: *"A changed fact fails the run, with no policy
knob … a flag to permit it would only ever be used to paper over the moment a result stopped being
interpretable."* `CLAUDE.md` § Invariants makes the same point structurally: **operation commands
take paths and nothing else**, and a mode gets its own command name — so there is no flag surface to
add one to either.

**What this costs, said plainly rather than sold as free.** An operator who knowingly changed the
apparatus mid-run — a firmware push they authorized — cannot finish the run. That is correct and it
is the *point*: the two periods are two datasets, the ledger keeps both, and the route is a second
run joined in a `study`. The alternative is a flag that exists only for the case where the result
stopped being interpretable.

**What the pin cannot prove**, stated because a test whose name claims a guarantee is a named trap
here: neither arm can prove that no *future* knob will be added. Arm (a) pins the schema, arm (b)
pins that today's most permissive config does not soften the gate. Nothing can pin the absence of a
field nobody has written.

### 8. `batch` and the apparatus stay independent

**Ruling: Part B changes nothing about `batch`, and ships the test that says so. Two runs identical
but for `replication` — `n` seed levels versus one `batch` level of the **same** `n` — over the same
probe produce the identical ordered `(phase, condition)` ledger sequence, the identical
`provenance.apparatus.facts` and the identical `hash`; and a moving fact stops both at the same
execution index.**

**Grounds.** `CLAUDE.md` defines `batch` as *"the state of the apparatus it measures through"*, which
is precisely the sentence that invites someone to wire the two together. The scoping measured them
independent by running both arms — the live wire is `W-REPL-DETERMINISTIC`, which reads **step
declarations** — and Part A left that untouched (`apparatus.py` names `batch` nowhere;
`replication.py` names the apparatus nowhere). Part B is the first slice that can stop a run over
apparatus state, so it is the slice that owes the pin.

**Equal `n` is load-bearing and belongs in the design, not only in the plan.** With unequal `n` the
two arms have different execution counts, so their ledgers differ in length for a reason that has
nothing to do with the apparatus — and a fixture whose two arms differ for an uninteresting reason
cannot see the interesting one.

**Cost if wrong.** Coupling them would make a `batch` level change what the gate compares, which
turns "measure the drift that remains when identity held still" into "permit identity to move" —
the policy knob of Decision 7 arriving through the repeat vocabulary instead.

### 9. The other four apparatus codes keep Part A's refusal — filed, not fixed

**Ruling: `E-APPARATUS-RETURN`, `E-APPARATUS-FACT-TYPE`, `E-APPARATUS-FACT-MISSING` and
`E-APPARATUS-FACT-CREDENTIAL` continue to end the command with a redacted diagnostic, no `run.yaml`
and exit 1, mid-plan as at run start. Part B does not convert them into record-preserving stops. The
cost — executions paid for whose run record is lost — is **filed** in `spec-defects.md`, unassigned,
with the route stated.**

**Grounds.** These four are the plugin and the template disagreeing about what the probe supplies —
a fault in the declarations, not a fact about the world. `partial` is reserved by § What status means
to **one** cause and `failed` to three; giving these four a status would mint four record shapes no
document names, on the failure path, in a slice whose review is scoped for stops. Their route out is
a `reference.md` sentence siting a fact-contract failure at run time, which is a document change
nobody has argued for yet.

**Measured, so the filing is concrete rather than theoretical:** a probe omitting a declared key on
its fourth call gives exit 1, `E-APPARATUS-FACT-MISSING`, no `run.yaml`, with one completed
execution's artifacts and ledger lines on disk.

**Cost if wrong.** One execution's record is lost on a run whose plugin misbehaves mid-run — bounded,
and visible in the ledger. Converting them here would be four undocumented statuses instead.

### 10. A stop never retries

**Ruling: neither stop re-probes, re-checks, or re-executes anything. The `break` is the last thing
the loop does.**

**Grounds.** A retry is another authenticated, metered call against an apparatus already known to be
in trouble, and § The apparatus core can only observe makes restarting under a changed apparatus a
**new run** rather than a continuation — `resume` refuses it too. Part A retries nothing and states
the rule; Part B is where it becomes enforceable, so it is restated as a decision rather than
inherited silently.

**Cost if wrong.** A retry on an unreachable apparatus doubles the spend at the moment the run is
already lost, and a retry on a moved one asks the same question core has already answered.

### 11. The gate cannot fire at `validate`, and cannot fire in the run-start round

**Ruling: no new guard is added at `validate` — Part A's flag-file pin already holds it, verified
above — and the design records **why the run-start round can never trip the gate**: it makes exactly
one call per resolved condition, so no `(condition, fact)` pair has a prior observation to disagree
with. Every gate stop is therefore a `pre_execution` stop.**

**Grounds and the trap it avoids.** This is a claim about reachability, and `CLAUDE.md`'s rule is
that **a safety argument is a claim needing a mutation** — Part A's only Critical came from an
unreachability claim a three-line fixture falsified. So this claim is not permitted to live in a
comment: it is expressed as a **test**, asserting that a probe returning a *different* value on each
of its run-start calls (two conditions, two values) completes the round and stops nothing, because
the two calls belong to different conditions. That fixture makes the claim happen instead of
asserting it.

**Cost if wrong.** If a future round ever probes one condition twice before the first execution, the
gate would fire during setup and the test above is what would fail — which is the outcome wanted,
rather than a comment nobody re-reads.

### 12. `sweep.yaml` is what a reader compares the truncated plan against

**Ruling: nothing new records the planned execution count. `run_status`'s `planned` argument is
`len(plan)`, computed at the call site from the plan already in scope, and nothing writes it into
`run.yaml`.**

**Grounds.** `sweep.yaml` already records the resolved conditions and repeats a reader derives the
plan length from, and `executions.jsonl` records what ran; a third number in `run.yaml` would be a
third thing that can disagree with the other two. `CLAUDE.md` § Invariants' three-hashes rule is the
same instinct one level up: a derived number recorded beside its inputs is a maintenance obligation,
not a fact.

**Cost if wrong.** A reader wanting "how many executions were planned" computes it from `sweep.yaml`
rather than reading it. If that proves genuinely hard, the route is a `run.yaml` key with a document
row — not a key added quietly here.

### 13. The stop reason is core's own vocabulary, not a document surface

**Ruling: the three stop reasons are internal identifiers on a core construct. They are not written
into any artifact, not exported from `publishable`, and not named in the four documents. What the
documents describe is the **status** and the **exit code**, which is what a reader and a script see.**

**Grounds.** `CLAUDE.md`: everything a user writes against is imported from `publishable` and
§ The importable surface is the enumerated list — adding a name to it for a value nobody imports
would be a surface with no reader. The statuses and codes already have rows.

**Cost if wrong.** If a later slice (`resume`, `report`) needs to know *why* a run stopped, it reads
the diagnostic's code and the status, which are the documented facts, or the enumeration becomes a
document surface then, with the row it would owe.

### 14. One diagnostic per stop, printed through a fresh redacting `Collector`

**Ruling: a stop prints exactly one finding — `E-APPARATUS-CHANGED` or `E-APPARATUS-RAISED` — through
a **fresh** `Collector` carrying the `credentials` mapping `command_run` already bound before the
roster call. Never appended to `c`, which has already been rendered and printed.**

**Grounds.** Part A's shipped shape, cited rather than re-derived: appending to the printed collector
re-prints every earlier finding and inflates the counts line, which is how Part A's own review caught
a related defect (a second render printing "3 problems" rather than 4). `credentials` is **reused,
never recomputed** — a second derivation is a second answer, which is the reasoning behind three
credential leaks on this project.

**Cost if wrong.** A recomputed credential set is a set that can differ from the one `redact` uses,
which is exactly how Part A's whole-branch Major 2 arose — two mechanisms over one value set
disagreeing.

---

## Out of scope, with the route

| Excluded | Route |
|---|---|
| Making `E-APPARATUS-RETURN` / `-FACT-TYPE` / `-FACT-MISSING` / `-FACT-CREDENTIAL` record-preserving stops | **Filed**, unassigned (Decision 9). Decidable once `reference.md` sites a fact-contract failure at run time |
| Exit 5 for *"a missing credential"* and for *"a clone or `uv sync` that failed"* | **H9** (`reproduce`). Measured: a missing declared credential exits 1 today. Named so it is not read as this slice's gap |
| `resume`'s refusal of a changed apparatus; `dry-run`'s probe phase and its cost-ordered codes; `reproduce`'s `apparatus.expected.json` | **H9**, per the spine design § The hardening slices. All unbuilt — every claim here about them is a **spec claim**, read, never a build fact |
| `freeze`'s re-probe; `diff`'s `apparatus DIFFERS` row; `report study.yaml` cross-checking `provenance.apparatus.hash` | **H8**, same section, same unbuilt status |
| `resume`/`dry-run`/`freeze` hooks shipped "as callables with tests" | **Declined**, on Part A's Decision 14: the calling slice builds its own call site against `apparatus.py`'s public functions. `EXIT_EXTERNAL` gaining a reader here removes one member of the family that argument rests on; the argument stands on the rest |
| **Narrowing** the per-execution probe — the route Part A left open to Part B *"if `C` calls before a condition-less execution proves too expensive"* | **Declined here.** No evidence of the cost was produced, and "before every execution" is stated at two sites, one argument-bearing. It stays available to a later slice **with the `reference.md` change it requires** |
| A `stopped_at` key, or a planned-execution count, in `run.yaml` | **Refused** (Decisions 3 and 12): `executions.jsonl` and `sweep.yaml` already say it |
| A policy knob permitting a changed fact | **Permanent refusal**, § The apparatus core can only observe. Decision 7 is the pin |
| Core inspecting a probe's body to decide whether it will reach the network | **Permanent refusal.** Core validates declarations and verifies effects |
| An apparatus **hash** among `HASHED_TREES` or in `hashes.py` | **Permanent refusal**, and untouched: Part A sited `apparatus_hash` beside the mapping it hashes precisely because it is not a fourth hash |
| `BaseTemplate.field_convention`, declarable on a shipped class and read by nothing | **Unassigned** in `spec-defects.md`. Not adopted: folding it in would make this slice the owner of a gap it did not find |
| `io.reuse_from` | **Unassigned**, not apparatus — and it is what keeps six configs non-executable, so no sentence here may imply otherwise |
| Holdouts and folds inside cells | **H3c-3** |
| An interaction, a dose-response ordering, a difference-in-differences | **Permanent refusal.** Contrasts do not nest; the route is a `summary`-step `Estimate` |

---

## The discriminating fixtures

**The constraints first**, because a later task may substitute only a fixture meeting all of them.
Part A had **six** prescribed mutations that could not discriminate and one assertion whose substring
agreed with either branch, so:

- **Every literal is computed here, in writing, from the design it tests.** Derived values (a hash, a
  facts mapping, an `unobserved` count) are **recomputed by the test** from the artifact it just
  read, never transcribed.
- **A fixture must separate every candidate reading, not two of them.**
- **A control asserting only an absence passes identically if nothing ran.** Every control below is
  paired with something that must report.
- **Every assertion is named against the mutation it catches.** An assertion true under both
  branches is stated as such rather than counted as a pin.

### Fixture P — the plugin, inherited

Part A's shipped shape: a scaffolded project, a **project-local** template declaring
`apparatus_probe` and `apparatus_facts`, and a synthetic **installed** distribution whose
`publishable.probes` entry point names a module whose probe counts its own calls in a file. **Each
fixture below needs its own module name**: two fixtures sharing one importable module name in one
test session get the first one's code, which silently swapped a raising probe for a moving one while
measuring this design.

### Fixture G1 — the four transitions, one condition, one run

**Design.** No `sweep` — one condition, key `"00"`. Four `seed` repeat levels and one repeat-scoped
step, so **4 executions planned**. `apparatus_facts = ["pinned", "appears", "vanishes"]`, and the
probe also returns an **undeclared** `sometimes`. By call, with the run-start round being call 1:

| Call | Where | `pinned` | `appears` | `vanishes` | `sometimes` |
|---|---|---|---|---|---|
| 1 | `run_start` | `"r1"` | `null` | `"L1"` | `"S1"` |
| 2 | before execution 1 | `"r1"` | `"A1"` | `null` | *absent* |
| 3 | before execution 2 | `"r1"` | `"A1"` | `null` | *absent* |
| 4 | before execution 3 | **`"r2"`** | `"A1"` | `null` | *absent* |

**Computed expectations.** The stop is at call 4, before execution 3 runs, so: **`executions.jsonl`
has 2 lines**; **`apparatus/probes.jsonl` has 4 lines**, the fourth carrying `pinned: "r2"`;
`run.yaml` exists with **`status: failed`**; the exit code is **4**; `latest` exists.
`provenance.apparatus.facts["00"]` is `{pinned: "r1", appears: "A1", vanishes: "L1", sometimes: "S1"}`
— every one a first-answered value. `unobserved` carries **three** entries, the declared facts only:
`pinned {null_probes: 0, total_probes: 4}`, `appears {1, 4}`, `vanishes {3, 4}`.
`W-APPARATUS-UNANSWERED` appears **exactly twice** — `appears` and `vanishes` — and **not** for
`pinned`, which is the control that must report. The diagnostic names `pinned`, `r1` and `r2`.

**Which assertion catches which mutation.** The ledger's **4 lines with `r2` last** is the only one
that discriminates append-before-stop. `total_probes: 4` for `pinned` is the only one that
discriminates record-before-stop. `facts["00"]` is **true under every ordering** — first-answered
never overwrites — and is stated here as a shape assertion, not as a pin for either ordering.
`vanishes` and `appears` passing is what discriminates the two transition mutations from each other,
by the fact **named in the message**, since both would otherwise stop at call 2 with the same code.

### Fixture G2 — first answered versus most recent

**Design.** One condition, three executions planned, one declared fact `flip`. Call 1 `"F1"`, call 2
`null`, call 3 `"F2"`. **Expectations:** the stop is at call 3 — `E-APPARATUS-CHANGED` naming `flip`,
`F1` and `F2`, `status: failed`, exit 4, **1 line** in `executions.jsonl`, **3 lines** in the ledger.

**Why it exists and why G1 cannot replace it.** Under a *most-recent* comparison G1 stops at call 4
exactly as designed — the mutation is invisible there. Under most-recent, G2's call 3 compares
`null → "F2"` and **does not stop**: exit 0, `status: completed`. Two branches, two different
outcomes, from the one shape the document's own wording distinguishes.

### Fixture G3 — the per-condition scope, from Part A's shipped shape

**Design.** Two conditions (`sweep.grid` over `instrument.model` with two levels) and a probe
returning the swept value it read as `model_revision` — Part A's shipped swept-fact test, re-driven
to completion. **Expectations:** exit 0, `status: completed`, `facts` holding **two different**
values keyed by the two condition keys, and **no** `E-APPARATUS-CHANGED` anywhere. Under a
cross-condition comparison the run stops at the second run-start call. This is also the pin for
Decision 11's run-start claim: two calls, two different values, nothing compared.

### Fixture U — unreachable, mid-plan

**Design.** One condition, four executions planned, a probe raising on call **4**. **Expectations:**
exit **5**; `run.yaml` written with **`status: partial`**; **2 lines** in `executions.jsonl`;
**3 lines** in the ledger — a failed probe appends nothing, so a build that appended for it gives 4;
`latest` exists; the diagnostic is `E-APPARATUS-RAISED`. **The status byte and the exit code are
asserted separately**, because a build deriving the code from `partial` returns 3 and no single
assertion can see that.

### Fixture Z — nothing paid for

**Two arms, one shape each.** A probe raising on call **1** (the run-start round): exit **5**, no
`run.yaml`, `latest` absent, ledger absent. A probe moving on call **2** — one condition, so call 2
is the first `pre_execution` — with the first execution not yet run: exit **1**, no `run.yaml`,
`latest` absent, **2 ledger lines**. This is the boundary Decision 4 draws, and the two arms are what
make the boundary observable rather than argued.

### Fixture T — the neighbouring guard, asserted **unchanged**

**Design.** The shipped `max_failed_fraction` fixture — a step that completes while recording nothing
for the test partition — re-driven after this slice. **Expectations, every one identical to today's
measured behaviour:** the plan stops at **2 of 5** executions with every execution `completed`,
`run.yaml` records **`status: completed`**, and the exit code is **0**. A second arm with a *mixed*
status set asserts **`partial`** and exit **3**.

**This is a regression fixture, and it is the one that keeps Decision 5 narrow.** Its job is to catch
a build that widened the status contract past the apparatus — the change Decision 5 declines and files
— rather than to pin a new behaviour. Both arms **must report**: a control asserting only that nothing
changed would pass if the guard stopped firing altogether, so each arm asserts the truncation
happened (`len(executions.jsonl)` short of `sweep.yaml`'s `execution_order`, the comparison the
shipped `_planned_execution_count` helper already makes) **and** the status and code it produced.

### Fixture K — the knob that cannot be written

**Two arms.** `limits.allow_apparatus_change: true` through `validate_config` earns
`E-CONFIG-KEY-UNKNOWN`, with the same config minus that key reporting nothing — the control that must
report is the refusal itself, and its absence in the control is what makes it attributable. Then
G1's run with every existing `limits` key at its most permissive still stops, with the same computed
line counts.

### Fixture B — `batch` independence

**Two arms, equal `n`.** `replication` as four `seed` levels, and as one `batch` level of `n: 4`,
over G1's own probe. **Expectations:** the ordered `(phase, condition)` ledger sequence, the
`facts` mapping and the `hash` are **identical** across the arms, and the stop lands at the same
execution index. Equal `n` is what makes the two arms comparable at all.

---

## The mutations, each with the assertion that catches it

Every row's two branches produce different observable results; where a mutation is blind, the row
says so.

| Mutation | Caught by |
|---|---|
| Compare against the **most recent** observation rather than the first answered | **G2**: exit 0 and `status: completed` against the asserted exit 4 and `failed`. G1 is blind to this one, deliberately |
| Fail on `value → null` | **G1**: the stop moves to call 2, giving 2 ledger lines and 0 executions against 4 and 2 — and the message names `vanishes`, not `pinned` |
| Fail on `null → value` | **G1**: same counts, message naming `appears`. The **named fact** is what tells this row from the one above |
| Compare a condition against another condition's first observation | **G3**: the run stops at the second run-start call instead of exiting 0 with two distinct recorded values |
| Compare an **undeclared** fact's disappearance as a change | **G1**: `sometimes` is absent from calls 2–4; a build treating absence as a change stops at call 2 |
| Gate **before** `append_observation` | **G1**: 3 ledger lines, the `r2` observation missing — the assertion nothing else can make |
| Gate **before** `Observations.record` | **G1**: `unobserved.pinned.total_probes` is 3 against the computed 4. A count, because every *value* assertion is true under both orderings |
| Raise instead of stopping | **G1**: no `run.yaml` and exit 1 — Part A's measured shape — against the asserted record and exit 4 |
| Map the unreachable stop to `failed` | **U**: the `status` byte is `failed` against the asserted `partial` |
| Return `EXIT_PARTIAL` for the unreachable stop | **U**: exit 3 against the asserted 5, while the status byte still reads `partial` — which is why the two are asserted separately |
| Drop the stop reason and let `run_status` fold over the results | **U**: every execution completed, so the fold gives `completed` and exit 0 against `partial` and 5 |
| Map `max_failed_fraction`'s stop to `partial` — the widening Decision 5 declines | **T**'s all-completed arm: `partial` and exit 3 against the asserted `completed` and 0 |
| Map `max_failed_fraction`'s stop to `failed` | **T**'s mixed arm: `failed` and exit 4 against the asserted `partial` and 3, which is also every shipped `EXIT_PARTIAL` truncation test's assertion |
| Suppress the truncation assert for **every** stop rather than for a **recorded** reason | **Blind end to end** and said so; the pin is the direct call below |
| Delete `run_status`'s truncation assert | **Blind end to end**, and said so: with every stop carrying a reason there is no reachable run that trips it. The pin is a **direct call** — a truncated results list with `stop=None` must raise — and it is named as a direct-call pin rather than dressed up as an end-to-end one |
| Probe once at run start instead of once per condition | Part A's shipped call-count contract, unchanged and re-run |
| Wire the gate to the `batch` level | **B**: the two arms' ledgers and stop indexes diverge |
| Read a permissive `limits` key as licence to continue | **K**: the run still stops, with G1's computed counts |

---

## Task decomposition — 11

**Documents first — 1**

1. **`reference.md` § What status means — made consistent *about the apparatus*, and no further**
   (Decision 5). The `failed` paragraph **gains** the moved apparatus and its **count phrase goes
   three → four**, because the `max_failed_fraction` clause **stays**: this slice does not own that
   guard, and deleting a clause to make a sentence tidy while the code still contradicts it would be
   making the document consistent by omission. The `partial` paragraph's *"one thing produces that"*
   is amended to name the apparatus-**unreachable** case precisely, which is what the code does after
   this slice. **§ The apparatus core can only observe states the outcome** a changed fact produces
   (`status: failed`, the record kept, the ledger holding both observations) where it says only
   *"fails the run"*; **§ Exit codes and diagnostics gains the one clause** Decision 4 needs — that
   the unreachable case exits 5 whether or not a record was written. `experimental-designs.md`
   § Mistakes core prevents' apparatus row and `design-principles.md`'s design-goal sentence are
   **checked, not changed**: both already say a change fails the run, and this slice makes that true.
   **What this task does NOT close, and must say so in its report:** the all-completed truncation
   remains a state no row describes, and the `failed` clause about the failure fraction remains one
   the code contradicts. That is task 11's filing, not a sentence this task may repair. First, so no
   code emits against an un-amended sentence.

**The gate — 3**

2. **The comparison** (Decision 1) on `Observations`, reading `_first_answered` rather than keeping a
   second mapping: the four transitions, per `(condition, fact)`.
3. **`E-APPARATUS-CHANGED`** (Decision 2) — the code, and the message naming the condition key, the
   fact and both values.
4. **The ordering chain** (Decision 3): `check_facts` → `append_observation` → `record` → compare,
   with G1's two ordering assertions as the pins.

**The stop — 3**

5. **`StopSignal` and the `break`** in `execute_plan`'s loop (Decision 3), on
   `max_failed_fraction`'s precedent, as a defaulted keyword so no existing call site changes.
6. **`run_status`'s contract** (Decision 5): `planned` and `stop`, the three reasons, the truncation
   assert, and `max_failed_fraction` threaded but **mapped to today's fold** — a documented no-op
   whose purpose is to keep the assert sound, pinned by Fixture T asserting the guard's behaviour is
   **unchanged**. **No shipped expectation and no docstring changes in this task**, which is the
   property that distinguishes it from the ruling it declines; the only literal this slice moves is
   task 8's.

7. **The record on a stop** (Decision 4): the record phase reached whenever a result exists, the
   zero-result arms keeping Part A's shape, and the single redacted diagnostic (Decision 14).

**The codes — 1**

8. **`EXIT_EXTERNAL`'s reader and the precedence** (Decision 6), with the status byte and the exit
   code asserted separately, and the shipped run-start-raise literal moving `EXIT_WRONG` →
   `EXIT_EXTERNAL`.

**Guards — 2**

9. **No policy knob** (Decision 7): Fixture K's two arms, and the sentence stating what the pin
   cannot prove.
10. **`batch` independence** (Decision 8) and **the run-start round cannot trip the gate**
    (Decision 11) — the second expressed as Fixture G3's assertion rather than as a comment, because
    an unreachability claim in a comment is what produced Part A's only Critical.

**Rows and filings — 1**

11. **§ Errors core raises' rows: the new one for `E-APPARATUS-CHANGED`, and
    `E-APPARATUS-RAISED`'s existing row rewritten** — it says today that `command_run` contains the
    raise and ends the command, and after this slice the same code can write `status: partial` and
    exit 5 when executions had already run. One row per code, not per emit site, so both outcomes
    belong in the one row. And **three filings, in `spec-defects.md` itself** — struck or written
    there rather than in a ledger line, each stating **the check its owner must make**, and each
    giving *unassigned* as **a fact with a reason** rather than the *"whichever slice does X"* form
    that points at a closed slice: strike `EXIT_EXTERNAL`'s entry now that task 8 gives it a reader;
    file the four contract refusals' lost record (Decision 9); file `max_failed_fraction`'s
    truncation status (Decision 5). The two struck-or-adjacent entries are re-read against the code
    this slice changed before they are touched, because a filing's claims about the code go stale.

**Direction against the scoping's 9 and Part A's revised 8: 11.** Up by three. Part A's routing
lists the code and test work and names **no document task and no filings task** — both of which
every code minted here requires, and both of which Part A itself needed and built. Down by nothing.
That direction — a re-scope finding a charter under-counted and missing surface — is what every
re-scope on this project has found.

### The ordering constraints, each with its reason

- **1 before everything**, so no code emits against a sentence the repo has not corrected.
- **2 and 3 before 4.** There is nothing to order until there is a comparison and a code.
- **5 before 6 and 7.** The status contract and the record both read a stop reason that does not
  exist until the signal does.
- **6 before 8.** The exit branch reads the same reason the status does; building the code first
  would mean deriving 5 from a status, which is the mutation task 8 exists to catch.
- **7 after 6**, since the record phase is reached with a status already decided.
- **9 and 10 after 5**, and 10's G3 arm may land any time after 2 — it asserts about a round that
  Part A already ships.
- **11 last**, so every row is written against emitted behaviour and the struck filing is struck
  against landed code.

---

## The traps this slice is most likely to hit

Drawn from `CLAUDE.md` § Misreadings, narrowed to what this design touches.

- **A safety argument in a comment is a claim needing a mutation.** Two live here: *the run-start
  round cannot trip the gate* (Decision 11) and *`len(plan)` is what a clean run's results reach*
  (Decision 5). Both are expressed as tests. If a comment says *this cannot happen*, make it happen.
- **A mutation's silence is evidence about the tests.** Every row in § The mutations names its
  assertion; the one blind row says so and gives its direct-call pin instead.
- **A fixture whose numbers agree with the bug.** Every count in § The discriminating fixtures is
  derived in writing here from the call schedule, and every derived value is recomputed by the test
  from the artifact it read.
- **An assertion whose substring agrees with either branch.** Part A shipped one. G1's two
  transition mutations both stop at call 2 with the same code; only the **named fact** separates
  them, so the assertion is on that phrase.
- **Reading a subprocess probe as a pin.** Verify each behaviour through the real console script,
  then pin by a mutation from the table — five correct-but-unpinned fixes on this project, four of
  them on Part A's branch alone.
- **Scoping a diagnostic by the helper it calls.** § Errors carries **one row per code, not per emit
  site**, and `E-APPARATUS-RAISED`'s row now describes two outcomes (record kept, record absent)
  depending on what had run.
- **Locating a table row by position, and count phrases near an insertion.** Task 1 inserts into an
  enumeration that counts itself.
- **Sweeping for the claim, not the file it was noticed in.** Task 1 touches one document and checks
  two more; task 11 touches `reference.md` and `spec-defects.md`. Three sweeps in one recent slice
  stopped one file short.
- **`git checkout -- <file>` destroys uncommitted work.** Keep a copy before mutating and verify a
  revert by **behaviour**.

---

## The consistency sweep this slice owes

The four documents only; the development record is **exempt** and must not be retro-edited.

- **`reference.md`** — § What status means and when a run keeps going (`failed`'s membership and
  its count phrase, `partial`'s *"one thing"*), § The apparatus core can only observe (the outcome sentence),
  § Exit codes and diagnostics (the one clause of Decision 4), § Errors core raises (the
  `E-APPARATUS-CHANGED` row), § The apparatus files (**checked, not changed** — its
  both-observations sentence is what Decision 3 implements), § Validation (**nothing owed**: every
  check here needs a probe call, and that section's own *"six things deliberately absent"* paragraph
  already states it for the apparatus — recorded so no later reader re-files it), § The importable
  surface and § Package layout (**no change**: Decision 13 adds no importable name), § The one config
  file (**no change**: Decision 7 adds no field).
- **`experimental-designs.md`** — § Mistakes core prevents' apparatus row: checked, not changed.
- **`design-principles.md`** — the design-goal sentence and § Not bit-identical reruns both already
  say a change fails the run: checked, not changed.
- **`README.md`** — no change; the worked example declares no probe.
- **Mechanical pass in full** on every file touched: links and `#anchor`s resolve, no colliding
  headings, table rows match their header's column count, no trailing whitespace or tabs, `×` not
  `x`, hyphens rather than en dashes in anything becoming an anchor. Fenced blocks skipped.
- **After removing or renaming any string**, grep the four documents, `CLAUDE.md` and the feasibility
  analysis for what should no longer exist — filtering the **file list**, never a sweep's output.

---

## The filings this slice touches

| Filing | What Part B does |
|---|---|
| *`EXIT_EXTERNAL = 5` ships and is read by nothing* — **Owner Part B** | **Closed** by task 8 and struck in `spec-defects.md`, after re-reading its claims against the code this slice changed. Re-confirmed shipped-and-unread at `290634e` before the work started |
| *The four contract refusals lose the run record mid-plan* — **NEW, unassigned** | **Filed** by task 11 with its measurement (a declared key missing on call 4: exit 1, no `run.yaml`, one execution paid for). **Unassigned is a fact with a reason:** no chartered slice contains this work, because no `reference.md` sentence sites a fact-contract failure at run time, so there is no section a slice could be said to own. **The check its owner must make:** whether the fault recurs identically on the next call (a declaration mismatch does; an unreachable apparatus need not); what `status` such a record would carry, given that § What status means has no row for it; and whether assembling a record on that path costs anything Fixture Z's boundary did not measure |
| *`max_failed_fraction`'s truncation status* — **NEW, unassigned** | **Filed** by task 11. **Unassigned is a fact with a reason:** the guard belongs to no remaining chartered slice — H8, H9 and H3c-3 are scoped elsewhere in the spine design § The hardening slices — and Part B declines it as a neighbouring mechanism's semantics (Decision 5). **The check its owner must make:** that the current behaviour is **pinned with a written justification** in `test_max_failed_fraction_is_measured_against_the_test_partition`'s docstring, which a closer must **argue against rather than discover**; that the all-completed, mixed and nothing-completed cases are three separate answers today and may need three rulings; which of § What status means' four passages governs, given that no row describes the all-completed truncation at all; and that `run_status` already carries the `max_failed_fraction` reason after Part B, so the change is one mapping entry plus the document rows — verified against the code rather than assumed from this entry |
| *`BaseTemplate.field_convention` is declarable and read by nothing* — **unassigned** | **Untouched and still unassigned.** Not adopted here |
| *two specified readers of `required_env` belong to unbuilt commands* | Not this slice's; named so it is not folded in |
| *`io.reuse_from` is unbuilt and unowned* | Not apparatus; named because it is what keeps six configs non-executable |

**The truncated-plan finding is filed rather than closed**, and it had never been filed anywhere: it
lived in the scoping's § 0.4 — where its stated ground is false — and, in the opposite direction, in a
shipped test's docstring, where the behaviour is argued for. Two records disagreeing about one
behaviour, neither of them the defects file, is precisely what a filing is for.

---

## Cost and risk — what a metered probe does and does not constrain

**A probe is user code; core only ever needs a fake.** Quota constrains **placement, not
testability**: every fixture above uses a probe that counts its calls in a file and never leaves the
machine. Three rules follow, and they are rules rather than caveats:

1. **`validate` must never call one** — Part A's pin, verified here, not re-built.
2. **The call count is a number `dry-run` must state before a run is scheduled** — Part A's
   `C + E_c + C × E_none`, unchanged by this slice, and its contract test is re-run rather than
   rewritten.
3. **A stop must not retry** (Decision 10). A retry is another paid call against an apparatus already
   known to be in trouble, and it is also a second answer to a question core has answered.

The one behaviour no fixture can stand in for is the one the null rule exists for — a hosted
deployment answering a fact on most calls and omitting it on some. That is why `null` is a legal
value, why Fixture G1 encodes exactly that shape by hand, and why an integration test against a real
deployment would be a **worse** pin: it would pass or fail for reasons the code does not control.

---

## The payoff, stated so it cannot be rounded

### The counts, measured on 2026-08-19 against commit `290634e`

**Part B unblocks ZERO configs.** No config in
[the feasibility analysis](../../feasibility-llm-growth-studies.md) declares an `apparatus_probe`
that a real plugin backs — the declaration is a template attribute and the substituted template is
`generic`. **Six with no remaining core-side blocker; three executable. Neither moves**, and the only
direction this slice can move a config-level count is **down**: `E-APPARATUS-CHANGED` is a new error
a probe-declaring run can newly earn. A closed defect is not an executable-run count, and no
sentence in this slice may put the two in one breath.

**What it is worth instead:**

- **A run whose apparatus moves stops instead of publishing.** Measured today: a probe answering
  `r1` twice and `r2` for the remaining ten calls produces exit 0, `status: completed`, and a
  `provenance.apparatus.facts` block reading `r1` — whose own ledger says `r2` ten times, and whose
  `hash` fingerprints an apparatus the run mostly did not measure through. That is the record
  `design-principles.md`'s first design goal claims cannot happen.
- **A stopped run keeps its record.** The measured shape today is exit 1, no `run.yaml`, no `status`
  byte, `latest` uncreated, with one execution's artifacts on disk — *every execution paid for, the
  record lost*, which is `CLAUDE.md`'s own name for the failure.
- **A plan truncated *by the apparatus* stops calling itself complete.** The mechanism that makes
  that possible — a stop reason reaching the status determination — is what the scoping asked for, and
  it is built here for the two apparatus reasons only. The neighbouring guard's own truncation status
  is **unchanged and filed**, with the check its owner must make written down (Decision 5), which is
  the difference between a measurement paying off and a slice inheriting a mechanism it does not own.
- **`EXIT_EXTERNAL` gains its first reader**, closing the fourth member of the shipped-but-unread
  family this repo has now filed five times.

**Nothing in the feasibility analysis gets closer to running because Part B lands.** What changes is
that a run of the designs it describes can no longer publish a record of an apparatus it stopped
measuring through.

**Task count is 11.**

---

## What did not survive the re-measurement

| Claim, and where | Verdict |
|---|---|
| *"`max_failed_fraction`'s `break` is only reachable once failures have accumulated, so its results list is never all-completed, which is why no test has ever separated the two"* — [`H7d-SCOPING.md`](../H7d-SCOPING.md) § 9, task 17 | **False on both halves.** That guard counts **units with no settled answer**, not failed executions, so a step completing while recording nothing trips it with every execution `completed`. Measured end to end: 2 of 5 executions, all `completed`, `status: completed`, exit 0 — and a **shipped, named test asserts exactly that**, with `expect_exit=EXIT_OK` and a docstring saying so. The state is reachable, reached and pinned, which is the opposite of hidden. **Consequences, both:** the truncated-plan lie is not apparatus-specific — and the same test's docstring **argues for** the behaviour, which is why Decision 5 threads that guard's reason and changes nothing about it, filing the question instead of inheriting it |
| § What status means, read as one settled section — the scoping quotes its `failed` paragraph and Part A's routing inherits that reading | **The section contradicts itself three ways about a truncated plan**, and the code answers a fourth (Decision 5's table). Its `partial` **table row** admits *"stopped early with executions already recorded"*; its `failed` paragraph lists `max_failed_fraction`; the paragraph after that says *"one thing"* produces an early-stopping `partial`. Neither the scoping nor Part A's routing names this, because both quote one passage. Task 1 settles it **for the apparatus only** and leaves the failure-fraction clause untouched; the state the code actually produces there — an all-completed truncation at exit 0 — is described by **no row**, and that remainder is filed with the check its owner must make |
| *"moved ⇒ the run fails, on the same line as a dirty tree"* — the scoping's task 19 | **The analogy points at the one member with no shape to copy.** A dirty tree is refused before a run directory exists (`E-CODE-DIRTY`, exit 1, nothing paid for). The other member of the document's own list — *an input file that moved* — is `E-INPUT-CHANGED`, which sets `status = "failed"`, writes the record and exits 4. Decision 4 copies that instead |
| The scoping's Part B list of 9, and Part A's revision to 8 | **Under-counted by three.** Neither names a **document** task or a **filings** task; § Errors owes a row for every code minted, § What status means owes a fourth producer of `failed` with its count phrase, and `EXIT_EXTERNAL`'s own filing must be struck. Part A needed and built both kinds of task |
| *"Part A provably cannot stop a run"* — Part A's whole-branch review | **True in the sense meant, and worth restating precisely** so no test here blurs it: Part A's mid-plan refusal **does** end execution; what it cannot do is end it **with a record**. The observable difference this slice makes is the record and the code, not whether the plan continues |
| *"Exit code 5 does not exist in this build"* — the scoping's § 0.3 | **Already corrected** by the scoping's appended correction and Part A's design; **re-confirmed at `290634e`**: defined, and read by nothing in `src/` or `tests/` |
| The scoping's task 18, *"`EXIT_EXTERNAL = 5` in `diagnostics.py` — the first code beyond 0–4"* | **Narrower, as Part A said.** What is owed is a reader and a pin. The narrowing survives re-measurement |
| The scoping's § 5 `batch` finding, and § 7's zero/six/three | **Survive**, re-measured: `apparatus.py` names `batch` nowhere and `replication.py` names the apparatus nowhere; the counts are unmoved |
| Part A's Decision 1 siting (checks run wherever a probe runs) and Decision 9's ledger shape | **Survive**, and Part B builds on them unchanged |

---

## What could not be measured

1. **Whether a `run.yaml` can be assembled over an empty results list.** No fixture at `290634e` can
   produce a stop with zero results, because no stop exists yet — which is exactly why Decision 4
   does **not** put that path on the failure route. Fixture Z's two arms are what will settle it once
   the code exists, and if assembling proves safe the ruling can be revisited **with the document row
   it would owe**.
2. **Anything about `dry-run`, `freeze`, `diff`, `reproduce`, `resume`.** All five print *specified
   but not built*, so every claim here about them is a **spec claim**, read, never a build fact — the
   gate's composition with `resume`'s restart most of all.
3. **The nine configs' actual plugin.** `publishable-llm`, `llm_screen` and `llm_deployment` are
   designs in the feasibility analysis, not code. Fixture P is a documented substitution — the same
   one every § Executability entry has used since 2026-08-16 — and it is a substitution, not the
   thing.
4. **A real metered probe**, deliberately, per § Cost and risk.
5. **Whether any shipped test asserts a literal this slice changes, beyond the one.** The one is
   `test_a_probe_that_raises_is_a_redacted_diagnostic_at_run` (exit 1 → 5), task 8's. Under the
   narrowed Decision 5, task 6 changes no expectation and no docstring at all, so the suite sweep an
   earlier draft of this design owed is **not owed**. What **was** measured and is worth carrying:
   `max_failed_fraction: 0.2` is materialized into **every** generated config (`materialize.py`), so
   the guard is armed in every end-to-end test — and yet the shipped `EXIT_PARTIAL` tests are **not**
   truncations, because a step whose every execution raises is never classified as *recording* and so
   trips nothing (`_units_failed_anywhere`'s own rule, read at `290634e`, consistent with those tests'
   docstrings saying *"the rest of the plan runs"*). The `run_status` call sites in
   `tests/test_runner.py` assert over `results` and are untouched by a defaulted keyword. What
   remains unmeasured is whether a mutated build changes any other literal, which needs a build.

6. **Whether Fixture G1 is the smallest fixture separating its five readings.** It separates them; no
   smaller one was searched for, and a smaller one would have to be checked against the same five.

---

## Ruling from the controller, recorded so the plan author sees why Decision 5 is narrow

**The ruling.** `run_status` is widened for the **apparatus** reasons only. `max_failed_fraction`
keeps `completed`, its reason is threaded so the truncation assert stays sound, and the question is
**filed** with the check its owner must make. § What status means is settled for the apparatus and
its remainder is filed rather than repaired. An earlier draft of this design ruled the other way —
`max_failed_fraction` → `partial`, one shipped literal and one docstring changed — on the strength of
the re-measurement alone.

**Two grounds, both about ownership rather than about which answer is better.**

1. **`max_failed_fraction` is not this slice's guard.** Carrying apparatus stop reasons into the
   status determination is H7d's. Re-deciding what the failure fraction reports changes **every run
   that declares it**, and every generated config declares it at `0.2` — measured. That belongs to
   whichever slice owns the guard, and an apparatus slice inheriting a neighbour's status semantics is
   scope creep even when the new answer is better argued.
2. **The behaviour is pinned with its reason written down**, in
   `test_max_failed_fraction_is_measured_against_the_test_partition`'s docstring. Editing a shipped
   assertion **and** the argument justifying it, in a slice about something else, is indistinguishable
   in the record from weakening a pin to pass — which is the move this project has been burned by. A
   closer must **argue against** that docstring, not discover it.

**What the earlier draft got right and is kept:** the measurement itself, unchanged and dated; the
finding that the scoping's ground for the defect is false on both halves; the finding that § What
status means contradicts itself and that the code answers a fourth way; and the mechanism, which is
built here.

**What it costs if this ruling is wrong.** A documented contradiction outlives this slice by one
more, now visible in a filing instead of in a scoping's prose — the recoverable direction. The
unrecoverable one is a slice about the apparatus having quietly changed what every run declaring a
failure fraction reports, discovered later by someone reading a test whose justification no longer
matches its assertion.

**The order this establishes, worth carrying past this slice:** a document may not be made
self-consistent by widening a behaviour change. Settle the part your slice owns, say plainly what is
left, and file the remainder with the check its owner must make.
