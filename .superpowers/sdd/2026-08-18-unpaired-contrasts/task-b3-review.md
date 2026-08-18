# Batch 3 review: tasks 9 (adopted), 10, 11, 12, 13 (+17a)

Reviewed at `908d273` on branch `h4c-unpaired-contrasts`, 2026-08-18. Baseline reproduced in the
foreground: **2252 passed, 1 skipped, 2 xfailed** (125.8 s); `ruff check` clean, `ruff format --check`
**80 files already formatted**, `mypy` **45 source files**. Five mutations run against the full,
unfiltered suite; every one reverted by editing the file back and the suite re-run to the same
baseline. **Tree clean at the end** (`git status --short` empty, `__pycache__` cleared).

## Verdicts

**Spec compliance: PASS.** Every ruling in
`docs/superpowers/specs/2026-08-18-unpaired-contrasts-design.md` and its § Corrections against the code
that this batch owns is honoured, and no ruling is quietly widened.

- **Decision 2 — a third evidence *kind*, not a fourth modifier.** Verified by *building every illegal
  combination in-process*: `sides` beside `pool` → `"…not pool, sides"`, beside `diffs` → `"…not diffs,
  sides"`, all three → `"…not pool, diffs, sides"`, none → `"none of the three"`; `weights` beside
  `sides` and `clusters` beside `sides` each raise **with and without** a `ci95`, because both modifier
  checks precede the exactly-one rule's early return. The only combination that constructs is
  `sides`+`pool`/`sides`+`diffs` **with `ci95=None`**, which is the pre-existing `pool`/`diffs`
  exemption unchanged, not a new hole. `correction.py:131-216` (`Member.__post_init__`).
- **Decision 2 / correction 4 — five *t* arms, six return paths, each returning the construction it
  claims.** Verified by direct call: each of the six member shapes' bounds are **bit-equal** to a
  direct call of `welch_t_over_units_clustered`, `welch_t_over_units`, `paired_t_over_units_clustered`,
  `weighted_paired_t_over_units`, `paired_t_over_units` and `interval_at` at `confidence=0.975`
  (`correction.py:347-384`, the `sides`/`diffs`/`pool` arms).
- **The corrected bound MOVES for the unpaired cells** — H4b-1's silently-unpinned α is not repeated.
  Fixture A's `sides` member gives half-width 3.039125537798091 at level 0.05 and 3.5578500187538484 at
  0.025, and the latter is exactly the literal `test_an_unpaired_members_corrected_bound_is_the_welch_form_at_a_smaller_alpha`
  asserts. Verified by direct computation.
- **Arm order's pin exists rather than being claimed.** `test_a_member_carries_exactly_one_of_pool_diffs_and_sides`
  (`tests/test_correction.py:94-119`) asserts all three illegal pairs plus the empty case raise, which
  is what makes correction 10's unobservability argument sound.
- **Decision 5 — `n_paired` absent, not null, and written in place.** `n_of`/`n_against` occupy the
  same slot between `method` and `ci95` in both new record literals (`cli.py:1041-1045`, `1226-1228`),
  so no existing record's key order moved; `test_a_paired_contrast_entry_still_grows_no_unpaired_key`
  and `test_an_unpaired_contrast_records_its_two_side_counts_and_no_n_paired` pin both directions, each
  beside a presence that must report. The pin decision 5 says must survive —
  `n_paired == 0` for a *paired* contrast over an empty stratum (`tests/test_cli.py:4387`) — is
  untouched and passing.
- **Decision 7 — one predicate, two callers, and task 9's restored body is correct.**
  `crossed_group_axes = differing_axes(of, against) ∩ (of.selectors | against.selectors)`
  (`contrasts.py:119-153`) is exactly § Allocation's pairing table: `selectors` is populated from
  `sweep.selector_paths`, whose `SELECTOR_MODES` is `groups` alone (`sweep.py:496-521` and `sweep.py:1016`), so
  "any `groups` axis ⇒ unpaired, parameter axes only ⇒ paired" is what the expression computes.
  `validate._check_sweep` and `cli._comparison_step_blocks` both call it and nothing recomputes it.
