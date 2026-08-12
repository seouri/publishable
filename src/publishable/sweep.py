"""Sweep expansion. See docs/reference.md § Expansion modes.

Pure: a config dict in, an ordered condition list out. No filesystem, no
`Config` object, no git — expansion is a function of the declaration alone,
so it can be tested exhaustively without a repository. Importing
`publishable.errors` keeps that: it has no dependencies and no I/O of its own.
`publishable.hashes.design_digest` is the same kind of import for the same
reason — it is a pure function of the config dict (`hashes.py` reads a file
only in `code_hash`, which nothing here calls), and `sweep.sample` needs it
because § Expansion modes derives the sample seed from the design digest.
Taking a digest *parameter* instead would push that derivation onto every
caller of `expand`, which is the drift this module exists to prevent.

A `baseline` whose values happen to coincide with a grid cell produces two
conditions with identical `values` — `00_baseline` and the matching grid
row — and `expand` deliberately does not dedup them: the baseline is
declared and the grid is mechanical, and reconciling the two is not
`expand`'s job.
"""

import hashlib
import itertools
import math
import random
import re
import warnings
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

from publishable.errors import ContractError
from publishable.hashes import design_digest

if TYPE_CHECKING:
    from publishable.replication import Repeat, RepeatLevel
    from publishable.units import Unit


@dataclass(frozen=True)
class Condition:
    index: int
    label: str | None
    values: Mapping[str, Any] = field(default_factory=dict)
    is_baseline: bool = False

    def __post_init__(self) -> None:
        # `values` is a plain dict handed in by `expand`; without wrapping it, a
        # caller could mutate a condition's values after the fact, or reach back
        # through the dict it originally passed in. The proxy over a copy is what
        # makes `values["x"] = ...` raise rather than silently drift out of sync
        # with `sweep.yaml`, written from these same objects. Same fix as
        # `Unit.attributes` in `units.py`, same reason.
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))


SWEPT_VALUE_PATTERN = r"^[A-Za-z0-9._+-]+$"


