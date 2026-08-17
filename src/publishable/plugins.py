"""Entry-point discovery for the registries a plugin declares.

docs/reference.md § Creating a plugin. Every name a config can write for a
plugin artifact resolves through this module, and it resolves from **package
metadata**: nothing here calls `EntryPoint.load()`, and nothing that calls this
module may either. That is not a performance choice. § Creating a plugin
justifies the whole entry-point mechanism by `validate` being able to answer
"no installed package registers `plate_wells`" without importing a line of that
package, and `validate` is documented as creating nothing and reaching nothing
off the machine. A check that reaches for the object behind a name has changed
the guarantee whatever it returns.

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

from importlib.metadata import EntryPoint, entry_points

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
