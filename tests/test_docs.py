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


# ---------------------------------------------------------------------------
# H9d task 4 — the `credentials` region body, and `generate experiment`'s
# `required_env` merge.
#
# Two experiments, deliberately: one declaring two variables and one declaring
# ONE OF THE SAME TWO. A single experiment tests the write and not the merge —
# every row would have exactly one name in its second cell, so a builder that
# overwrote instead of unioning, and one that unioned, produce the same table.
# ---------------------------------------------------------------------------

_ALPHA_TEMPLATE = """\
from publishable import BaseTemplate, Param, register_template


@register_template("alpha_assay")
class AlphaAssayTemplate(BaseTemplate):
    required_env = ["ALPHA_TOKEN", "SHARED_TOKEN"]
    parameter_spec = {
        "alpha.threshold": Param(float, default=0.5, gt=0, lt=1, help="a threshold"),
    }
"""

_BETA_TEMPLATE = """\
from publishable import BaseTemplate, Param, register_template


@register_template("beta_assay")
class BetaAssayTemplate(BaseTemplate):
    required_env = ["SHARED_TOKEN"]
    parameter_spec = {
        "beta.threshold": Param(float, default=0.5, gt=0, lt=1, help="a threshold"),
    }
"""


def _project(tmp_path: Path, templates: dict[str, str] | None = None) -> Path:
    """A scaffolded project, with any local templates written before anything
    reads them. Never this repository: every helper here works in `tmp_path`,
    because `docs` walks up from `Path.cwd()` and pytest's own cwd is the
    `publishable` checkout — whose README is guard-pin arm B's subject."""
    from publishable.scaffold import scaffold_project

    root = scaffold_project(tmp_path / "my-study")
    for name, source in (templates or {}).items():
        (root / "templates").mkdir(exist_ok=True)
        (root / "templates" / f"{name}.py").write_text(source)
    return root


def _generate(root: Path, tmp_path: Path, name: str, template: str) -> Path:
    from publishable.generators.experiment import generate_experiment

    return generate_experiment(
        repo_root=root,
        name=name,
        template_name=template,
        input_dir=str(tmp_path / "input"),
        output_dir=str(tmp_path / "results"),
    )


def test_the_credentials_region_merges_two_experiments_declared_required_env(tmp_path: Path):
    """The merge, asserted as the WHOLE region body rather than as substrings:
    a row per variable in variable order, and the experiments needing it in the
    second cell in name order.

    `SHARED_TOKEN` is declared by both templates and gets ONE row naming both —
    which is the assertion a single-experiment fixture cannot make.
    """
    root = _project(tmp_path, {"alpha": _ALPHA_TEMPLATE, "beta": _BETA_TEMPLATE})
    _generate(root, tmp_path, "exp-one", "alpha_assay")
    _generate(root, tmp_path, "exp-two", "beta_assay")

    body = body_of((root / "README.md").read_text(), "credentials")
    assert body == (
        "### Required credentials\n"
        "\n"
        "| Variable | Needed by |\n"
        "|---|---|\n"
        "| `ALPHA_TOKEN` | `exp-one` |\n"
        "| `SHARED_TOKEN` | `exp-one`, `exp-two` |\n"
    )


def test_the_generator_moves_no_byte_outside_the_regions_it_merges(tmp_path: Path):
    """The other half of the same write, and the one a substring assertion
    cannot make: every byte of the README outside the two spans `generate
    experiment` merges is identical to what `publishable new` wrote. Compared
    as whole files against an independently spliced expectation, never as `in`.

    Both regions are named because task 5 added the second one to the same
    call. Splicing only `credentials` here would fail on the `experiments`
    table and hide which of the two moved.
    """
    root = _project(tmp_path, {"alpha": _ALPHA_TEMPLATE})
    before = (root / "README.md").read_text()
    _generate(root, tmp_path, "exp-one", "alpha_assay")
    after = (root / "README.md").read_text()

    assert after != before
    spliced = rewrite(before, "credentials", body_of(after, "credentials"))
    spliced = rewrite(spliced, "experiments", body_of(after, "experiments"))
    assert after == spliced


def test_a_project_with_no_experiments_renders_the_scaffolds_own_empty_row(tmp_path: Path):
    """The empty state is not a second literal: it is the row
    `readme_templates/README.md.tmpl` already carries, so refreshing a freshly
    scaffolded project rewrites the file to ITSELF, byte for byte.

    That identity is the honouring half of Ruling EE from the other side. A
    populated form that could not degenerate to the scaffold's own line would
    mean the scaffold documents a state the generator never writes — and the
    round trip is asserted on the whole file, so it cannot pass by the
    comparison being a substring of itself.
    """
    from publishable.docs import CREDENTIALS_EMPTY_ROW, credentials_body, refresh

    root = _project(tmp_path)
    before = (root / "README.md").read_text()
    assert CREDENTIALS_EMPTY_ROW in body_of(before, "credentials")
    assert credentials_body(root) + "\n" == body_of(before, "credentials")

    rewritten, absent = refresh(root, ("credentials",))
    assert (rewritten, absent) == (["credentials"], [])
    assert (root / "README.md").read_text() == before


