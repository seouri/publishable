# H4b-2 batch 2 (tasks 6–9) — review

Reviewed at `472e938` on branch `h4b2-clustered-contrasts`, 2026-08-18. Gates re-run in the
foreground by me at that commit: `ruff check` clean, `ruff format --check` 80 files, `mypy` clean on
45 source files, `pytest` **2178 passed, 1 skipped, 2 xfailed** — matching the report.

## Verdicts

**Spec compliance: PASS.** All four tasks build what the design's § Corrections-amended body
prescribes. Task 7 added a `clusters` parameter and a third `method` string to
`paired_percentile_of_derived` rather than a fourth function (Corrections item 1, honoured). Task 8's
`E-DATA-WEIGHT-CLUSTER-CONTRAST` carries both a § Errors row (`docs/reference.md:515`) and a
§ Validation row (`docs/reference.md:318`) and is not a `-UNSUPPORTED` code; § Statistical reporting's
*"in this build"* hedge is gone (`docs/reference.md:2444–2447`) and nothing left in that section
implies the composition may yet appear. `E-DATA-CLUSTER-CONTRAST` is alive
(`src/publishable/validate.py:5017`) and every new refusal test asserts alongside it, never in place
of it. No sentence in any touched file claims a config is unblocked; the six/three counts are
untouched — verified by grep over the touched file list.

**Task quality: PASS with reservations.** The statistics are right and the discriminators are real —
I recomputed the correct half-width and re-ran three mutations against the full unfiltered suite. The
reservations are all in claims *about* the code: two normative/comment sentences that a probe
falsifies, one live filing left asserting a gap this batch closed, and one mutation recorded blind for
which a discriminating fixture demonstrably exists.

**Do the Majors move the verdicts? No, and here is why, stated rather than left to inference.** The
two candidates are Major 1 (a sentence in one of the four normative documents falsified by probe) and
Major 5 (a live filing still asserting the gap task 9 closed, on the one file CLAUDE.md says a closed
gap must be *struck* in). Both are failures to **propagate** a claim, not failures to **build** the
thing the spec ordered — task 9's brief prescribed the child entry alone, and the construction, the
refusal and the rows are all what the design specifies. Spec compliance therefore holds at PASS, and
both findings land on task quality, which is where the reservations are. Neither is deferrable past
this branch: Major 5 is a live list, and Major 1 sits in `reference.md`.

## Verified by running

- **The fixture's five answers.** I recomputed the correct half-width independently (mean 76/12,
  per-cluster residual sums −10.6667/−5.3333/+16.0, meat 398.2222, V = (3/2)·398.2222/144,
  t(.975, df 2) = 4.302653) → **8.763216**, matching the asserted `8.763214143637903`
  (`tests/test_stats.py:1460`). The four wrong readings in the docstring (4.4827, 3.8678, 6.1110,
  1.9786) all reproduce, and the nearest is 6.111 — far outside `pytest.approx`. The single
  half-width assertion does discriminate all four.
- **Mutation A — task 6 mutation 1** (`dict(zip(sorted(keys), labels, strict=True))`,
  `src/publishable/stats.py:435`): full unfiltered suite → **1 failed, 2177 passed**, half-width
  `5.971123930019732` exactly as prescribed, with the `method` and centre assertions still passing.
  This is the *replacement* for the known-blind label reversal, and it discriminates.
- **Mutation B — task 9 mutation 2** (key-in-signature proxy inside `_drawable_content`,
  `src/publishable/stats.py:1265`): full suite → **4 failed** (all four parametrized cases), 2174
  passed. The proxy shape is pinned.
- **Mutation C — task 8 mutation 1** (`and True` for the weight half,
  `src/publishable/validate.py:5049`): full suite → **5 failed**, including the prescribed
  `test_a_cluster_without_a_weight_draws_only_the_cluster_refusal`. I read each extra failure; all
  are clustered-comparison configs the over-firing mutant now hits (including the *control half* of
  `test_a_clustered_baseline_that_generates_no_comparison_stays_legal`), so the guard is correctly
  two-sided.
