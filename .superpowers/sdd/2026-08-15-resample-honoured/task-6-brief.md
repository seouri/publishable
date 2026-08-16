## Task 6: The comparisons-only lower bound on `n`, and the filed residue

**Files:** Modify `src/publishable/validate.py`, `docs/reference.md`, `docs/superpowers/spec-defects.md`. Test `tests/test_validate.py`.

**Interfaces:**
- Consumes: `validate._check_resample(doc, roster, c)` (Tasks 4–5); `sweep.expand(doc) -> list[Condition]`; `contrasts.resolve_contrasts(doc, conditions)`; `stats.min_honest_draws(confidence)`; `correction.ALPHA`.
- Produces: `W-STATS-RESAMPLE-FAMILY`.

**What cannot be built, and why the plan says so rather than deferring it.** The old scoping wanted `validate` to bound `n` against the family size, which `correction.family_shape` computes as `comparisons × metrics`. **`metrics` is unknowable at validate time by design.** It is `len({(m.step, m.metric) for m in members})`, and `cli` builds a `Member` per metric per comparison *after every execution has run*, from (a) recorded columns, which come from `io.record` calls inside user step code, and (b) `aggregate`'s returned keys, which come from user template code. Neither is declared anywhere in the config: `envelope.LEAF_TYPES` has no `metrics` path, `parameter_spec` declares parameters, and `hypotheses` names only the metrics a user chose to pre-register. Core "never inspects the body of user Python" (CLAUDE.md, greenfield only). So the full bound needs a capability core refuses to have.

**What can be built.** `comparisons` *is* resolvable — `contrasts.resolve_contrasts` already runs at validate time, and `E-DATA-WEIGHT-CONTRAST` already reads the resolved count. With `k` comparisons and at least one metric each, Holm's tightest level is `ALPHA / k` and the corrected interval needs `min_honest_draws(1 - ALPHA/k)` draws. A warning at that bound is **always true when it fires and silent when it might not be**. Exact values: `k=1 → 80`, `k=2 → 160`, `k=3 → 240`, `k=4 → 321`, `k=5 → 400`.

**Gate on the correction method.** `fdr_bh` implies no per-comparison level at all (`correction._level_for` returns `None`), and `none` corrects nothing; under either, `ci95_corrected` is null regardless of `n` and this warning would be a false positive. `cli` treats an unset `statistics.correction` as **holm**, so unset is in scope.

**Re-derive `conditions`, do not hoist.** `_check_sweep`, `_check_contrasts` and `_check_hypotheses` each call `expand(doc)` behind their own `try/except Exception: conditions = []` guard — three existing precedents. The `fold_basis` hoist in `validate_config` exists because `_check_replication` bounds `k` against a number and `_check_sweep` sizes a budget from the same number, and "a `k` checked against one number while the budget counts another is the drift a single derivation removes". Nothing here is bounded against `comparisons`; it only sets a warning threshold. Re-derivation with the same guard is the smaller change and matches three siblings.

- [ ] **Step 1: Write the failing test** — append to `tests/test_validate.py`:

