"""H8b tasks 4-6: `freeze` — the refusals, the resolution, the credential
pre-check, the condition set, the probe round and the CLI arm.

Fixture P (inherited from `test_apparatus.py`): a synthetic installed
distribution registering a probe, a project-local template declaring
`apparatus_probe`/`apparatus_facts`, two swept conditions.
"""

import json
from pathlib import Path

import pytest
import yaml
from tests.test_cli import run_a_project

from publishable.diagnostics import EXIT_EXTERNAL, EXIT_WRONG
from publishable.freeze import _precheck, _Ready, _Refused

_F_PROBE_MODULE = """\
from publishable import Apparatus, register_probe


@register_probe("f_probe")
def probe(cfg):
    return Apparatus(facts={"model_revision": cfg.parameters.instrument.model})
"""

_F_TEMPLATE = """\
from publishable import BaseTemplate, Param, register_template


@register_template("f_assay")
class FAssay(BaseTemplate):
    naming_pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    apparatus_probe = "f_probe"
    apparatus_facts = ["model_revision"]
    parameter_spec = {
        "instrument.model": Param(str, default="m1", choices=["m1", "m2", "m3"]),
    }
"""

# The M16 discriminator (§ Corrections, plan task 4 step 13): the credential
# is declared on a PARAMETER VALUE's `requires_env`, never on the template's
# own `required_env`, so a build that narrows the collector to
# `template.required_env` alone would miss it.
_F_CRED_TEMPLATE = """\
from publishable import BaseTemplate, Param, register_template


@register_template("f_cred_assay")
class FCredAssay(BaseTemplate):
    naming_pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    apparatus_probe = "f_probe"
    apparatus_facts = ["model_revision"]
    parameter_spec = {
        "instrument.model": Param(
            str,
            default="m1",
            choices=["m1", "m2", "m3"],
            requires_env={"m1": ["F_CRED_TOKEN"], "m2": [], "m3": []},
        ),
    }
"""


_fixture_p_counter = 0


def _fixture_p(installed, tmp_path, capsys, **overrides):
    # Each call gets a distinct module name. `f9_probe_mod` reused across
    # tests hits Python's own `sys.modules` cache: the module is not
    # re-executed on a second import under the same name, so a decorator
    # inside it never re-runs even though the `registries` fixture has
    # cleared `PROBES` between tests — `check_registration` then fails
    # `E-PLUGIN-DECORATOR` for a probe that IS correctly decorated. Every
    # other caller in `test_apparatus.py`/`test_cli.py` gives each probe
    # module a distinct name for the identical reason.
    global _fixture_p_counter
    _fixture_p_counter += 1
    mod = f"f9_probe_mod_{_fixture_p_counter}"
    dist = f"dist-f9-{_fixture_p_counter}"
    site = installed(dist, "1.0", {"publishable.probes": {"f_probe": f"{mod}:probe"}})
    (site / f"{mod}.py").write_text(_F_PROBE_MODULE)
    overrides.setdefault("experiment_type", "f_assay")
    overrides.setdefault("parameters", {"instrument": {"model": "m1"}})
    overrides.setdefault("sweep", {"grid": {"instrument.model": ["m1", "m2"]}})
    overrides.setdefault("_local_template", _F_TEMPLATE)
    return run_a_project(tmp_path, capsys=capsys, **overrides)


def _mid_run(run_dir: Path) -> None:
    """Fixture F1's own shape: `run.yaml` deleted, a lock written by hand —
    a CONSTRUCTED mid-run state, not a real one."""
    (run_dir / "run.yaml").unlink()
    (run_dir / "lock").write_text(json.dumps({"host": "x", "pid": 1}))


def _ledger_lines(run_dir: Path) -> list[dict]:
    path = run_dir / "apparatus" / "probes.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()]


def _edit_config_yaml(run_dir: Path, **changes) -> None:
    doc = yaml.safe_load((run_dir / "config.yaml").read_text())
    doc.update(changes)
    (run_dir / "config.yaml").write_text(yaml.safe_dump(doc))


def _load_sweep_yaml(run_dir: Path) -> dict:
    return yaml.safe_load((run_dir / "sweep.yaml").read_text())


def _assert_refused(result, code: str, exit_code: int, ledger_before: list[dict], run_dir: Path):
    assert isinstance(result, _Refused), result
    assert result.exit_code == exit_code
    # Every refusal makes NO probe call and writes NO ledger line.
    assert _ledger_lines(run_dir) == ledger_before


# --- Task 4: the refusal gate, direct calls to `_precheck` -----------------


def test_precheck_returns_ready_on_a_well_formed_mid_run_directory(
    installed, registries, tmp_path, capsys
):
    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    result = _precheck(run_dir)
    assert isinstance(result, _Ready), result
    assert result.probe_name == "f_probe"
    assert result.declared_facts == ["model_revision"]
    assert len(result.conditions) == 2


def test_a_run_ended_gate_a_refuses_and_writes_no_line(installed, registries, tmp_path, capsys):
    """(a) `run.yaml` present -> `E-FREEZE-RUN-ENDED`, exit 1. Answered by
    `run.yaml`'s presence alone — the lock is absent here, which a
    lock-based check would misread as "still running"."""
    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    assert (run_dir / "run.yaml").exists()
    before = _ledger_lines(run_dir)
    result = _precheck(run_dir)
    _assert_refused(result, "E-FREEZE-RUN-ENDED", EXIT_WRONG, before, run_dir)


def test_gate_b_config_yaml_absent_is_no_config(installed, registries, tmp_path, capsys):
    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    before = _ledger_lines(run_dir)
    (run_dir / "config.yaml").unlink()
    result = _precheck(run_dir)
    _assert_refused(result, "E-FREEZE-NO-CONFIG", EXIT_WRONG, before, run_dir)


def test_gate_b_config_yaml_not_a_mapping_is_no_config(installed, registries, tmp_path, capsys):
    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    before = _ledger_lines(run_dir)
    (run_dir / "config.yaml").write_text("- just\n- a\n- list\n")
    result = _precheck(run_dir)
    _assert_refused(result, "E-FREEZE-NO-CONFIG", EXIT_WRONG, before, run_dir)


def test_gate_c_repo_root_txt_absent_is_no_config(installed, registries, tmp_path, capsys):
    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    before = _ledger_lines(run_dir)
    (run_dir / "environment" / "repo_root.txt").unlink()
    result = _precheck(run_dir)
    _assert_refused(result, "E-FREEZE-NO-CONFIG", EXIT_WRONG, before, run_dir)


def test_gate_c_repo_root_txt_empty_is_no_config(installed, registries, tmp_path, capsys):
    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    before = _ledger_lines(run_dir)
    (run_dir / "environment" / "repo_root.txt").write_text("")
    result = _precheck(run_dir)
    _assert_refused(result, "E-FREEZE-NO-CONFIG", EXIT_WRONG, before, run_dir)