def test_an_experiment_whose_template_is_installed_contributes_a_row_saying_so(
    tmp_path: Path, installed
):
    """Correction 21: an installed template's class is `None` by construction —
    core resolves an entry-point name from package metadata without importing
    the package — so its `required_env` cannot be read. The region says so, in
    a row, naming the experiment, the template and the distribution.

    A **silence** is the fault this exists to exclude: a table that simply
    omitted the experiment is indistinguishable from a template declaring no
    credentials at all. So the positive control is in the same test — a local
    template's real row is present beside it.
    """
    installed("dist-assay", "0.3.1", {"publishable.templates": {"far_assay": "far.t:T"}})
    root = _project(tmp_path, {"alpha": _ALPHA_TEMPLATE})
    _generate(root, tmp_path, "exp-one", "alpha_assay")
    # `generate experiment` refuses an installed template outright
    # (`E-TEMPLATE-INSTALLED-UNSUPPORTED`), so the config that names one is
    # written directly here: the case is a repository that ACQUIRES the plugin
    # later, or a config a collaborator wrote against a build that resolves it.
    (root / "configs" / "exp-far").mkdir()
    (root / "configs" / "exp-far" / "config.yaml").write_text(
        "name: exp-far\nexperiment_type: far_assay\n"
    )
    from publishable.docs import credentials_body

    body = credentials_body(root)
    assert "| `ALPHA_TOKEN` | `exp-one` |" in body
    assert (
        "| _(unknown)_ | `exp-far` — its template `far_assay` is installed "
        "(dist-assay 0.3.1), so its `required_env` is not readable "
        "(`E-TEMPLATE-INSTALLED-UNSUPPORTED`) |"
    ) in body


def test_a_config_naming_no_template_core_can_resolve_also_gets_a_row(tmp_path: Path):
    """The two other unreadable shapes, for the same reason and in the same
    place: a config declaring no `experiment_type` core can read, and one
    naming a template nothing claims. Both would otherwise be silences."""
    from publishable.docs import credentials_body

    root = _project(tmp_path)
    for name, text in (
        ("exp-blank", "name: exp-blank\n"),
        ("exp-ghost", "name: exp-ghost\nexperiment_type: nobody_registers_this\n"),
    ):
        (root / "configs" / name).mkdir(parents=True)
        (root / "configs" / name / "config.yaml").write_text(text)

    body = credentials_body(root)
    assert (
        "| _(unknown)_ | `exp-blank` — its `config.yaml` declares no readable "
        "`experiment_type`, so no template's `required_env` could be read |"
    ) in body
    assert (
        "| _(unknown)_ | `exp-ghost` — no template claims the name "
        "`nobody_registers_this`, so no `required_env` could be read |"
    ) in body
    # And the empty row is NOT there: rows exist, so the "none yet" line would
    # be a false claim beside them.
    assert "_(none yet" not in body


def test_generate_experiment_survives_a_readme_it_cannot_rewrite_and_names_it(
    tmp_path: Path, capsys
):
    """The generator's files are on disk BEFORE the merge, and the merge raises
    nothing: a project scaffolded before H9d declares no `credentials` region,
    and a README that cannot be rewritten may not cost the caller the package
    and the config it just asked for.

    Both directions in one test — the note is printed AND the two artifacts
    exist. A test asserting only that nothing raised would pass for a generator
    that wrote nothing at all.
    """
    root = _project(tmp_path, {"alpha": _ALPHA_TEMPLATE})
    readme = root / "README.md"
    # An older README: one well-formed region, and no `credentials` one.
    readme.write_text(
        "# my-study\n\n<!-- publishable:begin overview -->\nprose\n"
        "<!-- publishable:end overview -->\n"
    )
    capsys.readouterr()
    config = _generate(root, tmp_path, "exp-one", "alpha_assay")

    captured = capsys.readouterr()
    assert captured.err == (
        "note: README.md declares no `credentials` region, so nothing was "
        "written there — a region is never created, only rewritten\n"
        "note: README.md declares no `experiments` region, so nothing was "
        "written there — a region is never created, only rewritten\n"
    )
    assert config.is_file()
    assert (root / "src" / "exp_one" / "experiment.py").is_file()
    assert readme.read_text() == (
        "# my-study\n\n<!-- publishable:begin overview -->\nprose\n"
        "<!-- publishable:end overview -->\n"
    )


def test_a_malformed_readme_is_named_by_its_code_and_still_costs_the_generator_nothing(
    tmp_path: Path, capsys
):
    """The other arm of the same guarantee: a structurally broken README is one
    of `docs`' five refusals, and `merge_into_readme` turns it into a printed
    note carrying the code rather than into an exception the generator dies
    on. The safety claim in that function's docstring is what this makes fail."""
    root = _project(tmp_path, {"alpha": _ALPHA_TEMPLATE})
    (root / "README.md").write_text("# my-study\n\n<!-- publishable:begin credentials -->\nprose\n")
    capsys.readouterr()
    config = _generate(root, tmp_path, "exp-one", "alpha_assay")

    err = capsys.readouterr().err
    assert "E-DOCS-REGION-UNBALANCED" in err
    assert "begins and never ends" in err
    assert config.is_file()


# ---------------------------------------------------------------------------
# H9d task 5 — the `experiments` region body, and `generate experiment`'s row
# merge.
# ---------------------------------------------------------------------------


def test_the_experiments_region_carries_its_own_heading_and_one_row_per_config(tmp_path: Path):
    """`## Experiments` is INSIDE the region as of task 3, so the body carries
    the heading; a row per `configs/<name>/config.yaml` in name order, with the
    `Run` cell holding the invocation rather than a description.

    Asserted as the whole body: a substring check on one row cannot see a
    missing heading, a lost column, or a second row that should not be there.
    """
    root = _project(tmp_path, {"alpha": _ALPHA_TEMPLATE, "beta": _BETA_TEMPLATE})
    _generate(root, tmp_path, "exp-two", "beta_assay")
    _generate(root, tmp_path, "exp-one", "alpha_assay")

    body = body_of((root / "README.md").read_text(), "experiments")
    assert body == (
        "## Experiments\n"
        "\n"
        "| Name | Template | Run |\n"
        "|---|---|---|\n"
        "| `exp-one` | `alpha_assay` | `uv run publishable run configs/exp-one/config.yaml` |\n"
        "| `exp-two` | `beta_assay` | `uv run publishable run configs/exp-two/config.yaml` |\n"
    )


