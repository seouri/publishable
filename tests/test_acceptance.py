"""S1's whole promise: `reference.md` § The starter step runs."""

import math
import subprocess
from pathlib import Path

import pytest
import yaml

from publishable.cli import main
from publishable.diagnostics import EXIT_FAILED, EXIT_OK, EXIT_PARTIAL, EXIT_WRONG


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

    assert doc["provenance"]["publishable_version"] == importlib.metadata.version("publishable")

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

    # H8b Decision 7: `run` also writes `<run_dir>/config.yaml` (the config as it
    # was) and `environment/repo_root.txt` (the repo it came from) — the two
    # facts a mid-run command cannot otherwise obtain, and what `freeze` needs.
    assert (run_dir / "environment" / "repo_root.txt").read_text().strip() == str(root.resolve())
    config_copy = yaml.safe_load((run_dir / "config.yaml").read_text())
    assert config_copy["experiment_type"] == doc["config"]["experiment_type"]


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


def test_the_starter_step_publishes_a_real_metric(tmp_path: Path):
    """Whole-project review C1. The scaffold exists to demonstrate the loop, and
    the loop's product is an interval — so what it publishes is asserted key by
    key, not counted. The pre-fix step recorded `{"present": True}`, a bool
    column, which by H5b's rule earns no metric block: `aggregated` for this
    step was `{}` at exit 0 with no diagnostic anywhere.
    """
    _, cfg, results = build(tmp_path)
    assert main(["run", str(cfg)]) == EXIT_OK
    doc = yaml.safe_load((next(results.glob("run_*")) / "run.yaml").read_text())
    step = doc["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]
    entry = step["placeholder_score"]
    assert entry["basis"] == "units"
    assert entry["method"] == "t_over_units"
    assert entry["n"] == {"resolved": 2, "completed": 2, "ineligible": 0, "failed": 0}
    low, high = entry["ci95"]
    assert low < entry["value"] < high
    # A draw per repeat, so the five seed repeats disagree: `repeat_spread` is
    # the half of the block a bool column could never have produced either.
    assert entry["repeat_spread"]["kind"] == "seed"
    assert entry["repeat_spread"]["n"] == 5
    assert entry["repeat_spread"]["std"] > 0.0


def test_the_starter_steps_todo_sits_on_the_line_that_decides_the_metric(tmp_path: Path):
    """C1's third cause: the one `TODO` sat on the `return`, while the reason a
    first run published nothing was the `io.record` line above it.
    """
    root, _, _ = build(tmp_path)
    lines = (root / "src" / "cohort_pilot" / "steps" / "step01_summarize_units.py").read_text()
    lines = lines.splitlines()
    todo = next(i for i, line in enumerate(lines) if "TODO" in line)
    record = next(i for i, line in enumerate(lines) if "io.record(" in line)
    returned = next(i for i, line in enumerate(lines) if line.strip().startswith("return "))
    assert todo < record < returned
    assert "TODO" not in lines[returned]


def test_run_refuses_a_dirty_code_tree(tmp_path: Path, capsys):
    root, cfg, _ = build(tmp_path)
    # Appended, not overwritten: the edit must dirty `src/**` while leaving the
    # entrypoint importable. `validate` now imports it, and it runs before this
    # gate, so an edit that also broke the import would be caught as
    # `E-ENTRYPOINT-IMPORT` first and never reach the dirty-tree gate at all.
    experiment_py = root / "src" / "cohort_pilot" / "experiment.py"
    experiment_py.write_text(experiment_py.read_text() + "\n# edited\n")
    assert main(["run", str(cfg)]) == EXIT_WRONG
    # `E-CODE-DIRTY` is rendered through `Collector`, like every other diagnostic —
    # this is what distinguishes the dirty-tree gate from a downstream import failure
    # that would produce the same exit code for a different reason.
    assert "E-CODE-DIRTY" in capsys.readouterr().out


def test_run_refuses_an_untracked_file_a_global_exclude_hides(tmp_path: Path, capsys, monkeypatch):
    """H6a whole-branch fix round, Ruling L, end to end through `run`.

    The convergence `reference.md`'s `E-CODE-DIRTY` row claims lives in a run,
    so it is asserted in one — the two `git_provenance` arms in
    `tests/test_hashes.py` hold the same property at the seam.

    **Both arms use the same file and the same pattern, and differ only in
    where the rule lives**, which is what attributes the refusal to the rule
    rather than to the file. Committed in the repo's own `.gitignore`, the
    run proceeds; moved out of the tree into a machine's global
    `core.excludesFile`, the same tree is refused — because that file is
    untracked, ignored by nothing a clone would carry, and folded into
    `code_hash` regardless (Ruling F). A gate that could not see it would let
    a run publish an identity claim over a file no clone of the commit holds.
    """
    root, cfg, _ = build(tmp_path)
    pkg_note = root / "src" / "cohort_pilot" / "notes.log"

    gitignore = root / ".gitignore"
    gitignore.write_text(gitignore.read_text() + "notes.log\n")
    for args in (
        ["add", ".gitignore"],
        ["-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "ignore notes"],
    ):
        subprocess.run(["git", *args], cwd=root, check=True)
    pkg_note.write_text("machine chatter\n")
    assert main(["run", str(cfg)]) == EXIT_OK
    assert "E-CODE-DIRTY" not in capsys.readouterr().out

    # The identical rule, moved off the tree and onto the machine.
    gitignore.write_text(gitignore.read_text().replace("notes.log\n", ""))
    for args in (
        ["add", ".gitignore"],
        ["-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "unignore notes"],
    ):
        subprocess.run(["git", *args], cwd=root, check=True)
    excludes = tmp_path / "machine_excludes"
    excludes.write_text("notes.log\n")
    machine_config = tmp_path / "machine_gitconfig"
    machine_config.write_text(f"[core]\n\texcludesFile = {excludes}\n")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(machine_config))
    asked = subprocess.run(
        ["git", "check-ignore", "src/cohort_pilot/notes.log"], cwd=root, capture_output=True
    )
    assert asked.returncode == 0, "the fixture's global exclude must be one git really reads"

    assert main(["run", str(cfg)]) == EXIT_WRONG
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
    # the entrypoint-import gate specifically, not the dirty-tree gate. `validate` now
    # imports the entrypoint, so the refusal arrives as a collected finding on stdout
    # rather than as a raised `ContractError` printed to stderr.
    assert main(["run", str(cfg)]) == EXIT_WRONG
    assert "E-ENTRYPOINT-IMPORT" in capsys.readouterr().out


def test_a_stale_cached_module_does_not_leak_between_same_named_projects(tmp_path: Path):
    """`load_experiment` purges the entrypoint's root package from `sys.modules` first.

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
        ["git", "-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "distinguish"],
        cwd=root_b,
        check=True,
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
        [
            "git",
            "-c",
            "user.email=t@e.com",
            "-c",
            "user.name=t",
            "commit",
            "-qm",
            "mutate input mid-run",
        ],
        cwd=root,
        check=True,
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


def write_sweep_step(root: Path) -> None:
    """Overwrite the starter step with one whose recorded `score` depends on
    `cfg.parameters.analysis.method` — so the three conditions a sweep over that
    axis produces genuinely differ, not just in label.
    """
    step_path = root / "src" / "cohort_pilot" / "steps" / "step01_summarize_units.py"
    step_path.write_text(
        "from publishable import BaseStep\n\n\n"
        "class Step(BaseStep):\n"
        '    scope = "repeat"\n\n'
        "    def run(self, cfg, io):\n"
        '        by_method = {"pearson": 1.0, "spearman": 2.0, "kendall": 3.0}\n'
        "        score = by_method[cfg.parameters.analysis.method]\n"
        "        for unit in io.units:\n"
        '            io.record(unit.key, {"score": score})\n'
        "        return {}\n"
    )


def build_sweep_project(tmp_path: Path, n_units: int) -> tuple[Path, Path, Path]:
    """A project swept over `analysis.method`: a declared baseline (pearson) plus
    a grid of the other two — 3 conditions × 5 seed repeats over one shared roster.
    """
    root, cfg, results_dir, _ = build_with_units(tmp_path, n_units)
    write_sweep_step(root)
    doc = yaml.safe_load(cfg.read_text())
    doc["sweep"] = {
        "baseline": {"analysis.method": "pearson"},
        "grid": {"analysis.method": ["spearman", "kendall"]},
    }
    cfg.write_text(yaml.safe_dump(doc))
    commit(root, "declare the sweep")
    return root, cfg, results_dir


def build_project_without_sweep(tmp_path: Path, n_units: int) -> tuple[Path, Path, Path]:
    """The regression baseline: no `sweep` block at all, so `expand` resolves the
    single unlabeled condition and no `conditions/` level should appear.
    """
    root, cfg, results_dir, _ = build_with_units(tmp_path, n_units)
    commit(root, "no sweep")
    return root, cfg, results_dir


def test_a_sweep_runs_every_condition_over_one_roster(tmp_path: Path):
    """3 conditions × 5 seed repeats = 15 executions, in the right tree."""
    root, cfg, results_dir = build_sweep_project(tmp_path, n_units=240)
    assert main(["run", str(cfg)]) == EXIT_OK

    run_dir = next(results_dir.glob("run_*"))
    doc = yaml.safe_load((run_dir / "run.yaml").read_text())

    conds = doc["results"]["conditions"]
    assert [c["label"] for c in conds] == ["baseline", "method=spearman", "method=kendall"]
    assert conds[0]["is_baseline"] is True

    # the tree: a conditions/ level, five repeat dirs under each
    labels = sorted(p.name for p in (run_dir / "conditions").iterdir())
    assert labels == ["00_baseline", "01_method=spearman", "02_method=kendall"]
    for label in labels:
        seeds = [p for p in (run_dir / "conditions" / label).iterdir() if p.is_dir()]
        assert len(seeds) == 5, label

    lines = (run_dir / "executions.jsonl").read_text().splitlines()
    assert len(lines) == 15


def test_each_condition_reports_its_own_numbers(tmp_path: Path):
    """The headline test: two conditions must not share an aggregated block."""
    root, cfg, results_dir = build_sweep_project(tmp_path, n_units=240)
    assert main(["run", str(cfg)]) == EXIT_OK
    doc = yaml.safe_load((next(results_dir.glob("run_*")) / "run.yaml").read_text())

    blocks = [
        c["aggregated"]["step01_summarize_units"]["score"] for c in doc["results"]["conditions"]
    ]
    values = [b["value"] for b in blocks]
    assert len(set(values)) == 3, f"conditions must differ, got {values}"
    assert blocks[0] is not blocks[1], "aggregated must not be a shared object"
    for b in blocks:
        assert b["basis"] == "units"
        assert b["correction"] is None, "an uncorrected interval must say so"
        assert b["n"]["resolved"] == 240


def test_sweep_yaml_records_the_resolved_plan(tmp_path: Path):
    root, cfg, results_dir = build_sweep_project(tmp_path, n_units=40)
    assert main(["run", str(cfg)]) == EXIT_OK
    sweep_doc = yaml.safe_load((next(results_dir.glob("run_*")) / "sweep.yaml").read_text())
    assert [c["label"] for c in sweep_doc["conditions"]] == [
        "baseline",
        "method=spearman",
        "method=kendall",
    ]
    # `repeats` groups by kind (only `seed` exists yet), so one entry whose
    # `seeds` list carries all five — not five entries. See `sweep.sweep_document`.
    assert len(sweep_doc["repeats"]) == 1
    assert len(sweep_doc["repeats"][0]["seeds"]) == 5
    assert len(sweep_doc["execution_order"]) == 15


def test_a_single_condition_run_is_unchanged(tmp_path: Path):
    """The regression risk of adding a level is that it appears where it should not."""
    root, cfg, results_dir = build_project_without_sweep(tmp_path, n_units=40)
    assert main(["run", str(cfg)]) == EXIT_OK
    run_dir = next(results_dir.glob("run_*"))
    assert not (run_dir / "conditions").exists()


def test_a_summary_step_reading_a_swept_parameter_is_refused_in_a_real_run(tmp_path: Path):
    """`resolve_wide_cfg` plants `SweptAway` for every swept path in the config the
    `run`/`summary`-scoped cfg is built from — proved here through an actual `run`,
    not only by calling `execute_plan` directly with a hand-built `cfgs`.
    """
    from publishable.generators.step import generate_step

    root, cfg, results_dir, _ = build_with_units(tmp_path, n_units=40)
    write_sweep_step(root)
    generate_step(repo_root=root, experiment="cohort-pilot", step_name="check_swept")
    step_path = root / "src" / "cohort_pilot" / "steps" / "step02_check_swept.py"
    step_path.write_text(
        "from publishable import BaseStep\n\n\n"
        "class Step(BaseStep):\n"
        '    scope = "summary"\n\n'
        "    def run(self, cfg, io):\n"
        '        return {"method": cfg.parameters.analysis.method}\n'
    )
    doc = yaml.safe_load(cfg.read_text())
    doc["sweep"] = {
        "baseline": {"analysis.method": "pearson"},
        "grid": {"analysis.method": ["spearman", "kendall"]},
    }
    cfg.write_text(yaml.safe_dump(doc))
    commit(root, "add a summary step that reads the swept parameter")

    assert main(["run", str(cfg)]) == EXIT_PARTIAL
    run_dir = next(results_dir.glob("run_*"))
    run_doc = yaml.safe_load((run_dir / "run.yaml").read_text())
    assert run_doc["status"] == "partial"
    error = run_doc["execution"]["summary"]["step02_check_swept"]["error"]
    assert "E-STEP-SWEPT-PARAM" in error


def test_a_summary_step_reads_every_condition_in_a_real_run(tmp_path: Path):
    """`io.conditions`/`io.read_condition` are wired through `runner.execute_plan`'s
    `StepIO` construction — proved here by a `summary`-scoped step that actually
    reads each condition's own `step01_summarize_units` output back, in a real run.
    """
    from publishable.generators.step import generate_step

    root, cfg, results_dir, _ = build_with_units(tmp_path, n_units=40)
    write_sweep_step(root)
    generate_step(repo_root=root, experiment="cohort-pilot", step_name="compare_conditions")
    step_path = root / "src" / "cohort_pilot" / "steps" / "step02_compare_conditions.py"
    step_path.write_text(
        "from publishable import BaseStep\n\n\n"
        "class Step(BaseStep):\n"
        '    scope = "summary"\n\n'
        "    def run(self, cfg, io):\n"
        "        seen = {}\n"
        "        for condition in io.conditions:\n"
        "            table = io.read_condition(\n"
        '                condition, "step01_summarize_units", "units.parquet",\n'
        "                repeat=io.repeats[0],\n"
        "            )\n"
        '            seen[condition[1]] = table[0]["score"]\n'
        "        return seen\n"
    )
    doc = yaml.safe_load(cfg.read_text())
    doc["sweep"] = {
        "baseline": {"analysis.method": "pearson"},
        "grid": {"analysis.method": ["spearman", "kendall"]},
    }
    cfg.write_text(yaml.safe_dump(doc))
    commit(root, "add a summary step that reads across conditions")

    assert main(["run", str(cfg)]) == EXIT_OK
    run_doc = yaml.safe_load((next(results_dir.glob("run_*")) / "run.yaml").read_text())
    seen = run_doc["results"]["summary"]["step02_compare_conditions"]
    assert seen == {"baseline": 1.0, "method=spearman": 2.0, "method=kendall": 3.0}


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


def test_a_run_scoped_step_reading_a_baseline_only_path_is_refused(tmp_path: Path):
    """`swept_paths` is every path any condition fixes, not just the grid's axes.
    A path fixed by `sweep.baseline` and absent from `sweep.grid` still varies
    across conditions — `00_baseline` uses the baseline's value and every other
    condition the base config's — so at `run`/`summary` scope it must be
    unreadable. Reading the grid alone let a `run`-scoped step resolve it to the
    base value, which is a value *no condition in the run used*, and the run
    exited 0 with `status: completed`.
    """
    from publishable.generators.step import generate_step

    root, cfg, results_dir, _ = build_with_units(tmp_path, n_units=40)
    write_sweep_step(root)
    generate_step(repo_root=root, experiment="cohort-pilot", step_name="read_baseline_only")
    step_path = root / "src" / "cohort_pilot" / "steps" / "step02_read_baseline_only.py"
    step_path.write_text(
        "from publishable import BaseStep\n\n\n"
        "class Step(BaseStep):\n"
        '    scope = "run"\n\n'
        "    def run(self, cfg, io):\n"
        '        return {"seen": cfg.parameters.analysis.method}\n'
    )
    doc = yaml.safe_load(cfg.read_text())
    # The baseline fixes both axes (so this is not the partial-baseline case);
    # `analysis.method` is fixed by the baseline alone and never by the grid.
    doc["sweep"] = {
        "baseline": {"analysis.method": "pearson", "analysis.min_samples": 10},
        "grid": {"analysis.min_samples": [10, 20]},
    }
    cfg.write_text(yaml.safe_dump(doc))
    commit(root, "add a run-scoped step reading a baseline-only path")

    assert main(["run", str(cfg)]) == EXIT_PARTIAL
    run_doc = yaml.safe_load((next(results_dir.glob("run_*")) / "run.yaml").read_text())
    assert run_doc["status"] == "partial"
    error = run_doc["execution"]["shared"]["step02_read_baseline_only"]["error"]
    assert "E-STEP-SWEPT-PARAM" in error


def test_sweep_yaml_is_written_before_the_first_execution(tmp_path: Path, monkeypatch):
    """`reference.md` § The other files a run writes: `sweep.yaml` is "settled
    before the first execution and never touched again", and `resume` reads it
    back rather than re-deriving it. Written after `execute_plan`, a run that died
    inside the loop — `E-RUN-CFG-MISSING`, `E-RUN-SEED-MISSING`, both deliberately
    outside the per-execution `try` — left a run directory with no plan at all.

    The fatal is injected rather than induced: neither raise is reachable through
    `command_run` (`cfgs` is built from the same `conditions` the plan is), so the
    ordering is what is under test, not the specific fatal.
    """
    import publishable.cli as cli_module

    root, cfg, results_dir = build_sweep_project(tmp_path, n_units=40)

    def boom(**kwargs):
        raise RuntimeError("died inside the execution loop")

    monkeypatch.setattr(cli_module, "execute_plan", boom)
    with pytest.raises(RuntimeError):
        main(["run", str(cfg)])

    run_dir = next(results_dir.glob("run_*"))
    sweep_doc = yaml.safe_load((run_dir / "sweep.yaml").read_text())
    assert [c["label"] for c in sweep_doc["conditions"]] == [
        "baseline",
        "method=spearman",
        "method=kendall",
    ]
    assert len(sweep_doc["execution_order"]) == 15


def test_run_yaml_records_what_each_condition_varied(tmp_path: Path):
    """`reference.md`:393 and § Statistical reporting both show `values` on the
    condition entry. `run.yaml` is the file a paper attaches, so a reader of it
    alone must be able to say what each condition varied without opening
    `sweep.yaml`, which the document positions as the plan rather than the record.
    """
    root, cfg, results_dir = build_sweep_project(tmp_path, n_units=40)
    assert main(["run", str(cfg)]) == EXIT_OK
    run_doc = yaml.safe_load((next(results_dir.glob("run_*")) / "run.yaml").read_text())
    conditions = run_doc["results"]["conditions"]
    assert [c["values"] for c in conditions] == [
        {"analysis.method": "pearson"},
        {"analysis.method": "spearman"},
        {"analysis.method": "kendall"},
    ]
    assert [c["is_baseline"] for c in conditions] == [True, False, False]


def test_a_run_imports_the_entrypoint_once(tmp_path: Path):
    """`validate` imports the entrypoint now, and so does `run`. `command_run` loads it
    first and hands it to `validate_config`, so user code is imported once per run —
    a module with an expensive or side-effecting import must not pay twice."""
    root, cfg, _ = build(tmp_path)
    tally = tmp_path / "imports.log"  # outside the repo, so `src/**` stays clean
    experiment_py = root / "src" / "cohort_pilot" / "experiment.py"
    experiment_py.write_text(
        experiment_py.read_text()
        + f'\nwith open({str(tally)!r}, "a") as _f:\n    _f.write("imported\\n")\n'
    )
    for args in (
        ["add", "."],
        ["-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "tally"],
    ):
        subprocess.run(["git", *args], cwd=root, check=True)

    assert main(["run", str(cfg)]) == EXIT_OK
    assert tally.read_text().count("imported") == 1
