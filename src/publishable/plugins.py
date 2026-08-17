"""Entry-point discovery for the registries a plugin declares.

docs/reference.md § Creating a plugin. Every name a config can write for a
plugin artifact resolves through this module, and *resolving a name* —
`scan_group`, `names`, `check_registration`, and every lookup `validate` makes
— answers from **package metadata** and imports nothing. That is not a
performance choice. § Creating a plugin justifies the whole entry-point
mechanism by `validate` being able to answer "no installed package registers
`plate_wells`" without importing a line of that package, and `validate` is
documented as creating nothing and reaching nothing off the machine. A check
that reaches for the object behind a name has changed the guarantee whatever
it returns — which is exactly what `validate` never does.

Loading the object behind a name is a separate, named operation —
`load_entry_point`, the one function in this module that calls
`EntryPoint.load()` — reached only once a name has resolved and the object is
actually needed. That is what keeps the guarantee above intact where it is
claimed: a *negative* answer costs nothing, because deciding that no installed
package registers `plate_wells` never reaches the package. A caller that does
need the object pays the import, and `validate` is such a caller for exactly one
declaration, `data.units.from.resolver`, whose resolver `reference.md` § Where
units come from puts at `validate` and `dry-run` rather than only at `run`.

The cost of that, stated rather than discovered: a claim read from metadata is a
name and a provider and nothing else. A refusal computed from it therefore has
no class to interrogate — no `parameter_spec`, no `required_env` — which is why
a plugin-side collision cannot redact a credential the way a project-local one
can. See `templates/registry.py` and § Creating a plugin for that residual.

Templates are scanned through here like everything else, but they are *merged*
in `templates/registry.py`, because a template name has a second home — a
project's own `templates/` — and the merge is the one place holding all three
sources at once.
"""

from collections.abc import Callable, Sequence
from importlib.metadata import EntryPoint, entry_points
from typing import Any, TypeVar

from publishable.artifacts import CORE_SUFFIXES, READERS, WRITERS
from publishable.errors import ContractError
from publishable.templates.discovery import PartialLoadError, drain_pending

F = TypeVar("F", bound=Callable[..., Any])

GROUPS = (
    "publishable.templates",
    "publishable.resolvers",
    "publishable.probes",
    "publishable.writers",
    "publishable.readers",
)
"""Every entry-point group core reads, one per registry § Creating a plugin declares."""


def provider_of(ep: EntryPoint) -> str:
    """What a reader uninstalls or pins, which is a distribution rather than a module.

    Falls back to the entry point's own target only when `entry_points()` handed
    back an unattached object, which its own construction does not produce — kept
    so a message can never interpolate `None`.
    """
    dist = ep.dist
    if dist is None:  # pragma: no cover - entry_points() always attaches one
        return ep.value
    return f"{dist.name} {dist.version}"


def scan_group(group: str) -> dict[str, list[EntryPoint]]:
    """Every claim on every key in `group`, keyed by the key a config writes.

    A list per key rather than a single entry point, because two installed
    distributions claiming one key is a fault to *report* — naming both — rather
    than one to resolve by whichever the scan walked first. Keys come back in
    name order and claimants in provider order for the same reason: install order
    is a property of a machine, so it may not decide what a message says either.
    """
    found: dict[str, list[EntryPoint]] = {}
    for ep in entry_points(group=group):
        found.setdefault(ep.name, []).append(ep)
    return {name: sorted(found[name], key=provider_of) for name in sorted(found)}


def names(group: str) -> list[str]:
    """The keys `group` registers, in name order."""
    return list(scan_group(group))


RESOLVERS: dict[str, Callable[..., Any]] = {}
"""Every resolver a plugin module registered, by the name a config writes.

Module-global because a decorator runs when a plugin is imported and has nowhere
else to put what it recorded. That is the opposite arrangement from
`templates/registry.py`'s per-call merge, and for a reason that does not apply
here: two projects resolved in one process must never see each other's
`templates/`, but an installed distribution is the same distribution for both.
"""

