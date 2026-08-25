import hashlib
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
    for expected in (
        "README.md",
        "CITATION.cff",
        "LICENSE",
        "pyproject.toml",
        ".gitignore",
        ".env.example",
    ):
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
        repo_root=root,
        name="cohort-pilot",
        template_name="generic",
        input_dir=str(tmp_path / "data"),
        output_dir=str(tmp_path / "results"),
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
        repo_root=root,
        name="cohort-pilot",
        template_name="generic",
        input_dir=str(tmp_path / "data"),
        output_dir=str(tmp_path / "results"),
    )
    path = generate_step(repo_root=root, experiment="cohort-pilot", step_name="analyze")
    assert path.name == "step02_analyze.py"
    experiment_py = (root / "src" / "cohort_pilot" / "experiment.py").read_text()
    assert "step02_analyze" in experiment_py


def test_generate_experiment_refuses_paths_inside_the_repo(tmp_path: Path):
    root = scaffold_project(tmp_path / "my-study")
    with pytest.raises(ContractError) as e:
        generate_experiment(
            repo_root=root,
            name="cohort-pilot",
            template_name="generic",
            input_dir=str(root / "data"),
            output_dir=str(tmp_path / "results"),
        )
    assert e.value.code == "E-DATA-IN-REPO"


def test_generate_step_refuses_a_duplicate_name(tmp_path: Path):
    root = scaffold_project(tmp_path / "my-study")
    generate_experiment(
        repo_root=root,
        name="cohort-pilot",
        template_name="generic",
        input_dir=str(tmp_path / "data"),
        output_dir=str(tmp_path / "results"),
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
        repo_root=root,
        name="cohort-pilot",
        template_name="generic",
        input_dir=str(tmp_path / "data"),
        output_dir=str(tmp_path / "results"),
    )
    pkg_dir = root / "src" / "cohort_pilot"
    before_experiment_py = (pkg_dir / "experiment.py").read_text()

    with pytest.raises(ContractError) as e:
        generate_experiment(
            repo_root=root,
            name="cohort-pilot",
            template_name="generic",
            input_dir=str(tmp_path / "data2"),
            output_dir=str(tmp_path / "results2"),
        )
    assert e.value.code == "E-EXPERIMENT-EXISTS"
    assert (pkg_dir / "experiment.py").read_text() == before_experiment_py


