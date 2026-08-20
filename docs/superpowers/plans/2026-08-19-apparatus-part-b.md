# H7d Part B — the apparatus: gate and stop — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to
> implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** a run whose apparatus moves under it **stops, says so, and keeps the record of the period
that was certified.** Part A observes and records; Part B is the half that can end a run. Each
observation is compared against its own `(condition, fact)` pair's first *answered* value, a change
stops the plan where it stands, an unreachable apparatus is distinguished from a moved one,
`EXIT_EXTERNAL` gains its first reader, and `run_status` stops letting an apparatus-truncated plan
call itself `completed`.

**The payoff, stated so it cannot be rounded. Part B unblocks ZERO configs.** No config in
[the feasibility analysis](../../feasibility-llm-growth-studies.md) declares an `apparatus_probe` a
real plugin backs — the declaration is a **template** attribute and the template those measurements
substitute is `generic`, which declares none. **Six with no remaining core-side blocker and three
executable both stay exactly where H4b-1 left them**, and **the only direction this slice can move a
config-level count is down**, since `E-APPARATUS-CHANGED` is a new error a probe-declaring run can
newly earn. No task may write a sentence putting a closed filing and an executable-run count in one
breath. What Part B is worth instead: a run whose apparatus moved stops instead of publishing a
record whose own ledger contradicts it, a stopped run keeps the record its executions paid for, and
one more member of the shipped-but-unread family gains a reader.

**Architecture.** One new error code, one new construct that is deliberately **not** exported, two
widened signatures, one new branch in the exit mapping. **No new module** — a new module would move
the `mypy` gate's own literal, and Decision 13 rules the stop reason internal.

- **`apparatus.Observations`** gains the comparison (task 2). It reads `_first_answered`, the mapping
  Part A already keys by `(condition_key, fact)` and already updates only for a pair with no answered
  value — so the gate and `provenance.apparatus.facts` can never disagree about what a fact was
  pinned to, because there is one mapping.
- **`apparatus.Observer._observe_one`** gains the last link of the ordering chain (task 4):
  `check_facts` → `append_observation` → `Observations.record` → **compare** → raise.
- **`runner.StopSignal`** is a small mutable record — reason, code, message — that `execute_plan`
  writes and its caller reads. It lives in `runner.py` beside `execute_plan`, is passed as a
  **defaulted keyword**, and is exported from nothing.
- **`runner.execute_plan`** gains one `except ContractError` around its per-execution probe round,
  filtered to exactly `{E-APPARATUS-RAISED, E-APPARATUS-CHANGED}`, which records the reason and
  `break`s — `max_failed_fraction`'s own shipped mechanism, the one thing in this codebase that means
  "the run stops where it stands." Its existing break records `max_failed_fraction` on the same
  signal.
- **`run_record.run_status`** gains `planned` and `stop`. Two reasons decide the status outright; the
  third is threaded and **mapped to today's fold**, which is what keeps the truncation assert sound
  without changing one observable thing about the neighbouring guard.
- **`cli.command_run`** prints one redacted diagnostic per apparatus stop, continues into the record
  phase whenever a result exists, keeps Part A's shape when none does, and returns `EXIT_EXTERNAL`
  for an unreachable apparatus regardless of the status byte it wrote.

**Tech stack:** Python ≥ 3.11, `pytest`, `ruff`, `mypy`. No new dependency. The changes land in
`src/publishable/apparatus.py`, `src/publishable/runner.py`, `src/publishable/run_record.py`,
`src/publishable/cli.py`, `docs/reference.md`, `docs/superpowers/spec-defects.md`, and the test
modules `tests/test_apparatus.py`, `tests/test_cli.py`, `tests/test_runner.py`.

