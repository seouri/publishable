import pytest

from publishable.correction import (
    ALPHA,
    Member,
    UnpairedEvidence,
    _corrected_bounds,
    corrected_fields,
    corrected_for,
    family_members,
    family_shape,
    rank_family,
)
from publishable.stats import (
    interval_at,
    paired_t_over_units,
    paired_t_over_units_clustered,
    weighted_paired_t_over_units,
    welch_t_over_units,
    welch_t_over_units_clustered,
)


def _m(where="1", step="s", metric="r", delta=0.1, ci95=(0.0, 0.2), decl=0):
    return Member(
        where=where,
        step=step,
        metric=metric,
        delta=delta,
        ci95=ci95,
        pool=None,
        diffs=(0.1, 0.2, 0.3),
        declaration_index=decl,
    )


def test_alpha_is_five_percent_and_not_configurable():
    """`ci95` is in every record field name, so the raw confidence is fixed and
    only the corrected level varies. A config field for it would have to rename
    the record field."""
    assert ALPHA == 0.05


def test_a_member_with_an_interval_rejects_both_pool_and_diffs():
    """Both set would let `_corrected_bounds` silently take the `diffs`
    branch and build a *t* interval as the corrected counterpart of a
    *percentile* raw one — wrong by construction, not by evidence."""
    with pytest.raises(ValueError, match="pool, diffs"):
        Member(
            where="1",
            step="s",
            metric="r",
            delta=0.1,
            ci95=(0.0, 0.2),
            pool=(0.1, 0.2, 0.3),
            diffs=(0.1, 0.2, 0.3),
            declaration_index=0,
        )


def test_a_member_with_an_interval_rejects_neither_pool_nor_diffs():
    """None of the three set would make `_corrected_bounds` return `None` for a
    reason that has nothing to do with the pool being too small, so `thin: True`
    would fire over a member that was never thin."""
    with pytest.raises(ValueError, match="none of the three"):
        Member(
            where="1",
            step="s",
            metric="r",
            delta=0.1,
            ci95=(0.0, 0.2),
            pool=None,
            diffs=None,
            declaration_index=0,
        )


def test_unpaired_evidence_carries_two_vectors_and_validates_its_own_alignment():
    """A Welch interval's evidence is neither a pool nor a difference vector: it is
    two per-side value vectors, plus two per-side label vectors when clustered. The
    alignment invariant lives HERE rather than on `Member`, because a modifier's
    length check belongs to the object that defines the vectors it aligns against —
    a flat `clusters` pair beside `sides` would be one field with two admissible
    shapes, which is the misaligned-vector class that produces a plausible number
    rather than an error.

    Both sides are checked, because a check reading one passes any fixture whose
    other side happens to align."""
    plain = UnpairedEvidence(of=(1.0, 2.0), against=(3.0, 4.0, 5.0))
    assert plain.clusters is None
    clustered = UnpairedEvidence(
        of=(1.0, 2.0), against=(3.0, 4.0, 5.0), clusters=(("a", "b"), ("c", "c", "d"))
    )
    assert clustered.clusters == (("a", "b"), ("c", "c", "d"))
    with pytest.raises(ValueError, match="of"):
        UnpairedEvidence(of=(1.0, 2.0), against=(3.0, 4.0), clusters=(("a",), ("c", "d")))
    with pytest.raises(ValueError, match="against"):
        UnpairedEvidence(of=(1.0, 2.0), against=(3.0, 4.0), clusters=(("a", "b"), ("c",)))


def test_a_member_carries_exactly_one_of_pool_diffs_and_sides():
    """The rule counted over three rather than extended from an equality. Today's
    `(pool is None) == (diffs is None)` does not generalize, and a second equality
    beside it would admit a member carrying two kinds — which would let
    `_corrected_bounds` build a *t* corrected bound for a percentile raw interval,
    narrower or wider than the truth by construction rather than by evidence.

    All three pairs are asserted plus the empty case, because a count that tested
    `<= 1` would admit none and a count testing `>= 1` would admit all three."""
    common = dict(where="1", step="s", metric="m", delta=1.0, ci95=(0.0, 2.0), declaration_index=0)
    sides = UnpairedEvidence(of=(1.0, 2.0), against=(3.0, 4.0))
    Member(pool=None, diffs=None, sides=sides, **common)  # the control: one is fine
    with pytest.raises(ValueError, match="pool, sides"):
        Member(pool=(1.0, 2.0), diffs=None, sides=sides, **common)
    with pytest.raises(ValueError, match="diffs, sides"):
        Member(pool=None, diffs=(1.0, 2.0), sides=sides, **common)
    with pytest.raises(ValueError, match="pool, diffs"):
        Member(pool=(1.0,), diffs=(1.0,), sides=None, **common)
    with pytest.raises(ValueError, match="none of the three"):
        Member(pool=None, diffs=None, sides=None, **common)


def test_a_member_may_not_carry_a_modifier_beside_sides():
    """Both modifiers are modifiers on `diffs`, and neither composes with `sides`.
    `weights` because `E-DATA-WEIGHT-ALLOCATION-CONTRAST` refuses the weighted
    unpaired composition at `validate`, so a member carrying both is `cli`'s
    bookkeeping error exactly as `E-DATA-WEIGHT-CLUSTER-CONTRAST` makes the other
    pair's. `clusters` because unpaired membership is PER SIDE and lives inside
    `UnpairedEvidence` — a flat label vector beside `sides` could not say which
    side it belongs to, and a construction reading it would align it against
    whichever vector came first.

    Asserted with `ci95=None` as well as with an interval, because both modifier
    checks run BEFORE the exactly-one rule's early return and must not become
    reachable only through it."""
    common = dict(where="1", step="s", metric="m", delta=1.0, declaration_index=0)
    sides = UnpairedEvidence(of=(1.0, 2.0), against=(3.0, 4.0))
    with pytest.raises(ValueError, match="sides"):
        Member(pool=None, diffs=None, sides=sides, weights=(1.0, 1.0), ci95=(0.0, 2.0), **common)
    with pytest.raises(ValueError, match="sides"):
        Member(pool=None, diffs=None, sides=sides, clusters=("a", "b"), ci95=(0.0, 2.0), **common)
    with pytest.raises(ValueError, match="sides"):
        Member(pool=None, diffs=None, sides=sides, weights=(1.0, 1.0), ci95=None, **common)


def test_a_member_with_no_interval_may_carry_sides_and_is_not_corrected():
    """The exemption `pool` and `diffs` already have, read for the third kind: a
    member with no `ci95` is dropped by `family_members` before any evidence field
    is read, and it is not required to carry none — a contrast whose construction
    came back below its floor still holds the two side vectors it was computed
    from.

    `family_members` reads `ci95` and nothing else, which is why it needs no change
    for this field; that is asserted here rather than left as a claim in a task
    report."""
    common = dict(where="1", step="s", metric="m", delta=1.0, declaration_index=0)
    sides = UnpairedEvidence(of=(1.0,), against=(3.0,))
    thin = Member(pool=None, diffs=None, sides=sides, ci95=None, **common)
    assert thin.sides is sides
    assert family_members([thin]) == []
    fat = Member(pool=None, diffs=None, sides=sides, ci95=(0.0, 2.0), **common)
    assert family_members([thin, fat]) == [fat]  # the presence that must report


_CB_OF = (17.0, 19.0, 20.0, 21.0, 23.0)
_CB_AGAINST = (5.0,) * 12 + (15.0,) * 12 + (10.0,)


