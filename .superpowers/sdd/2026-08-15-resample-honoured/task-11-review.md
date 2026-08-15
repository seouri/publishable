# Task 11 review — `resample_draws` for a column metric

**Spec compliance: ❌** — the invariant decision 2 rests on is stated unconditionally in both
`stats.py` and `spec-defects.md`, and it is false for a reachable column shape; and the defect
entry cites `reference.md` § Statistical reporting as saying something it does not say.

**Task quality: findings** (1 Critical, 3 Important, 2 Minor). The mechanics are sound — mutation
reproduced exactly, tree clean, the brief-defect catch is correct — but the deliverable of this task
*is* the proof, and the proof has a hole.

## Verified first (all confirmed independently)

- Mutation reproduces: `units.usable_weight` guard `<= 0` → `< 0`, `__pycache__` cleared →
  `[0]` and `[0.0]` FAIL with `ZeroDivisionError` at `stats.py:167`; reverted by in-place edit,
  8/8 pass again. `git diff --stat` shows only the reviewer's own `progress.md`.
- `uv run pytest` → **1762 passed, 2 xfailed**; `ruff check .` and `mypy` clean.
- The brief defect the implementer reports is **real and correctly diagnosed**: `summarize_step`'s
  `out[column] = {...}` carries `value`/`basis`/`n`/`ci95`/`method`/`correction` and no
  `resample_draws` key, and `tests/test_cli.py:6750` already asserts
  `"resample_draws" not in column`. Refusing to write the brief's present-tense sentence was right.
- The three-branch case analysis is exhaustive **over branches** as they stand after tasks 9 and 10
  (stratified / weighted / unweighted, plus the two `None` gates above them). It is not exhaustive
  over the value domain — see Critical.

## Critical

**C1. A reachable column shape has no defined mean, so the invariant is false as written.**
Non-finite values reach a column end to end: `coerce_scalars` accepts `float("nan")` and
`float("inf")` (verified directly), `_is_numeric` in `summarize_step` accepts them
(`isinstance(value, (int, float))`, bool excluded — finiteness never checked), and the column branch
passes them through. Today that already yields `value: NaN, ci95: [NaN, NaN]` via `t_over_units`;
once 12/14 wires `percentile_over_units` for columns, every draw's mean is `nan` and the record would
say `resample_draws: 2000` where the derived sibling on the same data says `0`.

A second instance of the same gap: `usable_weight` gates each weight finite and positive, but Σw over
the drawn subset can still overflow. `percentile_over_units([1,2,3,4], weights=[1e308]*4)` returns
`Interval(low=nan, high=nan)`. "Σw is strictly positive" is true; "so the weighted mean is defined"
does not follow.

**But `(Interval, int)` is not the fix, and the review should not conclude that.**
`percentile_over_units` has no per-draw survivor filter at all, so the tuple would return
`(Interval(nan, nan), 2000)` — the same false claim with an extra field. Decision 2's *conclusion*
(record the requested `n`, keep the bare `Interval`) survives; its *proof* does not.

Required: state the condition in both places — the invariant holds for **finite** column values and a
Σw that does not overflow — and record the non-finite-column gap as its own `spec-defects.md` entry
for 12/14 to route (reject non-finite recorded values upstream, or drop non-finite draws). An
unconditional guarantee in a docstring is precisely the failure class CLAUDE.md counts 12+ times, and
this task's entire output is a guarantee claim.

## Important

**I2. The `None` question is unanswered, and one of the two `None` paths is incoherent under the
ruling.** Neither the docstring nor the defect entry says what `resample_draws` reports when
`percentile_over_units` returns `None`. Concretely: a column refused by tasks 9/10's
all-strata-constant rule would write `resample_draws: 2000` beside `ci95: null` — a positive count
asserting evidence for an interval that was *refused*, which collides with `reference.md`'s three-way
distinction (`null` = never attempted, `0` = attempted and every draw degenerate, otherwise the
survivor count). The `draws < min_honest_draws` path happens to read correctly under requested-`n`
semantics (reference.md:2306 already covers "below the floor"), which sharpens it: the field is
coherent for one `None` path and incoherent for the other. Task 11 addressed neither, and it is the
question tasks 9 and 10 created for exactly this decision.

**I3. The defect entry cites `reference.md` for the opposite of what it says.** The entry closes
"…the two metric kinds carry the same field with subtly different provenance, which `reference.md`
§ Statistical reporting states." Line 2350 states the field is "recorded beside every derived metric
in `aggregated`" — columns are not mentioned. So the ruling *contradicts* the current sentence rather
than being stated by it, and under "the document changes first" the entry must name the
§ Statistical reporting amendment 12/14 owes. This is the spec-compliance trigger.

**I4. The new adversarial test's case 1 pins the divergent side of an inconsistency 9/10 created.**
`percentile_over_units([5.0]*4)` → `Interval(5.0, 5.0)`, a zero-width interval; the same data with
`strata=["a"]*4` → `None`. Case 1 asserts `got is not None` for the former, converting a latent
inconsistency into a defended one. Two consequences worth recording rather than silently accepting:
`percentile_over_units`'s own docstring still claims the ordering "makes the one-stratum case
reproduce the unstratified path digit for digit", which is now false for constant data; and 9/10's
refusal is narrower than `reference.md`'s honesty rule ("a zero-width 95 % interval is not"). Not
Critical — `t_over_units([5.0]*4)` is zero-width too, so the unstratified zero-width predates this
slice and is a broader question — but the pin should carry the caveat or be reworded.

## Minor

**M5. The adversarial set varies structure while holding the value domain constant.** All five cases
are ordinary finite floats differing only in strata/weights *shape* — the repo's own "varying config
shape when the property is about content" trap. Worth noting the pin is one list line from having
teeth: `assert got.low <= got.high` is `False` for `nan`, so adding `([nan, 1.0, 2.0, 3.0], {})` or
`([1,2,3,4], {"weights": [1e308]*4})` would have caught C1. The other two tests can fail (the weight
refusal is mutation-proven; the bare-`Interval` pin fails on a tuple return).

**M6. A perishable build claim inside a source docstring.** "today's build still refuses a declared
`resample` with `E-STATS-RESAMPLE-UNSUPPORTED`, and the recorded-column branch there carries no
`resample_draws` key at all" goes stale the moment 12/14 lands, in a file that task need not touch.
Flagged rather than charged: `units.py:1141` and `validate.py:5000` already do the same, so it is
house practice.

## Suggested minimum to clear ❌

1. Add the finiteness/overflow condition to the docstring and to the defect entry's ruling paragraph
   (C1), plus a separate defect entry for non-finite recorded values reaching a column interval.
2. Answer the `None` case explicitly in the defect entry, distinguishing the refusal path from the
   below-floor path (I2).
3. Replace the `reference.md` citation with the amendment it owes (I3).
4. Caveat or reword the constant-column case in the adversarial test, and add one non-finite case
   (I4, M5).
