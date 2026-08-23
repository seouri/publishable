# H9a — whole-branch gate — **HOLD**

**Gated 2026-08-23 at `12a9370`**, branch `h9a-re-entry-seam`, 27 commits and
`+7137/−65` lines against `main`. Worktree clean at review time; every mutation reverted by
**editing/copying back** and verified by **re-running**, never by `git status`.

## Verdict: HOLD on two Majors, both closeable by document-and-records edits alone. No code defect found.

| # | Sev | Finding | Route |
|---|---|---|---|
| 1 | **Major** | The widened `W-APPARATUS-UNANSWERED` row now contradicts itself and asserts that **`dry-run` replays a ledger** — the insertion displaced the antecedent of the following `freeze` sentence | `reference.md` § Warnings core reports — move the clause after that sentence, or bind it |
| 2 | **Major** | **Three records claim `publishable draft new` keeps its exit code and prints the arity message. Measured: exit 2 → 1, `E-IO-FAILED`, and a config path IS read.** One of the four enumerated behaviour changes is misdescribed, including inside a **dated** § Executability entry | append a correction to design § 5 and plan task 4; correct § Executability item (3) in place with a stated replacement |
| 3 | Minor | *"Fifteen § Errors / § Warnings rows"* is **thirteen** in task 12 (14 with the fix round, and the 14th is a widening, not a narrowing) — and the wrong number is now in `CLAUDE.md` | `CLAUDE.md`'s H9a paragraph; note on the report |
| 4 | Minor | The `command_run`-residue filing claims the signpost is landed on by all 34 `cli.py` hits. Measured **2 of 34** — *names* is not *sits inside* | `spec-defects.md` — correct the mitigation sentence, keep the ownership |
| 5 | Minor | `_dry_run_step_dirs`' `dict.fromkeys` comment argues the de-duplication is *"real rather than defensive — under `collapse` two repeat executions of one step in one condition share a directory"*. `collapse` **is** `len(repeats) <= 1`, so there is only one such execution: the case cannot occur | `cli.py` — delete the justification (a deletion cannot invent), or state it as defensive |

Findings 1, 3, 4 and 5 and the batch-level detail for 1–4 are in
[`task-b5-review.md`](task-b5-review.md); finding 2 is a gate finding and is written out in both.

**Suite: 3019 passed, 1 skipped, 2 xfailed** in 215.58s, run directly in the foreground after clearing
stale `pytest-of-joon` dirs and every `__pycache__`. `ruff check` → *All checks passed!* ·
`ruff format --check` → *93 files already formatted* · `mypy` → *Success: no issues found in 52 source
files*.

**Delta fully accounted, derived rather than chained.** An `ast` walk over every test file the branch
touches, comparing `main` to HEAD:

```
tests/test_apparatus.py: +0 -0
tests/test_cli.py:      +46 -0
TOTAL new test functions: 46   removed: 0
new @parametrize lines in the branch diff: 0
```

`main` 2973 + 46 = **3019.** `test_apparatus.py` changed and added no test — its whole diff is task 13's
docstring retarget, confirmed by reading. No test was removed, renamed away, or skipped.

---

## 9. The extraction is **still** behaviour-preserving at HEAD — measured, not inherited

This is a different question from batch 2's, which was measured at `cd91adc`; tasks 3–14 have since
rewritten `cli.py` around `_prepare_run`. Re-measured at HEAD against a `main` worktree, **two console
scripts from two editable installs**, with the positive control printing a distinct
`publishable.__file__` per side:

```
HEAD side: /Users/joon/src/tries/publishable/src/publishable/__init__.py
MAIN side: …/scratchpad/mainwt/src/publishable/__init__.py
```

One real out-of-repo project, committed once, then run once from each side: 4 steps across three
scopes (`run` → `repeat` → `summary`), `baseline` + a 2-value grid = 3 conditions, 2 seed repeats, 60
units with two attributes, a template `aggregate` deriving a metric, one `confirmatory` hypothesis.
**Batch 2's normalization list used verbatim** (timestamps `at`/`started_at`/`wall_seconds`; `run_id`
and everything derived from it; absolute paths; `hostname`) — reused rather than rewritten, because a
list written now is a list written after seeing a diff.

