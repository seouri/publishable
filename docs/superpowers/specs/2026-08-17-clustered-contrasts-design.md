# H4b-2 — clusters through contrasts — design

**Goal:** a `data.units.cluster_by` declared beside a comparison stops being refused. The delta and its
interval are computed by a construction that reads the cluster as the draw, the `method` says so, and the
cluster count travels beside `n_paired`.

**What it delivers, stated honestly. H4b-2 unblocks ZERO configs.** No config in
`docs/feasibility-llm-growth-studies.md` declares `cluster_by` — its only two hits are both
`cluster_by: null` — so **the no-remaining-core-side-blocker count stays six and the executable count
stays three.** Neither moves. A retired refusal is not an execution, and this slice retires a refusal no
experiment hits. What it is worth instead is four things, and none of them is a number in that table: a
**live defect closed** (the zero-width stratified paired draw, filed by H4b-1 and owned here by name), a
**documented rule given code** (§ Statistical reporting's `_clustered` suffix rule has no paired
construction behind it), **one refusal retired, one re-owned or retired, and one narrow refusal minted**,
and a **build-hedged sentence in the specification resolved** in one direction.

**What it is not.** Not the unpaired forms — `welch_t_over_units`, `unpaired_percentile_over_units` and
both clustered counterparts are **H4c**'s, and H4c's refusal standing is what makes two paired
constructions sufficient here. Not `null_test` — H4d. Not `io.reuse_from` — unbuilt and unowned.

---

## The measurement this rests on

`docs/superpowers/H4b-2-SCOPING.md`, taken 2026-08-17 against `main` at `001ed9f`, after H4b-1 merged.
**Verdict: 18 tasks against the charter's 7.** It re-measures the cluster half of
`docs/superpowers/H4b-SCOPING.md`, taken at `b65ab91` — *before* H4b-1 merged, and H4b-1 changed the exact
functions this slice must touch. Baseline recorded there: `uv run pytest -q` → **2159 passed, 1 skipped,
2 xfailed**, foreground. Nothing here re-measures it; no production code ships from this document.

**Two commit pins, deliberately not blurred into one.** Everything inherited from the scoping is pinned to
**`001ed9f`**. Four facts were re-verified while writing this spec and are pinned to **`8e26727`**: the two
unconditional `"paired": True` literals in `cli._comparison_step_blocks`; § Statistical reporting's
`_clustered` suffix sentence being **generic over the contrast table** rather than an enumeration of rows;
`stats.t_over_units_clustered`'s CR1 scaling being `G/(G−1) · meat / n²` with df = `G − 1`; and the two
§ Validation rows *Clustered deltas aren't computed* and *Allocation deltas aren't computed*, the second
citing the first by name.

**The re-scope recorded one item moving DOWN** — the first decrease this repo has recorded. H4b-1 minted
`n_paired_effective` as a scalar sibling of `n_paired`, so the charter's "design and document a shape no
document licenses" is discharged and `n_paired_clusters` is precedent-following.

---

## Decisions