**Spec:** `docs/superpowers/specs/2026-08-19-apparatus-part-b-design.md` — read it beside this plan,
**including its appended § Ruling from the controller**, which narrows Decision 5 and establishes an
order this plan may not reverse. **It is the binding authority and this plan argues from it. Its body
must not be edited.** Where this plan measured something that contradicts it, the disagreement is
recorded in [§ Corrections against the code](#corrections-against-the-code) at the end of this file,
appended by this plan's author and extended by no task.

**Measurement this plan argues from:** `docs/superpowers/H7d-SCOPING.md` **including its appended
correction**; Part A's design, its plan **including that plan's § Corrections against the code**, and
its ledger; and this plan's own re-measurement against **`main` at `814eadd`**, this branch's point.
Every signature, record key, helper name, fixture shape, document section and literal below was read
or **run** at `814eadd`. **Nothing is cited by line number.**

**Baseline, measured 2026-08-19 in the FOREGROUND at `814eadd`:**

- `uv run pytest -q` → **2423 passed, 1 skipped, 2 xfailed** in 148.14 s
- `uv run ruff check .` → **All checks passed!**
- `uv run ruff format --check .` → **82 files already formatted**
- `uv run mypy` → **Success: no issues found in 46 source files**

**Task count: 13.** The design's 11 in its own grain and its own numbering, plus **task 12, the guard
pin, which runs FIRST**, and **task 13, Decision 11's run-start pin, split out of task 10 so it lands
in the first batch that can stop a run.** Both deviations are argued below. 13 tasks make 13 commits.

---

## Sequencing

**Execution order: 12 → 1 → 2 → 3 → 4 → 13 → 5 → 6 → 7 → 8 → 9 → 10 → 11.**

Each task restates the constraint it depends on in its own text, because an implementer sees only
their own task.

| Constraint | Why, and where it is enforced |
|---|---|
| **Task 12 first** | It pins the three things this slice moves — what `run_status` answers, what the exit code is, and what `run.yaml` holds — **captured from real runs at `814eadd`**, before task 6 changes a signature or task 7 changes a path. A pin recorded afterwards records the move, not the baseline. Part A's precedent: its batch-1 pin caught a spurious key three batches later and was never edited |
| **Task 1 before every code task** | § What `status` means contradicts itself about a truncated plan and the code answers a fourth way. No code may emit against a sentence the repo has not corrected. Task 1 settles it **for the apparatus only** and files the remainder |
| **Tasks 2 and 3 before 4** | There is nothing to order until there is a comparison and a code for it to raise |
| **Task 4 before 13** | Task 13's subject is a round that must **not** trip the gate, which is only assertable once the gate is live |
| **Task 13 in the same batch as 4** | Task 4 is the first commit in which a real `run` can stop over apparatus state. The risk this slice carries that Part A did not is *a run that stops when it should not*, and task 13 is the only pin for it. Leaving it to task 10 would let three batches ship a spuriously-firing gate with no review able to see it |
| **Task 5 before 6 and 7** | Both read a stop reason that does not exist until the signal does |
| **Task 6 before 8** | The exit branch reads the same reason the status does. Building the code first would mean deriving `5` from a status, which is the mutation task 8 exists to catch |
| **Task 7 after 6** | The record phase is reached with a status already decided |
| **Tasks 9 and 10 after 7** | Both assert an end-to-end stop's observable shape, which is not complete until the record and the code are |
| **Task 11 last** | Every row is written against emitted behaviour, and the struck filing is struck against landed code rather than an intention to land it |

### Two deviations from the design's grain, each argued

**(a) Task 12 exists at all.** The design names no regression pin. The surfaces it rewrites —
`run_status`'s answer, the exit mapping, and what a truncated run's `run.yaml` says — are exactly the
shape Part A's pin covered, and Part A's held **byte-identical** through five batches while still
discriminating. It is written against template `generic`, so it needs no plugin and no probe at all,
and its three arms were captured by running rather than transcribed.

**(b) Decision 11's pin is task 13 rather than an arm of task 10.** The design allows it to land "any
time after 2" and puts it in the last-but-one batch. Splitting it out moves it to the first
stop-capable batch, where it is the review's only way to see a gate that fires when it should not.
Task 10 keeps Fixture B alone. **Direction: 11 → 13, up by two, in the same direction every re-scope
on this project has moved.**

---

## Batching — six batches, one report and one review each

| Batch | Tasks | The seam, and what its review must be able to see |
|---|---|---|
| **B1** | **12, 1** | **The pin and the document.** Nothing here calls a probe and nothing changes behaviour, so no later batch emits against an un-amended sentence and the baseline is captured before anything moves. **Its review is a document review plus a capture check**: it must read § What `status` means, § Exit codes and diagnostics and § The apparatus core can only observe against each other, and it must confirm the pin's three arms were produced by running rather than read off `run_record.py` |
| **B2** | **2, 3** | **The comparison and its code, and not one call site.** Both are direct-call: a comparison on `Observations` and a message built from three strings. **Its review is transition arithmetic with no run in the picture** — all five of Decision 1's transitions pinned by direct call here, so the run-level batches are not also re-litigating what "changed" means. The seam is that a spurious gate cannot yet reach a run, because nothing calls the comparison |
| **B3** | **4, 13** | **The first batch in which a real `run` can stop over apparatus state.** The gate is wired into `_observe_one` and raises; nothing breaks the loop yet, so the whole risk of this batch is **firing when it should not**. **Its review must be a `run`-level review** — Part A's only Critical was invisible to every direct-call probe and surfaced only through an end-to-end `run` — and it must include task 13's sentinel mutation, which is the one cheap way to learn whether Part A's shipped suite would notice a gate that fires on `null → value` |
| **B4** | **5, 6** | **The stop mechanism and the status contract, and no record work.** Its property is almost entirely *nothing observable changed*: the `break` is `max_failed_fraction`'s own, and `run_status`'s third reason is a documented no-op. **Its review sees Fixture T's two arms and task 12's pin and nothing else**, deliberately — a reviewer certifying "the neighbouring guard is untouched" must not be the same one certifying "the new stop produces the right record", because that is how the controller's narrow ruling gets widened by accident |
| **B5** | **7, 8** | **The record on a stop, and the codes.** **Its review is a `run`-level review of what survives**: `run.yaml` with a `status` byte, `latest`, `apparatus/probes.jsonl` holding the moving observation, `executions.jsonl` short of `sweep.yaml`'s plan, and each execution's own artifacts — against Part A's measured shape, where a mid-plan refusal left *every execution paid for and the record lost*. It must check the status byte and the exit code as **two** assertions, and it must confirm the widened `run_a_project` guard left the suite count where task 12 put it |
| **B6** | **9, 10, 11** | **Guards, independence, rows and filings**, written against emitted behaviour. **Its review is a guard-and-document review**: what the two-arm knob pin can and cannot prove, whether the `batch` arms differ for any reason other than the apparatus, and whether each of the three filings names the check its owner must make |

---

## Global Constraints

Every task inherits all of these. They are copied verbatim rather than cross-referenced, because an
implementer sees only their own task brief.

**Commands.** Tests `uv run pytest`. Lint `uv run ruff check .`. Format `uv run ruff format .`.
Types `uv run mypy`. All four must pass before a commit. **Baseline at `814eadd`: 2423 passed, 1
skipped, 2 xfailed; 82 files formatted; 46 source files typed.**

**Run `uv run pytest` DIRECTLY, in the foreground, and wait for it.** It takes about two and a half
minutes. **Never construct a wait, a monitor, a poll or a background run around it** — several agents
on preceding slices stalled that way and one stopped with a mutation still applied. Clear
`__pycache__` and any stale `pytest-of-*` temp directory before a run.

**Verify format with `uv run ruff format --check .`, never the bare form.** A previous brief in this
repo wrote the bare form where it meant `--check` and rewrote 67 files. **`ruff format` does not
process `.md`** — measured on Part A's branch after a fix round reverted two documents on that
misdiagnosis; do not repeat it.

**Every task states its own DELTA, not an absolute.** Compute the absolute from your own previous run
and reconcile any difference before committing.

**Every task says whether its surface is `validate`, `run`, a direct call, or documents**, and the
task text states it. Tasks 2 and 3 are direct calls. Task 4 is both, and says which assertion is
which. Tasks 5 and 6 are direct calls plus `run`. Tasks 7, 8, 9, 10, 12 and 13 are `run`. Tasks 1 and
11 are documents. **No task's surface is `validate`** — every check this slice adds needs a probe
call, and `reference.md` § Validation's own *"six things deliberately absent"* paragraph already
states that for the apparatus. **None is owed, and that is a fact rather than a filing** (Part A's
batch-5 ruling, recorded so nobody re-files it).

**`validate` collects rather than aborting.** A refusal elsewhere never makes a later check
unreachable. Ask what `validate` **reports**, in full — and **assert alongside a second finding,
never on a total code set**: the `_validate_with` fixture this plan uses carries an incidental
`E-NAME-DIR`, measured at `814eadd`, so a total-set assertion would be fixture-incidental.

**A probe is user code that costs somebody else's quota, and core only ever needs a FAKE.** Every
test here runs a probe this repo wrote, counting its own calls, never reaching a network. The stand-in
is Part A's shipped three-part shape: `installed("dist-…", "1.0", {"publishable.probes": {"<name>":
"<module>:probe"}})` writing a real `.dist-info`, a module file written into that site directory
holding a `@register_probe` function, and `_local_template=` giving `run_a_project` a project-local
template that declares `apparatus_probe` and `apparatus_facts`. Request the `registries` fixture
whenever a decorator runs.

**Each fixture needs its OWN module name, its own probe name and its own template name.** Part A's
counting probes hold their counter in a **module-level** variable, and `sys.modules` caches across a
test session — two fixtures sharing an importable module name get the first one's code, which
silently swapped a raising probe for a moving one while the design was being measured. Two runs
**inside one test** additionally need **two `tmp_path` subdirectories**, because `run_a_project`
builds `proj/`, `data/` and `results/` under the path it is given and `data.mkdir()` takes no
`exist_ok`. The shipped precedent for all of this is
`test_two_runs_with_identical_facts_share_a_hash_and_one_changed_fact_moves_it` together with
`_APPARATUS_ASSAY_TEMPLATE_2` and its `h7d_probe2`; cite it rather than re-deriving it.

**Every literal is computed, not guessed.** Part A had **six** prescribed mutations that could not
discriminate and one assertion whose substring agreed with either branch. Every count in this plan is
derived in writing from the call schedule where it is stated, and **every derived value — an
`unobserved` count, a facts mapping, a hash, a condition key — is recomputed by the test from the
ledger or the `sweep.yaml` it just read**, never hard-coded. The only hard-coded numbers are ledger
line counts, exit codes, and task 12's captured key list.

**A mutation is a claim too.** For every mutation you apply, name the assertion that catches it
**and** state why the two branches can produce different results. Two rows in the design's own table
are named **blind end to end** and are pinned by a direct call instead; do not dress either up as an
end-to-end pin. **A mutation that changes nothing is evidence about the tests, not about the code.**

**Mutation discipline, every task.** Keep a copy of the file before mutating. Apply the named
mutation. Run the named test, confirm it **FAILS**, then run the **full, unfiltered** suite in the
foreground. Then `find . -name __pycache__ -type d -exec rm -rf {} +`. Then revert **by editing the
file back in place** — **never `git checkout -- <file>`**, which destroys uncommitted work and has now
been mistaken for a revert three times in this repo, the third time on a diagnosis that was itself
wrong. Verify the revert by **behaviour** and by diffing against your saved copy, never by
`git status`.

**A safety argument in a comment is a claim, and needs a mutation like any other.** Part A's only
Critical came from an unreachability claim a three-line fixture falsified, and the batch wrote **two
comments** from that claim without testing it. Two claims are live here — *the run-start round cannot
trip the gate* and *`len(plan)` is what a clean run's `results` reaches* — and **both are expressed as
tests, not as comments** (tasks 13 and 12/6). If a comment you write says *this cannot happen*, make
it happen.

**A stop must not lose the record that was paid for.** `CLAUDE.md`'s name for the failure is *every
execution paid for, the record lost*, and Part A's shape was measured precisely: exit 1, no
`run.yaml`, no `status` byte, `latest` uncreated, with one execution's artifacts and the ledger's
lines on disk. Every task that touches a stop states what its tests assert **survives** it.

**Reading a subprocess probe as a pin.** Verify each behaviour through the real console script
(`main(["run", …])`), then pin it by a mutation. **Five correct-but-unpinned fixes on this project,
four of them on Part A's branch alone**, every one found by mutation after being reported closed.

**Answering a question with a proxy** is this repo's most expensive habit. *Did this fact change* is
answered by the pair's own first answered value, never by the previous observation. *Did the run keep
its record* is answered by reading `run.yaml` back, never by the exit code. *Is the stop reason read*
is answered by a mutation, never by the presence of an enum member.

**Documentation rules.** `×` not `x` for multiplication, including inside fenced blocks. Hyphen,
never an en dash, in anything that becomes a filename or an anchor. **Cite by section**
(`reference.md` § "What `status` means, and when a run keeps going"), **never by line number**. **No
positional locators** ("the row above", "further up"): name what a sibling row *does*, and when you
insert a row check every row it **moved** and every count phrase near it — one Part A round removed
four locators and **added four more**, one in shipped source. **No counts in prose or comments** and
**no call-site enumerations**. **A build fact is dated and pinned to a commit.** **Prefer deleting a
claim to rewriting it** — a rewrite invents, a deletion cannot. **When you edit a docstring, re-read
the whole one.**

**Sweeps.** **Never filter the output of a sweep whose job is to find a string — filter the FILE
LIST**, and prove each sweep can fail by running it against a string known to be present. Name the
four documents explicitly, and **name the feasibility analysis too**: Part A's Major 1 was a
paraphrase of a re-sited rule surviving in that file because the brief's sweep named only the four.

**§ Errors carries one row per code, covering every emit site** — not one row per site.
`E-APPARATUS-RAISED` gains a second outcome in this slice and its unit of work is every site that
raises *or* reports it.

**The four normative documents LEAD; `src/` follows.** Where they and the code disagree, **the
document changes first** and the gap is recorded in `docs/superpowers/spec-defects.md`. The
cross-document pass governs those four **only** — never the development record under
`docs/superpowers/`, where a correction is **appended** rather than retro-edited. `spec-defects.md`
is the one exception: a closed gap is **struck** there rather than left to mislead. **This slice's
spec, Part A's spec and plan, `H7d-SCOPING.md` and its appended correction must not be retro-edited.**

**Two shipped things no task may change.** (1)
`test_max_failed_fraction_is_measured_against_the_test_partition` — neither its expectation nor its
docstring. It is deliberately pinned behaviour **with its argument written down**, and a slice about
the apparatus editing both the assertion and the argument justifying it is indistinguishable in the
record from weakening a pin to pass. If a task appears to need to, **that is a finding to report, not
a change to make.** (2) Task 12's guard pin, once captured. If it fails during task 6 or 7, that is a
finding; task 6 adds no second Fixture T, and its report states the pin's body was not touched.

**Do not touch the worked example.** `cohort-pilot` uses template `generic`, which declares no probe,
so it can never reach the gate and every interval in `CLAUDE.md` § The worked example stays as it is.

**`tests/conftest.py` already has** an autouse `os.environ` restore, an opt-in `registries` fixture
and an opt-in `installed` distribution fixture. **Do not add duplicates, and do not add a second
autouse fixture of any kind.**

---

## The discriminating fixtures, stated once because ten tasks share them

**Carried from the design's § The discriminating fixtures, with every literal re-derived here against
the code at `814eadd` by running.** **No later task may weaken any constraint below**, and a
substitute must meet all of them:

1. **Every literal is computed, not guessed**, and every *derived* value is recomputed by the test
   from what it read back.
2. **A fixture must separate every candidate reading, not two of them.** The design states outright
   that a two-observation fixture cannot separate the gate's three transitions; G1 is why.
3. **A control asserting only absences passes identically if nothing ran.** Every control here is
   paired with something that must report.
4. **No test reaches a network.** Every probe is a function this repo wrote.

### Fixture P — the plugin, inherited from Part A

A scaffolded project, a **project-local** template declaring `apparatus_probe` and
`apparatus_facts`, and a synthetic **installed** distribution whose `publishable.probes` entry point
names a module holding a `@register_probe` function that counts its own calls in a module-level
variable. Every fixture below is a Fixture P instance with **its own** distribution name, module
name, probe name and template name, for the reason § Global Constraints gives.

### Fixture G1 — all four transitions, one condition, one run

**Design.** No `sweep`, so **one condition whose key is `"00"`** (`reference.md` § The apparatus
files: the `<nn>_<label>` scheme with an empty label). `replication: {repeats: [{kind: seed, n:
4}]}` and the one scaffolded `repeat`-scoped step, so **4 executions planned** and, uninterrupted,
**5 probe calls** — one `run_start` round of one call, plus one `pre_execution` call before each
execution. `apparatus_facts = ["pinned", "appears", "vanishes"]`; the probe also returns an
**undeclared** `sometimes`, on call 1 only.

**The observation sequence, computed from the call schedule:**

| Call | Phase | Condition | `pinned` | `appears` | `vanishes` | `sometimes` | Covers |
|---|---|---|---|---|---|---|---|
| 1 | `run_start` | `00` | `"r1"` | `null` | `"L1"` | `"S1"` | the pins are established |
| 2 | `pre_execution`, before execution 1 | `00` | `"r1"` | `"A1"` | `null` | *absent* | `null → value`, `value → null`, an undeclared key's disappearance |
| 3 | `pre_execution`, before execution 2 | `00` | `"r1"` | `"A1"` | `null` | *absent* | the same three, a second time |
| 4 | `pre_execution`, before execution 3 | `00` | **`"r2"`** | `"A1"` | `null` | *absent* | `value → different value` — **the stop** |

```python
_GATE_MOVING_PROBE_MODULE = """\
from publishable import Apparatus, register_probe

_n = 0


@register_probe("h7d_gate_probe")
def probe(cfg):
    global _n
    _n += 1
    facts = {
        "pinned": "r1" if _n < 4 else "r2",
        "appears": None if _n == 1 else "A1",
        "vanishes": "L1" if _n == 1 else None,
    }
    if _n == 1:
        facts["sometimes"] = "S1"
    return Apparatus(facts=facts)
"""
```

**Computed expectations.** The stop is at call 4, **before execution 3 runs**, so:

- `executions.jsonl` holds **2 lines**, both `completed`.
- `apparatus/probes.jsonl` holds **4 lines**, and the **fourth** carries `pinned: "r2"`.
- `run.yaml` exists, with **`status: failed`**; the exit code is **4**; `latest` exists.
- `provenance.apparatus.facts["00"] == {"pinned": "r1", "appears": "A1", "vanishes": "L1",
  "sometimes": "S1"}` — every one a first-answered value, and **true under every ordering of the
  chain**, so it is a shape assertion and not a pin for any of them.
- `provenance.apparatus.unobserved` carries **three** entries, the declared facts only:
  `pinned {null_probes: 0, total_probes: 4}`, `appears {1, 4}`, `vanishes {3, 4}`. **Recomputed by
  the test from the four ledger lines**, which is itself the discriminator for gate-before-`record`.
- `W-APPARATUS-UNANSWERED` appears **exactly twice** — `appears` and `vanishes`, never `pinned`. Both
  warnings are things that must report, and they are also a **second, independent witness that the
  record phase was reached at all**, since `warn_unanswered` fires after `run.yaml` is written.
- The diagnostic names the condition key `00`, the fact `pinned`, and **`r1 → r2`**.

**Which assertion catches which mutation.**

| Mutation | Caught by | Why the branches differ |
|---|---|---|
| Gate **before** `append_observation` | the ledger's **4 lines with `r2` last** | 3 lines against 4; the recomputed `unobserved` is *equal* under this one, so the line count is the only witness |
| Gate **before** `Observations.record` | `unobserved.pinned.total_probes` **recomputed from the ledger** | ledger says 4, the record says 3 — a count, because every *value* assertion is true under both orderings |
| Fail on `value → null` | the stop moves to call 2: **2 ledger lines, no `executions.jsonl`** — and the message names **`vanishes`** | different counts *and* a different fact name |
| Fail on `null → value` | the same counts, message naming **`appears`** | the **named fact** is what separates this row from the one above; both would otherwise stop at call 2 with the same code |
| Treat an undeclared fact's **absence** as a change | the stop moves to call 2 | `sometimes` is absent from calls 2–4; a gate iterating `_first_answered`'s keys rather than the incoming mapping fires there |
| Raise instead of stopping | **no `run.yaml`** and exit 1 — Part A's measured shape — against the asserted record and exit 4 | |

**G1 is deliberately blind to** *compare against the most recent observation*: under that reading it
stops at call 4 exactly as designed. Fixture G2 is the only pin for it.

### Fixture G2 — first answered versus most recent

**Design.** One condition, `replication: {repeats: [{kind: seed, n: 3}]}` → **3 executions**, one
declared fact `flip`. Call 1 `"F1"`, call 2 `null`, call 3 `"F2"`, and `"F2"` thereafter.

```python
_GATE_FLIP_PROBE_MODULE = """\
from publishable import Apparatus, register_probe

_n = 0


@register_probe("h7d_flip_probe")
def probe(cfg):
    global _n
    _n += 1
    return Apparatus(facts={"flip": {1: "F1", 2: None}.get(_n, "F2")})
"""
```

**Computed expectations.** Call 1 is `run_start`; call 2 precedes execution 1; call 3 precedes
execution 2 and is where `_first_answered["00", "flip"] == "F1"` meets `"F2"`. So: the stop is at
**call 3**, `E-APPARATUS-CHANGED` naming `flip` and **`F1 → F2`**, `status: failed`, exit **4**,
**1 line** in `executions.jsonl`, **3 lines** in the ledger.

**Why G1 cannot replace it, and why the mutant arm terminates cleanly.** Under a most-recent
comparison, call 3 compares `null → "F2"` and does **not** stop; call 4 compares `"F2" → "F2"` and
does not either. The mutant run therefore **completes**: exit 0, `status: completed`, 3 executions,
4 ledger lines. Two branches, four different numbers. The `"F2"` default for calls ≥ 4 is what makes
the mutant arm end for the intended reason rather than stopping on a second, unrelated change.

### Fixture G3 — the per-condition scope, and the run-start round that must not fire

**Design.** Part A's shipped `test_a_probe_reading_a_swept_parameter_gets_ITS_condition_s_value` and
its `_SWEPT_FACT_PROBE_MODULE`, re-driven: `sweep.grid` over `instrument.model` with two levels, and
a probe returning the swept value it read as `model_revision`. **Two conditions, two different values,
two `run_start` calls.**

**Computed expectations.** Exit **0**, `status: completed`, `provenance.apparatus.facts` holding
**two different** values keyed by the two condition keys, and **no `E-APPARATUS-CHANGED` anywhere in
stdout or stderr**. Under a cross-condition comparison the run stops at the **second `run_start`
call** — 1 ledger line, no `executions.jsonl`, no `run.yaml`. This is the same fixture that makes
Decision 11's claim happen rather than asserting it: the run-start round makes exactly one call per
resolved condition, so no pair has a prior observation to disagree with, and a build that probed one
condition twice there would fail this test.

**The absence assertion is paired with something that must report** — the two distinct recorded
values, and `status: completed` — because "no `E-APPARATUS-CHANGED`" alone passes identically if
nothing ran.

### Fixture U — unreachable, mid-plan

**Design.** One condition, `{kind: seed, n: 4}` → **4 executions**, a probe raising on call **4**.

```python
_GATE_UNREACHABLE_PROBE_MODULE = """\
from publishable import Apparatus, register_probe

_n = 0


@register_probe("h7d_unreachable_probe")
def probe(cfg):
    global _n
    _n += 1
    if _n >= 4:
        raise RuntimeError("the instrument stopped responding")
    return Apparatus(facts={"model_revision": "r1"})
"""
```

**Computed expectations.** Exit **5**; `run.yaml` written with **`status: partial`**; **2 lines** in
`executions.jsonl`, both `completed`; **3 lines** in the ledger — a failed probe raises inside
`observe_once`, before `check_facts` and before any append, so a build that appended for it gives 4;
`latest` exists; the diagnostic is `E-APPARATUS-RAISED`.

**The status byte and the exit code are asserted separately**, because a build deriving the code from
`partial` returns 3 and no single assertion can see that. **`status: partial` with every execution
`completed`** is also what catches *drop the stop reason and let `run_status` fold*: the fold gives
`completed` and exit 0.

### Fixture Z — nothing paid for, both arms

**Arm 1 — a probe raising on call 1**, the `run_start` round. This is Part A's shipped
`test_a_probe_that_raises_is_a_redacted_diagnostic_at_run`, whose **one literal moves**
`EXIT_WRONG` → `EXIT_EXTERNAL`. **Measured at `814eadd` by running it:** the run directory exists and
holds exactly `environment`, `manifest`, `sweep.yaml` — **no `run.yaml`, no `executions.jsonl`, no
`apparatus/` directory at all** — and the results directory holds **no `latest` and no `latest.txt`**.
Its no-`run.yaml`, redaction and no-credential-anywhere assertions are untouched.

**Arm 2 — a probe moving on call 2**, one condition (`{kind: seed, n: 2}`), so call 2 is the first
`pre_execution` round and the first execution has not run.

```python
_GATE_EARLY_MOVE_PROBE_MODULE = """\
from publishable import Apparatus, register_probe

_n = 0


@register_probe("h7d_early_move_probe")
def probe(cfg):
    global _n
    _n += 1
    return Apparatus(facts={"model_revision": "r1" if _n == 1 else "r2"})
"""
```

**Computed expectations:** exit **1**; **no `run.yaml`**; **no `executions.jsonl`** (nothing
executed); **2 ledger lines**; `latest` and `latest.txt` both absent; `E-APPARATUS-CHANGED` in the
output. **This is the boundary Decision 4 draws, and the two arms are what make it observable rather
than argued.** Because exit 1 is `EXIT_WRONG`, `run_a_project` returns `run_dir: None` for this arm —
the test globs `results_dir` for `run_*` itself.

### Fixture T — the neighbouring guard, asserted **unchanged**, captured in task 12

**Both arms were captured by running at `814eadd`** and are task 12's arms B and C, so task 6 adds no
new fixture and re-runs these.

| Arm | Shape | Measured at `814eadd` |
|---|---|---|
| **all-completed** | The shipped `max_failed_fraction` fixture: `units=20`, a `holdout` of `frac: 0.2`, `limits.max_failed_fraction: 0.5`, `_ALWAYS_FAILING_STEP` | `executions.jsonl` **2 of 5**, every execution **`completed`**, `run.yaml` **`status: completed`**, exit **0** |
| **mixed** | `units=20`, `limits.max_failed_fraction: 0.5`, one step that records every unit on its first execution and **raises** on every later one | `executions.jsonl` **2 of 5**, statuses **`[completed, failed]`**, `run.yaml` **`status: partial`**, exit **3** |

**Both arms must report**: each asserts the truncation **happened** —
`len(executions.jsonl) < len(sweep.yaml["execution_order"])`, the comparison the shipped
`_planned_execution_count` helper already makes — **and** the status and the code it produced. A
control asserting only that nothing changed would pass if the guard stopped firing altogether. **And
each asserts that no apparatus diagnostic was printed**, since the truncation now travels on the same
`StopSignal` and a build that printed for every reason would be visible only here.

### Fixture K — the knob that cannot be written

**Arm (a), measured at `814eadd`.** `limits: {allow_apparatus_change: true}` through
`validate_config` reports **`E-CONFIG-KEY-UNKNOWN` at path `limits.allow_apparatus_change`**; the
same config without that key reports it not at all. The control's remaining finding is an incidental
`E-NAME-DIR` on `metadata.name`, which is why the assertion is **on the difference**, never on a
total code set.

**Arm (b).** Fixture G1's run with **every existing `limits` key at its most permissive** —
`max_executions` large, `max_failed_fraction: 1.0`, `max_ineligible_fraction: 1.0`,
`min_units_per_cell: 1`, `min_clusters: 1`, `min_reported_n: 1` — still stops, with G1's computed
counts. `1.0` is load-bearing: the neighbouring guard fires on `>`, so at `1.0` it can never fire and
cannot be confused with the gate.

**What this pin cannot prove**, stated because a test whose name claims a guarantee is a named trap
here: neither arm can prove that no *future* knob will be added. Arm (a) pins the schema; arm (b) pins
that today's most permissive config does not soften the gate. Nothing can pin the absence of a field
nobody has written.

### Fixture B — `batch` independence, two arms, equal `n`

**Design.** Two runs over the **same probe source**, identical but for `replication`: `{kind: seed,
n: 4}` against **one** `{kind: batch, n: 4}`. **Equal `n` is load-bearing** — with unequal `n` the
arms have different execution counts and their ledgers differ in length for a reason that has nothing
to do with the apparatus.

**Two arms in one test means two of everything:** two `tmp_path` subdirectories, two installed
distributions, two module names, two probe names, two template names — because the probe's counter is
module-level and `sys.modules` caches across the session. The two module sources are the same text
with a different registered name.

**Computed expectations.** The ordered `(phase, condition)` sequence read off `apparatus/probes.jsonl`
is **identical** across the arms — `[(run_start, "00"), (pre_execution, "00") × 3]` — as are
`provenance.apparatus.facts` and `provenance.apparatus.hash`, and `len(executions.jsonl)` is **2** in
both, which is "the stop lands at the same execution index". The ledger records no repeat label, which
is exactly why this projection is the comparable one. A `batch` level with no step declaring
`nondeterministic = True` earns `W-REPL-DETERMINISTIC`, so the arms' **stdout** differs by a warning
line for a reason that is not the apparatus; assert on the ledger, the facts and the hash, never on
whole output.

---

## Task 12: the guard pin, its literals captured at `814eadd`

**Runs FIRST, before task 1. Surface: `run`.** It pins what `run_status` answers, what the exit code
is, and what `run.yaml` holds — the three surfaces tasks 6, 7 and 8 rewrite. A literal recorded
afterwards records the change, not the baseline.

**Files:**
- Test: `tests/test_cli.py` (add)

**Interfaces:**
- Consumes: `run_a_project`, `_planned_execution_count`, `_ALWAYS_FAILING_STEP`, `yaml.safe_load`
  over `run.yaml`.
- Produces: nothing importable. Three pins every later task's suite run must keep green.

**The property.** For a template declaring **no** probe — template `generic`, which is every run in
this repo's own suite and the worked example — nothing about a run's status, its exit code, its
`run.yaml` key list, or the neighbouring guard's truncation behaviour moves in this slice. **These are
Fixture T's two arms plus a clean-run arm, and task 6 re-runs them rather than building a second copy
of them.**

- [ ] **Step 1: re-capture the three arms yourself, by running.** These were produced at `814eadd`
      by driving `run_a_project` and reading the artifacts back. **Re-run them before writing the
      assertions** and reconcile any difference: a pin whose expected value was transcribed from
      `run_record.py` pins the source, not the behaviour.

```
Arm A — a clean run (units=8, replication: seed n=4, template `generic`):
  len(executions.jsonl)            = 4
  len(sweep.yaml execution_order)  = 4      # equal — Decision 5's literal, end to end
  run.yaml status                  = completed
  exit                             = 0
  run.yaml top-level keys, in order:
    ['schema_version', 'run_id', 'status', 'draft', 'config', 'parameters_hash',
     'code_hash', 'provenance', 'layout', 'execution', 'results']
  results dir entries              = ['latest', 'run_<id>']     # a symlink on this platform

