"""H8b tasks 7-8: `covered_config`'s delta walk over `diff.py`, plus form
detection, the per-side header and the four rows that need no apparatus row
(H7d's — task 9's job). `diff` does not dispatch through `main` until task
11, so every call here is direct, on `command_diff`.
"""

import re
import uuid
from pathlib import Path

import pytest
import yaml
from tests.test_acceptance import build
from tests.test_cli import run_a_project

from publishable.cli import main
from publishable.diagnostics import EXIT_OK, EXIT_WRONG
from publishable.diff import (
    _NOT_COMPARABLE_REASONS,
    ROW_LABELS,
    _form,
    _header_line,
    _load_side,
    _render_row,
    command_diff,
    parameter_deltas,
)
from publishable.errors import ContractError

README_MD = Path(__file__).resolve().parents[1] / "README.md"
DESIGN_PRINCIPLES_MD = Path(__file__).resolve().parents[1] / "docs" / "design-principles.md"
REFERENCE_MD = Path(__file__).resolve().parents[1] / "docs" / "reference.md"

# ---------------------------------------------------------------------------
# Fixture M (task 7 step 4): metadata versus limits, the coverage pin.
# ---------------------------------------------------------------------------


def _m_base() -> dict:
    return {
        "experiment_type": "generic",
        "metadata": {"description": "one"},
        "data": {"input_dir": "/x", "output_dir": "/y", "input_manifest_policy": "hash_all"},
        "parameters": {"analysis": {"method": "pearson"}},
        "limits": {"max_failed_fraction": 0.2},
    }


def test_h8b_fixture_m_arm_one_metadata_only_edit_is_zero_delta_lines():
    """Fixture M arm one: two records differing only in `metadata.description`
    must print zero delta lines — the coverage pin's first half."""
    a = _m_base()
    b = {**a, "metadata": {"description": "a different one entirely"}}
    assert parameter_deltas(a, b) == []


def test_h8b_fixture_m_arm_two_limits_only_edit_is_exactly_one_line():
    """Fixture M arm two: two records differing only in
    `limits.max_failed_fraction` must print exactly one line, naming that
    path and both values — read back from the two configs, not typed."""
    a = _m_base()
    b = {**a, "limits": {"max_failed_fraction": 0.4}}
    lines = parameter_deltas(a, b)
    assert lines == [
        f"  limits.max_failed_fraction  {a['limits']['max_failed_fraction']} → "
        f"{b['limits']['max_failed_fraction']}"
    ]


def test_h8b_fixture_m_arm_three_a_reordered_list_is_one_line_not_indexed():
    """A leaf is anything that is not a `dict` — a list is a leaf, not a
    subtree. Reordering `sweep.grid`'s axis list with the same members must
    print exactly ONE line (the whole list moved), never one per position."""
    a = {
        "experiment_type": "generic",
        "sweep": {"grid": {"analysis.method": ["pearson", "spearman", "kendall"]}},
        "parameters": {},
    }
    b = {
        "experiment_type": "generic",
        "sweep": {"grid": {"analysis.method": ["spearman", "pearson", "kendall"]}},
        "parameters": {},
    }
    lines = parameter_deltas(a, b)
    assert len(lines) == 1
    assert lines[0].startswith("  sweep.grid.analysis.method  ")


def test_h8b_a_leaf_present_on_only_one_side_renders_absent_arrow_value():
    a = {"experiment_type": "generic", "parameters": {}}
    b = {"experiment_type": "generic", "parameters": {}, "statistics": {"contrasts": [{"a": 1}]}}
    lines = parameter_deltas(a, b)
    assert lines == ["  statistics.contrasts  (absent) → [{a: 1}]"]
    # And the reverse direction:
    reverse = parameter_deltas(b, a)
    assert reverse == ["  statistics.contrasts  [{a: 1}] → (absent)"]


def test_h8b_parameter_deltas_are_sorted_by_path():
    a = {"experiment_type": "generic", "parameters": {}}
    b = {
        "experiment_type": "generic",
        "parameters": {"z": {"late": 1}, "a": {"early": 1}},
    }
    lines = parameter_deltas(a, b)
    paths = [line.split()[0] for line in lines]
    assert paths == sorted(paths)
    assert paths == ["parameters.a.early", "parameters.z.late"]


# ---------------------------------------------------------------------------
# Batch 5 review, Major 1: an empty mapping is a leaf too, and `sweep: {}`
# — what `publishable init` itself materializes — is the reachable case.
# ---------------------------------------------------------------------------


