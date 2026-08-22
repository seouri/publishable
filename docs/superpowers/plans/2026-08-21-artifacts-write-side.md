# H5a — write-side integrity and the reserved-column namespace — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to
> implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** everything that happens **before and during a write** to a per-unit table or a row-shaped
artifact — what a column may hold, what a column may be called, and what happens to a value on its
way into a cell. Two `reference.md` sections state rules the code already enforced and never wrote
down; one identifier is minted; the two row-shaped writers gain the scalar walk their own documented
contract already asked for; roster attribute values become guaranteed scalars; and three small guards
close asymmetries nothing filed. H5b owns everything downstream of a write that already works.

**H5a moves NO row of the four-row table**, and mints no fifth number. The 2026-08-20 correction in
[the feasibility analysis](../../feasibility-llm-growth-studies.md) § Executability on this build
ruled that a single figure answers no consistent question for that analysis. H8a replaced the number
with a table, H8b, H8c and H8a's successors repeated it unchanged, and **H5a repeats it unchanged
again — all four rows.**

| Figure | Count | Visible to `validate`? |
|---|---|---|
| Transplantable configs validating with zero errors | **8 of 8** | yes — the only figure `validate` can see |
| Blocked on `io.reuse_from` | **0** | no — the method ships; six configs still need the plugin body to call it |
| Meet the `report_by`-under-`resample` gap | **7** | no — **H4 Statistics'** gap, untouched here |
| Free of every core-side dependency this analysis can name | **1** | no — E5, and only with the plugin written and installed |

**Row 1 was checked by READING the analysis, not by a grep**, because three of H5a's four new
refusals fire at `validate` and a filtered grep is the trap `CLAUDE.md` § Mechanical traps names by
name. Read at `d2caacf`: the analysis declares two `data.units.attributes` lists (E-family, C-family)
and § Executability's own stand-in roster names a third set; **none of the three contains `unit`,
`measurement` or `by`.** Its single `io.record` payload names none of the three either — checked
separately because Decision 9's refusal is a *recorded*-side one and an attribute sweep would have
missed it. It contains **no row-shaped `io.write`** at all. **Row 1 is unmoved.** **Row 4's
re-derivation is H5b's to publish** (design Decision 11): no task here appends to § Executability,
and **no task may write "N configs now execute" or mint a fifth number.**

**Architecture.** No new module, no new export, no new file of any kind. Five source files and one
document move.

- **`units.py`** — `RESERVED_FIELDS` splits into `UNIT_FIELDS` and `RESERVED_COLUMNS`; the three
  attribute call sites check both; `resolve_units` coerces attribute values on its way out.
- **`coercion.py`** — one branch in `_coerce_one`: a value that is already a `str` by inheritance is
  that string.
- **`artifacts.py`** — the two row-shaped encoders coerce and refuse a non-mapping row; `io.write`
  prefixes the artifact name onto a writer's `ContractError`; `io.record`'s plain branch refuses a
  `measurement` column; `finalize`'s `columns` list is deduped.
- **`validate.py`** — reports the new identifier (measured: through the path it already has).
- **`docs/reference.md`** — § The per-unit tables, § Validation, § Errors `validate` reports,
  § Errors core raises, § Steps and artifacts.
- **`docs/superpowers/spec-defects.md`** — four entries closed or struck, two re-owned, two filed.

**Tech stack:** Python ≥ 3.11, `pytest`, `ruff`, `mypy`. Tests land in existing modules —
`tests/test_artifacts.py`, `tests/test_coercion.py`, `tests/test_units.py`,
`tests/test_validate.py`, `tests/test_cli.py`, `tests/test_apparatus.py`. **No new file is created
by any task**, so the `ruff format --check` and `mypy` counts do not move.

**Spec:** `docs/superpowers/specs/2026-08-21-artifacts-write-side-design.md` — read it beside this
plan, including its § Refusals, § The discriminating fixtures, § The mutations, § Testability and its
appended **§ Ruling from the controller, whose four requirements are binding**. It is the authority
this plan argues from. **Its body must not be edited.** Where this plan measured something that
contradicts it, the disagreement is in [§ Corrections against the code](#corrections-against-the-code),
appended by this plan's author and extended by no task.

**Measurement this plan argues from:** `docs/superpowers/H5-SCOPING.md` — **several of whose claims
the design already falsified, and the design wins**; the design's own re-measurement at `38df123`;
and this plan's re-measurement against **`main` at `d2caacf`**. `d2caacf` is a docs-only commit above
`38df123` (`git diff --stat 38df123 d2caacf` → the design document alone), so the code this plan
measured is byte-identical to the code the design measured — which is what licenses reusing the
design's fixture shapes while re-checking its claims. Every signature, message, helper name and
literal below was read or **run** at `d2caacf`. **Nothing is cited by line number.**

**Baseline, measured 2026-08-21 in the FOREGROUND at `d2caacf`:**

- `uv run pytest -q` → **2835 passed, 1 skipped, 2 xfailed** in 184.86 s
- `uv run ruff check .` → **All checks passed!**
- `uv run ruff format --check .` → **93 files already formatted**
- `uv run mypy` → **Success: no issues found in 52 source files**

**Task count: 13.** The design's 12 in its own grain and its own numbering, plus **task 13, the guard
pin, which runs FIRST**. The addition **appends** rather than renumbering, on H8a's, H8b's, H8c's and
both H7d parts' precedent, so the design's numbering stays citable. 13 tasks make 13 commits.

---

## Sequencing

**Execution order: 13 → 1 → 2 → 3 → 4 → 10 → 5 → 6 → 7 → 8 → 9 → 11 → 12.**

The task headings below are written in that order. Each task restates the constraint it depends on in
its own text, because an implementer sees only their own task brief.

| Constraint | Why, and where it is enforced |
|---|---|
| **Task 13 first** | H5a changes what `run` refuses and **must leave a legal run's artifacts byte-identical**. That claim is only pinnable against bytes captured from a real run **before anything changed**; a literal captured after a task has run records the move, not the baseline. Five slices running, a pin captured that way has held. Its arm D has **no authorized editor** at all |
| **1, 2 before 3** | Tasks 1 and 2 state the per-unit tables' rules in the section a reader lands in; task 3's § Errors rows point at that section. A row citing an unwritten rule is a link to nothing |
| **4 before every code task** | Design Decision 4: the identifier is minted in the four documents' registry **before any code raises it**. This is the repo's documents-lead order, not a build claim — a § Errors row is normative specification and `reference.md`'s `Status` columns are where build state lives |
| **10 before 6 and before 9** | **This is a correction against the design's stated order** (§ Corrections, correction 6). `coerce_scalars` refuses `np.str_` today. Task 6 makes it run over roster attribute values and task 9 over written rows, so landing either before task 10 ships a window in which a resolver yielding an `np.str_` attribute — which works today — and a `.parquet` write of a NumPy string column both refuse. **The window is invisible to the suite**, which is the reason to order it rather than to trust green |
| **5 before 6** | Both are `units.py`. Task 5's refusal is what makes task 6's coercion the only remaining attribute-shaped fault; landing 6 first leaves a roster whose values are scalars and whose names may still be `unit` |
| **6 before 9** | Design Decision 6 and controller requirement 3. Task 9's coercion applies to `finalize`'s own write, so shipping 9 first leaves a window where a **completed** run raises `ContractError` inside `finalize` — every execution paid for, the record lost |
| **7, 8 before 9** | Both touch `artifacts.py` and neither touches an encoder. Landing them first means task 9's diff is the encoders, `io.write` and one document section, and its reviewer is reading one thing |
| **11 after every code task** | Task 11 is narrowed to the cross-cutting pins no single code task can own, and its last step re-runs **every** mutation on the finished branch (§ Corrections, correction 7) |
| **12 last** | Both consistency passes and every filing run against the finished branch |

### Four deviations from the design's grain, each argued

**(a) Task 13 exists at all.** The design names no regression pin. Controller requirement 2 says byte
identity must be **pinned, not measured once** — and the design's own Fixture B **cannot** pin it
(§ Corrections, correction 2). A never-moves detector over the bytes a legal run writes has to be
captured before the first code task.

**(b) Task 11's fixtures are redistributed into the tasks that own their decisions.** The design puts
Fixtures W, B, S, N, A, R, M, D, C, E and every mutation in one task at the end. That would ship
every code task **unpinned** until then — *a correct fix shipped unpinned* has happened **seven**
times in this repo — and it would leave each code task's reviewer unable to see whether the behaviour
in front of them is pinned at all. So Fixture A goes to task 5, R to task 6, M to task 7, D to task
8, S and N to task 9, C to task 10, B's byte arms to task 13; **task 11 keeps Fixture W's full
per-format matrix, Fixture E, Fixture B's cross-spelling arm, and the whole-branch mutation re-run.**
Task 11 is **narrowed, not renumbered**, so the design's numbering stays citable.

**(c) `RESERVED_COLUMNS` gets exactly one reader, not four.** Design Decision 3 prescribes re-pointing
three guards at the new constant. Two of the three would silently drop a **legally recorded `by`
column** from `units.parquet`, and the third would refuse one outright — contradicting Decision 4's
own text, the controller's ruling, and § Steps and artifacts. Applying Decision 4 against Decision 3
(§ Corrections, correction 1), the constant's only reader is the attribute-name check, and task 5
**pins** the `by` column's survival rather than describing it.

**(d) `_check_column_types` does not gain a `where` parameter.** The design's own goal — a message
that does not name a surface the caller was not using — is met by **deleting** the enumeration, which
is the house preference, rather than by threading a parameter that has one caller and one possible
value (§ Corrections, correction 4).

---

## Batching — nine batches, one report and one review each

**Three different risks live in this slice and they are three seams.** A document's failure mode is a
sentence narrower than its code; a scalar rule's is a value silently changed on the way through; a
namespace refusal's is a legal name refused or a reserved one admitted; a writer's is a run that
stops. One review certifying all four would be certifying nothing in particular.

| Batch | Tasks | The seam, and what its review must be able to see |
|---|---|---|
| **B1** | **13** | **The pin, before anything moves.** A capture check: that every arm was produced by **running** — a real `run` for the `units.parquet` arm, real `StepIO.write` calls for the encoder arms — and never transcribed from `artifacts.py`; that arm A asserts **decoded values with their exact Python types and the column order**, not merely equality; that arm B's parquet byte-hash carries its stated edit conditions in the docstring; and that **arm D needs no authorized editor**, so a passing arm D is itself the proof that no worked example moved. It must confirm no gate literal moved: still 52 source files, still 93 formatted |
| **B2** | **1, 2** | **Documents that state built behaviour, alone.** No identifier is minted here and no code moves, which is the seam. Its review is a **document-against-code review**: every clause of the unification rule traced to the code that enforces it or to the shipped test that pins it (`grep` for each, and report what you grepped); and `measurements.parquet`'s stated column set checked against a table written by a **real run declaring `data.units.measurements`** — the design's own § What could not be measured names that fixture as absent and task 2 is where it stops being absent |
| **B3** | **3, 4** | **The `E-` registry, alone, and reviewed.** *One row per code covering EVERY emit site* was the whole-branch Major on H8a and H8b and shipped **twice** inside H8c. Its review must certify, for each of `E-STEP-RETURN-TYPE`, `E-STEP-KEY-COLLISION`, `E-ARTIFACT-UNWRITABLE` and the newly minted `E-UNITS-ATTR-COLUMN`, that the row was widened by **reading the emit sites and then confirming with a grep** — in that order, since the reverse is the substitution `CLAUDE.md` § Answering a question with a proxy is about — and that the reserved-**metric** sentence in § Steps and artifacts still says its set is one, because H5a does not add to it |
| **B4** | **10** | **The one scalar rule, alone, because every surface shares it.** `coerce_scalars` has callers in `runner.py`, `apparatus.py`, `cli.py` and `artifacts.py`, and this batch widens what all of them accept. Its review is a **blast-radius review**: the caller list enumerated by reading and confirmed by grep; what the widening admits stated **per caller**, including the two consequences the design does not name — an `np.str_` apparatus fact now coerces instead of drawing `E-APPARATUS-FACT-TYPE`, and a `str`-subclass `Estimate.value` now draws `E-STEP-ESTIMATE-VALUE` instead of `E-STEP-RETURN-TYPE`; and `str.__str__` versus `str()` demonstrated on the `str`-Enum arm, which is the only input on which the two constructors disagree |
| **B5** | **5, 6** | **The attribute namespace and the roster, and this batch owns controller requirement 3.** Its review must see the **ordering** pinned, not only the coercion: a real `run` whose resolver yields a structural attribute value leaves **no run directory in `output_dir`**, and the mutation that removes the coercion fails **on that assertion** — read the failure text and say which assertion failed. It must also see the `by`-column survival arms of § Corrections correction 1, the `paths` arm that proves the two codes are told apart, and Fixture A's table carrying `unit`, `measurement`, `by` **and both decoys as real columns** — without which every arm fires on `E-UNITS-ATTR-MISSING` instead |
| **B6** | **7, 8** | **Two small guards on the recorded side, no encoder in the picture.** The seam is that neither task touches a writer. Its review is a **control review**: Fixture M's arm 3 (a column named `measurements`, plural, still **writes** — asserted by reading the parquet back, because a prefix or substring guard would swallow it) and Fixture D's assertion on the **column list** rather than on the file, since the file is already correct in shape and a file assertion would pass before and after. It must also confirm task 8's docstring claims only what the dedupe does — the residual shadow for a directly constructed `Unit` is stated, not implied (§ Corrections, correction 5) |
| **B7** | **9** | **The behaviour change. Its review must be a real-command review.** H7d Part A's only Critical was invisible to every direct-call probe and surfaced only through an end-to-end run, and every direct-call probe there hand-built its inputs and so never reached it. So: a real `run` completing with `units.parquet` byte-identical to task 13's capture; a real `StepIO.write` for every refusal arm; the unregistered-suffix control asserting the artifact name appears **exactly once** (§ Corrections, correction 3); Fixture S's offending cell in the **first** and in the **last** row; and the document half — the writer/reader row split for `.csv`, the coercion statement, and the sentence a user whose run stopped will find |
| **B8** | **11** | **The cross-format matrix and the whole-branch mutation re-run.** The seam is that nothing here is new code: this batch's only product is pins. Its review must see Fixture W's `.csv` arms comparing against **`str()` of the coerced value**, never against the coerced value itself (§ Corrections, correction 2), and it must read the re-run's output for **every** mutation in this plan, including the two named blind in advance — a mutation's silence is evidence about the tests, not about the code |
| **B9** | **12** | **Filings and both consistency passes, alone, and reviewed — the batch H8b skipped.** Three of one gate's four Majors lived in exactly such a commit. Its review is a **filing-and-sweep review**: every closed entry **struck** rather than deleted; every re-owning stated as a **fact with a reason** and never as *"whichever slice next touches X"*; every sweep **naming its files** rather than filtering its output and **proven able to fail** by running it against a string known to be present; and § Executability's four-row table repeated **character for character** with no fifth number |

---

## Global Constraints

Every task inherits all of these. They are copied verbatim rather than cross-referenced, because an
implementer sees only their own task brief.

**Commands.** Tests `uv run pytest`. Lint `uv run ruff check .`. Format `uv run ruff format .`.
Types `uv run mypy`. All four must pass before a commit. **Baseline at `d2caacf`: 2835 passed, 1
skipped, 2 xfailed; 93 files formatted; 52 source files typed.**

**No gate literal moves in this slice.** No task creates a file of any kind, so `ruff format --check`
stays **93** and `mypy` stays **52 source files** at every commit. **Every task states its own DELTA
on the test count, not an absolute**; compute the absolute from your own previous run and reconcile
any difference before committing.

**Run `uv run pytest` DIRECTLY, in the foreground, and wait for it.** It takes about three minutes at
this baseline. **Never construct a wait, a monitor, a poll or a background run around it** — six
agents on preceding slices stalled that way and one stopped with a mutation still applied. Clear
`__pycache__` and any stale `pytest-of-*` temp directory before a run.

**Verify format with `uv run ruff format --check .`, never the bare form.** A previous brief in this
repo wrote the bare form where it meant `--check` and rewrote 67 files. **`ruff format` does not
process `.md`** — measured twice on preceding branches by copying a document, running the formatter
and diffing byte-identical; two agents nonetheless reverted documents on that misdiagnosis. **A
revert is verified by behaviour**, never by `git status`, and least of all by an account of what
caused the change. **`git checkout -- <file>` destroys uncommitted work** and has been mistaken for
reverting a mutation three times here.

**Every task says whether its surface is `validate`, a real command, a direct call, or documents.**
Three of H5a's four new refusals are reachable at `validate`, and one is reachable only through a
write. **Where a task's surface is a direct call, its brief says which later batch covers it through
a real command** — H7d Part A's only Critical was invisible to every direct-call probe.

**`units.parquet` has no reader in any shipped command, and exactly one documented reader in user
code.** Measured at `d2caacf` by reading each module and then grepping: `report.py`, `study.py`,
`diff.py`, `freeze.py`, `lineage.py`, `runner.py` and `stats.py` contain the string `parquet` **zero**
times; `cli.py`'s one occurrence is a comment. No hash covers either table. **Two consequences pull
in opposite directions and every task must hold both.** It makes H5a cheap: no shipped command can
break. And it makes H5a's tests unusually easy to write wrong: a corruption in `units.parquet` is
invisible to every test that goes through `run.yaml`, which is every test in `tests/test_cli.py` that
checks a metric. **A parquet assertion has to open the file.** The one documented consumer is
§ Steps that need every condition's `io.read_condition(c, "step02_score", "units.parquet")`, which
dispatches to the same `_decode_parquet` these fixtures exercise — so a corrupt table is not only a
corrupt published artifact, it is what that step reads.

**H5a moves NO row of the feasibility analysis' four-row table and mints no fifth number.** Rows 1–3
are unmoved and row 1 was checked by reading rather than by a grep. **Row 4's re-derivation is H5b's
to publish** (design Decision 11), and if H5b does not land in this development cycle the entry must
be appended by whichever slice does — **not by any task here.** No task may write "N configs now
execute".

**Four things that run today stop running, and each must be findable in a document.** Controller
requirement 1: *a user whose run stops must be able to find the sentence that says why*, with what
ran before and what happens now. The four, with the task that owes the sentence:

1. A **structural or `bytes` cell** in a `.csv` or `.parquet` written through `io.write` — task 9.
   **Its two halves have different "what ran before" and must be written as two** (§ Corrections,
   correction 2): in `.csv` the cell was silently mangled into its `repr`; in `.parquet` it
   **round-tripped intact** and the refusal takes a working round trip away.
2. A **row that is not a mapping** handed to either writer — task 9. Makes an existing documented
   refusal true rather than inventing one.
3. A **declared attribute** named `unit`, `measurement` or `by` — task 4 (the document) and task 5
   (the code).
4. A **resolver-yielded declared attribute value** that is structural — task 6.

**Two refusals retire, and controller requirement 4 says a retirement is stated, not left implicit.**
`io.write` of `.csv`/`.parquet` rows mixing a NumPy scalar with its Python counterpart stops raising
(task 9), and an apparatus fact value that is a `str` by inheritance stops drawing
`E-APPARATUS-FACT-TYPE` (task 10). **One refusal is added on the recorded side**: a plain `io.record`
column named `measurement` (task 7).

**A legal run's artifacts are byte-identical, and that is task 13's pin rather than any task's
claim.** No task may assert byte identity from its own reasoning; every task's suite run includes
task 13's arms, and a task whose diff moves them has found a finding, not an assertion to edit.

**Every literal is computed, not guessed, and every mutation names the assertion that catches it AND
why the two branches can differ.** Across recent slices prescribed mutations: **were what the shipped
code already did**; made **both branches identical**; were **placed one line off** and so tested a
different property; **fired for the wrong reason** because another clause already refused the
fixture; **iterated the thing under test**; and were **satisfied by neighbouring output** (three in
one batch). **A mutation that changes nothing is evidence about the TESTS, not about the code**, and
"no mutation reaches this" and "no mutation *can* reach this" are different claims. Before trusting
any mutation, check its two branches can produce different results **on the named fixture**.

**Mutation discipline, every task.** Keep a copy of the file before mutating. Apply the named
mutation. Run the named test, confirm it **FAILS and read WHY it failed** — a mutation that fails for
the wrong reason is not a pin, and only reading the failure text tells you which you have. Then run
the **full, unfiltered** suite in the foreground. Then
`find . -name __pycache__ -type d -exec rm -rf {} +`. Then revert **by editing the file back in
place**. Verify the revert by **behaviour** and by diffing against your saved copy.

**A safety argument in a comment is a claim, and needs a mutation like any other.** Two in this
slice are named in advance: `_check_column_types`' new docstring precondition (*its input is already
coerced, and its correctness depends on that*) — task 9's coercion-deletion mutation is its pin — and
task 8's dedupe, whose comment must **not** argue that Decision 4 makes the duplicate unreachable,
because a directly constructed `Unit` still reaches it. **A comment or docstring claiming a guarantee
the code does not provide** is this repo's most repeated habit; if a comment says *this cannot
happen*, make it happen. And **prefer deleting a claim to rewriting it** — a rewrite invents, a
deletion cannot.