Arm B — the all-completed truncation (the shipped max_failed_fraction fixture's shape):
  len(executions.jsonl) = 2, len(execution_order) = 5, all statuses 'completed',
  run.yaml status = completed, exit = 0

Arm C — the mixed truncation (a step that records every unit once, then raises):
  len(executions.jsonl) = 2, len(execution_order) = 5, statuses ['completed', 'failed'],
  run.yaml status = partial, exit = 3
```

- [ ] **Step 2: write the three pins.** One test per arm, named for what it asserts. Arm A asserts
      the **full key list** as a list, not membership — a key added unconditionally by the record work
      is exactly what this catches and an assertion on `status` alone would not see it — plus
      `len(executions.jsonl) == len(sweep.yaml["execution_order"])`, which is Decision 5's
      `len(plan) == len(results)` claim expressed as behaviour rather than as a comment. Arm C's step
      source is new and belongs beside the shipped `_ALWAYS_FAILING_STEP`:

```python
_RECORDS_ONCE_THEN_RAISES_STEP = """\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
from publishable import BaseStep

_first = True


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        global _first
        if _first:
            _first = False
            for unit in io.units:
                io.record(unit.key, {{"value": 1.0}})
            return {{"n": len(io.units)}}
        raise RuntimeError("this execution fails on purpose")
"""
```

      **Why arm C truncates, derived rather than assumed:** `_units_failed_anywhere` unions across
      every recording execution of the run, so after the raising execution every unit is recorded
      under the first repeat label and not under the second — unresolved, 20 of 20, past `0.5`.
      Arm C's docstring says that, and says the numbers were measured.

- [ ] **Step 3: run.** `uv run pytest` → **2423 + 3 = 2426 passed**, 1 skipped, 2 xfailed.

- [ ] **Step 4: the mutation, and it is the shape Decision 3 refuses.** In `src/publishable/cli.py`,
      add `"stopped_at": None,` to the document `assemble_run_yaml` writes (or, if that document is
      assembled inside `run_record.assemble_run_yaml`, add it there). Run the **full** suite. Arm A
      must FAIL on the key-list assertion. **Why the two branches differ:** the list has one more
      element, and `status` is unchanged — so this proves the assertion reads the *shape*, which is
      what Decision 3 refuses to add and what tasks 7 and 8 could add by accident. Revert by editing
      the line out; confirm green.

- [ ] **Step 5: commit.** `git add -A && git commit -m "H7d Part B task 12: pin the status, the exit
      code and the run.yaml shape before anything moves"`.

---

## Task 1: `reference.md` made consistent about the apparatus, and no further

**Runs before every code task. Surface: documents.**

**The measured contradiction, and the boundary of this task.** § What `status` means, and when a run
keeps going says four things about a truncated plan and the code answers a fifth way: the `partial`
table row admits *"stopped early with executions already recorded"* at exit `3`; the `failed`
paragraph counts `limits.max_failed_fraction` among the things that produce `failed`; the paragraph
after it says *"one thing"* produces an early-stopping `partial`; the `completed` row says *"every
execution in the plan completed"*; and the code, measured at `814eadd`, reports **`completed` at exit
0 for an all-completed truncation**, which **no row above describes**.

**This task settles it for the apparatus only.**

- [ ] **Step 1: the `failed` paragraph gains the moved apparatus, and its count phrase moves with
      it.** That paragraph names three producers and says so in words; the moved apparatus is a
      fourth, so the phrase becomes four. **The `max_failed_fraction` clause STAYS.** This slice does
      not own that guard, and deleting a clause to make a sentence tidy while the code still
      contradicts it would be making the document consistent by omission.

- [ ] **Step 2: the `partial` paragraph's *"one thing produces that"* is made precise** — it is the
      apparatus becoming **unreachable**, not the apparatus generally, which is what the code does
      after this slice. Its exit-`5` sentence already says the right thing and is not rewritten.

- [ ] **Step 3: § The apparatus core can only observe states the outcome** where it today says only
      *"A changed fact fails the run"*: `status: failed`, the record kept, and the ledger holding both
      observations. The existing sentence about `resume` and about the ledger keeping both
      observations is what this extends; do not restate it.

- [ ] **Step 4: § Exit codes and diagnostics gains the one clause Decision 4 needs** — that the
      unreachable case exits `5` **whether or not a record was written**. Its `status: partial` and
      exits `5` sentence already exists; this is the clause it lacks, and exit `5`'s own row is
      already the only one of `3`/`4`/`5` not marked *"`run`, `draft`, `resume` only"*, which is why
      the clause is coherent.

- [ ] **Step 5: one precision edit, and it is this plan's own addition** (§ Corrections, correction
      6). § The apparatus core can only observe says a deployment is compared against *"its own first
      observation"*, while § The apparatus files says `facts` is the *"first **answered**
      observation"* — *"what the gate compares against"*. Those are different rules for the
      `value → null → other` case, and the second is the one Decision 1 implements. Tighten the first
      to match. **Prefer the minimal insertion of the one word to a rewritten sentence.**

