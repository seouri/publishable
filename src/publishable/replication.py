"""Repeat kinds. S1 implements `seed`; S3b adds `batch` and nests it with `seed`;
S3c adds `fold`.

See docs/reference.md § Repeat kinds.
"""

import hashlib
import itertools
import random
from dataclasses import dataclass
from typing import Any

from publishable.errors import ContractError
from publishable.units import Unit

SUPPORTED_KINDS = ("seed", "batch", "fold")
LABEL_JOIN = "_"
"""The separator `cross_levels` composes labels with. `realize_order` groups pairs
by splitting on this same character, so the two must never drift apart — changing
one without the other silently breaks either the composed label or the grouping
that reads it back."""
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
    stratify_by: str | None = None
    """The attribute a `fold` level balances its split on, `None` for every other
    kind and for an unstratified fold.

    Carried on the level rather than read from `replication.repeats` a second time
    where the partition is drawn: `resolve_repeats` is already the single reader of
    a level's declaration — it is what turns `k: all` into a count — and a caller
    walking the repeats list again to find the same level would be a second answer
    to which level is the fold and what it stratifies on."""

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
    if kind in ("batch", "fold"):
        prefix = kind
        return tuple(
            RepeatMember(label=f"{prefix}{i + 1:02d}", seed=s) for i, s in enumerate(seeds)
        )
    labels = [f"seed{s % 100:02d}" for s in seeds]
    if len(set(labels)) != n:
        labels = [f"seed{s}" for s in seeds]
    return tuple(RepeatMember(label=lb, seed=s) for lb, s in zip(labels, seeds, strict=True))


def _fold_k(level: dict[str, Any], fold_basis: int | None, cluster_by: str | None = None) -> int:
    """`k` is an integer >= 2, or `all` for leave-one-out.

    `all` needs the roster, because "as many folds as there are things to leave
    out" is a fact about the cohort rather than the config — which is the whole
    reason reference.md § Repeat kinds prefers it to a hard-coded count.

    `fold_basis` is that count of things to leave out, resolved by the caller
    through `units.fold_basis`: the resolved unit count, or the cluster count when
    `data.units.cluster_by` is declared, since a cluster is indivisible. One number
    rather than a unit count beside a cluster count — two that could disagree, with
    nothing to catch it.

    `cluster_by` names the attribute only so the refusal says which things it
    counted. It comes from the same `config` the levels do, so it cannot introduce
    a second count; nothing here reads a value from it.
    """
    if level.get("stratify_by") is not None:
        raise ContractError(
            "`fold.stratify_by` is specified but not implemented in this build; "
            "stratified partitioning is a second partitioning rule with its own "
            "cross-field checks, and will be honored in a later slice",
            code="E-REPL-FOLD-STRATIFY-UNSUPPORTED",
        )
    k = level.get("k")
    if k == "all":
        if fold_basis is None:
            raise ContractError(
                "`{kind: fold, k: all}` needs the resolved roster to know how many "
                "folds to draw, and none was supplied",
                code="E-REPL-FOLD-K",
            )
        k = fold_basis
    if not isinstance(k, int) or isinstance(k, bool) or k < 2:
        raise ContractError(
            f"`{{kind: fold, k: {k!r}}}` is not a fold count; `k` is an integer >= 2, "
            "or `all` for leave-one-out",
            code="E-REPL-FOLD-K",
        )
    if fold_basis is not None and k > fold_basis:
        if cluster_by:
            raise ContractError(
                f"`{{kind: fold, k: {k}}}` over {fold_basis} clusters of "
                f"`{cluster_by}` would leave a fold with no cluster to test; a cluster "
                "is indivisible, so `k` may not exceed the cluster count — the units "
                "inside one cannot be dealt out to make the folds up",
                code="E-REPL-FOLD-K-TOO-LARGE",
            )
        raise ContractError(
            f"`{{kind: fold, k: {k}}}` over {fold_basis} resolved units would leave a "
            "fold with nothing to test; a fold with no units is a declaration error, "
            "not a small fold",
            code="E-REPL-FOLD-K-TOO-LARGE",
        )
    return k