def test_h8b_an_empty_mapping_leaf_prints_one_line_not_a_bare_differs():
    """`covered_config({"sweep": {}})` and `covered_config({})` must NOT
    flatten identically — the defect Major 1 named: `_flatten` used to drop
    an empty `dict` entirely, so `parameters_hash` moved while the delta
    walk printed nothing."""
    a = {"experiment_type": "generic", "parameters": {}, "sweep": {}}
    b = {"experiment_type": "generic", "parameters": {}}
    lines = parameter_deltas(a, b)
    assert lines == ["  sweep  {} → (absent)"]
    reverse = parameter_deltas(b, a)
    assert reverse == ["  sweep  (absent) → {}"]


def test_h8b_fixture_m_arm_four_sweep_empty_block_deleted_end_to_end(tmp_path: Path):
    """Major 1, end to end against `init`'s own output: `generate_experiment`
    materializes `sweep: {}` (`materialize.py`'s own comment: "Empty (or
    omitted) means a single, unswept condition"), so deleting the key
    between two runs is a real, reachable edit — not a hand-built dict.
    `parameters_hash` must differ (the projection includes `sweep` either
    way) AND the delta walk must name exactly one line, never zero."""
    doc = run_a_project(tmp_path, units=8)
    run_a = doc["run_dir"]
    config_a = yaml.safe_load((run_a / "config.yaml").read_text())
    assert config_a["sweep"] == {}, "measured: init/generate_experiment writes sweep: {}"

    def edit(config: dict) -> None:
        del config["sweep"]

    run_b = _second_run_after_edit(doc, edit)
    doc_a = yaml.safe_load((run_a / "run.yaml").read_text())
    doc_b = yaml.safe_load((run_b / "run.yaml").read_text())
    assert doc_a["parameters_hash"] != doc_b["parameters_hash"]
    lines = parameter_deltas(doc_a["config"], doc_b["config"])
    assert lines == ["  sweep  {} → (absent)"]


# ---------------------------------------------------------------------------
# Batch 5 review, Major 3: a scalar leaf renders in the config's own YAML
# vocabulary, not Python's repr.
# ---------------------------------------------------------------------------


def test_h8b_bool_and_none_leaves_render_as_yaml_not_python_repr():
    a = {
        "experiment_type": "generic",
        "parameters": {"analysis": {"drop_missing": True}},
        "data": {"units": {"cluster_by": None}},
    }
    b = {
        "experiment_type": "generic",
        "parameters": {"analysis": {"drop_missing": False}},
        "data": {"units": {"cluster_by": "site"}},
    }
    lines = parameter_deltas(a, b)
    joined = "\n".join(lines)
    assert "true → false" in joined
    assert "null → site" in joined
    assert "True" not in joined
    assert "None" not in joined


def test_h8b_scalar_string_leaves_are_not_yaml_quoted():
    """A `str` scalar keeps `str(value)` — Major 3's fix is not a blanket
    `safe_dump` widening that would start quoting ordinary strings."""
    a = {"experiment_type": "generic", "parameters": {"analysis": {"method": "pearson"}}}
    b = {"experiment_type": "generic", "parameters": {"analysis": {"method": "spearman"}}}
    lines = parameter_deltas(a, b)
    assert lines == ["  parameters.analysis.method  pearson → spearman"]


# ---------------------------------------------------------------------------
# Real runs: Fixture R (base), Fixture R2 (one parameter edited), Fixture L
# (a real lockfile, and a lockfile that then moves).
# ---------------------------------------------------------------------------


def _second_run_after_edit(doc: dict, edit) -> Path:
    """Fixture R2's mechanism: edit the SAME project's config as a mapping,
    write it back, and run again — `run_a_project` scaffolds and runs once,
    so a second run against an edited copy is driven directly through
    `main`, on `run_a_project`'s own precedent for what a caller building a
    second run does."""
    cfg = doc["cfg"]
    config = yaml.safe_load(cfg.read_text())
    edit(config)
    cfg.write_text(yaml.safe_dump(config))
    assert main(["run", str(cfg)]) == EXIT_OK
    run_b = next(p for p in doc["results_dir"].glob("run_*") if p != doc["run_dir"])
    return run_b


