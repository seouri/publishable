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
conditions with identical `values` — a baseline row and the matching grid
row — and `expand` deliberately does not dedup them: the baseline is
declared and the grid is mechanical, and reconciling the two is not
`expand`'s job. Per-cell expansion makes that coincidence the ordinary case
rather than the odd one — a baseline fixing `analysis.method: pearson` while
`pearson` is also a `grid` level coincides once per cell of the axes it
leaves free — and the policy is unchanged for the same reason.
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
    selectors: frozenset[str] = frozenset()
    """Which of this condition's `values` paths select *units* rather than set a parameter.

    `runner.resolve_condition_cfg` reads a condition's `values` as "each dotted
    path names a leaf under `parameters`", and for `grid`, `paired`, `sample`,
    `ablate` and a parameter `baseline` that is exactly true. A group cell
    breaks it: § Expansion modes says "a group level is a *set of units*", so
    `{arm: control}` names no parameter at all — laid over `parameters` it would
    invent an `arm` no template declares and carry it into `parameters_hash`,
    which is the opposite of the claim § Expansion modes makes about a group
    axis ("same code, same parameters, different units").

    Carried on the condition rather than re-derived per reader, and set by
    `expand`, which is the only place that knows which mode produced a cell:
    every consumer of `values` needs the same answer, and seven independent
    "is this a group path?" derivations is how six agree and one does not.
    **The readers still ignore it in this build** — teaching them is the next
    task's, and until then the field is a marking with no consequence.
    """

    def __post_init__(self) -> None:
        # `values` is a plain dict handed in by `expand`; without wrapping it, a
        # caller could mutate a condition's values after the fact, or reach back
        # through the dict it originally passed in. The proxy over a copy is what
        # makes `values["x"] = ...` raise rather than silently drift out of sync
        # with `sweep.yaml`, written from these same objects. Same fix as
        # `Unit.attributes` in `units.py`, same reason.
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))
        # Same treatment, one line shorter because the target type is already
        # immutable: the *annotation* says `frozenset`, the constructor accepts
        # whatever it is handed, and a caller passing a plain `set` would keep a
        # live handle on a condition's selector set. Coercing here is what makes
        # the annotation true of every instance.
        object.__setattr__(self, "selectors", frozenset(self.selectors))


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

    `validate._check_sweep` calls this per value of every mode `label_for`
    renders — `grid`, `paired` and `ablate.override` — and reports
    `E-SWEEP-VALUE-UNNAMEABLE`; a `baseline` entry is exempt, because
    `label_for` never joins a baseline's *fixed* values into a label — a
    baseline that fixes every axis renders as the literal `baseline`, and a
    per-cell baseline renders its cell of the axes it left *free* and then the
    literal `baseline`.

    Every value in that cell is an axis value that has been checked here
    already as the axis's own, so the exemption costs nothing. That holds
    because the only axes a baseline can leave free are `grid` and `paired`,
    both of which `_check_sweep` now checks: `sample` cannot be declared beside
    a baseline at all (`E-SWEEP-SAMPLE-BASELINE`), and `ablate` is not an axis
    and composes with none (`E-SWEEP-ABLATE-CROSSED`). It did *not* hold while
    `paired` went unchecked — a free `paired` axis put unchecked values into a
    baseline's rendered cell — which is the half of this claim commit 884959a
    made true rather than the half it deleted.
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


PRODUCT_MODES = ("grid", "paired", "sample", "groups")
"""The modes the condition product is defined over — one half of the partition.

A mode is here when the condition set is a product *across* it rather than a
list appended after it: `grid`, `paired` and `sample` each contribute an axis
of parameter cells, and `groups` contributes an axis of unit arms.

**`groups` produces no conditions in this build.** It is classified here
because that is what it is — § Expansion modes crosses group arms with the
parameter axes — but `_axes` does not read it yet, so a `sweep` declaring
`groups` alone expands to nothing and `validate` refuses it outright
(`E-SWEEP-GROUPS-UNSUPPORTED`). Membership in this tuple is a statement about
the vocabulary, not a claim about what executes today.

This tuple is not what `ablate` may not cross — that is
`PARAMETER_AXIS_MODES`, a strict subset. The two questions were one tuple
until this split, and `groups` is precisely the mode that answers them
differently.
"""

NON_PRODUCT_MODES = ("baseline", "ablate")
"""The modes the product is not taken over — the other half of the partition.

`baseline` fixes values rather than varying them, and `ablate` applies after
the product rather than joining it: § Expansion modes says it "emits `n`
conditions, each one change away from the baseline". Neither multiplies the
condition count by a number of cells.
"""