```python
def _resample_family_config(write_config, *, n, correction, levels):
    return write_config(
        {
            "data.units": {"from": "index.csv", "key": "patient_id"},
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "grid": {"analysis.method": levels},
            },
            "statistics": {"correction": correction,
                           "resample": {"method": "bootstrap", "n": n}},
        }
    )


def test_a_resample_n_too_small_for_the_comparison_family_warns(write_config):
    """Three comparisons put Holm's tightest level at ALPHA/3, whose interval
    needs `min_honest_draws(1 - 0.05/3)` = 240 draws. `n: 200` clears the 80-draw
    floor and still cannot support the corrected interval, which is the whole
    gap this warning covers.

    The metric count is deliberately NOT in the bound: `correction.family_shape`
    derives it from `Member`s built after the run out of `io.record` keys and
    `aggregate`'s return, neither of which the config declares, and core never
    inspects the body of user Python. So this is a LOWER bound — always true when
    it fires."""
    found = codes(
        _resample_family_config(
            write_config, n=200, correction="holm", levels=["spearman", "kendall", "theil"]
        )
    )
    assert "W-STATS-RESAMPLE-FAMILY" in found
    assert "E-STATS-RESAMPLE-N" not in found  # 200 is above the 80 floor


def test_the_family_bound_is_silent_when_n_clears_it(write_config):
    """The positive companion to the test above, and the one that makes the
    threshold real rather than a warning that always fires: the same three
    comparisons with `n: 240` — exactly `min_honest_draws(1 - 0.05/3)` — are
    silent. 239 and 240 is the boundary pair."""
    assert "W-STATS-RESAMPLE-FAMILY" in codes(
        _resample_family_config(
            write_config, n=239, correction="holm", levels=["spearman", "kendall", "theil"]
        )
    )
    assert "W-STATS-RESAMPLE-FAMILY" not in codes(
        _resample_family_config(
            write_config, n=240, correction="holm", levels=["spearman", "kendall", "theil"]
        )
    )


def test_the_family_bound_scales_with_the_comparison_count(write_config):
    """One comparison needs 80 draws and three need 240, so an `n: 100` that is
    fine under one is not under three. A bound that read a constant rather than
    the resolved family passes one of these and fails the other."""
    assert "W-STATS-RESAMPLE-FAMILY" not in codes(
        _resample_family_config(write_config, n=100, correction="holm", levels=["spearman"])
    )
    assert "W-STATS-RESAMPLE-FAMILY" in codes(
        _resample_family_config(
            write_config, n=100, correction="holm", levels=["spearman", "kendall", "theil"]
        )
    )


@pytest.mark.parametrize("correction", ["none", "fdr_bh"])
def test_the_family_bound_is_not_reported_where_no_level_exists(write_config, correction):
    """`fdr_bh` implies no per-comparison level (`correction._level_for` returns
    `None`) and `none` corrects nothing, so under either `ci95_corrected` is null
    whatever `n` is and this warning would be a false positive."""
    assert "W-STATS-RESAMPLE-FAMILY" not in codes(
        _resample_family_config(
            write_config, n=100, correction=correction,
            levels=["spearman", "kendall", "theil"],
        )
    )


def test_the_family_bound_applies_when_correction_is_unset(write_config):
    """`cli` reads `(statistics.correction) or "holm"`, so an unset correction is
    holm and its family is corrected. A check gated on the key being present
    would leave every generated-but-edited config unwarned."""
    path = write_config(
        {
            "data.units": {"from": "index.csv", "key": "patient_id"},
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "grid": {"analysis.method": ["spearman", "kendall", "theil"]},
            },
            "statistics": {"resample": {"method": "bootstrap", "n": 100}},
        }
    )
    assert "W-STATS-RESAMPLE-FAMILY" in codes(path)
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_validate.py -k family_bound or too_small_for_the_comparison -x`. Expect the four positive assertions to fail on the missing code; the two negative-assertion tests pass vacuously and are controls whose value comes from their positive siblings.

- [ ] **Step 3: Implement** — in `src/publishable/validate.py`, append to `_check_resample` (after the `stratify_by` loop), and add `from publishable.correction import ALPHA` to the imports:

```python
    # The comparisons-only lower bound. Holm's tightest level is `ALPHA / m` at
    # rank 1, and a corrected interval is read off the SAME pool the raw one was
    # (`correction.interval_at`), so a pool below `min_honest_draws(1 - level)`
    # yields `ci95_corrected: null` with only `W-STATS-CORRECTED-THIN` at run
    # time to say why. `m` is `comparisons × metrics` and the metric count is
    # unknowable here BY DESIGN — `correction.family_shape` derives it from
    # `Member`s built after the run, out of `io.record` keys and `aggregate`'s
    # return, and core never inspects the body of user Python. So this bounds
    # against `comparisons` alone: always true when it fires, silent when it
    # might not be. The residue — a config with many metrics that still nulls
    # every corrected bound — is filed in `spec-defects.md` as a run-time
    # disclosure that already exists, not a check to build.
    #
    # `expand(doc)` re-derived behind the same guard `_check_sweep`,
    # `_check_contrasts` and `_check_hypotheses` each use, rather than hoisted
    # into `validate_config` the way `fold_basis` is: that hoist exists because
    # two checks BOUND declarations against one number and must not disagree,
    # where this only sets a warning threshold.
    correction_method = statistics.get("correction") or "holm"
    # `fdr_bh` implies no per-comparison level at all and `none` corrects
    # nothing, so under either `ci95_corrected` is null whatever `n` is and this
    # would be a false positive. Unset is `holm`, the same default `cli` applies.
    if correction_method not in ("holm", "bonferroni"):
        return
    if not isinstance(n, int) or isinstance(n, bool) or n < floor:
        return  # already refused above, or defaulted; nothing to bound
    try:
        conditions = expand(doc)
    except Exception:
        conditions = []
    try:
        comparisons = len(resolve_contrasts(doc, conditions))
    except (TypeError, KeyError, AttributeError, ValueError):
        comparisons = 0
    if comparisons < 1:
        return
    needed = min_honest_draws(1.0 - ALPHA / comparisons)
    if n < needed:
        plural = "" if comparisons == 1 else "s"
        c.warn(
            "W-STATS-RESAMPLE-FAMILY",
            "statistics.resample.n",
            f"is {n}, and this design resolves to {comparisons} comparison{plural}, so "
            f"`{correction_method}` puts the tightest corrected level at "
            f"{ALPHA / comparisons:.5f} — an interval at that level needs at least "
            f"{needed} draws, so `ci95_corrected` would be null rather than reported "
            "too narrow. This is a lower bound: the family is comparisons × metrics "
            "and the metric count is not knowable before the run, so the real "
            "requirement is at least this",
        )
```

  `expand` and `resolve_contrasts` are already imported at the top of `validate.py` (used by `_check_sweep`); confirm with `grep -n "^from publishable.sweep import\|^from publishable.contrasts import" src/publishable/validate.py` and add only what is missing.

  (b) `docs/reference.md` § Warnings core reports:

