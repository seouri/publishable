# H4b-1 — weights through contrasts — design

**Goal:** a `data.units.weight_by` declared beside a comparison stops being refused. A weighted
contrast is computed, its interval is its own construction over the paired intersection, and the
record says it was weighted.

**What it delivers, stated honestly.** **`E-DATA-WEIGHT-CONTRAST` retired, and the count of
experiments with no remaining core-side blocker goes three → six** — C1, C2 and C3 join E1, E2 and
E5. **The executable count stays at three.** C1–C3 also depend on `io.reuse_from`, which is unbuilt,
unowned, and which no config or grep can settle; until it is, "no remaining core-side blocker" is the
honest phrase and "executes" is not.

**What it is not.** Not clusters through contrasts — that is **H4b-2**, seven tasks that unblock
**zero** configs. Not the unpaired forms — H4c. Not `null_test` — H4d. Not `io.reuse_from`.

---

## The measurement this rests on

`docs/superpowers/H4b-SCOPING.md`, taken 2026-08-17 against `main` at `b65ab91`, after H3d, H7c and
both halves of H7b. The charter's **14** becomes **22**, of which this slice is the **weights** half.

**It also caught an error of mine.** My scoping brief asserted "5 emit sites in `validate.py` and 3
rows in `reference.md`" — a `grep -c`, which counts *spellings*. Measured and verified: **one emit**,
four mentions in a docstring and three comments; **one § Errors row**, the other two being sibling
rows that *cite* it; plus **one § Validation row the brief did not count at all.** This is the exact
substitution the same brief warned against, three paragraphs above the error.

---

## Decisions

| # | Decision | Ruling | Grounds |
|---|---|---|---|
| 1 | Ship 22 tasks as one slice or two | **Two, seamed at weights/clusters** | 22 is above this repo's band — H3c-1 20, H7b Part A 20, H3d 19, H7c 14, H7b Part B 13. The seam is `H4-SCOPING`'s own fallback, promoted here because **the entire payoff is in the weights half**: clusters through contrasts unblocks **zero** configs. Splitting on the payoff line means the half that moves the number ships first and alone |
| 2 | Which construction the payoff actually runs through | **`paired_percentile_of_derived`, via a closure change and a record change — *not* `paired_t_over_units`** | The refusal's own message, its § Errors row and the charter all name `paired_t_over_units`, `paired_delta_of_derived` and `paired_percentile_of_derived` as the estimators needing weights. **All three C configs declare `resample`**, so `resample_columns=True`, so a column contrast goes through `paired_percentile_of_derived` with a `_column_mean` closure whose `Member` carries `pool`, not `diffs`. `paired_t_over_units` is **never called** on C1–C3, raw or corrected. A spec written from the charter builds the wrong thing and ships a payoff that never runs |
| 3 | A weighted contrast's `method` string | **Minted here, because the four documents give it none** | § Statistical reporting gives weights explicit rows *per condition* and a `_clustered` suffix rule *on contrasts*, and gives **weights on a contrast nothing**. There is no `weighted_paired_*` spelling anywhere. A record key that code writes and no document names is the pair `CLAUDE.md` says to grep for; mint the vocabulary in the document first, then emit it |
| 4 | The corrected bound under a weight | **Decided before any code, and argued against `Member.__post_init__`'s exactly-one invariant** | `correction._corrected_bounds` calls `paired_t_over_units(member.diffs)`, and **`Member` has no weights field** — so a weighted raw interval would ship beside an *unweighted* corrected one, and **every existing test would pass.** Either `Member` carries weights or the corrected path is forced onto the pool; both touch an invariant, so the decision is a task, not an implementation detail |
| 5 | `resample.stratify_by` on a contrast | **Closed here, not filed** | Verified: of four percentile constructions, `percentile_over_units`, `percentile_over_units_clustered` and `percentile_of_derived` take `strata`; **`paired_percentile_of_derived` does not.** So a declared stratification is honoured per condition and **silently dropped on every contrast** — and **all three payoff configs declare one.** Filing it would ship "C1–C3 have no core-side blocker" while their contrast intervals quietly ignore a declaration they made. That is the `hash_index` shape, which went unfiled for four slices; this one is on the payoff path and closes here |
| 6 | The payoff figure | **Three → six with *no remaining core-side blocker*; executable stays at three** | `CLAUDE.md`'s feasibility step 10 exists because a refusal-count has been read as an executable-count. C1–C3's `io.reuse_from` dependency is **unsettled** — the scoping says plainly that no config and no grep can settle it — so the honest sentence names the blocker rather than rounding it away |