def test_an_unpaired_members_corrected_bound_is_the_welch_form_at_a_smaller_alpha():
    """The corrected interval must be the SAME construction at a smaller α or it is
    a counterpart in name only. Fixture A: raw half-width 3.039125537798091 at df
    96/7, and Bonferroni over a family of 2 is α = 0.025, so the corrected
    half-width is that times `t(96/7, 0.9875) / t(96/7, 0.975)` =
    1.1706821500146336 — 3.5578…

    **The ratio is the assertion, at the entry's OWN df**, not the presence of a
    wider interval: a corrected bound built at an unpaired-IID df where a clustered
    one belongs, or at a paired df, is also wider. The clustered fixture below gives
    a ratio of 1.4227764722656022 at df 2.095031, and the two differ by 21 %, which
    is what makes each assertion discriminating."""
    member = Member(
        where="c",
        step="s",
        metric="m",
        delta=10.0,
        ci95=(10.0 - 3.039125537798091, 10.0 + 3.039125537798091),
        pool=None,
        diffs=None,
        sides=UnpairedEvidence(of=_CB_OF, against=_CB_AGAINST),
        declaration_index=0,
    )
    bounds = _corrected_bounds(member, 0.025)
    assert bounds is not None
    half = (bounds[1] - bounds[0]) / 2
    assert half == pytest.approx(3.039125537798091 * 1.1706821500146336)
    assert (bounds[0] + bounds[1]) / 2 == pytest.approx(10.0)


def test_an_unpaired_clustered_members_corrected_bound_reads_its_own_two_cluster_counts():
    """Fixture B: raw half-width 34.14810237373095 at df 2.0950313633473936, so the
    corrected half-width at α = 0.025 is that times 1.4227764722656022 — 48.5814…

    **The 21 % gap from the IID ratio is the point.** A corrected bound built from
    the two value vectors while ignoring the label vectors gives the IID Welch
    construction, whose own df is 8.399133841827005 and whose ratio is therefore a
    visibly different number — so this assertion catches a `clusters` field that was
    threaded onto the member and then dropped by the construction, which is the
    failure H4b-2 pinned one axis over.

    **The centre is asserted too.** Half-width alone does not pin which side is
    `of` and which is `against`: swapping them in the clustered call leaves
    `var_of + var_against` unchanged (it is symmetric) and only flips the centre,
    so a half-width-only assertion is blind to that swap. Batch 3's review caught
    this arm unpinned — its `of`/`against` swap was found only by a `zip()` length
    crash from this fixture's 9-vs-12 asymmetry, not by any check of the value."""
    of = (0.0,) * 2 + (15.0,) * 3 + (30.0,) * 4
    against = (2.0,) * 2 + (4.0,) * 3 + (6.0,) * 3 + (8.0,) * 4
    labels = (
        ("p",) * 2 + ("q",) * 3 + ("r",) * 4,
        ("w",) * 2 + ("x",) * 3 + ("y",) * 3 + ("z",) * 4,
    )
    member = Member(
        where="c",
        step="s",
        metric="m",
        delta=12.833333333333332,
        ci95=(12.833333333333332 - 34.14810237373095, 12.833333333333332 + 34.14810237373095),
        pool=None,
        diffs=None,
        sides=UnpairedEvidence(of=of, against=against, clusters=labels),
        declaration_index=0,
    )
    bounds = _corrected_bounds(member, 0.025)
    assert bounds is not None
    half = (bounds[1] - bounds[0]) / 2
    assert half == pytest.approx(34.14810237373095 * 1.4227764722656022)
    assert (bounds[0] + bounds[1]) / 2 == pytest.approx(12.833333333333332)


def test_an_unpaired_percentile_member_reads_a_second_rank_pair_off_its_pool():
    """An unpaired percentile's evidence is a pool of resampled differences,
    structurally identical to a paired one's — so `pool` needs no change and this is
    the arm that must NOT have grown a fourth branch. Asserted as `corrected ⊇ raw`
    off the same pool, which is a property of the arithmetic rather than of two RNG
    calls agreeing."""
    pool = tuple(float(i) for i in range(400))
    member = Member(
        where="c",
        step="s",
        metric="m",
        delta=200.0,
        ci95=(10.0, 389.0),
        pool=pool,
        diffs=None,
        sides=None,
        declaration_index=0,
    )
    bounds = _corrected_bounds(member, 0.025)
    assert bounds is not None
    assert bounds[0] < 10.0 and bounds[1] > 389.0


def test_the_five_t_arms_are_each_reached_by_one_member_shape():
    """Five *t* arms, counted rather than carried: two under `sides` and three under
    `diffs`, plus the `pool` fall-through. **An implementer writing six leaves an arm
    no input reaches, and one writing four leaves a cell falling through to a wrong
    construction** — so every arm is asserted against a **direct call of the
    construction its `method` names**, at the same corrected confidence, rather than
    by non-`None`-ness and distinctness alone: a distinctness assertion over the six
    bounds only catches a fall-through that happens to COLLIDE with a neighbour's
    answer, and a fall-through that changes the number without colliding (dropping
    `sides.clusters`, say) would leave that assertion green — batch 3's review
    caught exactly this gap.

    Both `sides` fixtures are unequal per side (4-vs-3, 3-vs-4): § The discriminating
    fixtures' constraint 1 — equal per-side sizes make the pooled and Welch standard
    errors coincide algebraically, which would make a pooled-variance mutant on
    either `sides` arm invisible here."""
    common = dict(where="c", step="s", metric="m", delta=1.0, declaration_index=0)
    diffs = (1.0, 2.0, 3.0, 4.0)
    sides_clustered_of = (1.0, 1.0, 5.0, 5.0)
    sides_clustered_of_labels = ("a", "a", "b", "b")
    sides_clustered_against = (2.0, 2.0, 8.0)
    sides_clustered_against_labels = ("c", "c", "d")
    sides_plain_of = (1.0, 2.0, 3.0)
    sides_plain_against = (4.0, 5.0, 7.0, 9.0)
    diffs_clustered_clusters = ("a", "a", "b", "b")
    diffs_weighted_weights = (1.0, 2.0, 1.0, 2.0)
    pool = tuple(float(i) for i in range(400))
    shapes = {
        "sides_clustered": dict(
            pool=None,
            diffs=None,
            sides=UnpairedEvidence(
                of=sides_clustered_of,
                against=sides_clustered_against,
                clusters=(sides_clustered_of_labels, sides_clustered_against_labels),
            ),
        ),
        "sides_plain": dict(
            pool=None,
            diffs=None,
            sides=UnpairedEvidence(of=sides_plain_of, against=sides_plain_against),
        ),
        "diffs_clustered": dict(
            pool=None, diffs=diffs, sides=None, clusters=diffs_clustered_clusters
        ),
        "diffs_weighted": dict(pool=None, diffs=diffs, sides=None, weights=diffs_weighted_weights),
        "diffs_plain": dict(pool=None, diffs=diffs, sides=None),
        "pool": dict(pool=pool, diffs=None, sides=None),
    }
    # What each arm's `method` names, called directly at the same corrected
    # confidence `_corrected_bounds(member, 0.025)` uses (1.0 - 0.025 = 0.975) — the
    # reviewer's own verification, now pinned rather than re-established by hand
    # each time.
    expected = {
        "sides_clustered": welch_t_over_units_clustered(
            sides_clustered_of,
            sides_clustered_of_labels,
            sides_clustered_against,
            sides_clustered_against_labels,
            confidence=0.975,
        ),
        "sides_plain": welch_t_over_units(sides_plain_of, sides_plain_against, confidence=0.975),
        "diffs_clustered": paired_t_over_units_clustered(
            diffs, diffs_clustered_clusters, confidence=0.975
        ),
        "diffs_weighted": weighted_paired_t_over_units(
            diffs, diffs_weighted_weights, confidence=0.975
        ),
        "diffs_plain": paired_t_over_units(diffs, confidence=0.975),
    }
    got = {}
    for name, fields in shapes.items():
        member = Member(ci95=(0.0, 2.0), **common, **fields)
        got[name] = _corrected_bounds(member, 0.025)
    # Every arm returned a bound, so no shape fell through to the final `None`.
    assert all(v is not None for v in got.values()), got
    # Each of the five *t* arms is bit-equal to a direct call of the construction
    # its `method` names — the assertion a distinctness check cannot make, because
    # it is blind to a fall-through that moves the number without colliding.
    for name, interval in expected.items():
        assert got[name] == (interval.low, interval.high), name
    # The pool arm reads a second rank pair off the same pool `interval_at` would.
    assert got["pool"] == interval_at(pool, 0.975)
    # And no two arms produced the same bound, so no shape fell through to a
    # neighbour's construction: five distinct *t* answers plus the pool's.
    assert len({tuple(v) for v in got.values() if v is not None}) == 6


