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


# Whole-project review 2026-08-26, M2: `manifest_hash` digested the whole
# manifest, `mtime` included, so `touch` alone moved `input_manifest_hash` while
# `verify_manifest` — the change DETECTOR — correctly reported nothing changed,
# because it compares `sha256` for a hashed file and falls back to size+mtime
# only for one the policy left unhashed. The detector was content-addressed
# where it could be and the hash never was.


def test_touch_alone_does_not_move_the_hash_under_hash_all(input_dir: Path):
    """The defect, stated as the property. Every byte is identical and every
    mtime differs, so nothing but the mtime can be what a moved digest saw.

    Paired with the detector's own answer in the same test: `verify_manifest`
    reported nothing changed before this fix too, and asserting the hash alone
    would not say the two now agree — which is the whole finding.
    """
    before = build_manifest(input_dir, "hash_all")
    digest = manifest_hash(before)
    for path in (input_dir / "index.csv", input_dir / "sub" / "scan.bin"):
        stat = path.stat()
        os.utime(path, ns=(stat.st_mtime_ns + 1_000_000_000, stat.st_mtime_ns + 1_000_000_000))
    after = build_manifest(input_dir, "hash_all")
    # The mtimes really moved — without this the test passes on a filesystem
    # that quietly ignored `os.utime`, which is a test that cannot fail.
    assert {r: e["mtime"] for r, e in after["files"].items()} != {
        r: e["mtime"] for r, e in before["files"].items()
    }
    assert verify_manifest(input_dir, before) == []
    assert manifest_hash(after) == digest


def test_a_content_edit_still_moves_the_hash_under_hash_all(input_dir: Path):
    """The control the test above needs: a projection that dropped too much
    would make the digest insensitive to content as well, and a hash nothing
    moves is not an identity claim."""
    before = build_manifest(input_dir, "hash_all")
    (input_dir / "index.csv").write_text("patient_id\np1\np2\np3\n")
    assert manifest_hash(build_manifest(input_dir, "hash_all")) != manifest_hash(before)


def test_the_manifest_still_records_mtime_for_a_hashed_file(input_dir: Path):
    """Only the DIGEST drops it. `verify_manifest`'s size+mtime fallback reads
    the recorded value for an unhashed file, and `manifest/input.json` is
    byte-identical across this change — so the projection has to live in
    `manifest_hash` rather than in `build_manifest`."""
    m = build_manifest(input_dir, "hash_all")
    for entry in m["files"].values():
        assert entry["sha256"] is not None
        assert isinstance(entry["mtime"], int)


def test_touch_still_moves_the_hash_under_none(input_dir: Path):
    """No weaker where content is not available. Under `none` there is no
    content hash, so size and mtime are the only evidence there is and the
    digest must keep covering both — the policy's own documented claim is a
    change *detector*, not a verification."""
    before = build_manifest(input_dir, "none")
    path = input_dir / "index.csv"
    stat = path.stat()
    os.utime(path, ns=(stat.st_mtime_ns + 1_000_000_000, stat.st_mtime_ns + 1_000_000_000))
    assert manifest_hash(build_manifest(input_dir, "none")) != manifest_hash(before)


def test_under_hash_index_only_the_named_files_mtime_stops_counting(tmp_path: Path):
    """The discriminating arm: one file the policy hashed and one it did not, in
    one `input_dir`, touched one at a time. A projection applied to every file
    alike would pass the first half and fail the second; one applied to none
    would fail the first. Neither reading survives both assertions."""
    (tmp_path / "index.csv").write_text("patient_id\np1\n")
    (tmp_path / "unnamed.txt").write_text("not named by anything\n")

    def touch(name: str) -> None:
        path = tmp_path / name
        ns = path.stat().st_mtime_ns + 1_000_000_000
        os.utime(path, ns=(ns, ns))

    before = build_manifest(tmp_path, "hash_index", {"index.csv"})
    assert before["files"]["index.csv"]["sha256"] is not None
    assert before["files"]["unnamed.txt"]["sha256"] is None

    touch("index.csv")
    assert manifest_hash(build_manifest(tmp_path, "hash_index", {"index.csv"})) == manifest_hash(
        before
    )

    middle = build_manifest(tmp_path, "hash_index", {"index.csv"})
    touch("unnamed.txt")
    assert manifest_hash(build_manifest(tmp_path, "hash_index", {"index.csv"})) != manifest_hash(
        middle
    )


def test_the_policy_stays_in_the_payload_so_two_claims_cannot_collide(tmp_path: Path):
    """Under an `input_dir` whose every file is an index file, `hash_index` and
    `hash_all` produce identical per-file projections. They are two different
    claims about the same bytes — "the units were identical and nothing else
    moved size or timestamp" against "the data was identical" — so they must
    not share one digest. Dropping `policy` from the payload makes them equal.
    """
    (tmp_path / "index.csv").write_text("patient_id\np1\n")
    all_ = build_manifest(tmp_path, "hash_all")
    index = build_manifest(tmp_path, "hash_index", {"index.csv"})
    assert all_["files"] == index["files"]
    assert manifest_hash(all_) != manifest_hash(index)
