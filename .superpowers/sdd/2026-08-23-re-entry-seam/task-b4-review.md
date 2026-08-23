# H9a batches 3, 4 and 5 review — tasks 3–9

**Verdicts: all seven PASS.** Four Majors, five Minors. **Two Majors block task 12's dispatch
and one blocks it via a plan amendment**; none of the four is a behaviour regression on a
previously shipped path.

**Suite, read from a FULL unfiltered `uv run pytest`: 3010 passed, 1 skipped, 2 xfailed** (215s),
re-run after every mutation was reverted and identical. Gates clean: `ruff check .` (all passed),
`ruff format --check .` (93 files already formatted), `mypy` (52 source files, no issues).
**Reconciled against batch 2's 2984: +26 = batch 3's +8 (4 + 4) and batch 4's +18 (3 / 1 / 7 / 2 / 5).**
Every per-task count in both reports matches the 37 `test_h9a_*` functions now in `tests/test_cli.py`.

**Scope of the diff, read from `git diff a9743f7..HEAD --stat`:** `docs/reference.md` (14 ±),
`src/publishable/cli.py` (290 +), `tests/test_cli.py` (998 ±), and the two reports. `provenance.py`,
`runner.py`, `apparatus.py`, `report.py`, `diff.py`, `study.py`, `run_record.py` and `hashes.py`
are **byte-unchanged** over the whole three-batch range — `git diff a9743f7..HEAD -- <those eight>`
is empty.

---

## What was verified by BEHAVIOUR versus by READING

**By behaviour (mutation or probe, each named below):** Ruling T's pathspec, both halves; `draft`
being read rather than accepted; `dry-run` creating nothing (independently, whole-tree); the
`E-CODE-EMPTY` inheritance pin; both directions of the arity guard; all three `draft` readers;
Fixture U's collapse branch; Fixture R's forced-flag branch; both agreement-pin mutations; the
latest-pointer line; the notice; console-script dispatch for `draft` and `dry-run`; arm F's ability
to fail; the `(baseline + baseline + grid)` defect.

**By reading only:** `provenance.py` byte-unchanged (git range diff — this is the report's own
mechanical guard, and my root-versus-`src/` probe is the behavioural half the report did not have);
the holdout leg of `_handed_counts` (`cli.py:2424` and `runner.py:715–723`); the fact that no
guard-pin arm other than F moved (`git diff a9743f7..HEAD -- tests/test_cli.py | grep '^-'` returns
**exactly one line**); the four anchors the doc edits introduce; the mechanical pass on the six
touched `reference.md` lines.

---

## The load-bearing checks, one by one

### 1. Ruling T — the pathspec did NOT widen. Verified by behaviour.

A probe built a real project outside this repo (pytest `tmp_path`), committed it, then dirtied a
file at the project **root** and a file under **`src/**`**, checking `git status --porcelain --
src templates` at each step:

| Tree state | `run` | `draft` | recorded `code_dirty` |
|---|---|---|---|
| dirt at the repo root only | exit **0**, no `E-CODE-DIRTY` | exit **0**, **no** notice | `false` for both |
| dirt under `src/**` | exit **1**, `E-CODE-DIRTY`, no run directory | exit **0**, notice on stderr | `false`/`true` respectively, `draft: true` |

Exactly as ruled: `draft` changes one boolean at one call site and the gate's scope is unmoved. The
three positive controls (`test_h9a_fixture_q_a_draft_on_a_dirty_tree`,
`test_h9a_a_dirty_tree_still_refuses_plain_run`,
`test_h9a_fixture_q_draft_pathspec_does_not_widen_to_the_repo_root`) all pass in the full run above.

### 2. `draft` is READ, not accepted. Mutation M1, full suite.

Deleted `draft=draft` at `cli.py:4084` → **6 failed, 3004 passed**:
`test_h9a_fixture_q_a_draft_on_a_dirty_tree`, `..._on_a_clean_tree_records_code_dirty_false`,
`test_h9a_t5_report_refuses_a_real_draft`, `test_h9a_t5_a_bundle_flags_a_real_draft_member_and_still_renders`,
`test_h9a_t5_diff_labels_a_real_draft_on_one_side_only`,
`test_h9a_fixture_r_a_draft_of_a_clean_tree_records_code_dirty_false`. Batch 3 claimed **2** at its
own commit, which is right for that commit; task 5 and task 6 then added four more readers of the
same forwarding. Not an unread parameter.