def test_a_member_with_no_interval_is_not_in_the_family():
    """Counted-iff-corrected: a metric reported without an interval is not a
    comparison a reader can read as significant, so it neither takes a slot nor
    consumes a rank. `cli` passes `ci95=None` for it."""
    with_interval = _m(metric="r")
    without = Member(
        where="1",
        step="s",
        metric="n_units",
        delta=3.0,
        ci95=None,
        pool=None,
        diffs=None,
        declaration_index=1,
    )
    assert family_members([with_interval, without]) == [with_interval]


def test_the_family_is_comparisons_times_metrics():
    """`reference.md`: "The family is comparisons × metrics, not comparisons." A
    six-condition sweep is five comparisons, but three metrics per step means a
    reader is shown fifteen intervals."""
    members = [_m(where=str(c), metric=k) for c in (1, 2, 3, 4, 5) for k in ("r", "rmse", "auc")]
    size, shape = family_shape(family_members(members))
    assert shape == {"comparisons": 5, "metrics": 3}
    assert size == 15


def test_the_worked_example_is_two_comparisons_and_one_metric():
    """`reference.md`'s worked example: 3 conditions give 2 baseline comparisons,
    one metric gives `metrics: 1`, so `family_size: 2`. This is the number the
    acceptance test asserts, pinned here at the arithmetic."""
    members = [_m(where="1", metric="r"), _m(where="2", metric="r")]
    size, shape = family_shape(family_members(members))
    assert size == 2
    assert shape == {"comparisons": 2, "metrics": 1}


def test_a_contrast_and_a_baseline_comparison_are_both_comparisons():
    """`reference.md`: "A 'comparison' is a baseline contrast or a declared one" —
    both put an interval in front of a reader. Counting only `vs_baseline`
    under-corrects by exactly the declared contrasts a config asked for."""
    members = [_m(where="1"), _m(where="sensitivity")]
    size, shape = family_shape(family_members(members))
    assert shape["comparisons"] == 2
    assert size == 2


def test_a_metric_absent_from_one_comparison_still_counts_as_a_metric():
    """The product can exceed the member count. That is the conservative
    direction — a larger family means a smaller α and a wider corrected
    interval — and `reference.md`'s own arithmetic is the product. Pinned so
    nobody "fixes" it into the member count."""
    members = [
        _m(where="1", metric="r"),
        _m(where="1", metric="rmse"),
        _m(where="2", metric="r"),
    ]
    size, shape = family_shape(family_members(members))
    assert shape == {"comparisons": 2, "metrics": 2}
    assert size == 4  # not 3


def test_the_same_metric_name_in_two_steps_counts_as_two_metrics():
    """`metrics` keys on `(step, metric)`, not `metric` alone. A simplification
    to `{m.metric for m in members}` would collapse `step01.r` and `step02.r`
    into one metric, undercounting the family — and a family counted too small
    gives an α that is too large and corrected intervals that are too narrow,
    which is the failure `reference.md` calls out as worse than not correcting
    at all."""
    members = [
        _m(where="1", step="step01", metric="r"),
        _m(where="1", step="step02", metric="r"),
    ]
    size, shape = family_shape(family_members(members))
    assert shape == {"comparisons": 1, "metrics": 2}
    assert size == 2


def test_the_family_ranks_by_estimate_over_half_width():
    """`reference.md`: the ranking statistic is "the point estimate over half the
    raw `ci95` width, largest first" — the one quantity every member has, since
    Holm's own p-value is unavailable here (a `null_test` supplies one only where
    `shuffle` names an attribute, which a parameter-axis contrast never is).

    These are the worked example's two members: kendall at 0.169 over a
    half-width of 0.044 is 3.84, spearman at 0.026 over 0.033 is 0.79. Ranking
    on the raw *width* instead would order them the other way, since kendall's
    interval is the wider of the two."""
    kendall = _m(where="2", metric="r", delta=-0.169, ci95=(-0.213, -0.125))
    spearman = _m(where="1", metric="r", delta=0.026, ci95=(-0.007, 0.059))
    assert [m.where for m in rank_family([spearman, kendall])] == ["2", "1"]


def test_the_ranking_statistic_uses_the_magnitude_not_the_signed_estimate():
    """Kendall's delta is negative and it is the *strongest* member. Ranking on
    the signed estimate puts every negative delta last regardless of its
    evidence, which would silently hand the smallest correction to the members
    that most need it."""
    strong_negative = _m(where="a", delta=-0.169, ci95=(-0.213, -0.125))
    weak_positive = _m(where="b", delta=0.026, ci95=(-0.007, 0.059))
    assert [m.where for m in rank_family([weak_positive, strong_negative])] == ["a", "b"]


def test_ties_break_by_declaration_index_not_where_or_metric_name():
    """`reference.md`: ties break by declaration order — the index `cli`
    assigned when it built the family — not by `where` or by metric name.
    These three carry identical evidence, and their `where`/`metric` would
    order them `(1, auc), (1, rmse), (2, auc)` were the tie-break keyed on
    those fields instead (sorted lexicographically); `declaration_index`
    orders them differently, and that is the order that must win, whichever
    order the members arrive in."""
    a = _m(where="2", metric="auc", delta=0.1, ci95=(0.0, 0.2), decl=2)
    b = _m(where="1", metric="rmse", delta=0.1, ci95=(0.0, 0.2), decl=0)
    c = _m(where="1", metric="auc", delta=0.1, ci95=(0.0, 0.2), decl=1)
    assert [(m.where, m.metric) for m in rank_family([a, b, c])] == [
        ("1", "rmse"),
        ("1", "auc"),
        ("2", "auc"),
    ]
    assert rank_family([a, b, c]) == rank_family([c, b, a])


def test_a_tie_breaks_by_declaration_order_not_by_metric_name() -> None:
    """Two members with identical evidence rank in the order cli built them.

    Named `zeta` first and `alpha` second on purpose: a lexicographic tie-break
    puts `alpha` first, and declaration order puts `zeta` first.
    """
    members = [
        Member(
            where="cond:1",
            step="step02",
            metric="zeta",
            delta=0.1,
            ci95=(0.0, 0.2),
            pool=None,
            diffs=(0.1, 0.1),
            declaration_index=0,
        ),
        Member(
            where="cond:1",
            step="step02",
            metric="alpha",
            delta=0.1,
            ci95=(0.0, 0.2),
            pool=None,
            diffs=(0.1, 0.1),
            declaration_index=1,
        ),
    ]
    assert [m.metric for m in rank_family(members)] == ["zeta", "alpha"]


def test_a_zero_width_interval_ranks_first_rather_than_dividing_by_zero():
    """A point-mass bootstrap is legitimate (S4b task 5 established it), so a
    half-width of exactly 0.0 is reachable and must not raise. Infinite evidence
    ranks first, which is also what the ratio's limit says."""
    point_mass = _m(where="a", delta=0.5, ci95=(0.5, 0.5))
    ordinary = _m(where="b", delta=0.169, ci95=(0.125, 0.213))
    assert [m.where for m in rank_family([ordinary, point_mass])] == ["a", "b"]


def _from_diffs(where, mean, spread, metric="r", decl=0):
    """A member whose `ci95` **is** the t interval over its own `diffs`.

    This matters: `corrected_fields` rebuilds a column metric's corrected
    interval by re-running `paired_t_over_units` over `diffs`, so a member whose
    `ci95` was hand-written to some other value would make "corrected at α equals
    raw" compare two unrelated numbers and fail against a correct
    implementation. Deriving both from one source keeps the assertion about
    Holm's level rather than about the fixture.
    """
    diffs = tuple(mean + spread * ((i % 5) - 2) for i in range(228))
    interval = paired_t_over_units(diffs)
    assert interval is not None
    return Member(
        where=where,
        step="step03_analyze",
        metric=metric,
        delta=sum(diffs) / len(diffs),
        ci95=(interval.low, interval.high),
        pool=None,
        diffs=diffs,
        declaration_index=decl,
    )