- **Decision 6's interim reading is right.** The `reported_n` placeholder fires iff **either** side is
  below the floor (`min(...)`), which is decision 6's rule, not a weaker one.
- **`E-DATA-ALLOCATION-CONTRAST` is alive**, its **exact-set** assertion at `tests/test_validate.py:8115`
  unchanged and passing; the three new weighted-refusal tests assert **alongside** it and attribute
  their refusals (`E-DATA-ALLOCATION-WITHIN-ARMS` / `-NO-ARMS` asserted absent). Every new
  `_comparison_step_blocks` test routes by **direct call**. **No sentence anywhere in the batch claims
  a config is unblocked** — swept the added lines for `unblock`, `executable`, `newly execut`, "three of
  nine", "six with no": zero hits. Zero, six and three are unmoved.
- **`W-STATS-CONTRAST-THIN`'s second emit at `validate` was left alone, not half-fixed.** The only
  `validate.py` changes in the batch are the import line and the `_check_sweep` guard; the message at
  `validate.py:5365` still reads as it did, and correction 1 assigns it to task 16.
- **Task 17a replaced rather than deleted.** `test_a_contrast_entrys_paired_flag_is_written_unconditionally_at_every_branch`
  is gone, the `inspect` import with it, and `test_a_contrast_entrys_paired_flag_is_derived_at_every_branch`
  (`tests/test_cli.py:4020`) asserts **both** answers in one test. All four `paired` cells are
  pinned: unpaired-recorded and paired-recorded there, derived-unpaired by
  `test_a_derived_metrics_unpaired_contrast_also_derives_its_flag`, derived-paired by
  `test_an_unpaired_pass_leaves_a_summary_estimate_alone`'s `block["score"]["paired"] is True`.
- **`n_paired`'s readers, enumerated by reading then confirmed by grep**: `src/` contains *writes only*
  — `cli.py:1041`, `cli.py:1185` — plus prose. Nothing in `attrition`, `_entry_for`, `artifacts.py`,
  `hypotheses.py` or the `observed` path reads the key, so absence costs no reader. Every `tests/`
  reader is on a paired fixture.
- **Task 13's regression obligation holds and still discriminates.** The batch-1 six-cell pin
  `test_every_paired_contrast_cell_is_unmoved_across_this_branch` (raw `ci95` **and**
  `ci95_corrected` per cell) passes, and mutating `_corrected_bounds`' clustered `diffs` arm to the
  unclustered construction failed `[clustered_t]` plus two others (3 failed / 2249 passed). Verified by
  running.

**Task quality: PASS WITH FINDINGS.** The code is right; two of its *stated guarantees* are not, and
one arm of the new dispatch is pinned only by an accident of fixture geometry. All three are one-line
remedies. Nothing here is a correctness defect in shipped behaviour, and nothing is left applied.

## Findings

### Major 1 — a test docstring claims a guarantee its body does not make, and the mutation proves it

`tests/test_correction.py:248`, `test_the_five_t_arms_are_each_reached_by_one_member_shape`. Its
docstring says *"every arm is asserted by the construction its `method` names, read off the raw
interval each arm rebuilds"* and that the failure it guards is *"an unpaired clustered member taking
the plain Welch arm gives a plausible number 3.5 times too narrow"*. The body reads no `.method`,
rebuilds no raw interval, and asserts only `all(v is not None)` plus `len({tuple(v)}) == 6`.

