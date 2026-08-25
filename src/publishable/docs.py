"""The managed-region machinery `publishable docs` rewrites through.

`docs/reference.md` § The generated README: the `<!-- publishable:begin ... -->`
regions are **managed**, and *"a generator that populates one leaves everything
outside it untouched."* This module is that promise's implementation — the
parser that computes the bound, and the rewriter that respects it. It
dispatches nothing: `cli.command_docs` is H9d task 7's.

**Ruling EE (design § 3, Decision 3).** `docs` rewrites **only what a region
encloses**, and a region it cannot find is a **named refusal, never a
silence** — *a command that silently rewrites nothing looks identical to one
that worked*. Every failure mode below is a case where the bound a rewrite
would be performed against cannot be computed, and a rewrite performed against
a bound that could not be computed is the unrecoverable outcome: prose outside
a region is hand-written by definition and has no other copy.

A README missing SOME of the four regions is deliberately **not** a refusal —
that is the ordinary state of every project scaffolded before this slice, and
the caller rewrites what it finds and names what it did not (task 7). A README
holding **none** of them is, which is why `regions` raises rather than
returning an empty mapping: an empty return is indistinguishable, at the call
site, from a successful parse of a file with nothing to manage.
"""

import re
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from publishable.errors import ContractError

if TYPE_CHECKING:
    from publishable.templates.registry import Claim

#: The four regions core manages. The first three come from `docs/reference.md`
#: § The generated README; the fourth from § Templates, whose plugin README
#: shows a `templates` region holding a generated parameter table.
MANAGED_REGIONS: tuple[str, ...] = ("overview", "credentials", "experiments", "templates")

# A marker line, matched WHOLE: leading and trailing whitespace is tolerated
# because a markdown formatter may indent one, but nothing else may share the
# line. A marker with prose after it would leave a rewrite ambiguous about
# whether that prose is inside the region or outside it, and this parser
# answers only questions it can answer exactly.
_MARKER = re.compile(r"^[ \t]*<!--[ \t]*publishable:(begin|end)[ \t]+([^\s>]+)[ \t]*-->[ \t]*$")

# A fenced code block's delimiter, CommonMark's rule: up to three leading
# spaces, then three or more backticks or tildes. The closing fence uses the
# same character, is at least as long as the opener, and carries no info
# string.
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")


def _marker_lines(lines: list[str]) -> list[tuple[int, str, str]]:
    """Every marker line OUTSIDE a fenced code block, as `(index, kind, name)`.

    The fence exclusion is the whole reason this is a scanner rather than a
    `str.find`: this repository's own documents contain markdown inside
    markdown — § The generated README fences a README that itself fences a
    `bash` block, which is why the outer fence there is four backticks — and a
    marker spelling inside such a block is CONTENT. A parser that scanned
    lines without excluding fences would rewrite an example.
    """
    found: list[tuple[int, str, str]] = []
    fence: tuple[str, int] | None = None
    for index, line in enumerate(lines):
        delimiter = _FENCE.match(line)
        if fence is None:
            if delimiter is not None and not (
                delimiter.group(1).startswith("`") and "`" in delimiter.group(2)
            ):
                fence = (delimiter.group(1)[0], len(delimiter.group(1)))
            else:
                marker = _MARKER.match(line)
                if marker is not None:
                    found.append((index, marker.group(1), marker.group(2)))
            continue
        character, length = fence
        if (
            delimiter is not None
            and delimiter.group(1)[0] == character
            and len(delimiter.group(1)) >= length
            and delimiter.group(2).strip() == ""
        ):
            fence = None
    return found


