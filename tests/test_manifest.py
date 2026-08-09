# tests/test_manifest.py
from pathlib import Path

import pytest

from publishable.manifest import build_manifest, manifest_hash, verify_manifest


@pytest.fixture
def input_dir(tmp_path: Path) -> Path:
    d = tmp_path / "input"
    (d / "sub").mkdir(parents=True)
    (d / "index.csv").write_text("patient_id\np1\np2\n")
    (d / "sub" / "scan.bin").write_bytes(b"\x00\x01")
    return d


def test_hash_all_records_a_content_hash_for_every_file(input_dir: Path):
    m = build_manifest(input_dir, "hash_all")
    assert m["policy"] == "hash_all"
    assert set(m["files"]) == {"index.csv", "sub/scan.bin"}
    assert all(e["sha256"] for e in m["files"].values())
    assert all("size" in e and "mtime" in e for e in m["files"].values())


def test_none_records_paths_sizes_and_mtimes_but_no_content_hash(input_dir: Path):
    m = build_manifest(input_dir, "none")
    assert all(e["sha256"] is None for e in m["files"].values())


def test_a_clean_input_verifies(input_dir: Path):
    m = build_manifest(input_dir, "hash_all")
    assert verify_manifest(input_dir, m) == []


def test_changed_content_is_detected_under_hash_all(input_dir: Path):
    m = build_manifest(input_dir, "hash_all")
    (input_dir / "index.csv").write_text("patient_id\np1\np2\np3\n")
    assert verify_manifest(input_dir, m) == ["index.csv"]


def test_a_removed_file_is_detected(input_dir: Path):
    m = build_manifest(input_dir, "hash_all")
    (input_dir / "sub" / "scan.bin").unlink()
    assert verify_manifest(input_dir, m) == ["sub/scan.bin"]


def test_an_added_file_is_detected(input_dir: Path):
    """`hash_all` claims the data was identical; a new file means it was not."""
    m = build_manifest(input_dir, "hash_all")
    (input_dir / "extra.csv").write_text("patient_id\np3\n")
    assert verify_manifest(input_dir, m) == ["extra.csv"]


def test_the_manifest_hash_is_stable_and_prefixed(input_dir: Path):
    m = build_manifest(input_dir, "hash_all")
    assert manifest_hash(m) == manifest_hash(build_manifest(input_dir, "hash_all"))
    assert manifest_hash(m).startswith("sha256:")
