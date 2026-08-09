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


@pytest.mark.xfail(
    reason=(
        "point_latest's two pointer forms can disagree: a run on a "
        "symlink-capable filesystem does not clear a stale latest.txt left "
        "by an earlier fallback run, so a caller reading latest.txt sees "
        "the old run while a caller reading the `latest` symlink sees the "
        "new one. See task-13-report.md."
    ),
    strict=True,
)
def test_point_latest_does_not_leave_disagreeing_pointers(tmp_path: Path, monkeypatch):
    first = allocate_run_dir(tmp_path, HASH, WHEN)
    second = allocate_run_dir(tmp_path, HASH, WHEN)

    real_symlink_to = Path.symlink_to

    def failing_symlink_to(self: Path, *args: object, **kwargs: object) -> None:
        raise OSError("symlinks unavailable")

    monkeypatch.setattr(Path, "symlink_to", failing_symlink_to)
    point_latest(tmp_path, first)
    assert (tmp_path / "latest.txt").read_text().strip() == first.name

    monkeypatch.setattr(Path, "symlink_to", real_symlink_to)
    point_latest(tmp_path, second)

    latest_link = tmp_path / "latest"
    latest_txt = tmp_path / "latest.txt"
    assert latest_link.is_symlink()
    assert latest_link.resolve().name == second.name
    # The stale latest.txt from the fallback run should not still claim `first`.
    assert not latest_txt.exists() or latest_txt.read_text().strip() == second.name