def regions(text: str) -> dict[str, tuple[int, int]]:
    """Every managed region in `text`, as `name → (start, stop)` — the
    half-open **line** span strictly between its `begin` and its `end` marker,
    both marker lines excluded.

    Four of the five refusals live here, each a `ContractError` carrying its
    own code:

    - a `begin` with no matching `end` before EOF, or an `end` with no `begin`,
      or a second `begin` opening while one is still open →
      `E-DOCS-REGION-UNBALANCED`
    - two `begin` markers naming one region → `E-DOCS-REGION-DUPLICATE`
    - a region name core does not manage → `E-DOCS-REGION-UNKNOWN`
    - none of `MANAGED_REGIONS` present at all → `E-DOCS-NO-REGIONS`

    Line indices rather than byte offsets because the markers are whole lines
    and a rewrite splices lines; and half-open so an empty region — the two
    markers adjacent — is `(n, n)` rather than something a caller has to
    special-case.
    """
    lines = text.split("\n")
    spans: dict[str, tuple[int, int]] = {}
    open_name: str | None = None
    open_at = -1
    for index, kind, name in _marker_lines(lines):
        if name not in MANAGED_REGIONS:
            raise ContractError(
                f"line {index + 1}: `{name}` is not a region core manages — "
                f"the managed regions are {', '.join(MANAGED_REGIONS)}",
                code="E-DOCS-REGION-UNKNOWN",
            )
        if kind == "begin":
            if open_name is not None:
                raise ContractError(
                    f"line {index + 1}: region `{name}` opens while `{open_name}` "
                    f"(line {open_at + 1}) is still open — regions do not nest",
                    code="E-DOCS-REGION-UNBALANCED",
                )
            if name in spans:
                raise ContractError(
                    f"line {index + 1}: region `{name}` is opened twice in one file",
                    code="E-DOCS-REGION-DUPLICATE",
                )
            open_name, open_at = name, index
        else:
            if open_name is None:
                raise ContractError(
                    f"line {index + 1}: region `{name}` ends without ever beginning",
                    code="E-DOCS-REGION-UNBALANCED",
                )
            if name != open_name:
                raise ContractError(
                    f"line {index + 1}: region `{name}` ends while `{open_name}` "
                    f"(line {open_at + 1}) is the open one",
                    code="E-DOCS-REGION-UNBALANCED",
                )
            spans[open_name] = (open_at + 1, index)
            open_name = None
    if open_name is not None:
        raise ContractError(
            f"line {open_at + 1}: region `{open_name}` begins and never ends",
            code="E-DOCS-REGION-UNBALANCED",
        )
    if not spans:
        raise ContractError(
            "this README declares none of the managed regions "
            f"({', '.join(MANAGED_REGIONS)}), so there is nothing `docs` may "
            "rewrite — a README is not regenerated from a template, because "
            "everything outside a region is hand-written",
            code="E-DOCS-NO-REGIONS",
        )
    return spans


def body_of(text: str, name: str) -> str:
    """The current body of one region, in the form `rewrite` takes back.

    `rewrite(text, name, body_of(text, name)) == text` for every region of
    every file `regions` accepts — the round-trip identity that says the
    splice moves no byte it was not asked to move.
    """
    start, stop = _span(text, name)
    lines = text.split("\n")[start:stop]
    return "".join(line + "\n" for line in lines)


def rewrite(text: str, name: str, body: str) -> str:
    """`text` with region `name`'s body replaced by `body`, and **every other
    byte identical** — both marker lines, the prose above and below, and the
    file's trailing-newline convention included.

    `body` is spliced as whole lines: one trailing newline is the separator
    rather than an extra blank line (so `"a\\nb"` and `"a\\nb\\n"` both give two
    lines, and `""` gives none, leaving the two markers adjacent).
    """
    start, stop = _span(text, name)
    lines = text.split("\n")
    new = body.split("\n")
    if new and new[-1] == "":
        new.pop()
    return "\n".join(lines[:start] + new + lines[stop:])


def _span(text: str, name: str) -> tuple[int, int]:
    """One region's span, refusing a name this file does not carry.

    A managed name absent from THIS file is refused rather than silently
    skipped, for Ruling EE's reason: a rewriter that returned `text` unchanged
    for a region it could not find would be indistinguishable from one that
    worked. It carries `E-DOCS-REGION-UNKNOWN` — the caller asked for a region
    that is not there — rather than a sixth code no § Errors row covers.
    """
    if name not in MANAGED_REGIONS:
        raise ContractError(
            f"`{name}` is not a region core manages — the managed regions are "
            f"{', '.join(MANAGED_REGIONS)}",
            code="E-DOCS-REGION-UNKNOWN",
        )
    spans = regions(text)
    if name not in spans:
        raise ContractError(
            f"this README declares no `{name}` region, so there is nowhere to "
            "write one — `docs` never writes outside a region",
            code="E-DOCS-REGION-UNKNOWN",
        )
    return spans[name]


