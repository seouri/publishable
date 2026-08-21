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
    _parameters_hash_for,
    _render_row,
    _Side,
    _upstream_block_lines,
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
# Whole-branch review Major 1: a config operand holding a value
# `json.dumps` cannot serialize (a bare, unquoted date, most plausibly)
# tracebacked out of `diff` after printing four rows. `_parameters_hash_for`
# is the guard's home — it is the one call that recomputes a config side's
# hash fresh — and `E-DIFF-CONFIG-UNREADABLE` is the sibling refusal reused
# rather than a new code minted for a config operand this build cannot read.
# ---------------------------------------------------------------------------


def test_h8b_parameters_hash_for_a_config_with_an_unserializable_value_is_e_diff_config_unreadable(
    tmp_path: Path,
):
    """Direct unit-level proof, on the precedent
    `test_h8b_load_side_raises_contracterror_for_unreadable_record` sets: the
    function that raises does so under the right code, independent of how
    `main`/`command_diff` render it."""
    a = tmp_path / "d.yaml"
    a.write_text("experiment_type: generic\nexpires: 2026-01-01\nparameters: {}\n")
    side = _load_side(a)
    with pytest.raises(ContractError) as exc_info:
        _parameters_hash_for(side)
    assert exc_info.value.code == "E-DIFF-CONFIG-UNREADABLE"


def test_h8b_diff_of_two_configs_with_an_unserializable_value_is_a_clean_diagnostic_not_a_traceback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """End to end through `main`, reproducing the whole-branch review's exact
    repro: an unquoted date under `yaml.safe_load` is a `datetime.date`, with
    no quoting mistake in sight. Before the fix this reached `main` as a bare
    `TypeError` after the four `not comparable` rows had already printed;
    `main`'s own `except PublishableError` is what turns a raised
    `ContractError` into a diagnostic on stderr rather than a traceback, so
    this asserts through the real dispatch path, not a direct
    `command_diff` call."""
    d = tmp_path / "d.yaml"
    d.write_text("experiment_type: generic\nexpires: 2026-01-01\nparameters: {}\n")
    code = main(["diff", str(d), str(d)])
    out, err = capsys.readouterr()
    assert code == EXIT_WRONG
    assert "E-DIFF-CONFIG-UNREADABLE" in err
    assert "Traceback" not in err
    # The four rows this operand pair CAN answer still printed before the
    # guard's own refusal — the "cheap close" the review names, not a
    # validate-first redesign that would withhold them.
    assert "not comparable" in out


def test_h8b_diff_of_a_config_with_an_unserializable_value_against_an_ordinary_config_still_raises(
    tmp_path: Path,
):
    """Property-preserving arm: an ordinary config beside the bad one still
    reaches the same guard, because `_parameters_hash_for` is called on BOTH
    sides regardless of which one is malformed — the crash site the review
    found is reachable from either operand position."""
    bad = tmp_path / "bad.yaml"
    bad.write_text("experiment_type: generic\nexpires: 2026-01-01\nparameters: {}\n")
    ok = tmp_path / "ok.yaml"
    ok.write_text("experiment_type: generic\nparameters: {}\n")
    with pytest.raises(ContractError) as exc_info:
        command_diff(ok, bad)
    assert exc_info.value.code == "E-DIFF-CONFIG-UNREADABLE"


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
    # Fix round 1, Minor 10: reverse only the OUTER (condition) order.
    # Each condition here holds exactly one fact (`calibration_id`), so a
    # per-fact reversal inside a one-entry dict is a no-op that decorated
    # this fixture without doing any work — reversing the two conditions'
    # order is the one reordering that actually changes iteration order,
    # and it is what the assertion below measures rather than assumes.
    reordered = dict(reversed(list(facts_b.items())))
    assert list(reordered) != list(facts_b), (
        "the reorder must actually change iteration order, or this fixture proves nothing"
    )
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
    # Fix round 1, Minor 5: the converse of the run-vs-run control below —
    # a config side never prints `not captured` either, which
    # `_render_parameters_hash_mixed`'s own docstring claims ("has no
    # reachable case here"). `parameters_hash` is always freshly computed
    # for a config and always written unconditionally for a run.
    assert "not captured" not in out


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


