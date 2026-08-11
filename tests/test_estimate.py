import dataclasses

import pytest

from publishable import Estimate


def test_an_estimate_is_importable_from_the_package_root():
    """`reference.md` § The importable surface: everything a user writes against
    is imported from `publishable` itself, and that section's table already
    enumerates `Estimate`. A user reaching into `publishable.estimate` would be
    depending on where core happens to keep the file."""
    assert Estimate(value=0.031).value == 0.031


def test_only_value_is_required():
    """A summary step may report a number with no interval — `converged: True`
    beside it in the documented example is a bare value, and a bare `Estimate`
    is the same claim with the marking."""
    est = Estimate(value=0.031)
    assert est.ci95 is None
    assert est.n is None
    assert est.method is None


def test_it_is_frozen():
    """Core stores what the step returned. A mutable Estimate would let a later
    step or a template edit a number the record attributes to the step that
    computed it."""
    est = Estimate(value=0.031)
    with pytest.raises(dataclasses.FrozenInstanceError):
        est.value = 0.999


def test_it_constructs_without_validating():
    """Every rule about an Estimate is a diagnostic core emits, not an exception
    user code trips over: a `ValueError` from a constructor inside a plugin
    surfaces as a bare traceback with no identifier, and this repo's contract is
    that a failure prints a stable `E-` code. `ci95` without `method` is
    `E-STEP-ESTIMATE-METHOD` at coercion time (Task 2), not a raise here."""
    est = Estimate(value=0.031, ci95=[0.008, 0.055])
    assert est.method is None
