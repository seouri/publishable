# Task 19 report — `ablate × groups` still composes, and `groups` still cannot be a parameter

Branch `h3c1-arms-read`. All steps done. Full suite green: `uv run pytest` — 1495 passed, 2 xfailed.
`uv run ruff check .` and `uv run mypy` both clean.

## Step 1 — `ablate × groups` arithmetic and labels

`tests/test_validate.py::test_ablate_times_groups_gives_one_baseline_and_its_ablations_per_level`
runs `sweep.expand` directly on § Expansion modes' own YAML (`cohort` derivation/validation,
`features.labs`/`features.notes`) — 2 levels × (1 baseline + 2 ablations) = 6, per the addendum's
correction (not the 2 × 4 = 8 the original brief proposed). Asserts the exact label **set** (not
just the count) and that the two baselines land at different indices.

**Found, and left alone on purpose:** `expand`'s actual index order (both baselines first as a
leading block; every ablation after) does not match reference.md's own Index row for this exact
example (`00_cohort=derivation__baseline`, …, `03_cohort=validation__baseline`). This is not new —
it is `docs/superpowers/spec-defects.md` § Per-cell baseline numbering, already recorded, with
explicit ownership: "a document decision... not a code change taken on the way past." **Per
review, the test does not assert this order at all** — an earlier draft pinned
`conditions[:2]`'s labels to the leading-block order, which review flagged as entrenching a
divergence from a normative document for zero gain (nothing the brief requires depends on the
order; "one baseline per level, not per run" is already carried by the label set and by
`derivation_baseline.index != validation_baseline.index`). The docstring still cites the
spec-defect entry so a reader knows why the document's own numbering isn't asserted here, but the
test no longer pins either ordering.

A second test, `test_ablate_times_groups_with_declared_paths_validates_clean`, proves the same
composition validates clean using paths `GenericTemplate.parameter_spec` actually declares (only
`analysis.drop_missing` is boolean, so this shape is 2×(1+1)=4 — deliberately a different count
from the arithmetic test so the two are never confused).

## Step 2 — `groups` colliding with a parameter path: a real gap, fixed

Per the addendum's correction: `E-SWEEP-GROUPS-PARAMETER` was **not** minted; task 5's
`E-SWEEP-PATH-DUPLICATE` is the existing refusal and is pinned as-is
(`test_a_group_axis_may_not_name_a_path_a_parameter_axis_writes`, pre-existing, untouched).

