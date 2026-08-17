# tests/test_manifest.py
import os
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


def test_stored_mtime_is_an_int_at_nanosecond_scale(input_dir: Path):
    """A later reader must not mistake this for whole seconds.

    A plausible seconds-since-epoch value in 2026 is on the order of 1.8e9; a
    nanosecond-scaled value is about a billion times larger, so a bare lower
    bound is enough to distinguish the two without pinning an exact value.
    """
    m = build_manifest(input_dir, "hash_all")
    for entry in m["files"].values():
        assert isinstance(entry["mtime"], int)
        assert entry["mtime"] > 10**18


def test_a_same_size_edit_is_detected_under_hash_all_regardless_of_timestamp(input_dir: Path):
    """The content-hash path must not start depending on mtime.

    Both the size and the mtime are pinned to the manifest's recorded values
    (via `os.utime`) before the edit, so only the sha256 comparison can be
    what catches this.
    """
    path = input_dir / "index.csv"
    m = build_manifest(input_dir, "hash_all")
    entry = m["files"]["index.csv"]
    same_size_content = "patient_id\np1\npX\n"
    assert len(same_size_content) == entry["size"]
    path.write_text(same_size_content)
    ns = entry["mtime"]
    os.utime(path, ns=(ns, ns))
    assert path.stat().st_size == entry["size"]
    assert path.stat().st_mtime_ns == entry["mtime"]
    assert verify_manifest(input_dir, m) == ["index.csv"]


def test_a_same_size_edit_is_detected_under_none_at_nanosecond_resolution(input_dir: Path):
    """`none` has no content hash, so it can only catch this via mtime.

    We force the post-edit mtime to a different nanosecond than the
    manifest's recorded value with `os.utime`, rather than relying on the
    filesystem clock to advance between the two writes on its own — on a
    coarse-grained filesystem clock two writes in the same tick would make
    this test flaky without that.
    """
    path = input_dir / "index.csv"
    m = build_manifest(input_dir, "none")
    entry = m["files"]["index.csv"]
    same_size_content = "patient_id\np1\npX\n"
    assert len(same_size_content) == entry["size"]
    path.write_text(same_size_content)
    os.utime(path, ns=(entry["mtime"] + 1, entry["mtime"] + 1))
    assert path.stat().st_size == entry["size"]
    assert verify_manifest(input_dir, m) == ["index.csv"]


def test_hash_index_hashes_the_named_files_and_nothing_else(tmp_path: Path):
    """The VALUE, not the key. Under `hash_index` the `sha256` key is present and
    `None` today, so `"sha256" in entry` passes on a completely broken policy —
    which is how this went unnoticed since the policy shipped. The unnamed file is
    the control that separates `hash_index` from `hash_all`."""
    (tmp_path / "index.csv").write_text("patient_id\np1\n")
    (tmp_path / "scan.bin").write_bytes(b"\x00\x01")
    (tmp_path / "unnamed.txt").write_text("not named by anything\n")

    manifest = build_manifest(tmp_path, "hash_index", {"index.csv", "scan.bin"})
    files = manifest["files"]

    assert files["index.csv"]["sha256"] is not None
    assert files["scan.bin"]["sha256"] is not None
    assert files["unnamed.txt"]["sha256"] is None
    assert (
        files["index.csv"]["sha256"]
        == build_manifest(tmp_path, "hash_all")["files"]["index.csv"]["sha256"]
    )
