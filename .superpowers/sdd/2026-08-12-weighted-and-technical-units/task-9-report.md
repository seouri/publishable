# Task 9 report — `n` gains `effective`, and the record carries `weighted_by`

**Status:** DONE_WITH_CONCERNS. One blocking hand-off for task 11 (below), one brief defect,
one infeasible test placement in the brief.

**Commits:** `2836af1` — *feat: report the effective n a weighted interval was computed at*;
`2cdd197` — *test: pin the derived metric's weighted_by and the four int parts of n*

**Suite:** `uv run pytest` → 1208 passed, 3 xfailed (was 1203 + 2). `ruff check` and `mypy` clean.
`ruff format` deliberately not run.

---

## What landed

**`runner.py`** — `attrition` gains `weights: dict[str, Any] | None = None` and its return widens to
`dict[str, float]`. All three return sites now go through **one** builder, `_counts(resolved,
completed, ineligible, failed, weights)`: three parallel dict literals is exactly how `effective`
reaches two sites and not the third, so the shape is decided in one place rather than guarded by a
test. `effective` is `kish_effective_n` over the **completed** units' weights, sorted for float
reproducibility, present only when `weights` is not `None`.

**`stats.py`** — `summarize_step`'s `counts` widened `dict[str, int]` → `dict[str, float]`, and the
two-route docstring updated to say `effective` arrives that way and why the annotation had to move.
**No other change was needed**: `n` is already `{**counts, "completed": ...}` in both the
recorded-column and the derived loop, and `weighted_by` already rides `beside_n`. The route task 6
decided was followed exactly; nothing new was invented.

**`cli.py`** — builds `weights = {u.key: u.attributes.get(weight_by) for u in roster}` when
`data.units.weight_by` is a non-empty string, passes it to **both** `attrition` call sites (the
condition's and each `report_by` level's), and puts `weighted_by` in `beside_n`.

**`reference.md`** — the owed dual listing for `E-DATA-WEIGHT-INVALID`: a new § Errors core raises
row phrased from the raise site (computing Kish's size or a weighted interval over a weight
`units.usable_weight` rejects), plus the "Raised at run time too, under the same code" clause on the
existing § Validation row, mirroring `E-DATA-MEASUREMENTS-COLLAPSE-TYPE`. No prose count governs the
raise-time table (checked), and the validate-time count did not move — no row was added there.

`run_record.py` was **not** touched, and the brief's file list is wrong to name it: its own comments
already say there is no `counts` parameter because `summarize_step` embeds `n` per metric, and
`assemble_run_yaml` copies `aggregated` through verbatim. Verified rather than assumed.

---

## ⚠️ BLOCKING HAND-OFF TO TASK 11 — the value is not weighted yet

**No task in this plan wires `weighted_t_over_units` (or a weighted mean) into the runner path.**
Task 8 built both in `stats.py`; task 10 builds the weighted percentile path in `stats.py`; task 11
retires the refusal; task 12 is consistency passes. Grep confirms `weighted_t_over_units` has no
caller outside `stats.py` and its tests.

So after this commit a weighted run would record `weighted_by: sampling_weight` and
`n.effective: 3.0` **beside an unweighted mean and an unweighted-df interval** — which is precisely
the bug task 8's own brief named ("a test asserting only that `weighted_by` was recorded would pass
against an implementation that stores the declaration and computes the unweighted interval — which
is the bug, not the fix").

It is **latent, not live**: `E-DATA-WEIGHT-UNSUPPORTED` is still in validate's five-field loop and
`command_run` returns `EXIT_WRONG` on `c.has_errors`, so no config declaring `weight_by` reaches the
runner today. **Task 11's commit is what turns it live.** By this slice's own task 6 ruling, retiring
a refusal while leaving the gap unrecorded is the forbidden outcome — so task 11 must either land the
estimator wiring or not retire the refusal.

I did **not** absorb the wiring: it needs decisions I would be inventing (whether core re-weights a
*derived* value — § Weighted samples says core hands the column to `aggregate` "so a derived metric
can weight itself", i.e. it must not; how the weighted percentile path interacts; whether a
`weighted_by` on a derived metric means anything). A ⚠️ comment at the `cli.py` wiring site names
what is missing, so the fact is durable in code and not only here.

**Carry forward for whoever does it:** `summarize_step` overrides `completed` per column precisely
because a condition-wide figure beside a ragged column's interval is a lie. Condition-wide
`effective` is consistent *today* (the interval is not weighted) and becomes that same lie the moment
it is — a column recorded for a subset of completed units gets an interval whose df comes from that
subset's weights, not from the `effective` printed beside it.

---

## Brief defects

