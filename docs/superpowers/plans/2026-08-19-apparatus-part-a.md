# H7d Part A — the apparatus: observe and record — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to
> implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** a run whose template declares an `apparatus_probe` stops writing a false
`apparatus: null`. Core resolves the declared probe through the dispatch a resolver already uses,
calls it with this condition's `cfg`, refuses a fact value equal to a credential core read, projects
what came back onto `apparatus_facts`, appends every observation to `apparatus/probes.jsonl`, and
assembles `provenance.apparatus`'s five sub-keys from what it observed. Nothing here compares two
observations, and nothing here stops a run that is already executing.

**The payoff, stated so it cannot be rounded. Part A unblocks ZERO configs.** All nine configs in
`docs/feasibility-llm-growth-studies.md` return exactly `['W-DATA-CLUSTER-UNDECLARED']` through
`validate_config` — measured at `0faa2e3` in `docs/superpowers/H7d-SCOPING.md` § 7 with its can-fail
control firing. **Six with no remaining core-side blocker and three executable both stay exactly
where H4b-1 left them.** This slice retires **no** refusal; it mints refusals. **The only direction
it can move a config-level count is down**, once a probe that fails to yield a declared key becomes
a reachable error. No task may write a sentence putting a closed filing and an executable-run count
in one breath. What Part A is worth instead: a run's record stops lying, and `PROBES` and
`apparatus_facts` — two members of the shipped-but-unread family this repo has filed three times —
gain their first readers.

**Architecture.** One new module, one new exported construct, five new error codes, one new warning,
one new run artifact, one new `provenance` block.

