"""H9d task 9 — fixture E: the stale-bytecode pair, at all three call sites.

Two `spec-defects.md` filings, one root cause. CPython's `SourceFileLoader`
validates its `__pycache__/*.pyc` against the source's `(mtime, size)`, and
`mtime` is whole-second on the filesystems this was measured against — so a
**same-size** rewrite inside one wall-clock second is served from the previous
compile, at exit `0`, with no exception and no diagnostic.

Each arm below rewrites a file **at the same byte length** — a differently
sized second file is picked up even unfixed, so it would test nothing — and
then **pins the mtime of the first write onto the second** with `os.utime`.
That is the fixture's own claim made deterministic rather than left to the
clock: without it, a second boundary falling between the two writes makes the
arm pass for a reason that has nothing to do with the code, which is the
shape the filing itself describes as *"a caller would misdiagnose as
flakiness."*

The three arms exercise the three PRODUCTION entry points — `discover_local`,
`render_with_override`, `load_experiment` — rather than the loader, so
reverting the fix at exactly one site fails exactly one of them (design § 10
row 6, *a sweep that stops one file short*).
"""

import os
import subprocess
import sys
import threading
from pathlib import Path

import yaml

from publishable.base_experiment import load_experiment
from publishable.report import render_with_override
from publishable.templates.discovery import discover_local


def _rewrite_at_the_same_second(path: Path, text: str) -> None:
    """Overwrite `path` with `text`, keeping the file's own `(mtime, size)`.

    Asserts the size actually matches, because a same-second rewrite of a
    DIFFERENT size is picked up even unfixed: the arm would go green while
    testing nothing, which is the one way this fixture can lie.
    """
    before = path.stat()
    assert len(text.encode()) == before.st_size, (
        "fixture E requires a same-LENGTH rewrite: "
        f"{len(text.encode())} bytes replacing {before.st_size}"
    )
    path.write_text(text)
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
    assert path.stat().st_mtime_ns == before.st_mtime_ns


_TEMPLATE = """\
from publishable import BaseTemplate, register_template


@register_template("s_assay")
class SAssay(BaseTemplate):
    apparatus_probe = "{probe}"
"""


def test_discover_local_serves_the_second_write_not_the_first(tmp_path: Path):
    """Call site 1 — `templates/discovery.py::_import_file`, and the filing's
    own recipe verbatim: write `templates/s.py` declaring
    `apparatus_probe = "f_probe"`, resolve, overwrite the SAME path with
    `"g_probe"` at the same byte length, resolve again. The claim is
    `g_probe`.
    """
    templates = tmp_path / "templates"
    templates.mkdir()
    source = templates / "s.py"
    source.write_text(_TEMPLATE.format(probe="f_probe"))

    first = discover_local(tmp_path)
    assert first["s_assay"].cls.apparatus_probe == "f_probe"

    _rewrite_at_the_same_second(source, _TEMPLATE.format(probe="g_probe"))

    second = discover_local(tmp_path)
    assert second["s_assay"].cls.apparatus_probe == "g_probe"


_OVERRIDE = """\
from publishable import BaseReport


class Override(BaseReport):
    MARKER = "MARKER_{marker}"
"""


def test_render_with_override_serves_the_second_write_not_the_first(tmp_path: Path):
    """Call site 2 — `report.py::render_with_override`. The filing's own
    recipe: render an override whose body is `MARKER_AAA`, rewrite the
    identical file with `MARKER_BBB` — byte-identical in length, same second —
    and render again. Unfixed, the second render answers `MARKER_AAA` at exit
    `0`, which is `report`'s entire artifact being silently the previous
    version of a file its author just edited.
    """
    from tests.test_report import _build_project, _write_report

    built = _build_project(tmp_path / "proj", tmp_path / "data", tmp_path / "results")
    _write_report(built["root"], built["pkg"], _OVERRIDE.format(marker="AAA"))
    override = built["root"] / "src" / built["pkg"] / "report.py"

    first = render_with_override(built["run_dir"], built["record"], render=lambda cls: cls)
    assert first is not None
    assert first.MARKER == "MARKER_AAA"

    _rewrite_at_the_same_second(override, _OVERRIDE.format(marker="BBB"))

    second = render_with_override(built["run_dir"], built["record"], render=lambda cls: cls)
    assert second is not None
    assert second.MARKER == "MARKER_BBB"


_ENTRYPOINT = """\
from publishable import BaseExperiment, BaseStep


class Step01Measure(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        return {{}}


class CohortPilotExperiment(BaseExperiment):
    steps = [Step01Measure]
    MARKER = "MARKER_{marker}"
"""


def test_load_experiment_serves_the_second_write_not_the_first(git_repo: Path):
    """Call site 3 — `base_experiment.py::load_experiment`, which
    `validate` and `run` both reach. It predates the filing that found the
    other two and has the identical exposure: an entrypoint rewritten at the
    same size inside one second is served from the previous compile, so a run
    executes the steps of a pipeline its author has already changed.
    """
    package = git_repo / "src" / "cohort_pilot"
    source = package / "experiment.py"
    source.write_text(_ENTRYPOINT.format(marker="AAA"))

    first = load_experiment(git_repo, "cohort_pilot.experiment:CohortPilotExperiment")
    assert first.MARKER == "MARKER_AAA"

    _rewrite_at_the_same_second(source, _ENTRYPOINT.format(marker="BBB"))

    second = load_experiment(git_repo, "cohort_pilot.experiment:CohortPilotExperiment")
    assert second.MARKER == "MARKER_BBB"


