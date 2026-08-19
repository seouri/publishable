# H4d batch 4 report — tasks 16, 17+10, 18, 19, 20

## Status

All five tasks complete and committed, in order. Gates clean: `ruff check`, `ruff format --check`,
`mypy` (45 source files, no issues). Full suite: **2325 (pre-batch) → 2348 passed, 1 skipped, 2
xfailed** — a net +23 across the batch (task 16 +5, task 17+10 +10, task 18 +1, task 19 +2, task 20
+5), matching each brief's own delta.

## Commits

- `9f1fa46` — H4d task 16: `Member.p_value`, the widened family, and a rank tier that does not
  reach the evidence ratio
- `7d182e2` — H4d tasks 17+10: BH's suffix min, both per-member adjustments, and the warning
  narrowed in the same change
- `f2f0e93` — H4d task 18: `fdr_bh` made real end to end, and the `thin` interaction settled
- `79baad8` — H4d task 19: the contrast-side `p_value` and its resolved `null_test` echo
- `14bd0d5` — H4d task 20: the per-condition `p_value`, uncorrected, gated on an unbuilt clustered
  construction

## Test summary

One line per task, mutation outcomes all correct-direction (assertion failures, never crashes),
every mutation reverted by editing back and re-verified by rerunning the full suite:

- Task 16: 5 new tests in `test_correction.py`. Two mutations, both PASS→FAIL as predicted:
  (a) narrowing `family_members` back to `ci95 is not None` — the p-only member drops from the
  family; (b) the sentinel-ratio key `(0, 0.0, index)` instead of the tiered `(1, 0.0, index)` — the
  p-only member ties the zero-ratio one and wins on declaration index, producing `cond:3, cond:1,
  cond:2` exactly as predicted.
- Task 17+10: 10 new tests (7 `test_correction.py`, 2 `test_validate.py`, 1 `test_hypotheses.py`).
  Three mutations: (a) the suffix-min collapsed to a single assignment — Y reports 0.44 instead of
  the bound 0.41333…; (b) BH's sort key switched to the evidence ratio — X's adjusted value becomes
  `p` instead of `4×p`; (c) the `thin` narrowing's `and member.ci95 is not None` clause removed — a
  p-only member under `holm` now reports `thin: True`. All three FAIL as predicted.
- Task 18: 1 new test in `test_cli.py`, against `corrected_fields` + `_entry_for` directly (validate
  still gates `run`). Mutation: dropped the `bh` lookup — `KeyError` on `p_value_corrected`, caught
  as a test failure (not a crash) because the test asserts the key's presence before reading it.
