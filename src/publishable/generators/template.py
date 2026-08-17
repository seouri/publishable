"""`generate template` — a project-local template stub. Greenfield only."""

from pathlib import Path

from publishable.errors import ContractError

# The stub emits `parameter_spec`, `validate`, `aggregate`, `naming_pattern` and
# `default_repeats`, and none of the rest. `required_env` has a reader
# (`validate` checks it), but a stub declaring `[]` would only ever satisfy that
# check trivially and would still teach its reader to set a field this generated
# file has no other use for. `version` is omitted for a sharper reason: a
# project-local template is never version-checked at all, so a version in this
# file would be a string nothing reads. `field_convention` and `apparatus_facts`
# are declared on the base class and read by nothing in this build;
# `apparatus_probe` is read (`validate` checks it against the installed probes)
# but a stub declaring `None` would only ever satisfy that check trivially.
# `docs/reference.md` § Templates: where parameters are defined
# shows the whole set, because that example is core's own `generic` rather than
# a file you are about to edit.
#
# Everything the stub imports comes from `publishable` itself — the one import
# root; `publishable.templates` and every other submodule are implementation
# detail.
TEMPLATE_PY = '''\
# templates/{name}.py — a template only this project needs, discovered by path
from publishable import BaseTemplate, Param, register_template


@register_template("{name}")
class {cls}(BaseTemplate):
    # One spec drives all three jobs: what `init` writes, what its inline
    # comments say, and what `validate` enforces. There is no second source of
    # truth, so adding a parameter here is the whole of adding a parameter.
    parameter_spec = {{
        "{name}.threshold": Param(
            float, default=0.5, gt=0, lt=1,
            help="TODO: replace with this experiment type's own parameters",
        ),
    }}

    naming_pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"    # what an experiment name must match
    default_repeats = 1

    def validate(self, config) -> list[str]:
        """Cross-field rules over the WHOLE config; `[]` when there is nothing
        to say. This is where a rule core cannot know goes — a pipeline that
        fits a model rejecting a config with no `holdout` and no `fold`, say."""
        return []

    def aggregate(self, units, cfg) -> dict:
        """Derive condition-level metrics from the per-unit table; `{{}}` when
        there is nothing to derive. Core calls this once per recording step, and
        on each resampled table, which is what gives a derived metric a real
        interval. `units` supports iteration, `units.<column>`, `len` and
        `units.columns` — and nothing else."""
        return {{}}
'''


def class_name(name: str) -> str:
    """`my_assay` → `MyAssayTemplate`. The class is read by people, not by core:
    the `@register_template` argument is the whole of a local registration."""
    return "".join(part.capitalize() for part in name.split("_")) + "Template"


def is_usable_name(name: str) -> bool:
    """Whether `templates/<name>.py` is a file discovery would actually read.

    An identifier because the file must be importable as a sibling helper is,
    and because a name carrying a path separator would write outside
    `templates/` altogether. Not `__`-prefixed because `discover_local` skips
    those by the same convention `__init__.py` uses — a generator that wrote
    one would write a file that never registers.
    """
    return name.isidentifier() and not name.startswith("__")


def generate_template(*, repo_root: Path, name: str) -> Path:
    """Write `templates/<name>.py`, refusing an existing one.

    Greenfield, like every other generator: the file is code the run's numbers
    come out of — `code_hash` covers `templates/**` — so replacing one a
    project already edited is the one thing this must never do.
    """
    templates_dir = repo_root / "templates"
    path = templates_dir / f"{name}.py"
    if path.exists():
        raise ContractError(
            f"templates/{name}.py already exists — `generate template` never "
            "modifies an existing template",
            code="E-TEMPLATE-EXISTS",
        )
    templates_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(TEMPLATE_PY.format(name=name, cls=class_name(name)))
    return path
