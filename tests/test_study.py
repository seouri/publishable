# tests/test_study.py
"""`study new` and `study add`. docs/reference.md § Studies: what a paper
reports. H8c tasks 11-14 —
`docs/superpowers/plans/2026-08-21-report-study.md`,
`docs/superpowers/specs/2026-08-21-report-study-design.md` Decisions 9-13.
"""

from pathlib import Path

import pytest
import yaml

from publishable.cli import main
from publishable.diagnostics import EXIT_INVOCATION, EXIT_OK, EXIT_WRONG
from publishable.errors import ContractError
from publishable.study import study_new


def _snapshot(root: Path) -> set[tuple[str, bytes]]:
    """Every file under `root`, path plus bytes — the refuse-before-write
    review's own tool: a refusal whose bundle is byte-identical before and
    after proves nothing reached disk, where an exit-code assertion alone
    would pass a build that wrote first and refused second."""
    if not root.exists():
        return set()
    return {(str(p.relative_to(root)), p.read_bytes()) for p in root.rglob("*") if p.is_file()}


# --- Task 11: `study new` ---------------------------------------------------


def test_study_new_writes_title_authors_and_empty_runs_and_no_code_block(tmp_path: Path):
    bundle = tmp_path / "study"
    assert main(["study", "new", str(bundle), "--title", "Rank correlation methods"]) == EXIT_OK
    doc = yaml.safe_load((bundle / "study.yaml").read_text())
    assert doc == {"title": "Rank correlation methods", "authors": [], "runs": {}}
    assert "code" not in doc


def test_study_new_refuses_an_existing_study_yaml_and_writes_nothing(tmp_path: Path):
    bundle = tmp_path / "study"
    assert main(["study", "new", str(bundle), "--title", "First"]) == EXIT_OK
    before = _snapshot(bundle)
    assert main(["study", "new", str(bundle), "--title", "Second"]) == EXIT_WRONG
    assert _snapshot(bundle) == before
    # The original title survives — a refused second `study new` changed
    # nothing, not even the one file it might have "just updated".
    doc = yaml.safe_load((bundle / "study.yaml").read_text())
    assert doc["title"] == "First"


def test_study_new_onto_a_bare_directory_with_no_study_yaml_succeeds(tmp_path: Path):
    """Mutation target (task 11 step 5): treating an existing DIRECTORY as
    'existing' would refuse here. `~/papers/x/study` beside a manuscript is
    a directory a person may well have made first."""
    bundle = tmp_path / "study"
    bundle.mkdir(parents=True)
    (bundle / "notes.txt").write_text("not a study.yaml")
    assert main(["study", "new", str(bundle), "--title", "Title"]) == EXIT_OK
    assert (bundle / "study.yaml").exists()
    assert (bundle / "notes.txt").exists()


def test_study_new_refuses_inside_a_git_repo_and_writes_no_study_yaml(tmp_path: Path):
    """Mutation target (task 11 step 5): checking `E-STUDY-IN-REPO` AFTER
    writing would still exit non-zero here but leave `study.yaml` behind —
    caught by asserting its absence, not just the exit code."""
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    bundle = repo / "papers" / "study"
    assert main(["study", "new", str(bundle), "--title", "Title"]) == EXIT_WRONG
    assert not (bundle / "study.yaml").exists()
    assert not bundle.exists()


def test_study_new_direct_call_raises_e_study_in_repo(tmp_path: Path):
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    bundle = repo / "study"
    with pytest.raises(ContractError) as exc_info:
        study_new(bundle, "Title")
    assert exc_info.value.code == "E-STUDY-IN-REPO"


def test_study_new_direct_call_raises_e_study_exists(tmp_path: Path):
    bundle = tmp_path / "study"
    study_new(bundle, "First")
    with pytest.raises(ContractError) as exc_info:
        study_new(bundle, "Second")
    assert exc_info.value.code == "E-STUDY-EXISTS"


def test_study_new_refuses_an_unrecognized_option_before_touching_disk(tmp_path: Path):
    bundle = tmp_path / "study"
    assert main(["study", "new", str(bundle), "--titel", "Typo"]) == EXIT_INVOCATION
    assert not bundle.exists()


def test_study_new_refuses_missing_title_before_touching_disk(tmp_path: Path):
    bundle = tmp_path / "study"
    assert main(["study", "new", str(bundle)]) == EXIT_INVOCATION
    assert not bundle.exists()


def test_study_new_probe_arity_from_the_cli_table_test_writes_nothing_here():
    """The exact invocation `test_reference_cli_tables_match_what_the_cli_does`
    makes, run from inside this repository: two junk positionals and no
    `--title`, which must refuse before scaffolding anything into the
    working tree the way `generate template`'s own arity check protects
    against."""
    assert main(["study", "new", "_probe_a", "_probe_b"]) == EXIT_INVOCATION
    assert not Path("_probe_a").exists()


def test_study_add_still_not_built_until_task_13(tmp_path: Path):
    bundle = tmp_path / "study"
    study_new(bundle, "Title")
    assert main(["study", "add", str(bundle), "x", "--as", "main"]) == EXIT_INVOCATION


def test_study_with_no_subcommand_still_answers_not_built_until_task_13():
    assert main(["study"]) == EXIT_INVOCATION