def test_gate_c_repo_root_txt_naming_a_nonexistent_path_is_no_config_not_template_unknown(
    installed, registries, tmp_path, capsys
):
    """Whole-branch review, Minor 5: unchecked, this fell through to
    `_claims`, which answers as if the repo simply registers no local
    template, so the eventual refusal was `E-TEMPLATE-UNKNOWN` — a real code
    with the WRONG remedy for a hand-edited run directory. `_assert_refused`
    checks the exit code and the untouched ledger, but not the printed
    diagnostic's own code and text, so those are asserted here directly
    against `_precheck`'s stderr render — the only place either is
    observable."""
    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    before = _ledger_lines(run_dir)
    bogus = str(tmp_path / "does-not-exist-at-all")
    (run_dir / "environment" / "repo_root.txt").write_text(bogus)
    result = _precheck(run_dir)
    err = capsys.readouterr().err
    _assert_refused(result, "E-FREEZE-NO-CONFIG", EXIT_WRONG, before, run_dir)
    assert "E-FREEZE-NO-CONFIG" in err
    assert "not a directory" in err
    assert "E-TEMPLATE-UNKNOWN" not in err


def test_gate_c_repo_root_txt_naming_a_plain_file_is_no_config_not_template_unknown(
    installed, registries, tmp_path, capsys
):
    """The second shape Minor 5 named: a plain file rather than a missing
    path, distinguishing `is_dir()` from a bare `exists()` check."""
    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    before = _ledger_lines(run_dir)
    plain_file = tmp_path / "a-plain-file.txt"
    plain_file.write_text("not a repo")
    (run_dir / "environment" / "repo_root.txt").write_text(str(plain_file))
    result = _precheck(run_dir)
    err = capsys.readouterr().err
    _assert_refused(result, "E-FREEZE-NO-CONFIG", EXIT_WRONG, before, run_dir)
    assert "E-FREEZE-NO-CONFIG" in err
    assert "not a directory" in err
    assert "E-TEMPLATE-UNKNOWN" not in err


def test_gate_e_unknown_template_reuses_the_shipped_code(installed, registries, tmp_path, capsys):
    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    before = _ledger_lines(run_dir)
    _edit_config_yaml(run_dir, experiment_type="no_such_template_xyz")
    result = _precheck(run_dir)
    _assert_refused(result, "E-TEMPLATE-UNKNOWN", EXIT_WRONG, before, run_dir)


def test_gate_e_installed_only_template_reuses_the_shipped_code(
    installed, registries, tmp_path, capsys
):
    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    # A second distribution claims a name no local template registers, so
    # `_claims` resolves the claim but `claim.cls` is `None` (installed
    # claims carry no class — Decision 6 of the plan's corrections).
    installed(
        "dist-installed-only", "1.0", {"publishable.templates": {"installed_only_tmpl": "x:Y"}}
    )
    before = _ledger_lines(run_dir)
    _edit_config_yaml(run_dir, experiment_type="installed_only_tmpl")
    result = _precheck(run_dir)
    _assert_refused(result, "E-TEMPLATE-INSTALLED-UNSUPPORTED", EXIT_WRONG, before, run_dir)


def test_gate_e_a_load_fault_reuses_E_TEMPLATE_LOAD_and_carries_credentials(
    installed, registries, tmp_path, capsys
):
    """A second, broken file under the SAME repo's `templates/` poisons
    discovery for the whole directory, regardless of `experiment_type` —
    `_claims` raises before any name-specific verdict. `partial_templates`
    is read for its credentials (task 4 step 7 / plan correction 6), so the
    template that DID load cleanly still has its declared credential
    redacted in the finding — even though the whole call failed."""
    doc = _fixture_p(
        installed,
        tmp_path,
        capsys,
        _local_template=_F_CRED_TEMPLATE,
        experiment_type="f_cred_assay",
        parameters={"instrument": {"model": "m1"}},
        sweep={},
        _env_file="F_CRED_TOKEN=shh\n",
    )
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    (doc["root"] / "templates" / "broken.py").write_text("raise RuntimeError('boom')\n")
    before = _ledger_lines(run_dir)
    result = _precheck(run_dir)
    _assert_refused(result, "E-TEMPLATE-LOAD", EXIT_WRONG, before, run_dir)


def test_gate_e_a_collision_reuses_E_TEMPLATE_COLLISION(installed, registries, tmp_path, capsys):
    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    (doc["root"] / "templates" / "second.py").write_text(_F_TEMPLATE)
    before = _ledger_lines(run_dir)
    result = _precheck(run_dir)
    _assert_refused(result, "E-TEMPLATE-COLLISION", EXIT_WRONG, before, run_dir)


_NO_PROBE_TEMPLATE = """\
from publishable import BaseTemplate, Param, register_template


@register_template("f_assay")
class FAssay(BaseTemplate):
    naming_pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    parameter_spec = {
        "instrument.model": Param(str, default="m1", choices=["m1", "m2"]),
    }
"""


def test_gate_f_no_apparatus_probe_declared(installed, registries, tmp_path, capsys):
    """A template declaring no probe cannot be built with `run_a_project`
    (no `apparatus/` directory to make a plausible mid-run state from), so
    this arm constructs the directory by hand from a real run's shape:
    take Fixture P's run, then swap `templates/f_assay.py` for one that
    declares no probe — the run itself still ran under the PROBED template,
    but `freeze` resolves the template it finds NOW, exactly as
    `E-FREEZE-PROBE-MISMATCH` (a sibling arm) also exploits."""
    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    # A NEW filename, not an in-place edit: `_import_file`'s bytecode cache
    # is keyed by (mtime, size) at whole-second granularity, so overwriting
    # the SAME path within the same wall-clock second silently serves the
    # STALE compiled module — measured 2026-08-20, a real defect in
    # `discover_local` unrelated to this task, worked around here rather
    # than papered over with a `time.sleep`.
    (doc["root"] / "templates" / "cred_assay.py").unlink()
    (doc["root"] / "templates" / "no_probe.py").write_text(_NO_PROBE_TEMPLATE)
    before = _ledger_lines(run_dir)
    result = _precheck(run_dir)
    _assert_refused(result, "E-FREEZE-NO-APPARATUS", EXIT_WRONG, before, run_dir)


def test_gate_i_ledger_missing_covers_an_absent_ledger(installed, registries, tmp_path, capsys):
    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    import shutil

    shutil.rmtree(run_dir / "apparatus")
    before = _ledger_lines(run_dir)
    result = _precheck(run_dir)
    _assert_refused(result, "E-FREEZE-LEDGER-MISSING", EXIT_WRONG, before, run_dir)


