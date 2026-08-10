import json
import re
import subprocess
from collections import namedtuple
from pathlib import Path
from typing import Any

import pytest
import yaml

from publishable import BaseStep
from publishable.cli import _apply_execution_order, main
from publishable.diagnostics import EXIT_INVOCATION, EXIT_OK, EXIT_WRONG
from publishable.errors import ContractError
from publishable.generators.experiment import generate_experiment
from publishable.generators.step import generate_step
from publishable.replication import LABEL_JOIN
from publishable.scope import Execution

Ran = namedtuple("Ran", ["condition_index", "repeat_label"])


def run_a_project(
    tmp_path: Path,
    *,
    replication: dict[str, Any] | None = None,
    capsys: pytest.CaptureFixture[str] | None = None,
    extra_steps: list[str] | None = None,
    aggregate_returns: str | None = None,
    units: int = 10,
    unit_attributes: list[str] | None = None,
    **overrides: Any,
) -> dict[str, Any]:
    """Scaffold, configure, commit, and `run` a project end to end.

    The one end-to-end driver `test_cli.py` has: every test in this module that
    needs a real run through `main(["run", ...])` builds on this rather than
    inventing its own scaffold-and-commit dance. `overrides` lands as top-level
    keys merged onto the generated `config.yaml` (`sweep`, for instance);
    `replication` is named explicitly since every caller in this file sets it.

    Returns the run directory, the resolved paths, and `results`: one `Ran`
    entry per line of `executions.jsonl`, in the order execution actually
    produced them — the ground truth for "did the plan run in the order
    `sweep.yaml` recorded," read from the ledger rather than re-derived from
    the plan the way the thing under test builds `execution_order`.

    `capsys` is optional and additive: pass the fixture when a caller needs to
    assert on a diagnostic `run` prints (`command_run` prints `validate`'s
    findings — warnings included, such as `W-REPL-DETERMINISTIC` — to stdout,
    the same surface `test_an_unwritable_output_dir_is_a_diagnostic_not_a_traceback`
    reads for `E-IO-FAILED`). When given, the captured text lands in the
    returned dict under `"stdout"`/`"stderr"`; existing callers that don't pass
    it are unaffected.

    `extra_steps` names additional generated steps, appended after the scaffold's
    one. Every generated step is `repeat`-scoped, so this is how a caller gets a
    pipeline with more than one repeat-scope step — the shape that distinguishes
    step-major from pair-major execution, and which the single-step scaffold
    cannot express at all.

    `aggregate_returns` names a derived metric to produce end to end: when set,
    the scaffolded step records a `pred` column (one float per unit, `0.0`..
    `n-1`) and the template's `aggregate` returns `{aggregate_returns: mean(pred)}`
    over the collapsed unit table — a mean, not a sum, since it needs `len(units)`
    rather than assuming the caller already has a denominator. Patched in via
    `pytest.MonkeyPatch.context()`, self-contained so no caller needs its own
    `monkeypatch` fixture, and undone before this function returns.

    `unit_attributes` names columns to declare under `data.units.attributes`.
    The roster file always carries a `cohort` column (alternating `a`/`b`) and
    an `arm` column (`x`/`y`, in pairs so its membership genuinely differs from
    `cohort`'s rather than being the same split under a second name — two
    perfectly correlated attributes would make a `report_by: [cohort, arm]`
    test pass on byte-identical blocks), so a caller wanting a `within` stratum
    passes `unit_attributes=["cohort"]` — `validate` refuses a `within` naming
    an attribute the config never declared (`E-STATS-CONTRAST-WITHIN`), and
    unit resolution refuses one the table doesn't have
    (`E-UNITS-ATTR-MISSING`), so both halves have to be present. Both columns
    are written unconditionally because an undeclared column is simply never
    read.
    """
    tmp_path.mkdir(parents=True, exist_ok=True)
    root = tmp_path / "proj"
    data = tmp_path / "data"
    results_dir = tmp_path / "results"
    data.mkdir()
    # 10 patients by default, not 2: a `fold` design (`{kind: fold, k: 5}`) needs
    # `k <= unit_count`, and every other caller in this module only ever checks
    # `results`/`sweep.yaml` shape, never the roster's exact size. `units` is a
    # caller-set override — a thin-pairing test wants a roster small enough that
    # `n_paired` trips `limits.min_reported_n` without inflating every other
    # caller's fixture to match.
    patients = "\n".join(
        f"p{i},{'ab'[i % 2]},{'xy'[(i // 2) % 2]}" for i in range(1, units + 1)
    )
    (data / "index.csv").write_text(f"patient_id,cohort,arm\n{patients}\n")
    assert main(["new", str(root)]) == EXIT_OK
    with pytest.MonkeyPatch.context() as mp:
        if aggregate_returns is not None:
            import publishable.generators.experiment as experiment_gen
            from publishable.templates.builtin.generic import GenericTemplate

            metric_name = aggregate_returns
            mp.setattr(experiment_gen, "STARTER_STEP", _AGGREGATE_STEP)
            mp.setattr(
                GenericTemplate,
                "aggregate",
                lambda self, units, cfg, _name=metric_name: {
                    _name: sum(units.pred) / len(units)
                },
            )
        cfg = generate_experiment(
            repo_root=root,
            name="cohort-pilot",
            template_name="generic",
            input_dir=str(data),
            output_dir=str(results_dir),
        )
        for step_name in extra_steps or []:
            generate_step(repo_root=root, experiment="cohort-pilot", step_name=step_name)
        doc = yaml.safe_load(cfg.read_text())
        doc["metadata"]["description"] = "an end-to-end helper run"
        doc["metadata"]["authors"] = ["Kyungjoon Lee"]
        if replication is not None:
            doc["replication"] = replication
        doc.update(overrides)
        if unit_attributes is not None:
            doc["data"]["units"]["attributes"] = list(unit_attributes)
        cfg.write_text(yaml.safe_dump(doc))
        for args in (
            ["add", "."],
            ["-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "helper run"],
        ):
            subprocess.run(["git", *args], cwd=root, check=True)

        assert main(["run", str(cfg)]) == EXIT_OK
        captured = capsys.readouterr() if capsys is not None else None
    run_dir = next(results_dir.glob("run_*"))
    lines = (run_dir / "executions.jsonl").read_text().splitlines()
    ledger = [json.loads(line) for line in lines]
    results = [Ran(e["condition"], e["repeat"]) for e in ledger]
    return {
        "root": root,
        "cfg": cfg,
        "results_dir": results_dir,
        "run_dir": run_dir,
        "results": results,
        "stdout": captured.out if captured is not None else None,
        "stderr": captured.err if captured is not None else None,
    }


def test_an_unknown_command_is_an_invocation_error(capsys):
    assert main(["frobnicate", "x"]) == EXIT_INVOCATION


def test_a_missing_argument_is_an_invocation_error():
    assert main(["run"]) == EXIT_INVOCATION


def test_run_on_a_path_with_no_repo_is_wrong_not_invalid(tmp_path: Path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("schema_version: '1.0'\n")
    assert main(["run", str(cfg)]) == EXIT_WRONG


def test_operation_commands_take_no_flags(capsys):
    assert main(["run", "cfg.yaml", "--allow-dirty"]) == EXIT_INVOCATION


def test_an_unwritable_output_dir_is_a_diagnostic_not_a_traceback(tmp_path: Path, capsys):
    """The ruled-on fix: `run`'s OSError surfaces as `E-IO-FAILED` at exit 1, never a
    bare traceback. `output_dir` existing as a *file* makes `Path.mkdir` raise
    `FileExistsError` (an `OSError` subclass) inside `allocate_run_dir` — the
    simplest way to provoke a real filesystem refusal without touching permissions,
    which don't behave uniformly across CI filesystems.
    """
    import subprocess

    import yaml

    from publishable.generators.experiment import generate_experiment

    root = tmp_path / "proj"
    data = tmp_path / "data"
    data.mkdir()
    (data / "index.csv").write_text("patient_id\np1\n")
    output_as_file = tmp_path / "results-is-a-file"
    output_as_file.write_text("not a directory\n")

    assert main(["new", str(root)]) == 0
    cfg = generate_experiment(
        repo_root=root,
        name="cohort-pilot",
        template_name="generic",
        input_dir=str(data),
        output_dir=str(output_as_file),
    )
    doc = yaml.safe_load(cfg.read_text())
    doc["metadata"]["description"] = "a diagnostic, not a traceback"
    doc["metadata"]["authors"] = ["Kyungjoon Lee"]
    cfg.write_text(yaml.safe_dump(doc))
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "experiment"],
        cwd=root,
        check=True,
    )

    assert main(["run", str(cfg)]) == EXIT_WRONG
    err = capsys.readouterr().err
    assert "E-IO-FAILED" in err


RANDOMIZED_ACROSS_CONDITIONS: dict[str, Any] = {
    "sweep": {
        "baseline": {"analysis.method": "pearson"},
        "grid": {"analysis.method": ["spearman"]},
    },
    "replication": {
        "repeats": [{"kind": "batch", "n": 2}, {"kind": "seed", "n": 3}],
        "order": "randomized",
    },
}
"""2 conditions × 2 batches × 3 seeds = 12 pairs — enough that `rng.shuffle` landing on the
identity permutation is vanishingly unlikely, and with 2 conditions the shuffle actually has
condition boundaries to cross. A single-condition, 2-seed fixture doesn't exercise either
risk: it can't interleave conditions, and a 2-element shuffle has a 50% chance of doing
nothing, which would let a broken reorder pass silently.
"""


def test_sweep_yaml_records_the_order_mode_and_seed(tmp_path: Path):
    doc = run_a_project(
        tmp_path,
        sweep=RANDOMIZED_ACROSS_CONDITIONS["sweep"],
        replication=RANDOMIZED_ACROSS_CONDITIONS["replication"],
    )
    sweep = yaml.safe_load((doc["run_dir"] / "sweep.yaml").read_text())
    assert sweep["order"] == "randomized"
    assert isinstance(sweep["order_seed"], int)
    assert len(sweep["execution_order"]) == len(sweep["labels"]) * len(sweep["conditions"])
    declared = [
        (c["index"], label) for c in sweep["conditions"] for label in sweep["labels"]
    ]
    recorded = [(e["condition"], e["repeat"]) for e in sweep["execution_order"]]
    assert recorded != declared, "the shuffle must actually move something"
    batches = [r.split(LABEL_JOIN)[0] for _, r in recorded]
    assert batches == sorted(batches), "batch01 pairs must all precede batch02 pairs"


def test_as_declared_executes_step_major(tmp_path: Path):
    """`as_declared` must leave `build_plan`'s layout alone — step-major within a
    condition (for each step, for each repeat), which is what S3a executed.

    `_apply_execution_order` regroups repeat executions pair-major, which is the
    right grain once an order has been *realized*; applied to the default path it
    silently reordered every design with ≥2 repeat-scope steps and ≥2 repeats.
    Two repeat-scope steps are the whole point of the fixture: with the scaffold's
    single step the two layouts are indistinguishable, which is why nothing caught
    this.
    """
    doc = run_a_project(
        tmp_path,
        replication={"repeats": [{"kind": "seed", "n": 2}]},
        extra_steps=["second_pass"],
    )
    repeat_runs = [
        (e["step"], e["repeat"])
        for e in (json.loads(line) for line in
                  (doc["run_dir"] / "executions.jsonl").read_text().splitlines())
        if e["scope"] == "repeat"
    ]
    steps = [step for step, _ in repeat_runs]
    assert len(set(steps)) == 2, "the fixture must have two repeat-scope steps"
    # Step-major: each step's repeats run consecutively, so the step name changes
    # exactly once. Pair-major would alternate, changing it on every row but one.
    changes = sum(1 for a, b in zip(steps, steps[1:], strict=False) if a != b)
    assert changes == 1, f"expected step-major, got {repeat_runs!r}"


def test_as_declared_records_no_order_seed(tmp_path: Path):
    doc = run_a_project(tmp_path, replication={"repeats": [{"kind": "seed", "n": 2}]})
    sweep = yaml.safe_load((doc["run_dir"] / "sweep.yaml").read_text())
    assert sweep["order"] == "as_declared"
    assert sweep.get("order_seed") is None


