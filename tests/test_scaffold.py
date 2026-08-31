import hashlib
import itertools
import re
import subprocess
import tomllib
from pathlib import Path

import pytest
import yaml

from publishable import ContractError
from publishable.generators.experiment import generate_experiment, package_name
from publishable.generators.step import generate_step
from publishable.scaffold import scaffold_project

_REPO_ROOT = Path(__file__).resolve().parents[1]
_REPO_PYPROJECT = _REPO_ROOT / "pyproject.toml"
_REFERENCE_MD = _REPO_ROOT / "docs" / "reference.md"
_TUTORIAL_MD = _REPO_ROOT / "docs" / "tutorial-writing-a-plugin.md"

# The tutorial is NOT in the sdist: `[tool.hatch.build.targets.sdist]` ships the
# three normative documents and not this one. So the three pins below cannot
# read their subject from an unpacked tarball, where they fail with
# `FileNotFoundError` — measured on 2026-08-29, three of the five failures a
# tests-carrying sdist produces.
#
# **The condition is the absence AND the tree not being a checkout**, not the
# absence alone. A bare `skipif(not exists)` fails open in the direction that
# matters: delete or rename the tutorial in this repository and three pins would
# go quietly green, which is the whole failure mode `_tutorial_fence` already
# guards against inside the file. With `.git` in the condition, a missing
# tutorial in a checkout still runs these tests and still fails loudly; only a
# distribution, which is not a git repository and is not supposed to carry the
# file, skips them.
_needs_the_tutorial = pytest.mark.skipif(
    not _TUTORIAL_MD.exists() and not (_REPO_ROOT / ".git").exists(),
    reason="the tutorial is not shipped in the sdist; in a checkout its absence is a failure",
)


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


def test_generate_step_refuses_a_name_that_cannot_be_an_identifier(tmp_path: Path):
    """The name lands in an import path and a class name, and neither position
    can be escaped: a value that is not an identifier makes `experiment.py`
    unparseable, and `experiment.py` is a file this command did not create.

    **Both halves are asserted, and the second is the one that matters.**
    Refusing after the step file is written would still leave a stray module;
    refusing after the rewrite would leave a project that does not import. The
    check has to run before anything reaches disk, so the test reads the
    directory and the file rather than only the exception.
    """
    root = scaffold_project(tmp_path / "my-study")
    generate_experiment(
        repo_root=root,
        name="cohort-pilot",
        template_name="generic",
        input_dir=str(tmp_path / "data"),
        output_dir=str(tmp_path / "results"),
    )
    experiment_py = root / "src" / "cohort_pilot" / "experiment.py"
    before = experiment_py.read_text()
    steps_dir = root / "src" / "cohort_pilot" / "steps"
    before_files = sorted(p.name for p in steps_dir.glob("step[0-9][0-9]_*.py"))

    with pytest.raises(ContractError) as e:
        generate_step(repo_root=root, experiment="cohort-pilot", step_name='foo"bar')
    assert e.value.code == "E-GENERATE-NAME"

    assert experiment_py.read_text() == before, "the rewrite reached a file it did not create"
    assert sorted(p.name for p in steps_dir.glob("step[0-9][0-9]_*.py")) == before_files
    # And the file still parses, which is the fault this guard exists to
    # prevent — an unchanged-bytes assertion alone would pass on a rewrite that
    # happened to be reverted rather than never made.
    compile(experiment_py.read_text(), str(experiment_py), "exec")


@pytest.mark.parametrize("step_name", ['foo"bar', "fit-model", "with space", "a/b", "__dunder"])
def test_generate_step_refuses_every_name_that_would_not_import(tmp_path: Path, step_name: str):
    """One shape per way the old interpolation broke: a quote, a hyphen, a
    space, a path separator, and the `__` prefix discovery skips."""
    root = scaffold_project(tmp_path / "my-study")
    generate_experiment(
        repo_root=root,
        name="cohort-pilot",
        template_name="generic",
        input_dir=str(tmp_path / "data"),
        output_dir=str(tmp_path / "results"),
    )
    with pytest.raises(ContractError) as e:
        generate_step(repo_root=root, experiment="cohort-pilot", step_name=step_name)
    assert e.value.code == "E-GENERATE-NAME"


