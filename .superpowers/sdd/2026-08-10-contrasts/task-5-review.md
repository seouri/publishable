# Task 5 review: `paired_percentile_of_derived`

Reviewed from `review-23c830a..ddf2769.diff` at commit `ddf2769`. The working tree was
not touched and the suite was not re-run (658 passed / ruff clean / mypy clean, per the
reviewer's own prior run on this commit).

**Spec compliance: ✅**
**Task quality: findings** (2 Important, 1 Important test gap, 4 Minor)

---

## Spec compliance

| Requirement | Where | Verdict |
|---|---|---|
| One draw over the intersection applied to both sides | `src/publishable/stats.py:270-273` | ✅ a single `drawn` list builds both tables |
| RNG consulted once per draw, not twice | `stats.py:270` — the only `rng.` call in the function | ✅ |
| Method string `paired_percentile_over_units` | `stats.py:287`; matches `docs/reference.md` § Interval constructions | ✅ |
| No second copy of the rank arithmetic | `stats.py:285` calls `_percentile_ranks` | ✅ |
| No second copy of the survivor floor | `stats.py:282` calls `min_honest_draws` | ✅ |
| Survivor count returned always, including on `None` | `stats.py:283, 288` | ✅ |
| `< 2` keys returns `(None, 0)` | `stats.py:264-265` | ✅ matches the sibling |
| Degenerate draw = `None` / `nan` / raise, either side | `stats.py:271-280` | ✅ by inspection (see I2 for the test gap) |
| Purity — no filesystem, no `config`/`artifacts`/`runner`/`cli` at runtime | `stats.py:1-25` imports unchanged by this diff | ✅ (`runner` stays under `TYPE_CHECKING`) |
| `Interval` used as a frozen 3-field dataclass, not a tuple | `stats.py:287` keyword-constructed | ✅ |
| Style — line length, `×`, no new deps | whole diff | ✅ |

The construction is the specified one. Nothing here is the defect the task was written
to catch.

---

## Findings

### Important 1 — the `try` is wider than the sibling's, and swallows key errors

`src/publishable/stats.py:271-275`

```python
try:
    a = compute(_unit_table_from_rows([{"unit": k, **of[k]} for k in drawn]))
    b = compute(_unit_table_from_rows([{"unit": k, **against[k]} for k in drawn]))
except Exception:  # a degenerate draw, not a fault; see percentile_of_derived
    continue
```

`percentile_of_derived` deliberately builds its table *outside* the `try` and wraps only
the `compute` call. Its docstring argues the point at length: a raise is treated as a
degenerate draw because a *template's* `aggregate` may legitimately raise on a
zero-variance resample. Table construction is not that; it is core's own code.

Here the dict lookups `of[k]` / `against[k]` and both `_unit_table_from_rows` calls sit
inside the `try`. `keys` is caller-supplied, so a key absent from either side — a
`paired_keys` regression, a `within` stratum applied to one side only, a caller passing
the union instead of the intersection — raises `KeyError` on every iteration and the
function returns `(None, 0)`: byte-identical to "the resample was attempted and every
draw was degenerate", which is precisely the distinction the sibling's docstring says
the survivor count exists to preserve. The sibling would surface the same bug as a
`KeyError`.

Fix: hoist both table constructions above the `try`, leaving only the two `compute`
calls inside.

```python
table_of = _unit_table_from_rows([{"unit": k, **of[k]} for k in drawn])
table_against = _unit_table_from_rows([{"unit": k, **against[k]} for k in drawn])
try:
    a = compute(table_of)
    b = compute(table_against)
except Exception:
    continue
```

### Important 2 — the degenerate-draw path the brief singled out is untested

`tests/test_stats.py:1125-1175`

Aim point 3 of the task is specifically that "a failure on *either* side drops the draw
rather than being half-counted." The implementation gets this right. Nothing pins it:

- No test uses a `compute` that **raises**.
- No test uses a `compute` that returns **`nan`**.
- No test makes **one side** fail while the other succeeds.
- The only degenerate test, `test_below_the_survivor_floor_there_is_no_interval_paired`
  (`tests/test_stats.py:1169-1175`), uses `lambda t: None` — total failure on both sides.

A refactor that moved the `try` to wrap only `a`, or that replaced `a is None or b is
None` with `a is None`, would pass all five new tests. Two cheap additions close it: a
`compute` that returns `None` only when the table's mean exceeds some threshold (so
survivors are partial and the returned count is between 0 and `draws`), and a `compute`
that raises on one side's column but not the other's.

### Important 3 — the discarded constant-offset fixture was the *better* discriminator

`tests/test_stats.py:1135-1136`, and the report's § "Fixture defect found in the brief's
Step 1 test code"