class _RepeatStep(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        return {}


def test_a_plan_pair_missing_from_execution_order_is_a_core_bug():
    """`_apply_execution_order`'s invariant: every repeat-scope execution `build_plan`
    produced must have a home among `execution_order`'s pairs. `command_run` builds
    both from the same `conditions`/`repeats`, so this should be unreachable there —
    pinned directly, the way `tests/test_runner.py` pins `E-RUN-CFG-MISSING` and
    `E-RUN-SEED-MISSING` by constructing a mismatch `execute_plan` never resolves
    itself.
    """
    plan = [
        Execution(_RepeatStep, "repeat_step", "repeat", 0, None, "seedA"),
        Execution(_RepeatStep, "repeat_step", "repeat", 0, None, "seedB"),
    ]
    with pytest.raises(ContractError) as excinfo:
        _apply_execution_order(plan, [(0, "seedA")])  # "seedB" has no home
    assert excinfo.value.code == "E-RUN-ORDER-MISMATCH"


def test_the_recorded_order_is_the_order_that_ran(tmp_path: Path):
    """The realized order is a fact about the run, not a rule to re-derive.

    Uses `RANDOMIZED_ACROSS_CONDITIONS` (2 conditions) rather than a single-condition
    fixture: with one condition there is no condition boundary for a batch to cross,
    so the plan-reordering this test exists to catch could be missing entirely and
    a single-condition run would still pass.
    """
    doc = run_a_project(
        tmp_path,
        sweep=RANDOMIZED_ACROSS_CONDITIONS["sweep"],
        replication=RANDOMIZED_ACROSS_CONDITIONS["replication"],
    )
    sweep = yaml.safe_load((doc["run_dir"] / "sweep.yaml").read_text())
    recorded = [(e["condition"], e["repeat"]) for e in sweep["execution_order"]]
    ran = [(r.condition_index, r.repeat_label) for r in doc["results"] if r.repeat_label]
    assert recorded == ran


# --- Task 9: the acceptance test — a nested batch × seed design, end to end -----


def test_a_nested_batch_seed_run_end_to_end(tmp_path, capsys):
    doc = run_a_project(
        tmp_path,
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
        replication={
            "repeats": [{"kind": "batch", "n": 3}, {"kind": "seed", "n": 2}],
            "order": "randomized",
        },
        capsys=capsys,
    )
    # The `generic` template's demo step never sets `nondeterministic = True`, so a
    # declared `batch` level is exactly the case `W-REPL-DETERMINISTIC` warns on —
    # pinned here so a change that silently dropped the warning on this path
    # wouldn't leave the whole suite green.
    assert "W-REPL-DETERMINISTIC" in doc["stdout"]
    run_dir = doc["run_dir"]
    repeat_dirs = sorted(p.name for p in (run_dir / "conditions").glob("*/*") if p.is_dir())
    # 2 conditions × 6 composed repeat labels each = 12 directories; the same 6
    # labels recur under both condition directories, so the set is 6 wide.
    assert len(repeat_dirs) == 2 * 3 * 2
    assert len(set(repeat_dirs)) == 3 * 2
    label_pattern = re.escape(LABEL_JOIN).join([r"batch0\d", r"seed\d+"])
    assert all(re.fullmatch(label_pattern, n) for n in set(repeat_dirs))
    sweep = yaml.safe_load((run_dir / "sweep.yaml").read_text())
    declared = [(c["index"], label) for c in sweep["conditions"] for label in sweep["labels"]]
    recorded = [(e["condition"], e["repeat"]) for e in sweep["execution_order"]]
    assert recorded != declared, "the shuffle must actually move something"
    batches = [e["repeat"].split(LABEL_JOIN)[0] for e in sweep["execution_order"]]
    assert batches == sorted(batches), "batches must run in declared order"
    assert len(sweep["execution_order"]) == 12


def test_the_recorded_order_seed_reproduces_the_order(tmp_path):
    a = run_a_project(
        tmp_path / "a",
        replication={
            "repeats": [{"kind": "batch", "n": 2}, {"kind": "seed", "n": 3}],
            "order": "randomized",
        },
    )
    b = run_a_project(
        tmp_path / "b",
        replication={
            "repeats": [{"kind": "batch", "n": 2}, {"kind": "seed", "n": 3}],
            "order": "randomized",
        },
    )
    sa = yaml.safe_load((a["run_dir"] / "sweep.yaml").read_text())
    sb = yaml.safe_load((b["run_dir"] / "sweep.yaml").read_text())
    assert sa["order_seed"] == sb["order_seed"]
    assert sa["execution_order"] == sb["execution_order"]


def test_a_single_level_seed_run_has_no_composed_labels(tmp_path, capsys):
    """The regression risk of introducing a level is that it appears where it should not."""
    doc = run_a_project(
        tmp_path, replication={"repeats": [{"kind": "seed", "n": 2}]}, capsys=capsys
    )
    # No `batch` level is declared at all, so `W-REPL-DETERMINISTIC` — which fires
    # only when a `batch` level lacks a `nondeterministic` step — has nothing to
    # warn about here; asserted so the two tests pin opposite sides of the rule
    # rather than both happening to pass for unrelated reasons.
    assert "W-REPL-DETERMINISTIC" not in doc["stdout"]
    dirs = [p.name for p in doc["run_dir"].rglob("*") if p.is_dir()]
    assert not any(f"{LABEL_JOIN}seed" in d for d in dirs)
    assert not any(d.startswith("batch") for d in dirs)


def test_a_five_fold_run_end_to_end(tmp_path, capsys):
    """The abort this slice fixes: before it, `_units_failed_anywhere` measured
    against the whole roster, so under `{k: 5}` every unit outside a fold's own
    partition counted as failed on that fold's execution and the run aborted at
    `max_failed_fraction` reporting `failed`, well short of every fold running."""
    doc = run_a_project(tmp_path, capsys=capsys,
                        replication={"repeats": [{"kind": "fold", "k": 5}]})
    sweep = yaml.safe_load((doc["run_dir"] / "sweep.yaml").read_text())
    assert [p["fold"] for p in sweep["partitions"]] == [
        "fold01", "fold02", "fold03", "fold04", "fold05"]
    tested = [k for p in sweep["partitions"] for k in p["test"]]
    assert len(tested) == len(set(tested))          # each unit tested exactly once
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    assert run["status"] == "completed"             # the abort this slice fixes

    # The discriminating assertion: dropping `fold_members=` from `execute_plan`
    # disables the roster-wide subtraction `_units_failed_anywhere` does AND the
    # per-fold narrowing at the same time, so `status: completed` alone holds
    # either way. Only the per-fold `n_units` tells the two apart — unwired, each
    # fold's own step sees the whole 10-unit roster, not its own 2-unit partition.
    per_repeat = run["results"]["conditions"][0]["per_repeat"]["step01_summarize_units"]
    n_units = [per_repeat[f"fold{i:02d}"]["n_units"] for i in range(1, 6)]
    assert n_units == [2, 2, 2, 2, 2]
    assert sum(n_units) == 10


# --- Task 2 (derived-metrics): the live defect this slice closes ---------------

_NUMPY_RETURN_STEP = '''\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
import numpy as np

from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        return {{"score": np.float64(1.5)}}    # forces a NumPy scalar into run.yaml
'''


def test_a_numpy_scalar_return_produces_a_run_yaml_that_serializes(tmp_path, monkeypatch):
    """The ruled-on fix: before `coerce_scalars` was wired into a step's return, a
    `numpy.float64` reached `yaml.safe_dump` while writing `run.yaml` and raised
    `RepresenterError` — a bare traceback, not a diagnostic. Confirmed to fail with
    that traceback before this task's fix landed."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _NUMPY_RETURN_STEP)
    doc = run_a_project(tmp_path)
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    assert run["status"] == "completed"
    per_repeat = run["results"]["conditions"][0]["per_repeat"]["step01_summarize_units"]
    score = next(iter(per_repeat.values()))["score"]
    assert type(score) is float


# --- Task 6 (derived-metrics): a template's `aggregate` reaches the record -----

_AGGREGATE_STEP = '''\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        units = list(io.units)
        for i, unit in enumerate(units):
            io.record(unit.key, {{"pred": float(i)}})
        return {{"n_units": len(units)}}
'''


def test_a_derived_metric_reaches_run_yaml_with_a_resampled_interval(tmp_path, monkeypatch):
    """The integration this task closes: a template's `aggregate` actually runs
    once per recording step, over that step's collapsed unit table, and its
    return reaches `run.yaml` as `basis: units` with a resampled `ci95` — not
    a scalar `aggregate` computed and core silently discarded."""
    import publishable.generators.experiment as experiment_gen
    from publishable.templates.builtin.generic import GenericTemplate

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _AGGREGATE_STEP)
    monkeypatch.setattr(
        GenericTemplate, "aggregate", lambda self, units, cfg: {"total": sum(units.pred)}
    )
    doc = run_a_project(tmp_path)
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    assert run["status"] == "completed"
    metric = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]["total"]
    assert metric["basis"] == "units"
    assert metric["method"] == "percentile_over_units"
    assert metric["ci95"] is not None
    low, high = metric["ci95"]
    assert low < metric["value"] < high
    assert metric["cohens_d"] is None


def test_a_project_without_aggregate_records_only_the_recorded_column(tmp_path, monkeypatch):
    """The regression guard: a run whose template never overrides `aggregate`
    (the base's `{}`) must record only the recorded column, exactly as before
    this task — no `total`, no empty placeholder, nothing new in `aggregated`."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _AGGREGATE_STEP)
    doc = run_a_project(tmp_path)
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    aggregated = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]
    assert "total" not in aggregated
    assert set(aggregated) == {"pred"}


# --- Task 9 (derived-metrics): acceptance — a derived metric reaches `run.yaml`
# from `main(["run", ...])`, via `run_a_project`'s new `aggregate_returns` --------


def _first_metric(run: dict[str, Any], name: str) -> dict[str, Any] | None:
    """The metric named `name`, wherever in `results.conditions[*].aggregated`
    it landed — a small local helper, since every caller here already knows
    which step it expects but the acceptance tests don't need to name it."""
    for condition in run["results"]["conditions"]:
        for step_aggregated in condition["aggregated"].values():
            if name in step_aggregated:
                metric = step_aggregated[name]
                assert isinstance(metric, dict)
                return metric
    return None


def test_a_derived_metric_end_to_end(tmp_path, capsys):
    doc = run_a_project(tmp_path, capsys=capsys, aggregate_returns="mean_pred")
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    metric = _first_metric(run, "mean_pred")
    assert metric["basis"] == "units"
    assert metric["method"] == "percentile_over_units"
    assert metric["ci95"] is not None
    assert metric["cohens_d"] is None
    assert metric["correction"] is None  # S4b's job; disclosed, not silently corrected


def test_the_same_digest_reproduces_the_derived_interval(tmp_path, capsys):
    a = run_a_project(tmp_path / "a", capsys=capsys, aggregate_returns="mean_pred")
    b = run_a_project(tmp_path / "b", capsys=capsys, aggregate_returns="mean_pred")
    ra = yaml.safe_load((a["run_dir"] / "run.yaml").read_text())
    rb = yaml.safe_load((b["run_dir"] / "run.yaml").read_text())
    assert _first_metric(ra, "mean_pred")["ci95"] == _first_metric(rb, "mean_pred")["ci95"]


def test_a_project_without_aggregate_reports_no_derived_metric(tmp_path, capsys):
    doc = run_a_project(tmp_path, capsys=capsys)
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    assert _first_metric(run, "mean_pred") is None


def test_a_failing_aggregate_does_not_cost_the_run_its_record(tmp_path, monkeypatch, capsys):
    """The Critical this task's review found: `aggregate` is user code in
    exactly the sense a step's `run` is, but ran uncontained — a raise other
    than `PublishableError`/`OSError` would have crashed before `run.yaml` was
    ever written, discarding every completed execution over one metric core
    couldn't compute. `run` must still complete, still write `run.yaml`, and
    still carry the recorded column's own summary; the failure is disclosed
    on stdout rather than swallowed or allowed to crash."""
    import publishable.generators.experiment as experiment_gen
    from publishable.templates.builtin.generic import GenericTemplate

    def _raises(self, units, cfg):
        raise ZeroDivisionError("a degenerate ratio, not a resample draw")

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _AGGREGATE_STEP)
    monkeypatch.setattr(GenericTemplate, "aggregate", _raises)
    doc = run_a_project(tmp_path, capsys=capsys)
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    # A run that did happen: every execution completed, so `status` is not
    # downgraded by a metric that could not be computed — that is a fact
    # about `aggregate`, not about whether the pipeline ran.
    assert run["status"] == "completed"
    aggregated = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]
    assert "total" not in aggregated
    assert set(aggregated) == {"pred"}
    assert "W-STATS-AGGREGATE-FAILED" in doc["stdout"]
    assert "ZeroDivisionError" in doc["stdout"]


