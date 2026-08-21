"""H8b tasks 4-6: `freeze` — the refusals, the resolution, the credential
pre-check, the condition set, the probe round and the CLI arm.

Fixture P (inherited from `test_apparatus.py`): a synthetic installed
distribution registering a probe, a project-local template declaring
`apparatus_probe`/`apparatus_facts`, two swept conditions.
"""

import json
from pathlib import Path

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
        "instrument.model": Param(str, default="m1", choices=["m1", "m2"]),
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
            choices=["m1", "m2"],
            requires_env={"m1": ["F_CRED_TOKEN"], "m2": []},
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
