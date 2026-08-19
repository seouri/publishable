# src/publishable/apparatus.py
"""What a probe returns, and how a declared probe name resolves to one.

docs/reference.md § The apparatus core can only observe and § The apparatus
files. A probe is a plain function, `probe(cfg) -> Apparatus`, registered the
same way a resolver is — `reference.md` § Creating a plugin — and `Apparatus`
is the one shape it may return.
"""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, cast

from publishable.coercion import coerce_scalars
from publishable.diagnostics import Collector
from publishable.errors import ContractError
from publishable.plugins import check_registration, declared_names, load_entry_point, scan_group


@dataclass(frozen=True)
class Apparatus:
    """What a probe returns: `facts`, and nothing else.

    § The importable surface's row says "What a probe returns: facts", and a
    second field would be a surface no document describes.

    **Not validated here.** `Apparatus` is constructed inside the probe's own
    body, so a refusal raised in `__init__` would be indistinguishable from any
    other exception a probe's body raises. `Unit` is the shipped precedent for
    exactly this split: `Unit.__post_init__` validates nothing (it freezes
    `attributes` into a read-only view, which stops a caller from mutating a
    roster shared across every condition — a property this class does not
    need, since nothing downstream holds one `Apparatus` across two callers),
    and `units._from_resolver` is where a yielded non-`Unit` is refused, under
    `E-RESOLVER-YIELD`. The value contract for `facts` — `str` keys, scalar
    values — is enforced the same way, at core's boundary, once a probe has
    already returned. `frozen=True` stops `facts` from being *rebound*; the
    mapping it holds is not itself made read-only, unlike `Unit.attributes`.
    """

    facts: Mapping[str, Any] = field(default_factory=dict)


PROBE_GROUP = "publishable.probes"


def _probe_for(name: str) -> Callable[..., Any]:
    """The callable an `apparatus_probe` name resolves to, or the refusal that
    answers instead. `units._resolver_for`'s sibling, step for step:

    - **The name**, answered from package metadata alone (`scan_group`), so a
      name no installed distribution registers costs no import at all.
      `E-PROBE-UNKNOWN`, naming every member of the group it did find, because
      the ordinary cause is a spelling. `validate._check_probe` reports the
      same code from the same metadata scan; this function raises it at
      dispatch.
    - **The object**, through `load_entry_point`, the one function in `plugins`
      that calls `EntryPoint.load()`. Every way a plugin's top level can fail
      arrives as `E-PLUGIN-LOAD`, including `SystemExit`.
    - **The declaration against the key** (`check_registration` over
      `declared_names`), `E-PLUGIN-DECORATOR`.

    Two sources of truth exist for "is this probe registered" — the
    entry-point metadata scan above, and the `PROBES` mapping `register_probe`
    fills at import — and they are reconciled here rather than read from either
    alone: `PROBES` alone would resolve a decorator-only registration
    `validate` refused, and the metadata scan alone would resolve to an object
    never checked against its own declaration. `declared_names` is what
    reconciles them, giving `PROBES` its first reader.

    A collision between two distributions claiming this key is **not** decided
    here. `validate`'s own check reports `E-PLUGIN-COLLISION` over the
    complete claim set, from metadata, in name order — the first claimant is
    used here rather than re-deciding a tie, since a verdict computed twice is
    a verdict that can disagree with itself.
    """
    found = scan_group(PROBE_GROUP)
    claimants = found.get(name)
    if not claimants:
        listed = ", ".join(found) if found else "none installed"
        raise ContractError(
            f"`apparatus_probe` names `{name}`, which no installed distribution "
            f"registers in the `{PROBE_GROUP}` entry-point group (registered: {listed})",
            code="E-PROBE-UNKNOWN",
        )
    ep = claimants[0]
    fn = load_entry_point(ep)
    check_registration(ep, declared_names(PROBE_GROUP, fn))
    return cast("Callable[..., Any]", fn)