**Answering a question with a proxy is this repo's most expensive habit.** One corner was given
**five** wrong grounds across two slices. In this slice, each direct question and the correlate it
replaces:

- *May this attribute take this name* — membership in `UNIT_FIELDS` (a field of the type) or in
  `RESERVED_COLUMNS` (a column in a per-unit table or the record's stratum block). Two questions,
  two constants, two codes. Never one wider tuple.
- *Is this a stratum* — **never the string `by`.** The sixth instance of *a name standing in for a
  structural fact* in this repo was exactly this column: H8c had to replace a `by` name test with a
  structural one because a recorded column legitimately named `by` was being silently dropped. **This
  slice's refusal removes one PRODUCER of a `by` column — a declared attribute — and not the
  POSSIBILITY of one**, because a step *recording* `by` stays legal by design. `report`'s structural
  test remains the only thing that can tell a stratum from a metric, and **nothing here is licence to
  reintroduce a name test anywhere.** That reasoning must survive into the code comments.
- *Which surface produced this refusal* — `io.write`'s own prefix, which names the artifact. Never a
  hard-coded enumeration of surfaces inside a message a fourth caller reaches.
- *Is this value a scalar* — `coerce_scalars`, the one scalar walk, called with a fourth and fifth
  call site. Never a writer-specific type check.
- *Did the coercion change the bytes* — task 13's captured bytes from before the change. **Never a
  comparison between the NumPy-spelled and Python-spelled versions of the same column**, which after
  coercion are the same input and cannot differ (§ Corrections, correction 2).
- *Did the run pay for anything before it refused* — whether `output_dir` holds a `run_*` directory.
  Never the exit code alone, which is the same in both branches.

**Never filter the output of a sweep whose job is to find a string — filter the FILE LIST**, and
prove each sweep can fail by running it against a string known to be present. **Name the four
documents explicitly (`README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`,
`docs/reference.md`), and name `CLAUDE.md` and `docs/feasibility-llm-growth-studies.md` too.** The
development record under `docs/superpowers/` is **not** governed by the cross-document pass and is
never retro-edited; `spec-defects.md` is the one exception, where a closed gap is **struck** rather
than left to mislead.

**Row-shaped `io.write` also lives outside `src/` and `tests/`.** Swept at `d2caacf` by naming the
file list — `src/publishable/templates/`, `src/publishable/generators/`,
`src/publishable/readme_templates/`, `scaffold.py`, `plugin_scaffold.py` and the four documents.
Result: the generators and scaffolds contain **no** `io.write` at all; the documents contain
`io.write("scores.parquet", result.rows)` (README and § Steps and artifacts, the shape whose refusal
task 9 retires), `io.write("comparison.csv", table)` (§ Steps that need every condition, whose
`table` is elided and stays legal under the contract that row already declares) and a `programs/…json`
write no task touches. **A generated example that starts refusing is worse than a test that breaks**,
so a task changing writer behaviour re-runs this sweep rather than trusting this paragraph.

**When a change makes a sentence false, that sentence is in the diff already being read.** Three
instances are pre-named so nobody discovers them. § Steps and artifacts' **"One rule, all three
surfaces"** becomes false when task 9 adds the two row-shaped writers — the fix drops the count
rather than raising it, since counts in prose are what this rule exists to prevent. § Steps and
artifacts' **"What a writer takes is what its reader gives back"** is false for `.csv` for **every**
value and not only structural ones (measured), and task 9 states the exception rather than leaving
the coercion statement beside a claim contradicting it. And `E-APPARATUS-FACT-TYPE`'s § Errors row
**derives** its scope from *"the closed scalar set `coercion` already enforces"*, so task 10's
widening needs **no** edit there — replacing that clause with an enumeration would convert a
self-maintaining statement into a maintenance obligation nobody owns.

**One shipped sentence is re-read and judged STILL TRUE, and no task may rewrite it.** § Steps and
artifacts' reserved-**metric** sentence — *"it is a set of one today; anything added to it is a
breaking change to what a template's `aggregate` may return"* — describes what `aggregate` may
return, and that set stays `{by}`. H5a adds a **different set with a different subject**: what
`data.units.attributes` may name. Task 4's edit **distinguishes the two namespaces** and must not be
written as though this slice added to the metric set. A task that "fixed" that sentence would delete
a true claim.

**Documentation rules.** `×` not `x` for multiplication, including inside fenced blocks. Hyphen,
never an en dash, in anything that becomes a filename or an anchor. **Cite by section**
(`reference.md` § "The per-unit tables"), **never by line number**. **No positional locators** ("the
row above", "further up"): name what a sibling row *does*, and when you insert a row check every row
it **moved** and every count phrase near it — at least seven positional references in this repo were
wrong twice. **No counts in prose or comments** and **no call-site enumerations**. **A build fact is
dated and pinned to a commit** — today is **2026-08-21**.

**The four normative documents LEAD; `src/` follows.** Where they and the code disagree, **the
document changes first** and the gap is recorded in `docs/superpowers/spec-defects.md`. **A ledger
line saying "filed" is not a filing.** **This slice's spec, `H5-SCOPING.md`, and every preceding plan
and ledger must not be retro-edited.**

**The worked example is BINDING and no task touches it.** § The worked example's intervals were
checked numerically against a synthetic 228-unit table and **must not be narrowed back**; `cohens_d`
stays `null`; the hash prefixes `8e21`, `1a2b`, `3d8a`, `6b1f`, `2f5c8d0` and both run IDs stay.
Task 13's arm D captures the worked example's own numbers as raw text **with no authorized editor**,
so a passing arm D is the proof rather than the promise.

**`tests/conftest.py` already has** an autouse `os.environ` restore, an opt-in `registries` fixture
and an opt-in `installed` distribution fixture. **Do not add duplicates, and do not add a second
autouse fixture of any kind.**

**`validate` collects rather than aborting**, so a refusal elsewhere never makes a later check
unreachable, and **no task may reason that one refusal makes a later check blind** — two independent
readers on a preceding slice recorded a mutation as blind on exactly that reasoning before a reviewer
disproved it by building the fixture. Note the shape this slice actually has: `_check_units` reports
`resolve_units`' `ContractError` and then returns `None` for the roster, so downstream roster checks
are **skipped** rather than made unreachable. Ask what `validate` *reports*, in full.

**The sibling that already got it right is the first place to look.** Four recipes this slice copies
rather than reinvents: `coerce_scalars` is **the one scalar walk** and task 9 adds call sites rather
than a writer-specific type check; `apparatus.check_facts`' catch-and-re-code is the precedent for
`io.write`'s prefix, copied **with its containment** — the `try` encloses the dispatch and nothing
else, because *a recipe is its calls plus where they sit*; `_contained` is the precedent for one
predicate called with a different base rather than duplicated; and `tests/test_cli.py`'s
`_install_plate_wells_resolver` plus `run_a_project(units_overrides={"from": {"resolver": …}})` is a
working end-to-end resolver run and is what tasks 6's and 11's real-command arms build on. And one
that is **H5b's**, named so H5a does not spend it: `units.rule_for` / `coerce_for_rule` /
`apply_rule` already solve the collapse-across-repeats problem. H5a collapses nothing and needs none
of it.

**What H5a refuses to do, with the route, so no task folds it in.** Changing the promote/refuse
boundary for a genuinely mixed column → **H5b**. Refusing a **recorded** column named `by` →
**nowhere; it stays legal by design.** Refusing `aggregate` from returning `unit` or `measurement` →
**H5b task 14.** A non-numeric column reaching `collapse_repeats`, `summarize_step` or `aggregate`'s
table → **H5b tasks 11–13**, whose Critical is a silent `n_valid: 0.0` over six `True` rows, and
**H5a must not make it harder to fix**: nothing here narrows what a column may hold. The second
empty-level gate in `cli.py`'s stratum loop → **H5b task 15.** Coercing the rows a nesting-taking
writer receives → **unassigned with a reason**, filed by task 12. Hashing `units.parquet` → **out of
scope; H6's boundary if anyone wants it.** Adding cross-row type unification to `.csv` → **not built
here**, and § Corrections correction 8 says why. `field_convention`, declarable on a shipped class
and read by nothing → **not H5's**; an implementer reading `units.py` will meet it and must leave it.

---

## The fixtures this slice rests on, and where each one lives

The design's § The discriminating fixtures is the authority for their shapes. This table records
where each lands after deviation (b), because an implementer sees only their own brief.

| Fixture | What it claims | Task |
|---|---|---|
| **B** — byte identity for a legal write | Coercion moves no byte a legal run writes today | **13** (the golden arms) and **11** (the cross-spelling arm, declared weak) |
| **A** — the reserved attribute name, decoy on each side | `unit`/`measurement`/`by` refuse as `E-UNITS-ATTR-COLUMN`; `paths` still refuses as `E-UNITS-ATTR-RESERVED` | **5** |
| **R** — the resolver's structural attribute value, and its coercion control | A structural declared attribute refuses at resolution; an `np.float64` one resolves to exactly `float` | **6** |
| **M** — the `measurement` column, both branches, plus the plural control | The two `record` branches agree; `measurements` still writes | **7** |
| **D** — `finalize`'s deduped columns | The claim is about the list, so the assertion is about the list | **8** |
| **S** — the structural cell, first row and last row | The refusal names the column, the row and the artifact | **9** |
| **N** — the non-mapping row | The *type* of the failure is `ArtifactError` · `E-ARTIFACT-UNWRITABLE` | **9** |
| **C** — the coercion branch, `str` against `bytes` | `np.str_` coerces; `np.bytes_` and `bytes` still refuse; a `str`-Enum keeps its value; an array still refuses | **10** |
| **W** — the writer round trip, per format | Both formats agree where they can, and `.csv`'s difference is stated | **11** |
| **E** — the empty and all-`None` row sets | The two arms a coercion change breaks silently | **11** |

---

## Task 13: the guard pin — a legal run's bytes, both encoders' bytes, and the worked example

**Runs FIRST, before every other task. Surface: a real `run`, direct `StepIO.write` calls, and raw
document text.** H5a changes what `run` refuses and **must leave a legal run's artifacts
byte-identical**; controller requirement 2 says that is **pinned, not measured once**, because *a
correct fix shipped unpinned* has happened seven times here. A literal captured after a task has run
records the move, not the baseline.

**Files:**
- Test: `tests/test_artifacts.py` (add), `tests/test_cli.py` (add)

**Interfaces:**
- Consumes: `run_a_project` from `tests/test_cli.py`, `StepIO.write`, `_decode_parquet`,
  `_decode_csv`, and the raw text of `README.md`, `docs/design-principles.md`, `docs/reference.md`.
- Produces: nothing importable. Arms every later task's suite run must keep green.

**What this pin deliberately does NOT re-capture, and why.** `run.yaml`'s top-level and `provenance`
key lists are already pinned by more than one shipped assertion, and `publishable.__all__` is already
asserted somewhere in the suite. H5a exports nothing and writes no new record key. **Grep for them
before writing anything, and report what you grepped rather than a count** — *before writing "no
existing test asserts X", grep for it* is the check that catches the shape where six consecutive
slices' reports claimed zero disagreements and all six were wrong.

- [ ] **Step 1: capture arm A by RUNNING a real run.** Drive `run_a_project` with
      `unit_attributes` declaring at least one attribute, ten units, and a starter step recording a
      numeric column. Then open `units.parquet` from a step directory and capture:
      the **column order** as a list; each column's decoded values; and `type(v).__name__` for one
      value of each column. **A literal transcribed from `artifacts.py` pins the source, not the
      behaviour.** Assert all three. *Why this arm is the load-bearing one:* it is version-robust —
      it catches `int` silently promoted to `float`, a `bool` becoming an `int`, a `str` becoming its
      `repr`, a `None` becoming something else, and any reordering — every way coercion could move a
      legal artifact, without depending on the locked `pyarrow`.

- [ ] **Step 2: capture arm B by RUNNING both encoders through a real `StepIO.write`.** One row set
      of Python scalars covering `int`, `float`, `str`, `bool` and `None`, written to a `.csv` and to
      a `.parquet` in a step directory, and read back as **bytes**.

```
Arm B1 — .csv GOLDEN BYTES. NEVER MOVE IN THIS SLICE.
  The exact bytes, as a literal, captured by running. Deterministic: `csv` is
  stdlib and no library version is in the path.

Arm B2 — .parquet GOLDEN sha256. A TRIPWIRE, and its edit conditions are
  STATED IN ADVANCE in the docstring.
  The sha256 hex of the bytes, captured by running.
  The docstring must say: this hex is coupled to the pyarrow pinned by
  `uv.lock`. If it fails, arm A is what tells you which fault you have —
  arm A green and this red means the library moved; both red means the
  coercion moved a legal artifact. A hash arm that fails on a library bump
  is a pin someone will edit, so the condition under which it may be
  recaptured is written down here and NOT left to judgement:
  ONLY when `uv.lock`'s pyarrow entry changed in the same commit, and only
  with arm A green.
  NO TASK IN THIS SLICE MAY EDIT IT: no task in H5a touches `uv.lock`.
```

- [ ] **Step 3: capture arm C — the shapes that must keep raising.** Through the same real
      `StepIO.write`: `.parquet` rows whose column mixes `bool` with `int`, and `str` with `int`,
      each raising `ContractError` · `E-STEP-RETURN-TYPE`. These two are already pinned by shipped
      tests in `tests/test_artifacts.py` — **grep for them, name them in the docstring, and do NOT
      add a third copy.** What this arm adds that they do not: the same two shapes through a **real
      `io.write`** rather than through `_encode_parquet` directly, so task 9's `except ContractError`
      wrapper cannot swallow or re-code them. Assert the code **and** that the message names the
      column and both type names.
      **Assert those three as SUBSTRINGS — never the whole message, never `startswith`, and never the
      surface clause.** Task 9 **deletes** that message's surface enumeration (*"io.record's values, a
      step's return, and a template's aggregate…"*) and **prefixes the artifact name** onto it, and
      **both changes are authorized.** A golden message literal here would fail an arm this plan gives
      no editor, and the resolution would be a quiet weakening — which is the failure arm D's design
      exists to avoid. This arm pins the **code and the named operands**, not the wording.

- [ ] **Step 4: capture arm D — the worked example's own numbers, as raw text. NO AUTHORIZED
      EDITOR.** For each of `README.md`, `docs/design-principles.md` and `docs/reference.md`: the
      lines carrying the worked example's interval and hash literals — `0.581`, `0.488`, `0.661`,
      `0.607`, `0.412`, `0.026`, `−0.007`, `0.059`, `−0.169`, `0.014`, `8e21`, `1a2b`, `3d8a`,
      `6b1f`, `2f5c8d0` — collected as a **tuple of raw strings** by scanning each file for the
      literal and keeping the whole line, and compared byte for byte. **Locate each line by the
      literal it contains, never by an ordinal or an nth-line index** — a positional locator, wrong
      twice in this repo. Assert on **raw text**, never through a markdown or YAML reader: a defect
      that lives in *how* bytes are written is undone by a reader before the assertion reaches it,
      which is how a YAML-alias defect once shipped past two tests. **This arm needs no authorized
      editor: no task in H5a edits a worked example, so a passing arm D is the proof.**

- [ ] **Step 5: run.** `uv run pytest` → **2835 + your new tests** passed, 1 skipped, 2 xfailed.
      `uv run mypy` → still **52 source files**; `uv run ruff format --check .` → still **93 files**.
      This task adds no file and no module.

- [ ] **Step 6: the mutations — four, because one arm proving itself proves nothing about
      another.**
      (i) In `src/publishable/artifacts.py`, in `_encode_parquet`, change the column-collection loop
      to `for key in sorted(row)`. **Arm A's column-order assertion must FAIL** and arm B2's hash
      must fail; arm B1 must **pass** if the fixture's Python-scalar row happens to be alphabetical,
      so read which failed. *Why the branches differ:* the union-in-first-seen-order is observable in
      the file's schema and the attribute columns of a real run are not alphabetical.
      (ii) In `_encode_parquet`, wrap every value in `float()` before building the table. **Arm A's
      type assertion must FAIL** for the `str` and `bool` columns. *Why the branches differ:* arm A
      asserts `type(v).__name__` per column, which no other assertion in the suite does for this
      file.
      (iii) In `_encode_csv`, change `lineterminator="\n"` to `"\r\n"`. **Arm B1 must FAIL.** *Why
      the branches differ:* the bytes differ and nothing else in the suite compares this file's
      bytes.
      (iv) In `docs/design-principles.md`, change one worked-example interval bound by one digit.
      **Arm D must FAIL for that file and pass for the other two.** *Why the branches differ:* three
      independently captured tuples.
      Revert all four by editing in place and verify by behaviour.

- [ ] **Step 7: commit.** `git add -A && git commit -m "H5a task 13: pin a legal run's bytes, both
      encoders' bytes and the worked example before anything moves"`.

---

## Task 1: § The per-unit tables states the cross-row unification rule

**Surface: documents.** No code moves. Design Decision 1: the rule the code enforces is documented as
it is, and the code's own answer is **not changed here**.

**Files:**
- Modify: `docs/reference.md` (§ The per-unit tables)

- [ ] **Step 1: trace every clause to the code or to a shipped test, and report what you grepped.**
      The rule to state, from design Decision 1: a column of one type round-trips, `str` and `bool`
      included; `int` beside `float` **promotes to float**, in both declaration orders; `None` is not
      a type — it is skipped, so all-`None` and `None`-mixed-with-one-type both round-trip; an empty
      row set writes an empty table and raises nothing; **everything else refuses** with
      `ContractError` · `E-STEP-RETURN-TYPE`, naming the column, both types and one unit for each.
      For each clause: name the code that enforces it (`_check_column_types`' normalization, its
      `value is None` skip, its two-group refusal) or the shipped test that pins it. **Two shipped
      tests pin the promote/refuse boundary and predate this slice — grep for them by name and quote
      the names in your report.** Do not write "no test asserts X" without having grepped.

- [ ] **Step 2: write the rule into § The per-unit tables**, beside the sentence that already states
      `units.parquet`'s column set. State the **reason** the boundary sits where it does, from design
      Decision 1: `design-principles.md` already draws it for a quantity — a per-unit metric whole
      for some units and fractional for others is ordinary, and `bool` beside `int` is a type
      confusion silence would hide. **Do not state the strictness as settled forever**: the more
      forgiving reading (write the column as `str` and let the reader see the mixture) is **H5b's
      Decision 10** to arbitrate, and this section must not foreclose it.

- [ ] **Step 3: state it for the format it is true of.** Measured at `d2caacf`: the cross-row check
      runs in `_encode_parquet` only, so a `.csv` whose rows disagree on a column's type **writes
      today** (`[{"v": "a"}, {"v": 1}]` → `b'v\na\n1\n'`). This section is about the per-unit tables,
      which are `.parquet`, so **state the rule for the per-unit tables** and do not generalise it to
      every row-shaped write. § Corrections correction 8 records why the `.csv` gap is not closed
      here.

- [ ] **Step 4: run the mechanical pass on what you edited** — every relative link and `#anchor`
      resolves, no two headings produce the same anchor, every table row matches its header's column
      count, no trailing whitespace, tab or invisible unicode, skipping fenced blocks. `×` not `x`.

- [ ] **Step 5: run.** All four gates. Test count unchanged: **2835 + task 13's**.

- [ ] **Step 6: commit.** `git add -A && git commit -m "H5a task 1: state the cross-row unification
      rule for the per-unit tables"`.

---

## Task 2: § The per-unit tables states `measurements.parquet`'s column set

**Surface: documents, plus one fixture from a real run.** Design Decision 2: the column set is
`unit`, `measurement`, then every recorded key — and **no** declared attribute.

**Files:**
- Modify: `docs/reference.md` (§ The per-unit tables)
- Test: `tests/test_cli.py` (add)

**The design's own § What could not be measured names this fixture as absent**: *"A
`measurements.parquet` written by a real run. Decision 2 states its column set from the code and from
direct `StepIO` probes; no scratchpad config here declared `data.units.measurements`."* **Task 2 is
where it stops being absent.**

- [ ] **Step 1: write the fixture first, and read the column set off the file.** A real run through
      `run_a_project` declaring `data.units.measurements` with a `by` and a `collapse`, a roster whose
      table carries the measurement axis column, and a starter step calling
      `io.record(unit, values, measurement=…)`. Open `measurements.parquet` and assert its **column
      list**, in order. Assert the declared attribute names are **absent** from it and **present** in
      the sibling `units.parquet` — the two halves together are what makes the asymmetry the claim.
      **Read every literal back from what produced it**: `run_a_project` prefixes a generated step's
      name and derives repeat labels per run, so no step name and no repeat label may be a literal.

- [ ] **Step 2: state the column set in § The per-unit tables**, with the ground from design
      Decision 2: an attribute comes from the roster, not from an execution — it is constant across
      every measurement of one unit, so repeating it per `(unit, measurement)` row is a
      denormalization core would have to keep consistent with its sibling, for a value the reader can
      join on `unit`. § Templates already gives the same argument in the other direction (a declared
      attribute *"is carried through unchanged rather than averaged … it has nothing to collapse
      across a unit's repeats"*), and this file is the *uncollapsed* table, where there is nothing
      for an attribute to be uncollapsed into.

- [ ] **Step 3: state that the three column groups are disjoint, and that it is enforced rather than
      assumed.** `io.record`'s `measurement=` branch refuses a recorded key named `unit`, one named
      `measurement`, and one shadowing a declared attribute. **Read those guards before writing the
      sentence** — the sentence claims a property of code and goes stale like any comment.

- [ ] **Step 4: the mutation.** In `src/publishable/artifacts.py`'s `finalize`, change the
      `measurements.parquet` write to pass rows merged with the roster's attributes the way the
      `units.parquet` write does. **Step 1's absence assertion must FAIL.** *Why the branches
      differ:* the column list gains the attribute names, and nothing else in the suite enumerates
      this file's columns. Revert by editing in place.

- [ ] **Step 5: mechanical pass, then run.** All four gates; test count **+1**.

- [ ] **Step 6: commit.** `git add -A && git commit -m "H5a task 2: state measurements.parquet's
      column set, and pin it from a real run"`.

---

## Task 3: § Errors core raises — three shipped rows widened to every emit site

**Surface: documents.** *§ Errors carries one row per code covering EVERY emit site, not one row per
site.* That shape was the whole-branch Major on H8a and on H8b and **shipped twice inside H8c**.

**Files:**
- Modify: `docs/reference.md` (§ Errors core raises)

- [ ] **Step 1: enumerate the emit sites by READING, then confirm by grep — in that order.** The
      reverse order is the substitution that shipped a credential leak in H7c, made by the author of
      the rule forbidding it, while measuring for it. Measured at `d2caacf`, and each of these is a
      claim you must re-check rather than copy:
      - `E-STEP-RETURN-TYPE` has **three** sites, not the two the scoping enumerated by reading:
        `coercion.py` (a value core can't record), `artifacts.py` (`_check_column_types`, a `.parquet`
        whose rows disagree on a column's type) **and `runner.py`** (a step's `run` returning a
        non-mapping). Task 9 adds a fourth surface — the same `coercion.py` raise reached from the two
        encoders — which is a **new caller of an existing site**, not a new site.
      - `E-STEP-KEY-COLLISION` has sites in `stats.py` and `artifacts.py`. Its present row names *"a
        derived key against a recorded column, a recorded column against a unit attribute"* and names
        **neither** the `unit` nor the `measurement` column collision, both of which ship today.
      - `E-ARTIFACT-UNWRITABLE` has one site today, and task 9 adds the non-mapping row.

- [ ] **Step 2: widen the rows.** `E-STEP-RETURN-TYPE`'s clause covers a value core can't record, a
      step's `run` returning a non-mapping, **and a written `.csv` or `.parquet` row whose value is
      not a scalar or whose rows disagree on a column's type** — with the disagreement clause stated
      for the format it is true of (the cross-row check runs for `.parquet`; § Corrections correction
      8). `E-STEP-KEY-COLLISION`'s clause gains the two structural column names. `E-ARTIFACT-UNWRITABLE`'s
      clause gains the non-mapping row. **Check the count phrase in the row you are editing**: the
      shared row's *"Four emit sites for the escape alone"* is about `E-ARTIFACT-NAME` and stays true
      — verify that by reading rather than assuming, because a count phrase near an edit is what this
      repo has got wrong at least seven times.

- [ ] **Step 3: check what the widening does NOT license.** These rows describe code that task 9 has
      not written yet. That is the documents-lead order and it is deliberate — a § Errors row is
      normative specification, and `reference.md`'s `Status` columns are where build state lives —
      but it means **task 9's reviewer must re-read these rows against the code**, and this task's
      report must say so in one sentence.

- [ ] **Step 4: mechanical pass, then run.** All four gates; test count unchanged.

- [ ] **Step 5: commit.** `git add -A && git commit -m "H5a task 3: widen three § Errors rows to
      every emit site"`.

---

## Task 4: mint `E-UNITS-ATTR-COLUMN`, before any code raises it

**Surface: documents.** Design Decision 4. The identifier is written into three `reference.md`
sections **before any code**, and the edit **distinguishes two namespaces** rather than re-arguing
the reserved-metric sentence.

**Files:**
- Modify: `docs/reference.md` (§ Validation, § Errors `validate` reports, § Steps and artifacts)
- Consider: `docs/experimental-designs.md` (§ Mistakes core prevents) — a **decision for this task**

- [ ] **Step 1: read the sibling row before writing the new one.** `E-UNITS-ATTR-RESERVED` lives in
      § Errors `validate` reports and in § Validation's *Attribute names aren't reserved* row, and
      **not** in § Errors core raises (measured at `d2caacf`). The `unit`-shadow filing in
      `spec-defects.md` predicts the fix *"touches `reference.md` § Errors core raises"* — **that
      prediction is wrong**, and task 12 strikes it rather than propagating it. The three homes are
      § Validation, § Errors `validate` reports and § Steps and artifacts.

- [ ] **Step 2: mint the identifier.** `E-UNITS-ATTR-RESERVED` keeps its meaning — an attribute named
      for a field of `Unit`. **`E-UNITS-ATTR-COLUMN`** refuses an attribute named `unit`,
      `measurement` or `by`. Write the § Validation row so it names **both** cases and sends a reader
      holding either code to the right one; write the § Errors `validate` reports row beside its
      sibling. **State the ground for two codes rather than one wider row**, from Decision 4: the two
      faults differ on **lifetime** — one says *this name belongs to the type you are declaring
      against*, permanently; the other says *this name belongs to a column in the artifact*,
      revocably. `E-APPARATUS-FACT-TYPE`'s own row states the same principle for a code sharing
      `coerce_scalars` with `E-STEP-RETURN-TYPE`: **sharing a mechanism is not sharing a fault.**

- [ ] **Step 3: state stoppage 3 so a user whose run stops can find it** (controller requirement 1).
      What ran before: a declared attribute named `unit` **replaced the unit key column** in
      `units.parquet` — measured at `d2caacf`, the published table read
      `[{'unit': 'HIJACK', 'site': 'n', 'v': 1.0}]`, the identity `n`, pairing and every contrast
      rest on. What happens now: the declaration is refused, at `validate` and therefore at `run`.

- [ ] **Step 4: distinguish the two namespaces in § Steps and artifacts, and do NOT re-argue the
      metric sentence.** The reserved-**metric** sentence describes what a template's `aggregate` may
      return and that set stays `{by}`. What H5a adds is a different set with a different subject —
      what `data.units.attributes` may name — and `by` is in both for one underlying reason (a
      stratified block keys its rows by `by`). **Grep for "set of one" and check the surrounding
      paragraph reads consistently afterwards.** Write, in the document, the sentence that stops the
      next reader from taking this refusal as licence: the refusal removes one **producer** of a `by`
      column and not the **possibility** of one, because a step *recording* `by` stays legal — so
      `report`'s structural stratum test remains the only thing that can tell a stratum from a
      metric. **The sixth instance of a name standing in for a structural fact in this repo was
      exactly this column.**

- [ ] **Step 5: decide the `experimental-designs.md` § Mistakes core prevents question, and record the
      decision either way.** An attribute silently replacing the unit key is that section's subject
      matter, and the design routes the decision here rather than asserting a gap. Whichever way you
      rule: anything in that section must be **structurally impossible in the schema**, not merely
      discouraged, so a row is legitimate only because the declaration is now refused. If you add a
      row, run the mechanical pass on that file too and check every row your insertion **moved**.

- [ ] **Step 6: mechanical pass over both files, then run.** All four gates; test count unchanged.

- [ ] **Step 7: commit.** `git add -A && git commit -m "H5a task 4: mint E-UNITS-ATTR-COLUMN in three
      sections, before any code raises it"`.

---

## Task 10: the `str`-by-inheritance branch in `_coerce_one`

**Surface: a direct call, and the two document sentences it makes false.** Design Decision 7.
**Ordered here — before tasks 6 and 9 — as a correction against the design's stated order**
(§ Corrections, correction 6): `coerce_scalars` refuses `np.str_` today, so landing either of those
first ships a window in which a resolver yielding an `np.str_` attribute, which works today, refuses.
**The window is invisible to the suite.**

**Files:**
- Modify: `src/publishable/coercion.py`, `docs/reference.md` (§ Steps and artifacts)
- Test: `tests/test_coercion.py` (add), `tests/test_apparatus.py` (add), `tests/test_estimate.py` or
  `tests/test_coercion.py` for the `Estimate` arm — whichever module already holds the
  `_coerce_estimate` tests; **grep before choosing, and add no new file**

**Interfaces:**
- Modifies: `coercion._coerce_one` — one branch, placed **after** the exact-type test and **before**
  the `__len__` guard.
- Consumed by, measured at `d2caacf` by reading and confirmed with
  `grep -rn 'coerce_scalars' src/`: `runner.py` (a step's return), `apparatus.py` (`check_facts`),
  `cli.py` (a template's `aggregate`, a derived metric, a null-test draw), `artifacts.py`
  (`io.record`, both branches). **Task 6 and task 9 add two more callers, which is why this task
  precedes both.**

- [ ] **Step 1: write the branch, and state which ground each half rests on.** `_coerce_one` tests
      `type(value) in _SCALARS` — exact, because `numpy.float64` is a real `float` subclass and an
      `isinstance` test would let it through uncoerced into `yaml.safe_dump`. The next line refuses
      anything with `__len__`, before the protocol checks, because *a NumPy array satisfies
      `__float__`, `__index__` and `__bool__` just as a scalar does*. `np.str_` has `__len__`, so it
      is refused there. The fix is one branch: **a value that is already a `str` by inheritance is
      that string** — `str.__str__(value)`, which returns an exact `str` and preserves the value.
      The docstring must say, separately for each:
      - **`np.str_` coerces because `str` IS in `_SCALARS`.** It is already one of the four types
        this module accepts; the only thing wrong with it is that its type is not exactly `str` —
        the identical situation `np.float64` is in.
      - **`np.bytes_` stays refused because `bytes` is NOT in `_SCALARS`**, and plain `bytes` raises
        the same code with the same message. A `bytes` value has no place in a cell whose reader
        gives back a `str`, and admitting the NumPy spelling of a type core refuses in its Python
        spelling would be the divergence *one rule* exists to prevent. **The `__len__` guard is no
        longer part of the answer for either**, and a fix admitting `np.str_` must not be argued as
        also settling `np.bytes_`.
      - **`str` only, not "any `_SCALARS` type by inheritance".** Measured at `d2caacf`:
        `np.float64` is a `float` subclass and `np.int64` and `np.bool_` are **not** subclasses of
        `int` and `bool`; none of the three has `__len__`, so none reaches the guard and all three
        are handled by the `item()` unwrap — which is exactly why that unwrap must stay ahead of the
        `__index__` fallback. A branch covering all four would be three parts unreachable.
      - **`str.__str__`, not `str()`, and it is a decision rather than a spelling.** Measured:
        `str(Color.RED)` is `'Color.RED'` under Python 3.11+ and would have corrupted the value
        silently; `str.__str__(Color.RED)` is `'red'`, and its type is exactly `str`. The widening to
        every `str` subclass is accepted on purpose — a `str`-enum in a recorded column is a value,
        not a structure — and the alternative, a NumPy-specific type test, would put library
        knowledge in a module whose whole argument is that it tests protocols and not vendors.

- [ ] **Step 2: state what the widening admits, PER CALLER, and pin the two the design does not
      name.** This is the step whose omission would ship a behaviour change unargued.
      - `io.record`, a step's return, a template's `aggregate`, a derived metric: an `np.str_` value
        coerces instead of refusing. That is the point.
      - **`apparatus.check_facts`**: it catches `coerce_scalars`' `ContractError` and re-codes it to
        `E-APPARATUS-FACT-TYPE`, so **an `np.str_` fact value stops drawing that refusal and is
        recorded instead.** Controller requirement 4: **a refusal that stops firing is stated as a
        retirement.** Pin it — an arm asserting the fact resolves and its recorded value is exactly
        `str`. And **check `E-APPARATUS-FACT-TYPE`'s § Errors row rather than editing it**: it
        derives its scope from *"the closed scalar set `coercion` already enforces"*, so it needs no
        edit, and replacing that clause with an enumeration would convert a self-maintaining
        statement into a maintenance obligation nobody owns.
      - **`_coerce_estimate`**: a `str`-subclass `value` used to raise `E-STEP-RETURN-TYPE` from
        `_coerce_one`; it now coerces and then fails `_is_number`, so it raises
        **`E-STEP-ESTIMATE-VALUE`** instead. Same for a `ci95` bound and `E-STEP-ESTIMATE-CI95`. The
        shape refuses before and after — only the code moves, and it moves to the **more precise**
        one. Pin both, and check each code's § Errors row already covers the shape rather than
        widening a row that already does.

- [ ] **Step 3: Fixture C.** `np.str_('a')` coerces to exactly `str` with value `'a'` (asserted with
      `type(...) is str`, not `isinstance`, because `np.str_` passes `isinstance`); `np.bytes_(b'a')`
      and plain `b'a'` both raise `E-STEP-RETURN-TYPE`; a `str`-Enum member coerces to its **value**
      `'red'` — the literal the enum declares, which is why `str.__str__` and not `str()`; and
      `np.array([1.0, 2.0])` and `np.array(1.0)` both **still raise**, which is the positive control
      proving the `__len__` guard still does the job it exists for. **Without the array control the
      arms prove only that something was refused.**

- [ ] **Step 4: the document sentence.** § Steps and artifacts states the mechanism — *core coerces
      anything implementing `__float__`, `__index__`, or `__bool__`*. A `str` subclass coercing is a
      new clause and belongs in the same paragraph, with the retirement named. **Do not touch "One
      rule, all three surfaces" here** — task 9 owns that sentence, and two tasks editing one
      sentence is how a half-edit ships.

- [ ] **Step 5: the mutations — three.**
      (i) **Remove the branch.** Fixture C's `np.str_` arm → raises. *Why the branches differ:*
      measured at `d2caacf`, that exact input raises today; unmutated it returns `'a'`.
      (ii) **Move the branch AFTER the `__len__` guard.** The same arm → raises. *Why the branches
      differ:* the guard refuses `np.str_` first, so **placement is the whole of the fix** — and a
      mutation one line off tests a different property, which has shipped here.
      (iii) **Replace `str.__str__(value)` with `str(value)`.** Fixture C's `str`-Enum arm → the
      value becomes `'Color.RED'`. *Why the branches differ:* measured — the two constructors
      disagree on exactly this input and **agree on `np.str_`**, which is why the enum arm exists at
      all.
      For each: read the failure text and say which assertion failed. Revert by editing in place.

- [ ] **Step 6: run.** All four gates. **Read the full suite output**: this task widens what every
      `coerce_scalars` caller accepts, so an unexpected pass or failure elsewhere is information.

- [ ] **Step 7: commit.** `git add -A && git commit -m "H5a task 10: a str by inheritance is that
      string, with the two grounds and the apparatus retirement named"`.

---

## Task 5: split the constant, refuse a reserved column name, and pin that `by` stays legal

**Surface: `validate`, and a direct call.** Design Decisions 3 and 4. **This task carries the
plan's largest correction against the design** (§ Corrections, correction 1): `RESERVED_COLUMNS` gets
**one** reader, not four.

**Files:**
- Modify: `src/publishable/units.py`
- Test: `tests/test_units.py` (add), `tests/test_validate.py` (add), `tests/test_artifacts.py` (add)
- Read, and confirm no edit is needed: `src/publishable/validate.py`

**Interfaces:**
- Produces: `units.UNIT_FIELDS` and `units.RESERVED_COLUMNS`, replacing `units.RESERVED_FIELDS`.
  **Neither constant is exported** — § The importable surface is the enumerated list and H5a adds
  nothing to it.
- Consumes: nothing new.

**The rename's full surface, swept at `d2caacf` with `grep -rn 'RESERVED_FIELDS' src/ tests/ docs/`
— the whole trees, not the file the name was first noticed in.** Result: `units.py` holds the
definition, three guard sites and three message interpolations; **`validate.py` mentions it in a
COMMENT and does not import it**; `tests/test_validate.py` mentions it in a **docstring** and asserts
nothing about it; every other hit is the development record, which is **never retro-edited**
(`spec-defects.md` excepted, and task 12 owns that entry). **So the rename touches `units.py`, one
comment in `validate.py` and one docstring in `tests/test_validate.py`** — and step 1 re-runs that
sweep rather than trusting this paragraph, because *sweep for the claim, not for the file the claim
was first noticed in* is a habit this repo paid for three times in one slice.

- [ ] **Step 1: split the constant, and write each one's MEMBERSHIP RULE beside it.** A set whose
      membership rule cannot be stated is the failure this split exists to prevent.
      - `UNIT_FIELDS = ("key", "paths", "attributes")` — *can `unit.<name>` reach this attribute?*
        `Unit` is a frozen dataclass whose `__getattr__` resolves attributes, so a field of the same
        name wins and the attribute is unreachable by the accessor the documents give for it. **These
        cannot be freed: the accessor is the type's own API.**
      - `RESERVED_COLUMNS = ("unit", "measurement", "by")` — *would this attribute silently occupy a
        column that already means something?* Each already names a column in a per-unit table or a
        block in the record. **Any of these could be freed** by renaming the column or the block, and
        that different lifetime is the whole ground for two constants.

- [ ] **Step 2: give `RESERVED_COLUMNS` exactly ONE reader, and say why in a comment.** Its only
      reader is the attribute-name check at the three attribute call sites (`_from_table`,
      `_from_glob`, `_from_resolver`). **It must NOT be pointed at `io.record`'s collision guards, at
      `_collapse_measurements`' structural-column exclusion, or at `finalize`'s `key != "unit"`** —
      the design's Decision 3 prescribes all three and **all three would break a legally recorded
      `by` column**: `record` would refuse it, and the other two would silently drop it from
      `units.parquet`. Decision 4's own text, the controller's ruling and § Steps and artifacts all
      say a recorded `by` stays legal. Those three sites answer a **different question** — *may a
      recorded column be named this?* — whose answer for `by` is **yes**. Leave their literals alone;
      the comment states the reason rather than inventing a second constant, because **preferring to
      delete a claim over rewriting it applies to constants too.**

- [ ] **Step 3: add the check at all three attribute call sites, in one order.** `UNIT_FIELDS` first,
      then `RESERVED_COLUMNS`, then the existing unsourced check — **the same order at all three**,
      which is what `_from_table`'s own comment already asks for (*"reserved before unsourced, so one
      declaration draws one code whichever source it sits under"*). The message names the offending
      attribute and says which column it would occupy.

- [ ] **Step 4: MEASURE which surfaces report it, then state it — do not assume two.** The design's
      own § What could not be measured leaves this open. Measured at `d2caacf` by reading:
      `validate._check_units` calls `resolve_units` inside `except ContractError` and reports the
      code under `data.units`; `command_run` calls `validate_config` **first** and returns
      `EXIT_WRONG` on any error, before its own `resolve_units` call. **So there is one emit path and
      `run` meets it through `validate`** — write it that way, on `E-UNITS-ATTR-MISSING`'s row as the
      precedent for how a dual-surface raise is written down, and **confirm by running both commands**
      rather than by reading alone.

- [ ] **Step 5: Fixture A — the reserved attribute name, with a decoy on EACH side.** Three arms —
      `unit`, `measurement`, `by` — each declared in a `data.units.attributes` list that **also**
      holds `aaa_site` sorting before it and `zzz_site` sorting after it. Grounds: the existing
      refusal reports the first offending name and stops, so a fixture with the reserved name in one
      position cannot distinguish *reports the first offender* from *reports the first name* or from
      an ordering that happens to agree. **Two names only ever distinguish two answers.**
      **The fixture's table must carry `unit`, `measurement`, `by`, `aaa_site` AND `zzz_site` as real
      columns.** Without the decoy columns every arm fires on `E-UNITS-ATTR-MISSING` — a mutation
      firing for the wrong reason, which has shipped here — and without the reserved names as columns
      the arm cannot show the refusal is about the name rather than about the missing column.
      Each arm asserts `E-UNITS-ATTR-COLUMN` **and** that the message names the offending attribute.
      A fourth arm declares `paths` and asserts `E-UNITS-ATTR-RESERVED`, **which is what proves the
      two codes are told apart rather than one having swallowed the other.** Run every arm through
      `validate_config` (so the report path is exercised) **and** through `resolve_units` (so the
      resolution path is).
      **The glob arm is different and must be written differently:** `_from_glob` refuses *every*
      declared attribute as unsourceable, so a leading decoy raises `E-UNITS-ATTR-MISSING` first.
      The glob arm declares the reserved name **first** or alone, and its docstring says why it
      cannot carry the decoys its siblings do.

- [ ] **Step 6: pin that a `by` COLUMN survives — the arms § Corrections correction 1 exists for.**
      Two assertions, both reading the parquet back:
      (a) a **plain** `io.record` payload with a column named `by` reaches `units.parquet` with its
      value (and, at `run`, draws `W-STATS-STRATUM-SHADOWED`, which is already shipped — grep before
      claiming anything about it);
      (b) a **`measurement=`**-recorded column named `by` **survives `_collapse_measurements`** into
      `units.parquet`. **Declare `collapse: first`, or give `by` a numeric value, and say which in the
      arm's docstring with the reason.** `_collapse_measurements` calls `rule_for("by", collapse)` and
      then `coerce_for_rule`, so under a numeric rule a string `by` value **refuses before the arm can
      observe survival** — and an implementer would read that refusal as the guard working. A fixture
      that fires for the wrong reason has shipped here.
      Without these two arms, a later slice re-points those guards at the constant and the column
      vanishes with the suite green.

- [ ] **Step 7: the mutations — four.**
      (i) **Drop `unit` from `RESERVED_COLUMNS`** (then, separately, `measurement`, then `by`).
      Fixture A's arm for that name → validates clean. *Why the branches differ:* each arm names one
      member, so a one-member deletion fails **exactly one** arm — a single arm covering all three
      would fail on any deletion and tell nobody which.
      (ii) **Point the attribute check at `UNIT_FIELDS` alone.** Fixture A's three arms fail and the
      `paths` arm passes. *Why the branches differ:* the two constants are disjoint, so aiming at one
      is observable through the other.
      (iii) **Raise `E-UNITS-ATTR-RESERVED` for a reserved column.** Fixture A's code assertions
      fail. *Why the branches differ:* the arms assert the codes separately — **this is the mutation
      that makes Decision 4's mint load-bearing rather than decorative.**
      (iv) **Point `finalize`'s `key != "unit"` at `RESERVED_COLUMNS`.** Step 6(a) must FAIL, on the
      **column's absence from the file**. *Why the branches differ:* `by` is in the constant and not
      in the literal, so the recorded column is dropped — the defect this task's correction exists to
      prevent, and it is caught by a file assertion and by nothing else.
      For each: read the failure text and say which assertion failed. Revert by editing in place.

- [ ] **Step 8: run.** All four gates. Report the test-count delta.

- [ ] **Step 9: commit.** `git add -A && git commit -m "H5a task 5: split the constant, refuse a
      reserved column name, and pin that a recorded by column survives"`.

---

## Task 6: coerce roster attribute values at `resolve_units`, and PIN THE ORDERING

**Surface: `validate`, and a real `run`.** Design Decision 6 and **controller requirement 3: this
decision is load-bearing and the plan must pin the ORDERING, not just the coercion.** Coercing at
`resolve_units` exists because task 9's coercion alone would turn a **completed** run into a
`ContractError` inside `finalize` — **after every execution is paid for**, which is this repo's named
habit *every execution paid for, the record lost*.

**Files:**
- Modify: `src/publishable/units.py`, `docs/reference.md` (§ Errors core raises, § Where units come
  from)
- Test: `tests/test_units.py` (add), `tests/test_validate.py` (add), `tests/test_cli.py` (add)

**Interfaces:**
- Consumes: `coercion.coerce_scalars` — the fourth call site of the one scalar walk. **Task 10 must
  have landed**, or a resolver yielding an `np.str_` attribute, which works today, starts refusing.
- Produces: `Unit.attributes` values that are **guaranteed scalars for every consumer** —
  `cluster_by`, `weight_by`, a fold's `stratify_by`, `holdout.from` and `_attributed`'s merge all
  read them. That is a real invariant this build does not currently have.

- [ ] **Step 1: read the docstring the design tells you to read, not this paragraph.** The design
      checked that this coercion cannot move a published number and says *"Task 6's implementer should
      re-read that docstring rather than trust this paragraph."* Re-read `cli._attributed`'s
      docstring, which names the hazard by hand: a numeric attribute *"would be published as a metric
      with its own `ci95` … not reachable while every roster attribute arrives from `csv.DictReader`
      as a string, and the reason not to depend on that staying true."* Confirm for yourself that the
      merge is into the table's **rows only, never into `collapsed`**, and that `stats._is_numeric` is
      an `isinstance` test while `numpy.int64` is **not** an `int` subclass (measured at `d2caacf`).
      **State your own conclusion in the report** — if the merge has moved since, this task's scope
      has changed.

- [ ] **Step 2: place the coercion, and pin the placement.** Run every attribute mapping through
      `coerce_scalars` **at the end of `resolve_units`, immediately before `return UnitList(units)`**
      — after the source, after `collapse_measurements` (which can itself produce a numeric attribute
      value through `apply_rule`) and **after the uniqueness loop**, so a roster that is both
      duplicate-keyed and structurally-attributed still reports `E-UNITS-KEY-DUPLICATE`, the fault
      about the roster's identity, exactly as it does today. Rebuild each `Unit` unconditionally —
      `Unit` is frozen, `__post_init__` re-wraps `attributes`, and a conditional rebuild would add a
      branch whose two sides no fixture separates. **Pin the placement** with one arm: a resolver
      yielding two units sharing a key, one of them carrying a structural declared attribute →
      `E-UNITS-KEY-DUPLICATE`.

- [ ] **Step 3: widen `E-RESOLVER-YIELD` rather than minting.** By Decision 4's own test the fault
      does not differ: `E-RESOLVER-YIELD` already means *what this resolver yielded is not something
      core can build a roster row from*, and a `Unit` carrying an unusable attribute value is that
      fault in a second shape. Only a resolver can produce it — a table source hands every value
      through `csv.DictReader` as a `str` and a glob yields no attributes at all — so the family is
      right. **Widen its § Errors row to cover both shapes; mint nothing.** Note in the docstring that
      the coercion runs over every source's values at one site, and that the code is a resolver's
      because a resolver is the only source that can produce the fault.

- [ ] **Step 4: state stoppage 4 and the identity cost.** § Where units come from is where a reader
      learns what `Unit.attributes` may hold; state that an attribute value is a scalar under the same
      coercion every other surface uses, with what ran before (a resolver-yielded list **wrote a list
      column into the published inference base**, measured) and what happens now. And state the cost
      the design names so the implementer does not discover it: the `Unit` a resolver constructed is
      replaced by an equal-but-coerced one — `Unit` is frozen and hashable by `key`, so nothing
      promises object identity, but a resolver holding a reference to its own yielded object and
      expecting core to hold the same one would be surprised. **Put that in the docstring, not only
      in the report.**

- [ ] **Step 5: Fixture R.** A registered resolver yielding
      `Unit(key=…, attributes={"tags": [1, 2], "site": "north"})` **with `tags` declared in
      `data.units.attributes`** — measured at `d2caacf`: `_from_resolver` projects onto the declared
      list, so an **undeclared** structural attribute is dropped and never refuses. Assert
      `E-RESOLVER-YIELD` at `validate`. Its **positive control** is the same resolver yielding
      `{"score": np.float64(1.5), "site": "north"}`, asserting the roster resolves and that
      `roster[0].attributes["score"]` is **exactly `float`** — `type(...) is float`, not
      `isinstance`, because `np.float64` passes `isinstance`. **Without that control the arm proves
      only that something was refused.** Build the resolver on `tests/test_cli.py`'s
      `_install_plate_wells_resolver` shape rather than inventing one.

- [ ] **Step 6: THE ORDERING PIN — a real `run`, two arms.** This is controller requirement 3 and it
      is the reason this task is not just a coercion.
      - **Arm O1:** `run_a_project(..., units_overrides={"from": {"resolver": …}},
        unit_attributes=[…], expect_exit=EXIT_WRONG)` against a resolver yielding a structural
        declared attribute value. Assert the diagnostic names `E-RESOLVER-YIELD`, **and that
        `output_dir` holds no `run_*` directory at all**, and that no `latest` pointer exists. That
        second assertion is the ordering: **nothing was paid for.** The exit code alone is not the
        pin — it is the same in both branches.
      - **Arm O2, the positive control:** the same project with the resolver yielding
        `np.float64` instead. The run completes, a `run_*` directory exists, and `units.parquet` holds
        the attribute column. **Without O2, O1 passes identically if the run never started for an
        unrelated reason.**
      - **Read `run_a_project`'s returned keys rather than assuming them** — it returns the run
        directory and the resolved paths, and with `expect_exit=EXIT_WRONG` the run directory may not
        exist. Take `output_dir` from the returned paths.

- [ ] **Step 7: the mutations — three, and SAY WHAT THE PIN'S FAILURE LOOKS LIKE.**
      (i) **Remove the coercion from `resolve_units`.** Fixture R's refusal arm → the structural value
      survives to the roster, **and** the control arm's `type(...) is float` assertion fails. *Why the
      branches differ:* two assertions, two directions — one proves the refusal, one proves the
      coercion, and a single arm would leave the coercion half unpinned, which is Decision 6's actual
      payload. **And arm O1 must FAIL on the run-directory assertion** — a `run_*` directory now
      exists, holding `manifest/`, `environment/` and at least one step directory. **That is what the
      ordering pin's failure looks like: the run executed.** Note that task 9 has not landed yet, so
      the mutant's run *completes* rather than raising inside `finalize`; task 11 re-runs this
      mutation on the finished branch, where the full shape — every execution paid for, the record
      lost — is observable. Say both in your report.
      (ii) **Make the coercion refuse `np.float64` rather than coerce it.** Fixture R's control arm
      fails. *Why the branches differ:* the control asserts a **resolved** roster, so refusal and
      coercion are different outcomes.
      (iii) **Move the coercion above the uniqueness loop.** Step 2's placement arm → reports
      `E-RESOLVER-YIELD` instead of `E-UNITS-KEY-DUPLICATE`. *Why the branches differ:* the fixture is
      built to violate both, and which one is reported is exactly the placement.
      For each: read the failure text and say which assertion failed. Revert by editing in place.

- [ ] **Step 8: run.** All four gates. Report the test-count delta. **Read the full suite output**:
      this task changes what every roster's attribute values are, and roughly sixty existing call
      sites reach `resolve_units`.

- [ ] **Step 9: commit.** `git add -A && git commit -m "H5a task 6: coerce roster attribute values at
      resolve_units, and pin that nothing is paid for before the refusal"`.

---

## Task 7: `io.record`'s plain branch refuses a `measurement` column

**Surface: a direct call.** Design Decision 9. **The real-command surface for this guard arrives with
task 9's end-to-end run**, which goes through `io.record` on the way to `finalize`.

**Files:**
- Modify: `src/publishable/artifacts.py`
- Test: `tests/test_artifacts.py` (add)

- [ ] **Step 1: read the asymmetry, then close it.** Measured at `d2caacf`, filed nowhere:
      `io.record(key, {"measurement": …})` **without** `measurement=` is accepted and writes a
      `measurement` column into `units.parquet` —
      `[{'unit': 'U1', 'site': 'n', 'measurement': 'HIJACK', 'v': 1.0}]` — while the `measurement=`
      branch refuses the identical key with `E-STEP-KEY-COLLISION`. Add the mirror guard to the plain
      branch, with the same code and a message naming the same reason. **Grounds, in the comment:**
      in one step's directory `units.parquet` and `measurements.parquet` are siblings, and
      `_collapse_measurements` **consumes** the measurement axis on its way into `units.parquet` — the
      column is dropped there precisely because it has no meaning once the rows are one unit. So a
      `measurement` column in `units.parquet` means *the axis, consumed* for a measured unit and
      *whatever the step recorded* for a plain one, in the same file, in the same column.

- [ ] **Step 2: unconditional, not gated on whether `data.units.measurements` is declared.** The
      `unit` guard is unconditional and this matches it. Gating would make one line of step code
      legal or illegal depending on a config block elsewhere — the same *"depending on which call the
      step happened to make first"* arbitrariness `record`'s own docstring argues against for the
      settle rules. **State that in the comment**, because the gated version is the plausible
      alternative and a later reader will ask.

- [ ] **Step 3: Fixture M — three arms, and the third is what stops the first two being a test of
      nothing.** Arm 1: plain `io.record` with a `measurement` key → `E-STEP-KEY-COLLISION`. Arm 2:
      the same key through `measurement=` → the same code — **already passing today, and kept, because
      the symmetry is what the test asserts.** Arm 3, the control: a plain record with a column named
      `measurements` (**plural**) **writes**, asserted by reading the parquet back and finding the
      column — because a guard written as a prefix or substring test would swallow it.

- [ ] **Step 4: the mutation.** Replace the plain branch's guard with a substring or prefix test
      (`"measurement" in key` over the keys). **Fixture M's arm 3 must FAIL**, on `measurements`
      refusing. *Why the branches differ:* measured at `d2caacf` — the plural column writes today, so
      the mutant and the original disagree on it. Read the failure text; revert by editing in place.

- [ ] **Step 5: run.** All four gates. Report the delta.

- [ ] **Step 6: commit.** `git add -A && git commit -m "H5a task 7: io.record's plain branch refuses a
      measurement column, closing an asymmetry nothing filed"`.

---

## Task 8: `finalize`'s `columns` list is deduped by name

**Surface: a direct call.** Design Decision 10.

**Files:**
- Modify: `src/publishable/artifacts.py`
- Test: `tests/test_artifacts.py` (add)

- [ ] **Step 1: dedupe the list, and claim only what the dedupe does.** `columns = ["unit",
      *attribute_names, *recorded]` can hold `"unit"` twice: `recorded` excludes it,
      `attribute_names` does not. Dedupe by name, preserving first-seen order. **The comment must
      NOT argue that task 5's refusal makes the duplicate unreachable** — `finalize` is called with a
      `UnitList` core constructs, and a `Unit` is on § The importable surface, so a caller can build
      one directly. *A list whose correctness depends on a refusal three modules away is a safety
      argument in a comment; deduping locally is one line and needs no argument.*

- [ ] **Step 2: state the residual rather than implying it** (§ Corrections, correction 5). Measured
      at `d2caacf`: the row comprehension already collapsed the duplicate, so **the file's shape was
      never wrong** — but the attribute merge **overwrites** `merged["unit"]`, so a directly
      constructed `Unit` carrying an attribute named `unit` still publishes the attribute's value in
      the unit-key column. **The dedupe fixes the list, not the value**, and only task 5's refusal
      closes it for a config. Say exactly that in the docstring, and no more. Task 12 files the
      residual for a direct caller; **this task does not build a guard for it** — that would be a
      fifth stoppage nobody argued.

- [ ] **Step 3: Fixture D.** A `UnitList` built directly, one `Unit` carrying an attribute named
      `unit`, and the assertion on **the column list `finalize` builds** rather than on the file —
      since the file's shape is already correct, an assertion on the file would pass before and after
      and prove nothing. **The claim is about the list, so the assertion is about the list.** Reach
      the list without changing `finalize`'s signature: assert on the parquet's **column order** for
      a row set where the duplicate would be visible, or extract the list into a module-level helper
      `finalize` calls and assert on the helper. **Choose one and say why in the report** — if you
      extract a helper, the mutation must be applied at the call site and not only in the helper's
      body, because *a mutation applied to a proxy* has shipped here.

- [ ] **Step 4: the mutation.** Delete the dedupe. **Fixture D's list assertion must FAIL.** *Why the
      branches differ:* measured — the list holds `unit` twice today and **the file's bytes do not
      change**, so only a list assertion can tell them apart. This is one of the two mutations
      **named as blind in the design** for a file assertion: do not read a file arm's silence as
      confirmation. Read the failure text; revert by editing in place.

- [ ] **Step 5: run.** All four gates, and confirm task 13's arm A and arm B stay green — this task
      must move no byte.

- [ ] **Step 6: commit.** `git add -A && git commit -m "H5a task 8: dedupe finalize's columns list,
      and state what the dedupe does not fix"`.

---

## Task 9: the two row-shaped writers coerce, and `io.write` names the artifact

**Surface: a real `run`, and direct `StepIO.write` calls.** Design Decisions 5 and 8. **This is the
slice's behaviour change**, and its review is a real-command review: H7d Part A's only Critical was
invisible to every direct-call probe and surfaced only through an end-to-end run.

**Files:**
- Modify: `src/publishable/artifacts.py`, `docs/reference.md` (§ Steps and artifacts)
- Test: `tests/test_artifacts.py` (add), `tests/test_cli.py` (add)

**Interfaces:**
- Consumes: `coercion.coerce_scalars` — the fifth call site. **Task 10 must have landed**, or a
  `.parquet` write of a NumPy string column refuses.
- Modifies: `_encode_csv`, `_encode_parquet`, `_check_column_types`, `StepIO.write`. **`WRITERS`'
  signature does not change** — it is a plugin contract and may not grow a parameter.
- Does not touch: `_encode_json`, `_encode_yaml`, `_encode_jsonl`, or any plugin writer. **No
  coercion runs for them**, deliberately (Decision 5), and task 12 files what that leaves open.

- [ ] **Step 1: one shared helper, called at TWO sites.** Write one module-level function that takes
      the row sequence and returns a list of coerced row dicts, refusing a non-mapping row with
      `ArtifactError` · `E-ARTIFACT-UNWRITABLE` — **the code § Steps and artifacts already promises
      for "handing a writer anything else"**, so this makes an existing documented refusal true rather
      than inventing one. Call it from `_encode_csv` and from `_encode_parquet`. **Two call sites, not
      one shared body reached once**, so the design's two separate mutations stay expressible. The
      non-mapping guard must come **before** anything iterates the row's keys — measured at `d2caacf`,
      a non-mapping row raises a bare `TypeError` out of `_encode_parquet` and a bare `AttributeError`
      out of `_encode_csv` today. The `where` passed to `coerce_scalars` is the row's **index**, so
      the refusal names the row.

- [ ] **Step 2: `io.write` prefixes the artifact name onto a writer's `ContractError`.** A writer sees
      rows and not a name. So wrap the `WRITERS[suffix](obj)` dispatch in **one** `except
      ContractError` and re-raise with the artifact name **prefixed and the code preserved**,
      `from exc` — the same catch-and-re-code `apparatus.check_facts` already makes over
      `coerce_scalars`. **It prefixes and never rewords**, so a plugin writer's own message survives
      inside it. **A recipe is its calls plus where they sit: this `try` encloses the dispatch and
      nothing else**, so `io.path`'s existence check and `_resolve`'s containment refusal are outside
      it. **Read `check_facts` before writing this**, and copy where its `try` sits, not only what it
      calls — H8c shipped a credential leak by lifting calls out of their `try`.

- [ ] **Step 3: `_check_column_types` states its precondition, and its message loses the surface
      enumeration.** Its docstring must say **its input is already coerced and its correctness depends
      on that** — a safety claim, whose mutation is step 7(i). And its message currently reads *"io.
      record's values, a step's return, and a template's aggregate take the same scalars"*, which
      **names a surface the caller was not using** once an `io.write` caller reaches it. **Delete the
      enumeration rather than threading a `where` parameter** (§ Corrections, correction 4): the
      caller-identifying half is supplied by step 2's prefix at every reachable path including
      `finalize`'s own write, and a parameter with one caller and one possible value pins nothing.
      Keep the column name, both type names and one row identifier for each.
      **Do NOT add a second, coercion-aware normalization.** With coercion in front of it, every
      value the check sees is exactly `bool`, `int`, `float`, `str` or `None`, so `float if actual in
      (int, float) else actual` is **correct as written** and the surviving groups are exactly
      `{bool, float, str}`. A second normalization would put NumPy knowledge in two modules and create
      a branch **no fixture can reach** — and the two-name message (*"recorded both a bool … and a
      bool"*, measured at `d2caacf` for `np.bool_` beside `bool`) is closed by making its case
      **legal**, not by editing the message: after coercion no two surviving groups can report the
      same type name. **That is why the pin is a round-trip assertion rather than a message
      assertion.**

- [ ] **Step 4: the document work — the writer/reader table, split, and the coercion stated.**
      - **Split the `.csv · .parquet` row.** Measured at `d2caacf`: `_decode_csv` gives back **every**
        value as a `str` — `[{"v": 1.0}]` reads back `[{'v': '1.0'}]` — so *"what a writer takes is
        what its reader gives back"* is false for `.csv` across the board and **coercion does not fix
        it.** State the exception in the same paragraph, or the coercion statement ships beside a claim
        contradicting it.
      - **State the coercion and which formats it covers**: the two row-shaped writers, and not
        `.json`/`.yaml`/`.jsonl`, whose documented input is any nesting, and not a plugin's format,
        whose input stays the plugin's business. Give the ground: the rule belongs to the **format**
        whose contract states it.
      - **"One rule, all three surfaces" becomes false.** Widen it, and **drop the count** rather than
        raising it — counts in prose are what that rule exists to prevent. Grep for the phrase across
        the four documents, `CLAUDE.md` and the feasibility analysis before editing; measured at
        `d2caacf` it appears in `reference.md` once, and `coercion.py`'s module docstring paraphrases
        it. **`CLAUDE.md`'s invariant sentence is about what a step's `run` and a template's
        `aggregate` RETURN and stays true — do not edit it.**
      - **Stoppages 1 and 2, each findable, and stoppage 1 written as TWO halves**
        (§ Corrections, correction 2). For `.csv`: a structural cell was silently written as its
        `repr` and read back as a string, and a `bytes` cell as `b'x'` — the refusal **converts silent
        corruption into a loud refusal.** For `.parquet`: a structural cell and a `bytes` cell both
        **round-tripped intact** (measured), so the refusal **takes a working round trip away**, on
        the *one rule, all surfaces* ground and on the `_SCALARS` ground rather than on a corruption
        ground. **Do not write "was corrupt" for `.parquet`.** For the non-mapping row: it raised a
        bare traceback and now raises the documented code.
      - **State the retirement** (controller requirement 4): `.parquet` rows mixing a NumPy scalar
        with its Python counterpart — the shape § Steps and artifacts' own worked step produces —
        **stop raising.**

- [ ] **Step 5: Fixture S — the structural cell, on each side of the row set.** A `[1, 2]` cell in the
      **first** row and a `[1, 2]` cell in the **last** row of a multi-row set, each arm asserting the
      refusal names the column, the row index **and the artifact**. Both formats, because the two
      disagreed before this slice and the disagreement is the defect. **Both sides, because a check
      that stops at the first row passes a fixture whose only offending row is the first** — the
      decoy-sort-position trap in its row-order form, which this repo has hit twice, the second time
      after the first was caught and disclosed.

- [ ] **Step 6: Fixture N — the non-mapping row, and its control.** A `.csv` and a `.parquet` write
      whose rows are `[{"v": 1.0}, "not a mapping"]`, asserting `ArtifactError` ·
      `E-ARTIFACT-UNWRITABLE` **rather than** `AttributeError` or `TypeError`. The claim is the *type*
      of the failure, so assert the exception class and the code. **A control writes the same rows
      with the string removed and asserts the file exists** — without it the arm passes if nothing
      was written at all.

- [ ] **Step 7: the mutations — five.**
      (i) **Delete the coercion call from `_encode_parquet`.** Fixture W's `np.float64`-beside-`float`
      arm (task 11) → raises `E-STEP-RETURN-TYPE` instead of round-tripping; **write a local arm here
      too** so this task's own commit is pinned. *Why the branches differ:* measured at `d2caacf` —
      that exact input raises today and unmutated it writes. **This is also the mutation that pins
      step 3's docstring precondition**, because it reproduces the future caller's mistake.
      (ii) **Delete it from `_encode_csv` only.** Fixture S's `.csv` arm → the list cell writes
      `"[1, 2]"` and the refusal never comes. *Why the branches differ:* the two encoders are separate
      functions, so a mutation in one must be caught by a `.csv` assertion — the `.parquet` arm stays
      green, which is why both formats are in every arm.
      (iii) **Change `_check_column_types`' normalization from `float if actual in (int, float)` to
      `actual`.** Fixture W's `int`-beside-`float` arm → raises instead of promoting. *Why the
      branches differ:* measured — promotion is the current behaviour and the mutant refuses it.
      **The reverse mutation (folding more types together) is NOT prescribed**: after coercion the
      surviving types are `{bool, float, str}` and folding any two changes no legal outcome — **a
      mutation whose branches cannot differ, named here so nobody writes it.**
      (iv) **Delete the `except ContractError` wrapper in `io.write`.** Fixture S's assertion that the
      message names the **artifact**. *Why the branches differ:* the writer's own message names the
      column and the row and **never** the artifact, so the two messages differ in a substring the
      assertion picks. **Checked: no other part of the message contains the artifact name**, so this
      is not an assertion neighbouring output satisfies — but re-check it against the message you
      actually wrote, since three assertions in one recent batch were satisfied by neighbouring
      output.
      (v) **Widen that wrapper to enclose the whole body of `io.write`** (and widen the `except` to
      the shared base, which the mutation requires to be expressible at all). The control: the
      `E-ARTIFACT-UNWRITABLE` message for an **unregistered suffix** must not gain a prefix. **Assert
      it as `msg.count(name) == 1` and `not msg.startswith(f"{name}:")`** — that raise's message
      already contains the artifact name, so "not prefixed" as the design words it is unassertable
      (§ Corrections, correction 3). *Why the branches differ:* that raise sits in `io.write`'s own
      `else` branch, outside the dispatch, so a body-wide wrapper reaches it and a dispatch-only one
      does not. **`io.path`'s `ArtifactExistsError` cannot serve here**: it is an `ArtifactError`
      sibling of `ContractError`, so an `except ContractError` never catches it, widened or not, and a
      control built on it passes in both branches — **a mutation whose two branches cannot differ,
      named so nobody writes it.**
      For each: read the failure text and say which assertion failed. Revert by editing in place.

- [ ] **Step 8: the real-command arm, and the sweep.** A real `run` through `run_a_project` completing
      with `units.parquet` **byte-identical to task 13's capture** — confirm arms A, B1, B2 and C are
      green and say so, rather than asserting byte identity from your own reasoning. Then re-run the
      row-shaped-`io.write` sweep over the named file list (`src/publishable/templates/`,
      `generators/`, `readme_templates/`, `scaffold.py`, `plugin_scaffold.py` and the four documents)
      and confirm no generated or documented example starts refusing. **Filter the file list, never
      the output**, and prove the sweep can fail by running it against a string known to be present.

- [ ] **Step 9: re-read the § Errors rows task 3 wrote.** They describe this code, and a row and a
      code are the same check seen from two ends. Report whether each row is now true of the code, and
      **name every emit site you read**, not a count.

- [ ] **Step 10: mechanical pass, then run.** All four gates. Report the delta.

- [ ] **Step 11: commit.** `git add -A && git commit -m "H5a task 9: the two row-shaped writers
      coerce, io.write names the artifact, and § Steps and artifacts says which formats"`.

---

## Task 11: Fixture W, Fixture E, and the whole-branch mutation re-run

**Surface: direct calls, plus the branch's own suite.** **Narrowed from the design's task 11 by
deviation (b)**: every decision-specific fixture ships in the task that made the decision, and this
task keeps the cross-cutting pins no single code task can own.

**Files:**
- Test: `tests/test_artifacts.py` (add)

- [ ] **Step 1: Fixture W — the writer round trip, per format.** Rows built in the test, written
      through a real `StepIO.write`, read back through the registered reader. Arms: homogeneous
      `float`; `np.float64` beside `float`; `np.str_` beside `str`; `np.bool_` beside `bool`; `int`
      beside `float`. Both `.csv` **and** `.parquet`, because the two disagreed before this slice.
      - For `.parquet`: compare to the **input rows as coerced** — not to a hand-written expectation,
        so the claim is the round trip rather than a literal someone typed — and assert the
        `int`-beside-`float` arm's every decoded value is a `float` **by `isinstance` over the decoded
        rows**, which is the promotion, computed rather than written down.
      - For `.csv`: **compare to `str()` of the coerced value, not to the coerced value**
        (§ Corrections, correction 2). Measured at `d2caacf`: `_decode_csv` returns a `str` for every
        value, so an equality against the coerced rows fails for **every** arm and an implementer who
        wrote it would "fix" it by weakening the `.parquet` half. State the asymmetry in the
        docstring and cite § Steps and artifacts' split row.

- [ ] **Step 2: Fixture E — the empty and all-`None` row sets.** An empty row list writes an empty
      table and raises nothing; a column whose every value is `None` round-trips as `None` in every
      row. Both formats. **These are the arms a coercion change is most likely to break silently**,
      and both are asserted on the **decoded** rows. Measured at `d2caacf` for `.parquet`: an empty
      row set writes, and `[{"v": None}, {"v": None}]` round-trips.

- [ ] **Step 3: Fixture B's cross-spelling arm, declared weak in its own docstring.** The
      NumPy-spelled and Python-spelled versions of one column written to two artifacts and the two
      files' **bytes** compared, both formats. **Its docstring must say what it can and cannot see:**
      after coercion the two inputs are the same coerced rows, so byte equality is **true by
      construction** and this arm discriminates only *coercion present* versus *coercion deleted* —
      the same thing Fixture W's arms catch. **The claim "a legal run's artifacts are byte-identical"
      is pinned by task 13's arms A, B1 and B2 and by nothing here.** Written down so nobody reads
      this arm as the pin controller requirement 2 asked for.

- [ ] **Step 4: re-run EVERY mutation in this plan on the finished branch, and read each failure.**
      Tasks 2, 5, 6, 7, 8, 9, 10 and 13 each prescribe theirs. Two things this re-run exists for that
      no per-task run could see:
      - **Task 6's mutation (i) in its full shape.** Remove the coercion from `resolve_units` with
        task 9 landed: the run now **executes and raises `ContractError` inside `finalize`** — every
        execution paid for, the record lost. Confirm arm O1 fails on the run-directory assertion and
        **describe the mutant's end state from the artifacts you find on disk**, not from this
        sentence.
      - **The two mutations named blind in advance.** Emptying `_check_column_types`' body leaves the
        suite green in the NumPy cases *after* task 9 lands, because coercion has already removed the
        clash — that is task 9 step 3's point, **not** evidence the check is dead, and task 13's arm C
        (bool/int and str/int through a real `io.write`) is what keeps it honest. And task 8's dedupe
        deletion changes no file's bytes, which is why its assertion is on the list. **A mutation that
        changes nothing is evidence about the tests, not about the code.**

- [ ] **Step 5: run.** All four gates. Report the delta.

- [ ] **Step 6: commit.** `git add -A && git commit -m "H5a task 11: Fixture W per format, Fixture E,
      and the whole-branch mutation re-run"`.

---

## Task 12: the filings, and both consistency passes

**Surface: documents.** **Its own batch and reviewed** — three of one gate's four Majors lived in
exactly such a commit, because a documents-and-filings task looks like the safest one to skip and is
the one whose output no later batch reads.

**Files:**
- Modify: `docs/superpowers/spec-defects.md`
- Read, and edit only if the sweeps require it: `README.md`, `docs/design-principles.md`,
  `docs/experimental-designs.md`, `docs/reference.md`, `CLAUDE.md`,
  `docs/feasibility-llm-growth-studies.md`

- [ ] **Step 1: close and STRIKE, never delete.** `spec-defects.md` is the one file in the
      development record where a closed gap is **struck** rather than left to mislead, and the rest of
      the record is never retro-edited. Each of these needs its status line rewritten against what
      the branch actually did — **re-read the entry before writing, because a filing's claims about
      the code go stale like any other comment:**
      - The `units.parquet` **type-unification** entry: its live half is *"`reference.md` § The
        per-unit tables states no rule for cross-row type unification at all"* — closed by task 1.
        Its dead half is the S5 amendment's prediction that H5 *"also lands non-numeric recorded
        columns"* — that is **H5b's**, and it is struck.
      - The **`np.str_` / `np.bytes_`** row in the S4a residue table: closed by task 10, with **which
        ground each half rests on** named, since the entry pairs the two and the branch separates
        them.
      - The **`unit`-shadow** entry: closed by task 5, and **its severity bound is widened** — the
        entry says the damage is confined to the published `units.parquet`, and § Steps that need
        every condition's `io.read_condition(c, "step02_score", "units.parquet")` means the shadow
        also corrupts **what a `summary` step reads.** Its prediction that the fix *"touches
        `reference.md` § Errors core raises"* is **wrong** (measured: the sibling code lives in
        § Errors `validate` reports) and is struck rather than rewritten.
      - The **`finalize` `columns` duplicate** clause: closed by task 8, **and the residual stated** —
        the dedupe fixes the list, not the value, and a directly constructed `Unit` carrying an
        attribute named `unit` still publishes the attribute's value in the key column.
      - Both **H5-owned residue rows** that are not H5a's — the non-numeric-column half of the
        `aggregate`-table entry and the unpinned second empty-level gate — are **re-owned to H5b by
        name.** State it as a **fact with a reason**, never as *"whichever slice next touches X"*, the
        form this file rejects at its own re-owning entry.

- [ ] **Step 2: file what H5a leaves open, each unassigned WITH A REASON.**
      - **Coercing the rows a nesting-taking writer receives.** Measured at `d2caacf` and quoted from
        design Decision 5: `io.write("x.yaml", {"v": np.float64(1.0)})` raises a bare
        `yaml.RepresenterError`, and `.json`/`.jsonl` raise a bare `TypeError` for `np.int64` and
        `np.bool_` (`np.float64` and `np.str_` survive `json.dumps` because it accepts a `float`/`str`
        subclass). **That is the traceback-instead-of-diagnostic class `coercion.py`'s own docstring
        says it exists to prevent**, now visibly excluded rather than merely unaddressed. Those three
        take *any nesting*, so the flat walk does not apply: the route is **one recursive walk, three
        writers, one decision.** **No remaining slice has them as its surface** — that is the reason,
        and it is what makes this unassigned rather than orphaned.
      - **A non-`str` column key in a `.csv` or `.parquet`.** Measured at `d2caacf`, this plan's own
        find and named in no design: `[{1: "a"}]` raises a bare `TypeError` out of `_encode_parquet`
        and **writes** through `_encode_csv`. H5a's contract sentence speaks to **values**; a column
        name is a different question, and folding it in would have been scope creep. Unassigned, with
        the same reason.
      - **A directly constructed `Unit` whose attribute is named `unit`** — the residual from step 1.

- [ ] **Step 3: the mechanical pass, in full, over what the branch edited.** Every relative link and
      `#anchor` resolves; no two headings in a file produce the same anchor; every table's rows match
      its header's column count and no row is empty; no line carries trailing whitespace, a tab or
      invisible unicode. **Skip fenced code blocks in all of these** — the docs contain markdown
      inside markdown. `×` not `x`. Hyphen, never an en dash, in anything that becomes an anchor.

- [ ] **Step 4: the cross-document pass, and it is the one that catches real defects.** Name the
      files; never glob `*.md`; **filter the file list, never the output** — a reviewer checking this
      exact rule once lost a true hit to `grep -v superpowers` because the matching line contained
      that path. Prove each sweep can fail. The classes that actually drift here:
      - **`E-UNITS-ATTR-COLUMN` appears in § Validation, § Errors `validate` reports, § Steps and
        artifacts, and `experimental-designs.md` § Mistakes core prevents** — its fourth home, since
        that passage carries a `CLAUDE.md` cross-document invariant (structurally impossible in the
        schema, not merely discouraged) and is false of the code until task 5 lands — and nowhere
        claims a scope narrower than its code. **One row per code, every site** — the shape that was
        a whole-branch Major on H8a and H8b and shipped twice inside H8c.
      - **The reserved-metric sentence in § Steps and artifacts still says its set is one.** Grep for
        "set of one" and check the surrounding paragraph distinguishes the two namespaces.
      - **§ Templates' "whatever the step recorded plus every declared unit attribute" must NOT have
        been edited on this branch.** It is false of the code for a non-numeric recorded column and
        that is **H5b's**; a half-edit here would leave the document asserting a narrowing nobody
        argued. Verify by `git diff` against the branch point, not by reading.
      - **§ Steps and artifacts' writer/reader table reads consistently after task 9's split** — both
        halves of the `E-ARTIFACT-UNWRITABLE` sentence, and the `.csv` exception beside the coercion
        statement.
      - **`E-STEP-RETURN-TYPE`'s row against the finished code**, because task 9 added an end.
      - **Config completeness, enum comments and versions**: H5a adds no config field and no enum
        value, so these should be no-ops — **confirm rather than assume.**
      - **§ Executability's four-row table is repeated character for character** and no fifth number
        appears anywhere on the branch. Grep the branch's whole diff for a bare digit followed by
        "of" and for "now execute".
      - **A sweep for every string the branch removed**, over the four documents named explicitly,
        `CLAUDE.md` and the feasibility analysis. `RESERVED_FIELDS` is the obvious one.

- [ ] **Step 5: run.** All four gates. Test count unchanged by this task.

- [ ] **Step 6: commit.** `git add -A && git commit -m "H5a task 12: close four filings, re-own two
      rows to H5b, file three gaps, and run both consistency passes"`.

---

## Corrections against the code

**Appended by this plan's author and extended by no task.** Each was measured at `d2caacf`. The rule
is `CLAUDE.md`'s: *the plan argues from the spec, and the code outranks both; where they disagree the
code wins and the document changes first.* Recent plans made ten to seventeen corrections each, and
**six of six implementers on one recent slice found a real disagreement** — finding one is expected,
not exceptional.

**1. `RESERVED_COLUMNS` may have exactly ONE reader, and the design's Decision 3 prescribes four.**
Decision 3 says *"Only the guards are re-pointed at the constant — `record`'s collision checks,
`_collapse_measurements`' structural-column exclusion, and `finalize`'s `key != "unit"`."* Measured:
all three would break a **legally recorded `by` column**. `record`'s guards refuse `unit` and
`measurement` and **do not refuse `by`** — a recorded `by` is legal by design, drawing
`W-STATS-STRATUM-SHADOWED`; `_collapse_measurements` excludes `("unit", "measurement")`, so pointing
it at a constant containing `by` **drops a recorded `by` column from the collapse**; and `finalize`'s
`key != "unit"` filter, so pointed, **drops it from `recorded` and therefore from `units.parquet`
entirely.** Decision 3's own supporting claim is also false: it says `_collapse_measurements` spells
*"the same three names as a bare literal tuple"* — the tuple holds **two**, and `by` is not one of
them. **This is not the plan overruling the design; it is Decision 4 applied against Decision 3** —
Decision 4's text, the controller's ruling and § Steps and artifacts all state that a step *recording*
`by` stays legal. **Task 5 gives the constant one reader (the attribute check), leaves the three
literals alone with the reason in a comment, and PINS the `by` column's survival in both `record`
branches** — because prose in a corrections section prevents nothing, and mutation (iv) of task 5 is
what stops a future slice from "finishing" the sweep.

**2. Fixture B cannot pin byte identity, and Fixture W's `.csv` arms cannot compare to coerced rows.**
Two measurements. First: after coercion, `_encode_parquet([{"v": np.float64(1.5)}])` and
`_encode_parquet([{"v": 1.5}])` receive the **same coerced rows**, so byte equality between them is
true by construction and the arm can only fail if coercion is absent — which Fixture W already
catches. The claim controller requirement 2 actually asks to be pinned is *the coercion moved no byte
a legal run writes*, and **only bytes captured before the change can pin that**: hence task 13, whose
arm A (decoded values, exact Python types, column order) is version-robust and load-bearing, and whose
arm B2 (a parquet sha256) is a tripwire with its edit conditions stated in advance, because a hash arm
that fails on a library bump is a pin someone will edit and this repo's record is pins quietly
weakened. Second: `_decode_csv` returns a `str` for **every** value — `[{"v": 1.0}]` reads back
`[{'v': '1.0'}]` — so Fixture W's stated method (*compared to the input rows as coerced*) fails for
every `.csv` arm; task 11 compares against `str()` of the coerced value and says so.
**Consequence for the documents:** § Steps and artifacts' *"What a writer takes is what its reader
gives back"* is false for `.csv` across the board, not only for structural cells, and its single
`.csv · .parquet` row asserts one answer where there are two. Task 9 splits the row — document-only,
in the section it already edits, and squarely inside this slice's own charter of *stating the rules
that were already enforced.*

**3. Stoppage 1 has two halves with different "what ran before", and the design's mutation control for
`io.write`'s wrapper is unassertable as written.** Measured: `.parquet` **round-trips a `[1, 2]` cell
as a list and a `bytes` cell as `bytes`.** So the controller's ground — *"refusing that cell does not
take a working behaviour away; it converts silent corruption into a loud refusal"* — is true of `.csv`
and **false of `.parquet` for both shapes.** The controller's *first* sentence still carries the
refusal (*one documented row, two answers*), and the refusal stands on the `_SCALARS` and
*one rule, all surfaces* grounds — but requirement 1 says the user must find **the sentence that says
why**, and *"was corrupt"* is the wrong sentence for `.parquet`. Task 9 writes the two halves
separately. Separately: the design's control for the widened-wrapper mutation is *"the
`E-ARTIFACT-UNWRITABLE` message for an unregistered suffix is not prefixed with the artifact name"* —
but that message **already contains the name** (*"{name} has no registered writer …"*), so
"not prefixed" is unassertable. Task 9 asserts `msg.count(name) == 1` and
`not msg.startswith(f"{name}:")`.

**4. `_check_column_types` should not gain a `where` parameter.** The design's task 9 prescribes one,
to fix a message that *"names a surface the caller was not using"*. Measured: `_check_column_types`
has exactly one caller (`_encode_parquet`), which cannot know the artifact name — `WRITERS`' signature
is a plugin contract and may not grow a parameter — so `where` would be a parameter with one caller
and one constant value, which pins nothing that an assertion on the constant does not pin better. The
caller-identifying half is already supplied by `io.write`'s prefix at **every** reachable path,
`finalize`'s own write included. So task 9 **deletes** the surface enumeration from the message
instead — *prefer deleting a claim to rewriting it.* **Rejected alternative recorded:** thread `where`
anyway, which becomes correct the moment a second caller exists (see correction 8).

**5. Decision 10's dedupe does not close the `unit` shadow for a direct caller, and the design's
framing invites the opposite reading.** Decision 10 says the duplicate is *"harmless in the file,
because each row is built as a dict comprehension over `columns` and the duplicate collapses."* True
about the **shape** and misleading about the **value**: measured, `finalize`'s attribute loop
**overwrites** `merged["unit"]`, so a `Unit` carrying an attribute named `unit` publishes
`[{'unit': 'HIJACK', …}]` — the identity gone — and the dedupe changes nothing about that. Task 5's
refusal closes it for every config; a directly constructed `Unit` still reaches it, because `Unit` is
on § The importable surface. Task 8's docstring states the residual and task 12 files it; **no guard is
built for it**, because that would be a fifth stoppage nobody argued.

**6. Task 10 must precede tasks 6 and 9, against the design's stated order.** The design orders
*"1–4, then 5–10, then 11, then 12"*. Measured: `coerce_scalars` refuses `np.str_` today (the
`__len__` guard). Task 6 makes it run over roster attribute values and task 9 over written rows, so
landing either before task 10 ships a window in which **a resolver yielding an `np.str_` attribute,
which works today, refuses**, and in which a `.parquet` write of a NumPy string column refuses. No
test covers either, so the window is invisible to the suite — which is the reason to order it rather
than to trust green.

**7. Task 11's fixtures are redistributed, and task 11 is narrowed rather than renumbered.** The
design's single test task would leave every code task shipping unpinned until the end — *a correct fix
shipped unpinned* has happened seven times here — and would leave each code batch's reviewer unable to
see whether the behaviour in front of them is pinned at all. Deviation (b) records the mapping.

**8. Adding cross-row type unification to `.csv` would be a FIFTH stoppage, and is not built.**
Measured: `_check_column_types` is called from `_encode_parquet` only, so
`_encode_csv([{"v": "a"}, {"v": 1}])` **writes** `b'v\na\n1\n'` today. Design task 3 would have the
§ Errors row read *"a written `.csv`/`.parquet` whose rows disagree on a column's type"*, which is
false for `.csv` and would be made true only by a stoppage neither the design nor the controller
disclosed. Task 3 states the disagreement clause for the format it is true of; task 1 states the
unification rule for the per-unit tables, which are `.parquet`. **Route:** if the two formats should
agree, that is a disclosed behaviour change for another slice, and it is the second caller correction
4's rejected alternative was waiting for.

**9. Task 10's widening reaches two callers the design never names, and one of them is a second
retirement.** Enumerated by reading and confirmed with `grep -rn 'coerce_scalars' src/`:
`apparatus.check_facts` catches `coerce_scalars`' `ContractError` and re-codes it to
`E-APPARATUS-FACT-TYPE`, so **an `np.str_` apparatus fact value stops being refused** — a retirement,
and controller requirement 4 says a refusal that stops firing is stated as one. And `_coerce_estimate`
calls `_coerce_one` on `value` and each `ci95` bound, so a `str`-subclass there moves from
`E-STEP-RETURN-TYPE` to `E-STEP-ESTIMATE-VALUE` / `E-STEP-ESTIMATE-CI95` — refused before and after,
but under a different (and more precise) code. Both are pinned in task 10.
`E-APPARATUS-FACT-TYPE`'s § Errors row **derives** its scope from the closed scalar set and needs no
edit, which is the self-maintaining-statement pattern this repo prefers to an enumeration.

**10. `E-UNITS-ATTR-COLUMN` has ONE emit path, not two surfaces, and the design's unmeasured item 5 is
answered by that.** The design asks whether the code *"fires at `run` for a table source as well as a
resolver"*. Measured: `command_run` calls `validate_config` first and returns `EXIT_WRONG` on any
error, before its own `resolve_units` call — so a `run` meets this refusal **through `validate`**, for
every source. Task 5 writes it as one emit path and confirms it by running both commands.

**11. The `unit`-shadow filing's prediction about which document section the fix touches is wrong.**
It says the natural fix *"mints a new `E-` identifier, which means it touches `reference.md` § Errors
core raises"*. Measured: `E-UNITS-ATTR-RESERVED` appears in § Errors **`validate` reports** and in
§ Validation, and in § Errors core raises **not at all** — because `validate` is what reports it.
Task 4's three homes are right; task 12 strikes the prediction rather than propagating it, on
*prefer deleting a claim to rewriting it.*

**12. Row 1 of the four-row table is unmoved, and it was checked by reading rather than by a grep.**
Three of H5a's four new refusals fire at `validate`, so this had to be checked and not assumed. Read
at `d2caacf`: the feasibility analysis declares two `data.units.attributes` lists and § Executability's
stand-in roster names a third set; none of the three contains `unit`, `measurement` or `by`. Its single
`io.record` payload names none of them either. It contains no row-shaped `io.write`. One observation
made while reading and **deliberately not filed**: that payload records `truth` while the E-family
config declares `truth` as an attribute, which is the **shipped** `E-STEP-KEY-COLLISION`
attribute-shadow guard and neither new nor H5a's — and § Executability's predicate runs only the
`data`/`statistics` blocks through `validate_config`, so it is outside row 1 either way. **No task may
file it.**

---

## What could not be measured

- **Whether any real project writes a structural or `bytes` cell to `.csv`/`.parquet` through
  `io.write`.** The only evidence about frequency is that the feasibility analysis contains no
  row-shaped `io.write` at all and that the documents' own row-shaped examples are `result.rows` and
  an elided `table`. The cost of being wrong is a refusal on a use nobody has demonstrated, with
  `.json` as the documented route.
- **Whether `csv.DictWriter`'s `str()` and coercion agree for every scalar, or only for the ones
  probed.** Byte identity was measured for `float`/`int`/`bool`/`str` and their NumPy spellings —
  the set `_SCALARS` closes over — but that is a probe over four types, not a proof over the type
  lattice. Task 13's arm B1 is where it becomes a pin, and it pins the fixture's own row set and no
  more.
- **Whether a plugin writer raising `ContractError` benefits from `io.write`'s prefix or is confused
  by it.** No plugin writer exists to try. Assumed beneficial, because the prefix names the artifact
  and never rewords the message.
- **Whether task 13's arm B2 survives a `pyarrow` bump.** It will not, and that is stated in its own
  docstring with the recapture conditions written in advance rather than left to judgement. **No task
  in H5a touches `uv.lock`**, so within this slice a failure means the coercion moved a legal
  artifact.
- **What a project whose steps write many row-shaped artifacts pays in wall time** for a per-row
  scalar walk on every `.csv`/`.parquet` write. Not measured; `io.record` already pays it per row, so
  the shape is not new, but no task benchmarks it.
- **The interaction between task 6's rebuild and a very large roster.** Every `Unit` is reconstructed
  on every `resolve_units` call. `_from_resolver` already rebuilds its own, so only the table and glob
  paths gain the cost, and no fixture sizes it.

---

## Plan self-review

- **Every claim about the code was measured at `d2caacf`, by reading the file or running the
  behaviour**, and `d2caacf` is a docs-only commit above the design's `38df123`, so the design's
  fixture shapes are reusable while its claims are re-checked. **Twelve corrections**, four of which
  reshape a task: correction 1 (the constant gets one reader and two new pins), correction 2 (task 13
  exists and Fixture W's `.csv` method changes), correction 6 (task 10 moves ahead of two tasks) and
  correction 7 (the fixtures redistribute).
- **No count phrase, positional row locator, call-site enumeration or line-number citation appears
  above** except where a count is the thing being pinned (the gate literals) or the thing being
  corrected. Section citations only.
- **Every mutation names its assertion AND why its two branches can differ on the named fixture**, and
  **three are named as REJECTED or BLIND with the reason**: folding two surviving types together after
  coercion (branches cannot differ), a control built on `io.path`'s `ArtifactExistsError` (never caught
  by an `except ContractError`, widened or not), and emptying `_check_column_types`' body plus deleting
  task 8's dedupe (both blind, for stated reasons).
- **The guard pin's arm D needs no authorized editor at all**, on H8c's arm-D precedent, and arm B2's
  single recapture condition is stated in advance and is unreachable inside this slice. **A pin that
  cannot be legitimately edited is strictly better than one that can.**
- **Controller requirement 3 is pinned as an ORDERING, not as a coercion**: the assertion is that
  `output_dir` holds no run directory, its failure shape is described in advance, and task 11 re-runs
  the mutation on the finished branch where the full *every execution paid for* shape is observable.
- **The four-row table is repeated unchanged, no fifth number appears, and row 4 is left to H5b.**

---

## Correction appended 2026-08-22 — the second controller ruling post-dates this plan, and its task text carries the pre-ruling reading

**This plan was written before the design's SECOND controller ruling**, which narrowed Decision 5 after
measuring that `.parquet` round-trips a structural cell and a `bytes` cell **intact** while `.csv` does
not. Several task texts here therefore describe the **pre-ruling** scope — most visibly task 3's *"a
written `.csv` or `.parquet` row whose value is not a scalar or whose rows disagree on a column's type"*,
which read literally would have `.parquet` refusing a structural cell.

**Task 3's implementer found the ambiguity, resolved it correctly by binding each clause to one format,
and flagged that it could find no passage stating that binding as plainly for the first clause as for the
second.** That flag is why this correction exists.

**The binding rule, for every task after this line.** *A writer accepts what it can give back* — **one
rule, different answers per format:**

- **`.csv` refuses** a structural or `bytes` cell, because it cannot return one (it returns `'[1, 2]'` and
  `"b'x'"`).
- **`.parquet` accepts both**, byte-faithfully, and that acceptance is a **capability pinned by batch 1's
  arm E**, whose `.parquet` half has **no authorized editor.**
- **Cross-row type disagreement is a separate question** from cell structure, and correction 8 measured
  that unification for `.csv` is **not built** — so a row about it must be worded for the format it is
  true of.

**Tasks 7, 9 and 11 are the ones this reaches**, since they own the recorded-side guard, the encoder
coercion and the cross-format matrix. **Read this correction before their briefs' wording, not after.**

**And this is the fourth variant of one failure this project keeps recording.** A finding carried *into* a
brief still needs verifying; a ruling that *overrules* a brief must reach the brief; an instruction living
*only* in a dispatch can be outweighed by the brief; and now — **a ruling that post-dates a plan leaves
every later task's text carrying the superseded reading.** The remedy is the same in all four: **put the
correction where the brief is extracted from.**
