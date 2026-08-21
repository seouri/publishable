# H8c — `report`, `study`, and `BaseReport` — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to
> implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** the reporting half of H8, and the last of its three sub-slices. `BaseReport` and a frozen
`Section`; a read-only `ReportIO`; override discovery from the run's own `entrypoint`; four standard
sections that are pure functions of the parsed record; two renderers over one section stream;
`report <run.yaml>`; `report <study.yaml>` with its two cross-checks; `study new` and `study add` with
their redaction, their refusals and their disclosure prompt; and `generate report`. Nothing here
executes a step, takes a lock, probes an apparatus, or writes a byte inside a run directory.

**The payoff, stated so it cannot be rounded, and it is a table rather than a number. H8c moves NO
row of it.** The 2026-08-20 correction in
[the feasibility analysis](../../feasibility-llm-growth-studies.md) § Executability on this build ruled
that a single figure answers no consistent question for that analysis. H8a replaced the number with a
four-row table, H8b repeated it unchanged, and **H8c repeats it unchanged again — all four rows.**

| Figure | Count | Visible to `validate`? |
|---|---|---|
| Transplantable configs validating with zero errors | **8 of 8** | yes — the only figure `validate` can see |
| Blocked on `io.reuse_from` | **0** | no — the method ships; six configs still need the plugin body to call it |
| Meet the `report_by`-under-`resample` gap | **7** | no — **H4 Statistics'** gap, untouched here |
| Free of every core-side dependency this analysis can name | **1** | no — E5, and only with the plugin written and installed |

**No task may write "N configs now execute", and no task may mint a fifth number.** Nothing H8c
builds runs at `validate`, nothing it builds is called from a step, and no config in that analysis
declares a report override. **The only direction H8c could move a count is down** — H7d Part B's and
H8b's shape, said here for the same reason — and it does not move one: `report` reads, `study` bundles.
**The `report_by`-under-`resample` gap is H4's and no task may claim or file it.**

**Architecture.** Two new modules named by § Package layout already, one new generator, one new
`io` class beside the one whose read half it shares, one new export.

- **`report.py`** (new) holds `BaseReport`, the frozen `Section`, `command_report`, form detection,
  override discovery, the four standard sections, the two renderers and the bundle render. It imports
  `lineage.read_run_record`/`read_record_file`, `artifacts.ReportIO`,
  `base_experiment.load_experiment`, `stats.RESERVED_METRIC_NAMES`,
  `templates.registry.get_template`, `validate.declared_credential_names_for` and
  `secrets.credential_values`.
- **`study.py`** (new) holds `command_study_new`, `command_study_add`, the four-field redaction, the
  `code`-block semantics, the duplicate-name refusal and the `min_reported_n` prompt.
- **`artifacts.ReportIO`** — four read members, built over module-level traversal functions that
  `StepIO`'s own `read_condition`/`_nest_repeat` are rewritten to call, so the artifact-tree layout
  cannot move for a step and hold still for a report.
- **`lineage.read_record_file(path)`** — the parse-and-refuse body `read_run_record` already has,
  extracted so a **file** can be read; `read_run_record(run_dir)` delegates with `run_dir / "run.yaml"`
  (§ Corrections, correction 1). A bundle member is `<name>.run.yaml`, not `<dir>/run.yaml`.
- **`generators/report.py`** (new) holds `generate_report`, on `generators/template.py`'s shape.
- **`cli.py`** gains `"report"` in `OPERATION_COMMANDS` and a `study` arm with its own flag parsing.
- **`publishable/__init__.py`** exports `BaseReport` — the one new name on § The importable surface.

**Tech stack:** Python ≥ 3.11, `pytest`, `ruff`, `mypy`. The changes land in
`src/publishable/report.py` (new), `src/publishable/study.py` (new),
`src/publishable/generators/report.py` (new), `src/publishable/artifacts.py`,
`src/publishable/lineage.py`, `src/publishable/cli.py`, `src/publishable/__init__.py`,
`README.md`, `docs/design-principles.md`, `docs/reference.md`,
`docs/superpowers/spec-defects.md`, `CLAUDE.md`, and the test modules
`tests/test_report.py` (new), `tests/test_study.py` (new), `tests/test_cli.py`,
`tests/test_diff.py`, `tests/test_artifacts.py`, `tests/test_lineage.py`.

**Spec:** `docs/superpowers/specs/2026-08-21-report-study-design.md` — read it beside this plan,
including its § Refusals, § The discriminating fixtures, § The mutations, § The filings this slice
makes and § What did not survive H8a and H8b shipping. It is the binding authority and this plan
argues from it. **Its body must not be edited.** Where this plan measured something that contradicts
it, the disagreement is recorded in [§ Corrections against the code](#corrections-against-the-code),
appended by this plan's author and extended by no task.

**Measurement this plan argues from:** `docs/superpowers/H8-SCOPING.md` — **whose H8c claims the
design already falsified in six places, and the design wins**; the design's own re-measurement; and
this plan's re-measurement against **`main` at `ebf642a`**, this branch's point. **`ebf642a` is one
docs-only commit above the design's `9963841`** (`git diff --stat 9963841 ebf642a` → one file, the
design itself), so the code this plan measured is byte-identical to the code the design measured —
which is what licenses reusing the design's fixture shapes while re-measuring its claims. Every
signature, record field, helper name and literal below was read or **run** at `ebf642a`. **Nothing is
cited by line number.**

**Baseline, measured 2026-08-21 in the FOREGROUND at `ebf642a`:**

- `uv run pytest -q` → **2636 passed, 1 skipped, 2 xfailed** in 154.22 s
- `uv run ruff check .` → **All checks passed!**
- `uv run ruff format --check .` → **88 files already formatted**
- `uv run mypy` → **Success: no issues found in 49 source files**

**Task count: 17.** The design's 16 in its own grain and its own numbering, plus **task 17, the guard
pin, which runs FIRST**. The addition **appends** rather than renumbering, on H8a's, H8b's and both
H7d parts' precedent, so the design's numbering stays citable. 17 tasks make 17 commits.

---

## Sequencing

**Execution order: 17 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14 → 15 → 16.**

The task headings below are written in that order. Each task restates the constraint it depends on in
its own text, because an implementer sees only their own task brief.

| Constraint | Why, and where it is enforced |
|---|---|
| **Task 17 first** | H8c moves no run record and no artifact, so its pin is a **never-moves** detector over exactly the surface `report` reads: the record's field-level shape, the artifact paths `read_condition` resolves, `__all__`, and the three worked `diff` blocks' row text. A literal captured after a task has run records the move, not the baseline. Four slices running, a pin captured from a real run **before anything changed** has held |
| **1 before 2, 2 before 3** | `Section` is what `sections` yields; `ReportIO` is what `sections` takes; discovery is what produces the subclass. Building them in the other order gives a discoverer with nothing to discover |
| **2 before 5** | Not for the sections' sake — they touch no `io` — but because task 2 rewrites `StepIO`'s traversal, and a batch that also rendered would mix an artifacts-layout regression with a rendering one |
| **3 alone in its batch** | The highest-risk decision in the slice. Its review must certify three separate "not a proxy" answers, and a reviewer certifying those must not also be certifying a renderer |
| **4 before 5, 6, 7** | A section needs a record to render, and task 4 is what loads one — including `read_record_file`, which task 10 also needs |
| **5, 6 before 7** | A renderer consumes a section stream; there is nothing to render until the stream exists |
| **8 owns `report`'s CLI arm and its `Status` cell** | `_dispatch`'s built branches precede the `NOT_BUILT_COMMANDS` lookup and `tests/test_cli.py`'s CLI-table test asserts **both** directions, so arm, constant key and document cell must land in **one commit** — and at the point the command is complete, not before (§ Corrections, correction 5) |
| **8 before 9** | The draft refusal is a gate in front of a render that must already work |
| **9 before 10** | The bundle's flag-not-refuse asymmetry is the second arm of task 9's decision, and task 10 renders the bundle it flags in |
| **10 before 11–14** | A bundle render is what proves a bundle is readable; `study add` is what writes one. Building the writer first would let a reader be shaped to whatever the writer happened to emit |
| **11 owns the `study` arm, and routes `add` to `_report_not_built` until task 13** | The built-branch-first rule again: a `study` arm that swallowed `study add` while its `Status` cell still read `NOT BUILT` fails the CLI-table test (§ Corrections, correction 5) |
| **13 owns `study add`'s `Status` cell, the group-usage arm, and the shipped group test** | Once both subcommands are built, `_dispatch`'s `any(n.startswith("study "))` fallback matches nothing and `test_a_command_group_answers_for_its_unbuilt_subcommands`'s premise is false (§ Corrections, correction 4) |
| **12 before 13, 13 before 14** | Copy, then the refusal that must precede the copy, then the prompt that must precede both. Ordered so each task's fixture can assert the *bytes on disk* of what the previous one wrote |
| **15 owns § Generators' `Status` cell and the shipped table-parser test** | Same one-commit rule, plus: § Generators' only `NOT BUILT` row is `report`, so flipping it makes a shipped per-table assertion false (§ Corrections, correction 3) |
| **16 last** | § Package layout, § CLI reference's prose, § What `study add` redacts' ruling, § A report override's `io` sentence, § Exit codes' creation-command enumeration, the three worked `diff` blocks and both consistency passes all run against the finished branch |

### Three deviations from the design's grain, each argued

**(a) Task 17 exists at all.** The design names no regression pin. What `report` reads is the
*inside* of a record — field by field — and what `ReportIO` resolves is the artifact tree; neither is
pinned at field level today, while the top-level and `provenance` key lists already **are** pinned by
more than one shipped assertion — H8a's arm B, H8b's arm C, and a shipped H7d apparatus test, all
three measured at `ebf642a` — so task 17 deliberately adds no further copy of those and says so.

**(b) Every code's § Errors row lands in the commit that first raises it, not in task 16.** The design
puts all of Decision 15's rows in task 16. **A § Errors row narrower than its code was the
whole-branch Major on both preceding sub-slices** — H8a's, in rows a task had *just* repaired three
rows above, and H8b's twice over, in codes its own Decision 10 explicitly reused — and H8b's ledger
records that **no review was dispatched for the task that held them**, with three of four whole-branch
Majors living in that one commit. A row written in the same commit as its raise is read by the same
reviewer who reads the raise. Task 16 keeps the cross-cutting document work and **verifies** that every
code raised on the branch has a row (§ Corrections, correction 6).

**(c) The four `Status` cells leave task 16.** Argued in the table above and in § Corrections,
correction 5. This is H8b's correction 1 re-derived against the same code, not carried from it.

---

## Batching — nine batches, one report and one review each

**`report` renders, `study` bundles, `BaseReport` is user-facing API: three different risks, and they
are three seams.** A renderer's failure mode is text that omits a number; a bundler's is bytes written
outside a repo and a name silently overwritten; an API's is a shape every override ever written is
built against. One review certifying all three would be certifying nothing in particular.

| Batch | Tasks | The seam, and what its review must be able to see |
|---|---|---|
| **B1** | **17** | **The pin, before anything moves.** A capture check: that every arm was produced by **running** and reading artifacts back, never transcribed from `cli.py`, `run_record.py` or `stats.py`; that the record-field arm asserts **full key lists as lists**, not membership; that the worked-`diff`-block arm captures the rows **as raw text** so no reader normalizes the thing under test away; and that the one authorized-edit clause names exactly one task and states its post-edit state in advance. It must confirm no gate literal moved: still 49 source files, still 88 formatted |
| **B2** | **1, 2** | **The user-facing API, and nothing dispatches.** `BaseReport`, `Section` and `ReportIO` are reachable from no command in this batch, which is the seam. Its review is a **type-and-surface review**: M14 (`Section` unfrozen) demonstrated against an override that mutates a body; `ReportIO`'s withheld half asserted by name (`write`, `record`, `append`, `finalize`, `skip`); and — the part only this batch can check — the extracted traversal mutated **once** and **both** a `StepIO` test and a `ReportIO` test failing on it, which is the whole of Decision 4's anti-drift claim. A mutation that fails only the report side proves the extraction was a copy |
| **B3** | **3** | **Override discovery, alone, because it is the slice's proxy risk.** Its review must certify **three** direct answers, each against the correlate it replaces: the module comes from `entrypoint`'s root package and not from a scan of `src/*/report.py` (M1, two packages); the repo comes from `environment/repo_root.txt` and not from `provenance.git.repo_root` (M2) and not from a walk-up (rejected as a mutation, § Corrections, correction 12); and the render happens **inside** the `sys.path` window with the root package purged from `sys.modules` first (M11, M15). **M15's arm is two projects declaring the same package name, rendered in sequence in one process** — the only arm on which purge and no-purge differ — and no other fixture in this slice can see it |
| **B4** | **4, 5, 6, 7** | **The record in, text out — no run directory in the picture.** All four standard sections are pure functions of the parsed record, so this batch's review is a **rendering review against emitted text**: the four section titles' **order** read out of the render (never out of the generator — that is the thing-under-test-iterating-itself shape a recent slice shipped); M13's `by` exclusion on a fixture that genuinely declares `report_by`; M4's `results.contrasts` on Fixture D, the only fixture where the two readings differ; and `repeat_spread` present in the Conditions section (§ Corrections, correction 8). It must confirm task 4's `read_record_file` extraction left `read_run_record`'s three refusals reachable from **both** entries |
| **B5** | **8, 9** | **The first real-command batch. Its review must be a real-command review.** H7d Part A's only Critical was invisible to every direct-call probe and surfaced only through an end-to-end run, and every direct-call probe there hand-built the maps and so never reached it. Every assertion here goes through `main(["report", …])`: exit `0` on a `partial` record **with the failed executions named in the Attrition section** (Fixture P — asserting only the exit code passes identically if the section rendered nothing), M5, M6's exit-1-**and**-empty-stdout pair, and the credential arm of § Corrections, correction 7 with a **positive control that leaks the sentinel when redaction is unwired** |
| **B6** | **10** | **The bundle render, alone, and its review certifies a NEGATIVE.** No override discovery happens on a bundle — a batch that also built discovery would be certifying that against itself. It must see: M3's hand-edited-hash arm (the only record on which "compare the recorded string" and "recompute from `facts`" differ — on every honest record the branches are identical, which H8b already pinned); the `apparatus: null` **exclusion** arm, which the other three cannot see; the `code_hash` notice **naming what was found and diagnosing no cause**; and that the render opens no path outside the bundle directory |
| **B7** | **11, 12, 13, 14** | **Bytes on disk, outside every repo.** The seam is that nothing here renders and nothing here reads a run directory. Its review is a **refuse-before-write review**: every refusal arm asserts the bundle's bytes are **unchanged afterwards** (M8, M9 — a name-set or exit-code check alone passes a build that refuses *after* copying), every hash asserted **byte-equal to the source record's**, the `hostname` row exercised only over a record whose docstring says it was synthesized, and M7's **proper-subset** list with the floor read back from the record. It must also confirm the `study` group arm and the shipped group test moved together (§ Corrections, correction 4) |
| **B8** | **15** | **A generator that writes into a repo.** Its review must see the arity refusal firing **before anything reaches disk** — `tests/test_cli.py`'s CLI-table test probes every built generator with two junk positionals **inside this repository**, which is `generate template`'s own stated reason for checking arity first — the scaffolded body rendering **more** sections than no override at all, and the shipped table-parser assertion edited to exactly the post-edit state task 17's clause states |
| **B9** | **16** | **Documents, alone, and reviewed — which is the batch H8b skipped.** H8b's ledger names this precisely: *a documents-and-codes task looks like the safest one to skip and is the one whose output no later batch reads, so nothing else will find its errors.* Its review is a **guard-and-document review**: whether every code raised on this branch has a § Errors row covering **every** emit site; whether the three worked `diff` blocks changed by exactly two lines each with **no hash prefix, run ID, delta line, row label, row order or separator moved** (task 17's arm D is the proof, not the promise); whether every sweep **named its files** rather than filtering its output and was **proven able to fail**; and whether § Executability's four-row table is repeated **character for character** with no fifth number |

