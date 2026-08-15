# Task 1 review: the regression pin for the undeclared-`resample` shape

Reviewed `0f62ba0` (parent `eaf3605`) on `h4a-resample-honoured`. Tests only, +154 lines,
verbatim from the brief.

## Verdicts

- **Spec compliance: ✅** — with two exclusions named below, so the tick does not silently
  absorb them.
- **Task quality: findings** — 2 Important, 4 Minor. The two mutations the brief demanded do
  fail correctly; a third mutation, not demanded, passes green and should not.

## What was verified by mutation, not by reading

Every mutation was applied where the behaviour lives, `__pycache__` cleared between runs,
reverted **by editing in place**, and each revert confirmed **by behaviour** (re-running the
pins and, for the numeric ones, re-reading the produced values) plus a `diff` against a
pre-mutation copy.

| # | Mutation | Result |
|---|---|---|
| 1 | `cli.py` `derived_metric_draws = 2000` → `500` | **Both** pins fail on `assert 500 == 2000`. As claimed |
| 2 | `stats.py` `summarize_step` column branch `t_over_units(values)` → `percentile_over_units(values, 1, draws=2000)` | **Both** pins fail on `'percentile_over_units' == 't_over_units'`. As claimed |
| 3 | The real task-13 bug shape: `(doc.get("statistics") or {}).get("resample", {"draws": 777})` then `(_spec or {}).get("draws", 2000)` | **absent-key FAILS (777 ≠ 2000), explicit-null PASSES.** The two-test split is genuinely load-bearing |
| 4 | The mirror bug: `777 if "resample" in statistics else 2000` | **explicit-null FAILS, absent-key PASSES.** Both documents are distinguished, in both directions |
| 5 | `cli.py` derived-metric `seed=resample_seed_value` → `+ 1` | **Both pins PASS.** Derived `ci95` moved `[16.025, 23.025]` → `[15.825, 22.925]` undetected |
| 6 | `cli.py` column-contrast `diffs`: drop the subtraction, use `against_collapsed[k][metric_key]` alone | **Both pins PASS.** The contrast stops being a contrast and nothing notices |