def render_value(value: Any) -> str:
    """As written in the config: `true`/`false` for booleans, shortest round-trip float."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return repr(value)
    return str(value)


# The axis separator in a label. Kept as a module-level name — not inlined
# as a literal in `label_for` and `check_swept_value` — because both places
# that care about it must agree on what it is: the separator `label_for`
# joins axes with is exactly the substring `check_swept_value` refuses.
AXIS_SEPARATOR = "__"


def check_swept_value(value: Any) -> str | None:
    """None if `value` is safe to render into a condition label; otherwise why not.

    `docs/reference.md` § How artifacts are organized states two rules that
    cannot both hold for every value: a swept value must render as
    `SWEPT_VALUE_PATTERN` (which admits `_`), and axes in a label are joined
    by `__`. A rendered value containing `__` — e.g. `a__b` — passes the
    pattern but destroys the separator: `one=a__b__two=c` splits into three
    axes instead of two. Since a label is also a selector (a hypothesis's
    `compare.condition`, a contrast's `of`/`against`, and a `report` filter
    all name conditions by parsing the label's body back into axes), this
    resolves the conflict by refusing the value rather than the character —
    `_` alone stays legal.

    `validate._check_sweep` calls this per swept `grid` value and reports
    `E-SWEEP-VALUE-UNNAMEABLE`; a `baseline` entry is exempt, because
    `label_for` renders a baseline condition as the literal `baseline` and
    never joins its fixed values into a label.
    """
    rendered = render_value(value)
    if not re.match(SWEPT_VALUE_PATTERN, rendered):
        return f"swept value {rendered!r} does not match {SWEPT_VALUE_PATTERN}"
    if AXIS_SEPARATOR in rendered:
        return (
            f"swept value {rendered!r} contains {AXIS_SEPARATOR!r}, the separator "
            "between axes in a condition label; a label is also a selector, so a "
            "value containing the separator would produce a label that cannot be "
            "parsed back into axes"
        )
    return None


def _keys_for(paths: list[str]) -> dict[str, str]:
    """The shortest suffix of each dotted path that is unique among them all.

    A label is also a selector, so the key has to be something a reader can
    type without opening the directory — but it must still identify one axis.
    """
    keys: dict[str, str] = {}
    for path in paths:
        segments = path.split(".")
        for depth in range(1, len(segments) + 1):
            candidate = ".".join(segments[-depth:])
            others = [p for p in paths if p != path]
            if not any(p == candidate or p.endswith("." + candidate) for p in others):
                keys[path] = candidate
                break
        else:
            keys[path] = path
    return keys


SAMPLE_METHODS = ("sobol", "latin_hypercube", "random")
SAMPLE_RANGE_FORMS = ("uniform", "int_uniform", "log_uniform")
_DEFAULT_SAMPLE_METHOD = "random"


def sample_fault(sample: Any) -> str | None:
    """None if `sweep.sample` can be drawn from; otherwise why not, as one message.

    Total over arbitrary input on purpose. Two callers need the same answer from
    two ends: `validate._check_sweep` reports it as `E-SWEEP-SAMPLE-INVALID`
    before anything executes, and `_sample_cells` raises on it so a config that
    reached `expand` some other way fails with a coded error rather than an
    `AttributeError` out of the drawing code. `validate` swallows expansion
    crashes on the premise that its own checks report them, so a fault this
    function cannot name is a config that validates clean and crashes `run` —
    the class this project keeps having to close. Every operation `_sample_cells`
    performs on `sample`-derived data is gated here: the `n` it draws, the
    `method` it dispatches on, the `seed` it either pins or derives, the
    `ranges` mapping it iterates, each path it uses as a dict key and splits in
    `_keys_for`, each entry's single form key, and both bounds it scales through.

    Shape faults are *also* refused by `validate._check_shape` under
    `E-CONFIG-SHAPE`, fatally, which is where a wrong-typed block belongs and
    where a reader of the other modes' guards will look. That overlap is
    deliberate: `_check_shape`'s guard is what a user sees, this one is what
    keeps `expand` from crashing when it is reached without one.
    """
    if not isinstance(sample, dict):
        return f"is a {type(sample).__name__} (`{sample!r}`); expected a mapping"

    n = sample.get("n")
    if n is None:
        return "declares no `n`, so there is no number of conditions to draw"
    if not isinstance(n, int) or isinstance(n, bool):
        return f"`n` is `{n!r}`; expected an integer"
    if n < 1:
        return f"`n` is {n}; a sample draws at least one condition"

    method = sample.get("method", _DEFAULT_SAMPLE_METHOD)
    if method is not None:
        if not isinstance(method, str):
            return f"`method` is `{method!r}`; expected a string"
        if method not in SAMPLE_METHODS:
            return f"`method` is `{method}`; the methods are {' | '.join(SAMPLE_METHODS)}"

    seed = sample.get("seed", "auto")
    pinned = isinstance(seed, int) and not isinstance(seed, bool)
    if seed is not None and seed != "auto" and not pinned:
        return (
            f"`seed` is `{seed!r}`; a sample seed is `auto` — derived from the design "
            "digest — or a pinned integer"
        )

    ranges = sample.get("ranges")
    if not isinstance(ranges, dict):
        if ranges is None:
            return "declares no `ranges`, so there is nothing to draw over"
        return f"`ranges` is a {type(ranges).__name__} (`{ranges!r}`); expected a mapping"
    if not ranges:
        return "declares an empty `ranges`, so there is nothing to draw over"

    for path, spec in ranges.items():
        if not isinstance(path, str):
            return f"`ranges` key `{path!r}` is not a string, so it is not a parameter path"
        if not isinstance(spec, dict):
            return f"`ranges.{path}` is a {type(spec).__name__} (`{spec!r}`); expected a mapping"
        if len(spec) != 1:
            return (
                f"`ranges.{path}` declares {len(spec)} forms "
                f"({', '.join(repr(k) for k in spec) or 'none'}); a range is exactly one of "
                f"{' | '.join(SAMPLE_RANGE_FORMS)}"
            )
        form, bounds = next(iter(spec.items()))
        if not isinstance(form, str) or form not in SAMPLE_RANGE_FORMS:
            return (
                f"`ranges.{path}` declares `{form!r}`; the forms are "
                f"{' | '.join(SAMPLE_RANGE_FORMS)}"
            )
        if not isinstance(bounds, list) or len(bounds) != 2:
            return f"`ranges.{path}.{form}` is `{bounds!r}`; expected a list of two bounds"
        low, high = bounds
        for bound in bounds:
            if isinstance(bound, bool) or not isinstance(bound, int | float):
                return f"`ranges.{path}.{form}` bound `{bound!r}` is not a number"
        if low >= high:
            return (
                f"`ranges.{path}.{form}` is [{low}, {high}]; the lower bound must be below "
                "the upper one"
            )
        if form == "int_uniform" and (int(low) != low or int(high) != high):
            return f"`ranges.{path}.int_uniform` is [{low}, {high}]; both bounds must be integers"
        if form == "log_uniform" and low <= 0:
            return (
                f"`ranges.{path}.log_uniform` is [{low}, {high}]; a log-uniform range is drawn "
                "in the log of its bounds, so both must be above zero"
            )
    return None


def _sample_seed(digest: str, index: int = 0) -> int:
    """The seed a sample draws from, derived from the design digest.

    Same construction as `replication._seed_for`, with `|sample|` in place of
    `|seed|` so a draw and a repeat seed derived from one digest never collide.
    """
    payload = f"{digest}|sample|{index}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "big")


def sample_seed_for(config: dict[str, Any]) -> int | None:
    """The seed `sweep.sample` draws with, or None when nothing draws.

    Public because `cli.py` records it in `sweep.yaml` beside the realized
    conditions, and a second derivation of this number is how the recorded seed
    and the executed draw come apart.

    A pinned integer is returned literally and the digest is not computed at
    all: § What `auto` derives from says "an omitted `seed` is `auto`, not an
    error … pinning an integer is the deliberate act, and the one to take for
    anything you intend to cite", so a pinned sample must draw the same
    conditions whatever the roster does.

    The digest is computed only when a `sample` is declared, and only on the
    `auto` path. `design_digest` json-dumps `data.units`, which is arbitrary
    user YAML — a bare date parses as `datetime.date` and is not JSON
    serializable — so the narrower call is the cheaper exposure.

    **The `TypeError` conversion below is defensive, not the user-visible
    route, and saying so is the point of this paragraph.** `cli.command_run`
    computes `design_digest(doc)` itself at phase 5, before `expand` is ever
    called, so on the run path that same bad date raises there first, as a bare
    traceback, for any config at all — a pre-existing crash independent of
    `sweep.sample` and recorded in `docs/superpowers/spec-defects.md`. What the
    conversion buys is this module's own contract: `expand` is public and
    documented to raise `PublishableError`, and a caller reaching it without
    going through `cli` (a test, a future tool) gets a coded error rather than
    a `TypeError` from a hashing helper it never called.
    """
    sample = (config.get("sweep") or {}).get("sample")
    if not sample:
        return None
    declared = sample.get("seed", "auto") if isinstance(sample, dict) else "auto"
    if isinstance(declared, int) and not isinstance(declared, bool):
        return declared
    try:
        digest = design_digest(config)
    except TypeError as exc:
        raise ContractError(
            f"`data.units` or `sweep.groups` holds a value the design digest cannot be "
            f"computed over ({exc}), and `sweep.sample` derives its seed from that digest",
            code="E-SWEEP-SAMPLE-INVALID",
        ) from exc
    return _sample_seed(digest)


def _scaled(form: str, draw: float, low: float, high: float) -> Any:
    """One unit-hypercube coordinate mapped into one declared range.

    Returns a plain `int`/`float`, never a NumPy scalar: a condition's `values`
    are written to `sweep.yaml` with `yaml.safe_dump`, which refuses one.
    """
    if form == "int_uniform":
        # Inclusive of both endpoints, which is why the span is `high - low + 1`
        # and the result is clamped: a draw of exactly 1.0 would otherwise land
        # one past `high`.
        return min(int(low) + int(draw * (int(high) - int(low) + 1)), int(high))
    if form == "log_uniform":
        return float(math.exp(math.log(low) + draw * (math.log(high) - math.log(low))))
    return float(low) + draw * (float(high) - float(low))


def _sample_cells(sample: Any, seed: int) -> list[dict[str, Any]]:
    """`n` realized draws over the declared ranges, as one axis's cells.

    Deterministic given `seed`, which is what § Expansion modes promises and
    what lets `sweep.yaml` record the seed beside the conditions rather than a
    reader re-deriving them.

    `sobol` and `latin_hypercube` come from `scipy.stats.qmc`, a declared
    dependency; `random` is the standard library's generator. Both scipy
    engines are scrambled (the default), which is what makes
    the seed matter at all — an unscrambled Sobol sequence is the same points
    for every seed.

    **`n` is drawn exactly, including when it is not a power of two.** scipy
    warns there that Sobol's balance properties need one; that warning is about
    the uniformity of the sequence, not about correctness, and `n` is the
    condition count — billed against `limits.max_executions`, printed by
    `dry-run`, and recorded as the design. Rounding it would execute a
    different experiment than the one declared, so the warning is suppressed
    around that one call and the count stands.
    """
    fault = sample_fault(sample)
    if fault is not None:
        raise ContractError(f"`sweep.sample` {fault}", code="E-SWEEP-SAMPLE-INVALID")

    ranges: dict[str, Any] = sample["ranges"]
    paths = list(ranges)
    n = sample["n"]
    method = sample.get("method") or _DEFAULT_SAMPLE_METHOD
    draws: Any
    if method == "sobol":
        from scipy.stats import qmc

        engine = qmc.Sobol(d=len(paths), seed=seed)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            draws = engine.random(n)
    elif method == "latin_hypercube":
        from scipy.stats import qmc

        draws = qmc.LatinHypercube(d=len(paths), seed=seed).random(n)
    else:
        # `random.Random`, not `numpy.random.default_rng`: this is the one place
        # in `src/` that would import NumPy for a single uniform draw, and the
        # stream only has to be deterministic given the seed — which both are.
        # `stats.py` seeds the same stdlib generator for the same reason.
        rng = random.Random(seed)
        draws = [[rng.random() for _ in paths] for _ in range(n)]

    cells: list[dict[str, Any]] = []
    for row in draws:
        cell: dict[str, Any] = {}
        for path, draw in zip(paths, row, strict=True):
            form, bounds = next(iter(ranges[path].items()))
            cell[path] = _scaled(form, float(draw), bounds[0], bounds[1])
        cells.append(cell)
    return cells


def _swept_paths(sweep: dict[str, Any]) -> list[str]:
    """Every path any axis-shaped mode sweeps, in declared order.

    `label_for` shortens these to unique suffixes, so it needs the whole set:
    a key is only unambiguous against every other swept path, not against one
    mode's. Later modes extend this and nothing else about labelling changes.

    A path may recur across `paired` entries (each entry sets the same keys to
    different values) or even reappear from `grid` in a hand-written config;
    it is added at most once, in the order it was first seen — a duplicate
    would make `_keys_for` compare a path against itself, which is trivially
    "unique" (`p != path` excludes it) and would silently under-disambiguate
    every other path sharing that suffix.
    """
    paths = list(sweep.get("grid") or {})
    for entry in sweep.get("paired") or []:
        for path in entry:
            if path not in paths:
                paths.append(path)
    sample = sweep.get("sample")
    if isinstance(sample, dict) and isinstance(sample.get("ranges"), dict):
        # Read defensively rather than through `sample_fault`: this function is
        # called by `validate._check_unimplemented` on a config no check has
        # cleared yet, and a malformed `sample` must not stop the swept-path
        # list — which `E-SWEEP-BASELINE-PARTIAL` reads — from being built out
        # of the modes that *are* well-formed. `_sample_cells` is where a
        # malformed `sample` is refused.
        for path in sample["ranges"]:
            if isinstance(path, str) and path not in paths:
                paths.append(path)
    return paths


def label_for(values: dict[str, Any], swept: list[str], is_baseline: bool) -> str:
    if is_baseline:
        return "baseline"
    keys = _keys_for(swept)
    return AXIS_SEPARATOR.join(
        f"{keys.get(path, path.rsplit('.', 1)[-1])}={render_value(value)}"
        for path, value in values.items()
    )


def condition_dir_name(index: int, label: str) -> str:
    """The `<nn>_<label>` name a condition nests under, in `run_dir/conditions/`.

    Single source of truth for the format: `runner.step_dir_for` and
    `artifacts.StepIO.read_condition` both nest here, and a second implementation
    of this string is how they drift apart.
    """
    return f"{index:02d}_{label}"


def _axes(sweep: dict[str, Any], sample_seed: int | None = None) -> list[list[dict[str, Any]]]:
    """One entry per axis-shaped mode present, each a list of `{path: value}` cells.

    The product of these is the condition set. `grid` contributes one axis per
    key; later modes contribute one axis each, whose cells may set several paths
    at once. Keeping every mode in this one list is what makes the composition
    rule — "the product of every axis-shaped mode present" — a property of the
    structure rather than a sentence someone has to remember.
    """
    axes: list[list[dict[str, Any]]] = []
    for path, values in (sweep.get("grid") or {}).items():
        axes.append([{path: value} for value in values])
    paired = sweep.get("paired") or []
    if paired:
        # One axis, not one per key: a paired entry is a single setting that
        # happens to set several paths. Treating its keys as separate axes is
        # exactly the combinatorial reading § Expansion modes rejects.
        axes.append([dict(entry) for entry in paired])
    sample = sweep.get("sample")
    if sample:
        # One axis of `n` realized draws, for the same reason `paired` is one
        # axis: a draw sets every sampled path at once, and the paths are
        # coordinates of one point rather than dimensions to cross. Crossing
        # them would give `n ** d` conditions from a declaration that says `n`.
        if sample_seed is None:
            # Never a fallback seed. A default here would draw a real,
            # reproducible-looking sample from a seed no config derived, and
            # `sweep.yaml` would record a different one beside it.
            raise ContractError(
                "`sweep.sample` is declared but no sample seed was derived; `expand` "
                "derives it from the design digest and is the only caller of `_axes`",
                code="E-SWEEP-SAMPLE-INVALID",
            )
        axes.append(_sample_cells(sample, sample_seed))
    return axes


def expand(config: dict[str, Any]) -> list[Condition]:
    """Ordered conditions: a declared baseline as 00, then the product of every axis.

    With no `sweep` block, one condition whose label is None — which is what
    keeps the `conditions/` level out of the artifact tree.
    """
    sweep = config.get("sweep") or {}
    if not sweep:
        return [Condition(index=0, label=None, values={}, is_baseline=False)]

    rows: list[tuple[dict[str, Any], bool]] = []
    baseline = sweep.get("baseline")
    if baseline:
        rows.append((dict(baseline), True))

    axes = _axes(sweep, sample_seed_for(config))
    if axes:
        # `itertools.product` varies its LAST argument fastest, which is the
        # declared-order nesting the specification asks for. Preserved from the
        # grid-only implementation this replaces.
        for combo in itertools.product(*axes):
            values: dict[str, Any] = {}
            for cell in combo:
                values.update(cell)
            rows.append((values, False))

    swept = _swept_paths(sweep)
    return [
        Condition(index=i, label=label_for(values, swept, is_baseline),
                  values=values, is_baseline=is_baseline)
        for i, (values, is_baseline) in enumerate(rows)
    ]


def sweep_document(
    conditions: list[Condition],
    levels: list["RepeatLevel"],
    repeats: list["Repeat"],
    digest: str,
    order: str,
    execution_order: list[tuple[int, str]],
    order_seed: int | None = None,
    partitions: list[list["Unit"]] | None = None,
    sample_seed: int | None = None,
) -> dict[str, Any]:
    """The `sweep.yaml` payload: the resolved plan, as plain YAML-safe data.

    Matches `docs/reference.md` § "`sweep.yaml` — the resolved plan" exactly.
    `order` and `execution_order` are two different things and stay two
    parameters: `order` is the scalar *mode* (`as_declared` | `randomized`) —
    the rule — while `execution_order` is the realized sequence of
    `(condition index, repeat label)` pairs actually run — the fact. The mode
    is derivable from the config; what happened is not, which is why both are
    recorded rather than one re-deriving the other.

    `order_seed` is the seed `order: randomized`'s shuffle used, and is
    written only when given — its absence under `as_declared` says nothing
    was shuffled, not that the seed was lost. `sample_seed` is the same shape
    for the same reason: § "`sweep.yaml` — the resolved plan" says a `sample`
    sweep adds "the drawn `values` per condition and the seed they came from",
    and the values are already `conditions[].values` — a second copy of them
    is exactly the drift this project keeps finding, so the seed is the only
    addition, absent when nothing drew.

    `levels` and `repeats` are the same design at two grains and both are
    needed. `levels` is the declared structure — one entry per level, outer to
    inner — and is what `repeats:` records, because the nesting is exactly what
    a reader (and `resume`) must not have to recover by splitting label strings
    apart. `repeats` is that structure crossed into leaves, and supplies
    `labels:` alone.

    Each `repeats:` entry carries its kind plus exactly the fields
    `reference.md` § Repeat kinds gives that kind: a `seed` level its resolved
    `seeds`, whether they came from `auto` or were listed explicitly; a `batch`
    level its `n` and nothing else, because a batch has no parameter of its own.
    A level's `seeds` are its own members', never one per execution — under
    `batch` × `seed`, six leaves over two resolved seeds is the documented
    consequence of `batch01_seed42` and `batch02_seed42` drawing alike, and a
    flattened list of six would assert six streams that do not exist.

    `labels` stays the separate, top-level list of each leaf's composed label,
    outer to inner — under a `fold` × `seed` nesting this is where
    `fold03_seed42` appears.

    Fold membership (`partitions`) belongs here too per § The other files a
    run writes. `partitions` is `None` exactly when no `fold` level is
    declared, and the key is omitted rather than written as an empty list —
    an empty list would read as "no folds were drawn", a different claim from
    "this design has no folds". Each entry pairs a fold's label with the unit
    keys on each side: `test` is that fold's own partition, `train` every
    other partition concatenated in fold order — the same train/test split
    `io.units`/`io.units.train` hand a repeat-scope step for that label.
    """
    repeat_entries: list[dict[str, Any]] = []
    for lv in levels:
        if lv.kind == "batch":
            repeat_entries.append({"kind": lv.kind, "n": lv.n})
        else:
            repeat_entries.append({"kind": lv.kind, "seeds": [m.seed for m in lv.members]})

    doc: dict[str, Any] = {
        "design_digest": digest,
        "conditions": [
            {"index": c.index, "label": c.label, "values": dict(c.values),
             "is_baseline": c.is_baseline}
            for c in conditions
        ],
        "repeats": repeat_entries,
        "labels": [r.label for r in repeats],
        "order": order,
        "execution_order": [
            {"condition": index, "repeat": label} for index, label in execution_order
        ],
    }
    if order_seed is not None:
        doc["order_seed"] = order_seed
    if sample_seed is not None:
        doc["sample_seed"] = sample_seed
    if partitions is not None:
        fold = next((lv for lv in levels if lv.kind == "fold"), None)
        if fold is None:
            # Raised rather than asserted: an `assert` disappears under
            # `python -O`, leaving `zip(None.members, ...)` and an
            # `AttributeError` carrying no code. Partitions with no fold level
            # to label them is core's resolved state disagreeing with itself.
            raise ContractError(
                "partitions were drawn but no `fold` level is declared, so there are "
                "no member labels to pair them with",
                code="E-RUN-FOLD-UNRESOLVED",
            )
        doc["partitions"] = [
            {
                "fold": member.label,
                "test": [u.key for u in part],
                # `other is not part` composes `train` by object identity, which is
                # safe rather than incidental: `partition_units` builds a fresh list
                # per fold, so no two entries of `partitions` are the same object
                # even when two folds hold equal units.
                "train": [u.key for other in partitions if other is not part for u in other],
            }
            for member, part in zip(fold.members, partitions, strict=True)
        ]
    return doc
