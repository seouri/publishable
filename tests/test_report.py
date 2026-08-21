# tests/test_report.py
"""`BaseReport`, `Section`, override discovery, and `command_report`.
docs/reference.md § A report override, § The importable surface, §
Operation commands' `report` row. H8c tasks 1-3 built `BaseReport` and
discovery; task 8 wires `report <run.yaml>` into `main` end to end — see
`docs/superpowers/plans/2026-08-21-report-study.md` and
`docs/superpowers/specs/2026-08-21-report-study-design.md` Decisions 1-3,
6-7.

Task 8's own brief: "No assertion in this task may be made by calling
`command_report` directly" — every test below task 8's own section header
goes through `main(["report", ...])`, never through `command_report` or
`render_with_override` in isolation, on H7d Part A's own precedent (its
only Critical was invisible to every direct-call probe).
"""

import dataclasses
import inspect
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml
from tests.test_cli import run_a_project

from publishable import BaseReport
from publishable.apparatus import apparatus_hash
from publishable.artifacts import ReportIO, derive_step_scopes_and_repeats
from publishable.cli import main
from publishable.diagnostics import (
    EXIT_FAILED,
    EXIT_OK,
    EXIT_PARTIAL,
    EXIT_WRONG,
)
from publishable.errors import ContractError
from publishable.lineage import read_record_file
from publishable.report import (
    Section,
    attrition_section,
    conditions_section,
    deltas_section,
    hypotheses_section,
    read_bundle,
    render_bundle,
    render_html,
    render_markdown,
    render_report,
    render_with_override,
    report_form,
)


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


def test_base_report_sections_is_a_generator_yielding_all_four_standard_sections():
    """Task 6 completes the base: all four standard sections, in Decision
    5's order, over an empty `run`. Conditions, Deltas and Hypothesis
    verdicts each have nothing to say about an empty record and yield an
    empty `rows` list; Attrition still reports the (missing) top-level
    `status` — it is not refused for lack of content either, it just has
    one row to show for it.
    """
    report = BaseReport()
    result = report.sections(run={}, io=object())
    assert inspect.isgenerator(result)
    sections = list(result)
    assert [s.title for s in sections] == [
        "Conditions",
        "Deltas",
        "Hypothesis verdicts",
        "Attrition",
    ]
    by_title = {s.title: s for s in sections}
    assert by_title["Conditions"].body == {"rows": []}
    assert by_title["Deltas"].body == {"rows": []}
    assert by_title["Hypothesis verdicts"].body == {"rows": []}
    assert by_title["Attrition"].body == {"rows": [{"kind": "status", "status": None}]}


def test_an_override_composes_with_yield_from_super():
    """The documented composition shape: `yield from super().sections(run,
    io)` then more. The base yields all four standard sections ahead of an
    override's own, so this pins that an override's own sections still
    arrive, in the order yielded, AFTER whatever the base contributes.
    """

    class Report(BaseReport):
        def sections(self, run, io):
            yield from super().sections(run, io)
            yield self.section("First", body="a")
            yield self.section("Second", body="b")

    titles = [s.title for s in Report().sections(run={}, io=object())]
    assert titles == [
        "Conditions",
        "Deltas",
        "Hypothesis verdicts",
        "Attrition",
        "First",
        "Second",
    ]


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


# ---------------------------------------------------------------------------
# H8c task 3 — override discovery, alone in its batch because it is this
# slice's proxy risk (docs/superpowers/specs/2026-08-21-report-study-design.md
# Decision 3; docs/superpowers/plans/2026-08-21-report-study.md task 3).
# The named FIXTURES (O, the M2 fixture, O2, V) each run a REAL project
# through `main(["run", ...])`, because the property under test is what a
# real `environment/repo_root.txt` and a real `config.entrypoint` say. The
# shape-refusal tests immediately below build records and run directories
# by hand — that is the point of THOSE tests, which exist to prove a
# hand-edited record or a hand-edited artifact is refused rather than
# silently read as "no override".
# ---------------------------------------------------------------------------


