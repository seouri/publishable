# H6a — the two hash definitions — the ledger

Branch `h6a-hash-definitions`, off `main` at the H5b merge. **13 tasks in six batches, every batch
reviewed.** The slice changes **what two identity functions compute for unchanged inputs**, which is a
harder exposure than H5b's: `aggregated`'s numbers were wrong on the record's own terms, whereas a hash
that moves is not wrong — it is *differently defined*, and no reader can see the redefinition from a
record. `schema_version` is deliberately **not** bumped (bumping makes `lineage.read_record_file` refuse
every record on disk), so **`uv.lock` is the carrier and the disclosure obligation is heavier, not
lighter.**

Five controller rulings arrived with the design (A–E) and four more with the plan (F–I).

## Batch 1 — tasks 1, 2, 7, 10 — the rulings, the documents, and the pin

Commits `c863e3e` (§ How the three are computed), `ad59bdd` (**the guard pin**), `76efc72` (the
disclosure and arm N), `13ae83c` (Ruling B written, the normalization claim deleted), `6db2942`,
`419ca29` (in-batch fix round), review `db32e13`. Suite 2931 → **2939**. **All four PASS, two Minors, no
Major.**

**Ruling F held and was measured rather than read.** Every `check-ignore` invocation runs as
`GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null git -c core.excludesFile= check-ignore -z
--stdin`, and both the batch and the reviewer built a throwaway repo with a global exclude beside a
committed `.gitignore` to confirm **only the committed rule answers**, with `.git/info/exclude` surviving
as the one disclosed residue. **The ruling overrode the brief in two places and the commit said so** —
the table row drops `core.excludesFile`, and the *machine-dependence is fine, the dirty gate has it too*
paragraph was **not written**. That paragraph would have been the defect: a gate answers *may this run
proceed here*, which is local by nature; a hash answers *is this the same code*, which is not.

**The plan's own base tree could not be run, and the batch found it rather than working around it.**
`templates/t.py` holding `b = 2` is **discovered as a project-local template**, registers nothing, and
`validate`/`run` refuse with `E-TEMPLATE-LOAD` — so arms A and B each carry **two** trees, the plan's for
the direct call and a runnable one for the `run_id` half. The consequence is a live overruling: **arm B's
moving set is four literals, not two**, and it is written into arm B's own docstring, which is the only
place a later task's implementer will see it.

**Two fixture premises were checked by running before any literal was pinned.**
`input_manifest_hash` covers `st_mtime_ns`, so arm C **fixes the roster's mtime** rather than recomputing
the figure; and `allocation_hash` would have been `null` on the implied project, so arm C's project
declares a `between`/`by_attribute` axis to make the figure real. **A fixture built on a false premise is
a fixture whose numbers agree with the bug**, and both of these would have been.

**Four of seven arms have no authorized editor — A, C, D and N — and every arm was proven able to fail.**
The reviewer mutated `hashes.py`'s fold separator (A, B, C, D fail; E correctly unaffected) and `diff.py`'s
row comparison two ways, and reproduced the **asymmetry** the in-batch fix round documents: inverting
fails both of arm N's tests, while forcing `True` fails only the DIFFERS half and leaves the control
passing. **Arm N is the seventh arm and holds the claim a later slice will most want to soften** — that a
`diff` across this boundary prints `code_hash DIFFERS` for identical code.

**One literal was wrong before it was pinned and the fixture caught it** — `parameters_hash` drifted with
a config's `rationale` text. That is the evidence the fixture discriminates, and it is worth more than any
assertion about it.

**Both Minors are about owners and names, and one is the rule stated exactly.** `hashes.py`'s `code_hash`
docstring still says it reads the working tree *"not from git"* — true today, **false after task 5** — and
the report routed it to *"task 3 or 5"*. **An owner that is a disjunction is not an owner**: task 3 changes
only the signature, task 5 wires the predicate, so it is **task 5's**.

## Batch 2 — tasks 3, 4 — the seam, and a pin arm edited without authorization