| # | Decision | Ruling | Grounds |
|---|---|---|---|
| 1 | One slice or two | **One, 18 tasks** | 18 is inside this repo's observed band — H3c-1 20, H7b Part A 20, H3d 19, H4b-1 15, H7c 14, H7b Part B 13. Decisively: H4b-1 split 22 **on the payoff line**, and that seam does not exist here — the payoff is zero for the whole slice, so any cut produces two halves neither of which moves a number. A cut would also sever the ordering chain: task 1 gates 6–9 and 11, task 4 gates 2, and task 14 must be last. The split question is closed here so planning does not reopen it |
| 2 | Where the retirement sits | **Last, after every construction, `method` string and record key** | `_comparison_step_blocks` takes `weights`, `strata` and `weighted_by` and **no membership parameter at all**; its `method` selection branches only on `weights is None` and `resample_columns`. Delete the emit today and a clustered contrast takes the **unclustered** path, publishing `method: paired_t_over_units` beside per-condition values that *are* `t_over_units_clustered`, with nothing in the record saying which is which — **and every existing test passes**, because the combination is refused today and no fixture exercises it. This is H4b-1's decision 4 one axis over: a raw interval whose counterpart was computed on different evidence |
| 3 | The weight × cluster combination H4b-1 left unrefused | **Mint the narrower refusal; do not build the weighted clustered pair** | `H4b-SCOPING` § 10 assigned that refusal to H4b-1 **by name**; `E-DATA-WEIGHT-CONTRAST` is gone and no replacement was minted, so a `weight_by` + `cluster_by` + baseline config earns `E-DATA-CLUSTER-CONTRAST` alone today. Minting is the house move — H3a minted `E-DATA-WEIGHT-CONTRAST`, H3b `E-DATA-CLUSTER-DERIVED`. The composition unblocks nothing measurable (no config declares `cluster_by` at all) and doubles the fixture burden on the dimension where a wrong choice hides best: df from the **cluster count** versus Kish's effective size, which coincide in any fixture not built to separate them. **Two constraints on the mint:** it is a **documented narrow refusal carrying both a § Errors row and a § Validation row**, not a `-UNSUPPORTED` build-family code — `CLAUDE.md` § Misreadings draws that distinction and it decides whether the code outlives this slice; and § Statistical reporting's *"does not compose with either weighted form **in this build**"* **loses the hedge and gains a link to the new code in the same task**, because a sentence and a guard are one claim seen from two ends. **Proposed spelling: `E-DATA-WEIGHT-CLUSTER-CONTRAST`**, on the `E-DATA-WEIGHT-CONTRAST` / `E-DATA-CLUSTER-CONTRAST` / `E-DATA-CLUSTER-DERIVED` family shape and verified free at `8e26727` (`grep -rn 'E-DATA-WEIGHT-CLUSTER' src/ docs/ tests/` → no hits) — named here rather than left to task 8, because an identifier nobody wrote down is how one gets minted twice under two spellings. **H4c inherits the composition itself** |
| 4 | The H4c ordering constraint no charter row states | **Assert it two ways, and neither of them is the obvious one** | `_comparison_step_blocks` writes `"paired": True` **unconditionally at both metric branches**, so every comparison surviving `E-DATA-ALLOCATION-CONTRAST` is paired and **two paired clustered constructions suffice** — but only while that code stands. The obvious pin, "a test that fails if `paired` is ever written `False`", is a **mutation whose two branches cannot differ**: `paired` is a literal, so there is no runtime state to assert against. Pin instead (a) that **both sites write the literal unconditionally**, so the test fails the moment H4c makes either conditional, and (b) that **`E-DATA-ALLOCATION-CONTRAST` still fires for every unpaired shape**, which is the behavioural gate — it fails the moment H4c retires that code and forces whoever does it to confront the clustered unpaired forms that do not exist. The emit message's *"once the paired **and unpaired** estimators take clusters"* is a promise about a code path that does not exist; it dies with the row rather than being built toward |
| 5 | The record shape, and whether new `method` vocabulary must be minted | **`n_paired_clusters`, documented before code writes it. No new `method` rows** | Two halves, and they part company. The **record key** is new: a key code writes and no document names is the pair `CLAUDE.md` says to grep for, so § Contrasts documents `n_paired_clusters` as a scalar sibling of `n_paired`, on H4b-1's own `n_paired_effective` precedent and by extending — not repeating — `cli.py`'s argument that `clusters` travels in `attrition` because "nothing in the documents shows a `clustered_by` sibling of `weighted_by`". The **`method` spellings** are **not** new: § Statistical reporting's suffix sentence is generic over the whole contrast table ("each of the **unweighted** forms above takes a `_clustered` suffix"), so `paired_t_over_units_clustered` and `paired_percentile_over_units_clustered` are already licensed. **Ruled explicitly: the two new forms get no table rows of their own.** `efa13bc` just repaired the opposite mistake by narrowing a quantifier rather than enumerating; adding rows converts a self-maintaining rule into a maintenance obligation nobody owns. Without this ruling in writing a later task will helpfully enumerate them |
| 6 | The live defect H4b-1 filed and this slice owns by name | **Fold in, built *with* the new construction — and strike the filing's amendment rather than implementing it** | `paired_percentile_of_derived` is the only one of four percentile constructions with **no content-based degenerate refusal**, and H4b-1 task 5's `strata` parameter made it reachable: a near-unique `stratify_by` makes every stratified contrast draw pick from an identical multiset, so the entry publishes `ci95: [x, x]` — a zero-width 95 % interval § Statistical reporting refuses in those terms, indistinguishable from a genuine one. **The obligation is live and the diagnosis is wrong.** Read at `001ed9f`: *both* return paths sort the returned pool, so the amendment's "second route to an unsorted-pool input" describes the **stratum key pools**, a different object from `PairedResample.pool`. The entry's original condition — "a **new** percentile construction returning an unsorted pool" — is exactly what task 7 adds. **Restore the entry to that condition and strike the 2026-08-17 amendment's stratum-pool reasoning**; `CLAUDE.md`: *"when you change code a `spec-defects.md` entry describes, re-read the entry"* |
| 7 | The payoff figure | **Zero configs unblocked; six and three unchanged, dated 2026-08-17 / `001ed9f`** | Verified by grep with a can-fail control on the same file: `cluster_by` → two hits, both `cluster_by: null`; `weight_by` → 10, a field that *is* declared. `CLAUDE.md`'s feasibility procedure step 10 exists because **a refusal count has been read as an execution count** — that failure arrived in H4b-1's own retirement commit and failed both review verdicts. No sentence in this slice may imply otherwise. The honest net on refusals is **one retired, one re-owned or retired, one minted**, which is not a regression and must not be written as "two refusals narrowed" |

