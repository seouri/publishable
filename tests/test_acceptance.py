"""S1's whole promise: `reference.md` § The starter step runs."""

import math
import subprocess
from pathlib import Path

import pytest
import yaml

from publishable.cli import main
from publishable.diagnostics import EXIT_FAILED, EXIT_OK, EXIT_WRONG


def build(tmp_path: Path) -> tuple[Path, Path, Path]:
    root = tmp_path / "my-study"
    data = tmp_path / "data"
    results = tmp_path / "results"
    data.mkdir()
    (data / "index.csv").write_text("patient_id\np1\np2\n")
    assert main(["new", str(root)]) == EXIT_OK
    from publishable.generators.experiment import generate_experiment

    cfg = generate_experiment(
        repo_root=root,
        name="cohort-pilot",
        template_name="generic",
        input_dir=str(data),
        output_dir=str(results),
    )
    doc = yaml.safe_load(cfg.read_text())
    doc["metadata"]["description"] = "the spine's acceptance run"
    doc["metadata"]["authors"] = ["Kyungjoon Lee"]
    cfg.write_text(yaml.safe_dump(doc))
    for args in (
        ["add", "."],
        ["-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "experiment"],
    ):
        subprocess.run(["git", *args], cwd=root, check=True)
    return root, cfg, results


def test_scaffold_then_run_produces_a_real_record(tmp_path: Path, capsys):
    root, cfg, results = build(tmp_path)
    assert main(["validate", str(cfg)]) == EXIT_OK
    assert main(["run", str(cfg)]) == EXIT_OK

    run_dir = next(results.glob("run_*"))
    doc = yaml.safe_load((run_dir / "run.yaml").read_text())

    assert doc["status"] == "completed"
    assert doc["draft"] is False
    assert doc["code_hash"].startswith("sha256:")
    assert doc["parameters_hash"].startswith("sha256:")
    assert doc["provenance"]["input_manifest_hash"].startswith("sha256:")
    assert doc["config"]["metadata"]["name"] == "cohort-pilot"
    assert doc["config"] == yaml.safe_load(cfg.read_text())  # embedded verbatim

    # Read from installed package metadata, not hardcoded, so it cannot drift from
    # `pyproject.toml` and `CITATION.cff`.
    import importlib.metadata

    assert doc["provenance"]["publishable_version"] == importlib.metadata.version(
        "publishable"
    )

    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True
    ).stdout.strip()
    assert doc["provenance"]["git"]["commit"] == commit
    assert doc["provenance"]["git"]["code_dirty"] is False

    assert run_dir.name.startswith("run_")
    assert run_dir.name.endswith(doc["code_hash"].split(":")[1][:7])
    assert (run_dir / "executions.jsonl").is_file()
    assert (run_dir / "manifest" / "input.json").is_file()
    assert not (run_dir / "lock").exists()

    # `root` scaffolds with no `uv.lock` (publishable isn't published, so `uv lock`
    # can't resolve inside a generated project yet) — `pyproject.toml` is still always
    # captured, and the run says out loud that it isn't pinned rather than staying quiet.
    assert (run_dir / "environment" / "pyproject.toml").read_bytes() == (
        root / "pyproject.toml"
    ).read_bytes()
    assert not (run_dir / "environment" / "uv.lock").exists()
    assert doc["provenance"]["environment"]["uv_lock"] is None
    assert doc["provenance"]["environment"]["uv_lock_hash"] is None
    assert "W-ENV-UNLOCKED" in capsys.readouterr().out


