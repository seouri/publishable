"""The three hashes. See docs/reference.md § How the three are computed."""

import hashlib
import json
from pathlib import Path
from typing import Any

HASHED_TREES = ("src", "templates")
_SKIP_DIRS = {"__pycache__", ".git", ".ruff_cache", ".mypy_cache", ".pytest_cache"}
_SKIP_SUFFIXES = {".pyc", ".pyo"}


def _prefixed(digest: str) -> str:
    return f"sha256:{digest}"


def short(hash_str: str) -> str:
    return hash_str.split(":", 1)[-1][:7]


def hashed_files(repo_root: Path) -> list[tuple[str, Path]]:
    """Sorted (repo-relative path, file) pairs across src/** and templates/**."""
    found: list[tuple[str, Path]] = []
    for tree in HASHED_TREES:
        base = repo_root / tree
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            rel_to_tree = path.relative_to(base)
            if any(part in _SKIP_DIRS for part in rel_to_tree.parts):
                continue
            if path.suffix in _SKIP_SUFFIXES:
                continue
            found.append((path.relative_to(repo_root).as_posix(), path))
    return sorted(found)


def code_hash(repo_root: Path) -> str:
    """sha256 over the sorted list of (relative path, sha256 of contents) pairs.

    Read from the working tree, not from git, so `run` and `draft` compute the
    same function over a clean and a dirty tree alike.
    """
    outer = hashlib.sha256()
    for rel, path in hashed_files(repo_root):
        inner = hashlib.sha256(path.read_bytes()).hexdigest()
        outer.update(rel.encode())
        outer.update(b"\0")
        outer.update(inner.encode())
        outer.update(b"\n")
    return _prefixed(outer.hexdigest())


def _canonical(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def parameters_hash(config: dict[str, Any]) -> str:
    """Everything in the config except `metadata` and the two host paths."""
    covered = {k: v for k, v in config.items() if k != "metadata"}
    data = covered.get("data")
    if isinstance(data, dict):
        covered["data"] = {k: v for k, v in data.items() if k not in ("input_dir", "output_dir")}
    return _prefixed(hashlib.sha256(_canonical(covered)).hexdigest())


def _units_excluding_assign_seed(units: Any) -> Any:
    """`data.units` with `assign.<axis>.seed` dropped from every axis block.

    `assign` is a mapping of axis name -> block, so the exclusion is per-axis:
    an axis's own `seed` is dropped from its own block only, never the whole
    `assign` subtree and never a sibling axis's `seed`. See docs/reference.md
    § What `auto` derives from: an axis's `assign.seed` "mixes digest + the
    axis name + the resolved roster" — a seed that is itself inside the
    digest it is mixed with would make the derivation self-referential.

    `design_digest` runs at run time on a validated config, but `validate`
    reaches it too (indirectly, via `expand` -> the `sample` seed derivation),
    so a malformed config can arrive here first. This function never raises:
    a non-mapping `units`, a non-mapping `assign`, or a non-mapping axis block
    is left exactly as given rather than unpacked, so the caller's canonical
    JSON encoding still runs over *something* instead of crashing on a shape
    it did not expect.
    """
    if not isinstance(units, dict):
        return units
    assign = units.get("assign")
    if not isinstance(assign, dict):
        return units
    new_assign = {}
    changed = False
    for axis, block in assign.items():
        if isinstance(block, dict) and "seed" in block:
            new_assign[axis] = {k: v for k, v in block.items() if k != "seed"}
            changed = True
        else:
            new_assign[axis] = block
    if not changed:
        return units
    return {**units, "assign": new_assign}


def design_digest(config: dict[str, Any]) -> str:
    """`data.units` (every field except `assign.seed` itself) and `sweep.groups`.

    A parameter edit redraws nothing, and neither does pinning or changing an
    axis's `assign.seed` — see `_units_excluding_assign_seed`.
    """
    units = _units_excluding_assign_seed((config.get("data") or {}).get("units"))
    groups = (config.get("sweep") or {}).get("groups")
    return _prefixed(hashlib.sha256(_canonical({"units": units, "groups": groups})).hexdigest())
