"""H8b tasks 7-8: `covered_config`'s delta walk over `diff.py`, plus form
detection, the per-side header and the four rows that need no apparatus row
(H7d's — task 9's job). `diff` does not dispatch through `main` until task
11, so every call here is direct, on `command_diff`.
"""

import re
from pathlib import Path

import pytest
import yaml
from tests.test_acceptance import build
from tests.test_cli import run_a_project

from publishable.cli import main
from publishable.diagnostics import EXIT_OK, EXIT_WRONG
from publishable.diff import (
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
    assert ROW_LABELS == ["code_hash", "input_manifest", "uv.lock", "parameters_hash"]
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
    # The literal below is the independent expectation.
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
    § Same code, different parameters both show the four-row form (no
    apparatus row, since template `generic` declares no probe) —
    `ROW_LABELS` must equal what THEY say. If either document renamed
    `uv.lock` tomorrow, this must fail."""
    assert _document_row_labels(README_MD) == ROW_LABELS
    assert _document_row_labels(DESIGN_PRINCIPLES_MD) == ROW_LABELS


def test_h8b_row_labels_agree_with_reference_once_apparatus_is_dropped():
    """reference.md § The apparatus core can only observe shows the
    five-row form. `apparatus` is task 9's row; until it lands,
    `ROW_LABELS` is that same document sequence with `apparatus` removed."""
    labels = _document_row_labels(REFERENCE_MD)
    assert "apparatus" in labels
    assert [label for label in labels if label != "apparatus"] == ROW_LABELS


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
