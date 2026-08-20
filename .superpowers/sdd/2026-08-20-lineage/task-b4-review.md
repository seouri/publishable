# Batch 4 review — task 12 (`_contained` wired into `read_upstream` and `read_condition`)

Reviewed 2026-08-20 on branch `h8a-lineage` at `68a1726` (code commit `406a86a`).

## Verdicts

- **Spec compliance: PASS.** The rule is containment and nothing more, wired at the base each reader
  already computed, under `E-ARTIFACT-NAME` — exactly Decision 5 as narrowed by controller ruling 1.
  Forward separators stay legal and the over-refusal failure mode is caught.
- **Task quality: PASS with four Minors.** Every mutation the brief prescribed lands, and — the part
  batch 3 got wrong — **all three refusal grounds now discriminate alone, for all three readers**,
  which I verified by three separate mutations of `_contained` the report did not run. The Minors are
  prose and record-hygiene, not behaviour.

## Verified by running

Gates, run directly and read:

- `uv run ruff check .` → `All checks passed!`
- `uv run ruff format --check .` → `84 files already formatted`
- `uv run mypy` → `Success: no issues found in 47 source files`
- `uv run pytest -q` → **`2503 passed, 1 skipped, 2 xfailed`** (134s), matching the report exactly.

All four were taken before the residual diff described under § Environment finding appeared; a reader
re-running them now may see different numbers.

**Attribution (instruction 3).** `git show --numstat 406a86a -- tests/` → `140 0 tests/test_artifacts.py`:
**zero deleted lines in `tests/`**, and `git show 406a86a -- tests/ | grep -c '^+def test_'` → **4**.
The commit touches exactly two files (`src/publishable/artifacts.py`, 6 changed lines / 2 deletions —
the two rewritten return statements — and `tests/test_artifacts.py`). With the full suite green at
`68a1726` and no pre-existing test text altered, **+4 exactly and zero pre-existing tests moved**
holds, and with it the design's measured claim that nothing in this repo reads through a `..` segment.

**Instruction 1 — the rule does not overshoot.** Widening `_contained` to `"/" in name or …` fails
**all three** positive controls (`read_upstream`, `read_condition`, and the pre-existing
`test_reuse_from_positive_control_…` at `tests/test_artifacts.py:1814`, which I confirmed predates
this batch by reading it out of `39256e3`). Unmutated, all three pass, so
`programs/gpt-4.1__seed29.json` reads through each reader.

**Instructions 1 and 2 — each ground discriminates alone.** All four arms live inside one test
function per reader, so a whole-test failure attributes nothing; I mutated the three grounds
separately and read the **failing `pytest.raises` line** each time.

| Mutation of `src/publishable/artifacts.py` `_contained` (lines 952–953) | Failing line, per reader | Arm |
|---|---|---|
| Delete `Path(name).is_absolute() or` | 1303 / 1368 / 1938 | **absolute name pointing INSIDE the step dir** |
| Replace `not str(candidate).startswith(...)` with `False` | 1287 / 1358 / 1919 | `..` traversal |
| `(base / name).resolve()` → `Path(os.path.normpath(base / name))` | 1313 / 1377 / 1948 | escaping symlink |

So instruction 2 is answered affirmatively: the inside-step absolute fixture **exists** at
`tests/test_artifacts.py:1301` (`read_upstream`), `:1366` (`read_condition`) and `:1936`
(`reuse_from`), and deleting `Path(name).is_absolute()` alone fails it and nothing else in those
tests. Batch 3's finding is not repeated. The third mutation is the one nobody ran: it is what shows
**resolution, not shape**, is what catches the symlink — normpath collapses `..` lexically and leaves
that arm green while the symlink arm goes red.

**Instruction 5 — the guard pin.** Arms B and C live in `tests/test_cli.py` (`:15350`, `:15383`).
`406a86a` touches two files, neither of them `test_cli.py`, so **neither arm was touched**.

## Findings

### Minor 1 — an ambiguous count in three shipped docstrings
`tests/test_artifacts.py:1273`, `:1340` (this task) and `:1900` (batch 3's fix round). Each says
*"Fixture N's **three** … refusal arms"*; each body has **four** `pytest.raises` blocks — `..`,
absolute-outside, absolute-inside, symlink — verified by counting blocks per function with a script,
not by reading the report. **The number is ambiguous between two readings and wrong under one of
them**: three is the count of *grounds* Decision 5 and `_contained`'s docstring enumerate (`..`, an
absolute path, an escaping symlink), four is the count of *arms*, which is the word the docstring
actually uses, because absolute gets two arms after batch 3's fix round added the inside-step one.
The report notices the tension and leaves the count standing. Instruction 6 forbids counts: **drop the
number rather than correct it**, which is also the only edit no later arm can falsify.

