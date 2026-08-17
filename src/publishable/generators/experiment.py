"""`generate experiment` — always creates, never wraps. Greenfield only."""

import subprocess
from pathlib import Path

from publishable.errors import ContractError
from publishable.materialize import materialize_config
from publishable.provenance import resolves_inside_repo
from publishable.templates.registry import (
    _claims,
    installed_template_message,
    unknown_template_message,
)

STARTER_STEP = """\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        units = list(io.units)
        for unit in units:
            io.record(unit.key, {{"present": True}})
        return {{"n_units": len(units)}}    # TODO: replace with your analysis
"""

EXPERIMENT_PY = """\
# src/{pkg}/experiment.py — order, nothing else
from publishable import BaseExperiment

from .steps.step01_summarize_units import Step as SummarizeUnits

STEPS = [SummarizeUnits]


class {cls}(BaseExperiment):
    # Order, nothing else. Each step declares its own scope; core derives
    # the execution plan from that. Reordering here IS reordering the pipeline.
    steps = STEPS
"""


def package_name(experiment: str) -> str:
    return experiment.replace("-", "_")


def class_name(experiment: str) -> str:
    return "".join(part.capitalize() for part in experiment.split("-")) + "Experiment"


def uv_add(repo_root: Path, requirement: str) -> None:
    """`uv add <requirement>` in the project, and nothing more.

    `reference.md` § Plugins: no registry, no bespoke installer, no new trust
    boundary beyond "this is a git dependency," because it is one. The install
    is what makes the plugin a normal `pyproject.toml` line and a pinned
    `uv.lock` entry, which is what gives `reproduce` the exact version free.
    """
    result = subprocess.run(
        ["uv", "add", requirement], cwd=repo_root, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise ContractError(
            f"`uv add {requirement}` failed: {result.stderr.strip() or result.stdout.strip()}",
            code="E-UV-ADD",
        )


def plugin_requirement(spec: str) -> str:
    """`<user>/<repo>` or `<user>/<repo>@<ref>` to what `uv add` takes."""
    return f"git+https://github.com/{spec}"


def generate_experiment(
    *,
    repo_root: Path,
    name: str,
    template_name: str,
    input_dir: str,
    output_dir: str,
    plugin: str | None = None,
) -> Path:
    # Installed first, and before `_claims` resolves anything: the whole point
    # of `--plugin` is that the template it names comes from the package being
    # installed, so resolving first would refuse a name the install is about
    # to provide. And a failed install must leave no half-scaffolded package —
    # this function refuses if `src/<pkg>/` exists, so a retry after a failed
    # install must find a clean tree.
    if plugin:
        uv_add(repo_root, plugin_requirement(plugin))
    # One merge for both halves — the resolution and the known-name list the
    # message prints — so a repo's `templates/` is imported once here too.
    # Read through `_claims` rather than a resolve-only helper, because this site
    # also has to tell an installed-only claim apart from a name nothing
    # claims — the same distinction `validate_config` makes at its own emit
    # site, and for the same reason: an installed name is known from package
    # metadata without importing it, so `E-TEMPLATE-UNKNOWN` would be false of
    # it (spec correction 1).
    claims = _claims(repo_root)
    claim = claims.get(template_name)
    template = claim.cls() if claim is not None and claim.cls is not None else None
    known = sorted(claims)
    if template is None:
        if claim is not None and claim.provenance == "installed":
            raise ContractError(
                installed_template_message(template_name, claim),
                code="E-TEMPLATE-INSTALLED-UNSUPPORTED",
            )
        # `plugin=None` is untested but true by construction: `None` is
        # `unknown_template_message`'s own default for the parameter, so
        # passing it explicitly here is documentation rather than behaviour —
        # no mutation of this argument can differ from deleting it. `generate
        # experiment` has no config to read a `plugin` field from; it is the
        # command writing the file that field would live in (review M3).
        raise ContractError(
            unknown_template_message(template_name, known, plugin=None),
            code="E-TEMPLATE-UNKNOWN",
        )
    root = repo_root.resolve()
    for label, raw in (("input_dir", input_dir), ("output_dir", output_dir)):
        resolved = Path(raw).expanduser().resolve()
        if resolves_inside_repo(resolved, root):
            raise ContractError(
                f"{label} {resolved} resolves inside the git repository at {root}",
                code="E-DATA-IN-REPO",
            )

    pkg = package_name(name)
    entrypoint = f"{pkg}.experiment:{class_name(name)}"
    pkg_dir = repo_root / "src" / pkg
    if pkg_dir.exists():
        raise ContractError(
            f"src/{pkg}/ already exists — `generate experiment` never modifies an existing package",
            code="E-EXPERIMENT-EXISTS",
        )
    (pkg_dir / "steps").mkdir(parents=True, exist_ok=False)
    (pkg_dir / "__init__.py").touch()
    (pkg_dir / "steps" / "__init__.py").touch()
    (pkg_dir / "steps" / "step01_summarize_units.py").write_text(STARTER_STEP.format(pkg=pkg))
    (pkg_dir / "experiment.py").write_text(EXPERIMENT_PY.format(pkg=pkg, cls=class_name(name)))

    config_path = repo_root / "configs" / name / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        materialize_config(
            template=template,
            template_name=template_name,
            name=name,
            input_dir=input_dir,
            output_dir=output_dir,
            entrypoint=entrypoint,
            plugin=plugin,
        )
    )
    return config_path