PARAMETER_AXIS_MODES = ("grid", "paired", "sample")
"""The modes that sweep a *parameter path* — a subset of `PRODUCT_MODES`.

Three places ask this question of a `sweep` block: `_axes` builds the
parameter cells from exactly these, `_swept_paths` collects their paths, and
`validate`'s `E-SWEEP-ABLATE-CROSSED` refuses `ablate` composed with any of
them. The rule § Expansion modes states names no mode ("a second parameter
axis"), so its enforcement should not either.

`groups` is in `PRODUCT_MODES` and deliberately not here: it varies units, not
parameters, which is exactly why § Expansion modes permits `ablate × groups`
and why `E-SWEEP-ABLATE-CROSSED` must not fire on it.

**This tuple is a predicate, not a partition half, so it is not what makes the
vocabulary closed** — `SWEEP_MODES` below is. A mode added to `PRODUCT_MODES`
and forgotten here silently becomes one `ablate` may cross, which is why the
residual `PRODUCT_MODES - PARAMETER_AXIS_MODES` is pinned as a literal in
`tests/test_sweep.py` rather than only its containment.
"""

SWEEP_MODES = PRODUCT_MODES + NON_PRODUCT_MODES
"""The six modes `sweep` may declare, per § Expansion modes.

Derived rather than written out, and this is the load-bearing part: `validate`
reads this set to refuse an unrecognised `sweep` key, so a seventh mode cannot
be used at all until it appears here — and it can only appear here by being
put in `PRODUCT_MODES` or `NON_PRODUCT_MODES`. Whoever adds one therefore has
to say which it is. The alternative — a literal set in `validate` beside a
hand-maintained tuple here — leaves the two free to disagree, with the
composition refusal under-firing silently while every config still validates.

The partition is over the *product* predicate rather than the parameter-axis
one because only the product predicate partitions: `PARAMETER_AXIS_MODES` is a
subset of `PRODUCT_MODES`, so the two together would double-count `grid`,
`paired` and `sample` and could never be a partition of the six.
"""


SELECTOR_MODES = tuple(mode for mode in PRODUCT_MODES if mode not in PARAMETER_AXIS_MODES)
"""The product modes that vary *units* — the residual of the parameter-axis predicate.

Derived rather than written out as `("groups",)`, for the same reason
`SWEEP_MODES` is: `PARAMETER_AXIS_MODES` is already the repo's answer to "does
this mode name a parameter path?", and a second hand-maintained tuple is free
to disagree with it. A product mode added and left out of
`PARAMETER_AXIS_MODES` becomes a selector mode here automatically, which is the
safe direction — its paths are marked as selecting units rather than silently
laid over `parameters`.

The residual is pinned as the literal `{"groups"}` in `tests/test_sweep.py`, so
the derivation cannot quietly become empty.
"""


def selector_paths(sweep: dict[str, Any]) -> list[str]:
    """Every path a `SELECTOR_MODES` mode varies, deduped, in declared order.

    The counterpart to `_swept_paths`, which collects the parameter axes'. Read
    one mode at a time because each has its own shape — today `groups` alone,
    whose entries § Expansion modes fixes as `{by: <axis>, levels: [...]}` in a
    **list** ("`groups` is a list, always … there is no mapping shorthand"), so
    the axis name is each entry's `by`. A second selector mode has to be read
    here explicitly; membership in `SELECTOR_MODES` alone will not find its
    paths.

    Total over malformed input, deliberately, and the same premise as
    `_swept_paths`: `validate` expands inside a `try` because it collects
    findings rather than raising, so a shape fault this function crashed on
    would be a config that validates clean and crashes `run`. A mapping-form
    `groups`, an entry with no `by`, and a bare string entry each contribute no
    selector path rather than an `AttributeError`; refusing them is
    `validate`'s.
    """
    paths: list[str] = []
    for mode in SELECTOR_MODES:
        for entry in sweep.get(mode) or []:
            if not isinstance(entry, dict):
                continue
            by = entry.get("by")
            if isinstance(by, str) and by not in paths:
                paths.append(by)
    return paths


