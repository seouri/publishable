# H8b — `diff` and `freeze` — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to
> implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** two commands that read what a run already wrote and say what moved. `diff` compares two
runs hash by hash and names the parameters that differ; `freeze` re-probes a run **in progress** and
reports a moved apparatus before the next block of executions is spent on it. Neither executes a
step, neither changes a run's status, and between them they write exactly one kind of byte into a
run directory: an appended line in `apparatus/probes.jsonl`. One command that already executes
changes, additively: `run` writes two more artifacts at run start, which is what makes `freeze`
possible at all.

**The payoff, stated so it cannot be rounded, and it is a table rather than a number. H8b moves NO
row of it.** The 2026-08-20 correction in [the feasibility analysis](../../feasibility-llm-growth-studies.md)
§ Executability on this build ruled that a single figure answers no consistent question for that
analysis; H8a's own entry replaced the number with a four-row table. **H8b repeats that table
unchanged — all four rows.**

| Figure | Count | Visible to `validate`? |
|---|---|---|
| Transplantable configs validating with zero errors | **8 of 8** | yes — the only figure `validate` can see |
| Blocked on `io.reuse_from` | **0** | no — the method ships; six configs still need the plugin body to call it |
| Meet the `report_by`-under-`resample` gap | **7** | no — **H4 Statistics'** gap, untouched here |
| Free of every core-side dependency this analysis can name | **1** | no — E5, and only with the plugin written and installed |

**No task may write "N configs now execute", and no task may mint a fifth number.** Nothing H8b
builds runs at `validate`, nothing it builds is called from a step, and no config in that analysis
declares an `apparatus_probe` a real plugin backs. **The only direction H8b could move a count is
down** — H7d Part B's shape, said here for the same reason. It retires no refusal. **The
`report_by`-under-`resample` gap is H4's and no task may claim or file it.**

**Architecture.** Two new modules, two new run-start artifacts, one extracted projection, one ledger
reader, one enforced vocabulary. No new dependency, no new export.

- **`diff.py`** (new) holds `command_diff`, form detection, the five rows, the three verdicts, the
  parameter delta walk, the apparatus detail lines and the upstream block. It imports
  `lineage.read_run_record`, `hashes.covered_config`/`parameters_hash`, `apparatus.apparatus_hash`.
- **`freeze.py`** (new) holds `command_freeze`, the seven refusals, the config load, template and
  probe resolution against the recorded repo root, the condition re-expansion and its cross-check,
  the credential pre-check, the probe round and the verdicts.
- **`hashes.covered_config(config)`** — the projection `parameters_hash` already computes inline,
  extracted so a row's verdict and its detail lines come from one function (Decision 3).
- **`apparatus.replay_ledger(run_dir) -> Observations`** — the ledger reader, beside the
  `append_observation` that writes the file it reads (Decision 14).
- **`apparatus.PHASES`** plus four module-level constants, and `assert phase in PHASES` as
  `append_observation`'s first statement (Decision 13).
- **`cli.command_run`** writes `<run_dir>/config.yaml` (a byte copy) and
  `<run_dir>/environment/repo_root.txt` inside the existing `RunLock` block, beside the shipped
  `environment/` captures. **Additive only** — no existing artifact changes, no verdict, status or
  exit code changes (task 3 pins that).
- **`cli._dispatch`** gains `"freeze"` in `OPERATION_COMMANDS` and a two-path arm for `diff`.
  `cli.py` keeps only the dispatch and the argument checks, exactly as it does for `validate` and
  `run` whose engines are `validate.py` and `runner.py`.

**Tech stack:** Python ≥ 3.11, `pytest`, `ruff`, `mypy`. The changes land in
`src/publishable/diff.py` (new), `src/publishable/freeze.py` (new), `src/publishable/apparatus.py`,
`src/publishable/hashes.py`, `src/publishable/cli.py`, `src/publishable/artifacts.py` (one docstring),
`docs/reference.md`, `docs/superpowers/spec-defects.md`, `docs/feasibility-llm-growth-studies.md`,
`CLAUDE.md`, and the test modules `tests/test_diff.py` (new), `tests/test_freeze.py` (new),
`tests/test_apparatus.py`, `tests/test_hashes.py`, `tests/test_cli.py`, `tests/test_acceptance.py`.

**Spec:** `docs/superpowers/specs/2026-08-20-diff-freeze-design.md` — read it beside this plan,
including its § Refusals, § The discriminating fixtures and § What did not survive H8a shipping. It
is the binding authority and this plan argues from it. **Its body must not be edited.** Where this
plan measured something that contradicts it, the disagreement is recorded in
[§ Corrections against the code](#corrections-against-the-code), appended by this plan's author and
extended by no task.

**Measurement this plan argues from:** `docs/superpowers/H8-SCOPING.md` — **whose H8b claims the
design already falsified in several places, and the design wins**; the design's own re-measurement;
and this plan's re-measurement against **`main` at `0a636af`**, this branch's point. Every
signature, record key, helper name, fixture shape and literal below was read or **run** at
`0a636af`. **Nothing is cited by line number.**

**Baseline, measured 2026-08-20 in the FOREGROUND at `0a636af`:**

- `uv run pytest -q` → **2513 passed, 1 skipped, 2 xfailed** in 137.66 s
- `uv run ruff check .` → **All checks passed!**
- `uv run ruff format --check .` → **84 files already formatted**
- `uv run mypy` → **Success: no issues found in 47 source files**

**Task count: 14.** The design's 12 in its own grain and its own numbering, plus **task 13, the guard
pin, which runs FIRST**, and **task 14, the document ruling Decision 7's artifacts owe, which runs
SECOND and before the code that writes them**. Both deviations **append** rather than renumber, on
H8a's and H7d Part B's precedent, so the design's numbering stays citable. 14 tasks make 14 commits.

---

## Sequencing

**Execution order: 13 → 14 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12.**

The task headings below are written in that order. Each task restates the constraint it depends on
in its own text, because an implementer sees only their own task.

| Constraint | Why, and where it is enforced |
|---|---|
| **Task 13 first** | Decision 7 changes the run directory, so what must be captured first is **the run directory's current contents** — plus every figure `diff` will read and every `sweep.yaml` field `freeze` will cross-check. Captured from a real `run` at `0a636af`, before task 3 adds a file. A literal recorded afterwards records the move, not the baseline. H8a's pin and both H7d parts' pins were captured this way and all three held |
| **Task 14 before task 3** | The controller's requirement: § The two files is framed as *"`config.yaml` and `run.yaml`"* and a **third** file inside the run directory named `config.yaml` bears on it. **The document says what the artifact means before the code writes it**, so no later task discovers the collision |
| **1 before 6** | A verdict is computed against a baseline, and `replay_ledger` is the baseline |
| **2 before 4** | `freeze` passes `PHASE_FREEZE`; the constant exists before its first caller |
| **3 before 4** | `freeze` has nothing to read until the artifacts exist |
| **3 alone in its batch** | It is the only task in H8b that changes behaviour a shipped test can see, so a suite-count or pin change is attributable to it and to nothing else — H8a's B4 precedent |
| **4 → 5 → 6** | The refusals gate the condition set; the condition set is what gets probed |
| **6 owns `freeze`'s CLI arm and its `Status` flip** | The built branches of `_dispatch` precede the `NOT_BUILT_COMMANDS` lookup, so an arm without the flip fails `test_reference_cli_tables_match_what_the_cli_does` — and a flip before task 6 would dispatch a command that resolves a template and never probes. **Arm, constant key and `Status` cell in one commit, at the point the command is complete** (§ Corrections, correction 1) |
| **7 before 8** | A row's verdict and its detail lines must come from one projection |
| **8 → 9, 10, 11** | All four are `diff` and share a fixture set |
| **11 owns `diff`'s CLI arm and its `Status` flip** | Same rule as task 6, at the point `diff` is complete: before task 9 it has no apparatus row, and a four-`identical` output over a pair whose apparatus moved is the single most dangerous thing this command can print (Decision 1's own cost-if-wrong) |
| **12 last** | § Errors, § Package layout, the remaining document rows and a re-measurement all run against the finished branch |

### Three deviations from the design's grain, each argued

**(a) Task 13 exists at all.** The design names no regression pin. What H8b moves is the run
directory's contents and `parameters_hash`'s internals — the same shape H8a and both H7d parts pinned
first. It is written against template `generic` and needs no plugin. **Two of its arms are authorized
to be edited, by exactly one task each, and the pin says which and to what.**

**(b) Task 14 exists at all.** The controller ruled Decision 7 approved but *explicit rather than
incidental*, and required the document change to **precede** the code. The design folds those
document rows into its task 3. Splitting them is not size, it is kind: task 14 rules what a third
`config.yaml` means to a section framed around two files, and task 3 writes bytes. Merging them gives
one report that muddles *"is the copy the right object"* with *"does § The two files still say something
true"*.

**(c) The two `Status` flips leave task 12.** Argued in the table above and in § Corrections,
correction 1. Task 12 keeps § Errors, § Package layout, the § Executability re-measurement and every
document row not owed by an earlier task.

---

## Batching — seven batches, one report and one review each

`diff` and `freeze` are two commands and they are **two seams**, not one: they share no code path,
no fixture and no failure mode, and `freeze` calls user code while `diff` reads files. Batching them
together would give one review that has to certify both a metered probe round and a text-rendering
table.

| Batch | Tasks | The seam, and what its review must be able to see |
|---|---|---|
| **B1** | **13, 14** | **The pin and the document ruling, both before anything moves.** Its review is a **capture check plus a document check**: that every pin arm was produced by **running** rather than transcribed from `cli.py` or `run_record.py`; that the two authorized-edit clauses each name exactly one task and state the post-edit list in advance; and that § The two files says what a third file named `config.yaml` inside a run directory **is** — a run-start capture, not a second editable config — rather than being left for a reader to reconcile. It must confirm no gate literal moved: still 47 source files, still 84 formatted |
| **B2** | **1, 2** | **The shared apparatus machinery, direct-call only, and nothing dispatches.** `replay_ledger` and `PHASES` are reachable from no command in this batch, which is the seam. Its review is **mutation arithmetic with no command in the picture**: M6 sited **above** the write with the ledger's content as the discriminator, M7 over all four names, and M8/M9 each producing **two different exit codes** rather than two different internal states. It must also confirm **every** core call site passes a constant — `Observer._observe_one`, `command_run`'s run-start round, and any other site the batch found by reading rather than by grepping one spelling |
| **B3** | **3** | **The only behaviour change to a shipped command, alone and reviewable as one thing.** Its review must see **three** things: task 13's arms A and B edited to exactly the stated post-edit lists with nothing else moved; the named credential-sweep tests whose **file set widens** re-run and reported green by name; and Fixture C's **two** arms, with M12 confirmed to fail the byte arm while the mapping arm still passes. A reviewer certifying "additive" must be the same one certifying "the copy is the same object `run.yaml` embeds" |
| **B4** | **4, 5, 6** | **`freeze`, end to end, and the first batch in which core calls a probe from a command that is not `run`.** **Its review must be a real-command review** — H7d Part A's only Critical was invisible to every direct-call probe and surfaced only through an end-to-end `run`, and every direct-call probe there hand-built the maps and so never reached it. It must see Fixture F5's **pair** (the credential's absence from stderr **and** `E-APPARATUS-RAISED`'s presence, since asserting only the absence passes identically if nothing ran), Fixture F1's lock byte-identical after `freeze`, and **Fixture F3's second process, which may not be downgraded to a constructed fixture** |
| **B5** | **7, 8** | **One projection, two readers.** Its review is **coverage arithmetic**: Fixture M's *pair* is what discriminates M4 — either arm alone passes under the narrowed walk — and task 13 arm G must still hold, which is what proves `parameters_hash` was rewritten over `covered_config` without changing what it hashes. It must confirm task 7's docstring makes **no** normalization claim (§ Corrections, correction 5) |
| **B6** | **9, 10, 11** | **The apparatus row, the exit code, the upstream block, and the CLI arm — one fixture set.** Its review is a **rendering review against emitted text**: A1's **two** condition-keyed lines (one line versus two is the observable difference), A2's identical arm under a **re-serialized** `facts` mapping, R2's exit `0` **beside** a `DIFFERS` row, and U's **five `identical`s**, which is what proves the block carries information no row does. It must check the CLI-table test moved for exactly one row |
| **B7** | **12** | **Codes, homes and the re-measurement.** Its review is a **guard-and-document review**: whether every § Errors row covers **every** emit site — `E-APPARATUS-CHANGED` gaining `freeze` at exit `1` beside its existing exit `4`, and H8a's three `E-UPSTREAM-RECORD-*` rows gaining `diff` — whether every sweep **named its files** rather than filtering its output, and whether the § Executability entry **repeats the four-row table unchanged and mints no fifth number** |

---

## Global Constraints

Every task inherits all of these. They are copied verbatim rather than cross-referenced, because an
implementer sees only their own task brief.

**Commands.** Tests `uv run pytest`. Lint `uv run ruff check .`. Format `uv run ruff format .`.
Types `uv run mypy`. All four must pass before a commit. **Baseline at `0a636af`: 2513 passed, 1
skipped, 2 xfailed; 84 files formatted; 47 source files typed.**

**The gate literals move in this slice, and the tasks that move them are named.**
`src/publishable/diff.py` and `src/publishable/freeze.py` take `mypy` to **48** from task 8 and
**49** from task 4 respectively — an implementer who reads 47 as the expected number after either
will reconcile a "failure" that is a new module. `ruff format --check` rises by each new file:
`src/publishable/freeze.py` + `tests/test_freeze.py` in task 4 (**86**), `src/publishable/diff.py` +
`tests/test_diff.py` in task 8 (**88**). Nothing else adds a file. **Every task states its own DELTA
on the test count, not an absolute**; compute the absolute from your own previous run and reconcile
any difference before committing.

**Run `uv run pytest` DIRECTLY, in the foreground, and wait for it.** It takes about two and a
quarter minutes at this baseline. **Never construct a wait, a monitor, a poll or a background run
around it** — several agents on preceding slices stalled that way and one stopped with a mutation
still applied. Clear `__pycache__` and any stale `pytest-of-*` temp directory before a run.

**Verify format with `uv run ruff format --check .`, never the bare form.** A previous brief in this
repo wrote the bare form where it meant `--check` and rewrote 67 files. **`ruff format` does not
process `.md`** — measured twice on preceding branches by copying a document, running the formatter
and diffing byte-identical; two agents nonetheless reverted documents on that misdiagnosis. A revert
is verified by **behaviour**, never by `git status`, and least of all by an account of what caused
the change.

**Every task says whether its surface is `validate`, `run`, a new command, a direct call, or
documents.** **No task's surface is `validate`, and none is owed** — § The apparatus core can only
observe enumerates where a probe runs (*"`dry-run`, at run start, before every execution, and at
`freeze` — never at `validate`"*) and neither `diff` nor `freeze` is a `validate`-time check of
anything. **That is a fact, not a filing**, and no task may file it as a gap.

**Nothing in H8b stops or alters a run except task 3, and task 3 alters nothing a reader can
observe.** Task 3's claim is **additive only**: no existing artifact's bytes change, no verdict
changes, no `status`, no exit code, no `provenance` key, no hash. Measured at `0a636af`: `code_hash`
covers `src/**` + `templates/**` and a run directory is outside both; `input_manifest_hash` covers
`input_dir`; `parameters_hash` covers the config; nothing in `src/` globs or iterates the run
directory's root. Task 3 pins the claim rather than asserting it.

**`freeze` writes exactly one kind of byte and every task that touches it states what it must NOT
touch.** § One execution at a time: `freeze` *"executes nothing and writes nothing but one line to
the append-only probe ledger, so it is safe against a live lock — which is the entire point of having
it."* So `freeze` does not take the run's lock, does not create or remove `lock`, does not write or
modify `run.yaml`, does not touch `environment/`, `sweep.yaml`, `allocation.json`,
`executions.jsonl` or any step directory, and changes no status. Fixture F1's assertion that `lock`
is **byte-identical after `freeze`** is what catches a `freeze` that takes or clears it.

**A probe costs somebody else's quota, and that constrains PLACEMENT, not testability.** Core only
ever needs a **fake** probe — a registered callable whose answers come from a file the test writes,
which is H7d Part A's shipped Fixture P shape. No test in this slice may call a real service. What
quota constrains is where a probe call sits relative to a cheap objection: § Exit codes' argument for
`dry-run`'s phase ordering is the precedent, verbatim — *"the cheap objection should never be
reported second, behind a metered request that was going to fail anyway."* Every `freeze` refusal and
the credential pre-check therefore report **before** the probe is called, and Fixture F5's sibling arm
pins that by a probe that writes a flag file and an assertion on the flag's **absence**.

**Every literal is computed, not guessed, and every mutation names the assertion that catches it AND
why the two branches can differ.** Across recent slices several prescribed mutations could not
discriminate: one *was* what the shipped code already did, one made both branches identical, one was
intercepted by an assert an earlier batch added, one was **placed one line off** and so tested a
different property, and one **fired for the wrong reason** because a different clause already refused
the fixture. **A mutation that changes nothing is evidence about the tests, not about the code**, and
"no mutation reaches this" and "no mutation *can* reach this" are different claims.

**Read every fixture literal back from what produced it.** Measured at `0a636af`: `run_a_project`
prefixes a generated step's name (`extra_steps=["step09_publish"]` produced
`step02_step09_publish`), and every hash a fixture asserts must be read back from the record or
recomputed by the hash function over the same inputs — never written as a literal, which would pin
the test to this repo's tree at fixture-writing time.

**`run_a_project` rewrites the config with `yaml.safe_dump`, and that makes one prescribed mutation
blind.** Measured at `0a636af`: `yaml.safe_dump(yaml.safe_load(x)) == x` is **True** for the config
that helper writes, so a `run` writing `yaml.safe_dump(doc)` instead of copying bytes produces
**byte-identical** output there. Fixture C therefore may **not** be built on `run_a_project`; task 3
prescribes the mechanism instead (§ Corrections, correction 2).

**Mutation discipline, every task.** Keep a copy of the file before mutating. Apply the named
mutation. Run the named test, confirm it **FAILS**, then run the **full, unfiltered** suite in the
foreground. Then `find . -name __pycache__ -type d -exec rm -rf {} +`. Then revert **by editing the
file back in place** — **never `git checkout -- <file>`**, which destroys uncommitted work and has
been mistaken for a revert three times in this repo. Verify the revert by **behaviour** and by
diffing against your saved copy, never by `git status`.

**A safety argument in a comment is a claim, and needs a mutation like any other.** Decision 13's
whole existence is that proof: `append_observation`'s docstring already claims a *"closed vocabulary
of four … named here so H8's and H9's callers do not mint a fifth spelling"*, and the mutation
re-run at `0a636af` wrote `"BOGUS_FIFTH_SPELLING"` **verbatim** to `apparatus/probes.jsonl`. **Five
consecutive batches on H7d Part B shipped a false comment**, the last promising that a committed task
would fix the line it sat on. If a comment you write says *this cannot happen*, make it happen.

**Redaction: every diagnostic `freeze` prints goes through a fresh credential-bearing `Collector`,
and `KeyboardInterrupt` is re-raised fresh and argument-less.** Measured at `0a636af`: `main`'s
`except PublishableError` prints `f"  error   {exc.code:<20} {exc}"` with **no collector in scope**,
so anything reaching it is un-redacted; a non-`PublishableError` reaching it ends the command in a
traceback. `observe_once`'s own docstring says the redaction *"is NOT here — the call site turns it
into a diagnostic through a fresh `Collector` carrying `credentials`."* `freeze.py` is a **new** call
site for `_probe_for` and `observe_once`, in a process `command_run`'s containment does not reach. An
implementer who prints `str(exc)` here ships the leak H7c shipped once already, by grepping for one
spelling while a bare `{exc}` site leaked to stderr. **Enumerate by reading where a thing can happen,
then confirm with greps; the reverse order is the substitution that shipped that leak, made by the
author of the rule forbidding it.**

