"""`publishable new`. docs/reference.md § Scaffolding."""

import subprocess
from importlib.resources import files
from pathlib import Path

from publishable.errors import ContractError


def read_scaffold(filename: str) -> str:
    """One shipped scaffold, read out of `publishable.readme_templates` at
    scaffold time.

    `README.md.tmpl`, `CITATION.cff.tmpl`, `LICENSE.mit.tmpl` and
    `gitignore.tmpl` live as FILES rather than as this module's string
    globals, which is what `docs/reference.md` § Package layout has always
    said `readme_templates/` holds, and what the S1 spine plan scheduled for
    *"when `publishable docs` needs to rewrite managed regions"* — this slice.
    It is not tidying: `docs` regenerates the same region bodies `new` writes,
    so the two either share one source or become two copies of four regions
    that drift.

    Read through `importlib.resources` rather than off `__file__`, so an
    installed wheel answers the same way a source checkout does; the two
    `{name}` interpolations and every refusal stay in `scaffold_project`.
    """
    return (files("publishable.readme_templates") / filename).read_text()


PYPROJECT = """\
[project]
name = "{name}"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["publishable"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
package = false
"""
"""What `publishable new` writes, and the last two lines are load-bearing.

Without `package = false`, `uv` tries to BUILD the project it is asked to run
in, hatchling looks for a package matching the distribution name, and there is
none: `src/` holds a `.gitkeep`, and `generate experiment <name>` writes
`src/<experiment>/` rather than `src/<project>/` — so no experiment ever
supplies one either. Every `uv run publishable ...` in a scaffolded project
failed on a hatchling traceback, including the `next:` line `new` itself
prints.

`package = false` rather than a `[tool.hatch.build.targets.wheel]` entry
because the declaration is true rather than a workaround: an experiment
repository is code under a commit, not a distribution anybody installs — which
is exactly why `code_hash` covers `src/**` and `templates/**` and `uv.lock`
pins everything else. A plugin package needs none of this; `publishable-my-assay`
builds, its `src/publishable_my_assay/` matching its own name.
"""


def scaffold_project(root: Path, license_name: str = "MIT") -> Path:
    """Fixed layout, so commands never need --repo or --templates-dir."""
    name = root.name
    if root.exists() and any(root.iterdir()):
        raise ContractError(
            f"{root} already exists and is not empty — `new` never overwrites an "
            "existing project; choose a different path or remove it deliberately",
            code="E-PROJECT-EXISTS",
        )
    root.mkdir(parents=True, exist_ok=True)
    for directory in ("src", "templates", "configs", "tests", "docs"):
        (root / directory).mkdir(exist_ok=True)
        (root / directory / ".gitkeep").touch()
    (root / "README.md").write_text(read_scaffold("README.md.tmpl").format(name=name))
    (root / "CITATION.cff").write_text(read_scaffold("CITATION.cff.tmpl").format(name=name))
    (root / "LICENSE").write_text(
        read_scaffold("LICENSE.mit.tmpl") if license_name == "MIT" else f"{license_name}\n"
    )
    (root / "pyproject.toml").write_text(PYPROJECT.format(name=name))
    (root / ".gitignore").write_text(read_scaffold("gitignore.tmpl"))
    (root / ".env.example").write_text("# Credential variable NAMES only, never values\n")
    if not (root / ".git").exists():
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(
            # gpgsign=false so scaffolding cannot hang or fail on a machine that
            # has commit signing configured globally.
            [
                "git",
                "-c",
                "user.email=you@example.com",
                "-c",
                "user.name=you",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "-qm",
                "Scaffold a publishable experiment repository",
            ],
            cwd=root,
            check=True,
        )
    return root
