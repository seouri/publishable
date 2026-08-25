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
from pathlib import Path

from publishable.errors import ContractError

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
