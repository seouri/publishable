"""An experiment type's parameters. See docs/reference.md § Templates."""

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from publishable.param import Param

if TYPE_CHECKING:
    from publishable.stats import UnitTable


class BaseTemplate:
    naming_pattern: str = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    field_convention: str = "generic"
    default_repeats: int = 1
    required_env: list[str] = []
    apparatus_probe: str | None = None
    apparatus_facts: list[str] = []
    parameter_spec: dict[str, Param] = {}
    # What this template reports as its own spec version, which a config's
    # `template_version` is compared against. `None` for a template that tracks
    # no version — the base's answer, and the right one for a project-local file,
    # whose version is a string its author remembers to bump rather than a fact
    # core can check.
    version: str | None = None

    def validate(self, config: Mapping[str, Any]) -> list[str]:
        """Cross-field rules. Receives the WHOLE config; [] when OK.

        **A mapping — the parsed document — and deliberately not the dot-access
        node `aggregate`'s `cfg` is.** This method reads *declarations*, where an
        absent optional block is the answer; `aggregate` reads a condition's
        *resolved* values, where a path that misses is a typo and a node refusing
        it is right. Five of the paths a cross-block rule asks about
        (`statistics.contrasts`, `.report_by`, `.resample`, `.null_test`, a
        `sweep` mode) are absent from what `init` writes, so a reader that raised
        on an absence could not answer the question this method exists for —
        `reference.md` § Templates has the idiom and the worked rule.
        """
        return []

    def aggregate(self, units: "UnitTable", cfg: Any) -> dict[str, Any]:
        """Derive metrics from the unit table; `{}` when there is nothing to derive.

        Core calls this once per recording step, and a pipeline can have several,
        so returning `{}` for a table this template does not recognize is the
        right answer rather than an error. `cfg` is this condition's resolved
        parameters — the same object a step receives — which is what lets one
        `aggregate` compute pearson under one condition and kendall under another.

        The return is what a step may return: a flat mapping of scalars under the
        same coercion. There is no `Estimate` exception here, unlike a `summary`
        step's return, because a derived metric is one core computes and resamples
        itself rather than one the user asserts.
        """
        return {}