| Comparison | Result |
|---|---|
| `run.yaml` leaf by leaf, **in order** | **284 leaves each, key order equal, 0 leaf differences** |
| Run-directory tree, path by path (kind, size, sha256) | **36 paths each, 1 difference** — `config.yaml`, attributed below |
| `sweep.yaml` leaf by leaf | 31 leaves each, **equal** |
| `executions.jsonl`, line by line, key by key | 8 lines each, identical key lists, **0 unattributed key differences** (only `started_at`/`wall_seconds`) |
| stdout, line by line | 5 lines each, **equal** |
| stderr | **equal** (both empty) |
| Exit code | **equal** (0) |

**The one difference, attributed individually:** the copied `config.yaml` differs because the two sides
were pointed at two different `output_dir` values so they would not collide.
`diff <(sed 's|…/resA|<OUT>|g' A/config.yaml) <(sed 's|…/resB|<OUT>|g' B/config.yaml)` → **empty**.
That is normalization item 3, absolute paths. **Unattributed differences: ZERO.**

Note this comparison is strictly stronger than a green suite: `git.commit`, `code_hash`,
`parameters_hash`, `input_manifest_hash`, `uv_lock_hash` and `units_hash` are **compared as values**
and are equal, because the project is committed once and run twice.

## 8. Cross-batch interactions — every earlier guard mutated, every one still fails

The concern is a guard made dead, or a claim falsified, by a batch that landed on top of it. Five
mutations, each against `tests/` with the named `-k` selection, each reverted by copying the file back
and re-running:

| Mutation (which batch's guard) | `-k` selection | Result |
|---|---|---|
| Drop `and not allow_dirty` — **task 2's single changed line in phases 1–5** | `arm_e_a_dirty_tree or fixture_q or h9a_draft or h9a_fixture_r` | **1 failed** (`-x`), on `E-CODE-DIRTY`'s own text |
| `command_draft` passes `draft=False` — **tasks 3/4's wiring** | `h9a_draft or fixture_q or fixture_r` | **1 failed**, 2 passed |
| `dry-run` probes under the **wide** cfg (`cfgs[-1]`) — **task 10's siting** | `h9a_fixture_v` | **1 failed**, 1 passed |
| Drop the **flag** half of the shared arity arm — **task 4's first genuine pin** | `arity or no_flags or json` | **1 failed**, 4 passed |
| Delete `draft`'s stderr notice — **Decision 10, task 3** | `h9a_draft or fixture_q` | **1 failed** |

Nothing earlier is dead. Two further checks in the same class:

- **Task 2's resolver containment, now with three callers, verified by behaviour.** A resolver plugin
  raising with a credential declared through `Param(requires_env={"alpha": ["RR_TOKEN"]})` and set in
  `.env`, run through the real console script: `validate`, `dry-run`, `draft` and `run` each exit 1
  with `E-RESOLVER-RAISED`, the secret **absent** and `<redacted:` **present**. So the widened row's
  claim that `_prepare_run` *"contains the identical raise at each of those three commands"* is true of
  the code, not only of the row. **My first attempt at this fixture passed vacuously** (a bare-string
  `requires_env` made core iterate the string per character and left `credentials` empty, so the secret
  printed at all four commands **and on `main`**) — recorded because it is the exact trap Fixture W's
  note names.
- **Task 10's probe containment**: a probe raising with a declared credential → exit **5**,
  `E-APPARATUS-RAISED`, `<redacted:REV_SECRET>`, secret absent. Decision 14's split (`EXIT_EXTERNAL`
  for `RAISED`, `EXIT_WRONG` otherwise) exercised in both directions — the non-`RAISED` branch by a
  declared fact the probe omits entirely, which earns `E-APPARATUS-FACT-MISSING` and exit 1.

