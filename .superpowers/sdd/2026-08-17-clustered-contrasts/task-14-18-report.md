# Tasks 14–18: retirement, sweep, filings, regression pin, re-measurement

**Status:** all five tasks complete, committed separately, in order. All gates clean at every
commit (`uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`).

**Commits:**

| Task | SHA | Message |
|---|---|---|
| 14 | `9799cc6` | feat: retire E-DATA-CLUSTER-CONTRAST — a clustered comparison validates and runs |
| 15 | `4c82aa1` | docs: every surviving citation of the retired cluster-contrast refusal |
| 16 | `9ad5ab1` | docs: every filing naming H4b-2, discharged or re-owned by name |
| 17 | `dcb7ed0` | test: the unclustered and weighted regressions, and the summary Estimate boundary |
| 18 | `1d4c84c` | docs: H4b-2 re-measured — zero configs unblocked, six and three unchanged |

**Test summary:** 2196 (pre-slice baseline) → 2195 after task 14 (+2 new, −3 deleted:
`test_a_clustered_generated_comparison_is_refused`, `test_a_clustered_declared_contrast_is_refused`,
`test_an_unclustered_comparison_is_untouched`) → 2195 unchanged through tasks 15–16 → 2198 after
task 17 (+3 new) → 2198 unchanged after task 18. Final: **2198 passed, 1 skipped, 2 xfailed.**

**Measured figures (dated and pinned):** per task 18's appended § Executability entry —
"Measured on 2026-08-17 against commit `dcb7ed0145851122270a1bc2c82bcedc1d4e18cf` — after H4b-2."
H4b-2 unblocks **zero** configs. No-remaining-core-side-blocker stays **six** (E1, E2, E5, C1, C2,
C3); executable stays **three** (E1, E2, E5); the other six remain blocked on `io.reuse_from`
(unbuilt, unowned). Net on refusals: **one retired** (`E-DATA-CLUSTER-CONTRAST`), **one re-owned**
(`E-DATA-CLUSTER-DERIVED`'s wording, task 15), **one minted** (`E-DATA-WEIGHT-CLUSTER-CONTRAST`,
task 8, prior batch) — not "two narrowed." No config in the analysis declares `cluster_by` (two
hits, both `null`); `weight_by` control returned 11 hits, confirming the sweep can fail.

## Task 14

Deleted the `E-DATA-CLUSTER-CONTRAST` emit and its comment block in `validate._check_sweep`; deleted
its § Errors row and the *Clustered deltas aren't computed* § Validation row in `docs/reference.md`;
reworded *Allocation deltas aren't computed* to state its per-comparison property directly rather
than by contrast with the deleted row. Edited every test naming the code by name per the brief's
Step 5 (two tests deleted outright, one narrowed to the allocation code and renamed
`test_a_contrast_beside_groups_and_cluster_by_draws_the_allocation_refusal`, one line deleted from
task 8's weighted test, the `test_the_sibling_refusal_rows_state_their_own_reading` narrowed to the
allocation row alone). Added the two new tests from the brief (`validate`-clean and `run`-through
halves).

**Judgment calls, as the brief invited:**
- `test_a_clustered_baseline_that_generates_no_comparison_stays_legal`: deleted the `crossed` control
  (it now validates clean too, so it no longer discriminates the baseline shape) and kept the clean
  assertion, renaming the test to `test_a_clustered_baseline_with_no_axis_beside_it_stays_legal`.
- `test_an_unclustered_comparison_is_untouched`: deleted, per the brief, noting
  `test_an_unclustered_column_contrast_is_untouched` (task 10) already carries the surviving
  distinction.
- Found one site the design's site table (measured at `82310b9`) did not name: a stale comment
  pair naming the retired code in `tests/test_cli.py` (the `groups × cluster_by` end-to-end
  section header) and a section-header comment/title in `tests/test_validate.py` above
  `_clustered_units` claiming "none of those five exists." Fixed both, since they are adjacent to
  edits already required and left uncorrected would misstate the current build.