---

## Global Constraints

Every task inherits all of these. They are copied verbatim rather than cross-referenced, because an
implementer sees only their own task brief.

**Commands.** Tests `uv run pytest`. Lint `uv run ruff check .`. Format `uv run ruff format .`.
Types `uv run mypy`. All four must pass before a commit. **Baseline at `ebf642a`: 2636 passed, 1
skipped, 2 xfailed; 88 files formatted; 49 source files typed.**

**The gate literals move in this slice, and the tasks that move them are named.** `mypy`'s source
count rises with each new module: `src/publishable/report.py` in task 1 (**50**),
`src/publishable/study.py` in task 11 (**51**), `src/publishable/generators/report.py` in task 15
(**52**). `ruff format --check` rises with each new file of any kind: `report.py` +
`tests/test_report.py` in task 1 (**90**), `study.py` + `tests/test_study.py` in task 11 (**92**),
`generators/report.py` in task 15 (**93**). **Every task states its own DELTA on the test count, not
an absolute**; compute the absolute from your own previous run and reconcile any difference before
committing. An implementer who reads 49 as the expected source count after task 1 will reconcile a
"failure" that is a new module.

**Run `uv run pytest` DIRECTLY, in the foreground, and wait for it.** It takes about two and a half
minutes at this baseline. **Never construct a wait, a monitor, a poll or a background run around it** —
several agents on preceding slices stalled that way and one stopped with a mutation still applied.
Clear `__pycache__` and any stale `pytest-of-*` temp directory before a run.

**Verify format with `uv run ruff format --check .`, never the bare form.** A previous brief in this
repo wrote the bare form where it meant `--check` and rewrote 67 files. **`ruff format` does not
process `.md`** — measured twice on preceding branches by copying a document, running the formatter and
diffing byte-identical; two agents nonetheless reverted documents on that misdiagnosis. **A revert is
verified by behaviour**, never by `git status`, and least of all by an account of what caused the
change. **`git checkout -- <file>` destroys uncommitted work** and has been mistaken for reverting a
mutation three times in this repo.

**Every task says whether its surface is `validate`, a real command, a direct call, or documents.**
**No task's surface is `validate`, and none is owed** — `report` and `study` are not `validate`-time
checks of anything, and § The apparatus core can only observe enumerates where a probe runs and
neither command is among them. **That is a fact, not a filing**, and no task may file it as a gap.
**Where a task's surface is a direct call, its brief says what the real-command batch will cover
instead** — H7d Part A's only Critical was invisible to every direct-call probe and surfaced only
through an end-to-end run.

**Nothing in H8c stops or alters a run, and every task states what it must not touch.** `report`
opens nothing for writing: every standard section is a pure function of the parsed record, the only
files it may open under a run directory are through `ReportIO.read_condition`/`read_input`, and
`ReportIO` has no write member to call. It takes **no lock**. `study add` writes only inside the
bundle, which is refused inside any git repo. **No probe runs** — neither command is one of the four
phases, so neither spends quota and neither appends to `apparatus/probes.jsonl`. A task that writes
into a run directory has broken append-only for the artifact a paper cites.

**Every literal is computed, not guessed, and every mutation names the assertion that catches it AND
why the two branches can differ.** Across recent slices several prescribed mutations could not
discriminate: one **was what the shipped code already did**; one made **both branches identical**; one
was **placed one line off** and so tested a different property; one **fired for the wrong reason**
because another clause already refused the fixture; and one **iterated the thing under test**, so
removing a member moved the expectation and the actual together. **A mutation that changes nothing is
evidence about the TESTS, not about the code**, and "no mutation reaches this" and "no mutation *can*
reach this" are different claims. Before trusting any mutation, check that its two branches can
produce different results **on the named fixture**.

**Read every fixture literal back from what produced it.** Measured at `ebf642a`: `run_a_project`
prefixes a generated step's name (`extra_steps=["step_summary"]` produced `step02_step_summary`);
the default `replication` is five `seed` repeats, and a repeat label is `seed<NN>` with digits
derived per run, so **no repeat label may be written as a literal**; and every hash a fixture
asserts must be read back from the record or recomputed over the same inputs.

**Mutation discipline, every task.** Keep a copy of the file before mutating. Apply the named
mutation. Run the named test, confirm it **FAILS and read WHY it failed** — a mutation that fails for
the wrong reason is not a pin, and only reading the failure text tells you which you have. Then run
the **full, unfiltered** suite in the foreground. Then
`find . -name __pycache__ -type d -exec rm -rf {} +`. Then revert **by editing the file back in
place**. Verify the revert by **behaviour** and by diffing against your saved copy.

**A safety argument in a comment is a claim, and needs a mutation like any other.** Decision 2's own
history is the proof: an earlier draft argued that "an override cannot change a number" was
*structural* and concluded there was nothing to mutate — false for a `Section` whose `body` is a
mapping, which this design permits. The claim is now sized to what the type provides and the type is
frozen so that it is true (M14). **A comment or docstring claiming a guarantee the code does not
provide** is this repo's most repeated habit; if a comment you write says *this cannot happen*, make
it happen. And **prefer deleting a claim to rewriting it** — a rewrite invents, a deletion cannot.

**Answering a question with a proxy is this repo's most expensive habit.** Both fail-opens in H7a and
a shipped credential leak in H7c came from it, and one corner was given **five** wrong grounds across
two slices. In this slice, each direct question and the correlate it replaces:

- *Which form is this path* — the argument's **file name** (`run.yaml` or `study.yaml`) and nothing
  else. Never by parsing the document and looking for a discriminating key, never by `is_dir()`, and
  **never by reusing `diff._form`**, which answers "config or run record", a different question.
- *Which override belongs to this run* — the record's embedded `config.entrypoint`'s **root package**,
  and that package's `report` module. Never a scan of `src/`, never a module-name prefix, never a
  marker stamped on a class, never definition order among two subclasses.
- *Which repo did this run come from* — **`environment/repo_root.txt`**, read from the run directory.
  Never `provenance.git.repo_root` (recorded at run end, and redacted by `study add`), and never a
  walk-up: `output_dir` may never resolve inside the git repo, so a walk-up answers "is there a repo
  above `output_dir`" — a different question — and on a correctly configured project **`find_repo_root`
  raises `E-GIT-NO-REPO`** rather than answering it.
- *Is this the same apparatus* — the recorded `provenance.apparatus.hash` **string**, never a
  recomputation over `facts`, whose key order the hash is invariant to and whose recanonicalization
  `apparatus_hash`'s own docstring constrains.
- *Which keys of `aggregated[step]` are metrics* — every key **except** those in
  `stats.RESERVED_METRIC_NAMES`, imported, never a literal `"by"`.
- *Did the copy land* — the **bytes on disk**, never the `runs` key set, which is written by a
  different statement and can agree while the file is wrong.
- *Is this metric thin* — the **entry's own** figure keyed on what that entry carries, never a lookup
  over a list of three shapes.

**Never filter the output of a sweep whose job is to find a string — filter the FILE LIST**, and prove
each sweep can fail by running it against a string known to be present. **Name the four documents
explicitly (`README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`,
`docs/reference.md`), and name `CLAUDE.md` and `docs/feasibility-llm-growth-studies.md` too**: H7d
Part A's Major 1 was a paraphrase surviving in the feasibility analysis because the brief's sweep named
only the four. The development record under `docs/superpowers/` is **not** governed by the
cross-document pass and is never retro-edited; `spec-defects.md` is the one exception, where a closed
gap is **struck** rather than left to mislead.

**When a change makes a sentence false, that sentence is in the diff already being read.** Four
instances are pre-named here so nobody discovers them: task 1 makes § The importable surface's
`not yet built` cell false, and the sentence *"Importing one raises `ImportError` today"* **derives**
its claim from the `Status` column, so it needs **no** edit — replacing it with an enumeration would
convert a self-maintaining statement into a maintenance obligation nobody owns. Task 8 makes
§ CLI reference's `report` row's `NOT BUILT` false. Task 13 makes
`test_a_command_group_answers_for_its_unbuilt_subcommands`'s docstring premise — *"every subcommand it
could name is unbuilt"* — false. Task 15 makes § Generators' `report` row and the inline
`` `report` (NOT BUILT) `` in § Creation commands' `generate` cell false, and the shipped table-parser
test asserts the tie between them.

**One shipped sentence is re-read and judged STILL TRUE, and no task may rewrite it.**
`W-STEP-ESTIMATE-N`'s message says an interval with no stated denominator *"is the disclosure risk
`limits.min_reported_n` exists to catch, and `study add` cannot check what it cannot see."* Decision
13 lists such an `Estimate` **unconditionally** — which is the *consequence* of not being able to
check it, not a contradiction of the sentence. Named here because the two readings are one word apart
and a task that "fixed" it would delete a true claim (§ Corrections, correction 11).

**Documentation rules.** `×` not `x` for multiplication, including inside fenced blocks. Hyphen,
never an en dash, in anything that becomes a filename or an anchor. **Cite by section**
(`reference.md` § "What `study add` redacts"), **never by line number**. **No positional locators**
("the row above", "further up"): name what a sibling row *does*, and when you insert a row check every
row it **moved** and every count phrase near it — at least seven positional references in this repo
were wrong twice. **No counts in prose or comments** and **no call-site enumerations**. **A build fact
is dated and pinned to a commit** — today is **2026-08-21**.

**§ Errors carries one row per code, covering every emit site**, not one row per site — the
`E-TEMPLATE-UNKNOWN` two-emit-sites shape, which went on claiming "no installed template registers"
under a row just rewritten to say otherwise. In this slice that binds three shipped codes:
`E-UPSTREAM-RECORD-MISSING`, `-UNREADABLE` and `-VERSION` each gain **two** callers (`report` and
`study add`) on top of the `diff` their row already names, and each gains a **file** operand shape
their present wording contradicts (§ Corrections, correction 1).

**The four normative documents LEAD; `src/` follows.** Where they and the code disagree, **the
document changes first** and the gap is recorded in `docs/superpowers/spec-defects.md`. **A ledger
line saying "filed" is not a filing** — a gap recorded as "registered against \<owner\>" once existed
only in a ledger while the defects file had no such entry. **This slice's spec, `H8-SCOPING.md`, and
every preceding plan and ledger must not be retro-edited.**

**The worked example is BINDING and is touched in exactly one way.** § The worked example's intervals
were checked numerically against a synthetic 228-unit table and **must not be narrowed back**. Task 16
adds two header lines to each of three fenced `diff` blocks and changes **nothing else**: no hash
prefix (`8e21`, `3d8a`, `6b1f`, `1a2b`), no run ID, no delta line, no row label, no row order, and the
two-space separator stays. `report` renders no worked example into any document, so no other task owes
it anything.

**Nothing new is exported except `BaseReport`.** `Section`, `ReportIO`, `read_record_file` and both
command modules are core's own plumbing. § The importable surface is the enumerated list, and a task
that exports anything else has widened a promise rather than tidied an import.

**`tests/conftest.py` already has** an autouse `os.environ` restore, an opt-in `registries` fixture and
an opt-in `installed` distribution fixture. **Do not add duplicates, and do not add a second autouse
fixture of any kind.**

**`validate` collects rather than aborting.** It matters here only in the negative: there is nothing in
this family for `validate` to collect, so no task may infer anything about a `validate` finding from
H8c's behaviour, and **no task may reason that one refusal makes a later check unreachable** — two
independent readers on a preceding slice recorded a mutation as blind on exactly that reasoning before
a reviewer disproved it by building the fixture.

---

## The measured record, once, because every section task reads it

Produced at `ebf642a` by driving `tests/test_cli.py`'s `run_a_project` from a scratchpad script: 24
units with a `cohort` attribute, a declared `baseline` plus a one-axis `grid` (2 conditions), 3 `seed`
repeats, `statistics.report_by: [cohort]`, one declared `statistics.contrasts` entry, one
`confirmatory` hypothesis, a starter step recording a numeric `score` column and calling `io.skip` on a
subset, and a `summary` step returning two `Estimate`s — one with `n: null` and one with `n: 40`.
**Every field named below was read out of that record. No task may take these as literals to assert;
they are the field inventory a section must cover, and each fixture reads its own values back.**

```
run.yaml top-level  : schema_version, run_id, status, draft, config, parameters_hash,
                      code_hash, provenance, layout, execution, results
results             : conditions, summary, contrasts, hypotheses
conditions[]        : index, label, values, per_repeat, aggregated, is_baseline
                      (+ vs_baseline on a non-baseline condition; ABSENT on the baseline)
aggregated[step]    : <metric names> and `by`  — `by` is a SIBLING of the metric names
a metric entry      : value, basis, n{resolved,completed,ineligible,failed}, ci95, method,
                      correction, repeat_spread{std,n,kind}
a `by` stratum entry: value, basis, n{...}, ci95, method, correction   (NO repeat_spread)
vs_baseline[step][m]: delta, basis, paired, method, n_paired, ci95, cohens_d, correction,
                      ci95_corrected, correction_level, family_size, family{comparisons,metrics}
results.contrasts[] : id, of, against, then <step>[<metric>] with the same entry shape
                      (`of`/`against` are the RECORDED, index-prefixed labels)
results.hypotheses[]: id, kind, declared_in, observed, verdict_evaluated_on, supported,
                      verdict_rests_on, family_size, family{hypotheses}
results.summary     : <step>[<key>] = {value, reported: true, ci95, n, method}   (n may be null)
provenance.units    : n, key
execution           : shared (mapping), conditions (LIST of {index,label,steps}), summary (mapping)
a step's entry      : status, started_at, wall_seconds, attempts
                      — a REPEAT-scoped step nests one level of repeat labels FIRST
per_repeat[step][r] : the step's returned scalars  — where a returned scalar lives, and the only
                      place it lives; there is NO `aggregated` entry for it
```

**Three measured facts that decide code, not just assertions:**

1. **`nondeterministic` appears zero times** in `run.yaml` and zero times in `executions.jsonl`.
   Task 6's Attrition section therefore does not claim it (filing 2).
2. **A repeat-scoped step's record entry nests repeat labels even when the run resolved ONE repeat,
   while its DIRECTORY collapses** — measured with `n: 1`: `execution` held
   `step01: {seed47: {...}}` and the tree held `conditions/00_baseline/step01_summarize_units` with no
   repeat segment. So the scope derivation is unambiguous at every repeat count, and `_nest_repeat`'s
   collapse depends on the repeat **count**, which `ReportIO` must therefore be given.
3. **A condition-scoped step's entry holds `status` directly; a repeat-scoped step's holds repeat
   labels.** That is the discriminator task 2 uses, and it was measured in one run holding both.

---

## The discriminating fixtures, stated once because the tasks share them

The design's § The discriminating fixtures is the authority; this section adds only what this plan
measured. **A fixture is a claim too**, and **every fixture whose record was hand-built says so in its
docstring, in those words.** Six fixtures across a recent slice failed their own constraints — one
asserting `b = 0` where 66 hits were expected, one asserting the very value it existed to reject —
every one caught by computing rather than by reading.