def test_generate_step_keeps_generated_imports_contiguous(tmp_path: Path):
    root = scaffold_project(tmp_path / "my-study")
    generate_experiment(
        repo_root=root,
        name="cohort-pilot",
        template_name="generic",
        input_dir=str(tmp_path / "data"),
        output_dir=str(tmp_path / "results"),
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
        [
            "uv",
            "run",
            "ruff",
            "check",
            "--config",
            str(_REPO_PYPROJECT),
            "--select",
            "I001",
            str(experiment_py),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
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


# ---------------------------------------------------------------------------
# H9d guard-pin arm D (design § 8). See the header block at the end of
# `tests/test_cli.py` for the other six arms and their editors.
# ---------------------------------------------------------------------------

_H9D_ARM_D_SCAFFOLD_DIGESTS = {
    ".env.example": "d1855601bdc301556a2733001dd31aa15a4849f97f5dcfd72238c9aa5b071a77",
    ".gitignore": "38678ba27aa0a359ccfb37af76639220d7dce2630fb7bcf682452514f89b74a8",
    "CITATION.cff": "921011172129382a00da3e00e623b7956aa1fa2270aa0d8556f0654d7527386b",
    "LICENSE": "2b548550d33cea762ba2c229c394d8512be0f86fa3ab5f65372f4b6c48fd2552",
    "configs/.gitkeep": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "docs/.gitkeep": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "pyproject.toml": "51ee00b516a6a5d71bdd7cfa0015e13699e0f61d127b5d8000edbc9a0906f08b",
    "src/.gitkeep": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "templates/.gitkeep": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "tests/.gitkeep": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
}


def test_h9d_arm_d_every_scaffolded_file_except_the_readme(tmp_path: Path):
    """H9d guard-pin arm D. **NO AUTHORIZED EDITOR.**

    A `{relative path → sha256}` map of a `publishable new` project's whole
    tree except `README.md`, captured at `f9434bf` by running
    `scaffold_project` into a temporary directory. Its job is Decision 16:
    H9d task 3 moves `README`, `CITATION`, `MIT` and `GITIGNORE` out of
    `scaffold.py`'s module globals into files under `readme_templates/`, and
    that move changes only WHERE the bytes are read from. Every byte this map
    covers must be identical across it, which is a claim no mutation can make
    — the *absence* of a behaviour difference is the thing being asserted —
    so this arm asserts it directly (design § 10, "blind in advance").

    `README.md` is excluded because task 3 deliberately rewrites it (Decision
    9), and `.git/` is excluded because `git init` plus a commit writes index
    and object bytes that are not reproducible between two runs; the map was
    captured twice in one session and compared before the literal was written.

    The project name is fixed at `my-study` — the name `reference.md`
    § The generated README uses — because `CITATION.cff` and `pyproject.toml`
    both interpolate it.
    """
    root = scaffold_project(tmp_path / "my-study")
    seen = {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
        and path.relative_to(root).as_posix() != "README.md"
        and path.relative_to(root).parts[0] != ".git"
    }
    assert seen == _H9D_ARM_D_SCAFFOLD_DIGESTS


# ---------------------------------------------------------------------------
# H9d task 3, move (b): `scaffold.README` becomes what `docs/reference.md`
# § The generated README specifies. Each region's body is asserted BY REGION,
# read back through the same `docs.regions` parser `publishable docs` uses —
# never as a whole-file digest, so a failure names the region that moved.
# ---------------------------------------------------------------------------

_CREDENTIALS_BODY = """\
### Required credentials

| Variable | Needed by |
|---|---|
| _(none yet — added as experiments declare them)_ | |
"""

_EXPERIMENTS_BODY = """\
## Experiments

| Name | Template | Run |
|---|---|---|
| _(none yet — add one with `publishable generate experiment`)_ | | |
"""

_TEMPLATES_BODY = """\
## Templates

_(none yet — add one with `publishable generate template`)_
"""

_REGION_BODIES = {
    "credentials": _CREDENTIALS_BODY,
    "experiments": _EXPERIMENTS_BODY,
    "templates": _TEMPLATES_BODY,
}


def test_the_templates_regions_empty_state_is_what_a_populated_one_degenerates_to(
    tmp_path: Path,
):
    """`reference.md` § Templates renders a populated `templates` region as one
    **sub-section per template** — `### \u0060<name>\u0060`, a convention line, then a
    five-column `parameter_spec` table — so the empty state is a bare line
    under the heading rather than a table header of its own.

    A two-column `Template | Parameters` header here would declare a schema
    the populated form never writes, which is the *declared vs. derived* drift
    the cross-document rule names, and would be a header H9d task 6 has to
    delete before it can write anything.
    """
    from publishable.docs import body_of

    text = (scaffold_project(tmp_path / "my-study") / "README.md").read_text()
    body = body_of(text, "templates")
    assert body.startswith("## Templates\n")
    assert "|---|" not in body
    assert "_(none yet — add one with `publishable generate template`)_" in body


def test_the_scaffolded_readme_declares_all_four_managed_regions(tmp_path: Path):
    """Before this slice it declared two (`overview`, `experiments`), which is
    a documented surface of `new` that `new` did not write. Parsed rather than
    grepped: `docs.regions` is what `publishable docs` will read this file
    with, so a README whose markers a substring check finds and the parser
    does not is caught here."""
    from publishable.docs import MANAGED_REGIONS, regions

    root = scaffold_project(tmp_path / "my-study")
    assert set(regions((root / "README.md").read_text())) == set(MANAGED_REGIONS)


@pytest.mark.parametrize("name", sorted(_REGION_BODIES))
def test_each_scaffolded_region_body_is_what_the_document_specifies(name: str, tmp_path: Path):
    """One assertion per region, on the body BETWEEN the markers, so a change
    inside one region fails a test that names it rather than a whole-file
    pin that names the file."""
    from publishable.docs import body_of

    root = scaffold_project(tmp_path / "my-study")
    assert body_of((root / "README.md").read_text(), name) == _REGION_BODIES[name]


def test_the_experiments_heading_moved_inside_its_own_region(tmp_path: Path):
    """§ The generated README puts `## Experiments` INSIDE the region, so the
    generator that writes the table owns the heading too. It used to sit
    above the `begin` marker with prose inside — which meant a region whose
    body a generator replaced would leave a heading nothing owned.

    Both halves: the heading is inside the span, and the pre-slice prose line
    is gone."""
    from publishable.docs import body_of, regions

    text = (scaffold_project(tmp_path / "my-study") / "README.md").read_text()
    start, _ = regions(text)["experiments"]
    lines = text.split("\n")
    assert lines[start] == "## Experiments"
    assert "## Experiments" in body_of(text, "experiments")
    assert "None yet. Create one with" not in text


def test_the_scaffolded_readme_carries_the_setup_and_reproduce_lines(tmp_path: Path):
    """The two documented lines that live OUTSIDE every region — hand-written
    prose as far as `docs` is concerned, and therefore `new`'s only chance to
    write them."""
    from publishable.docs import regions

    text = (scaffold_project(tmp_path / "my-study") / "README.md").read_text()
    assert "cp .env.example .env    # then fill in the values below" in text
    assert "## Reproducing a published result" in text
    assert "uv run --with publishable publishable reproduce run.yaml" in text
    # Outside every region, asserted structurally rather than by eye: no
    # region's span may contain either line, so `docs` can never rewrite them.
    lines = text.split("\n")
    inside = {index for start, stop in regions(text).values() for index in range(start, stop)}
    for index, line in enumerate(lines):
        if "cp .env.example .env" in line or line == "## Reproducing a published result":
            assert index not in inside, line


def test_the_scaffolds_are_read_from_files_rather_than_module_globals(tmp_path: Path):
    """Decision 16, asserted where it is observable: the four scaffolds are
    files under `publishable/readme_templates/`, and `scaffold_project` reads
    them. The behavioural half is guard-pin arm D above — every other
    scaffolded byte is unchanged by the move — and this is the structural
    half, which arm D cannot see because it hashes the OUTPUT.
    """
    from publishable.scaffold import read_scaffold

    for filename in (
        "README.md.tmpl",
        "CITATION.cff.tmpl",
        "LICENSE.mit.tmpl",
        "gitignore.tmpl",
    ):
        assert read_scaffold(filename), filename
    root = scaffold_project(tmp_path / "my-study")
    assert (root / ".gitignore").read_text() == read_scaffold("gitignore.tmpl")
    assert (root / "LICENSE").read_text() == read_scaffold("LICENSE.mit.tmpl")
    assert (root / "README.md").read_text() == read_scaffold("README.md.tmpl").format(
        name="my-study"
    )


def test_the_scaffolded_gitignore_still_says_nothing_about_demo_progress(tmp_path: Path):
    """Decision 9's other half, and it is a refusal to change something:
    `.demo-progress` is `demo`'s file, appended to the demo repository's own
    `.gitignore` after `scaffold_project` returns. Putting it in the shipped
    constant would put a line about a file `demo` invents into every
    `publishable new` project forever — the *widening a behaviour change to
    make a document self-consistent* fault. The documented sentence is what
    moves, and task 14 moves it."""
    root = scaffold_project(tmp_path / "my-study")
    ignored = (root / ".gitignore").read_text()
    assert ".demo-progress" not in ignored
    assert ".env" in ignored and "__pycache__/" in ignored
