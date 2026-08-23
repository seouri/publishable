# H6b batch 5 review — tasks 8, 9, 10, 11 (filing-and-sweep)

Reviewed at commit `df1796c`, worktree `h6b-environment-record`, alone. No subagents dispatched.
Every check below marked **(behaviour)** was run directly in this session; everything marked
**(reading)** was read and cross-checked against the code/doc rather than executed.

## Verdicts

| Task | Commit | Verdict |
|---|---|---|
| 8 — `spec-defects.md` | `2a62bbe` | **PASS** |
| 9 — `CLAUDE.md` | `49c8a33` | **PASS** |
| 10 — consistency passes | `9b7cc54` | **PASS** |
| 11 — § Executability | `4a3b9fc` | **PASS** |

Follow-up `df1796c` (the streak-ordinal correction) is folded into task 11's verdict; it is a genuine
self-correction (derived the ordinal instead of asserting it), not a new defect.

## Gates (behaviour)

```
uv run ruff check .            → All checks passed!
uv run ruff format --check .   → 93 files already formatted
uv run mypy                    → Success: no issues found in 52 source files
uv run pytest                  → 2971 passed, 1 skipped, 2 xfailed in 207.41s
```
Matches the report's claimed baseline exactly. Delta 0. Run in the foreground, no monitor/poll (the
harness auto-backgrounded the long-running `pytest` invocation; I waited for its completion
notification rather than polling).

## The report's six self-raised items, adjudicated

1. **Root-`.gitignore` entry: heading says `Owner: H6b`, body's 2026-08-23 amendment says
   "Re-owned: unassigned."** CONFIRMED by reading (`sed -n '9435,9490p' docs/superpowers/spec-defects.md`):
   the `##` heading at line 9435 still reads `**Owner: H6b**` while the amendment at line 9470 ends
   "**Re-owned: unassigned, with the reason.**" This is a real, live inconsistency. It is correctly out
   of scope for tasks 8–11: task 8 is explicitly forbidden from touching this entry, and no other task
   in the batch edits `spec-defects.md` outside the entries it owns. **Minor** — needs a follow-up task
   to update the heading string; not a blocker for this batch, and it is disclosed, not hidden.

2. **Design Decision 16: "Four … no authorized editor" vs. five/six arms.** CONFIRMED by reading
   `docs/superpowers/specs/2026-08-23-environment-record-design.md`: Decision 16's answer text (line
   573) says "Six arms … Four have no authorized editor," but its own table two paragraphs below (lines
   585–596) lists **six** arms (P, Q, R, S, T, U) with **P** the only one carrying an editor (task 3) —
   i.e., five (Q, R, S, T, U) have none. The plan (`docs/superpowers/plans/2026-08-23-environment-record.md:1042`)
   and `task-b1-review.md` both independently say "five of six arms." The design's own answer-sentence
   is wrong; the design is a spec and was correctly **not** retro-edited — the report just names the
   defect. Consistent with the report.

3. **Task 8's brief's two false claims, both corrected in the entry itself.** CONFIRMED by reading
   `src/publishable/cli.py` against `docs/reference.md` § The two files directly:
   - `git`'s six keys (`repo_root`, `commit`, `branch`, `remote`, `code_dirty`, `config_committed`) are
     written and documented in the identical order — so `environment` is not the only sub-block whose
     key order matches. Also true of `environment`'s seven keys, independently verified (order:
     `manager`, `python_version`, `os`, `hostname`, `uv_lock`, `uv_lock_hash`, `hardware` in both code
     and doc).
   - The `provenance.allocation`/`.allocation_hash` row: `spec-defects.md` line 3595 confirms it was
     "CLOSED 2026-08-13 (H3c1 task 14), struck **here** on 2026-08-23" — i.e., amended in 2026-08-13 but
     left unstruck until this batch. Confirmed.
   - The real top-level divergence — `cli.py` builds `publishable_version`/`plugin_versions` **before**
     `units`/`units_hash`/`allocation`/`allocation_hash`/`upstream`, while § The two files' example shows
     them **after** — reproduced with a direct extraction of `cli.py`'s dict-literal key order:
     `git, environment, apparatus, input_manifest, input_manifest_hash, input_manifest_changed,
     publishable_version, plugin_versions, units, units_hash, allocation, allocation_hash, upstream`.
     Matches the report's description exactly.

4. **The `bc20b13` table-wrap fix.** CONFIRMED by `git show 9b7cc54 -- docs/feasibility-llm-growth-studies.md`:
   the diff is a single one-line join of the Class-ratio row plus a deletion of the duplicated
   parenthetical link, nothing else in § What core refuses' table moved (single hunk, 1 insertion / 2
   deletions net).