def test_a_colliding_derived_key_does_not_cost_the_run_its_record(tmp_path, monkeypatch, capsys):
    """The same Critical through its second door. `summarize_step` refuses a
    derived key that shadows a recorded column (`E-STEP-KEY-COLLISION`), and
    that call sat outside the containment above — so a template returning
    `pred` against a step recording `pred` exited 1 with no `run.yaml`,
    discarding every completed execution over one badly chosen name, while
    the sibling case (a structural return) merely warned. The refusal itself
    stands; what it costs is the derived metric, not the run's record."""
    import publishable.generators.experiment as experiment_gen
    from publishable.templates.builtin.generic import GenericTemplate

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _AGGREGATE_STEP)
    monkeypatch.setattr(GenericTemplate, "aggregate", lambda self, units, cfg: {"pred": 1.0})
    doc = run_a_project(tmp_path, capsys=capsys)
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    assert run["status"] == "completed"
    aggregated = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]
    # The recorded column's own summary survives, and is the recorded column's
    # mean — not the derived value that tried to shadow it.
    assert set(aggregated) == {"pred"}
    assert aggregated["pred"]["value"] == sum(float(i) for i in range(10)) / 10
    assert "W-STATS-AGGREGATE-FAILED" in doc["stdout"]
    assert "E-STEP-KEY-COLLISION" in doc["stdout"]


def test_a_shrunken_resample_is_warned_about(tmp_path, monkeypatch, capsys):
    """An interval built from 100 of 2000 draws must not read like a clean
    one. `resample_draws` records it; `W-STATS-RESAMPLE-THIN` says it out
    loud, because a reader who never opens `run.yaml` has no other signal.
    Distinct from `W-STATS-AGGREGATE-FAILED`: `aggregate` did not fail — it
    produced numbers, on fewer draws than were asked for."""
    import publishable.generators.experiment as experiment_gen
    from publishable.templates.builtin.generic import GenericTemplate

    calls = {"n": 0}

    def _survives_a_hundred_draws(self, units, cfg):
        calls["n"] += 1
        # Call 1 is the real, unresampled one whose return is the reported
        # value; the next 100 are draws that survive, and every draw after
        # that is degenerate.
        if calls["n"] > 101:
            return {"total": None}
        return {"total": sum(units.pred)}

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _AGGREGATE_STEP)
    monkeypatch.setattr(GenericTemplate, "aggregate", _survives_a_hundred_draws)
    doc = run_a_project(tmp_path, capsys=capsys)
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    metric = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]["total"]
    assert metric["resample_draws"] == 100
    assert metric["ci95"] is not None  # 100 is above the honest floor of 80
    assert "W-STATS-RESAMPLE-THIN" in doc["stdout"]
    assert "100 of 2000 resample draws" in doc["stdout"]


def test_too_few_surviving_draws_report_no_interval_at_all(tmp_path, monkeypatch, capsys):
    """Below the floor there is no honest percentile to read: at two
    survivors the two ranks coincide and `run.yaml` carried a zero-width 95 %
    interval labelled `percentile_over_units`. Now the point value stands
    alone, and the warning says why."""
    import publishable.generators.experiment as experiment_gen
    from publishable.templates.builtin.generic import GenericTemplate

    calls = {"n": 0}

    def _survives_two_draws(self, units, cfg):
        calls["n"] += 1
        return {"total": sum(units.pred) if calls["n"] <= 3 else None}

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _AGGREGATE_STEP)
    monkeypatch.setattr(GenericTemplate, "aggregate", _survives_two_draws)
    doc = run_a_project(tmp_path, capsys=capsys)
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    metric = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]["total"]
    assert metric["resample_draws"] == 2
    assert metric["ci95"] is None
    assert metric["method"] is None
    assert "W-STATS-RESAMPLE-THIN" in doc["stdout"]
    assert "so none is reported" in doc["stdout"]


def test_a_raising_resample_draw_does_not_crash_the_run(tmp_path, monkeypatch):
    """The nan-versus-raise asymmetry the review named, at the integration
    level: the single unresampled call to `aggregate` must succeed (so the
    point value is real) while a resampled draw's call to the same
    `aggregate` can legitimately raise on a degenerate composition — the same
    situation `pearsonr` returning `nan` covers for a library that doesn't
    raise. The run must still complete with a real `ci95` or an honest
    `None`, never a traceback."""
    import publishable.generators.experiment as experiment_gen
    from publishable.templates.builtin.generic import GenericTemplate

    def _sum_or_raise(self, units, cfg):
        values = units.pred
        if len(set(values)) < 2:  # a resample draw that happened to lack spread
            raise ZeroDivisionError("degenerate draw")
        return {"total": sum(values)}

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _AGGREGATE_STEP)
    monkeypatch.setattr(GenericTemplate, "aggregate", _sum_or_raise)
    doc = run_a_project(tmp_path)
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    assert run["status"] == "completed"
    metric = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]["total"]
    assert metric["value"] == sum(float(i) for i in range(10))
    # Either a real interval survived enough draws, or none did — both are
    # honest; a traceback is the only wrong answer, and this test would have
    # raised one before the resample draws were contained.
    assert metric["ci95"] is None or len(metric["ci95"]) == 2


def test_a_total_resample_failure_is_disclosed_not_silent(tmp_path, capsys, monkeypatch):
    """The second review round's finding: `aggregate` that succeeds once (on
    the real, all-distinct table) but raises on every single resampled draw
    (because a bootstrap draw duplicates units, and this `aggregate`
    deliberately assumes distinct ones — exactly the template the review
    warned the unit-identity fix makes more likely) must not read identically
    to a metric nobody tried to resample at all. `resample_draws: 0` and a
    `W-STATS-AGGREGATE-FAILED` warning distinguish it; `status` stays
    `completed` regardless, since every execution genuinely did complete."""
    import publishable.generators.experiment as experiment_gen
    from publishable.templates.builtin.generic import GenericTemplate

    def _sum_if_distinct(self, units, cfg):
        values = units.pred
        if len(set(values)) != len(values):  # a resampled draw always duplicates
            raise ZeroDivisionError("this aggregate assumes distinct units")
        return {"total": sum(values)}

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _AGGREGATE_STEP)
    monkeypatch.setattr(GenericTemplate, "aggregate", _sum_if_distinct)
    doc = run_a_project(tmp_path, capsys=capsys)
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    assert run["status"] == "completed"
    metric = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]["total"]
    assert metric["value"] == sum(float(i) for i in range(10))  # the one real call succeeded
    if metric["resample_draws"] == 0:
        assert metric["ci95"] is None
        assert "W-STATS-AGGREGATE-FAILED" in doc["stdout"]
        assert "every resample draw failed" in doc["stdout"]
    else:
        # With 2000 draws over a 10-unit roster, an exact all-distinct
        # permutation surviving once or twice is possible but rare; if it
        # happened here, the disclosure path wasn't exercised and the
        # unit-level tests (`test_a_raising_compute_is_treated_as_degenerate_
        # not_propagated`, `test_total_resample_failure_is_distinguishable_
        # from_no_resample_supplied`) are what pin the behaviour deterministically.
        assert metric["resample_draws"] is not None


_METHOD_VARYING_STEP = '''\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        units = list(io.units)
        # A per-unit value that differs both by condition (`shift`, keyed off
        # the swept `analysis.method`, so `of` and `against` genuinely diverge
        # rather than recording the same numbers under two labels) and
        # *per-unit differently between the two conditions* (the alternating
        # `extra`, whose parity flips with `shift`) — the per-unit differences
        # must themselves vary, not just the two conditions' means, or the
        # paired interval is zero-width and `cohens_dz` returns `None`
        # regardless of which condition is which. A per-unit offset that's
        # merely constant-but-nonzero (`+ 0.5` on every unit, in both
        # conditions) cancels in the difference and hits the same trap: S4b
        # task 5's plan did, and its fix is in
        # `docs/superpowers/sdd/2026-08-10-contrasts/progress.md`, Task 5.
        #
        # The shift is per *method* — a `1 if spearman else 0` flag, which is
        # what stood here, makes every arm past the first byte-identical to
        # the baseline under a two-arm grid: all-zero per-unit differences, a
        # zero-width interval, and infinite evidence, which ranks that arm
        # first in the correction family and makes a corrected-interval
        # assertion compare 0.0 against 0.0. Every non-baseline shift is odd,
        # so the alternating `extra` flips parity against the baseline in each
        # arm; a shift whose parity matched the baseline's would cancel the
        # +0.5 and land back on a point mass by the other route.
        shift = {{"pearson": 0, "spearman": 1, "kendall": 3}}.get(
            cfg.parameters.analysis.method, 0
        )
        for i, unit in enumerate(units):
            extra = 0.5 if (i + shift) % 2 == 1 else 0.0
            io.record(unit.key, {{"pred": float(i) + float(shift) + extra}})
        return {{"n_units": len(units)}}
'''


def _first_contrast(run: dict[str, Any], label: str) -> dict[str, Any] | None:
    """The first metric entry in the condition labeled `label`'s `vs_baseline`
    block, wherever it landed — mirrors `_first_metric`'s shape on the
    contrast side, since a caller here already knows which condition it
    expects but not which step or metric name carries it."""
    for condition in run["results"]["conditions"]:
        if condition.get("label") != label:
            continue
        for step_block in condition.get("vs_baseline", {}).values():
            for metric in step_block.values():
                assert isinstance(metric, dict)
                return metric
    return None


def test_a_baseline_sweep_reports_a_delta(tmp_path, capsys, monkeypatch):
    """`vs_baseline` is where `resolve_contrasts`'s auto-generated,
    condition-against-baseline comparisons land. The scaffold's own step
    records only a bool (`{"present": True}`, filtered by `_is_numeric`), so
    this uses `_METHOD_VARYING_STEP` — a per-unit value that genuinely
    differs by condition and has real within-condition variance — to get a
    real numeric column to difference, rather than `_AGGREGATE_STEP`'s
    `float(i)` (identical under both conditions, so `delta` and `cohens_d`
    would pass at their degenerate `0.0`/`None` values regardless of a sign
    error or a hardcoded `None`)."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entry = _first_contrast(run, "method=spearman")
    assert entry is not None
    assert entry["paired"] is True
    assert entry["n_paired"] > 0
    assert entry["method"] in ("paired_t_over_units", "paired_percentile_over_units")
    # A comparison is corrected against the family it belongs to, and the
    # default method is `holm` when the config names none. One comparison over
    # one metric is a family of one, whose only rank is corrected at α itself —
    # so `ci95_corrected` equals `ci95` here, and the arithmetic below is
    # unchanged by the correction pass.
    assert entry["correction"] == "holm"
    assert entry["family_size"] == 1
    assert entry["ci95_corrected"] == pytest.approx(entry["ci95"])
    # The shift is +1.0 for spearman over pearson on every unit, so the mean
    # per-unit difference is exactly 1.0 regardless of the alternating +0.5 —
    # pins the sign (`of - against`, not `against - of`) and the magnitude.
    assert entry["delta"] == pytest.approx(1.0)
    assert entry["ci95"] is not None
    low, high = entry["ci95"]
    assert low < entry["delta"] < high
    assert high - low > 0  # real variance from the alternating +0.5, not a point mass
    # `pred` is a recorded column, so `cohens_d = cohens_dz(diffs)` — a real
    # float, not the `None` a derived metric would carry.
    assert isinstance(entry["cohens_d"], float)


def test_a_contrast_crossing_two_axes_is_marked_confounded(tmp_path, capsys, monkeypatch):
    """`reference.md`: "A contrast crossing two axes at once ... differs in two
    places, so its delta mixes the two effects and no amount of correct pairing
    separates them — that's the factorial main-effects problem, and it's why
    such a contrast is marked rather than merely reported." `differs_on` names
    the axes, because the boolean alone says a contrast is confounded without
    saying by what."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        sweep={
            "baseline": {"analysis.method": "pearson", "analysis.min_samples": 10},
            "grid": {"analysis.method": ["spearman"], "analysis.min_samples": [20]},
        },
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entries = [
        metric
        for condition in run["results"]["conditions"]
        for step_block in condition.get("vs_baseline", {}).values()
        for metric in step_block.values()
    ]
    crossed = [e for e in entries if e.get("confounded")]
    assert crossed, "a condition differing on both axes must be marked"
    assert crossed[0]["differs_on"] == ["analysis.method", "analysis.min_samples"]


