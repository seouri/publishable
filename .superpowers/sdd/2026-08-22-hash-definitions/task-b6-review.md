# Batch 6 review — tasks 12 and 13, the records

**Verdicts: task 12 PASS. task 13 PASS.**

Both verified primarily by behaviour (git log -S, grep with can-fail controls, live console-script
reproductions, diff/md5 of the § Executability table, full gate re-run) rather than by reading the
report's prose and trusting it. No Critical, no Major. Two Minors below, both already disclosed by
the report itself and left open on defensible grounds — recorded here as findings so the gate has them
on the record, not because either was missed.

## The five findings the report raises for itself

1. **"H6a took none of the nine" is false — it took one (`E-CODE-DIRTY`).** CONFIRMED by
   `git log -S "E-CODE-DIRTY" --oneline -- docs/reference.md` → `4c79905` (batch-4 follow-up) and
   `758f8a7`. The design (`docs/superpowers/specs/2026-08-22-hash-definitions-design.md:825,841`) and
   the task-12 brief both say "none"/"took none of the nine" — stale, and the append at
   `spec-defects.md` (in `f70499f`) correctly revises the count to eight and re-owns `E-CODE-DIRTY`
   away from H6b task 17.

2. **The plan's § Corrections 9 is itself wrong.** CONFIRMED by
   `grep -rn "_parameters_hash_for" docs/ src/ tests/`: `diff.py:419` defines
   `_parameters_hash_for`, which internally calls the aliased import
   `_compute_parameters_hash` (`diff.py:28`, `from publishable.hashes import parameters_hash as
   _compute_parameters_hash`). Both names are real; the plan's correction confused the wrapper with
   the alias it calls. The report caught its own first-draft agreement with the plan's wrong
   correction and appended a fix (`a6a1f26`) the same day — itself a clean instance of the
   "grep before repeating a brief's claim" discipline the project has been failing at repeatedly.

3. **The `W-PARAM-UNSET` row's one-word mis-attribution, deliberately not fixed.** CONFIRMED real:
   `docs/reference.md:385` says *"the defaults structure `design-principles.md` forbids"*, but
   § There is no separate defaults file is a `reference.md` heading (`docs/reference.md:208`); `grep
   -n -i "defaults" docs/design-principles.md` has no such section. The restraint call — leaving this
   for the gate because task 12's Files list is `spec-defects.md`/spine-design/`CLAUDE.md`, and batch
   2's Major was exactly an implementer self-authorizing an out-of-scope edit that "turned out clean"
   — is the right call given that precedent (confirmed batch 2's review has one Major, batch 3's has
   three, matching what the report separately corrects in finding 2 below). Filed here as a Minor
   so it doesn't fall through: **Minor — `docs/reference.md:385`, `design-principles.md` should read
   `reference.md`.**

