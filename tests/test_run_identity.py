from datetime import UTC, datetime
from pathlib import Path

import pytest

from publishable import ContractError
from publishable.run_identity import RunLock, allocate_run_dir, point_latest

WHEN = datetime(2026, 8, 8, 14, 2, 11, tzinfo=UTC)
HASH = "sha256:8e21ab3cafe0000000000000000000000000000000000000000000000000000"


def test_the_id_is_timestamp_then_short_code_hash(tmp_path: Path):
    run_dir = allocate_run_dir(tmp_path, HASH, WHEN)
    assert run_dir.name == "run_2026-08-08T14-02-11Z_8e21ab3"
    assert run_dir.is_dir()


def test_a_collision_is_resolved_by_suffix_not_by_precision(tmp_path: Path):
    first = allocate_run_dir(tmp_path, HASH, WHEN)
    second = allocate_run_dir(tmp_path, HASH, WHEN)
    third = allocate_run_dir(tmp_path, HASH, WHEN)
    assert second.name == first.name + "_b"
    assert third.name == first.name + "_c"


def test_latest_points_at_the_real_id(tmp_path: Path):
    run_dir = allocate_run_dir(tmp_path, HASH, WHEN)
    point_latest(tmp_path, run_dir)
    latest = tmp_path / "latest"
    resolved = latest.resolve() if latest.is_symlink() else tmp_path / (
        tmp_path / "latest.txt"
    ).read_text().strip()
    assert resolved.name == run_dir.name


def test_the_lock_records_who_holds_it_and_is_released(tmp_path: Path):
    run_dir = allocate_run_dir(tmp_path, HASH, WHEN)
    with RunLock(run_dir):
        assert (run_dir / "lock").is_file()
        assert "pid" in (run_dir / "lock").read_text()
    assert not (run_dir / "lock").exists()


def test_a_held_lock_is_reported_rather_than_assumed_dead(tmp_path: Path):
    run_dir = allocate_run_dir(tmp_path, HASH, WHEN)
    with RunLock(run_dir):
        with pytest.raises(ContractError) as e:
            with RunLock(run_dir):
                pass
        assert e.value.code == "E-RUN-LOCKED"


def _sole_pointer_target(tmp_path: Path) -> str:
    """Assert exactly one pointer form exists and return the run id it names."""
    link = tmp_path / "latest"
    text = tmp_path / "latest.txt"
    link_there = link.is_symlink() or link.exists()
    text_there = text.exists()
    assert link_there != text_there, "exactly one pointer form must exist"
    if link_there:
        return link.resolve().name
    return text.read_text().strip()


def test_a_fallback_run_followed_by_a_symlink_run_leaves_one_pointer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    first = allocate_run_dir(tmp_path, HASH, WHEN)
    second = allocate_run_dir(tmp_path, HASH, WHEN)

    real_symlink_to = Path.symlink_to

    def failing_symlink_to(self: Path, *args: object, **kwargs: object) -> None:
        raise OSError("symlinks unavailable")

    monkeypatch.setattr(Path, "symlink_to", failing_symlink_to)
    point_latest(tmp_path, first)
    assert _sole_pointer_target(tmp_path) == first.name

    monkeypatch.setattr(Path, "symlink_to", real_symlink_to)
    point_latest(tmp_path, second)
    assert _sole_pointer_target(tmp_path) == second.name


def test_a_symlink_run_followed_by_a_fallback_run_leaves_one_pointer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    first = allocate_run_dir(tmp_path, HASH, WHEN)
    second = allocate_run_dir(tmp_path, HASH, WHEN)

    point_latest(tmp_path, first)
    assert _sole_pointer_target(tmp_path) == first.name

    def failing_symlink_to(self: Path, *args: object, **kwargs: object) -> None:
        raise OSError("symlinks unavailable")

    monkeypatch.setattr(Path, "symlink_to", failing_symlink_to)
    point_latest(tmp_path, second)
    assert _sole_pointer_target(tmp_path) == second.name


def test_a_held_locks_message_survives_a_vanished_lock_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    run_dir = allocate_run_dir(tmp_path, HASH, WHEN)
    with RunLock(run_dir):

        def unreadable(self: Path, *args: object, **kwargs: object) -> str:
            raise OSError("lock file vanished mid-read")

        monkeypatch.setattr(Path, "read_text", unreadable)
        with pytest.raises(ContractError) as e:
            with RunLock(run_dir):
                pass
        assert e.value.code == "E-RUN-LOCKED"
