# H4c batch 2 review — tasks 4–8

Reviewed `72e3e67` on `h4c-unpaired-contrasts`, against
`docs/superpowers/specs/2026-08-18-unpaired-contrasts-design.md` including its appended
§ Corrections against the code, the five task briefs, and `CLAUDE.md`.

## The two verdicts

**Spec compliance: PASS.** All four constructions exist with the `method` strings decision 3 fixes,
the df of the unpaired clustered *t* is Welch-Satterthwaite over the two per-side CR1 variances at
`G_s − 1` (decision 4), the degenerate-draw rule across two independent draws is AND (correction 8),
`PairedResample`'s docstring had "paired" **deleted** rather than rewritten (correction 7),
`_cr1_variance` was **extracted** rather than called (correction 2), `E-DATA-ALLOCATION-CONTRAST` is
alive at every one of its sites, every test is a direct call, and no sentence in the diff, the five
commit messages or the report claims a config unblocked. Every fixture literal is right.

**Task quality: PASS WITH RESERVATIONS.** No behavioural defect found: I could not construct or
provoke a wrong number anywhere in the five commits. All three Majors are in **prose and in the
mutation record** — one shipped docstring makes two claims the code falsifies, and two of the
report's mutation outcomes are wrong in a direction that makes the tests look better guarded than
they are. One of those two is the batch's own headline blindness claim, and it does not survive.

## Verified by running, before the findings

- Gates at HEAD, foreground: `ruff check` clean, `ruff format --check` **80 files**, `mypy` **45
  source files**, `pytest` **2227 passed, 1 skipped, 2 xfailed** — the report's numbers exactly.
- **Every fixture literal recomputed independently** in a standalone script that imports `scipy`
  directly and never imports `publishable`: fixture A's SE √2, df 96/7, correct half-width
  `3.039125537798091` and all four mutant half-widths; the pooled sd `4.705619740571601`, *d*s
  `2.1251185925162073` and the Welch-denominator `7.0710678118654755`; fixture B's per-side CR1
  variances `67.07818930041152`/`1.5879629629629628` at G = 3 and G = 4, SE `8.286504224543332`,
  df `2.0950313633473936` and **half-width `34.14810237373095`**, plus all five rejected readings;
  both Bonferroni ratios; the 2/4/6 CR1 oracle `8.763214143637903`. All reproduced.
- **No test passes under either rejected clustered df.** `min(G) − 1` gives `35.653950021811816`
  and `G_total − 2` gives `21.301137240534675` (note: the review brief labelled `26.371…` as
  `G_total−2`; that number is `G_against − 1`, and `G_total−2` is `21.301…`). The target test asserts
  `pytest.approx(34.14810237373095)` at the default rel 1e-6 and every candidate is >4 % away.
- **Four prescribed mutations re-run against the full, unfiltered suite in the foreground**, each
  checked against the body of the test it names (details in the findings): task 6 mutation 2, task 6
  mutation 3, task 6 mutation 4, task 7 mutation 4 under its literal reading. Each was reverted by
  editing the file back, `__pycache__` cleared, and the file diffed byte-for-byte against a
  pre-mutation copy.
- **Task 4's mutation 4 re-run as well**, precisely because Major 3 shows the report's cross-cell
  attributions unreliable in that region. `(len(values) - 1)` → `len(values)` in `_sample_variance`
  gives **26 failed, 2201 passed**, and `[plain_t]` **is** among them — so that reported outcome is
  sound and Major 3 stays an instance rather than a pattern. It also shows how wide this extraction's
  blast radius is: the weighted, clustered and paired-clustered *t* tests all move with it.

## Findings

### Major 1 — `_sample_variance`'s docstring makes two claims the code falsifies

`src/publishable/stats.py:76` and `:92`.

