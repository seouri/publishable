# Task 16 (batch 9) — the documents: homes, prose, the `allocation.json` ruling, and three worked `diff` headers

## Status

Complete. Reviewed by `advisor` before commit; four findings surfaced and all four fixed before
this report was written (see § Findings from the advisor pass below).

## What was done, by brief step

1. **§ Package layout markers off.** `report.py` and `study.py` lost their `— not yet built`
   markers, unchanged otherwise. `artifacts.py`'s gloss, which previously enumerated only
   `StepIO`'s members, now also names `ReportIO`'s four (`conditions`, `repeats`,
   `read_condition`, `read_input`) and `ResolverIO`'s one (`read_input`) — the module holds
   three `io`-shaped classes, not two, and a partial fix naming only the one this slice added
   would have been a new, narrower inaccuracy of the same shape the audit exists to catch.
2. **§ A report override's `io` sentence.** Replaced the false "same read-only accessor a
   `summary` step gets" with `ReportIO`'s own four members, named as the read half of the
   `StepIO` a `summary` step carries. Also fixed Minor 7 (carried by name): the worked
   `report.py — generated` block now matches `generators/report.py`'s `REPORT_PY` byte for
   byte (two blank lines after the import, a bare `TODO` comment rather than a second `yield`
   calling an undefined `render_scatter`). Added a new paragraph documenting the
   `{"rows": [...]}` table-body convention (found while re-reading the surrounding code for the
   `io` fix, and confirmed undocumented anywhere — the brief's own "documented in no document"
   item): a `body` mapping with a `rows` list renders one row per entry, columns in first-seen
   key order; a mapping without one renders as a `key`/`value` two-column table; anything else
   is `E-REPORT-BODY`, linked rather than restated.
3. **§ What `study add` redacts.** Landed Decision 14's ruling verbatim in argument order (shape
   commits it, participant-identity gap, the hash already discloses nothing, the named route via
   `allocation_hash`), and deleted both the open question and the "not yet built" hedge — the
   hedge located by grepping the clause (`study add is not yet built, so what follows is a
   reading of the shape...`), not the phrase, since `#package-layout`'s own not-yet-built
   markers had to stay findable by phrase for unrelated modules.
4. **§ Exit codes' creation-command enumeration.** Already complete — `E-STUDY-EXISTS` and
   `E-REPORT-EXISTS` were both already in the hand-enumerated sentence, landed by tasks 11/8.
   No edit needed; verified rather than assumed.