### Decision 4 gates decision 5, and the asymmetry is the grounds

If task 4 rules **build the clustered derived draw**, a clustered contrast entry can exist with an
**unsuffixed** `method` — and the argument against a `clustered_by` sibling collapses, because that
argument is precisely that the suffix already discloses the clustering, whereas `weighted_by` was needed
since a weighted *derived* metric's `method` stays `paired_percentile_over_units`. If task 4 rules
**re-word and re-own**, the asymmetry holds cleanly. **Task 4 therefore precedes task 2**, and the
asymmetry is what makes the record decision principled rather than aesthetic.

### `validate` gates `run`, so the threading tasks cannot be tested through `run`

H4b-1's planning correction 1 applies here verbatim, and it is stated in the spec rather than left for
planning because H4b-1 paid a round discovering it. `cli.command_run` calls `validate_config` and returns
`EXIT_WRONG` on any error, and `E-DATA-CLUSTER-CONTRAST` is one — so **no clustered contrast reaches
`_comparison_step_blocks` through `run` until task 14 retires the refusal.** Tasks 6–13 test by direct
call, which the suite already does at three sites; **task 14 carries the `validate`-clean and
`run`-through halves.**

---

## What the scoping overturned

**The charter's hardest document task is already discharged, by a better move than the one it proposed.**
`H4b-SCOPING` § 5 ruled that `E-DATA-CLUSTER-CONTRAST`'s *"none of those five constructions exists"* had
to become an enumeration. `efa13bc` instead narrowed the quantifier's **scope** — "each **unweighted**
contrast construction", "**none of those** exists in this build". No count, no enumeration, still
self-maintaining. **Record the trade as resolved in H4b-1's favour, not as owed.**

**The charter's "`clusters` beside `n_paired`, in the shape task 3 designs" names a shape that does not
exist as described.** Task 3 was H4b-1's and it shipped a smaller answer, `n_paired_effective`.

**`E-DATA-WEIGHT-CONTRAST` is retired**, so `H4b-SCOPING` § 12's "live sibling row to re-word" is gone; and
**the weight × cluster code the charter said H4b-2 would *retire* was never minted**, so there is nothing
to retire and a decision to make instead (decision 3).

**Real, and never named by the charter:** the silent mis-routing (decision 2); `correction.py` as a
**second** production call site for both paired *t* forms, making `_corrected_bounds`
`paired_t_over_units_clustered`'s **first** caller; the `strata` × clusters composition inside the new
percentile construction, `paired_percentile_of_derived` having gained `strata` after the charter was
written; the zero-width stratified paired draw; and `paired` written unconditionally `True`.

**The development record is exempt from every sweep here.** `H4b-SCOPING.md`, `spec-defects.md`'s dated
entries and H4b-1's spec all carry "five" and **must not be retro-edited** — they record what was measured
on their date. `spec-defects.md`'s live entries are the one exception, and there a closed gap is **struck**
rather than deleted.

---

## The traps