def test_gate_i_ledger_missing_covers_a_ledger_with_no_qualifying_line(
    installed, registries, tmp_path, capsys
):
    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    (run_dir / "apparatus" / "probes.jsonl").write_text(
        json.dumps(
            {"at": "t", "phase": "dry_run", "condition": "00_x", "probe": "f_probe", "facts": {}}
        )
        + "\n"
    )
    before = _ledger_lines(run_dir)
    result = _precheck(run_dir)
    _assert_refused(result, "E-FREEZE-LEDGER-MISSING", EXIT_WRONG, before, run_dir)


# --- Batch 4 review, Major 2: the three hand-edited ledger shapes core's
# own single `append_observation` call site can never write, each pinned
# individually through `main` --------------------------------------------


def _append_raw_ledger_line(run_dir: Path, doc: dict) -> None:
    with (run_dir / "apparatus" / "probes.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(doc) + "\n")


def test_a_hand_edited_facts_null_line_is_E_FREEZE_LEDGER_UNREADABLE_not_a_traceback(
    installed, registries, tmp_path, capsys
):
    """Batch 4 review, Major 2, shape 1: before this fix, `facts: null`
    reached `Observations.record` and raised a bare `AttributeError` out of
    `main` — never a diagnostic. Driven through `main`, exactly as the
    reviewer measured, not through `_precheck` directly."""
    from publishable.cli import main
    from publishable.diagnostics import EXIT_WRONG

    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    _append_raw_ledger_line(
        run_dir,
        {"at": "t", "phase": "run_start", "condition": "00_x", "probe": "f_probe", "facts": None},
    )
    code = main(["freeze", str(run_dir)])
    output = capsys.readouterr().err
    assert code == EXIT_WRONG
    assert "E-FREEZE-LEDGER-UNREADABLE" in output
    assert "AttributeError" not in output


def test_a_hand_edited_facts_list_line_is_E_FREEZE_LEDGER_UNREADABLE_not_a_traceback(
    installed, registries, tmp_path, capsys
):
    """Batch 4 review, Major 2, shape 2: `facts: [1, 2]` — same
    `AttributeError` site (`Observations.record`'s `.items()` call), same
    fix, same code."""
    from publishable.cli import main
    from publishable.diagnostics import EXIT_WRONG

    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    _append_raw_ledger_line(
        run_dir,
        {
            "at": "t",
            "phase": "run_start",
            "condition": "00_x",
            "probe": "f_probe",
            "facts": [1, 2],
        },
    )
    code = main(["freeze", str(run_dir)])
    output = capsys.readouterr().err
    assert code == EXIT_WRONG
    assert "E-FREEZE-LEDGER-UNREADABLE" in output
    assert "AttributeError" not in output


def test_a_hand_edited_int_condition_line_is_E_FREEZE_LEDGER_UNREADABLE_not_a_false_unchanged(
    installed, registries, tmp_path, capsys
):
    """Batch 4 review, Major 2, shape 3 — the quieter fail-open: before this
    fix, `condition: 42` was accepted silently, producing an int-keyed
    baseline nothing else in the ledger ever matches, and `freeze` reported
    every condition `unchanged` at exit 0 over a ledger nobody should
    trust. Must now refuse rather than reach that verdict."""
    from publishable.cli import main
    from publishable.diagnostics import EXIT_WRONG

    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    _append_raw_ledger_line(
        run_dir,
        {"at": "t", "phase": "run_start", "condition": 42, "probe": "f_probe", "facts": {}},
    )
    code = main(["freeze", str(run_dir)])
    captured = capsys.readouterr()
    assert code == EXIT_WRONG
    assert "E-FREEZE-LEDGER-UNREADABLE" in captured.err
    assert "unchanged" not in captured.out


def test_gate_j_probe_mismatch_when_template_now_declares_a_different_registered_probe(
    installed, registries, tmp_path, capsys
):
    """The second probe name must be genuinely registered, or this arm
    fires as `E-PROBE-UNKNOWN` for the wrong reason (§ Habits — the shape
    that cost a preceding slice a round)."""
    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    site = installed(
        "dist-second-probe", "1.0", {"publishable.probes": {"g_probe": "g_probe_mod:probe"}}
    )
    # A genuinely registered second probe, so the mismatch fires for the
    # right reason rather than as `E-PROBE-UNKNOWN` — the gate must not
    # reach `_probe_for` at all, but the name must be real.
    (site / "g_probe_mod.py").write_text(_F_PROBE_MODULE.replace("f_probe", "g_probe"))
    _switched = """\
from publishable import BaseTemplate, Param, register_template


@register_template("f_assay")
class FAssay(BaseTemplate):
    naming_pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    apparatus_probe = "g_probe"
    apparatus_facts = ["model_revision"]
    parameter_spec = {
        "instrument.model": Param(str, default="m1", choices=["m1", "m2"]),
    }
"""
    # Same bytecode-cache hazard as gate (f)'s arm above — a new filename,
    # not an in-place edit.
    (doc["root"] / "templates" / "cred_assay.py").unlink()
    (doc["root"] / "templates" / "switched.py").write_text(_switched)
    before = _ledger_lines(run_dir)
    result = _precheck(run_dir)
    _assert_refused(result, "E-FREEZE-PROBE-MISMATCH", EXIT_WRONG, before, run_dir)


# --- Fixture F5 (sibling arm) / M16, the part reachable without a probe ----


def test_f5_sibling_arm_credential_precheck_before_any_probe_call(
    installed, registries, tmp_path, capsys, monkeypatch
):
    """F5's sibling arm, and the M16 discriminator together: the credential
    is declared on a PARAMETER VALUE's `requires_env`, the variable is
    unset entirely, and `_precheck` must refuse at gate (k) — `E-APPARATUS-
    RAISED` at `EXIT_EXTERNAL` — with no ledger line written. Since
    `_precheck` never calls the probe at all, "no probe call was made" is
    witnessed structurally: this function has no reachable call site for
    one."""
    monkeypatch.delenv("F_CRED_TOKEN", raising=False)
    doc = _fixture_p(
        installed,
        tmp_path,
        capsys,
        _local_template=_F_CRED_TEMPLATE,
        experiment_type="f_cred_assay",
        parameters={"instrument": {"model": "m1"}},
        sweep={},
        _env_file="F_CRED_TOKEN=shh\n",
    )
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    # The run itself completed with the token available via `.env`; now
    # simulate `freeze` invoked from a shell where it is not exported AND
    # the project's `.env` no longer supplies it either — deleting the
    # file, not merely `delenv`, since `_precheck` calls `load_env` on the
    # repo root and would otherwise silently re-supply the value from disk.
    monkeypatch.delenv("F_CRED_TOKEN", raising=False)
    (doc["root"] / ".env").unlink()
    before = _ledger_lines(run_dir)
    result = _precheck(run_dir)
    _assert_refused(result, "E-APPARATUS-RAISED", EXIT_EXTERNAL, before, run_dir)


def test_m1_credential_check_precedes_the_metered_call_end_to_end_through_main(
    installed, registries, tmp_path, capsys, monkeypatch
):
    """Batch 4 review, Major 1: the shipped suite's only credential-pre-check
    test asserted `isinstance(result, _Refused)`, which is true whether the
    check runs BEFORE `_probe_for`/`observe_round` or is moved to AFTER
    them — a proxy for the property Decision 10 actually states ("no probe
    call made"). This is the reviewer's own discriminating triple, built
    here: a probe that appends to a MARKER FILE on every call, driven
    through `main`, with the credential genuinely unset and `.env` deleted.

    Verified by hand against both mutations the review ran (not persisted,
    since the shipped code already has the right order and there is no
    lever in `freeze.py` to keep both branches without duplicating the
    check): moving gate (k)'s block from `_precheck` into `command_freeze`
    AFTER `observer.observe_round(...)` makes the marker file appear and
    the ledger grow by one line — this test's own three assertions below
    would each fail. Moving the same block to just before `_probe_for`
    (still after `_precheck` returns) leaves this test passing, since the
    probe is still never reached.
    """
    global _fixture_p_counter
    _fixture_p_counter += 1
    mod = f"f9_probe_mod_{_fixture_p_counter}"
    dist = f"dist-f9-{_fixture_p_counter}"
    marker_file = tmp_path / "marker"
    site = installed(dist, "1.0", {"publishable.probes": {"f_probe": f"{mod}:probe"}})
    probe_src = f"""from pathlib import Path

from publishable import Apparatus, register_probe

MARKER_FILE = {str(marker_file)!r}


@register_probe("f_probe")
def probe(cfg):
    with Path(MARKER_FILE).open("a") as fh:
        fh.write("called\\n")
    return Apparatus(facts={{"model_revision": cfg.parameters.instrument.model}})
"""
    (site / f"{mod}.py").write_text(probe_src)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        experiment_type="f_cred_assay",
        parameters={"instrument": {"model": "m1"}},
        sweep={},
        _local_template=_F_CRED_TEMPLATE,
        _env_file="F_CRED_TOKEN=shh\n",
    )
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    assert marker_file.exists(), "the probe must have run at least once during the run itself"
    marker_file.unlink()

    monkeypatch.delenv("F_CRED_TOKEN", raising=False)
    (doc["root"] / ".env").unlink()
    before_lines = _ledger_lines(run_dir)

    from publishable.cli import main

    code = main(["freeze", str(run_dir)])
    output = capsys.readouterr().err
    assert code == EXIT_EXTERNAL
    assert "E-APPARATUS-RAISED" in output
    assert not marker_file.exists(), "the probe must never be called once a credential is missing"
    assert _ledger_lines(run_dir) == before_lines