def _two_member_family():
    """Two members, the first carrying much the stronger evidence — the worked
    example's shape (kendall against spearman), with the same wide gap in the
    ranking ratio and intervals that are genuinely their own construction."""
    strong = _from_diffs("2", mean=-0.169, spread=0.02, decl=0)
    weak = _from_diffs("1", mean=0.026, spread=0.30, decl=1)
    return strong, weak


def test_corrected_for_takes_the_family_size_it_is_given():
    """The hypothesis family "counts the confirmatory hypotheses whose
    observations core computed, where a sweep's family counts comparisons ×
    metrics" — it "multiplies nothing". Only the size differs, so only the size
    is a parameter."""
    strong, weak = _two_member_family()
    got = corrected_for([strong, weak], "bonferroni", 7, {"hypotheses": 7})
    for entry in got.values():
        assert entry["correction_level"] == pytest.approx(0.05 / 7)
        assert entry["family_size"] == 7
        assert entry["family"] == {"hypotheses": 7}


def test_corrected_fields_still_computes_the_sweep_shape():
    """The existing caller keeps its behaviour: it passes the product, not the
    member count, and its breakout still names comparisons and metrics.

    Non-square on purpose, following
    `test_the_level_divides_by_the_family_product_not_the_member_count`'s
    fixture shape: `rmse` is recorded in comparison "1" and absent from
    comparison "2", so 3 members span a family of 2 comparisons × 2 metrics =
    4. A caller that substituted `len(family)` (3) for the product would
    compute `family_size: 3` here and this test would catch it — a square
    fixture (comparisons == metrics == members) cannot, since the product and
    the member count coincide by construction."""
    members = [
        _from_diffs("1", mean=-0.169, spread=0.02, metric="r", decl=0),
        _from_diffs("1", mean=-0.150, spread=0.02, metric="rmse", decl=1),
        _from_diffs("2", mean=0.026, spread=0.30, metric="r", decl=2),
    ]
    got = corrected_fields(members, "bonferroni")
    assert len(got) == 3
    for entry in got.values():
        assert entry["family_size"] == 4
        assert entry["family"] == {"comparisons": 2, "metrics": 2}
        assert entry["correction_level"] == pytest.approx(0.05 / 4)


def test_holm_ranks_within_whatever_family_size_it_is_handed():
    """Holm's level is α/(m−i+1), so a larger m makes rank 1 tighter. Passing a
    size the members did not imply is exactly what the hypothesis family does."""
    strong, weak = _two_member_family()
    got = corrected_for([strong, weak], "holm", 5, {"hypotheses": 5})
    levels = sorted(e["correction_level"] for e in got.values())
    assert levels == [pytest.approx(0.05 / 5), pytest.approx(0.05 / 4)]


def test_holm_corrects_the_weakest_member_by_nothing():
    """`reference.md`: "the weakest comparison in a family is corrected by
    nothing — at rank m the level is α itself", which the worked example shows:
    spearman is rank 2 of 2, so `correction_level: 0.05` and its corrected
    interval *is* its raw one. That is Holm working, not a correction that
    failed, and it is the property that makes Holm more powerful than
    Bonferroni.

    Passed in as `[weak, strong]` — reversed from ranked order — so a
    `rank_family` call replaced by `enumerate` over the input as given cannot
    pass by accident; the correct implementation must actually re-rank."""
    strong, weak_member = _two_member_family()
    got = corrected_fields([weak_member, strong], "holm")
    weak = got[("1", "step03_analyze", "r")]
    assert weak["correction_level"] == pytest.approx(0.05)
    assert weak["ci95_corrected"] == pytest.approx(list(weak_member.ci95))


def test_holm_corrects_the_strongest_member_at_alpha_over_m():
    """Rank 1 of 2 gets α/(m−i+1) = α/2, so its corrected interval is strictly
    wider than its raw one on both sides. Using α for every member — the
    mutation that keeps the weakest member's test green — is caught here."""
    strong_member, weak_member = _two_member_family()
    got = corrected_fields([strong_member, weak_member], "holm")
    strong = got[("2", "step03_analyze", "r")]
    assert strong["correction_level"] == pytest.approx(0.025)
    low, high = strong["ci95_corrected"]
    assert low < strong_member.ci95[0]
    assert high > strong_member.ci95[1]


def test_bonferroni_gives_every_member_the_same_level():
    """α/m regardless of rank — the difference from Holm, and the reason Holm is
    uniformly more powerful."""
    strong, weak = _two_member_family()
    got = corrected_fields([strong, weak], "bonferroni")
    levels = {e["correction_level"] for e in got.values()}
    assert levels == {0.025}
    for member in (strong, weak):
        entry = got[(member.where, member.step, member.metric)]
        low, high = entry["ci95_corrected"]
        assert low < member.ci95[0] and high > member.ci95[1]
        assert entry["correction"] == "bonferroni"


def test_the_level_divides_by_the_family_product_not_the_member_count():
    """`family_size` is `comparisons × metrics`, and it is the *m* both Holm and
    Bonferroni divide α by — not `len(family)`, which on a non-square family is
    smaller. `rmse` is recorded in comparison "1" and absent from comparison
    "2", so 3 members span a family of 2 × 2 = 4: the level is 0.05/4, and
    correcting at 0.05/3 instead would publish every interval in the run
    narrower than the evidence supports, beside a `family_size: 4` saying the
    opposite. The design spec records the same warning in prose ("Recorded here
    so a future reader does not 'fix' it into the member count"); this is what
    stops them."""
    members = [
        _from_diffs("1", mean=-0.169, spread=0.02, metric="r", decl=0),
        _from_diffs("1", mean=-0.150, spread=0.02, metric="rmse", decl=1),
        _from_diffs("2", mean=0.026, spread=0.30, metric="r", decl=2),
    ]
    got = corrected_fields(members, "bonferroni")
    assert len(got) == 3
    for entry in got.values():
        assert entry["family_size"] == 4  # not 3
        assert entry["family"] == {"comparisons": 2, "metrics": 2}
        assert entry["correction_level"] == pytest.approx(0.05 / 4)  # not 0.05 / 3
        assert entry["correction_level"] != pytest.approx(0.05 / 3)


def test_fdr_bh_records_no_interval_and_no_level():
    """`reference.md`: Benjamini-Hochberg "has no interval that means anything of
    the kind — controlling a false discovery *rate* is a statement about a set,
    not a bound on any one comparison — so core reports the adjusted p-value and
    leaves `ci95_corrected` null". No p-value exists in this build, so there is
    no `p_value_corrected` either.

    `thin` must be `False` here even though `bounds` is always `None` under
    `fdr_bh` — there is no `level` to have been too tight for the pool, so
    reporting thin would blame the evidence for a method that never asked for
    an interval in the first place."""
    strong, weak = _two_member_family()
    got = corrected_fields([strong, weak], "fdr_bh")
    for entry in got.values():
        assert entry["ci95_corrected"] is None
        assert entry["correction_level"] is None
        assert entry["thin"] is False
        assert "p_value_corrected" not in entry


def test_none_produces_no_corrected_fields_at_all():
    """`reference.md`'s table: under `none`, `ci95_corrected` is *absent*. An
    explicit null would claim a correction was attempted."""
    strong, weak = _two_member_family()
    assert corrected_fields([strong, weak], "none") == {}


def test_every_member_carries_the_family_it_was_corrected_against():
    """`family` is "reported broken out rather than as a single integer, so the
    count is auditable instead of asserted"."""
    strong, weak = _two_member_family()
    got = corrected_fields([strong, weak], "holm")
    for entry in got.values():
        assert entry["family_size"] == 2
        assert entry["family"] == {"comparisons": 2, "metrics": 1}