Commits `84a7393` (`include` required, `code_hash_of` extracted), `3baaa46`
(`unignored_under_hashed_trees`, `E-CODE-FILE-LIST`), `10f5fe0`, review `a59f862`. Suite 2939 → **2945**.
**Both PASS; one Major, and it is a process finding rather than a code one.**

**No pinned hash literal moved, which is this batch's whole claim** — the value change is batch 3's — and
it was verified digest by digest by running rather than by reading the diff.

**The Major: task 3 edited guard-pin arms A, B and D, exceeding its brief's authorization** (*"arms this
task may edit: E, and only by adding `None`"*). Substantively harmless — diffed to exactly `, None` plus
docstring prose, no assertion or digest moved, and **both of batch 1's production mutations were re-run
against the current tree and still caught.** But the mechanism is the finding, and it has two halves.

**Half one is sequencing, and it is the controller's.** The design finalized the **two**-argument
`code_hash` signature; batch 1's pin capture then wrote its new arms against the **old one-argument
call** an hour later, so task 3 inherited a tree where honouring *"arm E only"* left the module
un-importable. **A pin arm must be captured in the shape the design has already decided** — otherwise the
next task is forced to choose between a broken import and an unauthorized edit, and there is no third
option to find. The defaulted-parameter alternative that would have avoided this was **named and rejected
in the design on anti-fail-open grounds**, so it was priced in rather than overlooked; what was not priced
in was capturing against the superseded shape.

**Half two is the implementer's, and it is the rule worth carrying: an implementer may not
self-authorize an edit to an arm with no authorized editor, even when the edit is mechanical and even
when it turns out clean.** The device's entire value is that a passing arm is the proof; an edit made and
then justified is indistinguishable from an edit made to pass. **The route is a controller ruling**, which
costs one round-trip and preserves the thing the arm exists for.

**Everything else was verified by building the state rather than reading for it.** `check-ignore`'s
**tri-state** returncode has three branches, each independently mutated and each caught by a different
test. Ruling F holds at the **sole** invocation, config-neutralized. Ruling H's payoff is real:
`E-CODE-FILE-LIST` has **one** emit site, which is the property the extraction was chosen for over a
memoizing closure. And the three states that made `git ls-files` the wrong answer — a tracked file
deleted from the working tree, a tracked file under `__pycache__`, **a submodule** — were each **built**
against the shipped predicate and answered correctly. That is the difference between rejecting a proxy on
an argument and rejecting it on a measurement.

## Batch 3 — tasks 5, 6 — THE VALUE CHANGE

Commits `9685ae0` (the predicate wired at `command_run`), `c98b24e` (Fixture J, the duplicated
`__pycache__` pin replaced), `5974c93`, `d959b34`, review `eb8e347` (**both PASS — three Majors, six
Minors, none behavioural**), fix round `cb5003d` / `8f2b26f` / `440a72d` / `bc14559`. Suite 2945 →
**2951**, unmoved by the fix round.

**The value change is correct end to end, and both sides were built.** Through the installed console
script on a project outside the repo, a **byte-identical tree** records `09a843b1…` before this slice and
`f6a935cf…` after; `run_id` and `results/latest` follow. Ruling F was confirmed by behaviour rather than
by grep: a **machine-local global exclude left the file hashed** (`a34ed58…`), and moving the same rule
into a **committed `.gitignore`** returned the digest to `f6a935c`. That pair is the ruling's whole
content — *a rule that does not travel with the tree cannot define the tree's identity* — and nothing but
running it twice could have shown it.

**Three of the four moved digests land on the SAME after-value**, which the reviewer flagged rather than
skipped: a coincidence of three trees reducing to the same file set weakens each fixture's ability to
discriminate, and it is now named in a comment where the next reader meets it.

**Two brief steps were unreachable as written, and the second is the more interesting.** The plan's base
tree cannot be `run` at all (`E-TEMPLATE-LOAD`). And **a resolver writing into `src/**` on its FIRST call
refuses with `E-CODE-DIRTY` — because `validate` dispatches resolvers too**, so the write happens before
the gate rather than during the run. The fixture writes from the **second** call and asserts the counter.
Both were verified by running.