- [ ] **Step 6: checked, not changed.** `experimental-designs.md` § Mistakes core prevents' apparatus
      row and `design-principles.md`'s design-goal sentence and § Not bit-identical reruns all
      already say a changed fact fails the run; this slice makes that true. `README.md` declares no
      probe. Record in the report that each was **read** and needed nothing.

- [ ] **Step 7: the mechanical pass, in full, on every file touched** — every relative link and
      `#anchor` resolves, no two headings collide, table rows match their header's column count, no
      trailing whitespace or tab or invisible unicode, `×` not `x`, hyphens rather than en dashes in
      anything becoming an anchor, fenced blocks skipped. Then sweep the **four documents,
      `CLAUDE.md` and the feasibility analysis** for any string this task's edits should have made
      false — **filtering the file list, never the sweep's output**, and proving each sweep can fail
      against a string known to be present.

- [ ] **Step 8: what this task does NOT close, and it must say so in its report.** The all-completed
      truncation remains a state **no row describes**, and the `failed` paragraph's
      `max_failed_fraction` clause remains one **the code contradicts**. That is task 11's filing, not
      a sentence this task may repair. A later task quietly closing it would be the widening the
      controller's ruling forbids.

- [ ] **Step 9: run all four gates** (no test count changes) **and commit.**

---

## Task 2: the comparison, on `Observations`, reading `_first_answered`

**Runs after task 1. Surface: direct call.**

**Files:**
- `src/publishable/apparatus.py`
- Test: `tests/test_apparatus.py`

**Ruling (Decision 1).** For each `(condition, fact)` pair an observation is compared against the
pair's **first answered** value — never the previous observation, never another condition's. The
comparison reads `Observations._first_answered`, the mapping Part A already keys that way and already
updates only when the pair has no answered value and the incoming value is not `None`; **it keeps no
second mapping**, so `provenance.apparatus.facts` and the gate cannot disagree about what a fact was
pinned to.