| Trap | The rule |
|---|---|
| A clustered interval that merely moves | Under positive within-cluster correlation a cluster-robust interval comes out **wider** whatever df it uses, so widening is not evidence the cluster count reached the critical value — `t_over_units_clustered`'s own docstring says so. **Only the number is.** Size every fixture so a wrong clustering gives a *different* answer, and compute both by hand before asserting, as H4b-1's controller did for 6.0 versus 8.0 |
| A cluster fixture whose cluster count cannot change the answer | `CLAUDE.md` § Writing checks that can fail names this exact instance — *"a cluster fixture where correct and buggy cluster counts were both 3"* |
| A singleton-cluster fixture | One unit per cluster makes `clusters − 1` equal `n_paired − 1`, so the clustered and unclustered *t* forms **coincide exactly** and every assertion passes under a mutant that ignores membership entirely. The *fixture whose numbers agree with the bug* shape |
| Equal cluster sizes in the percentile fixture | Makes "a replicate's pooled row count varies" invisible; a mutant drawing **units** instead of clusters returns a fixed row count and is never seen |
| Kish and clusters coinciding | The df comes from the **cluster count**, not from Kish — § Statistical reporting settles that per condition and the paired form inherits it. A fixture where the two happen to agree cannot see a construction that took the wrong one |
| A mutation whose two branches cannot differ | **A mutation is a claim too.** H4b-1 shipped five blind mutations, one provably unbuildable. Decision 4's `paired`-is-`False` pin is the instance this slice would otherwise ship |
| A mutation applied to a proxy | `t_over_units_clustered` is shipped, tested and correct; breaking it proves nothing about the paired form. The discriminating mutation is on the **new** construction and on the `method`-selection branch |
| Reading a mutation's silence as confirmation | A mutation that changes nothing is evidence about the **tests**, not about the code |
| A mutation run against a self-chosen subset | H4b-1 produced a **false blind-spot claim** exactly this way — `strata=None` was declared blind on one self-chosen test and fails a named test on the full suite. Every mutation runs against the **full, unfiltered** suite in the **foreground**; a backgrounded run is how a re-reviewer stopped with a mutation possibly still applied |
| Reading "this config is refused" as "this path does not run" | **`validate` collects rather than aborting.** Four readers here have got this wrong, two of them in H4b-1 alone. Ask what `validate` *reports*, in full |
| A test asserting only that `n_paired_clusters` is present | H4b-1 pinned the three-way obligation for weights — value, interval and size move together — after `weighted_by`'s value passed under a hardcoded constant. A clustered entry carries the same obligation |
| A carried line number | `H4b-SCOPING` cited `stats.py:1900` for `E-DATA-CLUSTER-DERIVED`; it is elsewhere now. **Cite by name** |
| Filtering a sweep's output | Filter the **file list**, never the output — and exclude the development record, which is evidence rather than text to repair |

---

## The discriminating fixture, stated here so no later task can weaken it

**The constraints first**, because a later task may only substitute a fixture that meets all four:

1. **Not singleton clusters** — otherwise `clusters − 1 = n_paired − 1`.
2. **Correct and buggy cluster counts must differ** — the documented "both 3" failure.
3. **Two independent mutants must fail differently**: one keeping CR1's meat but taking the wrong df, one
   keeping the df but using the IID variance. That needs **strong within-cluster correlation in the
   differences**; i.i.d.-looking differences make CR1 ≈ IID and only the df moves.
4. **Unequal cluster sizes**, for the percentile form.

**The fixture: 12 units in 3 clusters of sizes 2, 4, 6**, per-unit differences `1.0 ×2`, `5.0 ×4`,
`9.0 ×6` against the baseline side. Delta = 76 / 12 = **6.3333…**. Half-widths, computed against
`t_over_units_clustered`'s own CR1 scaling (`G/(G−1) · Σ_g S_g² / n²`, df = `G − 1`) and
`t.ppf(0.975, df)` at df 2, 3 and 11 = 4.302653, 3.182446, 2.200985:

| What computes it | Half-width |
|---|---|
| **Correct** — CR1 meat, df = 2 | **8.7632** |
| Mutant: CR1 meat, df = `n − 1` = 11 | 4.4827 |
| Mutant: IID variance, df = 2 | 3.8678 |
| Mutant: cluster count miscounted as 4 | 6.1110 |
| `paired_t_over_units`, the unclustered form | 1.9786 |

