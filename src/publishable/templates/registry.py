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

from publishable.templates.base import BaseTemplate
from publishable.templates.builtin.generic import GenericTemplate
from publishable.templates.discovery import PartialLoadError, discover_local

_BUILTIN: dict[str, type[BaseTemplate]] = {"generic": GenericTemplate}


def _merged(repo_root: Path | None) -> dict[str, type[BaseTemplate]]:
    if repo_root is None:
        return dict(_BUILTIN)
    local = discover_local(repo_root)
    for name in sorted(local):  # name order: import order may decide nothing here
        if name in _BUILTIN:
            core = _BUILTIN[name]
            raise PartialLoadError(
                f"the project-local template `{local[name].provider}` claims the name "
                f"`{name}`, which core itself registers as "
                f"{core.__module__}.{core.__qualname__} — a local template that could "
                "redefine a core name could change what a config means without "
                "changing the config, which is what `parameters_hash` exists to make "
                "impossible. Rename yours.",
                code="E-TEMPLATE-COLLISION",
                partial_templates=[found.cls for found in local.values()],
            )
    return {name: found.cls for name, found in local.items()} | _BUILTIN


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
    """
    merged = _merged(repo_root)
    cls = merged.get(name)
    return (cls() if cls else None), sorted(merged)


def template_names(repo_root: Path | None = None) -> list[str]:
    return sorted(_merged(repo_root))


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