| Fixture | Shape | Built by, and the one thing only it can see |
|---|---|---|
| **R** | One real completed run: the measured record above | Tasks 5, 6, 7. The base record; **every printed figure is read back from it** |
| **D** | R plus a declared `statistics.contrasts` entry | Task 5. **Without it, Decision 5's "read both" ships unpinned** — R's every delta is in `vs_baseline`, so a section reading only `vs_baseline` passes the whole suite (M4) |
| **P** | R's starter step raising for one condition's units, `expect_exit=EXIT_PARTIAL` | Task 8. Exit **0** *and* the failed executions named by their own condition and repeat labels. Asserting only the exit code passes identically if the section rendered nothing |
| **T** | R's record with `draft` flipped to `true` and `git.code_dirty` with it — **hand-edited, and the docstring says so and why** (`publishable draft` is H9's) | Task 9. Two arms: `report <run.yaml>` → exit 1, `E-REPORT-DRAFT`, **and empty stdout**; a bundle holding it → exit 0 with the run flagged |
| **O** | An R project whose `src/` holds **two packages**, each with its own `report.py` yielding a distinctly-titled section, `entrypoint` naming one | Task 3. **One package cannot distinguish an entrypoint answer from a directory scan** (M1). Sibling arms: raising import; no subclass; two subclasses; no `format`; and a positive control with **no** `report.py` asserting the four standard sections render and no diagnostic prints |
| **O2** | **Two separate projects declaring the SAME package name**, rendered in sequence in one process, each asserting its own section title | Task 3, and it is this plan's addition. **The only arm on which the `sys.modules` purge and its absence differ** (M15) — on a fresh process with one project the branches are byte-identical, which is why nothing in the design's fixture set can see it |
| **V** | O's override calling `io.read_condition(condition, step, name)` for an artifact its own step wrote, in a run with **more than one** repeat | Task 3 (window) and task 2 (`ReportIO`). The one fixture needing the run **directory**; pins the render happens **inside** the `sys.path` window (M11) and that the repeat segment resolves (M16). Sibling arm: `ReportIO` has **no** `write`, `record`, `append`, `finalize` or `skip` member |
| **B** | Two R runs from the **same** commit, a third from a second commit, and a hand-edited fourth whose `git.commit` matches the first while its `code_hash` does not — **docstring says it was edited** | Task 10. The `code_hash` notice's own case is unreachable from two honest runs |
| **A** | H7d's probe-plugin shape inherited from H8b's Fixture P: a synthetic installed distribution, a project-local template declaring `apparatus_probe`/`apparatus_facts`, answers from a file the test writes | Task 10. Four arms: agreeing facts → no notice; differing facts under one commit → the notice; **one record whose recorded `apparatus.hash` is hand-edited to disagree with a recomputation over its own `facts`** (M3 — the only record where the two readings differ, since H8b already pinned that they agree on every honest one); and one `apparatus: null` beside a real block asserting **no** mismatch notice |
| **N** | R with `limits.min_reported_n` set so the **`by` strata fall below and the whole-condition metric does not**, plus a hand-written `basis: "repeats"` entry in a **synthesized** record whose docstring says nothing in this build writes it and cites the filing | Task 14. The prompt's list is a **proper subset** (M7). Arms: a reported `Estimate` with `n` above the floor asserted **not** listed; the `n: null` one asserted listed; and a run from a directory holding a config with a **different** floor (M12) |
| **Y** | `study new` outside any repo, then two adds, assertions reading the **bytes** | Tasks 11–14. Arms: bundle inside a repo; second `study new`; re-add under a used name with the file's bytes asserted **unchanged**; one run under two names asserted to succeed; and the non-TTY arm asserting `E-STUDY-CONFIRM-REQUIRED` **and that the bundle holds no new file** |
| **H** | The three documents' fenced `diff` blocks, parsed out of the files, against `diff`'s **real** output for a run pair | Task 16. Extends `tests/test_diff.py`'s existing document reader to the **header** lines rather than writing a second parser over the same three files. **Its parser reads INTO fences on purpose** — the mechanical consistency pass skips fenced blocks, and nobody may "fix" this parser to match |

**One fixture the design names that this plan re-sites.** Fixture R's `summary` `Estimate` with no `n`
emits `W-STEP-ESTIMATE-N` at `run`. That warning is expected output, not a failure; a fixture asserting
a clean stdout would fail for a reason that has nothing to do with `report`.

---

## Task 17: the guard pin — the record's fields, the artifact paths, `__all__`, and the worked blocks

**Runs FIRST, before every other task. Surface: `run` plus direct calls plus raw document text.**
H8c changes no run record and no run artifact, so this pin is a **never-moves detector** over exactly
the surface `report` reads. A literal captured after a task has run records the change, not the
baseline. Four slices running, a pin captured from a real run before anything moved has held.

**Files:**
- Test: `tests/test_cli.py` (add), `tests/test_artifacts.py` (add), `tests/test_diff.py` (add)

**Interfaces:**
- Consumes: `run_a_project`, `yaml.safe_load` over `run.yaml`, `StepIO.read_condition`,
  `publishable.__all__`, and the raw text of `README.md`, `docs/design-principles.md`,
  `docs/reference.md`.
- Produces: nothing importable. Arms every later task's suite run must keep green.

**What this pin deliberately does NOT re-capture, and why.** `run.yaml`'s **top-level** key list and
its **`provenance`** key list are already pinned by more than one shipped assertion — measured at
`ebf642a`: H8a's guard-pin arm B, H8b's arm C, and a shipped H7d apparatus test. (H8a's batch-1 review
found the duplication and carried it by name, at a point when there were fewer.) One more copy is one
more place to edit and no new discriminating power. **Grep for them before writing anything, and
report what you grepped rather than a count** — this is the check that catches the six-instance shape
H8b's ledger records, where every false claim was about *other tests* rather than about the
implementer's own code.

- [ ] **Step 1: capture every arm yourself, by running.** Drive `run_a_project` with a `cohort`
      attribute, two conditions, **three** `seed` repeats, `report_by: [cohort]`, one declared
      `statistics.contrasts` entry, one `confirmatory` hypothesis, an `io.skip` call, and a `summary`
      step returning an `Estimate` with `ci95` and **no `n`**. Read every arm below back from the
      artifacts. **A literal transcribed from `cli.py`, `stats.py` or `run_record.py` pins the source,
      not the behaviour.**

```
Arm A — THE RECORD'S FIELD-LEVEL SHAPE. NEVER MOVES IN THIS SLICE.
  Assert FULL KEY LISTS, AS LISTS, not membership — a key added by accident is
  exactly what this catches and a membership assertion cannot see it.
    results                       key list
    conditions[0]                 key list   (baseline: NO `vs_baseline`)
    conditions[1]                 key list   (non-baseline: `vs_baseline` present)
    aggregated[step]              key set == the recorded metric names | {'by'}
    a metric entry                key list, INCLUDING `basis`, `correction`, `repeat_spread`
    a `by` stratum entry          key list, and `repeat_spread` NOT in it
    vs_baseline[step][metric]     key list
    results.contrasts[0]          key list, and `of`/`against` read back (index-prefixed)
    results.hypotheses[0]         key list, INCLUDING `family_size` and `family`
    results.hypotheses[0].family  key list == ['hypotheses']   (NOT comparisons/metrics)
    results.summary[step][key]    key list, and `n` is None for the no-`n` Estimate
    provenance.units              key list
    execution                     key list; execution['conditions'] is a LIST
    a condition-scoped step entry has 'status'; a repeat-scoped one does NOT and its
      keys are the run's repeat labels    (read the labels back; never a literal)
  Every VALUE is read back or recomputed. The only literals are KEY names.

Arm B — `publishable.__all__`, AS A FULL SORTED LIST. THE ONE ARM AN AUTHORIZED TASK MAY EDIT.
  publishable.__all__ == sorted(publishable.__all__)   and equals the captured list
  and 'BaseReport' not in publishable.__all__          (today)

Arm C — THE ARTIFACT PATHS `read_condition` RESOLVES. NEVER MOVES IN THIS SLICE.
  Through a real `summary` step in a run with THREE repeats and again with ONE:
    a condition-scoped step's artifact reads back
    a repeat-scoped step's artifact reads back, WITH the repeat segment at three
      repeats and WITHOUT it at one
  Assert on the VALUE READ, not on a constructed path: task 2 rewrites this traversal,
  and a path assertion would pin the construction rather than the answer.

Arm D — THE THREE WORKED `diff` BLOCKS' ROWS, AS RAW TEXT. NEVER MOVES IN THIS SLICE.
  For each of README.md, docs/design-principles.md, docs/reference.md: the fenced
  `diff` output's lines from the `code_hash` line to the end of the fence, as a tuple
  of raw strings, compared byte for byte.
  LOCATE THE BLOCK BY THE `code_hash` LINE IT CONTAINS, never by an ordinal or an
  nth-fence index: that is a positional locator, wrong twice in this repo, and task 16
  inserts lines into these same files.
  This arm needs NO authorized editor: task 16 inserts two lines ABOVE `code_hash`
  and touches nothing at or below it, so a passing arm D is the proof that no hash
  prefix, run ID, delta line, row label, row order or separator moved.
```

- [ ] **Step 2: write the arms.** One test per arm, named for what it asserts, each docstring saying
      what the arm can see that its siblings cannot. Arm D asserts on **raw text**, never on
      `yaml.safe_load` or any other reader: a defect that lives in *how* bytes are written is undone by
      a reader before the assertion reaches it, which is how a YAML-alias defect once shipped past two
      tests.

- [ ] **Step 3: write arm B's authorized-edit clause.** **Task 1 is the only task permitted to edit
      arm B**, and the post-edit state is stated in advance: `'BaseReport'` is **appended and the list
      re-sorted**, the absence assertion is **deleted**, and nothing else changes. The clause adds:
      **task 1's report must show the diff is exactly that one name plus that one deleted line, with
      nothing reordered beyond the sort.** **Every other task that finds any arm failing has found a
      finding to report, not an assertion to edit.** Without this clause arm B is a change detector the
      slice must silently weaken, which is indistinguishable in the record from weakening a pin to pass.
      The mechanism has completed three clean cycles (H8a batches 1/5, H8b batches 1/3) and is house
      practice.

- [ ] **Step 4: run.** `uv run pytest` → **2636 + your new tests** passed, 1 skipped, 2 xfailed.
      `uv run mypy` → still **49 source files**; `uv run ruff format --check .` → still **88 files**.
      This task adds no file and no module.

- [ ] **Step 5: the mutations — three, because one arm proving itself proves nothing about another.**
      (i) In `src/publishable/stats.py`, add a spurious key to a metric entry's mapping where `basis`
      is written. **Arm A must FAIL** on the metric-entry key list and **arm A's `by`-stratum
      assertion must also fail if the same writer feeds both** — read which assertions failed and say
      so. *Why the branches differ:* the key list gains an element; nothing else in the suite
      enumerates that mapping.
      (ii) In `src/publishable/artifacts.py`, delete the `len(self._repeats or []) > 1` guard in
      `_nest_repeat` so the segment is always added. **Arm C's one-repeat case must FAIL** while its
      three-repeat case **passes**. *Why the branches differ:* the collapse is the only behaviour that
      distinguishes them, which is exactly what task 2 must not move.
      (iii) In `docs/design-principles.md`'s fenced `diff` block, change `sha256:8e21…` to
      `sha256:8e22…`. **Arm D must FAIL for that file and pass for the other two.** *Why the branches
      differ:* three independently captured tuples. Revert all three by editing in place.

- [ ] **Step 6: commit.** `git add -A && git commit -m "H8c task 17: pin the record's fields, the
      artifact paths, __all__ and the worked diff blocks before anything moves"`.

---

## Task 1: `BaseReport` and a frozen `Section`

**Surface: a direct call. Nothing dispatches.** The real-command surface arrives in task 8; this task
builds the API every override is written against, and a shape shipped wrong here breaks every override
ever written.

**Files:**
- Source: `src/publishable/report.py` (new), `src/publishable/__init__.py`
- Test: `tests/test_report.py` (new), `tests/test_cli.py` (arm B edit)
- Docs: `docs/reference.md` (§ The importable surface's `Status` cell, § What you define's
  `BaseReport` row), `docs/superpowers/spec-defects.md` (strike one entry)

**Interfaces:**
- Produces: `report.BaseReport`, `report.Section`; `BaseReport` exported from
  `publishable/__init__.py`.
- Consumes: nothing yet.

- [ ] **Step 1: `Section`, frozen.** `title` and `body`, where `body` is markdown text **or a mapping
      core knows how to table**. **Frozen is a property of the type, not a sentence about intent**: a
      plain value class whose `body` is a mapping lets a subclass reach into that mapping and change a
      number core computed, and *a safety argument in a comment is a claim needing a mutation* (M14).
      A frozen dataclass does not deep-freeze a mapping body — say so in the docstring rather than
      claiming more than the type provides, and note that what it does guarantee is that a
      **re-yielded standard section cannot be rebound**.

- [ ] **Step 2: `BaseReport`.** `sections(self, run, io)` is a **generator** — § The importable
      surface's own middle column says so — yielding `Section`. Core never materializes the list before
      rendering: an override that yields a cheap section first and an expensive figure last must print
      the cheap one first. `self.section(title, *, body)` constructs one, because § A report override's
      worked block calls `self.section("Method agreement", body=...)` and a subclass must not have to
      import a name that block does not import. **`format` has no base default** — a class declaring
      none is refused at render in task 7, not silently defaulted, on `BaseTemplate.aggregate`'s own
      argument that a default makes "declared" and "omitted" indistinguishable. The base
      `sections` yields nothing yet; tasks 5 and 6 fill it.

- [ ] **Step 3: export, and edit task 17's arm B.** Add `BaseReport` to
      `publishable/__init__.py`'s imports and `__all__`, keeping `__all__` sorted. Then edit **arm B
      only**, to exactly the post-edit state its clause states: append the name, re-sort, delete the
      absence assertion, change nothing else. **Show the diff in your report.** § The importable
      surface's `BaseReport` row flips `not yet built` → `built`. **Do not touch the sentence
      *"Importing one raises `ImportError` today"*** — it **derives** its claim from the `Status`
      column and is self-maintaining; replacing it with an enumeration would create a second source of
      truth for build state.

- [ ] **Step 4: § What you define's `BaseReport` row.** Its `Core's` cell names only the standard
      sections. `self.section` and `__init__` are core's too, and a reader of that table is deciding
      what to define. Add `self.section` to that cell (§ Corrections, correction 15).

- [ ] **Step 5: strike the `spec-defects.md` entry.** The entry
      *"~~The importable surface names five things `publishable/__init__.py` does not export~~ —
      MOSTLY CLOSED; only `BaseReport` remains"* is now fully closed. **Strike it rather than deleting
      it** — that file is a live list, and a closed gap is struck so it cannot mislead. Re-read the
      whole entry before editing: **a filing's claims about the code go stale like any other comment**,
      and this one carries a `grep` result that is no longer true.

- [ ] **Step 6: run, then mutate.** Gates: mypy **50** source files, format **90** files, test count
      +your new tests. **Mutation (M14):** remove `frozen=True` from `Section` and add an arm whose
      override reaches into a standard section's `body` mapping and changes a number before yielding
      it. Under frozen the arm's override **fails loudly**; unfrozen it renders a mutated figure. *Why
      the branches differ:* both read the same record, so the difference is entirely in what reaches
      the page. **This arm cannot be written until task 5 produces a standard section with a mapping
      body — so write the frozen-ness assertion here (constructing a `Section` and asserting
      assignment raises) and prescribe the render-level arm to task 5's brief by name.** Say in your
      report that you did, so the carry does not fall out of the chain the way a routed finding did on
      H8a and again on H8b.

- [ ] **Step 7: commit.** `git commit -m "H8c task 1: BaseReport, a frozen Section, and the one new
      export"`.

---

## Task 2: `ReportIO` in `artifacts.py`, and one traversal both classes call

**Surface: a direct call.** *New relative to the design's own task list only in emphasis — the design
adds it because the scoping had no home for the `io` half.*

**Files:**
- Source: `src/publishable/artifacts.py`
- Test: `tests/test_artifacts.py`, `tests/test_report.py`

