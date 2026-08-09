# src/publishable/manifest.py
"""What was read. See docs/reference.md § How the three are computed."""

import hashlib
import json
from pathlib import Path
from typing import Any

POLICIES = ("hash_all", "hash_index", "none")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(
    input_dir: Path, policy: str, index_names: set[str] | None = None
) -> dict[str, Any]:
    """Relative paths plus size, mtime, and — at the policy's depth — content hash."""
    if policy not in POLICIES:
        raise ValueError(f"unknown input_manifest_policy {policy!r}")
    files: dict[str, Any] = {}
    for path in sorted(p for p in input_dir.rglob("*") if p.is_file()):
        rel = path.relative_to(input_dir).as_posix()
        stat = path.stat()
        hash_it = policy == "hash_all" or (
            policy == "hash_index" and rel in (index_names or set())
        )
        files[rel] = {
            "size": stat.st_size,
            "mtime": stat.st_mtime_ns,
            "sha256": _sha256(path) if hash_it else None,
        }
    return {"policy": policy, "files": files}


def manifest_hash(manifest: dict[str, Any]) -> str:
    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def verify_manifest(input_dir: Path, manifest: dict[str, Any]) -> list[str]:
    """Relative paths that moved since the manifest was built. Empty when clean.

    An added file counts as a change: `hash_all` claims the data was identical,
    and a dataset with a file in it that was not there at run start is not.
    """
    changed: list[str] = []
    present = {p.relative_to(input_dir).as_posix() for p in input_dir.rglob("*") if p.is_file()}
    changed.extend(present - set(manifest["files"]))
    for rel, entry in manifest["files"].items():
        path = input_dir / rel
        if not path.is_file():
            changed.append(rel)
            continue
        stat = path.stat()
        if entry["sha256"] is not None:
            if _sha256(path) != entry["sha256"]:
                changed.append(rel)
        elif stat.st_size != entry["size"] or stat.st_mtime_ns != entry["mtime"]:
            changed.append(rel)
    return sorted(changed)