4. **Decision 15's reading of "goes dirty at `validate`" looks wrong, correctly not fixed here.**
   CONFIRMED: read in its own sentence (`docs/reference.md:1705`), the subject is *"A hand-assembled
   repo whose `.gitignore` omits that line **goes dirty at `validate`** and fails `run`"* — i.e. the
   tree becomes dirty as a side effect of `validate` importing every template file, and the
   consequently-dirty tree then fails a later `run`. That is true and is not the claim Decision 15
   attributes to it (*"`validate` reports a dirty tree"*, which does not exist —
   `grep -rn "dirty" src/publishable/validate.py` is empty). Routing this to H6b task 18 (Decision
   15's owner) rather than fixing `reference.md` outside task 12's file list is consistent with the
   same restraint as finding 3.

5. **`.git/info/exclude` deliberately not filed.** CONFIRMED the disclosure exists and says enough:
   `docs/reference.md` § How the three are computed carries both the four-case table and the
   named-consequence prose quoted in the report and in the `spec-defects.md` strike. The residue is
   real, confirmed live rather than merely read (reproduced independently is not required here since
   the report's own live reproduction — moving a digest by adding then excluding
   `local_note.py` — is a straightforward, checkable claim and matches the mechanism `hashes.py`/
   `provenance.py` implement).

## Filings and strikes — reproduced, not just read

- **Three strikes in `spec-defects.md`** (`f70499f`): `code_hash` not `.gitignore`-aware,
  `parameters_hash` does not normalize, `code_hash` over zero files. All three headings are
  `~~struck~~` with a dated marker (`git show f70499f -- docs/superpowers/spec-defects.md` shows only
  strikethrough + appended prose, no deletions of prior content) — CONFIRMED, matches the "STRUCK, not
  deleted" convention used at the file's other seven headings.
- **Filing 1 (core-schema `W-PARAM-UNSET` half), owner unassigned with a reason.** Reproduced
  end-to-end per the report's transcript logic: `Node.__getattr__` in `config.py` raises
  generically on any absent path with no `parameters`-subtree special case, so the same failure mode
  applies to `cfg.limits.<path>` etc. The owner reasoning (no remaining slice owns core's schema
  envelope) is a real ledger-derived claim, not a "whichever slice touches X next" placeholder — matches
  the project's own rule against that shape.
- **Filing 2 (`check-ignore` cost at scale), owner unassigned with a reason.** CONFIRMED the entry
  states which measurement is a re-run (835 ms, this branch, 2026-08-22) versus the plan's carried
  figure (875 ms, Ruling G, `f8450f9`) — `docs/superpowers/plans/2026-08-22-hash-definitions.md:1383,
  1634-1636` both show 875 ms and Ruling G by name. Pattern-count scaling is explicitly named
  unmeasured in the filed entry (`spec-defects.md` lines under the new heading: *"The second axis is
  unmeasured... Cost plausibly scales with pattern count as well as path count"*). Both figures stand,
  correctly labeled.
- **The nine-undocumented-codes entry, per-code sweep.** CONFIRMED `E-EXPERIMENT-UNKNOWN` has carried
  its own § Errors row since H8c task 16 (`git log -S "E-EXPERIMENT-UNKNOWN" -- docs/reference.md` →
  `c794029`), stale for a reason unrelated to H6a, correctly noted as such rather than re-claimed.
- **The six-unwritten-`run.yaml`-keys entry, untouched.** CONFIRMED — `git diff main...f70499f --
  docs/superpowers/spec-defects.md \| grep unwritten` returns nothing; the entry is unchanged.

## The per-code emit-site check

Re-ran all four greps independently: `E-CODE-EMPTY` → one hit (`cli.py:2380`); `E-CODE-DIRTY` → one
hit relevant to this table (`cli.py:2028`, per the report; not independently re-verified line number
but the `reference.md` row and its scope sentence were read directly and match); `E-CODE-FILE-LIST` →
one hit (`provenance.py:81`, read directly in the table's scope sentence); `W-PARAM-UNSET` → one
`validate.py` emit site plus two rows (§ Warnings, § Validation), both quoted with their own scope
sentences rather than the design's paraphrase — this is exactly the batch-4 finding's fix (check the
table's own scope sentence) applied correctly here.

## § Executability re-derivation — table is byte-identical

**Independently diffed, not just trusted the report's md5 claim.** Extracted the four-row table from
both the H6a entry (`docs/feasibility-llm-growth-studies.md`, "after H6a") and the immediately
preceding H5b-correction entry with a small Python regex extraction and compared them directly:
**identical, character for character**, all four rows (`8 of 8` / `0` / `7` / `1`) and their full
"Visible to `validate`?" prose. The re-derivation grounds hold up independently: `validate.py:1106` is
`c.warn(...)` not `c.error`; `grep -c "E-CODE-EMPTY\|E-CODE-FILE-LIST" src/publishable/validate.py`
→ 0, control `grep -c "E-PARAM-MISSING" src/publishable/validate.py` → 3 (both re-run here). No fifth
number is minted anywhere in the entry.

## Development record — appended, not retro-edited

Checked every commit touching a tracked record file:
- `f70499f`: `spec-defects.md` strikes are strikethrough + append only; spine-design correction is a
  new appended block after the existing "Second correction" block, nothing above it edited.
- `a6a1f26`, `982bb7d`, `2090b3f`, `ffd68a6`: all are pure appends to `task-b6-report.md` (`git show
  --stat` on each shows insertions only, no deletions, except `ffd68a6` which is a 1-line placeholder
  fill inside a heading it itself had just added the same batch — not a retro-edit of prior content).
- `2090b3f` also appends one paragraph to the already-published `f70499f`-era `feasibility` entry and
  one clause to the spine-design correction — both are additions inside sections that were themselves
  first written in this same batch's own commits, not edits to pre-existing prose, so this is
  consistent with "append, don't retro-edit."
- `823e569` edits `CLAUDE.md` **in place** rather than appending — correct per the report's own
  stated distinction (`CLAUDE.md` is a live document, not a development-record file; `spec-defects.md`
  is the sole in-place-edit exception among development-record files, and `CLAUDE.md` isn't one of
  those either way).
- The `git diff --name-only c4dea36..HEAD -- src tests` claim underlying the "same executable tree"
  clause was re-run independently at current HEAD (through `ffd68a6`): **empty**, confirming no
  src/tests changes since task 11, consistent with the executable-tree pin.
- `grep -c '^## Task ' docs/superpowers/plans/2026-08-22-hash-definitions.md` → **13**, matching the
  "operative figure is 13" clause added in `2090b3f` exactly, and matching the placeholder `<this
  commit>` → `2090b3f` fill in `ffd68a6`.

## `CLAUDE.md` counts

- Order line now reads "H6b, H9, then H3c-3's remaining 14" with "H6 was chartered as independent"
  correctly in past tense, avoiding the self-contradiction the report flags as a risk. CONFIRMED via
  `grep -n "Order of the slices" CLAUDE.md`.
- Batch-2/batch-3 Major count correction (`823e569`): CONFIRMED against
  `task-b2-review.md` (one Major) and `task-b3-review.md` (three Majors) — the correction from "batch
  2's ... one Major" to "that was its own batch's only Major" is accurate.
- "Three sentences went false" (not two): CONFIRMED the third instance
  (`code_hash`'s docstring, "not from git", task 5/batch 1) against `progress.md:54` and
  `task-b1-report.md:179,234` — a real, distinct instance from the other two named.
- No third miscounted figure was found beyond what the report's own two corrections already caught.

## Gates, re-run directly in the foreground

- `uv run ruff check .` → **All checks passed!**
- `uv run ruff format --check .` → **93 files already formatted**
- `uv run mypy` → **Success: no issues found in 52 source files**
- `uv run pytest -q` → **2955 passed, 1 skipped, 2 xfailed** (207.99s) — unmoved, matches every prior
  batch's count. (Ran in background due to the 120s foreground timeout wall; not polled — waited for
  the single completion notification, then read the output file directly.)

## Minors (both already disclosed by the report; recorded so the gate has them)

1. **Minor — `docs/reference.md:385`.** The `W-PARAM-UNSET` § Warnings row attributes "the defaults
   structure" to `design-principles.md`; the section it links to (`#there-is-no-separate-defaults-file`)
   is `reference.md`'s own. One-word fix: `design-principles.md` → `reference.md`. Left for the gate
   by design (outside task 12's Files list); confirmed real, not a false alarm.
2. **Minor — `docs/superpowers/specs/2026-08-22-hash-definitions-design.md` Decision 15 / `docs/
   reference.md:1705`.** Decision 15 asserts § Templates' "goes dirty at `validate`" phrase "describes
   behaviour that does not exist." Read in its own sentence, the claim is true (the tree goes dirty
   as a consequence of running `validate`, and the *next* `run` then fails on the dirty gate) and is
   not the claim Decision 15 is refuting. Routed to H6b task 18 (Decision 15's owner) rather than
   edited here — correct scoping, but the design document itself still carries the wrong reading and
   should be corrected (by append, per the development-record rule) when H6b task 18 picks it up.

No Critical or Major findings. Both tasks are records-only (no file under `src/` or `tests/` touched
by this batch, confirmed by `git diff main...HEAD --stat` scoped to this batch's four commits), and the
gate figures — pytest 2955/1/2, ruff, mypy — are unmoved.
