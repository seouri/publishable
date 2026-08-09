"""Name → template. S1 knows only core's own; plugins arrive in hardening."""

from publishable.templates.base import BaseTemplate
from publishable.templates.builtin.generic import GenericTemplate

_BUILTIN: dict[str, type[BaseTemplate]] = {"generic": GenericTemplate}


def get_template(name: str) -> BaseTemplate | None:
    cls = _BUILTIN.get(name)
    return cls() if cls else None


def template_names() -> list[str]:
    return sorted(_BUILTIN)
