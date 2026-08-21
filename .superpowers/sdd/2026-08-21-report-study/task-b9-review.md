# Task 16 (batch 9) review — the documents: homes, prose, the `allocation.json` ruling, three worked `diff` headers

Reviewed at `c794029` (branch `h8c-report-study`), against `.superpowers/sdd/2026-08-21-report-study/review-b9.diff`,
`task-16-brief.md`, `task-b9-report.md`, the design's Decisions 14/18/20, the plan's § Corrections
against the code, and `CLAUDE.md` § The worked example / § Checking consistency after any `*.md` edit.

## Verdicts

**Spec compliance: PASS with reservations.** Decisions 14, 18 and 20 land correctly and completely.
§ Package layout now matches `src/publishable/` **exactly in both directions** (verified by set-diff:
nothing in `src/` is missing from the tree, and the only two tree entries absent from `src/` are
`docs.py` and `reproduce.py`, which are precisely the two rows still carrying `— not yet built`). The
shared worked example is intact — no hash prefix, run ID, delta line, row label, row order or separator
moved, proven by mutation against arm D rather than by reading. **But § Exit codes' one-row-per-code
rule ("each diagnostic carries a stable identifier"; a row's unit of work is every site that raises *or*
reports it) is violated in two places that this commit's own audit step existed to find, and one of the
two new/edited rows makes a false claim about the code.**

**Task quality: FAIL — four Majors, all in the steps whose job was checking the record's own honesty.**
Step 5 (audit every code at every emit site) produced two Majors. Step 8 (strike rather than delete)
produced one: the commit struck one `spec-defects.md` filing and left **two OPEN filings that name
"H8c task 16" as their owner and that this same commit fixed**. Step 9 (the dated § Executability entry)
produced the fourth: the entry is pinned to a commit at which its own headline claim is false. The
batch's own closing concern — "the advisor pass found four real gaps in my first pass … worth a second
reviewer's own pass" — was correct, and the fourth item it invited me to look for is Major 4 below.

Gates re-run by me, all green and matching the brief's literals:
`ruff check` clean · `ruff format --check` **93 files** · `mypy` **52 source files** ·
`pytest` **2832 passed, 1 skipped, 2 xfailed** (196s, foreground, caches cleared).
Tree left clean apart from this review file; `.superpowers/sdd/.gitignore` is **not** clobbered
(full content intact) and this file is not ignored.

---

## Findings

### Major 1 — the § Executability entry is pinned to a commit at which its own headline claim is false
**`docs/feasibility-llm-growth-studies.md:1644`** — `### Measured on 2026-08-21 against commit `52612ed` — after H8c`

`52612ed` is **H8c task 17**, the *first* commit on this branch (the guard pin, Fri Aug 21 06:57), not
the slice's landing. **Verified by reading `git show 52612ed:src/publishable/cli.py`**: at that commit
`NOT_BUILT_COMMANDS` still holds `"report"`, `"study add"` and `"study new"`, and `NOT_BUILT_GENERATORS`
still holds `"report"`. The entry's first paragraph asserts the exact opposite —
*"`cli.NOT_BUILT_COMMANDS` holds neither `report`, `study new`, nor `study add` any longer"* and
*"`BaseReport`, `generate report`, and `study new`/`study add` all ship"* — so the section that exists to
make build claims **dated and reproducible** points a reader at a tree that falsifies it.

The convention the two sibling entries set is the slice's own documents commit: H8a → `254aabe`
("H8a task 9: the documents this slice owes"), H8b → `cad8940`. The pin should be `ae71d2a` (the last
code commit) or this commit. **Verified by running** that the claims are true *here*: `main(["report",
"run.yaml"])` reaches real argument handling (`E-UPSTREAM-RECORD-MISSING`, exit 1) and
`main(["study","new",...])` reaches its usage check (exit 2), with `NOT_BUILT_COMMANDS` down to
`demo, docs, draft, dry-run, list-templates, reproduce, resume`.