**Five distinct answers, each separated by a margin no rounding can produce**, and the correct one is not
the extreme of any single dimension — so an assertion on the number discriminates all four failure modes,
which an assertion on "is it wider" does not.

For the **percentile** form the same 2 / 4 / 6 sizes make a replicate's pooled row count vary between 6
and 18 while a unit-drawing mutant returns a fixed 12 — the row count is itself an assertable
discriminator, and it must be asserted, not inferred from the interval.

---

## Task decomposition — 18

Grain matches `H4b-SCOPING.md`, `H7b-PartB-SCOPING.md` and `H3d-SCOPING-2.md`: each new construction, each
new record key and each document-table edit is its own task. **Seven ordering constraints:**

| Constraint | Reason |
|---|---|
| **Task 1 before 6–9 and 11** | Under decision 3 what task 1 fixes is the refusal's identifier and whether two constructions exist or four — and with it how many cells task 11's branch has. Building first bakes the answer in by omission — H4b-1's own *5 before 7*, one axis over |
| **Task 4 before task 2** | Decision 4 gates decision 5: whether a clustered contrast can carry an unsuffixed `method` decides whether the no-`clustered_by`-sibling argument holds |
| **Task 3 before 7** | A degenerate-draw refusal lives **inside** the percentile construction |
| **Task 2 before 13** | A record key must exist in a document before code writes it — H4b-1's *2 and 3 before 7–10* |
| **Task 6 before 12** | `correction._corrected_bounds` is `paired_t_over_units_clustered`'s **first** caller, exactly as H4b-1's spec correction 2 found for the weighted form |
| **Task 14 last** | A refusal is deleted only after everything it stood in for exists, and task 14 alone carries the `validate`-clean and `run`-through halves |
| **Task 15 must not touch the development record** | It is evidence, not text to repair |

**Decisions and documents — 5**

1. **Decide and record the weight × cluster composition** per decision 3: mint the narrower refusal,
   de-hedge § Statistical reporting's "does not compose" sentence and link it to the new code.
2. **Document `n_paired_clusters`** in § Contrasts, on the `n_paired_effective` precedent, extending or
   distinguishing `cli.py`'s "no `clustered_by` sibling" argument per decision 5. **After task 4.**
3. **Decide the degenerate-draw refusal** for the paired percentile family — decision 6's filed zero-width
   defect, and the content-based refusal each of its three siblings carries.
4. **Decide `E-DATA-CLUSTER-DERIVED`'s fate**: build the clustered derived draw, or re-word its § Errors
   row — whose justification is *"Temporary, alongside `E-DATA-CLUSTER-CONTRAST`"* and dangles the moment
   task 14 lands — and re-own the code **by name**. Silence is how a deferral ends up owned by nobody.
5. **Record the `E-DATA-ALLOCATION-CONTRAST` sequencing dependency** in writing with its two pins, per
   decision 4.

**Constructions and refusals — 4**

6. **`paired_t_over_units_clustered`** — CR1 over the differenced values, df = clusters − 1, mirroring
   `t_over_units_clustered` rather than hand-rolling a variance.
7. **`paired_percentile_over_units_clustered`** — whole clusters, one joint draw for both sides,
   **composing with `strata`**: a cluster drawn within its stratum, mirroring
   `percentile_over_units_clustered`'s existing equality, which § Validation's
   *`E-STATS-RESAMPLE-STRATIFY-VARIES`* already specifies.
8. **Mint the weight × cluster refusal** per task 1 — the code, its § Errors row and its § Validation row,
   bundled as one task on H4b-1's task-11 precedent.
9. **The content-based degenerate refusal** built into the paired percentile family, per task 3.

**Threading and record — 4**

10. **Thread `clusters` into `_compute_vs_baseline`, `_compute_declared_contrasts` and
    `_comparison_step_blocks`** — the mapping already exists at `command_run` (`clusters_of(roster,
    cluster_by)`, the single authority); none of the three takes it.
