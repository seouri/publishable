## Task 13: the § Executability entry — four rows, character for character, no fifth number

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is how the previous
> slice shipped a Critical, and this pointer is the fix. **Ruling F (the exclude chain) changes the
> command every hashing task runs.**

**Surface: one appended dated entry in a non-normative analysis.**

**Files:** `docs/feasibility-llm-growth-studies.md`.

**§ Executability does not move, and the design DERIVED that rather than assuming it.** Row 1 counts
configs validating with zero **errors**; `W-PARAM-UNSET` is a warning, which changes no exit code and no
error count, and the two new **errors** are raised by `command_run`, not by `validate`. Rows 2 and 3 name
`io.reuse_from`'s plugin-side call and the `report_by`-under-`resample` gap, neither of which this slice
touches. Row 4 counts configs free of every core-side dependency the analysis can name; `code_hash` is
computed for every run regardless of config, so **no config gains or loses a dependency**.

- [ ] **Step 1: append one entry**, headed *"Measured on 2026-08-22 against commit `<sha>`"* with the
      branch's own sha, in § Executability on this build. **Never state a build fact undated.**
- [ ] **Step 2: repeat the four rows CHARACTER FOR CHARACTER, copied from the FEASIBILITY ANALYSIS' own
      last entry — NOT from this plan's header.** This plan reproduces the table in its own opening for a
      reader's convenience, and **that copy is not a source of truth**; a second source of truth is how
      both of this analysis' wrong figures were made. Copy the immediately preceding entry's table out of
      `docs/feasibility-llm-growth-studies.md` and **diff it against that source rather than retyping
      it.** **No fifth number is minted, and
      no single figure is quoted for this analysis' executability — quote the table, or name the
      dependency.**
- [ ] **Step 3: state what newly stops and what newly warns, for THESE configs, in prose.** Following
      H5b's own dated correction — whose finding was a miscounted *newly-firing* thing rather than a
      moved row — the entry says: **`E-CODE-EMPTY` and `E-CODE-FILE-LIST` cannot fire for any of them**,
      because both are properties of a repository rather than of a config and no config in this analysis
      names a repository; and **`W-PARAM-UNSET`'s effect on them is UNKNOWABLE, with the reason** — it
      depends on the `growth_screen` template's `parameter_spec`, and neither `growth_screen` nor
      `publishable-llm` is installable in any build.
- [ ] **Step 4: state the value change's effect on this analysis, and it is not a row.** Any run of any
      of these configs made before this build and any made after would compare as `code_hash DIFFERS` for
      identical code if the project carried an excluded file under the two trees. That is a fact about
      comparisons, not about executability, and **it mints no row.**
- [ ] **Step 5: mechanical pass** in full — this file is **exempt from the cross-document pass** and
      subject to the mechanical one in full: links, anchors, tables, whitespace, `×` for multiplication,
      hyphens in anchors.

**Delta:** 0 tests.

**What this task must NOT touch.** Any of the four documents. Any row of the table. The corrections
already in that section.

**Guard-pin arms this task may edit: NONE.**

---

## Corrections against the code

**Appended by this plan's author and extended by no task.** Each was measured at `f8450f9`, in a
scratchpad git repository or by running the suite. The rule is `CLAUDE.md`'s: *the plan argues from the
spec, and the code outranks both; where they disagree the code wins and the document changes first.*
**Six of six implementers on one recent slice found a real disagreement, so finding one is expected** —
and **do not report a count of zero.** Every claim below names what was run.

**1. `git check-ignore` answers from git's WHOLE exclude chain, not from `.gitignore`.** The design's
Decision 1, its four-case table and its § The value change all say *"`.gitignore`"*. **Measured** in a
scratchpad repo: with `core.excludesFile` pointed at a file holding `globignored.py`, `.git/info/exclude`
holding `infoexcluded.py`, and a **per-directory** `src/sub/.gitignore` holding `perdir.py`, one
`check-ignore -z --stdin` call reported all three of `src/pkg/globignored.py`,
`src/pkg/infoexcluded.py` and `src/sub/perdir.py` as excluded. **What the task must do instead:** task 1's
four-case table names the chain in its *excluded* row and task 1's step 3 discloses the consequence — an
untracked file under the two trees can be excluded on one machine and not another, which collides with
§ How the three are computed's own *"A hash that two machines compute differently is not an identity
claim."* **The honest framing, and the one to write: the dirty gate already has this property today**
(`git status --porcelain -- src templates` consults the same chain), so Decision 1 **extends an existing
behaviour to the hash** rather than inventing one — which is Decision 1's own argument. **This reopens
neither Decision 2 nor Decision 1**, and no task may add a flag that narrows the chain.