# ---------------------------------------------------------------------------
# Task 11: the upstream block (Decision 6), and the CLI arm.
#
# Fixture U: two runs identical in EVERY printed row — all five read
# `identical`, which is what proves the upstream block carries information
# no row does — one of which consumed an upstream through `io.reuse_from`
# and one which did not. A real `uv.lock` is committed (Fixture L's own
# mechanism) before either of the two compared runs, so `uv.lock` reads
# `identical` rather than `not captured`; `code_hash`/`input_manifest`/
# `parameters_hash` are identical by construction (same commit, same
# config, unedited between the two `main(["run", str(cfg)])` calls), and
# the Fixture-P apparatus template (same `calibration_id` both times) makes
# `apparatus` identical too. Which run consumes the upstream is decided by
# an ENVIRONMENT VARIABLE the starter step reads at call time, never by
# editing source or config, which is what keeps every other row identical:
# a step that instead had two different SOURCE forms (one calling
# `reuse_from`, one not) would make `code_hash` itself differ, defeating
# the fixture before it starts.
# ---------------------------------------------------------------------------

_H8B_FIXTURE_U_UPSTREAM_STEP = (
    "from publishable import BaseStep\n\n\n"
    "class Step(BaseStep):\n"
    '    scope = "run"\n\n'
    "    def run(self, cfg, io):\n"
    '        io.write("out.json", {{"n": 3}})\n'
)

_H8B_FIXTURE_U_STARTER_STEP = """\
import os

from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        units = list(io.units)
        for unit in units:
            io.record(unit.key, {{"present": True}})
        upstream_dir = os.environ.get("H8B_FIXTURE_U_UPSTREAM_DIR")
        upstream_step = os.environ.get("H8B_FIXTURE_U_UPSTREAM_STEP")
        if upstream_dir and upstream_step:
            io.reuse_from(upstream_dir, upstream_step, "out.json")
        return {{"n_units": len(units)}}
"""


def _resolve_latest(output_dir: Path) -> Path:
    """`<output_dir>/latest`, never a glob — a glob over a directory holding
    more than one `run_*` has no defined order (`Path.glob`), which is the
    exact hazard H8a's own § Corrections records having been observed. Falls
    back to `latest.txt` on the same precedent `point_latest` writes it on."""
    link = output_dir / "latest"
    if link.exists():
        return link.resolve()
    text = (output_dir / "latest.txt").read_text().strip()
    return output_dir / text