def read_readme(repo_root: Path) -> tuple[Path, str]:
    """The repository's own `README.md`, refusing its absence by name.

    The fifth refusal of design § 3's table: `E-DOCS-NO-README`. `docs` never
    creates one — a README `publishable new` did not write is a file this
    command has no template for, and writing one would be writing outside
    every region.
    """
    path = repo_root / "README.md"
    if not path.is_file():
        raise ContractError(
            f"no README.md at {repo_root} — `docs` rewrites the managed regions "
            "of a README that already exists and never creates one",
            code="E-DOCS-NO-README",
        )
    return path, path.read_text()


# --- The region BODIES, and the merge every generator performs (tasks 4-7) ---
#
# One builder per managed region, each a pure function of the repository: the
# region is *derived*, so a generator never composes markdown of its own and
# `docs` never has a second opinion about what a region should hold. The
# generators call `merge_into_readme` for the regions their own write changed;
# `publishable docs` calls `refresh` for all four.
#
# Every empty state below is the literal the scaffolded README already carries
# (`readme_templates/README.md.tmpl`), so `docs` on a freshly scaffolded
# project rewrites the file to itself byte for byte — pinned, because a
# populated form that cannot degenerate to the scaffold's own line means the
# line is documentation of a state the generator never writes.

#: The `credentials` row a project with nothing to declare carries.
CREDENTIALS_EMPTY_ROW = "| _(none yet — added as experiments declare them)_ | |"


def config_paths(repo_root: Path) -> list[Path]:
    """Every `configs/<name>/config.yaml`, in name order.

    The experiment's NAME is its directory's, not a field read out of the file:
    `generate experiment` creates `configs/<name>/`, and the directory is what
    the `Run` column's own invocation has to name for the command to work.
    """
    return sorted((repo_root / "configs").glob("*/config.yaml"))


def _declared_template(path: Path) -> str | None:
    """One config's `experiment_type`, or `None` when the file cannot be read.

    Tolerant on purpose: a generator refreshing the README is not the place a
    malformed config is refused — `validate` is, and it says so with a code and
    a remedy. `None` becomes a printed row here rather than a silence, which is
    Ruling EE's rule applied to the row rather than to the region.
    """
    try:
        doc = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(doc, Mapping):
        return None
    name = doc.get("experiment_type")
    return name if isinstance(name, str) and name else None


def experiments(repo_root: Path) -> list[tuple[str, str | None]]:
    """`(experiment name, template name or None)` for every config, in name order."""
    return [(path.parent.name, _declared_template(path)) for path in config_paths(repo_root)]


def _unreadable_reason(name: str, template_name: str | None, claim: "Claim | None") -> str:
    """Why one experiment contributes no credential row — a printed fact, never
    a silence.

    Correction 21 is the case this exists for: an installed template's `cls` is
    `None` by construction, because core resolves an entry-point name from
    package metadata without importing the package, so its `required_env` is
    unreadable here and a *shorter table with no explanation* would be the
    silently-skipped fault. The other two shapes are reached the same way and
    say what they are.
    """
    if template_name is None:
        return (
            f"`{name}` — its `config.yaml` declares no readable `experiment_type`, "
            "so no template's `required_env` could be read"
        )
    if claim is None:
        return (
            f"`{name}` — no template claims the name `{template_name}`, so no "
            "`required_env` could be read"
        )
    return (
        f"`{name}` — its template `{template_name}` is installed "
        f"({claim.provider}), so its `required_env` is not readable in this "
        "build (`E-TEMPLATE-INSTALLED-UNSUPPORTED`)"
    )