- **The pooled row counts.** `paired_percentile_of_derived` at seed 11 over the 2/4/6 fixture:
  unstratified clustered → `{6,8,10,12,14,16,18}`; stratified → `{10,12,14}`. The unstratified test's
  `min==6 and max==18` plus `set(seen) != {12}` is asserted directly, so item 2's property holds.
- **The rendered diagnostic** for a weighted+clustered comparison, through `validate_config` and
  `Collector.render()`: see Major 2.
- **`percentile_over_units([5.0]*8)` unstratified** still returns `Interval(5.0, 5.0)`: see Major 1.
- **Unsorted `keys` with `strata`, guard disabled**, produce the *identical* draw sequence to sorted
  keys: see Major 3.
- **Unsorted `keys` with neither `strata` nor `clusters`** are accepted and produce a *different*
  draw sequence from sorted keys: see Major 4.

All mutations were reverted by editing the file back (never `git checkout --`), each against a
scratchpad copy taken beforehand, and every revert confirmed byte-for-byte by `diff` plus a final
clean full run. **The tree is clean**: after the last revert `git status --porcelain` was empty and
the final suite was 2178/1/2. The only thing standing in it now is this review file, untracked —
`git check-ignore` confirms `.superpowers/sdd/.gitignore` does **not** ignore it (that file's content
is intact, not clobbered), but `git add -f` remains the reliable spelling.

## Findings

### Critical

None.

### Major

**Major 1 — a normative sentence claims a refusal the per-condition forms do not make, and a live
filing says so.** `docs/reference.md:2449`: *"That is the same refusal the per-condition percentile
forms already make for their own draws."* **Verified false by running:**
`percentile_over_units([5.0]*8, seed=1, draws=200)` returns `Interval(low=5.0, high=5.0)` at HEAD —
the unstratified, unclustered per-condition draw publishes the zero-width interval this batch now
refuses on the contrast path. `docs/superpowers/spec-defects.md:5588` (Finding 2's scoping paragraph)
states exactly this, probed, and warns in terms: *"a reader inferring the general guarantee from the
sentence above would be wrong."* Task 3 wrote the sentence; task 9 gave it code and closed the filing
without reconciling the two. The consequence is real and undisclosed: within one run a constant
column now gets `ci95: [5,5]` per condition and `ci95: null` on the delta. Either narrow the sentence
to the branches that make it, or record the asymmetry.

**Major 2 — task 8's message is the only one in `validate.py` that restates its own `path`, and the
test that forced it does not test the thing that broke.** `src/publishable/validate.py:5056–5065`.
**Verified by running** through `validate_config` + `Collector.render()`:

```
  error   E-DATA-WEIGHT-CLUSTER-CONTRAST data.units.weight_by
          `data.units.weight_by` and `data.units.cluster_by` are both declared beside a comparison, …
```

I parsed every `c.error`/`c.warn` emit in `validate.py`: 128 of 137 open lowercase, as a continuation
of the path line, and the sibling `E-DATA-CLUSTER-CONTRAST` opens *"makes the cluster the inferential
draw…"*. This is the **only** message whose literal opening repeats its own `path`. The implementer's
diagnosis (disagreement 2) is correct — `messages_by_code` reads `f.message` alone — but the fix went
to the symptom. **On the harder question asked:** the test is not vacuous (an empty message fails it),
but it is near-vacuous *as a message test* — the dict is already keyed by code, so `"weight_by" in
message` and `"cluster_by" in message` add almost nothing, and the field that actually carries the
identity, `f.path`, is unasserted. Restore the brief's continuation wording and pin `path` (or assert
the rendered line).