The implementer's diagnosis is empirically correct — verified independently here by
replaying the exact draw sequence (`random.Random(seed).randrange(60)`, 2000 draws,
n = 60):

| seed | rank 49 | rank 1949 | width | `low < 0.5 < high` |
|---|---|---|---|---|
| 7 | `0.5` | `0.5` | `0.0` | False |
| 99 | `0.5` | `0.5` | `0.0` | False |

So on the brief's original fixture a correct paired implementation returns
`Interval(0.5, 0.5)`, the strict-bracket assertion fails, and seed 7 equals seed 99. The
report is right on all three counts, and right that no assertion rewrite rescues the
seed test.

But the conclusion drawn was to *replace* the fixture, and the constant fixture is the
sharpest paired-versus-independent test available anywhere in this suite. Under a
correct implementation the width is exactly `0.0`; under independently-drawn sides it is
≈12.4 — an unbounded discriminator ratio, against the 17.5× margin the alternating
fixture leaves (below). And zero-width **is** correct behaviour, not an artifact: a
difference with no sampling variability has a point-mass bootstrap distribution, so
every percentile of it coincides. That is a property worth asserting in its own right.

The brief needed both fixtures. Recommended addition, keeping the alternating fixture
where it is:

```python
def test_a_difference_with_no_sampling_variability_has_no_width():
    """Every unit differs by exactly 0.5, so one draw applied to both sides gives
    0.5 on every resample: the bootstrap distribution is a point mass and every
    percentile of it coincides. Drawing the two sides independently instead gives
    a width of ≈12.4 here, so this is the sharpest paired-vs-independent test in
    the file — sharper than the inequality in the narrowness test above."""
    of = {f"u{i}": {"m": float(i) + 0.5} for i in range(60)}
    against = {f"u{i}": {"m": float(i)} for i in range(60)}
    got, used = paired_percentile_of_derived(of, against, sorted(of), _mean_m, seed=7)
    assert got.high - got.low < 1e-9
    assert used == 2000
```

Use the tolerance rather than `got.low == got.high == 0.5`. Exact equality happens to
hold today, but only because the ±3.55e-15 rounding tails (26 draws each side, see
Minor 4) fall outside ranks 49 and 1949 — a fact contingent on n = 60, draws = 2000, and
the magnitude of the `i` values. The tolerance encodes the intent; the equality encodes
a rank-block accident.

---

## The narrowness test as evidence

`tests/test_stats.py:1125-1142`

The margin is very large. On the alternating fixture the per-unit difference is 1.0 for
even `i` and 0.0 for odd, so the resampled difference is `Binomial(60, ½)/60`, sd
≈ 0.0645, width ≈ 0.25. Each side's own mean has sd ≈ 17.3/√60 ≈ 2.23, width ≈ 8.7, so
`independent_width / 4` ≈ 4.39. **0.25 against a 4.39 threshold: a 17.5× margin**, in
agreement with the reviewer's measured 0.2500 / 17.5500.

What it catches:

- Two independent draws (the target defect) — ≈12.4, fails. Confirmed twice by the
  implementer via swap-and-revert, once against each fixture.
- One side resampled and the other computed on the full roster — ≈8.7, fails.
- A fresh `random.Random(seed)` per side inside the loop — degenerate, fails.

What it does **not** catch, and the reason it is acceptable:

- A partially-paired implementation that shares the draw but rebuilds one side from
  `sorted(drawn)`. Sorting preserves the multiset, and `_mean_m` is order-insensitive,
  so the width is unchanged. This only diverges for an order-sensitive `compute`, and
  order-sensitivity is something both `paired_keys` (`stats.py:444-445`) and
  `_unit_table_from_rows` (`stats.py:747-757`) already argue the module deliberately
  does not depend on. No test pins row-order alignment between the two tables; given
  those two docstrings, that is a defensible omission rather than a gap.
- Any per-draw defect small enough to stay under a 17.5× margin. The recommended
  zero-width test (Important 3) is the answer to this: it leaves no margin at all.

Pinned elsewhere in the five tests: the method string
(`tests/test_stats.py:1154-1158`), seed reproducibility and seed sensitivity
(`1159-1168`), and the survivor floor at its extreme (`1169-1175`). The floor's
*boundary* (survivors just below vs. just above `min_honest_draws`) is not exercised for
the paired function, but `min_honest_draws` and `_percentile_ranks` are shared code with
their own tests, including the off-by-one regression test at `tests/test_stats.py:1108`,
so a second copy of that coverage would be duplicative.

---

## Minor