---

## What the scoping overturned

**`H4-SCOPING`'s "`effective`/`clusters` beside `n_paired`" is an undocumented invention.** `n_paired`
is a scalar and no sentence in the four documents licenses that shape.

**`E-DATA-CLUSTER-CONTRAST`'s "none of those five constructions exists" cannot be walked to zero by
H4b** — two of the five are unpaired forms **H4c** owns.

**`H4a-SCOPING`'s line numbers moved by ~50** since `53090e9`.

**Confirmed rather than merely carried:** `H4-SCOPING` § 4.3's derived-half argument, now better
documented than when written; § 1.2's weighted-percentile correction; `report_by` minting no `Member`;
and H3d task 15's roster-inertness finding — **but only when no comparison declares `within`.**

---

## The traps

| Trap | The rule |
|---|---|
| Building the estimator the refusal names | Decision 2. The message, the row and the charter agree with each other and **not with the code path C1–C3 take** |
| A weight that changes nothing | A weighted interval whose weights are uniform is the unweighted one. **Size the fixture so a wrong weighting gives a different answer** — this repo has found sixteen checks that could not fail in statistics alone |
| The corrected bound diverging silently | Decision 4. A weighted raw beside an unweighted corrected passes **every existing test** |
| Reading a mutation's silence as confirmation | A mutation that changes nothing is evidence about the **tests** |
| A probe proving the moment | **A test proves tomorrow.** Five times in three slices a correct fix shipped unpinned, most recently a credential-leak remedy verified by subprocess and caught by nothing |
| Counting a spelling | Decision 2's measurement, and my own error above. **Enumerate by reading, then confirm by grep** |

---

## Task decomposition — 15

The weights half of the scoping's § 10, in its order. Its three ordering constraints are adopted:
**5 before 7** (a stratified draw lives *inside* the weighted closure, so building the closure first
bakes the answer in by omission — which is how `stratify_by` got dropped here in the first place);
**2 and 3 before 7–10** (an emitted `method` string and a record key must exist in a document before
code writes them); **13 last**, because a refusal is deleted only after everything it stood in for
exists.

1. Settle and file the derived/column split; narrow the published refusal's over-broad claim.
2. **Decision 3** — mint the weighted-contrast `method` vocabulary in § Statistical reporting.
3. Design and document the contrast record shape under a weight.
4. **Decision 4** — the corrected bound, argued against `Member`'s exactly-one invariant.
5. **Decision 5** — `resample.stratify_by` on a contrast.
6. Thread `weights` into `_compute_vs_baseline`, `_compute_declared_contrasts`, `_comparison_step_blocks`.
7. The weighted closure in the paired percentile path.
8. The record: `weighted_by` on the contrast entry.
9. The corrected path, per decision 4.
10. Weighted `paired_t_over_units` — the **general** case, off the payoff path, made honest.
11. The § Validation row the brief never counted, and the two sibling rows to re-word.
12. The three C configs exercised end to end against a real weighted contrast.
13. **Retire `E-DATA-WEIGHT-CONTRAST`** — its single emit site and its one § Errors row.
14. The owned prose sweep — by claim, over named files.
15. The dated count, per decision 6, in its own section.

---

## Out of scope, with the route

Clusters through contrasts — **H4b-2**, seven tasks, zero configs unblocked. The unpaired
constructions — **H4c**. `null_test` — **H4d**. `io.reuse_from` — unbuilt, unowned, and the reason
C1–C3's executable status stays unsettled after this slice.