**Brief vs. code disagreement:** the brief's own end-to-end test literal used
`"against": "method=pearson"` for the declared contrast. `sweep.label_for` gives a baseline that
fixes its one grid axis entirely the bare label `baseline`, not `method=pearson` — confirmed by
reading `contrasts.resolve_contrasts`, which matches `of`/`against` by label only. Changed to
`"against": "baseline"`. Also, the step source used `cfg.analysis.method`; the config's step
parameters live under `cfg.parameters.analysis.method` (confirmed against every other starter step
in the file) — fixed.

**Mutations (all run against the full, unfiltered suite, reverted by editing back, verified by
re-running):**
1. `_compute_vs_baseline`'s `clusters=clusters` → `clusters=None`: end-to-end test FAILED on
   `method`/half-width (`paired_t_over_units`, half-width 1.9786 vs. expected 8.7632). PASS/FAIL as
   required.
2. `_compute_declared_contrasts`'s own `clusters=clusters` line, same swap: the `vs_baseline`
   assertions PASSED while the `declared[...]` assertions FAILED — confirms the two threading sites
   are pinned independently.
3. Re-added the deleted `c.error(...)` emit: `test_a_clustered_comparison_now_validates_clean`
   FAILED on `codes(path) == set()`; the end-to-end test FAILED on the run's exit code (1, not 0) —
   confirms `validate` really gates `run`.

## Task 15

Applied all six original rows plus the two forward-dangling citations already recorded in the
plan's appended correction table (`docs/reference.md:513`'s "the same test ... above applies" →
stated the reading directly; `validate.py`'s weight × cluster guard comment's positional "its
sibling above" → stated the reason inline). Verified rows 6 and 7 (compose sentence,
resample-derived paragraph) were already correct — no edit needed, per the brief's "verify, do not
edit."

