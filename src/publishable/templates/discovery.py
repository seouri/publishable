"""`register_template` and the pending-registration buffer it fills.

A local template's `@register_template` argument is the whole of its
registration — the decorator records `(name, cls)` and returns the class
unchanged, so `class X(BaseTemplate)` still resolves for every later
reference to `X`.

The pending list is module-level, but it is only a staging buffer: task 6's
requirement is that two projects in one process never see each other's
templates, so nothing here keeps a persistent name→class mapping. Discovery
drains this list into whatever scoped registry it builds per run.
"""

from collections.abc import Callable

from publishable.templates.base import BaseTemplate

_pending: list[tuple[str, type[BaseTemplate]]] = []


def register_template(
    name: str,
) -> Callable[[type[BaseTemplate]], type[BaseTemplate]]:
    """Record `(name, cls)` for the next `drain_pending()` and return `cls` unchanged."""

    def decorator(cls: type[BaseTemplate]) -> type[BaseTemplate]:
        _pending.append((name, cls))
        return cls

    return decorator


def drain_pending() -> list[tuple[str, type[BaseTemplate]]]:
    """Hand over the accumulated registrations and empty the buffer."""
    pending = list(_pending)
    _pending.clear()
    return pending
