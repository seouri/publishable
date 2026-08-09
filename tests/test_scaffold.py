from pathlib import Path

import yaml

from publishable.generators.experiment import generate_experiment, package_name
from publishable.generators.step import generate_step
from publishable.scaffold import scaffold_project


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
    import pytest

    from publishable import ContractError

    with pytest.raises(ContractError) as e:
        generate_experiment(
            repo_root=root, name="cohort-pilot", template_name="generic",
            input_dir=str(root / "data"), output_dir=str(tmp_path / "results"),
        )
    assert e.value.code == "E-DATA-IN-REPO"