11. **The `method`-selection branch** — today two-way on `weights is None` and `resample_columns`, now
    **six-way** on `weights` × `clusters` × `resample_columns`, and the `method` string each writes.
    **Six, counted rather than carried**, because the scoping's "four-way (or six-way, per the composition
    decision)" reads the other direction: *build* the composition gives eight reachable cells, and decision
    3's *mint the refusal* removes the two weighted-clustered ones, leaving

    | `weights` | `clusters` | `resample_columns` | `method` |
    |---|---|---|---|
    | no | no | no | `paired_t_over_units` |
    | no | no | yes | `paired_percentile_over_units` |
    | no | yes | no | `paired_t_over_units_clustered` |
    | no | yes | yes | `paired_percentile_over_units_clustered` |
    | yes | no | no | `weighted_paired_t_over_units` |
    | yes | no | yes | `weighted_paired_percentile_over_units` |

    An implementer writing four arms leaves two cells falling through to a wrong `method` — decision 2's
    failure one axis over, and again with every existing test passing, because the refused cell has no
    fixture.
12. **`Member.clusters` and the corrected bound** — `correction.py`, the call site the charter names
    nowhere, and the second widening H4b-1's task-4 ruling predicted when it named its own cost.
13. **`n_paired_clusters` on every affected entry**, with H4b-1's three-way move-together obligation
    pinned: value, interval and size.

**Retirement, residue and regression — 5**