5. **Audit every `E-`/`W-` code raised or reported on this branch.** Diffed `main..HEAD` for
   every `"E-*"`/`"W-*"` literal touched, then read (not grepped) each site:
   - **`E-EXPERIMENT-UNKNOWN`** had zero rows anywhere in `reference.md`, despite two raise
     sites (`generators/step.py`, pre-existing, and `generators/report.py`, new this slice).
     Added a row in § Errors core raises, beside `E-UV-ADD`, naming both callers.
   - **`E-ARTIFACT-NAME`**'s row claimed "three emit sites for the escape alone" — true before
     this slice, false after: `ReportIO.read_condition` (task 4) is a fourth call to the shared
     `_contained` check. Updated the row to name the report override's `read_condition` and
     changed "three" to "four".
   - Every other touched code (`E-REPORT-*`, `E-STUDY-*`, `W-STUDY-*`, `E-STEP-READ-CONDITION-
     UNKNOWN`/`E-STEP-READ-REPEAT-REQUIRED`, the `E-UPSTREAM-RECORD-*` family, `E-GIT-NO-REPO`,
     `E-TEMPLATE-LOAD`) was already covered by an existing row whose wording already generalizes
     over the new call site, or — for `E-GIT-NO-REPO` — is a pre-existing gap (no dedicated row
     for `new`/`validate`/`run`'s own walk-up failure) that this slice's raise sites don't touch
     and don't widen; left unfiled as out of scope for this audit rather than fixed under a
     brief that didn't ask for it.
   - **Advisor-caught**: § Creation commands' `generate` row's Arguments cell (Minor 8, carried
     by name) was still missing `--format` after I'd checked the wrong table (§ Exit codes, § Generators)
     and declared the item done. Fixed: `--format` now named beside `--plugin`.
6. **Three worked `diff` headers.** Added at each block's own concreteness, directly above each
   block's `code_hash` line and nothing else:
   - `reference.md` § The apparatus core can only observe: `run_2026-08-06T14-02-11Z_8e21ab3`
     / `run_2026-08-07T09-14-03Z_8e21ab3`, both `completed` — matching the worked example's real
     run IDs.
   - `README.md` § The loop you'll actually live in: `run_A` / `run_B`, both `completed` —
     matching the block's own identity column, since a run directory's name *is* its `run_id`.
   - `docs/design-principles.md` § Same code, different parameters: `<run_a>` / `<run_b>`, both
     `completed` — unchanged in kind from the block's existing placeholder style.
   Also added one sentence after the apparatus block naming why `completed` beside
   `apparatus DIFFERS` is the pairing worth showing (advisor-caught — I had shown it but not
   said why).
7. **Fixture H** (`tests/test_diff.py`): added `_document_header_lines` and `_header_shape`,
   extending the existing document-parsing approach rather than writing a second parser, with a
   control test (`test_h8c_header_lines_are_parsed_from_the_documents_at_all`), a real-`diff`
   shape comparison over a genuine run pair (`test_h8c_fixture_h_document_headers_match_real_
   diffs_shape`), and a no-blank-line check (`test_h8c_no_blank_line_between_header_and_first_
   row`). One test I originally added — re-running the three shipped `_document_row_labels` pins
   verbatim inside a new test — was a second source of truth for the same pin (advisor-caught);
   deleted, since the shipped pins already re-run in the same suite and are the confirmation the
   brief asked for.
8. **Closed the spec-defects.md filing.** Struck (not deleted) the "three worked `diff` outputs"
   entry, prepended a `CLOSED by H8c task 16` paragraph naming what closed it and how it's
   pinned, and did not re-land the entry's own stale clause about the diff-vs-gate sentence
   (already landed by H8b task 12).
9. **CLAUDE.md.** Added the dated H8c development-record entry in the same shape as H8a/H8b's,
   and updated the "Order of the slices that remain" line to move H8c from "remain" into
   "complete" (the pattern H8a/H8b's own landings set).
10. **Both consistency passes.** Mechanical: no trailing whitespace/tabs/invisible unicode in
    any touched file (checked via `grep -nP '[ \t]+$'` and a Unicode-invisibles pattern over the
    diff's added lines only); no en dashes or bare `x`-for-multiplication introduced; the new
    feasibility-doc table's columns match its header; every new link (`#generators`,
    `#a-report-override-renders-one-experiments-own-figures`, `#errors-validate-reports`,
    `#errors-core-raises`) resolves against an existing heading. Cross-document: confirmed
    `study.yaml`'s fenced example in § Building one matches `study_new`/`study_add`'s actual
    writes in both directions, including the one expected non-match already named in the
    brief (no `code:` block from `study new`) — read `study.py` directly rather than trusted.
    Swept for "not yet built" and for the allocation.json open-question phrasing across
    `README.md`, `docs/design-principles.md`, `docs/reference.md`, `CLAUDE.md`,
    `docs/feasibility-llm-growth-studies.md`, and `docs/superpowers/spec-defects.md` by name;
    proved the sweep could fail by first confirming it still finds `docs.py`/`reproduce.py`'s
    genuine `— not yet built` markers before confirming it finds nothing for `report.py`/
    `study.py`.
11. Added H8c's dated entry to `docs/feasibility-llm-growth-studies.md` § Executability on this
    build, repeating the four-row table character for character from the H8a/H8b entries — no
    fifth number, no row moves, matching the brief's "H8c moves NO config count."

## Arm D (task 17's guard pin) — confirmed passing, unedited

`test_h8c_arm_d_readme_worked_diff_block_rows`,
`test_h8c_arm_d_design_principles_worked_diff_block_rows`, and the `reference.md` equivalent all
pass with no edit from this task. They locate each block by its own `code_hash` line and pin
every line from there to the fence's end as raw text; since this task's only edit to those three
fenced blocks was inserting two header lines *above* `code_hash`, a passing arm D is exactly the
proof that nothing at or below `code_hash` moved — no hash prefix, run ID, delta line, row label,
or row order.

## Gates

- `uv run ruff check .` — all checks passed
- `uv run ruff format --check .` — 93 files already formatted (unchanged)
- `uv run mypy` — success, 52 source files (unchanged)
- `uv run pytest -q` — **2832 passed, 1 skipped, 2 xfailed** (2829 baseline + 4 new Fixture H
  tests − 1 duplicate test deleted after the advisor pass = 2832)

## What I grepped, and its scope

- `git diff $(git merge-base main HEAD) HEAD -- src/publishable | grep -ohE '"(E|W)-[A-Z0-9-]+"'`
  — every `E-`/`W-` string literal touched by this branch's code, used as the audit's code list
  (not a grep for a spelling already suspected; the list came from the diff, then each site was
  read).
- `grep -n "_contained(" src/publishable/artifacts.py` — found the fourth `E-ARTIFACT-NAME` call
  site by reading call sites of the shared helper, not by grepping the code string itself.
- `grep -rn "not yet built" README.md docs/*.md CLAUDE.md docs/feasibility-llm-growth-studies.md`
  and a second pass with `grep -n '"rows"' src/publishable/report.py` / `grep -n
  "W-STUDY-COMMIT-MISMATCH\|W-STUDY-CODE-HASH-MISMATCH\|W-STUDY-APPARATUS-MISMATCH"
  docs/reference.md` (the latter prompted by the advisor) — confirmed by control (docs.py/
  reproduce.py still found) rather than assumed clean on a `0`-hit result alone.

## Concerns

- **`E-GIT-NO-REPO` has no dedicated § Errors row** for `new`/`validate`/`run`'s own walk-up
  failure — only design-principles.md prose that never names the code, plus the two H8c-added
  cross-references (`E-REPORT-OVERRIDE-REPO`, `E-STUDY-IN-REPO`) that mention it in passing. This
  predates H8c, and H8c's own raise sites don't add a new `raise` for it (only new call paths to
  the existing one), so I left it unfiled rather than fix it under a brief that scoped the audit
  to this branch's own sites. Worth a filing if no later slice claims it first.
- The advisor pass found four real gaps in my first pass (Minor 8 unaddressed, the table-body
  convention undocumented, the `artifacts.py` gloss now provably incomplete, and one weak test);
  all four are fixed and reflected above, but it's evidence my first sweep of "the rest of the
  task" wasn't as complete as the step-by-step brief made it feel — worth a second reviewer's own
  pass rather than trusting this report's "done" at face value, per the brief's own framing of
  why this task is reviewed at all.
