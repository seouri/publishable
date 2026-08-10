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
    patients = "\n".join(f"p{i}" for i in range(1, units + 1))
    (data / "index.csv").write_text(f"patient_id\n{patients}\n")
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
        # A per-unit value that differs both by condition (`is_spearman`,
        # keyed off the swept `analysis.method`, so `of` and `against`
        # genuinely diverge rather than recording the same numbers under two
        # labels) and *per-unit differently between the two conditions* (the
        # alternating `extra`, whose parity flips with `is_spearman`) — the
        # per-unit differences must themselves vary, not just the two
        # conditions' means, or the paired interval is zero-width and
        # `cohens_dz` returns `None` regardless of which condition is which.
        # A per-unit offset that's merely constant-but-nonzero (`+ 0.5` on
        # every unit, in both conditions) cancels in the difference and hits
        # the same trap: S4b task 5's plan did, and its fix is in
        # `docs/superpowers/sdd/2026-08-10-contrasts/progress.md`, Task 5.
        is_spearman = 1 if cfg.parameters.analysis.method == "spearman" else 0
        for i, unit in enumerate(units):
            extra = 0.5 if (i + is_spearman) % 2 == 1 else 0.0
            io.record(unit.key, {{"pred": float(i) + float(is_spearman) + extra}})
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
    assert entry["correction"] is None  # S4c's job, disclosed not applied
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


def test_a_thin_pairing_warns(tmp_path, capsys, monkeypatch):
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=3,
        limits={"min_reported_n": 10},
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
    )
    assert "min_reported_n" in doc["stdout"] or "N_PAIRED" in doc["stdout"]
