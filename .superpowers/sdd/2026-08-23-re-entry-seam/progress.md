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

## Fix round — batches 3–5 review (`task-b4-review.md` @ `574eba7`)

Four Majors, five Minors — all closed or explicitly ruled open. Full detail in the dated addendum to
`task-b4-report.md`. Two code fixes (`dry-run`'s double-counted `baseline`, the shared arity arm's
mischaracterized pin), two document-only fixes (`reference.md:872`'s stale "resolves the run
directory" clause, task 12's sweep target amended in the plan), and three test additions (a
baseline+grid fixture pinning Major 1, Fixture V fixturing the holdout leg Minor 3 named, and a
`main([...])`-driven arm closing Minor 4). Suite 3010 → 3012 (+2, the two brand-new test functions;
no other count moved).

**One deliberate non-fix, ruled rather than silently deferred:** Minor 5's `probes the apparatus`
clause stays in `reference.md`'s `dry-run` row false-until-task-10, because task 10 — next in this
same slice, same unmerged branch — is what makes it true, and narrowing it now would mean re-widening
it again inside one slice. The whole-branch gate owns re-checking it; if task 10 doesn't land before
merge, that promotes this to a Major at the gate.

## Batches 3, 4 and 5 — tasks 3–9 — `draft`, `dry-run`, and their documents

Commits `137d55e`, `d4af219`, `16518aa`; `5bb8009`, `41208be`, `b5a2293`, `985971a`, `a684f1b`,
`6cc266f`, `6421e62`; review `574eba7` (**all seven PASS**, four Majors, five Minors); fix round
`0525cc5` / `72ea0d2` / `d8f79ef`. Suite 2984 → **3012**.

**`dry-run` creates nothing, and that was established by snapshotting rather than by reading.** A
whole-tree `{path → sha256}` map before and after `main(["dry-run", cfg])` gave **ADDED [] REMOVED []
CHANGED [] over 119 paths** — and it is pinned: a `mkdir` under `output_dir` fails both arms. *If a comment
says nothing is created, make it create something* is the rule, and reading for absent `mkdir` calls is
the proxy it forbids.

**Batch 3 found the gap its own brief was written around.** `_execute_prepared` **accepted `draft` and never
forwarded it** to `assemble_run_yaml` — an unread parameter, which is *an unbuilt reader of a shipped
surface* in miniature. Wired and pinned by a mutation that removes the forwarding.

**Major 1 is a live output defect that the worked example's own shape produces.** `dry-run`'s sweep header
printed **`(baseline + baseline + grid)`**, because `modes` seeds with `"baseline"` and then adds every
truthy `sweep` key — **and `baseline` is one of them.** The only assertion on that line used a **grid-only**
config, so it was structurally blind: *a fixture that cannot distinguish the two readings is not a
fixture*. Closed with a **baseline+grid** fixture, and the mutation reproducing the bug fails only the new
test — which is the proof the old one was blind rather than merely quiet. **The first thing a reader of the
docs would have run is exactly this shape.**

**Major 4 is *"pinned by nothing"* being false, and the reason is the proxy this repo keeps paying for.**
Both the plan and the design said the shared arity arm was unpinned; **two pre-existing tests fail when the
count half is dropped.** Only the **flag** half was genuinely new. It was missed because **both greps were
on message text** — *answering a question with a proxy*. Corrected by **appending** to the plan and the
design rather than retro-editing either, and the narrower truth stated: count pinned, flag not.

**Major 2 is a mandated sweep that would have found nothing.** Three unowned `reference.md` edits were
**correct in content** and left `grep "every artifact path"` at **zero homes across six files** — so a
later task told to sweep for it would have reported zero and called it clean. The plan's § Task 12 was
**amended** to target strings that exist, re-measured at 4 and 3 homes. *A correction that is wrong is
worse than no correction.*

**Ruling R's narrowing held and its cost is stated rather than hidden.** § Operation commands promised
*"every artifact path that would be written"*, which requires reading step bodies — something
`reference.md` itself promises core never does. **A promise requiring a stated non-promise to be broken is
the document being wrong**, so `dry-run` prints step directories, fixed files and the unit-execution
count, **and the row names what it omits.** The same clause was found kept at one site while deleted at
another and is now deleted at both.

