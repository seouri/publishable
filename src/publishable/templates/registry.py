"""Name → template. S1 knows only core's own; a local template arrives here
once a repo root is given.

The merged mapping is built fresh on every call — never cached module-globally
— because two projects resolved in one process must never see each other's
`templates/`.

A local name core already registers is refused here rather than resolved by a
merge order: `reference.md` § Creating a plugin requires a shadow of a core
name to fail at load, naming both providers, because "a plugin that could
redefine `generic` could change what a config means without changing the
config". This is the merge, so it is the first place that holds both sides —
and `discovery.py` cannot hold them, `registry` importing it. The refusal is
of the repo rather than of one lookup: every name resolves through `_merged`,
so a `templates/` core cannot merge refuses a config naming some third
template too, and there is no order left for a merge to express.
"""

from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple

from publishable.plugins import provider_of, scan_group
from publishable.templates.base import BaseTemplate
from publishable.templates.builtin.generic import GenericTemplate
from publishable.templates.discovery import PartialLoadError, discover_local

_BUILTIN: dict[str, type[BaseTemplate]] = {"generic": GenericTemplate}


class Claim(NamedTuple):
    """One registration of one template name, and who made it.

    `cls` is `None` for an installed claim, and that is the mechanism rather than
    a gap: an entry point is resolved from package metadata, so core knows the
    name and the distribution without importing a line — see `plugins.py`. The
    consequences are that an installed name is *known* and not *resolvable* in
    this build, and that a refused installed claim carries no class whose
    declarations could be read.
    """

    provenance: str
    provider: str
    cls: type[BaseTemplate] | None


def _claims(repo_root: Path | None) -> dict[str, Claim]:
    """Every claim on every template name, from all three sources, verdict reached.

    The three sources are core's own registry, the installed distributions'
    `publishable.templates` entry points, and — when a repo root is given — that
    repo's `templates/`. Collected in full before any verdict, on
    `discover_local`'s precedent and for its reason: a verdict reached while a
    claim set was still partial is a verdict over the wrong set. Reported in name
    order, and claimants within a name in provider order, because install order
    and import order are properties of a machine rather than of a design.

    Two local registrations of one name never reach here — `discover_local`
    refuses that pair itself, knowing what a repo declares — so this function
    sees at most one local claimant per name.
    """
    claims: dict[str, list[Claim]] = {}
    for name, core in _BUILTIN.items():
        claims.setdefault(name, []).append(
            Claim(provenance="core", provider=f"{core.__module__}.{core.__qualname__}", cls=core)
        )
    for name, entries in scan_group("publishable.templates").items():
        for ep in entries:
            claims.setdefault(name, []).append(
                Claim(provenance="installed", provider=provider_of(ep), cls=None)
            )
    local = discover_local(repo_root) if repo_root is not None else {}
    for name, found in local.items():
        claims.setdefault(name, []).append(
            Claim(provenance="local", provider=found.provider, cls=found.cls)
        )
    for name in sorted(claims):
        if len(claims[name]) > 1:
            who = " and ".join(sorted(claim.provider for claim in claims[name]))
            raise PartialLoadError(
                f"the template name `{name}` is claimed more than once: {who} — a "
                "template that could redefine another's name could change what a "
                "config means without changing the config, which is what "
                "`parameters_hash` exists to make impossible. Install order and "
                "import order are the only tie-breaks available, and both are "
                "properties of a machine rather than of a design. Rename yours.",
                code="E-TEMPLATE-COLLISION",
                partial_templates=[
                    claim.cls
                    for these in claims.values()
                    for claim in these
                    if claim.cls is not None
                ],
            )
    return {name: these[0] for name, these in claims.items()}


def _merged(repo_root: Path | None) -> dict[str, type[BaseTemplate]]:
    """The names this build can hand back a class for: core's and this repo's.

    An installed name is in `_claims` and not here. `template_names` reads
    `_claims`, so the name is known; `get_template` reads this, so it is not
    resolved — see `Claim.cls`.
    """
    return {name: claim.cls for name, claim in _claims(repo_root).items() if claim.cls is not None}


def get_template(name: str, repo_root: Path | None = None) -> BaseTemplate | None:
    cls = _merged(repo_root).get(name)
    return cls() if cls else None


def resolve_template(
    name: str, repo_root: Path | None = None
) -> tuple[BaseTemplate | None, list[str]]:
    """`get_template`, plus the known names, from **one** merge.

    The pair exists because the two callers that report `E-TEMPLATE-UNKNOWN`
    need both halves, and asking for them separately would run local discovery
    twice — which means importing every `templates/*.py` twice, executing every
    user top level twice. `reference.md` § Creating a plugin widens `validate`'s
    import exception from one named module to a whole directory; it does not
    widen it to that directory twice.

    `_claims` is called once per call here, exactly as `_merged` was — asking
    for the two halves separately would import every `templates/*.py` twice.
    """
    claims = _claims(repo_root)
    claim = claims.get(name)
    cls = claim.cls if claim is not None else None
    return (cls() if cls else None), sorted(claims)


def template_names(repo_root: Path | None = None) -> list[str]:
    return sorted(_claims(repo_root))


def template_provenance(name: str, repo_root: Path | None = None) -> str | None:
    """Where the template `name` resolves from — `core`, `local`, `installed` — or
    `None` if nothing claims it.

    Asked at the merge, which is the one place holding all three sources, and
    answered from which source a claim came from rather than from anything
    observable on a class afterward. `discovery.is_local_template` answers a
    narrower question about a class that is already in hand, and keeps its two
    callers: nothing in this build ever holds an installed template's class, so a
    class-taking predicate has no third value to return.
    """
    claim = _claims(repo_root).get(name)
    return claim.provenance if claim is not None else None


def unknown_template_message(name: str, known: Sequence[str]) -> str:
    """The one wording for a name neither `resolve_template` call site resolved —
    `validate`'s finding and `generate_experiment`'s raise both read this
    rather than each keeping its own copy, so the two surfaces cannot drift
    the way two hard-coded literals eventually would.

    Takes the already-resolved names rather than a repo root, so building the
    message costs no second discovery: each caller has just merged, and has
    them in hand.
    """
    return (
        f"names `{name}`, which no template — core's, an installed plugin's, "
        f"or this project's own `templates/` — registers "
        f"(known: {', '.join(known)})"
    )