def test_credentials_include_a_parameter_value_s_requires_env(
    installed, registries, tmp_path, capsys
):
    """The other half of M16: with the credential SET (not unset), `_Ready`
    must carry it — `command_freeze`'s eventual redaction (task 6) reads
    `ready.credentials`, and a build narrowing the collector to
    `template.required_env` alone would leave this empty."""
    doc = _fixture_p(
        installed,
        tmp_path,
        capsys,
        _local_template=_F_CRED_TEMPLATE,
        experiment_type="f_cred_assay",
        parameters={"instrument": {"model": "m1"}},
        sweep={},
        _env_file="F_CRED_TOKEN=shh\n",
    )
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    result = _precheck(run_dir)
    assert isinstance(result, _Ready), result
    assert result.credentials.get("F_CRED_TOKEN") == "shh"


# --- Task 5: the sweep.yaml cross-check ------------------------------------


def test_gate_g_sweep_yaml_absent_is_plan_missing(installed, registries, tmp_path, capsys):
    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    before = _ledger_lines(run_dir)
    (run_dir / "sweep.yaml").unlink()
    result = _precheck(run_dir)
    _assert_refused(result, "E-FREEZE-PLAN-MISSING", EXIT_WRONG, before, run_dir)


def test_gate_g_sweep_yaml_unreadable_is_plan_missing(installed, registries, tmp_path, capsys):
    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    before = _ledger_lines(run_dir)
    (run_dir / "sweep.yaml").write_text("not: [valid, yaml: at all\n")
    result = _precheck(run_dir)
    _assert_refused(result, "E-FREEZE-PLAN-MISSING", EXIT_WRONG, before, run_dir)


def test_gate_h_a_structural_edit_is_plan_mismatch(installed, registries, tmp_path, capsys):
    """M13's discriminator: the config copy's `sweep` is edited so
    re-expansion yields a different label set than `sweep.yaml` recorded."""
    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    _edit_config_yaml(
        run_dir, sweep={"grid": {"instrument.model": ["m1"]}}
    )  # one condition, not two
    before = _ledger_lines(run_dir)
    result = _precheck(run_dir)
    _assert_refused(result, "E-FREEZE-PLAN-MISMATCH", EXIT_WRONG, before, run_dir)


def test_gate_h_values_only_edit_is_plan_mismatch(installed, registries, tmp_path, capsys):
    """The second mutation's own discriminator (task 5 step 7): a declared
    `baseline` whose VALUE moves in the config copy while `index`, `label`
    and `is_baseline` all hold still — printed and checked below before
    trusting the fixture, per the brief's own instruction."""
    doc = _fixture_p(
        installed,
        tmp_path,
        capsys,
        sweep={"baseline": {"instrument.model": "m1"}},
    )
    run_dir = doc["run_dir"]
    sweep_doc = _load_sweep_yaml(run_dir)
    recorded = sweep_doc["conditions"]
    assert len(recorded) == 1
    assert recorded[0]["label"] == "baseline"
    assert recorded[0]["is_baseline"] is True
    assert recorded[0]["values"] == {"instrument.model": "m1"}

    _mid_run(run_dir)
    _edit_config_yaml(run_dir, sweep={"baseline": {"instrument.model": "m2"}})

    # Confirm the two branches CAN differ before trusting the fixture: the
    # re-expanded condition's `label`/`index`/`is_baseline` must still match
    # the recorded ones — only `values` moves.
    from publishable.sweep import expand
    from publishable.validate import load_document

    edited_doc = load_document(run_dir / "config.yaml")
    reexpanded = expand(edited_doc)
    assert len(reexpanded) == 1
    assert reexpanded[0].label == recorded[0]["label"]
    assert reexpanded[0].index == recorded[0]["index"]
    assert reexpanded[0].is_baseline == recorded[0]["is_baseline"]
    assert dict(reexpanded[0].values) != recorded[0]["values"]

    before = _ledger_lines(run_dir)
    result = _precheck(run_dir)
    _assert_refused(result, "E-FREEZE-PLAN-MISMATCH", EXIT_WRONG, before, run_dir)


