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

## Batch 5 — task 11 alone — `W-PARAM-UNSET`, and Ruling B's replacement payoff

Commit `c4dea36`, review `0c0a92c` (**PASS**, one Minor). Suite 2953 → **2955**.

**Ruling B's rejection of the charter's own clause is now paid for rather than merely argued.**
`parameters_hash` is not normalized against `parameter_spec` — normalizing would give **one identity claim
to a config that runs and a config that cannot**, since an omitted `parameter_spec` default validates
clean and then its step dies. What H6a ships instead is the diagnostic that makes the omission visible at
`validate`, as a **warning rather than an error**, because omitting a defaulted parameter is what almost
every config in this repo does and core cannot know whether a step reads it without reading user Python.

**Three different blast-radius numbers were in play and the reviewer measured rather than picked.** The
design said *"5 tests assert `✓ config valid`, 4 assert the `N problems` line"*; the plan's correction 7
said *"zero `✓`, three not four"*; and the task then measured **eight** pre-existing tests firing the new
warning where the design said seven. Measured independently: **zero and three** (correction 7 right), and
**nine total firings, eight of them pre-existing** (the task right, the design wrong). **Three sources,
two of them wrong, none of them wrong in a way anything downstream would have caught** — which is the
whole reason this project re-measures instead of carrying.

**The shared-helper extraction was checked the way that class of change has to be checked.** A
comprehension moved out of `_check_versions` and gained a second reader, and *when you move a call site,
grep the suite for patches aimed at what you moved* — a monkeypatch left pointing at a name the code no
longer calls defuses itself while its test keeps passing. None existed, and the reviewer then **blanked
the helper's body and confirmed BOTH readers' tests fail**, which is the direct question rather than the
grep's proxy for it.

**Both directions are pinned by distinct mutations** — deleting the call site fails only the positive
arm; inverting the condition fails four tests. And **a true claim was deliberately kept**: the design
ruled that *prefer deleting to rewriting* does **not** license deleting `W-TEMPLATE-VERSION`'s clause,
because it is true. The clause deleted was a different one — a shipped docstring's *"so a defaulted
parameter it omits is not reported"*, **made false by this very task**, which is the third time this slice
has caught a sentence going false under its own change.

**The Minor is the sixth miscount in two slices**: *"caught by arm F alone"* against a measured two. None
of the six changed a conclusion.

## Batch 6 — tasks 12, 13 — the records, reviewed rather than skimmed

Commits `f70499f` (three entries struck, two gaps filed, the spine correction, `CLAUDE.md`), `fe8ea47`
(the § Executability entry), `eb5b038` and five self-found corrections, review `d56eee3` (**both PASS**,
no Critical, no Major, two Minors carried to the gate), controller follow-up closing both. Suite unmoved
at **2955**; no file under `src/` or `tests/` touched.

**§ Executability does not move, re-derived rather than repeated**, and the four-row table was
**independently re-extracted and diffed byte-for-byte** against the preceding entry by the reviewer
rather than accepted on the report's md5. Row 1 counts *errors* and `W-PARAM-UNSET` is a warning; the two
new errors are raised by `command_run`, not `validate`; rows 2–3 name dependencies this slice does not
touch; row 4 counts per-config dependencies and `code_hash` is computed for every run regardless of
config. Whether `W-PARAM-UNSET` fires on those nine is **unknowable with a reason** — neither plugin is
installable — which is the honest form of that answer.

**The batch found two things wrong in its own authorities, which is what a records task is for.** The
brief and the design both said H6a *"took none of the nine undocumented codes"* — **it took one**,
`E-CODE-DIRTY`, in this slice's own batch-4 follow-up, found by `git log -S` rather than by reading. And
**the plan's § Corrections 9 is itself wrong**: `_parameters_hash_for` **does** exist, and the correction
confused it with the alias it calls. *A correction that is wrong is worse than no correction*, because a
task told to distrust a name distrusts the right one.

**Two Minors were left for the gate rather than fixed, and the restraint was the right call in one and
the routing right in the other.** A `reference.md` row attributed the no-defaults-file rule to
`design-principles.md` while its own link points into `reference.md` — **outside task 12's file list, and
batch 2's Major was exactly a self-authorized out-of-scope edit**, so it was named rather than taken. And
**Decision 15 misreads the sentence it proposes to change**: § Templates' *"goes dirty at `validate`"*,
read with its own subject, says discovery's import writes `templates/__pycache__/` so **the tree becomes
dirty as a result of validating** — which is true, and is a stronger claim after Ruling F than before,
since a `.gitignore` omitting that line now changes two answers rather than one. Both are closed by the
controller: the attribution edited, the misreading **appended** to the design rather than edited into it.

