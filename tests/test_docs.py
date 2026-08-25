"""H9d task 2 — the managed-region parser and rewriter (`publishable docs`).

**Ruling EE** is what these fixtures exist for: `docs` rewrites only what a
region encloses, and a region it cannot find is a named refusal rather than a
silence. So every arm below is pinned in BOTH directions — what the parser
accepts and what it refuses, what the rewriter replaces and what it leaves
alone — because a rewriter that did nothing at all would pass every
refusal test on its own.

Design § 9's fixtures B and C.
"""

from pathlib import Path

import pytest

from publishable.docs import (
    MANAGED_REGIONS,
    body_of,
    read_readme,
    regions,
    rewrite,
)
from publishable.errors import ContractError

# ---------------------------------------------------------------------------
# Fixture C — all four regions, hand-written prose above, between and below,
# and a marker spelling inside a fenced code block.
#
# The fenced decoy is the fixture's whole point, and it is built as the
# documents' own shape rather than as a bare ``` block: `docs/reference.md`
# § The generated README fences a README that itself fences a `bash` block,
# so the outer fence is FOUR backticks and the inner three. A parser that
# toggled on any ``` line would come out of the outer fence at the inner
# one and rewrite the example.
# ---------------------------------------------------------------------------

_FIXTURE_C = """\
# my-study

Hand-written prose above every region. This sentence has no other copy.

<!-- publishable:begin overview -->
The overview body, as `publishable new` wrote it.
<!-- publishable:end overview -->

Hand-written prose between the overview and the credentials.

<!-- publishable:begin credentials -->
### Required credentials

| Variable | Needed by |
|---|---|
| _(none yet — added as experiments declare them)_ | |
<!-- publishable:end credentials -->

An example of what a managed region looks like, quoted rather than declared:

````markdown
# some-other-study

<!-- publishable:begin experiments -->
## Experiments

```bash
uv run publishable run configs/x/config.yaml
```
<!-- publishable:end experiments -->
````

<!-- publishable:begin experiments -->
## Experiments

| Name | Template | Run |
|---|---|---|
| _(none yet — add one with `publishable generate experiment`)_ | | |
<!-- publishable:end experiments -->

Hand-written prose between the experiments and the templates.

<!-- publishable:begin templates -->
## Templates

_(none yet — add one with `publishable generate template`)_
<!-- publishable:end templates -->

Hand-written prose below every region, which is where a reader's own notes
live and which no generator may touch.
"""

_DECOY_LINES = (
    "````markdown",
    "# some-other-study",
    "<!-- publishable:begin experiments -->",
    "```bash",
    "uv run publishable run configs/x/config.yaml",
    "```",
    "<!-- publishable:end experiments -->",
    "````",
)


def test_fixture_c_finds_exactly_the_four_regions_and_not_the_fenced_decoy():
    """Both halves in one assertion set: the four real regions ARE found, and
    the fenced copy of `experiments` is NOT — which is the only way the
    `experiments` entry can be checked at all, since a fence-blind parser
    finds a region of that name too, just the wrong one."""
    found = regions(_FIXTURE_C)
    assert set(found) == set(MANAGED_REGIONS)

    lines = _FIXTURE_C.split("\n")
    start, stop = found["experiments"]
    assert lines[start - 1] == "<!-- publishable:begin experiments -->"
    assert lines[stop] == "<!-- publishable:end experiments -->"
    # The real region's body is the four-column table; the decoy's is a bash
    # block. Asserting the CONTENT of the span, not only its bounds, is what
    # separates the two same-named regions.
    assert "| Name | Template | Run |" in body_of(_FIXTURE_C, "experiments")
    assert "uv run publishable run configs/x/config.yaml" not in body_of(_FIXTURE_C, "experiments")
    # And the decoy sits ABOVE the real region, so a fence-blind parser fails
    # here rather than merely reporting a wider span.
    assert _FIXTURE_C.split("\n").index("````markdown") < start


