import math

import pytest

from publishable.stats import mean_of, t_over_units


def test_interval_matches_a_published_critical_value():
    """t(0.975, df=9) = 2.262. Ten values, mean 10, sample sd exactly 1."""
    values = [10 + d for d in (-1.5, -1.5, -0.5, -0.5, 0.0, 0.0, 0.5, 0.5, 1.5, 1.5)]
    n = len(values)
    sd = math.sqrt(sum((v - 10) ** 2 for v in values) / (n - 1))
    expected_half = 2.262 * sd / math.sqrt(n)
    iv = t_over_units(values)
    assert iv is not None
    assert iv.method == "t_over_units"
    assert abs((iv.high - iv.low) / 2 - expected_half) < 1e-3
    assert abs((iv.low + iv.high) / 2 - 10) < 1e-12


def test_interval_is_hand_checkable_on_a_tiny_dataset():
    """values [1, 2, 3, 4]: mean 2.5, sample sd sqrt(5/3)=1.29099,
    sem 0.645497, t(0.975, df=3)=3.182, half-width 2.0540."""
    iv = t_over_units([1.0, 2.0, 3.0, 4.0])
    assert iv is not None
    assert abs(iv.low - (2.5 - 2.0540)) < 1e-3
    assert abs(iv.high - (2.5 + 2.0540)) < 1e-3


def test_the_t_interval_is_wider_than_normal_and_converges():
    """The check that would catch shipping z by mistake."""
    from statistics import NormalDist

    def normal_half(vals):
        n = len(vals)
        m = sum(vals) / n
        sd = math.sqrt(sum((v - m) ** 2 for v in vals) / (n - 1))
        return NormalDist().inv_cdf(0.975) * sd / math.sqrt(n)

    small = [float(i % 7) for i in range(8)]
    large = [float(i % 7) for i in range(4000)]
    small_iv, large_iv = t_over_units(small), t_over_units(large)
    assert small_iv is not None and large_iv is not None
    small_ratio = ((small_iv.high - small_iv.low) / 2) / normal_half(small)
    large_ratio = ((large_iv.high - large_iv.low) / 2) / normal_half(large)
    assert small_ratio > 1.15, "t must be materially wider than z at n=8"
    assert 1.0 < large_ratio < 1.002, "t must converge to z as n grows"


@pytest.mark.parametrize("values", [[], [3.0]])
def test_fewer_than_two_values_has_no_interval(values):
    """df = n - 1, so one value has no dispersion to describe."""
    assert t_over_units(values) is None


def test_zero_variance_yields_a_degenerate_but_real_interval():
    iv = t_over_units([5.0, 5.0, 5.0])
    assert iv is not None and iv.low == iv.high == 5.0


def test_mean_of_is_none_for_an_empty_sequence():
    assert mean_of([]) is None
    assert mean_of([1.0, 2.0]) == 1.5


def test_confidence_widens_the_interval():
    narrow = t_over_units([1.0, 2.0, 3.0, 4.0], confidence=0.80)
    wide = t_over_units([1.0, 2.0, 3.0, 4.0], confidence=0.99)
    assert narrow is not None and wide is not None
    assert (wide.high - wide.low) > (narrow.high - narrow.low)