def test_generate_experiment_refuses_a_name_that_cannot_be_a_package(tmp_path: Path):
    """`src/<pkg>/` has to be importable, and the class name has to parse. The
    damage here is bounded — every file this command writes is one it creates —
    but the root cause is the step generator's, and a project scaffolded into
    `src/foo"bar/` is unusable at exit 0, which is the same silence."""
    root = scaffold_project(tmp_path / "my-study")
    with pytest.raises(ContractError) as e:
        generate_experiment(
            repo_root=root,
            name='foo"bar',
            template_name="generic",
            input_dir=str(tmp_path / "data"),
            output_dir=str(tmp_path / "results"),
        )
    assert e.value.code == "E-GENERATE-NAME"
    assert not (root / "configs" / 'foo"bar').exists()
    assert not (root / "src" / 'foo"bar').exists()


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

    **NARROWED 2026-08-27, and the narrowing is the arm working rather than the
    arm failing.** `pyproject.toml` left this map when `scaffold.PYPROJECT`
    gained `[tool.uv] package = false` — the fix for *a scaffolded project
    cannot be built by `uv`*, without which every `uv run publishable ...` in a
    fresh project failed. The hash was NOT refreshed, because a digest over a
    file whose content is a **behaviour** slices change is a proxy that fires
    whenever the scaffold legitimately moves, which is H9d arm C's own lesson
    one file over; and this arm's job — proving task 3's move of four scaffolds
    into `readme_templates/` changed no byte — is discharged and cannot recur,
    `pyproject.toml` never having been one of the four. The nine entries that
    remain are files that should not move, for which a digest IS the direct
    question. What replaced it is the direct question for this file too:
    `test_the_scaffolded_pyproject_declares_the_project_unbuildable` below,
    which reads the declaration rather than the bytes around it.

    The project name is fixed at `my-study` — the name `reference.md`
    § The generated README uses — because `CITATION.cff` and `pyproject.toml`
    both interpolate it.
    """
    root = scaffold_project(tmp_path / "my-study")
    seen = {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
        and path.relative_to(root).as_posix() not in ("README.md", "pyproject.toml")
        and path.relative_to(root).parts[0] != ".git"
    }
    assert seen == _H9D_ARM_D_SCAFFOLD_DIGESTS


def test_the_scaffolded_pyproject_declares_the_project_unbuildable(tmp_path: Path):
    """`[tool.uv] package = false`, without which `uv` tries to build the project
    it is asked to run in and hatchling finds no package matching the
    distribution name — `src/` holds a `.gitkeep` and `generate experiment`
    writes `src/<experiment>/`, never `src/<project>/`.

    Parsed rather than grepped, so a line inside a string or a comment cannot
    satisfy it, and asserted as the resolved value rather than as the presence of
    a key: `package = true` would pass a `"[tool.uv]" in text` check while
    restoring the failure exactly.
    """
    root = scaffold_project(tmp_path / "my-study")
    declared = tomllib.loads((root / "pyproject.toml").read_text())
    assert declared.get("tool", {}).get("uv", {}).get("package") is False, (
        "`[tool.uv] package = false` is absent, so `uv` will try to build this "
        "project and hatchling will find no package matching its name"
    )
    # The other half, and the reason this key is needed at all: nothing in the
    # scaffold gives hatchling a package to find, and no generator adds one.
    assert not (root / "src" / "my_study").exists()
    assert [p.name for p in (root / "src").iterdir()] == [".gitkeep"]


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


def test_new_prints_what_it_created_and_the_next_command(tmp_path: Path, capsys):
    """Whole-project review, Minor: `new` printed zero bytes at exit 0.

    The printed path is asserted to be one that exists and holds the scaffold,
    not merely to appear — a line naming a path nothing wrote is the failure
    this fix would otherwise trade for silence.
    """
    from publishable.cli import main

    root = tmp_path / "my-study"
    assert main(["new", str(root)]) == 0
    out = capsys.readouterr().out
    assert f"project → {root}" in out
    assert (root / "pyproject.toml").is_file()
    next_line = next(line for line in out.splitlines() if line.startswith("next: "))
    assert f"cd {root}" in next_line
    # The command it names has to be one the CLI dispatches, not a name from
    # the roadmap: `generate` is a built branch, and this reads the mapping
    # rather than a literal so a command that becomes unbuilt fails here.
    from publishable.cli import NOT_BUILT_COMMANDS

    assert "generate experiment" in next_line
    assert "generate" not in NOT_BUILT_COMMANDS


def test_generate_experiment_prints_its_paths_and_a_next_command_that_works(
    tmp_path: Path, capsys, monkeypatch
):
    """The other half of that Minor, and the `next:` line is RUN rather than
    matched: a printed next command that does not dispatch is worse than none.

    It is run twice, because the honest answer has two halves. On the config as
    generated it exits `1` naming the two `metadata` fields `init` deliberately
    leaves empty — `validate` doing its job, which is why `next:` points at it —
    and with those two filled the same invocation exits `0`.
    """
    from publishable.cli import main

    root = scaffold_project(tmp_path / "my-study")
    data = tmp_path / "data"
    data.mkdir()
    (data / "index.csv").write_text("patient_id\np1\np2\n")
    monkeypatch.chdir(root)
    capsys.readouterr()
    assert (
        main(
            [
                "generate",
                "experiment",
                "cohort-pilot",
                "--template",
                "generic",
                "--input-dir",
                str(data),
                "--output-dir",
                str(tmp_path / "results"),
            ]
        )
        == 0
    )
    out = capsys.readouterr().out
    config = root / "configs" / "cohort-pilot" / "config.yaml"
    step = root / "src" / "cohort_pilot" / "steps" / "step01_summarize_units.py"
    assert f"config → {config}" in out
    assert f"step   → {step}" in out
    assert config.is_file() and step.is_file()
    next_line = next(line for line in out.splitlines() if line.startswith("next: "))
    assert next_line == f"next: uv run publishable validate {config}"
    argv = next_line.removeprefix("next: uv run publishable ").split()
    capsys.readouterr()
    assert main(argv) == 1
    reported = capsys.readouterr().out
    assert "metadata.description" in reported and "metadata.authors" in reported

    doc = yaml.safe_load(config.read_text())
    doc["metadata"]["description"] = "the Minor's acceptance run"
    doc["metadata"]["authors"] = ["Kyungjoon Lee"]
    config.write_text(yaml.safe_dump(doc))
    capsys.readouterr()
    assert main(argv) == 0
    assert "✓ config valid" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# W3 — the documented layouts versus what the scaffolds write.
# `docs/superpowers/W3-SCOPING.md`.
#
# The layout lives in `reference.md`'s two fenced trees and in `scaffold.py` /
# `plugin_scaffold.py`, and nothing compared them — which is how six lines came
# to disagree. This is the pair § CLI reference has had for commands since H9
# (`tests/test_cli.py`, "the list of commands lives in the document and in
# `cli.NOT_BUILT_COMMANDS`, nowhere else"): parse the document, observe the code,
# keep no third copy.
# ---------------------------------------------------------------------------

_TREE_ENTRY = re.compile(r"^(?P<indent>(?:[│ ]   )*)(?:├──|└──) (?P<name>[^#]+?)\s*(?:#.*)?$")


def documented_tree(section: str, document: Path = _REFERENCE_MD) -> set[str]:
    """The set of paths the fenced tree under `section` names, root stripped.

    Paths only — never the trailing annotation, which the document must stay free
    to reword without failing a test. A trailing `/` is kept, because it is what
    marks a directory and the reverse direction below needs to know.

    Located by its heading rather than by position: *"the fenced block after the
    third paragraph"* is the row-position trap in another currency.
    """
    text = document.read_text()
    start = text.index(section)
    while True:
        fence = text.index("```", start)
        body = text[text.index("\n", fence) + 1 : text.index("```", fence + 3)]
        if "├──" in body:
            break
        start = text.index("```", fence + 3) + 3
    parents: dict[int, str] = {}
    named: set[str] = set()
    for line in body.split("\n"):
        match = _TREE_ENTRY.match(line)
        if match is None:
            continue
        depth = len(match.group("indent")) // 4
        name = match.group("name").strip()
        parents[depth] = name
        prefix = "".join(parents[d] for d in range(depth))
        named.add(prefix + name)
    return named


def _tracked(root: Path) -> set[str]:
    """What the scaffold's own first commit holds, which is what a CLONE sees.

    `git ls-files` rather than a filesystem walk, deliberately: W3-SCOPING § 0's
    whole finding is that the two differ — an empty directory exists on the
    author's disk, is invisible to git in both directions, and is absent from
    every clone.
    """
    listed = subprocess.run(
        ["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True
    )
    return {line for line in listed.stdout.split("\n") if line}


def _unenumerated(named: set[str], tracked: set[str]) -> list[str]:
    """Directories a tree half-enumerates.

    The two directions below are each necessary and neither catches a **deleted**
    line: dropping `src/<pkg>/steps/` removes a claim, so the forward direction has
    nothing to check, and the reverse direction finds every file under it announced
    by the parent that is still named. Measured — the arm that should have caught it
    stayed green.

    So: **a tree that enumerates a level enumerates it completely.** Where the tree
    names any child of a directory, every subdirectory of that directory holding a
    tracked file must be named too. Files need no such rule — no tree lists every
    `__init__.py`, and none pretends to.
    """
    # A directory the tree names, or names something inside: naming
    # `<pkg>/templates/my_assay.py` announces `<pkg>/templates/` as surely as
    # naming the directory would.
    announced = set()
    for entry in named:
        if entry.endswith("/"):
            announced.add(entry)
        head = entry.rsplit("/", 1)[0] + "/" if "/" in entry else ""
        if head:
            announced.add(head)
    enumerated = {d for d in announced if any(a != d and a.startswith(d) for a in announced)}
    problems = []
    for path in sorted(tracked):
        if "/" not in path:
            continue
        directory = path.rsplit("/", 1)[0] + "/"
        parent = directory[:-1].rsplit("/", 1)[0] + "/" if directory[:-1].count("/") else ""
        if parent in enumerated and directory not in announced:
            problems.append(
                f"the tree enumerates {parent} and does not name {directory}, which holds {path}"
            )
    return sorted(set(problems))


def _visible_in(entry: str, tracked: set[str]) -> bool:
    """Whether a clone of the scaffold's own commit would hold `entry`.

    Checked against `git ls-files` rather than the filesystem, and that is the
    whole point of this helper: an existence check on disk **cannot see** the
    fault W3-SCOPING § 0 found. `examples/<stem>/` was created and left empty, git
    tracks no empty directory, so it existed on the author's disk and in no clone
    — and deleting the `.gitkeep` that fixes it left an `exists()`-based agreement
    test entirely green, measured, which is why this reads the commit instead.

    A directory counts as present when something tracked sits under it; a file
    counts when it is tracked itself. `.git/` is the one entry its caller exempts:
    a repository's own directory is not content, and the tree names it to say that
    `git init` ran.
    """
    if entry.endswith("/"):
        return any(path.startswith(entry) for path in tracked)
    return entry in tracked


def _assert_agreement(root: Path, named: set[str]) -> None:
    """Both directions, and the second is the one nobody was checking.

    Collected into one assertion rather than two, so a failure reports **every**
    disagreement at once: two `assert`s stop at the first, and a reader who cannot
    count what is broken reviews these lines one at a time — which is how five of
    them survived.
    """
    directories = tuple(entry for entry in named if entry.endswith("/"))
    tracked = _tracked(root)
    problems = (
        _unenumerated(named, tracked)
        + [
            f"named by the document and absent from what the scaffold commits: {entry}"
            for entry in sorted(named)
            if entry != ".git/" and not _visible_in(entry, tracked)
        ]
        + [
            f"tracked by the scaffold and named nowhere in the tree: {path}"
            for path in sorted(_tracked(root))
            if path not in named and not path.startswith(directories)
        ]
    )
    assert not problems, "\n".join(problems)


def test_w3_the_documented_project_tree_is_what_new_writes(tmp_path: Path):
    """§ Scaffolding's tree against `publishable new`."""
    named = documented_tree("## Scaffolding: `publishable new`")
    _assert_agreement(scaffold_project(tmp_path / "my-study"), named)