def _check_count_field(kind: str, level: dict[str, Any]) -> None:
    """Each kind takes its own count field and no other's.

    `reference.md` § Repeat kinds gives a `fold` its `k` and a `seed`/`batch`
    their `n`, and says "and only these". Nothing enforced it, so
    `{kind: fold, k: 2, n: 5}` was read as two folds by the executor and as five
    repeats by `validate`'s budget arithmetic — a declaration that means two
    different things to two readers, with the wrong number of the two written
    into a recorded warning. Refused rather than resolved by precedence:
    silently preferring one reading is what hid it.

    Checked after the kind checks, so an unknown kind still gets `E-REPL-KIND`,
    and before `_fold_k`, so `{kind: fold, n: 5}` is told its `n` was ignored
    rather than that `k: None` is not a fold count.
    """
    wrong = "n" if kind == "fold" else "k"
    right = "k" if kind == "fold" else "n"
    if level.get(wrong) is not None:
        raise ContractError(
            f"`{{kind: {kind}}}` declares `{wrong}: {level[wrong]!r}`, which a "
            f"`{kind}` level does not take — its count is `{right}`. A count the "
            "executor ignores and the budget check believes is one declaration "
            "meaning two different things",
            code="E-REPL-LEVEL-FIELD",
        )


# What a `batch` level may hold. `reference.md` § Repeat kinds gives it `n` and
# "nothing else", and § Validation's "Batch takes no fields" row says the same.
_BATCH_KEYS = frozenset({"kind", "n"})


def _check_batch_keys(kind: str, level: dict[str, Any]) -> None:
    """A `batch` level's keys, closed against `_BATCH_KEYS`.

    Only `batch`. A `seed` level takes `seeds` and a `fold` level takes
    `stratify_by` besides its count, so the same closure over those kinds would
    refuse declarations the document allows.

    Runs after `_check_count_field`, so `{kind: batch, k: 3}` keeps the message
    naming `n` as a batch's count rather than being reported as an unknown key.
    """
    if kind != "batch":
        return
    extra = sorted(k for k in level if k not in _BATCH_KEYS)
    if extra:
        raise ContractError(
            f"`{{kind: batch}}` declares {', '.join(f'`{k}`' for k in extra)}, which a "
            "`batch` level does not take — its only field is `n`. A batch varies "
            "nothing the pipeline declares, so a field on one is read by nobody and "
            "describes a design core does not execute",
            code="E-REPL-LEVEL-FIELD",
        )


def resolve_repeats(
    config: dict[str, Any], digest: str, fold_basis: int | None = None
) -> list[RepeatLevel]:
    """`fold_basis` is how many indivisible things a `fold` may be drawn from —
    `units.fold_basis` of the resolved roster, which is the unit count unless
    `data.units.cluster_by` is declared and the cluster count when it is. The
    caller resolves it because the roster lives there; this reads `cluster_by`
    from `config` only to say which of the two a refusal counted.
    """
    levels = ((config.get("replication") or {}).get("repeats")) or []
    cluster_by = ((config.get("data") or {}).get("units") or {}).get("cluster_by")
    if not isinstance(cluster_by, str) or not cluster_by:
        # A wrongly-typed or empty `cluster_by` is `check_envelope`'s finding and
        # `_check_cluster_by`'s; here it only chooses a noun, and naming a cluster
        # attribute that resolution never read would describe a count nobody took.
        cluster_by = None
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
        if kind not in SUPPORTED_KINDS:
            raise ContractError(f"`{kind}` is not a repeat kind", code="E-REPL-KIND")
        _check_count_field(kind, level)
        _check_batch_keys(kind, level)
        if kind == "fold":
            n = _fold_k(level, fold_basis, cluster_by)
        else:
            n = int(level.get("n", 1))
            if n < 1:
                # Returning [] here would produce a run with no repeat executions at
                # all, which reads as success. A design that repeats nothing is a
                # declaration error.
                raise ContractError(
                    f"`{{kind: {kind}, n: {n}}}` executes nothing; n must be at least 1",
                    code="E-REPL-N",
                )
        # Only a truthy string, and only on a `fold`: an empty or wrongly-typed
        # `stratify_by` names no attribute to balance on and is
        # `_check_fold_stratify_by`'s finding (`E-REPL-FOLD-STRATIFY-UNKNOWN`), so
        # carrying it here would hand the partition a name no unit has a value for.
        # A `stratify_by` on any other kind is a key that level does not take.
        declared_stratum = level.get("stratify_by") if kind == "fold" else None
        resolved.append(
            RepeatLevel(
                kind=kind,
                members=_seed_members(digest, kind, n),
                stratify_by=(
                    declared_stratum
                    if isinstance(declared_stratum, str) and declared_stratum
                    else None
                ),
            )
        )
    kinds = [lv.kind for lv in resolved]
    if len(set(kinds)) != len(kinds):
        raise ContractError(
            f"repeat levels {kinds} declare the same kind twice; labels compose by kind "
            "and dispersion is reported one entry per level, so two levels of one kind "
            "are ambiguous in both",
            code="E-REPL-LEVEL-DUPLICATE",
        )
    _check_batch_is_outermost(resolved)
    for lv in resolved:
        _check_no_collisions(lv, digest)
    return resolved