def _build_fixture_u_upstream(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> tuple[Path, str]:
    doc = run_a_project(
        tmp_path / "upstream_u",
        capsys=capsys,
        units=8,
        extra_steps=["publish"],
        extra_step_source=_H8B_FIXTURE_U_UPSTREAM_STEP,
    )
    run_dir = doc["run_dir"]
    record = yaml.safe_load((run_dir / "run.yaml").read_text())
    shared_names = list(record["execution"]["shared"].keys())
    assert len(shared_names) == 1
    return run_dir, shared_names[0]


def test_h8b_fixture_u_upstream_block_and_the_differ_only_line(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch, installed, registries
):
    """All five rows read `identical`, which is what proves the upstream
    block carries information no row does. That needs a REAL `uv.lock`
    (Fixture L's own mechanism) committed before either of the two runs
    this fixture compares — a throwaway first run scaffolds the project,
    then the lockfile is written and committed, then the two runs under
    comparison both happen on that same, now-unmoving commit, so
    `code_hash`/`uv.lock`/`input_manifest`/`parameters_hash` are identical
    by construction and `apparatus` is identical because the probe answers
    the same `calibration_id` every time — only the environment variable
    the starter step reads decides which of the two calls `reuse_from`."""
    import subprocess

    _install_h8b_probe(installed)
    upstream_run_dir, upstream_step = _build_fixture_u_upstream(tmp_path, capsys)

    monkeypatch.delenv("H8B_FIXTURE_U_UPSTREAM_DIR", raising=False)
    monkeypatch.delenv("H8B_FIXTURE_U_UPSTREAM_STEP", raising=False)
    monkeypatch.setenv("H8B_CALIBRATION_ID", "CAL-STABLE")
    doc = run_a_project(
        tmp_path / "proj_u",
        capsys=capsys,
        experiment_type="h8b_apparatus_assay",
        parameters={"instrument": {"model": "m1"}},
        sweep={"grid": {"instrument.model": ["m1", "m2"]}},
        _local_template=_H8B_APPARATUS_TEMPLATE,
        _starter_step=_H8B_FIXTURE_U_STARTER_STEP,
    )
    root = doc["root"]
    cfg = doc["cfg"]
    output_dir = doc["results_dir"]

    # Fixture L's mechanism: a real lockfile, committed, AFTER the
    # throwaway first run and BEFORE either of the two runs this fixture
    # actually compares — so both share one non-null `uv_lock_hash`.
    (root / "uv.lock").write_text("# a stand-in lockfile, fixture U\n")
    subprocess.run(["git", "add", "uv.lock"], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "lock"],
        cwd=root,
        check=True,
    )

    assert main(["run", str(cfg)]) == EXIT_OK
    run_x = _resolve_latest(output_dir)  # no upstream

    monkeypatch.setenv("H8B_FIXTURE_U_UPSTREAM_DIR", str(upstream_run_dir))
    monkeypatch.setenv("H8B_FIXTURE_U_UPSTREAM_STEP", upstream_step)
    assert main(["run", str(cfg)]) == EXIT_OK
    run_y = _resolve_latest(output_dir)  # WITH upstream
    assert run_y != run_x

    run_x_yaml = yaml.safe_load((run_x / "run.yaml").read_text())
    run_y_yaml = yaml.safe_load((run_y / "run.yaml").read_text())
    assert run_x_yaml["provenance"]["environment"]["uv_lock_hash"] is not None
    assert run_x_yaml["provenance"]["upstream"] == []
    assert len(run_y_yaml["provenance"]["upstream"]) == 1

    capsys.readouterr()
    code = command_diff(run_x, run_y)
    out = capsys.readouterr().out
    assert code == EXIT_OK

    # All five rows read `identical` — no row disagrees, and none is
    # `not captured` either, which is the pre-condition the "differ only"
    # line depends on.
    assert "DIFFERS" not in out
    assert "not captured" not in out
    for row in ROW_LABELS:
        assert re.search(rf"^{re.escape(row)}\s+identical", out, re.M), (row, out)
    # Fix round 1, Minor 6: the real EMITTED order, not just each row's
    # presence — this fixture is the one place `apparatus` actually prints
    # (Fixture R2/L's pairs omit it), so it is the one place that can pin
    # position for all five labels at once.
    assert _row_labels_in_output(out) == ROW_LABELS

    # The upstream block: not a sixth row, present, naming B's entry.
    assert re.search(r"^upstream$", out, re.M)
    upstream_run_id = run_y_yaml["provenance"]["upstream"][0]["run_id"]
    assert re.search(rf"^\s+B\s+{re.escape(upstream_run_id)}\s", out, re.M)
    assert not re.search(rf"^\s+A\s+{re.escape(upstream_run_id)}\s", out, re.M)

    # And the line that proves the block carries information no row does.
    assert "these runs differ only in their upstreams" in out


