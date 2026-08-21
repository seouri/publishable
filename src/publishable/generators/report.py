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

import json
from pathlib import Path

from publishable.errors import ContractError
from publishable.generators.experiment import package_name

# `format` has no base default on `BaseReport` (Decision 2) — that absence is
# exactly what `generate report` makes true, because it always writes this
# line. `--format` seeds the attribute and nothing else; the class is the
# source of truth from then on. When `--format` is omitted, this generator
# picks "markdown" — the same medium core renders in when no override exists
# at all — as ITS OWN default; `BaseReport` itself still declares none.
#
# `{fmt}` below is a Python STRING-LITERAL SOURCE TEXT, already quoted and
# escaped by `json.dumps` at the call site — never the raw value substituted
# between hand-written quotes. `json.dumps` always emits a double-quoted,
# backslash-escaped literal that is also valid Python source (JSON's escape
# vocabulary is a subset of Python's), so any string --format carries writes
# a file that PARSES, whatever characters it holds (fix round 1, Major 1 /
# Minor 1: the prior form embedded the raw value inside hand-written quotes,
# so a value carrying a `"` produced a non-parsing file, and a value crafted
# around that broke out of the literal and ran at import).
REPORT_PY = """\
# src/{pkg}/report.py — generated
from publishable import BaseReport


class Report(BaseReport):
    format = {fmt}                             # html | markdown — `--format` seeds this line

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

    `fmt` is not checked against the enum `"html"`/`"markdown"` here, and
    that deferral to `report`'s own render-time check (`E-REPORT-FORMAT`) is
    deliberate and stays: `--format` writes the attribute and nothing else,
    the class is the source of truth from then on, and a second enum check
    here would be a second source of truth for the one rule `E-REPORT-FORMAT`
    already owns (fix round 1, reviewer's Attack 6). What is NOT deferred is
    that the file this function writes parses — that is this function's own
    promise, not a judgement about the value's meaning, and it holds for
    every `fmt`, not only the two the enum accepts: `json.dumps` below turns
    `fmt` into a self-quoting, self-escaping Python literal before it ever
    reaches `REPORT_PY`, so a `"`, a newline, or a backslash in `--format`'s
    argument can no longer break out of the literal or the class body. A
    value that survives to declare something other than `"html"`/
    `"markdown"` still reaches `E-REPORT-FORMAT` at render, exactly as this
    module's docstring on `format` describes — including a value that used
    to reach a different code entirely (`E-REPORT-OVERRIDE-IMPORT`, on a
    file that failed to import at all) before this fix.
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
    path.write_text(REPORT_PY.format(pkg=pkg, fmt=json.dumps(resolved_fmt)))
    return path
