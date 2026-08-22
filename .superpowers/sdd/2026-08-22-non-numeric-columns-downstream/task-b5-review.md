# H5b batch 5 review — tasks 15 and 16

**Commits reviewed:** `56aad22` (task 15), `da31016` (task 16), `c8a1380`/`dea7c70` (report),
`bc50409` (in-batch fix round). Filing-and-sweep review; no `src/` or `tests/` file moves in this batch,
confirmed by `git show --stat` on all four commits.

## Verdicts

- **Task 15 (the records): PASS.**
- **Task 16 (the § Executability entry): PASS.**

No Critical or Major findings. Two Minors (both in the report's own bookkeeping, not in the shipped
documents).

---

## What was verified by behaviour vs. by reading

**By behaviour (run, not read):**
- Full suite: `uv run pytest` foreground → **2931 passed, 1 skipped, 2 xfailed** (193.76s), matching the
  report exactly. Ran twice (once auto-backgrounded by the harness, once again to be sure); both agree.
- `uv run ruff check .` → clean. `uv run ruff format --check .` → clean (93 files). `uv run mypy` → clean
  (52 files).
- **H9 filing reproduced independently**, using `tests/test_diff.py`'s own `build` helper, a two-run
  scaffold with a `uv.lock` package pin moved between runs, and a direct `command_diff` call with
  `capsys`-equivalent capture. Output:
  ```
  uv.lock            DIFFERS
    sha256:45cd… → sha256:2d84…
  ```
  `pkg-a` does not appear anywhere in the output; exit is `EXIT_OK`; `"pkg-a" not in out` passes. The gap
  reproduces exactly as filed.
- **`uv_lock_hash` carrier, both halves grepped directly**: `cli.py:3769` writes it under
  `provenance.environment`; `diff.py:234` reads exactly that key for the `uv.lock` row. Confirmed.
- **Per-code emit-site tables re-derived by grep, all four codes**: `W-STATS-REPEATS-DISAGREE` (1 site,
  `cli.py:2934`), `W-STATS-COLUMN-THIN` (1 site, `cli.py:3333`), `W-STATS-STRATUM-SHADOWED` (1 site,
  `cli.py:3603`), `E-STEP-KEY-COLLISION` (8 sites: `artifacts.py:746/752/760/778/797/805` +
  `stats.py:3262/3270`). Read each site's code to confirm the claimed phrase/row actually covers it — all
  eight `E-STEP-KEY-COLLISION` sites are covered by the row's five collision phrases as claimed (unit ×2,
  measurement ×2, attribute ×2, derived-vs-recorded ×1, derived-vs-`by` ×1).
- **Every strike checked against the code, not just against the ledger text.** Confirmed `collapse_repeats`
  admits every unit and carries non-numeric values (direct probe); confirmed the bool-only-column arm B
  fixture value (`n_valid: {value: 6.0, ci95: [6.0, 6.0]}`) is what the test actually pins
  (`tests/test_stats.py::test_a_bool_only_column_widens_exactly_seven_moving_keys` exists and matches).
  Confirmed task 11's empty-level-gate strike is not duplicated: `grep -c "STRUCK 2026-08-22 (H5b task 11)"` → 2 lines, both task 11's.