def observe_once(probe: Callable[..., Any], cfg: Any, *, probe_name: str) -> Apparatus:
    """Call a probe with ONE condition's cfg and return what it gave back.

    Three clauses, every one H7b Part B's shipped resolver path
    (`cli.command_run`'s roster `except BaseException` block), cited rather
    than re-derived: `except BaseException` so a probe calling `sys.exit()`
    is covered — `except Exception` would let a `SystemExit` end the command
    with no diagnostic at all; `KeyboardInterrupt` is re-raised **fresh and
    argument-less, `from None`**, so Ctrl-C still stops the command and a
    `KeyboardInterrupt("…secret…")` a probe body constructed never reaches
    Python's own printer; anything else becomes a coded `ContractError`
    carrying the probe's own message, `E-APPARATUS-RAISED`, the sibling of
    `E-RESOLVER-RAISED`.

    The redaction is NOT here. This function builds the message; the call
    site turns it into a diagnostic through a fresh `Collector` carrying
    `credentials`, which is what redacts — one mechanism per surface,
    deliberately, so each has its own mutation to catch it.

    The return value's shape — whether it is an `Apparatus` at all — is task
    5's boundary check, `check_facts`, not this function's job.
    """
    try:
        returned = probe(cfg)
    except KeyboardInterrupt:
        raise KeyboardInterrupt from None
    except BaseException as exc:
        raise ContractError(
            f"probe `{probe_name}` raised {type(exc).__name__}: {exc}",
            code="E-APPARATUS-RAISED",
        ) from exc
    return cast("Apparatus", returned)


def check_facts(
    returned: Any, declared: Sequence[str], *, probe_name: str, credentials: Mapping[str, str]
) -> dict[str, Any]:
    """The three phase-independent checks, in the order a leak forbids reversing.

    `data.units.attributes`' projection rule, with one deliberate difference:
    a resolver's undeclared attribute is DROPPED, a probe's undeclared fact
    is KEPT — a probe would not return a fact if it did not describe the
    apparatus, while a unit table's columns are the config's declared shape.
    So every key `returned.facts` carries survives into the result, declared
    or not, and only a DECLARED key `returned.facts` omits is refused.
    """
    # 1. shape            → E-APPARATUS-RETURN
    if not isinstance(returned, Apparatus):
        raise ContractError(
            f"probe `{probe_name}` returned a {type(returned).__name__}, not an `Apparatus` — "
            "`Apparatus(facts=...)` is the one shape a probe may return",
            code="E-APPARATUS-RETURN",
        )
    facts = returned.facts
    if not isinstance(facts, Mapping):
        raise ContractError(
            f"probe `{probe_name}` returned an `Apparatus` whose `facts` is a "
            f"{type(facts).__name__}, not a mapping",
            code="E-APPARATUS-RETURN",
        )
    for key in facts:
        if not isinstance(key, str):
            raise ContractError(
                f"probe `{probe_name}` returned a fact keyed by a {type(key).__name__}, "
                "not a `str` — `facts` keys are fact names",
                code="E-APPARATUS-RETURN",
            )
    # 2. credentials      → E-APPARATUS-FACT-CREDENTIAL
    for key, value in facts.items():
        for cred_name, cred_value in credentials.items():
            if value == cred_value:
                raise ContractError(
                    f"probe `{probe_name}` returned fact `{key}` equal to the value core "
                    f"read for `{cred_name}` — a fact may not carry a credential's value, "
                    "so this refuses rather than redacting it into the record",
                    code="E-APPARATUS-FACT-CREDENTIAL",
                )
    # 3. scalar walk      → E-APPARATUS-FACT-TYPE
    try:
        checked = coerce_scalars(dict(facts), f"probe `{probe_name}`")
    except ContractError as exc:
        raise ContractError(str(exc), code="E-APPARATUS-FACT-TYPE") from exc
    # 4. declared keys    → E-APPARATUS-FACT-MISSING
    for key in declared:
        if key not in checked:
            raise ContractError(
                f"`apparatus_facts` names `{key}`, which probe `{probe_name}` did not "
                "return — the plugin and the template disagree about what this probe "
                "supplies",
                code="E-APPARATUS-FACT-MISSING",
            )
    return checked