Line 76: *"The unbiased sample variance, Σ(v − v̄)² / (n − 1) — **the one copy in this module**."*
Line 92: *"`weighted_t_over_units` and `cohens_dz` deliberately do NOT call this: their denominators
are `Σw − Σw²/Σw` and a difference vector's own, **which are different quantities**."*

`cohens_dz` at `src/publishable/stats.py:678` computes
`sum((d - mean) ** 2 for d in diffs) / (len(diffs) - 1)` — a second literal copy of the extracted
expression, and the *same* quantity, not a different one. Only the input vector differs, and the
function is parameterized by its input. **Verified by running:** `cohens_dz(d)` and
`mean / sqrt(_sample_variance(d, mean))` are bit-identical (`1.2620103632966184`) on a five-value
vector. The clause is true of `weighted_t_over_units`, whose denominator really is Kish's; it is
false of `cohens_dz`.

This is the shape `CLAUDE.md` § Habits names first, and it is load-bearing rather than cosmetic: the
justification the extraction rests on is *"two copies is how two intervals over the same data come to
disagree about what the dispersion is"*, and the docstring asserts a uniqueness the module does not
have, 580 lines above the second copy. Per house convention the repair is **deletion** of both
claims, not a rewrite; leaving `cohens_dz` un-rewired is a defensible scope call the brief made and I
am not faulting it.

Both sentences were prescribed **verbatim** in `task-4-brief.md` Step 3. That is where they came from,
and it is not a defence — the code outranks the plan, and six of six implementers on the previous
slice found a real disagreement. Nothing in the report records this one.

### Major 2 — task 6 mutation 2 is not blind; the claim is stale, and the mutation was mis-fixtured

`task-b2-report.md` § Mutation outcomes (task 6) and § Disagreements 3 record the pooled-draw
mutation as *"**PASSED**, contrary to the brief … the 'mutation whose two branches cannot differ'
trap"*.

**Verified by running at HEAD.** I applied exactly that mutation — both per-side comprehensions
replaced by one draw over `of_pools + against_pools`, split at `len(of_keys)` — and the full
unfiltered suite gave **2 failed, 2225 passed, 1 skipped, 2 xfailed**:
`tests/test_stats.py::test_the_unpaired_clustered_percentile_draws_whole_clusters_per_side` and
`::test_the_unpaired_clustered_percentile_is_invariant_to_relabelling`, both through an **uncaught**
`KeyError: 'ag00'` raised at `src/publishable/stats.py:1865` — `unit_table_from_rows`, which sits
*outside* the `try`, so the fault is a hard error rather than a silently thinned pool.

The implementer's arithmetic is right about fixture A and the reported outcome was honest **for the
moment it was taken** — mid task 6, before task 8's clustered tests existed. It is wrong now, and the
report states it in the present tense as a property of the mutation. So this is not the
branches-cannot-differ trap; it is the mis-fixtured case, and the answer to the question the review
brief asks is explicit:

- **A clustered fixture discriminates.** Under clusters each side's drawn key list has *variable*
  length (of: 6–12 rows from 3 cluster draws; against: 8–16 from 4), so a split at the fixed
  `len(of_keys)` = 9 cannot reconstruct either side and cross-contaminates the two key spaces.
- **A stratified fixture does not.** With strata and no clusters the concatenated group order is
  still every `of` stratum then every `against` stratum, and the per-side totals stay exactly 5 and
  25, so the split reproduces both draws bit-for-bit. Blind for the same reason fixture A is.

What the batch actually earned here is the two-mapping signature the spec argued for: the disjoint
key spaces convert this class of mistake into a raise instead of a plausible number. That is worth
recording; "PASSED, blind" is not.

### Major 3 — task 6 mutation 4's recorded outcome names two tests that do not fail

`task-b2-report.md` § Mutation outcomes (task 6): the reversal of `_draw_pools`' unclustered `items`
order *"→ FAIL on the extraction oracle's endpoints and on
`test_cli.py::test_every_paired_contrast_cell_is_unmoved_across_this_branch[plain_t]`/
`[weighted_percentile]`"*.

