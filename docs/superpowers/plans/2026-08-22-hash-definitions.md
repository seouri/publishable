# H6a — the two hash definitions — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to
> implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `code_hash` stops letting a file the repo's own git excludes move a published identity claim,
and a repo with no file to hash stops publishing the digest of nothing at exit 0. `parameters_hash`
computes exactly what it computes today — the charter's normalization clause is rejected with grounds,
§ How the three are computed's false sentence and its false justification are **deleted**, and what H6a
builds instead is the warning for the half that misleads: a template parameter the config omits, which
validates clean today and then kills every execution.

**H6a is not additive.** One published identity claim moves for an unchanged tree at an unchanged commit.
The argument is made in the open in the design's § The value change, re-measured by this plan
(§ Corrections 1, 3, 5, 6), and pinned with computed literals in task 2 before anything moves.

**H6a moves NO row of the four-row table and mints no fifth number.** Task 13 repeats it character for
character, per design Decision 14, which **derived** that rather than assuming it.

| Figure | Count | Visible to `validate`? |
|---|---|---|
| Transplantable configs validating with zero errors | **8 of 8** | yes — the only figure `validate` can see |
| Blocked on `io.reuse_from` | **0** | no — a step-level call; the method now ships, so this row's *parenthetical* ("unbuilt") is what went false, not the dependency: six configs (E3, E4, E6, C1, C2, C3) still need the plugin body to *call* it |
| Meet the `report_by`-under-`resample` gap | **7** | no — a construction chosen inside `summarize_step`; **H8a touches none of this** — it is H4 Statistics' gap, live on E1, E2, E4, E6, C1, C2, C3, and unmoved by anything this slice built |
| Free of every core-side dependency this analysis can name | **1** | no — E5, and only with the plugin written and installed |

**That table is reproduced here for a reader's convenience and is NOT this plan's source of truth for
it** — task 13 copies it from the feasibility analysis' own last entry and diffs against that.
Row 1 counts configs validating with zero **errors**; `W-PARAM-UNSET` is a warning and the two new codes
are errors raised by `command_run`, not by `validate`. Rows 2 and 3 name surfaces this slice does not
touch. Row 4 counts core-side dependencies; `code_hash` is computed for every run regardless of config,
so no config gains or loses one. **No task may write "N configs now execute" or mint a fifth number.**

**Architecture.** No new module, no new file of any kind. Two source files and four documents move.

- **`hashes.py`** — `hashed_files` and `code_hash` gain a **required, positional, batch** `include`
  parameter; the fold is extracted as `code_hash_of(pairs)` so a caller that already holds the file list
  does not walk twice (§ Corrections 2). The module docstring links the four-case table.
- **`provenance.py`** — the ignore helper: `git check-ignore -z --stdin`, `os.fsdecode`, tri-state
  returncode, `E-CODE-FILE-LIST`. It sits beside `git_provenance`, which already shells to git and
  already imports `HASHED_TREES`, and it **does not call `_git`**.
- **`cli.py`** — `command_run`'s single hashing site: build the predicate, take the file list once,
  refuse on zero files (`E-CODE-EMPTY`), fold.
- **`validate.py`** — `W-PARAM-UNSET` in `_check_parameters`, and one shared unset-and-defaulted helper
  read by both it and `_check_versions`.
- **`docs/reference.md`** — § How the three are computed (the four-case table, the deleted normalization
  sentence, the deleted false justification), § Templates: where parameters are defined, § Errors core
  raises, § Warnings core reports, § Validation, § Three hashes.
- **`docs/superpowers/spec-defects.md`** — three entries struck, one appended to, one new filing.
- **`docs/feasibility-llm-growth-studies.md`** — one appended § Executability entry.
- **`docs/superpowers/specs/2026-08-08-implementation-spine-design.md`** — one appended correction.
- **`CLAUDE.md`** — the slice entry and the order line.

**Tech stack:** Python ≥ 3.11, `pytest`, `ruff`, `mypy`. Tests land in existing modules —
`tests/test_hashes.py`, `tests/test_provenance.py`, `tests/test_cli.py`, `tests/test_validate.py`,
`tests/test_diff.py`. **No new file is created by any task**, so `ruff format --check` stays at 93 and
`mypy` at 52 source files.