**The Majors were all claims, and the arm-E one is the device catching itself.** Guard-pin arm E's
docstring asserted *"`code_hash` still has exactly one production call site in `src/`"* — **made false by
this very batch**, sitting in an arm no task may edit. Batch 2's Major had just established the route:
**an implementer may not self-authorize an arm edit, even a mechanical one**. This time the route was
used — a controller ruling naming the post-edit state in advance (**that clause gone, the past-tense
count kept, no assertion or literal moved**) — and the diff shows one line. **That is the difference
between the two batches, and it is the whole value of writing the post-edit state before the edit.**

**`hashes.code_hash` was measured before it was judged, and the measurement reversed the likely answer.**
Zero production callers looked like dead code or a second definition of an identity function — *two
sources of truth for one identity function is the same fault as a separate defaults file, and worse,
because a suite pinned against the dead one keeps passing while the live one drifts.* Measured, its body
**is** `code_hash_of(hashed_files(...))`, the same two functions `command_run` calls, **pinned equal to
that composition by an existing test.** One implementation, not a duplicate. `reference.md`'s two mentions
say *"report never calls it"*, which is true and claims nothing more.

**And a mutation was dropped under a heading reading *"every one"*.** The reviewer re-ran it, Fixture M
catches it, **so the silence was the finding rather than a hole** — corrected by appending, never by
editing the heading. That is the fifth instance in two slices of *dropping a clause is legitimate;
dropping it silently is not.*

## Batch 4 — tasks 8, 9 — the zero-file refusal

Commits `758f8a7` (`E-CODE-EMPTY` at the caller, Fixtures G and H, two § Errors rows), `c09e937` (the
filing re-owned, the report), review `9262b45` (**both PASS**, one Minor), controller follow-up `b7a2ad0`.
Suite 2951 → **2953**.

**Ruling D is closed and the guard's placement was proven by the design's own evidence.** The reviewer
**moved the guard into `hashes.py` in a scratch copy** and watched the two negative-control tests break
there — which is the argument for putting it at the caller, made as a measurement instead of as a
sentence. Both directions of the refusal are pinned by different mutations: deleting the guard restores
the old empty-digest behaviour (a completed run whose `run_id` ends `_e3b0c44`), while **moving it past
`allocate_run_dir` fails on the *no run directory* assertion instead** — different failures for different
faults, which is what *pinned in both directions* means.

**One thing the batch review got wrong, and the shape is worth more than the fix.** It settled where
`E-CODE-EMPTY`'s § Errors row belongs by **citing the design's instruction** — *"the design directs it to
§ Errors core raises, so the report's self-doubt was unfounded."* That is **answering from a proxy**: the
direct question is what the table's own scope sentence and column header say. They say **"Raised by |
Type · code"**, over a preamble that introduces an exception hierarchy and describes *"the surfaces that
raise instead"* — and `E-CODE-EMPTY` raises nothing, which is why the task had to invent a `Type` cell
reading *(no exception; a `Collector` diagnostic)*. **A design can direct a row into a table whose scope
does not admit it, and then the design is what is wrong.**

**The fix names the third category once rather than moving the row.** `validate` neither hashes nor
consults git status, so these codes do not belong in § Errors `validate` reports either; a reader who
meets one at `run` looks in § Errors core raises. So that section's preamble now says **two of its rows
are refusals a command makes through a fresh `Collector`**, and why. **And `E-CODE-DIRTY` gained the row
it never had** — a shipped code documented nowhere, which is *the documented-rule-with-no-code defect
running in reverse*, and whose very absence is what made the invented `Type` cell look acceptable: with
no sibling to match, there was nothing to be inconsistent with.

**The new row's claims were each checked against the code before it was written** — `git status
--porcelain` over the two trees, so **untracked files count and ignored ones do not** — which lets the row
state Ruling F's real payoff: **the gate and the hash now consider the same set of files, and did not
before.** That was the defect this slice opened with, stated from the other end.