- **Mechanical consistency pass, rebuilt from scratch rather than trusted.** My first version of the
  script had three real bugs (an inverted fence-skip on the heading/whitespace loop, an inverted fence-skip
  on the table loop that made it check nothing, and a slugger that collapsed `"Secrets & credentials"`'s
  double space into a single hyphen instead of GitHub's per-space hyphen). Each was caught by deliberately
  injecting a known fault and watching the tool report "clean" anyway — the same "prove the sweep can fail"
  discipline this task's brief demands. After fixing all three: clean on the seven files that matter
  (`README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md`,
  `docs/feasibility-llm-growth-studies.md`, `CLAUDE.md`, `docs/superpowers/spec-defects.md`), and each
  check class (duplicate anchor, trailing whitespace, tab, invisible unicode, table-column mismatch,
  broken local anchor, broken cross-file anchor) individually confirmed able to fire on an injected fault.
- **`×`-for-multiplication and en-dash-in-heading sweeps re-run directly**: `[0-9] ?x ?[0-9]` → 0 hits
  over the five documents; `×` control → 79 hits across three files (nonzero, so the sweep can hit).
  En-dash-in-heading `^#+ .*–` → 0 hits (docs + `CLAUDE.md`); bare en-dash control → nonzero in two files
  (so it too can hit).
- **Worked-example literals**: `git diff main..HEAD` touches only `docs/reference.md` (23 insertions / 4
  deletions) among the three worked-example files; grep for every worked-example interval/hash literal
  over the diff → 0 hits. No narrowing, no hash move.
- **Row 4's table, diffed programmatically rather than eyeballed**: extracted the four-row table from the
  H8a entry, the `71f3c6e` (post-H5a) entry, and the `56aad22` (post-H5b) entry and compared line by line.
  Rows 1–3 are byte-identical across all three. Row 4's **cell text** is also identical (`**1**`) in the
  H5a and H5b entries — which is exactly what the report says is not a no-op: same character, and the
  H5a entry's own closing paragraph names the dependency that makes that `1` wrong at the time it was
  published, which the H5b entry's prose corrects without editing the earlier text. **Confirmed: the
  "1 → 0 → 1" re-derivation holds** — 0 is the value that should have applied between H5a and H5b, 1 is
  correct now that H5b closes the dependency, and the published "1" in the intervening entry was wrong on
  its own terms (a fact the report discloses rather than hides).

**By reading (code or docs), not executed:**
- The `_check_column_types` per-execution write-side scope, and why a genuinely mixed `str`-beside-number
  column cannot reach `collapse_repeats` in the ordinary (non-fold-edge-case) path — I probed this by
  direct call and confirmed the write-side gate refuses a within-execution type mixture across units, which
  is what keeps task 3's residual filing (the "genuinely mixed .parquet column" entry) accurate rather than
  stale under Ruling 1's later three-mixture amendment. Read `task 3`'s spec-defects entry in full against
  Ruling 1's amendment table: they answer compatible, non-overlapping questions (str-vs-number, which
  "cannot occur," vs. number-vs-`None`, which Ruling 1 actually rules on) — **not** the "different question
  in a new costume" failure shape. No defect found here, but it is a closer read than the report gives it
  credit for; the report's own confirmation ("Task 3's entry exists and no second one was written") is
  true but doesn't establish the entry is still *accurate*, which I checked separately.
- `spec-defects.md`'s struck entries were read for the "STRUCK not deleted" shape (all three confirmed:
  headings show `~~OPEN~~ STRUCK`, `**Owner:**` lines show `~~**Owner: H5b**~~`, and the pre-existing body
  text is untouched below the strike marker, appended-to rather than rewritten).
- `CLAUDE.md`'s diff, read in full: the order-line correction ("only H5b carries behaviour-change exposure"
  → deleted, replaced with the narrower H5a/H5b split) is grounded in the spine's own first
  correction (already present before this task, lines 116–131 of the spine design), not invented for this
  task. H5a's task 9 claim ("changed a shipped surface too") checked against H5a's own plan
  (`docs/superpowers/plans/2026-08-21-artifacts-write-side.md`) and H5a's own CLAUDE.md entry
  ("the slice's one behaviour change... both row-shaped writers coerce") — consistent.

---

## Findings

### Minor 1 — the removal-sweep's own counts are stale by one commit

**File:** `.superpowers/sdd/2026-08-22-non-numeric-columns-downstream/task-b5-report.md` (task 15's
Step 6 table).