**Interfaces:**
- Produces: `artifacts.ReportIO` with `conditions`, `repeats`,
  `read_condition(condition, step, name, repeat=None)`, `read_input(relpath)`; and module-level
  traversal functions both it and `StepIO` call.
- Consumes: `sweep.condition_dir_name` (already imported by this module).

**The property.** § A report override calls `io` *"the same read-only accessor a `summary` step
gets"*. **Measured at `ebf642a`: a `summary`-scope `StepIO` is NOT read-only** — it carries `record`,
`write`, `append`, `skip` and `finalize`. Handing one to a renderer would let presentation code write
into a finished run directory, which is the opposite of what `report` is. So `ReportIO` is the
**read half**, and § A report override's sentence changes in task 16 — the document changing first.

- [ ] **Step 1: extract the traversal, do not copy it.** Pull the body of `read_condition` **after**
      its `_summary_only` gate, together with `_nest_repeat`, into module-level functions taking the
      run directory, the conditions list, the repeat labels, the step-scope mapping, and the
      arguments. Rewrite `StepIO.read_condition`/`_nest_repeat` to call them. **`ReportIO` does not
      subclass `StepIO`** (that inherits the write half it exists to withhold) and `StepIO` does not
      subclass `ReportIO`. `_nest_repeat`'s own docstring already carries the argument — *"One rule, two
      callers … Writing it twice is how the two drift — which is exactly what had happened"* — and
      that is the precedent, not an analogy.

- [ ] **Step 2: `ReportIO`'s four members, with a `summary` step's signatures byte for byte.**
      `read_condition` accepts a bare index **or** the `(index, label)` element `conditions` yields,
      because § A report override's documented pattern is
      `for condition in io.conditions: io.read_condition(condition, ...)`. Same containment check on
      `name` (`E-ARTIFACT-NAME`), same refusals, same `read_input`. **No `_summary_only` gate**: a
      report has no scope.

- [ ] **Step 3: build the state from the record, and name where each field comes from.**
      `conditions` from `results.conditions`' `index`/`label`. `run_dir` is the argument's parent.
      `input_dir` is `config.data.input_dir` from the embedded config. `step_scopes` and `repeats`
      are **derived here, from `execution`**, and this is where the design and the code disagree:
      **`lineage.resolve_step` does NOT perform this derivation** — it resolves a *location* and
      **refuses** anything under `conditions[]`, never distinguishing `condition` from `repeat`, which
      is precisely the distinction `_nest_repeat` needs (§ Corrections, correction 2). Build it, with
      the measured discriminator: `execution.shared` → `run`; `execution.summary` → `summary`; a step
      under `execution.conditions[].steps` whose entry **holds `status`** → `condition`; one whose
      entry's keys are repeat labels → `repeat`. Measured at `ebf642a`: **a repeat-scoped step's entry
      nests labels even when the run resolved ONE repeat, while its directory collapses** — so the
      derivation is unambiguous at every repeat count and `repeats`' **length** is what decides the
      path. `repeats` is derived from those same nested keys (and from `per_repeat`'s sub-keys, which
      hold the same labels); its **order is the record's, which is EXECUTION order under
      `order: randomized` and not a `summary` step's plan order** — say that in the docstring and
      **claim no ordering identity**, because only `len() > 1` is load-bearing.

- [ ] **Step 4: the withheld half, asserted by name.** A test asserting `ReportIO` has **no**
      `write`, `record`, `append`, `finalize` or `skip` attribute. **A positive arm cannot see this**,
      which is the *control asserting only absences* shape run backwards: pair it with the four
      members working.

- [ ] **Step 5: run, then mutate — and this is the batch's load-bearing mutation.** In the extracted
      traversal, change the repeat-segment rule (drop the `> 1` guard). Confirm **both** a `StepIO`
      test **and** a `ReportIO` test fail — that pair is the whole of Decision 4's anti-drift claim
      (M16). *Why the branches differ:* the one-repeat case collapses and the multi-repeat case does
      not, and both classes resolve through the same function. **A mutation that fails only the report
      side proves the extraction was a copy**, so report which tests failed, not how many. Also
      confirm task 17's **arm C still passes** at HEAD before you mutate and after you revert.

- [ ] **Step 6: commit.** `git commit -m "H8c task 2: ReportIO, and one artifact-tree traversal two
      classes call"`.

---

## Task 3: override discovery — the direct question, the window, and three refusals

**Surface: a direct call, driven from real projects on disk.** *This task is alone in its batch: it is
the slice's proxy risk, and both H7a fail-opens plus their follow-on came from answering "is this
local?" with something correlated.*

**Files:**
- Source: `src/publishable/report.py`
- Test: `tests/test_report.py`

**Interfaces:**
- Produces: a discovery function returning the resolved `BaseReport` subclass or `None`, **and doing
  the whole render inside its own `sys.path` window** (the render callable is passed in; tasks 5–7
  supply it).
- Consumes: `base_experiment.load_experiment`'s rule, `environment/repo_root.txt`.

**The direct question, stated as a question with one answer.** *The run record's embedded
`config.entrypoint` is an import path `<module>:<attribute>`; its root package is this experiment's
package; the override is that package's `report` module, and the class is the `BaseReport` subclass
that module defines.* **Nothing else is consulted** — not a directory scan of `src/`, not a
module-name prefix, not a marker stamped on a class, not "does this file sit under this repo", and not
definition order among two subclasses.

**Where `repo_root` comes from, and why it cannot be walked up to.** `report <run.yaml>` is handed a
path inside `output_dir`, and **`output_dir` may never resolve inside the git repo** — the standing
invariant, checked at generate, at validate, and by every command that executes. A walk-up therefore
answers *"is there a repo above `output_dir`"*, a different question; measured at `ebf642a`,
`find_repo_root` **raises `E-GIT-NO-REPO`** when there is none. The fact is
**`environment/repo_root.txt`**, the one-line run-start artifact H8b introduced for the structurally
identical problem in `freeze`, read from the run directory. **`provenance.git.repo_root` is not
used**: it is the same value recorded at run end, `study add` redacts it, and two sources for one fact
is how the two drift.

- [ ] **Step 1: read the repo root, and check its shape.** H8b's whole-branch fix round found that an
      unchecked `repo_root.txt` let a bogus or non-directory path fall through to a **coded but
      wrong-remedy** diagnostic. Missing, empty, or not a directory is a refusal with the right
      remedy, not a silent "no override".

- [ ] **Step 2: resolve the module through the same window `load_experiment` uses.** Purge the root
      package and its submodules from `sys.modules` first — `load_experiment`'s own docstring gives
      the reason, *"two projects in one process can declare the same package name"*, and this repo's
      suite runs many projects in one process off a scaffold whose package name is stable. Insert
      `<repo_root>/src` on `sys.path`, import `<root_pkg>.report`, take the class, **perform the whole
      render**, and pop `sys.path` in a `finally`. **Rendering inside the window is the part that is
      easy to get wrong and cheap to get right**: a `sections` body that lazily imported a sibling
      module at render time would fail after the pop — H7a's *state read at the wrong moment* in a new
      costume. **Say whether discovery CALLS `load_experiment` or re-implements its window**, and rule
      it here rather than leaving it to a reader of the diff: discovery needs `<root_pkg>.report`, not
      the entrypoint attribute, so it re-implements the window **by calling the same two steps in the
      same order** and states that in its docstring — which means it does **not** inherit
      `E-ENTRYPOINT-IMPORT`. So handle the embedded `entrypoint` being **absent, empty, or not a
      `str`** explicitly: a hand-edited record can hold any of the three, and a `None` reaching
      `.partition` is a traceback rather than a diagnostic. Route it to a refusal with a remedy, not to
      "no override" — that would be the fail-open this task exists to avoid.

- [ ] **Step 3: the three refusals, none of them a fail-open.** No `report` module → **no override**,
      standard sections only (the ordinary case: `generate report` is opt-in). A `report` module that
      **raises on import** → `E-REPORT-OVERRIDE-IMPORT`, never "no override" — distinguish the
      module's absence from its failure by the import machinery's own answer, not by catching
      everything. **No** `BaseReport` subclass, or **more than one** → `E-REPORT-OVERRIDE-CLASS`;
      "more than one" is refused rather than resolved by definition order, because definition order is
      exactly the proxy this task forbids and a project has one report. Write **both** § Errors rows
      in this commit (§ Corrections, correction 6).

- [ ] **Step 4: `report <study.yaml>` performs NO discovery.** Stated here, enforced in task 10: a
      bundle sits outside every experiment repo by construction, carries records rather than run
      directories, and has `provenance.git.repo_root` redacted out of every one of them. There is no
      repo, no `repo_root.txt`, and no `src/**` for `code_hash` to cover. This is a rule with grounds,
      not a limitation.

- [ ] **Step 5: run, then mutate — four, and read each failure.**
      **M1** — discover by scanning `src/*/report.py` instead of from `entrypoint`. Caught by Fixture
      O's assertion on **which** titled section appears. *Why the branches differ:* two packages, two
      distinct titles, one named by `entrypoint`; a scan finds both and must pick, and any pick is
      observable. **On a one-package project the branches are identical, which is why the fixture has
      two.**
      **M2** — read `repo_root` from `provenance.git.repo_root` instead of the file. Caught by an
      arm whose record's `provenance.git.repo_root` is hand-edited to a path that exists and holds a
      *different* project. *Why the branches differ:* both branches find *a* repo, so an assertion on
      "an override was found" cannot see it — **the assertion is on the section title.**
      **M11** — perform the render **after** `sys.path` is restored. Caught by Fixture V, whose
      override **reads a condition artifact**. *Why the branches differ:* the module is imported either
      way; an override that yielded a constant string cannot see it.
      **M15 — this plan's addition, and the one no other fixture can see.** Delete the `sys.modules`
      purge (or narrow it to the bare root package, dropping `root_pkg + "."`). Caught by **Fixture
      O2**: two separate projects declaring the **same** package name, rendered in sequence in one
      process, each asserting its own section title. *Why the branches differ:* with the purge each
      render imports its own module; without it the second render is served the first's cached one. **On
      a fresh process with one project the branches are byte-identical**, which is why this arm exists.
      **One mutation deliberately NOT prescribed, with the reason:** replacing the `repo_root.txt` read
      with a walk-up. Measured at `ebf642a`, `find_repo_root` **raises** `E-GIT-NO-REPO` above an
      `output_dir` outside any repo, so that mutation is caught **by a crash rather than by the
      property** — H8a's batch-2 Major, where a guard whose only fixture crashes is a guard tested by
      accident. M2's hand-edited-record form is the one that discriminates.

- [ ] **Step 6: commit.** `git commit -m "H8c task 3: override discovery from the run's own
      entrypoint, inside one sys.path window"`.

---

## Task 4: `report`'s argument and form, and one record reader with two entries

**Surface: a direct call.**

**Files:**
- Source: `src/publishable/report.py`, `src/publishable/lineage.py`
- Test: `tests/test_report.py`, `tests/test_lineage.py`
- Docs: `docs/reference.md` (§ Errors `validate` reports — one new row, three widened)

**Interfaces:**
- Produces: form detection; `lineage.read_record_file(path)`.
- Consumes: `lineage.read_run_record`.

- [ ] **Step 1: the form, from the argument's file NAME and nothing else.** `run.yaml` is a run,
      `study.yaml` is a bundle, **any other name is refused** (`E-REPORT-FORM`), and a **directory** is
      refused too. Not by parsing the document and looking for a discriminating key, and not by
      `is_dir()` succeeding. **`diff._form` is not reused** — it answers "config or run record", a
      different question over a different document family, and reusing a predicate that answers a
      different question is the proxy substitution this repo has paid five wrong grounds for.
      `_record_dir`'s **rule** *is* reused in substance (a `run.yaml` path's run directory is its
      parent), because that is the same fact. A missing operand path stays `E-IO-FAILED` at exit `1`
      through `main`'s `OSError` handler, exactly as `diff`'s does — do not catch it here.

- [ ] **Step 2: extract `read_record_file`, because a bundle member is not `<dir>/run.yaml`.**
      Measured at `ebf642a`: `lineage.read_run_record(path)` takes the **run directory** and reads
      `path / "run.yaml"`, while § Building one's bundle tree holds `main.run.yaml`,
      `sensitivity.run.yaml` — bare files (§ Corrections, correction 1). Extract the parse-and-refuse
      body into `read_record_file(path)` and make `read_run_record(run_dir)` delegate with
      `run_dir / "run.yaml"`. **One refusal set, two entries** — `_nest_repeat`'s own docstring is the
      precedent. All three refusals must stay reachable **from both entries**, and the
      not-a-mapping-parses-to-a-list fault must still be distinguishable by **message** and not only
      by code: H8a's batch-1 review found two faults reaching one assertion, and *two faults reaching
      one assertion is the same defect as one code covering two faults*.

- [ ] **Step 3: reword the message that is now false, and widen the rows.**
      `E-UPSTREAM-RECORD-MISSING`'s message says *"the run never finished, or this is not a run
      directory"* — false of a bundle member, which is a file. Reword so it is true of both operand
      shapes, or carry the operand's own description; **prefer deleting the false half to inventing a
      new claim.** Then widen all three § Errors rows: the row already names `diff` as a second
      caller, and `report` and `study add` are the third and fourth. **§ Errors carries one row per
      code covering every emit site** — a row narrower than its code was the whole-branch Major on
      **both** preceding sub-slices, once in rows a task had just repaired three rows above.

- [ ] **Step 4: run, then mutate.** Mutation: make `read_record_file` accept a directory (append
      `run.yaml` unconditionally). Caught by a bundle-member read arm. *Why the branches differ:* a
      bundle member is a file, so the mutant looks for `main.run.yaml/run.yaml` and the honest code
      reads the file. Second mutation: decide the form by `is_dir()` instead of by name. Caught by the
      directory-refusal arm **and** by an arm passing a file named neither — one arm alone passes under
      one wrong answer.

- [ ] **Step 5: commit.** `git commit -m "H8c task 4: report's form by file name, and a record reader
      a bundle member can use"`.

---

## Task 5: the Conditions and Deltas sections

**Surface: a direct call over Fixtures R and D.**

**Files:**
- Source: `src/publishable/report.py`
- Test: `tests/test_report.py`

- [ ] **Step 1: Conditions.** For each `results.conditions[]` entry: `index`, `label`, `values`,
      `is_baseline`; then for each step's `aggregated[step]`, every metric's `value`, `ci95`,
      `method`, `n`, **`basis`, `correction` and `repeat_spread`**; then the `by[attribute][level]`
      strata when `statistics.report_by` was declared. **`repeat_spread` is in the record and is not in
      the design's list** (§ Corrections, correction 8): `CLAUDE.md`'s invariant makes it the
      designated home of repeat dispersion — *"repeat dispersion is reported separately as
      `repeat_spread`"* — so a Conditions section that dropped it would drop the only place a reader
      sees it. Measured: a `by` stratum entry carries **no** `repeat_spread`, so the renderer must not
      require one.

- [ ] **Step 2: `by` is not a metric name, and the exclusion comes from
      `stats.RESERVED_METRIC_NAMES`, never from a literal.** `aggregated[step]` holds the strata block
      under the key `by`, **as a sibling of the metric names**, so a section iterating that mapping's
      keys as metrics renders a strata block as a metric with no value. This is not a new hazard: S4d
      filed it after `cli._compute_one_contrast` differenced `by` as though it were a metric, and
      `_comparison_step_blocks` already excludes it at that choke point. The filing's own opening
      sentence is *"every consumer of a step block reads its keys as metric names"* — **`report` is the
      next consumer and inherits the obligation.** Import the frozenset.