def test_a_derived_member_is_corrected_off_its_own_pool():
    """A derived metric has no per-unit differences, so its corrected interval is
    a second rank pair off the stored draws. Nesting is structural: the same
    pool, read further into both tails.

    Two metrics on the same comparison so the family is size 2 and the level is
    genuinely below α — at family size 1 the level is α itself and
    `interval_at(pool, 0.95)` (the raw call) would be indistinguishable from the
    correct one."""
    pool = tuple(float(i) / 1000.0 for i in range(2000))
    member = Member(
        where="1",
        step="s",
        metric="r",
        delta=1.0,
        ci95=(0.049, 1.949),
        pool=pool,
        diffs=None,
        declaration_index=0,
    )
    other = Member(
        where="1",
        step="s",
        metric="rmse",
        delta=1.0,
        ci95=(0.049, 1.949),
        pool=pool,
        diffs=None,
        declaration_index=1,
    )
    got = corrected_fields([member, other], "bonferroni")[("1", "s", "r")]
    low, high = got["ci95_corrected"]
    assert low < member.ci95[0] and high > member.ci95[1]


def test_a_pool_too_small_for_the_level_reports_no_interval_and_says_so():
    """A family of 40 implies α/40, whose honest-draw floor is 3201 against a
    2000-draw pool. `ci95_corrected` is null while `correction_level` still
    records what was asked for, and `thin` is what the caller turns into
    `W-STATS-CORRECTED-THIN` — a silent null here would read as "no correction
    applies" rather than "the evidence cannot support this level"."""
    pool = tuple(float(i) / 1000.0 for i in range(2000))
    members = [
        Member(
            where=str(c),
            step="s",
            metric=k,
            delta=1.0,
            ci95=(0.049, 1.949),
            pool=pool,
            diffs=None,
            declaration_index=i,
        )
        for i, (c, k) in enumerate((c, k) for c in range(20) for k in ("r", "rmse"))
    ]
    got = corrected_fields(members, "bonferroni")
    entry = got[("0", "s", "r")]
    assert entry["family_size"] == 40
    assert entry["correction_level"] == pytest.approx(0.05 / 40)
    assert entry["ci95_corrected"] is None
    assert entry["thin"] is True


def test_a_member_may_carry_weights_alongside_its_differences():
    """Decision 4. A weighted column contrast with no `resample` declared has a
    weighted raw *t* interval, and `_corrected_bounds` rebuilds the corrected one
    from the same evidence — so the weights have to travel with the differences
    they weighted. Anything else publishes a weighted raw beside an unweighted
    corrected, which is the fault `__post_init__`'s docstring names for the
    pool/diffs mix one axis over."""
    member = Member(
        where="cond:1",
        step="s",
        metric="m",
        delta=8.0,
        ci95=(4.0, 12.0),
        pool=None,
        diffs=(1.0, 2.0, 3.0, 9.0, 10.0, 11.0),
        weights=(1, 1, 1, 3, 3, 3),
        declaration_index=0,
    )
    assert member.weights == (1, 1, 1, 3, 3, 3)


def test_weights_beside_a_pool_is_refused():
    """A percentile pool is already built from weighted draws, so weights there
    would be applied twice. The exactly-one-of `pool`/`diffs` invariant is
    untouched: this is a second, separate rule about which evidence `weights` can
    modify, which is why it names `pool` in its own message."""
    with pytest.raises(ValueError) as excinfo:
        Member(
            where="cond:1",
            step="s",
            metric="m",
            delta=8.0,
            ci95=(4.0, 12.0),
            pool=(1.0, 2.0, 3.0),
            diffs=None,
            weights=(1, 1, 1),
            declaration_index=0,
        )
    assert "pool" in str(excinfo.value)


def test_weights_of_a_different_length_than_the_differences_is_refused():
    """A misaligned weight vector is the whole failure class this wiring guards
    against — it produces a plausible number rather than an error, which is what
    `stats._weighted_mean`'s `strict=True` zip refuses one level down. Caught at
    construction so the fault names the bookkeeping rather than surfacing as a
    `zip` error inside a corrected bound."""
    with pytest.raises(ValueError) as excinfo:
        Member(
            where="cond:1",
            step="s",
            metric="m",
            delta=8.0,
            ci95=(4.0, 12.0),
            pool=None,
            diffs=(1.0, 2.0, 3.0),
            weights=(1, 1),
            declaration_index=0,
        )
    assert "length" in str(excinfo.value)


def test_a_member_with_no_weights_is_unchanged():
    """The neighbouring shape, and the reason the field is defaulted: every
    existing construction site and every existing test builds a `Member` without
    it, and none of them moved."""
    member = Member(
        where="cond:1",
        step="s",
        metric="m",
        delta=1.0,
        ci95=(0.5, 1.5),
        pool=None,
        diffs=(1.0, 2.0),
        declaration_index=0,
    )
    assert member.weights is None


def test_weights_are_checked_even_when_ci95_is_none():
    """The weights checks run before the `ci95 is None` early return,
    deliberately: the existing rule's exemption is about *evidence being
    absent*, not about alignment being optional.
    `test_a_member_with_no_interval_is_not_in_the_family` builds exactly this
    member shape (`ci95=None`, `diffs=None`) without weights; adding a
    misaligned `weights` here must still be refused."""
    with pytest.raises(ValueError) as excinfo:
        Member(
            where="1",
            step="s",
            metric="n_units",
            delta=3.0,
            ci95=None,
            pool=None,
            diffs=None,
            weights=(1, 1),
            declaration_index=1,
        )
    assert "length" in str(excinfo.value)


def test_a_corrected_bound_over_weighted_differences_is_weighted_too():
    """Decision 4, made observable. `_corrected_bounds` rebuilds the corrected
    interval from the same evidence as the raw one — so weighted differences get a
    weighted construction at the smaller α, not an unweighted counterpart of a
    weighted raw interval.

    Two members, identical but for the weights, at a family size of one so the
    level is α itself and the corrected bound is the raw one's own construction.
    The centres are exact: 8.0 weighted, 6.0 unweighted.

    A second check, at family size **two**, pins the α itself rather than only
    the construction: at family size one, `1.0 - level` is `0.95`, the default
    `confidence` `weighted_paired_t_over_units` would fall back to even with
    `confidence=1.0 - level` dropped from the call — so that first check alone
    cannot tell a threaded α from a silently-defaulted one. At family size two
    the bonferroni level is `0.05 / 2`, so `confidence=0.975`, a value nothing
    defaults to. The exact bound at that level, verified directly against the
    weighted construction: `[1.4426305905416408, 14.55736940945836]`."""
    diffs = (1.0, 2.0, 3.0, 9.0, 10.0, 11.0)
    common = dict(step="s", metric="m", ci95=(4.0, 12.0), pool=None, declaration_index=0)
    weighted = Member(where="cond:1", delta=8.0, diffs=diffs, weights=(1, 1, 1, 3, 3, 3), **common)
    plain = Member(where="cond:2", delta=6.0, diffs=diffs, **common)
    got_w = corrected_for([weighted], "bonferroni", 1, {"comparisons": 1, "metrics": 1})
    got_p = corrected_for([plain], "bonferroni", 1, {"comparisons": 1, "metrics": 1})
    low_w, high_w = got_w[("cond:1", "s", "m")]["ci95_corrected"]
    low_p, high_p = got_p[("cond:2", "s", "m")]["ci95_corrected"]
    assert (low_w + high_w) / 2 == pytest.approx(8.0)
    assert (low_p + high_p) / 2 == pytest.approx(6.0)

    got_w2 = corrected_for([weighted], "bonferroni", 2, {"comparisons": 1, "metrics": 1})
    low_w2, high_w2 = got_w2[("cond:1", "s", "m")]["ci95_corrected"]
    assert low_w2 == pytest.approx(1.4426305905416408)
    assert high_w2 == pytest.approx(14.55736940945836)