def credentials_body(repo_root: Path) -> str:
    """The `credentials` region: one row per variable any experiment's template
    declares in `required_env`, sorted by variable, with the experiments needing
    it in the second cell.

    **`required_env` only, deliberately not the wider set
    `validate.declared_credential_names_for` computes.** That helper unions
    `required_env` with every `Param.requires_env` variable across the expanded
    sweep — a variable a *choice* needs. Such a variable is needed by the
    experiment only under one value of one parameter, so a `Needed by` cell
    naming the experiment flatly would be false under every other value, and
    this table has no column to qualify it in. `publishable list-templates` and
    the `templates` region carry the per-choice requirement instead, beside the
    choice it belongs to.
    """
    from publishable.templates.registry import _claims

    claims = _claims(repo_root)
    needed: dict[str, set[str]] = {}
    unreadable: list[str] = []
    for name, template_name in experiments(repo_root):
        claim = claims.get(template_name) if template_name is not None else None
        cls = claim.cls if claim is not None else None
        if cls is None:
            unreadable.append(_unreadable_reason(name, template_name, claim))
            continue
        declared = getattr(cls, "required_env", None)
        # The same guard `validate._check_required_env` uses: a `required_env`
        # that is not a list is that check's finding to report, not this
        # renderer's to iterate as characters.
        for variable in declared if isinstance(declared, list) else []:
            needed.setdefault(str(variable), set()).add(name)
    rows = [
        f"| `{variable}` | {', '.join(f'`{who}`' for who in sorted(names))} |"
        for variable, names in sorted(needed.items())
    ]
    rows += [f"| _(unknown)_ | {reason} |" for reason in unreadable]
    return "\n".join(
        [
            "### Required credentials",
            "",
            "| Variable | Needed by |",
            "|---|---|",
            *(rows or [CREDENTIALS_EMPTY_ROW]),
        ]
    )


#: Region name → the function that computes its body from the repository.
#: `refresh` reads this rather than a chain of branches, so a region with no
#: builder is a `KeyError` at the call site rather than a region silently left
#: alone — the silence Ruling EE refuses.
BODY_BUILDERS: dict[str, Callable[[Path], str]] = {
    "credentials": credentials_body,
}


def refresh(repo_root: Path, names: Sequence[str]) -> tuple[list[str], list[str]]:
    """Rewrite the named regions of this repository's README from the repository
    itself, and answer `(rewritten, not declared)`.

    Raises this module's five refusals — the README's absence, and the four
    structural faults `regions` computes — because each is a case where the
    bound a rewrite would be performed against cannot be computed. A managed
    name this README does not declare is **not** one of them: that is the
    ordinary state of every project scaffolded before H9d, and it is returned
    in the second list for the caller to NAME rather than being skipped
    silently.

    The file is written only when a byte actually moved, so a repository whose
    README is already current keeps its mtime.
    """
    path, text = read_readme(repo_root)
    present = regions(text)
    rewritten: list[str] = []
    absent: list[str] = []
    updated = text
    for name in names:
        if name not in present:
            absent.append(name)
            continue
        updated = rewrite(updated, name, BODY_BUILDERS[name](repo_root))
        rewritten.append(name)
    if updated != text:
        path.write_text(updated)
    return rewritten, absent


def merge_into_readme(repo_root: Path, names: Sequence[str]) -> list[str]:
    """`refresh`, for a GENERATOR: the notes it should print, and no exception.

    A generator has already written a package, a config or a template file by
    the time it gets here, so a README it cannot rewrite may not cost the
    caller the files that are already on disk — `generate experiment` against a
    README scaffolded before this slice would otherwise leave a half-generated
    tree behind a non-zero exit. Every fault therefore becomes a **printed
    note** and the generator succeeds.

    The notes are the caller's to print, not this function's: `docs` names its
    own absences on stdout, and a generator prints these beside its own
    diagnostics on stderr.
    """
    try:
        _rewritten, absent = refresh(repo_root, names)
    except ContractError as exc:
        return [
            f"note: README.md's managed regions were not updated — {exc.code}: {exc}",
        ]
    except OSError as exc:
        return [f"note: README.md's managed regions were not updated — {exc}"]
    return [
        f"note: README.md declares no `{name}` region, so nothing was written "
        "there — a region is never created, only rewritten"
        for name in absent
    ]
