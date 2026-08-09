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
    return repeats