def test_a_one_axis_contrast_carries_neither_marker(tmp_path, capsys, monkeypatch):
    """Absent, not `false`/`[]` — the house rule the `vs_baseline` block itself
    follows. A `confounded: false` on every ordinary contrast is noise a reader
    has to learn to skip."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entry = _first_contrast(run, "method=spearman")
    assert "confounded" not in entry
    assert "differs_on" not in entry


def test_a_baseline_only_axis_still_counts_toward_confounded(tmp_path, capsys, monkeypatch):
    """`sweep.baseline` may fix an axis the grid never sweeps at all — `validate`
    requires every `sweep.grid` axis to be fixed in `sweep.baseline` but never
    the reverse (`unfixed = [p for p in grid if p not in baseline]` is the check;
    nothing walks it the other way). When that baseline-only value diverges
    from the axis's own parameter default, a grid condition and the baseline
    genuinely differ on two axes — one swept (`analysis.method`), one fixed only
    in `sweep.baseline` (`analysis.confidence`, default `0.95`, pinned here to
    `0.99`) — even though the grid condition's own `Condition.values` never
    mentions the second axis at all. `_differing_axes` has to walk the union of
    both sides' keys to see it; a one-directional walk over the grid
    condition's keys alone would silently drop it, since that axis is absent
    from `values` on that side, not merely equal.
    """
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        sweep={
            "baseline": {"analysis.method": "pearson", "analysis.confidence": 0.99},
            "grid": {"analysis.method": ["spearman"]},
        },
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entry = _first_contrast(run, "method=spearman")
    assert entry is not None
    assert entry.get("confounded") is True
    assert entry.get("differs_on") == ["analysis.method", "analysis.confidence"]


def test_a_declared_contrast_crossing_two_axes_is_marked_confounded(
    tmp_path, capsys, monkeypatch
):
    """The same marking logic in `_comparison_step_blocks` backs
    `_compute_declared_contrasts` too, since both call it — but every other
    declared-contrast test in this module (`_declared_contrast_run`) uses a
    single-axis sweep, so that path has never been exercised. A two-axis grid
    plus a `statistics.contrasts` entry between the baseline and the one grid
    condition that differs from it on both axes proves the sharing actually
    holds, landing in `results.contrasts` rather than `vs_baseline`.
    """
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        sweep={
            "baseline": {"analysis.method": "pearson", "analysis.min_samples": 10},
            "grid": {
                "analysis.method": ["pearson", "spearman"],
                "analysis.min_samples": [10, 20],
            },
        },
        statistics={
            "contrasts": [
                {
                    "id": "crossed",
                    # Differs from baseline on both swept axes: method and
                    # min_samples. `label_for` renders grid labels in
                    # declaration order, joined by `__` (`sweep.AXIS_SEPARATOR`).
                    "of": "method=spearman__min_samples=20",
                    "against": "baseline",
                }
            ]
        },
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    contrasts = run["results"]["contrasts"]
    assert [c["id"] for c in contrasts] == ["crossed"]
    metrics = [
        metric
        for step_block in contrasts[0].values()
        if isinstance(step_block, dict)
        for metric in step_block.values()
        if isinstance(metric, dict)
    ]
    crossed = [m for m in metrics if m.get("confounded")]
    assert crossed, "a declared contrast differing on both axes must be marked"
    assert crossed[0]["differs_on"] == ["analysis.method", "analysis.min_samples"]


def test_a_baseline_sweep_reports_a_corrected_interval(tmp_path, capsys, monkeypatch):
    """The whole slice, end to end: two comparisons over one metric is a family
    of 2 under the default `holm`, the weaker member is corrected by nothing, and
    the stronger one is corrected at α/2. `family` is broken out beside the size
    so a reviewer can check it."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman", "kendall"]},
        },
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    # Keyed by the condition's own label, not collected label-blind: the
    # *multiset* of levels survives every member ranking wrongly — with every
    # `Member.delta` zero, say, all members tie and Holm hands α/2 to whichever
    # comparison has the lower condition index, so the strongest claim in the
    # run can receive the weakest correction with the multiset unchanged. Which
    # arm gets which level is the only thing that pins the `cli` → `Member` →
    # rank path, and the expectation is computed from the record rather than
    # written down: the evidence ratio is |delta| over half the raw `ci95`
    # width, and the larger one must carry the tighter level.
    by_label = {
        condition["label"]: metric
        for condition in run["results"]["conditions"]
        for step_block in condition.get("vs_baseline", {}).values()
        for metric in step_block.values()
    }
    assert set(by_label) == {"method=spearman", "method=kendall"}
    entries = list(by_label.values())
    for entry in entries:
        assert entry["correction"] == "holm"
        assert entry["family_size"] == 2
        assert entry["family"] == {"comparisons": 2, "metrics": 1}
        assert entry["ci95_corrected"] is not None
    levels = sorted(e["correction_level"] for e in entries)
    assert levels == [pytest.approx(0.025), pytest.approx(0.05)]

    ratios = {
        label: abs(e["delta"]) / ((e["ci95"][1] - e["ci95"][0]) / 2.0)
        for label, e in by_label.items()
    }
    strong_label, weak_label = sorted(ratios, key=lambda label: -ratios[label])
    # Not a tie: on a tie the assertions below would pass under any ranking,
    # which is exactly the vacuity this test exists to close.
    assert ratios[strong_label] > ratios[weak_label]
    strongest = by_label[strong_label]
    weakest = by_label[weak_label]
    assert strongest["correction_level"] == pytest.approx(0.025)
    assert weakest["correction_level"] == pytest.approx(0.05)
    assert weakest["ci95_corrected"] == pytest.approx(weakest["ci95"])
    assert strongest["ci95_corrected"][0] < strongest["ci95"][0]
    assert strongest["ci95_corrected"][1] > strongest["ci95"][1]


def test_each_member_carries_the_condition_index_of_its_own_comparison():
    """`Member.condition_index` is read in exactly one place — `rank_family`'s
    tie-break — so hardcoding it to `0` in `cli` changes nothing until two
    members tie, and then it silently reorders them and hands out the wrong
    levels. No end-to-end record carries the index, so the assignment is pinned
    where it is made: `_comparison_step_blocks` called directly with a
    comparison whose `of` is deliberately not `0`, the same
    called-directly treatment `_check_contrasts`'s kept guard gets in
    `tests/test_validate.py`."""
    from publishable.cli import _comparison_step_blocks
    from publishable.contrasts import Comparison
    from publishable.diagnostics import Collector
    from publishable.sweep import Condition
    from publishable.units import Unit, UnitList

    roster = UnitList([Unit(key=f"u{i}") for i in range(12)])
    of_collapsed = {f"u{i}": {"r": 1.0 + 0.1 * (i % 3)} for i in range(12)}
    against_collapsed = {f"u{i}": {"r": 0.5} for i in range(12)}
    block, members = _comparison_step_blocks(
        Comparison(id="c", of=2, against=0),
        roster=roster,
        aggregated={2: {"s": {"r": 1.1}}, 0: {"s": {"r": 0.5}}},
        collapsed_by_key={(2, "s"): of_collapsed, (0, "s"): against_collapsed},
        derived_by_key={},
        resample_fns_by_key={},
        seed=7,
        draws=200,
        min_reported_n=None,
        findings=Collector(),
        where="condition 2",
        where_id="cond:2",
        conditions_by_index={
            0: Condition(index=0, label="baseline", is_baseline=True),
            2: Condition(index=2, label="method=kendall", values={"analysis.method": "kendall"}),
        },
    )
    assert block["s"]["r"]["ci95"] is not None
    assert [(m.where, m.condition_index, m.step, m.metric) for m in members] == [
        ("cond:2", 2, "s", "r")
    ]
    assert members[0].delta == pytest.approx(block["s"]["r"]["delta"])
    assert members[0].delta != 0.0


@pytest.mark.parametrize("method", ["none", "bonferroni", "holm", "fdr_bh"])
def test_the_configured_correction_method_decides_the_record(
    tmp_path, capsys, monkeypatch, method
):
    """`statistics.correction` is read from the config, and each of its four
    values produces the record `reference.md` § Statistical reporting's table
    requires. Without this, hardcoding `"holm"` at the call site passes every
    other test in this file — the config→record path for the one field that
    decides how every interval in a run is corrected would be unpinned, and
    the `none` row in particular backs a claim (the corrected fields are
    *absent*, not null, since an explicit null would say a correction was
    attempted and found nothing to do) that nothing else checks.

    One family throughout: two non-baseline arms over one metric, so *m* = 2
    and α/m = 0.025 — far enough from α = 0.05 that a method reading the wrong
    row cannot land on the right number.
    """
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman", "kendall"]},
        },
        statistics={"correction": method},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entries = [
        metric
        for condition in run["results"]["conditions"]
        for step_block in condition.get("vs_baseline", {}).values()
        for metric in step_block.values()
    ]
    assert len(entries) == 2
    if method == "none":
        for entry in entries:
            # `correction: null` is the metric block's own default, which is
            # what says "uncorrected" here; the other four fields never appear.
            assert entry["correction"] is None
            absent = {"ci95_corrected", "correction_level", "family_size", "family"}
            assert absent.isdisjoint(entry)
        return
    for entry in entries:
        assert entry["correction"] == method
        assert entry["family_size"] == 2
        assert entry["family"] == {"comparisons": 2, "metrics": 1}
    if method == "fdr_bh":
        # Controlling a false discovery *rate* is a statement about a set, not
        # a bound on any one comparison, so there is no level and no interval —
        # but the family is still counted, and still says so.
        for entry in entries:
            assert entry["ci95_corrected"] is None
            assert entry["correction_level"] is None
        return
    levels = sorted(e["correction_level"] for e in entries)
    if method == "bonferroni":
        # α/m for every member, rank or no rank.
        assert levels == [pytest.approx(0.025), pytest.approx(0.025)]
        for entry in entries:
            assert entry["ci95_corrected"][0] < entry["ci95"][0]
            assert entry["ci95_corrected"][1] > entry["ci95"][1]
        return
    # holm: α/(m−i+1), so rank 2 of 2 is corrected by nothing at all.
    assert levels == [pytest.approx(0.025), pytest.approx(0.05)]
    weakest = next(e for e in entries if e["correction_level"] == pytest.approx(0.05))
    assert weakest["ci95_corrected"] == pytest.approx(weakest["ci95"])


