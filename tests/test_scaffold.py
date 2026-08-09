import itertools
import subprocess
from pathlib import Path

import pytest
import yaml

from publishable import ContractError
from publishable.generators.experiment import generate_experiment, package_name
from publishable.generators.step import generate_step
from publishable.scaffold import scaffold_project

_REPO_PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


def test_new_creates_the_fixed_layout_and_a_first_commit(tmp_path: Path):
    root = scaffold_project(tmp_path / "my-study")
    for expected in ("README.md", "CITATION.cff", "LICENSE", "pyproject.toml",
                     ".gitignore", ".env.example"):
        assert (root / expected).is_file(), expected
    for expected in ("src", "templates", "configs", "tests", "docs", ".git"):
        assert (root / expected).exists(), expected
    assert not (root / "data").exists()
    assert not (root / "results").exists()


def test_the_scaffold_gitignores_env_but_says_nothing_about_configs(tmp_path: Path):
    root = scaffold_project(tmp_path / "my-study")
    ignored = (root / ".gitignore").read_text()
    assert ".env" in ignored
    assert "configs/" not in ignored


def test_package_name_converts_the_kebab_config_name(tmp_path: Path):
    assert package_name("cohort-pilot") == "cohort_pilot"


def test_generate_experiment_writes_config_package_and_a_runnable_step(tmp_path: Path):
    root = scaffold_project(tmp_path / "my-study")
    cfg_path = generate_experiment(
        repo_root=root, name="cohort-pilot", template_name="generic",
        input_dir=str(tmp_path / "data"), output_dir=str(tmp_path / "results"),
    )
    assert cfg_path == root / "configs" / "cohort-pilot" / "config.yaml"
    doc = yaml.safe_load(cfg_path.read_text())
    assert doc["metadata"]["name"] == "cohort-pilot"
    assert doc["entrypoint"] == "cohort_pilot.experiment:CohortPilotExperiment"
    pkg = root / "src" / "cohort_pilot"
    assert (pkg / "experiment.py").is_file()
    starter = next((pkg / "steps").glob("step01_*.py"))
    assert "TODO" in starter.read_text()
    assert "BaseStep" in starter.read_text()


def test_generate_step_numbers_the_next_file_and_registers_it(tmp_path: Path):
    root = scaffold_project(tmp_path / "my-study")
    generate_experiment(
        repo_root=root, name="cohort-pilot", template_name="generic",
        input_dir=str(tmp_path / "data"), output_dir=str(tmp_path / "results"),
    )
    path = generate_step(repo_root=root, experiment="cohort-pilot", step_name="analyze")
    assert path.name == "step02_analyze.py"
    experiment_py = (root / "src" / "cohort_pilot" / "experiment.py").read_text()
    assert "step02_analyze" in experiment_py


def test_generate_experiment_refuses_paths_inside_the_repo(tmp_path: Path):
    root = scaffold_project(tmp_path / "my-study")
    with pytest.raises(ContractError) as e:
        generate_experiment(
            repo_root=root, name="cohort-pilot", template_name="generic",
            input_dir=str(root / "data"), output_dir=str(tmp_path / "results"),
        )
    assert e.value.code == "E-DATA-IN-REPO"


def test_generate_step_refuses_a_duplicate_name(tmp_path: Path):
    root = scaffold_project(tmp_path / "my-study")
    generate_experiment(
        repo_root=root, name="cohort-pilot", template_name="generic",
        input_dir=str(tmp_path / "data"), output_dir=str(tmp_path / "results"),
    )
    generate_step(repo_root=root, experiment="cohort-pilot", step_name="analyze")
    experiment_py = root / "src" / "cohort_pilot" / "experiment.py"
    before = experiment_py.read_text()
    steps_dir = root / "src" / "cohort_pilot" / "steps"
    before_files = sorted(p.name for p in steps_dir.glob("step[0-9][0-9]_*.py"))

    with pytest.raises(ContractError) as e:
        generate_step(repo_root=root, experiment="cohort-pilot", step_name="analyze")
    assert e.value.code == "E-STEP-EXISTS"

    after_files = sorted(p.name for p in steps_dir.glob("step[0-9][0-9]_*.py"))
    assert after_files == before_files
    assert experiment_py.read_text() == before


def test_generate_experiment_refuses_to_overwrite_an_existing_package(tmp_path: Path):
    root = scaffold_project(tmp_path / "my-study")
    generate_experiment(
        repo_root=root, name="cohort-pilot", template_name="generic",
        input_dir=str(tmp_path / "data"), output_dir=str(tmp_path / "results"),
    )
    pkg_dir = root / "src" / "cohort_pilot"
    before_experiment_py = (pkg_dir / "experiment.py").read_text()

    with pytest.raises(ContractError) as e:
        generate_experiment(
            repo_root=root, name="cohort-pilot", template_name="generic",
            input_dir=str(tmp_path / "data2"), output_dir=str(tmp_path / "results2"),
        )
    assert e.value.code == "E-EXPERIMENT-EXISTS"
    assert (pkg_dir / "experiment.py").read_text() == before_experiment_py


def test_generate_step_keeps_generated_imports_contiguous(tmp_path: Path):
    root = scaffold_project(tmp_path / "my-study")
    generate_experiment(
        repo_root=root, name="cohort-pilot", template_name="generic",
        input_dir=str(tmp_path / "data"), output_dir=str(tmp_path / "results"),
    )
    generate_step(repo_root=root, experiment="cohort-pilot", step_name="fit_model")
    generate_step(repo_root=root, experiment="cohort-pilot", step_name="analyze")

    experiment_py = root / "src" / "cohort_pilot" / "experiment.py"
    lines = experiment_py.read_text().splitlines()
    import_lines = [i for i, line in enumerate(lines) if line.startswith("from .steps.")]
    assert len(import_lines) == 3
    for earlier, later in itertools.pairwise(import_lines):
        assert later == earlier + 1, "a blank line separates consecutive step imports"

    result = subprocess.run(
        ["uv", "run", "ruff", "check", "--config", str(_REPO_PYPROJECT), "--select", "I001",
         str(experiment_py)],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_new_refuses_a_nonempty_target_but_allows_an_empty_one(tmp_path: Path):
    target = tmp_path / "my-study"
    scaffold_project(target)
    edited = (target / "README.md").read_text() + "\n<!-- my hand edit -->\n"
    (target / "README.md").write_text(edited)

    with pytest.raises(ContractError) as e:
        scaffold_project(target)
    assert e.value.code == "E-PROJECT-EXISTS"
    assert (target / "README.md").read_text() == edited

    empty_target = tmp_path / "empty-study"
    empty_target.mkdir()
    root = scaffold_project(empty_target)
    assert (root / "README.md").is_file()