class Observations:
    """Every observation this run made, and the two documents derived from them.

    One accumulator, two projections, no second source of truth (§ Corrections
    against the code, correction 3). Neither published mapping can supply
    `W-APPARATUS-UNANSWERED` at its own grain: `provenance.apparatus.facts` is
    the first *answered* observation of each fact, so a fact answered on some
    calls and omitted on others shows no `null` at all; `provenance.apparatus.
    unobserved` aggregates over every condition, so it carries no condition to
    name. This class keeps per-(condition, fact) null and total counts —
    strictly more than either published mapping holds — and `facts_document`,
    `unobserved` and `warn_unanswered` are all projections of those counts.
    """

    def __init__(self) -> None:
        self._first_answered: dict[tuple[str, str], Any] = {}
        self._null_counts: dict[tuple[str, str], int] = {}
        self._total_counts: dict[tuple[str, str], int] = {}
        self._conditions: list[str] = []
        self._facts_by_condition: dict[str, list[str]] = {}

    def record(self, condition_key: str, facts: Mapping[str, Any]) -> None:
        """One probe call's worth of facts, for one condition."""
        if condition_key not in self._facts_by_condition:
            self._facts_by_condition[condition_key] = []
            self._conditions.append(condition_key)
        seen = self._facts_by_condition[condition_key]
        for fact, value in facts.items():
            if fact not in seen:
                seen.append(fact)
            pair = (condition_key, fact)
            self._total_counts[pair] = self._total_counts.get(pair, 0) + 1
            if value is None:
                self._null_counts[pair] = self._null_counts.get(pair, 0) + 1
            elif pair not in self._first_answered:
                # The FIRST answered observation wins — a fact whose first call
                # answered `null` and whose second answered a value records the
                # answer; a fact that never answers stays `null`. A build that
                # kept the LAST observation instead cannot be told apart from
                # this one by any fixture with fewer than three observations.
                self._first_answered[pair] = value

    def facts_document(self) -> dict[str, dict[str, Any]]:
        """`provenance.apparatus.facts` — the first answered value per
        (condition, fact), `null` for a fact that never answered."""
        return {
            condition: {
                fact: self._first_answered.get((condition, fact))
                for fact in self._facts_by_condition[condition]
            }
            for condition in self._conditions
        }

    def unobserved(self, declared: Sequence[str]) -> dict[str, dict[str, int]]:
        """`provenance.apparatus.unobserved` — declared facts only, each
        summed over every condition's counts, matching § The apparatus core
        can only observe's own example (`reagent_lot: {null_probes: 3,
        total_probes: 15}`)."""
        out: dict[str, dict[str, int]] = {}
        for fact in declared:
            null_probes = sum(n for (_, f), n in self._null_counts.items() if f == fact)
            total_probes = sum(n for (_, f), n in self._total_counts.items() if f == fact)
            out[fact] = {"null_probes": null_probes, "total_probes": total_probes}
        return out

    def warn_unanswered(self, c: Collector) -> None:
        """`W-APPARATUS-UNANSWERED`, once per (condition, fact) pair with at
        least one `null` observation, read off the counts rather than emitted
        per call — a per-call emission would print the same flaky pair's line
        once for every probe that missed it. Never changes an exit code, on
        `W-ENV-UNLOCKED`'s existing precedent."""
        for condition in self._conditions:
            for fact in self._facts_by_condition[condition]:
                pair = (condition, fact)
                nulls = self._null_counts.get(pair, 0)
                if not nulls:
                    continue
                total = self._total_counts.get(pair, 0)
                c.warn(
                    "W-APPARATUS-UNANSWERED",
                    "apparatus",
                    f"condition `{condition}`'s fact `{fact}` came back `null` on "
                    f"{nulls} of {total} probes",
                )