**The five readings, and only the first fails:** `value → different value` fails;
`null → value` passes and the value becomes the pair's first answered; `value → null` passes and the
first answered stands; a key **absent** from a later call is not compared at all (a *declared* key's
absence is already `E-APPARATUS-FACT-MISSING`, Part A's, so the only absence reaching here is an
undeclared fact's); and `value → null → different value` **fails**, which is what makes *first
answered* a different rule from *most recent*.

**The signature, and it iterates the INCOMING mapping:**

```python
def changed(self, condition_key: str, facts: Mapping[str, Any]) -> tuple[str, Any, Any] | None:
    """The first (fact, first_answered, incoming) triple that contradicts this
    pair's first answered value, or None."""
```

- [ ] **Step 1: write it, and do not write a branch for a pair with no first answered value.** This
      method is called **after** `Observations.record` (task 4), and `record` establishes
      `_first_answered[pair]` for every non-`None` incoming value. So after `record`, a non-`None`
      value's pair **always** has a first answered entry, and a `self._first_answered.get(pair)`
      whose `None` result silently `continue`s would be a **dead branch that fails open on exactly
      the comparison this slice exists to build** — invisible to every fixture, because no fixture can
      reach it. Write the invariant as a bare `assert` on core's own contract, the same way
      `execute_plan` already asserts about its own callers, and say in the docstring that the ordering
      is what makes it hold. **Do not write a silent skip.**

- [ ] **Step 2: the direct-call tests, all five readings.** Build an `Observations`, call `record`
      then `changed` in the chain's order, and assert the triple or `None`. Two conditions in one
      instance, with the same fact taking different values, is the per-condition reading's own test —
      `changed` must return `None` for the second condition's own first observation.

- [ ] **Step 3: run.** `uv run pytest` → **previous + 6 passed** (one per reading, plus the
      per-condition pair).

- [ ] **Step 4: three mutations.** (a) compare against a most-recent mapping instead: the
      `value → null → other` test must FAIL. (b) drop the `value is None` guard: the `value → null`
      test must FAIL. (c) iterate `self._first_answered`'s keys instead of `facts`: the
      undeclared-absence test must FAIL. **Each pair of branches produces a different return value,
      not a crash.** Revert each by editing back.

- [ ] **Step 5: commit.**

---

## Task 3: `E-APPARATUS-CHANGED`, and what its message may name

**Runs after task 2. Surface: direct call.**

**Files:**
- `src/publishable/apparatus.py`
- Test: `tests/test_apparatus.py`

**Ruling (Decision 2).** One new code, `E-APPARATUS-CHANGED`, raised where the comparison happens.
Its message names **the condition key, the fact name, and both values**, in the shape `diff`'s own
apparatus row prints — `calibration_id: CAL-2026-07-19 → CAL-2026-08-02`, with `→` and not `->`.

**Why naming the values is safe, and it rests on Part A rather than a fresh judgement.** A fact value
is contracted non-secret and non-identifying, and Part A's `check_facts` **refuses** a value that
equals *or contains* a declared credential **before** anything is recorded — so by the time the gate
sees a pair of values, core has already established that neither carries a credential it read. The
diagnostic still renders through a credential-bearing `Collector`, so a value core did not read but a
plugin embedded is redacted on the way out. Both mechanisms are Part A's and are **reused, never
re-derived** — a second derivation is a second answer, which is the reasoning behind three credential
leaks on this project.

- [ ] **Step 1: raise it from the gate's caller-facing helper**, with a message naming the condition
      key, the fact, and `first → incoming`.

- [ ] **Step 2: the membership ruling, and it is this plan's own** (§ Corrections, correction 4).
      **`E-APPARATUS-CHANGED` is NOT added to `apparatus.APPARATUS_CODES`.** That frozenset is
      `command_run`'s containment filter for a probe **call** crossing the `execute_plan` boundary,
      and after task 5 a changed fact never crosses it — the loop breaks on it. Adding it would put an
      **unpinned member** in an enumeration whose every member is pinned, which is precisely Part A's
      Major 2 (deleting three of five left the suite byte-identical). Instead this slice mints
      `apparatus.STOP_CODES`, the two codes `execute_plan` breaks on, and **every member of it is
      pinned** — `E-APPARATUS-RAISED` by Fixture U, `E-APPARATUS-CHANGED` by Fixture G1. Write the
      reason in the constant's docstring **without** claiming that a run-start change *cannot* happen:
      task 13 is where that claim is made to happen, and a comment asserting it is the shape that
      produced Part A's only Critical.

- [ ] **Step 3: the tests.** Direct-call: the code, and the message containing `r1 → r2`, the fact
      name and the condition key, and **never** either value's variable name. Plus the credential
      case as a control that must report: a `changed` triple whose value contains a declared
      credential cannot arise, because `check_facts` refused it first — assert that ordering by
      calling the two in the chain's order and watching `check_facts` raise its own code.

- [ ] **Step 4: run.** `uv run pytest` → **previous + 3 passed**.

- [ ] **Step 5: the mutation.** Reduce the message to the fact name alone. The message test must FAIL
      on the `→` phrase. **Why the branches differ:** the arrow phrase is present in one and absent
      in the other — and it is asserted as the **whole phrase including both values**, not as a
      substring either branch would satisfy, which is the shape Part A shipped once and paid for.

- [ ] **Step 6: commit.**

---

## Task 4: the ordering chain, and the two assertions only it can make

**Runs after task 3. Surface: BOTH a direct call and `run`, and each assertion says which.**

**Files:**
- `src/publishable/apparatus.py`
- Test: `tests/test_apparatus.py`, `tests/test_cli.py`

**Ruling (Decision 3): inside one probe round the order is fixed and every step of it is
load-bearing.**

```
check_facts  →  append_observation  →  Observations.record  →  the gate compares  →  raise
```

- `check_facts` **first**, unchanged from Part A's ruling: a credential-carrying fact is refused
  before a byte reaches the ledger.
- `append_observation` **before** the comparison, because § The apparatus files requires that *"a run
  that failed on a moved apparatus still shows the evaluable earlier period"* and § The apparatus core
  can only observe that *"the ledger keeps both observations"* — **both**, which means the moving
  observation is on disk. A gate that stopped before appending would record the earlier period and
  lose the evidence of what ended it.
- `record` **before** the comparison, so the moving call is counted in `unobserved.total_probes` like
  any other probe: the counts are a census of calls, not of agreements. Because `_first_answered`
  never overwrites an answered pair, this ordering **cannot change the value the gate compares
  against** — which is why the discriminator for this clause is a **count**, not a value.
- The gate **last**. In this task it **raises**; task 5 is what turns the raise into a stop.

- [ ] **Step 1: add the comparison as the last statement of `Observer._observe_one`**, after
      `self.observations.record(key, facts)`, raising task 3's code when `changed` returns a triple.
      **Nothing else in that method moves.**

- [ ] **Step 2: the direct-call pin for record-before-gate.** Build an `Observer` over a fake probe
      following G1's schedule, drive four rounds, catch the raise, and assert
      `observer.observations.unobserved(["pinned"])["pinned"]["total_probes"] == 4`. **A direct call
      rather than end to end**, because at this commit the raise still ends the command before
      `run.yaml` is written, so `provenance.apparatus.unobserved` does not exist to read; task 7
      re-asserts the same number end to end.

- [ ] **Step 3: the `run`-level pin for append-before-gate, which is Fixture G1's ledger.** Drive G1
      end to end with `expect_exit=EXIT_WRONG` — **the shape at this commit**, and the task's own text
      must say that this expectation is task 7's to change and that changing it there is expected
      rather than a regression. Assert **4 ledger lines**, the **fourth** carrying `pinned: "r2"`, and
      the diagnostic naming `pinned` and `r1 → r2`. **The ledger is written on the raise path** —
      measured on Part A's branch: a mid-plan refusal preserves every line already appended.

- [ ] **Step 4: run.** `uv run pytest` → **previous + 2 passed**.

- [ ] **Step 5: two mutations.** (a) move the comparison **above** `append_observation`: step 3's test
      must FAIL on **3 lines against 4** — a count, and the only assertion that can see it, since the
      recomputed `unobserved` is *equal* under this mutation. (b) move it **above**
      `self.observations.record`: step 2's test must FAIL on **3 against 4**. Neither is a crash.
      Revert each by editing back.

- [ ] **Step 6: commit.**

---

## Task 13: the run-start round cannot trip the gate, and the sentinel that proves the suite would notice

**Runs immediately after task 4, in the same batch. Surface: `run`.**

**Files:**
- Test: `tests/test_cli.py`

**Ruling (Decision 11).** No new guard is added at `validate` — Part A's flag-file pin
(`test_no_validate_path_calls_a_declared_probe`, whose probe writes a flag file **and then raises**)
already holds that, and this slice adds nothing to it. What is owed is the claim that the run-start
round **can never** trip the gate, and **`CLAUDE.md`'s rule is that a safety argument is a claim
needing a mutation**: Part A's only Critical came from an unreachability claim a three-line fixture
falsified. **So the claim is not permitted to live in a comment. It is a test.**

- [ ] **Step 1: Fixture G3, re-driven to completion.** Two conditions sweeping `instrument.model`, a
      probe returning the swept value as `model_revision` — Part A's shipped
      `_SWEPT_FACT_PROBE_MODULE` and `_APPARATUS_ASSAY_TEMPLATE`, with **your own** distribution and
      module names. Assert exit **0**, `status: completed`, `facts` holding **two different** values
      keyed by the two condition keys, and **no `E-APPARATUS-CHANGED`** in stdout or stderr. The
      absence assertion is paired with the two distinct values and the `completed` status, which must
      report — the absence alone passes identically if nothing ran.

- [ ] **Step 2: the mutation for the cross-condition reading.** Make `changed` compare against any
      condition's first answered value for that fact. Step 1's test must FAIL: the run stops at the
      **second `run_start` call** — 1 ledger line, no `executions.jsonl`, no `run.yaml`, exit
      non-zero — against the asserted exit 0 and two recorded values. Revert.

- [ ] **Step 3: the sentinel mutation, which is about the SUITE rather than about the code.** Part A
      shipped tests that ought to fail under a spuriously-firing gate — Fixture N's
      `test_a_declared_probe_records_the_five_sub_keys_per_condition` drives a probe whose
      `calibration_id` answers `null` on its first call and a value afterward, which is
      `null → value` twice over — but **nobody has checked**, because they predate the gate. So: make
      `changed` **fail on `null → value`**, run the **full, unfiltered** suite, and record which tests
      fail.
      - If Fixture N's test fails: the sentinel is real. Say so in the report, name it, and add
        nothing.
      - If it does **not** fail: the sentinel is imaginary, and a fixture is owed. Build the smallest
        one that fails under this mutation and passes without it, and say in the report that it was
        owed because a shipped test that looked like a pin was not one.
      **This is the one cheap way this batch's review can see a gate that fires when it should not**,
      and it is prescribed as a measurement whose outcome is not assumed. Revert by editing back.

- [ ] **Step 4: run** the full suite clean, then **commit.**

---

## Task 5: `StopSignal` and the `break`, on `max_failed_fraction`'s precedent

**Runs after task 13. Surface: direct call plus `run`.**

**Files:**
- `src/publishable/runner.py`
- Test: `tests/test_runner.py`, `tests/test_cli.py`

**Ruling (Decision 3): the stop is a `break` in `execute_plan`'s loop** — the one shipped mechanism
in this codebase that means "the run stops where it stands." **One seam, not two:**
`Observer.observe_round` **raises** for both faults, which is what Part A's `observe_once` already
does for an unreachable probe and what task 4's gate now does for a moved one, and `execute_plan`'s
loop catches `ContractError` around **that call only**, and for exactly `apparatus.STOP_CODES` records
the reason and breaks. **Every other code is re-raised** and keeps Part A's containment path byte for
byte, the four contract refusals of Decision 9 included. So *"stops rather than raising"* means **does
not escape to `command_run`'s containment**, which is what the mutation *raise instead of stopping*
actually tests.

**A stop never retries** (Decision 10). The `break` is the last thing the loop does: a retry is
another authenticated, metered call against an apparatus already known to be in trouble, and on a
moved one it asks the same question core has already answered.

- [ ] **Step 1: `StopSignal` in `runner.py`, beside `execute_plan`.** A small mutable record —
      `reason`, `code`, `message`, all defaulting to `None`. **Not exported from `publishable`**
      (Decision 13: everything a user writes against is on the enumerated importable surface, and this
      is a value nobody imports), **and not written into any artifact.** No new module: a new module
      moves the `mypy` gate's own literal off 46 source files for a construct one function pair
      shares.

- [ ] **Step 2: `execute_plan` gains `stop: StopSignal | None = None`**, a defaulted keyword exactly
      as `credentials` and `observer` already are, **so no existing call site changes and no test line
      is deleted.** Wrap only the per-execution probe round:

```python
if observer is not None:
    try:
        observer.observe_round(phase="pre_execution", condition_index=execution.condition_index)
    except ContractError as exc:
        if stop is None or exc.code not in apparatus.STOP_CODES:
            raise
        stop.reason = (
            "apparatus_unreachable" if exc.code == "E-APPARATUS-RAISED" else "apparatus_changed"
        )
        stop.code, stop.message = exc.code, str(exc)
        break
```

      The message is carried **raw**; it is redacted where it is rendered, through the
      credential-bearing `Collector` (task 7), which is the one mechanism per surface rule Part A
      shipped.

- [ ] **Step 3: the existing `max_failed_fraction` break records its own reason** on the same signal —
      `stop.reason = "max_failed_fraction"`, no code and no message. **Nothing else about that guard
      changes**, and this is what keeps task 6's truncation assert sound.

- [ ] **Step 4: the tests.** Direct call on `execute_plan` with a fake observer that raises on its
      *n*-th round: the returned `results` is short, `stop.reason` is the right member, and the
      `ContractError` did **not** escape. A second direct call with one of Decision 9's four contract
      codes: it **does** escape, unchanged. Plus Fixture U end to end at this commit's expectation,
      which the task text names as task 7's to change.

- [ ] **Step 5: run.** `uv run pytest` → **previous + 3 passed**.

- [ ] **Step 6: two mutations.** (a) widen the filter to all of `APPARATUS_CODES`: the escape test for
      a contract code must FAIL, because that code now breaks instead of ending the command. (b) drop
      `E-APPARATUS-CHANGED` from `STOP_CODES`: G1's end-to-end test must FAIL — the raise escapes,
      is **not** in `APPARATUS_CODES` (task 3's ruling), and so reaches `main`'s own bare
      `PublishableError` handler, giving exit 1 with no collector-rendered summary and no `run.yaml`.
      **Both mutations change what is printed and what exists on disk, not merely whether something
      crashes.** Revert each by editing back.

- [ ] **Step 7: commit.**

---

## Task 6: `run_status`'s contract — widened for the apparatus, and NOT re-decided for the neighbour

**Runs after task 5. Surface: direct call plus `run`.**

**Files:**
- `src/publishable/run_record.py`, `src/publishable/cli.py`
- Test: `tests/test_runner.py`

**`run_status` lives in `run_record.py`, not in `runner.py`** — the design names the function without
naming the file (§ Corrections, correction 1).

**Ruling (Decision 5, as narrowed by the controller's ruling).**
`run_status(results, *, planned=None, stop=None)`, where `stop` is a **reason string** from a closed
vocabulary of three. Two decide the status outright — `apparatus_unreachable` → `partial`,
`apparatus_changed` → `failed`. The third, `max_failed_fraction`, is **threaded and deliberately
mapped to today's fold over the results**, so that guard's observable behaviour is **unchanged by
this slice**, including the all-completed truncation that reports `completed` at exit 0. When
`planned` is given, `len(results) < planned` with `stop is None` is a **core defect** and asserts
rather than folding.

**Why the third reason is threaded at all, since it changes nothing.** It is what makes the
truncation assert sound: without a reason on that path, every `max_failed_fraction` stop would trip a
guard meant to catch core truncating a plan for no recorded reason. **So the member IS read** — by the
branch that suppresses the assert and falls through to the fold — and the fall-through is a documented
no-op rather than an omission. It also leaves the change its owner may want as **one mapping entry**.

**Why the neighbour is not re-decided, and the first ground settles it.** The current behaviour is
**pinned with its reason written down**, in
`test_max_failed_fraction_is_measured_against_the_test_partition`'s docstring, which argues that the
guard and the execution-level exit code are two different mechanisms. **A slice about something else
editing both a shipped assertion and the argument justifying it is indistinguishable in the record
from weakening a pin to pass.** And `max_failed_fraction` is not this slice's guard: re-deciding what
it reports changes **every run that declares it**, and every generated config declares it at `0.2`
(materialized in `materialize.py`, measured). **No shipped expectation and no docstring changes in
this task.** If one appears to need to, that is a finding to report.

- [ ] **Step 1: the signature and the mapping.** A module-level mapping from the two apparatus
      reasons to their statuses, consulted first; then the truncation assert; then today's fold,
      untouched.

- [ ] **Step 2: the truncation guard is a bare `assert`, not a coded `ContractError`** (§ Corrections,
      correction 2). The design cites `E-RUN-CFG-MISSING`'s precedent for asserting about core's own
      callers; the **closer** precedent is `execute_plan`'s own two bare asserts, whose comments say
      they assert about core's own callers rather than about a config. A coded error would mint a
      sixth `E-` code owing a § Errors row for a state **no config can reach**, which is a document
      surface with no reader. State that in the assert's message.

- [ ] **Step 3: `cli.command_run` constructs a `StopSignal`, passes it to `execute_plan`, and calls
      `run_status(results, planned=len(plan), stop=stop.reason)`.** `planned` is `len(plan)`,
      computed at the call site from the plan already in scope, and **nothing writes it into
      `run.yaml`** (Decision 12): `sweep.yaml` already records what a reader derives the plan length
      from and `executions.jsonl` records what ran, and a third number is a third thing that can
      disagree.

- [ ] **Step 4: the direct-call pins.** `run_status` with each of the three reasons; `run_status` with
      a truncated list and `stop=None` **must raise**; `run_status` with a truncated list and
      `stop="max_failed_fraction"` must fold. **The truncation assert's pin is a direct call and is
      named as one** — with every stop carrying a reason, no reachable run trips it, so an end-to-end
      mutation of it is **blind** and the design says so. Do not dress it up.

- [ ] **Step 5: re-run task 12's arms B and C — Fixture T — and change nothing about them.** Both
      must still report exactly what they were captured reporting, and each must additionally assert
      that **no apparatus diagnostic was printed**, since the truncation now travels on the same
      signal. **The report states that the pin's body was not edited.**

- [ ] **Step 6: run.** `uv run pytest` → **previous + 4 passed**, and Fixture T's arms unchanged.

- [ ] **Step 7: four mutations.** (a) map `max_failed_fraction` to `partial`: arm B must FAIL —
      `partial`/3 against `completed`/0. (b) map it to `failed`: arm C must FAIL — `failed`/4 against
      `partial`/3. (c) delete the truncation assert: **blind end to end**, and the direct-call pin
      from step 4 is what catches it; say so rather than claiming an end-to-end catch. (d) suppress
      the assert for **every** stop rather than for a recorded reason: **also blind end to end**, and
      pinned by the same direct call. Revert each by editing back.

- [ ] **Step 8: commit.**

---

## Task 7: the record on a stop — the code and the record move together

**Runs after task 6. Surface: `run`.**

**Files:**
- `src/publishable/cli.py`
- Test: `tests/test_cli.py`

**Ruling (Decision 4): an apparatus stop continues into `command_run`'s record phase — the same path
`max_failed_fraction`'s `break` already takes — whenever at least one `ExecutionResult` exists. With
**no** results, nothing was paid for, and the command keeps Part A's shape: a redacted diagnostic, no
`run.yaml`, `latest` untouched.**

| Fault | Results | Record | `status` | Exit |
|---|---|---|---|---|
| Unreachable (a probe raised) | ≥ 1 | `run.yaml` | `partial` | **5** (task 8) |
| Unreachable | 0 | none | — | **5** (task 8) |
| Moved (a fact changed) | ≥ 1 | `run.yaml` | `failed` | **4** |
| Moved | 0 | none | — | **1** |

**The ground for "the record phase is reached" is the truncation break, measured.** The
`max_failed_fraction` `break` already returns from `execute_plan` with a short results list and
`command_run` already writes `run.yaml` and repoints `latest` for it — measured at `814eadd`, 2 of 5
executions with a `run.yaml` on disk. **That is a stronger ground than the input-drift analogue**,
which is cited only for the status-and-exit pair: `E-INPUT-CHANGED` sets `status = "failed"` after the
executions, writes the record, and exits 4, which is `reference.md`'s own *"same line as … an input
file that moved"* one dependency along.

**The novel record shape is G1's**, and no shipped fixture covers it: a **truncated** results list in
which **every execution completed**, recorded as **`status: failed`**. The truncation precedent covers
truncated-and-mixed and truncated-and-all-completed-at-`completed`; it does not cover this.

**One diagnostic per stop, printed through a FRESH redacting `Collector`** (Decision 14) carrying the
`credentials` mapping `command_run` already bound before the roster call. **Never appended to `c`,
which has already been rendered and printed** — appending re-prints every earlier finding and inflates
the counts line, which is how Part A's own review caught a second render printing "3 problems" rather
than 4. `credentials` is **reused, never recomputed**.

- [ ] **Step 1: the branch, immediately after `execute_plan` returns and before the aggregate phase.**
      Printed there rather than at the end so the reason a run stopped is on the operator's screen
      before any phase that can itself fail. **Gated on the two apparatus reasons only** — a
      `max_failed_fraction` stop prints nothing, exactly as today, which Fixture T's arms now assert.

```python
if stop.reason in ("apparatus_unreachable", "apparatus_changed"):
    stop_c = Collector()
    stop_c.credentials = credentials
    stop_c.error(stop.code, "experiment_type", stop.message)
    print(stop_c.render(), file=sys.stderr)
    if not results:
        return EXIT_WRONG      # task 8 turns the unreachable arm of this into EXIT_EXTERNAL
```

      `"experiment_type"` is the path Part A's probe diagnostics already use, which keeps
      `_assert_went_through_the_containment_wrapper` — the helper that discriminates a
      collector-rendered finding from `main`'s bare one-line print — usable here.

- [ ] **Step 2: widen `run_a_project`'s no-ledger guard, and verify it by the suite rather than by
      argument** (§ Corrections, correction 3). That helper returns `run_dir: None` **only** for
      `expect_exit == EXIT_WRONG`; for any other code it does
      `next(results_dir.glob("run_*"))` and then reads `executions.jsonl`, which **does not exist**
      when no execution ran — measured at `814eadd`: a run-start probe raise leaves a run directory
      holding exactly `environment`, `manifest`, `sweep.yaml`. Add a second condition — a run
      directory with no `executions.jsonl` returns the same `run_dir: None`, `results: None` shape —
      and state the helper's rule as *`run_dir` is not `None` exactly when there is a ledger to read*.
      **Then run the full suite and confirm the count is unchanged from task 12's**; that converts
      "no existing caller has a run directory without a ledger" from a reading of the code into a
      measurement.

- [ ] **Step 3: Fixture G1, end to end and in full.** `expect_exit=EXIT_FAILED`. Read the **whole**
      `run.yaml` back, not just the status byte: the key list from task 12's pin, `status: failed`,
      and `provenance.apparatus` with `facts["00"]` as computed and `unobserved` **recomputed from
      the four ledger lines**. Then **2 lines** in `executions.jsonl` both `completed`, **4 lines** in
      `apparatus/probes.jsonl` with `pinned: "r2"` last, `latest` present, the diagnostic naming
      `pinned` and `r1 → r2`, and **exactly two** `W-APPARATUS-UNANSWERED` lines — which is a second,
      independent witness that the record phase was reached, since that warning fires after
      `run.yaml` is written. **This is the test whose `expect_exit` task 4 said would change here.**

- [ ] **Step 4: Fixture U, end to end.** `expect_exit=EXIT_WRONG` at this commit — task 8 moves it to
      `EXIT_EXTERNAL`, and this task's text says so. `status: partial` with **every execution
      `completed`**, 2 executions, **3 ledger lines** (a failed probe appends nothing, so a build that
      appended for it gives 4), `latest` present.

- [ ] **Step 5: Fixture Z arm 2, the zero-results moved case.** `expect_exit=EXIT_WRONG`; **no
      `run.yaml`**, **no `executions.jsonl`**, **2 ledger lines**, `latest` and `latest.txt` both
      absent, `E-APPARATUS-CHANGED` in the output. Because the helper now returns `run_dir: None`
      here, the test globs `results_dir` for `run_*` itself.

- [ ] **Step 6: run.** `uv run pytest` → **previous + 3 passed**, and task 12's three pins green.

- [ ] **Step 7: three mutations.** (a) return before the record phase for every stop: G1's and U's
      run.yaml assertions must FAIL — no `run.yaml` at all, which is Part A's measured
      record-lost shape. (b) write a record for the zero-results case too: arm 2 must FAIL on
      `run.yaml` existing. (c) append the finding to `c` instead of a fresh collector: assert on the
      rendered counts line, which inflates past one problem. Revert each by editing back.

- [ ] **Step 8: commit.**

---

## Task 8: `EXIT_EXTERNAL`'s reader, and the precedence

**Runs after task 7. Surface: `run`.**

**Files:**
- `src/publishable/cli.py`
- Test: `tests/test_cli.py`

**Ruling (Decision 6): `cli.command_run`'s final mapping gains one branch — an
`apparatus_unreachable` stop returns `EXIT_EXTERNAL` regardless of the status it wrote — and the
run-start containment handler returns `EXIT_EXTERNAL` for `E-APPARATUS-RAISED` and `EXIT_WRONG` for
everything else it contains. Nothing else in this slice reads the constant, and nothing else in the
exit-5 family is built here.**

**Grounds.** § Exit codes and diagnostics states the precedence outright — *"`5` is separate from all
of them because it is the class you retry, and the others are not — so when both apply, `5` wins"* —
with the worked case *"writes `status: partial` and exits `5`"*. `EXIT_EXTERNAL = 5` ships in
`diagnostics.py` and is read by **nothing** in `src/` or `tests/`, re-confirmed at `814eadd` with
`EXIT_PARTIAL` as the control that finds three files. **The pin must assert the status byte and the
exit code separately**: a build deriving the code from the status returns 3, and an assertion on
either one alone cannot see it.

**A composition worth naming and not fixturing.** If an unreachable stop wrote `status: partial` and
the input manifest then failed its re-verification, `status` becomes `failed` while the code stays
`5`. That is the documented precedence, not a defect: exit 5's row describes the **fault** — *"Something
outside the machine refused"* — rather than a record, and unlike 3 and 4 it is not marked *"`run`,
`draft`, `resume` only"*, so it composes with any status. **No fixture, and no filing** — a fourth
filing for a combination this slice does not own is scope creep.

**Not built here, and named so they are not folded in:** exit 5 for *"a missing credential"* and for
*"a clone or `uv sync` that failed"*. Measured: a missing declared credential is `E-CRED-MISSING` /
`E-CRED-PARAM-MISSING` at `validate`, exiting **1** today, and the clone case belongs to `reproduce`,
which prints *specified but not built*. Both route to **H9**.

- [ ] **Step 1: the two branches**, and the final one placed so it reads the reason rather than the
      status.

- [ ] **Step 2: Fixture U's expectation moves to `EXIT_EXTERNAL`**, with **the status byte asserted
      as its own statement** — `status: partial` — beside it.

- [ ] **Step 3: the one shipped literal this slice moves.** In
      `test_a_probe_that_raises_is_a_redacted_diagnostic_at_run`, `expect_exit=EXIT_WRONG` becomes
      `expect_exit=EXIT_EXTERNAL`. Its docstring says *"exit non-zero"* and **stays true**; its
      no-`run.yaml`, redaction, and no-credential-anywhere assertions are **untouched**. Measured
      sweep at `814eadd`: this is the **only** end-to-end test asserting an exit code for a probe
      raise — `E-APPARATUS-RAISED` appears in `tests/` in exactly this test and in two direct-call
      tests on `observe_once` that assert no exit code at all. The four contract refusals' own
      `EXIT_WRONG` expectations are **unchanged** (Decision 9), and Fixture Z arm 1 is this same test.

- [ ] **Step 4: run.** `uv run pytest` → **previous + 0 new tests**, all green, with two expectations
      moved.

- [ ] **Step 5: two mutations.** (a) derive the code from the status — return `EXIT_PARTIAL` for a
      `partial` stop: Fixture U's **exit** assertion must FAIL while its **status** assertion still
      passes, which is exactly why the two are separate statements. (b) return `EXIT_EXTERNAL` for the
      moved stop too: G1's exit assertion must FAIL on 5 against 4. Revert each by editing back.

- [ ] **Step 6: commit.**

---

## Task 9: no policy knob, and what the pin cannot prove

**Runs after task 8. Surface: `validate` for arm (a), `run` for arm (b).**

**Files:**
- Test: `tests/test_validate.py`, `tests/test_cli.py`

**Ruling (Decision 7): nothing configurable can permit a changed fact.** Part B adds no field.
§ The apparatus core can only observe: *"A changed fact fails the run, with no policy knob … a flag to
permit it would only ever be used to paper over the moment a result stopped being interpretable."*
`CLAUDE.md` § Invariants makes the same point structurally — **operation commands take paths and
nothing else**, and a mode gets its own command name, so there is no flag surface to add one to.

**What this costs, said plainly rather than sold as free.** An operator who knowingly changed the
apparatus mid-run cannot finish the run. That is the point: the two periods are two datasets, the
ledger keeps both, and the route is a second run joined in a `study`.

- [ ] **Step 1: arm (a), Fixture K's schema arm.** `limits: {allow_apparatus_change: true}` through
      `validate_config` reports `E-CONFIG-KEY-UNKNOWN` at path `limits.allow_apparatus_change`, and
      the same config without that key does not. **Assert on the difference, alongside the fixture's
      incidental `E-NAME-DIR`, never on a total code set** — measured at `814eadd`. The refusal itself
      is the control that must report, and its absence in the control is what makes it attributable.

- [ ] **Step 2: arm (b), Fixture K's most-permissive arm.** G1's run with every existing `limits` key
      at its most permissive — `max_failed_fraction: 1.0` is load-bearing, since the neighbouring
      guard fires on `>` and so can never fire at `1.0` and cannot be confused with the gate — still
      stops, with G1's computed counts and `status: failed` at exit 4. Reconcile any extra warning the
      permissive values earn rather than asserting a total set.

- [ ] **Step 3: the sentence stating what the pin cannot prove**, in the test's own docstring:
      neither arm can prove that no *future* knob will be added. Arm (a) pins the schema; arm (b) pins
      that today's most permissive config does not soften the gate. **Nothing can pin the absence of a
      field nobody has written**, and a docstring claiming otherwise would be a name claiming a
      guarantee no assertion makes.

- [ ] **Step 4: run.** `uv run pytest` → **previous + 2 passed**.

- [ ] **Step 5: the mutation.** Make the gate consult `(doc.get("limits") or {})` for any
      permissive-looking key and return early. Arm (b) must FAIL: the run completes at exit 0 instead
      of stopping at exit 4 with 2 executions. **Arm (a) is blind to it and says so** — a schema
      refusal cannot see a code path. Revert.

- [ ] **Step 6: commit.**

---

## Task 10: `batch` and the apparatus stay independent

**Runs after task 9. Surface: `run`.**

**Files:**
- Test: `tests/test_cli.py`

**Ruling (Decision 8): Part B changes nothing about `batch`, and ships the test that says so.**
`CLAUDE.md` defines `batch` as *"the state of the apparatus it measures through"*, which is precisely
the sentence that invites someone to wire the two together. Measured at `814eadd`: `apparatus.py`
names `batch` nowhere and `replication.py` names the apparatus nowhere; the live wire is
`W-REPL-DETERMINISTIC`, which reads **step declarations**. Part B is the first slice that can stop a
run over apparatus state, so it is the slice that owes the pin.

- [ ] **Step 1: Fixture B's two arms, with two of everything.** Two `tmp_path` subdirectories, two
      installed distributions, two module names, two probe names, two template names — because the
      probe's counter is module-level and `sys.modules` caches across the session. The shipped
      precedent is `test_two_runs_with_identical_facts_share_a_hash_and_one_changed_fact_moves_it`
      with `_APPARATUS_ASSAY_TEMPLATE_2` and `h7d_probe2`. **Equal `n` and it belongs in the test's
      docstring:** with unequal `n` the arms have different execution counts, so their ledgers differ
      in length for a reason that has nothing to do with the apparatus, and a fixture whose two arms
      differ for an uninteresting reason cannot see the interesting one.

- [ ] **Step 2: the assertions.** The ordered `(phase, condition)` sequence read off
      `apparatus/probes.jsonl` is identical across the arms; `provenance.apparatus.facts` and
      `provenance.apparatus.hash` are identical; `len(executions.jsonl)` is **2** in both, which is
      "the stop lands at the same execution index". **Not on whole output** — the `batch` arm earns
      `W-REPL-DETERMINISTIC`, so stdout differs for a reason that is not the apparatus, and that
      difference is named in the docstring rather than asserted away.

- [ ] **Step 3: run.** `uv run pytest` → **previous + 1 passed**.

- [ ] **Step 4: the mutation.** Make the gate key its comparison on the repeat label as well as the
      condition — the shape a `batch`-aware gate would have. The arms' ledgers and stop indexes
      diverge: the `seed` arm's four distinct labels never contradict each other and the run
      completes, while the `batch` arm's single label still stops. **Two different execution counts
      from the two arms, not a crash.** Revert.

- [ ] **Step 5: commit.**

---

## Task 11: every document row this slice owes, and three filings

**Runs last. Surface: documents.**

**Files:**
- `docs/reference.md`, `docs/superpowers/spec-defects.md`

- [ ] **Step 1: § Errors core raises gains one row, for `E-APPARATUS-CHANGED`.** Located by naming
      what a sibling row **does** — it follows the row for the declared key the probe did not return,
      because the gate runs after `check_facts`'s four checks — and **never by position**. The row
      states the comparison (per `(condition, fact)`, against the first answered value), what the
      message names, and the outcome: the plan stops where it stands, `status: failed`, the record
      kept, exit 4.

- [ ] **Step 2: `E-APPARATUS-RAISED`'s existing row is rewritten**, because **one row per code covers
      every emit site and every outcome**. It says today that `command_run` contains the raise and
      ends the command; after this slice the same code can also stop the plan, write `status:
      partial` and exit `5` when executions had already run. Both outcomes belong in the one row, and
      the `KeyboardInterrupt` carve-out stays exactly as written.

- [ ] **Step 3: check every row the insertion MOVED, and every count phrase near it.** Locators have
      been wrong twice here in rows no diff touched, and one Part A round removed four and added four.

- [ ] **Step 4: the mechanical pass in full**, then a sweep of the **four documents, `CLAUDE.md` and
      the feasibility analysis** for anything this slice's edits should have made false — **filtering
      the file list, never the sweep's output.**

- [ ] **Step 5: the three filings, in `spec-defects.md` itself.** A ledger line saying "filed" is not
      a filing. **Re-read each entry's claims about the code before touching it** — a filing's claims
      go stale like any other comment — and give *unassigned* as **a fact with a reason**, never the
      *"whichever slice does X"* form that points at a closed slice.

      1. **Strike** the `EXIT_EXTERNAL` entry — *ships and is read by nothing*, owner Part B — now
         that task 8 gives it a reader. Struck against landed code, not against an intention.
      2. **File** the four contract refusals' lost record (Decision 9): `E-APPARATUS-RETURN`,
         `-FACT-TYPE`, `-FACT-MISSING` and `-FACT-CREDENTIAL` continue to end the command with a
         redacted diagnostic, no `run.yaml` and exit 1, mid-plan as at run start, so executions
         already paid for lose their run record. **Unassigned is a fact with a reason:** no chartered
         slice contains this work, because no `reference.md` sentence sites a fact-contract failure at
         run time, so there is no section a slice could be said to own. **The checks its owner must
         make:** whether the fault recurs identically on the next call (a declaration mismatch does;
         an unreachable apparatus need not); what `status` such a record would carry, given § What
         `status` means has no row for it; and whether assembling a record on that path costs anything
         Fixture Z's boundary did not measure. Include the measurement: a declared key missing on call
         4 gives exit 1, `E-APPARATUS-FACT-MISSING`, no `run.yaml`, one execution paid for.
      3. **File** `max_failed_fraction`'s truncation status, **which is also where task 1's remainder
         goes** — both halves are one document-versus-code disagreement about one guard, and splitting
         them across two entries would leave two records to keep in step. Say so in the entry, so a
         reader looking for task 1's remainder finds it here. **Unassigned is a fact with a reason:**
         the guard belongs to no remaining chartered slice, and Part B declines it as a neighbouring
         mechanism's semantics. **The checks its owner must make:** that the current behaviour is
         **pinned with a written justification** in
         `test_max_failed_fraction_is_measured_against_the_test_partition`'s docstring, which a closer
         must **argue against rather than discover**; that the all-completed, mixed and
         nothing-completed cases are three separate answers today and may need three rulings; which of
         § What `status` means' passages governs, given that **no row describes the all-completed
         truncation at all**; and that `run_status` already carries the `max_failed_fraction` reason
         after Part B, so the change is one mapping entry plus the document rows — verified against
         the code rather than assumed from the entry.

- [ ] **Step 6: the report enumerates what was filed against the three that were owed**, and says for
      each whether it is its own entry or a clause inside another, with the reason. Producing two
      entries where three were named, without saying why, reads as a missing filing.

- [ ] **Step 7: untouched and named so they are not folded in.**
      `BaseTemplate.field_convention`, declarable on a shipped class and read by nothing, stays
      **unassigned**; `io.reuse_from` stays **unassigned** and is **not** apparatus — it is what keeps
      six configs non-executable, so no sentence here may imply otherwise.

- [ ] **Step 8: run all four gates and commit.**

---

## Corrections against the code

**Written 2026-08-19 against `main` at `814eadd`**, correcting the design
(`docs/superpowers/specs/2026-08-19-apparatus-part-b-design.md`). Per `CLAUDE.md`, **the spec's body
is not retro-edited** — this section is appended and says what it replaces. Every claim below was
produced by **running** something or by reading the named source at `814eadd`; none is carried from a
scoping.

**1. `run_status` lives in `run_record.py`, not in `runner.py`.** The design's task 6 names the
function and its new signature without naming the file, and `runner.py` is the obvious guess because
`execute_plan` and `ExecutionResult` live there. Measured: `run_status` is defined in
`src/publishable/run_record.py` and imported by `cli.py` from there; its only other importer is
`tests/test_runner.py`, whose three call sites pass a results list positionally and are therefore
untouched by a defaulted keyword. Task 6's files list is corrected accordingly.

**2. The truncation guard is a bare `assert`, not a coded `ContractError`.** Decision 5 says it
*"raises rather than folding, on `E-RUN-CFG-MISSING`'s precedent for asserting about core's own
callers."* Measured: `E-RUN-CFG-MISSING` is a coded `ContractError`, and every code core raises owes a
§ Errors core raises row — which this slice's own task 11 would then have to write, for a state **no
config can reach**, since with every stop carrying a reason no run trips the guard. The closer
precedent is in `execute_plan` itself, whose two shipped `assert` statements carry comments saying
they assert about core's own callers rather than about a config. Task 6 uses a bare `assert`, mints no
code, and owes no row. **This is a narrowing of the design, not a widening**, and the design's
argument for asserting at all survives untouched.

**3. `run_a_project` crashes on the exit code task 8 introduces, so task 8's "one shipped literal" is
one literal plus one helper.** The design says the run-start-raise test's *"no-`run.yaml`
and no-credential-anywhere assertions are untouched"*, which is true — but the helper cannot deliver
the document to assert on. Measured by reading and then by running: `run_a_project` returns
`run_dir: None, results: None` **only** when `expect_exit == EXIT_WRONG`, and otherwise does
`next(results_dir.glob("run_*"))` followed by `(run_dir / "executions.jsonl").read_text()`.
`executions.jsonl` is created **only** by the per-execution append inside `execute_plan`'s loop — it
is the sole writer in `src/` — so a run that stops before its first execution has no such file. Driven
at `814eadd`, a run-start probe raise leaves a run directory holding exactly `environment`,
`manifest`, `sweep.yaml`, with **no `run.yaml`, no `executions.jsonl` and no `apparatus/` directory**,
and no `latest` or `latest.txt` beside it. Under `expect_exit=EXIT_EXTERNAL` the helper would raise
`FileNotFoundError` before any assertion ran. Task 7 step 2 widens the guard to *`run_dir` is not
`None` exactly when there is a ledger to read* and **verifies it by the full suite's count** rather
than by the reading of the code that suggested it. Measured for that reading: the only two tests
asserting `doc["run_dir"] is None` are cases where **no run directory exists at all**, so both are
unaffected.

**4. `E-APPARATUS-CHANGED` must NOT join `apparatus.APPARATUS_CODES`, and the design does not say
which way to go.** Measured: that frozenset is `command_run`'s containment filter for a
`ContractError` crossing the run-start round or the `execute_plan` boundary, and its docstring states
that **every member is pinned** — after Part A's Major 2, where deleting three of five members left
the suite byte-identical at 2402. After task 5 a changed fact never crosses that boundary: the loop
breaks on it, and Decision 11 rules the run-start round unable to produce it. So admitting it would
add an **unpinned member** to the one enumeration this project has already been burned by. Task 3
mints `apparatus.STOP_CODES` instead — the two codes `execute_plan` breaks on, **both pinned**, by
Fixture U and Fixture G1 — and task 5's mutation (b) is what makes the exclusion observable. **The
cost if this is wrong**, stated rather than argued away: a changed fact reaching the run-start handler
would re-raise past the filter to `main`'s bare `PublishableError` printer, giving exit 1 with no
collector-rendered summary. It carries no credential — `check_facts` refuses a fact value containing
one before the gate ever sees a pair — and task 13's Fixture G3 is what makes the unreachability
happen rather than asserting it.

**5. Fixture T's mixed arm did not exist and had to be constructed; its numbers are measured.** The
design says the mixed arm's `partial`/3 assertion *"is also every shipped `EXIT_PARTIAL` truncation
test's assertion"*, while the same document measures — correctly — that **the shipped `EXIT_PARTIAL`
tests are not truncations**, because a step whose every execution raises is never classified as
recording and trips nothing. Both cannot be true of one fixture, so the mixed arm is new. Constructed
and run at `814eadd`: `units=20`, `limits.max_failed_fraction: 0.5`, and one `repeat`-scoped step that
records every unit on its **first** execution and raises on every later one gives
`executions.jsonl` = **2 of 5**, statuses **`[completed, failed]`**, `run.yaml` **`status: partial`**,
exit **3**. The mechanism is `_units_failed_anywhere`'s union across recording executions: after the
raising execution every unit is recorded under the first repeat label and not under the second, so 20
of 20 are unresolved, past `0.5`. Task 12 captures it as arm C.

**6. Two document sections give the gate two different comparison rules, and the design's task 1 does
not list it.** Measured by reading both in full: § The apparatus core can only observe says a
deployment *"is compared against its own first observation, never against another condition's"*, while
§ The apparatus files says `provenance.apparatus.facts` is *"the first **answered** observation of
each fact — what the gate compares against."* Those differ on exactly the
`value → null → different value` case Decision 1 rules **fails**: under *first observation* read
literally the rule is the same, but the sentence is the one a reader takes the gate's contract from,
and the design's own grounds cite the *answered* wording. Task 1 gains a step tightening the first to
match, as a minimal insertion rather than a rewrite.

**7. The all-completed truncation and the mixed truncation are both reachable, reached and pinned
today** — re-confirmed by running at `814eadd`, agreeing with the design's re-measurement and
contradicting `H7d-SCOPING.md` § 9's ground on both halves. Recorded here because task 12's arms rest
on it and because a plan repeating a scoping's claim without re-running it is what this section exists
to prevent.

**8. What survives unchallenged**, stated so this section is not read as general doubt:
`Observations._first_answered`'s keying and its never-overwrite rule; `check_facts`'s four checks in
their shipped order, including the containment match Part A's whole-branch review added;
`_observe_one` as the one place the per-round order is fixed; `execute_plan`'s unconditional
`results.append` per iteration and its `max_failed_fraction` `break` as the only truncation; the
`E-INPUT-CHANGED` analogue setting `status = "failed"`, writing the record and exiting 4;
`EXIT_EXTERNAL = 5` defined in `diagnostics.py` and read by nothing in `src/` or `tests/`, with
`EXIT_PARTIAL` as the control that finds three files; `limits` as a closed key set answering
`E-CONFIG-KEY-UNKNOWN`; `max_failed_fraction: 0.2` materialized into every generated config;
`apparatus.py` naming `batch` nowhere and `replication.py` naming the apparatus nowhere; Part A's
`validate`-calls-no-probe pin; and the zero/six/three figures.

---

## What could not be measured

1. **Whether a `run.yaml` can be assembled over an empty results list.** No fixture at `814eadd` can
   produce a stop with zero results, because no stop exists yet — which is exactly why Decision 4 does
   **not** put that path on the failure route. Fixture Z's two arms are what will settle it once the
   code exists, and if assembling proves safe the ruling can be revisited **with the document row it
   would owe**.
2. **Anything about `dry-run`, `freeze`, `diff`, `reproduce`, `resume`.** All five print *specified
   but not built*, so every claim here about them is a **spec claim**, read, never a build fact — the
   gate's composition with `resume`'s restart most of all.
3. **The nine configs' actual plugin.** `publishable-llm`, `llm_screen` and `llm_deployment` are
   designs in the feasibility analysis, not code. Fixture P is a documented substitution — the same
   one every § Executability entry has used since 2026-08-16 — and it is a substitution, not the thing.
4. **A real metered probe**, deliberately. Quota constrains **placement, not testability**: core only
   ever needs a fake, and the one behaviour no fixture can stand in for — a hosted deployment that
   answers a fact on most calls and omits it on some — is exactly why `null` is a legal value, why
   Fixture G1 encodes that shape by hand, and why an integration test against a real deployment would
   be a **worse** pin.
5. **Whether any shipped test asserts a literal this slice changes beyond the one.** Swept at
   `814eadd`: `E-APPARATUS-RAISED` appears in `tests/` in exactly three places — one end-to-end test
   with an exit-code expectation (task 8's literal) and two direct-call tests on `observe_once` that
   assert no exit code. The four contract refusals' `EXIT_WRONG` expectations are untouched by
   Decision 9, and `run_status`'s test call sites pass positionally. What remains unmeasured is
   whether a **mutated** build moves any other literal, which needs a build.
6. **Whether Fixture G1 is the smallest fixture separating its six readings.** It separates them; no
   smaller one was searched for, and a smaller one would have to be checked against the same six.
   **The design states outright that a two-observation fixture cannot separate the three transitions**,
   which is the constraint any substitute must meet.
7. **Whether Part A's Fixture N test is a real sentinel for a spuriously-firing gate.** It looks like
   one — its probe answers `calibration_id` `null` on its first call per condition and a value
   afterward — but nobody has run the mutation, because the gate did not exist when it was written.
   Task 13 step 3 prescribes the measurement and does **not** assume its outcome; if the sentinel is
   imaginary, a fixture is owed there.

---

## Plan self-review

- **Every task states its surface** — `validate`, `run`, a direct call, or documents — because
  `validate` collects rather than aborting and a refusal never makes a later check unreachable. Task 4
  is the one task with two surfaces and it says which assertion is which, and why the direct-call one
  cannot be end-to-end at that commit.
- **Every prescribed mutation names the assertion that catches it and why its branches differ.** The
  places where a mutation **cannot** discriminate are named as such rather than dressed up: the
  truncation assert's deletion and its over-broad suppression are **blind end to end** and pinned by a
  direct call (task 6), Fixture K's schema arm is blind to a code-path mutation (task 9), and Fixture
  G1 is blind to the most-recent comparison by design (Fixture G2 is its only pin).
- **The gate's fixture separates all four transitions in one run, and the fifth is G2's.** Every count
  is derived in writing from the call schedule, and every derived value is recomputed by the test from
  what it read — including the one recompute that is itself a discriminator.
- **The status byte and the exit code are separate assertions** wherever both move, which is the only
  way the `EXIT_PARTIAL`-for-`partial` mutation is visible.
- **A guard pin exists, it runs first, and it is captured from real runs.** Its mutation is the
  `stopped_at` key Decision 3 refuses, and no task may edit it: a failure there is a finding.
- **No task claims this slice unblocks a config.** Zero configs; six with no remaining core-side
  blocker; three executable; both unmoved; the only direction available is **down**.
- **The controller's order is not reversed.** Task 1 settles § What `status` means for the apparatus
  and files the remainder; task 6 changes no shipped expectation and no docstring;
  `test_max_failed_fraction_is_measured_against_the_test_partition` is named in § Global Constraints as
  untouchable, with "that is a finding, not a change" stated; and Fixture T's arms are captured
  **before** `run_status` moves rather than after.
- **Three filings are owed and task 11 enumerates them against what it filed**, with the reason a
  clause inside another entry is a clause rather than an entry of its own.