def test_w3_the_documented_plugin_tree_is_what_plugin_new_writes(tmp_path: Path):
    """§ Creating a plugin's tree against `publishable plugin new`."""
    from publishable.plugin_scaffold import scaffold_plugin

    named = documented_tree("### Creating a plugin: `publishable plugin new`")
    _assert_agreement(scaffold_plugin(tmp_path / "publishable-my-assay"), named)


def test_w3_the_tree_parser_can_fail():
    """A parser whose zeros nobody has seen fail is a parser that reports zero.

    Three claims: it finds the counts the two trees actually carry, it resolves a
    nested entry to its parent rather than to a bare name, and a path the tree
    does not carry is absent from what it returns.
    """
    project = documented_tree("## Scaffolding: `publishable new`")
    plugin = documented_tree("### Creating a plugin: `publishable plugin new`")

    assert len(project) == 12, sorted(project)
    assert "pyproject.toml" in project and "src/" in project
    # The trees name what the scaffolds write and nothing else, which is what lets
    # the agreement above need no exception list and no reading of the annotation
    # column: `uv.lock` is written by `uv` on first run and is named in prose
    # beside both trees instead.
    assert "uv.lock" not in project

    assert "src/publishable_my_assay/templates/my_assay.py" in plugin
    assert "templates/my_assay.py" not in plugin  # the nesting is resolved, not flattened
    assert "tests/test_my_assay.py" in plugin
    assert "publishable-my-assay/" not in plugin  # the root is stripped
    assert "not-in-any-tree.txt" not in plugin