PROBES: dict[str, Callable[..., Any]] = {}
"""Every apparatus probe a plugin module registered. See `RESOLVERS`."""


def register_resolver(name: str) -> Callable[[F], F]:
    """Record `name -> fn` for this process and return `fn` unchanged.

    The entry point is the registration and this argument is a declaration
    checked against it — `reference.md` § Creating a plugin — so this records
    what the source says. Returned unchanged so the plugin's own module keeps
    a callable under the name it just defined, which is what makes the
    artifact testable in its own suite.
    """

    def decorator(fn: F) -> F:
        RESOLVERS[name] = fn
        return fn

    return decorator


def register_probe(name: str) -> Callable[[F], F]:
    """Record `name -> fn` for this process and return `fn` unchanged. See
    `register_resolver` for why the mapping is module-global and why the object
    comes back untouched."""

    def decorator(fn: F) -> F:
        PROBES[name] = fn
        return fn

    return decorator


def register_writer(suffix: str) -> Callable[[F], F]:
    """Record a writer for `suffix` in the table `io.write` dispatches through.

    One table rather than a registry of its own: `io.write` finds a writer with
    `_suffix_for`, which iterates `artifacts.WRITERS`, and a second mapping would
    be a second answer to "what suffix does core know".

    A suffix core itself writes is refused here rather than resolved by import
    order — `reference.md` § Creating a plugin — because a plugin that could
    redefine `.csv` could change what an artifact means without changing the step
    that wrote it. Two *plugins* claiming one suffix is the other half of the same
    rule and is decided from entry-point metadata by `validate`, since core's own
    table appears in nobody's metadata and an installed pair appears in no table.
    """

    def decorator(fn: F) -> F:
        if suffix in CORE_SUFFIXES:
            raise ContractError(
                f"a writer claims `{suffix}`, which core itself writes — a plugin that "
                "could redefine a core suffix could change what an artifact means "
                "without changing the step that wrote it. Claim a suffix of your own",
                code="E-PLUGIN-COLLISION",
            )
        WRITERS[suffix] = fn
        return fn

    return decorator


def register_reader(suffix: str) -> Callable[[F], F]:
    """Record a reader for `suffix`, the inverse `io.read_upstream` dispatches to.

    Refuses a core suffix for the reason `register_writer` does, and under the
    same code: the pair is one claim on one extension, so redefining half of it
    is redefining it. The check is `suffix in CORE_SUFFIXES`, i.e. `WRITERS`'s
    keys at import time — a proxy for "core itself reads `suffix`" rather than
    a read of `artifacts.READERS` directly, correct only because core's own
    writer and reader tables in `artifacts.py` are defined with identical keys.
    """

    def decorator(fn: F) -> F:
        if suffix in CORE_SUFFIXES:
            raise ContractError(
                f"a reader claims `{suffix}`, which core itself reads — a plugin that "
                "could redefine a core suffix could change what an artifact means "
                "without changing the step that wrote it. Claim a suffix of your own",
                code="E-PLUGIN-COLLISION",
            )
        READERS[suffix] = fn
        return fn

    return decorator


def _registry_for(group: str) -> dict[str, Callable[..., Any]] | None:
    """The mapping a group's decorator fills, or `None` for a group whose
    registration is not a name-to-object mapping.

    Templates are the `None` case: `register_template` records into a pending
    buffer a discovery pass drains, so what a template class declared is known to
    whoever drained it and not to this module.
    """
    registries: dict[str, dict[str, Callable[..., Any]]] = {
        "publishable.resolvers": RESOLVERS,
        "publishable.probes": PROBES,
        "publishable.writers": WRITERS,
        "publishable.readers": READERS,
    }
    return registries.get(group)