def test_a_second_experiment_gains_exactly_one_row_and_moves_no_other_byte(tmp_path: Path):
    """The plan's own mutation for this task, written as the assertion it
    names: the region gains **exactly one** row, and every byte outside it is
    unchanged — compared as a whole file against an independently spliced
    expectation rather than as a substring.

    "Outside" means outside the two regions this generator merges — and the
    `credentials` one really does move here, because the second experiment's
    template declares `SHARED_TOKEN`, which the first's already did, so that
    variable's `Needed by` cell gains a name. Both are spliced from the
    after-state and the whole file is then compared, so a byte moved anywhere
    else — a heading, the Setup fence, the `Reproducing` section — fails here.
    """
    root = _project(tmp_path, {"alpha": _ALPHA_TEMPLATE, "beta": _BETA_TEMPLATE})
    _generate(root, tmp_path, "exp-one", "alpha_assay")
    before = (root / "README.md").read_text()

    _generate(root, tmp_path, "exp-two", "beta_assay")
    after = (root / "README.md").read_text()

    added = [
        line
        for line in body_of(after, "experiments").splitlines()
        if line not in body_of(before, "experiments").splitlines()
    ]
    assert added == [
        "| `exp-two` | `beta_assay` | `uv run publishable run configs/exp-two/config.yaml` |"
    ]
    assert body_of(after, "credentials") == body_of(before, "credentials").replace(
        "| `SHARED_TOKEN` | `exp-one` |", "| `SHARED_TOKEN` | `exp-one`, `exp-two` |"
    )
    spliced = rewrite(before, "experiments", body_of(after, "experiments"))
    spliced = rewrite(spliced, "credentials", body_of(after, "credentials"))
    assert after == spliced


def test_the_experiments_empty_state_is_the_scaffolds_own_row(tmp_path: Path):
    """The same degeneracy the `credentials` region has: refreshing a project
    with no experiments rewrites the scaffolded README to itself, byte for
    byte, so the empty row is not a second literal maintained beside the
    scaffold's."""
    from publishable.docs import EXPERIMENTS_EMPTY_ROW, experiments_body, refresh

    root = _project(tmp_path)
    before = (root / "README.md").read_text()
    assert EXPERIMENTS_EMPTY_ROW in body_of(before, "experiments")
    assert experiments_body(root) + "\n" == body_of(before, "experiments")

    assert refresh(root, ("experiments", "credentials")) == (["experiments", "credentials"], [])
    assert (root / "README.md").read_text() == before


def test_a_config_that_declares_no_readable_template_still_gets_its_row(tmp_path: Path):
    """A row with `_(unknown)_` in the Template cell, never a dropped row: the
    experiment exists, `configs/<name>/config.yaml` is on disk, and a table
    that omitted it would tell a reader this project has no such experiment."""
    from publishable.docs import experiments_body

    root = _project(tmp_path)
    (root / "configs" / "exp-blank").mkdir(parents=True)
    (root / "configs" / "exp-blank" / "config.yaml").write_text("name: exp-blank\n")

    assert (
        "| `exp-blank` | _(unknown)_ | `uv run publishable run configs/exp-blank/config.yaml` |"
    ) in experiments_body(root)


def test_both_region_bodies_are_in_name_order_whatever_the_filesystem_answers(
    tmp_path: Path, monkeypatch
):
    """The replacement for a mutation that was **blind**: dropping the
    `sorted()` that used to sit on the `configs/*/config.yaml` glob left the
    full suite green, because this machine's directory order already agrees
    with name order. A sort a fixture cannot disagree with is a sort no
    assertion can see.

    So the ordering decision moved to `experiments()`, and this hands it a
    REVERSED list — the one arrangement that distinguishes name order from
    discovery order for two elements — and asserts both region bodies come out
    in name order regardless.
    """
    import publishable.docs as docs_module

    root = _project(tmp_path, {"alpha": _ALPHA_TEMPLATE, "beta": _BETA_TEMPLATE})
    _generate(root, tmp_path, "exp-one", "alpha_assay")
    _generate(root, tmp_path, "exp-two", "beta_assay")

    # Reversed by NAME, not by whatever the filesystem returned. Until
    # 2026-08-27 this was `list(reversed(real(r)))` and the assertion below
    # expected `["exp-two", "exp-one"]` — which holds only where the raw
    # directory order already happens to be `exp-one, exp-two`. On a Linux
    # runner it is not, and this test failed: its own precondition depended on
    # the filesystem the test exists to defeat. Sorting descending by name
    # hands `experiments()` the reversed arrangement on every filesystem,
    # which is what the docstring above claims.
    real = docs_module.config_paths
    monkeypatch.setattr(
        docs_module,
        "config_paths",
        lambda r: sorted(real(r), key=lambda path: path.parent.name, reverse=True),
    )
    assert [path.parent.name for path in docs_module.config_paths(root)] == [
        "exp-two",
        "exp-one",
    ]

    rows = [
        line for line in docs_module.experiments_body(root).splitlines() if line.startswith("| `")
    ]
    assert [row.split("`")[1] for row in rows] == ["exp-one", "exp-two"]
    assert "| `SHARED_TOKEN` | `exp-one`, `exp-two` |" in docs_module.credentials_body(root)


# ---------------------------------------------------------------------------
# H9d task 6 — the `templates` region body, and `generate template`'s write.
#
# The fixture declares the FOUR shapes whose rendering differs, in one
# template, because a spec with one parameter tests one branch: a required
# parameter (no `default`), a `nullable=True` `default=None`, one with
# `choices` AND `requires_env`, and a `list` with `item_type`.
# ---------------------------------------------------------------------------