- [ ] **Step 3: Deltas reads `results.contrasts` AS WELL AS `vs_baseline`.** Measured: `command_run`
      splits `resolve_contrasts`'s output, sending undeclared comparisons to each condition's
      `vs_baseline` and declared `statistics.contrasts` entries to a **top-level `results.contrasts`**.
      A section reading only `vs_baseline` silently omits every declared contrast — and § The two
      files' `run.yaml` example shows `vs_baseline` and no `contrasts`, so **the reading that produces
      the bug is the one a reader of that example reaches first.** Render `delta`, `method`, `paired`,
      `ci95`, `ci95_corrected`, `correction`, `correction_level`, and whichever of `n_paired` /
      `n_of`+`n_against` / `n_paired_clusters` / `n_paired_effective` / `weighted_by` / `cohens_d` /
      `cohens_ds` / `p_value` / `p_value_corrected` the entry carries. **`n_paired` is ABSENT rather
      than `null` on an unpaired entry** (H4c's conditional write, because `0` already means *pairing
      failed*), so key presence decides what prints, never a `None` test.

- [ ] **Step 4: the family line, once per family.** Every entry records `family_size` and
      `family: {comparisons, metrics}` — measured, and this is the one place a reader of a finished run
      can see why every interval widened. `validate`'s `W-STATS-FAMILY` is the warning, before the run;
      `report` is where the consequence becomes legible after it, and **`report` reads: nothing is
      computed and nothing warns.** Read `family` as a **mapping**, never by its two literal keys:
      measured, a *hypothesis* family's `family` is `{hypotheses: N}` — a different shape — and a
      renderer keyed on `comparisons`/`metrics` would fail on it the day the two renderers share a
      helper (§ Corrections, correction 9).

- [ ] **Step 5: run, then mutate.**
      **M4** — drop `results.contrasts` from the section. Caught by **Fixture D**. *Why the branches
      differ:* Fixture R has no declared contrast, so **the branches are identical there**; D is the
      only fixture on which they differ.
      **M13** — iterate `aggregated[step]`'s keys as the metric set without the exclusion. Caught by
      an assertion that the rendered metric names are **exactly** the record's real ones. *Why the
      branches differ:* Fixture R declares `report_by: [cohort]`, so its `aggregated[step]` genuinely
      holds a `by` key beside `score`; **without the strata declared the branches are identical.**
      **The `repeat_spread` mutation** — drop it from the rendered entry. Caught by an assertion on the
      rendered text. *Why the branches differ:* the record carries it and nothing else in the section
      prints its value.
      **Carried in from task 1 by name:** build M14's render-level arm here — an override that mutates
      a standard section's mapping `body` before yielding it, asserting the rendered figure is the
      record's. Task 1 could not write it because no standard section existed yet. **A finding routed
      to a task does not reach it unless the brief carries it** — this is the carry, and your report
      must say whether you built it.

- [ ] **Step 6: commit.** `git commit -m "H8c task 5: the Conditions and Deltas sections, contrasts
      and strata included"`.

---

## Task 6: the Hypothesis-verdicts and Attrition sections

**Surface: a direct call over Fixture R.**

**Files:**
- Source: `src/publishable/report.py`
- Test: `tests/test_report.py`
- Docs: `docs/superpowers/spec-defects.md` (one new filing)

- [ ] **Step 1: Hypothesis verdicts.** `results.hypotheses[]`'s `id`, `kind`, `declared_in`,
      `observed`, `verdict_evaluated_on`, `supported`, `verdict_rests_on` — **and `family_size` and
      `family`, which are in the record and not in the design's list** (§ Corrections, correction 9).
      `verdict_rests_on` distinguishes `computed` from `reported`, which is the whole point of § The
      unit table is the inference base's rule that the one interval core stores without computing is
      an `Estimate` a `summary` step returned.

- [ ] **Step 2: Attrition.** `provenance.units.n`; each metric's own
      `n: {resolved, completed, ineligible, failed}`; `execution`'s per-execution `status`, walked
      through all three of `shared`, `conditions[]` (with the repeat nesting) and `summary`; the
      top-level `status`; and `provenance.input_manifest_changed` — measured to be a **list**, so
      render what it holds rather than a boolean.