def test_w3_the_documented_plugin_readme_is_the_one_the_scaffold_writes(tmp_path: Path):
    """§ Creating a plugin shows the generated README in full, so it is a second
    copy of a generated artifact — the same defect class as the tree, in prose.

    Compared byte for byte, which is safe *because* the README is derived: every
    name in it comes from the distribution's stem, so there is no worked value for
    a document to elide and no reason for the two to differ. The block is located
    by the sentence that introduces it rather than by position, and the extraction
    asserts it found the block before comparing.
    """
    from publishable.plugin_scaffold import scaffold_plugin

    text = _REFERENCE_MD.read_text()
    intro = text.index("an install line and **the names it registers**")
    fence = text.index("````markdown", intro)
    documented = text[text.index("\n", fence) + 1 : text.index("````", fence + 4)]
    assert documented.startswith("# publishable-my-assay"), "the fenced block is not the README"

    root = scaffold_plugin(tmp_path / "publishable-my-assay")
    assert documented == (root / "README.md").read_text()


# ---------------------------------------------------------------------------
# The tutorial reproduces three generated artifacts — the plugin layout, its
# entry-point table and its shipped test. Each is compared to what the scaffold
# writes, for `reference.md` § CLI reference's reason: a document that copies a
# generated artifact is a second copy, and a second copy drifts. The tutorial
# carries no dated build claim, so these are what keep its present tense true.
# ---------------------------------------------------------------------------


