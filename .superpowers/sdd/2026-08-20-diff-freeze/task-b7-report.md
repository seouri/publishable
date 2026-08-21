# Task report: task 12 — codes, homes, and the § Executability re-measurement

Dated 2026-08-21. This is the last task of H8b; it touches documents only (`docs/reference.md`,
`CLAUDE.md`, `docs/superpowers/spec-defects.md`, `docs/feasibility-llm-growth-studies.md`), no
`src/` or `tests/` file.

## Status: done

Commit: (see below — committed after this report per the plan's own step 12 ordering).

## How the codes were enumerated

**By reading the code first, confirmed by grep second** (per CLAUDE.md's own rule on this). Read
`src/publishable/freeze.py`'s `_precheck` docstring (the ordered fault table, lines ~104-116) and
every `_refuse(...)` call site in the module; read `src/publishable/apparatus.py`'s
`replay_ledger` for `E-FREEZE-LEDGER-UNREADABLE`'s five raise sites; read `src/publishable/diff.py`
for `E-DIFF-CONFIG-UNREADABLE`'s two raise sites and the module docstring naming `E-IO-FAILED` as
the OSError path. That gave nine error codes (seven `E-FREEZE-*`, `E-DIFF-CONFIG-UNREADABLE`,
`E-FREEZE-LEDGER-UNREADABLE` — the brief's own count) plus `W-FREEZE-LOCK-MOVED`. Confirmed by
`grep -n "E-FREEZE\|E-DIFF\|W-FREEZE" src/publishable/*.py` afterward — no additional emit site
turned up.

For the four reused-code rows, read each row's *current* text in `docs/reference.md` first
(`E-APPARATUS-CHANGED`, `E-UPSTREAM-RECORD-MISSING`/`-UNREADABLE`/`-VERSION`,
`E-TEMPLATE-UNKNOWN`/`-INSTALLED-UNSUPPORTED`/`-LOAD`/`-COLLISION`), then read every new emit site
in `freeze.py`/`diff.py`/`lineage.py`, then decided per row whether the existing wording already
covered the new site generically (`E-TEMPLATE-LOAD` and `E-TEMPLATE-COLLISION`'s rows already say
"every other command that resolves a template" / "every command", true of `freeze` without
editing) or needed a specific rewrite (`E-TEMPLATE-UNKNOWN`'s row said "**two** surfaces meet this
condition" naming them by name — false once `freeze` raises the same code, so widened to three,
and the "hint appears only at the first" clause was corrected too: `freeze.py` passes the config's
`plugin` field to the same `unknown_template_message` helper `validate` does, so the hint is not
generate-exclusive). `E-TEMPLATE-INSTALLED-UNSUPPORTED` gains no row: it is a member of the
deliberately-unregistered `-UNSUPPORTED` family (confirmed by reading the existing prose at
`reference.md` line ~425, "no row in the registry below") and `freeze` reaching it does not change
that.

`E-APPARATUS-CHANGED`'s exit-code split (4 at `run`, 1 at `freeze`) was confirmed by reading
`freeze.py`'s `except ContractError` branch (`EXIT_WRONG` unless `E-APPARATUS-RAISED`) rather than
assumed from the design doc. `E-UPSTREAM-RECORD-*`'s widening was confirmed by reading
`diff.py::_load_side` calling `lineage.read_run_record` directly — the identical function
`io.reuse_from` uses.

## What I grepped, and its scope

- `grep -rn "E-FREEZE\|E-DIFF\|W-FREEZE" src/publishable/*.py` — every emit site, used to build the
  nine-plus-one rows (scope: `src/publishable/`, all files).
- `grep -n "E-TEMPLATE-...|E-APPARATUS-CHANGED|E-UPSTREAM-RECORD-..." docs/reference.md` before
  editing each row, to read its full current text rather than guess at it.
- Per-code sweep across the four documents plus `CLAUDE.md` and the feasibility analysis, for both
  the nine new codes and the four reused ones, run as `grep -ln "<CODE>" README.md
  docs/design-principles.md docs/experimental-designs.md docs/reference.md CLAUDE.md
  docs/feasibility-llm-growth-studies.md docs/superpowers/spec-defects.md`, filtering the **file
  list** passed to grep, never its output. **Proved the sweep can fail** by running the identical
  command first against `code_hash` (known present in all four core documents) and confirming all
  four came back — only then treated a code's absence from README/design-principles/
  experimental-designs as a true absence (those three documents don't enumerate error-code rows at
  all, which is the existing pattern, not a gap this task created). Every new/reused code's only
  hits outside `reference.md` were in `CLAUDE.md`/`spec-defects.md`/the feasibility analysis — the
  development record, dated and not retro-edited.

## What I did, by step

1. Nine new rows (seven `E-FREEZE-*`, `E-DIFF-CONFIG-UNREADABLE`, `E-FREEZE-LEDGER-UNREADABLE`) plus
   one `W-FREEZE-LOCK-MOVED` row, added to § Errors `validate` reports / § Warnings core reports —
   the "reported by a command" family per that section's own opening paragraph, not the raised
   family.
2. Widened `E-APPARATUS-CHANGED` (both exit codes, both surfaces named), `E-UPSTREAM-RECORD-*` (both
   readers named, fault text not duplicated), `E-TEMPLATE-UNKNOWN` (three surfaces, hint clause
   corrected), `E-IO-FAILED` (diff's missing-operand path named in the § Exit codes prose).
   `E-TEMPLATE-LOAD`/`E-TEMPLATE-COLLISION` needed no edit — their existing "every other/every
   command" wording is generic and already true of `freeze`; `E-TEMPLATE-INSTALLED-UNSUPPORTED`
   gains no row, per the `-UNSUPPORTED` family's existing exclusion.
3. § Package layout: `diff.py`/`freeze.py` rows inserted after `secrets.py`, before `reproduce.py` —
   comment-column aligned to the sibling rows' `#` position (checked with `awk 'index($0,"#")'`,
   fixed a one-column misalignment on first pass). No count phrase near the tree needed touching.
4. ASCII `...` → `…`: both named locations (`design-principles.md` § Same code, different
   parameters; `reference.md` § The apparatus core can only observe's fenced example) were **already**
   `…` — fixed by an earlier task in this branch (confirmed by `git log -p` showing the edit
   happened when the apparatus row was added). Found one I had to fix myself: the apparatus
   provenance YAML example's `hash: sha256:5d7c...` in the same reference.md section, missed by that
   earlier pass. Fixed and re-aligned its trailing comment column to match its siblings.
5. Deleted the stale `EXIT_EXTERNAL` clause from CLAUDE.md's § Misreadings unbuilt-reader row
   (it had already been *rewritten* rather than deleted by an earlier commit in this branch, which
   is itself a violation of "prefer deleting a claim to rewriting it" — replaced with a clean
   deletion, leaving `field_convention` as the sole remaining example, which is the row's true
   content).
6. Added the H8b entry to CLAUDE.md's development record, placed after the H8a entry (continuing
   H8's own narrative) and before H7d Part B's. Updated the "Order of the slices that remain" line
   to drop H8b (now complete alongside H8a).
7. `spec-defects.md`: filed the new gap (a plain `parameters` edit to the run-start `config.yaml`
   copy, invisible to `freeze`'s cross-check because `expand()` never reads `parameters` and no
   `parameters_hash` exists until `run.yaml`), owner H9, the check named rather than decided.
   Checked § What `status` means for the "config.yaml present, no run.yaml" state named in the
   brief's second bullet — **already covered**: that section explicitly names "the case with no
   terminal status at all" and attributes it to what `resume` is for, which is exactly that state.
   Filed nothing there, as instructed for the case where it's already covered. Did NOT strike the
   `parameters_hash` normalization entry (H6), the upstream-hash-`None` entry (H9, H8b secondary),
   or the `max_failed_fraction` truncation entry (unassigned) — verified each is present at HEAD and
   unstruck before leaving them alone. Checked the `discover_local` bytecode-caching filing named in
   the outer brief as "left with no owner by batch 4 and mis-attributing a quote to reference.md":
   **already fixed** — `git log -p` shows the owner (H9, with H8b task 12's narrower option (b)) and
   the correct attribution (to `freeze.py`, not `reference.md`) both landed in the batch-4 fix round
   commit (`d25f141`), before this task started. No further edit made; reported here rather than
   silently re-doing already-done work.
8. § Executability re-measurement: new dated entry `### Measured on 2026-08-21 against commit
   \`cad8940\`` (the last commit before this task's own docs commit; matches the commit's own
   `%cI` timestamp of 2026-08-21). Verified by running, not by reading: `main(["diff", "/nope/a",
   "/nope/b"])` → `E-IO-FAILED`, exit 1; `cli.NOT_BUILT_COMMANDS` has 10 keys, neither `diff` nor
   `freeze` among them; `GenericTemplate.apparatus_probe` resolves to `None` and `generic` is the
   only registered template. The four-row table is **copied character for character** from the H8a
   entry (diffed the two ranges directly to confirm byte-identity) — no row moved, no fifth number
   minted, no "N configs now execute" claim. Appended a correction to the 2026-08-15 entry's stale
   "`dry-run`, `draft`, `resume`, `study`, and `reproduce` … print `unknown command`" sentence
   (verified by running `resume`: it prints the specified-but-unbuilt diagnostic, not `unknown
   command`) rather than retro-editing that dated entry.
9. Both consistency passes run over the four documents by name plus `CLAUDE.md` and the feasibility
   analysis: no trailing whitespace, no tabs, no invisible unicode introduced by this task's own
   diff (checked programmatically); every link/anchor I added resolves (checked against the actual
   heading list, not a naive slugger — six of the anchors I added are pre-existing ones already used
   elsewhere in the document); every table row I touched has the same column count as its header
   (checked with `awk`, both the 2-column §-Errors rows and the 3-column Executability table); no
   `# a | b | c` enum comment was touched; no config schema field was added to prose without an
   existing example; no version number touched. The feasibility analysis edit is exempt from the
   cross-document pass and was held to the mechanical pass only.
10. `test_reference_cli_tables_are_parsed_at_all` and `test_reference_cli_tables_match_what_the_cli_does`
    both run and pass (`3 passed` including a third CLI-table test in the same `-k` filter) — the
    binding is tested, not asserted; no cell was flipped without its key.
11. Gates, run directly and read: `uv run ruff check .` → clean. `uv run ruff format --check .` →
    **88 files** already formatted. `uv run mypy` → **49** source files, clean. `uv run pytest` →
    **2631 passed, 1 skipped, 2 xfailed** in 147.91s — identical to the branch's stated baseline,
    since this task changes no `src/`/`tests/` file.

## The diff-vs-gate filing

The controller's ruling (already committed at `cad8940`, "two questions, not two answers") named
the remaining obligation as one `reference.md` sentence, owed to H8c but takeable here if it fit a
section already being edited. Task 12 was already editing § The apparatus core can only observe for
the ellipsis fix, so I wrote the sentence there (directly below the worked `diff` example) and
closed the `spec-defects.md` filing with an **AMENDED … CLOSED** note rather than leaving it
pointed at H8c.

## Concerns / things a reviewer should re-check

- The § Executability entry's "10 not-built commands" sentence lists all ten by name
  (`dry-run`, `draft`, `resume`, `study add`, `study new`, `report`, `reproduce`, `docs`,
  `list-templates`, `demo`) — this is a **count phrase** in substance even though it doesn't use a
  bare number; CLAUDE.md's rule against counts is aimed at figures that can silently go stale, and
  this list is verified by running `cli.NOT_BUILT_COMMANDS` at this commit, dated. Flagging for a
  second opinion on whether naming all ten is the right amount of specificity versus a shorter
  "the remaining unbuilt set" phrasing.
- I added one doc sentence (the diff-vs-gate tolerance note) and one `spec-defects.md` closure that
  were not explicitly assigned to task 12 by the plan file, under the outer brief's explicit
  permission ("if that sentence fits naturally in a section you are already editing, write it here
  and say so") — flagged here as instructed.

## Whole-branch fix round — 2026-08-21

Review at `.superpowers/sdd/2026-08-20-diff-freeze/whole-branch-review.md`, verdict DO NOT MERGE,
four Majors (one behavioural, three documentation/record), no Critical. All four closed, plus five
Minors, in this round. One commit.

### Major 1 — `diff` tracebacked on a config operand holding a non-JSON-serializable scalar

**Changed:** `src/publishable/diff.py`'s `_parameters_hash_for` now wraps its one call that
recomputes a config side's hash fresh (`hashes.parameters_hash(side.config)`) in `try`/`except
TypeError`, reraising as `ContractError(code="E-DIFF-CONFIG-UNREADABLE")` — the sibling refusal a
config operand `diff` cannot read already carries, reused rather than minting a tenth code. A run
side never reaches this branch (its `parameters_hash` is a string already on disk), so the guard is
scoped to exactly the operand class the review found unsafe.

**Verified by:**
- Running the review's own repro end to end through the real console script:
  `uv run publishable diff d.yaml d.yaml` (an unquoted `2026-01-01` under `parameters:`) now prints
  the header, the four `not comparable` rows, and `error E-DIFF-CONFIG-UNREADABLE ... contains a
  value \`diff\` cannot hash: Object of type date is not JSON serializable` — exit 1, no traceback.
  Confirmed a clean pair (no bad scalar) still renders `parameters_hash identical` correctly
  (regression check).
- Three new tests in `tests/test_diff.py`: a direct unit-level proof on `_parameters_hash_for`
  (mirrors the existing `test_h8b_load_side_raises_contracterror_for_unreadable_record` pattern);
  an end-to-end test through `main(["diff", ...])` asserting exit `EXIT_WRONG`, the code and "not
  comparable" in stderr/stdout respectively, and `"Traceback" not in err`; a property-preserving
  arm pairing the bad config against an ordinary one, confirming the guard fires from either
  operand position (`_parameters_hash_for` is called on both sides unconditionally).
- **Mutation**: reverted the guard (bare `return _compute_parameters_hash(side.config)`, no
  `try`/`except`) and ran the full, unfiltered `tests/test_diff.py` — all three new tests failed
  (with the exact `TypeError: Object of type date is not JSON serializable` the review reported),
  45 others stayed green. **What the property-preserving arm does:** the pre-existing
  `test_h8b_a_config_that_is_not_a_mapping_is_e_diff_config_unreadable` test (a different
  `E-DIFF-CONFIG-UNREADABLE` shape — a config that parses to a list, not a mapping) is untouched by
  either branch of this mutation, since that fault is caught earlier in `_read_config`, before
  `_parameters_hash_for` is ever reached — confirming the two `E-DIFF-CONFIG-UNREADABLE` fixtures
  exercise genuinely different code paths rather than one masking the other. Reverted by editing the
  file back (kept a pre-mutation copy at `/tmp/diff.py.postfix`); revert verified both by `diff`
  against the copy (identical) and by re-running `tests/test_diff.py` (48 passed).
- `docs/superpowers/spec-defects.md`'s pre-existing entry for the identical `TypeError` class at
  `design_digest`/`run` (owner H3) is **amended, not struck**: `diff`'s own instance is closed here;
  `run`'s crash — the entry's actual subject — is untouched and still H3's.

### Major 2 — `E-APPARATUS-RAISED`'s § Errors row said "one of two outcomes"; `freeze` is a third

**Changed:** `docs/reference.md`'s `E-APPARATUS-RAISED` row (§ Errors core raises) now says "one of
**three** outcomes" and names `freeze` as the third: raised from `freeze`'s own call to
`observe_once`, before `append_observation` ever runs for that call (verified by reading
`apparatus._observe_one`'s fixed order — probe call, then `check_facts`, then
`append_observation`), so no ledger line is written and no `run.yaml` is at stake either way, exit
`5` through the same redacting `Collector`.

**Verified by:** reading `src/publishable/freeze.py`'s `except ContractError` branch
(`if exc.code == "E-APPARATUS-RAISED": return EXIT_EXTERNAL`), and reading `observe_once`'s call
order inside `_observe_one` to confirm the probe raises before any ledger write is attempted for
that call. Not a new test — this is a documentation widening of an already-tested behaviour
(`tests/test_freeze.py`'s existing `E-APPARATUS-RAISED`/exit-5 fixtures already cover the code path
this row now describes).

### Major 3 — `apparatus.py`'s `PHASES` docstring claimed a filing that did not exist

**Changed:** filed the gap for real in `docs/superpowers/spec-defects.md` — a new entry, "no build
appends a `PHASE_DRY_RUN` ledger line, and § Operation commands and § The apparatus files
contradict each other about whether one belongs," owner H9 — rather than deleting the docstring's
claim. `src/publishable/apparatus.py`'s `PHASES` docstring now points at that entry by name instead
of asserting "is filed to H9" with nothing behind it.

**Verified by:** `grep -rn "PHASE_DRY_RUN" docs/superpowers/spec-defects.md` before the change
(zero hits) and after (the new entry's heading and body). Chose filing-for-real over the
cheaper four-word deletion the review also offered, because `replay_ledger`'s own docstring in the
same file already makes the narrower, accurate claim ("§ Refusals routes that gap to H9" — the
design document, not `spec-defects.md`) — deleting the `PHASES` docstring's claim would have left
the actual gap (nobody has decided whether `dry-run`, once built, should append this phase, or
whether `freeze`'s ledger replay should then widen to admit it) with nowhere written down at all.
`docs/superpowers/specs/2026-08-20-diff-freeze-design.md` and
`docs/superpowers/plans/2026-08-20-diff-freeze.md`'s own "filed to H9" claims are development
record and were not retro-edited — they are now true rather than merely no longer contradicted,
since the filing they pointed at exists.

### Major 4 — `W-APPARATUS-UNANSWERED`'s § Warnings row described only `run`'s surface

**Changed:** `docs/reference.md`'s row now names `freeze` as a second surface, and states precisely
what its counts are: the run's own accumulated `run_start`/`pre_execution` history (replayed from
the ledger as `freeze`'s starting `Observations`) **plus** the one round `freeze` itself just
probed — never a fresh accumulator, and never a prior `freeze`'s own round (which the ledger
replay's phase filter excludes).

**Verified by:** reading `apparatus.Observations.record` (accumulates via `.get(pair, 0) + 1`,
never resets) and `freeze.py`'s `Observer` construction (`observations=ready.baseline`, from
`apparatus.replay_ledger`, which filters to `PHASE_RUN_START`/`PHASE_PRE_EXECUTION` only — a prior
`freeze`'s own `PHASE_FREEZE` line is excluded from the baseline). Confirmed against
`tests/test_freeze.py`'s existing `test_w_apparatus_unanswered_fires_at_freeze_when_a_declared_fact_comes_back_null`,
whose own fixture (a run that always answered a real value, `null` only once `freeze` itself calls
it) is consistent with — but does not by itself distinguish — the cumulative-counts claim; the
distinguishing evidence is the code reading above, stated as such in my report rather than
overclaimed as test-proven.

### Minor 1 — a stale "seven"/"eighth" count in a shipped `freeze.py` comment

**Changed:** the comment at `freeze.py`'s probe-dispatch fallback now says "eight `E-FREEZE-*`
codes" and "a ninth code" — the true count (`RUN-ENDED`, `NO-CONFIG`, `NO-APPARATUS`,
`PLAN-MISSING`, `PLAN-MISMATCH`, `LEDGER-MISSING`, `LEDGER-UNREADABLE`, `PROBE-MISMATCH`), verified
by `grep -n 'E-FREEZE-' src/publishable/*.py`. Comment-only; no test needed or added.

### Minor 2 — the "five rows / four when null" count phrase in `CLAUDE.md`

**Changed:** deleted the count phrase from `CLAUDE.md`'s H8b entry rather than correcting it to add
the missing config-side exception (`reference.md`'s own copy self-corrects four lines later; the
`CLAUDE.md` copy did not), per the standing rule that counts in a document get deleted rather than
patched. Replaced with the four verdict words the count was standing in for
(`identical`/`DIFFERS`/`not captured`/`not comparable`), which carries the same information without
a number that can drift out of sync with a second copy elsewhere.

### Minor 4 — a deferral's owner line named a task that has finished

**Changed:** `spec-defects.md`'s `discover_local` bytecode-caching entry's title no longer names
"H8b task 12" as a live alternative for option (b) — re-owned to **H9** alone, with a note that H9
now weighs both options rather than defaulting to (a) because (b) went untaken.

### Minor 5 — `repo_root.txt`'s shape was unchecked, misrouting the remedy through `E-TEMPLATE-UNKNOWN`

**Changed:** `freeze.py` now checks `repo_root.is_dir()` after reading `environment/repo_root.txt`,
refusing `E-FREEZE-NO-CONFIG` (reusing the exact message family the sibling checks in the same
block already use) rather than falling through to `_claims`, which answered as if the project
registered no local template at all.

**Verified by:**
- Two new tests in `tests/test_freeze.py`: a nonexistent path and a plain file, both asserting
  `E-FREEZE-NO-CONFIG` and `"not a directory"` in stderr, and `"E-TEMPLATE-UNKNOWN" not in err`.
  `_assert_refused` (the existing helper) checks only the exit code and the untouched ledger — its
  `code` parameter is unused in its body — so the code/message assertions are made directly against
  `capsys`'s captured stderr, which is the only place either is actually observable.
- **Mutation**: reverted the `is_dir()` guard and ran the full, unfiltered `tests/test_freeze.py` —
  both new tests failed, reproducing the exact `E-TEMPLATE-UNKNOWN` misroute the review found
  (`error E-TEMPLATE-UNKNOWN experiment_type names \`f_assay\`, which no template ... registers`);
  the two pre-existing sibling tests (`repo_root.txt` absent, `repo_root.txt` empty) stayed green.
  **What the property-preserving arm does:** the two pre-existing tests exercise a DIFFERENT branch
  (absence and empty-string, both caught earlier in the same function, before `Path(repo_root_text)`
  is ever constructed) so they cannot be sensitive to this mutation either way — confirming the new
  tests, not the old ones, are what pin this property. Reverted by editing back (kept a
  pre-mutation copy at `/tmp/freeze.py.postfix`); revert verified by `diff` (identical) and by
  re-running the file (40 passed).
- `docs/reference.md`'s `E-FREEZE-NO-CONFIG` row widened to name the new shape.

### Also closed, not separately numbered by the review

- One documentation sentence (`reference.md`, the `freeze` prose in § Operation commands) naming
  which stream each of `freeze`'s two warnings currently prints to (`W-APPARATUS-UNANSWERED` →
  stdout, on `run`'s own precedent; `W-FREEZE-LOCK-MOVED` → stderr) — stated as the shipped fact,
  explicitly not as a decided rule, per Minor 3's own framing ("no document states either").
- `progress.md` gained entries for batches 6 and 7 (Minor 7) — reconstructed after the fact from
  `task-b6-report.md`/`task-b6-review.md`/`task-b7-report.md`, not from having watched the batches,
  and said so in the entries themselves. Also recorded there: this whole-branch review and fix
  round.

### Not closed

- **Minor 6** (the three worked `diff` outputs across README/design-principles/reference.md show
  no per-side header lines). Left open: the review itself frames this as scoped out of the design's
  own consistency sweep on purpose, and the shared worked example carries a stricter
  cross-document consistency bar than an ordinary sentence — CLAUDE.md's own § The worked example
  is explicit that a change there must be checked everywhere it appears. Editing three fenced
  blocks to add two header lines each, across three documents, without its own review pass felt
  like exactly the kind of change that has burned this branch before (a paraphrase surviving a
  one-file-short sweep). Flagging rather than acting unilaterally.

### Gates, run directly and read, before this commit

`uv run ruff check .` → clean. `uv run ruff format --check .` (after `ruff format .`, which left all
88 files unchanged) → 88 files. `uv run mypy` → 49 source files, clean. `uv run pytest` → **2636
passed, 1 skipped, 2 xfailed** (2631 baseline + 5 new tests: 3 in `tests/test_diff.py`, 2 in
`tests/test_freeze.py`). Guard-pin arms and `ROW_LABELS` untouched — confirmed by `git diff` over
`tests/test_cli.py` and `tests/test_hashes.py` showing no changes.
