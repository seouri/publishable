# H5b — non-numeric columns downstream to `aggregate` — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to
> implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** a column a step recorded that is not a number — a bool, a label, a reason string — reaches
the table a template's `aggregate` receives, and the unit that recorded it is a unit. `collapse_repeats`
stops dropping the value and stops dropping the whole unit; a column that disagrees across a unit's
repeats collapses to `None` and says so; `summarize_step` keeps such a column out of `aggregated`
because a metric block's `value` is a number; the derived-key collision its shipped docstring already
promises becomes real; a non-numeric recorded `by` column earns the warning § Steps and artifacts
already states without qualification; and the contrast subtraction gains the guard that stands between
a non-numeric value and a completed run losing its `run.yaml`.

**H5b is not additive.** It changes what existing keys in `run.yaml` report. The argument is made in the
open in the design's § The behaviour change, re-measured by this plan (§ Corrections 9 and 10), and
pinned key by key with computed literals in task 1.

**H5b moves ONE row of the four-row table and mints no fifth number.** The 2026-08-20 correction in
[the feasibility analysis](../../feasibility-llm-growth-studies.md) § Executability on this build ruled
that a single figure answers no consistent question for that analysis. H8a replaced the number with a
table and every slice since has repeated it. **H5b repeats rows 1–3 character for character and
re-derives row 4**, per H5a design Decision 11 and this design's Decision 14.

| Figure | Count | Visible to `validate`? |
|---|---|---|
| Transplantable configs validating with zero errors | **8 of 8** | yes — the only figure `validate` can see |
| Blocked on `io.reuse_from` | **0** | no — the method ships; six configs still need the plugin body to call it |
| Meet the `report_by`-under-`resample` gap | **7** | no — a documented permanent limitation, **not** this slice's and **not** folded in |
| Free of every core-side dependency this analysis can name | **`0` before this slice, `1` after** | no — E5, and only with the plugin written and installed |

**Row 4's published value is `1` and the honest figure today is `0`** (design Decision 14): a
non-numeric recorded column vanishing between the write and `aggregate` is a core-side dependency, and
E5's own shared request step records `valid`, `invalid_reason` and `finish_reason`. **The entry dated
2026-08-22 against `71f3c6e` left row 4 at `1` and substituted a paragraph** — so task 16 **appends a
correction naming what it replaces**, and edits nothing. **No task may write "N configs now execute" or
mint a fifth number.**

**Architecture.** No new module, no new export, no new file of any kind. Two source files and two
documents move.

- **`stats.py`** — the repeat walk is extracted once and read twice: `collapse_repeats` carries every
  recorded value and admits every unit it was handed, and a new public `repeats_disagreeing` answers
  *which columns disagreed across a unit's repeats* **from the rows**, never from a collapsed cell.
  `summarize_step` ships **no code change** and one deleted docstring clause. The return type widens at
  20 annotation sites.
- **`cli.py`** — the disagreement warning's one call site; the contrast filter in the paired arm's
  `col_keys` and the unpaired arm's `of_col`/`against_col`; the `by` gate re-pointed at the
  recorded-column set the same loop already computes; `_attributed`'s two falsified grounds deleted.
- **`docs/reference.md`** — § Templates: where parameters are defined, § Statistical reporting,
  § The per-unit tables, § Warnings core reports, § Steps and artifacts.
- **`docs/superpowers/spec-defects.md`** — three entries struck, three filed, one re-owned onto H9.
- **`docs/feasibility-llm-growth-studies.md`** — one appended § Executability entry.
- **`docs/superpowers/specs/2026-08-08-implementation-spine-design.md`** — one appended correction.
- **`CLAUDE.md`** — the slice entry and the order line.

**Tech stack:** Python ≥ 3.11, `pytest`, `ruff`, `mypy`. Tests land in existing modules —
`tests/test_stats.py`, `tests/test_cli.py`, `tests/test_report.py`, `tests/test_study.py`. **No new
file is created by any task**, so `ruff format --check` stays at 93 and `mypy` at 52 source files.