_SHAPES_TEMPLATE = """\
from publishable import BaseTemplate, Param, register_template


@register_template("shapes_assay")
class ShapesAssayTemplate(BaseTemplate):
    field_convention = "wet_lab"
    default_repeats = 3
    required_env = ["SHAPES_TOKEN"]
    parameter_spec = {
        "assay.model": Param(str, help="Instrument model identifier"),
        "assay.calibration": Param(
            str, default=None, nullable=True, help="Calibration id, or null"
        ),
        "assay.vendor": Param(
            str,
            default="vendor_a",
            choices=["vendor_a", "vendor_b"],
            requires_env={"vendor_a": [], "vendor_b": ["VENDOR_B_TOKEN"]},
            help="Which vendor's API the readings come through",
        ),
        "assay.wells": Param(
            list, default=[], item_type=int, min_items=0, max_items=96,
            help="Which wells to read",
        ),
    }
"""


def test_the_templates_region_renders_the_four_shapes_from_parameter_spec(tmp_path: Path):
    """The whole sub-section, asserted as bytes: the heading, the convention
    line, the five-column table with one row per parameter in DECLARATION
    order, and the `Required credentials` line.

    Each of the four rows is a different rendering branch — `required` with no
    default, a nullable `null` default, a `choices` list carrying its own
    `requires_env` note and escaped pipes, and a `list` with an item type and
    both bounds. A one-parameter fixture would exercise one of them.
    """
    from publishable.docs import templates_body

    root = _project(tmp_path, {"shapes": _SHAPES_TEMPLATE})
    assert templates_body(root) == (
        "## Templates\n"
        "\n"
        "### `shapes_assay`\n"
        "\n"
        "Convention class `wet_lab` · default repeats 3 · naming "
        "`^[a-z0-9]+(-[a-z0-9]+)*$`\n"
        "\n"
        "| Parameter | Type | Default | Constraints | Description |\n"
        "|---|---|---|---|---|\n"
        "| `assay.model` | string | — | required | Instrument model identifier |\n"
        "| `assay.calibration` | string | `null` | nullable | Calibration id, or null |\n"
        "| `assay.vendor` | string | `vendor_a` | choices: vendor_a \\| vendor_b "
        "(needs VENDOR_B_TOKEN) | Which vendor's API the readings come through |\n"
        "| `assay.wells` | list | `[]` | list of integer; at least 0 items; at most 96 "
        "items | Which wells to read |\n"
        "\n"
        "**Required credentials:** `SHAPES_TOKEN`"
    )


def test_the_templates_region_does_not_list_cores_own_generic(tmp_path: Path):
    """The scaffolded empty state — *"none yet — add one with `publishable
    generate template`"* — is what decides this: a fresh project that listed a
    template nobody added would make that line false the moment it was written.

    Both directions in one test, because an assertion that `generic` is absent
    passes identically if the builder returned nothing at all: the fresh
    project degenerates to the scaffold's own line, and the same project with
    one local template lists that one and still not `generic`.
    """
    from publishable.docs import TEMPLATES_EMPTY_LINE, refresh, templates_body

    root = _project(tmp_path)
    before = (root / "README.md").read_text()
    assert TEMPLATES_EMPTY_LINE in body_of(before, "templates")
    assert templates_body(root) + "\n" == body_of(before, "templates")
    assert refresh(root, ("templates",)) == (["templates"], [])
    assert (root / "README.md").read_text() == before

    (root / "templates").mkdir(exist_ok=True)
    (root / "templates" / "shapes.py").write_text(_SHAPES_TEMPLATE)
    populated = templates_body(root)
    assert "### `shapes_assay`" in populated
    assert "generic" not in populated
    assert TEMPLATES_EMPTY_LINE not in populated


def test_an_installed_template_gets_a_named_line_and_no_table(tmp_path: Path, installed):
    """Correction 21: its class is `None`, so there is no `parameter_spec` to
    read without importing the package — which is the one thing every other
    surface in this build refuses to do. It gets a LINE saying so, citing the
    code, never a blank and never an omission.

    The positive control is in the same test: a local template's real table is
    rendered beside it, so this cannot pass for a builder that emitted no
    tables at all.
    """
    installed("dist-assay", "0.3.1", {"publishable.templates": {"far_assay": "far.t:T"}})
    from publishable.docs import templates_body

    root = _project(tmp_path, {"shapes": _SHAPES_TEMPLATE})
    body = templates_body(root)

    assert "### `far_assay`\n\nInstalled, provided by `dist-assay 0.3.1` — " in body
    assert "`E-TEMPLATE-INSTALLED-UNSUPPORTED`" in body
    # The line, and nothing else: no convention line and no table for it. The
    # local template's table proves the assertion is not vacuous.
    far = body.split("### `far_assay`", 1)[1].split("### `", 1)[0]
    assert "| Parameter | Type |" not in far
    assert "Convention class" not in far
    assert "| `assay.model` | string | — | required |" in body


def test_generate_template_writes_its_own_parameter_table_into_the_region(tmp_path: Path, capsys):
    """The generator's half. The table is read back out of the file it just
    wrote, through discovery, so it is derived from `parameter_spec` rather
    than composed from the stub's own text — and the region is the ONLY thing
    that moves, asserted as a whole-file comparison.
    """
    from publishable.generators.template import generate_template

    root = _project(tmp_path)
    before = (root / "README.md").read_text()
    capsys.readouterr()
    generate_template(repo_root=root, name="my_assay")

    after = (root / "README.md").read_text()
    assert capsys.readouterr().err == ""
    assert body_of(after, "templates") == (
        "## Templates\n"
        "\n"
        "### `my_assay`\n"
        "\n"
        "Convention class `generic` · default repeats 1 · naming "
        "`^[a-z0-9]+(-[a-z0-9]+)*$`\n"
        "\n"
        "| Parameter | Type | Default | Constraints | Description |\n"
        "|---|---|---|---|---|\n"
        "| `my_assay.threshold` | float | `0.5` | > 0; < 1 | TODO: replace with this "
        "experiment type's own parameters |\n"
    )
    assert after == rewrite(before, "templates", body_of(after, "templates"))