CLAUDE.md § Feasibility analyses step 10 is the rule this breaks: *"must be dated and pinned to a commit
where it is made."*

### Major 2 — `E-STEP-READ-CONDITION-UNKNOWN` / `E-STEP-READ-REPEAT-REQUIRED`'s row names one of its two callers
**`docs/reference.md:1132`**

The row reads *"[`io.read_condition`](#steps-that-need-every-condition) naming a condition index this run
did not resolve, or naming a repeat-scoped step with no `repeat=`"* and names only the step surface.
**Verified by reading** `src/publishable/artifacts.py`: both codes are raised at **one shared function**,
`_resolve_condition_step_dir` (lines 415 and 421), whose docstring says in as many words that it is
module-level *"so `StepIO` and `ReportIO` call the same function"* — called from `StepIO.read_condition`
(:899) and `ReportIO.read_condition` (:1184). A report override reaching a bad condition index gets these
codes, and the row does not say so.

What makes this a Major rather than a nit is the asymmetry **inside this same commit**: the audit
correctly widened `E-ARTIFACT-NAME`'s row (`docs/reference.md:1085`) to name *"a [report override's] own
`io.read_condition`, which checks the identical target-step containment through the same `_contained`
call"* — the fourth of four sites. The two codes next door come out of the same second caller, through
the same shared helper, and were not widened. This is the `E-TEMPLATE-UNKNOWN` two-emit-sites shape and
the whole-branch Major on both preceding sub-slices, shipped a third time.

### Major 3 — the new `E-EXPERIMENT-UNKNOWN` row asserts "one raise" where the code has two
**`docs/reference.md:1124`**

The row (added by this commit, correctly closing a genuine zero-row gap) ends:
*"Both callers share the one `package_name` helper **and its one raise**, so a missing package is the
identical fault under the identical code regardless of which generator meets it first."*

**Verified by reading**: `package_name` is `src/publishable/generators/experiment.py:46-47`,
`return experiment.replace("-", "_")` — a pure string transform that raises nothing. The code has **two
independent `raise ContractError(...)` statements**, `generators/step.py:24` and
`generators/report.py:78`, each with its own `pkg_dir.is_dir()` guard and its own message string. The
consequence is concrete: an editor repairing the message, the guard, or the code at one site would
believe from this row that both were fixed. `CLAUDE.md` § Habits that cost real work names this exactly
— *"a comment or docstring claiming a guarantee the code does not provide"* — and the same section's
remedy applies: **delete the clause rather than rewrite it**; the row's first sentence already carries
everything a reader needs.

### Major 4 — two `spec-defects.md` filings owned by "H8c task 16", fixed by this commit, left OPEN
**`docs/superpowers/spec-defects.md:7960` and `:7978`**

- `:7960` — *"OPEN — § A report override's fenced block is labelled `— generated` and is no longer what
  `generate report` writes — **Owner: H8c task 16***"
- `:7978` — *"OPEN — § Creation commands' `generate` Arguments cell does not name `--format` —
  **Owner: H8c task 16***"