**Verified by running** the brief's exact mutation (`items = [[key] for key in reversed(keys)]` at
`src/publishable/stats.py`' unclustered branch) against the full unfiltered suite: **7 failed**, and
the seven are `test_cli.py::test_every_paired_contrast_cell_is_unmoved_across_this_branch[weighted_percentile]`,
`test_cli.py::test_the_undeclared_resample_shape_is_pinned_absent_key`,
`test_cli.py::test_the_undeclared_resample_shape_is_pinned_explicit_null`,
`test_cli.py::test_an_unclustered_resampled_contrast_draws_what_it_always_drew`,
`test_stats.py::test_the_unclustered_paired_draw_is_the_same_sequence_it_always_was`,
`test_stats.py::test_the_unpaired_percentile_draws_each_side_independently`, and
`test_stats.py::test_the_unpaired_clustered_percentile_is_not_the_unclustered_one`.

Neither test the report names is among them, and neither *can* be:

- `test_the_extracted_draw_pools_leaves_the_paired_draw_where_it_was` passes `clusters=`, so **its
  endpoint assertion — the only assertion in it that reads a draw — exercises only the clustered
  branch**. Its `ValueError` arm does enter the unclustered branch, but raises on
  `keys != sorted(keys)` before the item order can matter, and its `ContractError` arm is clustered.
  So the test the brief designates as *the* oracle for this extraction cannot see a change to the
  unclustered half of the body it was extracted from, and its own docstring — *"The extraction is
  pure code motion and this is the oracle"* — over-claims. The property is covered, by the two
  pre-existing unclustered-sequence tests above; the claim to be the oracle is what is wrong.
- `[plain_t]` is a `paired_t_over_units` cell (`_H4C_CELLS["plain_t"] = dict(clusters=None)`, no
  `resample_columns`) and never reaches `_draw_pools` at all. It failed under task 4's mutation 4,
  which is presumably where the line came from.

Also worth stating plainly: the brief predicted `[plain_percentile]` **and** `[clustered_percentile]`
must fail, and **neither does** — `plain_percentile`'s pinned endpoints `[4.666…, 8.0]` happen to
survive the reversal. The report noticed only that `weighted_percentile` moved "instead" and called
it *"same property"*. It is the same property with one of the two named cells demonstrably unable to
see it, which is the *"a fixture whose numbers agree with the bug"* shape and deserved a sentence
rather than a parenthesis.

### Minor 4 — two present-tense docstring claims about a type that does not exist

`src/publishable/stats.py:477` (*"`correction.Member` carries them as `UnpairedEvidence`"*) and
`:538` (*"`correction.UnpairedEvidence` carries exactly that pair"*). `grep -rn UnpairedEvidence src/`
returns exactly those two docstring lines and no definition — the type is task 11's. Brief-prescribed
and resolved by the time the branch merges, but false in shipped `src/` today.

### Minor 5 — `_cr1_variance`'s uniqueness claim does not name its exclusion

`src/publishable/stats.py:268`: *"One expression for the cluster-robust variance, and three
callers"*. `weighted_t_over_units_clustered` deliberately keeps its own sandwich (correctly — its
scores carry weights and its bread is `1/Σw`), and this docstring does not say so, where
`_sample_variance`'s attempts to. The "three callers" wording itself is accurate as written: two
direct, one transitive through `t_over_units_clustered`.

### Minor 6 — `t_over_units_clustered`'s surviving floor is now unfalsifiable

`src/publishable/stats.py` — `if n < 2: return None` in `t_over_units_clustered` now returns the same
answer `_cr1_variance`'s own `n < 2` floor would, so no mutation of that guard can fail a test, while
the docstring at `:340` still spends a sentence on it as a *kept* floor and then says *"Both floors
… live in `_cr1_variance`"*. Not false, and `n` is still needed for the mean; noted because a later
reader is likelier to mutate it than to notice it cannot fail.