14. **Retire `E-DATA-CLUSTER-CONTRAST`** — its one emit, its § Errors row, its § Validation row *Clustered
    deltas aren't computed*, the sibling row *Allocation deltas aren't computed* **re-worded rather than
    left dangling** (it cites the clustered row **by name** to state its own per-comparison reading against
    that row's per-family one, and the citation was installed deliberately by H4b-1's task-9-12 review so it
    would survive `E-DATA-WEIGHT-CONTRAST`'s deletion — this slice is what breaks it), and six test
    assertions. **Last**, and it carries the `validate`-clean and `run`-through halves.
15. **The surviving-citation sweep** — every site naming `E-DATA-CLUSTER-CONTRAST` that task 14 does *not*
    delete: three `validate.py` comments, `stats.summarize_step`'s docstring, `E-DATA-CLUSTER-DERIVED`'s
    § Errors row, § Statistical reporting's compose sentence, and the `tests/` assertions pinning
    `E-DATA-CLUSTER-CONTRAST` and `E-DATA-ALLOCATION-CONTRAST` **co-reporting** — which is behaviour, not
    wording, and must be **narrowed to the allocation code alone rather than deleted**, since deleting them
    drops the pin on `validate`'s collect-don't-abort property. By claim, over a named file list, excluding
    the development record. **Not** the "five" sweep: both surviving ends of that claim sit inside blocks
    task 14 deletes.
16. **The filings** — the finiteness entry with its two `*_is_a_known_unfixed_gap` tests, which move **with**
    the entry; contrast-disclosure findings 1 and 3; the sorted-pool row **re-stated or struck** per
    decision 6 rather than implemented as filed; § *How a metric becomes a number* claimed or **declined in
    writing** (declined twice already, and a third silent pass is how it goes stale); `report_by`'s
    whole-roster-versus-arm gap **explicitly re-owned to H4c**; and `correction.corrected_fields`' dedupe
    recorded as **not H4b-2's** — this slice widens `Member`, it does not build `Member` lists elsewhere,
    which is the condition that filing names.
17. **The regression pin** — an unclustered unweighted config byte-identical (`paired_t_over_units`,
    `paired_percentile_over_units`, and the worked example's intervals, which `CLAUDE.md` § The worked
    example says **must not be narrowed back**), **and an unclustered weighted one**, which is H4b-1's
    output and must not move. Plus the boundary test this slice owes rather than merely respects: a
    clustered pass walking every metric block **must skip** a `summary`-step `Estimate`, which is
    `reported: true`, outside the correction family and never recomputed.
18. **The dated re-measurement** in `docs/feasibility-llm-growth-studies.md` § Executability on this build
    — **re-dated, not edited**, stating **zero** plainly and leaving six and three unchanged.

---

## Out of scope, with the route

| Out | Owner |
|---|---|
| `welch_t_over_units`, `unpaired_percentile_over_units` and both clustered counterparts; `E-DATA-ALLOCATION-CONTRAST`; the `cohens_d` *d*s branch; **and the weight × cluster composition this slice refuses** | **H4c.** Its refusal standing is what makes H4b-2's two paired constructions sufficient |
| `W-STATS-REPORTBY-THIN`'s whole-roster-versus-arm gap and the `report_by` level's `resample_columns` asymmetry | **H4c.** Live on C1–C3, created by neither weights nor clusters. **Declined in writing** by task 16, not folded in |
| `statistics.null_test`, `p_value`, `fdr_bh` made real | **H4d** |
| `io.reuse_from` and `lineage.py` | **Unowned**, filed. Blocks E3/E4/E6 |
| Folds and holdouts within cells; `E-REPL-FOLD-CELLS` / `E-DATA-HOLDOUT-CELLS` | **H3c-3** |
| The apparatus probe, `apparatus_facts`, `cli.py`'s hardcoded `apparatus: null` | **H7d** |
| `study` / `report` / `diff` / `freeze` | **H8** |
| Interactions, dose-response orderings, differences-in-differences | **Refused.** Contrasts do not nest |

**Task count is 18.**

---

## Corrections against the code — appended 2026-08-17 while planning, at `82310b9`

**Appended rather than edited into the body above**, per `CLAUDE.md`: a spec records what was decided
when it was written, and retro-editing destroys the evidence it exists to hold. Each item below
**replaces** the named claim; everything else in this document stands. Every one was found by reading
the function or the test named beside it, at `82310b9`.

| # | What the spec says | What the code says | What replaces it |
|---|---|---|---|
| 1 | § 5's table lists `paired_percentile_over_units_clustered` under "In `stats.py` — **No**", and task 7 names it as a construction to build | `paired_percentile_over_units` is **not a function**: it is a `method` string `paired_percentile_of_derived` emits through its `method=` parameter, which already serves two spellings because one construction is shared by a derived contrast and a recorded column's | Task 7 adds a `clusters` parameter to `paired_percentile_of_derived` and a **third `method` string**, not a fourth function. A separate function would duplicate the `strata` composition, the sorted-`keys` precondition and the degenerate refusal |
| 2 | Task 11 describes "**the** `method`-selection branch", six-way on `weights` × `clusters` × `resample_columns` | It is **two sites**. The *t* arm's `method` comes from the construction it calls — each `stats` function stamps its own — while the percentile arm's comes from a `method=` argument the caller passes | The six-cell table stands as the specification of what must be written; the plan wires the *t* site in task 10 and the percentile site in task 11, and asserts all six cells together. An implementer looking for one branch will not find it |
| 3 | Task 14 lists "six test assertions" and the scoping attributes three surviving comments to `_check_unimplemented`'s docstring, the `_check_assign` comment, and the allocation guard comment | `tests/test_validate.py` holds **seven** assertion lines naming the code, and `tests/test_cli.py::test_the_sibling_refusal_rows_state_their_own_reading` locates the § Errors row with `next(...)` — so it raises `StopIteration` when task 14 deletes the row. Of the three `src/` comments, one is in `_check_evaluation_split_cells`' **docstring** and one is a comment **inside `_check_unimplemented`** about what an assigned run may not do; only the allocation-guard attribution is right | The plan enumerates every site by **what the comment does** rather than by the function the scoping named, and task 14 owns `test_the_sibling_refusal_rows_state_their_own_reading` — **narrowed to the allocation row, never deleted**, the same ruling the spec makes for the co-reporting tests. A task scoped by function name would have missed two sites, which is the `E-TEMPLATE-UNKNOWN` misreading exactly |
| 4 | § The discriminating fixture and § The traps both say a wrong clustering must give a different answer, and leave which mutations prove it to planning | The obvious alignment mutation — reversing the label vector against the 2 / 4 / 6 fixture — maps the three clusters onto a **different partition with the identical multiset of per-cluster residual sums**, so the half-width comes back 8.763214143637901 against 8.763214143637903. Verified numerically at `82310b9` | The plan names that mutation as **blind by arithmetic** so nobody prescribes it later, and prescribes instead a lexicographic key-order mutation, which gives 5.971123930019732. The fixture itself is unchanged and all five spec half-widths were confirmed by calling the shipped `t_over_units_clustered` |

**Not a correction, recorded so it is not re-derived:** decision 6's reading of the sorted-pool
filing was checked again at `82310b9` and **holds** — both of `paired_percentile_of_derived`'s return
paths sort the pool, so the 2026-08-17 amendment's "second route to an unsorted-pool input" is about
the stratum key pools, a different object. The plan's task 16 strikes the amendment and restores the
entry's original condition, as decision 6 directs.
