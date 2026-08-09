"""uv is not optional. S1 hashes the lockfile; syncing arrives with `reproduce`."""

import hashlib
from pathlib import Path


def uv_lock_info(repo_root: Path) -> tuple[Path | None, str | None]:
    lock = repo_root / "uv.lock"
    if not lock.is_file():
        return None, None
    return lock, "sha256:" + hashlib.sha256(lock.read_bytes()).hexdigest()