def _build_project(root: Path, data: Path, results: Path, *, name: str = "cohort-pilot") -> dict:
    """One real, committed, run project — no override, no extra step. The
    minimum every discovery fixture starts from: a real
    `environment/repo_root.txt` and a real `config.entrypoint`.
    """
    from publishable.cli import main
    from publishable.generators.experiment import generate_experiment

    data.mkdir(parents=True, exist_ok=True)
    rows = "\n".join(f"p{i}" for i in range(10))
    (data / "index.csv").write_text(f"patient_id\n{rows}\n")
    assert main(["new", str(root)]) == 0
    cfg = generate_experiment(
        repo_root=root,
        name=name,
        template_name="generic",
        input_dir=str(data),
        output_dir=str(results),
    )
    doc = yaml.safe_load(cfg.read_text())
    doc["metadata"]["description"] = "H8c task 3 override discovery"
    doc["metadata"]["authors"] = ["Kyungjoon Lee"]
    cfg.write_text(yaml.safe_dump(doc))
    for args in (
        ["add", "."],
        ["-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "override discovery"],
    ):
        subprocess.run(["git", *args], cwd=root, check=True)
    assert main(["run", str(cfg)]) == 0
    run_dir = next(results.glob("run_*"))
    record = yaml.safe_load((run_dir / "run.yaml").read_text())
    return {"root": root, "run_dir": run_dir, "record": record, "pkg": name.replace("-", "_")}


def _write_report(root: Path, pkg: str, body: str) -> None:
    (root / "src" / pkg / "report.py").write_text(body)


def test_no_report_module_is_no_override_not_a_fail_open(tmp_path: Path):
    """The ordinary case: `generate report` is opt-in, so a project that
    never wrote one renders standard sections only. `render` receives
    `None`, never a silently-swallowed error.
    """
    built = _build_project(tmp_path / "proj", tmp_path / "data", tmp_path / "results")
    result = render_with_override(built["run_dir"], built["record"], render=lambda cls: cls)
    assert result is None


def test_report_module_raising_on_import_is_e_report_override_import(tmp_path: Path):
    """Distinguished from "no module" by the import machinery's own
    answer, never by catching everything: this module DOES exist, and
    raises while importing.
    """
    built = _build_project(tmp_path / "proj", tmp_path / "data", tmp_path / "results")
    _write_report(built["root"], built["pkg"], "raise RuntimeError('boom, deliberately')\n")
    with pytest.raises(ContractError) as exc_info:
        render_with_override(built["run_dir"], built["record"], render=lambda cls: cls)
    assert exc_info.value.code == "E-REPORT-OVERRIDE-IMPORT"


def test_report_module_importing_a_missing_dependency_is_also_e_report_override_import(
    tmp_path: Path,
):
    """A `ModuleNotFoundError` for a DIFFERENT module than the one this
    call tried to import is a failure, not an absence — the discriminator
    is `ModuleNotFoundError.name`, not the exception type alone.
    """
    built = _build_project(tmp_path / "proj", tmp_path / "data", tmp_path / "results")
    _write_report(built["root"], built["pkg"], "import this_dependency_does_not_exist\n")
    with pytest.raises(ContractError) as exc_info:
        render_with_override(built["run_dir"], built["record"], render=lambda cls: cls)
    assert exc_info.value.code == "E-REPORT-OVERRIDE-IMPORT"


def test_report_module_with_no_base_report_subclass_is_e_report_override_class(tmp_path: Path):
    built = _build_project(tmp_path / "proj", tmp_path / "data", tmp_path / "results")
    _write_report(built["root"], built["pkg"], "class NotAReport:\n    pass\n")
    with pytest.raises(ContractError) as exc_info:
        render_with_override(built["run_dir"], built["record"], render=lambda cls: cls)
    assert exc_info.value.code == "E-REPORT-OVERRIDE-CLASS"


def test_report_module_with_two_base_report_subclasses_is_e_report_override_class(
    tmp_path: Path,
):
    """ "More than one" is refused rather than resolved by definition
    order — order is exactly the proxy this function forbids, and a
    project has one report.
    """
    built = _build_project(tmp_path / "proj", tmp_path / "data", tmp_path / "results")
    _write_report(
        built["root"],
        built["pkg"],
        "from publishable import BaseReport\n\n\n"
        "class First(BaseReport):\n    format = 'markdown'\n\n\n"
        "class Second(BaseReport):\n    format = 'markdown'\n",
    )
    with pytest.raises(ContractError) as exc_info:
        render_with_override(built["run_dir"], built["record"], render=lambda cls: cls)
    assert exc_info.value.code == "E-REPORT-OVERRIDE-CLASS"


def test_a_base_report_merely_imported_does_not_count_as_a_second_definition(tmp_path: Path):
    """The `obj.__module__ == module.__name__` filter, pinned: it is what
    stands in for H7a's "marker on the class" proxy, closing the same
    question ("does THIS module own this class") on the direct fact
    instead. `reference.md` § A report override documents "a renderer
    several experiments share is an ordinary import from a plugin, called
    by each one's override" as the supported route for sharing a base
    class across report modules — this module imports one and ALSO
    defines its own. Deleting the filter would count the imported name
    too and wrongly refuse this legitimate module with
    `E-REPORT-OVERRIDE-CLASS`, "defines 2, not exactly one".
    """
    built = _build_project(tmp_path / "proj", tmp_path / "data", tmp_path / "results")
    (built["root"] / "src" / built["pkg"] / "shared_report.py").write_text(
        "from publishable import BaseReport\n\n\n"
        "class SharedReport(BaseReport):\n"
        "    format = 'markdown'\n"
    )
    _write_report(
        built["root"],
        built["pkg"],
        f"from {built['pkg']}.shared_report import SharedReport\n"
        "from publishable import BaseReport\n\n\n"
        "class Report(BaseReport):\n"
        "    format = 'markdown'\n\n"
        "    def sections(self, run, io):\n"
        "        yield self.section('LOCAL', body=str(SharedReport))\n",
    )

    def render(cls):
        assert cls is not None
        assert cls.__name__ == "Report"
        return list(cls().sections(built["record"], object()))[0].title

    title = render_with_override(built["run_dir"], built["record"], render=render)
    assert title == "LOCAL"


def test_missing_repo_root_file_is_refused_with_a_remedy_not_a_fail_open(tmp_path: Path):
    run_dir = tmp_path / "run_dir"
    (run_dir / "environment").mkdir(parents=True)
    with pytest.raises(ContractError) as exc_info:
        render_with_override(run_dir, record={}, render=lambda cls: cls)
    assert exc_info.value.code == "E-REPORT-OVERRIDE-REPO"


def test_empty_repo_root_file_is_refused_with_a_remedy_not_a_fail_open(tmp_path: Path):
    run_dir = tmp_path / "run_dir"
    (run_dir / "environment").mkdir(parents=True)
    (run_dir / "environment" / "repo_root.txt").write_text("")
    with pytest.raises(ContractError) as exc_info:
        render_with_override(run_dir, record={}, render=lambda cls: cls)
    assert exc_info.value.code == "E-REPORT-OVERRIDE-REPO"


def test_repo_root_naming_a_non_directory_is_refused_with_a_remedy_not_a_fail_open(
    tmp_path: Path,
):
    run_dir = tmp_path / "run_dir"
    (run_dir / "environment").mkdir(parents=True)
    not_a_dir = tmp_path / "plain_file.txt"
    not_a_dir.write_text("not a directory")
    (run_dir / "environment" / "repo_root.txt").write_text(f"{not_a_dir}\n")
    with pytest.raises(ContractError) as exc_info:
        render_with_override(run_dir, record={}, render=lambda cls: cls)
    assert exc_info.value.code == "E-REPORT-OVERRIDE-REPO"


def _run_dir_with_good_repo_root(tmp_path: Path) -> Path:
    run_dir = tmp_path / "run_dir"
    (run_dir / "environment").mkdir(parents=True)
    (run_dir / "environment" / "repo_root.txt").write_text(f"{tmp_path}\n")
    return run_dir


@pytest.mark.parametrize(
    "record",
    [
        {},
        {"config": {}},
        {"config": {"entrypoint": None}},
        {"config": {"entrypoint": ""}},
        {"config": {"entrypoint": ["cohort_pilot.experiment", "Experiment"]}},
        {"config": {"entrypoint": "no_colon_at_all"}},
        {"config": {"entrypoint": ":missing_module"}},
        {"config": {"entrypoint": "cohort_pilot.experiment:"}},
    ],
)
def test_bad_entrypoint_shapes_are_refused_with_a_remedy_not_a_fail_open(
    tmp_path: Path, record: dict
):
    """Absent, empty, non-`str`, or malformed — every shape but a
    well-formed `<module>:<attribute>` string. A hand-edited record can
    hold any of these, and `None` reaching `.partition` would be a
    traceback rather than a diagnostic.
    """
    run_dir = _run_dir_with_good_repo_root(tmp_path)
    with pytest.raises(ContractError) as exc_info:
        render_with_override(run_dir, record, render=lambda cls: cls)
    assert exc_info.value.code == "E-REPORT-OVERRIDE-ENTRYPOINT"


def test_fixture_o_m1_two_packages_one_named_by_entrypoint(tmp_path: Path):
    """**M1**: discover by scanning `src/*/report.py` instead of from
    `entrypoint`. THREE packages sit side by side in the same `src/`, each
    with its own `BaseReport` override and its own titled section; only
    one is named by this run's `entrypoint`. A scan finds all three and
    must pick — the correct answer is the one `entrypoint` names, never
    whichever a scan happens to prefer.

    Two decoys, not one, and on PURPOSE: a single decoy only ever
    distinguishes ONE ordering from the honest answer, so a decoy that
    happens to sort on the same side as a scan's own bias (first, or last)
    passes by coincidence rather than by the fixture actually ruling that
    reading out — this is the exact shape of this task's own first draft,
    which used one decoy sorting after the real package and so left a
    scan-last mutation undetected (whole-branch review, Major 3). A decoy
    on EACH side (`aaa_` sorting before, `zzz_` sorting after) rules out
    scan-first AND scan-last at once; no alphabetical pick a scan can make
    is the right one. On a one-package project every reading is
    byte-identical, which is why this fixture needs more than one.
    """
    built = _build_project(tmp_path / "proj", tmp_path / "data", tmp_path / "results")
    _write_report(
        built["root"],
        built["pkg"],
        "from publishable import BaseReport\n\n\n"
        "class Report(BaseReport):\n"
        "    format = 'markdown'\n\n"
        "    def sections(self, run, io):\n"
        "        yield self.section('ENTRYPOINT-NAMED', body='x')\n",
    )
    for decoy_name in ("aaa_decoy_pkg", "zzz_decoy_pkg"):
        decoy_pkg = built["root"] / "src" / decoy_name
        decoy_pkg.mkdir(parents=True)
        (decoy_pkg / "__init__.py").write_text("")
        (decoy_pkg / "report.py").write_text(
            "from publishable import BaseReport\n\n\n"
            "class Report(BaseReport):\n"
            "    format = 'markdown'\n\n"
            "    def sections(self, run, io):\n"
            f"        yield self.section({decoy_name.upper()!r}, body='x')\n",
        )

    def render(cls):
        assert cls is not None
        return list(cls().sections(built["record"], object()))[0].title

    title = render_with_override(built["run_dir"], built["record"], render=render)
    assert title == "ENTRYPOINT-NAMED"


def test_m2_repo_root_comes_from_the_file_not_from_provenance_git_repo_root(tmp_path: Path):
    """**M2**: read `repo_root` from `provenance.git.repo_root` instead of
    `environment/repo_root.txt`. Both branches find *a* repo — target's
    own record is hand-edited so its `provenance.git.repo_root` names a
    DIFFERENT, real project — so an assertion on "an override was found"
    cannot see the bug; the assertion has to be on which section title
    comes back. `environment/repo_root.txt` is left untouched and correct,
    so the honest reading resolves the target's own override regardless
    of what `provenance` claims.
    """
    target = _build_project(
        tmp_path / "target", tmp_path / "target_data", tmp_path / "target_results"
    )
    other = _build_project(tmp_path / "other", tmp_path / "other_data", tmp_path / "other_results")
    assert target["pkg"] == other["pkg"]  # same scaffold name; only the repo differs

    _write_report(
        target["root"],
        target["pkg"],
        "from publishable import BaseReport\n\n\n"
        "class Report(BaseReport):\n"
        "    format = 'markdown'\n\n"
        "    def sections(self, run, io):\n"
        "        yield self.section('TARGET-PROJECT', body='x')\n",
    )
    _write_report(
        other["root"],
        other["pkg"],
        "from publishable import BaseReport\n\n\n"
        "class Report(BaseReport):\n"
        "    format = 'markdown'\n\n"
        "    def sections(self, run, io):\n"
        "        yield self.section('OTHER-PROJECT', body='x')\n",
    )

    record = dict(target["record"])
    record["provenance"] = dict(record.get("provenance") or {})
    record["provenance"]["git"] = dict(record["provenance"].get("git") or {})
    record["provenance"]["git"]["repo_root"] = str(other["root"])  # hand-edited, wrong on purpose

    def render(cls):
        assert cls is not None
        return list(cls().sections({}, object()))[0].title

    title = render_with_override(target["run_dir"], record, render=render)
    assert title == "TARGET-PROJECT"


def test_fixture_o2_m15_same_package_name_two_projects_in_one_process(tmp_path: Path):
    """**M15**: delete the `sys.modules` purge, or narrow it to the bare
    root package (dropping `root_pkg + "."`). Two SEPARATE projects
    declaring the SAME package name (both scaffolded from `cohort-pilot`),
    rendered in SEQUENCE in this one process, each asserting its OWN
    section title. With the purge, each render imports its own module;
    without it, the second render is served the first's cached one. On a
    fresh process with a single project the two readings are
    byte-identical, which is why this fixture needs two projects.
    """
    first = _build_project(
        tmp_path / "first" / "proj", tmp_path / "first" / "data", tmp_path / "first" / "results"
    )
    second = _build_project(
        tmp_path / "second" / "proj", tmp_path / "second" / "data", tmp_path / "second" / "results"
    )
    assert first["pkg"] == second["pkg"]  # the whole point: identical package names

    _write_report(
        first["root"],
        first["pkg"],
        "from publishable import BaseReport\n\n\n"
        "class Report(BaseReport):\n"
        "    format = 'markdown'\n\n"
        "    def sections(self, run, io):\n"
        "        yield self.section('FIRST-PROJECT', body='x')\n",
    )
    _write_report(
        second["root"],
        second["pkg"],
        "from publishable import BaseReport\n\n\n"
        "class Report(BaseReport):\n"
        "    format = 'markdown'\n\n"
        "    def sections(self, run, io):\n"
        "        yield self.section('SECOND-PROJECT', body='x')\n",
    )

    def render(cls):
        assert cls is not None
        return list(cls().sections({}, object()))[0].title

    title_1 = render_with_override(first["run_dir"], first["record"], render=render)
    title_2 = render_with_override(second["run_dir"], second["record"], render=render)
    assert title_1 == "FIRST-PROJECT"
    assert title_2 == "SECOND-PROJECT"


def test_fixture_v_m11_render_happens_inside_the_sys_path_window(tmp_path: Path):
    """**M11**: perform the render after `sys.path` is restored. The
    override lazily imports a TOP-LEVEL sibling module that sits directly
    in `src/` (not inside the package, so it has no `__path__` of its own
    to fall back on) and uses it to read a real condition artifact — a
    constant-string override could not tell the difference, since the
    override MODULE itself is imported either way. This one can: the
    lazy import only resolves while `<repo_root>/src` is still on
    `sys.path`.
    """
    built = _build_and_run_for_report_io(tmp_path / "proj", 1)
    # Recover the repo root the same way discovery itself does — from the
    # run's own `environment/repo_root.txt`, not from any path arithmetic.
    repo_root = Path(
        (built["run_dir"] / "environment" / "repo_root.txt").read_text(encoding="utf-8").strip()
    )
    pkg = "cohort_pilot"
    (repo_root / "src" / "report_helper.py").write_text(
        "def read_it(io):\n    return io.read_condition(0, 'step02_fit', 'model.json')\n"
    )
    _write_report(
        repo_root,
        pkg,
        "from publishable import BaseReport\n\n\n"
        "class Report(BaseReport):\n"
        "    format = 'markdown'\n\n"
        "    def sections(self, run, io):\n"
        "        from report_helper import read_it  # lazy — a top-level sibling in src/\n"
        "        yield self.section('Fixture V', body=read_it(io))\n",
    )

    def render(cls):
        assert cls is not None
        io = _report_io_from_record(built)
        return list(cls().sections(built["record"], io))[0].body

    result = render_with_override(built["run_dir"], built["record"], render=render)
    assert result == {"m": "pearson"}


def test_sys_path_is_restored_after_a_successful_render(tmp_path: Path):
    """Major 1 (whole-branch review): restoration was previously pinned by
    nothing — replacing the `finally` body with `pass` left the full suite
    green. `sys.path` must come back to exactly what it was, on the
    ordinary success path.
    """
    built = _build_project(tmp_path / "proj", tmp_path / "data", tmp_path / "results")
    before = list(sys.path)
    result = render_with_override(built["run_dir"], built["record"], render=lambda cls: cls)
    assert result is None  # no override written; the ordinary case
    assert sys.path == before


def test_sys_path_is_restored_after_render_raises(tmp_path: Path):
    """The other half of Major 1: restoration on the REFUSAL/exception
    path, not only the success path. `render` itself raising must not
    leave `<repo_root>/src` on `sys.path` — the `finally` covers both.
    """
    built = _build_project(tmp_path / "proj", tmp_path / "data", tmp_path / "results")
    before = list(sys.path)

    def render(cls):
        raise RuntimeError("boom, deliberately, inside render")

    with pytest.raises(RuntimeError, match="boom, deliberately"):
        render_with_override(built["run_dir"], built["record"], render=render)
    assert sys.path == before


def test_sys_path_entry_is_removed_by_identity_not_by_position(tmp_path: Path):
    """Major 1's core finding: `sys.path.pop(0)` answers "which entry did
    I insert" with a POSITION rather than with the fact. `sections()` runs
    inside this window by design, and an override reaching for a vendored
    directory via `sys.path.insert(0, ...)` — an ordinary Python idiom —
    pushes THIS function's own entry to index 1. A positional pop would
    then remove the override's freshly-inserted entry instead and leak
    `<repo_root>/src` on `sys.path` permanently — Decision 3's own "render
    one experiment's figures for another's run", reached by a route other
    than a directory scan. Removing by the exact path STRING, wherever it
    sits, is what this pins.
    """
    built = _build_project(tmp_path / "proj", tmp_path / "data", tmp_path / "results")
    vendored = tmp_path / "vendored"
    vendored.mkdir()
    _write_report(
        built["root"],
        built["pkg"],
        "import sys\n"
        "from publishable import BaseReport\n\n\n"
        "class Report(BaseReport):\n"
        "    format = 'markdown'\n\n"
        "    def sections(self, run, io):\n"
        f"        sys.path.insert(0, {str(vendored)!r})\n"
        "        yield self.section('X', body='x')\n",
    )
    src_entry = str(built["root"] / "src")
    before = [p for p in sys.path if p != str(vendored)]

    def render(cls):
        assert cls is not None
        return list(cls().sections({}, object()))

    try:
        render_with_override(built["run_dir"], built["record"], render=render)
        assert src_entry not in sys.path
    finally:
        # The override's own leak, not this function's — clean it up so
        # this test doesn't pollute any test that runs after it.
        if str(vendored) in sys.path:
            sys.path.remove(str(vendored))
    assert sys.path == before


# ---------------------------------------------------------------------------
# H8c task 4 — `report_form`, deciding a run from a bundle by the argument's
# file NAME alone (docs/superpowers/specs/2026-08-21-report-study-design.md
# Decision 1), and `lineage.read_record_file`, which `report` reads a bundle
# member through (tests for `read_record_file` itself live in
# tests/test_lineage.py — these pin only that `report_form` and a real
# `run.yaml` compose the way `report` will need).
# ---------------------------------------------------------------------------


def test_report_form_run_yaml_is_a_run(tmp_path: Path):
    assert report_form(tmp_path / "run.yaml") == "run"


def test_report_form_study_yaml_is_a_bundle(tmp_path: Path):
    assert report_form(tmp_path / "study.yaml") == "bundle"


def test_report_form_any_other_name_is_e_report_form(tmp_path: Path):
    with pytest.raises(ContractError) as e:
        report_form(tmp_path / "sensitivity.run.yaml")
    assert e.value.code == "E-REPORT-FORM"


def test_report_form_run_yaml_shaped_but_nested_is_still_a_run(tmp_path: Path):
    """The rule is the file's own NAME, not its position — a `run.yaml`
    three directories deep is still a run, the same way `study add`'s
    bundle members sit under a `runs/` directory of their own."""
    nested = tmp_path / "a" / "b" / "run.yaml"
    assert report_form(nested) == "run"


def test_report_form_refuses_a_directory_even_though_diff_accepts_one(tmp_path: Path):
    """Decision 1: `report`'s two forms are two file names, and a directory
    admits neither — unlike `diff._form`, which treats a directory as a run
    record because that operand family has a run DIRECTORY as one of its two
    shapes. Reusing `diff._form` here would be exactly the proxy substitution
    Decision 1's own grounds forbid, so this is asserted directly against
    `report_form` rather than by importing `diff._form` and finding it
    disagrees."""
    directory = tmp_path / "some_run_dir"
    directory.mkdir()
    with pytest.raises(ContractError) as e:
        report_form(directory)
    assert e.value.code == "E-REPORT-FORM"


def test_report_form_a_directory_named_run_yaml_is_still_refused(tmp_path: Path):
    """The one arm that separates "decide by name" from "decide by
    `is_dir()`": a directory literally named `run.yaml` reads as a run under
    `is_dir()` (which would return the wrong-for-Decision-1 answer, "run
    record", since it never reaches the name check at all) and is refused
    under the name rule, since `path.is_dir()` is checked FIRST and wins
    regardless of the name. This is the arm that would pass under a
    by-`is_dir()` mutant alongside `test_report_form_refuses_a_directory_
    even_though_diff_accepts_one` above (which alone would pass under a
    wrong-direction mutant too) — together they rule out both readings a
    mutant swap could produce.
    """
    directory = tmp_path / "run.yaml"
    directory.mkdir()
    with pytest.raises(ContractError) as e:
        report_form(directory)
    assert e.value.code == "E-REPORT-FORM"


def test_report_form_does_not_touch_a_missing_path(tmp_path: Path):
    """A path that does not exist at all is decided from its name alone,
    exactly like one that does — `report_form` performs no existence
    check, and a missing operand is left for whatever reads the file next
    (`E-IO-FAILED` through `main`'s `OSError` handler, once `report` is
    wired in task 8) rather than caught here."""
    missing = tmp_path / "run.yaml"
    assert not missing.exists()
    assert report_form(missing) == "run"


def test_report_and_diff_would_read_the_same_run_directory_from_a_run_yaml_path(
    tmp_path: Path,
):
    """`_record_dir`'s RULE is reused in substance, not by import: a
    `run.yaml` path's run directory is its own parent. Exercised end to end
    over a real run rather than asserted as a one-liner, so a future change
    to where `run.yaml` sits would fail this rather than a restatement of
    the same line."""
    doc = _build_project(tmp_path / "proj", tmp_path / "data", tmp_path / "results")
    run_yaml_path = doc["run_dir"] / "run.yaml"
    assert report_form(run_yaml_path) == "run"
    assert run_yaml_path.parent == doc["run_dir"]
    record = read_record_file(run_yaml_path)
    assert record["run_id"] == doc["record"]["run_id"]


# ---------------------------------------------------------------------------
# H8c task 5 — Conditions and Deltas, over Fixtures R and D
# (docs/superpowers/plans/2026-08-21-report-study.md task 5;
# docs/superpowers/specs/2026-08-21-report-study-design.md Decision 5).
# Both fixtures are driven through a genuine `main(["run", ...])` — a
# starter step recording a numeric "score" column and calling `io.skip` on
# a subset, `statistics.report_by: [cohort]`, one confirmatory hypothesis,
# and a `summary` step returning two `Estimate`s, one with `n: null` and one
# with `n: 40` — so every field a section renders is read back from a record
# core actually wrote, not asserted as a literal.
# ---------------------------------------------------------------------------

_SCORE_STEP = """\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        shift = {{"pearson": 0.0, "spearman": 1.0}}.get(cfg.parameters.analysis.method, 0.0)
        units = list(io.units)
        for i, unit in enumerate(units):
            if i % 8 == 0:
                io.skip(unit.key, "deliberately ineligible")
                continue
            extra = 0.5 if i % 2 == 0 else -0.5
            io.record(unit.key, {{"score": float(i) + shift + extra}})
        return {{}}
"""

_TWO_ESTIMATE_SUMMARY_STEP = """\
# generated, and runnable as-is
from publishable import BaseStep, Estimate


class Step(BaseStep):
    scope = "summary"

    def run(self, cfg, io):
        return {{
            "adjusted": Estimate(value=0.031, ci95=[0.008, 0.055], n=None,
                                  method="mixed model, REML"),
            "power": Estimate(value=0.82, ci95=[0.75, 0.88], n=40,
                               method="simulation"),
        }}
"""


_SHARED_CHECK_STEP = """\
from publishable import BaseStep


class Step(BaseStep):
    scope = "run"

    def run(self, cfg, io):
        return {}
"""

_CONDITION_CHECK_STEP = """\
from publishable import BaseStep


class Step(BaseStep):
    scope = "condition"

    def run(self, cfg, io):
        return {}
"""


def _fixture_r_or_d(
    tmp_path: Path, *, declare_contrast: bool, capsys: pytest.CaptureFixture[str]
) -> dict[str, Any]:
    """Fixture R (`declare_contrast=False`) and Fixture D (`True`, R plus one
    declared `statistics.contrasts` entry — task 5's own seam: without it,
    Decision 5's "read both `vs_baseline` and `results.contrasts`" ships
    unpinned, since R's every delta is already in `vs_baseline`).

    Built directly (not through `run_a_project`'s `extra_steps`, which
    generates every extra step from the SAME `extra_step_source`) because
    Major 2 (task-b4 review) found `_execution_rows`' `shared` walk and its
    condition-scoped discriminator exercised by NOTHING: this fixture's
    `execution.shared` was `{}` and its only `conditions[].steps` entry was
    repeat-label-keyed. Fixture R now carries all THREE nesting shapes a
    real `execution` block can hold — a `run`-scoped step (`shared_check`,
    lands in `execution.shared`), a `condition`-scoped step (`cond_check`,
    lands in `execution.conditions[].steps` with a direct `status`, no
    repeat label), the original `repeat`-scoped starter step, and the
    `summary`-scoped step — generated one at a time so each can carry its
    own scope.
    """
    import publishable.generators.experiment as experiment_gen
    from publishable.cli import main
    from publishable.generators.experiment import generate_experiment
    from publishable.generators.step import generate_step

    root = tmp_path / "proj"
    data = tmp_path / "data"
    results = tmp_path / "results"
    data.mkdir(parents=True)
    units = 24
    rows = "\n".join(f"p{i},{'ab'[i % 2]},{'xy'[(i // 2) % 2]}" for i in range(1, units + 1))
    (data / "index.csv").write_text(f"patient_id,cohort,arm\n{rows}\n")
    assert main(["new", str(root)]) == 0
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(experiment_gen, "STARTER_STEP", _SCORE_STEP)
        cfg = generate_experiment(
            repo_root=root,
            name="cohort-pilot",
            template_name="generic",
            input_dir=str(data),
            output_dir=str(results),
        )
    generate_step(repo_root=root, experiment="cohort-pilot", step_name="shared_check").write_text(
        _SHARED_CHECK_STEP
    )
    generate_step(repo_root=root, experiment="cohort-pilot", step_name="cond_check").write_text(
        _CONDITION_CHECK_STEP
    )
    generate_step(repo_root=root, experiment="cohort-pilot", step_name="summarize").write_text(
        _TWO_ESTIMATE_SUMMARY_STEP.format()
    )

    doc = yaml.safe_load(cfg.read_text())
    doc["metadata"]["description"] = "H8c batch 4 fix round 1 — Fixture R, all three nesting shapes"
    doc["metadata"]["authors"] = ["Kyungjoon Lee"]
    doc["replication"] = {"repeats": [{"kind": "seed", "n": 3}]}
    doc["sweep"] = {
        "baseline": {"analysis.method": "pearson"},
        "grid": {"analysis.method": ["spearman"]},
    }
    doc["data"]["units"]["attributes"] = ["cohort"]
    statistics: dict[str, Any] = {"report_by": ["cohort"]}
    if declare_contrast:
        # TWO declared contrasts, not one (m3, task-b4 review: a fixture
        # with exactly one element cannot tell a loop from a first-element
        # read — `[:1]` on the `results.contrasts` walk stays green against
        # a single-entry list). Both name the same comparison on purpose
        # (H4b-1's own precedent for "declared twice, counted twice"), with
        # distinct `id`s so each is independently findable in the rendered
        # rows.
        statistics["contrasts"] = [
            {"id": "spearman_vs_baseline", "of": "method=spearman", "against": "baseline"},
            {"id": "spearman_vs_baseline_2", "of": "method=spearman", "against": "baseline"},
        ]
    doc["statistics"] = statistics
    doc["hypotheses"] = [
        {
            "id": "h1",
            "kind": "confirmatory",
            "statement": "spearman's score exceeds pearson's",
            "metric": "step01_summarize_units.score",
            "compare": {"condition": "method=spearman", "to": "baseline"},
            "direction": "greater",
            "threshold": 0.0,
            "evaluate_on": "observed",
        }
    ]
    cfg.write_text(yaml.safe_dump(doc))
    for args in (
        ["add", "."],
        [
            "-c",
            "user.email=t@e.com",
            "-c",
            "user.name=t",
            "commit",
            "-qm",
            "fixture r, all three nesting shapes",
        ],
    ):
        subprocess.run(["git", *args], cwd=root, check=True)
    assert main(["run", str(cfg)]) == 0
    run_dir = next(results.glob("run_*"))
    run = yaml.safe_load((run_dir / "run.yaml").read_text())
    return {"root": root, "run_dir": run_dir, "run": run}


@pytest.fixture
def fixture_r(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> dict[str, Any]:
    return _fixture_r_or_d(tmp_path, declare_contrast=False, capsys=capsys)


@pytest.fixture
def fixture_d(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> dict[str, Any]:
    return _fixture_r_or_d(tmp_path, declare_contrast=True, capsys=capsys)


def test_fixture_r_is_shaped_the_way_this_task_needs(fixture_r: dict[str, Any]):
    """A fixture is a claim too: pin the shape task 5's sections depend on
    before trusting any section built over it — two conditions, a `score`
    metric, a `by.cohort` stratum, a `vs_baseline` block on the non-baseline
    condition and none on the baseline, and no top-level `results.contrasts`
    (R declares no contrast; that is what Fixture D adds)."""
    run = fixture_r["run"]
    conditions = run["results"]["conditions"]
    assert len(conditions) == 2
    baseline = next(c for c in conditions if c["is_baseline"])
    other = next(c for c in conditions if not c["is_baseline"])
    assert "vs_baseline" not in baseline
    assert "vs_baseline" in other
    assert "score" in baseline["aggregated"]["step01_summarize_units"]
    assert "by" in baseline["aggregated"]["step01_summarize_units"]
    assert "cohort" in baseline["aggregated"]["step01_summarize_units"]["by"]
    assert "results" in run and "contrasts" not in run["results"]
    assert run["results"]["hypotheses"][0]["id"] == "h1"


def test_fixture_d_declares_two_contrasts_beside_r_s_own_shape(fixture_d: dict[str, Any]):
    run = fixture_d["run"]
    assert len(run["results"]["contrasts"]) == 2
    assert {c["id"] for c in run["results"]["contrasts"]} == {
        "spearman_vs_baseline",
        "spearman_vs_baseline_2",
    }


# --- Conditions ---------------------------------------------------------


def test_conditions_section_title(fixture_r: dict[str, Any]):
    section = conditions_section(fixture_r["run"])
    assert section.title == "Conditions"


def test_conditions_section_carries_identity_for_every_condition(fixture_r: dict[str, Any]):
    run = fixture_r["run"]
    section = conditions_section(run)
    rows = section.body["rows"]
    seen = {(r["condition_index"], r["condition_label"], r["is_baseline"]) for r in rows}
    expected = {(c["index"], c["label"], c["is_baseline"]) for c in run["results"]["conditions"]}
    assert seen == expected
    for row in rows:
        condition = next(
            c for c in run["results"]["conditions"] if c["index"] == row["condition_index"]
        )
        assert row["values"] == condition["values"]


def test_conditions_section_metric_names_exclude_by_and_match_the_record_exactly(
    fixture_r: dict[str, Any],
):
    """M13's discriminating assertion: the rendered metric set is EXACTLY
    the record's real metric names — `by` excluded not because the STRING
    `"by"` is filtered out, but because Fixture R's `by` key structurally
    IS the `report_by` strata block (attribute -> level -> metric), which
    `_is_strata_block` recognizes on shape, never on name (Major 3, task-b4
    review: excluding by the literal name is the same proxy substitution
    as a module-name prefix, a class marker, or `pop(0)`). Fixture R
    declares `report_by: [cohort]`, so `aggregated[step01_summarize_
    units]` genuinely holds that stratum block beside `score` — the arm
    this fixture exists to give the structural test something to bite on.
    The sibling case — a recorded COLUMN literally named `by`, which must
    render rather than vanish — is
    `test_a_recorded_column_named_by_renders_as_a_real_metric_row` below.
    """
    run = fixture_r["run"]
    rows = section_rows_for_step(run, "step01_summarize_units")
    metrics = {r["metric"] for r in rows if r["by_attribute"] is None}
    assert metrics == {"score"}
    assert "by" not in metrics


def section_rows_for_step(run: dict[str, Any], step: str) -> list[dict[str, Any]]:
    return [r for r in conditions_section(run).body["rows"] if r["step"] == step]


_RECORDS_A_BY_COLUMN_STEP = """\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        for i, unit in enumerate(io.units):
            io.record(unit.key, {{"pred": float(i), "by": float(i) * 2.0}})
        return {{"n_units": len(io.units)}}
"""


def test_a_recorded_column_named_by_renders_as_a_real_metric_row(tmp_path, capsys):
    """Major 3, task-b4 review: Decision 5's own grounds for excluding
    `by` — "the record `report` reads can never hold a metric called
    `by`" — are false against the code. `cli.py`'s `W-STATS-STRATUM-
    SHADOWED` says in writing that a recorded column of that name "keeps
    its value" and that no strata are written for that step, whether or
    not `report_by` was declared — verified here over a REAL run, over
    `docs/superpowers/spec-defects.md`'s own "New reserved metric name:
    `by`" ruling ("the column wins"). The Conditions section must agree
    with the write side: a column named `by` renders as a real metric,
    with its own `value`/`ci95`/`basis`, never dropped.
    """
    import publishable.generators.experiment as experiment_gen

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(experiment_gen, "STARTER_STEP", _RECORDS_A_BY_COLUMN_STEP)
        doc = run_a_project(
            tmp_path,
            capsys=capsys,
            units=40,
            unit_attributes=["cohort"],
            statistics={"report_by": ["cohort"]},
        )
    assert "W-STATS-STRATUM-SHADOWED" in doc["stdout"]
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    real_entry = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]["by"]
    assert real_entry["basis"] == "units"
    assert "value" in real_entry
    rows = section_rows_for_step(run, "step01_summarize_units")
    by_rows = [r for r in rows if r["metric"] == "by" and r["by_attribute"] is None]
    assert by_rows, "the recorded `by` column never reached the Conditions section"
    row = by_rows[0]
    assert row["value"] == real_entry["value"]
    assert row["basis"] == real_entry["basis"]
    assert row["ci95"] == real_entry["ci95"]
    # And no phantom stratum rows were produced from misreading the same
    # key: `report_by: [cohort]` was declared, but `cli.py` writes no
    # strata block for THIS step because the column shadows it, so there
    # must be no `by_attribute == "cohort"` row for step01 at all.
    assert not [r for r in rows if r["by_attribute"] == "cohort"]


def test_conditions_section_top_level_metric_carries_the_named_fields(fixture_r: dict[str, Any]):
    run = fixture_r["run"]
    baseline = next(c for c in run["results"]["conditions"] if c["is_baseline"])
    real_entry = baseline["aggregated"]["step01_summarize_units"]["score"]
    row = next(
        r
        for r in section_rows_for_step(run, "step01_summarize_units")
        if r["condition_index"] == baseline["index"] and r["by_attribute"] is None
    )
    for field in ("value", "ci95", "method", "n", "basis", "correction", "repeat_spread"):
        assert field in real_entry, f"fixture no longer carries {field!r} — re-derive the fixture"
        assert row[field] == real_entry[field]


def test_conditions_by_stratum_carries_no_repeat_spread_and_the_renderer_does_not_require_one(
    fixture_r: dict[str, Any],
):
    """Measured: a `by` stratum entry carries NO `repeat_spread` at all —
    the renderer must not require one, so this reads a real stratum entry
    and asserts the row simply omits the key rather than setting it to
    `None`."""
    run = fixture_r["run"]
    baseline = next(c for c in run["results"]["conditions"] if c["is_baseline"])
    by = baseline["aggregated"]["step01_summarize_units"]["by"]
    attribute, levels = next(iter(by.items()))
    level, level_metrics = next(iter(levels.items()))
    real_entry = level_metrics["score"]
    assert "repeat_spread" not in real_entry
    row = next(
        r
        for r in section_rows_for_step(run, "step01_summarize_units")
        if r["by_attribute"] == attribute and r["by_level"] == level
    )
    assert "repeat_spread" not in row
    for field in ("value", "ci95", "method", "n", "basis", "correction"):
        assert row[field] == real_entry[field]


# --- Deltas --------------------------------------------------------------


def test_deltas_section_title(fixture_r: dict[str, Any]):
    assert deltas_section(fixture_r["run"]).title == "Deltas"


def test_deltas_section_reads_vs_baseline(fixture_r: dict[str, Any]):
    run = fixture_r["run"]
    other = next(c for c in run["results"]["conditions"] if not c["is_baseline"])
    real_entry = other["vs_baseline"]["step01_summarize_units"]["score"]
    rows = deltas_section(run).body["rows"]
    row = next(r for r in rows if r["comparison"] is None and r["step"] == "step01_summarize_units")
    for field in (
        "delta",
        "method",
        "paired",
        "ci95",
        "ci95_corrected",
        "correction",
        "correction_level",
    ):
        assert row[field] == real_entry[field]
    # `n_paired` is ABSENT rather than `null` when the entry itself omits it
    # — key presence decides what prints, never a `None` test.
    assert ("n_paired" in row) == ("n_paired" in real_entry)


def test_deltas_section_reads_results_contrasts_too(fixture_d: dict[str, Any]):
    """Decision 5's own correction: § The two files' `run.yaml` example
    shows only `vs_baseline`, and reading only it is the bug. Fixture D
    declares TWO `statistics.contrasts` entries (m3, task-b4 review: one
    entry cannot distinguish a loop from a first-element read), and this
    asserts BOTH reach the rendered rows by their own declared `id` — the
    seam M4 exists to cut."""
    run = fixture_d["run"]
    contrasts_by_id = {c["id"]: c for c in run["results"]["contrasts"]}
    assert set(contrasts_by_id) == {"spearman_vs_baseline", "spearman_vs_baseline_2"}
    rows = deltas_section(run).body["rows"]
    for comparison_id, contrast in contrasts_by_id.items():
        declared_rows = [r for r in rows if r["comparison"] == comparison_id]
        assert declared_rows, f"{comparison_id!r} never reached the Deltas section"
        real_entry = contrast["step01_summarize_units"]["score"]
        row = next(r for r in declared_rows if r["step"] == "step01_summarize_units")
        assert row["of"] == contrast["of"]
        assert row["against"] == contrast["against"]
        assert row["delta"] == real_entry["delta"]


def test_deltas_section_family_is_read_as_a_mapping_and_travels_with_each_row(
    fixture_r: dict[str, Any],
):
    run = fixture_r["run"]
    rows = deltas_section(run).body["rows"]
    row = next(r for r in rows if r["step"] == "step01_summarize_units")
    other = next(c for c in run["results"]["conditions"] if not c["is_baseline"])
    real_entry = other["vs_baseline"]["step01_summarize_units"]["score"]
    assert "family_size" in real_entry and "family" in real_entry
    assert row["family_size"] == real_entry["family_size"]
    assert row["family"] == real_entry["family"]
    assert isinstance(row["family"], dict)


def test_hypothesis_family_shape_differs_and_is_not_hardcoded_by_this_module(
    fixture_r: dict[str, Any],
):
    """§ Corrections correction 9: a hypothesis family's `family` is
    `{hypotheses: N}`, a different shape from a comparison family's
    `{comparisons, metrics}`. This module reads `family` generically
    (never by two literal keys) — pinned here against the record's OWN
    hypothesis family, which task 6's Hypothesis-verdicts section reads
    through the identical `_present_fields` helper.
    """
    run = fixture_r["run"]
    verdict = run["results"]["hypotheses"][0]
    assert "family" in verdict
    assert set(verdict["family"]) == {"hypotheses"}


# --- Mutations (run, then reverted; see task-b4 report for text/outcome) ---
# M4, M13, the repeat_spread mutation, and M14's render-level arm are
# exercised by hand against this module and reverted — see the task report
# for each one's exact text and PASS/FAIL outcome. The tests above are what
# each one is caught by.


def test_m14_an_override_mutating_a_standard_sections_mapping_body_in_place_reaches_the_page(
    fixture_r: dict[str, Any],
):
    """The carry from task 1: Decision 2 says an override "cannot obtain a
    figure core did not already compute" — it says nothing about a mapping
    `body`'s contents being protected from in-place mutation, and `Section`
    being frozen (task 1) guarantees only that `title`/`body` cannot be
    REBOUND. This is the render-level arm task 1 could not write because no
    standard section with a mapping body existed yet: reach into the
    Conditions section's `body["rows"]` and mutate a value in place, then
    confirm the mutated figure is what a reader ultimately sees — the
    RENDERED TEXT, through both renderers, never the row dict a mutation
    was just written into (M1, task-b4 review: a test named "reaches the
    page" has to read the page, not the dict a mutation and its own
    assertion share).
    """
    run = fixture_r["run"]

    class MutatingReport(BaseReport):
        def sections(self, run, io):
            for section in super().sections(run, io):
                if section.title == "Conditions":
                    section.body["rows"][0]["value"] = "MUTATED-BY-OVERRIDE"
                yield section

    # The control: render the SAME sections with no mutation applied, and
    # confirm the real, unmutated figure is what appears — so the next
    # assertion (the mutated text appearing instead) is known to mean
    # something, rather than "MUTATED-BY-OVERRIDE" merely being present
    # somewhere incidental.
    plain_markdown = render_markdown(BaseReport().sections(run, io=object()))
    assert "MUTATED-BY-OVERRIDE" not in plain_markdown

    markdown = render_markdown(MutatingReport().sections(run, io=object()))
    assert "MUTATED-BY-OVERRIDE" in markdown
    html = render_html(MutatingReport().sections(run, io=object()))
    assert "MUTATED-BY-OVERRIDE" in html

    # The frozen guarantee itself still holds: the override cannot rebind
    # `body` to a different mapping entirely, only mutate the one object
    # core handed it.
    sections = list(MutatingReport().sections(run, io=object()))
    conditions = next(s for s in sections if s.title == "Conditions")
    with pytest.raises(dataclasses.FrozenInstanceError):
        conditions.body = {"rows": []}  # type: ignore[misc]


# ---------------------------------------------------------------------------
# H8c task 6 — Hypothesis verdicts and Attrition, over Fixture R
# (docs/superpowers/plans/2026-08-21-report-study.md task 6;
# docs/superpowers/specs/2026-08-21-report-study-design.md Decision 5).
# ---------------------------------------------------------------------------


def test_hypotheses_section_title(fixture_r: dict[str, Any]):
    assert hypotheses_section(fixture_r["run"]).title == "Hypothesis verdicts"


def test_hypotheses_section_carries_the_named_fields_and_the_family(fixture_r: dict[str, Any]):
    run = fixture_r["run"]
    real = run["results"]["hypotheses"][0]
    row = hypotheses_section(run).body["rows"][0]
    for field in (
        "id",
        "kind",
        "declared_in",
        "observed",
        "verdict_evaluated_on",
        "supported",
        "verdict_rests_on",
    ):
        assert row[field] == real[field]
    assert "family_size" in real and "family" in real
    assert row["family_size"] == real["family_size"]
    assert row["family"] == real["family"]
    assert set(row["family"]) == {"hypotheses"}


def test_hypotheses_section_omits_family_when_the_record_does(fixture_r: dict[str, Any]):
    """The `reported`-verdict shape (H8c doesn't build one over this
    fixture, but the section must not assume `family`/`family_size` are
    always present): a verdict dict missing both keys must not gain them.
    """
    verdict = {
        "id": "h9",
        "kind": "confirmatory",
        "declared_in": "parameters_hash deadbeef",
        "observed": None,
        "verdict_evaluated_on": "observed",
        "supported": None,
        "verdict_rests_on": "reported",
    }
    run = {"results": {"hypotheses": [verdict]}}
    row = hypotheses_section(run).body["rows"][0]
    assert "family_size" not in row
    assert "family" not in row


# --- Attrition -------------------------------------------------------------


def test_attrition_section_title(fixture_r: dict[str, Any]):
    assert attrition_section(fixture_r["run"]).title == "Attrition"


def test_attrition_section_carries_top_level_status_and_provenance_units(
    fixture_r: dict[str, Any],
):
    run = fixture_r["run"]
    rows = attrition_section(run).body["rows"]
    status_row = next(r for r in rows if r["kind"] == "status")
    assert status_row["status"] == run["status"]
    units_row = next(r for r in rows if r["kind"] == "provenance_units")
    assert units_row["n"] == run["provenance"]["units"]["n"]
    assert units_row["key"] == run["provenance"]["units"]["key"]


def test_attrition_section_input_manifest_changed_is_rendered_as_the_list_it_is(
    fixture_r: dict[str, Any],
):
    """Measured: `provenance.input_manifest_changed` is a LIST, not a
    boolean. This asserts the row's value is that list, unconverted — the
    discriminator against the boolean-coercion mutation, since `bool([])`
    is `False` and a row holding `False` would be indistinguishable from a
    genuinely boolean field elsewhere in the section."""
    run = fixture_r["run"]
    real = run["provenance"]["input_manifest_changed"]
    assert isinstance(real, list)
    rows = attrition_section(run).body["rows"]
    row = next(r for r in rows if r["kind"] == "input_manifest_changed")
    assert row["value"] == real
    assert isinstance(row["value"], list)
    assert row["value"] is not False


def test_attrition_section_carries_each_metrics_own_n(fixture_r: dict[str, Any]):
    """Checked against BOTH conditions (m3, task-b4 review: `_metric_n_
    rows`' condition loop is asserted on only its first element otherwise,
    which cannot tell a loop from a single read even though Fixture R has
    two conditions)."""
    run = fixture_r["run"]
    rows = attrition_section(run).body["rows"]
    for condition in run["results"]["conditions"]:
        real_n = condition["aggregated"]["step01_summarize_units"]["score"]["n"]
        row = next(
            r
            for r in rows
            if r["kind"] == "metric_n"
            and r["condition_index"] == condition["index"]
            and r["step"] == "step01_summarize_units"
            and r["metric"] == "score"
            and r["by_attribute"] is None
        )
        assert row["n"] == real_n


def test_attrition_section_walks_shared_conditions_and_summary(fixture_r: dict[str, Any]):
    """The mutation this pins against: walking only `execution.conditions`
    and skipping `shared`/`summary`. Major 2 (task-b4 review): Fixture R
    now carries all THREE nesting shapes for real — a `run`-scoped step
    (`step02_shared_check`, lands in `execution.shared`), a
    `condition`-scoped step (`step03_cond_check`, direct `status` under
    `conditions[].steps`, no repeat label) and the `repeat`-scoped starter
    step, plus the `summary`-scoped step — so each of the four asserted
    scopes below has a REAL row to fail its own absence on, not merely a
    name in the test's docstring.
    """
    run = fixture_r["run"]
    rows = attrition_section(run).body["rows"]
    execution_rows = [r for r in rows if r["kind"] == "execution"]
    scopes = {r["scope"] for r in execution_rows}
    assert scopes == {"shared", "condition", "repeat", "summary"}

    shared_row = next(r for r in execution_rows if r["scope"] == "shared")
    assert shared_row["step"] == "step02_shared_check"
    assert shared_row["status"] == run["execution"]["shared"]["step02_shared_check"]["status"]

    condition_rows = [r for r in execution_rows if r["scope"] == "condition"]
    assert {r["condition_index"] for r in condition_rows} == {
        c["index"] for c in run["results"]["conditions"]
    }
    for row in condition_rows:
        assert row["step"] == "step03_cond_check"
        assert "status" in row and "repeat" not in row

    summary_row = next(r for r in execution_rows if r["scope"] == "summary")
    assert summary_row["step"] == "step04_summarize"
    assert summary_row["status"] == run["execution"]["summary"]["step04_summarize"]["status"]

    # And the repeat-scoped starter step's execution is walked too, nested
    # correctly under `conditions[]`, for BOTH conditions (m3, task-b4
    # review: a loop asserted on only its first element is not asserted on
    # at all).
    repeat_rows = [r for r in execution_rows if r["scope"] == "repeat"]
    assert repeat_rows, "no repeat-scoped execution reached the Attrition section"
    assert {r["condition_index"] for r in repeat_rows} == {
        c["index"] for c in run["results"]["conditions"]
    }
    for row in repeat_rows:
        assert row["step"] == "step01_summarize_units"
        assert "repeat" in row and row["repeat"]
        assert "status" in row


def test_attrition_section_does_not_mention_nondeterministic(fixture_r: dict[str, Any]):
    """The filing, pinned rather than merely stated: `nondeterministic`
    appears nowhere in a real run's `execution` block, and this section
    does not manufacture it. If a future build starts writing it, this
    test's own premise (`assert "nondeterministic" not in text.dumps of
    execution`) breaks first and points back at the filing rather than at
    a silent default sneaking into the render.
    """
    run = fixture_r["run"]
    assert "nondeterministic" not in yaml.safe_dump(run["execution"])
    rows = attrition_section(run).body["rows"]
    for row in rows:
        assert "nondeterministic" not in row


# ---------------------------------------------------------------------------
# H8c task 7 — two renderers over one section stream, `E-REPORT-FORMAT`, and
# the section order pinned from a real render
# (docs/superpowers/plans/2026-08-21-report-study.md task 7;
# docs/superpowers/specs/2026-08-21-report-study-design.md Decision 16).
# ---------------------------------------------------------------------------


def test_render_markdown_emits_a_heading_and_a_pipe_table():
    section = Section(title="Conditions", body={"rows": [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]})
    text = render_markdown(iter([section]))
    assert "## Conditions" in text
    assert "| a | b |" in text
    assert "| 1 | x |" in text
    assert "| 2 | y |" in text


def test_render_markdown_emits_a_block_for_a_str_body():
    section = Section(title="Figure", body="some *markdown* text")
    text = render_markdown(iter([section]))
    assert "## Figure" in text
    assert "some *markdown* text" in text


def test_render_html_emits_a_heading_and_a_table():
    section = Section(title="Conditions", body={"rows": [{"a": 1, "b": "x"}]})
    text = render_html(iter([section]))
    assert "<h2>Conditions</h2>" in text
    assert "<table>" in text
    assert "<td>1</td>" in text
    assert "<td>x</td>" in text


def test_render_html_escapes_a_title_and_a_cell():
    section = Section(title="<script>", body={"rows": [{"value": "<b>x</b>"}]})
    text = render_html(iter([section]))
    assert "<script>" not in text
    assert "&lt;script&gt;" in text
    assert "<b>x</b>" not in text
    assert "&lt;b&gt;x&lt;/b&gt;" in text


def test_render_html_is_self_contained_and_the_assertion_can_actually_fail():
    """Decision 16: HTML is self-contained and offline — no external
    stylesheet, script or font. The assertion is built so it CAN fail: a
    body deliberately carrying `http://` text is checked first, to prove
    the substring search actually looks (CLAUDE.md's "prove each sweep can
    fail by running it against a string known to be present")."""
    section = Section(title="Conditions", body={"rows": [{"a": "http://example.com/not-a-link"}]})
    text = render_html(iter([section]))
    # The control: this text IS present (a plain data value containing a
    # URL-shaped string), which the next assertion's kind of check WOULD
    # catch if it looked for the wrong thing.
    assert "http://example.com/not-a-link" in text
    # The real assertion: no actual external reference tag exists.
    for external in ("<link ", "<script src=", '<img src="http', "@import", "fonts.googleapis"):
        assert external not in text


def test_render_report_with_a_real_override_dispatches_by_its_declared_format(
    tmp_path: Path,
):
    built = _build_project(tmp_path / "proj", tmp_path / "data", tmp_path / "results")
    _write_report(
        built["root"],
        built["pkg"],
        "from publishable import BaseReport\n\n\nclass Report(BaseReport):\n    format = 'html'\n",
    )
    text = render_with_override(
        built["run_dir"],
        built["record"],
        render=lambda cls: render_report(cls, built["record"], io=object()),
    )
    assert text.startswith("<!doctype html>")
    assert "<h2>Conditions</h2>" in text


def test_render_report_with_no_override_renders_markdown_with_no_diagnostic(
    tmp_path: Path,
):
    """Fixture O's positive control: no `report.py` at all renders the
    four standard sections and prints no diagnostic — `report_cls is None`
    is the ordinary case, not the class-declares-nothing refusal."""
    built = _build_project(tmp_path / "proj", tmp_path / "data", tmp_path / "results")
    text = render_with_override(
        built["run_dir"],
        built["record"],
        render=lambda cls: render_report(cls, built["record"], io=object()),
    )
    for title in ("Conditions", "Deltas", "Hypothesis verdicts", "Attrition"):
        assert f"## {title}" in text


def test_render_report_with_an_override_declaring_no_format_is_e_report_format(
    tmp_path: Path,
):
    """Fixture O's no-`format` arm, and M10's discriminating arm: a REAL
    class exists (this project wrote `report.py`) and genuinely declares
    no `format` — refused rather than defaulted, because a base default
    would make this indistinguishable from a class that meant `markdown`.
    """
    built = _build_project(tmp_path / "proj", tmp_path / "data", tmp_path / "results")
    _write_report(
        built["root"],
        built["pkg"],
        "from publishable import BaseReport\n\n\nclass Report(BaseReport):\n    pass\n",
    )
    with pytest.raises(ContractError) as exc_info:
        render_with_override(
            built["run_dir"],
            built["record"],
            render=lambda cls: render_report(cls, built["record"], io=object()),
        )
    assert exc_info.value.code == "E-REPORT-FORMAT"


def test_render_report_with_an_override_declaring_an_unknown_format_is_e_report_format(
    tmp_path: Path,
):
    built = _build_project(tmp_path / "proj", tmp_path / "data", tmp_path / "results")
    _write_report(
        built["root"],
        built["pkg"],
        "from publishable import BaseReport\n\n\nclass Report(BaseReport):\n    format = 'pdf'\n",
    )
    with pytest.raises(ContractError) as exc_info:
        render_with_override(
            built["run_dir"],
            built["record"],
            render=lambda cls: render_report(cls, built["record"], io=object()),
        )
    assert exc_info.value.code == "E-REPORT-FORMAT"


def test_report_takes_no_format_argument_render_report_has_no_such_parameter():
    """Decision 16, task 7 step 4: an operation command takes paths and
    nothing else, so `report` never takes a format argument — pinned at
    the type this module actually exposes, `render_report`'s own
    signature, rather than as a CLI assertion task 8 owns.
    """
    import inspect as _inspect

    params = _inspect.signature(render_report).parameters
    assert "format" not in params


def test_section_order_is_pinned_from_the_rendered_text_of_fixture_r(fixture_r: dict[str, Any]):
    """Assert the four standard section titles' order in the RENDERED
    TEXT, never by reordering `BaseReport.sections`'s own yields — that
    would be the thing under test iterating itself, the shape a recent
    slice shipped where removing a member moved the expectation and the
    actual together and the second assertion went vacuous under every
    mutation."""
    text = render_report(None, fixture_r["run"], io=object())
    titles = ["Conditions", "Deltas", "Hypothesis verdicts", "Attrition"]
    positions = [text.index(f"## {title}") for title in titles]
    assert positions == sorted(positions)


# --- M10 -----------------------------------------------------------------


def test_m10_a_report_class_genuinely_declaring_no_format_is_refused_not_defaulted(
    tmp_path: Path,
):
    """M10, run directly against `render_report` rather than through the
    override machinery, to isolate the property from discovery: giving
    `BaseReport` a base `format = "markdown"` would make this arm render
    at exit 0 instead of refusing, because the override subclass below
    inherits it and both branches read the identical input — a class that
    declares nothing. See the task report for the mutation's exact text
    and outcome."""

    class NoFormatReport(BaseReport):
        pass

    with pytest.raises(ContractError) as exc_info:
        render_report(NoFormatReport, {"results": {}}, io=object())
    assert exc_info.value.code == "E-REPORT-FORMAT"


# ---------------------------------------------------------------------------
# H8c task 8 — `report <run.yaml>` end to end, through `main`, never
# `command_report` directly (docs/superpowers/plans/2026-08-21-report-
# study.md task 8; design Decisions 1, 6, § Corrections correction 7).
# ---------------------------------------------------------------------------


def test_a_non_mapping_body_is_e_report_body_not_an_attributeerror():
    """m10 (batch 4 review): `body=42`, a `list`, and `None` all raised a
    bare `AttributeError` out of `_as_rows` before this guard existed —
    verified for BOTH renderers, since each calls `_as_rows` on its own.
    """
    for renderer in (render_markdown, render_html):
        for body in (42, [1, 2, 3], None):
            with pytest.raises(ContractError) as exc_info:
                list(renderer(iter([Section(title="t", body=body)])))
            assert exc_info.value.code == "E-REPORT-BODY", (renderer, body)


def test_report_of_a_completed_run_through_main_renders_all_four_sections(
    fixture_r: dict[str, Any], capsys: pytest.CaptureFixture[str]
):
    """Decision 6's `completed` arm, through the real command. Fixture R
    writes no `report.py`, so this is also the no-override path exercised
    through `main` rather than through `render_with_override` directly.
    """
    capsys.readouterr()
    code = main(["report", str(fixture_r["run_dir"] / "run.yaml")])
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert fixture_r["run"]["status"] == "completed"
    for title in ("Conditions", "Deltas", "Hypothesis verdicts", "Attrition"):
        assert f"## {title}" in out


_FAILS_EVERY_REPEAT_STEP = """\
# generated, and runnable as-is
from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        raise ValueError("Fixture P/F: deliberately fails, every repeat")
"""

_SWEPT_ANALYSIS_METHOD = {
    "baseline": {"analysis.method": "pearson"},
    "grid": {"analysis.method": ["spearman"]},
}


def test_fixture_p_a_partial_run_renders_at_exit_0_with_the_failures_shown(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """Decision 6's `partial` arm: `report` exits 0 with the failed
    executions shown by their OWN condition and repeat labels, read back
    from the record — Fixture P asserts the pair, not a bare code (task 8
    brief step 4)."""
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=10,
        replication={"repeats": [{"kind": "seed", "n": 2}]},
        sweep=_SWEPT_ANALYSIS_METHOD,
        extra_steps=["summarize"],
        extra_step_source=_FAILS_EVERY_REPEAT_STEP,
        expect_exit=EXIT_PARTIAL,
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    assert run["status"] == "partial"
    condition = run["execution"]["conditions"][0]
    condition_label = condition["label"]
    assert condition_label  # a fixture is a claim too: this must be non-empty
    entries = condition["steps"]["step02_summarize"]
    repeat_label, entry = next(iter(entries.items()))
    assert entry["status"] == "failed"

    capsys.readouterr()
    code = main(["report", str(doc["run_dir"] / "run.yaml")])
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert "## Attrition" in out
    assert "partial" in out
    assert condition_label in out
    assert repeat_label in out
    assert "failed" in out


def test_fixture_f_a_wholly_failed_run_also_renders_at_exit_0(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """Decision 6's `failed` arm: no step anywhere completes, so
    `run_status` reports `"failed"` rather than `"partial"`
    (`test_io_units_train_raises_without_a_fold_or_holdout`'s own measured
    shape) — and `report` still renders it at exit 0, the same rule
    covering all three statuses."""
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=10,
        sweep=_SWEPT_ANALYSIS_METHOD,
        _starter_step=_FAILS_EVERY_REPEAT_STEP,
        expect_exit=EXIT_FAILED,
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    assert run["status"] == "failed"

    capsys.readouterr()
    code = main(["report", str(doc["run_dir"] / "run.yaml")])
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert "## Attrition" in out
    assert "failed" in out


def test_report_form_e_report_form_through_main_is_exit_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """`E-REPORT-FORM`, redacted through the SAME collector path as every
    other refusal this function prints — no credentials are at stake this
    early, but the exit code and the coded diagnostic both travel through
    `main` rather than a direct `report_form` call."""
    bogus = tmp_path / "not_a_run_or_study.yaml"
    bogus.write_text("{}\n")
    capsys.readouterr()
    code = main(["report", str(bogus)])
    err = capsys.readouterr().err
    assert code == EXIT_WRONG
    assert "E-REPORT-FORM" in err


# --- Correction 7: redaction, with a positive control ---------------------

_REPORT_CRED_TEMPLATE = """\
from publishable import BaseTemplate, register_template


@register_template("cred_report_assay")
class CredReportAssay(BaseTemplate):
    naming_pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    required_env = ["PUBLISHABLE_TEST_REPORT_CRED"]
"""

_LEAKY_REPORT_OVERRIDE = """\
import os

from publishable import BaseReport


class Report(BaseReport):
    format = "markdown"

    def sections(self, run, io):
        raise RuntimeError(
            "boom, deliberately, carrying " + os.environ["PUBLISHABLE_TEST_REPORT_CRED"]
        )
"""

_REPORT_CRED_SENTINEL = "sekrit-report-h8c-task8-9f3a"


def _build_credentialed_project(tmp_path: Path) -> dict[str, Any]:
    """A project-local template (`required_env`), so `get_template`
    resolving it through `repo_root` is what makes `credentials`
    genuinely non-empty — never a hand-built record, on the advisor's own
    point that a positive control over a set populated by luck proves
    nothing."""
    from publishable.generators.experiment import generate_experiment

    root = tmp_path / "proj"
    data = tmp_path / "data"
    results = tmp_path / "results"
    data.mkdir(parents=True)
    rows = "\n".join(f"p{i}" for i in range(10))
    (data / "index.csv").write_text(f"patient_id\n{rows}\n")
    assert main(["new", str(root)]) == 0
    (root / "templates").mkdir(parents=True, exist_ok=True)
    (root / "templates" / "cred_report_assay.py").write_text(_REPORT_CRED_TEMPLATE)
    cfg = generate_experiment(
        repo_root=root,
        name="cohort-pilot",
        template_name="cred_report_assay",
        input_dir=str(data),
        output_dir=str(results),
    )
    doc = yaml.safe_load(cfg.read_text())
    doc["metadata"]["description"] = "H8c task 8 credential redaction positive control"
    doc["metadata"]["authors"] = ["Kyungjoon Lee"]
    cfg.write_text(yaml.safe_dump(doc))
    for args in (
        ["add", "."],
        ["-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "cred report"],
    ):
        subprocess.run(["git", *args], cwd=root, check=True)
    assert main(["run", str(cfg)]) == 0
    run_dir = next(results.glob("run_*"))
    return {"root": root, "run_dir": run_dir, "pkg": "cohort_pilot"}


def test_an_override_raise_carrying_a_declared_credential_is_redacted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    """Correction 7's whole point, verified through `main`. The override's
    `sections()` raises a plain `RuntimeError` — not a `ContractError` —
    carrying the declared credential's VALUE in its message; `report`
    must still redact it, through `E-REPORT-OVERRIDE-RAISED`.

    The template declares `required_env`, resolved through the project's
    OWN `repo_root` — never a hand-built `credentials` mapping — so a
    passing assertion here is evidence the wiring works, not evidence a
    fixture got lucky.
    """
    monkeypatch.delenv("PUBLISHABLE_TEST_REPORT_CRED", raising=False)
    monkeypatch.setenv("PUBLISHABLE_TEST_REPORT_CRED", _REPORT_CRED_SENTINEL)
    built = _build_credentialed_project(tmp_path)
    _write_report(built["root"], built["pkg"], _LEAKY_REPORT_OVERRIDE)

    capsys.readouterr()
    code = main(["report", str(built["run_dir"] / "run.yaml")])
    captured = capsys.readouterr()
    assert code == EXIT_WRONG
    # The pair, not just the absence (CLAUDE.md: "pair the absence with
    # the presence" — an assertion of absence alone passes identically if
    # nothing ran at all).
    assert _REPORT_CRED_SENTINEL not in captured.err
    assert _REPORT_CRED_SENTINEL not in captured.out
    assert "E-REPORT-OVERRIDE-RAISED" in captured.err
    assert "<redacted:PUBLISHABLE_TEST_REPORT_CRED>" in captured.err


# ---------------------------------------------------------------------------
# H8c task 9 — the draft refusal, and the bundle's flag-not-refuse
# asymmetry (docs/superpowers/plans/2026-08-21-report-study.md task 9;
# design Decision 7). **The bundle-flag arm is carried forward to task 10
# by name** — a bundle render does not exist yet, so it cannot be pinned
# here; task 10's own brief owns building it, over Fixture T's record
# placed inside a bundle.
# ---------------------------------------------------------------------------


def test_fixture_t_a_draft_run_is_refused_not_rendered(
    fixture_r: dict[str, Any], capsys: pytest.CaptureFixture[str]
):
    """Fixture T: `draft: true` is a SHIPPED key — `run` writes `draft:
    false` on every record it writes, measured just below — while the
    `draft` COMMAND is H9's and NOT BUILT. So this hand-edits a real,
    completed run's own record to the one key a genuine draft run would
    carry, and says so here rather than leaving a future reader to
    mistake it for one.

    M6's own assertion PAIR: exit 1 AND empty stdout. The exit code alone
    would already catch "render a draft with a banner instead of
    refusing" (that arm exits 0), but pairing it with emptiness also
    catches a refusal that printed something to stdout before failing —
    § Draft runs' verb is "refuses", not "refuses after printing".
    """
    run_path = fixture_r["run_dir"] / "run.yaml"
    doc = yaml.safe_load(run_path.read_text())
    assert doc["draft"] is False  # the fixture's own claim: `run` wrote this
    doc["draft"] = True
    run_path.write_text(yaml.safe_dump(doc))

    capsys.readouterr()
    code = main(["report", str(run_path)])
    captured = capsys.readouterr()
    assert code == EXIT_WRONG
    assert captured.out == ""
    assert "E-REPORT-DRAFT" in captured.err


# ---------------------------------------------------------------------------
# H8c task 8/9 fix round 1 — whole-branch review findings
# (.superpowers/sdd/2026-08-21-report-study/task-b5-review.md)
# ---------------------------------------------------------------------------

_KEYBOARD_INTERRUPT_REPORT_OVERRIDE = """\
from publishable import BaseReport


class Report(BaseReport):
    format = "markdown"

    def sections(self, run, io):
        raise KeyboardInterrupt("ctrl-c carrying sekrit-h8c-b5-fix-round-1")
"""


def test_major_3_keyboard_interrupt_from_an_override_propagates_with_no_message(
    fixture_r: dict[str, Any], capsys: pytest.CaptureFixture[str]
):
    """Whole-branch review, Major 3: the `except KeyboardInterrupt: raise
    KeyboardInterrupt from None` guard was shipped and pinned by NOTHING
    — mutating it to a bare `raise` left the full suite unchanged at
    2746, and the reviewer's own probe then leaked the sentinel. Pinned
    here the same way `test_a_resolvers_keyboard_interrupt_at_run_
    propagates_with_no_message` (`tests/test_cli.py`) pins the identical
    shape for a resolver: `pytest.raises(KeyboardInterrupt)` around
    `main([...])`, then assert the re-raised object carries no message —
    `excinfo.value.args == ()` — so a probe-constructed credential
    cannot reach Python's own uncaught-exception printer.

    A mutation deleting the `except KeyboardInterrupt` arm (falling
    through to the wide `except BaseException` below it) would report a
    finding and return `EXIT_WRONG` instead of propagating — this test
    would then see no `KeyboardInterrupt` at all and fail on
    `pytest.raises` itself, which is why the assertion is only
    reachable at all if the guard's `except` clause exists.
    """
    _write_report(fixture_r["root"], "cohort_pilot", _KEYBOARD_INTERRUPT_REPORT_OVERRIDE)
    capsys.readouterr()
    with pytest.raises(KeyboardInterrupt) as excinfo:
        main(["report", str(fixture_r["run_dir"] / "run.yaml")])
    assert excinfo.value.args == ()
    assert str(excinfo.value) == ""
    captured = capsys.readouterr()
    assert "sekrit-h8c-b5-fix-round-1" not in captured.out
    assert "sekrit-h8c-b5-fix-round-1" not in captured.err


# --- Minor 2: `E-REPORT-BODY` pinned through `main`, not through the
# renderer directly (task 8's own brief: no assertion via a direct call) ---

_BAD_BODY_REPORT_OVERRIDE = """\
from publishable import BaseReport


class Report(BaseReport):
    format = "markdown"

    def sections(self, run, io):
        yield self.section("Bad body", body=42)
"""


def test_minor_2_e_report_body_is_reachable_through_main(
    fixture_r: dict[str, Any], capsys: pytest.CaptureFixture[str]
):
    """Whole-branch review, Minor 2: the shipped guard was pinned only at
    `render_markdown`/`render_html` directly, against the brief's own
    "every assertion in this task goes through `main`" instruction. An
    override yielding a non-`str`, non-mapping `body` must give a coded
    refusal at the command, not a call-site-only guarantee."""
    _write_report(fixture_r["root"], "cohort_pilot", _BAD_BODY_REPORT_OVERRIDE)
    capsys.readouterr()
    code = main(["report", str(fixture_r["run_dir"] / "run.yaml")])
    err = capsys.readouterr().err
    assert code == EXIT_WRONG
    assert "E-REPORT-BODY" in err


# --- Minor 4: a SUCCESSFUL override, composing with the standard sections,
# rendered through the real command — both formats ---

_SUCCESSFUL_HTML_REPORT_OVERRIDE = """\
from publishable import BaseReport


class Report(BaseReport):
    format = "html"

    def sections(self, run, io):
        yield from super().sections(run, io)
        yield self.section("Extra figure", body="a figure an override adds")
"""


def test_minor_4_a_successful_html_override_renders_through_main(
    fixture_r: dict[str, Any], capsys: pytest.CaptureFixture[str]
):
    """Whole-branch review, Minor 4: every `main(["report", ...])` call in
    the suite so far was either the no-override path or a FAILURE path —
    `format = "html"` and a composing override's ordinary success were
    both unpinned at the command surface Decision 16 is about."""
    _write_report(fixture_r["root"], "cohort_pilot", _SUCCESSFUL_HTML_REPORT_OVERRIDE)
    capsys.readouterr()
    code = main(["report", str(fixture_r["run_dir"] / "run.yaml")])
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert out.startswith("<!doctype html>")
    assert "<h2>Conditions</h2>" in out
    assert "<h2>Extra figure</h2>" in out
    assert "a figure an override adds" in out


# --- Critical 1: `get_template` resolving OUTSIDE every `try`, before
# `credentials` exists, escaped into `main`'s bare, un-redacting handler ---

_RAISES_AFTER_REGISTRATION_CRED_TEMPLATE = """\
import os

from publishable import BaseTemplate, register_template


@register_template("cred_report_assay")
class CredReportAssay(BaseTemplate):
    naming_pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    required_env = ["PUBLISHABLE_TEST_REPORT_CRED"]


raise RuntimeError(
    "template top level boom, carrying " + os.environ["PUBLISHABLE_TEST_REPORT_CRED"]
)
"""


def test_critical_1_a_template_raising_after_registration_is_still_redacted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
):
    """Whole-branch review, Critical 1: `get_template`/`declared_
    credential_names_for` ran OUTSIDE every `try` and BEFORE `credentials`
    existed, so a project-local template that raises while importing —
    AFTER its own `@register_template` call, the case § Secrets &
    credentials explicitly promises IS covered — escaped `command_report`
    entirely into `main`'s bare `except PublishableError`, which
    `spec-defects.md` already files as un-redacted by construction.

    `freeze.py`'s own recipe (the one task 8 cited as precedent) wraps
    this exact call in a `try`/`except BaseException` and refuses through
    a redacting `Collector`, recovering `required_env` off the
    `partial_templates` the exception still carries — copied here.

    A project's `templates/` directory can hold only ONE file per
    experiment; this reuses `_build_credentialed_project`'s scaffold and
    then overwrites the template file with a module whose top level
    raises after registering, so the class exists in memory (readable
    for `required_env`) while the module that defined it is refused
    wholesale — the exact shape `PartialLoadError.partial_templates`
    exists for.
    """
    monkeypatch.delenv("PUBLISHABLE_TEST_REPORT_CRED", raising=False)
    monkeypatch.setenv("PUBLISHABLE_TEST_REPORT_CRED", _REPORT_CRED_SENTINEL)
    built = _build_credentialed_project(tmp_path)
    (built["root"] / "templates" / "cred_report_assay.py").write_text(
        _RAISES_AFTER_REGISTRATION_CRED_TEMPLATE
    )

    capsys.readouterr()
    code = main(["report", str(built["run_dir"] / "run.yaml")])
    captured = capsys.readouterr()
    assert code == EXIT_WRONG
    assert _REPORT_CRED_SENTINEL not in captured.err
    assert _REPORT_CRED_SENTINEL not in captured.out
    assert "<redacted:PUBLISHABLE_TEST_REPORT_CRED>" in captured.err
    assert "E-TEMPLATE-LOAD" in captured.err


# --- Major 1: the bundle form's own honest refusal, at an exit code
# Decision 6 permits, never the "command is not built" diagnostic ---


def test_major_1_report_of_a_bundle_path_is_report_s_own_refusal_not_a_false_claim(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """Whole-branch review, Major 1: `report <study.yaml>` printed
    `` `publishable report` is specified but not built `` at exit 2 —
    false as of the very commit that flipped the `Status` cell to
    `built`, and 2 is reserved for an invocation fault Decision 6 says is
    decided BEFORE this function is ever called. `report`'s own refusal
    was `E-REPORT-BUNDLE-UNSUPPORTED` at exit 1, naming the FORM rather
    than the command; task 10 retires that code wholesale (`CLAUDE.md`'s
    "-UNSUPPORTED suffix... retired wholesale, absent from the
    registry") and builds the real bundle render. This test now pins the
    SAME property — `report`'s own coded refusal, never the CLI's
    generic diagnostic, never exit 2 — over the bundle DOCUMENT'S own
    shape fault instead: `runs: []` is not a mapping, `E-STUDY-
    UNREADABLE`'s own trigger."""
    bundle = tmp_path / "study.yaml"
    bundle.write_text("runs: []\n")
    capsys.readouterr()
    code = main(["report", str(bundle)])
    err = capsys.readouterr().err
    assert code == EXIT_WRONG
    assert "E-STUDY-UNREADABLE" in err
    assert "E-REPORT-BUNDLE-UNSUPPORTED" not in err
    assert "is specified but not built" not in err


# --- Major 2: a parseable-but-incomplete record is refused, not a traceback ---


@pytest.mark.parametrize("dropped_key", ["execution", "results", "config"])
def test_major_2_a_record_missing_a_needed_key_is_refused_not_a_traceback(
    fixture_r: dict[str, Any], capsys: pytest.CaptureFixture[str], dropped_key: str
):
    """Whole-branch review, Major 2: `_report_io_from_record` subscripted
    `execution`, `results.conditions` and `config.data.input_dir`
    unguarded, so dropping any one of the three top-level keys gave a raw
    `KeyError` traceback out of a built command — where `diff` over the
    identical file renders at exit 0. Parametrized over all three
    dropped keys the reviewer's own table names, so each is independently
    proven refused rather than only the first one tried."""
    run_path = fixture_r["run_dir"] / "run.yaml"
    doc = yaml.safe_load(run_path.read_text())
    assert dropped_key in doc  # the fixture's own claim: it's really there
    del doc[dropped_key]
    run_path.write_text(yaml.safe_dump(doc))

    capsys.readouterr()
    code = main(["report", str(run_path)])
    err = capsys.readouterr().err
    assert code == EXIT_WRONG
    assert "E-REPORT-RECORD-INCOMPLETE" in err
    assert "Traceback" not in err


# ---------------------------------------------------------------------------
# H8c task 10 — the bundle render, and its two cross-checks
# (docs/superpowers/plans/2026-08-21-report-study.md task 10; design
# Decisions 1, 7, 8; § Corrections correction 17). `study new`/`study add`
# (tasks 11/13) do not exist yet in this build, so every bundle fixture
# below writes `study.yaml` and its bare `<name>.run.yaml` members BY HAND
# — the exact bytes reference.md § Building one already commits to, and
# what `study add` will eventually produce.
# ---------------------------------------------------------------------------


def _write_bundle(bundle_dir: Path, members: list[tuple[str, dict[str, Any]]]) -> Path:
    bundle_dir.mkdir(parents=True, exist_ok=True)
    runs: dict[str, Any] = {}
    for name, record in members:
        (bundle_dir / f"{name}.run.yaml").write_text(yaml.safe_dump(record))
        runs[name] = {"file": f"{name}.run.yaml", "run_id": record.get("run_id")}
    study_doc = {
        "title": "H8c task 10 bundle fixture",
        "authors": ["Kyungjoon Lee"],
        "runs": runs,
    }
    (bundle_dir / "study.yaml").write_text(yaml.safe_dump(study_doc, sort_keys=False))
    return bundle_dir / "study.yaml"


def _build_bundle_source_project(tmp_path: Path, *, name: str = "cohort-pilot") -> dict[str, Any]:
    """A minimal, real, committed project with no override and no extra
    step — used only to produce multiple run records sharing one
    `provenance.git.commit`/`code_hash` (Fixture B's own shape) by calling
    `main(["run", str(cfg)])` more than once against the identical
    committed tree, and to produce a second, DIFFERENT commit by editing
    and recommitting `src/**` between runs.
    """
    from publishable.generators.experiment import generate_experiment

    root = tmp_path / "proj"
    data = tmp_path / "data"
    results = tmp_path / "results"
    data.mkdir(parents=True)
    rows = "\n".join(f"p{i}" for i in range(10))
    (data / "index.csv").write_text(f"patient_id\n{rows}\n")
    assert main(["new", str(root)]) == 0
    cfg = generate_experiment(
        repo_root=root,
        name=name,
        template_name="generic",
        input_dir=str(data),
        output_dir=str(results),
    )
    doc = yaml.safe_load(cfg.read_text())
    doc["metadata"]["description"] = "H8c task 10 bundle fixtures"
    doc["metadata"]["authors"] = ["Kyungjoon Lee"]
    cfg.write_text(yaml.safe_dump(doc))
    for args in (
        ["add", "."],
        ["-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "bundle source"],
    ):
        subprocess.run(["git", *args], cwd=root, check=True)
    return {"root": root, "cfg": cfg, "results": results, "pkg": name.replace("-", "_")}


def _run_once(proj: dict[str, Any]) -> dict[str, Any]:
    before = {p.name for p in proj["results"].glob("run_*")}
    assert main(["run", str(proj["cfg"])]) == 0
    (run_dir,) = [p for p in proj["results"].glob("run_*") if p.name not in before]
    record = yaml.safe_load((run_dir / "run.yaml").read_text())
    return {"run_dir": run_dir, "record": record}


def _recommit_a_trivial_code_change(root: Path, pkg: str) -> None:
    """Edits `src/**` (never `configs/**`) so the NEXT run gets a genuinely
    different `code_hash` and `provenance.git.commit` — `code_hash` covers
    `src/**`/`templates/**` only, so a config-only edit would not move it.
    """
    starter = next((root / "src" / pkg / "steps").glob("step01_*.py"))
    starter.write_text(starter.read_text() + "\n# a trivial, harmless edit\n")
    for args in (
        ["add", "."],
        ["-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "trivial recommit"],
    ):
        subprocess.run(["git", *args], cwd=root, check=True)


def test_read_bundle_missing_study_yaml_is_e_study_unreadable(tmp_path: Path):
    with pytest.raises(ContractError) as excinfo:
        read_bundle(tmp_path / "study.yaml")
    assert excinfo.value.code == "E-STUDY-UNREADABLE"
    assert "no study.yaml at" in str(excinfo.value)


def test_read_bundle_invalid_yaml_is_e_study_unreadable(tmp_path: Path):
    path = tmp_path / "study.yaml"
    path.write_text("runs: [unterminated\n")
    with pytest.raises(ContractError) as excinfo:
        read_bundle(path)
    assert excinfo.value.code == "E-STUDY-UNREADABLE"
    assert "not valid YAML" in str(excinfo.value)


def test_read_bundle_not_a_mapping_is_e_study_unreadable(tmp_path: Path):
    path = tmp_path / "study.yaml"
    path.write_text("- just\n- a\n- list\n")
    with pytest.raises(ContractError) as excinfo:
        read_bundle(path)
    assert excinfo.value.code == "E-STUDY-UNREADABLE"
    assert "did not parse to a mapping" in str(excinfo.value)


def test_read_bundle_runs_not_a_mapping_is_e_study_unreadable(tmp_path: Path):
    path = tmp_path / "study.yaml"
    path.write_text("title: x\nauthors: []\nruns: []\n")
    with pytest.raises(ContractError) as excinfo:
        read_bundle(path)
    assert excinfo.value.code == "E-STUDY-UNREADABLE"
    assert "`runs` is" in str(excinfo.value)


def test_read_bundle_entry_not_a_mapping_is_e_study_unreadable(tmp_path: Path):
    path = tmp_path / "study.yaml"
    path.write_text("runs:\n  main: not-a-mapping\n")
    with pytest.raises(ContractError) as excinfo:
        read_bundle(path)
    assert excinfo.value.code == "E-STUDY-UNREADABLE"
    assert "runs.'main' is" in str(excinfo.value)


def test_read_bundle_file_field_missing_is_e_study_unreadable(tmp_path: Path):
    path = tmp_path / "study.yaml"
    path.write_text("runs:\n  main: {run_id: r1}\n")
    with pytest.raises(ContractError) as excinfo:
        read_bundle(path)
    assert excinfo.value.code == "E-STUDY-UNREADABLE"
    assert "not a non-empty string" in str(excinfo.value)


def test_read_bundle_file_not_in_the_bundle_is_e_study_unreadable(tmp_path: Path):
    path = tmp_path / "study.yaml"
    path.write_text("runs:\n  main: {file: main.run.yaml, run_id: r1}\n")
    with pytest.raises(ContractError) as excinfo:
        read_bundle(path)
    assert excinfo.value.code == "E-STUDY-UNREADABLE"
    assert "is not a file in the bundle" in str(excinfo.value)


def test_read_bundle_file_escaping_the_bundle_is_e_study_unreadable(tmp_path: Path):
    """'every reference is resolved relative to the bundle directory and
    nothing resolves outside it' (task 10's brief, step 2) — a `..`
    escape is refused with the SAME code as a missing file, never
    silently followed."""
    outside = tmp_path / "outside.yaml"
    outside.write_text(yaml.safe_dump({"run_id": "r1", "schema_version": "1.0"}))
    path = tmp_path / "bundle" / "study.yaml"
    path.parent.mkdir()
    path.write_text("runs:\n  main: {file: ../outside.yaml, run_id: r1}\n")
    with pytest.raises(ContractError) as excinfo:
        read_bundle(path)
    assert excinfo.value.code == "E-STUDY-UNREADABLE"
    assert "resolves outside the bundle directory" in str(excinfo.value)


def test_read_bundle_file_absolute_path_is_e_study_unreadable(tmp_path: Path):
    """An absolute `file` value is a second escape shape `..` does not
    cover: `Path.__truediv__` with an absolute right operand discards the
    left one entirely (measured: `Path("/bundle") / "/etc/passwd"` is
    `Path("/etc/passwd")`), so the join alone would silently step outside
    the bundle. Caught anyway by the SAME `relative_to` containment check
    that catches `..`, because the joined result still fails to sit under
    the bundle directory once resolved — not by a separate `is_absolute`
    guard, which would be a second, driftable rule for one property."""
    outside = tmp_path / "outside.yaml"
    outside.write_text(yaml.safe_dump({"run_id": "r1", "schema_version": "1.0"}))
    path = tmp_path / "bundle" / "study.yaml"
    path.parent.mkdir()
    path.write_text(f"runs:\n  main: {{file: {outside}, run_id: r1}}\n")
    with pytest.raises(ContractError) as excinfo:
        read_bundle(path)
    assert excinfo.value.code == "E-STUDY-UNREADABLE"
    assert "resolves outside the bundle directory" in str(excinfo.value)


def test_read_bundle_member_present_but_corrupt_is_e_upstream_record_unreadable(tmp_path: Path):
    """The adjacent-but-distinguishable fault task 10's brief step 1 names
    by hand: a `runs` entry whose `file` IS in the bundle but does not
    parse is `E-UPSTREAM-RECORD-UNREADABLE`, `read_record_file`'s own
    code — never `E-STUDY-UNREADABLE`, which is for the bundle DOCUMENT'S
    own shape."""
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    (bundle_dir / "main.run.yaml").write_text("not: a-run-record\n")
    path = bundle_dir / "study.yaml"
    path.write_text("runs:\n  main: {file: main.run.yaml, run_id: r1}\n")
    with pytest.raises(ContractError) as excinfo:
        read_bundle(path)
    assert excinfo.value.code == "E-UPSTREAM-RECORD-UNREADABLE"


@pytest.mark.parametrize("dropped_key", ["execution", "results", "config"])
def test_bundle_member_missing_a_needed_key_is_e_report_record_incomplete(
    fixture_r: dict[str, Any], capsys: pytest.CaptureFixture[str], dropped_key: str
):
    """Major 4 (whole-branch review): the bundle-side `E-REPORT-RECORD-
    INCOMPLETE` guard (`render_bundle`'s own `try`/`except`) was
    documented — the § Errors row widened in this same commit — and
    reached by NO test. Verified by running: deleting the whole
    `try`/`except` there left the full suite green, and a probe through
    the real console script confirmed the guard IS reachable. Parametrized
    over the run form's own three dropped keys (whole-branch review,
    Major 2, task-b5) so the bundle path is proven refused — never a
    traceback — through `main`, for each of the three facts the row
    names."""
    record = dict(fixture_r["run"])
    assert dropped_key in record  # the fixture's own claim: it's really there
    del record[dropped_key]
    bundle_path = _write_bundle(fixture_r["run_dir"].parent / "bundle", [("main", record)])
    capsys.readouterr()
    code = main(["report", str(bundle_path)])
    err = capsys.readouterr().err
    assert code == EXIT_WRONG
    assert "E-REPORT-RECORD-INCOMPLETE" in err
    assert "Traceback" not in err


def test_bundle_member_with_execution_not_a_mapping_is_refused_not_a_traceback(
    fixture_r: dict[str, Any], capsys: pytest.CaptureFixture[str]
):
    """Major 5 (whole-branch review): a member whose `execution` is a
    plain string (`execution: "x"`) reaches `.get` on a `str` inside
    `artifacts.derive_step_scopes_and_repeats` and raised a bare
    `AttributeError` traceback out of this built command — escaping the
    old `except (KeyError, TypeError)` at BOTH this guard's copy and the
    run form's. Both sites now also catch `AttributeError`, `ValueError`
    and `IndexError`; this pins the bundle side through the real command.
    The § Errors row named `execution` as covered before this fix made
    that true — this test is what makes the row's claim checkable rather
    than merely written."""
    record = dict(fixture_r["run"])
    record["execution"] = "x"
    bundle_path = _write_bundle(fixture_r["run_dir"].parent / "bundle", [("main", record)])
    capsys.readouterr()
    code = main(["report", str(bundle_path)])
    err = capsys.readouterr().err
    assert code == EXIT_WRONG
    assert "E-REPORT-RECORD-INCOMPLETE" in err
    assert "Traceback" not in err


def test_run_form_with_execution_not_a_mapping_is_refused_not_a_traceback(
    fixture_r: dict[str, Any], capsys: pytest.CaptureFixture[str]
):
    """Major 5's sibling arm, over `report <run.yaml>` directly — the site
    this task's bundle-side guard was copied FROM, and the one the
    reviewer confirmed shares the identical hole through the real
    console script."""
    run_path = fixture_r["run_dir"] / "run.yaml"
    doc = yaml.safe_load(run_path.read_text())
    doc["execution"] = "x"
    run_path.write_text(yaml.safe_dump(doc))
    capsys.readouterr()
    code = main(["report", str(run_path)])
    err = capsys.readouterr().err
    assert code == EXIT_WRONG
    assert "E-REPORT-RECORD-INCOMPLETE" in err
    assert "Traceback" not in err


def test_read_bundle_reads_members_in_declared_order(fixture_r: dict[str, Any]):
    record = fixture_r["run"]
    bundle_path = _write_bundle(
        fixture_r["run_dir"].parent / "bundle",
        [("second", record), ("first", record)],
    )
    _doc, members = read_bundle(bundle_path)
    assert [name for name, _ in members] == ["second", "first"]


def test_bundle_render_through_main_shows_every_members_standard_sections_and_hypotheses(
    fixture_r: dict[str, Any], capsys: pytest.CaptureFixture[str]
):
    bundle_path = _write_bundle(
        fixture_r["run_dir"].parent / "bundle",
        [("main", fixture_r["run"])],
    )
    capsys.readouterr()
    code = main(["report", str(bundle_path)])
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert "## main" in out
    assert "## Conditions" in out
    assert "## Deltas" in out
    assert "## Hypothesis verdicts" in out
    assert "## Attrition" in out
    assert "## Hypotheses" in out
    assert "h1" in out  # fixture_r's own declared hypothesis id, in the combined table


def test_bundle_hypotheses_table_tags_each_row_with_its_run_name(fixture_r: dict[str, Any]):
    """Major 2 (whole-branch review): the original version asserted only
    that each member's own name appeared SOMEWHERE in the rendered text —
    satisfied by `_bundle_header_section`'s `## <name>` heading alone, so
    deleting `{"run": name}` from `_bundle_hypotheses_rows` (report.py)
    left it green. Fixed by giving the two members DISTINCT hypothesis
    ids (`h1`, `h2`) and isolating the Hypotheses section's own text, so
    each hypothesis row's `run` tag is checked against ITS OWN row, not
    against output any other section could have produced."""
    second_record = dict(fixture_r["run"])
    results = dict(second_record["results"])
    hypotheses = [dict(results["hypotheses"][0])]
    hypotheses[0]["id"] = "h2"
    results["hypotheses"] = hypotheses
    second_record["results"] = results

    bundle_path = _write_bundle(
        bundle_dir=fixture_r["run_dir"].parent / "bundle",
        members=[("baseline_run", fixture_r["run"]), ("second_run", second_record)],
    )
    _doc, members = read_bundle(bundle_path)
    rendered = render_bundle(bundle_path.parent, members)

    hypotheses_text = rendered.split("## Hypotheses", 1)[1]
    (h1_row,) = [line for line in hypotheses_text.splitlines() if "h1" in line and "|" in line]
    (h2_row,) = [line for line in hypotheses_text.splitlines() if "h2" in line and "|" in line]
    assert "baseline_run" in h1_row
    assert "second_run" not in h1_row
    assert "second_run" in h2_row
    assert "baseline_run" not in h2_row


# --- Fixture T's bundle arm (carried from task 9 by name) ---


def test_fixture_t_bundle_flags_a_draft_member_at_exit_0(
    fixture_r: dict[str, Any], capsys: pytest.CaptureFixture[str]
):
    """Fixture T's SECOND arm, over the bundle render that did not exist
    when task 9 ran: `report <run.yaml>` refuses a draft (pinned already,
    task 9); `report <study.yaml>` FLAGS one instead (Decision 7's own
    asymmetry — "a bundle is a set, and refusing the whole render because
    one of five runs was a draft would throw away four legitimate
    renders"). `draft: true` is hand-edited onto a real, completed
    record — the shipped key, never the unbuilt `draft` COMMAND — exactly
    as task 9's own Fixture T states.

    Major 3 (whole-branch review): the original version named the
    flagged member `draft_run` and asserted bare `"draft" in out`, which
    the member's OWN NAME already satisfies via `## draft_run` — verified
    by neutering the flag in `_bundle_header_section` and finding the
    surviving `"draft"` hits were exactly that heading and a hypotheses
    row, with the suite unchanged. Renamed to names carrying no
    substring of "draft" (`sensitivity`, `primary`), and the flagged
    member's own section text is isolated from the clean member's before
    asserting, so only the flag's OWN SENTENCE — reachable only through
    `if record.get("draft") is True` — can satisfy the assertion."""
    draft_record = dict(fixture_r["run"])
    assert draft_record["draft"] is False  # the fixture's own claim
    draft_record["draft"] = True
    bundle_path = _write_bundle(
        fixture_r["run_dir"].parent / "bundle",
        [("sensitivity", draft_record), ("primary", fixture_r["run"])],
    )
    capsys.readouterr()
    code = main(["report", str(bundle_path)])
    out = capsys.readouterr().out
    assert code == EXIT_OK
    sensitivity_block, primary_block = out.split("## primary", 1)
    assert "not reachable from any commit" in sensitivity_block
    assert "not reachable from any commit" not in primary_block
    assert "## Conditions" in primary_block  # the clean run's own sections still render


# --- No override discovery happens on the bundle path, ever ---


def test_bundle_render_never_calls_render_with_override(
    fixture_r: dict[str, Any], monkeypatch: pytest.MonkeyPatch
):
    """The batch's own negative, proven DIRECTLY: `render_with_override` is
    the run form's one entry point into override discovery, and this
    monkeypatches it to fail loudly if anything on the bundle path ever
    calls it. A passing bundle render through the SAME `render_bundle`
    `command_report` calls is the proof — not an inference from "no extra
    section appeared", which a discovery call that happened to import
    nothing could also produce."""
    import publishable.report as report_module

    def _fail_if_called(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("render_with_override was called on the bundle path")

    monkeypatch.setattr(report_module, "render_with_override", _fail_if_called)
    bundle_path = _write_bundle(
        fixture_r["run_dir"].parent / "bundle",
        [("main", fixture_r["run"])],
    )
    _doc, members = report_module.read_bundle(bundle_path)
    text = report_module.render_bundle(bundle_path.parent, members)
    assert "## Conditions" in text


def test_m_discovery_bundle_beside_a_report_py_shows_no_extra_section(tmp_path: Path):
    """The design's own Fixture: "an arm whose bundle sits beside a
    directory holding a `report.py`, asserting no extra section appears."
    `_build_project` builds a real, committed project; `_write_report`
    gives it a `report.py` with a distinctly-titled extra section. The
    bundle sits in a SIBLING directory and its one member's `entrypoint`
    still names that project's own package — the shape a wrongly-wired
    discovery call would need to succeed.

    Minor 1 (whole-branch review): the original version left the bundle
    directory WITHOUT `environment/repo_root.txt`, so a wrongly-wired
    discovery call there would raise `E-REPORT-OVERRIDE-REPO` before ever
    reaching the decoy's import — the fixture caught the discovery
    mutation by CRASH, not by its own assertion, and could not tell "no
    discovery" apart from "discovery that fails for an unrelated reason".
    Verified by running: under the discovery mutation, adding
    `repo_root.txt` (as below) made the decoy section RENDER for real.
    Writing that file here makes the mutation succeed if it ran at all,
    so this assertion is now load-bearing rather than a crash in
    disguise — the negative is `DECOY OVERRIDE SECTION` staying absent
    even though discovery, if it ran, would find and render it."""
    built = _build_project(tmp_path / "proj", tmp_path / "data", tmp_path / "results")
    _write_report(
        built["root"],
        built["pkg"],
        "from publishable import BaseReport\n\n\n"
        "class Report(BaseReport):\n"
        '    format = "markdown"\n\n'
        "    def sections(self, run, io):\n"
        "        yield from super().sections(run, io)\n"
        "        yield self.section('DECOY OVERRIDE SECTION', body='should never render')\n",
    )
    bundle_path = _write_bundle(tmp_path / "bundle", [("main", built["record"])])
    environment_dir = bundle_path.parent / "environment"
    environment_dir.mkdir()
    (environment_dir / "repo_root.txt").write_text(str(built["root"]))

    _doc, members = read_bundle(bundle_path)
    text = render_bundle(bundle_path.parent, members)
    assert "DECOY OVERRIDE SECTION" not in text
    assert "## Conditions" in text


# --- Decision 8's two cross-checks: recorded figures compared, neither computed ---


def _apparatus_block(facts: dict[str, Any]) -> dict[str, Any]:
    """A hand-built `provenance.apparatus` block, over a hand-chosen
    `facts` mapping and its OWN, honestly-computed `apparatus_hash` —
    Fixture A's shape without the full probe/plugin machinery H7d's
    original Fixture P needed, because `report` never calls
    `apparatus_hash` at all: only the two fields it reads (`hash`,
    implicitly `facts`) matter to the code under test here."""
    return {
        "probe": "test_probe",
        "ledger": "apparatus/probes.jsonl",
        "hash": apparatus_hash(facts),
        "facts": facts,
        "unobserved": [],
    }


def _with_apparatus(record: dict[str, Any], apparatus: "dict[str, Any] | None") -> dict[str, Any]:
    copy = dict(record)
    provenance = dict(copy["provenance"])
    provenance["apparatus"] = apparatus
    copy["provenance"] = provenance
    return copy


def test_bundle_two_runs_same_commit_same_code_hash_no_notice(
    fixture_r: dict[str, Any], capsys: pytest.CaptureFixture[str]
):
    """Major 1 (whole-branch review): the original version took no
    `capsys` and asserted only `EXIT_OK` — which `command_report`'s own
    docstring guarantees neither cross-check notice ever changes, so the
    assertion could not fail even if `W-STUDY-CODE-HASH-MISMATCH` fired
    on every honest pair. Verified by running: making
    `_bundle_cross_checks` emit the notice unconditionally left the old
    body green. Now asserts the notice's ABSENCE directly, matching the
    sibling apparatus agree-arm's own shape."""
    proj = _build_bundle_source_project(fixture_r["run_dir"].parent.parent / "src2")
    a = _run_once(proj)
    b = _run_once(proj)
    assert a["record"]["provenance"]["git"]["commit"] == b["record"]["provenance"]["git"]["commit"]
    assert a["record"]["code_hash"] == b["record"]["code_hash"]
    bundle_path = _write_bundle(
        proj["results"] / "bundle", [("a", a["record"]), ("b", b["record"])]
    )
    capsys.readouterr()
    code = main(["report", str(bundle_path)])
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert "W-STUDY-CODE-HASH-MISMATCH" not in out


def test_bundle_notice_code_hash_mismatch_under_one_commit(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """Two runs recording the SAME `provenance.git.commit` but a
    hand-edited, differing `code_hash` — the case Decision 8 exists for,
    unreachable from two honest runs of one committed tree, so the
    docstring says this one was edited."""
    proj = _build_bundle_source_project(tmp_path)
    a = _run_once(proj)
    b = _run_once(proj)
    b["record"]["code_hash"] = "sha256:" + "0" * 64  # hand-edited to disagree
    assert a["record"]["code_hash"] != b["record"]["code_hash"]
    bundle_path = _write_bundle(
        proj["results"] / "bundle", [("a", a["record"]), ("b", b["record"])]
    )
    capsys.readouterr()
    code = main(["report", str(bundle_path)])
    out = capsys.readouterr().out
    assert code == EXIT_OK  # a notice, never a refusal
    assert "W-STUDY-CODE-HASH-MISMATCH" in out


def test_bundle_no_code_hash_notice_across_two_different_commits(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """A sensitivity rerun at a later commit is ordinary (Decision 11's own
    precedent) — two runs at DIFFERENT commits are never grouped for the
    `code_hash` comparison at all, so a genuinely different `code_hash`
    between them is not a finding."""
    proj = _build_bundle_source_project(tmp_path)
    a = _run_once(proj)
    _recommit_a_trivial_code_change(proj["root"], proj["pkg"])
    b = _run_once(proj)
    assert a["record"]["provenance"]["git"]["commit"] != b["record"]["provenance"]["git"]["commit"]
    assert a["record"]["code_hash"] != b["record"]["code_hash"]
    bundle_path = _write_bundle(
        proj["results"] / "bundle", [("a", a["record"]), ("b", b["record"])]
    )
    capsys.readouterr()
    code = main(["report", str(bundle_path)])
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert "W-STUDY-CODE-HASH-MISMATCH" not in out


def test_bundle_apparatus_hashes_agree_no_notice(
    fixture_r: dict[str, Any], capsys: pytest.CaptureFixture[str]
):
    facts = {"gpu": "A100"}
    a = _with_apparatus(fixture_r["run"], _apparatus_block(facts))
    b = _with_apparatus(fixture_r["run"], _apparatus_block(facts))
    bundle_path = _write_bundle(fixture_r["run_dir"].parent / "bundle", [("a", a), ("b", b)])
    capsys.readouterr()
    code = main(["report", str(bundle_path)])
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert "W-STUDY-APPARATUS-MISMATCH" not in out


def test_bundle_missing_code_hash_excluded_not_printed_as_none(
    fixture_r: dict[str, Any], capsys: pytest.CaptureFixture[str]
):
    """Minor 2 (whole-branch review): a record with NO `code_hash` at all
    is now excluded from the comparison rather than folded in as the
    string `'None'` — verified before the fix by calling
    `_bundle_cross_checks` directly and observing
    `code_hash differs (['None', 'sha256:...'])` for a pair that never
    made a disagreeing claim at all. One member's `code_hash` key is
    deleted outright (not set to `null`); the other's is real. Same
    commit on both, so without the fix the pair would have been
    reported."""
    a = dict(fixture_r["run"])
    del a["code_hash"]
    b = dict(fixture_r["run"])
    assert a["provenance"]["git"]["commit"] == b["provenance"]["git"]["commit"]
    bundle_path = _write_bundle(fixture_r["run_dir"].parent / "bundle", [("a", a), ("b", b)])
    capsys.readouterr()
    code = main(["report", str(bundle_path)])
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert "W-STUDY-CODE-HASH-MISMATCH" not in out
    assert "None" not in out


def test_bundle_apparatus_mapping_with_no_hash_key_excluded_not_printed_as_none(
    fixture_r: dict[str, Any], capsys: pytest.CaptureFixture[str]
):
    """Minor 2's identical fix one column over: an apparatus block that IS
    a mapping but carries no `hash` key at all — distinct from Decision
    8's own `null`-apparatus case, which this fixture does not exercise —
    is excluded the same way, rather than contributing the string
    `'None'` to a printed mismatch beside a real hash."""
    a = _with_apparatus(fixture_r["run"], {"probe": "x", "facts": {}})  # no "hash" key
    b = _with_apparatus(fixture_r["run"], _apparatus_block({"gpu": "A100"}))
    bundle_path = _write_bundle(fixture_r["run_dir"].parent / "bundle", [("a", a), ("b", b)])
    capsys.readouterr()
    code = main(["report", str(bundle_path)])
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert "W-STUDY-APPARATUS-MISMATCH" not in out
    assert "None" not in out


def test_bundle_apparatus_hashes_differ_under_one_commit_is_a_notice(
    fixture_r: dict[str, Any], capsys: pytest.CaptureFixture[str]
):
    a = _with_apparatus(fixture_r["run"], _apparatus_block({"gpu": "A100"}))
    b = _with_apparatus(fixture_r["run"], _apparatus_block({"gpu": "H100"}))
    bundle_path = _write_bundle(fixture_r["run_dir"].parent / "bundle", [("a", a), ("b", b)])
    capsys.readouterr()
    code = main(["report", str(bundle_path)])
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert "W-STUDY-APPARATUS-MISMATCH" in out


def test_bundle_apparatus_hand_edited_hash_disagrees_with_recomputation(
    fixture_r: dict[str, Any], capsys: pytest.CaptureFixture[str]
):
    """M3's own fixture: a record whose recorded `provenance.apparatus.hash`
    has been hand-edited to disagree with a recomputation over its OWN
    `facts` — the only record on which "compare the recorded string" and
    "recompute from `facts`" give different answers, because on every
    honest record the two already agree (H8b's own
    `test_the_apparatus_hash_is_recomputable_from_the_recorded_facts`
    pin). Both members share identical facts (so a RECOMPUTATION would
    find them equal); one's RECORDED `hash` is edited to a different
    string, so shipped code (comparing recorded strings) fires the
    notice."""
    facts = {"gpu": "A100"}
    honest = _apparatus_block(facts)
    tampered = dict(honest)
    tampered["hash"] = "sha256:" + "f" * 64
    assert tampered["hash"] != apparatus_hash(facts)  # the fixture's own claim: it disagrees
    a = _with_apparatus(fixture_r["run"], honest)
    b = _with_apparatus(fixture_r["run"], tampered)
    bundle_path = _write_bundle(fixture_r["run_dir"].parent / "bundle", [("a", a), ("b", b)])
    capsys.readouterr()
    code = main(["report", str(bundle_path)])
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert "W-STUDY-APPARATUS-MISMATCH" in out


def test_bundle_null_apparatus_excluded_not_counted_a_mismatch(
    fixture_r: dict[str, Any], capsys: pytest.CaptureFixture[str]
):
    """Decision 8's exclusion rule, over its own named fixture: one run
    with `provenance.apparatus: null` beside one with a real block, under
    the SAME commit. "This experiment declares no probe" is not a
    deployment claim, so this must NOT fire — which the other three arms
    (agree / differ / hand-edited) cannot see, since each of them has two
    non-null members already."""
    a = _with_apparatus(fixture_r["run"], None)
    b = _with_apparatus(fixture_r["run"], _apparatus_block({"gpu": "A100"}))
    bundle_path = _write_bundle(fixture_r["run_dir"].parent / "bundle", [("a", a), ("b", b)])
    capsys.readouterr()
    code = main(["report", str(bundle_path)])
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert "W-STUDY-APPARATUS-MISMATCH" not in out