def test_no_draw_pool_reaches_the_record(tmp_path, capsys, monkeypatch):
    """A corrected interval is read off 2000 stored draws. Those must travel
    beside the record, never inside it: a run.yaml carrying a 2000-element array
    per metric is unreadable, and `io` never promised to serialize one."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    # The `results` block, not the whole file: `run.yaml` echoes the config,
    # whose `input_dir`/`output_dir` are under a `tmp_path` named after this
    # very test — so a whole-file `"pool" not in text` fails on the pytest
    # directory rather than on anything core wrote. Every field a member
    # carries would land here, in a comparison entry, or nowhere.
    text = yaml.safe_dump(run["results"], sort_keys=False)
    assert "pool" not in text
    assert "diffs" not in text
    # `"thin:"`, not `"thin"`: the bare substring is satisfied by `within`,
    # so a record legitimately carrying a `within` stratum would fail this for
    # a reason that has nothing to do with a leaked field.
    assert "thin:" not in text
    entry = _first_contrast(run, "method=spearman")
    assert not [k for k in entry if k.startswith("_")]


def test_a_contrast_named_after_a_condition_index_is_its_own_comparison(
    tmp_path, capsys, monkeypatch
):
    """The family is counted over distinct comparisons, so the key that
    identifies one must not be forgeable. A declared contrast may carry any
    `id` — `validate` refuses only an unresolvable `of`/`against` — and `id:
    "1"` is exactly the string condition 1's own `vs_baseline` block would be
    addressed by. Merged, they are one comparison instead of two: a family of 1
    where there are 2, an α twice as large as it should be, and two intervals
    narrower than the evidence supports in the direction no reader can check.

    This declared contrast is the *same* comparison as the baseline block, over
    the same 10 units, so the two raw intervals are identical and only the
    family separates them: an implementation that merges them cannot be caught
    by any assertion on `ci95`.
    """
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
        statistics={
            "contrasts": [{"id": "1", "of": "method=spearman", "against": "baseline"}]
        },
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    from_baseline = _first_contrast(run, "method=spearman")
    declared = run["results"]["contrasts"][0]["step01_summarize_units"]["pred"]
    assert from_baseline is not None
    for entry in (from_baseline, declared):
        assert entry["family_size"] == 2
        assert entry["family"] == {"comparisons": 2, "metrics": 1}
        assert entry["ci95_corrected"] is not None
    levels = sorted(e["correction_level"] for e in (from_baseline, declared))
    assert levels == [pytest.approx(0.025), pytest.approx(0.05)]


def _named_contrast(run: dict[str, Any], label: str, metric: str) -> dict[str, Any] | None:
    """One *named* metric in the condition labeled `label`'s `vs_baseline`
    block. `_first_contrast` takes whichever metric comes first, which is the
    recorded column when a step records one and its `aggregate` derives another
    — so a caller after the derived one has to say which."""
    for condition in run["results"]["conditions"]:
        if condition.get("label") != label:
            continue
        for step_block in condition.get("vs_baseline", {}).values():
            if metric in step_block:
                found = step_block[metric]
                assert isinstance(found, dict)
                return found
    return None


def test_a_derived_contrast_resamples_each_side_with_its_own_formula(
    tmp_path, capsys, monkeypatch
):
    """The end-to-end guard on the shared-closure cancellation. The step records
    an identical `pred` under both conditions and only the *formula* differs by
    `analysis.method` — the documented worked example's shape, where
    `analysis.method` changes what `aggregate` computes rather than what the
    step records. Evaluating one side's closure against both sides' draws makes
    the difference cancel on every draw: a zero-width `ci95` at zero beside a
    nonzero point-estimate `delta`, an interval that does not contain its own
    estimate. `tests/test_stats.py` pins this inside
    `paired_percentile_of_derived`; only a run through `main(["run", ...])`
    pins the *call site*, where passing `compute_of` for both sides
    reintroduces it with every unit test green.
    """
    import publishable.generators.experiment as experiment_gen
    from publishable.templates.builtin.generic import GenericTemplate

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _AGGREGATE_STEP)
    monkeypatch.setattr(
        GenericTemplate,
        "aggregate",
        lambda self, units, cfg: {
            "score": (
                2.0 if cfg.parameters.analysis.method == "spearman" else 1.0
            )
            * sum(units.pred)
            / len(units)
        },
    )
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entry = _named_contrast(run, "method=spearman", "score")
    assert entry is not None
    assert entry["method"] == "paired_percentile_over_units"
    # `pred` is 0.0..39.0, so the baseline's mean is 19.5 and spearman's is
    # 39.0 — a delta of exactly 19.5, which the interval has to bracket.
    assert entry["delta"] == pytest.approx(19.5)
    low, high = entry["ci95"]
    assert low < entry["delta"] < high
    # A derived metric has no per-unit value to difference, so no Cohen's d —
    # the reason the worked example carries `cohens_d: null` for `r`.
    assert entry["cohens_d"] is None


_COHORT_VARYING_STEP = '''\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        # `pred` varies *within* cohort `a` (so the stratum's own interval is
        # not a point mass) and is offset by 1000 in cohort `b` (so a whole-
        # sample mean is nowhere near the cohort-`a` one). Identical under both
        # conditions: only the aggregate FORMULA varies, which is the worked
        # example's shape.
        for i, unit in enumerate(io.units):
            offset = 0.0 if unit.attributes["cohort"] == "a" else 1000.0
            io.record(unit.key, {{"pred": float(i) + offset}})
        return {{"n_units": len(io.units)}}
'''


def _stratified_derived_run(tmp_path, capsys, monkeypatch, within):
    """A `within` contrast on a metric the template derives, where the stratum's
    delta and the whole-sample delta are far apart — so an interval built over
    the intersection and a point estimate built over the full roster cannot be
    mistaken for each other."""
    import publishable.generators.experiment as experiment_gen
    from publishable.templates.builtin.generic import GenericTemplate

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _COHORT_VARYING_STEP)
    monkeypatch.setattr(
        GenericTemplate,
        "aggregate",
        lambda self, units, cfg: {
            "score": (2.0 if cfg.parameters.analysis.method == "spearman" else 1.0)
            * sum(units.pred)
            / len(units)
        },
    )
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=20,
        unit_attributes=["cohort"],
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
        statistics={
            "contrasts": [
                {
                    "id": "stratum",
                    "of": "method=spearman",
                    "against": "baseline",
                    "within": within,
                }
            ]
        },
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    return run["results"]["contrasts"][0]["step01_summarize_units"]["score"]


def test_a_stratified_derived_delta_is_computed_over_its_own_intersection(
    tmp_path, capsys, monkeypatch
):
    """`reference.md` § Contrasts: "a paired comparison exists only for units
    that completed in *both*. Differencing the two condition means instead
    would not be a paired comparison at all, however carefully `paired: true`
    was derived." A derived metric has no per-unit value to difference, so the
    delta is `aggregate` evaluated on each side — but over the *intersection*,
    the same units the interval rests on. Taking the two conditions'
    whole-sample `aggregated` values instead puts a point estimate outside its
    own interval the moment a `within` narrows one and not the other.

    `pred` is `i` on the ten cohort-`a` units (roster indices 1, 3, .., 19,
    since `p1` is cohort `b`) and `i + 1000` on the cohort-`b` ones, and
    `score` is `k·mean(pred)` with `k` 1.0 under pearson and 2.0 under
    spearman. Over cohort `a` alone mean(pred) = 10.0, so the stratum's delta
    is 10.0; over all 20 units it is 509.5. The whole-sample number is not
    merely imprecise here — it is 51× the quantity the interval describes.
    """
    entry = _stratified_derived_run(tmp_path, capsys, monkeypatch, {"cohort": "a"})
    assert entry["n_paired"] == 10
    assert entry["delta"] == pytest.approx(10.0)
    low, high = entry["ci95"]
    assert low < entry["delta"] < high


def test_a_derived_contrast_over_an_empty_stratum_reports_no_delta(
    tmp_path, capsys, monkeypatch
):
    """`reference.md` § Contrasts: "A contrast whose intersection is empty is
    reported as such rather than as a delta of zero." Reported as a *number* is
    worse than either — a confident 509.5 with no denominator beside it — which
    is what a whole-sample point estimate does here, since nothing about the
    two conditions' own aggregates knows the stratum matched nobody."""
    entry = _stratified_derived_run(tmp_path, capsys, monkeypatch, {"cohort": "z"})
    assert entry["n_paired"] == 0
    assert entry["delta"] is None
    assert entry["ci95"] is None


def _declared_contrast_run(tmp_path, capsys, monkeypatch, **kwargs):
    """A run declaring one `statistics.contrasts` entry that is field-for-field
    indistinguishable from the auto-generated baseline comparison — same `of`,
    same `against`, and an `id` equal to `of`'s own label — except for its
    `within` stratum. `validate` permits every part of that, so it is the shape
    that separates reading `Comparison.declared` from reconstructing
    "auto-generated?" out of `id`/`against`.
    """
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        unit_attributes=["cohort"],
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
        statistics={
            "contrasts": [
                {
                    "id": "method=spearman",
                    "of": "method=spearman",
                    "against": "baseline",
                    "within": {"cohort": "a"},
                }
            ]
        },
        **kwargs,
    )
    return yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())


def test_a_declared_contrast_lands_beside_the_conditions_not_inside_one(
    tmp_path, capsys, monkeypatch
):
    """`reference.md` § Contrasts: a contrast belongs to neither of its sides, so
    a declared entry is `results.contrasts`, never a condition's `vs_baseline`.
    Reconstructing "auto-generated?" as `against == baseline and id ==
    label_of(of)` misfiles this entry into `vs_baseline` — where, because
    declared entries are resolved second, it *overwrites* the genuine
    unrestricted block — and it never reaches `results.contrasts` at all.
    """
    run = _declared_contrast_run(tmp_path, capsys, monkeypatch)
    contrasts = run["results"]["contrasts"]
    assert [c["id"] for c in contrasts] == ["method=spearman"]
    assert contrasts[0]["of"] == "01_method=spearman"
    assert contrasts[0]["against"] == "00_baseline"


def test_a_declared_contrast_does_not_displace_the_baseline_block(
    tmp_path, capsys, monkeypatch
):
    """The data-loss half of the same defect, and the half that a placement
    assertion alone would miss: the condition's own `vs_baseline` must still
    hold the *unrestricted* comparison over all 10 units, not the declared
    entry's `cohort: a` half of them.
    """
    run = _declared_contrast_run(tmp_path, capsys, monkeypatch)
    unrestricted = _first_contrast(run, "method=spearman")
    assert unrestricted is not None
    assert unrestricted["n_paired"] == 10
    restricted = run["results"]["contrasts"][0]
    n_paired = {
        metric["n_paired"]
        for step_block in restricted.values()
        if isinstance(step_block, dict)
        for metric in step_block.values()
    }
    assert n_paired == {5}  # the `cohort: a` half, and it did not land above


def test_a_run_with_no_baseline_has_no_vs_baseline_block(tmp_path, capsys):
    """Absent, not empty. An empty block would claim a comparison was made and
    found nothing."""
    doc = run_a_project(tmp_path, capsys=capsys)
    text = (doc["run_dir"] / "run.yaml").read_text()
    assert "vs_baseline" not in text


def test_a_baseline_sweep_with_no_metric_has_no_vs_baseline_block(tmp_path, capsys):
    """The discriminating case `test_a_run_with_no_baseline_has_no_vs_baseline_
    block` can't reach: a declared baseline exists (comparisons are resolved),
    but the scaffold's default step records only a bool, so every
    `metric_block` this task builds is empty. This is what actually exercises
    `_compute_vs_baseline`'s `return out or None` and `run_record.py`'s
    `if block:` guard — with no baseline at all, both are already unreachable
    for a different reason, and either could be silently dropped without this
    test moving."""
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
    )
    text = (doc["run_dir"] / "run.yaml").read_text()
    assert "vs_baseline" not in text


def test_a_thin_within_contrast_warns(tmp_path, capsys, monkeypatch):
    """`reference.md` § Contrasts scopes `limits.min_reported_n` to a `within`
    contrast's `n_paired` — "a stratified paired comparison is where a small
    denominator is easiest to miss and most disclosive" — so the stratum is
    what makes this fire. The assertion names the identifier: both the `where`
    field and the message body contain the substring `min_reported_n`, so an
    assertion on that alone stays green under any other diagnostic and under a
    renamed code."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=6,
        unit_attributes=["cohort"],
        limits={"min_reported_n": 10},
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
        statistics={
            "contrasts": [
                {
                    "id": "thin",
                    "of": "method=spearman",
                    "against": "baseline",
                    "within": {"cohort": "a"},
                }
            ]
        },
    )
    assert "W-STATS-CONTRAST-THIN" in doc["stdout"]


def test_an_unstratified_contrast_below_min_reported_n_does_not_warn(
    tmp_path, capsys, monkeypatch
):
    """The other half of that scope, and the reason it matters: `min_reported_n:
    10` is in every generated config (`materialize.py`), so warning on every
    comparison would fire on any pilot under ten units — a disclosure warning
    for a comparison the document never scoped it to. Same 6-unit roster as
    above, no `within`, so `n_paired` is 6 against a floor of 10."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=6,
        limits={"min_reported_n": 10},
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
    )
    assert "W-STATS-CONTRAST-THIN" not in doc["stdout"]


def _first_metric_width(run: dict[str, Any], condition_index: int) -> float:
    """The `ci95` width of the first numeric metric in one condition's
    `aggregated` block — the per-condition counterpart to `_first_contrast`'s
    delta, so a caller can compare the two widths directly."""
    condition = run["results"]["conditions"][condition_index]
    for step_block in condition["aggregated"].values():
        for metric in step_block.values():
            assert isinstance(metric, dict)
            if metric.get("ci95") is not None:
                low, high = metric["ci95"]
                return high - low
    raise AssertionError("no numeric metric with a ci95 found in this condition")