def test_h8b_upstream_block_absent_when_both_sides_upstream_is_empty(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """Fixture R2's own pair: `provenance.upstream` is `[]` on both sides
    (measured — every scaffolded run writes it), so the block must not
    print at all, and the "differ only" line certainly must not."""
    doc = run_a_project(tmp_path, units=8, capsys=capsys)
    run_a = doc["run_dir"]

    def edit(config: dict) -> None:
        config["parameters"]["analysis"]["min_samples"] += 1

    run_b = _second_run_after_edit(doc, edit)
    capsys.readouterr()
    command_diff(run_a, run_b)
    out = capsys.readouterr().out
    assert not re.search(r"^upstream$", out, re.M)
    assert "differ only in their upstreams" not in out


def test_h8b_a_draft_run_earns_the_draft_label_in_the_header(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """The draft label, from a fixture with `draft: true` hand-set on a
    record — `draft` itself is H9's, so a GENUINE draft run cannot be
    produced at this task; this pins the RENDER against the recorded key,
    not against a real draft run. See the batch report."""
    doc = run_a_project(tmp_path / "proj_a", units=8, capsys=capsys)
    run_dir = doc["run_dir"]
    run_yaml_path = run_dir / "run.yaml"
    record = yaml.safe_load(run_yaml_path.read_text())
    assert record["draft"] is False, "measured: draft: false present on every run"
    record["draft"] = True
    run_yaml_path.write_text(yaml.safe_dump(record, sort_keys=False))

    from publishable.diff import _load_side

    side = _load_side(run_dir)
    line = _header_line("A", side)
    assert "draft" in line.split()


# ---------------------------------------------------------------------------
# Mutations for the upstream block (task 11 steps 9-10).
# ---------------------------------------------------------------------------


def test_h8b_mutation_unconditional_upstream_block_caught_by_fixture_r2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    """M (step 9): print the block unconditionally. Caught by an ordinary
    two-run pair — `[]` on both sides is what every such pair writes
    (measured), so an unconditional block would print an empty `upstream`
    section on every comparison. The real code must NOT print it here;
    this test is the pin, and the mutation is applied and reverted against
    `diff.py` directly (reported in the batch report, not left applied)."""
    doc = run_a_project(tmp_path, units=8, capsys=capsys)
    run_a = doc["run_dir"]

    def edit(config: dict) -> None:
        config["parameters"]["analysis"]["min_samples"] += 1

    run_b = _second_run_after_edit(doc, edit)
    capsys.readouterr()
    command_diff(run_a, run_b)
    out = capsys.readouterr().out
    assert "upstream" not in out


def test_h8b_the_differ_only_line_absent_when_a_row_also_differs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch, installed, registries
):
    """The second discriminating fixture for the upstream block (step 10):
    upstreams differ AND `parameters_hash` differs. The block still prints
    (an upstream entry exists on one side), but the "differ only" line's
    whole content is that the OTHER rows agree — printing it beside a
    DIFFERS row would be a false claim, so it must be absent here even
    though an all-identical fixture (Fixture U) alone could not tell a
    correct build from one that prints the line unconditionally."""
    import subprocess

    _install_h8b_probe(installed)
    upstream_run_dir, upstream_step = _build_fixture_u_upstream(tmp_path, capsys)

    monkeypatch.delenv("H8B_FIXTURE_U_UPSTREAM_DIR", raising=False)
    monkeypatch.delenv("H8B_FIXTURE_U_UPSTREAM_STEP", raising=False)
    monkeypatch.setenv("H8B_CALIBRATION_ID", "CAL-STABLE")
    doc = run_a_project(
        tmp_path / "proj_u2",
        capsys=capsys,
        experiment_type="h8b_apparatus_assay",
        parameters={"instrument": {"model": "m1"}},
        sweep={"grid": {"instrument.model": ["m1", "m2"]}},
        _local_template=_H8B_APPARATUS_TEMPLATE,
        _starter_step=_H8B_FIXTURE_U_STARTER_STEP,
    )
    root = doc["root"]
    cfg = doc["cfg"]
    output_dir = doc["results_dir"]
    (root / "uv.lock").write_text("# a stand-in lockfile\n")
    subprocess.run(["git", "add", "uv.lock"], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "lock"],
        cwd=root,
        check=True,
    )
    assert main(["run", str(cfg)]) == EXIT_OK
    run_x = _resolve_latest(output_dir)

    # Edit a parameter AND set the upstream env vars, so both `parameters_hash`
    # and the upstream list move between run_x and run_y.
    config = yaml.safe_load(cfg.read_text())
    config["parameters"]["instrument"]["model"] = "m2"
    cfg.write_text(yaml.safe_dump(config))
    monkeypatch.setenv("H8B_FIXTURE_U_UPSTREAM_DIR", str(upstream_run_dir))
    monkeypatch.setenv("H8B_FIXTURE_U_UPSTREAM_STEP", upstream_step)
    assert main(["run", str(cfg)]) == EXIT_OK
    run_y = _resolve_latest(output_dir)
    assert run_y != run_x

    capsys.readouterr()
    command_diff(run_x, run_y)
    out = capsys.readouterr().out
    assert re.search(r"^parameters_hash\s+DIFFERS$", out, re.M)
    assert re.search(r"^upstream$", out, re.M)
    assert "these runs differ only in their upstreams" not in out


# ---------------------------------------------------------------------------
# Fix round 1, Major 2: Decision 2's third sub-ruling — a condition key
# present in one side's `facts` and not the other gets its own line — had
# no fixture. Hand-built records, on the review's own repro, exercise it
# directly through `_render_row` without a real probe: two conditions on
# one side, one of them entirely missing from the other's `facts`.
# ---------------------------------------------------------------------------