5. **The streak ordinal, derived not incremented.** CONFIRMED. Reproduced the derivation independently:
   ```
   for L in 1566 1616 1657 1686 1774; do diff -q <(sed -n "${L},$((L+5))p" f) <(sed -n '1862,1867p' f); done
   ```
   gives **identical** for all five (H8a, H8b, H8c, H5a, H5b), and the block preceding H8a's entry
   (the "Correction to the correction," around line 1538) **differs**. So H8a is where the four-row
   block was established and "sixth" is correct — the report's `df1796c` follow-up correctly replaced
   an asserted ordinal with this derivation. This is exactly the carried-vs-derived shape
   § Executability's own corrections exist to prevent, caught before merge rather than after.

6. **`## Cost and execution summary` structurally nests every § Executability entry from 2026-08-20
   on.** CONFIRMED: `## Cost and execution summary` sits at line 1443, between the H7d Part B entry
   (1404) and the H8a entry (1554) — no intervening `##` heading, so H8a through H6b's own new entry are
   all nested under it. Pre-existing on `main`. Inbound links to `#executability-on-this-build`: I count
   **eight** in `docs/feasibility-llm-growth-studies.md` alone (lines 24, 67, 68, 515, 751, 823, 825,
   1471) — more than the report's "at least six," consistent with it. Repairing the heading would move
   an anchor with real inbound references; leaving it "for a ruling" rather than fixing it inside a
   filing-and-sweep batch is the right call — a heading move belongs to a task with edit authority over
   that document's structure, not to a review batch.

## The rest of the checklist

**Strikes and filings (reading + behaviour).** Every closed `spec-defects.md` entry task 8 touches is
struck with a dated closing note, never deleted — verified with `git show 2a62bbe -- docs/superpowers/spec-defects.md`
and reading the `+`/`-` hunks: removed lines are old headings/table rows: the `+` side always
re-adds the same text wrapped in `~~...~~` plus a dated closure sentence. No content silently vanished.

Ruling N's "five remaining undocumented codes" re-derived independently:
```
grep -n "E-GIT-NO-REPO\|E-GIT-NO-COMMIT" docs/reference.md   → 4 hits
```
Two are the new § Errors rows (lines 1149, 1150); the other two are mentions inside
`E-REPORT-OVERRIDE-REPO`'s and `E-STUDY-IN-REPO`'s cells (lines 582, 585) — exactly what the entry
claims. The five-code table (`E-INPUT-CHANGED`, `E-RUN-LOCKED`, `E-RUN-ID-EXHAUSTED`,
`E-PROJECT-EXISTS`, `E-EXPERIMENT-EXISTS`) is filed with `**Owner: unassigned, with the reason**`
(line 4105), and `E-STEP-EXISTS` is correctly excluded (never one of the nine — recorded as a separate
observation). Count is **five, not six** — confirmed correction-18's arithmetic holds.