**Answering a question with a proxy** is this repo's most expensive habit; both fail-opens in H7a and
a shipped credential leak in H7c came from it, and one corner was given **five** wrong grounds across
two slices. Here: *which form is this path* is answered by its **shape** — a directory, or a file
named `run.yaml` — and by nothing else, never by parsing content and never by whether a record loads.
*Which repo did this run come from* is answered by `environment/repo_root.txt`, the value
`command_run` wrote, **never** re-derived by walking up from the run directory, which finds whatever
repo happens to sit above `output_dir`. *Is this the same apparatus* is answered by
`provenance.apparatus.hash`, never by comparing the `facts` mappings, whose key order the hash is
invariant to. *Did the copy come from the right object* is answered by **bytes** against the source
file **and** by the parsed mapping against `run.yaml`'s embedded `config`, because either alone
passes under a different wrong answer. *Is this run over* is answered by `run.yaml`'s presence, never
by the lock's absence.

**Never filter the output of a sweep whose job is to find a string — filter the FILE LIST**, and
prove each sweep can fail by running it against a string known to be present. **Name the four
documents explicitly (`README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`,
`docs/reference.md`), and name `CLAUDE.md` and `docs/feasibility-llm-growth-studies.md` too**: H7d
Part A's Major 1 was a paraphrase surviving in the feasibility analysis because the brief's sweep
named only the four. The development record under `docs/superpowers/` is **not** governed by the
cross-document pass and is never retro-edited; `spec-defects.md` is the one exception, where a closed
gap is **struck** rather than left to mislead.

**When a change makes a sentence false, that sentence is in the diff already being read.** A
cross-batch stale row was H8a's only whole-branch Major. Three specific instances are pre-named here
so nobody discovers them: task 6 changes `OPERATION_COMMANDS`'s value, and the literal
`OPERATION_COMMANDS = {"validate", "run"}` is **quoted** in `artifacts.build_allocation_document`'s
docstring and in `reference.md` § Resuming (§ Corrections, correction 3); task 3 makes § CLI
reference's `resume` sentence — *"that run directory already contains the config it used"* — **true**;
and task 12 makes `CLAUDE.md`'s *"`EXIT_EXTERNAL` … defined in `diagnostics.py`, read by nothing"*
clause more false than it already is (§ Corrections, correction 4). **Prefer deleting a claim to
rewriting it** — a rewrite invents, a deletion cannot — and when you edit a docstring, re-read the
whole one.