```markdown
| `statistics.resample.n` is below the draw count the resolved comparison family's tightest corrected level needs, under `holm` or `bonferroni` — a **lower** bound, since the family is comparisons × metrics and the metric count is not knowable before the run | `W-STATS-RESAMPLE-FAMILY` |
```

  And a § Validation row beside *Resample draws are honest*:

```markdown
| Resample draws fit the family | `statistics.resample: {n: 200}` over 3 comparisons under `holm` — the tightest corrected level is 0.01667 and needs 240 draws, so `ci95_corrected` would be null (warning) |
```

  (c) `docs/superpowers/spec-defects.md` — append a new section:

```markdown
## A validate-time `comparisons × metrics` bound on `resample.n` cannot be built

Found while scoping H4a (2026-08-15, `eaf3605`). `H4-SCOPING.md`'s trap 1 asked `validate` to
bound `statistics.resample.n` against the correction family, which `correction.family_shape`
computes as `comparisons × metrics`.

**The metric count is unknowable at `validate` time by design.** `family_shape` reads
`len({(m.step, m.metric) for m in members})` from `Member`s `cli._comparison_step_blocks` builds
*after every execution has run*, out of (a) recorded columns, which come from `io.record` calls
inside user step code, and (b) `aggregate`'s returned keys, which come from user template code.
Neither is declared anywhere in the config — `envelope.LEAF_TYPES` has no `metrics` path,
`parameter_spec` declares parameters, and `hypotheses` names metrics only for the ones a user
pre-registered. `CLAUDE.md`'s greenfield invariant closes the door: core "never inspects the body
of user Python."

**What H4a built instead:** `W-STATS-RESAMPLE-FAMILY`, a comparisons-only lower bound — with `k`
comparisons and at least one metric each, `holm`'s tightest level is `ALPHA / k` and needs
`min_honest_draws(1 − ALPHA/k)` draws. Always true when it fires, silent when it might not be.

**The residue, accepted rather than fixed:** a config with many metrics can still null every
`ci95_corrected` while clearing this bound. That is already disclosed at run time by
`W-STATS-CORRECTED-THIN`, which names the realized `family_size` and `correction_level`. Proposed
resolution: none — a validate-time check that reported the real requirement would have to know
what user code returns, and the run-time disclosure is the honest surface for it. Recorded so the
absence is a decision rather than a gap nobody noticed.
```

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_validate.py -k resample`, then `uv run pytest`, `uv run mypy`, `uv run ruff check .`, then the doc mechanical pass on both `reference.md` and `spec-defects.md`.

- [ ] **Step 5: Mutate** — in `validate.py`, change `needed = min_honest_draws(1.0 - ALPHA / comparisons)` to `needed = min_honest_draws()`. Run `uv run pytest tests/test_validate.py -k family_bound`. `test_the_family_bound_scales_with_the_comparison_count` must FAIL on its second assertion (100 ≥ 80, so no warning at three comparisons) and `test_the_family_bound_is_silent_when_n_clears_it` must FAIL on its 239 assertion — two tests, which is why the scaling test exists beside the boundary test. Delete `__pycache__`, edit the expression back in place, re-run. Second mutation: delete the `if correction_method not in ("holm", "bonferroni"): return` guard; `test_the_family_bound_is_not_reported_where_no_level_exists` must FAIL for both parameters. Revert in place.

- [ ] **Step 6: Commit** — `feat: W-STATS-RESAMPLE-FAMILY, the comparisons-only bound; file the metric-count residue`.

---