def test_a_paired_delta_is_narrower_than_the_conditions_it_compares(
    tmp_path, capsys, monkeypatch
):
    """The contrast that `allocation: within` buys, end to end: per-condition
    intervals are wide and the delta's is narrow, over the same units.

    The margin is a ratio, not `<`. Measured on this fixture the delta's width
    is ≈0.181 against a per-condition ≈12.577 — about 70× — so a bare `width <
    per_condition` passes at 12.5 and would stay green for an implementation
    that had lost almost all of the pairing benefit (an unpaired construction
    over the same two conditions is *wider* than either side, not narrower).
    `/10` keeps a 7× margin over what the fixture actually produces while
    refusing anything that isn't recognisably paired.
    """
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=120,
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    delta = _first_contrast(run, "method=spearman")
    assert delta is not None
    width = delta["ci95"][1] - delta["ci95"][0]
    per_condition = _first_metric_width(run, condition_index=1)
    assert width < per_condition / 10


def test_the_delta_interval_matches_this_fixture_s_own_arithmetic(tmp_path, capsys, monkeypatch):
    """The lower half of the bracket, and it is computed from this fixture
    rather than borrowed. `_METHOD_VARYING_STEP` shifts every unit by exactly
    +1.0 between the two conditions and alternates a further ±0.5, so the 120
    per-unit differences are 60 at 1.5 and 60 at 0.5: mean 1.0, sample sd
    0.5·√(120/119) = 0.502096, standard error 0.045836, and with
    t(0.975, 119) = 1.980100 a half-width of 0.090767 — a width of 0.181534.

    A bare `high > low` is what stood here, and it rejects only a zero-width
    interval; CLAUDE.md's ≈0.033 floor, which the old docstring cited, is an
    n≈228 linear-versus-rank number that says nothing about this fixture. The
    exact value is assertable because a *t* interval over a deterministic
    column involves no drawing at all — nothing here is seed-dependent.
    """
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=120,
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entry = _first_contrast(run, "method=spearman")
    assert entry is not None
    lo, hi = entry["ci95"]
    assert hi - lo == pytest.approx(0.1815155, rel=1e-5)
    assert lo == pytest.approx(1.0 - 0.0907577, rel=1e-5)
    assert hi == pytest.approx(1.0 + 0.0907577, rel=1e-5)


# --- Task 9 (carries): limits.max_ineligible_fraction ------------------------

_SKIP_MOST_STEP = '''\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        # 8 of 10 units declared ineligible, which is `io.skip`'s meaning: not a
        # failure, and deliberately not attrition. The other two record a value so
        # the step still produces a numeric column.
        for i, unit in enumerate(io.units):
            if i < 8:
                io.skip(unit.key, "outside the eligibility window")
            else:
                io.record(unit.key, {{"pred": float(i)}})
        return {{"n_units": len(io.units)}}
'''


def test_a_condition_skipping_too_many_units_warns(tmp_path, capsys, monkeypatch):
    """`limits.max_ineligible_fraction` was written into every generated config
    and read by nothing — the last live silent no-op of the class S4a's refusals
    closed. `io.skip` is what declares a unit ineligible."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _SKIP_MOST_STEP)
    doc = run_a_project(
        tmp_path, capsys=capsys, units=10, limits={"max_ineligible_fraction": 0.2}
    )
    assert "W-DATA-INELIGIBLE" in doc["stdout"]


def test_a_string_ineligible_limit_does_not_raise_or_warn(tmp_path, capsys, monkeypatch):
    """`limits` is user-written YAML, and `command_run` must not raise on a
    string threshold. `isinstance(max_ineligible, (int, float))` fails for a
    string, so the whole guard is skipped — no warning, no traceback — even
    though 8 of 10 units are ineligible, which would trip a numeric threshold
    below 0.8."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _SKIP_MOST_STEP)
    doc = run_a_project(
        tmp_path, capsys=capsys, units=10, limits={"max_ineligible_fraction": "half"}
    )
    assert "W-DATA-INELIGIBLE" not in doc["stdout"]


def test_a_true_ineligible_limit_does_not_warn(tmp_path, capsys, monkeypatch):
    """Kept as documentation, not as the guard's real test: `True` compares equal
    to `1`, and a fraction can never exceed `1`, so this case cannot distinguish
    the `bool` exclusion's presence from its absence — either way nothing warns.
    `test_a_false_ineligible_limit_does_not_warn` below is the discriminating
    case."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _SKIP_MOST_STEP)
    doc = run_a_project(
        tmp_path, capsys=capsys, units=10, limits={"max_ineligible_fraction": True}
    )
    assert "W-DATA-INELIGIBLE" not in doc["stdout"]


def test_a_false_ineligible_limit_does_not_warn(tmp_path, capsys, monkeypatch):
    """The case that actually earns the `bool` exclusion: `False == 0`, so
    without `not isinstance(max_ineligible, bool)` the guard would read
    `max_ineligible_fraction: false` as a `0.0` threshold and warn the moment
    any unit is ineligible — `_SKIP_MOST_STEP` skips 8 of 10, well above zero.
    With the exclusion, `false` is not a real fraction and the whole guard is
    skipped, so nothing warns."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _SKIP_MOST_STEP)
    doc = run_a_project(
        tmp_path, capsys=capsys, units=10, limits={"max_ineligible_fraction": False}
    )
    assert "W-DATA-INELIGIBLE" not in doc["stdout"]


# --- Task 10 (correction-family): acceptance ---------------------------------

_WIDE_COLUMN_STEP = '''\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        units = list(io.units)
        shift = {{"pearson": 0, "spearman": 1, "kendall": 3}}.get(
            cfg.parameters.analysis.method, 0
        )
        for i, unit in enumerate(units):
            extra = 0.5 if (i + shift) % 2 == 1 else 0.0
            base = float(i) + float(shift) + extra
            io.record(unit.key, {{f"pred{{j:02d}}": base * (j + 1) for j in range(14)}})
        return {{"n_units": len(units)}}
'''




def test_a_declared_contrast_with_a_stratum_joins_the_correction_family(
    tmp_path, capsys, monkeypatch
):
    """`reference.md`: a declared contrast joins the correction family alongside
    the baseline comparisons, "because a reader shown both is exposed to both."
    One baseline comparison plus one declared contrast is a family of 2, and both
    entries must say so — correcting only `vs_baseline` under-corrects by exactly
    the contrasts the config asked for.

    The `within` stratum is what this adds over
    `test_a_contrast_named_after_a_condition_index_is_its_own_comparison`, which
    pins the same family arithmetic for an unstratified declared contrast: a
    subgroup a config asks to *test* joins the family too (it is a contrast, not
    a `report_by` stratum), even though it rests on half the roster and so
    carries different evidence from the comparison it sits beside.
    """
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        unit_attributes=["cohort"],
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
        statistics={
            "correction": "holm",
            "contrasts": [
                {
                    "id": "stratum_a",
                    "of": "method=spearman",
                    "against": "baseline",
                    "within": {"cohort": "a"},
                }
            ],
        },
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    baseline_entry = _first_contrast(run, "method=spearman")
    # Addressed explicitly rather than by "the first dict-valued key": a
    # contrast entry's own `id`/`of`/`against` are strings today, but a future
    # field carrying a mapping (an echoed `within`, say) would make a generic
    # scan iterate the stratum instead of a metric block.
    declared_entry = run["results"]["contrasts"][0]["step01_summarize_units"]["pred"]
    assert baseline_entry is not None
    # The stratum really is half the roster, so the two members are not the same
    # comparison wearing two names.
    assert declared_entry["n_paired"] == 20
    assert baseline_entry["n_paired"] == 40
    for entry in (baseline_entry, declared_entry):
        assert entry["family_size"] == 2
        assert entry["family"] == {"comparisons": 2, "metrics": 1}
        assert entry["correction"] == "holm"
    assert sorted(
        [baseline_entry["correction_level"], declared_entry["correction_level"]]
    ) == [pytest.approx(0.025), pytest.approx(0.05)]


def test_fdr_bh_records_the_correction_it_could_not_apply(tmp_path, capsys, monkeypatch):
    """The documented state, end to end: the correction is named in the record,
    every `ci95_corrected` is null, and `run`'s own stdout says why. Nothing is
    silent, and nothing claims an adjustment that did not happen.

    `test_the_configured_correction_method_decides_the_record[fdr_bh]` pins the
    record; what this adds is the pairing — the warning `validate` raises
    reaching the operator through `main(["run", ...])`, not only through a
    `validate` unit test, since a record with null intervals and no visible
    reason is the failure mode the warning exists to prevent."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        statistics={"correction": "fdr_bh"},
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entry = _first_contrast(run, "method=spearman")
    assert entry["correction"] == "fdr_bh"
    assert entry["ci95_corrected"] is None
    assert entry["correction_level"] is None
    assert "p_value_corrected" not in entry
    assert "W-STATS-CORRECTION-INAPPLICABLE" in doc["stdout"]


def test_an_uncorrected_run_carries_no_corrected_fields(tmp_path, capsys, monkeypatch):
    """Under `correction: none` the fields are *absent*, per `reference.md`'s
    table — and `W-STATS-FAMILY` reaches stdout, which is the pairing that makes
    an uncorrected family honest rather than hidden. S4b writes `correction:
    None` onto every entry, and `correction: none` must leave that null rather
    than the string `"none"`: an explicit method name would claim a correction
    was applied."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        statistics={"correction": "none"},
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entry = _first_contrast(run, "method=spearman")
    assert "ci95_corrected" not in entry
    assert "correction_level" not in entry
    assert "family_size" not in entry
    assert entry["correction"] is None  # the S4b field, still there and still null
    assert "W-STATS-FAMILY" in doc["stdout"]


def test_a_family_too_wide_for_the_draws_reports_no_corrected_interval(
    tmp_path, capsys, monkeypatch
):
    """`W-STATS-CORRECTED-THIN`, end to end — the one identifier this slice
    minted that no other test produces.

    The arithmetic that makes it fire: a percentile interval needs
    `min_honest_draws(1 - level)` = `ceil(4 / level)` draws, so a 2000-draw pool
    supports a corrected level down to exactly 0.002 and no further. Three
    method arms give 2 comparisons; a step recording 14 per-unit columns beside
    one `aggregate`-derived metric gives 15 metrics; the family is 2 × 15 = 30,
    and `bonferroni` hands *every* member α/30 = 0.0016667, whose floor of 2400
    draws the pool cannot meet.

    `bonferroni`, not the default `holm`, on purpose: under `holm` the last rank
    is corrected at α itself, so the widest-level member is never thin and "every
    derived member is thin" could not be asserted at all.

    Two halves, and both matter. The derived metric is thin — and the disclosure
    is the point: `correction_level` still records the level that was *asked
    for*, so a reader sees a correction that was scoped and could not be built,
    rather than a null that reads as "no correction applies". The 14 recorded
    columns, corrected through `paired_t_over_units` instead, are exact at any α
    and come back strictly wider: thinness is a property of the draw pool, not
    of the level, and a `ci95_corrected: null` blanket over the whole family
    would be the wrong record.
    """
    import publishable.generators.experiment as experiment_gen
    from publishable.templates.builtin.generic import GenericTemplate

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _WIDE_COLUMN_STEP)
    monkeypatch.setattr(
        GenericTemplate,
        "aggregate",
        lambda self, units, cfg: {"score": sum(units.pred00) / len(units)},
    )
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        statistics={"correction": "bonferroni"},
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman", "kendall"]},
        },
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entries = [
        (name, metric)
        for condition in run["results"]["conditions"]
        for step_block in condition.get("vs_baseline", {}).values()
        for name, metric in step_block.items()
    ]
    derived = [metric for name, metric in entries if name == "score"]
    recorded = [metric for name, metric in entries if name.startswith("pred")]
    assert len(derived) == 2 and len(recorded) == 28
    # Counted from the record rather than asserted from the plan: 15 distinct
    # (step, metric) pairs over 2 comparisons is what the family *is*, and the
    # size is the product.
    assert {metric["family"]["comparisons"] for _, metric in entries} == {2}
    assert {metric["family"]["metrics"] for _, metric in entries} == {15}
    assert {metric["family_size"] for _, metric in entries} == {30}
    assert all(
        metric["correction_level"] == pytest.approx(0.05 / 30) for _, metric in entries
    )
    for metric in derived:
        assert metric["method"] == "paired_percentile_over_units"
        # Not a point mass: the raw interval this one could not be corrected
        # against is a real interval, so `None` below is thinness rather than
        # a degenerate fixture with nothing to widen.
        assert metric["ci95"][0] < metric["delta"] < metric["ci95"][1]
        assert metric["ci95_corrected"] is None
    for metric in recorded:
        assert metric["ci95_corrected"][0] < metric["ci95"][0]
        assert metric["ci95_corrected"][1] > metric["ci95"][1]
    assert "W-STATS-CORRECTED-THIN" in doc["stdout"]
    assert "score" in doc["stdout"] and "0.00167" in doc["stdout"]