### Minor 7 — the CAPTURE-AND-PASTE literals are right, but the brief's stated constraint is thin

Checked **against a constraint rather than against themselves**, as required. Taken one at a time:
for `[-4.7272727272727275, 23.242424242424242]` the brief states constraints on the *draw sizes*
(`len(set(seen_of)) > 1`, `6 ≤ · ≤ 12`, `8 ≤ · ≤ 16`) and **no constraint on the endpoints at all**;
for `[4.0, 19.833333333333332]` the one stated constraint is that the pair differ from the clustered
pair, which **any two distinct pairs satisfy** — vacuous rather than weak. The "brackets the delta /
is wider" checks are ones I supplied, not ones the record states. **The numbers are not the problem;
the record is.**

I supplied a real one instead, and **both literals pass it**. Enumerating every difference achievable
under a whole-cluster draw (of: 3 draws with replacement from totals/sizes 0/2, 45/3, 120/4;
against: 4 from 4/2, 12/3, 18/3, 32/4) against every difference achievable under a unit draw:
`-4.7272727272727275` = −52/11 and `23.242424242424242` = 767/33 are **reachable under the cluster
draw and unreachable under the unit draw**, while `4.0` and `19.833333333333332` = 119/6 are
**reachable under the unit draw and unreachable under the cluster draw**. The two sets share the same
range (−8 … 28), so the range discriminates nothing and the denominators do everything. Verified by
running an exact-rational enumeration. The captured numbers are therefore construction-pinned — the
record just doesn't say why.

### Minor 8 — two small misstatements in the report

- Task 5 mutation 3 is recorded as *"FAIL with `ZeroDivisionError` (an attributable failure, not the
  bare `None` the brief predicted)"*. `task-5-brief.md` Step 5 predicted **`ZeroDivisionError`**, in
  those words. The outcome agreed with the brief; the note says it didn't.
- The report's task 7 note says the literal reading of mutation 4 *"produces neither of the two
  numbers the brief names … nor the fixture-B mutant table's numbers — I got 17.346768653175…"*. That
  is right, and worth one addition: `17.34676865317526` sits **0.017 % from** the spec table's
  `17.343852668925262` (`CR1 meat, df = n_of + n_against − 2`). No test asserts the latter, so
  nothing is unfailable, but two distinct wrong readings landing that close is the kind of
  coincidence this slice's fixture design is otherwise built to avoid.

## The two adjudications the review brief asked for

**Task 6 mutation 2 — overturned.** Not blind. See Major 2, including which fixture shapes
discriminate and which do not.

**Task 7 mutation 4 — the implementer's reading is the right one, and the ambiguity is harmless.**
**Verified by running** the *literal* reading (both `_cr1_variance` calls replaced by
`_sample_variance(side, mean)/n` while `groups_of`/`groups_against` stay the real cluster counts 3
and 4): the suite gives **2 failed, 2225 passed**, with
`test_the_unpaired_clustered_t_combines_two_per_side_cluster_dfs` failing at
`17.34676865317526 == 34.14810237373095` and the singleton-cluster arm of
`test_the_unpaired_clustered_t_refuses_a_side_below_two_clusters` failing too. So **both readings
kill the target test**, and this is emphatically *not* a mutation whose two branches cannot differ.
The implementer's reading — cluster counts also collapsed to unit counts — is the one the brief
*named* (*"the IID Welch form on the identical data"*, the spec's own fixture-B table row at ratio
0.2825), reproduces its stated target `9.647234756296374` exactly, and is the stronger mutant because
it removes clustering entirely rather than half. The defect is in the brief's instruction, which
under-specified the df; the implementation and the recorded outcome are sound.

## Attack points that came back clean