**The report's table claims** `is silently dropped` → 1 hit, `owned by H5b` → 1 hit (both "inside the
dated H5a entry"), and `W-STATS-COLUMN-THIN` → 5 hits (`reference.md`×3, `CLAUDE.md`×2). Re-running the
same newline-insensitive sweep over the same six files against the **final** state of the batch (i.e.
after task 16's commit, which the report as a whole covers) finds:
- `is silently dropped` → **2** hits (the dated H5a entry, plus task 16's own quotation of that exact
  sentence when explaining what it replaces — `docs/feasibility-llm-growth-studies.md:1727`)
- `owned by H5b` → **2** hits (same pattern, same two lines)
- `W-STATS-COLUMN-THIN` → **6** hits, not 5 (`reference.md`×3, `CLAUDE.md`×2, **and one in
  `docs/feasibility-llm-growth-studies.md:1714`**, added by task 16's own new entry)

**Why this is a Minor and not a Major:** every extra hit is legitimate — task 16 quoting the exact phrase
it corrects is required by its own brief ("says what it replaces"), and its use of the warning code in its
own prose is exactly the disclosure the brief asks for. Nothing here is a defect in the shipped documents.
The miscount is procedural: task 15's Step 6 sweep ran and was reported **before** task 16 committed
(`56aad22` before `da31016`), and the counts were never re-run against the finished batch before the
combined report (`c8a1380`) was written. This is the exact shape this repository's own culture flags
repeatedly — a number carried forward without being re-derived against the state that actually shipped —
just landing in a review artifact rather than in a spec.

**Failure scenario:** a later reader trusts "5, two files" as the full footprint of a known-present string
and misses that the string also lives in the feasibility analysis, in a context that mattered enough to be
worth checking.

### Minor 2 — none (retracted after investigation)

Investigated whether task 3's "genuinely mixed `.parquet` column" filing had gone stale relative to
Ruling 1's later three-mixture amendment (checklist item 3). Confirmed by direct probe that the two
entries describe disjoint, compatible cases (str-vs-number, unreachable, vs. number-vs-`None`, Ruling 1's
actual subject) rather than the "answers a different question" failure shape. No finding.

---

## Disagreements adjudicated (report's own § Disagreements, 5 items)

1. **Nine moving-key classes, not eight** — confirmed against Ruling 8 (second ruling set) and the
   `report_by` arm. Correct override of the stale brief.
2. **Two warnings minted, not one** — confirmed by grep: `W-STATS-COLUMN-THIN` has one emit site
   (`cli.py:3333`) and one § Warnings row (`reference.md:387`), independent of and later than
   `W-STATS-REPEATS-DISAGREE`. Correct.
3. **16 tasks shipped, not the spine's (10) or the design's 15** — confirmed:
   `grep -c '^## Task '` over the plan → 16; design body says "The scoping's 15 stand" at line 809 but the
   approved plan split one task after that sentence was written. The task correctly reported the shipped
   number and appended the correction rather than silently picking one.
4. **Arm G's docstring self-contradiction (`1927` "fourth" vs. "third")** — reproduced: docstring at
   `tests/test_cli.py:18462` says "fourth", inline comment at `:18506` says "third"; four is the correct
   count (`1998`, `1999`, `1997`, `1927`). **Correct restraint not to fix it here**: this batch is
   documents-only, and fixing a pin arm's docstring is indistinguishable from editing a guard pin outside
   its named editor. Flagging it for the whole-branch gate is the right call, not a punt — the alternative
   (silently patching a comment in a "no code change" task) is exactly the kind of quiet scope-widening this
   repo's ledger calls out elsewhere as a finding even when the result would be correct.
5. **The brief's `grep -rF` sweep shape misses line-wrapped phrases** — confirmed by re-running the
   removal sweep both ways; the newline-insensitive Python version is the one that must be trusted, and it
   was used. Correctly flagged and correctly worked around.

## Other adjudications

- **Task 16 pinning `56aad22` (task 15's commit) rather than its own `da31016`** — the entry's own prose
  states which tree it names and that no executable file moves between the two commits. This is an honest,
  narrow caveat rather than a papered-over circularity: the entry cannot pin a commit that doesn't exist
  yet at write time in the normal course of drafting, and it says so instead of pretending otherwise.
- **The consolidated re-owner note (five entries' stale *reasons*) filed before H5b's own merge to `main`**
  — the note is explicit about being "premature by one merge" inside itself. Given this repository's
  established workflow (every other "merged on \<date\>" CLAUDE.md/spec-defects entry in this codebase is
  authored on the feature branch as part of the batch that will itself be the merge), and given the
  precedent this file already uses for one-note-over-five-edits, I read this as consistent with how every
  other slice's landing note is written, not as a premature assertion of a false state — it becomes true
  the moment this branch merges, which is what the note is timed against.
- **Struck-not-deleted discipline** — verified by reading the actual diffs (`git show 56aad22`) rather
  than trusting the report's description: all three strikes use `~~...~~` markup with an appended note,
  none delete or rewrite prior body text.
- **Development record not retro-edited** — confirmed: the spine design's second correction is appended
  after the existing amendment, editing nothing above it; `spec-defects.md`'s live-list exception is used
  correctly (struck headings, appended notes).

---

## Suite and gates

`uv run pytest` → **2931 passed, 1 skipped, 2 xfailed** (193.76s), run twice, foreground both times.
`uv run ruff check .` → clean. `uv run ruff format --check .` → clean. `uv run mypy` → clean. No
`src/` or `tests/` file changed in this batch (confirmed via `git show --stat` on all four commits), so
this run is evidence about the branch as a whole, not about tasks 15/16 specifically — consistent with
what the report itself states.