- [ ] **Step 3: the Attrition section does NOT claim `nondeterministic`, and this is the filing.**
      Measured at `ebf642a`: `nondeterministic` appears **zero** times in a real `run.yaml` and **zero**
      times in `executions.jsonl`; it exists only as a `BaseStep` class attribute and as what
      `W-REPL-DETERMINISTIC` reads off the classes at `validate`. Meanwhile § The two files' `run.yaml`
      example shows it on every repeat-scoped execution entry and `design-principles.md` § Not
      bit-identical reruns says core *"records that in `run.yaml` and notes it in `report`"*. **A
      section printing `nondeterministic: false` for every execution would be reporting a default
      nothing measured.** File it in `docs/superpowers/spec-defects.md` as a real entry — **a ledger
      line saying "filed" is not a filing** — with: the measurement and its date and commit; the two
      document passages; **Owner: unassigned**, and *why H8c and H4 are both the wrong owner* (nothing
      in H8c may alter a run, and the H4 family is complete, so naming either would point the entry at
      a slice that will not claim it); the check its owner must make (whether `run` owes an emitter, or
      whether `design-principles.md`'s *"notes it in `report`"* is the sentence that should go); and
      **which section it lands in on the day the field is written.** Note that this is **not** covered
      by the existing "Six `provenance` and `results` keys" filing, which is about `provenance` and
      `results` and names H6's three remaining keys.

- [ ] **Step 4: run, then mutate.** Mutation: walk only `execution.conditions` and skip `shared` and
      `summary`. Caught by an arm whose run has a `summary` step — Fixture R does — asserting its
      execution appears. *Why the branches differ:* the record holds three nesting shapes and the
      mutant reads one. Second mutation: read `provenance.input_manifest_changed` as a boolean.
      Caught by an assertion on the rendered text for a record whose value is an empty list, which is
      **not** the same rendering as `false`.

- [ ] **Step 5: commit.** `git commit -m "H8c task 6: the verdict and attrition sections, and the
      nondeterministic filing"`.

---

## Task 7: two renderers over one section stream

**Surface: a direct call.**

**Files:**
- Source: `src/publishable/report.py`
- Test: `tests/test_report.py`

- [ ] **Step 1: one stream, two emitters.** A markdown renderer and an HTML renderer, selected by the
      report class's `format`. **Both consume the same generator.** A section's `body` is markdown text
      or a mapping core tables; the renderers differ only in how they emit a heading, a table and a
      block. **No third representation and no template language.**

- [ ] **Step 2: `E-REPORT-FORMAT`.** A resolved report class declaring no `format` is refused at
      render, exit `1`, not silently defaulted. Write its § Errors row in this commit.

- [ ] **Step 3: HTML is self-contained and offline.** A bundle render is explicitly offline
      (*"`publishable report study.yaml` renders it offline"*), so the HTML carries no external
      stylesheet, script or font, and an override that embeds a figure embeds it. Assert the emitted
      HTML contains no external reference — and make the assertion **able to fail** by checking it
      against a string you know is present.

- [ ] **Step 4: `report` takes no format argument, and this is an invariant not a preference.** An
      operation command takes paths and nothing else; a `--format` on `report` would be the
      behaviour-changing flag § Everything is in the file forbids. The medium is a property of the
      experiment's own committed code, under `code_hash`. Task 15's `generate report --format` seeds
      the attribute and does not afterwards own it, exactly as `--input-dir` seeds a config field.

- [ ] **Step 5: pin the section ORDER from the render, and read why this is not a mutation.** Assert
      the four standard section titles' order in the **rendered text** of Fixture R. **Do not prove
      order by reordering `BaseReport.sections`'s yields** — that is *the thing under test iterating
      itself*, the shape a recent slice shipped where removing a member moved the expectation and the
      actual together and the second assertion went vacuous under every mutation. Said here rather
      than left as a silent gap, because **a mutation that changes nothing is evidence about the tests
      and not about the code.**

- [ ] **Step 6: run, then mutate.** **M10** — give `format` a base default of `"markdown"`. Caught by
      Fixture O's no-`format` arm asserting `E-REPORT-FORMAT`. *Why the branches differ:* with a
      default the arm renders markdown at exit 0; without one it refuses, and the class genuinely
      declares nothing so both branches read the same input.

- [ ] **Step 7: commit.** `git commit -m "H8c task 7: the markdown and HTML renderers, and the
      format refusal"`.

---

## Task 8: `report <run.yaml>` end to end, exit 0 on `partial`, and the CLI arm

**Surface: a real command, through `main(["report", …])`. Every assertion in this task goes through
it.** H7d Part A's only Critical was **invisible to every direct-call probe** and surfaced only
through an end-to-end run, and every direct-call probe there hand-built the maps and so never reached
it. **No assertion in this task may be made by calling `command_report` directly.**

**Files:**
- Source: `src/publishable/report.py`, `src/publishable/cli.py`
- Test: `tests/test_report.py`
- Docs: `docs/reference.md` (§ Operation commands' `report` row `Status` cell)

- [ ] **Step 1: the CLI arm, the constant key and the `Status` cell — ONE commit.** Add `"report"` to
      `OPERATION_COMMANDS` (it takes exactly one path and no flags, which is that arm's existing rule
      and needs no second enforcer), remove it from `NOT_BUILT_COMMANDS`, and flip § Operation
      commands' `report` row to `built`. **The built branches of `_dispatch` precede the
      `NOT_BUILT_COMMANDS` lookup and `test_reference_cli_tables_match_what_the_cli_does` asserts both
      directions**, so an arm without the flip fails that test and a flip before the command works
      would dispatch a command that renders nothing (§ Corrections, correction 5). Note what that test
      does: it invokes `main(["report", "_probe_a", "_probe_b"])` and asserts only that neither
      `unknown command` nor the not-built diagnostic appears — the arity refusal is what it sees.
      **`OPERATION_COMMANDS`'s literal VALUE is quoted outside `cli.py`.** H8b's own corrections named
      two such sites when `freeze` joined the set — `artifacts.build_allocation_document`'s docstring
      and `reference.md` § Resuming — and *repairing an instance of a shape does not immunize the next
      one* is in both ledgers. **Grep for the quoted literal across `src/`, `tests/` and the four
      documents named individually, and report what you grepped rather than a count.** Then check
      whether anything **reads** `OPERATION_COMMANDS` beyond `_dispatch`'s arity rule: if any site
      branches on membership, adding `report` is a **behaviour change** rather than a dispatch change,
      and it must be pinned as one.

- [ ] **Step 2: any status renders at exit 0.** `completed`, `partial`, `failed` alike, with the
      status printed in the Attrition section and the failed executions enumerated there. § Exit codes
      is explicit and is the one code it disambiguates for `report`: *"`report` of a `partial` run
      exits `0` — it was asked to render a record and it rendered one, with the failures shown."* `3`
      and `4` belong to the commands that execute, which those rows' own text says. **`report` exits
      `1` only for its own refusals and `2` only for an invocation fault.** Consistency with H8b is
      stated rather than assumed: `diff`'s Decision 4 ruled **0 whenever it rendered**, leaning on this
      very row as its precedent, and the two now agree in both directions for one reason — **a read
      command's exit code reports whether it could read, never what it read.**

- [ ] **Step 3: user code runs here, so wire redaction — and this is a decision the design did not
      make (§ Corrections, correction 7).** `report` is the **third** core command to execute user
      code (a resolver was H7b Part B's, a probe was H8b's), and `main`'s
      `except PublishableError` prints `f"  error   {exc.code:<20} {exc}"` **with no collector in
      scope**, which `spec-defects.md` already files as un-redacted by construction. Every diagnostic
      this command prints for a user-code fault — the override's import and the render — goes through a
      **fresh `Collector` carrying `credentials`**, populated by `freeze`'s own shipped recipe:
      `validate.declared_credential_names_for(doc, template)` over the record's embedded config and
      the template resolved through `templates.registry.get_template(name, repo_root)`, then
      `secrets.credential_values(names)`. **`report` does NOT call `load_env`** — it executes nothing
      metered and needs no credential — so the set it can redact is what the process environment
      already holds for a declared name; say that in the docstring and **claim no more**, because a
      value core never read cannot be redacted by name-matching. **Re-raise `KeyboardInterrupt` fresh
      and argument-less**, as H7b Part B's resolver path does, so Ctrl-C still stops the command
      carrying no message. **Enumerate the sites by READING where an exception can reach a stream,
      then confirm with greps** — the reverse order is what shipped H7c's leak, by the author of the
      rule forbidding it, while measuring for it.

- [ ] **Step 4: run, then mutate.**
      **M5** — return `EXIT_PARTIAL` from `report` on a `partial` record. Caught by Fixture P's
      exit-0 assertion. *Why the branches differ:* the record's `status` is genuinely `partial`, so
      both branches read the same input and return different codes.
      **The redaction mutation** — print `str(exc)` directly instead of through the collector. Caught
      by an arm whose override raises with a declared credential's value in the message, asserting the
      value is **absent** from stderr **and** that the coded diagnostic is **present**. *Why the
      branches differ:* one prints the value, the other prints `<redacted:NAME>`. **Pair the absence
      with the presence** — asserting only the absence passes identically if nothing ran, and build the
      **positive control that leaks the sentinel when redaction is unwired**, which is what H8b's
      whole-branch review required and got.
      **Fixture P asserts a pair, not a code** — exit 0 **and** the failed executions present by their
      own condition and repeat labels, read back from the record.

- [ ] **Step 5: commit.** `git commit -m "H8c task 8: report <run.yaml> end to end, exit 0 on
      partial, and its CLI arm"`.

---

## Task 9: the draft refusal, and the bundle's flag-not-refuse asymmetry

**Surface: a real command.**

**Files:**
- Source: `src/publishable/report.py`
- Test: `tests/test_report.py`
- Docs: `docs/reference.md` (§ Errors — one new row)

- [ ] **Step 1: `E-REPORT-DRAFT`, exit 1, and nothing rendered.** § Draft runs: *"Draft runs are
      recorded with `draft: true` and `git.code_dirty: true`, `report` refuses to render one as a final
      result, and `diff` labels it."* **It is a refusal, not a watermark** — the document's verb is
      "refuses", and a report that rendered a draft with a banner would be citable, which is the
      sentence the whole `draft`-versus-`--allow-dirty` argument rests on.

- [ ] **Step 2: testable today, reachable only later, and the fixture says so.** `draft: true` is a
      **shipped** key — measured, `draft: false` is written by `run` on every record — while the
      `draft` **command** is `NOT BUILT` and H9's. This is the *"an unbuilt reader of a shipped surface
      is a defect; of an unbuilt surface is specification"* line, on the shipped side. **Fixture T's
      docstring states that the record was hand-edited and why**, so nobody later reads it as a real
      draft run.

- [ ] **Step 3: a bundle FLAGS rather than refuses.** § Building one says the bundle render *"flag[s]
      any draft runs"*. A bundle is a set, and refusing a whole render because one of five runs was a
      draft would throw away four legitimate renders. So a bundle's per-run block renders with a
      `draft` label and the bundle-level exit stays `0`. **The asymmetry is the same one `code.commit`
      has:** a single run is one claim, a bundle is a set of them. **This task owns the label and the
      single-run refusal; the bundle arm is TASK 10's** — a bundle render does not exist yet, and a
      task cannot pin an arm against code that is not there. **Carry it into task 10's brief by name**,
      and say in your report that you did.

- [ ] **Step 4: run, then mutate.** **M6** — render a draft with a banner instead of refusing.
      Caught by Fixture T's run arm asserting exit 1 **and empty stdout**. *Why the branches differ:* a
      banner render exits 0 and prints sections; the refusal exits 1 and prints none. Asserting only
      the exit code would still catch it — **assert emptiness too**, which catches a refusal that
      prints first.

- [ ] **Step 5: commit.** `git commit -m "H8c task 9: report refuses a draft run, and a bundle flags
      one"`.

---

## Task 10: `report <study.yaml>` — the bundle render and its two cross-checks

**Surface: a real command.** *Alone in its batch: its review certifies a **negative** — that no
override discovery happens — and a batch that also built discovery would be certifying that against
itself.*

**Files:**
- Source: `src/publishable/report.py`
- Test: `tests/test_report.py`
- Docs: `docs/reference.md` (§ Errors — `E-STUDY-UNREADABLE`; § Warnings —
  `W-STUDY-COMMIT-MISMATCH`'s report-side surface if this task emits it)

- [ ] **Step 1: read the bundle.** `study.yaml`, its `runs` entries, and each member through
      `read_record_file` (task 4). `E-STUDY-UNREADABLE` when a `study.yaml` is absent, unparseable, not
      a mapping, or names a `runs` entry whose `file` is not in the bundle; a member that **is** there
      and is corrupt is `E-UPSTREAM-RECORD-UNREADABLE`, the shipped code — **two adjacent faults, two
      distinguishable answers**, stated here so no task guesses. Every reference is resolved
      **relative to the bundle directory** and nothing resolves outside it.

- [ ] **Step 2: the standard sections, and NO override discovery.** A bundle renders the four standard
      sections per member plus every declared hypothesis collected into one table, and **nothing
      else**. An override is one experiment's presentation, hashed under that experiment's commit, and
      a device-independent bundle deliberately has neither. Every standard section is a pure function
      of the parsed record, so a bundle needs no run directory — which is exactly why this works.
      **`sections(run, io)` still needs an `io`**, and the design rules none for a bundle: construct a
      `ReportIO` over the **bundle directory**. No override runs and no standard section touches `io`,
      so it is **unreachable in this form** — and **no task may claim it is exercised**
      (§ Corrections, correction 13).

- [ ] **Step 3: both cross-checks compare RECORDED figures and compute neither.** `report` calls
      neither `hashes.code_hash` nor `apparatus.apparatus_hash`.
      **`code_hash`:** recomputing it is impossible offline — it covers `src/**` and `templates/**` of
      a repo the bundle deliberately does not carry, and `reproduce` sets the precedent in words
      (*"It cannot verify a `code_hash` and says so, rather than reporting a match it never made"*).
      **`apparatus.hash`:** recomputing it *is* arithmetically possible from a record's own `facts`
      and is **still refused** — `apparatus_hash`'s own docstring requires a reader to re-canonicalize
      with exactly its `json.dumps` arguments, and `diff`'s Decision 2 already ruled that the
      `apparatus` row's verdict *"must not be able to disagree with the one figure this project treats
      as authoritative"*. **The apparatus is explicitly not a fourth hash** — it sits beside
      `uv_lock_hash` as an environment fingerprint, and a fingerprint two core commands can disagree
      about is worse than none.

- [ ] **Step 4: what the notices say, and what they may never say.** Two runs whose
      `provenance.git.commit` agree must have agreeing `code_hash` — same commit, same two trees — and
      when they do not, that is a real finding, reported as a **notice at exit 0**, not a refusal.
      **The notice says what was found and does not diagnose why:** *"these runs record commit X and
      their `code_hash` differs"* is checkable from the two records; *"one of them was a dirty tree"* is
      a guess, and a dirty tree is one candidate among an uncommitted `templates/**` edit and — the
      case `CLAUDE.md`'s invariant names precisely because people expect tree-scoping to be
      per-experiment and it is not — **another experiment's package moving inside the hashed trees**. A
      notice stating a cause as fact would be the comment-claiming-a-guarantee habit one layer out.
      The apparatus check is the same shape one column over, and **a run whose `provenance.apparatus`
      is `null` is EXCLUDED from it rather than counted as a mismatch**: "this experiment declares no
      probe" is not a deployment claim. `diff` makes the opposite call for a one-sided `null` and
      correctly — the two commands ask different questions, which `reference.md` § The apparatus core
      can only observe now records.

- [ ] **Step 5: RULE what the two notices are, because neither has an identifier today.** Decision 15
      mints `W-STUDY-COMMIT-MISMATCH` for `study add`'s commit notice, and **neither of the two notices
      this command prints appears in any table.** § Exit codes says *"Each diagnostic carries a stable
      identifier"*, and task 16's audit walks every `E-`/`W-` identifier raised **or reported** — which
      finds nothing at all if these are bare prints. **Decide, in writing, one of two ways:** mint two
      `W-` codes and write their § Warnings rows **in this commit**, or state why these are render
      *content* rather than diagnostics and why the identifier rule does not reach them. **Leaving it
      undecided is the row-narrower-than-its-code shape that was the whole-branch Major on both
      preceding sub-slices**, one step earlier.

- [ ] **Step 6: run, then mutate.**
      **M3** — recompute `apparatus_hash` over `facts` instead of comparing recorded `hash` strings.
      Caught by **Fixture A's hand-edited-hash arm**. *Why the branches differ:* on every honest record
      the recorded hash **equals** a recomputation — H8b's shipped
      `test_the_apparatus_hash_is_recomputable_from_the_recorded_facts` pins exactly that — so the
      branches are **identical** on Fixtures R and B, and only the edited record separates them.
      **The exclusion mutation** — count a `null` apparatus as a mismatch. Caught by Fixture A's
      fourth arm. *Why the branches differ:* one side has no `apparatus` block at all, and the other
      three arms cannot see it. **Refusing on a `null` apparatus would make every bundle of `generic`
      runs — the whole worked example — print a mismatch notice for a deployment nobody claimed.**
      **The discovery mutation** — perform override discovery on a bundle. Caught by an arm whose
      bundle sits beside a directory holding a `report.py`, asserting no extra section appears.

- [ ] **Step 7: Fixture T's bundle arm lands HERE, carried in from task 9 by name.** Task 9 owns the
      draft **label** and its single-run refusal; it cannot exercise a bundle render that does not yet
      exist. So the second arm — a bundle holding the hand-edited draft record, asserting **exit 0 with
      the run flagged** — is this task's, and it is the arm task 9's own decision cannot show alone.
      **Say in your report whether you built it**: a finding routed to a task does not reach it unless
      the brief carries it, which fell out of the chain on H8a and again on H8b.

- [ ] **Step 8: commit.** `git commit -m "H8c task 10: the bundle render, and two cross-checks over
      recorded figures"`.

---

## Task 11: `study new` — the bundle, outside any repo, refusing an existing one

**Surface: a real command.**

**Files:**
- Source: `src/publishable/study.py` (new), `src/publishable/cli.py`
- Test: `tests/test_study.py` (new)
- Docs: `docs/reference.md` (§ Creation commands' `study new` `Status` cell; § Errors — two new rows)

- [ ] **Step 1: `publishable study new <bundle> --title "..."`.** Writes `<bundle>/study.yaml` with
      `title`, `authors: []` and `runs: {}` — and **no `code` block**, because `code.commit` is a
      specific run's and there is no run yet. It is a **creation command**, so `--title` is legitimate:
      creation commands take what is needed to bring something into existence.

- [ ] **Step 2: the `study` arm in `_dispatch`, and it must not shadow `study add`.** Add a `study`
      arm handling `new`, **routing `add` to `_report_not_built("study add", …)` until task 13**, and
      answering a missing or unrecognized subcommand. The built branches precede the
      `NOT_BUILT_COMMANDS` lookup, so an arm that swallowed `study add` while its `Status` cell still
      read `NOT BUILT` fails the CLI-table test (§ Corrections, correction 5). **Parse `--title`
      explicitly and refuse its absence at exit 2 BEFORE anything reaches disk:**
      `test_reference_cli_tables_match_what_the_cli_does` invokes
      `main(["study", "new", "_probe_a", "_probe_b"])` **inside this repository**, which is
      `generate template`'s own stated reason for checking arity first — *"a generator that wrote
      first would scaffold … into the working tree"*. **An unrecognized option is REFUSED at exit 2,
      and this plan rules it rather than leaving it to a coin flip.** `_dispatch_generate` silently
      accepts and drops one, and that behaviour must not be inherited here: a typo'd `--titel` would
      write a bundle carrying the wrong title, and `E-STUDY-EXISTS` then refuses to correct it —
      a creation command's refusal to overwrite turns a silently-dropped flag into an unrecoverable
      one. Pin the refusal with an arm.

- [ ] **Step 3: `E-STUDY-IN-REPO`.** A bundle path resolving inside a git repo is refused — § Why not
      in the repo gives three structural arguments, so the check is structural too, using the same
      walk-up `input_dir`/`output_dir` already use. **Measured at `ebf642a`: `find_repo_root` RAISES
      `E-GIT-NO-REPO` when there is none**, so the check is "the walk-up **succeeded**", with that one
      code caught as the pass branch — **catch that code specifically and let every other
      `ContractError` propagate** (§ Corrections, correction 12). The route goes in the message: put it
      where the manuscript lives.

- [ ] **Step 4: `E-STUDY-EXISTS`.** `study new` onto a path already holding a `study.yaml` is refused
      at exit `1`, joining the family § Exit codes already defines (`E-PROJECT-EXISTS`,
      `E-EXPERIMENT-EXISTS`, `E-STEP-EXISTS`, `E-TEMPLATE-EXISTS`) and matching `scaffold.py`'s shipped
      shape: refusing is how a creation command stays safe to re-run. **"Existing" means a
      `study.yaml` is already there** — not that the directory exists, since `~/papers/x/study` beside
      a manuscript is a directory a person may well have made first. Write both § Errors rows in this
      commit.

- [ ] **Step 5: run, then mutate.** Gates: mypy **51** source files, format **92** files. Mutation:
      treat an existing **directory** as "existing". Caught by an arm creating the directory first and
      asserting `study new` succeeds. *Why the branches differ:* the honest rule reads the file and the
      mutant reads the directory, and the arm supplies a directory with no file. Second mutation:
      check `E-STUDY-IN-REPO` **after** writing. Caught by an in-repo arm asserting **no `study.yaml`
      exists afterwards** — an exit-code assertion alone passes a build that refuses after writing.

- [ ] **Step 6: commit.** `git commit -m "H8c task 11: study new, outside any repo, refusing an
      existing bundle"`.

---

## Task 12: `study add` part 1 — the copy, the redaction, and the `code` block

**Surface: a real command.**

**Files:**
- Source: `src/publishable/study.py`
- Test: `tests/test_study.py`
- Docs: `docs/reference.md` (§ Warnings — `W-STUDY-COMMIT-MISMATCH`)

- [ ] **Step 1: the copy.** `publishable study add <bundle> <run.yaml> --as <name>` copies the record
      to `<bundle>/<name>.run.yaml` and adds `runs.<name>: {file, run_id}` to `study.yaml`. **The
      source is read through `read_record_file(path)`, task 4's file entry** — the argument names a
      file, and using the directory entry would re-append `run.yaml` to a path that already ends in it.
      **`report` uses the directory form instead, and that is not an inconsistency:** it needs the run
      directory anyway, for `environment/repo_root.txt` and for `ReportIO`, while `study add` needs the
      record and nothing else. **`study add` reads the record and never its directory**, which is
      Decision 14's reason 1 and is what keeps this a record-copying command.

- [ ] **Step 2: the four fields, and a marker that distinguishes redacted from never captured.**
      § What `study add` redacts requires *"a marker recording that a value existed and was removed, so
      a reader can distinguish 'redacted' from 'never captured'"*. So: a field **present** in the
      source becomes the literal marker; a field **absent or `null`** is **left exactly as it was**.
      **The distinction is carried by the two states themselves rather than by two marker strings**,
      because "never captured" is already spelled unambiguously in this format and has been since
      `apparatus: null` — minting a second marker would give one fact two spellings.
      **The table is four exercisable rows, not five, at this commit.** § What `study add` redacts
      names `data.input_dir`, `data.output_dir`, `provenance.git.repo_root`,
      `provenance.environment.hostname` and `provenance.input_manifest`. Measured at `ebf642a`:
      `provenance.environment` is `{manager, python_version, uv_lock, uv_lock_hash}` — **`hostname` is
      never written**, and it is **H6's**. So `hostname`'s rule is exercised only over a **synthesized**
      record whose docstring says so in those words. **The rule needs no special case:** `hostname`
      absent today is the "never captured" branch and becomes the "redacted" branch the day H6 writes
      it, with no code change.

- [ ] **Step 3: every hash stays, and this is asserted byte-equal to the source.**
      `input_manifest_hash` survives while `input_manifest`'s path does not, so a holder of the data
      can still verify it without the record disclosing where it lives. `parameters_hash` never
      covered the path fields and `code_hash` covers only the two trees, so **redaction disturbs no
      verification** — § What `study add` redacts' own closing argument, and the reason the redaction
      can be this blunt. **Nothing is redacted from `provenance.apparatus`, by design:** § The
      apparatus core can only observe makes a probe emit non-identifying facts precisely so that this
      table has no apparatus row.

- [ ] **Step 4: name the distinction, because the two words are the same.** **This is not
      `secrets.redact`.** That function matches credential *values* by substring anywhere in a string,
      for exception text. This is **field replacement at four known paths**. The mechanisms share
      nothing.

- [ ] **Step 5: `code.commit` names ONE run's commit.** Written on the **first** `study add` from that
      run's `provenance.git.commit`, with `code.remote` from `provenance.git.remote`. A later
      `study add --as main` **replaces** it; a later add under any other name does not. The grounds are
      the section's own: *"`code.commit` is one commit and a study's runs need not share one … `code`
      is the citable pointer a reader follows from the paper, not a claim that every run came from
      it."* **`code.remote` is `null` when the run's own is** — a bundle inventing one would be a claim
      about where code lives that nobody made. **A commit mismatch is a notice**
      (`W-STUDY-COMMIT-MISMATCH`), exit unchanged at `0`, naming both commits and which run each
      belongs to: a sensitivity analysis rerun a month later at a later commit is ordinary, and
      refusing it would make the ordinary workflow impossible.

- [ ] **Step 6: run, then mutate.** Mutation: write the marker for an **absent** field too. Caught by
      Fixture Y's assertion that `provenance.environment` carries **no `hostname` key** afterwards.
      *Why the branches differ:* the source record has no such key, so one branch adds one and the
      other does not — and this is the assertion that keeps "redacted" and "never captured"
      distinguishable. Second mutation: recompute `code.commit` as "the commit all runs share". Caught
      by Fixture B's third run. *Why the branches differ:* two commits, so the mutant has no answer
      while the honest code keeps the first.

- [ ] **Step 7: commit.** `git commit -m "H8c task 12: study add copies, redacts four fields, and
      names one run's commit"`.

---

## Task 13: `study add` part 2 — the duplicate-name refusal, before any write

**Surface: a real command.**

**Files:**
- Source: `src/publishable/study.py`, `src/publishable/cli.py`
- Test: `tests/test_study.py`, `tests/test_cli.py` (one shipped test edited)
- Docs: `docs/reference.md` (§ Creation commands' `study add` `Status` cell; § Errors — one new row)

- [ ] **Step 1: `E-STUDY-NAME-EXISTS`, exit 1, and it is the load-bearing refusal of the command.**
      § Building one: *"what it refuses is a **name already in the bundle**, since `main.run.yaml`
      silently becoming a different run is exactly the overwrite [append-only] forbids, and a bundle
      beside a manuscript is the last place to allow it. Re-add under a new name, or start a new
      bundle."* **Both routes go in the message.**

- [ ] **Step 2: two checks, not one, and both BEFORE any write.** The name is checked against
      `study.yaml`'s `runs` keys **and** against the file on disk, because the two can disagree — a
      hand-edited `study.yaml`, or a copy interrupted between the two writes — and **the file is the
      thing whose overwrite loses data.** **Adding the same `run_id` twice under two names is
      permitted:** the refusal is about the name, a paper legitimately reports one run in two roles,
      and inventing a second refusal would be core deciding what a paper may say.

- [ ] **Step 3: the `study` arm completes, and two shipped things move with it.** Remove
      `"study add"` from `NOT_BUILT_COMMANDS`, flip § Creation commands' `study add` cell, and — because
      **both** subcommands are now built — handle `publishable study` with no subcommand **in the arm
      itself**: `_dispatch`'s `any(n.startswith("study "))` fallback now matches nothing, so without
      this the group prints the `unknown command` diagnostic, which is the one wrong word for a group the
      document specifies. **Edit the shipped
      `test_a_command_group_answers_for_its_unbuilt_subcommands`**: its docstring premise — *"every
      subcommand it could name is unbuilt"* — is now false, so it becomes a usage assertion naming both
      subcommands, at exit `2` (§ Corrections, correction 4). **Prefer deleting the false claim to
      rewriting it** where the sentence has nothing true left to say, and re-read the whole docstring
      when you touch it.

- [ ] **Step 4: run, then mutate.** **M9** — let `study add` overwrite an existing name. Caught by
      Fixture Y's re-add arm asserting **the file's bytes are unchanged** afterwards. *Why the branches
      differ:* the two runs differ, so an overwrite changes the bytes — **a name-set check alone would
      pass a build that refused after writing.** Second mutation: check only `study.yaml`'s keys, not
      the file. Caught by an arm whose `study.yaml` was hand-edited to drop the entry while the file
      remains. *Why the branches differ:* the two sources disagree by construction in that arm, and in
      no other.

- [ ] **Step 5: commit.** `git commit -m "H8c task 13: study add refuses a used name before writing,
      and the study group answers for itself"`.

---

## Task 14: the `min_reported_n` prompt — over the record's entries, and one branch nothing writes

**Surface: a real command.** *Split from task 13 by the design: the unreachable branch and its filing
are not the same work as the refusal.*

**Files:**
- Source: `src/publishable/study.py`
- Test: `tests/test_study.py`
- Docs: `docs/reference.md` (§ Errors — `E-STUDY-CONFIRM-REQUIRED`),
  `docs/superpowers/spec-defects.md` (one new filing)

- [ ] **Step 1: iterate the record's ENTRIES and key each on what that entry carries.** Not three
      shapes looked up in turn. An entry carrying `basis: "units"` is compared against `n.completed`;
      one carrying `reported: true` against the declared `n`, and is **listed unconditionally when `n`
      is `null`**; one carrying `basis: "repeats"` against the repeat count. **Iterating shapes instead
      of entries silently skips whatever the record actually holds — including `by` strata and
      `vs_baseline`, which is where the disclosure risk is highest.**

- [ ] **Step 2: the third branch ships behind a synthesized record, and the fixture says so.**
      Measured at `ebf642a`: `grep -n '"basis"'` over `src/publishable/` returns emit sites that **all
      write `"units"`**; a step-returned scalar reaches `per_repeat` and gets **no `aggregated` entry
      at all** (measured on a run with a unit table present), and a run with `data.units` undeclared
      writes **no `aggregated` key whatsoever**. So `reference.md`'s present-tense passages asserting
      that such a metric *"says `basis: repeats`, reports the spread, and omits `ci95`"* describe a
      shape core does not produce, and the **shipped** `W-HYPOTHESIS-INFERENCE-BASE` names it in its own
      message. **Build the branch, from the document, and pin it on a record synthesized by hand whose
      docstring says it was**, names the measurement, and cites the filing. The alternative — omit the
      branch until a producer exists — would ship a prompt that silently under-reports the day the
      producer lands, in the command whose entire job is to catch a disclosure nobody else will. **No
      task may claim the shape is producible.**

- [ ] **Step 3: file it.** `docs/superpowers/spec-defects.md` gains a real entry — **a ledger line
      saying "filed" is not a filing** — carrying: the measurement, dated and pinned to `ebf642a`; the
      affected `reference.md` passages **named by section**, plus `W-HYPOTHESIS-INFERENCE-BASE`'s own
      message; **Owner: unassigned**, with *why H8c and H4 are both wrong* (writing a metric into
      `aggregated` is `run`'s work and nothing in H8c may alter a run; the H4 family is complete, so
      naming it would point the entry at a closed slice — the exact re-owning failure `CLAUDE.md`
      records); and **the check to run before dispositioning it**: whether
      `W-HYPOTHESIS-INFERENCE-BASE`'s message can be true of any record this build writes. **It cannot
      be, today.** State the question rather than pre-deciding it: *is the documented shape the
      intended one (and `run` owes an emitter), or has the design moved to "a step-returned scalar
      lives in `per_repeat` and nowhere else" (and those passages owe a rewrite)?*

- [ ] **Step 4: what the prompt is, and what it may never be.** It prints the offending metrics and
      asks proceed-or-quit. Nothing else. `design-principles.md` § Everything is in the file: *"every
      one of those prompts is proceed-or-quit: a pause may never alter the config … Pausing changes
      what a person sees, never what executes."* Here there is no config and nothing executes, and the
      rule binds one step further: **quitting writes nothing** — not a partial copy, not a `study.yaml`
      entry — and proceeding writes exactly what a bundle with no thin metric would have written. **The
      prompt changes no bytes either way.** With no TTY it does **not** silently proceed:
      `E-STUDY-CONFIRM-REQUIRED`, because an unattended `study add` that proceeded past a disclosure
      warning is the automation this prompt exists to prevent.

- [ ] **Step 5: the floor is the bundled record's own.** `limits.min_reported_n` is read from the
      **record's embedded config**, never from a config in the working directory, because the limit is
      a property of the run being bundled. Measured at `ebf642a`: `init` materializes
      `min_reported_n: 10`, so the field exists in every scaffolded config and the fixture sets it
      rather than inventing it.

- [ ] **Step 6: run, then mutate.**
      **M7** — list every metric. Caught by Fixture N's **proper-subset** assertion. *Why the branches
      differ:* the floor is chosen — **read back from the record, not guessed** — so the `by` strata
      fall below it and the whole-condition metric does not, making "all" and "the thin ones" different
      lists.
      **M8** — proceed silently with no TTY. Caught by the non-TTY arm asserting
      `E-STUDY-CONFIRM-REQUIRED` **and that the bundle holds no new file**. *Why the branches differ:*
      a written record versus a refusal — **asserting only the code would pass a build that refused
      after copying.**
      **M12** — compare against a working-directory config's floor. Caught by an arm **run from a
      directory holding a config with a different floor**. *Why the branches differ:* two floors, two
      lists; **one floor makes the branches identical**, so the arm supplies two.

- [ ] **Step 7: the join — one end-to-end arm, because NO batch owns it otherwise.** Task 10 renders
      bundles that **Fixture B hand-builds**, and tasks 11–14 write bundles that nothing renders. B6
      certifies a reader against synthetic bytes and B7 a writer against no reader, so **a shape
      mismatch between them is invisible to both reviews.** That is exactly H8b's whole-branch Major —
      no batch owned what a config operand may contain, because one batch built the projection, another
      the reader and a third the hash call — and it surfaced only end to end. So: `study new`, then
      `study add` **twice**, then `report <study.yaml>`, **all through `main`**, asserting the render
      succeeds at exit `0` and names both runs. **Fixture B's docstring must say its bundle was
      hand-built and name this arm as the one that closes the loop**, so nobody reads a synthetic
      bundle as proof the writer and the reader agree.

- [ ] **Step 8: commit.** `git commit -m "H8c task 14: the min_reported_n prompt over the record's
      own entries, and the basis: repeats filing"`.

---

## Task 15: `generate report`, and the shipped table-parser assertion it moves

**Surface: a real command (`main(["generate", "report", …])`).**

**Files:**
- Source: `src/publishable/generators/report.py` (new), `src/publishable/cli.py`
- Test: `tests/test_cli.py` (one shipped test edited, plus new arms)
- Docs: `docs/reference.md` (§ Generators' `report` row, § Creation commands' `generate` cell,
  § Errors — one new row)

- [ ] **Step 1: `publishable g report <experiment> [--format html|markdown]`.** Writes
      `src/<pkg>/report.py` — the class § A report override shows, with the `format` line seeded. Reuse
      `generators.experiment.package_name` and `E-EXPERIMENT-UNKNOWN` for a missing package, exactly as
      `generate step` does. **`--format` writes the attribute and nothing else** — the class is the
      source of truth from then on, exactly as `--input-dir` seeds a config field it doesn't afterwards
      own. **Claimed here because nothing else claims it:** it is in `NOT_BUILT_GENERATORS`, § Generators
      marks it NOT BUILT, and it is not in H9's list — and it writes the class `BaseReport` exists to be
      subclassed from, so the alternative is shipping a base class with no writer.

- [ ] **Step 2: arity BEFORE anything reaches disk.** `test_reference_cli_tables_match_what_the_cli_does`
      probes every **built** generator with two junk positionals **inside this repository**, which is
      `generate template`'s own stated reason for checking arity first. One positional; anything else is
      exit `2` with a message citing § Generators.

- [ ] **Step 3: `E-REPORT-EXISTS`**, refusing an existing `src/<pkg>/report.py`, joining the same
      `E-*-EXISTS` family for the same reason as `study new`'s. Row in this commit.

- [ ] **Step 4: the scaffolded body must be runnable as-is**, on `generate step`'s and the starter
      step's precedent: it `yield from super().sections(run, io)` and yields nothing else, with a
      `TODO` marking the one place a figure goes. **A generated override that raised, or that rendered
      FEWER sections than no override at all, would make `generate report` a downgrade** — assert the
      generated file, imported through a real `report` run, renders the four standard sections.
      Everything it imports comes from `publishable` itself.

- [ ] **Step 5: the document cells and the shipped assertion, in this commit.** Flip § Generators'
      `report` row to `built`, remove the inline `` `report` (NOT BUILT) `` from § Creation commands'
      `generate` cell — **the shipped table-parser test asserts the tie between the cell and the
      Status column** — and remove `report` from `NOT_BUILT_GENERATORS`. **Then edit
      `test_reference_cli_tables_are_parsed_at_all`:** its per-table
      `statuses == {"built", "NOT BUILT"}` assertion goes **false for the Generator column** once its
      only `NOT BUILT` row flips (§ Corrections, correction 3). **You are that test's sole authorized
      editor and the post-edit state is stated in advance:** the per-table assertion becomes a
      **subset-and-non-empty** check, and a **row-presence pair for Generator** is added mirroring the
      Command table's — `("report", "built")` and one other row — so the vacuity control the test
      exists for survives. **Show the diff in your report, and change nothing else.** The set-equality
      checks against `NOT_BUILT_COMMANDS`/`NOT_BUILT_GENERATORS` stay exactly as they are: an empty
      set on both sides is still both directions.

- [ ] **Step 6: run, then mutate.** Gates: mypy **52** source files, format **93** files. Mutation:
      write the file before the existence check. Caught by an arm with a pre-existing `report.py`
      asserting its **bytes are unchanged**. *Why the branches differ:* the honest code never opens it
      for writing. Second mutation: drop the `yield from super().sections(...)` line from the scaffold.
      Caught by the four-standard-sections assertion on a generated override. *Why the branches
      differ:* the render is the observable, and an override yielding nothing renders nothing.

- [ ] **Step 7: commit.** `git commit -m "H8c task 15: generate report, and the table-parser
      assertion its Status flip moves"`.

---

## Task 16: the documents — homes, prose, the `allocation.json` ruling, and three worked blocks

**Surface: documents, plus one document-parsing test.** *Alone in its batch and REVIEWED. H8b
dispatched no review for its documents-and-codes task and **three of its four whole-branch Majors lived
in that one commit** — its ledger's own words: a documents-and-codes task looks like the safest one to
skip and is the one whose output no later batch reads, so nothing else will find its errors.*

**Files:**
- Docs: `README.md`, `docs/design-principles.md`, `docs/reference.md`, `CLAUDE.md`,
  `docs/feasibility-llm-growth-studies.md`, `docs/superpowers/spec-defects.md`
- Test: `tests/test_diff.py` (Fixture H)

- [ ] **Step 1: § Package layout's two markers come off.** `report.py` and `study.py` are both already
      in the tree block with `— not yet built` markers, glossed exactly as this slice built them.
      **No new module row is added and no gloss is rewritten** — `generators/` is one line with no
      per-kind rows, so `generators/report.py` needs none. **One gloss does owe a change:**
      `artifacts.py`'s enumerates the `io` members of the one class it held, and the module now holds a
      second (§ Corrections, correction 15). **Check every row the edit MOVED and every count phrase
      near it** — locating a row by position has been wrong twice in this repo, once in a row no diff
      touched.

- [ ] **Step 2: § A report override's `io` sentence.** *"`io` is the same read-only accessor a
      `summary` step gets"* is **false of the code** — a `summary`-scope `StepIO` carries `record`,
      `write`, `append`, `skip` and `finalize`. Replace it by naming `ReportIO`'s four members and
      saying they are the read half of one. **The document changes first**, rather than the code being
      bent to a sentence that was never true.

- [ ] **Step 3: § What `study add` redacts gains the `allocation.json` ruling and loses its hedge.**
      **A bundle never carries `allocation.json`, and no option is added to put it there.** The
      grounds, in the order they bind: § Building one's own shape decides it (`study add` takes a
      `run.yaml` **path**, and `allocation.json` is a run-*directory* artifact not reachable from that
      argument — admitting it would quietly turn a record-copying command into a directory-copying
      one); it is **the one run artifact that is a list of unit identities**, in the artifact most
      likely to be deposited publicly, and adding it would *create* a gap the table would then need a
      rule to close; **the hash is already in the bundle and discloses nothing** — `provenance.allocation`
      is a bare filename and `allocation_hash` a digest, both written whenever an arm assignment or
      holdout resolves; and **the route for a reader who wants to verify the split is named rather
      than left implicit** — one file the author attaches beside the bundle, with `allocation_hash`
      making the transfer checkable, which is exactly the posture the section already takes for
      `input_manifest`. Then delete the paragraph's closing *"is a question this slice leaves open for
      whichever slice builds `study.py`"* **and** its hedge clause, whose *"not yet built"* sits
      **inside a link to `#package-layout`** — so **grep the clause, not the phrase**, or your sweep
      finds nothing.

- [ ] **Step 4: § Exit codes' creation-command enumeration.** It lists `E-PROJECT-EXISTS`,
      `E-EXPERIMENT-EXISTS`, `E-STEP-EXISTS` and `E-TEMPLATE-EXISTS` **by hand**, under the claim that
      it is *"one rule shared by every generator with something to protect."* `E-STUDY-EXISTS` and
      `E-REPORT-EXISTS` make that enumeration incomplete — **the count-phrase-near-an-insertion trap in
      its normative form: the sentence is wrong the moment the codes exist and no mechanical check
      would catch it.** Both go in, and the sentence's own claim is what makes them belong.

- [ ] **Step 5: verify every code has a row, at every emit site.** Each earlier task wrote its own
      § Errors row (§ Corrections, correction 6). **Your job is the audit, not the writing:** for every
      `E-`/`W-` identifier raised or reported anywhere on this branch, confirm a row exists and that it
      covers **every** site — the `E-TEMPLATE-UNKNOWN` two-emit-sites shape. **Grep for the code, then
      READ where each is raised**; a grep for one spelling is the substitution that shipped H7c's
      credential leak.

- [ ] **Step 6: the three worked `diff` blocks each gain a header at that block's own level of
      concreteness.** The measured format, re-taken through the real console script at `ebf642a`:
      two-space column separators; the letter, the form, then a run record's `run_id` and `status`,
      with `draft` appended when `draft: true`; **and no blank line between the header and the first
      row** — measured, `command_diff` prints the two header lines and then the rows. **All three
      blocks are run-vs-run pairs with `completed` status**, so none needs the config-side shape (form
      plus the path as given, no status word). Three edits, not one, because each block sits at its own
      abstraction:

| Block | Header, at that block's concreteness |
|---|---|
| `reference.md` § The apparatus core can only observe | the worked example's real run IDs, each `completed` — and **`completed` beside `apparatus DIFFERS` is the pairing worth showing** rather than leaving a reader to wonder: an apparatus that moved between two *finished* runs is exactly what that block is about |
| `README.md` § The loop you'll actually live in | its own `run_A` / `run_B` level. **A run directory's name IS its `run_id`** — measured — so a block whose operands are `~/results/cohort-pilot/run_A/run.yaml` shows `run_A` in the identity column, and that is consistent rather than a placeholder in a real column |
| `design-principles.md` § Same code, different parameters | its `<run_a>` / `<run_b>` placeholders, unchanged in kind |

      **What must not change**, and this list is the filing's own: no hash prefix (`8e21`, `3d8a`,
      `6b1f`, `1a2b`), no run ID, no delta line, no row label, no row order, and the two-space
      separator stays. **§ The worked example's intervals are numerically checked and are not touched
      by this edit at all** — these blocks carry hashes and deltas, not intervals — stated so a later
      reader does not go looking for a narrowing that never happened. **Task 17's arm D is the proof:**
      it pins each block's rows from `code_hash` to the end of the fence as raw text, so if it passes
      after your edit, nothing at or below `code_hash` moved.

- [ ] **Step 7: Fixture H.** Extend `tests/test_diff.py`'s existing document-parsing row-label reader
      to the **header** lines rather than writing a second parser over the same three files, and compare
      against `diff`'s **real** output for a run pair: label set, label order, the two-space separator,
      and the header's own column shape. **Its parser reads INTO fenced blocks on purpose** — the
      mechanical consistency pass skips fences because these documents contain markdown inside markdown,
      and a later reader must not "fix" this parser to match. Say that in its docstring. Confirm the
      shipped `_document_row_labels` pins still pass unchanged: their regex requires
      `identical|DIFFERS` as the second field, which a header line does not have.

- [ ] **Step 8: close the filing, and strike rather than delete.** `spec-defects.md`'s
      *"OPEN — the three worked `diff` outputs predate the per-side header"* entry is closed by this
      task. **Strike it** — that file is a live list. **Re-read the whole entry first:** a filing's
      claims about the code go stale like any other comment, and this one's *"which already owns … the
      one `reference.md` sentence closing the `diff`-versus-gate ruling"* is **already stale** —
      H8b task 12 landed that sentence while editing the same section, which the design records under
      § What did not survive. **Do not re-land it.**

- [ ] **Step 9: `CLAUDE.md` and the dated § Executability entry.** Add H8c's development-record entry
      at the minting site, in the same shape the preceding slices' entries take, and **repeat the
      four-row table character for character** with the date matching its commit. **No fifth number.**
      **No counts in prose** — a stale count phrase in the H8b entry was a Minor on that branch and was
      closed by deleting the count rather than correcting it.

- [ ] **Step 10: both consistency passes, with every sweep proven able to fail.**
      **Mechanical**, in full over the four documents named individually: every relative link and
      `#anchor` resolves; no duplicate heading anchors; every table's rows match its header's column
      count and no row is empty; no trailing whitespace, tab or invisible unicode; **fenced blocks
      skipped throughout**; `×` not `x`; hyphens, never en dashes, in anything that becomes an anchor.
      **Cross-document**, the classes this slice moves: the **shared worked example** (step 6, pinned by
      arm D and Fixture H rather than promised); the **`Status` columns** — four cells flipped across
      tasks 8, 11, 13 and 15, plus § The importable surface's `BaseReport` row in task 1, whose
      neighbouring sentence **derives** its claim from the column and therefore needs no edit;
      **schema fields in prose** — `study.yaml`'s keys in § Building one's fenced block must match what
      `study new`/`study add` write, **in both directions** — and one expected non-match is named here
      so nobody "fixes" it: § Building one's fenced block shows a `code:` block, while `study new`
      writes **none** and the first `study add` is what adds it, because `code.commit` is a specific
      run's and there is no run yet. **Do not make `study new` write an empty one**; and **after removing a string, grep for
      what should no longer exist**, naming `CLAUDE.md` and the feasibility analysis too, since a
      paraphrase surviving in the analysis was H7d Part A's Major 1. **Never filter a sweep's
      output — filter the file list**, and run each sweep against a string known to be present first: a
      reviewer checking this exact rule lost a true hit to `grep -v superpowers` because the matching
      line contained that path. **Neither pass touches the development record.**

- [ ] **Step 11: run and commit.** Full suite green; gate literals unchanged from task 15's.
      `git commit -m "H8c task 16: homes, prose, the allocation.json ruling, and the three worked diff
      headers"`.

---

## Corrections against the code

**Appended by this plan's author and extended by no task.** Each was measured at `ebf642a`. The rule
is `CLAUDE.md`'s: *the plan argues from the spec, and the code outranks both; where they disagree the
code wins and the document changes first.* H8b's plan made ten corrections, H8a's ten, H7d Part A's
fourteen, and **six of six implementers on one recent slice found a real disagreement** — finding one
is expected, not exceptional.

**1. `lineage.read_run_record(path)` takes the run DIRECTORY, and a bundle member is not one.** The
design's § What H8c reuses lists `read_run_record(run_dir)` as imported by `report` and `study add`.
Measured: it reads `path / "run.yaml"`, while § Building one's bundle tree holds `main.run.yaml` —
bare files. **Task 4 extracts `read_record_file(path)` and makes `read_run_record` delegate**, on
`_nest_repeat`'s own "one rule, two callers" grounds. Two consequences the design does not rule:
`E-UPSTREAM-RECORD-MISSING`'s message *"this is not a run directory"* is **false of a bundle member**
and is reworded in the same commit; and the adjacent faults are separated in writing — a `runs` entry
whose `file` is absent from the bundle is `E-STUDY-UNREADABLE`, a member present but corrupt is
`E-UPSTREAM-RECORD-UNREADABLE`.

**2. `lineage.resolve_step` does NOT derive step scopes.** The design's Decision 4 says `step_scopes`
comes from *"the identical derivation `lineage.resolve_step` already performs over the same block."*
Measured: `resolve_step` resolves a **location** for `shared`/`summary` and **refuses** anything under
`conditions[]` with `E-UPSTREAM-STEP-SCOPED`, never distinguishing `condition` from `repeat` — which
is precisely the distinction `_nest_repeat` needs. Task 2 builds the derivation, with the measured
discriminator (`status` in the entry → `condition`; repeat-label keys → `repeat`) and the measured
one-repeat case (**the record nests, the directory collapses**).

**3. `test_reference_cli_tables_are_parsed_at_all` breaks when § Generators loses its only NOT BUILT
row.** Its per-table `statuses == {"built", "NOT BUILT"}` assertion goes false for the Generator
column. **Task 15 is its sole authorized editor**, with the post-edit state stated in advance and the
vacuity control preserved by a row-presence pair. The set-equality checks against the two `NOT_BUILT_*`
constants stay untouched — an empty set on both sides is still both directions.

**4. `test_a_command_group_answers_for_its_unbuilt_subcommands` breaks when both `study` subcommands
are built, and `_dispatch`'s group fallback stops matching.** The shipped test asserts
`main(["study"])` prints the not-built diagnostic under the premise *"every subcommand it could name is
unbuilt"*; once both leave `NOT_BUILT_COMMANDS`, `any(n.startswith("study "))` matches nothing and the
group would print `unknown command`. **Task 13 owns the arm's group-usage branch and the test's
edit.**

**5. The four `Status` cells cannot live in task 16.** `_dispatch`'s built branches precede the
`NOT_BUILT_COMMANDS` lookup and the CLI-table test asserts **both** directions, so arm, constant key
and document cell must land in one commit per command: `report` in task 8, `study new` in task 11,
`study add` in task 13, § Generators' in task 15. This is H8b's correction 1 re-derived against the
same code. **A further consequence the design does not name:** task 11's `study` arm must route `add`
to `_report_not_built` until task 13, or it shadows a row still marked `NOT BUILT`.

**6. Every code's § Errors row lands in the commit that first raises it, not in task 16.** **A § Errors
row narrower than its code was the whole-branch Major on both preceding sub-slices** — H8a's in rows a
task had just repaired three rows above, H8b's twice in codes its own decision explicitly reused — and
H8b's ledger records that **no review was dispatched for the task holding them.** Task 16 audits rather
than authors.

**7. `report` runs user code, and the design rules nothing about redaction.** `report` is the third
core command to execute user code; `main`'s `except PublishableError` prints with **no collector in
scope**, which `spec-defects.md` already files as un-redacted by construction. Both precedents wired
redaction (H7b Part B for a resolver's raise, H8b for `freeze`'s probe round). **Ruling: wire it**, by
`freeze`'s shipped recipe — `validate.declared_credential_names_for(doc, template)` over the record's
embedded config plus `secrets.credential_values` — for the run form; the bundle form runs no user code
and needs none. **`report` does not call `load_env`**, and the docstring must claim only what
name-matching over the process environment can deliver. Task 8 owns it, with a positive control.

**8. Decision 5's Conditions row is narrower than the record.** A metric entry also carries `basis`,
`correction` and **`repeat_spread`** — and `CLAUDE.md`'s invariant makes `repeat_spread` the designated
home of repeat dispersion, so omitting it would drop the only place a reader sees it. A `by` stratum
entry carries **no** `repeat_spread`, so the renderer must not require one.

**9. Decision 5's Hypothesis row is narrower than the record, and a family is not one shape.**
Verdict entries also carry `family_size` and `family` — and a hypothesis family's `family` is
**`{hypotheses: N}`**, not `{comparisons, metrics}`. A family renderer must read the mapping
generically, or it fails the day the two sections share a helper.

**10. `ReportIO.repeats`' order is the record's, which is EXECUTION order.** Measured: repeat labels
appear in `execution` in the order execution produced them, which under `order: randomized` is not the
plan order a `summary` step's `io.repeats` sees. Only `len() > 1` is load-bearing (it decides the path
segment), so the code is correct and the **claim** must be sized: task 2's docstring says where the
labels come from and asserts no ordering identity.

**11. `W-STEP-ESTIMATE-N`'s shipped message is re-read and judged STILL TRUE.** It says `study add`
*"cannot check what it cannot see"*, and Decision 13 lists such an `Estimate` unconditionally — which
is the **consequence** of not being able to check it, not a contradiction. Recorded so no task
"repairs" a true claim. **Prefer deleting a claim to rewriting it** applies only to false ones.

**12. `find_repo_root` RAISES `E-GIT-NO-REPO`; it does not return `None`.** Two consequences. The
walk-up form of Decision 3's repo-root mutation is **rejected as a mutation**: above an `output_dir`
outside any repo it is caught **by a crash rather than by the property**, which is H8a's batch-2 Major
(*a guard whose only fixture crashes is a guard tested by accident*). And `E-STUDY-IN-REPO` is
implemented as "the walk-up **succeeded**", catching that **one** code as the pass branch and letting
every other `ContractError` propagate.

**13. A bundle render still has to hand `sections` an `io`, and the design rules none.** Ruling:
construct `ReportIO` over the bundle directory. No override runs on a bundle and no standard section
touches `io`, so the object is **unreachable in that form** — and **no task may claim it is
exercised.** The device-independence assertion (the render opens no path outside the bundle) is what
covers it.

**14. `E-UPSTREAM-*` naming, kept rather than reminted.** `report` and `study add` become the third
and fourth callers of three codes whose names say "upstream". The design's ruling stands — minting a
fourth spelling of "this record will not read" is H4d's one-code-for-five-faults shape run backwards —
and the rows widen instead.

**15. Two document rows the design does not name.** § What you define's `BaseReport` row's `Core's`
cell names only the standard sections, while `self.section` and `__init__` are core's too (task 1).
And § Package layout's `artifacts.py` gloss enumerates the `io` members of the one class it held, while
the module now holds a second (task 16).

**16. The gate literals, computed.** mypy 49 → **50** (task 1) → **51** (task 11) → **52** (task 15).
`ruff format --check` 88 → **90** (task 1) → **92** (task 11) → **93** (task 15). Every task states a
**delta** on the test count and computes its absolute from its own previous run.

**17. `report`'s own two bundle-level notices need identifiers, and neither the design nor
Decision 15's table names them.** Decision 15 mints `W-STUDY-COMMIT-MISMATCH` for `study add`'s
own commit notice (a single run's `provenance.git.commit` against `code.commit`, at add time) —
a different notice from the two `report study.yaml` prints (a bundle-wide comparison among
runs that already share a commit). § Exit codes' rule — "each diagnostic carries a stable
identifier" — and task 16's audit of every `E-`/`W-` identifier **raised or reported** reach a
bare print exactly as they reach a raise; leaving these two unidentified is the row-narrower-
than-its-code shape both preceding sub-slices shipped as their whole-branch Major, one step
earlier than where it would have been found again here. **Ruling: mint two `W-` codes,**
`W-STUDY-CODE-HASH-MISMATCH` and `W-STUDY-APPARATUS-MISMATCH`, with their § Warnings rows
landing in task 10's own commit (correction 6's rule applies to a `W-` notice exactly as it
does to an `E-` refusal). Both stay warnings — they never raise, and a bundle render's exit
stays `0` regardless of what they find, on `W-APPARATUS-UNANSWERED`'s own precedent for a
notice that changes nothing about the command's own success.

---

## What could not be measured

- **`report` against a bundle assembled on another machine.** Every fixture builds its bundle locally,
  so the device-independence claim — *"every reference is relative, `run_id` is a label rather than a
  locator, and nothing resolves through the original output storage"* — is pinned by asserting the
  bundle's references are relative and that the render opens no path outside it, **not** by moving a
  bundle between machines. Said rather than claimed.
- **`provenance.environment.hostname`'s redaction against real output.** Never written (H6's), so that
  one row is exercised only over a synthesized record whose docstring says so.
- **A genuine `draft` run.** `publishable draft` is `NOT BUILT` and H9's; Fixture T's record is
  hand-edited from a real one and says so.
- **A metric with `basis: "repeats"`.** Nothing in this build writes one. The branch ships behind a
  synthesized record and a filing (task 14), and **no task may claim the shape is producible.**
- **What an override does with a `failed` run whose `results` are thin.** Fixture P covers `partial`; a
  run that stopped with almost nothing recorded renders whatever the record holds — the same code path
  — but no fixture exercises the degenerate end of it.
- **Whether the HTML renderer's output is correct HTML to a browser.** Asserted structurally (no
  external reference, well-formed enough to parse) and not by rendering.

---

## Plan self-review

- **Every claim about the code was measured at `ebf642a`, by reading the file or running the
  behaviour**, and `ebf642a` is one docs-only commit above the design's `9963841`, so the design's
  measurement shapes are reusable while its claims are re-checked. Sixteen corrections, two of which
  reshape a task (task 2's derivation, task 4's reader extraction) and three of which move work out of
  task 16.
- **No count phrase, positional row locator, call-site enumeration or line-number citation appears
  above.** Section citations only.
- **Every mutation names its assertion AND why its two branches can differ on the named fixture**, and
  **two are named as REJECTED with the reason**: the walk-up repo root (caught by a crash, not by the
  property) and reordering `BaseReport.sections`'s yields (the thing under test iterating itself).
- **One mutation and one fixture are this plan's additions, not the design's:** M15 and Fixture O2 —
  two projects declaring the same package name — because H7a's third fail-open was *state read at the
  wrong moment* and the design's fixture set cannot see the `sys.modules` purge.
- **The guard pin has one authorized editor for one arm, with the post-edit state stated in advance**,
  and arm D is deliberately written so that it needs **no** editor at all — a pin that cannot be
  legitimately edited is strictly better than one that can.
- **The four-row table is repeated unchanged and no fifth number appears.**