**2. Under the design's own task split the predicate runs TWICE per run, and that falsifies three of its
claims.** Task 8's guard is specified over `hashed_files`' return while task 5 wires `include` at
`code_hash`'s call site — so `command_run` would call both, walking the two trees twice and running
`git check-ignore` twice. **Measured on a 10,002-file tree:** the walk costs **233 ms** and
`check-ignore` **875 ms**, so the naive shape costs ~2.2 s of pure duplication. It also makes Decision 4's
*"the walk happens once, in one place"* false, and makes `E-CODE-FILE-LIST`'s **one emit site** false
against the code, since the helper would have two reachable raise paths. **What the task must do
instead:** task 3 extracts `code_hash_of(pairs)` and task 5 does `pairs → guard → fold`, with **task 3
step 3's identity test** keeping the two paths one and **task 5 step 8's subprocess-count pin** proving
the once. **And the tempting one-liner for the guard is rejected by name:** `ch == "sha256:e3b0c442…"`
answers *were there zero files?* with a digest comparison — **a mutation swapping `not pairs` for it
passes every fixture in this slice**, which is why task 8 forbids it in the brief rather than leaving it
to review.

**3. `check-ignore` does NOT "cost the same" on a large tree — 875 ms against 19 ms.** Decision 2's
ground includes *"it costs the same: 12.1 ms against 12.2 ms over this repo's 53 paths"*, and Decision 6's
cost-if-wrong says *"one subprocess per `run`, once, measured at 12 ms for 53 paths."* **Measured here on
a tree of 10,002 hashed files:** `check-ignore -z --stdin` **875 ms** (five runs, min 874.6), `ls-files
-z -co --exclude-standard` **19 ms** — a 45× gap, and `check-ignore` alone costs **2×** the whole
`code_hash` computation (410 ms) and 3.8× the walk. **Decision 2 still stands and is not reopened**: the
three `ls-files` failure modes are real and one of them (a submodule's contents) is **silent**, and
correctness outranks 850 ms once per run. **What the task must do instead:** task 5's report records the
measured figure beside the 12.1 ms one; the `ls-files`-plus-three-exceptions fallback stays recorded in
Decision 6 so a successor does not re-derive it; and the **second axis is named as unmeasured** — cost
plausibly scales with **pattern count** as well as path count, and this was measured against a
four-pattern `.gitignore`.

**4. Fixture F as designed cannot catch mutation 3, and under one reading it cannot pass at all.** The
design's Fixture F uses **tracked** non-ASCII files and asserts *"`git_answer_set == {rel for rel, _ in
hashed_files(repo)}`"*. **Measured:** for tracked, unexcluded files `check-ignore -z --stdin` returns
**rc 1 with empty stdout** — so git's answer is the empty set and the stated equality is false, while the
*kept* set is everything with or without `-z`, so **mutation 3 changes nothing**. The design's item 7 was
measured against **`ls-files`' output — the rejected route** — and carried into a fixture for the chosen
one. **What the task must do instead:** task 4 step 5 rebuilds Fixture F on **excluded** non-ASCII paths.
Measured there: `check-ignore` returns them, without `-z` they come back C-quoted
(`"src/pkg/na\303\257ve.env"`), nothing is subtracted, and the digest stays at `06604d0c…` instead of
`71bf339c…`. **Two branches that differ, computed.** A bonus the restructure buys: an untracked path
never round-trips through the index, so **no NFC/NFD platform caveat applies** — the design's *"read the
fixture's result on Linux before trusting it"* belongs to the tracked arm being dropped.

**5. Fixture D's literal `6ddb8634…` is not reproducible from the design's own stated tree.** The `.pyd`'s
**bytes are never stated**, and the digest is a function of them. **Measured:** over the base tree with
`src/pkg/loose.pyd` = `X`, the digest is `sha256:eec1541edde45c11c395e788000f719a48965a8f6fd2b3772a56de92cca18dc2`;
nine candidate contents (`X`, empty, `\n`, `c = 3\n`, `a = 1\n`, `b = 2\n`, `d = 4\n`, `pyd\n`, a NUL
byte) were tried and **none** produces `6ddb8634…`. **What the task must do instead:** task 5 step 5 and
task 2's arm D fix the bytes at `X` and assert `eec1541e…`. The design's structural claim **does**
reproduce and is kept: the untracked twin's *today* value is also `eec1541e…`, so the **after** column is
the discriminator.

**6. Fixture H would not reach `E-CODE-EMPTY` as the design states it.** It is described as *"a committed
repo whose `.gitignore` is `src/` and whose `src/pkg/step.py` is untracked"*, deriving from a tree that
also holds `templates/t.py`. **Measured:** with `templates/t.py` present the dirty gate is clean, the
after digest is `sha256:ef36e0c97881b4541db22e03def3912ed01059e4fdeeb739079b1244554f62c7` and **the
refusal never fires**; with **no file under `templates/**`** the after state is **zero hashed files** and
today's digest is `sha256:f6a935cfc29196b2a5f5a7f873096c4ab3ee077ff3152afedafeb34fb919078a`. **What the
task must do instead:** task 8 step 3 states the no-`templates` requirement and carries the
counter-example, so a later fixture edit cannot quietly re-add the file.

**7. `W-PARAM-UNSET`'s blast radius is ZERO failing tests, and the design's bound is wrong in both
halves.** The design says *"5 tests assert on the `✓ config valid` string and 4 on the `N problems`
summary line"* and asks the plan to measure. **Measured:** `grep -rn '✓' tests/*.py` → **0 hits** —
**no test asserts that string at all** (it is printed by `command_validate` and asserted nowhere) — and
`grep -rn "problems (" tests/*.py` → 4 hits of which **3 are assertions**, all in
`tests/test_diagnostics.py`, over configs that never reach `_check_parameters`. Then the real
measurement: a copy of the repo with the warning wired in exactly Decision 10's shape ran the **full
suite green — 2931 passed, 1 skipped, 2 xfailed**. The measurement is **not vacuous**: a direct positive
control fired (a config omitting two of `generic`'s four produced one `W-PARAM-UNSET` naming both; the
complete config produced none), and an instrumented subset run showed the warning firing in **7** tests
across `tests/test_validate.py` and `tests/test_templates.py`, all passing. **What the task must do
instead:** task 11 step 6 carries the measured zero **and states what invalidates it** — a per-parameter
shape, or a different `path`, moves finding counts and path sets and must be re-measured.

**8. A shipped test's docstring becomes FALSE while its assertion stays green.**
`tests/test_validate.py::test_an_unset_parameter_is_named_only_when_the_version_moved` says *"The naming
is gated on the mismatch: a config matching the installed version draws no warning at all, so a defaulted
parameter it omits is not reported."* Its assertion is `"W-TEMPLATE-VERSION" not in codes(path)`, which
still passes — **and it was one of the 7 tests measured firing the new warning.** After this slice the
second clause is false. The design's Decision 11 rules the redundancy deliberate and never noticed that a
shipped test asserts the exclusivity **in prose**. This is the repo's *comment claiming a guarantee the
code does not provide*, at a site nothing would sweep. **What the task must do instead:** task 11 step 7
**deletes the false clause and keeps the test's name**, and says in the report that the edit sits
**outside guard-pin arm F**.

**9. `diff.py`'s helper is `_compute_parameters_hash`, not `_parameters_hash_for`.** The design cites
*"`diff.py::_parameters_hash_for`"* in Decision 12. Read at `f8450f9`: `diff.py` does
`from publishable.hashes import parameters_hash as _compute_parameters_hash` and calls that alias for a
config-side operand. **What the task must do instead:** tasks 7 and 12 cite the real name where they cite
one at all. The **behavioural** claim is unaffected and confirmed: only a config operand is recomputed;
a run side reads the recorded string.

**10. Mutation 7 is NOT blind — the fixture the design could not confirm is buildable, and here is the
construction.** The design lists *"whether a real resolver writing under `src/` during resolution is
buildable as a fixture"* as unmeasured and says the plan must build one or name the mutation blind.
**Measured by reading the helpers that already exist:** `tests/test_cli.py` holds
`_install_plate_wells_resolver`, which writes a real resolver module for an installed distribution's
entry point, and `run_a_project`, which scaffolds, commits and runs a project end to end. The resolver's
module **text** is written by the test, so it can embed an absolute path into the project's own `src/`.
**What the task must do instead:** task 5 step 7 builds it and asserts the **digest** — recompute
`code_hash_of(hashed_files(repo_root, live_predicate))` after the run and require equality with the
record's `code_hash` — rather than the generated file's presence, so the two branches differ by a digest.

**11. `run_a_project`'s `_env_file` writes at the project ROOT, which is in neither hashed tree.** Its own
docstring says so: *"a file at the project root is in neither."* Fixtures B and C need
`src/pkg/.env`. **What the task must do instead:** tasks 2 and 5 build those trees directly rather than
through `_env_file`, and say so, so an implementer does not reach for the helper and produce a fixture
that measures nothing. **The scaffold's `.gitignore` opens with `.env`**, so the file stays untracked
under `git add .` either way, which is what makes the fixture honest.

**12. The guard pin covers two of the five carriers, and the other three need a written derivation rather
than three more arms.** § The value change enumerates five fields carrying the moved hash. Arms A, B and
D cover `code_hash` and `run_id`; Fixture M covers `provenance.upstream[]`. **The bundled copy and the
`latest` target are unpinned.** **What the task must do instead:** task 7 step 1 states the derivation in
the document — `study add` copies a run's `run.yaml` **verbatim**, so the record's own pin covers the
bundled copy, and `point_latest` names the run **directory**, so the `run_id` arm covers the pointer —
and task 5's report says which carriers are pinned and which are derived. **Five carriers with two pinned
and no sentence is the shape a gate review catches.**

**What was grepped, rather than a count.** `grep -rn "code_hash(" src/publishable/*.py` → the definition
and `cli.command_run`, nothing else. `grep -c "code_hash(" tests/test_hashes.py` → **13**, enumerated by
test in task 3; `grep -rln "code_hash(" tests/` → `tests/test_hashes.py` and `tests/test_run_identity.py`,
**whose single hit is the NAME of `test_the_id_is_timestamp_then_short_code_hash`, not a call site** —
recorded so nobody re-derives it as a 15th. `grep -rn "hashed_files(" src/ tests/` → two hits, both in
`hashes.py`. `grep -c "git init\|subprocess" tests/test_hashes.py` → **0**. `grep -rn` for
`E-CODE-EMPTY`, `E-CODE-FILE-LIST` and `W-PARAM-UNSET` across `src/`, `tests/`, `docs/*.md` and
`README.md` → **0** each; control `E-CODE-DIRTY` → **3**, all in `src/` and `tests/` and none in a
document. `grep -rn "dirty" src/publishable/validate.py` → **0**. `grep -n "code_hash"
src/publishable/lineage.py` → the copy sites, confirming Fixture M's premise. `grep -rn '✓' tests/*.py` →
**0**. `grep -n "unconditionally\|has no bearing on\|goes dirty at" docs/reference.md
docs/experimental-designs.md docs/design-principles.md README.md` → both § Templates clauses in **one**
paragraph, and no other home. **None of these filtered the output of a sweep whose job was to find a
string.**

---

## Live overrulings — restated here because a ruling that overrules a brief has to reach the brief

A plan correction was once overruled when the plan landed, the overruling was recorded in the slice
ledger, and the plan was left carrying the old text — so the brief extracted from that plan still said
*delete*, and the task deleted. **The ledger reaches the controller and the reviewers; it reaches no
implementer.** These are in the plan itself, in the task sections they bind, and again here.

1. **`code_hash_of` exists and `command_run` calls the two-step form** (§ Corrections 2). A brief reading
   Decision 4 and Decision 7 literally would call `hashed_files` and `code_hash` separately. **Task 3
   builds the extraction; task 5 uses it; task 8's guard sits between them.**
2. **The rule is git's whole exclude chain, never "`.gitignore`"** (§ Corrections 1). **No task writes the
   narrow form**, including in a docstring or a § Errors row.
3. **Fixture F is built on EXCLUDED non-ASCII paths** (§ Corrections 4). A brief reading the design's
   Fixture F literally would build tracked ones and ship a blind mutation.
4. **Fixture D's bytes are `X` and its literal is `eec1541e…`** (§ Corrections 5). The design's
   `6ddb8634…` is not reproducible and no task may assert it.
5. **Fixture H carries no file under `templates/**`** (§ Corrections 6).
6. **The zero-file guard tests the LIST, never the digest** (§ Corrections 2).
7. **Nothing is minted to make the value change more visible.** A `provenance.hash_definition` key, a
   fourth hash, a `schema_version` bump and a `diff` row of its own are each **refused by ruling**
   (Decision 8), not merely unbuilt. No task proposes one, and Fixture M's key-set assertion is what makes
   a future attempt fail loudly.
8. **`parameters_hash`'s code does not change** (Decision 9). A task that finds itself editing
   `covered_config`'s body or `parameters_hash` has found a disagreement and must report it.
9. **`W-PARAM-UNSET` is a WARNING, and the core-schema half is FILED, not built** (Decision 10). Task 11
   builds the `parameters` half; task 12 files the other with its reason and **unassigned** ownership.
10. **`diff`'s `uv.lock` detail lines stay H9's** (Decision 12), and **`diff <config> <run>`'s
    recomputation is untouched** — a consequence of Ruling B, not a separate choice. No `diff` code
    changes in this slice.

---

## What could not be measured

- **Whether a tracked non-ASCII filename joins correctly on Linux or on a case-insensitive non-APFS
  filesystem.** Measured true on macOS/APFS with `core.precomposeunicode = true`. **§ Corrections 4
  removes the exposure** by building Fixture F on untracked, excluded paths, which never round-trip
  through the index — so the platform question no longer gates a fixture in this slice. Recorded because
  a future slice that hashes a *tracked* non-ASCII path will meet it.
- **`check-ignore`'s cost as a function of PATTERN count.** Measured against path count (53 → 12.1 ms;
  10,002 → 875 ms) with a four-pattern `.gitignore`. A repo with hundreds of patterns is unmeasured, and
  the fallback Decision 6 records is what a successor reaches for.
- **Whether any project in the wild carries a submodule under `src/**`.** Unknowable, which is why
  Decision 6's cost-if-wrong names the fallback rather than claiming there is none.
- **`W-PARAM-UNSET`'s blast radius under any shape other than Decision 10's.** Measured zero for one
  diagnostic at path `parameters`; task 11 step 6 states what invalidates it.
- **The nine configs' real behaviour**, because neither `growth_screen` nor `publishable-llm` exists to
  install. Task 13's *unknowable* is that, and the entry says so.

---

## What the design leaves undecidable, for the controller

1. **The exclude chain's machine-dependence** (§ Corrections 1). Task 1 discloses it in
   § How the three are computed and argues it is an existing property of the dirty gate being extended to
   the hash. **The alternative the controller may prefer is a filing** — *"`code_hash` can differ between
   two machines for an untracked, globally-excluded file"* — owned by nobody, since no remaining slice has
   this surface. This plan takes the disclosure because a filing without a sentence in the document
   leaves a reader of § How the three are computed with a claim the code no longer honours. **Either way,
   narrowing the chain with a flag is refused**: `--no-index` is measured wrong, and there is no flag that
   selects "root `.gitignore` only".
2. **The 875 ms** (§ Corrections 3). This plan rules it a **disclosure, not a blocker** — correctness
   outranks it and Decision 2's three failure modes are real. A controller who disagrees has Decision 6's
   recorded fallback and would be reopening Decision 2, which this plan does not do.
3. **Whether `code_hash_of` should instead be a memoizing closure in `provenance.py`**
   (§ Corrections 2). The extraction kills both the second subprocess **and** the second walk and costs
   one name in `hashes.py`; the closure kills only the subprocess and costs no name, and its cache key
   *is* the candidate list, so it is not the H7a state-at-the-wrong-moment proxy. This plan takes the
   extraction. **If the controller prefers the closure, task 3 loses `code_hash_of` and its identity
   test, task 5 keeps two calls, and task 8's guard moves back onto `hashed_files`' return — and the
   subprocess-count pin stays either way.**
4. **Whether Fixture N belongs in the guard pin as a seventh arm** rather than as task 7's own test. This
   plan makes it a test with a can-fail control, because the pin's arms are about literals that must not
   move and Fixture N is about a render that *should* say `DIFFERS`.

---

## Plan self-review

- **Every claim about the code was measured at `f8450f9`**, by reading the file or **running** the
  command, in a scratchpad git repository or against a copy of the repo with the warning wired. Twelve
  corrections, of which **six reshape a task** (1, 2, 4, 5, 6, 7) and one deletes a false sentence in a
  shipped test (8).
- **Every literal in every fixture was computed**, and the two the design supplied that could not be
  reproduced are corrected with what was run (`6ddb8634…` → `eec1541e…`) or restructured (Fixture F).
- **Every mutation has two branches that can differ, checked in advance.** Three are named blind **in
  advance** and each owes a stated replacement: mutation 1 (typing only → `mypy`, and the runtime
  property is mutation 2's), mutation 13 (two identical implementations → a reading obligation on the
  batch review), and task 8's digest-comparison mutant (mathematically identical → forbidden in the brief
  rather than tested).
- **At least one guard-pin arm has no authorized editor: three do** — A, C and D — and a passing arm
  after every task is the proof.
- **Every § Errors and § Warnings row covers every emit site**, and each new code's site count is stated
  as a number in its task: `E-CODE-EMPTY` one, `E-CODE-FILE-LIST` one, `W-PARAM-UNSET` one.
- **No task is unreviewed**, including the last, and batch 3 is the value change with a real-command
  review.
- **Nothing here reopens Decision 2 or Decision 9.**


---

## Controller rulings, 2026-08-22 — the four questions the plan handed up

### Ruling F — the exclude chain is narrowed to the repo's own committed rules, not disclosed as machine-dependent

**The plan is right that `git check-ignore` answers from git's whole exclude chain, and wrong that the
only options are *disclose* or *reopen Decision 2*.** A third exists and it is the direct question.

`code_hash` exists to make *same code, different parameters* provable **across machines and across time**.
An identity function that consults `core.excludesFile` is not that: two machines with identical trees and
different global git config compute different digests, and the record gives a reader no way to see why.
The dirty gate's machine-dependence is not a precedent — a gate answers *may this run proceed here*,
which is a local question by nature; a hash answers *is this the same code*, which is not.

**Measured, in a throwaway repo with a global exclude of `*.log` and a committed `.gitignore` of
`b.txt`:**

```
git check-ignore --stdin                                    → a.log, b.txt   (both)
GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null \
  git -c core.excludesFile= check-ignore --stdin            → b.txt          (the committed rule only)
```

**So: every `check-ignore` invocation in this slice runs with the global and system config neutralized.**
What remains is the repo's own committed rules — the root `.gitignore` and every per-directory one, both
of which travel with the tree — plus `.git/info/exclude`, which **no flag can disable** and which is the
one residue to disclose. That is a far smaller disclosure than the whole chain, and it names something a
reader can act on.

**Cost if wrong:** a project deliberately relying on a global exclude to keep something out of its hash
finds it hashed. That is the correct outcome under this ruling's own argument — a rule that does not
travel with the tree cannot define the tree's identity — and it is the reason the ruling is stated rather
than left to the implementer.

### Ruling G — the 875 ms at ten thousand paths is accepted and disclosed, not designed around

Correctness decided Decision 2 and cost does not reopen it. **Disclose the measurement** — `875 ms` versus
`19 ms` for the rejected `ls-files` shape at 10,002 paths, roughly twice the whole of `code_hash` — and
**file the scaling note with an owner that is a fact with a reason.** Pattern-count scaling is unmeasured;
say so rather than implying paths are the only axis. A research repo with ten thousand files under
`src/**` is outside anything this project has seen, and paying under a second there to answer the right
question on every ordinary repo is the trade this project makes everywhere else.

### Ruling H — take the `code_hash_of` extraction, not the memoizing closure

**Grounds beyond the plan's own:** the extraction kills the second **walk** as well as the subprocess, and
it leaves `E-CODE-FILE-LIST` with **one emit site.** *§ Errors carries one row per code covering every
emit site* is the shape that produced a whole-branch Major on two sub-slices, shipped twice in a third,
and was miscounted twice in the slice just merged. **A structural change that makes a code un-multipliable
is worth one name**, and a memoizing closure leaves the second site there for a later reader to find.

### Ruling I — Fixture N becomes the guard pin's seventh arm, with NO authorized editor

The claim it holds is *a `diff` across this boundary prints `code_hash DIFFERS` for identical code* —
the disclosure that `schema_version` deliberately does not carry. **That is precisely the claim a later
slice will want to soften**, because it reads like a defect and is a consequence. An arm with no
authorized editor is this repo's answer to five slices weakening a pin quietly: **a passing arm is the
proof.** As task 7's own test it would be editable by whoever next touches task 7's surface.
