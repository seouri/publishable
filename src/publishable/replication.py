"""Repeat kinds. S1 implements `seed`; `batch` and `fold` arrive in S3.

See docs/reference.md § Repeat kinds.
"""

import hashlib
from dataclasses import dataclass
from typing import Any

from publishable.errors import ContractError

SUPPORTED_KINDS = ("seed",)
PLANNED_KINDS = ("batch", "fold")
REJECTED_KINDS = {
    "bootstrap": "declare `statistics.resample` instead",
    "permutation": "declare `statistics.null_test` instead",
    "technical": "declare `data.units.measurements` instead",
    "biological": "independent samples are rows in the unit table",
    "holdout": "declare `data.units.holdout` instead",
}


@dataclass(frozen=True)
class Repeat:
    kind: str
    label: str
    seed: int


def _seed_for(digest: str, index: int) -> int:
    payload = f"{digest}|seed|{index}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "big")


def resolve_repeats(config: dict[str, Any], digest: str) -> list[Repeat]:
    levels = ((config.get("replication") or {}).get("repeats")) or []
    if not levels:
        return [Repeat(kind="seed", label="", seed=_seed_for(digest, 0))]
    if len(levels) > 1:
        raise ContractError(
            "nested repeat levels are not supported yet; S3 adds them",
            code="E-REPL-KIND-UNSUPPORTED",
        )
    level = levels[0]
    kind = level.get("kind")
    if kind in REJECTED_KINDS:
        raise ContractError(
            f"`{kind}` is not a repeat kind — {REJECTED_KINDS[kind]}", code="E-REPL-KIND"
        )
    if kind in PLANNED_KINDS:
        raise ContractError(
            f"repeat kind `{kind}` is specified but not implemented in this build",
            code="E-REPL-KIND-UNSUPPORTED",
        )
    if kind not in SUPPORTED_KINDS:
        raise ContractError(f"`{kind}` is not a repeat kind", code="E-REPL-KIND")
    n = int(level.get("n", 1))
    if n < 1:
        # Returning [] here would produce a run with no repeat executions at all,
        # which reads as success. A design that repeats nothing is a declaration error.
        raise ContractError(
            f"`{{kind: seed, n: {n}}}` executes nothing; n must be at least 1",
            code="E-REPL-N",
        )
    repeats = []
    for index in range(n):
        seed = _seed_for(digest, index)
        repeats.append(Repeat(kind="seed", label=f"seed{seed % 100:02d}", seed=seed))
    if len({r.label for r in repeats}) != n:
        repeats = [Repeat(kind="seed", label=f"seed{r.seed}", seed=r.seed) for r in repeats]
    _check_no_collisions(repeats, digest)
    return repeats


def _check_no_collisions(repeats: list[Repeat], digest: str) -> None:
    # Two repeats deriving the same seed are not two repeats: they execute
    # identically and produce the same answer, which would silently understate
    # repeat_spread. A seed is never perturbed to break the tie — that would make
    # the derivation not reproducible from the digest alone — so a collision here
    # is a hard error naming the colliding seed and the digest it came from.
    seeds_seen: dict[int, int] = {}
    for index, r in enumerate(repeats):
        if r.seed in seeds_seen:
            raise ContractError(
                f"repeats {seeds_seen[r.seed]} and {index} both derive seed {r.seed} "
                f"from digest {digest!r}; two repeats cannot share a seed",
                code="E-REPL-SEED-COLLISION",
            )
        seeds_seen[r.seed] = index
    labels_seen: dict[str, int] = {}
    for index, r in enumerate(repeats):
        if r.label in labels_seen:
            raise ContractError(
                f"repeats {labels_seen[r.label]} and {index} both resolve to label "
                f"{r.label!r} from digest {digest!r}; two repeats cannot share a label",
                code="E-REPL-SEED-COLLISION",
            )
        labels_seen[r.label] = index