def test_generate_template_survives_a_readme_with_no_templates_region(tmp_path: Path, capsys):
    """A project scaffolded before H9d declares no `templates` region — the
    region task 3 added. The stub is still written and the absence is NAMED,
    both asserted here, because a test that only checked nothing raised would
    pass for a generator that wrote nothing at all."""
    from publishable.generators.template import generate_template

    root = _project(tmp_path)
    (root / "README.md").write_text(
        "# my-study\n\n<!-- publishable:begin overview -->\nprose\n"
        "<!-- publishable:end overview -->\n"
    )
    capsys.readouterr()
    path = generate_template(repo_root=root, name="my_assay")

    assert capsys.readouterr().err == (
        "note: README.md declares no `templates` region, so nothing was "
        "written there — a region is never created, only rewritten\n"
    )
    assert path.is_file()
    assert "parameter_spec" in path.read_text()


# ---------------------------------------------------------------------------
# H9d task 7 — `publishable docs`' dispatch.
#
# Every arm here runs in `tmp_path`. `docs` walks up from `Path.cwd()` and
# pytest's own cwd is the `publishable` checkout, whose README is guard-pin
# arm B's subject with an editor this task is not — so a `monkeypatch.chdir`
# is not tidiness here, it is the guard.
# ---------------------------------------------------------------------------


def _older_readme(root: Path) -> str:
    """A README as `publishable new` wrote it BEFORE H9d: two of the four
    regions, and hand-written prose outside them."""
    text = (
        "# my-study\n"
        "\n"
        "Hand-written prose with no other copy.\n"
        "\n"
        "<!-- publishable:begin overview -->\n"
        "something a person typed over the generated overview\n"
        "<!-- publishable:end overview -->\n"
        "\n"
        "## Experiments\n"
        "\n"
        "<!-- publishable:begin experiments -->\n"
        "None yet.\n"
        "<!-- publishable:end experiments -->\n"
    )
    (root / "README.md").write_text(text)
    return text


def test_docs_rewrites_what_it_finds_and_names_what_it_did_not(tmp_path: Path, monkeypatch, capsys):
    """Ruling EE's asymmetry, in both directions and in one test.

    A README missing two of the four is NOT a refusal — it is the ordinary
    state of every project scaffolded before this slice. So: exit `0`, the two
    it found actually rewritten (their bytes moved, and to the computed
    bodies), the two it did not NAMED on stdout, and every byte outside the two
    spans untouched — the hand-written prose included, which is the thing the
    markers exist to protect.
    """
    from publishable.cli import main
    from publishable.docs import experiments_body, overview_body

    root = _project(tmp_path)
    before = _older_readme(root)
    monkeypatch.chdir(root)

    assert main(["docs"]) == 0
    out = capsys.readouterr().out
    after = (root / "README.md").read_text()

    assert out == (
        "README.md: rewrote `overview`, `experiments`\n"
        "README.md declares no `credentials` region, so nothing was written "
        "there — a region is never created, only rewritten\n"
        "README.md declares no `templates` region, so nothing was written "
        "there — a region is never created, only rewritten\n"
    )
    assert after != before
    assert body_of(after, "overview") == overview_body(root) + "\n"
    assert body_of(after, "experiments") == experiments_body(root) + "\n"
    spliced = rewrite(before, "overview", body_of(after, "overview"))
    spliced = rewrite(spliced, "experiments", body_of(after, "experiments"))
    assert after == spliced
    assert "Hand-written prose with no other copy." in after


def test_docs_on_a_freshly_scaffolded_project_names_all_four_and_moves_no_byte(
    tmp_path: Path, monkeypatch, capsys
):
    """The idempotence the four builders' empty states buy: every region a
    fresh `publishable new` writes is exactly what `docs` computes, so the file
    is byte-identical afterward.

    The stdout line is asserted BESIDE that, because *"the file did not
    change"* is also what a command that did nothing produces — which is the
    fault Ruling EE exists for.
    """
    from publishable.cli import main

    root = _project(tmp_path)
    before = (root / "README.md").read_text()
    monkeypatch.chdir(root)

    assert main(["docs"]) == 0
    assert capsys.readouterr().out == (
        "README.md: rewrote `overview`, `credentials`, `experiments`, `templates`\n"
    )
    assert (root / "README.md").read_text() == before


def test_docs_picks_up_an_experiment_and_a_template_added_since_the_last_write(
    tmp_path: Path, monkeypatch, capsys
):
    """The positive control for the test above, and the command's whole
    purpose: a repository whose README is stale is brought current — a table
    row for the experiment, a sub-section for the template — by `docs` alone,
    with no generator involved."""
    from publishable.cli import main

    root = _project(tmp_path, {"shapes": _SHAPES_TEMPLATE})
    (root / "configs" / "exp-one").mkdir(parents=True)
    (root / "configs" / "exp-one" / "config.yaml").write_text(
        "name: exp-one\nexperiment_type: shapes_assay\n"
    )
    monkeypatch.chdir(root)

    assert main(["docs"]) == 0
    capsys.readouterr()
    text = (root / "README.md").read_text()
    assert (
        "| `exp-one` | `shapes_assay` | `uv run publishable run configs/exp-one/config.yaml` |"
    ) in body_of(text, "experiments")
    assert "### `shapes_assay`" in body_of(text, "templates")
    assert "| `SHAPES_TOKEN` | `exp-one` |" in body_of(text, "credentials")


