# src/publishable/apparatus.py
"""What a probe returns, and how a declared probe name resolves to one.

docs/reference.md § The apparatus core can only observe and § The apparatus
files. A probe is a plain function, `probe(cfg) -> Apparatus`, registered the
same way a resolver is — `reference.md` § Creating a plugin — and `Apparatus`
is the one shape it may return.
"""

import hashlib
import json
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from publishable.coercion import coerce_scalars
from publishable.diagnostics import Collector
from publishable.errors import ContractError
from publishable.plugins import check_registration, declared_names, load_entry_point, scan_group
from publishable.sweep import condition_dir_name


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
        # `isinstance(value, str)` guards the containment check itself: a
        # credential value is always a `str` (`secrets.credential_values`'s
        # return type), and `in` is only the check this row wants for a
        # `str` value — a non-`str` fact value is left for the scalar walk
        # below to accept or refuse on its own terms (`E-APPARATUS-FACT-TYPE`),
        # rather than being tested for containment at all. Matched by
        # CONTAINMENT, the same way `secrets.redact` matches over the
        # identical value set (`credential_values(declared_credential_names(
        # ...))`) — exact equality alone let a probe publish a credential
        # embedded in a larger value (an endpoint URL carrying `?key=<token>`)
        # verbatim into `provenance.apparatus.facts` and the ledger, the two
        # records § The apparatus core can only observe calls "publishable
        # as-is". `cred_value and` skips an unset credential the same way
        # `redact` does, so an empty value can never match every fact.
        if not isinstance(value, str):
            continue
        for cred_name, cred_value in credentials.items():
            if cred_value and cred_value in value:
                raise ContractError(
                    f"probe `{probe_name}` returned fact `{key}` containing the value core "
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


def _unchanged(incoming: Any, first: Any) -> bool:
    """Reflexivity-safe equality for `Observations.changed` (whole-branch
    review, Major 1). A bare `incoming != first` reports `float('nan')` as a
    change against itself, because `nan != nan` is `True` in Python — and
    `coerce_scalars` legally admits a non-finite float (`reference.md`'s
    `E-APPARATUS-FACT-TYPE` row names `float` unqualified), so this is not a
    hypothetical input. Only the nan-vs-nan case is special-cased; every
    other pair, including a `nan` compared against a *different* `nan`-typed
    value or a non-float, still falls through to ordinary `==`.
    """
    if isinstance(incoming, float) and isinstance(first, float):
        if math.isnan(incoming) and math.isnan(first):
            return True
    return bool(incoming == first)


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
                # answer; a fact that never answers stays `null`.
                self._first_answered[pair] = value

    def changed(self, condition_key: str, facts: Mapping[str, Any]) -> tuple[str, Any, Any] | None:
        """The first (fact, first_answered, incoming) triple that contradicts
        this pair's first answered value, or None.

        Compares each incoming fact against `_first_answered[(condition_key,
        fact)]` — never the previous observation, never another condition's
        (Decision 1). Called after `record` for the same `facts`, which is
        what makes the assert below load-bearing rather than defensive:
        `record` establishes `_first_answered[pair]` for every pair whose
        incoming value is not `None`, so by the time this method runs, a
        non-`None` incoming value's pair is *always* already keyed. A
        `self._first_answered.get(pair)` returning `None` for such a pair
        would be a dead branch reachable only if this method's caller broke
        that ordering — reachable by a direct call that skips `record` first
        (verified by review; no shipped test calls it that way), not by any
        fixture that keeps the ordering. Written as an `assert` on core's own
        contract (`execute_plan`'s shipped asserts about its own callers are
        the precedent), not as a silent `continue`.

        A `None` incoming value with no first-answered entry is not that
        case: it is the ordinary "never yet answered" state — `null → value`
        passes precisely because a fact that never answered cannot yet
        contradict itself — so that combination is skipped rather than
        asserted about. A key `facts` does not carry is not iterated at all,
        so an undeclared fact's absence from a later call is never compared.

        **`!=` alone is not reflexivity-safe.** `reference.md`'s
        `E-APPARATUS-FACT-TYPE` row admits `float` unqualified, so
        `coerce_scalars` legally passes through a non-finite value, and
        `float('nan') != float('nan')` is `True` in Python — a fact whose
        value is a constant `nan` would report a change against ITSELF on
        its very first observation, which is exactly the false-stop this
        slice exists to prevent. `_unchanged` below is the reflexivity-safe
        comparison this method uses instead of a bare `!=`.
        """
        for fact, incoming in facts.items():
            pair = (condition_key, fact)
            first = self._first_answered.get(pair)
            if first is None:
                assert incoming is None, (
                    "record() runs before changed() for the same `facts`; a "
                    "non-null incoming value already became this pair's first "
                    "answered entry, so a missing entry here would mean the "
                    "caller broke that ordering, not that the fact never answered"
                )
                continue
            if incoming is None:
                continue
            if not _unchanged(incoming, first):
                return (fact, first, incoming)
        return None

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

    def warn_unanswered(self, c: Collector, declared: Sequence[str]) -> None:
        """`W-APPARATUS-UNANSWERED`, once per (condition, DECLARED fact) pair
        with at least one `null` observation, read off the counts rather than
        emitted per call — a per-call emission would print the same flaky
        pair's line once for every probe that missed it. Never changes an
        exit code, on `W-ENV-UNLOCKED`'s existing precedent.

        `declared` narrows exactly as `unobserved` does, on Decision 8's own
        opening clause ("a **declared** fact that came back `null`") and
        Decision 4's fourth row: an undeclared fact's `null` is recorded (in
        `facts_document`) but warns about nothing, because the warning is
        what a DECLARATION buys — a probe returning an extra, undeclared
        diagnostic that happens to come back empty is not a disagreement
        between the plugin and the template the way a missed declared fact
        is."""
        for condition in self._conditions:
            for fact in self._facts_by_condition[condition]:
                if fact not in declared:
                    continue
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


def check_changed(
    observations: Observations, condition_key_value: str, facts: Mapping[str, Any]
) -> None:
    """The gate's caller-facing helper (Decision 2): calls `Observations.changed`
    and raises `E-APPARATUS-CHANGED` for the first contradicting triple, or
    returns silently.

    **What the message may name, and why it is safe for a `str` fact value.**
    The message names the condition key, the fact name, and both values —
    `condition `00`'s fact `pinned` changed: r1 → r2` — in the shape `diff`'s
    own apparatus row prints. For a `str` fact value this is safe because
    `check_facts` (Part A) refuses a value that equals or contains a declared
    credential **before** anything is recorded, so by the time
    `Observations.changed` sees a pair of `str` values, core has already
    established that neither is a credential it read. That ordering is
    reused here, not re-derived. **The containment check itself is skipped
    by `check_facts` for any non-`str` value** (its own deliberate carve-out),
    so a non-`str` fact equal to a declared credential's value is not caught
    there; there is no call site yet, and the wired diagnostic's redacting
    `Collector` (Decision 14) is the mitigation for that residual — worth
    naming for whoever wires the diagnostic, not a claim this function makes
    good on itself.

    Task 4 wires this into `Observer._observe_one`, after
    `Observations.record`, on the order Decision 3 fixes — a raise here still
    reaches `command_run`'s containment as an ordinary `ContractError` until
    task 5 gives `execute_plan`'s loop a `break` to catch it on. This
    function still has its own direct-call surface (`test_apparatus.py`), the
    same way `check_facts` and `observe_once` are exercised directly as well
    as through `Observer`.
    """
    result = observations.changed(condition_key_value, facts)
    if result is None:
        return
    fact, first, incoming = result
    raise ContractError(
        f"condition `{condition_key_value}`'s fact `{fact}` changed: {first} → {incoming}",
        code="E-APPARATUS-CHANGED",
    )


def condition_key(index: int, label: str | None) -> str:
    """The key `probes.jsonl` and `provenance.apparatus.facts` both use for one
    condition — the `<nn>_<label>` form `sweep.condition_dir_name` renders,
    imported rather than formatted a second time (§ Corrections against the
    code, correction 2). A run declaring no `sweep` has one condition whose
    label is `None`; canonical JSON cannot sort a `null` key beside `str` keys
    under `sort_keys=True`, so that case is `f"{index:02d}"` — the same scheme
    with an empty body — rather than the string `"None"` or a literal `null`.

    **The import itself is not behaviourally pinnable.** `condition_dir_name`
    is exactly `f"{index:02d}_{label}"` with no sanitisation, so a mutation
    that inlined that f-string here instead of calling the import would
    produce an identical result for every input — two branches that cannot
    differ. What a test *can* pin is the labelled branch's output value
    (`condition_key(0, "baseline") == "00_baseline"`, which would catch a
    build that emitted the bare label — Decision 9's reading before
    correction 2 overrode it) and the no-sweep branch's value and sort
    behaviour under canonical JSON. The import is kept because it is the one
    documented source of truth for this string, not because any test proves
    calling it rather than re-deriving it.
    """
    if label is None:
        return f"{index:02d}"
    return condition_dir_name(index, label)


def append_observation(
    run_dir: Path, *, phase: str, condition: str, probe: str, facts: Mapping[str, Any]
) -> None:
    """Append one line to the append-only ledger `apparatus/probes.jsonl`.

    Exactly § The apparatus files' five keys — `at`, `phase`, `condition`,
    `probe`, `facts` — nulls and undeclared facts included, one line per
    probe call, written at the call rather than after the execution it
    precedes: an execution that raises still gets its result appended and the
    run continues (`runner.execute_plan`'s `except Exception` comment, "a
    failed execution never stops the run") — the run also stops early when
    `max_failed_fraction` is exceeded, which an after-the-execution append
    would still have recorded correctly, so the qualification does not change
    the ordering argument. What after-the-execution WOULD lose is the
    observation for a run that dies *inside* the execution itself, or between
    executions, before any later append runs — which is the run this ledger
    exists for. `condition` is the `<nn>_<label>` key from `condition_key`,
    never the bare label.

    `phase` is one of a closed vocabulary of four: `run_start`, `pre_execution`,
    `dry_run`, `freeze`. Part A only ever calls this with the first two; the
    other two are named here so H8's and H9's callers do not mint a fifth
    spelling of a phase this module already has a name for.

    This function writes `facts` verbatim, with no check of its own —
    `Observer._observe_one` is what rules the order against `check_facts`.
    """
    ledger_dir = run_dir / "apparatus"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    line = {
        "at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "phase": phase,
        "condition": condition,
        "probe": probe,
        "facts": dict(facts),
    }
    with (ledger_dir / "probes.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(line) + "\n")


APPARATUS_CODES: frozenset[str] = frozenset(
    {
        "E-APPARATUS-RAISED",
        "E-APPARATUS-RETURN",
        "E-APPARATUS-FACT-TYPE",
        "E-APPARATUS-FACT-MISSING",
        "E-APPARATUS-FACT-CREDENTIAL",
    }
)
"""The five codes `check_facts` and `observe_once` raise, and the exact filter
`cli.command_run`'s run-start/`execute_plan` wrapper uses (task 9). Deliberately
narrow: `E-PROBE-UNKNOWN`, `E-PLUGIN-LOAD` and `E-PLUGIN-DECORATOR` are dispatch
codes `apparatus._probe_for` raises, not codes a probe CALL raises, and none of
the three belongs in this set. `E-PROBE-UNKNOWN` is pre-answered by
`validate._check_probe` from the same metadata scan `_probe_for` reads, before
`command_run` ever reaches the lock. `E-PLUGIN-LOAD` and `E-PLUGIN-DECORATOR`
are NOT pre-answered by `validate` — `validate._check_probe` never calls
`EntryPoint.load()`, so a plugin whose top level raises is caught by
`command_run`'s own dispatch-time wrapper around `_probe_for` (the roster
wrapper's shape, redacting before `main` ever sees it), sited before this
filter's `try` is even entered — not by admitting the two codes here."""


STOP_CODES: frozenset[str] = frozenset(
    {
        "E-APPARATUS-RAISED",
        "E-APPARATUS-CHANGED",
    }
)
"""The two codes `execute_plan`'s loop breaks on (task 5). At this commit the
only pin is one shared set-equality assertion over both members (each
member's absence is independently checked by deleting it and rerunning that
one test), because Fixture U and Fixture G1 — the run-level pins each code
eventually earns on its own — are owed by tasks 5 and 7 and do not exist
here.

**`E-APPARATUS-CHANGED` is deliberately NOT a member of `APPARATUS_CODES`.**
That frozenset is `command_run`'s containment filter for a probe CALL
crossing the run-start round or the `execute_plan` boundary; after task 5 a
changed fact never reaches that filter at all, because the loop this
constant names breaks on it first. Admitting it to `APPARATUS_CODES` would
add a member nothing exercises through that filter — an unpinned addition to
an enumeration this project has already been burned by once. This is not a
claim that a changed fact **cannot** reach a run-start call: task 13 is where
that claim is made to happen, by fixture, and a comment asserting it here
without that fixture is the shape that produced Part A's only Critical."""


class Observer:
    """One object per `run`, holding everything `observe_round` needs to make
    a probe call phase-independent: which callable to call, under which cfg,
    keyed by which condition, written where, and against which credentials.

    `reference.md` § The apparatus core can only observe: an experiment
    declaring no `apparatus_probe` records nothing, so `command_run` never
    constructs one in that case — `observer` is `None` and every call site
    (task 9's run-start round, task 10's per-execution round) is guarded on
    that, not on some property of this class.

    **Ruling on the ordering `spec-defects.md` left open, since this class is
    the first caller of both `check_facts` and `append_observation`:**
    `check_facts` runs BEFORE `append_observation`, every time. A probe
    returning a value equal to a declared credential is refused by
    `check_facts` before a single byte reaches `apparatus/probes.jsonl` — the
    reverse order would put a credential-carrying fact on disk while
    satisfying every ordering the design states, which is precisely the leak
    Decision 6 exists to prevent. This closes the OPEN filing naming H7d batch
    3 as owner; `Observer._observe_one`, this class's own per-condition
    probe-and-append step, is where the order is fixed.
    """

    def __init__(
        self,
        *,
        probe_name: str,
        probe: Callable[..., Any],
        declared_facts: Sequence[str],
        conditions: Sequence[Any],
        cfgs: Mapping[int, Any],
        run_dir: Path,
        credentials: Mapping[str, str],
    ) -> None:
        self.probe_name = probe_name
        self.probe = probe
        self.declared_facts = list(declared_facts)
        self.conditions = list(conditions)
        self.cfgs = cfgs
        self.run_dir = run_dir
        self.credentials = credentials
        self.observations = Observations()

    def observe_round(self, *, phase: str, condition_index: int | None) -> None:
        """The phase-independent entry point every caller uses (Decision 2,
        Decision 3). Given `condition_index=None` — the run-start round (task
        9) and a condition-less execution (task 10) — this makes one call PER
        RESOLVED CONDITION, each under that condition's own cfg, never the
        wide one (`self.cfgs[-1]` is never read here). Given an index, one
        call, under that condition's cfg.
        """
        if condition_index is None:
            targets = self.conditions
        else:
            targets = [c for c in self.conditions if c.index == condition_index]
        for condition in targets:
            self._observe_one(phase, condition)

    def _observe_one(self, phase: str, condition: Any) -> None:
        """Task 4 (Decision 3): the order inside one probe round is fixed and
        every step of it is load-bearing — `check_facts` (a credential-carrying
        fact is refused before a byte reaches the ledger), then
        `append_observation` (the moving observation is on disk before
        anything can stop the run — the earlier-period-plus-ledger guarantee
        § The apparatus files and § The apparatus core can only observe both
        state), then `Observations.record` (the moving call is counted in
        `unobserved.total_probes` like any other probe — a census of calls,
        not of agreements), and only then the gate. Nothing else in this
        method moves. The gate raises here; task 5 is what turns the raise
        into a stop rather than letting it escape."""
        cfg = self.cfgs[condition.index]
        returned = observe_once(self.probe, cfg, probe_name=self.probe_name)
        facts = check_facts(
            returned,
            self.declared_facts,
            probe_name=self.probe_name,
            credentials=self.credentials,
        )
        key = condition_key(condition.index, condition.label)
        append_observation(
            self.run_dir,
            phase=phase,
            condition=key,
            probe=self.probe_name,
            facts=facts,
        )
        self.observations.record(key, facts)
        check_changed(self.observations, key, facts)

    def warn_unanswered(self, c: Collector) -> None:
        """`W-APPARATUS-UNANSWERED`, delegated to `Observations` — this
        object's only job here is supplying the declared-facts narrowing
        (Decision 8) so a caller need not carry it separately."""
        self.observations.warn_unanswered(c, self.declared_facts)

    def block(self) -> dict[str, Any]:
        """`provenance.apparatus`'s five sub-keys, exactly `reference.md` §
        The apparatus core can only observe's fenced example: `probe`, `ledger`,
        `hash`, `facts`, `unobserved` — assembled from `Observations`'s two
        projections rather than re-deriving either. `command_run` calls this
        only when `observer is not None`; a template declaring no probe never
        constructs an `Observer` at all, so the whole block is `None` there
        (Decision 7) rather than this method being asked to return one."""
        facts = self.observations.facts_document()
        return {
            "probe": self.probe_name,
            "ledger": "apparatus/probes.jsonl",
            "hash": apparatus_hash(facts),
            "facts": facts,
            "unobserved": self.observations.unobserved(self.declared_facts),
        }


def apparatus_hash(facts_document: Mapping[str, Any]) -> str:
    """`provenance.apparatus.hash` (Decision 10): sha256 over canonical JSON
    (`sort_keys=True`, `separators=(",", ":")`, `ensure_ascii=False`) of the
    resolved condition → facts mapping alone — never the ledger, the probe
    name, phases, timestamps or `unobserved`. This is **not a fourth hash** in
    `CLAUDE.md`'s sense: it sits beside `uv_lock_hash` as an environment
    fingerprint core compares (a lockfile mismatch is one, a moved apparatus
    is another), not among the three identity claims `HASHED_TREES` and
    `parameters_hash`/`input_manifest_hash` make provable. That is why this
    function lives here, beside the builder of the mapping it hashes —
    `manifest_hash` beside `build_manifest` in `manifest.py`, `allocation_hash`
    beside `build_allocation_document` in `artifacts.py` are the shipped
    precedent — and not in `hashes.py`.

    **The hash is over the mapping, not over any file's bytes.** `run.yaml`
    renders this same mapping through `yaml.safe_dump` and the ledger renders
    individual observations through `json.dumps`; neither encoding reproduces
    this digest. A reader checking it must re-canonicalize the *parsed*
    `facts` mapping with the exact `json.dumps` arguments this function uses,
    not hash either file's rendered text.
    """
    canonical = json.dumps(
        facts_document, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
