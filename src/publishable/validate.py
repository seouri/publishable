"""The S1 check subset. Collects rather than stops. docs/reference.md § Validation."""

import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

from publishable.base_experiment import load_experiment
from publishable.contrasts import crossed_group_axes, resolve_contrasts, units_matching
from publishable.correction import ALPHA
from publishable.diagnostics import Collector
from publishable.envelope import check_envelope
from publishable.errors import ContractError
from publishable.hashes import design_digest
from publishable.manifest import POLICIES
from publishable.param import MISSING
from publishable.plugins import GROUPS, names, provider_of, scan_group
from publishable.provenance import find_repo_root, resolves_inside_repo
from publishable.replication import resolve_repeats
from publishable.runner import resolve_wide_cfg
from publishable.scope import step_name as _step_name
from publishable.secrets import credential_values, load_env, missing_env
from publishable.stats import NULL_TEST_METHODS, min_honest_draws, min_honest_permutations
from publishable.strata import levels_for
from publishable.sweep import (
    NAMEABLE_CHAR,
    SWEEP_MODES,
    check_swept_value,
    expand,
    parameter_axis_modes_present,
    removal_value,
    render_value,
    sample_fault,
    selector_paths,
    wide_swept_paths,
)
from publishable.templates.base import BaseTemplate
from publishable.templates.discovery import is_local_template
from publishable.templates.registry import (
    _claims,
    installed_template_message,
    unknown_template_message,
)
from publishable.units import (
    COLLAPSE_RULES,
    DRAWN_ASSIGN_METHODS,
    NUMERIC_COLLAPSE_RULES,
    ArmPlan,
    UnitList,
    assignment_for,
    auto_block_size,
    cell_label,
    cells_of,
    clusters_of,
    fold_basis,
    holdout_seed_for,
    holdout_sizes,
    holdout_values_fault,
    holdout_within_cells,
    is_measurement_numeric,
    null_test_level,
    populated_cells,
    resolve_units,
    rule_for,
    stratum_names,
    stratum_varies_within_cluster,
    thinnest_cell,
    usable_weight,
)

REQUIRED_METADATA = ("description", "authors")

# The shape of every top-level block, checked once before any `_check_*` reads one —
# a property of the config format, not of whichever check happens to read a block
# first. `statistics`, `limits`, and `hypotheses` are included even though nothing
# reads them yet in this build, so the next reader inherits the guard rather than
# the crash a hand-edited config would otherwise produce.
_MAPPING_BLOCKS = (
    "metadata",
    "data",
    "parameters",
    "sweep",
    "replication",
    "statistics",
    "limits",
)
_LIST_BLOCKS = ("hypotheses",)
_STRING_BLOCKS = ("schema_version", "experiment_type", "template_version", "entrypoint", "plugin")

_KIND_LABEL = {
    "mapping": "a mapping",
    "list": "a list",
    "string": "a string",
    "integer": "an integer",
    "number": "a number",
    "string_or_integer": "a string or an integer",
}


def _flatten(node: Any, prefix: str = "") -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for key, value in (node or {}).items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(_flatten(value, path))
        else:
            flat[path] = value
    return flat


def _check_shape(doc: dict[str, Any], c: Collector) -> bool:
    """Every top-level block's type, checked once before any later `_check_*` indexes
    into one. Returns whether the doc is shaped well enough to keep validating —
    `validate_config` returns early when it is not, the same pattern it already uses
    for an unparseable config and an unknown template: every later check indexes into
    these blocks, so continuing would cascade into confusing secondary errors about a
    config whose shape is already known wrong.

    An absent key is not a shape error — optional blocks stay optional, and required
    ones are already reported by their own check. A key present but `null` is treated
    the same as absent, matching the rest of this module (`doc.get("x") or {}`): a
    hand-edited `sweep: null` is not a declaration, and shouldn't become a new kind of
    error just because this check now runs first.
    """
    ok = True

    def _bad(key: str, value: Any, kind: str) -> None:
        nonlocal ok
        c.error(
            "E-CONFIG-SHAPE",
            key,
            f"is a {type(value).__name__} (`{value!r}`); expected {_KIND_LABEL[kind]}",
        )
        ok = False

    for block, kind, isa in (
        *((k, "mapping", dict) for k in _MAPPING_BLOCKS),
        *((k, "list", list) for k in _LIST_BLOCKS),
        *((k, "string", str) for k in _STRING_BLOCKS),
    ):
        value = doc.get(block)
        if value is not None and not isinstance(value, isa):
            _bad(block, value, kind)

    # Nested shapes a later check indexes into directly, folded into the same
    # `E-CONFIG-SHAPE` identifier rather than a second code for one condition. Each
    # container is checked before its items — a container of the wrong shape (a
    # mapping in place of a list, most plausibly a forgotten `-` on `repeats`) must
    # be caught here too, or the per-item loop below is simply skipped and the crash
    # just moves one level down, into whichever `_check_*` reads it next.
    data = doc.get("data")
    if isinstance(data, dict):
        units = data.get("units")
        if units is not None and not isinstance(units, dict):
            _bad("data.units", units, "mapping")
        elif isinstance(units, dict):
            attributes = units.get("attributes")
            if attributes is not None and not isinstance(attributes, list):
                _bad("data.units.attributes", attributes, "list")

    # `sweep`'s two implemented sub-blocks, and each grid axis's value list.
    # `_check_sweep` calls `grid.items()` and `sweep.expand` calls `dict(baseline)`
    # on whatever is here, so a list or a string in either place escaped `main`'s
    # `PublishableError`/`OSError` handler as a bare traceback. The per-axis `list`
    # check closes the quieter version of the same gap: a bare string axis
    # (`analysis.method: spearman`, brackets forgotten) is iterable, so it expanded
    # character by character into one condition per letter.
    sweep = doc.get("sweep")
    if isinstance(sweep, dict):
        baseline = sweep.get("baseline")
        if baseline is not None and not isinstance(baseline, dict):
            _bad("sweep.baseline", baseline, "mapping")
        grid = sweep.get("grid")
        if grid is not None and not isinstance(grid, dict):
            _bad("sweep.grid", grid, "mapping")
        elif isinstance(grid, dict):
            for path, values in grid.items():
                # Same crash as `paired`'s non-string-key guard below, reached
                # through `grid` instead: YAML permits a non-string mapping key
                # (`123: [...]` parses fine), but `_keys_for` feeds every swept
                # path into `.split(".")`, so a non-string `grid` key crashes
                # `AttributeError: 'int' object has no attribute 'split'` before
                # this guard existed. Pre-existing and outside the review's
                # original finding for `paired` — closed here rather than left
                # as the one axis-shaped mode without the guard its sibling has.
                if not isinstance(path, str):
                    _bad("sweep.grid", path, "string")
                    continue
                if values is not None and not isinstance(values, list):
                    _bad(f"sweep.grid.{path}", values, "list")

        # `paired` closes the same gap `grid` does, one level down: `_axes` now
        # reads it unconditionally (`dict(entry) for entry in paired`), so a
        # non-list `paired` or a non-mapping entry escaped as a bare `TypeError`/
        # `ValueError` from `expand`, past `_check_sweep`'s premise that it is the
        # check that reports an expansion crash. Two guards, same shape as
        # `grid`'s: the container, then each entry. Unlike a `grid` axis value —
        # which is used as-is and stays legal as `null` (a param-value question,
        # not a shape one) — every `paired` entry is fed straight into `dict()`,
        # so a `null` entry is itself the crash (`dict(None)` raises `TypeError`)
        # and is refused here rather than treated as absent.
        #
        # A third guard, same reasoning: `dict()` itself tolerates a non-string
        # key (`{123: 30}` parses fine off YAML), but `_swept_paths`/`_keys_for`
        # feed every `paired` key straight into `.split(".")` and an `endswith`
        # scan, both string-only, so `123.split(".")` is the crash — one level
        # further down than the entry-shape guard above, reached only once an
        # entry *is* a mapping. `envelope.py`'s `_check_unknown_keys` faces a
        # structurally similar non-string YAML key and chooses the other
        # route — coerce to `str` and report `E-CONFIG-KEY-UNKNOWN` — but that
        # works there because every leaf sits under a closed, known vocabulary
        # a coerced string can be compared against and reported as unmatched.
        # A `paired` key is an open dotted path into `parameters`, not a member
        # of any closed set `_check_shape` knows here (that resolution is
        # `_check_sweep`'s `E-SWEEP-PATH-UNKNOWN`, reached only for a *string*
        # key); coercing and continuing would just move today's crash one
        # frame deeper for no reporting benefit, so this stays a shape fault —
        # `E-CONFIG-SHAPE`, fatal, consistent with every other guard in this
        # function — rather than `envelope.py`'s coerce-and-report.
        paired = sweep.get("paired")
        if paired is not None and not isinstance(paired, list):
            _bad("sweep.paired", paired, "list")
        elif isinstance(paired, list):
            for i, entry in enumerate(paired):
                if not isinstance(entry, dict):
                    _bad(f"sweep.paired[{i}]", entry, "mapping")
                    continue
                for key in entry:
                    if not isinstance(key, str):
                        _bad(f"sweep.paired[{i}]", key, "string")

        # `ablate` gets the same walk `paired` gets, at every depth
        # `sweep.ablation_changes` reads — enumerated from the operations that
        # function performs, not from inputs someone imagined:
        #   `ablate.items()`                → the block must be a mapping
        #   `for path in remove`            → a list (a bare string iterates
        #                                     character by character into one
        #                                     condition per letter, the quiet
        #                                     failure `grid`'s axis guard closed)
        #   `{path: ...}` then `.split(".")` in `_keys_for` → a string path
        #                                     (a list entry is unhashable and
        #                                     raises at the dict literal; an int
        #                                     is hashable and raises later, in
        #                                     `_keys_for`)
        #   `for entry in override`         → a list, same reasoning
        #   `dict(entry)`                   → a mapping, exactly `paired`'s guard
        #   each override key               → a string, for `_keys_for` again
        # `from` is deliberately absent: `expand` reads `sweep.baseline`
        # directly and performs no operation on `from` at all, so there is no
        # type that makes it raise, and guarding it here would be guessing at
        # inputs rather than closing a crash. A `from` naming anything but
        # `baseline` is a value fault nothing yet reports — recorded in
        # `docs/superpowers/spec-defects.md`. `dict(baseline)` is now read by
        # ablate rows too; its guard is `sweep.baseline`'s above, unchanged.
        ablate = sweep.get("ablate")
        if ablate is not None and not isinstance(ablate, dict):
            _bad("sweep.ablate", ablate, "mapping")
        elif isinstance(ablate, dict):
            remove = ablate.get("remove")
            if remove is not None and not isinstance(remove, list):
                _bad("sweep.ablate.remove", remove, "list")
            elif isinstance(remove, list):
                for i, path in enumerate(remove):
                    if not isinstance(path, str):
                        _bad(f"sweep.ablate.remove[{i}]", path, "string")
            override = ablate.get("override")
            if override is not None and not isinstance(override, list):
                _bad("sweep.ablate.override", override, "list")
            elif isinstance(override, list):
                for i, entry in enumerate(override):
                    if not isinstance(entry, dict):
                        _bad(f"sweep.ablate.override[{i}]", entry, "mapping")
                        continue
                    for key in entry:
                        if not isinstance(key, str):
                            _bad(f"sweep.ablate.override[{i}]", key, "string")

        # `sample` gets the same treatment at every depth `_sample_cells` reads,
        # rather than one guard per input someone thought of: the container, then
        # `n`/`method`/`seed`, then the `ranges` mapping, then each range's path,
        # its single form key, and the two-element bound list the scaling
        # indexes into. Each of these is an operation on user data — a
        # comparison, a `dict` key, a `.split(".")`, a subscript — and each has a
        # YAML-expressible type that makes it raise, which is why the walk is
        # exhaustive over the *shapes* rather than over the examples. `bool` is
        # excluded from `n` deliberately (`n: true` is an `int` to Python and
        # nothing to a reader), and from a bound for the same reason.
        # `sweep.sample_fault` refuses this same family from the other end, so a
        # config reaching `expand` without passing here still gets a coded
        # error; the value-level residue it also names (a `method` outside the
        # enum, `n < 1`, an unknown form, inverted bounds) is `_check_sweep`'s
        # `E-SWEEP-SAMPLE-INVALID`, because those are legal shapes carrying
        # illegal values — the same division `grid` draws between its `list`
        # guard here and `E-SWEEP-AXIS-EMPTY` there.
        sample = sweep.get("sample")
        if sample is not None and not isinstance(sample, dict):
            _bad("sweep.sample", sample, "mapping")
        elif isinstance(sample, dict):
            n = sample.get("n")
            if n is not None and (isinstance(n, bool) or not isinstance(n, int)):
                _bad("sweep.sample.n", n, "integer")
            method = sample.get("method")
            if method is not None and not isinstance(method, str):
                _bad("sweep.sample.method", method, "string")
            seed = sample.get("seed")
            if seed is not None and not isinstance(seed, str | int):
                # Both types, because both are legal: `auto` and a pinned
                # integer (§ What `auto` derives from). Reporting "expected a
                # string" would send a user who wrote `seed: [1]` toward
                # quoting a number.
                _bad("sweep.sample.seed", seed, "string_or_integer")
            ranges = sample.get("ranges")
            if ranges is not None and not isinstance(ranges, dict):
                _bad("sweep.sample.ranges", ranges, "mapping")
            elif isinstance(ranges, dict):
                for path, spec in ranges.items():
                    if not isinstance(path, str):
                        _bad("sweep.sample.ranges", path, "string")
                        continue
                    if not isinstance(spec, dict):
                        _bad(f"sweep.sample.ranges.{path}", spec, "mapping")
                        continue
                    for form, bounds in spec.items():
                        if not isinstance(form, str):
                            _bad(f"sweep.sample.ranges.{path}", form, "string")
                            continue
                        where = f"sweep.sample.ranges.{path}.{form}"
                        if not isinstance(bounds, list):
                            _bad(where, bounds, "list")
                            continue
                        for bound in bounds:
                            if isinstance(bound, bool) or not isinstance(bound, int | float):
                                _bad(where, bound, "number")

        # `groups` gets the same container/entry walk `grid`'s axis-value guard
        # and `paired`'s entry guard get, one level shallower than either needs to
        # go: `sweep._axes` and `selector_paths` both read `entry.get("by")` and
        # `entry.get("levels")` defensively already (a non-dict entry, a
        # non-string `by`, or a non-list `levels` is skipped rather than raised),
        # so nothing here crashes on a malformed block — the failure this guard
        # closes is quieter than a crash: a non-list `groups`, or an entry that
        # skips silently, drops the axis from the product with **no** finding at
        # all, budgeting the parameter-only product as though no axis had been
        # declared. `_check_assign`'s docstring names the one-code overlap this
        # produces with `E-DATA-ALLOCATION-NO-ARMS`/`E-DATA-ASSIGN-MISSING` for a
        # non-string `by` specifically.
        groups = sweep.get("groups")
        if groups is not None and not isinstance(groups, list):
            _bad("sweep.groups", groups, "list")
        elif isinstance(groups, list):
            for i, entry in enumerate(groups):
                if not isinstance(entry, dict):
                    _bad(f"sweep.groups[{i}]", entry, "mapping")
                    continue
                by = entry.get("by")
                if by is not None and not isinstance(by, str):
                    _bad(f"sweep.groups[{i}].by", by, "string")
                elif isinstance(by, str) and not re.search(NAMEABLE_CHAR, by.rsplit(".", 1)[-1]):
                    # Checked on the axis name **as `label_for` renders it** —
                    # `path.rsplit('.', 1)[-1]` — not on `by` whole. Testing
                    # `by` whole left `by: "arm."` open, which renders to
                    # nothing and reaches the exact outcome this refusal exists
                    # to prevent: end to end with a matching `assign` block it
                    # produced labels `=control`/`=treatment`, directories
                    # `00_=control`/`01_=treatment`, and exit 0 with nothing
                    # reported. The rendered name is what a reader sees and
                    # what a directory carries, so it is what the rule is about.
                    #
                    # **An allowlist, not a denylist**, and reusing
                    # `sweep.NAMEABLE_CHAR` — the class `SWEPT_VALUE_PATTERN` is
                    # built from, which § How artifacts are organized already
                    # states as what may be rendered into a label. Two earlier
                    # spellings of one fault got through a denylist: `""` and
                    # `" "` were caught by `strip()`, `"arm."` was not, and a
                    # zero-width space is not caught by `strip()` either
                    # (`'​'.isspace()` is False), so it validated clean and
                    # named directories `00_​=control`. Enumerating what is
                    # forbidden loses that race by construction — there is an
                    # unbounded supply of invisible codepoints and one alphabet
                    # of legal ones. Requiring at least one legal character
                    # closes every spelling, present and future, in one line.
                    #
                    # Deliberately *at least one* rather than
                    # `SWEPT_VALUE_PATTERN`'s full match: a name like
                    # `study arm` renders, resolves, and narrows correctly, and
                    # refusing it is a separate rule about label hygiene that
                    # nobody has argued for. This rule is only about a name with
                    # nothing in it.
                    #
                    # A blank axis name is where `selector_paths` and
                    # `cli._resolved_group_axes` disagree, and the one shape where
                    # that disagreement is not a caller bug but a config anyone can
                    # write: `isinstance(by, str)` accepts `""`, so `expand` renders
                    # conditions under it (`Condition.selectors == {""}`, labels
                    # `=a`/`=b`), while `_resolved_group_axes`' own `not axis` check
                    # skips it. Without an `assign` block of the same name the pair
                    # is caught late, as `E-DATA-ASSIGN-MISSING`; *with* one — and
                    # `data.units.assign` is a bare mapping no schema closes — the
                    # config validates clean and `run` dies on `arm_members`' bare
                    # `KeyError('')`, a traceback out of a command rather than a
                    # diagnostic. A name of only whitespace is refused with it: it
                    # resolves, but it names condition directories (`00_ =control`)
                    # nothing else in this project would produce.
                    #
                    # `ok` is deliberately left alone, unlike every `_bad` above.
                    # `_check_shape`'s return is what makes `validate_config`
                    # give up, and § Errors `validate` reports frames that early
                    # return as a *container*-shape fault: every later check
                    # indexes into a block already known to be the wrong kind, so
                    # continuing would cascade. A blank `by` is a well-typed
                    # string with bad content — nothing downstream indexes into
                    # it, `_check_assign` runs against it without incident (it
                    # reports `E-DATA-ASSIGN-MISSING` for the same config), and
                    # suppressing every other finding over one bad axis name
                    # would cost `validate` the collect-everything contract for
                    # no protection.
                    c.error(
                        "E-CONFIG-SHAPE",
                        f"sweep.groups[{i}].by",
                        f"renders to an axis name with no nameable character (`{by!r}`); "
                        f"expected at least one matching {NAMEABLE_CHAR} — the name "
                        "labels the conditions this axis expands into, names the "
                        "directories they get, and names the `data.units.assign` block "
                        "that fills them",
                    )
                levels = entry.get("levels")
                if levels is not None and not isinstance(levels, list):
                    _bad(f"sweep.groups[{i}].levels", levels, "list")
                elif isinstance(levels, list):
                    for j, level in enumerate(levels):
                        if not isinstance(level, str):
                            _bad(f"sweep.groups[{i}].levels[{j}]", level, "string")

    replication = doc.get("replication")
    if isinstance(replication, dict):
        repeats = replication.get("repeats")
        if repeats is not None and not isinstance(repeats, list):
            _bad("replication.repeats", repeats, "list")
        elif isinstance(repeats, list):
            for i, level in enumerate(repeats):
                if not isinstance(level, dict):
                    _bad(f"replication.repeats[{i}]", level, "mapping")

    # `statistics.contrasts` is read by two `_check_*` functions and by
    # `contrasts.resolve_contrasts`, so it belongs here rather than being guarded
    # three times. Verified against the pre-this-change code directly (not
    # assumed): a scalar here does not currently crash `validate` — `_check_sweep`
    # already contains `resolve_contrasts`'s `TypeError` in a `try/except`, and
    # `_check_contrasts` already has its own `isinstance(entries, list)` guard, so
    # the two together already report `E-STATS-CONTRAST-SHAPE` cleanly. What this
    # block buys instead is what every other entry in this pass buys: one refusal,
    # here, under the shared `E-CONFIG-SHAPE` identifier, so a future third reader
    # of this block inherits the guard rather than needing its own.
    statistics = doc.get("statistics")
    if isinstance(statistics, dict):
        contrasts = statistics.get("contrasts")
        if contrasts is not None and not isinstance(contrasts, list):
            _bad("statistics.contrasts", contrasts, "list")

        report_by = statistics.get("report_by")
        if report_by is not None and not isinstance(report_by, list):
            _bad("statistics.report_by", report_by, "list")

    # The leaf layer, in the same walk as the container layer above: shape and
    # type are one question asked at two depths, and two walks over one document
    # is how the two rules drift apart. Leaf faults are deliberately NOT fatal —
    # `ok` is untouched here. A wrong-typed `metadata.name` must not suppress a
    # `data.input_dir` finding, while a wrong-typed *container* must, because
    # every later check indexes into it.
    for code, field, message in check_envelope(doc):
        c.error(code, field, message)

    return ok


def load_document(config_path: Path, c: Collector | None = None) -> dict[str, Any] | None:
    """Parse the config and confirm it is a mapping — the two things every later check
    presumes. `c` is optional so a caller that only wants the entrypoint out of the file
    (`command_run`, so it can import once rather than twice) can parse without reporting:
    `validate_config` re-parses and reports, and one fault must produce one finding.
    """
    try:
        doc = yaml.safe_load(config_path.read_text())
    except yaml.YAMLError as exc:
        if c is not None:
            c.error("E-CONFIG-PARSE", str(config_path), f"does not parse: {exc}")
        return None
    if not isinstance(doc, dict):
        if c is not None:
            c.error("E-CONFIG-PARSE", str(config_path), "does not parse as a mapping")
        return None
    return doc


def validate_config(
    config_path: Path, c: Collector, *, experiment: Any | None = None
) -> dict[str, Any] | None:
    """Validate one config. `experiment` is the already-imported entrypoint, when the
    caller has one — `command_run` passes what it loaded so a run imports user code once.
    When it is absent and the config names an entrypoint, `validate` imports it itself:
    `W-REPL-DETERMINISTIC` reads `nondeterministic` off the step classes, and warning at
    run time instead would spend exactly the compute the warning is about.
    """
    doc = load_document(config_path, c)
    if doc is None:
        return None

    if not _check_shape(doc, c):
        return None  # every later check indexes into a block already known malformed

    name = doc.get("experiment_type", "")
    try:
        repo_root: Path | None = find_repo_root(config_path)
    except ContractError:
        # No repo at all. That is `_check_data`'s finding to make (or not), and
        # there is no `templates/` to discover locally, so local discovery is
        # skipped rather than reported here — `generic` still resolves as a
        # core template regardless.
        repo_root = None
    # `.env`, once, before the first check that reads the environment —
    # `_check_required_env` below, today, which is what
    # `test_a_required_env_variable_may_be_supplied_by_dot_env` pins. That is
    # weaker than "before `_claims`", and deliberately so: no test
    # distinguishes the two placements, so the stronger claim would be one the
    # suite cannot hold. It is not that resolution is environment-free —
    # `_claims` imports every project-local `templates/*.py`, executing
    # user top level, which may read anything. Loading before that is why the
    # call sits here rather than lower; only the weaker property is pinned.
    # `reference.md` § CLI reference promises `validate` "creates nothing and
    # reaches nothing off the machine"; a file in the repository root is
    # on-machine, so this is inside that promise rather than an exception to it.
    # Never overrides an exported variable — see `secrets.load_env`.
    load_env(repo_root)
    try:
        # One merge, so one local discovery: the known-name list the unknown-name
        # finding prints, and the claim (provenance and provider) an unresolved
        # name's finding reads, both come back from the same call that resolved
        # the name. Asking for any of them separately would import every
        # `templates/*.py` a second time — every user top level executed twice —
        # and, since a later finding is built after this guard closes, a
        # `ContractError` from that second import would escape `validate_config`
        # and discard every other finding.
        claims = _claims(repo_root)
    except ContractError as exc:
        # The load-time refusals resolving a template can make — two codes,
        # `E-TEMPLATE-LOAD` and `E-TEMPLATE-COLLISION`. Two *codes*, not two
        # faults: `E-TEMPLATE-LOAD` covers three shapes of its own (see its
        # § Errors row), and a `Param` whose construction raises — `default=None`
        # without `nullable=True`, or a `requires_env` mapping that is not total
        # over `choices` — is the first of them, "raises while importing". Adding
        # such a fault adds no code and does not move this count. A malformed
        # `parameter_spec` path (`E-TEMPLATE-PARAM-PATH`, `BaseTemplate.__init_subclass__`)
        # raises at the same moment — class-definition time, before `@register_template`
        # or anything else ever sees the class — and folds into the same shape
        # too, but it DOES carry its own code, still readable inside `exc`'s message
        # even though `exc.code` itself reads `E-TEMPLATE-LOAD` here. Reported under
        # the code the raise carries rather than a code chosen here, so the two
        # surfaces stay one fault, and reported at all because `validate` is
        # contracted never to raise. Nothing later can run: which template a name
        # means is exactly what either leaves unanswered.
        #
        # `c.credentials` is normally set below, once `template` resolves — but
        # a load or collision fault means it never will, and the finding just
        # appended can itself carry a raising file's own exception text
        # (`E-TEMPLATE-LOAD` embeds `{exc!r}`). A class body finishes running
        # before `@register_template` or anything else ever sees the class, so a
        # file that raises after registration, or a file that raises while a sibling in
        # the same directory already registered cleanly, still leaves a fully
        # formed class behind — `discover_local`/`_merged` hand it back as
        # `exc.partial_templates` for exactly this. Read the same way a
        # resolved template's declarations are read below, so the set does not
        # drift from `declared_credential_names_for`. A raise from *inside* a
        # class body, before `@register_template` or anything else ever sees the
        # class, leaves no class to read; that residual is `reference.md`'s to describe rather
        # than this call's to close.
        partial = getattr(exc, "partial_templates", None) or []
        names: list[str] = []
        for cls in partial:
            names.extend(declared_credential_names_for(doc, cls))
        c.credentials = credential_values(names)
        c.error(exc.code, "experiment_type", str(exc))
        return None
    claim = claims.get(name)
    template = claim.cls() if claim is not None and claim.cls is not None else None
    known = sorted(claims)
    if template is None:
        if claim is not None and claim.provenance == "installed":
            c.error(
                "E-TEMPLATE-INSTALLED-UNSUPPORTED",
                "experiment_type",
                installed_template_message(name, claim),
            )
        else:
            plugin = doc.get("plugin")
            # The `isinstance(plugin, str) and plugin` guard is unpinned: no
            # config in the suite declares a non-string `plugin` alongside an
            # unresolved `experiment_type`, so a `plugin: 123` rendering
            # "should come from `123`" would go undetected if this guard were
            # deleted. Left rather than fixed with a fixture — recorded here
            # so the gap is not lost (`spec-defects.md`/review M3).
            c.error(
                "E-TEMPLATE-UNKNOWN",
                "experiment_type",
                unknown_template_message(
                    name, known, plugin if isinstance(plugin, str) and plugin else None
                ),
            )
        return None  # every later check reads the spec

    entrypoint = doc.get("entrypoint")
    if experiment is None and isinstance(entrypoint, str) and entrypoint:
        try:
            if repo_root is not None:
                experiment = load_experiment(repo_root, entrypoint)
        except SystemExit as exc:
            # `SystemExit` is a `BaseException`, so the broad `except Exception` below
            # does not see it. A user package calling `sys.exit()` at module scope —
            # or building an `argparse` parser at import — would otherwise end the
            # process with the user's own exit code and no diagnostic at all, which
            # is the one outcome `validate` is contracted never to produce.
            c.error(
                "E-ENTRYPOINT-IMPORT",
                "entrypoint",
                f"could not be imported: SystemExit: {exc.code}",
            )
        except Exception as exc:
            # Deliberately broad. Importing user code can fail every way user code
            # can fail — a syntax error, a missing dependency, a module-scope raise —
            # and `validate` reports rather than raises, so each of those is one
            # finding. Letting any of them propagate would turn a diagnosable config
            # into a traceback, which is the whole reason this import moved earlier.
            #
            # `load_experiment`'s own refusals already say which fault they are, so
            # their wording passes through: a value that is not `<module>:<attribute>`
            # was never imported at all, and framing it as an import failure sends the
            # reader hunting for a missing module rather than a malformed config line.
            own = isinstance(exc, ContractError) and exc.code == "E-ENTRYPOINT-IMPORT"
            c.error(
                "E-ENTRYPOINT-IMPORT",
                "entrypoint",
                str(exc) if own else f"could not be imported: {type(exc).__name__}: {exc}",
            )

    _check_metadata(doc, config_path, template, c)
    _check_entrypoint(doc, c)
    _check_plugin_collisions(c)
    _check_required_env(doc, template, c)
    _check_requires_env(doc, template, c)
    _check_probe(name, template, c)
    # Set once `template` is resolved, so `c.render()` — whenever it is finally
    # called, by `command_validate` or `command_run` — redacts a credential value
    # out of any finding's text, including `E-ENTRYPOINT-IMPORT` above, which is
    # built before this line runs. Redaction happens at render, not at
    # construction (`Diagnostic` is a frozen record with no methods), so setting
    # this after the fact still covers every finding already appended.
    c.credentials = credential_values(declared_credential_names_for(doc, template))
    _check_parameters(doc, template, c)
    _check_versions(doc, template, c)
    _check_data(doc, config_path, c)
    _check_units_source(doc, c)
    roster, technical_n, columns = _check_units(doc, c)
    units_decl = _units_declaration(doc.get("data") or {}, c) or {}
    _check_measurements(units_decl, roster, technical_n, columns, c)
    _check_weight_by(units_decl, roster, c)
    _check_cluster_by(doc, units_decl, roster, c)
    _check_assign(doc, units_decl, roster, c)
    # How many indivisible things a `fold` may be drawn from: the resolved unit
    # count, or the cluster count when `data.units.cluster_by` declares the units
    # are not independent draws (`reference.md` § Validation, *Folds fit inside the
    # clusters*). Resolved once, here, and handed to both checks that need it —
    # `_check_replication` bounds `k` against it and `_check_sweep` sizes a
    # `k: all` budget from it, and a `k` checked against one number while the
    # budget counts another is the drift a single derivation removes.
    #
    # `units.fold_basis` raises `E-DATA-CLUSTER-UNKNOWN` when a unit carries no
    # value for the cluster attribute — the case `_check_cluster_by` above reports
    # from the declaration where it can, and `_check_units` reports for a column
    # that never resolved. This module collects rather than raises, so an
    # unreadable basis becomes `None`: a `k: all` then reports `E-REPL-FOLD-K`
    # (honest — the fold count genuinely cannot be known) beside the cluster
    # finding that explains why.
    declared_cluster = units_decl.get("cluster_by")
    # A wrongly-typed or empty `cluster_by` is reported by `check_envelope` and
    # `_check_cluster_by`; counting clusters by it here would report a second,
    # derived fault on top of the one the reader has to fix anyway.
    usable_cluster = (
        declared_cluster if isinstance(declared_cluster, str) and declared_cluster else None
    )
    # The design's cells, realized here so the basis below is the basis of the
    # cell the fold is actually drawn inside. `None` means *no cell structure*
    # — which is also what a fault means, `_resolved_cells` swallowing every
    # one — and both readings take the roster-wide answer.
    cells = _resolved_cells(doc, units_decl, roster, usable_cluster)
    basis: int | None = None
    # The cell `basis` was counted over, when it was counted over one — the
    # label `replication._fold_k` needs to name the declaration a reader must
    # change, and `None` there means *no cells resolved* rather than *cells
    # resolved and unnamed*. It comes back from the same walk as the number, so
    # the two cannot disagree about which cell the bound bit on.
    basis_cell: tuple[tuple[str, str], ...] | None = None
    if roster is not None:
        try:
            # **Which question this call asks: the FOLD's basis** — how many
            # indivisible things a fold can be drawn from, in the cell that has
            # fewest, because a fold level runs in every cell and the cell that
            # cannot carry `k` is what makes the declaration unaffordable. The
            # `limits.min_clusters` call further down asks a different question
            # of the same function and stays roster-wide; see its own comment,
            # and Decision 4 of
            # `docs/superpowers/specs/2026-08-25-folds-inside-cells-design.md`,
            # whose table states all three call sites' questions in one place.
            #
            # One local, both callers (`_check_replication` bounds `k` against
            # it, `_check_sweep` sizes a `k: all` budget from it), and the
            # substitution is inside the SAME `try`: `thinnest_cell` calls
            # `fold_basis` once per cell, so `E-DATA-CLUSTER-UNKNOWN`
            # propagates from any one of them and an unwrapped call would turn
            # a collecting `validate` into a raising one.
            if cells is not None:
                basis, basis_cell = thinnest_cell(roster, usable_cluster, cells)
            else:
                basis = fold_basis(roster, usable_cluster)
        except ContractError:
            # Swallowed so `validate` keeps collecting. Usually the same fault is
            # reported beside this by `_check_cluster_by` — but **not always, and
            # the difference matters.** `E-DATA-CLUSTER-UNKNOWN` raised here for a
            # unit with no value for the attribute has no validate-time reporter:
            # `_check_cluster_by` tests the declaration against `attributes`, not
            # each unit's value. The reachable case is `cluster_by` naming
            # `measurements.by` where every unit has one measurement row; see
            # `cli`'s note at the `clusters_of` call. With no `fold` level, this
            # `basis` local itself goes unused — but `_check_resample`'s own
            # `limits.min_clusters` check (below) resolves the identical
            # roster/`cluster_by` pair a second time and meets the same
            # `ContractError`, so "nothing downstream needs it" is no longer
            # true in general, only true of this particular local. Either way
            # the config validates clean here and meets `E-DATA-CLUSTER-UNKNOWN`
            # for real at `run`.
            basis = None
            basis_cell = None
    # The holdout's realized test partition, resolved once and threaded — the
    # denominator a resample's cluster count is actually over. Resolved here
    # rather than inside `_check_resample` so a future second reader gets the
    # same object rather than realizing a second draw.
    # The thin-cell floor, over the same decomposition the fold bound and the
    # holdout loop read. Sited beside them rather than inside `_check_assign`
    # because it answers for `limits.min_units_per_cell` — a floor on a
    # realized cell — and not for the `assign` declaration.
    _check_cell_size(doc, roster, cells, c)
    holdout_test = _holdout_test_roster(doc, units_decl, roster, usable_cluster, cells)
    # A `fold` level's `stratify_by`, from the same usable-cluster local the basis
    # was resolved from: the name it declares, and — when a cluster is declared —
    # whether the stratum survives a split that cannot divide one. Not in
    # `replication._fold_k`, which sees the declaration and a count and never a
    # roster.
    _check_fold_stratify_by(doc, units_decl, roster, usable_cluster, c)
    # `usable_cluster` is already narrowed to a non-empty string or `None`
    # above, so this call needs no guard of its own.
    _check_holdout(doc, units_decl, roster, usable_cluster, cells, c)
    _check_replication(
        doc,
        template,
        c,
        experiment=experiment,
        fold_basis=basis,
        fold_cell=basis_cell,
    )
    _check_unimplemented(doc, c)
    _check_sweep(doc, template, c, fold_basis=basis)
    # After `_check_sweep`, before `_check_contrasts`: `roster` is already in
    # hand three calls earlier (`_check_fold_stratify_by` reads it too), so
    # position here buys grouping with the other `statistics.*` checks and a
    # sensible finding order, not roster availability. `_check_sweep` returns
    # `None` and stores nothing on `doc` — it hands nothing forward — so a
    # later check needing the resolved comparison family (task 6's `n` bound
    # against it) must recompute that family locally rather than read it off
    # this call site.
    _check_resample(doc, roster, c, holdout_test=holdout_test)
    _check_null_test(doc, roster, c)
    _check_contrasts(doc, c, roster)
    _check_hypotheses(doc, c, experiment, template)
    _check_report_by(doc, c, roster)
    # `template.validate` is contracted to return `list[str]` (`BaseTemplate.validate`),
    # never to raise — but it is user code, reachable through a project-local
    # `templates/*.py`, and `validate` collects rather than raises. Unguarded, a
    # raise here would propagate out of `validate_config`, out of `_dispatch`, and
    # land in `main`'s bare `except PublishableError`, which prints straight to
    # stderr and bypasses `c.render()` — the one place a credential in the text
    # gets redacted. `c.credentials` is already set above, so catching here keeps
    # this inside the same collector every other `E-TEMPLATE-RULE` finding goes
    # through, rather than opening a second, unredacted exit for the same fault.
    # Mirrors `load_experiment`'s guard above: `SystemExit` is a `BaseException`
    # and would otherwise end the process with the user's own exit code.
    try:
        for message in template.validate(doc):
            c.error("E-TEMPLATE-RULE", "parameters", message)
    except SystemExit as exc:
        c.error(
            "E-TEMPLATE-RULE",
            "parameters",
            f"raised while validating: SystemExit: {exc.code}",
        )
    except Exception as exc:
        c.error(
            "E-TEMPLATE-RULE",
            "parameters",
            f"raised while validating: {type(exc).__name__}: {exc}",
        )
    return doc


def _check_metadata(doc: dict[str, Any], config_path: Path, template: Any, c: Collector) -> None:
    metadata = doc.get("metadata") or {}
    for field in REQUIRED_METADATA:
        if not metadata.get(field):
            c.error("E-META-REQUIRED", f"metadata.{field}", "is empty, and is required")
    name = metadata.get("name", "")
    # `check_envelope` is what REPORTS a wrong-typed `name` (E-CONFIG-TYPE) — this
    # guard exists because this function may be reached without it having run: a
    # leaf fault is deliberately non-fatal to the pass, so `_check_metadata` still
    # executes on the still-malformed `doc`, and `re.match` requires a str/bytes-
    # like second argument. Without this, a list or int name raised `TypeError`
    # out of `validate` for the exact leaf fault this pass exists to turn into a
    # diagnostic instead.
    if name and isinstance(name, str) and not re.match(template.naming_pattern, name):
        c.error(
            "E-NAME-PATTERN",
            "metadata.name",
            f"is `{name}`, which does not match the template's naming_pattern "
            f"{template.naming_pattern}",
        )
    directory = config_path.parent.name
    if name and directory and name != directory:
        c.error(
            "E-NAME-DIR",
            "metadata.name",
            f"is `{name}` under `configs/{directory}/`; the two name one experiment",
        )


def _check_plugin_collisions(c: Collector) -> None:
    """One entry-point key claimed by two installed distributions, outside templates.

    `publishable.templates` needs no skip in the loop below, because this
    function is never reached while one is live: `validate_config` calls
    `_claims(repo_root)` earlier, inside a `try` that returns from the `except
    ContractError` branch on `E-TEMPLATE-COLLISION` — the same merge that
    would raise it — before `_check_plugin_collisions` is ever called. A
    template collision is reported as `E-TEMPLATE-COLLISION` at that earlier
    call, not here. These four groups have no such earlier merge, so their
    collision is a property of the machine's installed set alone, decided
    only when this loop notices it.

    Reported rather than raised, and reported for every config rather than only
    for one naming a colliding key: a registry core cannot make sense of is
    refused however it is asked, which is the same shape `_claims` takes for a
    `templates/` core cannot merge. Read from metadata, so no plugin is imported
    to reach a verdict.
    """
    for group in GROUPS:
        for name, entries in scan_group(group).items():
            if len(entries) > 1:
                who = " and ".join(sorted(provider_of(ep) for ep in entries))
                c.error(
                    "E-PLUGIN-COLLISION",
                    "plugin",
                    f"key `{name}` in the `{group}` entry-point group is claimed by "
                    f"{who} — install order is the only tie-break available and it is "
                    "a property of a machine rather than of a design. Uninstall one",
                )


def _check_entrypoint(doc: dict[str, Any], c: Collector) -> None:
    entrypoint = doc.get("entrypoint")
    if not entrypoint or not isinstance(entrypoint, str):
        c.error(
            "E-ENTRYPOINT-REQUIRED",
            "entrypoint",
            "is empty, and is required — `run` cannot import a step without it",
        )


def _check_required_env(doc: dict[str, Any], template: Any, c: Collector) -> None:
    """The template-level credential set — `reference.md` § Secrets & credentials.

    Read from the class, so it needs no roster and no expansion: a `required_env`
    list says what an experiment *type* always needs, which is the wrong shape
    exactly when the credential follows a choice. That case belongs to
    `_check_requires_env`, below.

    Reported at `experiment_type`, the field that decided which template's list
    applies. The value is never printed — the message names the variable and
    where to put a value, which is the whole of what is safe to say and the whole
    of what a reader needs.
    """
    names = getattr(template, "required_env", None)
    if not isinstance(names, list):
        # Nothing reports a `required_env` that is not a list — this repo has
        # no check for it anywhere — so a template declaring one this way is a
        # silent author mistake rather than a diagnosed one.
        # `declared_credential_names_for`/`cli.declared_credential_names` use
        # this same guard, precisely so a malformed `required_env` is ignored
        # everywhere alike rather than iterated as characters in one place.
        return
    name = doc.get("experiment_type", "")
    for variable in missing_env(str(n) for n in names):
        c.error(
            "E-CRED-MISSING",
            "experiment_type",
            f"template `{name}` requires `{variable}`, which has no value in the "
            "environment or in `.env` — the config records the NAME, so put the value "
            "in `.env` at the repository root",
        )


def _check_requires_env(doc: dict[str, Any], template: Any, c: Collector) -> None:
    """The union over the conditions the sweep actually resolves.

    That union is the entire reason a value carries its own credential
    requirement instead of a template carrying a static list: a config selecting
    Azure and OpenAI must say nothing about Ollama's key, and one selecting none
    of them must say nothing about any. `reference.md` § A credential can belong
    to a parameter value.

    A condition's value is resolved the way `runner.resolve_condition_cfg`
    resolves it — declared parameters, then each of `condition.values` whose path
    is not a **selector**, a group cell naming no parameter at all — computed
    locally rather than by importing the runner, since this needs one path's
    value rather than a whole `Config`.

    A resolved value with no key in the mapping requires nothing. `requires_env`
    is total over `choices`, so that case is exactly the values `choices` does
    not hold: `sweep.ablate.remove` sets a nullable parameter to `null`, which is
    a legal resolved value and not a choice.

    One finding per variable, attributed to the first condition that selected it:
    one missing value is one thing to fix, whatever selected it.
    """
    spec = getattr(template, "parameter_spec", None)
    if not isinstance(spec, dict):
        # A malformed `parameter_spec` (not a dict) is `E-TEMPLATE-LOAD`'s
        # finding to make, not this collector's crash to cause — same
        # guard shape as `required_env` above.
        return
    wanted = {path: p for path, p in spec.items() if getattr(p, "requires_env", None)}
    if not wanted:
        return
    try:
        conditions = expand(doc)
    except Exception:
        # Guarded the same way `_condition_labels` guards its own `expand(doc)`:
        # an unexpandable sweep is `_check_sweep`'s to report, and this module
        # collects rather than raises.
        return
    declared = _flatten(doc.get("parameters"), "")
    # `dict`, so insertion order is condition order then declared-parameter
    # order — a deterministic finding order without sorting away the attribution.
    first_seen: dict[str, tuple[str, Any, str | None]] = {}
    for condition in conditions:
        resolved = dict(declared)
        for path, value in condition.values.items():
            if path in condition.selectors:
                continue
            resolved[path] = value
        for path, param in wanted.items():
            if path in resolved:
                value = resolved[path]
            elif param.default is not MISSING:
                value = param.default
            else:
                continue  # required and absent — `E-PARAM-MISSING`'s finding, not this one
            try:
                needs = param.requires_env.get(value)
            except TypeError:
                continue  # an unhashable resolved value cannot key the mapping
            for variable in needs or []:
                first_seen.setdefault(variable, (path, value, condition.label))
    for variable in missing_env(first_seen):
        path, value, label = first_seen[variable]
        where = f"condition `{label}`" if label else "the base parameters"
        c.error(
            "E-CRED-PARAM-MISSING",
            f"parameters.{path}",
            f"is `{value}` in {where}, which requires `{variable}` — no value in the "
            "environment or in `.env`",
        )


def _check_probe(name: str, template: Any, c: Collector) -> None:
    """The resolved template's `apparatus_probe` against the installed probes.

    Read from package metadata, so a name no distribution declares is refused
    without importing one — the same guarantee every other plugin name is
    answered under. Reported at `experiment_type` because the declaration is the
    template's rather than the config's: a reader who cannot install the plugin
    changes which template the experiment uses, and `experiment_type` is where
    that decision is written.

    Takes the registered name rather than recovering it from the class, which
    cannot be done: a class knows what it was decorated with only until the
    pending buffer is drained, and `validate_config` is holding the name anyway.

    A template declaring no probe is the ordinary case and draws nothing —
    `reference.md` § The apparatus core can only observe: an experiment whose
    measurements never leave the machine declares nothing and records
    `apparatus: null`. `None` is the one documented spelling of that —
    anything else that is not a usable name (a list, an empty string, any
    other non-`str`) is a declaration that disagrees with itself and is
    reported rather than silently read as "no probe": `cli.command_run`
    calls `validate_config` before it ever inspects `apparatus_probe` itself
    and returns before constructing an `Observer` when `c.has_errors`, so
    this is also what keeps `run` from silently skipping a malformed
    declaration the same way — whole-branch review, Major 1.
    """
    declared = getattr(template, "apparatus_probe", None)
    if declared is None:
        return
    if not isinstance(declared, str) or not declared:
        c.error(
            "E-PROBE-UNKNOWN",
            "experiment_type",
            f"resolves template `{name}`, which declares `apparatus_probe` as "
            f"{declared!r} — an `apparatus_probe` name is a non-empty `str`; `null` "
            'is the only spelling of "no probe declared"',
        )
        return
    known = names("publishable.probes")
    if declared in known:
        return
    listed = ", ".join(known) if known else "none installed"
    c.error(
        "E-PROBE-UNKNOWN",
        "experiment_type",
        f"resolves template `{name}`, which declares `apparatus_probe: {declared}` — "
        "a name no installed distribution registers in the `publishable.probes` "
        f"entry-point group (registered: {listed})",
    )


def declared_credential_names_for(doc: dict[str, Any], template: Any) -> list[str]:
    """Every environment variable this config's declarations name.

    The same two collectors `_check_required_env` and `_check_requires_env`
    check for *presence* above, read here for their *values* — deliberately the
    same set, which is what makes the redaction this feeds a fact rather than a
    guess. Not shared as one function with `cli.declared_credential_names`: that
    one takes the `conditions` its caller already expanded, because a second
    `expand(doc)` there would be a second derivation of the plan actually
    executed; this module's every other check (`_check_requires_env`,
    `_check_sweep`, `_check_contrasts`) already re-derives `expand(doc)` locally
    under the same guard, since `validate` collects findings rather than
    threading one resolved plan through them, so re-deriving here matches this
    file's own convention rather than breaking it.

    A `None` template — reached only when `validate_config` already returned
    early, since it never calls this once `template` is `None` — yields the
    empty list, since `getattr(None, ...)` on a missing template answers
    nothing rather than guessing.
    """
    raw_required = getattr(template, "required_env", None)
    # Same guard as `_check_required_env`: nothing reports a `required_env`
    # that is not a list, so it is ignored here alike rather than iterated as
    # characters.
    names: list[str] = list(raw_required) if isinstance(raw_required, list) else []
    spec = getattr(template, "parameter_spec", None)
    if not isinstance(spec, dict):
        # Same guard as `_check_requires_env`: a malformed `parameter_spec`
        # is that check's finding to make, not this collector's crash to
        # cause.
        return names
    wanted = {path: p for path, p in spec.items() if getattr(p, "requires_env", None)}
    if not wanted:
        return names
    try:
        conditions = expand(doc)
    except Exception:
        # Guarded the same way `_check_requires_env` guards its own `expand(doc)`:
        # an unexpandable sweep is `_check_sweep`'s finding to make, not this
        # collector's crash to cause.
        return names
    declared = _flatten(doc.get("parameters"), "")
    for condition in conditions:
        resolved = dict(declared)
        for path, value in condition.values.items():
            if path in condition.selectors:
                continue
            resolved[path] = value
        for path, param in wanted.items():
            if path in resolved:
                value = resolved[path]
            elif param.default is not MISSING:
                value = param.default
            else:
                continue
            try:
                needs = param.requires_env.get(value)
            except TypeError:
                continue
            names.extend(needs or [])
    return names


def _unset_defaulted_paths(doc: dict[str, Any], template: Any) -> list[str]:
    """Every `parameter_spec` path this config leaves to the template's default.

    Shared by `_check_versions` (named only inside `W-TEMPLATE-VERSION`, and
    only under a version mismatch) and `_check_parameters` (named
    unconditionally, as `W-PARAM-UNSET`) — one comprehension, so the two
    readers cannot drift the way two independent copies would.
    """
    set_here = _flatten(doc.get("parameters"), "")
    return [
        path
        for path, param in template.parameter_spec.items()
        if path not in set_here and param.default is not MISSING
    ]


def _check_parameters(doc: dict[str, Any], template: Any, c: Collector) -> None:
    declared = _flatten(doc.get("parameters"), "")
    spec = template.parameter_spec
    for path, value in declared.items():
        param = spec.get(path)
        if param is None:
            import difflib

            near = difflib.get_close_matches(path, list(spec), n=1)
            hint = f" — did you mean `{near[0]}`?" if near else ""
            c.error(
                "E-PARAM-UNKNOWN",
                f"parameters.{path}",
                f"is not a parameter of this template{hint}",
            )
            continue
        problem = param.check(value)
        if problem:
            c.error("E-PARAM-VALUE", f"parameters.{path}", problem)
    for path, param in spec.items():
        if path not in declared and param.default is MISSING:
            c.error("E-PARAM-MISSING", f"parameters.{path}", "is required and absent")
    unset = _unset_defaulted_paths(doc, template)
    if unset:
        c.warn(
            "W-PARAM-UNSET",
            "parameters",
            # The subject of the sentence is the PATH, not the block: every
            # diagnostic here renders as `<path> <message>`, and the path this
            # one carries is `parameters`, which does not itself carry a
            # default — the enumerated paths under it do. Fixed in H6a's
            # whole-branch fix round (Minor 2) and pinned whole below the
            # W-TEMPLATE-VERSION arm in tests/test_validate.py.
            "holds paths that carry a default and are left unset here; a step "
            "reading one as cfg.parameters.<path> raises E-STEP-PARAM-UNKNOWN: "
            f"{', '.join(unset)}",
        )


def _check_versions(doc: dict[str, Any], template: Any, c: Collector) -> None:
    """The moved version, and which parameters this config leaves to a default.

    § Validation's "Template version moved" row reports both halves in one
    warning — the version, and `request.timeout` being unset. The second half
    is computed through `_unset_defaulted_paths`, shared with `_check_parameters`'
    unconditional `W-PARAM-UNSET`, but named here only under a version
    mismatch: a config whose `template_version` matches draws nothing from
    this function, and an omitted parameter with no default is
    `E-PARAM-MISSING`'s to report regardless of any version. The duplication
    with `W-PARAM-UNSET` on a version-mismatched config is deliberate, not an
    oversight — both warnings render in one `Collector` output.

    The message states what is observable — a parameter the installed template
    defaults and this config does not set. Core cannot tell that apart from one
    the author deliberately left at its default, and asserting which it is would
    be a claim the declaration does not carry.

    A local template is skipped regardless of what `template_version` declares,
    and so is any template reporting no version of its own. What a config's
    declared string is compared against is the template's own `version`, read
    off the class: a module constant would be core's answer for a template core
    did not write, which `docs/reference.md` § Three hashes rejects — a
    `template_version` "isn't the answer for a local template — it's a string
    its author remembers to bump."
    """
    if is_local_template(type(template)):
        return
    reported = type(template).version
    declared = doc.get("template_version")
    if reported is None or not declared or declared == reported:
        return
    unset = _unset_defaulted_paths(doc, template)
    detail = f"; unset here and left to the template's default: {', '.join(unset)}" if unset else ""
    c.warn(
        "W-TEMPLATE-VERSION",
        "template_version",
        f"is {declared} but the template reports {reported}{detail}",
    )


def _check_data(doc: dict[str, Any], config_path: Path, c: Collector) -> None:
    data = doc.get("data") or {}

    # Checked first and unconditionally: `input_manifest_policy` has nothing to do
    # with the repo, so it must not be gated behind the repo-existence check below —
    # a repo-less config still has to be one `manifest.build_manifest` can execute.
    policy = data.get("input_manifest_policy")
    if not policy:
        c.error(
            "E-DATA-POLICY",
            "data.input_manifest_policy",
            "is empty, and is required",
        )
    elif policy not in POLICIES:
        c.error(
            "E-DATA-POLICY",
            "data.input_manifest_policy",
            f"is `{policy}`, which is not one of {', '.join(POLICIES)}",
        )

    # `E-DATA-REQUIRED` and `E-DATA-UNREADABLE` have nothing to do with the repo
    # either — same reasoning as the policy check above — so they must not sit
    # behind the repo-existence early return below. Only `E-DATA-IN-REPO`
    # legitimately needs a repo root to compare against.
    resolvable: dict[str, Path] = {}
    for field in ("input_dir", "output_dir"):
        raw = data.get(field)
        if not raw:
            c.error("E-DATA-REQUIRED", f"data.{field}", "is empty, and is required")
            continue
        if not isinstance(raw, str):
            # `check_envelope` is what REPORTS this (E-CONFIG-TYPE) — this guard
            # exists because this function may be reached without it having run:
            # a leaf fault is deliberately non-fatal, so `_check_data` still runs
            # on a still-malformed `doc`, and `Path()` requires a str/PathLike.
            continue
        path = Path(raw).expanduser()
        if not path.is_absolute():
            c.error(
                "E-DATA-NOT-ABSOLUTE",
                f"data.{field}",
                f"is `{raw}`, which is not an absolute path — reference.md requires "
                "input_dir/output_dir to be absolute so the config means the same "
                "location regardless of the directory a command is run from",
            )
            continue
        resolvable[field] = path.resolve()

    input_dir = data.get("input_dir")
    # Same reasoning as the `isinstance` guard above: `check_envelope` reports a
    # wrong-typed `input_dir`, but this function may be reached without it having
    # run, and `Path()` requires a str/PathLike.
    if input_dir and isinstance(input_dir, str):
        path = Path(input_dir).expanduser()
        if not path.is_dir() or not any(path.iterdir()):
            c.error("E-DATA-UNREADABLE", "data.input_dir", f"{path} is unreadable or empty")

    try:
        repo_root = find_repo_root(config_path).resolve()
    except ContractError as exc:
        if exc.code == "E-GIT-NO-REPO":
            return  # not in a repo, so "inside the repo" doesn't arise
        raise
    for field, resolved in resolvable.items():
        if resolves_inside_repo(resolved, repo_root):
            c.error(
                "E-DATA-IN-REPO",
                f"data.{field}",
                f"resolves inside the git repository at {repo_root}",
            )


def _check_units_source(doc: dict[str, Any], c: Collector) -> None:
    """A `data.units.from` mapping may declare `glob` or `resolver`, not both.

    `units.resolve_units` tests for `glob` first, so a mapping carrying both
    keys resolves as a glob and the `resolver` key is never read — silently,
    since neither key is malformed on its own. Refusing the combination
    outright is what stops a config from declaring an intent that dispatch
    would quietly overrule.

    Its own function rather than a branch beside another check, since neither
    the glob-first order it guards against nor the ambiguity itself belongs
    to any one refusal's lifecycle.
    """
    units = _units_declaration(doc.get("data") or {}, c) or {}
    source = units.get("from")
    if isinstance(source, dict) and "glob" in source and "resolver" in source:
        c.error(
            "E-UNITS-SOURCE-AMBIGUOUS",
            "data.units.from",
            "declares both `glob` and `resolver`, which name two different ways of "
            "finding the same roster — `from` says how core finds a unit, and a "
            "declaration with two answers has none. Declare one",
        )


def _units_declaration(data: dict[str, Any], c: Collector) -> dict[str, Any] | None:
    """`data.units`, or `None` if there is no declaration or its shape is wrong.

    In the normal pipeline this shape is already guaranteed by `_check_shape`, which
    runs first in `validate_config` and stops the whole check before any of this
    module's readers of `data.units` are ever called. This guard exists so a
    caller of this function — `_check_units_source`, `_check_units`, and any
    other reader of `data.units` — does not crash on a non-mapping `data.units`
    reached on its own, whether through `_check_shape` or a direct call.
    Reported —
    under the same `E-CONFIG-SHAPE` identifier `_check_shape` uses, so a bad shape is
    never two different codes — only if that exact diagnostic is not already in
    `c.findings`, which is what keeps a direct call from double-reporting one
    `_check_shape` already caught.
    """
    units_decl = data.get("units")
    if not units_decl:
        return None
    if not isinstance(units_decl, dict):
        already_reported = any(
            f.code == "E-CONFIG-SHAPE" and f.path == "data.units" for f in c.findings
        )
        if not already_reported:
            c.error(
                "E-CONFIG-SHAPE",
                "data.units",
                f"is a {type(units_decl).__name__} (`{units_decl!r}`); expected a mapping "
                "with a `from` key, e.g. `{from: index.csv, key: patient_id}`",
            )
        return None
    return units_decl


def _check_units(
    doc: dict[str, Any], c: Collector
) -> tuple[UnitList | None, dict[str, float] | None, frozenset[str]]:
    """Resolve the roster so unit checks are real rather than deferred to run time.

    A `ContractError` from resolution becomes a diagnostic carrying the SAME
    identifier, so a user sees one code for one problem whether it surfaced here
    or during a run.

    One thing skips resolution outright rather than piling a second error onto a
    config `_check_data` has already flagged: `input_dir` missing, not absolute,
    or unreadable — `_check_data` already reported the real problem, and
    resolving would only add a confusing "file not found" on top of a directory
    that does not exist.

    No `-UNSUPPORTED` field is skipped on: `allocation` and `assign`'s
    method are not read by `resolve_units` at all, and the three that ARE read
    — `cluster_by`, `weight_by`, and (under `by_attribute`) `holdout.from` —
    are read only where a `data.units.measurements` collapse could file a unit
    by row order, which is an independent fault of its own. So resolving
    against a real table or glob alongside one of those refusals adds a
    genuine, independent finding — a duplicate key in the roster is a real
    defect whether or not `holdout` is also declared — rather than noise about
    the same problem twice.

    Returns the resolved roster, or `None` when resolution did not happen or did
    not succeed — `_check_replication` uses its length to check a `fold` count
    against real units rather than resolving the roster a second time — and
    `technical_n` beside it, which is `None` under the same conditions and
    whenever `data.units.measurements` is undeclared. `_check_measurements` reads
    it to tell an input table that actually carried replicates from one that did
    not: `{max: 1}` means no row was merged, which is what separates a `by` that
    names an input column from one naming a measurement a step invents.
    """
    data = doc.get("data") or {}
    units_decl = _units_declaration(data, c)
    if units_decl is None:
        return None, None, frozenset()
    input_dir = data.get("input_dir")
    if not input_dir:
        return None, None, frozenset()  # E-DATA-REQUIRED already reported by _check_data
    if not isinstance(input_dir, str):
        # `check_envelope` is what REPORTS this (E-CONFIG-TYPE) — this guard
        # exists because this function may be reached without it having run: a
        # leaf fault is deliberately non-fatal, so `_check_units` still runs on
        # a still-malformed `doc`, and `Path()` requires a str/PathLike. This is
        # a second, independent `Path(input_dir)` call from the one `_check_data`
        # already guards — the two read the same leaf for two different purposes
        # (whether the directory is usable at all vs. whether a roster resolves
        # against it), so each needs its own guard.
        return None, None, frozenset()
    path = Path(input_dir).expanduser()
    if not path.is_absolute() or not path.is_dir() or not any(path.iterdir()):
        # E-DATA-NOT-ABSOLUTE / E-DATA-UNREADABLE already reported by _check_data
        return None, None, frozenset()
    source = units_decl.get("from")
    key = units_decl.get("key")
    if key is not None and not isinstance(key, str):
        # `check_envelope` is what REPORTS this (E-CONFIG-TYPE) — this guard
        # exists because this function may be reached without it having run.
        # `_from_table` hashes `key` against a `set` of column names
        # (`key_col not in columns`), which raises `TypeError: unhashable type`
        # for a list or dict rather than the `ContractError` the `except` below
        # is built to catch — a plain wrong-but-hashable type (an int, a bool)
        # does not crash there, but skipping uniformly on any wrong type keeps
        # this guard matching what `check_envelope` already typed the leaf as,
        # rather than only covering the unhashable subset that happens to crash
        # today.
        return None, None, frozenset()
    # `LEAF_TYPES` types `data.units.attributes` itself a `list` — and it is one
    # here, so `check_envelope` reports nothing — but names no dotted path for a
    # list ELEMENT (the same reason `sweep.grid`'s axis values aren't in the
    # table either). So a non-string item is this function's own finding to
    # make, not a fault `check_envelope` already caught: unlike the `input_dir`
    # and `key` guards above, skipping here silently would be a real gap, not a
    # duplicate. `_from_table` (`units.py`) checks each name against
    # `UNIT_FIELDS`, then `RESERVED_COLUMNS` (both tuples — tolerate an
    # unhashable name) and then against
    # `columns` (a `set` — raises `TypeError: unhashable type` for a list or
    # dict). Reported under `E-UNITS-ATTR-MISSING`, the identifier `_from_table`
    # itself already raises for a *string* name the table doesn't have — a
    # non-string name can never equal a CSV column name either, so "the table
    # does not have it" is exactly as true, and this is one identifier for one
    # user-facing question ("is this a real column?") rather than a second code
    # for the type-shaped version of the same fault.
    attrs = units_decl.get("attributes")
    if isinstance(source, str) and isinstance(attrs, list):
        bad_attrs = [a for a in attrs if not isinstance(a, str)]
        if bad_attrs:
            for bad in bad_attrs:
                c.error(
                    "E-UNITS-ATTR-MISSING",
                    "data.units.attributes",
                    f"names {bad!r}, which {source} does not have",
                )
            return None, None, frozenset()
    try:
        # `technical_n` and the source's columns are passed out rather than
        # discarded: `run` reports the first, and `_check_measurements` reads its
        # `max` to know whether the input path merged any rows at all and the
        # second to know what `measurements.by` could name.
        #
        # The same `cfg` a `scope: "run"` step sees, so a resolver reading a swept
        # parameter meets a `SweptAway` marker rather than a value no condition
        # used. Built here rather than threaded from `validate_config` because
        # every other check in this module re-derives from `doc` locally.
        roster, technical_n, columns = resolve_units(
            units_decl,
            path,
            cfg=resolve_wide_cfg(doc, wide_swept_paths(doc.get("sweep") or {})),
        )
        return roster, technical_n, columns
    except ContractError as exc:
        c.error(exc.code, "data.units", str(exc))
        return None, None, frozenset()
    except BaseException as exc:
        # `validate` is contracted never to raise, and a resolver body is user
        # code that can fail through `BaseException`, not just `Exception` —
        # a bare `sys.exit()` or a raised `KeyboardInterrupt`/`BaseException`
        # would otherwise escape this function entirely. `KeyboardInterrupt`
        # is re-raised rather than turned into a diagnostic, so Ctrl-C still
        # stops the command — but as a FRESH, argument-less
        # `KeyboardInterrupt`, `from None`: a real Ctrl-C already carries no
        # message, and this is what stops a resolver body that constructed
        # one carrying a credential from reaching Python's own
        # uncaught-exception printer, which prints an exception's `str()`
        # same as any other. `from None` suppresses the chain — plain `raise`
        # re-raises the ORIGINAL object, message and all. A table or glob
        # source's own non-`ContractError` faults (a mis-encoded CSV, an
        # absolute glob pattern) are recoded to `E-UNITS-SOURCE-UNREADABLE`
        # inside `resolve_units` itself and so are already `ContractError`s
        # by the time they reach here.
        if isinstance(exc, KeyboardInterrupt):
            raise KeyboardInterrupt from None
        c.error(
            "E-RESOLVER-RAISED",
            "data.units",
            f"resolution raised {type(exc).__name__}: {exc}",
        )
        return None, None, frozenset()


def _check_measurements(
    units: dict[str, Any],
    roster: UnitList | None,
    technical_n: dict[str, float] | None,
    columns: frozenset[str],
    c: Collector,
) -> None:
    """`data.units.measurements` — shape, then `by`, then the collapse rule against the column.

    `reference.md` § Validation, "Collapse rule fits the column": `measurements.collapse:
    mean` over `site`, which is a string, has no meaning — use `first` or `mode`, or a
    per-column map. The type comes from the *resolved roster's own attribute values*
    rather than from the declaration, because `attributes` declares names, not types.
    When the roster does not resolve, `by`'s and `collapse`'s own shape are still
    checked below — a config can be wrong about `measurements`'s shape with no
    `input_dir` in reach at all, and skipping that too would let the roster's absence
    swallow an unrelated fault — but the two arms that check `by` against what the
    source actually has (`E-RESOLVER-MEASUREMENT-FIELD`, `E-UNITS-ATTR-MISSING`) and
    the numeric-type loop are all gated on the roster having resolved: none of them
    has anything true to say about a source that never ran.

    A single rule applies to every collapsed column (a per-column map's un-named
    columns fall back to `first`, the same fallback `units.rule_for` uses), so a
    *constant* string column is refused here even though `units.apply_rule`'s
    constant-column shortcut would let `mean` survive it at run time: whether a
    check's verdict depends on the data happening to be constant is not something a
    reader can act on, and the document draws no such exception for row 243.
    """
    decl = units.get("measurements")
    if decl is None:
        return
    if not isinstance(decl, dict) or not decl:
        c.error(
            "E-DATA-MEASUREMENTS-INVALID",
            "data.units.measurements",
            "is empty or is not a mapping; it needs `by` (the attribute distinguishing "
            "one measurement of a unit from another) and `collapse` (how rows sharing a "
            "key become one). An empty declaration changes no behavior, which is the "
            "failure the refusal it replaces exists to prevent",
        )
        return
    by = decl.get("by")
    valid_by = by if isinstance(by, str) and by else None
    if valid_by is None:
        c.error(
            "E-DATA-MEASUREMENTS-INVALID",
            "data.units.measurements.by",
            "is missing or is not an attribute name; without it nothing distinguishes "
            "a second measurement of one unit from a resumed retry of the same one, "
            "and the two collapse in opposite directions",
        )
    source = units.get("from")
    resolver = source.get("resolver") if isinstance(source, dict) else None
    if valid_by is not None and isinstance(resolver, str) and resolver and roster is not None:
        # Ungated on collapse, unlike the table arm below it — but gated on the
        # roster having resolved at all. A table's `by` may name a measurement
        # identity the STEP invents through `io.record(..., measurement=)`,
        # which is why that arm waits until rows were actually collapsed. A
        # resolver has no columns at all, so `reference.md` § Where units come
        # from turns yielding `by` into an obligation — "the field a CSV would
        # simply have carried has to be named" — and
        # `E-RESOLVER-MEASUREMENT-FIELD`'s row states the fault without a
        # collapse precondition. But `_check_units` returns `frozenset()` for
        # `columns` on every failure path — an unregistered resolver name,
        # `E-RESOLVER-YIELD`, `E-UNITS-EMPTY`, a missing or non-absolute
        # `input_dir` — and none of those means the resolver yielded nothing
        # named `by`; it means the resolver never ran (or never finished
        # running) at all. `roster is not None` is exactly `_check_units`
        # resolved cleanly, which is when `columns` is an honest report of what
        # the resolver yielded rather than an empty default standing in for a
        # fault this arm has no business re-describing. The columns here are
        # what the resolver yielded, before the projection onto
        # `data.units.attributes`: the projected roster carries only declared
        # attributes, and `by` is not one of them.
        if valid_by not in columns:
            c.error(
                "E-RESOLVER-MEASUREMENT-FIELD",
                "data.units.measurements.by",
                f"names {valid_by!r}, and resolver `{resolver}` yields no unit carrying an "
                "attribute of that name to collapse on. A resolver has no columns beyond the "
                "attributes it yields, so yield one `Unit` per measurement, sharing a `key`, "
                f"and emit {valid_by!r} as an attribute",
            )
    elif (
        valid_by is not None
        and resolver is None
        and technical_n is not None
        and technical_n["max"] > 1
    ):
        # The input table actually merged rows, so `by` had to name one of ITS
        # columns — and `units.collapse_measurements` groups on the unit `key`
        # alone, reading `by` only to drop that name from the merged attributes.
        # A `by` naming nothing therefore collapses exactly as a correct one
        # would, and reports a `technical_n` claiming the merge was intentional:
        # rows nothing declared to be measurements of one unit, averaged. That is
        # a wrong number rather than a missing diagnostic, which is why it is
        # refused before the block stops being refused wholesale.
        #
        # The source's COLUMNS, never `data.units.attributes`.
        # `design-principles.md` § Core vs. plugin lists `key`, `attributes`,
        # `cluster_by`, `measurements.by`, `holdout.from`, `assign.from`,
        # `stratify_by` and `null_test.shuffle` as parallel namers of input fields, so
        # `by` names a column in its own right; the fence in `reference.md`
        # § What isn't a repeat declares no `attributes` at all, and against the
        # declared set this check would refuse the document's own example.
        #
        # Gated on `max > 1` rather than checked unconditionally, because the
        # same declaration serves the step path — `io.record(..., measurement=)`
        # — where the measurement identity is one the STEP invents and no input
        # column carries it. `artifacts._collapse_measurements` never reads `by`
        # at all, so an unnameable axis there costs nothing and refusing it
        # would refuse a design `reference.md` § What isn't a repeat documents.
        # (Recorded in `docs/superpowers/spec-defects.md`: `by` means two
        # different things on the two paths and only the first is checkable.)
        #
        # `E-UNITS-ATTR-MISSING`, not a second identifier: its own row already
        # states this predicate — "names a value the source table has no column
        # for" — and this is that question asked about a second field.
        if valid_by not in columns:
            source = units.get("from")
            where = source if isinstance(source, str) else "the unit source"
            c.error(
                "E-UNITS-ATTR-MISSING",
                "data.units.measurements.by",
                f"names {valid_by!r}, which {where} does not have, while rows sharing a key "
                f"were collapsed anyway (up to {int(technical_n['max'])} per unit). Nothing "
                "distinguished those rows as measurements of one unit, so the collapsed "
                "values average rows the design never said belonged together. Name the "
                "column that tells one measurement of a unit from another, or remove "
                "`data.units.measurements` if the repeated key is a duplicate",
            )
    collapse = decl.get("collapse")
    if collapse is None:
        # `E-UNITS-COLLAPSE-RULE`, below, is reserved for a rule that NAMES
        # something invalid — `reference.md`'s row for it says exactly that
        # ("names a rule that is none of `mean`, `median`, `sum`, `first`, or
        # `mode`"), and an omission names nothing. Routing a missing `collapse`
        # there would make that row, which is dual-listed with `units.apply_rule`'s
        # own raise, mean two different things depending on which surface hit it.
        c.error(
            "E-DATA-MEASUREMENTS-INVALID",
            "data.units.measurements.collapse",
            "is missing; `collapse` is required alongside `by` — how rows sharing a key become one",
        )
        return
    rules = list(collapse.values()) if isinstance(collapse, dict) else [collapse]
    for rule in rules:
        if rule not in COLLAPSE_RULES:
            # Same code `units.apply_rule` raises once task 3 wires collapse into
            # `resolve_units` — `reference.md` § Errors `validate` reports already
            # lists `E-UNITS-COLLAPSE-RULE` as one identifier reached from both
            # surfaces, the same reuse `E-REPL-SEED-COLLISION` illustrates, so this
            # is not a second code for the fault `apply_rule` will also raise on.
            c.error(
                "E-UNITS-COLLAPSE-RULE",
                "data.units.measurements.collapse",
                f"is {rule!r}; expected one of {', '.join(COLLAPSE_RULES)}, or a "
                "mapping of column name to one of them",
            )
            return
    if roster is None:
        return
    for name in sorted({n for u in roster for n in u.attributes} - {valid_by}):
        # `units.rule_for`, not a second copy of its fallback: this check and the
        # collapse it guards must not come to hold two different ideas of which
        # rule a column gets. The two copies had already drifted — the inline one
        # skipped `rule_for`'s `str()` coercion — which is how a config could
        # validate against one reading and run under the other.
        rule = rule_for(name, collapse)
        if rule not in NUMERIC_COLLAPSE_RULES:
            continue
        offenders = [
            u.attributes[name]
            for u in roster
            if name in u.attributes and not is_measurement_numeric(u.attributes[name])
        ]
        if offenders:
            c.error(
                "E-DATA-MEASUREMENTS-COLLAPSE-TYPE",
                f"data.units.measurements.collapse.{name}",
                f"is {rule!r} over {name!r}, which holds {offenders[0]!r} — a "
                f"{type(offenders[0]).__name__} that is not numeric and does not parse "
                "as one. Use `first` or `mode` for it, or a per-column map giving each "
                "column the rule that fits it",
            )


# A name test, and the only one in this module. `reference.md` § Weighted samples
# states the trigger this list is half of: numeric, positive, varying across
# units, and named like a weight. Without the name half the other three match
# `age`, `dose`, `latency` and `score` — nearly every numeric attribute there is —
# and a warning that fires on almost everything is one a reader learns to skip,
# which costs more than the false positive on a `body_weight` column does. It is
# admittedly not a core-vs-plugin-clean test: `weight` means body mass in a
# wet-lab assay and a sampling weight in a survey, and no substring test can tell
# them apart. What makes that payable is that the message states its own remedy
# in one step — declare it, or rename it — so a false positive costs a reader one
# decision rather than an investigation.
_WEIGHT_NAME_HINTS = ("weight", "_prob", "probability")


def _check_weight_by(units: dict[str, Any], roster: UnitList | None, c: Collector) -> None:
    """`data.units.weight_by` — the attribute exists, its values are usable, and a
    column that looks like a weight is not silently going unused.

    `reference.md` § Validation, rows "Weight attribute exists", "Weights are
    usable" and "Weighting looks undeclared".

    **`data.units.attributes` is the reference set for the name**, and this is the
    opposite of `_check_measurements`'s `by`, deliberately. A weight is read *per
    unit at analysis time* — § Weighted samples: core "hands the column to
    `aggregate` like any other attribute" — so it has to survive resolution as an
    attribute, and `units._from_table` populates `Unit.attributes` from
    `data.units.attributes` and nothing else. `measurements.by` is *consumed* at
    collapse time and dropped from the merged unit, so it need not survive at all
    and is checked against the source's columns instead. The § Validation rows say
    exactly this: `weight_by` names something "which is not a unit attribute",
    where `measurements.by` names a column of "a `reads.csv` with no `read_id`
    column".

    The declared list is read rather than the roster's realized attribute names so
    the name check runs with no roster at all — the same construction
    `_check_report_by` uses, and equivalent when a roster does resolve, since
    `_from_table` refuses an attribute its table has no column for. Skipping the
    *value* half when the roster is absent is not the silent skip H1 removed: the
    name half still reports, and a test pins that.

    Under a `{glob: ...}` source no attribute can be declared at all — `_from_glob`
    refuses any name — so a `weight_by` there always draws
    `E-DATA-WEIGHT-UNKNOWN`. That is truthful rather than a gap: a glob yields a
    key and a path and nothing else, so no weight column exists to name.
    """
    declared = units.get("weight_by")
    if declared is None:
        _warn_undeclared_weight(units, roster, c)
        return
    if not isinstance(declared, str):
        # `check_envelope` is what REPORTS this (`E-CONFIG-TYPE` — `envelope.py`
        # types `data.units.weight_by` a `str`). Reporting it again here would
        # both duplicate the finding and describe `3` as "empty", a word that
        # does not fit it.
        return
    if not declared:
        c.error(
            "E-DATA-WEIGHT-UNKNOWN",
            "data.units.weight_by",
            "is empty; it names the unit attribute holding the weight, and an empty "
            "declaration changes no behavior — which is the failure a truthy read of "
            "it would hide. Name the attribute, or remove the key",
        )
        return
    # A non-string item in `data.units.attributes` is `_check_units`'s own finding
    # (`E-UNITS-ATTR-MISSING`); filtering it here just treats it as undeclared,
    # which it already is, and keeps `set()` off an unhashable item in a module
    # contracted to collect rather than raise.
    #
    # An absent or `null` `attributes` is an empty list, not a skip: "no
    # attributes are declared, so `weight_by` names none of them" is exactly row
    # 291's case, and skipping it would make the commonest form of the mistake the
    # one form that reports nothing. Only a *present, wrongly-shaped* list is
    # skipped, `E-CONFIG-SHAPE` having already reported it.
    attrs = units.get("attributes") or []
    if not isinstance(attrs, list):
        return
    names = sorted({a for a in attrs if isinstance(a, str)})
    if declared not in names:
        c.error(
            "E-DATA-WEIGHT-UNKNOWN",
            "data.units.weight_by",
            f"names {declared!r}, which is not a unit attribute — a weight is read per "
            f"unit, so it has to be one. `data.units.attributes` declares "
            f"{', '.join(names) or 'none'}",
        )
        return
    if roster is None:
        return
    bad = [
        (u.key, u.attributes.get(declared))
        for u in roster
        if usable_weight(u.attributes.get(declared)) is None
    ]
    if bad:
        key, value = bad[0]
        c.error(
            "E-DATA-WEIGHT-INVALID",
            "data.units.weight_by",
            f"names {declared!r}, which holds a value that is not a positive finite "
            f"number for {len(bad)} of {len(roster)} units (unit {key!r} holds "
            f"{value!r}). A weight is how much of the population a unit stands for, so "
            "zero, a negative, a non-number and a NaN are each a unit standing for "
            "nothing core could weight with",
        )


def _warn_undeclared_weight(units: dict[str, Any], roster: UnitList | None, c: Collector) -> None:
    """`W-DATA-WEIGHT-UNDECLARED` — an attribute that looks like a sampling weight
    while `weight_by` is unset.

    The trigger cannot read the declaration it is about, so it reads the roster:
    an attribute whose name contains `weight`, `_prob` or `probability`, whose
    every value is a positive finite number, and which does not hold one value
    across every unit. `reference.md` § Weighted samples states all four, and the
    `W-` registry row repeats them, because a warning whose trigger is unstated is
    one a user cannot act on.

    Constancy is the discriminator that matters most in practice: a column that
    does not vary weights nothing, and warning about it would teach a reader to
    ignore the warning — which costs more than the missed case, this being a
    warning about a *possible* omission rather than a fault.

    Reported for the first candidate in sorted order rather than for each. The
    remedy is the same sentence whichever one a reader looks at, and `weight_by`
    takes one name, so a second warning adds no decision.
    """
    if roster is None:
        return
    for name in sorted({n for u in roster for n in u.attributes}):
        if not any(hint in name.lower() for hint in _WEIGHT_NAME_HINTS):
            continue
        weights = [usable_weight(u.attributes.get(name)) for u in roster]
        if any(w is None for w in weights):
            continue
        if len(set(weights)) < 2:
            continue
        c.warn(
            "W-DATA-WEIGHT-UNDECLARED",
            f"data.units.attributes.{name}",
            f"{name!r} is numeric, positive and varies across units, and its name reads "
            "like an inverse sampling probability — but `data.units.weight_by` is unset, "
            "so it is reported like any other attribute and no estimate is weighted by "
            "it. An unweighted mean over an enriched sample answers a different question "
            "than the population one, in the same shape. Set `data.units.weight_by` if it "
            "is a weight, or rename the attribute if it is not",
        )
        return


def _check_cluster_by(
    doc: dict[str, Any], units: dict[str, Any], roster: UnitList | None, c: Collector
) -> None:
    """`data.units.cluster_by` — the attribute exists, and a column that looks like
    a cluster identifier is not silently going undeclared.

    `reference.md` § Validation, rows "Cluster attribute exists" and "Clustering
    looks undeclared".

    **`data.units.attributes` is the reference set for the name**, the same side of
    the line `_check_weight_by` reads and the opposite side from
    `_check_measurements`'s `by`. The § Validation row says `cluster_by` names
    something "which is not a unit attribute", where `measurements.by` names a
    column of "a `reads.csv` with no `read_id` column"; a cluster is read per unit
    when the partition is drawn, so it has to survive resolution as an attribute,
    where a `by` is consumed at collapse time and dropped from the merged unit.
    That also supplies the glob cross-check for free: `_from_glob` refuses every
    declared attribute, so a `cluster_by` under a `{glob: ...}` source always draws
    `E-DATA-CLUSTER-UNKNOWN` — truthfully, a glob yielding a key and a path and
    nothing else.

    The declaration is read rather than the roster's realized attribute names, so
    the name check runs with no roster at all — `_check_weight_by`'s construction,
    and equivalent when a roster does resolve, since `_from_table` refuses an
    attribute its table has no column for.

    There is no *value* half here, unlike the weight check: any label is a usable
    cluster id, and the one value fault there is — a unit carrying none — is
    `units.clusters_of`'s raise, under this same code.
    """
    declared = units.get("cluster_by")
    if declared is None:
        _warn_undeclared_cluster(doc, units, roster, c)
        return
    if not isinstance(declared, str):
        # `check_envelope` reports this (`E-CONFIG-TYPE` — `envelope.py` types
        # `data.units.cluster_by` a `str`). Reporting it again here would duplicate
        # the finding and describe `3` as "empty", a word that does not fit it.
        return
    if not declared:
        c.error(
            "E-DATA-CLUSTER-UNKNOWN",
            "data.units.cluster_by",
            "is empty; it names the unit attribute holding the cluster identity, and "
            "an empty declaration changes no behavior — which is the failure a truthy "
            "read of it would hide. Name the attribute, or remove the key",
        )
        return
    # A non-string item in `data.units.attributes` is `_check_units`'s own finding
    # (`E-UNITS-ATTR-MISSING`); filtering it here treats it as undeclared, which it
    # already is, and keeps `set()` off an unhashable item in a module contracted to
    # collect rather than raise. An absent or `null` `attributes` is an empty list
    # rather than a skip, for the reason `_check_weight_by` states: "no attributes
    # are declared, so `cluster_by` names none of them" is exactly the row's case.
    attrs = units.get("attributes") or []
    if not isinstance(attrs, list):
        return
    names = sorted({a for a in attrs if isinstance(a, str)})
    if declared not in names:
        c.error(
            "E-DATA-CLUSTER-UNKNOWN",
            "data.units.cluster_by",
            f"names {declared!r}, which is not a unit attribute — a cluster is read per "
            f"unit when the split is drawn, so it has to be one. `data.units.attributes` "
            f"declares {', '.join(names) or 'none'}",
        )


ALLOCATION_MODES = ("within", "between")
"""The allocation values, in § The one config file's own order.

The single source of the enum for `data.units.allocation`. `envelope.py` types the
field a bare `str`, so nothing there catches a misspelling — `_check_assign` reads
it against this tuple before either of its own branches (*Allocation needs arms*,
*Arms need allocation*) run, the same role `ASSIGN_METHODS` plays for
`assign.<axis>.method` in the same function. An absent or `null` value is `within`,
the default, and is not in the enum for that reason — the check below reads
`None` as legal rather than requiring it spelled out.
"""

ASSIGN_METHODS = ("random", "by_attribute", "blocked")
"""The assignment methods, in § The one config file's own order.

The single source of the enum for `data.units.assign.<axis>.method`. Which of a
block's other fields are read follows from which one it is — `from` is
`by_attribute`'s, `block_size` is `blocked`'s — so a block whose discriminator is
absent or misspelled describes no assignment at all, which is what
`E-DATA-ASSIGN-METHOD` refuses.

**All three execute.** `random` and `blocked` draw an arm and `by_attribute`
reads one, which is why the enum's members are not interchangeable to any row
below: `units.DRAWN_ASSIGN_METHODS` splits this tuple into the two that draw and
the one that reads, and that split is what decides which of a block's other
fields mean anything. A value *outside* the enum is a different thing again — a
malformed declaration, `E-DATA-ASSIGN-METHOD` — and no row here reads it as a
method at all.
"""

# `DRAWN_ASSIGN_METHODS` is imported from `units` rather than declared here, and
# the direction is deliberate. Two literals naming which methods draw — one here,
# one in `units.assignment_for` — would be pinned in agreement by nothing, and a
# fourth drawing method added to `ASSIGN_METHODS` on this side alone would pass
# `validate` and then partition on a column. `units` is the right home for the
# one copy: the dependency edge already runs that way (`units.py` imports
# nothing from here). This module's use of the tuple outlived the refusal it was
# minted for: it named the methods `E-DATA-ASSIGN-DRAWN` refused, and now names
# the branch a drawn method takes through `_check_assign`.


HOLDOUT_METHODS = ("random", "by_attribute")
"""`data.units.holdout.method`'s enum — `reference.md` § A fixed holdout split.

Two values and no more, and stated as a closed enum for `ASSIGN_METHODS`'s
reason: a third named here and realized nowhere would validate clean and then
reach `units.holdout_for`, which refuses what it cannot draw. Which of the two
reads a partition and which draws one is what decides every other field's
meaning, so a malformed `method` is reported before any of them is read.
"""


def _declared_levels(sweep: Any, axis: str) -> list[str] | None:
    """`sweep.groups`'s declared `levels` for `axis`, or `None` when the axis
    isn't declared there, or is, but its `levels` don't resolve to a non-empty
    list of strings — `sweep.groups`'s own shape fault, reported elsewhere or
    not at all in this build, and not this function's to report a second time.

    Shared by `_check_assign`'s `by_attribute` branch (`arms_of` needs the same
    list to partition a resolved roster against) and its `random`/`blocked`
    branch (*Ratio names levels* needs it to check a declared `ratio`'s keys),
    reading `sweep.groups` the same second way `_check_assign`'s own docstring
    already describes: entry by entry, since `levels` is not a `by`-path
    `selector_paths` collects.
    """
    if not isinstance(sweep, dict):
        return None
    for entry in sweep.get("groups") or []:
        if isinstance(entry, dict) and entry.get("by") == axis:
            candidate = entry.get("levels")
            if (
                isinstance(candidate, list)
                and candidate
                and all(isinstance(v, str) for v in candidate)
            ):
                return candidate
            return None
    return None


def _usable_ratio_share(value: Any) -> bool:
    """Whether one `assign.<axis>.ratio` entry is a share `units._apportion`
    can divide a roster by: a finite, strictly positive `int` or `float`.

    **Deliberately not `units.usable_weight`**, the house predicate for the
    neighbouring question about `data.units.weight_by`. That one reads through
    `is_measurement_numeric`, which accepts a numeric *string* — it has to,
    because a weight arrives from `csv.DictReader`, which yields `str` for
    every column. A `ratio` share never arrives from a table: it is written in
    the config file by hand, and `units._apportion` sums its values, so
    accepting `"3"` here would validate clean and then raise a bare
    `TypeError` on `sum` — the validate-clean-then-crash gap this whole family
    of checks exists to close.

    `bool` is excluded ahead of `int` for the usual reason `True` is `1`: a
    `ratio: {a: true, b: 2}` describes no split anyone meant. Finiteness is
    checked on top of positivity for `usable_weight`'s reason, one step
    earlier: `float("nan") <= 0` is `False`, so a positivity test alone admits
    a value that reaches `int(nan)` in `_apportion` and raises `ValueError`
    there instead of being reported here.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(value) and value > 0


def _read_axis_column(block: Any, axis: str, attribute_names: set[str]) -> str | None:
    """The unit attribute an axis's arm is **read** out of, or `None` when the
    axis draws instead, or names no attribute this build can resolve.

    One question, asked of a *neighbouring* axis rather than of the block being
    checked: *Allocation strata survive clustering* needs it for a
    `stratify_by` naming an earlier group axis, where the stratum's value per
    unit is that axis's realized membership. Under `by_attribute` that
    membership is a column and this returns its name; under `random` or
    `blocked` it is a draw, which allocates whole clusters and so is constant
    within every cluster with nothing to check. Any other `method` value is
    out of the enum and reads nothing at all.

    The `from` resolution is `units.assignment_for`'s own — the declared `from`
    when it is a non-empty string, else the axis name — deliberately *not* a
    second copy of the rule but the same sentence, and the reason this returns
    a column rather than a `bool`: a caller that had to re-resolve `from`
    itself would be the second resolution `assignment_for`'s docstring exists
    to prevent. An absent, non-mapping, or method-less block reads a column
    too, the same fallback `_check_assign` and `assignment_for` both take.

    `None` for a name outside `attribute_names`: `E-DATA-ASSIGN-UNKNOWN` is
    that axis's own block's fault to report, and a constancy finding derived
    from a column nothing declares would be a second finding about the first's
    subject.
    """
    block_map = block if isinstance(block, dict) else {}
    if block_map.get("method") not in (None, "by_attribute"):
        # A drawn method, and — for a value outside the enum entirely —
        # `E-DATA-ASSIGN-METHOD`'s own fault to report, which no draw of that
        # axis ever gets past (`assignment_for` allows `by_attribute` and
        # refuses the rest). Neither reads a column, so neither has one here.
        return None
    declared_from = block_map.get("from")
    column = declared_from if isinstance(declared_from, str) and declared_from else axis
    return column if column in attribute_names else None


def _check_assign(
    doc: dict[str, Any], units: dict[str, Any], roster: UnitList | None, c: Collector
) -> None:
    """`data.units.allocation` and `data.units.assign` against each other and against
    `sweep.groups` — fourteen § Validation rows, all but two read from declarations
    alone, so each reports whether or not a roster resolved; only *Attribute
    assignment resolves* and *Allocation strata survive clustering* need the roster.
    (The count was already one short at "eleven" before this slice: *Block size
    fills the arms* was implemented here and never counted.)

    *Allocation is a known value* — `allocation` present and not one of
    `ALLOCATION_MODES` (`within`, `between`). Checked first, and both branches below
    are gated to assume it already passed: an absent or `null` value is `within`,
    the default, and is not this row's concern.

    *Allocation needs arms* — `allocation: between` with no group axis. § Allocation
    puts the reason in one sentence: `between` "answers *how units reach an arm*, not
    *what the arms are*", so the declaration on its own describes one cohort and
    nothing to divide it into.

    *Every axis is assigned* — a declared group axis with no block under `assign`.
    One finding per unassigned axis, in declaration order, because the remedy is one
    block per axis and a reader fixing the first would otherwise come back for the
    second. Together with *Allocation needs arms* this is the whole of § The one
    config file's "`assign` is REQUIRED when `allocation` is `between`": an absent
    `assign` and an empty `assign: {}` both leave every declared axis unassigned, and
    `between` with no axes at all is what *Allocation needs arms* reports. Neither
    fires under `allocation: within` — that value takes the sibling branch below.

    *Arms need allocation* — the mirror of *Allocation needs arms*: a declared
    group axis with `allocation` absent or `within`, rather than `between` with no
    group axis. `within` says every unit appears in every condition, so a unit
    cannot be in one arm and in all of them — the design the pair below exists to
    make structurally impossible: handing every condition on a group axis the
    same, whole roster is exactly two identical measurements reported as two arms.
    `E-DATA-ALLOCATION-WITHIN-ARMS`, read from the declarations alone like its
    mirror, and mutually exclusive with it by construction — one `if`/`elif` over
    the same `allocation` value.

    *Assignment names a method*, which is **not** gated on `allocation`: it is a
    check on the block, not on the pair, and an `assign` block naming no method
    describes no assignment wherever it was declared.

    **A drawn method (`random`, `blocked`) takes the middle branch of the same
    `elif` chain *Assignment names a method* reads**, where every row about a
    field only a draw gives meaning to lives. That branch carried
    `E-DATA-ASSIGN-DRAWN` — "in the enum, but not built" — until the slice that
    built drawing retired it; what the branch is *for* is unchanged, since which
    of a block's other fields are read still follows from whether the method
    draws or reads.

    *Ratio names levels* — checked in that branch: `ratio` only means anything
    for a method that draws, so a `random`/`blocked` block earns
    `E-DATA-ASSIGN-RATIO` for a non-empty
    `ratio` this build cannot apportion — one code over the whole malformed-value
    family, not one per shape: not a mapping at all (`ratio: 3`); a mapping whose
    keys don't equal the axis's declared `sweep.groups` levels exactly (a partial
    mapping — § Allocation: "the levels I left out get the average" is a rule
    nobody should have to infer — or a key naming no declared level); or a mapping
    with the right keys but a value that is not a finite positive number (`{a:
    -1, b: 2}`, `{a: "x", b: 2}`, `{a: .nan, b: 2}` — `_usable_ratio_share` is
    the predicate) — a share of zero or less draws no units for that level and
    `units._apportion` has no check of its own to catch it. An empty `ratio` is
    equal allocation and earns nothing, matching every other row here. Skipped
    when the axis's declared `levels` don't resolve to a non-empty list of
    strings, `sweep.groups`'s own shape fault — except the not-a-mapping case,
    which needs no `levels` to detect.

    *Allocation strata exist* — checked in the same branch and for the same
    reason `ratio` is: `stratify_by` names how a draw is *balanced*, so it means
    something only where a draw happens (`by_attribute`'s non-empty one is
    *Ratio and strata need a draw* instead). `E-DATA-ASSIGN-STRATIFY-UNKNOWN`
    for a name that is neither in `data.units.attributes` nor a `sweep.groups`
    axis — **existence only**, an axis declared *after* this one being
    *Stratification is forward-only*'s row and its own code. One finding per
    offending name. The declaration is read through `units.stratum_names`, the
    same function the draw balances on, so a bare `stratify_by: site` cannot be
    one name to the draw and a character sequence here.

    *Stratification is forward-only* — `E-DATA-ASSIGN-STRATIFY-FORWARD`, the
    order half of *Allocation strata exist* and a separate code because a row and
    a code are the same check seen from two ends: a stratum naming a `sweep.groups` axis
    this one is drawn *before*, or naming this axis itself. A drawn axis leaves
    no column, so the balance is over the earlier axis's **realized** membership,
    which `cli._resolved_group_axes` supplies by handing each draw the plans
    already drawn — making this a sequencing requirement rather than a check on
    one, and the reason a cycle is unrepresentable rather than something to
    detect. Order comes from `sweep.selector_paths`, the same declaration order
    that loop walks. A stratum resolving to a declared attribute is exempt before
    this runs, matching `units._stratum_groups`' own precedence. An axis-name
    stratum that passes this row is handed on to *Allocation strata survive
    clustering*, which reads it through the column its axis reads — see
    `_read_axis_column`.

    *Allocation strata survive clustering* — `E-DATA-ASSIGN-STRATIFY-VARIES`,
    one of the two rows here needing a roster: a declared stratum whose value is
    not constant across one cluster, under a declared `cluster_by`. **A stratum
    naming an earlier group axis is read through that axis's own column** when
    it has one — an axis drawn `by_attribute` has membership that *is* a
    column's value, and a column varying within a cluster is a membership that
    does, which splits the cluster between this axis's arms even though core
    computed the partition. An earlier axis that draws needs no check: it
    allocated whole clusters. A cluster is
    drawn whole, so an arm cannot be balanced on a stratum that cluster carries
    two of, and core refuses the pair rather than prioritizing one constraint —
    the argument `partition_units` makes for the identical composition over
    folds, which is why `units.stratum_varies_within_cluster` is shared with
    `_check_fold_stratify_by` rather than reimplemented. Skipped for a name
    already reported above, and under `blocked`, whose combination with any
    `cluster_by` *Blocked draw excludes clustering* refuses outright.

    *Blocked draw excludes clustering* — `method: blocked` beside a declared,
    non-empty `data.units.cluster_by`, refused as
    `E-DATA-ASSIGN-BLOCKED-CLUSTER`. A block fills to an exact unit count and a cluster is
    indivisible, so no `block_size` — declared or `auto` — honours both;
    `units.assignment_for`'s own `blocked` branch raises `NotImplementedError`
    for the identical combination rather than realizing one rule over the
    other, and this is the check that keeps a config naming it from ever
    reaching that raise. **`random` earns no mirror row**: it draws whole
    clusters instead of filling to a size, so it has no size for `cluster_by`
    to conflict with — the asymmetry `reference.md` § Clustered units and §
    Allocation both state. Read `usable_cluster`, resolved once ahead of the
    per-axis loop the same "present, non-empty `str`" way `validate_config`'s
    own local of that name is (a wrongly-typed or empty `cluster_by` is
    `check_envelope`'s or `_check_cluster_by`'s fault to report, not this row's
    to report a second time) — so it reports whether or not a roster resolved,
    and the check runs first inside the `blocked` branch, ahead of *Block size
    fills the arms*: once it fires, every check that branch would otherwise run
    is moot rather than merely redundant, and the loop moves to the next axis.

    *Assignment seed is auto or pinned* — `E-DATA-ASSIGN-SEED`, checked in the
    drawn branch because `by_attribute` consults no seed at all. A `seed` that
    is neither `auto` (or absent, or `null`) nor a pinned `int` is one
    `units.assign_seed_for` cannot honour: it returns an `int` literally and
    derives from the digest for everything else, so `seed: "1234"` draws a
    derived allocation and `allocation.json` records that derived seed as the
    axis's own — a pin discarded with no diagnostic anywhere, the fault the
    sibling `sweep.sample.seed` already earns `E-SWEEP-SAMPLE-INVALID` for. Its
    own code rather than a broadening of a neighbour: each code here owns one
    field's value space, and `seed` was the one drawn field with none —
    `E-DATA-ASSIGN-NO-DRAW` least of all, that being about a field meaningless
    under `by_attribute`. A `bool` is refused, matching `assign_seed_for`'s own
    exclusion. Read from the declaration alone, so it reports with or without a
    roster, and checked ahead of *Every arm draws units* so a block reported
    here is not then drawn from the seed it just refused.

    *Every arm draws units* — `E-DATA-ASSIGN-LEVELS`, the other roster-needing
    row and the last thing the drawn branch does: `units.assignment_for` is
    called on a block every row above accepted, and the `ContractError` it
    raises for a level the apportionment gave no unit becomes the finding. The
    fault is a proportion against a *roster size* rather than a declaration —
    `ratio: {a: 1, b: 1000}` over ten units names every level and carries only
    positive shares — so no declaration-only row can reach it, which is why it
    sits beside `E-DATA-ASSIGN-LEVELS`'s other roster-resolved check in the
    `by_attribute` branch below rather than in the `ratio` family. The draw is
    the check rather than a second emptiness rule, and its plan is discarded:
    two producers of membership is the disagreement this whole seam exists to
    prevent. **Restricted to the unstratified, unclustered draw**, where every
    level's realized size is a function of the roster size and the ratio alone
    and the placeholder digest cannot change the answer; the residue is
    recorded in `reference.md` § Errors `validate` reports rather than left
    unstated. Skipped for a block already reported, whose fault the draw would
    only restate or crash on.

    **`method: by_attribute`'s three rows, checked only in that branch of the
    same `elif` chain** — the chain being a partition of which of a block's
    fields mean what, not a refusal of any branch of it. `from` is the only one
    a draw does not read at all, there being no column to read; `ratio`,
    `stratify_by` and the axis's declared `levels` are all read under a draw
    too, `ratio` and `stratify_by` by that branch's own rows above and `levels`
    as *the set of arms the apportionment fills* rather than the set the
    column's values must equal, which is this branch's own *Attribute
    assignment resolves*. Under an absent or out-of-enum method they mean
    nothing at all, which *Assignment names a method* already refuses:

    *Ratio and strata need a draw* — `by_attribute` reads an arm already assigned
    rather than drawing one, so a non-empty `ratio` describes a proportion no draw
    produced and a non-empty `stratify_by` describes a balance no draw performed.
    § Allocation calls the two "the same fault," so both are reported under the
    one code, `E-DATA-ASSIGN-NO-DRAW`, distinguished only by which field's path
    the finding names — one finding per offending field, so a block declaring
    both earns two findings rather than one that only names the first. An empty
    `ratio: {}` or `stratify_by: []` — what `init` writes and what most designs
    carry — changes no behavior and earns neither. **A wrong-typed value is
    absorbed here too rather than left silent** — `ratio: 3`, a bare
    `stratify_by: site` — the same absorption `E-DATA-ASSIGN-METHOD` performs
    for a non-mapping block and `E-DATA-ASSIGN-UNKNOWN` for a non-`str` `from`:
    neither field is an `envelope.py` `LEAF_TYPES` leaf, so there is no
    `E-CONFIG-TYPE` backstop, and task 4's key-closure check closes the axis
    block's names, not its values' types, so nothing else in `src/` reads either
    field at all. "Present and non-empty" is read structurally
    (`is not None and != {}` / `!= []`) rather than by `isinstance`, so a bare
    string is exactly as non-empty as a populated mapping — this row's fault is
    presence, unlike *Ratio names levels* above, whose fault is specifically the
    keys.

    *Assignment attribute exists* — `assign.<axis>.from`, declared or **defaulted
    to the axis name** (§ The one config file: "`from` is `by_attribute` only, and
    defaults to the axis name"), is not in `data.units.attributes`.
    `E-DATA-ASSIGN-UNKNOWN`. Modelled on `_check_weight_by`'s name half:
    `data.units.attributes` is the reference set rather than the roster's realized
    names, for the same reason — an arm is read per unit, so it has to survive
    resolution as an attribute — and that lets the check run with no roster at
    all. **Where it diverges from `_check_weight_by`, stated rather than left
    silent**: `weight_by`/`cluster_by` are `envelope.py` `LEAF_TYPES` leaves, so a
    non-`str` declaration there is `E-CONFIG-TYPE`'s to report and `_check_weight_by`
    returns rather than duplicating it. `assign.<axis>.from` is not — `assign`'s
    children are axis names no fixed dotted path can type, the same reason `method`
    itself carries no such guard — so there is no backstop to defer to, and
    returning silently the way the two siblings do would report a non-`str`,
    non-`None` `from` nowhere at all: a fault this build's shape checks cannot see,
    the inverse of what this pass exists to hunt for. So this branch, alone among
    the three, does not defer: a non-`str` `from` is folded into
    `E-DATA-ASSIGN-UNKNOWN` itself — the same absorption `E-DATA-ASSIGN-METHOD`
    already performs for a non-mapping block, "the block naming no method that it
    is" — rather than skipped or given a code of its own.

    **An explicit `from: ""` matches the sibling rather than diverging**:
    `_check_weight_by`'s own wording — present, not absent, so no default applies,
    and an empty declaration changes no behavior — carries over to the same shape,
    because there is no reason for the two to say it differently. It is not
    word-for-word: this message ends by naming the remedy the sibling has no
    equivalent for, removing the key to take the axis-name default. `weight_by`
    has no default to fall back to, so there the remedy is to name the attribute.

    *Attribute assignment resolves* — the resolved attribute's values, over the
    resolved roster, are not exactly the axis's declared `sweep.groups` levels —
    **set equality, in either direction, one code**: a value naming no declared
    level, or a declared level no unit's value names. `units.assignment_for` is
    the single producer of a realized allocation and is what this asks — not
    `units.arms_of` beneath it, which would be `validate` resolving membership
    by a route the runner does not take, the second producer that seam exists to
    prevent, one level up. Its `ContractError` is caught here and reported under
    its own code, `E-DATA-ASSIGN-LEVELS`, the same reuse `_check_units` already
    makes of `resolve_units`'s raise. Skipped when the roster did not resolve, when the
    axis's declared `levels` did not resolve to a non-empty list of strings —
    `sweep.groups`'s own shape fault, reported elsewhere or not at all in this
    build — or when the attribute name above did not resolve, there being nothing
    to partition against.

    Group axis names come from `sweep.selector_paths`, which is total over a
    malformed `sweep.groups` and dedupes — the dedup being exactly why
    `_check_sweep`'s *Axis names are distinct* row reads `sweep.groups` a third
    way, entry by entry rather than through this function, to see two entries
    sharing one name that `selector_paths` would otherwise collapse into one.
    One consequence, stated rather than left to be discovered: `groups: [{by: 123}]`
    yields no axis name, so `between` beside
    it reports *Allocation needs arms* **beside** `_check_shape`'s own
    `E-CONFIG-SHAPE` on `sweep.groups[0].by` — a non-string `by` is a shape fault
    `_check_shape` now catches directly, and a finding that also names the real
    consequence of the unreadable axis beats leaving that consequence silent. The
    two new rows read `sweep.groups` a second way, entry by entry, since `levels`
    is not a `by`-path `selector_paths` collects.

    A non-mapping `assign` is skipped entirely: `envelope.py` types
    `data.units.assign` a `dict`, so `E-CONFIG-TYPE` already reports it and a
    second, derived finding on top is one more thing to read and nothing more to
    fix. A non-mapping *axis block* has no such reporter — the envelope's own
    comment says `assign`'s children are axis names no fixed dotted key could ever
    name — so it is reported here, as the block naming no method that it is.
    """
    assign = units.get("assign")
    # An absent or null `assign` is an empty one — the module's `or {}` convention,
    # and the point of the row: a config with no `assign` key at all is exactly the
    # shape "REQUIRED when `allocation` is `between`" refuses. A non-mapping is a
    # different thing, and neither check reads it.
    blocks = assign if isinstance(assign, dict) else {}
    malformed = assign is not None and not isinstance(assign, dict)
    sweep = doc.get("sweep")
    axes = selector_paths(sweep) if isinstance(sweep, dict) else []

    # *Blocked draw excludes clustering* — read the same "usable" way
    # `validate_config`'s own `cluster_by` local is (a wrongly-typed or empty
    # declaration is `check_envelope`'s/`_check_cluster_by`'s fault to report, and
    # counting a second, derived fault on top of it here would cost a reader one
    # more line for no new information). Resolved once, ahead of the loop below,
    # since it does not vary per axis — every `blocked` block in this `assign`
    # answers to the one `data.units.cluster_by` declaration.
    declared_cluster = units.get("cluster_by")
    usable_cluster = (
        declared_cluster if isinstance(declared_cluster, str) and declared_cluster else None
    )

    allocation = units.get("allocation")
    if allocation is not None and allocation not in ALLOCATION_MODES:
        # *Allocation is a known value* — checked before either branch below runs,
        # so both can safely assume `allocation` is already `None`/`within`/`between`
        # rather than misreading a typo as `within` (the fault the mirror row,
        # *Arms need allocation*, is gated to avoid) or as `between` (which its own
        # sibling branch would misread as "no arms declared" instead of "not a
        # legal value"). Recorded as a gap in `docs/superpowers/spec-defects.md`
        # while `E-DATA-ALLOCATION-UNSUPPORTED`'s blanket refusal covered every
        # out-of-enum value anyway; this row is what covers it now that the
        # blanket refusal is gone.
        c.error(
            "E-DATA-ALLOCATION-METHOD",
            "data.units.allocation",
            f"is {allocation!r}, which is not an allocation; expected one of "
            f"{', '.join(ALLOCATION_MODES)}",
        )
    elif units.get("allocation") == "between":
        if not axes:
            c.error(
                "E-DATA-ALLOCATION-NO-ARMS",
                "data.units.allocation",
                "is `between`, but `sweep.groups` declares no axis to say what the arms "
                "are — `between` says how a unit reaches an arm, not what the arms are, so "
                "on its own it divides nothing. Declare a group axis, or use `within`",
            )
        elif not malformed:
            for axis in axes:
                if blocks.get(axis) is None:
                    c.error(
                        "E-DATA-ASSIGN-MISSING",
                        "data.units.assign",
                        f"declares no `{axis}` block, but `sweep.groups` declares that axis "
                        f"and `data.units.allocation` is `between` — one block per axis is "
                        f"what says how each unit reaches its arm, and an axis without one "
                        f"names arms nothing puts a unit in",
                    )
    elif units.get("allocation") in (None, "within") and axes:
        # *Arms need allocation* — the mirror of *Allocation needs arms* above:
        # `sweep.groups` names an axis but `allocation` is `within`, or absent
        # (which defaults to it). Gated on `(None, "within")` explicitly, rather
        # than a bare `elif axes:`, so a stray out-of-enum `allocation` value —
        # caught above by *Allocation is a known value* (`E-DATA-ALLOCATION-METHOD`)
        # before this `elif` chain ever reaches here — is not misreported here as
        # `within`.
        c.error(
            "E-DATA-ALLOCATION-WITHIN-ARMS",
            "data.units.allocation",
            f"is `within` (the default when the key is absent), but `sweep.groups` "
            f"declares {', '.join(axes)} — `within` says every unit appears in every "
            f"condition, so a unit can't be in one arm and in all of them. Declare "
            f"`allocation: between`, or drop the group axis",
        )

    for axis, block in blocks.items():
        if block is None:
            continue  # an absent block; *Every axis is assigned* is the one that speaks
        if not isinstance(block, dict):
            c.error(
                "E-DATA-ASSIGN-METHOD",
                f"data.units.assign.{axis}",
                f"is a {type(block).__name__} (`{block!r}`) rather than a block declaring a "
                f"`method`; the methods are {', '.join(ASSIGN_METHODS)}, and which of the "
                f"block's other fields are read follows from which one it is",
            )
            continue
        method = block.get("method")
        where = f"data.units.assign.{axis}.method"
        if method is None:
            c.error(
                "E-DATA-ASSIGN-METHOD",
                where,
                f"is not declared; the methods are {', '.join(ASSIGN_METHODS)}, and which of "
                f"the block's other fields are read follows from which one it is, so a block "
                f"without one describes no assignment",
            )
        elif method not in ASSIGN_METHODS:
            c.error(
                "E-DATA-ASSIGN-METHOD",
                where,
                f"is {method!r}, which is not an assignment method; expected one of "
                f"{', '.join(ASSIGN_METHODS)}",
            )
        elif method in DRAWN_ASSIGN_METHODS:
            # The branch a *drawn* method takes — `random` and `blocked`, the two
            # `units.assignment_for` realizes. It carried `E-DATA-ASSIGN-DRAWN`
            # until the slice that built the draw retired it, and the tuple stayed:
            # what it discriminates is which of a block's fields mean anything
            # (`ratio`, `block_size`, `stratify_by` here; `from` in the
            # `by_attribute` branch below), which is a permanent question, not the
            # temporary refusal it used to gate.
            #
            # The count of findings this branch started with, read once at the
            # end by *Every arm draws units*: that row realizes the draw, and a
            # draw is only worth realizing over a block every row below accepted.
            findings_before_block = len(c.findings)
            # *Ratio names levels* — `ratio` only means anything for a method that
            # draws, so it is checked here rather than in the `by_attribute` branch
            # below. An empty
            # `ratio` (or an absent one) is equal allocation and earns no finding,
            # and neither does a mapping whose keys already equal the axis's
            # declared `levels` set exactly and whose values are all positive
            # numbers — the accept path this row shares with every other in this
            # function.
            #
            # **One code covers the whole malformed-value family**, not one per
            # shape: a non-mapping (`ratio: 3`), a mapping with the wrong keys, and
            # a mapping with a non-positive or non-numeric value all mean "this
            # `ratio` cannot be apportioned" to `units._apportion`, which has no
            # backstop of its own for any of the three — a non-mapping falls
            # through `assignment_for`'s own `isinstance(ratio, dict) and ratio`
            # guard to equal allocation silently, and a non-positive weight (`{a:
            # -1, b: 2}`) is silently floored to 0 rather than raising, and a
            # `nan` share reaches `int(nan)` and raises `ValueError` from inside
            # the apportionment — see `_usable_ratio_share`. Reported
            # once per block, the first violation found, mirroring every other row
            # here that reports one finding rather than every possible one.
            ratio = block.get("ratio")
            if ratio is not None and ratio != {}:
                levels = _declared_levels(sweep, axis)
                levels_repr = ", ".join(repr(level) for level in levels) if levels else ""
                if not isinstance(ratio, dict):
                    c.error(
                        "E-DATA-ASSIGN-RATIO",
                        f"data.units.assign.{axis}.ratio",
                        f"is {ratio!r}, a {type(ratio).__name__}, not a mapping; "
                        f"expected one entry per level of axis {axis!r}"
                        + (f" ({levels_repr})" if levels_repr else ""),
                    )
                elif levels is not None and set(ratio) != set(levels):
                    declared_keys = sorted(str(k) for k in ratio)
                    noun = "key" if len(declared_keys) == 1 else "keys"
                    keys_repr = ", ".join(repr(k) for k in declared_keys)
                    c.error(
                        "E-DATA-ASSIGN-RATIO",
                        f"data.units.assign.{axis}.ratio",
                        f"has {noun} {keys_repr}; expected one entry per level of "
                        f"axis {axis!r} ({levels_repr})",
                    )
                elif levels is not None and any(
                    not _usable_ratio_share(value) for value in ratio.values()
                ):
                    bad_keys = sorted(
                        str(key) for key, value in ratio.items() if not _usable_ratio_share(value)
                    )
                    noun = "value" if len(bad_keys) == 1 else "values"
                    c.error(
                        "E-DATA-ASSIGN-RATIO",
                        f"data.units.assign.{axis}.ratio",
                        f"has a non-positive or non-numeric {noun} for "
                        f"{', '.join(repr(k) for k in bad_keys)}; every entry is a "
                        f"share of the roster, and a share of zero or less draws no "
                        f"units for that level",
                    )

            # *Allocation strata exist* — `assign.<axis>.stratify_by` under a
            # method that draws. **Existence only**: a target naming an axis declared
            # *after* this one is a different row, *Stratification is
            # forward-only*, and its own code — order is not this row's
            # question.
            #
            # The reference sets are `data.units.attributes` and
            # `sweep.groups`, not the roster's realized columns, for the reason
            # `E-DATA-CLUSTER-UNKNOWN` reads the first: a stratum is read per
            # unit when the assignment is drawn, so it has to survive
            # resolution as an attribute — or resolve as an axis, the one
            # target this row admits that a `fold`'s or `holdout`'s
            # `stratify_by` does not. Read from the declarations alone, so it
            # reports whether or not a roster resolved.
            #
            # `units.stratum_names` reads the declaration, rather than a second
            # `isinstance` chain here: the draw balances on the names that
            # function returns, so a bare `stratify_by: site` read as one name
            # there and as a sequence of characters here would be the
            # validate-clean-then-disagree gap this slice exists to close. A
            # non-string or empty entry names neither an attribute nor an axis
            # and is absorbed under this code rather than left silent — the
            # same absorption `E-DATA-ASSIGN-UNKNOWN` performs for a non-`str`
            # `from`, and for its reason: `stratify_by` is no `envelope.py`
            # `LEAF_TYPES` leaf, so there is no `E-CONFIG-TYPE` backstop.
            # One finding per offending name, so a reader fixing the first is
            # not sent back for the second.
            declared_attrs = units.get("attributes") or []
            attribute_names = (
                {a for a in declared_attrs if isinstance(a, str)}
                if isinstance(declared_attrs, list)
                else set()
            )
            resolvable_strata: list[str] = []
            axis_strata: list[tuple[str, str]] = []
            for name in stratum_names(block.get("stratify_by")):
                if isinstance(name, str) and name in attribute_names:
                    resolvable_strata.append(name)
                    continue
                if isinstance(name, str) and name in axes:
                    # *Stratification is forward-only* — the order half, and its
                    # own code. An axis may only stratify on one **already
                    # resolved**, because the stratum is that axis's realized
                    # membership rather than a column: `units.assignment_for` is
                    # handed the plans drawn so far, so a stratum naming an axis
                    # this one is drawn before, or naming this one itself, names
                    # membership that does not exist yet. `sweep.selector_paths`
                    # is the declaration order both sides read — the same list
                    # `cli._resolved_group_axes` walks — so the position this
                    # compares is the position the draw actually happens at.
                    #
                    # Skipped when this axis is not itself a `sweep.groups` axis:
                    # nothing draws it, so it has no position to be forward of,
                    # and a finding about the order of a block no draw reaches
                    # would be derived from a different fault (*Every assignment
                    # names an axis*) rather than reported on its own terms.
                    if axis not in axes or axes.index(name) < axes.index(axis):
                        # A legal stratum: an axis drawn before this one. Its
                        # *column*, when it has one, is what *Allocation strata
                        # survive clustering* below reads — see
                        # `_read_axis_column`, and the paragraph on this branch
                        # in the docstring.
                        column = _read_axis_column(blocks.get(name), name, attribute_names)
                        if column is not None:
                            axis_strata.append((name, column))
                        continue
                    itself = " itself" if name == axis else ""
                    c.error(
                        "E-DATA-ASSIGN-STRATIFY-FORWARD",
                        f"data.units.assign.{axis}.stratify_by",
                        f"names {name!r}, the axis{itself} rather than one declared "
                        f"before it — `sweep.groups` declares "
                        f"{', '.join(axes)} in that order, and an axis may only "
                        f"stratify on one already resolved. A drawn axis leaves no "
                        f"column, so the balance is over the earlier axis's realized "
                        f"membership, and {name!r} has none when {axis!r} is drawn. "
                        f"Declare {name!r} first, or stratify on a unit attribute",
                    )
                    continue
                c.error(
                    "E-DATA-ASSIGN-STRATIFY-UNKNOWN",
                    f"data.units.assign.{axis}.stratify_by",
                    f"names {name!r}, which is neither a unit attribute nor a group "
                    f"axis — a stratum is read per unit when the arm is drawn, so it "
                    f"has to survive resolution as an attribute, or name an axis whose "
                    f"arms are already drawn. `data.units.attributes` declares "
                    f"{', '.join(sorted(attribute_names)) or 'none'}, and `sweep.groups` "
                    f"declares {', '.join(axes) or 'none'}",
                )

            # *Allocation strata survive clustering* — a stratum a cluster
            # carries two values of cannot be balanced across a draw that
            # cannot divide that cluster, so core refuses the pair rather than
            # silently prioritizing one of the two constraints (§ Clustered
            # units). `units.stratum_varies_within_cluster` is the constancy
            # test, shared with the `fold` half rather than reimplemented, and
            # it reads membership from `units.clusters_of`.
            #
            # Only the names above that resolved to a declared attribute, or
            # that resolved to an earlier axis **reading a column** — a name
            # this build cannot read has already been reported, and a second
            # finding derived from the first is the noise `_check_cluster_by`
            # argues against. **Not reached under `blocked`** either —
            # `blocked` beside any `cluster_by` is refused outright by *Blocked
            # draw excludes clustering* below, which makes a stratum's
            # constancy inside that combination a question about a design
            # already refused.
            #
            # **An axis-name stratum is read through the column its axis
            # reads**, and that is the whole of the second half's construction.
            # `_read_axis_column` returns one only for an earlier axis whose
            # own method is `by_attribute`, where the realized membership *is*
            # the column's value, so a column that varies within a cluster is a
            # membership that does. An earlier axis that **draws** needs no
            # check and gets none: it allocated whole clusters, so its
            # membership is constant within every cluster by construction.
            # Before this, an axis-name stratum reached no constancy check at
            # all, and the consequence was measurable rather than theoretical —
            # an earlier `by_attribute` axis whose `from` varies within a
            # cluster splits that cluster between its *own* arms, the halves
            # land in different strata here, and
            # `_assign_whole_clusters_by_ratio` allocates each independently,
            # so the cluster straddles both arms of this axis too. That
            # contradicts `reference.md` § Clustered units' "core computed the
            # partition, so core keeps it indivisible", which is why this is
            # the same rule reaching further rather than a new one: same code,
            # same row, one more way for a stratum to be non-constant.
            if roster is not None and usable_cluster is not None and method == "random":
                for name, column in [(n, n) for n in resolvable_strata] + axis_strata:
                    try:
                        offender = stratum_varies_within_cluster(roster, usable_cluster, column)
                    except ContractError:
                        # `clusters_of` refuses a unit carrying no cluster value
                        # (`E-DATA-CLUSTER-UNKNOWN`), already reported beside this by
                        # `_check_cluster_by`. This module collects rather than raises.
                        break
                    if offender is not None:
                        cluster, values = offender
                        # An axis name and the column it reads are the same
                        # sentence with one clause added, rather than a second
                        # message: the fault is one a reader fixes in the same
                        # place either way, and naming only the axis would send
                        # them looking for a column that axis's block spells.
                        lead = (
                            f"names {name!r}, which"
                            if column == name
                            else f"names {name!r}, an axis drawn before this one whose "
                            f"realized membership is the column {column!r} — which"
                        )
                        c.error(
                            "E-DATA-ASSIGN-STRATIFY-VARIES",
                            f"data.units.assign.{axis}.stratify_by",
                            f"{lead} varies within `{usable_cluster}` "
                            f"{cluster} — it carries {', '.join(values)}. A cluster is "
                            "drawn whole, so an arm cannot be balanced on a stratum the "
                            "cluster carrying both values would have to be split for; "
                            "stratify on an attribute that is constant within a cluster, "
                            "or drop the stratification",
                        )

            # *Block size fills the arms* — `block_size` means something only for
            # `blocked` (`from`'s own reason: the discriminator decides which of a
            # block's other fields are read), and only for an explicit `int` value —
            # `"auto"`, or anything else that isn't a plain `int`, resolves to twice
            # the ratio's sum at draw time (`units.assignment_for`'s own rule) and is
            # by construction a whole multiple of it. `ratio_sum` is read the same
            # "usable" way the checks above establish it, rather than re-derived: a
            # `ratio` that is absent, empty, or already reported above by *Ratio names
            # levels* falls back to the level count — equal allocation's implied
            # sum — so this row does not also re-report a `ratio` shape fault the row
            # above already owns; a well-formed `ratio` sums its own declared shares.
            # `math.isclose` rather than a bare `%`, because `ratio`'s values may be
            # `float` and a sum like `1.5 + 2.5` should not fail a whole-multiple test
            # to floating-point noise.
            if method == "blocked":
                # *Blocked draw excludes clustering* — checked before any of the
                # `block_size` logic below, and with a `continue` rather than an
                # `else` wrapping it: a block fills to an exact unit count and a
                # cluster is indivisible, so no `block_size` — declared or `auto` —
                # honours both, which makes every check below moot once this one
                # fires rather than merely redundant. `random` earns no such row:
                # it draws whole clusters instead of filling to a size, so it has
                # no size to conflict with `cluster_by` in the first place — the
                # asymmetry `reference.md` § Clustered units and § Allocation both
                # state. `units.assignment_for`'s own `blocked` branch raises
                # `NotImplementedError` for this exact combination — its own
                # docstring names this refusal as the reason it never has to
                # realize one rule over the other — so this check is what keeps a
                # config naming it from ever reaching that raise. The `ratio`
                # check above already ran for
                # this block — orthogonal to whether a cluster is declared, so it
                # is not re-gated here — but nothing after this point is: a
                # `block_size` this build cannot honour beside a cluster is not a
                # value to also validate on its own terms.
                if usable_cluster is not None:
                    c.error(
                        "E-DATA-ASSIGN-BLOCKED-CLUSTER",
                        where,
                        f"is `blocked` beside a declared `data.units.cluster_by` "
                        f"({usable_cluster!r}) — a block counts units and fills to an "
                        f"exact size, a cluster is indivisible, and no block size "
                        f"honours both. Use `random` for a cluster-randomized draw, or "
                        f"`by_attribute` for a read one",
                    )
                    continue
                declared_block_size = block.get("block_size", "auto")
                # **`"auto"` is checked too, not exempted** — a controller ruling
                # from a review round that first tried exempting it: `auto` is
                # twice `ratio`'s sum, and for a ratio like `{a: 0.33, b: 0.33, c:
                # 0.34}` (a plain percentage split) that resolves to a
                # `block_size` of 2, which starves `b` in *every* block —
                # `units.assignment_for` raises `E-DATA-ASSIGN-LEVELS` on a
                # config that validated clean, the same validate-clean-then-fail
                # shape the explicit-value half of this check exists to close.
                # `resolved_block_size` is `None` only when there is nothing yet
                # to check: a malformed explicit value (its own finding already
                # filed below) or unresolved `levels` (below that).
                resolved_block_size: int | None = None
                if declared_block_size != "auto":
                    # **One code covers the whole malformed-value family here too**
                    # — not a mapping's keys this time, but `_apportion`'s own
                    # caller-side gap: `units.assignment_for` cuts the roster with
                    # `range(0, len(keys), block_size)`, which raises a bare
                    # `ValueError` for `0` and silently produces no blocks at all
                    # for a negative step, and treats any non-`"auto"`, non-`int`
                    # value (`2.5`, `"four"`, `null`) as `auto` outright rather than
                    # reporting it — the same validate-clean-then-crash/
                    # silently-ignore shape `E-DATA-ASSIGN-RATIO`'s non-mapping and
                    # non-positive branches close for `ratio`. Checked before the
                    # whole-multiple arithmetic below and unconditionally — not
                    # gated on `ratio_sum > 0`, which every reachable path already
                    # makes true (`_usable_ratio_share` requires a positive value
                    # and `_declared_levels` a non-empty level list) and so could
                    # never itself skip this branch, only read as though it might.
                    if (
                        isinstance(declared_block_size, bool)
                        or not isinstance(declared_block_size, int)
                        or declared_block_size <= 0
                    ):
                        c.error(
                            "E-DATA-ASSIGN-BLOCK-SIZE",
                            f"data.units.assign.{axis}.block_size",
                            f"is {declared_block_size!r}, which is not a positive "
                            f"whole number of units — a block is a count to cut "
                            f'the roster into, and only `"auto"` or a positive '
                            f"`int` names one",
                        )
                    else:
                        resolved_block_size = declared_block_size

                levels_for_block_size = _declared_levels(sweep, axis)
                if levels_for_block_size is not None and (
                    declared_block_size == "auto" or resolved_block_size is not None
                ):
                    usable_ratio = (
                        ratio
                        if isinstance(ratio, dict)
                        and ratio
                        and set(ratio) == set(levels_for_block_size)
                        and all(_usable_ratio_share(v) for v in ratio.values())
                        else None
                    )
                    weights_for_block_size = (
                        [usable_ratio[level] for level in levels_for_block_size]
                        if usable_ratio is not None
                        else [1] * len(levels_for_block_size)
                    )
                    ratio_sum = sum(weights_for_block_size)
                    # `units.auto_block_size`, imported rather than a second copy
                    # of its formula: the controller's task 7 ruling on
                    # `DRAWN_ASSIGN_METHODS` applies verbatim here — two
                    # independent copies of one value are pinned in agreement by
                    # nothing, and `validate` approving a `block_size` its own
                    # draw then computes differently is the validate-clean-
                    # then-disagree gap this whole slice exists to close.
                    # A ternary rather than an `assert` to reach `int`: the
                    # outer `if` above already guarantees `resolved_block_size`
                    # is not `None` whenever `declared_block_size != "auto"`, and
                    # this expression covers the remaining case, `"auto"`,
                    # explicitly — no runtime narrowing hint needed, and nothing
                    # here disappears under `python -O`.
                    block_size = (
                        resolved_block_size
                        if resolved_block_size is not None
                        else auto_block_size(weights_for_block_size)
                    )
                    # **Per-level share, not the sum's divisibility** — a
                    # controller ruling: `block_size` dividing `ratio_sum` evenly
                    # is neither necessary nor sufficient for "every block fills
                    # each arm exactly" (§ Allocation's own purpose clause) — the
                    # two checks are not ordered, verified both directions rather
                    # than assumed. Not sufficient: `ratio: {a: 0.5, b: 0.5}`
                    # sums to 1, and `block_size: 1` is a whole multiple of `1` —
                    # yet every block apportions `[1, 0]`, starving `b` in every
                    # block and dying at `units.assignment_for`'s
                    # `E-DATA-ASSIGN-LEVELS` instead. Not necessary either:
                    # `ratio: {a: 2, b: 2}` sums to 4, and `block_size: 2` is
                    # *not* a whole multiple of 4 — the old check would have
                    # refused it — yet each level's own per-block share,
                    # `2 x 2 / 4 = 1`, is whole, and `_apportion(2, [2, 2]) ==
                    # [1, 1]` fills it exactly. (The two checks agree on some
                    # ratios — `{}`, `{1, 2}` — and disagree on others — `{2,
                    # 2}`, `{0.5, 0.5}` — with no single simpler rule
                    # distinguishing which, so no "they coincide when ..."
                    # clause is stated here; the two counterexamples are the
                    # claim.) Checking each level's own per-block share
                    # (`block_size * weight / ratio_sum`) is the direct
                    # implementation of the purpose clause and replaces the sum
                    # check rather than merely tightening it.
                    bad_levels = [
                        level
                        for level, weight in zip(
                            levels_for_block_size, weights_for_block_size, strict=True
                        )
                        if not math.isclose(
                            (share := block_size * weight / ratio_sum),
                            round(share),
                            abs_tol=1e-9,
                        )
                    ]
                    if bad_levels:
                        noun = "level" if len(bad_levels) == 1 else "levels"
                        resolved_note = (
                            " (resolved from `auto`)" if declared_block_size == "auto" else ""
                        )
                        c.error(
                            "E-DATA-ASSIGN-BLOCK-SIZE",
                            f"data.units.assign.{axis}.block_size",
                            f"is {block_size}{resolved_note}, which does "
                            f"not fill {noun} "
                            f"{', '.join(repr(lvl) for lvl in bad_levels)} exactly "
                            f"in every block — a block must give each level a "
                            f"whole number of units, or it can't hold that arm's "
                            f"share. Use a `block_size` for which every level's "
                            f"own share of it — its ratio weight times the block "
                            f"size, over {ratio_sum!r} — is a whole number",
                        )

            # *Assignment seed is auto or pinned* — a `seed` this build cannot
            # honour as the pin it was written to be. `units.assign_seed_for`
            # returns an `int` literally and derives from the digest for
            # everything else, so `seed: "1234"`, `seed: 1.5` and `seed: true`
            # each draw a *derived* allocation while `allocation.json` records
            # that derived seed under the axis whose seed the config meant to
            # fix — a discarded pin that surfaces nowhere, which is why it is
            # refused here rather than left to a shape check nothing performs:
            # `assign`'s children are axis names no `envelope.py` `LEAF_TYPES`
            # path can type (the same absence `from`, `ratio` and `stratify_by`
            # each answer for themselves), and `_check_assign_axis_keys` closes
            # the block's key *names*, not its values' types.
            #
            # Its own code, `E-DATA-ASSIGN-SEED`, rather than a broadening of a
            # neighbour: every code in this family owns one field's value space
            # — `ratio`'s, `block_size`'s, `stratify_by`'s — and `seed` was the
            # one field of a drawn block with none. `E-DATA-ASSIGN-NO-DRAW` in
            # particular is the wrong home: it is about a field that means
            # nothing under `by_attribute`, and a `seed` under a drawn method
            # means a great deal. `E-SWEEP-SAMPLE-INVALID` refuses the sibling
            # `sweep.sample.seed` for the identical shape, which is the
            # precedent for refusing at all.
            #
            # A `bool` is not an integer here, matching `assign_seed_for`'s own
            # `not isinstance(seed, bool)` exclusion — `seed: true` would
            # otherwise pin the axis to 1 without ever saying so. An absent key
            # and an explicit `null` are both `auto`, § What `auto` derives
            # from's "an omitted `seed` is `auto`, not an error" and the
            # module's `null` is absent convention.
            #
            # Checked before *Every arm draws units*, so a block reported here
            # falls inside `findings_before_block`'s gate: realizing a draw over
            # a seed this row just refused would seed it from the derivation and
            # report a second, derived finding about an allocation no run makes.
            seed = block.get("seed")
            if (
                seed is not None
                and seed != "auto"
                and not (isinstance(seed, int) and not isinstance(seed, bool))
            ):
                c.error(
                    "E-DATA-ASSIGN-SEED",
                    f"data.units.assign.{axis}.seed",
                    f"is {seed!r}, which is neither `auto` nor a pinned integer — "
                    f"a drawn axis takes one or the other, and anything else falls "
                    f"through to the derived seed that `allocation.json` would then "
                    f"record as though it were the pin",
                )

            # *Every arm draws units* — the roster-dependent half of the drawn
            # branch. `ratio: {a: 1, b: 1000}` over a ten-unit roster names
            # every level and carries only positive shares, so it passes every
            # declaration-only row above, and then apportions `b` the whole
            # roster and `a` nothing — `units.assignment_for` raising
            # `E-DATA-ASSIGN-LEVELS` on a config `validate` had approved. That
            # was unreachable while a drawn method was refused outright, which
            # is why this row arrived with the slice that retired the refusal.
            #
            # The fault is a *proportion against a roster size*, not a
            # declaration, so it belongs here beside
            # `E-DATA-ASSIGN-LEVELS`'s existing roster-resolved check in the
            # `by_attribute` branch below rather than in the `ratio` family.
            #
            # **The draw itself is the check**, the same single-producer
            # argument that branch's own `assignment_for` call makes: an
            # emptiness rule reimplemented here is a second answer to "does
            # this arm resolve any units", which is the disagreement the whole
            # seam exists to prevent. The returned plan is **discarded** — it is
            # not a plan anything runs, and keeping it would make this function
            # a second producer of membership inside the check written to close
            # a gap.
            #
            # **Gated to the unstratified, unclustered draw, and the residue —
            # three draws excluded for two different reasons — is recorded
            # rather than silently skipped** (`reference.md` § Errors `validate`
            # reports, this code's row).
            #
            # The first reason is digest-independence: with no strata and no
            # clusters, every level's realized size is a function of
            # `(len(roster), ratio)` alone — `_apportion` decides the sizes and
            # the shuffle only decides which unit lands in which — so the
            # placeholder digest below cannot make this check answer differently
            # from the run's own draw. `"validate"` is `_check_replication`'s own
            # placeholder convention, sound here only because of that. A
            # clustered draw does not have the property:
            # `_assign_whole_clusters_by_ratio` shuffles the cluster order
            # before its stable size sort, so which arm is left with no cluster
            # is genuinely seed-dependent and a placeholder-digest draw could be
            # wrong in either direction.
            #
            # The second reason is the strata, and it is **not** the digest. A
            # stratum naming an earlier group axis needs that axis's realized
            # membership, which only the run's own ordered draw produces. A
            # stratum naming a declared attribute would answer identically at
            # every seed — `_stratum_groups` groups by the column's values in
            # roster order and `_apportion` runs inside each group — so
            # excluding it buys nothing about determinism. It is excluded
            # because `_stratum_groups` **raises** for an attribute
            # `data.units.attributes` declares and no resolved unit carries,
            # which *Allocation strata exist* passes because it reads the
            # declaration: drawing here would turn that broken roster into a
            # traceback out of a module contracted to collect findings and never
            # raise. Admitting it means either swallowing that raise or
            # repeating `_stratum_groups`' precedence rule here, and both are a
            # second rule rather than this one reaching further.
            #
            # Skipped when this block already earned a finding: a `ratio` this
            # build cannot apportion or a `block_size` it cannot honour is
            # already reported on its own terms, and drawing against it would
            # either raise a second, derived finding or crash inside
            # `assignment_for` on a value the row above exists to refuse.
            if (
                len(c.findings) == findings_before_block
                and roster is not None
                and usable_cluster is None
                and not stratum_names(block.get("stratify_by"))
            ):
                drawn_levels = _declared_levels(sweep, axis)
                if drawn_levels is not None:
                    try:
                        assignment_for(roster, axis, block, drawn_levels, "validate")
                    except ContractError as exc:
                        c.error(exc.code, f"data.units.assign.{axis}.ratio", str(exc))
        else:
            # `method == "by_attribute"`, the one value neither elif above caught —
            # the branch where `from` and the axis's declared `levels` mean anything
            # at all.

            # *Ratio and strata need a draw* — `by_attribute` reads an arm already
            # assigned rather than drawing one, so a `ratio` describes a proportion
            # no draw produced and a `stratify_by` describes a balance no draw
            # performed. § Allocation calls the two "the same fault", so both are
            # reported under the one code, `E-DATA-ASSIGN-NO-DRAW`, distinguished
            # only by which field's path the finding names. An empty `ratio: {}` or
            # an empty `stratify_by: []` — what `init` writes and what most designs
            # carry — changes no behavior and is not this row's concern.
            #
            # A wrong-typed value (`ratio: 3`, `stratify_by: site`) is absorbed here
            # too, rather than left silent: neither field is an `envelope.py`
            # `LEAF_TYPES` leaf, so there is no `E-CONFIG-TYPE` backstop to defer
            # to — the same reason `from`'s own non-`str` case has none — and
            # task 4's key-closure check (`_check_assign_axis_keys`) closes the
            # axis block's *names*, not the *types* of their values, so nothing
            # else in `src/` reads `assign.<axis>.stratify_by` at all, and nothing
            # else reads a non-mapping `assign.<axis>.ratio` either. So "present and
            # non-empty" is read structurally — `is not None and != {}` / `!= []` —
            # rather than by `isinstance`, the same absorption `E-DATA-ASSIGN-METHOD`
            # performs for a non-mapping block and `E-DATA-ASSIGN-UNKNOWN` for a
            # non-`str` `from`. A bare string is non-empty by this test the same way
            # `{control: 1}` is: the fault is *presence*, not a key set — unlike
            # *Ratio names levels* above, whose fault is specifically the keys.
            ratio = block.get("ratio")
            if ratio is not None and ratio != {}:
                c.error(
                    "E-DATA-ASSIGN-NO-DRAW",
                    f"data.units.assign.{axis}.ratio",
                    f"is {ratio!r}, which describes a draw that didn't happen — "
                    f"`method: by_attribute` reads an arm already assigned rather "
                    f"than drawing one, so a `ratio` would record a proportion the "
                    f"data may not honour. Remove it, or use `method: random`/"
                    f"`blocked`",
                )
            stratify_by = block.get("stratify_by")
            if stratify_by is not None and stratify_by != []:
                c.error(
                    "E-DATA-ASSIGN-NO-DRAW",
                    f"data.units.assign.{axis}.stratify_by",
                    f"is {stratify_by!r}, which describes how a draw was balanced "
                    f"when none was — `method: by_attribute` reads an arm already "
                    f"assigned rather than drawing one, so a `stratify_by` would "
                    f"record a balance the data may not honour. Remove it, or use "
                    f"`method: random`/`blocked`",
                )

            declared_from = block.get("from")
            if declared_from is not None and not isinstance(declared_from, str):
                # No `E-CONFIG-TYPE` backstop exists for this leaf (see docstring):
                # `assign`'s children are axis names no fixed dotted path can type,
                # so nothing else reports a non-`str` `from`. Folded into
                # `E-DATA-ASSIGN-UNKNOWN` rather than a new code, the way
                # `E-DATA-ASSIGN-METHOD` already absorbs a non-mapping block as
                # "the block naming no method that it is" — a value of the wrong
                # type can never name an attribute either.
                c.error(
                    "E-DATA-ASSIGN-UNKNOWN",
                    f"data.units.assign.{axis}.from",
                    f"is a {type(declared_from).__name__} (`{declared_from!r}`) "
                    f"rather than a string naming a unit attribute — `from` reads a "
                    f"column per unit, so it has to be one",
                )
                continue
            if declared_from == "":
                # `_check_weight_by`'s own wording for the same shape: an empty
                # string is present, not absent, so it does not take the default —
                # and reporting it as "resolves to ''" would leave a reader
                # wondering whether that is a real attribute name rather than a
                # declaration that changes no behavior.
                c.error(
                    "E-DATA-ASSIGN-UNKNOWN",
                    f"data.units.assign.{axis}.from",
                    "is empty; it names the unit attribute holding the arm, and an "
                    "empty declaration changes no behavior — which is the failure a "
                    "truthy read of it would hide. Name the attribute, or remove the "
                    "key to take the axis-name default",
                )
                continue
            resolved_from = declared_from if declared_from is not None else axis
            attrs = units.get("attributes") or []
            if not isinstance(attrs, list):
                continue
            names = sorted({a for a in attrs if isinstance(a, str)})
            if resolved_from not in names:
                default_note = (
                    "" if declared_from is not None else " (defaulted from the axis name)"
                )
                c.error(
                    "E-DATA-ASSIGN-UNKNOWN",
                    f"data.units.assign.{axis}.from",
                    f"resolves to {resolved_from!r}{default_note}, which is not a unit "
                    f"attribute — an arm is read per unit when a `between` roster is "
                    f"built, so it has to be one. `data.units.attributes` declares "
                    f"{', '.join(names) or 'none'}",
                )
                continue
            if roster is None:
                continue
            levels = _declared_levels(sweep, axis)
            if levels is None:
                continue  # `sweep.groups`'s own shape fault, not this row's to report
            try:
                # `assignment_for`, not `arms_of`: the runner resolves this
                # axis's membership through the one producer, so `validate` has
                # to ask the same question of the same declaration or the
                # second membership producer that seam exists to prevent
                # reappears one level up — here, in the check whose whole job
                # is to prove the runner's partition resolves. The block is
                # passed whole rather than as the `from` this branch already
                # resolved, so the resolution is that function's single copy of
                # it too.
                #
                # **The digest is a placeholder**, `_check_replication`'s own
                # convention where it hands `resolve_repeats` a literal
                # `"validate"`: a digest is what a *draw* seeds from, and this
                # call sits inside the `by_attribute` branch, where the
                # parameter is provably unread. It is not defaulted in the
                # signature for exactly that reason — a draw silently seeded
                # from a placeholder is the failure that would be invisible —
                # so a future edit hoisting this call above the method dispatch
                # has to confront the value rather than inherit it.
                assignment_for(roster, axis, block, levels, "validate")
            except ContractError as exc:
                c.error(exc.code, f"data.units.assign.{axis}.from", str(exc))


def _check_fold_stratify_by(
    doc: dict[str, Any],
    units: dict[str, Any],
    roster: UnitList | None,
    cluster_by: str | None,
    c: Collector,
) -> None:
    """A `fold` level's `stratify_by` — the attribute exists, and it survives the
    clustering that decides what a split cannot divide.

    `reference.md` § Validation, rows "Stratification attribute exists" and "Fold
    strata survive clustering". **Only the `fold` level's**: the first row names a
    `fold` level's *or* `holdout`'s `stratify_by`, and its `holdout` half is
    `_check_holdout`'s, under its own code (`E-DATA-HOLDOUT-STRATIFY-UNKNOWN`), so
    that half is not discharged by this. Two checks answer to that one row.
    `data.units.assign.<axis>.stratify_by` is not this row's at all — `reference.md`
    routes it to *Allocation strata exist* instead, under
    `E-DATA-ASSIGN-STRATIFY-UNKNOWN`.

    **`data.units.attributes` is the reference set for the name**, the side of the
    line `_check_cluster_by` and `_check_weight_by` read, and for the same reason: a
    stratum is read per unit when the partition is drawn, so it has to survive
    resolution as an attribute rather than merely be a column of the source. Read
    from the declaration, so the name check runs with no roster at all.

    **A `data.units.measurements.by` fails that test too**, and is refused under the
    same code for it: the measurement axis is consumed where the rows collapse, so a
    stratum naming it is declared as an attribute and absent from every resolved
    unit. Before task 12 retired `E-REPL-FOLD-STRATIFY-UNSUPPORTED` no config
    reached the partition at all and `cli` merely carried a note about the
    `KeyError`; retiring it made the path reachable, which is what makes this a
    check rather than a note.

    Unlike `data.units.cluster_by` there is **no `E-CONFIG-TYPE` backstop** for a
    value of the wrong type: `envelope.LEAF_TYPES` types `replication.repeats` a
    `list` and nothing inside a level, so a `stratify_by: [label]` — the list form
    `holdout`, `assign` and `statistics.resample` each take — would otherwise be
    reported by no check at all. A fold stratifies on one attribute named as a
    string, and anything else, an empty string or empty list included, names none.

    The clustering half needs the cluster membership and the stratum values
    together, which is why it lives here rather than in `replication._fold_k`: that
    function sees the declaration and a count, and never a roster. `cluster_by` is
    handed in — `validate_config`'s one usable-cluster local, the same value
    `units.fold_basis` was resolved from — so nothing here decides for itself what a
    usable cluster declaration is.

    When the attribute is not declared at all, the clustering check is skipped: the
    reader has to declare it either way, and a second finding derived from the first
    is the noise `_check_cluster_by` argues against.
    """
    levels = ((doc.get("replication") or {}).get("repeats")) or []
    if not isinstance(levels, list):
        return  # `check_envelope` types `replication.repeats`; `_check_shape` too
    attrs = units.get("attributes") or []
    names = sorted({a for a in attrs if isinstance(a, str)}) if isinstance(attrs, list) else []
    for level in levels:
        if not isinstance(level, dict) or level.get("kind") != "fold":
            continue
        declared = level.get("stratify_by")
        if declared is None:
            continue
        if not isinstance(declared, str) or not declared:
            empty = declared == "" or declared == []
            c.error(
                "E-REPL-FOLD-STRATIFY-UNKNOWN",
                "replication.repeats",
                (
                    "declares an empty `fold.stratify_by`, which names no attribute to "
                    "balance the folds on and changes no behavior — which is the failure "
                    "a truthy read of it would hide. Name the attribute, or remove the key"
                )
                if empty
                else (
                    f"declares `fold.stratify_by: {declared!r}`, which is not the name of a "
                    "unit attribute; a fold balances its folds on one declared attribute, "
                    "named as a string"
                ),
            )
            continue
        if declared not in names:
            c.error(
                "E-REPL-FOLD-STRATIFY-UNKNOWN",
                "replication.repeats",
                f"declares `fold.stratify_by: {declared}`, which is not a unit attribute — "
                "a stratum is read per unit when the partition is drawn, so it has to be "
                f"one. `data.units.attributes` declares {', '.join(names) or 'none'}",
            )
            continue
        # Declared as an attribute *and* named as the measurement axis, which is a
        # name that does not survive resolution: `collapse_measurements` consumes
        # `measurements.by` — it distinguished the rows and has no value once they
        # are one unit — so `cli` would rebuild the strata from an attribute the
        # collapsed roster no longer carries and reach a bare `KeyError`. Reported
        # under the same code as an undeclared name because it is the same fault
        # under this code's own reasoning: the reference set is `attributes` rather
        # than the source's columns *because* a stratum has to survive resolution,
        # and this one does not.
        #
        # Deliberately asymmetric with `data.units.cluster_by`, which reaches
        # `E-DATA-CLUSTER-VARIES` at run time for the same declaration shape: a
        # cluster naming the measurement axis varies within every unit by
        # construction, and `collapse_measurements` is the one place holding the
        # pre-collapse rows that prove it. A stratum's fault needs no rows — the two
        # declarations alone settle it — so it is refused here, from the
        # declaration, and the two codes say different things about what broke.
        measurements = units.get("measurements")
        axis = measurements.get("by") if isinstance(measurements, dict) else None
        if isinstance(axis, str) and axis == declared:
            c.error(
                "E-REPL-FOLD-STRATIFY-UNKNOWN",
                "replication.repeats",
                f"declares `fold.stratify_by: {declared}`, which `data.units.measurements.by` "
                "also names — the measurement axis is consumed when a unit's rows collapse "
                "and is not an attribute of the resolved unit, so there is nothing left to "
                "balance the folds on. Stratify on an attribute that survives the collapse",
            )
            continue
        if roster is None or not cluster_by:
            continue
        try:
            offender = stratum_varies_within_cluster(roster, cluster_by, declared)
        except ContractError:
            # `clusters_of` refuses a unit carrying no cluster value
            # (`E-DATA-CLUSTER-UNKNOWN`), which is already reported beside this by
            # `_check_cluster_by` or by the resolution `_check_units` performed.
            # This module collects rather than raises, so an unreadable grouping is
            # silence here rather than a traceback.
            return
        if offender is not None:
            cluster, values = offender
            c.error(
                "E-REPL-FOLD-STRATIFY-VARIES",
                "replication.repeats",
                f"declares `fold.stratify_by: {declared}`, which varies within "
                f"`{cluster_by}` {cluster} — it carries {', '.join(values)}. A cluster is "
                "indivisible, so a stratum cannot be balanced across a split that cannot "
                "divide the cluster carrying both values; stratify on an attribute that is "
                "constant within a cluster, or drop the stratification",
            )


def _check_holdout(
    doc: dict[str, Any],
    units: dict[str, Any],
    roster: UnitList | None,
    cluster_by: str | None,
    cells: dict[tuple[tuple[str, str], ...], frozenset[str]] | None,
    c: Collector,
) -> None:
    """Every check `data.units.holdout` gets — ten findings at this commit,
    in emit order, and the enumeration is the list rather than a sample of it:

    - `E-DATA-HOLDOUT-METHOD` — the `method` enum.
    - `E-DATA-HOLDOUT-FRAC` — `frac` in the open interval (0, 1), under `random`.
    - `E-DATA-HOLDOUT-FROM` — `from` required, under `by_attribute`.
    - `E-DATA-HOLDOUT-NO-DRAW` — a field meaning nothing under the declared
      method.
    - `E-DATA-HOLDOUT-SEED` — the seed pin.
    - `E-DATA-HOLDOUT-STRATIFY-UNKNOWN` — a `stratify_by` name that is not a
      declared unit attribute, names `data.units.measurements.by`, or is not
      the name of an attribute at all.
    - `E-DATA-HOLDOUT-FOLD` — a `{kind: fold}` repeat declared beside this
      block. The only check here that reads a block other than `data.units`.
    - `E-DATA-HOLDOUT-VALUES` — **reads the roster:** under `by_attribute`, the
      named column resolving to exactly `train` and `test`.
    - `E-DATA-HOLDOUT-STRATIFY-VARIES` — **reads the roster:** a stratum that
      varies within a `cluster_by` cluster.
    - `E-DATA-HOLDOUT-EMPTY` — **reads the roster, and the cells:** a `random`,
      unstratified, unclustered split that apportions the test side zero units
      — over the **thinnest populated cell** when the design has a cell
      structure, since that is the sub-roster the split is drawn inside
      (`units.holdout_within_cells`), and over the whole roster when it has
      none.

    **Three of the ten read `roster`**, and each carries its own
    `roster is not None` guard rather than leaning on a caller — `_check_resample`'s
    stated convention.

    **Only `E-DATA-HOLDOUT-FOLD` reads `doc`**, and only `E-DATA-HOLDOUT-EMPTY`
    reads `cells` — `_resolved_cells`' realized decomposition, threaded from
    `validate_config`'s single local rather than derived a second time here, for
    the reason `_holdout_test_roster` takes it: two answers to one declaration
    is what a single derivation exists to prevent. `roster` and `cluster_by` are
    both in the signature anyway, `units.assignment_for`'s reason: the caller
    already holds them, and a caller told the signature changed under it is
    what a stable one avoids. A check added here must state which side of
    that line it is on — this list is what the next reader counts against,
    so an eleventh finding belongs in it, and a roster-reading one carries
    its own `roster is not None` guard rather than leaning on a caller.

    **An empty or non-mapping declaration returns reporting nothing**,
    `_check_resample`'s own gate one block over. `holdout: {}` and
    `holdout: null` declare nothing and partition nothing; this function's own
    `if not isinstance(holdout, dict) or not holdout: return` is what keeps
    both from being read as a declaration, and a misspelled child inside a
    non-empty block is `check_envelope`'s `E-CONFIG-KEY-UNKNOWN` rather than
    this function's.

    Every value-shape fault reported here — the `frac` interval, the
    `method`/`from` type absorptions — is `isinstance`-guarded and quietly
    skipped when the field is not the leaf `envelope.LEAF_TYPES` type, the
    same division `_check_report_by` keeps: a leaf type fault is
    `E-CONFIG-TYPE`, reported already and deliberately non-fatal, and
    reporting a second, derived fault on top of the one the reader has to fix
    anyway is what `validate_config`'s own `usable_cluster` guard avoids. The
    three `NO-DRAW` checks are the exception: they test presence, not shape
    (`is not None`, no `isinstance`), so a wrong-typed `frac`/`stratify_by`
    still under the wrong method earns `E-CONFIG-TYPE` alongside `NO-DRAW`
    rather than being absorbed — presence under the wrong method is the fault
    regardless of what the value would have been.

    **`frac`'s interval is open at both ends.** `0` holds nothing out and `1`
    holds everything out; each leaves one side of the split empty, and a split
    with an empty side is not a split. A `frac` small enough to apportion the
    test side zero units over *this* roster — or over the thinnest cell of it —
    is a different fault with a different fix — widen it, or resolve more units
    — and is not this check's but `E-DATA-HOLDOUT-EMPTY`'s.

    **The train side is not checked here, under cells or without them.** A cell
    thin enough for `holdout_sizes` to leave the *train* side empty is
    `reference.md` § Errors core raises' own row — "the **train** side of any
    draw, since `validate` tests the test side alone" — and widening this check
    to it would give one fault two reporting surfaces with two messages.
    """
    holdout = units.get("holdout")
    if not isinstance(holdout, dict) or not holdout:
        return

    method = holdout.get("method")
    if method is None:
        c.error(
            "E-DATA-HOLDOUT-METHOD",
            "data.units.holdout.method",
            f"is not declared; the methods are {', '.join(HOLDOUT_METHODS)}, and which "
            "one is declared decides what every other field of the block means — "
            "`random` draws a split and `by_attribute` reads one already in the data",
        )
    elif not isinstance(method, str):
        # Absorbed here rather than left to `E-CONFIG-TYPE` alone: the reader's
        # question is which method they meant, and a bare type finding does not
        # enumerate the two.
        c.error(
            "E-DATA-HOLDOUT-METHOD",
            "data.units.holdout.method",
            f"is {method!r}, which names no method; the methods are {', '.join(HOLDOUT_METHODS)}",
        )
    elif method not in HOLDOUT_METHODS:
        c.error(
            "E-DATA-HOLDOUT-METHOD",
            "data.units.holdout.method",
            f"is {method!r}, which is not one of {', '.join(HOLDOUT_METHODS)}. A method "
            "named here and realized nowhere would validate clean and then partition "
            "on something core never drew",
        )

    declared_frac = holdout.get("frac")
    declared_from = holdout.get("from")
    if method == "random":
        if declared_frac is None:
            c.error(
                "E-DATA-HOLDOUT-FRAC",
                "data.units.holdout.frac",
                "is not declared, and `method: random` draws the test side by "
                "fraction — there is nothing to draw without one",
            )
        elif isinstance(declared_frac, (int, float)) and not isinstance(declared_frac, bool):
            if not 0.0 < float(declared_frac) < 1.0:
                c.error(
                    "E-DATA-HOLDOUT-FRAC",
                    "data.units.holdout.frac",
                    f"is {declared_frac}, and a test fraction is strictly between 0 and "
                    "1 — `0` holds nothing out and `1` holds everything out, and each "
                    "leaves one side of the split empty",
                )
        if declared_from is not None:
            c.error(
                "E-DATA-HOLDOUT-NO-DRAW",
                "data.units.holdout.from",
                "means nothing under `method: random`, which draws the split rather "
                "than reading one out of a column — declare `method: by_attribute` to "
                "read the column, or drop `from`",
            )
    elif method == "by_attribute":
        if declared_from is None:
            c.error(
                "E-DATA-HOLDOUT-FROM",
                "data.units.holdout.from",
                "is not declared, and `method: by_attribute` reads the split out of a "
                "column — unlike an assignment axis there is no axis name to default "
                "to, so the column has to be named",
            )
        elif isinstance(declared_from, str) and not declared_from:
            c.error(
                "E-DATA-HOLDOUT-FROM",
                "data.units.holdout.from",
                "is empty, which names no column to read the split out of",
            )
        if declared_frac is not None:
            c.error(
                "E-DATA-HOLDOUT-NO-DRAW",
                "data.units.holdout.frac",
                "means nothing under `method: by_attribute`, which reads a split the "
                "data already holds rather than drawing one to a size — the realized "
                "proportion is whatever the column says it is",
            )
        declared_stratify_by = holdout.get("stratify_by")
        if declared_stratify_by is not None and declared_stratify_by != []:
            c.error(
                "E-DATA-HOLDOUT-NO-DRAW",
                "data.units.holdout.stratify_by",
                "means nothing under `method: by_attribute`: `stratify_by` names how a "
                "draw is BALANCED, and a split read out of a column was not drawn. The "
                "same absorption `E-DATA-ASSIGN-NO-DRAW` performs for the same field "
                "one declaration over — including its `!= []` exemption, which is not "
                "this block's own reason: `init` never writes a `holdout` block at "
                "all, and an empty `stratify_by: []` is not silently accepted here — "
                "it is refused two checks later, as `E-DATA-HOLDOUT-STRATIFY-UNKNOWN`",
            )

    if "seed" in holdout:
        seed = holdout["seed"]
        pinned = isinstance(seed, int) and not isinstance(seed, bool)
        if not pinned and seed != "auto":
            c.error(
                "E-DATA-HOLDOUT-SEED",
                "data.units.holdout.seed",
                f"is {seed!r}, and a seed is `auto` or a plain integer. A quoted "
                "number, a float, or a boolean is a pin nothing can honour, and "
                "deriving one anyway would record a derived seed under a key the "
                "config wrote deliberately",
            )

    # `stratify_by`, through `units.stratum_names` — the single authority the
    # draw balances on, which reads a bare `stratify_by: label` as one name
    # exactly as `[label]` is. Re-deriving that reading here with an
    # `isinstance` chain would pin two independent readings of one declaration
    # in agreement by nothing, which is what `_check_resample` reads it this
    # way to avoid.
    #
    # **`data.units.attributes` is the reference set**, not the source's
    # columns, the side of the line `_check_cluster_by`, `_check_weight_by` and
    # `_check_fold_stratify_by` all read: a stratum is read per unit when the
    # split is drawn, so it has to survive resolution as an attribute rather
    # than merely be a column of the source. Checked from the declaration
    # alone, so it reports whether or not a roster resolved.
    #
    # One finding per offending name, `E-DATA-ASSIGN-STRATIFY-UNKNOWN`'s rule:
    # a declaration naming two undeclared attributes earns two, rather than one
    # naming only the first.
    attrs = units.get("attributes") or []
    declared_names = (
        sorted({a for a in attrs if isinstance(a, str)}) if isinstance(attrs, list) else []
    )
    measurements = units.get("measurements")
    measurement_axis = measurements.get("by") if isinstance(measurements, dict) else None
    raw_strata = holdout.get("stratify_by")
    strata = stratum_names(raw_strata)
    if raw_strata is not None and not strata:
        # Present, and normalizing to no names: `stratum_names` returns `()`
        # not just for `""` and `[]` but for anything falsy — `0`, `False`,
        # `{}` all reach here too. Left silent it would be a declaration that
        # changes no behaviour, which is exactly what a truthy read of it
        # hides.
        c.error(
            "E-DATA-HOLDOUT-STRATIFY-UNKNOWN",
            "data.units.holdout.stratify_by",
            "is empty, which names no attribute to balance the split on and changes "
            "no behavior. Name the attribute, or remove the key",
        )
    for name in strata:
        if not isinstance(name, str) or not name:
            c.error(
                "E-DATA-HOLDOUT-STRATIFY-UNKNOWN",
                "data.units.holdout.stratify_by",
                f"names {name!r}, which is not the name of a unit attribute — a split "
                "is balanced on attributes named as strings",
            )
            continue
        if name not in declared_names:
            c.error(
                "E-DATA-HOLDOUT-STRATIFY-UNKNOWN",
                "data.units.holdout.stratify_by",
                f"names {name!r}, which is not a unit attribute — a stratum is read "
                "per unit when the split is drawn, so it has to be one. "
                f"`data.units.attributes` declares "
                f"{', '.join(declared_names) or 'none'}",
            )
            continue
        if isinstance(measurement_axis, str) and measurement_axis == name:
            c.error(
                "E-DATA-HOLDOUT-STRATIFY-UNKNOWN",
                "data.units.holdout.stratify_by",
                f"names {name!r}, which `data.units.measurements.by` also names — the "
                "measurement axis is consumed when a unit's rows collapse and is not "
                "an attribute of the resolved unit, so there is nothing left to "
                "balance the split on. Stratify on an attribute that survives the "
                "collapse",
            )

    # The one check here that reads a block other than `data.units`. Sited in
    # `validate` rather than in `resolve_repeats` because a `fold` level is a
    # perfectly well-formed *repeat*: what is refused is the COMBINATION with a
    # declaration in another block, which `resolve_repeats` never sees. That is
    # also why `replication.REPL_DECLARATION_CODES` is unchanged by this.
    repeats = (doc.get("replication") or {}).get("repeats")
    if isinstance(repeats, list) and any(
        isinstance(level, dict) and level.get("kind") == "fold" for level in repeats
    ):
        c.error(
            "E-DATA-HOLDOUT-FOLD",
            "data.units.holdout",
            "is declared beside a `{kind: fold}` repeat level, and the two are "
            "mutually exclusive — each divides the units for evaluation, so together "
            "they leave `which units is this metric over?` with no single answer. To "
            "hold out a final test set AND cross-validate for model selection, declare "
            "the holdout and do the inner search inside the step over `io.units.train`",
        )

    # `by_attribute`'s two literals, through `units.holdout_values_fault` — one
    # authority for both the verdict (`arms_of`'s set equality) and the wording,
    # so this collected finding and the one `holdout_for` raises at run time
    # cannot drift apart. `stratum_varies_within_cluster`'s own arrangement:
    # the function returns a fault and each caller decides whether to collect
    # it or raise it.
    if (
        method == "by_attribute"
        and roster is not None
        and isinstance(declared_from, str)
        and declared_from
    ):
        fault = holdout_values_fault(roster, declared_from)
        if fault is not None:
            c.error("E-DATA-HOLDOUT-VALUES", "data.units.holdout.from", fault)

    # *Holdout strata survive clustering*, through the fourth
    # `stratum_varies_within_cluster` call site. Reusing that function rather
    # than minting a second notion of constancy is the point: whole clusters go
    # to one side of a holdout, exactly as they do to one side of a fold, so
    # the holdout inherits the rule rather than inventing one. Skipping a name
    # already refused above is not load-bearing here — an undeclared or
    # non-string name carries no value on any unit, so it is constant within
    # every cluster and this loop would report nothing for it either way — but
    # it matches the resample site's shape at the same call, one call over.
    if roster is not None and cluster_by:
        for name in strata:
            if not isinstance(name, str) or name not in declared_names:
                continue  # already refused above
            try:
                offender = stratum_varies_within_cluster(roster, cluster_by, name)
            except ContractError:
                # `clusters_of` refuses a unit carrying no cluster value
                # (`E-DATA-CLUSTER-UNKNOWN`), reported beside this by
                # `_check_cluster_by` or by `_check_units`' own resolution. This
                # module collects rather than raises.
                break
            if offender is not None:
                cluster, values = offender
                c.error(
                    "E-DATA-HOLDOUT-STRATIFY-VARIES",
                    "data.units.holdout.stratify_by",
                    f"names {name!r}, which varies within `{cluster_by}` {cluster} — it "
                    f"carries {', '.join(values)}. A cluster is indivisible and goes "
                    "whole to one side of the split, so a cluster carrying two stratum "
                    "values can be dealt to neither; stratify on an attribute constant "
                    "within a cluster",
                )

    # The zero-size test partition, sited exactly as *Every arm draws units* is:
    # **the unstratified, unclustered `random` draw only**. A stratified or
    # clustered split apportions inside each stratum or moves whole clusters,
    # so the realized test size is not this arithmetic's answer and only the
    # draw knows what it moved — that one is checked where the run performs it.
    # `by_attribute` needs nothing here: `arms_of` above already refuses a
    # literal no unit's value names, which is an empty side by another name,
    # and a second refusal of one fault under two codes is what this omission
    # avoids.
    if (
        method == "random"
        and roster is not None
        and not strata
        and not cluster_by
        and isinstance(declared_frac, (int, float))
        and not isinstance(declared_frac, bool)
        and 0.0 < float(declared_frac) < 1.0
    ):
        # **The denominator is the thinnest POPULATED cell**, not the roster,
        # when the design has a cell structure — because that is the sub-roster
        # `units.holdout_within_cells` draws inside, and a `frac` that clears
        # the roster does not clear every cell of it. `holdout_sizes` is
        # largest-remainder and so non-decreasing in `n`, which is why this
        # REPLACES the roster-wide bound rather than joining it: a thinnest
        # cell that clears leaves nothing for a roster-wide test to catch.
        # `populated_cells` is the predicate rather than a second spelling of
        # it, and it is the same projection the draw loops over, so the cell
        # this names is a cell that will really be drawn in — an empty cell is
        # dropped by both.
        bound_cell: tuple[tuple[str, str], ...] | None = None
        bound_n = len(roster)
        populated = populated_cells(cells or {})
        if populated:
            bound_cell, bound_keys = min(populated, key=lambda item: len(item[1]))
            bound_n = len(bound_keys)
        _train_size, test_size = holdout_sizes(bound_n, float(declared_frac))
        if test_size == 0:
            where = (
                f"{bound_n} resolved units"
                if bound_cell is None
                else f"the {bound_n} resolved units in cell {cell_label(bound_cell)}, the "
                "thinnest of the design's cells and the sub-roster the split is drawn inside"
            )
            c.error(
                "E-DATA-HOLDOUT-EMPTY",
                "data.units.holdout.frac",
                f"is {declared_frac} over {where}, which apportions "
                "the test side zero of them — every metric would be over nothing. Widen "
                "`frac`, or resolve a larger roster",
            )


def _accounted_attribute_names(doc: dict[str, Any], units: dict[str, Any]) -> set[str]:
    """Attribute names another declaration already accounts for, so the
    undeclared-cluster warning stays off them.

    `reference.md`'s `W-DATA-CLUSTER-UNDECLARED` row names four: an attribute a
    `sweep.groups` axis names or an `assign.from` reads, since every `between`
    design's arm would otherwise report one; any `stratify_by`, which must be
    constant within a cluster and so is coarser than one; and
    `statistics.null_test`'s `shuffle`, which names the label a cluster is what
    shuffling *respects*.

    `stratify_by` is collected by walking for the key rather than from an
    enumerated list of the blocks that carry one (`assign.<axis>`, a `fold` repeat
    level, `statistics.resample`). The row says *any* `stratify_by`, and an
    enumeration would quietly stop matching the row the first time a block gains
    one — which is a live prospect while three of those blocks are still unbuilt.

    The walk is over the four blocks that describe the design, **not the whole
    document**: `parameters` is the template's namespace, and a template free to
    declare a parameter of any name is free to declare one called `stratify_by`,
    which would silence a real cluster column for no reason a reader could see.
    """
    accounted: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "stratify_by":
                    if isinstance(value, str):
                        accounted.add(value)
                    elif isinstance(value, list):
                        accounted.update(v for v in value if isinstance(v, str))
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    for block in ("data", "sweep", "replication", "statistics"):
        walk(doc.get(block))
    groups = (doc.get("sweep") or {}).get("groups") or []
    if isinstance(groups, list):
        for axis in groups:
            if isinstance(axis, dict) and isinstance(axis.get("by"), str):
                accounted.add(axis["by"])
    assign = units.get("assign") or {}
    if isinstance(assign, dict):
        for axis_name, block in assign.items():
            # The axis name is the default `from`, per § The one config file's
            # `from: arm  # by_attribute; defaults to the axis name`, so an
            # assignment reading its own column accounts for it either way.
            if isinstance(axis_name, str):
                accounted.add(axis_name)
            if isinstance(block, dict) and isinstance(block.get("from"), str):
                accounted.add(block["from"])
    null_test = (doc.get("statistics") or {}).get("null_test") or {}
    if isinstance(null_test, dict) and isinstance(null_test.get("shuffle"), str):
        accounted.add(null_test["shuffle"])
    return accounted


def _warn_undeclared_cluster(
    doc: dict[str, Any], units: dict[str, Any], roster: UnitList | None, c: Collector
) -> None:
    """`W-DATA-CLUSTER-UNDECLARED` — an attribute that looks like a cluster
    identifier while `cluster_by` is unset.

    The four clauses are `reference.md`'s row verbatim, and each earns its place
    against a false positive the documents themselves contain:

    1. **every unit carries a value for it** — a column some units lack is not a
       grain the whole roster is partitioned on;
    2. **its values are not all numeric**, read through `units.is_measurement_numeric`
       so a table-sourced `"37"` counts as the number it holds — this is what keeps
       the warning off `age`, `dose` and `latency`, whose distinct values are also
       each held by several units. Its cost is a missed integer-coded identifier,
       which is the right way to be wrong: a numeric column with repeated values is
       a measurement far more often than an identifier;
    3. **more than two distinct values** — two is a level set like `label` or `sex`,
       and a cluster-robust *t* has df = clusters − 1, so two clusters is no
       inference base at all;
    4. **at least one value held by more than one unit** — otherwise the column is
       effectively a second key.

    Plus the exclusions `_accounted_attribute_names` collects. `statistics.report_by`
    is deliberately **not** among them: a run that reports by `site` while `site`
    really is a cluster wants both declarations, not silence.

    Deliberately **not** built on `units.clusters_of`. That function answers "which
    cluster is this unit in" for a declaration that exists — and raises when a unit
    carries no value, which is clause 1's ordinary case here rather than a fault.
    This is a scan for *candidates*, a different question, and reading it as a
    second notion of membership is the misreading to avoid: nothing here decides
    what any cluster contains.

    Reported for the first candidate in sorted order rather than for each, as the
    weight warning is and for the same reason: `cluster_by` takes one name and the
    remedy is the same sentence whichever candidate a reader looks at.
    """
    if roster is None:
        return
    accounted = _accounted_attribute_names(doc, units)
    for name in sorted({n for u in roster for n in u.attributes}):
        if name in accounted:
            continue
        if any(name not in u.attributes for u in roster):
            continue
        values = [u.attributes[name] for u in roster]
        # An empty cell is "carries no value", not "carries the empty label": a
        # sparse column would otherwise satisfy clauses 2 and 4 together on its
        # blanks alone, which is the commonest false positive this clause has.
        if any(v is None or (isinstance(v, str) and not v.strip()) for v in values):
            continue
        if all(is_measurement_numeric(v) for v in values):
            continue
        # Stringified for the same reason `clusters_of` stringifies: a cluster id is
        # a label, and a hand-built roster may carry something `set` cannot hold.
        counts = Counter(str(v) for v in values)
        if len(counts) <= 2:
            continue
        if max(counts.values()) < 2:
            continue
        c.warn(
            "W-DATA-CLUSTER-UNDECLARED",
            f"data.units.attributes.{name}",
            f"{name!r} holds {len(counts)} repeated non-numeric labels across "
            f"{len(roster)} units — too few to be a second key and too many to be a "
            "level set, which is the shape of a cluster identifier — but "
            "`data.units.cluster_by` is unset, so core treats every unit as an "
            "independent draw. Intervals computed that way are too narrow, and a fold "
            "may put one cluster on both sides of the split. Set "
            "`data.units.cluster_by` if it is a cluster, and ignore this if the units "
            "really are independent",
        )
        return


# Refusals that are properties of the DECLARATION, so `validate` reports them as
# findings. Anything else `resolve_repeats` raises is a genuine fault and still
# propagates — swallowing all of them is how a real error becomes a silent pass.
# This set is deliberately narrow: a future code `resolve_repeats` raises that is
# not added here propagates rather than being silently absorbed into a finding.
# `test_an_unresolved_repl_code_is_not_swallowed` pins that escape path.
REPL_DECLARATION_CODES = frozenset(
    {
        "E-REPL-FOLD-K",
        "E-REPL-FOLD-K-TOO-LARGE",
        "E-REPL-LEVEL-DUPLICATE",
        "E-REPL-LEVEL-FIELD",
        "E-REPL-LEVEL-DEPTH",
        "E-REPL-LEVEL-BATCH-INNER",
        "E-REPL-KIND",
        "E-REPL-N",
        "E-REPL-SEED-COLLISION",
    }
)


def _declared_count(level: dict[str, Any]) -> Any:
    """The count key this level's kind actually takes, exactly as declared.

    `reference.md` § Repeat kinds gives each kind its own fields *and only these*:
    a `fold` takes `k` (and an optional `stratify_by`), a `seed` and a `batch`
    take `n`. Reading `n` first and falling back to `k` for every kind is what let
    `{kind: fold, k: 2, n: 5}` report a five-execution budget for a run that
    executes two folds — one declaration meaning two different things to two
    readers. `resolve_repeats` refuses that cross-talk outright
    (`E-REPL-LEVEL-FIELD`); this function is the arithmetic half of the same
    rule, so the number every check here derives is the number the run executes.
    """
    return level.get("k") if level.get("kind") == "fold" else level.get("n")


def _level_count(level: dict[str, Any], fold_basis: int | None) -> int | None:
    """This level's count as a number, or `None` when there isn't one to have.

    `None` covers two cases the callers separate with `_declared_count`: nothing
    declared at all (which contributes 1×), and a count declared but unresolvable
    — `{kind: fold, k: all}` against a roster that did not resolve, or any other
    string `k`, which `resolve_repeats` reports by name. A resolvable `k: all` is
    the fold basis — the roster size, or the cluster count when
    `data.units.cluster_by` is declared, leave-one-out being leave-one-*cluster*-out
    there — the same number `_fold_k` gives the run.
    """
    count = _declared_count(level)
    if count == "all" and level.get("kind") == "fold":
        return fold_basis
    if isinstance(count, bool) or not isinstance(count, int | float):
        return None
    return int(count)


def _check_replication(
    doc: dict[str, Any],
    template: Any,
    c: Collector,
    *,
    experiment: Any | None = None,
    fold_basis: int | None = None,
    fold_cell: tuple[tuple[str, str], ...] | None = None,
) -> None:
    levels = ((doc.get("replication") or {}).get("repeats")) or []
    # A `fold` level partitions units into train/test splits; with no
    # `data.units` declared there is no roster to partition at all. Left
    # unchecked, `resolve_repeats` accepts a fixed `k` with `fold_basis=None`
    # (only `k: all` needs a count, and that already reports `E-REPL-FOLD-K`) —
    # so a config with a fold and no units would validate clean and then, at
    # `run`, either crash (`fold_members_for` zips a fold's members against no
    # partitions) or, worse, complete: `k` roster-less repeats all executing
    # against nothing while `sweep.yaml`/`run.yaml` describe a k-fold
    # cross-validation that never happened. Caught here, at the declaration,
    # rather than guarded at `run` — a config that validates clean must not
    # then fail (see `docs/superpowers/spec-defects.md`).
    if any(level.get("kind") == "fold" for level in levels) and not (doc.get("data") or {}).get(
        "units"
    ):
        c.error(
            "E-REPL-FOLD-NO-UNITS",
            "replication.repeats",
            "a `fold` level partitions units, and `data.units` is not declared; "
            "there is nothing to partition",
        )
    total = 1
    any_invalid = False
    has_unresolved_fold = False
    for level in levels:
        count = _level_count(level, fold_basis)
        if count is None and isinstance(_declared_count(level), str):
            # The count is declared as a word rather than a number and could not
            # be resolved — `{kind: fold, k: all}` with no roster, or any other
            # string `k`, which `resolve_repeats` reports by name as
            # `E-REPL-FOLD-K` below. The total from here on is not a fact: don't
            # fold a guess into it, and don't derive a floor warning from it.
            # Deliberately `str` rather than "not a number": a `n: yes` (a bool
            # under YAML) is the one repeat `resolve_repeats` will execute, so
            # treating it as unknown would suppress the budget check for the
            # whole config over a typo — the silent skip this pass exists to end.
            has_unresolved_fold = True
            continue
        if count is not None and int(count) < 1:
            c.error(
                "E-REPL-N",
                "replication.repeats",
                f"declares {count}, which executes nothing; the count must be at least 1",
            )
            any_invalid = True
            continue
        total *= 1 if count is None else int(count)
    if any_invalid:
        return  # a floor warning derived from an invalid design would be noise
    if not has_unresolved_fold and total < template.default_repeats:
        c.warn(
            "W-REPL-FLOOR",
            "replication.repeats",
            f"total of {total} is below this convention class's default of "
            f"{template.default_repeats}",
        )

    # `resolve_repeats` raises for refusals that are properties of the declaration
    # itself — fold, duplicate kinds, and depth past two levels among them. At run
    # time raising is right; here `validate` collects, so translate rather than let
    # it escape. The digest is a placeholder: seeds are irrelevant to a declaration
    # check, only the shape of `replication.repeats` is. `fold_basis` is the count
    # `validate_config` already resolved from the roster — its units, or its
    # clusters under `data.units.cluster_by` — threaded through rather than
    # resolved again: `k: all` and an oversized `k` can only be checked against a
    # real count. When the roster or its clusters failed to resolve, `fold_basis`
    # is `None` and `k: all` reports
    # `E-REPL-FOLD-K`, which is honest: the fold count genuinely cannot be known,
    # and the roster's own finding is already reported beside it.
    try:
        # `fold_cell` travels with `fold_basis` for the reason `_fold_k` states:
        # a bound taken over one cell and reported against the whole roster's
        # count sends a reader to the wrong declaration. This forwarding IS the
        # third emit site of `E-REPL-FOLD-K-TOO-LARGE` — the `c.error` below
        # prints `str(exc)`, so the clause reaches `validate` only if the label
        # reaches `_fold_k`.
        #
        # **Why `E-REPL-FOLD-K-TOO-LARGE` still has ONE § Errors row, in the
        # `validate` table, while `_fold_k` raises it twice.** § Errors core
        # raises covers the codes core raises where no `validate` pass is
        # running; that would owe this code a row only if a config could
        # validate clean and then meet the raise. It cannot: `validate`'s cell
        # draw and `_prepare_run`'s call `units.assignment_for` over the same
        # roster at the same `design_digest(doc)` through the same skip rules,
        # so they resolve the same cells and take the same minimum — a `k` this
        # check clears is a `k` `_fold_k` clears at run. **Including the
        # declaration they read it from**, which is the one input the two spell
        # differently: `validate_config` passes `_units_declaration(...) or {}`
        # and `_prepare_run` passes `(doc.get("data") or {}).get("units")`.
        # `_units_declaration` returns that same object or `None`, and it
        # returns `None` for a non-mapping only after reporting
        # `E-CONFIG-SHAPE` — so for any config that validates clean the two
        # accessors are the same mapping, and neither can see an `assign` block
        # the other cannot. Where the draw faults,
        # `_resolved_cells` returns `None` and the roster-wide basis is used at
        # BOTH ends, since the fault is the same fault; the config then meets
        # that fault itself, under its own code, rather than this one.
        # `E-DATA-HOLDOUT-EMPTY` has rows in both tables because its two bounds
        # are genuinely two computations (`_check_holdout`'s against a declared
        # `frac`, `holdout_for`'s against a realized split), which is the
        # asymmetry, not an inconsistency.
        resolve_repeats(doc, "validate", fold_basis=fold_basis, fold_cell=fold_cell)
    except ContractError as exc:
        if exc.code in REPL_DECLARATION_CODES:
            c.error(exc.code, "replication.repeats", str(exc))
        else:
            raise

    # A `batch` says *when*, not *what*: it re-executes the pipeline to capture the
    # apparatus drifting between blocks. If nothing in the pipeline declares itself
    # nondeterministic, there is no drift to capture. `experiment is not None` is
    # load-bearing — when the import failed, `E-ENTRYPOINT-IMPORT` is already
    # reported, and a second finding about a pipeline nobody could load is noise.
    kinds = {lv.get("kind") for lv in levels if isinstance(lv, dict)}
    if "batch" in kinds and experiment is not None:
        if not any(getattr(s, "nondeterministic", False) for s in experiment.steps):
            c.warn(
                "W-REPL-DETERMINISTIC",
                "replication.repeats",
                "declares a `batch` level, but no step sets `nondeterministic = True`; "
                "under a fully deterministic pipeline a batch recomputes the same answer "
                "each time, so its dispersion is a row of zeros bought with n× the compute",
            )

    order = (doc.get("replication") or {}).get("order")
    if order is not None and order not in ("as_declared", "randomized"):
        c.error(
            "E-REPL-ORDER",
            "replication.order",
            f"is `{order}`; the only orders are `as_declared` and `randomized`",
        )


def _check_unimplemented(doc: dict[str, Any], c: Collector) -> None:
    """Declared-but-unimplemented blocks, refused rather than silently ignored.

    This build expands `sweep.baseline`, `sweep.grid`, `sweep.paired`,
    `sweep.sample` and `sweep.ablate` only. Both declared orders are honored —
    `randomized` shuffles within each batch and `as_declared` leaves the plan's
    step-major layout alone.

    A `baseline` fixing only *some* of the swept axes is no longer refused here:
    `sweep._baseline_cells` expands it over the rest, one baseline condition per
    cell of the unfixed axes, which is § Expansion modes' second row and the row
    it tells a reader to prefer. Each condition is compared against the baseline
    of its own cell (`contrasts.baseline_for`), and a baseline is never a
    comparison's subject, so the correction family counts comparisons rather
    than conditions.

    `sweep.paired` is no longer refused here: `_axes` composes it
    as a single axis whose cells set several paths at once, per § Expansion
    modes — `_check_shape` guards its container and entry shapes, and
    `_check_sweep` refuses a path it shares with another axis-shaped mode
    (`E-SWEEP-PATH-DUPLICATE`), the same way a bad `grid` shape or an
    unresolvable `grid` path already were. Neither is `sweep.sample`, which
    composes as one axis of `n` realized draws seeded from the design digest:
    `_check_shape` guards every shape `_sample_cells` reads and `_check_sweep`
    reports the value-level residue as `E-SWEEP-SAMPLE-INVALID`, its paths
    through the same `E-SWEEP-PATH-UNKNOWN` `grid` uses, and its bounds through
    the same `E-PARAM-VALUE` (§ Validation, "Sample ranges"). Neither is
    `sweep.ablate`, which `expand` applies after the product as the one mode that
    does not multiply: `_check_shape` guards every shape `ablation_changes`
    reads, and `_check_sweep` checks each `override` value against its own
    `Param` on the same `E-PARAM-VALUE`/`E-SWEEP-VALUE-UNNAMEABLE` pair a `grid`
    value gets. Its composition rules are checked there too, as of this slice —
    a `remove` on a parameter that can hold neither `false` nor `null`
    (`E-SWEEP-ABLATE-TARGET`), `ablate` without a `baseline`
    (`E-SWEEP-ABLATE-BASELINE-MISSING`), and `ablate` crossed with a parameter
    axis (`E-SWEEP-ABLATE-CROSSED`). § Validation's "Ablation baseline isn't a
    group level" needed a group axis to have a level for a baseline to fix, and
    is checked here too, beside its sibling "Baseline isn't a group level"
    (`E-SWEEP-ABLATE-BASELINE-GROUP` and `E-SWEEP-BASELINE-GROUP`) — one rule
    under two codes, guarded exclusively, because the same declaration duplicates
    a level under the plain product and hides every other level under `ablate`.
    `sweep.groups` is no longer refused here, and
    neither is `data.units.allocation: between` nor `data.units.assign`: `expand`
    crosses a group axis into the condition product, `_check_assign` checks
    `allocation` and `assign` against each other and against `sweep.groups` for
    real, `units.arm_members` narrows a condition's roster to its own arm, and
    `cli.py` writes `allocation.json` and `provenance.allocation_hash` — so each
    declaration changes the record, which is the test this family applies.
    `data.units.holdout` is no longer among
    them either: `_check_holdout` checks the declaration for real,
    `_resolved_holdout` realizes the partition once per run over the run's own
    digest, `io.units`/`io.units.train` see the test and training halves,
    and `cli.py` narrows every denominator to the test partition and writes
    `allocation.json` and `provenance.allocation_hash` — so the declaration
    changes the record, which is the test this family applies.
    `data.units.measurements` is no longer among them either: `resolve_units` collapses
    the rows an input table carries, `StepIO.finalize` collapses the ones a step
    records under `measurement=`, and `technical_n` reaches every metric block,
    so the declaration changes the record. Neither are `weight_by` and
    `cluster_by`: each decides an interval's construction, and a `cluster_by`
    decides a `fold`'s partition as well. Each of these
    would otherwise validate clean and then run something other than what the
    config describes — the same class of failure `resolve_repeats` already
    refuses for repeat levels: `E-REPL-LEVEL-DUPLICATE` for two levels of the same
    kind, and `E-REPL-LEVEL-DEPTH` past two levels, and
    `E-REPL-LEVEL-BATCH-INNER` for a `batch` that is not the outermost level.
    `batch` and `fold` themselves are no longer refused — both are supported
    kinds. `statistics.resample` is no longer in this family: `_check_resample`
    checks the declaration for real — the method enum, the 80-draw floor, the
    strata against `data.units.attributes`, the roster's absence, and the
    cluster count — so a fault in the block is named on its own terms rather
    than the whole block being refused. The *honouring* — resolving the block
    in `cli.command_run` and threading it into the interval constructions —
    had not landed as of commit `2fdc957` (H4a task 12, the wholesale
    refusal's retirement): check `cli.command_run`'s `derived_metric_draws`
    directly rather than trusting this sentence, since two tasks after that
    commit close exactly this gap. `statistics.null_test` is no longer in this
    family either: `_check_null_test` now checks the declaration for real —
    the `method` enum, the `n` floor, `shuffle`, the level derivation, and the
    no-roster and `report_by` refusals — and `cli.command_run` computes and
    records a p-value at both p-value homes (H4d tasks 7–20). A top-level
    `hypotheses` block is refused the same
    way too — a pre-registered hypothesis that runs and reports success while
    honoring neither is the same silent-no-op class. `statistics.contrasts` is no longer in
    this family: `_check_contrasts` now resolves and checks each declared entry
    instead of refusing the block wholesale. Neither is `statistics.report_by`,
    which `_check_report_by` now checks for real instead of refusing wholesale.
    Neither is `statistics.correction`,
    which `cli.py` now applies: every comparison carries `ci95_corrected`,
    `correction_level`, `family_size`, and `family`, so what this module owes it
    is the value checks below (`E-STATS-CORRECTION-UNKNOWN`,
    `W-STATS-CORRECTION-INAPPLICABLE`) plus `W-STATS-FAMILY` on the one value that
    opts out — `none`, which corrects nothing and records `correction: null` to
    say so. Each remaining message says
    plainly that the block is honored in a later slice, so a user does not read this as
    their config being malformed.
    """
    sweep = doc.get("sweep") or {}

    # A `baseline` declared beside a `sample` axis. `reference.md` § Sweeps and
    # repeats states that the correction family "counts conditions from `grid`,
    # `paired`, `ablate`, and `groups`, and skips `sample`", because "forty sobol
    # draws … are forty points feeding one downstream curve, and nobody claims a
    # finding about draw 17 against draw 1". Nothing in this build implements
    # that exclusion: `contrasts.resolve_contrasts` emits one `vs_baseline`
    # comparison per non-baseline condition whatever mode produced it, and
    # `cli.command_run` corrects every interval against the whole set — so a
    # `grid × sample` design is corrected against six comparisons where the
    # document says two, and the intervals a reader is shown are narrower than
    # the design supports. The declared design is not the executed design, which
    # is the failure every other refusal in this function exists to prevent.
    #
    # **A `sample` sweep with no `baseline` is untouched and stays legal**:
    # `resolve_contrasts` generates a comparison only against a *declared*
    # baseline, so a sample-only sweep produces none and nothing is inflated. A
    # declared `statistics.contrasts` entry is untouched too — its members are
    # named by the user rather than generated per condition, so the family is
    # exactly what was asked for.
    #
    # This restores, narrowly, the protection `E-SWEEP-BASELINE-PARTIAL` gave
    # until it was retired: that refusal is what made `baseline` + `sample`
    # unreachable, which is why the family semantics were never needed. Retiring
    # it made the shape reachable without implementing them. The exclusion is
    # `statistics`-family work rather than sweep work, so it lands with the slice
    # that owns the correction family, and this refusal retires with it.
    #
    # **Whoever retires it: grep `E-SWEEP-SAMPLE-BASELINE` first.** Two comments
    # elsewhere argue from this refusal rather than merely mentioning it —
    # `sweep._baseline_cells` ("only `paired` reaches it from a baseline today")
    # and `sweep.check_swept_value` — and both become false the moment a baseline
    # may sit beside a `sample` axis again. They are marked as temporary at each
    # site; this is the marker that makes them findable from here.
    if sweep.get("baseline") and sweep.get("sample"):
        c.error(
            "E-SWEEP-SAMPLE-BASELINE",
            "sweep.baseline",
            "is declared beside a `sweep.sample` axis, so every non-baseline cell — every "
            "combination of a draw with the other axes' levels, not every draw — becomes a "
            "comparison against it, and a `sample` draw is not a comparison: the correction family "
            "skips `sample` conditions, which is specified but not implemented in this "
            "build, so each interval would be corrected against a family several times the "
            "size the design has. Sample draws feed one downstream fit rather than being "
            "compared to a reference, so declare only one of the two here; compare a "
            "specific pair with a declared `statistics.contrasts` entry, or run the "
            "reference condition as its own run and join the two in a `study`. The "
            "combination will be honored once the family excludes drawn conditions",
        )

    # No `data.units` block is refused wholesale any more. Each block
    # this function used to hold — `allocation`/`assign`, `cluster_by`,
    # `weight_by`, `measurements`, and now `holdout` — is checked for real by
    # its own function instead, and each changes the run's record rather than
    # validating clean and then doing nothing:
    #
    # `allocation: between` and `assign` are checked by `_check_assign` —
    # against each other and against `sweep.groups` — reporting an out-of-enum
    # `allocation` value under `E-DATA-ALLOCATION-METHOD`, the pairing faults
    # under `E-DATA-ALLOCATION-NO-ARMS`/`E-DATA-ASSIGN-MISSING`/
    # `E-DATA-ALLOCATION-WITHIN-ARMS`, and a malformed or unresolvable `assign`
    # block under `E-DATA-ASSIGN-METHOD`/`E-DATA-ASSIGN-UNKNOWN`/
    # `E-DATA-ASSIGN-LEVELS`. `units.arm_members` narrows a condition's roster
    # to its own arm, and `cli.py` writes `allocation.json` and
    # `provenance.allocation_hash`.
    #
    # `cluster_by` is checked by `_check_cluster_by`; `attrition` counts the
    # clusters, `partition_units` keeps one out of two folds, and
    # `summarize_step` gives every `basis: units` column a cluster-robust
    # interval. A derived metric under a declared `cluster_by` also resamples,
    # through `stats.percentile_of_derived_clustered` (H4d task 15a),
    # dispatched from `stats.summarize_step` — no separate `validate` check
    # for it, since whether a template's `aggregate` derives anything at all
    # is not knowable from a declaration.
    #
    # `weight_by` is checked by `_check_weight_by`; `attrition` computes
    # Kish's effective size from it, and `summarize_step` weights every
    # `basis: units` column's value and interval. A weighted run now also
    # publishes a weighted contrast — the paired constructions take the same
    # weights the per-condition values do, and the record carries
    # `weighted_by` and `n_paired_effective` — so nothing about `weight_by`
    # is checked here at all.
    #
    # `measurements` is checked by `_check_measurements`; `resolve_units`
    # collapses the input path, `finalize` collapses the step path, and
    # `technical_n` reaches every metric block.
    #
    # `holdout` is checked by `_check_holdout`; `_resolved_holdout` realizes the
    # partition once per run, `io.units`/`io.units.train` see the two halves,
    # `cli.py` narrows the denominator to the test partition and writes
    # `allocation.json` and `provenance.allocation_hash`.

    # `statistics.contrasts`, `statistics.report_by` and the top-level
    # `hypotheses` block used to be in this list too; they are now checked for
    # real by `_check_contrasts`, `_check_report_by` and `_check_hypotheses`
    # instead of being refused wholesale — `cli.py` evaluates every declared
    # hypothesis and writes its verdict, so the declaration changes the record.
    # `statistics.correction` is not in it either, and no longer for a disclosure
    # reason: `cli.py` applies it, so a declared correction changes the record —
    # the correction checks further down this module check its *value* instead,
    # and warn only on `none`, which corrects nothing by request.
    # `statistics.null_test` is not in it either, as of H4d: `_check_null_test`
    # checks it for real (above this function's own docstring) and
    # `cli.command_run` computes and records the p-value it declares.


def _repeat_total(doc: dict[str, Any], fold_basis: int | None) -> int | None:
    """The product of every repeat level's count, permissively: an invalid level
    (`n < 1`) is already reported by `_check_replication` under its own identifier,
    so this treats it as absent rather than reporting the same defect twice under
    `W-EXEC-BUDGET`.

    `{kind: fold, k: all}` resolves against `fold_basis` — the roster
    `_check_units` already resolved, counted in clusters when
    `data.units.cluster_by` is declared — because leave-one-out is the single design
    `W-EXEC-BUDGET` matters most for (`reference.md` § Sweeps and repeats), and
    it was the one design that could not produce the warning while this function
    read a string and gave up.

    Returns `None` only when a count declared as a *word* cannot be resolved: a
    `k: all` whose roster did not resolve, or a string `k` that is not `all`
    (reported by name as `E-REPL-FOLD-K`). Anything else unreadable — a `n: yes`,
    which YAML parses as a bool — executes 1× and is reported under its own
    identifier, so it contributes 1× here rather than suppressing the check for
    the whole config. Silently treating an unresolved level as
    contributing 1× would understate the total by the roster size — a wrong
    small number is worse than admitting the total is unknown, so the caller
    skips the check rather than trust a guess.
    """
    levels = ((doc.get("replication") or {}).get("repeats")) or []
    total = 1
    for level in levels:
        count = _level_count(level, fold_basis)
        if count is None:
            # A string count that did not resolve is genuinely unknown; anything
            # else unreadable (a bool, a list) is reported under its own
            # identifier and executes 1×, so it must not suppress this check.
            if isinstance(_declared_count(level), str):
                return None
            continue
        if count >= 1:
            total *= count
    return total


def _check_sampled_values(
    sample: Any, spec: dict[str, Any], conditions: list[Any], c: Collector
) -> None:
    """Every value `sweep.sample` actually draws satisfies its own `Param`.

    **Checking the bounds is not checking the values, and only the values
    execute.** `uniform: [10, 200]` over `Param(int, ge=2)` has two perfectly
    legal integer bounds and draws `118.38516808291541`, which a step then reads
    where the template declares an `int`; `int_uniform: [10, 50]` over
    `Param(int, choices=[10, 50])` passes on both endpoints and draws `37`,
    which is neither choice. Both validate clean under a bounds-only check and
    then run a config § Validation's "Types" and "Choices" rows promise to
    refuse — the validates-clean-misbehaves-at-run class, one level up from the
    shape class `_check_shape` and `sample_fault` close.

    **The realized values are checked rather than the declaration's *form*,**
    deliberately. Refusing "a non-`int_uniform` range on an `int` parameter"
    would catch the first example and nothing else: it says nothing about
    `choices`, `pattern`, `ge`/`lt`, or a `log_uniform` range that dips under a
    `gt=0`, and the constraint vocabulary is closed but not small. What executes
    is the drawn value, so that is what `Param.check` is asked about — the same
    call `grid` values and `baseline` values already go through, on the same
    identifier (`E-PARAM-VALUE`), rather than a `sample`-shaped approximation of
    it.

    Its cost, stated rather than hidden: the finding names a value the user did
    not literally write. That is why the message quotes both the drawn value and
    the range that produced it. It is not flaky — the draw is deterministic
    given the config, so "this config draws an illegal value" is as stable a
    claim as any other check here, and re-running `validate` on an unedited
    config reports the same value. Only the *first* offending draw per path is
    reported: `n: 50` over a wrong-typed range is one mistake, not fifty.
    """
    if not sample or sample_fault(sample) is not None:
        return
    for path in sample["ranges"]:
        if path not in spec:
            continue  # already reported as `E-SWEEP-PATH-UNKNOWN`
        for condition in conditions:
            if path not in condition.values:
                continue
            value = condition.values[path]
            problem = spec[path].check(value)
            if problem is None:
                continue
            form = next(iter(sample["ranges"][path]))
            hint = ""
            if spec[path].type_ is int and form != "int_uniform":
                hint = " — `int_uniform` is the form that draws integers"
            c.error(
                "E-PARAM-VALUE",
                f"sweep.sample.ranges.{path}.{form}",
                f"draws `{render_value(value)}`, which {problem.lstrip()}{hint}",
            )
            break


def _check_sweep(
    doc: dict[str, Any], template: Any, c: Collector, *, fold_basis: int | None = None
) -> None:
    """Checks that only become reachable once a sweep actually expands: an
    unrecognised mode, an axis with nothing in it, a swept path the template
    doesn't declare, a value the spec itself rejects, a value that can't render
    into a condition label, the execution budget, and the multiplicity family
    an enumerated sweep creates. `sweep.expand` is the single source of the
    condition count — re-deriving it here is exactly the drift Task 4 was
    told not to reintroduce.

    `E-SWEEP-EXPANDS-EMPTY` is a backstop beneath the per-axis checks above,
    not a replacement for them: it refuses on the *result* of `expand(doc)`
    being zero conditions, whatever shape of `sweep` produced that — an empty
    `grid` axis still gets the specific `E-SWEEP-AXIS-EMPTY` diagnosis (this
    check runs after, so it never displaces that one), but a declared `sweep`
    with no shape anyone enumerated here — `{grid: {}}`, or a hand-written
    block of falsy keys — is still caught, because it is checked mechanically
    against what would actually execute rather than against a list of shapes
    someone thought of. A run that would otherwise execute zero conditions
    while reporting `status: completed` is exactly the failure this project
    treats as worst: a record describing an experiment nobody performed.
    """
    import difflib

    sweep = doc.get("sweep") or {}
    # Not a literal set: `sweep.SWEEP_MODES` is `PRODUCT_MODES +
    # NON_PRODUCT_MODES`, and this check is the vocabulary's choke point — a
    # mode absent from it is refused here, so no config can use one. Reading the
    # derived tuple is what makes `E-SWEEP-ABLATE-CROSSED`'s "a second parameter
    # axis" true of a mode added later: it cannot become usable without being
    # classified as a product mode or not. A literal here would let the two
    # drift, with this check accepting a mode `parameter_axis_modes_present` has
    # never heard of. Classification is two questions since the split, and only
    # the product one closes the vocabulary; that a product mode must also be
    # placed in or out of `PARAMETER_AXIS_MODES` is pinned in `tests/test_sweep.py`.
    for key in sweep:
        if key not in SWEEP_MODES:
            near = difflib.get_close_matches(key, sorted(SWEEP_MODES), n=1)
            hint = f" — did you mean `{near[0]}`?" if near else ""
            c.error(
                "E-SWEEP-KEY-UNKNOWN",
                f"sweep.{key}",
                # The vocabulary comes from `SWEEP_MODES`, the same tuple the
                # check gates on. Naming the *implemented* modes here instead
                # made the message contradict its own emit site the moment the
                # two lists diverged: this branch accepts `groups` and the
                # sentence said `expand` does not understand it. A mode that is
                # recognized but not built is refused by its own
                # `-UNSUPPORTED` code, which is where that fact belongs.
                f"is not a sweep mode{hint} — the modes are "
                + ", ".join(f"`{mode}`" for mode in sorted(SWEEP_MODES))
                + ", so an unrecognised key would expand to zero conditions and the run "
                "would execute nothing while reporting success",
            )

    spec = template.parameter_spec

    def _path_resolves(path: str, where: str) -> bool:
        """`path` names a parameter this template declares. Shared by `grid` and
        `baseline` deliberately: both fix a value at a dotted `parameters` path,
        and two copies of this check is how the two drift apart."""
        if path in spec:
            return True
        near = difflib.get_close_matches(path, list(spec), n=1)
        hint = f" — did you mean `{near[0]}`?" if near else ""
        c.error("E-SWEEP-PATH-UNKNOWN", where, f"is not a parameter of this template{hint}")
        return False

    def _value_checks(path: str, value: Any, where: str, nameable: bool) -> None:
        """The value satisfies its own `Param`, and — for a value that will be
        rendered into a condition label — is nameable.

        `nameable` is False for a `baseline` entry: `sweep.label_for` returns the
        literal `baseline` for a baseline condition, so its fixed values are never
        rendered into a label, and refusing an unnameable one would reject a config
        that is legal (`reference.md`:1419 labels a per-cell baseline by the axes it
        leaves *free*, so this stays true when that expansion lands).
        """
        problem = spec[path].check(value)
        if problem:
            c.error("E-PARAM-VALUE", where, problem)
        if nameable:
            unnameable = check_swept_value(value)
            if unnameable:
                c.error("E-SWEEP-VALUE-UNNAMEABLE", where, unnameable)

    grid = sweep.get("grid") or {}
    for path, values in grid.items():
        if not values:
            c.error(
                "E-SWEEP-AXIS-EMPTY",
                f"sweep.grid.{path}",
                "declares no values, so the sweep expands to zero conditions and the run "
                "would execute nothing while reporting success",
            )
            continue
        if not _path_resolves(path, f"sweep.grid.{path}"):
            continue
        for i, value in enumerate(values):
            _value_checks(path, value, f"sweep.grid.{path}[{i}]", nameable=True)

    # `sweep.paired`, through the same two checks `grid` gets, for the same
    # reason and in `_axes` order. A `paired` entry is structurally a `grid`
    # cell written the other way round — one value per path, several paths per
    # condition — so every fault a `grid` value can carry, a `paired` value
    # carries identically: `resolve_condition_cfg`'s `setdefault` walk *creates*
    # a misspelled path (`analysis.methdo`) rather than failing on it, so the
    # swept parameter keeps the config's own value in every condition while each
    # condition still earns a distinct `parameters_hash` — one experiment
    # executed twice and recorded as a two-arm sweep, which is
    # `experimental-designs.md` § Mistakes core prevents' "a typo'd parameter
    # silently using a default". `nameable=True` because a `paired` value IS
    # what `label_for` renders (unlike a `baseline` one): a value carrying `/`
    # passes into a condition *directory* segment, so `analysis.method: ../../x`
    # would resolve outside the condition directory.
    #
    # Task 2 promoted `paired` from refused to executable and left these behind;
    # it was the sole axis-shaped mode without them.
    #
    # Both `isinstance` guards are unreachable today — `_check_shape` refuses a
    # non-list `paired`, a non-mapping entry and a non-string key fatally, and
    # `validate_config` returns before this function runs — and are kept anyway,
    # exactly as the `ablate.override` loop keeps its own: `_check_sweep` is
    # called directly by tests, and `validate` collects findings and never
    # raises.
    paired = sweep.get("paired") or []
    if isinstance(paired, list):
        for i, entry in enumerate(paired):
            if not isinstance(entry, dict):
                continue  # `_check_shape` already refused it, fatally
            for path, value in entry.items():
                if not isinstance(path, str):
                    continue  # likewise
                where = f"sweep.paired[{i}].{path}"
                # Gated on the path first: `_value_checks` indexes `spec[path]`
                # unguarded, so an unknown path would raise `KeyError`.
                if _path_resolves(path, where):
                    _value_checks(path, value, where, nameable=True)

    # `sweep.sample`, from three angles, in the order a reader would ask them.
    # First whether the declaration can be drawn from at all: `sample_fault` is
    # `sweep.py`'s own gate, shared rather than reimplemented so the check that
    # reports and the code that draws can never disagree about what is legal.
    # Then, only once it can, the two checks that need the template: each swept
    # path is a parameter it declares (`E-SWEEP-PATH-UNKNOWN`, the same check
    # `grid` gets), and each bound satisfies that parameter's own constraints —
    # which is § Validation's "Sample ranges" row exactly, whose example
    # ("upper bound 1.4 violates the parameter's `lt=1`") is `Param.check` on
    # the bound, and so reports `E-PARAM-VALUE` like every other illegal value
    # rather than a code of its own. A bound is checked `nameable=False`: it is
    # never rendered into a label — the *drawn* value is — and a drawn float
    # always renders inside `SWEPT_VALUE_PATTERN`.
    sample = sweep.get("sample")
    if sample:
        fault = sample_fault(sample)
        if fault is not None:
            c.error("E-SWEEP-SAMPLE-INVALID", "sweep.sample", fault)
        else:
            # Not `spec` — that name is this function's `template.parameter_spec`,
            # which `_path_resolves` and `_value_checks` both close over.
            for path, declared_range in sample["ranges"].items():
                if not _path_resolves(path, f"sweep.sample.ranges.{path}"):
                    continue
                form, bounds = next(iter(declared_range.items()))
                for i, bound in enumerate(bounds):
                    _value_checks(
                        path, bound, f"sweep.sample.ranges.{path}.{form}[{i}]", nameable=False
                    )

    # `grid` and `paired` writing the same path is not a shape fault — both are
    # well-formed on their own — but `expand`'s product applies each axis's cell
    # to `values` in declared order, so whichever mode is later in `_axes`
    # silently overwrites the other's value for that path on every combination.
    # Some combinations then collapse to byte-identical `values`: two different
    # `grid` settings paired with the same `paired` entry both resolve to that
    # entry's value, producing duplicate conditions `_condition_labels` cannot
    # see (it collects into a `set`). Filed as a spec gap in
    # `docs/superpowers/spec-defects.md` — § Expansion modes never states that a
    # path belongs to at most one axis-shaped mode — and refused here rather
    # than left to execute a design other than the one declared.
    #
    # Walked over every axis-shaped mode rather than the `grid`/`paired` pair it
    # started as: `sample` joins the same product, so a path it shares with
    # either would reopen exactly this hole through a third route — and a draw
    # overwritten by a `grid` cell is worse than the enumerated case, since the
    # drawn value is recorded in `sweep.yaml` as the condition's while the run
    # used another. The report names the *later* mode, which is the one whose
    # value wins, in `_axes` order (grid, then paired, then sample).
    # `groups` is deliberately not one of the modes walked into `named_by`: a
    # group axis writes no parameter at all, so two of them naming one path is a
    # different fault (§ Validation, "Axis names are distinct") and a group axis
    # sharing a path with a parameter axis is the *worse* one checked separately
    # below, under the same code.
    named_by: dict[str, list[tuple[str, str]]] = {}

    def _names(mode: str, path: Any, where: str) -> None:
        if isinstance(path, str):
            named_by.setdefault(path, []).append((mode, where))

    for path in grid:
        _names("grid", path, f"sweep.grid.{path}")
    for i, entry in enumerate(sweep.get("paired") or []):
        if isinstance(entry, dict):
            for path in entry:
                _names("paired", path, f"sweep.paired[{i}]")
    if isinstance(sample, dict) and isinstance(sample.get("ranges"), dict):
        for path in sample["ranges"]:
            _names("sample", path, f"sweep.sample.ranges.{path}")

    for path in sorted(named_by):
        occurrences = named_by[path]
        modes = {mode for mode, _ in occurrences}
        if len(modes) < 2:
            continue  # one mode naming a path repeatedly is that mode's own business
        last_mode = occurrences[-1][0]
        earlier = ", ".join(f"`{where}`" for mode, where in occurrences if mode != last_mode)
        c.error(
            "E-SWEEP-PATH-DUPLICATE",
            f"sweep.{last_mode}.{path}",
            f"is also written by {earlier} — two axis-shaped modes "
            "writing the same path make `expand`'s product overwrite one mode's value "
            "with the other's on every combination, collapsing some conditions to "
            "duplicates the run would silently execute twice",
        )

    # Two group axes naming the same `by` — § Validation's *Axis names are
    # distinct* — under the same code, for the reason the comment beside
    # `named_by` above gives: a group axis writes no parameter, so this is a
    # different fault from the collision below, not a milder version of it.
    # Read `sweep.get("groups")` entry by entry rather than through
    # `selector_paths`: that function is "total over a malformed `sweep.groups`
    # and dedupes" (`_check_assign`'s own docstring), and the dedup is exactly
    # what would hide two axes sharing one name — `sweep._axes`, unlike this
    # check, builds one axis per entry regardless, so `groups: [{by: arm, ...},
    # {by: arm, ...}]` crosses two same-named axes into the product and two
    # conditions render the identical label (`arm=c` for both a
    # first-axis-`c` and a second-axis-`c` cell) — a design that declares four
    # distinct cells collapsing into two labels, silently, the same "unpaired
    # conditions the design didn't ask for" harm a duplicate `grid` path already
    # gets a code for.
    by_names: dict[str, list[int]] = {}
    for i, entry in enumerate(sweep.get("groups") or []):
        if isinstance(entry, dict):
            by = entry.get("by")
            if isinstance(by, str) and by:
                by_names.setdefault(by, []).append(i)
    for by, indices in by_names.items():
        if len(indices) > 1:
            where = ", ".join(f"sweep.groups[{i}]" for i in indices)
            c.error(
                "E-SWEEP-PATH-DUPLICATE",
                f"sweep.groups.{by}",
                f"names {by!r} {len(indices)} times ({where}) — a condition can't hold "
                "two values of one axis, and crossing two same-named axes into the "
                "product renders two conditions under the identical label. Rename one "
                "of the two, or drop the duplicate",
            )

    # A group axis's `by` sharing a path with a parameter axis, under the same
    # code and for a sharper harm than the overwrite above. `expand` marks the
    # path a *selector* on every row it reaches, so `runner.resolve_condition_cfg`
    # plants nothing at it and `cli`'s wide config subtracts it: the parameter
    # axis claims to sweep `parameters.arm` while every condition runs the base
    # value at every scope, which is § Mistakes core prevents' "a typo'd
    # parameter silently using a default" by a route nothing else covers. Read
    # through `selector_paths`, the same function `expand` marks with, so the
    # check cannot disagree with the marking it is about.
    # A `by` naming a path this template declares as a parameter, whether or not
    # anything sweeps it, is the other half of the same fault — `spec` (already
    # bound above, `template.parameter_spec`) is the reference set `_path_resolves`
    # checks a `grid`/`baseline`/`ablate` path against, so a `by` that resolves
    # there is indistinguishable from a real parameter path at every one of the
    # seven reader sites `Condition.selectors` exists to keep apart. Unswept, no
    # OTHER axis silently loses its value the way the swept case below does — the
    # harm here is a condition's own label and directory claiming a value
    # (`method=spearman`) that `resolve_condition_cfg` never plants, because
    # `expand` marked the path a selector and skipped it: `cfg.parameters.<path>`
    # stays at the base config's value on every condition while the label claims
    # otherwise, indistinguishable from a real grid axis's label to a reader who
    # has not opened `sweep.yaml`'s `values`.
    #
    # **Checked AFTER the swept-collision case below, not before** — a path
    # that is both swept (`named_by`) and declared (`spec`) is the swept
    # case's to report: that message names the OTHER axis that silently loses
    # its value, which is the sharper of the two harms and the one a reader
    # needs first. Checking `spec` first would report the weaker, unswept
    # message for a config the swept branch was written for — reachable only
    # when the check order is wrong, which is exactly the bug a review caught
    # here: `spec`-first left the swept message reachable only when the swept
    # path was *undeclared* (`E-SWEEP-PATH-UNKNOWN` territory, a config
    # already broken by a misspelling), which is why the pre-existing test
    # for the swept case never noticed the branch order was backwards.
    group_axes = selector_paths(sweep)
    for path in group_axes:
        if path in named_by:
            where = ", ".join(f"`{w}`" for _, w in named_by[path])
            c.error(
                "E-SWEEP-PATH-DUPLICATE",
                f"sweep.groups.{path}",
                f"names a path {where} also writes — but a group axis varies *units* "
                "rather than a parameter, so every condition marks that path a selector "
                "and no scope plants the parameter: the parameter axis would claim to "
                f"sweep `parameters.{path}` while every condition ran its base value. "
                "Rename one of the two — a group axis's name is the label's key and "
                "need not be a parameter path at all",
            )
            continue
        if path not in spec:
            continue
        c.error(
            "E-SWEEP-PATH-DUPLICATE",
            f"sweep.groups.{path}",
            f"names {path!r}, which this template declares as a parameter — but a "
            "group axis varies *units* rather than a parameter, so every condition "
            "marks that path a selector and `resolve_condition_cfg` plants nothing "
            f"there: every condition's `parameters.{path}` stays at the base config's "
            "value while the condition's own label and directory claim the group "
            "level's value instead, indistinguishable from a real swept parameter to "
            "a reader who has not opened `sweep.yaml`'s `values`. Rename one of the "
            "two — a group axis's name is the label's key and need not be a "
            "parameter path at all",
        )

    # Every level of every group axis, through the label check alone. A group
    # cell renders into a condition label now that the axis expands
    # (`00_arm=control`), and a label is also a directory segment and a
    # selector — so a level carrying `/` or the axis separator is refused
    # exactly as a `grid` value is. Not `_value_checks`: a level names a set of
    # units rather than a parameter, so there is no `Param` to satisfy and
    # `spec[path]` would raise.
    for i, entry in enumerate(sweep.get("groups") or []):
        if not isinstance(entry, dict) or not isinstance(entry.get("levels"), list):
            continue
        for j, level in enumerate(entry["levels"]):
            unnameable = check_swept_value(level)
            if unnameable:
                c.error(
                    "E-SWEEP-VALUE-UNNAMEABLE",
                    f"sweep.groups[{i}].levels[{j}]",
                    unnameable,
                )
        # A level repeated inside ONE axis, which is § Mistakes core prevents'
        # *two identical measurements reported as two arms* by the one route
        # that row's three codes do not cover. They all guard the
        # `within`-versus-arms question — whether the design says every unit
        # appears everywhere. This says nothing about allocation: with
        # `levels: [control, treatment, control]` and a correct
        # `allocation: between`, `expand` renders three conditions, two of them
        # carrying the same label and the same `values`, and the run is green
        # whichever way the arm is decided — but *what* it does depends on the
        # method, and this comment names both rather than one. Under
        # `method: by_attribute`, `arms_of` hands both conditions the same units
        # because `{control} == {control}` — its set equality has nothing to
        # disagree with — so two condition directories come out byte-identical
        # at every artifact. Under a draw there is no column to agree with
        # itself: `assignment_for` keys `members` by level, so the second
        # `control` slice lands on the first key rather than beside it. Under
        # `random` it **overwrites**, and units vanish — a 12-unit roster and
        # `levels: [control, treatment, control]` leave 4 + 4 = 8 units
        # allocated unclustered, and 3 + 3 = 6 clustered, where the whole-cluster
        # buckets are zipped into the same duplicate key. Under `blocked` it
        # accumulates instead — `_blocked_draw` extends per-level lists — so all
        # 12 survive and `control` is drawn 8 to `treatment`'s 4, an arm twice
        # the ratio it declared. Both are measured against the run's own
        # `resolved`, and in every case the duplicate condition still reports,
        # identical to its twin. None of it is reachable through a config, since
        # this row refuses the declaration; what it is here to say is that the
        # fault is not "a harmless repeat" under any of the three methods.
        # Verified by calling `assignment_for` on that roster, not inferred.
        #
        # `E-SWEEP-PATH-DUPLICATE` is the sibling and does not reach this:
        # it compares axis *names* across entries, never values within one
        # entry's `levels`.
        #
        # The same hole exists on a parameter axis
        # (`grid: {analysis.method: [pearson, pearson]}`) and is left alone
        # deliberately — but **not because its consequence is milder**, which is
        # what an earlier version of this comment and its registry row both
        # claimed. Crossed with a group axis it reproduces this outcome exactly:
        # `groups: [{by: arm, levels: [control, treatment]}] × grid:
        # {analysis.method: [pearson, pearson]}` runs to exit 0 with
        # `00_arm=control__method=pearson` and `01_arm=control__method=pearson`
        # identical at every artifact, and those duplicated label bodies carry
        # the arm, so they are selectors — a contrast naming one resolves to the
        # later of the pair silently. The line drawn here is about what a
        # duplicate *means*, not what it costs: a group level is a claim about
        # which units, a parameter value is not. The parameter-axis duplicate is
        # a known gap, recorded on this code's row in § Errors `validate`
        # reports rather than closed.
        seen: dict[str, int] = {}
        for j, level in enumerate(entry["levels"]):
            if not isinstance(level, str):
                continue  # `_check_shape` owns the type; don't report it twice
            if level in seen:
                c.error(
                    "E-SWEEP-LEVEL-DUPLICATE",
                    f"sweep.groups[{i}].levels[{j}]",
                    f"repeats {level!r}, already declared at "
                    f"`sweep.groups[{i}].levels[{seen[level]}]` — a level names a "
                    "set of units, so the two conditions it expands into carry the "
                    "same label, hold the same units, and record the same values. "
                    "That is one measurement reported as two arms, and no later "
                    "check catches it: allocation is satisfied, and the arms are "
                    "equal rather than overlapping. Drop the repeat, or rename it "
                    "if two different sets of units were meant",
                )
            else:
                seen[level] = j

    # `sweep.baseline` gets the same per-entry checks — one value, not a list.
    # `reference.md`:218 names this by example ("Baseline is a valid condition |
    # `sweep.baseline` sets `analysis.method: pearsonn`"). Unchecked, a misspelled
    # path was planted verbatim into condition `00`'s config by
    # `resolve_condition_cfg`'s `setdefault` walk, so `00_baseline` ran the base
    # config under a label claiming otherwise and the run reported success.
    #
    # **A group level is the one baseline key that is not a parameter path**, and
    # it is skipped before `_path_resolves` rather than after: it is refused by
    # `E-SWEEP-BASELINE-GROUP`/`E-SWEEP-ABLATE-BASELINE-GROUP` below rather than
    # as an unknown parameter — § Expansion modes says "`sweep.baseline` may not
    # fix a level of a group axis" and names why — and `_value_checks` indexes
    # `spec[path]` unguarded, so suppressing only the error would move the
    # `KeyError` one line down inside a function contracted never to raise. The
    # gate is the declared axis names, never the presence of a `groups` block: a
    # baseline fixing a group path no axis declares is an unknown path, and stays
    # `E-SWEEP-PATH-UNKNOWN`.
    baseline = sweep.get("baseline") or {}
    for path, value in baseline.items():
        if path in group_axes:
            continue
        if _path_resolves(path, f"sweep.baseline.{path}"):
            _value_checks(path, value, f"sweep.baseline.{path}", nameable=False)

    # `sweep.ablate.override`, through the same two checks, because an override
    # entry is structurally a `grid` value: a value the user wrote at a dotted
    # path, planted into a condition's config and rendered into its label. Left
    # unchecked, `override: [{analysis.method: pearsonn}]` executes a condition
    # whose config holds a value § Validation's "Choices" row promises to refuse,
    # and `nameable=True` because an override value — unlike a `baseline` one —
    # *is* what `label_for` renders, so a value carrying the axis separator would
    # produce a label that cannot be parsed back into axes.
    #
    # Gated on `_path_resolves` first, exactly as the `grid` and `sample` loops
    # are: `_value_checks` indexes `spec[path]` unguarded, so an unknown path
    # would raise `KeyError` inside a function contracted never to raise.
    #
    # A `remove` path takes the SAME path check, on the same identifier, for the
    # same reason `baseline` does: `expand` plants `false`/`null` at it through
    # `resolve_condition_cfg`'s `setdefault` walk, so a misspelling
    # (`remove: [analysis.methdo]`) creates a parameter this template never
    # declared and runs a condition whose label claims a change nothing made.
    # What `remove` then *produces* at a path that does resolve is
    # `E-SWEEP-ABLATE-TARGET`'s question, below.
    ablate = sweep.get("ablate")

    # § Expansion modes: `ablate` "reads the baseline rather than re-emitting
    # it", so without one there is nothing for a change to be one change away
    # *from* — "It therefore requires `sweep.baseline`, which `validate`
    # checks". `expand` is permissive here by design (it emits n conditions
    # each carrying only its own change), which is why the refusal lives here
    # rather than there. Truthiness, not presence: `init` writes `ablate: null`,
    # and a null `ablate` expands to nothing and is not a declared ablation.
    if ablate and not baseline:
        c.error(
            "E-SWEEP-ABLATE-BASELINE-MISSING",
            "sweep.ablate",
            "is declared but `sweep.baseline` is not — an ablation is one change away "
            "from the baseline, so there is nothing to ablate from; without one, each "
            "ablated condition carries only its own change and the run has no reference "
            "condition to compare against. Declare `sweep.baseline`",
        )

    # § Expansion modes: "the product of 'vary one thing at a time' with a
    # second parameter axis is no longer one thing at a time, and there is no
    # defensible reading of what it would mean". The modes come from
    # `sweep.PARAMETER_AXIS_MODES` rather than a tuple written here — the rule
    # names no mode ("a second parameter axis"), and neither should its
    # enforcement. A mode added to `_axes` alone would still slip past this,
    # which is why `PARAMETER_AXIS_MODES` is not the pin: `known` above reads
    # `SWEEP_MODES`, derived from `PRODUCT_MODES + NON_PRODUCT_MODES`, so a
    # seventh mode is refused outright (`E-SWEEP-KEY-UNKNOWN`) until someone
    # classifies it — and classifying it as a parameter axis is what puts it
    # here. That second classification is a separate act since the split, and
    # `tests/test_sweep.py` pins the residual so it cannot be skipped.
    # `groups` is a product mode and deliberately not a parameter axis, which is
    # the row's stated exception: it varies units rather than parameters, so
    # every condition is still exactly one parameter change from its own arm's
    # baseline — legal beside `ablate`, and no longer refused for its own reason
    # the way it was before this row's own family of checks landed for real.
    # § Expansion modes: "`sweep.baseline` may not fix a level of a group axis —
    # the arms are peers". **One rule, two codes**, because the same declaration
    # breaks two different ways and a message naming the wrong one is a message
    # a reader cannot act on. `expand`'s `crossed` branch is the discriminator:
    # under `ablate` over group axes alone it suppresses the bare product rows,
    # so the fixed level is *not* duplicated and what goes wrong is that every
    # other level executes nowhere; without `ablate` the product rows are emitted
    # and the fixed level is rendered twice. The guards below are mutually
    # exclusive so that no config collects both, and each states what its own
    # shape actually does.
    #
    # `ablate`'s branch, § Expansion modes twice over: "an ablation is one change
    # from *its own cell's* full model, and there is no single reference
    # condition when the reference cohort differs". The consequence is worse than
    # a mis-numbering, which is why it is an error rather than a warning: a fixed
    # group axis is a *fixed* axis to `_baseline_cells`, so it expands over
    # nothing, the crossed ablation has one empty cell to repeat over, and every
    # level but the fixed one is executed nowhere while the run reports success —
    # a record describing an experiment nobody performed.
    #
    # **That "executed nowhere" reading holds for the composition § Expansion
    # modes permits — `ablate` over group axes and nothing else — and is scoped
    # to it deliberately.** `expand`'s `crossed` requires *every* axis to be a
    # group axis, so `ablate` beside a parameter axis takes the other branch of
    # `expand` and duplicates the level as well. That shape is refused for its
    # own reason by `E-SWEEP-ABLATE-CROSSED` beside this code — the document
    # gives it no reading at all — and the message says "would be executed by no
    # condition at all" of the composition it names rather than of every config
    # that reaches this line. `test_a_baseline_may_not_fix_a_group_level` pins
    # the three-code finding set for the crossed shape so the co-report is not
    # something a later reader has to re-derive.
    fixed_levels = [path for path in (sweep.get("baseline") or {}) if path in group_axes]
    if ablate and fixed_levels:
        c.error(
            "E-SWEEP-ABLATE-BASELINE-GROUP",
            f"sweep.baseline.{fixed_levels[0]}",
            f"fixes the `sweep.groups` axis `{fixed_levels[0]}` while `sweep.ablate` is "
            "declared — an ablation is one change from its own cell's full model, and "
            "there is no single reference condition when the reference cohort differs. "
            "Crossed with the group axes alone, a fixed group axis also expands over "
            "nothing, so every other level of it would be executed by no condition at "
            "all. Drop the level from the baseline: `ablate × groups` gives one baseline "
            "and its ablations per level",
        )
    elif fixed_levels:
        # The plain product case, which nothing refused until this check: the
        # baseline row and the axis's own product row are the same cell. Over the
        # roster the level names they resolve to the same parameters, the same
        # units, and two condition directories identical at every artifact —
        # `experimental-designs.md` § Mistakes core prevents' *two identical
        # measurements reported as two arms*, verbatim. Where the axis declares
        # two or more levels, the other levels' product rows cross the single
        # baseline — a comparison that now computes rather than being refused —
        # but at one level there is no cross-arm comparison at all, which is
        # where the run was green.
        #
        # The guard is keyed on the PATH, never on the value, so both shapes reach
        # here and the message states both: a value naming a declared level is
        # rendered twice, and one naming no declared level expands over no units.
        # Saying only the first would be false of a config this same rule refuses —
        # the defect class this branch hit seven times.
        c.error(
            "E-SWEEP-BASELINE-GROUP",
            f"sweep.baseline.{fixed_levels[0]}",
            f"fixes the `sweep.groups` axis `{fixed_levels[0]}` — the arms of a group "
            "axis are peers, and a baseline designating one of them is not a reference "
            "the expansion can give. Where the value names a level the axis declares, "
            "that level is rendered twice — once as the baseline row and once as the "
            "product row its own axis emits — so two conditions hold the same units and "
            "the same parameters and their directories are identical at every artifact; "
            "where it names no declared level, the baseline row expands over no units at "
            "all. Drop the level from the baseline, which then expands over the axis and "
            "gives every arm its own reference. Where the axis declares two or more "
            "levels, the comparison a designated arm was reaching for is a "
            "`statistics.contrasts` entry naming both conditions, which core computes — "
            "the baseline is refused because the arms of a group axis are peers, not "
            "because the comparison itself is unavailable",
        )

    crossed_modes = parameter_axis_modes_present(sweep) if ablate else []
    if crossed_modes:
        c.error(
            "E-SWEEP-ABLATE-CROSSED",
            "sweep.ablate",
            f"cannot be combined with {', '.join(f'`sweep.{m}`' for m in crossed_modes)} — "
            "`ablate` varies one thing at a time and a parameter axis varies a second, "
            "so their product is no design with a defensible reading. Split the axis "
            "into its own run, or express the ablation as `paired` rows. Only "
            "`sweep.groups` composes with `ablate`, because it varies units rather than "
            "parameters",
        )

    if isinstance(ablate, dict):
        for i, path in enumerate(ablate.get("remove") or []):
            if not isinstance(path, str) or not _path_resolves(path, f"sweep.ablate.remove[{i}]"):
                continue
            # § Validation, "Ablation targets": "`sweep.ablate.remove[0]` is
            # `analysis.min_samples` (int); `remove` needs a boolean or nullable
            # parameter — use `override`". Two branches, one identifier, because
            # they are one question asked of the two things that answer it —
            # the parameter, and the baseline `sweep.removal_value` reads.
            #
            # Branch 1 is the row's own words and is a fact about the parameter
            # alone, so it is ungated by the baseline: a `remove` on an `int`
            # with no `null` in its domain has nothing `remove` could set it to,
            # whatever the baseline says.
            #
            # Branch 2 exists because task 4 coupled the two readings (see
            # `docs/superpowers/spec-defects.md`, "Row 216 has two readings"):
            # `removal_value` picks `false` versus `null` from the *baseline's*
            # value, having no `parameter_spec` to ask, so a boolean the
            # baseline does not fix takes the nullable reading and plants `null`
            # at a non-nullable parameter — branch 1 passes it (it is a boolean)
            # and the run executes a value the "Types" row promises to refuse.
            # Checking what `removal_value` produces rather than what the config
            # declares is what closes that: the declaration is legal and the
            # product is not. It is `elif`, and gated on a declared baseline,
            # because `E-SWEEP-ABLATE-BASELINE-MISSING` owns the no-baseline
            # config whole — reporting every `remove` entry again there would
            # restate one fault n times.
            #
            # `remove` only, never `override`: an override states its own value,
            # so the baseline does not decide what it produces, and refusing an
            # override on a path the baseline leaves free would reject a legal
            # config (the same line `sweep.ablated_paths` draws when it keeps
            # ablated paths out of the axis-shaped modes' set).
            param = spec[path]
            where = f"sweep.ablate.remove[{i}]"
            if not (param.type_ is bool or param.nullable):
                c.error(
                    "E-SWEEP-ABLATE-TARGET",
                    where,
                    f"is `{path}`, which is neither a boolean nor nullable — `remove` "
                    "sets a boolean parameter to `false` and a nullable one to `null`, "
                    "and this parameter can hold neither; use `override` to state the "
                    "value the ablated condition should run instead",
                )
                continue
            problem = param.check(removal_value(baseline, path))
            if baseline and problem:
                c.error(
                    "E-SWEEP-ABLATE-TARGET",
                    where,
                    f"is `{path}`, which `sweep.baseline` fixes no *boolean* value for — "
                    "so `remove` reads the baseline, finds nothing it can turn off, and "
                    f"sets `null` rather than `false`, which {problem.lstrip()}. "
                    "Fix the parameter to `true` or `false` in `sweep.baseline`: an "
                    "ablation is one change away from the baseline, so the baseline has "
                    "to state what is being removed",
                )
        for i, entry in enumerate(ablate.get("override") or []):
            if not isinstance(entry, dict):
                continue  # `_check_shape` already refused it, fatally
            for path, value in entry.items():
                where = f"sweep.ablate.override[{i}].{path}"
                if _path_resolves(path, where):
                    _value_checks(path, value, where, nameable=True)

    # Guarded the same way `_condition_labels` guards its own `expand(doc)`:
    # `validate` collects findings and never raises. A `sweep.grid` axis value
    # of `null` reaches here — past the per-axis `E-SWEEP-AXIS-EMPTY` check
    # above, which fires only on a value that is *present and falsy* and then
    # `continue`s past the rest of the per-axis body, and past `_check_shape`'s
    # per-axis `list` guard, which refuses only a *present, non-list* value —
    # and makes `itertools.product` raise `TypeError` inside `expand`.
    # `E-SWEEP-EXPANDS-EMPTY` below is deliberately skipped rather than fired
    # on the caught exception: that check means "this sweep is shaped well
    # enough to expand, and expanding it yields nothing," a different and more
    # specific claim than "this sweep could not be expanded at all," and
    # firing it here would misreport a crash as an empty grid.
    # `conditions = []` regardless, so every later use in this function (the
    # execution-budget arithmetic below) sees zero rather than reading a name
    # that was never assigned.
    try:
        conditions = expand(doc)
    except Exception:
        conditions = []
    else:
        if sweep and not conditions:
            c.error(
                "E-SWEEP-EXPANDS-EMPTY",
                "sweep",
                "expands to zero conditions, so the run would execute nothing while "
                "reporting success — declare `baseline`, a non-empty `grid`, or remove "
                "`sweep` entirely",
            )
        _check_sampled_values(sample, spec, conditions, c)

    # `reference.md` § Validation, "Baseline leaves contrasts confounded": a
    # `sweep.baseline` that "fixes a value on every axis" leaves comparisons that
    # "differ on both and are reported `confounded: true`". `cli.py` computes
    # that fact per comparison at run time, after the compute is spent; the
    # declaration alone decides it, so it is warnable here.
    #
    # **The condition is the row's, and it is deliberately narrower than run
    # time.** Axes are compared over `sweep.grid`'s keys only — `swept_axes =
    # list(grid)`, no other mode — and only when the baseline fixes every one of
    # them, which is the row's own "fixes a value on every axis". A baseline that
    # leaves a *grid* axis free is a different shape: `sweep._baseline_cells`
    # gives it one baseline per cell of the unfixed axes rather than one
    # reference for the whole run, so the row's condition does not hold and the
    # `all(...)` guard below skips it. That is a config core accepts, and this
    # warning saying nothing about it is silence rather than a verdict —
    # deliberately so, and NOT a claim that nothing is confounded there. A
    # baseline fixing *two* of three swept axes leaves the third free, so this
    # guard is False, while every cell that moves both fixed axes still differs
    # from its own cell's baseline on both and is marked `confounded` at run
    # time — measured, and pinned by
    # `test_a_partly_fixed_baseline_is_silent_while_its_run_marks_confounded`.
    #
    # **The per-cell mechanism above explains the `grid` case and only that
    # one.** Two shapes are silent for a narrower reason, and stating the
    # per-cell expansion as though it covered them would be false. First, a
    # baseline that fixes *some* of the paths a multi-path `paired` axis varies
    # — `paired` and not `sample`, which cannot be declared beside a baseline at
    # all (`E-SWEEP-SAMPLE-BASELINE`): `_baseline_cells` reads fixedness off the cells'
    # paths and counts an axis fixed when the baseline names *any* of them, so
    # nothing expands per cell — there is one baseline, every comparison against
    # it differs on the paths the baseline left alone, and the run marks a
    # comparison `confounded: true` while this stays quiet whenever that level
    # *also* differs on a fixed path. Not every one of them does: `confounded` is
    # more than one differing path rather than any, so a level whose value on the
    # fixed path equals the baseline's differs on one path only and is reported
    # clean. The same half-fixed axis can yield both verdicts at once, and saying
    # otherwise here would be the claim-wider-than-the-code this comment replaced.
    # Second, a `paired` axis is outside `swept_axes` whether the baseline
    # touches it or not. Neither is a behaviour claim being made here: widening
    # the guard is a behaviour change, and this comment's job is to say what the
    # guard does rather than what a reader might assume from the row above it.
    #
    # **The remedy is in the message, and it is per-cell targeting that earned
    # it.** A run now takes each comparison against its own cell's baseline
    # (`contrasts.baseline_for`), so "leave the axis you are stratifying over
    # free" names an outcome this build delivers: the free axis stops appearing
    # in `differs_on` at all. Task 7 could not say that — targeting was
    # single-baseline then, and freeing an axis left the same comparison
    # `confounded` — so the message stated the fact and stopped, and the remedy
    # waited for the build to make it true rather than being hedged with build
    # state. It is true now — for a `grid` axis, which is the only kind this
    # message is ever emitted beside, since the guard reads no other mode.
    #
    # `contrasts.differing_axes` instead walks the *union* of both sides' keys
    # against a sentinel, so a baseline fixing an
    # axis the grid never sweeps adds a differing axis to every comparison and
    # can mark `confounded` where this warning stays silent. That direction is
    # the safe one — this never fires where a run would not mark the comparison
    # — and it is why the three lines below are not `contrasts.differing_axes`
    # reused: sharing the helper would import the wider semantics along with it.
    #
    # One finding, not one per condition: the fault is a single declaration, and
    # `sweep.baseline` is the line the reader edits.
    baseline_fixed = sweep.get("baseline") or {}
    swept_axes = list(grid)
    if swept_axes and baseline_fixed and all(axis in baseline_fixed for axis in swept_axes):
        crossed: list[tuple[Any, list[str]]] = []
        for cond in conditions:
            if cond.is_baseline:
                continue
            differing = [a for a in swept_axes if cond.values.get(a) != baseline_fixed.get(a)]
            if len(differing) > 1:
                crossed.append((cond, differing))
        if crossed:
            example, axes = crossed[0]
            c.warn(
                "W-SWEEP-BASELINE-CONFOUNDED",
                "sweep.baseline",
                f"fixes a value on every swept axis, so {len(crossed)} of "
                f"{len(conditions) - 1} baseline comparisons differ on more than one axis "
                f"and are reported `confounded: true` — `{example.label}` differs on "
                f"{', '.join(f'`{a}`' for a in axes)}, so its delta mixes those effects "
                "and no amount of correct pairing separates them; fix the axis you are "
                "measuring and leave the ones you are stratifying over free, and each "
                "cell gets its own baseline",
            )

    repeat_total = _repeat_total(doc, fold_basis)
    budget = (doc.get("limits") or {}).get("max_executions")
    # `repeat_total` is `None` only when a declared count cannot be resolved at
    # all — a `k: all` whose roster did not resolve, or a string `k` that is not
    # `all` — see `_repeat_total`. Skipping the check rather than computing
    # against a guessed 1× is deliberate: an unknown total must not be reported
    # as a small one. A `k: all` over a roster that DID resolve is a real number
    # here, and warns like any other count.
    # `check_envelope` is what REPORTS a wrong-typed `budget` (E-CONFIG-TYPE) —
    # this guard exists because this function may be reached without it having
    # run: a leaf fault is deliberately non-fatal, so `_check_sweep` still runs
    # on a still-malformed `doc`, and `executions > budget` below would raise
    # `TypeError` comparing an `int` to a `str`. `bool` is excluded explicitly,
    # matching `envelope._is_type`'s own bool-excluding rule for the same leaf
    # (`LEAF_TYPES` types `max_executions` as `int`, not `int | bool`): without
    # the exclusion, `isinstance(True, int)` is `True`, so a `max_executions:
    # true` would both get `E-CONFIG-TYPE` from the envelope AND run this check
    # against a `bool` budget, warning "exceeds True" — a message a wrong-typed
    # value should never be able to produce.
    if repeat_total is not None and isinstance(budget, int) and not isinstance(budget, bool):
        executions = len(conditions) * repeat_total
        if executions > budget:
            c.warn(
                "W-EXEC-BUDGET",
                "limits.max_executions",
                f"{len(conditions)} conditions × {repeat_total} repeats = {executions} "
                f"executions exceeds {budget}",
            )

    # The family is what `resolve_contrasts` will actually build — every
    # baseline comparison plus every declared contrast — not `len(conditions)`.
    # A grid-only sweep declares no baseline, so it publishes no comparison at
    # all, and telling its author they have a family of two was a false
    # positive rather than a backstop (`spec-defects.md`).
    correction = (doc.get("statistics") or {}).get("correction")
    known_corrections = {"none", "bonferroni", "holm", "fdr_bh"}
    # An out-of-enum *string* is the more likely mistake in practice — a typo
    # like `bonferonni` — and left unchecked it collects zero findings while
    # `corrected_for` downstream returns `ci95_corrected: null` with `thin:
    # false` and `correction: "bonferonni"` recorded on every member: a
    # correction named as applied while none was, and `thin: false`
    # suppresses the one signal that would otherwise flag it (`reference.md` §
    # Statistical reporting). Checking `isinstance` before the set membership
    # test is deliberate, not stylistic — `in` on a `set` raises `TypeError`
    # for an unhashable value (a `list` or `dict`), and `and` short-circuits
    # before that ever runs.
    if correction is not None and not (
        isinstance(correction, str) and correction in known_corrections
    ):
        shown = f"`{correction}`" if isinstance(correction, str) else type(correction).__name__
        c.error(
            "E-STATS-CORRECTION-UNKNOWN",
            "statistics.correction",
            f"is {shown}, not one of `none`, `bonferroni`, `holm` or `fdr_bh`",
        )
        correction = None
    # `resolve_contrasts` trusts its caller to have refused an unusable
    # `statistics.contrasts` block first (`contrasts.py`'s own comment leans on
    # this), and `_check_contrasts` is the check that does that — but it runs
    # *after* this one, so a malformed block (a scalar, a non-mapping entry, an
    # unresolvable or nested label) reaches this call first. `validate.py`
    # collects findings and never raises, so a block that cannot be resolved
    # yet counts as no resolvable family here; `_check_contrasts` reports the
    # shape or label fault under its own, more specific code.
    try:
        resolved_contrasts = resolve_contrasts(doc, conditions)
    except (TypeError, KeyError, AttributeError, ValueError):
        resolved_contrasts = []
    comparisons = len(resolved_contrasts)
    # `_units_declaration` takes the collector and reports a malformed
    # `data.units` under its own code; reading it once here and reusing the
    # result avoids reporting that fault again for the cluster guard below.
    units_here = _units_declaration(doc.get("data") or {}, c) or {}

    cluster_by = units_here.get("cluster_by")

    # A design declaring BOTH a weight and a cluster beside a comparison. H4b-2
    # builds the two unweighted paired clustered constructions `reference.md`
    # § Statistical reporting's suffix rule names, and deliberately not their
    # weighted counterparts: a weighted clustered contrast takes its df from the
    # CLUSTER COUNT and not from Kish's effective size — § Weighted samples,
    # "`cluster_by` still decides the draw when both are declared" — and the two
    # coincide in any fixture not built to separate them, so the wrong choice
    # would be invisible, so the combination is refused below rather than
    # approximated.
    #
    # Reads the resolved family rather than the declaration: a `sweep.baseline`
    # with no axis beside it publishes no delta, and this guard should not
    # refuse a design that never reaches a comparison. It refuses a COMBINATION
    # rather than a declaration, so it
    # carries a § Validation row and is not one of the `NOT BUILT` declarations
    # § The one config file counts: both `weight_by` and `cluster_by` are built,
    # and a run declaring both publishes `weighted_t_over_units_clustered` per
    # condition.
    weight_by = units_here.get("weight_by")
    if (
        comparisons > 0
        and isinstance(cluster_by, str)
        and cluster_by
        and isinstance(weight_by, str)
        and weight_by
    ):
        c.error(
            "E-DATA-WEIGHT-CLUSTER-CONTRAST",
            "data.units.weight_by",
            "and `data.units.cluster_by` are both declared beside a comparison, and no "
            "construction in this build computes a weighted clustered delta: the weighted "
            "paired forms take no membership and the clustered paired forms take no "
            "weights. Declare one of the two here — the cluster if what the units share "
            "is what threatens the interval, the weight if what they represent is — or "
            "keep both and express the difference as an `Estimate` returned by a `summary` "
            "step, which core records as reported rather than recomputing",
        )

    # A contrast whose two conditions were assigned to different arms of a
    # `sweep.groups` axis is unpaired — `reference.md` § Allocation's pairing
    # table: parameter axes only under `allocation: between` share the same
    # arm's units and are "paired within that arm", but two conditions that
    # differ on *any* `groups` axis hold disjoint sets of units "by
    # construction". `welch_t_over_units[_clustered]` and
    # `unpaired_percentile_over_units[_clustered]` compute that interval now
    # (H4c), so this loop no longer refuses the combination itself — it exists
    # for the one construction that still does not exist: a WEIGHTED unpaired
    # delta, refused below as `E-DATA-WEIGHT-ALLOCATION-CONTRAST`.
    #
    # **This guard reads each resolved comparison individually rather than
    # firing on `comparisons > 0`,** because a group axis does not affect
    # every contrast in the family alike: in a `groups × grid`
    # design, control-pearson vs. control-spearman shares the same arm's units
    # and is paired, while control-pearson vs. treatment-pearson is unpaired.
    # A guard firing on the resolved family's size alone would refuse (or
    # exempt) the first comparison along with the second and make "each arm
    # analyzed several ways" unexpressible. `contrasts.crossed_group_axes`
    # gives the group axes two conditions disagree on and is the same
    # predicate `cli`'s own pairing derivation reads, so the two cannot
    # disagree about which comparisons are unpaired. Imported at module
    # scope, the same as its sibling's helpers, rather than gated on
    # `allocation`: the axis being a declared `groups` axis is what makes the
    # two sides disjoint, whatever `allocation` itself is declared as (or left
    # undeclared, the `within` default) — a config missing that declaration
    # entirely still co-reports `E-DATA-ALLOCATION-WITHIN-ARMS`.
    conditions_by_index = {cond.index: cond for cond in conditions}
    for comp in resolved_contrasts:
        of_cond = conditions_by_index.get(comp.of)
        against_cond = conditions_by_index.get(comp.against)
        if of_cond is None or against_cond is None:
            continue
        group_axes = crossed_group_axes(of_cond, against_cond)
        if not group_axes:
            continue
        plural = "" if len(group_axes) == 1 else "s"
        # A weighted unpaired contrast has no construction and will not get one.
        # `weight_by` beside a cross-arm comparison needs Kish's effective size PER
        # SIDE — two df inputs where the paired form needed one — and the two
        # readings coincide in any fixture not built to separate them, so the wrong
        # choice would be invisible. Refused rather than approximated, on the
        # precedent `E-DATA-WEIGHT-CLUSTER-CONTRAST` set. Standing, not temporary:
        # it refuses a COMBINATION rather than a declaration, so it carries a
        # § Validation row and a § Errors row and is not one of the `NOT BUILT`
        # declarations § The one config file counts.
        #
        # Inside this loop rather than beside the `comparisons > 0` guards above,
        # because it is the same per-comparison reading its neighbour is: a
        # `groups × grid` design's within-arm comparisons are paired and weightable,
        # and a guard firing on the declaration would refuse a design core computes
        # correctly today.
        if isinstance(weight_by, str) and weight_by:
            c.error(
                "E-DATA-WEIGHT-ALLOCATION-CONTRAST",
                "data.units.weight_by",
                f"is declared beside a comparison whose two conditions "
                f"({of_cond.label!r} and {against_cond.label!r}) differ on group "
                f"axis{plural} {', '.join(group_axes)}, and no construction computes "
                "a weighted unpaired delta: a Welch *t* on two weighted means takes "
                "its df from Kish's effective size per side, two inputs where the "
                "paired form needed one, and the two readings coincide in any sample "
                "not built to separate them. Drop `weight_by` and the cross-arm delta "
                "is computed unweighted, keep it and compare within an arm, or express "
                "the weighted difference as an `Estimate` returned by a `summary` step, "
                "which core records as reported rather than recomputing",
            )

    if comparisons > 0 and (correction or "holm") == "none":
        c.warn(
            "W-STATS-FAMILY",
            "statistics.correction",
            f"{comparisons} comparisons per metric form a family, and "
            "`statistics.correction` is `none` — every interval reported is uncorrected, and "
            "each records `correction: null` to say so",
        )
    # Read once, not twice: this same declaration is read again below for
    # `W-STATS-NULLTEST-FAMILY`, and a second independent read is how two
    # checks over one declaration come to disagree about what it says.
    null_test = (doc.get("statistics") or {}).get("null_test")
    if comparisons > 0 and correction == "fdr_bh":
        # Task 10. The three disjuncts of § Validation's *Correction can be
        # applied*: no `null_test` is declared at all, its `shuffle` names no
        # axis any comparison in this family crosses, or every comparison here
        # is a parameter-axis one (paired, and so has no relabelling null to
        # carry a p-value from). `contrasts.crossed_group_axes` is the same
        # expression the pairing derivation above already reads, so this
        # cannot disagree with it about which comparisons are unpaired.
        declared_null_test = isinstance(null_test, dict) and bool(null_test)
        shuffle = null_test.get("shuffle") if isinstance(null_test, dict) else None
        crossed_by_any_comparison: set[str] = set()
        for comp in resolved_contrasts:
            of_cond = conditions_by_index.get(comp.of)
            against_cond = conditions_by_index.get(comp.against)
            if of_cond is None or against_cond is None:
                continue
            crossed_by_any_comparison.update(crossed_group_axes(of_cond, against_cond))
        if not declared_null_test:
            reason = "no `statistics.null_test` is declared, so no comparison carries a p-value"
        elif not crossed_by_any_comparison:
            reason = (
                "every comparison in this family differs only on a parameter axis, so its "
                "null is a per-unit sign flip rather than a relabelling and `shuffle` cannot "
                "express it"
            )
        elif shuffle not in crossed_by_any_comparison:
            reason = (
                f"`statistics.null_test.shuffle` names `{shuffle}`, which is not a group "
                "axis any comparison in this family crosses"
            )
        else:
            reason = None
        if reason is not None:
            c.warn(
                "W-STATS-CORRECTION-INAPPLICABLE",
                "statistics.correction",
                f"`fdr_bh` adjusts p-values, and {reason} — every `ci95_corrected` will "
                "be null. Use `holm` or `bonferroni`, whose corrections are interval-shaped",
            )
    if comparisons > 0 and isinstance(null_test, dict) and null_test:
        # `W-STATS-RESAMPLE-FAMILY`'s twin: Holm's tightest level is still α/m at
        # rank 1, and a permutation p-value is only as fine-grained as `1/(n+1)` —
        # `stats.min_honest_permutations` — so a family this size needs at least
        # `min_honest_permutations(ALPHA / comparisons)` draws or its own tightest
        # corrected p can never fall below the level demanded of it. `m` is
        # `comparisons × metrics` and the metric count is unknowable here by the
        # same design `_check_resample`'s comment gives, so this bounds against
        # `comparisons` alone — always true when it fires, silent when it might
        # not be.
        n = null_test.get("n")
        if n is None:
            effective_n = 5000
        elif isinstance(n, int) and not isinstance(n, bool):
            effective_n = n
        else:
            effective_n = None
        if effective_n is not None:
            needed = min_honest_permutations(ALPHA / comparisons)
            if effective_n < needed:
                plural = "" if comparisons == 1 else "s"
                n_desc = f"is {n}" if n is not None else "is unset, so defaults to 5000,"
                c.warn(
                    "W-STATS-NULLTEST-FAMILY",
                    "statistics.null_test.n",
                    f"{n_desc} and this design resolves to {comparisons} comparison{plural}, "
                    f"so the tightest corrected p this family can ever report needs at least "
                    f"{needed} permutations — a p-value cannot fall below `1/(n+1)`. This is a "
                    "lower bound: the family is comparisons × metrics and the metric count is "
                    "not knowable before the run, so the real requirement is at least this",
                )


def _check_contrasts(doc: dict[str, Any], c: Collector, roster: UnitList | None = None) -> None:
    """Each declared `statistics.contrasts` entry, checked for real now that the
    block is no longer refused wholesale (`_check_unimplemented` used to raise
    `E-STATS-CONTRASTS-UNSUPPORTED` for any non-empty declaration).

    `of` and `against` name conditions **by label** (`reference.md` § Contrasts),
    the same grammar `sweep.baseline`/`sweep.grid` resolve against, so a name that
    resolves to nothing would otherwise reach `contrasts.resolve_contrasts` and
    raise a bare `KeyError` at run time — the same silent-failure-deferred-to-a-
    crash class every other check in this module exists to move earlier.

    **Contrasts do not nest.** `reference.md` and `design-principles.md` both say
    a comparison between two contrasts — a dose-response ordering, a difference-
    in-differences, a nested mean over cells — is an *interaction*, not a
    contrast, and stays a `summary`-step `Estimate`. So a side naming another
    entry's `id` is refused under its own code, `E-STATS-CONTRAST-NESTED`, rather
    than the vaguer `E-STATS-CONTRAST-UNKNOWN` an unresolvable label gets — nesting
    is checked first for exactly that reason: an `id` that happens to also fail to
    resolve as a condition label must still be diagnosed as nesting, since that is
    the more specific and more actionable fault. A name that is simultaneously a
    real condition label and another entry's `id` resolves as the label instead —
    a legal contrast must not be refused as nesting just because some other entry
    happens to reuse its label as an `id`.

    **`within` names a unit attribute**, the same one `units_matching` (Task 2)
    reads with `.get`, which returns `None` for a typo exactly as it would for a
    stratum that is genuinely empty of units — the two are indistinguishable
    downstream. So this is checked here, at validate time, against the declared
    `data.units.attributes` list — analogous to the `report_by` unknown-attribute
    rule (`reference.md` § Reporting strata) — rather than left to look like a
    silently-empty stratum.

    **A `within` stratum too thin to disclose is warned about here too**
    (`reference.md` § Validation, "Contrast stratum is populated"), under the
    same `W-STATS-CONTRAST-THIN` the run emits — one code fired at two
    observation points, the way `report_by`'s roster-time and completed-time
    counts are two (`W-STATS-REPORTBY-THIN`/`W-STATS-STRATUM-THIN`). Which of
    those two shapes a future thinness check should take is not settled by
    anything in this function, so this comment does not argue it.

    The count here is over *resolved roster* units matching the stratum, which is
    all `validate` can see: pairing is a fact about which units both sides
    *completed*, and `cli.py`'s `allowed` set is `units_matching` over this same
    roster, so `n_paired` is bounded above by this number — the run-time check is
    what sees the attrition between them, which no declaration predicts.
    Only `roster` is optional in this function's signature: a caller with no
    resolved roster (`_check_contrasts` is called directly by tests) still gets
    every declaration-only check, and skips only the one that needs units.

    **The shape is checked here too, and it has to be.** `resolve_contrasts`
    reads `entry["of"]` and `entry.get("id")` off whatever the list holds, and
    its comment leans on this function having refused anything that would make
    those raise; before this block was un-refused, nothing could reach it at
    all. So a non-list `contrasts`, an entry that is not a mapping (a bare list
    of condition labels is the plausible slip), and a missing or non-string
    `id` are all `E-STATS-CONTRAST-SHAPE` rather than an `AttributeError` out
    of `run` or the literal string `'None'` published as a contrast's name,
    where two such entries would collide.

    **The two sides must be distinct** (`reference.md` § Validation, "Contrast
    has two distinct sides"), checked only once both resolve so the diagnostic
    for a typo stays the more specific `E-STATS-CONTRAST-UNKNOWN`. A condition
    compared with itself is a perfect null with a zero-width interval over
    every unit, published as a finding and occupying a slot in the correction
    family.
    """
    entries = ((doc.get("statistics") or {}).get("contrasts")) or []
    if not entries:
        return
    if not isinstance(entries, list):
        c.error(
            "E-STATS-CONTRAST-SHAPE",
            "statistics.contrasts",
            "is not a list of contrast entries; each entry is a mapping with `id`, `of` and "
            "`against`",
        )
        return

    # `isinstance(..., str)` before the value enters a `set`, for the reason the
    # `of`/`against` loop below states: building a `set` hashes every element, so
    # an `id` holding a mapping or a list (one bad indent under `id:`) raised
    # `TypeError` out of `validate_config` here, before a single finding was
    # collected. A non-string `id` is not a name a contrast can be published
    # under, so dropping it from `ids` routes it to the missing-or-not-a-string
    # branch below rather than minting an identifier.
    ids = {
        entry["id"]
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("id"), str) and entry["id"]
    }
    # Guarded the same way `_condition_labels` guards its own `expand(doc)`:
    # `validate` collects findings and never raises. `_check_sweep` calls this
    # same pure function on this same doc one statement earlier and is *also*
    # guarded now, so a sweep malformed enough to make `expand` raise (a
    # `null` grid axis value, past `_check_shape`'s per-axis `list` guard) no
    # longer crashes there first — meaning this guard is genuinely reachable
    # through `validate_config` too, not only from a caller that reaches
    # `_check_contrasts` directly. Kept regardless of that overlap, on the
    # same reasoning the `isinstance(entries, list)` guard just above was kept
    # once `_check_shape` started covering its shape first: two guards on the
    # same pure call is deliberate belt-and-braces, not redundancy to delete —
    # a caller that reaches `_check_contrasts` directly, skipping
    # `_check_sweep` entirely (`test_check_contrasts_guards_expand_when_called_directly`
    # does exactly this), still needs its own guard, and a future change that
    # reopens `_check_sweep`'s crash must not silently reopen this one too.
    # `conditions = []` rather than returning:
    # the shape and `id`-collision checks below don't need a resolved sweep at
    # all, and every `of`/`against` correctly reports `E-STATS-CONTRAST-UNKNOWN`
    # against an empty `labels` rather than the block going silently unchecked.
    try:
        conditions = expand(doc)
    except Exception:
        conditions = []
    labels = {cond.label for cond in conditions if cond.label is not None}
    # Same reasoning as `_check_report_by`'s `declared` set: a non-string item in
    # `data.units.attributes` is `_check_units`'s finding to make, not this
    # function's, but `set(...)` over the raw list would crash on it first.
    declared_attrs = {
        a
        for a in (((doc.get("data") or {}).get("units") or {}).get("attributes") or [])
        if isinstance(a, str)
    }
    seen_ids: set[str] = set()
    # The same guard `_check_report_by` puts on its own floor, for the same
    # reason: `check_envelope` is what REPORTS a wrong-typed `min_reported_n`
    # (`E-CONFIG-TYPE`), a leaf fault is deliberately non-fatal, so this function
    # still runs on a doc holding a `str` floor and `len(matched) < floor` would
    # raise `TypeError`. `bool` is excluded explicitly because `isinstance(True,
    # int)` is `True`, and a value the envelope already flagged must not also
    # drive a warning nobody can act on ("below limits.min_reported_n (True)").
    raw_floor = (doc.get("limits") or {}).get("min_reported_n")
    floor: float | None = (
        raw_floor
        if not isinstance(raw_floor, bool) and isinstance(raw_floor, (int, float))
        else None
    )

    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            c.error(
                "E-STATS-CONTRAST-SHAPE",
                f"statistics.contrasts[{i}]",
                f"is {type(entry).__name__}, not a mapping with `id`, `of` and `against` — a "
                "list of condition labels is not a list of contrasts",
            )
            continue
        # The second site that hashes `id`: `in seen_ids` raises for an
        # unhashable value exactly as the `ids` construction above did, so the
        # `isinstance` guard has to come first here too. A non-string `id` is
        # never a repeat of anything — it gets the shape error below instead.
        raw_id = entry.get("id")
        is_named = isinstance(raw_id, str) and raw_id
        if is_named and raw_id in seen_ids:
            c.error(
                "E-STATS-CONTRAST-SHAPE",
                f"statistics.contrasts[{i}].id",
                f"repeats `{raw_id}`, which an earlier entry already uses; two "
                "contrasts under one name are indistinguishable in `results.contrasts` and "
                "in a hypothesis naming it",
            )
        elif is_named:
            seen_ids.add(entry["id"])
        if not is_named:
            c.error(
                "E-STATS-CONTRAST-SHAPE",
                f"statistics.contrasts[{i}].id",
                "is missing or not a string; `id` is how the contrast is named in "
                "`results.contrasts` and in a hypothesis, so two entries cannot share one",
            )
        for field in ("of", "against"):
            value = entry.get(field)
            where = f"statistics.contrasts[{i}].{field}"
            # `isinstance` before either membership test, the same guard
            # `E-STATS-CORRECTION-UNKNOWN` uses above: `in` on `ids`/`labels` (both
            # `set`s) raises `TypeError` for an unhashable `value` (a `list` or a
            # `dict`), and `and`/`not (... and ...)` short-circuits before that ever
            # runs. A non-string `of`/`against` is simply not a condition's label,
            # so it falls into the same `E-STATS-CONTRAST-UNKNOWN` branch a
            # resolvable-but-wrong string would.
            if isinstance(value, str) and value in ids and value not in labels:
                c.error(
                    "E-STATS-CONTRAST-NESTED",
                    where,
                    f"names `{value}`, which is another contrast's `id` — contrasts compare "
                    "conditions and do not nest. A comparison between two contrasts (a "
                    "dose-response ordering, a difference-in-differences, a nested mean over "
                    "cells) is an interaction, and stays a `summary`-step `Estimate` rather "
                    "than a declared contrast",
                )
            elif not (isinstance(value, str) and value in labels):
                c.error(
                    "E-STATS-CONTRAST-UNKNOWN",
                    where,
                    f"names `{value!r}`, which no condition's label matches",
                )
        of_value = entry.get("of")
        if isinstance(of_value, str) and of_value in labels and of_value == entry.get("against"):
            c.error(
                "E-STATS-CONTRAST-SAME-SIDES",
                f"statistics.contrasts[{i}]",
                f"sets `of` and `against` to the same condition (`{entry.get('of')}`); a "
                "contrast has two distinct sides. Comparing a condition with itself publishes "
                "a perfect null over every unit as a finding, and it joins the correction "
                "family, tightening every other interval in the run",
            )
        within = entry.get("within")
        if isinstance(within, dict):
            unknown = False
            for name in within:
                if name not in declared_attrs:
                    unknown = True
                    c.error(
                        "E-STATS-CONTRAST-WITHIN",
                        f"statistics.contrasts[{i}].within",
                        f"names `{name}`, which is not in `data.units.attributes`",
                    )
            # Skipped for a stratum already refused above, the way
            # `_check_report_by` skips a level of an attribute it just refused:
            # an unknown attribute matches no unit, so counting it would report
            # a thin stratum as well as an undeclared one for a single typo.
            if not unknown and within and roster is not None and floor is not None:
                matched = units_matching(roster, within) or set()
                if len(matched) < floor:
                    stratum = ", ".join(f"`{k}={v}`" for k, v in sorted(within.items()))
                    c.warn(
                        "W-STATS-CONTRAST-THIN",
                        f"statistics.contrasts[{i}].within",
                        f"selects {stratum}, which {len(matched)} of {len(roster)} units "
                        f"match, below limits.min_reported_n ({floor}). The run counts "
                        f"this comparison's own denominator over the two sides' completed "
                        f"units, which attrition can only make smaller",
                    )


_DIRECTIONS = ("greater", "less")
_EVALUATE_ONS = ("observed", "ci95_lower", "ci95_upper")
_KINDS = ("confirmatory", "exploratory")


def _condition_labels(doc: dict[str, Any]) -> tuple[set[str], set[str]] | None:
    """Every declared condition label, and the baseline's own, or `None`.

    `None` means the sweep block is malformed badly enough that `expand` cannot
    read it — a scalar where an axis's value list belongs, a non-mapping
    `baseline`. `_check_sweep` is the check that reports those, and this module
    collects rather than raises, so an unexpandable sweep silently skips the
    label test instead of turning one bad indent into a traceback.
    """
    try:
        conditions = expand(doc)
    except Exception:
        return None
    labels = {cond.label for cond in conditions if cond.label is not None}
    baselines = {cond.label for cond in conditions if cond.label is not None and cond.is_baseline}
    return labels, baselines


def _check_hypotheses(
    doc: dict[str, Any], c: Collector, experiment: Any | None, template: Any
) -> None:
    """Each declared `hypotheses` entry, checked for real now that the block is
    non-empty and list-shaped (`_check_shape` already refused anything else).

    **`metric` names the quantity under test, and `compare` only ever says
    *where*.** `reference.md` § Pre-registration: "`metric` is required in every
    form, because `compare` says *where* and never *what*." A contrast or a
    condition comparison reports one value per step metric exactly as a summary
    step does, so a hypothesis that names only `compare` leaves the quantity
    unstated — `E-HYPOTHESIS-METRIC`. A `metric` naming a step this experiment's
    `steps` list does not declare is the same failure by a different route: the
    string looks like it names something, but nothing in the run will ever
    produce it, so it is refused under the same identifier rather than a third
    one — there being no experiment to check against (its import already failed,
    reported elsewhere as `E-ENTRYPOINT-IMPORT`) is not a hypothesis fault, so
    that case is silently skipped rather than double-reported.

    **`compare.to: baseline` needs a declared baseline — and so does a bare
    `compare.condition` with no `to` at all, because `hypotheses.resolve` reads
    `compare.condition` as a baseline comparison whether or not `to` spells it
    out.** `reference.md` § Validation, "Hypothesis needs baseline":
    `hypotheses[0].compare.to: baseline` but `sweep.baseline` is not declared.
    Nothing downstream guards this — `hypotheses.resolve` reads `vs_baseline`,
    which `cli` never populates without a declared baseline, so the hypothesis
    would silently resolve to no observation rather than being refused before a
    run starts. The same gap exists one form earlier: `compare: {condition: X}`
    with neither `to: baseline` nor a declared `sweep.baseline` used to fire
    neither this check (no `to` to read) nor `E-HYPOTHESIS-CONDITION` (the label
    can resolve just fine), so it validated clean while naming a condition and
    nothing to compare it against — `reference.md` § Pre-registration's ruling
    is to refuse that form rather than default the missing side to baseline, so
    `E-HYPOTHESIS-BASELINE`'s condition is widened to `to == "baseline"` *or*
    (`condition` present, `to` absent, and `contrast` absent too) — the last
    exclusion because `hypotheses.resolve` checks `"contrast" in compare` first
    and returns from that branch without ever reading `condition`, so a
    `{contrast: x, condition: y}` hypothesis resolves through the contrast and
    needs no baseline at all — rather than minting a second code for one fault
    that is the same fault under a different spelling.
    `E-HYPOTHESIS-BASELINE`.

    **`compare.to` has exactly one value, and it is `baseline`.**
    `reference.md` § Pre-registration writes `to: baseline` and core computes
    no other per-condition comparison — a claim against some *other* condition
    is a `statistics.contrasts` entry, named through `compare.contrast`. Left
    unchecked, `to: some_other_label` validates clean and
    `hypotheses.resolve` — which never reads the field — evaluates it against
    the baseline anyway, so the verdict answers a question the config did not
    ask and nothing in the record reveals the substitution.
    `E-HYPOTHESIS-COMPARE-TO`.

    **`compare.contrast` needs a real contrast.** `reference.md` § Validation,
    "Hypothesis names a real contrast": `hypotheses[1].compare.contrast` is
    `invariance`, which `statistics.contrasts` does not declare. The same
    unresolvable-label class `_check_contrasts` already refuses for `of` and
    `against` — a typo here would resolve to nothing in `hypotheses.resolve`
    and read back `block=None`, reported but never diagnosed as a typo.
    `E-HYPOTHESIS-CONTRAST`.

    **`evaluate_on` needs a bound that can exist.** `reference.md` §
    Validation, "Hypothesis bound exists": `evaluate_on` names a bound
    (`ci95_lower`/`ci95_upper`), but no metric this run computes could ever
    carry an interval — `data.units` undeclared *and* the template defines no
    `aggregate`, which together are the only way a `basis: units` metric with
    a `ci95` gets produced at all. `generic`, the only template this build
    registers, does not override `BaseTemplate.aggregate` — it inherits the
    `{}`-returning default — so the `aggregate`-half of this condition holds
    for every config naming it; `data.units` presence is what discriminates.

    **That two-condition test is `reference.md`'s own — "the config-level
    form" — and this check adds one more gate on top of it, not a divergence
    from it.** § What a hypothesis is tested against draws the line itself:
    "`validate` catches the config-level form of that, where nothing in the
    run could carry an interval; the per-metric form is settled when the step
    returns." The Validation row's own wording is "no metric this run
    *computes*" — and CLAUDE.md's own invariant is explicit that "the one
    interval core stores *without computing* is an `Estimate` returned by a
    `summary` step"; a `reported: true` `Estimate` a step supplies directly
    ("A hypothesis may name a summary metric") is therefore outside what that
    row is even about, not an exception carved into it. Core never inspects a
    step's body to know whether *this* summary step actually returns one, so
    the check below only fires when the metric's scope is affirmatively known
    and is not `"summary"` — unknown (no experiment, or a `metric` that
    doesn't parse) is treated the same as `"summary"`, conservatively, since
    the check can rule out neither. `E-HYPOTHESIS-BOUND`.

    **The same impossible-interval condition, without a bound requested, is a
    warning rather than a refusal — and shares the same scope gate, for the
    warning's own reason rather than the error's.** `reference.md` §
    Validation, "Hypothesis has an inference base": every metric will be
    `basis: repeats` — reportable (`evaluate_on: observed` still reads a
    value) but not testable against an interval. That premise is false for a
    `scope: "summary"` metric that turns out to be a reported `Estimate`: it
    is neither `basis: repeats` nor untestable — it is `reported`, carries its
    own interval, and is exactly what `evaluate_on: ci95_lower`/`ci95_upper`
    can test. (The error's hard-stop argument — `command_run` treats
    `E-HYPOTHESIS-BOUND` as `c.has_errors` and a warning never stops a run —
    does not transfer to the warning and is not why this one is gated; a
    warning it wrongly issued would cost nothing but a false alarm, so the
    gate here is justified only by the premise being false, the same way it
    is for the error.) `W-HYPOTHESIS-INFERENCE-BASE` fires exactly where
    `E-HYPOTHESIS-BOUND` does not, under that shared gate: same condition,
    `evaluate_on` absent or `observed` instead of a bound.

    **A hypothesis's form must match its metric's scope.** `reference.md` § What
    a hypothesis is tested against: a `scope: "summary"` metric "is one value
    per run, not a contrast between conditions" and takes no `compare`, while a
    `condition`- or `repeat`-scoped metric only exists per condition and "is the
    same mistake inverted" without one. Both directions are `E-HYPOTHESIS-FORM`.

    **`direction` and `evaluate_on` are closed vocabularies, refused here rather
    than reaching the evaluator at all.** The two fields are not symmetric in
    what happens if this check didn't exist. `hypotheses.py::verdict_for` already
    guards `direction`: `supported` is set only when `direction in ("greater",
    "less")`, so an out-of-vocabulary value (Task 4's review found `greatr`) gets
    `supported: None` rather than a wrong verdict — the refusal here is a second,
    earlier line of defence, so a mistyped `direction` never even reaches a real
    run, rather than being caught only after one. `evaluate_on` has no such
    guard: `_tested_number` reads `evaluate_on == "observed"` and, failing that,
    `evaluate_on == "ci95_lower"` — anything else, including a typo of either
    string, silently falls through to `ci95_upper` and both fields go on to
    build a genuinely different verdict, with nothing in the record to reveal
    that the value was never recognized. So `E-HYPOTHESIS-EVALUATE-ON` is closing
    a live, currently-unguarded misread; `E-HYPOTHESIS-DIRECTION` is moving an
    already-guarded one earlier. `direction` has no named enum anywhere in the
    four documents; `evaluate_on`'s is documented
    (`observed | ci95_lower | ci95_upper`) but no identifier existed for either.

    **`kind`, `direction` and `threshold` are required, not merely constrained.**
    `reference.md` § The one config file writes all three in every hypothesis and
    gives a default for none of them, and each has a different silent
    consequence when absent. `kind` is the worst: `hypotheses._is_counted` tests
    `== "confirmatory"`, so an omitted or mistyped `kind` leaves the correction
    family and the verdict is decided on the *raw* — tighter — bound, over-
    supporting a claim that the corrected level would have refused, with the
    record echoing the typo but no diagnostic anywhere. `direction` and
    `threshold` fail the other way, honestly but expensively: `verdict_for`
    returns `supported: None` and the run comes back with no verdict after the
    compute is spent. So `direction`'s check drops its `is not None` guard and
    `E-HYPOTHESIS-KIND` and `E-HYPOTHESIS-THRESHOLD` join it. `evaluate_on`
    stays optional, because `observed` is a documented default rather than an
    omission.

    **`compare.condition` is resolved against the declared labels**, the job
    `_check_contrasts` already does for `of`/`against` with the same `expand(doc)`
    machinery. A typo'd label validated clean and came back `observed: null,
    supported: null`; so did naming the baseline's own label, which
    `vs_baseline` has no entry for by construction. Both are
    `E-HYPOTHESIS-CONDITION`.
    """
    entries = doc.get("hypotheses")
    if not isinstance(entries, list) or not entries:
        return  # `_check_shape` already refused a bad shape; `[]` is not a declaration

    scopes_by_step: dict[str, str] = {}
    if experiment is not None:
        scopes_by_step = {_step_name(cls): cls.scope for cls in experiment.steps}

    has_baseline = bool((doc.get("sweep") or {}).get("baseline"))
    labels = _condition_labels(doc)
    contrast_entries = ((doc.get("statistics") or {}).get("contrasts")) or []
    contrast_ids = (
        {
            entry["id"]
            for entry in contrast_entries
            if isinstance(entry, dict) and isinstance(entry.get("id"), str) and entry["id"]
        }
        if isinstance(contrast_entries, list)
        else set()
    )
    # The bound-exists error and the inference-base warning share one condition:
    # no metric this run computes could ever carry an interval, because that
    # needs a `basis: units` metric and the only source of one is a resolved
    # unit table run through a template's `aggregate`. `generic` — the only
    # template this build registers — inherits `BaseTemplate.aggregate`'s
    # `{}`-returning default rather than overriding it, so `data.units` is what
    # discriminates in practice; the `type(...) is not BaseTemplate.aggregate`
    # check is what would let a future template with a real `aggregate` clear
    # this condition without either check changing.
    no_interval_possible = (
        not bool((doc.get("data") or {}).get("units"))
        and type(template).aggregate is BaseTemplate.aggregate
    )

    for i, hyp in enumerate(entries):
        if not isinstance(hyp, dict):
            c.error(
                "E-HYPOTHESIS-METRIC",
                f"hypotheses[{i}]",
                f"is a {type(hyp).__name__}, not a mapping with `metric`, `direction` and "
                "`threshold`",
            )
            continue

        kind = hyp.get("kind")
        if kind not in _KINDS:
            c.error(
                "E-HYPOTHESIS-KIND",
                f"hypotheses[{i}].kind",
                f"is `{kind}`; the only kinds are `confirmatory` and `exploratory`, and "
                "there is no default — `hypotheses.evaluate` counts a hypothesis into the "
                "correction family only when `kind` is exactly `confirmatory`, so a typo or "
                "an omission drops a pre-registered claim out of its family and decides it "
                "on the raw, tighter bound instead of the corrected one",
            )

        direction = hyp.get("direction")
        if direction not in _DIRECTIONS:
            c.error(
                "E-HYPOTHESIS-DIRECTION",
                f"hypotheses[{i}].direction",
                f"is `{direction}`; the only directions are `greater` and `less`, and it is "
                "required — the evaluator refuses to guess by returning `supported: None` "
                "for anything else, so a mistyped or missing direction otherwise reaches a "
                "full run and comes back with no verdict rather than being refused before "
                "one starts",
            )

        threshold = hyp.get("threshold")
        if not isinstance(threshold, (int, float)) or isinstance(threshold, bool):
            c.error(
                "E-HYPOTHESIS-THRESHOLD",
                f"hypotheses[{i}].threshold",
                f"is `{threshold}`; a hypothesis is one quantity against one numeric "
                "threshold, and `verdict_for` compares against nothing else — a missing or "
                "non-numeric threshold yields `supported: null` after the whole run is "
                "spent, with nothing in the record saying why",
            )

        evaluate_on = hyp.get("evaluate_on")
        if evaluate_on is not None and evaluate_on not in _EVALUATE_ONS:
            c.error(
                "E-HYPOTHESIS-EVALUATE-ON",
                f"hypotheses[{i}].evaluate_on",
                f"is `{evaluate_on}`; the only values are `observed`, `ci95_lower` and "
                "`ci95_upper` — unlike `direction`, the evaluator has no guard for this one "
                "and silently reads anything else as `ci95_upper`, so a typo changes which "
                "bound the verdict is about rather than being caught anywhere",
            )

        compare = hyp.get("compare")
        if isinstance(compare, dict):
            if "to" in compare and compare.get("to") != "baseline":
                c.error(
                    "E-HYPOTHESIS-COMPARE-TO",
                    f"hypotheses[{i}].compare.to",
                    f"is `{compare.get('to')}`; the only value is `baseline` — core computes "
                    "no other per-condition comparison, and `hypotheses.resolve` reads the "
                    "baseline block whatever this says, so any other value names a "
                    "comparison that will never be made and is silently evaluated against "
                    "the baseline instead",
                )
            # `to: baseline` is the ordinary spelling, but `hypotheses.resolve`
            # reads `compare.condition` as a baseline comparison whether or not
            # `to` says so — so a bare `{condition: X}` implies the same
            # comparison `to: baseline` spells out, and needs the same declared
            # baseline. Without this second branch, that bare form fired neither
            # this check (no `to` to read) nor `E-HYPOTHESIS-CONDITION` (the
            # label can resolve just fine), and validated clean while naming a
            # condition and nothing to compare it against.
            #
            # Excludes `contrast in compare`: `resolve` checks `"contrast" in
            # compare` first and returns from that branch without ever reading
            # `condition` — so `{contrast: x, condition: y}` resolves through the
            # contrast, not the baseline, and needs no baseline at all. Without
            # this exclusion, a hypothesis that names both would be refused for a
            # comparison it was never going to make.
            implies_baseline = compare.get("to") == "baseline" or (
                "condition" in compare and "to" not in compare and "contrast" not in compare
            )
            missing_baseline = implies_baseline and not has_baseline
            if missing_baseline:
                if "to" in compare:
                    detail = "sets `to: baseline`, but `sweep.baseline` is not declared"
                else:
                    detail = (
                        "names `condition` with no `to` and no declared `sweep.baseline` — "
                        "a `compare` names both sides of the comparison, and `to: baseline` "
                        "is the ordinary spelling of the side this is missing"
                    )
                c.error(
                    "E-HYPOTHESIS-BASELINE",
                    f"hypotheses[{i}].compare",
                    f"{detail} — nothing populates a baseline comparison without one, so this "
                    "hypothesis would silently resolve to no observation rather than the "
                    "comparison it names",
                )
            # Gated on `missing_baseline` so one fault gets one code: with no
            # declared baseline there is no comparison for *any* label to name,
            # and `E-HYPOTHESIS-BASELINE` above already says so — reporting the
            # label as unknown too would be the double-report the dotless-metric
            # ordering fix exists to avoid.
            if "condition" in compare and not missing_baseline and labels is not None:
                declared_labels, baseline_labels = labels
                named = compare.get("condition")
                if not isinstance(named, str) or named not in declared_labels:
                    c.error(
                        "E-HYPOTHESIS-CONDITION",
                        f"hypotheses[{i}].compare.condition",
                        f"names `{named!r}`, which is not a condition this run's `sweep` "
                        "declares — `hypotheses.resolve` looks the label up and finds "
                        "nothing, so the verdict comes back `observed: null, supported: "
                        "null` after the whole run is spent, exactly the unresolvable-label "
                        "class `E-STATS-CONTRAST-UNKNOWN` refuses for a contrast's sides",
                    )
                elif named in baseline_labels:
                    c.error(
                        "E-HYPOTHESIS-CONDITION",
                        f"hypotheses[{i}].compare.condition",
                        f"names `{named}`, which is the baseline itself — `vs_baseline` holds "
                        "one entry per *other* condition, because a baseline has no "
                        "comparison against itself, so this resolves to no observation",
                    )
            if "contrast" in compare:
                contrast_id = compare.get("contrast")
                if not isinstance(contrast_id, str) or contrast_id not in contrast_ids:
                    c.error(
                        "E-HYPOTHESIS-CONTRAST",
                        f"hypotheses[{i}].compare.contrast",
                        f"names `{contrast_id!r}`, which `statistics.contrasts` does not declare",
                    )

        metric = hyp.get("metric")
        step, _, name = metric.partition(".") if isinstance(metric, str) else ("", "", "")
        metric_is_well_formed = isinstance(metric, str) and bool(metric) and bool(name)

        # A `scope: "summary"` metric can be a `reported: true` `Estimate` a step
        # supplies directly (`reference.md` § What a hypothesis is tested
        # against, "A hypothesis may name a summary metric") — its own real
        # `ci95`, with no unit table involved, and it is itself the answer to
        # `basis: repeats`'s "reportable but not testable": a reported `Estimate`
        # is neither `basis: repeats` nor untestable, so the warning's own
        # premise is false for one, and the error's "no metric ... could carry
        # an interval" is false for one too. Core never inspects a step's body
        # to know whether *this* summary step actually returns one, so both
        # checks below fire only when the metric's scope is affirmatively known
        # and is *not* `"summary"` — unknown (no experiment) is treated the same
        # as `"summary"`, conservatively. A `condition`- or `repeat`-scoped
        # metric has no such exception: its only possible interval is `basis:
        # units`, derived from `data.units` through a template's `aggregate`,
        # which `no_interval_possible` already covers in full.
        #
        # Gated on `metric_is_well_formed` too, and deliberately checked before
        # the malformed-metric refusal just below: a `metric` that doesn't parse
        # to `step.metric` names no scope to look up, and `step` alone (a
        # dotless value) can still collide with a real step name, which would
        # otherwise let this block read a real `scope` for a metric that is
        # about to be refused anyway — reporting the same entry under two
        # unrelated codes rather than the one `E-HYPOTHESIS-METRIC` fault it
        # actually has.
        if metric_is_well_formed:
            scope = scopes_by_step.get(step) if step else None
            if no_interval_possible and scope not in (None, "summary"):
                if evaluate_on in ("ci95_lower", "ci95_upper"):
                    c.error(
                        "E-HYPOTHESIS-BOUND",
                        f"hypotheses[{i}].evaluate_on",
                        f"names `{evaluate_on}`, but no metric this run computes could carry "
                        "an interval — `data.units` is undeclared and the template defines no "
                        "`aggregate`, so nothing produces a `ci95` to evaluate a bound against",
                    )
                else:
                    c.warn(
                        "W-HYPOTHESIS-INFERENCE-BASE",
                        f"hypotheses[{i}]",
                        "names a metric under a run where `data.units` is undeclared and the "
                        "template defines no `aggregate` — every metric will be `basis: "
                        "repeats`, reportable but not testable against an interval",
                    )

        if not metric_is_well_formed:
            c.error(
                "E-HYPOTHESIS-METRIC",
                f"hypotheses[{i}].metric",
                "is missing or not a `step.metric` string; `compare` says where a "
                "hypothesis is tested and never what, so a contrast or condition "
                "comparison alone leaves the quantity under test unnamed",
            )
            continue

        if experiment is None:
            continue  # the entrypoint didn't import; no step list to check the form against

        scope = scopes_by_step.get(step)
        if scope is None:
            c.error(
                "E-HYPOTHESIS-METRIC",
                f"hypotheses[{i}].metric",
                f"names step `{step}`, which the entrypoint's `steps` list does not declare",
            )
            continue

        has_compare = isinstance(hyp.get("compare"), dict)
        if scope == "summary" and has_compare:
            c.error(
                "E-HYPOTHESIS-FORM",
                f"hypotheses[{i}]",
                f'names `{metric}`, a `scope: "summary"` metric, and declares `compare` — '
                "a summary metric is one value per run, not a contrast between conditions",
            )
        elif scope != "summary" and not has_compare:
            c.error(
                "E-HYPOTHESIS-FORM",
                f"hypotheses[{i}]",
                f'names `{metric}`, a `scope: "{scope}"` metric, without declaring `compare` '
                "— that quantity only exists per condition, so the hypothesis must say which "
                "conditions it compares",
            )


RESAMPLE_METHODS = ("bootstrap",)
"""Every value `statistics.resample.method` may take — `reference.md`
§ Statistical reporting's *Resample methods* table, which is the enum this
tuple enforces.

**A closed, one-value enum on purpose.** `bootstrap` is the only value the
schema shows and the only construction `stats.py` has, and § Statistical
reporting's construction tables enumerate the method strings core *emits*
(`percentile_over_units`, `paired_percentile_over_units`) — outputs, not inputs
a config may name. Stating the enum is what makes `method: bootstap` a
diagnostic rather than a shrug, and what makes adding a second value a
documented change rather than a silent one."""


def _resolved_cells(
    doc: dict[str, Any],
    units_decl: dict[str, Any],
    roster: UnitList | None,
    cluster_by: str | None,
) -> dict[tuple[tuple[str, str], ...], frozenset[str]] | None:
    """The design's realized **cells** — every `sweep.groups` axis drawn for
    real and intersected by `units.cells_of` — or `None` when the design has no
    cell structure or the draw cannot be performed.

    **`_holdout_test_roster` is the precedent, and its ground is repeated here
    verbatim.** That function realizes the holdout through `units.holdout_for`,
    the same pure function `cli._prepare_run` realizes it with, because
    `validate` has to ask *which units will this rest on* of the same
    declaration the run asks it of — **a second answer computed here would be a
    check aimed at a partition the run does not use.** A cell bound on one
    decomposition while the run draws its folds inside another is that defect
    with a different noun.

    **The digest is the real `design_digest(doc)`, not `_check_assign`'s
    placeholder `"validate"`.** That placeholder is sound only where it is
    used: the unstratified, unclustered `by_attribute`-adjacent case, whose
    *sizes* are digest-independent. A cell's **cluster count** is precisely the
    seed-dependent quantity that gating excludes, and it is the number
    `thinnest_cell` returns under a declared `cluster_by`. Drawing at
    `"validate"` would bound `k` against a decomposition no run produces.

    Every fault becomes `None`, the way `_holdout_test_roster` does and for its
    reason: this runs over configs that are already known bad — a malformed
    `assign` block, an unresolvable level, a `blocked` method beside a declared
    `cluster_by`, a unit carrying no value for the cluster attribute — and each
    is reported by its own check elsewhere. Here they mean *no cells resolved*,
    and every cell-aware check simply does not run rather than reporting a
    second, derived fault on top of the one the reader has to fix anyway.

    **`None` also answers the triviality question, so no caller has to.** A
    design whose `sweep.groups` resolves to no axis at all has no cell
    structure, and returning `None` rather than `cells_of({})`'s one empty cell
    makes the caller's test one comparison — the same one
    `cli._prepare_run` makes against its own `group_axes`. Two callers deciding
    "is this decomposition trivial" for themselves is how `validate` ends up
    bounding `k` against one number while the run draws against another.

    The axis loop is `cli._resolved_group_axes`' loop, skip rules included: a
    non-mapping entry, a `by` that is not a non-empty string, and a `levels`
    that is not a non-empty list of strings are each skipped, exactly as
    `_check_assign` skips them. **Deliberately the same skips, not merely
    similar ones**: two loops that skipped different axes would give `validate`
    and `run` different decompositions of one declaration, which is the whole
    fault this function exists not to introduce. It is duplicated rather than
    imported because `cli` imports this module.
    """
    if roster is None:
        return None
    groups = (doc.get("sweep") or {}).get("groups")
    if not isinstance(groups, list) or not groups:
        return None
    assign = units_decl.get("assign")
    blocks = assign if isinstance(assign, dict) else {}
    try:
        clusters = clusters_of(roster, cluster_by) if cluster_by else None
        axes: dict[str, ArmPlan] = {}
        for entry in groups:
            if not isinstance(entry, dict):
                continue
            axis = entry.get("by")
            if not isinstance(axis, str) or not axis:
                continue
            levels = entry.get("levels")
            if not (
                isinstance(levels, list) and levels and all(isinstance(v, str) for v in levels)
            ):
                continue
            block = blocks.get(axis)
            # `dict(axes)` — the axes drawn SO FAR, for `_resolved_group_axes`'
            # reason: an axis whose `stratify_by` names an earlier one is
            # balanced on that axis's realized membership, and a copy rather
            # than the live dict is what the axis was drawn against.
            axes[axis] = assignment_for(
                roster,
                axis,
                block if isinstance(block, dict) else None,
                levels,
                design_digest(doc),
                clusters,
                dict(axes),
            )
        if not axes:
            return None
        return cells_of(axes)
    # `ZeroDivisionError` is the sixth, and the design's Decision 8 enumerates
    # only five: it was **measured**, not predicted, by
    # `test_a_ratio_whose_values_are_not_usable_shares_is_refused[all-zero]`.
    # An `assign.<axis>.ratio` whose weights are all zero reaches
    # `units._apportion`'s `n * weight / total` with `total == 0`, and before
    # H3c-3 task 6 wired this function into `validate_config` nothing in
    # `validate` drew that shape for real — `_check_assign` refuses it as
    # `E-DATA-ASSIGN-RATIO` from the declaration. Without it a config `validate`
    # is supposed to REFUSE crashes instead, which is the collecting-to-raising
    # fault this whole `try` exists to prevent.
    #
    # The list stays an enumeration rather than becoming a bare `except
    # Exception`, for `REPL_DECLARATION_CODES`' reason: a fault outside it is a
    # genuine core defect, and absorbing all of them is how a real error becomes
    # a silent pass.
    except (
        ContractError,
        NotImplementedError,
        KeyError,
        TypeError,
        ValueError,
        ZeroDivisionError,
    ):
        return None


def _check_cell_size(
    doc: dict[str, Any],
    roster: UnitList | None,
    cells: dict[tuple[tuple[str, str], ...], frozenset[str]] | None,
    c: Collector,
) -> None:
    """`W-DATA-CELL-THIN` — the design's thinnest populated cell holds fewer
    units than `limits.min_units_per_cell`.

    **A warning rather than a refusal, because three document sites say
    warning in those words** and the code follows the documents:
    `reference.md` § Validation's *Cells are populated* and *Allocation is
    coherent*, and § The one config file's own inline comment on the
    parameter. § Weighted samples supplies the reason — *"a two-arm design
    where one arm resolves to exactly two units passes `validate` clean and
    reports a real `basis: units` interval from those two observations"* — and
    that is a design whose answer is weak, not a declaration that is wrong.
    The hard line already sits at `E-DATA-ASSIGN-LEVELS`, which refuses the arm
    no unit resolves to at all.

    **Gated on a cell structure resolving, and the gate is the whole of the
    care this check needs.** `materialize.py` writes `min_units_per_cell: 20`
    into every config `publishable init` produces, so an ungated floor over the
    roster would fire on every generated project with fewer than twenty units
    — the scaffold `demo` builds included — and a warning readers learn to skip
    is worse than none. `cells is None` is *no cell structure resolved*, which
    is also what a fault inside `_resolved_cells` becomes, and both readings
    are silence here. Neither § Validation row states the gate in its own cell;
    both rows' **examples** carry it (`sex × arm`, `allocation: between` over 2
    arms), which is the *"taking a § Validation row's own wording as its whole
    scope"* misreading in its natural habitat.

    **`units.thinnest_cell` is deliberately NOT reused, and the two answers
    genuinely differ.** That helper returns a *fold basis* — the cluster count
    under a declared `data.units.cluster_by`, the unit count otherwise —
    because `replication._fold_k` bounds `k` against indivisible things. This
    floor counts **units**, and `limits.min_units_per_cell` says so in its
    name. On a design whose thinnest cell holds two clusters of ten units, the
    fold basis is 2 and the unit count is 20: at `min_units_per_cell: 20` this
    check must be silent and `thinnest_cell` would have it report, naming a
    cluster count as though it were a unit count. Two questions over one
    decomposition, not one derivation written twice — `populated_cells` is the
    shared piece, and it is shared.

    **Empty cells are skipped**, through `units.populated_cells` — the same
    projection the draw loops over and the same one `_check_holdout`'s bound
    takes, rather than a second spelling. A cell no unit falls in holds zero
    units, is below every floor, and would name a cell no reader can make
    thicker; a level no unit resolves to is `E-DATA-ASSIGN-LEVELS`' fault and
    is reported there.

    Reported **once**, for the thinnest such cell, on
    `W-DATA-CLUSTER-UNDECLARED`'s and `W-DATA-WEIGHT-UNDECLARED`'s own shape:
    the remedy — enrol more units, or drop an axis — is the same for every thin
    cell in one design, so a diagnostic per cell would be the same sentence
    repeated once per level of the product.

    The `bool`/`int` guard on the floor is `_check_report_by`'s, for its
    reason: `check_envelope` is what REPORTS a wrong-typed
    `limits.min_units_per_cell` (`E-CONFIG-TYPE`), a leaf fault is deliberately
    non-fatal so this function still runs on that doc, and `isinstance(True,
    int)` is `True` in Python.
    """
    if roster is None or cells is None:
        return
    floor = (doc.get("limits") or {}).get("min_units_per_cell")
    if isinstance(floor, bool) or not isinstance(floor, (int, float)):
        return
    populated = populated_cells(cells)
    if not populated:
        return
    cell, keys = min(populated, key=lambda item: len(item[1]))
    if len(keys) >= floor:
        return
    c.warn(
        "W-DATA-CELL-THIN",
        "limits.min_units_per_cell",
        f"is {floor}, and the design's thinnest cell (`{cell_label(cell)}`) holds "
        f"{len(keys)} of {len(roster)} resolved units. Every interval a condition "
        f"in that cell reports rests on those, and attrition can only make the "
        f"number smaller",
    )


def _holdout_test_roster(
    doc: dict[str, Any],
    units_decl: dict[str, Any],
    roster: UnitList | None,
    cluster_by: str | None,
    cells: dict[tuple[tuple[str, str], ...], frozenset[str]] | None,
) -> UnitList | None:
    """The holdout's realized **test** partition, or `None` when the design
    declares none or the draw cannot be performed.

    Realized through `units.holdout_within_cells`, the same pure function
    `cli._resolved_holdout` realizes it with — which is the reason that
    function is pure at all, `assignment_for`'s own argument: `validate` has to
    ask "which units will the interval rest on" of the same declaration the run
    asks it of, so a second answer computed here would be a check aimed at a
    partition the run does not use.

    **`cells` is `_resolved_cells`' answer, threaded rather than re-derived**,
    and it is what makes that sentence true again. The split is drawn inside
    each cell, so a call that passed the decomposition here and not there — or
    the reverse — would bound `limits.min_clusters` against a test partition no
    run produces. `None` is a design with no cell structure and takes
    `holdout_within_cells`' own one-cell reduction, which is the byte-identical
    whole-roster draw this function has always made.

    **Does not raise for any fault `validate` can already see.** `validate`
    collects, and this runs over configs that are already known bad — a
    malformed `frac`, an unresolvable column, an unknown stratum, a cluster
    attribute a unit does not carry — each caught by the `except` below and
    each reported by its own check elsewhere. Here they become `None`, and
    the check that reads this simply does not run rather than reporting a
    second, derived fault on top of the one the reader has to fix anyway.
    """
    if roster is None:
        return None
    block = units_decl.get("holdout")
    if not isinstance(block, dict) or not block:
        return None
    try:
        clusters = clusters_of(roster, cluster_by) if cluster_by else None
        plan = holdout_within_cells(
            roster,
            block,
            seed=holdout_seed_for(block, design_digest(doc), roster),
            cells=cells,
            clusters=clusters,
        )
    except (ContractError, NotImplementedError, KeyError, TypeError, ValueError):
        return None
    test = set(plan.test)
    return UnitList([u for u in roster if u.key in test])


def _check_resample(
    doc: dict[str, Any],
    roster: UnitList | None,
    c: Collector,
    holdout_test: UnitList | None = None,
) -> None:
    """Every check `statistics.resample` gets, seven findings in declaration
    order — the enumeration is the list, not a sample of it:

    - `E-STATS-RESAMPLE-UNITS` — a `resample` with no `data.units` at all.
    - `E-STATS-RESAMPLE-METHOD` — the `method` enum.
    - `E-STATS-RESAMPLE-N` — the `n` floor.
    - `E-STATS-RESAMPLE-STRATIFY-UNKNOWN` — a `stratify_by` name that is not a
      declared unit attribute.
    - `W-STATS-RESAMPLE-CLUSTERS` — **reads the holdout's test partition when
      one is declared, the roster otherwise:** `limits.min_clusters` against
      the resolved cluster count, over the per-unit table a resample actually
      draws from.
    - `E-STATS-RESAMPLE-STRATIFY-VARIES` — **reads the WHOLE roster, on
      purpose**, even under a `data.units.holdout`. Constancy within a cluster
      over the whole roster implies it over any subset, so the wider read is
      the stricter one; the narrower would let a config validate whose training
      half is incoherent and whose test half happens not to show it.
    - `W-STATS-RESAMPLE-FAMILY` — the comparison-family lower bound on that
      same `n`.

    **Two of the seven read `roster`, not one**, and each carries its own
    `roster is not None` guard rather than leaning on a caller or on the
    no-`return` gate below. A check added here must state which side of that
    line it is on; this list is what the next reader counts against, so an
    eighth finding belongs in it.

    `_check_unimplemented`'s wholesale refusal of a declared `resample`
    retired with H4a task 12 (commit `2fdc957`) — a shape fault inside the
    block is worth reporting on its own terms rather than only as
    "unsupported", the same way a malformed `report_by` entry is worth
    naming even though `report_by` runs for real. Resampling itself was not
    honored by `cli.command_run` at that commit, so for two tasks a declared
    `resample` validated clean here before it changed any interval; H4a tasks
    13–15 closed that window, and `cli.command_run` now resolves the block
    once and threads it into the column and derived constructions alike.

    Every check here presupposes the declaration is a mapping; a scalar or a
    list is `check_envelope`'s `E-CONFIG-TYPE` (`statistics.resample` is typed
    `dict`), and a wrong-typed child (`method`, `n`, `stratify_by`) is the same, because Task 3
    closed the block one level in. A leaf type fault is deliberately non-fatal
    in this module — reported, and validation continues — so each value read
    here is `isinstance`-guarded and quietly skipped when it is not a leaf the
    envelope types — the same division `_check_report_by` keeps with its own
    entries.

    **The `n` floor is the load-bearing one.** `stats.percentile_over_units`
    returns `None` below `min_honest_draws(confidence)` draws — 80 at 95 % — so
    a declared `n: 50` would null `ci95` on every recorded column in the run,
    silently and with nothing in the record saying why. Refusing it here is why
    `validate` learns about `n` in the same slice that will teach
    `summarize_step` to honor it, rather than a slice later.
    """
    statistics = doc.get("statistics") or {}
    resample = statistics.get("resample")
    if not isinstance(resample, dict) or not resample:
        return
    # No roster at all, worth its own finding independent of everything below.
    # `reference.md` § The one config file marks `units:` "required by fold,
    # resample, null_test", and § Where units come from says resample "isn't
    # available" without one. The precedent is `_check_replication`'s own
    # `E-REPL-FOLD-NO-UNITS` — the same `not (doc.get("data") or {}).get("units")`
    # expression, refusing a `fold` level for the identical reason. (Not
    # `E-REPL-FOLD-K`: that is the unrelated `k: all`-basis-unknowable fault.)
    # `null_test`'s own no-roster fault is `_check_null_test`'s
    # `E-STATS-NULLTEST-UNITS` (H4d task 8) — the same expression, checked
    # there rather than here, since the two declarations are independent and
    # a config can carry either without the other.
    #
    # Read from the DECLARATION, not from `roster is None`: the roster is also
    # `None` when `data.units` is declared and failed to resolve, and that fault
    # already has `_check_units`' own finding. A second, derived fault on top of
    # the one the reader has to fix anyway is what `validate_config`'s
    # `usable_cluster` guard avoids by the same argument.
    #
    # No `return` here, matching the `E-REPL-FOLD-NO-UNITS` twin. Of the checks
    # below, `method`, `n`, the family bound, and `stratify_by`'s names read
    # `resample`/`doc` alone and are safe with no roster at all. The two that
    # DO read `roster` — `limits.min_clusters` and the stratum-varies-within-
    # cluster composition, both enumerated in the docstring above — each
    # require `roster is not None` themselves rather than leaning on this
    # early-exit having not fired. So this comment's job is only to explain why
    # there is no `return` here — not to promise every check below is
    # roster-independent, which the next reader extending this function must
    # re-verify against the docstring's list rather than assume from this
    # sentence. Stopping here would silently swallow a `method`/`n` fault the
    # reader would only meet on their next pass.
    units_declared = ((doc.get("data") or {}).get("units")) or {}
    if not units_declared:
        c.error(
            "E-STATS-RESAMPLE-UNITS",
            "statistics.resample",
            "is declared and `data.units` is not, so there is no unit table to draw "
            "from and no metric core could recompute on a draw — a declaration that "
            "changes no behavior. Declare `data.units`, or drop `resample` and report "
            "over repeats, which is honest for a design whose executions are the "
            "observations",
        )
    method = resample.get("method")
    # `None`/absent means the documented default, `bootstrap` — § Statistical
    # reporting: declaring `resample` "changes the method or the count rather
    # than switching the behaviour on". Only a value actually named is checked.
    # A wrong-typed `method` is `E-CONFIG-TYPE`'s finding already; skipped here
    # rather than reported a second time under this code.
    if method is not None and isinstance(method, str) and method not in RESAMPLE_METHODS:
        c.error(
            "E-STATS-RESAMPLE-METHOD",
            "statistics.resample.method",
            f"is `{method}`, not one of {', '.join(f'`{m}`' for m in RESAMPLE_METHODS)}",
        )
    n = resample.get("n")
    floor = min_honest_draws()
    # `bool` excluded explicitly: `isinstance(True, int)` is `True` in Python,
    # and `resample: {n: true}` is already `E-CONFIG-TYPE` from the envelope —
    # a value flagged wrong-typed there must not also drive this check.
    if n is not None and isinstance(n, int) and not isinstance(n, bool) and n < floor:
        c.error(
            "E-STATS-RESAMPLE-N",
            "statistics.resample.n",
            f"is {n}; a percentile interval needs at least {floor} draws before both "
            "of its ranks are interior, so below that the lower endpoint IS the "
            "smallest draw while the upper keeps shrinking — low-biased and "
            f"systematically too narrow. Under {floor} core reports no interval at "
            "all, so this would null `ci95` on every metric in the run rather than "
            "narrowing one",
        )
    # The declared set, `data.units.attributes` — the same reference
    # `_check_report_by` reads, and for its reason: `strata.levels_for` and the
    # draw both read the attribute per unit, so a typo and an attribute no unit
    # carries are indistinguishable downstream. NOT `units._stratum_groups`,
    # which is `assign`-specific: it admits a `sweep.groups` axis name as a
    # legal target and raises a bare `NotImplementedError` for everything
    # else (deliberately uncoded — its own docstring says why: the raise
    # cannot tell which of two `validate`-time faults it is), and a resample
    # draws from the roster rather than from an allocation, so neither applies.
    #
    # Read through `units.stratum_names`, the same normalization the draw
    # balances on: a bare `stratify_by: site` is one name to both. Two
    # independent readings of one declaration is the validate-clean-then-
    # disagree shape that function's own docstring exists to prevent.
    #
    # Filtered to strings the same way `_check_report_by` filters `attributes`:
    # a non-string item there is `_check_units`' own finding (`E-UNITS-ATTR-
    # MISSING`), and `set(...)` over the raw list would raise on an unhashable
    # one before that finding is ever reached.
    declared = {
        a
        for a in (((doc.get("data") or {}).get("units") or {}).get("attributes") or [])
        if isinstance(a, str)
    }
    stratify_by = resample.get("stratify_by")
    # The container itself IS an envelope leaf (`(str, list)`), unlike
    # `assign.<axis>.stratify_by`, which has no `LEAF_TYPES` entry at all — so a
    # wrong-typed container (`stratify_by: 5`) is already `E-CONFIG-TYPE` from
    # the envelope, and `stratum_names` would otherwise wrap it as a one-name
    # tuple and report it a second time under this code. Skipped here the same
    # way `method`/`n` skip a wrong-typed leaf above.
    if stratify_by is not None and not isinstance(stratify_by, (str, list)):
        stratify_by = None
    for name in stratum_names(stratify_by):
        # One finding per offending name, not one naming only the first: the
        # declaration is a list and each entry is separately fixable, the same
        # rule `E-DATA-ASSIGN-STRATIFY-UNKNOWN` already follows. A non-string
        # entry is absorbed here rather than left silent — it names no
        # attribute either, and `stratify_by`'s LEAF type is the container's,
        # not each item's.
        if not isinstance(name, str) or name not in declared:
            c.error(
                "E-STATS-RESAMPLE-STRATIFY-UNKNOWN",
                "statistics.resample.stratify_by",
                f"names `{name}`, which is not a unit attribute — a stratum is read "
                f"per unit when the draw is taken, so it has to be one. "
                f"`data.units.attributes` declares {', '.join(sorted(declared)) or 'none'}",
            )

    # `limits.min_clusters`: materialized in every generated config, typed by
    # `envelope.py`, and — until this slice — read by nothing. § Validation's
    # *Clusters enough to resample*: "`statistics.resample` with `cluster_by:
    # animal_id` over 4 animals bootstraps 4 draws; below `limits.min_clusters`
    # (warning)". Scoped to `resample` WITH `cluster_by`, because `cluster_by`
    # alone decides each condition's own interval and draws nothing.
    #
    # Counted through `units.fold_basis`, the same function `_check_replication`
    # and `_check_sweep` read — via `basis`, resolved once above this call and
    # threaded through as their `fold_basis=` argument. This check calls it a
    # second time on `cluster_by` rather than being handed `basis` itself:
    # `basis` is the fold's basis, while this call is over `holdout_test` when
    # one resolved — a different roster than `basis` was counted from whenever a
    # holdout is declared — and, since H3c-3 threaded cells into it, `basis` is
    # narrowed to the SMALLEST CELL under a cell structure while this
    # denominator is not, which is the third reason the two are deliberately not
    # the same derivation reused, only the same function.
    #
    # **Which question this call asks: how many independent draws does a
    # percentile interval rest on.** `statistics.resample` draws over the
    # per-unit table, which holds every condition's units across every cell, so
    # the answer does not decompose by cell — the denominator is the whole test
    # roster's clusters. Threading `basis` in, or giving `fold_basis` a `cells`
    # argument, would warn against a denominator no interval used (Ruling LL,
    # and Decision 4's three-site table).
    #
    # A second call to one derivation is not a second derivation, but it IS a
    # second `try`/`except ContractError` an edit to the first must not forget
    # to mirror.
    cluster_by = units_declared.get("cluster_by")
    min_clusters = (doc.get("limits") or {}).get("min_clusters")
    if (
        roster is not None
        and isinstance(cluster_by, str)
        and cluster_by
        and isinstance(min_clusters, int)
        and not isinstance(min_clusters, bool)
    ):
        try:
            # **The test partition when a holdout is declared, not the whole
            # roster.** `statistics.resample` draws over the per-unit table,
            # which under a holdout holds only the units that recorded — so a
            # percentile interval rests on the clusters of the TEST side, and
            # counting the wider set warns against a denominator no interval
            # used. Wrong in the direction of NOT firing: 50 clusters at
            # `frac: 0.2` leaves roughly 10, and `min_clusters: 20` passed
            # silently.
            #
            # `holdout_test` is `None` whenever no holdout is declared or the
            # draw could not be performed, so this is `roster` unchanged for
            # every other design — including every config in the build before
            # a holdout existed.
            groups = fold_basis(holdout_test if holdout_test is not None else roster, cluster_by)
        except ContractError:
            # A unit carrying no value for the cluster attribute
            # (`E-DATA-CLUSTER-UNKNOWN`). Sometimes reported beside this by
            # `_check_cluster_by` (which tests the DECLARATION against
            # `attributes`) or by `_check_units` (a column that never resolved
            # at all) — but NOT always: `cluster_by: measurements.by`, naming a
            # measurement rather than an input column, resolves the roster and
            # `_check_units` cleanly, and `_check_cluster_by` has nothing to
            # say about a name that isn't a unit attribute in the first place.
            # That combination reaches here with no companion finding. Swallowed
            # anyway, because this check cannot proceed without a readable
            # grouping and `validate` collects rather than raises — a config in
            # that shape validates clean today and meets `E-DATA-CLUSTER-UNKNOWN`
            # for real at `run`, same as the `basis` computation above handles it.
            groups = None
        if groups is not None and groups < min_clusters:
            counted = "this holdout's test partition" if holdout_test is not None else "this roster"
            c.warn(
                "W-STATS-RESAMPLE-CLUSTERS",
                "limits.min_clusters",
                f"is {min_clusters}, and `data.units.cluster_by: {cluster_by}` puts "
                f"{counted} in {groups} clusters — `resample` draws whole clusters, so the "
                f"percentile interval rests on {groups} independent draws however many "
                "units they hold",
            )

    # The composition rule, from the declarations plus the roster — the same
    # shape *Fold strata survive clustering* and *Holdout strata survive
    # clustering* already have, and reusing `units.stratum_varies_within_cluster`
    # rather than minting a second notion of constancy is the point: a resample
    # draws whole clusters, so it inherits the rule rather than inventing one.
    if roster is not None and isinstance(cluster_by, str) and cluster_by:
        for name in stratum_names(resample.get("stratify_by")):
            if not isinstance(name, str) or name not in declared:
                continue  # already refused above
            try:
                offender = stratum_varies_within_cluster(roster, cluster_by, name)
            except ContractError:
                # A unit with no cluster value (`E-DATA-CLUSTER-UNKNOWN`),
                # already reported beside this. This module collects.
                break
            if offender is not None:
                cluster, seen = offender
                c.error(
                    "E-STATS-RESAMPLE-STRATIFY-VARIES",
                    "statistics.resample.stratify_by",
                    f"names `{name}`, which varies within `{cluster_by}` {cluster} — it "
                    f"carries {', '.join(seen)}. A resample draws whole clusters, so a "
                    "cluster cannot be drawn within one stratum while carrying two; "
                    "stratify on an attribute constant within a cluster",
                )

    # The comparisons-only lower bound. Holm's tightest level is `ALPHA / m` at
    # rank 1, and a corrected interval is read off the same pool the raw one
    # was — true of every pool-backed member today; a future construction that
    # reads a different pool for the corrected number is not this check's to
    # anticipate — (`stats.interval_at`, which `correction` calls), so a pool
    # below `min_honest_draws(1 - level)` yields `ci95_corrected: null` with
    # only `W-STATS-CORRECTED-THIN` at run time to say why. `m` is
    # `comparisons × metrics` and the metric count is unknowable here BY
    # DESIGN — `correction.family_shape` derives it from `Member`s built after
    # the run, out of `io.record` keys and `aggregate`'s return, and core never
    # inspects the body of user Python. So this bounds against `comparisons`
    # alone: always true when it fires, silent when it might not be. The
    # residue — a config with many metrics that still nulls every corrected
    # bound, and the separate hypothesis family that has the same shape of gap
    # — is filed in `spec-defects.md` as a run-time disclosure that already
    # exists, not a check to build.
    #
    # `expand(doc)` re-derived behind the same guard `_check_sweep` and
    # `_check_contrasts` each use directly — `_check_hypotheses` is not a third
    # precedent here; it goes through `_condition_labels`, which wraps its own
    # `expand(doc)` in the same shape of guard but is a different call site —
    # rather than hoisted into `validate_config` the way `fold_basis` is: that
    # hoist exists because two checks BOUND declarations against one number and
    # must not disagree, where this only sets a warning threshold.
    correction_method = statistics.get("correction") or "holm"
    # `fdr_bh` implies no per-comparison level at all and `none` corrects
    # nothing, so under either `ci95_corrected` is null whatever `n` is and this
    # would be a false positive. Unset is `holm`, the same default `cli` applies.
    if correction_method not in ("holm", "bonferroni"):
        return
    # An absent `n` is not "nothing to bound": `cli.py`'s `derived_metric_draws
    # = 2000` is the value actually used whenever `n` goes undeclared — the
    # documented default (§ How a metric becomes a number) — so a large enough
    # family still underprovisions it. Only a value already reported —
    # wrong-typed (`E-CONFIG-TYPE`) or below the honest floor
    # (`E-STATS-RESAMPLE-N`, checked above) — has nothing left for this bound
    # to add.
    if n is None:
        effective_n = 2000
    elif isinstance(n, int) and not isinstance(n, bool):
        if n < floor:
            return
        effective_n = n
    else:
        return
    try:
        conditions = expand(doc)
    except Exception:
        conditions = []
    try:
        comparisons = len(resolve_contrasts(doc, conditions))
    except (TypeError, KeyError, AttributeError, ValueError):
        comparisons = 0
    if comparisons < 1:
        return
    needed = min_honest_draws(1.0 - ALPHA / comparisons)
    if effective_n < needed:
        plural = "" if comparisons == 1 else "s"
        n_desc = f"is {n}" if n is not None else "is unset, so defaults to 2000,"
        c.warn(
            "W-STATS-RESAMPLE-FAMILY",
            "statistics.resample.n",
            f"{n_desc} and this design resolves to {comparisons} comparison{plural}, so "
            f"`{correction_method}` puts the tightest corrected level at "
            f"{ALPHA / comparisons:.5f} — an interval at that level needs at least "
            f"{needed} draws, so `ci95_corrected` would be null rather than reported "
            "too narrow. This is a lower bound: the family is comparisons × metrics "
            "and the metric count is not knowable before the run, so the real "
            "requirement is at least this",
        )


def _check_null_test(doc: dict[str, Any], roster: UnitList | None, c: Collector) -> None:
    """Every check `statistics.null_test` gets — the enumeration is the list, not a
    sample of it:

    - `E-STATS-NULLTEST-UNITS` — a `null_test` with no `data.units` at all.
    - `E-STATS-NULLTEST-METHOD` — the `method` enum.
    - `E-STATS-NULLTEST-N` — the `n` floor, `stats.min_honest_permutations`.
    - `E-STATS-NULLTEST-SHUFFLE` — a `shuffle` that is absent or empty (there is
      nothing to relabel), OR one naming neither a declared unit attribute NOR a
      declared `sweep.groups` axis.
    - `E-STATS-NULLTEST-REPORTBY` — a `shuffle` naming a `statistics.report_by`
      attribute.
    - `E-STATS-NULLTEST-LEVEL` — **reads `roster`** for one of its two findings:
      a `shuffle` that varies within some clusters and not others, so neither a
      within-cluster nor a whole-cluster null applies; OR — roster-independent,
      the declaration alone is enough — a `shuffle` naming a `sweep.groups` axis
      alongside a declared `cluster_by`, which `null_test_level` cannot derive a
      level for at all (see its own docstring).

    **Only one call in this function reads `roster`** (`null_test_level`'s), and
    it carries its own `roster is not None` guard rather than leaning on a
    caller; a check added here must state which side of that line it is on.

    **`shuffle` is checked against `data.units.attributes` UNION the declared
    `sweep.groups` axis names**, and the union is the load-bearing half rather than
    a convenience: a group-axis shuffle is the only p-value home that joins the
    correction family, so a check reading `attributes` alone would refuse the one
    shape a `null_test` is declared for. The precedent for admitting an axis name
    beside an attribute name is `units._stratum_groups`, which already does it for
    `assign`. **`null_test_level` itself is never called with an axis name**,
    though — its domain is a roster attribute, so this function calls it only
    when `shuffle in declared`, and refuses outright (`E-STATS-NULLTEST-LEVEL`)
    when `shuffle` is an axis-only name under a declared `cluster_by`, rather
    than passing a value outside what that function was built to answer.

    Every check here presupposes the declaration is a mapping; a scalar or a list
    is `check_envelope`'s `E-CONFIG-TYPE`, and so is a wrong-typed child, because
    the block is closed one level in. A leaf type fault is deliberately non-fatal
    in this module, so each value read here is `isinstance`-guarded and quietly
    skipped when it is not a leaf the envelope types.
    """
    statistics = doc.get("statistics") or {}
    null_test = statistics.get("null_test")
    if not isinstance(null_test, dict) or not null_test:
        return
    # No roster at all, worth its own finding independent of everything below.
    # `reference.md` § The one config file marks `units:` "required by fold,
    # resample, null_test", and § Where units come from says a `null_test` "isn't
    # available" without one. The precedent is `_check_resample`'s own
    # `E-STATS-RESAMPLE-UNITS` and `_check_replication`'s `E-REPL-FOLD-NO-UNITS` —
    # the same `not (doc.get("data") or {}).get("units")` expression.
    #
    # Read from the DECLARATION, not from `roster is None`: the roster is also
    # `None` when `data.units` is declared and failed to resolve, and that fault
    # already has `_check_units`' own finding.
    #
    # No `return`, matching both twins. Of the checks below, only the level
    # derivation reads `roster`, and it requires `roster is not None` itself
    # rather than leaning on this early-exit having not fired — so this comment's
    # job is to explain the absence of a `return`, not to promise the rest are
    # roster-independent.
    if not ((doc.get("data") or {}).get("units")):
        c.error(
            "E-STATS-NULLTEST-UNITS",
            "statistics.null_test",
            "is declared and `data.units` is not, so there is no unit table to relabel "
            "and no metric core could recompute under a relabelling — a declaration "
            "that changes no behavior. Declare `data.units`, or drop `null_test` and "
            "report over repeats, which is honest for a design whose executions are the "
            "observations",
        )
    method = null_test.get("method")
    if method is not None and isinstance(method, str) and method not in NULL_TEST_METHODS:
        c.error(
            "E-STATS-NULLTEST-METHOD",
            "statistics.null_test.method",
            f"is `{method}`, not one of {', '.join(f'`{m}`' for m in NULL_TEST_METHODS)}",
        )
    n = null_test.get("n")
    floor = min_honest_permutations()
    # `bool` excluded explicitly: `isinstance(True, int)` is `True` in Python, and
    # `n: true` is already `E-CONFIG-TYPE` from the envelope — a value flagged
    # wrong-typed there must not also drive this check.
    if n is not None and isinstance(n, int) and not isinstance(n, bool) and n < floor:
        c.error(
            "E-STATS-NULLTEST-N",
            "statistics.null_test.n",
            f"is {n}; a permutation p-value's smallest possible value is 1/(n+1), so "
            f"below {floor} relabellings it cannot fall under 0.05 however extreme the "
            "observed statistic is — the test would be incapable of the answer it was "
            "declared to look for",
        )
    declared = {
        a
        for a in (((doc.get("data") or {}).get("units") or {}).get("attributes") or [])
        if isinstance(a, str)
    }
    axes: set[str] = set()
    for axis in (doc.get("sweep") or {}).get("groups") or []:
        by = axis.get("by") if isinstance(axis, dict) else None
        if isinstance(by, str):
            axes.add(by)
    shuffle = null_test.get("shuffle")
    # `null_test` is declared FOR a relabelling, so an absent or empty `shuffle`
    # is the block's missing subject — a declaration that permutes nothing and
    # changes no behavior, the same class of hole task 8 closed one field over
    # for a missing roster. `reference.md` § Validation's *Null test coherence*
    # already states "requires `shuffle`"; this is the check behind that row.
    # Read from the DECLARATION (`None` covers both an absent key and an
    # explicit `shuffle: null`, which § The one config file treats as
    # equivalent everywhere else), not from any derived state, so a wrong-typed
    # `shuffle` (caught by the envelope's `E-CONFIG-TYPE`) is quietly skipped
    # here rather than double-reported.
    if shuffle is None or (isinstance(shuffle, str) and not shuffle):
        c.error(
            "E-STATS-NULLTEST-SHUFFLE",
            "statistics.null_test.shuffle",
            "is unset, so there is nothing to relabel — a declared `null_test` needs "
            "a unit attribute or a `sweep.groups` axis to permute, or it changes no "
            "behavior. `data.units.attributes` declares "
            f"{', '.join(sorted(declared)) or 'none'}; `sweep.groups` declares "
            f"{', '.join(sorted(axes)) or 'none'}",
        )
    elif isinstance(shuffle, str) and shuffle and shuffle not in (declared | axes):
        c.error(
            "E-STATS-NULLTEST-SHUFFLE",
            "statistics.null_test.shuffle",
            f"names `{shuffle}`, which is neither a unit attribute nor a `sweep.groups` "
            "axis — the label is read per unit when the relabelling is drawn, so it has "
            f"to be one. `data.units.attributes` declares "
            f"{', '.join(sorted(declared)) or 'none'}; `sweep.groups` declares "
            f"{', '.join(sorted(axes)) or 'none'}",
        )
    report_by = {a for a in (statistics.get("report_by") or []) if isinstance(a, str)}
    if isinstance(shuffle, str) and shuffle in report_by:
        c.error(
            "E-STATS-NULLTEST-REPORTBY",
            "statistics.null_test.shuffle",
            f"names `{shuffle}`, which `statistics.report_by` also names. A permutation "
            "of that attribute moves units between strata, so each drawn stratum holds a "
            "different set of units and the null describes a different partition rather "
            "than the same estimate under a null hypothesis. Shuffle an attribute the "
            "reporting strata do not use, or drop the level from `report_by` and read "
            "the contrast instead",
        )
    cluster_by = ((doc.get("data") or {}).get("units") or {}).get("cluster_by")
    cluster_declared = isinstance(cluster_by, str) and bool(cluster_by)
    # `null_test_level`'s domain is a roster ATTRIBUTE: it reads
    # `unit.attributes.get(shuffle)` per unit, so passing an axis name that is
    # NOT also a declared attribute reads nothing for anybody — every unit
    # renders "no value", every cluster reads constant, and the function
    # returns a confident `whole_cluster` for a roster it never actually
    # examined. That is the fail-open CLAUDE.md § Answering a question with a
    # proxy warns about, found in review: a `sweep.groups` axis under a
    # declared `cluster_by` has no roster-attribute derivation in this build,
    # so this refuses the combination rather than silently guessing a level —
    # never calling `null_test_level` with a bare axis name at all.
    if (
        cluster_declared
        and isinstance(shuffle, str)
        and shuffle in axes
        and shuffle not in declared
    ):
        c.error(
            "E-STATS-NULLTEST-LEVEL",
            "statistics.null_test.shuffle",
            f"names `{shuffle}`, a `sweep.groups` axis, alongside a declared "
            f"`data.units.cluster_by: {cluster_by}` — an axis carries no per-unit "
            "attribute value this build can read, so whether the relabelling is "
            "within-cluster or whole-cluster cannot be derived from the roster at all, "
            "rather than merely being ambiguous. Shuffle a unit attribute instead, or "
            "drop `cluster_by` for an axis shuffle",
        )
    # The one remaining check here that reads `roster`, guarded on its own
    # rather than on the no-units exit above having not fired: `data.units` can
    # be declared and fail to resolve, and `_check_units` owns that finding.
    # Restricted to `declared` (never `axes`) for the reason above: this is the
    # only branch that may call `null_test_level`, and it must never do so with
    # a value outside that function's own documented domain.
    elif roster is not None and isinstance(shuffle, str) and shuffle in declared:
        try:
            level, witnesses = null_test_level(
                roster, cluster_by if cluster_declared else None, shuffle
            )
        except ContractError:
            # A unit carrying no cluster value (`E-DATA-CLUSTER-UNKNOWN`), which
            # `_check_cluster_by` or `_check_units` usually reports beside this
            # and sometimes does not — the same swallow `_check_resample`'s
            # `fold_basis` call makes, and for its reason: this check cannot
            # proceed without a readable grouping, and this module collects.
            level, witnesses = "rows", None
        if level == "ambiguous" and witnesses is not None:
            c.error(
                "E-STATS-NULLTEST-LEVEL",
                "statistics.null_test.shuffle",
                f"names `{shuffle}`, which varies within `{cluster_by}` {witnesses[0]} and "
                f"is constant within {witnesses[1]} — so neither a within-cluster null "
                "(permuting labels inside each cluster) nor a whole-cluster one "
                "(relabelling clusters entire) applies to this roster. Shuffle an "
                "attribute that is either constant within every cluster or varying "
                "within every one",
            )


def _check_report_by(doc: dict[str, Any], c: Collector, roster: UnitList | None) -> None:
    """Each `statistics.report_by` attribute, checked against the declared ones,
    then against the roster for a level too thin to disclose.

    `reference.md` § Reporting strata: "validate rejects a `report_by` attribute
    that isn't declared in `data.units.attributes`". The reason is the same one
    `E-STATS-CONTRAST-WITHIN` exists for: `strata.levels_for` reads the attribute
    with `.get`, which returns `None` for a typo exactly as it would for an
    attribute no unit carries, so the two are indistinguishable downstream — the
    record would hold no `by` block and never say why.

    A non-string entry is refused under the same code rather than reaching the
    set membership test below, where an unhashable one would raise out of a
    module whose contract is that it collects.

    The thinness warning that follows counts over *resolved* units, which is all
    `validate` can see; attrition between here and a run is `W-STATS-STRATUM-THIN`'s
    job at run time.
    """
    entries = ((doc.get("statistics") or {}).get("report_by")) or []
    if not isinstance(entries, list):
        return  # `_check_shape` already refused it, and returned early
    # A non-string item in `data.units.attributes` is `_check_units`'s own
    # finding to make (`E-UNITS-ATTR-MISSING`), not this function's — but
    # `set(...)` over the raw list would still crash on it before that finding
    # is ever reached (`TypeError: unhashable type` for a list or dict item).
    # Filtering to strings here just means a non-string item is treated as "not
    # declared", which is already true of it regardless.
    declared = {
        a
        for a in (((doc.get("data") or {}).get("units") or {}).get("attributes") or [])
        if isinstance(a, str)
    }
    for i, name in enumerate(entries):
        if not isinstance(name, str) or name not in declared:
            c.error(
                "E-STATS-REPORTBY-UNKNOWN",
                f"statistics.report_by[{i}]",
                f"names `{name}`, which is not in `data.units.attributes`",
            )

    floor = (doc.get("limits") or {}).get("min_reported_n")
    # `check_envelope` is what REPORTS a wrong-typed `floor` (E-CONFIG-TYPE) —
    # this guard exists because this function may be reached without it having
    # run: a leaf fault is deliberately non-fatal, so `_check_report_by` still
    # runs on a still-malformed `doc`, and `len(keys) < floor` below would raise
    # `TypeError` comparing an `int` to a `str`. `bool` is excluded explicitly,
    # the same rule as the budget guard above: `isinstance(True, (int, float))`
    # is `True` in Python, and a value already flagged wrong-typed by the
    # envelope must not also drive this check — whether or not the result
    # would be visibly wrong. (Here it happens not to be: every level in
    # `levels_for` holds at least one unit, so `len(keys) < floor` can never
    # hold for `floor` coerced to `0` or `1` either. The exclusion still
    # belongs here, on the same principle as the budget guard, rather than
    # relying on that being true forever.)
    if roster is None or isinstance(floor, bool) or not isinstance(floor, (int, float)):
        return
    for i, name in enumerate(entries):
        if not isinstance(name, str) or name not in declared:
            continue  # already refused above
        for level, keys in sorted(levels_for(roster, name).items()):
            if len(keys) < floor:
                c.warn(
                    "W-STATS-REPORTBY-THIN",
                    f"statistics.report_by[{i}]",
                    f"level `{level}` of `{name}` would hold {len(keys)} of "
                    f"{len(roster)} units, below limits.min_reported_n ({floor})",
                )