@pytest.mark.parametrize(
    "condition,code,fragment",
    [
        (
            "<!-- publishable:begin credentials -->\nbody\n",
            "E-DOCS-REGION-UNBALANCED",
            "begins and never ends",
        ),
        (
            "<!-- publishable:begin overview -->\na\n<!-- publishable:end overview -->\n"
            "<!-- publishable:begin overview -->\nb\n<!-- publishable:end overview -->\n",
            "E-DOCS-REGION-DUPLICATE",
            "is opened twice",
        ),
        (
            "<!-- publishable:begin summary -->\nb\n<!-- publishable:end summary -->\n",
            "E-DOCS-REGION-UNKNOWN",
            "is not a region core manages",
        ),
        (
            "no region here at all\n",
            "E-DOCS-NO-REGIONS",
            "declares none of the managed regions",
        ),
    ],
)
def test_docs_refuses_a_readme_whose_bound_it_cannot_compute(
    tmp_path: Path, monkeypatch, capsys, condition: str, code: str, fragment: str
):
    """Exit `1`, the CODE and the stderr LINE — never the exit code alone,
    which a `return EXIT_OK` mutation would leave alone in one of these arms
    and which says nothing about whether the user was told what to fix.

    And the file is asserted UNCHANGED: a refusal that had already rewritten
    half the regions before deciding would pass every assertion above it.
    """
    from publishable.cli import main

    root = _project(tmp_path)
    (root / "README.md").write_text(condition)
    monkeypatch.chdir(root)

    assert main(["docs"]) == 1
    captured = capsys.readouterr()
    assert code in captured.err
    assert fragment in captured.err
    assert captured.out == ""
    assert (root / "README.md").read_text() == condition


def test_docs_refuses_a_repository_with_no_readme(tmp_path: Path, monkeypatch, capsys):
    """The fifth refusal. `docs` never CREATES a README — one `publishable new`
    did not write is a file this command has no template for, and writing one
    would be writing outside every region."""
    from publishable.cli import main

    root = _project(tmp_path)
    (root / "README.md").unlink()
    monkeypatch.chdir(root)

    assert main(["docs"]) == 1
    err = capsys.readouterr().err
    assert "E-DOCS-NO-README" in err
    # The path column names the DIRECTORY, not a `README.md` the message beside
    # it says does not exist — the four structural refusals name the file
    # because there is one, and this refusal is the absence of it.
    assert f"E-DOCS-NO-README     {root}\n" in err
    assert f"{root / 'README.md'}\n" not in err
    assert not (root / "README.md").exists()


def test_docs_outside_a_repository_is_a_rendered_diagnostic_not_a_traceback(
    tmp_path: Path, monkeypatch, capsys
):
    """`E-GIT-NO-REPO`, caught **by code** and re-reported through this
    command's own `Collector` at exit `1` — never raised into `main`, whose
    handler holds no collector and applies no redaction pass.

    Asserted on the `Collector`'s own rendering (`  error   <code>` and the
    trailing problem count), because `main`'s bare handler prints a line that
    also contains the code: a substring check on the code alone cannot tell the
    two printers apart.
    """
    from publishable.cli import main

    here = tmp_path / "not-a-repo"
    here.mkdir()
    monkeypatch.chdir(here)

    assert main(["docs"]) == 1
    err = capsys.readouterr().err
    assert err.startswith("  error   E-GIT-NO-REPO")
    assert "1 problem (1 error, 0 warnings)" in err
    assert "rewrites the managed regions of a repository's own README" in err


_LEAKY_TEMPLATE = """\
import os

from publishable import BaseTemplate, register_template


@register_template("leaky_assay")
class LeakyAssayTemplate(BaseTemplate):
    required_env = ["DOCS_TOKEN"]


raise RuntimeError("connecting with " + os.environ["DOCS_TOKEN"])
"""


def test_a_credential_a_local_template_raises_with_is_redacted(tmp_path: Path, monkeypatch, capsys):
    """`docs` runs user code — `_claims` imports every `templates/*.py` — so a
    template that raises can put an environment value in its message, and
    `main`'s own handler would print it verbatim. This command prints through
    its own credential-bearing `Collector` instead.

    Both directions: the redaction marker naming the variable IS present, and
    the value is NOT — a test asserting only the absence passes if the whole
    message went missing.
    """
    from publishable.cli import main

    monkeypatch.setenv("DOCS_TOKEN", "sk-do-not-print-this")
    root = _project(tmp_path, {"leaky": _LEAKY_TEMPLATE})
    monkeypatch.chdir(root)

    assert main(["docs"]) == 1
    err = capsys.readouterr().err
    assert "E-TEMPLATE-LOAD" in err
    assert "<redacted:DOCS_TOKEN>" in err
    assert "sk-do-not-print-this" not in err


def test_docs_takes_no_argument_and_no_flag(tmp_path: Path, monkeypatch, capsys):
    """*Operation commands take paths and nothing else* — and the argument
    `docs/reference.md` § Operation commands gives this one is *(none)*, so
    both halves of the arity rule are the same check: an argument and a flag
    are both `rest`.

    Pinned in the state task 13 leaves behind, with `NOT_BUILT_COMMANDS`
    emptied, because until then the shipped dictionary answers first — which
    the companion below pins from the other side. `main` is called rather than
    `_dispatch`, so the whole invocation path is what is measured.
    """
    import publishable.cli as cli_module
    from publishable.cli import main

    root = _project(tmp_path)
    monkeypatch.chdir(root)
    monkeypatch.setattr(cli_module, "NOT_BUILT_COMMANDS", {})

    for argv in (["docs", "somewhere"], ["docs", "--force"], ["docs", "a", "b"]):
        assert main(argv) == 2, argv
        assert capsys.readouterr().err == "`docs` takes no arguments and no flags\n"
    # The honouring half in the same state: with no arguments it really runs.
    assert main(["docs"]) == 0
    assert capsys.readouterr().out.startswith("README.md: rewrote")


# ---------------------------------------------------------------------------
# H9d task 8 — `publishable list-templates`.
#
# These live beside `docs`' arms rather than in `tests/test_cli.py` because
# they reuse this file's project fixture and because the two commands share one
# renderer (`docs.template_details`) — a rendering asserted in one file and
# built in another is how two copies of one table start.
#
# Fixture D (design § 9): `aaa_probe` and `zzz_probe`, ONE ON EACH SIDE of
# core's `generic` in sort order, plus an installed claim between them. Locals
# on both sides is what makes name order, provenance order and discovery order
# three different answers — a decoy that sorts on one side only rules out
# `first`-wins and lets `last`-wins through, which this repo has been bitten by
# twice.
# ---------------------------------------------------------------------------

