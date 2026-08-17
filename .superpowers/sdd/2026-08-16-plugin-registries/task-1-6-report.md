# Tasks 1-6 report — H7b Part A documentation debt

**Status:** All six tasks complete. Gates green: `uv run pytest` → 2000 passed, 2 xfailed (task 5
added one test to the 1999+2 baseline; no test moved or was removed by any of the six); `ruff check`
clean; `ruff format --check` → 76 files, 0 to reformat; `mypy` → 43 source files, no issues.

## Commits (in order)

1. `b94029d` — docs: mint the resolver family's identifiers, and E-PROBE-UNKNOWN (task 1)
2. `fe371ad` — docs: the four load-time refusals get identifiers, and neither count phrase moves (task 2)
3. `e0cf062` — docs: mint the publishable.readers group, and file the gap it closes (task 3)
4. `bf5dc73` — docs: plugins.py gets a home in the tree, marked unbuilt until task 7 (task 4)
5. `1f7ac35` — fix: init's from comment lists every value the schema defines, and marks the unbuilt one (task 5)
6. `67d7219` — docs: --plugin is marked NOT BUILT until task 18 builds it (task 6)
7. `bbfe9d7` — docs: fix task 1's insertion point — keep the E-TEMPLATE-* family contiguous (correction to task 1, found during self-review before this report; see below)

## Test summary

`uv run pytest` → **2000 passed, 2 xfailed** (task 5's `test_the_from_enum_s_not_built_marking_is_honoured_by_core` is the +1 over the 1999+2 baseline; `test_the_generated_units_block_carries_its_comments` was extended in place, not added). `ruff check .`, `ruff format --check .` (76 files), and `mypy` (43 source files) all clean at the final commit.

## Corrections made after initial landing, before this report

**Task 1's row placement was wrong on first landing and has been fixed (commit `bbfe9d7`).** The
brief said to place the four new rows "adjacent to each other," anchored on "the row reporting a
template name claimed twice" (`E-TEMPLATE-COLLISION`). Read literally, I first placed the four rows
immediately after that row — which put them *between* `E-TEMPLATE-COLLISION` and `E-TEMPLATE-LOAD`,
splitting the `E-TEMPLATE-*` family, which every other position in this table keeps contiguous (the
table is sorted by code prefix throughout: CONFIG → CRED → DATA → ENTRYPOINT → HYPOTHESIS → META →
NAME → PARAM → REPL → STATS → SWEEP → TEMPLATE → UNITS; the one prior cross-prefix insertion,
`E-REPL-FOLD-CELLS`, sits beside the specific sibling its own text names and splits no family).
Caught on review before commit `bbfe9d7`: moved the four-row block to after `E-TEMPLATE-UNKNOWN`
(end of the template family) and before `E-UNITS-ATTR-MISSING`. This satisfies both the brief's
"adjacent to each other" instruction and the table's own convention of keeping one code-prefix
family together. Re-ran the full suite and mechanical pass after the move; nothing else in the
table's ordering was touched.

## Brief-vs-document / brief-vs-spec disagreements found

1. **The row-placement issue above** is itself the clearest instance: the brief's literal anchor
   instruction, if followed to the letter, breaks a table convention the brief's author did not
   appear to check against. Worth flagging for whoever writes task 8 (which touches this same
   table's `E-PLUGIN-COLLISION` region next) — check the family-contiguity convention before
   anchoring by "the row reporting X" rather than by position.

2. **Build-state marker asymmetry between tasks 1 and 2.** Task 1's four new rows (`E-RESOLVER-*`,
   `E-PROBE-UNKNOWN`) each carry an explicit **"Not yet emitted:"** clause. Task 2's three new
   `E-PLUGIN-*` rows in § Errors core raises, and the extended `E-TEMPLATE-COLLISION` row in the same
   table, carry no equivalent build-state marker, despite describing checks that tasks 8, 16 and 17
   build later in this same slice. I used both blocks verbatim as each brief specified — this is not
   something I introduced — but the inconsistency is real and should be visible to whoever writes
   those later tasks, since § Errors core raises has no established convention (unlike § The one
   config file and § CLI reference) for marking a described-but-unbuilt raise.

3. **A build-state disclosure gap opened between task 5 and task 11.** Task 5 deleted § The one
   config file's identifying-fields clause "the plugin case is not yet checked, since no entry point
   is resolved in this build" (per its brief, deletion preferred over rewriting, since task 11 owns
   the replacement). Between this commit and task 11 landing, that paragraph states the resolution
   rule for `experiment_type` with no disclosure that the installed-plugin case is unbuilt, while
   `E-TEMPLATE-UNKNOWN`'s own row (task 11's, untouched here) still carries that disclosure. The
   asymmetry is deliberate per the brief's own reasoning (propagating the claim to a second site is
   what a previous round got wrong) but is worth naming as a live interval rather than assuming it's
   invisible.