def test_a_pool_carrying_member_is_unaffected_by_the_weights_branch():
    """The payoff path's own corrected bound, pinned as unchanged. A column
    contrast under a declared `resample` carries the POOL, whose draws task 7's
    closure already weighted, so `interval_at` reads a second rank pair off
    weighted evidence and nothing more is needed. `Member` refuses weights beside a
    pool, so this is the shape that must keep working untouched."""
    pool = tuple(float(i) for i in range(200))
    member = Member(
        where="cond:1",
        step="s",
        metric="m",
        delta=100.0,
        ci95=(5.0, 195.0),
        pool=pool,
        diffs=None,
        declaration_index=0,
    )
    got = corrected_for([member], "bonferroni", 1, {"comparisons": 1, "metrics": 1})
    assert got[("cond:1", "s", "m")]["ci95_corrected"] is not None


def test_a_clustered_members_corrected_bound_is_the_clustered_construction():
    """The corrected interval is the raw one at a smaller α, from the same
    evidence — so a member whose raw interval was cluster-robust must not get an
    unclustered counterpart. `correction.py` is this construction's FIRST caller.

    At α = 0.05 the bound is the plan's 8.7632 half-width; at α = 0.01 it is
    t(0.995, df 2) = 9.924843 times the same standard error 2.0366934, i.e.
    20.2139. The unclustered counterpart at α = 0.01 would be 2.7919 — two
    numbers no rounding can confuse, and both are asserted so a construction that
    ignored the level would fail as loudly as one that ignored the membership."""
    diffs = tuple([1.0] * 2 + [5.0] * 4 + [9.0] * 6)
    labels = tuple(["a"] * 2 + ["b"] * 4 + ["c"] * 6)
    member = Member(
        where="cond:1",
        step="s",
        metric="m",
        delta=6.333333333333333,
        ci95=(6.333333333333333 - 8.763214143637903, 6.333333333333333 + 8.763214143637903),
        pool=None,
        diffs=diffs,
        declaration_index=0,
        clusters=labels,
    )
    # The RAW half-width, independently constructed rather than read back off
    # `member.ci95` (which is built from this same literal two lines above, so an
    # assertion against it would be arithmetic on the test's own input, not a
    # check on production code).
    raw = paired_t_over_units_clustered(diffs, labels)
    assert raw is not None
    assert (raw.high - raw.low) / 2 == pytest.approx(8.763214143637903)
    bounds = _corrected_bounds(member, 0.01)
    assert bounds is not None
    assert (bounds[1] - bounds[0]) / 2 == pytest.approx(20.213931212789273)


def test_a_member_may_not_carry_clusters_beside_a_pool_or_a_weight():
    """`clusters` is a modifier on `diffs`, so the same three rules `weights`
    carries. Beside a pool it would be applied twice — a clustered percentile pool
    is already drawn from clusters. Beside `weights` it names a combination
    `E-DATA-WEIGHT-CLUSTER-CONTRAST` refuses at `validate` and
    `_comparison_step_blocks` refuses again, so a member holding both is core's
    bookkeeping error. At the wrong length it is a misaligned vector, which
    produces a plausible number rather than an error."""
    common = {
        "where": "cond:1",
        "step": "s",
        "metric": "m",
        "delta": 1.0,
        "ci95": (0.0, 2.0),
        "declaration_index": 0,
    }
    with pytest.raises(ValueError, match="clusters"):
        Member(pool=(1.0, 2.0), diffs=None, clusters=("a", "b"), **common)
    with pytest.raises(ValueError, match="clusters"):
        Member(pool=None, diffs=(1.0, 2.0), clusters=("a",), **common)
    with pytest.raises(ValueError, match="clusters"):
        Member(
            pool=None,
            diffs=(1.0, 2.0),
            clusters=("a", "b"),
            weights=(1.0, 1.0),
            **common,
        )


_PIN_MEMBERS = [
    Member(
        where="cond:1",
        step="s",
        metric="m",
        delta=0.026,
        ci95=(-0.007, 0.059),
        pool=None,
        diffs=tuple(0.026 + 0.01 * k for k in range(-5, 6)),
        declaration_index=0,
    ),
    Member(
        where="cond:2",
        step="s",
        metric="m",
        delta=-0.169,
        ci95=(-0.213, -0.125),
        pool=None,
        diffs=tuple(-0.169 + 0.005 * k for k in range(-5, 6)),
        declaration_index=1,
    ),
    Member(
        where="cond:3",
        step="s",
        metric="m",
        delta=0.0,
        ci95=(-0.5, 0.5),
        pool=None,
        diffs=tuple(0.1 * k for k in range(-5, 6)),
        declaration_index=2,
    ),
    Member(
        where="cond:4",
        step="s",
        metric="m",
        delta=1.0,
        ci95=None,
        pool=None,
        diffs=(1.0, 1.0, 1.0),
        declaration_index=3,
    ),
]


_PIN_INNER_KEYS = {
    "ci95_corrected",
    "correction",
    "correction_level",
    "family_size",
    "family",
    "thin",
}


def test_holms_corrected_bounds_are_unmoved_by_the_p_value_work():
    """The regression pin, captured at `a207702` before any H4d change.

    Three properties in one family, and each would move under a different fault.
    The RANK ORDER is asserted first because a level is a function of a rank:
    `cond:3` has `delta` exactly 0 with a finite width, so `_evidence_ratio`
    returns exactly `0.0` for it — a REAL member at the value a p-only member
    would be handed by any sentinel. It must keep rank 3 of 3, which is what
    says the new tier sorts below every interval-carrying member rather than
    among them.

    The three levels are alpha/3, alpha/2 and alpha, which is Holm at m = 3 —
    so a family that admitted `cond:4` would show 4, and every bound would move.

    Round-1 review (M2): the outer `set(fields)` assertion pinned member
    identities only, so a task widening what EACH block carries — `holm` and
    `bonferroni` both gain `p_value_corrected` in tasks 17/18, `fdr_bh`'s
    `ci95_corrected` stays `null` under a rewritten two-pass `corrected_for` —
    could pass this test with a spurious key or a spurious `None` added to
    every block. Each block's own key set is now pinned alongside its values,
    so an added or missing key fails here rather than passing.
    """
    ranked = [m.where for m in rank_family(family_members(_PIN_MEMBERS))]
    assert ranked == ["cond:2", "cond:1", "cond:3"]

    fields = corrected_fields(_PIN_MEMBERS, "holm")
    assert set(fields) == {
        ("cond:1", "s", "m"),
        ("cond:2", "s", "m"),
        ("cond:3", "s", "m"),
    }
    for key in fields:
        assert set(fields[key]) == _PIN_INNER_KEYS
    assert fields[("cond:2", "s", "m")]["correction_level"] == pytest.approx(0.05 / 3)
    assert fields[("cond:2", "s", "m")]["ci95_corrected"] == [
        pytest.approx(-0.18335036277829492),
        pytest.approx(-0.1546496372217051),
    ]
    assert fields[("cond:1", "s", "m")]["correction_level"] == pytest.approx(0.025)
    assert fields[("cond:1", "s", "m")]["ci95_corrected"] == [
        pytest.approx(-0.00033766915711599607),
        pytest.approx(0.05233766915711599),
    ]
    assert fields[("cond:3", "s", "m")]["correction_level"] == pytest.approx(0.05)
    assert fields[("cond:3", "s", "m")]["ci95_corrected"] == [
        pytest.approx(-0.22281388519862744),
        pytest.approx(0.22281388519862744),
    ]
    assert [v["thin"] for v in fields.values()] == [False, False, False]