**Spec:** `docs/superpowers/specs/2026-08-22-hash-definitions-design.md` — read it beside this plan,
including its § The value change, § The fixtures, § The mutations, § The guard pin, § The § Errors and
§ Warnings work, and § The records this slice owes. **Its body must not be edited.** Where this plan
measured something that contradicts it, the disagreement is in
[§ Corrections against the code](#corrections-against-the-code), appended by this plan's author and
extended by no task.

**Measurement this plan argues from:** `docs/superpowers/H6-SCOPING.md`, measured 2026-08-22 against
`da9907b` — **whose recommended implementation route the design already rejected with measurements, and
the design wins** (Decision 2); the design's own re-measurement at `560e3a8`; and this plan's
re-measurement against **`main` at `f8450f9`**. `git diff --stat da9907b f8450f9 -- src tests` was
**run** and prints nothing — so the code this plan measured is byte-identical to the code the scoping
measured, which is what licenses reusing its baseline while re-checking its claims. That was checked by
running the diff, not by reading four `docs:` commit-message prefixes, which would have been a correlate
standing in for the fact. Every signature, message, helper name and literal below was read or
**run** at `f8450f9`. **Nothing is cited by line number.**

**Baseline at `f8450f9`, and HOW each figure was obtained — because a task that reconciles against a
false provenance line is a task that stops for the wrong reason:**

- `uv run pytest --collect-only -q` → **2934 tests collected**, run in the real repo, foreground.
- `uv run pytest -q` → **2931 passed, 1 skipped, 2 xfailed** (2931 + 1 + 2 = 2934, so the collection
  matches). **This figure was produced in a scratchpad COPY of the repo, with `W-PARAM-UNSET` already
  patched in, under `-p no:randomly`, for § Corrections 7's blast-radius measurement** — not by a
  foreground run of `main` in this working tree. The patch adds **no test**, so the count is the
  baseline's; the honest statement is that the *count* is measured and the *run* was the corrections
  measurement. **Task 1's implementer re-confirms it with one foreground `uv run pytest -q` in this repo
  before committing, and reconciles any difference before proceeding.**
- `uv run ruff check .` → **All checks passed!** — run in the real repo, foreground.
- `uv run ruff format --check .` → **93 files already formatted** — run in the real repo, foreground.
- `uv run mypy` → **Success: no issues found in 52 source files** — run in the real repo, foreground.

**Task count: 13.** The design's 12 in its own grain and its own numbering, plus **task 13, the
§ Executability entry**, which the controller's hard requirement gives a task of its own. The addition
**appends** rather than renumbering, on H5a's, H5b's, H8a's, H8b's, H8c's and both H7d parts' precedent,
so the design's numbering stays citable. 13 tasks make 13 commits.

---

## Sequencing

**Execution order: 1 → 2 → 7 → 10 → 3 → 4 → 5 → 6 → 8 → 9 → 11 → 12 → 13.**
The design's order with task 13 appended. Each task restates the constraint it depends on in its own
text, because an implementer sees only their own task brief.

| Constraint | Why, and where it is enforced |
|---|---|
| **Task 2 before every code task** | H6a moves a published identity claim, and that is only pinnable against literals captured **before** anything moves. **Arms A, C and D have no authorized editor at all** |
| **Tasks 1, 7 and 10 before any code** | The documents lead. The four-case table is written before the code implements it, Ruling C's disclosure is written before the value moves, and Ruling B's two false sentences are deleted before anything could be read as depending on them |
| **3 before 4 and 5** | Without the production call site passing `None`, batch 2 does not typecheck. Task 3 is the seam; task 4 is what will fill it |
| **4 before 5** | Task 4 builds the predicate and its refusal; task 5 wires it. Landing 5 first would wire a name that does not exist |
| **5 before 6** | Task 6 asserts the hash and the dirty gate agree about an ignored-but-present file. That agreement does not exist until task 5 lands, so writing it first would pin today's disagreement |
| **8 after 5** | `E-CODE-EMPTY`'s second reachable situation — a repo whose whole `src/` is ignored — **is created by task 5**. Fixture H is unreachable before it |
| **9 after 8** | It re-runs guard-pin arm E over the finished refusal and reports the diff line count |
| **11 anywhere after 1** | `W-PARAM-UNSET` shares no file with the `code_hash` half. It is placed after the code half so its suite-wide render count is measured against a branch that already moved everything else it is going to move |
| **12, then 13** | Every filing and both consistency passes against the finished branch; the § Executability entry is appended last so its commit sha is the branch's |

**Two ordering facts, said once so neither reads as an omission.** **(i) The task sections below appear
in EXECUTION order, not numeric order** — 1, 2, 7, 10, 3, 4, 5, 6, 8, 9, 11, 12, 13 — which is the
design's own order with task 13 appended. H5b's plan, which this one copies its form from, happened to
have the two orders coincide; here they do not, and a controller looking for `## Task 3` in third
position should look fifth. `task-brief` extracts a section by its heading, so nothing depends on the
file order. **(ii) Both new § Errors rows land in task 8, two batches after `E-CODE-FILE-LIST`'s code
lands in task 4.** That is deliberate and it is the one place this slice does not lead with the document:
the row's content — *"an empty answer is not read as nothing-excluded"*, and the submodule as the
reachable instance — **is a description of the returncode behaviour task 4 establishes**, and writing it
first would be writing a row about a tri-state nobody had measured in code yet. The two rows are written
by one task so they have one shape, which is what *one row per code, covering every emit site* asks for.

### Three deviations from the design's grain, each argued

**(a) Task 13 exists at all.** The design folds the § Executability entry into task 12's record sweep.
The controller's requirement gives it a task, and the reason is in the record: the two wrong figures that
analysis has carried were both made by a slice that folded the entry into a sweep and repeated a phrase
without re-deriving it. **Task 12 is narrowed, not renumbered.**

**(b) Task 3 also extracts `code_hash_of(pairs)`.** § Corrections 2. Without it, task 8's guard forces a
**second** walk of the two trees and a **second** `git check-ignore` subprocess per run — measured at
233 ms and 875 ms respectively on a 10,002-file tree — and falsifies both Decision 4's *"the walk happens
once, in one place"* and `E-CODE-FILE-LIST`'s **one** emit site.

**(c) Task 7 gains a pin.** The controller requires the disclosure to have "its own task and its own
pin", and the design's six arms contain nothing that exercises the boundary. Task 7 builds two
hand-written `run.yaml` records — one carrying an old-definition digest, one a new-definition digest for
the same tree — and pins that `diff` prints `code_hash DIFFERS` for identical code.

---

## Batching — six batches, one report and one review each

**Every batch gets a review, including the last.** Twice a controller ran a slice's final batch straight
into the whole-branch gate, and the second time **three of four whole-branch Majors lived in it.**

| Batch | Tasks | The seam, and what its review must be able to see |
|---|---|---|
| **B1 — the rulings, the documents, the pin** | **1, 2, 7, 10** | Does the four-case table exist in **one** place, and does every other site **link** rather than restate? A four-case rule invites a two-case sentence; H5b shipped one in five files. Does the table's *ignored* row name **git's whole exclude chain** rather than `.gitignore` alone (§ Corrections 1)? Does any new sentence claim behaviour the code will not have after B3? Does the pin have a named sole editor per arm, **three arms with none**, and are arm B's two moving literals and arm D's after-value written down **now**? Were § How the three are computed's two false clauses **deleted** rather than rewritten, and were **all** their homes swept newline-insensitively (§ Corrections 12)? Mechanical pass on every `reference.md` edit |
| **B2 — the seam** | **3, 4** | Is `include` **required** and positional, and does `mypy` pass? Is `code_hash(repo, include) == code_hash_of(hashed_files(repo, include))` asserted by a test rather than by a comment? Does the helper check the **returncode** rather than stdout, pass `-z` on both ends, decode with `os.fsdecode`, and **not call `provenance._git`**? Does Fixture F use **ignored** non-ASCII paths (§ Corrections 4), and does its mutation actually change the digest? Arm E's `git diff` line count **reported**, every changed line a call and not an assert |
| **B3 — THE VALUE CHANGE** | **5, 6** | **A real-command review**: run the installed console script end to end on Fixtures A, B, D and J's projects and read `run.yaml` **key by key** against § The value change's tables — not `validate`, not a direct call. Is arm B's edit **exactly** the two enumerated literals, with the other seven present figures untouched? Does Fixture M's record carry **two** digests, and does its assertion name the record's top-level key set rather than merely asserting a marker's absence? Is arm A still passing, unedited? Is arm D still green **without** an edit? Was the duplicated `__pycache__` pin replaced by a test that can fail, and was **that** demonstrated by mutation rather than asserted? Is `git check-ignore` invoked **once** per `run` (§ Corrections 2), asserted by counting? |
| **B4 — the zero-file refusal** | **8, 9** | Is there exactly **one** emit site, and does the § Errors row cover **both** reachable situations? Does Fixture G assert that **no run directory** was created, not only the exit code? Does Fixture H carry **no file under `templates/**`** (§ Corrections 6)? Was the zero-file guard written as `not pairs` rather than as a comparison against the empty digest (§ Corrections 2, the rejected one-liner)? Was the stale H1 owner line corrected **before** the entry was struck? |
| **B5 — the parameters half** | **11** | Is the boundary stated — `parameters` block only, core-schema half filed **unassigned with the reason**? Is Fixture K's control arm present and can it fail? Is arm F byte-unchanged? **Report the suite-wide count** of tests whose render changed and, for each, whether the assertion was *updated* or *loosened* — this plan measured **zero** (§ Corrections 7) and a non-zero result is a disagreement to report, not to absorb. Was the false docstring clause **deleted** (§ Corrections 8), and is that edit stated as sitting **outside** arm F? |
| **B6 — the records** | **12, 13** | **A full review, not a skim.** Every struck entry checked against the code; every "filed" checked against the file; every re-owning stated as a fact with a reason and never as *"whichever slice next touches X"*; the spine correction **appended** rather than edited; every sweep **naming its files**, never filtering its output, **newline-insensitive**, and **proven able to fail**. And: the four-row table repeated **character for character**, no fifth number |

---

## Global Constraints

Every task inherits all of these. They are copied verbatim rather than cross-referenced, because an
implementer sees only their own task brief.

**Commands.** Tests `uv run pytest`. Lint `uv run ruff check .`. Format `uv run ruff format .`. Types
`uv run mypy`. All four must pass before a commit. **Baseline at `f8450f9`: 2931 passed, 1 skipped, 2
xfailed; 93 files formatted; 52 source files typed.**

**No gate literal moves in this slice.** No task creates a file of any kind, so `ruff format --check`
stays **93** and `mypy` stays **52 source files** at every commit. **Every task states its own DELTA on
the test count, not an absolute**; compute the absolute from your own previous run and reconcile any
difference before committing. **Task 6 is the one task with a negative component** — it removes one
duplicated test — and states its delta as *added minus removed*, naming the removed test.

**Run `uv run pytest` DIRECTLY, in the foreground, and wait for it.** It takes about three and a half
minutes at this baseline. **Never construct a wait, a monitor, a poll or a background run around it** —
six agents on preceding slices stalled that way and one stopped with a mutation still applied. Clear
`__pycache__` and any stale `pytest-of-*` temp directory before a run.

**Verify format with `uv run ruff format --check .`, never the bare form.** A previous brief in this repo
wrote the bare form where it meant `--check` and rewrote 67 files. **`ruff format` does not process
`.md`** — measured twice on preceding branches by copying a document, running the formatter and diffing
byte-identical; two agents nonetheless reverted documents on that misdiagnosis. **A revert is verified by
behaviour**, never by `git status`, and least of all by an account of what caused the change.
**`git checkout -- <file>` destroys uncommitted work** and has been mistaken for reverting a mutation
three times here. Keep a copy before mutating; restore by copying back; verify by behaviour.

**Every probe project lives under the session scratchpad**, is a real `git init` repository with at least
one commit, and re-asserts its baseline digest after every perturbation. A digest quoted in a report that
was not produced by running something is a finding.

**The exclude chain, not `.gitignore` alone.** `git check-ignore` answers from the root `.gitignore`,
**every per-directory `.gitignore`**, **`.git/info/exclude`**, and the user's **`core.excludesFile`** —
all four measured (§ Corrections 1). Every sentence any task writes about this rule says *git's exclude
rules* or enumerates the four; **no task writes "`.gitignore`" as the whole rule**, and the four-case
table's *ignored* row is where the enumeration lives once.

**`hashes.py` is not shelling to git and no task may make it.** 13 `code_hash(` call sites in
`tests/test_hashes.py` run against a bare `tmp_path` with **no repository** (`grep -c "git init\|
subprocess" tests/test_hashes.py` → 0). That testability property, not the spine's unqualified purity
sentence, is what forces the injected predicate — the sentence is already false of the shipped module,
which rglobs, reads bytes and carries `_SKIP_DIRS`.

**Mutation numbers: the design's are 1–14 and this plan does not renumber them; the two this plan adds
are `P1` and `P2`.** Briefs cite mutation numbers across task boundaries, so two tasks calling two
different things "mutation 10" would produce two reports claiming the same pin. **P1** is task 8's
empty-digest-comparison mutant (blind, and forbidden in the brief for that reason); **P2** is task 5's
subprocess-count mutant. Every other number in this plan is the design's own.

**One row per code, covering every emit site.** That shape was the whole-branch Major on two of H8's
sub-slices, shipped twice inside a third, and miscounted twice in H5b. A diagnostic's unit of work is
every site that raises *or* reports it, not every helper it calls.

**Answer the question, not a correlate.** Decision 2 exists because `git ls-files` answers *which paths
does git list* where the rule asks *which paths does git ignore*. The same fault in another currency is
`pop(0)` for *which entry did I add?*, and a **reserved name** standing in for a structural fact. Two
concrete instances are forbidden by name in this slice: the ignore helper must not call
`provenance._git` (whose `check=False` + `strip()` turns rc 128 into an empty string indistinguishable
from *nothing is ignored*), and the zero-file guard must not be written as a comparison against the
empty digest (§ Corrections 2).

**A safety argument in a comment is a claim.** If a comment says *this cannot happen*, make it happen.
**Prefer deleting a claim to rewriting it.** **The sibling that already got it right is the first place
to look — and copy where it sits, not only what it calls**: `provenance.py`'s `E-GIT-NO-COMMIT` block is
the precedent for refusing at a call site where an empty answer has no honest reading, and it is the
containment as much as the call.

**What this slice does NOT touch, stated so no task folds it in** (on H4b-2's precedent):

- **`diff`'s `uv.lock` detail lines naming the moved package.** Filed against **H9** by H5b, re-affirmed
  in writing by design Decision 12. **Not folded in.** `diff`'s `parameters_hash` row prints per-key
  detail because `diff` reads two embedded configs; `uv.lock`'s row has two digests because a run
  archives the lockfile and the record carries only its hash. Producing a per-package delta means ruling
  on what a moved pin means, which is the question H9's charter is defined by.
- **`diff <config> <run>`'s recomputation.** `diff.py` imports `hashes.parameters_hash` as
  `_compute_parameters_hash` and calls it for a **config**-side operand only (§ Corrections 9). Because
  Ruling B changes nothing about what `parameters_hash` computes, **`diff <config> <run>` returns exactly
  the verdicts it returns today for every run already on disk**, and no task may move one. Had Ruling B
  gone the other way it would have moved published verdicts on the day it landed; that is an argument
  that was **used**, not one that became moot.
- **A dirty-tree or empty-tree check at `validate`.** H6b task 18 (Decision 15). `validate` walks no tree
  and shells to no git today (`grep -rn "dirty" src/publishable/validate.py` → 0 hits), and adding one
  here would mint a `W-` seat against a section H6b is rewriting.
- **`E-CODE-DIRTY`'s missing § Errors row, and `E-GIT-NO-REPO`/`E-GIT-NO-COMMIT`'s.** H6b task 17, gated
  on the spine owner's ruling about widening this charter to the nine undocumented codes. **H6a mints
  rows for its own two new codes and touches no other.**
- **`provenance.environment.os`/`.hostname`/`.hardware`.** H6b tasks 13–16. H6a writes no environment key.
- **`BaseTemplate.field_convention`**, declarable on a shipped class and read by nothing — § Misreadings'
  sole remaining example of an unbuilt reader of a shipped surface. An implementer reading
  `templates/builtin/generic.py` will meet it. **Not H6a's**, owned by nobody.
- **The `report_by`-under-`resample` gap.** Row 3 of the four-row table, live on seven configs,
  unassigned. Nothing here touches `stats.py`.

**No positional row locators, no line-number citations, no count phrases where an enumeration is
possible.** Cite a document by section. Name what a sibling table row *does*. `×`, not `x`, for
multiplication. Hyphens, never en dashes, in anything that becomes an anchor.

---

## The fixtures this slice rests on, and where each one lives

**A fixture is a claim too**: every literal below was computed by **running** the shipped `code_hash` for
a *today* column and this plan's Decision 2 predicate for an *after* column, in a scratchpad git
repository built for it. Six fixtures in one earlier slice failed their own constraints, one asserting
the very value it existed to reject.

**The base tree, used by A–F and referred to as "the base tree" in every task below.** A committed
repository whose `.gitignore` holds the scaffold's four patterns —

```
.env
__pycache__/
*.py[cod]
.venv/
```

— with `src/pkg/step.py` = `a = 1\n` and `templates/t.py` = `b = 2\n`, and nothing else under either
tree. `code_hash` of that tree, **today and after**, is
`sha256:71bf339cc9463f4c776c711f3d65ccf9b3bc1e18d383b78ae7d4e5170b526c2b`. Every other fixture states its
perturbation and its own two digests.

| Fixture | The claim, with its literals | Task |
|---|---|---|
| **A** — the ordinary path does not move | The base tree hashes to `71bf339c…` before and after | **2** (arm A) and **5** |
| **B** — the credentials case | Base tree + untracked `src/pkg/.env` = `OPENAI_API_KEY=sk-live-1\n`. Today `sha256:ebc5ee53ac39bbab63d5270475271068dc67e6f34ead9db648bad114845b1cce`; after **`71bf339c…`, equal to A's** | **2** (arm B) and **5** |
| **C** — the other two unhonoured patterns | Base tree + untracked `src/.venv/lib/site.py` = `s = 3\n`, `src/pkg/loose.pyd` = `X` (one byte, no newline), `src/pkg/.env` as in B. Today `sha256:1947d2a21da33a9c6e4b3a45448ae11ac89e0399797c53168569a297a3f46bcf`; after **`71bf339c…`**. `check-ignore` returns rc **0** naming exactly those three | **5** |
| **D** — a **tracked** file matching an ignore pattern is still hashed | Base tree + `src/pkg/loose.pyd` = `X`, committed with `git add -f`. `check-ignore` reports **no match** (rc 1). After: `sha256:eec1541edde45c11c395e788000f719a48965a8f6fd2b3772a56de92cca18dc2` — **different from A's**, which is the whole assertion | **2** (arm D) and **5** |
| **D′** — the coincidence a fixture must not rest on | The same `.pyd` **untracked**: today also `eec1541e…`, after `71bf339c…`. The *today* column cannot tell tracked from untracked, so **D asserts the after value** | **5** |
| **E** — the fixed skip set survives, tracked or not | D's tree + `src/pkg/__pycache__/keep.py` = `k = 1\n`, `git add -f`-ed. git reports it **not ignored** (rc 1); the digest stays `eec1541e…` — unmoved. The positive control for § Templates' *"unconditionally"* | **2** (arm D) and **6** |
| **F** — the `-z` claim, on **ignored** non-ASCII paths | Base tree with `*.env` appended to `.gitignore`, plus untracked `src/pkg/naïve.env` = `K=1\n` and `src/pkg/ünï.pyd` = `x\n`. Today `sha256:06604d0ca69e38499035c0a2f20a27534aecf675c22739e38fd3690a9e7e6e0d`; after **`71bf339c…`**. Dropping `-z` leaves the digest at `06604d0c…` — measured (§ Corrections 4) | **4** |
| **G** — the zero-file refusal, end to end | A committed repo with an **empty** `src/`, no `templates/`, and an entrypoint importable from a `PYTHONPATH` directory outside both trees. Today: a completed run at exit 0 with `code_hash: sha256:e3b0c442…` in its `run_id`. After: exit 1, `E-CODE-EMPTY`, **no run directory** | **8** |
| **H** — the zero-file case task 5 creates | A committed repo whose `.gitignore` is `src/`, whose `src/pkg/step.py` is untracked, **and which holds no file under `templates/**`**. Measured: `git status --porcelain -- src templates` prints **nothing**; today `sha256:f6a935cfc29196b2a5f5a7f873096c4ab3ee077ff3152afedafeb34fb919078a`; after **zero hashed files**. **With `templates/t.py` present the after digest is `sha256:ef36e0c97881b4541db22e03def3912ed01059e4fdeeb739079b1244554f62c7` and the refusal never fires** (§ Corrections 6) | **8** |
| **I** — the submodule refusal | A host repo with `src/pkg/step.py` and `src/vendor` added as a submodule holding `lib/z.py`. Measured: `check-ignore` exits **128** with `fatal: Pathspec 'src/vendor/lib/z.py' is in submodule 'src/vendor'`; `hashed_files` finds `src/pkg/step.py`, `src/vendor/lib/z.py`, `templates/t.py`. The claim: `run` refuses with `E-CODE-FILE-LIST` and the message contains `src/vendor` | **4** |
| **J** — hash and gate agree on the ignored-but-present file | One test, two assertions on B's tree: `git_provenance(...).code_dirty is False` **and** the file is absent from `hashed_files`' output | **6** |
| **K** — `W-PARAM-UNSET` fires, with its control | Two configs against `generic`: one omitting `analysis.confidence` and `analysis.drop_missing` (one diagnostic naming **both**, exit 0, `has_errors` False), one setting all four (**no** warning) | **11** |
| **L** — the two negative controls still hold | `code_hash(tmp_path / "nonexistent_empty_repo", None)` still returns `sha256:e3b0c442…`; the guard did **not** migrate into `hashes.py`. Not a new fixture — it is the two existing tests | **2** (arm E) and **9** |
| **M** — one record carrying two hash definitions | A hand-written pre-H6a `run.yaml` whose `code_hash` is `ebc5ee53…`, consumed through `io.reuse_from` by a post-change run over the base tree. The new record's own `code_hash` is `71bf339c…`, `provenance.upstream[0].code_hash` is `ebc5ee53…` **copied verbatim**, and **no key distinguishes them** | **5** |
| **N** — `diff` across the boundary | Two hand-written `run.yaml` records for the same tree at the same commit, one carrying `ebc5ee53…` and one `71bf339c…`. `diff` prints `code_hash DIFFERS` at exit 0 for **identical code** | **7** |

---

## Task 1: Ruling A written into the documents, and the four-case table

**Surface: documents only.** No code, no test.

**Files:** `docs/reference.md`.

**The ruling.** § How the three are computed wins. `code_hash` becomes aware of git's exclude rules, and
§ Templates' *"an ignore file has no bearing on"* clause narrows to the **dirty gate**, which is the
question that sentence is actually about. The grounds are the design's Decision 1 and are not re-argued
here: the defect is that the dirty gate consults git and the hash does not, so one mechanism says
*nothing changed* while the other says *the code moved*, and the warning that fires downstream
(`W-STUDY-CODE-HASH-MISMATCH`) names three candidate causes, **none of which is this one**.

**§ Corrections 1 binds this task and reshapes what it writes.** `git check-ignore` answers from **git's
whole exclude chain**, measured in a scratchpad repo: the root `.gitignore`, a **per-directory**
`.gitignore` (`src/sub/.gitignore` holding `perdir.py`), **`.git/info/exclude`**, and the user's
**`core.excludesFile`** — a single call reported all three of `src/pkg/globignored.py`,
`src/pkg/infoexcluded.py` and `src/sub/perdir.py` as ignored. **A table row that says "`.gitignore`"
while the code means "any of git's four exclude sources" is a row narrower than its code**, which is the
shape that was the whole-branch Major on two of H8's sub-slices.

- [ ] **Step 1: add the four-case table to § How the three are computed, and enumerate the rule ONCE.**
      The design's Decision 3 is explicit that a four-case rule invites a two-case sentence at every site
      that mentions it — H5b shipped one in five files. So the table lives in exactly one place and every
      other site **links to its anchor**.

| A file under `src/**` or `templates/**` is | Hashed? |
|---|---|
| in the fixed skip set (`__pycache__`, `.git`, `.ruff_cache`, `.mypy_cache`, `.pytest_cache` as a path component; suffix `.pyc`/`.pyo`) | **no**, whatever git says — including when it is tracked |
| tracked | **yes**, even when it matches an exclude pattern |
| untracked and not excluded | **yes** |
| excluded by any of git's exclude sources — the repo's `.gitignore` files at any depth, `.git/info/exclude`, and the user's `core.excludesFile` | **no** |

- [ ] **Step 2: amend the sentence that states the rule.** § How the three are computed says `code_hash`
      is *"taken from the working tree and skipping whatever `.gitignore` skips."* It stays taken from
      the working tree; what it skips is stated by the table and the sentence links to it. **Do not
      write a second prose statement of the four cases beside the table.**
- [ ] **Step 3: disclose the machine-dependence, in § How the three are computed, beside the table.**
      Because the chain includes a **user-level** excludes file, an untracked file under the two trees
      can be excluded on one machine and not on another. The section's own opening argues *"A hash that
      two machines compute differently is not an identity claim."* The honest statement, which is the one
      to write: **the dirty gate already has exactly this property today** — `git status --porcelain --
      src templates` consults the same chain — so this ruling **extends an existing behaviour to the
      hash** rather than inventing one, and the two mechanisms agreeing is the whole point of Decision 1.
      A file whose hashing status you need to be machine-independent is a file you **commit**. **This
      paragraph is a disclosure, not a reopening of Decision 2**; no task may propose a flag that
      narrows the chain.
- [ ] **Step 4: narrow § Templates' clause to the dirty gate.** Both clauses live in one paragraph of
      § Templates: where parameters are defined — the one that says `code_hash` *"skips `__pycache__`
      directories and compiled `.pyc`/`.pyo` files unconditionally … so no ignore file could have done
      that for it"* and, later, that a hand-assembled repo's *"`code_hash` is unchanged, that being the
      mechanism an ignore file has no bearing on."* The first is **true and stays** — it is the fixed
      skip set, applied first — and gains a link to the table. The second is **narrowed to the dirty
      gate**, which is what that sentence is about. **Do not touch its *"goes dirty at `validate`"*
      clause**: it describes behaviour that does not exist and it is **H6b task 18's**, named here so its
      survival is not read as this task's omission.
- [ ] **Step 5: link, do not restate, at every other site that mentions the rule.** § Three hashes' table
      row for `code_hash`; § Warnings core reports' `W-STUDY-CODE-HASH-MISMATCH` row, which gains **one
      link and nothing else** — its three candidate causes stay three, because Decision 1 makes the
      fourth cause *disappear* rather than need naming.
- [ ] **Step 6: mechanical pass on every edit.** Every relative link and `#anchor` resolves; no two
      headings produce the same anchor; the new table's rows match its header's column count; no trailing
      whitespace, tab or invisible unicode; `×` not `x`; hyphens, never en dashes, in anything that
      becomes an anchor. Skip fenced blocks.

**What this task must NOT touch.** Any code. Any test. `E-CODE-DIRTY`'s absent § Errors row (H6b task
17). § How the three are computed's **normalization** sentence and its false `diff` justification — those
are **task 10's**, and two tasks editing one paragraph in one batch is how a sweep stops one file short.

**Guard-pin arms this task may edit: NONE.** The pin is captured by task 2 in the same batch; if this
task lands first, arm capture happens after it and the arms are unaffected because this task changes no
behaviour.

---

## Task 2: the guard pin — six arms, captured before anything moves

**Runs before every code task. Surface: direct calls to `hashes.code_hash` for arms A, C, D and E; a real
`run` through `main` for arms A and B's `run_id` halves; `validate` through a `Collector` for arm F.**

**Three arms have no authorized editor at all, so a passing arm is itself the proof.** This device is the
answer to five slices weakening a pin quietly, and to the two that pinned one list twice and edited both.

**Files:** `tests/test_hashes.py` (add), `tests/test_cli.py` (add), `tests/test_validate.py` (add).

| Arm | The claim | Sole authorized editor | State specified in advance |
|---|---|---|---|
| **A** | The base tree — no excluded file under either tree — hashes to `sha256:71bf339cc9463f4c776c711f3d65ccf9b3bc1e18d383b78ae7d4e5170b526c2b`, and an end-to-end `run` over it produces a `run_id` ending `_71bf339` | **NONE** | unchanged, byte for byte |
| **B** | The base tree plus a git-excluded `src/pkg/.env` hashes to `sha256:ebc5ee53ac39bbab63d5270475271068dc67e6f34ead9db648bad114845b1cce` and its `run_id` ends `_ebc5ee5` | **task 5 only** | **exactly two literals move**, both written now: `ebc5ee53…` → `71bf339c…` and `_ebc5ee5` → `_71bf339` |
| **C** | The **other seven present figures** a record carries are unmoved for arm B's project, asserted as literals: `parameters_hash`, `input_manifest_hash`, the per-file digests in `manifest/input.json`, `uv_lock_hash`, `units_hash`, `allocation_hash`, `design_digest` | **NONE** | zero lines changed. This is the arm that makes *"exactly one hash moves"* a pin rather than a sentence |
| **D** | Fixtures D and E: a tracked `.pyd` matching `*.py[cod]` is hashed, and a tracked file inside `__pycache__` is not — both asserted on the **after** value `sha256:eec1541edde45c11c395e788000f719a48965a8f6fd2b3772a56de92cca18dc2`, which is also their today value | **NONE** | unchanged. A passing arm after task 5 **is** the proof; there is no editor who could make it pass another way |
| **E** | `tests/test_hashes.py`'s two negative controls still resolve `code_hash` of a nonexistent directory to `sha256:e3b0c442…` | **task 3 only** | task 3 adds the literal `None` argument to **13** call sites and changes **no assertion** |
| **F** | `W-TEMPLATE-VERSION`'s full message string, including its unset-and-defaulted clause | **task 11 only** | **zero characters change** |

- [ ] **Step 1: capture arm A. NO AUTHORIZED EDITOR.** Build the base tree in a `tmp_path` git repository
      and assert `code_hash(base) == "sha256:71bf339c…"` (the full 64 hex characters, written out). Then
      run the same tree end to end through `main(["run", …])` and assert the run directory's name ends
      `_71bf339`. **State in the docstring that a task which finds this arm failing has found the
      ordinary path moving, which this slice says it does not** — the response is to stop, not to edit
      the literal.
- [ ] **Step 2: capture arm B, with its two moving literals named IN THE DOCSTRING.** Same tree plus
      untracked `src/pkg/.env` = `OPENAI_API_KEY=sk-live-1\n`. Assert `ebc5ee53…` and a `run_id` ending
      `_ebc5ee5`. The docstring says: **task 5 is the sole editor, exactly two literals move, and they
      are `ebc5ee53…` → `71bf339c…` and `_ebc5ee5` → `_71bf339`. An edit to anything else in this arm is
      a finding.**
- [ ] **Step 3: capture arm C — the seven unmoved present figures, as literals. NO AUTHORIZED EDITOR.**
      Read them off arm B's real `run.yaml` and `manifest/input.json` and assert each. **Three of the ten
      figures § The value change enumerates are ABSENCES on this project** — `apparatus.hash` (no probe
      is declared under `generic`), the copied upstream `code_hash`/`parameters_hash` (no `io.reuse_from`
      here), and the derived seeds (never published as digests) — so they are **deliberately not in this
      arm**: *a control asserting only absences passes identically if nothing ran.* Say so in the
      docstring and name Fixture M as what covers the upstream pair.
      **Say explicitly that arm B carries NO copy of these seven figures.** The design puts them in arm B
      *and* arm C; this plan puts them in **C only**, so **no list is pinned twice** and task 5 — arm B's
      sole editor — has nothing of arm C's to edit. Two slices pinned one list twice and edited both;
      this is the answer to that, and it is stated rather than left as a silent shrinkage a reviewer
      diffing against the design would query.
- [ ] **Step 4: capture arm D. NO AUTHORIZED EDITOR.** Fixture D's tree and Fixture E's tree, both
      asserted at `eec1541e…`. **The docstring states the coincidence and why the arm is built on the
      after value**: the untracked-`.pyd` tree has the *same* today value, so an assertion on the today
      column would pass under a mutation that drops tracked files too.
- [ ] **Step 5: capture arm E.** Assert that `hashes.code_hash` of a directory that does not exist
      returns `sha256:e3b0c442…`, as a standalone claim, and name the two existing tests that depend on
      it as negative controls: `test_code_hash_skip_list_matches_relative_path_not_absolute` and
      `test_code_hash_handles_a_dot_git_intermediate_path_component`. **Task 3 is the sole editor and its
      only edit is adding `None` to 13 call sites.**
- [ ] **Step 6: capture arm F.** Assert `W-TEMPLATE-VERSION`'s **full message string** for a config that
      declares a moved `template_version` and omits `analysis.confidence`. The docstring states that
      **task 11 is the sole editor and zero characters change** — task 11 extracts a comprehension into a
      shared helper, and if the message moves, the extraction was not behaviour-preserving.
- [ ] **Step 7: grep before claiming.** Before writing *"no existing test asserts X"* for any arm, grep
      for it and **report what you grepped, not a count**. `run.yaml`'s top-level and `provenance` key
      lists are already asserted somewhere in the suite; find those assertions and say so rather than
      duplicating them. Six consecutive slices reported zero disagreements and all six were wrong, and
      every one hid in a claim about **other** tests.

**Delta:** +6 tests (one per arm; arms A and B each carry their direct-call and end-to-end halves in one
test).

**What this task must NOT touch.** Any file under `src/`. Any existing test. Any document.

---

## Task 7: Ruling C written — no marker, `uv.lock` is the carrier — and the boundary pinned

**Surface: documents, plus one pin over two hand-written records through the shipped `diff`.**

**Files:** `docs/reference.md`, `tests/test_diff.py` (add).

**The ruling, and it is not re-argued here.** Nothing is minted to mark which definition produced a
record's `code_hash`, and `run.yaml`'s `schema_version` is **not** bumped. `run_record.SCHEMA_VERSION`
is `"1.0"` and `lineage.read_record_file` **refuses** any other value, so bumping it would make
`io.reuse_from` refuse **every record already on disk** — strictly worse than an unmarked value change.
The carrier that already exists is `uv.lock`: core's own version is pinned there, which is precisely why
`code_hash` covers only the repo's two trees, and `provenance.environment.uv_lock_hash` is written by
`cli.py` and read by `diff.py`'s `uv.lock` row. This is the ruling H5b shipped under, on the same
carrier.

**Because nothing is minted, the disclosure obligation is HEAVIER, not lighter.** This task discharges
it in the documents; task 12 discharges it in `CLAUDE.md` and the ledger.

- [ ] **Step 1: enumerate, in § How the three are computed beside the four-case table, every hash whose
      value moves and every record field that carries it.** **Exactly one hash moves: `code_hash`.** The
      other ten figures a record carries are unmoved, and they are **enumerated rather than counted** so
      a reviewer can check them: `parameters_hash`, `input_manifest_hash`, the per-file `sha256`s in
      `manifest/input.json`, `uv_lock_hash`, `units_hash`, `allocation_hash`, `apparatus.hash`,
      `design_digest`, the copied upstream `parameters_hash`, and every derived seed. **Ruling B is what
      keeps that list at ten.**

| Field carrying the moved hash | Where |
|---|---|
| `code_hash` | `run.yaml`, top level (`run_record.py`) |
| `run_id` | `run.yaml`, and the run **directory's name** — `allocate_run_dir` uses `short(code_hash)`, the first 7 hex characters |
| `provenance.upstream[].code_hash` | `lineage.py`, **copied** from an upstream record, so one record can carry two definitions |
| the bundled copy of each of the above | `study add` copies a run's `run.yaml` into `runs/<name>/` verbatim |
| the `latest` pointer's target | `point_latest`, which names the run directory |

- [ ] **Step 2: state the consequence plainly, in the document, in the words a reader needs.**
      **Two runs of the same config over the same data at the same commit, on either side of this
      change, publish different `code_hash` values and different `run_id`s whenever the repo carries an
      excluded file under the two trees — which the scaffold's own `.gitignore` makes the common case.
      `diff` prints `code_hash DIFFERS` for identical code.** `report study.yaml` over a bundle spanning
      the boundary prints `W-STUDY-CODE-HASH-MISMATCH`, whose message names three candidate causes and
      **will still name three, none of which is a build boundary** — the row is not widened, because
      widening it would document a transient. The carrier is `uv.lock`, and the honest statement is
      H5b's: **the change is visible as a dependency change and is not visible as a hash-definition
      change.**
- [ ] **Step 3: state Ruling C's sharpest cost, which is this ruling's specifically.** A post-change run
      that consumes a pre-change upstream through `io.reuse_from` publishes **one record carrying two
      hash definitions** — its own under the new rule and `provenance.upstream[].code_hash` copied
      verbatim from the old one — **with nothing marking which is which.** Stated, not mitigated.
- [ ] **Step 4: build Fixture N, the pin the controller requires. Do NOT hand-write two records from
      scratch.** `tests/test_diff.py` already imports `run_a_project` from `tests/test_cli.py` and calls
      **`command_diff(run_a, run_b)`** directly on two run directories — that is this fixture's shape.
      Produce one real run, copy its directory, and edit the copy's `run.yaml` so the pair is identical
      in every field except `code_hash` — one `ebc5ee53…`, one `71bf339c…` — with each `run_id`'s suffix
      matching its own digest. Then call `command_diff` over the pair and assert the rendered output contains `code_hash` and `DIFFERS` on
      the same row and that the exit code is **0** (`diff` exits 0 on every comparison it renders, 1 only
      when an operand cannot be read). **The docstring says what the test is for in one sentence: this is
      what a reader sees across the H6a boundary for identical code, and it is the cost Ruling C accepts
      rather than a defect to fix.**
- [ ] **Step 5: the can-fail control.** A second pair of records identical in `code_hash` must print
      `identical` on that row. Without it the assertion passes on any render that happens to contain the
      word.
- [ ] **Step 6: mechanical pass** on every `reference.md` edit, as task 1's step 6 specifies.

**Delta:** +2 tests.

**What this task must NOT touch.** Any file under `src/`. `diff`'s code — **no `diff` code changes in
this slice**. `W-STUDY-CODE-HASH-MISMATCH`'s three candidate causes. The `uv.lock` row's detail lines,
which are **H9's** and are re-affirmed as H9's in writing by design Decision 12.

**Guard-pin arms this task may edit: NONE.**

---

## Task 10: Ruling B written into the documents — two false sentences DELETED

**Surface: documents only, plus one docstring under `src/` that quotes one of them.**

**Files:** `docs/reference.md`, `src/publishable/hashes.py` (the `covered_config` docstring only).

**The ruling.** `parameters_hash` is **not** normalized. The charter's second clause —
*"`parameters_hash` normalization against `parameter_spec`"* — is **rejected**, not narrowed. Three
grounds, each independently sufficient, and none of them is re-derived by this task:

1. **`parameter_spec` cannot reach the gap.** Of the nine omissions the scoping measured moving the hash,
   **eight are core-schema keys**, and core-schema defaults exist **nowhere as data** —
   `materialize.materialize_config` emits them as literal text lines, and only the `parameters` block is
   generated from `parameter_spec`. Normalizing "against `parameter_spec`" reaches **one** of nine.
2. **Reaching the other eight needs a structure the invariants forbid by name** — *"there is deliberately
   no separate defaults file"*, stated normatively in § There is no separate defaults file.
3. **Normalizing the `parameters` half would be actively wrong.** An omitted `parameter_spec` default
   validates clean and then the step that reads it dies with `E-STEP-PARAM-UNKNOWN`, every execution
   `failed`. Normalizing would hand **one identity claim to a config that runs and a config that
   cannot** — the opposite of what an identity claim is for.

- [ ] **Step 1: DELETE the normalization sentence.** In § How the three are computed, the clause
      *"Values are normalized to what `init` would have materialized before hashing — an omitted
      `cluster_by` and an explicit `cluster_by: null` are the same declaration, and a config that omits a
      defaulted key hashes identically to one that spells it out"* is **deleted**, not softened.
      **Prefer deleting a claim to rewriting it**: a rewrite invents, a deletion cannot. A round that
      closed a false-owner comment by *propagating* the claim to two more sites is the precedent for why.
- [ ] **Step 2: DELETE its justification, which is false against the shipped command.** The following
      sentence argues *"Without that rule, a hand-trimmed config and the file `init` wrote would disagree
      about parameters that are equal, and `diff` would report a difference with nothing to print."*
      `diff` prints exactly the right thing —

      ```
      parameters_hash    DIFFERS
        data.units.cluster_by  null → (absent)
      ```

      — so the justification is false, and it goes with the claim.
- [ ] **Step 3: leave the subtractive rule standing and add ONE honest sentence.** § How the three are
      computed already states the rule two paragraphs later — *"everything in the config except
      `metadata` and `data.input_dir`/`data.output_dir`"* — and it is correct. What replaces the deleted
      pair is one sentence naming the consequence honestly: **a hand-trimmed config and the file `init`
      wrote are two declarations, they hash differently, and `diff` names the key that differs.** Do not
      write a second statement of the coverage rule; the table beneath it already carries that.
- [ ] **Step 4: re-point `covered_config`'s docstring.** It currently says the normalization sentence *"is
      not implemented here — see `docs/superpowers/spec-defects.md` … an OPEN gap owned by H6"*, and it
      **quotes the sentence being deleted**. Once task 12 strikes that entry, this docstring points at a
      struck entry. Replace that paragraph with the **ruling**: `parameters_hash` hashes the config as
      written, by decision, and § How the three are computed is where the rule and its consequence are
      stated. **Delete the quotation rather than updating it.**
- [ ] **Step 5: sweep for the deleted sentences' OTHER homes, and the sweep must be able to fail.**
      Sweep **named files**: the four documents (`README.md`, `docs/design-principles.md`,
      `docs/experimental-designs.md`, `docs/reference.md`), `CLAUDE.md`,
      `docs/feasibility-llm-growth-studies.md`, `docs/superpowers/spec-defects.md`, and every file under
      `src/` and `tests/`. **The sweep must be newline-insensitive** — normalize whitespace across the
      whole file before matching, because a `grep -F` cannot match a phrase that wraps, and that is how
      two of one false sentence's five homes hid on the preceding slice. **Never filter the output of a
      sweep whose job is to find a string** — filter the file list. Prove each sweep can fail by running
      it against a string known to be present. **`covered_config`'s docstring is a known second home**
      and is closed by step 4; find the rest before committing, and **report what you swept, not a
      count**.
- [ ] **Step 6: mechanical pass** on every `reference.md` edit, as task 1's step 6 specifies.

**Delta:** 0 tests.

**What this task must NOT touch.** `hashes.covered_config`'s **body** or `parameters_hash`'s behaviour —
**Ruling B means the code does not change.** A task that finds itself editing either has found a
disagreement and must report it rather than proceed. `diff`'s config-side recomputation. The
`spec-defects.md` entries themselves — striking them is **task 12's**, and this task's docstring edit is
what makes the strike safe.

**Guard-pin arms this task may edit: NONE.**

---

## Task 3: `include` becomes a required batch parameter, and the fold is extracted

**Surface: `src/publishable/hashes.py`, plus 14 call sites.**

**Files:** `src/publishable/hashes.py`, `src/publishable/cli.py`, `tests/test_hashes.py`.

**The signature, and `None` is an explicit claim.**

```python
def hashed_files(
    repo_root: Path, include: Callable[[list[str]], set[str]] | None
) -> list[tuple[str, Path]]:
    """Sorted (repo-relative path, file) pairs across src/** and templates/**.

    `include` is handed EVERY candidate path that survived the fixed skip set,
    as repo-relative posix strings, and returns the subset to keep. It is
    positional and required: `None` is not a default, it is the explicit claim
    `hash every file these trees hold`, which only a caller without a
    repository can honestly make.
    """
```

```python
def code_hash_of(pairs: list[tuple[str, Path]]) -> str:
    """The fold, over a file list the caller already holds."""


def code_hash(repo_root: Path, include: Callable[[list[str]], set[str]] | None) -> str:
    return code_hash_of(hashed_files(repo_root, include))
```

**Why `code_hash_of` exists, and it is § Corrections 2 rather than tidiness.** Task 8's zero-file guard
needs the file list, and `command_run` also needs the digest. Without the extraction the command calls
`hashed_files` **and** `code_hash`, which walks the two trees **twice** and runs `git check-ignore`
**twice** — measured at 233 ms and 875 ms respectively on a 10,002-file tree — and makes
`E-CODE-FILE-LIST`'s **one emit site** false against the code, since the helper would have two reachable
raise paths. The extraction also makes Decision 4's *"the walk happens once, in one place"* literally
true.

**Why the parameter is required rather than defaulted.** `code_hash` has exactly **one** production
caller, so requiring it costs one line there and 13 mechanical edits in the pins, and it converts *a
future caller forgets and silently gets the un-excluded hash* into a `mypy` error. **Both of H7a's
fail-opens were predicates that answered permissively when nobody had told them otherwise.**

**Why a batch filter and not a per-path predicate.** `git check-ignore` costs **12.1 ms for 53 paths in
one call**; asking it per path would be 53 subprocesses. A memoizing per-path closure would have to do
**its own walk** to build its cache, re-introducing the second path spelling Decision 2 exists to
eliminate. Batching also makes Decision 3's *"git is never consulted about a path that is skipped
anyway"* literally true: the filter is called **after** the skip set has run, over exactly the survivors.

- [ ] **Step 1: add the parameter and apply it after the fixed skip set.** Collect the candidates exactly
      as today, then — when `include` is not `None` — call it **once** with the list of repo-relative
      posix strings and keep the pairs whose path is in the returned set. **The fixed skip set runs
      first, unconditionally**, so a tracked file inside `__pycache__` never reaches the filter. Sort as
      today.
- [ ] **Step 2: extract `code_hash_of` and make `code_hash` call it.** The fold is unchanged, byte for
      byte: `sha256(path) \0 sha256(contents) \n` folded over the sorted pairs, `sha256:`-prefixed.
- [ ] **Step 3: pin the identity, with a test rather than a comment.** Assert
      `code_hash(repo, None) == code_hash_of(hashed_files(repo, None))` on a real tree, **and** on a tree
      with a non-trivial `include`. Two implementations of one fold is what `covered_config` was
      extracted to prevent; this assertion is what keeps them one.
- [ ] **Step 4: edit the 14 call sites.** **13 in `tests/test_hashes.py`**, spread over six tests —
      `test_code_hash_covers_src_and_templates_only` (3), `test_code_hash_ignores_pycache` (2),
      `test_code_hash_is_prefixed_and_short_takes_seven` (1),
      `test_code_hash_skip_list_matches_relative_path_not_absolute` (3),
      `test_code_hash_still_skips_a_genuine_pycache_dir_inside_the_tree` (2),
      `test_code_hash_handles_a_dot_git_intermediate_path_component` (2) — **and `cli.command_run`'s
      `ch = code_hash(repo_root)`**, which gains a literal `None` here and is swapped for the real filter
      by task 5. **Without the production site, batch 2 does not typecheck.**
      **A near-miss worth not re-deriving:** `grep -c "code_hash(" tests/test_run_identity.py` returns 1,
      and it is the **name** of `test_the_id_is_timestamp_then_short_code_hash`, not a call site. There is
      no 15th site.
- [ ] **Step 5: guard-pin arm E — you are its SOLE AUTHORIZED EDITOR, and the edit is `None` only.**
      **Change no assertion.** Report the `git diff` line count for `tests/test_hashes.py` and confirm
      every changed line is a call rather than an assert. The two negative controls
      (`test_code_hash_skip_list_matches_relative_path_not_absolute`,
      `test_code_hash_handles_a_dot_git_intermediate_path_component`) must still resolve
      `code_hash(tmp_path / "nonexistent_empty_repo", None)` to `sha256:e3b0c442…`.
- [ ] **Step 6: mutation 1, and it is NAMED PARTLY BLIND IN ADVANCE.** Making `include` default to `None`
      has **no runtime difference** for callers that pass it. The catch is `uv run mypy` against a
      synthetic caller that omits it, and the runtime property that matters — that the one production
      caller passes a real predicate — is **task 5's mutation 2**. Name this in the report; do not claim
      it as a runtime pin.
- [ ] **Step 7: `code_hash_of`'s survival is a READING OBLIGATION, not a mutation, and it is stated as
      one.** Deleting the extraction does not make step 3's test *fail*, it makes it fail to **import** —
      two branches that cannot differ in the way a mutation needs. **A mutation is a claim too**, so this
      is not dressed up as one: the batch review reads `code_hash`'s body and confirms it delegates to
      `code_hash_of`, and task 5's **mutation P2** is what pins the property that actually matters — that
      the production caller takes the file list **once**.

**Delta:** +1 test.

**What this task must NOT touch.** `provenance.py` — the predicate is **task 4's**. Any assertion in
`tests/test_hashes.py`. The two byte-identical `__pycache__` tests, whose replacement is **task 6's**;
this task edits their call sites and nothing else, and **the 13 becomes 12 when task 6 removes one** —
that is expected and is not an arm-E violation.

**Guard-pin arms this task may edit: E, and only by adding `None`.**

---

## Task 4: the ignore helper in `provenance.py`, and `E-CODE-FILE-LIST`

**Surface: `src/publishable/provenance.py`, plus tests through direct calls and real repositories.**

**Files:** `src/publishable/provenance.py`, `tests/test_provenance.py`.

**The helper.**

```python
def unignored_under_hashed_trees(repo_root: Path, candidates: list[str]) -> set[str]:
    """The candidates git does NOT exclude, asked as one question in one call.

    `git check-ignore -z --stdin`, fed the repo-relative posix paths
    `hashes.hashed_files` already found, run with cwd=repo_root. Returncode 0
    means some listed path is excluded, 1 means none is, and anything else is
    a fault this refuses rather than reads: a path inside a submodule exits
    128 with `fatal: Pathspec ... is in submodule ...`, and inferring "nothing
    is excluded" from an empty stdout would hash another repository's files
    under a claim this record cannot support.

    `-z` is passed on BOTH ends and each entry is decoded with `os.fsdecode`:
    without `-z` git returns an excluded non-ASCII path C-quoted
    (`"src/pkg/na\\303\\257ve.env"`), which matches no key `hashed_files`
    produces, and `text=True` would decode with the locale's encoding rather
    than the filesystem's.
    """
```

**Three implementation routes are forbidden by name, because each is the likely error.**

1. **It must NOT call `provenance._git`.** That helper runs `check=False` and returns
   `result.stdout.strip()`, discarding the returncode — precisely the inference this refusal forbids, and
   it would turn rc 128 into an empty string indistinguishable from *nothing is excluded*.
   **`provenance.py` is the right place for the helper to sit; `_git` is the wrong thing for it to
   call.** *A recipe is its calls plus where they sit.* The precedent for refusing at a call site where
   an empty answer has no honest reading is `git_provenance`'s own `E-GIT-NO-COMMIT` block, in this same
   file — copy where it sits, not only what it calls.
2. **It must NOT pass `--no-index`.** Measured: for a committed `src/pkg/loose.pyd` against a
   `*.py[cod]` pattern, plain `check-ignore` reports **no match** (git does not exclude a tracked file)
   while `--no-index` reports `.gitignore:3:*.py[cod]`. **The flag that looks like a purity improvement
   is the one that breaks the rule.**
3. **It must NOT be reached with an empty candidate list and read as an error.** Measured:
   `check-ignore -z --stdin` with empty stdin returns rc **1**, which the tri-state already reads
   correctly as *nothing excluded* — but short-circuit on an empty list anyway and say why, because a
   subprocess for a question with no subject is work with no answer.

- [ ] **Step 1: write the helper**, exactly the signature Decision 4 specifies, so the caller can pass it
      as `include` without an adapter. Subtract git's answer from the candidate set and return the
      remainder.
- [ ] **Step 2: check the returncode, and raise `E-CODE-FILE-LIST` on anything but 0 or 1.** The message
      carries **git's own stderr verbatim** and names the repo root. Use `ContractError` with
      `code="E-CODE-FILE-LIST"`, the same shape `E-GIT-NO-COMMIT` uses.
- [ ] **Step 3: build Fixture I and assert the refusal.** A host repo with `src/pkg/step.py` and
      `src/vendor` added as a git submodule holding `lib/z.py`. **Measured here:** `check-ignore` exits
      **128** with `fatal: Pathspec 'src/vendor/lib/z.py' is in submodule 'src/vendor'`, while
      `hashed_files` finds `src/pkg/step.py`, `src/vendor/lib/z.py` and `templates/t.py`. Assert the
      raised error's `.code` is `E-CODE-FILE-LIST` and its message contains `src/vendor`. **Adding a
      submodule inside a test needs `-c protocol.file.allow=always`** on the `git submodule add`
      invocation; that is measured, not guessed.
- [ ] **Step 4: mutation 6 — route the call through `provenance._git`.** Caught by Fixture I: rc 128
      comes with **empty stdout**, so the mutant reads *nothing excluded*, keeps every candidate and
      raises nothing. Two branches that differ, measured.
- [ ] **Step 5: build Fixture F and assert the `-z` claim on EXCLUDED non-ASCII paths.** **§ Corrections
      4 binds this step and replaces the design's Fixture F.** The base tree with `*.env` appended to
      `.gitignore`, plus untracked `src/pkg/naïve.env` = `K=1\n` and `src/pkg/ünï.pyd` = `x\n`. Assert
      **two things**: the returned set equals `{"src/pkg/step.py", "templates/t.py"}` — set equality on
      the **kept** set, which is what `-z` protects — and `code_hash_of` over the kept pairs is
      `sha256:71bf339c…`, the base tree's digest. The docstring records that this was measured on
      macOS/APFS with `core.precomposeunicode = true`, and that **the paths are untracked**, so no index
      round-trip and therefore **no NFC/NFD normalization question arises** on any platform.
- [ ] **Step 6: mutation 3 — drop `-z` and split on newlines.** Caught by step 5's set equality **and**
      its digest: measured, the mutant's excluded set is
      `{'"src/pkg/na\\303\\257ve.env"', '"src/pkg/\\303\\274n\\303\\257.pyd"'}`, nothing is subtracted,
      the kept set gains both files and the digest becomes `sha256:06604d0c…` instead of `71bf339c…`.
      Two branches that differ, computed.
- [ ] **Step 7: mutation 4 — add `--no-index`.** Caught at task 5 by Fixture D's after value; **name it
      here and say which task's fixture catches it**, because a mutation whose catch lives in another
      task is a mutation whose report must say so.
- [ ] **Step 8: the ASCII control.** A tree with an excluded ASCII path only must return the same
      **shape** of answer, so a reviewer can see the non-ASCII arm is testing the encoding rather than
      the mechanism.
- [ ] **Step 9: the helper's docstring links the four-case table** in § How the three are computed
      (task 1) and **does not restate it**.

**Delta:** +5 tests.

**What this task must NOT touch.** `hashes.py`. `cli.py` — the wiring is **task 5's**. `_git` itself, and
no other `_git` call site. `git_provenance`'s pathspec.

**Guard-pin arms this task may edit: NONE.**

---

## Task 5: wire it at `command_run`'s single call site — THE VALUE CHANGE

**Surface: a real `run` through the installed console script. Not `validate`, not a direct call.**

**Files:** `src/publishable/cli.py`, `tests/test_cli.py`, `tests/test_hashes.py`.

**BINDING, and it reaches this brief because a ruling that overrules a brief has to reach the brief:**

- **You are guard-pin arm B's SOLE AUTHORIZED EDITOR, and exactly two literals move:**
  `ebc5ee53…` → `71bf339c…` and `_ebc5ee5` → `_71bf339`. **Every other literal in that arm stays put.**
  **An edit to arm A, C, D, E or F is a finding**, and arms A, C and D have **no authorized editor at
  all** — a passing arm after this task is the proof.
- **The predicate is built HERE and bound at the moment of hashing — phase 5, not phase 3.** Between the
  dirty gate and the hash, `command_run` resolves units, which runs a **plugin resolver — user code that
  can create or remove files under `src/`**. An ignore answer captured at phase 3 and used at phase 5
  answers *what did git see before user code ran*, which is not the question the hash asks. **State read
  at the wrong moment is a proxy**, and it is the H7a corollary that cost its own round.
- **`git check-ignore` must run exactly ONCE per `run`** (§ Corrections 2). Take the file list once at the
  existing `ch = code_hash(repo_root)` site and fold it with `code_hash_of`.

**The edit.** At `command_run`'s existing hashing site, replace `ch = code_hash(repo_root)` with:

```python
def _include(candidates: list[str]) -> set[str]:
    return unignored_under_hashed_trees(repo_root, candidates)

hashed = hashed_files(repo_root, _include)
# task 8 inserts the E-CODE-EMPTY guard here, over `hashed`
ch = code_hash_of(hashed)
```

- [ ] **Step 0: name the import edits, because the plan this one copies its form from had exactly this
      correction.** H5b's § Corrections held *"`cli.py` does not import `_is_numeric`."* Here, `cli.py`
      imports `code_hash, design_digest, parameters_hash` from `publishable.hashes` and
      `find_repo_root, git_provenance` from `publishable.provenance`. **This task adds `hashed_files` and
      `code_hash_of` to the first and `unignored_under_hashed_trees` to the second.** Neither name is in
      scope before this edit.
- [ ] **Step 1: wire it, and change nothing about where the site sits.** The existing site already runs
      after unit resolution and before `allocate_run_dir`, which is what Decision 5 and Decision 7 both
      require. Do not move it.
- [ ] **Step 2: Fixtures A and B, end to end through `main(["run", …])`.** Assert the recorded
      `code_hash` and the run directory's name for both. Arm B's two literals move here and nowhere else.
- [ ] **Step 3: mutation 2 — compute the filter and ignore it** (drop the `include` application from
      `hashed_files`' loop). Caught by Fixtures B and C: `ebc5ee53…` versus `71bf339c…`, measured.
- [ ] **Step 4: Fixture C, the other two unhonoured patterns.** Untracked `src/.venv/lib/site.py` and
      `src/pkg/loose.pyd` beside B's `.env`. Assert the today digest `1947d2a2…` is **not** what the run
      records and that the recorded digest is `71bf339c…`. Assert the helper's own answer names exactly
      those three paths.
- [ ] **Step 5: Fixtures D and D′, and mutation 4.** A **tracked** `src/pkg/loose.pyd` = `X` (one byte,
      no newline, `git add -f`-ed) is still hashed: `eec1541e…`. **§ Corrections 5 binds this step:** the
      design's literal `6ddb8634…` is not reproducible from its own stated tree because the `.pyd`'s
      bytes were never stated, and `X` gives `eec1541e…`. **Fix the bytes in the fixture and assert the
      recomputed value.** The untracked twin's *today* value is also `eec1541e…`, so **assert the after
      value**; the today value would pass under a mutation that drops tracked files too. Mutation 4
      (`--no-index`) turns `eec1541e…` into `71bf339c…` — measured.
- [ ] **Step 6: mutation 5 — ask git before applying the fixed skip set** and drop the skip for a path
      git calls unexcluded. Caught by Fixture E (task 6 owns Fixture E's own test; **this mutation's
      catch lives there and this report says so**).
- [ ] **Step 7: mutation 7 — build the predicate at phase 3 and reuse it at phase 5. IT IS NOT BLIND, and
      § Corrections 10 gives the construction.** A project-local resolver whose module text embeds an
      **absolute path** into the project's own `src/` and writes `src/pkg/generated.py` during
      `resolve_units` — `tests/test_cli.py`'s `_install_plate_wells_resolver` and `run_a_project` are the
      two helpers that already do everything else this needs. The dirty gate ran at phase 3 and passed
      before the file existed, so the run proceeds. **The assertion:** after the run, recompute
      `code_hash_of(hashed_files(repo_root, live_predicate))` over the same tree and assert it **equals**
      the record's `code_hash`. Under the mutant the phase-3 answer predates the write, `generated.py`
      drops out of `include`, and the two differ by one file. Two branches that differ, and the
      discriminator is a digest rather than a file's presence.
- [ ] **Step 8: mutation P2 — pin the subprocess count.** Patch `subprocess.run` (or the helper) with a
      counter and assert `git check-ignore` is invoked **exactly once** for one `run`. **The mutant:** call
      `hashed_files(repo_root, _include)` and `code_hash(repo_root, _include)` separately — the naive
      shape — and watch the count go to 2. This is the pin § Corrections 2 exists for, and without it the
      correction is prose.
- [ ] **Step 9: Fixture M — one record carrying two hash definitions, and mutation 14.**
      **The sibling that already got it right is the first place to look:** `tests/test_cli.py`'s
      `_build_fixture_f_upstream` builds a **genuinely produced** upstream run with a `run`-scoped step
      publishing `out.json` and reads the shared step's name back out of its own `run.yaml` rather than
      assuming it. **Use it, then rewrite that record's `code_hash` to `ebc5ee53…` in place** — a real
      record with one field edited is a better pre-change artefact than a hand-written mapping, because
      it satisfies `lineage.read_record_file` by construction rather than by luck. Then run a post-change
      run over the base tree that consumes it through `io.reuse_from`. Assert the new record's own `code_hash` is `71bf339c…`, that
      `provenance.upstream[0].code_hash` is `ebc5ee53…` **copied verbatim** (`lineage.py` copies it;
      grepped), and — this is the part that must not be written as an absence —
      **assert the record's top-level key set as a literal**, so a future slice that adds a marker fails
      this fixture and has to come back and read Ruling C. Mutation 14 (recompute the upstream's hash at
      ledger time) makes both digests `71bf339c…`.
- [ ] **Step 10: run the whole suite and report the moved-test list**, named rather than counted.

**Delta:** +6 tests, plus arm B's two edited literals.

**What this task must NOT touch.** Arms A, C, D, E, F. `hashes.py`'s fold. `provenance.py`'s helper.
`diff.py`. The dirty gate at phase 3 — **the predicate is not bound there**, and a task that finds itself
editing phase 3 has misread Decision 5.

**Guard-pin arms this task may edit: B, and only its two enumerated literals.**

---

## Task 6: the hash and the gate agree, and the duplicated `__pycache__` pin is replaced

**Surface: direct calls to `hashes.hashed_files` and `provenance.git_provenance` over a real repository.**

**Files:** `tests/test_hashes.py`.

**Decision 13, and the false sentence it exists to stop.** The scoping says the hash and the dirty gate
*"would share one file list."* **They do not, and writing that into a docstring would be a false claim.**
They share `HASHED_TREES` — one constant, one pathspec — and ask git **two different questions**:
`git status --porcelain -- src templates` (has anything moved?) and `git check-ignore` (is this path
excluded?). `status` never lists a clean tracked file, so it cannot produce the hash's file list. **What
this task pins is behavioural agreement, not a shared list.**

- [ ] **Step 1: Fixture J — one test, two assertions, on one tree.** Fixture B's tree: assert
      `git_provenance(...).code_dirty is False` **and** that `src/pkg/.env` is absent from
      `hashed_files`' output. Both halves in one place so neither can move alone. The docstring states
      the four states and that they agree — untracked-not-excluded is dirty and hashed, tracked-modified
      is dirty and hashed, tracked-clean is not dirty and hashed, **excluded-but-present is neither** —
      and states that **today** the last one is *not dirty and hashed*, which is the disagreement this
      slice closed.
- [ ] **Step 2: replace the duplicated pin.** `test_code_hash_ignores_pycache` and
      `test_code_hash_still_skips_a_genuine_pycache_dir_inside_the_tree` are **byte-identical in body** —
      both write `src/pkg/step.py`, take a digest, write
      `src/pkg/__pycache__/step.cpython-311.pyc` = `"junk"`, and assert the digest is unchanged. Remove
      **one** and give the survivor Fixture E's tracked arm: a **tracked** `src/pkg/__pycache__/keep.py`
      = `k = 1\n`, `git add -f`-ed, which **git reports as not excluded** (measured, rc 1) and which the
      fixed skip set must keep out anyway. The digest stays `eec1541e…` — measured on Fixture D's tree.
      **This is the positive control for § Templates' *"unconditionally"*.**
- [ ] **Step 3: demonstrate the survivor can fail, by mutation, not by assertion.** Remove `__pycache__`
      from `_SKIP_DIRS` and confirm the test fails. **A mutation that changes nothing is evidence about
      the tests, not about the code** — and the removed twin proves the point: deleting either one alone
      left the suite green, which is why one of them was doing no work.
- [ ] **Step 4: state the delta as added minus removed**, and name the removed test by its full name in
      the report. This is the one task in the slice with a negative component.

**Delta:** +2 tests, −1 test (net +1). The 13 `code_hash(` call sites become 12; **that is expected and
is not a guard-pin arm E violation**, because arm E's claim is about the two negative controls' return
value, neither of which is the removed test.

**What this task must NOT touch.** `src/` — this task is tests only. The two negative controls. Arm D,
whose literal this task's fixture shares and **does not edit**.

**Guard-pin arms this task may edit: NONE.**

---

## Task 8: `E-CODE-EMPTY` — the guard, its § Errors row, and its two reachable situations

**Surface: `src/publishable/cli.py`, and a real `run` through the installed console script.**

**Files:** `src/publishable/cli.py`, `docs/reference.md`, `tests/test_cli.py`.

**The guard is at the CALLER, and the reason is measurable.** Two tests in `tests/test_hashes.py` use
`code_hash(tmp_path / "nonexistent_empty_repo", None)` as a **negative control** —
`test_code_hash_skip_list_matches_relative_path_not_absolute` and
`test_code_hash_handles_a_dot_git_intermediate_path_component`, both of which compare a real digest
against the empty one to prove the skip list is matched against **relative** parts. **A refusal inside
`hashes.py` would break both.** So `hashes.code_hash` still returns `sha256:e3b0c442…` for an empty tree,
and `command_run` refuses.

**The guard is written as `if not hashed:`, NOT as a comparison against the empty digest.** `ch ==
"sha256:e3b0c442…"` is behaviourally exact and it answers *were there zero files?* with a digest
comparison — **a proxy**, and a mutation swapping one for the other passes every fixture in this slice.
It is rejected by name here so it is not discovered in review.

**One emit site, and the cost of that choice is stated rather than hidden.** The site is at the hashing
site established by task 5, before `allocate_run_dir` and before any execution is paid for — **and after
unit resolution, so a resolver's quota may already be spent when it fires.** A second, earlier gate at
phase 3 would save that quota, but a mutation deleting the phase-5 site would then be **blind** unless a
fixture empties the trees *between* the two phases. **Two sites where one has a blind mutation and no
replacement** is the shape the § Errors work exists to catch, so H6a ships **one**.

- [ ] **Step 1: insert the guard** immediately after `hashed = hashed_files(repo_root, _include)` and
      before `ch = code_hash_of(hashed)`. Refuse through a `Collector` the way `E-CODE-DIRTY` does in the
      same function, print, and return `EXIT_WRONG`. The message **names both hashed trees** and says the
      run would otherwise publish the digest of nothing.
- [ ] **Step 2: Fixture G, end to end. Two construction facts, both measured, so the fixture is not
      discovered to be unbuildable mid-task.** **Git does not track an empty directory**, so `src/` must
      exist on disk while git holds nothing under it — which is also why the dirty gate is clean here,
      the same property measured for Fixture H. And the entrypoint must resolve from **outside** both
      trees: `load_experiment` inserts `<repo>/src` at the front of `sys.path`, but
      `importlib.import_module` still resolves anything else already importable, which is exactly how
      the scoping reached this case. A committed repo with an **empty** `src/`, no `templates/`, and
      an entrypoint importable from a `PYTHONPATH` directory outside both trees — the shape the scoping
      measured producing a **completed run at exit 0** with `code_hash: sha256:e3b0c442…` in its
      `run_id`. Assert exit 1, `E-CODE-EMPTY` in the output, **and that no run directory exists** — by
      listing `output_dir`, not by the exit code alone. *A refusal that leaves an empty run directory
      behind is a different behaviour from one that does not.*
- [ ] **Step 3: Fixture H — the situation task 5 CREATED.** A committed repo whose `.gitignore` is
      `src/`, whose `src/pkg/step.py` is untracked, **and which holds no file under `templates/**`**.
      **§ Corrections 6 binds this step:** measured, `git status --porcelain -- src templates` prints
      **nothing** (the dirty gate passes), today's digest is `f6a935cf…` — a real one — and after task 5
      there are **zero** hashed files. **With a `templates/t.py` present the after digest is `ef36e0c9…`
      and the refusal never fires**, so the fixture as the design states it would not reach the code it
      exists to test.
- [ ] **Step 4: mutation 8 — delete the guard.** Caught by Fixtures G and H: exit 0 and a completed run
      with the empty digest, measured as today's behaviour.
- [ ] **Step 5: mutation 9 — move the guard after `allocate_run_dir`.** Caught by Fixture G's *no run
      directory* assertion: the mutant leaves a directory behind.
- [ ] **Step 6: mutation P1 — replace `not hashed` with a comparison against the empty digest.**
      **Named blind in advance**: the two branches cannot differ, because the digest of an
      empty list *is* the empty digest. **The replacement is a reading obligation, stated as one**: the
      batch review reads the guard and confirms it tests the list, not the digest. That is why the
      one-liner is forbidden in this brief rather than left to a test.
- [ ] **Step 7: the § Errors row — ONE row covering EVERY emit site.** Add `E-CODE-EMPTY` to § Errors core
      raises. The row names **both reachable situations in one row**: no file under the two trees at all,
      and every file under them excluded by git. It says the guard is at the caller and that
      `hashes.code_hash` still returns the empty digest, **so a reader does not go looking for it in
      `hashes.py`**. It links the four-case table and restates none of it.
- [ ] **Step 8: the § Errors row for `E-CODE-FILE-LIST`**, whose code landed in task 4 and whose row lands
      here so both new rows are written by one task with one shape. **One row, one emit site** — the
      helper in `provenance.py`, reached from `command_run`'s single hashing site. It names the submodule
      case as the reachable instance, says the message carries git's own stderr, and says **explicitly
      that an empty answer is not read as "nothing excluded"**.
- [ ] **Step 9: mechanical pass** on both `reference.md` rows, as task 1's step 6 specifies.

**Delta:** +2 tests.

**What this task must NOT touch.** `hashes.py` — the empty digest stays. `E-CODE-DIRTY`'s absent row
(H6b task 17). `validate` (Decision 15). The nine undocumented codes.

**Guard-pin arms this task may edit: NONE.**

---

## Task 9: the zero-file blast radius, and the stale owner corrected before it is struck

**Surface: reading and re-running, plus one `spec-defects.md` correction.**

**Files:** `docs/superpowers/spec-defects.md`.

- [ ] **Step 1: re-run guard-pin arm E and report it.** `code_hash(tmp_path / "nonexistent_empty_repo",
      None)` still returns `sha256:e3b0c442…`; both negative controls still pass. **Report the `git diff`
      line count** across `tests/test_hashes.py` for the whole branch to this point and confirm every
      changed line in those two tests is a call rather than an assert.
- [ ] **Step 2: correct the stale owner line BEFORE the entry is struck, so the correction survives in
      the record.** The `code_hash` over zero files entry routes its diagnostic to *"H1 Validation's
      registry once H6 says what it should say"* — **and H1 has shipped.** That is the closed-slice-owner
      pattern this file rejects by name at its own `RE-OWNED 2026-08-19` entry. Append the correction
      naming what it replaces; **do not retro-edit the original text.** The strike itself is **task
      12's**, and it will read the corrected owner rather than the stale one.
- [ ] **Step 3: report what you grepped, not a count.** Before writing any claim about what other tests
      assert about the empty digest, grep for it across `tests/` by name and report the file list and the
      hits.

**Delta:** 0 tests.

**What this task must NOT touch.** The strike itself. Any other `spec-defects.md` entry. Any code.

**Guard-pin arms this task may edit: NONE** — arm E is re-run, not edited.

---

## Task 11: `W-PARAM-UNSET` at `validate`, and the shared helper

**Surface: `validate` through a `Collector`.**

**Files:** `src/publishable/validate.py`, `docs/reference.md`, `tests/test_validate.py`.

**The warning, and its boundary — which is the part that would otherwise be an overclaim.**
`W-PARAM-UNSET` is reported by `validate._check_parameters` for every `parameter_spec` path that carries
a default and that this config does not set — **one diagnostic naming all of them**, on
`W-TEMPLATE-VERSION`'s own enumerating message shape, never one per parameter. **It covers the
`parameters` block only.** An omitted **core-schema** key is the same symptom through the same code
(`Node.__getattr__` → `E-STEP-PARAM-UNKNOWN`) and is **filed, not built** — task 12 files it —
**unassigned, with the reason**: core itself reads core-schema keys defensively (`(config.get("sweep")
or {})`), so an omitted one harms nothing core does; the only casualty is a **step** reaching for it
through `cfg`, and knowing whether a step does that means reading its body, which is the line core does
not cross. Closing it would need either the forbidden defaults structure or the greenfield line crossed.

**It is a warning and not an error, and the reason is measured.** Omitting a defaulted parameter is what
almost every hand-written config does; a freshly `init`-ed config sets all four of `generic`'s, so the
warning does **not** fire for a scaffolded project. And core cannot know whether a step reads the
parameter.

**`W-TEMPLATE-VERSION` keeps its unset-and-defaulted clause** (Decision 11). The clause is **true**, so
*prefer deleting a claim to rewriting it* does not license removing it — that rule is about false claims.
What changes is that both sites compute the list through **one** helper, which is the `covered_config`
precedent for how two sites do not drift.

**§ Corrections 7 and 8 bind this task.**

- [ ] **Step 1: extract the shared helper.** `_check_versions` already computes exactly this list —
      `[path for path, param in template.parameter_spec.items() if path not in set_here and param.default
      is not MISSING]`. Extract it once and call it from both sites. **Non-behavioural**: arm F asserts
      `W-TEMPLATE-VERSION`'s full message and **zero characters change**.
- [ ] **Step 2: report the warning from `_check_parameters`**, after the existing `E-PARAM-MISSING` loop,
      at path `parameters`, enumerating every unset-and-defaulted path in one message and stating the
      consequence (`cfg.parameters.<path>` raises `E-STEP-PARAM-UNKNOWN`).
- [ ] **Step 3: Fixture K, with its control arm.** Two configs against `generic`: one omitting
      `analysis.confidence` and `analysis.drop_missing` — the warning fires **naming both**, exit 0,
      `has_errors` False — and one setting all four, where **no** warning fires. **The second arm is what
      makes the first non-vacuous**, and it fails if the check fires unconditionally.
- [ ] **Step 4: mutations 10, 11 and 12.** (10) Delete the call site — caught by Fixture K's first arm;
      **check the render's other diagnostics for the string `analysis.drop_missing` first** rather than
      assuming nothing else produces it. (11) Fire for parameters that **are** set — caught by the
      control arm. (12) Delete `W-TEMPLATE-VERSION`'s unset clause after the extraction — caught by arm F,
      which asserts the full message and of which **the clause is a substring**.
- [ ] **Step 5: mutation 13 is NAMED BLIND IN ADVANCE and owes a replacement.** Replacing the shared
      helper's body at **one** of its two call sites with an inlined copy is caught by nothing: two
      identical implementations produce identical results, which is what sharing them prevents. **The
      replacement is a reading obligation, and it is stated as one: the batch review reads both call
      sites and reports that each calls the helper.**
- [ ] **Step 6: run the full suite and report the count of tests whose render changed.** **This plan
      measured that count and it is ZERO** (§ Corrections 7): with the warning wired in exactly this
      shape, `uv run pytest -q` returned **2931 passed, 1 skipped, 2 xfailed** — no failures. The
      positive control fired (a direct `_check_parameters` call over a config omitting two of `generic`'s
      four produced exactly one `W-PARAM-UNSET` naming both; the complete config produced none), and an
      instrumented run of `tests/test_validate.py`, `tests/test_templates.py`, `tests/test_materialize.py`
      and `tests/test_diagnostics.py` showed the warning firing in **7** tests, all still passing.
      **The measurement is valid for THIS shape — one diagnostic, at path `parameters`.** A per-parameter
      shape, or a different `path`, moves finding counts and path sets and **the measurement must be
      re-run.** A non-zero count is a **disagreement to report**, and for each moved test say whether the
      assertion was *updated* or *loosened*.
- [ ] **Step 7: DELETE the false clause in a shipped test's docstring. § Corrections 8.**
      `test_an_unset_parameter_is_named_only_when_the_version_moved`'s docstring reads *"a config matching
      the installed version draws no warning at all, so a defaulted parameter it omits is not
      reported."* After this task the second clause is **false** and the test **still passes**, because
      its assertion is `"W-TEMPLATE-VERSION" not in codes(path)`. **Delete the false clause; keep the
      test's name** — it is still true of `W-TEMPLATE-VERSION`, and renaming it breaks every grep that
      finds it. **This edit sits OUTSIDE guard-pin arm F**, whose claim is that the *message* changes zero
      characters; say so in the report so a reviewer does not read it as an arm-F violation.
- [ ] **Step 8: the § Warnings row and the § Validation row.** One § Warnings core reports row for
      `W-PARAM-UNSET` covering its **one** emit site, stating the condition rather than the wording, and
      one § Validation row — a row there and a code there are the same check seen from two ends.
      **`W-TEMPLATE-VERSION`'s row does not change** (Decision 11), and `E-STEP-PARAM-UNKNOWN`'s does not
      either: its row describes a `cfg` path the config does not hold, which stays exactly true.
      **Mechanical pass** on both edits.
- [ ] **Step 9: grep before claiming.** `grep -rn "W-PARAM-UNSET" src/ tests/ docs/*.md README.md` → **0**
      at `f8450f9`, control `E-CODE-DIRTY` → 3. Re-run and report both.

**Delta:** +2 tests, plus one deleted docstring clause.

**What this task must NOT touch.** `_check_versions`' behaviour or message. `hashes.py`. The core-schema
half — **filed, not built**. `E-PARAM-MISSING`'s condition, which is about a **defaultless** parameter
and is a different check.

**Guard-pin arms this task may edit: F — and the specified edit is ZERO characters.** Arm F passing
unedited after this task is the proof that the extraction was behaviour-preserving.

---

## Task 12: the records

**Surface: tracked records and `CLAUDE.md`. `spec-defects.md` is a live list, so a closed gap is struck;
every other tracked record is appended to, never retro-edited.**

**Files:** `docs/superpowers/spec-defects.md`, `docs/superpowers/specs/2026-08-08-implementation-spine-design.md`, `CLAUDE.md`.

- [ ] **Step 1: strike *"`code_hash` is not `.gitignore`-aware (S1 deviation, not a spec defect)"*.** The
      strike carries the ruling **and quotes and corrects the entry's own false sentence**: *"In practice
      nothing else gitignored appears under `src/**` or `templates/**`, so the two agree today"* was
      falsified by **three of the scaffold's own four patterns** — `.env`, `.venv/` and a `.pyd` all move
      the hash today, while `__pycache__/x.pyc` and a loose `.pyc` do not, and that last pair is a
      coincidence rather than a partial honouring. Note that the resolution the entry itself names —
      *"passing an `is_ignored` predicate in from the caller, which already shells to git"* — is what
      shipped, and that the predicate answers about **git's whole exclude chain**, not `.gitignore`
      alone.
- [ ] **Step 2: strike *"`parameters_hash` does not normalize to what `init` would have materialized"* —
      AS RULED, NOT AS BUILT.** Say which of the entry's own two options it took: the second (*"state in
      § How the three are computed that normalization is the caller's job and name the caller"*) is close
      to what shipped, and what actually shipped is **the sentence deleted rather than relocated**, with
      its false `diff` justification deleted beside it. **Check `hashes.covered_config`'s docstring
      against this strike before committing** — task 10 re-pointed it, and a filing's claims about the
      code go stale like any other comment.
- [ ] **Step 3: strike *"`code_hash` over zero files is indistinguishable from several distinct
      situations"* — after task 9's owner correction, which must already be in the file.** The strike
      names `E-CODE-EMPTY`, its **one** emit site, and the fact that the empty digest is still what
      `hashes.code_hash` returns.
- [ ] **Step 4: append to the nine-undocumented-codes entry.** Record that H6a documented **its own two
      new codes and took none of the nine**, and that `E-CODE-DIRTY` remains **H6b task 17's** gated
      question. Do not resolve the widening question; it is the spine owner's.
- [ ] **Step 5: file the new gap — an omitted CORE-SCHEMA key validates clean and kills a step that reads
      it.** **Owner: unassigned, with the reason** — no remaining slice (H6b, H9, H3c-3's remaining 14)
      has core's schema envelope as its surface, and closing it needs either the forbidden defaults
      structure or reading user Python. **Not *"whichever slice next touches the schema"***, the form
      this file rejects by name. **A ledger line saying "filed" is not a filing**: write the entry.
- [ ] **Step 6: do NOT touch the six-unwritten-`run.yaml`-keys entry.** Its last live row
      (`provenance.environment.os`/`.hostname`/`.hardware`) is **H6b's**; H6a writes no environment key.
      Named here so its survival is not read as an omission.
- [ ] **Step 7: append a correction to the spine design § The hardening slices — APPEND, DO NOT EDIT.**
      Three things: the H6 row's *"`parameters_hash` normalization against `parameter_spec`"* is
      **rejected**, with Decision 9's grounds; its *"the purity rule that forced both"* names a rule that
      is **not in `design-principles.md` at all** and is already broken in its own terms (`hashes.py`
      rglobs, reads bytes and carries `_SKIP_DIRS`, which is filesystem policy); and its *"Independent"*
      verdict is **too strong in one direction — H6 before H9.**
- [ ] **Step 8: the `CLAUDE.md` slice entry.** It states: the **value change** and that `code_hash` is the
      only hash that moves; the two minted errors and one warning; **zero configs unblocked**; that
      `diff` prints `code_hash DIFFERS` for identical code across the boundary and `uv.lock` is the
      carrier; and Ruling C's sharpest cost — **one record can carry two hash definitions**, its own
      under the new rule and a copied upstream's under the old, with nothing marking which is which.
      Update the order line from *"H6 Hashes and provenance, H9, then H3c-3's remaining 14"* to **H6b,
      H9, then H3c-3's remaining 14**.
- [ ] **Step 9: both consistency passes, over NAMED files.** **Mechanical**, in full, over every `.md`
      this branch touched: every relative link and `#anchor` resolves; no two headings in a file produce
      the same anchor; every table's rows match its header's column count and no row is empty; no
      trailing whitespace, tab or invisible unicode; `×` not `x`; hyphens in anchors. **Skip fenced
      blocks.** **Cross-document**, over the four documents only: the shared worked example, config
      completeness, enum comments, schema fields in prose, declared-versus-derived, versions, prevented
      mistakes. **Neither pass governs the development record**, and `spec-defects.md` is the one
      exception where a closed gap is struck rather than left.
- [ ] **Step 10: the sweeps.** After removing or renaming any string, sweep the four documents, `CLAUDE.md`
      and the feasibility analysis for what should no longer exist. **Name the file list. Never filter
      the output of a sweep whose job is to find a string — filter the file list.** **Every sweep must be
      newline-insensitive**: normalize whitespace over the whole file before matching, because a `grep
      -F` cannot match a wrapped phrase, and that is how two of one false sentence's five homes hid.
      **Prove each sweep can fail** by running it against a string known to be present, and **report what
      you swept rather than a count.**

**Delta:** 0 tests.

**What this task must NOT touch.** The § Executability entry — **task 13's**. Any `spec-defects.md` entry
this slice did not close. Any code.

**Guard-pin arms this task may edit: NONE.**

---

## Task 13: the § Executability entry — four rows, character for character, no fifth number

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