- **`src/publishable/apparatus.py`** holds everything phase-independent: the `Apparatus` construct,
  `_probe_for` (`units._resolver_for`'s sibling), the credential check, the scalar walk, the
  `apparatus_facts` projection, the ledger append, the per-condition accumulation, the `unobserved`
  counts, the record block and its hash. **Nothing about `dry-run` lives in it**, and nothing about
  a gate: those are H9's and Part B's callers of the same functions.
- **`apparatus.Observer`** is the one object a caller holds. It is constructed by
  `cli.command_run` from the resolved template, the resolved conditions, the resolved `cfgs`, the
  run directory and the credentials mapping `command_run` already binds — the single-authority
  shape `holdout_plan` and `group_axes` already use — and it exposes exactly
  `observe_round(phase, condition_index)`, `block()` and `warn_unanswered(collector)`. `run` calls
  the first at run start and inside `execute_plan`'s loop; H9's `dry-run` and H8's `freeze` call it
  with their own `phase`. **Nothing is stubbed for an unbuilt command** (Decision 14).
- **`runner.execute_plan` derives nothing about the apparatus.** It gains one defaulted keyword,
  `observer`, and calls `observe_round` before each execution with `execution.condition_index`. The
  condition list and the `cfgs` live on the `Observer`, because the plan's own `conditions_list` is
  built from executions and is **empty** for a pipeline of `run`- and `summary`-scoped steps alone.
- **A probe's failure ends the command; it never truncates a plan** (Decision 12). Every
  `ContractError` `apparatus.py` raises crosses `execute_plan`'s boundary and is caught by
  `command_run`'s wrapper around that call, rendered through a fresh `Collector` carrying
  `credentials`, and answered with `EXIT_WRONG` — byte-for-byte the roster path H7b Part B shipped.

**Tech stack:** Python ≥ 3.11, `pytest`, `ruff`, `mypy`. No new dependency. The changes land in
`src/publishable/apparatus.py` (new), `src/publishable/__init__.py`, `src/publishable/cli.py`,
`src/publishable/runner.py`, `src/publishable/validate.py`, `docs/reference.md`,
`docs/experimental-designs.md`, `docs/superpowers/spec-defects.md`, and the test modules
`tests/test_apparatus.py` (new), `tests/test_cli.py`, `tests/test_validate.py`,
`tests/test_runner.py`.

**Spec:** `docs/superpowers/specs/2026-08-19-apparatus-part-a-design.md` — read it beside this plan.
**It is the binding authority and this plan argues from it.** **Its body must not be edited.** Where
this plan measured something that contradicts it, the disagreement is recorded in
[§ Corrections against the code](#corrections-against-the-code) at the end of this file, appended by
this plan's author and extended by no task.

**Measurement this plan argues from:** `docs/superpowers/H7d-SCOPING.md` **including its appended
correction** (§ 0.3's exit-code claim is false; `EXIT_EXTERNAL = 5` ships with no reader), taken
2026-08-19 against `0faa2e3`, and this plan's own re-measurement against **`main` at `4508ea6`**,
this branch's point. Every signature, record key, helper name, fixture shape and document section
below was read from the source named beside it **at `4508ea6`**, not carried from the scoping.
**Nothing is cited by line number.**

**Baseline, measured 2026-08-19 in the FOREGROUND at `4508ea6`:**

- `uv run pytest -q` → **2363 passed, 1 skipped, 2 xfailed** in 139.37 s
- `uv run ruff check .` → **All checks passed!**
- `uv run ruff format --check .` → **80 files already formatted**
- `uv run mypy` → **Success: no issues found in 45 source files**

**Task count: 18.** The design's 17 in its own grain and its own numbering, plus **task 18, the
guard pin, which runs FIRST** — H4d's task 27 is the precedent for a pin numbered last and executed
first. 18 tasks make 18 commits.

---

## Sequencing

**Execution order: 18 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 15 → 11 → 12 → 13 → 14 → 16 → 17.**

Each task restates the constraint it depends on in its own text, because an implementer sees only
their own task.

| Constraint | Why, and where it is enforced |
|---|---|
| **Task 18 first** | It pins the record shape `cli.py` writes **today** — the full `provenance` key list and `apparatus is None` for a template declaring no probe — and task 11 is the task that moves that surface. A pin captured after the move records the move, not the baseline. Its literals were captured at `4508ea6` by a real `run` and are written into the task as literals |
| **Task 1 before every code task** | The design's Decision 1: three checks are sited at `dry-run` in `reference.md`, and `dry-run` does not exist in this build. No code may emit against a sentence the repo has not corrected. **Two sentences in `reference.md` and one row in `experimental-designs.md`** — a one-file sweep is this repo's named habit, and three sweeps in one recent slice each stopped one file short |
| **Tasks 2 and 3 before 4** | There is nothing to return and no name to call until the construct exists and a name resolves |
| **Task 4 before 5, 6, 7** | Each of the three checks takes the mapping an invocation returned |
| **Tasks 5, 6, 7 before 9 and 10** | A call site added before its checks is the slice Decision 1 refuses to ship, **even transiently inside the branch** |
| **Task 8 before 9 and 10** | Both placements append to the ledger |
| **Task 15 immediately after 10** | It is the call-count contract for exactly what 9 and 10 wire, and H9's `dry-run` must be able to state that number before a run is scheduled. Landing it in the same batch is what makes batch 3's review a `run`-level review |
| **Tasks 9 and 10 before 11 and 12** | The record and its hash are assembled from what was observed |
| **Task 14 may land any time after 3** | It is a claim about a path that must stay callless. It sits in the last batch because its review is a guard/document review, not because it waits on 10 |
| **Tasks 16 and 17 last** | Every code documented then exists, every row is written against emitted behaviour rather than intent, and the two struck filings are struck against code that has landed rather than against an intention to land it |

### Two deviations from the design's grain, each argued

**(a) Task 18 exists at all.** The design names no regression pin. The preceding slice's batch 1
built one and it caught a spurious key three batches later without ever being edited; the surface
this slice rewrites — `cli.py`'s unconditional `"apparatus": None` — is exactly that shape. The pin
is written against template `generic`, so it needs no plugin and no probe at all.

**(b) Task 5 mints a fifth code, `E-APPARATUS-RETURN`.** The design enumerates four codes and gives
a probe returning something that is not an `Apparatus` — or an `Apparatus` whose `facts` is not a
mapping of `str` keys — no refusal at all. Measured: `coercion.coerce_scalars` iterates
`values.items()` and never checks a key's type, so both shapes reach `run` as an `AttributeError`
or a `TypeError` escaping `command_run`. `E-RESOLVER-YIELD` exists one module over for the
identical fault at the identical boundary. See § Corrections, correction 4; **the payoff sentence in
task 16 and in `CLAUDE.md`'s eventual entry says five codes, not four.**

---

## Batching — five batches, one report and one review each

| Batch | Tasks | The seam, and why it is there |
|---|---|---|
| **B1** | **18, 1, 2, 3** | **Documents and constructs.** Nothing in it calls a probe, so no later batch emits against an uncorrected sentence, and the guard pin lands before task 11 can move what it covers. The review here is a *document* review: it must read the two `reference.md` sentences and the `experimental-designs.md` row against each other |
| **B2** | **4, 5, 6, 7, 8** | **Every check and the ledger, and not one call site.** All five are phase-independent functions in `apparatus.py`, all testable by **direct call** with a fake probe, no `run` and no `validate` involved. The seam is that B2 can be reviewed for arithmetic and refusal-ordering alone, with no wiring in the picture |
| **B3** | **9, 10, 15** | **Placement.** The first batch in which a real `run` calls user code, and task 15's call-count fixture is the pin for exactly what 9 and 10 wire. **Its review must be a `run`-level review**: on the preceding slice a Critical survived a batch because every direct-call probe hand-built the maps and only an end-to-end `run` reached the defect |
| **B4** | **11, 12, 13** | **The record**, assembled from what B3 observed. Reviewable as one property — what `run.yaml` now holds and what it must not hold |
| **B5** | **14, 16, 17** | **Guards, rows and filings**, written against emitted behaviour. Task 14 could have landed in B2; it sits here because its review is the same kind as 16's and 17's, and because a guard whose subject is "no `validate` path calls a probe" is strongest when every call site the slice will ever add already exists |

---

## Global Constraints

Every task inherits all of these. They are copied verbatim rather than cross-referenced, because an
implementer sees only their own task brief.

**Commands.** Tests `uv run pytest`. Lint `uv run ruff check .`. Format `uv run ruff format .`.
Types `uv run mypy`. All four must pass before a commit.

**Run `uv run pytest` DIRECTLY, in the foreground, and wait for it.** It takes about two and a
third minutes. **Never construct a wait, a monitor, a poll or a background run around it** —
several agents on preceding slices stalled that way and one stopped with a mutation still applied.

**Verify format with `uv run ruff format --check .`, never the bare form.** A previous brief in this
repo wrote the bare form where it meant `--check` and rewrote 67 files.

**Every task states its own DELTA, not an absolute.** Compute the absolute from your own previous
run and reconcile any difference before committing.

**A probe is user code that costs somebody else's quota, and core only ever needs a FAKE.** Every
test in this plan runs with a probe this repo wrote. The stand-in, everywhere, is the shape
`tests/test_cli.py` already uses for a resolver and for a project-local template, and it is three
parts: `installed("dist-one", "1.0", {"publishable.probes": {"<name>": "<module>:probe"}})` writing
a real `.dist-info`, a module file written into that site directory holding a `@register_probe`
function, and `_local_template=` giving `run_a_project` a project-local template that declares
`apparatus_probe` and `apparatus_facts`. Request the `registries` fixture whenever a decorator runs,
and `sys.modules.pop(module, None)` in a `finally`, exactly as
`test_a_resolver_run_records_the_plugin_version_it_resolved_through` does. **No test may reach a
network, and none needs to.**

**Every literal is computed, not guessed.** Six fixtures on the immediately preceding slice failed
their own constraints — one asserting `b = 0` where 66 hits were expected, one asserting the very
value it existed to reject. Every count in this plan is derived in writing where it is stated, and
**every derived value — a hash, a per-condition fact mapping, an `unobserved` count, a condition
key — is recomputed by the test from the ledger or the `sweep.yaml` it just read**, never
hard-coded. The only hard-coded numbers are ledger line counts and the guard pin's key list.

**A mutation caught by a crash is not a pin, and a mutation caught by a string literal is not an
arithmetic pin.** On the preceding slice a fixture yielding `[0.0, 0.0]` was read as confirming a
clustered interval, when a zero-width interval is identical under every construction. Each mutation
below names the assertion that catches it **and** why its two branches can produce different
results.

**Mutation discipline, every task.** Apply the named mutation to the file it names. Run the named
test. Confirm it **FAILS**. Then `find . -name __pycache__ -type d -exec rm -rf {} +`. Then revert
**by editing the file back in place** — **never `git checkout -- <file>`**, which destroys
uncommitted work and has been mistaken for a revert twice in this repo. Confirm the test **PASSES**
again, and verify the revert by *behaviour*, never by `git status`. **Every mutation runs against
the full, unfiltered suite, in the foreground.**

**A safety argument in a comment is a claim, and needs a mutation like any other.** If a comment
you write says *this cannot happen*, make it happen. **Decision 12 is the one at risk here:** no
comment, docstring or test name in Part A may assert that an unreachable probe *cannot* stop a run
mid-plan. Part A asserts only that Part A does not make it do so — Part B is the slice that owns
`status: partial`, exit `5` and the `run_status` contract.

**`validate` collects rather than aborting.** A refusal elsewhere never makes a later check
unreachable, and `E-PROBE-UNKNOWN` never makes a later check unreachable. Ask what `validate`
**reports**, in full, as an exact set.

**Every task says whether its surface is `validate`, `run`, or a direct call**, and the task text
states it. Tasks 2–8 are direct calls. Tasks 9, 10, 11, 12, 13, 15 and 18 are `run`. Task 14 is
`validate`. Tasks 1, 16 and 17 are documents.

**Answering a question with a proxy** is this repo's most expensive habit. *Is this fact value a
credential* is answered by **equality against the values core read**, never by a name pattern or an
entropy heuristic. *Which `cfg` does this probe get* is answered by the condition the execution
belongs to, never by `cfgs[0]`.

**Documentation rules.** `×` not `x` for multiplication, including inside fenced blocks. Hyphen,
never an en dash, in anything that becomes a filename or an anchor. **Cite by section**
(`reference.md` § "The apparatus files"), **never by line number**. **No positional locators**
("the row above", "further up"): name what a sibling row *does*, and when you insert a row check
every row it **moved** and every count phrase near it. **No counts in prose or comments** and **no
call-site enumerations**. **A build fact is dated and pinned to a commit where it is true.**
**Prefer deleting a claim to rewriting it** — a rewrite invents, a deletion cannot; on the preceding
slice one comment was rewritten three times and a seventh wrong ground for one corner shipped
inside the commit fixing the sixth. **When you edit a docstring, re-read the whole one.**

**Sweeps.** **Never filter the output of a sweep whose job is to find a string — filter the FILE
LIST**, and prove each sweep can fail by running it against a string known to be present. Name the
four documents explicitly, since the development record is tracked and `*.md` no longer means what
it used to.

**§ Errors carries one row per code, covering every emit site** — not one row per site.
`E-PROBE-UNKNOWN` gains a second emit site in task 3, and its unit of work is every site that
raises *or* reports it. `E-TEMPLATE-UNKNOWN` is the instance this repo already failed on.

**The four normative documents LEAD; `src/` follows.** Where they and the code disagree, **the
document changes first** and the gap is recorded in `docs/superpowers/spec-defects.md`. The
cross-document pass governs those four **only** — never the development record under
`docs/superpowers/`, where a correction is **appended** rather than retro-edited. `spec-defects.md`
is the one exception: a closed gap is **struck** there rather than left to mislead. **This slice's
spec, `H7d-SCOPING.md` and its appended correction must not be retro-edited.**

**Do not touch the worked example.** `cohort-pilot` uses template `generic`, which declares no
probe, so its `run.yaml` keeps `apparatus: null` and every interval in `CLAUDE.md` § The worked
example stays exactly as it is.

**`tests/conftest.py` already has** an autouse `os.environ` restore, an opt-in `registries` fixture
and an opt-in `installed` distribution fixture. **Do not add duplicates, and do not add a second
autouse fixture of any kind.**

---

## The discriminating fixtures, stated once because eight tasks share them

**Carried from the design's § The discriminating fixtures, with every literal re-derived here against
the code at `4508ea6` and one shape changed for a measured reason** (§ Corrections, correction 5).
**No later task may weaken any constraint below**, and a substitute must meet all of them:

1. **Every literal is computed, not guessed**, and every *derived* value is recomputed by the test
   from what it read back.
2. **A fixture must separate every candidate reading, not two of them.** Two elements only ever
   distinguish two answers.
3. **A control asserting only absences passes identically if nothing ran.** Every control here is
   paired with something that must report.
4. **No test reaches a network.** Every probe is a function this repo wrote.

### Fixture P — the plugin, and the three parts that make it real

Measured shapes, all of them already in `tests/test_cli.py` at `4508ea6`:

- `installed("dist-one", "1.0", {"publishable.probes": {"llm_deployment": "<module>:probe"}})`
  writes a real `<name>-<version>.dist-info` with `METADATA` and `entry_points.txt` onto
  `sys.path` — the same discovery path `_check_probe` and `_probe_for` both answer from.
- A module file written into that site directory holding `@register_probe("llm_deployment")`, so
  `check_registration` has a declaration to check the key against. `sys.modules.pop(<module>, None)`
  in a `finally`, and the `registries` fixture requested, exactly as
  `_install_plate_wells_resolver`'s callers do.
- `run_a_project(..., experiment_type="cred_assay", _local_template=<source>)`, whose helper writes
  `templates/cred_assay.py` **before** `git add .` because `code_hash` covers `templates/**`. The
  template declares `apparatus_probe = "llm_deployment"` and an `apparatus_facts` list.

Both halves are load-bearing: the project-local template is what makes the declaration reachable
without publishing a plugin, and the installed distribution is what both readers of the *name*
answer from.

### Fixture F — the call count, which must separate six readings

**Design, and it is buildable with `run_a_project` as it stands — verified by a real run at
`4508ea6`:**

- `sweep={"grid": {"analysis.method": ["pearson", "spearman"]}}` → **C = 2** resolved conditions,
  labels `method=pearson` and `method=spearman`, condition keys `00_method=pearson` and
  `01_method=spearman`.
- `replication={"repeats": [{"kind": "seed", "n": 1}], "order": "as_declared"}` → one repeat.
- The scaffolded step is `repeat`-scoped → **E_c = 2** condition-bearing executions.
- One extra step whose `extra_step_source` declares `scope = "run"` → **E_none = 1**.

So `C + E_c + C × E_none` = 2 + 2 + 2 = **6 ledger lines**. **Measured, not assumed:** a real run of
exactly this shape at `4508ea6` produced `executions.jsonl` in the order `step02_wrapup` (run
scope) → `step01_summarize_units` (condition 0) → `step01_summarize_units` (condition 1) — the
`run`-scoped execution runs **first**, whatever order the steps were generated in.

**The assertion is the ordered list of `(phase, condition)` pairs, not the count alone**, because
two of the six readings collide on the count:

| Candidate reading | Lines | The pair list |
|---|---|---|
| Once per run | 1 | one `run_start`, one condition |
| Once per condition, at run start only | 2 | two `run_start`, no `pre_execution` |
| Run start per condition, then before every **condition-bearing** execution only (the narrowing Decision 3 rejects) | 4 | no `pre_execution` for the `run`-scoped step |
| Run start per condition, then one **wide-cfg** call before the condition-less execution | 5 | a `pre_execution` whose `condition` is absent from `facts` |
| Run start **once per run**, then this design's per-execution rounds | 5 | **one** `run_start` line |
| **This design** — `C + E_c + C × E_none` | **6** | the list below |

**The expected list, derived from the execution order measured above:**

```
("run_start",     "00_method=pearson")
("run_start",     "01_method=spearman")
("pre_execution", "00_method=pearson")     # the run-scoped execution's round, condition 0
("pre_execution", "01_method=spearman")    # the same round, condition 1
("pre_execution", "00_method=pearson")     # step01, condition 0
("pre_execution", "01_method=spearman")    # step01, condition 1
```

**The condition keys are read back from `sweep.yaml`, never typed twice**: the test builds them as
`f"{c['index']:02d}_{c['label']}"` from `sweep.yaml`'s own `conditions` list.

### Fixture S — which `cfg`, and why the raise test is not the pin

**Design:** Fixture F's probe returns the swept parameter it read —
`{"model_revision": cfg.parameters.analysis.method}` — as a fact.

**Assertion:** `provenance.apparatus.facts["00_method=pearson"]["model_revision"] == "pearson"` and
`...["01_method=spearman"]["model_revision"] == "spearman"`, **both read back from `sweep.yaml`'s
labels rather than written twice**, and the two values asserted **different**.

**Not** an assertion that no `E-STEP-SWEPT-PARAM` was raised. Under Decision 2 no `SweptAway` marker
is present, so such an assertion is true of a build that hands the probe nothing at all.

### Fixture N — the null accounting, every number recomputed from the ledger

**Design:** the template declares `apparatus_facts = ["model_revision", "reagent_lot", "flaky_pin"]`;
the probe answers `model_revision` for both conditions, answers `reagent_lot` **only** under
`01_method=spearman`, answers `flaky_pin` on its **first call under each condition and `null`
thereafter** — a counter kept in a file beside the probe module, since a probe is user code and may
keep its own state — and also returns one **undeclared** fact, `endpoint_fingerprint`.

**`flaky_pin` is the shape the null rule exists for**, and no fixture in the design reaches it:
§ The apparatus core can only observe describes *"a hosted deployment [that] returns a revision
fingerprint on most calls and omits it on some."* It is the case that separates a warning read off
`facts` from a warning read off per-(condition, fact) counts — under `facts` alone a partially
answered fact records its **answer** and produces no finding at all.

**The arithmetic, derived from Fixture F's six lines:** three lines carry condition
`00_method=pearson` (one `run_start`, one for its own `step01` execution, one from the condition-less
round) and three carry `01_method=spearman`. So:

- `facts["00_method=pearson"]["reagent_lot"] is None` — declared, never answered.
- `facts["01_method=spearman"]["reagent_lot"]` holds the value — the first **answered** observation.
- `facts[<either>]["flaky_pin"]` holds the value, because the first observation answered — and its
  per-condition null count is **2** all the same.
- `unobserved == {"model_revision": {"null_probes": 0, "total_probes": 6},
  "reagent_lot": {"null_probes": 3, "total_probes": 6},
  "flaky_pin": {"null_probes": 4, "total_probes": 6}}` — two null calls under each of two conditions —
  and **the test recomputes every number from the ledger it just read**, asserting the recomputation
  equals what `run.yaml` recorded.
- `endpoint_fingerprint` is present in `facts` for **both** conditions and in **every** ledger line,
  and **absent from `unobserved`** — Decision 4's fourth row, which no other fixture reaches. The
  presence assertion and the absence assertion are one pair; the absence alone would pass if the
  probe had never run.
- `W-APPARATUS-UNANSWERED` appears **exactly three times** in the run's stdout — once for
  (`00_method=pearson`, `reagent_lot`) and once for each condition's `flaky_pin` — and **not** for
  `model_revision`, **not** for (`01_method=spearman`, `reagent_lot`), and **not** for the undeclared
  fact. Three findings across six calls is also what separates the run-end grain from a per-call
  emission, which would print eight.

### Fixture K — the credential refusal, whose mutation can actually differ

**Design:** a declared credential — a project-local template with `required_env = ["PUBLISHABLE_TEST_TOKEN"]`
and `_env_file="PUBLISHABLE_TEST_TOKEN=lab7\n"` — and a probe that returns `{"model_revision": os.environ["PUBLISHABLE_TEST_TOKEN"]}`.

**The value is `lab7`: short, lowercase, ordinary-looking, and it is a whole word.** That is the
point rather than a detail. A random-looking value makes an exact-value check and an entropy or name
heuristic **agree**, so the mutation "replace exact-value matching with a heuristic" would have two
branches that cannot differ — the shape this repo has already shipped once as a proposed proof.

**Assertions:** the command exits non-zero, `E-APPARATUS-FACT-CREDENTIAL` appears in the captured
output, **no `run.yaml` exists in the run directory**, and the string `lab7` appears in **no byte of
any file under the results directory** — asserted on the **raw text** of every file, on
`test_a_project_local_template_s_credentials_are_redacted_too`'s `_files_under` sweep shape, because
a defect that lives in how a value is written is one a parsing reader undoes before the assertion.
The sweep asserts `swept` is non-empty first, so it cannot pass vacuously.

**A second credential fixture, K2, for the raise path:** the same declared credential, and a probe
whose body raises `RuntimeError(os.environ["PUBLISHABLE_TEST_TOKEN"])`. Assertions: exit non-zero,
`E-APPARATUS-RAISED` in the captured output, `<redacted:PUBLISHABLE_TEST_TOKEN>` in it, and `lab7`
in **no** byte of stdout, stderr or the results directory.

### Fixture H — the hash, as a construction and never a digest literal

The test recomputes

```python
hashlib.sha256(
    json.dumps(facts, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
).hexdigest()
```

from the `facts` mapping it read back out of `run.yaml`, and compares it to
`provenance.apparatus.hash` with its `sha256:` prefix stripped. A second assertion pins the property
a literal would have hidden: **two runs of Fixture F whose probe returns identical facts produce
identical `hash` values while their `run_id`s, timestamps and ledgers differ**, and changing one
fact value changes the hash.

---

## Task 18: the guard pin, its literals captured at `4508ea6`

**Runs FIRST, before task 1.** It pins the record shape `cli.py` writes today, which **task 11
rewrites**. A literal recorded afterwards records the change, not the baseline. **Surface: `run`.**

**Files:**
- Test: `tests/test_cli.py` (add)

**Interfaces:**
- Consumes: `run_a_project` (this module's own end-to-end driver), `yaml.safe_load` over `run.yaml`.
- Produces: nothing importable. One pin every later task's suite run must keep green.

**The property, and what it catches:** a run whose template declares **no** probe — template
`generic`, which is every run in this repo's own suite and the worked example — records
`provenance["apparatus"] is None` and **no other `provenance` key moves**. Under Decision 7 that
whole-block `null` is the honest record for a template declaring none; the scoping's `probe: null`
phrasing would reproduce the false-record defect in a new spelling, and tasks 11 and 12 are the
tasks that could do it by adding a key or a block unconditionally.

- [ ] **Step 1: the literals, captured at `4508ea6` by a real run.** These were produced by
      scaffolding a project, generating a `generic` experiment, committing and running it:

```
provenance keys, in order: ['git', 'environment', 'apparatus', 'input_manifest',
  'input_manifest_hash', 'input_manifest_changed', 'publishable_version', 'plugin_versions',
  'units', 'units_hash', 'allocation', 'allocation_hash']
provenance["apparatus"]: None
run directory entries: environment, executions.jsonl, manifest, run.yaml, sweep.yaml, <repeat dirs>
```

      **Re-run it yourself before writing the assertion** and reconcile any difference: a pin whose
      expected value was transcribed from `cli.py`'s dict rather than from a run pins the source,
      not the behaviour.

- [ ] **Step 2: write the pin.** Add to `tests/test_cli.py`:

```python
def test_a_run_with_no_declared_probe_records_a_null_apparatus_block_and_no_ledger(tmp_path, capsys):
    """The guard pin, captured at `4508ea6` before any H7d change.

    `reference.md` § The apparatus core can only observe: an experiment whose
    measurements never leave the machine declares nothing and records
    `apparatus: null` — the WHOLE block. A block present with `probe: null`
    beside four other nulls is a different record: it says a probe was asked for
    and did not name itself. Template `generic` declares no probe, so this is
    every run in this suite and the worked example both.

    The full key LIST is asserted, not just `apparatus`: a sub-key or a sibling
    added unconditionally by the record work is exactly what this catches, and
    an assertion on `apparatus` alone would not see it.
    """
    doc = run_a_project(tmp_path, capsys=capsys)
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    assert list(run["provenance"]) == [
        "git", "environment", "apparatus", "input_manifest", "input_manifest_hash",
        "input_manifest_changed", "publishable_version", "plugin_versions",
        "units", "units_hash", "allocation", "allocation_hash",
    ]
    assert run["provenance"]["apparatus"] is None
    assert not (doc["run_dir"] / "apparatus").exists()
```

- [ ] **Step 3: run.** `uv run pytest` → **2363 + 1 = 2364 passed**, 1 skipped, 2 xfailed.

- [ ] **Step 4: the mutation.** In `src/publishable/cli.py`, change `"apparatus": None,` in the
      provenance document to `"apparatus": {"probe": None},`. Run the **full** suite. The new test
      must FAIL on `is None`. **Why the two branches differ:** a dict is not `None`, and the key
      list is unchanged — so this mutation proves the assertion reads the *value*, which is the
      exact spelling Decision 7 rejects. Revert by editing the line back; confirm green.

- [ ] **Step 5: commit.** `git add -A && git commit -m "H7d Part A task 18: pin the no-probe record
      shape before anything moves"`.

---

## Task 1: the check-placement change, in `reference.md` and `experimental-designs.md`

**Runs before every code task.** Decision 1: `reference.md` sites three checks — *every key in
`apparatus_facts` came back*, *no returned value matches a credential*, *a declared fact came back
`null`* — at **`dry-run`**, and `dry-run` prints *"specified but not built in this version"* in this
build (measured at `0faa2e3`, § The measurement this rests on). Taken literally, Part A would call
user code once per execution with nothing checking that a declared key came back. **The document
changes first.** **No new command is invented, and no check moves OFF `dry-run`** — `dry-run` keeps
all three, because it also runs a probe. What changes is that `dry-run` stops being *where they
live* and becomes *one of the places they run*. **Surface: documents.**

**Files:**
- `docs/reference.md` — § The apparatus core can only observe, two sentences
- `docs/experimental-designs.md` — § Mistakes core prevents, the apparatus row
- Test: `tests/test_validate.py` (add one document pin)

**"Before every execution" is NOT narrowed.** Decision 3 rejects the narrowing an earlier draft of
the design proposed, and `reference.md` § One execution at a time states the same placement as one
of the four guarantees that make serial execution non-optional. **Read that section and change
nothing in it.**

- [ ] **Step 1: the first sentence.** In § The apparatus core can only observe, the sentence that
      begins *"So the split follows what is answerable without a call"* ends with a clause siting
      the three checks at `dry-run`. Replace that clause so it names the split it is drawing —
      `validate` answers what needs no call — and then says the yield checks run **wherever a probe
      runs**, naming `dry-run` as the first and cheapest of those places, with run start, before
      each execution, and `freeze` beside it. Keep the `validate` half of that sentence exactly as
      it is: it is correct and it survives.

- [ ] **Step 2: the second sentence.** In the paragraph beginning *"That is also the whole of what
      declaring a fact buys"*, the clause reading *"a **warning at `dry-run`** when the fact comes
      back `null`"* carries the same siting. Widen it the same way — the warning is a function of
      the observations, and a run makes observations `dry-run` never saw. **Do not add a sentence
      naming a code**; `W-APPARATUS-UNANSWERED`'s row is task 16's, and a code named in two places
      before it exists is a second source of truth for build state.

- [ ] **Step 3: the third file, and it is the one a one-file sweep misses.**
      `experimental-designs.md` § Mistakes core prevents' apparatus row ends *"so an
      unevenly-reported pin stays declarable and `dry-run` warns instead of the run failing."* The
      same widening applies. **Three sweeps in one recent slice each stopped one file short**, and
      this row is the third file.

- [ ] **Step 4: sweep for the claim, not for the wording.** Run, over a **file list** naming the
      four documents explicitly and never filtering a sweep's output:

```
grep -n "dry-run" README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md
```

      Read **every** hit and decide, for each, whether it states `dry-run` as a *place a probe runs*
      (correct, keep — § CLI reference's row, § Before you spend it, § Exit codes and diagnostics'
      cost ordering) or as *the only place a yield is checked* (wrong, fix). Prove the sweep can
      fail by running it against a string known to be present.

- [ ] **Step 5: the document pin.** Add to `tests/test_validate.py`, beside the sweep-shaped tests
      already there:

```python
def test_the_yield_checks_are_not_sited_at_dry_run_alone():
    """Decision 1: the projection, the credential check and the null warning are
    phase-independent, so no document may site them at a command that does not
    exist in this build. Asserted on the RAW text of both documents, with a
    length guard so an empty or moved file cannot make it pass vacuously."""
    import pathlib

    root = pathlib.Path(__file__).resolve().parent.parent
    reference = (root / "docs" / "reference.md").read_text()
    designs = (root / "docs" / "experimental-designs.md").read_text()
    assert len(reference) > 100000 and len(designs) > 10000
    assert "warning at `dry-run`" not in reference
    assert "`dry-run` warns instead of the run failing" not in designs
    assert "wherever a probe runs" in reference
```

      **Verify each of the two absent strings is PRESENT at `4508ea6` before you edit** —
      `grep -c 'warning at `dry-run`' docs/reference.md` and the sibling — or the pin asserts the
      absence of something that was never there.

- [ ] **Step 6: the mechanical pass** on both edited files: every relative link and `#anchor`
      resolves, no two headings collide, table rows match their header's column count, no trailing
      whitespace or tab, `×` not `x`, hyphens rather than en dashes in anything becoming an anchor.
      Fenced blocks skipped.

- [ ] **Step 7: run.** `uv run pytest` → **previous + 1 passed**.

- [ ] **Step 8: commit.** `git add -A && git commit -m "H7d Part A task 1: the yield checks run
      wherever a probe runs, not at dry-run alone"`.

---

## Task 2: `Apparatus`, exported, and where its value contract is NOT enforced

**Runs after task 1, before task 4. Surface: direct call.**

**Files:**
- `src/publishable/apparatus.py` (new), `src/publishable/__init__.py`
- `docs/reference.md` — § The importable surface's `Apparatus` row `not yet built` → `built`;
  § Package layout's `apparatus.py` marker
- Test: `tests/test_apparatus.py` (new)

**The code:**

```python
@dataclass(frozen=True)
class Apparatus:
    """What a probe returns: `facts`, and nothing else."""

    facts: Mapping[str, Any] = field(default_factory=dict)
```

**One field, because § The importable surface's row says `What a probe returns: facts`** and a
second field would be a surface no document describes.

**The value contract is NOT enforced in `__init__`, and that is a ruling rather than an
omission.** `Apparatus` is constructed inside the probe's own body, so a refusal raised there is
indistinguishable from any other exception out of user code: task 4's wrapper would report it as
`E-APPARATUS-RAISED`, a code whose § Errors row describes a different fault. `Unit` is the shipped
precedent for exactly this split — it freezes its attributes and validates nothing, and
`units._from_resolver` is where a yielded non-`Unit` is refused, under `E-RESOLVER-YIELD`. **Every
check in this slice therefore runs at core's boundary, in task 5.**

- [ ] **Step 1: write the module and the export.** Create `src/publishable/apparatus.py` with the
      dataclass above and a module docstring citing `reference.md` § The apparatus core can only
      observe and § The apparatus files. Add `Apparatus` to `publishable/__init__.py`'s imports and
      to `__all__`, keeping `__all__` in the sorted order it is already in.

- [ ] **Step 2: the two document rows.** § The importable surface's `Apparatus` row moves from
      `not yet built` to `built`. § Package layout's `apparatus.py` entry drops its
      `— not yet built` marker. **Name what each sibling row does when you locate them; never a
      position.** `reference.md`'s own sentence *"A row marked `not yet built` is a promise, not an
      export. Importing one raises `ImportError` today"* **derives** its claim from the `Status`
      column and needs no edit — do not rewrite a self-maintaining sentence into an enumeration.

- [ ] **Step 3: the tests.** In `tests/test_apparatus.py`:

```python
def test_apparatus_is_importable_from_the_one_root_and_is_frozen():
    from publishable import Apparatus

    a = Apparatus(facts={"model_revision": "r1"})
    assert a.facts == {"model_revision": "r1"}
    with pytest.raises(Exception):
        a.facts = {}          # frozen: dataclasses raises FrozenInstanceError


def test_apparatus_accepts_a_shape_core_will_later_refuse():
    """The contract is enforced at core's boundary, not in `__init__` — a raise
    inside a probe's own body cannot be told from any other probe raise, and
    would be reported under a code whose row describes a different fault. This
    test is what stops a later task from "fixing" that by validating here."""
    from publishable import Apparatus

    assert Apparatus(facts={"nested": {"a": 1}}).facts["nested"] == {"a": 1}
```

- [ ] **Step 4: run.** `uv run pytest` → **previous + 2 passed**. `uv run mypy` must report **46**
      source files, one more than the baseline's 45.

- [ ] **Step 5: the mutation.** Add a `__post_init__` to `Apparatus` that raises `ContractError` on
      a non-scalar fact value. Run the full suite:
      `test_apparatus_accepts_a_shape_core_will_later_refuse` must FAIL. **Why the two branches
      differ:** the fixture constructs exactly the shape the mutation refuses, so one branch returns
      an object and the other raises. Revert by deleting the method; confirm green.

- [ ] **Step 6: commit.** `git add -A && git commit -m "H7d Part A task 2: the Apparatus construct
      and its one field"`.

---

## Task 3: probe dispatch, as `units._resolver_for`'s sibling

**Runs after task 2, before task 4. Surface: direct call** (its second surface, `validate`, already
exists and is untouched).

**Files:**
- `src/publishable/apparatus.py`
- Test: `tests/test_apparatus.py`

**Interfaces:**
- Consumes: `plugins.scan_group`, `plugins.load_entry_point`, `plugins.check_registration`,
  `plugins.declared_names` — all four read from `src/publishable/plugins.py` at `4508ea6`, all four
  already with production callers through `units._resolver_for`.
- Produces: `apparatus.PROBE_GROUP = "publishable.probes"` and
  `apparatus._probe_for(name) -> Callable[..., Any]`.

**The code follows `units._resolver_for` step for step**, three steps and three codes in the order
the information arrives: `scan_group(PROBE_GROUP)` → `E-PROBE-UNKNOWN` when nothing registers the
name, naming every member of the group it did find; `load_entry_point(ep)` → `E-PLUGIN-LOAD`;
`check_registration(ep, declared_names(PROBE_GROUP, fn))` → `E-PLUGIN-DECORATOR`. **A collision
between two distributions claiming the key is not decided here** — `validate`'s own check reports
`E-PLUGIN-COLLISION` over the complete claim set, and the first claimant is used here rather than
re-deciding a tie, exactly as the resolver's dispatch documents.

**This gives `PROBES` its first reader**, through `declared_names`, which closes the H7d half of
that filing (task 17 strikes it). **`E-PROBE-UNKNOWN` becomes dual-surface** — reported by
`validate._check_probe` from metadata, raised here at dispatch — and **its § Errors row is task 16's
work, one row per code covering both sites.**

- [ ] **Step 1: write `_probe_for`.** Its docstring states the three steps and their codes, and
      states that the two sources of truth the scoping measured — the entry-point metadata scan and
      the `PROBES` mapping the decorator fills — are reconciled by checking the declaration against
      the key, never by reading `PROBES` alone.

- [ ] **Step 2: the tests**, all three with the `installed` and `registries` fixtures and a real
      `.dist-info`, on Fixture P's shape:

```python
def test_a_registered_probe_name_resolves_to_the_decorated_function(installed, registries, tmp_path):
    """Positive control: without it, the two refusals below pass identically if
    nothing resolves at all."""


def test_a_probe_name_no_distribution_registers_is_E_PROBE_UNKNOWN(installed, registries, tmp_path):
    """Answered from metadata alone: assert the message names the group's other
    registered member, which is what says the scan ran rather than an empty
    dict being consulted."""


def test_a_probe_whose_module_declares_a_different_name_is_E_PLUGIN_DECORATOR(
    installed, registries, tmp_path
):
    """The entry-point key and the `@register_probe` argument disagree — the
    check that makes `validate`'s metadata answer and the registry agree."""
```

- [ ] **Step 3: run.** `uv run pytest` → **previous + 3 passed**.

- [ ] **Step 4: the mutation, and it is arithmetic rather than a crash.** In `apparatus.py`, delete
      the `check_registration(...)` call. Run the full suite:
      `test_a_probe_whose_module_declares_a_different_name_is_E_PLUGIN_DECORATOR` must FAIL — under
      the mutation the mismatched module resolves and returns a callable instead of raising.
      **Why the two branches differ:** the fixture's entry-point key and decorator argument are
      deliberately different strings, so one branch raises and the other returns. Revert; confirm
      green.

- [ ] **Step 5: commit.** `git add -A && git commit -m "H7d Part A task 3: probe dispatch, the
      resolver's sibling, and PROBES's first reader"`.

---

## Task 4: probe invocation, and the raise path

**Runs after task 3, before 5, 6 and 7. Surface: direct call.**

**Files:**
- `src/publishable/apparatus.py`
- Test: `tests/test_apparatus.py`

**The code:**

```python
def observe_once(probe: Callable[..., Any], cfg: Any, *, probe_name: str) -> Apparatus:
    """Call a probe with ONE condition's cfg and return what it gave back."""
    try:
        returned = probe(cfg)
    except KeyboardInterrupt:
        raise KeyboardInterrupt from None
    except BaseException as exc:
        raise ContractError(
            f"probe `{probe_name}` raised {type(exc).__name__}: {exc}",
            code="E-APPARATUS-RAISED",
        ) from exc
    return returned          # its shape is task 5's boundary check
```

**Every clause is H7b Part B's shipped resolver path, cited rather than re-derived** — read
`cli.command_run`'s roster `except BaseException` block at `4508ea6` and copy its reasoning:
`except BaseException` so a probe calling `sys.exit()` is covered; `KeyboardInterrupt` re-raised
**fresh and argument-less, `from None`**, so Ctrl-C still stops the command and a
`KeyboardInterrupt("…secret…")` a probe body constructed never reaches Python's own printer.

**The redaction is NOT here, and that is the whole ruling.** This function builds the message; the
**call site** turns it into a diagnostic through a fresh `Collector` carrying `credentials`, which
is what redacts. **One mechanism per surface, deliberately:** two redacting mechanisms would make
each other's mutation blind, and a mutation whose two branches cannot differ is one this repo has
already shipped as a proposed proof. Tasks 9 and 10 own the call sites, and Fixture K2 is the pin.

**A probe receives `runner.resolve_condition_cfg(doc, condition)` and never
`runner.resolve_wide_cfg`** (Decision 2): § The apparatus core can only observe says a probe *may*
read a swept parameter *and usually must*, and the wide cfg plants a `SweptAway` marker that raises
`E-STEP-SWEPT-PARAM` on exactly that read. **Which cfg reaches this function is the caller's
choice, and tasks 9 and 10 make it**; this task's tests pass a cfg directly.

- [ ] **Step 1: write it**, with a docstring stating the three clauses above and no claim about
      where redaction happens beyond naming the caller as its site.

- [ ] **Step 2: the tests.**

```python
def test_a_probe_that_raises_becomes_a_coded_refusal_carrying_its_message():
    """`E-APPARATUS-RAISED`, the sibling of `E-RESOLVER-RAISED`. The message is
    asserted to CARRY the probe's own text: the redaction that removes a
    credential from it happens at the call site, and a message emptied here
    would leave nothing for that redaction to be observed on."""


def test_a_probe_calling_sys_exit_is_contained_too():
    """`SystemExit` is a `BaseException`; `except Exception` would let it end
    the command with no diagnostic at all."""


def test_a_keyboard_interrupt_is_re_raised_fresh_and_argument_less():
    """Ctrl-C still stops the command, and a `KeyboardInterrupt("secret")` a
    probe body constructed does not reach Python's printer with its message.
    Assert BOTH: that `KeyboardInterrupt` propagates, and that `str(exc) == ""`."""
```

- [ ] **Step 3: run.** `uv run pytest` → **previous + 3 passed**.

- [ ] **Step 4: two mutations.** (a) Change `except BaseException` to `except Exception`:
      `test_a_probe_calling_sys_exit_is_contained_too` must FAIL, because `SystemExit` propagates
      instead of becoming a `ContractError` — two different exception types out of one call. (b)
      Change `raise KeyboardInterrupt from None` to a bare `raise`:
      `test_a_keyboard_interrupt_is_re_raised_fresh_and_argument_less` must FAIL on `str(exc) == ""`,
      because the original object carries its constructed message. Revert each by editing back.

- [ ] **Step 5: commit.** `git add -A && git commit -m "H7d Part A task 4: probe invocation and the
      contained raise"`.

---

## Task 5: the `apparatus_facts` projection, and the return-shape refusal

**Runs after task 4. Surface: direct call.** Gives `apparatus_facts` its **first reader**.

**Files:**
- `src/publishable/apparatus.py`
- Test: `tests/test_apparatus.py`

**Decision 4's four states, and only one of them is an error:**

| What happened | The record | Error? |
|---|---|---|
| Declared key, value returned | the value | no |
| Declared key, `null` returned | `null`, and the fact's `unobserved` counter advances (task 7) | no |
| Declared key **absent** from what the probe returned | nothing; the command refuses | **`E-APPARATUS-FACT-MISSING`** |
| **Undeclared** key the probe returned | the value, and **no `unobserved` entry** | no |

**This is `data.units.attributes`' projection rule with one deliberate difference, stated so nobody
"fixes" it: a resolver's undeclared attribute is DROPPED, a probe's undeclared fact is KEPT.** The
reason is § The apparatus core can only observe's *"Every fact a probe returns is recorded and gated
on these terms, named in `apparatus_facts` or not"* — a probe would not return a fact if it did not
describe the apparatus — and the reason a roster drops one is that a unit table's columns are the
config's declared shape.

**`E-APPARATUS-RETURN` is minted here, and the design does not name it** (§ Corrections, correction
4). A probe returning something that is not an `Apparatus`, or an `Apparatus` whose `facts` is not a
mapping, or a `facts` mapping with a non-`str` key, reaches `run` today as an `AttributeError` or a
`TypeError` — measured: `coercion.coerce_scalars` iterates `values.items()` and never checks a key's
type. `units._from_resolver`'s `E-RESOLVER-YIELD` is the precedent, one module over, for the
identical fault at the identical boundary.

**`E-APPARATUS-FACT-TYPE` is a catch-and-re-code, not a new parameter on a shared helper.**
`coercion._refuse` hardcodes `E-STEP-RETURN-TYPE` and `coerce_scalars` takes no `code`; adding one
would touch every existing caller's pinned identifier. So `check_facts` calls
`coerce_scalars(facts, f"probe `{name}`")` — **with no `scope`**, so an `Estimate` falls straight
through to the same refusal any other structural value gets — and re-codes the `ContractError` it
may raise, exactly as `units._from_resolver` re-codes `E-STEP-SWEPT-PARAM` into
`E-RESOLVER-SWEPT-PARAM`. **The refusal message names the value's TYPE and never the value**, which
`coercion._refuse` already does by interpolating `type(value).__name__` — copy that shape rather
than re-deriving it, because a probe returning an object whose `__repr__` carries a credential must
not have that text interpolated into a refusal.

**The code:**

```python
def check_facts(
    returned: Any, declared: Sequence[str], *, probe_name: str, credentials: Mapping[str, str]
) -> dict[str, Any]:
    """The three phase-independent checks, in the order a leak forbids reversing."""
    # 1. shape            → E-APPARATUS-RETURN
    # 2. credentials      → E-APPARATUS-FACT-CREDENTIAL      (task 6)
    # 3. scalar walk      → E-APPARATUS-FACT-TYPE
    # 4. declared keys    → E-APPARATUS-FACT-MISSING
```

**The order is part of the ruling.** The credential check runs **before** the scalar walk, so a
probe returning a credential as a plain `str` is refused before anything interpolates a value; and
the declared-key check runs **last**, so a payload carrying a credential is refused for the
credential rather than reported for a missing key. Task 6 inserts step 2 into this function.

- [ ] **Step 1: write steps 1, 3 and 4** — leave step 2 as the single-line comment above for task 6
      to fill, so the two tasks do not both edit one line.

- [ ] **Step 2: the tests**, all direct calls with a plain dict for `credentials`:

```python
def test_every_declared_fact_that_came_back_is_kept_and_a_null_is_kept_as_null():
    """The first two states in one assertion, because a test asserting only the
    value state passes identically when `null` is dropped."""


def test_a_declared_fact_the_probe_omitted_is_E_APPARATUS_FACT_MISSING():
    """The third state — the plugin and the template disagreeing about what this
    probe supplies. Assert the message names the missing KEY."""


def test_an_undeclared_fact_the_probe_returned_is_kept():
    """The fourth state, and the deliberate difference from a resolver's
    attribute projection. Paired with the assertion above that the declared ones
    survive, so it cannot pass on an implementation that keeps everything by
    doing nothing at all — assert the returned mapping's exact key set."""


def test_a_probe_returning_something_that_is_not_an_apparatus_is_E_APPARATUS_RETURN():
    """Parametrized over three shapes: a dict, an `Apparatus` whose `facts` is a
    list, and an `Apparatus` whose `facts` has a non-`str` key. Without this,
    each reaches `run` as an `AttributeError` or a `TypeError`."""


def test_a_structural_fact_value_is_E_APPARATUS_FACT_TYPE_and_the_message_names_the_type():
    """Re-coded from `coerce_scalars`, not `E-STEP-RETURN-TYPE`: a reader holding
    that identifier is sent to § Steps and artifacts, which describes a different
    fault at a different time. Assert the code AND that the offending value's own
    text is absent from the message."""
```

- [ ] **Step 3: run.** `uv run pytest` → **previous + 5 passed** (the parametrized case counts
      three; reconcile your own absolute).

- [ ] **Step 4: three mutations.** (a) Delete the declared-key loop: the
      `E-APPARATUS-FACT-MISSING` test must FAIL, because the fixture omits a declared key and the
      two branches return a mapping versus raise. (b) Project onto the declared list — the
      resolver's rule — instead of keeping undeclared facts: the undeclared-fact test must FAIL on
      the exact key set. (c) Re-raise `coerce_scalars`' `ContractError` unchanged instead of
      re-coding it: the type test must FAIL on the code, since the two branches carry different
      identifiers. Revert each by editing back.

- [ ] **Step 5: commit.** `git add -A && git commit -m "H7d Part A task 5: the apparatus_facts
      projection, and its first reader"`.

---

## Task 6: the credential check on returned fact values — a refusal, not a redaction

**Runs after task 5. Surface: direct call** (its end-to-end pin is Fixture K, in task 9).

**Files:**
- `src/publishable/apparatus.py`
- Test: `tests/test_apparatus.py`

**Ruling (Decision 6, first half): a fact value equal to a credential value core read for a
DECLARED variable fails the command under `E-APPARATUS-FACT-CREDENTIAL`. It is not redacted, not
warned about, and not recorded.** § The apparatus core can only observe makes non-secret,
non-identifying facts *"a rule rather than a convention"*, and the property it buys is that
`provenance.apparatus` is publishable as-is and `study add` *"has nothing to redact from it."* A
redaction would leave `<redacted:INSTRUMENT_API_TOKEN>` sitting in a block whose whole contract is
that it needs none — and it would be **recorded**, so the block would carry evidence of a credential
having been there.

**The match is by exact value, never by pattern**, on H7c's decision 4: core knows what it read out
of the environment, and a pattern check fails open on a credential named `instrument_pw` and fails
closed on a config value that happens to look random. **The values checked are exactly
`credential_values(declared_credential_names(doc, template, conditions))`** — the same set `redact`
answers from and the same set `validate` checks for presence. A value a probe read for a name
nothing declared is outside what core saw and is not matched, identically to § Secrets &
credentials' existing statement of that limit.

- [ ] **Step 1: fill step 2 of `check_facts`.** Compare each returned value against each credential
      value by equality, and refuse naming **the fact's key and the variable's NAME** — never the
      value, and never the variable's value.

- [ ] **Step 2: the tests.**

```python
def test_a_fact_equal_to_a_declared_credential_value_is_refused():
    """The value is `lab7`: short, lowercase, ordinary-looking, a whole word.
    That is the point — a random-looking value makes an exact-value check and a
    heuristic AGREE, so the mutation below would have two branches that cannot
    differ."""


def test_the_refusal_names_the_variable_and_never_the_value():
    """A refusal that quoted the value would be the leak the check exists to
    prevent. Assert `lab7` is absent from the message and the variable's name is
    present."""


def test_a_value_core_never_read_is_not_matched():
    """The documented limit: a probe reading `os.environ` for a name nothing
    declared is outside what core saw. The control that keeps the check from
    being a string-similarity heuristic in disguise."""
```

- [ ] **Step 3: run.** `uv run pytest` → **previous + 3 passed**.

- [ ] **Step 4: the mutation, and its branches genuinely differ.** Replace the equality test with a
      heuristic — `len(value) >= 20 or any(c.isdigit() for c in value) and value.isalnum()`, or any
      entropy rule you like. `test_a_fact_equal_to_a_declared_credential_value_is_refused` must
      FAIL, because `lab7` is four characters of ordinary lowercase-plus-digit text that no
      heuristic flags while equality does. **This is why the fixture value is what it is.** Revert
      by editing back.

- [ ] **Step 5: commit.** `git add -A && git commit -m "H7d Part A task 6: a returned credential
      fails the command rather than being redacted into the record"`.

---

## Task 7: null semantics, the `unobserved` counts, and `W-APPARATUS-UNANSWERED`

**Runs after task 4. Surface: direct call** (its end-to-end pin is Fixture N, in task 11).

**Files:**
- `src/publishable/apparatus.py`
- Test: `tests/test_apparatus.py`

**The code — an accumulator, because the record is a function of every observation:**

```python
class Observations:
    """Every observation this run made, and the two documents derived from them."""

    def record(self, condition_key: str, facts: Mapping[str, Any]) -> None: ...
    def facts_document(self) -> dict[str, dict[str, Any]]: ...
    def unobserved(self, declared: Sequence[str]) -> dict[str, dict[str, int]]: ...
    def warn_unanswered(self, c: Collector) -> None: ...
```

**`facts_document` is the FIRST ANSWERED observation of each fact, per condition** — § The
apparatus files states exactly that, *"per fact rather than per probe, since a probe that answered
three of four facts pinned three of them"* — and *"a fact still unanswered when the run ends stays
`null` there."* So a fact whose first observation was `null` and whose second answered records the
**answer**; a fact that never answered records `null`.

**`unobserved` is keyed by DECLARED facts only** (Decision 4's fourth row: *"What the declaration
adds is a warning… and an `unobserved` count in the record"*), and its counts are over the run's
probes: `{fact: {"null_probes": n, "total_probes": m}}`, with `total_probes` the number of
observations this run made **in total**, matching § The apparatus core can only observe's own
example, where `reagent_lot` carries `{null_probes: 3, total_probes: 15}`. A run whose template
declares no `apparatus_facts` records `unobserved: {}` while still recording every fact the probe
returned.

**The accumulator keeps per-(condition, fact) null counts, which is strictly more than either
document mapping holds, and that is the ruling this task turns on.** § The apparatus core can only
observe says the declaration buys *"a warning… when the fact comes back `null`"* — **when it comes
back `null` on a call**, which includes the flaky case that section describes in as many words: a
deployment answering a fingerprint on most calls and omitting it on some. Neither published mapping
can answer that at the warning's grain: `facts` records the **answer** for a partially answered
fact and so shows no `null` at all, and `unobserved` aggregates over conditions and so carries no
condition to name (§ Corrections, correction 3). So `Observations` counts per (condition, fact) and
**both** published mappings are derived from those counts — `facts_document` from the observations,
`unobserved` by summing the per-condition counts. One accumulator, two projections, no second
source of truth.

**`W-APPARATUS-UNANSWERED` fires once per (condition, fact) with at least one `null` observation, at
run end** — never per call. Under Decision 3 an N-execution run makes many calls per condition, so a
per-call emission would print one line many times over and train a reader to ignore it. The message
names the condition, the fact, and that pair's null count out of its total. **A warning never
changes an exit code**, on `W-ENV-UNLOCKED`'s existing precedent. **The call site is task 11's** —
this task's pin is direct-call only, and no terminal output exists yet when it lands.

- [ ] **Step 1: write the class**, and make `warn_unanswered` take a `Collector` so it composes with
      the one `command_run` already prints from.

- [ ] **Step 2: the tests**, direct calls over hand-built observations:

```python
def test_the_first_answered_observation_wins_and_a_never_answered_fact_stays_null():
    """Three observations of one fact — null, then a value, then a different
    value — and the recorded entry is the SECOND. A fixture with two
    observations could not tell "first answered" from "last seen"."""


def test_a_partially_answered_fact_records_its_answer_and_still_counts_its_nulls():
    """The flaky case the null rule exists for, and the one `facts` alone cannot
    see: the recorded entry holds the value AND the pair's null count is 2. A
    build that derived the counts from `facts` would report 0."""


def test_unobserved_counts_declared_facts_only_and_counts_every_probe():
    """The undeclared fact must have NO entry, asserted beside the declared
    ones' presence: an absence assertion alone passes if nothing was recorded.
    `unobserved` is the per-condition counts summed, asserted against a
    hand-computed total over the observations this test recorded."""


def test_the_warning_is_one_finding_per_condition_and_fact_including_the_flaky_pair():
    """Two conditions × three declared facts over six observations, arranged as
    Fixture N: one never-answered pair, two partially answered pairs, and three
    pairs with no null at all. Exactly THREE findings, asserted as a count and as
    the exact set of (condition, fact) pairs — per-call emission would produce
    eight, and a warning derived from `facts` alone would produce one."""
```

- [ ] **Step 3: run.** `uv run pytest` → **previous + 3 passed**.

- [ ] **Step 4: three mutations.** (a) Make `facts_document` keep the **last** observation rather
      than the first answered: the first test must FAIL, because its third observation differs from
      its second. (b) Derive the warning from `facts_document()` — a `null` entry — rather than from
      the per-(condition, fact) counts: the warning test must FAIL on the count, **one finding
      against three**, because both flaky pairs record their answer and so show no `null`. (c) Emit
      the warning once per recorded observation: the same test must FAIL the other way, eight
      findings against three. Revert each by editing back.

- [ ] **Step 5: commit.** `git add -A && git commit -m "H7d Part A task 7: null semantics, the
      unobserved counts, and the unanswered warning"`.

---

## Task 8: `apparatus/probes.jsonl`

**Runs after task 4, before 9 and 10. Surface: direct call** (its placement pins are tasks 9 and 10).

**Files:**
- `src/publishable/apparatus.py`
- `docs/reference.md` — § Artifact layout's run tree
- Test: `tests/test_apparatus.py`

**The line's keys are exactly § The apparatus files' five** — `at`, `phase`, `condition`, `probe`,
`facts` — nulls included, undeclared facts included, one line per probe call, appended **at the
call**. `at` is UTC in the `%Y-%m-%dT%H:%M:%SZ` spelling `executions.jsonl` already writes. `phase`
is a closed vocabulary of four — `run_start`, `pre_execution`, `dry_run`, `freeze` — of which Part A
emits the first two; naming all four here keeps H8's and H9's callers from minting a fifth spelling.

**`condition` is the condition's `<nn>_<label>` key, not its bare label** (§ Corrections, correction
2): § The apparatus files' own example writes `"condition": "00_baseline"` and § The apparatus core
can only observe keys `facts` the same way, and `sweep.condition_dir_name(index, label)` is the one
function in core that renders that string. **Import it rather than formatting the string a second
time.** A condition with **no** label — a run declaring no `sweep`, which is the worked example and
most of this suite — has no `conditions/` level at all, so its key is `f"{index:02d}"`, the same
scheme with an empty body. **Write `apparatus.condition_key(index, label)` as the one place that
decides this**, and let the ledger, `facts` and every warning read from it.

**One inconsistency, named rather than smoothed:** `executions.jsonl` writes `condition` as an
**index**; this ledger writes the `<nn>_<label>` key. Both are the record their own document
specifies, and the key is what `facts` is keyed by, so a reader joining the two files joins on
`sweep.yaml`'s index↔label mapping. **Do not "harmonize" one to the other** — it would break the
join with `facts`.

**Append-only, in the sense `executions.jsonl` is**: Part A never removes or rewrites a line.

- [ ] **Step 1: write `append_observation(run_dir, *, phase, condition, probe, facts)`** and
      `condition_key(index, label)`. The ledger is `run_dir / "apparatus" / "probes.jsonl"`, and its
      directory is created with `mkdir(parents=True, exist_ok=True)` at the append.

- [ ] **Step 2: § Artifact layout's tree.** Add an `apparatus/probes.jsonl` entry with a short
      comment naming what it holds. **Locate it by naming what a sibling row does** — the
      `executions.jsonl` row, *"one record per finished execution"* — never by position, and check
      every row the insertion **moved** and every count phrase near it.

- [ ] **Step 3: the tests.**

```python
def test_a_ledger_line_carries_exactly_the_five_documented_keys():
    """Asserted as an exact key SET, in the shape `json.loads` gives back: a
    sixth key nobody documented is what this catches."""


def test_a_null_fact_and_an_undeclared_fact_both_reach_the_ledger():
    """The ledger is every observation, nulls included — which is what makes a
    fact that only started answering halfway through visible as exactly that."""


def test_a_second_append_adds_a_line_and_rewrites_nothing():
    """Append-only, asserted on the file's RAW text: both lines present, the
    first byte-identical to what the first call wrote."""


def test_the_condition_key_is_the_nn_label_form_and_a_labelless_condition_is_nn():
    """`condition_dir_name`'s own spelling, imported rather than re-formatted, and
    the no-sweep case that `reference.md`'s example never shows."""
```

- [ ] **Step 4: run.** `uv run pytest` → **previous + 4 passed**.

- [ ] **Step 5: the mutation.** Open the ledger with `"w"` instead of `"a"`.
      `test_a_second_append_adds_a_line_and_rewrites_nothing` must FAIL — one line on disk against
      two. **Why the branches differ:** the fixture appends twice with different `facts`. Revert;
      confirm green.

- [ ] **Step 6: commit.** `git add -A && git commit -m "H7d Part A task 8: the append-only probe
      ledger"`.

---

## Task 9: the probe at run start, once per resolved condition

**Runs after 5, 6, 7 and 8. Surface: `run`.** The first task in the slice at which core calls user
code.

**Files:**
- `src/publishable/apparatus.py` (the `Observer`), `src/publishable/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes, all read from `src/publishable/cli.py` at `4508ea6`: `run_template` (resolved before the
  roster call, with `repo_root` passed, so a project-local template resolves), `conditions` from
  `expand(doc)`, `cfgs` — `{c.index: resolve_condition_cfg(doc, c)}` plus `cfgs[-1]`, the wide cfg —
  `credentials` from `credential_values(declared_credential_names(doc, run_template, conditions))`,
  and `run_dir`.
- Produces: `apparatus.Observer`, constructed once by `command_run`, holding the probe's name and
  callable, the declared `apparatus_facts`, the resolved conditions, the per-condition `cfgs`, the
  `run_dir`, the `credentials` and an `Observations`. Its whole public surface is
  `observe_round(*, phase, condition_index)`, `block()` (task 11) and `warn_unanswered(c)`.

**`Observer.observe_round` is the phase-independent entry point every caller uses**, and it is what
makes Decision 14 hold: H9's `dry-run` calls it with `phase="dry_run"`, H8's `freeze` with
`phase="freeze"`, and **nothing is stubbed here for either**. Given `condition_index=None` it makes
**one call per resolved condition**, each under that condition's own cfg; given an index it makes one.

**Where it sits in `command_run`'s phases, and why not earlier:** after the run directory is
allocated and **inside its lock**, after `sweep.yaml` and `allocation.json` are written, before the
first execution. The ledger is a run artifact, so it has nowhere to go before the directory exists —
and everything before that point is free (validation, the manifest, the roster, the plan, the two
partition files), which is the same cost ordering § Exit codes and diagnostics states for `dry-run`.
**A plan author reading "fail fast" will move the probe ahead of the run directory and leave the
ledger with no home; do not.**

**Why one call per condition** (Decision 2): a probe *may* read a swept parameter *and usually must*,
so it gets `cfgs[c.index]` and never `cfgs[-1]`; and both the ledger's `condition` and
`facts`'s keying are per condition, from two independent document sites.

**The failure path, and it is ONE mechanism:**

```python
try:
    observer.observe_round(phase="run_start", condition_index=None)   # this task
    results = execute_plan(..., observer=observer)                    # task 10 threads it
except ContractError as exc:
    if exc.code not in apparatus.APPARATUS_CODES:
        raise
    probe_c = Collector()
    probe_c.credentials = credentials
    probe_c.error(exc.code, "experiment_type", str(exc))
    print(probe_c.render(), file=sys.stderr)
    return EXIT_WRONG
```

- **A FRESH `Collector`**, because `c` has already been rendered and printed — appending to it would
  re-print every earlier finding and inflate the counts line. This is the roster path's own shape.
- **`credentials` reused, never recomputed**: a second derivation is a second answer.
- **The code filter is deliberate, narrow, and every member of it is pinned by a test in this
  plan.** `apparatus.APPARATUS_CODES` is **the five `E-APPARATUS-*` codes and nothing else** —
  `E-APPARATUS-RAISED`, `-RETURN`, `-FACT-TYPE`, `-FACT-MISSING`, `-FACT-CREDENTIAL`. The three
  dispatch codes are deliberately **outside** it: `command_run` calls `validate_config` first and
  returns `EXIT_WRONG` on any error, and `_check_probe` answers `E-PROBE-UNKNOWN` from the same
  metadata scan `_probe_for` reads — so a dispatch failure at the run-start round requires the
  installed set to change between `validate` and the lock, which **no fixture in this plan reaches
  and none easily can**. Including an unreachable member would ship exactly the shipped-but-unread
  shape task 17 files against others. Left outside, a dispatch failure escapes to `main` and is
  reported there as a coded refusal, the same way a plan/cfg disagreement already is. Every other
  `ContractError` out of `execute_plan` (`E-RUN-CFG-MISSING`, `E-RUN-SEED-MISSING`) also keeps
  escaping exactly as it does today; this slice does not change how core's own inconsistencies are
  reported.
- **What the run directory holds afterwards:** `sweep.yaml`, `allocation.json` where one was
  written, whatever `apparatus/probes.jsonl` had accumulated, and **no `run.yaml`** — the same shape
  a failure before `run.yaml` already produces. **Write that as what happens, and do not write that
  a probe cannot stop a run mid-plan** — Part B owns `status: partial` and exit `5`.

- [ ] **Step 1: write the `Observer`**, then construct it in `command_run` inside the lock at the
      point named above. It is `None` when the resolved template declares no `apparatus_probe`, and
      every call site is guarded on that — the ordinary case, and the case task 18 pins.

- [ ] **Step 2: the tests**, on Fixture P's three parts:

```python
def test_a_declared_probe_is_called_once_per_condition_at_run_start(installed, registries, tmp_path, capsys):
    """The end of the false `apparatus: null`. Two conditions, and the ledger's
    `run_start` lines are asserted as the exact list of condition keys read back
    from `sweep.yaml` — not a count, which cannot tell two calls for one
    condition from one call for each."""


def test_a_probe_reading_a_swept_parameter_gets_ITS_condition_s_value(installed, registries, tmp_path, capsys):
    """Fixture S. The two conditions' recorded facts must DIFFER and each equal
    its own swept value. NOT an assertion that `E-STEP-SWEPT-PARAM` was not
    raised: no marker is present under this design, so that assertion is true of
    a build that hands the probe nothing at all."""


def test_a_probe_returning_a_declared_credential_fails_the_command_and_writes_no_run_yaml(
    installed, registries, tmp_path, capsys
):
    """Fixture K, end to end: exit non-zero, `E-APPARATUS-FACT-CREDENTIAL` in the
    captured output, no `run.yaml`, and `lab7` in no byte of any file under the
    results directory — asserted on RAW text over a file list proven non-empty
    first, on `_files_under`'s shape."""


def test_a_probe_that_raises_is_a_redacted_diagnostic_at_run(installed, registries, tmp_path, capsys):
    """Fixture K2, and the pin for the containment mechanism as a whole: exit
    non-zero, `E-APPARATUS-RAISED` present, `<redacted:PUBLISHABLE_TEST_TOKEN>`
    present, and `lab7` absent from stdout, from stderr and from every file under
    the results directory."""
```

- [ ] **Step 3: run.** `uv run pytest` → **previous + 4 passed**.

- [ ] **Step 4: three mutations.** (a) Hand every call `cfgs[0]` instead of the condition's cfg:
      Fixture S's test must FAIL, because the two conditions' facts become equal and the fixture's
      swept values differ. **Handing `cfgs[-1]` instead would crash, so that is not the mutation.**
      (b) Delete `probe_c.credentials = credentials`: the K2 test must FAIL on `lab7`'s absence,
      because the escape route — `main`'s `PublishableError` handler — prints `{exc}` with **no**
      collector, which this plan measured at `4508ea6`. **This is why there is exactly one redacting
      mechanism: with two, neither mutation could be seen.** (c) Probe once for the run instead of
      once per condition: the run-start test must FAIL on the condition-key list. Revert each by
      editing back.

- [ ] **Step 5: commit.** `git add -A && git commit -m "H7d Part A task 9: the run-start round, and
      a probe failure as a redacted diagnostic"`.

---

## Task 10: the probe before every execution

**Runs after task 9. Surface: `run`.**

**Files:**
- `src/publishable/runner.py`, `src/publishable/cli.py`
- Test: `tests/test_cli.py`, `tests/test_runner.py`

**Ruling (Decision 3): a probe runs before EVERY execution, with no narrowing.** An execution
belonging to a condition is probed once, under that condition's cfg. An execution belonging to **no**
condition — `run` or `summary` scope — is probed **once per resolved condition**, under each
condition's own cfg. `reference.md`'s *"before every execution"* stands **unamended**, and it is
stated at two sites, the second argument-bearing: § One execution at a time gives it as one of the
four guarantees that make serial execution non-optional.

**Both rejected readings, with their reasons, because both are cheaper:** handing a condition-less
execution the wide cfg breaks the documented normal case (a probe reading a swept parameter meets
`E-STEP-SWEPT-PARAM` at every `run`- and `summary`-scoped execution, and nearly every design has a
`summary` step); skipping it leaves the execution furthest in time from any observation as the only
uncertified one.

**The code, and `execute_plan` derives nothing:**

```python
# runner.execute_plan gains one defaulted keyword:
observer: "Observer | None" = None
# and, inside the loop, before the step is constructed and before anything is executed:
if observer is not None:
    observer.observe_round(phase="pre_execution", condition_index=execution.condition_index)
```

**The condition list lives on the `Observer`, not on the plan.** `execute_plan`'s own
`conditions_list` is built from the executions it sees, so for a pipeline of `run`- and
`summary`-scoped steps alone it is **empty** — a plan-derived list would silently probe nothing for
exactly the executions Decision 3 exists to cover. The `Observer` holds the resolved conditions
`command_run` expanded, the same single-authority rule `holdout_plan` and `group_axes` already
follow.

**Appended BEFORE the execution, not after**, which is what makes *"the ledger keeps both
observations so the evaluable earlier period is still reportable"* true of a run that dies inside an
execution: the observation the run executed **under** is on disk regardless of how the execution
ended.

- [ ] **Step 1: thread `observer` through `execute_plan`** and add the call. `credentials` is already
      a parameter of that function and is **not** re-derived.

- [ ] **Step 2: the before-placement pin, and it is arithmetic rather than a crash.** The design's
      prescribed mutation-catcher for this — a step that raises, leaving the ledger short by one line
      — **cannot work**, because a failed execution never stops the run and the ledger line would be
      appended either way (§ Corrections, correction 5). The pin that does work: a `run`-scoped step
      that **counts the ledger's lines while it is executing** and writes the count as an artifact.
      Under Fixture F, that step is the first execution in the plan (measured at `4508ea6`), so
      before it runs the ledger holds the two `run_start` lines plus its own round's two lines:

```python
_LEDGER_COUNTING_RUN_STEP = '''\
from pathlib import Path

from publishable import BaseStep


class Step(BaseStep):
    scope = "run"

    def run(self, cfg, io):
        ledger = Path(io.run_dir) / "apparatus" / "probes.jsonl"
        seen = len(ledger.read_text().splitlines()) if ledger.exists() else 0
        io.write("seen.json", {{"lines": seen}})
        return {{}}
'''
```

      **Expected: 4** — two `run_start` lines (one per condition) plus the two lines of this
      execution's own condition-less round. Under an after-the-execution append it is **2**. The
      test reads `<run_dir>/shared/<step>/seen.json`. `io.run_dir` is core's own attribute rather
      than a documented step surface; it is used here because this is a fixture, and the test asserts
      nothing about the public surface.

- [ ] **Step 3: the tests.**

```python
def test_the_ledger_line_precedes_the_execution_it_covers(installed, registries, tmp_path, capsys):
    """`seen.json` holds 4: the two run-start lines and this execution's own
    round, both written before the step ran. An after-the-execution append gives
    2 — a different number, not a crash."""


def test_a_condition_less_execution_is_probed_once_per_condition(installed, registries, tmp_path, capsys):
    """The `pre_execution` lines for the `run`-scoped step carry BOTH condition
    keys, and both keys are present in `provenance.apparatus.facts`. The wide-cfg
    reading would produce one line whose condition is absent from `facts`."""
```

- [ ] **Step 4: run.** `uv run pytest` → **previous + 2 passed**.

- [ ] **Step 5: two mutations.** (a) Guard the call with
      `if execution.condition_index is not None`: the condition-less test must FAIL, because two
      `pre_execution` lines disappear and the asserted key list changes. (b) Move the
      `observe_round` call to after the `ExecutionResult` is appended: the ordering test must FAIL
      on `4` against `2`. Revert each by editing back.

- [ ] **Step 6: commit.** `git add -A && git commit -m "H7d Part A task 10: a probe before every
      execution, condition-less ones included"`.

---

## Task 15: the call-count contract

**Runs immediately after task 10, in the same batch. Surface: `run`.** H9's `dry-run` must be able
to state the number before a run is scheduled, so it is a contract rather than an incidental count:
**`C + E_c + C × E_none`**.

**Files:**
- Test: `tests/test_cli.py`

**Fixture F, derived in § The discriminating fixtures and repeated here because an implementer sees
only this task:** `sweep.grid` over one axis with two levels (**C = 2**), one repeat, the scaffolded
`repeat`-scoped step (**E_c = 2**), one extra `run`-scoped step (**E_none = 1**) — so
`2 + 2 + 2 × 1` = **6 ledger lines**, and the expected ordered `(phase, condition)` list is the one
tabulated there. **The `run`-scoped execution runs first**, measured at `4508ea6` by a real run of
exactly this shape.

**The assertion is the ordered pair list, not the count**, because two of the six candidate readings
land on 5 and would be indistinguishable from each other by count alone.

- [ ] **Step 1: write the test.** Build the condition keys from `sweep.yaml`'s own `conditions`
      entries — `f"{c['index']:02d}_{c['label']}"` — so no label is typed twice, and assert the
      ledger's `[(line["phase"], line["condition"]) for line in lines]` equals the expected list.

- [ ] **Step 2: the docstring states the five rejected readings and their line counts**, so a reader
      who changes the placement sees what each alternative would have produced. It must **not** claim
      the fixture rules out a reading it cannot — with two conditions, "once per run at run start"
      and "one wide-cfg call" both give five lines, and it is the pair list that separates them.

- [ ] **Step 3: run.** `uv run pytest` → **previous + 1 passed**.

- [ ] **Step 4: the mutation.** In `runner.execute_plan`, probe only on the first execution
      (`if observer is not None and not results:`). The test must FAIL: three lines against six, and
      a different pair list. Revert by editing back.

- [ ] **Step 5: commit.** `git add -A && git commit -m "H7d Part A task 15: the call-count contract,
      pinned against every candidate reading"`.

---

## Task 11: `provenance.apparatus`'s five sub-keys

**Runs after 9, 10 and 15. Surface: `run`. Closes the OPEN filing** *a run whose template declares
an installed probe records a false `apparatus: null`* (struck in task 17).

**Files:**
- `src/publishable/apparatus.py` (`Observer.block()`), `src/publishable/cli.py`
- `docs/reference.md` — nothing: § The apparatus core can only observe already carries the fenced
  `provenance.apparatus` block, and this task's job is to make the code match it. **Check that, and
  change nothing if it agrees.**
- Test: `tests/test_cli.py`

**The block, exactly the document's five keys:** `probe` (the registered name), `ledger`
(`"apparatus/probes.jsonl"`, the same relative-path spelling `input_manifest` uses), `hash` (task
12), `facts` (per condition, first answered), `unobserved` (per declared fact).

**The whole block stays `null` for a template declaring no probe** (Decision 7, and the document's
own words: *"An experiment whose measurements never leave the machine declares nothing and records
`apparatus: null`"*). **`probe: null` beside four other nulls is a different record** — it says a
probe was asked for and did not name itself — and writing it would reproduce the false-record defect
this slice exists to close in a new spelling. Task 18's pin is what holds that.

**Where it goes:** `cli.command_run`'s provenance document, replacing `"apparatus": None,` with
`observer.block() if observer is not None else None`. **Keep the key in its current place in that
dict** — `run.yaml`'s key order is what task 18 pins, and moving it is a change no document asks for.

- [ ] **Step 1: write `Observer.block()`**, assembling from `Observations` rather than re-deriving
      anything, and wire it in `cli.py`.

- [ ] **Step 2: `warn_unanswered`'s call site.** `run.yaml` has no diagnostics channel —
      `command_run`'s own comment says so where it prints `aggregate_c.render()` to stdout — so the
      warning is terminal output through a fresh `Collector` printed to **stdout**, on that shipped
      precedent, once at run end. A warning never changes the exit code.

- [ ] **Step 3: the tests.**

```python
def test_a_declared_probe_records_the_five_sub_keys_per_condition(installed, registries, tmp_path, capsys):
    """Fixture N end to end. Asserts the block's exact key SET, then `facts` per
    condition with the unanswered fact `None` and the answered one holding its
    value, then `unobserved` RECOMPUTED from the ledger the test just read — the
    two numbers are never hard-coded."""


def test_the_undeclared_fact_is_recorded_and_has_no_unobserved_entry(installed, registries, tmp_path, capsys):
    """Decision 4's fourth row, which no other test reaches. The presence
    assertion and the absence assertion are one pair: the absence alone would pass
    if the probe had never run."""


def test_the_unanswered_warning_fires_once_per_condition_and_fact_with_a_null(
    installed, registries, tmp_path, capsys
):
    """Fixture N: exactly THREE `W-APPARATUS-UNANSWERED` lines in stdout across
    six probe calls — the never-answered pair and the two partially answered ones
    — and none for a fact that always answered or for the undeclared fact. A
    count assertion and an exact pair set, because per-call emission would print
    eight and a warning derived from `facts` alone would print one. The exit code
    stays 0, on `W-ENV-UNLOCKED`'s precedent."""
```

- [ ] **Step 4: run.** `uv run pytest` → **previous + 3 passed**. Task 18's pin must still be green:
      it is the assertion that this task did not add a key to a no-probe run.

- [ ] **Step 5: two mutations.** (a) Write the block unconditionally, with `probe: None` when no
      probe is declared: **task 18's pin** must FAIL on `is None`. (b) Build `unobserved` from every
      returned fact rather than the declared ones: the undeclared-fact test must FAIL, because the
      fixture's undeclared fact gains an entry the assertion says is absent. Revert each by editing
      back.

- [ ] **Step 6: commit.** `git add -A && git commit -m "H7d Part A task 11: provenance.apparatus
      stops being a false null"`.

---

## Task 12: `provenance.apparatus.hash`

**Runs after 11. Surface: `run`.**

**Files:**
- `src/publishable/apparatus.py`
- Test: `tests/test_cli.py` or `tests/test_apparatus.py` — the construction test is a direct call,
  the two-runs test is a `run`
- `docs/reference.md` — nothing: § The apparatus core can only observe already states *"over the
  resolved condition → facts mapping"*. **Check and change nothing if it agrees.**

**Ruling (Decision 10): sha256 over canonical JSON (`sort_keys=True`, `separators=(",", ":")`,
`ensure_ascii=False`) of `provenance.apparatus.facts` exactly, `sha256:`-prefixed, computed by a
function in `apparatus.py` beside the builder of that mapping.**

**This is NOT a fourth hash**, and two mechanical consequences are part of the ruling: **`HASHED_TREES`
is not touched**, and the function does **not** go in `hashes.py`. It goes in `apparatus.py` on
`manifest_hash`'s and `allocation_hash`'s shipped placement — measured at `4508ea6`: `manifest_hash`
lives in `manifest.py` beside `build_manifest`, `allocation_hash` in `artifacts.py` beside
`build_allocation_document`, and `allocation_hash`'s own docstring argues that `hashes.py` holds
hashes over things the caller already had lying around. § The apparatus core can only observe says
the same in its own words: the apparatus fingerprint *"sits beside `uv_lock_hash`… rather than one of
the three identity claims."*

**Carry `allocation_hash`'s document-versus-file-bytes warning in kind:** the hash is over the
**mapping**, not over any file's bytes. `run.yaml` renders the same mapping through `yaml.safe_dump`
and the ledger renders individual observations through `json.dumps`; neither encoding hashes to this
digest, and a reader reproducing it must re-canonicalize the parsed `facts` mapping.

**What it does not cover:** the ledger, the probe name, the phase, the timestamps and `unobserved`.
It covers the facts and only the facts, because the question it answers is *did two runs measure
through the same apparatus* — a run that probed more times is not a different apparatus.

- [ ] **Step 1: write `apparatus_hash(facts_document) -> str`** returning the `sha256:`-prefixed
      digest, with the docstring carrying both the placement argument and the encoding warning.

- [ ] **Step 2: the tests — Fixture H, and never a digest literal.**

```python
def test_the_apparatus_hash_is_recomputable_from_the_recorded_facts(installed, registries, tmp_path, capsys):
    """Recomputed by the test from the `facts` mapping it read out of `run.yaml`,
    with `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=False)`.
    A digest literal would pass under an encoder that changed and hide it."""


def test_two_runs_with_identical_facts_share_a_hash_and_one_changed_fact_moves_it(
    installed, registries, tmp_path, capsys
):
    """The property a literal would have hidden: identical facts, different
    `run_id`s and different timestamps, identical hash — and a probe returning one
    different value gives a different hash. Both halves, because the first alone
    passes for a constant."""


def test_the_hash_does_not_cover_unobserved_or_the_probe_name():
    """Direct call: two facts documents that differ in nothing hash the same, and
    the argument is the facts mapping alone — the assertion is on the function's
    signature-level behaviour rather than on a comment claiming it."""
```

- [ ] **Step 3: run.** `uv run pytest` → **previous + 3 passed**.

- [ ] **Step 4: the mutation.** Hash the whole `apparatus` block — `probe`, `ledger`, `facts`,
      `unobserved` — instead of `facts` alone. The recomputation test must FAIL, because the
      test-side canonicalization is over `facts` and the two inputs differ. A second mutation worth
      running: `sort_keys=False`. It must FAIL the recomputation test whenever the fixture's fact
      insertion order differs from sorted order — **check that your fixture's does**, or the mutation
      is blind and the fixture needs a fact whose name sorts before an earlier-inserted one. Revert
      each by editing back.

- [ ] **Step 5: commit.** `git add -A && git commit -m "H7d Part A task 12: the apparatus
      fingerprint, beside its construction and not in hashes.py"`.

---

## Task 13: the publishable-as-is test

**Runs after 11 and 12. Surface: `run`.**

**Files:**
- Test: `tests/test_cli.py`

**The property, stated as § The apparatus core can only observe states it:** `provenance.apparatus`
is **publishable as-is** and [`study add`](../../reference.md) *"has nothing to redact from it."*
This task is the pin, and it is deliberately not a comment.

- [ ] **Step 1: the test**, over a Fixture P run whose template declares a credential the probe does
      **not** return and whose facts are ordinary strings:

```python
def test_the_recorded_apparatus_block_carries_no_credential_value(installed, registries, tmp_path, capsys):
    """Two assertions, and neither alone is the property. First: the run
    COMPLETES and the block is populated — a block that is `null` because nothing
    ran would pass an absence sweep trivially. Second: no declared credential
    value appears in the block's RAW YAML text, sliced out of `run.yaml` rather
    than re-serialized, because a defect in how a value is written is one a
    parsing reader undoes before the assertion.

    The credential is DECLARED and PRESENT in the environment for this run — a
    sweep for a value core never read would pass whatever the code did."""
```

- [ ] **Step 2: state what this test does NOT prove**, in its own docstring: it is the record's
      property, not the ledger's and not the terminal's. Fixture K covers a returned credential and
      Fixture K2 the raise path, both in task 9. **Do not write a docstring claiming a guarantee
      wider than the body** — a test whose name claims the guarantee shipped twice on H4c.

- [ ] **Step 3: run.** `uv run pytest` → **previous + 1 passed**.

- [ ] **Step 4: the mutation.** In `apparatus.py`, make the credential check **redact** the value
      into the block (`redact(value, credentials)`) instead of refusing. This test alone would still
      pass — its probe returns no credential — so run it **with** task 9's Fixture K test: that one
      must FAIL on the exit code and on the raw-text sweep finding `<redacted:…>` where nothing
      should exist. **Stated here because a mutation that leaves a test green is evidence about the
      test**: this task's own fixture cannot see that mutation, and saying so is the point.

- [ ] **Step 5: commit.** `git add -A && git commit -m "H7d Part A task 13: the recorded block is
      publishable as-is"`.

---

## Task 14: no `validate` path calls a probe

**Runs any time after task 3; scheduled last but one. Surface: `validate`.** Decision 13: the old
charter's task 3, **moved in from Part B**, because Part A is the slice that creates the call sites
the guard exists for.

**Files:**
- Test: `tests/test_validate.py`

**Why it belongs here rather than in Part B:** before Part A there is no call site, so the guard is a
claim about code that does not exist; after Part A there are call sites in `command_run` and in
`execute_plan`, and this guard is what keeps `validate` inside *"may read your config and your input,
and may not reach anything outside the machine."* `validate` is the command you run in a loop while
editing YAML, and an accidental probe call there is metered money per keystroke.

**The shape is the scoping's own measurement, and it has two halves:** a probe that **writes a flag
file and then raises**, so a call cannot be silent; and the assertion on **both** the flag's absence
**and** the findings list being the expected set. **A control asserting only an absence passes
identically if nothing ran** — and here "nothing ran" is exactly the failure mode, since a config
that never resolved the template would also never call a probe.

- [ ] **Step 1: the test.**

```python
def test_no_validate_path_calls_a_declared_probe(installed, registries, tmp_path):
    """The probe writes a flag file and then raises: a call core made cannot be
    silent, and a call it made and swallowed would still leave the flag. The
    findings assertion is the control that must REPORT — an exact set, because
    `validate` collects rather than aborting and a refusal elsewhere never makes a
    later check unreachable.

    Both halves are load-bearing: the flag's absence says no probe ran, and the
    findings set says `validate` got far enough to have called one."""
```

      The findings set is whatever this fixture legitimately earns — read it by running
      `validate_config` once and asserting **that** set, and state in the docstring which finding is
      the control.

- [ ] **Step 2: run.** `uv run pytest` → **previous + 1 passed**.

- [ ] **Step 3: the mutation, and it must be applied where the behaviour lives.** In
      `validate.validate_config`, add a call to `apparatus._probe_for(declared)` followed by an
      invocation, inside `_check_probe`'s success branch. The test must FAIL on the flag's existence.
      **Why the two branches differ:** the fixture's probe writes a file, so one branch leaves it on
      disk and the other does not. Revert by deleting the added lines; confirm green **and** confirm
      the flag file is absent again.

- [ ] **Step 4: commit.** `git add -A && git commit -m "H7d Part A task 14: validate calls no probe,
      pinned by a probe that cannot be silent"`.

---

## Task 16: every document row for every code this slice minted

**Runs after every code task. Surface: documents.**

**Files:**
- `docs/reference.md` — § Errors core raises, § Warnings core reports, § Errors `validate` reports,
  § Validation, and § The apparatus core can only observe / § The apparatus files where a phrase now
  under-describes what the code does

**The family has ONE code today — `E-PROBE-UNKNOWN` — and that is the documentation debt's whole
measured size** (H7d-SCOPING § 2, re-confirmed at `4508ea6`: `E-APPARATUS`, `E-PROBE-FACT` and
`W-APPARATUS` are free identifiers across `src/`, `tests/` and the four documents).

**The rows owed, five errors and one warning — the design says four errors; task 5 mints a fifth,
`E-APPARATUS-RETURN`, and this task's rows and the payoff sentence say five** (§ Corrections,
correction 4):

| Row | Section |
|---|---|
| `E-APPARATUS-RAISED` | § Errors core raises — the sibling of `E-RESOLVER-RAISED`, with the `KeyboardInterrupt` clause that row already carries |
| `E-APPARATUS-RETURN` | § Errors core raises — `E-RESOLVER-YIELD`'s sibling: a probe returning something that is not an `Apparatus`, or a `facts` that is not a mapping of `str` keys |
| `E-APPARATUS-FACT-TYPE` | § Errors core raises — and the row states why it is not `E-STEP-RETURN-TYPE`, on the precedent `E-RESOLVER-SWEPT-PARAM` already sets |
| `E-APPARATUS-FACT-MISSING` | § Errors core raises — the one of Decision 4's three states that is an error |
| `E-APPARATUS-FACT-CREDENTIAL` | § Errors core raises — a refusal rather than a redaction, and why |
| `W-APPARATUS-UNANSWERED` | **§ Warnings core reports**, which the design's own task list does not name (§ Corrections, correction 3). That table is ordered by code, so this row sorts **first**; its condition names the (condition, fact) grain and the run-end timing |
| `E-PROBE-UNKNOWN` restated as **dual-surface** | § Errors `validate` reports — the existing row gains the dispatch site. **One row per code, not per emit site**: `E-TEMPLATE-UNKNOWN` is the instance this repo already failed on, where a task scoped by one helper's call site missed the second |

- [ ] **Step 1: write the rows.** Each states its **condition**, not its wording. Check each table's
      ordering convention before inserting, and **name what a sibling row does** rather than a
      position.

- [ ] **Step 2: § Validation.** Its "Probe is installed" row is `validate`'s and is **unchanged** —
      every check this slice added needs a call, and § Validation is the table of checks that do not.
      **Read it and change nothing**, then say so in the commit message so a later reader does not
      re-open the question.

- [ ] **Step 3: the sweep, over a FILE LIST naming the four documents plus `CLAUDE.md` and the
      feasibility analysis**, never filtering a sweep's output: every one of the six new identifiers
      appears exactly where a row defines it, and no identifier that should no longer exist survives.
      Prove the sweep can fail against a string known to be present.

- [ ] **Step 4: `CLAUDE.md` § Misreadings' *unbuilt reader of a shipped surface* row.** It names
      `apparatus_facts`; task 5 gave it a reader, so the example must move to `field_convention`
      alone — which the scoping showed was already true at `0faa2e3`, before this slice. **Delete the
      stale example rather than rewriting the sentence around it.**

- [ ] **Step 5: the mechanical pass in full** on every file touched, and the cross-document pass over
      the four documents only. **The development record is exempt and must not be retro-edited.**

- [ ] **Step 6: run.** `uv run pytest` → **previous + 0 passed** (documents only; task 1's pin and
      task 18's pin both stay green).

- [ ] **Step 7: commit.** `git add -A && git commit -m "H7d Part A task 16: one row per code for the
      five refusals and the warning this slice mints"`.

---

## Task 17: the filings, in `spec-defects.md` itself

**Runs last. Surface: documents.** A separate task because **a ledger line saying "filed" is not a
filing** — a gap recorded here as "registered against \<owner\>" has already existed only in a ledger
— and because **a filing's claims about the code go stale**, so each entry is re-read against the
code this slice changed before it is struck.

**Files:**
- `docs/superpowers/spec-defects.md`

| Filing | What this task does |
|---|---|
| *a run whose template declares an installed probe records a false `apparatus: null`* — **Owner H7d** | **Strike it.** Closed by task 11. Re-verify its claims against the code as it now stands before striking — its text describes `cli.py`'s unconditional `None`, which task 11 replaced |
| *`PROBES` and `RESOLVERS` are written by their decorators and read by nothing* — `PROBES` half **Owner H7d** | **Strike the `PROBES` half.** Closed by task 3, whose `declared_names` call is the reader. The entry's own stated reason for being a filing — *"a reader for `PROBES` means executing a probe"* — is exactly what this slice ships |
| *`BaseTemplate.field_convention` is declarable and read by nothing* — **unassigned** | **Amend** to name `field_convention` alone, now that `apparatus_facts` has a reader. **Still unassigned; this slice does not adopt it** — folding it in would make Part A the owner of a gap it did not find. H7c's entry models the amendment shape |
| **`EXIT_EXTERNAL = 5` ships and is read by nothing** — **NEW, Owner Part B** | **File it here, not in a ledger line.** Measured at `0faa2e3` and `27e397e`, and re-confirmed at `4508ea6`: one definition in `diagnostics.py`, no reader anywhere in `src/` or `tests/`. It is a fourth member of the shipped-but-unread family, and it narrows Part B's exit-code task: what is owed is a **reader** and the documented precedence (5 wins over 3 and 4), not the constant |
| *two specified readers of `required_env` belong to unbuilt commands* · *`io.reuse_from` is unbuilt and unowned* | **Untouched**, named here so neither is folded in. `io.reuse_from` is what keeps six configs non-executable, and **no sentence this slice writes may imply Part A moved that** |

- [ ] **Step 1: re-read each entry against the code at this branch's HEAD** before touching it, and
      say in the commit message which claims you re-verified.

- [ ] **Step 2: strike, amend and file** as tabulated. A closed gap is **struck** in this file rather
      than deleted, which is this file's one exception to the no-retro-edit rule.

- [ ] **Step 3: the payoff sentence, written once and correctly.** Part A unblocks **zero** configs;
      **six** with no remaining core-side blocker and **three** executable, both unmoved; **the only
      direction this slice can move a config-level count is down**. It retires no refusal and mints
      five codes and one warning. **A closed filing is not an executable-run count.**

- [ ] **Step 4: run.** `uv run pytest` → **previous + 0 passed**.

- [ ] **Step 5: commit.** `git add -f docs/superpowers/spec-defects.md && git add -A && git commit -m
      "H7d Part A task 17: two filings struck, one amended, EXIT_EXTERNAL filed against Part B"`.

---

## Corrections against the code

**Written 2026-08-19 against `main` at `4508ea6`**, correcting the design
(`docs/superpowers/specs/2026-08-19-apparatus-part-a-design.md`) and, where noted, `CLAUDE.md`. Per
`CLAUDE.md`, **the spec's body is not retro-edited** — this section is appended and says what it
replaces. Every claim below was produced by running something or by reading the named source at
`4508ea6`; none is carried from a scoping.

**1. `scripts/task-brief` does not exist in this repository.** `CLAUDE.md` § The development record
says task briefs are *"extracted from the plan by `scripts/task-brief`"*. Measured: there is no
`scripts/` directory at HEAD, and `git log --oneline --all -- scripts` returns **nothing** — the
directory has never been committed. The heading shape this plan uses (`## Task N:`) was verified with
a throwaway extractor written under the scratchpad, matching `2026-08-18-null-test.md`'s exact
heading form. **Nothing in this plan depends on that script existing**, and the CLAUDE.md sentence is
outside this slice's surface; it is recorded here rather than fixed, because a plan is not the place
to change `CLAUDE.md`.

**2. The ledger's `condition` and `facts`'s keys are the `<nn>_<label>` form, not the bare label.**
Decision 9 says *"`condition` is the condition **label**"*. Measured: a `sweep.grid` over
`analysis.method` resolves labels `method=pearson` and `method=spearman` — **no index prefix** — while
§ The apparatus files' own ledger example writes `"condition": "00_baseline"` and § The apparatus core
can only observe keys `facts` by `00_baseline`. `sweep.condition_dir_name(index, label)` is the one
function in core that renders `<nn>_<label>`. So the design's word is one level off its own document's
example, and this plan rules the **key**, imported from `sweep` rather than formatted twice (task 8).
**A second gap neither the design nor `reference.md` answers:** a run declaring no `sweep` has one
condition whose label is `None` (measured in a real run's `sweep.yaml` and `run.yaml`). Ruled
`f"{index:02d}"` — the same scheme with an empty body — on the ground that Decision 10's canonical
JSON cannot hold a `None` key beside `str` keys under `sort_keys=True`, so `null` as a key would break
the hash rather than merely read oddly.

**3. Neither published mapping can supply `W-APPARATUS-UNANSWERED` at the grain Decision 8 states.**
Decision 8 rules *"one finding per (condition, fact), emitted once at run end from
`provenance.apparatus.unobserved`."* Measured against the document: § The apparatus core can only
observe's own example makes `unobserved` **per fact, aggregated over the run's probes**
(`reagent_lot: {null_probes: 3, total_probes: 15}`), so it carries no condition to name; and § The
apparatus files makes `facts` the **first answered** observation, so a fact answered on some calls
and omitted on others records its **answer** and shows no `null` at all. The second half is the case
the whole null rule exists for — that same section describes *"a hosted deployment [that] returns a
revision fingerprint on most calls and omits it on some"* — and a warning read off `facts` is silent
for exactly it. So this plan keeps Decision 8's grain and changes what it is computed from: task 7's
accumulator keeps **per-(condition, fact) null counts**, both published mappings are projections of
those counts, and the warning reads the counts. Fixture N gains a third fact, `flaky_pin`, which is
the only shape in either document's or the design's fixtures that separates the two readings — one
finding against three. **And § Warnings core reports appears in neither the design's task 16 nor its
consistency sweep**, so that table's row is added explicitly in task 16; it is ordered by code, so
the new row sorts first.

**4. A probe returning something that is not an `Apparatus` has no refusal in the design.** The design
enumerates four minted codes. Measured: `coercion.coerce_scalars` iterates `values.items()` and never
checks that a key is a `str`, and nothing anywhere checks the returned object's type — so a probe
returning a `dict`, or an `Apparatus` whose `facts` is a list, or a `facts` with an integer key,
reaches `run` as an `AttributeError` or a `TypeError` escaping `command_run`. `units._from_resolver`
refuses the identical fault at the identical boundary as `E-RESOLVER-YIELD`. This plan mints
`E-APPARATUS-RETURN` in task 5 and **corrects the count everywhere it is stated: five codes and one
warning, not four and one.**

**5. `E-APPARATUS-FACT-TYPE` is a catch-and-re-code, because `coerce_scalars` takes no `code`.**
Measured: `coercion._refuse` hardcodes `E-STEP-RETURN-TYPE`, and `coerce_scalars(values, where, *,
scope=None)` has no code parameter. Adding one would touch every existing caller's pinned identifier,
so task 5 catches the `ContractError` and re-codes it, on `units._from_resolver`'s shipped precedent
for `E-STEP-SWEPT-PARAM` → `E-RESOLVER-SWEPT-PARAM`. Also measured and load-bearing: passing **no**
`scope` is what makes an `Estimate` in a fact value fall through to the same refusal, since
`_coerce_estimate` refuses outright when `scope is None`.

**6. The design's mutation for "append the ledger line after the execution" cannot fail.** It
prescribes *"a Fixture P variant whose step raises: the ledger is short by one line."* Measured in
`runner.execute_plan`: a step's exception is caught per execution (`except Exception: # a failed
execution never stops the run`), the result is appended and the loop continues — so an
after-the-execution append writes its line either way and the ledger is **not** short. Task 10
replaces it with an arithmetic pin: a `run`-scoped step that counts the ledger's lines while it is
executing, expected **4** under a before-append and **2** under an after-append.

**7. The design's mutation table under-counts one reading of Fixture F.** It says *"Probe once per
run instead of once per condition at run start | Fixture F: 6 lines against 8."* Under its own
fixture that mutation yields `1 + E_c + C × E_none` = 1 + 4 + 2 = **7**, which is also what its
wide-cfg reading yields — so the count alone cannot separate them. This plan asserts the **ordered
`(phase, condition)` pair list** instead (§ The discriminating fixtures, task 15), which separates
all six readings; the same collision exists in this plan's own six-line fixture and is answered the
same way.

**8. "the collector `command_run` already holds" is not a thing that exists.** Decision 6 says a
probe's raise becomes a redacted diagnostic *"through a fresh `Collector` whose `credentials` is the
mapping `command_run` **already binds** before the roster call"* — the second half is exact and
measured; the first half is what this plan implements. Measured: `command_run`'s `c` is constructed at
the top and has already been **rendered and printed** by the time phase 5 runs, which is why the
roster path builds a *fresh* collector and assigns `credentials` to it. What `command_run` holds at
`execute_plan` is the `credentials` mapping, not a live collector.

**9. Nothing in `execute_plan` can supply the condition list for a condition-less execution.**
Decision 3 puts the per-execution probe *"inside `execute_plan`'s loop… once per condition for a
condition-less one"* without saying where that list comes from. Measured: `execute_plan` builds
`conditions_list` from `plan` — `by_index` is filled only from executions whose `condition_index is
not None` — so for a pipeline of `run`- and `summary`-scoped steps alone it is **empty**, and a
plan-derived list would probe nothing for exactly the executions Decision 3 exists to cover. This
plan puts the resolved conditions and the `cfgs` on the `Observer`, which `command_run` constructs
(task 9), and `execute_plan` derives nothing.

**10. An apparatus `ContractError` has an un-redacted escape route, and it is why the wrapper is
sited where it is.** Measured in `cli.main`: `except PublishableError as exc: print(f"  error
{exc.code:<20} {exc}", file=sys.stderr)` — no collector, so no redaction. A probe raise crossing
`execute_plan`'s boundary would reach it. Task 9's wrapper around the run-start round and the
`execute_plan` call is the one containment site, filtered by `apparatus.APPARATUS_CODES` — the five
`E-APPARATUS-*` codes, every one of them pinned — so `E-RUN-CFG-MISSING`, `E-RUN-SEED-MISSING` and
the three dispatch codes keep escaping to `main` exactly as they do today. The dispatch codes are
outside the set because no fixture can reach them at that point: `validate_config` runs first and
answers `E-PROBE-UNKNOWN` from the same metadata scan, so reaching the wrapper would need the
installed set to change between `validate` and the lock. **A set member with no test is the shape
this slice is filing against others.** **One
mechanism, deliberately** — with a second redaction inside `apparatus.py`, neither site's mutation
could be seen.

**11. Decision 5's value contract is enforced at core's boundary, not in `Apparatus.__init__`.** A
refusal raised inside the probe's own body is indistinguishable from any other exception out of user
code and would be reported as `E-APPARATUS-RAISED`, a code whose row describes a different fault.
Measured precedent: `units.Unit` freezes its attributes and type-validates nothing;
`units._from_resolver` is where a yielded non-`Unit` is refused. Task 2 states this and task 2's
second test is what stops a later task from "fixing" it.

**12. § Artifact layout's run tree carries no `apparatus/` entry** at `4508ea6` — confirming the
design's task 8 note. The insertion is task 8's, located by naming what the `executions.jsonl` row
does.

**13. `EXIT_EXTERNAL = 5` re-confirmed shipped and unread at `4508ea6`**, which agrees with the
scoping's appended correction and contradicts its § 0.3. Filed in task 17 with Part B as its owner.

**14. What survives unchallenged**, stated so this section is not read as general doubt: the
`_check_probe` boundary measurement and its two-sources-of-truth finding; the three-step dispatch as
the sibling of `units._resolver_for` (all four `plugins` helpers read at `4508ea6`, all with
production callers); `coercion._SCALARS == (bool, int, float, str)` with `None` passing through;
`runner.execute_plan` already taking `credentials`; `cli.command_run` binding `credentials` **before**
the roster call; the `provenance.apparatus` fenced block's five keys; `allocation_hash`'s and
`manifest_hash`'s placement argument, quoted from the docstring that still says it; and the
zero/six/three figures.

---

## What could not be measured

1. **`scripts/task-brief`.** Correction 1. Verified with a throwaway extractor instead.
2. **Anything about `dry-run`, `freeze`, `diff`, `reproduce`, `resume`.** All five print *specified
   but not built*, so every claim in this plan about where their checks live is a **spec claim**,
   read, never a build fact. Part A ships no hook for any of them (Decision 14).
3. **The nine configs' actual plugin.** `publishable-llm`, `llm_screen` and `llm_deployment` are
   designs in the feasibility analysis, not code. Fixture P is a documented substitution — the same
   one every § Executability entry has used since 2026-08-16 — and it is a substitution, not the
   thing.
4. **A real metered probe**, deliberately. Quota constrains **placement, not testability**: core only
   ever needs a fake, and the one behaviour no fixture can stand in for — a hosted deployment that
   answers a fact on most calls and omits it on some — is exactly why `null` is a legal value and why
   an integration test against a real deployment would be a **worse** pin than the fixture.
5. **Whether the six-line Fixture F is the smallest fixture separating all six readings.** It
   separates them; no smaller one was searched for, and a smaller one would have to be checked
   against the same six.

---

## Plan self-review

- **Every task states its surface** — `validate`, `run`, direct call, or documents — because
  `validate` collects rather than aborting and a refusal never makes a later check unreachable.
- **Every prescribed mutation names the assertion that catches it and why its branches differ.** Two
  places where a mutation **cannot** discriminate are named as such rather than dressed up: task 13's
  own fixture cannot see the redact-instead-of-refuse mutation (task 9's Fixture K can), and task 12's
  `sort_keys=False` mutation is blind unless the fixture's fact insertion order differs from sorted
  order, which the task tells the implementer to check.
- **No task claims this slice unblocks a config.** Zero configs; six with no remaining core-side
  blocker; three executable; both unmoved; the only direction available is down.
- **Part B's exclusions stay excluded** — the gate, the truncation, `run_status`'s contract,
  `EXIT_EXTERNAL`'s reader, the unreachable-versus-moved distinction, the ledger-across-a-stop
  property, and the `batch`-independence test — and Decision 12's prohibition on any comment claiming
  an unreachable probe *cannot* stop a run mid-plan is in § Global Constraints, which every task
  inherits.
- **The guard pin is task 18** and it runs first, because task 11 is the task that moves what it
  covers.
