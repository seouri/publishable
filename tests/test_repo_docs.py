"""The mechanical pass over this repository's own documents, as tests.

`CLAUDE.md` § Checking consistency after any `*.md` edit describes this pass and
says to write it as throwaway greps each time rather than keeping a checker
around. That rule is about not maintaining a *tool*; it is not an argument
against pinning the property, which is what this repo does with everything else.
These are assertions about this repository's documents, they run inside
`uv run pytest`, and `tests/` is deliberately absent from the sdist — so nothing
here is shipped and no tooling is kept.

**What each check is, and the trap it exists for.** Every one of the three was
first written wrong, and the wrong version passed:

- **Fenced blocks are excluded from every structural scan, links included.**
  `reference.md` holds Python whose calls read as markdown links to a naive
  regex — `pearsonr(units.pred, units.truth)` looks like `[...](...)` — and a
  scan that skips fences only when collecting headings reports a broken link
  that does not exist.
- **Table structure is judged on the line with inline code spans removed, and
  emptiness on the raw line.** Prose quoting a header (``the last `| Figure |
  Count |` header``) otherwise reads as a table row; and a row whose every cell
  is a code span (`` | `pattern=r"..."` | `str` | ``) reads as empty once the
  spans are stripped. Both were live false positives, in
  `feasibility-llm-growth-studies.md` and `reference.md` respectively.
- **Pipes split on unescaped `|` only.** This repo's tables carry `int \| bool`
  in type-union cells, and counting that as a separator fails a correct row.

Anchors follow GitHub's slugger, including its `-1`/`-2` suffixes for a repeated
heading — which is also why an en dash may not appear in a heading that anything
links to: the slugger drops it entirely.
"""

import re
import unicodedata
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]

# The documents this pass governs. `docs/superpowers/` is deliberately absent:
# it is the development record, which the pass never governs, and retro-editing
# it destroys the evidence it exists to hold.
_EXPECTED = (
    "README.md",
    "CLAUDE.md",
    "docs/design-principles.md",
    "docs/experimental-designs.md",
    "docs/reference.md",
)


def _documents() -> list[Path]:
    found = [_REPO_ROOT / "README.md", _REPO_ROOT / "CLAUDE.md"]
    found += sorted((_REPO_ROOT / "docs").glob("*.md"))
    return [p for p in found if p.exists()]


def _rel(path: Path) -> str:
    return path.relative_to(_REPO_ROOT).as_posix()


DOCUMENTS = _documents()

# An unpacked sdist carries three documents and no `CLAUDE.md`, so a missing file
# there is the distribution working as designed. In a checkout it is a deletion,
# and these tests must fail rather than quietly check less — the same condition
# `test_scaffold.py`'s tutorial pins use, and for the same reason.
_IN_CHECKOUT = (_REPO_ROOT / ".git").exists()


def _tag_fences(text: str) -> list[tuple[str, str]]:
    out, in_fence = [], False
    for line in text.split("\n"):
        if re.match(r"^\s*```", line):
            in_fence = not in_fence
            out.append(("FENCE", line))
            continue
        out.append(("FENCE" if in_fence else "TEXT", line))
    return out


