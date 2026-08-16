## Task 12: Refuse what has no construction, then retire both codes

### Two refusals, not one — and the second was found by task 10

**The clustered contrast family.** § Statistical reporting extends the `_clustered` suffix to the **contrast** constructions — `paired_*` and the unpaired forms, "jointly across both sides when paired". Those do not exist, so retiring `E-DATA-CLUSTER-UNSUPPORTED` without addressing it makes every clustered `vs_baseline` delta a wrong number.

**The clustered derived-metric draw.** Task 10 found that my earlier brief conflated two functions. `percentile_over_units` — which task 10 made cluster-aware — is reached only through `statistics.resample`, still refused by `E-STATS-RESAMPLE-UNSUPPORTED`. The interval that runs **unconditionally** is `percentile_of_derived`, driven by `cli`'s hard-coded `derived_metric_draws = 2000`, and **its clustered form does not exist**. Verified: `percentile_over_units` has zero callers outside `stats.py`; `percentile_of_derived` has one.

Exposure is narrow but real: the shipped `generic` template does not override `aggregate`, so only a **user-written template that derives a metric** reaches it. **Ruled by the user: refuse the combination rather than growing the construction here.**

**Both refusals follow H3a's `E-DATA-WEIGHT-CONTRAST` precedent**, which retired a broad refusal and minted a narrow one for the combination it had just made reachable but could not yet compute. H4 owns lifting both, alongside the `_clustered` family it already owns.

**Measure each blast radius before writing the guard.** H3a's implementer found that gating on the *resolved family* (`comparisons > 0`) rather than on the declaration was both narrower and wider in the right places — a bare `sweep.baseline` produces no comparison and must stay legal. Ask the same question of the derived refusal: **what does "returns derived metrics" mean at validate time**, when `aggregate` is user code core never inspects? If it cannot be known before the run, say so and say where the refusal has to live instead.

### Then: the retirements

### The retirement details


**Files:** Modify `src/publishable/validate.py`, `src/publishable/replication.py`, `docs/reference.md`; Test `tests/test_validate.py`

§ Statistical reporting extends the `_clustered` suffix to the **contrast** constructions — `paired_*` and the unpaired forms, *"jointly across both sides when paired"*. Those do not exist, so retiring `E-DATA-CLUSTER-UNSUPPORTED` without addressing it makes every clustered `vs_baseline` delta a wrong number.

**Mint a narrow temporary refusal**, exactly as H3a did with `E-DATA-WEIGHT-CONTRAST` and H2 with `E-SWEEP-SAMPLE-BASELINE`. **Measure the blast radius first**: H3a's implementer found that gating on the *resolved family* (`comparisons > 0`) rather than on the declaration is both narrower and wider in the right places — a bare `sweep.baseline` produces no comparison and must stay legal. Reuse that shape and say what you measured.

Then the retirements. Both refusals go; § The one config file's prose count goes **nine → seven**; and `E-REPL-FOLD-STRATIFY-UNSUPPORTED`'s removal is the ordering flip task 6 pinned.

- [ ] **Step 1–6:** The refusal with its blast-radius measurement and registry rows; both retirements; **grep every tracked `*.md` for both retired codes and prove the grep can fail** against one that exists; commit.

---