### 3. `dry-run` creates NOTHING. Verified twice, and pinned.

**My own filesystem comparison, path by path, before and after** — a probe snapshotting the **whole**
`tmp_path` tree (project *and* `output_dir`, `__pycache__` excluded) as `{relative path → sha256, or
None for a directory}` around `main(["dry-run", cfg])`:

```
PATHS-BEFORE 119
ADDED []
REMOVED []
CHANGED []
LASTLINE creates nothing
```

Nothing added, nothing removed, nothing changed, over 119 paths, through the **dispatched** command,
paired with a positive (the transcript printed and ends `creates nothing`).

**And it is pinned.** Mutation M2 added `(prepared.output_dir / "_mutation_probe").mkdir(...)` before
the print → `test_h9a_dry_run_creates_nothing_under_output_dir_on_a_never_run_project` and
`test_h9a_dry_run_leaves_an_existing_output_dir_byte_identical` both fail. Both arms are genuine
before/after comparisons (arm 1 a path list, arm 2 a `{path → bytes}` snapshot) and both are
non-vacuous — arm 1 asserts `before == []` plus `not results.glob("run_*")`, arm 2 asserts `before`
truthy first.

### 4. `E-CODE-EMPTY` inheritance — pinned. Mutation M6, full suite.

`if not hashed:` → `if False:` → **4 failed, 3006 passed**, and
`test_h9a_dry_run_inherits_e_code_empty_from_phases_1_to_5` is among them (beside arm E and the two
H6a fixtures). The test asserts `EXIT_WRONG`, `E-CODE-EMPTY` on **stdout**, and
`not list(results.glob("*"))` — refused, not refused-after-creating.

### 5. Ruling R's narrowed promise says what it omits. Adjudicated: correct.

§ Operation commands' row now carries *"**Does not** list the artifact files inside those
directories: their names are `io.write` arguments in step code, which core never inspects — see
[design-principles.md § Greenfield only]"*, and both links resolve (`#greenfield-only` exists in
`design-principles.md`; `#the-apparatus-core-can-only-observe` exists in `reference.md` — checked by
generating both files' anchor sets). The output says the same thing in three lines, asserted end to
end and in Fixture U.