_AAA_PROBE = """\
from publishable import BaseTemplate, Param, register_template


@register_template("aaa_probe")
class AaaProbeTemplate(BaseTemplate):
    required_env = ["AAA_TOKEN"]
    parameter_spec = {"aaa.n": Param(int, default=3, ge=1, help="how many")}
"""

_ZZZ_PROBE = """\
from publishable import BaseTemplate, Param, register_template


@register_template("zzz_probe")
class ZzzProbeTemplate(BaseTemplate):
    parameter_spec = {"zzz.label": Param(str, help="a label")}
"""

#: A module that RECORDS ITS OWN IMPORT. Mutation 7's assertion — that
#: `list-templates` reads an installed claim from package metadata and imports
#: nothing — cannot be made from an absence of output: a command that printed
#: nothing at all would satisfy it. This leaves a file behind if it is ever
#: executed, and the test proves the sentinel works before trusting its silence.
_SENTINEL_MODULE = """\
import os
from pathlib import Path

from publishable import BaseTemplate, register_template


Path(os.environ["SENTINEL_MARKER"]).write_text("imported")


# Named `Mmm` to match the entry point's own `sentinel_tpl:Mmm` target, so a
# mutation that DOES import this module succeeds and is then caught by the
# marker above rather than by an AttributeError. A mutation caught by a crash
# proves the import happened and nothing about the property.
@register_template("mmm_installed")
class Mmm(BaseTemplate):
    parameter_spec = {}
"""


def _fixture_d(tmp_path: Path, installed, monkeypatch) -> Path:
    """Two local templates on either side of `generic`, plus an installed claim
    whose module records its own import."""
    import sys

    # The sentinel's module NAME is what `sys.modules` caches, and each call to
    # `installed` writes a fresh copy of it in a fresh directory — so a second
    # test in the same session would import nothing, the body would not run, and
    # the marker would stay absent no matter what the command did. Measured, not
    # anticipated: with this line missing, the mutation that makes
    # `list-templates` import an installed template left this file's own
    # no-import arm GREEN, because an earlier arm had already imported the
    # sentinel. The entry is dropped so every arm's import is a real one.
    monkeypatch.delitem(sys.modules, "sentinel_tpl", raising=False)
    site = installed(
        "dist-assay", "0.3.1", {"publishable.templates": {"mmm_installed": "sentinel_tpl:Mmm"}}
    )
    (site / "sentinel_tpl.py").write_text(_SENTINEL_MODULE)
    monkeypatch.setenv("SENTINEL_MARKER", str(tmp_path / "sentinel-was-imported"))
    return _project(tmp_path, {"aaa_probe": _AAA_PROBE, "zzz_probe": _ZZZ_PROBE})


def test_list_templates_prints_every_claim_in_name_order(
    tmp_path: Path, installed, monkeypatch, capsys
):
    """Every claim `_claims` returns — core's, this project's own, and the
    installed one — in NAME order, each with its provenance and its provider.

    The headings are asserted as a SEQUENCE, not as memberships: with a local
    template on each side of `generic` and an installed claim between them, the
    reverse of this list, discovery order (core, installed, local) and
    insertion order are three different sequences, so no one of them can pass
    for another.
    """
    from publishable.cli import main

    root = _fixture_d(tmp_path, installed, monkeypatch)
    monkeypatch.chdir(root)

    assert main(["list-templates"]) == 0
    out = capsys.readouterr().out
    assert [line for line in out.splitlines() if line.startswith("### ")] == [
        "### `aaa_probe`",
        "### `generic`",
        "### `mmm_installed`",
        "### `zzz_probe`",
    ]
    assert "local · provider" in out
    assert "core · provider `publishable.templates.builtin.generic.GenericTemplate`" in out
    assert "| `aaa.n` | integer | `3` | >= 1 | how many |" in out
    assert "**Required credentials:** `AAA_TOKEN`" in out


def test_an_installed_claim_prints_a_named_absence_and_imports_nothing(
    tmp_path: Path, installed, monkeypatch, capsys
):
    """Correction 21, and the invariant behind it: core resolves an installed
    template's name from package metadata **without importing the package**, so
    this command cannot print its spec and says so rather than printing a
    blank.

    The no-import claim is made by a sentinel module that records its own
    import — never by an absence of output, which a command that printed
    nothing would also satisfy. The sentinel is PROVEN to work in the same
    test, by importing it directly afterward: without that control, a broken
    sentinel and a correct command are indistinguishable.
    """
    import importlib
    import sys

    from publishable.cli import main

    root = _fixture_d(tmp_path, installed, monkeypatch)
    marker = tmp_path / "sentinel-was-imported"
    monkeypatch.chdir(root)

    assert main(["list-templates"]) == 0
    out = capsys.readouterr().out
    assert "### `mmm_installed`\n\nInstalled, provided by `dist-assay 0.3.1` — " in out
    assert "`E-TEMPLATE-INSTALLED-UNSUPPORTED`" in out
    installed_block = out.split("### `mmm_installed`", 1)[1].split("### `", 1)[0]
    assert "| Parameter | Type |" not in installed_block
    assert "Convention class" not in installed_block
    assert not marker.exists()

    # The positive control: the sentinel really does record, so its silence
    # above is evidence about the command rather than about the sentinel.
    sys.modules.pop("sentinel_tpl", None)
    importlib.import_module("sentinel_tpl")
    assert marker.read_text() == "imported"