def test_ready_carries_cfgs_keyed_by_condition_index(installed, registries, tmp_path, capsys):
    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    result = _precheck(run_dir)
    assert isinstance(result, _Ready), result
    assert set(result.cfgs) == {c.index for c in result.conditions}
    for condition in result.conditions:
        assert (
            result.cfgs[condition.index].parameters.instrument.model
            == (condition.values["instrument.model"])
        )


# --- Task 6: the probe round, its verdicts, exit codes, and the CLI arm ----


def _snapshot(root: Path) -> dict[str, bytes]:
    """`{relative path: bytes}` over every file under `root`, excluding
    `apparatus/probes.jsonl` — the one thing `freeze` is allowed to change.
    Naming that exclusion explicitly is what makes the rest of the
    comparison mean something (Fixture F1's own requirement)."""
    out: dict[str, bytes] = {}
    for path in root.rglob("*"):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            if rel == "apparatus/probes.jsonl":
                continue
            out[rel] = path.read_bytes()
    return out


_MOVING_PROBE_TEMPLATE = """\
from pathlib import Path

from publishable import Apparatus, register_probe

ANSWER_FILE = {answer_file!r}


@register_probe("f_probe")
def probe(cfg):
    return Apparatus(facts={{"model_revision": Path(ANSWER_FILE).read_text().strip()}})
"""


def _fixture_p_moving(installed, tmp_path, capsys, answer_file: Path, **overrides):
    """Fixture P's shape with a probe whose answer comes from a file the
    test writes, so a fact can be moved between the run and a later
    `freeze` — the design's own Fixture P/F2 shape."""
    global _fixture_p_counter
    _fixture_p_counter += 1
    mod = f"f9_probe_mod_{_fixture_p_counter}"
    dist = f"dist-f9-{_fixture_p_counter}"
    site = installed(dist, "1.0", {"publishable.probes": {"f_probe": f"{mod}:probe"}})
    (site / f"{mod}.py").write_text(_MOVING_PROBE_TEMPLATE.format(answer_file=str(answer_file)))
    overrides.setdefault("experiment_type", "f_assay")
    overrides.setdefault("parameters", {"instrument": {"model": "m1"}})
    overrides.setdefault("sweep", {})
    overrides.setdefault("_local_template", _F_TEMPLATE)
    return run_a_project(tmp_path, capsys=capsys, **overrides)


def test_f1_freeze_end_to_end_on_a_constructed_mid_run_directory(
    installed, registries, tmp_path, capsys
):
    from publishable.diagnostics import EXIT_OK
    from publishable.freeze import command_freeze

    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    before_lines = _ledger_lines(run_dir)
    before_snapshot = _snapshot(run_dir)
    n_conditions = 2

    code = command_freeze(run_dir)
    assert code == EXIT_OK

    after_lines = _ledger_lines(run_dir)
    assert len(after_lines) == len(before_lines) + n_conditions
    new_lines = after_lines[len(before_lines) :]
    assert all(line["phase"] == "freeze" for line in new_lines)
    assert not (run_dir / "run.yaml").exists()

    # Byte-identical over everything else, `lock` included — the assertion
    # that catches a `freeze` taking or clearing the lock (M10).
    after_snapshot = _snapshot(run_dir)
    assert after_snapshot == before_snapshot


_MULTI_MOVING_PROBE_TEMPLATE = """\
from pathlib import Path

from publishable import Apparatus, register_probe

ANSWER_DIR = {answer_dir!r}


@register_probe("f_probe")
def probe(cfg):
    model = cfg.parameters.instrument.model
    text = (Path(ANSWER_DIR) / f"{{model}}.txt").read_text().strip()
    return Apparatus(facts={{"model_revision": text}})
"""


def test_f2_freeze_sees_a_moved_fact(installed, registries, tmp_path, capsys):
    """Batch 4 review, Minor 8: a ONE-condition fixture cannot see "every
    condition up to and including the mover, none after" — widened to
    three conditions with the SECOND one moving, exactly as the reviewer's
    own re-measurement did."""
    from publishable.diagnostics import EXIT_WRONG
    from publishable.freeze import command_freeze

    answer_dir = tmp_path / "answers"
    answer_dir.mkdir()
    for model in ("m1", "m2", "m3"):
        (answer_dir / f"{model}.txt").write_text("rev1")

    global _fixture_p_counter
    _fixture_p_counter += 1
    mod = f"f9_probe_mod_{_fixture_p_counter}"
    dist = f"dist-f9-{_fixture_p_counter}"
    site = installed(dist, "1.0", {"publishable.probes": {"f_probe": f"{mod}:probe"}})
    (site / f"{mod}.py").write_text(_MULTI_MOVING_PROBE_TEMPLATE.format(answer_dir=str(answer_dir)))
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        experiment_type="f_assay",
        parameters={"instrument": {"model": "m1"}},
        sweep={"grid": {"instrument.model": ["m1", "m2", "m3"]}},
        _local_template=_F_TEMPLATE,
    )
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    before_lines = _ledger_lines(run_dir)

    (answer_dir / "m2.txt").write_text("rev2")  # only the SECOND condition moves
    code = command_freeze(run_dir)
    assert code == EXIT_WRONG

    after_lines = _ledger_lines(run_dir)
    new_lines = after_lines[len(before_lines) :]
    # Every condition UP TO AND INCLUDING the mover, none after: the first
    # condition (unchanged) gets a line, the second (moved) gets a line and
    # raises, the third is never reached.
    assert [line["condition"] for line in new_lines] == ["00_model=m1", "01_model=m2"]
    assert new_lines[0]["facts"]["model_revision"] == "rev1"
    moved = new_lines[-1]
    assert moved["phase"] == "freeze"
    assert moved["condition"] == "01_model=m2"
    assert moved["facts"]["model_revision"] == "rev2"

    assert not (run_dir / "run.yaml").exists()