**On the `probes the apparatus` clause describing behaviour this branch does not yet have** — see
Minor 5. The clause is **plan-mandated content** (task 9's section: *"wording yours, that content
mandatory"*), task 10 owns the probe and lands on this branch, and `Status` is per **command**, so
it cannot express a per-clause build state. The implementer was right to name it rather than edit
mandated content. It is a branch-internal transient, not a merge-state defect — but it is a false
present-tense claim about a `built` command until task 10 lands, so the whole-branch gate must
re-check it.

### 6. The three unowned `reference.md` edits. Adjudicated: content correct, process a Major.

See **Major 2** and **Major 3**. All three edits are correct in content, resolve their anchors, and
pass the mechanical pass. The problem is ownership and its measured downstream cost.

### 7. The arity arm, both ways. Two full-suite mutations, different tests.

| Mutation | Result | Failing tests |
|---|---|---|
| drop the **flag** check (`if len(rest) != 1:`) | (inside M2) | `test_h9a_draft_with_a_flag_is_an_invocation_error`, `test_h9a_dry_run_with_a_flag_is_an_invocation_error` — **and nothing else** |
| drop the **count** check (`if rest and rest[0].startswith("-"):`) | **6 failed, 3004 passed** (M3) | the four new no-path/two-path tests **plus `test_a_missing_argument_is_an_invocation_error` and `test_operation_commands_take_no_flags`** |

Both halves fail, and they fail *different* tests. This split is also what establishes **Major 4**.

### 8. The `Status` column. Verified through the installed console script.

From `/tmp/h9a-rev-probe` (outside this repo), `/Users/joon/src/tries/publishable/.venv/bin/publishable`:

```
draft            → `draft` takes exactly one path and no flags        exit 2
draft x.yaml     → error E-IO-FAILED …                                (real code, not a diagnostic)
dry-run          → `dry-run` takes exactly one path and no flags      exit 2
dry-run x.yaml   → error E-IO-FAILED …
resume           → `publishable resume` is specified but not built …
reproduce        → `publishable reproduce` is specified but not built …
```

Both flipped cells dispatch; the unflipped ones still print the not-built diagnostic. **No other
`Status` cell moved**: `git diff a9743f7..HEAD -- docs/reference.md` touches lines 368, 3673, 3675
(the two `Status` cells), 3741/3743, 3756 and 3882 only.

### 9. Every claimed mutation, re-run. All counts reconcile.

| Claim | Mine | Verdict |
|---|---|---|
| t3 (a) `draft=False` → 2 (at `137d55e`) | 6 at HEAD (M1) | correct for its commit; HEAD figure stronger |
| t3 (c) delete the notice → 1 | 1 failed, 36 passed (`-k h9a`, **file-and-k-scoped, stated**) | ✓ `test_h9a_fixture_q_a_draft_on_a_dirty_tree` |
| t4 bare `len(rest) != 1` → 1 (at `d4af219`) | 2 at HEAD (M2), the second being task 9's own | ✓, and task 9 reports the 2 |
| t5 ×3 reader guards → 2 each | 6 total in M2, exactly the three named pairs | ✓ — the report's correction of its brief's "exactly one" is right |
| t6 force `code_dirty=True` → 3 | 3 in M4, the exact three named | ✓ — including the third the brief did not predict |
| t7 `collapse=True` → 3 Fixture U arms | 3 in M4 | ✓ |
| t8 (a) drop `_arm_keys` → 1 (T, 160 vs 80) | 1 in M5, `assert 160 == 80` | ✓ |
| t8 (b) `None` → `scoped` → 1 (S) | 1 in M5 | ✓ |
| follow-up: delete the latest line → 1 | 1 in M4, the end-to-end test | ✓ |
| t7 mkdir under `output_dir` → 2 | 2 in M2 | ✓ |

M2 (five mutations, disjoint) gave **exactly 10 failures = 2+2+2+2+2**, and M4 (three mutations)
**exactly 7 = 3+3+1** — the sums are themselves evidence the failure sets are disjoint and correctly
attributed. **No miscount found. This is the first batch in this family whose mutation counts I could
not fault.** Both self-corrected predictions check out: there is no `<experiment>` path segment (my
probe printed `…/results/run_.../`), and Fixture U arm 3 is not blind (`INIT_REPEATS = 5` at
`materialize.py:10`, so `run_a_project`'s default has >1 repeat).

### 10. Guard-pin arms. Only F moved, to its specified state.

`git diff a9743f7..HEAD -- tests/test_cli.py | grep -E "^-" | grep -v "^---"` returns **exactly one
line**: `-    assert ("dry-run", "NOT BUILT") in tables["Command"]`. The whole arm-F change is that
line plus two additions (`("dry-run", "built")`, `("resume", "NOT BUILT")`), nothing reordered,
`("validate", "built")` and both `set(NOT_BUILT_*)` equalities untouched — byte-for-byte the
post-edit state design Decision 4 wrote in advance. **Arm F can still fail**: flipping the row's
`Status` cell back to `NOT BUILT` in `reference.md` fails `test_reference_cli_tables_are_parsed_at_all`
*and* `test_reference_cli_tables_match_what_the_cli_does[Command]` (reverted). Arm E's ability to
fail is shown by M6 (`test_h9a_arm_e_the_zero_file_e_code_empty` failed). No other arm was edited, so
no other arm's discriminating power changed; that arms A–D can fail rests on batch 1's and batch 2's
work, not on mine.

### 11–12. Claims about other code, and brief-versus-shipped.

Every claim I could grep, I grepped. Verified true: task 6's `code_dirty` sweep (README 0,
design-principles 0, experimental-designs 0, `reference.md` 2, `CLAUDE.md` 1, feasibility 0 — exact,
at `5bb8009`); the `:680` comment *"`run` refuses if true, `draft` permits it"* is **true of the code**
(my pathspec probe); `_arm_keys` already imported into `cli.py` at `a9743f7`; `INIT_REPEATS = 5`;
both literal arity greps at `137d55e` (0 hits and 1 hit, `_DIFF_ARITY_MESSAGE`). Found false: the
*conclusion* drawn from those greps (**Major 4**), and one over-claim in task 5's table (**Minor 2**).

No undisclosed drop against any of the seven briefs. Every brief item ships: `command_draft` verbatim
including its docstring; Fixture Q's four assertions; the three `_dispatch` edits per task; Fixture R
with its verified premise; `command_dry_run` with the full transcript and all three conditional
fixed-file branches fixtured; Fixtures S and T with observed ground truth; arm F; the two arity
trios; both `<command> new` routing pins. Task 3's mutation (b) is deferred to task 6 **by the
brief's own instruction**, and was run there. Task 7 built `_handed_counts` as well as calling it,
which its brief authorizes ("otherwise build both").

---

## Findings

### Major 1 (task 7) — `dry-run`'s sweep header prints `baseline` twice

`command_dry_run` builds its mode list as `["baseline"] if any(c.is_baseline …)` and then
`+= [k for k, v in sweep.items() if v]` — and `baseline` is itself a truthy `sweep` key, so it is
counted twice.

```
sweep: 3 conditions (baseline + baseline + grid) × 2 repeats = 6 executions
```

Measured live through `main(["dry-run", cfg])` on a project with
`sweep: {baseline: {analysis.method: pearson}, grid: {analysis.method: [spearman, kendall]}}`.
The brief's own mandated template reads `(baseline + grid)`. **No test can see it**: the only
assertion on that line is `"sweep: 2 conditions (grid) × 2 repeats = 4 executions"`, from a
grid-only config, so the `modes` accumulation is exercised in exactly the arrangement where the
duplicate cannot appear — the *fixture whose numbers agree with the bug* shape, in the primary
header line of a newly shipped command.

**This blocks task 12.** Task 12's section instructs *"Verify the 20 by running a dry-run of a
4-step, 3-condition, 5-seed project"*, and the worked example `cohort-pilot` is **exactly**
baseline + grid over `analysis.method` — so task 12 will run this shape and either transcribe the
duplicate into a normative document or be blocked by it. Fix round owed before task 12 is
dispatched, with a fixture whose config declares a `baseline`.

### Major 2 (task 9) — three unowned `reference.md` edits leave task 12's mandated sweep with zero hits

`:368` (§ Validation), `:3756` (§ What `demo` walks you through, stop 4) and `:3882` (entrypoint
resolution) were edited by a task whose section owns none of them. **The content of all three is
correct** — I checked each against the code and the mechanical pass — and the implementer's ground
(leaving them would make `reference.md` contradict its own row) is sound. The cost is measured:

```
$ grep -n "every artifact path" README.md docs/design-principles.md \
      docs/experimental-designs.md docs/reference.md CLAUDE.md \
      docs/feasibility-llm-growth-studies.md
(no output)
```

**Zero homes.** Task 12's section mandates a sweep for `every artifact path` and states
*"Measured already: `64 artifacts` and `would write` have one home each"* — `would write` now has
**four** homes, three of them task 9's new wording, and `every artifact path` has none. Task 12's
implementer will run a mandated sweep that finds nothing and cannot see why. `CLAUDE.md` is explicit
about the remedy — *"Append the correction to the plan when the ruling is made"* — and the plan was
**not** amended. **Requires a plan amendment to § Task 12 before that task is dispatched**, not a
re-litigation of the edits.

### Major 3 (task 9, unowned) — `reference.md:872` still says `dry-run` "resolves the run directory"

> `dry-run` takes none: it **resolves the run directory** to print paths and creates nothing …

`dry-run` is now `built` and does **not** resolve the run directory: `_DRY_RUN_PLACEHOLDER = "run_..."`,
and my probe printed `…/results/run_.../`. So a normative document carries a false present-tense
claim about a shipped command. The report files this as Concern 3 and leaves it — but the ground it
used to authorize editing `:368` (*"leaving them would make the document contradict its own
`dry-run` row"*) applies **identically** here, and `:368` is the one site where that exact clause was
**deleted**. Two treatments of one word in one file, on one ground: the asymmetry is
self-inconsistent rather than a judgement call. **Needs an owner named** (task 12 or 13) and closing
before the branch merges; the load-bearing halves of the sentence ("takes none", "creates nothing")
are true and pinned, so the fix is to drop or narrow four words.

### Major 4 (task 4; originating in plan correction 11 and design Decision 13) — "the shared arity arm is pinned by nothing" is false

The report states *"Neither grep hit pinned the shared arm before this task"* and *"Added the shared
arm's first pin"*. Both are false. Mutation M3 replaced the arm's condition with
`if rest and rest[0].startswith("-"):` — dropping only the **count** half — and the full suite
returned **6 failures**, two of which are shipped tests predating H9a (`git log -S` → `dc21d55`):

- `tests/test_cli.py:304 test_a_missing_argument_is_an_invocation_error` — `main(["run"])` → `EXIT_INVOCATION`
- `tests/test_cli.py:314 test_operation_commands_take_no_flags` — `main(["run", "cfg.yaml", "--allow-dirty"])` → `EXIT_INVOCATION`

So the **count** half of the shared arm was already pinned. What was genuinely unpinned is the
**flag** half — M2 confirms it: dropping the flag check fails *only* the two new `--json` tests. The
pin task 4 added is real and valuable; its **characterization** is wrong.

The mechanism is the one `CLAUDE.md` names verbatim under *A grep for one spelling*: both greps were
on **message text** (`"takes exactly one path"`, `"no flags"`), and `test_operation_commands_take_no_flags`
asserts only an exit code while its *name* spells the phrase with underscores — so a
space-separated grep could not see it. The false claim originates in the **plan** (correction 11) and
the **design** (Decision 13), which task 4 repeated; `CLAUDE.md`'s rule is *"before repeating any
claim a brief makes about the code, grep for it"*, and the grep that was owed was for the behaviour,
not for two spellings the brief supplied. **Route the correction to the plan and the design's
disagreement list**, or the next slice inherits it.

### Minor 1 (pre-existing) — a test whose name claims a guarantee it never exercises

`test_operation_commands_take_no_flags` invokes `main(["run", "cfg.yaml", "--allow-dirty"])` — two
arguments, so it short-circuits on `len(rest) != 1` and **never reaches the flag half its name
claims**. Proved by M2: dropping the flag check leaves it green. This is exactly why the message-text
greps concluded wrongly, and it is a fresh instance of *a test whose name claims the guarantee* — a
reader greps for that name and stops looking. Worth filing against no task in this batch; worth
renaming or strengthening when someone owns that region.

### Minor 2 (task 5) — "every hit attributed" over-claims

The report's table says its `grep -rn 'draft' tests/test_report.py tests/test_diff.py tests/test_study.py`
had "every hit attributed" and lists five rows. At `d4af219` that grep returns many more lines,
including two the table does not name: `tests/test_diff.py:531` (`assert "draft" not in line`) and
`:738` (`# … no draft here`). Both are pre-existing negative-side assertions and neither changes a
conclusion — but the table is the *reader tests*, not every hit, and saying "every hit" is the shape
this repo has been burned by.

### Minor 3 (task 8) — Decision 11 names three cases; two are fixtured and the third is not a branch

`_handed_counts` covers **fold** (Fixture S) and **otherwise** (Fixture T). The **holdout** case has
no fixture, and in the code it is not a branch at all — it falls through to `handed = scoped`. I
checked the claim it rests on rather than taking it: `eval_roster = _evaluation_roster(roster,
holdout_plan)` at `cli.py:2424`, computed inside phases 1–5 and stored on `Prepared`, and
`runner.py:715–723` says in its own comment *"`units` is already the TEST partition when a holdout is
declared"*, attaching only `train=holdout_train` — which changes no length. So the fall-through is
**correct by construction** and the report's restatement is accurate. Worth stating in the record
anyway: the number Decision 11 built a pin for has a third case the pin cannot see, and the reason it
needs no arm is a property of `_evaluation_roster`'s placement that a later phase hoist could move.

### Minor 4 (task 7) — the two *creates nothing* arms call `command_dry_run` directly

Neither goes through `main(["dry-run", …])`, so *creates nothing through the dispatched command* is
pinned only by the end-to-end transcript test, which asserts output rather than the filesystem. I
verified the dispatched path myself (check 3, 119 paths unchanged) — but that verification is a probe,
not a pin, and the probe is gone. One `main`-driven arm would close it.

### Minor 5 (task 9) — the row's `probes the apparatus` clause is false until task 10 lands

Adjudicated in check 5: acceptable, because the content is plan-mandated, `Status` is per command,
and task 10 lands on this branch. **But it must be re-checked at the whole-branch gate**, together
with the same clause surviving at `:368`, and this is a false build claim in a normative document
until then. Named here so the gate has it on a list rather than in a report's Concerns.

---

## Reverts

Every mutation was applied by script and reverted **by editing back / restoring a pre-mutation copy**
(`/tmp/cli.py.pristine`, `/tmp/report.py.pristine`, `/tmp/diff.py.pristine`,
`/tmp/reference.md.pristine`) — **never `git checkout --`**. `__pycache__` cleared before every run.
Verified by **re-running the full suite to 3010 passed** and by `git status --short` returning empty
and `git diff --stat` returning empty. The two throwaway probe files were deleted.