@pytest.mark.parametrize("name", MANAGED_REGIONS)
def test_rewriting_a_region_with_its_own_body_is_the_identity(name: str):
    """The round trip: `rewrite(text, name, body_of(text, name)) == text`,
    byte for byte, including the trailing-newline convention. A whole-file
    comparison after a rewrite whose body DIFFERS is the companion below —
    on its own, this one would pass for a `rewrite` that returned its
    argument."""
    assert rewrite(_FIXTURE_C, name, body_of(_FIXTURE_C, name)) == _FIXTURE_C


@pytest.mark.parametrize("name", MANAGED_REGIONS)
def test_a_rewrite_replaces_the_span_and_moves_no_other_byte(name: str):
    """Asserted as a whole-file comparison against an expected string built by
    splicing the same lines independently — never as a substring check, which
    would pass for a rewrite that appended.

    The body genuinely differs from the one it replaces, so this cannot pass
    for a `rewrite` that is a no-op: the first assertion is that the file
    CHANGED.
    """
    start, stop = regions(_FIXTURE_C)[name]
    lines = _FIXTURE_C.split("\n")
    body = "REPLACED LINE ONE\nREPLACED LINE TWO\n"

    out = rewrite(_FIXTURE_C, name, body)

    assert out != _FIXTURE_C
    expected = "\n".join(lines[:start] + ["REPLACED LINE ONE", "REPLACED LINE TWO"] + lines[stop:])
    assert out == expected
    # The two marker lines survive, so the region can be rewritten again.
    assert f"<!-- publishable:begin {name} -->" in out
    assert f"<!-- publishable:end {name} -->" in out
    assert set(regions(out)) == set(MANAGED_REGIONS)


def test_hand_written_prose_and_the_fenced_decoy_survive_all_four_rewrites():
    """The survival case Ruling EE's cost sentence names: a user's prose
    outside a region has no other copy. All four regions are rewritten in one
    pass — the shape `docs` itself will use — and every line outside them is
    asserted present, including the eight lines of the fenced decoy, which a
    fence-blind rewriter consumes."""
    out = _FIXTURE_C
    for name in MANAGED_REGIONS:
        out = rewrite(out, name, f"the new {name} body\n")

    for prose in (
        "Hand-written prose above every region. This sentence has no other copy.",
        "Hand-written prose between the overview and the credentials.",
        "An example of what a managed region looks like, quoted rather than declared:",
        "Hand-written prose between the experiments and the templates.",
        "live and which no generator may touch.",
    ):
        assert prose in out, prose
    for line in _DECOY_LINES:
        assert line in out, line
    # The decoy is not merely present somewhere: its whole block is intact and
    # in order, which an assertion per line cannot say.
    assert "\n".join(_DECOY_LINES[:2]) in out
    # And the four bodies really were replaced — the control that stops every
    # assertion above from passing for a rewriter that did nothing.
    for name in MANAGED_REGIONS:
        assert body_of(out, name) == f"the new {name} body\n"


def test_the_trailing_newline_convention_is_untouched_in_both_directions():
    """A file ending in a newline keeps it; a file NOT ending in one does not
    gain one. Both, because a `+ "\\n"` in the rewriter passes the first."""
    assert rewrite(_FIXTURE_C, "overview", "x\n").endswith("touch.\n")
    without = _FIXTURE_C.rstrip("\n")
    out = rewrite(without, "overview", "x\n")
    assert not out.endswith("\n")
    assert out == without.replace(
        "The overview body, as `publishable new` wrote it.",
        "x",
    )


def test_an_empty_body_leaves_the_two_markers_adjacent():
    out = rewrite(_FIXTURE_C, "overview", "")
    assert "<!-- publishable:begin overview -->\n<!-- publishable:end overview -->" in out
    assert body_of(out, "overview") == ""
    assert regions(out)["overview"][0] == regions(out)["overview"][1]


