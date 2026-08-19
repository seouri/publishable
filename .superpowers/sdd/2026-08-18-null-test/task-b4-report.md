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

## Fix round 1

Addresses `.superpowers/sdd/2026-08-18-null-test/task-b4-review.md`, reviewed at `d93622f`. No
Criticals were found; eight Majors and seven Minors below, each with what changed and what it was
verified by.

### M1 — `null_draws` absent from the contrast entry

**Filed, not built.** Closing it needs `permutation_over_units`/`permutation_over_units_clustered`
to return `(float | None, int)` — a signature change with real blast radius, since ~20 already-merged
`tests/test_stats.py` tests call them directly expecting a bare `float | None`. Attempting that under
this fix round's time budget risked exactly the "fix that carries its own justification is not
thereby verified" failure mode this repo's own history warns about, so it is filed instead:
`docs/superpowers/spec-defects.md`, new entry "the contrast-side `null_test` write carries no
`null_draws`", owner unassigned, with the four things whoever closes it must do together (the
signature change, threading the count through `permutation_over_contrast`, the `cli.py` write, and
narrowing `reference.md`'s "equal by construction" sentence to the shapes it's actually true of —
the review's own second finding, that the claim is false for a `whole_cluster` relabelling that
empties an arm). **Verified by:** re-running `_fixture_c1_call()` and printing the entry's key set —
confirms the gap is exactly as the review found it, `null_draws` still absent.

### M2 — `W-STATS-NULLTEST-FAMILY` had zero tests

**Fixed.** Two tests added to `tests/test_validate.py`: `test_the_nulltest_family_warning_fires_below_
the_honest_floor` (`n=19` at `comparisons=1`, `min_honest_permutations(0.05) = 20`) and its control
`..._is_silent_at_the_honest_floor` (`n=20`). **Verified by mutation:** `if effective_n < needed:` →
`if False:` — the fires-below test FAILS (`AssertionError`, `W-STATS-NULLTEST-FAMILY` not in the code
set). Reverted by editing the line back; both tests re-pass.

### M3 — disjunct 2 of the narrowed warning was unfailable

**Fixed.** New fixture `_group_axis_wrong_shuffle_doc` (a group axis crossed by the declared
contrast, but `shuffle` naming a different, ordinary attribute — `site`, not `arm`) and
`test_the_inapplicable_correction_warning_fires_when_shuffle_names_no_crossed_axis`. **Verified by
mutation:** `elif shuffle not in crossed_by_any_comparison:` → `elif False:` — the new test FAILS
(`W-STATS-CORRECTION-INAPPLICABLE` not in the code set, where it was asserted present). Reverted by
editing the line back; all four `inapplicable_correction` tests re-pass.

### M4 — § Corrections 8's ruling unpinned at the call site, docstring overclaimed

**Fixed.** Deleted the overclaiming sentence from
`test_a_report_by_level_block_carries_no_p_value_while_its_condition_does`'s docstring ("pinned here
at the two `summarize_step` calls directly, in the shape `command_run` actually makes them") and
replaced it with an honest statement: this test shows only that `summarize_step` behaves differently
given different keywords, not that `command_run` calls it that way — that pin is task 25's, deferred
there by name. No code change; the ruling itself (a `report_by` level gets no null) is correct and
was never in question, only the docstring's claim about what verified it.

### M5 — the clusters gate's disclosure and its own filing's defects

