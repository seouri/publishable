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
    """Relative paths plus size, mtime, and — at the policy's depth — content hash.

    `units.index_names` supplies `index_names` for `hash_index`: the source's own
    file, where the source names one, plus every path its resolved units name.
    """
    if policy not in POLICIES:
        raise ValueError(f"unknown input_manifest_policy {policy!r}")
    files: dict[str, Any] = {}
    for path in sorted(p for p in input_dir.rglob("*") if p.is_file()):
        rel = path.relative_to(input_dir).as_posix()
        stat = path.stat()
        hash_it = policy == "hash_all" or (policy == "hash_index" and rel in (index_names or set()))
        files[rel] = {
            "size": stat.st_size,
            "mtime": stat.st_mtime_ns,
            "sha256": _sha256(path) if hash_it else None,
        }
    return {"policy": policy, "files": files}


def _hash_payload(manifest: dict[str, Any]) -> dict[str, Any]:
    """The manifest with each HASHED file's `mtime` dropped.

    `input_manifest_hash` answers *was the data identical?*, and an `mtime` is
    not data. Digesting the manifest whole made `touch` alone move the published
    hash while `verify_manifest` — the change *detector* — correctly reported
    nothing changed, because it compares `sha256` for a file the policy hashed
    and falls back to size and mtime only for one it did not. The detector was
    content-addressed where it could be and the hash never was.

    The projection is exactly that asymmetry and no wider:

    - a file the policy hashed contributes its `size` and its `sha256`, and not
      its `mtime` — content decides, and `size` is redundant beside a content
      hash rather than wrong, so it is left in place rather than removed for
      tidiness;
    - a file the policy did **not** hash contributes all three, unchanged. Size
      and mtime are the only evidence there is, and dropping the mtime would make
      the hash *weaker* than the detector rather than as strong.

    `policy` stays in the payload. Under an `input_dir` whose every file is an
    index file, `hash_index` and `hash_all` produce identical per-file
    projections, and two different claims about the same bytes must not collide
    on one digest.

    The MANIFEST itself is unchanged — `verify_manifest`'s fallback needs the
    mtime, and `manifest/input.json` is byte-identical across this change. Only
    the digest taken over it moves.
    """
    files = {}
    for rel, entry in manifest["files"].items():
        if entry.get("sha256") is None:
            files[rel] = entry
            continue
        files[rel] = {k: v for k, v in entry.items() if k != "mtime"}
    return {**manifest, "files": files}


def manifest_hash(manifest: dict[str, Any]) -> str:
    payload = json.dumps(_hash_payload(manifest), sort_keys=True, separators=(",", ":")).encode()
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
