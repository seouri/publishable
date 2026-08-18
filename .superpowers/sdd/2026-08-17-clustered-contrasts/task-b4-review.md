# Batch 4 review — tasks 14–18

Reviewed at `3ccd199` (the batch's last commit; `e77836d`, the controller's dispatch ledger, landed
during the review and changes no code). Tree left clean.

## Verdicts

**Spec compliance: PASS.** The retirement is done at both ends and completely. `_check_sweep`'s single
emit is gone; nothing in `src/` or the four documents emits, raises or reports
`E-DATA-CLUSTER-CONTRAST`; both its § Errors and § Validation rows are deleted; the sibling rows that
cited it by name now state their own property; and the two tests that pinned other properties were
narrowed rather than deleted, including `test_the_sibling_refusal_rows_state_their_own_reading` exactly
as spec § Corrections item 3 directs. It was treated as a **narrow documented refusal** rather than as
the `-UNSUPPORTED` build family: both rows removed because the combination is now honoured, and the
replacement tests assert `codes(path) == set()` rather than the absence of one code. The dated count is
right — zero unblocked, six / three unchanged.

**Task quality: CHANGES REQUIRED.** Three Majors. The measurement is misdated, and **both of task 14's
appended plan corrections went unexecuted and unreported** — one of them an obligation
`spec-defects.md` names task 14 for by name, whose corner I reproduced as still live and still
undecided.

---

## Critical

None.

## Major

**M1 — The measurement is dated a day early.** `docs/feasibility-llm-growth-studies.md:1209` heads the
new subsection *"Measured on 2026-08-17 against commit `dcb7ed0…`"*, and `task-14-18-report.md:45`
and `:191` repeat it. **Verified by running** `git show -s --format=%ci dcb7ed0` → `2026-08-18
04:00:15 -0400`; today is 2026-08-18 (`date`), and the implementer was told so. All four sibling
headings match their own commit's date (`d72724b` 08-16, `c42eb87` 08-16, `959cc8d` 08-17, `f9d9914`
08-17, `0f15c3f` 08-17). Feasibility step 10 exists because an undated build claim reads as a spec
claim later; a misdated one reads as verified. Fix the heading and both report lines to 2026-08-18.
**Nothing links to that heading** — the link/anchor scan over all five documents found no reference to
`#measured-on-2026-08-17-against-commit-dcb7ed0…`, so the date edit breaks no anchor.

**M2 — Task 14's plan correction 1 (`plans/2026-08-17-clustered-contrasts.md:2867`) was not executed
and is not mentioned anywhere in the report.** It required task 14, when building its end-to-end
fixture, to "add one that makes a template's `aggregate` return a derived metric under a declared
`cluster_by`, **and decide whether `n_paired_clusters` beside a null interval is the record
`reference.md` wants**." No such fixture exists and no decision is recorded. `spec-defects.md:6501`
states the same obligation in stronger terms: *"Task 14, which retires `E-DATA-CLUSTER-CONTRAST`, must
re-check this corner before treating it as closed."*

**Reproduced by direct call** (`_comparison_step_blocks` with `derived_by_key` holding a key that is
also in `aggregated`, plus `clusters`), which returns:

```
{'delta': None, 'basis': 'units', 'paired': True, 'method': None,
 'n_paired': 12, 'ci95': None, 'cohens_d': None, 'correction': None,
 'n_paired_clusters': 3}
```