def test_a_derived_metric_is_corrected_off_its_own_draw_pool(tmp_path, capsys, monkeypatch):
    """The widening property for the *pool* branch of `_corrected_bounds`, which
    every other end-to-end correction test exercises only through
    `paired_t_over_units`: a derived metric's corrected interval is a second rank
    pair read off the same stored draws, so it strictly contains the raw one
    rather than being a fresh resample that could land inside it.

    The fixture is the one `test_a_derived_contrast_resamples_each_side_with_its
    _own_formula` already proved non-degenerate — the recorded `pred` is
    identical under every condition and only the aggregate *formula* varies —
    which makes each draw's difference `(factor − 1) × mean(drawn pred)`: a pool
    with many distinct values, so two different rank pairs cannot coincide by
    accident. `bonferroni` again, so the level does not depend on which member
    ranks where; a family of 4 puts it at 0.0125, whose 320-draw floor the
    2000-draw pool clears with room, which is what separates this case from the
    thin one above.
    """
    import publishable.generators.experiment as experiment_gen
    from publishable.templates.builtin.generic import GenericTemplate

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _AGGREGATE_STEP)
    monkeypatch.setattr(
        GenericTemplate,
        "aggregate",
        lambda self, units, cfg: {
            "score": {"pearson": 1.0, "spearman": 2.0, "kendall": 3.0}[
                cfg.parameters.analysis.method
            ]
            * sum(units.pred)
            / len(units)
        },
    )
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        statistics={"correction": "bonferroni"},
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman", "kendall"]},
        },
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    derived = [
        _named_contrast(run, label, "score") for label in ("method=spearman", "method=kendall")
    ]
    assert all(entry is not None for entry in derived)
    for entry in derived:
        assert entry["method"] == "paired_percentile_over_units"
        assert entry["family_size"] == 4
        assert entry["correction_level"] == pytest.approx(0.0125)
        assert entry["ci95"][0] < entry["ci95"][1]  # a real pool, not a point mass
        assert entry["ci95_corrected"][0] < entry["ci95"][0]
        assert entry["ci95_corrected"][1] > entry["ci95"][1]
    assert "W-STATS-CORRECTED-THIN" not in doc["stdout"]


def test_a_reporting_stratum_repeats_the_metric_over_its_own_units(
    tmp_path, capsys, monkeypatch
):
    """`reference.md` § Reporting strata: core "repeats the aggregation it already
    performs, over the subsets of the per-unit table each level picks out". Each
    level's `n` and `ci95` are its own — computed over that level's units, not
    the condition's. A stratum whose numbers equal the parent's is the defect
    this test exists to catch."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        unit_attributes=["cohort"],
        statistics={"report_by": ["cohort"]},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    step_block = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]
    by = step_block["by"]["cohort"]
    assert set(by) == {"a", "b"}
    for level in ("a", "b"):
        entry = by[level]["pred"]
        assert entry["basis"] == "units"
        assert entry["n"]["completed"] == 20
        # `completed` is computed per column from the table handed to
        # `summarize_step`, but `resolved` comes from the `counts` beside it —
        # so this is the assertion that catches a level's rows reported against
        # the condition's denominator, the S4b Critical's exact shape.
        assert entry["n"]["resolved"] == 20
        assert entry["ci95"] is not None
        # `repeat_spread` is the parent block's, not a stratum's: the documented
        # example carries value, basis, n and ci95 and nothing else, and `cli`
        # attaches spread outside `summarize_step`.
        assert "repeat_spread" not in entry
    # The parent block is unchanged and covers every unit.
    assert step_block["pred"]["n"]["completed"] == 40
    # Each level's interval is its own, not a copy of the parent's.
    assert by["a"]["pred"]["ci95"] != step_block["pred"]["ci95"]


def test_two_attributes_are_two_marginal_splits_not_their_cross(
    tmp_path, capsys, monkeypatch
):
    """`reference.md` § Reporting strata: "`report_by: [sex, site]` adds a `by.sex`
    block and a `by.site` block, each over the whole table; it does not produce a
    `f × site_03` cell." The cartesian product is the thing that section exists to
    avoid — five reporting attributes would be a cell explosion of subgroups
    nobody asked for."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        unit_attributes=["cohort", "arm"],
        statistics={"report_by": ["cohort", "arm"]},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    by = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]["by"]
    assert set(by) == {"cohort", "arm"}
    assert set(by["cohort"]) == {"a", "b"}
    # Each marginal covers the whole table, so the two levels sum to every unit.
    assert sum(by["cohort"][lv]["pred"]["n"]["completed"] for lv in by["cohort"]) == 40
    # No cell of the cross exists anywhere.
    assert "a__x" not in by["cohort"]
    assert not any(isinstance(v, dict) and "arm" in v for v in by["cohort"].values())


def test_a_run_without_report_by_has_no_by_block(tmp_path, capsys, monkeypatch):
    """Absent, not empty — the rule `vs_baseline` and `contrasts` already follow.
    An empty `by: {}` would claim a stratification was performed and found
    nothing."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(tmp_path, capsys=capsys, units=40)
    text = (doc["run_dir"] / "run.yaml").read_text()
    # A word boundary, not a bare `"by:" not in text`: the echoed config always
    # carries `cluster_by:` and `weight_by:`, so the bare substring is present in
    # every run.yaml ever written and would fail here for a reason that has
    # nothing to do with strata — and, worse, could not distinguish an
    # unconditional `by: {}` from its absence.
    assert re.search(r"\bby:", text) is None


def test_strata_do_not_join_the_correction_family(tmp_path, capsys, monkeypatch):
    """`reference.md` § Reporting strata: "Strata don't join the correction
    family, because a stratum is a description rather than a comparison a reader
    acts on." If they did, adding `report_by` would enlarge the family, shrink α,
    and silently tighten every real comparison in the run."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    sweep = {
        "baseline": {"analysis.method": "pearson"},
        "grid": {"analysis.method": ["spearman"]},
    }
    without = run_a_project(tmp_path / "a", capsys=capsys, units=40, sweep=sweep)
    with_strata = run_a_project(
        tmp_path / "b",
        capsys=capsys,
        units=40,
        unit_attributes=["cohort"],
        sweep=sweep,
        statistics={"report_by": ["cohort"]},
    )
    sizes = []
    for doc in (without, with_strata):
        run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
        entry = _first_contrast(run, "method=spearman")
        sizes.append((entry["family_size"], entry["family"]))
    assert sizes[0] == sizes[1]


# --- Fix round 1: the derived path, empty levels, and the reserved `by` key ---

_SKIP_ONE_COHORT_STEP = """\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        # Every unit of cohort `a` is ineligible, so that level completes
        # nothing at all while `b` completes normally. `io.skip` is the
        # declaration; the unit lands in `ineligible`, not in attrition.
        for i, unit in enumerate(io.units):
            if unit.attributes.get("cohort") == "a":
                io.skip(unit.key, "outside the eligibility window")
            else:
                io.record(unit.key, {{"pred": float(i)}})
        return {{"n_units": len(io.units)}}
"""


_RECORDS_A_BY_COLUMN_STEP = """\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        for i, unit in enumerate(io.units):
            io.record(unit.key, {{"pred": float(i), "by": float(i) * 2.0}})
        return {{"n_units": len(io.units)}}
"""


def test_a_stratum_recomputes_a_derived_metric_over_its_own_units(
    tmp_path, capsys, monkeypatch
):
    """`summarize_step` never recomputes a derived metric — it writes `value`
    straight through from the mapping it is handed, and takes only the interval
    and `n.completed` from the table beside it. So a stratum handed the parent's
    `derived` would publish the whole sample's point estimate against the level's
    own `n` and `ci95`: the S4b Critical's shape one layer in. `reference.md` §
    Reporting strata shows three different values (0.607 / 0.591 / 0.622) for
    exactly this reason."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _AGGREGATE_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        aggregate_returns="r",
        unit_attributes=["cohort"],
        statistics={"report_by": ["cohort"]},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    step_block = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]
    by = step_block["by"]["cohort"]
    # `pred` is `float(i)` over units in roster order, and `cohort` alternates,
    # so `a` holds the odd indices and `b` the even ones: 20, 19, and 19.5 over
    # the whole table. Three different numbers, none of them the parent's.
    assert step_block["r"]["value"] == pytest.approx(19.5)
    assert by["a"]["r"]["value"] == pytest.approx(20.0)
    assert by["b"]["r"]["value"] == pytest.approx(19.0)
    assert by["a"]["r"]["value"] != by["b"]["r"]["value"]
    for level in ("a", "b"):
        entry = by[level]["r"]
        assert entry["basis"] == "units"
        assert entry["n"]["completed"] == 20
        assert entry["n"]["resolved"] == 20
        # The interval is resampled over the level's own table, through the same
        # closure that recomputed the value.
        assert entry["ci95"] is not None
        assert entry["ci95"][0] <= entry["value"] <= entry["ci95"][1]
        assert entry["resample_draws"] == 2000


def test_a_level_that_completed_nothing_gets_no_block(tmp_path, capsys, monkeypatch):
    """A block whose metrics rest on no rows carries nothing
    `W-STATS-STRATUM-THIN` does not already say, so an empty level is absent
    rather than present-and-empty — the same absent-not-empty rule the `by` block
    itself follows. It also keeps `aggregate` from being called on an empty
    table, which raises for most templates."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _SKIP_ONE_COHORT_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        unit_attributes=["cohort"],
        statistics={"report_by": ["cohort"]},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    step_block = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]
    assert set(step_block["by"]["cohort"]) == {"b"}
    assert step_block["by"]["cohort"]["b"]["pred"]["n"]["completed"] == 20


def test_levels_are_reported_in_sorted_order(tmp_path, capsys, monkeypatch):
    """`levels_for` returns a plain dict in roster first-seen order, and
    `run.yaml` is dumped with `sort_keys=False` — so level order in the
    published record is whatever the level loop iterates. Sorting it is what
    makes two runs over the same roster produce byte-comparable records.

    The fixture discriminates because `run_a_project` writes `'ab'[i % 2]` with
    `i` starting at 1: `p1` is cohort `b`, so first-seen order is `b, a` — the
    reverse of alphabetical. A roster whose first unit were cohort `a` would
    pass this test with the sort removed."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        unit_attributes=["cohort"],
        statistics={"report_by": ["cohort"]},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    step_block = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]
    assert list(step_block["by"]["cohort"]) == ["a", "b"]


def test_a_derived_metric_named_by_is_refused_not_silently_overwritten(
    tmp_path, capsys, monkeypatch
):
    """`by` is reserved: it holds the reporting strata, beside the metric names
    in the same mapping, and every consumer of a step block reads its keys as
    metric names. A derived key of that name is `E-STEP-KEY-COLLISION`, caught by
    the retry that already contains that fault — the run survives, the whole
    `derived` mapping is dropped, and the strata are still reported."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _AGGREGATE_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        aggregate_returns="by",
        unit_attributes=["cohort"],
        statistics={"report_by": ["cohort"]},
    )
    assert "W-STATS-AGGREGATE-FAILED" in doc["stdout"]
    assert "E-STEP-KEY-COLLISION" in doc["stdout"]
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    step_block = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]
    # `by` holds the strata, not a metric: the recorded column survived, the
    # derived metric did not, and no `value` was written under the reserved key.
    assert set(step_block["by"]) == {"cohort"}
    assert "value" not in step_block["by"]
    assert step_block["pred"]["n"]["completed"] == 40