def _apparatus_record(facts: dict) -> dict:
    from publishable.apparatus import apparatus_hash

    return {"provenance": {"apparatus": {"hash": apparatus_hash(facts), "facts": facts}}}


def test_h8b_a_condition_missing_from_one_side_s_facts_gets_its_own_line():
    facts_a = {
        "00_baseline": {"calibration_id": "CAL-X"},
        "01_m=s": {"calibration_id": "CAL-X"},
    }
    facts_b = {"00_baseline": {"calibration_id": "CAL-X"}}  # "01_m=s" entirely absent
    record_a = _apparatus_record(facts_a)
    record_b = _apparatus_record(facts_b)

    lines = _render_row("apparatus", record_a, record_b)
    assert any(line.strip() == "01_m=s" or "01_m=s" in line for line in lines), lines
    matching = [line for line in lines if "01_m=s" in line]
    assert len(matching) == 1
    assert "no apparatus recorded for B" in matching[0]
    # And the reverse operand order names the other letter.
    reverse_lines = _render_row("apparatus", record_b, record_a)
    reverse_matching = [line for line in reverse_lines if "01_m=s" in line]
    assert len(reverse_matching) == 1
    assert "no apparatus recorded for A" in reverse_matching[0]


# ---------------------------------------------------------------------------
# Fix round 1, Major 4: the upstream block's `not captured` render
# (`_upstream_hash_repr`) was unreachable from any fixture — no test built
# an upstream entry with a missing hash. § Corrections correction 7:
# `UpstreamLedger.record` copies `record.get("code_hash")`/
# `record.get("parameters_hash")`, so either CAN be `None` on an honest
# record. Hand-built `_Side` objects exercise the render directly, on both
# fields independently, without needing a real `reuse_from` call.
# ---------------------------------------------------------------------------


def _side_with_upstream(entries: list[dict]) -> _Side:
    from pathlib import Path as _P

    return _Side(
        _P("unused"),
        "run record",
        record={"provenance": {"upstream": entries}},
    )


def test_h8b_an_upstream_entry_with_a_missing_hash_renders_not_captured():
    side_a = _side_with_upstream([])
    side_b = _side_with_upstream(
        [{"run_id": "run_x", "code_hash": None, "parameters_hash": "sha256:abcd1234", "used": []}]
    )
    lines = _upstream_block_lines(side_a, side_b)
    matching = [line for line in lines if "run_x" in line]
    assert len(matching) == 1
    assert "code_hash not captured" in matching[0]
    assert "parameters_hash sha256:abcd…" in matching[0]

    # And the reverse field: `parameters_hash` missing, `code_hash` present.
    side_c = _side_with_upstream(
        [{"run_id": "run_y", "code_hash": "sha256:deadbeef", "parameters_hash": None, "used": []}]
    )
    lines2 = _upstream_block_lines(side_a, side_c)
    matching2 = [line for line in lines2 if "run_y" in line]
    assert len(matching2) == 1
    assert "code_hash sha256:dead…" in matching2[0]
    assert "parameters_hash not captured" in matching2[0]


# ---------------------------------------------------------------------------
# Fix round 1, Minor 12: an empty-string fact/parameter value must render
# visibly, not as zero characters.
# ---------------------------------------------------------------------------


def test_h8b_an_empty_string_apparatus_fact_renders_visibly():
    facts_a = {"00_baseline": {"calibration_id": ""}}
    facts_b = {"00_baseline": {"calibration_id": "CAL-X"}}
    record_a = _apparatus_record(facts_a)
    record_b = _apparatus_record(facts_b)
    lines = _render_row("apparatus", record_a, record_b)
    detail = [line for line in lines if "calibration_id" in line]
    assert len(detail) == 1
    assert '"" → CAL-X' in detail[0]


def test_h8b_an_empty_string_parameter_value_renders_visibly():
    a = {"experiment_type": "generic", "parameters": {"analysis": {"method": ""}}}
    b = {"experiment_type": "generic", "parameters": {"analysis": {"method": "pearson"}}}
    lines = parameter_deltas(a, b)
    assert lines == ['  parameters.analysis.method  "" → pearson']