Both were filed by the previous batch (`ae71d2a`) naming this task as owner. **Both are fixed by this
commit**, and the task report says so in its own words (step 2: "Minor 7 (carried by name)… now matches
`generators/report.py`'s `REPORT_PY` byte for byte"; step 5: "Minor 8… Fixed: `--format` now named
beside `--plugin`"). **Verified by running**, not by reading: I re-rendered `REPORT_PY` with
`pkg="cohort_pilot"`, `fmt=json.dumps("html")` and compared it to the fenced block in
§ A report override — **byte-identical**; and `docs/reference.md:3554`'s `generate` row now reads
*"(`experiment` accepts `--plugin`; `report` accepts `--format`)"*.

They sit **immediately below** the filing this task did strike (`:7732`), so the strike step reached the
right file, opened it, and stopped one entry short. `CLAUDE.md`: *"the one exception is
`spec-defects.md`, a live list, where a closed gap is struck rather than left to mislead"*, and
*"re-owner a deferral when the slice that filed it finishes"* — with H8c complete, two entries now name
a closed task as the owner of work already done. Strike both with a `CLOSED by H8c task 16` note, the
same shape `:7732` got.

### Minor 5 — "character for character" is false of the table it describes
**`docs/feasibility-llm-growth-studies.md:1661` (the row) and `:1664-1665` (the claim)**

The H8c entry says the table is *"repeated from the H8a entry unchanged"* and, four lines later,
*"this entry's own table above is the H8a entry's, **character for character**"* — and the brief said
the same ("repeat the four-row table character for character"). **Verified by diffing the extracted
rows**: exactly one cell differs — the `report_by`-under-`resample` row reads **"H8c touches none of
this"** where H8a's and H8b's both read **"H8a touches none of this"**. H8b, which makes the identical
claim, shipped the cell verbatim with `H8a` in it, so this also breaks the precedent it cites. Either
restore `H8a` (matches H8b, makes the claim true, and the sentence's own argument — *"the table's own
words are what a later reader should quote"* — favours it) or drop the character-for-character claim.
Nothing is misread as a result, hence Minor.

### Minor 6 — the repaired `REPORT_PY` ↔ document agreement ships unpinned
**`docs/reference.md:3779-3789` and `src/publishable/generators/report.py:35-46`**

**Verified by running** (above) that the two now agree byte for byte, and **verified by grep** that
`grep -rn REPORT_PY tests/` returns nothing: no test compares them. This is `CLAUDE.md`'s *"five times in
three slices a correct fix shipped unpinned — verify by probe, then pin by mutation"*, and the drift
being repaired here **already happened once**: the block carried an extra `yield` and an undefined
`render_scatter` while labelled `— generated`. Now that § Generators' `report` row reads `built`, that
label is a **build claim**, which is the filing's own argument. The pin is cheap and the pattern already
exists in this branch — `tests/test_diff.py`'s `_diff_block_raw_lines` / arm D reads a fenced block out
of a document as raw text; the same ten lines over § A report override's block, compared against
`REPORT_PY.format(...)`, closes it. Highest-value of the Minors.

### Minor 7 — `E-GIT-NO-REPO` (attack 7): the batch's adjudication is half right, and the concern is not a filing
**`src/publishable/provenance.py:47` (the raise); `docs/reference.md:578` and `:581` (the two new mentions)**

The batch is **right** that this branch adds no new `raise`: `study.py:56` and `report.py` both *catch*
`E-GIT-NO-REPO` (the former as `E-STUDY-IN-REPO`'s pass branch, the latter converting to
`E-REPORT-OVERRIDE-REPO`), and `generate`'s uncaught `find_repo_root(Path.cwd())` at `cli.py:3948` ran
before the kind branch already. It is **wrong** that the branch does not widen the gap. Two facts I
verified:

1. **`git show main:docs/reference.md | grep -c E-GIT-NO-REPO` → 0.** The code appears in the four
   documents for the **first time on this branch**, in two normative § Errors cells, one of which
   (`:581`) explains at length that `find_repo_root` *"raises `E-GIT-NO-REPO` rather than returning
   `None`"*. Naming a code in a normative row **is** the widening: a reader who follows that name finds
   no row for it anywhere.
2. **It is user-visible under its own code.** `cli.py:1960` (`command_run`) and `cli.py:3948`
   (`_dispatch_generate`) call `find_repo_root` **uncaught**, so it reaches `main`'s
   `except PublishableError` printer.

Remedy: a **filing in `docs/superpowers/spec-defects.md` with a named owner**, not a row — the audit was
legitimately scoped to this branch's own sites, but a concern in a task report is not a filing
(`CLAUDE.md`: *"a ledger line saying 'filed' is not a filing"*). Scope to put in it: the same gap exists
for `E-PROJECT-EXISTS`, `E-STEP-EXISTS` and `E-TEMPLATE-EXISTS`, each named only in § Exit codes' prose
sentence at `docs/reference.md:3628` with no § Errors row — and `E-PROJECT-EXISTS`'s sentence
(*"`publishable new` reports `E-PROJECT-EXISTS`"*) is itself narrower than the code, which
`plugin_scaffold.py:169` also raises. Does not block.

---

## Checked and found correct (so the next reviewer does not re-open these)

- **Arm D really is the proof the batch claims.** Not taken on trust: I mutated one **delta line**
  (`README.md`, `30 → 50` → `30 → 51`) and one **hash prefix** (`docs/reference.md`, `sha256:8e21…` →
  `sha256:8e22…`) and confirmed the matching arm-D test **fails** in each case, reverting by `cp` from a
  backup and re-running. `_diff_block_raw_lines` anchors on `^code_hash\s{2,}(identical|DIFFERS)` — I
  confirmed by grep that **exactly one** line matches per document, so the "first matching fence" walk
  cannot pick the wrong block. Arm D passed unedited after task 16, and it structurally cannot see the
  inserted header lines (it starts *at* `code_hash`), which is exactly why the claim "nothing at or below
  `code_hash` moved" is sound.
- **Fixture H's header pins can fail.** Also mutated rather than read: `A  run record` → `A run record`
  in `README.md` fails both `test_h8c_fixture_h_document_headers_match_real_diffs_shape` and
  `test_h8c_no_blank_line_between_header_and_first_row`; inserting a blank line after the `B` header
  fails only the latter, which is the correct division of labour between the two. Both reverted, tree
  verified clean by behaviour and by `git status`.
- **Each header sits at its own level of abstraction** (Decision 20), and the format matches the code:
  `_header_line` (`diff.py:106-121`) is `"  ".join([letter, form, run_id, status])` with `draft`
  appended, printed at `diff.py:578-579` immediately before the rows with no blank line. `reference.md`
  carries the worked example's two real run IDs (byte-identical to CLAUDE.md § The worked example's),
  `README.md` carries `run_A`/`run_B` matching its own operands, `design-principles.md` carries
  `<run_a>`/`<run_b>` matching its own. All three `completed`, all run-vs-run.
- **Decision 14 lands complete.** All four grounds present in argument order; both the closing open
  question and the "not yet built" hedge are gone (`grep` for the clause across all six documents:
  zero hits, with a control confirming the sweep still finds `docs.py`/`reproduce.py`'s genuine markers).
- **§ Package layout.** Set-diff both directions against `src/publishable/*.py` — exact match modulo the
  two unbuilt modules. `artifacts.py`'s gloss names `ReportIO`'s four members and `ResolverIO`'s
  `read_input`; **verified against the class bodies**: `ReportIO` (`artifacts.py:1108`) exposes exactly
  `conditions`, `repeats`, `read_condition`, `read_input`. (`ResolverIO` also carries a `read_paths`
  property, but that is core-facing and the glosses are summaries, not enumerations — `StepIO`'s own
  omits `skip`, `finalize`, `units` and `read_upstream`. Not a finding.)
- **§ A report override's `io` sentence.** `StepIO` does carry all four names, so "the read half of the
  `StepIO` a `summary` step gets" is true, and the enumeration immediately before it removes any
  ambiguity. (It is a subset of StepIO's read surface rather than all of it — `read_upstream`, `exists`,
  `units` are absent — but the enumeration is what a reader uses. Not a finding.)
- **The `{"rows": […]}` paragraph is accurate.** Checked line by line against `_as_rows`
  (`report.py:568-599`), `_table_columns` (first-seen key order), `_render_html_section`'s
  `<pre>`+escape branch, and all four standard sections plus the bundle's `Hypotheses` section, each of
  which builds `body={"rows": …}`.
- **§ Exit codes' creation-command enumeration** is complete for the six codes it names, as the report
  says (`E-STUDY-EXISTS` and `E-REPORT-EXISTS` were already there). Its narrowness for
  `E-PROJECT-EXISTS` is folded into Minor 7.
- **§ The importable surface's "A row marked `not yet built` is a promise" paragraph
  (`docs/reference.md:1034`) is correctly left alone.** H8c task 1 flipped `BaseReport`, the table's last
  such row, so the category is now empty — but sentences 1 and 2 are conditionals that stay true
  vacuously and sentence 3 is a standing policy for future rows. `CLAUDE.md` records the ruling that this
  sentence *derives* its claim from the `Status` column and that replacing it "would have converted a
  self-maintaining statement into a maintenance obligation nobody owns." Ruled a non-finding
  deliberately, so it is not re-opened.
- **Both consistency passes, re-run independently, every sweep proven able to fail.**
  Mechanical over the four documents named individually plus `CLAUDE.md`, the feasibility analysis and
  `spec-defects.md`, fences skipped: **all relative links and `#anchor`s resolve** (32 apparent failures
  were my slugger's handling of `_` and ` — `; zero real); **no duplicate heading anchors**; **every
  table's rows match its header's column count and no row is empty** — sweep proven able to fail by
  deleting a cell from `reference.md`'s `publishable new` row and watching it report `[3, 4]`, then
  reverting; **no trailing whitespace, tab or invisible unicode**; **no bare `x` for multiplication**;
  **no en dash in any heading** (the six/nine en dashes are `C1–C3` ranges in prose). Cross-document:
  the shared worked example (arm D, above), the four `Status` cells (consistent with
  `NOT_BUILT_COMMANDS` = 7 keys and `NOT_BUILT_GENERATORS` = `{}`), and **no positional row locator or
  stale count phrase near either insertion** — grepped `reference.md` for "the row(s) above/below",
  "the two/three/four rows", "further up", and for `<number> (emit sites|rows|codes|callers|raise sites)`:
  the only count phrase touching an insertion is `E-ARTIFACT-NAME`'s "three"→"four", correctly updated
  (`_contained` has exactly four `E-ARTIFACT-NAME` call sites: `artifacts.py:819, 908, 964, 1193`).
  **Post-removal sweeps for the strings this commit deleted** — `render_scatter`, `Method agreement`,
  `read-only accessor`, `three emit sites` — over all six documents by name (file list filtered, never
  the output): zero survivors outside `CLAUDE.md`'s own H8c development-record entry, which describes
  the removal and is correct to name it.
- **§ Executability re-measured, two configs, with a can-fail control.** Not re-derived: I built a real
  scaffolded project outside the repo (`publishable new` + `init`), transplanted **E1**'s and **C1**'s
  `data.units` and `statistics` blocks verbatim under the analysis's own documented `index.csv`
  substitution (240- and 330-row synthetic tables carrying their declared attributes), and ran
  `publishable validate`. **Both report zero errors** — the only finding is
  `W-DATA-CLUSTER-UNDECLARED` on `age_band`, which the 2026-08-16 entry already names as a property of
  the fixture rather than of the design. The **can-fail control** (E1 with `holdout.frac: 0`) reports
  `E-DATA-HOLDOUT-FRAC`, the same discriminating mutation the original measurement used. C1's
  `weight_by: sampling_weight` beside a declared `baseline` validates clean, consistent with H4b-1.
  The "8 of 8" row therefore stands for the two I re-measured, the table carries **no fifth number**, and
  no row moved. Only the **commit pin** is wrong (Major 1).

## What I could not check

- **The table's other six configs.** I re-measured E1 and C1 only; the remaining seven rest on the
  carried H8a measurement, which this entry repeats rather than re-derives.
- **Whether "8 of 8" is the right denominator.** "Transplantable" is defined elsewhere in the analysis
  and I did not re-derive which of the nine it excludes.
- **Whether § Errors `validate` reports is the right home for the `E-REPORT-*`/`E-STUDY-*` rows.** They
  are raised by `command_report`/`study add`, not reported by `validate`. Decision 15 owns code homes and
  earlier tasks landed those rows; noted, not filed.
- **Any claim about `main`'s printer output for `E-GIT-NO-REPO`** beyond reading the two uncaught call
  sites — I did not construct a repo-less invocation of `run`/`generate` to see the diagnostic.