**Spec:** `docs/superpowers/specs/2026-08-22-non-numeric-columns-downstream-design.md` — read it beside
this plan, including its § The behaviour change, § The discriminating fixtures, § The mutations, § The
guard pin, § The § Errors and § Warnings work, § What each change makes reachable, and its **appended
Controller ruling, which post-dates the body and wins over it**. Its body must not be edited. Where this
plan measured something that contradicts it, the disagreement is in
[§ Corrections against the code](#corrections-against-the-code), appended by this plan's author and
extended by no task.

**Measurement this plan argues from:** `docs/superpowers/H5b-SCOPING.md`, measured 2026-08-22 against
`5ee3a0c` — **several of whose claims the design already falsified, and the design wins**; the design's
own re-measurement at `7dba9e8`; and this plan's re-measurement against **`main` at `ee8085e`**.
`git diff --stat 5ee3a0c ee8085e -- src tests` prints **nothing** — every commit between them is
documents — so the code this plan measured is byte-identical to the code the scoping measured, which is
what licenses reusing its baseline while re-checking its claims. Every signature, message, helper name
and literal below was read or **run** at `ee8085e`. **Nothing is cited by line number.**

**Baseline, measured 2026-08-22 in the FOREGROUND at `ee8085e`:**

- `uv run pytest -q` → **2891 passed, 1 skipped, 2 xfailed** (the scoping's own foreground run, valid
  here by the empty `src`/`tests` diff above; re-confirm it once before task 1 commits and reconcile any
  difference before proceeding)
- `uv run ruff check .` → **All checks passed!**
- `uv run ruff format --check .` → **93 files already formatted**
- `uv run mypy` → **Success: no issues found in 52 source files**

**Task count: 16.** The design's 15 in its own grain and its own numbering, plus **task 16, the
§ Executability entry**, which the controller's hard requirement gives a task of its own. The addition
**appends** rather than renumbering, on H5a's, H8a's, H8b's, H8c's and both H7d parts' precedent, so the
design's numbering stays citable. 16 tasks make 16 commits.

---

## Sequencing

**Execution order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14 → 15 → 16.**
The design's own order, unchanged. Each task restates the constraint it depends on in its own text,
because an implementer sees only their own task brief.

| Constraint | Why, and where it is enforced |
|---|---|
| **Task 1 first, before any code** | H5b moves published numbers and must leave the numeric-only path untouched. That is only pinnable against literals captured **before** anything moved; a literal captured after a task has run records the move, not the baseline. Arms A, C and D have **no authorized editor at all** |
| **2 and 3 before 4** | The documents lead. `W-STATS-REPEATS-DISAGREE` is minted in § Warnings core reports **before any code reports it**, and § Templates states the collapse rule before the collapse implements it. This is the repo's documents-lead order, not a build claim |
| **4 before 5** | Task 4 is carriage and admission; task 5 is the across-repeats rule over what task 4 carries. Landing 5 first would write a rule for values nothing yet gathers |
| **4 carries Fixtures E and H** | **A live overruling of the scoping's task list, made by the design and restated here so it reaches the brief** (design § What each change makes reachable). The derived-key collision and `cli.py`'s second empty-level gate both go live at task 4 with no further code, and their pins would otherwise sit two batches later where the collapse batch's green suite is no evidence about either. Tasks 10 and 11 keep their **document and record** halves and lose their pins to task 4 |
| **5 before 6** | Task 6's only product is a deleted docstring clause and the projection pin, and the clause is false only once nothing is dropped above — which is true after task 4 and complete after task 5 |
| **7 before 8** | Both are the contrast surface. Task 7 is the guard; task 8 documents the `paired_keys` ruling that decides what the guard is guarding |
| **9 before 10** | Both touch a namespace question in the same `cli.py` loop; landing the `by` arbitration first means task 10's diff is `tests/test_stats.py` and one § Errors assertion |
| **12, 13, 14 after every code task** | They are pins over the finished behaviour, and one of them (14) reads `run.yaml` through two shipped commands |
| **15, then 16** | Both consistency passes and every filing run against the finished branch; the § Executability entry is appended last so its commit sha is the branch's |

### Three deviations from the design's grain, each argued

**(a) Task 16 exists at all.** The design folds the § Executability entry into task 15's record sweep.
The controller's requirement gives it a task, and the reason is in the design's own history: the last
slice to owe this entry appended a paragraph and left row 4 at `1`. A record sweep and a **correction to
a published figure** are two different reviews — one checks that every strike matches the code, the other
checks that three rows are repeated character for character and the fourth's re-derivation is argued.
Task 15 is **narrowed, not renumbered**.

**(b) Fixtures E and H move into task 4.** Stated as a constraint above; it is the design's own ruling
and it is repeated here because *a ruling that overrules a brief has to reach the brief.*

**(c) The guard pin gains a fifth arm, E.** The design's arm B is Fixture A's single-condition run,
seven keys. The correction-family half of § The behaviour change — the two-condition Holm run — is a
**different fixture with a different key list**, and this plan re-measured it (§ Corrections 9). Merging
the two into one "N keys move" phrase is exactly the carried-summary failure the feasibility analysis'
own corrections were written about, so it is a separate arm with its own literals and its own sole
editor.

---

## Batching — five batches, one report and one review each

**Every batch gets a review, including the last.** Twice a controller ran a slice's final batch straight
into the whole-branch gate, and the second time **three of four whole-branch Majors lived in it.**

| Batch | Tasks | The seam, and what its review must be able to see |
|---|---|---|
| **B1** | **1, 2, 3** | **The pin and the documents, before anything moves.** A capture check: every literal produced by **running**, never transcribed; arms A, C and D with **no authorized editor**; arm B's seven keys and arm E's key list enumerated in the docstring rather than counted; arm A's rule (*identity holds when no non-numeric column exists anywhere in the same correction family*) and what its fixture pins (*none anywhere in the run*) stated as **two labelled sentences**. And a **document-against-future-code** review: does any new sentence claim a behaviour the code will not have after B2? Is `W-STATS-REPEATS-DISAGREE`'s row true of the one site B2 will add? Mechanical pass on every `reference.md` edit. **Arm A's fixture must NOT use the default `STARTER_STEP`** — it records `{"present": True}`, a bool, which falsifies the arm's own premise |
| **B2** | **4, 5, 6** (carrying Fixtures E and H) | **THE BEHAVIOUR CHANGE. Its review must be a real-command review.** Run the installed console script end to end on Fixture A's project and on Fixture B's, and read `run.yaml` **key by key** against § The behaviour change's table — not `validate`, not a direct call. The previous slice family's only Critical was invisible to every direct-call probe. Then: is arm B's edit **exactly** the seven keys enumerated in advance, with every `score.*` literal and `mean_score.value` untouched? Is arm A still passing, untouched? Are the collision (Fixture E) and the empty-level gate (Fixture H) pinned **here** rather than promised to B3? Is the mixed-column rule of § Corrections 5 implemented as prescribed, and did the implementer **compute** the radius rather than accept the prescription? Re-run the whole suite and **report the actual moved-test list** — the scoping's "exactly two tests move" is dated to a shape with no across-repeats rule (§ Corrections 11) |
| **B3** | **7, 8, 9, 10, 11** | **The guards and the namespace.** Arm C's `git diff` line count over the two existing numeric-`by` tests — **report the number**. Does Fixture G's direct-call arm say **in its own docstring** that it drives a state production cannot reach, and does the end-to-end arm carry the production claim? Is the unpaired filter in `of_col`/`against_col` rather than in `of_values`/`against_values` (§ Corrections 2) — check `n_of` and the cluster mapping against the value vector. Were `_attributed`'s two grounds **deleted** rather than rewritten? |
| **B4** | **12, 13, 14** | **Pins over finished behaviour, and nothing new.** Does any assertion here pass if the behaviour is neutered? Grep every claim the briefs make about other tests **before repeating it** and **report what was grepped, not a count** — six consecutive slices reported zero disagreements and all six were wrong, and every one hid in a claim about other tests or other rows |
| **B5** | **15, 16** | **Filings, both consistency passes, and a correction to a published figure — reviewed, not skimmed.** Every struck entry checked against the code; every "filed" checked against the file; every re-owning stated as a fact with a reason and never as *"whichever slice next touches X"*; every sweep **naming its files**, never filtering its output, and **proven able to fail** by running it against a string known to be present. And: rows 1–3 of the four-row table repeated **character for character**, no fifth number, row 4's move **appended with what it replaces** |

---

## Global Constraints

Every task inherits all of these. They are copied verbatim rather than cross-referenced, because an
implementer sees only their own task brief.

**Commands.** Tests `uv run pytest`. Lint `uv run ruff check .`. Format `uv run ruff format .`. Types
`uv run mypy`. All four must pass before a commit. **Baseline at `ee8085e`: 2891 passed, 1 skipped, 2
xfailed; 93 files formatted; 52 source files typed.**

**No gate literal moves in this slice.** No task creates a file of any kind, so `ruff format --check`
stays **93** and `mypy` stays **52 source files** at every commit. **Every task states its own DELTA on
the test count, not an absolute**; compute the absolute from your own previous run and reconcile any
difference before committing. **Tasks 4 and 5 are the exception in one direction only**: they *change*
existing tests, so their delta is stated as *added minus removed*, and any test that changes its
assertions is named.

**Run `uv run pytest` DIRECTLY, in the foreground, and wait for it.** It takes about three minutes at
this baseline. **Never construct a wait, a monitor, a poll or a background run around it** — six agents
on preceding slices stalled that way and one stopped with a mutation still applied. Clear `__pycache__`
and any stale `pytest-of-*` temp directory before a run.

**Verify format with `uv run ruff format --check .`, never the bare form.** A previous brief in this repo
wrote the bare form where it meant `--check` and rewrote 67 files. **`ruff format` does not process
`.md`** — measured twice on preceding branches by copying a document, running the formatter and diffing
byte-identical; two agents nonetheless reverted documents on that misdiagnosis. **A revert is verified by
behaviour**, never by `git status`, and least of all by an account of what caused the change.
**`git checkout -- <file>` destroys uncommitted work** and has been mistaken for reverting a mutation
three times here. Keep a copy before mutating; restore by copying back; verify by behaviour.

**An `ExecutionResult`'s `recorded` field is a set of UNIT KEYS, not of column names.** This plan's
author built a probe that passed column names and measured `collapse_repeats` returning `{}` for a table
that today collapses four units — a fixture that fires for the wrong reason and would have made every
literal below wrong. `tests/test_stats.py::_result` gets this right
(`recorded=frozenset(r["unit"] for r in rows)`) and **is the helper every direct-call fixture here must
use.** *The sibling that already got it right is the first place to look.*

**Every task says whether its surface is `validate`, a real command, a direct call, or documents.** Where
a task's surface is a direct call, its brief says which later batch covers it through a real command.

**`aggregated` has two shipped readers and no hash.** `report.py` and `study.py` both walk it;
`code_hash`, `parameters_hash` and `input_manifest_hash` cover none of it, and **nothing in this slice
moves any hash.** Two consequences pull in opposite directions and every task must hold both. It makes
the readers cheap to check — task 14 does it end to end. And it means the change this slice makes is
**invisible to `diff`'s three hash rows**: the one row that moves is `uv.lock`, because upgrading
`publishable` is what delivers the new behaviour. The controller ruled that this is the honest carrier
and that nothing is minted to improve on it; the *disclosure* obligation is discharged in the ledger and
in `CLAUDE.md`, and the residual — that `diff`'s `uv.lock` detail lines do not name the moved package —
is **filed against H9** by task 15.

**What this slice does NOT touch, stated so no task folds it in** (on H4b-2's precedent):

- **The `report_by`-under-`resample` gap.** Converted 2026-08-18 to a documented permanent limitation,
  live on **seven** of the analysis' nine configs. `stats.py` is this slice's surface and the gap lives
  there. Not folded in; row 3 of the four-row table is repeated unchanged.
- **`repeat_spread`'s `std: 0.0`.** RE-OWNED 2026-08-21 to unassigned. This slice adds a function
  *beside* `repeat_spread` and changes nothing inside it.
- **A degenerate stratum's missing console warning.** Its filing still reads "H4 Statistics", an owner
  that no longer exists. **This slice neither corrects that ownership nor silently inherits it**; the
  scoping's ruling stands — it is for whoever next sweeps that file.
- **H3c-3's `fold_members`.** This slice changes what `collapse_repeats` **returns**, not how it
  intersects. Pinned by Fixture K in task 4, not merely named.
- **`BaseTemplate.field_convention`**, declarable on a shipped class and read by nothing. Named because
  § Misreadings calls it the sole remaining example of an unbuilt reader of a shipped surface, and an
  implementer reading `units.py` will meet it. Not H5b's.
- **`E-STEP-RETURN-TYPE` and the write side.** Decision 11 decides the read; the write stays strict.
  Task 3 files the residual **unassigned with a reason**.
- **`.csv`'s null encoding**, H5a's appended correction. Already filed, unassigned, not this surface.

**No positional row locators, no line-number citations, no count phrases where an enumeration is
possible.** Cite a document by section. Name what a sibling table row *does*. `×`, not `x`, for
multiplication. Hyphens, never en dashes, in anything that becomes an anchor.

---

## The fixtures this slice rests on, and where each one lives

The design's § The discriminating fixtures is the authority for their shapes. This table records where
each lands, because an implementer sees only their own brief. **A fixture is a claim too**: every
literal in every fixture below was computed by running something, and the task text names what.

| Fixture | What it claims | Task |
|---|---|---|
| **A** — the moving run, key by key | Seven keys move and `mean_score.value` does not | **1** (as pin arm B) and **4** |
| **A′** — the two-condition Holm run | The correction family moves: `n_paired`, both `correction_level`s, and a purely numeric column's `ci95_corrected` | **1** (as pin arm E) and **4** |
| **B** — the scaffold's own run, end to end | `aggregated == {}` unchanged; a template reading `units.present` gets `6.0` and no warning | **4** |
| **C** — repeats that disagree on a non-numeric column | The key is present and the cell is `None`; the warning names the column | **5** |
| **D** — repeats that agree on a recorded `None`, and its harder second arm | A recorded `None` and a collapsed disagreement are the same cell, so the rule cannot answer from the cell | **5** |
| **E** — the collision, driven from the collapse's own output | `E-STEP-KEY-COLLISION` fires from a `collapsed` a production caller can produce | **4** (pin) and **10** (documents) |
| **F** — a non-numeric `by` column, numeric arm as control | The warning fires and the strata are suppressed | **9** |
| **G** — the contrast guard, both ends | The subtraction is guarded where it happens, not by another function's output | **7** |
| **H** — the stratum's empty level | The second empty-level gate is reachable and holds | **4** (pin) and **11** (documents, record) |
| **I** — where the projection sits | Stripping at `summarize_step`'s input puts a point estimate outside its own interval | **6** |
| **J** — `report` and `study` as readers of `aggregated` | The additive-only half of the ruling, for the shipped commands | **14** |
| **K** — the fold path | Decision 1 changed what the function returns, nothing about how it intersects | **4** |
| **L** — the mixed column across repeats | A column numeric in one repeat and a string in another keeps today's published mean and gains the warning (§ Corrections 5) | **5** |
| **M** — `repeat_spread` under the widened `keys` | Widening `keys=set(collapsed)` moves no `repeat_spread` figure, on a fixture where it could (§ Corrections 6) | **4** |

---

## Task 1: the guard pin — five arms, captured before anything moves

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Runs FIRST, before every other task. Surface: direct calls to `stats.summarize_step` for arms B and
D, a real `run` through `main` for arms A, C and E.** H5b moves published numbers, and a literal
captured after a task has run records the move rather than the baseline. **Two arms have no authorized
editor at all, so a passing arm is itself the proof** — the answer to five slices weakening a pin
quietly, and to the two that pinned one list twice and edited both.

**Files:**
- Test: `tests/test_cli.py` (add), `tests/test_stats.py` (add)

**Interfaces:**
- Consumes: `run_a_project` and `_first_contrast` from `tests/test_cli.py`, `_result` from
  `tests/test_stats.py`, `stats.summarize_step`, `stats.collapse_repeats`.
- Produces: nothing importable. Arms every later task's suite run must keep green.

**What this pin deliberately does NOT re-capture, and why.** `run.yaml`'s top-level and `provenance` key
lists are already pinned by more than one shipped assertion, and `publishable.__all__` is already
asserted somewhere in the suite. H5b exports one new name (`repeats_disagreeing`, from `stats.py`, which
is **not** part of `publishable`'s importable surface and must not be added to it) and writes no new
record key. **Grep for those pins before writing anything, and report what you grepped rather than a
count** — *before writing "no existing test asserts X", grep for it* is the check that catches the shape
where six consecutive slices' reports claimed zero disagreements and all six were wrong.

- [ ] **Step 1: capture arm A — the numeric-only run's `results` block. NO AUTHORIZED EDITOR.**
      A two-condition, two-seed, Holm-corrected run over 40 units with **one numeric recorded column and
      one derived metric, and NO non-numeric recorded column anywhere in the run.** Assert the whole
      `results` mapping against a literal.
      **The default `STARTER_STEP` records `{"present": True}` — a bool — so `run_a_project` with no
      step override falsifies this arm's own premise and the arm would fire for the wrong reason.**
      Use `aggregate_returns=` (which swaps in `_AGGREGATE_STEP`'s float `pred` column) or an explicit
      numeric `_starter_step`; **grep the helper for `_AGGREGATE_STEP` and say in the docstring which
      you used and that the step records no bool.** **Say in the arm's own text that a second recorded
      column of any non-numeric type FALSIFIES this arm rather than failing it** — the arm would then be
      asserting identity over a run this slice legitimately moves, and the response is to fix the fixture,
      not the literal.
      **The docstring carries two labelled sentences, not one:**
      *The rule:* identity holds when no non-numeric column exists **anywhere in the same correction
      family**, because Holm ranks across the family and one metric's interval width moves another's
      corrected interval.
      *What this fixture pins:* the safe framing — **none anywhere in the run** — so that a later
      fixture edit cannot quietly turn the rule into the false loose one. The loose version is what the
      scoping falsified, and arm E is the measurement that falsified it.
      **No task in this slice edits this arm.** A passing arm A after every task is the proof that the
      numeric-only path did not move.

- [ ] **Step 2: capture arm B — Fixture A's seven moving keys, by RUNNING `summarize_step`.**
      Six units, `seed=7`, `draws=2000`. Units `u0`–`u3` recorded `{"score": float(i), "valid": True}`;
      units `u4`–`u5` recorded `{"valid": True}`. `counts = {"resolved": 6.0, "completed": 6.0,
      "ineligible": 0.0, "failed": 0.0}`. The template's `aggregate` returns `n_rows` (row count),
      `n_valid` (rows whose `valid` is `True`) and `mean_score` (mean of the `score` values present).
      **The `aggregate` must never return `None` on this table** — production passes whatever
      `coerce_scalars` returns and `if derived:` is a truthiness gate, so a `None` top-level value would
      be a shape this fixture measures and production reaches differently. On this table `mean_score` is
      `1.5`; the `None` branch exists only for a degenerate resample draw, which is what produces the
      `1998` below.
      Drive it **twice**: once over the `collapsed` today's `collapse_repeats` returns for those
      executions (`{u0..u3: {"score": …}}`, four units — computed by calling `collapse_repeats` on
      `_result`-built executions, **not** hand-written), and once over the wide `collapsed`
      (`{u0..u3: {"score": …, "valid": True}, u4..u5: {"valid": True}}`).
      **Assert these seven, and only these seven, as the moving set — enumerated, never counted:**

```
  KEY                          TODAY                         AFTER
  n_valid.value                0.0                           6.0
  n_valid.ci95                 [0.0, 0.0]                    [6.0, 6.0]
  n_rows.value                 4.0                           6.0
  n_rows.ci95                  [4.0, 4.0]                    [6.0, 6.0]
  mean_score.n.completed       4                             6
  mean_score.ci95              [0.5, 2.5]                    [0.3333333333333333, 2.5]
  mean_score.resample_draws    2000                          1998

  AND THESE MUST NOT MOVE:
  mean_score.value             1.5                           1.5
  score.value                  1.5                           1.5
  score.n.completed            4                             4
  score.ci95                   [-0.5542602567605206, 3.5542602567605206]   (identical)
  score.method                 t_over_units                  t_over_units
```

      Every literal above was produced by running `summarize_step` at `ee8085e` (this plan's probe `p1`).
      **`mean_score.value` unmoved is the load-bearing assertion nobody would think to write:** a fixture
      in which every number moves cannot tell *the table widened* from *the metric changed*.
      **`1998` is this fixture's number at `seed=7, draws=2000` and is not a constant** — the same shape
      run end to end at a run-derived seed gave `1999` (§ Corrections 7). Do not reuse it elsewhere.
      **Sole authorized editor: task 4.** Task 4 flips exactly those seven to the AFTER column, literal
      for literal, and edits nothing else in this arm. **Task 5 is not an editor of this arm**: Fixture A
      has no column that disagrees across repeats, so the collapse rule cannot reach it, and a task-5
      edit here is a **finding**, not a fixture repair.

- [ ] **Step 3: capture arm E — the correction family, by RUNNING the console path. Sole authorized
      editor: task 4.** A two-condition run (`sweep.baseline: {analysis.method: pearson}`,
      `grid: {analysis.method: [spearman]}`), six units, default five seeds, `correction: holm`, whose
      step records `{"score": float(i) + thr, "valid": True}` for `i < 4` and `{"valid": True}`
      otherwise, with `thr` `0.5` under pearson and `0.4` under spearman, and whose template's
      `aggregate` returns `n_rows` and `mean_score`. **This is a different fixture from arm B, with a
      different key list, and the two are never merged into one count.**

```
  KEY (condition `method=spearman` unless noted)          TODAY                    AFTER
  aggregated…n_rows.value / .n.completed                  4.0 / 4                  6.0 / 6
  aggregated…n_rows.ci95                                  [4.0, 4.0]               [6.0, 6.0]
  aggregated…mean_score.n.completed                       4                        6
  aggregated…mean_score.ci95 (baseline)                   [1.0, 3.0]               [0.8333333333333334, 3.1666666666666665]
  aggregated…mean_score.ci95 (spearman)                   [0.8999999999999999, 2.9] [0.7333333333333334, 3.0666666666666664]
  vs_baseline…mean_score.n_paired                         4                        6
  vs_baseline…mean_score.correction_level                 0.025                    0.05
  vs_baseline…mean_score.ci95 / .ci95_corrected           [-0.10000000000000009, -0.09999999999999998]
                                                                                   [-0.10000000000000053, -0.09999999999999964]
  vs_baseline…score.correction_level                      0.05                     0.025
  vs_baseline…score.ci95_corrected                        [-0.10000000000000014, -0.09999999999999998]
                                                                                   [-0.10000000000000017, -0.09999999999999995]

  AND THESE MUST NOT MOVE:
  aggregated…score.*  (value, n, ci95, method, repeat_spread)  identical in both conditions
  vs_baseline…score.n_paired                              4                        4
  vs_baseline…score.ci95                                  [-0.10000000000000014, -0.09999999999999998]
  vs_baseline…n_rows.correction_level                     0.016666666666666666     0.016666666666666666
```

      **Re-measured by this plan, not copied.** The scoping's three literals — `n_paired` 4 → 6, the
      `correction_level` swap, and `score.ci95_corrected` moving in its last digits — **all three
      reproduce at `ee8085e`**, and the re-measurement found **two the scoping's paragraph does not
      name**: the derived contrast's own `ci95` and `ci95_corrected` (§ Corrections 9). **`score`'s
      corrected interval moving is the whole point of this arm**: `score` carries no non-numeric value
      anywhere, and Holm ranks on the point estimate over half the raw `ci95` width, so the *other*
      metric's widening moves it. That is what makes arm A's loose framing false and its safe framing
      necessary.
      **Capture this arm by RUNNING the console path with the AFTER behaviour monkeypatched in**, the way
      this plan did (a `collapse_repeats` replacement installed on `publishable.cli`), and record the
      TODAY column from the unpatched run. **The monkeypatch does not ship**: the arm's committed form
      asserts the TODAY column, and task 4 flips it.

- [ ] **Step 3b: capture arm F — a DERIVED metric's permutation p-value moves, and a recorded column's
      and a contrast's do not. Sole authorized editor: task 4.** Fixture A's two tables again, this time
      with `null_test={"method": "permutation", "n": 500, "shuffle": "grp", "level": "rows"}`, `labels`
      mapping each unit to `"a"`/`"b"` by parity, `seed=7`, and a `null_fn` per key that reads the
      **relabelled mapping** (a one-argument closure cannot express a permutation here —
      `permutation_of_derived`'s docstring says why, and a closure ignoring `labels` returns `None` for
      every key, measured).

```
  KEY                                   TODAY (4 units)        AFTER (6 units)
  mean_score.p_value                    0.846307385229541      0.812375249500998
  mean_score.null_draws                 500                    500

  AND THESE MUST NOT MOVE (they have no p_value at all):
  score.p_value / .null_draws           None / None            None / None
```

      Measured at `ee8085e` (§ Corrections 16). **Why this arm exists:** the design and the scoping both
      enumerate the moving keys and **neither names `p_value`**, and `permutation_of_derived` takes the
      whole `collapsed` and rebuilds each draw's table from whole rows — the same mechanism that moves
      `mean_score.ci95`. **Why it is a separate arm rather than more keys on arm B:** arm B's fixture
      declares no `null_test`, and adding one would change the block shape every one of its seven literals
      was captured from.
      **State the asymmetry in the docstring, and state which half was reasoned:** a **recorded column**
      gets no `p_value` from `summarize_step` at all (read: the write is in the derived branch only,
      confirmed by grepping `p_value` in `stats.py` over the column loop's range → nothing); and a
      **contrast's** p-value comes from `permutation_over_contrast` over `of_values`/`against_values` in
      the **unpaired recorded-column** arm, which task 7 narrows — so it does not widen. **The contrast
      half was read, not run**; if the reader wants it run, one direct call settles it.
      **No row of the four-row table moves on this**: all eight `statistics` blocks in the feasibility
      analysis carry `null_test: null`, which the truthy guard treats as undeclared.

- [ ] **Step 4: capture arm C — the numeric `by` column keeps its metric block and its warning. NO
      AUTHORIZED EDITOR.** `tests/test_cli.py::test_a_recorded_column_named_by_keeps_its_metric_and_warns`
      and `::test_a_recorded_by_column_warns_even_with_no_report_by_declared`, both asserting
      `aggregated[step]["by"]["value"] == 39.0`. **Grep for both names and quote the assertion you
      found; do not add a third copy.** This arm is the statement that **zero lines of those two test
      bodies change in this slice** — the B3 review reports the `git diff` line count over both bodies,
      and the number must be `0`. **Related but distinct, and it is NOT this arm's:**
      `tests/test_artifacts.py::test_a_measured_by_column_survives_the_collapse_into_units_parquet`
      records a **non-numeric** `by` column at the artifact layer and never reaches `collapse_repeats`
      (§ Corrections 1) — it must also stay green, and task 9's brief names it.

- [ ] **Step 5: capture arm D — the two behaviours this slice narrows AROUND and must not narrow AWAY.
      NO AUTHORIZED EDITOR.** By direct call to `summarize_step`:
      (i) `E-STEP-COLUMN-UNKNOWN` still raises for a name **no** row holds — through `UnitTable`, on a
      table that does hold other columns, so the fixture cannot fire on an empty table instead;
      (ii) the derived-key collision still raises `E-STEP-KEY-COLLISION` for a **numeric** recorded
      column. Assert the codes, not the wording.

- [ ] **Step 6: run.** `uv run pytest` → **2891 + your new tests** passed, 1 skipped, 2 xfailed.
      `uv run mypy` → still **52 source files**; `uv run ruff format --check .` → still **93 files**.

- [ ] **Step 7: the mutations — five, because one arm proving itself proves nothing about another.**
      Keep a copy of every file you mutate; restore by copying back; verify by **behaviour**.
      (i) In `stats.collapse_repeats`, delete `or not _is_numeric(value)` from the inner loop's skip.
      **Arm B's TODAY column must FAIL** and arm A must **PASS**. *Why the branches differ:* arm B's
      fixture has two units whose only value is a bool; arm A's run has none.
      (ii) In `stats.summarize_step`'s column loop, delete the `all(_is_numeric(v) for v in raw)` clause.
      **Arm B's AFTER-side key set must FAIL** (a `valid` metric block appears). *Why the branches
      differ:* measured — the clause is the projection, and the wide table carries a bool column.
      (iii) In `cli.py`, change the `by` gate from `if "by" in step_summary` to `if False`. **Arm C's
      warning assertion must FAIL.** *Why the branches differ:* the numeric `by` column reaches
      `step_summary` today, measured by the scoping both ways.
      (iv) In `correction.py`, reverse the Holm rank ordering. **Arm E's `correction_level` assertions
      must FAIL** for both metrics. *Why the branches differ:* the two metrics' levels are `0.025` and
      `0.05`, distinct literals in the captured arm.
      (v) In `stats.py`'s `UnitTable.__getattr__`, return an all-`None` column instead of raising.
      **Arm D(i) must FAIL.** *Why the branches differ:* arm D asserts a raise, and nothing else in this
      pin does.
      **Named blind in advance, with its replacement:** no mutation is proposed for arm B's *unmoved*
      literals as a group, because any mutation that moves `score.*` also moves arm A. Their replacement
      is mutation (i) above, which moves the moving keys and leaves the unmoved ones alone — the
      discrimination arm B exists for.

- [ ] **Step 8: commit.** `git add -A && git commit -m "H5b task 1: pin the numeric-only run, the two
      moving runs, the numeric by column and the two narrowed-around refusals before anything moves"`.

---

## Task 2: § Templates states what the collapsed table carries

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Surface: documents.** Design Decision 10. **The sentence is not narrowed — it is made true for the
first time**, so no argument against `design-principles.md` is owed. `H5-SCOPING` task 10's premise
(*"narrowing it needs an argument"*) was wrong, and the design says so.

**Files:** `docs/reference.md`

**The section is `Templates: where parameters are defined`, anchor
`#templates-where-parameters-are-defined` — NOT the later `## Templates` section, which is the
`my_assay` parameter table.** Two headings in this file answer to "§ Templates" and the design cites the
first. **Grep for the sentence rather than for the heading:** `grep -n 'Columns are whatever the step'
docs/reference.md` returns exactly one line, and that paragraph is the target (§ Corrections 8).

- [ ] **Step 1.** The paragraph already reads *"Columns are whatever the step recorded plus every
      declared unit attribute"* and already says of a declared attribute *"A declared attribute is
      carried through **unchanged** rather than averaged … It is a column here and nothing else — never
      a metric."* **Add the recorded-column half beside it, in the same shape**, stating three things:
      a recorded column that is not a number is carried too; across a unit's repeats it collapses to its
      value when every repeat agreed and to `None` when they did not, because a non-numeric column has
      no average and `data.units.measurements.collapse` governs measurements rather than repeats; and it
      is a column and never a metric, for the reason § Statistical reporting gives.
      **Do not restate the four-operation contract, and do not touch it.**

- [ ] **Step 2.** Link the collapse sentence to [§ What isn't a repeat](../../reference.md#what-isnt-a-repeat), whose
      *"Attributes constant within a key collapse to that value with no rule needed"* is the rule this
      reuses, and to § Warnings core reports for the disclosure. **Verify both anchors resolve** by
      grepping the headings; a `#anchor` that does not exist is a mechanical-pass failure.

- [ ] **Step 3: the mechanical pass on this edit only.** Every relative link and `#anchor` resolves; no
      trailing whitespace, tab or invisible unicode; no table row's column count changed; `×` not `x`.
      **Skip fenced blocks.**

- [ ] **Step 4: the cross-document pass on this edit only.** Two classes can bite here. **Config
      completeness:** this edit names no new config field, so nothing is owed to § The one config file —
      **check that claim by grepping your own diff for a backticked `data.` or `statistics.` path and
      confirming each already appears there.** **Declared vs. derived:** the collapse rule describes a
      derived value; grep the four documents by name for any passage showing a repeat-level collapse
      rule as a *settable* input, and report what you grepped.

- [ ] **Step 5.** No mutation: a document has no behaviour. **Named blind in advance.** Its replacement
      is task 4's Fixture A and task 5's Fixtures C, D and L, which pin the behaviour this sentence
      describes, plus the B1 review's document-against-future-code read.

- [ ] **Step 6: run** the four commands (no test delta) and **commit**: `H5b task 2: § Templates states
      that a non-numeric recorded column is carried, and how it collapses across repeats`.

---

## Task 3: § The per-unit tables' routed question decided, § Statistical reporting, and `W-STATS-REPEATS-DISAGREE` minted

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Surface: documents. Runs before any code reports the warning** — the documents lead, and a § Warnings
row is normative specification rather than a build claim.

**Files:** `docs/reference.md`, `docs/superpowers/spec-defects.md`

- [ ] **Step 1: § The per-unit tables — decide the routed mixed-type question (Decision 11).** The
      section currently ends the paragraph about a column that is `str` for some units and a number for
      others with *"The more forgiving reading … is a live question for how the table `aggregate`
      receives should treat such a column, and is not decided here."* **Replace the open clause with the
      decision**: on the **read** side a column is published as a metric only when **every** value
      carried for it is a real number, so one string in a column of floats costs that column its metric
      block and nothing else — the column still reaches `aggregate`, where a template that knows what
      the mixture means can use it. On the **write** side `E-STEP-RETURN-TYPE` is **not** loosened,
      because loosening it would make a column's published-or-not status depend on the data rather than
      on the config: one run of a config would publish a metric and the next would not, with no
      diagnostic distinguishing them.
      **This is the total rule over however a mixed column arises**, which is what makes it a decision
      rather than a reachability claim — measured: `summarize_step` over a column with **one** `None`
      cell and five floats publishes **no** metric block for it at all (this plan's probe `p3`).

- [ ] **Step 2: § Statistical reporting states what `aggregated` may not hold.** A metric block's `value`
      is a number, so a recorded column earns a block only when every value carried for it is a real
      number. **One sentence, in the section that already defines the metric block**, and it must not
      contradict the `basis: repeats` and `reported: true` cases the section already carries — read them
      first and say in the report which you read.

- [ ] **Step 3: mint `W-STATS-REPEATS-DISAGREE` in § Warnings core reports.** **One row, covering its
      single emit site.** Place it among the `W-STATS-*` rows by code — its siblings are
      `W-STATS-NULLTEST-FAMILY` and `W-STATS-REPORTBY-THIN`; **locate them by their codes, never by
      position.** The row states the condition, not the wording: *a step's recorded column is not a
      number and disagrees across the repeats of at least one unit, so that unit's cell is `None`; the
      per-repeat `units.parquet` files still hold every observation, and the declared route for a
      within-unit collapse is `data.units.measurements`.* Fires at **`run`** time.
      **Why one site is the whole story, established by reading and then confirmed:** the aggregation
      phase collapses once per (condition, step); the stratum loop re-filters the same `collapsed` rather
      than collapsing again. Confirmed by `grep -n 'collapse_repeats(' src/publishable/*.py` → **one**
      production call site plus the definition. **Run that grep yourself and report it** — a diagnostic's
      unit of work is every site that raises *or* reports it, and a task scoped by a helper's single call
      site has already missed a second site once in this repo.

- [ ] **Step 4: three § Errors rows are asserted, not edited. Read each emit site, then grep.** In that
      order — the reverse is the substitution § Answering a question with a proxy is about.
      `E-STEP-KEY-COLLISION`: its row already names *"a derived key against a recorded column"* and
      already says this site is re-reported as `W-STATS-AGGREGATE-FAILED` rather than raised; **no emit
      site is added, the same site sees a wider input, so the row does not move.**
      `E-STEP-COLUMN-UNKNOWN`: its row describes *"a column no row of the unit table holds"*, which
      stays exactly true as the held set widens. **No change.**
      `E-STEP-RETURN-TYPE`: **no change** — step 1 decides the read and leaves the write strict.
      **Report the greps and the sites, and if a row turns out narrower than its code, that is a finding
      and it is filed rather than quietly widened.**

- [ ] **Step 5: file the write-side residual, unassigned with a reason.** `spec-defects.md` gets a new
      entry: *whether `E-STEP-RETURN-TYPE` should ever be forgiving for a genuinely mixed `.parquet`
      column.* **Owner: unassigned, with the reason** — no remaining slice (H6, H9, H3c-3's remaining 14)
      has the write side as its surface, and H5a is merged. **Name in the entry that H5a's design said of
      this question "Filed, not built, owner H5b" and that no such filing existed** —
      `grep -n 'more forgiving' docs/superpowers/spec-defects.md` → **0 lines** at `ee8085e`, control
      `grep -c 'E-STEP-RETURN-TYPE' docs/superpowers/spec-defects.md` → **4**, so the sweep can hit.
      **Run both and report them.** *A design line saying "Filed" is not a filing* — second instance in
      one slice pair, and saying so is part of the entry.

- [ ] **Step 6: both consistency passes on these edits**, in the shape task 2's steps 3 and 4 give.
      **Enum comments:** grep for any inline `# a | b | c` comment listing warning or error codes and
      confirm none enumerates the `W-STATS-*` set — if one does, it gains the new code.

- [ ] **Step 7.** No mutation; **named blind in advance** for the same reason task 2's is. Its
      replacement is task 5's Fixtures C and D, which pin the warning at its site, and the B1 review's
      *is the mint's row true of the site batch 2 will add?* check.

- [ ] **Step 8: run** the four commands (no test delta) and **commit**: `H5b task 3: decide the mixed
      column's read, state what aggregated may not hold, mint W-STATS-REPEATS-DISAGREE, file the write
      side`.

---

## Task 4: the collapse carries every recorded value and admits every unit it was handed

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**THE BEHAVIOUR CHANGE. Surface: a direct call and a real `run`, both.** Design Decisions 1, 5 and 6.
This task also **carries Fixtures E, H and K and the pins the scoping put in tasks 10 and 11** — a live
overruling from the design's § What each change makes reachable, restated here because *a ruling that
overrules a brief has to reach the brief.*

**Files:**
- Source: `src/publishable/stats.py`, `src/publishable/cli.py` (annotations only)
- Test: `tests/test_stats.py`, `tests/test_cli.py`

- [ ] **Step 1: extract the repeat walk once, so it has one implementation and two readers.** In
      `stats.py`, lift `collapse_repeats`' gathering into a module-private helper and leave
      `collapse_repeats` as its reader. **This is what lets task 5's `repeats_disagreeing` ask the rows
      the same question without a second walk that can drift** — and it is why the design's *"plus the
      unit keys"* parameter is unnecessary (§ Corrections 3).

```python
def _gather_repeats(
    results: "list[ExecutionResult]",
    step_name: str,
    condition_index: int,
    fold_members: dict[str, frozenset[str]] | None,
) -> dict[str, dict[str, list[Any]]]:
    """Every value each admitted unit recorded for each column, across the repeats
    it was handed — raw, uncoerced, in the order `sorted(candidates)` fixes.

    One walk, two readers: `collapse_repeats` turns it into one row per unit, and
    `repeats_disagreeing` asks it which columns disagreed. A second walk would be a
    second implementation of the membership rule, and the two would drift.
    """
    recording = [
        r
        for r in results
        if r.execution.step_name == step_name
        and r.execution.scope == "repeat"
        and r.execution.condition_index == condition_index
    ]
    if not recording:
        return {}
    rows_by_label: dict[str, list[dict[str, Any]]] = {}
    recorded_by_label: dict[str, set[str]] = {}
    for r in recording:
        label = r.execution.repeat_label or ""
        rows_by_label.setdefault(label, []).extend(r.rows)
        recorded_by_label.setdefault(label, set()).update(r.recorded)
    labels = list(recorded_by_label)
    candidates: set[str] = set()
    for keys in recorded_by_label.values():
        candidates |= keys

    gathered: dict[str, dict[str, list[Any]]] = {}
    for key in sorted(candidates):
        mine = handed_to(key, labels, fold_members)
        if not mine or any(key not in recorded_by_label[lb] for lb in mine):
            continue
        # The unit passed the membership gate, so it IS a unit. It gets a row even
        # when every value it recorded is non-numeric, and even when it recorded no
        # column at all — `io.record(key, {})` settles a unit and records nothing,
        # which is reachable (measured). `runner.attrition` already counts such a
        # unit `completed`; this was the one place in the program that did not.
        gathered.setdefault(key, {})
        for lb in mine:
            for row in rows_by_label[lb]:
                if row["unit"] != key:
                    continue
                for column, value in row.items():
                    # `unit` is the key, not a measurement. `cli._attributed` is what
                    # puts the key column back for a bootstrap draw that duplicates
                    # units; it is never a column of `collapsed`.
                    if column == "unit":
                        continue
                    gathered[key].setdefault(column, []).append(value)
    return gathered
```

      **Preserve every comment the original loop carried**, in particular the two whose reasons are still
      true: `sorted(candidates)` is load-bearing because `summarize_step` derives a metric's column order
      from this dict and `order: randomized` decides encounter order; and the accumulation rather than a
      comprehension is what makes two executions sharing one repeat label merge rather than overwrite.
      **Delete nothing you cannot argue is false.**

- [ ] **Step 2: `collapse_repeats` reads the walk and averages what it can.**

```python
def collapse_repeats(
    results: "list[ExecutionResult]",
    step_name: str,
    condition_index: int,
    fold_members: dict[str, frozenset[str]] | None = None,
) -> dict[str, dict[str, Any]]:
    gathered = _gather_repeats(results, step_name, condition_index, fold_members)
    return {
        key: {col: _across_repeats(vals) for col, vals in cols.items()}
        for key, cols in gathered.items()
    }
```

      and the rule itself, in `stats.py` beside `_is_numeric`:

```python
def _across_repeats(values: list[Any]) -> Any:
    """One unit's values for one column, collapsed across the repeats it was handed.

    Three cases, and the third is the one that keeps a published number where it is.

    - Every value a real number: the mean, which is what this function has always
      done and the only case a purely numeric run reaches.
    - SOME values numbers: the mean of those, which is EXACTLY today's arithmetic —
      today's inner loop skipped the non-numeric ones and averaged the rest. Moving
      this to `None` would cost the whole column its metric block, for every unit,
      because `summarize_step` requires *all* carried values numeric (measured). That
      is a published column deleted, which no decision here argues for; the
      disagreement is disclosed instead, by `repeats_disagreeing`.
    - NO value a number: the value itself when the repeats agreed, `None` when they
      did not. `first` and `mode` are rules the user declared for `measurements` and
      never for repeats, and both are order-dependent here — `_gather_repeats`
      iterates in execution order, which `order: randomized` shuffles — so picking
      one would put the shuffle into a published column, the exact fault
      `sorted(candidates)` exists to keep out.

    `None` rather than omitting the key: omission would remove the column from
    `summarize_step`'s `columns` list when every unit disagreed, and `columns` is
    what the derived-key collision check reads — so omission reopens the silent
    coexistence defect through a second door. `_is_numeric(None)` is `False`, so a
    `None` cell keeps the column visible and unpublishable. Measured: the collision
    fires for a column whose every cell is `None`.

    `reference.md` § What isn't a repeat's *"Attributes constant within a key
    collapse to that value with no rule needed"* is the rule reused here, and
    `units.apply_rule` is the sibling that implements it for `measurements`. It is
    deliberately NOT called: it takes a rule name, every name it accepts returns a
    value on disagreement, and there is no declared rule for repeats to pass it.
    """
    numeric = [float(v) for v in values if _is_numeric(v)]
    if numeric:
        return sum(numeric) / len(numeric)
    if _repeats_disagree(values):
        return None
    return values[0]


def _repeats_disagree(values: list[Any]) -> bool:
    """Whether a unit's repeats disagreed about a non-numeric column.

    Pairwise against the first value, on `(is-it-a-number, the value)` rather than on
    the value alone: `True == 1.0` in Python, so a column recorded as `True` in one
    repeat and `1.0` in another would read as constant and collapse to whichever
    arrived first — order-dependent, which is what this rule refuses. Compared
    pairwise rather than through a set, so nothing here depends on a recorded value
    being hashable.

    All-numeric columns are excluded: unequal numbers are what averaging is for, and
    reporting them as a disagreement would fire on every honest run.
    """
    if all(_is_numeric(v) for v in values):
        return False
    first = values[0]
    return any((_is_numeric(v), v) != (_is_numeric(first), first) for v in values)
```

      **`_repeats_disagree` is a `stats.py` private and task 5's public `repeats_disagreeing` is what
      reads it.** Writing the predicate here rather than in `units.py` is deliberate: a shared helper
      would couple the measurements rule to the repeats rule, and a future edit to one would silently
      move the other.

- [ ] **Step 3: sweep the 20 annotation sites.** `grep -rn 'dict\[str, dict\[str, float\]\]'
      src/publishable/*.py | wc -l` → **20** at `ee8085e` (16 `stats.py`, 4 `cli.py`), re-run and report
      it. Each becomes `dict[str, dict[str, Any]]`. **Filter the file list, never the output.** The
      widened type is `Any` and **not** a `Scalar` union, because every arithmetic consumer re-narrows at
      runtime through `_is_numeric`, which mypy cannot see: a union would trade twenty annotations for a
      dozen `cast`s asserting the same runtime fact twice. `uv run mypy` is this step's check — **an
      annotation change has no observable behaviour, so a mutation for it is one whose two branches
      cannot differ, and it is named blind here rather than invented** (its replacement is task 7's
      mutation, which pins the runtime narrowing the annotation stopped expressing).

- [ ] **Step 4: Fixture A, and the arm B flip.** Drive `summarize_step` over a `collapsed` produced by
      calling the **new** `collapse_repeats` on `_result`-built executions (`recorded` = **unit keys**),
      and assert the AFTER column of task 1's arm B — the seven moved literals **and** the five that must
      not move. **Then edit arm B in `tests/`, flipping exactly those seven and nothing else.** You are
      that arm's **sole authorized editor**. Arms A, C, D and E: **do not touch** (arm E is yours in
      step 5). If arm A fails, stop — a numeric-only run moved and that is a defect, not a pin to edit.

- [ ] **Step 5: the arm E flip, through a real command.** Run the console script on arm E's project and
      read `run.yaml` **key by key** against arm E's AFTER column. Flip arm E's literals. **`score`'s
      `ci95` and `n_paired` must not move and `score.ci95_corrected` must**; if the corrected interval
      does not move, that is a **finding** — the correction family did not see the widening — and it is
      reported rather than smoothed.

- [ ] **Step 6: Fixture B — the scaffold's own run, end to end.** With `STARTER_STEP` unmodified and six
      units: `aggregated.step01_summarize_units == {}` **before and after** (Decision 12 — `generic`
      inherits `BaseTemplate.aggregate` returning `{}`, so the scaffold's symptom does not move), and,
      with a project-local template whose `aggregate` returns
      `{"n_present": float(len([r for r in units if r.get("present")]))}`, the value is **`6.0`** and no
      `W-STATS-AGGREGATE-FAILED` appears **on stdout** — the stream every shipped assertion on a run
      finding reads. Today the same project publishes `0.0` at exit 0.
      **The control that can fail:** a template reading `units.absent_column` still earns
      `E-STEP-COLUMN-UNKNOWN` under `W-STATS-AGGREGATE-FAILED`. **Without it this fixture asserts only
      absences and would pass identically if nothing ran.**

- [ ] **Step 7: Fixture E — the collision, driven from the collapse's own output.** `collapse_repeats`
      over executions recording `{"score": float(i), "r": True}`, its return fed to
      `summarize_step(…, derived={"r": 1.0})`, asserting `E-STEP-KEY-COLLISION`. **This is the pin, not
      the rewrite** — task 10 owns the shipped test's fixture replacement and the § Errors assertion.
      **Second arm, and it is the one that pins Decision 2's `None` choice:** a colliding column that
      **disagrees** across repeats, so its cell is `None` and the collision must still fire. Measured at
      `ee8085e`: it does.
      **Plus the end-to-end arm:** a real run whose template returns a colliding key publishes no `r`
      metric, warns, and **writes its `run.yaml`** — the containment is already right and is not touched.

- [ ] **Step 8: Fixture H — the stratum's empty level.** A run with `report_by` on an attribute one of
      whose levels contains **only** units whose every recorded value is non-numeric, and a template
      returning one derived metric. Assert that level is **absent** from the `by` block while the other
      level is **present**. **The presence half is what stops this from being an absence-only control.**

- [ ] **Step 9: Fixture K — the fold path.** Re-assert the existing `fold_members` collapse fixture over
      a roster where one fold's units record only a bool: each such unit is admitted **within its own
      fold**, and `handed_to`'s intersection is unchanged. **Grep for the existing fixture by name and
      extend it rather than writing a second one**; report what you grepped. The claim is that this task
      changed what the function **returns** and nothing about how it **intersects** — H3c-3's contact
      point, pinned rather than named.

- [ ] **Step 10: Fixture M — `repeat_spread` under the widened `keys`.** `cli.py` passes
      `keys=set(collapsed)`, which goes 4 → 6 in Fixture A's shape while the column's own `n` stays 4.
      **The gate that holds is `_repeat_spread_entries`' own `_is_numeric(row[column])` filter, and a
      fixture whose repeats record identical scores cannot see whether it held** — `std: 0.0` agrees
      with the bug. So: two repeats recording `score` **2.0 apart**, four units carrying it, two units
      carrying only a bool. Measured at `ee8085e` (this plan's probe `p5`): `{'std': 1.0, 'n': 2, 'kind':
      'seed'}` under the narrow keys and **identical** under the wide ones. Assert both.

- [ ] **Step 11: run the whole suite and REPORT THE MOVED TESTS BY NAME.** The scoping measured *"exactly
      two tests move"* under a shape that carried values and admitted units but had **no across-repeats
      rule and no mixed-column rule** — that figure is dated to `5ee3a0c` and to that shape, and it is
      **not** a prediction about this branch (§ Corrections 11). Expect
      `tests/test_stats.py::test_collapse_drops_a_bool_column_rather_than_averaging_it` (task 5 owns its
      replacement) and
      `::test_a_derived_key_colliding_with_a_dropped_non_numeric_column_is_refused` (task 10 owns its
      fixture). **Any third is a finding**: name it, say whether it pins the defect or a real guarantee,
      and do not edit a test whose guarantee is real without saying so in the report.
      **Do not "fix" `test_collapse_drops_a_bool_column_rather_than_averaging_it` here** — it asserts
      `"flag" not in collapsed.get("p0", {})` and passes today because `p0` is not in `collapsed` **at
      all** (§ Corrections 12), so it is a pin of the unit drop wearing the name of a column drop. Task 5
      replaces it, and this task's suite run may leave it failing between the two commits **only if that
      is stated in the report** — otherwise mark it `xfail` with task 5 named as its remover.

- [ ] **Step 12: the mutations — four, each with the assertion that catches it and two branches that can
      differ.**
      (i) Restore `or not _is_numeric(value)` in `_gather_repeats`' inner loop. **Fixture A's
      `n_valid.value` (`6.0` vs `0.0`) and Fixture B's `n_present` (`6.0` vs `0.0`) must FAIL.** *Why
      the branches differ:* measured — that exact input yields `{}` for a bool-only roster and drops two
      units in Fixture A's.
      (ii) Admit only units with at least one **numeric** value (keep the carriage, drop the admission):
      `if not gathered.get(key): gathered.pop(key, None)`-shaped, or `gathered.setdefault` moved back
      inside the value loop. **Fixture A's `n_rows.value` (`6.0` vs `4.0`) and
      `mean_score.n.completed` must FAIL.** *Why the branches differ:* the two rules differ **exactly**
      on units `u4`/`u5`, which carry a value and no number — the case a single-arm fixture would miss,
      and the reason Fixture A has both kinds of unit.
      (iii) Replace `cli.py`'s second empty-level gate (`if set(level_summary) - set(level_derived or
      {}):`) with `if True:`. **Fixture H's absent-level assertion must FAIL.** *Why the branches
      differ:* measured at `5ee3a0c` — this mutation leaves the **whole suite** green today, and it stops
      being blind at this task. **That is the point of pinning it here rather than in batch 3.**
      (iv) In Fixture E's second arm, make `_across_repeats` omit the key instead of returning `None` for
      a disagreeing non-numeric column. **The collision assertion must FAIL** — omission removes the
      column from `columns`, so the check stops seeing it. *Why the branches differ:* measured — the
      collision fires for an all-`None` column and cannot fire for an absent one.
      **Named blind in advance, with replacements:** the annotation sweep (step 3), replaced by task 7's
      mutation; and the docstring/comment edits in steps 1–2, replaced by the B2 review reading each
      comment against the code it sits on. *If a comment says this cannot happen, make it happen.*

- [ ] **Step 13: run** the four commands. **Delta:** Fixtures A, B, E, H, K, M added; `mypy` still 52
      source files; `ruff format --check` still 93. **Commit:** `H5b task 4: the collapse carries every
      recorded value and admits every unit it was handed`.

**What this task must NOT touch.** `summarize_step`'s body (task 6 deletes one docstring clause and
nothing else); `cli.py`'s contrast arms (task 7); `cli.py`'s `by` gate (task 9); `STARTER_STEP`
(Decision 12 refuses it); `paired_keys` and `unpaired_keys` (Decision 6 rules that a unit with no
numeric column **does** enter the intersection, and the per-column arms already narrow — no code
change); pin arms A, C and D (**no authorized editor**).

---

## Task 5: the disagreement is disclosed from the ROWS, never from the collapsed cell

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Surface: a direct call and a real `run`.** Design Decisions 2 and 3.

**The obvious design is wrong and was measured wrong.** A first draft said *a `None` value can only be
produced by the disagreement rule, so `cli.py` can warn by scanning `collapsed`.* Measured:
`coerce_scalars({"valid": None}, where=…)` returns `{'valid': None}` unchanged, and § The per-unit tables
states that a recorded cell may hold `None` and that a column of all `None` round-trips. **A recorded
`None` and a collapsed disagreement are the same cell**, so warning from the cell answers the question
with a proxy — the fault § Answering a question with a proxy records six times.

**Files:**
- Source: `src/publishable/stats.py`, `src/publishable/cli.py`
- Test: `tests/test_stats.py`, `tests/test_cli.py`

- [ ] **Step 1: the pure function, in `stats.py` beside `repeat_spread`.** `repeat_spread` is the sibling
      that already got it right: a separate pure function over `results`, called from `cli.py` beside the
      collapse, for a per-column across-repeats fact, with the warning living at the call site.
      **`stats.py` imports no findings channel and must not gain one.**

```python
def repeats_disagreeing(
    results: "list[ExecutionResult]",
    step_name: str,
    condition_index: int,
    fold_members: dict[str, frozenset[str]] | None = None,
) -> dict[str, int]:
    """Column name → how many admitted units disagreed about it across their repeats.

    Asks the ROWS, not the collapsed cell. A recorded `None` and a collapsed
    disagreement are the same cell (`coerce_scalars` leaves `None` alone, and
    `reference.md` § The per-unit tables makes an all-`None` column legal), so a
    scan of `collapsed` would answer this question with a proxy and give one answer
    to two different facts.

    The same four arguments `collapse_repeats` takes, over the same `_gather_repeats`
    walk, so membership has one implementation. Sorted keys, so the warning order is
    a property of the roster rather than of the shuffle — the reason
    `_gather_repeats` sorts.

    A column whose values are all numbers never appears here: unequal numbers are
    what averaging is for. A column that is numeric in some repeats and a string in
    others DOES appear, and its collapsed cell is still the mean of the numbers —
    the disclosure is the warning, not the loss of the column (`_across_repeats`
    says why).
    """
    gathered = _gather_repeats(results, step_name, condition_index, fold_members)
    counts: dict[str, int] = {}
    for cols in gathered.values():
        for column, values in cols.items():
            if _repeats_disagree(values):
                counts[column] = counts.get(column, 0) + 1
    return {column: counts[column] for column in sorted(counts)}
```

      **Not exported from `publishable`.** § The importable surface is an enumerated list and this is not
      on it; `stats.py` is implementation detail. **Grep `src/publishable/__init__.py` for `repeat_spread`
      and confirm it is absent** — that is the precedent, and report the grep.

- [ ] **Step 2: the one call site, in `cli.py`'s aggregation phase.** Immediately after
      `collapsed = collapse_repeats(...)`, before `counts`:

```python
                    for column, units_count in repeats_disagreeing(
                        results, step_name, cond.index, fold_members=fold_members
                    ).items():
                        aggregate_c.warn(
                            "W-STATS-REPEATS-DISAGREE",
                            aggregate_where,
                            f"condition {cond.index} step {step_name!r}: recorded column "
                            f"{column!r} is not a number and disagrees across the repeats of "
                            f"{units_count} unit(s), so those units carry no value for it; "
                            "declare data.units.measurements.collapse if the within-unit "
                            "collapse is what you meant",
                        )
```

      **`aggregate_where`, and the reason is the sibling row's own.** The fault is the recorded column,
      not `aggregate`, and `W-STATS-STRATUM-SHADOWED` — the other recorded-column finding in this same
      loop — already uses `aggregate_where` with that stated. `data.units.measurements` was considered
      and rejected as the `where` for exactly the reason the `by` row gives for not pointing at
      `statistics.report_by`: **there may be no such key in the file to point at.** Inventing a second
      convention for one class of fault is the two-sources-of-truth move.
      **Add `repeats_disagreeing` to `cli.py`'s `from publishable.stats import (…)` block**, in the
      block's existing alphabetical order.

- [ ] **Step 3: replace `test_collapse_drops_a_bool_column_rather_than_averaging_it` with Fixture C.**
      One unit, two repeats, recording `{"flag": True}` and `{"flag": False}`. Assert
      `collapsed["p0"]["flag"] is None` — **the key present and the value `None`, two assertions, not
      one** — and, through a real run, that `W-STATS-REPEATS-DISAGREE` names `flag` **on stdout**.
      `values[0]` is `True`, so a mutant carrying the first value gives `True`, which `is None` separates.
      **This is a CORRECT move, not a weakening, and the replacement says so in its own docstring**: the
      old assertion (`"flag" not in collapsed.get("p0", {})`) pinned the behaviour that **is** the defect,
      and it passed today because `p0` was not in `collapsed` at all — so its name described a column
      drop while its subject was a unit drop. **Keep the old test's name discoverable**: the new test's
      docstring names it, so a reader grepping for it lands here.

- [ ] **Step 4: Fixture D — the control Decision 3 rests on, and its harder second arm.**
      *Arm 1:* two repeats **both** recording `{"valid": None}`. Assert the cell is `None` **and that
      `W-STATS-REPEATS-DISAGREE` does not fire** — asserted on the run's **stdout**, not on stderr and
      not on an exit code. **The stream was measured, not assumed:** every shipped assertion on a run
      finding reads stdout (`tests/test_cli.py` carries two `assert "W-STATS-STRATUM-SHADOWED" in
      doc["stdout"]` lines and `tests/test_report.py` a third — **grep for them and quote one**). An
      absence asserted on stderr would pass whether the warning fired or not, which would make exactly
      this fixture unable to fail.
      *Arm 2, and it is the one Decision 3 is actually about:* one repeat recording `{"valid": None}` and
      another recording `{"valid": True}` — a genuine disagreement whose collapsed cell is `None`,
      **bit-identical to arm 1's**. Assert the cell is `None` and that the warning **does** fire. The two
      arms differ **only in the rows**, never in the collapsed value, so a rule answering from the cell
      gives one answer to both and must fail one of them.

- [ ] **Step 5: Fixture L — the mixed column (§ Corrections 5).** One unit, two repeats, recording
      `{"score": 4.0}` and `{"score": "n/a"}`. Assert **three** things: the cell is `4.0` (today's
      arithmetic, **unmoved** — the numeric subset's mean); the column **keeps** its metric block in
      `aggregated` through a real run; and `W-STATS-REPEATS-DISAGREE` names `score`.
      **This is the fixture that separates the prescribed rule from the plausible wrong one.** Under
      *mixed → `None`* the cell is `None`, and measured at `ee8085e` **one `None` cell costs the whole
      column its metric block for every unit** (probe `p3`) — a published column silently deleted, which
      no decision argues for. Under the prescribed rule the value is unmoved and the disclosure is the
      warning. **A second arm as the can-fail control:** the same column with **both** repeats numeric
      (`4.0` and `6.0`) collapses to `5.0` and draws **no** warning, asserted on stdout.

- [ ] **Step 6: the measurements interaction, OBSERVED rather than reasoned.** The design's § What could
      not be measured says a `measurements.parquet` from a real run was never inspected and *"the plan
      should build one."* **This plan built it** (§ Corrections 13) and the finding is that the two levels
      **do not interact**. Pin it: a run declaring `data.units.measurements: {by: read_id, collapse:
      first}` whose step records `{"score": …, "valid": True, "tag": "a"|"b"}` per measurement. Assert
      `measurements.parquet` holds both measurement rows with both `tag` values; `units.parquet` holds
      `tag: 'a'` (the declared collapse's answer); the collapsed table's `tag` is `'a'`; and **no**
      `W-STATS-REPEATS-DISAGREE` fires — the declared collapse ran **inside** each execution, so the
      repeat rule saw a constant. All four literals were observed at `ee8085e`. **State in the docstring
      why a numeric declared rule cannot reach this path**: `_collapse_measurements` calls `rule_for` then
      `coerce_for_rule`, which refuses a non-numeric value under a numeric rule before the repeat rule is
      reached — so only `first` and `mode` get here. **Grep
      `tests/test_artifacts.py::test_a_numeric_rule_coerces_a_recorded_string_before_applying` and cite
      it** rather than restating the mechanism.

- [ ] **Step 7: the mutations — three.**
      (i) Carry `values[0]` instead of `None` for a disagreeing non-numeric column. **Fixture C's
      `is None` must FAIL.** *Why the branches differ:* `values[0]` is `True` there, by construction.
      (ii) Make `repeats_disagreeing` answer from the collapsed cell (`value is None`) rather than from
      the rows. **Fixture D must FAIL** — arm 1 gains a warning it must not have. *Why the branches
      differ:* a recorded `None` is indistinguishable from a disagreement at the cell, which is the whole
      ground for Decision 3, and the two arms are bit-identical in `collapsed`.
      (iii) Delete the `W-STATS-REPEATS-DISAGREE` call site. **Fixture C's warning assertion must FAIL**,
      on **stdout**, with the column name in it. *Why the branches differ:* the message names `flag`, and
      nothing else in that run's output does — **checked against the run's other diagnostics rather than
      assumed**, which is the check `assert "draft" in out` failing on `draft_run` exists to force.
      **A fourth is named REJECTED rather than blind:** dropping the `all numeric → False` early return
      in `_repeats_disagree` would make every unequal numeric column "disagree" — caught by Fixture L's
      second arm and by arm A's `results` snapshot, which carries a numeric column with real variance.
      Run it; it is not blind, and naming it as such would be wrong.

- [ ] **Step 8: run** the four commands. **Delta:** Fixtures C, D, L and the measurements pin added; **one
      test replaced** (`test_collapse_drops_a_bool_column_rather_than_averaging_it`), named in the report.
      **Commit:** `H5b task 5: a disagreeing non-numeric column collapses to None and says so, from the
      rows`.

**What this task must NOT touch.** Pin arms A, B, C, D, E — **arm B in particular**: Fixture A has no
column that disagrees across repeats, so this task cannot reach it, and an edit here is a finding.
`repeat_spread`'s body (its `std: 0.0` filing is unassigned and stays). `units.apply_rule`,
`units.rule_for`, `units.coerce_for_rule` — cited, never called, never refactored.

---

## Task 6: `summarize_step`'s deleted clause, and where the projection sits

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Surface: a direct call, plus one deleted docstring sentence.** Design Decision 4. **`summarize_step`
ships NO code change** — measured: it publishes the numeric column and the derived metrics over a
`collapsed` carrying `valid: True` and raises nothing, because the column loop's existing `if not raw or
not all(_is_numeric(v) for v in raw): continue` **is** the projection. The scoping's task 13 (*keep the
column out of `aggregated`*) is already true of the shipped code.

**Files:**
- Source: `src/publishable/stats.py` (docstring only)
- Test: `tests/test_stats.py`

- [ ] **Step 1: delete the clause, do not rewrite it.** `summarize_step`'s docstring reads *"A derived key
      colliding with a recorded column — **even one dropped above for being non-numeric** — is refused."*
      After task 4 no column is dropped above, so the qualifier describes nothing. **Delete the em-dashed
      qualifier and leave the sentence, which is then exactly true.** *Prefer deleting a claim to
      rewriting it: a rewrite invents; a deletion cannot.*
      **Then re-read the whole docstring against the code you now have** and report every other clause
      that mentions dropping, non-numeric values or bools. The paragraph beginning *"A column is skipped
      entirely — not coerced, not defaulted — when any unit's value for it is not a real number"* is
      **still true** and is the projection this task pins; say so rather than editing it.

- [ ] **Step 2: Fixture I — where the projection sits, and why it is a correctness rule.**
      `summarize_step` over Fixture A's table with a derived metric that **reads the bool column**.
      Assert `ci95[0] <= value <= ci95[1]`, and concretely `value == 6.0`, `ci95 == [6.0, 6.0]`,
      `resample_draws == 2000`.
      **The load-bearing claim:** `summarize_step` passes the `collapsed` it received straight to
      `percentile_of_derived`, which rebuilds each draw's table from **whole rows**. Stripping the column
      at the **input** would give the 2000 draws a narrower table than the single unresampled `aggregate`
      call in `cli.py` — measured on this fixture: `(6.0, 6.0)` against the full table and **`(0.0,
      0.0)`** against the stripped one, **a point estimate outside its own interval.**

- [ ] **Step 3: the mutation.** Project non-numeric columns out of `collapsed` at `summarize_step`'s
      **input** (a comprehension at the top of the function). **Fixture I's `value`-inside-`ci95`
      assertion must FAIL.** *Why the branches differ:* measured, both ways, above.
      **Named blind in advance:** restoring the deleted docstring clause. A docstring has no behaviour.
      **Its replacement is task 4's mutation (iv)**, which pins the property the clause was describing —
      that the collision sees a column whose cells are `None` — plus the B2 review reading the sentence
      against the code.
      **A second mutation is named blind and is NOT left unpinned:** emptying the `_is_numeric` gate in
      the column loop is *not* blind — it publishes the non-numeric column as a metric, caught by
      Fixture A's key-set assertion and by task 14's `report` row assertion. Named here so nobody assumes
      otherwise.

- [ ] **Step 4: run** the four commands. **Delta:** Fixture I added. **Commit:** `H5b task 6: delete the
      clause task 4 falsified, and pin the projection at summarize_step's output`.

---

## Task 7: the contrast guard — the naive fix destroys a run record, and this is the pin that makes it happen

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Surface: a direct call and a real `run`.** Design Decision 7. **This is the task the controller singled
out**: *a non-numeric value reaching the contrast subtraction hits an unguarded subtraction in `cli.py`,
`TypeError` outside every `try`, no `run.yaml`* — every execution paid for, the record lost.

**A rule enforced only by another function's output is not a guard.** Measured: a non-numeric column
cannot become a `metric_key` today, because `_comparison_step_blocks` iterates
`sorted((set(of_summary) & set(against_summary)) - {"by"})` and `of_summary` is `aggregated`'s step block.
So after task 6 the subtraction is unreachable **by convention at another function's output** — and the
scoping measured what happens when that convention breaks: `TypeError: unsupported operand type(s) for
-: 'str' and 'str'` at `of_collapsed[k][metric_key] - against_collapsed[k][metric_key]`, run directory
complete, **no `run.yaml`.**

**Files:**
- Source: `src/publishable/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: import the predicate.** Add `_is_numeric` to `cli.py`'s
      `from publishable.stats import (…)` block. **`cli.py` does not import it today** (§ Corrections 4);
      the precedent for a private cross-module import is `_arm_keys` from `runner`, already in this file.
      It sorts first in the block, as `_arm_keys` does in its own.

- [ ] **Step 2: the paired arm.** In `_comparison_step_blocks`' recorded-column branch, the `col_keys`
      comprehension that already filters by membership gains the narrowing:

```python
                    col_keys = [
                        k
                        for k in base_keys
                        if metric_key in of_collapsed[k]
                        and metric_key in against_collapsed[k]
                        # The guard at the subtraction, not at another function's
                        # output. Today the only thing keeping a non-numeric value
                        # out of `metric_key` is that `of_summary` is `aggregated`'s
                        # step block and `summarize_step` publishes numbers only —
                        # a convention, not a guard, and when it breaks the
                        # subtraction below raises `TypeError` outside every `try`,
                        # losing a completed run its `run.yaml`.
                        and _is_numeric(of_collapsed[k][metric_key])
                        and _is_numeric(against_collapsed[k][metric_key])
                    ]
```

      **`col_keys` and not `of_values` is the right place** because `diffs`, `col_weights`, `col_clusters`
      and `n_paired` are **all** derived from `col_keys` — the one-pass discipline this function already
      states. A narrowing applied further down would leave a count and a cluster mapping describing a
      different set than the vector beside them.

- [ ] **Step 3: the unpaired arm — and it goes in `of_col`/`against_col`, NOT in
      `of_values`/`against_values`.** § Corrections 2. The design's text says the value vectors; measured,
      `n_of` is `len(of_col)`, `n_against` is `len(against_col)`, and `of_clusters`/`against_clusters` are
      built by keying off `of_col`/`against_col`. Filtering only the value vectors would publish a count
      and group a cluster set that the difference did not come from — *a vector filtered or ordered
      differently*, this project's one recurring version of that fault.

```python
                    of_col = [
                        k
                        for k in of_side_keys
                        if metric_key in of_collapsed[k]
                        and _is_numeric(of_collapsed[k][metric_key])
                    ]
                    against_col = [
                        k
                        for k in against_side_keys
                        if metric_key in against_collapsed[k]
                        and _is_numeric(against_collapsed[k][metric_key])
                    ]
```

- [ ] **Step 4: it SKIPS, it never raises — and skipping is not silence.** No new error or warning code
      (design Decision 7: the path is unreachable from a validated config, and a § Errors row that can
      never fire misleads). The two existing core-bookkeeping guards in this function raise `ValueError`
      and both sit in code reached **before** any interval is built; a raise **here** loses the `run.yaml`
      this guard exists to protect. A unit dropped this way is dropped exactly as a unit missing the
      column is dropped today, and `n_paired` reports what remains — `0` already means *pairing failed*,
      so an all-dropped metric publishes `n_paired: 0` and `ci95: null`, a shape a reader can already
      read. **Write that reasoning as a comment at the guard and nowhere else** — do not restate it at the
      unpaired arm, which is the same claim in a second place.

- [ ] **Step 5: Fixture G, both ends.**
      *Direct call:* `_comparison_step_blocks` driven with an `aggregated` carrying a `str`-valued metric
      key and a `collapsed` carrying `str` values for it. Assert it returns **without raising** and
      publishes **no entry** for that key. Today that call is the measured `TypeError`.
      **Its docstring says in so many words that it drives a state production cannot reach, and why the
      guard exists anyway** — a rule enforced by another function's output is not a guard, and the
      scoping measured the cost when it broke.
      *Unpaired arm:* the same, over a declared `sweep.groups` axis, asserting the published `n_of` and
      `n_against` are the **narrowed** counts and that `cohens_d` is not computed over a mixed vector.
      **Two separate assertions on two separate comprehensions**, because a mutation in one must be caught
      by an assertion on that one.
      *End to end (the honest half):* a real run recording a non-numeric column asserts `run.yaml`
      **exists**, `vs_baseline` holds **no entry** for that column, and exit is `0`. That is the claim
      about production, stated separately from the direct-call claim about the guard.
      **The `run.yaml`-exists assertion is the one the controller asked for**: it is the shape that makes
      *every execution paid for, the record lost* observable, and it must be asserted on the file rather
      than on the exit code.

- [ ] **Step 6: the mutations — two, and they must be run separately.**
      (i) Delete the two `_is_numeric` clauses from the paired arm's `col_keys`. **Fixture G's
      direct-call paired arm must FAIL** with the measured `TypeError`. *Why the branches differ:* the
      unguarded subtraction raises on `str` operands, measured.
      (ii) Delete them from the unpaired arm's `of_col`/`against_col`. **Fixture G's unpaired arm must
      FAIL.** *Why the branches differ:* the two arms are separate comprehensions, so a mutation in one is
      invisible to an assertion on the other — which is why this fixture has both.
      **A third, and it is the one that pins § Corrections 2:** move the unpaired narrowing from
      `of_col`/`against_col` into `of_values`/`against_values`. **The unpaired arm's `n_of` assertion must
      FAIL** while the interval still computes. *Why the branches differ:* `n_of` is `len(of_col)`, so the
      count and the vector disagree under the mutant and agree under the fix. **Without this mutation the
      correction is prose, and prose in a corrections section prevents nothing.**

- [ ] **Step 7: run** the four commands. **Delta:** Fixture G's three arms. **Commit:** `H5b task 7: the
      contrast guard sits at the subtraction, and skips`.

**What this task must NOT touch.** `paired_keys`/`unpaired_keys` (task 8 documents the ruling; no code
changes). The derived branch's `base_keys` — Decision 6 rules that a unit with no numeric column **does**
enter the intersection and the resample pool, because narrowing `paired_keys` would make `n_paired`
describe a different set than the pool `paired_percentile_of_derived` draws from. Pin arms A–E.

---

## Task 8: the `paired_keys` ruling, documented

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Surface: documents.** Design Decision 6. The scoping named this as the fourth question the filing did
not ask, and it is **record-visible** — `vs_baseline…mean_score.n_paired` moves 4 → 6, pinned in task 1's
arm E.

**Files:** `docs/reference.md`

- [ ] **Step 1.** § Statistical reporting already documents `n_paired` as the paired intersection rather
      than as a count of contributing values. **State the consequence beside it**: a unit that completed
      in both conditions enters the intersection whether or not it carries the metric's own column,
      because a derived metric is computed over the whole table and a recorded column's own arm narrows to
      the units carrying it. So a **derived** contrast's `n_paired` can exceed the number of units that
      influenced the difference, and a **recorded column's** cannot.
      **Say why it is the honest figure:** it is exactly the pool the interval rests on —
      `paired_percentile_of_derived` draws over `base_keys` and recomputes — so narrowing the count
      without narrowing the pool would publish a count describing a different set than the interval
      beside it.

- [ ] **Step 2: check the claim against the code before writing it.** Read `paired_keys` (it is
      `set(of) & set(against)`, narrowed by a `within` stratum) and the paired arm's `col_keys`
      (which narrows by column membership), and **report both** — the scoping measured the recorded column
      `score`'s own `n` **unmoved at 4** while the derived metric's moved, and that asymmetry is what this
      sentence describes. **If the code disagrees with the sentence you were about to write, the code
      wins and the disagreement is a finding.**

- [ ] **Step 3: both consistency passes on this edit**, in task 2's shape. **Declared vs. derived** is the
      class that bites: `n_paired` is derived, so grep the four documents by name for any passage showing
      it as a settable input.

- [ ] **Step 4.** No mutation; **named blind**, a document has no behaviour. Its replacement is task 1's
      arm E, which pins the moved `n_paired` for the derived metric and the unmoved one for the recorded
      column **in the same assertion block** — the discrimination this sentence claims.

- [ ] **Step 5: run** (no test delta) and **commit**: `H5b task 8: § Statistical reporting states which
      units enter the pairing intersection`.

---

## Task 9: the `by` arbitration answers from the recorded-column set, and `_attributed`'s two falsified grounds are deleted

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Surface: a real `run`.** Design Decision 9.

Today `cli.py` tests `if "by" in step_summary`, so a **non-numeric** `by` column draws no
`W-STATS-STRATUM-SHADOWED` and the strata are published under the same name the column holds in
`units.parquet` — measured by the scoping both ways, with the numeric case as its can-fail control. After
task 6 the non-numeric column still never reaches `step_summary`, so the gate must move.

**Files:**
- Source: `src/publishable/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: move the gate to the recorded-column set — the set this loop ALREADY computes.**
      `recorded_columns = {col for cols in collapsed.values() for col in cols}` is built a few statements
      earlier in the same loop body, for the `repeat_spread` walk. **Reuse it; do not recompute it.**
      *Before writing a walk, a guard or a containment, grep for one that already exists.* The gate
      becomes `if "by" in recorded_columns:` and the `elif by_block:` branch below it is unchanged.
      **This is the direct question** — *did any unit record a column called `by`?* — rather than a proxy
      for it. It is **not** the *reserved NAME standing in for a structural fact* fault: there the question
      was *is this entry a stratum?* and the answer was a name; here the question **is** whether a name was
      recorded.
      **Verify the widening is only a widening:** `by` in `step_summary` implies `by` in
      `recorded_columns`, because a **derived** `by` is refused in `summarize_step` and the containment
      retry passes no `derived` at all. **Read both branches and report that reading** rather than
      asserting it.

- [ ] **Step 2: both arms warn and both suppress the strata.** § Steps and artifacts already states it
      without qualification — *"no strata are reported for the step at all"* — and a run whose
      `units.parquet` holds a `by` column while its `run.yaml` holds a `by` strata block is the
      two-meanings-under-one-name case the reserved name exists to prevent. The `if`/`elif` shape already
      delivers both, so **this is a one-expression change**; say so rather than restructuring the branch.

- [ ] **Step 3: reword the `W-STATS-STRATUM-SHADOWED` row in § Warnings core reports — ONE row, ONE emit
      site, two conditions.** The row reads *"A step records a metric named `by` … so that column keeps
      its recorded value but is reported with no contrast delta"*. A non-numeric `by` column keeps **no**
      `aggregated` entry to keep, so the row must cover a column with a metric block and one without.
      **Locate the row by its code, never by position.** Then check § Steps and artifacts' reserved-`by`
      paragraph against the reworded row and against the code, and report all three readings.
      **No other row moves, and the emit site is ONE — but the grep returns TWO lines.**
      `grep -rn 'W-STATS-STRATUM-SHADOWED' src/publishable/*.py` → `cli.py`'s `warn` call **and a
      docstring in `report.py`**. Run it and report both. *§ Errors and § Warnings carry one row per code,
      not per emit site, so a diagnostic's unit of work is every site that raises or reports it* — that
      was the whole-branch Major on two sub-slices and shipped twice inside a third, and **the second hit
      here is not an emit site but IS a claim this slice changes** (§ Corrections 15).

- [ ] **Step 3b: re-read `report.py`'s two structural predicates, because this task moves what they
      claim.** `_is_strata_block`'s docstring says *"`cli.py` does not write this block at all when a
      recorded column of that name exists"* — **false today for a NON-numeric `by` column**, which is
      exactly what the scoping measured, and **true after step 1.** `_is_metric_entry`'s docstring says a
      recorded `by` column *"keeps its value … as a real metric entry"* — true for the numeric case and
      **false for the non-numeric one**, which keeps no metric block at all after task 6.
      **Correct both by narrowing the claim to the case it holds for, or by deleting the clause**
      (*prefer deleting a claim to rewriting it*), and **change no code in `report.py`**: both predicates
      are structural and both stay. **When you change code a comment describes, re-read the comment** —
      and this is the sibling that already got the structural test right, so nothing here is a defect
      except the sentences.

- [ ] **Step 4: DELETE `_attributed`'s two falsified grounds.** Its docstring argues `unit` is restored
      *"because nothing refuses an attribute named `unit`"* — H5a's `units.RESERVED_COLUMNS` now does, at
      `validate` and at roster resolution — and argues a numeric attribute's publication is *"not
      reachable while every roster attribute arrives from `csv.DictReader` as a string"*, which H5a's
      `coerce_scalars` at `resolve_units` makes weaker than it reads: a resolver may yield a float and it
      stays a float. **Both grounds go. Delete, do not rewrite.**
      **The true reasons stay:** the unit key column must survive a bootstrap draw that duplicates units,
      and an attribute is merged into **rows** and never into `collapsed`, which is why it can never be
      published as a metric. **Grep `RESERVED_COLUMNS` in `src/publishable/units.py` and quote the
      constant** before writing that the first ground is false — *before repeating any claim a brief makes
      about the code, grep for it.*

- [ ] **Step 5: Fixture F — a non-numeric `by` column, with the numeric arm as its can-fail control.**
      A step recording `{"pred": float(i), "by": f"lvl{i % 2}"}` with `report_by` declared. Assert
      `W-STATS-STRATUM-SHADOWED` fires **on stdout**, `"by" not in aggregated[step]` (a non-numeric column
      has no metric block to keep), and **no strata block**.
      **The controls, and there are two:**
      (a) the two **existing** tests over `_RECORDS_A_BY_COLUMN_STEP`, which records `float(i) * 2.0` and
      asserts `aggregated[step]["by"]["value"] == 39.0` — task 1's pin arm C, **zero lines changed**, and
      the B3 review reports the `git diff` line count over both bodies.
      (b) `tests/test_artifacts.py::test_a_measured_by_column_survives_the_collapse_into_units_parquet`,
      which records `{"by": "north", …}` — **a non-numeric `by` column at the artifact layer**, which
      never reaches `collapse_repeats` and must stay green. **The design says "no test in the suite records
      a non-numeric `by`"; that is false, and this is the test (§ Corrections 1).** The true claim is
      narrower: no test in **`tests/test_cli.py`** does, so Fixture F's end-to-end arm exists nowhere
      today. **Grep `'"by": ' tests/*.py` yourself and report the hit list** rather than repeating either
      claim.

- [ ] **Step 6: the mutations — two.**
      (i) Point the gate back at `step_summary`. **Fixture F's warning assertion AND its no-strata
      assertion must FAIL.** *Why the branches differ:* measured by the scoping both ways — the
      non-numeric column never reaches `step_summary`, so the mutant is silent.
      (ii) Widen the gate to suppress a **numeric** `by` column's metric block (drop the column from
      `step_summary` instead of only the strata). **Pin arm C must FAIL** — the two existing tests assert
      `aggregated[step]["by"]["value"] == 39.0`. *Why the branches differ:* the numeric arm keeps its
      metric block, and a widened guard removes it.
      **Named blind in advance, with its replacement:** the `_attributed` docstring deletion. A docstring
      has no behaviour; its replacement is the B3 review's *were the two grounds deleted rather than
      rewritten?* check, run against `git diff` rather than against the report.

- [ ] **Step 7: run** the four commands. **Delta:** Fixture F. **Commit:** `H5b task 9: the by
      arbitration answers from the recorded columns, and _attributed loses two false grounds`.

---

## Task 10: the derived-key collision, made real

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Surface: a direct call, and one § Errors row asserted rather than edited.** Design Decision 8. **No new
code**: measured, `summarize_step({u: {"score": …, "valid": True}}, …, derived={"valid": 1.0})` **raises**
`E-STEP-KEY-COLLISION` today, because the check is `collision = set(derived) & set(columns)` with
`columns` built from `collapsed`. Task 4 is the whole fix.

**Files:** `tests/test_stats.py`, `docs/reference.md` (assertion only), `docs/superpowers/spec-defects.md`

- [ ] **Step 1: make the green unreachable test real. It is NOT deleted and NOT moved.**
      `tests/test_stats.py::test_a_derived_key_colliding_with_a_dropped_non_numeric_column_is_refused`
      builds `{f"u{i}": {"r": True} for i in range(5)}` — a `collapsed` no production caller can produce,
      since that input returns `{}` today. **Its fixture becomes the output of a real `collapse_repeats`
      call over `_result`-built executions recording `{"score": float(i), "r": True}`, and its assertion
      is unchanged.** *The seam becomes reachable rather than being re-described.*
      **Its docstring must lose the words "dropped from `out` for being non-numeric"** — after task 4
      nothing is dropped — and gain, in their place, what the fixture now is: a `collapsed` a production
      caller produces. **The test's NAME keeps "dropped" and that is wrong**; rename it to
      `test_a_derived_key_colliding_with_a_non_numeric_recorded_column_is_refused` and **grep the suite
      for the old name first**, reporting the grep, because a reader greps for exactly that name and stops
      looking.

- [ ] **Step 2: the § Errors row is ASSERTED, not edited.** § Errors core raises' `E-STEP-KEY-COLLISION`
      row already names *"a derived key against a recorded column"* and already says this site is
      re-reported as `W-STATS-AGGREGATE-FAILED` rather than raised. **No emit site is added — the same
      site sees a wider input.** Read every site that raises **or reports** the code
      (`grep -rn 'E-STEP-KEY-COLLISION' src/publishable/*.py`, and read `artifacts.py`'s sibling raise as
      well as `stats.py`'s), then confirm the row covers all of them, and **report the sites and the
      grep.** If the row turns out narrower than its code, that is a finding: widen it here, in this task,
      rather than filing it.

- [ ] **Step 3: record it as found-and-closed in the same slice.** `spec-defects.md` gains no live entry
      for this: the scoping found *a derived key colliding with a non-numeric recorded column is not
      refused* filed **nowhere**, and this slice closes it. **Record it in the STRUCK/closed form**, beside
      the entries task 15 strikes, naming the three shipped claims that promised it (`summarize_step`'s
      docstring, § Errors' row, and the green test's own docstring) and that the test named the hazard
      verbatim while proving nothing.
      **And name what it closes upstream:** one corner of the H4b-2 Critical — a derived key colliding
      with a recorded column's name published an *unclustered* contrast interval because the refusal could
      not see the column. **For a non-numeric column it now can.** Do not claim more: the numeric case was
      already refused and is pin arm D(ii).

- [ ] **Step 4: the mutation.** Revert `_across_repeats` to omit a disagreeing column's key. **The
      renamed test's second arm (task 4 step 7) must FAIL.** *Why the branches differ:* omission removes
      the column from `columns`, so the collision stops firing; measured — it fires for an all-`None`
      column. **This is the same mutation task 4 runs, deliberately re-run here** on the finished
      fixture, because task 4's arm and this task's arm are two different call shapes.

- [ ] **Step 5: run** the four commands. **Delta:** one test renamed, its fixture replaced; no net add.
      **Commit:** `H5b task 10: the derived-key collision is driven from the collapse's own output`.

---

## Task 11: the second empty-level gate's document and record halves

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Surface: documents and records. Its PIN is task 4's Fixture H** — a live overruling of the scoping's
task list, made by the design so the pin lands in the batch where the behaviour goes live.

**Files:** `docs/reference.md`, `docs/superpowers/spec-defects.md`

- [ ] **Step 1: § Reporting strata states the rule the gate enforces.** A level block must carry at least
      one entry from the level's **own** table; a block holding nothing but derived metrics over a table
      whose every column was non-numeric is the empty case wearing a value, and such a level is **absent**
      rather than empty — the rule `vs_baseline` and `contrasts` already follow, since a `by: {}` would
      claim a stratification was performed and found nothing. **Check the section for a sentence that
      already says this before adding one**, and report what you found.

- [ ] **Step 2: strike the filing, and correct its own account of itself.** The entry *the second
      empty-level gate in `cli`'s stratum loop is unpinned* (RE-OWNED 2026-08-22 to H5b) is **struck**,
      naming Fixture H as the pin. **Its account of WHY it was unreachable is wrong and the strike says
      so:** the filing gives one reason, and the measured reason is that the gate goes live exactly when
      `collapse_repeats` admits a unit with no numeric column. **A filing's claims about the code go stale
      like any other comment; when you change code an entry describes, re-read the entry.**
      **Quote the entry's current text in your report before striking it**, so the correction is checkable.

- [ ] **Step 3: both consistency passes on the `reference.md` edit**, in task 2's shape.

- [ ] **Step 4.** No mutation. **Named blind, with its replacement stated as a fact rather than a
      promise:** task 4's mutation (iii) — `if True:` in place of the gate — **already ran and already
      failed Fixture H** by the time this task starts. Confirm it in this task's report by naming task 4's
      report, and **do not re-run it here**: re-running a mutation whose result is recorded is not
      evidence, and running it against a stale checkout is worse.

- [ ] **Step 5: run** (no test delta) and **commit**: `H5b task 11: the empty-level gate's rule stated and
      its filing struck`.

---

## Task 12: `E-STEP-COLUMN-UNKNOWN` pinned in both directions

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Surface: a direct call and a real `run`.** The scoping's task 17. This is the behaviour the slice
narrows **around** and must not narrow **away**.

**Files:** `tests/test_stats.py`, `tests/test_cli.py`

- [ ] **Step 1: it STOPS firing for a column the table now holds.** Through a real run: a template whose
      `aggregate` reads `units.valid` over a step recording `{"score": …, "valid": True}` produces its
      metric and **no** `W-STATS-AGGREGATE-FAILED` on stdout. Today the same project earns
      `W-STATS-AGGREGATE-FAILED … E-STEP-COLUMN-UNKNOWN ContractError: 'valid' is not a column this table
      holds` — measured by the scoping end to end. **Assert on the derived value, not only on the absence
      of the warning**, or the test passes identically if nothing ran.

- [ ] **Step 2: it STILL fires for a name no row holds.** The same run with `units.absent_column`:
      `W-STATS-AGGREGATE-FAILED` naming `E-STEP-COLUMN-UNKNOWN`, exit 0, `run.yaml` written, and the
      recorded columns' own summaries **unaffected** — the containment's own promise.
      **And by direct call**, on a table that holds other columns, so the fixture cannot fire on an empty
      table instead. **Grep for an existing direct-call pin of this code before adding one**
      (`grep -rn 'E-STEP-COLUMN-UNKNOWN' tests/*.py`) and report it; pin arm D(i) already covers one
      shape and this must not be a third copy of it.

- [ ] **Step 3: the mutations — two.**
      (i) Make `UnitTable.__getattr__` return an all-`None` column instead of raising. **Step 2's
      assertions must FAIL** (both arms). *Why the branches differ:* one asserts a raise and one asserts a
      diagnostic naming the code.
      (ii) Restore `or not _is_numeric(value)` in `_gather_repeats`. **Step 1's derived-value assertion
      must FAIL** — the column disappears and `E-STEP-COLUMN-UNKNOWN` returns. *Why the branches differ:*
      the two steps assert opposite directions of the same predicate, which is why one mutation cannot
      cover both.

- [ ] **Step 4: run** the four commands. **Delta:** both directions added. **Commit:** `H5b task 12:
      E-STEP-COLUMN-UNKNOWN pinned in both directions`.

---

## Task 13: the silent case's discriminating test

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Surface: a real `run`.** The scoping's task 16. **A fixture whose numbers agree with the bug is the
trap**: `n_valid: 0.0` over six `True` rows is a plausible value, and so is `n_rows: 4.0` over six units.

**Files:** `tests/test_cli.py`

- [ ] **Step 1: the discrimination, and it is why this task is separate from task 4.** Fixture A pins the
      literals; this task pins that the literals **could not have been produced by the bug**. Build a run
      whose correct and buggy answers are **different and neither is a round number a reader would
      accept**: a bool column recorded by **five of eight** units, so a template counting it reports
      `5.0` correctly and `5.0` under the bug too **unless** the units carrying no numeric column are the
      ones that carry the bool — **so make them exactly those.** Correct answer `5.0`; buggy answer
      `2.0`. **Compute both by running, and state both in the docstring.**

- [ ] **Step 2: the assertion that the bug cannot satisfy.** Assert the derived value **and** `n.completed`
      **and** that `resample_draws` is not the full `draws` — three facts a single wrong number cannot
      match. **Do not assert an absence alone**: a control asserting only absences passes identically if
      nothing ran.

- [ ] **Step 3: state what this test does NOT pin.** It says nothing about the correction family (arm E),
      nothing about a disagreeing column (Fixture C) and nothing about `report` (task 14). **Naming the
      boundary is what stops a later reader from treating a green suite as evidence about all four.**

- [ ] **Step 4: the mutation.** Restore `or not _is_numeric(value)` in `_gather_repeats`. **Step 2's three
      assertions must FAIL, and the report must say which failed first.** *Why the branches differ:*
      `5.0` against `2.0`, computed both ways.

- [ ] **Step 5: run** the four commands and **commit**: `H5b task 13: the silent case's discriminating
      test`.

---

## Task 14: `report` and `study` pinned as readers of `aggregated`, and three shipped docstrings re-derived

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Surface: two real commands.** The scoping's task 14 and the design's Fixture J. `report.py` and
`study.py` both walk `aggregated` — the key this slice changes — and the scoping's own instruction was
that this **must be pinned rather than assumed**, because it is precisely the additive-only claim the
ruling requires.

**Files:** `tests/test_report.py`, `tests/test_study.py`, `tests/test_cli.py` (docstrings)

- [ ] **Step 1: Fixture J — `report` over Fixture A's run.** Render the run's `run.yaml` through
      `publishable report` and assert the condition table holds rows for `n_valid`, `n_rows`,
      `mean_score` and `score` and **no row for `valid`**. **Assert on the rendered text**, and say what
      else in that output could produce the substring you assert — the scoping measured `report`
      rendering a non-numeric `value` **without complaint** when one reached `aggregated`, so a bare
      `assert "valid" not in out` would be satisfied by the absence of the *word*, not of the row.

- [ ] **Step 2: `study`'s thin-metric floor sees the same four entries.** A two-member bundle through
      `report study.yaml`. `study.py`'s `_floor_metric_entries` walks every entry carrying `basis`,
      **structurally**, so a string wearing a metric block's shape would enter the floor check. Assert the
      four entries and no fifth. **Grep `_floor_metric_entries` and read the walk before asserting what it
      sees**; report the grep.

- [ ] **Step 3: re-derive the three shipped test docstrings the scoping measured, and grep each claim.**
      **All three exist at the names the scoping gave** — confirmed at `ee8085e`,
      `grep -c` over `tests/test_cli.py` returns hits for all three; **run it and report it.**
      - `test_a_run_without_a_holdout_pins_its_denominators_and_artifacts` says *"`stats.summarize_step`
        drops a bool column outright"*. **False in the wrong function**: `summarize_step` never sees the
        column; it receives `{}` from the collapse. Re-derive it to what the test actually pins.
      - `test_a_baseline_sweep_reports_a_delta` says the scaffold's step *"records only a bool …
        filtered by `_is_numeric`"*, which names the right predicate in the wrong function. Re-derive.
      - `test_an_unclustered_resampled_contrast_draws_what_it_always_drew` says the default step *"grows
        no `basis: units` column"*, which **is true and stays.** Say so; do not edit it.
      **Both false docstrings become true after this slice in a different way than they were false**, so
      **delete the wrong clause and state what the test pins**, rather than relocating the claim. *Prefer
      deleting a claim to rewriting it.*

- [ ] **Step 4: the mutations — two.**
      (i) Empty `summarize_step`'s `_is_numeric` gate in the column loop, so a `valid` metric block is
      published. **Step 1's no-`valid`-row assertion and step 2's four-entry assertion must both FAIL.**
      *Why the branches differ:* the block reaches `aggregated`, both readers walk it structurally, and
      neither refuses it — measured by the scoping.
      (ii) Point `study.py`'s floor walk at a shallower path. **Step 2 must FAIL.** *Why the branches
      differ:* the shipped walk is the deep one, and a shallower walk was **dead on every real record** on
      a preceding slice — this is the fixture that would have caught it.
      **Named blind in advance:** the three docstring edits. Their replacement is the B4 review reading
      each against the code, and **the greps this task must report.**

- [ ] **Step 5: run** the four commands. **Delta:** Fixture J's two arms; three docstrings edited, one left
      alone. **Commit:** `H5b task 14: report and study pinned as readers of aggregated, and three shipped
      docstrings re-derived`.

---

## Task 15: the records

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Surface: records and documents. Runs against the finished branch.** `spec-defects.md` is a live list, so
a closed gap is **struck** rather than deleted; every other tracked record is **appended to, never
retro-edited**.

**Files:** `docs/superpowers/spec-defects.md`,
`docs/superpowers/specs/2026-08-08-implementation-spine-design.md`, `CLAUDE.md`

- [ ] **Step 1: strike three entries, each against the code.**
      - *a unit whose only recorded column is non-numeric is silently dropped* (Owner: H5b) — **struck**,
        naming **which of its four options was taken** (carry with the column, and admit the unit) and
        why the other three were rejected, and answering **the fourth question it did not ask**: such a
        unit **does** enter `paired_keys`, `n_paired` and the resample pool (Decision 6, documented by
        task 8).
      - *the `aggregate` table omits declared unit attributes and non-numeric columns* (RE-OWNED to H5b) —
        its **non-numeric half struck**; the attributes half was already closed by H5a and is not
        re-struck.
      - *the second empty-level gate in `cli`'s stratum loop is unpinned* — **already struck by task 11.**
        **Confirm it, do not strike it twice.** *A ledger line saying "filed" is not a filing*, and its
        converse holds too: an entry struck twice reads as two gaps.

- [ ] **Step 2: three things that were filed NOWHERE, each recorded in the right form.**
      - **The mixed `str`/`float` question**, which H5a's design says is *"Filed, not built, owner H5b"*
        while `spec-defects.md` has no such entry: **discharged by Decision 11 in `reference.md`** (task 3),
        and the write-side residual **filed unassigned with a reason** (task 3, step 5). **Confirm task 3's
        entry exists; do not write a second one.** Record in your report that *a design line saying
        "Filed" is not a filing* — **second instance in one slice pair**, the first being H5a's own `.csv`
        null question.
      - **A derived key colliding with a non-numeric recorded column is not refused** — recorded by task 10
        as *found and closed in the same slice*. Confirm.
      - **A non-numeric recorded `by` column draws no `W-STATS-STRATUM-SHADOWED`** — **closed by task 9**,
        recorded the same way, here.

- [ ] **Step 3: FILE AGAINST H9 — `diff`'s `uv.lock` detail lines do not name the moved package.** The
      controller's ruling: this slice's change is carried by `provenance.environment.uv_lock_hash`, which
      `diff` reads, so it is **not** true that no row points at it — the true and smaller claim is that
      **the row that points at it is the one a reader is least likely to read**. If the ruling is wrong, the
      symptom is a user who diffs two runs, sees `uv.lock DIFFERS` beside changed numbers, and **cannot
      tell whether the lockfile move caused the change.** File it with **Owner: H9**, and the reason:
      `reproduce` is what reads the environment back, so H9 is the slice with that surface. **Verify both
      halves before filing** — `cli.py` writes `provenance.environment.uv_lock_hash` and `diff.py`'s
      `ROW_LABELS` holds a `uv.lock` row reading exactly that key; grep both and report them.
      **Nothing is minted here to make the change more visible, and that is a decision rather than an
      omission**: a fourth hash, a core-version record key, or a `diff` row of its own would each add a
      second source of truth for something `uv.lock` already answers.

- [ ] **Step 4: append a correction to the spine's 2026-08-22 amendment. DO NOT EDIT IT.** Its
      § The hardening slices row sizes H5b at **"(10)"** and this slice is **16**; and its
      behaviour-change sentence has already been corrected once the same day. The append records the count
      **and** that the exposure is what the design's § The behaviour change enumerates — seven keys in
      one fixture, a correction family in another, four things that newly stop or newly warn — rather than
      a phrase. *A spec records what was decided when it was written; append the correction and say what it
      replaces.*

- [ ] **Step 5: `CLAUDE.md` — the slice entry and the order line.** A new entry in the shape of the
      existing ones, and it **must carry the disclosure the controller ruled stands**: the seven moving
      keys with computed before/after literals, and the **four** things that newly stop or newly warn —
      the collision, the `by` suppression, an `aggregate` that assumes every row carries its numeric
      column and may now raise (contained as `W-STATS-AGGREGATE-FAILED`), and **a purely numeric derived
      metric newly drawing `W-STATS-RESAMPLE-THIN`** because admitting units creates degenerate draws
      (`2000 → 1998` on Fixture A, `2000 → 1999` on the two-condition run — an existing code at an
      existing site seeing a wider input, so **no § Warnings row moves**). Add the eighth moving-key
      class — **a derived metric's `p_value` and, through the family, its `p_value_corrected`**
      (§ Corrections 16) — and say that **one warning is MINTED**, `W-STATS-REPEATS-DISAGREE`, which is a
      new thing that fires rather than a stoppage, so the entry does not read as if nothing new appears.
      Say that `uv.lock` is the
      carrier and that being *able* to derive the change from a lockfile hash is not being told.
      **The order line:** H5b removed from *remaining*; **H6, H9 and H3c-3's remaining 14** stated as what
      is left. **Grep `CLAUDE.md` for every occurrence of "H5b" and reconcile each**, reporting the list —
      the order line is not the only one.

- [ ] **Step 6: both consistency passes, in full, over the FOUR DOCUMENTS BY NAME.**
      `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md`, plus
      `CLAUDE.md` and the feasibility analysis for the removal sweep. **Every sweep names its files, never
      filters its output, and each must be PROVEN ABLE TO FAIL** by running it against a string known to
      be present — *a reviewer checking this exact rule lost a true hit to `grep -v superpowers`.*
      Mechanical: links, `#anchor`s, duplicate anchors, table column counts, trailing whitespace, tabs,
      invisible unicode, `×` not `x`, hyphens not en dashes — **skipping fenced blocks.**
      Cross-document: the shared worked example — **this slice changes no worked-example number, and the
      way to show it is `git diff` over `README.md`, `docs/design-principles.md` and `docs/reference.md`
      for the worked example's interval and hash literals, expecting ZERO hits.** (No pin arm in this
      slice covers those files; H5a's did, and citing it here would be a claim about the wrong branch.)
      Then: config completeness; enum comments; schema fields in prose; declared vs. derived; versions; prevented
      mistakes. **The feasibility analysis is exempt from the cross-document pass and subject to the
      mechanical pass in full.**
      **Neither pass touches the development record** — a spec and a scoping record what was decided and
      measured on their dates. `spec-defects.md` is the one exception.

- [ ] **Step 7.** No mutation. **Named blind, with its replacement:** the B5 review, which checks every
      struck entry against the code and every "filed" against the file. **Prove each sweep can fail and
      paste the proof** — that is this task's substitute for a mutation.

- [ ] **Step 8: run** the four commands (no test delta) and **commit**: `H5b task 15: strikes, filings,
      the H9 filing, the spine correction, CLAUDE.md, and both consistency passes`.

---

## Task 16: the § Executability entry — row 4 re-derived, `1 → 0 → 1`

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Surface: one appended section in a non-normative analysis.** H5a design Decision 11 ruled that this
re-derivation *"must be appended regardless of which slice does it"*; the entry dated 2026-08-22 against
`71f3c6e` **left row 4 at `1` and substituted a paragraph**, so this task is **correcting a published
figure** and therefore **appends and says what it replaces** — it never edits the earlier entry.

**Files:** `docs/feasibility-llm-growth-studies.md`

- [ ] **Step 1: append one entry, dated to this slice's merge and pinned to its commit**, in the shape
      § Executability on this build already uses: *"Measured on 2026-08-22 against commit `<sha>`"*, every
      refusal named by its code.

- [ ] **Step 2: repeat the four-row table with rows 1, 2 and 3 CHARACTER FOR CHARACTER.**
      8 of 8 validating clean; 0 blocked on `io.reuse_from`; **7** meeting the
      `report_by`-under-`resample` gap. **Row 3 is not this slice's and is not folded in.** **No fifth
      number is minted.** Copy the rows from the immediately preceding entry rather than retyping them,
      and **diff your copy against it**.

- [ ] **Step 3: row 4 goes `1 → 0 → 1`, with the re-derivation in the entry's own prose.** The predicate
      is *"free of every core-side dependency this analysis can name."* The named dependency is **a
      non-numeric recorded column vanishing between the write and `aggregate`**; it meets **all nine**
      configs, since all nine record through one request step whose payload carries `valid` (a bool),
      `invalid_reason` and `finish_reason` (strings); so row 4 **reads `0` today** and **`1`** once this
      slice lands. **Say plainly that the published figure was `1` and what it is replaced by.**

- [ ] **Step 4: the pre-emption question, decided, and named as decided.** E5's step records `"truth":
      unit.consensus_label` while the E-family declares `truth` as an attribute, so E5's own `io.record`
      would raise `E-STEP-KEY-COLLISION`. **That does NOT pre-empt the core-side dependency**: it is a
      defect in the analysis' own shown plugin code, fixable by renaming one key with no change to core,
      and the row's predicate names core-side dependencies only. Letting it pre-empt would answer *would
      this config as literally written run?* under a heading that asks about core, and would pin row 4 at
      `0` until the analysis is edited — the *carried phrase answering no consistent question* failure the
      two corrections in that section were written about.
      **So the entry names both, separately**: row 4 moves on the core-side dependency, and the `truth`
      collision is named as an **analysis-side obligation that changes no core-side count** — the same
      treatment the H8a entry gave E3's `summary`-step obligation. **State what was established and what
      was not:** the payload and the attribute list were quoted from the analysis; **the plugin was never
      run, because it does not exist.**

- [ ] **Step 5: repeat the two things the corrections require, in the entry's own words.** Do not quote a
      single figure for this analysis' executability, and **name the dependency**.

- [ ] **Step 6: the mechanical pass in full on this file** — it is exempt from the cross-document pass and
      **not** from this one. Links, `#anchor`s, table rows against the header's column count, whitespace,
      `×` for multiplication, hyphens in anchors. **Skip fenced blocks.**

- [ ] **Step 7.** No mutation; **named blind.** Its replacement is the B5 review's character-for-character
      check of rows 1–3 and its reading of row 4's argument.

- [ ] **Step 8: run** the four commands (no test delta) and **commit**: `H5b task 16: § Executability —
      row 4 re-derived 1 → 0 → 1, rows 1-3 unchanged`.

---

## Corrections against the code

**Appended by this plan's author and extended by no task.** Each was measured at `ee8085e`. The rule is
`CLAUDE.md`'s: *the plan argues from the spec, and the code outranks both; where they disagree the code
wins and the document changes first.* **Six of six implementers on one recent slice found a real
disagreement, so finding one is expected, not exceptional** — and **do not report a count of zero.** Every
claim below names what was run.

**1. "No test records a non-numeric `by` column" is false, and the design says it was grepped.** The
design's § What this pass found that the scoping did not, item 5, states: *"`tests/test_cli.py`'s
`_RECORDS_A_BY_COLUMN_STEP` records `{"pred": float(i), "by": float(i) * 2.0}` — the numeric arm — and
the only other `"by":` hits in the suite are `sweep.groups` entries. Grepped, not assumed."*
Run: `grep -rn '"by": ' tests/*.py`. **`tests/test_artifacts.py` holds two hits the claim misses** —
`io.record("p1", {"by": "north", "score": 10}, measurement="r1")` and its `r2` sibling, in
`test_a_measured_by_column_survives_the_collapse_into_units_parquet`, which records a **non-numeric `by`
column** deliberately and explains in its own docstring why the value must be a string.
**What the task must do instead:** task 9 narrows the claim to **`tests/test_cli.py`** — where it is
true, and where Fixture F's end-to-end arm therefore exists nowhere today — and names that artifacts test
as a **must-stay-green control** that never reaches `collapse_repeats`. **The general shape:** the design
grepped one file pattern and reported a claim about "the suite". *Sweep for the claim, not for the file the
claim was first noticed in.*

**2. Decision 7's unpaired narrowing must go in `of_col`/`against_col`, not in
`of_values`/`against_values`.** The design says *"the unpaired arm's `of_values`/`against_values` gain the
same narrowing in the same comprehension that builds them."* Read at `cli._comparison_step_blocks`:
`n_of` is `len(of_col)`, `n_against` is `len(against_col)`, and `of_clusters`/`against_clusters` are built
by keying off `of_col`/`against_col`. Narrowing only the value vectors would publish a count and group a
cluster set the difference did not come from. **What the task must do instead:** task 7 step 3 puts the
filter in `of_col`/`against_col`, and task 7's **third mutation** pins the difference by moving it back —
without that mutation this correction is prose, and *prose in a corrections section prevents nothing.*
The paired arm's `col_keys` is where the design put it and is correct, for the same reason: `diffs`,
`col_weights`, `col_clusters` and `n_paired` all derive from it. **And the unpaired arm has a fourth
consumer the design's reading would also break:** `permutation_over_contrast`'s `of_clusters`/
`against_clusters` are built as `[of_clusters[k] for k in of_col]`, so a value vector narrowed while
`of_col` was not would permute a cluster list of the wrong length beside it.

**3. The disagreement function needs no "plus the unit keys" parameter, because the walk is shared.**
The design specifies *"a new pure function in `stats.py` beside `repeat_spread`, taking the same four
arguments the collapse takes plus the unit keys."* The extra parameter exists to avoid re-deriving
membership — but re-deriving it is the real hazard, not the parameter. **What the task must do instead:**
task 4 step 1 extracts `_gather_repeats` once and both `collapse_repeats` and `repeats_disagreeing` read
it, so membership has **one implementation** and the signatures match exactly. A second walk would be a
second implementation of the membership rule, and the two would drift.

**4. `cli.py` does not import `_is_numeric`.** `grep -n '_is_numeric' src/publishable/*.py` → four lines,
**all in `stats.py`**. Decision 7's filter is written as if the predicate were in scope. **What the task
must do instead:** task 7 step 1 adds it to `cli.py`'s `from publishable.stats import (…)` block; the
precedent for a private cross-module import is `_arm_keys` from `runner`, already in that file.

**5. Decision 2 does not name the MIXED column, and the naive reading destroys a published metric
block.** The design gives two cases — constant and disagreeing — for a *non-numeric* column, and says
nothing about a column that is numeric in one repeat and non-numeric in another. It is reachable: each
repeat writes its own `units.parquet`, so H5a's within-file cross-row type rule does not bind across
repeats. Today such a column is **averaged over the numeric subset** (the inner loop skips the others).
**Measured, and this is what decides it:** `summarize_step` over a column with **one** `None` cell and
five floats publishes **no metric block for that column at all** (probe `p3`; the gate is
`all(_is_numeric(v) for v in raw)` over the whole column). So *mixed → `None`* would delete a **published**
column for **every** unit — a record-visible change nobody argued for — while for a genuinely non-numeric
column `None` costs nothing, there being no block. **What the task must do instead:** task 4's
`_across_repeats` returns the mean of the numeric values whenever there is at least one, so the mixed
path's published number is **exactly today's**; the disclosure is `W-STATS-REPEATS-DISAGREE`, and task 5's
**Fixture L** pins the value, the block's survival and the warning together, with an all-numeric second
arm as the can-fail control. **Flagged for the controller as a decision the design left open**, with the
rejected reading and its measured cost stated so the choice is checkable rather than inherited.

**6. `cli.py` passes `keys=set(collapsed)` to `repeat_spread`, which widens — and the obvious fixture
cannot see whether the inner gate held.** The second gate is `_repeat_spread_entries`' own
`_is_numeric(row[column])` filter. A fixture whose repeats record identical scores reports `std: 0.0`
**whether the gate held or not** — a dimension no assertion can see. Measured on a discriminating fixture
(two repeats 2.0 apart, four units carrying `score`, two carrying only a bool; probe `p5`):
`{'std': 1.0, 'n': 2, 'kind': 'seed'}` under the narrow keys and **identical** under the wide ones.
**What the task must do instead:** task 4 step 10 ships that fixture as **Fixture M**, so the claim is
pinned rather than inferred from a `0.0` that agrees with the bug.

**7. `resample_draws: 1998` is Fixture A's number at `seed=7, draws=2000`, not a constant.** The design's
§ The behaviour change table gives it as the `mean_score.resample_draws` literal. Reproduced exactly by
direct call — **and the same fixture shape run end to end at a run-derived seed gave `1999`.** Both are
correct; the count is the number of non-degenerate draws and depends on the seed. **What the task must do
instead:** task 1 arm B captures `1998` from its own `seed=7` call and arm E captures `1999` from its own
run, each labelled with the seed it came from, and **neither literal is reused across arms.**

**8. "§ Templates" names two sections in `reference.md`.** `## Templates: where parameters are defined`
(anchor `#templates-where-parameters-are-defined`) carries the four-operation contract, the `aggregate`
paragraph and the sentence Decision 10 edits; `## Templates` further down is the `my_assay` parameter
table. **What the task must do instead:** task 2 locates the paragraph by grepping for
`Columns are whatever the step` — one hit — rather than by the heading, and cites the long anchor.

**9. The scoping's two-condition Holm half REPRODUCES at `ee8085e`, and it moves two keys its paragraph
does not name.** Re-measured as the controller required, by running the console path with the H5b shape
installed on `publishable.cli` — **not copied.** All three cited literals hold: `n_paired` 4 → 6; the
`correction_level` swap (`mean_score` 0.025 → 0.05, `score` 0.05 → 0.025); and `score.ci95_corrected`
`[-0.10000000000000014, -0.09999999999999998]` → `[-0.10000000000000017, -0.09999999999999995]`.
**Additionally moved and unnamed in the design:** the derived contrast's own `ci95` **and**
`ci95_corrected`, `[-0.10000000000000009, -0.09999999999999998]` →
`[-0.10000000000000053, -0.09999999999999964]`, and both conditions' `aggregated…mean_score.ci95`.
**Unmoved, and load-bearing:** `vs_baseline…score.n_paired` stays `4`, `score.ci95` is identical, and
`n_rows.correction_level` stays `0.016666666666666666`. **What the task must do instead:** task 1 captures
this as **arm E**, a separate arm with its own key list, rather than folding it into arm B's seven.
*Merging two fixtures' moving sets into one count is the carried-summary failure this analysis' own
corrections were written about.*

**10. § The behaviour change's `n_rows` "today" value is `4.0`, and the design's own table says so — but
the reason is worth stating because it is not the one an implementer will assume.** `n_rows` is the row
count of the table `aggregate` receives, and today that table has **four** rows for a six-unit condition:
`collapse_repeats` returns `{}` only when **every** unit's every value is non-numeric, and drops **only
the units that carry no number** otherwise. Verified by direct call: the bool-only roster returns `{}`;
Fixture A's roster returns four units. **What the task must do instead:** task 4's Fixture A must have
**both** kinds of unit — some with a number, some without — because a bool-only roster cannot distinguish
*carriage* from *admission*, which is precisely what mutation (ii) tests.

**11. "Exactly two tests move" is dated to `5ee3a0c` AND to a shape this plan does not ship.** The scoping
measured it by installing a probe that carried values and admitted units — **with no across-repeats rule
and no mixed-column rule.** This plan's task 5 adds `None` cells and Fixture L's mixed rule. **This plan
did not re-run the suite under the shipped shape** and does not guess a number. **What the task must do
instead:** task 4 step 11 runs the whole suite and **reports the moved tests by name**, treating any third
as a finding; the scoping's figure stays attributed to its own shape and commit.

**12. `test_collapse_drops_a_bool_column_rather_than_averaging_it` does not pin what its name says.** It
asserts `"flag" not in collapsed.get("p0", {})`, and `p0` is **not in `collapsed` at all** today — the
collapse returns `{}` for that input, measured. So the test's name and docstring describe a **column**
drop while its subject is a **unit** drop, and `.get("p0", {})` is what hides the difference. **What the
task must do instead:** task 5's replacement asserts the key's **presence** and the value's being `None`
— two assertions — and names the old test in its docstring so a reader grepping for it lands there.
*A test whose name claims the guarantee* is one of this repo's recorded shapes, and this is an instance
nobody had filed.

**13. The measurements interaction is now OBSERVED, discharging the design's own request.** § What could
not be measured says *"A `measurements.parquet` written by a real run, so the interaction between Decision
2's repeat-level rule and a declared `data.units.measurements` collapse is reasoned … The plan should
build one."* Built: a real run declaring `{by: read_id, collapse: first}` whose step records
`{"score", "valid", "tag"}` per measurement. `measurements.parquet` holds both rows with both `tag`
values; `units.parquet` holds `tag: 'a'`; the collapsed table's `tag` is `'a'`; **no**
`W-STATS-REPEATS-DISAGREE` fires. **The two levels do not interact:** the declared collapse runs *inside*
each execution, so the repeat rule sees a constant. **And only `first`/`mode` can reach it** — a numeric
declared rule refuses a non-numeric value at `coerce_for_rule` first, which
`tests/test_artifacts.py::test_a_numeric_rule_coerces_a_recorded_string_before_applying` already pins.
**What the task must do instead:** task 5 step 6 pins all four observations rather than reasoning about
them.

**14. `repeats_disagreeing` must not join `publishable`'s importable surface.** § The importable surface
is an enumerated list and `stats.py` is implementation detail; `repeat_spread`, the sibling this function
is modelled on, is absent from `src/publishable/__init__.py`. Stated because a new **public** name in
`stats.py` invites the assumption. **What the task must do instead:** task 5 step 1 greps
`__init__.py` for `repeat_spread`, confirms the precedent, and exports nothing.

**15. Two `report.py` docstrings assert guarantees `cli.py` does not currently give, and this slice moves
both.** `grep -rn 'W-STATS-STRATUM-SHADOWED' src/publishable/*.py` returns **two** lines, and the second
is a docstring rather than an emit site. Read at `ee8085e`: `_is_strata_block` says *"`cli.py` does not
write this block at all when a recorded column of that name exists"* — **false for a non-numeric `by`
column today**, since the gate reads `step_summary` and such a column never reaches it, which is the
scoping's own measurement; and `_is_metric_entry` says a recorded `by` column *"keeps its value … as a
real metric entry"* — true for a numeric one and false for a non-numeric one, which keeps no metric block.
**What the task must do instead:** task 9 gains step 3b — narrow or delete both clauses, **changing no
code in `report.py`**, whose structural predicates are the sibling that already got this right. *A comment
or docstring claiming a guarantee the code does not provide* is this repo's most-recorded habit, and
**this instance is one the design did not name.**

**16. `statistics.null_test` widens by the same mechanism, and NOBODY enumerated it.** Neither the design
nor the scoping names `p_value` among the moving keys. `permutation_of_derived(collapsed, labels, compute,
seed, n=…)` takes the whole `collapsed` and rebuilds each draw's table from **whole rows**, exactly as
`percentile_of_derived` does — so admitting units widens the null distribution too. Measured on Fixture
A's two tables at `seed=7, n=500` with a label-reading `null_fn` (probe `p6`): `mean_score.p_value`
**`0.846307385229541` → `0.812375249500998`**, `null_draws` `500` in both. **The asymmetry is the same one
Decision 6 already documents for `n_paired`**, and both halves were established: a **recorded column**
gets no `p_value` from `summarize_step` at all (the write lives in the derived branch only), and a
**contrast's** p-value comes from `permutation_over_contrast` over `of_values`/`against_values` in the
unpaired recorded-column arm, which task 7 narrows — so it does not widen. **The contrast half was read
rather than run**, and is named as such. **What the task must do instead:** task 1 gains **arm F** with
those literals and task 15's `CLAUDE.md` list gains an eighth moving-key class. **No row of the four-row
table moves**: all eight `statistics` blocks in the feasibility analysis carry `null_test: null`, which the
truthy guard treats as undeclared — **say so explicitly, so a new moving key is not read as an
executability change.** *An enumeration that omits a class is the carried-summary failure in miniature*,
and this plan asserted one.

---

## Live overrulings — restated here because a ruling that overrules a brief has to reach the brief

A plan correction was once overruled when the plan landed, the overruling was recorded in the slice
ledger, and the plan was left carrying the old text — so the brief extracted from that plan still said
*delete*, and the task deleted. **The ledger reaches the controller and the reviewers; it reaches no
implementer.** These are in the plan itself, above and here.

1. **Fixtures E and H are task 4's, not tasks 10's and 11's.** The design's § What each change makes
   reachable overrules the scoping's task list: both go live at task 4 with no further code, and their
   pins would otherwise sit two batches later where the collapse batch's green suite is no evidence about
   either. Tasks 10 and 11 keep their **document and record** halves. **Task 10 and task 11's briefs must
   not re-add the pins**, and task 11 must not re-run task 4's mutation.
2. **The design's appended controller ruling post-dates its body and wins.** Its body's cost-if-wrong
   says *"no `diff` row points at the change"*; the ruling corrects that to *"the row that points at it is
   the one a reader is least likely to read"* — `uv.lock` is the carrier. **Any task quoting the
   cost-if-wrong must quote the corrected form**, and task 15 files the residual against H9.
3. **Nothing is minted to make the change more visible.** A fourth hash, a core-version record key, or a
   `diff` row of its own are each **refused by the controller**, not merely unbuilt. No task proposes one.
4. **`STARTER_STEP` is not changed** (Decision 12), and the scaffold's `aggregated: {step: {}}` is
   unchanged before and after. Task 4's Fixture B asserts that, and no task "fixes" the scaffold.
5. **`summarize_step` ships no code change** (Decision 4). A task that finds itself editing its body has
   found a disagreement and must report it rather than proceed.
6. **The mixed-column rule is § Corrections 5's, not the design's two-case reading.** Task 4's
   `_across_repeats` and task 5's Fixture L are the shipped form; a brief reading Decision 2 literally
   would return `None` for a mixed column and delete a published metric block.

---

## What could not be measured

- **The nine configs' real behaviour**, because neither `growth_screen` nor `publishable-llm` exists to
  install. Task 16's row-4 re-derivation rests on the payload and the attribute list quoted from the
  analysis, and **says so in the entry.**
- **The suite under the shipped shape** (§ Corrections 11). Routed to task 4 step 11 as a step, not
  guessed at here.
- **Whether any project in the wild reads `aggregated` for a column this slice newly admits.** Unknowable,
  which is why the disclosure is stated rather than a mitigation claimed.
- **Whether a run in which the SAME column is numeric for some units and non-numeric for others across
  the same repeat** (rather than across repeats) behaves as § Corrections 5 predicts end to end. The
  direct-call radius was measured (`p3`); the end-to-end shape is Fixture L's second responsibility and is
  task 5's to observe, not this plan's to assert.

---

## What the design leaves undecidable, for the controller

1. **The mixed column across repeats.** § Corrections 5 prescribes a rule and states the measured cost of
   the alternative. It is a **decision the design does not contain**, and it is record-visible in one
   direction: under the design's literal two-case reading a published metric block disappears. **If the
   controller prefers `None`, task 4's docstring, task 5's Fixture L and `CLAUDE.md`'s stoppage list all
   change, and a fifth newly-stopping thing joins the four.**
2. **Whether arm E belongs in the guard pin at all.** The design gives the pin four arms and puts the
   correction-family measurement only in prose. This plan makes it a fifth arm with a sole editor. The
   alternative — leaving it in prose — is what left the loose "byte-identical for a numeric-only run"
   framing alive long enough for the scoping to have to falsify it.
3. **The `where` on `W-STATS-REPEATS-DISAGREE`.** `aggregate_where` follows the sibling row in the same
   loop and is honest about neither the step nor the remedy; `data.units.measurements` names the remedy
   and may not exist in the file. Task 5 takes the sibling's answer with the sibling's reason. A
   controller who wants a step-shaped `where` is minting a second convention for one class of fault, and
   that is the trade.

---

## Plan self-review

- **Every claim about the code was measured at `ee8085e`**, by reading the file or **running** the
  behaviour, and `git diff --stat 5ee3a0c ee8085e -- src tests` is empty — so the scoping's baseline is
  reusable while its claims are re-checked. **Sixteen corrections**, seven of which reshape a task:
  correction 2 (task 7's unpaired filter moves and gains a mutation), correction 3 (task 4 extracts a
  shared walk), correction 5 (task 4's collapse rule and task 5's Fixture L), correction 6 (task 4 gains
  Fixture M) correction 9 (task 1 gains arm E), correction 15 (task 9 gains step 3b) and correction 16 (task 1 gains arm F and the moving-key enumeration gains an eighth class).
- **The required re-measurement was performed, not copied.** The scoping's Holm half reproduces and moves
  two keys its paragraph does not name. **It was not a non-reproduction, so no finding is owed there** —
  but the two extra keys are one.
- **Both design-flagged items are discharged:** the Holm half re-measured (correction 9), and the
  `measurements.parquet` interaction **observed** rather than reasoned (correction 13).
- **Every task states its surface, its mutations with two branches that can differ, what it must not
  touch, and its § Errors/§ Warnings work as one row per code covering every emit site.** Five mutations
  are named **blind in advance** — the annotation sweep, four docstring/comment edits, and the document
  tasks — and **each owes a named replacement.** One is named **REJECTED rather than blind** (task 5's
  fourth), because it is not blind and calling it so would be wrong.
- **Three pin arms have no authorized editor** (A, C, D) and three have exactly one each (B, E and F,
  all task 4). Arm A's rule and its fixture's framing are stated as **two labelled sentences**, because the
  loose version is what the scoping falsified.
- **The four collisions that stay where they are** — H3c-3's `fold_members`, the
  `report_by`-under-`resample` gap, `repeat_spread`'s `std: 0.0`, and the degenerate-stratum warning's
  stale owner — are named in the Global Constraints, and `fold_members` is **pinned** (Fixture K) rather
  than only named.
- **Batch 2 gets a real-command review; every batch gets a review, including the last.**
- **The four-row table is repeated with rows 1-3 unchanged, no fifth number appears, and row 4's
  re-derivation is appended as a correction to a published figure** rather than edited into it.
- **No count phrase, positional row locator, call-site enumeration or line-number citation appears above**
  except where a count is the thing being pinned (the gate literals, the 20 annotation sites, the moving
  keys) or the thing being corrected.

---

## Controller rulings, 2026-08-22 — appended AFTER this plan was written, and they bind every task below

**These are here because a ruling that overrules a brief has to reach the brief.** The ledger reaches the
controller and the reviewers; it reaches no implementer. A brief extracted from this plan carries these
paragraphs, so **no task may act on the superseded reading above.**

### Ruling 1 — the mixed column: mean over the values that exist, and the `n` must be the contributing count

**The question the plan leaves open** (its correction 5): a column that is numeric for some units and
`None` for others. The plan measured that *mixed → `None`* deletes the whole column's published block for
every unit, and proposed the mean of the numeric values with a warning.

**Ruling: the mean over the units that recorded a value, and `n` reports the number that contributed —
not `completed`.** Grounds, measured rather than reasoned:

- **A mixed *type* column cannot reach this question at all.** `_check_column_types(rows, ["v"])` refuses
  `float` beside `str` (*"column 'v' recorded both a float (unit 'row 0') and a str (unit 'row 1')"*) and
  `bool` beside `float`, while `int` beside `float` is accepted and promotes. So the only mixed column that
  survives H5a's write side is **numeric beside `None`**, which is exactly the case this ruling is about —
  and `None` is a legal recorded value (`coerce_scalars({"valid": None})` returns it), which this design
  established.
- **Dropping the column because one unit recorded `None` IS the defect this slice exists to end.** A
  silent drop that costs every unit its block because one cell is absent is the same fault at a different
  granularity, and choosing it here would mean shipping the defect's own shape as the fix.
- **`n` counting contributors rather than `completed` is what makes the interval true.** *Units are the
  inference base* and every interval core reports is computed from the per-unit table; an interval over
  five values published beside `n.completed: 240` is a lie about its own precision, and it is the kind of
  lie no later reader can detect from the record. The four-way `n` (`resolved`/`completed`/`ineligible`/
  `failed`) is not widened — this is a per-metric contributing count, reported where the metric is.

**Amendment to this ruling, same day, from batch 1's review — the reachable case, named.** Batch 1
shipped an all-or-nothing read sentence that this ruling rejects, and repairing it turned up the
distinction the ruling should have drawn in the first place. **There are three mixtures, not one:**

| The column holds | What reaches `aggregated` | Why |
|---|---|---|
| Non-numeric for **every** unit (a `str` column, a `bool` column) | **No metric block**, and the column still reaches `aggregate`'s table | There is no mean of strings. This is H5b's main case and the all-or-nothing wording is **correct here** |
| A number for some units, `None` for others | **A block computed over the units that carried a number**, with the contributing count reported and a warning naming it | This ruling's case. `None` is a legal recorded value, and a `None` cell means *this unit has no value for this metric* — which is the partial-coverage case the rest of the system already handles by counting the unit out |
| `str` **beside** a number | **Cannot occur.** `_check_column_types` refuses it at `finalize` — measured: *"column 'v' recorded both a float (unit 'row 0') and a str (unit 'row 1')"* | So a read rule for it describes an unreachable state, and a document that states one invites a later reader to build against it |

**The all-or-nothing sentence is therefore not wholly wrong — it is right about the first row and wrong
about the second**, which is why it read as plausible and passed its own task. The repair keeps its first
clause and replaces the second.

**Cost if wrong:** a metric whose coverage is a twentieth of the roster publishes an interval that reads
like every other metric's, distinguished only by a number a reader has to notice. **That is why the warning
is not optional and must name the count**, and why a task may not downgrade it to a silent computation.
The alternative — refusing the run outright — is rejected because a partially-recorded metric is ordinary
(a step that measures only what it can measure is exactly what `io.skip` exists beside), and a refusal
would make `None` unusable as the legal value H5a made it.

### Ruling 2 — `W-STATS-REPEATS-DISAGREE`'s `where` follows its sibling in the same loop

Use `aggregate_where`, the sibling row in the same loop, **and do not name `data.units.measurements` in
the `where`**. Grounds: *the sibling that already got it right is the first place to look*, and the
remedy-naming alternative points at a config field that **may not exist in the file being validated** —
a `where` that names an absent path is a diagnostic pointing at nothing. Name the remedy in the message
if it helps; the `where` locates the fault.

### Ruling 3 — the correction-family measurement stays IN the pin, not in prose

The plan asks whether the Holm/`fdr_bh` half of the moving-key measurement belongs in the guard pin at
all. **It does.** Grounds: this slice's predecessor produced **three miscounts in three consecutive
batches**, every one in a number carried as prose and framed as *read rather than estimated*. A
correction-family effect is the single least intuitive thing this slice moves — a column with **no
non-numeric value anywhere** gets a different `ci95_corrected` because admitting a unit flipped a rank —
and prose is exactly the medium those three miscounts travelled in. Arms E and F stand as captured.

### Ruling 4 — the `scripts/` finding is real, and it is not this slice's to fix

The plan is right that `scripts/` does not exist in this repo, so `CLAUDE.md`'s claims that briefs are
extracted by `scripts/task-brief` and that `scripts/sdd-workspace` rewrites `.superpowers/sdd/.gitignore`
are **documented rules with no code behind them** — the misreading `CLAUDE.md` itself names. Both scripts
live in the installed `superpowers` plugin, not in this repository, and the `.gitignore` clobber is a real
observed behaviour with a wrong path attached. **The controller fixes `CLAUDE.md` directly; no task here
touches it for this reason**, and no task may cite `scripts/` as a repo path.

---

## Controller rulings, second set — 2026-08-22, from batch 2's review

**Ruling 5 — Ruling 1's "warning naming the count" becomes `W-STATS-COLUMN-THIN`, checked against
`limits.min_reported_n` at `run` time.** Batch 2 shipped Ruling 1's contributing count and not its
warning, and the review is right that code and both document passages then diverge from the ruling
together. **The ruling is amended rather than enforced as written**, on grounds the ruling itself did not
have:

- **Its own justification is now satisfied by the count.** Ruling 1 argued the warning was *not optional*
  because *"an interval over five values published beside a `completed` of two hundred is a precision
  claim no later reader can catch."* Measured at HEAD, `run.yaml` publishes `n.completed: 3` for a column
  three of six units carry — **so the record no longer makes that claim**, and the warning's job shrinks
  from *preventing a lie* to *telling the person who never opens `run.yaml`*.
- **An unconditional warning is the wrong shape for an ordinary event.** A step that measures only what it
  can measure and records `None` otherwise is normal; warning on every such column would fire on runs with
  nothing wrong, which is how a warning becomes noise a reader learns to skip.
- **`limits.min_reported_n` is already this floor, and three shipped rows use it exactly this way** —
  `W-STATS-CONTRAST-THIN` at `run` against a realized denominator, `W-STATS-STRATUM-THIN` at `run` against
  what completed, and `W-STEP-ESTIMATE-N` citing it as *"the disclosure risk `limits.min_reported_n` exists
  to catch."* **The sibling that already got it right is the first place to look**, and a second threshold
  for the same hazard would be a second source of truth.

So: **one warning per (condition, step, column) whose contributing count is below `limits.min_reported_n`,
naming the column and the count.** Cost if wrong: a project declaring a floor of 1 gets no warning for a
column one unit carries — and the honest `n` is then the only signal, which is the state batch 2 already
shipped, so the downside is bounded by what exists today.

**Ruling 6 — the § Warnings row's granularity must match the loop.** *"Once per (condition, step)"* is
false of the code: the emit site iterates columns and a two-disagreeing-column step prints two. **Fix the
row, not the loop** — per column is the useful granularity, and the row is the thing that was wrong.

**Ruling 7 — delete the false premise, do not rewrite it.** `W-STATS-REPEATS-DISAGREE`'s message says a
mixed numeric/string column *"is not a number"* and that *"those units carry no value for it"* while the
record publishes a value for them; `reference.md`'s § Warnings row states the same premise normatively;
and `repeats_disagreeing`'s own docstring contradicts both. **Delete the clauses that make the false
claim.** *A rewrite invents; a deletion cannot* — and the same applies to `_across_repeats`'s ground
*"because `summarize_step` requires all carried values numeric"*, which task 6's own gate change
falsified and which its own docstring contradicts three paragraphs later.

**Ruling 8 — the two unpinned changes get pins, and the ninth moving-key class gets an arm.** The empty-
record admission (`n_rows` 4.0 → 6.0) and `_repeats_disagree`'s `(is-numeric, value)` tuple are both live
behaviour with **no test that fails when they are removed** — that is the *five slices weakening a pin
quietly* shape arriving as *never pinned at all*. And the `report_by` stratum path is a **ninth** moving-key
class the enumeration omits, carrying a **third** distinct `resample_draws` literal; it needs an arm, even
though `level_collapsed` is a projection with no separate code path. **A key that moves and appears in no
arm is precisely what the guard pin exists to catch.**
