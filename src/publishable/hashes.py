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


def _units_excluding_drawn_seeds(units: Any) -> Any:
    """`data.units` with every drawn partition's own `seed` dropped —
    `assign.<axis>.seed` from each axis block, and `holdout.seed`.

    `assign` is a mapping of axis name -> block, so its exclusion is per-axis:
    an axis's own `seed` is dropped from its own block only, never the whole
    `assign` subtree and never a sibling axis's `seed`. `holdout` is a single
    block, so its exclusion is one key. See docs/reference.md § What `auto`
    derives from: each of these seeds mixes the digest with the roster, and a
    seed that is itself inside the digest it is mixed with would make the
    derivation self-referential.

    **The wider harm is the reason this is not merely tidy.** `design_digest`
    canonicalizes `data.units` wholesale, and every other derived draw in the
    run reads the digest — the `seed` repeat stream, `sweep.sample`, each
    axis's assignment. Leaving a pinned seed in would mean that pinning one
    partition to cite it silently redrew all the others, which is the exact
    confounding § What `auto` derives from exists to prevent.

    Every other field of both blocks still moves the digest, which is the
    point: widening `frac`, restratifying, or changing an axis's `method` is a
    different design and must not be reproducible under the same digest.

    `design_digest` runs at run time on a validated config, but `validate`
    reaches it too (indirectly, via `expand` -> the `sample` seed derivation),
    so a malformed config can arrive here first. This function never raises: a
    non-mapping `units`, a non-mapping `assign`, a non-mapping axis block, or a
    non-mapping `holdout` is left exactly as given rather than unpacked, so the
    caller's canonical JSON encoding still runs over *something* instead of
    crashing on a shape it did not expect.
    """
    if not isinstance(units, dict):
        return units
    out = units
    assign = out.get("assign")
    if isinstance(assign, dict):
        new_assign = {}
        changed = False
        for axis, block in assign.items():
            if isinstance(block, dict) and "seed" in block:
                new_assign[axis] = {k: v for k, v in block.items() if k != "seed"}
                changed = True
            else:
                new_assign[axis] = block
        if changed:
            out = {**out, "assign": new_assign}
    holdout = out.get("holdout")
    if isinstance(holdout, dict) and "seed" in holdout:
        out = {**out, "holdout": {k: v for k, v in holdout.items() if k != "seed"}}
    return out


def design_digest(config: dict[str, Any]) -> str:
    """`data.units` (every field except a drawn partition's own `seed`) and `sweep.groups`.

    A parameter edit redraws nothing, and neither does pinning or changing an
    axis's `assign.seed` or `data.units.holdout.seed` — see
    `_units_excluding_drawn_seeds`.
    """
    units = _units_excluding_drawn_seeds((config.get("data") or {}).get("units"))
    groups = (config.get("sweep") or {}).get("groups")
    return _prefixed(hashlib.sha256(_canonical({"units": units, "groups": groups})).hexdigest())
