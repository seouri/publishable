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