def test_a_recorded_column_named_by_keeps_its_metric_and_warns(
    tmp_path, capsys, monkeypatch
):
    """The other half of the reserved key, and it cannot be refused where the
    derived half is: the retry that contains `E-STEP-KEY-COLLISION` passes the
    same collapsed table, so raising for a recorded column would re-raise
    uncontained after the run has spent every execution. The column wins — it is
    a real measurement over the units, while the strata re-present numbers
    already in the record — and the run says so."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _RECORDS_A_BY_COLUMN_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        unit_attributes=["cohort"],
        statistics={"report_by": ["cohort"]},
    )
    assert "W-STATS-STRATUM-SHADOWED" in doc["stdout"]
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    step_block = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]
    # The metric, not the strata: it carries a value and an interval of its own.
    assert step_block["by"]["basis"] == "units"
    assert step_block["by"]["value"] == pytest.approx(39.0)
    assert "cohort" not in step_block["by"]


def test_a_recorded_by_column_warns_even_with_no_report_by_declared(
    tmp_path, capsys, monkeypatch
):
    """The disclosure follows the column, not the strata block. `by` is dropped
    from every comparison's metric set unconditionally
    (`_comparison_step_blocks`), so a recorded column of that name loses its
    `vs_baseline` delta whether or not `report_by` was declared — and the
    undeclared case is the one where the author has no other hint that the name
    is reserved. Gating the warning on a non-empty `by` block left it silent
    exactly there."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _RECORDS_A_BY_COLUMN_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
    )
    assert "W-STATS-STRATUM-SHADOWED" in doc["stdout"]
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    step_block = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]
    # The column is a real measurement and keeps its own number, warning or not.
    assert step_block["by"]["value"] == pytest.approx(39.0)
    # And the consequence the warning now names: no delta, no seat in the family.
    compared = next(
        c for c in run["results"]["conditions"] if c.get("label") == "method=spearman"
    )
    metrics = sorted(
        name
        for step_block in compared["vs_baseline"].values()
        for name in step_block
    )
    assert metrics == ["pred"]
    assert _first_contrast(run, "method=spearman")["family_size"] == 1


# --- Task 6: `W-STATS-STRATUM-THIN` at run time --------------------------------

_SKIP_MOST_OF_COHORT_A_STEP = """\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        # Cohort `a` all but disappears through `io.skip`, so its level is thin
        # only AFTER the run — the case a roster-time count cannot predict.
        kept = 0
        for unit in io.units:
            if unit.attributes["cohort"] == "a" and kept >= 3:
                io.skip(unit.key, "outside the eligibility window")
                continue
            if unit.attributes["cohort"] == "a":
                kept += 1
            io.record(unit.key, {{"pred": float(len(unit.key))}})
        return {{"n_units": len(io.units)}}
"""


def test_a_stratum_thinned_by_attrition_warns_at_run_time(tmp_path, capsys, monkeypatch):
    """The gap validate cannot see. `W-STATS-REPORTBY-THIN` counts *resolved*
    units from the roster; attrition happens during the run, so a level that
    looked fine can complete on a handful. `reference.md` § What study add
    redacts is explicit that a per-subgroup result over a handful of units is
    exactly what no automatic rule can judge safe — so it is disclosed where it
    is first knowable."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _SKIP_MOST_OF_COHORT_A_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        unit_attributes=["cohort"],
        limits={"min_reported_n": 10},
        statistics={"report_by": ["cohort"]},
    )
    assert "W-STATS-STRATUM-THIN" in doc["stdout"]
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    by = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]["by"]
    # The thin level still gets a block: that the subgroup produced almost
    # nothing IS the finding, and dropping it would hide what the warning names.
    assert by["cohort"]["a"]["pred"]["n"]["completed"] < 10


def test_a_stratum_thinned_to_zero_warns_and_gets_no_block(tmp_path, capsys, monkeypatch):
    """Pins the placement itself, not just the identifier. The warning sits
    ahead of both skip-gates precisely so the most disclosive case — a level
    that completed nothing — still warns even though it earns no block (the
    fix-round-1 amendment above this section). Moving the check to after gate 1
    leaves every other test in the suite green, because none of them asserts
    both halves together: the warning firing over a numeric `min_reported_n`
    (not the bool-guard case, which is pinned separately), and the level's
    block being genuinely absent from `run.yaml`, at once."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _SKIP_ONE_COHORT_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        unit_attributes=["cohort"],
        limits={"min_reported_n": 10},
        statistics={"report_by": ["cohort"]},
    )
    assert "W-STATS-STRATUM-THIN" in doc["stdout"]
    assert "level `a` of `cohort`" in doc["stdout"]
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    by = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]["by"]
    # No block for the vanished level: a block with no rows says nothing the
    # warning does not, and the amendment above already rules that out.
    assert set(by["cohort"]) == {"b"}


def test_a_thick_stratum_does_not_warn_stratum_thin(tmp_path, capsys, monkeypatch):
    """The negative case beside the attrition test: every level completes well
    above the floor, so nothing should fire. This is what an "always warn"
    mutation of the floor comparison is caught by."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _AGGREGATE_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        unit_attributes=["cohort"],
        limits={"min_reported_n": 10},
        statistics={"report_by": ["cohort"]},
    )
    assert "W-STATS-STRATUM-THIN" not in doc["stdout"]


def test_min_reported_n_true_over_an_empty_level_does_not_warn(tmp_path, capsys, monkeypatch):
    """Task 4's reasoning for dropping the `isinstance`/`bool` guard does not
    transfer here. `strata.levels_for` never emits a zero-count level, so at
    validate time a floor of `1` (`True`) is unreachable — `len(keys) < 1` never
    holds. But a level's *completed* count genuinely can be `0` at run time
    (every unit in the level failed or was skipped), so `min_reported_n: true`
    giving a floor of `1` would make `0 < 1` fire without the guard. Cohort `a`
    is skipped entirely here, so its level completes nothing — the guard must
    keep that from warning."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _SKIP_ONE_COHORT_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        unit_attributes=["cohort"],
        limits={"min_reported_n": True},
        statistics={"report_by": ["cohort"]},
    )
    assert "W-STATS-STRATUM-THIN" not in doc["stdout"]


def test_aggregate_failing_for_one_level_only_still_warns_and_reports_the_other(
    tmp_path, capsys, monkeypatch
):
    """The per-level `try` around user `aggregate` code, exercised rather than
    merely present. `aggregate` raises for exactly one level's table (keyed off
    `len(units)`, distinguishing cohort `a`'s 3 completed units from cohort
    `b`'s 20 and the whole table's 23): the run survives, the warning names
    that stratum, the failing level omits the derived metric rather than
    inheriting the parent's value, and the other level still reports its own."""
    import publishable.generators.experiment as experiment_gen
    from publishable.templates.builtin.generic import GenericTemplate

    def aggregate_that_fails_for_one_level(self, units, cfg):
        if len(units) == 3:
            raise RuntimeError("boom for the thin level only")
        return {"r": sum(units.pred) / len(units)}

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _SKIP_MOST_OF_COHORT_A_STEP)
    monkeypatch.setattr(GenericTemplate, "aggregate", aggregate_that_fails_for_one_level)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        unit_attributes=["cohort"],
        statistics={"report_by": ["cohort"]},
    )
    assert "W-STATS-AGGREGATE-FAILED" in doc["stdout"]
    assert "stratum cohort=a" in doc["stdout"]
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    by = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]["by"]
    # The failing level still has a block (its recorded column survived) but no
    # derived metric — it does not inherit the parent's or the sibling's value.
    assert "r" not in by["cohort"]["a"]
    assert by["cohort"]["a"]["pred"]["n"]["completed"] == 3
    # The sibling level's own metric survives untouched. Cohort `b` is the odd
    # patient indices (`'ab'[i % 2]` puts `i=1` at `'b'`), all 20 recorded.
    assert by["cohort"]["b"]["r"]["value"] == pytest.approx(
        sum(float(len(f"p{i}")) for i in range(1, 41) if i % 2 == 1) / 20
    )


def test_an_empty_level_produces_no_spurious_aggregate_failed(tmp_path, capsys, monkeypatch):
    """Empty-level gate 1 (`if not level_collapsed: continue`) is not pinned by
    any other test: the existing empty-level test passes no `aggregate_returns`,
    so the second gate (no metric produced) covers it just as well. With a
    derived metric in play, gate 1 does real work — without it, `aggregate` is
    called on an empty table, which raises for this template, and every empty
    level would spuriously warn `W-STATS-AGGREGATE-FAILED`."""
    import publishable.generators.experiment as experiment_gen
    from publishable.templates.builtin.generic import GenericTemplate

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _SKIP_ONE_COHORT_STEP)
    monkeypatch.setattr(
        GenericTemplate,
        "aggregate",
        lambda self, units, cfg: {"r": sum(units.pred) / len(units)},
    )
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        unit_attributes=["cohort"],
        statistics={"report_by": ["cohort"]},
    )
    assert "W-STATS-AGGREGATE-FAILED" not in doc["stdout"]
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    by = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]["by"]
    assert set(by["cohort"]) == {"b"}


# --- Task 7: acceptance — the three properties § Reporting strata claims -------


def test_a_derived_metric_is_stratified_with_its_own_resample(
    tmp_path, capsys, monkeypatch
):
    """A derived metric has no per-unit value, so its stratum interval is
    `aggregate` recomputed on that level's resampled table — the same
    construction the parent block uses, over fewer rows. A stratum reusing the
    parent's interval, or reporting none, both look plausible in the record.

    `pred` is `float(i)` in roster order and `cohort` alternates, so the three
    means are 19.5 over the whole table, 20.0 over `a` and 19.0 over `b` — the
    exact numbers `test_a_stratum_recomputes_a_derived_metric_over_its_own_units`
    pins; here they are only the reason the inequalities below are meaningful.
    """
    import publishable.generators.experiment as experiment_gen
    from publishable.templates.builtin.generic import GenericTemplate

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _AGGREGATE_STEP)
    monkeypatch.setattr(
        GenericTemplate,
        "aggregate",
        lambda self, units, cfg: {"score": sum(units.pred) / len(units)},
    )
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        unit_attributes=["cohort"],
        statistics={"report_by": ["cohort"]},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    step_block = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]
    parent = step_block["score"]
    level = step_block["by"]["cohort"]["a"]["score"]
    assert level["basis"] == "units"
    assert level["ci95"] is not None
    assert level["ci95"] != parent["ci95"]
    assert level["value"] != parent["value"]


def test_a_stratum_carries_no_corrected_fields(tmp_path, capsys, monkeypatch):
    """Strata are not comparisons, so nothing in a `by` block is corrected — and
    the four correction fields must be absent rather than null, the same
    distinction `correction: none` observes.

    Four, not five: `correction: null` is a field `summarize_step` writes on
    *every* metric block, parent and stratum alike, and it predates the
    correction family — it says "no multiplicity correction applies to this
    number," which is exactly what a stratum means. The four asserted here are
    the ones `corrected_for` attaches, and only to comparisons."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        unit_attributes=["cohort"],
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
        statistics={"report_by": ["cohort"]},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    for condition in run["results"]["conditions"]:
        by_block = condition["aggregated"]["step01_summarize_units"]["by"]["cohort"]
        assert by_block
        for level in by_block.values():
            for entry in level.values():
                assert isinstance(entry, dict)
                assert {
                    "ci95_corrected",
                    "correction_level",
                    "family_size",
                    "family",
                }.isdisjoint(entry)


def test_report_by_adds_no_executions(tmp_path, capsys, monkeypatch):
    """`reference.md` § Reporting strata's first property: "No executions are
    added — the run is unchanged and the split happens over a table that already
    exists." The ledger is the ground truth for what ran.

    Both sides sweep, so `results` is a 15-entry list rather than the single
    condition a default run produces — the ledger keys on condition and repeat
    only, so a one-condition comparison would say much less.

    The two sides differ in `statistics.report_by` and nothing else. In
    particular both declare `data.units.attributes`: that block is inside the
    [design digest](#what-auto-derives-from) — `design_digest` covers
    `data.units` and `sweep.groups` — so declaring an attribute on one side
    only redraws every `auto` seed and the two ledgers would differ by their
    repeat labels, for a reason that has nothing to do with strata."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    sweep = {
        "baseline": {"analysis.method": "pearson"},
        "grid": {"analysis.method": ["spearman", "kendall"]},
    }
    without = run_a_project(
        tmp_path / "a",
        capsys=capsys,
        units=40,
        unit_attributes=["cohort"],
        sweep=sweep,
    )
    with_strata = run_a_project(
        tmp_path / "b",
        capsys=capsys,
        units=40,
        unit_attributes=["cohort"],
        sweep=sweep,
        statistics={"report_by": ["cohort"]},
    )
    # 3 conditions × 5 seed repeats, the generated config's default replication.
    assert len(without["results"]) == 15
    assert len(without["results"]) == len(with_strata["results"])
    assert without["results"] == with_strata["results"]
