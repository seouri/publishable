"""Repeat kinds. S1 implements `seed`; S3b adds `batch` and nests it with `seed`.

`fold` is still unimplemented.

See docs/reference.md § Repeat kinds.
"""

import hashlib
import itertools
import random
from dataclasses import dataclass
from typing import Any

from publishable.errors import ContractError

SUPPORTED_KINDS = ("seed", "batch")
MAX_LEVELS = 2
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


@dataclass(frozen=True)
class RepeatMember:
    label: str
    seed: int


@dataclass(frozen=True)
class RepeatLevel:
    kind: str
    members: tuple[RepeatMember, ...]

    @property
    def n(self) -> int:
        return len(self.members)


def _seed_for(digest: str, index: int) -> int:
    payload = f"{digest}|seed|{index}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "big")


def _seed_members(digest: str, kind: str, n: int) -> tuple[RepeatMember, ...]:
    """`seed` members carry their value in the label; `batch` members are positional.

    A batch varies nothing the pipeline declares, so its label says *which* block
    it is, not what was drawn for it — see reference.md § A `batch` says *when*,
    not *what*. It still carries a seed, because a step at batch scope still needs
    a stream to draw from.
    """
    seeds = [_seed_for(f"{digest}|{kind}", i) for i in range(n)]
    if kind == "batch":
        return tuple(RepeatMember(label=f"batch{i + 1:02d}", seed=s) for i, s in enumerate(seeds))
    labels = [f"seed{s % 100:02d}" for s in seeds]
    if len(set(labels)) != n:
        labels = [f"seed{s}" for s in seeds]
    return tuple(RepeatMember(label=lb, seed=s) for lb, s in zip(labels, seeds, strict=True))


def resolve_repeats(config: dict[str, Any], digest: str) -> list[RepeatLevel]:
    levels = ((config.get("replication") or {}).get("repeats")) or []
    if not levels:
        return [
            RepeatLevel(kind="seed", members=(RepeatMember(label="", seed=_seed_for(digest, 0)),))
        ]
    if len(levels) > MAX_LEVELS:
        raise ContractError(
            f"{len(levels)} repeat levels are declared; this build supports at most "
            f"{MAX_LEVELS}, and every design the documents describe is two deep",
            code="E-REPL-LEVEL-DEPTH",
        )
    resolved: list[RepeatLevel] = []
    for level in levels:
        kind = level.get("kind")
        if kind in REJECTED_KINDS:
            raise ContractError(
                f"`{kind}` is not a repeat kind — {REJECTED_KINDS[kind]}", code="E-REPL-KIND"
            )
        if kind == "fold":
            raise ContractError(
                "repeat kind `fold` is specified but not implemented in this build; it "
                "changes what `io.units` hands a step and how per-unit values combine, "
                "and will be honored in a later slice",
                code="E-REPL-FOLD-UNSUPPORTED",
            )
        if kind not in SUPPORTED_KINDS:
            raise ContractError(f"`{kind}` is not a repeat kind", code="E-REPL-KIND")
        n = int(level.get("n", 1))
        if n < 1:
            # Returning [] here would produce a run with no repeat executions at all,
            # which reads as success. A design that repeats nothing is a declaration error.
            raise ContractError(
                f"`{{kind: {kind}, n: {n}}}` executes nothing; n must be at least 1",
                code="E-REPL-N",
            )
        resolved.append(RepeatLevel(kind=kind, members=_seed_members(digest, kind, n)))
    kinds = [lv.kind for lv in resolved]
    if len(set(kinds)) != len(kinds):
        raise ContractError(
            f"repeat levels {kinds} declare the same kind twice; labels compose by kind "
            "and dispersion is reported one entry per level, so two levels of one kind "
            "are ambiguous in both",
            code="E-REPL-LEVEL-DUPLICATE",
        )
    for lv in resolved:
        _check_no_collisions(lv, digest)
    return resolved


def cross_levels(levels: list[RepeatLevel]) -> list[Repeat]:
    """Cross the levels outer-to-inner into one leaf per execution.

    The inner level varies fastest, so the sequence reads like nested loops
    written in declaration order — the same rule `sweep.expand` follows for
    conditions. A leaf takes the innermost level's kind and seed because the
    inner level is what differs between consecutive executions.
    """
    leaves: list[Repeat] = []
    inner = levels[-1]
    for combo in itertools.product(*[lv.members for lv in levels]):
        label = "_".join(m.label for m in combo if m.label)
        leaves.append(Repeat(kind=inner.kind, label=label, seed=combo[-1].seed))
    return leaves


def _check_no_collisions(level: RepeatLevel, digest: str) -> None:
    # Within one level, two members deriving the same seed are not two repeats:
    # they execute identically and would silently understate dispersion. Across
    # levels, a shared seed is correct — a `batch` varies nothing the pipeline
    # declares, so batch01_seed42 and batch02_seed42 SHOULD draw alike.
    seeds_seen: dict[int, int] = {}
    labels_seen: dict[str, int] = {}
    for index, m in enumerate(level.members):
        if m.seed in seeds_seen:
            raise ContractError(
                f"{level.kind} members {seeds_seen[m.seed]} and {index} both derive seed "
                f"{m.seed} from digest {digest!r}; two repeats cannot share a seed",
                code="E-REPL-SEED-COLLISION",
            )
        seeds_seen[m.seed] = index
        if m.label in labels_seen:
            raise ContractError(
                f"{level.kind} members {labels_seen[m.label]} and {index} both resolve to "
                f"label {m.label!r} from digest {digest!r}; two repeats cannot share a label",
                code="E-REPL-SEED-COLLISION",
            )
        labels_seen[m.label] = index


def order_seed_for(digest: str) -> int:
    """From the design digest, never from `parameters_hash`.

    Editing any parameter would otherwise redraw the execution order of a run
    that varied nothing about it — see reference.md § What auto-derives from.
    """
    return _seed_for(f"{digest}|order", 0)


def realize_order(
    pairs: list[tuple[int, str]],
    levels: list[RepeatLevel],
    mode: str,
    order_seed: int,
) -> list[tuple[int, str]]:
    """Shuffle within each batch; never across them.

    A batch is a position in time, so shuffling batches against each other would
    destroy the thing being declared. With no `batch` level the whole run is one
    block, because there is no boundary to shuffle inside.
    """
    if mode != "randomized":
        return list(pairs)
    batch_level = next((lv for lv in levels if lv.kind == "batch"), None)
    if batch_level is None:
        blocks: list[list[tuple[int, str]]] = [list(pairs)]
    else:
        by_batch: dict[str, list[tuple[int, str]]] = {m.label: [] for m in batch_level.members}
        for pair in pairs:
            # The batch member's label is a segment of the composed leaf label;
            # matching against the resolved members keeps the label FORMAT out
            # of this function, so changing it cannot silently regroup a run.
            member = next(m.label for m in batch_level.members if m.label in pair[1].split("_"))
            by_batch[member].append(pair)
        blocks = [by_batch[m.label] for m in batch_level.members]
    rng = random.Random(order_seed)
    out: list[tuple[int, str]] = []
    for block in blocks:
        shuffled = list(block)
        rng.shuffle(shuffled)
        out.extend(shuffled)
    return out