**What the gate found that no per-batch review could:** finding 1 (a row edit in batch 7 breaking the
sentence after it, only visible by diffing `main`→HEAD row by row) and finding 2 (a records claim
falsified in batch 3 and still standing in batch 7's own dated entry — the chain crosses four batches).

## 8b. Two checks the first pass owed: every `tests/` deletion, and the fixed-file list against a real run

**Every deletion in `tests/` across the whole branch attributed individually — not a name count.**
`+46 / −0` counts test *function names* and cannot see an assertion deleted from a pre-existing test or
a shared helper widened. The command that can:

```
$ git diff main...HEAD -- tests/ | grep '^-[^-]'
     1-7   test_apparatus.py — the getsource pin's docstring, replaced by the enumerated-bodies version
     8     test_apparatus.py — `cli_source = inspect.getsource(cli_mod.command_run)`
     9     test_cli.py       — `assert ("dry-run", "NOT BUILT") in tables["Command"]`
```

**Nine deletion lines on the whole branch, and both edits are authorized**: lines 1–8 are the
controller ruling `ec43c95` (the phase-constant pin retargeted to an enumerated list of bodies, which
the ledger records and whose post-edit state was specified), line 9 is arm F's, task 9's, its sole
authorized editor. Per commit: `ec43c95` 8, `a684f1b` 1, **every other commit 0** — and
`git diff 204fbf7^...HEAD -- tests/` has **zero** deletions, so the batch 6–7 report's *"additive at
every hunk"* claim is true as stated. **No pin was weakened.**

**And by history rather than only by endpoints.** Comparing arm bodies `190de68` → HEAD proves the
content is what task 1 captured but cannot see an edit-and-revert. Two commits' `test_cli.py` diffs
contain an `def test_h9a_arm_` line at all: `190de68` (the ten, added) and `137d55e` (task 3), whose
only occurrence is a **hunk-header context line** — it appended a new section after arm E and edited no
arm body. No edit-and-revert exists.

**`dry-run`'s fixed-file list has no fixture pinning it, so I pinned it by running.** The design's
fixture table pins the step **directories** set-to-set (Fixture U) and pins nothing for the fixed
**files** — and task 10 added a conditional (`apparatus/probes.jsonl`) on top of task 7's seven-entry
tuple, which is a cross-batch interaction inside the one list this command exists to print. Both
shapes, `dry-run` then `run`, same config, compared set to set:

| Shape | `dry-run` printed | The run actually wrote (outside step directories) |
|---|---|---|
| Probe-declaring, no group axis / holdout | 9: `apparatus/probes.jsonl`, `config.yaml`, `environment/pyproject.toml`, `environment/repo_root.txt`, `environment/uv.lock`, `executions.jsonl`, `manifest/input.json`, `run.yaml`, `sweep.yaml` | **the same 9** |
| No probe | 8: the same list without `apparatus/probes.jsonl` | **the same 8** |

**Exact agreement in both directions.** The only files a run wrote that the list omits are
`units.parquet` inside step directories — deliberately excluded, argued in the transcript's own last
lines, and covered by the step-directory list. Specifically checked for and **absent**: no `run_<id>/lock`
survives completion, so the release is real and its absence from the list is right; and
`environment/uv.lock`'s `lock_path is not None` guard tracked what `_execute_prepared` wrote in both
runs. **No code defect in the list.**

## 10. The guard pin — arms A–E untouched, F moved exactly as specified

**Arms A–E have no authorized editor.** All ten of task 1's arm functions extracted by name from
`190de68:tests/test_cli.py` and from HEAD and compared as full bodies: **SAME for all ten**, byte for
byte.

**Arm F** (`test_reference_cli_tables_are_parsed_at_all`) is the only one with an editor, task 9. Two
commits touch that region of the file: `d4af219` (task 4) and `a684f1b` (task 9). Task 4 added two new
test functions nearby and **did not touch arm F's body**; task 9 made exactly the specified edit —
`("dry-run", "NOT BUILT")` → `("dry-run", "built")` **plus** the added
`assert ("resume", "NOT BUILT") in tables["Command"]`. `("validate", "built")` untouched; both
`set(NOT_BUILT_COMMANDS)` / `set(NOT_BUILT_GENERATORS)` equalities untouched and self-maintaining.

**Every arm proven able to fail, by a mutation in production code**, each with its `-k` scope:

| Arm | Mutation | Result |
|---|---|---|
| A | `run_record.py`: `"schema_version": SCHEMA_VERSION` → `"9.9"` | **1 failed** |
| B | `cli.py`: `run.yaml →` → `run.yaml ->` in the final print | **1 failed** |
| C | `cli.py`: swap `EXIT_PARTIAL`/`EXIT_FAILED` in the status→exit mapping | **2 failed**, 1 passed |
| D | `runner.py:828`: drop `"wall_seconds"` from the ledger line | **1 failed** |
| E | `cli.py`: drop `c.has_errors` from the validate gate | **1 failed**, 2 passed |
| E | `cli.py`: drop `and not allow_dirty` | **1 failed** |

**Arm D is worth a line.** My first attempt dropped `"wall_seconds"` at `run_record.py:73` and the arm
**passed** — that site writes `run.yaml`'s own per-execution list, not `executions.jsonl`. The real
site is `runner.py:828`. *A mutation applied to a proxy* is the shape, and I only found it because I
treated the pass as evidence about my mutation rather than about the arm.

## 11. `dry-run` creates nothing — whole-tree snapshot, and it can fail

Recursive `{path: (size, sha256)}` over **73 paths** across `output_dir`, the project repo and
`input_dir`, taken before and after a real `main`-equivalent invocation through the console script:

```
results  ADDED [] REMOVED [] CHANGED []
proj     ADDED [] REMOVED [] CHANGED []
data     ADDED [] REMOVED [] CHANGED []
total paths compared: 73
```

**Can-fail control:** one `mkdir` under `output_dir` and the same snapshot prints
`control sees ADDED: [.../results/scratch_probe]`.

**Decision 12's named residue confirmed rather than accepted.** Re-run with `__pycache__` *included*:
the only two added paths anywhere are `templates/__pycache__` and
`templates/__pycache__/rev_assay.cpython-313.pyc`, and **nothing** under `output_dir`. No lock was
taken (no run directory exists to hold one).

## 12. `draft` relaxes without widening — Ruling T, built and run

- `git diff main...HEAD -- src/publishable/provenance.py src/publishable/hashes.py` → **empty**. The
  pathspec, the `-c` neutralization flags and `HASHED_TREES` are byte-unchanged.
- **The uncommitted-root-file case** (the one the ruling is about): `NOTES.txt` at the repo root,
  `git status --porcelain -- src templates` → **empty**, whole-repo porcelain → `?? NOTES.txt`.
  `run` → **exit 0**. `draft` → exit 0, **no notice on stderr**, and the record says
  `draft: true` / `code_dirty: false` — Decision 9's claim, verified on a tree verified dirty *outside*
  the two hashed trees. The gate did not widen.
- **The uncommitted-`src/**`-file case:** `run` → exit 1, `E-CODE-DIRTY`; `draft` → exit 0, notice on
  stderr (*"notice  draft   src/** or templates/** is uncommitted; recording draft: true and
  git.code_dirty: true"*), record `draft: true` / `code_dirty: true`.
- **`dry-run` on the same dirty tree** (Decision 8): exit 0, **zero** `E-CODE-DIRTY` on either stream.

## 13. The four disclosed behaviour changes

| # | Real? | Disclosed where a user would look? |
|---|---|---|
| 1 | **Yes** — `main`: both exit **2** with *"is specified but not built"* on stderr; HEAD: both dispatch (`exit=1`, `E-IO-FAILED`, for a missing path) | **Yes** — § CLI reference's `Status` cells are `built`, matching `NOT_BUILT_COMMANDS` exactly; § Operation commands and § Draft runs describe both |
| 2 | **Yes** — `publishable draft a b` prints `` `draft` takes exactly one path and no flags`` at HEAD, the unbuilt diagnostic on `main` | **Yes** — the invariant *operation commands take paths and nothing else* is the documented rule; the message is the rule's own wording |
| 3 | **NO — see Major 2.** Measured exit **2 → 1**, the line is `E-IO-FAILED` not the arity message, and a config path **is** read | Not disclosed anywhere a user looks, and **misdescribed in three records** |
| 4 | **Yes, and re-measured at HEAD** — § 9 above | **Yes** — no `run.yaml` key added, removed or reordered; `schema_version` unbumped; no `E-`/`W-` minted or retired |

## 14. Both consistency passes

**Mechanical, re-derived independently.** My own checker over the seven governed files —
`README.md`, `design-principles.md`, `experimental-designs.md`, `reference.md`,
`feasibility-llm-growth-studies.md`, `CLAUDE.md`, `spec-defects.md` — with GitHub's slugger rules
(`_` **kept**), escaped-pipe-aware table splitting, and fenced blocks skipped:
**`--- 0 problems over 7 files`**. **Proven able to fail**: 8 problems on a purpose-built bad file,
one per class, fenced content correctly ignored.

**Cross-document, over the four documents only.** Every sweep filtered the **file list**, named each
file individually, and carried a can-fail control; every hit attributed individually.

| Class | Result |
|---|---|
| The shared worked example | `cohort-pilot`'s intervals **not narrowed back** — all eight literals present at their expected home counts, and the branch diff of the four documents contains no line carrying any of them. Control `0.29801` → 0 |
| The `15` / `20` execution figures | 3 homes for `15`, all attributed to the `demo`'s genuinely one-step pipeline or to one step's own count; `20`/`4,800` only in § Before you spend it. No contradiction |
| Config completeness | no config field added or removed by the branch (diff filtered to `^[-+]\s{2,}[a-z_]+:` → empty) |
| Enum comments | none moved |
| `apparatus.PHASES` vs § The apparatus files | `PHASES` = 4 members; § The apparatus files names three ledger phases **plus** the reserved-name paragraph; *"the four places a probe runs"* consistent at both homes; `three outcomes` → 0 contradicting homes |
| Declared vs derived | unchanged |
| Versions | `CITATION.cff` `0.1.0` = `reference.md` `publishable_version: "0.1.0"` |
| Prevented mistakes | `experimental-designs.md:375`'s row still describes a structurally-prevented mistake (the gate fails the run); only the *recording* verb was scoped |
| The `Status` column (moved twice) | exact agreement in **both** directions with `NOT_BUILT_COMMANDS`, `OPERATION_COMMANDS`, `NOT_BUILT_GENERATORS` |
| House style | no en dash in an added heading; no ASCII `x` between digits |

## 15. The development record was not retro-edited

`docs/superpowers/plans/` and `docs/superpowers/specs/` are **+61/−2**, and the two "deletions" are the
`~~` strikethrough markers wrapped around the superseded sweep paragraph — the text is preserved in
full beside its replacement, which is the form this repo requires. The design's 19 lines are pure
appends. `docs/superpowers/H9-SCOPING.md` is **untouched**. `spec-defects.md` — the one live list — is
where entries are struck, and both strikes carry their resolution.

## 16. Gates

`ruff check .` → *All checks passed!* · `ruff format --check .` → *93 files already formatted* ·
`mypy` → *Success: no issues found in 52 source files* · `pytest` → **3019 passed, 1 skipped, 2
xfailed**, `main`'s 2973 + 46 new test functions, accounted above.

---

## What HOLD costs and what closes it

Both Majors are **document-and-records** edits and neither touches `src/`, so the suite figure above
survives them:

1. Reorder or rebind one sentence in `reference.md` § Warnings core reports.
2. Correct § Executability item (3) with a stated replacement inside the dated entry, and **append**
   the same correction to design § 5 and plan task 4.

Then the three Minors, none of which needs to block: `CLAUDE.md`'s thirteen, the filing's mitigation
sentence, and one comment in `cli.py` whose justification cannot occur.

**The shape worth carrying out of this gate.** Both Majors are the same fault in two currencies: a
claim that was *correct when written, adjacent to the thing that changed, and never re-read.* Finding 1
is a sentence whose subject moved when a clause was inserted above it. Finding 2 is a disclosure whose
own implementer measured the truth, wrote it into a test docstring, and left three records saying
otherwise — including the one section this repo built specifically so that build claims expire loudly.
The report's own addendum named the rule (*when you edit one line of a block, diff the block*) and both
survivors are one step further out: **when a batch falsifies a claim, grep for every record that
carries it — including the ones a later task will repeat it from.**

---

## Whole-branch fix round — 2026-08-23, at `bf2a76e`

All five findings closed. No code defect; the one `src/` edit is a comment correction, behaviour
unchanged (verified below). Full suite re-run directly in the foreground after clearing stale
`pytest-of-joon` dirs and `__pycache__`: **3019 passed, 1 skipped, 2 xfailed in 217.22s** — identical to
the gate's figure, nothing regressed. `ruff check .` → *All checks passed!* · `ruff format --check .` →
*93 files already formatted* · `mypy` → *Success: no issues found in 52 source files*.

**Major 1 — CLOSED.** `docs/reference.md` § Warnings core reports, the `W-APPARATUS-UNANSWERED` row:
moved the "Its counts are the run's own accumulated `run_start`/`pre_execution` history, replayed from
the ledger ... plus the one round `freeze` itself just probed" sentence to sit immediately after the
`freeze` sentence it describes, and bound it explicitly (`` **`freeze`'s own counts** are...``). The
`dry-run` sentence now ends on its own clause ("over that round's own in-memory counts alone ... printed
to stdout through a fresh `Collector` before the transcript") with no trailing claim about a ledger.
Checked the other twelve edited rows in the same table for the same displaced-antecedent shape by
re-reading each in full context (not just the row cell) — none has a pronoun whose referent moved; each
either replaces a name in place or appends at a clause boundary. The edit is confined to one table cell;
no other row's content or any anchor moved (confirmed by `git diff` — the file diff is a single line).

**Major 2 — CLOSED.** Measured through the real installed console script before touching anything:
`uv run publishable draft new` → exit `1`, `` error   E-IO-FAILED          No such file or
directory``; `uv run publishable dry-run new` → the same; `uv run publishable draft a b` → exit `2`,
the arity message (unaffected — item (2)'s claim, correct). So item (3)'s claim ("same exit code,
different line, and again no config is read") is wrong on all three counts: exit code changes 2 → 1,
the line printed is not the arity message, and `_prepare_run` does read `"new"` as a path and fails to
open it. `"new"` is a single token, so `rest == ["new"]` never trips the shared arm's
`len(rest) != 1` at all — the call dispatches straight into `command_draft`/`command_dry_run` and fails
inside `_prepare_run`, never reaching the arity arm. Task 4's own test docstring already said this
correctly. **Appended, never retro-edited:**
- `docs/superpowers/specs/2026-08-23-re-entry-seam-design.md` § 5, after item 4 and "What does not
  move" — a dated correction replacing item 3's last two sentences.
- `docs/superpowers/plans/2026-08-23-re-entry-seam.md` Task 4 — a dated correction replacing the "one
  shipped answer moves" paragraph's claim.
- `docs/feasibility-llm-growth-studies.md` § Executability on this build, inside the
  "Measured on 2026-08-23 against commit `c925416`" entry itself — a dated correction appended after
  the entry's closing paragraph, on the precedent of the two corrections already living in that section.
  No figure in the entry's table moved and no fifth number was minted; the correction is to the
  description of change (3), not to any row's count.

**Minor 1 (§ Errors/§ Warnings row count) — CLOSED.** `CLAUDE.md`'s H9a paragraph said "Fifteen § Errors
/ § Warnings rows were narrower than their code, every one narrowed by this slice itself." Corrected to
**"Thirteen ... each narrowed by this slice itself"**, with a new sentence stating the fourteenth
(`E-CODE-DIRTY`) separately: that row had gone wide in an earlier batch and was narrowed back by the
same fix round — a widening caught and closed, not one of the thirteen narrowings this slice's own
additions caused. This is not a dated record, so corrected in place rather than appended.

**Minor 2 (`command_run`-residue mitigation sentence) — CLOSED.** `docs/superpowers/spec-defects.md`'s
open filing said "A reader who greps `command_run` in `cli.py` lands on it: it is inside the function
every one of those 34 hits names." Re-measured by `ast` span over `cli.py`: `command_run`'s own span is
`(4123, 4148)`; of the 34 lines matching `command_run`, exactly **2** fall inside that span
(`[4123, 4134]`), the other 32 belonging to other functions' docstrings/comments
(`_resolved_group_axes`, `_cond_beside_n`, `_make_null_fn`, `_resolved_resample`, and others) that merely
name `command_run` in passing. Corrected the mitigation sentence to say the signpost is reached by 2 of
34 `cli.py` hits (2 of 195 overall), not by all 34; the filing's ownership routing (unassigned, with the
reason) is unchanged — this is `spec-defects.md`'s live list, corrected in place rather than appended,
since a live list is not one of the dated records.

**Minor 3 (`_dry_run_step_dirs` comment) — CLOSED.** The comment argued the `dict.fromkeys`
de-duplication is "real rather than defensive — under `collapse` two repeat executions of one step in
one condition share a directory." `collapse` is exactly `len(prepared.repeats) <= 1`
(`src/publishable/cli.py:_dry_run_step_dirs`), and `scope.build_plan` emits at most one
`(step, condition, repeat_label)` triple per repeat label per condition — when `collapse` is true there
is by definition at most one repeat label, so two repeat executions of one step in one condition sharing
a directory cannot occur. **Made the case happen, per the rule that a safety argument in a comment needs
a mutation**: replaced the `dict.fromkeys(...)` call with a bare list comprehension (no de-duplication
at all) and re-ran the full `h9a`- and `dry_run`-scoped selection —
`uv run pytest tests/test_cli.py -q -k "h9a"` → **46 passed** (unchanged from before the mutation);
`-k "dry_run"` → **11 passed** (unchanged). The de-duplication is provably dead for every shipped
fixture, confirming the case cannot occur rather than merely being untested. Reverted by copying the
pre-mutation file back and re-running the same selection (46 passed, 11 passed) — verified by
behaviour, not by `git status`. Corrected the comment to state the de-duplication is defensive rather
than to argue a case that cannot occur.

**Nothing regressed.** The extraction's behaviour-preservation claim, `dry-run` creating nothing,
`draft`'s relax-without-widen, and the `probes the apparatus` clause at its four homes are all
untouched by this round — no file under `src/` changed except the one comment above, confirmed
behaviour-identical by the mutation-and-revert above and by the unchanged suite count (3019/1/2).

**Grepped for every claim this round makes about other rows, files, or code, newline-insensitively,
and every hit attributed:**
- `grep -rn "Fifteen § Errors" CLAUDE.md docs/*.md docs/**/*.md` → 0 hits after the fix (was 1, in
  `CLAUDE.md`, now corrected); `grep -n "Thirteen § Errors" CLAUDE.md` → 1 hit, the corrected sentence.
- `grep -n "rest == \[\"new\"\]\|never trips" docs/superpowers/specs/2026-08-23-re-entry-seam-design.md
  docs/superpowers/plans/2026-08-23-re-entry-seam.md docs/feasibility-llm-growth-studies.md` → one hit
  in each of the three files, each the appended correction — attributed individually above.
- `git diff --stat` against the pre-round commit → exactly the seven files this report edited, no
  others; `git diff` on `docs/reference.md` → a single changed table line, no other row touched.
- The `_dry_run_step_dirs` mutation-and-revert is a behavioural check, not a `git status` check, per the
  branch's own recurring rule about verifying a revert.

**Suite delta:** none. 3019 passed / 1 skipped / 2 xfailed before and after this round, identical count
and identical composition (the round added no test and removed none — its only `tests/`-adjacent action
was the mutate-and-revert above, left reverted).