def _tutorial_fence(after: str, kind: str = "") -> str:
    """The first ```<kind> block following `after` in the tutorial.

    Located by a sentence rather than by position, and it asserts it found the
    marker: a parse that silently matches nothing reports agreement.
    """
    text = _TUTORIAL_MD.read_text()
    assert after in text, f"the sentence introducing this block moved: {after!r}"
    fence = text.index(f"```{kind}\n", text.index(after))
    return text[text.index("\n", fence) + 1 : text.index("```", fence + 3)]


@_needs_the_tutorial
def test_the_tutorials_plugin_tree_is_what_plugin_new_writes(tmp_path: Path):
    """Route B step 1's tree, both directions, against a real scaffold."""
    from publishable.plugin_scaffold import scaffold_plugin

    named = documented_tree("### 1. Scaffold", _TUTORIAL_MD)
    _assert_agreement(scaffold_plugin(tmp_path / "publishable-plate-assay"), named)


@_needs_the_tutorial
def test_the_tutorials_entry_point_table_is_what_plugin_new_declares(tmp_path: Path):
    """Route B step 2 quotes the generated `pyproject.toml`'s entry-point tables.

    Compared as parsed TOML rather than as text, because the tutorial shows those
    tables alone while the file also carries `[project]` and the build backend —
    a text comparison would fail on what the tutorial correctly omits.
    """
    from publishable.plugin_scaffold import scaffold_plugin

    documented = tomllib.loads(_tutorial_fence("The entry points are the registration", "toml"))
    root = scaffold_plugin(tmp_path / "publishable-plate-assay")
    written = tomllib.loads((root / "pyproject.toml").read_text())
    assert documented["project"]["entry-points"] == written["project"]["entry-points"]


@_needs_the_tutorial
def test_the_tutorials_quote_of_the_shipped_test_omits_only_its_docstring(tmp_path: Path):
    """§ Testing a plugin quotes `tests/test_<stem>.py` and says it elides one
    docstring. Every other line must be there, in order.

    Asserted as a line-by-line subsequence rather than by equality, because the
    elision is exactly what the tutorial declares — and asserted as ordered
    rather than as a set, so a quote that shuffled the file would still fail.
    """
    from publishable.plugin_scaffold import scaffold_plugin

    quoted = _tutorial_fence("asks one question", "python").split("\n")
    root = scaffold_plugin(tmp_path / "publishable-plate-assay")
    written = (root / "tests" / "test_plate_assay.py").read_text().split("\n")

    remaining = list(quoted)
    inside_docstring = False
    missing = []
    for line in written:
        if line.strip().startswith('"""'):
            inside_docstring = not inside_docstring or line.strip() != '"""'
            if line.count('"""') == 2:
                inside_docstring = False
            continue
        if inside_docstring:
            continue
        if line in remaining:
            remaining = remaining[remaining.index(line) + 1 :]
        else:
            missing.append(line)
    assert not missing, f"in the scaffold's test and not in the tutorial: {missing}"