def test_h8b_fixture_r2_the_documented_payoff(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    """Fixture R2: the same run, `parameters.analysis.min_samples` moved and
    nothing else. `code_hash`/`input_manifest` identical, `uv.lock` not
    captured (measured: a scaffolded project's `uv_lock_hash` is `None`),
    `parameters_hash` DIFFERS with exactly one delta line whose path and
    both values are read from the two configs, and exit 0 (M5's
    discriminator, pinned again properly at task 10 — asserted here since
    Decision 4 is already ruled)."""
    doc = run_a_project(tmp_path, units=8)
    run_a = doc["run_dir"]
    config_a = yaml.safe_load((run_a / "config.yaml").read_text())
    before = config_a["parameters"]["analysis"]["min_samples"]

    def edit(config: dict) -> None:
        config["parameters"]["analysis"]["min_samples"] = before + 20

    run_b = _second_run_after_edit(doc, edit)
    config_b = yaml.safe_load((run_b / "config.yaml").read_text())
    after = config_b["parameters"]["analysis"]["min_samples"]
    assert after == before + 20

    capsys.readouterr()
    code = command_diff(run_a, run_b)
    out = capsys.readouterr().out
    assert code == EXIT_OK
    # Regex, not a literal, since batch 5's fix round pads labels/verdicts
    # to the worked outputs' own column widths (Minor 1) rather than a
    # fixed number of spaces.
    assert re.search(r"^code_hash\s+identical", out, re.M)
    assert re.search(r"^input_manifest\s+identical", out, re.M)
    assert re.search(r"^uv\.lock\s+not captured$", out, re.M)
    assert re.search(r"^parameters_hash\s+DIFFERS$", out, re.M)
    delta_lines = [
        line
        for line in out.splitlines()
        if line.strip().startswith("parameters.analysis.min_samples")
    ]
    assert len(delta_lines) == 1
    assert f"{before} → {before + 20}" in delta_lines[0]


def test_h8b_fixture_l_the_lockfile_rows_non_null_path(tmp_path: Path):
    """Fixture L: a real `uv.lock` committed before the run, then a second
    run after the lockfile's bytes change — the only fixture that exercises
    `uv.lock`'s `identical` and `DIFFERS` arms, since every scaffolded run
    otherwise takes `not captured`."""
    root, cfg, results = build(tmp_path)
    import subprocess

    (root / "uv.lock").write_text("# a stand-in lockfile\n")
    subprocess.run(["git", "add", "uv.lock"], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "lock"],
        cwd=root,
        check=True,
    )
    assert main(["run", str(cfg)]) == EXIT_OK
    run_a = next(results.glob("run_*"))

    # identical arm: run again with no lockfile change
    assert main(["run", str(cfg)]) == EXIT_OK
    run_b = next(p for p in results.glob("run_*") if p != run_a)
    code_identical = command_diff(run_a, run_b)
    assert code_identical == EXIT_OK

    doc_a = yaml.safe_load((run_a / "run.yaml").read_text())
    doc_b = yaml.safe_load((run_b / "run.yaml").read_text())
    assert doc_a["provenance"]["environment"]["uv_lock_hash"] is not None
    assert (
        doc_a["provenance"]["environment"]["uv_lock_hash"]
        == doc_b["provenance"]["environment"]["uv_lock_hash"]
    )

    # DIFFERS arm: change the lockfile's bytes, run a third time
    (root / "uv.lock").write_text("# a stand-in lockfile, moved\n")
    subprocess.run(["git", "add", "uv.lock"], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "relock"],
        cwd=root,
        check=True,
    )
    assert main(["run", str(cfg)]) == EXIT_OK
    run_c = next(p for p in results.glob("run_*") if p not in (run_a, run_b))
    doc_c = yaml.safe_load((run_c / "run.yaml").read_text())
    assert (
        doc_c["provenance"]["environment"]["uv_lock_hash"]
        != doc_a["provenance"]["environment"]["uv_lock_hash"]
    )
    code_differs = command_diff(run_a, run_c)
    assert code_differs == EXIT_OK


def test_h8b_fixture_l_row_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    root, cfg, results = build(tmp_path)
    import subprocess

    (root / "uv.lock").write_text("# a stand-in lockfile\n")
    subprocess.run(["git", "add", "uv.lock"], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "lock"],
        cwd=root,
        check=True,
    )
    assert main(["run", str(cfg)]) == EXIT_OK
    run_a = next(results.glob("run_*"))
    assert main(["run", str(cfg)]) == EXIT_OK
    run_b = next(p for p in results.glob("run_*") if p != run_a)

    capsys.readouterr()
    command_diff(run_a, run_b)
    out = capsys.readouterr().out
    assert re.search(r"^uv\.lock\s+identical", out, re.M)

    (root / "uv.lock").write_text("# a stand-in lockfile, moved\n")
    subprocess.run(["git", "add", "uv.lock"], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "relock"],
        cwd=root,
        check=True,
    )
    assert main(["run", str(cfg)]) == EXIT_OK
    run_c = next(p for p in results.glob("run_*") if p not in (run_a, run_b))

    capsys.readouterr()
    command_diff(run_a, run_c)
    out2 = capsys.readouterr().out
    assert re.search(r"^uv\.lock\s+DIFFERS", out2, re.M)


# ---------------------------------------------------------------------------
# Batch 5 review, Major 2: the one-sided `not captured` arm — a null figure
# on only one side, not both. Fixture R2 only ever exercises the
# both-null case; this is the pin that was missing.
# ---------------------------------------------------------------------------