def parameter_axis_modes_present(sweep: dict[str, Any]) -> list[str]:
    """Which of `PARAMETER_AXIS_MODES` this `sweep` declares, in that tuple's order.

    Truthiness, not presence: `init` and a hand-written config alike leave a
    mode as `null` or `{}`, and an empty axis-shaped mode contributes no axis to
    `_axes`, so it is not a second axis for anything to be composed with. An
    empty `grid` has its own refusal (`E-SWEEP-AXIS-EMPTY`) and must not also be
    reported as a composition fault.

    Reads `PARAMETER_AXIS_MODES`, not `PRODUCT_MODES`: its one caller is
    `E-SWEEP-ABLATE-CROSSED`, and the rule it enforces is about a second
    *parameter* axis. A group axis composes with `ablate`.
    """
    return [mode for mode in PARAMETER_AXIS_MODES if sweep.get(mode)]


def _swept_paths(sweep: dict[str, Any]) -> list[str]:
    """Every path any axis-shaped mode sweeps, in declared order —
    `PARAMETER_AXIS_MODES`, read one mode at a time because each has its own
    shape. `groups` is a product mode but not a parameter axis: it sweeps no
    parameter path, so it contributes nothing here.

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
        # Read defensively rather than through `sample_fault`: `expand` calls
        # this on a config no check has cleared yet — `validate` expands inside
        # a `try` precisely because it collects findings rather than raising —
        # and a malformed `sample` must not stop the swept-path list, which is
        # what `label_for` shortens each path against, from being built out of
        # the modes that *are* well-formed. `_sample_cells` is where a malformed
        # `sample` is refused.
        for path in sample["ranges"]:
            if isinstance(path, str) and path not in paths:
                paths.append(path)
    return paths


def removal_value(baseline: Mapping[str, Any], path: str) -> Any:
    """What a `sweep.ablate.remove` entry sets at `path`: `false` for a boolean,
    `null` otherwise.

    Split out of `ablation_changes` so `validate` can ask what a `remove`
    *produces* rather than re-deriving it: § Validation's "Ablation targets" row
    is a rule about the value that lands in the condition's config, and a check
    that reimplemented this rule would be free to disagree with the expansion it
    is checking — the same reason `sample_fault` is shared rather than mirrored.

    The baseline decides, because this module is pure and has no
    `parameter_spec` to consult (see `ablation_changes`). A path the baseline
    does not fix therefore takes the `null` reading, whatever its parameter is —
    which is precisely what makes the produced value, not the declaration, the
    thing worth checking.
    """
    return False if isinstance(baseline.get(path), bool) else None


def ablation_changes(sweep: dict[str, Any]) -> list[dict[str, Any]]:
    """One `{path: value}` change per `ablate` entry, in declared order.

    `ablate` is not an axis, so it produces changes rather than cells: § Expansion
    modes says it "emits `n` conditions, each one change away from the baseline",
    and `expand` applies each of these *after* the product rather than crossing
    them into it.

    `remove` and `override` are read in the order the `ablate` mapping declares
    them, not `remove`-then-`override`, so the condition numbering a reader sees
    is the order they wrote. Any other key is ignored here — `expand` cannot
    refuse, and a typo (`removes:`) is a value-level fault for `validate` to
    report, not a shape one (see `docs/superpowers/spec-defects.md`).

    **What `remove` sets is decided by the baseline's value for that path**, and
    it has to be: § Expansion modes says `remove` "sets a boolean parameter to
    `false` or a nullable one to `null`", which is a fact about the parameter's
    `Param` — and this module is pure, with no template and so no
    `parameter_spec` to consult. The baseline is the one thing `ablate` is
    defined against (§ Validation, "Ablation targets": every removed path is one
    the baseline fixes), so a boolean *there* is what selects `false`; anything
    else takes the nullable reading and sets `null`. A path the baseline does not
    fix takes the same `null` reading, and is `validate`'s to refuse
    (`E-SWEEP-ABLATE-TARGET`, whose second branch asks this function's own
    `removal_value` what a `remove` produces and then asks the parameter's
    `Param` whether it may hold it) rather than this function's to guess at.
    """
    ablate = sweep.get("ablate")
    if not isinstance(ablate, dict):
        return []
    baseline = sweep.get("baseline") or {}
    changes: list[dict[str, Any]] = []
    for key, block in ablate.items():
        if key == "remove":
            for path in block or []:
                changes.append({path: removal_value(baseline, path)})
        elif key == "override":
            for entry in block or []:
                changes.append(dict(entry))
    return changes


def ablated_paths(sweep: dict[str, Any]) -> list[str]:
    """Every path `ablate` changes, deduped, in declared order.

    Deliberately NOT part of `_swept_paths`, which is the axis-shaped modes'
    set: an axis is a thing a baseline can leave free and a thing
    `_baseline_cells` can expand over, and `ablate` is neither — it does not
    multiply and cannot compose with an axis. An ablated path in that set would
    make a legal `override` on a path the baseline does not fix look like an
    unfixed axis, and there are no cells for a baseline to expand over.

    The two places that need it say so themselves instead. `expand` labels
    against the union of both, because `_keys_for` can only shorten a path
    unambiguously when it sees every path in the run — `features.notes` and
    `clinical.notes` both fall back to `notes` otherwise, and two conditions
    would share a label that is also a selector. `cli.command_run` unions it
    into the paths made unreadable at `run`/`summary` scope, for the reason the
    comment there already gives twice over: a path that varies across conditions
    resolves, at those scopes, to a value no condition in the run used.
    """
    paths: list[str] = []
    for change in ablation_changes(sweep):
        for path in change:
            if isinstance(path, str) and path not in paths:
                paths.append(path)
    return paths


def label_for(values: dict[str, Any], swept: list[str], is_baseline: bool) -> str:
    """The label body for one row: its axis values, and `baseline` when it is one.

    A baseline's `values` here are its *cell* of the axes it does not fix — never
    the values it fixes, which is what keeps `check_swept_value`'s exemption
    honest. § Expansion modes shows `00_cohort=derivation__baseline`: the cell
    first, then the literal, joined by the same `AXIS_SEPARATOR` every other axis
    is. A baseline that fixes every axis has an empty cell and stays the bare
    `baseline` — appending the separator to nothing would give `__baseline`, a
    label whose first axis is empty and which no reader would type as a selector.
    """
    keys = _keys_for(swept)
    body = AXIS_SEPARATOR.join(
        f"{keys.get(path, path.rsplit('.', 1)[-1])}={render_value(value)}"
        for path, value in values.items()
    )
    if is_baseline:
        return f"{body}{AXIS_SEPARATOR}baseline" if body else "baseline"
    return body


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


def _baseline_cells(
    axes: list[list[dict[str, Any]]], baseline: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """One cell per combination of the axes `baseline` does not fix, in axis order.

    § Expansion modes states one rule with two cases: "the baseline expands over
    whichever axes it doesn't fix — group axes and parameter axes alike", giving
    "one per cell of the unfixed axes". This function is that rule; `expand`
    turns each cell into a baseline row by laying the fixed values over it.

    A baseline fixing every axis leaves nothing to cross, and
    `itertools.product()` over no axes yields exactly one empty tuple — so the
    first row of the table falls out of the same expression rather than needing
    a branch that could disagree with it. One baseline, empty cell, label
    `baseline`, index 0.

    **An axis counts as fixed when the baseline names *any* path it varies**,
    not only when it names them all. A `paired` or `sample` axis sets several
    paths per cell, and expanding one the baseline half-fixes would have to
    choose between the baseline's declared value and the cell's — discarding a
    declared value either way. Fixing it keeps the baseline's declaration
    authoritative.

    The rule is written for both mode shapes, but only `paired` reaches it from
    a baseline today: `sample` beside a `baseline` is refused outright by
    `E-SWEEP-SAMPLE-BASELINE`, so a baseline cannot half-fix a `sample` axis at
    all. **That refusal is temporary** — it retires with the slice that makes
    the correction family exclude drawn conditions, and this paragraph goes
    stale the day it does. Whether a half-fixed `paired` baseline should be
    legal at all is `validate`'s to say, and today it says nothing.

    **Fixedness is read off the cells' paths, not off the mode's declaration**,
    which decides the empty-axis case: an axis with no cells carries no paths,
    so no baseline can fix it, so it is unfixed and the product over it is
    empty. `expand` therefore returns no conditions at all for an empty `grid`
    list — the same answer it already gave without a baseline, rather than a
    lone baseline row standing in for a design that has no cells. It is
    `E-SWEEP-AXIS-EMPTY` that says why.
    """
    unfixed = [
        axis
        for axis in axes
        if not any(path in baseline for cell in axis for path in cell)
    ]
    cells: list[dict[str, Any]] = []
    for combo in itertools.product(*unfixed):
        cell: dict[str, Any] = {}
        for part in combo:
            cell.update(part)
        cells.append(cell)
    return cells


def expand(config: dict[str, Any]) -> list[Condition]:
    """Ordered conditions: the declared baseline's rows first, then the product of
    every axis, then one condition per `ablate` entry.

    A baseline fixing every axis is one row, condition `00`, exactly as before.
    A baseline fixing only some expands over the rest — one row per cell of the
    unfixed axes, every one of them `is_baseline` — which is § Expansion modes'
    second row and the design it tells a reader to prefer. Those rows come first
    as a block rather than being interleaved into their cells, because the
    product's own numbering is declared-order nested loops (the last axis
    varying fastest) and reordering it to make each cell contiguous would
    renumber every condition in every existing design. § Expansion modes' one
    interleaved example is `ablate × groups`, which no config can reach here:
    `ablate` composes with no axis (`E-SWEEP-ABLATE-CROSSED`) and `groups` is
    not expanded in this build, so an `ablate` sweep has no axes and therefore
    exactly one baseline.

    With no `sweep` block, one condition whose label is None — which is what
    keeps the `conditions/` level out of the artifact tree.

    Two phases, because `ablate` is not an axis: everything axis-shaped is
    crossed into the product, and `ablate` is applied to the result. § Expansion
    modes: it "emits `n` conditions, each one change away from the baseline, and
    it **reads** the baseline rather than re-emitting it — so a declared baseline
    is condition `00` exactly once, never both as `00_baseline` and as an ablate
    row". That reading is why the baseline row is appended once, above, and each
    ablate row starts from a *copy* of the same values.

    A row therefore carries a third thing: the values its label is rendered from.
    For a product row that is the whole cell; for an ablate row it is the one
    change alone, which is what makes `01_labs=false` — the label § Expansion
    modes shows — rather than a label restating every baseline value the
    condition inherited but did not vary.
    """
    sweep = config.get("sweep") or {}
    if not sweep:
        return [Condition(index=0, label=None, values={}, is_baseline=False)]

    rows: list[tuple[dict[str, Any], dict[str, Any], bool]] = []
    baseline = sweep.get("baseline")
    axes = _axes(sweep, sample_seed_for(config))
    if baseline:
        # `dict(baseline)` before anything reads it, so a non-mapping `baseline`
        # raises here as it always has rather than half-expanding: `path in
        # baseline` would happily answer for a string. `_check_shape` refuses
        # that shape fatally, and this is the guard for reaching `expand`
        # without it.
        fixed = dict(baseline)
        for cell in _baseline_cells(axes, fixed):
            # The cell first, then the fixed values over it — the fixed values
            # are what the baseline *declares*, so they win any collision, and
            # a cell path can only collide when the baseline half-fixed a
            # multi-path axis (see `_baseline_cells`). The cell alone is what
            # the label is rendered from: `sex=f__baseline` names the cell this
            # reference belongs to, and restating the fixed values would name
            # the condition by what every row in the run holds constant.
            row_values = dict(cell)
            row_values.update(fixed)
            rows.append((row_values, cell, True))

    if axes:
        # `itertools.product` varies its LAST argument fastest, which is the
        # declared-order nesting the specification asks for. Preserved from the
        # grid-only implementation this replaces.
        for combo in itertools.product(*axes):
            values: dict[str, Any] = {}
            for cell in combo:
                values.update(cell)
            rows.append((values, values, False))

    for change in ablation_changes(sweep):
        # `dict(baseline or {})` first, then the change: an ablation is the
        # baseline with one thing different, so it has to carry the baseline's
        # other values — a row holding the change alone would leave every other
        # parameter at the base config's value and measure two differences at
        # once. `validate` refuses `ablate` without a `baseline`; expanding one
        # anyway (as the change alone) keeps this function total.
        ablated = dict(baseline or {})
        ablated.update(change)
        rows.append((ablated, dict(change), False))

    # The union, not `_swept_paths` alone: `_keys_for` shortens each path to a
    # suffix unique among the ones it is *shown*, so an ablated path missing here
    # falls back to `label_for`'s last-segment rule and two paths ending in the
    # same segment produce one label for two conditions. See `ablated_paths` for
    # why the union is taken here rather than inside `_swept_paths`.
    swept = _swept_paths(sweep)
    swept += [path for path in ablated_paths(sweep) if path not in swept]
    # Not unioned into `swept`: a group path is not a swept parameter path, and
    # `_keys_for` shortening one more path would move labels task 5 owns
    # (§ How artifacts are organized orders group axes before parameter ones).
    selectors = selector_paths(sweep)
    return [
        Condition(index=i, label=label_for(labelled, swept, is_baseline),
                  values=values, is_baseline=is_baseline,
                  # Per row, not per sweep: a group path reaches a row's values
                  # only when that row's cell or baseline actually fixed it, and
                  # a row of parameter cells alone must mark nothing.
                  selectors=frozenset(p for p in values if p in selectors))
        for i, (values, labelled, is_baseline) in enumerate(rows)
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