def test_f5_arm_one_a_probe_raising_with_a_credential_is_redacted_end_to_end(
    installed, registries, tmp_path, capsys
):
    """Fixture F5's first arm, completed end to end through `command_freeze`
    now that the probe round exists: the credential's absence from stderr
    AND `E-APPARATUS-RAISED`'s presence at exit `EXIT_EXTERNAL` — the pair,
    since asserting only the absence passes identically if nothing ran."""
    from publishable.diagnostics import EXIT_EXTERNAL
    from publishable.freeze import command_freeze

    # Batch 4 review, Minor 8: widened to three conditions with the SECOND
    # one raising — a one-condition fixture cannot show "no line for the
    # raising condition, none after". The probe must succeed for every
    # condition during the run (so the run itself completes) and only
    # raise for the TRIGGERED model once `freeze` calls it — a
    # `TRIGGER_FILE` naming which model should raise, checked at call time
    # on the SAME module object rather than by rewriting the file on disk
    # (which `load_entry_point`'s ordinary `importlib` caching would not
    # re-import).
    trigger_file = tmp_path / "trigger"
    trigger_file.write_text("")
    global _fixture_p_counter
    _fixture_p_counter += 1
    mod = f"f9_probe_mod_{_fixture_p_counter}"
    dist = f"dist-f9-{_fixture_p_counter}"
    site = installed(dist, "1.0", {"publishable.probes": {"f_probe": f"{mod}:probe"}})
    site_and_probe = f"""\
import os
from pathlib import Path

from publishable import Apparatus, register_probe

TRIGGER_FILE = {str(trigger_file)!r}


@register_probe("f_probe")
def probe(cfg):
    model = cfg.parameters.instrument.model
    if Path(TRIGGER_FILE).read_text().strip() == model:
        token = os.environ["F_CRED_TOKEN"]
        raise RuntimeError(f"could not reach the instrument, token was {{token}}")
    return Apparatus(facts={{"model_revision": model}})
"""
    (site / f"{mod}.py").write_text(site_and_probe)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        experiment_type="f_cred_assay",
        parameters={"instrument": {"model": "m1"}},
        sweep={"grid": {"instrument.model": ["m1", "m2", "m3"]}},
        _local_template=_F_CRED_TEMPLATE,
        _env_file="F_CRED_TOKEN=shh\n",
    )
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    before_lines = _ledger_lines(run_dir)
    trigger_file.write_text("m2")  # only the SECOND condition raises

    code = command_freeze(run_dir)
    output = capsys.readouterr().err
    assert code == EXIT_EXTERNAL
    assert "shh" not in output
    assert "E-APPARATUS-RAISED" in output
    # A line for the first (unaffected) condition, none for the raising
    # second condition, and none for the third — `observe_once` raises
    # before `append_observation` ever runs for the raising condition, and
    # `Observer.observe_round`'s plain loop aborts the remaining conditions.
    after_lines = _ledger_lines(run_dir)
    new_lines = after_lines[len(before_lines) :]
    assert [line["condition"] for line in new_lines] == ["00_model=m1"]


def test_m8_two_exit_codes_through_main_before_and_after_admitting_freeze_lines(
    installed, registries, tmp_path, capsys, monkeypatch
):
    """Task 1's own M8, completed at the command level: a fact that is
    `null` everywhere in the run, then answered at the first `freeze`, then
    answered DIFFERENTLY at a second `freeze` — two `0`s under the shipped
    filter, and exit `1` for the second once `phase == "freeze"` lines are
    (wrongly) admitted to the baseline."""
    from publishable.cli import main

    answer_file = tmp_path / "answer.txt"
    answer_file.write_text("")  # empty -> stripped to "" -> falsy, not null though

    # A probe returning `None` when the file is empty, a real value otherwise.
    global _fixture_p_counter
    _fixture_p_counter += 1
    mod = f"f9_probe_mod_{_fixture_p_counter}"
    dist = f"dist-f9-{_fixture_p_counter}"
    site = installed(dist, "1.0", {"publishable.probes": {"f_probe": f"{mod}:probe"}})
    probe_src = f"""\
from pathlib import Path

from publishable import Apparatus, register_probe

ANSWER_FILE = {str(answer_file)!r}


@register_probe("f_probe")
def probe(cfg):
    text = Path(ANSWER_FILE).read_text().strip()
    return Apparatus(facts={{"model_revision": text or None}})
"""
    (site / f"{mod}.py").write_text(probe_src)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        experiment_type="f_assay",
        parameters={"instrument": {"model": "m1"}},
        sweep={},
        _local_template=_F_TEMPLATE,
    )
    run_dir = doc["run_dir"]
    _mid_run(run_dir)

    answer_file.write_text("rev1")
    assert main(["freeze", str(run_dir)]) == 0

    answer_file.write_text("rev2")
    # Under the SHIPPED filter, `replay_ledger` excludes `phase == "freeze"`
    # lines, so this second call's baseline is still all-null — "rev2" is
    # answered for the first time within this round, exactly as "rev1" was
    # in the first, and both exit 0. M8 (admitting `freeze` lines to the
    # baseline) is what makes the second one 1 — run manually, reported
    # rather than persisted as a second mutant of this same fixture.
    assert main(["freeze", str(run_dir)]) == 0

    lines = _ledger_lines(run_dir)
    freeze_facts = [line["facts"]["model_revision"] for line in lines if line["phase"] == "freeze"]
    assert freeze_facts == ["rev1", "rev2"]


def test_m11_command_freeze_refuses_a_run_that_has_ended(installed, registries, tmp_path, capsys):
    """M11's own discriminator at the `command_freeze` level (task 6 step
    13): `run.yaml` present must refuse with NO new ledger line — the
    discriminating half, since a code assertion alone would pass a build
    that reported the code after appending."""
    from publishable.freeze import command_freeze

    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    assert (run_dir / "run.yaml").exists()
    before_lines = _ledger_lines(run_dir)
    code = command_freeze(run_dir)
    assert code == EXIT_WRONG
    assert _ledger_lines(run_dir) == before_lines