**Major 3 — the sorted-`keys` `ValueError`'s stated grounds are false, and task 7 rewrote the code
around them without re-checking.** `src/publishable/stats.py:1386–1394` claims the relabelling
invariance *"holds only because that first-occurrence order coincides with content order whenever
`keys` is ascending"*. **Verified by running:** with the guard temporarily disabled, a shuffled `keys`
list under `strata` produced a draw sequence **identical** to the sorted one — because
`pools = [sorted(group) …]` followed by `pools.sort()` makes the whole structure a pure function of
content. The guard is defensible as a bookkeeping assertion; its justification is a guarantee claim
the code does not need, restated at a second site (`tests/test_stats.py:4127`'s docstring). CLAUDE.md:
*"When you change a guard, re-read its justification."* Inherited from H4b-1, but task 7 rewrote the
enclosing comment and carried it. Prefer deleting the causal clause to rewriting it. Related and
smaller: that comment block now sits ~40 lines above the guard it explains, between `rng = …` and the
`items` construction — an insertion-orphaned paragraph, the batch-1 finding shape.

**Major 4 — task 7's mutation 4 is recorded blind, but a discriminating fixture exists and is legal.**
The report accepts the brief's reading that `items = sorted([key] for key in keys)` cannot be caught.
**Verified by running:** `paired_percentile_of_derived` with **no `strata` and no `clusters`** accepts
an unsorted `keys` list (the `ValueError` fires only under `strata`) and draws a *different* sequence
from the sorted one — so the mutant is caught by a one-line fixture change to
`test_the_unclustered_paired_draw_is_the_same_sequence_it_always_was`
(`tests/test_stats.py:1624`). CLAUDE.md: *"'No mutation reaches this' and 'no mutation can reach this'
are different claims."* This is the second claim being asserted where only the first was measured.

**Major 5 — the live filing still asserts the gap this batch closed, and the parent heading is now
false.** `docs/superpowers/spec-defects.md:5557`, heading: *"…and `paired_percentile_of_derived` never
got the zero-width sweep"* — it got one, in task 9. Finding 2's body (`:5588`) still reads *"The
paired construction has no such check"* and *"the sweep should finish rather than stop at three"*,
both false at HEAD. The implementer amended only the re-owning paragraph's *citation* of the child
entry. The spec's task 16 owns findings **1 and 3**, explicitly not 2 — because 2 is what task 9
closes — so this is task 9's own residue, on the one file CLAUDE.md names as a live list where a
closed gap must be struck. Also: the replacement clause *"which closes the paired construction's
content-based degenerate refusal"* is inverted (a gap is closed, not a refusal) and drops the
clustered/unclustered dimension the code covers.

### Minor

**Minor 1 — an assertion looser than the fixture supports, and a docstring stating an unreachable
value.** `tests/test_stats.py:1566`: `assert set(seen) <= {10, 12, 14, 16}`, docstring *"confined to
{10, 12, 14, 16}"*. Stratum A (clusters of 2 and 4) draws twice → {4,6,8}; stratum B (one cluster of
6) → 6; reachable totals are **{10, 12, 14}**. **Verified by running:** the observed set at seed 11 is
exactly `{10, 12, 14}` — **16 is unreachable**. Not a fail-open (mutation 3 escapes to 18 and is
caught), but the bound is loose and the docstring claims what the code cannot produce.