def test_a_present_lockfile_is_captured_and_hashed_with_no_warning(tmp_path: Path, capsys):
    root, cfg, results = build(tmp_path)
    (root / "uv.lock").write_text("# a stand-in lockfile; uv_support only hashes and copies it\n")
    subprocess.run(["git", "add", "uv.lock"], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "lock"],
        cwd=root,
        check=True,
    )

    assert main(["run", str(cfg)]) == EXIT_OK
    run_dir = next(results.glob("run_*"))
    doc = yaml.safe_load((run_dir / "run.yaml").read_text())

    assert (run_dir / "environment" / "uv.lock").read_bytes() == (root / "uv.lock").read_bytes()
    assert (run_dir / "environment" / "pyproject.toml").is_file()
    assert doc["provenance"]["environment"]["uv_lock"] == "environment/uv.lock"
    assert doc["provenance"]["environment"]["uv_lock_hash"].startswith("sha256:")
    assert "W-ENV-UNLOCKED" not in capsys.readouterr().out


def test_five_seed_repeats_land_in_a_collapsed_layout(tmp_path: Path):
    _, cfg, results = build(tmp_path)
    assert main(["run", str(cfg)]) == EXIT_OK
    run_dir = next(results.glob("run_*"))
    assert not (run_dir / "conditions").exists(), "no sweep means no conditions level"
    repeat_dirs = sorted(p.name for p in run_dir.glob("seed*") if p.is_dir())
    assert len(repeat_dirs) == 5
    doc = yaml.safe_load((run_dir / "run.yaml").read_text())
    per_repeat = doc["results"]["conditions"][0]["per_repeat"]["step01_summarize_units"]
    assert len(per_repeat) == 5
    assert all(v == {"n_units": 2} for v in per_repeat.values())
    # The S1 journey sweeps nothing (no `conditions/` level) but resolves 5 seed
    # repeats (a real repeat level) — `run.yaml`'s recorded layout must say exactly
    # that, per `reference.md` § How artifacts are organized.
    assert doc["layout"] == {"conditions": False, "repeats": True}


def test_run_refuses_a_dirty_code_tree(tmp_path: Path, capsys):
    root, cfg, _ = build(tmp_path)
    (root / "src" / "cohort_pilot" / "experiment.py").write_text("# edited\n")
    assert main(["run", str(cfg)]) == EXIT_WRONG
    # `E-CODE-DIRTY` is rendered through `Collector`, like every other diagnostic —
    # this is what distinguishes the dirty-tree gate from a downstream import failure
    # that would produce the same exit code for a different reason.
    assert "E-CODE-DIRTY" in capsys.readouterr().out


def test_run_refuses_data_inside_the_repo(tmp_path: Path, capsys):
    root, cfg, _ = build(tmp_path)
    doc = yaml.safe_load(cfg.read_text())
    doc["data"]["output_dir"] = str(root / "results")
    cfg.write_text(yaml.safe_dump(doc))
    assert main(["run", str(cfg)]) == EXIT_WRONG
    assert "E-DATA-IN-REPO" in capsys.readouterr().out


def test_run_refuses_an_entrypoint_that_does_not_import(tmp_path: Path, capsys):
    _, cfg, _ = build(tmp_path)
    doc = yaml.safe_load(cfg.read_text())
    doc["entrypoint"] = "cohort_pilot.experiment:NoSuchClass"
    cfg.write_text(yaml.safe_dump(doc))
    # Only `configs/**` changed — `src/**`/`templates/**` stay clean, so this exercises
    # phase 3's entrypoint-import gate specifically, not the dirty-tree gate.
    assert main(["run", str(cfg)]) == EXIT_WRONG
    assert "E-ENTRYPOINT-IMPORT" in capsys.readouterr().err