**Documentation rules.** `×` not `x` for multiplication, including inside fenced blocks. Hyphen,
never an en dash, in anything that becomes a filename or an anchor. **Cite by section**
(`reference.md` § "The apparatus files"), **never by line number**. **No positional locators** ("the
row above", "further up"): name what a sibling row *does*, and when you insert a row check every row
it **moved** and every count phrase near it. **No counts in prose or comments** and **no call-site
enumerations**. **A build fact is dated and pinned to a commit** — today is **2026-08-20**.

**§ Errors carries one row per code, covering every emit site**, not one row per site — the
`E-TEMPLATE-UNKNOWN` two-emit-sites shape, which went on claiming "no installed template registers"
under a row just rewritten to say otherwise. In this slice that binds four shipped codes:
`E-APPARATUS-CHANGED` gains `freeze` (and a second exit code, `1` beside its existing `4`), and
`E-UPSTREAM-RECORD-MISSING`/`-UNREADABLE`/`-VERSION` each gain `diff`. It also binds the four
**template** codes `freeze` reuses rather than re-mints — `E-TEMPLATE-UNKNOWN`,
`E-TEMPLATE-INSTALLED-UNSUPPORTED`, `E-TEMPLATE-LOAD`, `E-TEMPLATE-COLLISION` (§ Corrections,
correction 6).

**The four normative documents LEAD; `src/` follows.** Where they and the code disagree, **the
document changes first** and the gap is recorded in `docs/superpowers/spec-defects.md`. **This
slice's spec, `H8-SCOPING.md`, and every preceding plan and ledger must not be retro-edited.**

**Do not touch the worked example.** `cohort-pilot` runs no `freeze`, so every interval and hash
prefix in `CLAUDE.md` § The worked example stays as it is. The only changes any document owes it are
the two new run-start artifacts in § Run identity's tree and § The other files a run writes, and the
ASCII `...` → `…` in the two worked `diff` outputs that still use it.

**Nothing new is exported.** `publishable/__init__.py`'s `__all__` is untouched: `covered_config`,
`replay_ledger`, `PHASES` and both command modules are core's own plumbing. A task that exports any
of them has undone Decision 14 rather than tidied an import.

**`tests/conftest.py` already has** an autouse `os.environ` restore, an opt-in `registries` fixture
and an opt-in `installed` distribution fixture. **Do not add duplicates, and do not add a second
autouse fixture of any kind.**

**`validate` collects rather than aborting.** It matters here only in the negative: there is nothing
in this family for `validate` to collect, so no task may infer anything about a `validate` finding
from H8b's behaviour, and no task may reason that a `freeze` refusal makes a later `freeze` check
unreachable — two independent readers on a preceding slice recorded a mutation as blind on exactly
that reasoning before a reviewer disproved it by building the fixture.

---

## The discriminating fixtures, stated once because the tasks share them

**A fixture is a claim too.** Carried from the design's § The discriminating fixtures, with every
literal re-derived here against the code at `0a636af` by **running**. **No later task may weaken any
constraint below**, and a substitute must meet all of them. Six fixtures across H4d failed their own
constraints and every one was caught by computing rather than by reading.

### Fixture R — one real completed run, the base record

A scaffolded project, a 24-row synthetic index, `sweep.grid` over `analysis.method` (2 conditions), 5
`seed` repeats, through `main(["run", …])`, exit `0`, `status: completed`. **Measured at `0a636af`**
by driving exactly that: the run directory root holds
`['conditions', 'environment', 'executions.jsonl', 'manifest', 'run.yaml', 'sweep.yaml']`;
`environment/` holds `['pyproject.toml']` alone; `provenance.environment` is
`{manager: uv, python_version: …, uv_lock: None, uv_lock_hash: None}`; `provenance.apparatus` is
`None`; `provenance.upstream` is `[]`; and `run.yaml`'s embedded `config` equals
`yaml.safe_load` of the config file. **Note the sweep axis is spelled `analysis.method`, not
`parameters.analysis.method`** — the latter earns `E-SWEEP-PATH-UNKNOWN` and the run never happens;
that mistake cost this plan's author one measurement run. Every figure `diff` prints for Fixture R is
read back from the record it wrote, or recomputed by the hash function over the same inputs — never
asserted against a literal.

### Fixture R2 — the same run, one parameter edited

Fixture R's config with `parameters.analysis.min_samples` moved and nothing else, run again. This is
the documented payoff. The assertion is: `code_hash` and `input_manifest` `identical`; `uv.lock`
**`not captured`** (measured: `uv_lock_hash` is `None` on a scaffolded project, so this branch is
entered by the default fixture and M1 is not blind); `parameters_hash` `DIFFERS` with **exactly one**
delta line whose path and both values are read from the two configs rather than typed; **and exit
`0`**, which is M5's discriminator.

### Fixture L — the lockfile row's non-null path

Fixture R's project with a real `uv.lock` written and committed **before** the run, so
`environment/uv.lock` and `uv_lock_hash` are non-null — and a second run after the lockfile's bytes
change. **Without this fixture the `uv.lock` row's `identical` and `DIFFERS` arms ship unpinned**,
because every scaffolded run takes the `not captured` branch. `tests/test_acceptance.py`'s
`test_a_present_lockfile_is_captured_and_hashed_with_no_warning` is the shipped shape to copy: a
one-line stand-in lockfile, `git add`ed and committed, because `code_hash` does not cover it but a
dirty tree refuses the run for an unrelated reason. Measured at `0a636af`: `uv_lock_info` is a plain
content hash with **no `--locked` drift check**, so changing the file's bytes is sufficient and
nothing needs `uv` to resolve.

### Fixture M — `metadata` versus `limits`, the coverage pin

Two records differing **only** in `metadata.description`, and two differing only in
`limits.max_failed_fraction`. The first must print `parameters_hash identical` with **zero** delta
lines; the second `DIFFERS` with exactly `limits.max_failed_fraction` and its two values. **The two
arms cannot both pass if the delta walk and `parameters_hash` disagree about coverage** — and only
the pair discriminates M4, because the narrowed walk still passes the first arm.

### Fixture P — the probe plugin, inherited

H7d Part A's shipped shape, reused rather than reinvented: a synthetic installed distribution
registering a probe through `tests/conftest.py`'s `installed` fixture, a project-local template
declaring `apparatus_probe` and `apparatus_facts`, and a probe whose answers come from a file the
test writes, so a fact can be moved between calls. **Two conditions**, so the per-condition scope is
exercised rather than assumed. Two measured traps: `Param`'s first argument is **positional**
(`Param(str, default=…)`, not `Param(type=str, …)`) and a template file that raises while importing
becomes `E-TEMPLATE-LOAD` at `generate experiment` rather than anything about probes; and
`templates/**` is inside `code_hash`, so the template file must exist **before** the fixture's
`git add`.

### Fixture A1 — `apparatus DIFFERS`, two conditions moving

Two Fixture P runs whose probe answers a different `calibration_id` in the second. The assertion is
**two** detail lines, one per condition key, each carrying that condition's own old and new values
read from the two records' `provenance.apparatus.facts`. This is the fixture that catches a
collapsing implementation and the one that catches a line printed without its condition key — one
line versus two is the observable difference.

### Fixture A2 — `apparatus identical`, and the one-sided case

A Fixture P pair whose facts agree (row prints `identical` with the digest), **with one record's
`facts` mapping re-serialized in a different key order**, which is what makes M2 discriminate:
`apparatus_hash` canonicalizes under `sort_keys=True` and is invariant to the reordering the mapping
comparison is not. Plus a Fixture P record against a Fixture R record (`apparatus: null` on one side
→ `DIFFERS`, with a line naming which side recorded none), which is what pins "the row appears
whenever either side has one."

### Fixture C — the run-start config copy

**Not built on `run_a_project`** (§ Corrections, correction 2). A scaffold whose generated config is
edited **as raw text** — targeted string replacement filling `metadata.description` and
`metadata.authors`, which `init` writes empty and `validate` requires — so the file keeps every
inline comment `init` wrote. Measured at `0a636af`: `generate_experiment` writes a config carrying
`#` comments on most lines, and a `yaml.safe_load`/`safe_dump` round trip removes all of them. Two
assertions, and neither alone is sufficient: `(run_dir/"config.yaml").read_bytes() ==
cfg.read_bytes()` catches a re-dump, and `load_document(run_dir/"config.yaml") == run_yaml["config"]`
catches a copy taken from a different object.

### Fixture F1 — `freeze` on a constructed mid-run directory

Fixture P's run directory with `run.yaml` **deleted** and a `lock` file written by hand — a
**constructed** mid-run state, and this plan says so rather than calling it a real one. `freeze` must
exit `0` when the probe's answers match, append exactly one line per condition with `phase:
"freeze"`, and leave the `lock` file **present and byte-identical**. That last assertion is what
catches a `freeze` that takes or clears the lock (M10).

### Fixture F2 — `freeze` sees a moved fact

Fixture F1 with the probe's answer file changed between the run and the `freeze`. Exit **1**,
`E-APPARATUS-CHANGED`, the condition key and both values in the message — **and the ledger holding
the moving observation afterwards**, since that is what makes the report legible from the artifacts.

### Fixture F3 — `freeze` against a live run, in a second process

**The one H8b surface that needs concurrency, and the only test in this slice allowed a handshake.**
A run whose probe blocks on a sentinel file while the test invokes `freeze` against the same
directory, with a timeout. It pins one thing no constructed fixture can — that a **genuinely held**
lock does not stop `freeze` — and nothing else depends on it. **It may not be downgraded to a
constructed fixture**, which the design names as the most likely quiet loss in this slice. Fixture
F1's hand-written `lock` proves core does not *read* the lock file; F3 proves nothing else in the
process does either.

### Fixture F4 — each refusal, one run directory apiece

Seven directories plus the reused-code arms, each differing from Fixture F1 in exactly the one way
its code names, **asserted by code and not by message text**: `run.yaml` restored
(`E-FREEZE-RUN-ENDED`); `config.yaml` removed (`E-FREEZE-NO-CONFIG`); a template declaring no probe
(`E-FREEZE-NO-APPARATUS`); the ledger emptied of `run_start`/`pre_execution` lines
(`E-FREEZE-LEDGER-MISSING`); a template declaring a **second registered** probe name
(`E-FREEZE-PROBE-MISMATCH`); `sweep.yaml` removed (`E-FREEZE-PLAN-MISSING`); the config copy's
`sweep` edited so re-expansion yields a different label set (`E-FREEZE-PLAN-MISMATCH`). **Plus four
arms for the codes `freeze` reuses rather than mints** (§ Corrections, correction 6): the config
copy's `experiment_type` renamed to a name nothing claims (`E-TEMPLATE-UNKNOWN`), to a name only an
installed distribution claims (`E-TEMPLATE-INSTALLED-UNSUPPORTED`), a second `templates/*.py`
claiming the same name (`E-TEMPLATE-COLLISION`), and a `templates/*.py` that raises while importing
(`E-TEMPLATE-LOAD`). **Every arm also asserts the ledger gained no line**, which is what makes each
refusal a refusal rather than a report after the fact.

### Fixture F5 — a probe that raises with a credential in the message

Fixture P's plugin with a probe that reads a declared `requires_env` variable and raises carrying its
value, invoked through `freeze`. The assertion is **the pair**: the credential's **absence** from
stderr **and** `E-APPARATUS-RAISED`'s presence at exit **`5`** — asserting only the absence passes
identically if nothing ran. Its sibling arm unsets the variable entirely and asserts the credential
pre-check reports **before** the probe is called, by a probe that writes a flag file and an assertion
on the flag's **absence** at exit `5`. **Its credential is declared on a parameter value's
`requires_env`, not on the template's `required_env`** — that is what makes M16 discriminate.

### Fixture U — the upstream block

Two runs identical in all five rows, one of which consumed an upstream through `io.reuse_from` and
one of which did not — reachable today because H8a ships the method. The assertion is the block's
presence, its `run_id`, and the "these differ only in their upstreams" line. **The five rows must all
read `identical` in this fixture**, which is what proves the block carries information no row does.
Measured at `0a636af`: `UpstreamLedger.record` uses `record.get("code_hash")`, so an entry's hash
**can** be `None`; task 11 renders that as `not captured` and **does not close the open filing that
names H8b as its secondary consumer** (§ Corrections, correction 7).

---

## Task 13: the guard pin, its literals captured at `0a636af`

**Runs FIRST, before task 14 and before every other task. Surface: `run` plus one direct call.**
Decision 7 changes the run directory, so what must be captured first is **the run directory's
contents** — plus every figure `diff` will read and every `sweep.yaml` field `freeze` will
cross-check. A literal recorded afterwards records the change, not the baseline.

**Files:**
- Test: `tests/test_cli.py` (add), `tests/test_hashes.py` (add)

**Interfaces:**
- Consumes: `run_a_project`, `yaml.safe_load` over `run.yaml` and `sweep.yaml`,
  `hashes.parameters_hash`.
- Produces: nothing importable. Arms every later task's suite run must keep green.

**The property.** For a run of template `generic` — every run in this repo's suite and the worked
example — nothing about the run directory's contents, `environment/`'s contents, the record's key
lists, the five figures `diff` reads, `sweep.yaml`'s recorded plan shape, or `parameters_hash`'s
agreement with its own embedded config moves in this slice **except in the two places named below**.

- [ ] **Step 1: re-capture every arm yourself, by running.** These were produced at `0a636af` by
      driving `run_a_project` and reading the artifacts back. **Re-run them before writing the
      assertions** and reconcile any difference: a pin whose expected value was transcribed from
      `cli.py` pins the source, not the behaviour.

```
Arm A — THE RUN DIRECTORY'S ROOT. ONE OF TWO ARMS AN AUTHORIZED TASK MAY EDIT.
  sorted(p.name for p in run_dir.iterdir()) ==
    ['conditions', 'environment', 'executions.jsonl', 'manifest', 'run.yaml', 'sweep.yaml']
  (a run with no sweep has no `conditions`; drive one WITH a sweep so the list is this one)
  and (run_dir / 'lock').exists() is False

Arm B — environment/'s CONTENTS. THE SECOND ARM AN AUTHORIZED TASK MAY EDIT.
  sorted(p.name for p in (run_dir / 'environment').iterdir()) == ['pyproject.toml']
  (a scaffolded project resolves no lockfile — the W-ENV-UNLOCKED path)

Arm C — the record's key lists. NEVER MOVES IN THIS SLICE.
  run.yaml top-level keys, in order:
    ['schema_version', 'run_id', 'status', 'draft', 'config', 'parameters_hash',
     'code_hash', 'provenance', 'layout', 'execution', 'results']
  provenance keys, in order:
    ['git', 'environment', 'apparatus', 'input_manifest', 'input_manifest_hash',
     'input_manifest_changed', 'publishable_version', 'plugin_versions', 'units',
     'units_hash', 'allocation', 'allocation_hash', 'upstream']
  status = 'completed'; draft is False; exit = 0

Arm D — THE FIVE FIGURES `diff` READS. NEVER MOVES IN THIS SLICE.
  provenance['environment'] == {'manager': 'uv', 'python_version': <read back>,
                                'uv_lock': None, 'uv_lock_hash': None}
  provenance['apparatus'] is None
  provenance['upstream'] == []
  code_hash and parameters_hash and provenance['input_manifest_hash'] each start 'sha256:'
  (the DIGESTS are read back, never asserted as literals)

Arm E — sweep.yaml's RECORDED PLAN, which `freeze` cross-checks. NEVER MOVES IN THIS SLICE.
  sweep.yaml top-level keys == ['design_digest', 'conditions', 'repeats', 'labels',
                                'order', 'execution_order']
  every conditions[] entry's keys == ['index', 'label', 'values', 'is_baseline']
  'selectors' not in any conditions[] entry     # why Decision 8 re-expands
  design_digest(run.yaml['config']) == sweep.yaml['design_digest']

Arm F — the embedded config is the file. NEVER MOVES IN THIS SLICE.
  run.yaml['config'] == yaml.safe_load(cfg.read_text())

Arm G — parameters_hash AGREES WITH ITS OWN EMBEDDED CONFIG. NEVER MOVES IN THIS SLICE.
  parameters_hash(run.yaml['config']) == run.yaml['parameters_hash']
  and parameters_hash over a config differing ONLY in metadata.description is EQUAL
  and parameters_hash over a config differing ONLY in limits.max_failed_fraction DIFFERS
```

- [ ] **Step 2: write the arms.** One test per arm, named for what it asserts. Arms A, B, C and E
      assert the **full sorted list or full key list, as a list, not membership** — a file or key
      added by accident is exactly what this catches and a membership assertion would not see it.
      Arm G belongs in `tests/test_hashes.py` beside the shipped `parameters_hash` tests and takes
      its two extra sub-arms there directly, without a `run`: it is a pure function, and its point is
      that **task 7 rewrites its body without changing what it hashes.** Arm G's second and third
      sub-arms are Fixture M's arithmetic proven at the function level before any renderer exists.

- [ ] **Step 3: write the authorized-edit clauses, naming their editor and the post-edit state.**
      Two arms move in this slice and **task 3 is the only task permitted to edit either**:
      - **Arm A**'s docstring states: task 3 appends `'config.yaml'` to the list, keeping it sorted,
        and **nothing else changes** — the post-edit list is
        `['conditions', 'config.yaml', 'environment', 'executions.jsonl', 'manifest', 'run.yaml',
        'sweep.yaml']`.
      - **Arm B**'s docstring states: task 3 appends `'repo_root.txt'`, keeping it sorted — the
        post-edit list is `['pyproject.toml', 'repo_root.txt']`.
      Both clauses add: **task 3's report must show the diff is exactly one entry per arm with
      nothing reordered.** **Every other task that finds any arm failing has found a finding to
      report, not an assertion to edit.** Without these clauses the arms are change detectors the
      slice must silently weaken, which is indistinguishable in the record from weakening a pin to
      pass.

- [ ] **Step 4: run.** `uv run pytest` → **2513 + your new tests** passed, 1 skipped, 2 xfailed.
      `uv run mypy` → still **47 source files**; `uv run ruff format --check .` → still **84 files**.
      This task adds no file and no module.

- [ ] **Step 5: the mutation, and it is the shape task 3 could produce by accident.** In
      `src/publishable/cli.py`, inside the `with RunLock(run_dir):` block beside the shipped
      `environment/pyproject.toml` capture, add
      `(run_dir / "environment" / "stray.txt").write_text("x")`. Run the **full** suite. **Arm B must
      FAIL** on the list assertion and **arm A must PASS. Why the two branches differ:** the
      `environment/` list gains an element while the run directory's root list does not, so this
      proves arm B reads the directory task 3 edits and arm A reads a different one. Then move the
      same line to write `(run_dir / "stray.txt")` and confirm the reverse — **arm A fails, arm B
      passes.** Two mutations, because one arm proving itself does not prove the other is not reading
      the same thing. Revert by editing both lines out; confirm green by behaviour.

- [ ] **Step 6: commit.** `git add -A && git commit -m "H8b task 13: pin the run directory, the
      record's figures and the recorded plan before anything moves"`.

---

## Task 14: what a third `config.yaml` inside a run directory means — the document, before the code

**Runs SECOND, before task 3. Surface: documents only.** The controller's requirement, in its own
terms: Decision 7 *"IS a behaviour change to a shipped command, and it must be explicit rather than
incidental."* § The two files is framed as *"`config.yaml` and `run.yaml`"*, and a **third** file
inside the run directory named `config.yaml` bears on it. **This task says what the document must
say; task 3 writes the bytes.** Do not let task 3 discover the collision.

**Files:**
- `docs/reference.md`

**Interfaces:** none. No code changes and no test changes in this task.

**What each section must end up saying, and why it is that section's business.**

- [ ] **Step 1: § The two files gains the distinction, and does not lose its framing.** That section
      names two files by their **roles** — *what you edit* and *what you report* — and a run-start
      capture is neither. So the sentence to add says: a run directory also holds a **byte copy** of
      the config it was started from, written at run start and never modified, whose purpose is to
      let a mid-run command (`freeze`, and `resume` when it lands) reach the config a run is
      executing under **before `run.yaml` exists**; it is not a second file to edit, and editing it
      does not change the run. **Do not renumber or rename the section** — "the two files" is the
      role count, not a file count inside a directory, and § The other files a run writes is already
      the section that enumerates what a run directory holds. State that relationship in one clause
      so the next reader does not file the same question.

- [ ] **Step 2: § The other files a run writes gains both artifacts, as contracts.** That section's
      own opening says each file below it *"is therefore a contract rather than a log"* and
      distinguishes *settled before the first execution and never touched again* from *grows as the
      run goes*. Both new artifacts are the **first** kind, beside `sweep.yaml` and `allocation.json`.
      Say for each what reads it and what the remedy is when it is absent: `config.yaml` is what a
      mid-run command loads instead of `run.yaml`, and a run started by a build predating it cannot
      be frozen; `environment/repo_root.txt` holds the absolute repo root the command walked up to
      from the config path, and it exists because a **project-local** template — where
      `apparatus_probe` is declared — resolves only through local discovery, which needs that root.

- [ ] **Step 3: § Run identity's tree gains both lines.** The tree already writes
      `environment/{uv.lock,pyproject.toml}` as a braced pair; `repo_root.txt` joins that brace and
      `config.yaml` takes its own line. **Use `├──`/`└──` exactly as the shipped tree does**, and
      check the last entry still uses `└──` after your insertion.

- [ ] **Step 4: § CLI reference's `resume` sentence becomes TRUE rather than being edited.** It reads
      *"that run directory already contains the config it used."* That sentence was the document
      defect `H8-SCOPING.md` § 4 found; **the fix is the artifact, not a rewrite.** So this step's
      work is to **verify the sentence needs no change** and to say so in the report — and to add
      nothing that would make it a claim about `freeze`, which is a different command. If you find
      yourself editing that sentence, you have resolved the defect the wrong way.

- [ ] **Step 5: name the boundary, once, so a later slice does not grow the artifact.** § The other
      files a run writes gains one sentence stating what the pair holds and what it does not: exactly
      the two facts a mid-run command cannot otherwise obtain **and cannot compute** — the config as
      it was, and the repo it came from. Everything else is either computable from those two
      (`parameters_hash(config)`) or is a **recorded** figure belonging to `run.yaml`; `code_hash` at
      run start is not recoverable from a tree that has since moved, which is why `freeze` does not
      compare code and `resume` (H9) does. **Do not enumerate what a future command will read** — a
      claim about a slice that has not landed goes stale the way every one before it did.

- [ ] **Step 6: both consistency passes, over the FOUR DOCUMENTS BY NAME plus `CLAUDE.md` and
      `docs/feasibility-llm-growth-studies.md`.** Mechanical: every relative link and `#anchor`
      resolves, no two headings in a file share an anchor, every table's rows match its header's
      column count, no trailing whitespace, no tab, no invisible unicode, `×` not `x` — **skipping
      fenced code blocks**, since the docs contain markdown inside markdown. Cross-document:
      **Config completeness** does not apply (no config field is added — `config.yaml` inside a run
      directory is an artifact, not a schema field, and no task may add it to § The one config file);
      **Schema fields in prose** does (both new artifacts must appear in a tree or an enumeration and
      in prose, and vice versa). **Run each sweep against a string known to be present first**, and
      **filter the FILE LIST, never the sweep's output.**

- [ ] **Step 7: run the gates.** No code changed, so `uv run pytest` → **unchanged from task 13's
      total**. `ruff format` does not process `.md`; if a `.py` file appears in `format --check`'s
      output, something other than this task moved it — **find it rather than reverting on a story.**

- [ ] **Step 8: commit.** `git add -A && git commit -m "H8b task 14: what a run-start config copy is,
      said before the code writes one"`.

---

## Task 1: `replay_ledger` — the baseline, replayed through the shipped `Observations`

**Surface: a direct call.** Nothing dispatches in this task and nothing reads the ledger before it.
Measured at `0a636af`: `grep -rn "probes.jsonl" src/publishable/` finds `append_observation`'s writer
and `Observer.block`'s recorded path string. **No reader exists.**

**Files:**
- Source: `src/publishable/apparatus.py`
- Test: `tests/test_apparatus.py`

**Interfaces:**
- Produces: `replay_ledger(run_dir: Path) -> Observations`.
- Consumes: `Observations.record` (the **shipped** method), `json.loads`, `errors.ContractError`.

**Decision 9, and the property that comes from structure rather than from a test.** `replay_ledger`
reads `<run_dir>/apparatus/probes.jsonl` line by line and calls the **shipped
`Observations.record`** for each line whose `phase` is `run_start` or `pre_execution`, **in file
order**. Two properties follow and neither is re-derived: the first-answered rule cannot drift from
the gate's, **because it is the gate's code** — `H8-SCOPING.md`'s stated risk for this task (*"the
reconstruction must reproduce H7d Part B's rule exactly, or `freeze` and the gate disagree about the
same run"*) is closed structurally; and the per-condition scoping, the `null → value` and
`value → null` transitions, and `_unchanged`'s reflexivity carve-out for `nan` all come along
unchanged. **Do not reimplement any part of `Observations`, and do not add a keyword to `record`.**

**Decision 14's home, with grounds.** It lives in `apparatus.py`, beside the `append_observation`
that writes the file it reads and the `Observations` it replays into. `freeze.py` is refused as its
home on H8a's own argument for `read_run_record`: a reader of a file in a different module from its
writer is how the two drift.

- [ ] **Step 1: write the function so its docstring states the phase filter and WHY, in one
      paragraph.** The observations the run's own in-memory `Observations` holds are exactly its
      `run_start` and `pre_execution` calls. A `freeze` line is not one of them, and including one
      would let a fact **first answered to `freeze`** become a pin the run's own gate never adopted —
      so a second `freeze` would report a change the run will never fail on, which is the false stop
      H7d Part B's null handling exists to prevent. A `dry_run` line is excluded for the same reason
      and one more: nothing calls it (§ Refusals routes that contradiction to H9). **Do not write a
      sentence claiming any of this is unreachable** — say what is filtered and why, not what cannot
      happen.

- [ ] **Step 2: the refusals, and there is exactly ONE.** A malformed ledger line — not valid JSON,
      not a mapping, or missing `phase`/`condition`/`facts` — is `E-FREEZE-LEDGER-UNREADABLE`. **An
      absent file is NOT this function's refusal**: it returns an empty `Observations`, because
      "there is no baseline" is task 4's `E-FREEZE-LEDGER-MISSING` to report and it needs to
      distinguish *no file* from *a file with no qualifying line* — both of which land as an empty
      baseline here, and both of which that one code covers with one remedy. Say that split in the
      docstring so the next reader does not add a second code for it. A line whose `phase` is
      unrecognized is **skipped, not refused** — the ledger is append-only and a future build may
      write a phase this one does not read, and refusing would make an old `freeze` unable to read a
      newer run's ledger for no benefit.

- [ ] **Step 3: tests, on synthesized ledgers plus one real one.** A real one: Fixture P's run
      directory, whose `probes.jsonl` was written by `append_observation` and whose replay must
      reproduce `provenance.apparatus.facts` from the same run's `run.yaml` — read back from both
      files, never asserted as a literal. **That arm is what pins that the reader reads what the
      writer wrote.** Then the synthesized arms, each with a distinguishable shape: two conditions
      with different facts; a fact whose first line is `null` and whose second answers, asserting the
      **answer** wins; a fact answered then `null`, asserting the **answer** is kept; the malformed
      line; and the empty/absent file returning an `Observations` whose `facts_document()` is `{}`.

- [ ] **Step 4: M8 — include `phase == "freeze"` lines in the baseline.** The fixture: a declared fact
      that is `null` on every `run_start`/`pre_execution` line, **answered** at a first `freeze`, and
      answered **differently** at a second `freeze`. **Caught by** the second `freeze`'s exit code.
      **Why the two branches differ:** with freeze lines excluded, both freezes see a fact that never
      answered, so both report it as newly answered and exit `0`; with them included, the first
      freeze's answer becomes the pin and the second contradicts it — `E-APPARATUS-CHANGED`, exit `1`.
      **Two different exit codes, not two different internal states.** This mutation's assertion
      cannot be written until task 6 gives `freeze` its verdicts; **write the fixture here, assert
      `replay_ledger`'s own `changed()` result here, and re-run it as an exit-code assertion in task
      6.** Say in the report which half you pinned where — a mutation split across two tasks that is
      only ever half-asserted is not pinned.

- [ ] **Step 5: M9 — reimplement first-answered as MOST RECENT.** Concretely: replace the
      `Observations.record` call with a loop assigning `_first_answered[pair] = value` unconditionally.
      The fixture: a ledger whose fact goes `r1 → null → r2` across `pre_execution` lines, then an
      incoming observation of `r1`. **Caught by** a direct assertion that `changed()` returns `None`.
      **Why the two branches differ:** under *first answered* the baseline is `r1` and `r1` agrees;
      under *most recent* it is `r2` and `r1` contradicts it. **`r1 → null → r2` is the one transition
      that distinguishes the two rules** — a two-element ledger cannot, because with two values the
      first is also the last but one. Revert by editing the call back in place.

- [ ] **Step 6: run.** `uv run pytest` → **+ your new tests**. `uv run mypy` → still **47 source
      files** (no new module). `ruff format --check` → still **84 files**.

- [ ] **Step 7: commit.**

---

## Task 2: `PHASES`, the four constants, the assert, and every core call site

**Surface: a direct call plus `run`.** Decision 13. Measured at `0a636af`, by running:
`append_observation(t, phase="BOGUS_FIFTH_SPELLING", …)` wrote that string **verbatim** to
`apparatus/probes.jsonl`. The docstring's *"closed vocabulary of four … named here so H8's and H9's
callers do not mint a fifth spelling"* is **unenforced at this commit**. **A safety argument in a
comment is a claim needing a mutation, and this one is false today.**

**Files:**
- Source: `src/publishable/apparatus.py`, `src/publishable/cli.py`, `src/publishable/runner.py`
- Test: `tests/test_apparatus.py`, `tests/test_cli.py`

**Interfaces:**
- Produces: `PHASES: frozenset[str]`, `PHASE_RUN_START`, `PHASE_PRE_EXECUTION`, `PHASE_DRY_RUN`,
  `PHASE_FREEZE`.
- Consumes: nothing new.

**The constants carry the property; the assert only backs them.** Under `python -O` the assert is
stripped, so a build running optimized loses the check — which is why **the named constants are the
point**: they make a fifth spelling unreachable by typo, where the assert only converts it into a
crash. Say that in the docstring, and do not claim the assert is the guarantee.

**Why an `assert` and not an `E-` code, ruled rather than inherited.** The only way to violate this
vocabulary is a **core call site**. No config, plugin, CLI argument or artifact can reach it, so
there is no reader for whom an `E-` code would be actionable and no § Errors row to write.
`Observations.changed`'s own shipped assert about its caller's ordering, and `execute_plan`'s asserts
about its callers, are the precedent — read at `0a636af`, not assumed.

**What it costs when it fires, MEASURED here rather than carried from H7d Part B.** Measured at
`0a636af` by patching `append_observation` to raise `AssertionError` from a real `run` through
`main(["run", …])`, twice:

```
Fired on the FIRST pre_execution round (no execution yet paid for):
  UNCAUGHT AssertionError traceback — `main` catches only PublishableError and OSError
  run directory holds ['apparatus', 'environment', 'manifest', 'sweep.yaml']
  run.yaml            ABSENT
  executions.jsonl    ABSENT
  lock                REMOVED (RunLock.__exit__ runs as the exception propagates)
  latest              never repointed

Fired on a LATER pre_execution round (one execution already paid for):
  UNCAUGHT AssertionError traceback
  run directory holds ['apparatus','environment','executions.jsonl','manifest','seed47','sweep.yaml']
  executions.jsonl    1 line — the paid-for execution
  run.yaml            ABSENT
```

**So the cost is `CLAUDE.md`'s own phrase, measured rather than quoted: every execution paid for, the
record lost.** The reason is that `execute_plan`'s pre-execution round is wrapped in
`except ContractError` and `AssertionError` is not one — deliberately, since a core-call-site fault is
not a fault in what the caller asked for. **Write that cost into the docstring**, and write it as the
measurement it is, dated to 2026-08-20. At `freeze` the cost is smaller and different: `main` catches
neither, so it is an uncaught traceback with **nothing appended**, because the assert is the
function's first statement.

- [ ] **Step 1: add `PHASES` and the four constants at module scope in `apparatus.py`**, with the
      docstring stating the two paragraphs above — the constants-carry-it argument and the measured
      cost. `PHASE_DRY_RUN` is **named here and called by nothing**; say so, and say that where a
      `dry_run` line is appended is **filed to H9** rather than answered here (§ Operation commands
      says `dry-run` *"creates nothing"* while § The apparatus files lists `dry_run` as a phase; both
      cannot hold).

- [ ] **Step 2: `assert phase in PHASES` as `append_observation`'s FIRST statement**, above the
      `mkdir`, above the line dict, above the open. Its message names the offending value and the
      four legal names. **Placement is the whole content of M6** — an assert below the write still
      raises while leaving a bogus line on disk.

- [ ] **Step 3: convert every core call site to a constant, enumerated BY READING rather than by
      grepping one spelling.** Measured at `0a636af`: `Observer._observe_one` receives `phase` from
      `Observer.observe_round`, which receives it from two callers — `cli.command_run`'s run-start
      round (`phase="run_start"`) and `runner.execute_plan`'s per-execution round
      (`phase="pre_execution"`). Both literals become constants. **Read the file for where a phase
      string can appear rather than grepping for `phase=`** — a grep for one spelling is the fourth
      proxy in `CLAUDE.md` § Answering a question with a proxy, and it shipped a credential leak.
      Confirm your enumeration with a grep afterwards, in that order.

- [ ] **Step 4: M7 — remove one name from `PHASES`.** The test: call `append_observation` once per
      name against a throwaway directory and assert **four** lines land, each carrying its own
      `phase`. **Why the two branches differ:** four names, four lines — removing any one turns a
      pass into an `AssertionError` at a named phase. Run it once per name removed, not once.

- [ ] **Step 5: M6 — move the assert BELOW the file write.** The test asserts **both** the
      `AssertionError` **and** that `probes.jsonl` gained no line. **Why the two branches differ:**
      the raise happens in both branches; **only the ledger's content distinguishes them.** This is
      the one-line-off shape, prescribed against deliberately. Revert by editing the statement back to
      the top; verify by behaviour.

- [ ] **Step 6: run.** `uv run pytest` → **+ your new tests, and no shipped test may change.** If a
      shipped test's count or outcome moves, the constants are not equal to the literals they
      replaced — that is a finding, not an assertion to edit. `uv run mypy` → **47 source files**.

- [ ] **Step 7: commit.**

---

## Task 3: `run` writes `<run_dir>/config.yaml` and `environment/repo_root.txt`

**Surface: `run`. This is the ONLY task in H8b that changes behaviour a shipped test can see, and it
lands alone in its own batch and its own commit** so a suite-count or pin change is attributable to it
and to nothing else.

**Files:**
- Source: `src/publishable/cli.py`
- Test: `tests/test_cli.py` (add — Fixture C), `tests/test_acceptance.py` (add)
- Edit: task 13's arm A and arm B, **the two edits this task is authorized to make**

**Interfaces:**
- Consumes: `config_path` (the argument `command_run` was given), `repo_root` (the value
  `find_repo_root(config_path)` already returned), the existing `RunLock(run_dir)` block.
- Produces: two artifacts. **No new function, no new module, no new record key.**

**The hole this closes, re-measured at `0a636af`.** A probe is `probe(cfg) -> Apparatus`, and the
config a run used is reachable from its run directory **only through `run.yaml`, written once at the
end** — while `freeze` exists precisely for a run that has not ended. `sweep.yaml`'s condition entries
carry `values` and **no `selectors`** (task 13 arm E pins that), and `resolve_condition_cfg` skips a
selector path precisely so a group cell never becomes a parameter, so an overlay built from that file
would invent a parameter no `parameter_spec` declares. And resolving the run's **template** — where
`apparatus_probe` and `apparatus_facts` are declared — needs the **repo root**: measured at
`0a636af`, `get_template("loc_assay", proj)` returns the class and `get_template("loc_assay", None)`
returns **`None`**, because `_claims` calls `discover_local` only when `repo_root is not None`. A
resolution writing only the config would have shipped a `freeze` that fails on exactly the templates
H7a made possible.

**The claim this task makes, and it must be pinned rather than asserted: ADDITIVE ONLY.** No existing
artifact's bytes change. No verdict, `status`, exit code, `provenance` key or hash changes. Measured at
`0a636af`: `code_hash` covers `src/**` + `templates/**` and a run directory is outside both;
`input_manifest_hash` covers `input_dir`; `parameters_hash` covers the config; and nothing in `src/`
globs or iterates the run directory's root, so adding a file there is inert to core. **That last
clause is a measurement about `src/`, not about `tests/`** — step 4 is where `tests/` is measured.

- [ ] **Step 1: write both artifacts inside the existing `RunLock(run_dir)` block, beside the shipped
      `environment/` captures.** Placement is not cosmetic: those captures are byte copies for the
      same reason, they sit before `sweep.yaml`, and a mid-run command must find the config **before**
      the first execution. Two lines, in this order after `environment/` is created:
      - `(run_dir / "config.yaml").write_bytes(config_path.read_bytes())` — **a byte copy, never a
        re-dump.** Measured at `0a636af`: `load_document` is pure `yaml.safe_load` plus a mapping
        check — no defaults injected, no path resolved — so the copy parses to a document **equal** to
        the one `run.yaml` embeds; and `doc` is never mutated between load and
        `assemble_run_yaml(config=doc)`, confirmed by reading `command_run` for assignment into `doc`
        and then by grep for `doc[…] =`, `doc.setdefault` and `doc.update`, **in that order**. A
        re-dump would silently drop every comment `init` wrote into the file.
      - `(run_dir / "environment" / "repo_root.txt").write_text(f"{repo_root}\n")` — one line, the
        absolute repo root `command_run` **already computed** by walking up from the config path it was
        given. **Never re-derived from `run_dir` or `output_dir`**, which answer a different question:
        which repo happens to sit above the results tree.

- [ ] **Step 2: the comment beside both lines says what they are FOR and what they are not, in two
      sentences.** They hold exactly the two facts a mid-run command cannot otherwise obtain **and
      cannot compute**: the config as it was, and the repo it came from. Everything else is either
      computable from those two or is a **recorded** figure belonging to `run.yaml`. **Do not write a
      sentence claiming a future command reads them** — `resume` is H9's and a claim about an unlanded
      slice goes stale the way every one before it did. **Do not write a sentence claiming this cannot
      break a reader**; step 4 is the measurement, and a comment asserting safety without one is the
      shape that produced H7d Part A's only Critical.

- [ ] **Step 3: Fixture C, and it may NOT be built on `run_a_project`.** Measured at `0a636af`:
      `run_a_project` rewrites the config with `yaml.safe_dump(doc)` and
      `yaml.safe_dump(yaml.safe_load(x)) == x` is **True** for what it writes — so M12 would be
      **blind** there, the two branches producing byte-identical output. The mechanism instead,
      prescribed rather than left to intent: scaffold with `main(["new", …])`, call
      `generate_experiment(...)`, then **edit the generated config as RAW TEXT** — a targeted string
      replacement filling `metadata.description` and `metadata.authors`, which `init` writes empty and
      `validate` requires — so every inline comment survives and the config still validates. Then
      commit and `main(["run", str(cfg)])`. The shipped
      `test_an_unwritable_output_dir_is_a_diagnostic_not_a_traceback` is the in-file precedent for an
      inline scaffold-and-run that does not go through the helper. **Two assertions, and neither alone
      is sufficient:**
      - `(run_dir / "config.yaml").read_bytes() == cfg.read_bytes()` — catches a re-dump.
      - `load_document(run_dir / "config.yaml") == run_doc["config"]` — catches a copy taken from a
        different object.
      Plus a **control** that makes the first non-vacuous: assert `b"#" in cfg.read_bytes()`, so a
      fixture whose config lost its comments for an unrelated reason fails here rather than making the
      byte arm pass for free.

- [ ] **Step 4: measure which shipped tests this MOVES, and report each by name.** Measured at
      `0a636af` by reading `tests/` for every enumeration of a run directory or of `environment/`:
      - **Nothing in `tests/` enumerates the run directory's root or `environment/`.**
        `tests/test_acceptance.py` asserts **membership** — `(run_dir / "executions.jsonl").is_file()`,
        `not (run_dir / "lock").exists()`, `not (run_dir / "environment" / "uv.lock").exists()`,
        and `environment/pyproject.toml`'s bytes against the repo's — none of which a new sibling
        moves. `tests/test_cli.py`'s one `iterdir` equality is over `results_dir`, **one level up**
        (`== sorted(["latest", run_dir.name])`), which Decision 7 does not touch. The `rglob`
        assertions filter to **directories** (`if p.is_dir()`), and both new artifacts are files.
      - **One pin's SCOPE widens**: `tests/test_cli.py`'s `_files_under(results_dir)` sweeps **every
        file** a run wrote for a credential sentinel, and the two new artifacts enter that set. **Run
        every test that calls it, by name, and report them green** — reasoning that a credential value
        cannot appear in a config (the config holds a variable's **name**; `credential_values` reads
        the value from the environment) and cannot appear in a repo-root path is the right reasoning
        and **is still not the measurement.**
      - **`provenance` gains no key**, so task 13 arm C, H8a's guard-pin arm B and the shipped
        apparatus key-list test do **not** move. If any of them fails, the change is not additive —
        that is a finding, not an assertion to edit.

- [ ] **Step 5: edit task 13's arm A and arm B — the two edits this task is authorized to make.**
      Arm A gains `'config.yaml'` in sorted position; arm B gains `'repo_root.txt'`. **Nothing else
      changes and nothing is reordered**, and this task's report shows both diffs as exactly one entry
      each. Every other arm that fails is a finding to report.

- [ ] **Step 6: an acceptance arm, because the acceptance suite is where the run directory's shape is
      read as a whole.** In `tests/test_acceptance.py`, beside the shipped `environment/pyproject.toml`
      assertion, add: `repo_root.txt`'s stripped text equals the project root the fixture built, and
      `config.yaml` parses to a mapping whose `experiment_type` matches the record's. Read both back;
      assert no path literal.

- [ ] **Step 7: M12 — write the config copy with `yaml.safe_dump(doc)` instead of copying bytes.**
      **Caught by** Fixture C's byte-equality assertion. **Why the two branches differ:** the dump
      loses every comment `init` wrote, so the bytes differ **while the parsed mappings still agree** —
      which is exactly why Fixture C asserts both, and why the mutation must be confirmed to fail the
      **byte** arm and **pass** the mapping arm. Report that asymmetry; a mutation that failed both
      arms would mean the fixture is not testing what it claims. Revert by editing the line back.

- [ ] **Step 8: a second mutation, because "additive" is a claim too.** Change the copy's destination
      to `(run_dir / "environment" / "config.yaml")`. **Caught by** task 13 arm A (post-edit) failing
      on the root list **and** arm B (post-edit) failing on the `environment/` list — one loses an
      entry, the other gains one. **Why the two branches differ:** the two lists move in opposite
      directions, which no single-arm pin could distinguish from a file simply not being written.
      Revert by editing the path back.

- [ ] **Step 9: run.** `uv run pytest` → **+ your new tests, and every shipped test still passing
      except the two arms you were authorized to edit.** State the delta, not an absolute.
      `uv run mypy` → still **47 source files**; `ruff format --check` → still **84 files** (this task
      adds no file to either tree).

- [ ] **Step 10: commit.** `git add -A && git commit -m "H8b task 3: run writes the config copy and
      the recorded repo root, additively"`.

---

## Task 4: `freeze.py` — the refusals, the resolution, and the credential pre-check

**Surface: a direct call. `freeze` does NOT dispatch until task 6**, so nothing built here can be
reached from the command line and a resolution bug cannot reach a real run directory through
`main`. That is the seam: everything in this task is `freeze._precheck(run_dir)`-shaped and tested by
calling it.

**Files:**
- Source: `src/publishable/freeze.py` (new)
- Test: `tests/test_freeze.py` (new)

**Interfaces:**
- Produces: `freeze.py` holding the refusal gate and the resolution, plus the module's
  `command_freeze` **signature only** (task 6 fills its probe round). Nothing exported from
  `publishable/__init__.py`.
- Consumes: `validate.load_document`, `templates.registry._claims`,
  `templates.registry.installed_template_message`, `validate.unknown_template_message`,
  `validate.declared_credential_names_for`, `cli.declared_credential_names`,
  `apparatus._probe_for`, `apparatus.replay_ledger`, `secrets.load_env`,
  `secrets.credential_values`, `secrets.missing_env`, `diagnostics.Collector`, the `EXIT_*`
  constants, `errors.ContractError`/`PublishableError`.

**Import direction.** `freeze.py` may import `cli`'s `declared_credential_names` **or** re-derive the
same set locally; it may **not** be imported by `cli.py` at module scope if that closes a cycle —
measure the direction before writing the import and say which way it went. `cli.py` importing
`freeze.command_freeze` inside `_dispatch` (a function-local import) is the escape hatch if it does,
and H8a's `artifacts → lineage` ruling is the precedent for treating an import direction as
load-bearing rather than as tidying.

**The refusal order is cost order, and it is ruled here rather than discovered.** § Exit codes'
argument for `dry-run`'s phase ordering is the precedent, verbatim: *"the cheap objection should never
be reported second, behind a metered request that was going to fail anyway."* So:

```
(a) run.yaml present                        → E-FREEZE-RUN-ENDED            exit 1
(b) config.yaml absent / not a mapping      → E-FREEZE-NO-CONFIG            exit 1
(c) environment/repo_root.txt absent/empty  → E-FREEZE-NO-CONFIG            exit 1
(d) load_env(repo_root)                     (not a gate — it is what makes (k) answerable)
(e) template resolution                     → the FOUR REUSED template codes exit 1
(f) template declares no apparatus_probe    → E-FREEZE-NO-APPARATUS         exit 1
(g) sweep.yaml absent/unreadable            → E-FREEZE-PLAN-MISSING         exit 1
(h) re-expand + cross-check (task 5)        → E-FREEZE-PLAN-MISMATCH        exit 1
(i) ledger has no run_start/pre_execution   → E-FREEZE-LEDGER-MISSING       exit 1
    a ledger line is malformed              → E-FREEZE-LEDGER-UNREADABLE    exit 1
(j) probe name vs the ledger's `probe`      → E-FREEZE-PROBE-MISMATCH       exit 1
(k) a declared credential is unset          → EXIT_EXTERNAL                 exit 5
(l) THE PROBE CALL — task 6's, not this task's
```

**Every one of (a)–(k) reports with NO probe call made and NO ledger line written**, and Fixture F4
asserts the second half of that for every arm. The letters are the gate's order; the numbered
checkboxes below are this task's work items, and the two are deliberately not the same numbering.

- [ ] **Step 1: `E-FREEZE-RUN-ENDED` first, and the docstring says why it is sharper than
      `resume`'s.** § Operation commands has `resume` refuse a directory holding a `run.yaml` because
      *"that run ended."* `freeze`'s reason is sharper: `provenance.apparatus` was assembled from the
      observations that existed when the record was written, and **the record is never modified**, so
      appending an observation afterwards would leave the ledger and the record permanently disagreeing
      about a run nobody can re-derive. **Answered by `run.yaml`'s presence, never by the lock's
      absence** — a killed run leaves no lock and no record, and those are opposite answers.

- [ ] **Step 2: `E-FREEZE-NO-CONFIG`, and it covers the pair.** Both artifacts are written by the same
      task in the same commit inside the same `RunLock` block, so a directory holding one and not the
      other is a hand-edited directory rather than a build difference — one code, one remedy (*the run
      was started by a build before these artifacts existed, or the directory was edited; it cannot be
      frozen*). **Do not mint a second code for the repo-root half**; say in the message which of the
      two was missing so a reader can act, which is what a message is for.

- [ ] **Step 3: read the repo root from the FILE, never by walking up.** `environment/repo_root.txt`
      holds one line. Strip it and use it. **Walking up from `run_dir` answers a different question**
      — which repo happens to sit above `output_dir`, and the invariant is that `output_dir` may
      never resolve inside the git repo, so that walk finds either nothing or the wrong repo. This is
      the proxy that would silently return `repo_root=None` and make every project-local template
      resolve to `None` — measured at `0a636af`, which is Decision 7's whole ground.

- [ ] **Step 4: `load_env(repo_root)` BEFORE the credential pre-check, and the docstring says why.**
      `freeze` runs in a different shell from the run that is executing, so a credential the run holds
      may simply not be exported here — but the project's `.env` is where a real project files it, and
      `command_run` and `validate_config` both call `load_env(repo_root)` before anything reads the
      environment. Without this call the pre-check reports a missing credential the `.env` supplies,
      and **Fixture F5's sibling arm would pass for the wrong reason.** Measured at `0a636af`:
      `load_env` never overrides an exported variable and returns quietly on a missing file, so the
      call is safe and idempotent. **It must sit above the credential pre-check and below the repo-root read**
      in the gate order above, since it needs the one and answers for the other.

- [ ] **Step 5: template resolution reuses FOUR shipped codes and mints NONE** (§ Corrections,
      correction 6). Measured at `0a636af`: `get_template(name, root)` returns `None` for a name
      nothing claims **and** for a name only an installed distribution claims — two different faults
      with two different remedies — and `_claims(root)` **raises** `PartialLoadError` (a
      `ContractError`) under `E-TEMPLATE-LOAD` or `E-TEMPLATE-COLLISION`. So resolve through
      `_claims(repo_root)` rather than `get_template`, exactly as `validate_config` and
      `generate_experiment` both already do, for the reason both already state: one merge, so one
      local discovery, and the claim's `provenance` is what routes `E-TEMPLATE-UNKNOWN` from
      `E-TEMPLATE-INSTALLED-UNSUPPORTED`. Report the code the raise carries, never a code chosen here.
      **Reuse `unknown_template_message` and `installed_template_message`** rather than writing a
      second literal — `E-TEMPLATE-UNKNOWN`'s own two-emit-site history is what a second uncoordinated
      wording costs.

- [ ] **Step 6: the catch breadth around `_claims`, ruled rather than inherited.** `_claims` imports
      every `templates/*.py` — **user top level, at a new call site.** `validate_config` catches
      `ContractError` only; `apparatus._probe_for`'s wrapper in `command_run` uses `except
      BaseException` with `KeyboardInterrupt` re-raised **fresh and argument-less, `from None`**.
      **`freeze` uses the second shape**, and the ground is that a `sys.exit()` at a template's module
      scope is a `SystemExit`, which `except Exception` does not see — it would end `freeze` with the
      user's own exit code and no diagnostic at all, which is the outcome `validate` is contracted
      never to produce and which a read command has no better excuse for. A non-`PublishableError`
      becomes `E-TEMPLATE-LOAD`, the code that already covers *"raises while importing."*

- [ ] **Step 7: the credential set, and it must be buildable BEFORE the template resolves.** The
      chicken-and-egg is real and shipped code already solves it: a template-load or collision fault
      means the template never resolves, and the finding just built **can itself carry a raising
      file's own exception text**, so `validate_config` reads `exc.partial_templates` and takes
      `declared_credential_names_for(doc, cls)` over each. **Reuse that route** — the same set, so it
      cannot drift from `validate`'s. On the success path the set is
      `declared_credential_names(doc, template, conditions)` from the expanded conditions (task 5),
      and until task 5 lands, from `expand(doc)` called locally. Measured at `0a636af`: both
      collectors are callable from a config, a resolved template and an expanded condition list, so
      this needs no new machinery.

- [ ] **Step 8: EVERY diagnostic goes through a fresh credential-bearing `Collector`.** Measured at
      `0a636af`: `main`'s `except PublishableError` prints `f"  error   {exc.code:<20} {exc}"` with **no
      collector in scope**. So `command_freeze` catches its own faults and returns a code; it does not
      let a `ContractError` escape to `main`, because `main` would print it un-redacted **and** at exit
      `1`, which is wrong for `E-APPARATUS-RAISED` (task 6). A **fresh** `Collector` per diagnostic
      with `.credentials` set, never a shared one — a collector already rendered would re-print every
      earlier finding and inflate the counts line, which is `command_run`'s own stated reason.
      `KeyboardInterrupt` is re-raised **fresh and argument-less, `from None`**, so Ctrl-C still stops
      the command and a `KeyboardInterrupt("…secret…")` a template or probe body constructed never
      reaches Python's own printer.

- [ ] **Step 9: `E-FREEZE-NO-APPARATUS`, `-LEDGER-MISSING`, `-LEDGER-UNREADABLE`, `-PLAN-MISSING`,
      `-PROBE-MISMATCH`.** Each row's remedy is different, which is the test for whether a split is
      warranted — H4d's precedent, where *one code that returned for five distinct faults became five
      named refusals*. Two of them earn a sentence each:
      - **`E-FREEZE-LEDGER-MISSING`**: the run has not probed yet, so there is **no baseline**, and
        probing now would pin a fact the run's own gate never adopted. Task 1 returns an empty
        `Observations` for both an absent file and a file with no qualifying line; **this code covers
        both**, because the remedy is identical.
      - **Carried forward from task 1's batch review (Major 3), not closed there and not this task's
        to skip.** `replay_ledger`'s `E-FREEZE-LEDGER-UNREADABLE` guard checks key PRESENCE only, not
        shape: a line whose `facts` value is present but not a mapping (`null`, a list) raises a bare
        `AttributeError` out of `Observations.record` rather than being refused, and a line whose
        `condition` value is present but not a `str` (an `int`, say) is accepted silently and yields
        an int-keyed baseline that reads as "never answered" — a quieter fail-open, since it lets
        `freeze` adopt a pin it should have refused to compute at all. Both are exactly the
        edited-or-truncated-file class this refusal exists for, and the § Errors row task 12 writes
        for `E-FREEZE-LEDGER-UNREADABLE` gives the cause as "the file was edited or truncated" — a
        cause this task's own gate cannot currently honour for these two shapes. Once this task wires
        `freeze`, `main` catches only `PublishableError`/`OSError`, so an `AttributeError` here becomes
        an uncaught traceback rather than a diagnostic. **Repair, under code that already exists**:
        extend `replay_ledger`'s guard to also require `isinstance(doc["facts"], Mapping)` and
        `isinstance(doc["condition"], str)` before calling `Observations.record`, reported as the same
        one code.
      - **`E-FREEZE-PROBE-MISMATCH`** is the one that is easy to miss. `templates/**` is hashed but
        freely **editable while a run executes**, and `freeze` resolves the template **now**. Probing a
        different apparatus than the run measures through, and then reporting `unchanged`, is worse
        than not probing — so the probe name `freeze` resolved is checked against the `probe` field the
        ledger records.
      - **`apparatus_facts` is deliberately NOT cross-checked the way the probe name is**, and the
        asymmetry has a reason rather than being an oversight: the ledger records the facts a probe
        **returned**, never the facts a template **declared**, so there is nothing on disk to compare a
        declaration against. The consequence is real and accepted: a fact **added** to
        `apparatus_facts` mid-run makes `freeze` report `E-APPARATUS-FACT-MISSING` against a probe
        behaving exactly as the run expects. That is the correct report of a real edit. **Write this
        into the docstring** so the next reader does not file it as a gap.

- [ ] **Step 10: the credential pre-check, LAST before the probe and at exit `5`.** `secrets.missing_env`
      is the shipped checker. A missing declared credential is exit **`5`** — *"a missing credential"*
      is named in § Exit codes' `5` row — **with no probe call made and no ledger line written**,
      because without the pre-check that fault arrives as `E-APPARATUS-RAISED` at exit `5` **after** a
      metered call — gate position (k), immediately before the probe. Same code, one wasted call: the pre-check buys the call, not the number.

- [ ] **Step 11: Fixture F4, eleven arms, asserted by CODE and not by message text.** The seven
      `E-FREEZE-*` arms plus the four reused-template arms, each differing from Fixture F1 in exactly
      one way. **Every arm also asserts `apparatus/probes.jsonl` gained no line**, which is what makes
      each a refusal rather than a report after the fact. **Attribute each refusal before counting
      it**: nineteen adversary configs over one roster on a preceding slice made every refusal
      roster-incidental, and *a refusal that happens to fire must be attributed before it is counted*.
      Concretely, assert the reported code set is **exactly** the one expected, not that the expected
      code is present.

- [ ] **Step 12: Fixture F5, both arms, and its credential is on a PARAMETER VALUE.** Arm one: a probe
      that reads a declared `requires_env` variable and raises carrying its value — assert the
      credential's **absence** from stderr **and** `E-APPARATUS-RAISED`'s presence at exit **`5`**.
      **The pair, because asserting only the absence passes identically if nothing ran.** Arm two: the
      variable unset entirely, a probe that writes a flag file, asserting the flag's **absence** and
      exit `5`. (Arm one needs task 6's probe round; **write both arms here against the refusal gate's
      credential set and re-run arm one as an end-to-end assertion in task 6** — say in the report
      which half landed where.)

- [ ] **Step 13: M16 — narrow the credential set to the template's `required_env` alone.** **Caught
      by** Fixture F5, whose credential is declared on a **parameter value's** `requires_env`. **Why
      the two branches differ:** before, the value is redacted from stderr; after, it appears verbatim,
      and the assertion is on stderr's text. Revert by editing the collector back.

- [ ] **Step 14: M14 — resolve the template with `repo_root=None`.** **Caught by** Fixture F1, whose
      template is **project-local**. **Why the two branches differ:** measured at `0a636af`,
      `_claims(None)` skips `discover_local` entirely, so the name resolves to nothing and `freeze`
      reports `E-TEMPLATE-UNKNOWN` instead of proceeding — a different code at the same exit, which is
      why the assertion must be on the **code set** and not on the exit alone.

- [ ] **Step 15: M15 — drop the probe-name cross-check.** **Caught by** Fixture F4's
      `E-FREEZE-PROBE-MISMATCH` arm, whose template declares a **second registered** probe name.
      **Why the two branches differ:** before, the refusal and an unchanged ledger; after, the gate
      passes and `freeze` goes on to probe a different apparatus. The second name must be genuinely
      registered by the `installed` fixture, or the arm fires as `E-PROBE-UNKNOWN` **for the wrong
      reason** — the shape that cost a preceding slice a round.

- [ ] **Step 16: run.** `uv run pytest` → **+ your new tests**. `uv run mypy` → **48 source files**
      (`freeze.py`). `ruff format --check` → **86 files** (`freeze.py`, `tests/test_freeze.py`).
      Both moves are this module and its test file and nothing else.

- [ ] **Step 17: commit.**

---

## Task 5: `freeze`'s condition set — re-expanded, then cross-checked against the recorded plan

**Surface: a direct call.** Decision 8.

**Files:**
- Source: `src/publishable/freeze.py`
- Test: `tests/test_freeze.py`

**Interfaces:**
- Consumes: `sweep.expand`, `runner.resolve_condition_cfg`, `yaml.safe_load` over `sweep.yaml`.
- Produces: the `(conditions, cfgs)` pair `Observer.__init__` needs. Measured at `0a636af`:
  `Observer.__init__` takes `probe_name`, `probe`, `declared_facts`, `conditions`, `cfgs`, `run_dir`,
  `credentials`; `cfgs` is keyed by `condition.index`, and `resolve_condition_cfg(doc, condition)`
  takes the **whole `Condition`** — its `selectors`, not just its `values`.

**Why re-expansion is safe, and why it still needs a cross-check.** Measured at `0a636af`:
`expand(config)` takes the config and nothing else — no roster, no `io`, no resolver, no input read —
so `freeze` reaches the apparatus and nothing else off the machine. Re-derivation is nonetheless a
re-derivation, and this repo's rule for that is *lineage is recorded, not resolved*: the recorded plan
is what the run is actually executing, so the cheap cross-check is what makes the re-derivation safe.

- [ ] **Step 1: `expand(doc)` on the copied config, then one `cfg` per condition.** `cfgs` is
      `{c.index: resolve_condition_cfg(doc, c) for c in conditions}`. **Do not build `cfgs[-1]`** —
      `command_run` builds a wide cfg for `run`/`summary` scope and `Observer.observe_round`'s own
      docstring says `self.cfgs[-1]` is never read there; a wide cfg here would be an entry nothing
      reads.

- [ ] **Step 2: the cross-check compares FOUR fields per condition, not two** (§ Corrections,
      correction 8). Measured at `0a636af`: each `sweep.yaml` condition entry holds exactly
      `{index, label, values, is_baseline}` — task 13 arm E pins that — and **all four are
      comparable**. The design's Decision 8 names `(index, label)`; **`values` is the field that
      determines the cfg a probe is called under**, and under `ablate` or a declared `baseline` a
      label is a declared name that can hold still while `values` moves. So compare the full
      four-tuple per condition, in recorded order, and refuse any disagreement as
      `E-FREEZE-PLAN-MISMATCH` naming which condition and which field.

- [ ] **Step 3: `design_digest` is deliberately NOT part of the cross-check, and say why.** It covers
      `data.units` and `sweep.groups` — **neither of which affects the cfg a probe is called under** —
      so checking it would guard a property `freeze` does not depend on and would widen a refusal
      Decision 8 ruled narrowly. **The residual is real and belongs in the report, not in a check:**
      a plain `parameters` edit in the config copy changes every cfg and is **invisible to every
      artifact on disk mid-run**, because no `parameters_hash` is recorded until `run.yaml` is written.
      Name it as unmeasurable rather than half-covering it. **Do not file it as a defect** — it is a
      property of `run.yaml` being terminal, which § What `status` means already states.

- [ ] **Step 4: `E-FREEZE-PLAN-MISSING` covers an absent AND an unreadable `sweep.yaml`** — one code,
      one remedy (*the run died before its plan was written, or the directory was edited*). Task 4's
      gate already sites it; this task fills the reading.

- [ ] **Step 5: refuse a condition selector, in writing.** Naming one condition would be a selector
      flag, which `design-principles.md` § Everything is in the file forbids, and a mode with its own
      command name is not warranted for saving one metered call. **One probe per condition**, because
      the gate is per condition — § The apparatus core can only observe: *"a deployment is compared
      against its own first answered observation, never against another condition's"* — and the
      run-start round already makes one call per resolved condition, so freezing one condition would
      leave the rest uncertified **while looking like a full check**.

- [ ] **Step 6: M13 — skip the cross-check entirely.** **Caught by** Fixture F4's
      `E-FREEZE-PLAN-MISMATCH` arm, whose config copy's `sweep` was edited so re-expansion yields a
      different label set. **Why the two branches differ:** before, the refusal and an unchanged
      ledger; after, `freeze` builds a condition set the run is not running and (at task 6) probes it.

- [ ] **Step 7: a second mutation, for the `values` half specifically.** Narrow the comparison back to
      `(index, label)`. **Caught by** a second F4-shaped arm whose config copy changes a **`baseline`**
      value while the labels hold still. **Why the two branches differ:** the four-tuple sees a moved
      `values` mapping; the two-tuple does not. **Check before trusting it that the two branches CAN
      differ** — build the fixture, print both condition lists, and confirm the labels are genuinely
      equal across the edit. If they are not, the fixture does not discriminate and the arm must be
      rebuilt, not reworded.

- [ ] **Step 8: run and commit.** `mypy` → still **48 source files**; `ruff format --check` → still
      **86 files**.

---

## Task 6: `freeze`'s probe round, its verdicts, its exit codes, and its CLI arm

**Surface: the `freeze` command, end to end through `main(["freeze", …])`.** This task completes the
command, so it is also the task that gives it a dispatch arm and flips its `Status` cell — **arm,
constant key and document cell in one commit** (§ Corrections, correction 1).

**Files:**
- Source: `src/publishable/freeze.py`, `src/publishable/cli.py`, `src/publishable/artifacts.py` (one
  docstring), `docs/reference.md`
- Test: `tests/test_freeze.py`, `tests/test_cli.py`

**Interfaces:**
- Consumes: `apparatus.Observer` **or** its three pieces directly (see step 1),
  `apparatus.replay_ledger`, `apparatus.check_changed`, `apparatus.PHASE_FREEZE`,
  `apparatus.APPARATUS_CODES`, `uv_support.uv_lock_info`.
- Produces: a complete `command_freeze(run_dir: Path) -> int`, and `"freeze"` in
  `cli.OPERATION_COMMANDS`.

- [ ] **Step 1: the probe round reuses the SHIPPED order and does not restate it.** Per condition:
      `check_facts` → `append_observation` → `Observations.record` → `check_changed`. **That order is
      H7d Part A's ruling and is inherited rather than re-decided**: `check_facts` runs first so a
      credential-carrying fact never reaches disk, and `append_observation` runs before the gate so
      the moving observation is on disk before anything can report it. Decide and **state in the
      docstring** whether you reuse `Observer` (constructing it with `run_dir`, `cfgs`, `conditions`,
      `credentials` and the resolved probe, then calling `observe_round(phase=PHASE_FREEZE,
      condition_index=None)`) or call the four functions directly. **Ruled: reuse `Observer`, and give it an
      optional `observations=None` keyword** on `execute_plan`'s own defaulted-keyword precedent for
      `observer=`/`stop=` — measured at `0a636af`, `Observer.__init__` builds
      `self.observations = Observations()` with no parameter, so the alternative is assigning
      `observer.observations = replay_ledger(run_dir)` **from outside the class**, which a reviewer will
      flag and a later slice will "tidy" back. The keyword keeps Decision 9's structural argument intact
      (the order is the gate's code, so it cannot drift) at a smaller diff than it looks: one parameter,
      one `or Observations()`, and no shipped caller changes.
      **The hazard this closes, named because it is the single most likely way this task ships a
      `freeze` that is silently useless:** a fresh `Observations` means every incoming fact establishes
      its own first-answered entry and then compares **against itself**, so `freeze` reports
      `unchanged` on every run and passes its own happy-path test. **Write Fixture F2 BEFORE choosing
      the seam**, so the choice is validated by a failing-then-passing test rather than justified by
      this paragraph. If the keyword cannot be made to work, the direct-call route is the fallback and
      the report says so — with the docstring naming `Observer._observe_one` as the order it must
      match.

- [ ] **Step 2: `phase=PHASE_FREEZE`, one line per condition, and NOTHING else is written.** Assert in
      Fixture F1: exactly `len(conditions)` new lines, each with `phase: "freeze"`; `lock` **present
      and byte-identical**; `run.yaml` still absent; `sweep.yaml`, `environment/`, `allocation.json`,
      `executions.jsonl` and every step directory byte-identical (compare a recursive
      `{relative path: bytes}` mapping taken before and after, excluding `apparatus/probes.jsonl` —
      that exclusion is the one thing `freeze` is allowed to change, and naming it explicitly is what
      makes the rest of the assertion mean something).

- [ ] **Step 3: the verdicts and their exit codes, and the asymmetry with `diff` is deliberate.**

| What `freeze` found | Printed as | Exit |
|---|---|---|
| Every fact agrees with its first answered observation | the observation, per condition | `0` |
| A fact moved | `E-APPARATUS-CHANGED` — the **shipped** code — with condition, fact and both values | `1` |
| The probe raised, or `sys.exit()`ed | the shipped `E-APPARATUS-RAISED` | `5` |
| The probe returned a non-`Apparatus`, omitted a declared key, returned a credential, or returned an unencodable value | the shipped `E-APPARATUS-RETURN` / `-FACT-MISSING` / `-FACT-CREDENTIAL` / `-FACT-TYPE` | `1` |
| A declared fact came back `null` | the shipped `W-APPARATUS-UNANSWERED` | unchanged by a warning |
| The repo's `uv.lock` no longer hashes to `environment/uv.lock` | **`W-FREEZE-LOCK-MOVED`** | unchanged by a warning |

      **`E-APPARATUS-CHANGED` is reused, not re-minted** — § Errors carries one row per code, and this
      is the same fault the gate reports; a reader who greps that code should find both the run that
      stopped and the `freeze` that saw it coming. **Exit `1` for a moved fact**, because § Operation
      commands says `freeze` *"reports a moved apparatus as a failure"* and § Exit codes' `1` row
      already covers *"a changed apparatus fact caught before the first execution ran"*. **The
      five-code split is inherited, not re-decided**: measured at `0a636af`, `command_run`'s shipped
      containment returns `EXIT_EXTERNAL` for `E-APPARATUS-RAISED` alone and `EXIT_WRONG` for the other
      four of `APPARATUS_CODES`, on H7d Part B's Decision 6 — **Route off `APPARATUS_CODES` rather than
      hard-coding a code list here** — but route it the way `command_run` does, which is a SPLIT and not
      a single answer: `EXIT_EXTERNAL` for `E-APPARATUS-RAISED` alone, and `EXIT_WRONG` for
      `APPARATUS_CODES - {"E-APPARATUS-RAISED"}`. Reading the frozenset and giving all five members one
      code would be the literal reading of "route off it" and the wrong one. This way the same fault
      gets the same number from a read command and from the command that executes.

- [ ] **Step 4: `W-FREEZE-LOCK-MOVED` is a warning and never changes the code.** Nothing mid-run
      re-checks the lockfile, so an exit `1` here would tell a scheduler to act on something that will
      not stop the run — and § Exit codes is explicit that *"a warning never changes the code"*.
      Reporting it at all is required: § Operation commands says *"a moved lockfile is reported too and
      changes nothing on disk."* Compute it with the shipped `uv_lock_info(repo_root)` against
      `environment/uv.lock`'s bytes; measured at `0a636af`, that helper is a plain content hash with
      **no `--locked` drift check**, so this compares captured bytes to current bytes and claims
      nothing more. **Absent on either side is not a move** — a project with no lockfile then and none
      now has nothing to warn about, and a warning there would fire on every scaffolded project.

- [ ] **Step 5: `EXIT_EXTERNAL` gains its second reader, and `CLAUDE.md`'s clause about it is now
      doubly false.** H7d Part B gave `5` its first reader; an unreachable apparatus at `freeze` is the
      same class — *"the class you retry"*. **Do not edit `CLAUDE.md` here** — task 12 owns that
      deletion, and the reason it is a deletion rather than a rewrite is in § Corrections, correction 4.

- [ ] **Step 6: the CLI arm, and `"freeze"` joins `OPERATION_COMMANDS`.** Measured at `0a636af`, that
      arm enforces *exactly one path and no flags* and rejects a leading `-`; its body is a ternary over
      `validate`/`run`. **Ruled: add `"freeze"` to the set and replace the ternary with a mapping
      lookup built inside `_dispatch`.** Grounds: one enforcer of the one-path rule rather than two
      (two enforcers of one rule is the drift shape `_nest_repeat`'s own docstring already argues
      against), and a **local** mapping rather than a module-level one because `command_validate` and
      `command_run` are defined below the constant and a module-level dict of callables would be a
      forward reference. **Do not turn `OPERATION_COMMANDS` into a callable mapping** — that is a
      second change with no second benefit.

- [ ] **Step 7: the flip, in this commit.** Remove `"freeze"` from `cli.NOT_BUILT_COMMANDS` and change
      its `Status` cell in `reference.md` § Operation commands from `NOT BUILT` to `built`. **They must
      move together**: measured at `0a636af`, `_dispatch` checks the built branches **before** the
      `NOT_BUILT_COMMANDS` lookup, and `test_reference_cli_tables_are_parsed_at_all` asserts **set
      equality** between the table's `NOT BUILT` rows and that constant's keys, while
      `test_reference_cli_tables_match_what_the_cli_does` probes each row through `main` with two junk
      positionals. **Check both directions after the flip:** `main(["freeze", "_probe_a", "_probe_b"])`
      is two arguments to a one-path command, so it must print `` `freeze` takes exactly one path and
      no flags `` at exit `2` and must contain **neither** `unknown command` **nor** `is specified but
      not built`; and the Command table must still hold at least one `NOT BUILT` row, or that test's
      `statuses == {"built", "NOT BUILT"}` control goes vacuous. Measured at `0a636af`: `demo`,
      `dry-run`, `draft`, `resume`, `report`, `reproduce`, `docs`, `list-templates`, `study new` and
      `study add` remain, so it does not.

- [ ] **Step 8: the two sentences that quote `OPERATION_COMMANDS`'s value go false — DELETE the
      literal, do not rewrite it** (§ Corrections, correction 3). Measured at `0a636af`, the literal
      `OPERATION_COMMANDS = {"validate", "run"}` is quoted in
      `artifacts.build_allocation_document`'s docstring and in `reference.md` § Resuming. **Both
      sentences' content survives** — there is still no `resume` command, and `allocation.json`'s
      "read rather than re-drawn" rule still has no reader — so remove the quoted set from each and
      leave the claim. **A rewrite invents; a deletion cannot.** Both sites are in this task's diff
      because this task changes the constant.

- [ ] **Step 9: § Operation commands' `freeze` row and the surrounding prose.** The row's `Does` cell
      already describes the command; check it against what shipped and **change the document if they
      disagree.** The paragraph below it (*"`freeze` reports a moved apparatus; it doesn't decide"*)
      is normative and correct — verify, do not embellish. **Do not add a sentence about `resume`
      reading the two new artifacts**; that is H9's.

- [ ] **Step 10: Fixtures F1, F2, F3, and F5's arm one, end to end through `main`.** F3 is the one
      surface needing a second process and **may not be downgraded to a constructed fixture.** Give it
      a timeout, a sentinel-file handshake, and one assertion: `freeze` against a directory whose lock
      is **genuinely held** by a running process exits `0` and appends its lines. Nothing else depends
      on it, so it can be `xfail`-free and self-contained; if it cannot be made to pass, that is a
      finding about `freeze`, not a reason to delete it.

- [ ] **Step 11: M8's exit-code half, from task 1.** Re-run task 1's `null`-everywhere / answered-at-
      first-`freeze` / differently-answered-at-second-`freeze` fixture **through `main`** and assert
      **two `0`s** under the shipped filter. Then apply M8 (admit `phase == "freeze"` to
      `replay_ledger`) and assert the second `freeze` becomes exit `1` with `E-APPARATUS-CHANGED`.
      **Two different exit codes** — this is the half task 1 could not assert.

- [ ] **Step 12: M10 — have `freeze` take the run's lock** (`with RunLock(run_dir):` around the probe
      round). **Caught by** Fixture F1's byte-identical `lock` assertion **and** Fixture F3. **Why the
      two branches differ:** measured at `0a636af`, `RunLock.__enter__` raises `E-RUN-LOCKED` on an
      existing lock file and `__exit__` **unlinks** it — so a lock-taking `freeze` either refuses F1
      outright or, on a directory with no lock, writes and then deletes one. F1's hand-written lock
      makes the first branch the observed one; F3 makes it the real one.

- [ ] **Step 13: M11 — let `freeze` proceed on a directory holding `run.yaml`.** **Caught by** Fixture
      F4's `E-FREEZE-RUN-ENDED` arm, which asserts the code **and no new ledger line**. **Why the two
      branches differ:** before, a refusal and an unchanged ledger; after, exit `0` and one appended
      line per condition. **The ledger assertion is the discriminating half** — a code assertion alone
      would pass a build that reported the code after appending.

- [ ] **Step 14: run.** `uv run pytest` → **+ your new tests**, and **exactly two shipped tests may
      change**: the two CLI-table tests, and only in the `freeze` row's direction. `uv run mypy` →
      **48 source files**; `ruff format --check` → **86 files**.

- [ ] **Step 15: commit.** `git add -A && git commit -m "H8b task 6: freeze probes, reports and
      dispatches"`.

---

## Task 7: `covered_config` extracted, and the parameter delta walk over it

**Surface: a direct call.** Decision 3. Nothing dispatches in this task.

**Files:**
- Source: `src/publishable/hashes.py`, `src/publishable/diff.py` (new — the walk only; task 8 builds
  the command)
- Test: `tests/test_hashes.py`, `tests/test_diff.py` (new)

**Interfaces:**
- Produces: `hashes.covered_config(config: dict[str, Any]) -> dict[str, Any]`, and `diff.py`'s delta
  walk and its rendering of a delta line.
- Consumes: nothing new. `parameters_hash` is **rewritten to hash `covered_config`'s return**, not
  reimplemented.

**Why one function rather than two lists.** A row's verdict and the delta lines under it must agree
about coverage, or `diff` prints `parameters_hash identical` with delta lines beneath it, or `DIFFERS`
with none. One function is how they do not drift — the argument H8a's `read_run_record` already made
for importing `SCHEMA_VERSION` rather than restating it. **And the coverage is wider than the
`parameters` block on purpose:** § Three hashes states both halves of this, that *"a `metadata`-only
edit is invisible to `diff`"* and that `diff` *"prints a raised `max_failed_fraction` as the parameter
delta it is"* — `limits`, not `parameters`.

- [ ] **Step 1: extract, do not reimplement.** Measured at `0a636af`, `parameters_hash`'s projection
      is: every top-level key except `metadata`, with `data` narrowed to everything but `input_dir` and
      `output_dir`, and only when `data` is a `dict`. Move exactly that into `covered_config` and make
      `parameters_hash` call it. **Task 13 arm G is the pin**: `parameters_hash(run.yaml['config']) ==
      run.yaml['parameters_hash']` over a real run, plus the metadata-equal and limits-differ sub-arms.
      If arm G fails, the extraction changed what is hashed — a finding, not an assertion to edit.

- [ ] **Step 2: the docstring may NOT claim normalization, and may not implement it** (§ Corrections,
      correction 5). § Three hashes says *"Values are normalized to what `init` would have materialized
      before hashing"*, and `spec-defects.md` carries an **OPEN** entry that `parameters_hash` does not,
      owner **H6**. Cite that filing by its own title rather than restating its content, and implement
      nothing: normalizing here would move every hash in the suite from a slice about `diff`. **Do not
      strike the filing** and do not add a fixture arm for it.

- [ ] **Step 3: the delta walk flattens `covered_config` on both sides to dotted leaf paths**, and a
      leaf is anything that is not a `dict` — a list is a **leaf**, not a subtree, because a config
      list (`statistics.contrasts`, `metadata.authors`, `sweep.grid`'s values) is one declaration and
      splitting it by index would print a delta per element for a reordering. Render three shapes:

```
parameters_hash    DIFFERS
  parameters.analysis.method       pearson → spearman
  limits.max_failed_fraction       0.2 → 0.4
  statistics.contrasts             (absent) → [{name: dose_high_vs_low, ...}]
```

      A leaf present on one side only renders `(absent) → <value>` or `<value> → (absent)`. A leaf
      whose value is a list or mapping renders as **one line of YAML flow style, untruncated** — a
      config value is small, and a truncated delta is a delta a reader cannot act on. **The dotted path
      is rooted at the config, so it carries its top-level block**: the worked outputs in `README.md`
      and `docs/design-principles.md` both write `parameters.analysis.min_samples`, with the
      `parameters.` prefix — measured, not assumed. **Sort the lines by path** so two runs of `diff`
      over the same pair print identically; dict order is an implementation fact.

- [ ] **Step 4: Fixture M, the PAIR, and only the pair discriminates.** Arm one: two records differing
      only in `metadata.description` → `parameters_hash identical` with **zero** delta lines. Arm two:
      two differing only in `limits.max_failed_fraction` → `DIFFERS` with **exactly one** line naming
      that path and both values. Read both values back from the two configs.

- [ ] **Step 5: M4 — narrow the delta walk to `config["parameters"]`.** **Caught by** Fixture M's
      **second** arm. **Why the two branches differ:** before, one delta line; after, `DIFFERS` with
      **zero** lines — and **Fixture M's first arm still passes**, which is why only the pair
      discriminates and why a single-arm fixture here would be exactly the *"assertion implied by
      another"* shape. Report that the first arm passed under the mutation; a mutation that failed both
      arms would mean arm one is not testing coverage.

- [ ] **Step 6: a second mutation, for the leaf rule.** Treat a list as a subtree (recurse into it by
      index). **Caught by** a third Fixture M arm: two records whose `metadata.authors` — no, whose
      **`sweep.grid`** axis list is **reordered** with the same members. **Why the two branches differ:**
      the leaf rule prints one line for the whole list; the index rule prints one per moved position.
      **Check the two branches can differ before trusting it**: `parameters_hash` over a reordered list
      **does** move (canonical JSON preserves list order), so the row is `DIFFERS` under both branches
      and the discriminator is the **line count**, not the verdict. Assert the line count.

- [ ] **Step 7: run.** `uv run pytest` → **+ your new tests, and no shipped `test_hashes.py` test may
      change** — `parameters_hash`'s behaviour is unchanged and its shipped tests are the second pin on
      that. `uv run mypy` → still **48 source files** at this point if task 4 landed `freeze.py`; the
      new `diff.py` takes it to **49**. `ruff format --check` → **88 files** (`diff.py`,
      `tests/test_diff.py`).

- [ ] **Step 8: commit.**

---

## Task 8: `diff.py` — form detection, the per-side header, the five rows, the three verdicts

**Surface: a direct call on `diff.command_diff(a, b) -> int`. `diff` does NOT dispatch until task
11**, so nothing built here can print a four-row comparison over a pair whose apparatus moved — which
is the reason the arm waits (Decision 1's own cost-if-wrong).

**Files:**
- Source: `src/publishable/diff.py`
- Test: `tests/test_diff.py`

**Interfaces:**
- Produces: `command_diff(a: Path, b: Path) -> int` and the row renderer.
- Consumes: `lineage.read_run_record`, `validate.load_document`, `hashes.parameters_hash`,
  `hashes.covered_config`, task 7's delta walk.

- [ ] **Step 1: form detection by SHAPE, before any parsing.** A **directory**, or a file **named
      `run.yaml`**, is a run record, read through `read_run_record` on the **run directory** — measured
      at `0a636af`, that function is directory-keyed and appends `run.yaml` itself, so a `run.yaml`
      path is dispatched by taking its parent. **Any other file is a config.** Grounds: shape-based
      dispatch means the error message can name the form it assumed rather than guessing from content,
      and **accepting a directory is not a convenience** — `<output_dir>/latest` is a directory, and
      `diff <output>/latest <output>/run_2026-…` is the invocation a reader actually types.
      **Never decide the form by whether a record loads**; that is content, and it is the proxy this
      step exists to forbid.

- [ ] **Step 2: the refusals, and three of them are H8a's reused.** A path that is not a readable
      record or config: `E-IO-FAILED` for a missing path — measured at `0a636af`,
      `main(["validate", "/nope/nope.yaml"])` returns **`1`** through `main`'s own `except OSError`,
      **not `2`**, though § Exit codes lists "unreadable path" under `2`; **`diff` follows the shipped
      precedent** (Decision 4) and the document is not changed for it. `E-UPSTREAM-RECORD-MISSING` /
      `-UNREADABLE` / `-VERSION` for an unreadable **record**, reused from H8a and minting nothing —
      **and each of those three § Errors rows gains `diff` as an emit site in task 12.**
      `E-DIFF-CONFIG-UNREADABLE` for a config that does not parse to a mapping: the one new `E-DIFF-*`
      code, and it is new because `E-CONFIG-PARSE` is a `validate` finding at a config path and this is
      a command refusing an operand.

- [ ] **Step 3: the per-side header, one line per side.** `A` and `B`, the form, the identity, and —
      for a run record — its `status`, plus the word `draft` when `draft: true`:

```
A  run record  run_2026-08-06T14-02-11Z_8e21ab3   completed
B  run record  run_2026-08-07T09-14-03Z_8e21ab3   completed  draft
```

      `draft: true` earns the word `draft`, which is what § Draft runs requires (*"`report` refuses to
      render one as a final result, and `diff` labels it"*). `status` is printed for the same reason
      `study add` of a `partial` is *"visible as what it is"*. **A config side prints its form and the
      path AS GIVEN, and no status word** — a config has none, and inventing one would be a claim
      (§ Corrections, correction 9). **Do not print a resolved or absolute path**; a path is a fact
      about one machine, and the reader typed the one they typed.

- [ ] **Step 4: the five rows, in this order, with these labels.** The set, the order and the labels
      are not invented here: all three worked outputs — `README.md` § The loop you'll actually live in,
      `design-principles.md` § Same code, different parameters, and `reference.md` § The apparatus core
      can only observe — agree on them.

| Row label | Compares | Source in each record |
|---|---|---|
| `code_hash` | the identity claim over `src/**` + `templates/**` | top-level `code_hash` |
| `input_manifest` | the content hash over the input tree | `provenance.input_manifest_hash` |
| `uv.lock` | the environment fingerprint | `provenance.environment.uv_lock_hash` |
| `apparatus` | the apparatus fingerprint — **task 9** | `provenance.apparatus.hash` |
| `parameters_hash` | the declaration identity claim | top-level `parameters_hash` |

      **Pin the labels against the DOCUMENTS' text, not against your own constant** — `input_manifest`
      rather than `input_manifest_hash`, and `uv.lock` rather than `uv_lock_hash`. A test asserting a
      label against the same literal the code emits compares a literal to itself; the shipped
      `_status_tables`/`_interval_method_names` helpers in `tests/test_cli.py` are the in-repo shape
      for parsing a document and asserting against what it says.

- [ ] **Step 5: the three verdicts.**
      - **`identical`**, followed by the digest truncated to `sha256:` plus four hex characters plus
        `…` — the width all three worked outputs show. **Use `…`, one character, not `...`** —
        `README.md` already writes it and § Documentation conventions prefers it; task 12 fixes the two
        documents that still use ASCII.
      - **`DIFFERS`**, followed by its detail lines. `parameters_hash`'s are task 7's deltas and
        `apparatus`'s are task 9's per-fact lines. **The other three rows have no detail beyond the two
        digests, so a `DIFFERS` there prints `8e21… → 4c07…` on the following line** — an addition the
        worked outputs are silent about, made because a bare `DIFFERS` gives a reader nothing to cite.
      - **`not captured`**, when the figure is `null` on **either** side. Measured at `0a636af`: a
        scaffolded project with no lockfile records `uv_lock_hash: None`, so two such runs would
        otherwise print `uv.lock  identical  sha256:None…` — **a match over a fact neither run holds,
        and the single most dangerous output this command can produce.** `not captured` is `study add`'s
        own vocabulary for *never captured* as against *redacted*, reused rather than minted.

- [ ] **Step 6: Fixtures R, R2 and L.** R and R2 are the documented payoff and give `uv.lock`'s
      `not captured` arm for free (measured). **L is what pins the row's other two arms** — without it,
      `identical` and `DIFFERS` on that row ship unpinned, because every scaffolded run takes the
      `not captured` branch. Assert every digest by reading it back from the record or recomputing it;
      **no hash literal anywhere.**

- [ ] **Step 7: M1 — print `identical` instead of `not captured` when a hash is `null`.** **Caught by**
      Fixture R2's `uv.lock` row assertion, which asserts the **literal string** `not captured`. **Why
      the two branches differ:** measured — `uv_lock_hash` **is** `None` on a scaffolded run, so the
      branch is entered by the default fixture and this mutation is not blind. Then apply the
      one-sided variant (`null` on one side only, from Fixture L's non-null run against Fixture R's
      null one) and confirm it too reports `not captured` rather than `DIFFERS`: a figure one run holds
      and the other does not is a pin you don't have, not a pin that moved.

- [ ] **Step 8: a row-order mutation, because the rows in a fixed order are a claim.** Reverse the row
      order. **Caught by** an assertion on the emitted **sequence of labels**, not on membership.
      **Why the two branches differ:** four positions at this task — but note *two elements only ever
      distinguish two answers*, so assert the whole ordered list rather than one adjacency.
      **This assertion is a pin with ONE authorized editor, and its docstring says so**, on task 13
      arms A and B's own mechanism: at this task the emitted list is
      `['code_hash', 'input_manifest', 'uv.lock', 'parameters_hash']` — **four labels, because the
      apparatus row does not exist yet** — and **task 9 is the only task permitted to edit it**, to
      `['code_hash', 'input_manifest', 'uv.lock', 'apparatus', 'parameters_hash']`, with nothing else
      reordered and task 9's report showing that one-label diff. Without the clause, task 9 inserting a
      label into a passing ordered-list assertion is indistinguishable in the record from weakening a
      pin to pass.

- [ ] **Step 9: run and commit.** `uv run mypy` → **49 source files**; `ruff format --check` → **88
      files**. Both moves are `diff.py` and `tests/test_diff.py`.

---

## Task 9: `diff`'s apparatus row and its per-fact lines

**Surface: a direct call on `command_diff`.** Decision 2.

**Files:**
- Source: `src/publishable/diff.py`
- Test: `tests/test_diff.py`
- Document: `docs/reference.md` § The apparatus core can only observe's fenced `diff` output

**Interfaces:**
- Consumes: `provenance.apparatus.hash` for the verdict, `provenance.apparatus.facts` for the detail.

- [ ] **Step 1: the VERDICT compares `.hash`; the DETAIL LINES come from `.facts`.** The digest is what
      H7d Part A assembles over the resolved condition → facts mapping. **Comparing the `facts`
      mappings directly for the verdict would let the row disagree with `provenance.apparatus.hash`,
      which is the figure `report study.yaml` cross-checks in H8c — two comparisons of one fact, able to
      disagree.** Measured at `0a636af`: `apparatus_hash` canonicalizes with `sort_keys=True`, so it is
      invariant to a key reordering the mapping comparison is not.

- [ ] **Step 2: every detail line is qualified by the CONDITION KEY, with no collapsing.**

```
apparatus          DIFFERS
  00_baseline.calibration_id     CAL-2026-07-19 → CAL-2026-08-02
  01_dose=high.calibration_id    CAL-2026-07-19 → CAL-2026-08-02
```

      Facts are per condition *"since the apparatus may legitimately differ across a sweep"*, so a
      per-fact line that drops the condition is reporting a mapping's value without its key — and it
      makes a one-condition drift indistinguishable from a whole-run drift, which is the difference
      between a salvageable run and none. **Collapsing identical moves onto one unqualified line is
      refused**: it is a branch nothing in the documents asks for, it needs two fixtures before either
      arm is pinned, and a collapsed line cannot say whether *every* condition moved or only the ones
      it printed. **Sort the lines by `(condition, fact)`** so two runs print identically.

- [ ] **Step 3: the three sub-rulings, none of which the documents answer.**
      - **The row appears whenever EITHER record carries a non-null `provenance.apparatus`**, and prints
        `identical` with its digest when the two hashes match. It is omitted **only** when both are
        `null` — the one case `design-principles.md` documents (*"No apparatus row, because template
        `generic` declares no probe"*), and the reason `README.md`'s and `design-principles.md`'s worked
        outputs show four rows while `reference.md`'s shows five.
      - **One side with an apparatus and one without is `DIFFERS`**, with a detail line naming which
        side recorded none. Two runs are not comparable on a pin only one of them has, and **silence
        would read as agreement.**
      - **A condition key present in one record and not the other** gets a detail line saying so rather
        than being skipped. When the sweep itself changed, `parameters_hash` will also be `DIFFERS` and
        the deltas say why — but this row must not imply the per-condition mappings lined up.

- [ ] **Step 4: a CONFIG side makes this row `not comparable`, and that rule wins over step 3's**
      (§ Corrections, correction 10). Task 10 builds the `not comparable` vocabulary; state the
      precedence here so neither task discovers it: a config records no apparatus **and a probe is not
      run at `diff`**, so the row prints `not comparable` regardless of what the other side holds —
      including when the other side is `null`, where step 3 would have omitted it. Grounds: the
      omission rule is about two records that agree there is nothing to compare; a config side is about
      a figure that **cannot** be obtained here.

- [ ] **Step 5: the document changes first.** § The apparatus core can only observe's fenced `diff`
      output shows a **bare** `calibration_id` and **must gain its condition key**, because the code is
      about to emit one. Edit the fence to match what ships, character for character in the verdict
      words and the truncation, and **change its ASCII `...` to `…`** in the same edit — those two
      changes are the same sentence being made true. Then sweep the four documents **by name** for the
      old bare-fact shape.

- [ ] **Step 6: Fixture A1 — two conditions moving.** Assert **two** detail lines, each containing its
      own condition key, each carrying that condition's own old and new values **read from the two
      records' `provenance.apparatus.facts`.**

- [ ] **Step 7: Fixture A2 — the identical arm and the one-sided arm.** The identical arm's discriminator
      is that **one record's `facts` mapping is re-serialized in a different key order** before the
      comparison. The one-sided arm is a Fixture P record against a Fixture R record.

- [ ] **Step 8: M2 — compare `.facts` directly for the verdict instead of `.hash`.** **Caught by**
      Fixture A2's identical arm. **Why the two branches differ:** the mapping compares **unequal**
      under a reordering the hash is invariant to. **Verify the reordering actually survives to the
      comparison** — if the record is re-read through `yaml.safe_load` into a `dict`, insertion order is
      preserved in CPython, so the arm works; confirm that by printing both mappings' `list(...)` before
      trusting the arm, because a reader that normalized the order would make this mutation blind. This
      is the *"the test's reader normalising the defect away"* shape.

- [ ] **Step 9: M3 — drop the condition qualifier from a detail line.** **Caught by** Fixture A1,
      asserting **two** lines each containing its condition key. **Why the two branches differ:** two
      conditions, two keys — **one line versus two is the observable difference**, and a fixture with
      one condition could not tell a dropped qualifier from a collapsed pair.

- [ ] **Step 10: edit task 8's row-order assertion — the one edit this task is authorized to make.**
      Its list gains `'apparatus'` in fourth position, before `'parameters_hash'`, and **nothing else
      is reordered.** This task's report shows that one-label diff. Every other assertion that fails is
      a finding to report, not a pin to edit.

- [ ] **Step 11: run and commit.** `mypy` → still **49 source files**; format → still **88 files**.

---

## Task 10: `diff`'s exit code, and the config side's four `not comparable` rows

**Surface: a direct call on `command_diff`, plus documents.** Decisions 4 and 5 — the two
contradictions `H8-SCOPING.md` § 8 enumerated and left open.

**Files:**
- Source: `src/publishable/diff.py`
- Test: `tests/test_diff.py`
- Document: `docs/reference.md` § Exit codes and diagnostics, § Operation commands

- [ ] **Step 1: `diff` exits `0` on every comparison it renders**, whether five rows say `identical` or
      five say `DIFFERS`. It exits **`1`** only when it **cannot** render one: `E-IO-FAILED`,
      `E-UPSTREAM-RECORD-*`, `E-DIFF-CONFIG-UNREADABLE`. Three grounds, and the third is what makes it
      a ruling rather than a preference:
      1. **The advertised payoff IS a difference.** `design-principles.md` § Same code, different
         parameters shows `parameters_hash DIFFERS` and calls it *"the comparison to aim for"*. **A
         command whose documented success case exits non-zero is one no script can put on the left of
         `&&`.**
      2. **`report` is the named precedent.** § Exit codes disambiguates exactly one command this way:
         *"`report` of a `partial` run exits `0` — it was asked to render a record and it rendered
         one."* `diff` was asked to compare two records and it compared them.
      3. **The `1` row generalized from `resume`, where the analogy fails.** There a moved hash blocks
         an **action**: `resume` must not continue, so the code is what stops a script. **`diff` takes
         no action to block**, and the row's other members are all things that stopped something.
      The third candidate reading — `1` only when `code_hash` differs — is **refused**:
      `design-principles.md` makes comparing two runs *"weeks apart at different commits"* the whole
      point of the split.

- [ ] **Step 2: § Exit codes and diagnostics loses its `diff` clause.** The `1` row currently reads
      *"…a `diff` of runs that don't share a hash…"*; **delete that clause** and leave the row's other
      members. **A deletion, not a rewrite.** Then sweep the four documents **by name**, plus
      `CLAUDE.md` and the feasibility analysis, for the same claim stated anywhere else — run each sweep
      against a string known to be present first, and **filter the FILE LIST, never the output.**

- [ ] **Step 3: a config supplies exactly ONE of the five rows, and the other four are refused as ONE
      RULE.** `parameters_hash(doc)` is a pure function of the file. The other four print
      `not comparable` with their reason:

| Row, against a config side | Printed |
|---|---|
| `code_hash` | `not comparable  a config records no code_hash; the tree it would hash is the tree now, not the tree a run used` |
| `input_manifest` | `not comparable  a config records no input manifest; building one resolves the roster and may run a plugin resolver` |
| `uv.lock` | `not comparable  a config records no lockfile hash; the repo's lockfile is the environment now, not a run's` |
| `apparatus` | `not comparable  an apparatus fact is observed by a probe, and diff is not one of the places a probe runs` |

      **Grounds.** § Reproducing on another device solves the identical problem for `reproduce` and its
      sentence is the precedent: *"It cannot verify a `code_hash` and says so, rather than reporting a
      match it never made."* Computing `code_hash` or `uv_lock_hash` from the config's own repo would
      answer a **different question** — the working tree **now**, which `run` refuses to execute when
      dirty and which moves under the next keystroke — and printing that under the label
      `code_hash identical` beside a run's recorded hash is exactly the substitution `CLAUDE.md`
      § Answering a question with a proxy is about. The apparatus row is refused for a stronger reason
      still: § The apparatus core can only observe **enumerates** where a probe runs — *"`dry-run`, at
      run start, before every execution, and at `freeze` — never at `validate`"* — and **`diff` is not
      on that list**, so a probe call here would be a new metered surface no document specifies.

- [ ] **Step 4: config-vs-config and config-vs-run are the SAME RULE**, which is what closes the
      scoping's second contradiction: § Operation commands' *"two config or run paths"* is honoured as
      written, **the mixed form included**, and the wording needs no change. What that section gains is
      the sentence saying what a config side cannot supply, and **all four verdict strings** —
      `identical`, `DIFFERS`, `not captured`, `not comparable`. **The last two appear in no worked
      output anywhere**, so without this a reader greps for a string the code emits and finds nothing
      normative.

- [ ] **Step 5: fixtures.** Config-vs-run (one row computed, four `not comparable`), config-vs-config
      (same shape, both sides configs), and run-vs-run with all five computed — **the third arm is the
      control**, because a build that printed `not comparable` unconditionally would pass the first two.
      Assert the four reasons' text, since the reason is the whole content of the refusal.

- [ ] **Step 6: M5 — return exit `1` when any row `DIFFERS`.** **Caught by** Fixture R2, asserting
      exit **`0`** with a `DIFFERS` row **present**. **Why the two branches differ:** the fixture has a
      differing row **and** a rendered comparison, which is exactly the state Decision 4 splits from
      failure. **The `DIFFERS`-present half is what makes it non-vacuous** — an all-`identical` fixture
      would exit `0` under both branches.

- [ ] **Step 7: a second mutation, for the refusal side.** Return exit `0` on
      `E-DIFF-CONFIG-UNREADABLE`. **Caught by** a fixture whose one operand is a YAML scalar file.
      **Why the two branches differ:** no comparison is rendered in either branch, so **the exit code
      is the only observable**, and asserting it is what keeps `0`-on-difference from becoming
      `0`-on-everything.

- [ ] **Step 8: run and commit.**

---

## Task 11: `diff`'s upstream block, and `diff`'s CLI arm

**Surface: the `diff` command, end to end through `main(["diff", a, b])`.** Decision 6. This task
completes `diff`, so it is also the task that gives it a dispatch arm and flips its `Status` cell —
**arm, constant key and document cell in one commit** (§ Corrections, correction 1).

**Files:**
- Source: `src/publishable/diff.py`, `src/publishable/cli.py`, `docs/reference.md`
- Test: `tests/test_diff.py`, `tests/test_cli.py`

- [ ] **Step 1: the block, printed AFTER the rows and only when either side's `provenance.upstream` is
      non-empty.** It lists each entry's `run_id` and its two short hashes. **And when all five rows are
      `identical` while the upstream lists differ, one line saying exactly that.** Grounds: § Lineage
      between runs claims `diff` *"can tell you two runs differ only because their upstreams did"*, and
      that state is **reachable** — an upstream artifact is read from `output_dir`, not `input_dir`, so
      it is **outside the input manifest**, and two runs can match on all five rows and consume
      different ancestors. Measured at `0a636af`: `provenance.upstream` is written on **every** run and
      is `[]` when there is none, so this is an unbuilt reader of a **shipped** surface — a defect, not
      specification.

- [ ] **Step 2: it is NOT a sixth row, and the code must not make it one.** The five rows are documented
      three ways and their count is load-bearing; `draft`, `status` and `upstream` are a header and a
      block. Assert that the row-label sequence is unchanged when the block prints.

- [ ] **Step 3: a `None` hash in an upstream entry renders `not captured`, and the open filing stays
      open** (§ Corrections, correction 7). Measured at `0a636af`: `UpstreamLedger.record` uses
      `record.get("code_hash")` and `record.get("parameters_hash")`, so an entry's hash **can** be
      `None`, and printing `None…` would be the same false-identity shape Decision 1's `not captured`
      exists to prevent. Reuse that vocabulary. **`spec-defects.md` carries an OPEN entry naming H9 as
      the primary owner and H8b as the secondary consumer** — rendering it correctly is not resolving
      it, and **no task may strike that entry.** Say in the report that the render is defensive and the
      question (is a hash-less record corrupt, or honest from a build that wrote fewer keys) is still
      H9's.

- [ ] **Step 4: the CLI arm — `diff` gets its OWN arm, enforcing exactly TWO paths and no flags.**
      Measured at `0a636af`: `OPERATION_COMMANDS`'s arm enforces exactly one path, so `diff` cannot
      join it. Its arm rejects a leading `-` the same way, and there is **no `--format`, no `--only`,
      no selector** — `design-principles.md` § Everything is in the file forbids anything else.
      Wrong arity prints `` `diff` takes exactly two paths and no flags `` at exit `2`.

- [ ] **Step 5: the flip, in this commit.** Remove `"diff"` from `cli.NOT_BUILT_COMMANDS` and change its
      `Status` cell in `reference.md` § Operation commands to `built`. **Check both directions after the
      flip:** `main(["diff", "_probe_a", "_probe_b"])` is two paths to a two-path command, so it reaches
      real argument handling and reports `E-IO-FAILED` at exit `1` — which is what
      `test_reference_cli_tables_match_what_the_cli_does` requires of a `built` row (neither
      `unknown command` nor `is specified but not built` on stderr; it asserts no code for a built row);
      and the Command table must still hold at least one `NOT BUILT` row so
      `test_reference_cli_tables_are_parsed_at_all`'s control stays non-vacuous. **Do not add a
      `Status`-column workaround** — if the test fails, the flip and the arm are not in the same
      commit.

- [ ] **Step 6: § Operation commands' `diff` row's `Does` cell.** It reads *"Reports each hash as
      identical or differing, then the specific parameter deltas."* Check it against what shipped: it
      omits `not captured`, `not comparable`, the draft label and the upstream block. **The document
      changes to say what the command does**, which is task 10 step 4's obligation and this task's to
      complete for the block and the label.

- [ ] **Step 7: Fixture U, and its five `identical`s are the discriminating half.** Two runs identical in
      all five rows, one consuming an upstream through `io.reuse_from` and one not. Assert the block's
      presence, its `run_id`, and the "differ only in their upstreams" line — **and that all five rows
      read `identical`**, which is what proves the block carries information no row does. Measured at
      `0a636af`: **resolve a downstream run through `<output_dir>/latest` (with the `latest.txt`
      fallback), never through a glob** — `run_a_project` does `next(results_dir.glob("run_*"), None)`
      and `Path.glob` has no defined order, so a pre-placed upstream named `run_…` under the same
      `output_dir` can be selected instead, which H8a's own § Corrections records as having been
      observed.

- [ ] **Step 8: the draft label, from a `draft: true` fixture.** The key is written today (measured:
      `draft: false` present on every run), so a fixture record with it flipped is what pins the label.
      **`draft` itself is H9's**, so a *genuine* draft run cannot be produced here; say that in the
      report rather than implying the label was pinned against a real draft.

- [ ] **Step 9: a mutation for the block's gate.** Print the block unconditionally. **Caught by**
      Fixture R2, asserting the block's **absence** when both sides' `upstream` is `[]`. **Why the two
      branches differ:** measured — `[]` is what a no-upstream run writes, so the gate is entered by
      every ordinary fixture, and an unconditional block would print an empty section on every
      comparison. **`[]` and absent are both falsy and one truthiness assertion cannot tell them
      apart**, which is why the assertion is on the emitted text and not on a truthiness check.

- [ ] **Step 10: a second mutation, for the "differ only in their upstreams" line.** Print that line
      whenever the block prints. **Caught by** a fixture whose upstreams differ **and** whose
      `parameters_hash` differs, asserting the line's **absence**. **Why the two branches differ:** the
      line's whole content is that the rows agree; printing it beside a `DIFFERS` row is a false claim,
      and an all-identical fixture alone cannot catch it.

- [ ] **Step 11: run.** `uv run pytest` → **+ your new tests**, and **exactly two shipped tests may
      change**: the two CLI-table tests, and only in the `diff` row's direction. `mypy` → **49 source
      files**; format → **88 files**.

- [ ] **Step 12: commit.** `git add -A && git commit -m "H8b task 11: diff's upstream block, and diff
      dispatches"`.

---

## Task 12: codes, homes, and the § Executability re-measurement

**Surface: documents, plus one constant that is already empty of both names.** Runs LAST, so every
claim is made against the finished branch. **This is the last task heading in this file**, which
matters mechanically: `scripts/task-brief`'s extractor prints from a task's heading until the next
`Task N` heading, so **every section after this one lands in this task's brief.** That is deliberate —
§ Corrections against the code is exactly what this task's author must read — and it is said here so
nobody reports it as a defect.

**Files:**
- `docs/reference.md`, `CLAUDE.md`, `docs/superpowers/spec-defects.md`,
  `docs/feasibility-llm-growth-studies.md`
- Test: `tests/test_cli.py` (a document-agreement arm, if one is owed)

- [ ] **Step 1: § Errors — the NEW codes, one row per code.** Eight rows: seven `E-FREEZE-*` plus
      `E-DIFF-CONFIG-UNREADABLE`, plus one warning row for `W-FREEZE-LOCK-MOVED`, plus
      `E-FREEZE-LEDGER-UNREADABLE` if task 1 minted it (it did — nine error rows, and **count them in
      the diff rather than from this sentence**). Each row carries the fault **and the remedy**, because
      each remedy is different and that is the test for whether a split was warranted:

| Code | Fault | Remedy |
|---|---|---|
| `E-FREEZE-RUN-ENDED` | `run.yaml` is present | read the record; there is nothing to freeze |
| `E-FREEZE-NO-CONFIG` | no `<run_dir>/config.yaml`, or no `environment/repo_root.txt` | the run was started by a build before these artifacts existed, or the directory was edited; it cannot be frozen |
| `E-FREEZE-NO-APPARATUS` | the resolved template declares no `apparatus_probe` | nothing to re-probe — the experiment does not measure through an apparatus |
| `E-FREEZE-LEDGER-MISSING` | a probe is declared but the ledger holds no `run_start`/`pre_execution` line | the run has not probed yet; there is no baseline, and probing now would pin a fact the run never adopted |
| `E-FREEZE-LEDGER-UNREADABLE` | a ledger line is not JSON, not a mapping, or missing a required key | the file was edited or truncated |
| `E-FREEZE-PROBE-MISMATCH` | the template now declares a different probe than the ledger records | `templates/**` was edited mid-run; check out the tree the run started from |
| `E-FREEZE-PLAN-MISSING` | no readable `sweep.yaml` | the run died before its plan was written |
| `E-FREEZE-PLAN-MISMATCH` | re-expanded conditions disagree with the recorded plan | the run directory or the config copy was edited; do not trust either |
| `E-DIFF-CONFIG-UNREADABLE` | an operand `diff` read as a config does not parse to a mapping | it is not a config; if it is a run, pass its directory or its `run.yaml` |
| `W-FREEZE-LOCK-MOVED` | the repo's `uv.lock` no longer matches the captured copy | a warning — `environment/` is never rewritten, so nothing on disk changes |

      **Which § Errors table each belongs in**: these are codes a **command** reports as a diagnostic,
      not codes raised into a step, so they belong with the reported family — read that section's own
      opening paragraph (*"these are the codes a command reports"*) and place them the way it says
      rather than by which table looks fuller.

- [ ] **Step 2: § Errors — the REUSED codes, and each row's unit of work is EVERY emit site.**
      `E-TEMPLATE-UNKNOWN` had **two** emit sites and went on claiming "no installed template
      registers" under a row just rewritten to say otherwise; that history is why this step exists.
      - **`E-APPARATUS-CHANGED`** gains `freeze` as an emit site **and a second exit code**: its row
        today ends *"exit `4`"*, and at `freeze` the same fault is exit **`1`**. Say both, and say which
        surface gives which, because the row is what a reader greps.
      - **`E-UPSTREAM-RECORD-MISSING` / `-UNREADABLE` / `-VERSION`** each gain `diff` as an emit site.
        Their row today is written entirely in terms of `io.reuse_from`; widen it to name both readers
        without duplicating the fault descriptions.
      - **`E-TEMPLATE-UNKNOWN`, `E-TEMPLATE-INSTALLED-UNSUPPORTED`, `E-TEMPLATE-LOAD`,
        `E-TEMPLATE-COLLISION`** each gain `freeze`. This is the correction the design does not
        contain (§ Corrections, correction 6): `freeze` resolves a template and **mints nothing** for
        the four states that resolution can reach.
      - **`E-IO-FAILED`** gains `diff` — measured, a missing operand path reaches `main`'s `except
        OSError` at exit `1`.
      **Sweep for each code across the four documents BY NAME**, plus `CLAUDE.md` and the feasibility
      analysis, and prove each sweep can fail by running it first against a string known to be present.
      **Filter the FILE LIST, never the sweep's output** — a reviewer checking this exact rule once lost
      a true hit to `grep -v superpowers`.

- [ ] **Step 3: § Package layout gains two rows.**

```
├── diff.py                    # `diff`: the five rows, hash comparison, parameter deltas
├── freeze.py                  # `freeze`: mid-run re-probe against the ledger, reported not decided
```

      **Place each in the tree the way its siblings sit** — `reproduce.py`, `docs.py`, `study.py` and
      `report.py` are the per-command modules and `cli.py`'s gloss is `dispatch`, which is Decision 14's
      whole ground. Neither row carries `— not yet built`. **Check every row your insertion moved** and
      every count phrase near it; locating a row by position has been wrong twice in this repo,
      once in a row no diff touched.

- [ ] **Step 4: the two worked `diff` outputs that still use ASCII `...` become `…`.**
      `docs/design-principles.md` § Same code, different parameters and `docs/reference.md` § The
      apparatus core can only observe. `README.md` already writes `…` and § Documentation conventions
      prefers it, so this is bringing two files to what the third already does — **and it is required
      rather than cosmetic**, because the code emits one character and a reader greps for what the
      document shows. **Verify all three outputs match what shipped character for character** in their
      verdict words and their `sha256:` truncation width.

- [ ] **Step 5: `CLAUDE.md`'s `EXIT_EXTERNAL` clause — DELETE it** (§ Corrections, correction 4). The
      § Misreadings row on unbuilt readers reads *"`field_convention` is now the sole remaining
      example"* and then, two clauses later, *"`EXIT_EXTERNAL` is the same fault outside `BaseTemplate`:
      defined in `diagnostics.py`, read by nothing"* — **already self-contradictory at `0a636af`**, since
      H7d Part B gave it a reader, and `freeze` gives it a second. **Delete the clause; do not rewrite
      it.** A rewrite invents; a deletion cannot, and the row's remaining content (`field_convention`,
      owned by nobody) is true and load-bearing.

- [ ] **Step 6: `CLAUDE.md` records H8b, in the shape every preceding entry uses.** Dated 2026-08-20,
      naming what it built, **that it retires no refusal and unblocks ZERO configs**, that it repeats
      the four-row table unchanged, and the two or three things worth carrying — which this task's
      author picks from the branch's own reports rather than from this plan. **It may not mint a fifth
      number and may not write "N configs now execute".** It must name Decision 7 as a **behaviour
      change to a shipped command that is additive only**, since that is the one thing a later reader
      will need to know and will not find in a refusal list.

- [ ] **Step 7: `spec-defects.md` — file what H8b found and did NOT close, and strike nothing it did
      not close.**
      - **File**: that a plain `parameters` edit in `<run_dir>/config.yaml` changes every cfg `freeze`
        probes under and is **invisible to every artifact on disk mid-run**, because no
        `parameters_hash` is recorded until `run.yaml` is written (task 5 step 3). Owner: **H9**, whose
        `resume` reads the same two artifacts and must compare the recorded hashes. State the check its
        owner must make: whether `resume`'s hash comparison closes it for `freeze` too, or whether a
        run-start `parameters_hash` artifact is warranted — **and do not decide that here.**
      - **File**: § What `status` means describes no run-directory state for a run that has
        `config.yaml` and no `run.yaml` beyond what `resume` already implies — **only if you find that
        true after reading it.** If it is already covered, say so and file nothing; a filing that is not
        a gap is worse than none.
      - **Do NOT strike**: the `parameters_hash` normalization entry (owner H6 — task 7 step 2), the
        upstream-hash-`None` entry (owner H9, H8b secondary — task 11 step 3), or the
        `max_failed_fraction` truncation entry (unassigned; **no H8b command can reach a run's
        status**).
      - **Re-read every entry whose code this slice changed.** A filing's claims about the code go
        stale like any other comment.

- [ ] **Step 8: the § Executability re-measurement, repeating H8a's four-row table UNCHANGED.** A new
      `### Measured on 2026-08-20 against commit <sha>` section in
      `docs/feasibility-llm-growth-studies.md`, pinned to **this branch's merge commit**. It states:
      `diff` and `freeze` dispatch; `run` writes two more artifacts; **H8b unblocks zero configs**; and
      **all four rows of the table are repeated verbatim** with the note that no row moved and why —
      nothing H8b builds runs at `validate`, nothing is called from a step, and **no config in the
      analysis declares an `apparatus_probe` a real plugin backs**, so `freeze` against any of the nine
      would report `E-FREEZE-NO-APPARATUS`. **That last sentence is worth measuring rather than
      asserting**: it is checkable by resolving `generic` and reading its `apparatus_probe`, and the
      entry should say it was checked. **Mint no fifth number.** The `report_by`-under-`resample` gap
      row is **H4's** and this entry may not claim, move or file it. Also update the entry's own
      sentence about which commands dispatch — measured at `0a636af`, the older entries say `dry-run`,
      `draft`, `resume`, `study` and `reproduce` *"each print `unknown command` and exit 2"*, which was
      already imprecise (they print the specified-but-unbuilt diagnostic) and is a claim in a **dated**
      section, so **append a correction rather than retro-editing it** — that is how this file corrects
      a published claim.

- [ ] **Step 9: both consistency passes, over the FOUR DOCUMENTS BY NAME plus `CLAUDE.md` and the
      feasibility analysis.** Mechanical in full, skipping fenced code blocks: links, `#anchor`s,
      duplicate heading anchors, table column counts, no empty rows, no trailing whitespace, no tabs, no
      invisible unicode, `×` not `x`, hyphen never an en dash in anything that becomes an anchor.
      Cross-document: **Enum comments** (any inline `# a | b | c` this slice touched must list every
      value its table defines), **Schema fields in prose**, **Prevented mistakes**, **Versions**. The
      feasibility analysis is **exempt from the cross-document pass and subject to the mechanical pass
      in full.** The development record under `docs/superpowers/` is governed by neither and is never
      retro-edited; `spec-defects.md` is the one exception.

- [ ] **Step 10: verify `NOT_BUILT_COMMANDS` and the § Operation commands table agree, and that the
      agreement is tested rather than asserted.** Both names left the constant in tasks 6 and 11.
      `test_reference_cli_tables_are_parsed_at_all`'s set equality is the shipped binding; **run it and
      say so.** If this task finds it failing, tasks 6 or 11 flipped a cell without removing a key or
      vice versa — a finding, not a cell to edit.

- [ ] **Step 11: run the full gates and report absolutes.** `uv run pytest`, `uv run ruff check .`,
      `uv run ruff format --check .` (**88 files**), `uv run mypy` (**49 source files**). This is the
      branch's final number and the § Executability entry quotes it.

- [ ] **Step 12: commit.** `git add -A && git commit -m "H8b task 12: eight codes, two module rows, and
      the four-row table repeated unchanged"`. Use `git add -f` for any new file under
      `.superpowers/sdd/` — `scripts/sdd-workspace` rewrites that directory's `.gitignore` to a bare
      `*` every time it runs, and `task-brief` calls it. Restore that file's content when you notice.

---

## Corrections against the code

**Written 2026-08-20 against `main` at `0a636af`**, correcting the design
(`docs/superpowers/specs/2026-08-20-diff-freeze-design.md`). Per `CLAUDE.md`, **the spec's body is not
retro-edited** — this section is appended and says what it replaces. Every claim below was produced by
**running** something or by reading the named source at `0a636af`; none is carried from a scoping.
H7d Part A's plan made fourteen such corrections and H8a's ten, two of them reshaping a task, **so
finding them is expected rather than exceptional.** Two of the ten below reshape a task.

**1. The two `Status` flips cannot live in task 12, and each must land with its own command's CLI arm.
TASK-RESHAPING.** The design's task 12 holds *"`diff` and `freeze` out of `NOT_BUILT_COMMANDS`, both
§ Operation commands `Status` cells flipped"* alongside the § Errors rows. **Measured at `0a636af`:
`cli._dispatch` checks every built branch BEFORE the `NOT_BUILT_COMMANDS` lookup** — its own comment
says so and gives the reason — and `tests/test_cli.py`'s
`test_reference_cli_tables_match_what_the_cli_does` probes each row through `main` with two junk
positionals, asserting for a `NOT BUILT` row both `EXIT_INVOCATION` **and** that stderr starts with
the specified-but-unbuilt prefix. So the moment a task gives `freeze` or `diff` an arm, that test
fails on that row while the document still says `NOT BUILT`. `test_reference_cli_tables_are_parsed_at_all`
adds a second binding: **set equality** between the table's `NOT BUILT` rows and `NOT_BUILT_COMMANDS`'s
keys. **Ruled: the arm, the constant key and the `Status` cell land in ONE commit per command** — task
6 for `freeze`, task 11 for `diff`. Both are the task that **completes** its command, which is a
stronger placement than the design's task 8 would have been: `diff` has no apparatus row until task 9,
and a four-`identical` output over a pair whose apparatus moved is Decision 1's own named
cost-if-wrong. Task 12 keeps the § Errors rows, § Package layout, the remaining document rows and the
§ Executability entry. Also checked: after both flips the Command table still holds ten `NOT BUILT`
rows, so that test's `statuses == {"built", "NOT BUILT"}` control does not go vacuous.

**2. Mutation M12 is BLIND on any fixture built with `run_a_project`, and Fixture C therefore needs a
prescribed mechanism rather than a stated intent. TASK-RESHAPING.** The design's Fixture C asserts
that the run-start copy's **bytes** equal the config file's, and M12 replaces the byte copy with
`yaml.safe_dump(doc)`. **Measured at `0a636af` by running**: `run_a_project` writes its config as
`cfg.write_text(yaml.safe_dump(doc))`, and for that output `yaml.safe_dump(yaml.safe_load(x)) == x` is
**True** — so under M12 the copy is **byte-identical** and the mutation's two branches cannot differ.
The obvious repair has its own trap: `generate_experiment` writes `description: ""` and `authors: []`,
which `validate` **requires**, so a config left byte-for-byte as generated does not validate and an
implementer reaching for `safe_load`/`safe_dump` to fill them lands back on the blind fixture.
Prescribed in task 3 step 3: **edit the generated config as raw text** — targeted string replacement
on those two lines — so comments survive and validation passes, with `assert b"#" in cfg.read_bytes()`
as the control that keeps the byte arm non-vacuous. Also prescribed: confirm M12 fails the byte arm
**while the mapping arm still passes**, which is the asymmetry that makes Fixture C's two arms
necessary rather than redundant. Measured at `0a636af`: `generate_experiment`'s output carries `#`
comments on most lines and a round trip removes all of them.

**3. Task 6 changes `OPERATION_COMMANDS`'s value, and its literal is QUOTED in two places whose
sentences then go stale.** The design does not mention the constant. Measured at `0a636af`:
`OPERATION_COMMANDS = {"validate", "run"}`, and that exact literal appears in
`artifacts.build_allocation_document`'s docstring (*"`OPERATION_COMMANDS = {"validate", "run"}` in
`cli.py`, there is no `resume` command yet"*) and in `reference.md` § Resuming (*"`cli.py`'s
`OPERATION_COMMANDS = {"validate", "run"}` contains no `resume` command"*). **Both sentences' content
survives** — there is still no `resume` — so per `CLAUDE.md`'s *prefer deleting a claim to rewriting
it*, task 6 step 8 **removes the quoted set from each and leaves the claim.** Both sites are in task
6's own diff, because that is the task that changes the constant. Also ruled there, with grounds the
design leaves open: `"freeze"` **joins** the existing one-path arm (one enforcer of the one-path rule,
rather than two) and the arm's ternary becomes a mapping built **inside `_dispatch`** (a module-level
dict of callables would be a forward reference, since `command_validate` and `command_run` are defined
below the constant).

**4. `CLAUDE.md`'s `EXIT_EXTERNAL` clause was already false at `0a636af`, and `freeze` makes it
worse.** § Misreadings' unbuilt-reader row says *"`field_convention` is now the sole remaining
example"* and then, two clauses later, *"`EXIT_EXTERNAL` is the same fault outside `BaseTemplate`:
defined in `diagnostics.py`, read by nothing."* Measured at `0a636af`: `cli.py` returns
`EXIT_EXTERNAL` on an unreachable apparatus, and `tests/test_cli.py` imports it — H7d Part B gave it
its first reader, and its own `spec-defects.md` entry is **already struck as CLOSED**. So the clause
contradicts both the sentence before it and a struck filing. Task 12 step 5 **deletes it**. The design
mentions `EXIT_EXTERNAL` only as gaining a second reader; the stale clause is this plan's find.

**5. Task 7 must not implement or claim `parameters_hash` normalization, and `diff` SURFACES the gap
without owning it.** § Three hashes states *"Values are normalized to what `init` would have
materialized before hashing"* and `spec-defects.md` carries an **OPEN** entry that `parameters_hash`
does not, owner **H6**. `covered_config` is extracted from exactly that function, so an implementer
reading the document beside the code will be tempted to close the gap in passing — which would move
every hash in the suite from a slice about `diff`. Two consequences written into task 7 step 2:
the docstring may make **no** normalization claim, and the filing is **cited rather than restated and
not struck**. And one consequence recorded here rather than built: **`diff` will print
`(absent) → <default>` for a pair the document says hash identically**, because the delta walk sees
the omitted key and the hash does not normalize it. That is a real document-versus-code tension H8b
surfaces and does not own; **no task may add a fixture arm for it** and no task may file it a second
time.

**6. `freeze` resolving a template reaches FOUR states the design's seven `E-FREEZE-*` codes do not
cover, and the fix is reuse, not minting.** Decision 12 enumerates seven faults and the design's
Decision 7 grounds itself on `get_template` needing a repo root — but never says what `freeze` does
when the template does not resolve. Measured at `0a636af`: `get_template("nope", proj)` returns
**`None`** and `get_template("loc_assay", None)` returns **`None`** — and an **installed-only** claim
also returns `None`, because `Claim.cls` is `None` for one; while `_claims(root)` **raises**
`PartialLoadError` (a `ContractError`) under `E-TEMPLATE-LOAD` or `E-TEMPLATE-COLLISION`, and
`discover_local` imports every `templates/*.py`, executing user top level. So four reachable states,
with four different remedies, and **all four already have shipped codes** that `validate_config` and
`generate_experiment` both emit: `E-TEMPLATE-UNKNOWN`, `E-TEMPLATE-INSTALLED-UNSUPPORTED`,
`E-TEMPLATE-LOAD`, `E-TEMPLATE-COLLISION`. Task 4 step 5 resolves through `_claims` rather than
`get_template` for the reason both shipped call sites already give, reuses
`unknown_template_message`/`installed_template_message` rather than writing a second literal, and
**mints nothing**. Task 4 step 6 additionally rules the **catch breadth** the design leaves open —
`except BaseException` with `KeyboardInterrupt` re-raised fresh, on `_probe_for`'s wrapper's precedent
rather than `validate`'s `except ContractError`, because a `sys.exit()` at a template's module scope
is a `SystemExit` that would end `freeze` with the user's own code and no diagnostic. And task 4 step
7 routes the credential set through `exc.partial_templates` for a load or collision fault, which is
the shipped answer to the chicken-and-egg the design does not name: the credential set needs the
template, and a load fault means the template never resolves while the finding just built can carry
the raising file's own exception text. **Fixture F4 gains four arms** for these.

**7. An upstream entry's hash can be `None`, and rendering it correctly is NOT closing the filing that
names H8b.** Decision 6 says the upstream block lists each entry's `run_id` and *"its two short
hashes"* without saying what a missing one renders. Measured at `0a636af`: `UpstreamLedger.record`
copies `record.get("code_hash")` and `record.get("parameters_hash")`, so both can be `None`; and
`spec-defects.md` carries an **OPEN** entry — *is a hash-less upstream record a corrupt one or an
honest one from a build that wrote fewer keys* — naming **H9 as owner and H8b (`diff`) as the
secondary consumer that would observe a silently-`None` hash as a false absence of drift.** Task 11
step 3 renders it with Decision 1's `not captured` vocabulary and **explicitly does not strike the
entry**: a plan that renders it correctly *and* strikes the filing has closed someone else's gap by
accident, which the entry's own "check to run before dispositioning it" makes plain is a two-reading
question this slice does not answer.

**8. Decision 8's cross-check compares two fields where four are recorded, and the two it omits
include the one that determines the cfg.** The design says `freeze` cross-checks the resulting
`(index, label)` pairs against `sweep.yaml`'s recorded `conditions`. **Measured at `0a636af` by
running**: each recorded entry holds exactly `{index, label, values, is_baseline}` — all four
comparable, all four YAML-safe — and `values` is what `resolve_condition_cfg` overlays to build the
cfg a probe is called under. Under `ablate` or a declared `baseline` a label is a **declared name**
that can hold still while `values` moves, so the two-field check would pass a config copy whose
conditions probe different parameters than the run does. Task 5 step 2 compares the full four-tuple in
recorded order. **This is a sharpening, not a widening**: it is the same refusal
(`E-FREEZE-PLAN-MISMATCH`) with the same remedy. Two things deliberately NOT added: `design_digest` (also recorded,
also recomputable — measured, `design_digest(run.yaml["config"]) == sweep.yaml["design_digest"]` — but
it covers `data.units` and `sweep.groups`, **neither of which affects the cfg**, so checking it guards
a property `freeze` does not depend on); and any check for a plain `parameters` edit, which changes
every cfg and is **invisible to every artifact on disk mid-run** because no `parameters_hash` is
recorded until `run.yaml`. That residual is named in § What could not be measured and filed to H9 by
task 12 rather than half-covered by a check.

**9. Decision 6's header is specified for a run side and silent for a config side.** The fenced example
shows `A  run record  <run_id>  completed`. A config has no `run_id` and no `status`. Task 8 step 3
rules: **the form plus the path AS GIVEN, and no status word** — inventing a status would be a claim,
and printing a resolved path would print a fact about one machine when the reader typed something
else. Small, and ruled here because a task that discovers it will invent something.

**10. Decision 2's omission rule and Decision 5's `not comparable` rule overlap on one input, and the
design does not say which wins.** Decision 2: the apparatus row *"is omitted only when both are
`null`"*. Decision 5: against a config side the row prints `not comparable`. **A config side versus a
run whose `apparatus` is `null`** satisfies neither cleanly — there is no apparatus on either side, so
Decision 2 would omit the row, while Decision 5 would print `not comparable`. Task 9 step 4 rules
**Decision 5 wins**, with grounds: the omission rule is about two records that **agree there is
nothing to compare**, and a config side is about a figure that **cannot be obtained here at all** —
`diff` is not one of the four places § The apparatus core can only observe says a probe runs. Printing
nothing would let a reader conclude the two agreed.

---

## Which existing pins Decision 7's new artifacts move

**Measured 2026-08-20 at `0a636af` by reading `tests/` for every enumeration of a run directory or of
`environment/`, then confirming with greps for `iterdir`, `rglob`, `glob("*")` — in that order.**

**Nothing in `tests/` enumerates the run directory's root or `environment/`, so no pin moves on
content.** The nearest neighbours, each named so the next reader does not re-derive them:

| Site | What it asserts | Moves? |
|---|---|---|
| `tests/test_acceptance.py` — the provenance/artifact arm | **Membership**: `executions.jsonl` and `manifest/input.json` `is_file()`, `not (run_dir/"lock").exists()`, `not (run_dir/"environment"/"uv.lock").exists()`, `environment/pyproject.toml`'s bytes against the repo's | **No.** A new sibling file does not move a membership assertion |
| `tests/test_acceptance.py` — the lockfile arm | `environment/uv.lock`'s bytes, `environment/pyproject.toml.is_file()` | **No** |
| `tests/test_cli.py` — the `results_dir` enumeration | `sorted(p.name for p in results_dir.iterdir()) == sorted(["latest", run_dir.name])` | **No** — that is **one level up** from the run directory, and Decision 7 adds nothing to `output_dir` |
| `tests/test_cli.py` — the no-composed-labels arm | `rglob("*")` filtered to `if p.is_dir()` | **No** — both new artifacts are files |
| `tests/test_acceptance.py` — the collapsed-layout arm | `run_dir.glob("seed*")` filtered to directories | **No** |
| `tests/test_cli.py` — H8a's guard-pin arm B, and the apparatus key-list arm | `run.yaml`'s `provenance` key list, `provenance["apparatus"] is None`, `not (run_dir/"apparatus").exists()` | **No** — Decision 7 adds no record key |

**One pin's SCOPE widens, and it is the only one.** `tests/test_cli.py`'s `_files_under(results_dir)`
returns **every file** under the results tree and its callers sweep each one's bytes for a credential
sentinel. Both new artifacts enter that set. They should not carry a sentinel — the config holds a
variable's **name** and `credential_values` reads its value from the environment, and
`repo_root.txt` holds a repo path — **but that is reasoning, not measurement**, so task 3 step 4 runs
every caller of that helper **by name** and reports them green. This is the site to watch precisely
because it is a sweep whose file list grows silently.

**Two pins move BY DESIGN, in tasks 6 and 11, and both are the same pair.**
`test_reference_cli_tables_are_parsed_at_all` (set equality between the § Operation commands table's
`NOT BUILT` rows and `cli.NOT_BUILT_COMMANDS`) and `test_reference_cli_tables_match_what_the_cli_does`
(each row probed through `main`). Each command's flip moves exactly one row of each. § Corrections,
correction 1 is why they cannot both wait for task 12.

**And task 13's own arms A and B move, each by exactly one entry, each edited by task 3 alone**, with
the post-edit list stated in advance in the pin's own docstring.

**No hash moves.** `code_hash` covers `src/**` + `templates/**`; a run directory is outside both.
`input_manifest_hash` covers `input_dir`. `parameters_hash` covers the config. `design_digest` covers
`data.units` and `sweep.groups`. **Nothing in `src/` globs or iterates the run directory's root**, so
core itself has no reader to break — measured, and the reason § Corrections does not carry an
eleventh entry about one.

---

## What could not be measured

- **`freeze` against a genuinely live run holding its own lock.** Fixture F3 is prescribed and nothing
  was run for it here; every claim in this plan about lock tolerance is a **read** of § One execution at
  a time plus the measurement that `append_observation` is callable from outside `command_run` and
  writes to a directory it is handed. It is the one H8b surface needing a second process, and **the one
  most likely to be quietly downgraded to a constructed fixture during execution. It must not be.**
- **Whether `freeze` can seed `Observer`'s accumulator from `replay_ledger` without a change to
  `Observer`.** Measured: `Observer.__init__` builds a fresh `Observations` and takes no baseline
  argument. Whether task 6 reuses `Observer` (assigning `observer.observations` after construction) or
  calls the four functions directly is left to the implementer with the preference stated and the
  hazard named — a `freeze` probing against an empty accumulator compares each fact **against itself**
  and can never report a change. **Fixture F2 is the pin either way**, and if it cannot be made to pass
  through `Observer`, the direct-call route is the answer and the report says so.
- **Whether adding two files to a run directory breaks a reader nothing in `src/` or `tests/` has
  yet.** Measured for both trees at `0a636af`. `resume` (H9) will read that directory and is the reader
  this artifact is **for** — but it does not exist to check against.
- **What a `dry_run` phase line is appended to.** § The apparatus files lists `dry-run` as a phase and
  § Operation commands says `dry-run` *"creates nothing"*. Both cannot hold; `PHASE_DRY_RUN` is named
  in task 2, called by nothing, and the contradiction is **filed to H9** rather than answered.
- **A plain `parameters` edit in the run-start config copy.** It changes every cfg `freeze` probes
  under and is invisible to every artifact on disk mid-run, because no `parameters_hash` is recorded
  until `run.yaml` is written. Named in task 5 step 3, filed to H9 by task 12, **and deliberately not
  half-covered by a check.**
- **Whether any real project's `diff` output is legible at width.** Every worked output in the four
  documents is one condition's worth of facts and two parameter deltas. A 12-condition sweep whose
  apparatus moved prints twelve lines per moved fact under Decision 2's no-collapse rule, and no
  document shows that shape. Said rather than designed around.
- **Whether an upstream record missing a hash is corrupt or honest.** The open filing's own question,
  owner H9. Task 11 renders `not captured` for it and settles nothing.

---

## Plan self-review

- **Every task states its surface**, and none is `validate` — which § The apparatus core can only
  observe's own enumeration makes a fact rather than a filing.
- **Every mutation names the assertion that catches it and why the two branches can differ**, and the
  two that could not are handled rather than dressed up: **M12 is blind on `run_a_project`** and
  Fixture C is rebuilt for it (correction 2), and **M8 is split across tasks 1 and 6** because its
  discriminator is an exit code that does not exist until task 6 — each half named where it lands.
- **Three mutations carry an explicit "check the two branches can differ before trusting it"
  instruction** — task 5 step 7 (labels must be genuinely equal across the edit), task 7 step 6 (the
  verdict is `DIFFERS` under both branches, so the **line count** is the discriminator), and task 9
  step 8 (a reader that normalized key order would make M2 blind).
- **Every literal in the fixtures was produced by running at `0a636af`**, and every hash is read back
  or recomputed rather than written down.
- **The guard pin's two movable arms name their editor and their post-edit list in advance**, and every
  other arm is a finding if it fails.
- **The behaviour change lands alone**, in its own batch and its own commit, with the additive claim
  pinned in two directions (a stray file in each of the two directories) rather than asserted.
- **The document precedes the code** for Decision 7, on the controller's requirement, and § CLI
  reference's `resume` sentence is made **true by the artifact** rather than edited to match a hole.
- **No task moves a config count, mints a fifth number, or touches the `report_by`-under-`resample`
  gap**, and § The payoff, task 12 step 8 and the global constraints each say so independently, because
  an implementer sees only their own brief.
- **Three filings are named as NOT to be struck** (H6's normalization, H9's upstream hash, the
  unassigned truncation), because a plan that renders a gap correctly and strikes it has closed
  someone else's work by accident.