4. **CLAUDE.md is now stale in one place, out of scope for these six tasks.** Swept CLAUDE.md and
   `docs/feasibility-llm-growth-studies.md` (per the "grep the four documents, this file, and any
   feasibility analysis" convention) for every string these six tasks retired or changed. One live
   hit: CLAUDE.md § Feasibility analyses, procedure item 8, still reads "keep the registered
   artifacts to the four registries" — false as of task 3 (`e0cf062`), which minted a fifth
   (`publishable.readers`). Not fixed here: CLAUDE.md is outside the six tasks' file list. Every
   other retired string (`Four registries`, `four plugin registries`, `four entry-point groups`,
   `its reader inverts it` as a bare closing clause, `The two local cases`, `the plugin case is not
   yet checked`, `no entry point is resolved in this build`) had no hits in CLAUDE.md or the
   feasibility analysis.

## Task 6 re-probe (step 1), recorded per the brief

At commit `ba87aae` (branch base): `publishable generate experiment p2 --template generic --plugin
someuser/publishable-llm --input-dir <outside> --output-dir <outside>` exits 0 and writes `plugin:
null` into the generated config. `grep -rn "uv add" src/` → no hits. Control `grep -rln "uv_lock"
src/` → `cli.py`, `uv_support.py`. Matches the brief exactly; both document claims (`generate`
built *with* `--plugin`, `--plugin` runs `uv add`) were false before this task's edits.

## Commit-message notes worth carrying forward

- `bf5dc73` (task 4) inserts the `plugins.py` tree line immediately after the `manifest.py` line —
  named here since the commit message itself doesn't name the neighbour.
- **Task 18 reverts `67d7219`'s three edits** (§ Creation commands' `generate` row, § Generators'
  `experiment` row, § Plugins' opening sentence) when it builds `--plugin` for real. `67d7219`'s own
  message says "(reverts task 18)," which reads backwards — the fact for the record is: task 18
  reverts this commit, not the other way around.

## Verification performed beyond each task's own steps

- Anchor check: every `#anchor` introduced across all six tasks' diffs resolves to an existing
  heading in `docs/reference.md` (checked by extracting every `#anchor` from the diff and every
  heading slug from the document).
- No en dash introduced in any added line (`git diff ba87aae..HEAD -- docs/reference.md` diffed for
  "–" on added lines: zero hits).
- No trailing whitespace/tabs anywhere in `docs/reference.md` at the final commit.
- § Steps and artifacts does document the reader side of the writer/reader table (task 3's new
  cross-reference "`io.write` dispatches on the writer table and `io.read_upstream` indexes the
  reader table" points at real content there: "Every reader — `io.read_upstream`, `io.read_condition`,
  `io.reuse_from`, `io.read_input` — inverts the same table") — confirmed rather than assumed.
- `tests/test_cli.py` (the file that parses `reference.md`'s CLI tables) re-run in isolation after
  task 3 and task 6, both green, per each brief's own instruction.

## Concerns for the reviewer

- The row-placement correction (`bbfe9d7`) is a new commit rather than an amendment to `b94029d`,
  per this repo's "always create NEW commits rather than amending" rule — so task 1's original
  commit still shows the wrong placement in isolation; the fix is a separate, clearly-labeled commit
  layered on top. If a reviewer wants task 1 to read correctly in one commit, that would require a
  rebase this session did not perform.
- Items 2 and 3 above are pre-existing tensions in the brief/spec rather than defects I introduced;
  flagged for whoever executes tasks 8, 11, 16 and 17.