def test_a_stale_cached_module_does_not_leak_between_same_named_projects(tmp_path: Path):
    """`_load_experiment` purges the entrypoint's root package from `sys.modules` first.

    Two projects here both scaffold a `cohort_pilot` package (`build`'s fixed name).
    Project B's step is hand-edited to return a distinguishable value. If the purge
    were missing, running A first would leave `cohort_pilot.steps.step01_summarize_units`
    cached, and B's run would silently report A's value instead of its own.
    """
    a_dir, b_dir = tmp_path / "a", tmp_path / "b"
    a_dir.mkdir()
    b_dir.mkdir()
    _, cfg_a, _ = build(a_dir)
    root_b, cfg_b, results_b = build(b_dir)

    step_b = root_b / "src" / "cohort_pilot" / "steps" / "step01_summarize_units.py"
    step_b.write_text(
        "from publishable import BaseStep\n\n\n"
        'class Step(BaseStep):\n    scope = "repeat"\n\n'
        "    def run(self, cfg, io):\n"
        '        return {"scaffold_ok": "second-project"}\n'
    )
    subprocess.run(["git", "add", "."], cwd=root_b, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@e.com", "-c", "user.name=t",
         "commit", "-qm", "distinguish"],
        cwd=root_b, check=True,
    )

    assert main(["run", str(cfg_a)]) == EXIT_OK
    assert main(["run", str(cfg_b)]) == EXIT_OK

    run_dir_b = next(results_b.glob("run_*"))
    doc_b = yaml.safe_load((run_dir_b / "run.yaml").read_text())
    per_repeat = doc_b["results"]["conditions"][0]["per_repeat"]["step01_summarize_units"]
    assert all(v == {"scaffold_ok": "second-project"} for v in per_repeat.values())


def test_manifest_drift_mid_run_names_the_changed_path(tmp_path: Path, capsys):
    """`run` builds the input manifest at start and re-verifies it after execution.
    A step that mutates a file under `input_dir` while it runs makes that
    re-verification fail — and the failure must be visible: a diagnostic naming the
    changed path, and the same path recorded in `run.yaml`'s provenance, not a
    `status: failed` run with every execution entry reading `completed` and no clue
    why.
    """
    root, cfg, results = build(tmp_path)
    step_path = root / "src" / "cohort_pilot" / "steps" / "step01_summarize_units.py"
    step_path.write_text(
        "from publishable import BaseStep\n\n\n"
        'class Step(BaseStep):\n    scope = "repeat"\n\n'
        "    def run(self, cfg, io):\n"
        '        (io.input_dir / "index.csv").write_text("patient_id\\np1\\np2\\np3\\n")\n'
        '        return {"scaffold_ok": True}\n'
    )
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@e.com", "-c", "user.name=t",
         "commit", "-qm", "mutate input mid-run"],
        cwd=root, check=True,
    )

    assert main(["run", str(cfg)]) == EXIT_FAILED
    out = capsys.readouterr().out
    assert "E-INPUT-CHANGED" in out
    assert "index.csv" in out

    run_dir = next(results.glob("run_*"))
    doc = yaml.safe_load((run_dir / "run.yaml").read_text())
    assert doc["status"] == "failed"
    assert doc["provenance"]["input_manifest_changed"] == ["index.csv"]
    # Every execution entry still reads "completed" — the drift is a run-level
    # verdict, not a per-execution failure, which is exactly why it needs its own
    # diagnostic and its own recorded reason.
    step_entries = doc["execution"]["conditions"][0]["steps"]["step01_summarize_units"]
    assert all(e["status"] == "completed" for e in step_entries.values())


def build_with_units(tmp_path: Path, n_units: int) -> tuple[Path, Path, Path, Path]:
    """Scaffold a project over an `n_units`-row roster and generate the experiment.

    Returns `(root, cfg_path, results_dir, data_dir)`, uncommitted — so a test can
    replace the starter step before the first commit. Mirrors `build` above, but
    with a roster sized for attrition rather than the fixed two-row one.
    """
    root = tmp_path / "my-study"
    data = tmp_path / "data"
    results = tmp_path / "results"
    data.mkdir()
    rows = "\n".join(f"p{i}" for i in range(n_units))
    (data / "index.csv").write_text(f"patient_id\n{rows}\n")
    assert main(["new", str(root)]) == EXIT_OK
    from publishable.generators.experiment import generate_experiment

    cfg = generate_experiment(
        repo_root=root,
        name="cohort-pilot",
        template_name="generic",
        input_dir=str(data),
        output_dir=str(results),
    )
    doc = yaml.safe_load(cfg.read_text())
    doc["metadata"]["description"] = "the inference base's acceptance run"
    doc["metadata"]["authors"] = ["Kyungjoon Lee"]
    cfg.write_text(yaml.safe_dump(doc))
    return root, cfg, results, data