def _github_anchor(heading: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", heading.strip()).lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    return text.replace(" ", "-")


def _anchors(path: Path) -> list[str]:
    """Every anchor the file defines, in order, with GitHub's repeat suffixes."""
    seen: dict[str, int] = {}
    anchors = []
    for tag, line in _tag_fences(path.read_text(encoding="utf-8")):
        if tag != "TEXT":
            continue
        m = re.match(r"^#{1,6}\s+(.*)$", line)
        if not m:
            continue
        base = _github_anchor(m.group(1))
        if base in seen:
            seen[base] += 1
            anchors.append(f"{base}-{seen[base]}")
        else:
            seen[base] = 0
            anchors.append(base)
    return anchors


def _structural(line: str) -> str:
    """The line with inline code spans removed: only structural pipes survive."""
    return re.sub(r"`[^`]*`", "", line)


def _cells(line: str) -> list[str]:
    return re.split(r"(?<!\\)\|", line)


def test_every_document_this_pass_governs_is_present():
    """The fail-open guard for the three checks below.

    Each of them iterates the documents it finds, so a deleted file makes them
    check less and stay green. This is the assertion that notices, and it is
    skipped only outside a checkout — where an absent `CLAUDE.md` is the sdist's
    `include` list working as designed rather than a deletion.
    """
    if not _IN_CHECKOUT:
        pytest.skip("not a checkout; a distribution carries only the documents it ships")
    missing = [rel for rel in _EXPECTED if not (_REPO_ROOT / rel).exists()]
    assert missing == [], missing
    assert len(DOCUMENTS) >= len(_EXPECTED)


@pytest.mark.parametrize("path", DOCUMENTS, ids=_rel)
def test_every_link_and_anchor_resolves(path: Path):
    """Relative links, self anchors, and cross-file anchors, outside fences."""
    broken = []
    own = set(_anchors(path))
    for lineno, (tag, line) in enumerate(_tag_fences(path.read_text(encoding="utf-8")), 1):
        if tag != "TEXT":
            continue
        for _, target in re.findall(r"\[([^\]]*)\]\(([^)]+)\)", line):
            target = target.strip()
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            file_part, _, anchor = target.partition("#")
            if not file_part:
                if anchor not in own:
                    broken.append(f"{_rel(path)}:{lineno} self anchor #{anchor}")
                continue
            resolved = (path.parent / file_part).resolve()
            if not resolved.is_file():
                broken.append(f"{_rel(path)}:{lineno} file {target}")
            elif anchor and anchor not in set(_anchors(resolved)):
                broken.append(f"{_rel(path)}:{lineno} cross anchor {target}")
    assert broken == [], broken


@pytest.mark.parametrize("path", DOCUMENTS, ids=_rel)
def test_no_duplicate_anchors_and_no_stray_characters(path: Path):
    """Two headings producing one anchor, trailing whitespace, tabs, invisibles.

    A duplicate anchor is checked on the *base* slug rather than on the
    suffixed one: GitHub disambiguates with `-1`, so the suffixed list never
    collides and asserting over it would be a test that cannot fail.

    Whitespace is checked on every line including fenced ones. `CLAUDE.md` says
    to skip fences for this pass, and the reason is real — a code sample may
    carry a tab — but this repository's fenced blocks are prose examples and
    ruff-formatted Python, neither of which does. Should that change, the fix is
    an exemption with a reason, not a silent skip.
    """
    text = path.read_text(encoding="utf-8")
    bases: dict[str, list[str]] = {}
    for tag, line in _tag_fences(text):
        if tag != "TEXT":
            continue
        m = re.match(r"^#{1,6}\s+(.*)$", line)
        if m:
            bases.setdefault(_github_anchor(m.group(1)), []).append(m.group(1))
    duplicates = {slug: headings for slug, headings in bases.items() if len(headings) > 1}
    assert duplicates == {}, duplicates

    stray = []
    for lineno, line in enumerate(text.split("\n"), 1):
        if re.search(r"[ \t]+$", line):
            stray.append(f"{_rel(path)}:{lineno} trailing whitespace")
        if "\t" in line:
            stray.append(f"{_rel(path)}:{lineno} tab")
        for ch in line:
            if ch not in (" ", "\t") and unicodedata.category(ch) in ("Cf", "Co", "Zs"):
                stray.append(f"{_rel(path)}:{lineno} invisible {ch!r}")
    assert stray == [], stray


@pytest.mark.parametrize("path", DOCUMENTS, ids=_rel)
def test_every_table_row_matches_its_header(path: Path):
    """Column counts against the header, and no wholly empty row."""
    problems = []
    in_table, header_cols = False, None
    for lineno, (tag, line) in enumerate(_tag_fences(path.read_text(encoding="utf-8")), 1):
        if tag != "TEXT":
            in_table = False
            continue
        stripped = _structural(line).strip()
        is_row = "|" in stripped
        is_sep = bool(re.match(r"^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$", stripped))
        if is_row and not in_table:
            header_cols, in_table = len(_cells(_structural(line))), True
            continue
        if in_table and is_sep:
            if len(_cells(_structural(line))) != header_cols:
                problems.append(f"{_rel(path)}:{lineno} separator columns")
            continue
        if in_table and is_row:
            if len(_cells(_structural(line))) != header_cols:
                problems.append(
                    f"{_rel(path)}:{lineno} row has {len(_cells(_structural(line)))} "
                    f"columns against header {header_cols}: {line[:70]}"
                )
            # Emptiness on the RAW line: a row whose cells are all code spans is
            # stripped to blanks by `_structural`, and calling it empty is this
            # check's own false positive.
            if not [c for c in _cells(line) if c.strip()]:
                problems.append(f"{_rel(path)}:{lineno} empty row")
            continue
        in_table = False
    assert problems == [], problems