# ---------------------------------------------------------------------------
# H8c task 17: the guard pin, arm D — the three worked `diff` blocks' rows,
# as raw text. Captured by reading the documents, at `7f04755`. NEVER MOVES
# IN THIS SLICE: task 16 inserts its two per-side header lines ABOVE the
# `code_hash` line in each of these same three blocks and touches nothing
# at or below it, so a passing arm D — after task 16 lands — is itself the
# proof that no hash prefix, run ID, delta line, row label, row order or
# separator moved. This arm needs NO authorized editor for exactly that
# reason: if it fires, that is a finding, not a pin to update.
#
# The block is located by the `code_hash` ROW LINE it contains (the same
# `identical`/`DIFFERS` shape `_document_row_labels` above matches on),
# never by an ordinal or an nth-fence index — a positional locator has been
# wrong twice in this repo (`CLAUDE.md` § Locating a table row by
# position), and `reference.md` alone has more than one fence containing
# the literal substring "code_hash" (its full `run.yaml` example uses
# `code_hash: sha256:8e21...` in YAML syntax, which the stricter anchor
# below does not match). Raw text, never `yaml.safe_load` or any other
# reader: a defect that lives in *how* bytes are written is undone by a
# reader before the assertion reaches it (`CLAUDE.md`'s YAML-alias
# instance), which is why this parses the file's own lines rather than
# feeding them through any structured loader.
# ---------------------------------------------------------------------------


def _diff_block_raw_lines(path: Path) -> tuple[str, ...]:
    """The fenced block containing a `code_hash  identical|DIFFERS` row,
    from that row to the end of its own fence, as raw text lines. Fences in
    these documents don't nest, so consecutive ``` markers pair up in
    file order."""
    lines = path.read_text().splitlines()
    fence_idxs = [i for i, line in enumerate(lines) if line.startswith("```")]
    for start, end in zip(fence_idxs[0::2], fence_idxs[1::2], strict=True):
        body = lines[start + 1 : end]
        for j, line in enumerate(body):
            if re.match(r"^code_hash\s{2,}(identical|DIFFERS)\b", line):
                return tuple(body[j:])
    raise AssertionError(f"no `diff`-shaped fenced block found in {path}")


def test_h8c_arm_d_readme_worked_diff_block_rows(tmp_path: Path):
    """Arm D / README.md § The loop you'll actually live in."""
    assert _diff_block_raw_lines(README_MD) == (
        "code_hash          identical    sha256:8e21…",
        "input_manifest     identical    sha256:3d8a…",
        "uv.lock            identical    sha256:6b1f…",
        "parameters_hash    DIFFERS",
        "  parameters.analysis.min_samples   30 → 50",
    )


def test_h8c_arm_d_design_principles_worked_diff_block_rows(tmp_path: Path):
    """Arm D / design-principles.md § Same code, different parameters."""
    assert _diff_block_raw_lines(DESIGN_PRINCIPLES_MD) == (
        "code_hash          identical    sha256:8e21…",
        "input_manifest     identical    sha256:3d8a…",
        "uv.lock            identical    sha256:6b1f…",
        "parameters_hash    DIFFERS",
        "  parameters.analysis.method       pearson → spearman",
        "  parameters.analysis.min_samples  30 → 50",
    )


def test_h8c_arm_d_reference_worked_diff_block_rows(tmp_path: Path):
    """Arm D / reference.md § The apparatus core can only observe. The one
    of the three carrying an `apparatus` row instead of a `parameters_hash
    DIFFERS` — located correctly rather than by position is exactly what
    this arm proves for this file, since an earlier, YAML-syntax
    `code_hash: sha256:8e21...` line sits in an unrelated fenced block
    earlier in the same document."""
    assert _diff_block_raw_lines(REFERENCE_MD) == (
        "code_hash          identical    sha256:8e21…",
        "input_manifest     identical    sha256:3d8a…",
        "uv.lock            identical    sha256:6b1f…",
        "apparatus          DIFFERS",
        "  00_baseline.calibration_id         CAL-2026-07-19 → CAL-2026-08-02",
        "  01_method=spearman.calibration_id  CAL-2026-07-19 → CAL-2026-08-02",
        "parameters_hash    identical    sha256:1a2b…",
    )