1. **`tests/test_cli.py` placement is infeasible today.** Every `run.yaml` assertion in that module
   goes through `run_a_project` → `main(["run", ...])` → `command_run`, which validates first and
   returns before executing. `E-DATA-WEIGHT-UNSUPPORTED` is an *error*, so no weighted end-to-end run
   exists until task 11. The positive assertions therefore live in `tests/test_runner.py` (attrition)
   and `tests/test_stats.py` (the `counts` → `n` merge), which is where the behaviour actually is.
   The cli module carries the **negative** test (which is feasible and is the regression) plus one
   `xfail(strict=True)` pinning the end-to-end shape § Weighted samples prints — same device, and the
   same justification, as the two existing xfails in `test_sweep.py`/`test_contrasts.py`. Strict, so
   it XPASSes and fails the suite the moment task 11 lands: that is the hand-off made mechanical.
2. **`run_record.py` in the files list** — no change is required there (above).

## Decisions I made that the brief left open

- **`report_by` level blocks get both** `effective` (weights passed to the level's own `attrition`,
  so it is **recomputed over the stratum's units**) and `weighted_by` (a new `weighted_beside` dict,
  not the parent's `beside_n`). The existing comment withholding `beside_n` from a level is about
  `technical_n` specifically, and its reason is that `technical_n` is a whole-roster figure that would
  have to be *copied down*; Kish's size over a stratum is a different number computed from scratch,
  and `weighted_by` names a declaration that is as true of a subset as of the roster. Withholding it
  would leave a level block whose `n` carries `effective` with nothing beside it saying why.
  **Untestable end-to-end today** for the same reason as the rest of the cli wiring.
- **No pre-coercion and no filtering of weights.** `kish_effective_n` gates its own input against
  `units.usable_weight`; adding a check here would be the fourth notion this slice has three
  near-misses on. `weights` uses `.get(weight_by)` rather than `[...]` so a (core-defect) missing
  attribute reaches the gate as `E-DATA-WEIGHT-INVALID` instead of dropping a unit out of the
  denominator.
- **The raise window** is documented in `attrition`'s docstring rather than guarded: `attrition` sits
  *outside* `cli.py`'s containment around `summarize_step`, but `command_run` validates against the
  same roster it then resolves, so `run` cannot reach it with an unusable weight. It re-opens for
  `draft`/`resume` (H9), and the docstring says so.

## Mutation tests — three, separately, `__pycache__` cleared between, reverts verified by behaviour

| Mutation | Result |
|---|---|
| `effective` unconditional (`(weights or {}).get(k, 1.0)`) | 15 failures incl. `test_n_has_no_effective_key_without_weight_by` and the cli regression |
| `effective` over **resolved** instead of completed | `test_n_gains_effective_under_a_weighted_design` + the three-sites test FAIL |
| `weighted_by` set unconditionally in `cli.py` | `test_an_unweighted_run_grows_no_effective_and_no_weighted_by` FAILS |

Every probe has a control that must report. The positive fixture is built so the wrong denominator is
a *different number*, not a different direction: four completed units weighted 1/1/1/3 give Kish
exactly `36/12 = 3.0` (no float slack), while all five resolved give `256/112 = 2.2857…` and four
equal weights would give `4.0` — so "used resolved", "never computed Kish" and "returned the count"
are each killed by the number. The cli regression asserts `completed == 10` and a non-null derived
value as its control, so it cannot pass off an empty metric block.

## The cli wiring IS verified — by a throwaway probe, not by a committed test

Every `cli.py` line added here takes the `weight_by is not None` branch, which no committed test can
execute. So I removed `("weight_by", "E-DATA-WEIGHT-UNSUPPORTED")` from validate's five-field loop
**temporarily**, cleared `__pycache__`, ran, then restored it and verified the restore by behaviour
(`test_validate.py -k unsupported` → 13 passed; the cli test back to `xfail`). Not committed.

- `test_n_gains_effective_under_a_weighted_design` **XPASSed (strict)** — so the end-to-end wiring
  works, and the `xfail` really is a forcing function rather than an inert test failing for a second
  reason. Task 11 will see the suite fail the moment it retires the refusal.
- A wider probe (4 units weighted 1/1/1/3, `report_by: [cohort]` splitting them 1,1 | 1,3) printed:

  ```
  PRED  {resolved: 4, completed: 4, ineligible: 0, failed: 0, effective: 3.0}  sampling_weight
  TOTAL {resolved: 4, completed: 4, ineligible: 0, failed: 0, effective: 3.0}  sampling_weight
  LEVEL a pred/total {…, effective: 2.0}  sampling_weight  technical_n: absent
  LEVEL b pred/total {…, effective: 1.6}  sampling_weight  technical_n: absent
  ```

  So the derived branch carries both facts, and the **L2 level decision is provided rather than
  asserted**: each stratum's `effective` is genuinely recomputed (2.0 for equal weights, 16/10 = 1.6
  for 1 and 3, neither equal to the parent's 3.0), `weighted_by` is copied, and `technical_n` still
  is not. The derived-metric half of this is now a committed assertion inside the `xfail` test.

## Not touched

`partition_units`; `E-DATA-WEIGHT-UNSUPPORTED` (task 11); the worked example — `cohort-pilot`
declares no `weight_by` and nothing about it moved.
