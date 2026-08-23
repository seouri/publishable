# H9a — the re-entry seam, `draft`, and `dry-run` — design

**Written 2026-08-23 against `main` at `af78816`**, clean tree. Every measurement below was made by
reading or running at that commit and says which; nothing is carried from
[`H9-SCOPING.md`](../H9-SCOPING.md) without re-checking, and where this design disagrees with that
scoping the disagreement is named in § Where this design disagrees with the scoping rather than
silently corrected. The scoping is dated 2026-08-23 and pinned to `822fe4b`, one commit behind; **a
scoping expires and a spec does not**, so the figures here replace its figures where they differ.

H9a is the first of H9's four parts. It builds **no new record**: `draft` writes the record `run`
already writes with two flags set, and `dry-run` writes nothing at all. What it does build is the
**seam** — one extraction of `command_run`'s phases 1–5 behind a value object — and that extraction
is the only part of this slice that touches a shipped code path. Everything else is two new command
names and the document edits they force.

---

## 0. What was measured, before any decision

| Fact | How |
|---|---|
| `command_run` spans `cli.py` lines **2009–3924** — **1916 lines**, one nested `def` (`_include`) | `ast` walk of the module, `fn.lineno`/`fn.end_lineno` |
| Phases 1–5 end at the `allocate_run_dir` call (phase 6, line 2430). The region holds **55 top-level statements**, **four early exits** (2018, 2034, 2114, 2390) and **six print sites** (2015, 2016, 2033, 2113, 2389, 2412) | `ast` walk, `Return`/`print` nodes under statements ending before 2430. The fifth `return` in the region (2361) is inside the nested `_include` and is not an exit |
| **35 values cross the seam** — assigned in phases 1–5 and read in phases 6–10 before being re-assigned there | `ast` walk: `Store` names before the split, first occurrence after it. 36 raw hits minus the comprehension variable `u`; `warn_c` and `r` are re-bound after the split before any read and do **not** cross |
| The run-start apparatus probe is at line **2565** — *after* `allocate_run_dir` and **inside** `with RunLock(run_dir)` | read |
| `apparatus.Observer.__init__` requires `run_dir: Path`, and `_observe_one` calls `append_observation` **unconditionally** before `Observations.record` and the gate | read, `apparatus.py` |
| `Observations.record` populates `_first_answered` from the facts it is given; `changed` compares the *next* facts against that. So for **one round per condition** the gate is provably a no-op — the value it would compare against is the value it was just given | read, `apparatus.py` `record`/`changed` |
| `PHASE_DRY_RUN` has **zero call sites** in `src/` — the three that exist pass `PHASE_RUN_START` (`cli.py`), `PHASE_PRE_EXECUTION` (`runner.py`), `PHASE_FREEZE` (`freeze.py`) | `grep -rn 'PHASE_' src/publishable/*.py` |
| `dry_run` is nonetheless **load-bearing in tests**: `tests/test_apparatus.py`'s H8b task-2 vocabulary test enumerates all four literals, and two fixtures (`tests/test_apparatus.py` ~1113, `tests/test_freeze.py` ~357) use a well-formed `dry_run` line as the phase `replay_ledger`'s filter must **exclude** | grep |
| `_dispatch` already carries a **shared** one-path-no-flags arm for `OPERATION_COMMANDS = {"validate", "run", "freeze", "report"}`, and `diff` has its own two-path arm | read |
| That shared arm's message is pinned by **nothing**: `grep -rn "takes exactly one path" tests/` → **0 hits**. Only `diff`'s own message is pinned, as `_DIFF_ARITY_MESSAGE` (`tests/test_cli.py`) | grep, twice, with `no flags` as the second spelling |
| `assemble_run_yaml` already takes `draft: bool = False` and writes `"draft": draft`; `provenance.git.code_dirty` is already written from `git.code_dirty` | read, `run_record.py`, `cli.py` line 3810 |
| All three `draft` **readers** ship: `report.py` refuses a single run (`E-REPORT-DRAFT`) and flags a bundle member, `diff.py` prints the word in its per-side header | read |
| The narrowing chain that decides `len(io.units)` is, in order: `_arm_keys` (group axis) → then either the holdout branch, the fold branch (`None` at `run`/`condition` scope, `_handed_keys` at `repeat`, whole roster at `summary`), or neither | read, `runner.execute_plan` |
| `E-RUN-LOCKED` appears in **none** of the four documents — `0` in each of `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md`, with `E-PARAM-MISSING` returning `1` in `reference.md` as a can-fail control | `grep -c`, four files named individually |
| **Eight** `spec-defects.md` entries name H9 as owner, not six | a section-by-section scan (`## ` split, `Owner…H9` newline-insensitively over each body) |

---

## 1. The four controller rulings

### Decision 1 (Ruling R) — `dry-run`'s promise narrows to what core can derive

**Question.** § Operation commands promises `dry-run` *"prints every artifact path that would be
written."* Can it?

**Answer. No, and the document changes first.** `dry-run` prints, per config: the resolved condition
list, the repeat plan, the step list with scopes, the execution count, the **unit-execution** count,
the **step directories** a run would create, and the **fixed files** a run would write — and it says,
in the output itself, that the artifact *files* inside those directories cannot be listed and why.

**Grounds, measured.** Every artifact file comes from an `io.write`/`io.record`/`io.append` call whose
name is a string in a step body. There is **no artifact declaration anywhere in the config schema** —
grepped § The one config file for any such block: none. `design-principles.md` § Greenfield only says
core never inspects the body of user Python, and `reference.md` § Validation says so again in its own
words. Two artifacts are conditional on *runtime* facts rather than declarations:
`artifacts.finalize` writes `units.parquet` only when a step recorded at least one row and
`measurements.parquet` only when one passed `measurement=` (read, `artifacts.py`). So the promise is
not merely expensive — it is unsatisfiable under a stated non-promise, which makes it **the document
being wrong rather than the feature being hard.**