def test_the_fix_is_not_sys_dont_write_bytecode_and_leaves_it_alone(tmp_path: Path):
    """Design Decision 10 rejects `sys.dont_write_bytecode` because it is
    module-global and would change compilation for every concurrent import in
    the process. This is the assertion that says the shipped fix did not
    quietly take it anyway — a flag flipped and restored around one import
    would pass every arm above.

    Both halves: the flag is untouched by a resolution, and an ordinary
    import in the same process still writes its cache.
    """
    before = sys.dont_write_bytecode
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "s.py").write_text(_TEMPLATE.format(probe="f_probe"))
    assert discover_local(tmp_path)["s_assay"].cls.apparatus_probe == "f_probe"
    assert sys.dont_write_bytecode is before

    other = tmp_path / "elsewhere"
    other.mkdir()
    (other / "_h9d_ordinary_module.py").write_text("VALUE = 1\n")
    sys.path.insert(0, str(other))
    try:
        import _h9d_ordinary_module  # noqa: PLC0415

        assert _h9d_ordinary_module.VALUE == 1
    finally:
        sys.path.remove(str(other))
        sys.modules.pop("_h9d_ordinary_module", None)
    assert list((other / "__pycache__").glob("*.pyc"))


def test_a_project_whose_steps_a_run_imports_still_runs_end_to_end(tmp_path: Path):
    """The positive control for all three arms: forcing recompilation must not
    break ordinary importing. A real scaffolded project, generated, committed
    and RUN — `validate` and `run` both go through `load_experiment`, and the
    generated experiment module imports its own `steps/` package, so this
    exercises a dotted import chain rather than one file.
    """
    from publishable.cli import main
    from publishable.generators.experiment import generate_experiment

    data, results = tmp_path / "data", tmp_path / "results"
    data.mkdir()
    (data / "index.csv").write_text("patient_id\n" + "\n".join(f"p{i}" for i in range(6)) + "\n")
    root = tmp_path / "proj"
    assert main(["new", str(root)]) == 0
    cfg = generate_experiment(
        repo_root=root,
        name="cohort-pilot",
        template_name="generic",
        input_dir=str(data),
        output_dir=str(results),
    )
    doc = yaml.safe_load(cfg.read_text())
    doc["metadata"]["description"] = "H9d fixture E positive control"
    doc["metadata"]["authors"] = ["Kyungjoon Lee"]
    cfg.write_text(yaml.safe_dump(doc))
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "control"],
        cwd=root,
        check=True,
    )
    assert main(["run", str(cfg)]) == 0
    assert (next(results.glob("run_*")) / "run.yaml").is_file()


_RACE_STEP = "class Step:\n    scope = 'run'\n" + "# padding, to widen the exec window\n" * 200

_RACE_ENTRYPOINT = (
    "".join(f"from .steps.step{i:02d} import Step as S{i}\n" for i in range(6))
    + """\

from publishable import BaseExperiment


class RaceExperiment(BaseExperiment):
    steps = []
"""
)


def test_two_threads_loading_one_project_do_not_corrupt_each_others_import(tmp_path: Path):
    """`load_experiment` purges `sys.modules` and opens a `sys.path` window,
    and two of them at once corrupt each other unless the window is atomic.

    Core spawns no threads, so no command reaches this. `test_cli.py`'s H9b
    arm G does: it drives two `main(["resume", ...])` calls in threads as a
    stand-in for the two PROCESSES a takeover race is really between, and
    processes do not share `sys.modules`. That arm went red on CI on
    2026-08-29 with `KeyError: 'cohort_pilot.steps.step02_step02_score'` and
    had never failed on a developer machine, so this is the same hazard driven
    directly rather than through a run.

    **Sized against the unfixed code rather than guessed.** Unserialized, two
    threads over this project raise within milliseconds — 43,697 failures in 8
    seconds when the shape was first measured — in two forms: a purge landing
    between another thread's `exec_module` and CPython's
    `sys.modules.pop(spec.name)`, and `import_module_fresh` handing back a
    module another thread is still executing. The step modules are padded and
    there are six of them because both windows are the duration of an exec.
    """
    package = tmp_path / "src" / "race_pkg"
    (package / "steps").mkdir(parents=True)
    (package / "__init__.py").write_text("")
    (package / "steps" / "__init__.py").write_text("")
    for index in range(6):
        (package / "steps" / f"step{index:02d}.py").write_text(_RACE_STEP)
    (package / "experiment.py").write_text(_RACE_ENTRYPOINT)

    failures: list[str] = []
    guard = threading.Lock()

    def load_repeatedly() -> None:
        for _ in range(25):
            try:
                load_experiment(tmp_path, "race_pkg.experiment:RaceExperiment")
            except BaseException as exc:  # noqa: BLE001 - the failure is the finding
                with guard:
                    failures.append(f"{type(exc).__name__}: {exc}")
                return

    threads = [threading.Thread(target=load_repeatedly) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=120)

    assert not any(thread.is_alive() for thread in threads)
    assert failures == [], failures