def write_step(root: Path, *, recorded: int, skipped: int) -> None:
    """Overwrite the generated starter step: the first `recorded` units (in
    roster order) get a deterministic `score`, the next `skipped` are
    `io.skip`ped, and the rest are left untouched entirely — unrecorded, so they
    land in `failed` rather than `ineligible` or `completed`.
    """
    step_path = root / "src" / "cohort_pilot" / "steps" / "step01_summarize_units.py"
    step_path.write_text(
        "from publishable import BaseStep\n\n\n"
        "class Step(BaseStep):\n"
        '    scope = "repeat"\n\n'
        "    def run(self, cfg, io):\n"
        f"        recorded, skipped = {recorded}, {skipped}\n"
        "        for i, unit in enumerate(io.units):\n"
        "            if i < recorded:\n"
        '                io.record(unit.key, {"score": 1.0 + 0.01 * i})\n'
        "            elif i < recorded + skipped:\n"
        '                io.skip(unit.key, "ineligible for this acceptance fixture")\n'
        "        return {}\n"
    )


def commit(root: Path, message: str = "acceptance fixture") -> None:
    for args in (
        ["add", "."],
        ["-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", message],
    ):
        subprocess.run(["git", *args], cwd=root, check=True)


def test_the_inference_base_is_real(tmp_path: Path):
    """240 units resolve, some are skipped, 12 go unrecorded, and n reports what
    actually completed — closing the defect where a `data.units` declaration
    validated and ran without the roster ever reaching the runner.
    """
    root, cfg, results_dir, _ = build_with_units(tmp_path, n_units=240)
    write_step(root, recorded=226, skipped=2)
    commit(root)
    assert main(["run", str(cfg)]) == EXIT_OK

    doc = yaml.safe_load((next(results_dir.glob("run_*")) / "run.yaml").read_text())
    metric = doc["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]["score"]
    counts = metric["n"]
    assert counts["resolved"] == 240
    assert counts["completed"] == 226
    assert counts["ineligible"] == 2
    assert counts["failed"] == 12
    assert counts["resolved"] == counts["completed"] + counts["ineligible"] + counts["failed"]

    assert metric["basis"] == "units"
    assert metric["method"] == "t_over_units"
    low, high = metric["ci95"]
    assert low < metric["value"] < high

    assert doc["provenance"]["units"]["n"] == 240
    assert doc["provenance"]["units"]["key"] == "patient_id"
    assert doc["provenance"]["units_hash"].startswith("sha256:")


def test_the_interval_matches_an_independent_computation(tmp_path: Path):
    """Recompute the interval from `units.parquet` by hand and compare — verifying
    the interval against an independent computation, never against itself.
    """
    root, cfg, results_dir, _ = build_with_units(tmp_path, n_units=40)
    write_step(root, recorded=40, skipped=0)
    commit(root)
    assert main(["run", str(cfg)]) == EXIT_OK
    run_dir = next(results_dir.glob("run_*"))
    doc = yaml.safe_load((run_dir / "run.yaml").read_text())
    metric = doc["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]["score"]

    import pyarrow.parquet as pq

    tables = sorted(run_dir.glob("*/step01_summarize_units/units.parquet"))
    per_unit: dict[str, list[float]] = {}
    for t in tables:
        for row in pq.read_table(t).to_pylist():
            per_unit.setdefault(row["unit"], []).append(row["score"])
    values = [sum(v) / len(v) for v in per_unit.values()]
    n = len(values)
    mean = sum(values) / n
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1))
    from scipy import stats as sp

    half = float(sp.t.ppf(0.975, df=n - 1)) * sd / math.sqrt(n)
    assert metric["value"] == pytest.approx(mean)
    assert metric["ci95"][0] == pytest.approx(mean - half)
    assert metric["ci95"][1] == pytest.approx(mean + half)