def test_outside_a_repository_it_still_lists_and_says_why_the_list_is_shorter(
    tmp_path: Path, installed, monkeypatch, capsys
):
    """`E-GIT-NO-REPO` caught **by type**, leaving `repo_root=None` — the same
    thing `validate_config` does — never a refusal: core's `generic` and every
    installed claim are answerable without a repository.

    Asserted in both directions at once, which is what mutation 9 needs: the
    rows that ARE answerable are present, AND the explanatory line is there.
    A shorter list with no explanation is the *silently skipped* fault; an
    explanation with no list would be a refusal wearing a note.
    """
    from publishable.cli import main

    _fixture_d(tmp_path, installed, monkeypatch)
    here = tmp_path / "not-a-repo"
    here.mkdir()
    monkeypatch.chdir(here)

    assert main(["list-templates"]) == 0
    out = capsys.readouterr().out
    assert out.startswith(
        f"no git repository was found from {here} upwards, so no project-local "
        "`templates/` was searched"
    )
    assert [line for line in out.splitlines() if line.startswith("### ")] == [
        "### `generic`",
        "### `mmm_installed`",
    ]
    assert "aaa_probe" not in out


def test_a_collision_reaches_main_rather_than_being_listed_tolerantly(
    tmp_path: Path, monkeypatch, capsys
):
    """`_claims` raises `E-TEMPLATE-COLLISION` on a name two providers claim,
    and this command does not catch it — the same answer `validate` gives.
    The command whose job is enumerating names is the wrong place to invent a
    tolerant enumeration: a listing that picked one claimant would be a lie
    about the other.

    Told apart from a refusal this command decided by the PRINTER: `main`'s own
    handler prints one line and no problem count, where every `Collector` this
    slice builds renders a trailing `1 problem (…)`.
    """
    from publishable.cli import main

    root = _project(
        tmp_path,
        {"aaa_probe": _AAA_PROBE, "twin": _AAA_PROBE.replace("AaaProbe", "TwinProbe")},
    )
    monkeypatch.chdir(root)

    assert main(["list-templates"]) == 1
    err = capsys.readouterr().err
    assert err.startswith("  error   E-TEMPLATE-COLLISION")
    assert "claimed more than once" in err
    assert "problem" not in err


def test_list_templates_takes_no_argument_and_no_flag(tmp_path: Path, monkeypatch, capsys):
    """The same arity rule `docs` carries, pinned for this command too rather
    than inherited from its neighbour's arm: *(none)* is the argument
    `docs/reference.md` § Operation commands gives it, and a flag is an
    argument.

    Pinned in the state task 13 leaves, with `NOT_BUILT_COMMANDS` emptied; the
    companion below pins the transitional answer against the shipped one. The
    honouring half is asserted here too, so this cannot pass for a command that
    refuses every invocation.
    """
    import publishable.cli as cli_module
    from publishable.cli import main

    root = _project(tmp_path)
    monkeypatch.chdir(root)
    monkeypatch.setattr(cli_module, "NOT_BUILT_COMMANDS", {})

    for argv in (["list-templates", "somewhere"], ["list-templates", "--all"]):
        assert main(argv) == 2, argv
        assert capsys.readouterr().err == "`list-templates` takes no arguments and no flags\n"
    assert main(["list-templates"]) == 0
    assert "### `generic`" in capsys.readouterr().out


def test_the_two_surfaces_render_one_parameter_spec_the_same_way(
    tmp_path: Path, monkeypatch, capsys
):
    """`list-templates` and the README's `templates` region read the same
    renderer, so the table a reader sees on the terminal and the table their
    README carries cannot drift.

    Asserted by comparing the printed block against `docs.template_details`'
    own output for the same claim, rather than against a third literal — a
    third literal would be exactly the drift this is about.
    """
    from publishable.cli import main
    from publishable.docs import template_details
    from publishable.templates.registry import _claims

    root = _project(tmp_path, {"shapes": _SHAPES_TEMPLATE})
    monkeypatch.chdir(root)

    assert main(["list-templates"]) == 0
    out = capsys.readouterr().out
    expected = "\n".join(template_details(_claims(root)["shapes_assay"]))
    assert expected in out
    assert "| `assay.vendor` | string | `vendor_a` |" in expected


def test_docs_writes_an_installed_claims_named_absence_into_the_FILE(
    tmp_path: Path, installed, monkeypatch, capsys
):
    """The end-to-end arm the two installed tests above do not make: they call
    the body builders directly, and a direct call is a probe of the moment
    rather than of the path a user takes.

    So this runs the real command through `main`, in a project holding an
    installed claim and a local template, and reads the two regions back OUT OF
    THE FILE `docs` wrote. Both directions: the installed claim's named absence
    is in the `templates` region and its credentials row is in the
    `credentials` one, and the local template's real table is in the same file
    — so neither can pass for a command that wrote nothing.
    """
    from publishable.cli import main

    root = _fixture_d(tmp_path, installed, monkeypatch)
    (root / "configs" / "exp-far").mkdir(parents=True)
    (root / "configs" / "exp-far" / "config.yaml").write_text(
        "name: exp-far\nexperiment_type: mmm_installed\n"
    )
    monkeypatch.chdir(root)

    assert main(["docs"]) == 0
    capsys.readouterr()
    text = (root / "README.md").read_text()

    templates = body_of(text, "templates")
    assert "### `mmm_installed`\n\nInstalled, provided by `dist-assay 0.3.1` — " in templates
    assert "`E-TEMPLATE-INSTALLED-UNSUPPORTED`" in templates
    assert "| `aaa.n` | integer | `3` | >= 1 | how many |" in templates
    assert (
        "| _(unknown)_ | `exp-far` — its template `mmm_installed` is installed "
        "(dist-assay 0.3.1), so its `required_env` is not readable "
        "(`E-TEMPLATE-INSTALLED-UNSUPPORTED`) |"
    ) in body_of(text, "credentials")
    # And the provider written into this committed file is a DISTRIBUTION name
    # and version — what a reader pins or uninstalls — never a machine-local
    # path: `templates_body` prints no provider for a `local` claim at all.
    assert str(root) not in templates