**Verified by running** task 12's prescribed mutation 1 (`_corrected_bounds`' `sides` branch collapsed
to always call `welch_t_over_units`) against the full suite: **1 failed, 2251 passed** — and the single
failure was `test_an_unpaired_clustered_members_corrected_bound_reads_its_own_two_cluster_counts`
(11.484952890215286 against an expected 48.58511662986156). **This test stayed green under exactly the
mutation its docstring names**, because collapsing the clustered arm onto the plain one changes that
arm's bound without colliding with any other arm's. A distinctness assertion catches *collisions*, not
*neighbour fall-through in general* — confirmed in the other direction by the
paired-clustered-arm mutation in the table below, where collapsing `diffs_clustered` onto
`diffs_plain` *does* collide and this test does fail.

Two aggravations, read rather than run: both `sides` shapes in the fixture are **3 against 3**, which
is the one geometry § The discriminating fixtures' constraint 1 forbids ("unequal per-side sizes, or
pooled and Welch coincide algebraically") — so a pooled-variance mutant on `sides_plain` is invisible
there too; and the docstring's "3.5 times too narrow" is a number about fixture B, not about this
fixture. The claim was prescribed verbatim by `task-12-brief.md:126-137`, which does not excuse it —
this is the third false docstring claim on this slice, all three brief-prescribed.

**Remedy (recommended, not applied):** delete the two sentences that overclaim, or give the fixture
unequal per-side sizes and assert each `sides` arm against a direct call of the construction it names.
The distinctness assertion itself is worth keeping; it is just narrower than advertised.

### Major 2 — the clustered `sides` arm's centre is pinned only by a fixture-length crash

`tests/test_correction.py:192`. The plain unpaired test asserts the centre
(`(bounds[0]+bounds[1])/2 == approx(10.0)`); the clustered one asserts **only the half-width**.

**Verified by running** task 12's prescribed mutation 4 (`member.sides.of` / `member.sides.against`
swapped in the **clustered** call only): **1 failed, 2251 passed**, and the failure was a
`ValueError: zip() argument 2 is shorter than argument 1` raised inside `stats._cr1_variance`
(`stats.py:550`) — i.e. caught because fixture B's sides are 9 and 12 long, not by any assertion about
the value. `test_the_five_t_arms_…`, whose 3-vs-3 `sides_clustered` shape *would* reach the
arithmetic, stayed green. So a sign-flipped clustered unpaired `ci95_corrected` beside a correct raw
interval is not pinned by an assertion anywhere.

This also **adjudicates the implementer's disagreement 5 in their favour, and faults the brief**: the
brief's reasoning — *"the distinctness assertion compares `tuple(v)` pairs, which DO move when the
centre flips, so it discriminates"* — is wrong, because distinctness is insensitive to movement that
causes no collision. The implementer was right to record the deviation rather than force the named test
to fail.

**Remedy (recommended, not applied):** one line in the clustered test —
`assert (bounds[0] + bounds[1]) / 2 == pytest.approx(12.833333333333332)`.

### Minor 1 — a docstring claim about the fixtures that the fixtures contradict

`src/publishable/correction.py:53-67`, `UnpairedEvidence.__post_init__`: *"the two sides here are
deliberately different lengths in every fixture"*. Verified by reading: `test_a_member_carries_exactly_one_of_pool_diffs_and_sides`
and `test_a_member_may_not_carry_a_modifier_beside_sides` both use 2-against-2, and both `sides` shapes
in the arms test use 3-against-3. The *reason* the sentence gives (equal sizes make the pooled and
Welch SEs algebraically identical) is true and worth keeping; the claim about "every fixture" is false
and is the kind that decays further. Prescribed by `task-11-brief.md:196-201` verbatim. **Remedy: delete the
clause about the fixtures, keep the domain reason** — a deletion cannot invent.

### Minor 2 — a production comment asserting a property the code does not guarantee

