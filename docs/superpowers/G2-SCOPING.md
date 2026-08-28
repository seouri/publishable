# G2 scoping — a correctable member for a condition's own metric

Read-only measurement against `main` at `b3d1d06`, on 2026-08-28. Every probe and grep below was
run against that tree, never remembered. Spec claims and build facts are labelled separately.

Chartered by [`spec-defects.md`](spec-defects.md)'s entry *a `compare: {to: constant}` hypothesis's
bound test is never answerable under a declared correction method*, filed 2026-08-28 during G1's
Task 9 and closed there as an honest `supported: null` rather than as the mechanism it asked for.
The [growth-chart feasibility analysis](../feasibility-growth-chart-literacy.md) then hit it with a
live config — E2's above-chance AUROC — which is what prompted re-opening it.

**Verdict: the fix is real, bounded, and touches the correction family's evidence. 7 tasks.** The
blocker is one discarded value: `percentile_of_derived` computes a pool of draws, reads an interval
off it, and returns only `(Interval, int)`. A `Member` needs that pool. Nothing else is missing.

**Baseline at `b3d1d06`:** `uv run pytest -q` → **3531 passed, 1 skipped, 2 xfailed**, 423 s.

---

## 0. What is true today, measured

`hypotheses.py:412` is the whole of the current behaviour:

```python
elif _is_counted(hyp, obs) and method != "none" and key not in by_key:
    corrected_unavailable = True
```

A counted hypothesis with no matching `Member` is routed through the same path a too-thin family
takes: `ci95_corrected: null`, and `supported: null` for any `evaluate_on: ci95_lower`/`ci95_upper`.
Measured by calling `evaluate` directly under `holm`, `bonferroni` and `none` during G1's Task 9
re-review, and unchanged since.

**Why no `Member` exists.** `cli.py:1653` builds one per comparison — a `vs_baseline` delta or a
declared contrast — and every one carries exactly one of `pool` / `diffs` / `sides`, which is *the
evidence the corrected interval is rebuilt from*. A `compare: {to: constant}` observation is not a
comparison between two conditions; it reads one condition's own `aggregated` value. No comparison,
no member.

## 1. The one thing missing, and it is one value

| Construction | Returns today | Needs |
|---|---|---|
| `stats.percentile_of_derived` (`:1574`) | `tuple[Interval \| None, int]` | the pool it read the interval off |
| `stats.percentile_of_derived_clustered` (`:1747`) | `tuple[Interval \| None, int]` | the same |
| `stats.percentile_over_units` (`:1148`) | `Interval \| None` | the same, for a recorded column |

All three compute a pool, sort it, call `interval_at`, and drop it. `Member.pool` is documented as
*"already sorted ascending — `interval_at` reads fixed ranks off it and does not sort"*, so the value
a member needs is **exactly** the value these functions already hold at the moment they return.

**19 call sites** name `percentile_of_derived` across `src/` and `tests/`; the unpaired form has
**one** production caller, `stats.py:3298`, inside `summarize_step`. The paired and unpaired
contrast forms are separate functions and are not in scope.

## 2. What this is NOT

- **Not a new statistic.** The pool already exists and the interval already comes off it. This
  slice moves a value that is computed and thrown away.
- **Not a change to what is counted.** `_is_counted` and `family_shape` are untouched: the
  hypothesis is already in the family and already inflates every other member's level. What changes
  is that it becomes correctable rather than only counted.
- **Not the cross-run family.** That is a separate open entry and stays open.
- **It IS partly a `t`-interval story, and this scoping first said otherwise.** The bullet here
  originally read *"a condition's own metric under no declared `resample` has a `t` interval and no
  pool at all, so that case must stay `corrected_unavailable`"* — reasoned from `Member.pool` without
  reading `correction.py:349`, whose own docstring says **"What decides the construction is which
  field the member carries, not what kind of metric it is."** A `t` interval is rebuilt from
  `diffs`, exactly, at the smaller α. A **recorded column** with no resample therefore has evidence
  and is correctable; only a **derived** metric with no resample has none — and that one has no raw
  interval either, so there is nothing to correct. Corrected before any task ran; the design's
  Decision 1 carries the four-case table.

## 3. The risk, named

**The correction family's evidence is the most load-bearing structure in this project**, and this
slice changes what feeds it. Three specific hazards, each already a rule somewhere:

1. **`Member.__post_init__` requires exactly one of `pool`/`diffs`/`sides`.** A new member built
   with the wrong one, or with two, is refused at construction — which is the guard working, and a
   slice that loosened it to make its own case fit would be removing the check that protects every
   other member.
2. **A pool from a *different* construction than the raw interval.** `cli.py:1644`'s comment records
   this exact defect being caught once: a column contrast under a declared resample that kept
   `diffs` got "a `ci95` from a percentile and a `ci95_corrected` from `paired_t_over_units`.
   Nothing raises and no reader can tell." The same trap is live here.
3. **Bit-stability.** Every existing corrected bound must be byte-identical after this slice. A
   guard pin over a completed run's `run.yaml` is the direct question, and it should be captured
   *before* anything moves.

## 4. Decomposition — 7 tasks

| # | Is |
|---|---|
| 1 | Capture the bit-stability oracle: a completed run's `run.yaml` at `b3d1d06`, corrected bounds included |
| 2 | `percentile_of_derived` and its clustered sibling return the pool; every call site updated; no behaviour change |
| 3 | `percentile_over_units` does the same for a recorded column |
| 4 | `summarize_step` carries the pool out to `cli.py` |
| 5 | `cli.py` builds a `Member` for a condition's own metric, under a declared `resample` only |
| 6 | `hypotheses.py`'s `corrected_unavailable` branch narrows to the no-pool case; the `spec-defects.md` entry is amended |
| 7 | Whole-branch re-run, the consistency passes, and the oracle re-checked |

**Task 1 is not ceremony.** This project's own record says a guard pin captured after the change is
a pin over the change.

## 5. What is NOT in this slice

The refusals stay refused. The cross-run correction family stays open. `evaluate_on: observed`'s
behaviour does not change — correction reaches a verdict only through a bound, and that is a rule
this slice has no reason to touch.