Mutations 3 and 4 confirm the review's central question affirmatively: the `.get("resample",
DEFAULT)` vs `.get("resample") or DEFAULT` bug is caught, and only because the brief demanded
two separate documents rather than one parametrized case. That part of the design is sound and
the docstring's claim about it is accurate.

Trap 2 is genuinely handled. `_CONDITION_SCALED_STEP` produces real dispersion, verified by
running it: `col_contrast["delta"] = 19.5`, `cohens_d = 1.668`, `ci95 = [15.76, 23.24]` — not
the `Interval(0.0, 0.0)` / `cohens_d: None` degeneracy `_AGGREGATE_STEP` would have given.

Trap 1 is handled: the explicit-`null` test passes `correction` alongside `resample`, and both
pins assert `correction`, `correction_level`, `family_size` and `family`.

Tree left clean at `0f62ba0`: `git status` empty, `1691 passed, 2 xfailed`, `ruff check`
clean, `mypy` clean (42 files).

---

## Findings

### Important 1 — the fixture's numbers agree with the bug, and no numeric assertion exists

Mutations 5 and 6 both pass green. They are one gap, not two: **the pin has no numeric grip on
anything.** Every interval assertion is `ci95 is not None`; no `delta`, no bound, no width is
pinned anywhere in `_assert_undeclared_resample_shape`.

Two consequences, each proven:

- **A width-changing bug with the right method and the right draw count is invisible** (mut. 5).
  H4a's stated subject is "the method, draw count **and strata**" of the intervals. A strata bug
  that mis-stratifies an *undeclared* run yields `method: percentile_over_units`,
  `resample_draws: 2000`, and a different `ci95` — the pin cannot see it. The values are
  deterministic across runs (verified: `[16.025, 23.025]` reproduced exactly), so pinning them
  costs nothing.
- **The scale factors `{pearson: 1.0, spearman: 2.0}` make the per-unit difference numerically
  identical to the baseline column** — `i·2 − i·1 = i`. So the column contrast's `delta` (19.5),
  the column's `value` (19.5), the derived metric's `value` (19.5) and the derived contrast's
  `delta` (19.5) are the same number four times, and `col_contrast["ci95"]` is byte-identical to
  `column["ci95"]`. Mutation 6 exploits exactly this. This is the spec's own named trap — *"Draw
  counts and stratum levels need enough distinct values that each candidate wrong answer produces
  a different result"* — in a fixture that tasks 15 and 16 inherit as an interface.

**The remediation is two changes, and one alone does not work — verified.** Setting the spearman
scale to `3.0` with no new assertion leaves mutation 6 green (`method` is unchanged and
`cohens_dz` is scale-invariant: `39/2σ = 19.5/σ`). Adding a `delta` assertion at the shipped
`2.0` scale also leaves it green (correct and buggy deltas are both 19.5). Both together close
it: at scale `1.0/3.0` the correct `col_contrast["delta"]` is **39.0** and the buggy one is
**19.5**. Verified by running all four combinations.

Suggested: `{"pearson": 1.0, "spearman": 3.0, "kendall": 5.0}`, plus
`assert col_contrast["delta"] == pytest.approx(39.0)`,
`assert derived_contrast["delta"] == pytest.approx(39.0)`, and the two derived `ci95` bounds.

### Important 2 — the correction-level assertions are order-blind

```python
assert col_contrast["correction_level"] in (pytest.approx(0.05 / 2), pytest.approx(0.05 / 1))
levels = sorted(m["correction_level"] for m in (col_contrast, derived_contrast))
assert levels == [pytest.approx(0.025), pytest.approx(0.05)]
```

The first assertion accepts both values, so alone it constrains nothing. The second is a
`sorted()` over the pair, so it pins *that both levels occur* and never *which member gets
which*. Holm ranks on the point estimate over half the raw `ci95` width — precisely the quantity
H4a changes when it alters draws or strata — so a ranking swap is the expected symptom of a
regression here, and the pin is written to tolerate it.

The actual assignment is deterministic and stable across every configuration I ran:
`col_contrast = 0.05`, `derived_contrast = 0.025`. Pin them per member.

The spec's traps table ties the ranking mutation to *"a resample pass that walks every metric
block"*, i.e. task 12, and that reading is right — task 1 is not obliged to write that mutation.
But the spec's shape list does include *"Holm still ranks on `abs(delta)` over half the raw
interval width"* as part of the baseline, and an order-blind assertion does not pin it.

### Minor 1 — `_starter_step`'s docstring omits the brace-doubling rule its sibling states

`extra_step_source`'s paragraph ends with *"a literal `{` in it must be doubled unless it names
`step_name` itself."* `_starter_step` is `.format(pkg=pkg)`-ed at
`generators/experiment.py:82` and carries the identical hazard, but its paragraph says nothing
about it. `_CONDITION_SCALED_STEP` demonstrates the doubling, so nothing is broken today — but
a later task writing its own step source from only its own brief will hit it. One sentence.

### Minor 2 — undocumented precedence between `_starter_step` and `aggregate_returns`

The `_starter_step` block sits *after* the `aggregate_returns` block, so passing both silently
gives `_starter_step`'s source with `aggregate_returns`' `aggregate` patch still applied. The
docstring distinguishes the two parameters but never says which wins. Tasks 15/16 reuse this
helper.

### Minor 3 — `_CONDITION_SCALED_STEP` raises `KeyError` on an unlisted swept value

The scale lookup is a bare `[...]` over `{pearson, spearman, kendall}`. A later task sweeping
`analysis.method` over any fourth value gets a step failure, surfaced as failed units rather
than as a fixture error. `kendall` is present but unswept, so the constraint is invisible from
the pin itself.

### Minor 4 — the 5 seed repeats are degenerate

The probe shows `repeat_spread: {std: 0.0, n: 5, kind: seed}` — the step is seed-invariant, so
the repeat axis is degenerate in the same way `_AGGREGATE_STEP` was degenerate for contrasts,
one axis over. Not load-bearing for this pin, which asserts nothing about `repeat_spread`, but
it is inherited by tasks 15/16 along with the fixture.

---

## Answers to the two questions the review asked directly

**Does the pin protect `CLAUDE.md` § The worked example's numbers, or only their shape?**
Neither, strictly. The fixture is a synthetic 40-unit `pred = i·scale` table with no relation to
the 228-unit worked example, and the pin asserts no interval value at all. It protects method
names, `resample_draws`, key presence/absence, and the correction family's size — shape only.
The spec's bullet *"`CLAUDE.md` § The worked example's numbers … must not narrow"* is **not
owned by any task in the decomposition**, and task 1 does not discharge it. Worth assigning
before task 13 lands.

**What plausible task-13 bug would these tests not catch?** The `.get("resample", DEFAULT)` bug
the brief predicted **is** caught, in both directions (mutations 3 and 4). The ones that slip:

- Any change to the *derivation* of the resample seed for an undeclared run (mut. 5).
- A stratified draw wrongly applied to an undeclared run, if it keeps `method` and `n` (mut. 5's
  class).
- A resolution that returns `None` for the undeclared case and simply omits `draws=` at the
  `summarize_step` call — `summarize_step`'s own signature default is `draws: int = 2000`, so
  the observable output is unchanged and the pin passes. The outcome is still correct, so this
  is not a defect; but it does mean the pin cannot detect the loss of the explicitness
  `cli.py`'s own comment claims for the literal (*"a real, passed value rather than
  `summarize_step`'s own default taking effect unseen"*).

---

## Calibration notes

- The report's *"Concerns: None"* and its stated reasoning — *"not separately mutation-tested
  beyond the two mutations above, since the brief specifies exactly these two as the
  load-bearing pins"* — is what let mutation 6 through. The brief's two mutations test the two
  values task 13 will move; they were never going to test whether the *fixture* can distinguish
  a wrong answer. That is this repo's most-tracked defect class, and the report's own claim that
  the assertions were *"each checked once by hand to confirm … none is a tautology against a
  degenerate fixture"* is the overclaim: `col_contrast["cohens_d"] is not None` holds under a
  contrast that isn't a contrast.
- Pre-existing `resample_draws == 2000` pins at `tests/test_cli.py:2481`, `:4138` and `:6195`
  also fail mutation 1. The genuinely new coverage is the explicit-`null` **document** and the
  bundled shape assertion — not the draw count in isolation. The brief's framing of these tests
  as "the only baseline any later task can be compared against" is slightly stronger than the
  suite supports.
- The spec calls task 1 *"extend a pin, not write one"*; the implementation added two standalone
  tests instead. The brief specified them verbatim, so this is the brief's deviation, not the
  implementer's. No action.
- `ruff format --check` flags ~39 files repo-wide; pre-existing, out of scope, not raised.
