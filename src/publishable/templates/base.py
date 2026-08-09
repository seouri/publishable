"""An experiment type's parameters. See docs/reference.md § Templates."""

from typing import Any

from publishable.param import Param


class BaseTemplate:
    naming_pattern: str = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    field_convention: str = "generic"
    default_repeats: int = 1
    required_env: list[str] = []
    apparatus_probe: str | None = None
    apparatus_facts: list[str] = []
    parameter_spec: dict[str, Param] = {}

    def validate(self, config: Any) -> list[str]:
        """Cross-field rules. Receives the WHOLE config; [] when OK."""
        return []