# ---------------------------------------------------------------------------
# Fixture B — five malformed READMEs, one condition each. Each carries one
# WELL-FORMED region beside the broken one, so a refusal cannot pass by the
# file being empty; the `E-DOCS-NO-REGIONS` arm cannot carry one by
# definition, and carries a fenced decoy plus real prose instead, so it too
# is a file with something in it.
# ---------------------------------------------------------------------------

_WELL_FORMED = (
    "<!-- publishable:begin overview -->\nA real region, correctly closed.\n"
    "<!-- publishable:end overview -->\n"
)

_FIXTURE_B: dict[str, str] = {
    "begin-with-no-end": (
        f"# my-study\n\n{_WELL_FORMED}\n"
        "<!-- publishable:begin credentials -->\n### Required credentials\n"
    ),
    "end-with-no-begin": (f"# my-study\n\n{_WELL_FORMED}\n<!-- publishable:end templates -->\n"),
    "duplicate": (
        f"# my-study\n\n{_WELL_FORMED}\n"
        "<!-- publishable:begin overview -->\nA second one.\n"
        "<!-- publishable:end overview -->\n"
    ),
    "unknown": (
        f"# my-study\n\n{_WELL_FORMED}\n"
        "<!-- publishable:begin summary -->\nNot a region core manages.\n"
        "<!-- publishable:end summary -->\n"
    ),
    "no-regions": (
        "# my-study\n\nA README with prose and an example, and no managed region.\n\n"
        "````markdown\n<!-- publishable:begin overview -->\nquoted, not declared\n"
        "<!-- publishable:end overview -->\n````\n"
    ),
}

_FIXTURE_B_CODES = {
    "begin-with-no-end": "E-DOCS-REGION-UNBALANCED",
    "end-with-no-begin": "E-DOCS-REGION-UNBALANCED",
    "duplicate": "E-DOCS-REGION-DUPLICATE",
    "unknown": "E-DOCS-REGION-UNKNOWN",
    "no-regions": "E-DOCS-NO-REGIONS",
}

_FIXTURE_B_MESSAGES = {
    "begin-with-no-end": "`credentials` begins and never ends",
    "end-with-no-begin": "`templates` ends without ever beginning",
    "duplicate": "`overview` is opened twice",
    "unknown": "`summary` is not a region core manages",
    "no-regions": "declares none of the managed regions",
}


@pytest.mark.parametrize("condition", sorted(_FIXTURE_B))
def test_fixture_b_each_malformed_readme_is_its_own_named_refusal(condition: str):
    """Ruling EE: a region `docs` cannot find is a refusal, never a silence.

    Both the CODE and the MESSAGE are asserted — the message because it is
    what task 7 prints on stderr, and a refusal whose text does not name the
    region it could not parse leaves a user with nothing to fix. Asserting
    only the code would survive a message rewritten to name the wrong region.
    """
    with pytest.raises(ContractError) as raised:
        regions(_FIXTURE_B[condition])
    assert raised.value.code == _FIXTURE_B_CODES[condition]
    assert _FIXTURE_B_MESSAGES[condition] in str(raised.value)


@pytest.mark.parametrize("condition", sorted(set(_FIXTURE_B) - {"no-regions"}))
def test_fixture_b_the_well_formed_neighbour_is_what_makes_each_file_non_empty(
    condition: str,
):
    """The control for the arm above, and it is not an absence: the
    well-formed `overview` region each malformed file carries parses cleanly
    ON ITS OWN, so the refusal came from the broken region rather than from
    the file having nothing in it."""
    assert set(regions(f"# my-study\n\n{_WELL_FORMED}")) == {"overview"}
    assert _WELL_FORMED.rstrip("\n") in _FIXTURE_B[condition]


