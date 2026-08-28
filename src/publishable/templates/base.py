"""An experiment type's parameters. See docs/reference.md § Templates."""

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from publishable.errors import ContractError
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

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Check a subclass's own `parameter_spec` keys the moment the class body
        that declared them finishes — before `@register_template` ever runs.

        Every path in `parameter_spec` nests one level — `head.leaf`, exactly
        two dotted segments — because `materialize._parameters_block` renders
        the spec as one level of YAML nesting. A `Param` itself has no way to
        check this: the path is the *caller's* dict key, never anything passed
        to `Param.__init__`, which is why this check cannot sit inside `Param`
        beside its own (`default=None` without `nullable=True`) even though it
        enforces a rule of the same shape and kind — a malformed declaration
        rejected when the template loads, `reference.md` § Templates says of
        that one, and this is the same moment for a `dict`-shaped fault
        `Param` cannot see.

        `__init_subclass__` runs at class-*definition* time, not at
        `claim.cls()` — the earliest possible point, and the only one that
        also covers `list-templates`: `docs.template_details` reads a listed
        class's `parameter_spec` straight off the class (`claim.cls`) and
        never constructs an instance, so a check living only in `__init__`
        would leave that surface silent. Every command that resolves a
        template — `validate`, `generate experiment`, `list-templates`,
        `freeze`, `report`, `reproduce`, `demo` — imports the module that
        defines the class before it does anything else with it, so checking
        here is checking at every one of those, from one site. For a
        project-local `templates/*.py`, this raise happens before that file's
        own `@register_template` call is ever reached, the same place a raise
        from anywhere else in the class body already leaves no class behind to
        register — `discover_local` folds it into `E-TEMPLATE-LOAD`'s "raises
        while importing" shape exactly as it already does for `Param`'s own
        `default=None`/`requires_env` raises, and the code minted here still
        travels inside `{exc!r}`, unlike theirs. `docs/reference.md` §
        Templates states the constraint; § Errors `validate` reports carries
        the row.

        **Only checks a class-attribute `parameter_spec`** — the shape every
        template `reference.md` shows, and the only shape `cls.parameter_spec`
        can see here. A template that instead assigns `self.parameter_spec`
        inside its own `__init__` builds the dict after this method has
        already run, so a malformed path there still reaches
        `materialize._parameters_block`'s own `ValueError` guard the old way;
        that guard is kept in place for exactly this residual.
        """
        super().__init_subclass__(**kwargs)
        # A non-`dict` `parameter_spec` is a different fault (`validate.py`'s own
        # comment on the same question: "not this collector's crash to cause") —
        # left for whatever reads `.items()` off it to report, rather than
        # iterated here, where a string would be walked character by character
        # and every character would fail this exact check for the wrong reason.
        if not isinstance(cls.parameter_spec, dict):
            return
        for path in cls.parameter_spec:
            if path.count(".") != 1:
                raise ContractError(
                    f"E-TEMPLATE-PARAM-PATH: `parameter_spec` path {path!r} is not "
                    "`head.leaf` — a path is exactly two dotted segments, one to "
                    "nest under and one leaf name. Rename it: a template that "
                    'declared `"reference_frame"` fixed this by renaming it to '
                    '`"frame.reference"`.',
                    code="E-TEMPLATE-PARAM-PATH",
                )

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
