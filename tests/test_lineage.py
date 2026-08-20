"""`read_run_record` — the `run.yaml` reader `lineage.py` gives H8a, tested against
synthesized records for each refusal and against a genuinely produced one (Fixture R),
per `docs/superpowers/plans/2026-08-20-lineage.md` task 1 and
`docs/superpowers/specs/2026-08-20-lineage-design.md` § 3.
"""

from pathlib import Path

import pytest
import yaml
from tests.test_cli import run_a_project

from publishable.errors import ContractError
from publishable.lineage import read_run_record
from publishable.run_record import SCHEMA_VERSION


def _write_run_yaml(run_dir: Path, doc: dict) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run.yaml").write_text(yaml.safe_dump(doc))


def test_no_run_yaml_at_all_is_record_missing(tmp_path: Path):
    run_dir = tmp_path / "run_x"
    run_dir.mkdir()
    with pytest.raises(ContractError) as e:
        read_run_record(run_dir)
    assert e.value.code == "E-UPSTREAM-RECORD-MISSING"


def test_a_path_that_is_not_a_run_directory_at_all_is_record_missing(tmp_path: Path):
    # No directory exists here at all, which is the same fault as an empty one: no
    # run.yaml is at the resolved path either way.
    with pytest.raises(ContractError) as e:
        read_run_record(tmp_path / "never_created")
    assert e.value.code == "E-UPSTREAM-RECORD-MISSING"


def test_invalid_yaml_is_record_unreadable(tmp_path: Path):
    run_dir = tmp_path / "run_x"
    run_dir.mkdir()
    (run_dir / "run.yaml").write_text("schema_version: 1.0\nrun_id: [unterminated\n")
    with pytest.raises(ContractError) as e:
        read_run_record(run_dir)
    assert e.value.code == "E-UPSTREAM-RECORD-UNREADABLE"


def test_a_yaml_document_that_is_not_a_mapping_is_record_unreadable(tmp_path: Path):
    run_dir = tmp_path / "run_x"
    run_dir.mkdir()
    (run_dir / "run.yaml").write_text("- just\n- a\n- list\n")
    with pytest.raises(ContractError) as e:
        read_run_record(run_dir)
    assert e.value.code == "E-UPSTREAM-RECORD-UNREADABLE"


def test_a_mapping_with_no_run_id_is_record_unreadable(tmp_path: Path):
    run_dir = tmp_path / "run_x"
    _write_run_yaml(run_dir, {"schema_version": SCHEMA_VERSION, "status": "completed"})
    with pytest.raises(ContractError) as e:
        read_run_record(run_dir)
    assert e.value.code == "E-UPSTREAM-RECORD-UNREADABLE"


def test_a_schema_version_this_build_does_not_read_is_record_version(tmp_path: Path):
    run_dir = tmp_path / "run_x"
    _write_run_yaml(
        run_dir,
        {"schema_version": "99.9", "run_id": "run_2020-01-01T00-00-00Z_abcdef1"},
    )
    with pytest.raises(ContractError) as e:
        read_run_record(run_dir)
    assert e.value.code == "E-UPSTREAM-RECORD-VERSION"


def test_a_valid_synthesized_record_reads_back_the_parsed_mapping(tmp_path: Path):
    run_dir = tmp_path / "run_x"
    doc = {
        "schema_version": SCHEMA_VERSION,
        "run_id": "run_2020-01-01T00-00-00Z_abcdef1",
        "status": "completed",
    }
    _write_run_yaml(run_dir, doc)
    assert read_run_record(run_dir) == doc


@pytest.mark.parametrize("status", ["partial", "failed"])
def test_a_partial_or_failed_record_is_not_refused_here(tmp_path: Path, status: str):
    """A partial or failed run's completed step wrote a real artifact; refusing the
    whole record on a sibling condition's failure would make that artifact unreadable
    for a reason unrelated to it. The named step's own status is a later task's check.
    """
    run_dir = tmp_path / "run_x"
    doc = {
        "schema_version": SCHEMA_VERSION,
        "run_id": "run_2020-01-01T00-00-00Z_abcdef1",
        "status": status,
    }
    _write_run_yaml(run_dir, doc)
    assert read_run_record(run_dir) == doc


def test_fixture_r_a_real_run_yaml_reads_back_what_the_writer_wrote(tmp_path: Path):
    """Fixture R. `run_a_project` drives a genuine run through `main(["run", ...])`;
    `schema_version` and `run_id` are read back from the produced file rather than
    asserted as literals, so this pins that the reader reads what the writer wrote
    rather than pinning a value that happens to match today.
    """
    doc = run_a_project(tmp_path, replication={"repeats": [{"kind": "seed", "n": 1}]}, units=8)
    run_dir = doc["run_dir"]
    on_disk = yaml.safe_load((run_dir / "run.yaml").read_text())
    record = read_run_record(run_dir)
    assert record["schema_version"] == on_disk["schema_version"]
    assert record["run_id"] == on_disk["run_id"]
    assert record == on_disk