**One Minor is deliberately left OPEN inside the slice, with the reason.** The `dry-run` row's *probes the
apparatus* clause is false until task 10 lands — **narrowing it now would mean re-widening it inside one
slice**, so the whole-branch gate owns re-checking it, and **it promotes to a Major there if task 10 does
not land before the merge.** That is the honest form of a scope boundary: an open finding with a named
escalation, not a silence.

**And the review could not fault a single mutation count** — five disjoint mutations reconciling to
exactly 10, three to exactly 7 — **the first batch in four slices where that was true.**

## Batches 6 and 7, and the whole-branch gate

Commits `204fbf7` (the probe round), `42019f5`, `efad33c` (the transcript and thirteen § Errors rows),
`c925416`, `e133833` (both passes, § Executability), `66a24b4`, `12a9370`, reviews `a08cec7`
(**all five tasks PASS**; gate **HOLD** on two Majors), fix round `bf2a76e` / `c6bec08`. Suite
**3019 passed, 1 skipped, 2 xfailed** against `main`'s 2973 — **+46 test functions, derived by an `ast`
walk rather than counted.**

**The extraction is still behaviour-preserving at HEAD, and the gate re-measured it rather than inheriting
batch 2's number.** Two editable installs with a positive control: `run.yaml` equal over **284 leaves in
order**, the tree over **36 paths**, `sweep.yaml` over 31, `executions.jsonl` **key by key**, stdout,
stderr and exit code — one difference, `config.yaml`, attributed to a normalization item and empty once
paths are normalized. **Zero unattributed differences**, against a slice that moved 1916 lines of shipped
code.

**The deliberately-open finding closed.** The `dry-run` row's *probes the apparatus* clause was false when
batch 5 shipped it, left open with a named escalation, and task 10 made it true — verified through the real
console script with an installed probe distribution: **two probe calls, one per resolved condition, each
under its own cfg** (`m1`, `m2` — not `m1`, `m1`), both warning, `output_dir` empty, exit 0. **Four homes,
where the finding named one.** *An open finding with a named escalation is how a scope boundary should
read*, and this is the instance where it worked.

**Three mutations in these batches were claims that did not survive contact.** The design's Fixture Y
mutation was **blind on every shipped arm** — all three drove a `generic` project with
`apparatus_probe = None`, so `append_observation` had no round to add to; spliced in for real it gives
1 failed, 3 passed. Fixture X's mutation is **not constructible** (`prepared` unbound). And a `dict.fromkeys`
comment argued its de-duplication was *"real rather than defensive"* **for a case that cannot occur** —
removing the call entirely left the suite unchanged, so **the comment was corrected to say defensive**,
which is what *a safety argument in a comment is a claim* means when the claim turns out false rather than
dangerous.

**Major 1 is `CLAUDE.md`'s own insertion rule, failing in a new way.** Task 12's insertion into a
§ Warnings row **displaced the antecedent of the following sentence**, so the row said `dry-run`'s counts
are *"replayed from the ledger"* three clauses after saying they are *that round's own in-memory counts
alone* — **the one thing the design's decision exists to deny.** *When you insert or remove a row, check
every row it moved* now has a sibling: **check every sentence whose antecedent it displaced.** The other
twelve row edits were swept in full context; only this one had the shape.

**Major 2 is a disclosed behaviour change whose disclosure was wrong — including in a dated entry.** Three
records said `publishable draft new` keeps its exit code and prints the arity message. Measured on both
console scripts: exit **2 → 1**, the line is **`E-IO-FAILED`**, a config path **is** read, and the arity
arm is **never reached** because `new` is a single token. **Task 4's own test docstring had it right the
whole time.** Corrected by appending to the design, the plan and the § Executability entry, and in place in
`CLAUDE.md`. **A wrong disclosure is worse than no disclosure**, because it tells a reader the change is
smaller than it is — and this one was the only place a user would have looked.

**And the tenth miscount: *fifteen* narrowed § Errors rows is thirteen** — fourteen counting the fix
round's, whose fourteenth is a **widening**, not a narrowing. A count that merges two kinds is the shape
behind three of this family's miscounts, so the widening is now stated as its own fact.
