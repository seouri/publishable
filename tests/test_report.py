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
from publishable.errors import ContractError
from publishable.report import Section, render_with_override


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


# ---------------------------------------------------------------------------
# H8c task 3 — override discovery, alone in its batch because it is this
# slice's proxy risk (docs/superpowers/specs/2026-08-21-report-study-design.md
# Decision 3; docs/superpowers/plans/2026-08-21-report-study.md task 3).
# Every fixture below runs a REAL project through `main(["run", ...])` —
# never a hand-built record — because the whole point is that discovery
# reads the run's own `environment/repo_root.txt` and `config.entrypoint`,
# artifacts only a real run writes honestly.
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
    `entrypoint`. Two packages sit side by side in the same `src/`, each
    with its own `BaseReport` override and its own titled section; only
    one is named by this run's `entrypoint`. A scan finds both and must
    pick one — any pick is observable, and the correct answer is the one
    `entrypoint` names, not whichever a scan happens to prefer. On a
    one-package project the two readings are byte-identical, which is why
    this fixture has two.
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
    aaa_decoy_pkg = built["root"] / "src" / "aaa_decoy_pkg"
    aaa_decoy_pkg.mkdir(parents=True)
    (aaa_decoy_pkg / "__init__.py").write_text("")
    (aaa_decoy_pkg / "report.py").write_text(
        "from publishable import BaseReport\n\n\n"
        "class Report(BaseReport):\n"
        "    format = 'markdown'\n\n"
        "    def sections(self, run, io):\n"
        "        yield self.section('DECOY', body='x')\n",
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