What the addendum flagged as genuinely open — **a `by` naming a parameter that is declared but not
swept** — was verified as a real gap by direct probe before any fix: `sweep.groups: [{by:
analysis.method, levels: [pearson, spearman]}]` (no `grid`/`paired`/`sample` naming that path)
drew only `E-DATA-ALLOCATION-WITHIN-ARMS` — none of the eight `sweep.groups` § Validation rows —
because the existing check only reads `named_by` (built from `grid`/`paired`/`sample` entries),
never `spec` (the template's declared parameters).

**Fix:** `src/publishable/validate.py`, extending the `group_axes` loop (§ "A group axis's `by`
sharing a path with a parameter axis") to also fire when `path in spec`, checked AFTER the
existing `named_by` (swept) case rather than before — a path that is both swept and declared gets
the swept message, which names the other axis that silently loses its value and is the sharper of
the two harms. `docs/reference.md` § Validation's existing `E-SWEEP-PATH-DUPLICATE` row is extended
in place rather than given a new row, because both halves are one fault — a `by` naming a
parameter path, so `expand` marks it a selector and the label claims a value nothing plants — and
the swept half is a wider consequence of that same fault (it strands another axis too), not a
different fault needing its own code.

**Correction to an earlier draft of this report:** the original justification for extending rather
than minting cited `validate.py`'s docstring "counts eight § Validation rows" for `sweep.groups`.
That phrase belongs to `_check_assign`'s docstring and counts `allocation`/`assign` rows — a
different family, unaffected by this change either way. The decision to extend was independently
correct (see above); the citation supporting it was not.

**Review also caught a real ordering bug in the first draft of the fix**, now corrected: the
`path in spec` branch was checked *before* `named_by`, so a path that was both swept and declared
reported the weaker, unswept message instead of the sharper swept one — and the swept message
became reachable only when the swept path was undeclared (`E-SWEEP-PATH-UNKNOWN` territory, a
config already broken by a misspelling), which is why the existing swept-collision test never
noticed. Fixed by checking `named_by` first; verified by direct probe that
`groups: [{by: analysis.method}]` beside `grid: {analysis.method: [...]}` now reports the swept
message ("names a path `sweep.grid.analysis.method` also writes...").

New test: `test_a_group_axis_may_not_name_a_declared_parameter_even_if_unswept`. Beyond the
refusal, it asserts the harm directly: `expand` marks `analysis.method` a selector on the
`method=spearman` row, so `resolve_condition_cfg` skips planting it and the resolved config keeps
`analysis.method: "pearson"` — the base value — while the condition's own label and directory claim
`spearman`. Control: `by: cohort` (not a declared parameter) draws *Arms need allocation* alone.

## Step 3 — `groups × cluster_by`

Fixture (`_GROUPS_CLUSTER_ARMS`/`_GROUPS_CLUSTER_SITES` in `tests/test_validate.py`): 7
`control`/5 `treatment` units over 3 sites, built so every site spans both arms and `control`
alone touches all three sites — crossing task 12's 7/5 arm fixture and `test_runner.py`'s
5-unit/3-cluster harness, neither of which shares the other's partitioning attribute at all.

Per the addendum's correction, no `sweep.baseline` and no `statistics.contrasts`:
`test_groups_and_cluster_by_compose_with_no_comparison` validates the combination fully clean.
The can-fail control, `test_a_contrast_beside_groups_and_cluster_by_draws_both_refusals`, adds a
declared cross-arm contrast to the same fixture and asserts the **exact** set —
`{E-DATA-CLUSTER-CONTRAST, E-DATA-ALLOCATION-CONTRAST}` — confirmed by direct probe (task 16b
means two reporters fire over one comparison, not one). Mutation-verified: disabling
`E-DATA-CLUSTER-CONTRAST`'s guard makes the control test fail (missing from the set); reverted and
re-confirmed passing.

**Added per review (Minor 4):** validating clean is what lets the combination execute, and nothing
pinned that it actually does. `tests/test_cli.py::test_groups_and_cluster_by_execute_with_per_arm_cluster_counting`
runs the identical fixture (same 7 `control`/5 `treatment`/3-sites-crossing partition) through
`main(["run", ...])` to a real `run.yaml`, asserting `n` gains `clusters: 3` for BOTH arms
(`control`'s `n = {resolved: 7, completed: 7, ..., clusters: 3}`, `treatment`'s `{resolved: 5,
completed: 5, ..., clusters: 3}`) and that both conditions' interval uses
`t_over_units_clustered` — matching the reviewer's own independent measurement exactly.
Mutation-verified: reverting `_condition_beside_n`/`_condition_counts` to whole-roster behavior
makes this test fail (`control`'s `n` reports the full 12-unit roster instead of its own 7);
reverted and re-confirmed passing.

## Step 4 — `groups × measurements` end to end

`tests/test_units.py::test_a_constant_arm_survives_collapse_and_reaches_the_right_condition`,
placed beside task 11's own `test_an_arm_constant_within_a_units_rows_is_accepted` (which proves
attribute + `technical_n` survive collapse but stops there). Adds the third assertion the
addendum calls out as what makes it end to end: `units.arms_of` over the **actual roster
`resolve_units` produced** correctly partitions `p1`/`p3` (`control`) from `p2` (`treatment`).
Uneven measurement-row counts (2/3/2) make `technical_n` discriminating.
Mutation-verified: replacing computed `min`/`max`/`median` with constants fails the test; reverted
and re-confirmed passing.

## Step 6 — the end-to-end counting test task 13 could not write

`tests/test_cli.py::test_groups_between_and_by_attribute_reach_all_three_narrowed_call_sites`. A
real `sweep.groups` + `allocation: between` + `assign.method: by_attribute` +
`data.units.measurements` + `statistics.report_by` config, validating clean, run through
`main(["run", ...])`. Fixture: 4 `control` / 3 `treatment` (7 total, distinct from every other arm
fixture in this file and from `test_runner.py`'s cluster harness), with `arm` and `cohort` chosen
to genuinely cross so `report_by`'s per-level counts change under arm-narrowing rather than merely
gaining levels. `c1` is `io.skip`-ped (proves `control`'s `ineligible: 1`), `t1` is left
unrecorded (proves `treatment`'s `failed: 1`).

Asserts all three things `command_run`'s per-condition loop calls the narrowing helpers for:

- Call site 1 (`_condition_counts`): exact per-arm `n`, `resolved == completed + ineligible + failed`.
- Call site 2 (`_condition_report_by_levels`): exact `by.cohort` level counts, per arm — different
  in `control` than in `treatment` since the two partitions cross.
- Call site 3 (`_condition_beside_n`): `technical_n` **absent** from both conditions' `score`
  metric, because each was handed a narrowed (arm) roster rather than the whole one — itself a
  discriminating assertion, since a reversion to the whole roster makes `cond_roster is roster`
  true again and `technical_n` would reappear.

**Mutation results — reported as instructed, loudly:**

> Reverting all three of `command_run`'s call sites to whole-roster behavior (passing `None` for
> `arm_members_map` at each of the three sites) **makes this test FAIL** — `control_n`/`treatment_n`
> both report against the full 7-unit roster instead of their own arms.
>
> Each site was also reverted **individually** (three separate mutation runs, each followed by a
> `find … -name __pycache__ -exec rm -rf` and a revert, verified by re-running the test to a clean
> pass before moving to the next):
> - Site 1 alone (`_condition_counts`) → **test fails** (wrong per-arm `n`).
> - Site 2 alone (`_condition_report_by_levels`) → **test fails** (wrong per-level `by.cohort` counts).
> - Site 3 alone (`_condition_beside_n`) → **test fails** (`technical_n` reappears).
>
> **This is the opposite of task 13's disclosed finding.** Task 13's own Step 5 mutation passed
> green because `command_run`'s aggregation loop was unreachable end to end while
> `E-SWEEP-GROUPS-UNSUPPORTED` stood. Task 17 retired that refusal, and — checked directly, not
> assumed — the narrowing fix **is** wired in at all three call sites as of this run: every one of
> the four mutations above (three individual, one combined) is caught. There is no unpinned gap
> to report as Critical at this call site as of task 19.

## Files changed

- `src/publishable/validate.py` — Step 2's fix (extends the existing `E-SWEEP-PATH-DUPLICATE`
  check to also read `template.parameter_spec`, not only swept axes; checked AFTER the swept case
  per the review round below).
- `docs/reference.md` — the same row's prose extended in place (no new row; § Validation).
- `tests/test_validate.py` — Steps 1, 2, 3.
- `tests/test_units.py` — Step 4.
- `tests/test_cli.py` — Steps 3 (execution) and 6.

No other files touched. No probe/scratch files left in the tree.

## Review round (coordinator, after initial submission)

Spec ✅, quality strong; reviewer independently re-ran every mutation and confirmed step 6 kills the
test at all four sites, and confirmed step 2's gap was real (pre-fix `validate.py` fails the new
test with the code absent, and the harm assertions pass on the old code — the harm predates the
fix). Four items, all addressed:

1. **Important — branch order bug in step 2's fix, now corrected.** The `path in spec` check fired
   *before* the swept-collision (`named_by`) check, so a path that was both swept and declared
   reported the weaker, unswept message instead of the sharper one naming the OTHER axis that
   silently loses its value — and the swept message became reachable only when the swept path was
   undeclared (`E-SWEEP-PATH-UNKNOWN` territory), which is why the pre-existing swept-collision
   test never caught the ordering. Fixed by checking `named_by` first; the comment describing the
   (wrong) order was corrected to match. No refusal was ever lost — same code, same path; only the
   message differed. Verified by direct probe (see Step 2 section above).
2. **Minor — dropped the index-order assertion in Step 1's test.** Kept the docstring's citation
   of the spec-defect entry; removed the `conditions[:2]` label-order assertion, since it pinned a
   documented divergence for no gain the brief required.
3. **Minor — corrected a wrong citation in this report.** The "eight § Validation rows" phrase is
   `_check_assign`'s docstring (a different family, `allocation`/`assign`), not evidence for the
   extend-vs-mint decision. The decision itself was independently correct; only the citation
   supporting it was wrong. Corrected in the Step 2 section above.
4. **Minor — added the `groups × cluster_by` end-to-end execution test** Step 3 could not include
   (validate-level only, correctly, per the addendum's baseline/contrast restriction). Added to
   `tests/test_cli.py`; see Step 3 section above.

`uv run pytest` (1495 passed, 2 xfailed), `ruff check .`, and `mypy` all re-confirmed green after
these changes.

## Second review round — the Minor 4 test could not fail on the mutation it claimed to guard

Coordinator's finding: the reviewer mutated `runner._counts` —
`cluster_count_of(clusters, completed)` → `cluster_count_of(clusters, clusters.keys())` — and
`test_groups_and_cluster_by_execute_with_per_arm_cluster_counting` still passed, because the
fixture's every site spanned both arms, so the correct arm-scoped count and the buggy
whole-roster count both landed on 3. Instructed to give at least one site units in only one arm
and re-confirm the mutation now fails.

**The fixture fix alone does not make it fail — verified empirically, not assumed — and the real
cause is a second, independent fact about the code, not only the fixture.**

Fixed the fixture first (sites `C`/`D` now arm-exclusive — `control`'s own sites are `{A,B,C}`,
`treatment`'s are `{A,B,D}`, each 3, against a whole-roster total of `{A,B,C,D}` = 4 — a mix that
keeps at least one cluster (`A`, `B`) spanning both arms, the shape § Clustered units says
`by_attribute` allows and this design isn't the one that requires it). Then ran the reviewer's
exact `runner.py` mutation against the corrected fixture: **the test still passed, unchanged, at
3/3.**

Traced why: for a RECORDED column (`pred`, what this test reads), `stats.summarize_step`
recomputes `clusters` per column from that column's own carrier keys
(`cluster_count_of(clusters, column_keys)` at `stats.py` ~line 1360) and **unconditionally
overwrites** whatever `runner.attrition`/`_counts` computed — the docstring at that line says so
explicitly ("`clusters` is recomputed per column, for exactly the reasons `completed` and
`effective` already are"). The one path that would pass `attrition`'s own figure through
unmodified — a DERIVED metric, `{**counts}` with no override — is refused unconditionally whenever
`cluster_by` is declared (`E-DATA-CLUSTER-DERIVED`; confirmed by probe with `aggregate_returns`
and no `statistics.resample` declared, and already pinned by
`test_a_clustered_derived_metric_is_refused_rather_than_drawn`). So `runner._counts`'s own
`cluster_count_of(clusters, completed)` line **cannot reach any `command_run`-produced `run.yaml`
for any config with `cluster_by` declared** — not a fixture problem, an architectural one.

This does not mean the arithmetic is unpinned: `tests/test_runner.py`'s
`test_n_gains_clusters_under_a_clustered_design`, `test_every_attrition_return_site_agrees_about_clusters`,
and `test_clusters_and_effective_are_independent_parts_of_n` call `attrition` directly and DO catch
the reviewer's exact mutation (verified: applied, all three FAIL; reverted, all three PASS). It
means the mutation's effect is invisible at the one further hop (`run.yaml`) this task's own test
operates at.

**Fix applied:** retargeted this test's discriminating mutation to the site that actually produces
what it reads — `stats.py`'s `cluster_count_of(clusters, column_keys)` → `cluster_count_of(clusters,
clusters.keys())` — verified: applied with the corrected fixture, both arms report `clusters: 4`
(FAIL against the asserted 3); `__pycache__` cleared; reverted; both arms back to `clusters: 3`
(PASS). The docstring is rewritten to state what the number is actually computed from, name the
correct discriminating mutation site, and record both mutation results (the reachable one that
fails, and the reviewer's original one that — checked, not assumed — does not and cannot through
this route) so the next reader doesn't repeat the same probe.

`tests/test_validate.py`'s `_GROUPS_CLUSTER_SITES` mapping (Step 3's validate-level fixture) is
updated to match `C`/`D` exclusivity, keeping the "same design" claim between the two files true;
its own two tests are declaration-level only and unaffected by the change (re-run and confirmed
still `set()` / `{E-DATA-CLUSTER-CONTRAST, E-DATA-ALLOCATION-CONTRAST}`).

**Routing note, not a fix taken here:** whether `runner._counts`'s per-condition `clusters` figure
should ever be observable end to end for a recorded column (or whether the per-column recompute in
`stats.py` should be the only source of truth, making the `runner.py` line's output genuinely
write-only outside direct tests) is a design question this report surfaces rather than resolves —
no code was changed to address it, and no new `E-` code or spec-defects entry was minted.

`uv run pytest` (1496 passed, 2 xfailed), `ruff check .`, and `mypy` re-confirmed green after this
round.

## Third review round — the unreachability finding was right, three wording corrections

Coordinator confirmed independently: the retarget discriminates (`stats.py` mutation fails, revert
passes; `runner._counts` mutation does not fail this test but does fail the three direct-`attrition`
tests), the fixture satisfies both constraints, and the tree was clean. **The disposition is
settled as leave-and-record — no code logic change, no spec-defects entry, no new code** — but
three wording corrections were required because the write-up overstated the finding in the
direction that would stop a future reader from re-checking it. All three are docstring/comment-only.

1. **"Refused unconditionally" was false.** `stats.py`'s derived-metric block IS a live consumer of
   `attrition`'s own `clusters` figure — `"n": {**counts, "completed": len(collapsed)}` passes it
   straight through, with no per-column override. The gate that gets in the way today is narrower:
   `if clusters is not None and seed is not None:` plus a non-empty `drawable`, and it closes only
   because `command_run` always supplies a real seed (`resample_seed(digest)` never returns `None`)
   and always builds a resample closure for every derived key. Corrected in
   `tests/test_cli.py`'s docstring to say this precisely, naming what a fourth call site omitting
   `seed`/`resample` would do differently.

2. **The absolute was unmarked as time-bounded.** "No config reaches `run.yaml` with `attrition`'s
   own clusters figure displayed for `cluster_by` at all" holds only while `E-DATA-CLUSTER-DERIVED`
   stands, and `reference.md` marks it *Temporary* in two places, both naming H4 as the slice that
   lifts it. Corrected in the same docstring to scope the claim to "today's build" and name H4 as
   the condition under which the discriminating mutation site (`stats.py`, not `runner.py`) may need
   revisiting.

3. **One clause in `runner._counts`'s own docstring invited the misreading.** It justified the
   `clusters` figure as "the df of an interval" without noting that for a recorded column the actual
   df a reader sees comes from `stats.summarize_step`'s own per-column recompute (identical for a
   full column, correctly narrower for a ragged one) — not from this line. Added one clause to
   `src/publishable/runner.py`'s `_counts` docstring pointing at `summarize_step`'s "`clusters` is
   recomputed per column" paragraph, so the next reader sees the pointer before writing the same
   mutation the reviewer did.

**No code behavior changed in this round** — `src/publishable/runner.py` gained one docstring
paragraph (no logic touched), `tests/test_cli.py`'s docstring was reworded, and no test assertions
or fixtures changed. `uv run pytest` (1496 passed, 2 xfailed), `ruff check .`, and `mypy` all
re-confirmed green.
