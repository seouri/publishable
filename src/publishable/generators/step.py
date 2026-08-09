"""`generate step` — the next-numbered file, registered in order."""

from pathlib import Path

from publishable.errors import ContractError
from publishable.generators.experiment import package_name

STEP_PY = '''\
from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        return {{}}      # TODO: implement {step_name}
'''


def generate_step(*, repo_root: Path, experiment: str, step_name: str) -> Path:
    pkg = package_name(experiment)
    steps_dir = repo_root / "src" / pkg / "steps"
    if not steps_dir.is_dir():
        raise ContractError(
            f"no experiment package at src/{pkg}/", code="E-EXPERIMENT-UNKNOWN"
        )
    existing = sorted(steps_dir.glob("step[0-9][0-9]_*.py"))
    for prior in existing:
        if prior.stem.split("_", 1)[1] == step_name:
            raise ContractError(
                f"step `{step_name}` already exists at {prior} — `generate step` never "
                "renumbers or replaces an existing step",
                code="E-STEP-EXISTS",
            )
    number = len(existing) + 1
    path = steps_dir / f"step{number:02d}_{step_name}.py"
    path.write_text(STEP_PY.format(step_name=step_name))

    experiment_py = repo_root / "src" / pkg / "experiment.py"
    text = experiment_py.read_text()
    module = path.stem
    cls = "".join(part.capitalize() for part in step_name.split("_"))
    text = text.replace(
        "\nSTEPS = [",
        f"\nfrom .steps.{module} import Step as {cls}\n\nSTEPS = [",
    ).replace("STEPS = [", f"STEPS = [{cls}, ", 1)
    text = text.replace(f"STEPS = [{cls}, ]", f"STEPS = [{cls}]")
    experiment_py.write_text(_reorder(text, cls))
    return path


def _reorder(text: str, cls: str) -> str:
    """Keep the new step last in the ordered list rather than first."""
    import re

    match = re.search(r"STEPS = \[(.*?)\]", text, re.S)
    if not match:
        return text
    names = [n.strip() for n in match.group(1).split(",") if n.strip()]
    names = [n for n in names if n != cls] + [cls]
    return text[: match.start(1)] + ", ".join(names) + text[match.end(1) :]