`src/publishable/cli.py:1280-1282`: *"Per side once the sides are disjoint, and Welch's df reads both.
**Two integers that cannot coincide**, which is what makes them a stronger discriminator than any float
here."* Nothing prevents `n_clusters_of == n_clusters_against` — two arms with equal cluster counts is
an ordinary roster. The spec and the test both qualify this correctly ("two integers that cannot
coincide **on this fixture**, 3 against 4"); the production comment dropped the qualifier and states it
as a property of the keys. It is also a comment about a *test fixture's* discriminating power sitting
in production code. **Remedy: drop the sentence, or restore the fixture qualifier.**

### Minor 3 — two prose claims this batch falsified and did not re-read

Both in `src/publishable/cli.py`, both outside the hunks the tasks edited, both now describing one arm
as if it described the function:

- `:853-858` — *"Both constructions read `n_paired` off `stats.paired_keys` — the intersection of the
  two conditions' completed units…"*. After task 10 the unpaired arm reads `stats.unpaired_keys` and
  records no `n_paired`. The new paragraphs at `:888-902` state the unpaired behaviour correctly, so a
  reader gets both a true and a false account of the same fact. The whole paragraph at `:829-858`
  ("A recorded column takes `paired_t_over_units`… A derived metric… takes `paired_delta_of_derived`")
  needs the same quantifier narrowing rather than an enumeration.
- `:1293-1302` — *"`Member` requires exactly one of `pool`/`diffs` wherever there is an interval to
  correct"*. Task 11 made it three, and this comment is the `cli`-side mirror of the rule it re-argued
  in `correction.py`. **Remedy: narrow both quantifiers** (`CLAUDE.md`'s "sweep for the claim, not for
  the file the claim was first noticed in" — the `Member` docstring was swept, its mirror was not).

### Minor 4 — a caller enumeration re-introduced in the sibling of the one just deleted

`src/publishable/contrasts.py:130-134`: `crossed_group_axes`' docstring names its two callers
(*"`validate` refuses `weight_by` beside a non-empty answer, and `cli._comparison_step_blocks` derives
the `paired`…"*) in the same commit range whose `test_differing_axes_docstring_names_no_caller` pins
`"_comparison_step_blocks" not in doc` for the neighbouring function. Both claims here stay **true**
past task 18 (the weight refusal survives it), and the sentence is decision 7's rationale rather than
an incidental list, so this is a note rather than a defect — but it is the same maintenance obligation
the slice just paid to delete one line up, and task 19's sweep should read it rather than grep past it.

### Minor 5 — the thin-warning message still names a key the entry does not carry

`src/publishable/cli.py:1366` emits `"… metric 'm': n_paired {reported_n} is below …"` on an unpaired
entry that carries no `n_paired`. **Owned by task 16** in writing (the comment above it says so, and
correction 1 assigns the `validate`-side twin there), and unreachable through `run` until task 18, so
it is correctly deferred rather than half-fixed. Recorded so task 16 is not read as covering only the
`validate` site.

## The five brief/code disagreements, adjudicated

1. **`min_reported_n` placeholder / `UnboundLocalError` — genuine, and the replacement is right.**
   Verified by running: restoring the brief's literal `len(col_keys) if is_paired else …` fails
   `test_a_derived_key_collision_under_a_cluster_still_carries_the_intersection_facts` with
   `UnboundLocalError: cannot access local variable 'col_keys'` at `cli.py:1354`. The deviation
   `(len(base_keys) if is_derived else len(col_keys)) if is_paired else min(...)` is not merely
   non-crashing: it equals the record's own `n_paired` on both paired arms and implements decision 6's
   either-side rule on the unpaired one. **Accepted.**
2. **F821 in the record literal — genuine, not a misdiagnosis.** I did not accept "confirmed with a
   minimal repro": I put the brief's ternary back and ran `uv run ruff check .`, which reports
   `F821 Undefined name col_keys` at `cli.py:1041:76`. The simplification to `len(base_keys)` is
   correct on that arm (`is_derived` is invariantly true there) and the inline comment explains it
   without overclaiming. **Accepted.**
3. **The hardcoded `'"paired": True'` count updated from 2 to 4 — accepted.** The test was a
   source-text pin batch 1 knew was scope-limited, task 10 legitimately added two literal sites, and
   task 13 then replaced the whole test with the behavioural pin its predecessor's own docstring said
   it could not be. Updating rather than deleting mid-batch kept the branch green for the right reason.
4. **Task 12 mutation 1's predicted magnitude was wrong; the catch is still the right catch.**
   Measured 11.484952890215286, as the report says, against the brief's "near 41.9". The brief's number
   is what you get by changing only the **df** (34.148 × 1.2276 ≈ 41.9) while keeping the clustered
   variance; the mutation drops clustering entirely, so the variance changes too and the IID answer is
   ≈11.5. So the wrong prediction is an arithmetic slip in the brief, **not** a sign that the mutation
   hits something else: it fails on the intended assertion in the intended test, and its ratio is the
   one the spec's fixture-B table predicts for the IID form. Qualitative claim holding is enough
   **here**, because the mutation's target is identifiable from the failing assertion.
5. **Task 12 mutation 4 — qualitative claim holding is NOT enough here.** See Major 2. The named test
   could not have failed (a distinctness assertion is blind to a collision-free move), and what caught
   the mutation was a `zip()` length crash arising from the fixture's asymmetry rather than any check of
   the construction. The implementer's record is accurate and the brief's reasoning is what was wrong,
   but the honest conclusion is that **the clustered arm's centre is unpinned**, which the report does
   not draw.

## Mutations re-run here (all against the full, unfiltered suite, foreground)

| Mutation | Result | Reading |
|---|---|---|
| Task 12 m1 — `sides` clustered arm dropped | 1 failed / 2251 passed; `…reads_its_own_two_cluster_counts` on the ratio | Discriminating; **and** it exposed Major 1 |
| Task 12 m4 — `of`/`against` swapped in the clustered call | 1 failed / 2251 passed, via `zip()` `ValueError` in `stats.py:550` | Major 2: caught by a crash, not by a check |
| Task 13 m2 — derived branch's `"paired": is_paired` → `True` | 1 failed / 2251 passed; `test_a_derived_metrics_unpaired_contrast_also_derives_its_flag` on `assert True is False` | Discriminating, exactly the named test |
| Task 9 m3 — the intersection dropped from `crossed_group_axes` | **126 failed** / 2126 passed | The restored body is load-bearing. The report's 90 was measured at task 9's commit, before tasks 10–13 gave the predicate a second caller; the growth is expected, and both numbers are genuine |
| `_corrected_bounds`' paired clustered arm → unclustered | 3 failed; `test_every_paired_contrast_cell_is_unmoved_across_this_branch[clustered_t]`, `…_five_t_arms_…`, `…_clustered_members_corrected_bound_…` | Batch 1's six-cell guard pin still discriminates at its own α and df |

Each reverted by editing the file back, `__pycache__` cleared, and the suite re-run to
**2252 passed, 1 skipped, 2 xfailed**.

## Not checked

- **Task 14/15/16/18 surfaces**, deliberately: no `method` string is selected on the unpaired arm yet
  (`interval = None`, `cohens_d = None`), the derived-unpaired suppression has no guard of its own, and
  nothing reaches these paths through `run`. Whether the record shape is *correct end to end* is not
  answerable at this commit and is not this batch's claim.
- **`unpaired_percentile_of_sides` and the constructions themselves** (batch 2's), beyond confirming
  the two `welch_*` forms are what `_corrected_bounds` calls and that `unpaired_keys`' claim about the
  sorted-keys contract is true (it is: `_draw_pools` raises at `stats.py:1574-1582` when `strata` is given
  and `keys` is unsorted, and `unpaired_percentile_of_sides` reaches it).
- **The mechanical/cross-document passes in full** — task 22's. I checked the two new `reference.md`
  rows only: 2 cells each matching their tables' headers, `#weighted-samples` and `#expansion-modes`
  resolving, no trailing whitespace, tabs or bare `x` anywhere in the batch's changed files.
