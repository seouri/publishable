from pathlib import Path

from publishable.cli import main
from publishable.diagnostics import EXIT_INVOCATION, EXIT_WRONG


def test_an_unknown_command_is_an_invocation_error(capsys):
    assert main(["frobnicate", "x"]) == EXIT_INVOCATION


def test_a_missing_argument_is_an_invocation_error():
    assert main(["run"]) == EXIT_INVOCATION


def test_run_on_a_path_with_no_repo_is_wrong_not_invalid(tmp_path: Path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("schema_version: '1.0'\n")
    assert main(["run", str(cfg)]) == EXIT_WRONG


def test_operation_commands_take_no_flags(capsys):
    assert main(["run", "cfg.yaml", "--allow-dirty"]) == EXIT_INVOCATION


def test_an_unwritable_output_dir_is_a_diagnostic_not_a_traceback(tmp_path: Path, capsys):
    """The ruled-on fix: `run`'s OSError surfaces as `E-IO-FAILED` at exit 1, never a
    bare traceback. `output_dir` existing as a *file* makes `Path.mkdir` raise
    `FileExistsError` (an `OSError` subclass) inside `allocate_run_dir` — the
    simplest way to provoke a real filesystem refusal without touching permissions,
    which don't behave uniformly across CI filesystems.
    """
    import subprocess

    import yaml

    from publishable.generators.experiment import generate_experiment

    root = tmp_path / "proj"
    data = tmp_path / "data"
    data.mkdir()
    (data / "index.csv").write_text("patient_id\np1\n")
    output_as_file = tmp_path / "results-is-a-file"
    output_as_file.write_text("not a directory\n")

    assert main(["new", str(root)]) == 0
    cfg = generate_experiment(
        repo_root=root,
        name="cohort-pilot",
        template_name="generic",
        input_dir=str(data),
        output_dir=str(output_as_file),
    )
    doc = yaml.safe_load(cfg.read_text())
    doc["metadata"]["description"] = "a diagnostic, not a traceback"
    doc["metadata"]["authors"] = ["Kyungjoon Lee"]
    cfg.write_text(yaml.safe_dump(doc))
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "experiment"],
        cwd=root,
        check=True,
    )

    assert main(["run", str(cfg)]) == EXIT_WRONG
    err = capsys.readouterr().err
    assert "E-IO-FAILED" in err