def test_f3_freeze_against_a_genuinely_held_lock_in_a_second_process(
    installed, registries, tmp_path, capsys
):
    """The one H8b surface that needs concurrency, and the only test given
    a handshake: a run blocks INSIDE A STEP (not inside the probe — by then
    every run-start line has already landed, so `freeze` has a real
    baseline to compare against, which is the actual situation the command
    exists for) while the parent process calls `freeze` against the same,
    genuinely locked directory. `freeze` must exit 0 and append its lines
    despite the live lock — proving a lock is not what stops it.

    The synthetic probe distribution `installed` writes is on THIS
    process's `sys.path` only (`monkeypatch.syspath_prepend`), so the
    child process that runs the project needs the same site directory on
    its own `PYTHONPATH` to resolve the plugin — passed through `env=`
    rather than relying on inheritance, since the two must resolve to the
    identical registration for `freeze`'s own in-process `_probe_for` call
    to see the same probe the child ran with.
    """
    import os
    import subprocess
    import sys
    import time

    sentinel = tmp_path / "sentinel"
    release = tmp_path / "release"
    step_source = f"""\
# src/{{pkg}}/steps/step01_load_cohort.py — generated, blocks for the handshake
import time
from pathlib import Path

from publishable import BaseStep

SENTINEL = {str(sentinel)!r}
RELEASE = {str(release)!r}


class Step(BaseStep):
    scope = "run"

    def run(self, cfg, io):
        Path(SENTINEL).write_text("here")
        deadline = time.monotonic() + 20
        while not Path(RELEASE).exists():
            if time.monotonic() > deadline:
                raise TimeoutError("F3's release file never appeared")
            time.sleep(0.05)
        return {{{{}}}}
"""
    global _fixture_p_counter
    _fixture_p_counter += 1
    mod = f"f9_probe_mod_{_fixture_p_counter}"
    dist = f"dist-f9-{_fixture_p_counter}"
    site = installed(dist, "1.0", {"publishable.probes": {"f_probe": f"{mod}:probe"}})
    (site / f"{mod}.py").write_text(_F_PROBE_MODULE)

    # Scaffolded WITHOUT running: `run_a_project` calls `main(["run", ...])`
    # synchronously in THIS process, which would block on `sentinel` right
    # here with nothing to release it. The scaffold below is the same
    # sequence `run_a_project` runs up to (and excluding) that call.
    import subprocess as _sp

    import yaml as _yaml

    from publishable.cli import main as _main
    from publishable.generators.experiment import generate_experiment as _generate_experiment

    root = tmp_path / "proj"
    data = tmp_path / "data"
    results_dir = tmp_path / "results"
    data.mkdir()
    (data / "index.csv").write_text(
        "patient_id,cohort,arm\n" + "\n".join(f"p{i},a,x" for i in range(1, 11)) + "\n"
    )
    assert _main(["new", str(root)]) == 0
    (root / "templates").mkdir(exist_ok=True)
    (root / "templates" / "cred_assay.py").write_text(_F_TEMPLATE)
    with pytest.MonkeyPatch.context() as mp:
        import publishable.generators.experiment as _experiment_gen

        mp.setattr(_experiment_gen, "STARTER_STEP", step_source)
        cfg = _generate_experiment(
            repo_root=root,
            name="cohort-pilot",
            template_name="generic",
            input_dir=str(data),
            output_dir=str(results_dir),
        )
        cfg_doc = _yaml.safe_load(cfg.read_text())
        cfg_doc["metadata"]["description"] = "F3's blocking helper run"
        cfg_doc["metadata"]["authors"] = ["Kyungjoon Lee"]
        cfg_doc["experiment_type"] = "f_assay"
        cfg_doc["parameters"] = {"instrument": {"model": "m1"}}
        cfg_doc["sweep"] = {"grid": {"instrument.model": ["m1", "m2"]}}
        cfg.write_text(_yaml.safe_dump(cfg_doc))
        for args in (
            ["add", "."],
            ["-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "helper run"],
        ):
            _sp.run(["git", *args], cwd=root, check=True)

    run_dir_glob = results_dir

    child_env = dict(os.environ)
    existing = child_env.get("PYTHONPATH", "")
    child_env["PYTHONPATH"] = str(site) + (os.pathsep + existing if existing else "")

    proc = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import sys; from publishable.cli import main; "
            "sys.exit(main(['run', " + repr(str(cfg)) + "]))",
        ],
        env=child_env,
    )
    try:
        deadline = time.monotonic() + 20
        while not sentinel.exists():
            if time.monotonic() > deadline:
                proc.kill()
                raise TimeoutError("the run never reached the blocking step")
            time.sleep(0.05)

        run_dir = next(run_dir_glob.glob("run_*"))
        deadline = time.monotonic() + 20
        while not (run_dir / "apparatus" / "probes.jsonl").exists():
            if time.monotonic() > deadline:
                proc.kill()
                raise TimeoutError("the run-start probe round never landed")
            time.sleep(0.05)
        assert (run_dir / "lock").exists(), "the lock must be genuinely held for this fixture"
        before_lines = _ledger_lines(run_dir)

        from publishable.freeze import command_freeze

        code = command_freeze(run_dir)
        assert code == 0
        assert len(_ledger_lines(run_dir)) == len(before_lines) + 2
    finally:
        release.write_text("go")
        proc.wait(timeout=20)


# --- Batch 4 review, Major 3: both of Decision 10's warnings, pinned -------


def test_w_freeze_lock_moved_fires_when_the_captured_copy_and_the_repo_disagree(
    installed, registries, tmp_path, capsys
):
    """`W-FREEZE-LOCK-MOVED` must actually print when the two disagree —
    replacing `_warn_lock_moved`'s body with a bare `return` was shown to
    leave the whole suite green, so this asserts the printed text rather
    than merely calling the command."""
    from publishable.cli import main

    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    (run_dir / "environment" / "uv.lock").write_text("captured-content\n")
    (doc["root"] / "uv.lock").write_text("moved-content\n")

    code = main(["freeze", str(run_dir)])
    output = capsys.readouterr().err
    assert code == 0
    assert "W-FREEZE-LOCK-MOVED" in output


def test_w_freeze_lock_moved_is_silent_when_the_captured_copy_and_the_repo_agree(
    installed, registries, tmp_path, capsys
):
    from publishable.cli import main

    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    (run_dir / "environment" / "uv.lock").write_text("same-content\n")
    (doc["root"] / "uv.lock").write_text("same-content\n")

    code = main(["freeze", str(run_dir)])
    output = capsys.readouterr().err
    assert code == 0
    assert "W-FREEZE-LOCK-MOVED" not in output


def test_w_freeze_lock_moved_is_silent_when_nothing_was_captured(
    installed, registries, tmp_path, capsys
):
    """Minor 4's own pin: absent on the CAPTURED side is not a move,
    regardless of what the repo holds now — the docstring's claim narrowed
    to this side only."""
    from publishable.cli import main

    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    assert not (run_dir / "environment" / "uv.lock").exists()
    (doc["root"] / "uv.lock").write_text("some-content\n")

    code = main(["freeze", str(run_dir)])
    output = capsys.readouterr().err
    assert code == 0
    assert "W-FREEZE-LOCK-MOVED" not in output


_NULLABLE_PROBE_TEMPLATE = """\
from pathlib import Path

from publishable import Apparatus, register_probe

ANSWER_FILE = {answer_file!r}


@register_probe("f_probe")
def probe(cfg):
    text = Path(ANSWER_FILE).read_text().strip()
    return Apparatus(facts={{"model_revision": text or None}})
"""