def test_bonferronis_corrected_bounds_are_unmoved_by_the_p_value_work():
    """The same regression pin under `bonferroni`, added per round-1 review
    (M2): task 27's original pin exercised `holm` alone, while decision 3
    changes exactly Bonferroni's cell and task 18 rewrites the same
    `corrected_for` two-pass for `fdr_bh`. Captured at `a207702`, before any
    H4d change: every member is corrected at the same level α/m under
    Bonferroni, unlike Holm's per-rank level.
    """
    fields = corrected_fields(_PIN_MEMBERS, "bonferroni")
    assert set(fields) == {
        ("cond:1", "s", "m"),
        ("cond:2", "s", "m"),
        ("cond:3", "s", "m"),
    }
    for key in fields:
        assert set(fields[key]) == _PIN_INNER_KEYS
        assert fields[key]["correction_level"] == pytest.approx(0.05 / 3)
        assert fields[key]["correction"] == "bonferroni"
    assert fields[("cond:2", "s", "m")]["ci95_corrected"] == [
        pytest.approx(-0.18335036277829492),
        pytest.approx(-0.1546496372217051),
    ]
    assert fields[("cond:1", "s", "m")]["ci95_corrected"] == [
        pytest.approx(-0.0027007255565898065),
        pytest.approx(0.05470072555658981),
    ]
    assert fields[("cond:3", "s", "m")]["ci95_corrected"] == [
        pytest.approx(-0.2870072555658981),
        pytest.approx(0.2870072555658981),
    ]
    assert [v["thin"] for v in fields.values()] == [False, False, False]


def test_fdr_bhs_corrected_bounds_are_unmoved_by_the_p_value_work():
    """The same regression pin under `fdr_bh`, added per round-1 review (M2).

    `fdr_bh` is the method task 18 rewrites `corrected_for` two-pass for, and
    with no member of `_PIN_MEMBERS` carrying a `p_value`, `ci95_corrected`
    and `correction_level` must stay `None` for every member — a widened
    two-pass rewrite that started returning an interval, or a `p_value` key,
    here would move this pin.
    """
    fields = corrected_fields(_PIN_MEMBERS, "fdr_bh")
    assert set(fields) == {
        ("cond:1", "s", "m"),
        ("cond:2", "s", "m"),
        ("cond:3", "s", "m"),
    }
    for key in fields:
        assert set(fields[key]) == _PIN_INNER_KEYS
        assert fields[key]["ci95_corrected"] is None
        assert fields[key]["correction_level"] is None
        assert fields[key]["correction"] == "fdr_bh"
        assert fields[key]["thin"] is False


def test_a_member_with_no_interval_and_no_p_value_is_still_outside_the_family():
    """The property decision 4 rests on: widening `family_members` must be a no-op
    for every config that declares no `null_test`.

    `cond:4` carries `diffs` and no `ci95` — the shape `cli` builds for a thin
    pool, a too-short draw or a degenerate column. It must not be counted, and
    the assertion is on the family SIZE rather than on its absence: a member
    wrongly admitted inflates `m`, which tightens every level and narrows every
    corrected interval in the run, in the direction no reader can check.
    """
    counted = family_members(_PIN_MEMBERS)
    assert [m.where for m in counted] == ["cond:1", "cond:2", "cond:3"]
    assert family_shape(counted) == (3, {"comparisons": 3, "metrics": 1})


def test_a_member_carrying_only_a_p_value_is_in_the_family():
    """Decision 4's widening. `cli` builds exactly this member for a thin pool, a
    too-short draw or a degenerate column — while a permutation p-value needs only
    the observed statistic and the null, both of which exist in that state.
    Unwidened, `fdr_bh` would silently adjust nothing for precisely the member
    whose p-value was the only thing it had.

    The assertion is on the family SIZE as well as on membership: a member counted
    changes `m`, which is the quantity every level is derived from."""
    thin = Member(
        where="cond:9",
        step="s",
        metric="m",
        delta=0.4,
        ci95=None,
        pool=None,
        diffs=None,
        declaration_index=0,
        p_value=0.01,
    )
    with_interval = Member(
        where="cond:8",
        step="s",
        metric="m",
        delta=0.4,
        ci95=(0.1, 0.7),
        pool=None,
        diffs=(0.3, 0.4, 0.5),
        declaration_index=1,
    )
    counted = family_members([thin, with_interval])
    assert {m.where for m in counted} == {"cond:9", "cond:8"}
    assert family_shape(counted) == (2, {"comparisons": 2, "metrics": 1})


def test_a_member_with_neither_an_interval_nor_a_p_value_is_still_excluded():
    """The other half, and the one that says the widening is a widening rather
    than a deletion of the predicate."""
    neither = Member(
        where="cond:7",
        step="s",
        metric="m",
        delta=0.4,
        ci95=None,
        pool=None,
        diffs=(0.3, 0.4),
        declaration_index=0,
    )
    assert family_members([neither]) == []


def test_a_p_only_member_ranks_below_every_interval_carrying_one_including_a_zero_ratio():
    """**The discriminating case for the tier, and the reason it is a tuple
    element rather than a sentinel ratio.** `_evidence_ratio` returns exactly
    `0.0` for a member whose `delta` is 0 with a finite width — a REAL member —
    so a p-only member handed `0.0` would sort among those rather than after them.

    Three members: a strong one, a zero-ratio one, and a p-only one. The order
    must be strong, zero-ratio, p-only. A sentinel implementation gives strong,
    then the two in declaration order, which differs from this whenever the
    p-only member was declared first — which it is here, deliberately."""
    p_only = Member(
        where="cond:1",
        step="s",
        metric="m",
        delta=1.0,
        ci95=None,
        pool=None,
        diffs=None,
        declaration_index=0,
        p_value=0.01,
    )
    zero_ratio = Member(
        where="cond:2",
        step="s",
        metric="m",
        delta=0.0,
        ci95=(-0.5, 0.5),
        pool=None,
        diffs=(-0.1, 0.0, 0.1),
        declaration_index=1,
    )
    strong = Member(
        where="cond:3",
        step="s",
        metric="m",
        delta=1.0,
        ci95=(0.9, 1.1),
        pool=None,
        diffs=(0.9, 1.0, 1.1),
        declaration_index=2,
    )
    ranked = [m.where for m in rank_family(family_members([p_only, zero_ratio, strong]))]
    assert ranked == ["cond:3", "cond:2", "cond:1"]


def test_ranking_a_p_only_member_does_not_reach_the_evidence_ratio():
    """`_evidence_ratio` asserts `member.ci95 is not None`, and the widening makes
    that assert reachable. **This test asserts the ranking, not the assert**: a
    test catching the `AssertionError` would be testing the assert, and a mutation
    caught by a crash is not a pin. So the key must short-circuit, and the way to
    see that it does is that ranking a family of p-only members returns them in
    declaration order rather than raising."""
    members = [
        Member(
            where=f"cond:{i}",
            step="s",
            metric="m",
            delta=float(i),
            ci95=None,
            pool=None,
            diffs=None,
            declaration_index=i,
            p_value=0.1 * i,
        )
        for i in (1, 2, 3)
    ]
    assert [m.where for m in rank_family(family_members(members))] == [
        "cond:1",
        "cond:2",
        "cond:3",
    ]


def test_the_exactly_one_rule_is_unchanged_by_the_p_value_field():
    """Recorded as a decision rather than left as an omission: a p-value is not
    evidence, so it does not enter the exactly-one count. A member carrying a
    `ci95` and two evidence kinds is still refused, with or without a p-value."""
    with pytest.raises(ValueError, match="exactly one of pool/diffs/sides"):
        Member(
            where="cond:1",
            step="s",
            metric="m",
            delta=0.1,
            ci95=(0.0, 0.2),
            pool=(0.0, 0.1, 0.2),
            diffs=(0.1,),
            declaration_index=0,
            p_value=0.05,
        )


