"""`generate report` — a project-local `BaseReport` override, seeded with
`format`. docs/reference.md § A report override renders one experiment's own
figures.

The scaffolded body is runnable as-is, on `generate step`'s and the starter
step's own precedent (`generators/step.py`, `generators/experiment.py`): it
`yield from super().sections(run, io)` and yields nothing else, with a `TODO`
marking the one place a figure goes. A generated override that raised, or
that rendered FEWER sections than no override at all, would make `generate
report` a downgrade rather than a convenience.
"""

from pathlib import Path

from publishable.errors import ContractError
from publishable.generators.experiment import package_name

# `format` has no base default on `BaseReport` (Decision 2) — that absence is
# exactly what `generate report` makes true, because it always writes this
# line. `--format` seeds the attribute and nothing else; the class is the
# source of truth from then on, exactly as `--input-dir` seeds a config field
# it doesn't afterwards own. When `--format` is omitted, this generator picks
# "markdown" — the same medium core renders in when no override exists at
# all — as ITS OWN default; `BaseReport` itself still declares none.
REPORT_PY = """\
# src/{pkg}/report.py — generated
from publishable import BaseReport


class Report(BaseReport):
    format = "{fmt}"                             # html | markdown — `--format` seeds this line

    def sections(self, run, io):
        yield from super().sections(run, io)    # the standard blocks, in order
        # TODO: yield self.section("<title>", body=...) for a figure this experiment needs
"""


def generate_report(*, repo_root: Path, experiment: str, fmt: str | None) -> Path:
    """Write `src/<pkg>/report.py`, refusing an existing one.

    `experiment` names the package the same way `generate step` does — reuse
    of `package_name` and `E-EXPERIMENT-UNKNOWN`, so a missing package is the
    identical fault under the identical code regardless of which generator
    hit it first.

    `fmt` is written verbatim, whatever it is — this generator does not
    validate it against `"html"`/`"markdown"`. `--format` writes the
    attribute and nothing else; a class declaring anything else is `report`'s
    own refusal to make (`E-REPORT-FORMAT`, at render), the same division of
    labor `--input-dir` seeding a config field draws with the field's own
    later checks.
    """
    pkg = package_name(experiment)
    pkg_dir = repo_root / "src" / pkg
    if not pkg_dir.is_dir():
        raise ContractError(f"no experiment package at src/{pkg}/", code="E-EXPERIMENT-UNKNOWN")
    path = pkg_dir / "report.py"
    if path.exists():
        raise ContractError(
            f"src/{pkg}/report.py already exists — `generate report` never "
            "modifies an existing override",
            code="E-REPORT-EXISTS",
        )
    resolved_fmt = fmt if fmt is not None else "markdown"
    path.write_text(REPORT_PY.format(pkg=pkg, fmt=resolved_fmt))
    return path