The new filing (`validate_config`'s bare `except ContractError`) is real: `validate.py:511` catches a
bare `except ContractError:` with no code test, while its sibling `_check_data` at line 1221 catches
`except ContractError as exc:` and tests `exc.code == "E-GIT-NO-REPO"` before deciding to pass or
re-raise. Confirmed by reading both sites directly.

**§ Executability (behaviour).** Diffed the H6a table (1862–1867) against H6b's own appended table —
byte-identical, four rows, no fifth number:
```
diff <(sed -n '1862,1867p' docs/feasibility-llm-growth-studies.md) \
     <(sed -n '1946,1951p' docs/feasibility-llm-growth-studies.md)
→ (empty)
```
Row 1's "H6b emits nothing at `validate`" claim reproduced: `grep -c "E-GIT-NO-REPO\|E-GIT-NO-COMMIT"
src/publishable/validate.py` → 1, and that one hit (`validate.py:1223`, `if exc.code ==
"E-GIT-NO-REPO": return`) is a catch, not an emit — read directly, not merely counted.

**Both consistency passes, re-run independently (behaviour), not read off the report.** Wrote fresh
throwaway mechanical and link checkers rather than trusting the report's own scripts:
- Trailing whitespace / tabs: `grep -n ' $'` / literal-tab grep over the six files → **0 hits**.
- Table column mismatches: a corrected reimplementation (my first draft had two bugs — stale
  `header_cols` carried across adjacent tables, and no unescaped-pipe handling; both fixed and
  re-run) → **0 findings** across README, both design docs, reference, the feasibility analysis,
  and CLAUDE.md.
- Invisible unicode: **0 hits**.
- En dash in a heading, `x` for multiplication: **0 hits** in all six files.
- Anchor resolution: wrote a GitHub-slugger reimplementation, initially wrong on `&`-containing
  headings (collapsed double hyphens to one); corrected to match GitHub's actual behavior
  (`Secrets & credentials` → `secrets--credentials`), then **0 findings** across the six files.
  Proven able to fail: planted `[bad](#no-such-anchor-here)` and `[bad2](docs/definitely-missing.md)`
  on a copy of `reference.md` — both fired.
- Duplicate heading anchors: **0** across all six files.

**Cross-document pass (reading + behaviour).** `git diff main..HEAD -- README.md
docs/design-principles.md docs/experimental-designs.md docs/reference.md` touches only
`docs/reference.md` (13 insertions / 1 deletion). The worked example's only change is the `hardware`
line losing `gpu: "1x A100 80GB"`; `cohort-pilot`'s intervals, hash prefixes, unit counts, deltas, and
`repeat_spread` are all untouched (confirmed by reading the full diff, not merely the hardware line).

**Deleted-claim sweep, re-run independently (behaviour).** `gpu`: 2 hits in `docs/reference.md`
(`hms-gpu-node-04` + new prose), 5 in `CLAUDE.md`, 1 in `cli.py` (comment) — matches. `A100`: 0 in the
four documents; the only repo-wide hits outside the development record are `tests/test_report.py`'s
apparatus-fixture facts (`{"gpu": "A100"}`, correct and untouched) plus two irrelevant `.venv`
third-party matches. `ebf642a`: 2 in `study.py`, 1 in `CLAUDE.md` — matches. The `secrets.py`
enumeration phrasing is gone from every file in both spellings, checked flattened (whitespace
collapsed) as the report specifies, and I independently confirmed the flattening is load-bearing: the
phrase *"A GPU, an instrument revision, or a hosted model deployment is not"* is present in
`docs/reference.md` but wraps across a line break, so a naive `grep -F` misses it.

**Development record not retro-edited (behaviour).** `git show --stat` on all four task commits shows
each touches only one of `spec-defects.md`, `CLAUDE.md`, or `docs/feasibility-llm-growth-studies.md` —
never the plan or design files for this slice. `spec-defects.md` is the one file permitted to strike
rather than append, and every strike I inspected carries a dated closure rather than a deletion.

**`.superpowers/sdd/.gitignore`.** Currently intact (rule-comment + `task-*-brief.md` / `*.diff` /
`*.txt`), consistent with `git log -- .superpowers/sdd/.gitignore` showing a prior clobber-and-restore
cycle before this batch. `task-8-brief.md` and `task-9-brief.md` are correctly untracked (`git status
--ignored` shows `!!`); no new brief was force-added or committed by this batch.

## What I verified by behaviour vs. by reading

**By behaviour** (ran it myself, this session): all four gates; the full test suite; the
byte-identical § Executability table diff; the mechanical pass (trailing whitespace, tabs, invisible
unicode, table columns, en dash, `x`) with two self-inflicted false-positive bugs found and fixed
before trusting the result; the anchor/link pass with a slugger bug found and fixed the same way,
plus a planted-control proof it can fail; the `gpu`/`A100`/`ebf642a` sweep; the `cli.py` provenance
dict key-order extraction (both `git` and `environment` sub-blocks, and the top-level order); the
`find_repo_root` catch-site grep in `validate.py`; the `E-GIT-NO-REPO`/`E-GIT-NO-COMMIT` reach-path
grep in `reference.md`; the guard-pin arm table in the design doc; `git log --format='%ad %h %s'` for
H6a's merge date.

**By reading** (cross-checked text against text, not executed): the `spec-defects.md` strike/amend
history for the six-unwritten-keys entry and the nine-to-five entry; the CLAUDE.md diff's prose edits
(order line, H6b slice entry, Rulings O/Q/N/P, Decision 12); the report's own six self-raised items,
each independently reproduced above rather than taken on the report's word.

## Overall

No new Critical or Major findings. The one live, unresolved item — the root-`.gitignore` entry's
heading/body owner disagreement (self-raised item 1) — is correctly disclosed and correctly left
untouched by this batch (task 8 was forbidden from editing that entry; no other task in the batch
touches `spec-defects.md`). It should be picked up as a small follow-up, filed as:

- **Minor** — `docs/superpowers/spec-defects.md`, the root-`.gitignore` entry's `##` heading (around
  line 9435) still reads `**Owner: H6b**` after its own 2026-08-23 amendment re-owns it unassigned.
  Reproduce: `grep -n "uncommitted root \`.gitignore\` decides" docs/superpowers/spec-defects.md`, then
  read the heading against the amendment's last line in the same entry.

All four tasks' claims held up under independent re-derivation. The batch is accurate, the sweeps are
real (not merely asserted), and the suite/gates are unmoved at 2971/1/2.
