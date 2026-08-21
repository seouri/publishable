# tests/test_report.py
"""`BaseReport` and `Section`. docs/reference.md § A report override, § The
importable surface. H8c task 1 — see
`docs/superpowers/plans/2026-08-21-report-study.md` task 1 and
`docs/superpowers/specs/2026-08-21-report-study-design.md` Decision 2.

Nothing here dispatches; `report.py` builds the API every override is
written against, and there is no `run`/`io` construction yet.
"""

import dataclasses
import inspect

import pytest

from publishable import BaseReport
from publishable.report import Section


def test_section_is_frozen_and_carries_title_and_body():
    section = Section(title="Method agreement", body="some markdown")
    assert section.title == "Method agreement"
    assert section.body == "some markdown"
    with pytest.raises(dataclasses.FrozenInstanceError):
        section.title = "renamed"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        section.body = "replaced"  # type: ignore[misc]


def test_section_body_may_be_a_mapping_core_can_table():
    section = Section(title="Conditions", body={"pearson": 0.581, "spearman": 0.607})
    assert section.body == {"pearson": 0.581, "spearman": 0.607}


def test_section_frozen_does_not_deep_freeze_a_mapping_body():
    """The docstring's own claim, checked: a frozen `Section` guarantees a
    re-yielded standard section cannot be REBOUND — it says nothing about
    the mapping object `body` happens to hold. Reaching into that mapping
    and mutating it in place is exactly the M14 hazard task 5's brief
    inherits, since core has no standard section with a mapping body until
    that task builds one; this only pins that the type does not (and does
    not claim to) block it.
    """
    body = {"pearson": 0.581}
    section = Section(title="Conditions", body=body)
    body["pearson"] = 999.0
    assert section.body["pearson"] == 999.0


def test_base_report_section_constructs_one():
    report = BaseReport()
    section = report.section("Method agreement", body="markdown text")
    assert section == Section(title="Method agreement", body="markdown text")


def test_base_report_sections_is_a_generator_yielding_nothing():
    report = BaseReport()
    result = report.sections(run={}, io=object())
    assert inspect.isgenerator(result)
    assert list(result) == []


def test_an_override_composes_with_yield_from_super():
    """The documented composition shape: `yield from super().sections(run,
    io)` then more. The base yields nothing yet (tasks 5 and 6 fill it), so
    this pins that an override's own sections still arrive, in the order
    yielded, alongside whatever the base contributes.
    """

    class Report(BaseReport):
        def sections(self, run, io):
            yield from super().sections(run, io)
            yield self.section("First", body="a")
            yield self.section("Second", body="b")

    titles = [s.title for s in Report().sections(run={}, io=object())]
    assert titles == ["First", "Second"]


def test_an_override_omitting_yield_from_yields_none_of_the_standard_sections():
    """ "Omitting the `yield from` yields none of them" (Decision 2) — pinned
    now, ahead of tasks 5/6 giving the base something to omit, because the
    override's own choice not to compose is independent of what the base
    eventually yields.
    """

    class Report(BaseReport):
        def sections(self, run, io):
            yield self.section("Only mine", body="a")

    titles = [s.title for s in Report().sections(run={}, io=object())]
    assert titles == ["Only mine"]


def test_base_report_declares_no_format_attribute():
    """`format` has no base default (Decision 2, task 1 step 2) — a class
    declaring none is refused at render (task 7's `E-REPORT-FORMAT`), not
    silently defaulted. Checked directly on the class, since a default
    would make "declared" and "omitted" indistinguishable at that refusal.
    """
    assert not hasattr(BaseReport, "format")
    assert "format" not in vars(BaseReport)


# ---------------------------------------------------------------------------
# Carried to task 5's brief, by name, per this task's step 6: M14's
# render-level arm — an override reaching into a STANDARD section's mapping
# `body` and mutating a number before yielding it, then asserting the
# mutated figure DOES reach the page when `frozen=True` is removed from
# `Section` and DOES NOT (raises loudly) with it in place — cannot be
# written here. No standard section with a mapping body exists until task 5
# builds one. What this task pins instead, above, is the frozen-ness
# assertion in isolation: constructing a `Section` and asserting attribute
# assignment raises `dataclasses.FrozenInstanceError`.
# ---------------------------------------------------------------------------