So the corner survives task 14 unchanged: a cluster count beside a null interval, a null delta and a
null `method`. Partially mitigated — `reference.md:2657` does route the shape ("a separate, open
corner … recorded in `docs/superpowers/spec-defects.md` rather than promised here"), so this is not an
orphaned record key. What is missing is the fixture and the decision the correction asked for, and the
filing was left asserting a reachability condition task 14 lifted (see M3).

**M3 — `spec-defects.md` was left stale in the one entry task 14 changed the code under.**
- `:6522` names `tests/test_validate.py::test_a_contrast_beside_groups_and_cluster_by_draws_both_refusals`
  as one of two tripwires for an H4c obligation. Task 14 renamed it to
  `…_draws_the_allocation_refusal`; `grep -c` for the old name in `tests/` returns **0**. A tripwire
  identified by a name nobody can grep is the "ledger line saying filed is not a filing" failure in
  its other direction.
- `:6494` still reads "unreachable in a clustered run **only through `validate` and `run`
  end-to-end, and only while `E-DATA-CLUSTER-CONTRAST` refuses cluster + contrast wholesale**" — a
  condition that no longer obtains.

Task 16's Step 1 mandated reading **every** entry naming H4b-2 in full, and this entry's heading is
"RULED by H4b-2 task 5". Task 16 amended seven other rows in the same file and missed this one.

## Minor

**m1 — Task 14's plan correction 2 (`plan:3094`) required Mutation 1 at four sites; the report ran
two.** I ran the other two. `cli.py:2785` (`command_run` → `_compute_vs_baseline`) → `clusters=None`
fails on `entry["method"]` (`paired_t_over_units`); `cli.py:2802` (`command_run` →
`_compute_declared_contrasts`) fails on `declared["method"]` while the `vs_baseline` assertions pass.
All four sites are pinned independently and the required outcome holds — the gap is in the record, not
in the code. Both reverted by editing back; `cli.py` byte-identical to its pre-mutation copy.

**m2 — `docs/reference.md:506` swapped one sibling cross-reference for another.** Task 15's brief row
said to "**State the reading directly**: both guards read the resolved comparison family, not the
declaration." The row instead reads "…for the same reason a group axis's own guard does". The claim is
true, but it is a new citation of a sibling row in a commit whose whole subject is removing those —
and `validate.py`'s twin comment for the same check *does* state it directly, so the two ends of one
check now differ in form. `test_the_sibling_refusal_rows_state_their_own_reading` cannot see this.

**m3 — `tests/test_cli.py:10768`: `test_the_sibling_refusal_rows_state_their_own_reading` keeps a
plural name and the word "sibling" while checking one row.** The docstring was updated; the name was
not. CLAUDE.md's "a test whose name claims the guarantee" row applies — a reader greps the name and
stops looking.

**m4 — `src/publishable/cli.py:1167-1174` still asserts a guarantee the code does not provide.** "The
`is_derived` arm is unreachable under a declared cluster … so no metric here is derived" — false in
the key-collision case, exactly as `spec-defects.md`'s own fix-round-1 correction narrowed it and as
M2's probe shows. It escaped task 15's sweep legitimately (the comment does not name the retired
code), but it is the repo's most-repeated habit and it sits four lines above the write M2 is about.

**m5 — The new § Executability subsection is thinner than every dated sibling.** It carries no `Full
local pytest/ruff/mypy gates at this commit` line (`:1011`, `:1127`, `:1206` all do) and no per-config
table (the Part B and H4b-1 entries both do). It also makes no claim of having run `validate_config`,
while `task-14-18-report.md:188` says the measurement was made that way — the artifact's own stated
method is a grep on `cluster_by`.

**m6 — `CLAUDE.md:93`**: "clusters through contrasts is **H4b-2**, which unblocks zero configs and
still owns `E-DATA-CLUSTER-CONTRAST`" is now false. Outside task 15's declared file list, but
CLAUDE.md's own mechanical pass names "this file" as a sweep target. Owner: the merge task that writes
H4b-2's § Repository status entry — not a task 15 failure.

**m7 — Wrong scope name in a docstring and the report.** `tests/test_cli.py:10893` and
`task-14-18-report.md:179` both say `aggregated` is "built only from condition-scope step output".
`cli.py:2162-2168` filters `r.execution.scope == "repeat"`. The conclusion is unaffected; the stated
mechanism is wrong.

---

## Adjudications

### The two blindness claims — both UPHELD, one on better grounds than given

**Mutation 2 (the *t* branch's arm order): upheld, and the report understates why.** Attempted the
overturn the batch-2 precedent suggests — a direct call to `_comparison_step_blocks` with `weights=`
and `clusters=` both set. It does not reach the arms: `cli.py:905-909` raises
`ValueError("a weighted clustered comparison has no construction in this build; …")` first. So the two
arms are mutually exclusive for **every** input including a direct call, not merely for every fixture
in the file. The report's grounds ("no test in the suite constructs both non-`None` in one direct call
either") are the weaker, fixture-relative version of a guarantee the code enforces itself. Could not
overturn.

**Mutation 3 (a summary `Estimate` never enters the clustered walk): upheld by reading the
construction site.** `recording_steps` (`cli.py:2162-2168`) is built from
`r.execution.scope == "repeat"`, so nothing at `summary` scope can enter `aggregated`;
`run_record.py:104` writes `results.summary` from `scope == "summary"` on the ledger. Two disjoint
paths, no guard to mutate. Genuine.

**`_METHOD_VARYING_STEP`'s parity blindness: confirmed by running.** Under Mutation 1
(`stats.py:1401`, `items = [[key] for key in keys]` → `reversed(keys)`) the `_LINEAR_DIFF_STEP` test
FAILED at 15.825 vs 16.025 while the `_METHOD_VARYING_STEP`-based weighted test PASSED — which is both
the pin working and the implementer's diagnosis holding. Reverted by editing back; `stats.py`
byte-identical, re-verified by re-running the test green.

### The two brief-vs-code disagreements — both upheld, verified by running

I built my own clustered config and ran it. `against: "baseline"` resolves (the contrast came back with
`against: 00_baseline`); `against: "method=pearson"` would not. `cfg.parameters.analysis.method`
produced the intended non-zero shift, so the brief's `cfg.analysis.method` was wrong. The third
(`{"present": True}` records a bool, which grows no `basis: units` column) holds by reading
`stats._is_numeric:1529`, which excludes `bool` explicitly.

---

## Verified by running

- **The `run`-through half, end to end, on my own config** (not the shipped test): `run.yaml` on disk
  carries `method: paired_t_over_units_clustered`, `n_paired: 12`, `n_paired_clusters: 3`, raw ci95
  half-width 8.7632 — **and** `ci95_corrected` whose half-width 15.578 over the raw 8.763 is 1.777,
  which is the *t* ratio at **df = clusters − 1 = 2** (7.65/4.303) at the Holm level 0.0167. So the
  corrected bound is the clustered construction, not an unclustered one. Both the generated
  `vs_baseline` and the declared `results.contrasts` entry carry all three keys.
- **Task 17's regression literals are genuine pre-change baselines.** Task 7 is `377fceb`, after
  `82310b9`, and `82310b9` is an ancestor of HEAD. I created a throwaway worktree at `82310b9`, ran
  both configs there, and got `paired_percentile_over_units [16.025, 23.025]` and
  `weighted_paired_percentile_over_units [0.583333333333333, 1.4166666666666665]` with
  `n_paired_effective` 4.8 — exact matches for the shipped literals. Worktree removed; `git worktree
  list` shows one entry.
- **Feasibility re-measurement, two configs, my own transplant.** E1's and C1's `data`/`statistics`
  blocks through `validate_config` report only `W-DATA-CLUSTER-UNDECLARED` — no errors, so neither the
  retired nor the minted code fires. Can-fail control: the same C1 block with `cluster_by: age_band`
  draws exactly `{E-DATA-WEIGHT-CLUSTER-CONTRAST}`. The section's own grep is right too: `cluster_by`
  appears twice in the file, both `cluster_by: null`. Six / three agree with `CLAUDE.md:81-83`, and no
  sentence in the new section converts the six into an execution count.
- **The sweep can fail, and it was filtered by file list.**
  `grep -rn "E-DATA-CLUSTER-CONTRAST" README.md docs/design-principles.md docs/experimental-designs.md
  docs/reference.md src/ tests/` → 4 hits, all in `tests/`, all explicitly historical; control
  `E-DATA-WEIGHT-CLUSTER-CONTRAST` → 22. **Paraphrase sweeps** for "Clustered deltas", "those
  five"/"five construction", and "no contrast construction … clusters" return nothing live in `src/`
  or the four documents.
- **Cross-document pass, performed rather than assumed** — the class a *retirement* specifically
  threatens is CLAUDE.md's *Prevented mistakes* row, since a clustered contrast just became possible.
  Read every `cluster` hit in `docs/experimental-designs.md` and `docs/design-principles.md`.
  § Mistakes core prevents' four cluster rows (`:357`, `:359`, `:360`, `:361`) claim cluster-robust
  intervals, indivisible clusters in partitions, the cluster as the bootstrap draw, and the shuffle
  level — **none claims core refuses a clustered delta**, so all four stay true. § What core will not do
  for you carries no cluster-contrast claim. Better than neutral: `experimental-designs.md:330` already
  asserted "Core reports each arm **and their contrast** with intervals clustered on `match_set`", which
  was false before this batch and is what H4b-2 makes true.
  **Observation, not a finding against this batch:** that same sentence describes a design whose
  contrast crosses a `groups` axis (`status`), so it is still unmet — now under the live
  `E-DATA-ALLOCATION-CONTRAST` rather than the retired code. Pre-existing, and H4c owns it; worth
  carrying so the next slice does not read it as newly broken.
- **Mechanical pass** on `reference.md`, the feasibility analysis and `spec-defects.md`: zero trailing
  whitespace, tabs, NBSP/ZWSP/BOM, or `N x N`; every table's rows match its header (script-checked,
  fences skipped); no duplicate heading anchors in any of the five documents (reference.md 83/83,
  feasibility 35/35). The two deletions removed table rows, not headings, so no anchor moved; the
  count/positional phrases near them (`reference.md:296`, `:503`) point at rows the deletions did not
  move.
- **Gates:** `2198 passed, 1 skipped, 2 xfailed` (115.79s), `ruff check` clean, `ruff format --check`
  80 files, `mypy` clean on 45 files — the exact expected numbers.

## Could not check

- The new § Executability entry's own substitution methodology (a hand-written resolver plugin
  installed for the measurement, 60 synthetic units). My re-measurement substituted a **table source**
  instead, which answers whether H4b-2's codes fire but is not the same transplant.
- The report's per-commit intermediate test counts (2196 → 2195 → 2198). I confirmed the final number
  only.

## Tree state

Clean. Four mutations run (`cli.py` ×2, `stats.py` ×1 plus the arm-order direct-call probe), every one
reverted **by editing the file back** and confirmed byte-identical against a pre-mutation copy, with
behaviour re-verified by re-running. Two scratch test files and one worktree created and removed;
`__pycache__` and `pytest-of-joon` cleared. `git status --porcelain` is empty.