**Minor 2 — the batch left two forward-dangling citations of the code task 14 deletes, and neither is
recorded.** `docs/reference.md:515` (*"read the same way `E-DATA-CLUSTER-CONTRAST` above reads it"*)
and `src/publishable/validate.py:5044` (*"Reads the resolved family, for the reason its sibling above
does"* — a positional locator for an emit block task 14 removes). The spec's task 15 sweep enumerates
the surviving-citation sites as measured *before* these existed, so nobody owns them. Add both to the
task 14/15 list.

**Minor 3 — a brief/code disagreement the report did not flag.** Task 8's brief step 3 asks the
§ Errors row's first cell to state *"its temporariness"*, while the same brief's header and design
decision 3 rule that the code **outlives** this slice. The implementer followed the correct half and
wrote no temporariness clause, but did not record the contradiction — a fourth disagreement, resolved
right and left unsaid.

**Minor 4 — the sorted-`keys` guard is untested in composition with `clusters`.** Item 3's composition
half is otherwise well covered (`tests/test_stats.py:1566` for clusters × strata, and the
`E-STATS-RESAMPLE-STRATIFY-VARIES` test for a cluster straddling two strata, both re-run green), and
H4b-1's `ValueError` test (`tests/test_stats.py:4127`) survives unmodified — but only in its
unclustered form. No test exercises unsorted `keys` *with* `clusters`.

**Minor 5 — the report's "matched verbatim" claim is not true of task 7.**
`src/publishable/stats.py:1450` carries an `assert clusters is not None` and a three-line comment that
task 7's prescribed block does not contain. Both are **correct** — mypy needs the assert to narrow
`clusters[key]` in the raise below it, and I checked the comment's *"can never fire"* claim holds
(with `clusters=None` every item is a single key, so `strata[item[0]] == rendered` trivially) — so the
code is not a defect. The finding is the report's sentence *"Task 7's core draw-shape implementation …
matched the spec's prescribed code verbatim"*, which is an overreaching prose claim of the kind this
repo counts on its own.

**Minor 6 — a slice name and a count in a normative row.** `docs/reference.md:515` opens *"H4b-2
builds the two unweighted paired clustered constructions"*. Precedent for slice names in
`reference.md` exists (§ The one config file names H4a, H3d, H7b Part B), so this is not a house-style
break, but it is an undated build claim carrying a count in a document whose convention for build
state is the *"in this build"* idiom.

## Adjudications requested

1. **Double-counted draws in the regression test — accept.** The accumulator length was load-bearing
   only in the RNG-sequence test; splitting `compute_of`/`compute_against` so one records is the
   minimal fix and touches no construction. `test_the_paired_clustered_percentile_draws_whole_clusters`
   still passes one closure to both sides, which is harmless there because its assertions are over the
   count *set*. Read, not re-run in isolation.
2. **The `weight_by` literal — accept the diagnosis, reject the fix.** See Major 2.
3. **The orphaned `spec-defects.md` citation — accept, and it does not belong to task 16.** CLAUDE.md
   names `spec-defects.md` as the explicit exception to the no-retro-edit rule and separately requires
   re-reading an entry whose code you change. Leaving a citation pointing at a nonexistent heading
   would itself have been a finding. Fold Major 5 into the same paragraph rather than reverting.

## Incident recovery — complete

**No mutation survives in the committed diff**, verified two ways: I read the committed
`paired_t_over_units_clustered` (`src/publishable/stats.py:435`), which delegates to
`t_over_units_clustered` with `dict(zip(keys, labels, strict=True))` and rewrites the `method` — all
three of task 6's mutations absent — and I re-ran mutation 1 myself against the full suite, which is
the one whose result straddled the backgrounding gap. It fails exactly one test on exactly the
predicted number. Task 6's mutation results are trustworthy.

## Accounting, so it is not re-derived

The briefs' absolute figures (2166 / 2170 / 2174 / 2179) are each one high because this session's
measured baseline was 2162, not the spec's 2163: 2162 + 3 + 4 + 4 + 5 = **2178**, which is what I
measured. Not a finding.

## Not checked

- Tasks 10–18 (threading, `Member.clusters`, the retirement, the sweeps) — out of this batch.
- The mechanical `*.md` pass I ran covers `docs/reference.md` in full (trailing whitespace, tabs,
  invisible unicode, duplicate anchors, table column counts, `#anchor` resolution with a positive
  control). The three column-count mismatches it reports are pre-existing escaped-pipe artifacts at
  lines 476/1627/3237; both new rows are correct. The § Errors table is **not** alphabetically sorted
  (eleven pre-existing order breaks, related codes grouped instead), so the new row's placement beside
  its sibling follows practice.
- **Task 7's mutations 1–3 and task 9's mutations 1 and 3 were not re-run.** I relied on the
  implementer's report for those. A clean suite proves a mutation is not *applied*; it says nothing
  about whether it *discriminates*. Three mutations were re-run end to end, and they are the three
  named above.
