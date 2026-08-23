# H9a — the re-entry seam, `draft`, `dry-run` — the ledger

Branch `h9a-re-entry-seam`, off `main` at the H6b merge. **14 tasks in seven batches, every batch
reviewed.** H9 was scoped at **49 tasks in four parts**; H9a is the only part touching a shipped code
path, which is why it goes first and why its first task is a guard pin.

**This slice is NOT additive**, and the design says so in a section of its own: four enumerated changes,
including two shipped invocations' exit code and output. Five controller rulings (R–U plus the retarget
below) bind it; H6a's C, F, M and H6b's O, Q still bind where cited.

## Batch 1 — task 1 — the guard pin

Commit `190de68`, reviewed with batch 2. Suite 2973 → **2983**, ten new arms, **none with an authorized
editor**.

**Most of what the scoping wanted pinned already existed**, and the batch checked before building: H8a's,
H8b's and H8c's arms plus `sweep.yaml` cover much of it, and **re-capturing would have recreated *the same
list pinned twice*** — the fault a previous slice's review found when one list was pinned in two places
and a task edited both. Arm C's fourth sub-claim is satisfied by **citing** an existing heavier fixture
rather than duplicating it. What did not exist got built: `executions.jsonl`'s line key set had **two
docstring-only claims and no assertion**, and the shared `OPERATION_COMMANDS` arity arm had **zero** hits —
which matters because *"operation commands take paths and nothing else"* is a `CLAUDE.md` invariant and an
extraction can move a command's arity silently.

**One self-caught defect worth the entry: an arm that compared a value against its own read-back.** Arm A's
first draft asserted `provenance.git.commit` against the value it had just read — self-referential, and
non-discriminating by construction, because a commit SHA cannot be a stable literal. Fixed by adding
`commit` to the **normalization set** instead. *A leaf that cannot be a literal must be normalized, not
compared to itself.*

## Batch 2 — task 2 alone — THE EXTRACTION

Commit `cd91adc`, controller retarget `ec43c95`, follow-up `1a35eaf`, review `5d288ac` (**both tasks
PASS**; one Major, four Minors). Suite **2984**.

**Behaviour preservation was measured against a target fixed in advance, and the reviewer re-measured it
independently.** Two console scripts from two editable installs, with a positive control printing a
distinct `publishable.__file__` per side: `run.yaml` **equal over 147 leaves in order**, the run tree
**equal over 26 paths by kind, size and sha256**, stdout **equal over 4 lines**, `sweep.yaml` equal over
30, exit code equal — with the only differences being `started_at` ×4 and `wall_seconds` ×1 inside
`executions.jsonl`, **both on a normalization list written before the work.** Phases 6–10's body is
**byte-identical over 1495 lines**; phases 1–5 differ in **exactly one line**, the dirty gate gaining
`and not allow_dirty`. **Zero unattributed differences.**

**The normalization list preceding the diff is the whole method.** *A normalization decided after seeing a
diff is a normalization chosen to hide it* — so the list went into the report first, and the review's job
was to check it had not been tailored to what was found.

**The task left the branch RED rather than edit an arm with no authorized editor, and that was right.**
`test_cli_and_runner_call_sites_pass_the_named_constants` reads `inspect.getsource(command_run)`, and the
run-start round had moved to `_execute_prepared`. **Worse than red: its negative assertion now passed
VACUOUSLY** — a literal absent from `command_run` is absent from it whether the call site is there or not.
The controller's retarget reads an **enumerated list of bodies** rather than the module: a module read
would keep passing when a call site moves, while an enumeration **fails loudly at the moment a human
should re-aim the pin**. Re-proven able to fail three ways — the constant→literal mutation fails **both**
assertions, and an off-list move fails it too.

**Three findings the task produced that its own brief and design had wrong.** The design's *"mutation b is
blind"* prediction is **falsified** — moving `credentials` below the roster fails `ruff` F821 statically
and **7 tests** at runtime — so the owed replacement rests on mutation **c** instead, measured rather than
inherited. The brief's docstring ground for carrying one variable across the seam was **false** and was
**deleted rather than rewritten**. And a **runtime-only failure both static gates passed**:
`conditions: "list[Condition]"` must be quoted, because `Condition` is `TYPE_CHECKING`-only and dataclass
annotations evaluate at runtime — `ruff` and `mypy` were clean with the bare name and only importing
caught it. **The crossing count is 36, not the plan's 35**, and the 36th is a *parameter*, which the plan's
`ast` Store-walk structurally cannot see; `ruff` F821 found it.

**The Major is a count that was filed, listed and true at three different values.** Correction 22 —
prose naming `command_run` as the location of code now elsewhere — was **filed as five sites, listed as
four, and is six**, with two never named. The ~45 `src/`/`tests/` prose sites are adequately served by the
signpost docstring in `command_run` itself, where a grepping reader lands; **the normative § Errors rows
are not**, and all six are now corrected. **Ten further mentions are deliberately left**: each says the
run *command* meets a raise at run time, which stays true of `command_run` whichever helper holds the
line — the distinction the signpost exists to carry.

**And a Minor worth more than its rank: no arm mutation was ever run against the full suite.** Task 1's
mutation counts were **single-test-scoped and did not say so** — one reported as *"1 failed"* is
`247 failed, 196 passed` over its own file. The mutations were real and the arms do fail; what was wrong
was the number, which is the **ninth** miscount in four slices.