def declared_names(group: str, obj: object) -> list[str]:
    """Every name `obj` is registered under in `group`'s mapping, in name order.

    A list rather than one name because one function may serve two keys — a
    plugin keeping an old resolver name alongside a new one registers twice — and
    that is not a disagreement.
    """
    registry = _registry_for(group)
    if registry is None:
        return []
    return sorted(name for name, registered in registry.items() if registered is obj)


def check_registration(ep: EntryPoint, declared: Sequence[str]) -> None:
    """The `@register_*` argument against the entry-point key that named it.

    `reference.md` § Creating a plugin: the entry point is the registration and
    the decorator is a declaration checked against it. Two spellings of one name
    with no rule for which is canonical is a drift nobody detects until a config
    names the loser, so loading fails naming both rather than letting one
    silently win.

    Takes the declared names rather than computing them, so one comparison serves
    every group: a template's registration lands in a pending buffer its
    discovery pass drains, and a reverse lookup here would depend on whether
    anything had drained it yet.

    Meant to run once an object behind a key has actually been loaded, wherever
    that happens — including `validate`, which loads a resolver.
    """
    if ep.name in declared:
        return
    if declared:
        detail = f"declares `{'`, `'.join(declared)}` instead"
    else:
        detail = "calls no `@register_*` naming it"
    raise ContractError(
        f"the entry point `{ep.name}` in `{ep.group}` points at `{ep.value}`, which "
        f"{detail} — the entry point is the registration and the decorator is a "
        "declaration checked against it, so two spellings of one name are refused "
        "rather than resolved. Make them agree",
        code="E-PLUGIN-DECORATOR",
    )


def load_entry_point(ep: EntryPoint) -> Any:
    """Import what `ep` points at, containing every way a plugin's top level can fail.

    **The one function in this module that imports anything.** Everything else
    answers from package metadata, which is the guarantee § Creating a plugin
    justifies the whole mechanism by; this is what a command calls once it has
    resolved a name and actually needs the object.

    `SystemExit` gets its own arm because it is a `BaseException` and the broad
    one below does not see it: a plugin calling `sys.exit()` at module scope, or
    building an `argparse` parser at import, would otherwise end the command with
    the plugin's own exit code and no diagnostic at all.

    Whatever the failed import left in the pending registration buffer is drained
    onto the refusal rather than discarded. A class body finishes running before
    its own `@register_*` call is reached, so a module that raises after
    registering still leaves a fully formed class — and a caller that never gets
    a usable object can still ask that class what credentials it declares. It is
    drained rather than kept for the next load either way: a registration this
    import made is not the next one's to inherit.

    Drained before the import too, on `discover_local`'s precedent and for its
    exact reason: a module-scope `@register_template` queued by something else
    entirely — `cli` imports the experiment package before `validate_config`
    runs — is not this call's to inherit and misattribute onto its own refusal.
    Drained again on the success return, for the same reason in the other
    direction: what this import just registered is not the *next* load's to
    inherit either, and the object `ep.load()` handed back is already this
    call's own answer.

    The distribution is named rather than the module, because a distribution is
    what a reader uninstalls or pins.
    """
    drain_pending()  # discard anything queued before this call — not ours to attribute
    try:
        result = ep.load()
    except SystemExit as exc:
        raise PartialLoadError(
            f"the entry point `{ep.name}` in `{ep.group}`, from {provider_of(ep)}, called "
            f"`sys.exit()` while importing and registers nothing usable: SystemExit: {exc.code}",
            code="E-PLUGIN-LOAD",
            partial_templates=[cls for _, cls in drain_pending()],
        ) from exc
    except Exception as exc:
        raise PartialLoadError(
            f"the entry point `{ep.name}` in `{ep.group}`, from {provider_of(ep)}, raised "
            f"while importing and registers nothing usable: {exc!r}",
            code="E-PLUGIN-LOAD",
            partial_templates=[cls for _, cls in drain_pending()],
        ) from exc
    drain_pending()  # discard whatever this import registered — not the next load's to inherit
    return result
