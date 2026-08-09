"""`generate experiment` — always creates, never wraps. Greenfield only."""

from pathlib import Path

from publishable.errors import ContractError
from publishable.materialize import materialize_config
from publishable.provenance import resolves_inside_repo
from publishable.templates.registry import get_template

STARTER_STEP = '''\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        units = list(io.units)
        for unit in units:
            io.record(unit.key, {{"present": True}})
        return {{"n_units": len(units)}}    # TODO: replace with your analysis
'''

EXPERIMENT_PY = '''\
# src/{pkg}/experiment.py — order, nothing else
from publishable import BaseExperiment

from .steps.step01_summarize_units import Step as SummarizeUnits

STEPS = [SummarizeUnits]


class {cls}(BaseExperiment):
    # Order, nothing else. Each step declares its own scope; core derives
    # the execution plan from that. Reordering here IS reordering the pipeline.
    steps = STEPS
'''


def package_name(experiment: str) -> str:
    return experiment.replace("-", "_")


def class_name(experiment: str) -> str:
    return "".join(part.capitalize() for part in experiment.split("-")) + "Experiment"


def generate_experiment(
    *, repo_root: Path, name: str, template_name: str, input_dir: str, output_dir: str
) -> Path:
    template = get_template(template_name)
    if template is None:
        raise ContractError(
            f"no installed template registers `{template_name}`", code="E-TEMPLATE-UNKNOWN"
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
            f"src/{pkg}/ already exists — `generate experiment` never modifies an "
            "existing package",
            code="E-EXPERIMENT-EXISTS",
        )
    (pkg_dir / "steps").mkdir(parents=True, exist_ok=False)
    (pkg_dir / "__init__.py").touch()
    (pkg_dir / "steps" / "__init__.py").touch()
    (pkg_dir / "steps" / "step01_summarize_units.py").write_text(
        STARTER_STEP.format(pkg=pkg)
    )
    (pkg_dir / "experiment.py").write_text(
        EXPERIMENT_PY.format(pkg=pkg, cls=class_name(name))
    )

    config_path = repo_root / "configs" / name / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        materialize_config(
            template=template, template_name=template_name, name=name,
            input_dir=input_dir, output_dir=output_dir, entrypoint=entrypoint,
        )
    )
    return config_path