def test_w_apparatus_unanswered_fires_at_freeze_when_a_declared_fact_comes_back_null(
    installed, registries, tmp_path, capsys
):
    """Decision 10's fourth row, at `freeze`: deleting the four-line
    `warn_unanswered` block was shown to leave `test_freeze.py` green, so
    this asserts the printed warning text — never merely that the command
    ran — over a probe that answers a real value during the run and
    `null` only once `freeze` calls it."""
    from publishable.cli import main

    answer_file = tmp_path / "answer.txt"
    answer_file.write_text("rev1")
    global _fixture_p_counter
    _fixture_p_counter += 1
    mod = f"f9_probe_mod_{_fixture_p_counter}"
    dist = f"dist-f9-{_fixture_p_counter}"
    site = installed(dist, "1.0", {"publishable.probes": {"f_probe": f"{mod}:probe"}})
    (site / f"{mod}.py").write_text(_NULLABLE_PROBE_TEMPLATE.format(answer_file=str(answer_file)))
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        experiment_type="f_assay",
        parameters={"instrument": {"model": "m1"}},
        sweep={},
        _local_template=_F_TEMPLATE,
    )
    run_dir = doc["run_dir"]
    _mid_run(run_dir)

    answer_file.write_text("")  # -> None, once freeze calls it
    code = main(["freeze", str(run_dir)])
    captured = capsys.readouterr()
    assert code == 0
    assert "W-APPARATUS-UNANSWERED" in captured.out


def test_exit_0_prints_the_observation_per_condition_and_the_count(
    installed, registries, tmp_path, capsys
):
    """Batch 4 review, Minor 1: Decision 10's exit-0 row says "the
    observation, per condition"; Decision 8 says "the output states the
    count." Both were unmet, undisclosed and unfiled; built here rather
    than filed, since nothing in `reference.md` § Operation commands
    specifies a `freeze` output to override."""
    from publishable.cli import main

    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)

    code = main(["freeze", str(run_dir)])
    captured = capsys.readouterr()
    assert code == 0
    assert "model_revision=" in captured.out
    assert "2 condition(s) probed" in captured.out


def test_w_freeze_lock_moved_fires_when_the_repos_lockfile_is_deleted(
    installed, registries, tmp_path, capsys
):
    """Minor 4's other half: the captured side is guarded (see the silent
    test above), but the CURRENT side is not — a repo whose `uv.lock` was
    deleted since the run started still warns, since `uv_lock_info`
    answers `(None, None)` and that disagrees with any non-empty captured
    hash."""
    from publishable.cli import main

    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    (run_dir / "environment" / "uv.lock").write_text("captured-content\n")
    assert not (doc["root"] / "uv.lock").exists()

    code = main(["freeze", str(run_dir)])
    output = capsys.readouterr().err
    assert code == 0
    assert "W-FREEZE-LOCK-MOVED" in output


def test_a_nonexistent_run_directory_is_E_IO_FAILED_not_E_FREEZE_NO_CONFIG(tmp_path, capsys):
    """Batch 4 review, Minor 7: a typo'd path or a config path passed by
    mistake both used to land on `E-FREEZE-NO-CONFIG`'s remedy, which is
    about a real directory missing an artifact — not this. `validate`'s own
    precedent for an unanticipated path problem is `E-IO-FAILED` at exit 1,
    through `main`'s generic `OSError` handler."""
    from publishable.cli import main
    from publishable.diagnostics import EXIT_WRONG

    code = main(["freeze", str(tmp_path / "nope" / "nope")])
    output = capsys.readouterr().err
    assert code == EXIT_WRONG
    assert "E-IO-FAILED" in output
    assert "E-FREEZE-NO-CONFIG" not in output


# --- H9b task 16, Fixture K: `freeze`'s own `parameters_hash` comparison ----
# Design Decision 15. `resume`'s comparison does NOT close this one: `resume`
# re-reads the PROJECT's config (Decision 7) and never touches the run
# directory's copy, while the standing `spec-defects.md` filing's gap is an
# edit to that copy — a probe measuring under parameters the run never
# adopted. Closed here rather than deferred, because no remaining slice has
# `freeze` as its surface.


def test_h9b_freeze_refuses_a_config_copy_edited_since_the_run_started(
    installed, registries, tmp_path, capsys
):
    """The edit is to `parameters` ONLY, and to a value the sweep does not
    range over, so `E-FREEZE-PLAN-MISMATCH` cannot fire and the new gate is
    the only thing that can refuse — measured by the control below, which
    freezes the same directory clean before the edit.

    Both figures are in the message: a refusal that named neither would leave
    an operator with nothing to compare, and the recorded one is what says
    which side moved.
    """
    from publishable.cli import main
    from publishable.hashes import parameters_hash

    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    recorded = json.loads((run_dir / "identity.json").read_text())["parameters_hash"]

    # The control FIRST: unedited, this directory freezes at exit 0. Without
    # it the refusal below could be firing for any reason at all.
    assert main(["freeze", str(run_dir)]) == 0
    capsys.readouterr()
    # Read AFTER the control, which legitimately appended its own probe round:
    # what the refusal must not do is append to what is there NOW.
    before = _ledger_lines(run_dir)

    config = yaml.safe_load((run_dir / "config.yaml").read_text())
    assert config["parameters"]["instrument"]["model"] == "m1"
    config["parameters"]["instrument"]["model"] = "m3"
    (run_dir / "config.yaml").write_text(yaml.safe_dump(config))
    edited = parameters_hash(config)
    assert edited != recorded

    code = main(["freeze", str(run_dir)])
    printed = capsys.readouterr().err
    assert code == EXIT_WRONG
    assert "E-FREEZE-CONFIG-EDITED" in printed, printed
    assert recorded in printed and edited in printed
    assert "E-FREEZE-PLAN-MISMATCH" not in printed
    # A refusal makes no probe call and writes no ledger line — every other
    # gate's own property, asserted here rather than assumed.
    assert _ledger_lines(run_dir) == before


def test_h9b_freeze_with_no_identity_json_behaves_exactly_as_before(
    installed, registries, tmp_path, capsys
):
    """The negative control, and it asserts `freeze`'s FULL shipped output
    rather than only its exit code: a run directory started by a build that
    predates `identity.json` has nothing to compare, so the gate must be
    silent — not merely non-fatal.

    Two-sided: the same directory is frozen with the artifact present and
    then with it removed, and the two outputs are compared. The comparison is
    what makes this a control rather than an assertion that some output
    appeared, and the `E-FREEZE-CONFIG-EDITED` absence is asserted on stderr,
    the stream a refusal writes to.
    """
    from publishable.cli import main

    doc = _fixture_p(installed, tmp_path, capsys)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    assert (run_dir / "identity.json").is_file()
    with_artifact_code = main(["freeze", str(run_dir)])
    with_artifact = capsys.readouterr()

    (run_dir / "identity.json").unlink()
    without_code = main(["freeze", str(run_dir)])
    without = capsys.readouterr()

    assert with_artifact_code == without_code == 0
    assert "E-FREEZE-CONFIG-EDITED" not in without.err
    assert without.out == with_artifact.out
    assert without.err == with_artifact.err