def test_h8b_the_one_sided_not_captured_arm(tmp_path: Path):
    """`_render_row`'s `or` guard must fire when exactly one side's figure
    is `null`, not only when both are. Real records: a lockfile-backed run
    (Fixture L's own mechanism) against an ordinary `run_a_project`
    scaffold, in both operand orders."""
    import subprocess

    root, cfg, results = build(tmp_path)
    (root / "uv.lock").write_text("# a stand-in lockfile\n")
    subprocess.run(["git", "add", "uv.lock"], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "lock"],
        cwd=root,
        check=True,
    )
    assert main(["run", str(cfg)]) == EXIT_OK
    run_with_lock = next(results.glob("run_*"))
    doc_with_lock = yaml.safe_load((run_with_lock / "run.yaml").read_text())
    assert doc_with_lock["provenance"]["environment"]["uv_lock_hash"] is not None

    without_lock_root = tmp_path / "second_project"
    without_lock_root.mkdir()
    second = run_a_project(without_lock_root, units=8)
    doc_without_lock = yaml.safe_load((second["run_dir"] / "run.yaml").read_text())
    assert doc_without_lock["provenance"]["environment"]["uv_lock_hash"] is None

    for line in _render_row("uv.lock", doc_with_lock, doc_without_lock):
        assert re.fullmatch(r"uv\.lock\s+not captured", line)
    for line in _render_row("uv.lock", doc_without_lock, doc_with_lock):
        assert re.fullmatch(r"uv\.lock\s+not captured", line)


# ---------------------------------------------------------------------------
# Form detection (task 8 step 1).
# ---------------------------------------------------------------------------


def test_h8b_form_by_shape_a_directory_is_a_run_record(tmp_path: Path):
    d = tmp_path / "some_dir"
    d.mkdir()
    assert _form(d) == "run record"


def test_h8b_form_by_shape_a_run_yaml_file_is_a_run_record(tmp_path: Path):
    p = tmp_path / "run.yaml"
    assert _form(p) == "run record"  # not even written yet — shape, not content


def test_h8b_form_by_shape_any_other_file_is_a_config(tmp_path: Path):
    p = tmp_path / "config.yaml"
    assert _form(p) == "config"
    missing = tmp_path / "nope" / "nope.yaml"
    assert _form(missing) == "config"


# ---------------------------------------------------------------------------
# The refusals (task 8 step 2).
# ---------------------------------------------------------------------------


def test_h8b_a_missing_path_raises_os_error_uncaught(tmp_path: Path):
    """`diff` does not dispatch until task 11, so `main`'s generic `OSError`
    handler is not in the loop yet. `command_diff` follows `validate`'s and
    `freeze`'s own shipped precedent: an unanticipated path problem
    propagates uncaught. Once wired (task 11), `main` turns this into
    `E-IO-FAILED` at exit 1 — measured at `0a636af` for `validate`."""
    missing = tmp_path / "nope" / "nope.yaml"
    other = tmp_path / "also_missing.yaml"
    with pytest.raises(OSError):
        command_diff(missing, other)


def test_h8b_an_unreadable_run_record_is_e_upstream_record_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    other = tmp_path / "empty2"
    other.mkdir()
    code = command_diff(empty_dir, other)
    out = capsys.readouterr().out
    assert code == EXIT_WRONG
    assert "E-UPSTREAM-RECORD-MISSING" in out


