"""`publishable new`. docs/reference.md § Scaffolding."""

import subprocess
from pathlib import Path

from publishable.errors import ContractError

GITIGNORE = """\
# Credentials — never committed
.env

# Python
__pycache__/
*.py[cod]
.venv/
"""

README = """\
# {name}

<!-- publishable:begin overview -->
A `publishable` experiment repository. Code, parameters, and provenance are
separated by construction: this repo holds code and configs; input and output
data live outside it, under paths each config names.
<!-- publishable:end overview -->

## Setup

```bash
uv sync
```

## Experiments

<!-- publishable:begin experiments -->
None yet. Create one with `publishable generate experiment <name>`.
<!-- publishable:end experiments -->
"""

CITATION = """\
cff-version: 1.2.0
message: "If you use this software, please cite it as below."
type: software
title: {name}
authors:
  - family-names: ""
    given-names: ""
version: 0.1.0
"""

MIT = """\
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
"""

PYPROJECT = """\
[project]
name = "{name}"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["publishable"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
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
    (root / "README.md").write_text(README.format(name=name))
    (root / "CITATION.cff").write_text(CITATION.format(name=name))
    (root / "LICENSE").write_text(MIT if license_name == "MIT" else f"{license_name}\n")
    (root / "pyproject.toml").write_text(PYPROJECT.format(name=name))
    (root / ".gitignore").write_text(GITIGNORE)
    (root / ".env.example").write_text("# Credential variable NAMES only, never values\n")
    if not (root / ".git").exists():
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "add", "."], cwd=root, check=True)
        subprocess.run(
            # gpgsign=false so scaffolding cannot hang or fail on a machine that
            # has commit signing configured globally.
            ["git", "-c", "user.email=you@example.com", "-c", "user.name=you",
             "-c", "commit.gpgsign=false",
             "commit", "-qm", "Scaffold a publishable experiment repository"],
            cwd=root, check=True,
        )
    return root
