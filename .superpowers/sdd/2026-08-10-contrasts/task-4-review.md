# Task 4 review: `paired_t_over_units` and `cohens_dz`

## Verdicts

- **Spec compliance:** ✅
- **Task quality:** approved

## Analysis against the five aim points

1. **Delegation to `t_over_units`.** `paired_t_over_units` calls `t_over_units(diffs, confidence)` and only relabels `method` on the returned `Interval`. It does not recompute mean/variance/critical value itself, so it cannot drift from `t_over_units` — a future change to the Student's-t construction (e.g. a different critical-value source) is inherited automatically. Confirmed from the diff, not inferred from test agreement.

2. **`cohens_dz` denominator.** `variance = sum((d - mean) ** 2 for d in diffs) / (len(diffs) - 1)` — ddof = 1, identical formula/style to `t_over_units`'s own variance line. Hand-recomputed: diffs `[1,2,3,4]`, mean 2.5, sum of squared deviations = 2.25+0.25+0.25+2.25 = 5, sample variance = 5/3 = 1.666667, sd = 1.2909944, dz = 2.5/1.2909944 = **1.93649167** — matches the brief's and the test's constant exactly. Had ddof=0 been used instead, sd would be 1.1180340 and dz = 2.2360680 — a visibly different value, so the existing test (`pytest.approx(1.93649167, rel=1e-6)`) would catch a population/sample swap.

3. **The two `None` cases.** `len(diffs) < 2` returns `None` before any arithmetic (covers the "no dispersion describable" case with 0 or 1 diffs). Separately, `sd > 0 else None` catches zero-spread with `len >= 2` (test uses `[2.0, 2.0, 2.0]`, length 3, so it is not accidentally caught by the length guard — confirmed distinct code paths exercised). Division by zero is never reached.

4. **No `cohens_d`/derived-metric handling.** Function signature and body only take a flat `Sequence[float]` of per-unit diffs; nothing branches on metric provenance (derived vs. per-unit). Correct scope — that enforcement is Task 6/7's call site, not this function's job.

5. **Purity.** Diff touches only `stats.py` (math/`Interval`/`t_over_units`) and its test file. No new imports of `config`, `artifacts`, `runner`, `cli`, or filesystem APIs. `math` and `Sequence` typing already present/standard.

## Test evidence

- `test_the_interval_is_students_t_on_the_differences` — catches any reimplementation whose bounds diverge from `t_over_units`, e.g. wrong df, wrong critical value source, or an independent (buggy) mean/variance computation.
- `test_it_names_its_own_method` — catches forgetting to relabel `method`, which would silently make `paired_t_over_units` indistinguishable from `t_over_units` downstream (contract/provenance bug).
- `test_one_difference_has_no_interval` — catches a missing/incorrect `n < 2` guard in the paired wrapper (inherited from `t_over_units`, but confirms the wrapper propagates `None` rather than raising or fabricating an interval).
- `test_cohens_dz_is_the_mean_over_the_standard_deviation` — the load-bearing numeric test; as shown above it distinguishes ddof=0 from ddof=1 (2.236068 vs. 1.936492), so it would catch a population-vs-sample standard deviation swap. Hand-recomputed and confirmed correct.
- `test_cohens_dz_is_none_below_two_differences` — catches a missing/wrong length guard (e.g. `< 1` instead of `< 2`, which would attempt variance over a single point).
- `test_cohens_dz_is_none_when_every_difference_is_identical` — catches a missing zero-sd guard that would otherwise raise `ZeroDivisionError` or silently produce `inf`/`nan`. Confirmed it exercises a length-3 input, so it's testing the sd guard specifically, not the length guard.

No test directly asserts "this is implemented via delegation" (that property is only verifiable by reading the code, as the brief itself notes) — but the diff inspection above confirms the delegation is real, not incidental agreement.

## Style/interface conformance

- `Interval` used correctly as the frozen 3-field dataclass (`low`, `high`, `method`), not a tuple.
- Return types (`Interval | None`, `float | None`) match the brief's interface exactly.
- Line lengths within 100; no new imports beyond what's already used in the module; alphabetical import ordering preserved in the test file update.
- Report's stated verification (653 passed, ruff clean, mypy clean) is consistent with the diff's shape — no changes visible that would plausibly fail ruff/mypy strict (no bare `Any`, no untyped returns, `Sequence[float]` typing preserved).

## Minor notes (non-blocking)

- Docstrings quote `reference.md` § "How a metric becomes a number" and reference `cohens_d: null` for `r` — consistent with the spec's worked-example language; not verified against the doc text itself in this review since the task is a `stats.py`-only change, but nothing in the diff contradicts the four documents.