**And the batch disclosed that its own mechanical checker produced eight false positives on first run.**
That is the third time in two slices a sweep or checker could not be trusted until debugged — *prove
every sweep can fail* is a rule about the checker as much as about the claim.

## The whole-branch gate — HOLD on three Majors, and a ruling the fix round handed up

Review `d920470` (**HOLD**), fix round `7d55c87` / `26b5b6e` / `f5df7ee` / `33311f3`, then **Ruling M**
`7e30c4b` / `b69ef17` / `bb15a78`. Suite 2955 → **2963**, against `main`'s 2931.

**Every moved digest is enumerated and pinned** — a `main`-versus-HEAD run over one byte-identical project
outside the repo differs in `code_hash` alone (`09a843b1…` → `f6a935cf…`) plus timestamps, with `run_id`,
the directory name and `latest` following it and covered by arms A, B and C. All seven arms were proven
able to fail; the four with no authorized editor moved no assertion, literal or name; arm E moved only the
clause Ruling J authorized.

**And the gate earned itself on the slice's own central claim: Ruling F was pinned by NOTHING.**
`grep -rn "GIT_CONFIG_GLOBAL\|excludesFile" tests/` returned zero, and **removing the entire neutralization
left the suite byte-identical.** Batch 1 and batch 3 had each measured the property by hand — twice, on
different days, both times correctly — and *a probe proves the moment; a test proves tomorrow.* That is the
sixth time in four slices a correct fix shipped unpinned because a probe stood in for a pin.

**Two claims of the form "the only machine-dependent input left" failed, and I wrote one of them.** The
`E-CODE-DIRTY` row I added in batch 4's follow-up said *"the gate and the hash now consider the same set
of files, which they did not before"* — **false, because the hash was neutralized and the gate was not.**
The hole ran the wrong way and that is why it mattered: a globally-excluded file was **clean to the gate
and folded into the hash**, giving a run whose recorded identity covered a file **no clone of that commit
contains.** **Ruling L** closed it by neutralizing the gate too — *applying Ruling F's principle to the
hash but not to the gate is what produced the false sentence.* And the fix round then found that **Ruling
L alone still would not make the sentence true**: the hash drops its fixed skip set unconditionally, so a
tracked modified `src/pkg/step.pyc` is dirty at the gate and read by no hash. The row now claims **one
exclude chain**, not one file set — a smaller claim that is true. The **second** such failure was an
**uncommitted root `.gitignore`**, which decides what is hashed while the gate, scoped to the two trees,
cannot see it — the word *only* deleted rather than narrowed, and the residue filed against H6b.

**Ruling M is the entry worth carrying furthest, because the fix round could have shipped its own fix.**
Total neutralization — clearing `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM` and `core.excludesFile` — closed
the exclude question **and also killed `core.fileMode`, `core.autocrlf` and `core.symlinks`**, which are
*legitimately* machine-local: they exist because filesystems differ. Reproduced: with a global
`core.fileMode = false`, `chmod +x` on an **unedited** tracked file read `M`. **A run blocked on a correct
tree is strictly worse than the fault being closed**, and it would land on exactly the users least able to
diagnose it. The surgical form — `-c core.excludesFile=` plus `-c status.showUntrackedFiles=normal`, no
environment variables — **answers the direct question**, and the measurement that decided it is that
`-c core.excludesFile=` **alone closes all three exclude routes** (global config, the XDG default
`~/.config/git/ignore`, and a repo-local `.git/config`), so the environment variables were never
load-bearing for excludes at all. **Answering with a blunt instrument that happens to contain the answer
is the proxy move this repo keeps paying for** — and this time the agent that built the blunt version
**measured the alternative and handed the choice up rather than swapping it in**, which is the behaviour
the arm-edit rule was written to produce.

Two side effects of the surgical form, both measured: it reaches a **repo-local**
`status.showUntrackedFiles = no` that the environment form never did, and it **closes the `safe.directory`
fail-open** the fix round had just filed, since a legitimate global entry is no longer discarded. **Each
`-c` flag has its own arm** — removing the excludes flag fails four tests, removing the untracked flag
fails exactly one.
