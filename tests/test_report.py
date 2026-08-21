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
import subprocess
from pathlib import Path

import pytest
import yaml

from publishable import BaseReport
from publishable.artifacts import ReportIO, derive_step_scopes_and_repeats
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


# ---------------------------------------------------------------------------
# H8c task 2 — `ReportIO` against a REAL run record, at three repeats and at
# one. Deliberately parallel to `tests/test_artifacts.py`'s
# `test_h8c_arm_c_read_condition_resolves_at_three_repeats_and_at_one`
# (task 17's guard pin, arm C), which exercises the identical property
# through a real `summary` step's `io.read_condition` instead. Arm C is not
# this task's to edit and never moves in this slice; this test is the
# `ReportIO`-side half of the load-bearing mutation (M16): both must fail
# when the extracted traversal's repeat-segment rule loses its `> 1` guard,
# or the extraction was a copy rather than a share.
# ---------------------------------------------------------------------------


def _build_and_run_for_report_io(tmp_path: Path, n_repeats: int) -> dict:
    """One real project, deliberately smaller than arm C's: a
    condition-scoped `step02_fit` writes `model.json`; the generated
    (repeat-scoped) starter writes `units.parquet` via `io.record`. No
    `summary` step — `ReportIO` reads both back directly, from the test,
    never from inside a step.
    """
    from publishable.cli import main
    from publishable.generators.experiment import generate_experiment
    from publishable.generators.step import generate_step

    root = tmp_path / "proj"
    data = tmp_path / "data"
    results = tmp_path / "results"
    data.mkdir(parents=True)
    rows = "\n".join(f"p{i}" for i in range(10))
    (data / "index.csv").write_text(f"patient_id\n{rows}\n")
    assert main(["new", str(root)]) == 0
    cfg = generate_experiment(
        repo_root=root,
        name="cohort-pilot",
        template_name="generic",
        input_dir=str(data),
        output_dir=str(results),
    )
    generate_step(repo_root=root, experiment="cohort-pilot", step_name="fit")
    (root / "src" / "cohort_pilot" / "steps" / "step02_fit.py").write_text(
        "from publishable import BaseStep\n\n\n"
        "class Step(BaseStep):\n"
        '    scope = "condition"\n\n'
        "    def run(self, cfg, io):\n"
        '        io.write("model.json", {"m": cfg.parameters.analysis.method})\n'
        "        return {}\n"
    )
    doc = yaml.safe_load(cfg.read_text())
    doc["metadata"]["description"] = "H8c task 2 ReportIO"
    doc["metadata"]["authors"] = ["Kyungjoon Lee"]
    doc["replication"] = {"repeats": [{"kind": "seed", "n": n_repeats}]}
    cfg.write_text(yaml.safe_dump(doc))
    for args in (
        ["add", "."],
        ["-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "report io"],
    ):
        subprocess.run(["git", *args], cwd=root, check=True)
    assert main(["run", str(cfg)]) == 0
    run_dir = next(results.glob("run_*"))
    record = yaml.safe_load((run_dir / "run.yaml").read_text())
    return {"run_dir": run_dir, "record": record}


def _report_io_from_record(built: dict) -> ReportIO:
    record = built["record"]
    execution = record["execution"]
    step_scopes, repeats = derive_step_scopes_and_repeats(execution)
    conditions = [(c["index"], c["label"]) for c in record["results"]["conditions"]]
    return ReportIO(
        run_dir=built["run_dir"],
        input_dir=Path(record["config"]["data"]["input_dir"]),
        conditions=conditions,
        repeats=repeats,
        step_scopes=step_scopes,
    )


def test_report_io_resolves_the_same_artifacts_at_three_repeats_and_at_one(tmp_path: Path):
    """The measured discriminator (§ Corrections, correction 2): a
    repeat-scoped step's `execution` entry nests repeat labels even when the
    run resolved exactly one, while its directory has already collapsed.
    `ReportIO`, built from the record alone via `derive_step_scopes_and_repeats`,
    must read the same values at both repeat counts that arm C's `summary`
    step reads through `StepIO` — over the SAME shared traversal.
    """
    three = _build_and_run_for_report_io(tmp_path / "three", 3)
    one = _build_and_run_for_report_io(tmp_path / "one", 1)

    for built in (three, one):
        io = _report_io_from_record(built)
        assert io.read_condition(0, "step02_fit", "model.json") == {"m": "pearson"}
        repeat = io.repeats[0]
        units = io.read_condition(0, "step01_summarize_units", "units.parquet", repeat=repeat)
        assert len(units) == 10