**What replaces the `64`.** § Before you spend it's transcript ends `would write 64 artifacts under
/secure/results/cohort-pilot/run_.../`. `64` is derivable from nothing core knows. The replacement is
derivable and checkable: **one step directory per planned (step, condition, repeat) triple**, which is
exactly what `runner.step_dir_for` returns — and for the worked example that is **20**: `shared/step01_load_cohort`
(1) + `conditions/<c>/step02_fit_model` × 3 (3) + `conditions/<c>/<seed>/step03_analyze` × 3 × 5 (15)
+ `summary/step04_compare_methods` (1). The counting rule goes in the document beside the number, so
the next reader can re-derive it instead of carrying it.

**Alternatives rejected.** *Print the artifact names a template's steps are known to write* — there is
no such declaration and inventing one is a schema change H9a has no charter for and
`design-principles.md` argues against. *Print nothing about paths* — throws away the genuinely useful
half; `dry-run` exists to be read before a metered run, and where the run lands is the thing a reader
checks first. *Keep the sentence and let the count be approximate* — an approximate manifest is worse
than an honest partial one, because nothing marks it approximate at the point of reading.

**Cost if wrong.** A user expecting a full manifest gets a partial one. **That is why the narrowed
promise must say what it omits and why, in the output and in the document** — a quieter line that
simply printed less would reproduce the defect in the opposite direction, where the reader cannot see
that anything is missing.

### Decision 2 (Ruling S) — the extraction may not move arm-plan resolution

**Question.** `_resolved_group_axes` (line 2314) and `arm_members` (2331) sit **inside** the region
this slice extracts. May the extraction reorder or hoist them?

**Answer. No. They move as-is, in place, in their current order, and nothing about *when* they run
changes.** H3c-3's remaining 14 owns the phase hoist of exactly those two calls — its task 2, per
[`H3c-3-SCOPING.md`](../H3c-3-SCOPING.md) § 6 — because folds and holdouts *inside cells* need the
axes realized before the cell decomposition. **H9a moves phases; H3c-3 moves the arm-plan
resolution. They touch the same function and they are different moves.**

**Grounds.** H3c-3's remaining 14 is the only slice scheduled after H9 (spine § Order, amended
against outside evidence). Doing its task 2 here would take work from it *and* do it without its
design — the design that knows what a cell needs. The precedent is H4b-2, which declined to fold the
`report_by`-under-`resample` gap in and said so in writing rather than taking it because it was
nearby. Measured: `_resolved_group_axes` is called once, at 2314, and its result feeds `arm_members`
(2331), `holdout_plan` (2319) and the allocation document — four consumers, three of which are in
phases 6–10, so a hoist is a real reordering and not a cosmetic one.

**Cost if wrong.** The only slice left after H9 loses a task to a slice that never argued it, and the
hoist lands without the cell decomposition that motivates it — which is how a partial refactor
becomes the thing the next design has to undo first. **Named in every task section that touches
`command_run`**, not only here, because `task-brief` extracts one section and nothing else.

### Decision 3 (Ruling T) — `draft` relaxes the gate; the pathspec never moves

**Question.** `draft` permits a dirty code tree. Does anything about **what the gate covers** change?

**Answer. No. The pathspec stays `src/**` and `templates/**`, byte for byte.** `draft` changes one
boolean at one call site: whether a `True` from `git.code_dirty` refuses the run. `git_provenance`'s
`git status --porcelain -- src templates` is not touched, its `-c` neutralization flags are not
touched, and `HASHED_TREES` is not touched.

**Grounds.** H6b Decision 12 **declined** widening `E-CODE-DIRTY`'s pathspec to the repository root
and left it unassigned. The scoping's § 12 warns that the relaxation and the widening are *one line
apart* — measured true: both live at `cli.py` 2027–2033, the `if git.code_dirty:` test and the
`git_provenance` call one line above it. **Relaxing a gate for a mode and widening the gate's scope
are different edits.** A slice that did both would make a declined decision by accident.

**Cost if wrong.** The declined decision gets made in a slice that never argued it, and the argument
is then unavailable to the reader who meets the wider gate — exactly the shape H6a's Ruling L had to
un-pick. The guard against it is mechanical and is stated as a task constraint: the `draft` task may
not touch `provenance.py`, and its diff must show `git_provenance` unchanged.

### Decision 4 (Ruling U) — the guard pin comes first, in the shape already decided

**Question.** How is a behaviour-preserving extraction of a shipped code path proven behaviour-
preserving?

**Answer. A pin captured in batch 1, before any code moves, with every arm's authorized editor and
post-edit state written down now** — and with **arms that have no authorized editor at all**.

**Grounds.** H6a captured arms against a **superseded signature** and forced task 3 into an
unauthorized edit; H6b captured **forward**, wrote the post-edit state in advance, and its edit
matched byte for byte. The difference was one batch of foresight. H9a's exposure is sharper than
either: it **moves 420 lines of a shipped command without intending any change**, so the pin is the
only thing standing between the extraction and a silent behaviour change. And H6b's whole-branch gate
established the corollary this slice must not repeat: **proving an arm cannot move is not proof the
line is pinned** — an arm offered as evidence that an edit is safe *because it cannot see the edit* is
two opposite facts wearing one sentence.

**Cost if wrong.** An extraction that changes a value nothing asserts, in a record every downstream
command reads. There is no reader who could see it from a record. **An implementer may not
self-authorize an arm edit — the route is a controller ruling, and leaving the branch red is
correct.**

---

## 2. The seam

### Decision 5 — one frozen value object, `Prepared`, and a `Prepared | int` return

**Question.** What shape does the extraction take?

**Answer.** `cli._prepare_run(config_path, *, allow_dirty: bool) -> Prepared | int`, where `Prepared`
is a frozen dataclass holding the **35 values** measured to cross the seam, plus the live `Collector`.
The four early exits become the `int` arm, returning the same `EXIT_WRONG` they return today. The six
print sites move with the code and print the same bytes to the same streams.

**Grounds, measured rather than estimated.** The crossing set is 35 names, listed in the plan's task
2 section verbatim from the `ast` measurement, and that count **is the argument for the seam rather
than against it**: nothing in phases 6–10 can be re-entered without those 35 values, so a second
entry either receives them or recomputes them, and recomputing is what `resume` must *not* do. One of
the 35 is `c`, the run's `Collector` — a channel, not a value — and it is named separately in the
dataclass docstring so a reader does not mistake it for state.

**Alternatives rejected.** *A private exception carrying the exit code* — hides the four exit paths
from `mypy` and from a reader following control flow; the repo runs `mypy` and the union is checked.
*A tuple* — 35 positional fields is the fixture-with-numbers-that-agree-with-the-bug trap in a
different currency. *A mutable dataclass* — phases 6–10 would be free to write back into the object
that phases 1–5 pinned, which is the one thing the seam exists to prevent for `resume`.
*Sub-objects grouped by phase* — invents a decomposition no document holds; the ten-phase numbering
is an implementation fact in comments (grepped: `phase` over the four documents named individually
returns no sequence), and inventing a second one is a maintenance obligation nobody owns.

**Cost if wrong.** A 35-field object is unpleasant to read and will be split later. That is a
readability cost paid once, against the alternative of `resume` and `dry-run` each recomputing what
`run` pinned — which is two more sources of truth for one identity claim, the fault H6a spent a batch
establishing.

### Decision 6 — "phases 1–5 plus the probe" is not a contiguous prefix, and the probe is built from the shipped pieces rather than from `Observer`

**Question.** The scoping's re-entry table gives `dry-run` *"phases 1–5, and the probe; never 6."*
Can `dry-run` get the probe by running phases 1–5?

**Answer. No — and this changes how the seam is framed.** Measured: the run-start probe round is at
line **2565**, *after* `allocate_run_dir` (2430) and *inside* `with RunLock(run_dir)`. It is in phase
6/7, not in phases 1–5. So `dry-run` is **phases 1–5, plus a probe round of its own**, and the round
is built from the shipped pure pieces: `apparatus.observe_once` → `apparatus.check_facts` →
`Observations.record` → `Observations.warn_unanswered`. It never constructs an `Observer`, never calls
`append_observation`, and never calls `check_changed`.

**Grounds.** `Observer.__init__` **requires** `run_dir: Path` and `_observe_one` appends to the ledger
unconditionally, before recording and before the gate — deliberately, and its docstring gives the
reason (*"the moving observation is on disk before anything can stop the run"*). `dry-run` creates no
run directory, so there is no ledger. Defaulting `run_dir=None` and skipping the append inside
`_observe_one` was considered and **rejected**: it is a fail-open shape on a shipped class whose whole
guarantee is that the append happens first, and a future caller that forgets the argument loses the
ledger silently. Calling the pieces directly changes `apparatus.py` not at all.

**`check_changed` is omitted on a measured ground, not on "there is no baseline."** `Observations.record`
populates `_first_answered` from the facts handed to it, and `changed` compares the *next* facts
against that entry. With one round per condition, the value the gate would compare against **is the
value it was just given**, so `changed` can only return `None`. The omission is provable from the two
functions rather than argued from the absence of a run.

**`warn_unanswered` is kept.** `W-APPARATUS-UNANSWERED` before a metered run is precisely the news
§ Before you spend it exists to deliver, and it costs one in-memory `Observations`.

**Cost if wrong.** If a future `dry-run` were expected to write a ledger line, this decision has to be
revisited together with Decision 7 — the two are one question and are answered together.

### Decision 7 — `PHASE_DRY_RUN` keeps its constant, gains no call site, and the **document** changes

**Question.** § The apparatus files says the ledger is written *"at `dry-run`, at run start, before
each execution, and at `freeze`."* § Operation commands says `dry-run` *"Creates nothing."* Both
cannot hold. Which moves?

**Answer.** The **document** moves. `dry-run` appends no ledger line; `PHASE_DRY_RUN` stays in
`apparatus.PHASES`; § The apparatus files stops listing `dry-run` among the phases the ledger is
written at and states, in one sentence, that `dry_run` is a reserved phase name no build appends
**because the ledger lives inside a run directory `dry-run` never creates**. `replay_ledger`'s
two-phase filter **does not widen** — and that answer is the one H9b inherits, since `resume`'s
baseline reader is the filter's second caller.

**Grounds, and why deletion was rejected.** Deleting the constant looked cleaner (*prefer deleting a
claim to rewriting it*), and measurement reversed it. `dry_run` is load-bearing in the **tests**:
`tests/test_apparatus.py`'s H8b task-2 vocabulary test enumerates all four literals — the test
`CLAUDE.md` cites as the repaired form of *a test that iterates the thing under test* — and two
fixtures (`tests/test_apparatus.py` ~1113, `tests/test_freeze.py` ~357) use a well-formed `dry_run`
line as the phase `replay_ledger` must **exclude**. Deleting it would leave `freeze` as the only
excluded phase, **collapsing two distinct exclusion reasons into one** and weakening both fixtures:
`freeze` lines are excluded because they are not the run's own baseline; a `dry_run` line is excluded
because it is not an observation of this run at all. The document, not the vocabulary, is what is
false.

**The closed filing.** `spec-defects.md` § *no build appends a `PHASE_DRY_RUN` ledger line…* is closed
by this decision either way, and it is closed by **striking**, with the resolution named — the entry
is a live list and a closed gap left standing keeps recruiting readers (H6b's own Minor).

**Cost if wrong.** A reader looking for a `dry_run` line in a real ledger finds none and the
vocabulary says one is possible. That is why the reserved status is stated in the document rather than
left as an absence.

### Decision 8 — `dry-run` does not enforce the dirty gate, and that is not Ruling T's widening

**Question.** Does `dry-run` require a clean `src/**` and `templates/**`?

**Answer. No.** `dry-run` calls `_prepare_run(..., allow_dirty=True)`.

**Grounds.** The gate exists to protect a **record**: § Three hashes' whole argument is that a
`code_hash` is only a claim if the tree it covers is reachable from a commit. `dry-run` writes no
record and makes no claim, so there is nothing for the gate to protect. And the command's own purpose
argues the same way — `dry-run` is what you run *while iterating*, before you commit; a gate there
would make the cheap check the one you cannot run.

**This is a use of the same parameter Ruling T introduces, not a second widening.** `allow_dirty`
changes whether a computed `True` refuses; the pathspec and the neutralization flags are identical for
all three callers. Stated here because *relaxing for two modes* and *widening once* are one line
apart in exactly the way Ruling T names.

**Cost if wrong.** A user dry-runs a dirty tree, gets numbers, commits something else, and the numbers
were about the earlier tree. Mitigated the way `draft` is: `dry-run` prints no `code_hash` and no
identity claim at all, so there is no figure to mistake for one.

### Decision 9 — `draft` on a **clean** tree records `code_dirty: false`, and § Draft runs' conjunction is corrected

**Question.** § Draft runs: *"Draft runs are recorded with `draft: true` and `git.code_dirty: true`."*
Is that true of the code?

**Answer.** Half of it. `draft: true` is unconditional — `assemble_run_yaml(draft=True)`.
`git.code_dirty` is computed by `git_provenance` **from the actual tree**, so a `draft` of a clean tree
records `code_dirty: false`. The document's conjunction is corrected to say what the code does and
why: `draft` **permits** a dirty tree and records honestly what it found; `draft: true` is the flag
every reader keys on, and `code_dirty` remains a measurement rather than a mode marker.

**Grounds.** Measured at `cli.py` 3810 (`"code_dirty": git.code_dirty`) and `provenance.py` 209. The
alternative — forcing `code_dirty: true` under `draft` — would make a `provenance` figure lie about
the tree, which is the one thing `provenance` is for, and would break `diff`'s `git` comparison
between a clean draft and the `run` of the same commit. **All three `draft` readers key on `draft`,
not on `code_dirty`** (read: `report.py` twice, `diff.py` once), so nothing downstream needs the
forcing.

**Cost if wrong.** A reader who greps `code_dirty: true` to find drafts misses the clean ones. The
correction says which key is the flag, in the document, beside the sentence that used to imply both.

### Decision 10 — `draft` prints a notice to stderr when it relaxed the gate

**Question.** Does `draft` say that it permitted something `run` refuses?

**Answer.** One line to **stderr** when `git.code_dirty` is `True`, naming the recorded flags. Exit
code unchanged; a notice never changes a code.

**Grounds.** H8c's precedent — bundle notices to stderr — and § Draft runs' own argument that the
command name is what makes the mode legible. Silence would make a draft of a dirty tree
indistinguishable at the terminal from a `run`, and the one thing § Draft runs promises is *"you just
can't accidentally cite one."* stderr, because it is a notice about the invocation rather than part of
the record's own report, and because `run`'s stdout is pinned and this must not enter it.

**Cost if wrong.** One more line on a stream some harness captures into a log. Cheap, and reversible
without moving a record key.

### Decision 11 — `unit-executions` reuses `_arm_keys` and `_handed_keys`, and is held to an **agreement pin** rather than to a second extraction

**Question.** `dry-run`'s `unit-executions` is the sum of `len(io.units)` over planned executions.
`execute_plan` computes that narrowing inline. Extract it?

**Answer. No.** `dry-run` calls the two already-extracted helpers — `runner._arm_keys` and
`runner._handed_keys` — and restates the four-way `execution.scope` dispatch around them. What
prevents drift is not a shared function but a pin: **one fold fixture and one group-axis fixture in
which `dry-run`'s printed `unit-executions` must equal the summed `len(io.units)` a real `run` of the
same config actually hands out.**

**Grounds.** Extracting `units_for_execution` out of `execute_plan` would be a **second**
behaviour-preserving extraction on a shipped path, in **phase 7** — outside the phases this slice is
chartered to move — and it would need its own pin arm and its own line in the disclosure. `_arm_keys`
and `_handed_keys` are already single-call-site extracted functions, which is precisely the seam H6a
chose for `E-CODE-FILE-LIST` and for the same reason. The agreement pin catches divergence *and* costs
no phase-7 change; a shared helper catches divergence only while both callers keep calling it, which a
monkeypatch or a re-routed call site can defeat silently (`CLAUDE.md` § Mechanical traps).

**The narrowing, as measured, so the restatement is checkable.** In order: `_arm_keys` narrows when a
group axis is declared and the execution has a condition; then — under a declared **fold** —
`run`/`condition` scope receives `None`, `repeat` scope receives `_handed_keys`' partition, and
`summary` receives the whole (arm-narrowed) roster; under a declared **holdout**, every scope receives
the test partition; otherwise every scope receives the arm-narrowed roster. **An execution handed
`None` contributes zero**, and the printed line says so, because a fold's `run`- and
condition-scoped steps see no units at all and a reader computing by hand would otherwise be short.

**Cost if wrong.** The number a metered run is billed by is wrong, in a command whose entire purpose
is that number. Which is why the pin is an equality against a real `run`, on two configs chosen so
the two candidate readings differ, rather than against a hand-computed literal.

### Decision 12 — "Creates nothing" is scoped to `output_dir`, and `__pycache__` is the named residue

**Question.** How is *Creates nothing* pinned?

**Answer.** The filesystem under `output_dir` is byte-identical across the whole command and no
`run_*` directory appears; and `dry-run` against a run directory holding a **live lock** completes
normally and takes no lock.

**Grounds, and a premise that had to be corrected.** A repo-wide byte-identity assertion **fails**:
`dry-run` imports the entrypoint and runs `discover_local`, which writes `src/**/__pycache__/` and
`templates/__pycache__/`. That is measured, not predicted — H6b batch 4 reproduced it for `validate`
live, and § Templates' *"goes dirty at `validate`"* is the shipped sentence about it. An arm asserting
repo-wide identity would fail and the implementer would "fix" it by weakening the assertion, which is
the worst of the three outcomes. So the arm is scoped to `output_dir`, `__pycache__` is named as the
excluded residue with that citation, and the design says why that scoping **is** what "Creates
nothing" means: the promise is about the artifacts of a run, and a bytecode cache is not one.

The live-lock arm exists because § One execution at a time says pointing a read command at a live run
is *"as ordinary as reading the ledger"* — `freeze` is the shipped instance, and `dry-run` takes no
lock at all, so it is a stronger case.

**Cost if wrong.** A `dry-run` that creates a directory the user then has to clean up, or that blocks
on a lock it has no business taking. Both pinned.

### Decision 13 — the two commands join the **existing** shared arity arm, and that arm gains its first pin

**Question.** How are the two names dispatched, and what protects the invocation rule?

**Answer.** Both are added to `OPERATION_COMMANDS` and to the `handlers` mapping, and removed from
`NOT_BUILT_COMMANDS`. No second arity enforcer is written.

**Grounds.** The shared arm already reads `if len(rest) != 1 or rest[0].startswith("-")` and prints
`` `<command>` takes exactly one path and no flags`` — the arm `freeze` and `report` joined, with its
own comment arguing against two enforcers of one rule. `diff`'s separate arm is a different **arity**,
not a second enforcer of the same one.

**And the arm is pinned by nothing today.** `grep -rn "takes exactly one path" tests/` returns zero
hits; `grep -rn "no flags" tests/` returns one, `_DIFF_ARITY_MESSAGE`, which is `diff`'s. So H9a
widens an **unpinned** guard from four commands to six. Its mutation is named in § Mutations and it is
not blind: replacing the condition with a bare `len(rest) != 1` must fail a test.

**One shipped test constrains this before a line is written.**
`tests/test_cli.py::test_reference_cli_tables_match_what_the_cli_does` drives every unmarked row with
two junk arguments — `main(["dry-run", "_probe_a", "_probe_b"])` — and asserts the output contains
neither `unknown command` nor `is specified but not built`, and that nothing is scaffolded or executed.
**It asserts only absences**, which is H8b's Minor exactly, so it is a constraint and not a pin.

**Cost if wrong.** A flag reaches a parser, and `design-principles.md` § Everything is in the file is
breached by the two commands whose whole existence is the argument for modes-as-names.

### Decision 14 — the probe's **credential wrapper** travels with the calls

**Question.** `dry-run` runs user code — the probe. What contains a credential it read?

**Answer.** The dispatch wrapper at `cli.py` ~2522–2548 is copied **with its `try`**: `except
BaseException`, `KeyboardInterrupt` re-raised fresh and argument-less, a **fresh
credential-bearing `Collector`**, rendered to stderr. And the same containment covers `observe_once`,
which is where the probe body actually runs.

**Grounds.** This is verbatim the fault `CLAUDE.md` § Answering a question with a proxy names as
*copying a recipe's calls without its containment*: `freeze`'s credential wiring was cited as
precedent for `report`'s, the calls were lifted, **the `try` was not**, and a declared credential
reached stderr in a case § Secrets explicitly promises to redact. A recipe is its calls **plus where
they sit**. The positive control is named in § Fixtures: a project-local probe that raises with a
declared credential in its message, `dry-run` printing `<redacted:…>`.

**One ordering the extraction must not disturb.** `credentials` is computed at 2065, **before** the
roster resolution, and the comment at 2052–2058 says why: a resolver's body is the first thing in the
command that can raise carrying a credential, so the value set must exist before that call is reached.
The extraction preserves statement order throughout, and this pair is the one where reordering would
be silently wrong rather than loudly wrong.

**Cost if wrong.** A credential on stderr from the command this project tells users to run before they
spend money — the highest-traffic new surface in the slice.

### Decision 15 — no exit code is minted, and the cost ordering is the behaviour

**Question.** Does H9a mint an exit code?

**Answer. No.** `draft` becomes the second reader of `3` and `4` (their rows already name it).
`dry-run` exits `1` on a config that does not validate and `5` when the probe is unreachable, with the
**cost ordering** as the behaviour: validate → manifest → probe, stopping at the first failure, so a
config with an error never reaches a metered call. § Exit codes' own paragraph already states this and
had no reader.

**Grounds.** Measured § 9 of the scoping and re-checked: `3` and `4` have exactly one reader each
(`command_run`'s final mapping), and `draft` reaches it by construction because `command_draft`
delegates. `EXIT_EXTERNAL` already has readers; `dry-run` adds one more. Three of the last five slices
minted codes, so a slice that mints none is worth saying out loud.

**Cost if wrong.** A script cannot distinguish a `dry-run` that failed cheaply from one that failed
expensively. It can: `1` and `5` are exactly that distinction, and the ordering is what makes them
mean it.

### Decision 16 — the `resolve_contrasts` precondition is discharged for `dry-run` **by construction**, and the entry is amended rather than struck

**Question.** `spec-defects.md`'s S4c-task-9 entry names H9 as owner of a precondition: a caller that
reaches `contrasts.resolve_contrasts` without `validate_config` in front of it would crash on an
unhashable side. Does `dry-run` create one?

**Answer. No.** Measured: `resolve_contrasts` is called from `cli.py` only through
`_baseline_comparisons` (1753) and `_declared_comparisons` (1837), both in the aggregate phase —
**phase 8**, which `dry-run` never reaches — and `dry-run`'s phase 1 **is** `validate_config`. So the
cheaper of the entry's two answers is taken, and no guard is added to `contrasts.py`.

**The entry is amended, not struck.** `resume` (H9b) and `reproduce` (H9c) are also second entries and
the precondition still binds them. Striking it because H9a discharged its own half would leave two
live obligations unowned — the *"whichever slice next touches X"* failure this file rejects by name.

**Cost if wrong.** If a later H9a task were to print the correction family from a `dry-run`, that
would be a caller reaching `resolve_contrasts` outside phases 1–5, and the entry's other answer would
be owed. Named as a constraint in the task section: `dry-run` prints no comparison list beyond what
`sweep.yaml`'s own resolved conditions carry.

### Decision 17 — `E-RUN-LOCKED` is **H9b's**, and this slice says so rather than taking it

**Question.** `E-RUN-LOCKED` appears in none of the four documents (measured: `0` in each, with a
can-fail control). Does H9a give it a § Errors row?

**Answer. No.** It is `resume`'s documented refusal — § Resuming refuses *"one whose lock is held"* —
and it is **unreachable from `run`, `draft` and `dry-run` for a structural reason**: `allocate_run_dir`'s
`mkdir` *is* the claim, so a lock file cannot pre-exist a directory those commands just created, and
`dry-run` never takes a lock at all. H9b owns the row, its two sites (the raise in
`run_identity.RunLock.__enter__` and the report in `cli.main`'s `except PublishableError`), and the
five-codes filing's amendment.

**Grounds.** The scoping's own correction C3 enumerates the two sites by reading rather than by
counting a grep, and § Errors carries one row per code covering **every** site that raises *or*
reports it — the `E-TEMPLATE-UNKNOWN` precedent. Taking the row here would mean documenting a code
this slice cannot reach, from a slice with no `resume` to test it against.

**Cost if wrong.** A shipped code stays undocumented for one more slice. Stated in the design so it
is not rediscovered as a defect, and so H9b's task 9 finds it already argued.

---

## 3. Where this design disagrees with the scoping

Reported individually and attributed, per `CLAUDE.md`'s note that six consecutive slices reported zero
disagreements and all six were wrong. Each was found by measuring, and each measurement is named.

1. **`command_run` is 1916 lines (2009–3924), not 1918 (2009–3926).** `ast`, `end_lineno`.
2. **"Phases 1–5, and the probe" is not a contiguous prefix.** The probe is at 2565, after phase 6's
   `allocate_run_dir` and inside `with RunLock`. Decision 6.
3. **Scoping task 1's arms are largely already pinned.** The run-directory root list and
   `environment/`'s contents are H8b arms A and B; `run.yaml`'s and `provenance`'s key lists are H8a
   arms A and B, restated by H8b arm C; the record's field-level shape is H8c task 17 arm A;
   `sweep.yaml`'s key list is pinned in `tests/test_cli.py`. Re-capturing them would recreate H8a's
   *same list pinned twice*. § The guard pin cites them as already-pinned with **editor NONE**.
4. **`("dry-run", "NOT BUILT")` is an assertion in a shipped test, not an arm to capture** — and its
   sibling `{n for n, s in … } == set(NOT_BUILT_COMMANDS)` is **self-maintaining** and needs no editor.
5. **Eight `spec-defects.md` entries name H9, not six.** The two the scoping's § 8 table misses are
   the S4c-task-9 `resolve_contrasts` precondition (H9a's, since H9a owns `dry-run`) and
   `UpstreamLedger.record`'s missing-hash entry (H9c's, `reproduce` walking a chain of ancestors).
6. **§ The apparatus files is not the only home of the dry-run-ledger claim.**
   `docs/experimental-designs.md` § Mistakes core prevents says a probe's facts *"are recorded per
   condition at `dry-run`"* — *recorded* is the ledger. A second home the scoping's § 5.1 does not
   name, and the sweep is part of Decision 7's edit.
7. **`docs/feasibility-llm-growth-studies.md` carries a third home of the artifact-path promise** —
   *"`dry-run` prints … where every artifact will land"* — plus two build claims this slice falsifies:
   *"`draft` … does not dispatch in this build"* and *"`dry-run` prints specified but not built."*
8. **The `executions.jsonl` key set is asserted nowhere.** It is a claim in two `tests/test_cli.py`
   docstrings and no assertion — the H6b Major-2 shape exactly, and therefore new coverage.
9. **The shared `OPERATION_COMMANDS` arity arm is pinned by nothing** (zero hits for `takes exactly
   one path`; the one `no flags` hit is `diff`'s). H9a widens an unpinned guard.
10. **§ Draft runs' conjunction cannot be honoured.** Decision 9.
11. **`warn_c` looks like a crossing value and is not** — it is re-bound at 3906 before its second
    read. The true crossing count is 35 after removing it, `r`, and the comprehension variable `u`.
12. **Phases 1–5 hold four early exits, not five.** The fifth `return` in the region is inside the
    nested `_include` def.
13. **Two shipped comments already assert `draft`'s behaviour**: `hashes.py`'s `code_hash` docstring
    (*"`run` and `draft` compute the…"*) and `runner.py`'s *"`draft` and `resume` when they land
    (H9)"*. Both must be re-read when `draft` lands — a sentence going false under its own slice's
    change is this family's most frequent single defect.

---

## 4. What this slice refuses to build

The scoping's § What H9 must not fold in is the starting list; every row was re-checked at `af78816`.

| Not H9a's | Where it goes | Verified |
|---|---|---|
| The arm-plan hoist of `_resolved_group_axes`/`arm_members`, folds and holdouts inside cells | **H3c-3's remaining 14**, task 2 onward | Both calls measured inside the extracted region, at 2314 and 2331. Decision 2 |
| `E-DATA-HOLDOUT-CELLS` / `E-REPL-FOLD-CELLS` retirement | **H3c-3** | Unchanged; spine § Order |
| `resume`, its durability rulings, `allocation.json`'s reader, `run_status`'s `planned` contract | **H9b** | This slice adds no reader of a run directory |
| `E-RUN-LOCKED`, `E-RUN-ID-EXHAUSTED` § Errors rows | **H9b** | Decision 17; measured `0` hits in each of the four documents |
| `reproduce`, the lockfile questions, `apparatus.expected.json` | **H9c** | `W-ENV-UNLOCKED` still fires; nothing here reads it back |
| `demo`, `docs`, `list-templates`, the managed regions | **H9d** | `scaffold.README` still has two regions; no parser exists |
| `E-INPUT-CHANGED`, `E-PROJECT-EXISTS`, `E-EXPERIMENT-EXISTS` rows | **Unassigned, with the reason** — the manifest path and `generators/`/`scaffold.py` are not H9a's surface | Unchanged |
| `BaseTemplate.field_convention`'s missing reader | **Unassigned.** H9a creates no new one | Re-grepped: three hits in `src/`, none a reader |
| `report_by` under `resample` keeping a `t_over_units` interval | **Unassigned**, filed against H4 | `dry-run` computes no interval |
| `max_failed_fraction`'s truncation status semantics | **Unassigned**, filed by H7d Part B with a justification in a shipped test's docstring. `draft` runs the same loop and **must not weaken that pin** | Named as a task constraint |
| `validate_config`'s bare `except ContractError` around `find_repo_root` | **Unassigned.** H9a gives `docs`/`list-templates` no path, so the re-check that entry awaits is still H9d's | Unchanged |
| `limits.min_units_per_cell` having no reader | **Unassigned**, and outside H3c-3 too | Unchanged |
| A `W-PARAM-UNSET` equivalent for core-schema omissions | **Unassigned**, H6a Decision 10 | Unchanged |
| A marker for the hash definition in `run.yaml`; a fourth hash; a `provenance` key naming core's version; a `gpu` key | **Refused by ruling** (H6a Ruling C, H6a Decision 12 / Ruling E, H6b Decision 5) | H9a mints no `provenance` key at all |
| Widening `E-CODE-DIRTY`'s pathspec to the repository root | **Declined and unassigned** (H6b Decision 12). Decision 3 is the guard | Both edits measured one line apart, 2027 and 2028 |
| Extracting the per-execution roster narrowing out of `execute_plan` | **Not built here** — Decision 11. It is a phase-7 change; if a later slice wants it, the agreement pin is what tells it the two readings still match | — |
| A second phase decomposition entering `reference.md` | **Not built.** The ten-phase numbering stays an implementation fact in comments; grepped `phase` over the four documents named individually and found no sequence to extend | — |

---

## 5. Is this additive? — the disclosure

**No, and the honest form is an enumeration rather than a phrase** (H5b's and H6a's precedent).
Four things move, and the last is the one a reader would under-read.

**1. Two shipped invocations change their exit code and their output.** `publishable dry-run <path>`
and `publishable draft <path>` exit **2** today with `` `publishable dry-run` is specified but not
built in this version — see docs/reference.md § Operation commands`` on **stderr**. After H9a they
dispatch. This is the intended change and the `Status` column licenses it — the column exists so that
*"a marker that outlives its slice fails a test rather than misleading a reader"* — but it is a
behaviour change to a shipped invocation and is enumerated as one, not framed as additive.

**2. `NOT_BUILT_COMMANDS` loses two keys and `OPERATION_COMMANDS` gains two.** Consequence measured,
not assumed: the shared arity arm now answers for six commands instead of four, so
`publishable draft a b` prints `` `draft` takes exactly one path and no flags`` where it printed the
unbuilt diagnostic. And the two-token arm (`f"{command} {rest[0]}"`) no longer matches these names,
which is why the **order** of `_dispatch`'s branches is load-bearing and unchanged.

**3. One more shipped answer moves, and it is the item a reviewer would find by diffing behaviour
rather than reading this list.** `NOT_BUILT_COMMANDS` shrinking changes what the **two-token** arm
answers for: `publishable draft new` reaches `_report_not_built("draft", "Draft runs")` today, via the
single-name lookup after the two-token key misses, and afterwards reaches the shared arity arm and
prints `` `draft` takes exactly one path and no flags``. Same exit code, different line. The branch
order that makes this the only such case is unchanged and load-bearing.

**4. The extraction is claimed to move nothing, and the claim is measured rather than asserted.** The
target: for one real config run on a `main` worktree and on the branch, `run.yaml` is equal **leaf by
leaf**, the run-directory tree is equal **path by path**, stdout is equal **line by line**, and the
exit code is equal, with a normalization list written **in advance** — timestamps (`at`, `started_at`,
`wall_seconds`), `run_id` and everything derived from it (the directory name, `latest`), absolute
paths, and `hostname`. **Every remaining difference must be attributed individually**; an unattributed
difference is a finding, not noise. Green tests are not the evidence — H6b's whole-branch gate is the
precedent, where the additive claim was true and was *measured leaf by leaf rather than assumed*,
which is the only reason that slice shipped without a value-change disclosure.

**What does not move, stated so the negative is on the record.** No `run.yaml` key is added, removed
or reordered; `draft` sets a key that already exists with a default. No `provenance` sub-key changes.
No hash definition changes. No `E-` or `W-` code is minted or retired. `schema_version` is not bumped.
`git_provenance` is byte-unchanged.

---

## 6. Does § Executability move?

**No, and it is derived rather than repeated.** The four-row table in
[`docs/feasibility-llm-growth-studies.md`](../../feasibility-llm-growth-studies.md) § Executability on
this build is repeated **character for character** from the H8a entry, as the five entries since have
done, and **no fifth number is minted.**

The derivation, row by row:

- **Row 1, transplantable configs validating with zero errors — 8 of 8.** `dry-run` and `draft`
  neither run at `validate` nor are called from a step, and the extraction is behaviour-preserving,
  so `validate`'s answer for these configs is byte-identical.
- **Row 2, blocked on `io.reuse_from` — 0.** Untouched; H8a settled it and nothing here reads an
  upstream.
- **Row 3, meet the `report_by`-under-`resample` gap — 7.** A construction chosen inside
  `summarize_step`, in phase 8. `dry-run` never reaches phase 8 and `draft` reaches it identically to
  `run`.
- **Row 4, free of every core-side dependency this analysis can name — 1.** `draft` requires a dirty
  tree, which is a property of the operator's working tree and not of a config; `dry-run`'s probe
  round is unexercised because all nine configs validate against `generic`, whose `apparatus_probe`
  resolves to `None`.

**H9a therefore unblocks ZERO configs**, and the reason is structural rather than incidental: both
commands are *second entries into a sequence these configs already reach or do not*.

**Three live claims in that analysis do go false and must be corrected in the same task**, appended
rather than retro-edited: *"`draft` … does not dispatch in this build"*, *"`dry-run` prints specified
but not built"*, and *"`dry-run` prints … where every artifact will land"* — the last being Ruling R's
third home.

---

## 7. The guard pin

Captured in **batch 1, before any code moves** (Decision 4). Every arm names a sole authorized editor
or an explicit **NONE**, and every authorized post-edit state is written **now**.

| Arm | What it holds | Authorized editor |
|---|---|---|
| **A** | A completed `run`'s whole `run.yaml`, leaf by leaf, over a sweep-bearing project with a real `aggregate` metric — the normalized golden of § 5's target, as a **test** rather than as a probe | **NONE** |
| **B** | `run`'s full **stdout**, line by line, for a completed run | **NONE** |
| **C** | The exit code for each of the four outcomes `command_run` can produce — `completed` → 0, `partial` → 3, `failed` → 4, apparatus-unreachable → 5 — each asserted beside the `status` it wrote, separately, on H7d Part B's precedent | **NONE** |
| **D** | The `executions.jsonl` line's **key set**, exactly `{step, scope, condition, repeat, status, started_at, wall_seconds, error}` — new coverage; the claim exists today in two docstrings and no assertion | **NONE** |
| **E** | The four early-exit codes of phases 1–5, each reached end-to-end through `main([...])`: a config that fails validation, a dirty tree, a roster refusal, and the zero-file `E-CODE-EMPTY` | **NONE** |
| **F** | `tests/test_cli.py::test_reference_cli_tables_are_parsed_at_all` — the **shipped** assertion `("dry-run", "NOT BUILT")`. **Cited, not captured.** | **Task 9 only** — the task that dispatches `dry-run` and edits its § CLI reference row in the same commit, because the row and the assertion are one fact seen from two ends. Post-edit state, written now: that one line becomes `("dry-run", "built")` **and** a line `assert ("resume", "NOT BUILT") in tables["Command"]` is added so the table keeps a marked row-presence probe. `("validate", "built")` is untouched. The `set(NOT_BUILT_COMMANDS)` equalities are **self-maintaining and must not be edited** |
| **G** | Already pinned elsewhere and **not re-captured**: H8b arm A (the run directory's root list), H8b arm B (`environment/`'s contents), H8a arms A and B (`run.yaml`'s and `provenance`'s key lists), H8b arm C (the same restated), H8c task 17 arm A (the record's field-level shape), and `sweep.yaml`'s key list | **NONE.** Cited in the design so a reviewer does not read the absence as missing coverage |

**Every arm must be proven able to fail** before the batch is reviewed, by a mutation in the
production code — not by reading. Arm D's proof is the one to watch: it is new, and a docstring
claiming a key set is what it replaces.

---

## 8. Fixtures as claims

Every literal is computed, and the method is named. A fixture whose numbers agree with the bug is this
repo's most frequent single defect.

| Fixture | The claim | How every literal is obtained |
|---|---|---|
| **P** — the extraction's golden | A real `run` on `main` and on the branch produce equal records | **Not a literal at all**: the two sides are produced by running, and the comparison is between them. No transcription from `cli.py` |
| **Q** — `draft` on a **dirty** tree | `draft: true`, `git.code_dirty: true`, exit 0, `report` refuses, `diff` labels | Built by writing into `src/**` **after** the first commit, outside the repo. `code_dirty` read back from the record, never asserted from the config |
| **R** — `draft` on a **clean** tree | `draft: true`, `git.code_dirty: **false**` | Decision 9's claim. The premise (a clean tree) is verified by `git status --porcelain -- src templates` inside the fixture, so it cannot pass on a tree that happens to be dirty |
| **S** — `dry-run`'s `unit-executions` under a **fold** | The printed number equals the summed `len(io.units)` a real `run` hands out; `run`- and condition-scoped executions contribute **zero** | The expected value is **summed from the real run**, recorded per execution by a step that records `len(io.units)`. Never computed as `roster / k × executions`, which is the arithmetic the code could be wrong about in the same way |
| **T** — the same under a **group axis** | Same equality, arm-narrowed | Same method. **S and T must give different answers** — a fold fixture and a group fixture whose counts coincide would test one reading twice, which is the two-elements-distinguish-two-answers trap |
| **U** — `dry-run`'s step-directory list | The printed directories are exactly those a real `run` creates | Compared **set to set** against the real run's tree, not against a count. The worked example's **20** is derived in the document from the triple rule and stated with the rule beside it |
| **V** — `dry-run`'s probe reaches outward | A project-local probe is called once per resolved condition; `W-APPARATUS-UNANSWERED` fires for a declared fact it did not answer; exit `5` when it is unreachable | The probe counts its own calls into a file **outside** `output_dir`, so the call count is evidence and the *Creates nothing* arm stays true |
| **W** — the credential positive control | A probe raising with a **declared** credential in its message prints `<redacted:…>` at `dry-run` | The credential is declared through `Param(requires_env=)` and set in the environment, so the redaction has a real value set to match against — an undeclared one would pass vacuously |
| **X** — cost ordering | A config with a validation error exits `1` and the probe is **never called** | The probe writes a file on entry; the assertion is that the file does not exist. An exit-code-only assertion would pass with the ordering reversed |
| **Y** — creates nothing | `output_dir` is byte-identical across the command and holds no `run_*` directory; and `dry-run` against a run directory holding a live `lock` completes | The comparison is a recursive `(path, size, bytes)` snapshot of `output_dir` taken before and after. `__pycache__` under the repo is the named excluded residue (Decision 12) |

---

## 9. Mutations

Each is named with the assertion that catches it, and **each was checked in advance for two branches
that can differ** — a mutation whose branches cannot differ is a claim like any other.

| Mutation | Caught by | Two branches differ? |
|---|---|---|
| In `_prepare_run`, return `Prepared` **without** the dirty check when `allow_dirty=False` | Arm E's dirty-tree exit | Yes — the arm asserts exit 1 and the `E-CODE-DIRTY` text; without the check the run proceeds and writes a record |
| Swap `allow_dirty=True` for `False` in `command_dry_run` | Fixture Y run from a dirty tree | Yes — dirty tree, so the two paths give exit 1 versus exit 0 |
| Force `code_dirty=True` under `draft` | Fixture R | Yes — R's tree is verified clean, so `false` and `true` are distinguishable |
| Drop `_arm_keys` from `dry-run`'s narrowing | Fixture T | Yes — T's arms are proper subsets of the roster, so the sums differ |
| Drop the `None`-contributes-zero branch (count the whole roster at `run`/`condition` scope under a fold) | Fixture S | Yes — S's fold has k > 1 and a `run`-scoped step, so the sums differ |
| Reorder `dry-run`'s phases so the probe precedes validation | Fixture X | Yes — X's probe writes a file on entry; the assertion is its absence |
| Remove the `try` around `_probe_for`/`observe_once` | Fixture W | Yes — W's credential appears verbatim versus `<redacted:…>` |
| Add `append_observation` to `dry-run`'s round | Fixture Y | Yes — an `apparatus/` directory would appear under a path Y snapshots |
| Replace the shared arity arm's condition with a bare `len(rest) != 1` | **A new assertion this slice owes**, on the message and on the leading-`-` rejection for one of the two new commands | Yes — `main(["dry-run", "--json"])` is one argument and is rejected only by the `startswith("-")` half |
| Reorder `credentials` and the roster resolution inside `_prepare_run` | **Named blind in advance** — no shipped fixture makes the two orders differ, because the fault needs a *resolver* that raises carrying a credential | **No.** Owed a replacement: a resolver-raises fixture at `run`, asserting `<redacted:…>`, built in the extraction task. If it cannot be built, the ordering is pinned by an assertion on the statement order in `_prepare_run`'s own AST, and the design says which was done |
| Replace `isinstance(prepared, Prepared)` at a call site with a truthiness test | **Named blind in advance** — `Prepared` has no falsy instance and `EXIT_OK` is `0`, so `0` is the only `int` the swap would mis-handle, and phases 1–5 never return `EXIT_OK` | **No.** Owed a replacement: the rule is stated once (**every caller checks the union with `isinstance`, never truthiness**) and `mypy` is the enforcer; the four exit codes are pinned end-to-end by arm E instead |

---

## 10. Batching

**Fourteen tasks in seven batches, every batch reviewed.** The count is what the tasks came to, not a
figure aimed at the scoping's 12 — the scoping itself predicts a plan exceeds its own count, and
merging tasks to hit a number is the failure mode that prediction is about.

| Batch | Tasks | Why together | Review |
|---:|---|---|---|
| **1** | 1 | The guard pin, before anything moves | Every arm proven able to fail |
| **2** | 2 | **The extraction, alone.** | **A real-command review**: two worktrees, one config, `run.yaml` leaf by leaf, the tree path by path, stdout line by line, the normalization list written in advance and every remaining difference attributed. Green tests are not the evidence |
| **3** | 3, 4 | `draft`'s behaviour, then `draft` dispatched — the second needs the first to exist | The arity mutation, and § CLI reference's `draft` row |
| **4** | 5, 6 | `draft`'s three positive controls, and the clean-tree case | Each reader shown able to fail |
| **5** | 7, 8, 9 | `dry-run`'s derivation, its `unit-executions`, and its dispatch | The agreement pin against a real `run` |
| **6** | 10, 11 | The probe round and *Creates nothing* — one question from two ends | The credential positive control |
| **7** | 12, 13, 14 | The documents, the records, and both consistency passes | The batch with no review is where the findings will be; this one is reviewed |

**Batch 2 is the extraction and it is a batch of one.** That is deliberate: it is the only batch in
this slice that can change a shipped value, and a reviewer reading it must be reading nothing else.