### Minor 2 — a positional locator in a shipped comment
`tests/test_artifacts.py:1263`: *"`reuse_from`'s own arms are in the Task 5 block above"*. CLAUDE.md
§ Habits that cost real work names locating a table row or block by position, wrong twice already.
Name what the block *does* (`reuse_from`'s Fixture N arms), not where it sits. The three
*"arms above"* uses at `:1297`, `:1322` and `:1929` each refer within one function body and I am not
counting them.

### Minor 3 — the report cites `reference.md` by line number
`task-b4-report.md` § The § Errors row this task names for task 9 cites *"line 1026"* and *"the row at
line 1040"*. Documentation conventions: cite by section, never by line number — and this row's whole
point is that task 9 must find it after other edits have moved it. The quoted row text is sufficient
and correct; the line numbers are the stale half.

### Minor 4 — the stale design claim is real, but the sweep stopped short and the ownership is split
Instruction 4's premise **confirmed**: the design attributes this wiring to task 5, and that is false
against shipped code. `e21d795` (task 5) wired `_contained` into `reuse_from` only — verified by
reading `artifacts.py` at `39256e3`, where both other readers still ended in a bare
`self._read(step_dir / name)`. Not fixed, per instruction.

Two corrections to the report's account of it:

- The report names **two** sites (design lines 659 and 702). `grep -n "task 5"` over the design
  returns **seven** lines, of which 659, 664, 685, 687, 702, 713 and 733 all carry the attribution or
  derive from it. A sweep that stops at the sites its brief happened to notice is CLAUDE.md's own
  named habit.
- The report re-owns the whole thing to *"task 9's consistency pass"*. Only the **§ Errors row** half
  is task 9's (design line 663 says so explicitly). The **`spec-defects.md`** half — line 664's *"the
  `..`/absolute escape entry closed by task 5"*, restated in the filings table at 702 — is **task 10's**
  per the design's own task table. And the design document is **development record**: CLAUDE.md says
  neither consistency pass governs it and that it is not retro-edited, so the correct treatment of
  lines 659/685/687/702/713/733 is *not to be edited at all* — the correction belongs where the record
  corrects a published claim, appended, or simply carried by tasks 9 and 10 as "do not trust this row".
  The report's § Errors section gets task 9 right; its disagreements section blurs the two.

### Not findings, checked and clean
- No new comment describes the rule as a boundary. `_contained`'s docstring (task 5's, unchanged)
  already carries *"a step can `open()` any file on the machine regardless"* and *"must never be
  written up as one"*; the new lines add no competing claim. Grepped the diff for
  `sandbox|boundary|exfiltrat` → nothing added.
- No § Errors row edited (the commit touches no `docs/`), no config-count claim, no git-ignored brief
  citation (the block comment cites `docs/superpowers/plans/2026-08-20-lineage.md`, which is tracked;
  `task-b3-review.md`, cited in batch 3's comment, is tracked too — `git ls-files` confirms).
- No `x`-for-`×`.

## Environment finding — the tree is not clean, and it is not this task's doing

**Another session is writing to this working tree concurrently.** `git status` was clean when this
review began; partway through it showed uncommitted changes in `src/publishable/cli.py`,
`src/publishable/lineage.py`, `tests/test_cli.py` (+230) and `tests/test_lineage.py` (+102), plus a
`reuse_from` ledger-record insertion in `artifacts.py` — i.e. batch 5's task 6/7 work in progress
(`UpstreamLedger.record` exists in `lineage.py` with a matching keyword signature). Collected item
count moved from **2506** to **2513** mid-review.

Consequences, stated so they are not read as task-12 defects:

- **The `2503` run collected a clean test tree, by its own output**: 2503 + 1 + 2 = **2506 collected**,
  where a later `--collect-only` on the polluted tree gave **2513**. So no test file had been modified
  when that run collected. I am *not* claiming the source tree was clean for it — the `.orig` copy I
  took after that run already contained the concurrent `ledger.record` insertion, and my own restore
  overwrote the mtime that would date it.
- **The concurrent `artifacts.py` delta cannot affect anything this review measured.** It is 8 lines,
  entirely inside `reuse_from`, *after* `_contained` has returned and after `_read` — read, not
  assumed. So no containment outcome for any of the three readers can turn on it, and the whole
  mutation matrix (all of which ran after those edits landed) is immune to the pollution.
- Every later full-suite *count* I took is not attributable, and I discarded those.
- **I could not independently re-run the 2499 baseline.** My attempt (revert both call sites, deselect
  the four new tests, full suite) returned `2506 passed, 4 deselected` — seven items more than the
  tree collected an hour earlier, so the run measured the other session's tree, not batch 3's. The
  `+4` claim is instead established by the numstat/`grep -c` evidence above, which does not depend on
  a second suite run.
- **My own mutations are fully reverted by editing back**, never by `git checkout`, and the restored
  `artifacts.py` is byte-identical to the copy taken before the first mutation (`diff` → identical)
  and self-consistent with the concurrent `lineage.py`. I have no evidence I clobbered a concurrent
  edit to that file, but I cannot prove it either: the other session wrote `lineage.py` at 13:32:01
  and my last restore of `artifacts.py` was 13:32:11.
- **I deliberately did not clean the tree.** The residual diff is another session's uncommitted work
  and reverting it would destroy it. Task 12's own contribution is committed and the tree carries
  nothing of mine.

## Could not check
- The 2499 baseline by running (above).
- Whether the concurrent session's in-flight `artifacts.py` edit was momentarily reverted by one of my
  mutation cycles. The end state is correct; the interval is unobservable after the fact.