def _check_batch_is_outermost(levels: list[RepeatLevel]) -> None:
    """A `batch` may only be the outermost level.

    `cross_levels` gives a leaf the *innermost* member's seed, and `_seed_members`
    derives a level's seeds from `digest|kind` alone — which is exactly right when
    `batch` is outer, because `batch01_seed42` and `batch02_seed42` SHOULD draw
    alike (reference.md § A `batch` says *when*, not *what*). Declared the other
    way round it inverts: every `seedNN_batchMM` leaf takes the batch member's
    seed, so the outer `seed` level varies nothing but a directory name while the
    run reports success. `realize_order` inverts too — it finds the batch level by
    kind rather than by position, so it would block on batch while the labels and
    the directory tree say seed is outer.

    Refusing is the fix rather than re-deriving the leaf seed from the whole combo:
    that would break the documented invariant above, which is the entire point of
    the kind. Every design the documents describe nests other levels *inside* a
    batch — the section fixes the outer batch order and shuffles within one — so a
    batch nested inside a seed has no meaning to preserve. Trivially lifted if a
    document ever describes the inverted nesting.
    """
    for position, lv in enumerate(levels):
        if lv.kind == "batch" and position != 0:
            outer = [x.kind for x in levels[:position]]
            raise ContractError(
                f"a `batch` level is declared inside {outer!r}; a batch is a position in "
                "time, so every other level nests within it and `batch` must be the "
                "outermost level. Declared inside another level it varies nothing: every "
                "leaf takes the batch member's seed, so the outer level changes only a "
                "directory name. Swap the levels so `batch` is declared first",
                code="E-REPL-LEVEL-BATCH-INNER",
            )


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
        label = LABEL_JOIN.join(m.label for m in combo if m.label)
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

    The batch level is found by *kind*, not by position, which is only correct
    because `_check_batch_is_outermost` has already refused a `batch` anywhere
    but outermost. Without that refusal a `[seed, batch]` declaration would
    block on batch here while the composed labels and the directory tree said
    seed was outer — the record and the executed order disagreeing about which
    level is which.
    """
    if mode != "randomized":
        return list(pairs)
    batch_level = next((lv for lv in levels if lv.kind == "batch"), None)
    if batch_level is None:
        blocks: list[list[tuple[int, str]]] = [list(pairs)]
    else:
        by_batch: dict[str, list[tuple[int, str]]] = {m.label: [] for m in batch_level.members}
        for pair in pairs:
            # The batch member's label is a segment of the composed leaf label,
            # split on LABEL_JOIN — the same separator `cross_levels` composes
            # with, so this must stay in step with that function. Matching
            # against the resolved members (rather than parsing a fixed prefix)
            # keeps the label FORMAT out of this function.
            member = next(
                (m.label for m in batch_level.members if m.label in pair[1].split(LABEL_JOIN)),
                None,
            )
            if member is None:
                raise ContractError(
                    f"pair {pair!r} does not belong to any resolved batch "
                    f"({[m.label for m in batch_level.members]!r}); realize_order "
                    "requires every pair's label to have been produced by the same "
                    "levels it is passed",
                    code="E-REPL-ORDER-UNRESOLVED",
                )
            by_batch[member].append(pair)
        blocks = [by_batch[m.label] for m in batch_level.members]
    rng = random.Random(order_seed)
    out: list[tuple[int, str]] = []
    for block in blocks:
        shuffled = list(block)
        rng.shuffle(shuffled)
        out.extend(shuffled)
    return out


def fold_members_for(
    levels: list[RepeatLevel], partitions: list[list[Unit]]
) -> dict[str, frozenset[str]] | None:
    """Fold label -> the unit keys in that fold's test partition, or None.

    `None` when no `fold` level is declared, which is what keeps every
    downstream rule — the collapse, attrition, and the failure fraction —
    byte-for-byte identical to a run without folds.
    """
    fold = next((lv for lv in levels if lv.kind == "fold"), None)
    if fold is None:
        return None
    return {
        m.label: frozenset(u.key for u in part)
        for m, part in zip(fold.members, partitions, strict=True)
    }