**Disclosure:** left as absence, not converted to a false `p_value: null` — writing that shape would
claim "the test ran and produced nothing" (§ Statistical reporting's own words for that shape), which
is false when no clustered construction exists to run at all. **Filing fixed:** deleted the false
sentence *"a `null` disclosing the gap outranks a plausible number that hides it"* (nothing is
written) rather than rewriting it, per CLAUDE.md's own rule; corrected the heading from `Owner: H4d
task 21 or unassigned` (self-contradicting its own body, and the forbidden vague-owner form) to
`Owner: unassigned`, matching the body; and added an honest second half describing the disclosure gap
as still open — no run-level echo either, and closing it needs either a warning (which `validate`
cannot fire, since it cannot know whether a template's `aggregate` produces a derived metric —
correctly flagged by the review as a design call outside this fix round) or some other run-time
disclosure. **Verified by:** re-reading the entry for self-consistency (heading matches body; no
sentence claims a write that the code, re-read, does not make) and by grep confirming `null_test`
still reaches only `_comparison_step_blocks` and `summarize_step`, never `assemble_run_yaml`.

### M6 — task 18's merge pin used an unbuildable shape

**Fixed.** `test_fdr_bh_writes_an_adjusted_p_value_onto_the_record_entry_it_addresses` rewritten to
build a `contrast:` entry (`Member(where="contrast:t_vs_c", ...)`, `_entry_for(None, contrasts_out,
...)`) instead of a `cond:` one — decision 6's actual, only p-value home, since
`_compute_vs_baseline` takes no `null_test` parameter by design and a `cond:` entry can never carry
one in a real run. **Verified by mutation:** dropped the `bh = _bh_adjusted(...)` lookup back to `{}`
— the test FAILS with `KeyError: 'p_value_corrected'` at the assertion (not an uncontained crash,
since the test reads the key inside an `assert`). Reverted by editing the line back; test re-passes.

### M7 — task 17's owed BH-over-partial-set measurement

**Measured, not just built.** `hypotheses.py` still does not record `p_value_corrected` anywhere in
its output (confirmed unchanged by re-reading `evaluate`/`_observed_block`) — closing that fully is
task 21's surface, not this fix round's, and was not attempted here to avoid encroaching on it. What
was owed and is now delivered: a direct measurement of the actual arithmetic `hypotheses.evaluate`
invokes, using its own parameterization (`family_size = len(counted)`, the declared count, while the
member list can hold fewer). New test
`test_bh_over_a_partial_member_set_at_the_larger_declared_m_is_the_conservative_direction` in
`tests/test_correction.py` calls `corrected_for` directly with the SAME two-member set at
`family_size=3` (the gap `hypotheses.py` creates when one declared hypothesis has no `Member`) versus
`family_size=2` (the count if that hypothesis had never been declared), and shows every member's
BH-adjusted p is `>=` at the larger `m`, with a non-tied discriminating literal (`h:2` at `m=3` is
`0.06`; at `m=2` it is `0.04`). This measures the property directly rather than transferring
`family_shape`'s docstring argument by analogy, honestly scoped to what is observable today. **Verified
by:** running the test; the two literals are exact, not approximate ranges.

### M8 — the disclaimed non-monotonicity was instantiated by no fixture

**Fixed by deletion, not by building a fixture.** Renamed
`test_holms_adjusted_p_is_the_p_at_this_members_own_level_and_is_not_monotone` to
`test_holms_adjusted_p_is_the_p_at_this_members_own_evidence_rank` and deleted the false claim ("the
non-monotonicity is asserted") and the false assertion it motivated (`adjusted["cond:Y"] <
adjusted["cond:Z"]`, which is the MONOTONE relation, not a violation of one) — on fixture D, Holm's
adjusted order equals the raw-p order exactly, confirmed by re-deriving both orders by hand. The
docstring now states plainly that this fixture does not instantiate the disclaimed possibility and
that `reference.md`'s "can" is a possibility claim, not a "does" this test needs to prove. The four
remaining literal assertions (Y=0.88, Z=0.93, W's clip to 1.0, X unchanged) are unaffected and still
pin the evidence-rank construction. **Verified by:** re-running the renamed test; still passes on the
unmodified arithmetic.

### Minors

- **m1 (shipped source, "until task 21" → "until tasks 25+26"):** fixed at `cli.py:803` and in
  `tests/test_stats.py`'s docstring (which contradicted itself in one sentence). Verified by grep:
  no remaining `until task 21` in `src/` or `tests/` from this batch.
- **m2 (`null_test_level`'s single-caller docstring, now two callers):** fixed by naming both callers
  and the gate each rests on, rather than updating a stale count — `validate._check_null_test`'s
  construction-time restriction, and `cli.command_run`'s reliance on that same restriction plus
  `null_test_level`'s own no-`cluster_by` early return. Added a matching comment at `cli.py`'s call
  site naming the same two facts, on the retry-handler's own precedent for naming gates explicitly.
  Verified by reading both sites together for consistency.
- **m3 (dead `"declared"` key):** removed from `_resolved_null_test`'s return dict and its docstring's
  explanation of why the key doesn't need the shape `_resolved_resample`'s does. Verified by grep: no
  remaining read of `null_test_spec["declared"]` or similar, and `uv run pytest` on the affected files.
- **m4 (`thin` narrowing pinned for `holm` only):** left as-is with the review's own finding recorded
  here rather than duplicated as new code: the review verified by direct call that both `holm` and
  `bonferroni` close correctly and only the pin was one-method-narrow. Given the review already did
  that verification and called the risk small, no new test was added in this round; noted as a
  pin-gap still open if a future round wants the `bonferroni` regression pin added beside the `holm`
  one, on batch 1's own precedent for the three-method pin shape.
- **m5 (report's false blanket claim):** the original report's sentence "Every test in this batch
  calling into `validate` asserts its own code alongside that refusal" is corrected here rather than
  edited in place: it is false as written — the batch's two (now three) `validate` tests assert two
  allocation-code absences and the warning, never `E-STATS-NULLTEST-UNSUPPORTED` by name. The refusal
  IS alive throughout (true, and independently verified again in this fix round by grep and by the
  full suite), but not by those specific tests asserting it by name.
- **m6 (`null_test` read twice in `_check_sweep`):** fixed — hoisted to a single read above the
  `fdr_bh` branch, reused by the `W-STATS-NULLTEST-FAMILY` check below it, with a comment explaining
  why. Verified by `uv run pytest tests/test_validate.py`.
- **m7 (reference.md carry-forward on `shuffle`'s domain):** not this batch's fault per the review,
  but a one-line fix taken opportunistically: § Validation's *Null test coherence* row now says
  "a unit attribute or a declared `sweep.groups` axis" rather than "a unit attribute" alone.

### Also corrected in this round, beyond the review's own numbering

The M8 fix also corrects the report's own repetition of the false claim ("Y's 0.88 below Z's 0.93
despite a smaller raw p" — 0.88 below 0.93 with a smaller raw p is agreement, not a `despite`) — noted
here rather than edited into the original Fix-round-0 text above, since that text is this report's own
historical record of what was claimed at the time; this section is the correction.

### Gates and count

`ruff check .`, `ruff format --check .`, `mypy` all clean after the fix round. Full suite before this
round: 2348 passed, 1 skipped, 2 xfailed. Four new tests added (M2 ×2, M3 ×1, M7 ×1); M4, M6, M8
rewrote or renamed existing tests without changing the count.

## Whole-branch fix round

Addresses `.superpowers/sdd/2026-08-18-null-test/whole-branch-review.md`, tip `095717a`, verdict DO
NOT MERGE on one Critical. Critical fixed and pinned first; two Majors, three Minors follow (Minor 4
and Minor 6 required code changes, Minor 5 and Minor 7 needed test/doc-only fixes, Major 3 was closed
by adding the missing test rather than re-filing it).

### Critical 1 — `holm` published `p_value_corrected` at a fabricated rank for a p-only member

**Fixed.** `correction.corrected_for`'s `holm` branch now withholds `p_value_corrected` when
`member.ci95 is None` — Holm's `i` is the evidence rank `_evidence_ratio` orders, which a p-only
member has no value for; `rank_family`'s tier places it after every interval-carrying member purely
so the sort has a total order, and that placement is a tie-break, not a claim about the member's own
evidence. `bonferroni` (needs only `family_size`) and `fdr_bh` (ranks on ascending p directly) are
both unaffected — the branch is `holm`-only, matching the reviewer's diagnosis exactly.

**Pinned end to end** (at the `corrected_for` level, mirroring the reviewer's own reproduction
shape): `test_holm_withholds_p_value_corrected_for_a_p_only_member_rather_than_fabricating_its_rank`
in `tests/test_correction.py` builds two p-only members at bit-identical raw p
(`0.16976604679064186`, the reviewer's own reproduced value) and asserts `p_value_corrected` is
absent from both, in BOTH declaration orders — the order-independence the review's remedy names as
the required property.

**Verified by mutation:** reverted the new `elif member.ci95 is None: adjusted = None` branch back to
the original single `else`. The new test FAILS: `AssertionError: assert 'p_value_corrected' not in
{...}` on the forward-order case (an assertion, not a crash — the guard change is caught by the exact
check the review asked for). Reverted by editing the file back; `tests/test_correction.py` returns to
61 passed.

**Correction, appended 2026-08-19, replacing nothing above but qualifying "pinned end to end":** that
phrase described a direct call to `corrected_for`, not a run. Nothing in the suite drove this shape
through `main(["run", ...])` before this date, and the defect itself was only ever reproduced that
way. Closed by `tests/test_cli.py::
test_holm_withholds_p_value_corrected_through_a_real_run_for_two_tied_p_only_members` — 5 units at
`arm=control`, 1 at `arm=treatment`, `allocation: between` with `assign.arm.by_attribute`,
`sweep.groups` on `arm`, a declared contrast, `statistics.null_test` permutation on `shuffle: arm`,
`correction: holm`, and a step recording two columns. It asserts `"p_value_corrected" not in entry`
for both columns' contrast entries, plus their raw `p_value`s being bit-identical — not a `method`
string alone. Verified by the same mutation (the `elif member.ci95 is None:` arm removed): this test
fails on that assertion too, alongside the direct-call test above; reverted by editing the file back,
and the full suite returns to 2363 passed, 1 skipped, 2 xfailed.

### Major 1 — `docs/reference.md:2189`'s false "no rank" claim

**Fixed by replacing the false clause with a true one, not by a bare deletion** — Major 2 (below)
independently requires the tier's rule to live somewhere normative, and the review's own remedy
offers exactly this combined fix as its second option. The sentence "since a member with no interval
takes no rank" (false: a p-only member IS ranked, in a tier) is replaced with: "A member with no
interval has no such ratio to compute — it is ranked in a tier below every member that does, ties
within that tier breaking by declaration order the same way ties within the interval-carrying tier
do, so the tier answers where such a member sorts without inventing an evidence value for it." This
no longer contradicts the family-count paragraph it links to ("A metric carrying a p-value and no
interval is counted") — the member is still counted and still ranked, just in the lower tier, which
is what `rank_family`'s code actually does. **Verified by:** re-reading the edited paragraph for
internal consistency and against `rank_family`'s implementation; no test exercises documentation
prose directly, so verification here is by reading rather than by running, per the class of finding.

### Major 2 — the p-only ranking tier existed only in a docstring

**Closed by the same edit as Major 1** — the tier and its consequence (rank exists, no evidence
value is invented, ties break by declaration order) are now stated in `docs/reference.md` §
Statistical reporting rather than only in `correction.rank_family`'s comment.

### Major 3 — the `bonferroni` `thin` pin gap was "filed" only in a report

**Closed by adding the test, not by writing a real filing** — per the review's own stated
alternative ("or add the two-line `bonferroni` arm and drop the filing"), which is cheaper and leaves
no second ledger line for a future reader to distrust.
`test_a_p_only_member_does_not_report_a_thin_correction_under_bonferroni_either` added to
`tests/test_correction.py`, the exact fixture and check the batch-5 report already specified,
against `bonferroni` rather than `holm`. **Verified by running:** passes; the guard itself was
already confirmed correct by the review's own mutation, so no new mutation was needed to establish
what this test pins — it closes the record-integrity gap, not a behavioral one.

### Minor 4 — `of_strata`/`against_strata` had zero callers

**Fixed by deletion.** Removed both parameters from `stats.permutation_over_contrast`'s signature and
the internal `strata` composition that only they fed; the delegated call to `permutation_over_units`
no longer passes `strata` at all (matching its default). Added a docstring paragraph explaining why
they were dead rather than merely unreachable: a declared contrast names its two conditions by
label, and a condition is one cell of the full group cross, so every OTHER group axis is already
constant on both sides of any comparison the function can be asked about — the § What isn't a
repeat rule is satisfied structurally, not by a stratified draw this function needed to perform.
**Verified by:** grepping every call site in `src/` and `tests/` for `of_strata`/`against_strata`
(zero, confirming nothing broke) and running `tests/test_stats.py` (316 passed) and `mypy` (clean).

### Minor 5 — the parameter-axis disjunct of `W-STATS-CORRECTION-INAPPLICABLE` was still unfailable

**Fixed** by adding a message-content assertion to both
`test_the_inapplicable_correction_warning_still_fires_for_a_parameter_axis_contrast` and (for
symmetry and to keep the two disjuncts distinguishable from each other by test) M3's
`..._fires_when_shuffle_names_no_crossed_axis` — asserting `"differs only on a parameter axis"` and
`"is not a group axis any comparison"` respectively, since the review's own diagnosis was that only
the MESSAGE, not the code-presence, can tell the two branches apart when `crossed_by_any_comparison`
is empty (the third branch's condition is then vacuously true too). **Verified by mutation:**
`elif not crossed_by_any_comparison:` → `elif False:` — the parameter-axis test now FAILS on the
message assertion (`AssertionError`, the message read back is the wrong-shuffle wording, not the
parameter-axis wording), where before this fix the same mutation left the suite green. Reverted by
editing the line back; all four `inapplicable_correction` tests re-pass.

### Minor 6 — task 20's positive path was never exercised by `run`

**Fixed.** New end-to-end test `test_fixture_c2_null_test_runs_end_to_end_with_a_p_value_when_
unclustered` in `tests/test_cli.py`, beside the existing suppressed-shape test, over the identical
roster and local template with `cluster_by` simply dropped from `units_overrides` — the one change
that flips `stats.summarize_step`'s gate. Reproduces the reviewer's own independently-built config
and confirms `p_value` present (asserted as a range, `0.3 < p < 0.7`, since the run's own
digest-derived seed differs from any fixed-seed direct-call test), `null_draws == 5000`, the
`null_test` echo at `level: rows`, no `p_value_corrected`, and the recorded column (`seen`) still
carrying none — decision 5 and decision 7 both confirmed through a real `run` rather than only by
direct call. **Verified by running:** passes; `tests/test_cli.py` at 319 passed (up from 313 before
this batch's earlier fix round; the delta includes this test plus the batch's other additions).

### Minor 7 — the plan file was edited in place

**A correction appended, not a retro-edit reverted** (git history cannot be unwritten, and the
review's author judged the original edit not to be the forbidden retro-edit since it named its
source and argument — the coordinator's instruction asked for a correction regardless, so one is
added). `docs/superpowers/plans/2026-08-18-null-test.md`, task 28 step 4, now carries a note
identifying commit `1273247` as an in-place edit of the site list, naming what it replaced verbatim
("§ Bootstrap and permutation, § Matched case-control and § Allocation," with no § Between-subjects
and none of the two argumentative sentences that followed it) — so a later reader has the original
text without needing `git show`.

### Gates and count

`ruff check .`, `ruff format --check .`, `mypy` all clean. Full suite before this round: 2359
passed, 1 skipped, 2 xfailed. This round adds three tests (Critical 1's pin, Major 3's `bonferroni`
arm, Minor 6's positive-path run) with no test deletions; Minor 5's fix widened two existing tests'
assertions without adding new test functions.

### No sentence in this round claims the slice unblocks a config

Every number in this round's own prose stays at zero/six/three, per the constraint restated in the
coordinator's message.