1. **`nan` handling is spelled differently from the sibling.** `stats.py:278-279` computes
   `float(a) - float(b)` and checks `math.isnan(diff)`; `percentile_of_derived` checks
   `isinstance(value, float) and math.isnan(value)` per side. Equivalent for `nan`, since
   it propagates through subtraction. They differ on `±inf`: two equal infinities give
   `nan` here and are dropped, where the sibling would keep them. Immaterial in practice,
   but a one-line comment saying the check is deliberately on the difference would stop a
   future reader "harmonising" it in the wrong direction.
2. **`keys` order is caller-supplied.** The sibling sorts internally (`keys =
   sorted(collapsed)`); this function trusts its argument. Determinism therefore rests on
   `paired_keys` returning a sorted list, which it does and documents
   (`stats.py:444-445`). Worth one docstring line — "`keys` is assumed sorted, as
   `paired_keys` returns it" — since the seed-reproducibility test would not catch a
   caller that passed a set-ordered list.
3. **The docstring is thin by this module's standards.** Four lines against the sibling's
   forty. The deferral (`see percentile_of_derived`) is reasonable, but the two facts a
   reader most needs here — why the survivor count is returned even on `None`, and why a
   raise is a dropped draw — live only in the sibling. One cross-reference sentence naming
   both would suffice.
4. **The report's derivation of the zero-width result is stated wrongly, though its
   conclusion is right.** It says the paired construction makes "`mean(0.5 over drawn) ==
   0.5` identically." The code computes a *difference of means*, not a *mean of
   differences*, so the raw draws are not identically 0.5: the census over seed 7 is
   `-3.55e-15 × 26`, `0.0 × 1948`, `+3.55e-15 × 26`. The interval endpoints are exactly
   0.5 only because both tail blocks are smaller than the 50 draws that separate rank 49
   from the end. The conclusion survives; the mental model behind it does not, and it is
   the reason the recommended test in Important 3 needs a tolerance.

---

## Judgment on the fixture change

**Does the replacement still discriminate?** Yes, with room to spare: 0.25 against a 4.39
threshold, and ≈12.4 for the independent spelling — re-verified by the implementer
against the new fixture specifically, which was the right instinct, since changing test
data can silently destroy a discrimination already proved.

**Was zero-width the correct behaviour, making the brief's assertion wrong rather than
the fixture?** Yes. A difference with no sampling variability has a point-mass bootstrap
distribution, and every percentile of a point mass coincides; `Interval(0.5, 0.5)` is the
honest answer, not a degenerate one to design around. The brief's strict-bracket
assertion was unsatisfiable against correct behaviour and its seed-inequality was
unsatisfiable in principle. So the two assertions were wrong, not the data. The
implementer needed the alternating fixture for the bracket and seed tests — that part is
correct and necessary — but should have *added* it rather than replaced with it, keeping
the constant fixture under an assertion that matches what it actually demonstrates.

## Re-review

Scope: verify the fix diff (`review-70c6f5c..a79829d.diff`) against the three findings only.

1. **The `try` was too wide — ADDRESSED.** `table_a`/`table_b` are now built via `_unit_table_from_rows` before the `try` block; the `try` wraps only `a = compute(table_a); b = compute(table_b)`, matching `percentile_of_derived`'s pattern of wrapping only `compute`. A `KeyError` from `of[k]`/`against[k]` now surfaces rather than being swallowed.

2. **Degenerate handling was unpinned — ADDRESSED.** Four new tests pin the behavior: `test_a_raising_compute_is_treated_as_degenerate_not_propagated_paired`, `test_a_nan_compute_is_treated_as_degenerate_paired`, `test_a_one_sided_raise_drops_the_whole_draw_not_half`, and `test_a_one_sided_none_drops_the_whole_draw_not_half`. The two one-sided tests fail every 4th call on the `against` side only and assert `used == draws // 2`, which discriminates a narrowed-to-one-side `try` or an `a is None`-only check without needing to reintroduce the regression manually.

3. **The constant fixture should have been added, not replaced — ADDRESSED.** `test_a_constant_offset_gives_a_genuinely_zero_width_interval` was added (asserts `got.high - got.low < 1e-9`), and the original alternating fixture (`test_the_paired_interval_is_narrower_than_two_independent_draws`, line 1127) is untouched, along with its bracket test (`test_the_interval_brackets_the_observed_difference`) and seed-inequality test (`test_the_same_seed_reproduces_and_a_different_one_does_not_paired`).

**New breakage:** none found. Hoisting table construction outside the `try` does not change ordinary-path behavior — same values are computed, just constructed once instead of inline. The new degenerate tests use plain float dicts for `m`, not depending on `UnitTable`'s `None`-for-missing-column semantics.