def test_h8b_a_config_that_is_not_a_mapping_is_e_diff_config_unreadable(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    a = tmp_path / "a.yaml"
    a.write_text("- one\n- two\n")
    b = tmp_path / "b.yaml"
    b.write_text("experiment_type: generic\n")
    code = command_diff(a, b)
    out = capsys.readouterr().out
    assert code == EXIT_WRONG
    assert "E-DIFF-CONFIG-UNREADABLE" in out


def test_h8b_load_side_raises_contracterror_for_unreadable_record(tmp_path: Path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    with pytest.raises(ContractError) as exc_info:
        _load_side(empty_dir)
    assert exc_info.value.code == "E-UPSTREAM-RECORD-MISSING"


# ---------------------------------------------------------------------------
# The per-side header (task 8 step 3).
# ---------------------------------------------------------------------------


def test_h8b_header_for_a_run_record_shows_form_id_status(tmp_path: Path):
    doc = run_a_project(tmp_path, units=8)
    side = _load_side(doc["run_dir"])
    line = _header_line("A", side)
    assert line.startswith("A  run record  ")
    assert side.record is not None
    assert side.record["run_id"] in line
    assert "completed" in line
    assert "draft" not in line  # this run's `draft` is `False`


def test_h8b_header_for_a_config_shows_form_and_path_as_given_no_status(tmp_path: Path):
    p = tmp_path / "some" / "config.yaml"
    p.parent.mkdir(parents=True)
    p.write_text("experiment_type: generic\n")
    side = _load_side(p)
    line = _header_line("B", side)
    assert line == f"B  config  {p}"
    # No resolved/absolute-ized rewriting of what was given:
    assert str(p) in line


# ---------------------------------------------------------------------------
# The row order (task 8 step 8) — ONE AUTHORIZED EDITOR: task 9, which
# inserts 'apparatus' in fourth position, before 'parameters_hash', because
# the apparatus row does not exist at this task. No other task may reorder
# this list; any other failure here is a finding to report, not a pin to
# edit.
# ---------------------------------------------------------------------------


def _row_labels_in_output(output: str) -> list[str]:
    labels = []
    for line in output.splitlines():
        for label in ROW_LABELS:
            if line.startswith(label + " "):
                labels.append(label)
                break
    return labels


def test_h8b_row_order_is_pinned(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    # Task 9's one authorized edit to this list: 'apparatus' inserted in
    # fourth position, before 'parameters_hash'. Nothing else reordered.
    assert ROW_LABELS == ["code_hash", "input_manifest", "uv.lock", "apparatus", "parameters_hash"]
    doc = run_a_project(tmp_path, units=8)
    run_a = doc["run_dir"]

    def edit(config: dict) -> None:
        config["parameters"]["analysis"]["min_samples"] += 1

    run_b = _second_run_after_edit(doc, edit)
    capsys.readouterr()
    command_diff(run_a, run_b)
    out = capsys.readouterr().out
    # Deliberately NOT compared against the `ROW_LABELS` constant: if a
    # mutation reordered that constant, `_row_labels_in_output`'s extraction
    # would move with it and the assertion would stay vacuously true (the
    # "test iterates the thing under test" shape `CLAUDE.md` warns about).
    # The literal below is the independent expectation. `'apparatus'` is
    # deliberately NOT in this list: both sides here are `run_a_project`
    # scaffolds, template `generic` declares no probe, and Decision 2 OMITS
    # the row when both sides' `provenance.apparatus` is `null` — this
    # fixture never exercises the apparatus row's presence, only that its
    # absence doesn't disturb the other four rows' order.
    assert _row_labels_in_output(out) == [
        "code_hash",
        "input_manifest",
        "uv.lock",
        "parameters_hash",
    ]


# ---------------------------------------------------------------------------
# Batch 5 review, Major 4: `ROW_LABELS` pinned against the DOCUMENTS'
# text, not against the code's own idea of itself — the
# `_status_tables`/`_interval_method_names` shape from `tests/test_cli.py`.
# ---------------------------------------------------------------------------


def _document_row_labels(path: Path) -> list[str]:
    """Every `<label>  identical|DIFFERS` line in a fenced `diff` output.
    Anchored at the start of the line, so an indented detail line
    (`  calibration_id   CAL... → CAL...`) never matches — a detail line
    starts with whitespace, a row line starts with its label."""
    labels = []
    for line in path.read_text().splitlines():
        match = re.match(r"^([A-Za-z][A-Za-z0-9_.]*)\s{2,}(identical|DIFFERS)\b", line)
        if match:
            labels.append(match.group(1))
    return labels


def test_h8b_row_labels_are_parsed_from_the_documents_at_all():
    """The control: each of the three documents must yield at least one row
    label, or every agreement pin below passes vacuously."""
    assert _document_row_labels(README_MD)
    assert _document_row_labels(DESIGN_PRINCIPLES_MD)
    assert _document_row_labels(REFERENCE_MD)


def test_h8b_row_labels_agree_with_readme_and_design_principles():
    """README § The loop you'll actually live in and design-principles.md
    § Same code, different parameters both show the FOUR-row form — no
    apparatus row, since template `generic` declares no probe and Decision
    2 omits the row when both sides are `null`, which is every pair either
    worked output shows. `ROW_LABELS` now carries `apparatus` itself (task
    9), so the comparison is against `ROW_LABELS` with that one row
    dropped, not against `ROW_LABELS` whole — updated from task 8's
    equality (which held only while `apparatus` had not landed) for exactly
    the reason task 8's own docstring anticipated. If either document
    renamed `uv.lock` tomorrow, this must still fail."""
    without_apparatus = [label for label in ROW_LABELS if label != "apparatus"]
    assert _document_row_labels(README_MD) == without_apparatus
    assert _document_row_labels(DESIGN_PRINCIPLES_MD) == without_apparatus


def test_h8b_row_labels_agree_with_reference_now_that_apparatus_has_landed():
    """reference.md § The apparatus core can only observe shows the
    FIVE-row form, `apparatus` fourth. Now that task 9 has landed the row,
    `ROW_LABELS` must equal that document's sequence exactly — the
    inversion of the pin above, which drops the row precisely because
    README/design-principles' worked pair never has one to show."""
    assert _document_row_labels(REFERENCE_MD) == ROW_LABELS


# ---------------------------------------------------------------------------
# Batch 5 review, Minor 4: with both operands unreadable, both are reported
# in one run rather than one at a time.
# ---------------------------------------------------------------------------


def test_h8b_both_operands_unreadable_are_both_reported(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    empty_a = tmp_path / "empty_a"
    empty_a.mkdir()
    empty_b = tmp_path / "empty_b"
    empty_b.mkdir()
    code = command_diff(empty_a, empty_b)
    out = capsys.readouterr().out
    assert code == EXIT_WRONG
    assert str(empty_a) in out
    assert str(empty_b) in out
    assert out.count("E-UPSTREAM-RECORD-MISSING") == 2


# ---------------------------------------------------------------------------
# Task 9: the `apparatus` row. Fixture P (H7d Part A's shape, inherited): a
# synthetic installed distribution registering a probe, a project-local
# template declaring `apparatus_probe`/`apparatus_facts`, two conditions so
# the per-condition scope is exercised rather than assumed. The probe's
# `calibration_id` answer comes from an environment variable the test sets
# — "a fact that can be moved between calls" — rather than a file, since the
# registered probe function reads it at CALL time, not at import time, so
# the same registration serves two separately-scaffolded projects with two
# different answers.
# ---------------------------------------------------------------------------

_H8B_APPARATUS_TEMPLATE = """\
from publishable import BaseTemplate, Param, register_template


@register_template("h8b_apparatus_assay")
class H8bApparatusAssay(BaseTemplate):
    naming_pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    apparatus_probe = "h8b_probe"
    apparatus_facts = ["calibration_id"]
    parameter_spec = {
        "instrument.model": Param(str, default="m1", choices=["m1", "m2"]),
    }
"""

_H8B_PROBE_MODULE = """\
import os

from publishable import Apparatus, register_probe


@register_probe("h8b_probe")
def probe(cfg):
    return Apparatus(facts={"calibration_id": os.environ.get("H8B_CALIBRATION_ID")})
"""


def _install_h8b_probe(installed) -> None:
    # A fresh, per-test module NAME (not merely a fresh site directory):
    # `sys.modules` caches by module name across tests in the same process,
    # and a cached module's top level does not re-run on a second import —
    # so a second test reusing "h8b_probe_mod" would import the CACHED
    # module from an earlier test without re-executing `@register_probe`,
    # and `registries()` resetting the registry dict between tests would
    # then make the entry point look unregistered. Measured: this is
    # exactly the shape, distinct module per test avoids it.
    module_name = f"h8b_probe_mod_{uuid.uuid4().hex}"
    site = installed(
        "dist-h8b-probe", "1.0", {"publishable.probes": {"h8b_probe": f"{module_name}:probe"}}
    )
    (site / f"{module_name}.py").write_text(_H8B_PROBE_MODULE)


def _run_with_probe(
    project_dir: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    calibration_id: str,
) -> dict:
    project_dir.mkdir()
    monkeypatch.setenv("H8B_CALIBRATION_ID", calibration_id)
    return run_a_project(
        project_dir,
        capsys=capsys,
        experiment_type="h8b_apparatus_assay",
        parameters={"instrument": {"model": "m1"}},
        sweep={"grid": {"instrument.model": ["m1", "m2"]}},
        _local_template=_H8B_APPARATUS_TEMPLATE,
    )


def test_h8b_fixture_a1_apparatus_differs_two_conditions_moving(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch, installed, registries
):
    """Fixture A1: two Fixture P runs whose probe answers a different
    `calibration_id` in the second. Asserts exactly TWO detail lines, each
    containing its own condition key, each carrying that condition's own
    old and new values read back from the two records' own
    `provenance.apparatus.facts` — never typed."""
    _install_h8b_probe(installed)
    doc_a = _run_with_probe(tmp_path / "proj_a", capsys, monkeypatch, "CAL-2026-07-19")
    doc_b = _run_with_probe(tmp_path / "proj_b", capsys, monkeypatch, "CAL-2026-08-02")

    run_a_yaml = yaml.safe_load((doc_a["run_dir"] / "run.yaml").read_text())
    run_b_yaml = yaml.safe_load((doc_b["run_dir"] / "run.yaml").read_text())
    facts_a = run_a_yaml["provenance"]["apparatus"]["facts"]
    facts_b = run_b_yaml["provenance"]["apparatus"]["facts"]
    assert set(facts_a) == set(facts_b) and len(facts_a) == 2, "the fixture needs two conditions"

    capsys.readouterr()
    code = command_diff(doc_a["run_dir"], doc_b["run_dir"])
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert re.search(r"^apparatus\s+DIFFERS$", out, re.M)

    detail_lines = [line for line in out.splitlines() if "calibration_id" in line and "→" in line]
    assert len(detail_lines) == 2, "one per condition — no collapsing"
    for condition in facts_a:
        matching = [line for line in detail_lines if line.strip().startswith(condition + ".")]
        assert len(matching) == 1, f"condition {condition} must have its own qualified line"
        assert (
            f"{facts_a[condition]['calibration_id']} → {facts_b[condition]['calibration_id']}"
            in (matching[0])
        )


def test_h8b_fixture_a2_apparatus_identical_and_one_sided(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch, installed, registries
):
    """Fixture A2, first arm: a Fixture P pair whose probe answers the same
    `calibration_id` both times prints `apparatus identical` with the
    digest — never `DIFFERS`, and no detail lines."""
    _install_h8b_probe(installed)
    doc_a = _run_with_probe(tmp_path / "proj_a", capsys, monkeypatch, "CAL-2026-07-19")
    doc_b = _run_with_probe(tmp_path / "proj_b", capsys, monkeypatch, "CAL-2026-07-19")

    capsys.readouterr()
    code = command_diff(doc_a["run_dir"], doc_b["run_dir"])
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert re.search(r"^apparatus\s+identical\s+sha256:", out, re.M)
    assert "calibration_id" not in out


def test_h8b_fixture_a2_one_sided_apparatus_null_is_differs_and_names_the_side(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch, installed, registries
):
    """Fixture A2, second arm: a Fixture P record (apparatus non-null)
    against a Fixture R record (`run_a_project`'s ordinary scaffold,
    `apparatus: null` — template `generic` declares no probe) is `DIFFERS`
    in both operand orders, each naming which side recorded none. This is
    what pins "the row appears whenever EITHER side has one" and that
    silence would read as agreement."""
    _install_h8b_probe(installed)
    with_apparatus = _run_with_probe(tmp_path / "proj_a", capsys, monkeypatch, "CAL-2026-07-19")
    without_apparatus = run_a_project(tmp_path / "proj_b", units=8, capsys=capsys)

    run_with = with_apparatus["run_dir"]
    run_without = without_apparatus["run_dir"]

    capsys.readouterr()
    code = command_diff(run_with, run_without)
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert re.search(r"^apparatus\s+DIFFERS$", out, re.M)
    assert "B recorded no apparatus" in out

    capsys.readouterr()
    code_reverse = command_diff(run_without, run_with)
    out_reverse = capsys.readouterr().out
    assert code_reverse == EXIT_OK
    assert re.search(r"^apparatus\s+DIFFERS$", out_reverse, re.M)
    assert "A recorded no apparatus" in out_reverse


def test_h8b_apparatus_row_omitted_when_both_sides_null(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """The omission rule's own positive control: two ordinary `run_a_project`
    scaffolds (both `apparatus: null`) print no `apparatus` line at all —
    not `identical`, not `DIFFERS`, nothing."""
    doc_a = run_a_project(tmp_path / "proj_a", units=8, capsys=capsys)
    doc_b = run_a_project(tmp_path / "proj_b", units=8, capsys=capsys)
    capsys.readouterr()
    command_diff(doc_a["run_dir"], doc_b["run_dir"])
    out = capsys.readouterr().out
    assert not re.search(r"^apparatus\s", out, re.M)


# ---------------------------------------------------------------------------
# M2's own discriminating fixture (Decision 2's cost-if-wrong; task 9 step
# 8): the identical arm survives one side's `facts` mapping being
# RE-SERIALIZED in a different key order, because the verdict compares
# `.hash` (canonicalized with `sort_keys=True` by `apparatus.apparatus_hash`
# — invariant to reordering) rather than the `.facts` mapping directly. Two
# real Fixture P runs answering the SAME `calibration_id` never differ in
# key order on their own (same code path both times), so this reordering
# is applied BY HAND to be the thing that would trip a mapping comparison
# — printing `list(...)` first, per the brief, to confirm the reordering
# survives into what `_render_row` actually receives.
# ---------------------------------------------------------------------------


def test_h8b_apparatus_identical_survives_a_facts_key_reorder(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch, installed, registries
):
    _install_h8b_probe(installed)
    doc_a = _run_with_probe(tmp_path / "proj_a", capsys, monkeypatch, "CAL-2026-07-19")
    doc_b = _run_with_probe(tmp_path / "proj_b", capsys, monkeypatch, "CAL-2026-07-19")
    run_a = yaml.safe_load((doc_a["run_dir"] / "run.yaml").read_text())
    run_b = yaml.safe_load((doc_b["run_dir"] / "run.yaml").read_text())

    facts_b = run_b["provenance"]["apparatus"]["facts"]
    reordered = {
        condition: dict(reversed(list(fact_map.items()))) for condition, fact_map in facts_b.items()
    }
    reordered = dict(reversed(list(reordered.items())))
    # Confirm the reordering actually survives into what the comparison
    # sees, per the brief's own instruction — CPython dicts preserve
    # insertion order, so this is measuring that fact rather than assuming
    # it.
    assert list(reordered) != list(facts_b) or any(
        list(reordered[c]) != list(facts_b[c]) for c in facts_b
    ), "the reorder must actually change iteration order, or this fixture proves nothing"
    run_b["provenance"]["apparatus"]["facts"] = reordered

    lines = _render_row("apparatus", run_a, run_b)
    assert re.match(r"^apparatus\s+identical", lines[0]), lines


# ---------------------------------------------------------------------------
# Task 10: the config side's `not comparable` rows (Decision 5 part 4), and
# Decision 4's exit-code ruling.
# ---------------------------------------------------------------------------


def _minimal_config(tmp_path: Path, name: str, method: str = "pearson") -> Path:
    p = tmp_path / name
    p.write_text(
        yaml.safe_dump(
            {
                "experiment_type": "generic",
                "metadata": {"description": "x", "authors": []},
                "data": {
                    "input_dir": "/x",
                    "output_dir": "/y",
                    "input_manifest_policy": "hash_all",
                },
                "parameters": {"analysis": {"method": method}},
            }
        )
    )
    return p


def test_h8b_config_vs_run_one_row_computed_four_not_comparable(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """Config-vs-run: `parameters_hash` is the one computed row; the other
    four print `not comparable` with their reason text, verbatim."""
    doc = run_a_project(tmp_path / "proj", units=8, capsys=capsys)
    run_dir = doc["run_dir"]
    config_path = _minimal_config(tmp_path, "other.yaml")

    capsys.readouterr()
    code = command_diff(run_dir, config_path)
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert re.search(r"^parameters_hash\s+(identical|DIFFERS)", out, re.M)
    for row, reason in _NOT_COMPARABLE_REASONS.items():
        assert re.search(rf"^{re.escape(row)}\s+not comparable\s+{re.escape(reason)}$", out, re.M)


def test_h8b_config_vs_config_same_shape(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    """Config-vs-config: the identical shape as config-vs-run — Decision 5's
    'the same rule' claim, checked rather than assumed."""
    a = _minimal_config(tmp_path, "a.yaml", method="pearson")
    b = _minimal_config(tmp_path, "b.yaml", method="spearman")

    capsys.readouterr()
    code = command_diff(a, b)
    out = capsys.readouterr().out
    assert code == EXIT_OK
    assert re.search(r"^parameters_hash\s+DIFFERS$", out, re.M)
    assert "parameters.analysis.method  pearson → spearman" in out
    for row, reason in _NOT_COMPARABLE_REASONS.items():
        assert re.search(rf"^{re.escape(row)}\s+not comparable\s+{re.escape(reason)}$", out, re.M)


def test_h8b_run_vs_run_control_never_prints_not_comparable(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """The control (design's own Fixture, third arm): a run-vs-run pair
    computes all applicable rows and prints `not comparable` for NONE of
    them. Without this control, a build that printed `not comparable`
    unconditionally would pass the two tests above."""
    doc_a = run_a_project(tmp_path / "proj_a", units=8, capsys=capsys)
    doc_b = run_a_project(tmp_path / "proj_b", units=8, capsys=capsys)
    capsys.readouterr()
    command_diff(doc_a["run_dir"], doc_b["run_dir"])
    out = capsys.readouterr().out
    assert "not comparable" not in out


def test_h8b_a_config_that_is_not_a_mapping_still_yields_no_render(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """`not captured` and `not comparable` are different words on different
    paths: `not captured` is a run-vs-run row whose figure is `null` on a
    side that COULD have held one (Fixture R2/L's territory); `not
    comparable` is a config side that can never supply the figure at all.
    A config that fails to parse to a mapping is a THIRD path entirely —
    it never reaches either word, because nothing renders."""
    a = tmp_path / "a.yaml"
    a.write_text("- one\n- two\n")
    b = tmp_path / "b.yaml"
    b.write_text("experiment_type: generic\n")
    capsys.readouterr()
    code = command_diff(a, b)
    out = capsys.readouterr().out
    assert code == EXIT_WRONG
    assert "not captured" not in out
    assert "not comparable" not in out
    assert "E-DIFF-CONFIG-UNREADABLE" in out