def test_the_no_regions_file_is_not_empty_and_its_fenced_markers_are_content():
    """The `no-regions` arm's own control. The file carries a fenced copy of a
    real region, so this refusal proves the fence exclusion holds on the
    refusal path too: a fence-blind parser finds `overview` here and does not
    refuse at all."""
    text = _FIXTURE_B["no-regions"]
    assert "publishable:begin overview" in text
    with pytest.raises(ContractError) as raised:
        regions(text)
    assert raised.value.code == "E-DOCS-NO-REGIONS"


def test_a_readme_holding_some_of_the_four_is_not_a_refusal():
    """The asymmetry Ruling EE turns on, and the honouring half of the
    refusals above: a README missing SOME regions is the ordinary state of
    every project scaffolded before this slice, and it parses. Only a README
    holding NONE of them refuses."""
    text = f"# my-study\n\n{_WELL_FORMED}\nprose\n"
    assert set(regions(text)) == {"overview"}
    assert set(regions(text)) != set(MANAGED_REGIONS)
    assert rewrite(text, "overview", "new\n") != text


def test_rewriting_a_region_this_readme_does_not_declare_is_a_refusal():
    """A rewriter that returned `text` unchanged for a region it could not
    find is indistinguishable from one that worked — Ruling EE's sentence
    applied to the rewriter rather than to the parser."""
    text = f"# my-study\n\n{_WELL_FORMED}"
    with pytest.raises(ContractError) as raised:
        rewrite(text, "templates", "body\n")
    assert raised.value.code == "E-DOCS-REGION-UNKNOWN"
    assert "declares no `templates` region" in str(raised.value)


def test_rewriting_a_name_core_does_not_manage_is_a_refusal():
    with pytest.raises(ContractError) as raised:
        rewrite(_FIXTURE_C, "summary", "body\n")
    assert raised.value.code == "E-DOCS-REGION-UNKNOWN"
    assert "not a region core manages" in str(raised.value)


def test_read_readme_returns_the_file_and_refuses_its_absence(tmp_path: Path):
    """Both directions in one test, because the refusal alone would pass for a
    `read_readme` that always raised."""
    with pytest.raises(ContractError) as raised:
        read_readme(tmp_path)
    assert raised.value.code == "E-DOCS-NO-README"
    assert "rewrites the managed regions" in str(raised.value)

    (tmp_path / "README.md").write_text(_FIXTURE_C)
    path, text = read_readme(tmp_path)
    assert path == tmp_path / "README.md"
    assert text == _FIXTURE_C


# ---------------------------------------------------------------------------
# The round trip on a file with NO trailing newline — the ordinary shape of a
# hand-edited README, and the one where a rewriter's line-splice convention
# and a body reader's can disagree without either being obviously wrong. The
# `templates` region is the LAST one in fixture C, so its span is the one
# whose `lines[stop:]` tail is shortest.
# ---------------------------------------------------------------------------

_FIXTURE_C_NO_TRAILING_NEWLINE = _FIXTURE_C.rstrip("\n")

_FIXTURE_C_BLANK_LAST_BODY_LINE = _FIXTURE_C.replace(
    "The overview body, as `publishable new` wrote it.\n",
    "The overview body, as `publishable new` wrote it.\n\n",
)


@pytest.mark.parametrize("name", MANAGED_REGIONS)
@pytest.mark.parametrize(
    "text",
    [_FIXTURE_C_NO_TRAILING_NEWLINE, _FIXTURE_C_BLANK_LAST_BODY_LINE],
    ids=["no-trailing-newline", "blank-last-body-line"],
)
def test_the_round_trip_holds_for_a_file_that_does_not_end_in_a_newline(text: str, name: str):
    """Both shapes a splice convention can get wrong: a file whose last byte is
    not a newline, and a region whose own last line is blank. The identity has
    to hold for every region of both, or `docs` moves a byte on a README
    somebody hand-edited."""
    assert rewrite(text, name, body_of(text, name)) == text