- Task 19: 2 new tests in `test_cli.py` against `_comparison_step_blocks` directly, on Fixture C1
  (seed 11, n 5000 — `test_stats.py`'s own pin for `1/5001`). Mutation: the gate widened to fire for
  paired comparisons too (added the write to the paired recorded-column branch) — the paired control
  fails on `"p_value" not in entry`, an assertion, not a crash.
- Task 20: 5 new tests, 3 in `test_stats.py` (direct `summarize_step` calls) and 2 in `test_cli.py`
  (the real `_make_null_fn` closure, hoisted to module level so a test can call it, plus decision 7's
  recorded-column absence and the `report_by`-level ruling). Mutation: `_make_null_fn`'s `merged`
  dict reverted to bare `attrs` — the closure stops seeing the drawn labels and the two calls
  (observed-order, swapped-order) return unequal-but-now-wrong values, caught as
  `assert swapped == pytest.approx(10.0)` failing with `-10.0`.

## Rulings, as asked

**Task 16 — the widened `family_members` and its two consequences.** Widened to `e.ci95 is not
None or e.p_value is not None`, per the spec's decision 4 and reference.md's already-amended
sentence. Both mechanical consequences the spec named were real and are handled: (1)
`_evidence_ratio`'s `assert` is reachable now that a p-only member can enter the family, so
`rank_family`'s key **must** short-circuit before calling it — implemented as a tiered tuple
`(0, -ratio, idx)` / `(1, 0.0, idx)`, never an eager `-_evidence_ratio(m)` computed for every member.
(2) The tier is a tuple element, not a sentinel ratio, because `_evidence_ratio` legitimately
returns `0.0` for a real zero-delta member (task 27's `cond:3`) — a sentinel would tie a p-only
member against that real member and let declaration order (not the tier) decide, which mutation (b)
above demonstrates concretely. Both consequences are pinned by discriminating tests, not just
implemented.

**Task 18 — BH's ordering and accumulation.** BH ranks on the **ascending p-value** (decision 1),
never the evidence ratio — under `fdr_bh`, `_level_for` returns `None` for every member, so no
interval is ever built at a rank and the evidence ratio decides nothing there; the ranking-by-two-
statistics problem decision 1 forecloses does not arise. Only BH's adjustment is an
**accumulation** (a running suffix minimum over `m/i × p`, largest `i` down) — Holm's and
Bonferroni's are per-member functions of `(m, i)` alone (`min(1, p×(m−i+1))` and `min(1, p×m)`
respectively), computed at the member's own **evidence** rank, and Holm's non-monotonicity in the
raw p is the intended, asserted behavior (Y's 0.88 below Z's 0.93 despite a smaller raw p) — ranking
Holm on p instead would reintroduce the two-orderings problem decision 1 avoids. Fixture D pins all
of this with the p-order and evidence-order deliberately disagreeing, exactly as the spec requires.

**Task 17's owed check on `hypotheses.py`'s partial member set.** Measured by reading `evaluate`,
`_tested_number`, `verdict_for`, and confirmed by a new direct test
(`test_a_counted_hypothesis_on_a_p_only_member_records_an_unavailable_corrected_bound`): exactly one
field moves when a counted hypothesis's member is p-only — `observed.ci95_corrected` goes from
**absent** to **`null`**, because `corrected` is no longer `None` (the widened `family_members`
lets `corrected_for` return an entry for it) but its `ci95_corrected` is falsy, so
`corrected_unavailable` becomes `True`. `supported` does **not** move (a bound test had no raw
interval to read either, and this test used `evaluate_on: observed`, which bypasses the flag
entirely) and `family_size` does **not** move (`len(counted)`, unaffected by which members carry a
`Member`). BH over the partial member set: `i` runs over the members **present** (which can be
fewer than the declared `size`) while `m` stays the declared `size` — the larger-`m`/smaller-`i`
combination is the conservative direction, cited from `family_shape`'s own docstring rather than
re-derived as a second rule, per the spec's ruling.

## Disagreements between a brief/spec and the code — reported, not silently patched

**Task 20 — Fixture C2's prescribed literal (`p_value: 1/5001`, `level: "within_cluster"`) is
unreachable.** `stats.permutation_of_derived` (task 12, already merged) performs one free
`rng.shuffle` over every unit's label and takes no cluster argument at all — there is no
clustered counterpart. Measured directly against Fixture C's own 50-unit roster: the free
relabelling returns **p ≈ 0.4845**, which is exactly the spec's own "permutes across clusters (the
wrong stratum)" row, not the within-cluster `1/5001` a declared `cluster_by` promises. Per
CLAUDE.md's rule ("report the disagreement — do not adjust the fixture until it agrees") this was
not forced: `summarize_step`'s derived-null write is gated on `clusters is None`, so a declared
`cluster_by` now suppresses the write entirely rather than publishing a wrong number beside a
`level: "within_cluster"` echo that would be a false claim. Fixture C2's test is reshaped to the
roster the gate actually serves (no `cluster_by`, asserting the free-relabelling range
`0.3 < p < 0.7`, matching `test_stats.py`'s own existing pin on the identical fixture), plus a
second test pinning the gate itself (clustered call carries none of `p_value`/`null_draws`/
`null_test`; the identical unclustered call carries all three). Filed as a new OPEN entry in
`spec-defects.md`, owner unassigned (closing it needs a new `permutation_of_derived_clustered`
construction outside task 20's own file scope). The contrast-side (task 19, C1) is unaffected — it
delegates to `permutation_over_units_clustered` (task 13), which already has the clustered
construction, so C1's `1/5001` is genuine.

**Task 19's original blind-mutation risk, corrected before it shipped.** The brief's own
`_make_null_fn` code block is written as a closure capturing `aggregate_where` from
`command_run`'s locals, which (per the advisor's review) would leave it nested and untestable —
`E-STATS-NULLTEST-UNSUPPORTED` gates every config until task 21, so no `run` can reach it and no
direct-call test can build it either without a real project on disk. Hoisted `_make_null_fn` to
module level in `cli.py`, taking `aggregate_where` as an explicit parameter instead of a captured
name, so `test_the_null_closure_moves_with_the_drawn_labels_not_the_roster` calls the real closure
and the prescribed erasure mutation is pinned against it rather than against a hand-built proxy.

## No sentence claims this slice unblocks a config

The six-and-three counts (`no-remaining-core-side-blocker` / `executable`) are untouched by every
task in this batch — `E-STATS-NULLTEST-UNSUPPORTED` stays alive throughout, gating every declared
`null_test` at `validate` until task 21. Every test in this batch calling into `validate` asserts
its own code **alongside** that refusal, never in place of it.

## Concerns for the controller

1. The Fixture C2 disagreement above (spec-defects.md entry appended, unowned).
2. Tasks 19 and 20's `cli.py` wiring (`_resolved_null_test`, the `command_run` threading, `null_fns`)
   is unexercised by any real `run` — by construction, since `validate` gates `run` until task 21 and
   this batch does not touch that refusal. Both tasks' briefs name this explicitly ("re-verified by
   `run` in task 25, named there"); flagging it again here so the controller doesn't read the green
   suite as end-to-end coverage.
3. `docs/reference.md` § Reporting strata gained one paragraph (task 20 step 4b, beside task 24's
   existing sentence on the same call site, per the brief's instruction) and § Warnings gained a row
   for `W-STATS-NULLTEST-FAMILY` (task 17+10's task 10 half); mechanical pass (anchors, trailing
   whitespace, table column counts) checked by hand on both edits, no automated checker run.