- **Extractions preserved their callers' behaviour.** `t_over_units` over `_WELCH_AGAINST` gives
  `2.063898561628024`, matching the pinned `2.0638985616280205` well inside `approx`;
  `t_over_units_clustered` over the 2/4/6 fixture gives `8.763214143637903`, matching the pre-existing
  independent pin; `paired_percentile_of_derived`'s clustered draw still gives `[1.0, 8.0]`, matching
  what `test_cli.py::test_a_clustered_resampled_contrast_really_drew_clusters` already pinned.
- **No monkeypatch was left aimed at a moved name.** The only two in the suite
  (`tests/test_stats.py:2805`, `:2982`) target `publishable.stats.random.Random`, and every
  `rng = random.Random(seed)` call site stayed where it was — `_draw_pools` takes no `rng` and
  constructs none. Verified by grep over `tests/` for `monkeypatch.`/`mock.patch`/`setattr(`
  intersected with the statistics names.
- **AND, not OR, and a test that distinguishes them.** `src/publishable/stats.py:1847` is `and`.
  **Verified by running** the `and`→`or` mutation: exactly one failure,
  `test_the_unpaired_percentile_refuses_only_when_both_sides_cannot_vary`, on the one-flat case's
  `interval is not None`. The fixture genuinely separates the connectives — `flat_of` is five
  identical rows and `varied_against` holds three distinct values.
- **`E-DATA-ALLOCATION-CONTRAST` alive**, in its `_check_sweep` emit, the registry at
  `src/publishable/validate.py:5068`, its `reference.md` § Errors and § Validation rows,
  `experimental-designs.md` § Mistakes core prevents, and nine `tests/test_validate.py` sites. The
  batch touches only `src/publishable/stats.py` and `tests/test_stats.py`; no `validate`/`run` path is
  exercised, every new test is a direct call.
- **Every documentary quote in a new docstring is verbatim in `reference.md`** — the
  `welch_t_over_units` row (line 2436), the `unpaired_percentile_over_units` row (2437), the suffix
  rule including the df-combination clause and "the percentile forms resample whole clusters —
  jointly across both sides when paired" (2441), the *d*s paragraph (2481), and § Clustered units'
  matched case-control sentence (1460).
- **Mechanical pass on the two changed files:** no trailing whitespace, no tabs, no invisible
  unicode, no `x`-for-`×` in any added line.
- **No count claim anywhere.** `unblock|executable|no remaining core-side` returns nothing in the two
  changed files or the five commit messages; the only hit is the report's own sentence saying so.
- Task 8's tautological third assertion (`assert 9 not in {...} or len(set(seen_of)) > 1`) was
  deleted as the brief instructed. `_draw_pools`' `ValueError` message has the caller's name deleted,
  not enumerated. `PairedResample`'s docstring lost the word "paired" by deletion.

## What I could not check

- **`correction.py` and `cli.py` threading** — tasks 11–14, unbuilt at this commit. Nothing in this
  batch has a production caller yet, so "the constructions are right" is all that is verifiable here;
  whether the right one is selected is a later batch's verdict.
- **The `sides`/`UnpairedEvidence` claims in Minor 4** cannot be resolved either way until task 11.
- **`plain_percentile`'s pinned endpoints** — I established that they survive an unclustered
  draw-order reversal, but not whether they would survive every plausible draw mutation. Task 21 owns
  that cell; flagging it rather than re-deriving its pin.
- I did not re-run the remaining eight prescribed mutations (task 4's 1–3, task 5's three, task 7's
  1–3 and 5, task 8's three). Their recorded numbers all match my independent recomputation of the
  fixture tables, and the ones I did re-run are the three the review brief singled out plus task 4's
  mutation 4.

## Tree state

**Clean.** Every mutation was reverted by editing the file back in place — never `git checkout --` —
each revert verified by `diff` against a copy taken before the first mutation, `__pycache__` cleared
between runs, and the final foreground pass re-run to confirm: `ruff check` clean,
`ruff format --check` 80 files, `mypy` 45 source files, `pytest` **2227 passed, 1 skipped, 2
xfailed**, `git status --short` empty.
