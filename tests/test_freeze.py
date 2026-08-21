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


def test_f2_freeze_sees_a_moved_fact(installed, registries, tmp_path, capsys):
    from publishable.diagnostics import EXIT_WRONG
    from publishable.freeze import command_freeze

    answer_file = tmp_path / "answer.txt"
    answer_file.write_text("rev1")
    doc = _fixture_p_moving(installed, tmp_path, capsys, answer_file)
    run_dir = doc["run_dir"]
    _mid_run(run_dir)
    before_lines = _ledger_lines(run_dir)

    answer_file.write_text("rev2")
    code = command_freeze(run_dir)
    assert code == EXIT_WRONG

    after_lines = _ledger_lines(run_dir)
    # The ledger holds the moving observation — appended before the gate
    # fires, per H7d Part A's ruling, so the stop is legible from the
    # artifacts.
    assert len(after_lines) == len(before_lines) + 1
    moved = after_lines[-1]
    assert moved["phase"] == "freeze"
    assert moved["facts"]["model_revision"] == "rev2"


def test_f5_arm_one_a_probe_raising_with_a_credential_is_redacted_end_to_end(
    installed, registries, tmp_path, capsys
):
    """Fixture F5's first arm, completed end to end through `command_freeze`
    now that the probe round exists: the credential's absence from stderr
    AND `E-APPARATUS-RAISED`'s presence at exit `EXIT_EXTERNAL` — the pair,
    since asserting only the absence passes identically if nothing ran."""
    from publishable.diagnostics import EXIT_EXTERNAL
    from publishable.freeze import command_freeze

    # The probe must succeed during the run (so the run itself completes)
    # and only raise once `freeze` calls it — a `TRIGGER_FILE` whose
    # presence flips the behaviour, checked at call time on the SAME module
    # object rather than by rewriting the file on disk (which `load_
    # entry_point`'s ordinary `importlib` caching would not re-import).
    trigger_file = tmp_path / "trigger"
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
    if Path(TRIGGER_FILE).exists():
        token = os.environ["F_CRED_TOKEN"]
        raise RuntimeError(f"could not reach the instrument, token was {{token}}")
    return Apparatus(facts={{"model_revision": cfg.parameters.instrument.model}})
"""
    (site / f"{mod}.py").write_text(site_and_probe)
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
    before_lines = _ledger_lines(run_dir)
    trigger_file.write_text("go")

    code = command_freeze(run_dir)
    output = capsys.readouterr().err
    assert code == EXIT_EXTERNAL
    assert "shh" not in output
    assert "E-APPARATUS-RAISED" in output
    # No line for the raising probe call — `observe_once` raises before
    # `append_observation` ever runs for that condition.
    assert _ledger_lines(run_dir) == before_lines


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