def _fixture_d(x_has_interval: bool = True) -> list[Member]:
    """Four members at m = 4, with the p-order and the evidence order deliberately
    disagreeing — the only arrangement that can tell decision 1's ruling from an
    implementation that ranks BH on the evidence ratio.

    Evidence ratios 1, 4, 3, 2 give evidence ranks X=4, Y=1, Z=2, W=3 (verified at
    `a207702` by `rank_family`), against p-ranks X=1, Y=2, Z=3, W=4. `x_has_interval`
    is decision 4's variant: X carries a p-value and no interval, and the BH table
    must be IDENTICAL — X already ranks last on evidence, so demoting it to the
    no-interval tier moves no other member's Holm rank either."""

    def mk(where, delta, low, high, index, p, interval=True):
        return Member(
            where=where,
            step="s",
            metric="m",
            delta=delta,
            ci95=(low, high) if interval else None,
            pool=None,
            diffs=tuple(delta + 0.1 * k for k in range(-3, 4)),
            declaration_index=index,
            p_value=p,
        )

    return [
        mk("cond:X", 1.0, 0.0, 2.0, 0, 0.0001999600079984003, x_has_interval),
        mk("cond:Y", 4.0, 3.0, 5.0, 1, 0.22),
        mk("cond:Z", 3.0, 2.0, 4.0, 2, 0.31),
        mk("cond:W", 2.0, 1.0, 3.0, 3, 0.9),
    ]


def test_bh_ranks_on_the_ascending_p_value_and_its_suffix_min_binds():
    """Decision 1, and the single assertion that can tell a two-pass
    implementation from a one-pass one: **Y's own `m/i × p` is 0.44 and it is
    pulled down to Z's 0.41333…**. A single-pass implementation reports 0.44.

    **X is the member the whole ruling is about** — p-rank 1, evidence rank 4 —
    and the two readings differ on it by exactly the factor `m`: BH on the
    ascending p gives `4 × p`, BH on the evidence ratio gives `4/4 × p`, which is
    Holm's answer. So the X assertion is the ordering assertion and the Y/Z pair
    is the accumulation assertion; neither alone is enough.

    The Y/Z TIE is the signature of the bind, which means a mutation swapping
    those two members is invisible on those cells — the ordering is pinned on X
    and W, whose adjusted values are unique to them."""
    fields = corrected_for(_fixture_d(), "fdr_bh", 4, {"comparisons": 4, "metrics": 1})
    adjusted = {where: v["p_value_corrected"] for (where, _, _), v in fields.items()}
    assert adjusted["cond:X"] == pytest.approx(0.0007998400319936012)
    assert adjusted["cond:Y"] == pytest.approx(0.41333333333333333)
    assert adjusted["cond:Z"] == pytest.approx(0.41333333333333333)
    assert adjusted["cond:W"] == pytest.approx(0.9)
    assert adjusted["cond:Y"] != pytest.approx(0.44)


def test_fdr_bh_leaves_every_corrected_interval_null_by_design():
    """`_level_for` returns `None` for `fdr_bh` and that is the documented
    behaviour, not a gap: controlling a false discovery rate is a statement about
    a set, not a bound on any one comparison. Asserted beside the adjusted
    p-values, because "reports nothing" and "reports only the p" are the two
    states this method has been in."""
    fields = corrected_for(_fixture_d(), "fdr_bh", 4, {"comparisons": 4, "metrics": 1})
    assert all(v["ci95_corrected"] is None for v in fields.values())
    assert all(v["correction_level"] is None for v in fields.values())
    assert all(v["p_value_corrected"] is not None for v in fields.values())


def test_holms_adjusted_p_is_the_p_at_this_members_own_level_and_is_not_monotone():
    """Decision 2. Holm's level is α/(m − i + 1) at the EVIDENCE rank, so the p at
    that level is `p × (m − i + 1)`, clipped at 1.

    **The non-monotonicity is asserted, not merely tolerated**: Y's adjusted 0.88
    sits below Z's 0.93 while Y's raw p is smaller — the evidence ranking showing
    through. A later slice "fixing" that by ranking Holm on p would reintroduce
    the two-orderings problem decision 1 avoids, and this assertion is what would
    fail if it did.

    W is where the clip is asserted: 0.9 × 2 = 1.8."""
    fields = corrected_for(_fixture_d(), "holm", 4, {"comparisons": 4, "metrics": 1})
    adjusted = {where: v["p_value_corrected"] for (where, _, _), v in fields.items()}
    assert adjusted["cond:Y"] == pytest.approx(0.88)
    assert adjusted["cond:Z"] == pytest.approx(0.9299999999999999)
    assert adjusted["cond:W"] == pytest.approx(1.0)
    assert adjusted["cond:X"] == pytest.approx(0.0001999600079984003)
    assert adjusted["cond:Y"] < adjusted["cond:Z"]


def test_bonferroni_reports_the_p_at_alpha_over_m_for_every_member():
    """Decision 3: the table's Bonferroni `—` was an asymmetry with no ground, and
    it is amended. Every member gets `min(1, p × m)`, so Z and W both clip.

    Holm and Bonferroni necessarily AGREE at evidence rank 1 (both are α/m
    there), which is Y — so the discriminating members for that pair are Z (0.93
    against 1.0) and X (a factor of 4), and both are asserted."""
    fields = corrected_for(_fixture_d(), "bonferroni", 4, {"comparisons": 4, "metrics": 1})
    adjusted = {where: v["p_value_corrected"] for (where, _, _), v in fields.items()}
    assert adjusted["cond:X"] == pytest.approx(0.0007998400319936012)
    assert adjusted["cond:Y"] == pytest.approx(0.88)
    assert adjusted["cond:Z"] == pytest.approx(1.0)
    assert adjusted["cond:W"] == pytest.approx(1.0)


def test_the_bh_table_is_identical_when_one_member_carries_no_interval():
    """Decision 4's widening, made visible as four unchanged literals rather than
    as an absence. Unwidened, X vanishes and `m` drops to 3, which moves every
    other row.

    Asserted as an equality between the two tables rather than as eight literals:
    the relation is the claim, and a per-member literal restated twice would pass
    if both had moved together."""
    with_interval = corrected_for(_fixture_d(True), "fdr_bh", 4, {"comparisons": 4, "metrics": 1})
    without = corrected_for(_fixture_d(False), "fdr_bh", 4, {"comparisons": 4, "metrics": 1})
    assert {k: v["p_value_corrected"] for k, v in with_interval.items()} == {
        k: v["p_value_corrected"] for k, v in without.items()
    }


def test_a_member_with_no_p_value_gets_no_p_value_corrected_key():
    """Absent, not null: an explicit null would claim an adjustment was attempted
    and found nothing to do, which is the same distinction `ci95_corrected` makes
    under `correction: none`."""
    members = [
        Member(
            where="cond:1",
            step="s",
            metric="m",
            delta=0.5,
            ci95=(0.4, 0.6),
            pool=None,
            diffs=(0.4, 0.5, 0.6),
            declaration_index=0,
        )
    ]
    fields = corrected_for(members, "holm", 1, {"comparisons": 1, "metrics": 1})
    assert "p_value_corrected" not in fields[("cond:1", "s", "m")]


def test_a_p_only_member_does_not_report_a_thin_correction():
    """**A defect the widening would otherwise introduce, and the spec names only
    its `fdr_bh` half.** `corrected_for` computes `thin = level is not None and
    bounds is None`, and `_corrected_bounds` falls through to `None` for a member
    carrying none of the three evidence kinds — so under `holm` a p-only member
    would set `thin: True` and the caller would emit `W-STATS-CORRECTED-THIN`,
    whose message says the RESAMPLE'S DRAWS could not support the level. That is
    false of a member that never had an interval to build.

    Asserted as `thin is False` rather than by looking for the warning: this
    function returns the flag and `cli` reads it, so the flag is where the fault
    lives."""
    members = [
        Member(
            where="cond:1",
            step="s",
            metric="m",
            delta=0.5,
            ci95=None,
            pool=None,
            diffs=None,
            declaration_index=0,
            p_value=0.02,
        ),
        Member(
            where="cond:2",
            step="s",
            metric="m",
            delta=0.5,
            ci95=(0.4, 0.6),
            pool=None,
            diffs=(0.4, 0.5, 0.6),
            declaration_index=1,
        ),
    ]
    fields = corrected_for(members, "holm", 2, {"comparisons": 2, "metrics": 1})
    assert fields[("cond:1", "s", "m")]["thin"] is False
    assert fields[("cond:1", "s", "m")]["ci95_corrected"] is None