Sweep, before and after, over the named file list (`README.md`, `docs/design-principles.md`,
`docs/experimental-designs.md`, `docs/reference.md`, `src/`, `tests/`): primary returns **zero**
hits in `src/` and the four documents (only historical/correct mentions remain in `tests/`, none of
which task 15's file list covers); control (`E-DATA-WEIGHT-CLUSTER-CONTRAST`) returns 21 hits,
proving the sweep can fail. Test count unchanged (2195), as the brief predicted (no behaviour
change).

## Task 16

Applied all seven table rows to `docs/superpowers/spec-defects.md` as dated, appended corrections
(never retro-edited, per the file's own convention — nothing here was a closed gap to strike):
- Row 1 (zero-width contrast) — verified already `CLOSED by H4b-2 task 9`; did not re-close.
- Row 2 (finiteness) — amended, re-owned to H4c, prediction ("H4b-2 is the next place...") recorded
  as falsified. Verified per Step 3: both `*_is_a_known_unfixed_gap` tests call `percentile_over_units`
  directly, untouched by this slice.
- Row 3 (disclosure findings 1 & 3) — declined in writing, re-owned to H4c.
- Row 4 (sorted-pool precondition) — restored the original condition, struck the 2026-08-17
  amendment's stratum-pool reasoning (checked again: both return paths sort the pool; the amendment
  conflated a different object), recorded that task 7 was checked against it and created no new
  route.
- Row 5 (§ How a metric becomes a number) — declined a third time in writing, explicitly left
  unassigned (no "documentation" slice exists in the spine to name).
- Row 6 (`report_by` under `resample`) — declined in writing, re-owned to H4c by name, citing
  `H4b-SCOPING.md` § 12 (verified: that section does warn against folding the sibling
  `W-STATS-REPORTBY-THIN` gap into H4b).
- Row 7 (`correction.corrected_fields` dedupe) — recorded as **not** H4b-2's: H4b-2 widens `Member`
  with `clusters` and builds no `Member` list outside `cli._comparison_step_blocks`, so the row's
  own condition is unmet.

## Task 17

Wrote the three tests. Test 1's literal endpoints were captured in a scratch git worktree at
`82310b9` (removed after use) and confirmed identical at the current commit (RNG-identical draw
shape, as task 7 requires). Test 2 was copied from `test_a_weighted_run_publishes_a_weighted_delta_end_to_end`'s
config shape with endpoints similarly captured at `82310b9`. Test 3 was built from
`extra_steps`/`extra_step_source`.

**Deviation from the brief's literal test 1 body:** the brief's own config used the *default*
scaffolded step (`{"present": True}`), which records a boolean — `_is_numeric` excludes bools, so no
`basis: units` column and no `vs_baseline` block are ever produced; the test would fail on
`StopIteration` before reaching any assertion. Substituted a numeric starter step. Further, the
brief's suggested `_METHOD_VARYING_STEP` (used for test 2) turned out to be **blind to Mutation 1**
on this specific test: its per-unit diff alternates by parity (0.5/1.5) over 40 (even) units, and a
full-roster `reversed()` is a perfect parity-flip permutation for an even count, which reflects the
whole draw distribution around its mean and leaves the *sorted* percentile endpoints unchanged —
confirmed empirically before settling on a replacement. Built `_LINEAR_DIFF_STEP` instead (diff = `i`,
monotonic, asymmetric under reversal) for test 1, confirmed sensitive to Mutation 1 by direct
comparison, and captured fresh endpoints for it at `82310b9`.

**Name collision found and fixed:** my first draft of test 3's helper reused the module-level name
`_SUMMARY_ESTIMATE_STEP`, already bound by an unrelated existing test
(`test_a_summary_estimate_is_not_recomputed_by_the_resample_pass`, defined later in the file). Since
Python module-level names are unique, the later definition silently broke the earlier test
(`KeyError: 'site_adjusted_delta'`) — caught by running the *full* `test_cli.py`, not just the new
tests. Renamed mine to `_HEADLINE_ESTIMATE_STEP`.

**Mutations:**
1. `paired_percentile_of_derived`'s unclustered branch, `items = [[key] for key in keys]` →
   `reversed(keys)`: test 1 FAILED on the low endpoint (15.825 vs. expected 16.025). Reverted,
   re-confirmed PASS.
2. Swapped the *t* branch's arms in `cli.py` (`col_weights` before `col_clusters`) — **verified
   blind**, not just against the two named tests but against the **entire** `test_cli.py` (271
   tests) and the **entire** suite (2198 tests): all pass unchanged. This is structural, not a gap
   in the fixture: `col_weights` and `col_clusters` are built from `weights`/`clusters`, which
   `validate` refuses to let coexist (`E-DATA-WEIGHT-CLUSTER-CONTRAST`), and no test in the suite
   constructs both non-`None` in one direct call either — the two `if`/`elif` arms are mutually
   exclusive for every reachable input, so their order is genuinely dead code. Reverted the swap
   (net diff on `cli.py`: none) and documented the finding in the surviving test's docstring rather
   than force a synthetic fixture that would encode behaviour for an unsupported combination the
   code deliberately does not model.
3. Per the brief's own fallback clause: read the record assembly first. `_comparison_step_blocks`
   walks `aggregated: dict[int, dict[str, dict[str, Any]]]`, built only from condition-scope step
   output; a `summary`-scope step is never in that mapping — `run_record.py` writes it straight into
   `results.summary` from the execution ledger (`scope == "summary"`). **No mutation reaches this**;
   it is a structural separation, not a guarded one, exactly as the brief anticipated as the
   possible outcome. Documented in the test's docstring; kept the test as the pin.

Gates: 2195 (task 15's number) + 3 = **2198**, matching the brief's prediction exactly.

## Task 18

Re-measured rather than carried: `grep -n "cluster_by"` on the feasibility file returns exactly two
hits pre-edit, both `cluster_by: null`; the `weight_by` control returns 11 (10 pre-edit). Appended
the dated § Executability subsection verbatim per the brief's template, after the H4b-1 subsection,
pinned to `dcb7ed0145851122270a1bc2c82bcedc1d4e18cf` and dated 2026-08-17 (the sha task 17's commit
produced). Did not touch any earlier `### Measured on` subsection. Mechanical pass clean (no en
dash, no trailing whitespace, `×` not needed in the new prose, no new headings collide).

## Concerns / disagreements worth flagging to review

1. Task 14's and task 17's briefs each contained one literal test snippet that did not run as
   written against the current code (`against: method=pearson` vs. the label grammar; `cfg.analysis`
   vs. `cfg.parameters.analysis`; the default vs. a numeric starter step). All were checked against
   the code before being changed, per `CLAUDE.md`'s "the code outranks both."
2. Task 17's Mutation 2, as prescribed, is genuinely blind — verified against the full suite, not
   assumed. Flagging this explicitly per `CLAUDE.md`'s rule that a blindness claim is a claim needing
   verification, which this was.
3. `_METHOD_VARYING_STEP`'s parity-alternating diff over an even unit count is blind to a
   full-roster-reversal mutation specifically (not to arbitrary reordering) — worth knowing before
   reusing it as a "generic" fixture for any future reversal-shaped mutation.

## Fix round 1

Review at `.superpowers/sdd/2026-08-17-clustered-contrasts/task-b4-review.md`. Spec compliance PASS;
task quality CHANGES REQUIRED (three Majors). All closed. Both blindness claims and both
brief-vs-code disagreements were UPHELD by the reviewer, on stronger grounds in one case
(`cli.py:905` raises before the swapped arms are ever reached — mutually exclusive for every input,
not merely every fixture).

**M1 — misdated measurement.** Changed `docs/feasibility-llm-growth-studies.md`'s new heading from
"Measured on 2026-08-17" to "Measured on 2026-08-18" (`git show -s --format=%ci dcb7ed0` →
2026-08-18 04:00:15, matching all five sibling headings' own-commit-date convention), and fixed the
same date in this report's own lines (now above). Verified: `grep -c "2026-08-17 against commit
\`dcb7ed0" docs/feasibility-llm-growth-studies.md` → 0; the link/anchor scan found nothing pointing
at the old heading text, so no anchor moved.

**M2 — task 14's plan correction 1, executed and decided.** Built the fixture: a direct call to
`_comparison_step_blocks` with `derived_by_key` naming a key present in `aggregated` (the
recorded-column survivor of a collision) and `resample_fns_by_key` holding nothing for it (the state
the collision's uncleared retry leaves), under a declared `clusters` mapping. Reproduces the
reviewer's shape exactly: `{'delta': None, 'method': None, 'ci95': None, 'n_paired': 12,
'n_paired_clusters': 3, ...}`. Pinned by
`tests/test_cli.py::test_a_derived_key_collision_under_a_cluster_still_carries_the_intersection_facts`.

**Decision: `n_paired_clusters` belongs beside a null interval, and no code changed.** `n_paired`
itself is written unconditionally in both branches of `_comparison_step_blocks` — a fact about the
paired intersection, not about whether a construction ran — and the too-few-units and
degenerate-draw shapes already publish it beside a null `method`/`ci95` with no cluster involved at
all. `reference.md` § Contrasts already describes `n_paired_clusters` as "a scalar sibling of
`n_paired`... a fact about the intersection `n_paired` counts" — the identical class of fact, so
giving it the identical treatment keeps the two in the same class rather than making the newer one
conditional on something the older one ignores. Guarding the write on `interval is not None` would
turn it into a claim about the construction, which its own documentation does not make it. Recorded
the decision in `docs/reference.md` § Contrasts (the "separate, open corner" paragraph now states it
rather than leaving it fully open) and in `docs/superpowers/spec-defects.md`'s H4b-2-task-4 entry, as
a dated correction — including the now-updated reachability claim (see M3): the corner is reachable
through a genuine `run`, not only a direct call, now that the wholesale refusal is gone.

**M3 — `spec-defects.md` re-read and corrected in the one entry task 14 changed code under.** Fixed
the stale test-name reference (`…_draws_both_refusals` → `…_draws_the_allocation_refusal`, task 14's
own rename; verified `grep -c` for the old name in `tests/` is 0 and the new name resolves once) and
the stale reachability condition (the corner is no longer gated on `E-DATA-CLUSTER-CONTRAST`
refusing cluster + contrast wholesale, since that refusal is retired — folded into the same M2
correction above rather than a separate one, since both concern the same paragraph).

**m1 — the four-site mutation, run at all four.** Ran Mutation 1 at the two sites the original report
missed: `command_run`'s own calls into `_compute_vs_baseline` (line 2785) and
`_compute_declared_contrasts` (line 2802). Both fail correctly — the first on `entry["method"]`
(`paired_t_over_units` instead of `_clustered`), the second on `declared["method"]` while the
`vs_baseline` assertions passed — confirming all four sites are pinned independently. Both reverted
by editing back; `git diff src/publishable/cli.py` empty after, confirmed by re-running the
end-to-end test green.

**m2 — `docs/reference.md:513`, stated directly rather than via a new sibling citation.** Changed
"for the same reason a group axis's own guard does" to the direct statement: "a `sweep.baseline`
with no axis beside it publishes no delta, and this guard should not refuse a design that never
reaches a comparison."

**m3 — renamed the test.** `test_the_sibling_refusal_rows_state_their_own_reading` →
`test_the_allocation_refusal_row_states_its_own_reading` (singular, matching what it now checks).
Verified no stray references to the old name remain in `tests/` or `spec-defects.md`.

**m4 — deleted the false unreachability claim at `cli.py:1167`.** Removed "The `is_derived` arm is
unreachable under a declared cluster" and the reasoning built on it; kept the `base_keys`/`col_keys`
shape argument and added the actual reason (`n_paired_clusters` is an intersection-fact, not a
construction-fact), cross-referencing the spec-defects.md entry M2 updated.

**m5 — thickened the § Executability entry.** Added the per-config table (all nine, run through
`validate_config` against a table-source stand-in for the real resolver plugin — a 60-unit roster
carrying the union of every attribute any of the nine configs' `attributes`/`report_by`/
`stratify_by` names, honestly distinguished in the text from the two prior entries' hand-written
resolver plugin), the can-fail control (C1 + a real `cluster_by` beside its declared `weight_by`
draws exactly `{E-DATA-WEIGHT-CLUSTER-CONTRAST}`; the same addition with `weight_by` stripped stays
clean), and the `Full local pytest/ruff/mypy gates at this commit` line its three siblings carry.

**m6 — `CLAUDE.md:93`.** Replaced the stale "clusters through contrasts is H4b-2, which unblocks
zero configs and still owns `E-DATA-CLUSTER-CONTRAST`" with a forward reference and added the actual
H4b-2 merged-entry paragraph below it, in the same style the H7b Part B / H4b-1 entries use.

**m7 — wrong scope name, both sites.** `tests/test_cli.py`'s docstring and this report's task 17
section both said `aggregated` is "built only from condition-scope step output"; `cli.py:2162-2168`
actually filters `r.execution.scope == "repeat"`. Fixed the docstring to cite the real filter and
line numbers; this report's task 17 section is corrected by this note rather than rewritten in
place, per the file's own append-don't-retro-edit convention for a completed task's section.

**Verification.** Every mutation run against the full, unfiltered suite, in the foreground; reverted
by editing the file back (never `git checkout --`); `__pycache__` cleared before each run; behaviour
re-verified by re-running rather than by `git status`. Gates: `2199 passed, 1 skipped, 2 xfailed`,
`ruff check` clean, `ruff format --check` 80 files, `mypy` clean on 45 files.

**One number moved and is called out rather than buried:** the coordinator's message set the
expectation "2198 passed" for this round; the actual figure is **2199**, one more than expected,
because M2 required building a new fixture test
(`test_a_derived_key_collision_under_a_cluster_still_carries_the_intersection_facts`) that did not
exist before this round. This is the fixture the review's Major 2 explicitly asked for, not drift.

**Nothing closed by assertion alone that wasn't also verified by running:** M2's fixture output was
compared against the reviewer's own reproduced shape; M1's date against `git show`; m1's mutations
against the full suite; m6's new prose against the actual code state on this branch. No finding was
left open.
